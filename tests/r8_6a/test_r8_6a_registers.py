"""R8.6A registers: a received file never resolves an action, nothing qualifies, the Qortuba DXF is the wrong
revision, the unit claim stays on its own hash, and no gate moves toward migration."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = Path(__file__).parent / "registers"
QORTUBA_DWG = "2ec3a9c8b66eb2e129275b87010f4a8d79d7e5bdcc31c1897c14fd7e5647d355"
QORTUBA_DXF = "df0e1d690285f5455b3b5acebe7e20eaee2d1c8aa3743b633a9fd257c6d6f315"
P7757_DXF = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"


def r(name):
    return json.loads((REG / f"{name}.json").read_text())


def test_files_are_identified_by_hash_and_no_session_path_is_frozen():
    i = r("DXF_INTAKE_REGISTER")
    assert {k: v["dxf_sha256"] for k, v in i["files"].items()}["QORTUBA"] == QORTUBA_DXF
    text = json.dumps(i)
    assert "/root/.claude" not in text and "/tmp/" not in text
    for v in i["files"].values():
        assert v["modified_by_urban"] is False and v["normalised_by_urban"] is False
        assert v["handles"]["collisions"] == 0 and v["owner_references"]["unresolved"] == 0
    # the rejected ezdxf rebuilds stay in history, unchanged
    assert {h["status"] for h in i["history_previous_rejected_conversions"]} == {"DIAGNOSTIC_NONQUALIFYING_CONVERSION"}


def test_writer_decoder_and_lastsavedby_are_three_separate_facts():
    p = r("DXF_PROVENANCE_REGISTER")
    for name, f in p["files"].items():
        assert f["DXF_WRITER"]["class"] == "AUTOCAD_OR_ODA_FAMILY_FORMAT", name
        assert f["DWG_DECODER"]["state"] == "CONVERTER_UNKNOWN" and f["DWG_DECODER"]["independent"] is False
        assert f["SOURCE_METADATA_LASTSAVEDBY"] == "Msalf"
        assert f["admission_v2"]["qualifies_anything"] is False
        assert f["admission_v2"]["parser_independence"] == "NOT_ESTABLISHED"


def test_qortuba_dxf_is_a_later_revision_and_is_rejected():
    p = r("DXF_PROVENANCE_REGISTER")["files"]["QORTUBA"]
    assert p["revision"]["state"] == "SAME_LINEAGE_DIFFERENT_REVISION"
    assert p["revision"]["fingerprintguid_equal"] is True and p["revision"]["versionguid_equal"] is False
    assert p["admission_v2"]["status"] == "REJECTED"
    assert p["revision_evidence"]["source_entities_missing_from_dxf"] == 21
    assert p["revision_evidence"]["entities_added_inside_region"] == 19
    assert p["editing_time_evidence"]["added_editing_time_seconds"] > 3600
    f = r("SOURCE_FIDELITY_RESULTS")["files"]
    assert f["QORTUBA"]["result"] == "SOURCE_FIDELITY_FAIL"
    assert f["QORTUBA"]["intake_class"] == "DIFFERENT_SOURCE_REVISION_PROVENANCE_UNVERIFIED_DXF"


def test_p7757_and_st7757_are_faithful_but_unverified():
    p, f = r("DXF_PROVENANCE_REGISTER")["files"], r("SOURCE_FIDELITY_RESULTS")["files"]
    for name in ("P7757", "ST7757"):
        assert p[name]["revision"]["state"] == "SAME_REVISION"
        assert p[name]["admission_v2"]["status"] == "PROVENANCE_UNVERIFIED"
        assert p[name]["editing_time_evidence"]["added_editing_time_seconds"] < 600
        assert f[name]["result"] == "SOURCE_FIDELITY_PASS"
        assert f[name]["intake_class"] == "HIGH_FIDELITY_PROVENANCE_UNVERIFIED_DXF"
        ident = f[name]["identity"]
        assert ident["missing_in_dxf"] == 0 and ident["different"] == 0
        assert ident["d1_block_headers"] == ident["dxf_block_definitions"]
    assert r("P7757_DXF_RESULTS")["handle_0x929"]["dxf_type"] == "ARC_DIMENSION"


def test_no_signature_qualifies_and_every_one_says_why():
    for reg, keys in (("QORTUBA_ROUND1_DXF_RESULTS", ("signatures",)), ("P7757_DXF_RESULTS", ("signatures", "structural_ST7757"))):
        x = r(reg)
        assert x["qualified"] == 0
        for k in keys:
            states = x[k]["signature_states"]
            assert states and {v["state"] for v in states.values()} == {"PROVENANCE_NOT_INDEPENDENT"}
            assert all("diagnostic" in v for v in states.values())
    assert r("QORTUBA_ROUND1_DXF_RESULTS")["INDEPENDENT_QORTUBA_RECONCILIATION"] == "BLOCKED_EXTERNAL_PROVENANCE"


def test_plan_variants_are_named_by_position_and_the_selection_matches_the_measured_plan():
    pv = r("QORTUBA_ROUND1_DXF_RESULTS")["plan_variants"]
    v = sorted(pv["variants"], key=lambda x: x["position_rank_from_top"])
    assert [x["variant_id"] for x in v] == ["PLAN_VARIANT_1", "PLAN_VARIANT_2", "PLAN_VARIANT_3",
                                            "PLAN_VARIANT_4_SELECTED_CANDIDATE"]
    assert v[-1]["label_handle"] == pv["bottom_most_label_handle"] == pv["tracked_dwg_region"]["contains_label_handle"] == "1AC"
    assert pv["tracked_dwg_region"]["region_id"] == "RC:MODEL_SPACE:4267:540:1649"
    assert "ambiguous" in pv["note"]          # 'last' by creation order is another copy: recorded, not resolved


def test_owner_actions_split_file_received_from_independent_provenance():
    a = r("OWNER_ACTION_REGISTER")
    acts = {x["action_id"]: x for x in a["actions"]}
    for need in ("REVIEW_QORTUBA_SECOND_FLOOR_PLAN_DESIGNATION", "REVIEW_QORTUBA_Q14_CEILING_CONDITIONS",
                 "APPROVE_QORTUBA_ROUND1_BASELINE", "DECIDE_ALRASHED_COLUMN_DEDUCTION_METHOD", "CONFIRM_P7757_NATIVE_UNIT",
                 "RESOLVE_ALRASHED_UNIT", "REVIEW_ALRASHED_FLOOR_WINDOWS", "DECIDE_QORTUBA_DRAWING_REVISION",
                 "SUPPLY_QORTUBA_SOURCE_DWG_OF_DXF", "SUPPLY_DXF_CONVERSION_RECORD"):
        assert acts[need]["status"] == "OPEN", need
    assert [k for k, x in acts.items() if x["status"] == "RESOLVED"] == ["CONFIRM_QORTUBA_NATIVE_UNIT"]
    for k, sha in (("SUPPLY_INDEPENDENT_QORTUBA_DXF", QORTUBA_DXF), ("SUPPLY_INDEPENDENT_P7757_DXF", P7757_DXF)):
        assert acts[k]["status"] == "OPEN"
        assert acts[k]["FILE_RECEIVED"]["state"] == "RECEIVED" and acts[k]["FILE_RECEIVED"]["sha256"] == sha
        assert acts[k]["INDEPENDENT_PROVENANCE_ESTABLISHED"] == "NO"
    d = acts["REVIEW_QORTUBA_SECOND_FLOOR_PLAN_DESIGNATION"]
    assert d["question"] == "Is this the correct Qortuba second-floor plan view that Urban should use for quantity measurement?"
    assert d["choices"] == ["YES", "NO", "NOT SURE"] and d["binds_to"] == QORTUBA_DWG
    assert len(acts["REVIEW_QORTUBA_Q14_CEILING_CONDITIONS"]["affected_spaces"]) == 10
    for x in a["actions"]:
        assert len(x["exact_source_hash"]) == 64 and x["what_is_blocked"]


def test_unit_claim_is_not_transferred_to_the_new_files():
    claims = json.loads((ROOT / "data/registry/OWNER_UNIT_CLAIMS.json").read_text())["claims"]
    assert [c["source_sha256"] for c in claims] == [QORTUBA_DWG]
    u = {x["action_id"]: x for x in r("OWNER_ACTION_REGISTER")["actions"]}["CONFIRM_QORTUBA_NATIVE_UNIT"]
    assert u["binds_only_to"] == QORTUBA_DWG and QORTUBA_DXF in u["not_transferred_to"]


def test_gates_stay_closed_and_the_recommendation_is_recorded():
    d = r("R8_6A_DECISION_REGISTER")
    g = d["gates"]
    assert (g["PRODUCTION_MIGRATION"], g["MIGRATION_EXECUTION_READY"], g["MIGRATION_PLANNING_READY"]) == ("NO", "NO", "YES")
    assert g["INDEPENDENT_QORTUBA_RECONCILIATION"] == g["INDEPENDENT_P7757_RECONCILIATION"] == "BLOCKED_EXTERNAL_PROVENANCE"
    assert g["SIGNATURES_QUALIFIED"] == 0 and g["QORTUBA_REGION_DESIGNATION"] == "PENDING_OWNER"
    c = d["canonical_input_contract_review"]
    assert c["recommendation"] == "A" and len(c["fields"]) == 10
    assert all(f["fail_closed_today"] == "NO" for f in c["fields"])     # the gap the next round closes
