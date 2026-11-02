"""T-449 round 2: REBAR_BASIS_RULES_V1 on a SYNTHETIC villa (VILLA-SYNTH-04), never the training villa.

Every expected value is a hand calculation from the fixture below (unit mass d^2 / 162 kg/m: d10 0.617284, d14
1.209877, d16 1.580247, d18 2.000000). Normal cases, then adverse ones: a missing schedule row (HELD, never 0), mm vs m
bar lengths, an mm diameter read as m, an undeclared / pending method, mirrored end order, a full-top-mesh panel, a
short span beside a long one (segment cap), an unknown far span, a held kg in a released sum.
"""

from __future__ import annotations

import pytest

from engine import project_config as pc
from engine.source import rebar_basis_rules_v1 as R


def f(fid, value, unit="none", kind="CATEGORY", status="APPROVED", src="DRAWING"):
    d = {"fact_id": fid, "version": 1, "quantity_kind": kind, "value": value, "unit": unit,
         "source": {"kind": src, "reference": "synthetic sheet S-07"},
         "approval": {"status": status, "date": "2026-10-01"}, "affected_lines": ["REBAR.SYNTH"],
         "confidence": "CONFIRMED" if status == "APPROVED" else "PROVISIONAL"}
    if status == "APPROVED":
        d["approval"]["by"] = "DESIGNER"
    return d


UM = f(R.F_UNIT_MASS, "D2_OVER_162", src="OWNER_DECISION")
UNIT_T = f(R.F_BOQ_UNIT, "t", src="OWNER_DECISION")
COVER = f(R.F_END_COVER, 40, unit="mm", kind="LENGTH")
CONT = f(R.F_TOP_CONT, 0.30, unit="ratio", kind="RATIO")
END = f(R.F_TOP_END, 0.25, unit="ratio", kind="RATIO")
TDIA = f(R.F_TOP_DIA, 10, unit="mm", kind="LENGTH")
ALL = (UM, UNIT_T, COVER, CONT, END, TDIA)


def cfg(*facts):
    return pc.parse_project_config({"schema": pc.SCHEMA, "project_id": "VILLA-SYNTH-04", "config_version": "0.1.0",
                                    "facts": list(facts or ALL)})


U10, U14, U16, U18 = 100 / 162, 196 / 162, 256 / 162, 324 / 162


# ---------------------------------------------------------------- bar populations

def test_column_main_bars_hand_value():
    r = R.bar_population(cfg(), count=8, length=4.50, d_mm=16)
    assert r.state == R.VALUED and r.value == pytest.approx(8 * 4.50 * U16, abs=1e-9)   # 56.888889 kg
    assert r.value == pytest.approx(56.888889, abs=1e-6)
    assert r.facts_used == (R.F_UNIT_MASS,)


def test_beam_bottom_bars_in_millimetres_hand_value():
    r = R.bar_population(cfg(), count=4, length=5200, d_mm=14, length_unit="mm")
    assert r.state == R.VALUED and r.value == pytest.approx(4 * 5.2 * U14, abs=1e-9)    # 25.165432 kg


def test_missing_schedule_row_is_held_never_zero():
    for row in (None, "NOT_PRINTED", "DUPLICATE_ROW"):
        r = R.bar_population(cfg(), count=8, length=4.5, d_mm=16, schedule_row=row)
        assert r.state == R.HELD and r.value is None and "never released" in r.held_reason


@pytest.mark.parametrize("missing", ["count", "length", "d_mm"])
def test_missing_count_length_or_diameter_is_held(missing):
    kw = dict(count=8, length=4.5, d_mm=16)
    kw[missing] = None
    r = R.bar_population(cfg(), **kw)
    assert r.state == R.HELD and r.value is None


def test_mm_figure_read_as_metres_is_refused():
    with pytest.raises(ValueError, match="UNIT_REFUSED"):
        R.bar_population(cfg(), count=4, length=5200, d_mm=14)          # 5200 'm'


