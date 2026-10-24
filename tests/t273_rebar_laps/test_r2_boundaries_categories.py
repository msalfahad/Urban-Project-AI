"""T-273 r2 (owner acceptance s.6, 2026-10-24 18:38): splice-count boundaries, the five detailing categories, and the
column LAP / STARTER reconciliation of the S3 ledger.

Hand calculation (written before running; stock S = 12 m, lap 1.2 m = 75 x 16 mm, owner formula
laps = 0 if L <= S else ceil((L - S) / (S - lap)), S - lap = 10.8 m):
  12.00 -> 0 (within the stock);  12.01 -> ceil(0.01 / 10.8) = 1;  22.80 -> (10.8 / 10.8) = 1 exactly -> 1;
  22.81 -> ceil(10.81 / 10.8) = 2.   Frozen continuous_beams form ceil(L / S) - 1: 22.81 -> ceil(1.9008) - 1 = 1 (WRONG).
  33.60 = 12 + 2 x 10.8 -> 2;  33.61 -> 3.
Couplers (Villa G band 26.000 m, 4 T16): joints = ceil(26 / 12) - 1 = 2 per bar -> 8 couplers, no lap steel;
  net 4 x 26 x 256 / 162 = 164.345679 kg; a 24.000 m run -> 1 joint per bar (a lap of any length needs 2).
"""
from __future__ import annotations

import copy
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from engine.source import rebar_laps_v1 as RL

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t273"))

import t273r2_column_reconciliation as CREC  # noqa: E402

UM = {"method": "D2_OVER_162", "authority": "test", "selected_by": "test"}
BOUNDARY = [("12.00", 12000, 0), ("12.01", 12010, 1), ("22.80", 22800, 1), ("22.81", 22810, 2)]


# ------------------------------------------------------------------------------------------ s.6.3 boundary set
@pytest.mark.parametrize("text,mm,expected", BOUNDARY)
def test_boundary_float_literal_mm_integer_and_decimal_text(text, mm, expected):
    as_float = float(text)                          # the float literal
    assert RL.lap_count(as_float, 1.2, 12.0) == expected
    assert RL.lap_count(mm / 1000, 1.2, 12.0) == expected            # mm integer converted in float
    assert RL.lap_count_exact(as_float, 1.2, 12.0) == expected
    assert RL.lap_count_exact(text, "1.20", "12") == expected        # decimal text as read
    assert RL.lap_count_exact(Decimal(text), Decimal("1.2"), Decimal("12")) == expected
    assert RL.lap_count_exact(mm, 1200, 12000, unit="mm") == expected  # mm integers, exact


def test_boundary_lap_from_diameter_75d_t16():
    lap = 75 * 16 / 1000.0                            # 1.2 m from 75 d, computed not typed
    assert [RL.lap_count(float(t), lap, 12.0) for t, _, _ in BOUNDARY] == [0, 1, 1, 2]


def test_frozen_formula_fails_only_at_22_81():
    got = [RL.compare_with_frozen(float(t), 16, 75, 12.0) for t, _, _ in BOUNDARY]
    assert [g["laps_frozen"] for g in got] == [0, 1, 1, 1]
    assert [g["laps_v2"] for g in got] == [0, 1, 1, 2]
    assert got[3]["difference_m"] == pytest.approx(1.2)


def test_second_exact_boundary():
    assert RL.lap_count_exact("33.60", "1.2", "12") == 2
    assert RL.lap_count_exact("33.61", "1.2", "12") == 3
    assert RL.lap_count(33.6, 1.2, 12.0) == 2


@pytest.mark.parametrize("bad", [-1, "abc", float("nan"), float("inf"), True])
def test_length_refused(bad):
    with pytest.raises(RL.LapError):
        RL.length_exact_m(bad)


