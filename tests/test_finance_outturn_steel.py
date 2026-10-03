"""Tests for E15 Finance, E20 Estimate-vs-Actual, E2 BBS Steel."""

import pytest

from engine.finance import FinanceReport, CostLine
from engine.estimate_actual import OutturnReport, TradeOutturn
from engine.bbs_steel import Bar, steel_from_bars, ratio_check, BAR_KG_PER_M


# ---- E15 Finance ----
def test_forecast_and_margin():
    fr = FinanceReport(contract_value=150000, lines=[
        CostLine("concrete", budget=12000, committed=12800, actual=10000),
        CostLine("steel", budget=9270, committed=9270, actual=9270),
    ])
    # FAC = max(budget,committed,actual) per line = 12800 + 9270
    assert fr.forecast_at_completion() == 22070
    assert fr.projected_margin() == 150000 - 22070


def test_overspending_line_detected():
    fr = FinanceReport(contract_value=100000, lines=[
        CostLine("concrete", budget=12000, committed=12800),
    ])
    assert [l.category for l in fr.overspending_lines()] == ["concrete"]


def test_margin_erosion_alert():
    fr = FinanceReport(contract_value=10000, margin_alert_pct=5.0, lines=[
        CostLine("x", budget=9800, committed=9800),
    ])
    assert fr.margin_eroding()   # 2% margin < 5%


# ---- E20 Estimate vs Actual ----
def test_qty_and_cost_variance():
    t = TradeOutturn("concrete", estimated_qty=352.44, actual_qty=380,
                     estimated_cost=9868, actual_cost=10450)
    assert round(t.qty_variance_pct(), 1) == 7.8
    assert t.cost_variance_pct() > 0


def test_measured_production_rate_feeds_back():
    t = TradeOutturn("blockwork", actual_qty=1260, actual_weeks=6)
    assert t.measured_production_rate() == 210.0
    rep = OutturnReport("Alsenan", trades=[t])
    assert rep.learned_rates()["blockwork"] == 210.0


# ---- E2 BBS Steel ----
def test_bar_weight():
    # 10 bars of Ø12 at 12 m = 10*12*0.888
    b = Bar(12, 12.0, 10)
    assert b.weight_kg() == pytest.approx(10 * 12 * BAR_KG_PER_M[12])


def test_steel_totals_by_diameter():
    res = steel_from_bars([Bar(12, 10, 8), Bar(16, 10, 4)])
    assert 12 in res.by_diameter and 16 in res.by_diameter
    assert res.total_kg == pytest.approx(res.by_diameter[12] + res.by_diameter[16])


def test_ratio_check_healthy():
    # Alsenan: 44,190 kg / 352.44 m3 ≈ 125 kg/m3 → OK
    r = ratio_check(44190, 352.44)
    assert r["status"] == "OK"
    assert 120 < r["ratio"] < 130


def test_ratio_check_flags_absurd():
    assert ratio_check(500, 100)["status"] == "RED"   # 5 kg/m3
