"""T-356 extractor: private structural DXF -> values-only ALSENAN_T356_INPUT.json (handles, lengths, areas; no drawing text).

Usage (from the engine root, the DXF decoded into .work/private only):
    python3 -I research/agents_t356/t356_extract.py "<.work/private>/ST7757 dxf.dxf"

Reads, by handle (nothing typed by hand):
  * the three strap strips SB1 / SB2 / SB3 (edge LINEs on S-FOOTINGS, FOUNDATION PLAN frame: the T-174 / T-230 handles);
  * the footing outlines of PITS_T347.csv (LWPOLYLINE, INSERT 'F' unit square scaled, the three FN four-LINE squares);
  * the plot polyline S-BOUN 1658 and the inner band line S-BOUN 1659 (the foundation-plan boundary band);
  * the ground-beam strips of the GROUND BEAMS PLAN (T-230 pairing, moved to the foundation frame) - used ONLY to
    reproduce the candidate's strap-blinding basis (diagnostic), never as a deduction.
"""

import csv
import hashlib
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
STRAPS = {"SB1": ("1689", "1B1C"), "SB2": ("1B08", "1B09"), "SB3": ("1B26", "1B27")}
FN_LINE_SQUARES = ("10F8", "10F0", "1100")
P = 100.0          # p.13 blinding projection 0.10 m (mm in the DXF)


def _r(x, n=6):
    return round(x + 0.0, n)


def strap_strip(L1, L2, footings, plot, p):
    """One strap's blinding strip from its two drawn edge lines (shapely LineStrings, drawing units): the strap grown
    by p on its two SIDES only (not past its drawn ends), minus the footing outlines it joins, inside the plot.
    Returns (own area, area outside the plot, part inside the footings' blinding band, merged area)."""
    from shapely.geometry import MultiPoint, Polygon
    from shapely.ops import unary_union
    hull = MultiPoint(list(L1.coords) + list(L2.coords)).convex_hull
    dx, dy = L1.coords[1][0] - L1.coords[0][0], L1.coords[1][1] - L1.coords[0][1]
    n = math.hypot(dx, dy)
    ux, uy, nx, ny = dx / n, dy / n, -dy / n, dx / n
    ts = [c[0] * ux + c[1] * uy for c in hull.exterior.coords]
    t0, t1, big = min(ts), max(ts), 1e9
    slab = Polygon([(ux * t0 + nx * big, uy * t0 + ny * big), (ux * t1 + nx * big, uy * t1 + ny * big),
                    (ux * t1 - nx * big, uy * t1 - ny * big), (ux * t0 - nx * big, uy * t0 - ny * big)])
    UF = unary_union(footings)
    UFB = unary_union([f.buffer(p, join_style=2) for f in footings])
    strip = hull.buffer(p, join_style=2).intersection(slab).difference(UF)
    own = strip.intersection(plot)
    return own.area, strip.difference(plot).area, own.intersection(UFB).area, own.difference(UFB).area


