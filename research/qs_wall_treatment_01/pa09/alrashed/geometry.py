"""Exact rectilinear room recovery for the Al Rashed villa, inside the three plan windows the PDF plots.

The engine's planar faces are rasterised at 50 mm and say so: they establish topology, never a quantity.  This
module recovers the same rooms as exact polygons instead, which it can do because the building is drawn wholly
axis-aligned: every wall face lands on one of a finite set of x or y coordinates, so the plan is exactly a grid of
rectangles and a room is exactly a set of whole grid cells.  No cell is a fraction of a millimetre wrong.

Walls are barriers between cells rather than filled regions, so a wall's own two faces bound a one-cell-wide strip
whose width IS the wall thickness - which is how the thicknesses come out of the drawing rather than an assumption.
"""

from __future__ import annotations

import collections
import json
import math
import re
from pathlib import Path

DECODE = "data/runs/cad_convert/ALRASHED_ARCHITECTURAL.json"

# The current set.  Row R3 of the sheet layout: every dimension each PDF page prints is present in these windows
# with matching multiplicity (score 1.000), which is what identifies them as the plans that were plotted.
WINDOWS = {
    "FIRST":    (315.0, 347.0, 146.0, 182.0),
    "GROUND":   (353.0, 392.0, 146.0, 182.0),
    "BASEMENT": (395.0, 434.0, 146.0, 182.0),
}
WALL_LAYERS = ("WALL-EWAN",)
COLUMN_LAYERS = ("col.str",)
DOOR_LAYERS = ("DOOR-EWAN",)
WINDOW_LAYERS = ("WIN - EWAN",)
STAIR_LAYERS = ("STAIR", "STAIR - ANO - EWAN", "SRAIR - HIDDEN LINE - EWAN")
BOUNDARY_LAYERS = ("BOUN-EWAN",)
ROOF_LAYERS = ("ROOF-EWAN",)

TOL = 1e-6
SNAP_MM = 5.0            # two faces within 5 mm are the same face; the drawing is authored to the millimetre
MAX_WALL_M = 0.60        # a strip wider than this is a room, not a wall
MIN_ROOM_M2 = 0.30       # below this a cell island is a drafting artefact, not a space
MAX_CLOSURE_M = 3.00     # the widest gap in a wall line that is an opening rather than the wall simply ending


def _clean(s):
    s = re.sub(r"\{\\[^;}]*;", "", s or "")
    return s.replace("\\P", " ").replace("}", "").replace("\\A1;", "").strip()


def load(decode=DECODE):
    d = json.loads(Path(decode).read_text("utf-8"))
    layers = {}
    for o in d["OBJECTS"]:
        if o.get("object") == "LAYER":
            h = o.get("handle")
            if h:
                layers[tuple(h)[-1]] = _clean(o.get("name") or "")
    ents, cur = [], None
    for o in d["OBJECTS"]:
        e = o.get("entity")
        if e == "BLOCK":
            cur = 1
            continue
        if e == "ENDBLK":
            cur = None
            continue
        if cur is None and e:
            l = o.get("layer")
            o = dict(o)
            o["_layer"] = layers.get(tuple(l)[-1]) if l else None
            ents.append(o)
    return ents


def _segments(ents, layers, window):
    """Axis-aligned segments on the given layers inside the window, in metres."""
    x0, x1, y0, y1 = window
    out = []
    for o in ents:
        if o["_layer"] not in layers:
            continue
        pairs = []
        if o["entity"] == "LINE":
            a, b = o.get("start"), o.get("end")
            if a and b:
                pairs = [(a, b)]
        elif o["entity"] == "LWPOLYLINE":
            pts = o.get("points") or []
            pairs = list(zip(pts, pts[1:]))
            if o.get("flag", 0) & 1 and len(pts) > 2:
                pairs.append((pts[-1], pts[0]))
        for a, b in pairs:
            if not (x0 <= a[0] <= x1 and y0 <= a[1] <= y1 and x0 <= b[0] <= x1 and y0 <= b[1] <= y1):
                continue
            dx, dy = b[0] - a[0], b[1] - a[1]
            if abs(dx) < TOL and abs(dy) < TOL:
                continue
            if abs(dx) < TOL:
                out.append(("V", a[0], min(a[1], b[1]), max(a[1], b[1])))
            elif abs(dy) < TOL:
                out.append(("H", a[1], min(a[0], b[0]), max(a[0], b[0])))
    return out


