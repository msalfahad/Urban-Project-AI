"""Vector wall length per space (PA06 WS4).

Every material face is walked along its own geometry (segment parameter or
arc angle); each sample is assigned to the cell on that side of the face
and contiguous runs become boundary edges whose DEVELOPED_LENGTH comes
from the vector geometry, never from raster runs or a polygon perimeter.
The raster grid is used only to say WHICH cell lies beside a sample.
"""

from __future__ import annotations

import math

from engine.ingest import ids
from engine.ingest.spaces_v2 import _label_at

STEP_MM = 25.0
PROBE_MM = 120.0
MIN_EDGE_MM = 50.0


def _samples(p):
    """(x, y, nx, ny, s_along) samples along a segment or arc, with the unit normal (+ side) at each."""
    if p.kind == "SEGMENT":
        L = math.hypot(p.x2 - p.x1, p.y2 - p.y1)
        if L < 1e-6:
            return [], 0.0
        n = max(2, int(L / STEP_MM) + 1)
        ux, uy = (p.x2 - p.x1) / L, (p.y2 - p.y1) / L
        return [(p.x1 + ux * s, p.y1 + uy * s, -uy, ux, s) for s in (L * i / (n - 1) for i in range(n))], L
    sweep = (p.end_angle - p.start_angle) % (2 * math.pi) if p.kind == "ARC" else 2 * math.pi
    sweep = sweep or 2 * math.pi
    L = p.radius * sweep
    n = max(4, int(L / STEP_MM) + 1)
    out = []
    for i in range(n):
        a = (p.start_angle if p.kind == "ARC" else 0.0) + sweep * i / (n - 1)
        out.append((p.cx + p.radius * math.cos(a), p.cy + p.radius * math.sin(a), math.cos(a), math.sin(a), L * i / (n - 1)))
    return out, L


def _rc(meta, x, y, cell):
    return int((meta["y1"] - y) / cell), int((x - meta["x0"]) / cell)


SNAP_MM = 250.0     # a run end within this distance of a crossing material face snaps to the vector intersection (the true inner corner)


def _corner_params(p, material_segments):
    """Parameters along segment p where other material segments cross its line (inner corners)."""
    out = []
    dx, dy = p.x2 - p.x1, p.y2 - p.y1
    L = math.hypot(dx, dy)
    if L < 1e-9:
        return out
    for q in material_segments:
        if q is p:
            continue
        ex, ey = q.x2 - q.x1, q.y2 - q.y1
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        t = ((q.x1 - p.x1) * ey - (q.y1 - p.y1) * ex) / den
        u = ((q.x1 - p.x1) * dy - (q.y1 - p.y1) * dx) / den
        if -0.02 <= u <= 1.02 and -SNAP_MM / L <= t <= 1 + SNAP_MM / L:
            out.append(t * L)
    return sorted(out)


def _snap(s0, s1, corners):
    """Move each run end to the nearest crossing face within SNAP_MM (the sampled end sits a probe / raster margin away
    from the true inner corner, on either side of it)."""
    near0 = [c for c in corners if abs(c - s0) <= SNAP_MM]
    near1 = [c for c in corners if abs(c - s1) <= SNAP_MM]
    if near0:
        s0 = min(near0, key=lambda c: abs(c - s0))
    if near1:
        s1 = min(near1, key=lambda c: abs(c - s1))
    return s0, s1


