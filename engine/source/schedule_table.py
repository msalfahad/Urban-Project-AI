"""SCHEDULE TABLE READER (V1) - a drawn schedule (grid lines + values) as rows and cells, fail closed.

Input
    items     the value-bearing records inside the table: TEXT values and block ATTRIBUTE values, each with its
              source key, value, insertion point and (for attributes) tag and owner insert. The tag is EVIDENCE only:
              a value belongs to the column it is DRAWN in (an attribute tagged 'W' may sit under the header 'L').
    h_lines   horizontal grid segments (y, x0, x1, key); v_lines vertical grid segments (x, y0, y1, key).

Bands      every distinct grid y (clustered within eps) cuts the table into horizontal bands, top to bottom.
Cells      inside one band the vertical lines that CROSS the band's middle bound its cells; a group header cell
           therefore spans the child columns whose separators stop below it.
Merges     a cell continues the cell above when no horizontal grid segment covers its x-span on the boundary between
           them (a value drawn once for two sub-rows belongs to both); merged cells form one group.
Placement  each item lies in exactly one band (strictly inside) and one cell; an item on a grid line, outside every
           cell, or outside the table is UNPLACED and reported - never dropped (the silent row drop of the
           OpenTakeoff schedule scan is rejected; the reader itself is a clean reimplementation).

header_paths / record turn bands into labelled records: every leaf column of the lowest header band gets the label
path of the header cells above it; a data band's record maps each leaf column to the values of the (merged) cell
group drawn over it, with the merge recorded.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

POLICY_ID = "SCHEDULE_TABLE_READER_V1"
COMPLETE, ITEMS_UNPLACED, NO_GRID = "COMPLETE", "ITEMS_UNPLACED", "NO_GRID"
ON_GRID_LINE, OUTSIDE_TABLE, OUTSIDE_CELLS = "ON_GRID_LINE", "OUTSIDE_TABLE", "OUTSIDE_CELLS"


@dataclass(frozen=True)
class Item:
    key: str
    value: str
    x: float
    y: float
    kind: str = "TEXT"          # TEXT | ATTRIB
    tag: str | None = None
    owner: str | None = None    # owner insert handle (attributes)


def _cluster(vals, eps):
    out = []
    for v in sorted(vals):
        if out and v - out[-1][-1] <= eps:
            out[-1].append(v)
        else:
            out.append([v])
    return [sum(c) / len(c) for c in out]


def read(items, h_lines, v_lines, *, eps: float) -> dict:
    if not h_lines or not v_lines:
        return {"policy": POLICY_ID, "state": NO_GRID, "bands": [], "unplaced": [
            {"key": i.key, "value": i.value, "why": OUTSIDE_TABLE} for i in items]}
    ys = sorted(_cluster([h[0] for h in h_lines], eps), reverse=True)
    bands = []
    for k in range(len(ys) - 1):
        hi, lo = ys[k], ys[k + 1]
        mid = (hi + lo) / 2.0
        xs = _cluster([v[0] for v in v_lines if min(v[1], v[2]) - eps <= mid <= max(v[1], v[2]) + eps], eps)
        cells = [{"x0": xs[j], "x1": xs[j + 1], "values": [], "continues_above": False, "group": None}
                 for j in range(len(xs) - 1)]
        bands.append({"band": k, "y_hi": hi, "y_lo": lo, "cells": cells})
    # vertical merges: is the boundary y_hi of band k covered by horizontal segments over the cell's x-span?
    for k in range(1, len(bands)):
        y = bands[k]["y_hi"]
        segs = sorted((min(h[1], h[2]), max(h[1], h[2])) for h in h_lines if abs(h[0] - y) <= eps)
        for c in bands[k]["cells"]:
            a, b = c["x0"] + eps, c["x1"] - eps
            cur = a
            for s0, s1 in segs:
                if s0 - eps <= cur and s1 + eps >= cur:
                    cur = max(cur, s1)
                if cur >= b:
                    break
            c["continues_above"] = cur < b
    # merged groups (union-find over (band, cell))
    parent = {}

    def find(z):
        while parent.setdefault(z, z) != z:
            parent[z] = parent[parent[z]]
            z = parent[z]
        return z
    for k, bd in enumerate(bands):
        for j, c in enumerate(bd["cells"]):
            find((k, j))
            if c["continues_above"] and k > 0:
                mid = (c["x0"] + c["x1"]) / 2.0
                up = [jj for jj, cu in enumerate(bands[k - 1]["cells"]) if cu["x0"] - eps <= mid <= cu["x1"] + eps]
                if up:
                    parent[find((k, j))] = find((k - 1, up[0]))
    unplaced = []
    for it in sorted(items, key=lambda i: (i.key, i.value)):
        if not (ys[-1] < it.y < ys[0]):
            unplaced.append({"key": it.key, "value": it.value, "x": it.x, "y": it.y, "why": OUTSIDE_TABLE})
            continue
        if any(abs(it.y - y) <= eps for y in ys):
            unplaced.append({"key": it.key, "value": it.value, "x": it.x, "y": it.y, "why": ON_GRID_LINE})
            continue
        x_lo = min((c["x0"] for b in bands for c in b["cells"]), default=None)
        x_hi = max((c["x1"] for b in bands for c in b["cells"]), default=None)
        if x_lo is None or not (x_lo - eps <= it.x <= x_hi + eps):
            unplaced.append({"key": it.key, "value": it.value, "x": it.x, "y": it.y, "why": OUTSIDE_TABLE})
            continue
        bd = next(b for b in bands if b["y_lo"] < it.y < b["y_hi"])
        cell = [c for c in bd["cells"] if c["x0"] + eps < it.x < c["x1"] - eps]
        if len(cell) != 1:
            unplaced.append({"key": it.key, "value": it.value, "x": it.x, "y": it.y,
                             "why": ON_GRID_LINE if any(abs(it.x - c[e]) <= eps for c in bd["cells"]
                                                        for e in ("x0", "x1")) else OUTSIDE_CELLS})
            continue
        cell[0]["values"].append({"key": it.key, "value": it.value, "kind": it.kind, "tag": it.tag, "owner": it.owner,
                                  "x": it.x, "y": it.y})
    for k, bd in enumerate(bands):
        for j, c in enumerate(bd["cells"]):
            r = find((k, j))
            c["group"] = f"G{r[0]}.{r[1]}"
            c["values"].sort(key=lambda v: (v["x"], -v["y"], v["key"]))
    return {"policy": POLICY_ID, "state": ITEMS_UNPLACED if unplaced else COMPLETE, "bands": bands,
            "unplaced": unplaced, "grid": {"ys": ys, "h_lines": len(h_lines), "v_lines": len(v_lines)}}


def group_values(table) -> dict:
    out = {}
    for bd in table["bands"]:
        for c in bd["cells"]:
            out.setdefault(c["group"], []).extend(c["values"])
    return out


def header_paths(table, header_bands) -> list:
    """Leaf columns of the LOWEST header band, each with the label path of the header cells above it."""
    hb = sorted(header_bands)
    gv = group_values(table)
    leaves = []
    for c in table["bands"][hb[-1]]["cells"]:
        mid = (c["x0"] + c["x1"]) / 2.0
        path = []
        for k in hb:
            cell = next((cc for cc in table["bands"][k]["cells"] if cc["x0"] <= mid <= cc["x1"]), None)
            if cell is None:
                path.append("")
                continue
            label = " ".join(v["value"] for v in sorted(gv.get(cell["group"], []), key=lambda v: (-v["y"], v["x"])))
            if not path or label != path[-1]:
                path.append(label)
        leaves.append({"x0": c["x0"], "x1": c["x1"], "path": [p for p in path if p]})
    return leaves


def record(table, band, leaves) -> list:
    """[{leaf path, values, merged}] for one data band, one entry per leaf column (cells may span several leaves)."""
    gv = group_values(table)
    bd = table["bands"][band]
    out = []
    for lf in leaves:
        mid = (lf["x0"] + lf["x1"]) / 2.0
        cell = next((c for c in bd["cells"] if c["x0"] <= mid <= c["x1"]), None)
        vals = [] if cell is None else gv.get(cell["group"], [])
        members = sum(1 for b in table["bands"] for c in b["cells"] if cell is not None and c["group"] == cell["group"])
        out.append({"path": lf["path"], "values": [v["value"] for v in vals], "keys": [v["key"] for v in vals],
                    "tags": [v["tag"] for v in vals], "merged_bands": members})
    return out


def digest(table) -> str:
    return hashlib.sha256(json.dumps(table, sort_keys=True, default=str).encode()).hexdigest()


def policy_record() -> dict:
    return {"policy_id": POLICY_ID, "placement": "insertion point strictly inside one band and one cell",
            "merge": "no horizontal grid segment over the cell on the boundary -> the cell continues the one above",
            "never": ["dropping an unplaced value", "column by attribute tag", "a value from a neighbouring cell"]}
