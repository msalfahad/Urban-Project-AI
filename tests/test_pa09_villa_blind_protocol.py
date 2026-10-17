"""Qortuba sealed, and the villa protocol fixed before the drawings arrive.

A benchmark that can be edited is not a benchmark, so the seal is checkable rather than declarative.  And a blind
validation whose rules are written after the answer is visible proves nothing, so the protocol - what may be read,
what the classes are, what counts as a defect, what the tolerance is - is written and hashed while no villa drawing
exists anywhere in the repository.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.boq import benchmark_seal as BS
from research.qs_wall_treatment_01.pa09 import villa_blind_protocol as VP

BOQ = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
VILLA = Path(PR.OUT_DIR) / "pa09_villa_blind"


def reg(name, folder=BOQ):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


# ------------------------------------------------------------------ the seal
def test_the_benchmark_seal_covers_everything_the_owner_asked_to_preserve():
    s = reg("QORTUBA_BENCHMARK_SEAL")
    assert s["BENCHMARK_ID"] == "BENCHMARK_PROJECT_01"
    assert set(s["ROLES"]) == {"BENCHMARK_PROJECT_01", "WORKFLOW_REFERENCE", "REGRESSION_PROJECT"}
    for must in ("QORTUBA_FINAL_PRE_PRICING_TAKEOFF", "APPROVED_QUANTITIES",
                 "QORTUBA_BOQ_CONVERSION_WORKBOOK.xlsx", "URBAN_OWNER_RULES_V1"):
        assert must in s["SEALED_CONTENTS"], must
    assert s["MISSING"] == [] and s["SEAL_INTACT"] is True


def test_the_seal_notices_when_a_sealed_artifact_moves():
    """The whole value of a seal is that it fails when something changes."""
    v = BS.verify()
    assert v["SEAL_INTACT"] is True and v["CHANGED"] == [] and v["MISSING"] == []
    assert v["CHECKED"] == reg("QORTUBA_BENCHMARK_SEAL")["SEALED_COUNT"]


def test_the_sealed_project_carries_no_rate_and_nothing_approved():
    s = reg("QORTUBA_BENCHMARK_SEAL")
    assert s["RATES_SUPPLIED"] == 0 and s["WASTE_APPLIED"] is False
    assert s["APPROVED_COUNT"] == 0 and s["NOTHING_IS_APPROVED"] is True


# ------------------------------------------------------------------ what travels and what does not
def test_a_method_travels_and_a_measurement_of_one_flat_does_not():
    r = reg("QORTUBA_BENCHMARK_SEAL")["RULES"]
    carried = {x["RULE_ID"] for x in r["CARRIES_TO_THE_NEXT_PROJECT"]}
    barred = {x["RULE_ID"] for x in r["DOES_NOT_CARRY"]}
    assert carried and barred and not (carried & barred)
    assert all(i.startswith("US-") for i in carried), "only Urban standards travel"
    assert all(i.startswith("QP-") for i in barred), "every Qortuba project rule stays here"
    # the values that would be most tempting to reuse are exactly the ones barred
    params = {x["PARAMETER"]: x["VALUE"] for x in r["DOES_NOT_CARRY"]}
    assert params["QORTUBA_BLOCKWORK_HEIGHT"] == 3.00
    assert params["OWNER_CONFIRMED_INTERNAL_DOOR_HEIGHT"] == 2.20
    assert params["QORTUBA_WINDOW_HEIGHT"] == 1.500


def test_the_protocol_bars_the_same_project_values_the_seal_bars():
    p = reg("FULL_VILLA_BLIND_PROTOCOL", VILLA)
    s = reg("QORTUBA_BENCHMARK_SEAL")["RULES"]
    assert {x["RULE_ID"] for x in p["DOES_NOT_CARRY_FROM_QORTUBA"]} == {x["RULE_ID"] for x in s["DOES_NOT_CARRY"]}
    assert {x["RULE_ID"] for x in p["CARRIES_FROM_QORTUBA"]} == {x["RULE_ID"] for x in
                                                                 s["CARRIES_TO_THE_NEXT_PROJECT"]}


# ------------------------------------------------------------------ the blind discipline
def test_the_historical_boq_is_sealed_and_says_so_in_every_form():
    p = reg("FULL_VILLA_BLIND_PROTOCOL", VILLA)
    sealed = " | ".join(p["SEALED_UNTIL_FREEZE"]).lower()
    for must in ("quantities", "contractor measurements", "rates", "totals", "quotation"):
        assert must in sealed, must
    # a recollection is a leak too, so it is named
    assert "recollection" in sealed
    may = " | ".join(p["MAY_READ_BEFORE_FREEZE"]).lower()
    assert "historical" not in may


def test_only_an_engine_error_counts_against_the_system_and_it_is_declared_in_advance():
    p = reg("FULL_VILLA_BLIND_PROTOCOL", VILLA)
    assert set(p["DISCREPANCY_CLASSES"]) == set(VP.DISCREPANCY_CLASSES)
    assert p["CLASSES_THAT_ARE_DEFECTS"] == ["ENGINE_ERROR"]
    assert p["TOLERANCE"]["CLOSE_AGREEMENT_PCT"] == 2.0
    assert "before the comparison" in p["TOLERANCE"]["WHY"]


def test_a_frozen_blind_quantity_is_never_moved_to_improve_a_comparison():
    p = reg("FULL_VILLA_BLIND_PROTOCOL", VILLA)
    assert "not closed" in p["THE_FROZEN_FIGURE_IS_NEVER_MOVED"]
    assert set(VP.COMPARISON_FIELDS) >= {"OUR_QUANTITY", "HISTORICAL_QUANTITY", "ABSOLUTE_DELTA", "DELTA_PCT",
                                         "SCOPE_DIFFERENCE", "MEASUREMENT_BASIS_DIFFERENCE", "ENGINE_ERROR_IF_ANY",
                                         "OWNER_INPUT_DEPENDENCY", "STATUS"}


def test_an_ambiguity_becomes_a_question_before_it_becomes_code():
    a = reg("FULL_VILLA_BLIND_PROTOCOL", VILLA)["AMBIGUITY_POLICY"]
    assert a["DEFAULT"] == "ASK_THE_OWNER"
    assert len(a["CHANGE_SHARED_CODE_ONLY_IF"]) == 3
    assert any("ten-second question" in n for n in a["NEVER"])


def test_the_protocol_was_written_before_any_villa_drawing_existed():
    p = reg("FULL_VILLA_BLIND_PROTOCOL", VILLA)
    assert p["WRITTEN_BEFORE_ANY_DRAWING_WAS_READ"] is True
    assert p["STATUS"] == "AWAITING_DRAWINGS"
    assert p["INPUTS_PRESENT"] == [] or p["INPUTS_PRESENT"] == ["FULL_VILLA_BLIND_PROTOCOL.json"]
    assert p["NO_MANAGER_INTEGRATION_DURING_VALIDATION"] is True
    assert p["DIGEST"] and len(p["DIGEST"]) == 16


def test_the_success_test_measures_the_system_and_not_the_villa():
    m = {x["METRIC"] for x in reg("FULL_VILLA_BLIND_PROTOCOL", VILLA)["SUCCESS_METRICS"]}
    assert m == {"OWNER_QUESTIONS", "MANUAL_INTERVENTIONS", "MAJOR_QUANTITIES_MISSED",
                 "QUANTITY_DELTAS_BY_TRADE", "ENGINE_CODE_CHANGES", "TIME_DRAWINGS_TO_EXCEL"}