def test_metre_figure_read_as_mm_is_refused():
    with pytest.raises(ValueError, match="UNIT_REFUSED"):
        R.bar_population(cfg(), count=4, length=5.2, d_mm=14, length_unit="mm")


def test_diameter_in_metres_is_refused():
    with pytest.raises(ValueError, match="UNIT_REFUSED"):
        R.bar_population(cfg(), count=8, length=4.5, d_mm=0.016)


def test_fractional_count_is_refused():
    with pytest.raises(ValueError):
        R.bar_population(cfg(), count=7.5, length=4.5, d_mm=16)


def test_undeclared_or_pending_unit_mass_method_holds():
    r = R.bar_population(cfg(UNIT_T), count=8, length=4.5, d_mm=16)
    assert r.state == R.HELD and "not declared" in r.held_reason
    r = R.bar_population(cfg(f(R.F_UNIT_MASS, "D2_OVER_162", status="PENDING", src="OWNER_DECISION")), count=8,
                         length=4.5, d_mm=16)
    assert r.state == R.HELD and "PENDING" in r.held_reason


def test_unknown_unit_mass_method_holds():
    r = R.bar_population(cfg(f(R.F_UNIT_MASS, "BY_SUPPLIER", src="OWNER_DECISION")), count=8, length=4.5, d_mm=16)
    assert r.state == R.HELD and r.value is None


def test_other_declared_method_changes_the_value():
    r = R.bar_population(cfg(f(R.F_UNIT_MASS, "D2_OVER_162_16", src="OWNER_DECISION")), count=8, length=4.5,
                         d_mm=16)
    assert r.value == pytest.approx(8 * 4.5 * 256 / 162.16, abs=1e-9)


# ---------------------------------------------------------------- held ranges

def test_readings_range_min_max_and_info_reading_never_an_end():
    r = R.readings_range({"A": 10.2, "B": 11.4, "C_info_kg": 9.0})
    assert r.state == R.HELD and (r.low, r.high) == (10.2, 11.4) and r.value is None


def test_no_reading_is_held_with_no_range():
    r = R.readings_range({})
    assert r.state == R.HELD and r.low is None and r.high is None


def test_development_range_note_multiples_hand_value():
    r = R.development_range(cfg(), count=12, d_mm=18, k_low=40, k_high=70)
    # 12 ends x 0.72 m x 2.0 = 17.28 kg .. 12 x 1.26 x 2.0 = 30.24 kg; held, never a value
    assert r.state == R.HELD and r.value is None
    assert (r.low, r.high) == (pytest.approx(17.28, abs=1e-9), pytest.approx(30.24, abs=1e-9))


def test_development_range_without_count_is_held_with_no_range():
    r = R.development_range(cfg(), count=None, d_mm=18, k_low=40, k_high=70)
    assert r.state == R.HELD and r.low is None


# ---------------------------------------------------------------- slab bottom-bar ends

def dev_ends(order=1):
    a = [R.BarEnd("A", "EDGE_BEAM", 0.30, bar=i, end="lo") for i in range(5)] + \
        [R.BarEnd("A", "CONTINUOUS", 0.25, bar=i, end="hi") for i in range(5)]
    b = [R.BarEnd("B", "EDGE_BEAM", 0.30, bar=i, end="lo") for i in range(6)] + \
        [R.BarEnd("B", "CONTINUOUS", 0.25, bar=i, end="hi") for i in range(6)]
    return (a + b)[::order]


def test_slab_development_bound_hand_value():
    r = R.slab_development_line(cfg(), dev_ends(), 10)
    # straight part 0.30 - 0.040 = 0.26 m; A 5 x 0.26 = 1.30 m, B 6 x 0.26 = 1.56 m; x 0.617284
    assert r.state == R.BOUND_PART_WITH_HELD and r.value is None
    assert r.low == pytest.approx(1.30 * U10, abs=1e-9) and r.high == pytest.approx(1.56 * U10, abs=1e-9)


def test_slab_development_mirrored_end_order_same_result():
    assert R.slab_development_line(cfg(), dev_ends(-1), 10) == R.slab_development_line(cfg(), dev_ends(), 10)


