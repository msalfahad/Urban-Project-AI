"""T-403 extractor: private structural DXF -> values-only ALSENAN_T403_INPUT.json (handles, lengths, areas; no
coordinates, no drawing text, no names).

Usage (from the engine root; the DXF decoded into .work/private only):
    python3 -I research/agents_t403/t403_extract.py "<.work/private>/ST7757.dxf"           # check the committed input
    python3 -I research/agents_t403/t403_extract.py "<.work/private>/ST7757.dxf" --write   # rebuild it

Reads, by handle (nothing typed by hand):
  * the GROUND BEAMS PLAN boundary G.B band S-BOUN 7FE / 7FC / 810 (T-253: upper G.B 20 x 40, top at N.G.);
  * the FOUNDATION PLAN plot polyline S-BOUN 1658 and the inner band line 1659 (the lower boundary band, T-065 / T-356);
  * the footing outlines of research/agents_t347/PITS_T347.csv (as T-356);
  * layer-1 lines of the ground-beams plan (house ground-beam faces) inside the upper G.B band (overlap guard).

The two sheets share the y frame; the x translation is the difference of the plot's west edge (7FE outer west face vs
1658 west side) and is checked on the east edge (both must agree to 0.001 mm).
The lower band is split along its centreline (0.10 m inside the plot, i.e. the 0.20 band's axis) into:
  FENCE   the part under the upper G.B footprint (the fence band, the T-253 / T-396 runs);
  POOL    the part on the sea side between 7FC and the 7FE east leg (the pool back, T-392);
  HOUSE   the rest, per plot side (the house's own ground beams stand on the boundary there).
"""

import csv
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
OUT = os.path.join(HERE, "ALSENAN_T403_INPUT.json")
HALF = 100.0  # half the drawn 0.20 band (mm): the band axis


def _r(x, n=4):
    return round(x + 0.0, n)


