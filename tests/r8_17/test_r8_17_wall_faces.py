"""R8.17 §33: WALL_FACE_SURFACE_POLICY_V1 - physical wall surfaces from classified spans, opening deductions (US-06),
reveals (US-07 / source depth), reconciliation and the double-count guard. Synthetic only: written and frozen BEFORE
any Qortuba wall-face run (anti-calibration)."""

from __future__ import annotations

import random

from engine.source import room_topology as RT, topology as T, topology_closures as TC
from engine.source import wall_contact_path as WC, wall_faces as WF
from tests.r8_8 import helpers as H
from tests.r8_13.test_r8_13_wall_band_v4 import box
from tests.r8_16.test_r8_16_offset_closure import door_parts, walls
from tests.r8_16.test_r8_16_skirting_v3 import capped_passage, closure_passage, jambs_of, room, site_at
from tests.r8_17.test_r8_17_skirting_v4 import WALL_E, WIN, WIN_E, glazed_room, slide_map

U = 0.001                                             # native mm -> m
H3 = 3.0
AUTH = "TEST HEIGHT FACT"


def faces(r, pt, height=H3, auth=AUTH, **kw):
    kw.setdefault("jambs", jambs_of(r))
    return WF.site_faces(WC.site_edges(r["_arr"], site_at(r, pt)), u=U, height_m=height, height_authority=auth,
                         eps=1e-6, **kw)


def door_heights(r, h=2.2):
    return {occ: {"height_m": h, "authority": "TEST DOOR HEIGHT"} for occ in r["openings"]}


def test_a_rectangular_dry_room_is_its_boundary_spans_times_the_height():
    r = room(box(4000, 3000), [("BED", 2000, 1500)])
    f = faces(r, (2000, 1500))
    assert f["state"] == WF.COMPUTED and abs(f["areas_m2"]["WALL_FACE_NET"] - 14.0 * H3) < 1e-6
    assert f["conservation"]["reconciles"] and f["areas_m2"]["check_two_ways"]


def test_no_height_authority_means_no_area():
    r = room(box(4000, 3000), [("BED", 2000, 1500)])
    f = faces(r, (2000, 1500), auth=None)
    assert f["state"] == WF.BLOCKED and "areas_m2" not in f and f["blockers"][0] == "TRADE_HEIGHT_NOT_ESTABLISHED"


def test_a_door_deducts_its_full_area_and_leaves_a_lintel():
    r = room(walls() + door_parts(), [("A", 250, 200), ("B", 750, 200)])
    f = faces(r, (250, 200), opening_heights=door_heights(r))
    (op,) = f["openings"]
    assert op["kind"] == WF.DOOR and abs(op["deduction_m2"] - 0.1 * 2.2) < 1e-9 and abs(op["lintel_m2"] - 0.1 * 0.8) < 1e-9
    assert f["state"] == WF.COMPUTED and f["areas_m2"]["check_two_ways"]
    b = faces(r, (250, 200))                                                    # no door height -> blocked
    assert b["state"] == WF.BLOCKED and any(x.startswith("OPENING_HEIGHT_NOT_ESTABLISHED") for x in b["blockers"])


def test_a_window_above_the_floor_is_deducted_only_with_its_position_proven():
    fc = {WIN: WC.opening_contact(sill_m=1.0, sill_authority="SILL FACT")}
    e = [dict(WALL_E), dict(WIN_E)]
    ok = WF.site_faces(e, u=U, height_m=H3, height_authority=AUTH, floor_contact_by_entity=fc,
                       opening_heights={WIN: {"height_m": 1.5, "authority": "WIN H", "sill_m": 1.0,
                                              "sill_authority": "SILL FACT"}})
    (op,) = ok["openings"]
    assert op["kind"] == WF.WINDOW and abs(op["deduction_m2"] - 0.12 * 1.5) < 1e-9 and op["contained"]
    assert abs(ok["areas_m2"]["WALL_FACE_NET"] - (1.12 * H3 - 0.18)) < 1e-9
    no = WF.site_faces(e, u=U, height_m=H3, height_authority=AUTH, floor_contact_by_entity=fc,
                       opening_heights={WIN: {"height_m": 1.5, "authority": "WIN H"}})
    assert no["state"] == WF.BLOCKED and any(x.startswith("WINDOW_POSITION_NOT_PROVEN") for x in no["blockers"])


