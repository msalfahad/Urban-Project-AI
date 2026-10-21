"""Deterministic plan-region extraction from a normalized DWG plan copy.

Walls (solid wall layers) and door leaves / swings are rasterised on a
grid; regions are flood-filled from seed points; the region boundary is
classified cell by cell into WALL_FACE (a wall cell on the other side),
DOOR_LINE (a door-layer cell) or OPEN (another region / nothing).  Faces are
axis-aligned runs of boundary cells of one class along one side.

This yields, per region: physical host-wall face lengths (lm), open-edge
lengths, door-line lengths, the region area (cell count x cell area) and
the neighbouring regions across open edges.  Nothing here knows room names,
heights or trades.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np

WALL_LAYERS = ("1", "5", "W", "0")
DOOR_LAYERS = ("D",)


def rasterise(prims, box, cell_mm, wall_layers=WALL_LAYERS, door_layers=DOOR_LAYERS):
    """prims: iterable of (kind, id, layer, x1, y1, x2, y2, cx, cy, r, a0, a1).
    Returns (wall, door, meta) uint8 grids (rows = y up->down flipped so that
    row 0 is the top / max y)."""
    x0, y0, x1, y1 = box
    W = int(math.ceil((x1 - x0) / cell_mm)) + 1
    H = int(math.ceil((y1 - y0) / cell_mm)) + 1
    wall = np.zeros((H, W), np.uint8)
    door = np.zeros((H, W), np.uint8)
    ids = {}
    doors = []

    def cell(x, y):
        return int((y1 - y) / cell_mm), int((x - x0) / cell_mm)

    def line(grid, ax, ay, bx, by, oid):
        n = max(2, int(math.hypot(bx - ax, by - ay) / (cell_mm * 0.5)) + 1)
        for t in np.linspace(0.0, 1.0, n):
            r, c = cell(ax + (bx - ax) * t, ay + (by - ay) * t)
            if 0 <= r < H and 0 <= c < W:
                grid[r, c] = 1
                ids.setdefault((r, c), oid)

    def arc(grid, cx, cy, r, a0, a1, oid):
        if a0 is None:
            a0, a1 = 0.0, 2 * math.pi
        sweep = (a1 - a0) % (2 * math.pi) or 2 * math.pi
        n = max(4, int(r * sweep / (cell_mm * 0.5)) + 1)
        for t in np.linspace(0.0, 1.0, n):
            ang = a0 + sweep * t
            rr, cc = cell(cx + r * math.cos(ang), cy + r * math.sin(ang))
            if 0 <= rr < H and 0 <= cc < W:
                grid[rr, cc] = 1
                ids.setdefault((rr, cc), oid)

    for p in prims:
        kind, oid, lay = p[0], p[1], p[2]
        if lay in wall_layers:
            g = wall
        elif lay in door_layers:
            g = door
        else:
            continue
        if kind == "SEGMENT":
            ax, ay, bx, by = p[3], p[4], p[5], p[6]
            if max(ax, bx) < x0 or min(ax, bx) > x1 or max(ay, by) < y0 or min(ay, by) > y1:
                continue
            line(g, ax, ay, bx, by, oid)
        else:
            cx, cy, r = p[7], p[8], p[9]
            if cx + r < x0 or cx - r > x1 or cy + r < y0 or cy - r > y1:
                continue
            if kind == "CIRCLE":
                arc(g, cx, cy, r, None, None, oid)
            elif lay in door_layers and p[10] is not None:
                # a door swing: only the CLOSED position (hinge -> the arc end that meets the wall)
                # is drawn, so the opening is closed by a line of exactly the leaf width and the
                # swing / open leaf never become region boundary
                doors.append((cx, cy, r, p[10], p[11], oid))
            else:
                arc(g, cx, cy, r, p[10], p[11], oid)
    def near_wall(x, y, reach=3):
        rr, cc = cell(x, y)
        for dr in range(-reach, reach + 1):
            for dc in range(-reach, reach + 1):
                if 0 <= rr + dr < H and 0 <= cc + dc < W and wall[rr + dr, cc + dc]:
                    return True
        return False
    for cx, cy, r, a0, a1, oid in doors:
        ends = [(a, near_wall(cx + r * math.cos(a), cy + r * math.sin(a))) for a in (a0, a1)]
        chosen = [a for a, ok in ends if ok] or [a for a, _ in ends]
        for ang in chosen:
            line(door, cx, cy, cx + r * math.cos(ang), cy + r * math.sin(ang), oid)
    return wall, door, {"W": W, "H": H, "x0": x0, "y1": y1, "cell": cell_mm, "ids": ids}


def flood(wall, door, seeds, meta, max_cells=400000):
    """seeds: {seed_id: (x_mm, y_mm)}.  Returns label grid (int32, 0 = unassigned,
    -1 = barrier) and {seed_id: label}.  Seeds inside one connected free
    region share one label (the region is OPEN between them)."""
    H, W = wall.shape
    barrier = (wall > 0) | (door > 0)
    label = np.zeros((H, W), np.int32)
    label[barrier] = -1
    seed_label = {}
    nxt = 1
    for sid, (x, y) in seeds.items():
        r, c = int((meta["y1"] - y) / meta["cell"]), int((x - meta["x0"]) / meta["cell"])
        if not (0 <= r < H and 0 <= c < W) or barrier[r, c]:
            seed_label[sid] = None
            continue
        if label[r, c] > 0:
            seed_label[sid] = int(label[r, c])
            continue
        lab = nxt
        nxt += 1
        q = deque([(r, c)])
        label[r, c] = lab
        n = 0
        while q:
            rr, cc = q.popleft()
            n += 1
            if n > max_cells:
                break
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                r2, c2 = rr + dr, cc + dc
                if 0 <= r2 < H and 0 <= c2 < W and label[r2, c2] == 0:
                    label[r2, c2] = lab
                    q.append((r2, c2))
        seed_label[sid] = lab
    return label, seed_label


def boundary_faces(label, wall, door, lab, meta, min_run_cells=3):
    """Boundary runs of region `lab`.  For each of the four sides of every
    region cell, the neighbour is WALL, DOOR, OTHER_REGION or EDGE (grid
    edge / unassigned).  Runs of the same class along one side and one
    row/column are merged into faces with lengths in metres."""
    H, W = label.shape
    cell = meta["cell"]
    faces = []
    sides = {"N": (-1, 0), "S": (1, 0), "W": (0, -1), "E": (0, 1)}
    for side, (dr, dc) in sides.items():
        runs = {}
        rs, cs = np.where(label == lab)
        for r, c in zip(rs, cs):
            r2, c2 = r + dr, c + dc
            if 0 <= r2 < H and 0 <= c2 < W and label[r2, c2] == lab:
                continue
            if not (0 <= r2 < H and 0 <= c2 < W):
                cls, other = "EDGE", None
            elif wall[r2, c2]:
                cls, other = "WALL", meta["ids"].get((r2, c2))
            elif door[r2, c2]:
                cls, other = "DOOR", meta["ids"].get((r2, c2))
            elif label[r2, c2] > 0 and label[r2, c2] != lab:
                cls, other = "OPEN", int(label[r2, c2])
            else:
                cls, other = "OPEN", None
            key = (r if side in ("N", "S") else c)
            runs.setdefault((side, key), []).append((c if side in ("N", "S") else r, cls, other))
        for (sd, key), cells in runs.items():
            cells.sort()
            cur = None
            for pos, cls, other in cells:
                if cur and cur["cls"] == cls and pos == cur["end"] + 1:
                    cur["end"] = pos
                    if other is not None:
                        cur["ids"].add(other)
                else:
                    if cur:
                        faces.append(cur)
                    cur = {"side": sd, "key": key, "start": pos, "end": pos, "cls": cls, "ids": set([other]) if other is not None else set()}
            if cur:
                faces.append(cur)
    out = []
    for f in faces:
        n = f["end"] - f["start"] + 1
        if n < min_run_cells:
            continue
        if f["side"] in ("N", "S"):
            y = meta["y1"] - f["key"] * cell
            xa, xb = meta["x0"] + f["start"] * cell, meta["x0"] + (f["end"] + 1) * cell
            geom = {"AXIS": "x", "AT_MM": round(y, 1), "FROM_MM": round(xa, 1), "TO_MM": round(xb, 1)}
        else:
            x = meta["x0"] + f["key"] * cell
            ya, yb = meta["y1"] - (f["end"] + 1) * cell, meta["y1"] - f["start"] * cell
            geom = {"AXIS": "y", "AT_MM": round(x, 1), "FROM_MM": round(ya, 1), "TO_MM": round(yb, 1)}
        out.append({"SIDE": f["side"], "CLASS": f["cls"], "LENGTH_M": round(n * cell / 1000, 3), "GEOM": geom,
                    "ENTITY_IDS": sorted(str(i) for i in f["ids"] if isinstance(i, str)), "OTHER_REGIONS": sorted(i for i in f["ids"] if isinstance(i, int))})
    return out


def region_area_m2(label, lab, cell_mm):
    return round(float((label == lab).sum()) * (cell_mm / 1000) ** 2, 3)


def merge_collinear(faces, gap_cells_m=0.0):
    """Merge faces of the same side / class / axis position that touch."""
    faces = sorted(faces, key=lambda f: (f["SIDE"], f["CLASS"], f["GEOM"]["AT_MM"], f["GEOM"]["FROM_MM"]))
    out = []
    for f in faces:
        if out:
            g = out[-1]
            if (g["SIDE"], g["CLASS"], g["GEOM"]["AT_MM"]) == (f["SIDE"], f["CLASS"], f["GEOM"]["AT_MM"]) and abs(g["GEOM"]["TO_MM"] - f["GEOM"]["FROM_MM"]) <= gap_cells_m * 1000 + 1e-6:
                g["GEOM"]["TO_MM"] = f["GEOM"]["TO_MM"]
                g["LENGTH_M"] = round(g["LENGTH_M"] + f["LENGTH_M"], 3)
                g["ENTITY_IDS"] = sorted(set(g["ENTITY_IDS"]) | set(f["ENTITY_IDS"]))
                g["OTHER_REGIONS"] = sorted(set(g["OTHER_REGIONS"]) | set(f["OTHER_REGIONS"]))
                continue
        out.append(dict(f, GEOM=dict(f["GEOM"])))
    return out
