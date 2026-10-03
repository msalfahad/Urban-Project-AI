"""PA08-QORTUBA-R1 measurement layer (TRADE_MEASUREMENT_REGIONS): floor regions, wall lengths, skirting and profile paths,
ceiling regions and the block / plaster / paint inputs, built from the engine's physical geometry and topology only.

The engine's raster area is declared topology-only and is never a quantity.  A floor region's area is built here by the
ARRANGEMENT method: the axis-aligned boundary lines that seal the face (band faces, opening chords, unresolved chords, outline
edges) are the cut lines of an arrangement; every arrangement cell whose centre lies inside the face contributes its exact
rectangle.  The sum is a true vector area with a written formula.  The method refuses (NOT_ESTABLISHED) when a boundary line
is not axis-aligned, when the arrangement does not reproduce the raster face within tolerance, or when the face is bounded by
anything provisional - in which case the area is PROVISIONAL and never released.
"""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

SNAP_MM = 2.0
AREA_AGREEMENT_SHARE = 0.03        # the arrangement must reproduce the raster face within this share
AREA_AGREEMENT_MIN_M2 = 0.25


def _snap(vals):
    out = []
    for v in sorted(vals):
        if not out or v - out[-1] > SNAP_MM:
            out.append(v)
    return out


def face_polygon_area(face, grid, seals):
    """(area_m2, formula_dict) by the arrangement method, or (None, reason_dict)."""
    label, meta, cell = grid["label"], grid["meta"], grid["cell"]
    L = face["RUN_LABEL_NOT_A_KEY"]
    xs, ys, skew = set(), set(), []
    for i in face.get("SEAL_INDEXES", []):
        s = seals[i]
        pts = s["PTS"]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            if abs(ax - bx) <= 1e-6 and abs(ay - by) <= 1e-6:
                continue
            if abs(ax - bx) <= 1e-6:
                xs.add(round(ax, 3))
            elif abs(ay - by) <= 1e-6:
                ys.add(round(ay, 3))
            else:
                skew.append({"SEAL_KIND": s["KIND"], "BAND_ID": s.get("BAND_ID"), "P1": [round(ax, 1), round(ay, 1)], "P2": [round(bx, 1), round(by, 1)]})
    if skew:
        return None, {"METHOD": "ARRANGEMENT_OF_BOUNDARY_LINES", "STATUS": "NOT_APPLICABLE", "WHY": "a boundary line of this face is not axis-aligned (curved or angled wall); the arrangement method measures axis-aligned regions only", "SKEW_BOUNDARIES": skew[:6]}
    xs, ys = _snap(xs), _snap(ys)
    if len(xs) < 2 or len(ys) < 2:
        return None, {"METHOD": "ARRANGEMENT_OF_BOUNDARY_LINES", "STATUS": "NOT_ESTABLISHED", "WHY": f"only {len(xs)} vertical and {len(ys)} horizontal boundary lines seal this face: not a closed region"}
    H, W = label.shape
    rects, area = [], 0.0
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            rr, cc = int((meta["y1"] - cy) / cell), int((cx - meta["x0"]) / cell)
            if 0 <= rr < H and 0 <= cc < W and int(label[rr, cc]) == L:
                a = (x1 - x0) * (y1 - y0) / 1e6
                area += a
                rects.append({"X_MM": [round(x0, 1), round(x1, 1)], "Y_MM": [round(y0, 1), round(y1, 1)], "W_MM": round(x1 - x0, 1), "D_MM": round(y1 - y0, 1), "AREA_M2": round(a, 4)})
    raster = face["AREA_GEOMETRIC_M2"]
    tol = max(AREA_AGREEMENT_MIN_M2, AREA_AGREEMENT_SHARE * raster)
    formula = {"METHOD": "ARRANGEMENT_OF_BOUNDARY_LINES", "CUT_LINES_X_MM": [round(v, 1) for v in xs], "CUT_LINES_Y_MM": [round(v, 1) for v in ys],
               "RECTANGLES": rects, "FORMULA": " + ".join(f"{r['W_MM']:.0f} x {r['D_MM']:.0f}" for r in rects) + f" = {area:.4f} m2",
               "RASTER_CROSS_CHECK_M2": raster, "DIFFERENCE_M2": round(area - raster, 4), "TOLERANCE_M2": round(tol, 4)}
    if abs(area - raster) > tol:
        formula.update({"STATUS": "NOT_ESTABLISHED", "WHY": "the arrangement of the sealing lines does not reproduce the rasterised face within tolerance: the face is not a rectilinear region of those lines"})
        return None, formula
    formula["STATUS"] = "COMPUTED"
    return area, formula


def path_rows(brows, space_face_id):
    """Boundary stretches of one face, split into the three separate path items of §10."""
    rows = [r for r in brows if r["SPACE_FACE_ID"] == space_face_id]
    out = defaultdict(list)
    for r in rows:
        kind = r["SEAL_KIND"]
        if kind in ("FACE", "COLUMN_FACE"):
            out["PHYSICAL_HOST_WALL"].append(r)
        elif kind == "OPENING_CHORD":
            out["OPENING"].append(r)
        elif kind == "JUNCTION_CHORD":
            out["JUNCTION"].append(r)
        elif kind == "UNRESOLVED_CHORD":
            out["UNRESOLVED"].append(r)
    return out


def total(rows):
    return round(sum(r["LENGTH_MM"] for r in rows), 1)