def _snap(values, tol_m):
    """Collapse coordinates that are the same face drawn twice."""
    vals = sorted(values)
    out, cur = [], [vals[0]]
    for v in vals[1:]:
        if v - cur[-1] <= tol_m:
            cur.append(v)
        else:
            out.append(sum(cur) / len(cur))
            cur = [v]
    out.append(sum(cur) / len(cur))
    return out


def closures(walls):
    """Virtual closures across the openings in each wall line.

    A door is a hole in a wall, not the end of one: the wall line runs on past it and the room on either side stops
    at the jamb.  So for each face line the segments on it are sorted and any gap up to a door-or-window width is
    spanned.  The closure bounds the room; it is not wall material and is never measured as any.
    """
    out = []
    by_line = collections.defaultdict(list)
    for kind, pos, lo, hi in walls:
        by_line[(kind, round(pos, 3))].append((lo, hi))
    for (kind, pos), spans in by_line.items():
        spans.sort()
        merged = [list(spans[0])]
        for lo, hi in spans[1:]:
            if lo <= merged[-1][1] + TOL:
                merged[-1][1] = max(merged[-1][1], hi)
            else:
                merged.append([lo, hi])
        for a, b in zip(merged, merged[1:]):
            gap = b[0] - a[1]
            if 0 < gap <= MAX_CLOSURE_M:
                out.append((kind, pos, a[1], b[0]))
    return out


def grid(ents, window):
    """The exact rectilinear grid of the plan, and which cell walls separate which."""
    walls = _segments(ents, WALL_LAYERS, window)
    cols = _segments(ents, COLUMN_LAYERS, window)
    clos = closures(walls)
    barriers = walls + cols + clos
    if not barriers:
        return None
    xs = _snap([s[1] for s in barriers if s[0] == "V"], SNAP_MM / 1000.0)
    ys = _snap([s[1] for s in barriers if s[0] == "H"], SNAP_MM / 1000.0)
    return {"XS": xs, "YS": ys, "BARRIERS": barriers, "WALLS": walls, "COLUMNS": cols,
            "CLOSURES": clos, "WINDOW": window}


def _snap_to(v, axis, tol_m):
    i = min(range(len(axis)), key=lambda k: abs(axis[k] - v))
    return i if abs(axis[i] - v) <= tol_m else None


