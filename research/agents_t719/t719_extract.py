"""T-719 DRAWING READ (research, unwired): the drawn VOIDS / DOUBLE HEIGHT / SHAFTS of the development villa, read by
HANDLE on the architectural DXF (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, decoded by the wrapper into
.work/private only), beside the released engine's own reading of the same drawing (ARCH_TAKEOFF_V2.9 run on that DXF,
outputs kept in .work/private: ARCH_ROOMS.json / ARCH_PLAN.json), so that the builder can test, void by void, which
floor / ceiling line deducts which m2.

Writes T719_DRAWN.json: handles, lengths and areas only (no coordinate, no drawing text, no client name). Every length is
a difference of two drawn coordinates on the same plan; every area is a shapely area of polygons built from handles.

    .work/venv/bin/python -I research/agents_t719/t719_extract.py --dxf <P7757.dxf> --engine <dir of the V2.9 run> --write
    .work/venv/bin/python -I research/agents_t719/t719_extract.py --dxf <P7757.dxf> --engine <dir>          (re-read, compare)

Plans: GF / 1F / 2F are three frames side by side; the engine aligns them on the column grid (ARCH_PLAN run.double_height
offset, 15 column votes) and this read uses the same offset, checked here on the ST-02 tread lines (identical on GF and 1F).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "T719_DRAWN.json"
ROUND = 6

# ---- handles (1F plan unless stated) --------------------------------------------------------------------------------
# V-01 ST-02 light well (opening in the 1F floor slab over the GF reception): wall faces west / south, slab-edge lines
WELL_1F = {"west_wall_face": "AF7", "south_wall_face": "AEC", "east_edge": "AF5", "arrival_edge": "D24",
           "void_edge_east": "B75", "void_edge_north": "B74", "void_edge_south_piece": "B76"}
WELL_XRECT_1F = {"outline": "B77", "diag_1": "B78", "diag_2": "B79", "void_word_insert": "B7A"}
WELL_XRECT_GF = {"outline": "4B0", "diag_1": "4B2", "diag_2": "4B3"}          # the same void drawn 'above' on GF
WELL_TREAD_CHECK = [("BA4", "241"), ("BBA", "257"), ("B4E", "234"), ("B5A", "144")]  # 1F vs GF lines: same place
ST02_CORNER_FIRST_TREAD_1F = "B59"     # first tread line of the east flight: the corner landing ends here
# V-02 the lens-shaped opening east of the 1F curved wall (layer 5 on 1F, layer 2 'above' on GF)
OVAL = {"1F_outline": ["BCF", "2F1C", "C7A", "2F1B"], "1F_glazing_side_arc": "BCE", "GF_above": ["20A", "299"],
        "1F_same_centre": ["C7A", "BCE"]}
# V-03 lift shaft: the engine's stacked shaft (ARCH_PLAN run.stacked_shafts), 1.80 x 1.80 on GF / 1F / 2F
# V-05 / V-06 dome openings (2F plan = the 1F roof slab): layer-5 circles; V-07 the third dome drawn 'above' (layer 2)
DOMES_2F = {"west": "12EB", "east": "2F33", "third_above": "1300"}
# V-04 ST-01 dog-leg stair: the engine's stair spaces / flights (read only)
ST01_ROOMS = {"GF": "GF-R31F8AE", "1F": "1F-R78C367", "2F": "2F-R4D1B62"}
ROOM_1F_LIVING = "1F-R78C367"
ROOM_GF_OPEN = "GF-RC99C2A"


def _q(x):
    return round(float(x), ROUND)


def _ents(dxf):
    import ezdxf
    doc = ezdxf.readfile(dxf)
    return {e.dxf.handle: e for e in doc.modelspace()}


def _line(E, h):
    e = E[h]
    assert e.dxftype() == "LINE", (h, e.dxftype())
    a, b = e.dxf.start, e.dxf.end
    return (a.x, a.y), (b.x, b.y)


def _poly(E, h):
    e = E[h]
    assert e.dxftype() == "LWPOLYLINE", (h, e.dxftype())
    return [(p[0], p[1]) for p in e.get_points()]


def _unit(E):
    return 0.001       # the drawing is in millimetres (engine run: unit_m 0.001; printed 4000 / 7020 dimensions)


def _pieces(geom, u, xr, below):
    """connected pieces of a carried area, largest first: m2, bounding sizes (m), and what each piece touches."""
    gs = list(getattr(geom, "geoms", [geom]))
    rows = []
    for g in gs:
        a = g.area * u * u
        if a < 1e-4:
            continue
        b = g.bounds
        rows.append({"m2": _q(a), "w_m": _q((b[2] - b[0]) * u), "h_m": _q((b[3] - b[1]) * u),
                     "touches_xrect": bool(g.buffer(2.0).intersects(xr)),
                     "touches_below_seen_flight": bool(g.buffer(2.0).intersects(below))})
    return sorted(rows, key=lambda r: -r["m2"])


def read(dxf, engine_dir):
    from shapely.affinity import translate
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    E = _ents(dxf)
    u = _unit(E)
    m2 = u * u
    eng = Path(engine_dir)
    rooms = {r["room_id"]: r for r in json.loads((eng / "ARCH_ROOMS.json").read_text(encoding="utf-8"))["rooms"]}
    plan = json.loads((eng / "ARCH_PLAN.json").read_text(encoding="utf-8"))
    run = plan["run"]
    dh = run["double_height"]
    assert len(dh) == 1 and dh[0]["void_id"] == "V01", dh
    off = dh[0]["offset"]                  # 1F -> GF translation the engine found on the column grid
    out = {"unit_m": u, "frame_alignment": {"source": "engine column grid", "votes": off["votes"]}}

    # ---- V-01 light well --------------------------------------------------------------------------------------------
    x_w = _line(E, WELL_1F["west_wall_face"])[0][0]
    y_s = _line(E, WELL_1F["south_wall_face"])[0][1]
    (ea, eb) = _line(E, WELL_1F["east_edge"])
    x_e = ea[0]
    y_arr = _line(E, WELL_1F["arrival_edge"])[0][1]
    x_n = _line(E, WELL_1F["void_edge_east"])[0][0]
    y_n = _line(E, WELL_1F["void_edge_north"])[0][1]
    well = Polygon([(x_w, y_s), (x_e, y_s), (x_e, y_arr), (x_n, y_arr), (x_n, y_n), (x_w, y_n)])
    # the X-marked rectangle: the box of its first diagonal (the engine's X_RECT reading); the drawn outline B77 is an
    # OPEN 6-point polyline (its south-west piece is the radial flight's edge), recorded beside it
    (d1a, d1b) = _line(E, WELL_XRECT_1F["diag_1"])
    xr = Polygon([(min(d1a[0], d1b[0]), min(d1a[1], d1b[1])), (max(d1a[0], d1b[0]), min(d1a[1], d1b[1])),
                  (max(d1a[0], d1b[0]), max(d1a[1], d1b[1])), (min(d1a[0], d1b[0]), max(d1a[1], d1b[1]))])
    xr_open = _poly(E, WELL_XRECT_1F["outline"])
    word = E[WELL_XRECT_1F["void_word_insert"]].dxf.insert
    y_t1 = _line(E, ST02_CORNER_FIRST_TREAD_1F)[0][1]
    corner = Polygon([(x_n, y_s), (x_e, y_s), (x_e, y_t1), (x_n, y_t1)])
    # GF: the same rectangle drawn 'above' and the same treads, after the engine's offset
    (g1a, g1b) = _line(E, WELL_XRECT_GF["diag_1"])
    xr_gf = Polygon([(min(g1a[0], g1b[0]), min(g1a[1], g1b[1])), (max(g1a[0], g1b[0]), min(g1a[1], g1b[1])),
                     (max(g1a[0], g1b[0]), max(g1a[1], g1b[1])), (min(g1a[0], g1b[0]), max(g1a[1], g1b[1]))])
    shift = (xr_gf.bounds[0] - xr.bounds[0], xr_gf.bounds[1] - xr.bounds[1])
    tread_dev = []
    for h1, h0 in WELL_TREAD_CHECK:
        a1, b1 = _line(E, h1)
        a0, b0 = _line(E, h0)
        d = max(math.dist((a1[0] + shift[0], a1[1] + shift[1]), a0), math.dist((b1[0] + shift[0], b1[1] + shift[1]), b0))
        tread_dev.append([h1, h0, _q(d * u)])
    living = rooms[ROOM_1F_LIVING]
    face = Polygon(living["polygon"])
    below = [f for f in (living["symbols_inside"] or {}).get("stair_flights", []) if f.get("drawn_on_plan_below")]
    below_u = unary_union([Polygon(q) for f in below for q in f["tread_quads"]])
    parts = {"VOID": living["void_m2"]}
    in_face = face.intersection(well)
    covered = in_face.intersection(unary_union([xr, below_u]))
    resid = in_face.difference(unary_union([xr, below_u]))
    resid_corner = resid.intersection(corner).area * m2
    # the engine's own split of the same face (arch_floor.split_face, ARCH_FLOOR_AREAS parts) and its footprint union
    fa = json.loads((eng / "ARCH_FLOOR_AREAS.json").read_text(encoding="utf-8"))
    eparts = next(r["parts"] for fl in fa["floors"] for r in fl.get("rows", []) if r.get("room_id") == ROOM_1F_LIVING)
    below_fp = unary_union([Polygon(f["footprint"]) for f in below])
    covered_fp = in_face.intersection(unary_union([xr, below_fp]))
    out["V-01"] = {
        "handles": {**WELL_1F, **WELL_XRECT_1F, "corner_first_tread": ST02_CORNER_FIRST_TREAD_1F,
                    "gf_rectangle_above": WELL_XRECT_GF["outline"]},
        "dims_m": {"west_to_east_edge": _q((x_e - x_w) * u), "south_face_to_north_edge": _q((y_n - y_s) * u),
                   "west_to_void_edge_east": _q((x_n - x_w) * u), "south_face_to_arrival_edge": _q((y_arr - y_s) * u),
                   "xrect_w": _q((xr.bounds[2] - xr.bounds[0]) * u), "xrect_h": _q((xr.bounds[3] - xr.bounds[1]) * u),
                   "corner_landing_w": _q((x_e - x_n) * u), "corner_landing_d": _q((y_t1 - y_s) * u)},
        "void_word_inside_xrect": bool(xr.contains(Point(word.x, word.y))),
        "well_m2": _q(well.area * m2), "xrect_m2": _q(xr.area * m2), "corner_landing_m2": _q(corner.area * m2),
        "xrect_inside_well": bool(well.buffer(1.0).contains(xr)),
        "xrect_outline_open_polyline_points": len(xr_open),
        "xrect_outline_open_polyline_closed_m2": _q(Polygon(xr_open).area * m2),
        "gf_rectangle_above_m2": _q(xr_gf.area * m2), "gf_vs_1f_tread_deviation_m": tread_dev,
        "engine": {"room": ROOM_1F_LIVING, "face_m2": _q(face.area * m2), "face_in_well_m2": _q(in_face.area * m2),
                   "well_outside_face_m2": _q(well.difference(face).area * m2),
                   "void_part_m2": _q(parts["VOID"]),
                   "below_seen_flights": [f["flight_id"].split(":")[-1] for f in below],
                   "below_seen_treads_m2": _q(sum(sum(f["tread_areas_m2"]) for f in below)),
                   "below_seen_union_m2": _q(below_u.area * m2),
                   "deducted_in_well_m2": _q(covered.area * m2),
                   "split_face_parts_m2": {k: _q(v) for k, v in sorted(eparts.items())},
                   "deducted_in_well_by_footprint_m2": _q(covered_fp.area * m2),
                   "carried_in_well_by_footprint_m2": _q((in_face.area - covered_fp.area) * m2),
                   "xrect_overlap_below_seen_m2": _q(xr.intersection(below_u).area * m2),
                   "named_deductions_sum_m2": _q(parts["VOID"] + below_u.area * m2),
                   "carried_in_well_m2": _q(resid.area * m2),
                   "carried_corner_landing_m2": _q(resid_corner),
                   "carried_other_m2": _q(resid.area * m2 - resid_corner),
                   "carried_pieces": _pieces(resid.difference(corner), u, xr, below_u),
                   "gf_double_height_m2": dh[0]["area_m2"], "gf_room": dh[0]["in_spaces"][0]["face_id"]},
    }
    gf = rooms[ROOM_GF_OPEN]
    out["V-01"]["engine"]["gf_room_double_height_m2"] = gf["double_height_m2"]
    out["V-01"]["engine"]["ceiling_over_void_m2"] = living["void_m2"]
    well_gf = translate(well, shift[0], shift[1])
    gface = Polygon(gf["polygon"])
    out["V-01"]["engine"]["gf_face_in_well_m2"] = _q(gface.intersection(well_gf).area * m2)
    out["V-01"]["engine"]["gf_flights_in_well_m2"] = _q(gface.intersection(well_gf).intersection(unary_union(
        [Polygon(f["footprint"]) for f in (gf["symbols_inside"] or {}).get("stair_flights", [])])).area * m2)
    out["V-01"]["engine"]["below_seen_footprint_overlaps_m2"] = [
        [a["flight_id"].split(":")[-1], b["flight_id"].split(":")[-1],
         _q(Polygon(a["footprint"]).intersection(Polygon(b["footprint"])).area * m2)]
        for i, a in enumerate(below) for b in below[i + 1:]]

    # ---- V-02 the oval opening east of the 1F curved glazing (exterior) ----------------------------------------------
    # 1F layer-5 outline of four arcs, in order round the opening (counter-clockwise): BCF (r 1.735 about B, the west
    # side, 0.20 inside the arc BCE r 1.935 that follows the curved glazing), 2F1C (r 0.69, south), C7A (r 1.55 about A,
    # east), 2F1B (r 0.51, north). GF draws the same position 'above' (layer 2: 20A r 1.55 about A, 299 r 1.935 about B).
    def arc_pts(h, n=180):
        e = E[h]
        c, r = e.dxf.center, e.dxf.radius
        s0, s1 = e.dxf.start_angle, e.dxf.end_angle
        sweep = (s1 - s0) % 360.0
        return [(c.x + r * math.cos(math.radians(s0 + sweep * k / n)), c.y + r * math.sin(math.radians(s0 + sweep * k / n)))
                for k in range(n + 1)]
    ring = []
    gaps = []
    for h in OVAL["1F_outline"]:
        pts = arc_pts(h)
        if ring:
            gaps.append(_q(math.dist(ring[-1], pts[0]) * u))
        ring += pts
    gaps.append(_q(math.dist(ring[-1], ring[0]) * u))
    raw = Polygon(ring)
    oval = raw if raw.is_valid else raw.buffer(0)      # repeated joint points only; the area check below shows it
    cB = E[OVAL["1F_glazing_side_arc"]].dxf.center
    faces_1f = {rid: _q(Polygon(r["polygon"]).intersection(oval).area * m2) for rid, r in rooms.items()
                if r["floor"] == "1F" and Polygon(r["polygon"]).intersects(oval)}
    gfo = translate(oval, shift[0], shift[1])
    faces_gf = {rid: _q(Polygon(r["polygon"]).intersection(gfo).area * m2) for rid, r in rooms.items()
                if r["floor"] == "GF" and Polygon(r["polygon"]).intersects(gfo)}
    above = [E[h] for h in OVAL["GF_above"]]
    out["V-02"] = {"handles": OVAL, "outline_valid_as_drawn": bool(raw.is_valid),
                   "outline_m2": _q(oval.area * m2), "outline_m2_shoelace": _q(abs(raw.area) * m2),
                   "joint_gaps_m": gaps,
                   "span_m": [_q((oval.bounds[2] - oval.bounds[0]) * u), _q((oval.bounds[3] - oval.bounds[1]) * u)],
                   "radii_m": {h: _q(E[h].dxf.radius * u) for h in OVAL["1F_outline"] + [OVAL["1F_glazing_side_arc"]]},
                   "west_side_offset_from_glazing_arc_m": _q((E[OVAL["1F_glazing_side_arc"]].dxf.radius
                                                             - E[OVAL["1F_outline"][0]].dxf.radius) * u),
                   "gf_above_same_centres": all(math.dist((x.dxf.center.x - shift[0], x.dxf.center.y - shift[1]),
                                                          (E[y].dxf.center.x, E[y].dxf.center.y)) * u < 0.001
                                                for x, y in zip(above, OVAL["1F_same_centre"])),
                   "engine_faces_1f_m2": faces_1f, "engine_faces_gf_m2": faces_gf}

    # ---- V-03 lift shaft --------------------------------------------------------------------------------------------
    out["V-03"] = {"stacked_shafts": [{"floors": s["floors"], "m2_each": s["area_m2"]} for s in run["stacked_shafts"]],
                   "shaft_rooms": {r["floor"]: {"room": rid, "m2": _q(r["area_m2"]), "kind": r["kind"]}
                                   for rid, r in rooms.items() if r["kind"] == "SHAFT"}}

    # ---- V-04 ST-01 dog-leg stair -----------------------------------------------------------------------------------
    st = {}
    for fl, rid in ST01_ROOMS.items():
        r = rooms[rid]
        fls = (r["symbols_inside"] or {}).get("stair_flights", [])
        st[fl] = {"room": rid, "kind": r["kind"], "face_m2": _q(r["area_m2"]),
                  "flights": [{"id": f["flight_id"].split(":")[-1], "kind": f["kind"],
                               "treads_m2": _q(sum(f["tread_areas_m2"])), "below_seen": bool(f.get("drawn_on_plan_below")),
                               "stacked_over_below": bool(f.get("stacked_over"))} for f in fls]}
    out["V-04"] = st

    # ---- V-05 / V-06 / V-07 domes -----------------------------------------------------------------------------------
    dm = {}
    for k, h in DOMES_2F.items():
        e = E[h]
        dm[k] = {"handle": h, "layer": e.dxf.layer, "r_m": _q(e.dxf.radius * u),
                 "disc_m2": _q(math.pi * (e.dxf.radius * u) ** 2)}
    # the east dome over the light well? overlap of the disc (moved to the 1F frame) with the well
    e = E[DOMES_2F["east"]]
    c = e.dxf.center
    off2 = (xr.bounds[0] - xr_gf.bounds[0])           # GF -> 1F x shift (1F frame = GF frame + off2); 2F = 1F + off2
    disc = Point(c.x - off2, c.y).buffer(e.dxf.radius, 256)
    dm["east"]["overlap_with_light_well_m2"] = _q(disc.intersection(well).area * m2)
    dm["east"]["overlap_with_living_face_m2"] = _q(disc.intersection(face).area * m2)
    w = E[DOMES_2F["west"]]
    discw = Point(w.dxf.center.x - off2, w.dxf.center.y).buffer(w.dxf.radius, 256)
    dm["west"]["overlap_with_light_well_m2"] = _q(discw.intersection(well).area * m2)
    t3 = E[DOMES_2F["third_above"]]
    disc3 = Point(t3.dxf.center.x, t3.dxf.center.y).buffer(t3.dxf.radius, 256)
    dm["third_above"]["overlap_with_2f_faces_m2"] = {rid: _q(Polygon(r["polygon"]).intersection(disc3).area * m2)
                                                    for rid, r in rooms.items() if r["floor"] == "2F"
                                                    and Polygon(r["polygon"]).intersects(disc3)}
    # the two layer-5 dome circles on the 2F plan cut no 2F face (they lie on the 1F roof, outside the 2F rooms)
    dm["west"]["overlap_with_2f_faces_m2"] = _q(sum(Polygon(r["polygon"]).intersection(
        Point(w.dxf.center.x, w.dxf.center.y).buffer(w.dxf.radius, 256)).area for r in rooms.values()
        if r["floor"] == "2F") * m2)
    dm["east"]["overlap_with_2f_faces_m2"] = _q(sum(Polygon(r["polygon"]).intersection(
        Point(c.x, c.y).buffer(e.dxf.radius, 256)).area for r in rooms.values() if r["floor"] == "2F") * m2)
    out["DOMES"] = dm
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--engine", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    doc = read(a.dxf, a.engine)
    txt = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
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
