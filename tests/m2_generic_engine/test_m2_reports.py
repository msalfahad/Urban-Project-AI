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


@pytest.mark.skipif(not ST_DXF.exists(), reason="private ST7757 drawing not present")
def test_alsenan_generic_reproduces():
    spec = importlib.util.spec_from_file_location("m2rep", PKG / "build_m2_reports.py")
    B = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(B)
    I, D, conv, items, reg, risk = B.run_generic(ST_DXF)
    comp = {(r["TRADE"], r["FAMILY"]): r for r in B.comparison(items, D, risk)}
    frozen = {(r["TRADE"], r["FAMILY"]): r for r in csv.DictReader((PKG / "04_ALSENAN_GENERIC_VS_FROZEN.csv").open())}
    for k, r in frozen.items():
        assert comp[k]["GENERIC_PROVISIONAL_BASE"] == pytest.approx(float(r["GENERIC_PROVISIONAL_BASE"]), abs=1e-5), k
    gs = B.ground_slab_audit(D)
    assert sum(1 for r in gs if r["AUDIT_CLASS"] == "MATCHED_SLAB") == 19
    assert not any(r["AUDIT_CLASS"] == "GENERIC_NO_FACE_SILENT" for r in gs)
    assert all(i["category"] != "VERIFIED" for i in items)                  # a generic run never releases VERIFIED
