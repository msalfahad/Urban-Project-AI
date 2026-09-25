"""End-to-end: load a real .xlsx and audit it.

Proves the openpyxl loader + rules catch every defect class the owner named,
on an Alsenan-Chalet-like workbook. Replace the fixture with the real file and
this same flow runs unchanged.
"""

import pytest

from engine.audit import audit_workbook, Severity
from ._fixture import build_alsenan_like


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    path = tmp_path_factory.mktemp("alsenan") / "alsenan_chalet.xlsx"
    build_alsenan_like(str(path))
    return audit_workbook(str(path))


def _rules(report):
    return {i.rule for i in report.issues}


def test_workbook_loads_all_sheets(report):
    assert set(report.sheets) == {"Takeoff", "Structure", "Finishes"}
    assert report.rows_checked > 0


def test_overall_status_is_red(report):
    assert report.status is Severity.RED
    assert not report.approved


@pytest.mark.parametrize("rule", [
    "R01_excel_error",              # #REF!
    "R02_blank_price",              # سيجما at zero
    "R03_amount_formula_error",     # gypsum 120*2.5 != 500
    "R05_mixed_units",              # m2 + m + no in one total
    "R07_skipped_sum_row",          # subtotal skips rows
    "R08_concrete_classification",  # raft foundation at C15
    "R09_steel_ratio",              # 5 kg/m3
    "R10_missing_waste",            # tiles/marble, no waste
])
def test_named_defect_is_caught(report, rule):
    assert rule in _rules(report), f"{rule} not found; got {_rules(report)}"


def test_report_serialises(report):
    d = report.to_dict()
    assert d["status"] == "RED"
    assert d["counts"]["RED"] >= 1
    assert isinstance(d["issues"], list)
