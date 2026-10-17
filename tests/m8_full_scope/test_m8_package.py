"""M8 package: every deliverable present, the engine freeze holds (only the recorded post-freeze fixes changed), the
held-out and post-freeze records are their own (hashes, run-once invariants), the CSV deliverables rebuild from the
records byte for byte, the external positions appear only as differences, hygiene over the package and the M8 code,
and the visual QA PDF / workbook build (never committed)."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "urban_engine_m8_full_scope"
POST_FREEZE = {"engine/source/scope_quantities.py", "tools/m7_metamorphic.py"}
DELIVERABLES = ("00_M8_BRIEF.md", "00_ENGINE_FREEZE.json", "00_README.md", "01_EXECUTIVE_REPORT.md",
                "02_CONVENTIONS_V6.csv", "03_SCOPE_RULES.md", "04_HELDOUT_VALIDATION.md", "05_HELDOUT_BY_ELEMENT.csv",
                "06_ACCEPTANCE.csv", "06A_ACCEPTANCE_FROZEN.csv", "07_ST7757_BEFORE_AFTER.md",
                "08_ST7757_POSITIONS.md", "09_ABLATION.md", "10_PROPERTIES_AND_REGRESSION.md",
                "11_WEAKNESS_REGISTER.csv", "12_QUOTATION_STATUS.md", "13_REPRODUCIBILITY.md", "15_CHATGPT_HANDOFF.md",
                "heldout/HELDOUT_SUMMARY.json", "heldout_postfix/POSTFIX_SUMMARY.json",
                "st7757/SUMMARY.json", "st7757/POSITIONS.csv", "st7757/BY_FAMILY.csv", "st7757/ABLATION.csv",
                "st7757/SCOPE_BOUNDS.csv", "st7757/SCOPE_ITEMS.csv")
# TEST_GATE_M8.json records the full-suite run of this package, so it comes after it (as TEST_GATE_M7.json in M7)
M8_CODE = ("engine/source/scope_quantities.py", "tools/synthetic_villa_m8.py", "tools/m8_evaluate.py",
           "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json")
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}|(?i:als[ey]?n[ya]?an)")


def _module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_every_deliverable_is_present():
    missing = [f for f in DELIVERABLES if not (PKG / f).exists()]
    assert not missing, missing


def test_the_freeze_holds_the_files_as_committed():
    fz = json.loads((PKG / "00_ENGINE_FREEZE.json").read_text(encoding="utf-8"))
    assert fz["commit"] == "9d7aceb" and all(fz["git_blob_matches_commit"].values())
    for f, h in fz["files_sha256"].items():
        blob = subprocess.run(["git", "-C", str(ROOT), "show", f"{fz['commit']}:{f}"], capture_output=True,
                              check=True).stdout
        assert hashlib.sha256(blob).hexdigest() == h, f
    changed = {f for f, h in fz["files_sha256"].items() if hashlib.sha256((ROOT / f).read_bytes()).hexdigest() != h}
    assert changed == POST_FREEZE, changed            # exactly the post-freeze fixes P1-P4, nothing else


def test_the_heldout_record_is_its_own_and_was_run_on_the_frozen_engine():
    S = json.loads((PKG / "heldout" / "HELDOUT_SUMMARY.json").read_text(encoding="utf-8"))
    assert S["engine_commit"] == "9d7aceb" and S["seeds"] == [401, 440] and S["m7_seeds"] == [301, 340]
    for name, h in S["files_sha256"].items():
        assert hashlib.sha256((PKG / "heldout" / name).read_bytes()).hexdigest() == h, name
    for k, s in S["runs"].items():
        rec = json.loads((PKG / "heldout" / f"{k}.json").read_text(encoding="utf-8"))["summary"]
        assert json.loads(json.dumps(rec, default=str)) == json.loads(json.dumps(s, default=str)), k
    R = S["runs"]
    assert R["S_A"]["findings_without_range"] == 0 and R["S_B"]["findings_without_range"] == 0
    assert R["M7Q_A"]["rows_moved_vs_m7_v5"] == 0 and R["M7Q_B"]["rows_moved_vs_m7_v5"] == 0
    assert R["M7Q_A"]["silent_rows"] == 0 and R["M7Q_B"]["silent_rows"] == 0


def test_the_post_freeze_record_changes_only_stairs_and_keeps_them_in_range():
    P = json.loads((PKG / "heldout_postfix" / "POSTFIX_SUMMARY.json").read_text(encoding="utf-8"))
    assert P["frozen_commit"] == "9d7aceb" and set(P["post_freeze_files"]) == POST_FREEZE
    for run, changes in P["element_changes"].items():
        for c in changes:
            assert c["post_freeze"]["in_range"] and c["post_freeze"]["outcome"] == c["frozen"]["outcome"], c
    for run in ("S_A", "S_B"):
        v = P["runs"][run]["villa_total"]
        assert v["truth_in_bounded"] == v["n"] == 40
    for op in ("translate", "rot90", "rot180", "rot270", "units_m", "reorder", "explode", "dup_text"):
        assert P["runs"]["P"][op]["fail"] == 0, op


def test_the_csv_deliverables_rebuild_from_the_records():
    B = _module("m8_build_package", PKG / "build_package.py")
    for name, text in B.files().items():
        assert (PKG / name).read_text(encoding="utf-8") == text, name


def test_external_positions_appear_only_as_differences():
    """no external figure of the M5 record (freelance QS, MCP runs) is copied into the M8 package. The synthetic
    records (heldout*/, 05_HELDOUT_BY_ELEMENT.csv) are generator / engine output on synthetic drawings and can match a
    figure by chance (seed 428's tank truth does, at 3 decimals); for them the check is that the code that makes them
    never reads the M5 record."""
    synthetic = ("tools/synthetic_villa_m8.py", "tools/m8_evaluate.py",
                 "research/urban_engine_m8_full_scope/heldout_run.py",
                 "research/urban_engine_m8_full_scope/postfix_run.py")
    for f in synthetic:
        text = (ROOT / f).read_text(encoding="utf-8")
        assert "urban_engine_m5" not in text and "02C_FAMILY_TOTALS" not in text, f
    ext = set()
    for r in csv.DictReader((ROOT / "research/urban_engine_m5_concrete_reconciliation/02C_FAMILY_TOTALS.csv").open(
            encoding="utf-8")):
        for col in ("FREELANCER_M3", "UC4N_M3", "CHRISTIANNP_M3"):
            try:
                x = float(r[col])
            except ValueError:
                continue
            if x:
                ext.add(round(x, 3))
    nums = re.compile(r"-?\d+\.\d+")
    for p in PKG.rglob("*"):
        if p.is_file() and p.suffix in (".csv", ".md", ".json") and not any(x.startswith("heldout") for x in
                                                                              p.relative_to(PKG).parts) \
                and p.name != "05_HELDOUT_BY_ELEMENT.csv":
            found = {round(float(m), 3) for m in nums.findall(p.read_text(encoding="utf-8"))}
            assert not (found & ext), (p.name, sorted(found & ext)[:5])


def test_hygiene_over_the_package_and_the_m8_code():
    files = [p for p in PKG.rglob("*") if p.is_file() and p.suffix in (".md", ".csv", ".json", ".py")]
    files += [ROOT / f for f in M8_CODE]
    bad = {str(p.relative_to(ROOT)): sorted(set(HYGIENE.findall(p.read_text(encoding="utf-8"))))[:3]
           for p in files if HYGIENE.search(p.read_text(encoding="utf-8"))}
    assert not bad, bad
    tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", str(PKG.relative_to(ROOT))], capture_output=True,
                             text=True, check=True).stdout.split()
    assert not [p for p in tracked if p.lower().endswith((".pdf", ".xlsx", ".dxf", ".dwg", ".png", ".jpg", ".zip"))]


def test_the_st7757_record_has_every_finding_ranged():
    S = json.loads((PKG / "st7757" / "SUMMARY.json").read_text(encoding="utf-8"))
    assert S["phase"] == "POST_DISCOVERY" and S["scope_totals"]["findings_without_range"] == 0
    for name, h in S["files_sha256"].items():
        assert hashlib.sha256((PKG / "st7757" / name).read_bytes()).hexdigest() == h, name


def test_the_workbook_and_the_visual_qa_build(tmp_path):
    pytest.importorskip("openpyxl")
    pytest.importorskip("matplotlib")
    B = _module("m8_build_package2", PKG / "build_package.py")
    wb = B.workbook(tmp_path / "w.xlsx")
    assert Path(wb).stat().st_size > 10000
    V = _module("m8_build_visuals", PKG / "build_visuals.py")
    pdf = V.build(str(tmp_path / "v.pdf"))
    data = Path(pdf).read_bytes()
    assert data[:5] == b"%PDF-" and len(data) > 10000
