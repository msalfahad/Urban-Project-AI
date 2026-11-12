"""T-720 DRAWING READ (research, unwired): the GROSS floor area of every storey of the development villa, read by HANDLE
on the architectural DXF (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, decoded by the wrapper into
.work/private only), beside the released engine's own floor plate (ARCH_TAKEOFF_V2.9 run on the same DXF, its
ARCH_FLOOR_AREAS.json kept in .work/private).

Writes T720_DRAWN.json: handles, lengths and areas only (no coordinate, no drawing text, no client name). Every outline is
a list of vertices, each vertex = (x of a named vertical line, y of a named horizontal line), plus named arcs / bulged
polylines; the area is a shapely area of that outline (arcs flattened at 0.25 degree, error < 1e-4 m2 on these radii).

    .work/venv/bin/python -I research/agents_t720/t720_extract.py --dxf <P7757.dxf> --engine <dir of the V2.9 run> --write
    .work/venv/bin/python -I research/agents_t720/t720_extract.py --dxf <P7757.dxf> --engine <dir>          (re-read, compare)

Plans: GF / 1F / 2F are three frames side by side; the engine aligns them on the column grid (ARCH_FLOOR_AREAS
double_height offset dx 44852.655 mm, 15 column votes, dy 0); this read uses the same offset, checked here on the
north wall outer face (GF 2BC / 1F AC9 / 2F 1274, same y) and the west face of the stair core (GF 9B / 1F AF3 / 2F 1287).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "T720_DRAWN.json"
ROUND = 6
DX = 44852.655054          # engine column-grid offset between frames (GF -> 1F -> 2F), mm
STEP_DEG = 0.25

# ---- outlines (outer face of the external envelope), counter-clockwise; ("P", xh, yh) = vertex at (x of xh, y of yh)
# GF main house: south face 103, east 8B, court south wall E2, court-side face 94 / 26C, curved glazing 280 (outermost
# glazing line: no wall face crosses that opening), north face 2BC with the corner column 2F87 standing proud, west face
# 9B / 9C / 9D / 9E with the wall stub 338 / 34D / 34C (column 2FBA), the entrance step 15A, west face A1 / A0 / 9F.
GF_MAIN = [("P", "A1", "103"), ("P", "8B", "103"), ("P", "8B", "E2"), ("P", "94", "E2"), ("P", "94", "26C"),
           ("PLR", "280"), ("P", "2D6", "2B5"), ("P", "2D6", "2F87:bottom"), ("P", "2F87:east", "2F87:bottom"),
           ("P", "2F87:east", "2BC"), ("P", "9B", "2BC"), ("P", "9C", "338"), ("P", "34D", "338"), ("P", "34D", "34C"),
           ("P", "9D", "34C"), ("P", "9E", "15A"), ("P", "A1", "15A")]
# GF annex (own wall network): south 85 (corner column 2F9F), east A3 / A2, north 120 .. 123, return 12C, quarter arc 10D
# (outer face, r 1.30 m), north 10A, west 107 .. 109.
GF_ANNEX = [("P", "107", "85"), ("P", "A3", "85"), ("P", "A2", "120"), ("P", "12C", "120"), ("ARC", "10D", 0.0, 90.0),
            ("P", "107", "10A")]
# GF side passage between annex and house (Q-67): annex east face A3 / A2, house west face A1 / 9F, mouth on the south
# boundary line (layer-5 overhead lines 86 / 105 / 106), north end on the entrance step line 15A.
GF_PASSAGE = [("P", "A3", "86"), ("P", "A1", "86"), ("P", "9F", "15A"), ("P", "A2", "15A")]
# 1F: south face AE3 / ADF, east face B5D .. B62 (straight openings bridged on the face), the concave curved wall
# BD0 / BCD (outer face r 1.935 m, opening bridged on the same circle), north AC9, west AF3 / AF4, step B6C, west B3A / B3B.
F1 = [("P", "B3A", "AE3"), ("P", "B5D", "AE3"), ("P", "B61", "BD0:end"), ("ARCJ", "BD0", "BCD"),
      ("P", "B62", "AC9"), ("P", "AF3", "AC9"), ("P", "AF4", "B6C"), ("P", "B3B", "B6C")]
# 2F (roof structures: stair, lift, maid room): south 1280 / 1281, east 1291, north 1274 .. 1277, west 1287 / 1288.
F2 = [("P", "1288", "1281"), ("P", "1291", "1281"), ("P", "1291", "1274"), ("P", "1287", "1274")]
# GF plot: outer face of the boundary walls (layer-5 boundary lines 98 north, 8E east; the annex west face 107 and the
# south face 85 are on the boundary line); reference for the outside ground only, never a floor area
PLOT = [("P", "107", "85"), ("P", "8E", "85"), ("P", "8E", "98"), ("P", "107", "98")]
# frame of each outline: the x of a GF handle is used as is, of a 1F handle + DX, of a 2F handle + 2 DX (GF grid)
FRAMES = {"GF_MAIN": 0, "GF_ANNEX": 0, "GF_PASSAGE": 0, "PLOT": 0, "1F": 1, "2F": 2}
OUTLINES = {"GF_MAIN": GF_MAIN, "GF_ANNEX": GF_ANNEX, "GF_PASSAGE": GF_PASSAGE, "PLOT": PLOT, "1F": F1, "2F": F2}
# alignment checks: (GF handle, 1F handle, 2F handle or None, axis) must be the same line after the offset
ALIGN = [("2BC", "AC9", "1274", "y"), ("9B", "AF3", "1287", "x"), ("2D6", "B62", None, "x_minus_500")]
# printed dimensions (second source on the same sheets): (dimension handle, (handle, frame), (handle, frame)) -> the own
# distance between the two named face lines must equal the printed measurement
DIMS = [("A67", ("107", 0), ("9B", 0)), ("598", ("10A", 0), ("98", 0)), ("5F9", ("298", 0), ("B6", 0)),
        ("D87", ("107", 0), ("B3A", 1)), ("143C", ("1291", 2), ("B5D", 1))]
# the north-arrow symbol whose lines sit on the wall layer: never floor area (engine plate second component)
NORTH_ARROW = {"GF": "1612", "1F": "19A2", "2F": "19A3"}


def _q(x):
    return round(float(x), ROUND) + 0.0          # never -0.0


def _ents(dxf):
    import ezdxf
    doc = ezdxf.readfile(dxf)
    return doc, {e.dxf.handle: e for e in doc.modelspace()}


def _line_xy(E, h, frame):
    """('x', value) for a vertical line, ('y', value) for a horizontal one; column edges via 'HANDLE:side'."""
    off = frame * DX
    if ":" in h:
        hh, side = h.split(":")
        if side == "end":                                     # end point of an ARC entity
            e = E[hh]
            c, r, a = e.dxf.center, e.dxf.radius, math.radians(e.dxf.end_angle)
            return "y", c.y + r * math.sin(a)
        pts = [(p[0], p[1]) for p in E[hh].get_points()]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if side in ("east", "west"):
            return "x", (max(xs) if side == "east" else min(xs)) + off
        if side in ("north", "south", "bottom", "top"):
            return "y", max(ys) if side in ("north", "top") else min(ys)
        raise ValueError(h)
    e = E[h]
    assert e.dxftype() == "LINE", (h, e.dxftype())
    a, b = e.dxf.start, e.dxf.end
    if abs(a.x - b.x) < 0.5:
        return "x", a.x + off
    if abs(a.y - b.y) < 0.5:
        return "y", a.y
    raise ValueError(f"{h} is neither vertical nor horizontal")


def _arc_pts(E, h, a0, a1, frame):
    e = E[h]
    c, r = e.dxf.center, e.dxf.radius
    n = max(2, int(abs(a1 - a0) / STEP_DEG) + 1)
    return [(c.x + frame * DX + r * math.cos(math.radians(a0 + (a1 - a0) * k / (n - 1))),
             c.y + r * math.sin(math.radians(a0 + (a1 - a0) * k / (n - 1)))) for k in range(n)], r


def _bulge_pts(E, h, frame, reverse):
    from ezdxf.math import bulge_to_arc
    e = E[h]
    P = list(e.get_points("xyb"))
    out = []
    for i in range(len(P) - 1):
        (x0, y0, b), (x1, y1, _) = P[i], P[i + 1]
        out.append((x0, y0))
        if abs(b) > 1e-9:
            c, sa, ea, r = bulge_to_arc((x0, y0), (x1, y1), b)
            sa, ea = math.degrees(sa), math.degrees(ea)
            if b > 0 and ea < sa:
                ea += 360.0
            if b < 0 and sa < ea:
                sa += 360.0
            # bulge_to_arc returns the CCW arc; walk it from (x0, y0)
            st = (c.x + r * math.cos(math.radians(sa)), c.y + r * math.sin(math.radians(sa)))
            if math.hypot(st[0] - x0, st[1] - y0) > 1.0:
                sa, ea = ea, sa
            n = max(2, int(abs(ea - sa) / STEP_DEG) + 1)
            out += [(c.x + r * math.cos(math.radians(sa + (ea - sa) * k / (n - 1))),
                     c.y + r * math.sin(math.radians(sa + (ea - sa) * k / (n - 1)))) for k in range(1, n - 1)]
    out.append((P[-1][0], P[-1][1]))
    out = [(x + frame * DX, y) for x, y in out]
    return list(reversed(out)) if reverse else out


def outline(E, spec, frame):
    pts, handles, arcs = [], [], []
    for it in spec:
        if it[0] == "P":
            ax, vx = _line_xy(E, it[1], frame)
            ay, vy = _line_xy(E, it[2], frame)
            assert ax == "x" and ay == "y", it
            pts.append((vx, vy))
            handles += [it[1].split(":")[0], it[2].split(":")[0]]
        elif it[0] == "ARC":
            p, r = _arc_pts(E, it[1], it[2], it[3], frame)
            pts += p
            handles.append(it[1])
            arcs.append({"handle": it[1], "r_m": _q(r / 1000.0), "sweep_deg": _q(abs(it[3] - it[2]))})
        elif it[0] == "ARCJ":                                 # from the end of arc 1 to the start of arc 2, one circle
            e1, e2 = E[it[1]], E[it[2]]
            assert abs(e1.dxf.radius - e2.dxf.radius) < 0.5 and (e1.dxf.center - e2.dxf.center).magnitude < 0.5, it
            a0, a1 = e1.dxf.end_angle, e2.dxf.start_angle
            p, r = _arc_pts(E, it[1], a0, a1, frame)
            pts += p
            handles += [it[1], it[2]]
            arcs.append({"handle": it[1] + "+" + it[2], "r_m": _q(r / 1000.0), "sweep_deg": _q(abs(a1 - a0))})
        elif it[0] in ("PL", "PLR"):
            pts += _bulge_pts(E, it[1], frame, it[0] == "PLR")
            handles.append(it[1])
            arcs.append({"handle": it[1], "bulged_polyline": True,
                         "bulges": [_q(b) for *_, b in E[it[1]].get_points("xyb") if abs(b) > 1e-9]})
    from shapely.geometry import Polygon
    poly = Polygon(pts)
    return poly, sorted(set(handles)), arcs


def _closing_gaps(poly):
    """largest jump between consecutive vertices that are not on one drawn line is not tested here: the outline
    is closed by construction (each vertex shares a handle with the next); validity is shapely's."""
    return poly.is_valid


