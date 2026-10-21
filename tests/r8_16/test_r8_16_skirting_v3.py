"""R8.16 §36-§38: WALL_CONTACT_PATH_POLICY_V3 - floor-contact skirting authority (windows, doors, doorless
openings). Frozen before any Qortuba skirting total."""

from __future__ import annotations

import json
from pathlib import Path

from engine.source import room_topology as RT, topology as T, topology_closures as TC, wall_contact_path as WC
from tests.r8_8 import helpers as H
from tests.r8_13.test_r8_13_wall_band_v4 import box, wall
from tests.r8_16.test_r8_16_offset_closure import door_parts, walls

ROOT = Path(__file__).resolve().parents[2]
M = WC.SkirtingMethodV3("TEST-METHOD", 2, {})
RULE = next(r for r in json.loads((ROOT / "data/registry/URBAN_OWNER_METHOD_RULES.json").read_text())["rules"]
            if r["rule_id"] == "URBAN-SKIRTING-OPENING-METHOD")
WALL_E = {"sources": ["W|H9||SEGMENT|0"], "roles": ["TOPOLOGY_BOUNDARY"], "length": 1000.0, "hole": False}
WIN_E = {"sources": ["W|H9||SEGMENT|0", "W|H50||SEGMENT|0"], "roles": ["GLAZING_BOUNDARY", "TOPOLOGY_BOUNDARY"],
         "length": 120.0, "hole": False}
WIN = "W|H50||SEGMENT"


def fc(state, **kw):
    return {WIN: WC.floor_contact(**kw) if state is None else {"state": state}}


def room(parts, texts):
    return RT.run(H.inp(parts, texts=[H.text(50 + i, v, x, y) for i, (v, x, y) in enumerate(texts)]),
                  frame_insert=None, closure_policy=TC.POLICY_ID)


def site_at(r, pt):
    sid, _ = T.locate(r["_arr"], r["sites"], pt, 0.0)
    return next(s for s in r["sites"] if s["site_id"] == sid)


def jambs_of(r):
    bands = {b["band_id"]: b for b in r["wall_bands"]["bands"]}
    out = [j for p in r.get("passages") or [] for j in WC.passage_jambs(p, bands, 1e-6)]
    return out + WC.door_jambs(r["openings"], r["closures"])


def measure(r, pt, method=M, **kw):
    return WC.measure_v3(WC.site_edges(r["_arr"], site_at(r, pt)), method, jambs=jambs_of(r), eps=1e-6, **kw)


# ------------------------------------------------------------------------------- windows (§36)
def test_a_window_1_m_above_the_floor_keeps_the_skirting_continuous_below():
    m = WC.measure_v3([WALL_E, WIN_E], M, floor_contact_by_entity=fc(None, sill_m=1.0, sill_authority="OWNER"))
    assert m["state"] == WC.COMPUTED and m["length"] == 1120.0 and m["components"][WC.WINDOW_ABOVE_FLOOR] == 120.0
    assert m["continuity_under_windows"][0]["span"] == "SKIRTING_CONTINUITY_UNDER_WINDOW"


def test_a_window_0_5_m_above_the_floor_also_keeps_the_path():
    m = WC.measure_v3([WALL_E, WIN_E], M, floor_contact_by_entity=fc(None, sill_m=0.5, sill_authority="SOURCE"))
    assert m["length"] == 1120.0


def test_a_source_schedule_sill_and_an_owner_scoped_sill_both_prove_floor_contact():
    for auth in ("SOURCE_SCHEDULE W1 sill 0.90", "QORTUBA-NEW-NORMAL-WINDOWS-ABOVE-FLOOR-OWNER-001@v1"):
        assert WC.floor_contact(sill_m=0.9, sill_authority=auth)["state"] == WC.ABOVE_FLOOR


def test_full_height_glazing_and_a_sliding_door_break_the_path():
    for auth in ("floor-to-ceiling glazing (section)", "sliding door (schedule)"):
        m = WC.measure_v3([WALL_E, WIN_E], M, floor_contact_by_entity=fc(None, floor_level_authority=auth))
        assert m["length"] == 1000.0 and m["excluded"][WC.FULL_HEIGHT_GLAZED] == 120.0


def test_an_unknown_sill_is_withheld_not_guessed():
    m = WC.measure_v3([WALL_E, WIN_E], M, floor_contact_by_entity={})
    assert m["state"] == WC.COMPUTED_WITH_WITHHELD and m["withheld_length"] == 120.0 and m["length"] == 1000.0
    assert WC.floor_contact(sill_m=1.0)["state"] == WC.FLOOR_CONTACT_UNPROVEN      # a number without authority


def test_a_plan_window_never_breaks_the_floor_path_by_itself_and_never_touches_topology():
    r = room(box(500, 400), [("BED", 250, 200)])
    before = sorted(round(s["area"], 6) for s in r["sites"])
    m = WC.measure_v3([WALL_E, WIN_E], M, floor_contact_by_entity=fc(None, sill_m=1.0, sill_authority="OWNER"))
    assert WC.WINDOW_ABOVE_FLOOR in m["components"]
    assert sorted(round(s["area"], 6) for s in r["sites"]) == before            # trade-only, topology untouched
    assert "a plan-cut window as a floor opening without vertical evidence" in WC.policy_record_v3()["never"]


# ------------------------------------------------------------------------------- doors (§37)
def test_an_installed_door_stops_the_path_with_zero_jambs_and_zero_across():
    r = room(walls() + door_parts(), [("A", 250, 200), ("B", 750, 200)])
    m = measure(r, (250, 200))
    assert m["state"] == WC.COMPUTED and m["excluded"][WC.DOOR_PRESENT] == 100.0
    assert WC.PHYSICAL_OPENING_JAMB not in m["components"]
    assert abs(m["length"] - (495 + 400 + 495 + 150 + 150)) < 1e-9             # left room: walls only
    js = [j for j in jambs_of(r) if j["kind"] == WC.DOOR_JAMB]
    assert len(js) == 2 and all(abs(j["length"] - 10) < 1e-9 for j in js)


