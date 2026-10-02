"""R8.17 §11: WALL_CONTACT_PATH_POLICY_V4 - opening-side relations kept apart from physical jamb surfaces (V3-O1),
floor-reaching sliding glazed doors, conservation of every edge. Synthetic only: written and frozen BEFORE any
Qortuba V4 skirting run (anti-calibration)."""

from __future__ import annotations

import random

from engine.source import opening_facts as OPF, room_topology as RT, topology as T, topology_closures as TC
from engine.source import wall_contact_path as WC
from tests.r8_8 import helpers as H
from tests.r8_13.test_r8_13_wall_band_v4 import D2_TEXT, box, d2_replica
from tests.r8_16.test_r8_16_offset_closure import door_parts, walls
from tests.r8_16.test_r8_16_skirting_v3 import capped_passage, closure_passage, jambs_of, room, site_at

M = WC.SkirtingMethodV3("TEST-METHOD", 3, {})
WALL_E = {"sources": ["W|H9||SEGMENT|0"], "roles": ["TOPOLOGY_BOUNDARY"], "length": 1000.0, "hole": False,
          "p0": (0.0, 0.0), "p1": (1000.0, 0.0)}
WIN_E = {"sources": ["W|H9||SEGMENT|0", "W|H50||SEGMENT|0"], "roles": ["GLAZING_BOUNDARY", "TOPOLOGY_BOUNDARY"],
         "length": 120.0, "hole": False}
WIN = "W|H50||SEGMENT"
SLIDE = {"state": WC.FLOOR_LEVEL, "physical_class": WC.SLIDING_GLAZED_DOOR, "authority": "OWNER-SLIDE@v1"}


def m4(r, pt, method=M, jambs=None, **kw):
    return WC.measure_v4(WC.site_edges(r["_arr"], site_at(r, pt)), method,
                         jambs=jambs_of(r) if jambs is None else jambs, eps=1e-6, **kw)


def m3(r, pt, method=M, **kw):
    return WC.measure_v3(WC.site_edges(r["_arr"], site_at(r, pt)), method, jambs=jambs_of(r), eps=1e-6, **kw)


def glazed_room(shuffle=None):
    """Two rooms split by a 20-thick wall (y 400..420) with a 300-wide glazed opening (x 400..700): the wall ends are
    capped, one glazing line runs along the wall centre across the gap."""
    p = box() + [H.seg(10, 0, 400, 400, 400), H.seg(11, 700, 400, 1000, 400), H.seg(12, 0, 420, 400, 420),
                 H.seg(13, 700, 420, 1000, 420), H.seg(14, 400, 400, 400, 420), H.seg(15, 700, 400, 700, 420),
                 H.seg(16, 400, 410, 700, 410, layer="GLAZING")]
    if shuffle is not None:
        random.Random(shuffle).shuffle(p)
    return room(p, [("HALL", 500, 100), ("PAINTRY", 500, 700)])


def slide_map(r):
    keys = {s for c in r["closures"] if c.source_id.startswith("CLOSURE|GLAZED|") for s in (c.source_id,)}
    out = {}
    for k in keys:
        oid = k.split("|", 1)[1].rsplit("|", 1)[0]
        for x in (k, WC._entity(k), oid):
            out[x] = SLIDE
    for e in WC.site_edges(r["_arr"], site_at(r, (500, 100))):
        for s in e["sources"]:
            if not s.startswith("CLOSURE|") and WC.GLAZING_ROLE in e["roles"]:
                out[WC._entity(s)] = SLIDE
    return out


# ------------------------------------------------------------------------------- 1-5 jambs vs continuous faces
def test_01_doorless_opening_with_two_physical_jambs_counts_both_once():
    r = closure_passage()
    m = m4(r, (500, 100))
    assert abs(m["components"][WC.PHYSICAL_OPENING_JAMB] - 40.0) < 1e-9 and m["conservation"]["reconciles"]
    assert WC.TOPOLOGY_CLOSURE not in m["components"]


def test_02_one_jamb_and_one_continuous_face_counts_the_jamb_and_keeps_the_face():
    r = capped_passage()
    a, b = m3(r, (500, 100)), m4(r, (500, 100))
    assert abs(b["components"][WC.PHYSICAL_OPENING_JAMB] - 20.0) < 1e-9
    assert abs((b["length"] - a["length"]) - 20.0) < 1e-9                      # V3-O1: the 20 V3 lost is back
    assert "DOORLESS_JAMB_NOT_COUNTED" not in b["excluded"]


