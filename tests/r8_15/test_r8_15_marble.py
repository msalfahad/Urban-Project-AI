"""R8.15 §34: marble thresholds - the Urban wet / service rule and the explicit project fact."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.source import door_transition as DT, marble_thresholds as MT, owner_facts as OF, trade_strips as TS

ROOT = Path(__file__).resolve().parents[2]
RULE_REC = json.loads((ROOT / "data/registry/URBAN_OWNER_METHOD_RULES.json").read_text())["rules"][0]
RULE = MT.rule_from_record(RULE_REC)
ENTR = next(f for f in json.loads((ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json").read_text())["facts"]
            if f["fact_id"] == "QORTUBA-NEW-MAIN-ENTRANCE-MARBLE-OWNER-001")
EPS = 0.1
A = ((495.0, 150.0), (495.0, 250.0))                     # face closure A (10 native = 100 mm at 10 mm / unit)
B = ((505.0, 150.0), (505.0, 250.0))
AREA, PER = 100.0 * 10.0, 2 * (100.0 + 10.0)
DRY = {"site": "S-DRY", "class": "DRY_INTERNAL_ROOM", "treatment": "PORCELAIN_DRY_FLOOR"}
WET = {"site": "S-WET", "class": "WET_SERVICE_ROOM", "treatment": "CERAMIC_WET_FLOOR"}


def plane():
    return DT.transition_plane(A, B, (495.0, 150.0), eps_r=EPS, owner_centred="FACT@v1")


def marble_alloc(types, wet=WET):
    ev = MT.choose(None, MT.rule_evidence(RULE, types))
    return ev, DT.allocate(AREA, PER, plane(), wet, DRY, eps_r=EPS, marble=ev)


@pytest.mark.parametrize("room", ["BATHROOM", "KITCHEN", "WASHING_LAUNDRY_ROOM", "IRONING_ROOM"])
def test_a_wet_or_service_doorway_gets_a_full_marble_threshold(room):
    ev, a = marble_alloc({"A": room, "B": "BEDROOM"})
    assert ev["kind"] == MT.RULE and ev["ref"] == "URBAN-WET-SERVICE-MARBLE-THRESHOLD@v1"
    assert a["state"] == DT.MARBLE and len(a["regions"]) == 1 and a["regions"][0]["area"] == AREA


def test_a_dry_dry_door_gets_no_urban_marble():
    ev, a = marble_alloc({"A": "BEDROOM", "B": "LIVING_ROOM"}, wet=dict(DRY, site="S2"))
    assert ev is None and a["state"] == DT.CONTINUOUS
    assert MT.rule_evidence(RULE, {"A": "BEDROOM", "B": "LIVING_ROOM"})["state"] == MT.NOT_APPLICABLE


def test_the_main_entrance_is_marble_only_through_the_explicit_project_fact():
    outside = {"A": "HALL_LOBBY", "B": None}                              # the landing has no apartment room type
    assert MT.rule_evidence(RULE, outside)["state"] == MT.TYPE_UNRESOLVED
    assert MT.choose(None, MT.rule_evidence(RULE, outside)) is None
    f = OF.from_record(ENTR)
    ev = MT.choose(MT.explicit_evidence(f.ref, f.statement), MT.rule_evidence(RULE, outside))
    assert ev["kind"] == MT.EXPLICIT and ev["rise_mm"] == MT.NOT_STATED and ev["function"] is None
    a = DT.allocate(AREA, PER, plane(), DRY, {"site": "S-OUT", "treatment": "OUTSIDE_MEASURED_UNIT"}, eps_r=EPS,
                    marble=ev)
    rec = MT.record("T-ENTR", a, ev, unit_to_mm=10.0)
    assert rec["state"] == MT.COMPUTED and rec["vertical_rise_mm"] == MT.NOT_STATED and not rec["water_containment"]


def test_20_mm_is_a_vertical_rise_and_never_a_horizontal_depth():
    assert RULE.rise_mm == 20 and RULE_REC["measurement"]["rise_is"].startswith("VERTICAL")
    ev, a = marble_alloc({"A": "BATHROOM", "B": "BEDROOM"})
    rec = MT.record("T1", a, ev, unit_to_mm=10.0)
    assert rec["vertical_rise_mm"] == 20 and rec["depth_mm"] == 100.0 and rec["depth_mm"] != 20
    assert rec["clear_width_mm"] == 1000.0 and rec["water_containment"] is True
    assert "20 mm as a horizontal width or depth" in RULE.never


def test_the_horizontal_footprint_comes_from_the_doorway_geometry():
    ev, a = marble_alloc({"A": "BATHROOM", "B": "BEDROOM"})
    rec = MT.record("T1", a, ev, unit_to_mm=10.0)
    assert rec["plan_area_m2"] == rec["width_x_depth_m2"] == round(1.0 * 0.1, 6) and rec["length_lm"] == 1.0
    bad = DT.allocate(AREA * 1.5, PER, plane(), WET, DRY, eps_r=EPS, marble=ev)       # not the face-pair strip
    assert bad["state"] == DT.UNRESOLVED_GEOMETRY
    assert MT.record("T2", bad, ev, unit_to_mm=10.0)["state"] == MT.BLOCKED_GEOMETRY


def test_wet_tile_and_dry_porcelain_stop_at_the_marble_and_it_is_counted_once():
    ev, a = marble_alloc({"A": "BATHROOM", "B": "BEDROOM"})
    assert DT.contribution(a, "CERAMIC_WET_FLOOR") == 0 and DT.contribution(a, "PORCELAIN_DRY_FLOOR") == 0
    assert DT.contribution(a, DT.MARBLE) == AREA
    strip = {"id": "TH", "kind": "THRESHOLD", "location": TS.SEPARATE_SITE, "sides": ["S-WET", "S-DRY"],
             "site": "TH", "area_m2": AREA}
    tr = {"S-WET": "CERAMIC_WET_FLOOR", "S-DRY": "PORCELAIN_DRY_FLOOR"}
    wet = TS.audit_v2(strip, {"S-WET"}, tr, "CERAMIC_WET_FLOOR", trade="FLOOR_FINISH", allocation=a)
    dry = TS.audit_v2(strip, {"S-DRY"}, tr, "PORCELAIN_DRY_FLOOR", trade="FLOOR_FINISH", allocation=a)
    assert wet["state"] == dry["state"] == DT.MARBLE and wet["contribution_m2"] == dry["contribution_m2"] == 0
    q = MT.quantities([MT.record("T1", a, ev, unit_to_mm=10.0)])
    assert q["count"] == 1 and q["MARBLE_THRESHOLD_PLAN_AREA_M2"] == 0.1


def test_no_half_tile_contribution_where_marble_applies():
    ev, a = marble_alloc({"A": "BATHROOM", "B": "BEDROOM"})
    split = DT.allocate(AREA, PER, plane(), WET, DRY, eps_r=EPS)                      # what R8.14 would do
    assert split["state"] == DT.SPLIT and DT.contribution(split, "CERAMIC_WET_FLOOR") == AREA / 2
    assert [r["treatment"] for r in a["regions"]] == [DT.MARBLE]


def test_the_rule_does_not_transfer_to_an_unrelated_or_unscoped_room_type():
    for types in ({"A": "BEDROOM", "B": "HALL_LOBBY"}, {"A": "PANTRY", "B": "HALL_LOBBY"},
                  {"A": "WET_SERVICE_ROOM", "B": "BEDROOM"}):                         # a CLASS is not a room type
        assert MT.rule_evidence(RULE, types)["state"] == MT.NOT_APPLICABLE
    assert "PAINTRY / pantry (not named by the owner)" in RULE_REC["not_applicable_to"]
    assert set(RULE.applies_to) == {"BATHROOM", "KITCHEN", "WASHING_LAUNDRY_ROOM", "IRONING_ROOM"}
    assert {"a waterproofing extent change", "a slope", "a drainage", "a material rate or price"} <= set(RULE.never)
