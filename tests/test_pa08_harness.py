"""PA08 harness: acceptance refuses development projects and synthetic sources, the truth pack refuses results, the blind
subprocess catches a forbidden read, the comparison classifies a synthetic case and gate v4 stays NOT_READY without
independent validation."""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01.pa08 import config as C8, gate_v4 as G4, runner_ready_check as RR, source_acceptance as SA, truth_pack as TP


def test_acceptance_refuses_development_project_and_synthetic_sources(tmp_path):
    dev = [p for p in C8.DEVELOPMENT_PROJECTS["P7757"]["PATHS"] if Path(p).exists()]
    if dev:
        rec = SA.accept("CANDIDATE_X", dev[:1])
        assert rec["HAS_THIS_PROJECT_BEEN_USED_TO_DEVELOP_THE_ENGINE"] == "YES" and rec["INDEPENDENT_VALIDATION_STATUS"] == "REJECTED_NOT_INDEPENDENT"
    villa = RR.synthetic_villa(tmp_path / "v.json")
    rec = SA.accept("SYN", [str(villa)])
    assert rec["INDEPENDENT_VALIDATION_STATUS"] == "REJECTED_SYNTHETIC_DRY_RUN_ONLY" and rec["SYNTHETIC_SOURCE"]
    x = tmp_path / "boq.xlsx"; x.write_bytes(b"x")
    rec = SA.accept("SYN2", [str(villa), str(x)])
    assert any(r.get("REFUSED") for r in rec["FILES"])
    rec = SA.accept("P7757-again", [str(villa)])
    assert rec["HAS_THIS_PROJECT_BEEN_USED_TO_DEVELOP_THE_ENGINE"] == "YES"


def test_truth_pack_validation_refuses_results_and_requires_six_kinds():
    pack = RR.synthetic_truth_pack()
    assert TP.validate(pack)["VALID"]
    bad = json.loads(json.dumps(pack)); bad["CASES"][0]["EXPECTED_PLASTER_AREA_M2"] = 12.0
    v = TP.validate(bad)
    assert not v["VALID"] and any("forbidden key" in e for e in v["ERRORS"])
    few = json.loads(json.dumps(pack)); few["CASES"] = few["CASES"][:3]
    assert not TP.validate(few)["VALID"]


def test_dry_run_executes_every_step_and_catches_the_leak(tmp_path):
    rec = RR.run(out_dir=tmp_path)
    steps = {s["STEP"]: s for s in rec["STEPS"]}
    assert steps["BLIND_RUN"]["OK"] and steps["LEAK_IS_CAUGHT"]["OK"] and steps["LEAK_IS_CAUGHT"]["STATUS"] == "VALIDATION_INVALID"
    assert steps["TRUTH_PACK_VALIDATE_AND_SEAL"]["OK"] and steps["COMPARE"]["OK"]
    assert steps["COMPARE"]["METRICS"]["SILENT_WRONG_QUANTITY_COUNT"] == 0
    assert steps["GATE_V4"]["READINESS"] == "NOT_READY" and rec["COUNTS_AS_VALIDATION"] is False


def test_gate_v4_is_not_ready_without_validation():
    g = G4.evaluate()
    assert g["READINESS"] == "NOT_READY" and g["COUNTS"]["NOT_TESTED"] == 12
    review = {"ARTIFACT": "X", "FINDINGS": [{"FINDING_ID": "A", "SEVERITY": "CRITICAL_SILENT", "STATUS": "OPEN"}]}
    g = G4.evaluate(review=review)
    assert [c for c in g["CONDITIONS"] if c["ID"] == "C01_NO_CRITICAL_SILENT_PATH"][0]["STATUS"] == "FAIL"
    review["FINDINGS"][0]["STATUS"] = "GUARDED_PA07R2"
    g = G4.evaluate(review=review)
    assert [c for c in g["CONDITIONS"] if c["ID"] == "C01_NO_CRITICAL_SILENT_PATH"][0]["STATUS"] == "PASS" and g["READINESS"] == "NOT_READY"
