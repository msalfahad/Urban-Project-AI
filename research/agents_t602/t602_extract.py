"""T-602 development-villa DRAWING READ (research, unwired): (1) the census of EVERY drawn step-edge pair on the plans
(a layer-5 front edge with a layer-2 companion 0.040 .. 0.060 m away, parallel, overlapping at least half the
companion: the villa's step convention, T-412 / T-584), with the printed levels reachable on each side of it; (2) the
printed levels reachable on each side of EVERY exterior opening of the merged opening census (T-150) plus the street
gate opening G-01 (T-361), read BY ENTITY HANDLE from the architectural DXF (Drive "Alsenan chalet project"
P7757_DXF_COMPRESSED.zip, decoded into .work/private only).

    .work/venv/bin/python -I research/agents_t602/t602_extract.py --dxf <P7757.dxf> --write
    .work/venv/bin/python -I research/agents_t602/t602_extract.py --dxf <P7757.dxf>          (re-read, compare)

Region read = R-T592-1 (d): a printed level figure (or the +-0.00 datum block LEL) counts for a side when a straight
sight line from a start point on that side reaches it without crossing ANY drawn line (all model-space LINE /
LWPOLYLINE / ARC except the TEXT layer, plus the exploded door / arch blocks), directly or through ONE waypoint of a
0.25 m grid visible from a start. Start points: 0.08 m beyond the edge / face (pairs: beyond the edge on the low side,
beyond the companion on the high side); door inserts: as T-592 on both sides (beside and beyond the leaf).
Output: handles, lengths, storey and level figures only; no coordinate, no drawing text other than level figures."""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "T602_DRAWN.json"
MM = 0.001
LEVEL_RE = re.compile(r"^[+\-]?\d+\.\d\d$")
GRID = 250.0
# storey of a plan frame by the model-space x band of the three plan sheets (no coordinate is written out)
STOREYS = (("GF", -166000.0, -120000.0), ("1F", -211000.0, -166000.0), ("2F", -256000.0, -211000.0))
PLAN_Y = (-815000.0, -784000.0)
# exterior openings of the merged census (T-150 OPENINGS_T150.csv) + G-01 (T-361 GATES_T361.csv)
DOOR_INSERTS = {"D-GF-01": "15E", "D-GF-03": "1B5", "D-GF-05": "192", "D-GF-06": "33E", "D-GF-07": "281",
                "D-GF-09": "3FF", "D-GF-15": "2D8", "D-2F-01": "12BA"}
# line-defined openings: (handle on side A, handle on side B); the start on each side lies 0.08 m beyond its handle,
# away from the other handle. A = the inside / plot side named in the census, B = the outside.
LINE_OPENINGS = {
    "G-01": ("110", "10F"),      # street gate gap: companion (layer 2, plot side) / plot line edge (layer 5)
    "SX-01": ("B7", "8D"),       # pool-court east wall faces through the 4.521 opening (low wall drawn through)
    "SX-03": ("3A2", "3A1"),     # pool-court north wall gap 1.000: both face head lines (layer 2)
    "W15": ("BC3", "BC2"),       # 1F living window W15: inner frame line (W) / outer face line (layer 5)
    "W16": ("C93", "C92"),       # 1F living window W16
    "W17": ("BD2", "BCE"),       # 1F master bed curved window W17: frame arc (W) / outer face arc (layer 5)
}


