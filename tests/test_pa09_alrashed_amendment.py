"""The owner's corrections to the validation record, held as rules rather than as edits.

The amendment changes what was said about the historical evidence; it must change nothing that was measured.  So
the tests guard both halves: the reclassification is arithmetic on the 2% band and not a matter of taste, a floor
is written only where the workbook proves one, and the frozen artifact is still the artifact that was frozen.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import validation_amendment as VA

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"


def rec():
    return json.loads((OUT / "ALRASHED_VALIDATION_AMENDMENT_01.json").read_text("utf-8"))


def frozen():
    return json.loads((OUT / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json").read_text("utf-8"))


# ------------------------------------------------------------------ 1. the band
def test_close_agreement_is_two_percent_and_every_row_obeys_it():
    assert VA.CLOSE_AGREEMENT_MAX_PCT == 2.0
    for r in VA.RECLASSIFIED:
        inside = abs(r["DELTA_PCT"]) <= VA.CLOSE_AGREEMENT_MAX_PCT
        assert (r["NOW"] == "CLOSE_AGREEMENT") is inside, r["ITEM"]


def test_every_row_that_left_close_agreement_names_a_cause_rather_than_a_percentage():
    changed = [r for r in VA.RECLASSIFIED if r["CHANGED"]]
    assert len(changed) == 3
    for r in changed:
        assert r["WAS"] == "CLOSE_AGREEMENT" and r["NOW"] != "CLOSE_AGREEMENT"
        assert r["NOW"] in {"OWNER_INPUT_DIFFERENCE", "SOURCE_INFORMATION_MISSING", "SCOPE_DIFFERENCE"}
        assert len(r["WHY"]) > 60


# ------------------------------------------------------------------ 2. floors on proof only
def test_a_floor_is_written_only_where_the_workbook_proves_one():
    f = VA.FLOOR_ATTRIBUTION_RULE
    assert f["OTHERWISE"] == {"FLOOR": "UNKNOWN", "STATUS": "HISTORICAL_LOCATION_UNCONFIRMED"}
    assert len(f["PROVEN_ROWS"]) == f["RESULT"]["PROVEN_GROUND"] + f["RESULT"]["PROVEN_ROOF"]
    assert sum(f["RESULT"].values()) == 31
    for r in f["PROVEN_ROWS"]:
        assert r["PROOF"] and r["FLOOR"] in {"GROUND", "ROOF"}


def test_the_basement_inference_is_withdrawn():
    assert "withdrawn" in VA.FLOOR_ATTRIBUTION_RULE["WITHDRAWN"].lower() or \
           VA.FLOOR_ATTRIBUTION_RULE["WITHDRAWN"].startswith("the earlier reading")
    assert "inferred, not proven" in VA.FLOOR_ATTRIBUTION_RULE["WITHDRAWN"]


# ------------------------------------------------------------------ 3. rows, objects and leaves
def test_rows_and_objects_live_in_separate_fields():
    c = VA.HISTORICAL_COUNTS
    assert c["SCHEDULE_ROW_COUNT"] == {"WINDOWS": 24, "DOORS": 5, "SLIDING_DOORS": 2, "TOTAL": 31}
    assert c["PHYSICAL_OBJECT_COUNT"] == {"WINDOWS": 26, "DOORS": 6, "SLIDING_DOORS": 2, "TOTAL": 34}
    assert "ROW_COUNT" in c["FIELD_RULE"] and "PHYSICAL_OBJECT_COUNT" in c["FIELD_RULE"]


def test_every_multiplicity_is_stated_with_its_own_evidence():
    mult = VA.HISTORICAL_COUNTS["MULTIPLICITY"]
    assert len(mult) == 2
    for m in mult:
        assert m["PHYSICAL_OBJECT_COUNT"] == m["ROW_COUNT"] * m["MULTIPLICITY"]
        assert m["EVIDENCE"]
    extra = sum(m["PHYSICAL_OBJECT_COUNT"] - m["ROW_COUNT"] for m in mult)
    rows = VA.HISTORICAL_COUNTS["SCHEDULE_ROW_COUNT"]["TOTAL"]
    assert rows + extra == VA.HISTORICAL_COUNTS["PHYSICAL_OBJECT_COUNT"]["TOTAL"] == 34


def test_the_leaf_block_is_kept_out_of_the_opening_population():
    b = VA.HISTORICAL_COUNTS["SEPARATE_LEAF_COUNT_BLOCK"]
    assert b["TOTAL_LEAVES"] == 28
    assert b["IS_THE_SAME_POPULATION_AS_THE_L_M_SCHEDULE"] is False
    assert b["TOTAL_LEAVES"] != VA.HISTORICAL_COUNTS["PHYSICAL_OBJECT_COUNT"]["TOTAL"]
    assert "never be added" in b["NOTE"]


def test_the_revision_records_what_changed_and_what_did_not():
    assert VA.REVISION == 2
    last = VA.REVISION_HISTORY[-1]
    assert last["REVISION"] == 2 and "ROW_COUNT" in last["WHAT"]
    assert "no classification" in last["WHAT_DID_NOT_CHANGE"]


# ------------------------------------------------------------------ 4 and 5. two figures renamed
def test_the_950_area_is_a_commercial_basis_and_not_a_membrane_area():
    r = next(x for x in VA.RESTATED if x["FIGURE"] == 950.22)
    assert r["NOW"] == "HISTORICAL_COMMERCIAL_BASIS"
    assert r["MAY_BE_COMPARED_AGAINST_A_MEASURED_AREA"] is False
    assert "600.00" in r["WHY"]


def test_the_balustrade_is_a_site_question_and_enters_no_quantity():
    r = next(x for x in VA.RESTATED if x["FIGURE"] == 57.0)
    assert r["NOW"] == "FIELD_VERIFICATION_REQUIRED"
    assert r["ADDED_TO_FROZEN_QUANTITY"] is False


# ------------------------------------------------------------------ the rule decisions
def test_the_seven_decisions_are_recorded_exactly_as_the_owner_gave_them():
    by_id = {d["ID"]: d for d in VA.RULE_DECISIONS}
    assert sorted(by_id) == ["L-01", "L-02", "L-03", "L-04", "L-05", "L-06", "L-07"]
    assert by_id["L-01"]["DECISION"] == "REJECT"
    assert by_id["L-02"]["RULE_ID"] == "US-20"
    assert by_id["L-03"]["RULE_ID"] == "US-21"
    assert by_id["L-04"]["DECISION"] == "PROJECT_ONLY"
    assert by_id["L-05"]["CLASS"] == "NO_RULE"
    assert by_id["L-06"]["RULE_ID"] == "US-22"
    assert by_id["L-07"]["CLASS"] == "DATA_SCHEMA_RULE" and by_id["L-07"]["PERMANENT"] is True


def test_the_rejected_bathroom_height_never_reaches_the_window_guide():
    from research.qs_wall_treatment_01.pa09.alrashed import window_standard as WS
    assert WS.TABLE["BATHROOM"]["H"] == 0.60
    assert 0.75 not in {row["H"] for row in WS.TABLE.values()}


def test_only_promoted_decisions_carry_an_urban_or_schema_rule_id():
    promoted = {d["RULE_ID"] for d in VA.RULE_DECISIONS if d["DECISION"] == "PROMOTE"}
    assert promoted == set(VA.PROMOTED_RULE_IDS)
    for d in VA.RULE_DECISIONS:
        if d["DECISION"] != "PROMOTE":
            assert "RULE_ID" not in d, d["ID"]


# ------------------------------------------------------------------ the frozen state
def test_the_amendment_touches_nothing_that_was_measured():
    a = rec()
    assert a["FROZEN_UNCHANGED"]["TOUCHED"] is False
    assert frozen()["DIGEST"] == a["FROZEN_UNCHANGED"]["DIGEST"] == "ae259eaba3203798"


def test_the_corrected_verdict_reports_two_close_agreements_and_no_engine_error():
    v = rec()["CORRECTED_VERDICT"]
    assert v["CLOSE_AGREEMENT_AT_2_PCT_OR_BETTER"] == 2
    assert v["ENGINE_ERRORS"] == 0


def test_the_record_is_reproducible():
    assert VA.build()["DIGEST"] == rec()["DIGEST"]
