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
