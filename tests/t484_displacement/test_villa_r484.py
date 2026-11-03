"""T-484 hand-calculated fixture, villa R484 (NOT the development villa): three footing pits, A and B with
overlapping neat plans, a strap B -> C, one ground beam of undetermined depth crossing A and B through both columns,
and one blinding-only beam crossing it.

Hand calculation (m; EG +-0.00; footing underside -1.20; underlay 0.05 + blinding 0.10 -> formation -1.35, pit
blinding top -1.25; projection 0.10):
  A 2.00 x 2.00 at (0, 0), H 0.50 (top -0.70), column 0.30 x 0.30 at (0.85 .. 1.15)^2
  B 1.00 x 1.00 at (2.10, 0.50), H 0.40 (top -0.80), column 0.20 x 0.20 at (2.50 .. 2.70) x (0.90 .. 1.10)
  C 1.00 x 1.00 at (5.00, 0.50), H 0.40 (top -0.80)
  zone = union of the neat plans (A / B overlap 0.10 x 1.20 counted once)
  necks to EG: A 0.09 x 0.70 = 0.063, B 0.04 x 0.80 = 0.032
  strap B -> C, 0.40 wide (y 0.80 .. 1.20) x 0.40 deep: in the margins x 3.10 .. 3.20 and 4.90 .. 5.00:
      2 x 0.10 x 0.40 = 0.080 m2 x 0.40 = 0.032 m3
  beam G1 (depth not printed), band y 0.85 .. 1.15 from x -1.00 to 4.00; over the zone x -0.10 .. 3.20:
      beam 3.30 x 0.30 = 0.99 - columns 0.09 - 0.04 = 0.86 m2; strip (sides +0.10) 3.30 x 0.50 = 1.65 - 0.13 = 1.52 m2
      high: over A 0.60 - 0.09 = 0.51 x 0.70 = 0.357; over B 0.30 - 0.04 = 0.26 x 0.80 = 0.208;
            over the margins 0.86 - 0.51 - 0.26 = 0.09 x 1.25 = 0.1125; strip sides 0.66 x 0.10 = 0.066 -> 0.7435
      low: blinding strip 1.52 x 0.10 = 0.152 (shallowest reading) or 0 (OPEN_LOW_ZERO)
  beam G2 (bottom on EG, blinding only), band x 1.50 .. 1.80 over A (y -0.10 .. 2.10):
      strip 0.50 x 2.20 = 1.10 - the part G1's strip already owns 0.50 x 0.50 = 0.25 -> 0.85 m2 x 0.10 = 0.085
  scenario: F10 2.80 x 1.40 and F 0.90 x 0.80 inside a 3.25 frame, grown 0.10: 4.80 + 1.10 - 0.65 = 5.25 m2 (sum 5.90)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t484"))
import displacement_remeasure_v1 as R  # noqa: E402

EG, FLOOR = 0.0, -1.25
A, B, C = box(0, 0, 2, 2), box(2.10, 0.50, 3.10, 1.50), box(5.0, 0.5, 6.0, 1.5)
TOPS = {"A": -0.70, "B": -0.80, "C": -0.80}
COLA, COLB = box(0.85, 0.85, 1.15, 1.15), box(2.50, 0.90, 2.70, 1.10)


def g(p):
    return p.buffer(0.10, join_style=2)


def world(tf=lambda x: x):
    a, b, c = tf(A), tf(B), tf(C)
    zone = unary_union([g(a), g(b), g(c)])
    cols = unary_union([tf(COLA), tf(COLB)])
    fps = [(a, TOPS["A"]), (b, TOPS["B"]), (c, TOPS["C"])]
    g1b = tf(box(-1.0, 0.85, 4.0, 1.15))
    g1s = tf(box(-1.0, 0.75, 4.0, 1.25))
    g2b = tf(box(1.50, -1.0, 1.80, 3.0))
    g2s = tf(box(1.40, -1.0, 1.90, 3.0))
    strap = tf(box(3.10, 0.80, 5.00, 1.20))
    return dict(a=a, b=b, c=c, zone=zone, cols=cols, fps=fps, g1b=g1b, g1s=g1s, g2b=g2b, g2s=g2s, strap=strap)


TRANSFORMS = {
    "plain": lambda x: x,
    "mirror": lambda x: affinity.scale(x, xfact=-1, yfact=1, origin=(0, 0)),
    "rotate 30": lambda x: affinity.rotate(x, 30, origin=(0, 0)),
    "rotate 90 + shift": lambda x: affinity.translate(affinity.rotate(x, 90, origin=(0, 0)), 1000.0, -250.0),
}


def pieces(w, rule1="OPEN_LOW_BLINDING", with_g2=True):
    ps = [{"id": "G1", "cat": "OPEN", "rule": rule1, "beam": w["g1b"], "strip": w["g1s"]}]
    if with_g2:
        ps.append({"id": "G2", "cat": "EXT", "rule": "BLINDING_ONLY", "beam": w["g2b"], "strip": w["g2s"]})
    return ps


@pytest.mark.parametrize("name", list(TRANSFORMS))
def test_beam_bounds_by_hand(name):
    w = world(TRANSFORMS[name])
    r = R.beam_solid_bounds(pieces(w, with_g2=False), w["cols"], w["zone"], w["fps"], FLOOR, EG, 0.10)
    assert r.status == R.CALC
    assert r.parts["OPEN"]["beam_m2"] == pytest.approx(0.86, abs=1e-9)
    assert r.parts["OPEN"]["strip_m2"] == pytest.approx(1.52, abs=1e-9)
    assert r.high == pytest.approx(0.7435, abs=1e-9)
    assert r.low == pytest.approx(0.152, abs=1e-9)


def test_low_zero_rule():
    w = world()
    r = R.beam_solid_bounds(pieces(w, "OPEN_LOW_ZERO", False), w["cols"], w["zone"], w["fps"], FLOOR, EG, 0.10)
    assert (r.low, r.high) == (pytest.approx(0.0), pytest.approx(0.7435))


@pytest.mark.parametrize("name", list(TRANSFORMS))
def test_crossing_counted_once(name):
    w = world(TRANSFORMS[name])
    r = R.beam_solid_bounds(pieces(w), w["cols"], w["zone"], w["fps"], FLOOR, EG, 0.10, ["OPEN", "EXT"])
    assert r.parts["EXT"]["strip_m2"] == pytest.approx(0.85, abs=1e-9)
    assert r.parts["EXT"]["low"] == r.parts["EXT"]["high"] == pytest.approx(0.085, abs=1e-9)
    assert r.high == pytest.approx(0.7435 + 0.085, abs=1e-9)
    # adverse: the sum of the two pieces measured separately counts the crossing twice (0.110 instead of 0.085)
    alone = R.beam_solid_bounds(pieces(w)[1:], w["cols"], w["zone"], w["fps"], FLOOR, EG, 0.10)
    assert alone.high == pytest.approx(0.110, abs=1e-9) and alone.high > r.parts["EXT"]["high"]


def test_straddling_piece_only_inside_counts():
    w = world()
    longer = dict(w, g1b=box(-5.0, 0.85, 4.5, 1.15), g1s=box(-5.0, 0.75, 4.5, 1.25))
    r1 = R.beam_solid_bounds(pieces(w, with_g2=False), w["cols"], w["zone"], w["fps"], FLOOR, EG, 0.10)
    r2 = R.beam_solid_bounds(pieces(longer, with_g2=False), w["cols"], w["zone"], w["fps"], FLOOR, EG, 0.10)
    assert r2.high == pytest.approx(r1.high) and r2.low == pytest.approx(r1.low)


def test_column_inside_piece_is_the_necks():
    w = world()
    no_cols = R.beam_solid_bounds(pieces(w, with_g2=False), box(99, 99, 99.1, 99.1), w["zone"], w["fps"], FLOOR,
                                  EG, 0.10)
    with_cols = R.beam_solid_bounds(pieces(w, with_g2=False), w["cols"], w["zone"], w["fps"], FLOOR, EG, 0.10)
    # the two column footprints over the footings: 0.09 x 0.70 + 0.04 x 0.80 = 0.095 m3 belong to the necks
    assert no_cols.high - with_cols.high == pytest.approx(0.095, abs=1e-9)
    na = R.neck_below_eg(0.09, TOPS["A"], EG)
    nb = R.neck_below_eg(0.04, TOPS["B"], EG)
    assert na.value + nb.value == pytest.approx(0.095)


def test_high_stops_on_the_footing():
    w = world()
    stop = R.beam_solid_bounds(pieces(w, with_g2=False), w["cols"], w["zone"], w["fps"], FLOOR, EG, 0.10)
    nostop = R.beam_solid_bounds(pieces(w, with_g2=False), w["cols"], w["zone"], [], FLOOR, EG, 0.10)
    # without the stop the beam would pass through footing + underlay: 0.51 x (1.25 - 0.70) + 0.26 x (1.25 - 0.80)
    assert nostop.high - stop.high == pytest.approx(0.51 * 0.55 + 0.26 * 0.45, abs=1e-9)


@pytest.mark.parametrize("name", list(TRANSFORMS))
def test_strap_ends(name):
    w = world(TRANSFORMS[name])
    feet = unary_union([w["a"], w["b"], w["c"]])
    r = R.strap_end_volume(w["strap"], w["zone"], feet, 0.40, 0.40, 0.40)
    assert r.parts["plan_m2"] == pytest.approx(0.08, abs=1e-9)
    assert r.value == pytest.approx(0.032, abs=1e-9)


def test_strap_drawn_width_differs_from_section():
    w = world()
    feet = unary_union([w["a"], w["b"], w["c"]])
    narrow = box(3.10, 0.81, 5.00, 1.19)                      # drawn 0.38, printed section 0.40
    r = R.strap_end_volume(narrow, w["zone"], feet, 0.40, 0.38, 0.40)
    assert r.value == pytest.approx(0.032, abs=1e-9)


def test_necks():
    assert R.neck_below_eg(0.09, -0.70, 0.0).value == pytest.approx(0.063)
    assert R.neck_below_eg(0.04, -0.80, 0.0, in_env_m2=0.01).value == pytest.approx(0.024)
    # a footing top above EG: a calculated 0 from geometry, not a held value
    z = R.neck_below_eg(0.09, 0.10, 0.0)
    assert z.status == R.CALC and z.value == 0.0


@pytest.mark.parametrize("args,reason", [
    ((None, -0.70, 0.0), "SECTION_MISSING"),
    ((0.09, None, 0.0), "LEVEL_MISSING"),
    ((0.09, -0.70, None), "LEVEL_MISSING"),
])
def test_neck_missing_is_held_never_zero(args, reason):
    r = R.neck_below_eg(*args)
    assert r.status == R.HELD and r.value is None and r.reason == reason


def test_missing_levels_are_held():
    w = world()
    r = R.beam_solid_bounds(pieces(w), w["cols"], w["zone"], w["fps"], None, EG, 0.10)
    assert r.status == R.HELD and r.low is None and r.high is None
    r = R.beam_solid_bounds(pieces(w), w["cols"], w["zone"], [(w["a"], None)], FLOOR, EG, 0.10)
    assert r.status == R.HELD and r.reason == "FOOTING_LEVEL_MISSING"
    bad = [dict(pieces(w)[0], rule="GUESS")]
    assert R.beam_solid_bounds(bad, w["cols"], w["zone"], w["fps"], FLOOR, EG, 0.10).status == R.HELD
    feet = unary_union([w["a"], w["b"], w["c"]])
    s = R.strap_end_volume(w["strap"], w["zone"], feet, None)
    assert s.status == R.HELD and s.value is None


def test_scenario_union_not_sum():
    f10, f = box(0, 0, 2.80, 1.40), box(2.35, 0, 3.25, 0.80)
    assert R.union_plan([g(f10), g(f)]) == pytest.approx(5.25, abs=1e-9)
    assert g(f10).area + g(f).area == pytest.approx(5.90, abs=1e-9)
    # clipped at a plot line along y = 0: the strip below it is not in the excavation of the plot
    assert R.union_plan([g(f10), g(f)], box(-5, 0, 10, 10)) == pytest.approx(5.25 - 0.10 * 3.45, abs=1e-9)  # x -0.10 .. 3.35
