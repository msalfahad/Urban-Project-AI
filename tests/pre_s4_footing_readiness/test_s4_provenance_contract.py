"""S4 provenance contract (accurate_boq_rebar.validate_s4_part / summarise_s4) and the comparison version stamps
(comparison_scope.stamp / compare_stamped). Synthetic records only."""

from __future__ import annotations

import copy

import pytest

from engine.source import accurate_boq_rebar as AR
from engine.source import comparison_scope as CS

SHA = "a" * 64


def prov(**over):
    p = {"PROJECT_ID": "PRJ", "DRAWING_ID": "DRW.dxf", "DRAWING_SHA": SHA, "REVISION": "REV-A",
         "SHEET_REGION": "FOOTING SCHEDULE", "SOURCE_HANDLES": ["10:11+12"], "SOURCE_TEXT": "8 | 12",
         "FOOTING_OCCURRENCE_ID": "OCC-1", "FOOTING_MARK": "F1", "COMPONENT": "FOOTING_BOTTOM_SHORT",
         "RULE_ID": "S4-BOTTOM-STRAIGHT", "CONVENTION_ID": "COVER7-STRAIGHT", "MEASUREMENT_STATE": "SCHEDULE_DERIVED",
         "AUTHORITY_STATE": "SOURCE_EXPLICIT", "RELEASE_STATE": "VERIFIED",
         "FORMULA": "8 x (0.90 - 2 x 0.07) x 12^2/162", "INPUTS": {"count": 8, "dia_mm": 12, "L_m": 0.9},
         "ENGINE_COMMIT": "abc1234", "REGISTER_VERSION": "S4-R1", "CALCULATION_ROUND": "S4"}
    p.update(over)
    return p


def part(state="VERIFIED", kg=5.4, comp="FOOTING_BOTTOM_SHORT", **pv):
    p = {"part_id": "OCC-1:SHORT", "category": "FOUNDATIONS", "component": comp, "state": state, "kg": kg,
         "basis": ["SCHEDULE", "STRUCTURAL_DETAIL"]}
    p["provenance"] = prov(COMPONENT=comp, RELEASE_STATE=state, **pv)
    return p


def test_a_complete_part_passes():
    assert AR.validate_s4_part(part())["part_id"] == "OCC-1:SHORT"


@pytest.mark.parametrize("field", AR.S4_PROVENANCE_FIELDS)
def test_a_part_missing_any_mandatory_field_fails(field):
    p = part()
    del p["provenance"][field]
    with pytest.raises(AR.AccurateRebarError, match=field):
        AR.validate_s4_part(p)


@pytest.mark.parametrize("field", [f for f in AR.S4_PROVENANCE_FIELDS if f != "INPUTS"])
def test_an_empty_mandatory_field_fails(field):
    p = part()
    p["provenance"][field] = [] if field == "SOURCE_HANDLES" else ""
    with pytest.raises(AR.AccurateRebarError):
        AR.validate_s4_part(p)


def test_a_part_without_provenance_fails_and_summarise_s4_refuses_it():
    p = part()
    del p["provenance"]
    with pytest.raises(AR.AccurateRebarError, match="provenance"):
        AR.summarise_s4([p])


@pytest.mark.parametrize("over,msg", [({"DRAWING_SHA": "9f9d"}, "DRAWING_SHA"),
                                      ({"COMPONENT": "FOOTING_BOTTOM_LONG"}, "COMPONENT"),
                                      ({"RELEASE_STATE": "LOWER_BOUND"}, "RELEASE_STATE"),
                                      ({"MEASUREMENT_STATE": "GUESSED"}, "MEASUREMENT_STATE"),
                                      ({"AUTHORITY_STATE": "FREELANCER"}, "AUTHORITY_STATE"),
                                      ({"SOURCE_HANDLES": "10"}, "SOURCE_HANDLES"),
                                      ({"INPUTS": [8, 12]}, "INPUTS")])
def test_inconsistent_provenance_fails(over, msg):
    p = part()
    p["provenance"].update(over)
    with pytest.raises(AR.AccurateRebarError, match=msg):
        AR.validate_s4_part(p)


@pytest.mark.parametrize("auth", AR.NON_QUANTIFYING_AUTHORITIES)
@pytest.mark.parametrize("state,kg", [("VERIFIED", 5.0), ("LOWER_BOUND", 5.0), ("PROVISIONAL", 5.0),
                                      ("BLOCKED_MODELLED", 5.0)])
def test_pattern_hypothesis_unresolved_or_conflict_never_carries_a_quantity(auth, state, kg):
    p = part(state=state, kg=kg, AUTHORITY_STATE=auth,
             **({"LOW": 1.0, "BEST": 5.0, "HIGH": None, "UNQUANTIFIED_COMPONENTS": []} if state == "LOWER_BOUND"
                else {}))
    with pytest.raises(AR.AccurateRebarError, match="never carries a quantity"):
        AR.validate_s4_part(p)


