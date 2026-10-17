"""M9 S1 rule store and material specifications: the owner decisions of 1.5.0 replace their 1.4.0 records by rule_id,
an old rule never overrides a newer decision, proposals stay out unless asked for, every copy / export matches its
source, and a material value is never guessed (the stricter lap wins, with its source)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.source import material_spec as MS
from engine.source import rule_store as RS

ROOT = Path(__file__).resolve().parents[2]


def test_the_store_matches_its_manifest_and_sources():
    assert RS.check() == []
    assert (ROOT / "rules/owner_library/URBAN_PROJECTS_RULE_LIBRARY_1.4.0.json").read_bytes() == \
        (ROOT / "data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json").read_bytes()


def test_owner_decisions_replace_the_old_records():
    old, new = RS.rule("UP-WP-002", "1.4.0"), RS.rule("UP-WP-002", "1.5.0")
    assert (old["version"], new["version"]) == ("1.0.0", "2.0.0")
    assert new["value"] == 0.2 and new["status"] == "OWNER_APPROVED"
    assert "a door-width deduction" in new["never"]
    assert RS.rule("UP-STAIR-012")["version"] == "2.0.0" and RS.rule("UP-STAIR-012")["example"]["L_lm"] == 4.472
    assert RS.rule("UP-GEN-003")["value"]["WATERPROOFING_UPTURN"] == "NO_DEDUCTION"
    sup = {s["rule_id"]: (s["from"], s["to"]) for s in RS.rule_set()["superseded"]}
    assert sup == {"UP-STAIR-012": ("1.0.0", "2.0.0"), "UP-WP-002": ("1.0.0", "2.0.0"),
                   "UP-WP-003": ("1.0.0", "1.1.0"), "UP-GEN-003": ("1.0.0", "1.1.0")}


def test_no_rule_of_the_latest_set_carries_an_older_superseded_version():
    rs = RS.rule_set()
    for s in rs["superseded"]:
        assert rs["rules"][s["rule_id"]]["version"] == s["to"]
    with pytest.raises(KeyError):
        RS.rule("UP-STAIR-013", "1.4.0")                      # a new rule exists only from 1.5.0


def test_proposals_stay_out_unless_requested():
    assert "UP-STAIR-014" not in RS.rule_set()["rules"]
    assert RS.rule("UP-WP-004")["version"] == "1.0.0"         # the 1.4.0 record; v1.1.0 is only PROPOSED
    p = RS.rule_set(include_proposed=True)
    assert p["rules"]["UP-WP-004"]["version"] == "1.1.0" and "UP-STAIR-014" in p["rules"]
    assert p["digest"] != RS.rule_set()["digest"]


def test_rule_refs_name_version_set_and_digest():
    ref = RS.rule_ref("UP-WP-005")
    assert ref["version"] == "1.0.0" and ref["rule_set"] == "1.5.0" and len(ref["rule_set_digest"]) == 64
    with pytest.raises(RS.RuleStoreError):
        RS.rule_set("9.9.9")


def test_the_store_cannot_be_changed_through_a_returned_copy():
    r = RS.rule("UP-WP-002")
    r["value"] = 0.15
    assert RS.rule("UP-WP-002")["value"] == 0.2


def test_the_membrane_default_is_the_owner_roll():
    m = MS.membrane()
    assert (m["roll_width_m"], m["roll_length_m"], m["roll_area_m2"], m["min_side_lap_m"], m["min_end_lap_m"]) == \
        (1.0, 10.0, 10.0, 0.1, 0.1)
    assert m["upturn_rule"] == "UP-WP-002@2.0.0" and m["corner_treatment"] is None


def test_a_stricter_data_sheet_lap_wins_and_a_looser_one_does_not():
    m = MS.apply_data_sheet(MS.membrane(), {"side_lap_m": 0.15, "end_lap_m": 0.08, "source": "TDS test rev 1"})
    assert m["min_side_lap_m"] == 0.15 and m["lap_source"]["side"].startswith("DATA_SHEET")
    assert m["min_end_lap_m"] == 0.1 and m["lap_source"]["end"].startswith("OWNER_MINIMUM_GOVERNS")
    with pytest.raises(MS.SpecError):
        MS.apply_data_sheet(MS.membrane(), {"side_lap_m": 0.2})               # no source


def test_overrides_are_recorded_and_validated():
    m = MS.membrane(roll_length_m=20.0)
    assert m["roll_area_m2"] == 20.0 and m["overrides"] == {"roll_length_m": 20.0}
    with pytest.raises(MS.SpecError):
        MS.membrane(min_side_lap_m=1.0)                                       # a lap as wide as the roll
    with pytest.raises(MS.SpecError):
        MS.membrane(colour="black")


def test_tile_registry_holds_sizes_only_and_never_a_box():
    for sid, (L, W) in zip(MS.OWNER_TILE_SIZES, ((1.2, 0.6), (0.6, 0.6), (1.6, 0.8))):
        t = MS.tile(sid)
        assert (t["length_m"], t["width_m"]) == (L, W)
        assert t["pieces_per_box"] is None and t["box_area_m2"] is None and t["thickness_m"] is None
    c = MS.custom_tile(0.9, 0.9)
    assert c["spec_id"] == "TILE-CUSTOM-90x90" and c["authority"] == "CUSTOM_USER_INPUT"
    b = MS.with_packaging(MS.tile("TILE-60x60"), pieces_per_box=4, source="test")
    assert abs(b["box_area_m2"] - 1.44) < 1e-9
    with pytest.raises(MS.SpecError):
        MS.custom_tile(0.6, 0.6, pieces_per_box=4, box_area_m2=2.0)         # box area disagrees with 4 x 0.36


def test_the_skill_flat_percentages_are_reference_only():
    r = RS.rule("UP-CER-010")
    assert "never used" in r["note"]
    assert "a flat size-based waste percentage as the quantity" in r["never"]
    assert "a fixed waste percentage" in RS.rule("UP-WP-005")["never"]
