"""E21 — Campaign Budget & KPIs tests."""

import pytest

from engine.campaign import CampaignResult, kpi_rates, pace_budget, split_budget


# ---- split_budget -------------------------------------------------------------
def test_splits_in_proportion():
    out = split_budget(800.0, {"instagram": 5, "whatsapp": 3})
    assert out == {"instagram": 500.0, "whatsapp": 300.0}


def test_split_always_sums_to_the_total():
    # 1000/3 does not divide into fils evenly; the parts must still add up.
    out = split_budget(1000.0, {"a": 1, "b": 1, "c": 1})
    assert round(sum(out.values()), 3) == 1000.0


def test_residual_goes_to_the_largest_share():
    out = split_budget(100.0, {"big": 7, "small": 3})
    assert round(sum(out.values()), 3) == 100.0
    assert out["big"] > out["small"]


def test_single_channel_takes_everything():
    assert split_budget(250.0, {"instagram": 1}) == {"instagram": 250.0}


def test_zero_budget_splits_to_zero():
    out = split_budget(0.0, {"instagram": 5, "whatsapp": 3})
    assert out == {"instagram": 0.0, "whatsapp": 0.0}


def test_negative_total_rejected():
    with pytest.raises(ValueError, match="negative"):
        split_budget(-10.0, {"instagram": 1})


def test_no_weights_rejected():
    with pytest.raises(ValueError, match="at least one"):
        split_budget(100.0, {})


def test_non_positive_weight_rejected():
    with pytest.raises(ValueError, match="positive"):
        split_budget(100.0, {"instagram": 0})


def test_non_numeric_weight_rejected():
    with pytest.raises(ValueError, match="must be a number"):
        split_budget(100.0, {"instagram": "lots"})


def test_boolean_weight_rejected():
    # bool is an int subclass; True as a weight is a bug, not a weight of 1.
    with pytest.raises(ValueError, match="must be a number"):
        split_budget(100.0, {"instagram": True})


# ---- pace_budget --------------------------------------------------------------
def test_flat_pacing_is_even():
    assert pace_budget(400.0, 4) == [100.0, 100.0, 100.0, 100.0]


def test_pacing_sums_to_the_channel_budget():
    weeks = pace_budget(1000.0, 7, front_load=2.0)
    assert round(sum(weeks), 3) == 1000.0
    assert len(weeks) == 7


def test_front_load_spends_more_early():
    weeks = pace_budget(900.0, 3, front_load=2.0)
    assert weeks[0] > weeks[-1]


def test_back_load_builds_to_a_finish():
    weeks = pace_budget(900.0, 3, front_load=0.5)
    assert weeks[0] < weeks[-1]


def test_one_week_is_the_whole_budget():
    assert pace_budget(123.456, 1) == [123.456]


def test_zero_budget_paces_to_zeros():
    assert pace_budget(0.0, 3) == [0.0, 0.0, 0.0]


def test_zero_weeks_rejected():
    with pytest.raises(ValueError, match="at least 1"):
        pace_budget(100.0, 0)


def test_non_positive_front_load_rejected():
    with pytest.raises(ValueError, match="front_load must be positive"):
        pace_budget(100.0, 4, front_load=0)


# ---- kpi_rates ----------------------------------------------------------------
def test_cost_per_lead():
    rates = kpi_rates(CampaignResult(spend_kwd=300.0, leads=12))
    assert rates["cost_per_lead_kwd"] == 25.0


def test_conversion_percentages():
    rates = kpi_rates(CampaignResult(
        spend_kwd=500.0, impressions=20000, clicks=400,
        leads=40, enquiries=10, contracts=2,
    ))
    assert rates["click_through_pct"] == 2.0
    assert rates["lead_conversion_pct"] == 10.0
    assert rates["enquiry_conversion_pct"] == 25.0
    assert rates["contract_conversion_pct"] == 20.0
    assert rates["cost_per_1k_impressions_kwd"] == 25.0


def test_no_results_is_unknown_not_zero():
    # A campaign that got nothing has no cost per lead. Reporting 0.0 would
    # read on a dashboard as "free leads".
    rates = kpi_rates(CampaignResult(spend_kwd=400.0))
    assert rates["cost_per_lead_kwd"] is None
    assert rates["click_through_pct"] is None
    assert rates["contract_conversion_pct"] is None


def test_negative_spend_rejected():
    with pytest.raises(ValueError, match="negative"):
        kpi_rates(CampaignResult(spend_kwd=-1.0))
