"""T-684 probe: every drawn segment in the north turn zone of the dog-leg stair shaft, per plan (for the verifier).

Prints only RELATIVE geometry (metres from the shaft's north-west inner corner, lengths, angles), the layer name,
its linetype and the entity's own linetype; no absolute coordinate, text or other drawing content. Usage (drawing
outside the clone):
    bash scripts/agent_env.sh run --tree task-T-684 research/agents_t684/t684_probe.py --arch <architectural DXF>

Method. The dog-leg shaft on each plan is found from its two straight tread sets (layer '2' or '5', 1.150 m lines at
0.300 m pitch, the west set and the east set side by side, 1.2-1.4 m apart); the north end of the shaft is the
end of the west set farther from the east set's start... in practice the zone examined is the full shaft width
(both lanes + well) and 1.40 m beyond the far end of the longer west set, so that nothing in the corner squares is
missed. Every LINE / polyline piece / block piece touching that zone is listed.
"""

from __future__ import annotations

import argparse
import math
from collections import defaultdict

import ezdxf

STAIR_LAYERS = {"2", "5"}


def flat(doc):
    segs, titles = [], []

    def walk(ents, depth=0, inh=None, inh_lt=None):
        for e in ents:
            t = e.dxftype()
            lay = getattr(e.dxf, "layer", "?")
            try:
                lt = e.dxf.get("linetype", "BYLAYER")
            except Exception:
                lt = "?"
            if lay == "0" and inh:
                lay = inh
            if lt.upper() == "BYBLOCK" and inh_lt:
                lt = inh_lt
            try:
                if t == "LINE":
                    segs.append((lay, lt, e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y, t))
                elif t in ("LWPOLYLINE", "POLYLINE"):
                    for v in e.virtual_entities():
                        if v.dxftype() == "LINE":
                            segs.append((lay, lt, v.dxf.start.x, v.dxf.start.y, v.dxf.end.x, v.dxf.end.y, t))
                elif t == "ARC":
                    c, r = e.dxf.center, e.dxf.radius
                    a0, a1 = math.radians(e.dxf.start_angle), math.radians(e.dxf.end_angle)
                    segs.append((lay, lt, c.x + r * math.cos(a0), c.y + r * math.sin(a0), c.x + r * math.cos(a1),
                                 c.y + r * math.sin(a1), "ARC"))
                elif t == "INSERT" and depth < 8:
                    walk(list(e.virtual_entities()), depth + 1, lay, lt)
                elif t in ("TEXT", "MTEXT"):
                    s = e.dxf.text if t == "TEXT" else e.plain_text()
                    if "FLOOR PLAN" in s.upper():
                        titles.append((e.dxf.insert.x, s.split("1:")[0].strip()))
            except Exception:
                pass
    walk(doc.modelspace())
    return segs, sorted(titles)


def plan_of(titles, x):
    best = None
    for i, (tx, name) in enumerate(titles):
        lo = titles[i - 1][0] if i else -1e18
        if lo + 5000 < x <= tx + 15000:
            best = name
    return best or "?"


def vertical_sets(segs):
    """horizontal 1.150 m lines on the stair layers grouped in columns, runs at 0.30 m pitch (mm drawing)."""
    cols = defaultdict(set)
    for lay, lt, a, b, c, d, t in segs:
        if lay not in STAIR_LAYERS or t != "LINE":
            continue
        if abs(math.hypot(c - a, d - b) - 1150) > 3 or abs(d - b) > 1:
            continue
        cols[(round(min(a, c) / 50))].add((round(min(a, c)), round(max(a, c)), round(b)))
    out = []
    for key, ss in cols.items():
        ys = sorted({s[2] for s in ss})
        run = [ys[0]]
        for y in ys[1:]:
            if 250 <= y - run[-1] <= 350:
                run.append(y)
            elif y - run[-1] >= 100:
                if len(run) >= 3:
                    out.append((min(s[0] for s in ss), max(s[1] for s in ss), run))
                run = [y]
        if len(run) >= 3:
            out.append((min(s[0] for s in ss), max(s[1] for s in ss), run))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", required=True)
    ap.add_argument("--st")
    a = ap.parse_args()
    doc = ezdxf.readfile(a.arch)
    ltype_of_layer = {l.dxf.name: l.dxf.get("linetype", "?") for l in doc.layers}
    print("layer linetypes:", {k: ltype_of_layer.get(k) for k in sorted(STAIR_LAYERS | {"0"})})
    segs, titles = flat(doc)
    sets = vertical_sets(segs)
    # pair a 12-or-10-line west set with an 11-line east set 1.30 m (+-0.15) to its east, same plan
    for w in sets:
        for e in sets:
            dx = e[0] - w[0]
            if not 1200 <= dx <= 1400 or plan_of(titles, w[0]) != plan_of(titles, e[0]):
                continue
            plan = plan_of(titles, w[0])
            x0, x1 = w[0] - 60, e[1] + 60
            ytop = max(w[2][-1], e[2][-1])
            ybot = min(w[2][0], e[2][0])
            print(f"\n== {plan}: west set {len(w[2])} lines y {0:.3f}..{(w[2][-1]-w[2][0])/1000:.3f}; east set "
                  f"{len(e[2])} lines y {(e[2][0]-w[2][0])/1000:.3f}..{(e[2][-1]-w[2][0])/1000:.3f} (rel. to the west "
                  f"set's first line); lane x: west {0:.3f}..{(w[1]-w[0])/1000:.3f}, east {(e[0]-w[0])/1000:.3f}.."
                  f"{(e[1]-w[0])/1000:.3f}")
            for side, (ya, yb) in (("NORTH zone", (ytop - 50, ytop + 1500)), ("SOUTH zone", (ybot - 1500, ybot + 50))):
                rows = []
                for lay, lt, sa, sb, sc, sd, t in segs:
                    if not (min(sa, sc) >= x0 - 300 and max(sa, sc) <= x1 + 300):
                        continue
                    if not (min(sb, sd) >= ya - 300 and max(sb, sd) <= yb + 300):
                        continue
                    ln = math.hypot(sc - sa, sd - sb)
                    if ln < 50:
                        continue
                    ang = math.degrees(math.atan2(sd - sb, sc - sa)) % 180
                    rows.append((lay, lt, t, round((sa - w[0]) / 1000, 3), round((sb - w[2][0]) / 1000, 3),
                                 round((sc - w[0]) / 1000, 3), round((sd - w[2][0]) / 1000, 3), round(ln / 1000, 3),
                                 round(ang, 1)))
                rows = sorted(set(rows), key=lambda r: (r[0], r[8], r[4], r[3]))
                print(f"  -- {side}: {len(rows)} segments (layer, ent-linetype, type, x1, y1, x2, y2, len, ang)")
                for r in rows:
                    if r[8] % 90 not in (0.0,) or r[0] in STAIR_LAYERS:
                        print("    ", r)


