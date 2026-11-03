"""T-491 SITE_PREPARATION_V1 on hand-calculated non-Alsenan fixtures (villa Q, a 20 x 30 m plot) with adverse cases.

Hand calculations:
- perimeter 2 x (20 + 30) = 100.000 lm; one 4.00 m gate -> net fence 96.000 lm, 1 gate (task acceptance fixture).
- plot area 20 x 30 = 600.000 m2 (site clearance extent; formation compaction separate).
- L plot (0,0)-(30,0)-(30,10)-(15,10)-(15,20)-(0,20): area 30 x 10 + 15 x 10 = 450.000 m2; perimeter 30 + 10 + 15 +
  10 + 15 + 20 = 100.000 lm.
- programme 14 months, 1 cabin -> 14 nos x months; 3 trips / week x 52 weeks = 156 trips.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t491"))
import site_preparation_v1 as S  # noqa: E402

RECT = [(0, 0), (30, 0), (30, 20), (0, 20)]
L_PLOT = [(0, 0), (30, 0), (30, 10), (15, 10), (15, 20), (0, 20)]
OWNER_SCOPE = "owner 2026-11-02 17:20 (6)"


def by(rows):
    return {r["component"]: r for r in rows}


# ---------- normal cases ----------

def test_fence_100_less_one_4m_gate_is_96():
    r = by(S.hoarding(RECT, "m", gate_widths=[4.0]))
    assert r["HOARDING_GROSS_BOUNDARY"]["quantity"] == pytest.approx(100.0)
    assert r["HOARDING_FENCE_NET"]["quantity"] == pytest.approx(96.0)
    assert r["HOARDING_GATES"]["quantity"] == 1
    assert r["HOARDING_FENCE_NET"]["status"] == "DRAWING-CONFIRMED"


def test_fence_in_mm_equals_metres():
    mm = [(x * 1000, y * 1000) for x, y in RECT]
    r = by(S.hoarding(mm, "mm", gate_widths=[4000]))
    assert r["HOARDING_FENCE_NET"]["quantity"] == pytest.approx(96.0)


@pytest.mark.parametrize("transform", [
    lambda x, y: (-x, y),                                    # mirror
    lambda x, y: (x * math.cos(0.7) - y * math.sin(0.7), x * math.sin(0.7) + y * math.cos(0.7)),  # rotation
    lambda x, y: (x + 123456.0, y - 7890.0),                 # translation (drawing coordinates)
])
def test_mirror_rotation_translation_do_not_change_length_or_area(transform):
    poly = [transform(x, y) for x, y in L_PLOT]
    assert S.perimeter(poly) == pytest.approx(100.0)
    assert S.shoelace_area(poly) == pytest.approx(450.0)


def test_clockwise_and_closed_polygon_give_the_same_values():
    cw = list(reversed(RECT)) + [RECT[-1]]
    assert S.shoelace_area(cw) == pytest.approx(600.0)
    assert S.perimeter(cw) == pytest.approx(100.0)


def test_clearance_is_the_plot_area_and_separate_from_formation_compaction():
    rows = by(S.site_preparation({"plot_polygon": RECT, "clearance_scope_source": OWNER_SCOPE}))
    clr, fc = rows["SITE_CLEARANCE"], rows["FORMATION_COMPACTION"]
    assert clr["quantity"] == pytest.approx(600.0) and clr["unit"] == "m2" and clr["family"] == "B1-01"
    assert fc["quantity"] is None and fc["status"] == "HELD" and "T-350" in fc["source"]
    assert "never summed" in clr["note"]


def test_printed_clearance_limit_wins_over_the_plot_extent():
    r = S.site_clearance(RECT, "m", OWNER_SCOPE, printed_limit_m2=420.0)
    assert r["quantity"] == pytest.approx(420.0) and r["formula"] == "printed clearance limit"


def test_programme_and_logistics_given_compute_the_duration_lines():
    rows = by(S.site_preparation({
        "plot_polygon": RECT,
        "programme": {"construction_months": 14, "water_weeks": 52, "source": "programme rev A"},
        "logistics": {"guard_cabins": 1, "water_tanks": 2, "tanker_trips_per_week": 3, "source": "logistics plan"},
        "pour_sequence": {"pumped_pours": 9, "pour_days": 9, "source": "pour plan"},
    }))
    assert rows["GUARD_CABIN_OR_TENT"]["quantity"] == pytest.approx(14.0)
    assert rows["WATER_TANKER_TRIPS"]["quantity"] == pytest.approx(156.0)
    assert rows["WATER_TANKS"]["quantity"] == 2
    assert rows["CONCRETE_PUMP_POURS"]["quantity"] == 9 and rows["POUR_GENERATOR_DAYS"]["quantity"] == 9
    assert all(rows[k]["status"] == "PROJECT-SOURCED" for k in ("GUARD_CABIN_OR_TENT", "WATER_TANKER_TRIPS"))


def test_one_power_source_chosen_the_other_not_applicable():
    r = by(S.temporary_power(["GOVERNMENT_TEMPORARY_CONNECTION"], "contract cl. 4"))
    assert r["GOVERNMENT_TEMPORARY_CONNECTION"]["quantity"] == 1
    assert r["GENERATOR_FUEL"]["status"] == "NOT_APPLICABLE" and r["GENERATOR_FUEL"]["quantity"] is None


def test_insurance_follows_the_contract_and_handover_is_one_item():
    assert S.insurance(True, "contract cl. 9")["quantity"] == 1
    assert S.insurance(False, "contract cl. 9")["status"] == "NOT_APPLICABLE"
    h = S.site_handover()
    assert h["quantity"] == 1 and h["unit"] == "item"


# ---------- adverse cases ----------

def test_no_programme_keeps_every_duration_line_held_never_zero():
    rows = by(S.site_preparation({"plot_polygon": RECT}))
    for k in ("GUARD_CABIN_OR_TENT", "WATER_TANKER_TRIPS", "WATER_TANKS", "CONCRETE_PUMP_POURS",
              "POUR_GENERATOR_DAYS", "GENERATOR_FUEL", "GOVERNMENT_TEMPORARY_CONNECTION",
              "SITE_AND_WORKERS_INSURANCE"):
        assert rows[k]["status"] == "HELD" and rows[k]["quantity"] is None, k
        assert rows[k]["missing"] and rows[k]["formula"], k
        assert rows[k]["quantity"] != 0


def test_count_known_but_duration_missing_stays_held():
    r = S.duration_item("GUARD_CABIN_OR_TENT", "B1-07", "nos x months", count=1, duration=None,
                        count_source="logistics plan", duration_source=None)
    assert r["status"] == "HELD" and r["quantity"] is None
    assert any("programme" in m for m in r["missing"])


def test_a_value_without_its_source_is_not_used():
    r = S.duration_item("WATER_TANKER_TRIPS", "B1-07", "trips", count=3, duration=52,
                        count_source="logistics plan", duration_source=None)
    assert r["status"] == "HELD"


def test_unknown_gates_hold_the_net_with_the_gross_as_upper_bound():
    r = by(S.hoarding(RECT, "m", gate_widths=None))
    assert r["HOARDING_FENCE_NET"]["quantity"] is None and r["HOARDING_FENCE_NET"]["status"] == "HELD"
    assert r["HOARDING_FENCE_NET"]["at_most"] == pytest.approx(100.0)
    assert r["HOARDING_GATES"]["status"] == "HELD"


def test_stated_no_gate_gives_net_equal_to_gross():
    r = by(S.hoarding(RECT, "m", gate_widths=[]))
    assert r["HOARDING_FENCE_NET"]["quantity"] == pytest.approx(100.0) and r["HOARDING_GATES"]["quantity"] == 0


def test_both_power_sources_refused():
    with pytest.raises(S.RefusedInput):
        S.temporary_power(["GENERATOR_FUEL", "GOVERNMENT_TEMPORARY_CONNECTION"], "contract")


def test_power_choice_without_source_stays_held():
    r = by(S.temporary_power(["GENERATOR_FUEL"], None))
    assert r["GENERATOR_FUEL"]["status"] == "HELD" and r["GENERATOR_FUEL"]["quantity"] is None


@pytest.mark.parametrize("unit", [None, "ft", "M"])
def test_undeclared_unit_refused(unit):
    with pytest.raises(S.RefusedInput):
        S.perimeter(RECT, unit)


def test_degenerate_or_open_boundary_refused():
    with pytest.raises(S.RefusedInput):
        S.shoelace_area([(0, 0), (10, 0), (20, 0)])
    with pytest.raises(S.RefusedInput):
        S.perimeter([(0, 0), (10, 0)])


def test_gates_longer_than_the_boundary_or_non_positive_refused():
    with pytest.raises(S.RefusedInput):
        S.hoarding(RECT, "m", gate_widths=[60.0, 40.0])
    with pytest.raises(S.RefusedInput):
        S.hoarding(RECT, "m", gate_widths=[0.0])


def test_no_scope_source_holds_clearance_and_no_convention_extent():
    r = S.site_clearance(RECT, "m", in_scope_source=None)
    assert r["status"] == "HELD" and r["quantity"] is None
    with pytest.raises(S.RefusedInput):
        S.site_clearance(RECT, "m", OWNER_SCOPE, printed_limit_m2=-5)


def test_negative_programme_inputs_refused():
    with pytest.raises(S.RefusedInput):
        S.duration_item("X", "B1-07", "nos x months", count=1, duration=-2, count_source="a", duration_source="b")


def test_a_held_row_can_never_carry_a_quantity():
    with pytest.raises(AssertionError):
        S._row("X", "B1-07", "nos", 0, "HELD", "f", "s")
