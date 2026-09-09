"""Tests for the dimension-takeoff (حصر) auditor."""

import pytest

from engine.audit import audit_file, is_takeoff_workbook, Severity
from ._takeoff_fixture import build_concrete_takeoff


@pytest.fixture
def takeoff_path(tmp_path):
    return build_concrete_takeoff(str(tmp_path / "concrete.xlsx"))


def _rules(report):
    return {i.rule for i in report.issues}


def test_detected_as_takeoff(takeoff_path):
    assert is_takeoff_workbook(takeoff_path)


def test_ref_error_is_caught_and_red(takeoff_path):
    report = audit_file(takeoff_path)
    assert "T02_excel_error" in _rules(report)
    assert report.status is Severity.RED


def test_lean_exclusion_flagged(takeoff_path):
    report = audit_file(takeoff_path)
    lean = [i for i in report.issues if i.rule == "T07_lean_excluded"]
    assert lean
    assert abs(lean[0].detail["lean_m3"] - 47.055) < 0.01


def test_healthy_steel_ratio_not_flagged(takeoff_path):
    # 5.8t/77.63 ≈ 75, 7.95t/39.75 = 200, overall (13.75t/117.38)=117 — all in band.
    report = audit_file(takeoff_path)
    assert "T06_steel_ratio" not in _rules(report)


def test_clean_takeoff_has_no_red(tmp_path):
    path = build_concrete_takeoff(str(tmp_path / "clean.xlsx"), with_ref_error=False)
    report = audit_file(path)
    assert report.status is not Severity.RED  # only the lean YELLOW remains
    assert "T02_excel_error" not in _rules(report)


def test_volume_formulas_not_false_flagged(tmp_path):
    # The per-element volume =D*C*B correctly omits the count column; the auditor
    # must NOT flag that (the bug we fixed).
    path = build_concrete_takeoff(str(tmp_path / "x.xlsx"), with_ref_error=False)
    report = audit_file(path)
    assert not any(i.rule.startswith("T01") for i in report.issues)
