"""Tests for E3 Calculator, E10 Funnel, E11 Revision Delta, E13/E19 Benchmark,
E18 Subcontractor Scoring."""

import pytest

from engine.calculator import QtyRecord, calculate, total_for, priced_total
from engine.funnel import Lead, analyse
from engine.revision_delta import BoqSnapshotLine, diff
from engine.benchmark import ScheduleBenchmark, aggregate_rates, confidence
from engine.subcontractor import Subcontractor, price_score_from_quotes, rank


# ---- E3 Calculator ----
def test_calculate_sums_within_unit():
    recs = [QtyRecord("plaster", "wall", 18, "m2"), QtyRecord("plaster", "wall2", 12, "m2"),
            QtyRecord("plaster", "skirt", 30, "m")]
    out = calculate(recs)
    assert out["plaster"]["m2"] == 30 and out["plaster"]["m"] == 30


def test_priced_total_applies_rates():
    recs = [QtyRecord("concrete", "footings", 352.44, "m3")]
    assert priced_total(recs, {("concrete", "m3"): 28}) == pytest.approx(352.44 * 28)


# ---- E10 Funnel ----
def test_funnel_counts_and_conversion():
    leads = [Lead("1", "whatsapp", "signed"), Lead("2", "whatsapp", "quoted"),
             Lead("3", "instagram", "conversation"), Lead("4", "whatsapp", "drawings")]
    r = analyse(leads)
    assert r.counts["conversation"] == 4 and r.counts["signed"] == 1
    assert r.conversion["signed"] == 25.0
    assert r.by_source["whatsapp"]["conversation"] == 3


def test_funnel_lost_reasons():
    leads = [Lead("1", stage="quoted", lost=True, lost_reason="price"),
             Lead("2", stage="quoted", lost=True, lost_reason="price")]
    r = analyse(leads)
    assert r.lost_reasons["price"] == 2


# ---- E11 Revision Delta ----
def test_revision_detects_add_remove_change():
    old = [BoqSnapshotLine("a", "x", 10, "m2", 100), BoqSnapshotLine("b", "y", 5, "m2", 50)]
    new = [BoqSnapshotLine("a", "x", 12, "m2", 120), BoqSnapshotLine("c", "z", 3, "m2", 30)]
    r = diff(old, new)
    assert [l.id for l in r.added] == ["c"]
    assert [l.id for l in r.removed] == ["b"]
    assert any(c.field == "quantity" for c in r.changed)
    # +20 (a) +30 (c) -50 (b) = 0
    assert r.cost_delta == pytest.approx(0.0)


# ---- E13 / E19 Benchmark ----
def test_schedule_benchmark_note():
    b = ScheduleBenchmark(proposed_weeks=64, baseline_weeks=52, own_projects_weeks=[60, 66])
    assert b.vs_baseline_pct() > 0
    assert "over" in b.note()


def test_aggregate_rates_and_confidence():
    rates = aggregate_rates([{"blockwork": 210}, {"blockwork": 230}, {"plaster": 450}])
    assert rates["blockwork"] == 220
    assert confidence([{"blockwork": 210}, {"blockwork": 230}])["blockwork"] == 2


# ---- E18 Subcontractor ----
def test_price_score_lowest_is_best():
    assert price_score_from_quotes(100, 100, 200) == 100
    assert price_score_from_quotes(200, 100, 200) == 0


def test_rank_considers_all_factors():
    cheap_bad = Subcontractor("A", "block", price_score=100, reliability=20, quality=20, responsiveness=20)
    dearer_good = Subcontractor("B", "block", price_score=70, reliability=90, quality=90, responsiveness=80)
    ranked = rank([cheap_bad, dearer_good])
    assert ranked[0].name == "B"   # the cheapest quote wasn't the cheapest overall
