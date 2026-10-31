"""T-393: railing runs released segment by segment (R-T393-1 turns, R-T393-2 single binding, R-T393-3 guard side).

Synthetic 'Villa D' (not the development villa), hand calculation in research/agents_t393/t393_railing_runs.py:
dog-leg 3.20 m, 2 x 10 risers 0.160 / going 0.280 -> pitch line sqrt(2.520^2 + 1.440^2) = 2.902413 lm per flight;
level half-landing turn round a 0.20 m well with 0.05 m bands = 0.250 across + 0.025 + 0.025 = 0.300 lm; gallery guard
3.000 lm; total 9.104826 lm. Adverse: a landing return bound to both flights is refused; a winder turn with a rise and no
drawn profile is HELD (None, never 0) and does not stop the drawn flights; an undrawn guard on a walled side is refused;
mm read as m refused; mirror / rotation of the turn coordinates gives the same length.
"""

from __future__ import annotations

import csv
import importlib.util
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_P = ROOT / "research" / "agents_t393" / "t393_railing_runs.py"
_T164 = ROOT / "research" / "agents_t164" / "RAILINGS_T164.csv"


def _mod():
    spec = importlib.util.spec_from_file_location("t393_railing_runs", _P)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("t393_railing_runs", mod)
    spec.loader.exec_module(mod)
    return sys.modules["t393_railing_runs"]


R = _mod()


def test_villa_d_total_hand_calculation():
    t = R.totals(R.villa_d())
    assert t["confirmed_lm"] == pytest.approx(2 * math.hypot(2.52, 1.44) + 0.300 + 3.000, abs=1e-6)
    assert t["confirmed_lm"] == pytest.approx(9.104826, abs=1e-6)
    assert t["held"] == [] and t["unknown"] == []


def test_flight_pitch_not_plan():
    assert R.flight_pitch(10, 0.160, 0.280) == pytest.approx(2.902413, abs=1e-6)
    assert R.flight_pitch(10, 0.160, 0.280) > 9 * 0.280          # never the plan projection


@pytest.mark.parametrize("args", [
    (0.0, 0.30, 0.05, 2.95, 2.95, 3.00),        # north end
    (0.0, 0.30, 0.05, 0.05, 0.05, 0.00),        # south end
    (0.0, -0.30, 0.05, -2.95, -2.95, -3.00),    # mirrored both axes
    (10.0, 10.30, 0.05, 102.95, 102.95, 103.0),  # translated
])
def test_turn_plan_invariant(args):
    assert R.well_end_turn_plan(*args) == pytest.approx(0.300, abs=1e-9)


def test_turn_plan_mm_scaled():
    # same geometry in mm gives 300 (the caller converts once; no hidden unit guess)
    assert R.well_end_turn_plan(0.0, 300.0, 50.0, 2950.0, 2950.0, 3000.0) == pytest.approx(300.0)


def test_adverse_landing_return_bound_twice_refused():
    segs = R.villa_d() + [R.Segment("RD-1", "T1b", "same return listed under flight 2", 0.300, R.CONFIRMED, "x",
                                    binds=("LANDING-RETURN-1",))]
    with pytest.raises(R.RunInputError, match="bound twice"):
        R.totals(segs)


def test_adverse_winder_turn_held_never_zero_and_flights_still_released():
    w = R.turn_segment("RD-1", "T2", "winder turn", 0.300, 0.480, False, "plan", ("WINDER-1",),
                       "rail profile over the winders not drawn")
    assert w.status == R.HELD and w.length_m is None and w.plan_m == pytest.approx(0.300)
    t = R.totals(R.villa_d() + [w])
    assert t["confirmed_lm"] == pytest.approx(9.104826, abs=1e-6)   # drawn parts not held by the turn
    assert t["held"] == ["T2"]


def test_turn_with_drawn_profile_is_3d():
    s = R.turn_segment("RD-1", "T3", "ramped turn", 0.300, 0.400, True, "detail", ("T3",), "")
    assert s.length_m == pytest.approx(0.5)


def test_turn_rise_unknown_held():
    s = R.turn_segment("RD-1", "T4", "turn", 0.300, None, False, "plan", ("T4",), "")
    assert s.status == R.HELD and s.length_m is None and s.missing


def test_adverse_guard_on_walled_side_refused():
    with pytest.raises(R.RunInputError, match="WALL_HANDRAIL_NOT_SPECIFIED"):
        R.undrawn_wall_guard("W1")
    with pytest.raises(R.RunInputError):
        R.guard_segment("RD-1", "W2", "wall side", 3.0, "WALL", False, "none", ("W2",))
    ok = R.guard_segment("RD-1", "W3", "drawn wall rail", 3.0, "WALL", True, "detail", ("W3",))
    assert ok.length_m == 3.0


def test_held_segment_cannot_carry_a_number():
    with pytest.raises(R.RunInputError):
        R.Segment("X", "H1", "held", 0.0, R.HELD, "src", "missing fact")
    with pytest.raises(R.RunInputError):
        R.Segment("X", "H2", "held", None, R.HELD, "src", "")          # HELD needs the exact missing fact


def test_mm_read_as_m_refused():
    with pytest.raises(R.RunInputError):
        R.Segment("X", "M1", "mm as m", 3300.0, R.CONFIRMED, "src")
    with pytest.raises(R.RunInputError):
        R.flight_pitch(10, 160.0, 0.280)


def test_reconcile_names_causes_and_prints_remainder():
    rows = list(csv.DictReader(_T164.open()))
    by = {}
    for r in rows:
        if r["LENGTH_LM"]:
            by[r["RUN"]] = by.get(r["RUN"], 0.0) + float(r["LENGTH_LM"])
    ours = by["RL-05"] + by["RL-06"] + by["RL-08"]
    assert ours == pytest.approx(19.766, abs=1e-6)
    rec = R.reconcile(ours, 18.95, [("RL-08 D1", by["RL-08"])])
    assert rec["diff"] == pytest.approx(0.816, abs=1e-6)
    assert rec["unexplained"] == pytest.approx(-0.226, abs=1e-6)   # printed, never absorbed


def test_check_entrypoint_passes():
    assert R._check() == 0
