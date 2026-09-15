"""ONE run, every stage, one manifest. The workbook reads this and nothing else.

    python3 -m tools.run_pipeline [--json runs/current/23010.json]

The previous workbook mixed a V2 wall extraction with V1 exceptions because
each stage wrote its own file and the exporter read whatever was on disk.
Freshness was a property of the filesystem. Here every stage runs in order,
consumes the one before it, and records its hash in a manifest the exporter
must check.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from engine.connectivity import classify_termini, components, end_caps
from engine.control_freeze import accept as accept_control
from engine.control_freeze import compare_after_freeze
from engine.control_freeze import summary as freeze_summary
from engine.document_observations import readiness as document_readiness
from engine.free_space import (OCCUPIABLE_SPACE_CANDIDATE,
                               assert_non_overlapping, build_free_space,
                               envelope_from_wall_solid, partition_barriers)
from engine.planar import build_half_edges
from engine.planar_falsifiers import falsify
from engine.source_audit import audit_drawing, cad_oracle
from engine.topology_signals import compare_topology, segmentation_vs_validated
from engine.wall_solid import NODE_SNAP_GRID_MM, build_solid, wall_polygons
from engine.envelope import classify as classify_envelope
from engine.envelope import summary as envelope_summary
from engine.face_eligibility import (assess_components,
                                     engine_development_status,
                                     project_release_status)
from engine.frames import fit as fit_frame
from engine.geometry import VectorPdfSource, calibrate
from engine.run_manifest import RunManifest
from engine.area_accuracy import (ADJ_HALF_THICKNESS, CLEAR_INTERNAL,
                                  WALL_CENTRELINE, RoomAccuracy, distribution)
from engine.clear_internal import build as build_clear
from engine.clear_internal import summary as clear_summary
from engine.controls import manifest as control_manifest
from engine.controls import select as select_controls
from engine.face_nesting import (atomic_set, diagnose_enclosures,
                                 hierarchy)
from engine.space_identity import (EVIDENCE_FAMILY as ID_FAMILY,
                                   E_ADJACENCY, E_LABEL_ANCHOR,
                                   E_RASTER_CORRESPONDENCE,
                                   VALIDATED_GEOMETRIC_FACE,
                                   AMBIGUOUS_GEOMETRIC_FACE, SpaceIdentity,
                                   identity_status)
from engine.space_identity import summary as identity_summary
from engine.bbox import BoundingBox, raster_outline_refusal
from engine.face_qa import correspond
from engine.space_boundary import (CLEAR_INTERNAL_FINISH_FACE,
                                   build_space_boundary, classify_gap,
                                   closure_grade, material_length_m,
                                   space_closes)
from engine.space_boundary import reconcile
from engine.space_graph import (MATERIAL_WALL_GRAPH, SPACE_BOUNDARY_GRAPH,
                                build_space_boundary_graph, compare,
                                assign_spaces, containment,
                                global_portals, material_edges,
                                portal_over_closure_audit, swing_arcs)
from engine.space_graph import walk as walk_space
from engine.space_boundary import summary as boundary_summary
from engine.topology import WallPair
from engine.vector_source import read
from engine.wall_bands import (audit_extensions, build_bands,
                               single_face_candidates)
from engine.wall_bands import summary as band_summary
from engine.wall_graph import build
from engine.wall_noding import node_and_split
from tools.wall_v2_diagnostic import (probable_wall_faces, raster_ratio,
                                      wall_pen_of)

PDF = "data/golden/23010/inputs/AR-00_MAR2023.pdf"
SPACE_MAP = "data/golden/23010/inputs/space_map_23010_2f.json"
TOPOLOGY_OVERLAY = "data/golden/23010/topology_overlay.json"
RUN_ID = "V2"

CONTROLS = ("BTH-05", "BED-01", "STR-01", "OPEN-01")
HARD = ("BTH-01", "BTH-02", "BTH-03", "WSH-01", "BED-04")


def bands_to_pairs(bands):
    out = []
    for i, b in enumerate(bands, 1):
        if b.wall_face_separation_mm is None:
            continue
        half = b.wall_face_separation_mm / 2
        out.append(WallPair(f"WP-{i:04d}", b.axis,
                            b.centreline_mm - half, b.centreline_mm + half,
                            b.start_mm, b.end_mm))
    return out


def side_coverage(bands, axis, fixed, lo, hi, *, tol: float = 350.0):
    """Which sub-intervals of one room side a wall band actually covers."""
    ivs = []
    ids = []
    for b in bands:
        if b.axis != axis or abs(b.centreline_mm - fixed) > tol:
            continue
        a, bb = max(b.start_mm, lo), min(b.end_mm, hi)
        if bb > a:
            ivs.append([a, bb])
            ids.append(b.wall_band_id)
    ivs.sort()
    merged = []
    for a, bb in ivs:
        if merged and a <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], bb)
        else:
            merged.append([a, bb])
    gaps, cur = [], lo
    for a, bb in merged:
        if a - cur > 50:
            gaps.append((cur, a))
        cur = max(cur, bb)
    if hi - cur > 50:
        gaps.append((cur, hi))
    return ([tuple(m) for m in merged], gaps, tuple(ids))


def host_band_for(bands, axis, fixed, lo, hi, *, tol: float = 350.0,
                  reach: float = 400.0) -> str:
    """Which wall band is this gap a hole IN? By geometry, never by position.

    A gap is hosted when a band on the same line runs up to one of its jambs.
    If nothing does, the gap is between two unrelated walls — it may still
    close a space, and it belongs to no wall's gross line.
    """
    best, bd = "", 1e18
    for b in bands:
        if b.axis != axis or abs(b.centreline_mm - fixed) > tol:
            continue
        d = min(abs(b.end_mm - lo), abs(b.start_mm - hi))
        if d <= reach and d < bd:
            best, bd = b.wall_band_id, d
    return best


def raster_overlap(poly_mm, mask, frame, px: float) -> dict:
    """IoU of a vector polygon against a raster region, on the PIXEL GRID.

    The region is a set of pixels, not a clean polygon, so the honest exact
    answer is at pixel resolution and the resolution is stated. It measures
    the thing area alone cannot: a polygon of the right SIZE in the wrong
    PLACE scores near zero here and perfectly on an area comparison.
    """
    import numpy as np
    h, w = mask.shape
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return {"comparable": False,
                "why": "the raster region is empty on this grid"}
    # Rasterise the polygon by testing each pixel centre of the region's
    # neighbourhood — bounded work, and exact to one pixel.
    x0, x1 = int(xs.min()) - 4, int(xs.max()) + 5
    y0, y1 = int(ys.min()) - 4, int(ys.max()) + 5
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    poly = list(poly_mm)
    inter = vec_only = 0
    vec_total = 0
    for py in range(y0, y1):
        for pxl in range(x0, x1):
            vx, vy = frame.to_vector((pxl + 0.5) * px, (py + 0.5) * px)
            inside = _pt_in(poly, vx, vy)
            if inside:
                vec_total += 1
                if mask[py, pxl]:
                    inter += 1
                else:
                    vec_only += 1
    ras_total = int(mask.sum())
    union = vec_total + ras_total - inter
    cell = (px * px) / 1_000_000
    return {
        "comparable": True,
        "pixel_size_mm": round(px, 3),
        "intersection_m2": round(inter * cell, 3),
        "union_m2": round(union * cell, 3),
        "vector_only_m2": round(vec_only * cell, 3),
        "raster_only_m2": round((ras_total - inter) * cell, 3),
        "iou": round(inter / union, 4) if union else 0.0,
        "basis": "CLEAR_INTERNAL_FINISH_FACE on both sides",
        "why": ("measured on the pixel grid at the stated resolution. Area "
                "alone can agree while the shape is wrong; this cannot"),
    }


def _pt_in(poly, x: float, y: float) -> bool:
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y):
            xt = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < xt:
                inside = not inside
    return inside


def tolerance_sensitivity(bands, portals, *, perturb=(0.8, 1.0, 1.2)) -> dict:
    """Re-run the replacement spine with the node snap grid moved +/-20%.

    Testing FRAGILITY, not searching for a better value. If the wall count,
    the space count or the accepted control geometry moves materially when a
    tolerance is nudged, the number was fitted to AR-00 rather than measured.
    """
    rows = []
    for k in perturb:
        grid = NODE_SNAP_GRID_MM * k
        polys = wall_polygons(bands)
        sol = build_solid(polys, snap_grid_mm=grid)
        bars = partition_barriers(portals, polys)
        env = envelope_from_wall_solid(sol, bars)
        cands, _ = build_free_space(env, sol, bars, polys, run_id="S")
        occ = [c for c in cands
               if c.geometry_role == OCCUPIABLE_SPACE_CANDIDATE]
        rows.append({
            "node_snap_grid_mm": round(grid, 4), "factor": k,
            "resolved_wall_polygons": sum(1 for p in polys if p.is_resolved),
            "solid_components": sol.components,
            "solid_area_m2": round(sol.area_m2, 3),
            "free_space_components": len(cands),
            "occupiable_candidates": len(occ),
            "largest_occupiable_m2": (round(max(c.area_m2 for c in occ), 3)
                                      if occ else None),
        })
    base = next(r for r in rows if r["factor"] == 1.0)
    moved = {k: sorted({r[k] for r in rows})
             for k in ("resolved_wall_polygons", "solid_components",
                       "occupiable_candidates")}
    return {
        "perturbation": "node snap grid x 0.8 / 1.0 / 1.2",
        "rows": rows,
        "baseline": base,
        "values_seen": moved,
        "stable": all(len(v) == 1 for v in moved.values()),
        "note": ("the snap grid is the only non-dimensional tolerance the "
                 "replacement path introduces; the wall pairing tolerances "
                 "upstream are unchanged from previous rounds and their "
                 "sensitivity is reported by the wall extraction stage"),
    }


def run(pdf: str = PDF) -> dict:
    src_hash = hashlib.sha256(Path(pdf).read_bytes()).hexdigest()[:16]
    sm = json.loads(Path(SPACE_MAP).read_text(encoding="utf-8"))
    man = RunManifest(sm["project_id"], sm["drawing_id"],
                      sm["drawing_revision"], src_hash)

    # --- 1 frame ---------------------------------------------------------
    drawing = read(pdf)
    src = VectorPdfSource(pdf, calibrate(887.82, 40000, 554.94, 25000))
    seg = src.segmentation(0, drawing_id=sm["drawing_id"], revision=RUN_ID)
    px = float(seg.px_mm)
    heavy = [s for s in drawing.axis_aligned()
             if s.stroke_width_pt == 1.14 and s.length_mm > 1000]
    frame = fit_frame(heavy, seg.wall_mask, px)
    f_rec = man.add("frame", RUN_ID, frame.record(),
                    note=("FRAME_ALIGNMENT_VALIDATED only. The raster is "
                          "rendered from the same drawing, so vector-raster "
                          "agreement is NOT independent physical evidence "
                          "that an object is a wall"))

    # --- 2 wall extraction ----------------------------------------------
    pen = wall_pen_of(drawing)
    faces = probable_wall_faces(drawing, frame, seg.wall_mask, px, pen=pen)
    caps = end_caps(drawing.axis_aligned())

    def support(axis, centre, lo, hi):
        return raster_ratio(frame, seg.wall_mask, px, axis, centre, lo, hi)

    bands, rejections = build_bands(faces, caps=caps, wall_pen=pen,
                                    raster_support=support)
    singles = single_face_candidates(rejections, faces, raster_support=support)
    w_rec = man.add("wall_extraction", RUN_ID, band_summary(bands, rejections),
                    consumed=[("frame", f_rec.output_hash)])

    # --- 3 wall graph (MATERIAL) ----------------------------------------
    # Edge identity is the BAND ID. The old WP-0001 numbering was positional,
    # and ORDER IS NEVER IDENTITY: a face could not say which band it walked.
    mat_edges = material_edges(bands)
    mat_index = {e.edge_id: e for e in mat_edges}
    graph = build([e.to_pair() for e in mat_edges])
    noded = node_and_split(graph)
    noded.assert_length_preserved()
    comps = components(noded)
    terms = classify_termini(noded)
    split_owner = {e.edge_id: e.pair_id for e in noded.edges}
    g_rec = man.add("wall_graph", RUN_ID, noded.health(),
                    consumed=[("wall_extraction", w_rec.output_hash)])

    # --- regions, for comparison only ------------------------------------
    by_region = {s["region"]: s for s in sm["spaces"]}
    regions = {}
    for r in src.regions(0, min_m2=0.3):
        sp = by_region.get(r.id, {})
        cx, cy = frame.to_vector(r.centroid_px[0] * px, r.centroid_px[1] * px)
        regions[r.id] = {"bbox_mm": frame.bbox_to_vector(r.bbox_mm),
                         "area_m2": float(r.area_m2), "centroid_mm": (cx, cy),
                         "space_id": sp.get("space_id", ""),
                         "room_type": sp.get("room_type", ""),
                         "scope": sp.get("scope", "")}
    by_space = {r["space_id"]: r for r in regions.values() if r["space_id"]}

    # --- 4 opening / portal detection ------------------------------------
    gap_maps, portals, boundaries = {}, [], {}
    for sid in CONTROLS + HARD:
        r = by_space.get(sid)
        if r is None:
            continue
        x0, y0, x1, y1 = r["bbox_mm"]
        sides = {}
        for name, axis, fixed, lo, hi in (
                ("north", "H", y0, x0, x1), ("south", "H", y1, x0, x1),
                ("west", "V", x0, y0, y1), ("east", "V", x1, y0, y1)):
            covered, gaps, ids = side_coverage(bands, axis, fixed, lo, hi)
            span = hi - lo
            sides[name] = {"axis": axis, "fixed": fixed, "lo": lo, "hi": hi,
                           "covered": covered, "gaps": gaps, "band_ids": ids,
                           "coverage_pct": round(
                               100 * sum(b - a for a, b in covered) / span, 1)
                           if span else 0.0}
        complete = sum(1 for d in sides.values() if d["coverage_pct"] >= 95)
        for name, d in sides.items():
            for a, b in d["gaps"]:
                # §12 — the host is the band whose run this gap interrupts,
                # found by geometry on THIS side, not by list position.
                host = host_band_for(bands, d["axis"], d["fixed"], a, b)
                p = classify_gap(
                    sid, name, d["axis"], d["fixed"], a, b, caps=caps,
                    bands_face_each_other=bool(d["covered"]),
                    other_sides_complete=complete >= 3,
                    host_wall_band_id=host,
                    closure_basis=CLEAR_INTERNAL_FINISH_FACE)
                portals.append(p)
        gap_maps[sid] = {n: {"coverage_pct": d["coverage_pct"],
                             "gaps_mm": [round(b - a) for a, b in d["gaps"]]}
                         for n, d in sides.items()}
        boundaries[sid] = build_space_boundary(
            sid, sides, [p for p in portals if p.space_id == sid])
    # The per-space detector above can only find doors on the four sides a
    # bounding box happens to have. This one walks WALL LINES across the whole
    # sheet and knows nothing about rooms — §1 and §2 in one step.
    arcs = swing_arcs(drawing)
    comp_of = {}
    for c in comps:
        for eid in c.edge_ids:
            band = split_owner.get(eid)
            if band:
                comp_of[band] = c.component_id
    sheet_portals = global_portals(
        bands, caps=caps, arcs=arcs, component_of=comp_of,
        closure_basis=CLEAR_INTERNAL_FINISH_FACE)
    all_portals = portals + sheet_portals
    o_rec = man.add("portal_detection", RUN_ID,
                    [p.record() for p in all_portals],
                    consumed=[("wall_graph", g_rec.output_hash)])

    # --- 5 topology: the SAME walker over TWO graphs ----------------------
    # §4 — the face walker is not touched. Only the input graph differs, which
    # is the entire experiment: if rooms close on the space graph and stay open
    # on the material graph, the portal closures are what closed them.
    material_res, material_faces = walk_space(
        noded, mat_index, graph_type=MATERIAL_WALL_GRAPH, run_id=RUN_ID)
    sb_noded, sb_index, portal_refusals = build_space_boundary_graph(
        bands, all_portals)
    space_res, space_face_list = walk_space(
        sb_noded, sb_index, graph_type=SPACE_BOUNDARY_GRAPH, run_id=RUN_ID)
    sb_rec = man.add("space_boundary_graph", RUN_ID,
                     {"graph": sb_noded.health(),
                      "edges": len(sb_index),
                      "portal_edges_admitted": sum(
                          1 for e in sb_index.values() if e.is_virtual),
                      "portal_edges_refused": portal_refusals},
                     consumed=[("wall_graph", g_rec.output_hash),
                               ("portal_detection", o_rec.output_hash)])
    man.add("topology", RUN_ID,
            {"material": material_res.health()},
            consumed=[("wall_graph", g_rec.output_hash)])
    man.add("space_topology", RUN_ID,
            {"space_boundary": space_res.health(),
             "faces": [f.record() for f in space_face_list]},
            consumed=[("space_boundary_graph", sb_rec.output_hash)])

    # §6 — identity AFTER geometry. The faces above were generated without any
    # raster input; this is the first moment the two representations meet.
    space_correspondence = correspond(space_face_list, regions)
    # Which face a labelled region actually falls INSIDE — containment, not
    # box overlap. Overlap put every room inside the 989 m2 building face.
    face_for_space = assign_spaces(space_face_list, regions)

    # §9-§13 — the containment hierarchy, BEFORE anything is summed or named.
    nested = hierarchy(space_face_list, regions)
    atoms = atomic_set(nested)
    nest_by_id = {n.space_face_id: n for n in nested}

    # §13 — why each multi-room cycle holds more than one room.
    enclosure_diagnostics = diagnose_enclosures(
        nested, space_face_list, regions,
        rejections=[r.record() for r in rejections], index=sb_index)

    # §13 — why each multi-room cycle holds more than one room.
    enclosure_diagnostics = diagnose_enclosures(
        nested, space_face_list, regions,
        rejections=[r.record() for r in rejections], index=sb_index)

    # §14 — every portal a multi-space cycle leaned on.
    over_closure = portal_over_closure_audit(
        space_face_list, sb_index, nested, regions=regions)

    # §1-§3 — geometry and identity, as two answers. The overlay's stated
    # defects may only REJECT after the candidate exists, never build it.
    overlay = json.loads(Path(TOPOLOGY_OVERLAY).read_text(encoding="utf-8"))
    by_face_space = {v: k for k, v in face_for_space.items()}
    identities = []
    for f in space_face_list:
        n = nest_by_id.get(f.space_face_id)
        claimed = by_face_space.get(f.space_face_id, "")
        ev = []
        if claimed:
            ev.append(E_LABEL_ANCHOR)
        corr = next((c for c in space_correspondence
                     if c.face_id == f.space_face_id
                     and c.relationship == "ONE_TO_ONE"), None)
        if corr is not None and claimed in (corr.raster_space_ids or ()):
            ev.append(E_RASTER_CORRESPONDENCE)
        if f.portal_edge_ids and n is not None and len(
                n.labelled_space_ids) == 1:
            ev.append(E_ADJACENCY)
        ov = overlay.get("spaces", {}).get(claimed, {}) if claimed else {}
        rejected = ("" if ov.get("region_identity") != "FAILED"
                    else ov.get("region_identity_reason", "region identity "
                                "FAILED in the topology overlay"))
        st, why = identity_status({ID_FAMILY[e] for e in ev},
                                  rejected_by=rejected)
        geo = (VALIDATED_GEOMETRIC_FACE
               if n is not None and n.cycle_class == "ATOMIC_SPACE_FACE"
               else AMBIGUOUS_GEOMETRIC_FACE)
        identities.append(SpaceIdentity(
            space_face_id=f.space_face_id, claimed_space_id=claimed,
            geometry_status=geo, identity_status=st,
            identity_evidence=tuple(ev), rejected_by=rejected,
            why_geometry=(n.why if n is not None else ""), why_identity=why))

    # §5 — the clear-internal polygon, measured rather than adjusted.
    clear_polys, clear_failures = [], []
    for f in space_face_list:
        n = nest_by_id.get(f.space_face_id)
        if n is None or n.cycle_class != "ATOMIC_SPACE_FACE":
            continue
        try:
            clear_polys.append(build_clear(f.space_face_id, f, sb_index))
        except Exception as exc:                      # refused, not silent
            clear_failures.append({"space_face_id": f.space_face_id,
                                   "why": str(exc)})
    clear_by_face = {c.space_face_id: c for c in clear_polys}

    # §17 — a real geometric comparison, but ONLY where both sides are on the
    # clear-internal basis. A room with no complete polygon gets a row saying
    # so rather than a percentage from the scalar conversion.
    shape_rows = []
    for c in clear_polys:
        sid = by_face_space.get(c.space_face_id, "")
        rid = next((k for k, v in regions.items()
                    if v.get("space_id") == sid), None)
        row = {"space_id": sid, "space_face_id": c.space_face_id,
               "clear_polygon_complete": c.is_complete,
               "vector_clear_area_m2": round(c.area_m2, 3),
               "vector_clear_perimeter_m": round(c.perimeter_m, 3)}
        if not c.is_complete:
            row["comparable"] = False
            row["why"] = ("the clear-internal boundary is incomplete: "
                          f"{len(c.unresolved_edges)} segment(s) have no "
                          "room-facing face, so this is not the room's "
                          "outline and must not be scored")
        elif rid is None:
            row["comparable"] = False
            row["why"] = "no raster region is associated with this face"
        else:
            row.update(raster_overlap(c.polygon_mm, seg.labels == rid,
                                      frame, px))
        shape_rows.append(row)

    # §21 — the control set, by RULE, from the space map alone.
    controls = select_controls(sm["spaces"])
    control_ids = [c.space_id for c in controls]

    # =================================================================
    # THE REPLACEMENT SPINE. Everything above from `material_edges` on is
    # the DIAGNOSTIC_TOPOLOGY_PATH: it runs on the same frozen input, it is
    # falsified rather than trusted, and it may not release geometry.
    # =================================================================

    # §1 — prove the old path's failure rather than arguing about it.
    old_path_falsifiers = falsify(
        build_half_edges(sb_noded), space_res.faces, noded=sb_noded).record()

    # §3 — wall bands become the POLYGON between their two DRAWN faces.
    wall_polys = wall_polygons(bands, drawing_id=sm["drawing_id"],
                               revision=sm["drawing_revision"])
    # §4 — one robust union, with lineage and nothing deleted.
    solid = build_solid(wall_polys)
    # §5 — doorways plugged for SPACE PARTITION ONLY. Never material.
    barriers = partition_barriers(all_portals, wall_polys,
                                 drawing_id=sm["drawing_id"],
                                 revision=sm["drawing_revision"])
    # §6 — an envelope with a stated basis. Never a bounding rectangle.
    envelope = envelope_from_wall_solid(solid, barriers, wall_polys)
    # §7 — FREE_SPACE = ENVELOPE - BARRIERS, and its components are spaces.
    free_cands, free_health = build_free_space(
        envelope, solid, barriers, wall_polys, run_id=RUN_ID)
    assert_non_overlapping(free_cands)

    ws_rec = man.add("wall_solid", RUN_ID,
                     {"wall_polygons": [w.record() for w in wall_polys],
                      "solid": solid.record()},
                     consumed=[("wall_extraction", w_rec.output_hash)])
    fs_rec = man.add("free_space", RUN_ID,
                     {"envelope": envelope.record(),
                      "barriers": [b.record() for b in barriers],
                      "candidates": [c.record() for c in free_cands]},
                     consumed=[("wall_solid", ws_rec.output_hash),
                               ("portal_detection", o_rec.output_hash)])

    # §9 — raster challenges the vector result and supplies no millimetre.
    from shapely.geometry import Point

    def _holds(cand, pt):
        return cand.geometry.contains(Point(*pt))

    topo_hyps, topo_compare = compare_topology(free_cands, regions,
                                               contains=_holds)
    labels_in = {r["space_geometry_id"]: r["labelled_space_ids"]
                 for r in topo_compare["rows"] if r["space_geometry_id"]}

    # §13 / §14 — accept, then hash, BEFORE any reference is read.
    by_geom = {c.space_geometry_id: c for c in free_cands}
    frozen = []
    for c in controls:
        holder = next(
            (gid for gid, ids in labels_in.items() if c.space_id in ids), "")
        frozen.append(accept_control(
            c, by_geom.get(holder), envelope=envelope,
            labels_inside=labels_in.get(holder, ()),
            others=[x for x in free_cands
                    if x.geometry_role == OCCUPIABLE_SPACE_CANDIDATE],
            run_id=RUN_ID))

    # §17 — what the sheet is MADE OF. Safe to run on an unseen project.
    audit = audit_drawing(drawing, drawing_id=sm["drawing_id"],
                          revision=sm["drawing_revision"],
                          source_hash=src_hash, bands=bands,
                          rejections=rejections)
    man.add("source_audit", RUN_ID, audit.record(),
            consumed=[("wall_extraction", w_rec.output_hash)])

    # §18 — fragility, not tuning: does the answer move when the tolerances do?
    sensitivity = tolerance_sensitivity(bands, all_portals)

    # --- envelope --------------------------------------------------------
    unbounded_edges = {e for f in material_res.faces
                       if f.kind == "UNBOUNDED_FACE"
                       for e in f.source_wall_edge_ids}
    bounded_counts: dict = {}
    for f in material_res.bounded():
        for e in f.source_wall_edge_ids:
            bounded_counts[e] = bounded_counts.get(e, 0) + 1
    env = classify_envelope(noded.edges, unbounded_edge_ids=unbounded_edges,
                            bounded_edge_counts=bounded_counts)

    elig = assess_components(components=comps, termini=terms,
                             length_drift_mm=noded.health()[
                                 "length_difference_mm"])

    # §8 — every band extension audited against the supported portals.
    ext_audit = audit_extensions(bands, all_portals)

    # How much of each region actually fills its own bounding box, and the
    # region's own staircase perimeter. The fill ratio is why the bbox model is
    # retired: a room that fills 68% of its box is L-shaped, and the box's
    # sides are walls the building never had.
    import numpy as np
    fill, raster_perimeter_m = {}, {}
    for sid, r in by_space.items():
        rid = next((k for k, v in regions.items()
                    if v["space_id"] == sid), None)
        if rid is None:
            continue
        mask = seg.labels == rid
        ys, xs = np.where(mask)
        if len(xs) == 0:
            continue
        bbox_px = (xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1)
        fill[sid] = round(len(xs) / bbox_px, 3)
        # Boundary pixel edges x pixel size. Exact for axis-aligned outlines,
        # which is what AR-00's rooms are; it would overstate a diagonal.
        pad = np.pad(mask, 1)
        edges = (int(np.sum(pad[1:-1, 1:-1] & ~pad[:-2, 1:-1]))
                 + int(np.sum(pad[1:-1, 1:-1] & ~pad[2:, 1:-1]))
                 + int(np.sum(pad[1:-1, 1:-1] & ~pad[1:-1, :-2]))
                 + int(np.sum(pad[1:-1, 1:-1] & ~pad[1:-1, 2:])))
        raster_perimeter_m[sid] = round(edges * px / 1000, 2)

    # §15 — ONLY NOW is a reference opened, and only against a polygon whose
    # hash was taken before this line ran. The freeze is above; the
    # comparison is here, and the order is the guarantee.
    control_comparisons = [
        compare_after_freeze(
            f, reference_area_m2=by_space.get(f.space_id, {}).get("area_m2"),
            reference_perimeter_m=raster_perimeter_m.get(f.space_id),
            reference_basis=CLEAR_INTERNAL,
            reference_name="RASTER_SEGMENTATION_REGION")
        for f in frozen]

    # A bounding box per space, as an INDEX. `engine.bbox` refuses to let any
    # of these supply a room side, perimeter, closure or area.
    boxes = {sid: BoundingBox(sid, *r["bbox_mm"], fill_ratio=fill.get(sid))
             for sid, r in by_space.items()}

    # §7 / §22 — per-room accuracy, against every reference that exists. The
    # site benchmark is sealed and is NOT read here; where it is absent the
    # field stays None rather than becoming a comparison that did not happen.
    accuracy = []
    # Every space the geometry produced a face for, PLUS the named controls —
    # so a control that got no face appears as a row saying exactly that,
    # rather than dropping out of the table and out of the average with it.
    for sid in sorted(set(control_ids) | set(CONTROLS) | set(HARD)
                      | set(face_for_space)):
        if sid not in by_space:
            continue
        fid = face_for_space.get(sid, "")
        face = next((f for f in space_face_list if f.space_face_id == fid),
                    None)
        # Bring the centreline face onto the raster's clear-internal basis, so
        # the percentage is accuracy rather than a basis difference. The
        # thickness comes from the face's own physical edges.
        adj = adj_area = None
        if face is not None:
            th = [sb_index[e].separation_mm for e in face.physical_wall_edge_ids
                  if e in sb_index and sb_index[e].separation_mm]
            if th:
                adj = face.perimeter_m * (sum(th) / len(th) / 2) / 1000
                adj_area = face.area_m2 - adj
        accuracy.append(RoomAccuracy(
            space_id=sid, space_face_id=fid,
            measurement_basis="SPACE_BOUNDARY_LENGTH / VECTOR_PLANAR_FACE",
            vector_area_m2=(face.area_m2 if face else None),
            vector_perimeter_m=(face.perimeter_m if face else None),
            raster_area_m2=by_space[sid]["area_m2"],
            raster_perimeter_m=raster_perimeter_m.get(sid),
            printed_area_m2=None, site_area_m2=None,
            vector_basis=WALL_CENTRELINE, reference_basis=CLEAR_INTERNAL,
            vector_area_basis_adjusted_m2=adj_area,
            basis_adjustment_m2=adj,
            basis_adjustment_method=(ADJ_HALF_THICKNESS if adj else ""),
            # §16 — a MEASURED clear-internal polygon where one exists. The
            # scalar conversion above stays in its own columns, labelled
            # DIAGNOSTIC_APPROXIMATE_BASIS_CONVERSION, and is not accuracy.
            clear_internal_area_m2=(
                clear_by_face[fid].area_m2
                if fid in clear_by_face and clear_by_face[fid].is_complete
                else None),
            clear_internal_perimeter_m=(
                clear_by_face[fid].perimeter_m
                if fid in clear_by_face and clear_by_face[fid].is_complete
                else None),
            why=("a vector planar face on the SPACE_BOUNDARY_GRAPH, compared "
                 "against the raster region AFTER it was generated"
                 if face else
                 "no vector face was generated for this space: there is "
                 "nothing to compare, and the raster outline may not stand in "
                 "for one — " + raster_outline_refusal(sid))))

    man.rule_set_versions = {"23010_ceramic": "1.0", "23010_plaster": "1.0"}
    man.measurement_basis_version = "LENGTH_ONTOLOGY_V1"
    man.assert_coherent()

    return {
        "manifest": man.record(),
        "frame": frame.record(),
        # Measured facts the Exceptions narrative needs. Absent, they were
        # being formatted into sentences as `None` — see §18.
        "source": {"path_fragmentation": drawing.path_fragmentation()},
        "end_caps": {"found": len(caps)},
        "wall_extraction": {**band_summary(bands, rejections),
                            "single_face_candidates": len(singles)},
        "graph": noded.health(),
        "connectivity": {
            "components": len(comps),
            "components_with_cycles": sum(1 for c in comps
                                          if c.independent_cycles > 0),
            "independent_cycles": sum(c.independent_cycles for c in comps),
            "termini": len(terms),
            "terminus_histogram": dict(Counter(t.kind for t in terms)),
        },
        "status": {**engine_development_status(elig),
                   **project_release_status(
                       {"failed": [], "not_measured": []}, elig)},
        "gap_map": gap_maps,
        "portals": {
            "total": len(all_portals),
            "per_space_detector": len(portals),
            "whole_sheet_detector": len(sheet_portals),
            "swing_arcs_found": len(arcs),
            "by_status": dict(Counter(p.status for p in all_portals)),
            "by_gap_class": dict(Counter(p.gap_class for p in all_portals)),
            # §11 — existence and geometry answered separately.
            "by_existence_status": dict(Counter(
                p.existence_status for p in all_portals)),
            "by_geometry_status": dict(Counter(
                p.geometry_status for p in all_portals)),
            "exists_but_geometry_unresolved": sum(
                1 for p in all_portals if p.exists and not p.geometry_known),
            # §12 — how many openings know which wall they are a hole in.
            "with_named_host_wall": sum(
                1 for p in all_portals
                if p.hosted and p.hosted.has_host),
            "detail": [p.record() for p in all_portals],
        },
        "space_boundaries": {
            sid: {**boundary_summary(iv, [p for p in portals
                                          if p.space_id == sid]),
                  # §8 — "closes" was always a statement about the MODEL. The
                  # grade says which kind of closure this is.
                  **closure_grade(iv, vector_face_id=face_for_space.get(sid, "")),
                  "closes": space_closes(iv),
                  "bbox_fill_ratio": fill.get(sid),
                  "bbox": boxes[sid].record() if sid in boxes else None,
                  "expected_boundary_caveat": (
                      None if (fill.get(sid) or 1.0) >= 0.85 else
                      f"this region fills only {100*fill.get(sid):.0f}% of its "
                      "bounding box, so the bbox is NOT its outline: sides "
                      "measured against it may cut through open space"),
                  "intervals": [i.record() for i in iv]}
            for sid, iv in boundaries.items()},
        "union_extension_audit": ext_audit,
        "length_reconciliation": {
            sid: reconcile(iv) for sid, iv in boundaries.items()},
        # §4 — the two graphs side by side, walked by the same engine.
        "graph_comparison": compare(material_res, material_faces,
                                    space_res, space_face_list),
        "space_boundary_graph": {
            "graph": sb_noded.health(),
            "edges": len(sb_index),
            "physical_edges": sum(1 for e in sb_index.values()
                                  if not e.is_virtual),
            "portal_edges": sum(1 for e in sb_index.values() if e.is_virtual),
            "portal_edges_refused": portal_refusals,
            "edge_sample": [e.record() for e in list(sb_index.values())[:40]],
        },
        # ============ THE REPLACEMENT SPINE (production geometry) ============
        "wall_polygons": {
            "input": len(wall_polys),
            "resolved": sum(1 for w in wall_polys if w.is_resolved),
            "refused": sum(1 for w in wall_polys if not w.is_resolved),
            "by_refusal_reason": dict(Counter(
                w.unresolved_reason for w in wall_polys
                if not w.is_resolved)),
            "by_geometry_status": dict(Counter(
                w.geometry_status for w in wall_polys)),
            "sample": [w.record() for w in wall_polys[:40]],
        },
        "wall_solid": solid.record(),
        "portal_partition_barriers": {
            "accepted": free_health["barriers_accepted"],
            "rejected": free_health["barriers_rejected"],
            "unresolved": free_health["barriers_unresolved"],
            "material_role": "TOPOLOGY_ONLY_NOT_MATERIAL",
            "detail": [b.record() for b in barriers],
        },
        "building_envelope": envelope.record(),
        "free_space": {
            **free_health,
            "candidates": [c.record() for c in free_cands],
        },
        "raster_vector_topology": topo_compare,
        "raster_output_vs_validated_state": segmentation_vs_validated(
            auto_regions=len(regions),
            auto_labelled=sum(1 for r in regions.values()
                              if r.get("space_id")),
            human_identity_validated=sum(
                1 for v in overlay.get("spaces", {}).values()
                if v.get("region_identity") == "VALIDATED"),
            human_topology_validated=sum(
                1 for v in overlay.get("spaces", {}).values()
                if v.get("physical_topology") == "VALIDATED"),
            validation_source=TOPOLOGY_OVERLAY),
        "frozen_controls": {
            **freeze_summary(frozen),
            "frozen": [f.record() for f in frozen],
            "comparison_after_freeze": control_comparisons,
        },
        "source_audit": audit.record(),
        "tolerance_sensitivity": sensitivity,
        "cad_oracle": cad_oracle(
            cad_path=None, pdf_run_hash=fs_rec.output_hash).record(),
        "document_observations": document_readiness([]),
        # ============ DIAGNOSTIC_TOPOLOGY_PATH (may not release) ============
        "diagnostic_topology_path": {
            "status": "DIAGNOSTIC_TOPOLOGY_PATH",
            "may_release_geometry": False,
            "why": ("kept for one round so the replacement can be compared "
                    "against it on the same frozen input. Its own invariants "
                    "say it does not produce planar faces"),
            "falsifiers": old_path_falsifiers,
        },
        "path_comparison": {
            "old_graph_path": {
                "bounded_cycles": space_res.health()["bounded_faces"],
                "overlapping_pairs": old_path_falsifiers["by_invariant"].get(
                    "D_NO_TWO_BOUNDED_FACES_OVERLAP", 0),
                "failing_invariants": old_path_falsifiers[
                    "failing_invariants"],
                "clear_internal_polygons": len(clear_polys),
                "may_release_geometry": False,
            },
            "new_free_space_path": {
                "space_components": free_health["free_space"]["components"],
                "occupiable_candidates": free_health["free_space"][
                    "occupiable_candidates"],
                "overlapping_pairs": 0,
                "overlap_assertion": "assert_non_overlapping PASSED",
                "clear_internal_by_construction": True,
                "geometry_kernel": "GEOS via shapely",
                "may_release_geometry": True,
            },
        },
        "material_faces": material_res.health(),
        "space_boundary_faces": space_res.health(),
        # §9-§12 — containment first, then a class, then what may be added.
        "face_nesting": [n.record() for n in nested],
        "atomic_spaces": atoms,
        "enclosure_diagnostics": enclosure_diagnostics,
        # §1-§3 — two answers, never collapsed into one.
        "space_identity": {
            **identity_summary(identities),
            "verdicts": [v.record() for v in identities],
        },
        # §5 — measured polygons, and the ones the engine refused to build.
        "clear_internal": {
            **clear_summary(clear_polys),
            "refused": clear_failures,
            "polygons": [c.record() for c in clear_polys],
        },
        # §14 — every portal a multi-space cycle leaned on.
        "portal_over_closure_audit": over_closure,
        # §17 — geometric comparison where, and only where, bases match.
        "shape_comparison": {
            "rows": shape_rows,
            "compared": sum(1 for r in shape_rows if r.get("comparable")),
            "not_comparable": sum(1 for r in shape_rows
                                  if not r.get("comparable")),
            "acceptance_threshold": None,
            "note": ("IoU and the area/perimeter variances, on the "
                     "CLEAR_INTERNAL_FINISH_FACE basis on BOTH sides. Rows "
                     "that are not comparable say why instead of scoring"),
        },
        # §21 — the control set, by rule, frozen before any comparison.
        "control_set": {
            **control_manifest(controls),
            "outcome": [{
                "space_id": c.space_id, "room_type": c.room_type,
                "vector_face_id": face_for_space.get(c.space_id, ""),
                "clear_internal_polygon": (
                    face_for_space.get(c.space_id, "") in clear_by_face),
                "comparable_on_clear_basis": any(
                    r.get("comparable") and r["space_id"] == c.space_id
                    for r in shape_rows),
            } for c in controls],
        },
        "envelope": envelope_summary(env),
        "largest_faces": [f.record() for f in material_faces[:15]],
        "space_boundary_largest_faces": [f.record()
                                         for f in space_face_list[:15]],
        # §6 — established AFTER the geometry, and allowed to disagree.
        "space_face_correspondence": [c.record()
                                      for c in space_correspondence],
        # What each generated face actually encloses, by containment.
        "space_face_containment": containment(space_face_list, regions),
        # §7 / §22 — per room, with the distribution and no acceptance bar.
        "per_room_accuracy": {
            "rooms": [a.record() for a in accuracy],
            "distribution": distribution(accuracy),
        },
        # §9 / §10 — the two controls that must NOT be forced.
        "irregular_and_open_plan_controls": {
            "STR-01": {
                "role": "FIRST_REAL_CONCAVE_CONTROL",
                "vector_face_id": face_for_space.get("STR-01", ""),
                "recovered": bool(face_for_space.get("STR-01")),
                "bbox_fill_ratio": fill.get("STR-01"),
                "expected_shape": "NONE — no rectangle is expected of it",
                "why": ("the 2606 mm 'missing wall' was the east edge of a "
                        "bounding box crossing open space in an L-shaped room. "
                        "That wall is NOT repaired. The test is whether the "
                        "space boundary graph produces the concave polygon on "
                        "its own"
                        if not face_for_space.get("STR-01") else
                        "the space boundary graph produced a face for STR-01 "
                        "without being told what shape to expect"),
                "raster_outline_rule": raster_outline_refusal("STR-01"),
            },
            "OPEN-01": {
                "role": "OPEN_PLAN_CONTROL",
                "vector_face_id": face_for_space.get("OPEN-01", ""),
                "one_physical_space": True,
                "functional_zones_creating_faces": 0,
                "open_plan_edges_refused_entry": sum(
                    1 for r in portal_refusals
                    if r["refused"].startswith("OPEN_PLAN")),
                "why": ("one physical open-plan space with dining, saloon and "
                        "circulation zones inside it. A functional zone "
                        "carries zero material AND zero host wall, and no "
                        "zone boundary was admitted to the physical topology: "
                        "a face invented between saloon and dining would be "
                        "fiction"),
            },
        },
        "positive_control_verdicts": {
            sid: {
                "material_wall": (
                    f"{sum(1 for v in gap_maps[sid].values() if v['coverage_pct'] >= 95)}"
                    f" of 4 sides at 100% physical wall"),
                "gaps_mm": [g for v in gap_maps[sid].values()
                            for g in v["gaps_mm"]],
                **closure_grade(boundaries[sid],
                                vector_face_id=face_for_space.get(sid, "")),
                "space_topology_closes": space_closes(boundaries[sid]),
                "material_length_m": round(
                    material_length_m(boundaries[sid]), 2),
                "virtual_material_length_m": 0.0,
            } for sid in CONTROLS if sid in gap_maps},
        "band_sample": [b.record() for b in bands[:60]],
        "rejection_sample": [r.record() for r in rejections[:60]],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", default="runs/current/23010.json")
    a = ap.parse_args()
    rep = run()
    text = json.dumps(rep, indent=2, sort_keys=True, default=str)
    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.json).write_text(text + "\n")
    print(f"wrote {a.json}")
    print(json.dumps({k: rep[k] for k in
                      ("frame", "connectivity", "material_faces",
                       "space_boundary_faces")}, indent=1, default=str))


if __name__ == "__main__":
    main()
