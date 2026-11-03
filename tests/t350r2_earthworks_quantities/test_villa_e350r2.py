"""T-350 r2 hand-calculated fixture, villa E350R2 (NOT the development villa): three footing pits, two of them with
overlapping neat plans, the founding-level reading of the S01 kind (footing underside printed, the build-up below it).

Hand calculation (m; EG +-0.00 printed; footing underside -1.20 printed; underlay 0.05 + blinding 0.10 under it, the
blinding projecting 0.10 beyond the footing -> formation -1.35, depth 1.35):
  A footing 2.00 x 2.00 at (0, 0), H 0.50     neat (-0.10 .. 2.10)^2            = 4.84
  B footing 1.00 x 1.00 at (2.10, 0.50), H 0.40 neat 2.00 .. 3.20 x 0.40 .. 1.60  = 1.44
  A / B neat overlap 0.10 x 1.20 = 0.12 (one excavation, counted once)        -> 6.16
  C footing 1.50 x 1.00 at (5.00, 0), H 0.40   neat 1.70 x 1.20                  = 2.04   -> union 8.20 m2
  excavation 8.20 x 1.35 = 11.070 m3
  displacement: blinding one layer 8.20 x 0.10 = 0.820; underlay (4.00 + 1.00 + 1.50) x 0.05 = 0.325;
    footings 2.000 + 0.400 + 0.600 = 3.000; necks to EG: A 0.09 x 0.70 = 0.063, B 0.04 x 0.80 = 0.032,
    C 0.0625 x 0.80 = 0.050 -> 4.290 m3;  backfill 11.070 - 4.290 = 6.780 m3
  layers: backfill zone depth beside the footings = blinding top -1.25 to EG = 1.25 m -> 0.15: 9; 0.20: 7
  working space 0.50 (a sourced method sheet in this fixture): grown plans A 3.20^2 = 10.24, B 2.20^2 = 4.84,
    overlap 1.10 x 2.20 = 2.42, C 2.70 x 2.20 = 5.94 -> 18.60 m2; extra 10.40 x 1.35 = 14.040 m3
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t350r2"))
import earthworks_qty_v1 as E  # noqa: E402

SRC = "villa E350R2 fixture"
F = lambda v, s=E.DC: E.fact(v, s, SRC)  # noqa: E731
FOOT = [(0, 0, 2.0, 2.0), (2.10, 0.50, 3.10, 1.50), (5.0, 0.0, 6.5, 1.0)]
NEAT = [(x0 - .1, y0 - .1, x1 + .1, y1 + .1) for x0, y0, x1, y1 in FOOT]


def _mirror(R):
    return [(-x1, y0, -x0, y1) for x0, y0, x1, y1 in R]


def _rot90(R):
    return [(-y1, x0, -y0, x1) for x0, y0, x1, y1 in R]


def test_union_once_and_invariant_to_mirror_rotation_units():
    assert E.union_area(NEAT) == pytest.approx(8.20)
    assert sum((r[2] - r[0]) * (r[3] - r[1]) for r in NEAT) == pytest.approx(8.32)   # gross counts 0.12 twice
    assert E.union_area(_mirror(NEAT)) == pytest.approx(8.20)
    assert E.union_area(_rot90(NEAT)) == pytest.approx(8.20)
    assert E.union_area([tuple(v * 1000 for v in r) for r in NEAT], unit="mm") == pytest.approx(8.20)
    with pytest.raises(E.Refused, match="UNIT_NOT_DECLARED"):
        E.union_area(NEAT, unit="ft")


def test_excavation_backfill_layers():
    form = F(-1.20 - 0.05 - 0.10)
    dep = E.depth(F(0.0), form)
    assert dep["value"] == pytest.approx(1.35)
    ex = E.excavation(F(E.union_area(NEAT)), dep)
    assert ex["neat_m3"] == pytest.approx(11.070)
    disp = [F(0.820), F(0.325), F(3.000), F(0.063), F(0.032), F(0.050)]
    bf = E.backfill(E.fact(ex["neat_m3"], ex["neat_status"], SRC), disp)
    assert bf["value"] == pytest.approx(6.780) and bf["status"] == E.DC
    zd = F(1.35 - 0.10)
    assert E.layers(zd, E.fact(0.15, E.EST, SRC))["value"] == 9
    assert E.layers(zd, E.fact(0.20, E.EST, SRC))["value"] == 7


def test_working_space_union():
    grown = E.union_area(NEAT, grow=0.50)
    assert grown == pytest.approx(18.60)
    ex = E.excavation(F(8.20), F(1.35), working_space=E.fact(grown - 8.20, E.EST, "method sheet"))
    assert ex["working_space_m3"] == pytest.approx(14.040)
    assert ex["total_m3"] == pytest.approx(11.07 + 14.040)


def test_element_straddling_two_zones_is_split_once():
    # a strap 0.20 m3 whose 0.05 lies in pit C's plan and 0.15 in the strap trench: each zone takes its own part
    pit_part, trench_part = 0.05, 0.15
    assert pit_part + trench_part == pytest.approx(0.20)
    pit = E.backfill(F(2.754), [F(0.204), F(0.075), F(0.600), F(0.050), F(pit_part)])
    trench = E.backfill(F(0.60), [F(trench_part)])
    assert pit["value"] == pytest.approx(2.754 - 0.929 - 0.05)
    assert trench["value"] == pytest.approx(0.45)


def test_zero_depth_zone_is_a_calculated_zero_not_held():
    dep = E.depth(F(0.0), F(0.0))
    assert dep["value"] == 0.0 and dep["status"] == E.DC
    assert E.excavation(F(10.0), dep)["neat_m3"] == 0.0
    assert E.layers(dep, E.fact(0.15, E.EST, SRC))["value"] == 0


def test_missing_level_or_plan_holds_everything_downstream():
    dep = E.depth(F(0.0), E.fact(None, E.HELD, "founding level not printed"))
    assert dep["value"] is None and dep["status"] == E.HELD
    ex = E.excavation(F(8.20), dep)
    assert ex["neat_m3"] is None and ex["neat_status"] == E.HELD
    assert E.backfill(None, [F(1.0)])["value"] is None
    assert E.backfill(F(5.0), [F(1.0), E.fact(None, E.HELD, "neck section")])["value"] is None


def test_dry_mass_balance_procurement_from_the_placement_target():
    S = lambda v: E.fact(v, E.EST, "fixture soil data")  # noqa: E731
    r = E.dry_mass_balance(F(100.0), F(50.0), rho_insitu=S(1.60), rho_target=S(1.80), rho_loose_import=S(1.40),
                           rho_loose_spoil=S(1.35), reuse_fraction=S(1.0))
    assert r["required_dry_t"]["value"] == pytest.approx(90.0)
    assert r["imported_loose_m3"]["value"] == pytest.approx(0.0)
    assert r["surplus_insitu_m3"]["value"] == pytest.approx(43.75)          # payable basis: in situ
    assert r["surplus_loose_m3"]["value"] == pytest.approx(43.75 * 1.60 / 1.35)
    r = E.dry_mass_balance(F(100.0), F(50.0), rho_insitu=S(1.60), rho_target=S(1.80), rho_loose_import=S(1.40),
                           rho_loose_spoil=S(1.35), reuse_fraction=S(0.25))
    assert r["imported_loose_m3"]["value"] == pytest.approx(50.0 / 1.40)
    assert r["surplus_insitu_m3"]["value"] == pytest.approx(75.0)


def test_dry_mass_balance_adverse():
    S = lambda v, src="fixture soil data": E.fact(v, E.EST, src)  # noqa: E731
    acc = S(1.71, "acceptance 95 % x MDD")
    with pytest.raises(E.Refused, match="ACCEPTANCE_DENSITY_AS_PROCUREMENT"):
        E.dry_mass_balance(F(100.0), F(50.0), S(1.60), acc, S(1.40), S(1.35), S(1.0), rho_acceptance=acc)
    r = E.dry_mass_balance(F(100.0), F(50.0), S(1.60), S(1.80), S(1.40), S(1.35),
                           E.fact(None, E.HELD, "no geotechnical suitability evidence"))
    assert all(v["value"] is None and v["status"] == E.HELD for v in r.values())
