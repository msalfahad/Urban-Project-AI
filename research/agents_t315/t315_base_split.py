"""T-315 r2 (Gate B F-T315-C1 / C2): the pantry wall base per engine room, by the source entities each skirting line
names, measured on the drawing (read-only; prints handles, line ids, room ids and lengths only: no coordinate, no
name).

For each engine room of the run that the merged room split puts in the open pantry (T-262: GF-RC06FED wholly inside,
GF-RC99C2A in part), every boundary edge is laid on the drawn LINE / LWPOLYLINE entities it runs along (parallel, within
5 mm); the part of the edge inside the pantry's walls (the box spanned by the pantry's south wall face A6 and its north
wall face 158: west wall face to the open edge, south to north face) is kept, edge by edge, with the entity it lies on
(walls / columns first, then window frames). The result is compared with the pins in t315_inputs.BASE (an edited
drawing, a different engine room or a moved edge stops the build):

  GF-RC06FED: A6 1.6000 + AF 0.2000 + B0 0.1000 = 1.9000 lm of wall / column base (= its whole skirting line
              L-af6fb2d3 1.9 lm) and the W10 frame 3C9 / 3CC / 3D3 1.0000 lm (= its whole range line L-73ff85e3)
  GF-RC99C2A: 159 0.3409 + 158 0.7591 + 2FAE 0.9500 + AE 0.8000 + AF 0.6500 = 3.5000 lm of wall / column base inside
              its skirting line L-71e2e002 28.171589 lm, and the W09 frame 3BC / 3BF / 3C6 1.5000 lm inside its range
              line L-e7dcdc69 0 .. 7.831578 lm (OP-024 = W09 1.5 m, OP-019 6.33 m lies on another wall)
  the pantry base on no engine room boundary (counter cells): A6 1.4000 + AF 0.2000 = 1.6000 lm
  closure: 1.9 + 3.5 + 1.6 = 7.000 lm = T-296 ROOMS_T296 GF-07 base_wc_m 7.000 (wall + column base of the pantry)

    python3 -I research/agents_t315/t315_base_split.py <ARCH_ROOMS.json of the v29 run> <plan.dxf>
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

TOL = 5.0                    # mm: an edge lies on an entity when parallel and within this distance
BOX_TOL = 0.01               # mm: the pantry box margin (an edge on a wall face line is inside)
ANCHOR_SOUTH, ANCHOR_NORTH = "A6", "158"
ROOMS = ("GF-RC06FED", "GF-RC99C2A")
PRI = {"1": 0, "S-COL.BON": 0, "W": 1}     # walls / columns before window frames; other layers are not a base


def _segments(doc):
    out = []
    for e in doc.modelspace():
        t = e.dxftype()
        if t not in ("LINE", "LWPOLYLINE") or e.dxf.layer not in PRI:
            continue
        if t == "LINE":
            ss = [(tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2])]
        else:
            p = [tuple(x[:2]) for x in e.get_points()]
            if e.closed:
                p.append(p[0])
            ss = list(zip(p, p[1:]))
        for a, b in ss:
            if math.dist(a, b) > 0:
                out.append((e.dxf.handle, e.dxf.layer, a, b))
    return out


def _box(doc):
    s, n = doc.entitydb.get(ANCHOR_SOUTH), doc.entitydb.get(ANCHOR_NORTH)
    xs = (s.dxf.start[0], s.dxf.end[0])
    return min(xs), max(xs), s.dxf.start[1], n.dxf.start[1]


def _on(edge, seg):
    """the [t0, t1] interval of the edge (0 .. 1) that lies on the segment, or None."""
    (a, b), (_h, _l, c, d) = edge, seg
    L = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    vx, vy = d[0] - c[0], d[1] - c[1]
    Ls = math.hypot(vx, vy)
    if abs(ux * vy - uy * vx) / Ls > 1e-3:
        return None
    if abs((c[0] - a[0]) * uy - (c[1] - a[1]) * ux) > TOL:
        return None
    t = sorted(((c[0] - a[0]) * ux + (c[1] - a[1]) * uy, (d[0] - a[0]) * ux + (d[1] - a[1]) * uy))
    t0, t1 = max(t[0], 0.0) / L, min(t[1], L) / L
    return (t0, t1) if t1 - t0 > 1e-9 else None


def _clip(a, b, box):
    """the [t0, t1] of the edge inside the box (TOL margin)."""
    x0, x1, y0, y1 = box[0] - BOX_TOL, box[1] + BOX_TOL, box[2] - BOX_TOL, box[3] + BOX_TOL
    t0, t1 = 0.0, 1.0
    for p, q, lo, hi in ((a[0], b[0], x0, x1), (a[1], b[1], y0, y1)):
        dlt = q - p
        if abs(dlt) < 1e-12:
            if not (lo <= p <= hi):
                return None
            continue
        u, v = sorted(((lo - p) / dlt, (hi - p) / dlt))
        t0, t1 = max(t0, u), min(t1, v)
    return (t0, t1) if t1 - t0 > 1e-9 else None


def room_parts(room, segs, box, unit_m):
    """{entity: m} of the room's boundary inside the pantry box, each piece of an edge on one entity (priority)."""
    poly = room["polygon"]
    out = {}
    for a, b in zip(poly, poly[1:] + poly[:1]):
        L = math.dist(a, b)
        if L == 0:
            continue
        cl = _clip(a, b, box)
        if cl is None:
            continue
        ivs = []
        for s in segs:
            on = _on((a, b), s)
            if on is None:
                continue
            lo, hi = max(on[0], cl[0]), min(on[1], cl[1])
            if hi - lo > 1e-9:
                ivs.append((PRI[s[1]], s[0], lo, hi))
        taken = []                                     # disjoint pieces already given to an entity
        for _p, h, lo, hi in sorted(ivs):
            free = [(lo, hi)]
            for tl, th in taken:
                nxt = []
                for fl, fh in free:
                    if th <= fl or tl >= fh:
                        nxt.append((fl, fh))
                        continue
                    if fl < tl:
                        nxt.append((fl, tl))
                    if th < fh:
                        nxt.append((th, fh))
                free = nxt
            for fl, fh in free:
                if fh - fl > 1e-9:
                    out[h] = out.get(h, 0.0) + (fh - fl) * L * unit_m
                    taken.append((fl, fh))
    return {h: round(v, 4) for h, v in sorted(out.items()) if v > 1e-4}     # a corner touch (< 0.1 mm) is no base