def boundary_faces(view_id, prims, roles, cells, grids, sites, entity_ids):
    """Returns (rows, index): index maps (label, r, c) of every probe raster cell to the boundary edge id that produced it."""
    label, meta, cell = grids["cell_label"], grids["meta"], grids["cell"]
    cell_of = {c["RUN_LABEL_NOT_A_KEY"]: c for c in cells}
    rows, index = [], {}
    material_segments = [q for q in prims if q.kind == "SEGMENT" and roles.get(q.object_id, {}).get("MATERIAL")]
    for p in prims:
        r = roles.get(p.object_id, {})
        if not r.get("MATERIAL") and r.get("ROLE") != "GLAZING":
            continue
        samples, L = _samples(p)
        if not samples:
            continue
        for sgn, side in ((1, "+"), (-1, "-")):
            runs, cur = [], None
            for x, y, nx, ny, s in samples:
                px_, py_ = x + sgn * nx * PROBE_MM, y + sgn * ny * PROBE_MM
                lab = _label_at(label, meta, px_, py_, cell)
                if cur and cur[0] == lab:
                    cur[2] = s; cur[3].append(_rc(meta, px_, py_, cell))
                else:
                    if cur:
                        runs.append(cur)
                    cur = [lab, s, s, [_rc(meta, px_, py_, cell)]]
            if cur:
                runs.append(cur)
            corners = _corner_params(p, material_segments) if p.kind == "SEGMENT" else []
            for lab, s0, s1, rcs in runs:
                if lab == 0 or lab not in cell_of or (s1 - s0) < MIN_EDGE_MM:
                    continue
                if corners:
                    s0, s1 = _snap(s0, s1, corners)
                    s0, s1 = max(0.0, s0), min(L, s1)
                    if (s1 - s0) < MIN_EDGE_MM:
                        continue
                c = cell_of[lab]
                eid = ids.make_id("ATOMIC_FACE", view_id, entity_ids.get(p.object_id, p.object_id), side, [s0, s1], tol=25.0).replace("AF-", "BE-")
                for rc in rcs:
                    index.setdefault((lab, rc[0], rc[1]), eid)
                rows.append({"BOUNDARY_EDGE_ID": eid,
                             "SPACE_ID": c["CELL_ID"], "PHYSICAL_SPACE_ID": c.get("PHYSICAL_SPACE_ID"), "ENTITY_ID": entity_ids.get(p.object_id, p.object_id), "GEOMETRY_SOURCE": "VECTOR_" + p.kind,
                             "ROLE": r.get("ROLE"), "ROLE_STATUS": r.get("ROLE_STATUS"), "SIDE": side, "PARAM_MM": [round(s0, 1), round(s1, 1)], "ENTITY_LENGTH_MM": round(L, 1),
                             "DEVELOPED_LENGTH_MM": round(s1 - s0, 1), "MATERIAL_PRESENT": bool(r.get("MATERIAL")), "EXPOSED_TO_SPACE": True,
                             "CLEAR_FACE_OWNERSHIP": "THIS_SPACE" if r.get("MATERIAL") else "SEPARATOR_ONLY", "OPENING_SITE_ID": None,
                             "STATUS": "SOURCE_ESTABLISHED" if r.get("ROLE_STATUS") == "ESTABLISHED" else "PROVISIONAL"})
    # site chords: opening relations between cells (no material)
    for s in sites:
        if not s.get("CHORD_MM"):
            continue
        (ax, ay), (bx, by) = s["CHORD_MM"]
        mx, my, L = (ax + bx) / 2, (ay + by) / 2, math.hypot(bx - ax, by - ay)
        if L < 1e-6:
            continue
        nx, ny = -(by - ay) / L, (bx - ax) / L
        for sgn, side in ((1, "+"), (-1, "-")):
            lab = _label_at(label, meta, mx + sgn * nx * PROBE_MM, my + sgn * ny * PROBE_MM, cell)
            if lab and lab in cell_of:
                c = cell_of[lab]
                eid = ids.make_id("CLOSURE", view_id, s["SITE_ID"], side).replace("CL-", "BE-")
                n = max(2, int(L / STEP_MM) + 1)
                for i in range(n):
                    t = i / (n - 1)
                    rc = _rc(meta, ax + (bx - ax) * t + sgn * nx * PROBE_MM, ay + (by - ay) * t + sgn * ny * PROBE_MM, cell)
                    index.setdefault((lab, rc[0], rc[1]), eid)
                rows.append({"BOUNDARY_EDGE_ID": eid, "SPACE_ID": c["CELL_ID"], "PHYSICAL_SPACE_ID": c.get("PHYSICAL_SPACE_ID"),
                             "ENTITY_ID": None, "GEOMETRY_SOURCE": "SITE_CHORD", "ROLE": "OPENING_SITE:" + s["CLASS"], "ROLE_STATUS": None, "SIDE": side, "PARAM_MM": [0.0, round(L, 1)],
                             "ENTITY_LENGTH_MM": round(L, 1), "DEVELOPED_LENGTH_MM": round(L, 1), "MATERIAL_PRESENT": False, "EXPOSED_TO_SPACE": True, "CLEAR_FACE_OWNERSHIP": "NONE",
                             "OPENING_SITE_ID": s["SITE_ID"], "STATUS": s.get("RELATION_STATUS")})
    return rows, index