def test_slab_all_continuous_is_not_applicable_with_no_figure():
    r = R.slab_development_line(cfg(), [R.BarEnd("A", "CONTINUOUS", 0.25), R.BarEnd("B", "CONTINUOUS", 0.25)], 10)
    assert r.state == R.NOT_APPLICABLE and r.value is None and r.low is None


def test_slab_step_or_irregular_only_is_held():
    r = R.slab_development_line(cfg(), [R.BarEnd("A", "STEP_EDGE"), R.BarEnd("B", "IRREGULAR_SUPPORT")], 10)
    assert r.state == R.HELD and r.low is None


def test_slab_edge_cover_not_declared_holds_the_line():
    r = R.slab_development_line(cfg(UM), dev_ends(), 10)
    assert r.state == R.HELD and "CLEAR_COVER" in r.held_reason


def test_slab_unknown_support_class_refused():
    with pytest.raises(ValueError, match="SUPPORT_CLASS_REFUSED"):
        R.slab_development_line(cfg(), [R.BarEnd("A", "HALF_CONTINUOUS", 0.3)], 10)


def test_slab_edge_narrower_than_cover_refused():
    with pytest.raises(ValueError):
        R.slab_development_line(cfg(), [R.BarEnd("A", "EDGE_BEAM", 0.03)], 10)


# ---------------------------------------------------------------- slab top bars

def top_ends(n_a=3, n_b=4, ln=4.0, other=5.0):
    out = []
    for tag, n in (("A", n_a), ("B", n_b)):
        for i in range(n):
            out.append(R.BarEnd(tag, "CONTINUOUS", 0.25, ln, other, bar=i, end="lo"))
            out.append(R.BarEnd(tag, "EDGE_BEAM", 0.30, ln, None, bar=i, end="hi"))
    return out


def test_top_line_hand_value():
    r = R.slab_top_line(cfg(), top_ends())
    # per bar: continuous 0.30 x max(4, 5) = 1.50 + band 0.25 / 2 = 0.125; edge 0.25 x 4 = 1.00 + across 0.26 .. 0.30
    # low A 3 x 2.885 = 8.655 m; high B 4 x 2.925 = 11.70 m; x 0.617284 (declared top bar d10, not a mesh label)
    assert r.state == R.BOUND_PART_WITH_HELD and r.value is None and "hook-down legs" in r.held_reason
    assert r.low == pytest.approx(8.655 * U10, abs=1e-9) and r.high == pytest.approx(11.70 * U10, abs=1e-9)


def test_top_line_continuous_only_is_a_bound_with_nothing_held():
    ends = [R.BarEnd(t, "CONTINUOUS", 0.20, 3.0, 3.0, bar=i, end=s) for t, n in (("A", 2), ("B", 3))
            for i in range(n) for s in ("lo", "hi")]
    r = R.slab_top_line(cfg(), ends)
    # per bar 2 x (0.30 x 3.0 + 0.10) = 2.00 m (0.90 + 0.90 = 1.80 < 3.0: no cap); A 4.00 m, B 6.00 m
    assert r.state == R.BOUND and r.held_reason is None and r.value is None
    assert r.low == pytest.approx(4.0 * U10, abs=1e-9) and r.high == pytest.approx(6.0 * U10, abs=1e-9)


def test_top_line_mirrored_order_same_result():
    a, b = R.slab_top_line(cfg(), top_ends()[::-1]), R.slab_top_line(cfg(), top_ends())
    assert a.state == b.state
    assert a.low == pytest.approx(b.low, abs=1e-12) and a.high == pytest.approx(b.high, abs=1e-12)


