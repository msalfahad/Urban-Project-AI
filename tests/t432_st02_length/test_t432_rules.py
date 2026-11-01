"""T-432 length-basis rules (research/agents_t432/t432_rules.py) on a hand NON-Alsenan fixture.

Villa K432 (hypothetical): one CURVED flight (radial risers, lane r_in 1.0 / r_out 2.0, 90 deg, 8 risers, 8 treads of
11.25 deg), one STRAIGHT flight (6 risers, run 5 x 0.28 = 1.40, lane 1.0), a 1.0 x 1.0 corner landing, a short straight
flight (3 risers, run 2 x 0.28 = 0.56). Riser 0.175, 17 risers, rise 2.975. Hand figures:
  curved plan: inner 1.0 x pi/2 = 1.570796; centre 1.5 x pi/2 = 2.356194; outer 2.0 x pi/2 = 3.141593;
               riser-midpoint polyline 8 x 2 x 1.5 x sin(5.625 deg) = 2.352411; centre chord 1.5 x sqrt 2 = 2.121320
  landing:     inner 0; centre 0.5 + 0.5 = 1.0; outer 1.0 + 1.0 = 2.0; midpoints 0.5 x sqrt 2 = 0.707107
  CENTRE / PROFILE = 2.356194 + 1.40 + 1.0 + 0.56 + 2.975 = 8.291194
  OUTER  / PROFILE = 3.141593 + 1.40 + 2.0 + 0.56 + 2.975 = 10.076593
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t432"))
import t432_rules as R  # noqa: E402

CF = dict(INNER=1.570796, CENTRE=2.356194, RISERS=2.352411, OUTER=3.141593)
SF = {p: 1.40 for p in R.PATHS}
LD = dict(INNER=0.0, CENTRE=1.0, RISERS=0.707107, OUTER=2.0)
SA = {p: 0.56 for p in R.PATHS}


def stair(pieces=None, riser=0.175, n=17):
    pieces = pieces or [R.Piece("CF", "curved", 8, CF, dict(CENTRE=2.121320)), R.Piece("SF", "straight", 6, SF),
                        R.Piece("LD", "landing", 0, LD), R.Piece("SA", "straight", 3, SA)]
    return R.Stair(pieces, riser, n)


def test_hand_plan_figures_are_independent():
    assert CF["CENTRE"] == pytest.approx(1.5 * math.pi / 2, abs=1e-6)
    assert CF["RISERS"] == pytest.approx(8 * 2 * 1.5 * math.sin(math.radians(5.625)), abs=1e-6)
    assert LD["RISERS"] == pytest.approx(0.5 * math.sqrt(2), abs=1e-6)


def test_profile_and_plan_lengths():
    s = stair()
    assert s.rise == pytest.approx(2.975)
    assert R.length(s, "CENTRE", "PROFILE") == pytest.approx(8.291194, abs=1e-6)
    assert R.length(s, "OUTER", "PROFILE") == pytest.approx(10.076593, abs=1e-6)
    assert R.length(s, "INNER", "PLAN") == pytest.approx(1.570796 + 1.40 + 0.56, abs=1e-6)
    inc = math.hypot(2.356194, 1.4) + math.hypot(1.40, 1.05) + 1.0 + math.hypot(0.56, 0.525)
    assert R.length(s, "CENTRE", "INCLINED") == pytest.approx(inc, abs=1e-6)
    assert R.length(s, "CENTRE", "PROFILE_LANDING_IN_BOTH") == pytest.approx(8.291194 + 1.0, abs=1e-6)


def test_normal_row_length_traced_to_one_construction():
    res = R.classify(8.291194, R.constructions(stair()))
    assert res["state"] == "TRACED" and res["exact"] == ["CENTRE / PROFILE"]


def test_untraced_length_stays_unresolved_whole():
    res = R.classify(9.0, R.constructions(stair(), n_treads=15, going=0.28, landing_plans=dict(CENTRE=1.0)))
    assert res["state"] == "UNRESOLVED" and res["exact"] == []
    assert len(res["table"]) >= 30 and abs(res["nearest"][2]) > R.EXACT_TOL
    # his 1.0 x 9.0 x 0.25 against a drawn plan of 4.0 m2: term -1.25 m3 stays whole, never 0, never split
    out = R.restate_area_beyond(-1.25, 9.0, 1.0, 0.25, 4.0, res)
    assert out["unexplained_m3"] == -1.25 and out["terms"] == [dict(kind="UNRESOLVED", m3=-1.25)]


def test_nearest_is_not_chosen():
    res = R.classify(8.29, R.constructions(stair()))                  # 1.2 mm off the centre profile
    assert res["state"] == "UNRESOLVED" and res["nearest"][0] == "CENTRE / PROFILE"


def test_two_exact_constructions_are_ambiguous():
    res = R.classify(5.0, {"A": 5.0, "B": 5.0002, "C": 7.0})
    assert res["state"] == "AMBIGUOUS" and res["exact"] == ["A", "B"]


# ---------------------------------------------------------------------------------------------------- adverse cases

def test_rise_added_twice_on_a_landing_refused():
    with pytest.raises(R.RiseOnLandingError):
        R.Piece("LD", "landing", 6, LD)                              # the arriving flight's rise put on the landing
    with pytest.raises(R.RiseOnLandingError):
        R.length(stair(), "CENTRE", "PROFILE", rise_on_landing=True)
    with pytest.raises(R.Refused):                                    # every drawn riser once: 17 drawn, 23 owned
        R.Stair([R.Piece("CF", "curved", 8, CF), R.Piece("SF", "straight", 6, SF),
                 R.Piece("LD2", "straight", 6, LD | dict(INNER=0.01)), R.Piece("SA", "straight", 3, SA)], 0.175, 17)


def test_mixed_paths_refused():
    with pytest.raises(R.MixedPathError):
        R.length(stair(), dict(CF="OUTER", SF="CENTRE"), "PROFILE")


def test_chord_refused_as_curved_plan():
    with pytest.raises(R.ChordError):
        R.Piece("CF", "curved", 8, CF | dict(CENTRE=2.121320), dict(CENTRE=2.121320))


def test_units_and_missing_data_refused():
    with pytest.raises(R.Refused):
        stair(riser=175.0)                                            # millimetres read as metres
    with pytest.raises(R.Refused):
        R.Piece("CF", "curved", 8, {k: v for k, v in CF.items() if k != "OUTER"})   # missing path never 0
    with pytest.raises(R.Refused):
        R.Piece("SF", "straight", 6.0, SF)                            # float count
    with pytest.raises(R.Refused):
        R.Piece("SF", "straight", 0, SF)                              # flight without risers
    with pytest.raises(R.Refused):
        R.classify(None, {"A": 1.0})


def test_restate_traced_must_close():
    res = R.classify(8.291194, R.constructions(stair()))
    # row 1.0 x 8.291194 x 0.25 against drawn 4.0 m2: beyond = -(8.291194 - 4.0) x 0.25 = -1.072799 m3
    term = -(8.291194 - 4.0) * 0.25
    ok = R.restate_area_beyond(term, 8.291194, 1.0, 0.25, 4.0, res,
                               [dict(kind="RISE_IN_LENGTH", m3=-2.975 * 0.25), dict(kind="PLAN_BASIS", m3=term + 2.975 * 0.25)])
    assert ok["state"] == "TRACED" and ok["unexplained_m3"] == 0.0
    with pytest.raises(R.Refused):
        R.restate_area_beyond(term, 8.291194, 1.0, 0.25, 4.0, res, [dict(kind="RISE_IN_LENGTH", m3=-0.5)])
    with pytest.raises(R.Refused):
        R.restate_area_beyond(-9.9, 8.291194, 1.0, 0.25, 4.0, res)


def test_order_and_mirror_invariant():
    s = stair()
    rev = R.Stair(list(reversed(s.pieces)), 0.175, 17)              # walked down / mirrored plan: same pieces
    for p in R.PATHS:
        for b in ("PLAN", "PROFILE", "INCLINED", "PROFILE_LANDING_IN_BOTH"):
            assert R.length(rev, p, b) == pytest.approx(R.length(s, p, b), abs=1e-9)
