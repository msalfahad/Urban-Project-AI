"""T-727 DRAWING READ (research, unwired): the two T-719 findings on the V-01 light well, re-measured by HANDLE on the
architectural DXF (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, decoded by the wrapper into .work/private
only), beside the released engine's own reading of the same face (ARCH_TAKEOFF_V2.9 run on that DXF, pickled in
.work/private by tools.urban_boq_m9.arch_compute).

Writes T727_DRAWN.json: handles, lengths and areas only (no coordinate, no drawing text, no client name).

    .work/venv/bin/python -I research/agents_t727/t727_extract.py --dxf <P7757.dxf> --v29 <pickle> --write
    .work/venv/bin/python -I research/agents_t727/t727_extract.py --dxf <P7757.dxf> --v29 <pickle>     (re-read, compare)

What is read:
  1. the F1 / F4 junction on the 1F plan: F1 (radial flight of ST-02 seen through the light well, layer 2) ends on line
     B4E; F4 (straight flight, layer 5) starts on line B43. Both lines are measured (length, direction, spacing), and the
     engine footprints of F1 and F4 are intersected: the overlap must be the strip between B43 and B4E.
  2. the deduction pieces of the 1F living face inside the light-well outline: the void window, the below-seen flights
     F1 / F4 / F6 (each alone and as a union), and the remainder.
  3. the 1F roof over the light well on the 2F plan (= the 1F roof slab): every entity that crosses the well outline
     moved to the 2F frame, by type and layer, to show whether the drawing opens the roof slab over the well.
"""
from __future__ import annotations

import argparse
import ast
import json
import math
import pickle
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "T727_DRAWN.json"
ROUND = 6

WELL_1F = {"west_wall_face": "AF7", "south_wall_face": "AEC", "east_edge": "AF5", "arrival_edge": "D24",
           "void_edge_east": "B75", "void_edge_north": "B74"}          # T-719 outline handles (re-read here)
XRECT_DIAG_1F, XRECT_DIAG_GF = "B78", "4B2"
F4_FIRST_RISER, F1_LAST_LINE = "B43", "B4E"                            # 1F plan, ST-02 junction
EAST_DOME_2F, WEST_DOME_2F = "2F33", "12EB"
ROOM_1F_LIVING = "1F-R78C367"


def _q(x):
    return round(float(x), ROUND)


def _pts(v):
    return ast.literal_eval(v) if isinstance(v, str) else v