def test_unit_cm_refused_and_lap_ge_stock_blocked():
    with pytest.raises(RL.LapError):
        RL.lap_count_exact(2281, 120, 1200, unit="cm")
    with pytest.raises(RL.LapError):
        RL.lap_count_exact("24", "12", "12")
    with pytest.raises(RL.LapError):
        RL.lap_count_exact("24", None, "12")
    assert RL.lap_count_exact("12", None, "12") == 0


# ------------------------------------------------------------------------------------------ s.6.1 categories
def test_five_categories_and_ledger_mapping():
    assert len(RL.DETAILING_CATEGORIES) == 5
    for c in RL.DETAILING_CATEGORIES:
        assert RL.classify_detail({"category": c}) == c
    assert RL.classify_detail({"component": "LAP"}) == RL.LAP_CAT
    assert RL.classify_detail({"component": "STARTER"}) == RL.STARTER_CAT
    assert RL.classify_detail({"component": "ANCHORAGE"}) == RL.ANCHORAGE_CAT
    assert RL.classify_detail({"component": "HOOK_1"}) == RL.HOOK_CAT
    assert RL.classify_detail({"component": "COUPLER"}) == RL.COUPLER_CAT
    for bad in ({}, {"category": "DEVELOPMENT"}, {"component": "MAIN_BARS"}):
        with pytest.raises(RL.LapError):
            RL.classify_detail(bad)


def _note(category, governs=True):
    return {"tier": RL.NOTE, "lap_d": 70, "kind": RL.EXACT, "governs": governs, "ref": "VG-S-01 note 9",
            "category": category}


@pytest.mark.parametrize("cat", [RL.STARTER_CAT, RL.ANCHORAGE_CAT, RL.HOOK_CAT, RL.COUPLER_CAT])
def test_source_of_another_category_never_a_lap(cat):
    r = RL.resolve_lap({"element_kind": "BEAM", "dia_mm": 16}, [_note(cat)])
    assert r["state"] == RL.HELD and r["lap_m"] is None
    assert any(f.startswith("CATEGORY_MISMATCH") for f in r["findings"])


def test_source_of_another_category_does_not_block_the_convention_fallback_finding():
    r = RL.resolve_lap({"element_kind": "BEAM", "dia_mm": 16},
                       [_note(RL.STARTER_CAT), {"tier": RL.CONVENTION, "governs": True}], convention_allowed=True)
    assert r["state"] == RL.PROVISIONAL and r["lap_m"] == pytest.approx(0.96)     # 60 x 16 mm, labelled PROVISIONAL
    assert any(f.startswith("CATEGORY_MISMATCH") for f in r["findings"])


def test_lap_category_source_applied():
    r = RL.resolve_lap({"element_kind": "BEAM", "dia_mm": 16}, [_note(RL.LAP_CAT)])
    assert r["state"] == RL.DRAWING_CONFIRMED and r["lap_m"] == pytest.approx(1.12)


def _group(**kw):
    g = {"element": "VG-GB1", "floor": "FDN", "element_kind": "GROUND_BEAM", "bar_type": "B", "dia_mm": 16, "bars": 4,
         "run_m": 26.0, "run_status": RL.DRAWING_CONFIRMED, "continuity": "CONTINUOUS", "ref": "VG-S-03"}
    g.update(kw)
    return g


@pytest.mark.parametrize("cat", [RL.HOOK_CAT, RL.ANCHORAGE_CAT, RL.STARTER_CAT])
def test_hook_anchorage_starter_length_is_not_a_lap_row(cat):
    lap = RL.resolve_lap({"element_kind": "GROUND_BEAM", "dia_mm": 16}, [_note(RL.LAP_CAT)])
    with pytest.raises(RL.LapError):
        RL.lap_row(_group(detail_category=cat), stock_m=12.0, stock_ref="t", lap=lap, unit_mass_cfg=UM)


