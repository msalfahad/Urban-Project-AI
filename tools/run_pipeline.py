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
                               envelope_barrier_sensitivity,
                               envelope_from_wall_solid, partition_barriers)
from engine.disagreement_map import build as build_disagreement
from engine.disagreement_map import polygon_from_mask
from engine.counterfactual import RUN_A, RUN_B
from engine.counterfactual import compare as compare_arms
from engine.counterfactual import observe as observe_arm
from engine.free_space import RELEASABLE_PARTITION_BARRIER as \
    RELEASABLE_BARRIER
from engine.free_space import release_policy
from engine.blob_causes import build as build_blob_causes
from engine.junction_patch import propose as propose_patch
from engine.junction_patch import summary as patch_summary
from engine.wall_authority import DIAGNOSTIC as DIAGNOSTIC_SOLID
from engine.wall_authority import ESTABLISHED as ESTABLISHED_SOLID
from engine.wall_authority import build as build_authority_solid
from engine.wall_authority import classify_intervals as classify_admissions
from engine.wall_authority import compare as compare_solids
from engine.wall_authority import unestablished_dependency
from engine.reference_mapping import ReferenceRow, refuse_if_sealed
from engine.release_blocker import assess as assess_blockers
from engine.release_blocker import portal_bottleneck
from engine.unresolved_impact import assess as assess_unresolved
from engine.freeze_guard import check as check_freeze
from engine import boundary_match as hybrid_match
from engine import hybrid_path
from engine import raster_topology as raster_topo
from engine.document_reader import read_runs as read_document
from engine.glyph_text import locate as glyph_locate
from engine.region_boundary import simplify as simplify_ring
from engine.region_boundary import trace as trace_ring
from engine import space_role as hybrid_role
from engine import topology_metrics as hybrid_metrics
from engine.dimension_check import assess as assess_dimensions
from engine.space_objects import (MEASUREMENT_COMPLETE_DIAGNOSTIC,
                                  MEASUREMENT_COMPLETE_PRODUCTION,
                                  SRC_DIAGNOSTIC_VECTOR,
                                  SRC_VECTOR_WALL_FACE)