def read(dxf, v29):
    import ezdxf
    from shapely.affinity import translate
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import unary_union
    doc = ezdxf.readfile(dxf)
    E = {e.dxf.handle: e for e in doc.modelspace()}
    u = 0.001                                                          # millimetres (printed 4000 / 7020)
    m2 = u * u

    def ln(h):
        e = E[h]
        assert e.dxftype() == "LINE", (h, e.dxftype())
        return (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)

    out = {"unit_m": u}
    # ---- 1. F1 / F4 junction by handle ------------------------------------------------------------------------------
    a4, b4 = ln(F4_FIRST_RISER)
    a1, b1 = ln(F1_LAST_LINE)
    l4, l1 = math.dist(a4, b4), math.dist(a1, b1)
    vertical = abs(a4[0] - b4[0]) < 1e-6 and abs(a1[0] - b1[0]) < 1e-6
    spacing = abs(a4[0] - a1[0]) if vertical else None
    common = (min(max(a4[1], b4[1]), max(a1[1], b1[1])) - max(min(a4[1], b4[1]), min(a1[1], b1[1]))) if vertical else None
    strip = Polygon([(a4[0], max(min(a4[1], b4[1]), min(a1[1], b1[1]))), (a1[0], max(min(a4[1], b4[1]), min(a1[1], b1[1]))),
                     (a1[0], min(max(a4[1], b4[1]), max(a1[1], b1[1]))), (a4[0], min(max(a4[1], b4[1]), max(a1[1], b1[1])))])

    boq, arch, _extra = pickle.load(open(v29, "rb"))
    room = next(r for r in arch["rooms"] if r["room_id"] == ROOM_1F_LIVING)
    face = Polygon(room["polygon"])
    fl = {f["flight_id"].split(":")[-1]: f for f in (room["symbols_inside"] or {}).get("stair_flights", [])}
    fp = {k: Polygon(_pts(f["footprint"])) for k, f in fl.items()}
    quads = {k: unary_union([Polygon(q) for q in _pts(f["tread_quads"])]) for k, f in fl.items()}
    ov = fp["F1"].intersection(fp["F4"])
    ob = ov.bounds
    out["junction_F1_F4"] = {
        "handles": {"F4_first_riser": F4_FIRST_RISER, "F1_last_line": F1_LAST_LINE},
        "layers": {F4_FIRST_RISER: E[F4_FIRST_RISER].dxf.layer, F1_LAST_LINE: E[F1_LAST_LINE].dxf.layer},
        "lengths_m": {F4_FIRST_RISER: _q(l4 * u), F1_LAST_LINE: _q(l1 * u)},
        "parallel_same_direction": bool(vertical), "spacing_m": _q(spacing * u) if spacing is not None else None,
        "common_length_m": _q(common * u) if common is not None else None,
        "strip_by_handles_m2": _q(strip.area * m2),
        "engine_footprint_overlap_m2": _q(ov.area * m2),
        "engine_footprint_overlap_w_h_m": [_q((ob[2] - ob[0]) * u), _q((ob[3] - ob[1]) * u)],
        "engine_tread_quads_overlap_m2": _q(quads["F1"].intersection(quads["F4"]).area * m2),
        "overlap_equals_strip_m2": _q(ov.symmetric_difference(strip).area * m2),
        "F1_last_quad_m2": _q(fl["F1"]["tread_areas_m2"][-1]), "F1_typical_quad_m2": _q(fl["F1"]["tread_areas_m2"][3]),
        "F1_footprint_m2": _q(fp["F1"].area * m2), "F4_footprint_m2": _q(fp["F4"].area * m2),
        "F1_F4_union_m2": _q(fp["F1"].union(fp["F4"]).area * m2),
        "kinds": {k: fl[k]["kind"] for k in ("F1", "F4")},
        "below_seen": {k: bool(fl[k].get("drawn_on_plan_below")) for k in ("F1", "F4", "F6")},
    }
    # the same pair on the GF plan (the stair's own storey), moved by the X-rectangle shift 1F -> GF
    d1, d0 = ln(XRECT_DIAG_1F), ln(XRECT_DIAG_GF)
    sx = min(d0[0][0], d0[1][0]) - min(d1[0][0], d1[1][0])
    sy = min(d0[0][1], d0[1][1]) - min(d1[0][1], d1[1][1])
    gf_pair = {}
    for h, (p, q) in ((F4_FIRST_RISER, (a4, b4)), (F1_LAST_LINE, (a1, b1))):
        X, y0, y1 = p[0] + sx, min(p[1], q[1]) + sy, max(p[1], q[1]) + sy
        gf_pair[h] = sorted((e.dxf.handle, e.dxf.layer) for e in doc.modelspace() if e.dxftype() == "LINE"
                            and abs(e.dxf.start.x - X) < 1.0 and abs(e.dxf.end.x - X) < 1.0
                            and min(e.dxf.start.y, e.dxf.end.y) < y1 - 1.0 and max(e.dxf.start.y, e.dxf.end.y) > y0 + 1.0)
    out["junction_F1_F4"]["gf_plan_same_place"] = {h: [list(x) for x in v] for h, v in gf_pair.items()}

    # ---- 2. pieces of the face inside the light-well outline ----------------------------------------------------------
    xw = ln(WELL_1F["west_wall_face"])[0][0]
    ys = ln(WELL_1F["south_wall_face"])[0][1]
    xe = ln(WELL_1F["east_edge"])[0][0]
    yarr = ln(WELL_1F["arrival_edge"])[0][1]
    xn = ln(WELL_1F["void_edge_east"])[0][0]
    yn = ln(WELL_1F["void_edge_north"])[0][1]
    well = Polygon([(xw, ys), (xe, ys), (xe, yarr), (xn, yarr), (xn, yn), (xw, yn)])
    v = next(x for x in arch["run"]["double_height"] if x["void_id"] == "V01")
    W = Polygon([(x - v["offset"]["dx"], y - v["offset"]["dy"]) for x, y in v["window"]])
    in_face = face.intersection(well)
    below = [k for k in ("F1", "F4", "F6") if fl[k].get("drawn_on_plan_below")]
    each = {k: fp[k].intersection(in_face).difference(W).area * m2 for k in below}
    union = unary_union([fp[k] for k in below]).intersection(in_face).difference(W).area * m2
    # union increments in flight order (the piece's own rule: a flight less every earlier flight)
    inc, seen = {}, None
    for k in below:
        g = fp[k].intersection(in_face).difference(W)
        inc[k] = _q((g.difference(seen) if seen is not None else g).area * m2)
        seen = g if seen is None else seen.union(g)
    out["well_pieces_1F"] = {
        "well_m2": _q(well.area * m2), "face_in_well_m2": _q(in_face.area * m2),
        "void_window_m2": _q(W.intersection(in_face).area * m2),
        "below_seen_each_m2": {k: _q(x) for k, x in each.items()}, "below_seen_sum_m2": _q(sum(each.values())),
        "below_seen_union_m2": _q(union), "below_seen_union_increments_m2": inc,
        "sum_minus_union_m2": _q(sum(each.values()) - union),
        "overlap_inside_void_window_m2": _q(ov.intersection(W).area * m2),
        "overlap_inside_well_m2": _q(ov.intersection(in_face).area * m2),
        "remainder_after_void_and_union_m2": _q(in_face.area * m2 - W.intersection(in_face).area * m2 - union),
    }

    # ---- 3. the 1F roof over the light well (2F plan) -----------------------------------------------------------------
    g1 = ln(XRECT_DIAG_1F)
    g0 = ln(XRECT_DIAG_GF)
    off2 = min(g1[0][0], g1[1][0]) - min(g0[0][0], g0[1][0])          # GF -> 1F x shift; 2F = 1F + the same shift
    w2 = translate(well, off2, 0)
    cnt = Counter()
    named = []
    for e in doc.modelspace():
        t = e.dxftype()
        try:
            if t == "LINE":
                g = LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
            elif t == "LWPOLYLINE":
                p = [(q[0], q[1]) for q in e.get_points()]
                g = LineString(p) if len(p) > 1 else None
            elif t in ("CIRCLE", "ARC"):
                g = Point(e.dxf.center.x, e.dxf.center.y).buffer(e.dxf.radius, 256).exterior
            elif t in ("INSERT", "TEXT", "MTEXT"):
                g = Point(e.dxf.insert.x, e.dxf.insert.y)
            else:
                continue
        except (AttributeError, ValueError):
            continue
        if g is not None and g.intersects(w2.buffer(-20.0)):
            cnt[f"{t}/{e.dxf.layer}"] += 1
            if t in ("INSERT", "CIRCLE", "LWPOLYLINE"):
                named.append({"handle": e.dxf.handle, "type": t, "layer": e.dxf.layer,
                              "block": e.dxf.name if t == "INSERT" else None})
    east = E[EAST_DOME_2F]
    disc = Point(east.dxf.center.x - off2, east.dxf.center.y).buffer(east.dxf.radius, 256)
    west = E[WEST_DOME_2F]
    discw = Point(west.dxf.center.x - off2, west.dxf.center.y).buffer(west.dxf.radius, 256)
    out["roof_over_well_2F"] = {
        "entities_crossing_well_by_type_layer": dict(sorted(cnt.items())),
        "named_entities": sorted(named, key=lambda r: r["handle"]),
        "opening_outline_found": any(r["type"] == "LWPOLYLINE" for r in named),
        "east_dome_overlap_with_well_m2": _q(disc.intersection(well).area * m2),
        "east_dome_overlap_with_face_in_well_m2": _q(disc.intersection(in_face).area * m2),
        "west_dome_overlap_with_well_m2": _q(discw.intersection(well).area * m2),
        "roofed_face_in_well_m2": _q(in_face.difference(disc).area * m2),
        # the decor face excludes the ST-01 stair zone (own flights F2 / F3 / F5 of this face): does it reach the well?
        "own_flights_F2_F3_F5_in_well_m2": _q(unary_union([fp[k] for k in ("F2", "F3", "F5")]).intersection(well).area * m2),
        "own_flights_F2_F3_F5_gap_to_well_m": _q(unary_union([fp[k] for k in ("F2", "F3", "F5")]).distance(well) * u),
    }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--v29", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    txt = json.dumps(read(a.dxf, a.v29), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if a.write:
        OUT.write_text(txt, encoding="utf-8")
        print("written", OUT.name)
    else:
        same = OUT.exists() and OUT.read_text(encoding="utf-8") == txt
        print("re-read identical to", OUT.name, ":", same)
        if not same:
            print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
