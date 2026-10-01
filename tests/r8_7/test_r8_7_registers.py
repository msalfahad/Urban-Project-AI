"""R8.7 registers: revisions kept apart, owner decisions recorded where they were given, the remeasurement
labelled diagnostic, changes attributed to a cause, gates unchanged."""

from __future__ import annotations

import json
from pathlib import Path

REG = Path(__file__).parent / "registers"
OLD_DWG = "2ec3a9c8b66eb2e129275b87010f4a8d79d7e5bdcc31c1897c14fd7e5647d355"
NEW_DXF = "df0e1d690285f5455b3b5acebe7e20eaee2d1c8aa3743b633a9fd257c6d6f315"


def r(name):
    return json.loads((REG / f"{name}.json").read_text())


def test_two_revisions_never_mixed_and_the_old_proof_is_superseded_not_wrong():
    rv = r("QORTUBA_SOURCE_REVISION_REGISTER")["revisions"]
    old, new = rv["QORTUBA_REV_OLD"], rv["QORTUBA_REV_NEW"]
    assert old["dwg_sha256"] == OLD_DWG and old["status"] == "HISTORICAL_VALIDATED_REVISION" and old["plan_count"] == 1
    assert old["proof"]["R8_6_six_row_canonical_rebuild"] == "VALID_FOR_REVISION_OLD"
    assert old["proof"]["classification_now"] == "SUPERSEDED_SOURCE_BASELINE"
    assert old["proof"]["is_not"] == "CURRENT_QORTUBA_QUANTITY_TRUTH"
    assert new["dxf_sha256"] == NEW_DXF and new["matching_original_dwg"] == "PENDING_EXTERNAL_INPUT"
    assert new["relationship_to_old"] == ["SAME_DRAWING_LINEAGE", "LATER_REVISION", "OWNER_SELECTED_CURRENT_REVISION"]
    assert new["plan_count"] == 4 and new["selected"]["variant"] == "PLAN_VARIANT_4_SELECTED"
    assert set(new["plan_variants"]) == {"PLAN_VARIANT_1", "PLAN_VARIANT_2", "PLAN_VARIANT_3", "PLAN_VARIANT_4_SELECTED"}
    assert new["unit"]["state"] == "OWNER_CONFIRMED_PENDING_EXACT_DWG_ANCHOR"


def test_owner_actions_reflect_the_decisions_already_given():
    a = {x["action_id"]: x for x in r("OWNER_ACTION_REGISTER")["actions"]}
    for k in ("CONFIRM_QORTUBA_NATIVE_UNIT", "CONFIRM_QORTUBA_AUTHORITATIVE_REVISION", "SELECT_QORTUBA_BOTTOM_MOST_PLAN",
              "CONFIRM_QORTUBA_NEW_REVISION_NATIVE_UNIT", "REVIEW_QORTUBA_Q14_CEILING_CONDITIONS"):
        assert a[k]["status"] == "RESOLVED" and a[k]["resolved_by_claim"], k
    assert a["SUPPLY_QORTUBA_NEW_REVISION_DWG"]["status"] == "FILE_RECEIVED"          # identity not yet established
    assert a["APPROVE_QORTUBA_NEW_ROUND1_BASELINE"]["status"] == "OPEN_AFTER_REMEASUREMENT"
    assert "REVIEW_QORTUBA_SECOND_FLOOR_PLAN_DESIGNATION" not in a and "SUPPLY_DXF_CONVERSION_RECORD" not in a
    for k in ("DECIDE_ALRASHED_COLUMN_DEDUCTION_METHOD", "CONFIRM_P7757_NATIVE_UNIT", "RESOLVE_ALRASHED_UNIT",
              "REVIEW_ALRASHED_FLOOR_WINDOWS"):
        assert a[k]["status"] == "OPEN"


def test_every_declared_field_fails_closed_and_the_hall_case_is_caught():
    abl = r("FAIL_CLOSED_ABLATION_RESULTS")["ablations"]
    for x in abl:
        if x["field"] == "texts.text_height (not declared)":
            assert x["guarded_state"] == "COMPLETE" and not x["lenient_legacy_run"]["six_change"]
        else:
            assert x["guarded_state"] != "COMPLETE" and x["guarded_quantity"] is None, x["field"]
    hall = next(x for x in abl if x["field"] == "parts.block_identity+parts.source_part_id")
    assert ["HALL / whgm", 25.0925] in hall["lenient_legacy_run"]["rooms_only_in_lenient_run"]
    cut = next(x for x in abl if x["field"] == "region membership (candidate bounds)")
    assert cut["guarded_state"] == "METHOD_INPUT_INCOMPLETE" and cut["lenient_legacy_run"]["six"]["Q-13"] == 199.2895


def test_contract_fields_carry_evidence():
    c = r("QS01_METHOD_INPUT_CONTRACT")["contract"]
    for f in ("parts.block_identity", "parts.source_part_id", "parts.instance_path", "texts.world_placement",
              "dimensions.placed_points", "dimensions.measurement"):
        assert c["evidence"][f] == "CHANGES_OUTPUT", f
    assert c["evidence"]["texts.text_height (not declared)"] == "NO_CHANGE_ON_THIS_SOURCE"
    assert "text_height" not in c["text_fields"]