def rooms(g):
    """Connected components of grid cells, each an exact rectilinear region."""
    xs, ys = g["XS"], g["YS"]
    nx, ny = len(xs) - 1, len(ys) - 1
    if nx <= 0 or ny <= 0:
        return []
    tol = SNAP_MM / 1000.0
    # a barrier blocks the cell edge it lies on, along the span it covers
    blockV = collections.defaultdict(set)     # x-index -> set of y cell indices blocked
    blockH = collections.defaultdict(set)
    for kind, pos, lo, hi in g["BARRIERS"]:
        if kind == "V":
            i = _snap_to(pos, xs, tol)
            if i is None:
                continue
            for j in range(ny):
                if ys[j] >= lo - tol and ys[j + 1] <= hi + tol:
                    blockV[i].add(j)
        else:
            j = _snap_to(pos, ys, tol)
            if j is None:
                continue
            for i in range(nx):
                if xs[i] >= lo - tol and xs[i + 1] <= hi + tol:
                    blockH[j].add(i)
    seen = [[False] * ny for _ in range(nx)]
    comps = []
    for si in range(nx):
        for sj in range(ny):
            if seen[si][sj]:
                continue
            stack, cells = [(si, sj)], []
            seen[si][sj] = True
            while stack:
                i, j = stack.pop()
                cells.append((i, j))
                if i > 0 and not seen[i - 1][j] and j not in blockV.get(i, ()):
                    seen[i - 1][j] = True; stack.append((i - 1, j))
                if i < nx - 1 and not seen[i + 1][j] and j not in blockV.get(i + 1, ()):
                    seen[i + 1][j] = True; stack.append((i + 1, j))
                if j > 0 and not seen[i][j - 1] and i not in blockH.get(j, ()):
                    seen[i][j - 1] = True; stack.append((i, j - 1))
                if j < ny - 1 and not seen[i][j + 1] and i not in blockH.get(j + 1, ()):
                    seen[i][j + 1] = True; stack.append((i, j + 1))
            area = sum((xs[i + 1] - xs[i]) * (ys[j + 1] - ys[j]) for i, j in cells)
            bx0 = min(xs[i] for i, _ in cells); bx1 = max(xs[i + 1] for i, _ in cells)
            by0 = min(ys[j] for _, j in cells); by1 = max(ys[j + 1] for _, j in cells)
            comps.append({"CELLS": cells, "AREA_M2": round(area, 4), "BBOX": [bx0, by0, bx1, by1],
                          "WIDTH_M": round(bx1 - bx0, 4), "DEPTH_M": round(by1 - by0, 4),
                          "CELL_COUNT": len(cells)})
    return comps


def wall_cells(g):
    """Grid cells that ARE wall material, with the thickness and length each one contributes.

    Walls are barriers between cells, so the strip between a wall's two faces is itself a cell: narrow, blocked on
    both of its long sides, and exactly as wide as the wall is thick.  Reading the wall out of the grid this way
    means the thickness is measured from the drawing rather than assumed, and every millimetre of wall belongs to
    exactly one cell - so nothing is counted twice where walls meet.
    """
    xs, ys = g["XS"], g["YS"]
    nx, ny = len(xs) - 1, len(ys) - 1
    tol = SNAP_MM / 1000.0
    blockV, blockH = collections.defaultdict(set), collections.defaultdict(set)
    for kind, pos, lo, hi in g["WALLS"] + g["COLUMNS"]:
        if kind == "V":
            i = _snap_to(pos, xs, tol)
            if i is None:
                continue
            for j in range(ny):
                if ys[j] >= lo - tol and ys[j + 1] <= hi + tol:
                    blockV[i].add(j)
        else:
            j = _snap_to(pos, ys, tol)
            if j is None:
                continue
            for i in range(nx):
                if xs[i] >= lo - tol and xs[i + 1] <= hi + tol:
                    blockH[j].add(i)
    out = []
    for i in range(nx):
        w = xs[i + 1] - xs[i]
        for j in range(ny):
            h = ys[j + 1] - ys[j]
            v = w <= MAX_WALL_M and j in blockV.get(i, ()) and j in blockV.get(i + 1, ())
            hz = h <= MAX_WALL_M and i in blockH.get(j, ()) and i in blockH.get(j + 1, ())
            if v and (not hz or w <= h):
                out.append({"I": i, "J": j, "AXIS": "V", "THICKNESS_M": round(w, 4), "LENGTH_M": round(h, 4),
                            "AREA_M2": round(w * h, 6),
                            "FACES": [("LEFT", i - 1, j), ("RIGHT", i + 1, j)]})
            elif hz:
                out.append({"I": i, "J": j, "AXIS": "H", "THICKNESS_M": round(h, 4), "LENGTH_M": round(w, 4),
                            "AREA_M2": round(w * h, 6),
                            "FACES": [("BELOW", i, j - 1), ("ABOVE", i, j + 1)]})
    return out
