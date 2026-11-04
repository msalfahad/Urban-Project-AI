"""T-497: EXCAVATION_ZONE_OWNERSHIP_V1 (R-T497-1) on a hand-calculated NON-Alsenan villa E497 (own figures, metres).

Plot 0..20 x 0..15. Dig order: footing pits (one union), footing zone F (a non-pit footing zone, like an open outline),
then the blinding-only ground-beam trench T1, cut 0.10 below the existing ground.
  T1     -0.80 .. 7.20 x 5.00 .. 5.50: 8.00 x 0.50 = 4.00 m2, of it 0.80 x 0.50 = 0.40 beyond the plot line (x < 0).
  P1     2.00 .. 4.20 x 4.00 .. 6.20 (grown 0.10): over T1 2.20 x 0.50 = 1.10 m2, all in the plot.
  P0     -0.50 .. 1.30 x 4.80 .. 6.60 (grown, straddles the plot line): over T1 1.80 x 0.50 = 0.90 m2, of it 0.25 beyond.
  F      5.50 .. 6.50 x 4.50 .. 5.20: over T1 1.00 x 0.20 = 0.20 m2.
  T1 owns 4.00 - 1.10 - 0.90 - 0.20 = 1.80 m2: in plot 1.65, beyond 0.15 -> 0.165 .. 0.180 m3 (in plot .. with beyond).
  The list-based way (V3.0.48 defect, F-C-T350R4-1): T1 less only the in-plot pits zone = 4.00 - 1.10 - 0.65 = 2.25 m2
  -> 0.185 .. 0.225 m3: counts F's 0.20 m2 and P0's beyond-plot 0.25 m2 twice (0.045 m3 at the high end).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t497"))

import zone_ownership_v1 as Z  # noqa: E402

PLOT = box(0, 0, 20, 15)
T1 = box(-0.80, 5.00, 7.20, 5.50)
P1 = box(2.00, 4.00, 4.20, 6.20)
P0 = box(-0.50, 4.80, 1.30, 6.60)
F = box(5.50, 4.50, 6.50, 5.20)
PITS = unary_union([P0, P1])


def adverse():
    return Z.own_plans([("footing pits", PITS), ("footing zone F", F), ("trench T1", T1)], PLOT)


# ================================================================================================ normal case
def test_disjoint_zones_each_own_their_whole_plan():
    a, b, t = box(1, 1, 3, 3), box(5, 1, 7, 3), box(1, 8, 9, 8.5)
    own = Z.own_plans([("pit A", a), ("pit B", b), ("trench", t)], PLOT)
    assert own["trench"]["own_m2"] == pytest.approx(4.00) and own["trench"]["given_up_m2"] == {}
    assert own["pit A"]["own_m2"] == pytest.approx(4.0) and own["pit B"]["beyond_plot_m2"] == pytest.approx(0.0)
    vin, vby = Z.strip_volume(own["trench"], 0.10)
    assert (vin, vby) == (pytest.approx(0.40), pytest.approx(0.0))


# ================================================================================================ adverse case
def test_trench_crossing_a_pit_a_footing_zone_and_a_beyond_plot_strip_every_m3_once():
    own = adverse()
    t = own["trench T1"]
    assert t["own_m2"] == pytest.approx(1.80)
    assert t["in_plot_m2"] == pytest.approx(1.65) and t["beyond_plot_m2"] == pytest.approx(0.15)
    assert t["given_up_m2"] == {"footing pits": pytest.approx(2.00), "footing zone F": pytest.approx(0.20)}
    vin, vby = Z.strip_volume(t, 0.10)
    assert (vin, vin + vby) == (pytest.approx(0.165), pytest.approx(0.180))
    # every m2 once: the owned plans add up to the union, and the pits keep their whole plan (dug first)
    total = unary_union([PITS, F, T1]).area
    assert sum(r["own_m2"] for r in own.values()) == pytest.approx(total)
    assert own["footing pits"]["own_m2"] == pytest.approx(PITS.area)


def test_list_based_subtraction_double_counts_what_the_rule_removes():
    """the V3.0.48 way (only the in-plot pits zone removed) is 0.045 m3 larger at the high end"""
    old = T1.difference(PITS.intersection(PLOT))
    hi_old, lo_old = old.area * 0.10, old.intersection(PLOT).area * 0.10
    assert (lo_old, hi_old) == (pytest.approx(0.185), pytest.approx(0.225))
    t = adverse()["trench T1"]
    assert hi_old - t["own_m2"] * 0.10 == pytest.approx(0.20 * 0.10 + 0.25 * 0.10)


def test_dig_order_decides_the_owner_never_the_sum():
    """the same two plans in the other order: the overlap moves owner, the total ground stays the union"""
    a = Z.own_plans([("trench T1", T1), ("footing zone F", F)], PLOT)
    b = Z.own_plans([("footing zone F", F), ("trench T1", T1)], PLOT)
    assert a["trench T1"]["own_m2"] == pytest.approx(4.00) and b["trench T1"]["own_m2"] == pytest.approx(3.80)
    assert sum(r["own_m2"] for r in a.values()) == pytest.approx(sum(r["own_m2"] for r in b.values()))


def test_mirrored_and_rotated_villa_same_areas():
    from shapely import affinity
    for tf in (lambda g: affinity.scale(g, -1, 1, origin=(0, 0)), lambda g: affinity.rotate(g, 37, origin=(3, 2))):
        own = Z.own_plans([("footing pits", tf(PITS)), ("footing zone F", tf(F)), ("trench T1", tf(T1))], tf(PLOT))
        t = own["trench T1"]
        assert (t["in_plot_m2"], t["beyond_plot_m2"]) == (pytest.approx(1.65), pytest.approx(0.15))


def test_millimetre_plans_are_the_callers_unit_not_metres():
    """units: a plan in mm gives mm2 (10^6 x); the rule never rescales, the caller states metres"""
    mm = lambda g: Polygon([(x * 1000, y * 1000) for x, y in g.exterior.coords])  # noqa: E731
    own = Z.own_plans([("footing zone F", mm(F)), ("trench T1", mm(T1))], mm(PLOT))
    assert own["trench T1"]["own_m2"] == pytest.approx(3.80e6)


def test_wholly_dug_zone_owns_a_calculated_zero_not_a_missing_value():
    own = Z.own_plans([("footing pits", PITS), ("small strip", box(2.5, 5.0, 3.5, 5.5))], PLOT)
    assert own["small strip"]["own_m2"] == 0.0 and own["small strip"]["given_up_m2"] == {
        "footing pits": pytest.approx(0.5)}


@pytest.mark.parametrize("zones,msg", [
    ([("a", T1), ("a", F)], "ZONE_TWICE"),
    ([], "NO_ZONE"),
    ([("a", T1), ("b", Polygon())], "BAD_PLAN"),
    ([("a", T1), ("b", None)], "BAD_PLAN"),
    ([("a", Polygon([(0, 0), (2, 2), (2, 0), (0, 2)]))], "BAD_PLAN"),       # bow-tie: invalid
])
def test_refused(zones, msg):
    with pytest.raises(Z.Refused, match=msg):
        Z.own_plans(zones, PLOT)


@pytest.mark.parametrize("depth", [0, -0.1, None, True])
def test_bad_depth_and_missing_plot_refused(depth):
    own = adverse()
    with pytest.raises(Z.Refused, match="BAD_DEPTH"):
        Z.strip_volume(own["trench T1"], depth)
    no_plot = Z.own_plans([("trench T1", T1)])
    with pytest.raises(Z.Refused, match="NO_PLOT"):
        Z.strip_volume(no_plot["trench T1"], 0.10)
