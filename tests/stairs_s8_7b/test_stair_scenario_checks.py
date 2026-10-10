"""engine/source/stair_scenario_checks.py - synthetic known answers (no project data)."""

from __future__ import annotations

import math
import random

import pytest

from engine.source import stair_geometry as SG
from engine.source import stair_riser_schedule as RS
from engine.source import stair_scenario_checks as SC


# ------------------------------------------------------------------ landings
def test_a_landing_off_the_riser_grid_is_not_reachable():
    r = SC.landing_reach(1000.0, 5500.0, 28, 3500.0)
    assert r["riser_mm"] == pytest.approx(4500 / 28)
    assert r["k_exact"] == pytest.approx(2500 / (4500 / 28))           # 15.556: between two risers
    assert (r["k_below"], r["k_above"], r["k_nearest"]) == (15, 16, 16)
    assert r["level_below_mm"] == pytest.approx(1000 + 15 * 4500 / 28)
    assert r["nearest_error_mm"] == pytest.approx(1000 + 16 * 4500 / 28 - 3500)   # +71.4 mm
    assert not r["reachable"]
    q = SC.landing_reach(1000.0, 5500.0, 27, 3500.0)
    assert q["reachable"] and q["k_nearest"] == 15 and q["nearest_error_mm"] == pytest.approx(0.0, abs=1e-9)


