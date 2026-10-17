"""R8.18 §9: WALL_FACE_SURFACE_POLICY_V2 - one wall-plane identity (WF-O1 fixed), two area methods reading different
data, explicit surface partition. Synthetic only: written and frozen BEFORE any Qortuba V2 run. Every valid fixture
asserts state == COMPUTED and both methods PASS."""

from __future__ import annotations

import random

from engine.source import topology as T, wall_contact_path as WC, wall_faces as V1, wall_faces_v2 as WF
from tests.r8_8 import helpers as H
from tests.r8_13.test_r8_13_wall_band_v4 import box
from tests.r8_16.test_r8_16_offset_closure import door_parts, walls
from tests.r8_16.test_r8_16_skirting_v3 import capped_passage, closure_passage, jambs_of, room, site_at
from tests.r8_17.test_r8_17_skirting_v4 import WALL_E, WIN, WIN_E, glazed_room, slide_map

U, H3, AUTH = 0.001, 3.0, "TEST HEIGHT"
WIN2 = "W|H51||SEGMENT"
WIN2_E = {"sources": ["W|H9||SEGMENT|0", "W|H51||SEGMENT|0"], "roles": ["GLAZING_BOUNDARY", "TOPOLOGY_BOUNDARY"],
          "length": 200.0, "hole": False}
SILL = {"sill_m": 1.0, "sill_authority": "SILL FACT"}


def ok(f):
    assert f["state"] == WF.COMPUTED, f["blockers"]
    assert f["reconciliation"]["state"] == "PASS" and f["conservation"]["reconciles"]
    return f


def faces(r, pt, height=H3, **kw):
    kw.setdefault("jambs", jambs_of(r))
    return WF.site_faces(WC.site_edges(r["_arr"], site_at(r, pt)), u=U, height_m=height, height_authority=AUTH,
                         eps=1e-6, **kw)


def win_fc(*keys):
    return {k: WC.opening_contact(sill_m=1.0, sill_authority="SILL FACT") for k in keys}


def edges_faces(edges, heights, fc, height=H3):
    return WF.site_faces([dict(e) for e in edges], u=U, height_m=height, height_authority=AUTH,
                         floor_contact_by_entity=fc, opening_heights=heights)


def doors(r, h=2.2):
    return {occ: {"height_m": h, "authority": "DOOR H"} for occ in r["openings"]}


VALID = []


def test_01_blank_wall():
    f = ok(WF.site_faces([dict(WALL_E)], u=U, height_m=H3, height_authority=AUTH))
    assert abs(f["areas_m2"]["WALL_PLANE_NET"] - 3.0) < 1e-9
    VALID.append(f)


def test_02_one_door_deducts_its_rectangle_and_keeps_the_wall_above():
    r = room(walls() + door_parts(), [("A", 250, 200), ("B", 750, 200)])
    f = ok(faces(r, (250, 200), opening_heights=doors(r)))
    (o,) = f["openings"]
    assert abs(o["rectangle_m2"] - 0.22) < 1e-9 and abs(o["above_opening_m2"] - 0.08) < 1e-9 and o["below_sill_m2"] == 0
    VALID.append(f)


def test_03_a_normal_window_keeps_the_wall_below_and_above_wf_o1():
    f = ok(edges_faces([WALL_E, WIN_E], {WIN: {"height_m": 1.5, "authority": "WIN H", **SILL}}, win_fc(WIN)))
    (o,) = f["openings"]
    assert abs(o["below_sill_m2"] - 0.12) < 1e-9 and abs(o["above_opening_m2"] - 0.06) < 1e-9
    assert abs(f["areas_m2"]["WALL_PLANE_NET"] - (1.12 * 3.0 - 0.18)) < 1e-9
    v1 = V1.site_faces([dict(WALL_E), dict(WIN_E)], u=U, height_m=H3, height_authority=AUTH,
                       floor_contact_by_entity=win_fc(WIN),
                       opening_heights={WIN: {"height_m": 1.5, "authority": "WIN H", **SILL}})
    assert v1["state"] == V1.BLOCKED and "AREA_RECONCILIATION_FAILED" in v1["blockers"]     # WF-O1 reproduced
    VALID.append(f)


def test_04_two_windows_each_one_rectangle():
    hs = {WIN: {"height_m": 1.5, "authority": "W", **SILL}, WIN2: {"height_m": 1.2, "authority": "W", **SILL}}
    f = ok(edges_faces([WALL_E, WIN_E, WIN2_E], hs, win_fc(WIN, WIN2)))
    assert sorted(o["rectangle_m2"] for o in f["openings"]) == [0.18, 0.24]
    VALID.append(f)


