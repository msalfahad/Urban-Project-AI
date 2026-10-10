"""engine/source/stair_riser_schedule.py - synthetic known answers (no project data)."""

from __future__ import annotations

import math
import random

import pytest

from engine.source import stair_geometry as SG
from engine.source import stair_riser_schedule as RS


# ------------------------------------------------------------------ counting drawn lines
def test_nosing_and_riser_face_pairs_count_once():
    # a flight drawn with a visible nosing and a hidden riser face 50 mm behind it, 300 mm goings
    lines = [(1000 + 300 * i, f"N{i}") for i in range(12)] + [(1050 + 300 * i, f"F{i}") for i in range(12)]
    r = RS.pair_lines(lines, pair_tol=60)
    assert len(r) == 12 and all(len(ids) == 2 for _, ids in r)
    assert RS.pitches([p for p, _ in r]) == [300.0] * 11
    # counted raw, the same drawing gives twice the risers
    assert len(lines) == 24


def test_duplicate_line_and_irregular_going_reported_not_corrected():
    r = RS.pair_lines([(0, "a"), (0.4, "a-copy"), (300, "b"), (550, "c")], pair_tol=60)
    assert [len(ids) for _, ids in r] == [2, 1, 1]
    assert RS.pitches([p for p, _ in r]) == pytest.approx([299.8, 250.0])


# ------------------------------------------------------------------ uniform risers and counts
def test_uniform_risers_and_counts_in_range():
    assert RS.uniform_riser(4500, 28) == pytest.approx(160.714285714)
    assert RS.uniform_riser(4500, 29) == pytest.approx(155.172413793)
    assert RS.uniform_riser(4200, 27) == pytest.approx(155.555555556)
    assert RS.uniform_riser(4200, 26) == pytest.approx(161.538461538)
    assert RS.counts_in_range(4500, 150, 160) == [29, 30]          # 28 gives 160.7: just outside
    assert RS.counts_in_range(4200, 150, 160) == [27, 28]
    with pytest.raises(RS.RiserScheduleError):
        RS.uniform_riser(4500, 0)


def test_schedule_levels_and_landing():
    r = RS.schedule(1.00, 5.50, [("F1", RS.FLIGHT, 12), ("W1", RS.WINDERS, 4), ("L1", RS.LANDING, 0),
                                 ("F2", RS.FLIGHT, 12)])
    assert r["n"] == 28 and len(r["rows"]) == 28
    assert r["landings"][0]["after_riser"] == 16
    assert r["landings"][0]["finished_mm"] == pytest.approx(1000 + 16 * 4500 / 28)
    assert r["rows"][-1]["finished_mm"] == pytest.approx(5500) and r["rows"][-1]["onto"] == "TOP_FLOOR"
    assert r["rows"][15]["onto"] == "LANDING" and r["rows"][14]["onto"] == "TREAD"
    assert all(x["concrete_mm"] is None for x in r["rows"])            # no finish given: no concrete level


# ------------------------------------------------------------------ first and last concrete risers
def test_first_last_closed_form_matches_the_schedule():
    rnd = random.Random(3)
    for _ in range(200):
        n1, n2, n3 = rnd.randint(2, 14), rnd.randint(0, 5), rnd.randint(2, 14)
        segs = [("F1", RS.FLIGHT, n1)] + ([("W", RS.WINDERS, n2)] if n2 else []) + [("L", RS.LANDING, 0),
                                                                                    ("F2", RS.FLIGHT, n3)]
        fb, ft, s = rnd.uniform(0, 120), rnd.uniform(0, 120), rnd.uniform(10, 60)
        r = RS.schedule(1.0, 4.6, segs, {"floor_bottom": fb, "floor_top": ft, "tread": s})
        h = r["riser_mm"]
        conc = [x["concrete_riser_mm"] for x in r["rows"]]
        first, last = RS.first_last(h, fb, ft, s)
        assert conc[0] == pytest.approx(first) and conc[-1] == pytest.approx(last)
        assert all(c == pytest.approx(h) for c in conc[1:-1])          # landing carries the tread finish
        assert math.fsum(conc) == pytest.approx(r["rise_mm"] - ft + fb)  # concrete rises sum to SSL_t - SSL_b


def test_equal_build_ups_give_uniform_concrete_risers():
    r = RS.schedule(5.5, 9.7, [("F1", RS.FLIGHT, 12), ("L", RS.LANDING, 0), ("F2", RS.FLIGHT, 15)],
                    {"floor_bottom": 30, "floor_top": 30, "tread": 30})
    assert all(x["concrete_riser_mm"] == pytest.approx(r["riser_mm"]) for x in r["rows"])


def test_a_different_landing_finish_moves_the_risers_either_side_only():
    r = RS.schedule(0.0, 3.0, [("F1", RS.FLIGHT, 10), ("L", RS.LANDING, 0), ("F2", RS.FLIGHT, 10)],
                    {"floor_bottom": 30, "floor_top": 30, "tread": 30, "landing": 50})
    c = [x["concrete_riser_mm"] for x in r["rows"]]
    assert c[9] == pytest.approx(150 - 20) and c[10] == pytest.approx(150 + 20)
    assert all(v == pytest.approx(150) for i, v in enumerate(c) if i not in (9, 10))


def test_offsets_a_stated_first_last_pair_would_require():
    fb, ft = RS.offsets_for(160.714285714, 200.0, 100.0, 30.0)
    assert fb == pytest.approx(69.285714286) and ft == pytest.approx(90.714285714)
    assert RS.first_last(160.714285714, fb, ft, 30.0) == pytest.approx((200.0, 100.0))
    assert RS.first_last(160.0, None, 50, 30) == (None, None)


def test_schedule_refuses_bad_segments():
    with pytest.raises(RS.RiserScheduleError):
        RS.schedule(0, 3, [("L", RS.LANDING, 2)])
    with pytest.raises(RS.RiserScheduleError):
        RS.schedule(0, 3, [("X", "RAMP", 3)])


# ------------------------------------------------------------------ volumes and bars
def test_plane_equivalent_volume_equals_a_straight_flight_between_plumb_cuts():
    for n, r, g, w, t in ((12, 160.714285714, 300, 1200, 160), (11, 181.8, 300, 1200, 160), (5, 170, 280, 1150, 150)):
        f = SG.straight_flight(n, r, g, w, t)
        plan = (n - 1) * g * w / 1e6
        assert RS.winder_plane_volume(plan, r, g, t) == pytest.approx(f["STAIR_CONCRETE_VOLUME"] / 1e9, rel=1e-9)
    with pytest.raises(RS.RiserScheduleError):
        RS.winder_plane_volume(1.0, 160, 300, 0)


def test_bar_length_rate():
    assert RS.bar_length_rate(8, 1200, 3500) == pytest.approx(33.6)
    with pytest.raises(RS.RiserScheduleError):
        RS.bar_length_rate(0, 1200, 3500)
