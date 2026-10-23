"""T-218: wet class of the floor item, the wet sub-lines and doorway-strip classification on a NON-Alsenan hand
fixture (villa T218-V) with adverse cases.

Villa T218-V (hand truth, m):
- kitchen K, labelled KITCHEN, lexicon kind SERVICE, owner scope WET (UP-WET-001): 3.60 x 3.00 = 10.800 m2; boundary
  2 x (3.60 + 3.00) = 13.20 lm = wall 11.10 + window wall below a 1.00 m sill 1.20 + door 0.90 (wall 0.20 thick).
  Released-style run floors it FIN.FLOOR.PORCELAIN 10.800 (dry item) -> must be FIN.FLOOR.WET_TILE 10.800 (total
  unchanged); membrane floor 10.800; upturn walls only 13.20 - 0.90 = 12.30 lm x 0.20 = 2.460 m2; doorway piece
  0.90 x 0.20 = 0.180; transition 0 .. 0.90 x 0.20 = 0 .. 0.180 HELD; marble threshold 0.180; bed 4 .. 6 cm =
  0.432 .. 0.648 m3 (dry 3 .. 4 cm = 0.324 .. 0.432), cement 8 bags / m3 = 3.456 .. 5.184, sand 1.10 m3 / m3 =
  0.4752 .. 0.7128, adhesive 10.80 / 5 = 2.16 bags.
- bed room B (dry) 4.00 x 3.50 with door 0.90 in a 0.15 wall to the hall (dry): porcelain strip 0.135.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t218"))

import wet_class_strips as W                                           # noqa: E402


def kitchen(**kw):
    r = {"room_id": "K", "codes": ["KITCHEN"], "kind": "SERVICE",
         "finish_scope": {"scope": "WET", "rule": "UP-WET-001"}}
    r.update(kw)
    return r


def k_geom(**kw):
    g = {"floor_m2": 10.80, "rule": "UP-WET-001",
         "runs_lm": {"wall": 11.10, "column": 0.0, "window_threshold": 1.20, "door": 0.90, "glazing_edge": 0.0},
         "doors": [{"id": "D1", "width_m": 0.90, "wall_depth_m": 0.20}],
         "windows": [{"id": "W1", "width_m": 1.20, "sill_established": True}]}
    g.update(kw)
    return g


# ---------------------------------------------------------------------------------------------- normal case
def test_kitchen_floor_item_follows_the_owner_scope_not_the_lexicon():
    fi = W.floor_item(kitchen())
    assert fi["item_code"] == "FIN.FLOOR.WET_TILE" and fi["status"] == W.AOA
    assert fi["consistent"] is False and "owner scope governs" in fi["why"]


def test_released_style_kitchen_lines_are_flagged():
    lines = [{"item_code": "FIN.FLOOR.PORCELAIN", "qty": 10.80}, {"item_code": "FIN.WP.FLOOR", "qty": 10.80},
             {"item_code": "FIN.SKIRTING", "qty": None}, {"item_code": "FIN.PAINT", "qty": None}]
    f = W.check_room_lines(kitchen(), lines)
    assert f == [{"item": "FIN.FLOOR.PORCELAIN", "finding": "WET_ROOM_FLOORED_DRY", "qty": 10.80,
                  "should_be": "FIN.FLOOR.WET_TILE"}]


def test_wet_sublines_by_hand():
    L = W.wet_sublines(k_geom())["lines"]
    assert L["FIN.FLOOR.WET_TILE"]["qty"] == 10.80                 # floor total unchanged by the class
    assert L["FIN.WP.FLOOR"]["qty"] == 10.80
    assert L["FIN.WP.WALL_UPTURN_LM"]["qty"] == 12.30 and L["FIN.WP.WALL_UPTURN"]["qty"] == 2.46
    assert L["FIN.WP.WALL_UPTURN"]["status"] == W.DC
    assert L["FIN.WP.DOORWAY"]["qty"] == 0.18
    assert L["FIN.WP.DOORWAY_TRANSITION"]["qty"] is None and L["FIN.WP.DOORWAY_TRANSITION"]["range"] == [0.0, 0.18]
    assert L["FIN.MARBLE.THRESHOLD"]["qty"] == 0.18
    assert L["BED_MORTAR_M3"]["range"] == [0.432, 0.648]
    assert L["CEMENT_BAGS"]["range"] == [3.456, 5.184]
    assert L["SAND_M3"]["range"] == [0.4752, 0.7128]
    assert L["ADHESIVE_BAGS"]["qty"] == 2.16
    assert W.dry_bed(10.80)["BED_MORTAR_M3"] == [0.324, 0.432]


def test_dry_room_strip_and_lines():
    c = W.classify_strip({"opening_id": "D2", "opening_kind": "DOOR", "sides": ["DRY", "DRY"], "width_m": 0.90,
                          "depth_m": 0.15})
    assert c["item_code"].startswith("FIN.FLOOR.PORCELAIN") and c["qty_m2"] == 0.135 and c["status"] == W.DC
    bed = {"room_id": "B", "codes": ["MASTER_BEDROOM"], "kind": "DRY", "finish_scope": {"scope": "DRY",
                                                                                        "rule": "UP-SKIRT-001"}}
    assert W.check_room_lines(bed, [{"item_code": "FIN.FLOOR.PORCELAIN", "qty": 14.0}]) == []


# ------------------------------------------------------------------------------------------- adverse cases
def test_wet_class_without_rule_id_is_refused():
    with pytest.raises(W.Refused):
        W.floor_item(kitchen(finish_scope={"scope": "WET", "rule": None}))
    with pytest.raises(W.Refused):
        W.wet_sublines(k_geom(rule="SOME-GUESS"))


def test_wet_rule_cited_on_a_room_without_a_wet_code_is_refused():
    with pytest.raises(W.Refused):
        W.floor_item(kitchen(codes=["MASTER_BEDROOM"]))


def test_unknown_scope_is_held_never_dry():
    fi = W.floor_item(kitchen(finish_scope={"scope": None, "rule": None}))
    assert fi["item_code"] is None and fi["status"] == W.HELD


def test_window_without_sill_holds_the_upturn_never_zero():
    g = k_geom(windows=[{"id": "W1", "width_m": 1.20, "sill_established": False}])
    L = W.wet_sublines(g)["lines"]
    assert L["FIN.WP.WALL_UPTURN"]["status"] == W.HELD
    assert L["FIN.WP.WALL_UPTURN_LM"]["range_if_held"] == [11.10, 12.30]


def test_missing_door_depth_holds_the_doorway_lines():
    L = W.wet_sublines(k_geom(doors=[{"id": "D1", "width_m": 0.90, "wall_depth_m": None}]))["lines"]
    assert L["FIN.WP.DOORWAY"]["qty"] is None and L["FIN.WP.DOORWAY"]["status"] == W.HELD
    assert L["FIN.MARBLE.THRESHOLD"]["qty"] is None


def test_missing_floor_holds_every_area_line():
    L = W.wet_sublines(k_geom(floor_m2=None))["lines"]
    assert L["FIN.FLOOR.WET_TILE"]["qty"] is None and L["FIN.FLOOR.WET_TILE"]["status"] == W.HELD
    assert L["BED_MORTAR_M3"]["qty"] is None


def test_millimetres_are_refused():
    with pytest.raises(W.Refused):
        W.wet_sublines(k_geom(floor_m2=10_800_000.0))
    with pytest.raises(W.Refused):
        W.wet_sublines(k_geom(runs_lm={"wall": 11100.0, "door": 900.0}))
    with pytest.raises(W.Refused):
        W.classify_strip({"opening_kind": "DOOR", "sides": ["DRY", "DRY"], "width_m": 900.0, "depth_m": 150.0})


@pytest.mark.parametrize("sides,kind,item,status", [
    (["DRY", "WET"], "DOOR", "FIN.MARBLE.THRESHOLD", W.DC),
    (["WET", "EXTERIOR"], "DOOR", "FIN.MARBLE.THRESHOLD", W.DC),     # wet-area doorway to the outside
    (["DRY", "LIFT_SHAFT"], "PASSAGE", "ARCH.THRESHOLD (lift landing)", W.HELD),
    (["DRY", "EXTERIOR"], "DOOR", "ARCH.THRESHOLD (exterior sill)", W.HELD),
    (["DRY", "UNKNOWN"], "PASSAGE", None, W.HELD),
    (["DRY", "WET"], "PASSAGE", "ARCH.THRESHOLD", W.HELD),
])
def test_strip_classification(sides, kind, item, status):
    c = W.classify_strip({"opening_id": "X", "opening_kind": kind, "sides": sides, "width_m": 1.0, "depth_m": 0.2})
    assert c["item_code"] == item and c["status"] == status
    if status == W.HELD:
        assert c["qty_m2"] is None and c["measured_m2"] == 0.2      # measured, held, never 0


def test_strip_with_bad_sides_is_refused():
    with pytest.raises(W.Refused):
        W.classify_strip({"opening_kind": "DOOR", "sides": ["DRY"], "width_m": 1.0, "depth_m": 0.2})
    with pytest.raises(W.Refused):
        W.classify_strip({"opening_kind": "DOOR", "sides": ["DRY", "GARDEN"], "width_m": 1.0, "depth_m": 0.2})


def test_one_strip_two_lines_is_refused():
    lines = [{"line_id": "a", "opening_id": "1F:D2", "item_code": "FIN.FLOOR.PORCELAIN", "covers_m2": 0.135},
             {"line_id": "b", "opening_id": "1F:D2", "item_code": "ARCH.THRESHOLD", "covers_m2": 0.166}]
    res = W.one_strip_one_line(lines)
    assert res["duplicates"][0]["opening_id"] == "1F:D2" and res["duplicates"][0]["overlap_m2"] == 0.135
    with pytest.raises(W.Refused):
        W.assert_one_strip_one_line(lines)


def test_declared_residue_and_floor_qualified_ids_pass():
    lines = [{"line_id": "a", "opening_id": "1F:D2", "item_code": "FIN.FLOOR.PORCELAIN", "covers_m2": 0.135},
             {"line_id": "b", "opening_id": "1F:D2", "item_code": "ARCH.THRESHOLD", "covers_m2": 0.031,
              "residue": True},
             {"line_id": "c", "opening_id": "2F:D2", "item_code": "FIN.MARBLE.THRESHOLD", "covers_m2": 0.12}]
    assert W.assert_one_strip_one_line(lines)["duplicates"] == []


def test_decompose_reports_a_residual_never_hides_it():
    d = W.decompose(10.0, 9.0, [{"id": "scope", "m2": 0.6, "kind": "SCOPE"}])
    assert d["residual_m2"] == 0.4 and d["closed"] is False
    d = W.decompose(10.0, 9.0, [{"id": "scope", "m2": 0.6, "kind": "SCOPE"}, {"id": "x", "m2": 0.4,
                                                                                "kind": "UNRESOLVED"}])
    assert d["closed"] is True
