"""R8.6 pre-migration registers: owner input stays explicit, no gate is lowered, qualification is scoped."""

from __future__ import annotations

import json
from pathlib import Path

REG = Path(__file__).parent / "registers"
ROUND1 = ["Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14"]


def r(name):
    return json.loads((REG / f"{name}.json").read_text())


def test_no_owner_action_is_resolved_without_owner_input():
    a = r("OWNER_ACTION_REGISTER")
    ids = {x["action_id"] for x in a["actions"]}
    for need in ("CONFIRM_QORTUBA_NATIVE_UNIT", "REVIEW_QORTUBA_SECOND_FLOOR_PLAN_DESIGNATION",
                 "DECIDE_COLUMN_DEDUCTION_METHOD", "SUPPLY_INDEPENDENT_QORTUBA_DXF", "SUPPLY_INDEPENDENT_P7757_DXF"):
        assert need in ids
    resolved = [x for x in a["actions"] if x["status"] == "RESOLVED"]
    # the only resolved action is the one the owner answered explicitly, and it points at the recorded claim
    assert [x["action_id"] for x in resolved] == ["CONFIRM_QORTUBA_NATIVE_UNIT"] and a["resolved"] == 1
    claims = json.loads((Path(__file__).resolve().parents[2] / "data/registry/OWNER_UNIT_CLAIMS.json").read_text())
    c = next(c for c in claims["claims"] if c["evidence_id"] == resolved[0]["resolved_by_claim"])
    assert c["source_sha256"] == resolved[0]["exact_source_hash"] and c["native_to_mm"] == 10.0
    assert all(x["status"] == "OPEN" for x in a["actions"] if x is not resolved[0])
    assert next(x for x in a["actions"] if x["action_id"] == "REVIEW_QORTUBA_SECOND_FLOOR_PLAN_DESIGNATION")["status"] == "OPEN"
    for x in a["actions"]:
        assert len(x["exact_source_hash"]) == 64 and x["what_is_blocked"]


def test_every_gate_stays_where_the_evidence_puts_it():
    g = r("R8_6_DECISION_REGISTER")["gates"]
    assert g["PRODUCTION_MIGRATION"] == "NO" and g["MIGRATION_EXECUTION_READY"] == "NO"
    assert g["INDEPENDENT_REAL_RECONCILIATION"] == "BLOCKED_EXTERNAL_INPUT"
    assert g["QORTUBA_UNIT_CONTEXT"] == "CONFIRMED_BY_HUMAN"
    assert g["QORTUBA_REGION_DESIGNATION"] == "PENDING_OWNER" and g["QORTUBA_MEASUREMENT_FRAME"] == "UNCONFIRMED"
    assert g["ALRASHED_COLUMN_RULE"] == "TRADE_DEDUCTION_RULE_UNDECIDED"
    t = r("MIGRATION_TRANSACTION")
    assert t["status"] == "DESIGN_ONLY_NOT_EXECUTED" and t["MIGRATION_EXECUTION_READY"] == "NO"


def test_dependency_graph_blocks_every_row_and_names_what_blocks_it():
    g = r("QORTUBA_DEPENDENCY_GRAPH")
    states = set(g["states"])
    assert all(n["status"] in states for n in g["nodes"])
    nodes = {n["node"]: n["status"] for n in g["nodes"]}
    assert nodes["UNIT_CONTEXT"] == "READY" and nodes["REGION_DESIGNATION"] == "PENDING_OWNER"
    assert nodes["CAPABILITY_SIGNATURES"] == "PENDING_EXTERNAL" and nodes["MEASUREMENT_FRAME"] == "BLOCKED"
    assert sorted(x["node"].split(":")[1] for x in g["rows"]) == sorted(ROUND1)
    assert all(x["status"] == "BLOCKED" and x["blocking_ancestors"] for x in g["rows"])
    assert g["what_one_missing_fact_blocks"]["CEILING_CONDITIONS"] == ["QUANTITY_ROW:Q-14"]
    assert "UNIT_CONTEXT" not in g["what_one_missing_fact_blocks"]
    assert len(g["what_one_missing_fact_blocks"]["REGION_DESIGNATION"]) == 6


def test_round1_signatures_are_listed_one_by_one_and_none_is_qualified():
    s = r("ROUND1_CAPABILITY_SIGNATURES")
    assert s["required_count"] == len(s["required"]) == 10 and s["qualified"] == 0
    for x in s["required"]:
        assert x["QUALIFIED"] == "NO"
        for k in ("entity_kind", "curve_class", "transform_chain", "reflection_orientation", "block_depth",
                  "ocs_extrusion", "visibility", "handle_representation", "source_count"):
            assert x[k] is not None, k
        assert x["round1_occurrence_count"] >= 1
    assert s["net_reflected_occurrences"] > 0 and s["occurrences_inside_block_instances"] > 0
    assert len(s["not_required_for_round1"]) == s["source_signature_count"] - 10


