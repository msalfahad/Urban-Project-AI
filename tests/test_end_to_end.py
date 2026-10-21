"""Tests for the end-to-end trace pipeline."""

from engine.rate_library import RateLibrary, RateCategory, RateItem
from pipeline.end_to_end import TradeLine, trace, render_trace


def _rates():
    return RateLibrary(categories=[
        RateCategory("concrete", items=[
            RateItem("خرسانه", "concrete", qty=380, unit="m3", unit_cost=28, total=10640),
        ]),
    ])


def test_trace_prices_and_shapes_for_the_app():
    lines = [TradeLine("RC concrete", "p9", 352.44, "m3", "خرسانه", "m3",
                       priced_qty=380, audit_status="RED")]
    traced = trace(lines, _rates(), project_tag="TEST")
    t = traced[0]
    assert t.rate == 28
    assert t.amount == 28 * 380
    # over-order variance is surfaced
    assert round(t.variance_pct, 1) == 7.8
    # the boq document is in the app's shape
    assert t.boq_item["formulaType"] == "simple"
    assert t.boq_item["measurements"]["qty"] == 380
    assert t.boq_item["costRate"] == 28


def test_missing_rate_leaves_amount_none():
    lines = [TradeLine("Unknown", "x", 10, "m2", "nonexistent")]
    traced = trace(lines, _rates(), project_tag="TEST")
    assert traced[0].rate is None
    assert traced[0].amount is None


def test_render_trace_runs():
    lines = [TradeLine("RC concrete", "p9", 352.44, "m3", "خرسانه", "m3", priced_qty=380)]
    out = render_trace(trace(lines, _rates(), "TEST"))
    assert "TRADE" in out and "TOTAL" in out
