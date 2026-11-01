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


# ---------------------------------------------------------------- r2: rule R-T410-4 (a column face is a face)
# Villa K410, second stair (hand calculation):
#   F2 straight flight: 6 risers x 0.170, 5 goings x 0.300 -> run 1.500, rise 1.020; risers at s = 0, 0.3 .. 1.5.
#      wall side: wall face 0 .. 0.60, a column 0.050 PROUD of the wall line over 0.60 .. 1.20, wall 1.20 .. 1.50.
#      column stretch: plan 0.600, risers 0.6 / 0.9 = 2, returns 2 x 0.050 = 0.100 (both ends on the wall face)
#        zigzag 0.600 + 2 x 0.170 + 0.100 = 1.040; sloped 0.600 x hypot(1.5, 1.02) / 1.5 + 0.100
#        = 0.600 x 1.813946 / 1.5 + 0.100 = 0.725578 + 0.100 = 0.825578.
#   L2 landing, one level, 1.200 long: wall 0 .. 0.700, a column 0.050 proud from 0.700 running PAST the landing edge
#      to 1.300: column face 0.500 + 1 return 0.050 (at the wall end; the far end is beyond the landing) = 0.550;
#      landing side 0.700 + 0.550 = 1.250 DRAWING-CONFIRMED in either form.
#   F3 flight 4 risers x 0.170, 3 goings x 0.300 (run 0.900): band of unknown role 0 .. 0.300 ('no face'), column
#      0.050 proud 0.300 .. 0.900: its west return meets the UNKNOWN stretch -> 0.050 HELD, not counted.

F2 = K.Flight("F2", 6, 0.17, 5, 0.30)
F3 = K.Flight("F3", 4, 0.17, 3, 0.30)


def villa_cols(l2_s2=None, f2_returns=0.100, f2_face="column"):
    st = [
        K.Stretch("F2.Wa", "F2", "W", K.WALL, 0.0, 0.60, binds=("K-F2-W-a",)),
        K.Stretch("F2.Wc", "F2", "W", K.WALL, 0.60, 1.20, face=f2_face, returns_lm=f2_returns, binds=("K-F2-W-c",)),
        K.Stretch("F2.Wb", "F2", "W", K.WALL, 1.20, 1.50, binds=("K-F2-W-b",)),
        K.Stretch("L2.S1", "L2", "S", K.WALL, 0.0, 0.70, binds=("K-L2-S-a",)),
        l2_s2 or K.Stretch("L2.S2", "L2", "S", K.WALL, 0.70, 1.20, face="column", returns_lm=0.050,
                           binds=("K-L2-S-b",)),
        K.Stretch("F3.S0", "F3", "S", K.UNKNOWN, 0.0, 0.30, no_face=True, cause="band of unknown role, no face",
                  binds=("K-F3-S-a",)),
        K.Stretch("F3.S1", "F3", "S", K.WALL, 0.30, 0.90, face="column", binds=("K-F3-S-b",)),
    ]
    faces = [K.Face("F2", "W", "column", 0.60, 1.20, 0.05, "KC1"), K.Face("L2", "S", "column", 0.70, 1.30, 0.05, "KC2"),
             K.Face("F3", "S", "column", 0.30, 0.90, 0.05, "KC3")]
    return {"F2": F2, "F3": F3}, st, faces


def test_column_face_proud_of_the_wall_returns_counted_once():
    flights, st, faces = villa_cols()
    r = by_id(K.measure(flights, st))
    c = r["F2.Wc"]
    assert c["face"] == "column" and c["risers_in"] == 2 and c["returns_lm"] == pytest.approx(0.100)
    assert c["zigzag_lm"] == pytest.approx(1.040, abs=1e-6) and c["sloped_lm"] == pytest.approx(0.825578, abs=1e-6)
    assert c["qty_lm"] is None and c["status"] == K.FORM_HELD
    assert r["L2.S2"]["qty_lm"] == pytest.approx(0.550) and r["L2.S2"]["status"] == K.CONFIRMED
    assert r["L2.S1"]["qty_lm"] + r["L2.S2"]["qty_lm"] == pytest.approx(1.250)
    chk = {f["ref"]: f for f in K.check_faces(st, faces)}
    assert chk["KC1"]["returns_confirmed_lm"] == pytest.approx(0.100) and chk["KC1"]["carrier"] == "F2.Wc"
    assert chk["KC2"]["returns_confirmed_lm"] == pytest.approx(0.050)       # far end beyond the landing: no return
    assert chk["KC3"]["returns_confirmed_lm"] == 0.0 and chk["KC3"]["returns_held_lm"] == pytest.approx(0.050)
    # the whole flight side still closes: zigzag = run + rise + returns
    tot = sum(r[s]["zigzag_lm"] for s in ("F2.Wa", "F2.Wc", "F2.Wb"))
    assert tot == pytest.approx(F2.run + F2.rise + 0.100, abs=1e-6)


def test_column_face_read_as_no_face_refused():
    bad = K.Stretch("L2.S2", "L2", "S", K.UNKNOWN, 0.70, 1.20, no_face=True,
                    cause="the wall face stops here: no wall face drawn", binds=("K-L2-S-b",))
    flights, st, faces = villa_cols(l2_s2=bad)
    K.measure(flights, st)                                  # the table alone cannot see the column layer ...
    with pytest.raises(K.SkirtingInputError, match="a column face is a face"):
        K.check_faces(st, faces)                            # ... the face check refuses the 'no face' cause


def test_proud_column_in_a_wall_face_stretch_refused():
    flights, st, faces = villa_cols(f2_face="wall", f2_returns=0.0)
    with pytest.raises(K.SkirtingInputError, match="face 'column'"):
        K.check_faces(st, faces)


def test_returns_missing_or_double_counted_refused():
    for wrong in (0.0, 0.200):
        flights, st, faces = villa_cols(f2_returns=wrong)
        with pytest.raises(K.SkirtingInputError, match="returns"):
            K.check_faces(st, faces)


def test_no_face_flag_only_on_unknown_and_returns_only_on_wall():
    with pytest.raises(K.SkirtingInputError, match="UNKNOWN"):
        K.Stretch("X", "F2", "W", K.WALL, 0.0, 0.6, no_face=True)
    with pytest.raises(K.SkirtingInputError, match="returns"):
        K.Stretch("X", "F2", "W", K.HELD, 0.0, 0.6, returns_lm=0.05, cause="window")
    with pytest.raises(K.SkirtingInputError, match="metres"):
        K.Face("F2", "W", "column", 0.6, 1.2, 50.0, "mm")
