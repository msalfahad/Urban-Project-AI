"""M2 package checks: the deliverables exist, carry no forbidden text or firewalled number, and the Alsenan generic
comparison / audit reproduce from the private drawing (skipped when it is not present). Nothing is written."""

from __future__ import annotations

import csv
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research/urban_engine_m2_generalization"
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
DELIVERABLES = ["00_README.md", "01_EXECUTIVE_SUMMARY.md", "02_ARCHITECTURE_BEFORE_AFTER.md", "03_MODULES.md",
                "04_ALSENAN_GENERIC_VS_FROZEN.md", "04_ALSENAN_GENERIC_VS_FROZEN.csv", "05_REINFORCEMENT_COMPLETENESS.md",
                "05_REINFORCEMENT_COMPLETENESS_89.csv", "06_GROUND_SLAB_GAP_AUDIT.md", "06_GROUND_SLAB_GAP_AUDIT.csv",
                "07_ALSENAN_COVERAGE_RISK.csv", "08_ACCURACY_COVERAGE_METRICS.json", "09_BENCHMARK_POSITIONS.csv",
                "10_STAIR_SCENARIOS.csv", "11_GENERIC_TEST_RESULTS.md", "12_BENCHMARK_DISCREPANCY_REPORT.md",
                "13_TECHNICAL_DEBT.md", "14_ENGINEERING_RFIS.csv", "15_REPRODUCIBLE_COMMANDS.md",
                "16_COMMITS_AND_BRANCH.md", "17_SUCCESS_CRITERIA.md"]
ST_DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"


def _bench():
    spec = importlib.util.spec_from_file_location(
        "m1pf_t", ROOT / "research/alsenan_m1_usable_boq/post_freeze/post_freeze_comparison.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.BENCH


def test_deliverables_present():
    missing = [d for d in DELIVERABLES if not (PKG / d).exists()]
    assert not missing, missing


def test_package_text_is_clean_and_firewalled():
    bench = _bench()
    for p in PKG.rglob("*"):
        if p.suffix not in (".md", ".csv", ".json", ".html", ".svg") or not p.is_file():
            continue
        t = p.read_text(encoding="utf-8")
        assert not HYGIENE.search(t), p.relative_to(ROOT)
        if p.suffix != ".py":
            leaked = [b for b in bench if re.search(r"(?<![\d.])" + re.escape(b) + r"(?!\d)", t)]
            assert not leaked, (p.relative_to(ROOT), leaked)


def test_89_components_listed_one_by_one():
    rows = list(csv.DictReader((PKG / "05_REINFORCEMENT_COMPLETENESS_89.csv").open()))
    assert len(rows) == 89 and len({r["M1_COMPONENT_ID"] for r in rows}) == 89
    assert all(r["GENERIC_REBAR_STATE"] for r in rows)


def test_benchmark_positions_carry_no_values():
    rows = list(csv.DictReader((PKG / "09_BENCHMARK_POSITIONS.csv").open()))
    assert rows and not any(k.startswith("EXTERNAL_") and "POSITION" not in k for k in rows[0])
    assert {r["EXTERNAL_POSITION_VS_GENERIC"] for r in rows} <= {"BELOW", "INSIDE", "ABOVE", "NO_EXTERNAL_VALUE",
                                                                   "NO_GENERIC_VALUE"}


# M2 evidence is frozen: the files written by build_m2_reports at the M2 commit are pinned byte for byte. The live
# reproduction of the M2 comparison moved to tests/m3_recovery (the engine has changed since M2, deliberately; the
# M2 numbers remain the record of the M2 engine, reproducible at commit c5123a7).
M2_PINS = {
    "04_ALSENAN_GENERIC_VS_FROZEN.csv": "57cac71f8ab8c6e7481bc13efc0ffe563497c335f51f0db6336f0d2faa1f659f",
    "05_REINFORCEMENT_COMPLETENESS_89.csv": "7889dd08a8016b10f2bd58c8d26f1cdbbbbc59134e4efbded6375545d67c0002",
    "06_GROUND_SLAB_GAP_AUDIT.csv": "3e557ccc44924a5732a543aac3338f440144175790d541abde99de478ad951fe",
    "07_ALSENAN_COVERAGE_RISK.csv": "5daa9758ac4cf4cb76df2d723ac560652c8c340be3b606ab0a99a4613ab009dc",
    "09_BENCHMARK_POSITIONS.csv": "9eaae1365bb28bf665f021ca7a22acda7bc9c5fa83cb3934177f9863f32014bb",
    "08_ACCURACY_COVERAGE_METRICS.json": "754b5c078a7a773e1f05f31fdd3ab15f5c09ddaabda90df74d2c7ca1e914ae84",
    "10_STAIR_SCENARIOS.csv": "75589d9671a8473282b91820019ba83d11cfe53c51427bfc2edc0948a2132410",
}


def test_m2_evidence_is_frozen():
    import hashlib
    for name, sha in M2_PINS.items():
        assert hashlib.sha256((PKG / name).read_bytes()).hexdigest() == sha, name