def main(argv):
    import ezdxf
    from shapely.affinity import translate
    from shapely.geometry import LineString, MultiPoint, Polygon, box
    from shapely.ops import polygonize, unary_union

    dxf = argv[0]
    h = hashlib.sha256(open(dxf, "rb").read()).hexdigest()
    if h != DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    doc = ezdxf.readfile(dxf)
    db, msp = doc.entitydb, doc.modelspace()

    def outline(handle):
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
            ls = [LineString([tuple(x.dxf.start)[:2], tuple(x.dxf.end)[:2]])
                  for x in msp.query("LINE[layer=='S-FOOTINGS']")
                  if abs(x.dxf.start.x - cx) < 1300 and abs(x.dxf.start.y - cy) < 1300]
            sq = [p for p in polygonize(unary_union(ls)) if abs(p.area - 1e6) < 5e3]
            return sq[0] if len(sq) == 1 else None
        return None

    pits = list(csv.DictReader(open(os.path.join(ROOT, "research/agents_t347/PITS_T347.csv"), encoding="utf-8")))
    FT = {}
    for r in pits:
        tok = r["outline_handle"].split()
        if not tok:
            continue
        hd = tok[1] if tok[0] == "INSERT" else (tok[2] if tok[0] == "4" else tok[0])
        poly = outline(hd)
        if poly is None:
            raise SystemExit(f"outline {hd} not read")
        FT[f"{r['type']}:{hd}"] = poly
    UF = unary_union(list(FT.values()))
    UFB = unary_union([p.buffer(P, join_style=2) for p in FT.values()])
    plot = Polygon([p[:2] for p in db.get("1658").get_points()])
    inner = Polygon([p[:2] for p in db.get("1659").get_points()])

    # ---- straps --------------------------------------------------------------------------------------------------
    straps, hulls = {}, []
    for mark, (h1, h2) in STRAPS.items():
        e1, e2 = db.get(h1), db.get(h2)
        L1 = LineString([tuple(e1.dxf.start)[:2], tuple(e1.dxf.end)[:2]])
        L2 = LineString([tuple(e2.dxf.start)[:2], tuple(e2.dxf.end)[:2]])
        hull = MultiPoint(list(L1.coords) + list(L2.coords)).convex_hull
        hulls.append(hull)
        own, strip, band_part, merged = strap_strip(L1, L2, list(FT.values()), plot, P)
        mid = LineString([((L1.coords[0][0] + L2.coords[0][0]) / 2, (L1.coords[0][1] + L2.coords[0][1]) / 2),
                          ((L1.coords[1][0] + L2.coords[1][0]) / 2, (L1.coords[1][1] + L2.coords[1][1]) / 2)])
        from shapely.geometry import Point
        widths = [L2.distance(Point(L1.coords[0])), L2.distance(Point(L1.coords[1]))]
        straps[mark] = {
            "edge_handles": [h1, h2],
            "edge_lengths_m": [_r(L1.length / 1000, 4), _r(L2.length / 1000, 4)],
            "drawn_width_m": [_r(w / 1000, 4) for w in widths],
            "axis_clear_m": _r(mid.difference(UF).length / 1000, 4),
            "footings_joined": sorted(k for k, p in FT.items() if hull.intersection(p).area > 1.0),
            "clear_concrete_plan_m2": _r(hull.difference(UF).area / 1e6),
            "own_strip_m2": _r(own / 1e6),
            "strip_outside_plot_m2": _r(strip / 1e6),
            "in_footing_blinding_band_m2": _r(band_part / 1e6),
            "merged_strip_m2": _r(merged / 1e6),
        }

    # ---- ground-beam strips (diagnostic reproduction of the candidate's basis only) --------------------------------
    spec = importlib.util.spec_from_file_location("r141", os.path.join(ROOT, "research/agents_t141/run_t141_alsenan.py"))
    R = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(R)
    sys.path.insert(0, os.path.join(ROOT, "research/agents_t230"))
    import end_ownership as EO  # noqa: E402
    faces = [{"handle": e.dxf.handle, "layer": e.dxf.layer, "p0": tuple(e.dxf.start)[:2], "p1": tuple(e.dxf.end)[:2]}
             for e in msp.query("LINE[layer=='1']") if R.inb(*tuple(e.dxf.start)[:2], R.GBP)]
    res = R.GN.pair_straight(faces, width=300.0, tol=12.0, admitted_layers={"1"})
    shift = R.FP[0] - R.GBP[0]
    GB = []
    for b in res["bands"]:
        lo, hi = sorted((b["lo_off"], b["hi_off"]))
        GB.append(translate(Polygon(EO.band_slab(tuple(b["u"]), lo, hi, b["t0"], b["t1"])), xoff=shift))
    GBB = [g.buffer(P, join_style=2) for g in GB]
    FB_no10 = unary_union([p.buffer(P, join_style=2) for k, p in FT.items() if not k.startswith("F10")])
    SSB = [s.buffer(P, join_style=2) for s in hulls]
    diag = {}
    for nm, FBX in (("all_outlines", UFB), ("f10_outline_missing", FB_no10)):
        for gn, GX in (("no_gb", []), ("gb_strips", GB), ("gb_blinding_strips", GBB)):
            a = unary_union([FBX] + GX + SSB).area - unary_union([FBX] + GX).area
            diag[f"{nm}|{gn}"] = _r(a / 1e6)
    own_all = unary_union([s.buffer(P, join_style=2) for s in hulls]).difference(UF).intersection(plot)
    gb_overlap_plan = _r(own_all.difference(UFB).intersection(unary_union(GBB)).area / 1e6)

    # ---- boundary band (foundation plan) ---------------------------------------------------------------------------
    band = plot.difference(inner)
    cl = LineString(list(plot.buffer(-P, join_style=2).exterior.coords))
    crossings = sorted(((k, _r(cl.intersection(p).length / 1000, 4)) for k, p in FT.items()
                        if cl.intersection(p).length > 1.0), key=lambda kv: kv[0])
    out = {
        "schema": "URBAN_T356_INPUT_V1",
        "source": {"drive": "Alsenan chalet project / ST7757 dxf.dxf", "sha256": DXF_SHA, "frame": "FOUNDATION PLAN",
                   "projection_m": 0.10, "projection_source": "ST7757.pdf p.13 typical footing / ground-beam details"},
        "straps": straps,
        "straps_total": {k: _r(sum(v[k] for v in straps.values())) for k in
                         ("clear_concrete_plan_m2", "own_strip_m2", "in_footing_blinding_band_m2", "merged_strip_m2",
                          "strip_outside_plot_m2")},
        "candidate_basis_reproduction_m2": diag,
        "strap_blinding_plan_overlap_with_gb_blinding_m2": gb_overlap_plan,
        "band": {"outer_handle": "1658", "inner_handle": "1659", "width_m": 0.20,
                 "band_area_m2": _r(band.area / 1e6), "centreline_m": _r(cl.length / 1000, 4),
                 "crossings_m": crossings, "crossing_total_m": _r(sum(v for _, v in crossings), 4),
                 "crossing_outline_count": len(crossings)},
    }
    return out


if __name__ == "__main__":
    data = main(sys.argv[1:])
    path = os.path.join(HERE, "ALSENAN_T356_INPUT.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=1, sort_keys=True) + "\n")
    print(path)
