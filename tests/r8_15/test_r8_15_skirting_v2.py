"""R8.15 §36: WALL_CONTACT_PATH_POLICY_V2 - the physical path kept apart from the skirting measurement region.
Written and frozen BEFORE any Qortuba skirting quantity."""

from __future__ import annotations

from engine.source import room_topology as RT, topology as T, topology_closures as TC, wall_contact_path as WC
from tests.r8_8 import helpers as H
from tests.r8_13.test_r8_13_wall_band_v4 import box, rect, wall
from tests.r8_14.test_r8_14_skirting import door_rooms

M = WC.SkirtingMethod("TEST-METHOD", 1, {})                 # defaults: deduct windows, no return, faces included


def room(parts, texts):
    return RT.run(H.inp(parts, texts=texts), frame_insert=None, closure_policy=TC.POLICY_ID)


def site_at(r, pt):
    sid, _ = T.locate(r["_arr"], r["sites"], pt, 0.0)
    return next(s for s in r["sites"] if s["site_id"] == sid)


def jambs(r):
    return [tuple(map(tuple, j["segment"])) for p in r.get("passages") or [] for j in p.get("jamb_faces", [])]


def measure(r, pt, method=M, **kw):
    return WC.measure(WC.site_edges(r["_arr"], site_at(r, pt)), method, jamb_segments=jambs(r), eps=1e-6, **kw)


def edge(roles, length=120.0, src=("W|H1||SEGMENT|0", "W|H2||SEGMENT|0")):
    return {"sources": list(src), "roles": list(roles), "length": length, "hole": False}


WALL_E = edge(["TOPOLOGY_BOUNDARY"], 1000.0, ("W|H9||SEGMENT|0",))
WINDOW_E = edge(["GLAZING_BOUNDARY", "TOPOLOGY_BOUNDARY"])


def test_a_dry_room_wall_path_is_measured_from_its_real_walls():
    r = room(box(500, 400), [H.text(5, "BED", 250, 200)])
    m = measure(r, (250, 200))
    assert m["state"] == WC.COMPUTED and abs(m["length"] - 1800.0) < 1e-9 and set(m["components"]) == {WC.REAL_WALL_FACE}


def test_a_wardrobe_and_loose_furniture_do_not_remove_the_path():
    furn = rect(30, 0, 300, 200, 400, layer="FURNITURE") + rect(31, 200, 100, 350, 160, layer="FURNITURE")
    r = room(box(500, 400) + furn, [H.text(5, "BED", 250, 250)])
    assert abs(measure(r, (250, 250))["length"] - 1800.0) < 1e-9


def test_a_door_breaks_the_path():
    m = measure(door_rooms(), (250, 200))
    assert m[ "state"] == WC.COMPUTED and WC.DOOR_OPENING in m["excluded"]
    assert abs(m["length"] - (495 + 400 + 495 + 150 + 150)) < 1e-9


def test_an_open_passage_breaks_the_path_and_its_closure_jambs_count_zero():
    p = box() + wall(lower=((0, 300), (300, 600))) + \
        [H.seg(20, 720, 400, 1000, 400), H.seg(21, 720, 420, 1000, 420), H.seg(91, 720, 400, 720, 420, layer="DIM")]
    r = room(p, [H.text(5, "HALL", 500, 100), H.text(6, "LOBBY", 500, 700)])
    m = measure(r, (500, 100))
    assert m["state"] == WC.COMPUTED and WC.OPENING_JAMB in m["excluded"]
    assert WC.OPENING_JAMB not in m["components"] and WC.TOPOLOGY_CLOSURE not in m["components"]
    ret = measure(r, (500, 100), WC.SkirtingMethod("T", 1, {}, jamb_return=WC.RETURN_TO_FRAME))
    assert abs(ret["length"] - m["length"] - m["excluded"][WC.OPENING_JAMB]) < 1e-9


def test_a_drawn_jamb_cap_at_a_passage_is_a_jamb_not_room_wall_face():
    p = box() + [H.seg(10, 0, 400, 880, 400), H.seg(11, 0, 420, 880, 420), H.seg(12, 880, 400, 880, 420)]
    r = room(p, [H.text(5, "A", 500, 100), H.text(6, "B", 500, 700)])
    assert any(pp["end_kind"] == "CAPPED" for pp in r["passages"])
    m = measure(r, (500, 100))
    assert abs(m["excluded"][WC.OPENING_JAMB] - 20.0) < 1e-9                         # the 20-unit cap
    v1 = WC.path(WC.site_edges(r["_arr"], site_at(r, (500, 100))))                      # what V1 would have done
    assert abs(v1["on_path_length"] - m["length"] - 20.0) < 1e-9
    assert measure(r, (500, 100), WC.SkirtingMethod("T", 1, {}, jamb_return=WC.UNRESOLVED))["state"] == WC.INCOMPLETE


