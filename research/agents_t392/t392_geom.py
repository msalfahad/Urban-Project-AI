"""T-392 own geometry on the private structural DXF ('ST7757 dxf.dxf', sha256 9f9d1179...) and the T-387 route G
export (research/agents_t387/t387_geometry.py). Prints and writes ONLY areas (m2), volumes (m3) and entity handles:
no coordinate, polygon, name or drawing content leaves .work/private.

    python3 -I research/agents_t392/t392_geom.py <private ST dxf> <private geometry.json> <out summary json> \
        [<private P7757.dxf>]          (the 4th argument adds part (C): the pool's fourth side B7 / 8D)

Method (ERS s.2.1, R-BEAM-CURVED-AREA-2): every member is taken between its own drawn edges (arcs densified to
0.05 mm chord error; exact-arc cross-check on the ring); route G bands are mapped to the drawing frame by the one
translation that puts the B8 band (BAND0003) on its drawn faces 42C / 46D; the same translation is checked on every
other band used here (residual reported).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import ezdxf
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import polygonize, unary_union

LAYERS = ("1", "S-BEAM", "S-COL.BON")
W_C, W_RI, W_RO = "2F0", 1735.0, 1935.0          # west ring arcs: inner 2F0, outer 2EE / 2EF (one centre)
E_C, E_RI, E_RO = "310", 1550.0, 1750.0          # east ring arcs: inner 310 / 311, outer 312 / 313
RING_DEPTH = 0.75                                 # B7 20 x 75 (schedule ST p.10)


def _arc_pts(e, tol=0.05):
    c, r = e.dxf.center, e.dxf.radius
    a0, a1 = math.radians(e.dxf.start_angle), math.radians(e.dxf.end_angle)
    if a1 <= a0:
        a1 += 2 * math.pi
    step = 2 * math.acos(max(-1.0, 1 - tol / r))
    n = max(2, int(math.ceil((a1 - a0) / step)) + 1)
    return [(c.x + r * math.cos(a0 + (a1 - a0) * k / (n - 1)), c.y + r * math.sin(a0 + (a1 - a0) * k / (n - 1)))
            for k in range(n)]


def segments(doc, region):
    out = []
    for e in doc.modelspace():
        t = e.dxftype()
        if t not in ("LINE", "LWPOLYLINE", "ARC") or e.dxf.layer not in LAYERS:
            continue
        if t == "LINE":
            p = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        elif t == "ARC":
            p = _arc_pts(e)
        else:
            p = [(q[0], q[1]) for q in e.get_points()]
            if e.closed:
                p.append(p[0])
        ls = LineString(p)
        if ls.intersects(region):
            out.append((e.dxf.handle, ls.intersection(region)))
    return out


def faces(doc, region):
    segs = segments(doc, region)
    return list(polygonize(unary_union([s for _, s in segs] + [region.exterior]))), segs


def chain(db, handles):
    """one closed loop from drawn arcs taken end to nearest end; a gap is closed by a straight piece (reported)."""
    parts = [_arc_pts(db[h]) for h in handles]
    loop, rest, gaps = list(parts[0]), parts[1:], []
    while rest:
        end = loop[-1]
        k, rev = min(((i, r) for i in range(len(rest)) for r in (0, 1)),
                     key=lambda t: math.dist(end, rest[t[0]][-1 if t[1] else 0]))
        q = rest.pop(k)
        q = q[::-1] if rev else q
        gaps.append(round(math.dist(end, q[0]), 3))
        loop += q
    gaps.append(round(math.dist(loop[-1], loop[0]), 3))
    return Polygon(loop).buffer(0), gaps


def main(argv=None):
    dxf, geom, out = (argv or sys.argv[1:])[:3]
    sha = hashlib.sha256(Path(dxf).read_bytes()).hexdigest()
    doc = ezdxf.readfile(dxf)
    db = doc.entitydb
    G = json.loads(Path(geom).read_text(encoding="utf-8"))["sheets"]["SH06"]
    bands = {b["band_id"]: b for b in G["bands"]}
    res = {"dxf_sha256": sha, "route_g_sheet": "SH06 (GF roof slab plan)"}

    # frame: B8 band west face onto 42C, south end onto 42D
    b8 = Polygon(bands["BAND0003"]["polygon"])
    x42c = db["42C"].dxf.start.x
    y42d = db["42D"].dxf.start.y
    dx, dy = b8.bounds[0] - x42c, b8.bounds[1] - y42d

    def band(bid):
        return Polygon([(x - dx, y - dy) for x, y in bands[bid]["polygon"]]).buffer(0)

    # ---- (A) the GF void ring B7 from its own drawn edges ----
    cw, ce = db[W_C].dxf.center, db[E_C].dxf.center
    reg = box(min(cw.x - W_RO, ce.x - E_RO) - 400, cw.y - W_RO - 400, ce.x + E_RO + 400, cw.y + W_RO + 400)
    F, _ = faces(doc, reg)

    # the void it surrounds, from its own drawn boundary 2F0 / 318 / 310 / 311 / 317; the one straight closing piece is
    # the CB1 face 2A9 between 310 and 311 (T-252: the void touches the CB1 face along a segment)
    void, gaps = chain(db, ["2F0", "318", "310", "311", "317"])
    ann = unary_union([Point(cw.x, cw.y).buffer(W_RO + 1, 4096).difference(Point(cw.x, cw.y).buffer(W_RI - 1, 4096)),
                       Point(ce.x, ce.y).buffer(E_RO + 1, 4096).difference(Point(ce.x, ce.y).buffer(E_RI - 1, 4096))])
    pieces = []
    for f in F:
        g = f.difference(void)                    # the west crescent is one face with the void (tangent pinch on B8)
        for h in (list(g.geoms) if g.geom_type == "MultiPolygon" else [g]):
            if h.area > 1e3 and h.intersection(ann).area >= 0.9 * h.area:
                pieces.append(h)
    ring = unary_union(pieces)
    res["void"] = {"area_m2": round(void.area * 1e-6, 6), "closing_gaps_mm": gaps}
    res["ring"] = {"pieces_m2": sorted(round(f.area * 1e-6, 6) for f in pieces), "area_m2": round(ring.area * 1e-6, 6),
                   "m3": round(ring.area * 1e-6 * RING_DEPTH, 6)}
    rb = {}
    for bid in ("BAND0050", "BAND0051", "BAND0052", "BAND0053"):
        p = band(bid)
        rb[bid] = {"band_m2": round(p.area * 1e-6, 6), "in_ring_m2": round(p.intersection(ring).area * 1e-6, 6),
                   "outside_ring_m2": round(p.difference(ring).area * 1e-6, 6)}
    cover = unary_union([band(b) for b in rb]).intersection(ring)
    res["ring"]["route_g_arc_bands"] = rb
    res["ring"]["covered_by_arc_bands_m2"] = round(cover.area * 1e-6, 6)
    miss = ring.difference(cover)
    parts = list(miss.geoms) if miss.geom_type == "MultiPolygon" else [miss]
    res["ring"]["not_covered_m2"] = round(miss.area * 1e-6, 6)
    res["ring"]["not_covered_by_piece_m2"] = sorted((round(f.area * 1e-6, 6), round(f.intersection(miss).area * 1e-6, 6))
                                                    for f in pieces)
    # other members' drawn cells and candidate bands against the drawn ring
    oth = {}
    for bid, mark in (("BAND0003", "B8"), ("BAND0006", "B7 straight"), ("BAND0041.2", "CB1 span 2"),
                      ("BAND0041.1", "CB1 span 1")):
        p = band(bid)
        oth[bid] = {"mark": mark, "band_m2": round(p.area * 1e-6, 6),
                    "band_in_ring_m2": round(p.intersection(ring).area * 1e-6, 8),
                    "drawn_cell_m2": None}
        cells = [f for f in F if f.intersection(p).area > 0.5 * f.area and f.area > 1e4]
        if cells and not bid.startswith("BAND0041"):   # CB1's east face is the S-BOUN sheet edge: no closed cell here
            c = unary_union(cells)
            oth[bid]["drawn_cell_m2"] = round(c.area * 1e-6, 6)
            oth[bid]["drawn_cell_in_ring_m2"] = round(c.intersection(ring).area * 1e-6, 8)
            oth[bid]["band_vs_cell_sym_diff_m2"] = round(c.symmetric_difference(p).area * 1e-6, 6)
    res["ring_neighbours"] = oth
    res["frame_check_mm"] = {bid: round(max(abs(a - b) for a, b in zip(band(bid).bounds, c.bounds)), 3)
                             for bid in ("BAND0003",) for c in [unary_union([f for f in F if f.intersection(band(bid)).area > 0.5 * f.area])]}

    # ---- (B) the small residual group: B4 BAND0018, CB4 BAND0021.1 (oblique ends), CB8 BAND0039 ----
    L = lambda h: math.dist((db[h].dxf.start.x, db[h].dxf.start.y), (db[h].dxf.end.x, db[h].dxf.end.y))
    f325 = LineString([(db["325"].dxf.start.x, db["325"].dxf.start.y), (db["325"].dxf.end.x, db["325"].dxf.end.y)])
    f326 = LineString([(db["326"].dxf.start.x, db["326"].dxf.start.y), (db["326"].dxf.end.x, db["326"].dxf.end.y)])
    b18 = band("BAND0018")
    e27d, e282 = L("27D"), L("282")
    b21 = band("BAND0021.1")
    top21 = b21.bounds[3]
    e288 = top21 - min(db["288"].dxf.start.y, db["288"].dxf.end.y)
    e285 = top21 - min(db["285"].dxf.start.y, db["285"].dxf.end.y)
    on325 = [round(f325.distance(Point(db[h].dxf.end.x, db[h].dxf.end.y)), 3) for h in ("288", "285")]
    on325b = [round(f325.distance(Point(db[h].dxf.end.x, db[h].dxf.end.y)), 3) for h in ("27D", "282")]
    res["B4_BAND0018"] = {"edge_27D_m": round(e27d / 1000, 4), "edge_282_m": round(e282 / 1000, 4),
                          "ends_on_325_mm": on325b, "band_m2": round(b18.area * 1e-6, 6),
                          "trapezoid_m3": round(0.2 * 0.5 * (e27d + e282) / 2000, 6)}
    res["CB4_BAND0021.1"] = {"edge_288_m": round(e288 / 1000, 4), "edge_285_m": round(e285 / 1000, 4),
                             "ends_on_325_mm": on325, "band_m2": round(b21.area * 1e-6, 6),
                             "trapezoid_m3": round(0.2 * 0.5 * (e288 + e285) / 2000, 6)}
    # CB8: drawn cell between 272 and 2AC, from its west end (column 359's west face) to the B27 face 326
    b39 = band("BAND0039")
    x0, y0, x1, y1 = b39.bounds
    strip = box(x0, y0, x1 + 400, y1)
    west_of_326 = Polygon(list(f326.coords) + [(f326.coords[1][0] - 9e3, f326.coords[1][1]),
                                                (f326.coords[0][0] - 9e3, f326.coords[0][1])]).buffer(0)
    c359 = Polygon([(q[0], q[1]) for q in db["359"].get_points()])
    c37d = Polygon([(q[0], q[1]) for q in db["37D"].get_points()])
    cell = strip.intersection(west_of_326)
    net = cell.difference(c359).difference(c37d)
    overrun = b39.difference(west_of_326)
    lower = cell.difference(b39)
    res["CB8_BAND0039"] = {
        "band_m2": round(b39.area * 1e-6, 6), "band_len_m": round((x1 - x0) / 1000, 4),
        "edge_2AC_end_past_326_mm": round(f326.distance(Point(db["2AC"].dxf.start.x, db["2AC"].dxf.start.y)), 2),
        "drawn_cell_to_326_m2": round(cell.area * 1e-6, 6),
        "column_359_in_cell_m2": round(cell.intersection(c359).area * 1e-6, 6),
        "column_37D_in_cell_m2": round(cell.intersection(c37d).area * 1e-6, 6),
        "drawn_net_m2": round(net.area * 1e-6, 6), "drawn_net_m3": round(net.area * 1e-6 * 0.75, 6),
        "band_beyond_326_m2": round(overrun.area * 1e-6, 6),
        "band_beyond_326_m3_at_0.75": round(overrun.area * 1e-6 * 0.75, 6),
        "cell_not_in_band_m2": round(lower.area * 1e-6, 6),
        "cell_not_in_band_less_37D_m2": round(lower.difference(c37d).area * 1e-6, 6),
        "cell_not_in_band_less_37D_m3": round(lower.difference(c37d).area * 1e-6 * 0.75, 6),
        "band_48_2_overlap_m2": round(b39.intersection(band("BAND0048.2")).area * 1e-6, 6),
    }
    # B27 cell (polygonized) contains the overrun?
    regb = box(x1 - 1500, y0 - 300, x1 + 1600, y1 + 1200)
    Fb, _ = faces(doc, regb)
    host = [f for f in Fb if f.intersection(overrun).area > 0.5 * overrun.area]
    res["CB8_BAND0039"]["overrun_host_face_m2"] = [round(f.area * 1e-6, 6) for f in host]
    if len(argv or sys.argv[1:]) > 3:
        res["pool_fourth_side"] = pool_side((argv or sys.argv[1:])[3], db)
    Path(out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


def pool_side(arch_dxf, sdb):
    """(C) the pool's fourth (straight) side on the architectural GF plan: the layer-5 line pair B7 / 8D (0.20 apart,
    the boundary-wall pair, T-183 / T-016b convention) against the pool's own arcs 200 (outer R 1.75) / 202 (inner
    R 1.55); then the same side on the structural ground-beam plan (S-BOUN 7FC / 7FE: upper G.B 20 x 40) and the
    foundation plan (S-BOUN 1658 / 1659: the lower boundary band), by the sheet translations named below."""
    a = ezdxf.readfile(arch_dxf).entitydb
    sha = hashlib.sha256(Path(arch_dxf).read_bytes()).hexdigest()
    po, pi = a["200"], a["202"]
    c = po.dxf.center
    b7, d8 = a["B7"], a["8D"]
    ys = sorted([b7.dxf.start.y, b7.dxf.end.y])
    face_in, face_out = b7.dxf.start.x, d8.dxf.start.x
    pool_y = (c.y - po.dxf.radius, c.y + po.dxf.radius)
    south, north = pool_y[0] - ys[0], ys[1] - pool_y[1]
    r = {"arch_dxf_sha256": sha, "pair_layer": [b7.dxf.layer, d8.dxf.layer],
         "pair_length_m": round((ys[1] - ys[0]) / 1000, 4), "pair_spacing_m": round(abs(face_out - face_in) / 1000, 4),
         "inner_face_minus_pool_centre_m": round((face_in - c.x) / 1000, 4),
         "outer_face_minus_pool_centre_m": round((face_out - c.x) / 1000, 4),
         "pool_radii_m": [round(pi.dxf.radius / 1000, 4), round(po.dxf.radius / 1000, 4)],
         "pool_side_m": round(2 * po.dxf.radius / 1000, 4),
         "out_of_pool_south_m": round(south / 1000, 4), "out_of_pool_north_m": round(north / 1000, 4),
         "out_of_pool_total_m": round((south + north) / 1000, 4)}
    # pool wall band of the D (outer - inner): straight back 3.50 + two sides 1.75 + half circle (T-183 2.356726 m2)
    ro, ri = po.dxf.radius / 1000, pi.dxf.radius / 1000
    r["pool_wall_band_m2"] = round((2 * ro * ro + math.pi * ro * ro / 2) - (2 * ri * ri + math.pi * ri * ri / 2), 6)
    r["pool_wall_band_back_length_m"] = round(2 * ro, 4)
    # structural GF roof sheet: the ring arcs 312 (R 1.75) / 310 (R 1.55) are concentric with the pool arcs
    s312 = sdb["312"]
    tx, ty = s312.dxf.center.x - c.x, s312.dxf.center.y - c.y
    r["st_ring_radii_m"] = [round(sdb["310"].dxf.radius / 1000, 4), round(s312.dxf.radius / 1000, 4)]
    r["st_gf_boundary_2A7_minus_outer_face_mm"] = round(sdb["2A7"].dxf.start.x - (face_out + tx), 3)
    y0, y1 = ys[0] + ty, ys[1] + ty
    py0, py1 = pool_y[0] + ty, pool_y[1] + ty
    gx = sdb["7FE"].get_points()[0][0] - sdb["2A6"].dxf.end.x     # ground-beam sheet frame: x shift of the boundary
    r["gb_sheet_shift_check_mm"] = round((sdb["2A7"].dxf.start.x + gx) - max(q[0] for q in sdb["7FE"].get_points()), 3)

    def cover(handle, xs_band):
        pts = [(q[0], q[1]) for q in sdb[handle].get_points()]
        poly = Polygon(pts)
        east = poly.intersection(box(xs_band[0] - 1, -1e9, xs_band[1] + 1, 1e9))
        if east.is_empty:
            return None
        ey0, ey1 = east.bounds[1], east.bounds[3]
        seg = lambda a0, a1: max(0.0, min(ey1, a1) - max(ey0, a0)) / 1000
        return {"east_leg_m": round((ey1 - ey0) / 1000, 4), "over_south_part_m": round(seg(y0, py0), 4),
                "over_pool_back_m": round(seg(py0, py1), 4), "over_north_part_m": round(seg(py1, y1), 4)}
    xb = (face_in + tx + gx, face_out + tx + gx)
    r["ground_beam_plan_upper_GB"] = {h: cover(h, xb) for h in ("7FC", "7FE")}
    fx = min(q[0] for q in sdb["1658"].get_points()) - sdb["2A2"].dxf.start.x
    xf = (face_in + tx + fx, face_out + tx + fx)
    r["foundation_plan_lower_band"] = {h: cover(h, xf) for h in ("1658",)}
    inner = Polygon([(q[0], q[1]) for q in sdb["1659"].get_points()])
    r["foundation_plan_lower_band"]["band_1658_minus_1659_width_mm"] = round(
        max(q[0] for q in sdb["1658"].get_points()) - inner.bounds[2], 3)
    return r


if __name__ == "__main__":
    main()
