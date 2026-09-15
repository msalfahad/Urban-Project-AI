"""Tests for E12 — Schedule Engine."""

from datetime import date

import pytest

from engine.schedule import Activity, schedule


def test_quantity_driven_duration():
    # 352 m3 at 60 m3/week -> ceil(5.87) = 6 weeks
    a = Activity("conc", "Concrete", quantity=352, unit="m3", production_rate=60)
    assert a.duration_weeks() == 6


def test_fixed_duration():
    assert Activity("prep", "Site prep", fixed_weeks=1).duration_weeks() == 1


def test_simple_chain_and_total():
    acts = [
        Activity("a", "A", fixed_weeks=2),
        Activity("b", "B", fixed_weeks=3, depends_on=["a"]),
        Activity("c", "C", fixed_weeks=1, depends_on=["b"]),
    ]
    prog = schedule(acts, start_date=date(2026, 9, 15))
    assert prog.total_weeks == 6
    by = {s.activity.id: s for s in prog.activities}
    assert by["a"].start_week == 1 and by["a"].end_week == 2
    assert by["b"].start_week == 3 and by["b"].end_week == 5
    assert by["c"].start_week == 6 and by["c"].end_week == 6
    # a straight chain is all critical
    assert set(prog.critical_path()) == {"a", "b", "c"}


def test_float_on_parallel_branch():
    # a -> b(long) and a -> c(short) -> both feed d. c has float.
    acts = [
        Activity("a", "A", fixed_weeks=1),
        Activity("b", "B", fixed_weeks=5, depends_on=["a"]),
        Activity("c", "C", fixed_weeks=1, depends_on=["a"]),
        Activity("d", "D", fixed_weeks=1, depends_on=["b", "c"]),
    ]
    prog = schedule(acts)
    by = {s.activity.id: s for s in prog.activities}
    assert by["b"].total_float == 0 and by["b"].critical
    assert by["c"].total_float == 4 and not by["c"].critical


def test_overlap_lets_successor_start_early():
    # blockwork can start when frame is 50% done
    acts = [
        Activity("frame", "Frame", fixed_weeks=8),
        Activity("block", "Blockwork", fixed_weeks=4, overlaps=[("frame", 0.5)]),
    ]
    prog = schedule(acts)
    by = {s.activity.id: s for s in prog.activities}
    assert by["block"].start_week == 5   # after 4 of 8 weeks of frame
    assert prog.total_weeks == 8         # block finishes within frame window


def test_dates_are_computed():
    prog = schedule([Activity("a", "A", fixed_weeks=2)], start_date=date(2026, 9, 15))
    s = prog.activities[0]
    assert s.start_date == date(2026, 9, 15)


def test_cycle_detected():
    acts = [Activity("a", "A", fixed_weeks=1, depends_on=["b"]),
            Activity("b", "B", fixed_weeks=1, depends_on=["a"])]
    with pytest.raises(ValueError):
        schedule(acts)