def test_03_the_continuous_wall_face_stays_payable_and_is_only_annotated():
    b = m4(capped_passage(), (500, 100))
    (n,) = b["opening_side_annotations"]
    assert n["end_kind"] == "CONTINUOUS_WALL_FACE" and n["consumed"] == 0.0 and abs(n["overlap"] - 20.0) < 1e-9
    assert b["conservation"]["reconciles"] and abs(b["conservation"]["residual"]) < 1e-6


def test_04_a_topology_closure_record_can_never_consume_real_wall():
    fake = {"opening": "X", "kind": WC.DOORLESS_JAMB, "segment": ((100.0, 0.0), (300.0, 0.0)), "length": 200.0,
            "physical": True, "source": "TCLOSURE|TC-x"}
    assert not WC.is_physical_jamb(fake)
    m = WC.measure_v4([WALL_E], M, jambs=[fake], eps=1e-6)
    assert m["length"] == 1000.0 and m["components"][WC.REAL_WALL_FACE] == 1000.0
    assert m["opening_side_annotations"][0]["consumed"] == 0.0


def test_05_a_non_physical_jamb_record_can_never_consume_wall():
    rec = {"opening": "X", "kind": WC.DOORLESS_JAMB, "segment": ((0.0, 0.0), (150.0, 0.0)), "length": 150.0,
           "physical": False, "source": "W|H9||SEGMENT|0", "end_kind": "CONTINUOUS_WALL_FACE"}
    m = WC.measure_v4([WALL_E], M, jambs=[rec], eps=1e-6)
    assert m["length"] == 1000.0 and WC.PHYSICAL_OPENING_JAMB not in m["components"]
    v3 = WC.measure_v3([WALL_E], M, jambs=[rec], eps=1e-6)
    assert v3["length"] == 850.0                                               # the V3-O1 defect, reproduced


# ------------------------------------------------------------------------------- 6-10 doors / glazing / wet
def test_06_installed_door_physical_jambs_exist_but_skirting_is_zero():
    r = room(walls() + door_parts(), [("A", 250, 200), ("B", 750, 200)])
    js = [j for j in jambs_of(r) if j["kind"] == WC.DOOR_JAMB]
    assert js and all(WC.is_physical_jamb(j) for j in js)
    m = m4(r, (250, 200))
    assert WC.PHYSICAL_OPENING_JAMB not in m["components"] and m["excluded"][WC.DOOR_PRESENT] == 100.0
    assert m["conservation"]["reconciles"]


def test_07_a_sliding_glass_door_to_the_floor_breaks_the_path_and_its_jambs_are_zero():
    r = glazed_room()
    fc = slide_map(r)
    m = m4(r, (500, 100), floor_contact_by_entity=fc)
    assert m["excluded"][WC.SLIDING_GLAZED_DOOR_TO_FLOOR] == 300.0
    assert WC.WINDOW_ABOVE_FLOOR not in m["components"] and not m["continuity_under_windows"]
    gj = WC.glazed_door_jambs(r["closures"], {k: v for k, v in fc.items() if k.startswith("GLAZED|")})
    assert len(gj) == 2 and all(j["kind"] == WC.GLAZED_DOOR_JAMB and abs(j["length"] - 20) < 1e-9 for j in gj)
    m2 = m4(r, (500, 100), jambs=jambs_of(r) + gj, floor_contact_by_entity=fc)
    assert m2["length"] == m["length"] and WC.PHYSICAL_OPENING_JAMB not in m2["components"]


def test_08_a_normal_window_above_the_floor_keeps_payable_continuity():
    m = WC.measure_v4([WALL_E, WIN_E], M,
                      floor_contact_by_entity={WIN: WC.opening_contact(sill_m=1.0, sill_authority="OWNER")})
    assert m["length"] == 1120.0 and m["continuity_under_windows"][0]["span"] == "SKIRTING_CONTINUITY_UNDER_WINDOW"