def _trace(mask):
    """Boundary loops of a binary mask: 8-connected components of boundary cells, each ordered by Moore neighbour tracing."""
    import numpy as np
    H, W = mask.shape
    pad = np.zeros((H + 2, W + 2), bool); pad[1:-1, 1:-1] = mask
    inner = pad[1:-1, 1:-1]
    bnd = inner & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    loops, seen = [], np.zeros_like(inner, bool)
    dirs = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]
    for r0, c0 in zip(*np.where(bnd)):
        if seen[r0, c0]:
            continue
        loop, r, c, d = [], int(r0), int(c0), 0
        for _ in range(4 * (H + W) * 4):
            loop.append((r, c)); seen[r, c] = True
            found = False
            for k in range(8):
                dd = (d + 5 + k) % 8         # start from the direction behind-left of the last move (Moore tracing)
                nr, nc = r + dirs[dd][0], c + dirs[dd][1]
                if 0 <= nr < H and 0 <= nc < W and bnd[nr, nc]:
                    r, c, d = nr, nc, dd; found = True; break
            if not found or (r, c) == (int(r0), int(c0)):
                break
        if len(loop) >= 4:
            loops.append(loop)
    return loops


def boundary_chain(cell_row, grids, index, edges_by_id):
    """Ordered boundary of one cell as edge occurrences and raster gaps, from tracing the cell's own raster boundary.
    Consecutive occurrences share a node label; every loop closes on itself.  Where no vector edge lies beside a
    boundary run, an UNRESOLVED_EDGE of raster length is inserted so the measurement layer cannot form a ring across it."""
    import numpy as np
    label, cell, lab = grids["cell_label"], grids["cell"], cell_row["RUN_LABEL_NOT_A_KEY"]
    mask = label == lab
    chains = []
    for loop in _trace(mask):
        seq = []
        for r, c in loop:
            eid = None
            for dr in (0, -1, 1, -2, 2):
                for dc in (0, -1, 1, -2, 2):
                    eid = index.get((lab, r + dr, c + dc))
                    if eid:
                        break
                if eid:
                    break
            if seq and seq[-1][0] == eid:
                seq[-1][1] += 1
            else:
                seq.append([eid, 1])
        if len(seq) > 1 and seq[0][0] == seq[-1][0]:
            seq[0][1] += seq[-1][1]; seq.pop()
        occ = {}
        chain = []
        for i, (eid, n) in enumerate(seq):
            if eid is None:
                chain.append({"EDGE_ID": f"UNRESOLVED-{cell_row['CELL_ID']}-{len(chains)}-{i}", "KIND": "UNRESOLVED_EDGE", "RASTER_CELLS": n, "length_m": round(n * cell / 1000, 3), "length_source": "RASTER_BOUNDARY_RUN"})
            else:
                k = occ.get(eid, 0); occ[eid] = k + 1
                chain.append({"EDGE_ID": eid if k == 0 else f"{eid}#{k}", "SOURCE_EDGE_ID": eid, "RASTER_CELLS": n})
        # share raster counts of repeated occurrences proportionally; single occurrences carry the vector length
        for e in chain:
            if e["KIND"] if "KIND" in e else False:
                continue
            src = edges_by_id.get(e["SOURCE_EDGE_ID"], {})
            total_cells = sum(x["RASTER_CELLS"] for x in chain if x.get("SOURCE_EDGE_ID") == e["SOURCE_EDGE_ID"])
            share = e["RASTER_CELLS"] / total_cells if total_cells else 1.0
            e["KIND"] = ("EXPOSED_COLUMN_FACE" if src.get("ROLE") == "COLUMN_FACE" else "GLAZING_BOUNDARY" if src.get("ROLE") == "GLAZING" else
                         "CURVED_MATERIAL_FACE" if src.get("GEOMETRY_SOURCE") == "VECTOR_ARC" else "SITE_CHORD" if src.get("OPENING_SITE_ID") else "PHYSICAL_WALL_FACE")
            e["length_m"] = round(src.get("DEVELOPED_LENGTH_MM", 0.0) * share / 1000, 4)
            e["length_source"] = "DRAWING_CAD_GEOMETRY"
            e["trace_ids"] = [src.get("ENTITY_ID")] if src.get("ENTITY_ID") else []
            e["OPENING_SITE_ID"] = src.get("OPENING_SITE_ID")
        for i, e in enumerate(chain):
            e["a"], e["b"] = f"N{len(chains)}.{i}", f"N{len(chains)}.{(i + 1) % len(chain)}"
        chains.append(chain)
    return chains