def test_new_revision_is_diagnostic_and_every_change_has_a_cause():
    d = r("QORTUBA_REVISION_DELTA")
    assert d["label"].startswith("NEW_REVISION_DXF_DIAGNOSTIC")
    rows = {x["row"]: x for x in d["rows"]}
    assert rows["Q-03P"]["new_revision_value"] == rows["Q-12"]["new_revision_value"] == 11.685
    assert rows["Q-03"]["state"].startswith("NEW_REVISION_DXF_DIAGNOSTIC_REVIEW_REQUIRED")
    assert rows["Q-13"]["new_revision_value"] is None and rows["Q-13"]["state"].startswith("BLOCKED")
    assert rows["Q-14"]["new_revision_value"] is None
    for x in d["rows"]:
        assert x["old_revision_value_contract_K1"] == x["old_revision_value_R8_6"]          # no regression of R8.6
        assert x["METHOD_DIFFERENCE"].startswith("NONE")
        assert set(x["causes"]) <= {"NO_CHANGE", "PARSER_DIFFERENCE", "SOURCE_REVISION_CHANGE"}
    assert all("UNEXPLAINED" not in c for x in d["rooms"] for c in x["cause"])
    culprit = d["parser_difference"]["bisected_culprits"]["culprits"]
    assert [c["part"][0] for c in culprit] == ["584"] and culprit[0]["max_abs_difference"] < 1e-9
    assert d["runs"]["NEW_K2"]["input"]["anchor"] == NEW_DXF and d["runs"]["OLD_K1"]["input"]["anchor"] == OLD_DWG


def test_q14_rule_is_scoped_and_does_not_rescue_missing_geometry():
    q = r("Q14_SCOPED_CEILING_RULE")
    assert q["scope"]["revision_id"] == "QORTUBA_REV_NEW" and q["scope"]["items"] == ["Q-14|CEILING_BY_AREA"]
    assert q["Q14_NEW_REVISION"] is None and q["state"].startswith("BLOCKED")
    assert set(q["scope_tests"].values()) == {"OWNER_SCOPE_MISMATCH", "PURPOSE_NOT_AUTHORISED"}
    assert q["future_requirement"]["method"] == "CEILING_NET_PLAN_AREA"


def test_outside_content_is_classified_not_deleted():
    c = r("REGION_CLASSIFICATION_NEW_REVISION")
    assert c["counts"]["SELECTED_MEASUREMENT_REGION:parts"] == 1363 and c["occurrences_split_by_the_selected_frame"] == []
    assert any(k.startswith("ALTERNATE_PLAN_VARIANT") for k in c["counts"])


def test_gates_unchanged():
    g = r("R8_7_DECISION_REGISTER")["gates"]
    assert (g["PRODUCTION_MIGRATION"], g["MIGRATION_EXECUTION_READY"], g["MIGRATION_PLANNING_READY"]) == ("NO", "NO", "YES")
    assert g["SIGNATURES_QUALIFIED"] == 0 and g["INDEPENDENT_REAL_RECONCILIATION"] == "BLOCKED_EXTERNAL_PROVENANCE"


def test_candidate_dwg_identity_is_not_forced():
    d = r("NEW_DWG_SOURCE_IDENTITY")
    assert d["candidate_dwg"]["sha256"] == "e4babbc2ded14d8b01d64fbfd4b373e6a09ba60c4490a56e6305a82c9e47171f"
    assert d["candidate_dwg"]["bytes"] == 35110771
    assert d["decoder"]["binary_matches_pin"] is True and d["decoder"]["exit_code"] != 0
    assert {"Header", "Classes", "AcDbObjects"} <= set(d["decoder_report"]["sections_failed"])
    assert d["required_comparisons_possible"] is False and d["verdict"] == "NOT_ESTABLISHED"
    pe = d["partial_evidence_read"]
    assert pe["file_version"]["equal"] and pe["LASTSAVEDBY"]["equal"] and pe["TDCREATE"]["equal"]
    assert pe["TDINDWG"]["dxf_minus_dwg_seconds"] == 125.0
    assert pe["last_saved_by_application"]["product"] == "AutoCAD 2023"
    # consequences: nothing promoted, nothing re-anchored, parser independence untouched
    rev = r("QORTUBA_SOURCE_REVISION_REGISTER")["revisions"]["QORTUBA_REV_NEW"]
    assert rev["anchor_kind"] == "DERIVED_PENDING_SOURCE" and rev["dxf_sha256"] == NEW_DXF
    assert rev["candidate_original_dwg"]["anchor_promoted"] is False
    claims = r("OWNER_PROJECT_CLAIMS")
    assert claims["re_anchoring"]["claims_re_anchored"] is False
    assert all(c["anchor_state"] == "OWNER_CONFIRMED_PENDING_EXACT_SOURCE_ANCHOR" and c["status"] == "ACTIVE"
               for c in claims["claims"])
    a = {x["action_id"]: x for x in r("OWNER_ACTION_REGISTER")["actions"]}
    assert a["SUPPLY_QORTUBA_NEW_REVISION_DWG"]["status"] == "FILE_RECEIVED"
    assert a["ESTABLISH_NEW_DWG_SOURCE_IDENTITY"]["status"] == "OPEN"
    assert a["ANCHOR_SELECTED_PLAN_TO_EXACT_NEW_DWG"]["status"] == "OPEN"
    assert r("R8_7_DECISION_REGISTER")["gates"]["SIGNATURES_QUALIFIED"] == 0
