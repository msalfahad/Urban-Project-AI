"""engine/source/stair_fit_checks.py - synthetic known answers (no project data)."""

from __future__ import annotations

import random

import pytest

from engine.source import stair_fit_checks as FC


def test_run_end_both_directions():
    assert FC.run_end(1000.0, 12, 300.0, +1) == pytest.approx(4300.0)
    assert FC.run_end(5000.0, 12, 300.0, -1) == pytest.approx(1700.0)
    assert FC.run_end(5000.0, 1, 300.0, -1) == pytest.approx(5000.0)
    with pytest.raises(FC.FitCheckError):
        FC.run_end(0.0, 3, 300.0, 0)


def test_band_clearance_sign():
    # walking towards -y, beam band (1500, 1900) ahead: near face 1900
    assert FC.band_clearance(2000.0, (1500.0, 1900.0), -1) == pytest.approx(100.0)
    assert FC.band_clearance(1700.0, (1500.0, 1900.0), -1) == pytest.approx(-200.0)     # inside the band
    assert FC.band_clearance(1000.0, (1500.0, 1900.0), +1) == pytest.approx(500.0)
    assert FC.band_clearance(1600.0, (1900.0, 1500.0), +1) == pytest.approx(-100.0)     # order of the band ignored


def test_max_risers_and_going_to_fit():
    assert FC.max_risers(3100.0, 300.0) == 11           # 10 goings of 300 = 3000 <= 3100
    assert FC.max_risers(3300.0, 300.0) == 12
    assert FC.max_risers(0.0, 300.0) == 1
    assert FC.going_to_fit(3100.0, 12) == pytest.approx(3100 / 11)
    assert FC.going_to_fit(3000.0, 12) == pytest.approx(3000 / 11)
    with pytest.raises(FC.FitCheckError):
        FC.going_to_fit(3000.0, 1)


def test_transition_levels_close_and_are_uniform():
    r = FC.transition_levels(1000.0, 5500.0, [("F1", FC.FLIGHT, 10), ("W", FC.WINDERS, 5), ("L", FC.LANDING, 0),
                                              ("F2", FC.FLIGHT, 12)])
    s = {x["segment"]: x for x in r["segments"]}
    assert r["riser"] == pytest.approx(4500 / 27) and r["risers"] == 27
    assert s["F1"]["end_level"] == pytest.approx(1000 + 10 * 4500 / 27)
    assert s["L"]["start_level"] == s["L"]["end_level"] == pytest.approx(3500.0)
    assert s["F2"]["end_level"] == 5500.0 and (s["F2"]["first_riser"], s["F2"]["last_riser"]) == (16, 27)
    rnd = random.Random(5)
    for _ in range(100):
        segs = [("a", FC.FLIGHT, rnd.randint(1, 14)), ("w", FC.WINDERS, rnd.randint(1, 5)), ("l", FC.LANDING, 0),
                ("b", FC.FLIGHT, rnd.randint(1, 14))]
        r = FC.transition_levels(0.0, 4200.0, segs)
        ends = [x["end_level"] for x in r["segments"]]
        assert ends == sorted(ends) and ends[-1] == 4200.0
        for x in r["segments"]:
            assert x["end_level"] - x["start_level"] == pytest.approx(x["risers"] * r["riser"])
    with pytest.raises(FC.FitCheckError):
        FC.transition_levels(0, 3000, [("l", FC.LANDING, 1)])


def test_headroom():
    assert FC.headroom(5500.0, 500.0, 3411.0) == pytest.approx(1589.0)
    with pytest.raises(FC.FitCheckError):
        FC.headroom(5500.0, 0.0, 3000.0)