def test_only_multiples_of_nine_reach_a_five_ninths_landing():
    got = SC.uniform_counts_for_landing(1000.0, 5500.0, 3500.0, range(2, 61))
    assert [n for n, _, _ in got] == [9, 18, 27, 36, 45, 54]
    assert all(k == 5 * n // 9 for n, k, _ in got)
    assert not [n for n, _, h in got if 150 <= h <= 160]               # none in a 150 - 160 band


def test_unequal_risers_needed_to_keep_a_fixed_landing():
    s = SC.split_risers(1000.0, 5500.0, 3500.0, 16, 12)
    assert s["riser_below_mm"] == pytest.approx(156.25)
    assert s["riser_above_mm"] == pytest.approx(2000 / 12)
    assert s["difference_mm"] == pytest.approx(2000 / 12 - 156.25)
    with pytest.raises(SC.ScenarioCheckError):
        SC.split_risers(1000.0, 5500.0, 6000.0, 16, 12)


# ------------------------------------------------------------------ setting out
def test_rounding_levels_never_accumulates():
    for b, t, n in ((1000.0, 5500.0, 28), (5500.0, 9700.0, 27), (0.0, 3000.0, 17), (150.0, 1000.0, 5)):
        r = SC.setting_out(b, t, n)
        assert r["max_abs_deviation_mm"] <= 0.5 + 1e-9
        assert sum(r["rounded_riser_counts"].values()) == n
        assert math.fsum(x["rounded_riser_mm"] for x in r["rows"]) == pytest.approx(t - b)
        assert set(r["rounded_riser_counts"]) <= {math.floor((t - b) / n), math.ceil((t - b) / n)}
        assert r["rows"][-1]["exact_mm"] == t
    r = SC.setting_out(1000.0, 5500.0, 28)
    assert r["rounded_riser_counts"] == {160: 8, 161: 20}


def test_repeating_one_rounded_riser_accumulates():
    assert SC.rounded_riser_drift(4500, 28, 160) == pytest.approx(-20.0)
    assert SC.rounded_riser_drift(4500, 28, 161) == pytest.approx(8.0)
    assert SC.rounded_riser_drift(4200, 27, 156) == pytest.approx(12.0)
    assert SC.rounded_riser_drift(4200, 27, 155) == pytest.approx(-15.0)


# ------------------------------------------------------------------ finishes and datums
def test_build_up_keeps_unknown_layers_unknown():
    assert SC.build_up({"marble": 30.0, "bedding": None}) is None
    assert SC.build_up({"marble": 30.0, "bedding": 20.0}) == pytest.approx(50.0)
    with pytest.raises(SC.ScenarioCheckError):
        SC.build_up({"screed": -5.0})


def test_datum_model_agrees_with_the_schedule_and_the_closed_form():
    rnd = random.Random(11)
    for _ in range(300):
        n1, n2, n3 = rnd.randint(2, 14), rnd.randint(0, 5), rnd.randint(2, 14)
        n = n1 + n2 + n3
        segs = [("F1", RS.FLIGHT, n1)] + ([("W", RS.WINDERS, n2)] if n2 else []) + [("L", RS.LANDING, 0),
                                                                                    ("F2", RS.FLIGHT, n3)]
        fb, ft, s, sl = (rnd.uniform(0, 120) for _ in range(4))
        b, t = 1000.0, 1000.0 + rnd.uniform(2500, 4800)
        d = SC.datum_levels(b, t, n, [n1 + n2], fb, ft, s, sl)
        r = RS.schedule(b / 1000, t / 1000, segs, {"floor_bottom": fb, "floor_top": ft, "tread": s, "landing": sl})
        assert d["concrete_risers_mm"] == pytest.approx([x["concrete_riser_mm"] for x in r["rows"]])
        assert d["closure_mm"] == pytest.approx(0.0, abs=1e-7)
        if sl == s:
            assert (d["first_mm"], d["last_mm"]) == pytest.approx(RS.first_last(d["riser_mm"], fb, ft, s))


def test_signs_of_the_first_and_last_concrete_risers():
    h = 4500 / 28
    d = SC.datum_levels(1000, 5500, 28, [16], 80.0, 80.0, 30.0)
    assert d["first_mm"] == pytest.approx(h + 50) and d["last_mm"] == pytest.approx(h - 50)   # thicker floor: taller first
    d = SC.datum_levels(1000, 5500, 28, [16], 30.0, 30.0, 30.0)
    assert all(v == pytest.approx(h) for v in d["concrete_risers_mm"])                     # equal build-ups: uniform
    d = SC.datum_levels(1000, 5500, 28, [16], 10.0, 10.0, 30.0)
    assert d["first_mm"] < h < d["last_mm"]                                              # thinner floor: reverse
    assert SC.datum_levels(1000, 5500, 28, [16], None, 50.0, 30.0) is None


# ------------------------------------------------------------------ exact flight quantities
def test_section_integral_equals_the_plumb_cut_outline():
    for n, h, g, w, t in ((12, 4500 / 28, 300, 1200, 160), (11, 4200 / 27, 300, 1200, 200), (5, 170, 300, 2800, 150),
                          (4, 175, 300, 1200, 175)):
        whole = SC.flight_section_volume(n, h, g, w, t)
        assert whole == pytest.approx(SG.straight_flight(n, h, g, w, t)["STAIR_CONCRETE_VOLUME"], rel=1e-12)
        assert whole / 1e9 == pytest.approx(RS.winder_plane_volume((n - 1) * g * w / 1e6, h, g, t), rel=1e-12)
        cut = 0.37 * (n - 1) * g
        assert (SC.flight_section_volume(n, h, g, w, t, 0, cut) + SC.flight_section_volume(n, h, g, w, t, cut)
                == pytest.approx(whole, rel=1e-12))


def test_section_integral_against_brute_force():
    n, h, g, w, t = 12, 160.714285714, 300.0, 1200.0, 175.0
    slope, drop = h / g, t * math.hypot(g, h) / g
    m, s0, s1 = 200000, 3150.0, 3300.0                 # the last 150 mm of the run
    ds = (s1 - s0) / m
    acc = 0.0
    for i in range(m):
        s = s0 + (i + 0.5) * ds
        top = (math.floor(s / g) + 1) * h
        acc += (top - (slope * s - drop)) * ds
    assert SC.flight_section_volume(n, h, g, w, t, s0, s1) == pytest.approx(acc * w, rel=1e-6)


def test_solid_steps_and_winder_bounds():
    assert SC.solid_steps_volume(4, 175, 300, 1200) == pytest.approx((1 + 2 + 3) * 175 * 300 * 1200)
    b = SC.winder_bounds([400000.0] * 4, 160.0, 160.0, 250.0)
    assert b["plane_equivalent_mm3"] / 1e9 == pytest.approx(RS.winder_plane_volume(1.6, 160, 250, 160))
    assert b["flat_soffit_bound_mm3"] == pytest.approx(1.6e6 * 160 + 400000 * 160 * (0 + 1 + 2 + 3))
    assert b["flat_soffit_bound_mm3"] > b["plane_equivalent_mm3"]
    with pytest.raises(SC.ScenarioCheckError):
        SC.winder_bounds([], 160, 160, 250)
    with pytest.raises(SC.ScenarioCheckError):
        SC.flight_section_volume(12, 160, 300, 1200, 0)
