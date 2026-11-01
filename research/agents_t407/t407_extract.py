"""T-407 extractor: private structural DXF -> values-only ALSENAN_T407_INPUT.json (handles, lengths; no coordinates,
no drawing text, no names).

Usage (from the engine root; the DXF decoded into .work/private only):
    python3 -I research/agents_t407/t407_extract.py "<.work/private>/ST7757.dxf"           # check the committed input
    python3 -I research/agents_t407/t407_extract.py "<.work/private>/ST7757.dxf" --write   # rebuild it

What it reads (by handle, nothing typed by hand):
  * the FOUNDATION PLAN lower boundary band S-BOUN 1658 / 1659 (T-065 / T-356 / T-403) and its axis, 0.10 m inside;
  * the GROUND BEAMS PLAN fence band S-BOUN 7FE / 7FC / 810 (T-253), translated onto the foundation frame exactly as
    research/agents_t403/t403_extract.py does (x shift from the west edge, checked on the east edge);
  * the house exterior ground-beam faces of layer 1 that lie ON the plot line (outer face within 1 mm of it), i.e. the
    house beams that stand over the lower band; every other layer-1 face is inside the plot;
  * the S-COL.BON column outlines of the ground-beams plan cut by the band axis (necks through the masonry plane);
  * the footing outlines of research/agents_t347/PITS_T347.csv cut by the band axis (as T-403).

The HOUSE part of the band (T-403: not under the fence band, not the pool back) is split per plot side and, on the
south (neighbour) side, at the 810 passage band: west of it the annex, east of it the main house. Per run it reports
the band axis length, the plot-line house beam faces over it (handle + length), the column pieces and the footing
crossings along the axis. Every length is a band-axis length in m.
"""

import csv
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
OUT = os.path.join(HERE, "ALSENAN_T407_INPUT.json")
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

    def outline(handle):  # identical to research/agents_t403/t403_extract.py
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
    fc_top = up_f["7FC"].bounds[3]
    fe_east_bottom = min(p[1] for p in pts("7FE") if p[0] > gb_x1 - 1.0) + 0.0
    pool_box = box(x1 - eps, fc_top, x1 + 1, fe_east_bottom)
    house = plot.buffer(10.0).difference(UP).difference(pool_box)

    # the 810 passage band splits the south side: annex west of it, main house east of it
    p810 = up_f["810"].bounds
    split = {"ANNEX_S": box(x0 - 1, y0 - 1, p810[0], y0 + eps), "MAIN_S": box(p810[2], y0 - 1, x1 + 1, y0 + eps),
             "ANNEX_W_STREET": sides["W_STREET"], "MAIN_E_SEA": sides["E_SEA"], "HOUSE_N": sides["N"]}

    # house exterior ground-beam faces (layer 1, ground-beams plan) lying on the plot line, translated
    plot_line = plot.exterior
    faces = []
    for e in msp.query("LINE[layer=='1']"):
        L = translate(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]), xoff=dx)
        on = L.intersection(plot_line.buffer(1.0)).length
        if on > 1.0 and abs(on - L.length) < 1.0:
            faces.append((e.dxf.handle, L))
    # column outlines (S-COL.BON closed polylines) of the ground-beams plan, translated
    cols = []
    for e in msp.query("LWPOLYLINE[layer=='S-COL.BON']"):
        poly = Polygon([p[:2] for p in e.get_points()]).buffer(0)
        if poly.area > 1e4:
            cols.append(([e.dxf.handle], translate(poly, xoff=dx)))
    # columns cut by the band axis (the band axis passes through their outline): one record per outline
    runs = {}
    for name, b in split.items():
        g = cl.intersection(house.intersection(b))
        L = g.length / 1000.0
        if L < 1e-6:
            continue
        ftg = [[k, _r(g.intersection(p).length / 1000.0)] for k, p in sorted(FT.items()) if g.intersection(p).length > 1e-3]
        colp = []
        for hs, poly in cols:
            v = g.intersection(poly).length / 1000.0
            if v > 1e-6:
                colp.append([hs[0] if hs else "?", _r(v), _r(poly.area / 1e6, 4)])
        colp.sort()
        gbf = []
        for h, Lf in faces:
            v = Lf.intersection(b).length / 1000.0
            if v > 1e-6:
                gbf.append([h, _r(v)])
        gbf.sort()
        runs[name] = {"band_axis_m": _r(L), "footing_crossings_m": ftg, "column_pieces_m": colp,
                      "house_gb_faces_on_plot_line_m": gbf}
    # guard: every plot-line house face is on a run of the HOUSE band (none under the fence band)
    face_on_fence_mm = sum(Lf.intersection(UP.buffer(-5.0)).length for _, Lf in faces)
    frames = [plot.buffer(2000.0), translate(unary_union(list(upper.values())).envelope.buffer(2000.0), xoff=0.0)]
    gb_frame = box(gb_x0 - 2000.0, plot.bounds[1] - 2000.0, gb_x1 + 2000.0, plot.bounds[3] + 2000.0)
    from ezdxf import bbox as _bb
    other_boun = []
    for e in msp.query("*[layer=='S-BOUN']"):
        if e.dxf.handle in ("1658", "1659", "7FE", "7FC", "810"):
            continue
        ex = _bb.extents([e])
        g = box(ex.extmin.x, ex.extmin.y, ex.extmax.x + 1e-3, ex.extmax.y + 1e-3)
        if g.within(frames[0]) or g.within(gb_frame):
            other_boun.append(e.dxf.handle)
    house_axis = cl.intersection(house)
    fence_axis_overlap_mm = house_axis.intersection(UP.buffer(-1.0)).length
    out = {
        "schema": "URBAN_T407_INPUT_V1",
        "source": {"drive": "Alsenan chalet project / ST7757 dxf.dxf", "sha256": DXF_SHA,
                   "frames": "GROUND BEAMS PLAN (layer 1, S-COL.BON, S-BOUN 7FE / 7FC / 810) -> FOUNDATION PLAN (S-BOUN 1658 / 1659)",
                   "translation_check_east_mm": dx_east_check},
        "runs": runs,
        "house_axis_sum_m": _r(sum(v["band_axis_m"] for v in runs.values())),
        "guards": {"plot_line_house_faces": sorted(h for h, _ in faces),
                   "plot_line_house_face_mm_inside_fence_band": _r(face_on_fence_mm, 3),
                   "house_axis_mm_inside_fence_band": _r(fence_axis_overlap_mm, 3),
                   "band_axis_total_m": _r(cl.length / 1000.0),
                   "other_s_boun_entities_in_the_two_plan_frames": sorted(other_boun)},
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