def test_05_a_window_top_below_the_trade_height_has_an_above_surface():
    f = ok(edges_faces([WALL_E, WIN_E], {WIN: {"height_m": 1.0, "authority": "W", **SILL}}, win_fc(WIN)))
    assert f["openings"][0]["contained"] and abs(f["openings"][0]["above_opening_m2"] - 0.12) < 1e-9
    VALID.append(f)


def test_06_a_window_reaching_the_trade_height_has_no_above_surface():
    f = ok(edges_faces([WALL_E, WIN_E], {WIN: {"height_m": 2.0, "authority": "W", **SILL}}, win_fc(WIN)))
    o = f["openings"][0]
    assert o["above_opening_m2"] == 0.0 and abs(o["rectangle_m2"] - 0.24) < 1e-9 and o["contained"]
    g = ok(edges_faces([WALL_E, WIN_E], {WIN: {"height_m": 2.5, "authority": "W", **SILL}}, win_fc(WIN)))
    assert not g["openings"][0]["contained"] and abs(g["openings"][0]["rectangle_m2"] - 0.24) < 1e-9   # clipped
    VALID.append(f)


def test_07_a_floor_reaching_sliding_glass_door_has_no_low_wall():
    r = glazed_room()
    f = ok(faces(r, (500, 100), floor_contact_by_entity=slide_map(r),
                 opening_heights={k: {"height_m": 2.2, "authority": "S"} for k in slide_map(r)}))
    (o,) = f["openings"]
    assert o["kind"] == WF.SLIDING_DOOR and o["below_sill_m2"] == 0.0 and abs(o["rectangle_m2"] - 0.66) < 1e-9
    VALID.append(f)


def test_08_full_height_glazing_removes_the_whole_plane_span():
    fl = WC.opening_contact(physical_class="FULL_HEIGHT_GLAZING", contact="OPENING_TO_FLOOR", authority="SRC")
    f = ok(edges_faces([WALL_E, WIN_E], {}, {WIN: fl}))
    (o,) = f["openings"]
    assert o["kind"] == WF.FLOOR_GLAZING and abs(o["rectangle_m2"] - 0.36) < 1e-9 and o["above_opening_m2"] == 0.0
    VALID.append(f)


def test_09_a_low_head_passage_has_two_head_faces():
    r = closure_passage()
    (p,) = r["passages"]
    f = ok(faces(r, (500, 100), passages=[{"passage_id": p["passage_id"], "width_m": p["width"] * U,
                                           "head": WF.WITH_HEAD, "head_height_m": 2.2, "head_authority": "HEAD"}]))
    assert len(f["head_faces"]) == 2 and abs(f["areas_m2"]["passage_head_faces"] - 2 * p["width"] * U * 0.8) < 1e-9
    VALID.append(f)


def test_10_a_full_height_passage_has_no_head_face():
    r = capped_passage()
    (p,) = r["passages"]
    f = ok(faces(r, (500, 100), passages=[{"passage_id": p["passage_id"], "width_m": p["width"] * U,
                                           "head": WF.FULL_HEIGHT}]))
    assert f["head_faces"] == []
    VALID.append(f)


def test_11_the_offset_door_analogue_computes_on_both_sides():
    r = room(walls(upper_left=490.0) + door_parts(), [("A", 250, 200), ("B", 750, 200)])
    assert next(iter(r["openings"].values()))["closure_b_rule"] == T.B_OFFSET_JAMB
    for pt in ((250, 200), (750, 200)):
        VALID.append(ok(faces(r, pt, opening_heights=doors(r))))


def test_12_13_column_and_duct_faces_are_separate_classes_not_wall_plane():
    col = {"sources": ["W|H70||SEGMENT|2"], "roles": ["STRUCTURAL_OBSTACLE"], "length": 500.0, "hole": False}
    duct = {"sources": ["W|H77||SEGMENT|0"], "roles": ["TOPOLOGY_BOUNDARY"], "length": 400.0, "hole": True}
    f = ok(WF.site_faces([dict(WALL_E), col, duct], u=U, height_m=H3, height_authority=AUTH,
                         obstacle_authority={"W|H77||SEGMENT": WC.OWNER_PHYSICAL_OBSTACLE}))
    a = f["areas_m2"]
    assert abs(a["COLUMN_FACE"] - 1.5) < 1e-9 and abs(a["OBSTACLE_FACE"] - 1.2) < 1e-9
    assert abs(a["WALL_PLANE_NET"] - 3.0) < 1e-9
    VALID.append(f)


def test_14_a_wet_tiled_room_at_its_own_height():
    r = room(box(2000, 2000), [("BATH", 1000, 1000)])
    f = ok(faces(r, (1000, 1000), height=3.2))
    assert abs(f["areas_m2"]["WALL_PLANE_NET"] - 8.0 * 3.2) < 1e-6
    VALID.append(f)


