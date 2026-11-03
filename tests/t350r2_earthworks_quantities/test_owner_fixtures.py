"""T-350 r2: the owner's hand-calculated earthworks examples (OWNER SESSION 2026-11-02 17:20 (5)) as fixtures of
EARTHWORKS_QTY_V1, plus the adverse cases it names (missing factor -> HELD, never 0). The owner's swell / factor / lift /
truck figures are ILLUSTRATIVE (17:20 (4)): here they are passed as sourced test inputs, never module defaults."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t350r2"))
import earthworks_qty_v1 as E  # noqa: E402

SRC = "owner example 2026-11-02 17:20 (illustrative)"
F = lambda v, s=E.DC: E.fact(v, s, SRC)  # noqa: E731
EST = lambda v: E.fact(v, E.EST, SRC)  # noqa: E731


def test_bulk_400m2_x_1_50():
    dep = E.depth(F(0.0), F(-1.50))
    ex = E.excavation(F(400.0), dep)
    assert ex["neat_m3"] == pytest.approx(600.0)
    assert E.loose_from_insitu(F(600.0), EST(0.20))["value"] == pytest.approx(720.0)
    bf = E.backfill(F(600.0), [F(100.0)])
    assert bf["value"] == pytest.approx(500.0)
    assert E.loose_from_compacted(bf, EST(1.25))["value"] == pytest.approx(625.0)


@pytest.mark.parametrize("d,lift,n", [(1.50, 0.15, 10), (1.50, 0.20, 8), (1.00, 0.20, 5), (0.60, 0.15, 4)])
def test_layers(d, lift, n):
    assert E.layers(F(d), EST(lift))["value"] == n


def test_pit_with_and_without_working_space():
    dep = E.depth(F(0.0), F(-1.50))
    neat = E.union_area([(0, 0, 2.0, 2.0)])
    grown = E.union_area([(0, 0, 2.0, 2.0)], grow=0.50)
    assert neat == pytest.approx(4.0) and grown == pytest.approx(9.0)
    ex = E.excavation(F(neat), dep, working_space=EST(grown - neat))
    assert ex["neat_m3"] == pytest.approx(6.00)
    assert ex["total_m3"] == pytest.approx(13.50)
    assert ex["total_status"] == E.EST                              # never stronger than its estimated part
    # backfill 13.50 - footing 2.00 - blinding 2.20 x 2.20 x 0.10 = 0.484
    assert E.backfill(E.fact(ex["total_m3"], E.EST, SRC), [F(2.00), F(0.484)])["value"] == pytest.approx(11.016)


def test_working_space_not_given_keeps_the_neat_quantity_and_holds_the_rest():
    ex = E.excavation(F(4.0), E.depth(F(0.0), F(-1.50)))
    assert ex["neat_m3"] == pytest.approx(6.0)
    assert ex["working_space_m3"] is None and ex["total_m3"] is None and ex["working_space_status"] == E.HELD


def test_placed_fill_150m2_x_0_60():
    v = 150.0 * 0.60
    assert v == pytest.approx(90.0)
    assert E.loose_from_compacted(F(v), EST(1.25))["value"] == pytest.approx(112.50)
    assert E.layers(F(0.60), EST(0.15))["value"] == 4


def test_120_insitu_to_150_loose_to_10_loads():
    lo = E.loose_from_insitu(F(120.0), EST(0.25))
    assert lo["value"] == pytest.approx(150.0)
    assert E.truckloads(lo, EST(15.0))["value"] == 10


def test_levels_use_existing_ground_never_finished_ground():
    # existing +-0.00, finished +0.20, formation -1.50: the depth is 1.50, not 1.70 (finished ground is no input)
    assert E.depth(F(0.0), F(-1.50))["value"] == pytest.approx(1.50)
    with pytest.raises(TypeError):
        E.depth(F(0.0), F(-1.50), finished=F(0.20))                 # the API has no finished-ground input at all


@pytest.mark.parametrize("call", [
    lambda: E.loose_from_insitu(F(600.0), E.fact(None, E.HELD, "no soil report")),
    lambda: E.loose_from_compacted(F(500.0), E.fact(None, E.HELD, "no factor")),
    lambda: E.truckloads(F(150.0), E.fact(None, E.HELD, "no truck")),
    lambda: E.layers(F(1.50), E.fact(None, E.HELD, "no lift")),
])
def test_missing_factor_is_held_never_zero(call):
    r = call()
    assert r["value"] is None and r["status"] == E.HELD


def test_refusals():
    with pytest.raises(E.Refused, match="HELD_AS_VALUE"):
        E.fact(0.2, E.HELD)
    with pytest.raises(E.Refused, match="ESTIMATE_WITHOUT_SOURCE"):
        E.fact(0.2, E.EST)
    with pytest.raises(E.Refused, match="FORMATION_ABOVE_EG"):
        E.depth(F(0.0), F(0.30))
    with pytest.raises(E.Refused, match="DISPLACEMENT_EXCEEDS_EXCAVATION"):
        E.backfill(F(1.0), [F(1.5)])