def read(dxf, engine_dir):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    doc, E = _ents(dxf)
    u = 0.001
    out = {"unit_m": u, "frame_offset_dx_mm": DX, "outlines": {}, "align": [], "overlay": {}, "engine": {}}
    polys = {}
    for k, spec in OUTLINES.items():
        p, hs, arcs = outline(E, spec, FRAMES[k])
        assert p.is_valid, k
        polys[k] = p
        b = p.bounds
        out["outlines"][k] = {"m2": _q(p.area * u * u), "perimeter_m": _q(p.length * u), "handles": hs, "arcs": arcs,
                              "bbox_m": [_q((b[2] - b[0]) * u), _q((b[3] - b[1]) * u)], "vertices": len(p.exterior.coords) - 1}
    for g, f1, f2, ax in ALIGN:
        a0, v0 = _line_xy(E, g, 0)
        a1, v1 = _line_xy(E, f1, 1)
        row = {"gf": g, "f1": f1, "axis": ax, "gf_minus_1f_mm": _q(v0 - v1 + (500 if ax == "x_minus_500" else 0))}
        if f2:
            a2, v2 = _line_xy(E, f2, 2)
            row.update({"f2": f2, "gf_minus_2f_mm": _q(v0 - v2)})
        out["align"].append(row)
    # overlay on the GF grid: what the 1F floor covers outside the GF envelope; what the 2F covers on the 1F roof
    gf = unary_union([polys["GF_MAIN"], polys["GF_ANNEX"]])
    cov = polys["1F"].difference(gf)
    pieces = sorted(getattr(cov, "geoms", [cov]), key=lambda g: -g.area)
    out["overlay"]["1F_over_outside_GF_m2"] = _q(cov.area * u * u)
    out["overlay"]["1F_over_outside_GF_pieces"] = [
        {"m2": _q(g.area * u * u), "bbox_m": [_q((g.bounds[2] - g.bounds[0]) * u), _q((g.bounds[3] - g.bounds[1]) * u)],
         "in_passage_m2": _q(g.intersection(polys["GF_PASSAGE"]).area * u * u)} for g in pieces if g.area * u * u > 1e-4]
    out["overlay"]["passage_under_1F_m2"] = _q(polys["GF_PASSAGE"].intersection(polys["1F"]).area * u * u)
    out["overlay"]["1F_outside_GF_and_passage_m2"] = _q(cov.difference(polys["GF_PASSAGE"]).area * u * u)
    outside = polys["PLOT"].difference(gf)
    out["overlay"]["plot_outside_GF_envelope_m2"] = _q(outside.area * u * u)
    out["overlay"]["plot_outside_GF_not_under_1F_m2"] = _q(outside.difference(polys["1F"]).area * u * u)
    out["overlay"]["1F_outside_plot_m2"] = _q(polys["1F"].difference(polys["PLOT"]).area * u * u)
    out["overlay"]["GF_not_under_1F_m2"] = _q(gf.difference(polys["1F"]).area * u * u)
    out["overlay"]["1F_roof_not_under_2F_m2"] = _q(polys["1F"].difference(polys["2F"]).area * u * u)
    out["overlay"]["2F_outside_1F_m2"] = _q(polys["2F"].difference(polys["1F"]).area * u * u)
    out["printed_dims"] = []
    for dh, (h1, f1), (h2, f2) in DIMS:
        a1, v1 = _line_xy(E, h1, f1)
        a2, v2 = _line_xy(E, h2, f2)
        assert a1 == a2, (dh, h1, h2)
        own = abs(v1 - v2) * u
        printed = E[dh].get_measurement() * u
        out["printed_dims"].append({"dim": dh, "faces": [h1, h2], "printed_m": _q(printed), "own_m": _q(own),
                                    "diff_mm": _q((own - printed) * 1000.0)})
    # 1F east: the straight opening between column 2FD8 and wall B61 is bridged on the face line (R-T720-1); the engine
    # plate follows the window frame line C37 there, 80 mm inside the face: the strip is a named cause of the difference
    _, xf = _line_xy(E, "B61", 1)
    _, xw = _line_xy(E, "C37", 1)
    y_top_col = max(p[1] for p in E["2FD8"].get_points())
    y_wall = min(E["B61"].dxf.start.y, E["B61"].dxf.end.y)
    out["reveal_1F_east"] = {"handles": ["B61", "C37", "2FD8"], "depth_m": _q((xf - xw) * u),
                             "length_m": _q((y_wall - y_top_col) * u), "m2": _q((xf - xw) * (y_wall - y_top_col) * u * u)}
    # the north-arrow symbol (engine plate component 2 on every plan): its own area, read from its block outline
    na = {}
    for fl, h in NORTH_ARROW.items():
        e = E[h]
        pts = []
        for v in e.virtual_entities():
            if v.dxftype() == "LINE":
                pts += [(v.dxf.start.x, v.dxf.start.y), (v.dxf.end.x, v.dxf.end.y)]
        from shapely.geometry import MultiPoint
        hull = MultiPoint(pts).convex_hull if pts else None
        na[fl] = {"insert": h, "block": e.dxf.name, "layer": e.dxf.layer,
                  "line_layers": sorted({v.dxf.layer for v in e.virtual_entities() if v.dxftype() == "LINE"}),
                  "hull_m2": _q(hull.area * u * u) if hull is not None else None}
    out["north_arrow"] = na
    if engine_dir:
        fa = json.loads((Path(engine_dir) / "ARCH_FLOOR_AREAS.json").read_text())
        for f in fa["floors"]:
            out["engine"][f["floor"]] = {"gross_floor_plate_m2": f["gross_floor_plate_m2"],
                                         "plate_components_m2": f["plate_components_m2"],
                                         "plate_top_level_m2": f["plate_top_level_m2"],
                                         "categories_m2": f["categories_m2"],
                                         "internal_physical_floor_m2": f["internal_physical_floor_m2"]}
        rooms = json.loads((Path(engine_dir) / "ARCH_ROOMS.json").read_text())["rooms"]
        out["engine_rooms_outside_own_gross"] = []
        for r in rooms:
            fr = {"GF": 0, "1F": 1, "2F": 2}[r["floor"]]
            pr = Polygon([(x + fr * DX, y) for x, y in r["polygon"]])
            ref = gf if fr == 0 else polys["1F" if fr == 1 else "2F"]
            outside = pr.difference(ref).area * u * u
            if outside > 1e-4:
                out["engine_rooms_outside_own_gross"].append({"room_id": r["room_id"], "codes": r["codes"],
                                                              "m2": _q(r["area_m2"]), "outside_m2": _q(outside)})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--engine")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    d = read(a.dxf, a.engine)
    txt = json.dumps(d, indent=1, sort_keys=True) + "\n"
    if a.write:
        OUT.write_text(txt)
        print(f"wrote {OUT.name}")
        return 0
    same = OUT.exists() and OUT.read_text() == txt
    print("T720_DRAWN.json", "IDENTICAL" if same else "DIFFERS")
    if not same:
        print(txt[:3000])
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