def test_a_floor_reaching_sliding_glass_door_is_a_full_opening_with_no_low_wall():
    r = glazed_room()
    f = faces(r, (500, 100), floor_contact_by_entity=slide_map(r),
              opening_heights={k: {"height_m": 2.2, "authority": "SLIDE H"} for k in slide_map(r)})
    (op,) = f["openings"]
    assert op["kind"] == WF.SLIDING_DOOR and op["sill_m"] == 0.0 and abs(op["deduction_m2"] - 0.3 * 2.2) < 1e-9
    assert f["state"] == WF.COMPUTED and not [s for s in f["spans"] if s["class"] == WF.WALL_FACE and
                                              any("H16" in x for x in s["sources"])]


def test_a_doorless_low_head_passage_has_head_faces_and_jamb_reveals():
    r = closure_passage()
    (p,) = r["passages"]
    f = faces(r, (500, 100), passages=[{"passage_id": p["passage_id"], "width_m": p["width"] * U, "head": WF.WITH_HEAD,
                                        "head_height_m": 2.2, "head_authority": "HEAD FACT"}])
    assert len(f["head_faces"]) == 2 and all(abs(h["height_m"] - 0.8) < 1e-9 for h in f["head_faces"])
    rv = WF.opening_reveals(p["passage_id"], width_m=p["width"] * U, depth_m=p["wall_thickness"] * U,
                            depth_basis="SOURCE (band thickness)", height_m=2.2, head=True)
    assert [x["surface"] for x in rv] == ["LEFT_JAMB", "RIGHT_JAMB", "TOP_REVEAL"]
    assert f["conservation"]["reconciles"] and f["conservation"]["consumed_by_physical_jambs_m"] > 0


def test_a_doorless_full_height_passage_has_jambs_only_and_no_head_face():
    r = capped_passage()
    (p,) = r["passages"]
    f = faces(r, (500, 100), passages=[{"passage_id": p["passage_id"], "width_m": p["width"] * U,
                                        "head": WF.FULL_HEIGHT}])
    assert f["head_faces"] == [] and f["state"] == WF.COMPUTED
    rv = WF.opening_reveals(p["passage_id"], width_m=p["width"] * U, depth_m=0.02, depth_basis="SOURCE",
                            height_m=H3, head=False)
    assert [x["surface"] for x in rv] == ["LEFT_JAMB", "RIGHT_JAMB"]
    one = WF.opening_reveals(p["passage_id"], width_m=p["width"] * U, depth_m=0.02, depth_basis="SOURCE",
                             height_m=H3, head=False, sides=("LEFT_JAMB",))     # the far side is a wall face: no jamb
    assert [x["surface"] for x in one] == ["LEFT_JAMB"]
    cont = [s for s in f["spans"] if s["class"] == WF.WALL_FACE]
    # both rooms are one site through the passage: every wall face incl. the 20-long continuous far face, minus the cap
    assert abs(sum(s["length_m"] for s in cont) * 1000 - 5340.0) < 1e-6
    assert abs(f["conservation"]["boundary_m"] - f["conservation"]["consumed_by_physical_jambs_m"] - 5.34) < 1e-9


def test_the_offset_jamb_door_analogue_is_a_door_opening_on_both_sides():
    r = room(walls(upper_left=490.0) + door_parts(), [("A", 250, 200), ("B", 750, 200)])
    (occ, st), = r["openings"].items()
    assert st["closure_b_rule"] == T.B_OFFSET_JAMB
    for pt in ((250, 200), (750, 200)):
        f = faces(r, pt, opening_heights=door_heights(r))
        assert [o["kind"] for o in f["openings"]] == [WF.DOOR] and f["state"] == WF.COMPUTED


def test_column_and_duct_faces_are_their_own_classes():
    col = {"sources": ["W|H70||SEGMENT|2"], "roles": ["STRUCTURAL_OBSTACLE"], "length": 500.0, "hole": False}
    duct = {"sources": ["W|H77||SEGMENT|0"], "roles": ["TOPOLOGY_BOUNDARY"], "length": 400.0, "hole": True}
    f = WF.site_faces([dict(WALL_E), col, duct], u=U, height_m=H3, height_authority=AUTH,
                      obstacle_authority={"W|H77||SEGMENT": WC.OWNER_PHYSICAL_OBSTACLE})
    a = f["areas_m2"]
    assert abs(a["COLUMN_FACE"] - 1.5) < 1e-9 and abs(a["OBSTACLE_FACE"] - 1.2) < 1e-9
    assert abs(a["WALL_FACE_NET"] - 3.0) < 1e-9                                # never merged
    g = WF.site_faces([dict(WALL_E), duct], u=U, height_m=H3, height_authority=AUTH,
                      obstacle_authority={"W|H77||SEGMENT": "UNPROVEN_OBSTACLE"})
    assert g["state"] == WF.BLOCKED and any(x.startswith("SURFACE_UNPROVEN") for x in g["blockers"])


