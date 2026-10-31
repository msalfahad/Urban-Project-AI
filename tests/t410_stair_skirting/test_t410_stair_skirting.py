"""T-410: B7-07 / B7-08 stair skirting per side on a hand-calculated NON-Alsenan villa ('Villa K410'), normal and
adverse cases. No private input.

Villa K410 (hand calculation):
  F1 straight flight: 8 risers x 0.170, 7 goings x 0.290 -> run 2.030, rise 1.360; risers at s = 0, 0.29 .. 2.03.
     wall side W: wall face over s 0 .. 1.00, a window over 1.00 .. 2.03 (HELD); other side guarded (RL-K1).
     W-a: plan 1.00, risers at 0 / 0.29 / 0.58 / 0.87 = 4 -> zigzag 1.00 + 4 x 0.17 = 1.680;
          sloped 1.00 x hypot(2.03, 1.36) / 2.03 = 1.00 x 2.443461 / 2.03 = 1.203676.
     W-b (HELD): plan 1.03, risers 1.16 / 1.45 / 1.74 / 2.03 = 4 -> zigzag figure 1.710, quantity blank.
     whole side: zigzag 3.390 = run + rise; sloped 2.443461 = hypot(run, rise).
  L1 half landing, one level: wall side 1.400 -> 1.400 DRAWING-CONFIRMED in either form.
  C1 curved flight outer side r 1.80, 90 degrees, band of unknown role -> developed 2.827433 (pi/2 x 1.8), UNKNOWN.
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t410"))

import stair_skirting_sides as K  # noqa: E402

F1 = K.Flight("F1", 8, 0.17, 7, 0.29)


def villa(split=1.00):
    st = [
        K.Stretch("F1.Wa", "F1", "W", K.WALL, 0.0, split, binds=("K-F1-W-a",)),
        K.Stretch("F1.Wb", "F1", "W", K.HELD, split, F1.run, cause="window in the face, sill not printed",
                  binds=("K-F1-W-b",)),
        K.Stretch("F1.E", "F1", "E", K.OPEN, 0.0, F1.run, railing_run="RL-K1"),
        K.Stretch("L1.N", "L1", "N", K.WALL, plan=1.40, binds=("K-L1-N",)),
        K.Stretch("C1.OUT", "C1", "outer", K.UNKNOWN, curved_radius=1.80, curved_angle_deg=90.0,
                  cause="outer band, guard or string not established", binds=("K-C1-OUT",)),
    ]
    return {"F1": F1}, st


def by_id(rows):
    return {r["sid"]: r for r in rows}


def test_hand_calculation_villa_k410():
    r = by_id(K.measure(*villa()))
    a, b = r["F1.Wa"], r["F1.Wb"]
    assert a["risers_in"] == 4 and a["zigzag_lm"] == pytest.approx(1.680, abs=1e-6)
    assert a["sloped_lm"] == pytest.approx(1.203676, abs=1e-6)
    assert a["qty_lm"] is None and a["status"] == K.FORM_HELD          # form not fixed: blank, figures beside
    assert b["risers_in"] == 4 and b["zigzag_lm"] == pytest.approx(1.710, abs=1e-6) and b["qty_lm"] is None
    assert a["zigzag_lm"] + b["zigzag_lm"] == pytest.approx(F1.run + F1.rise, abs=1e-6)
    assert a["sloped_lm"] + b["sloped_lm"] == pytest.approx(math.hypot(2.03, 1.36), abs=1e-6)
    assert r["L1.N"]["qty_lm"] == pytest.approx(1.40) and r["L1.N"]["status"] == K.CONFIRMED
    assert r["C1.OUT"]["plan_lm"] == pytest.approx(math.pi / 2 * 1.8, abs=1e-6) and r["C1.OUT"]["qty_lm"] is None
    assert r["F1.E"]["qty_lm"] == 0.0 and r["F1.E"]["zigzag_lm"] is None
    t = K.totals(K.measure(*villa()))
    assert t["confirmed_horizontal_lm"] == pytest.approx(1.40) and t["held_risers"] == 4


def test_split_point_moves_risers_not_totals():
    # a riser exactly on the split belongs to the upper stretch; totals never change with the split
    for split in (0.58, 0.87, 1.00, 1.45):
        r = by_id(K.measure(*villa(split)))
        assert r["F1.Wa"]["risers_in"] + r["F1.Wb"]["risers_in"] == 8
        assert r["F1.Wa"]["zigzag_lm"] + r["F1.Wb"]["zigzag_lm"] == pytest.approx(3.39, abs=1e-6)
    assert by_id(K.measure(*villa(0.58)))["F1.Wa"]["risers_in"] == 2


def test_mirror_and_rotation_invariant():
    # run positions are measured along the flight: a mirrored / rotated stair gives the same stretch inputs
    base = K.measure(*villa())
    flights, st = villa()
    rot = [K.Stretch(**{**s.__dict__}) for s in st]
    assert K.measure(flights, rot) == base


def test_curved_side_as_chord_refused():
    with pytest.raises(K.SkirtingInputError, match="chord"):
        K.Stretch("C1.X", "C1", "outer", K.WALL, chord=2.545584)


def test_open_side_skirted_refused():
    with pytest.raises(K.SkirtingInputError, match="guarded"):
        K.Stretch("F1.E", "F1", "E", K.WALL, 0.0, F1.run, railing_run="RL-K1")


def test_winder_generated_refused():
    with pytest.raises(K.SkirtingInputError, match="S-9"):
        K.winder_region(1.2, 1.2, risers=5)


def test_held_as_zero_refused():
    flights, st = villa()
    rows = K.measure(flights, st)
    bad = [dict(r) for r in rows]
    next(r for r in bad if r["sid"] == "F1.Wb")["qty_lm"] = 0.0
    with pytest.raises(K.SkirtingInputError, match="never 0"):
        K.check(bad, flights, st)


def test_held_needs_a_cause():
    with pytest.raises(K.SkirtingInputError, match="cause"):
        K.Stretch("F1.Wb", "F1", "W", K.HELD, 1.0, 2.03)


def test_millimetres_refused():
    with pytest.raises(K.SkirtingInputError, match="metres"):
        K.Flight("F1", 8, 170.0, 7, 290.0)


def test_gap_overlap_and_double_binding_refused():
    flights, st = villa()
    gap = [st[0], K.Stretch("F1.Wb", "F1", "W", K.HELD, 1.10, F1.run, cause="window")] + st[2:]
    with pytest.raises(K.SkirtingInputError, match="gap or overlap"):
        K.measure(flights, gap)
    short = [st[0], K.Stretch("F1.Wb", "F1", "W", K.HELD, 1.00, 1.50, cause="window")] + st[2:]
    with pytest.raises(K.SkirtingInputError, match="covered"):
        K.measure(flights, short)
    dup = st + [K.Stretch("L1.N2", "L1", "N", K.WALL, plan=1.40, binds=("K-L1-N",))]
    with pytest.raises(K.SkirtingInputError, match="bound twice"):
        K.measure(flights, dup)


def test_stretch_outside_run_refused():
    with pytest.raises(K.SkirtingInputError, match="outside the run"):
        K.measure({"F1": F1}, [K.Stretch("F1.W", "F1", "W", K.WALL, 0.0, 2.50)])