if __name__ == "__main__" and "--arch" in __import__("sys").argv:
    main()


def st_main(path):
    """structural sheet: the two dog-leg sets per slab plan and every segment in the north 1.5 m (relative units, m)."""
    doc = ezdxf.readfile(path)
    segs, _ = flat(doc)
    titles = []
    for e in doc.modelspace().query("TEXT MTEXT"):
        s = e.dxf.text if e.dxftype() == "TEXT" else e.plain_text()
        if "--titles" in __import__("sys").argv and ("ROOF" in s.upper() or "PLAN" in s.upper()):
            print("title:", " ".join(s.split())[:50])
        if ("SLAB" in s.upper() or "BEAMS PLAN" in s.upper()) and ("FLOOR" in s.upper() or "GROUND" in s.upper()):
            titles.append((e.dxf.insert.x, e.dxf.insert.y, " ".join(s.split())[:40]))
    cols = defaultdict(set)
    for lay, lt, a, b, c, d, t in segs:
        if t == "LINE" and abs(d - b) < 1 and abs(math.hypot(c - a, d - b) - 1150) < 3:
            cols[(lay, round(min(a, c) / 50))].add(round(b))
    runs = []
    for (lay, kx), ys in cols.items():
        ys = sorted(ys)
        if len(ys) >= 5:
            runs.append((kx * 50, ys))
    runs.sort()
    for i, (xw, ysw) in enumerate(runs):
        for xe, yse in runs[i + 1:]:
            if not 1300 <= xe - xw <= 1400:
                continue
            # a slab plan's title is printed below its plan: the nearest title below the set, by plan distance
            below = [t for t in titles if t[1] < ysw[0]]
            near = min(below, key=lambda t: math.hypot(t[0] - xw, t[1] - ysw[0]))[2] if below else "?"
            y0 = ysw[0]
            ytop = max(ysw[-1], yse[-1])
            # the round reception stair (ST-02) is drawn only on the GF roof slab plan (T-184): its straight flight is
            # an 11-line set of VERTICAL 1.150 m lines; report whether one lies within 12 m of this dog-leg
            vx = defaultdict(set)
            for lay, lt, a, b, c, d, t in segs:
                if t == "LINE" and abs(c - a) < 1 and abs(math.hypot(c - a, d - b) - 1150) < 3 \
                        and math.hypot(a - xw, b - ysw[0]) < 12000:
                    vx[round(min(b, d) / 50)].add(round(a))
            rs = max((len(v) for v in vx.values()), default=0)
            near = f"{near}; vertical 1.150 m tread set within 12 m: {rs} lines"
            print(f"\n== ST sheet near title '{near}': west {len(ysw)} lines {0:.3f}..{(ysw[-1]-y0)/1000:.3f}, east "
                  f"{len(yse)} lines {(yse[0]-y0)/1000:.3f}..{(yse[-1]-y0)/1000:.3f}")
            rows = set()
            for lay, lt, sa, sb, sc, sd, t in segs:
                if min(sa, sc) >= xw - 400 and max(sa, sc) <= xe + 1550 and min(sb, sd) >= ytop - 50 \
                        and max(sb, sd) <= ytop + 1700 and math.hypot(sc - sa, sd - sb) >= 50:
                    ang = math.degrees(math.atan2(sd - sb, sc - sa)) % 180
                    rows.add((lay, t, round((sa - xw) / 1000, 3), round((sb - y0) / 1000, 3), round((sc - xw) / 1000, 3),
                              round((sd - y0) / 1000, 3), round(math.hypot(sc - sa, sd - sb) / 1000, 3), round(ang, 1)))
            diag = sorted(r for r in rows if r[7] % 90 > 1)
            print(f"  north zone: {len(rows)} segments, {len(diag)} not orthogonal:")
            for r in diag:
                print("    ", r)


if __name__ == "__main__" and "--st" in __import__("sys").argv:
    st_main(__import__("sys").argv[__import__("sys").argv.index("--st") + 1])
