"""T-111 reader: re-derive the stair readings of stair_flight_ledger.py from the architectural DXF (for the verifier).

Prints only counts, pitches, lengths, angles, radii and dimension values per plan; no coordinate, layer content or
text of the drawing is written. Usage (drawing outside the clone):
    python3 -I research/agents_t111/read_stair_cad.py --arch <architectural DXF>

Method: every LINE / polyline piece of the plan's stair layers is grouped into tread-line sets (parallel segments of
one length, 0.25-0.35 m apart, at least 3 in a row); radial sets (segments of one length whose extensions meet at one
point) are reported with their centre distance range and angular pitch. Plans are split at the plan titles
('... FLOOR PLAN'). The DIMENSION values whose text point lies inside a set's box (+0.6 m) are listed with it.
"""

from __future__ import annotations

import argparse
import math
from collections import defaultdict

import ezdxf
import numpy as np

STAIR_LAYERS = {"2", "5"}            # the layers that carry the tread lines on this drawing set (read, not assumed:
                                     # the census prints the layer of every set it uses)


def flat(doc):
    segs, dims, titles = [], [], []

    def walk(ents, depth=0, inh=None):
        for e in ents:
            t = e.dxftype()
            try:
                lay = e.dxf.layer
            except Exception:
                lay = "?"
            if lay == "0" and inh:
                lay = inh
            try:
                if t == "LINE":
                    segs.append((lay, e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y))
                elif t in ("LWPOLYLINE", "POLYLINE"):
                    walk(list(e.virtual_entities()), depth, lay)
                elif t == "INSERT" and depth < 8:
                    walk(list(e.virtual_entities()), depth + 1, lay)
                elif t == "DIMENSION":
                    p = e.dxf.text_midpoint
                    dims.append((p.x, p.y, e.get_measurement()))
                elif t in ("TEXT", "MTEXT"):
                    s = e.dxf.text if t == "TEXT" else e.plain_text()
                    if "FLOOR PLAN" in s.upper():
                        titles.append((e.dxf.insert.x, s.split("1:")[0].strip()))
            except Exception:
                pass
    walk(doc.modelspace())
    return segs, dims, titles


def tread_sets(segs):
    """parallel equal-length segments 0.25-0.35 m apart, >= 3 in a row (mm drawing)."""
    by = defaultdict(list)
    for lay, a, b, c, d in segs:
        if lay not in STAIR_LAYERS:
            continue
        ln = math.hypot(c - a, d - b)
        if not 800 <= ln <= 3000:
            continue
        ang = round(math.degrees(math.atan2(d - b, c - a)) % 180, 0)
        if ang % 90:
            continue
        by[(lay, ang, round(ln / 10) * 10)].append((a, b, c, d))
    out = []
    for (lay, ang, ln), ss in by.items():
        k = 1 if ang == 0 else 0                     # along-flight coordinate index (y for horizontal lines)
        cols = defaultdict(list)
        for s in set((round(s[0]), round(s[1]), round(s[2]), round(s[3])) for s in ss):
            cols[round(min(s[1 - k], s[3 - k]) / 100)].append(s)
        for col in cols.values():
            col.sort(key=lambda s: min(s[k], s[k + 2]))
            run = [col[0]]
            for s in col[1:]:
                gap = min(s[k], s[k + 2]) - min(run[-1][k], run[-1][k + 2])
                if gap < 100:
                    continue                          # a nosing / duplicate line of the same riser
                if gap <= 350 and gap >= 250:
                    run.append(s)
                else:
                    if len(run) >= 3:
                        out.append((lay, ang, ln, run))
                    run = [s]
            if len(run) >= 3:
                out.append((lay, ang, ln, run))
    return out


def radial_sets(segs, length=1150, tol=3):
    ss = [s for s in segs if s[0] in STAIR_LAYERS and abs(math.hypot(s[3] - s[1], s[4] - s[2]) - length) < tol
          and (math.degrees(math.atan2(s[4] - s[2], s[3] - s[1])) % 90) > 2
          and (math.degrees(math.atan2(s[4] - s[2], s[3] - s[1])) % 90) < 88]
    groups = defaultdict(list)
    for s in ss:
        groups[(s[0], round((s[1] + s[3]) / 20000), round((s[2] + s[4]) / 20000))].append(s)
    out = []
    for g in groups.values():
        if len(g) < 5:
            continue
        A, B = [], []
        for _, a, b, c, d in g:
            nx, ny = -(d - b), (c - a)
            n = math.hypot(nx, ny)
            A.append([nx / n, ny / n])
            B.append((nx * a + ny * b) / n)
        cx, cy = np.linalg.lstsq(np.array(A), np.array(B), rcond=None)[0]
        angs = sorted(math.degrees(math.atan2((b + d) / 2 - cy, (a + c) / 2 - cx)) % 360 for _, a, b, c, d in g)
        rr = [(math.hypot(a - cx, b - cy), math.hypot(c - cx, d - cy)) for _, a, b, c, d in g]
        out.append(dict(lines=len(g), r_in=round(np.median([min(r) for r in rr])), r_out=round(np.median([max(r) for r in rr])),
                        pitch_deg=round(float(np.median(np.diff(angs))), 2), sweep_deg=round(angs[-1] - angs[0], 2),
                        x=cx, y=cy))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", required=True)
    a = ap.parse_args()
    segs, dims, titles = flat(ezdxf.readfile(a.arch))
    titles = sorted(titles)
    def plan_of(x):
        # a plan's geometry lies to the left of its title's insertion point and right of the previous title
        best = None
        for i, (tx, name) in enumerate(titles):
            lo = titles[i - 1][0] if i else -1e18
            if lo + 5000 < x <= tx + 15000:
                best = name
        return best or "?"
    for lay, ang, ln, run in tread_sets(segs):
        k = 1 if ang == 0 else 0
        pos = [min(s[k], s[k + 2]) for s in run]
        x0 = min(min(s[0], s[2]) for s in run) - 600
        x1 = max(max(s[0], s[2]) for s in run) + 600
        y0 = min(min(s[1], s[3]) for s in run) - 600
        y1 = max(max(s[1], s[3]) for s in run) + 600
        dv = sorted({round(m) for x, y, m in dims if x0 <= x <= x1 and y0 <= y <= y1 and m > 0})
        print(f"{plan_of(run[0][0]):24s} layer {lay} tread set: {len(run):2d} lines of {ln / 1000:.3f} m, pitch "
              f"{np.median(np.diff(pos)) / 1000:.3f} m, first to last {(pos[-1] - pos[0]) / 1000:.3f} m; dims nearby "
              f"{[d / 1000 for d in dv]}")
    for r in radial_sets(segs):
        print(f"{plan_of(r['x']):24s} radial set: {r['lines']} lines, tread ends r {r['r_in'] / 1000:.3f} .. "
              f"{r['r_out'] / 1000:.3f} m, pitch {r['pitch_deg']} deg, sweep {r['sweep_deg']} deg")


if __name__ == "__main__":
    main()