def test_boxed_with_unresolved_authority_is_blocked_unquantified_with_a_reason():
    b = part(state="BLOCKED_UNQUANTIFIED", kg=None, comp="BOXED_REBAR", AUTHORITY_STATE="UNRESOLVED",
             MEASUREMENT_STATE="NOT_MEASURED", FORMULA="NONE (blocked)", INPUTS={}, SOURCE_TEXT="3+4")
    with pytest.raises(AR.AccurateRebarError, match="BLOCKING_REASON"):
        AR.validate_s4_part(copy.deepcopy(b))
    b["provenance"]["BLOCKING_REASON"] = "BOXED '3+4' semantics UNRESOLVED (source exhaustion)"
    assert AR.validate_s4_part(b)["kg"] is None


def test_unapproved_method_cannot_release():
    with pytest.raises(AR.AccurateRebarError, match="cannot release"):
        AR.validate_s4_part(part(AUTHORITY_STATE="UNAPPROVED_METHOD"))
    assert AR.validate_s4_part(part(state="PROVISIONAL", AUTHORITY_STATE="UNAPPROVED_METHOD"))


def test_lower_bound_states_its_bounds_and_the_missing_components():
    with pytest.raises(AR.AccurateRebarError, match="bounds"):
        AR.validate_s4_part(part(state="LOWER_BOUND"))
    ok = part(state="LOWER_BOUND", LOW=5.4, BEST=5.4, HIGH=None, UNQUANTIFIED_COMPONENTS=["BOXED_REBAR"])
    assert AR.validate_s4_part(ok)
    for bad in ({"LOW": 6.0, "BEST": 5.4, "HIGH": None, "UNQUANTIFIED_COMPONENTS": []},
                {"LOW": 5.4, "BEST": 5.4, "HIGH": 5.0, "UNQUANTIFIED_COMPONENTS": []},
                {"LOW": 5.4, "BEST": 5.4, "HIGH": None, "UNQUANTIFIED_COMPONENTS": ["BOXES"]},
                {"LOW": 5.4, "BEST": 5.4}):
        with pytest.raises(AR.AccurateRebarError):
            AR.validate_s4_part(part(state="LOWER_BOUND", **bad))


def test_summarise_s4_keeps_states_apart_and_never_finalises_with_a_blocked_boxed():
    a = part()
    b = part(state="BLOCKED_UNQUANTIFIED", kg=None, comp="BOXED_REBAR", AUTHORITY_STATE="UNRESOLVED",
             MEASUREMENT_STATE="NOT_MEASURED", FORMULA="NONE", INPUTS={}, BLOCKING_REASON="BOXED unresolved")
    b["part_id"] = "OCC-1:BOXED"
    s = AR.summarise_s4([a, b])
    f = s["categories"]["FOUNDATIONS"]
    assert f["verified_kg"] == 5.4 and f["blocked_unquantified_parts"] == 1
    assert f["official_status"] == AR.PARTIAL and s["project"]["final_rebar"] == AR.FINAL_REBAR_NOT_ESTABLISHED


def test_existing_non_s4_parts_are_unaffected():
    p = {"part_id": "x", "category": "COLUMNS", "component": "COLUMN_TIE", "state": "VERIFIED", "kg": 1.0,
         "basis": ["SCHEDULE"]}
    assert AR.summarise([p])["categories"]["COLUMNS"]["verified_kg"] == 1.0


# ------------------------------------------------------------------ version stamps
def st(**over):
    s = {"ENGINE_COMMIT": "aaa1111", "REGISTER_VERSION": "S4-R1", "DRAWING_SHA": SHA, "CALCULATION_ROUND": "S4"}
    s.update(over)
    return s


def test_stamp_requires_every_field():
    for f in CS.STAMP_FIELDS:
        bad = st()
        del bad[f]
        with pytest.raises(CS.ScopeError):
            CS.stamp(**bad)
    with pytest.raises(CS.ScopeError):
        CS.stamp(**st(EXTRA="x"))


def test_same_engine_state_compares_normally():
    r = CS.compare_stamped(10.0, 8.0, CS.DIRECT, stamp_a=st(), stamp_b=st())
    assert r["engine_relation"] == CS.SAME_ENGINE_STATE and r["difference"] == 2.0


@pytest.mark.parametrize("field", ["ENGINE_COMMIT", "REGISTER_VERSION", "CALCULATION_ROUND"])
def test_old_urban_vs_new_urban_is_refused_unless_declared(field):
    b = st(**{field: "other"})
    with pytest.raises(CS.ScopeError, match="different engine states"):
        CS.compare_stamped(10.0, 8.0, CS.DIRECT, stamp_a=st(), stamp_b=b)
    r = CS.compare_stamped(10.0, 8.0, CS.DIRECT, stamp_a=st(), stamp_b=b, cross_state=True)
    assert r["engine_relation"] == CS.CROSS_ENGINE_STATE and r["stamp_b"][field] == "other"


def test_a_different_drawing_is_never_comparable():
    r = CS.compare_stamped(10.0, 8.0, CS.DIRECT, stamp_a=st(), stamp_b=st(DRAWING_SHA="b" * 64), cross_state=True)
    assert r["status"] == CS.NOT_COMPARABLE and r["difference"] is None and r["engine_relation"] == CS.DIFFERENT_DRAWING


def test_s4_provenance_carries_the_comparison_stamp():
    assert set(CS.STAMP_FIELDS) <= set(AR.S4_PROVENANCE_FIELDS)
    pv = part()["provenance"]
    assert CS.stamp(**{f: pv[f] for f in CS.STAMP_FIELDS})