def wall_lengths(cells, regions, edges):
    """SPACE_WALL_LENGTH_REGISTER: vector material length per cell and per physical region, with the site relations."""
    per_cell = {}
    for e in edges:
        d = per_cell.setdefault(e["SPACE_ID"], {"MATERIAL_WALL_MM": 0.0, "COLUMN_FACE_MM": 0.0, "GLAZING_MM": 0.0, "SITE_CHORD_MM": 0.0, "EDGES": 0, "PROVISIONAL_MM": 0.0, "SITES": []})
        d["EDGES"] += 1
        if e["ROLE"] in ("MATERIAL_WALL_FACE", "MATERIAL_WALL_CENTERLINE"):
            d["MATERIAL_WALL_MM"] += e["DEVELOPED_LENGTH_MM"]
            if e["STATUS"] == "PROVISIONAL":
                d["PROVISIONAL_MM"] += e["DEVELOPED_LENGTH_MM"]
        elif e["ROLE"] == "COLUMN_FACE":
            d["COLUMN_FACE_MM"] += e["DEVELOPED_LENGTH_MM"]
        elif e["ROLE"] == "GLAZING":
            d["GLAZING_MM"] += e["DEVELOPED_LENGTH_MM"]
        elif e["OPENING_SITE_ID"]:
            d["SITE_CHORD_MM"] += e["DEVELOPED_LENGTH_MM"]; d["SITES"].append({"SITE_ID": e["OPENING_SITE_ID"], "CLASS": e["ROLE"].split(":", 1)[1], "SPAN_MM": e["DEVELOPED_LENGTH_MM"]})
    rows = []
    for c in cells:
        d = per_cell.get(c["CELL_ID"], {"MATERIAL_WALL_MM": 0.0, "COLUMN_FACE_MM": 0.0, "GLAZING_MM": 0.0, "SITE_CHORD_MM": 0.0, "EDGES": 0, "PROVISIONAL_MM": 0.0, "SITES": []})
        rows.append({"SPACE_ID": c["CELL_ID"], "KIND": "TOPOLOGY_CELL", "PHYSICAL_SPACE_ID": c.get("PHYSICAL_SPACE_ID"), "AREA_M2": c["AREA_M2"], "IN_RANGE": c["IN_RANGE"],
                     "VECTOR_MATERIAL_WALL_M": round(d["MATERIAL_WALL_MM"] / 1000, 3), "EXPOSED_COLUMN_FACE_M": round(d["COLUMN_FACE_MM"] / 1000, 3), "GLAZING_M": round(d["GLAZING_MM"] / 1000, 3),
                     "SITE_CHORD_M": round(d["SITE_CHORD_MM"] / 1000, 3), "PROVISIONAL_FACE_M": round(d["PROVISIONAL_MM"] / 1000, 3), "EDGE_COUNT": d["EDGES"], "SITES": d["SITES"],
                     "LENGTH_BASIS": "VECTOR_FACES", "POLYGON_PERIMETER_USED": False, "RASTER_RUNS_USED": False,
                     "STATUS": "SOURCE_ESTABLISHED" if d["PROVISIONAL_MM"] == 0 else "PROVISIONAL"})
    for r in regions:
        mem = [x for x in rows if x["PHYSICAL_SPACE_ID"] == r["PHYSICAL_SPACE_ID"]]
        rows.append({"SPACE_ID": r["PHYSICAL_SPACE_ID"], "KIND": "PHYSICAL_REGION", "PHYSICAL_SPACE_ID": r["PHYSICAL_SPACE_ID"], "AREA_M2": r["AREA_M2"], "IN_RANGE": r["IN_RANGE"],
                     "VECTOR_MATERIAL_WALL_M": round(sum(x["VECTOR_MATERIAL_WALL_M"] for x in mem), 3), "EXPOSED_COLUMN_FACE_M": round(sum(x["EXPOSED_COLUMN_FACE_M"] for x in mem), 3),
                     "GLAZING_M": round(sum(x["GLAZING_M"] for x in mem), 3), "SITE_CHORD_M": round(sum(x["SITE_CHORD_M"] for x in mem), 3), "PROVISIONAL_FACE_M": round(sum(x["PROVISIONAL_FACE_M"] for x in mem), 3),
                     "EDGE_COUNT": sum(x["EDGE_COUNT"] for x in mem), "SITES": [s for x in mem for s in x["SITES"]], "CELLS": r["CELLS"], "LENGTH_BASIS": "VECTOR_FACES", "POLYGON_PERIMETER_USED": False,
                     "RASTER_RUNS_USED": False, "STATUS": "SOURCE_ESTABLISHED" if all(x["STATUS"] == "SOURCE_ESTABLISHED" for x in mem) else "PROVISIONAL"})
    return rows
