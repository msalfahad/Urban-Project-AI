"""T-402 r2: what lies beside each face of a width-conflict beam (slab, opening, outside, held neighbour, undetermined).

Needed by R-T402-5: the slab line is net of the DRAWN faces, so which face an alternative width moves decides whether
the slab gives up / takes the strip (slab beside the face) or not (opening, outside, a held neighbour strip). The designer
has not said which face moves, so the slab pairing is a BOUND over the two faces, never a single figure unless both
faces see the same thing.

Read on the drawing (private Drive copy), per station every 0.05 m along each face, at a probe 0.10 m beyond it:
  * OPEN       probe inside the hull of an S-OPENING cross (the cross lines grouped by mutual intersection / contact);
  * HELD_NEIGH probe inside another HELD band (a projection strip whose own nature is held, T-402 R-T402-4);
  * SLAB       slab evidence (an S-REIN-SLAB bar, or an S-TEXT-SLAB bar / slab text: '%%c', 'S.S', 'SLAB') within 0.30 m of the ray from the face to the
               first structural line beyond it (layers 1 / S-BEAM / S-COL.BON / S-BOUN, <= 4.0 m);
  * NO_EVIDENCE_4M no structural line within 4.0 m and no slab evidence (outside, or a wide panel with no bar drawn:
               counted as possibly slab in the upper bound);
  * UNDETERMINED otherwise (a narrow strip bounded by a line, no bar or text drawn in it).
Output: <private>/t402/SIDES_T402.json (per line and face: length by class, handles of the evidence; no coordinates).

    python3 -I research/agents_t402/t402_sides.py <private>/ST7757_dxf.dxf <private>/t402/bands.json \
        <private>/t402/SIDES_T402.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import t402_read as T  # noqa: E402

WIDTH_LINES = ["L-9e4895663f76d7f03ac9", "L-2c7b0b1e1a439d9ffd1e", "L-60f09eece6568b15f6ce", "L-1fd49f3e7c5a7dd19d4d",
               "L-39ca5340879eafc35355", "L-50667f69855b6d588011", "L-43e804ba4a4c07529fd5"]
STEP, PROBE, REACH, EVID = 0.05, 0.10, 4.0, 0.30
BOUND_LAYERS = {"1", "S-BEAM", "S-COL.BON", "S-BOUN"}
SLAB_TEXT = re.compile(r"%%[cC]|\bS\.S\b|SLAB", re.I)   # a slab bar / slab mark; 'SEE DETAIL' or a member tag is not
CLASSES = ("SLAB", "OPEN", "NO_EVIDENCE_4M", "HELD_NEIGH", "UNDETERMINED")


def read(path):
    import ezdxf
    from shapely.geometry import LineString, MultiLineString, Point
    from shapely.ops import unary_union
    msp = ezdxf.readfile(path).modelspace()
    bounds, ops, evid = [], [], []
    for e in msp:
        if not e.dxf.hasattr("layer"):
            continue
        lay, t = e.dxf.layer, e.dxftype()
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            g = LineString([(a[0] / 1000, a[1] / 1000), (b[0] / 1000, b[1] / 1000)])
            if lay == "S-OPENING":
                ops.append((e.dxf.handle, g))
            elif lay in BOUND_LAYERS:
                bounds.append((e.dxf.handle, g))
            elif lay == "S-REIN-SLAB":
                evid.append((e.dxf.handle, g))
        elif t == "LWPOLYLINE" and lay in ("S-COL.BON",):
            pts = [(p[0] / 1000, p[1] / 1000) for p in e.get_points("xy")]
            if len(pts) > 1:
                bounds.append((e.dxf.handle, LineString(pts + ([pts[0]] if e.closed else []))))
        elif t == "TEXT" and lay == "S-TEXT-SLAB" and SLAB_TEXT.search(e.dxf.text):
            p = e.dxf.insert
            evid.append((e.dxf.handle, Point(p[0] / 1000, p[1] / 1000)))
    # group opening cross lines that touch each other; each group's convex hull is one opening
    groups = []
    for h, g in ops:
        hit = [i for i, (hs, gs) in enumerate(groups) if gs.distance(g) < 1e-3]
        hs, gs = [h], [g]
        for i in sorted(hit, reverse=True):
            hs += groups[i][0]
            gs.append(groups[i][1])
            groups.pop(i)
        groups.append((hs, unary_union(gs)))
    hulls = [(sorted(hs), MultiLineString([]).union(g).convex_hull) for hs, g in groups]
    return bounds, hulls, evid


def classify(lid, band, bands, bounds, hulls, evid):
    from shapely.geometry import LineString, Point, Polygon
    pts = band["pts"]
    o, u = T.axis(pts)
    n = (-u[1], u[0])
    ss = [T.pr(p, o, u) for p in pts]
    ws = [T.pp(p, o, u) for p in pts]
    s0, s1, w0, w1 = min(ss), max(ss), min(ws), max(ws)
    others = [(lid2, Polygon(bands[b2]["pts"])) for lid2, b2 in T.HELD.items() if b2 in bands and lid2 != lid]
    out = {}
    for face, wf, sg in (("w-", w0, -1.0), ("w+", w1, 1.0)):
        acc = {c: 0.0 for c in CLASSES}
        handles = {c: set() for c in CLASSES}
        k = 0
        while True:
            s = s0 + STEP / 2 + k * STEP
            if s > s1:
                break
            k += 1
            base = (o[0] + u[0] * s + n[0] * wf, o[1] + u[1] * s + n[1] * wf)
            probe = Point(base[0] + n[0] * sg * PROBE, base[1] + n[1] * sg * PROBE)
            seg_len = min(STEP, s1 - (s - STEP / 2))
            cls, why = None, ""
            for hs, hull in hulls:
                if hull.contains(probe):
                    cls, why = "OPEN", hs[0]
                    break
            if cls is None:
                for lid2, poly in others:
                    if poly.contains(probe):
                        cls, why = "HELD_NEIGH", lid2
                        break
            if cls is None:
                ray = LineString([(base[0] + n[0] * sg * 0.01, base[1] + n[1] * sg * 0.01),
                                  (base[0] + n[0] * sg * REACH, base[1] + n[1] * sg * REACH)])
                hits = sorted((Point(base).distance(g.intersection(ray)), h) for h, g in bounds if g.intersects(ray))
                reach = hits[0][0] if hits else REACH
                seg = LineString([(base[0] + n[0] * sg * 0.02, base[1] + n[1] * sg * 0.02),
                                  (base[0] + n[0] * sg * max(reach - 0.02, 0.03),
                                   base[1] + n[1] * sg * max(reach - 0.02, 0.03))])
                ev = [h for h, g in evid if g.distance(seg) < EVID]
                if ev:
                    cls, why = "SLAB", ev[0]
                elif not hits:
                    cls, why = "NO_EVIDENCE_4M", ""
                else:
                    cls, why = "UNDETERMINED", hits[0][1]
            acc[cls] += seg_len
            if why:
                handles[cls].add(why)
        out[face] = {"length_m": {c: round(v, 4) for c, v in acc.items()},
                     "evidence": {c: sorted(v)[:6] for c, v in handles.items() if v}}
    out["face_length_m"] = round(s1 - s0, 4)
    return out


def main(argv):
    dxf, bands_p, out_p = argv[1:4]
    bands = json.load(open(bands_p, encoding="utf-8"))
    bounds, hulls, evid = read(dxf)
    res = {lid: classify(lid, bands[T.HELD[lid]], bands, bounds, hulls, evid) for lid in WIDTH_LINES}
    json.dump(res, open(out_p, "w"), indent=1)
    for lid, r in res.items():
        print(lid, T.HELD[lid], "L", r["face_length_m"])
        for f in ("w-", "w+"):
            print("  ", f, {c: v for c, v in r[f]["length_m"].items() if v}, r[f]["evidence"])


if __name__ == "__main__":
    main(sys.argv)