from engine.reference_mapping import resolve as resolve_references
from engine.fragment_recovery import extension_summary
from engine.fragment_recovery import polygons as fragment_polygons
from engine.fragment_recovery import recover_extensions
from engine.fragment_recovery import resolve as resolve_fragments
from engine.fragment_recovery import summary as fragment_summary
from engine.fragment_selftest import cases as selftest_cases
from engine.fragment_selftest import report as selftest_report
from engine.fragment_selftest import run as run_selftest
from engine.free_space_invariants import falsify as falsify_free
from engine.leak_map import build as build_leaks
from engine.leak_map import summary as leak_summary
from engine.unpaired_strokes import classify as classify_strokes
from engine.unpaired_strokes import summary as stroke_summary
from engine.interval_fidelity import audit as interval_audit
from engine.snap_tolerance import compare_to_the_grid_in_use as compare_snap
from engine.snap_tolerance import measure as measure_snap
from engine.snap_topology import diff as snap_diff
from engine.space_recall import assess as assess_recall
from engine.stroke_sample import draw as draw_sample
from engine.unpaired_strokes import SINGLE_LINE_EXISTENCE_SUPPORTED
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
DOC_CACHE = "data/golden/23010/doc_read_cache"
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
    # §2 — the unpaired wall-pen population, classified on evidence. Its
    # LENGTH was previously reported as SINGLE_LINE_WALL, which was a guess
    # dressed as a measurement.
    paired_face_ids = {i for b in bands
                       for i in tuple(b.face_a_ids) + tuple(b.face_b_ids)}
    strokes = classify_strokes(
        [f for f in faces if f.segment_id not in paired_face_ids],
        bands, raster_support=support, wall_pen=pen)
    w_rec = man.add("wall_extraction", RUN_ID,
                    {**band_summary(bands, rejections),
                     "unpaired_wall_style_strokes": stroke_summary(strokes)},
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
    space_centroid_px = {}
    for r in src.regions(0, min_m2=0.3):
        sp = by_region.get(r.id, {})
        if sp.get("space_id"):
            space_centroid_px[sp["space_id"]] = r.centroid_px
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

    # §3 — the eight free-space invariants, run on the real result. Nothing
    # downstream may quote an area from a construction that does not hold.
    free_invariants = falsify_free(
        wall_polys, solid, barriers, envelope, free_cands).record()
    # §4 — an internal doorway must not move the floor's outer extent.
    envelope_sensitivity = envelope_barrier_sensitivity(
        solid, barriers, wall_polys)
    # §10 — does each polygon span only what the drawing drew?
    fidelity = interval_audit(wall_polys, portals=all_portals,
                              established=lambda q: q.exists).record()
    # §11 — the snap grid, measured on THIS drawing's coordinates.
    snap_evidence = measure_snap([w.ring for w in wall_polys
                                  if w.is_resolved])
    # §7 — production uses the MEASURED tolerance. A larger global snap is
    # not proven safe by a small area change: it can alter connectivity,
    # and physical junctions are repaired by JUNCTION_PATCH instead.
    measured_grid = (snap_evidence.recommended_grid_mm
                     if snap_evidence.is_usable else 0.0)
    snap_audit = {
        **snap_evidence.record(),
        "grid_actually_used": compare_snap(snap_evidence, solid.snap_grid_mm),
        "grid_used_for_the_established_solid_mm": measured_grid,
        "why_the_measured_grid_for_production": (
            "topology, not area, decides whether a tolerance is safe. A "
            "microscopic change can still create a connection, so the "
            "established solid is built on the measured noise floor and "
            "physical junctions are closed by an explicit JUNCTION_PATCH"),
    }

    # §13 — the replacement spine is SIX stages, and the manifest says so.
    # Collapsing them into "wall_solid" and "free_space" hid where an area
    # came from: a reader could not tell whether an envelope was derived
    # before or after the barriers, and lineage is the whole point.
    wp_rec = man.add("wall_polygon_run", RUN_ID,
                     {"wall_polygons": [w.record() for w in wall_polys],
                      "interval_fidelity": fidelity},
                     consumed=[("wall_extraction", w_rec.output_hash)])
    ws_rec = man.add("wall_solid_run", RUN_ID,
                     {"solid": solid.record(),
                      "numerical_snap_tolerance": snap_audit},
                     consumed=[("wall_polygon_run", wp_rec.output_hash)])
    pp_rec = man.add("portal_partition_run", RUN_ID,
                     {"barriers": [b.record() for b in barriers],
                      "material_role": "TOPOLOGY_ONLY_NOT_MATERIAL"},
                     consumed=[("wall_polygon_run", wp_rec.output_hash),
                               ("portal_detection", o_rec.output_hash)])
    be_rec = man.add("building_envelope_run", RUN_ID,
                     {"envelope": envelope.record(),
                      "internal_barrier_sensitivity": envelope_sensitivity},
                     consumed=[("wall_solid_run", ws_rec.output_hash),
                               ("portal_partition_run",
                                pp_rec.output_hash)])
    fs_rec = man.add("free_space_run", RUN_ID,
                     {"candidates": [c.record() for c in free_cands],
                      "health": free_health,
                      "invariants": free_invariants},
                     consumed=[("building_envelope_run",
                                be_rec.output_hash),
                               ("wall_solid_run", ws_rec.output_hash),
                               ("portal_partition_run",
                                pp_rec.output_hash)])

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

    # §8 / §9 — WHERE the merged components leaked, and what is drawn
    # there. Two localisers, because the raster one is provably incomplete
    # on its own; see engine.leak_map.build.
    rid_of = {r["space_id"]: k for k, r in regions.items()
              if r.get("space_id")}

    def _region_of(space_id):
        return seg.labels == rid_of[space_id] if space_id in rid_of else None

    thickest = max([w.thickness_mm for w in wall_polys
                    if w.thickness_mm is not None] or [0.0])
    leaks, leak_pairs = build_leaks(
        free_cands, labels_in, region_of=_region_of, px_mm=px,
        to_vector=frame.to_vector, bands=bands, strokes=strokes,
        portals=all_portals, controls=[c.space_id for c in controls],
        max_wall_thickness_mm=thickest,
        seeds={r["space_id"]: r["centroid_mm"] for r in regions.values()
               if r.get("space_id")})
    leaks_rec = leak_summary(leaks, candidates=free_cands, audit=leak_pairs)

    # §13 — resolution is its own stage: this is where a free-space
    # component acquires a label, and where a control is frozen against it.
    sr_rec = man.add("space_resolution_run", RUN_ID,
                     {"labels_inside": labels_in,
                      "raster_vector_topology": topo_compare,
        # §8 / §9 — where the merged components actually leaked.
        "space_leak_maps": leaks_rec,
        # §2 — the unpaired population, classified. NOT 851 m of wall.
        "unpaired_wall_style_strokes": stroke_summary(strokes),
                      "frozen_controls": [f.record() for f in frozen],
                      "leak_maps": leaks_rec},
                     consumed=[("free_space_run",
                                fs_rec.output_hash)])

    # §17 — what the sheet is MADE OF. Safe to run on an unseen project.
    # The unpaired stroke classification goes in, so the audit reports a
    # classified population rather than 851 m called SINGLE_LINE_WALL.
    audit = audit_drawing(drawing, drawing_id=sm["drawing_id"],
                          revision=sm["drawing_revision"],
                          source_hash=src_hash, bands=bands,
                          rejections=rejections, unpaired_strokes=strokes,
                          faces=faces)
    man.add("source_audit", RUN_ID, audit.record(),
            consumed=[("wall_extraction", w_rec.output_hash),
                      ("space_resolution_run", sr_rec.output_hash)])

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

    # §6 — WHY a frozen control differs from its raster reference, cut into
    # causes A-G. Nothing here corrects the geometry and nothing is tuned:
    # several of the causes are the REFERENCE's error.
    def _raster_polygon(space_id):
        rid = next((k for k, r in regions.items()
                    if r.get("space_id") == space_id), None)
        if rid is None:
            return None
        return polygon_from_mask(seg.labels == rid, px_mm=px,
                                 to_vector=frame.to_vector)

    other_polys = {r["space_id"]: _raster_polygon(r["space_id"])
                   for r in regions.values() if r.get("space_id")}
    disagreements = []
    for f in frozen:
        holder = next((c for c in free_cands
                       if f.space_id in labels_in.get(c.space_geometry_id,
                                                      ())), None)
        disagreements.append(build_disagreement(
            f.space_id,
            holder.geometry if holder is not None else None,
            other_polys.get(f.space_id), solid=solid, barriers=barriers,
            other_regions=other_polys,
            max_wall_thickness_mm=thickest).record())

    # §5 — which spaces rest on a barrier that may not release a quantity.
    barrier_release = release_policy(barriers, free_cands)

    # --- CONSERVATIVE GEOMETRY TRUTH -----------------------------------
    # §5 — a junction is closed by EVIDENCE or not at all. Every refused
    # gap still names the repair it actually needs.
    patches = [propose_patch(
        {"axis": lk.frontier_axis, "fixed_mm": lk.frontier_fixed_mm,
         "along_mm": lk.frontier_along_mm,
         "passage_width_mm": lk.passage_width_mm,
         "leak_id": lk.leak_id, "located_by": lk.localiser},
        bands, wall_polys=wall_polys, caps=caps, raster_support=support,
        strokes=strokes, max_wall_thickness_mm=thickest,
        drawing_id=sm["drawing_id"], revision=sm["drawing_revision"],
        patch_id=f"JP-{i:04d}")
        for i, lk in enumerate(sorted(
            (x for x in leaks if x.hairline_junction_gap),
            key=lambda x: x.passage_width_mm), 1)]
    validated_patches = [p for p in patches if p.is_validated]

    # --- FRAGMENTED WALL RECOVERY -------------------------------------
    # §7 — the known-answer test runs FIRST, on real accepted bands with
    # one face artificially cut up. If the resolver cannot put those back
    # it has no business touching the real population.
    consumed_faces = {i for b in bands
                      for i in tuple(b.face_a_ids) + tuple(b.face_b_ids)}
    selftest = selftest_report([run_selftest(c)
                                for c in selftest_cases(bands, limit=3)])

    # §4 / §5 — 1-to-N grouping among faces no band consumed.
    fragment_groups = resolve_fragments(
        faces, portals=all_portals, caps=caps, bands=bands,
        used_face_ids=consumed_faces, drawing_id=sm["drawing_id"],
        revision=sm["drawing_revision"])

    # §3 / §4 — per-interval admission, then the two solids. The
    # unestablished extensions never enter the established one.
    pre_authority = classify_admissions(wall_polys, patches=patches)
    # The case the round is really about: an UNRESOLVED_EXTENSION stretch
    # where the second face turns out to be drawn as collinear fragments.
    extension_recoveries = recover_extensions(
        pre_authority.admissions, wall_polys, faces, portals=all_portals,
        used_face_ids=consumed_faces, drawing_id=sm["drawing_id"],
        revision=sm["drawing_revision"])
    authority = classify_admissions(wall_polys, patches=patches,
                                    recoveries=extension_recoveries)
    from shapely.ops import unary_union as _u
    # §9 — a recovered multi-fragment wall enters the established solid
    # only where its polygon is fully supported; everything else is
    # diagnostic. The old pattern where an unresolved extension quietly
    # became masonry is not revived.
    recovered_polys = fragment_polygons(fragment_groups)
    recovered_diag_polys = fragment_polygons(fragment_groups,
                                             validated_only=False)
    _s0 = build_authority_solid(
        wall_polys, patches=validated_patches, solid=ESTABLISHED_SOLID,
        report=pre_authority, snap_grid_mm=measured_grid)
    established_solid = _u(
        [build_authority_solid(
            wall_polys, patches=validated_patches, solid=ESTABLISHED_SOLID,
            report=authority, snap_grid_mm=measured_grid)]
        + recovered_polys)
    diagnostic_solid = _u(
        [build_authority_solid(
            wall_polys, patches=patches, solid=DIAGNOSTIC_SOLID,
            report=authority, snap_grid_mm=measured_grid)]
        + recovered_diag_polys)
    solid_comparison = compare_solids(established_solid, diagnostic_solid)

    # §13 — two free spaces. RELEASE uses the established solid and only
    # release-eligible barriers; DIAGNOSTIC uses the augmented solid and
    # every accepted barrier. The pair is the honest picture of what we
    # KNOW against what we can plausibly hypothesise.
    releasable_barriers = [b for b in barriers
                           if b.release_class == RELEASABLE_BARRIER]
    _arm = dict(wall_polys=wall_polys, portals=all_portals,
                regions=regions, contains=_holds, controls=tuple(CONTROLS))
    release_arm = observe_arm("RELEASE_FREE_SPACE", established_solid,
                              barriers=releasable_barriers, run_id="REL",
                              **_arm)
    diagnostic_arm = observe_arm("DIAGNOSTIC_FREE_SPACE", diagnostic_solid,
                                 barriers=barriers, run_id="DIA", **_arm)

    # §6 — the counterfactual. Same established solid; the ONLY difference
    # is the validated junction patches.
    counterfactual = compare_arms(
        observe_arm(RUN_A, build_authority_solid(
            wall_polys, patches=[], solid=ESTABLISHED_SOLID,
            report=classify_admissions(wall_polys, patches=[]),
            snap_grid_mm=measured_grid),
            barriers=barriers, run_id="CFA", **_arm),
        observe_arm(RUN_B, build_authority_solid(
            wall_polys, patches=validated_patches, solid=ESTABLISHED_SOLID,
            report=classify_admissions(wall_polys,
                                       patches=validated_patches),
            snap_grid_mm=measured_grid),
            barriers=barriers, run_id="CFB", **_arm),
        repairs=[p.patch_id for p in validated_patches])

    # §10 — S0, S1, S2. The ONLY difference between S0 and S1 is the
    # validated fragmented-mate recovery.
    _arm2 = dict(wall_polys=wall_polys, portals=all_portals,
                 regions=regions, contains=_holds,
                 controls=tuple(CONTROLS), barriers=barriers)
    _a0 = observe_arm("S0_CURRENT_ESTABLISHED", _s0, run_id="S0", **_arm2)
    _a1 = observe_arm("S1_PLUS_VALIDATED_FRAGMENT_RECOVERY",
                      established_solid, run_id="S1", **_arm2)
    _a2 = observe_arm("S2_PLUS_DIAGNOSTIC_HYPOTHESES", diagnostic_solid,
                      run_id="S2", **_arm2)
    solid_arms = {
        **compare_arms(_a0, _a1, repairs=["VALIDATED_FRAGMENT_RECOVERY"]),
        "S2_plus_diagnostic_hypotheses": _a2.record(),
        "what_S2_adds": (
            "every hypothesis: unresolved extensions, unvalidated junction "
            "patches and diagnostic fragment groups. A space that appears "
            "only in S2 exists because a hypothesis was treated as fact"),
        "geometry_recovered_vs_partition_improved": (
            "S1 minus S0 is what VALIDATED recovery bought. Geometry "
            "recovered with no topology effect is a real gain in the wall "
            "solid and no gain in the partition, and the two are reported "
            "apart because only the second unlocks a room"),
    }

    # §11 — the release audit. DIAGNOSTIC_GEOMETRY_ACCEPTED and
    # PRODUCTION_GEOMETRY_RELEASED are different verdicts: a room whose
    # partition needs a merely diagnostic portal, or whose boundary rests on
    # unestablished wall material, cannot become production geometry
    # because the resulting polygon happens to be valid.
    by_release = {r["space_geometry_id"]: r
                  for r in barrier_release["space_geometries"]}
    control_release_audit = []
    for f in frozen:
        holder = next((c for c in free_cands
                       if f.space_id in labels_in.get(c.space_geometry_id,
                                                      ())), None)
        dep = (unestablished_dependency(holder, authority.admissions,
                                        wall_polys)
               if holder is not None else
               {"depends_on_unestablished_material": None,
                "why": "no free-space component holds this control"})
        rel = by_release.get(
            getattr(holder, "space_geometry_id", ""), {})
        labels_here = labels_in.get(
            getattr(holder, "space_geometry_id", ""), ())
        blockers = []
        if holder is None:
            blockers.append("no free-space component holds this control")
        if dep.get("depends_on_unestablished_material"):
            blockers.append(
                f"its boundary rests on "
                f"{dep['unestablished_boundary_length_m']} m of wall "
                "material whose physical presence is NOT established")
        if rel.get("release_class") == "DIAGNOSTIC_PARTITION_BARRIER":
            blockers.append(
                "its partition depends on a barrier whose portal existence "
                "is not validated: "
                + ", ".join(rel.get("barriers_that_cannot_release", ())))
        if len(labels_here) > 1:
            blockers.append(
                f"the component holding it also holds {len(labels_here) - 1} "
                "other labelled space(s), so it is not this room's polygon")
        control_release_audit.append({
            "space_id": f.space_id,
            "space_geometry_id": getattr(holder, "space_geometry_id", ""),
            "frozen_area_m2": f.area_m2,
            "geometry_hash": f.geometry_hash,
            "DIAGNOSTIC_GEOMETRY_ACCEPTED": (
                f.status == "GEOMETRY_ACCEPTED_AND_FROZEN"),
            "PRODUCTION_GEOMETRY_RELEASED": not blockers,
            "release_blockers": blockers,
            "unestablished_wall_dependency": dep,
            "barrier_release_class": rel.get("release_class"),
            "why": ("every boundary contributor satisfies production-level "
                    "evidence" if not blockers else
                    "; ".join(blockers)),
        })

    # §7 — topology, not area, decides whether a coarser grid is safe.
    from shapely.geometry import Polygon
    snap_topology = snap_diff(
        [Polygon(list(w.ring)) for w in wall_polys if w.is_resolved],
        fine_mm=measured_grid or 0.01, coarse_mm=NODE_SNAP_GRID_MM,
        noise_floor_mm=snap_evidence.recommended_grid_mm,
        patches=validated_patches).record()

    # §9 — a deterministic BLIND sample of the single-line population, with
    # each member's raw evidence and no verdict.
    single_line_sample = draw_sample(
        strokes, population_class=SINGLE_LINE_EXISTENCE_SUPPORTED,
        bands=bands, faces=faces, regions=regions,
        seed=f"{sm['drawing_id']}-{sm['drawing_revision']}").record()

    # §12 — two recalls. A hypothesis must not inflate the production one.
    in_scope = sum(1 for s in sm.get("spaces", ())
                   if s.get("scope") == "IN_SCOPE")
    recall = assess_recall(
        free_cands, labels_inside=labels_in, in_scope_spaces=in_scope,
        dependency_of=lambda c: unestablished_dependency(
            c, authority.admissions, wall_polys),
        release_of=lambda c: by_release.get(c.space_geometry_id, {})
    ).record()

    # §12 — which dependency holds release at zero. Zero because the
    # walls are not established is a different project from zero because
    # the portals are not validated.
    _blocked = []
    for row in recall.get("single_label_but_blocked", ()):
        gid = row.get("space_geometry_id")
        rel = by_release.get(gid, {})
        _blocked.append({**row, "blocking_portal_ids":
                         rel.get("barriers_that_cannot_release", ())})
    blockers = assess_blockers(
        {**recall, "single_label_but_blocked": _blocked},
        in_scope_spaces=in_scope)
    blocker_report = {
        **blockers.record(),
        # §15 — preparation for the document round, not extraction.
        "portal_bottleneck": portal_bottleneck(
            blockers.record()["rows"], barriers, portals=all_portals),
    }

    # §14 — the UNRESOLVED population, ranked by the separation failures
    # it sits in. NOT by length: a long stroke in site hatching is worth
    # nothing, and none of these is resolved this round.
    unresolved_impact = assess_unresolved(
        strokes, leaks, controls=tuple(CONTROLS)).record()

    # ================= HYBRID PDF TOPOLOGY =========================
    # Raster/vision finds the space; vector geometry supplies every
    # released millimetre. The automatic topology is built from the render
    # and the ESTABLISHED solid only — no golden region, no overlay, no
    # room list — and it is HASHED before anything human is read.
    hybrid_topology = raster_topo.build(
        seg, frame, established_solid=established_solid,
        diagnostic_solid=diagnostic_solid, portal_barriers=barriers,
        drawing_id=sm["drawing_id"], revision=sm["drawing_revision"])
    hybrid_topology_hash = hybrid_topology.output_hash

    # A face interval is production-eligible only where the wall authority
    # admits established material over that span. Everything else is
    # diagnostic vector geometry, which may complete a polygon and may
    # never release one.
    _est_by_band: dict = {}
    for _a in authority.admissions:
        if _a.is_established:
            _est_by_band.setdefault(_a.wall_band_id, []).append(
                (min(_a.start_mm, _a.end_mm), max(_a.start_mm, _a.end_mm)))

    def _classify_face(wp, side, lo, hi):
        spans = _est_by_band.get(wp.wall_band_id, ())
        lo, hi = min(lo, hi), max(lo, hi)
        covered = any(a <= lo + 1.0 and b >= hi - 1.0 for a, b in spans)
        return ((SRC_VECTOR_WALL_FACE, "ESTABLISHED") if covered
                else (SRC_DIAGNOSTIC_VECTOR, "DIAGNOSTIC"))

    # Where each labelled space sits in the AUTOMATIC regions. This is the
    # only place a label enters, and it enters after the hash above.
    _lab = np.asarray(hybrid_topology.labels)
    _region_of_label = {v: k for k, v in
                        hybrid_topology.region_label_of.items()}
    hybrid_labels_in: dict = {}
    hybrid_labels_unplaced = []
    for _sid, (_cx, _cy) in sorted(space_centroid_px.items()):
        _rid = _region_of_label.get(int(_lab[int(_cy), int(_cx)]))
        if _rid is None:
            hybrid_labels_unplaced.append(_sid)
        else:
            hybrid_labels_in.setdefault(_rid, []).append(_sid)

    hybrid = hybrid_path.run(
        hybrid_topology, wall_polys=wall_polys, caps=caps,
        barriers=barriers, frame=frame, px_mm=px,
        classify=_classify_face, labels_inside=hybrid_labels_in)

    # §16 — topology scored against the FROZEN automatic output.
    hybrid_topology_score = hybrid_metrics.score_topology(
        hybrid_topology, labels_in_region=hybrid_labels_in,
        expected_spaces=[x["space_id"] for x in sm["spaces"]]).record()

    # §17 — measurement, for the regions holding exactly one labelled space.
    _by_region = hybrid.by_region
    _single = [r for r in hybrid_topology.regions
               if len(hybrid_labels_in.get(r.region_id, ())) == 1]
    hybrid_measurement_score = hybrid_metrics.score_measurement(
        [(r, _by_region[r.region_id]) for r in _single
         if r.region_id in _by_region]).record()

    # §7 / §18 — the document read, from its cache. Reading is a separate
    # tool (tools/read_document_text.py) so the pipeline stays free and
    # offline; absent a cache this reports NOT_READ rather than "no text".
    _runs = glyph_locate(PDF)
    doc_read = read_document(
        PDF, _runs.runs, cache_dir=DOC_CACHE,
        drawing_id=sm["drawing_id"], revision=sm["drawing_revision"])
    doc_record = doc_read.record()

    # §18 — printed dimension against vector measurement, for the controls
    # and every other region holding one labelled space. Never averaged.
    hybrid_dimension_check = assess_dimensions(
        [(hybrid_labels_in[r.region_id][0], _by_region[r.region_id])
         for r in _single if r.region_id in _by_region],
        doc_read.dimensions).record()

    # §20 / §21 — the controls through the hybrid path. A NEW record with a
    # NEW hash: the historical diagnostic results are not mutated, and the
    # result closest to the raster is NOT the one chosen.
    hybrid_controls = []
    for _cid in CONTROLS:
        _rid = next((k for k, v in hybrid_labels_in.items()
                     if _cid in v), "")
        _cand = _by_region.get(_rid)
        _role = next((x for x in hybrid.roles if x.region_id == _rid), None)
        _reg = next((r for r in hybrid_topology.regions
                     if r.region_id == _rid), None)
        hybrid_controls.append({
            "space_id": _cid,
            "found_by_raster_topology": bool(_rid),
            "automatic_region_id": _rid,
            "labels_sharing_the_region": sorted(
                hybrid_labels_in.get(_rid, ())),
            "raster_APPROXIMATE_area_m2": (
                None if _reg is None
                else round(_reg.approximate_area_m2, 3)),
            "physical_role": None if _role is None else _role.role,
            "HYBRID_RESULT": (None if _cand is None else {
                "candidate_id": _cand.candidate_id,
                "measurement_status": _cand.measurement_status,
                "boundary_measured_pct": _cand.measured_pct,
                "boundary_production_eligible_pct": _cand.production_pct,
                "unresolved_intervals": len(_cand.unresolved_intervals),
                "area_m2": (None if _cand.area_m2 is None
                            else round(_cand.area_m2, 3)),
                "NEW_geometry_hash": _cand.geometry_hash,
                "polygon_closed": _cand.polygon_closed,
            }),
            "historical_results_are_not_mutated": (
                "the frozen diagnostic BED-01 result keeps its own hash and "
                "its 21.034 m². This is a separate record of a separate "
                "measurement by a different path"),
            "how_the_result_was_chosen": (
                "by the boundary matcher's own priority order. NOT by which "
                "answer came closest to the raster mask or to any "
                "reference"),
        })

    # §24 — the gate.
    _complete = [c for c in hybrid.candidates
                 if c.measurement_status in (
                     MEASUREMENT_COMPLETE_PRODUCTION,
                     MEASUREMENT_COMPLETE_DIAGNOSTIC)]
    _ctrl_complete = [x for x in hybrid_controls
                      if x["HYBRID_RESULT"]
                      and x["HYBRID_RESULT"]["polygon_closed"]]
    _mean_measured = (
        hybrid_measurement_score["boundary_source_coverage_pct"][
            "measured_mean"] or 0.0)
    hybrid_gate = hybrid_path.gate(
        controls_complete=bool(_ctrl_complete),
        complete_measured_spaces=len([
            c for c in _complete
            if len(hybrid_labels_in.get(c.region_id, ())) == 1]),
        deterministic_complete_spaces=0,
        topology_recall_pct=hybrid_topology_score["REGION_RECALL_PCT"],
        deterministic_single_room_spaces=_a1.single_room,
        expected_spaces=len(sm["spaces"]),
        mean_boundary_measured_pct=_mean_measured)

    hybrid_record = {
        **hybrid.record(),
        "labels_placed_in_an_automatic_region": sum(
            len(v) for v in hybrid_labels_in.values()),
        "labels_not_placed": hybrid_labels_unplaced,
        "TOPOLOGY_SCORE_can_it_find_the_room": hybrid_topology_score,
        "MEASUREMENT_SCORE_can_it_measure_the_room":
            hybrid_measurement_score,
        "zones": hybrid_role.zones(
            hybrid_topology.regions,
            labels_inside=hybrid_labels_in).record(),
        "frozen_controls_through_the_hybrid_path": hybrid_controls,
        "document_dimension_vs_vector": hybrid_dimension_check,
        "GATE": hybrid_gate,
        "search_window_sensitivity": (
            {} if not _single else hybrid_match.sensitivity(
                simplify_ring(trace_ring(
                    hybrid_topology.labels,
                    hybrid_topology.region_label_of[_single[0].region_id],
                    frame, px, min_run_px=1)),
                hybrid.pool)),
    }

    # §14 — one work list per merged component, ranked by what it unlocks.
    blob_table = build_blob_causes(
        leaks, labels_inside=labels_in, patches=patches, strokes=strokes,
        controls=CONTROLS, counterfactual=counterfactual).record()

    # §7 — other references may be opened AFTER the freeze, and only where
    # the mapping and the basis are both unambiguous. On this project the
    # space map carries names and types but no areas, so every row resolves
    # to a space and then stops at NO_VALUE: the mapping is recorded, the
    # comparison is not. The sealed site benchmark is refused by name.
    ref_rows = [ReferenceRow(row_id=f"SM-{i:03d}",
                             label=s.get("name_en") or s.get("space_id", ""),
                             value=None, basis="",
                             source="SPACE_MAP_LABEL_ROW")
                for i, s in enumerate(sm.get("spaces", ()), 1)]
    ref_spaces = {s["space_id"]: {"name_en": s.get("name_en", ""),
                                  "name_ar": s.get("name_ar", ""),
                                  "room_type": s.get("room_type", "")}
                  for s in sm.get("spaces", ()) if s.get("space_id")}
    reference_mapping = {
        **resolve_references(ref_rows, ref_spaces,
                             compatible_bases=(CLEAR_INTERNAL,)).record(),
        "references_available_on_this_project": {
            "RASTER_SEGMENTATION_REGION": (
                "opened, after the freeze, and decomposed by cause in "
                "frozen_controls.disagreement_maps. It is a second signal, "
                "not ground truth"),
            "SPACE_MAP_LABEL_ROWS": (
                "names and room types only. Every row maps to a space and "
                "carries NO area, so the mapping is recorded and no "
                "comparison is made"),
            "TOPOLOGY_OVERLAY": (
                "human validation states, not measurements. Counted "
                "separately from automatic output and never quoted as "
                "evidence that the algorithm is accurate"),
            "SEALED_SITE_BENCHMARK": (
                "NOT OPENED. It is the only honest test this project has of "
                "whether the engine measures a real building, and reading it "
                "here would spend it"),
        },
    }
    refuse_if_sealed(str(SPACE_MAP))

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
            # §5 — accepted is not releasable. A PORTAL_PROBABLE may make a
            # space hypothesis and may NOT make that space releasable.
            "release_policy": barrier_release,
            "detail": [b.record() for b in barriers],
        },
        "building_envelope": {
            **envelope.record(),
            # §4 — the audit, not an assurance. It is reported whether it
            # passes or fails, and a vacuous pass is visible: if every
            # barrier classified external there would be nothing to test.
            "internal_barrier_sensitivity": envelope_sensitivity,
        },
        "free_space": {
            **free_health,
            "candidates": [c.record() for c in free_cands],
        },
        # §3 — the invariants that make the free-space areas quotable.
        "free_space_invariants": free_invariants,
        # §10 — what the polygons span against what the drawing drew.
        "wall_polygon_interval_fidelity": fidelity,
        # §11 — a measured tolerance, and the constant it audits.
        "numerical_snap_tolerance": snap_audit,
        # §3 / §4 — two wall solids, and what the hypothesis adds.
        "wall_authority": {
            **authority.record(),
            "solid_comparison": solid_comparison,
        },
        # §5 — junctions closed by evidence, never by a tolerance.
        "junction_patches": patch_summary(patches),
        # §7 — every connection the coarser grid creates, classified.
        "snap_grid_topology_diff": snap_topology,
        # §9 — the blind sample of the single-line population.
        "single_line_wall_blind_sample": single_line_sample,
        # §12 — diagnostic recall beside release-eligible recall.
        "space_geometry_recall": recall,
        # §14 — the ranked work list for the merged components.
        "merged_component_causes": blob_table,
        # §6 — and the proof that the named repairs are or are not causal.
        "junction_patch_counterfactual": counterfactual,
        # §7 — the known-answer test, run before the real population.
        "fragment_recovery_selftest": selftest,
        # §4 / §5 / §8 — the real recovery, both modes.
        "fragment_recovery": {
            "new_groups": fragment_summary(fragment_groups),
            "band_extension_recoveries": extension_summary(
                extension_recoveries),
        },
        # §10 — S0 vs S1 vs S2. What validated recovery actually buys.
        "fragment_recovery_counterfactual": solid_arms,
        # §12 / §15 — which dependency is holding release at zero, and
        # which portals would be next to validate.
        "release_blockers": blocker_report,
        "unresolved_stroke_impact": unresolved_impact,
        "hybrid_pdf_topology": hybrid_record,
        "document_observations_read": doc_record,
        # §13 — what we KNOW against what we can plausibly hypothesise.
        "release_vs_diagnostic_free_space": {
            "release": release_arm.record(),
            "diagnostic": diagnostic_arm.record(),
            "release_eligible_barriers": len(releasable_barriers),
            "accepted_barriers": len([
                b for b in barriers if b.status == "BARRIER_ACCEPTED"]),
            "what_the_pair_shows": (
                "the RELEASE arm is built only from material whose physical "
                "presence is established and barriers whose portals are "
                "validated. The DIAGNOSTIC arm adds every hypothesis. A "
                "space that appears only in the diagnostic arm exists "
                "because a hypothesis was treated as fact"),
        },
        "raster_vector_topology": topo_compare,
        # §8 / §9 — where the merged components actually leaked.
        "space_leak_maps": leaks_rec,
        # §2 — the unpaired population, classified. NOT 851 m of wall.
        "unpaired_wall_style_strokes": stroke_summary(strokes),
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
            # §13 — the freeze is asserted, not assumed. A pin that lives
            # only in a directive is not a pin.
            "freeze_guard": check_freeze(
                [f.record() for f in frozen]).record(),
            "comparison_after_freeze": control_comparisons,
            # §6 — the delta decomposed. An area delta is not an error rate.
            "disagreement_maps": disagreements,
            # §7 — which other references may be opened at all.
            "reference_mapping": reference_mapping,
            # §11 — diagnostic acceptance and production release are two
            # different verdicts, and a valid polygon earns only the first.
            "release_audit": control_release_audit,
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
