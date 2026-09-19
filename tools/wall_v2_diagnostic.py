"""Wall extraction V2 — measure the representation, then rebuild the graph.

    python3 -m tools.wall_v2_diagnostic [--json OUT]

Order matters and is the point: the representation is measured, the pairing
rejection reasons are counted on the PROBABLE WALL population rather than on
thousands of glyph strokes, bands are built, and only then is a graph rebuilt
and the positive controls re-run.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

import numpy as np

from engine.connectivity import (classify_termini, components, end_caps)
from engine.frames import fit as fit_frame
from engine.geometry import VectorPdfSource, calibrate
from engine.local_topology import analyse_space, positive_controls
from engine.planar import (attach_holes, build_half_edges, resolve_unbounded,
                           walk_faces)
from engine.topology import WallPair
from engine.vector_source import read
from engine.wall_bands import (DOUBLE_FACE_WALL, VALIDATED,
                               build_bands, single_face_candidates,
                               single_face_candidates as _sfc, summary)
from engine.wall_graph import build
from engine.wall_noding import node_and_split

PDF = "data/golden/23010/inputs/AR-00_MAR2023.pdf"
SPACE_MAP = "data/golden/23010/inputs/space_map_23010_2f.json"

# The pen the sheet's long strokes use. Measured, not chosen — and used only as
# ONE evidence family. A heavy pen is not a wall.
def wall_pen_of(drawing) -> float | None:
    """The pen weight carrying the most stroked length in long marks."""
    acc: dict[float, float] = {}
    for s in drawing.axis_aligned():
        if s.path_type == "STROKE" and s.length_mm >= 1000:
            acc[s.stroke_width_pt] = acc.get(s.stroke_width_pt, 0.0) + s.length_mm
    return max(acc, key=acc.get) if acc else None


def probable_wall_faces(drawing, frame, wall_mask, px_mm, *, pen=None):
    """The population worth asking pairing questions about.

    NOT "the heavy pen population". A face qualifies on ANY of: the sheet's
    wall pen, or strong raster wall-mask support, or sheer length. Restricting
    to one signal would make the rejection histogram a study of that signal.
    """
    out = []
    for s in drawing.axis_aligned():
        if s.path_type != "STROKE" or s.length_mm < 300:
            continue
        support = raster_ratio(frame, wall_mask, px_mm,
                               s.axis, s.fixed_mm,
                               min(s.start_mm, s.end_mm),
                               max(s.start_mm, s.end_mm))
        if (pen is not None and s.stroke_width_pt == pen) or support >= 0.6 \
                or s.length_mm >= 2000:
            out.append(s)
    return out


def raster_ratio(frame, wall_mask, px_mm, axis, fixed, lo, hi,
                 samples: int = 14) -> float:
    """Share of sampled points along a line that land on raster wall ink.

    ONE evidence family. Raster evidence alone can never validate a vector
    wall: the mask is ink, and ink is furniture, hatch and text as well as
    walls.
    """
    h, w = wall_mask.shape
    hit = tot = 0
    for t in np.linspace(0.1, 0.9, samples):
        at = lo + (hi - lo) * t
        x, y = (at, fixed) if axis == "H" else (fixed, at)
        rx, ry = frame.to_raster(x, y)
        c, r = int(rx / px_mm), int(ry / px_mm)
        if 0 <= r < h and 0 <= c < w:
            tot += 1
            hit += bool(wall_mask[r, c])
    return hit / tot if tot else 0.0


def bands_to_pairs(bands):
    """Wall bands become graph edges. Only bands with a measured separation."""
    out = []
    for i, b in enumerate(bands, 1):
        if b.wall_face_separation_mm is None:
            continue
        half = b.wall_face_separation_mm / 2
        out.append(WallPair(f"WP-{i:04d}", b.axis,
                            b.centreline_mm - half, b.centreline_mm + half,
                            b.start_mm, b.end_mm))
    return out


def run(pdf: str = PDF) -> dict:
    drawing = read(pdf)
    src = VectorPdfSource(pdf, calibrate(887.82, 40000, 554.94, 25000))
    seg = src.segmentation(0, drawing_id="AR-00", revision="v2")
    px = float(seg.px_mm)
    heavy = [s for s in drawing.axis_aligned()
             if s.stroke_width_pt == 1.14 and s.length_mm > 1000]
    frame = fit_frame(heavy, seg.wall_mask, px)

    pen = wall_pen_of(drawing)
    faces = probable_wall_faces(drawing, frame, seg.wall_mask, px, pen=pen)
    caps = end_caps(drawing.axis_aligned())

    def support(axis, centre, lo, hi):
        return raster_ratio(frame, seg.wall_mask, px, axis, centre, lo, hi)

    bands, rejections = build_bands(faces, caps=caps, wall_pen=pen,
                                    raster_support=support)
    _ = rejections
    singles = single_face_candidates(rejections, faces, raster_support=support)

    # --- heavy-pen precision / support study ---------------------------------
    all_pen = [s for s in drawing.axis_aligned()
               if s.stroke_width_pt == pen and s.path_type == "STROKE"]
    pen_in_band = {f for b in bands for f in b.face_a_ids + b.face_b_ids}
    pen_study = {
        "wall_pen_pt": pen,
        "strokes_at_wall_pen": len(all_pen),
        "bands_using_the_wall_pen": sum(
            1 for b in bands if "DRAWN_WITH_THE_SHEET_WALL_PEN"
            in b.supporting_evidence),
        "bands_total": len(bands),
        "share_of_bands_at_wall_pen": (
            round(sum(1 for b in bands
                      if "DRAWN_WITH_THE_SHEET_WALL_PEN"
                      in b.supporting_evidence) / len(bands), 3)
            if bands else None),
        "wall_pen_strokes_that_became_a_band_face": sum(
            1 for s in all_pen if s.segment_id in pen_in_band),
        "precision_of_the_pen_as_a_wall_signal": (
            round(sum(1 for s in all_pen if s.segment_id in pen_in_band)
                  / len(all_pen), 3) if all_pen else None),
        "note": ("the pen is WALL_STYLE_EVIDENCE, one family among four. "
                 "Precision below 1.0 is the measure of why it may not "
                 "classify alone"),
    }

    # --- rebuild the graph from bands ---------------------------------------
    pairs = bands_to_pairs([b for b in bands])
    graph = build(pairs)
    noded = node_and_split(graph)
    noded.assert_length_preserved()
    comps = components(noded)
    terms = classify_termini(noded)

    res = attach_holes(resolve_unbounded(walk_faces(
        build_half_edges(noded),
        edge_status={e.edge_id: e.validation_status for e in noded.edges})))

    # --- positive controls, compared AFTER generation ------------------------
    sm = json.loads(Path(SPACE_MAP).read_text(encoding="utf-8"))
    by_region = {s["region"]: s for s in sm["spaces"]}
    regions = {}
    for r in src.regions(0, min_m2=0.3):
        sp = by_region.get(r.id, {})
        vb = frame.bbox_to_vector(r.bbox_mm)
        cx, cy = frame.to_vector(r.centroid_px[0] * px, r.centroid_px[1] * px)
        regions[r.id] = {"bbox_mm": vb, "area_m2": float(r.area_m2),
                         "centroid_mm": (cx, cy),
                         "space_id": sp.get("space_id", ""),
                         "room_type": sp.get("room_type", ""),
                         "scope": sp.get("scope", "")}
    controls = positive_controls(res.bounded(), regions,
                                 ["BTH-05", "BED-01", "STR-01", "OPEN-01"])
    hard = {}
    by_space = {r["space_id"]: r for r in regions.values() if r["space_id"]}
    for sid in ("BTH-01", "BTH-02", "BTH-03", "WSH-01", "BED-04"):
        r = by_space.get(sid)
        if r:
            hard[sid] = analyse_space(sid, r["bbox_mm"], edges=noded.edges,
                                      termini=terms, caps=caps)

    return {
        "frame": frame.record(),
        "population": {
            "axis_aligned_segments": len(drawing.axis_aligned()),
            "probable_wall_faces": len(faces),
            "end_caps": len(caps),
        },
        "bands": summary(bands, rejections),
        "single_face_candidates": {
            "count": len(singles),
            "note": ("kept as candidates and NEVER mirrored by an assumed "
                     "thickness"),
        },
        "heavy_pen_study": pen_study,
        "graph": noded.health(),
        "components": {"total": len(comps),
                       "with_cycles": sum(1 for c in comps
                                          if c.independent_cycles > 0),
                       "total_cycles": sum(c.independent_cycles
                                           for c in comps)},
        "faces": res.health(),
        "largest_faces": [f.record() for f in sorted(
            res.bounded(), key=lambda f: -f.area_m2)[:12]],
        "band_sample": [b.record() for b in bands[:60]],
        "rejection_sample": [r.record() for r in rejections[:60]],
        "positive_controls": controls,
        "hard_cases": {k: {"summary": v["summary"],
                           "sides": v["sides"]} for k, v in hard.items()},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    rep = run()
    text = json.dumps(rep, indent=2, sort_keys=True, default=str)
    print(text)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(text + "\n")


if __name__ == "__main__":
    main()