def test_wet_room_tile_and_no_paint_come_from_rule_data_not_geometry():
    rules = {"WET_SERVICE_ROOM": {"WALL_TILE": {"state": "APPLIES", "height_m": 3.2, "authority": "WET FACT"},
                                  "PAINT": {"state": "NONE", "authority": "US-03"},
                                  "PLASTER": {"state": "NONE", "authority": "US-03"}},
             "DRY_INTERNAL_ROOM": {"PLASTER": {"state": "APPLIES", "height_m": None, "authority": None}}}
    t = WF.trade_assignment("WET_SERVICE_ROOM", rules)
    assert t["WALL_TILE"]["state"] == "APPLIES" and t["PAINT"]["state"] == "NONE" and t["PLASTER"]["state"] == "NONE"
    assert WF.trade_assignment("UNKNOWN", rules) == {}
    r = room(box(2000, 2000), [("BATH", 1000, 1000)])
    f = faces(r, (1000, 1000), height=t["WALL_TILE"]["height_m"], auth=t["WALL_TILE"]["authority"])
    assert abs(f["areas_m2"]["WALL_FACE_NET"] - 8.0 * 3.2) < 1e-6


def test_reveal_depth_from_source_first_and_the_fallback_is_labelled():
    a = WF.opening_reveals("D1", width_m=0.9, depth_m=0.15, depth_basis="SOURCE (strip thickness)", height_m=2.2)
    b = WF.opening_reveals("W1", width_m=1.2, depth_m=0.25, depth_basis="US-07 FALLBACK (no source depth)",
                           height_m=1.5)
    assert {x["depth_basis"] for x in a} == {"SOURCE (strip thickness)"} and abs(a[0]["area_m2"] - 0.33) < 1e-9
    assert {x["depth_basis"] for x in b} == {"US-07 FALLBACK (no source depth)"} and len(b) == 3   # no sill
    c = WF.opening_reveals("W2", width_m=1.2, depth_m=None, depth_basis="NONE", height_m=1.5)
    assert {x["state"] for x in c} == {WF.BLOCKED}


def test_opening_deductions_use_area_never_width_and_reconcile_two_ways():
    r = room(walls() + door_parts(), [("A", 250, 200), ("B", 750, 200)])
    f = faces(r, (250, 200), opening_heights=door_heights(r, 2.0))
    a = f["areas_m2"]
    assert abs(a["opening_deductions"] - 0.1 * 2.0) < 1e-9 and a["check_two_ways"]
    assert abs(a["wall_plane_gross"] - a["WALL_FACE_NET"] - a["opening_deductions"] + a["passage_head_faces"]) < 1e-9


def test_no_surface_is_counted_twice_and_topology_closures_have_zero_area():
    r = closure_passage()
    f = faces(r, (500, 100))
    zero = [s for s in f["spans"] if s["class"] == WF.ZERO]
    assert all(s["area_m2"] == 0.0 for s in zero)
    rv = WF.opening_reveals("P", width_m=0.3, depth_m=0.02, depth_basis="SOURCE", height_m=2.2)
    g = WF.double_count_guard({"S1": f}, rv)
    assert g["state"] == "PASS"
    assert WF.double_count_guard({"S1": f, "S2": f}, rv + rv)["state"] == "FAIL"


def test_shuffled_input_gives_the_same_wall_faces():
    base = faces(glazed_room(), (500, 100), floor_contact_by_entity=slide_map(glazed_room()),
                 opening_heights={k: {"height_m": 2.2, "authority": "S"} for k in slide_map(glazed_room())})
    for seed in (4, 8):
        r = glazed_room(seed)
        f = faces(r, (500, 100), floor_contact_by_entity=slide_map(r),
                  opening_heights={k: {"height_m": 2.2, "authority": "S"} for k in slide_map(r)})
        assert f["areas_m2"] == base["areas_m2"] and f["lengths_m"] == base["lengths_m"]
    rec = WF.policy_record()
    assert rec["policy_id"] == "WALL_FACE_SURFACE_POLICY_V1" and "room perimeter x height" in rec["never"]
