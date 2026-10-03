"""Phase A2 frozen registers (built from the delivered drawings by research/external_engine_lab/alsenan_phase_a2.py):
the firewall held, the freeze validates, inferred roles are scoped claims, rooms certify only with evidence, every
quantity row has a class and blocked rows carry no quantity, heights / materials stay blocked, footings expanded
only by the constraint-unique rule, rebar is fail-closed and Qortuba did not change."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from engine.source import freeze_schema as FS

REG = Path(__file__).parent / "registers_a2"
NAMES = ("SOURCE_MANIFEST", "SOURCE_AUTHORITY_REGISTER", "ENTITY_ROLE_REGISTER", "PLAN_REGION_REGISTER",
         "WALL_BAND_REGISTER", "ROOM_TOPOLOGY_REGISTER", "ROOM_REGISTER", "OPENING_REGISTER",
         "PDF_VERTICAL_EVIDENCE_REGISTER", "FLOOR_CEILING_REGISTER", "ARCH_BOQ", "BLOCKWORK_REGISTER",
         "WALL_SURFACE_REGISTER", "SKIRTING_REGISTER", "STAIR_REGISTER", "WET_ROOM_REGISTER",
         "STRUCTURAL_FOOTING_REGISTER", "STRUCTURAL_COLUMN_REGISTER", "STRUCTURAL_BEAM_REGISTER",
         "STRUCTURAL_SLAB_REGISTER", "REBAR_EVIDENCE_REGISTER", "CONCRETE_REGISTER", "BENCHMARK_FIREWALL",
         "DONOR_REUSE_REGISTER", "OWNER_QUESTION_REGISTER", "QA_RECONCILIATION", "QORTUBA_REGRESSION",
         "ALSENAN_P7757_ST7757_PHASE_A2_FREEZE", "TEST_RESULTS")
CLASSES = {"PHYSICAL_MEASUREMENT", "TRADE_ASSIGNMENT", "BLOCKED_MATERIAL", "BLOCKED_HEIGHT", "BLOCKED_GEOMETRY"}


def R(n):
    p = REG / f"{n}.json"
    if not p.exists():
        pytest.skip(f"{n} not generated")
    return json.loads(p.read_text())


def test_all_registers_exist():
    assert sorted(p.stem for p in REG.glob("*.json")) == sorted(NAMES)


def test_firewall_held_and_nothing_denied_opened():
    fw = R("BENCHMARK_FIREWALL")
    assert fw["audit_verdict"]["state"] == "PASS" and not fw["audit_verdict"]["violations"]
    assert fw["module_verdict"]["state"] == "PASS"
    assert {r["class"] for r in fw["audit_verdict"]["non_code_files_opened"]} <= {"SOURCE", "SOURCE_DERIVED"}
    assert fw["statements"]["FREELANCER_BOQ_SEEN"] == "NO" and fw["statements"]["WEB_APP_QUANTITIES_SEEN"] == "NO"


def test_freeze_validates():
    fr = R("ALSENAN_P7757_ST7757_PHASE_A2_FREEZE")
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research/external_engine_lab"))
    import alsenan_a2_registers as AR2
    assert FS.validate({k: v for k, v in fr.items() if k != "schema_validation"}, AR2.FREEZE_SCHEMA)["state"] == "PASS"
    assert fr["FREELANCER_BOQ_SEEN"] is False and fr["WEB_APP_QUANTITIES_SEEN"] is False
    assert fr["EXPECTED_TOTALS_USED"] is False and fr["comparison"].startswith("NOT STARTED")


def test_claims_are_scoped_policy_accepted_and_name_no_layer_map():
    er = R("ENTITY_ROLE_REGISTER")
    assert er["policy"]["claim"]["review_state"] == "POLICY_ACCEPTED"
    for fl, e in er["floors"].items():
        for c in e["claims"]:
            assert c["review_state"] == "POLICY_ACCEPTED" and c["authority"] == "ENTITY_ROLE_INFERENCE_V1"
            assert c["part_keys"] > 0 and c["scope"].endswith(":" + fl) and c["evidence"]
        assert len(e["frames"]) == 1                                              # the sheet frame was rejected


def test_regions_do_not_leak():
    assert R("PLAN_REGION_REGISTER")["leakage"]["state"] == "NO_LEAKAGE"


def test_rooms_certify_only_with_a_clean_site():
    rooms = R("ROOM_REGISTER")["rooms"]
    assert R("ROOM_REGISTER")["certified"] >= 1
    for r in rooms:
        if r["status"] == "COMPUTED_SHADOW_COMPLETE":
            assert not r["issues"] and r["floor_area_m2"] > 0 and r["floor_area_m2"] == r["base_ceiling_area_m2"]
            assert r["wall_face_area_m2"] is None and r["wall_face_area_blocker"].startswith("HEIGHT_NOT_PROVED")
        else:
            assert r["floor_area_m2"] is None and r["blocker"]


def test_every_row_has_a_class_and_blocked_rows_have_no_quantity():
    rows = R("ARCH_BOQ")["rows"] + R("CONCRETE_REGISTER")["boq_rows"]
    for r in rows:
        assert r["class"] in CLASSES, r["item"]
        if r["status"] == "BLOCKED":
            assert r["qty"] is None and r["blockers"], r["item"]
        else:
            assert r["qty"] is not None
    assert all(r["status"] == "BLOCKED" for r in rows if r["class"] in ("BLOCKED_MATERIAL", "BLOCKED_HEIGHT"))


def test_floor_lines_equal_their_rooms():
    rooms = R("ROOM_REGISTER")["rooms"]
    for r in R("ARCH_BOQ")["rows"]:
        if r["item"].startswith("A2-FLR-") and r["qty"] is not None:
            fl = r["item"].rsplit("-", 1)[1]
            s = sum(x["floor_area_m2"] for x in rooms if x["floor"] == fl and x["status"] == "COMPUTED_SHADOW_COMPLETE")
            assert abs(r["qty"] - s) < 1e-6


def test_doors_from_motif_and_closure_windows_from_gaps():
    o = R("OPENING_REGISTER")
    assert o["doors"] and o["windows"]
    for d in o["doors"]:
        assert d["height"].startswith("BLOCKED_HEIGHT") and d["material"].startswith("BLOCKED_MATERIAL")
        assert d["state"] in ("CLOSED", "OPENING_CLOSURE_UNRESOLVED")
    for w in o["windows"]:
        assert w["height"].startswith("BLOCKED_HEIGHT") and 300 <= w["width_mm"] <= 8000


def test_vertical_evidence_is_transcribed_not_measured():
    v = R("PDF_VERTICAL_EVIDENCE_REGISTER")
    assert "no pixel measurement" in v["method"]
    for i in v["items"]:
        assert {"id", "page", "crop_px", "text", "confidence"} <= set(i)
    f2f = {(x["from"], x["to"]): x for x in v["floor_to_floor"]}
    assert f2f[("GF", "1F")]["floor_to_floor_m"] == 4.5 and f2f[("GF", "1F")]["printed_dimension_agrees"]
    assert v["clear_height"].startswith("BLOCKED")


def test_blockwork_only_in_the_wall_thickness_range():
    for r in R("BLOCKWORK_REGISTER")["rows"]:
        if r["item"].startswith("A2-BLK-") and "-T" in r["item"]:
            t = int(r["item"].rsplit("-T", 1)[1])
            assert 80 <= t <= 400


def test_footings_expanded_only_by_the_constraint_rule():
    f = R("STRUCTURAL_FOOTING_REGISTER")
    s = f["summary"]
    assert s["complete"] >= s["phase_a"]["complete"] and s["complete"] + s["blocked"] == s["occurrences"]
    for r in f["footing_rows"]:
        if r.get("completion"):
            assert r["completion"]["rule"] in ("CONTAINED", "COUNT_UNIQUE") and r["status"] == "COMPUTED_SHADOW_COMPLETE"
        if r["status"] == "COMPUTED_SHADOW_COMPLETE":
            d = r["dims"]
            assert abs(r["qty"] - d["L"]["m"] * d["W"]["m"] * d["H"]["m"]) < 1e-9
    for t, v in f["completion"]["result"].items():
        if v["state"] != "COUNT_UNIQUE":
            assert not any(r.get("completion") for r in f["footing_rows"] if r["element_id"].startswith(t + "@"))


def test_rebar_fail_closed_and_columns_volume_blocked():
    assert R("REBAR_EVIDENCE_REGISTER")["tonnage_kg"] is None
    for c in R("STRUCTURAL_COLUMN_REGISTER")["columns"]:
        assert c["volume_m3"] is None and c["volume_blocker"].startswith("COLUMN_HEIGHT_NOT_PROVED")


def test_qa_and_qortuba():
    q = R("QA_RECONCILIATION")
    assert q["silent_critical_errors"] == 0 and q["xlsx"]["readback"]["state"] == "PASS" and q["xlsx"]["rewrite_identical"]
    assert R("QORTUBA_REGRESSION")["state"] in ("UNCHANGED", "PROVENANCE_ONLY")


def test_owner_questions_are_new_and_never_ask_for_quantities():
    oq = R("OWNER_QUESTION_REGISTER")
    for q in oq["questions"]:
        t = q["question"].lower()
        assert "expected" not in t and "freelancer" not in t and "quantity" not in t
        assert "finish schedule" not in t and "door / window schedule" not in t