def test_the_offset_door_behaves_the_same_on_both_sides():
    r = room(walls(upper_left=490.0) + door_parts(), [("A", 250, 200), ("B", 750, 200)])
    for pt in ((250, 200), (750, 200)):
        m = measure(r, pt)
        assert m["state"] == WC.COMPUTED and WC.PHYSICAL_OPENING_JAMB not in m["components"]
        assert m["excluded"][WC.DOOR_PRESENT] == 100.0


def test_a_dry_wet_marble_door_has_the_same_stop_on_the_dry_side():
    r = room(walls() + door_parts(), [("BATH", 250, 200), ("BED", 750, 200)])
    m = measure(r, (750, 200))
    assert m["excluded"][WC.DOOR_PRESENT] == 100.0 and WC.PHYSICAL_OPENING_JAMB not in m["components"]
    assert measure(r, (250, 200), full_wall_tile=True)["state"] == WC.NO_SKIRTING


def test_door_plaster_jambs_exist_while_skirting_jambs_are_zero_and_the_swing_is_never_measured():
    r = room(walls() + door_parts(), [("A", 250, 200), ("B", 750, 200)])
    js = [j for j in jambs_of(r) if j["kind"] == WC.DOOR_JAMB]
    assert js and all(j["physical"] for j in js)                                 # a real reveal surface (plaster)
    m = measure(r, (250, 200))
    assert all("H20" not in " ".join(e["sources"]) for e in WC.site_edges(r["_arr"], site_at(r, (250, 200))))
    assert RULE["method"]["DOOR_PRESENT"] == {"path": "STOP_AT_OPENING", "across_opening": "NONE",
                                              "jamb_skirting": "NONE"} and m["components"]


# ------------------------------------------------------------------------------- doorless openings (§38)
def closure_passage():
    p = box() + wall(lower=((0, 300), (300, 600))) + \
        [H.seg(20, 720, 400, 1000, 400), H.seg(21, 720, 420, 1000, 420), H.seg(91, 720, 400, 720, 420, layer="DIM")]
    return room(p, [("HALL", 500, 100), ("LOBBY", 500, 700)])


def capped_passage():
    p = box() + [H.seg(10, 0, 400, 880, 400), H.seg(11, 0, 420, 880, 420), H.seg(12, 880, 400, 880, 420)]
    return room(p, [("A", 500, 100), ("B", 500, 700)])


def test_a_doorless_passage_has_no_skirting_across_and_both_physical_jambs():
    r = closure_passage()
    js = jambs_of(r)
    sides = sorted(j["side"] for j in js if j["kind"] == WC.DOORLESS_JAMB)
    assert sides == ["LEFT", "RIGHT"] and all(j["physical"] for j in js if j["kind"] == WC.DOORLESS_JAMB)
    m = measure(r, (500, 100))
    assert abs(m["components"][WC.PHYSICAL_OPENING_JAMB] - 40.0) < 1e-9          # two 20-unit jambs, once each
    assert WC.TOPOLOGY_CLOSURE not in m["components"]


def test_the_topology_closure_is_zero_but_the_real_jamb_behind_it_is_measured_from_the_band():
    r = closure_passage()
    m = measure(r, (500, 100))
    counted = [j for j in m["jambs_counted"] if j["counted"]]
    assert counted and all(j["source"].startswith("BANDEND|") for j in counted)
    assert all(not s.startswith("TCLOSURE|") for j in counted for s in [j["source"]])


def test_a_capped_doorless_passage_counts_its_cap_and_not_the_continuous_far_face():
    r = capped_passage()
    js = [j for j in jambs_of(r) if j["kind"] == WC.DOORLESS_JAMB]
    assert {j["side"]: j["physical"] for j in js} == {"LEFT": True, "RIGHT": False}
    assert [j for j in js if j["side"] == "RIGHT"][0]["end_kind"] == "CONTINUOUS_WALL_FACE"
    m = measure(r, (500, 100))
    assert abs(m["components"][WC.PHYSICAL_OPENING_JAMB] - 20.0) < 1e-9


def test_full_height_and_low_head_passages_use_the_same_floor_jamb_rule():
    a, b = measure(closure_passage(), (500, 100)), measure(capped_passage(), (500, 100))
    assert a["components"][WC.PHYSICAL_OPENING_JAMB] > 0 and b["components"][WC.PHYSICAL_OPENING_JAMB] > 0
    assert RULE["method"]["DOORLESS_OPENING"]["real_floor_side_jambs"] == "INCLUDED"


def test_a_full_wall_tile_side_has_no_skirting_even_at_a_doorless_jamb():
    m = measure(closure_passage(), (500, 100), full_wall_tile=True)
    assert m["state"] == WC.NO_SKIRTING and m["length"] == 0.0


def test_a_method_without_doorless_jambs_excludes_them_and_the_v3_policy_is_versioned():
    m = measure(closure_passage(), (500, 100), WC.SkirtingMethodV3("T", 1, {}, doorless_jambs=WC.EXCLUDED))
    assert WC.PHYSICAL_OPENING_JAMB not in m["components"] and m["excluded"]["DOORLESS_JAMB_NOT_COUNTED"] == 40.0
    rec = WC.policy_record_v3()
    assert rec["policy_id"] == "WALL_CONTACT_PATH_POLICY_V3" and rec["extends"] == "WALL_CONTACT_PATH_POLICY_V2"
