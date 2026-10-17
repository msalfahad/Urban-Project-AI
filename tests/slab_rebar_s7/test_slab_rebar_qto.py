"""Generic S7 slab rebar QTO tests (engine/source/slab_rebar_qto.py) - synthetic inputs only, no project data."""

import math

import pytest

from engine.source import slab_qto_authority as Q
from engine.source import slab_rebar_qto as S7


def _strips(poly, holes=(), d="X"):
    st = Q.bar_strips(poly, holes, d)
    return st, [(x["width"], 0.5 * (x["L0"] + x["L1"])) for x in st]


def _box(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# ------------------------------------------------------------------ rate integration
def test_rate_times_rectangle_integration():
    # 5 bars/m over a 3.6 m wide, 4.0 m long rectangle: 18 equivalent bars x 4.0 m = 72 m
    assert S7.rectangle_length_m(5, 3.6, 4.0) == pytest.approx(72.0, abs=1e-12)
    st, pairs = _strips(_box(0, 0, 4000, 3600), d="X")      # X bars run along x (4.0 m), width across y (3.6 m)
    r = S7.rate_strip_length(5, pairs)
    assert r["equivalent_count"] == pytest.approx(18.0, abs=1e-12)
    assert r["length_m"] == pytest.approx(72.0, abs=1e-9)
    assert r["mean_run_m"] == pytest.approx(4.0, abs=1e-12)
    assert r["physical_bbs_count"] == S7.UNRESOLVED
    # Σ(strip width × run) of a rectangular sanity fixture is the polygon area before any extension / curtailment
    assert S7.strip_coverage(pairs, 4000 * 3600)["reconciled"]


def test_rate_times_trapezoid_strip_integration():
    trap = [(0, 0), (6000, 0), (4000, 3000), (0, 3000)]      # area = (6 + 4) / 2 x 3 = 15 m2
    st, pairs = _strips(trap, d="X")
    r = S7.rate_strip_length(5, pairs)
    assert r["integral_m2"] == pytest.approx(15.0, abs=1e-9)
    assert r["length_m"] == pytest.approx(75.0, abs=1e-9)            # 5 /m x 15 m2
    assert r["length_m"] != pytest.approx(5 * 3.0 * 6.0)             # never the bounding rectangle (90 m)
    assert S7.strip_coverage(pairs, 15e6)["reconciled"]


def test_rate_times_l_shape_strip_integration():
    L = [(0, 0), (6000, 0), (6000, 2000), (2000, 2000), (2000, 5000), (0, 5000)]   # 12 + 6 = 18 m2
    for d in ("X", "Y"):
        st, pairs = _strips(L, d=d)
        assert len(st) >= 2
        r = S7.rate_strip_length(6, pairs)
        assert r["integral_m2"] == pytest.approx(18.0, abs=1e-9)
        assert r["length_m"] == pytest.approx(108.0, abs=1e-9)
        assert not S7.strip_overlaps([(x["id"] if "id" in x else k, x["t0"], x["t1"], x["s_start"][0],
                                       x["s_start"][1], x["s_end"][0], x["s_end"][1]) for k, x in enumerate(st)])


def test_no_integer_rounding_of_the_equivalent_count():
    r = S7.rate_strip_length(5, [(1550.0, 2000.0)])
    assert r["equivalent_count"] == pytest.approx(7.75, abs=1e-12)  # not 7, not 8
    assert r["equivalent_count"] != math.floor(r["equivalent_count"])
    assert r["length_m"] == pytest.approx(15.5, abs=1e-12)


def test_no_plus_one():
    r = S7.rate_strip_length(5, [(2000.0, 3000.0)])
    assert r["equivalent_count"] == 10.0                            # N x W, not N x W + 1
    assert r["length_m"] == pytest.approx(30.0, abs=1e-12)


def test_fifty_fifty_density():
    full = S7.rate_strip_length(5, [(3000.0, 4000.0)])
    cont = S7.rate_strip_length(5, [(3000.0, 4000.0)], fraction=0.5)
    curt = S7.rate_strip_length(5, [(3000.0, 3000.0)], fraction=0.5)   # 4.0 m less 2 x 0.125 x 4.0 m
    assert cont["equivalent_count"] + cont["equivalent_count"] == full["equivalent_count"]
    assert cont["length_m"] + curt["length_m"] == pytest.approx(30.0 + 22.5)
    assert S7.density_budget([0.5, 0.5])
    assert not S7.density_budget([0.5, 0.5, 0.5])
    with pytest.raises(S7.SlabRebarQtoError):
        S7.rate_strip_length(5, [(1000.0, 1000.0)], fraction=1.5)


def test_curtailment_ratio_is_project_source_and_convention_separate():
    a = S7.curtailment_authority(ratio_rule="P15-BOT-STOP-0.125L", span_stated_by_source=True,
                                 origin_stated_by_source=True)
    assert a["SOURCE_RATIO"] == 0.125 and a["SOURCE_RATIO_AUTHORITY"] == S7.PROJECT_SOURCE
    assert a["SPAN_BASIS_AUTHORITY"] == a["MEASUREMENT_ORIGIN_AUTHORITY"] == S7.PROJECT_SOURCE
    assert a["URBAN_CONVENTIONS"] == []
    b = S7.curtailment_authority(ratio_rule="P15-BOT-STOP-0.125L", span_stated_by_source=True,
                                 origin_stated_by_source=True, local_bar_line_rule="URBAN_LOCAL_BAR_LINE")
    assert b["SOURCE_RATIO_AUTHORITY"] == S7.PROJECT_SOURCE and b["URBAN_CONVENTIONS"] == ["URBAN_LOCAL_BAR_LINE"]


def test_one_third_ratio_is_project_source():
    a = S7.top_extent_authority(ratio_rule="NOTE-2", origin_stated_by_source=False, span_stated_by_source=False,
                                urban_rule="URBAN_TOP_V1")
    assert a["SOURCE_RATIO"] == pytest.approx(1 / 3) and a["SOURCE_RATIO_RULE"] == "NOTE-2"
    assert a["SOURCE_RATIO_AUTHORITY"] == S7.PROJECT_SOURCE
    with pytest.raises(S7.SlabRebarQtoError):                       # a ratio never takes an Urban authority
        S7.authority_record(ratio=1 / 3, ratio_rule="NOTE-2", ratio_authority=S7.URBAN_OWNER_MEASUREMENT_RULE)
    with pytest.raises(S7.SlabRebarQtoError):                       # nor a convention a project-source label
        S7.authority_record(conventions=["PROJECT_SOURCE_X"])


def test_support_face_measurement_convention_is_urban_where_the_source_is_silent():
    a = S7.top_extent_authority(ratio_rule="NOTE-2", origin_stated_by_source=False, span_stated_by_source=False,
                                urban_rule="URBAN_TOP_V1")
    assert a["MEASUREMENT_ORIGIN"].startswith("SUPPORT_FACE")
    assert a["MEASUREMENT_ORIGIN_AUTHORITY"] == S7.URBAN_OWNER_MEASUREMENT_RULE
    assert a["URBAN_CONVENTIONS"] == ["URBAN_TOP_V1"]
    b = S7.top_extent_authority(ratio_rule="NOTE-2", origin_stated_by_source=True, span_stated_by_source=True,
                                urban_rule="URBAN_TOP_V1")
    assert b["MEASUREMENT_ORIGIN_AUTHORITY"] == S7.PROJECT_SOURCE and b["URBAN_CONVENTIONS"] == []
    # extension = 1/3 x local clear span from the face, per side: 4.5 m span -> 1.5 m into the span
    ext = S7.rate_strip_length(5, [(2000.0, 4500.0 / 3.0)])
    assert ext["length_m"] == pytest.approx(5 * 2.0 * 1.5)


def test_local_top_override_needs_count_and_length_authority():
    blocked = S7.explicit_count_mass(3, 16, count_authority=S7.PROJECT_SOURCE, length_authority=S7.AUTHORITY_BLOCKED)
    assert blocked["kg"] is None and blocked["lane"] == S7.BLOCKED_UNQUANTIFIED
    no_len = S7.explicit_count_mass(3, 16, count_authority=S7.PROJECT_SOURCE, length_authority=S7.PROJECT_SOURCE)
    assert no_len["kg"] is None                                      # a count alone never makes mass
    ok = S7.explicit_count_mass(3, 16, count_authority=S7.PROJECT_SOURCE, length_authority=S7.PROJECT_SOURCE,
                                length_m=2.0)
    assert ok["kg"] == pytest.approx(3 * 2.0 * 256 / 162)
    # a finite count is never turned into a per-metre rate
    assert ok["count"] == 3 and "rate" not in ok


def test_same_role_generic_rule_not_double_counted():
    keys = [("SUP-1", "TOP_EXTENSION", "P-A"), ("SUP-1", "TOP_EXTENSION", "P-B"), ("SUP-1", "TOP_CROSSING", "A|B")]
    assert S7.duplicates(keys) == []
    assert S7.duplicates(keys + [("SUP-1", "TOP_EXTENSION", "P-A")]) == [("SUP-1", "TOP_EXTENSION", "P-A")]


def test_mismatch_left_right_runs_do_not_overlap():
    left = ("L-1", 0.0, 2000.0, 0.0, 0.0, 3000.0, 3000.0)          # panel left of the support face (x = 3000)
    right = ("R-1", 0.0, 2000.0, 3250.0, 3250.0, 7000.0, 7000.0)   # panel right of the far face (x = 3250)
    assert S7.strip_overlaps([left, right]) == []
    hidden_lap = ("R-1b", 0.0, 2000.0, 2600.0, 2600.0, 7000.0, 7000.0)   # a run pushed 400 mm past the face
    assert S7.strip_overlaps([left, hidden_lap]) == [("L-1", "R-1b")]


def test_no_hidden_lap_is_a_quantity():
    lane = S7.s7_lane(count_basis=S7.COUNT_RATE_DENSITY, length_authorities=[S7.AUTHORITY_BLOCKED])
    assert lane == S7.BLOCKED_UNQUANTIFIED and lane not in S7.MASS_LANES


def test_minimum_25mm_cover_is_project_basis_numeric():
    c = S7.cover_portion(True)
    assert c["lane"] == S7.PROJECT_BASIS_NUMERIC and c["note"] == S7.ACTUAL_LENGTH_NOT_ESTABLISHED
    assert S7.s7_lane(count_basis=S7.COUNT_SOURCE_EXPLICIT, length_authorities=[S7.MINIMUM_PROJECT_COVER],
                      physical_complete=True) == S7.PROJECT_BASIS_NUMERIC
    assert S7.cover_portion(False)["lane"] == S7.PROJECT_BASIS_QTO


def test_lanes_special_conflict_and_physical():
    assert S7.s7_lane(count_basis=S7.COUNT_RATE_DENSITY, length_authorities=[S7.PROJECT_GEOMETRY],
                      special=True) == S7.EXCLUDED_SPECIAL_STRUCTURE
    assert S7.s7_lane(count_basis=S7.COUNT_RATE_DENSITY, length_authorities=[S7.PROJECT_GEOMETRY],
                      conflict=True) == S7.SOURCE_CONFLICT
    assert S7.s7_lane(count_basis=S7.COUNT_RATE_DENSITY, length_authorities=[S7.PROJECT_GEOMETRY,
                                                                             S7.PROJECT_SOURCE]) == S7.PROJECT_BASIS_QTO
    # a rate is never SOURCE_DERIVED_PHYSICAL; an explicit count with source-only lengths and no blocked end is
    assert S7.s7_lane(count_basis=S7.COUNT_RATE_DENSITY, length_authorities=[S7.PROJECT_SOURCE],
                      physical_complete=True) == S7.PROJECT_BASIS_QTO
    assert S7.s7_lane(count_basis=S7.COUNT_SOURCE_EXPLICIT, length_authorities=[S7.PROJECT_SOURCE],
                      physical_complete=True) == S7.SOURCE_DERIVED_PHYSICAL
    assert S7.s7_lane(count_basis=S7.COUNT_SOURCE_EXPLICIT, length_authorities=[S7.PROJECT_SOURCE],
                      physical_complete=False) == S7.PROJECT_BASIS_QTO
    assert set(S7.NO_MASS_LANES) | set(S7.MASS_LANES) == set(S7.LANES)


def test_temperature_and_blocked_items_carry_no_kg():
    # a blocked temperature component never reaches the mass reconciliation
    with pytest.raises(S7.SlabRebarQtoError):
        S7.reconcile([{"kg": 1.0, "f": "A"}, {"kg": None, "f": "A"}], ["f"])
    assert S7.s7_lane(count_basis=S7.COUNT_UNRESOLVED, length_authorities=[]) == S7.BLOCKED_UNQUANTIFIED


def test_opening_clipping_uses_the_net_geometry():
    poly = _box(0, 0, 6000, 4000)
    hole = [_box(2000, 1000, 3000, 2500)]                           # 1.0 x 1.5 m opening
    st, pairs = _strips(poly, hole, d="X")
    r = S7.rate_strip_length(5, pairs)
    assert r["integral_m2"] == pytest.approx(24.0 - 1.5, abs=1e-9)  # clipped to the opening, not net area x kg/m2
    assert any(x["end_edge"][0] > 0 or x["start_edge"][0] > 0 for x in st)
    assert not S7.strip_overlaps([(k, x["t0"], x["t1"], x["s_start"][0], x["s_start"][1], x["s_end"][0],
                                   x["s_end"][1]) for k, x in enumerate(st)])


def test_unit_mass_is_d_squared_over_162():
    for d in (8, 10, 12, 16, 20):
        assert S7.unit_mass(d) == d * d / 162.0
    m = S7.mass(10, 162.0)
    assert m["kg"] == pytest.approx(100.0) and m["method"] == "D2_OVER_162"
    with pytest.raises(S7.SlabRebarQtoError):
        S7.unit_mass(0)


def test_strip_overlap_detects_crossing_trapezoids():
    a = ("a", 0.0, 1000.0, 0.0, 0.0, 1000.0, 3000.0)
    b = ("b", 0.0, 1000.0, 2000.0, 2000.0, 4000.0, 4000.0)         # a's far edge rises past b's near edge
    assert S7.strip_overlaps([a, b]) == [("a", "b")]
    c = ("c", 0.0, 1000.0, 3100.0, 3100.0, 4000.0, 4000.0)
    assert S7.strip_overlaps([a, c]) == []
    d_ = ("d", 1000.0, 2000.0, 0.0, 0.0, 1000.0, 1000.0)           # side by side across the bar: no overlap
    assert S7.strip_overlaps([a, d_]) == []


def test_reconciliation_by_diameter_floor_and_project():
    rows = [{"kg": 1.5, "dia": 10, "floor": "GF", "comp": "C1"}, {"kg": 2.25, "dia": 12, "floor": "GF", "comp": "C2"},
            {"kg": 0.25, "dia": 10, "floor": "1F", "comp": "C3"}]
    r = S7.reconcile(rows, ["dia", "floor", "comp"])
    assert r["ok"] and r["total"] == 4.0
    assert r["levels"]["dia"]["by"] == {10: 1.75, 12: 2.25}
    assert r["levels"]["floor"]["by"] == {"GF": 3.75, "1F": 0.25}


def test_forbidden_labels_and_total_name():
    for bad in ("VERIFIED_PHYSICAL", "as_built", "SOURCE_EXACT", "FINAL_SLAB_REBAR"):
        with pytest.raises(S7.SlabRebarQtoError):
            S7.check_label(bad)
    assert S7.check_label(S7.RESTRICTED_TOTAL) == "RESTRICTED_S7_PROJECT_BASIS_KG"


def test_blind_source_hits():
    assert S7.blind_source_hits("import csv\nx = 1\n", ["freelancer", "U-C4N"]) == []
    assert S7.blind_source_hits("p = 'freelancer.xlsx'", ["freelancer", "U-C4N"]) == ["freelancer"]
