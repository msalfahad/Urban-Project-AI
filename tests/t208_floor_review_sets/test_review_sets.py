"""T-208: review-set binding on a NON-Alsenan hand fixture (villa T208-V) with adverse cases.

Villa T208-V (hand truth, m):
- bed room B 4.00 x 3.50 = 14.000 m2 porcelain (released line), bath W 2.00 x 1.80 = 3.600 m2 wet tile (released line);
- lobby L, unlabelled, two wash basins only, opening 0.90 wide in a 0.20 wall: WET_SCOPE floor 2.40 x 1.50 = 3.600 m2
  wet tile + doorway strip 0.90 x 0.20 = 0.180 m2 porcelain; DRY_SCOPE 3.780 m2 porcelain. Owner Q-06 A -> WET.
  Key FLOOR.INTERNAL (porcelain + wet tile) = 14.000 + 3.600 + 3.600 + 0.180 = 21.380 m2.
Adverse: a basin space with an attached doorless cell (D-C3), a basin + WC space, a space with no fixture (unclassified),
a zone cut by drawn lines, a set that is not mutually exclusive, a missing room record, a labelled pantry with a basin,
a WET scenario absent from the set, a non-floor set kind; every one HELD (never dry, never 0) or ignored."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t208"))

import review_sets as RS                                               # noqa: E402

KEY = ("FIN.FLOOR.PORCELAIN [m2]", "FIN.FLOOR.WET_TILE [m2]")


def room(rid, fixtures=("BASIN", "BASIN"), issue="WET_CLASSIFICATION_REVIEW (UP-WET-002): basin only; "
         "UNLABELLED_SPACE: no room word", cls="UNLABELLED", codes=(), attached=(), conflict=None, closures=0):
    return {"room_id": rid, "floor": "GF", "class": cls, "codes": list(codes), "attached_cells": list(attached),
            "door_closures": closures,
            "fixture_conflict": conflict, "issue": issue,
            "evidence": {"fixtures": [{"fixture": f} for f in fixtures]}}


def rset(subject, wet=None, dry=None, exclusive=True, kind="REVIEW_CLASSIFICATION", scenarios=("WET_SCOPE", "DRY_SCOPE")):
    by = {}
    if wet is not None:
        by["WET_SCOPE"] = wet
    if dry is not None:
        by["DRY_SCOPE"] = dry
    return {"set_id": f"{kind}:GF:{subject}", "subject": subject, "kind": kind, "mutually_exclusive": exclusive,
            "scenarios": list(scenarios), "by_scenario": by}


LOBBY_WET = {"FIN.FLOOR.WET_TILE [m2]": 2.40 * 1.50, "FIN.FLOOR.PORCELAIN [m2]": 0.90 * 0.20,
             "FIN.WP.FLOOR [m2]": 3.60}
LOBBY_DRY = {"FIN.FLOOR.PORCELAIN [m2]": 3.78, "FIN.SKIRTING [lm]": 7.5}


def lines():
    return [{"item_code": "FIN.FLOOR.PORCELAIN", "evidence_state": "SOURCE_DERIVED", "measured_net": 4.00 * 3.50},
            {"item_code": "FIN.FLOOR.WET_TILE", "evidence_state": "SOURCE_DERIVED", "measured_net": 2.00 * 1.80},
            {"item_code": "FIN.SKIRTING", "evidence_state": "SOURCE_DERIVED", "measured_net": 15.0}]


def test_basin_only_lobby_is_wet_by_q06():
    b = RS.bind_set(rset("L", LOBBY_WET, LOBBY_DRY), room("L"))
    assert b["status"] == RS.ASSUMED and b["scenario"] == "WET_SCOPE" and b["rule_id"] == "Q-06 A"
    assert "Q-06" in b["source"] and abs(b["quantities"]["FIN.FLOOR.WET_TILE [m2]"] - 3.60) < 1e-9


def test_floor_line_hand_total_21_38():
    rr = {"categories": {"CONDITIONAL": {"scenario_sets": [rset("L", LOBBY_WET, LOBBY_DRY)]}}}
    doc = RS.bind_run(rr, [room("L")])
    fl = RS.floor_line(lines(), doc, KEY)
    assert fl["released_m2"] == 17.6 and fl["assumed_owner_approved_m2"] == 3.78 and fl["total_m2"] == 21.38
    rows = RS.key_rows(doc, "FLOOR.INTERNAL", KEY)
    assert rows == [{"id": "COND:REVIEW_CLASSIFICATION:GF:L:FLOOR.INTERNAL", "key": "FLOOR.INTERNAL", "qty": 3.78,
                     "status": RS.ASSUMED, "rule_id": "Q-06 A", "items_absent_in_scenario": [],
                     "surface": "COND:REVIEW_CLASSIFICATION:GF:L"}]


def test_closure_strip_counted_once_in_its_threshold_line():
    """lobby with a doorless opening closed by a closure strip (door_closures 1): the WET scenario's porcelain 0.18 is
    that strip, already its own threshold line: key = wet tile 3.60 only; total 14.00 + 3.60 + 3.60 = 21.20."""
    rr = {"categories": {"CONDITIONAL": {"scenario_sets": [rset("L", LOBBY_WET, LOBBY_DRY)]}}}
    doc = RS.bind_run(rr, [room("L", closures=1)])
    b = doc["bindings"][0]
    assert abs(b["closure_strip"]["m2"] - 0.18) < 1e-9 and "FIN.FLOOR.PORCELAIN [m2]" not in b["quantities"]
    fl = RS.floor_line(lines(), doc, KEY)
    assert fl["total_m2"] == 21.2 and fl["assumed_by_item"]["FIN.FLOOR.PORCELAIN [m2]"] == 0.0
    rows = RS.key_rows(doc, "FLOOR.INTERNAL", KEY)
    assert rows[0]["qty"] == 3.6 and rows[0]["items_absent_in_scenario"] == ["FIN.FLOOR.PORCELAIN [m2]"]
    # a DRY binding would keep its porcelain (no closure moved): never applied to a dry scenario
    assert RS.bind_set(rset("L", LOBBY_WET, LOBBY_DRY), room("L", closures=0))["closure_strip"] is None


def test_arabic_hand_wash_code_allowed_but_other_label_held():
    assert RS.bind_set(rset("H", LOBBY_WET, LOBBY_DRY), room("H", codes=("HAND_WASH",)))["status"] == RS.ASSUMED
    b = RS.bind_set(rset("P", LOBBY_WET, LOBBY_DRY), room("P", codes=("PANTRY",), cls="ROOM"))
    assert b["status"] == RS.HELD and b["quantities"] is None


def test_adverse_cases_are_held_never_dry():
    cases = {
        "D-C3": (rset("C", LOBBY_WET, LOBBY_DRY), room("C", attached=("SITE-x",)), "doorless cell"),
        "WC": (rset("W", LOBBY_WET, LOBBY_DRY), room("W", fixtures=("BASIN", "WC")), "non-basin fixture"),
        "NONE": (rset("N", LOBBY_WET, LOBBY_DRY), room("N", fixtures=()), "no answered owner rule"),
        "ZONE": (rset("Z", LOBBY_WET, LOBBY_DRY),
                 room("Z", issue="WET_CLASSIFICATION_REVIEW (UP-WET-002): x; ZONE_FROM_DRAWN_LINES: part of an open "
                                 "space"), "drawn lines"),
        "OPEN": (rset("O", LOBBY_WET, LOBBY_DRY, exclusive=False), room("O"), "not mutually exclusive"),
        "MISSING": (rset("M", LOBBY_WET, LOBBY_DRY), None, "missing"),
        "CONFLICT": (rset("F", LOBBY_WET, LOBBY_DRY), room("F", conflict="two readings"), "fixture conflict"),
        "NO_WET": (rset("X", None, LOBBY_DRY, scenarios=("DRY_SCOPE",)), room("X"), "no WET_SCOPE"),
    }
    for name, (s, r, why) in cases.items():
        b = RS.bind_set(s, r)
        assert b["status"] == RS.HELD, name
        assert b["scenario"] is None and b["quantities"] is None, name
        assert why in b["reason"], (name, b["reason"])


def test_held_set_makes_the_line_unknown_not_partial():
    rr = {"categories": {"CONDITIONAL": {"scenario_sets": [rset("L", LOBBY_WET, LOBBY_DRY),
                                                           rset("N", LOBBY_WET, LOBBY_DRY)]}}}
    doc = RS.bind_run(rr, [room("L"), room("N", fixtures=())])
    fl = RS.floor_line(lines(), doc, KEY)
    assert fl["total_m2"] is None and fl["held_sets"] == ["REVIEW_CLASSIFICATION:GF:N"]
    rows = {r["id"].split(":")[3]: r for r in RS.key_rows(doc, "FLOOR.INTERNAL", KEY)}
    assert rows["N"]["status"] == RS.HELD and rows["N"]["qty"] is None and rows["L"]["qty"] == 3.78


def test_held_line_also_blocks_the_total():
    rr = {"categories": {"CONDITIONAL": {"scenario_sets": [rset("L", LOBBY_WET, LOBBY_DRY)]}}}
    doc = RS.bind_run(rr, [room("L")])
    ls = lines() + [{"item_code": "FIN.FLOOR.PORCELAIN", "evidence_state": "BLOCKED_RFI", "measured_net": None}]
    fl = RS.floor_line(ls, doc, KEY)
    assert fl["held_lines"] == 1 and fl["total_m2"] is None


def test_confirmation_lifts_only_the_boundary_condition():
    zone = room("Z", issue="WET_CLASSIFICATION_REVIEW (UP-WET-002): x; ZONE_FROM_DRAWN_LINES: part of an open space")
    conf = {"Z": {"condition": "ZONE_FROM_DRAWN_LINES", "checked": "opening line on the wall face", "source": "plan"}}
    b = RS.bind_set(rset("Z", LOBBY_WET, LOBBY_DRY), zone, confirmations=conf)
    assert b["status"] == RS.ASSUMED and b["boundary_confirmation"] == conf["Z"]
    # a confirmation never makes a WC space a basin-only space
    wc = room("Z", fixtures=("BASIN", "WC"))
    assert RS.bind_set(rset("Z", LOBBY_WET, LOBBY_DRY), wc, confirmations=conf)["status"] == RS.HELD


def test_scenario_without_a_key_item_lists_it():
    wet = {"FIN.FLOOR.WET_TILE [m2]": 3.60}
    rr = {"categories": {"CONDITIONAL": {"scenario_sets": [rset("L", wet, LOBBY_DRY)]}}}
    rows = RS.key_rows(RS.bind_run(rr, [room("L")]), "FLOOR.INTERNAL", KEY)
    assert rows[0]["qty"] == 3.6 and rows[0]["items_absent_in_scenario"] == ["FIN.FLOOR.PORCELAIN [m2]"]


def test_non_floor_set_kinds_are_ignored():
    rr = {"categories": {"CONDITIONAL": {"scenario_sets": [
        {"set_id": "DOOR_OWNER_MINIMUM", "kind": "DOOR_OWNER_MINIMUM", "mutually_exclusive": True,
         "scenarios": ["A", "B"], "by_scenario": {"A": {"doors": 3}, "B": {"doors": 2}}}]}}}
    doc = RS.bind_run(rr, [])
    assert doc["bindings"] == [] and doc["ignored_sets"] == [{"set_id": "DOOR_OWNER_MINIMUM",
                                                               "kind": "DOOR_OWNER_MINIMUM"}]
    assert RS.floor_line(lines(), doc, KEY)["total_m2"] == 17.6


def test_issue_codes_parsing():
    assert RS._issue_codes("WET_CLASSIFICATION_REVIEW (UP-WET-002): a; UNLABELLED_SPACE: b; ZONE_FROM_DRAWN_LINES: c"
                           ) == ["WET_CLASSIFICATION_REVIEW", "UNLABELLED_SPACE", "ZONE_FROM_DRAWN_LINES"]
    assert RS._issue_codes(None) == []
