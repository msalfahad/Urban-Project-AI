"""T-550: measure every cut parapet of the architect's sections in a DWF 6 plot (reproducible reading, any villa).

Physical question: for each parapet cut by SECTION A-A / B-B, where are (a) its top, (b) the level line of the roof it
stands on (the printed finished level), (c) the top of the hatched structure, (d) the bottom of the hatched edge member
under it, all in metres relative to the printed level of that roof. Hatched = cut concrete in these sections (T-201
s.7). The datum is fixed by the view's own level markers exactly as research/agents_t214/section_bands.py does (one
translation reproduces every printed level within 5 mm, else the view is refused). Nothing is scaled off a raster.

Method: hatch strokes (short slanted segments) are binned in 25 mm columns; a column whose hatch rises more than 0.10 m
above a printed roof level is a parapet column; consecutive columns form one cut parapet; a group
wider than 0.45 m, topping out below +0.30 or above +1.70, or not reaching below the level line is dropped (another
slab's or an opening's hatch). Window-frame hatches can still pass the filter: read the result per roof, the repeated
(top, bottom) pairs are the parapets. For each cut parapet the
hatch top / bottom (max / min over its columns' strokes) and the long vertical outline lines bounding it are reported.

Run (Python 3.11, from the repository root; the DWF stays in .work/private, nothing of it is written to the tree):
    python3 -I research/agents_t550/t550_section_parapets.py <path to the architectural .dwf>
Prints JSON (metres, widths in m; no coordinates of the plot).
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t201"))
sys.path.insert(0, str(HERE.parent / "agents_t214"))
import w2d_reader as W  # noqa: E402
import section_bands as SB  # noqa: E402

ROOF_LEVELS = (4.30, 5.50, 9.70, 13.90)
BIN = 25.0           # mm
MIN_RISE = 100.0     # mm above the level line for a parapet column
MAX_STROKE = 600.0   # mm: a hatch stroke is short


def _strokes(segs):
    for a, b in segs:
        dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
        if dx > 5 and dy > 5 and (dx * dx + dy * dy) ** 0.5 < MAX_STROKE:
            yield a, b


def measure(dwf_path):
    graphics = W.read_dwf_graphics(dwf_path)
    out = {}
    for _, g in graphics:
        tr = g["units"]
        pl = [[W.to_model(q, tr) for q in poly] for poly in g["polylines"]]
        texts = [(W.to_model((t[0], t[1]), tr), t[2] if isinstance(t[2], str) else t[2].decode("latin1"))
                 for t in g["texts"]]
        for (tx, ty), s in texts:
            title = s.strip()
            if title not in SB.WINDOWS:
                continue
            x0, x1 = tx + SB.WINDOWS[title][0], tx + SB.WINDOWS[title][1]
            segs = list(SB._segments(pl, x0, x1))
            apex = {}
            for (x2, y2), s2 in texts:
                if not (x0 <= x2 <= x1 and abs(y2 - ty) < 20000 and SB.LEVEL_RE.match(s2.strip())):
                    continue
                tri = [poly for poly in pl if 3 <= len(poly) <= 4 and all(
                    -200 <= q[0] - x2 <= 700 and -1000 <= q[1] - y2 <= -500 for q in poly)]
                if tri:
                    apex[float(s2)] = min(q[1] for poly in tri for q in poly)
            y0s = [y - v * 1000 for v, y in apex.items()]
            if len(apex) < 3 or max(y0s) - min(y0s) > SB.TOL_LEVEL * 1000:
                out[title] = {"refused": "datum not fixed by the level markers"}
                continue
            y0 = sum(y0s) / len(y0s)
            st = list(_strokes(segs))
            vert = [(a, b) for a, b in segs if abs(a[0] - b[0]) < 1.0 and abs(a[1] - b[1]) > 300]
            res = []
            for lev in ROOF_LEVELS:
                top = y0 + lev * 1000
                cols = collections.defaultdict(list)
                for a, b in st:
                    lo, hi = min(a[1], b[1]), max(a[1], b[1])
                    if hi < top - 1500 or lo > top + 2500:
                        continue
                    for x in (a[0], b[0]):
                        cols[int(x // BIN)].append((lo, hi))
                pcols = sorted(k for k, v in cols.items() if max(h for _, h in v) > top + MIN_RISE)
                groups, cur = [], []
                for k in pcols:
                    if cur and k - cur[-1] > 2:
                        groups.append(cur)
                        cur = []
                    cur.append(k)
                if cur:
                    groups.append(cur)
                for gk in groups:
                    xa, xb = gk[0] * BIN, (gk[-1] + 1) * BIN
                    # the parapet's own columns: hatch extent over the columns
                    his = [h for k in gk for _, h in cols[k]]
                    los = [lo for k in gk for lo, _ in cols[k]]
                    # outline verticals inside / at the group's x range
                    vs = sorted({round(a[0]) for a, b in vert if xa - 60 <= a[0] <= xb + 60})
                    vspans = []
                    for vx in vs:
                        ys = [(min(a[1], b[1]), max(a[1], b[1])) for a, b in vert if round(a[0]) == vx]
                        vspans.append([round((min(y for y, _ in ys) - top) / 1000, 3),
                                       round((max(y for _, y in ys) - top) / 1000, 3)])
                    top_m, bot_m = round((max(his) - top) / 1000, 3), round((min(los) - top) / 1000, 3)
                    if (xb - xa) > 450 or not (0.3 <= top_m <= 1.7) or bot_m >= 0.1:
                        continue        # not a parapet cut: too wide, or the hatch of another slab / opening
                    res.append({"roof_level": f"{lev:+.2f}", "width_m": round((xb - xa) / 1000, 3),
                                "hatch_top_m": round((max(his) - top) / 1000, 3),
                                "hatch_bottom_m": round((min(los) - top) / 1000, 3),
                                "outline_verticals_m": vspans})
            out[title] = {"marker_spread_m": round((max(y0s) - min(y0s)) / 1000, 4), "parapets": res}
    return out


if __name__ == "__main__":
    print(json.dumps(measure(sys.argv[1]), indent=1, sort_keys=True))
