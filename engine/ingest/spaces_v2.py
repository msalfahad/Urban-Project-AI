"""Physical spaces v3 (PA06 WS3/WS4): topology cells and physical regions.

Physical separators (material faces, column faces, glazing, confirmed
door / window chords) bound PHYSICAL REGIONS.  Topology CELLS additionally
stop at every unresolved or passage site, so an open-plan region keeps
its cells for measurement while the physical record says the cells are one
region.  Neither cells nor regions are created from text.
"""

from __future__ import annotations

import numpy as np

from engine import plan_regions as PR
from engine.ingest import ids

CELL_MM = 50
MIN_AREA_M2, MAX_AREA_M2 = 0.8, 2500.0
SEPARATOR_ROLES = ("MATERIAL_WALL_FACE", "MATERIAL_WALL_CENTERLINE", "COLUMN_FACE", "GLAZING")


def _tuples(prims, roles, allowed):
    out = []
    for p in prims:
        if roles.get(p.object_id, {}).get("ROLE") not in allowed:
            continue
        if p.kind == "SEGMENT":
            out.append(("SEGMENT", p.object_id, "SEP", p.x1, p.y1, p.x2, p.y2, None, None, None, None, None))
        elif p.kind == "ARC":
            out.append(("ARC", p.object_id, "SEP", None, None, None, None, p.cx, p.cy, p.radius, p.start_angle, p.end_angle))
        elif p.kind == "CIRCLE":
            out.append(("CIRCLE", p.object_id, "SEP", None, None, None, None, p.cx, p.cy, p.radius, None, None))
    return out


def _flood(tuples, box, cell):
    wall, door, meta = PR.rasterise(tuples, box, cell, wall_layers=("SEP",), door_layers=("__CHORD__",))
    seeds, k = {}, 0
    for x in np.arange(box[0] + 500, box[2], 1000):
        for y in np.arange(box[1] + 500, box[3], 1000):
            seeds[k] = (float(x), float(y)); k += 1
    label, _ = PR.flood(wall, door, seeds, meta, max_cells=6_000_000)
    return label, meta


THIN_MM = 300.0     # a cell that vanishes under a 300 mm erosion is the inside of a wall band or a slit, not a space


def _thin(mask, n):
    """True when a binary mask is emptied by n steps of 4-neighbour erosion (pure numpy)."""
    m = mask.copy()
    for _ in range(n):
        if not m.any():
            return True
        e = m.copy()
        e[1:, :] &= m[:-1, :]; e[:-1, :] &= m[1:, :]; e[:, 1:] &= m[:, :-1]; e[:, :-1] &= m[:, 1:]
        e[0, :] = False; e[-1, :] = False; e[:, 0] = False; e[:, -1] = False
        m = e
    return not m.any()


def _label_at(label, meta, x, y, cell):
    r, c = int((meta["y1"] - y) / cell), int((x - meta["x0"]) / cell)
    H, W = label.shape
    return int(label[r, c]) if 0 <= r < H and 0 <= c < W else 0


def build(view, prims, roles, sites, cell=CELL_MM):
    """Returns (cells, regions, grids)."""
    x0, y0, x1, y1 = view["BBOX_MM"]
    box = (x0 - 500, y0 - 500, x1 + 500, y1 + 500)
    sep = _tuples(prims, roles, SEPARATOR_ROLES)
    phys = list(sep) + [("SEGMENT", "CHORD:" + s["SITE_ID"], "__CHORD__", *s["CHORD_MM"][0], *s["CHORD_MM"][1], None, None, None, None, None) for s in sites if s.get("PHYSICAL_SEPARATOR") and s.get("CHORD_MM")]
    cellb = list(sep) + [("SEGMENT", "CHORD:" + s["SITE_ID"], "__CHORD__", *s["CHORD_MM"][0], *s["CHORD_MM"][1], None, None, None, None, None) for s in sites if s.get("TOPOLOGY_CELL_BARRIER") and s.get("CHORD_MM")]
    plabel, meta = _flood(phys, box, cell)
    clabel, _ = _flood(cellb, box, cell)
    touches_edge = set(np.unique(np.concatenate([clabel[0], clabel[-1], clabel[:, 0], clabel[:, -1]])))
    cells = []
    labs, counts = np.unique(clabel[clabel > 0], return_counts=True)
    for lab, n in zip(labs, counts):
        area = float(n) * (cell / 1000) ** 2
        rs, cs = np.where(clabel == lab)
        r0, c0 = rs.mean(), cs.mean()
        kk = int(np.argmin((rs - r0) ** 2 + (cs - c0) ** 2))
        ax, ay = meta["x0"] + cs[kk] * cell + cell / 2, meta["y1"] - rs[kk] * cell - cell / 2
        region_lab = _label_at(plabel, meta, ax, ay, cell)
        exterior = int(lab) in touches_edge
        r0_, r1_, c0_, c1_ = rs.min(), rs.max() + 1, cs.min(), cs.max() + 1
        thin = _thin(clabel[r0_:r1_, c0_:c1_] == lab, int(THIN_MM / cell))
        cells.append({"CELL_ID": ids.region_id(view["VIEW_ID"], (ax, ay), area), "VIEW": view["VIEW_ID"], "RUN_LABEL_NOT_A_KEY": int(lab), "ANCHOR_MM": [round(float(ax), 1), round(float(ay), 1)],
                      "AREA_M2": round(area, 3), "REGION_RUN_LABEL": region_lab, "TOUCHES_VIEW_EDGE": exterior, "THIN_SLIT_OR_WALL_INTERIOR": thin,
                      "IN_RANGE": MIN_AREA_M2 <= area <= MAX_AREA_M2 and not exterior and not thin})
    # regions: union of cells sharing a physical label
    by_region = {}
    for c in cells:
        by_region.setdefault(c["REGION_RUN_LABEL"], []).append(c)
    regions = []
    for rl, members in by_region.items():
        if rl == 0:
            continue
        members.sort(key=lambda c: -c["AREA_M2"])
        anchor = members[0]["ANCHOR_MM"]
        area = round(sum(c["AREA_M2"] for c in members), 3)
        exterior = any(c["TOUCHES_VIEW_EDGE"] for c in members)
        thin = all(c["THIN_SLIT_OR_WALL_INTERIOR"] for c in members)
        rid = ids.space_id(view["VIEW_ID"], anchor, [c["CELL_ID"] for c in members])
        for c in members:
            c["PHYSICAL_SPACE_ID"] = rid
        regions.append({"PHYSICAL_SPACE_ID": rid, "VIEW": view["VIEW_ID"], "ANCHOR_MM": anchor, "AREA_M2": area, "CELLS": [c["CELL_ID"] for c in members], "CELL_COUNT": len(members),
                        "TOUCHES_VIEW_EDGE": exterior, "IN_RANGE": MIN_AREA_M2 <= area <= MAX_AREA_M2 and not exterior and not thin, "RUN_LABEL_NOT_A_KEY": int(rl),
                        "TOPOLOGY_STATUS": "SINGLE_CELL" if len(members) == 1 else "OPEN_GROUP_OF_CELLS", "SEMANTIC_IDENTITY": None, "FUNCTIONAL_ZONES": []})
    grids = {"cell_label": clabel, "region_label": plabel, "meta": meta, "cell": cell}
    return cells, regions, grids