def test_top_line_short_span_capped_at_its_clear_span():
    r = R.slab_top_line(cfg(), top_ends(1, 1, ln=2.0, other=6.0))
    # in-panel 0.30 x 6 = 1.80 + 0.25 x 2 = 0.50 = 2.30 > 2.0: low cut 0.30, high bound min(1.8, 2) + min(0.5, 2)
    # low = 1.80 + 0.125 + 0.50 + 0.26 - 0.30 = 2.385 m; high = 1.80 + 0.125 + 0.50 + 0.30 = 2.725 m
    assert r.low == pytest.approx(2.385 * U10, abs=1e-9) and r.high == pytest.approx(2.725 * U10, abs=1e-9)


def test_top_line_unknown_far_span_holds_that_side_only():
    ends = top_ends(1, 1, other=None)
    r = R.slab_top_line(cfg(), ends)
    # continuous side HELD (own span never substituted); edge side 1.00 + 0.26 .. 0.30
    assert r.state == R.BOUND_PART_WITH_HELD
    assert r.low == pytest.approx(1.26 * U10, abs=1e-9) and r.high == pytest.approx(1.30 * U10, abs=1e-9)


def test_top_line_full_top_mesh_is_unresolved_no_value():
    r = R.slab_top_line(cfg(), top_ends(), full_top_mesh=True)
    assert r.state == R.UNRESOLVED and r.low is None and r.value is None


def test_top_line_bar_size_not_declared_holds():
    r = R.slab_top_line(cfg(UM, COVER, CONT, END), top_ends())
    assert r.state == R.HELD and "BAR_DIA" in r.held_reason


def test_top_line_end_booked_twice_refused():
    with pytest.raises(ValueError, match="booked twice"):
        R.slab_top_line(cfg(), top_ends(1, 0) + top_ends(1, 0)[:1])


def test_top_line_all_ends_held_is_held():
    r = R.slab_top_line(cfg(), [R.BarEnd("A", "STEP_EDGE", None, 3.0), R.BarEnd("B", "OPENING_EDGE", None, 3.0)])
    assert r.state == R.HELD and r.low is None


# ---------------------------------------------------------------- tonnes at the boundary

def test_tonnes_once_from_unrounded_kg():
    r = R.to_tonnes(cfg(), [8 * 4.5 * U16, 4 * 5.2 * U14])
    assert r.state == R.VALUED and r.value == pytest.approx((56.888888889 + 25.165432099) / 1000, abs=1e-12)


def test_held_kg_never_enters_a_released_sum():
    with pytest.raises(ValueError):
        R.to_tonnes(cfg(), [56.888889, None])


def test_boq_unit_not_declared_holds():
    assert R.to_tonnes(cfg(UM), [1.0]).state == R.HELD


def test_module_imports_no_engine_or_research_module():
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(R))
    mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | {
        a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not any(m and (m.startswith("engine") or m.startswith("research")) for m in mods), mods
    assert R.DEFAULT_GUARD_CLASS == "UNWIRED_PRODUCER"


# ---------------------------------------------------------------- candidates and bar groups

def test_development_range_over_printed_bar_groups_hand_value():
    r = R.development_range_groups(cfg(), [(3, 16), (6, 16)], ends=2, k_low=40, k_high=70)
    # 2 ends x 9 bars d16: 18 x 0.64 m x 1.580247 = 18.204444 kg .. 18 x 1.12 m x 1.580247 = 31.857778 kg
    assert r.state == R.HELD and r.value is None
    assert r.low == pytest.approx(18 * 0.64 * U16, abs=1e-9) and r.high == pytest.approx(18 * 1.12 * U16, abs=1e-9)


def test_development_range_groups_without_ends_is_held():
    assert R.development_range_groups(cfg(), [(3, 16)], ends=0, k_low=40, k_high=70).low is None


def test_candidates_range_min_low_max_high():
    r = R.candidates_range({"LT5M": (12.196, 21.342), "EXT": (18.204, 31.858)})
    assert r.state == R.HELD and (r.low, r.high) == (12.196, 31.858) and r.value is None


def test_candidate_without_detail_holds_with_no_range():
    r = R.candidates_range({"LT5M": (12.196, 21.342), "CONC": None})
    assert r.state == R.HELD and r.low is None and "no defined figure" in r.held_reason