def test_parser_plan_is_scoped_and_admission_first():
    p = r("INDEPENDENT_PARSER_TEST_PLAN")
    assert p["status"] == "PLANNED_NOT_RUN" and p["INDEPENDENT_REAL_RECONCILIATION"] == "BLOCKED_EXTERNAL_INPUT"
    assert p["step_1_admission"]["required_acadver"] == "AC1032"
    assert p["step_2_verification"]["HANDLE_IDENTITY"]["failure_blocks"] == "ENTIRE_ROUND"
    kinds = {x["failure_blocks"] for x in p["step_3_signatures"]}
    assert kinds == {"ENTIRE_ROUND", "ROWS_ONLY"}
    for x in p["step_3_signatures"]:
        if x["failure_blocks"] == "ENTIRE_ROUND":
            assert sorted(x["rows_blocked_on_failure"]) == sorted(ROUND1)


def test_every_remaining_qortuba_row_says_what_is_missing():
    b = r("QORTUBA_BLOCKER_REGISTER")
    assert b["count"] == 22
    kinds = set(b["kinds"])
    for x in b["rows"]:
        assert x["row_specific_missing"]
        assert all(m["kind"] in kinds for m in x["row_specific_missing"] + x["shared_missing"])


def test_legacy_audit_classifies_and_separates_value_from_metadata():
    a = r("LEGACY_LOGIC_AUDIT")
    classes = set(a["classes"])
    assert all(x["class"] in classes for x in a["dependencies"])
    assert a["search_result"] == {"hardcoded_coordinates": 0, "hardcoded_room_ids": 0, "manual_totals_in_value_path": 0,
                                  "benchmark_imports": 0}
    assert any(x.startswith("ceiling area") for x in a["legacy_logic_in_value_path"])
    assert any(x.startswith("unit selection") for x in a["legacy_logic_in_value_path"])


def test_closed_flag_defect_is_versioned_not_applied_and_does_not_decide_the_trade():
    d = r("ACTIVE_PATH_DEFECT_REGISTER")["defects"][0]
    assert d["defect_kind"] == "ACTIVE_PATH_DEFECT" and d["fix_status"] == "NOT_APPLIED" and d["version"] == 2
    assert d["code_unchanged_since_measured"] is True and d["active_reader_changed"] is False
    assert d["source_evidence"]["dropped_closing_edges_total"] == 56
    assert d["source_evidence"]["dropped_closing_edges"] == {"BASEMENT": {"col.str": 24}, "GROUND": {"col.str": 25},
                                                             "FIRST": {"col.str": 7}}
    assert d["questions"]["SOURCE_GEOMETRY"]["answer"] == "YES"
    assert d["questions"]["TRADE_METHOD"]["answer"] == "UNDECIDED"
    assert d["trade_rule_interaction"]["chosen"] is None


def test_migration_abort_conditions_cover_the_brief_and_fail_closed():
    t = r("MIGRATION_TRANSACTION")
    codes = {a["code"] for a in t["abort_conditions"]}
    for need in ("SOURCE_HASH_CHANGED", "DECODER_CHANGED_OR_UNQUALIFIED", "SIGNATURE_OUTSIDE_QUALIFICATION",
                 "REGION_CHANGED", "FRAME_EVIDENCE_CHANGED", "UNIT_CHANGED", "METHOD_REVISION_CHANGED",
                 "SOURCE_BLOCKER_APPEARED", "VALUE_DELTA_OUTSIDE_TOLERANCE", "ROW_PROVENANCE_MISSING", "UNEXPECTED_ROW_SET"):
        assert need in codes
    assert all(a["on_trigger"] == "ABORT_FAIL_CLOSED" for a in t["abort_conditions"])
    assert [s["step"] for s in t["steps"]] == list(range(1, 11))
    assert "overwrite an approved quantity in place" in t["never"]


def test_proof_rows_are_complete_and_never_naked():
    p = r("QORTUBA_ROUND1_PROOF")
    keys = ("row_id", "trade", "item", "rooms", "source_observations", "source_geometry_ids", "canonical_region_id",
            "frame_id", "unit_context", "source_capability_signatures", "decoder_qualification_requirement",
            "method_rule_ids", "formula", "formula_inputs", "canonical_native_value", "canonical_physical_value",
            "current_value", "difference_preview_minus_current", "status", "blockers", "release_eligibility")
    assert [x["row_id"].split("|")[0] for x in p["rows"]] == ROUND1
    for x in p["rows"]:
        for k in keys:
            assert k in x, k
        assert x["source_observations"] and x["source_capability_signatures"] and x["blockers"]
        assert x["release_eligibility"] == "NOT_ELIGIBLE" and x["canonical_physical_value"] is None
    assert p["results"]["rooms_equal_active_vs_canonical"] and p["results"]["canonical_deterministic"]
    assert p["canonical_runs_use_session_uploads"] is False