def measure(arch_rooms, plan):
    import ezdxf
    doc = ezdxf.readfile(plan)
    segs = _segments(doc)
    box = _box(doc)
    rooms = {r["room_id"]: r for r in json.loads(Path(arch_rooms).read_text(encoding="utf-8"))["rooms"]}
    out = {}
    for rid in ROOMS:
        r = rooms[rid]
        unit_m = r["polygon_m"][0][0] / r["polygon"][0][0]
        out[rid] = room_parts(r, segs, box, unit_m)
    # the south (A6) and west (AF) wall faces of the pantry where no engine room runs (counter cells): entity length
    # less what the rooms above lie on (on A6 the column 2FAB top face is collinear: its 0.2 is A6's first 0.2 m)
    a6 = math.dist(doc.entitydb.get("A6").dxf.start, doc.entitydb.get("A6").dxf.end) * unit_m
    af = math.dist(doc.entitydb.get("AF").dxf.start, doc.entitydb.get("AF").dxf.end) * unit_m
    on = lambda h: sum(v.get(h, 0.0) for v in out.values())                 # noqa: E731
    out["NO_ENGINE_ROOM"] = {"A6": round(a6 - on("A6") - on("2FAB"), 4), "AF": round(af - on("AF"), 4)}
    return out


def main(argv=None):
    import t315_inputs as L21
    a = (argv or sys.argv[1:])
    got = measure(a[0], a[1])
    print(json.dumps(got, indent=1, sort_keys=True))
    pins = L21.base_pins()
    bad = []
    for rid, ents in pins.items():
        for h, m in ents.items():
            if abs(got.get(rid, {}).get(h, 0.0) - m) > 1e-4:
                bad.append(f"{rid} {h}: drawing {got.get(rid, {}).get(h)} != pin {m}")
        extra = sorted(set(got.get(rid, {})) - set(ents))
        if extra:
            bad.append(f"{rid}: entities on the pantry boundary not in the pins {extra} "
                       f"({[got[rid][h] for h in extra]})")
    if bad:
        raise SystemExit("BASE SPLIT DIFFERS:\n  " + "\n  ".join(bad))
    print("BASE SPLIT = the pins (t315_inputs.BASE)")
    return 0


if __name__ == "__main__":
    main()