def test_coupler_row_hand_values():
    r = RL.lap_row(_group(splice_type=RL.SPLICE_COUPLER, coupler_ref="VG-S-05 coupler note"), stock_m=12.0,
                   stock_ref="t", lap={"state": RL.HELD}, unit_mass_cfg=UM)
    assert r["category"] == RL.COUPLER_CAT
    assert (r["splices_per_bar"], r["couplers_pcs"]) == (2, 8)
    assert r["lap_kg"] == 0.0 and r["added_length_m"] == 0.0
    assert r["net_kg"] == pytest.approx(164.345679, abs=1e-6) and r["installed_kg"] == r["net_kg"]
    assert r["installed_t"] == 0.164346 and r["status"] == RL.DRAWING_CONFIRMED


def test_coupler_count_differs_from_lap_count_at_24m():
    c = RL.lap_row(_group(run_m=24.0, splice_type=RL.SPLICE_COUPLER), stock_m=12.0, stock_ref="t",
                   lap={"state": RL.HELD}, unit_mass_cfg=UM)
    assert c["splices_per_bar"] == 1 and c["status"] == RL.HELD           # coupler not printed -> HELD pieces
    assert any("coupler type" in f for f in c["findings"])
    assert RL.lap_count(24.0, 0.8, 12.0) == 2


def test_coupler_within_stock_and_unknown_splice_type():
    c = RL.lap_row(_group(run_m=12.0, splice_type=RL.SPLICE_COUPLER), stock_m=12.0, stock_ref="t",
                   lap={"state": RL.HELD}, unit_mass_cfg=UM)
    assert c["status"] == RL.NOT_REQUIRED and c["couplers_pcs"] == 0
    held = RL.lap_row(_group(splice_type=RL.SPLICE_COUPLER, continuity="NOT_ESTABLISHED"), stock_m=12.0,
                      stock_ref="t", lap={"state": RL.HELD}, unit_mass_cfg=UM)
    assert held["status"] == RL.HELD and held["couplers_pcs"] is None              # never 0
    with pytest.raises(RL.LapError):
        RL.lap_row(_group(splice_type="WELDED"), stock_m=12.0, stock_ref="t", lap={"state": RL.HELD},
                   unit_mass_cfg=UM)


def test_policy_names_categories():
    p = RL.policy_record()
    assert p["detailing_categories"] == list(RL.DETAILING_CATEGORIES)
    assert "a source of another detailing category used as a lap" in p["never"]


# ------------------------------------------------------------------------------------------ s.6.2 column ledger
@pytest.fixture(scope="module")
def rec():
    return CREC.build()


def test_column_ledger_counts_as_the_owner_states(rec):
    assert rec["lap_rows"] == 56 and rec["lap_rows_by_state"] == {"PROVISIONAL": 54, "LOWER_BOUND": 2}
    assert rec["starter_rows"] == 36 and rec["starter_rows_by_state"] == {"PROVISIONAL": 29, "BLOCKED": 5,
                                                                           "LOWER_BOUND": 2}
    assert rec["foundation_lap_rows"] == 30 and rec["foundation_lap_kg"] == pytest.approx(288.897, abs=1e-3)
    assert rec["chains_with_starter_and_foundation_lap"] == 30


def test_every_lap_zone_counted_exactly_twice(rec):
    assert rec["failures"] == []
    assert rec["footing_top_zones_counted_twice"] == 31                   # 36 starters - 5 BLOCKED (footing unknown)
    one = next(c for c in rec["chains"] if c["chain_id"] == "COLPOS-X01-Y01-2138-7462")
    ft = one["zones"][0]
    # F footing H 300: footing top -1.50 + 0.30 = -1.20; core 1.00 + 1.20 = 2.20 m from it; starter 230 + 300 + 640
    assert (ft["footing_top_level_mm"], ft["core_bottom_level_mm"], ft["core_interval_mm"]) == (-1200, -1200, 2200)
    assert ft["layers_in_lap_zone"] == 2 and ft["lap_zone_kg_each_layer"] == pytest.approx(8.081, abs=1e-3)