def test_15_16_17_physical_jambs_are_consumed_not_wall_and_reveals_have_their_own_identity():
    r = capped_passage()
    f = ok(faces(r, (500, 100)))
    assert f["conservation"]["consumed_by_physical_jambs_m"] > 0                 # the one physical cap jamb
    rv = V1.opening_reveals("P", width_m=0.12, depth_m=0.02, depth_basis="SOURCE", height_m=2.2, head=True,
                            sides=("LEFT_JAMB",))                                 # one-sided: no invented RIGHT
    assert [x["surface"] for x in rv] == ["LEFT_JAMB", "TOP_REVEAL"]
    VALID.append(f)


def test_18_topology_closures_are_zero_and_never_wall_plane():
    tc = {"sources": ["TCLOSURE|TC-x"], "roles": ["TOPOLOGY_CLOSURE"], "length": 200.0, "hole": False}
    f = ok(WF.site_faces([dict(WALL_E), tc], u=U, height_m=H3, height_authority=AUTH))
    assert abs(f["lengths_m"][WF.ZERO] - 0.2) < 1e-9 and not [s for s in f["surfaces"] if s["class"] == WF.ZERO]
    assert abs(f["areas_m2"]["WALL_PLANE_NET"] - 3.0) < 1e-9                    # zero material, zero area
    g = ok(faces(closure_passage(), (500, 100)))                                # closure lines are physical jambs here
    assert g["conservation"]["consumed_by_physical_jambs_m"] > 0
    VALID.append(f)


def test_19_duplicate_surface_guard():
    f = ok(faces(closure_passage(), (500, 100)))
    assert WF.double_count_guard({"S": f}, [])["state"] == "PASS"
    assert WF.double_count_guard({"S": f, "T": f, "S2": f}, [{"opening": "X", "surface": "LEFT_JAMB"}] * 2)[
        "state"] == "FAIL"


def test_20_shuffled_input_is_deterministic():
    base = faces(glazed_room(), (500, 100), floor_contact_by_entity=slide_map(glazed_room()),
                 opening_heights={k: {"height_m": 2.2, "authority": "S"} for k in slide_map(glazed_room())})
    for seed in (3, 7):
        r = glazed_room(seed)
        f = faces(r, (500, 100), floor_contact_by_entity=slide_map(r),
                  opening_heights={k: {"height_m": 2.2, "authority": "S"} for k in slide_map(r)})
        assert f["state"] == WF.COMPUTED and f["areas_m2"] == base["areas_m2"]


def test_21_both_area_methods_pass_on_every_valid_fixture():
    VALID.clear()
    for t in (test_01_blank_wall, test_02_one_door_deducts_its_rectangle_and_keeps_the_wall_above,
              test_03_a_normal_window_keeps_the_wall_below_and_above_wf_o1, test_04_two_windows_each_one_rectangle,
              test_05_a_window_top_below_the_trade_height_has_an_above_surface,
              test_06_a_window_reaching_the_trade_height_has_no_above_surface,
              test_07_a_floor_reaching_sliding_glass_door_has_no_low_wall,
              test_08_full_height_glazing_removes_the_whole_plane_span, test_09_a_low_head_passage_has_two_head_faces,
              test_10_a_full_height_passage_has_no_head_face, test_11_the_offset_door_analogue_computes_on_both_sides,
              test_12_13_column_and_duct_faces_are_separate_classes_not_wall_plane,
              test_14_a_wet_tiled_room_at_its_own_height,
              test_15_16_17_physical_jambs_are_consumed_not_wall_and_reveals_have_their_own_identity,
              test_18_topology_closures_are_zero_and_never_wall_plane):
        t()
    assert len(VALID) >= 16
    assert all(f["state"] == WF.COMPUTED and f["reconciliation"]["state"] == "PASS" for f in VALID)


def test_22_a_broken_surface_partition_fails_the_reconciliation():
    f = ok(edges_faces([WALL_E, WIN_E], {WIN: {"height_m": 1.5, "authority": "W", **SILL}}, win_fc(WIN)))
    broken = [s for s in f["surfaces"] if s["class"] != WF.BELOW_SILL]           # the WF-O1 kind of omission
    rec = WF.reconcile(f["reconciliation"]["method_a_m2"], broken)
    assert rec["state"] == "FAIL" and abs(rec["difference_m2"] - 0.12) < 1e-9
    doubled = f["surfaces"] + [s for s in f["surfaces"] if s["class"] == WF.ABOVE_OPENING]
    assert WF.reconcile(f["reconciliation"]["method_a_m2"], doubled)["state"] == "FAIL"
    no_h = WF.site_faces([dict(WALL_E)], u=U, height_m=None, height_authority=None)
    assert no_h["state"] == WF.BLOCKED and "areas_m2" not in no_h
    assert WF.policy_record()["extends"] == "WALL_FACE_SURFACE_POLICY_V1"
