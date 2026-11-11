"""T-700 EARTHWORKS_ROUND2_V1 on villa E700 (hand-calculated, not the development villa).

Villa E700: one ground-slab block, FFL +0.75, floor build-up 0.05, slab T 0.10 -> underside +0.60, EG +-0.00.
  Z2 panel 150 m2 x 0.60 = 90.000 m3, layers ceil(0.60 / 0.15) = 4.
  Interior beam L 10, b 0.30, top +0.70, D 0.40, blinding 0.10, projection 0.10:
     blinding bottom +0.20 -> under-beam fill 0.30 x 10 x 0.20 = 0.600; projections above EG 2 x 0.10 x 10 x 0.10 =
     0.200 (solids in the panel fill) -> +0.400 m3.
  Same beam, D-33 (only the printed 0.40 as a lower bound): D = 0.40 -> +0.400; D = 0.60 (blinding bottom at EG)
     -> 0 - 0.200 = -0.200; D -> inf -> 0  => [-0.200, +0.400].
  Lift pit 3.00 x 3.00 = 9.00 m2; a neighbour footing pit owns 0.60 x 3.00 = 1.80 m2 of it (counted once) -> own 7.20;
     shell 1.60 x 1.60 = 2.56; base 0.40; screed 0.05 + blinding 0.10 below; underside >= 1.50 below EG:
     excavation >= 7.20 x 1.65 = 11.880; backfill >= (7.20 - 2.56) x (1.50 - 0.40) = 4.64 x 1.10 = 5.104.
  Trench: piece a 2.0 m2 strip, min 0.10, designer depth; piece b 1.0 m2, 0.15 .. 0.25; datum 1.67:
     low 0.200 + 0.150 = 0.350; high 3.340 + 0.250 = 3.590; without a datum: AT_LEAST 0.350.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t700"))
import earthworks_round2_v1 as R2  # noqa: E402

LIFT = 0.15


def beam(D=(0.40,), open_above=False, eg=0.0, outer=False, top=0.70):
    return R2.beam_term("GB1", 10.0, 0.30, top, 0.10, eg, 0.10, list(D), open_above=open_above, outer_proj=outer)


# --------------------------------------------------------------------------------------------- normal cases ----

def test_panel_150m2_x_060_is_90m3_four_layers():
    p = R2.panel_term("P1", 150.0, [0.75], 0.05, 0.10, 0.0)
    assert p["depth_m"] == [0.6, 0.6] and p["fill_m3"] == [90.0, 90.0]
    z = R2.z2_zone([p], [], LIFT)
    assert z["fill_m3"] == [90.0, 90.0] and z["layers_max"] == 4 and z["compaction_footprint_m2"] == [150.0, 150.0]


def test_interior_beam_under_fill_minus_projections():
    t = beam()
    assert t["fill_m3"] == [0.4, 0.4] and t["under_fill_m"] == [0.2, 0.2]
    z = R2.z2_zone([R2.panel_term("P1", 150.0, [0.75], 0.05, 0.10, 0.0)], [t], LIFT)
    assert z["fill_m3"] == [90.4, 90.4]
    assert z["compaction_footprint_m2"] == [153.0, 153.0]


def test_designer_depth_beam_is_bounded_both_ways():
    t = beam(open_above=True)
    assert t["fill_m3"] == [-0.2, 0.4]


def test_exterior_beam_outer_projection_only():
    # D 0.50 -> blinding bottom +0.10: under (0.30 + 0.10) x 10 x 0.10 = 0.400; inner projection 0.10 x 10 x 0.10
    assert beam(D=(0.50,), outer=True)["fill_m3"] == [0.3, 0.3]
    # D 0.70 sits on EG: blinding below EG, no fill, no solid
    assert beam(D=(0.70,), outer=True)["fill_m3"] == [0.0, 0.0]


def test_split_level_panel_and_court_reading():
    p = R2.panel_term("LOBBY", 10.0, [0.30, 0.75], 0.05, 0.10, 0.0)
    assert p["depth_m"] == [0.15, 0.6] and p["fill_m3"] == [1.5, 6.0]
    c = R2.panel_term("COURT", 8.0, [0.15, 0.75], 0.05, 0.10, 0.0)       # +0.15 paving on N.G.: no fill
    assert c["fill_m3"] == [0.0, 4.8]


def test_eg_sensitivity_moves_every_column():
    lo = R2.panel_term("P1", 150.0, [0.75], 0.05, 0.10, -0.10)["fill_m3"][0]
    hi = R2.panel_term("P1", 150.0, [0.75], 0.05, 0.10, +0.10)["fill_m3"][0]
    assert math.isclose(lo, 105.0) and math.isclose(hi, 75.0)
    assert beam(eg=0.10)["fill_m3"] == [0.1, 0.1]          # 0.3 x 10 x 0.10 - 0.2 x 10 x 0.10


def test_rotation_and_mirror_do_not_enter():
    # the module works on plan areas and lengths only: the same panel / run read from a mirrored or rotated sheet
    # gives the same numbers (the extract reads areas, never signed coordinates)
    a = R2.panel_term("P1", 150.0, [0.75], 0.05, 0.10, 0.0)
    b = R2.panel_term("P1-mirror", 150.0, [0.75], 0.05, 0.10, 0.0)
    assert a["fill_m3"] == b["fill_m3"]


def test_supplier_pit_at_least_overlap_counted_once():
    own = R2.own_plan(9.0, {"neighbour footing pit": 1.80})
    assert own == 7.2
    r = R2.supplier_pit_at_least(own, 2.56, 1.50, 0.40, {"screed": 0.05, "blinding": 0.10}, 0.0)
    assert r["kind"] == "AT_LEAST" and r["upper"] is None
    assert r["excavation_m3"] == 11.88 and r["backfill_m3"] == 5.104


def test_trench_bounds_with_and_without_datum():
    parts = [("a", 2.0, 0.10, None), ("b", 1.0, 0.15, 0.25)]
    assert R2.trench_bounds(parts, 1.67) == {"kind": "BOUNDED", "low_m3": 0.35, "high_m3": 3.59, "open": []}
    assert R2.trench_bounds(parts, None) == {"kind": "AT_LEAST", "low_m3": 0.35, "high_m3": None, "open": ["a"]}


def test_layers():
    assert R2.layers(0.60, 0.15) == 4 and R2.layers(0.85, 0.15) == 6 and R2.layers(0.15, 0.15) == 1
    assert R2.layers(0.0, 0.15) == 0


# -------------------------------------------------------------------------------------------- adverse cases ----

def test_missing_existing_ground_is_held_never_zero():
    with pytest.raises(R2.Round2Error, match="existing ground EG"):
        R2.panel_term("P1", 150.0, [0.75], 0.05, 0.10, None)
    with pytest.raises(R2.Round2Error, match="existing ground EG"):
        R2.supplier_pit_at_least(7.2, 2.56, 1.50, 0.40, {}, None)


def test_missing_floor_level_is_held():
    with pytest.raises(R2.Round2Error, match="no FFL reading"):
        R2.panel_term("P1", 150.0, [], 0.05, 0.10, 0.0)
    with pytest.raises(R2.Round2Error, match="FFL: missing"):
        R2.panel_term("P1", 150.0, [None], 0.05, 0.10, 0.0)


def test_millimetre_levels_refused():
    with pytest.raises(R2.Round2Error, match="not a level in metres"):
        R2.panel_term("P1", 150.0, [750.0], 50.0, 100.0, 0.0)
    with pytest.raises(R2.Round2Error):
        beam(D=(400.0,))
    with pytest.raises(R2.Round2Error):
        R2.trench_bounds([("a", 2.0, 0.10, None)], 1670.0)


def test_slab_below_eg_has_no_negative_fill():
    p = R2.panel_term("SUNK", 5.0, [0.10], 0.05, 0.10, 0.0)          # underside -0.05: an excavation, not Z2
    assert p["fill_m3"] == [0.0, 0.0]


def test_overlap_larger_than_plan_refused_and_shell_outside_refused():
    with pytest.raises(R2.Round2Error, match="exceed the plan"):
        R2.own_plan(9.0, {"a": 6.0, "b": 4.0})
    with pytest.raises(R2.Round2Error, match="shell plan"):
        R2.supplier_pit_at_least(2.0, 2.56, 1.50, 0.40, {}, 0.0)
    with pytest.raises(R2.Round2Error, match="shallower than the printed minimum"):
        R2.supplier_pit_at_least(7.2, 2.56, 1.50, 0.40, {}, 0.0, founding_level_m=-1.20)


def test_solids_exceeding_fill_refused():
    with pytest.raises(R2.Round2Error, match="< 0"):
        R2.z2_zone([], [beam(open_above=True)], LIFT)


def test_wiring_guards():
    ok = R2.wiring_row("B1-03", "L-x", "EW:B1-03:Z2", "PROPOSED_RANGE", "RANGE", None, 1.0, 2.0, "b", "m")
    assert ok["report_class"] == "HELD" and ok["zone"] == "Z2"
    with pytest.raises(R2.Round2Error, match="carries a value"):
        R2.wiring_row("B1-03", "L-x", "EW:B1-03:Z2", "HELD", "BLANK", 0.0, None, None, "", "missing")
    with pytest.raises(R2.Round2Error, match="geometric proof"):
        R2.wiring_row("B1-03", "L-x", "EW:B1-03:Z2", "HELD", "ZERO_BY_GEOMETRY", 0.0, None, None, "", "")
    with pytest.raises(R2.Round2Error, match="no high end"):
        R2.wiring_row("B1-02", "L-x", "EW:B1-02:PIT", "HELD", "AT_LEAST", None, 1.0, 2.0, "b", "m")
    with pytest.raises(R2.Round2Error, match="name the missing input"):
        R2.wiring_row("B1-02", "L-x", "EW:B1-02:PIT", "HELD", "AT_LEAST", None, 1.0, None, "b", "")
    with pytest.raises(R2.Round2Error, match="family"):
        R2.wiring_row("B1-02", "L-x", "EW:B1-03:PIT", "HELD", "AT_LEAST", None, 1.0, None, "b", "m")
