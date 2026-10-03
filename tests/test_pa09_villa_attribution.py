"""The owner attributed two files to a new project. The question is whether they are one.

Attribution is the owner's to give; identity is not.  These tests hold the one thing a blind validation cannot be
talked out of: a source that is byte-identical to the sealed benchmark's own input is recognised as such, and the
phase reports that a blind measurement is impossible rather than producing a takeoff that would look like one.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.boq import benchmark_seal as BS
from research.qs_wall_treatment_01.pa09 import villa_attribution as VA

VILLA = Path(PR.OUT_DIR) / "pa09_villa_blind"


def rec():
    return json.loads((VILLA / "FULL_VILLA_BLIND_ATTRIBUTED_SOURCES.json").read_text("utf-8"))


def qs():
    return json.loads((VILLA / "FULL_VILLA_BLIND_OWNER_QUESTIONS_BATCH_01.json").read_text("utf-8"))


# ------------------------------------------------------------------ identity beats attribution
def test_a_source_identical_to_the_sealed_input_is_recognised_however_it_is_labelled():
    r = rec()
    hits = [x for x in r["ROWS"] if x["IDENTITY"]["IS_A_SEALED_BENCHMARK_INPUT"]]
    assert hits, "the attributed DWG is byte-identical to the benchmark's own input and must be caught"
    assert hits[0]["IDENTITY"]["SEALED_ROLE"] == "DWG"
    assert r["SEALED_BENCHMARK_INPUTS_IN_THE_ATTRIBUTED_SET"] == [h["SOURCE"] for h in hits]


def test_the_phase_refuses_to_call_this_a_blind_measurement():
    r = rec()
    assert r["BLIND_MEASUREMENT_POSSIBLE"] is False
    assert "no takeoff was produced from these sources" in r["WHAT_WAS_NOT_DONE"]


def test_identity_is_checked_against_the_benchmarks_own_module_not_a_copied_path():
    """If the benchmark's input ever moves, this check moves with it instead of silently passing."""
    from research.qs_wall_treatment_01.pa08.qortuba import blind as QB
    assert VA.SEALED_INPUTS["DWG"] == QB.DWG and VA.SEALED_INPUTS["PDF"] == QB.PDF


# ------------------------------------------------------------------ what the sheets say
def test_both_attributed_sheets_are_the_same_storey_of_the_same_building():
    r = rec()
    assert r["SHEETS_PRESENT"] == ["SECOND FLOOR PLAN"]
    assert r["DISCIPLINES_PRESENT"] == ["ARCHITECTURAL"]
    for row in r["ROWS"]:
        assert row["TITLE_BLOCK"]["ADDRESS"] and "Sabah Al Salem" in row["TITLE_BLOCK"]["ADDRESS"]


def test_the_storey_is_read_from_a_known_set_not_from_whatever_capitals_precede_it():
    """The flattened title block reads '...ALFAHDSECOND FLOOR PLAN'; the owner's name is not part of the sheet."""
    tb = VA.title_block("Mr : AHMAD SAMI ALFAHDSECOND FLOOR PLAN SCALE ------- 1/100")
    assert tb["SHEET_TITLE"] == "SECOND FLOOR PLAN"
    assert tb["OWNER_NAME"] == "AHMAD SAMI ALFAHD"


# ------------------------------------------------------------------ the revision
def test_the_two_revisions_differ_inside_the_plan_not_only_in_the_title_block():
    rv = rec()["REVISION_COMPARISON"]
    assert rv["VERDICT"] == "MATERIAL_REVISION"
    assert rv["ONLY_IN_A_INSIDE_PLAN_BODY"] > 200 and rv["ONLY_IN_B_INSIDE_PLAN_BODY"] > 200
    assert rv["SHARED"] > 0


def test_the_missing_disciplines_are_named_rather_than_assumed_absent():
    r = rec()
    assert set(r["DISCIPLINES_MISSING"]) >= {"STRUCTURAL", "MEP"}
    assert r["FLOORS_MISSING"] and r["VILLA_REQUIREMENT"]


# ------------------------------------------------------------------ the batch
def test_the_questions_arrive_as_one_batch_in_a_namespace_of_their_own():
    q = qs()
    assert q["BATCH"] == 1 and q["COUNT"] == len(q["QUESTIONS"])
    assert all(x["NO"].startswith("V-") for x in q["QUESTIONS"]), "Qortuba's numbers stay sealed with Qortuba"
    assert len({x["NO"] for x in q["QUESTIONS"]}) == q["COUNT"]


def test_no_question_asks_the_owner_to_read_an_opaque_id():
    for x in qs()["QUESTIONS"]:
        assert "OS-" not in x["ASK"] and "BE-" not in x["ASK"]
        assert x["WHY_IT_MATTERS"] and x["BLOCKS"]


# ------------------------------------------------------------------ the benchmark is untouched
def test_the_benchmark_seal_is_still_intact_after_the_attribution_pass():
    v = BS.verify()
    assert v["SEAL_INTACT"] is True and v["CHANGED"] == [] and v["MISSING"] == []