def _mid(e):
    if e.dxftype() == "LINE":
        s, t = e.dxf.start, e.dxf.end
        return ((s.x + t.x) / 2, (s.y + t.y) / 2)
    pts = [(v.x, v.y) for v in e.flattening(10)] if e.dxftype() == "ARC" else [(q[0], q[1]) for q in e.get_points()]
    return pts[len(pts) // 2]


def _geom(e):
    from shapely.geometry import LineString
    if e is None:
        return None
    if e.dxftype() == "LINE":
        return LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
    if e.dxftype() == "ARC":
        return LineString([(v.x, v.y) for v in e.flattening(10)])
    if e.dxftype() == "LWPOLYLINE":
        pts = [(q[0], q[1]) for q in e.get_points()]
        return LineString(pts) if len(pts) > 1 else None
    return None


def storey_of(x, y):
    if not PLAN_Y[0] <= y <= PLAN_Y[1]:
        return None
    for s, a, b in STOREYS:
        if a <= x < b:
            return s
    return None


def read(dxf_path):
    import ezdxf
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    from shapely.strtree import STRtree

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    assert doc.header.get("$INSUNITS") == 4, "drawing units are not mm"
    levels = []
    for e in msp.query("TEXT"):
        t = e.dxf.text.strip()
        if LEVEL_RE.match(t):
            levels.append((e.dxf.handle, t, (e.dxf.insert.x, e.dxf.insert.y)))
    for e in msp.query("INSERT"):
        if e.dxf.name == "LEL":
            levels.append((e.dxf.handle, "+-0.00", (e.dxf.insert.x, e.dxf.insert.y)))
    ents = [e for e in msp.query("LINE LWPOLYLINE ARC") if e.dxf.layer != "TEXT"]
    for ins in msp.query("INSERT"):
        if ins.dxf.name[:1] in "Dd" or ins.dxf.name in ("AR1", "arch120"):
            ents += [v for v in ins.virtual_entities() if v.dxftype() in ("LINE", "LWPOLYLINE", "ARC")]
    geoms = []
    for e in ents:
        if e.dxftype() == "LINE":
            geoms.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
        elif e.dxftype() == "ARC":
            geoms.append(LineString([(v.x, v.y) for v in e.flattening(10)]))
        else:
            pts = [(q[0], q[1]) for q in e.get_points()]
            if e.closed:
                pts.append(pts[0])
            if len(pts) > 1:
                geoms.append(LineString(pts))
    tree = STRtree(geoms)

    def clear(a, b):
        s = LineString([a, b])
        return not any(geoms[i].intersects(s) for i in tree.query(s))

    def reach(starts, centre, along, normal):
        """Levels reachable from the starts, directly or via one waypoint of the side's 0.25 m grid."""
        way = []
        for i in range(-40, 41):
            for j in range(1, 61):
                w = (centre[0] + along[0] * i * GRID + normal[0] * j * GRID,
                     centre[1] + along[1] * i * GRID + normal[1] * j * GRID)
                if any(clear(p, w) for p in starts):
                    way.append(w)
        got = {}
        for lh, t, p in levels:
            if min(math.dist(s, p) for s in starts) > 20000:
                continue
            if any(clear(s, p) for s in starts) or any(clear(w, p) for w in way):
                got.setdefault(t, []).append(lh)
        return {k: sorted(v) for k, v in sorted(got.items())}

    # ---- (1) every drawn step-edge pair ----------------------------------------------------------------------------
    def segs(lay):
        out = []
        for e in msp.query("LINE"):
            if e.dxf.layer == lay:
                out.append((e.dxf.handle, (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)))
        for e in msp.query("LWPOLYLINE"):
            if e.dxf.layer == lay:
                p = [(q[0], q[1]) for q in e.get_points()]
                if e.closed:
                    p.append(p[0])
                for i in range(len(p) - 1):
                    if math.dist(p[i], p[i + 1]) > 0:
                        out.append((f"{e.dxf.handle}#{i}", p[i], p[i + 1]))
        return out

    l5, l2 = segs("5"), segs("2")
    pairs = []
    for h2, a, b in l2:
        ln = math.dist(a, b)
        if ln < 300:
            continue
        ux, uy = (b[0] - a[0]) / ln, (b[1] - a[1]) / ln
        for h5, c, d in l5:
            l5n = math.dist(c, d)
            if l5n < 300:
                continue
            ex, ey = (d[0] - c[0]) / l5n, (d[1] - c[1]) / l5n
            if abs(ux * ey - uy * ex) > 0.01:
                continue
            off = (c[0] - a[0]) * (-uy) + (c[1] - a[1]) * ux          # signed offset of the edge from the companion
            if not 40 <= abs(off) <= 60:
                continue
            t0, t1 = sorted([(c[0] - a[0]) * ux + (c[1] - a[1]) * uy, (d[0] - a[0]) * ux + (d[1] - a[1]) * uy])
            ov = min(ln, t1) - max(0.0, t0)
            if ov < 0.5 * ln:
                continue
            sm = (max(0.0, t0) + min(ln, t1)) / 2                     # middle of the overlap, along the companion
            cm = (a[0] + ux * sm, a[1] + uy * sm)
            # unit normal pointing from the companion towards the edge (= downhill)
            sg = 1.0 if off > 0 else -1.0
            n = (-uy * sg, ux * sg)
            em = (cm[0] + n[0] * abs(off), cm[1] + n[1] * abs(off))
            st = storey_of(*cm)
            low = reach([(em[0] + n[0] * 80, em[1] + n[1] * 80)], em, (ux, uy), n)
            high = reach([(cm[0] - n[0] * 80, cm[1] - n[1] * 80)], cm, (ux, uy), (-n[0], -n[1]))
            pairs.append({"edge": h5, "companion": h2, "storey": st, "edge_m": round(l5n * MM, 6),
                          "companion_m": round(ln * MM, 6), "overlap_m": round(ov * MM, 6),
                          "offset_m": round(abs(off) * MM, 3),
                          "levels_low_side": low, "levels_high_side": high})
    # distance (m) from each pair to the nearest T-412 flight edge (merged nosing census handles) and to the nearest
    # exterior opening handle: the proof of which pairs are stair-zone edges and which stand at an opening
    import csv
    fl = set()
    with open(HERE.parents[1] / "research/agents_t412/NOSING_TABLE_T412.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            fl |= set(r["handles"].split())
    flg = [g for g in (_geom(doc.entitydb.get(h)) for h in sorted(fl)) if g is not None]
    opg = {}
    for oid, h in DOOR_INSERTS.items():
        ins = doc.entitydb.get(h)
        opg[oid] = unary_union([x for x in (_geom(v) for v in ins.virtual_entities()) if x is not None])
    for oid, hs in LINE_OPENINGS.items():
        opg[oid] = _geom(doc.entitydb.get(hs[0]))
    for p in pairs:
        g = _geom(doc.entitydb.get(p["edge"]))
        p["nearest_t412_flight_edge_m"] = round(min(g.distance(x) for x in flg) * MM, 3)
        near = sorted((round(g.distance(x) * MM, 3), oid) for oid, x in opg.items())[0]
        p["nearest_exterior_opening"] = {"id": near[1], "distance_m": near[0]}
        p["flight_handle"] = p["edge"] in fl or p["companion"].split("#")[0] in fl
    pairs.sort(key=lambda p: (p["storey"] or "", p["edge"], p["companion"]))

    # ---- (2) exterior openings -------------------------------------------------------------------------------------
    openings = {}
    for oid, h in DOOR_INSERTS.items():
        ins = doc.entitydb.get(h)
        assert ins is not None and ins.dxftype() == "INSERT", (oid, h)
        blk = doc.blocks.get(ins.dxf.name)
        bl = [b for b in blk if b.dxftype() == "LINE"]
        xs = [v for b in bl for v in (b.dxf.start.x, b.dxf.end.x)]
        span = (min(xs), max(xs))
        c = (span[0] + span[1]) / 2
        jy = [v for b in bl if abs(b.dxf.start.x - span[0]) < 1e-6 and abs(b.dxf.end.x - span[0]) < 1e-6
              for v in (b.dxf.start.y, b.dxf.end.y)]
        depth = max(jy) - min(jy)
        leaf = max(abs(b.dxf.end.y) for b in bl)
        m = ins.matrix44()

        def W(x, y):
            return tuple(m.transform((x, y, 0)))[:2]

        o = W(c, 0.0)
        ax, ay = (W(c + 1.0, 0.0)[0] - o[0], W(c + 1.0, 0.0)[1] - o[1])
        nx, ny = (W(c, 1.0)[0] - o[0], W(c, 1.0)[1] - o[1])
        na, nn = math.hypot(ax, ay), math.hypot(nx, ny)
        along, nrm = (ax / na, ay / na), (nx / nn, ny / nn)
        side0 = reach([W(c, -80.0), W(c, -(leaf + 60.0))], W(c, 0.0), along, (-nrm[0], -nrm[1]))
        side1 = reach([W(c, depth + 80.0), W(c, leaf + 60.0)], W(c, depth), along, nrm)
        openings[oid] = {"kind": "DOOR_INSERT", "handles": [h], "block": ins.dxf.name,
                         "storey": storey_of(*o), "width_m": round((span[1] - span[0]) * MM, 3),
                         "levels_side_face0": side0, "levels_side_face_depth": side1}
    for oid, (ha, hb) in LINE_OPENINGS.items():
        ea, eb = doc.entitydb.get(ha), doc.entitydb.get(hb)
        assert ea is not None and eb is not None, (oid, ha, hb)
        pa, pb = _mid(ea), _mid(eb)
        dd = math.dist(pa, pb)
        u = ((pa[0] - pb[0]) / dd, (pa[1] - pb[1]) / dd)            # from B towards A
        along = (-u[1], u[0])
        sa = reach([(pa[0] + u[0] * 80, pa[1] + u[1] * 80)], pa, along, u)
        sb = reach([(pb[0] - u[0] * 80, pb[1] - u[1] * 80)], pb, along, (-u[0], -u[1]))
        openings[oid] = {"kind": "LINE_PAIR", "handles": [ha, hb],
                         "layers": [ea.dxf.layer, eb.dxf.layer], "storey": storey_of(*pa),
                         "handle_a_m": None if ea.dxftype() != "LINE" else round(
                             math.dist((ea.dxf.start.x, ea.dxf.start.y), (ea.dxf.end.x, ea.dxf.end.y)) * MM, 6),
                         "handle_b_m": None if eb.dxftype() != "LINE" else round(
                             math.dist((eb.dxf.start.x, eb.dxf.start.y), (eb.dxf.end.x, eb.dxf.end.y)) * MM, 6),
                         "levels_side_a": sa, "levels_side_b": sb}
    return {"schema": "T602_DRAWN_V1", "drawing": "Drive 'Alsenan chalet project' P7757_DXF_COMPRESSED.zip "
            "(architectural DXF), read by handle", "units": "m", "pairs": pairs, "openings": openings,
            "plan_level_figures": sorted({t for _, t, _ in levels})}


def main(argv):
    if "--dxf" not in argv:
        raise SystemExit("--dxf <P7757.dxf> required (private input, .work/private)")
    got = read(argv[argv.index("--dxf") + 1])
    txt = json.dumps(got, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        OUT.write_text(txt, encoding="utf-8")
        print(f"wrote {OUT.name}")
    else:
        print("REPRODUCED" if OUT.exists() and OUT.read_text(encoding="utf-8") == txt else "DIFFERS")


if __name__ == "__main__":
    main(sys.argv[1:])
