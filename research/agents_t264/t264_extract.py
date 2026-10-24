"""T-264 extractor: private 'ST7757 dxf.dxf' (Drive "Alsenan chalet project", sha256 9f9d1179...) + the T-139 faces of
it -> ALSENAN_R4_INPUT.json (lengths, areas, m2 and DXF handles only; no coordinates, no drawing content).

    python3 -I research/agents_t264/t264_extract.py <ST7757 dxf.dxf> <faces.json> [out.json]

faces.json = `python3 -I research/agents_t139/slab_faces.py <dxf> faces.json` (T-139 faces, the partition formwork r3
walked). Run from the checkout root on Python 3.11. Everything read here is read-only: the r3 walk is re-run through the
merged module research/agents_t163/t163_formwork.py (rule r3, reproduced byte for byte before this extract).

What it extracts (each item is a change since formwork r3, T-163 MERGED 659f889f):
  (a) the GF void ring B7 (T-252 R-BEAM-CURVED-AREA-2): every drawn edge piece of the ring and of the void it encloses,
      arcs as arcs (R x sweep, never chords), with the face found 5 mm beyond the piece's mid point; plus what r3 had
      measured on the two ring pieces it could bind (GF-035, GF-060) and the RING_MIX lengths it held;
  (b) the two GF beams that end on the oblique B27 east face (T-252 R-BEAM-END-OBLIQUE-2): the T-139 face of each band
      and its edge lengths on the two drawn edges, to show whether r3's drawing-face walk already ended both edges on
      the carrier face;
  (c) the main-house ring ground beam ARC:157+158 (T-242 / T-253): inner and outer arc lengths and the parts inside the
      three column outlines it carries;
  (d) the planted 1F column COL-1F-57 (T-248: DRAWING-CONFIRMED from the slab top it stands on): its joint faces by the
      r3 face trace (column_face_trace + stated_joint), which r3 never computed because it held the column.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(RES / "agents_t163"))
sys.path.insert(0, str(RES / "agents_t252"))
import t163_formwork as T  # noqa: E402  (merged r3, read-only)
import t252_extract as X  # noqa: E402  (merged T-252 ring spec, read-only)

SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
PROBE = 0.005                       # m beyond a piece's mid point (well clear of the tangent points of the void)
RING_FACES_R3 = ("GF-035", "GF-060")  # the two B7 ring band pieces r3 bound to a member (T-139 'B7 ring band piece')
RING_MIX_FACE = "GF-040"            # r3: void + 0.391 m2 of ring drawn as one face (RING_MIX, held)
ARC_GB = dict(inner="157", outer="158", columns=("17BA", "17BD", "17C0"))   # T-242 ARC:157+158 (MAIN, EXT)
OBLIQUE = {"BM-GF-017#BAND0018": ("27D", "282"), "BM-GF-021#BAND0021.1": ("288", "285")}


def _arc(doc, h):
    e = doc.entitydb.get(h)
    c = e.dxf.center
    return (c.x / 1000.0, c.y / 1000.0), e.dxf.radius / 1000.0, e.dxf.start_angle, e.dxf.end_angle


def _line(doc, h):
    e = doc.entitydb.get(h)
    return (e.dxf.start.x / 1000.0, e.dxf.start.y / 1000.0), (e.dxf.end.x / 1000.0, e.dxf.end.y / 1000.0)


def _sweep(a0, a1):
    return (a1 - a0) % 360.0


def _pt(c, R, a):
    return c[0] + R * math.cos(math.radians(a)), c[1] + R * math.sin(math.radians(a))


def ring_pieces(doc, spec):
    """the closed loop of one T-252 ring boundary: [(kind, handle, length, mid, outward normal at mid)] in loop order
    (ccw); a 'face' piece runs from the previous arc's end to the next arc's start on the named face line."""
    arcs = [_arc(doc, h) if k == "arc" else None for k, h in spec]
    out = []
    for i, (k, h) in enumerate(spec):
        if k == "arc":
            c, R, a0, a1 = arcs[i]
            sw = _sweep(a0, a1)
            am = a0 + sw / 2.0
            out.append(dict(kind="arc", handle=h, R=R, sweep_deg=sw, length=R * math.radians(sw),
                            mid=_pt(c, R, am), radial=(math.cos(math.radians(am)), math.sin(math.radians(am)))))
        else:
            pc, pR, _p0, pa1 = arcs[i - 1]
            nc, nR, na0, _n1 = arcs[(i + 1) % len(spec)]
            p, q = _pt(pc, pR, pa1), _pt(nc, nR, na0)
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
            out.append(dict(kind="line", handle=h, length=L, mid=((p[0] + q[0]) / 2, (p[1] + q[1]) / 2),
                            radial=(uy, -ux)))       # right-hand normal of a ccw loop = outward
    return out


def who(polys, kinds, pt):
    from shapely.geometry import Point
    P = Point(pt)
    for fid, g in polys.items():
        if g.contains(P):
            return fid, kinds.get(fid)
    return None, "OUT"


def main(argv):
    import ezdxf
    from shapely import wkt
    from shapely.geometry import LineString, Polygon

    dxf, faces_json = argv[:2]
    sha = hashlib.sha256(Path(dxf).read_bytes()).hexdigest()
    if sha != SHA:
        raise SystemExit("DXF sha %s is not the manifest copy %s" % (sha, SHA))
    doc = ezdxf.readfile(dxf)
    import tempfile
    lines3, summ3, walk3, beams, cols, _g = T.alsenan(faces_json, tempfile.mkdtemp(), rule="r3")
    w = walk3["GF"]
    F = {f["id"]: wkt.loads(f["wkt"]) for f in json.load(open(faces_json, encoding="utf-8"))["GF"]}

    # (a) ring: pieces of the outer boundary and of the void, the face beyond each
    def dense(spec, n=2000):
        pts = []
        for k, h in spec:
            if k == "arc":
                c, R, a0, a1 = _arc(doc, h)
                sw = _sweep(a0, a1)
                pts += [_pt(c, R, a0 + sw * t / n) for t in range(n + 1)]
        return Polygon(pts).buffer(0)
    void = dense(X.RING["void"])
    outer = dense(X.RING["outer"])
    ringp = outer.difference(void)
    from shapely.geometry import Point
    kinds = {k: w["kind"].get(k, "") for k in F}
    out_r = {"outer": [], "void": []}
    for key in ("outer", "void"):
        for p in ring_pieces(doc, X.RING[key]):
            mx, my = p["mid"]
            rx, ry = p["radial"]
            cand = [(mx + rx * PROBE, my + ry * PROBE), (mx - rx * PROBE, my - ry * PROBE)]
            if key == "void" and p["kind"] == "arc":
                # a void arc is the ring's inner face: the void is beyond it by construction (the mid point of a small
                # arc can lie within mm of a tangent point, so it is never probed)
                fid, kind = None, "VOID"
            else:
                # the side that is neither ring nor void (an outer piece's neighbour; the beam a void line belongs to)
                away = [c for c in cand if not ringp.buffer(1e-4).contains(Point(c)) and not void.contains(Point(c))]
                if len(away) != 1:
                    raise SystemExit("piece %s: %d candidate sides beyond the ring" % (p["handle"], len(away)))
                fid, kind = who(F, kinds, away[0])
            assign = w["assign"].get(fid) if fid else None
            member = assign[1] if assign else None
            depth = next((b["D"] for b in beams if b["member"] == member), None) if member else None
            out_r[key].append(dict(kind=p["kind"], handle=p["handle"], length_m=round(p["length"], 6),
                                   R_m=round(p["R"], 6) if "R" in p else None,
                                   sweep_deg=round(p["sweep_deg"], 4) if "sweep_deg" in p else None,
                                   beyond_face=fid, beyond_kind=kind, beyond_member=member, beyond_D=depth))
    # r3's own measure on the ring pieces it bound, and the RING_MIX lengths it held
    acc = w["acc"]
    r3_ring = dict(soffit_m2={f: round(w["polys"][f].area, 6) for f in RING_FACES_R3},
                   side_m2={f: round(acc.get(("BEAM_SIDE", f), 0.0), 6) for f in RING_FACES_R3})
    ring_mix = {}
    for i, nk, j, L, tr in w["edges"]:
        if nk == "RING_MIX":
            ring_mix.setdefault(i, 0.0)
            ring_mix[i] += L
    r3_ring["ring_mix_len_by_face"] = {k: round(v, 6) for k, v in sorted(ring_mix.items())}
    r3_ring["ring_mix_face_area_m2"] = round(F[RING_MIX_FACE].area, 6)
    ring = dict(marks=list(X.RING["marks"]), pieces=out_r, r3=r3_ring, void_m2=round(void.area, 6),
                ring_m2=round(ringp.area, 6))

    # (b) oblique ends: the T-139 face that holds each band and its length on each drawn edge
    obl = {}
    for run, (ha, hb) in OBLIQUE.items():
        la, lb = LineString(_line(doc, ha)), LineString(_line(doc, hb))
        faces = {}
        for f, g in F.items():
            a_, b_ = g.buffer(0.001).intersection(la).length, g.buffer(0.001).intersection(lb).length
            if a_ > 0.05 or b_ > 0.05:
                faces[f] = dict(face_m2=round(g.area, 6), member=(w["assign"].get(f) or (None, None))[1],
                                kind=w["kind"].get(f), on_edge_m={ha: round(a_, 5), hb: round(b_, 5)})
        obl[run] = dict(faces=faces, edge_len_m={ha: round(la.length, 5), hb: round(lb.length, 5)})

    # (c) ring ground beam ARC:157+158: arc lengths and the parts inside the column outlines it carries
    colpoly = {}
    for h in ARC_GB["columns"]:
        e = doc.entitydb.get(h)
        colpoly[h] = Polygon([(x / 1000.0, y / 1000.0) for x, y in e.get_points("xy")])
    arcgb = {}
    for side in ("inner", "outer"):
        c, R, a0, a1 = _arc(doc, ARC_GB[side])
        sw = _sweep(a0, a1)
        poly = LineString([_pt(c, R, a0 + sw * t / 4000) for t in range(4001)])
        inside = {h: round(poly.intersection(P.buffer(1e-6)).length, 5) for h, P in colpoly.items()}
        arcgb[side] = dict(handle=ARC_GB[side], R_m=round(R, 6), sweep_deg=round(sw, 4),
                           length_m=round(R * math.radians(sw), 6), inside_columns_m=inside)

    # (d) planted COL-1F-57: r3 face trace on the 1F walk and the stated-section joint
    c57 = next(c for c in cols if c["id"] == "COL-1F-57")
    dep = {b["member"]: b["D"] for b in beams}
    tr = T.column_face_trace(c57, walk3["1F"], dep)
    lo, hi, st, note = T.stated_joint(c57, tr)
    drawn = sum(L * h for f in tr.values() for k, m, L, h in f["pieces"] if h is not None)
    col57 = dict(id="COL-1F-57", drawn=c57["drawn"], section="%.2fx%.2f" % (c57["a"], c57["b"]), Dctrl=c57["Dctrl"],
                 joint_drawn_m2=round(drawn, 6), joint_stated_lo=lo, joint_stated_hi=hi, stated_status=st, note=note,
                 faces={k: [(kk, mm, round(L, 4), h) for kk, mm, L, h in v["pieces"]] for k, v in tr.items()})
    w1 = walk3["1F"]
    own = [i for i, a in w1["assign"].items() if a[0] == "COLUMN" and a[1] == "COL-1F-57"]
    col57["r3_walk_acc"] = {"%s|%s" % (cat, i): round(v, 6) for (cat, i), v in sorted(w1["acc"].items()) if i in own
                            and (cat.startswith("JOINT") or cat == "EDGE_BAND")}

    out = dict(schema="T264_R4_INPUT", source_dxf_sha256=sha, units="m", r3_totals=summ3 and T.totals(lines3),
               void_ring=ring, oblique_ends=obl, arc_ground_beam=arcgb, planted_col_1f_57=col57)
    txt = json.dumps(out, indent=1, sort_keys=True, default=lambda o: round(o, 6) if isinstance(o, float) else str(o))
    if len(argv) > 2:
        Path(argv[2]).write_text(txt + "\n", encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
