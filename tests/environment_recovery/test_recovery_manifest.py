"""Environment recovery manifest and proposed inputs lock: paths and hashes only, every entry routed, no secrets."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "environment_recovery"
SECRETISH = re.compile(r"(BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|\"(password|secret|token|api_key)\"\s*:)", re.I)


def J(name):
    return json.loads((PKG / name).read_text(encoding="utf-8"))


def test_every_missing_prerequisite_is_categorised_and_routed():
    m = J("RECOVERY_MANIFEST.json")
    cats = {"DERIVED_EXPERIMENT", "BENCHMARK_TRUTH", "DERIVED_RUN", "SOURCE_DRAWING", "GOLDEN_FIXTURE",
            "DELIVERED_PACKAGE", "SESSION_UPLOAD", "OTHER"}
    assert m["missing_prerequisites"]
    for e in m["missing_prerequisites"]:
        assert e["category"] in cats and e["restore_route"] and e["evidence"]
        if "by_sha256/" in e["path"]:
            assert e["expected_sha256"] and e["expected_sha256"] in e["path"]
    assert all(e["restore_route"].startswith("RESTORE_FROM_SEALED_STORE") for e in m["missing_prerequisites"]
               if e["category"] == "BENCHMARK_TRUTH")


def test_lock_holds_metadata_and_hashes_only():
    lock = J("INPUTS.lock.proposed.json")
    assert set(lock["stores"]) == {"SOURCE", "DERIVED", "BENCHMARK"}
    for e in lock["entries"]:
        assert set(e) <= {"path", "sha256", "bytes", "store", "role", "discipline", "pinned_by", "note"}
        assert e["sha256"] is None or re.fullmatch(r"[0-9a-f]{64}", e["sha256"])
    for name in ("RECOVERY_MANIFEST.json", "INPUTS.lock.proposed.json", "README.md"):
        assert not SECRETISH.search((PKG / name).read_text(encoding="utf-8")), name


def test_checker_reports_and_flags_drift(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("check_prereq", PKG / "check_prerequisites.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    f = tmp_path / "x.bin"
    f.write_bytes(b"abc")
    monkeypatch.setattr(m, "ROOT", tmp_path)
    lock = tmp_path / "lock.json"
    lock.write_text(json.dumps({"entries": [{"path": "x.bin", "sha256": m.sha256(f), "store": "SOURCE"},
                                            {"path": "gone.bin", "sha256": "0" * 64, "store": "DERIVED"}]}))
    assert {r["path"]: r["state"] for r in m.check(lock)} == {"x.bin": "PRESENT", "gone.bin": "MISSING"}
    assert m.main(["x", str(lock)]) == 0
    f.write_bytes(b"abd")
    assert m.check(lock)[0]["state"] == "DRIFTED" and m.main(["x", str(lock)]) == 1


def test_reconstructed_inputs_are_marked_and_never_presented_as_originals():
    recon = "BYTE_IDENTICAL_RECONSTRUCTION_FROM_VERIFIED_UPLOAD"
    m = J("RECOVERY_MANIFEST.json")
    marked = {s["sha256"]: s["acquisition"] for s in m["registered_source_inputs"] if s.get("acquisition")}
    assert set(marked) == {"80b6a80428990db4dfa86aa343ed2c7cb429709459d564f0dac92362480a9b00",
                           "281a0c3f8c1cdd8f2a78528513b66d14ba4793e981e2d8059423faf6e6162f99"}
    for a in marked.values():
        assert a["acquisition"] == recon and a["not"] == "a separately obtained original"
        assert a["parent_evidence"].startswith("P7757_ARCH_PDF_SET_01-12") and re.fullmatch(r"[0-9a-f]{64}",
                                                                                            a["parent_sha256"])
    lock = {e["sha256"]: e for e in J("INPUTS.lock.proposed.json")["entries"] if e["sha256"] in marked}
    assert all(e["note"].startswith(recon) and "not a separately obtained original" in e["note"] for e in lock.values())


def _junit(tmp_path, cases):
    body = "".join(f'<testcase classname="t.m" name="{n}">{inner}</testcase>' for n, inner in cases)
    p = tmp_path / "j.xml"
    p.write_text(f'<?xml version="1.0"?><testsuites><testsuite>{body}</testsuite></testsuites>', encoding="utf-8")
    return p


def _classifier():
    spec = importlib.util.spec_from_file_location("classify_run", PKG / "classify_test_run.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_classifier_separates_proof_from_absence_and_breakage(tmp_path):
    m = _classifier()
    x = _junit(tmp_path, [
        ("ok", ""),
        ("skip_input", '<skipped message="private client drawings not restored in data/inputs/by_sha256"/>'),
        ("skip_other", '<skipped message="only on Windows"/>'),
        ("xf", '<skipped type="pytest.xfail" message="known limitation"/>'),
        ("blocked", "<failure message=\"FileNotFoundError: [Errno 2] No such file or directory: 'data/experiments/X/a.csv'\"/>"),
        ("prereq", '<failure message="AssertionError: run workbook_boq first"/>'),
        ("broken", '<failure message="AssertionError: 3 != 4"/>')])
    rep = m.classify(x, lock_path=tmp_path / "no_lock.json")
    assert rep["counts"] == {m.PASSED: 1, m.SKIP_PREREQ: 1, m.SKIP_OTHER: 1, m.XFAIL: 1, m.BLOCKED: 2, m.CODE: 1}
    assert rep["complete_project_regression_gate"] == "FAILED"            # a code failure always fails the gate
    assert rep["blocked_by_missing_path"]["data/experiments/X"] == 1


def test_gate_stays_incomplete_while_data_is_missing_and_completes_only_when_clean(tmp_path):
    m = _classifier()
    blocked = _junit(tmp_path, [("ok", ""), ("b", "<error message=\"No such file or directory: 'data/runs/7757/x'\"/>")])
    assert m.classify(blocked, lock_path=tmp_path / "none.json")["complete_project_regression_gate"] == "INCOMPLETE"
    skipped = _junit(tmp_path, [("ok", ""), ("s", '<skipped message="audited input not present"/>')])
    rep = m.classify(skipped, lock_path=tmp_path / "none.json")
    assert rep["complete_project_regression_gate"] == "INCOMPLETE" and rep["counts"][m.PASSED] == 1   # skip is no pass
    lock = tmp_path / "lock.json"
    lock.write_text(json.dumps({"entries": [{"path": "data/never_there.bin", "store": "BENCHMARK"}]}))
    clean = _junit(tmp_path, [("ok", ""), ("ok2", "")])
    assert m.classify(clean, lock_path=lock)["complete_project_regression_gate"] == "INCOMPLETE"
    assert m.classify(clean, lock_path=tmp_path / "none.json")["complete_project_regression_gate"] == "COMPLETE"