def test_70d_scenario_is_two_categories_and_a_scenario(rec):
    assert rec["scenario_70D_minus_40D_lap_kg"] == pytest.approx(372.736, abs=1e-3)
    assert rec["scenario_70D_minus_40D_anchorage_kg"] == pytest.approx(268.243, abs=1e-3)
    assert rec["scenario_70D_flag_total_kg"] == pytest.approx(640.99, abs=0.02)     # STR-COL-026 (row rounding)
    assert rec["scenario_70D_status"].startswith("SCENARIO")


def test_core_basis_finding(rec):
    f = rec["finding_core_basis"]
    assert f["chains"] == 31 and f["kg_if_formation_at_limit"] == pytest.approx(-74.381, abs=1e-3)


def _synthetic(core_from_footing_bottom=False, base_lap=False):
    H, n, d = 400, 6, 16
    kgm = d * d / 162
    st_len = (H - 70) + 300 + 40 * d
    ls = {"lap_rule": {"current_D": 40}, "anchorage_rule": {"current_D": 40},
          "starter_rule": {"bottom_cover_mm": 70, "foot_mm": 300, "projection_D": 40},
          "rows": [{"chain_id": "VG-C1", "component": "STARTER", "floor": "FOUNDATION", "count": n, "dia_mm": d,
                    "length_per_piece_mm": st_len, "kg": n * st_len / 1000 * kgm, "total_length_m": n * st_len / 1000,
                    "release_state": "PROVISIONAL", "part_id": "SEG-VG-C1-FOUNDATION|STARTER",
                    "footing": {"depth_mm": H, "ref": "VG-F1", "state": "DEFINED"}},
                   {"chain_id": "VG-C1", "component": "LAP", "floor": "FOUNDATION", "count": n, "dia_mm": d,
                    "length_per_piece_mm": 640, "kg": n * 0.64 * kgm, "total_length_m": n * 0.64,
                    "kg_at_alternative": n * 1.12 * kgm, "release_state": "PROVISIONAL",
                    "part_id": "SEG-VG-C1-FOUNDATION|LAP_BOTTOM" if base_lap else "SEG-VG-C1-FOUNDATION|LAP_TOP"}]}
    core_len = 2500 - H + (H if core_from_footing_bottom else 0)
    main = [{"chain_id": "VG-C1", "component": "MAIN_BARS", "floor": "FOUNDATION", "count": n, "dia_mm": d,
             "kg": n * core_len / 1000 * kgm, "total_length_m": n * core_len / 1000,
             "interval": {"length_mm": core_len, "state": "LOWER_BOUND",
                          "basis": f"GF FFL +1.00 m minus founding level <= -1.50 m minus footing depth "
                                   f"{0.0 if core_from_footing_bottom else float(H)} mm"}},
            {"chain_id": "VG-C1", "component": "MAIN_BARS", "floor": "GF", "count": n, "dia_mm": d, "kg": 1.0,
             "total_length_m": 1.0, "interval": {"length_mm": 4000, "state": "ESTABLISHED",
                                                 "basis": "printed floor-to-floor 4.0 m (FFL basis)"}}]
    return ls, main


def test_synthetic_villa_counted_twice():
    ls, main = _synthetic()
    r = CREC.build(ls, main)
    assert r["failures"] == [] and r["footing_top_zones_counted_twice"] == 1


def test_synthetic_core_from_footing_bottom_is_caught_as_triple_count():
    ls, main = _synthetic(core_from_footing_bottom=True)
    r = CREC.build(ls, main)
    assert {f["check"] for f in r["failures"]} >= {"core_starts_at_footing_top", "footing_top_zone_counted_twice"}


def test_synthetic_base_lap_beside_a_starter_is_caught():
    ls, main = _synthetic(base_lap=True)
    r = CREC.build(copy.deepcopy(ls), main)
    assert any(f["check"] == "lap_is_top_splice" for f in r["failures"])
