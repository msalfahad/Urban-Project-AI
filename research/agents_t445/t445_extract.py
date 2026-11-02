"""T-445 own read (values only): footing outlines of the FOUNDATION PLAN and the plot line S-BOUN from the structural
DXF (Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf', decoded into .work/private). Writes outline rectangles in
metres (plan coordinates relative to the plot line's lower-left corner), the plot rectangle and the sha256.
No text, no client name, no drawing content beyond sizes and positions.

    .work/venv/bin/python -I research/agents_t445/t445_extract.py <dxf> <out.json>
"""
from __future__ import annotations

import hashlib
import json
import sys

import ezdxf
from shapely.geometry import MultiPoint

# handles from the merged T-233 ledger (26 outlines in the FOUNDATION PLAN frame) and the plot line 1658
INSERT_OR_POLY = ["165C", "1663", "1664", "1665", "1666", "1667", "1668", "1669", "166A", "166B", "166C", "166D",
                  "180C", "180F", "1ABF", "1ADB", "1B07", "1B19", "1B1A", "1B1B", "1B24", "1B2A", "1B2B"]
FOUR_LINES = {"10F0": ["10F0", "10F1", "10F2", "10F3"], "10F8": ["10F8", "10F9", "10FA", "10FB"],
              "1100": ["1100", "1101", "1102", "1103"]}
PLOT = "1658"


def _pts(e):
    t = e.dxftype()
    if t == "LWPOLYLINE":
        return [(float(x), float(y)) for x, y in e.get_points("xy")]
    if t == "LINE":
        return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
    if t == "INSERT":
        out = []
        for v in e.virtual_entities():
            out += _pts(v)
        return out
    raise ValueError(f"unexpected entity {t}")


def main(src, dst):
    sha = hashlib.sha256(open(src, "rb").read()).hexdigest()
    doc = ezdxf.readfile(src)
    db = doc.entitydb
    plot = _pts(db[PLOT])
    x0 = min(p[0] for p in plot); y0 = min(p[1] for p in plot)
    out = {"schema": "URBAN_T445_OUTLINES_V1", "source": {"file": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'",
           "sha256": sha, "units": "mm in the file, m here", "origin": "plot line 1658 lower-left"}, "outlines": {}}

    def rel(pts):
        return [(round((x - x0) / 1000.0, 4), round((y - y0) / 1000.0, 4)) for x, y in pts]

    out["plot"] = rel(plot)
    for h in INSERT_OR_POLY:
        e = db[h]
        pts = rel(_pts(e))
        rec = {"entity": e.dxftype(), "layer": e.dxf.layer}
        if e.dxftype() == "LWPOLYLINE":
            rec["closed"] = bool(e.closed)
            rec["vertices"] = pts
        else:
            rec["vertices"] = [tuple(map(lambda c: round(c, 4), p)) for p in MultiPoint(pts).envelope.exterior.coords[:-1]]
        out["outlines"][h] = rec
    for h, hs in FOUR_LINES.items():
        pts = []
        for k in hs:
            pts += rel(_pts(db[k]))
        out["outlines"][h] = {"entity": "4xLINE", "layer": db[hs[0]].dxf.layer,
                              "vertices": [tuple(map(lambda c: round(c, 4), p))
                                           for p in MultiPoint(pts).envelope.exterior.coords[:-1]]}
    json.dump(out, open(dst, "w"), indent=1)
    print("sha256", sha, "outlines", len(out["outlines"]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