def test_topology_closure_has_zero_length_on_every_method():
    e = edge(["TOPOLOGY_CLOSURE"], 20.0, ("TCLOSURE|TC-1",))
    for method in (M, WC.SkirtingMethod("T", 1, {}, jamb_return=WC.RETURN_TO_FRAME, window_treatment=WC.FOLLOW_WALL_BELOW)):
        m = WC.measure([WALL_E, e], method)
        assert m["length"] == 1000.0 and m["excluded"][WC.TOPOLOGY_CLOSURE] == 20.0


def test_a_full_wall_tile_room_has_no_skirting_even_with_a_real_path():
    r = room(box(500, 400), [H.text(5, "BATH", 250, 200)])
    edges = WC.site_edges(r["_arr"], site_at(r, (250, 200)))
    assert WC.physical_path(edges)["floor_contact_length"] == 1800.0
    m = WC.measure(edges, M, full_wall_tile=True)
    assert m["state"] == WC.NO_SKIRTING and m["length"] == 0.0


def test_the_duct_face_is_handled_explicitly():
    r = room(box(500, 400) + rect(50, 200, 150, 300, 190), [H.text(5, "BED", 100, 100)])
    ent = r["wall_bands"]["isolated_loops"][0]["entity"]
    edges = WC.site_edges(r["_arr"], site_at(r, (100, 100)))
    assert WC.measure(edges, M, obstacle_authority={ent: "UNPROVEN_OBSTACLE"})["state"] == WC.INCOMPLETE
    ok = WC.measure(edges, M, obstacle_authority={ent: WC.OWNER_PHYSICAL_OBSTACLE})
    assert ok["state"] == WC.COMPUTED and abs(ok["components"][WC.OBSTACLE_FACE] - 280.0) < 1e-9
    assert abs(ok["length"] - 2080.0) < 1e-9


def test_a_window_above_the_floor_does_not_break_the_physical_path():
    follow = WC.SkirtingMethod("T", 1, {}, window_treatment=WC.FOLLOW_WALL_BELOW)
    m = WC.measure([WALL_E, WINDOW_E], follow, wall_below={"W|H1||SEGMENT": True})
    assert m["state"] == WC.COMPUTED and m["length"] == 1120.0
    assert WC.classify_v2(WINDOW_E) == WC.WINDOW_OPENING


def test_a_full_height_opening_breaks_the_path_and_unknown_is_withheld():
    follow = WC.SkirtingMethod("T", 1, {}, window_treatment=WC.FOLLOW_WALL_BELOW)
    assert WC.measure([WALL_E, WINDOW_E], follow, wall_below={"W|H1||SEGMENT": False})["length"] == 1000.0
    u = WC.measure([WALL_E, WINDOW_E], follow)
    assert u["state"] == WC.INCOMPLETE and u["length"] is None


def test_an_owner_deduct_every_window_method_removes_the_width_whether_or_not_wall_stands_below():
    for wb in (True, False, None):
        m = WC.measure([WALL_E, WINDOW_E], M, wall_below={"W|H1||SEGMENT": wb} if wb is not None else {})
        assert m["state"] == WC.COMPUTED and m["length"] == 1000.0 and m["excluded"][WC.WINDOW_OPENING] == 120.0


def test_column_faces_carry_skirting_and_unknown_roles_are_withheld():
    col = edge(["STRUCTURAL_OBSTACLE", "TOPOLOGY_BOUNDARY"], 60.0, ("W|H7||SEGMENT|0",))
    assert WC.classify_v2(col) == WC.COLUMN_FACE
    assert WC.measure([WALL_E, col], M)["length"] == 1060.0
    odd = edge(["FURNITURE_OUTLINE"], 50.0, ("W|H8||SEGMENT|0",))
    assert WC.measure([WALL_E, odd], M)["state"] == WC.INCOMPLETE


def test_the_physical_path_and_the_measurement_region_stay_separate():
    jamb = {"sources": ["W|H3||SEGMENT|0"], "roles": ["TOPOLOGY_BOUNDARY"], "length": 20.0, "hole": False,
            "p0": (0.0, 0.0), "p1": (0.0, 20.0)}
    kw = {"jamb_segments": [((0.0, 0.0), (0.0, 20.0))], "eps": 1e-6}
    phys = WC.physical_path([WALL_E, jamb, WINDOW_E], **kw)
    assert phys["floor_contact_length"] == 1020.0                              # wall + jamb (window: per opening)
    assert WC.measure([WALL_E, jamb, WINDOW_E], M, **kw)["length"] == 1000.0
    rec = WC.policy_record_v2()
    assert rec["policy_id"] == "WALL_CONTACT_PATH_POLICY_V2" and "a jamb return without a RETURN method" in rec["never"]