def main(argv):
    import ezdxf
    from shapely.affinity import translate
    from shapely.geometry import LineString, Polygon, box
    from shapely.ops import polygonize, unary_union

    dxf = argv[0]
    if hashlib.sha256(open(dxf, "rb").read()).hexdigest() != DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    doc = ezdxf.readfile(dxf)
    db, msp = doc.entitydb, doc.modelspace()

    def pts(h):
        return [(q[0], q[1]) for q in db[h].get_points()]

    def outline(handle):  # as research/agents_t356/t356_extract.py
        e = db.get(handle)
        if e is None:
            return None
        if e.dxftype() == "LWPOLYLINE":
            return Polygon([p[:2] for p in e.get_points()]).buffer(0)
        if e.dxftype() == "INSERT":
            x, y = e.dxf.insert.x, e.dxf.insert.y
            a, b = 500.0 * e.dxf.xscale, 500.0 * e.dxf.yscale
            if e.dxf.rotation % 180:
                a, b = b, a
            return box(x - a, y - b, x + a, y + b)
        if e.dxftype() == "LINE":
            cx = (e.dxf.start.x + e.dxf.end.x) / 2
            cy = (e.dxf.start.y + e.dxf.end.y) / 2
            ls = [LineString([(x.dxf.start.x, x.dxf.start.y), (x.dxf.end.x, x.dxf.end.y)])
                  for x in msp.query("LINE[layer=='S-FOOTINGS']")
                  if abs(x.dxf.start.x - cx) < 1300 and abs(x.dxf.start.y - cy) < 1300]
            sq = [p for p in polygonize(unary_union(ls)) if abs(p.area - 1e6) < 5e3]
            return sq[0] if len(sq) == 1 else None
        return None

    FT = {}
    for r in csv.DictReader(open(os.path.join(ROOT, "research/agents_t347/PITS_T347.csv"), encoding="utf-8")):
        tok = r["outline_handle"].split()
        if not tok:
            continue
        hd = tok[1] if tok[0] == "INSERT" else (tok[2] if tok[0] == "4" else tok[0])
        poly = outline(hd)
        if poly is None:
            raise SystemExit(f"outline {hd} not read")
        FT[f"{r['type']}:{hd}"] = poly

    plot = Polygon(pts("1658"))
    inner = Polygon(pts("1659"))
    upper = {h: Polygon(pts(h)) for h in ("7FE", "7FC", "810")}
    gb_x0 = min(p[0] for p in pts("7FE"))
    gb_x1 = max(p[0] for p in pts("7FE"))
    dx = plot.bounds[0] - gb_x0
    dx_east_check = _r((plot.bounds[2] - gb_x1) - dx, 3)
    if abs(dx_east_check) > 0.001:
        raise SystemExit("sheet translation does not close on the east edge")
    up_f = {h: translate(p, xoff=dx) for h, p in upper.items()}
    UP = unary_union(list(up_f.values()))

    cl = LineString(list(plot.buffer(-HALF, join_style=2).exterior.coords))
    x0, y0, x1, y1 = plot.bounds
    eps = HALF + 1.0
    sides = {"N": box(x0 - 1, y1 - eps, x1 + 1, y1 + 1), "S": box(x0 - 1, y0 - 1, x1 + 1, y0 + eps),
             "W_STREET": box(x0 - 1, y0 + eps, x0 + eps, y1 - eps), "E_SEA": box(x1 - eps, y0 + eps, x1 + 1, y1 - eps)}
    # the pool back: sea side between the top of 7FC and the bottom of the 7FE east leg
    fc_top = up_f["7FC"].bounds[3]
    fe_east_bottom = min(p[1] for p in pts("7FE") if p[0] > gb_x1 - 1.0)
    pool_box = box(x1 - eps, fc_top, x1 + 1, fe_east_bottom)

    def seg_len(geom):
        return cl.intersection(geom).length / 1000.0

    def footing_cross(geom):
        g = cl.intersection(geom)
        out = []
        for k, p in sorted(FT.items()):
            v = g.intersection(p).length / 1000.0
            if v > 1e-6:
                out.append([k, _r(v)])
        return out

    runs = {}
    for name, h in (("FENCE_7FE", "7FE"), ("FENCE_7FC", "7FC"), ("FENCE_810", "810")):
        g = up_f[h]
        per_side = {s: _r(seg_len(g.intersection(b))) for s, b in sides.items() if seg_len(g.intersection(b)) > 1e-6}
        runs[name] = {"class": "FENCE", "upper_gb_handle": h, "upper_gb_area_m2": _r(upper[h].area / 1e6, 6),
                      "upper_gb_len_by_area_m": _r(upper[h].area / 1e6 / 0.2),
                      "lower_band_axis_m": _r(seg_len(g)), "axis_by_side_m": per_side, "footing_crossings_m": footing_cross(g)}
    rest = plot.buffer(10.0).difference(UP)
    runs["POOL_BACK"] = {"class": "POOL", "lower_band_axis_m": _r(seg_len(pool_box.intersection(rest))),
                         "footing_crossings_m": footing_cross(pool_box.intersection(rest))}
    house = rest.difference(pool_box)
    for s, b in sides.items():
        g = house.intersection(b)
        L = seg_len(g)
        if L > 1e-6:
            runs[f"HOUSE_{s}"] = {"class": "HOUSE", "lower_band_axis_m": _r(L), "footing_crossings_m": footing_cross(g)}

    # overlap guard: house ground-beam faces (layer 1) of the ground-beams plan inside the upper G.B band
    UPg = unary_union(list(upper.values())).buffer(-5.0)
    gb_face_inside_mm = 0.0
    for e in msp.query("LINE[layer=='1']"):
        L = LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
        gb_face_inside_mm += L.intersection(UPg).length
    col_inside = 0
    for e in msp.query("LINE[layer=='S-COL.BON']"):
        L = LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
        col_inside += int(L.intersection(UPg).length > 1.0)

    total_axis = cl.length / 1000.0
    out = {
        "schema": "URBAN_T403_INPUT_V1",
        "source": {"drive": "Alsenan chalet project / ST7757 dxf.dxf", "sha256": DXF_SHA,
                   "frames": "GROUND BEAMS PLAN (S-BOUN 7FE / 7FC / 810) -> FOUNDATION PLAN (S-BOUN 1658 / 1659)",
                   "translation_check_east_mm": dx_east_check},
        "lower_band": {"outer_handle": "1658", "inner_handle": "1659", "band_area_m2": _r(plot.difference(inner).area / 1e6, 6),
                       "axis_m": _r(total_axis), "width_m": 0.2},
        "upper_gb_total_len_by_area_m": _r(sum(p.area for p in upper.values()) / 1e6 / 0.2),
        "runs": runs,
        "runs_axis_sum_m": _r(sum(v["lower_band_axis_m"] for v in runs.values())),
        "guards": {"house_gb_face_mm_inside_upper_gb": _r(gb_face_inside_mm, 3),
                   "boundary_column_lines_inside_upper_gb": col_inside},
    }
    return out


if __name__ == "__main__":
    data = main(sys.argv[1:])
    text = json.dumps(data, indent=1, sort_keys=True) + "\n"
    if "--write" in sys.argv:
        open(OUT, "w", encoding="utf-8").write(text)
        print(OUT)
    else:
        same = os.path.exists(OUT) and open(OUT, encoding="utf-8").read() == text
        print(text)
        print("committed input reproduced:", same)
        sys.exit(0 if same else 1)
