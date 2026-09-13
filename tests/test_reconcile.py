"""E30 — Benchmark Reconciler. An audit layer that never writes back.

The paired diagnostic is the point: area and perimeter together determine a
rectangle's sides, so a site row can be solved for the dimensions the surveyor
effectively measured. That is what caught the row-3 mis-mapping and what
disproved the centreline hypothesis.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from engine.reconcile import (AMBIGUOUS, CONFIRMED, DESIGN_VS_SITE, ENGINE_ERROR,
                              MEASUREMENT_BASIS_DIFFERENCE, BenchmarkReport,
                              Quantities, Reconciliation, derived_sides, sanity,
                              variance_pct)


def test_derived_sides_solves_the_real_qiyal_rows():
    assert [round(x, 3) for x in derived_sides(D("4.44"), D("8.50"))] == [D("2.400"), D("1.850")]
    assert [round(x, 3) for x in derived_sides(D("15.34"), D("16.30"))] == [D("5.200"), D("2.950")]
    assert [round(x, 3) for x in derived_sides(D("4.35"), D("8.80"))] == [D("2.900"), D("1.500")]


def test_an_impossible_area_perimeter_pair_returns_nothing():
    """No rectangle has 100 m2 inside an 8 m perimeter — say so, don't invent one."""
    assert derived_sides(D("100"), D("8")) is None


def test_a_square_is_solved_as_equal_sides():
    a, b = derived_sides(D("9"), D("12"))
    assert a == b == D("3")


def test_sanity_thresholds():
    assert sanity(D("1.5")) == "PASS"
    assert sanity(D("-1.5")) == "PASS"
    assert sanity(D("3")) == "REVIEW"
    assert sanity(D("9")) == "CHALLENGE"
    assert sanity(None) == "UNRESOLVED"


def test_variance_is_none_rather_than_a_divide_by_zero():
    assert variance_pct(D("5"), D("0")) is None
    assert variance_pct(None, D("5")) is None


def kit() -> Reconciliation:
    return Reconciliation(
        space_id="KIT-01",
        design=Quantities(D("20.3125"), D("19.00"), "printed 3250x6250"),
        site=Quantities(D("19.22"), D("18.50"), "qiyal row 1"),
        engine=Quantities(D("19.668"), None, "E23 raster"),
    )


def test_engine_and_site_variances_are_measured_against_design():
    r = kit()
    assert round(r.engine_area_variance_pct, 1) == D("-3.2")
    assert round(r.site_area_variance_pct, 1) == D("-5.4")
    assert round(r.site_perimeter_variance_pct, 1) == D("-2.6")


def test_engine_status_takes_the_worse_of_area_and_perimeter():
    r = kit()
    r.engine.perimeter_m = D("19.00")      # perfect perimeter, -3.2% area
    assert r.engine_status == "REVIEW"
    r.engine.area_m2 = D("30")             # now wildly wrong on area
    assert r.engine_status == "CHALLENGE"


def test_the_uniform_offset_that_would_explain_a_site_area():
    """If the qiyal measured to centrelines, one t should explain every room."""
    r = Reconciliation(
        space_id="BTH-05",
        design=Quantities(D("3.60"), D("7.80")),
        site=Quantities(D("4.35"), D("8.80")),
    )
    t = r.implied_uniform_offset_m()
    assert D("0.18") < t < D("0.19")        # ~184 mm for this room


def test_design_site_differences_never_block_the_agents():
    rep = BenchmarkReport(rows=[
        Reconciliation("A", classification=DESIGN_VS_SITE),
        Reconciliation("B", classification=MEASUREMENT_BASIS_DIFFERENCE),
    ])
    assert rep.ready_for_agents


def test_an_engine_error_blocks_the_agents():
    rep = BenchmarkReport(rows=[
        Reconciliation("A", classification=DESIGN_VS_SITE),
        Reconciliation("B", classification=ENGINE_ERROR),
    ])
    assert not rep.ready_for_agents and len(rep.engine_errors) == 1


def test_an_unresolved_row_also_blocks():
    rep = BenchmarkReport(rows=[Reconciliation("A")])     # defaults to UNRESOLVED
    assert not rep.ready_for_agents


def test_totals_skip_missing_values_rather_than_treating_them_as_zero():
    rep = BenchmarkReport(rows=[
        Reconciliation("A", design=Quantities(D("10"), D("4"))),
        Reconciliation("B", design=Quantities(None, D("6"))),
    ])
    assert rep.total("design", "area_m2") == D("10")
    assert rep.total("design", "perimeter_m") == D("10")