def test_09_floor_reaching_glazing_has_no_continuity_and_a_door_class_is_never_a_window():
    fl = WC.opening_contact(physical_class="FULL_HEIGHT_GLAZING", contact="OPENING_TO_FLOOR", authority="SRC")
    m = WC.measure_v4([WALL_E, WIN_E], M, floor_contact_by_entity={WIN: fl})
    assert m["excluded"][WC.FULL_HEIGHT_GLAZED] == 120.0 and not m["continuity_under_windows"]
    door = WC.opening_contact(physical_class=WC.SLIDING_GLAZED_DOOR, contact="OPENING_TO_FLOOR", authority="OWN",
                              sill_m=1.0, sill_authority="WINDOW FACT")
    assert door["state"] == WC.FLOOR_LEVEL and door["physical_class"] == WC.SLIDING_GLAZED_DOOR
    m2 = WC.measure_v4([WALL_E, WIN_E], M, floor_contact_by_entity={WIN: door, "W|H9||SEGMENT":
                                                                    WC.opening_contact(sill_m=1.0, sill_authority="W")})
    assert m2["excluded"][WC.SLIDING_GLAZED_DOOR_TO_FLOOR] == 120.0 and not m2["continuity_under_windows"]


def test_10_a_wet_full_wall_tile_room_has_no_skirting():
    m = m4(closure_passage(), (500, 100), full_wall_tile=True)
    assert m["state"] == WC.NO_SKIRTING and m["length"] == 0.0


# ------------------------------------------------------------------------------- 11-13 faces / determinism
def test_11_an_authorised_duct_face_is_payable_and_an_unauthorised_one_withheld():
    duct = {"sources": ["W|H77||SEGMENT|0"], "roles": ["TOPOLOGY_BOUNDARY"], "length": 400.0, "hole": True}
    a = WC.measure_v4([WALL_E, duct], M, obstacle_authority={"W|H77||SEGMENT": WC.OWNER_PHYSICAL_OBSTACLE})
    assert a["components"][WC.AUTHORISED_OBSTACLE_FACE] == 400.0 and a["length"] == 1400.0
    b = WC.measure_v4([WALL_E, duct], M, obstacle_authority={"W|H77||SEGMENT": "UNPROVEN_OBSTACLE"})
    assert b["withheld_length"] == 400.0 and b["state"] == WC.COMPUTED_WITH_WITHHELD


def test_12_a_column_face_is_its_own_class_on_the_path():
    col = {"sources": ["W|H70||SEGMENT|2"], "roles": ["STRUCTURAL_OBSTACLE"], "length": 50.0, "hole": False}
    m = WC.measure_v4([WALL_E, col], M)
    assert m["components"][WC.COLUMN_FACE] == 50.0 and m["components"][WC.REAL_WALL_FACE] == 1000.0


def test_13_shuffled_input_gives_the_same_v4_measurement():
    base = m4(capped_passage(), (500, 100))
    p = box() + [H.seg(10, 0, 400, 880, 400), H.seg(11, 0, 420, 880, 420), H.seg(12, 880, 400, 880, 420)]
    for seed in (2, 9):
        q = list(p)
        random.Random(seed).shuffle(q)
        r = room(q, [("A", 500, 100), ("B", 500, 700)])
        m = m4(r, (500, 100))
        assert abs(m["length"] - base["length"]) < 1e-9 and m["components"] == base["components"]
    a, b = m4(glazed_room(), (500, 100), floor_contact_by_entity=slide_map(glazed_room())), \
        m4(glazed_room(5), (500, 100), floor_contact_by_entity=slide_map(glazed_room(5)))
    assert a["length"] == b["length"] and a["excluded"] == b["excluded"]


# ------------------------------------------------------------------------------- 14-19 regressions
def test_14_hall_lobby_analogue_both_jambs_from_band_ends_closure_zero():
    r = closure_passage()
    m = m4(r, (500, 100))
    counted = [j for j in m["jambs_counted"] if j["counted"]]
    assert len(counted) == 2 and all(j["source"].startswith("BANDEND|") for j in counted)
    assert m["excluded"].get(WC.TOPOLOGY_CLOSURE, 0.0) >= 0.0 and WC.TOPOLOGY_CLOSURE not in m["components"]


