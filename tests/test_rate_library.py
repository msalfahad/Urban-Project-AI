"""Tests for E4 — Rate Library and the cost-export parser helpers."""

import pytest

from engine.rate_library import RateLibrary, RateCategory, RateItem
from tools.parse_cost_export import _num, _trailing_qty


def _lib():
    return RateLibrary(
        project="Test",
        grand_total=430.0,
        categories=[
            RateCategory("بند الخرسانة", stated_total=430.0, items=[
                RateItem("خرسانه", "بند الخرسانة", "Material", qty=380, unit="m3", unit_cost=28, total=10640),
            ]),
        ],
    )


def test_reconciles_true_when_items_match_total():
    c = RateCategory("x", stated_total=100.0, items=[
        RateItem("a", "x", total=60), RateItem("b", "x", total=40),
    ])
    assert c.reconciles()


def test_reconciles_false_on_mismatch():
    c = RateCategory("x", stated_total=100.0, items=[RateItem("a", "x", total=60)])
    assert not c.reconciles()


def test_find_and_rate_for():
    lib = _lib()
    assert lib.find("خرسانه")
    assert lib.rate_for("خرسانه", "m3") == 28


def test_implied_unit_cost_prefers_total_over_qty():
    it = RateItem("x", "c", qty=1500, unit="qty", unit_cost=0, total=0)
    assert it.implied_unit_cost() == 0.0
    it2 = RateItem("y", "c", qty=100, total=350)
    assert it2.implied_unit_cost() == 3.5


def test_round_trip_serialisation():
    lib = _lib()
    back = RateLibrary.from_dict(lib.to_dict())
    assert back.project == "Test"
    assert back.categories[0].items[0].unit == "m3"


def test_parser_number_helpers():
    assert _num("4,200 KWD") == 4200.0
    assert _num("28") == 28.0
    assert _num("no number") is None
    assert _trailing_qty("سيراميك1,400") == 1400.0
    assert _trailing_qty("محمد.م1") == 1.0
    assert _trailing_qty("no digits") is None
