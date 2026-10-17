"""Phase A frozen registers (built from the delivered drawings by research/external_engine_lab/alsenan_phase_a.py):
the firewall held, the freeze validates, nothing blocked carries a quantity or enters a total, every complete
footing row is confirmed by the drawing, rebar is fail-closed, and no row value can be traced to a denied file."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.source import freeze_schema as FS

REG = Path(__file__).parent / "registers"
NAMES = ("SOURCE_MANIFEST", "SOURCE_AUTHORITY_REGISTER", "FLOOR_PLAN_REGISTER", "ROOM_REGISTER", "ARCH_BOQ",
         "BLOCKWORK_REGISTER", "OPENING_REGISTER", "STAIR_REGISTER", "WATERPROOFING_REGISTER",
         "STRUCTURAL_ELEMENT_REGISTER", "CONCRETE_REGISTER", "REBAR_REGISTER", "SANITARY_EVIDENCE_REGISTER",
         "OWNER_QUESTION_REGISTER", "BENCHMARK_FIREWALL", "DONOR_REUSE_REGISTER", "QA_RECONCILIATION",
         "ALSENAN_P7757_ST7757_PHASE_A_FREEZE", "TEST_RESULTS")


def R(n):
    p = REG / f"{n}.json"
    if not p.exists():
        pytest.skip(f"{n} not generated")
    return json.loads(p.read_text())


def test_all_nineteen_registers_exist():
    assert sorted(p.stem for p in REG.glob("*.json")) == sorted(NAMES)


def test_every_delivered_file_admitted_by_hash():
    m = R("SOURCE_MANIFEST")
    assert len(m["files"]) == 9 and all(len(f["sha256"]) == 64 for f in m["files"])
    assert {f["discipline"] for f in m["files"]} == {"ARCHITECTURAL", "STRUCTURAL", "SANITARY_SUPPORTING"}


def test_firewall_held():
    fw = R("BENCHMARK_FIREWALL")
    assert fw["audit_verdict"]["state"] == "PASS" and not fw["audit_verdict"]["violations"]
    assert fw["module_verdict"]["state"] == "PASS"
    assert {r["class"] for r in fw["audit_verdict"]["non_code_files_opened"]} <= {"SOURCE", "SOURCE_DERIVED"}
    assert fw["census"]["unclassified"] == []
    assert fw["statements"]["FREELANCER_BOQ_SEEN"] == "NO" and fw["statements"]["WEB_APP_QUANTITIES_SEEN"] == "NO"


def test_freeze_validates_and_states_the_lock():
    fr = R("ALSENAN_P7757_ST7757_PHASE_A_FREEZE")
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research/external_engine_lab"))
    import alsenan_registers as AR                                            # the schema owner
    rec = {k: v for k, v in fr.items() if k != "schema_validation"}
    assert FS.validate(rec, AR.FREEZE_SCHEMA)["state"] == "PASS"
    assert fr["FREELANCER_BOQ_SEEN"] is False and fr["WEB_APP_QUANTITIES_SEEN"] is False
    assert fr["EXPECTED_TOTALS_USED"] is False and fr["HISTORICAL_P7757_GOLD_USED"] is False
    assert fr["CONTAMINATION_DISCLOSED"] is True and fr["comparison"].startswith("NOT STARTED")


def test_dwg_dxf_identity_and_units():
    a = R("SOURCE_AUTHORITY_REGISTER")
    assert a["dwg_dxf_identity"]["P7757"]["state"] == "GEOMETRY_IDENTICAL"
    assert a["dwg_dxf_identity"]["ST7757"]["state"] == "NOT_VERIFIED"
    for u in a["units"].values():
        assert u["status"] == "PROVISIONAL" and abs(u["native_to_mm"] - 1.0) < 1e-6
        assert "FINAL_MEASUREMENT" not in u["allowed_uses"]


def test_blocked_rows_carry_no_quantity_and_enter_no_total():
    rows = R("ARCH_BOQ")["rows"] + R("CONCRETE_REGISTER")["boq_rows"]
    for r in rows:
        if r["status"] == "BLOCKED":
            assert r["qty"] is None and r["blockers"], r["item"]
        else:
            assert r["qty"] is not None
    assert all(r["status"] == "BLOCKED" for r in R("ARCH_BOQ")["rows"])     # no certified room -> nothing measured


def test_footing_rows_confirmed_and_summed_exactly():
    c = R("CONCRETE_REGISTER")
    by = {r["element_id"]: r for r in c["footing_rows"]}
    for r in c["footing_rows"]:
        if r["status"] == "COMPUTED_SHADOW_COMPLETE":
            assert r["size_check"].startswith("SIZE_CONFIRMED")
            d = r["dims"]
            assert abs(r["qty"] - d["L"]["m"] * d["W"]["m"] * d["H"]["m"]) < 1e-9
    for s in c["boq_rows"]:
        if s["item"].startswith("S-FTG-"):
            q = sum(by[i]["qty"] for i in s["complete_rows"]) if s["complete_rows"] else None
            assert (q is None and s["qty"] is None) or abs(q - s["qty"]) < 1e-9
    fs = c["footing_summary"]
    assert fs["complete"] + fs["blocked"] == fs["occurrences"]


def test_rebar_fail_closed():
    rb = R("REBAR_REGISTER")
    assert rb["tonnage_kg"] is None and all(r["kg"] is None for r in rb["specifications"])
    assert all(r["gate"]["state"] != "COMPUTED_SHADOW_COMPLETE" for r in rb["specifications"])


def test_room_topology_reported_not_hidden():
    rr = R("ROOM_REGISTER")
    for fl, t in rr["topology_runs"].items():
        assert t["certified_room_sites"] == 0 and t["sites"] > 0
    assert rr["diagnostic_hypothesis_run"]["status"].startswith("DIAGNOSTIC_ONLY")
    assert all(r["area_m2"] is None for r in rr["rooms"])


def test_qa_has_no_silent_critical_error():
    q = R("QA_RECONCILIATION")
    assert q["silent_critical_errors"] == 0
    assert q["xlsx"]["readback"]["state"] == "PASS" and q["xlsx"]["rewrite_identical"]
    assert R("ALSENAN_P7757_ST7757_PHASE_A_FREEZE")["excel_content_digest"] == q["xlsx"]["content_digest"]


def test_owner_questions_never_ask_for_quantities():
    for q in R("OWNER_QUESTION_REGISTER")["questions"]:
        t = q["question"].lower()
        assert "expected" not in t and "freelancer" not in t and "quantity" not in t
