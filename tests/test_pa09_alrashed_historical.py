"""The historical workbook against the frozen takeoff: evidence weighed, not obeyed.

The workbook is a refurbishment price list, not a bill of quantities, and most of it has no quantity to compare.
Where a comparison was possible the tests hold the two disciplines that make it worth anything: a difference is
classified rather than corrected backwards, and ENGINE_ERROR is reserved for a frozen figure the drawing itself
contradicts.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import historical_audit as HA

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
CLASSES = {"CLOSE_AGREEMENT", "SCOPE_DIFFERENCE", "COMMERCIAL_RULE_DIFFERENCE",
           "HISTORICAL_CALCULATION_ERROR", "OWNER_INPUT_DIFFERENCE", "ENGINE_ERROR",
           "NOT_COMPARABLE", "SOURCE_INFORMATION_MISSING"}


def rec():
    return json.loads((OUT / "ALRASHED_HISTORICAL_VALIDATION.json").read_text("utf-8"))


def frozen():
    return json.loads((OUT / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json").read_text("utf-8"))


# ------------------------------------------------------------------ identity
def test_the_workbook_matches_the_hash_the_owner_declared():
    i = rec()["INTEGRITY"]
    assert i["MD5"] == HA.DECLARED_MD5 and i["MD5_MATCHES_DECLARATION"]
    assert i["SHA256"] == HA.DECLARED_SHA256 and i["SHA256_MATCHES_DECLARATION"]


def test_identity_rests_on_owner_confirmation_because_the_file_names_no_project():
    i = rec()["INTEGRITY"]
    assert i["PROJECT_NAME_INSIDE_WORKBOOK"] is None
    assert any("owner" in b for b in i["IDENTITY_BASIS"])
    assert any("room schedule" in b for b in i["IDENTITY_BASIS"])


# ------------------------------------------------------------------ the frozen result
def test_the_frozen_takeoff_is_unchanged_and_nothing_was_written_back():
    f = frozen()
    assert f["DIGEST"] == "ae259eaba3203798" and f["GIT_HEAD"] == "3e847af"
    assert f["TOTALS"]["ALUMINIUM_M2"] == 14.3301
    assert f["TOTALS"]["BLOCKWORK_200_NET_M2"] == 963.188
    assert rec()["FROZEN_UNCHANGED"]["WRITTEN_BACK"] is False


def test_no_historical_figure_leaked_into_the_frozen_artifact():
    blob = json.dumps(frozen(), ensure_ascii=False)
    for historical in ("950.22", "64.2739", "45306.33", "50743", "1425.33", "2230"):
        assert historical not in blob, historical


# ------------------------------------------------------------------ the formula audit
def test_every_formula_was_recalculated_and_none_is_arithmetically_wrong():
    a = rec()["ARITHMETIC_VERIFIED"]
    assert a["ARITHMETIC_ERRORS"] == 0
    assert a["LITERAL_ONLY_RECALCULATED_FROM_THEIR_OWN_TEXT"] == a["OF_THOSE_AGREEING_WITH_THE_CACHED_VALUE"]
    assert a["REFERENCE_BEARING_CHECKED_AGAINST_THEIR_PRECEDENTS"] == a["OF_THOSE_AGREEING"]


def test_the_grand_total_omission_is_quantified_not_merely_asserted():
    e = next(x for x in rec()["HISTORICAL_ERRORS"] if x["ID"] == "HE-01")
    assert e["CLASS"] == "HISTORICAL_FORMULA_ERROR"
    assert sum(e["OMITTED_CELLS"].values()) == e["UNDERSTATEMENT_BEFORE_UPLIFT"] == 1375.0
    assert abs(e["CORRECTED_I35"] - (e["AS_STATED_I35"] + 1375.0)) < 1e-6
    assert abs(e["CORRECTED_I37"] - e["CORRECTED_I35"] * 1.12) < 1e-6


def test_a_quantity_is_only_recovered_where_a_rate_and_a_formula_establish_it():
    for r in rec()["RECOVERED_QUANTITIES"]:
        if r["CONFIDENCE"] in ("NONE", "LOW"):
            assert r["QUANTITY"] is None or r["QUANTITY_SOURCE"] is None or r["CONFIDENCE"] == "LOW"
        if r["CONFIDENCE"] == "HIGH":
            assert r["QUANTITY"] and r["RATE"] and r["UNIT"] and r["QUANTITY_SOURCE"]


# ------------------------------------------------------------------ the comparison
def test_every_comparison_carries_a_classification_from_the_agreed_set():
    for c in rec()["COMPARISONS"]:
        assert c["CLASSIFICATION"] in CLASSES, c["ITEM"]
        assert c["EXPLANATION"] and c["TRADE"] and c["ITEM"]


def test_no_engine_error_was_declared_and_the_drawing_was_checked_before_ruling_it_out():
    assert rec()["VERDICT"]["ENGINE_ERRORS"] == 0
    assert not any(c["CLASSIFICATION"] == "ENGINE_ERROR" for c in rec()["COMPARISONS"])
    d = rec()["DRAWING_CHECK"]
    assert d["RESULT"]["GROUND"]["GLAZED_OPENING_RECTANGLES"] == 7
    assert d["RESULT"]["BASEMENT"]["GLAZED_OPENING_RECTANGLES"] == 0
    assert d["RESULT"]["FIRST"]["GLAZED_OPENING_RECTANGLES"] == 0
    assert "NOT an engine error" in d["VERDICT"]


def test_the_whole_aluminium_totals_were_not_compared_against_each_other():
    row = next(c for c in rec()["COMPARISONS"] if c["ITEM"] == "all glazed openings, whole villa")
    assert row["CLASSIFICATION"] == "NOT_COMPARABLE"
    assert "NOT THE SAME SCOPE" in row["BASIS"]


def test_the_door_counts_were_normalised_before_being_compared():
    b = next(c for c in rec()["COMPARISONS"] if c["ITEM"] == "basement door leaves")
    assert b["DELTA"] == 0 and b["CLASSIFICATION"] == "CLOSE_AGREEMENT"
    assert "aluminium" in b["BASIS"] and "wooden" in b["BASIS"]


def test_the_bathroom_window_gap_is_attributed_to_the_guide_not_to_the_measurement():
    row = next(c for c in rec()["COMPARISONS"] if "bathroom window" in c["ITEM"])
    assert row["CLASSIFICATION"] == "OWNER_INPUT_DIFFERENCE"
    assert "height" in row["EXPLANATION"]


def test_the_balustrade_is_a_missing_source_not_an_engine_failure():
    row = next(c for c in rec()["COMPARISONS"] if c["TRADE"] == "BALUSTRADE")
    assert row["CLASSIFICATION"] == "SOURCE_INFORMATION_MISSING"
    assert row["FROZEN_QUANTITY"] == 0 and row["HISTORICAL_QUANTITY"] == 57
    assert "do not write it into the frozen takeoff" in row["ACTION"]


# ------------------------------------------------------------------ lessons
def test_no_lesson_is_promoted_without_the_owner_being_asked():
    for l in rec()["LESSONS"]:
        assert l["CLASS"] in ("URBAN_STANDARD_CANDIDATE", "PROJECT_ONLY", "NO_RULE_INSUFFICIENT_EVIDENCE")
        if l["CLASS"] == "URBAN_STANDARD_CANDIDATE":
            assert l["ASK"].startswith("Promote to Urban Standard")


def test_the_window_guide_was_not_edited_by_this_pass():
    from research.qs_wall_treatment_01.pa09.alrashed import window_standard as WS
    assert WS.TABLE["BATHROOM"]["H"] == 0.60, "the guide stands until the owner decides"
