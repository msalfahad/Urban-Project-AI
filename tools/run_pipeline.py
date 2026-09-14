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
from decimal import Decimal
from pathlib import Path

from engine.connectivity import (classify_termini, components, cycle_capacity,
                                 end_caps)
from engine.envelope import classify as classify_envelope
from engine.envelope import summary as envelope_summary
from engine.face_eligibility import (assess_components,
                                     engine_development_status,
                                     project_release_status)
from engine.frames import fit as fit_frame
from engine.geometry import VectorPdfSource, calibrate
from engine.planar import (attach_holes, build_half_edges, resolve_unbounded,
                           walk_faces)
from engine.run_manifest import RunManifest
from engine.space_boundary import (build_space_boundary, classify_gap,
                                   material_length_m, space_closes)
from engine.space_boundary import reconcile
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
    graph = build(bands_to_pairs(bands))
    noded = node_and_split(graph)
    noded.assert_length_preserved()
    comps = components(noded)
    terms = classify_termini(noded)
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
                p = classify_gap(
                    sid, name, d["axis"], d["fixed"], a, b, caps=caps,
                    bands_face_each_other=bool(d["covered"]),
                    other_sides_complete=complete >= 3)
                portals.append(p)
        gap_maps[sid] = {n: {"coverage_pct": d["coverage_pct"],
                             "gaps_mm": [round(b - a) for a, b in d["gaps"]]}
                         for n, d in sides.items()}
        boundaries[sid] = build_space_boundary(
            sid, sides, [p for p in portals if p.space_id == sid])
    o_rec = man.add("opening_detection", RUN_ID,
                    [p.record() for p in portals],
                    consumed=[("wall_graph", g_rec.output_hash)])

    # --- 5 topology: MATERIAL faces, then SPACE BOUNDARY faces ------------
    material = attach_holes(resolve_unbounded(walk_faces(
        build_half_edges(noded),
        edge_status={e.edge_id: e.validation_status for e in noded.edges})))

    # The space-boundary graph adds a zero-material edge across each probable
    # portal. It is a SEPARATE graph; the material graph is untouched.
    virtual = [p for p in portals if p.may_close_a_space]
    sb_pairs = bands_to_pairs(bands) + [
        WallPair(f"VP-{i:04d}", p.axis, p.fixed_mm - 1.0, p.fixed_mm + 1.0,
                 p.start_mm, p.end_mm)
        for i, p in enumerate(virtual, 1)]
    sb_noded = node_and_split(build(sb_pairs))
    space_faces = attach_holes(resolve_unbounded(walk_faces(
        build_half_edges(sb_noded))))
    sb_rec = man.add("space_boundary_graph", RUN_ID, sb_noded.health(),
                     consumed=[("wall_graph", g_rec.output_hash),
                               ("opening_detection", o_rec.output_hash)])
    t_rec = man.add("topology", RUN_ID,
                    {"material": material.health(),
                     "space_boundary": space_faces.health()},
                    consumed=[("wall_graph", g_rec.output_hash),
                              ("space_boundary_graph", sb_rec.output_hash)])

    # --- envelope --------------------------------------------------------
    unbounded_edges = {e for f in material.faces
                       if f.kind == "UNBOUNDED_FACE"
                       for e in f.source_wall_edge_ids}
    bounded_counts: dict = {}
    for f in material.bounded():
        for e in f.source_wall_edge_ids:
            bounded_counts[e] = bounded_counts.get(e, 0) + 1
    env = classify_envelope(noded.edges, unbounded_edge_ids=unbounded_edges,
                            bounded_edge_counts=bounded_counts)

    elig = assess_components(components=comps, termini=terms,
                             length_drift_mm=noded.health()[
                                 "length_difference_mm"])

    # §8 — every band extension audited against the supported portals.
    ext_audit = audit_extensions(bands, portals)

    # How much of each region actually fills its own bounding box. A room that
    # fills 68% of its bbox is L-shaped, and using the bbox as its expected
    # boundary invents sides that were never meant to be walls.
    import numpy as np
    fill = {}
    for sid, r in by_space.items():
        rid = next((k for k, v in regions.items()
                    if v["space_id"] == sid), None)
        if rid is None:
            continue
        ys, xs = np.where(seg.labels == rid)
        if len(xs) == 0:
            continue
        bbox_px = (xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1)
        fill[sid] = round(len(xs) / bbox_px, 3)

    man.rule_set_versions = {"23010_ceramic": "1.0", "23010_plaster": "1.0"}
    man.measurement_basis_version = "LENGTH_ONTOLOGY_V1"
    man.assert_coherent()

    return {
        "manifest": man.record(),
        "frame": frame.record(),
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
            "total": len(portals),
            "by_status": dict(Counter(p.status for p in portals)),
            "by_gap_class": dict(Counter(p.gap_class for p in portals)),
            "detail": [p.record() for p in portals],
        },
        "space_boundaries": {
            sid: {**boundary_summary(iv, [p for p in portals
                                          if p.space_id == sid]),
                  "closes": space_closes(iv),
                  "bbox_fill_ratio": fill.get(sid),
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
        "material_faces": material.health(),
        "space_boundary_faces": space_faces.health(),
        "envelope": envelope_summary(env),
        "largest_faces": [f.record() for f in sorted(
            material.bounded(), key=lambda f: -f.area_m2)[:15]],
        "space_boundary_largest_faces": [f.record() for f in sorted(
            space_faces.bounded(), key=lambda f: -f.area_m2)[:15]],
        "positive_control_verdicts": {
            sid: {
                "material_wall": (
                    f"{sum(1 for v in gap_maps[sid].values() if v['coverage_pct'] >= 95)}"
                    f" of 4 sides at 100% physical wall"),
                "gaps_mm": [g for v in gap_maps[sid].values()
                            for g in v["gaps_mm"]],
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
