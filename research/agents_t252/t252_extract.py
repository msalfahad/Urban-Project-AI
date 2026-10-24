"""T-252 extractor: private 'ST7757 dxf.dxf' (Drive "Alsenan chalet project", sha256 9f9d1179...) -> the derived
values ALSENAN_R2_INPUT.json holds (lengths, widths, areas and DXF handles only; no coordinates, no drawing content).

    python3 -I research/agents_t252/t252_extract.py <ST7757 dxf.dxf> <faces.json> <bands.json> [out.json]

faces.json = `python3 -I research/agents_t139/slab_faces.py <dxf> faces.json` (T-139 faces, the partition T-234 and
T-241 used); bands.json = `python3 -I research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/
st7757_route_g bands.json` (route G band polygons on the DXF frame). Run from the checkout root on Python 3.11.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import beam_ledger_r2 as R2  # noqa: E402

SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"

# (a) members on the EAST face of B27 (S-BEAM line 325); start faces: column 362 south side (CB4 span 1), B22 west
#     face line 460 (B4 GF-017). Edges: layer-1 lines of each member, the end at the carrier listed second.
OBLIQUE_RUNS = {
    "BM-GF-021#BAND0021.1": dict(mark="CB4", edges=("288", "285"), start=("362", "south"), end="325", b=0.20, D=0.50),
    "BM-GF-017#BAND0018": dict(mark="B4", edges=("27D", "282"), start=("460", None), end="325", b=0.20, D=0.50),
}
# (b) GF void ring B7: outer boundary (ccw) and the void (ccw), each piece by handle; closing faces by handle
RING = dict(
    marks=("46E", "46F", "470", "471"),
    outer=[("arc", "2EE"), ("face", "46D"), ("arc", "2EF"), ("face", "42D"), ("arc", "312"), ("face", "2A9"),
           ("arc", "313"), ("face", "437")],
    void=[("arc", "2F0"), ("arc", "318"), ("arc", "310"), ("face", "2A9"), ("arc", "311"), ("arc", "317")],
    annuli=(("2EE", "2F0"), ("312", "310")),
    replaced_bands=("BAND0050@GF", "BAND0051@GF", "BAND0052@GF", "BAND0053@GF"),
)


def _ends_on(doc, h):
    e = doc.entitydb.get(h)
    s, t = e.dxf.start, e.dxf.end
    return (s.x / 1000.0, s.y / 1000.0), (t.x / 1000.0, t.y / 1000.0)


def oblique(doc):
    out = {}
    for rid, spec in OBLIQUE_RUNS.items():
        edges = []
        for h in spec["edges"]:
            p, q = _ends_on(doc, h)
            car = _ends_on(doc, spec["end"])
            cl = R2._line(*car)
            # orient: q = the end ON the carrier face
            if R2.dist_to_line(p, cl) < R2.dist_to_line(q, cl):
                p, q = q, p
            edges.append((p, q))
        sh, side = spec["start"]
        ent = doc.entitydb.get(sh)
        if ent.dxftype() == "LWPOLYLINE":
            pts = [(x / 1000.0, y / 1000.0) for x, y in ent.get_points("xy")]
            ymin = min(y for _, y in pts)
            sp = [p for p in pts if abs(p[1] - ymin) < 1e-6]
            start = (sp[0], sp[1])
        else:
            start = _ends_on(doc, sh)
        run = R2.run_between_faces(edges[0], edges[1], start, _ends_on(doc, spec["end"]), b_schedule=spec["b"],
                                   depth=spec["D"])
        out[rid] = dict(mark=spec["mark"], edges=list(spec["edges"]), start_face=sh, carrier_face=spec["end"],
                        b_drawn_m=round(run["b_drawn_m"], 5), La_m=round(run["La_m"], 5), Lb_m=round(run["Lb_m"], 5),
                        plan_m2=round(run["plan_m2"], 6), end_triangle_m2=round(run["end_triangle_m2"], 6),
                        b_schedule=spec["b"], depth_m=spec["D"])
    return out


def ring(doc, faces_json, bands_json):
    from shapely import wkt
    from shapely.geometry import Polygon

    def arc_of(h):
        e = doc.entitydb.get(h)
        c = e.dxf.center
        return (c.x / 1000.0, c.y / 1000.0), e.dxf.radius / 1000.0, e.dxf.start_angle, e.dxf.end_angle

    def build(spec):
        segs = []
        arcs = [arc_of(h) if k == "arc" else None for k, h in spec]
        for i, (k, h) in enumerate(spec):
            if k == "arc":
                c, R, a0, a1 = arcs[i]
                segs.append(("arc", c, R, a0, a1))
            else:
                # face piece: from the previous arc's end to the next arc's start, checked to lie on face line h
                pc, pR, _p0, pa1 = arcs[i - 1]
                nc, nR, na0, _n1 = arcs[(i + 1) % len(spec)]
                p = (pc[0] + pR * math.cos(math.radians(pa1)), pc[1] + pR * math.sin(math.radians(pa1)))
                q = (nc[0] + nR * math.cos(math.radians(na0)), nc[1] + nR * math.sin(math.radians(na0)))
                fl = R2._line(*_ends_on(doc, h))
                off = max(R2.dist_to_line(p, fl), R2.dist_to_line(q, fl))
                if off > R2.ON_FACE_TOL_M:
                    raise R2.Refused("closing piece %s is %.4f m off face line %s" % (i, off, h))
                segs.append(("line", p, q))
        return segs

    outer, void = build(RING["outer"]), build(RING["void"])
    radius = {h: arc_of(h)[1] for pair in RING["annuli"] for h in pair}
    res = R2.curved_member_area(outer, [void], annuli=[(radius[a], radius[b]) for a, b in RING["annuli"]],
                                b_schedule=0.20)

    def dens(segs, n=3000):
        pts = []
        for s in segs:
            if s[0] == "line":
                pts.append(s[1])
            else:
                _, c, R, a0, a1 = s
                sw = R2._norm_sweep(a0, a1)
                pts.extend((c[0] + R * math.cos(math.radians(a0 + sw * i / n)),
                            c[1] + R * math.sin(math.radians(a0 + sw * i / n))) for i in range(n))
        return Polygon(pts).buffer(0)

    rp = dens(outer).difference(dens(void))
    faces = json.load(open(faces_json, encoding="utf-8"))["GF"]
    face_hits = {}
    for f in faces:
        a = wkt.loads(f["wkt"]).intersection(rp).area
        if a > 1e-5:
            face_hits[f["id"]] = round(a, 5)
    bands = json.load(open(bands_json, encoding="utf-8"))
    band_hits = {}
    for k, b in bands.items():
        if not k.endswith("@GF"):
            continue
        p = Polygon(b["pts"])
        p = p if p.is_valid else p.buffer(0)
        a = p.intersection(rp).area
        if a > 1e-5:
            band_hits[k] = dict(title=b["title"], in_ring_m2=round(a, 5), band_m2=round(p.area, 5))
    cols = []
    for e in doc.modelspace().query('LWPOLYLINE[layer=="S-COL.BON"]'):
        pts = [(x / 1000.0, y / 1000.0) for x, y in e.get_points("xy")]
        if len(pts) >= 3 and Polygon(pts).buffer(0).intersection(rp).area > 1e-6:
            cols.append(e.dxf.handle)
    parts = sorted(round(g.area, 5) for g in getattr(rp, "geoms", [rp]))
    return dict(marks=list(RING["marks"]), outer_handles=[h for _k, h in RING["outer"]],
                void_handles=[h for _k, h in RING["void"]], area_m2=round(res["area_m2"], 6),
                outer_m2=round(res["outer_m2"], 6), void_m2=round(res["voids_m2"], 6),
                widths_m=[round(w, 4) for w in res["widths_m"]], max_gap_m=round(res["max_gap_m"], 6),
                polygon_check_m2=round(rp.area, 6), parts_m2=parts, t139_faces_in_ring_m2=face_hits,
                route_g_bands_in_ring=band_hits, replaced_bands=list(RING["replaced_bands"]),
                column_outlines_in_ring=cols)


def main(argv):
    import ezdxf

    dxf, faces_json, bands_json = argv[:3]
    sha = hashlib.sha256(Path(dxf).read_bytes()).hexdigest()
    if sha != SHA:
        raise SystemExit("DXF sha %s is not the manifest copy %s" % (sha, SHA))
    doc = ezdxf.readfile(dxf)
    out = dict(schema="T252_R2_INPUT", source_dxf_sha256=sha, units="m", oblique_runs=oblique(doc),
               void_ring=ring(doc, faces_json, bands_json))
    txt = json.dumps(out, indent=1, sort_keys=True)
    if len(argv) > 3:
        Path(argv[3]).write_text(txt + "\n", encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
