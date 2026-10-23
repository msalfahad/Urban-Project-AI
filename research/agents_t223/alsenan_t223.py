"""T-223 development-villa ledger: the curved 1F room (pairing by area AND perimeter), the typing of the unlabelled
faces (1F dressing, GF side passage), the three sills and the GF strips found on the way; the floor-area like-for-like
residual restated. Reads ONLY committed files: ALSENAN_T223_INPUT.json (extract_t223.py, by DXF handle, local frames,
no coordinates), the T-218 merged ledger (summary.json, FLOOR_KEY_T218.csv) and the released run A figures quoted in
RELEASED_A_T223.json (own re-run of tools/release_baseline.py, BOQ_LINES.csv b96185d4).

Usage: python3 -I research/agents_t223/alsenan_t223.py [--check]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t218"))
import floor_typing as FT          # noqa: E402
import wet_class_strips as WS      # noqa: E402

INPUT = HERE / "ALSENAN_T223_INPUT.json"
RELEASED = HERE / "RELEASED_A_T223.json"
OUT_PAIR = HERE / "CURVED_ROOM_PAIRING_T223.csv"
OUT_TYPE = HERE / "FACE_TYPING_T223.csv"
OUT_STRIP = HERE / "STRIPS_T223.csv"
OUT_KEY = HERE / "FLOOR_KEY_T223.csv"
OUT_SUM = HERE / "summary.json"

FREELANCER_ROW = {"row": "FIN tiles sheet row 22 'bed room 1'", "m2": 17.29, "lm": 22.89}   # T-218 BEDROOMS_T218.csv


def _r(x, n=4):
    return None if x is None else round(x + 0.0, n)


def _rect(x0, y0, x1, y1):
    return (x1 - x0) * (y1 - y0), 2 * ((x1 - x0) + (y1 - y0))


def _overlap(a, b):
    """area of two axis-aligned boxes (x0, y0, x1, y1)."""
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def curved_room(inp):
    r = inp["curved_room"]
    arc = r["jamb_arc_upper"]
    cx, cy = arc["centre"]
    R = arc["radius_m"]
    for k in ("jamb_arc_lower",):
        assert r[k]["radius_m"] == R and r[k]["centre"] == arc["centre"]
    glaz_room_side = max(g["radius_m"] for g in r["glazing_arcs"])
    lower = (r["south_east"]["b"][0], r["south_east"]["b"][1])                     # C0A end on the arc
    upper = (r["east_line_upper"]["a"][0], r["east_line_upper"]["a"][1])           # B6B start on the arc
    west_x = r["west"]["a"][0]
    north_y = r["north"]["a"][1]
    east_x = r["east_line_upper"]["a"][0]
    south_y = r["south_west"]["a"][1]
    ring = [{"p": (west_x, south_y)}, {"p": lower, "kind": "ARC", "radius": R, "side": -1, "role": "WALL"},
            {"p": upper}, {"p": (east_x, north_y)}, {"p": (west_x, north_y)}]
    main = FT.face_area(ring)
    straight = FT.chord_reading_refused([{"p": (west_x, south_y)}, {"p": (east_x, south_y)},
                                         {"p": (east_x, north_y)}, {"p": (west_x, north_y)}])
    chord = FT.chord_reading_refused(ring)
    # strip OP-009 and the lobby, from the faces
    sx0, sx1 = r["south_west"]["b"][0], r["south_east"]["a"][0]
    strip_y0 = r["strip_south_west"]["a"][1]
    strip = (sx0, strip_y0, sx1, south_y)
    lobby = (r["lobby_west"]["a"][0], r["lobby_west"]["a"][1], r["lobby_east_upper"]["a"][0], r["lobby_west"]["b"][1])
    a_strip, _ = _rect(*strip)
    a_lobby, p_lobby = _rect(*lobby)
    # column projections into the three parts (axis-aligned outlines; none reaches the arc)
    main_box = (west_x, south_y, east_x, north_y)
    cols = []
    for c in r["columns"]:
        xs = [p[0] for p in c["points"]]
        ys = [p[1] for p in c["points"]]
        cb = (min(xs), min(ys), max(xs), max(ys))
        ov = _overlap(cb, main_box) + _overlap(cb, strip) + _overlap(cb, lobby)
        assert cb[2] <= lower[0] + 1e-9 or cb[1] >= upper[1] - 1e-9 or ov == 0.0     # clear of the curved face
        cols.append({"handle": c["handle"], "m2": _r(ov, 5)})
    col_m2 = sum(c["m2"] for c in cols)
    opening = sx1 - sx0
    # outline of the joined face: column notches sit in corners (no perimeter change): checked by position
    total = main["area_m2"] + a_strip + a_lobby - col_m2
    per = main["perimeter_m"] - opening + 2 * (south_y - strip_y0) + p_lobby - opening
    # joinery box in the lobby (layer-5 box with a diagonal, no wall line): floor continues under it
    jb = [x for x in inp["lobby_inside"] if x.get("type") == "LINE"]
    jx = sorted({x["a"][0] for x in jb} | {x["b"][0] for x in jb})
    joinery = (jx[0], lobby[1], jx[-1], lobby[3])
    a_join = _rect(*joinery)[0]
    seg = straight["area_m2"] - main["area_m2"]
    dims = {d["handle"]: d["measurement_mm"] / 1000.0 for d in r["dims"]}
    printed = {"width F4C": dims["F4C"], "depth EAD": dims["EAD"], "apex width E6F": dims["E6F"],
               "lobby F88": dims["F88"], "lobby FAA": dims["FAA"], "strip F9F": dims["F9F"],
               "curved wall E7B": dims["E7B"]}
    checks = {
        "width = printed 4200": math.isclose(east_x - west_x, dims["F4C"], abs_tol=5e-4),
        "depth = printed 4000": math.isclose(north_y - south_y, dims["EAD"], abs_tol=5e-4),
        "apex = centre x - R = printed 3450": math.isclose(cx - R - west_x, dims["E6F"], abs_tol=5e-4),
        "curved wall R - R_outer = printed 200": math.isclose(R - r["outer_arcs"][0]["radius_m"], dims["E7B"], abs_tol=5e-4),
        "glazing room-side arc on the wall jamb radius": glaz_room_side == R,
        "lobby = printed 1800 x 2100": math.isclose(lobby[2] - lobby[0], dims["F88"], abs_tol=5e-4)
                                         and math.isclose(lobby[3] - lobby[1], dims["FAA"], abs_tol=5e-4),
        "strip depth = printed 150": math.isclose(south_y - strip_y0, dims["F9F"], abs_tol=5e-4),
    }
    assert all(checks.values()), checks
    readings = [
        {"id": "A drawn arc face R 2.135 + OP-009 strip + lobby, joinery not deducted (engine line)",
         "m2": total, "lm": per, "physical": True},
        {"id": "B as A, the lobby joinery 0.50 x 2.10 deducted", "m2": total - a_join, "lm": per + 2 * (joinery[2] - joinery[0]),
         "physical": True},
        {"id": "C room to the arc face only (no strip, no lobby)", "m2": main["area_m2"] - (cols[0]["m2"] + cols[1]["m2"])
         - _overlap(_box(r["columns"][2]), main_box), "lm": main["perimeter_m"], "physical": True},
        {"id": "D room to the arc face + strip", "m2": main["area_m2"] + a_strip - (cols[0]["m2"] + cols[1]["m2"])
         - _overlap(_box(r["columns"][2]), main_box), "lm": main["perimeter_m"] + 2 * (south_y - strip_y0), "physical": True},
        {"id": "E straight wall line (arc ignored) + strip + lobby: REFUSED (T-197 R4)", "m2": total + seg,
         "lm": per - main["perimeter_m"] + straight["perimeter_m"], "physical": False},
        {"id": "F chord between the arc ends + strip + lobby: REFUSED", "m2": total + (chord["area_m2"] - main["area_m2"]),
         "lm": per - main["perimeter_m"] + chord["perimeter_m"], "physical": False},
        {"id": "G apex width 3.45 x 4.00 + strip + lobby (printed E6F as a rectangle): REFUSED", "m2":
         dims["E6F"] * dims["EAD"] + a_strip + a_lobby - col_m2, "lm": 2 * (dims["E6F"] + dims["EAD"]) - opening
         + 2 * (south_y - strip_y0) + p_lobby - opening, "physical": False},
        {"id": "H the arc segment taken off twice (not a drawn element): REFUSED", "m2": total - seg, "lm": per,
         "physical": False},
    ]
    pairing = FT.pair_row(readings, FREELANCER_ROW["m2"], FREELANCER_ROW["lm"])
    a_row = pairing["readings"][0]
    h_row = pairing["readings"][-1]
    return {
        "element": "1F-R3CFCFD curved east room + open passage OP-009 + lobby (one line in the engine)",
        "arc": {"radius_m": R, "outer_radius_m": r["outer_arcs"][0]["radius_m"], "room_side": "R 2.135 (jamb arcs "
                "BD1 / BD6 on layer 1 and glazing BD2 on the same radius; BD3 .. BD5 glazing inside it, BCD / BD0 the "
                "outer face R 1.935)", "segment_vs_straight_m2": _r(seg), "arc_lm": main["arcs"][0]["arc_m"],
                "sense": main["arcs"][0]["sense"]},
        "printed": printed, "checks": checks,
        "parts": {"room_to_arc_m2": _r(main["area_m2"]), "strip_m2": _r(a_strip), "lobby_m2": _r(a_lobby),
                  "columns": cols, "columns_m2": _r(col_m2, 5), "joinery_box_m2": _r(a_join)},
        "engine_line_hand_m2": _r(total), "engine_line_hand_lm": _r(per, 4),
        "pairing": pairing,
        "residual": {"engine_minus_row_m2": a_row["d_m2"], "engine_minus_row_lm": a_row["d_lm"],
                     "of_which_segment_m2": _r(seg), "left_after_segment_m2": _r(a_row["d_m2"] - seg),
                     "segment_twice_reading": {"d_m2": h_row["d_m2"], "d_lm": h_row["d_lm"]}},
        "verdict": "ENGINE_RIGHT on geometry (own hand from the printed 4200 / 4000 / 3450 / 200 and the drawn arc R "
                   "2.135); the freelancer row 17.29 / 22.89 is UNRESOLVED: no physical reading closes either key, "
                   "the best area match (segment taken off twice, -0.043 m2) is not a drawn element and fails the "
                   "perimeter key by +0.739 lm",
    }


def _box(c):
    xs = [p[0] for p in c["points"]]
    ys = [p[1] for p in c["points"]]
    return (min(xs), min(ys), max(xs), max(ys))


def dressing(inp):
    d = inp["dressing"]
    f = {x["handle"]: x for x in d["faces"]}
    x0, x1 = f["B03"]["a"][0], f["B00"]["a"][0]
    y0, y1 = f["B00"]["a"][1], f["B20"]["a"][1]
    area, per = _rect(x0, y0, x1, y1)
    gap_s = f["AD4"]["b"][0] - f["AD5"]["a"][0]                    # OP-011, open passage to the 3.80 x 4.30 room
    gap_w = f["B03"]["b"][1] - f["B04"]["a"][1]                    # OP-019, door to the bath
    assert math.isclose(x1 - x0, inp["dressing"]["dims"][0]["measurement_mm"] / 1000, abs_tol=5e-4)
    boxes = [{"layer_role": "ANNOTATION", "has_wall_line": False, "counterpart_above_or_below": False,
              "handles": [b["handle"] for b in d["box"]], "layer": d["box"][0]["layer"]}]
    fixtures = [x for x in inp["dressing_inside"] if x.get("type") == "INSERT"]
    space = {"id": "1F-RFFE7AF", "label": None, "decision": None, "enclosed": True, "open_end_to_outside": False,
             "reached_from": ["DRY", "WET"], "fixtures": [], "drainage_checked": True,
             "stack_above_or_below": False, "floor_drawn_inside": True, "boxes": boxes, "area_m2": area}
    t = FT.type_space(space)
    return {"id": "1F-RFFE7AF", "faces": "B03 + B04 (west, door OP-019 between) / B00 (east) / B20 (north) / AD4 + AD5 "
            "(south, OP-011 between)", "size_m": [_r(x1 - x0, 3), _r(y1 - y0, 3)], "area_m2": _r(area),
            "outline_lm": _r(per), "op011_width_m": _r(gap_s, 3), "op019_width_m": _r(gap_w, 3),
            "inserts_inside": len(fixtures), "inside_any_layer": [x["handle"] for x in inp["dressing_inside"]],
            "typing": t,
            "released_A": "ARCH.SPACE 2.970 PROVISIONAL 'UNLABELLED_SPACE' (L-7c5a02386f49947cf223), in no floor line",
            "proposed": "FLOOR.INTERNAL +2.970 m2 (area DRAWING-CONFIRMED; Checker 22:05 re-measured), class DRY, "
                        "finish material HELD (URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1 would set porcelain once the DRY "
                        "class is VERIFIED; never borrowed from the bed room)"}


def side_passage(inp, rel):
    p = inp["side_passage"]
    w = max(x["a"][0] for x in p["east_faces"]) - p["west_faces"][0]["a"][0]
    L = p["mouth_ends"][0]["a"][1] - p["boundary_wall"][1]["a"][1]
    area = w * L
    space = {"id": "GF-R7B7A5D + GF-RF002DC + mouth strip OP-007", "label": None,
             "decision": {"class": "EXTERIOR", "source": "Q-67 A (condition MET, Checker 2026-10-20 21:05; mouth "
                          "re-read today: 0 lines on any layer across it)"},
             "enclosed": False, "open_end_to_outside": len(inp["side_passage_mouth_lines_on_any_layer"]) == 0,
             "area_m2": area}
    t = FT.type_space(space)
    eng = rel["gf_side_passage"]
    eng_in = eng["space_a_m2"] + eng["space_b_m2"] + eng["mouth_strip_m2"]
    return {"id": "GF side passage (engine faces GF-R7B7A5D 1.560 / GF-RF002DC 3.600)",
            "size_m": [_r(w, 3), _r(L, 3)], "area_m2": _r(area),
            "faces": "west A2 / A3 (door 19C between), east 9F / A0 / A1 (windows 3BE / 3CB), boundary wall 105 / 106 "
                     "(86 doubles 105), mouth between the ends of 120 / 15A",
            "mouth_lines_any_layer": len(inp["side_passage_mouth_lines_on_any_layer"]),
            "typing": t,
            "engine_released_A": eng,
            "engine_exterior_floor_m2": _r(eng_in),
            "missing_in_engine_m2": _r(area - eng_in),
            "not_floor_in_engine_m2": eng["boundary_wall_strip_m2"],
            "proposed": "out of ARCH.SPACE (internal unallocated) and out of the internal floor key: FLOOR.OUTDOOR side "
                        "area 5.640 m2 (area DRAWING-CONFIRMED: 1.200 x 4.700 own re-read = T-123), finish porcelain / "
                        "ceramic by the owner's sides rule (OWNER_RULE_OUTDOOR_FLOORS_2026-10-21: 'sides are never "
                        "interlock ... part of the house') = ASSUMED - OWNER-APPROVED; the mouth strip OP-007 0.240 is "
                        "part of it (not an interior doorway strip); the boundary-wall strip OP-001 0.280 is the top of "
                        "a solid wall (no opening drawn: lines 105 / 106 run the full width), no floor at all"}


def strips(rel):
    rows = []
    spec = [
        ("1F", "OP-011", "PASSAGE", ("DRY", "DRY"), 1.00, 0.15, "3.80 x 4.30 room / dressing (now typed DRY)"),
        ("1F", "OP-007", "PASSAGE", ("DRY", "LIFT_SHAFT"), 1.00, 0.20, "living / lift shaft (jambs B96 / B97)"),
        ("2F", "OP-002", "PASSAGE", ("DRY", "LIFT_SHAFT"), 1.00, 0.20, "stair room / lift shaft"),
        ("2F", "OP-001", "DOOR", ("DRY", "EXTERIOR"), 1.00, 0.15, "stair room / +9.70 roof"),
        ("GF", "OP-007", "PASSAGE", ("EXTERIOR", "EXTERIOR"), 1.20, 0.20, "side passage mouth (Q-67 A exterior)"),
    ]
    for fl, op, kind, sides, wd, dp, joins in spec:
        released = rel["strips"][f"{fl}-{op}"]
        if sides == ("EXTERIOR", "EXTERIOR"):
            c = {"item_code": "FLOOR.OUTDOOR (part of the side passage)", "status": FT.AOA, "qty_m2": _r(wd * dp),
                 "rule": "Q-67 A + OWNER_RULE_OUTDOOR_FLOORS sides rule", "why": "exterior floor, not a doorway strip"}
        else:
            c = WS.classify_strip({"opening_id": op, "opening_kind": kind, "sides": list(sides), "width_m": wd,
                                   "depth_m": dp})
        rows.append({"floor": fl, "opening": op, "joins": joins, "measured_m2": _r(wd * dp),
                     "released_A": released, "proposed_item": c["item_code"], "status": c["status"],
                     "qty_m2": c.get("qty_m2"), "rule": c["rule"]})
    rows.append({"floor": "GF", "opening": "OP-001", "joins": "side passage / boundary wall body (no opening drawn)",
                 "measured_m2": 0.0, "released_A": rel["strips"]["GF-OP-001"], "proposed_item": "none (no floor)",
                 "status": "ENGINE DEFECT", "qty_m2": None,
                 "rule": "UP-SPACE-001 / drawing: the boundary wall (lines 105 / 106, 86) runs the full 1.200 width"})
    # one strip, one line, after the proposal (the released twin ARCH.THRESHOLD of GF OP-001 retires with it)
    lines = [{"line_id": f"{x['floor']}-{x['opening']}", "opening_id": f"{x['floor']}-{x['opening']}",
              "item_code": x["proposed_item"].split(" (")[0], "covers_m2": x["qty_m2"] or x["measured_m2"]}
             for x in rows if x["proposed_item"] != "none (no floor)"]
    WS.assert_one_strip_one_line(lines)
    released_dup = WS.one_strip_one_line([
        {"line_id": rel["strips"]["GF-OP-001"]["line"], "opening_id": "GF-OP-001", "item_code": "FIN.FLOOR.PORCELAIN",
         "covers_m2": 0.28},
        {"line_id": rel["strips"]["GF-OP-001"]["twin"], "opening_id": "GF-OP-001", "item_code": "ARCH.THRESHOLD",
         "covers_m2": 0.28}])
    return rows, released_dup


def floor_key(cr, rel):
    t218 = json.loads((ROOT / "research/agents_t218/summary.json").read_text(encoding="utf-8"))["floor_key"]["after"]
    parts = list(csv.DictReader(open(ROOT / "research/agents_t218/FLOOR_KEY_T218.csv", encoding="utf-8")))
    eng = t218["engine_total_m2"] + 2.970 + 0.150                  # dressing in, OP-011 back to porcelain (DRY / DRY)
    eng -= rel["gf_side_passage"]["boundary_wall_strip_m2"] + rel["gf_side_passage"]["mouth_strip_m2"]
    ref = t218["compared_reference_m2"] + 3.120                    # S5 no longer taken out: both sides carry it
    new = []
    for p in parts:
        m2 = float(p["m2"])
        if p["id"].startswith("GF-OPEN"):
            m2 = m2 - rel["gf_side_passage"]["boundary_wall_strip_m2"] - rel["gf_side_passage"]["mouth_strip_m2"]
            new.append({"id": p["id"] + " less GF OP-001 0.280 (wall body) and OP-007 0.240 (exterior passage)",
                        "m2": _r(m2), "kind": "MEASUREMENT + SCOPE (T-223)"})
            continue
        if p["id"].startswith("1F curved"):
            new.append({"id": "1F curved room vs his 17.29 (engine geometry ENGINE_RIGHT; his row not reproducible)",
                        "m2": _r(cr["residual"]["engine_minus_row_m2"]), "kind": "UNRESOLVED (freelancer side)"})
            continue
        new.append({"id": p["id"], "m2": _r(m2), "kind": p["kind"]})
    new.append({"id": "1F dressing 2.970 + OP-011 0.150: in the engine key AND in his 'bed room 2' 19.46 (AGREE)",
                "m2": 0.0, "kind": "AGREE"})
    dec = WS.decompose(eng, ref, new)
    return {"engine_m2": _r(eng), "reference_m2": _r(ref), "like_for_like_m2": dec["diff_m2"],
            "like_for_like_pct": _r(100 * dec["diff_m2"] / ref, 2), "residual_m2": dec["residual_m2"],
            "closed": dec["closed"], "parts": new,
            "before_T218_m2": t218["like_for_like_m2"], "before_T218_pct": t218["like_for_like_pct"]}


def build():
    inp = json.loads(INPUT.read_text(encoding="utf-8"))
    rel = json.loads(RELEASED.read_text(encoding="utf-8"))
    cr = curved_room(inp)
    dr = dressing(inp)
    sp = side_passage(inp, rel)
    st, dup = strips(rel)
    fk = floor_key(cr, rel)
    sills = [x for x in st if x["opening"] in ("OP-007", "OP-002", "OP-001") and x["floor"] in ("1F", "2F")]
    summ = {"schema": "T223_SUMMARY_V1", "input_sha256_8": inp["sha256_8"], "curved_room": cr, "dressing": dr,
            "side_passage": sp, "strips": st, "released_duplicate_strip_lines": dup,
            "sills_to_threshold_m2": _r(sum(x["measured_m2"] for x in sills)), "floor_key": fk}
    return summ


def _csv(rows, cols):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in r.items()})
    return b.getvalue()


def outputs(s):
    pair = _csv(s["curved_room"]["pairing"]["readings"],
                ["id", "m2", "lm", "d_m2", "d_lm", "closes_area", "closes_perimeter", "physical", "verdict"])
    typ = _csv([{"id": s["dressing"]["id"], "class": s["dressing"]["typing"]["class"],
                 "wet_dry": s["dressing"]["typing"]["wet_dry"], "floor_line": s["dressing"]["typing"]["floor_line"],
                 "area_m2": s["dressing"]["area_m2"], "area_status": s["dressing"]["typing"]["area_status"],
                 "material_status": s["dressing"]["typing"]["material_status"], "released_A": s["dressing"]["released_A"],
                 "why": " | ".join(s["dressing"]["typing"]["why"])},
                {"id": s["side_passage"]["id"], "class": s["side_passage"]["typing"]["class"], "wet_dry": "",
                 "floor_line": s["side_passage"]["typing"]["floor_line"], "area_m2": s["side_passage"]["area_m2"],
                 "area_status": s["side_passage"]["typing"]["area_status"],
                 "material_status": "porcelain / ceramic, ASSUMED - OWNER-APPROVED (sides rule 2026-10-21)",
                 "released_A": "ARCH.SPACE 3.600 + 1.560 PROVISIONAL (internal unallocated) + GF-STRIP-OP-007 0.240 "
                               "porcelain; 0.240 missing; GF-STRIP-OP-001 0.280 porcelain is a wall top",
                 "why": " | ".join(s["side_passage"]["typing"]["why"])}],
               ["id", "class", "wet_dry", "floor_line", "area_m2", "area_status", "material_status", "released_A", "why"])
    st = _csv(s["strips"], ["floor", "opening", "joins", "measured_m2", "released_A", "proposed_item", "status",
                            "qty_m2", "rule"])
    key = _csv(s["floor_key"]["parts"], ["id", "m2", "kind"])
    return {OUT_PAIR: pair, OUT_TYPE: typ, OUT_STRIP: st, OUT_KEY: key,
            OUT_SUM: json.dumps(s, indent=1, sort_keys=True, ensure_ascii=False) + "\n"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    out = outputs(build())
    if a.check:
        bad = [p.name for p, t in out.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
        print("differs: " + ", ".join(bad) if bad else "T-223 ledger reproduces")
        return 1 if bad else 0
    for p, t in out.items():
        p.write_text(t, encoding="utf-8")
    print("wrote", ", ".join(p.name for p in out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