def test_15_mb_dress_analogue_one_cap_jamb_and_the_continuous_face_on_the_path():
    m = m4(capped_passage(), (500, 100))
    assert [j["side"] for j in m["jambs_counted"] if j["counted"]] == ["LEFT"]
    assert [n["side"] for n in m["opening_side_annotations"]] == ["RIGHT"]


def test_16_i1471_analogue_offset_door_stops_with_zero_jambs_on_both_sides():
    r = room(walls(upper_left=490.0) + door_parts(), [("A", 250, 200), ("B", 750, 200)])
    (occ, st), = r["openings"].items()
    assert st["closure_b_rule"] == T.B_OFFSET_JAMB
    for pt in ((250, 200), (750, 200)):
        m = m4(r, pt)
        assert m["excluded"][WC.DOOR_PRESENT] == 100.0 and WC.PHYSICAL_OPENING_JAMB not in m["components"]
        assert m["conservation"]["reconciles"]


def test_17_h2430_h2431_analogue_v4_never_touches_topology_and_closures_stay_zero():
    a, b = closure_passage(), closure_passage()
    m4(b, (500, 100))
    assert sorted(round(s["area"], 6) for s in a["sites"]) == sorted(round(s["area"], 6) for s in b["sites"])
    tcs = [e for e in WC.site_edges(b["_arr"], site_at(b, (500, 100))) if WC.classify_v4(e) == WC.TOPOLOGY_CLOSURE]
    m = m4(b, (500, 100))
    assert all(WC.classify_v4(e) == WC.TOPOLOGY_CLOSURE for e in tcs) and WC.TOPOLOGY_CLOSURE not in m["components"]


def test_18_h1316_analogue_glazing_without_authority_is_withheld_never_wall_and_no_closure():
    p = box() + [H.seg(20, 300, 0.14, 300, 19.86)] + \
        [H.seg(21 + k, 300, y, 500, y, layer="GLAZING") for k, y in enumerate((0.0, 7.0, 13.0, 20.0))]
    r = RT.run(H.inp(p, texts=[H.text(5, "A", 500, 400)]), frame_insert=None, closure_policy=TC.POLICY_ID)
    assert not [c for c in r["closures"] if c.source_id.startswith("TCLOSURE|")]
    for s in r["sites"]:
        if s["labels"]:
            m = WC.measure_v4(WC.site_edges(r["_arr"], s), M, eps=1e-6)
            assert WC.REAL_WALL_FACE in m["components"] and m["conservation"]["reconciles"]


def test_19_v3_d2_false_passage_analogue_creates_no_passage_jamb():
    r = RT.run(H.inp(d2_replica(), texts=D2_TEXT), frame_insert=None, closure_policy=TC.POLICY_ID)
    assert not [p for p in r["passages"] if p["width"] > 500]
    bands = {b["band_id"]: b for b in r["wall_bands"]["bands"]}
    js = [j for p in r["passages"] for j in WC.passage_jambs(p, bands, 1e-6)]
    assert not [j for j in js if j["length"] > 500]
    rec = WC.policy_record_v4()
    assert rec["policy_id"] == "WALL_CONTACT_PATH_POLICY_V4" and rec["extends"] == "WALL_CONTACT_PATH_POLICY_V3"
    assert OPF.policy_record()["policy_id"] == "OPENING_PHYSICAL_CLASS_POLICY_V1"


def test_20_an_opening_fact_maps_only_its_own_bound_parts_and_only_when_it_applies():
    from engine.source import owner_facts as OF
    f = OF.PhysicalFact("F", 1, OPF.KIND, ("OWNER",), {}, (("R|H533||SEGMENT|0", "fp", "GLAZING"),),
                        {"physical_class": WC.SLIDING_GLAZED_DOOR, "floor_contact": "OPENING_TO_FLOOR"},
                        OPF.ALLOWED_DOMAINS)
    assert OPF.contact_map(f, {"binding": "STALE"}) == {}
    m = OPF.contact_map(f, {"binding": "APPLIES"})
    assert set(m) == {"R|H533||SEGMENT|0", "R|H533||SEGMENT", "GLAZED|R|H533||SEGMENT|0",
                      "CLOSURE|GLAZED|R|H533||SEGMENT|0"}
    assert {v["physical_class"] for v in m.values()} == {WC.SLIDING_GLAZED_DOOR}
    assert {v["state"] for v in m.values()} == {WC.FLOOR_LEVEL}
