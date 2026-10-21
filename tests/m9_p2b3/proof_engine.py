"""ENGINE ADAPTER - Phase 2B-3 proof library: runs the production engine on a proof case and reads back the
quantities the case's hand calculation states, then compares them (expected vs engine, difference, tolerance, PASS /
FAIL). This is the only file of the library that imports the engine; the expected values never pass through it.

    wp_area(case, method)       the waterproofed area of a proof case through waterproofing_system (V2.4 or V2.5)
    wp_quantities(area)         the engine quantities, keyed like the case's expected values
    wp_shared(cases, method)    the procurement cutting plans of several cases (one roll inventory per system)
    compare(expected, engine)   rows {quantity, expected, engine, difference, tolerance, result}
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "m9_p2b2"))

import p2b2_fixtures as F                                     # noqa: E402
from engine.source import knowledge as K                      # noqa: E402
from engine.source import waterproofing_system as WS          # noqa: E402
from engine.source import wp_geometry as WG                   # noqa: E402

U = 1e-3
V24, V25 = "ARCH_TAKEOFF_V2.4", "ARCH_TAKEOFF_V2.5"
TOL = {"m2": 0.001, "m": 0.001}


def wp_area(case, method=V25, *, room_id=None, floor="GF"):
    sc = case["scenario"]
    ring = [tuple(p) for p in sc["ring"]]
    gaps = [(d["edge"], d["t0"], d["t1"], "DOOR", d["id"]) for d in sc["doors"]] + \
        [(e["edge"], e["t0"], e["t1"], "OTHER", e["id"]) for e in sc.get("open_edges", ())]
    pieces = [{"opening_id": d["id"], "width_m": d["width_m"], "depth_m": d["depth_m"]} for d in sc["doors"]]
    doorways = [{"opening_id": d["id"], "width_m": d["width_m"], "depth_m": d["depth_m"],
                 "other_side": d["other_side"]} for d in sc["doors"]]
    ents = {"inserts": [{"id": i["id"], "name": i["name"], "x": i["x"] / U, "y": i["y"] / U} for i in sc["inserts"]],
            "texts": [{"id": t["id"], "value": t["value"], "x": t["x"] / U, "y": t["y"] / U} for t in sc["texts"]]}
    rid = room_id or case["id"]
    room = {"room_id": rid, "floor": floor, "name_en": case["title"], "codes": list(sc["codes"]),
            "polygon_m": ring, "hole_polygons_m": [], "polygon": [(x / U, y / U) for x, y in ring],
            "hole_polygons": []}
    net = abs(WG.signed_area(ring))
    with K.using("1.1.0"):
        res = F.resolver(*sc.get("rules") or ())
        a = WS.make_area(room, F.walls(ring, gaps), scope=sc["scope"], net_m2=net, continuation_pieces=pieces,
                         doorways=doorways, ents=ents, unit_m=U)
        return WS.build_area(a, res, v25=method == V25)


def _seams(alt):
    return alt.get("seams")


def wp_quantities(a):
    r = a["row"]
    lay = (a["layout"].get("layout") or {})
    sel = lay.get("direction")
    alts = [x for x in lay.get("alternatives") or () if x["direction"] != sel]
    dws = [x for x in a["transitions"] if x["kind"] == "DOORWAY" and x["type"] == "DOOR_THRESHOLD_TRANSITION"]
    pen = r["penetrations"]
    cor = r["corners"]
    rng = r["doorway_transitions"]["range_m2"]
    sens = r.get("roll_sensitivity") or {}
    q = {"A_net_m2": r["A_net_horizontal_m2"], "perimeter_m": a["boundary"]["total_lm"],
         "eligible_m": r["upturn"]["eligible_lm"], "upturn_m2": r["upturn"]["area_m2"],
         "doorway_continuation_m2": r["doorway_continuation_m2"],
         "proven_subtotal_m2": (r.get("proven_subtotal") or {}).get("total_m2",
                                                                   round(r["A_net_horizontal_m2"] +
                                                                         (r["upturn"]["area_m2"] or 0) +
                                                                         r["doorway_continuation_m2"], 6)),
         "direction": sel, "floor_strips": lay.get("floor_strips"), "last_strip_w_m": lay.get("last_strip_width_m"),
         "band_pieces_m": sorted(lay.get("band_pieces_m") or ()),
         "band_joints": ((lay.get("seams") or {}).get("upturn_end_laps") or {}).get("count"),
         "laps_m2": r["laps_m2"], "detailing_m2": r.get("detailing_m2", 0.0), "B_m2": r["B_installed_m2"],
         "consumed_m2": r["consumed_m2"], "waste_m2": r["cutting_waste_m2"], "rolls": r["rolls_if_installed_alone"],
         "cuts_m": sorted((s["length_m"] for x in lay.get("rolls") or () for s in x["segments"]), reverse=True),
         "untouched_m2": r["untouched_roll_tails_if_alone_m2"],
         "alt_rolls": alts[0]["rolls"] if alts else None, "alt_seams": _seams(alts[0]) if alts else None,
         "alt_consumed_m2": alts[0]["consumed_m2"] if alts else None,
         "doorway_transition": dws[0]["state"] if dws else None,
         "transition_range_m2": [rng["low"], rng["high"]] if rng else None,
         "transition_m2": r["doorway_transitions"]["resolved_m2"],
         "rolls_if_threshold_upturned": sens.get("rolls_if_every_open_doorway_is_upturned"),
         "termination_unresolved_m": r["terminations"]["unresolved_lm"],
         "corners_internal": cor["internal"], "corners_external": cor["external"], "corner_state": cor["state"],
         "penetrations": "COUNTED" if pen["state"] == "COUNTED_FROM_DRAWING" else pen["state"],
         "penetration_count": pen["count"],
         "penetration_treatment": "BY_DETAIL" if pen.get("quantity") else "WITHHELD",
         "final_material_state": r.get("final_material_state")}
    return q


def wp_shared(cases, method=V25):
    built = [wp_area(c, method) for c in cases]
    with K.using("1.1.0"):
        return WS.cutting_plan(built, exact=method == V25), built


def _unit(key):
    return "m2" if key.endswith("m2") else ("m" if key.endswith("_m") else None)


def _close(e, v, tol):
    if isinstance(e, bool) or e is None or isinstance(e, str):
        return e == v
    if isinstance(e, (int, float)):
        return isinstance(v, (int, float)) and not isinstance(v, bool) and abs(e - v) <= (tol or 0) + 1e-9
    if isinstance(e, list):
        return isinstance(v, list) and len(e) == len(v) and all(_close(x, y, tol) for x, y in zip(e, v))
    return e == v


def compare(expected, engine):
    """(7) / (8): one row per expected quantity."""
    rows = []
    for k, e in expected.items():
        v = engine.get(k, "<not reported>")
        tol = TOL.get(_unit(k)) if not isinstance(e, (str, bool)) and not (isinstance(e, int) and _unit(k) is None) \
            else None
        diff = None
        if isinstance(e, (int, float)) and not isinstance(e, bool) and isinstance(v, (int, float)) and \
                not isinstance(v, bool):
            diff = round(v - e, 6)
        rows.append({"quantity": k, "expected": e, "engine": v, "difference": diff, "tolerance": tol,
                     "result": "PASS" if _close(e, v, tol) else "FAIL"})
    return rows


# ------------------------------------------------------------------------------------------------ doors
def _run_doors(ents, roles, *, facts=None, rules=(), method=V25):
    """p2b2_fixtures.run_doors with the method's feasibility (V2.5: inclusive reach, conservative open run) and the
    door BOQ lines and jamb plaster lines of the floor."""
    from engine.source import arch_measure as AM
    from engine.source import arch_rooms as AR
    from engine.source import arch_walls as AW
    from engine.source import door_feasibility as DF
    from engine.source import door_model as DM
    from engine.source import door_standards as DSTD
    from engine.source import robust_geometry as RG
    S = AR.spaces(ents, roles, U, region_id="R", tol="UNIT_RELATIVE", geom=RG.Geometry(U), release_safety=True)
    S["walls"] = AW.walls(ents, roles, U, S["faces"], S["openings"], columns=S["column_boxes"], geom=RG.Geometry(U))
    M = AM.measure(S, floor="GF", project_id="P", revision_set_sha256="0" * 64, documents=[], facts=facts,
                   owner_scope=True, release_safety=True, door_height=lambda o_: DSTD.door_height(DSTD.INTERNAL, facts))
    fm = DM.floor_model(S, M["rooms"], ents, U, "GF", wall_layers=[k for k, v in roles.items() if v == "WALL"],
                        facts=DSTD.door_model_facts(facts), guards=True)
    tx = {t["id"]: t for t in ents["texts"]}
    ft = {f["face_id"]: [tx[i] for i in f.get("label_text_ids") or () if i in tx] for f in S["faces"]}
    model = DM.building_model([("GF", fm)], {"GF": ents["texts"]}, {"GF": ft}, U, entrance_floor="GF", facts=facts,
                              guards=True, not_entrance_codes=("BALCONY", "ROOF"))
    ctx = {"project_id": "P", "revision_set_sha256": "0" * 64, "documents": []}
    with K.using("1.1.0"):
        res = F.resolver(*rules)
        fctx = {"GF": DF.floor_context(S, ents, roles, U, M["rooms"], "GF", walls=S["walls"])}
        rep = DF.feasibility(model, fctx, resolver=res, facts=facts, **({"v25": True} if method == V25 else {}))
        lines, _ = DF.jamb_plaster_lines(ctx, M["lines"], model, res, facts, WS.wp_line)
        scen = DSTD.door_scenarios(model, facts, openings=[dict(o, floor="GF") for o in M["openings"]],
                                   rooms=M["rooms"])
    return {"S": S, "M": M, "model": model, "rep": rep, "door_lines": DM.boq_lines(ctx, model), "lines": lines,
            "scenarios": scen}


def door_run(case, method=V25, plan=None):
    p = dict(plan or case["plan"])
    rules = p.pop("rules", ())
    main = p.pop("main_entrance", None)
    if "columns" in p:
        p["columns"] = tuple(tuple(c) for c in p["columns"])
    kw = {"a_word": "BEDROOM", "b_word": "LIVING", "s0": 1500, "s1": 2400, "columns": ((600, 3400),), "b_right": 8200}
    kw.update(p)
    top, b_right = 4200, kw["b_right"]
    rooms = {"B": [(4200, 200), (b_right, 200), (b_right, top), (4200, top)]}
    words = [(kw["b_word"], ((4200 + b_right) / 2, 3000))]
    if kw.get("a_partition") is None:
        rooms["A"] = [(200, 200), (4000, 200), (4000, top), (200, top)]
        words.append((kw["a_word"], (2000, 3000)))
    else:
        y0 = kw["a_partition"]
        rooms["A1"] = [(200, 200), (4000, 200), (4000, y0), (200, y0)]
        rooms["A2"] = [(200, y0 + 200), (4000, y0 + 200), (4000, top), (200, top)]
        words += [("STORE", (2000, (200 + y0) / 2)), (kw["a_word"], (2000, (y0 + 200 + top) / 2))]
    outer = [(0, 0), (b_right + 200, 0), (b_right + 200, top + 200), (0, top + 200)]
    s0, s1 = kw["s0"], kw["s1"]
    openings = [("DOOR", "x", 4000, 4200, s0, s1, None)]
    swings = [((4200, s0), s1 - s0, 0, 90)]
    if main:
        openings.append(("DOOR", "y", main["y0"], main["y1"], main["s0"], main["s1"], None))
        half = (main["s1"] - main["s0"]) / 2
        swings += [((main["s0"], main["y1"]), half, 0, 90), ((main["s1"], main["y1"]), half, 90, 180)]
    ents = F.AS._s4_ents(rooms, outer, openings, texts=tuple(words), swings=tuple(swings), columns=kw["columns"])
    ents["inserts"] = []
    return _run_doors(ents, F.ROLES, rules=rules, method=method)


def _door_of(run, x_centre=None, category=None):
    for r in run["rep"]["rows"]:
        if category is not None and r["category"] == category:
            return r
        if category is None:
            o = next((x for x in run["S"]["openings"] if x["opening_id"] == r["opening_id"]), None)
            if o is not None and abs(o["centre"][0] - 4100) < 1:
                return r
    raise AssertionError("door not found")


def door_quantities(case, method=V25):
    run = door_run(case, method)
    main = case["plan"].get("main_entrance")
    r = _door_of(run, category="MAIN_ENTRANCE" if main else None)
    st = r.get("standard") or {}
    cl = r.get("clearances") or {}
    pm = r.get("proposed_modification") or {}
    pl = (r.get("placements") or [{}])[0]
    sw = r.get("swing") or {}
    el = next(e for e in run["model"]["elements"] if e["element_id"] == r["element_id"])
    dl = [ln for ln in run["door_lines"] if ln["physical_element"] == r["element_id"]]
    jp = [ln for ln in run["lines"] if ln["item_code"] == "FIN.PLASTER" and ln.get("physical_element") ==
          "door jambs and head" and ln["location"]["room_id"].endswith("-OPENING-" + str(r["opening_id"]))]
    q = {"category": r["category"], "cad_wall_opening_m": r["cad_wall_opening_m"],
         "required_nominal_door_m": st.get("required_nominal_door_m"), "urban_nominal_m": st.get("urban_nominal_m"),
         "standard_state": st.get("state"), "required_wall_opening_m": st.get("required_wall_opening_m"),
         "standard": r.get("standard"), "available_nominal_m": r.get("available_nominal_m"),
         "enlargement_m": r.get("enlargement_m"), "compliance": r.get("compliance"),
         "start_constraint": (cl.get("START") or {}).get("constraint"),
         "start_plain_m": (cl.get("START") or {}).get("plain_m"),
         "end_constraint": (cl.get("END") or {}).get("constraint"), "end_plain_m": (cl.get("END") or {}).get("plain_m"),
         "max_feasible_enlargement_m": pm.get("max_feasible_enlargement_m"),
         "max_is_lower_bound": pm.get("max_feasible_is_lower_bound"), "placement": pl.get("placement"),
         "placement_start_m": pl.get("start_m"), "placement_end_m": pl.get("end_m"), "swing": sw.get("state"),
         "swing_as_drawn": sw.get("as_drawn"), "leaf_m": sw.get("leaf_m"),
         "structure": (r.get("host_wall") or {}).get("structure"), "feasibility": r["feasibility"],
         "approvals": [a["who"] for a in pm.get("approvals") or ()],
         "door_that_fits_m": (pm.get("if_not_approved") or {}).get("door_that_fits_m"),
         "height_m": r["height"].get("value_m"), "height_state": r["height"]["state"],
         "door_count": sum(ln["measured_net"] for ln in dl),
         "door_area_m2": dl[0]["calculation"]["inputs"]["area_m2"] if dl else None,
         "as_drawn_width_m": round(el["structural_opening_width_m"], 6),
         "jamb_plaster_m2": jp[0]["measured_net"] if jp else None}
    sc = next((x for x in run["scenarios"]["rows"] if x["element_id"] == r["element_id"]), None)
    if sc is not None:
        q["assumed_area_m2"] = sc["as_drawn"]["wall_opening_area"]["m2"]
        q["assumed_area_state"] = sc["as_drawn"]["wall_opening_area"]["state"]
    if case.get("scope_check"):
        plan = dict(case["plan"], **case["scope_check"], a_word="BEDROOM")
        r2 = _door_of(door_run(case, method, plan=plan))
        q["scope_check_required_nominal_door_m"] = (r2.get("standard") or {}).get("required_nominal_door_m")
    return q


# ------------------------------------------------------------------------------------------------ rules sheets (CLI)
def _sha(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _bound(doc, dxf):
    import copy
    import json
    d = copy.deepcopy(doc)
    if d.get("drawing_sha256") == "<THIS DRAWING>":
        d["drawing_sha256"] = _sha(dxf)
    return json.loads(json.dumps(d))


def cli_run(dxf, out, *, rules=None, checks=None, method=V25):
    """the CLI (tools/urban_boq_m9.py main) on a proof drawing; -> the exit code and the outputs read back."""
    import json
    from tools import urban_boq_m9 as M9
    argv = ["arch", "--drawings", str(dxf), "--out", str(out), "--method", method]
    for flag, doc, name in (("--project-rules", rules, "rules.json"), ("--independent-checks", checks,
                                                                       "checks.json")):
        if doc is not None:
            p = Path(out).parent / f"{Path(out).name}_{name}"
            p.write_text(json.dumps(_bound(doc, dxf) if flag == "--project-rules" else doc), encoding="utf-8")
            argv += [flag, str(p)]
    code = M9.main(argv)
    rd = lambda n: json.loads((Path(out) / n).read_text(encoding="utf-8"))     # noqa: E731
    return {"code": code, "read": rd, "out": Path(out)}


def pd1_room_ids(run):
    """BATH1 / BATH2 of PD-1 by position (BATH1 x 0.2 .. 4.2 m)."""
    rooms = run["read"]("ARCH_ROOMS.json")["rooms"]
    out = {}
    for r in rooms:
        if "BATHROOM" not in (r.get("codes") or ()):
            continue
        xs = [p[0] for p in r["polygon_m"]]
        out["BATH1" if max(xs) < 4.5 else "BATH2"] = r["room_id"]
    return out


def rules_quantities(case, run):
    wp = run["read"]("WATERPROOFING_SCHEDULE.json")["waterproofing"]
    sheet = run["read"]("PROJECT_RULES_SHEET.json")["sheet"]
    plan = run["read"]("MEMBRANE_CUTTING_PLAN.json")["systems"]
    ids = pd1_room_ids(run)
    by = {a["room_id"]: a for a in wp["areas"]}
    q = {"binding": sheet.get("drawing_binding", {}).get("state"),
         "sheet_names_drawing": (sheet["project"]["drawing"] or {}).get("sha256") is not None,
         "row_status": {r["row_id"]: r["status"] for r in sheet["rows"]}}
    for name, rid in ids.items():
        a = by[rid]
        q[name] = {"upturn_h_m": a["upturn"]["height_m"], "height_state": a["upturn"]["height_state"],
                   "upturn_m2": a["upturn"]["area_m2"], "eligible_m": a["upturn"]["eligible_lm"],
                   "A_m2": a["A_net_horizontal_m2"], "B_m2": a["B_installed_m2"], "consumed_m2": a["consumed_m2"],
                   "waste_m2": a["cutting_waste_m2"], "rolls": a["rolls_if_installed_alone"],
                   "direction": a["direction"], "layout_state": a["layout_state"]}
    mats = {m.get("location", {}).get("room_id"): m for m in run["read"]("MATERIAL_RESULTS.json")["results"]
            if (m.get("method") or "").startswith("MEMBRANE")}
    for name, rid in ids.items():
        lay = (mats.get(rid) or {}).get("layout") or {}
        q[name].update(band_w_m=lay.get("band_width_m"), lanes_per_width=lay.get("lanes_per_roll_width"))
    wet = [p for p in plan if p["system_id"] == "URBAN_DEFAULT_WET_AREA"]
    q["shared_rolls"] = wet[0]["rolls"] if wet else None
    q["rolls_if_each_alone"] = wet[0]["rolls_if_each_area_alone"] if wet else None
    p_rows = {r["row_id"]: r for r in sheet["rows"]}
    b = (p_rows.get("P-PR-1") or {}).get("binding") or {}
    q["bound_room"] = next((n for n, rid in ids.items() if rid == b.get("room_id")), None)
    unres = run["read"]("UNRESOLVED.json")["unresolved"]
    q["conflict_questions"] = sum(1 for u in unres if u.get("item") == "PROJECT_RULES" and
                                  str(u.get("reason")).startswith("PROJECT_RULE_CONFLICT"))
    q["conflict_approvals"] = sum(1 for a in run["read"]("APPROVALS_REQUIRED.json")["approvals"]["items"]
                                  if a.get("subject") == "PROJECT_RULES" and a.get("row_id", "").startswith("C-"))
    q["open_items_project_rules"] = sum(1 for u in unres if u.get("item") == "PROJECT_RULES")
    return q
