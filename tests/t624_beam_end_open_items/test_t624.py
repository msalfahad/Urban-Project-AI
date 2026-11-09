"""T-624: closing the beam-band pieces T-614 r2 / T-619 left open (R-T624-1). Synthetic non-Alsenan fixtures
(hand-calculated) + the committed development-villa result (internal arithmetic, no coordinates); the private rebuild
runs only when the decoded drawing is present."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import LineString, Polygon, box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t624"))
import t624_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t624" / "out"
RES = OUT / "T624_BEAM_END_OPEN_ITEMS.json"
PRIVATE_DXF = ROOT.parent / "private" / "st7757.dxf"

# ---- fixture (hand), not the training villa: an L-shaped arrangement.
#  Beam A 0.30 wide x 0.60 deep along +x (y 0 .. 0.30); its route G rectangle stops at x 4.00.
#  Column K 0.50 long x 0.20 deep at x 4.00 .. 4.50, y 0 .. 0.20 (covers 0.20 of the 0.30 band).
#  Neighbour beam B 0.25 wide along y at x 4.50 .. 4.75 (A frames into it).
#  The strip beside K inside A's band: x 4.00 .. 4.50, y 0.20 .. 0.30 = 0.050 m2 -> x 0.60 = 0.030 m3.
DA = 0.60
K = box(4.00, 0.0, 4.50, 0.20)
STRIP = box(4.00, 0.20, 4.50, 0.30)
REGION = box(4.00, 0.0, 4.50, 0.30).difference(K)         # the add region beyond A's rectangle up to B, net of K


def test_named_add_places_the_strip_beside_the_column():
    rec = R.place_in_add(STRIP, REGION, 0.030, DA)
    assert rec["verdict"] == "BILLED_BY_ADD"
    assert rec["in_add_m2"] == pytest.approx(0.050, abs=1e-12)
    assert rec["region_vs_add_m3"] == pytest.approx(0.0, abs=1e-12)


def test_add_with_a_wrong_value_does_not_place_it():
    # a printed add of 0.020 m3 cannot be this 0.050 m2 x 0.60 region (0.030 m3): disagreement, never 'billed'
    assert R.place_in_add(STRIP, REGION, 0.020, DA)["verdict"] == "ADD_REGION_DISAGREES"


def test_piece_outside_the_add_region_is_not_billed_by_it():
    other = box(0.0, 0.30, 0.50, 0.40)                       # 0.05 m2 elsewhere: 0.030 m3 outside the region
    assert R.place_in_add(other, REGION, 0.030, DA)["verdict"] == "PARTLY_IN_ADD"


def test_adverse_tolerance_larger_than_the_piece_is_refused():
    # a 0.0005 m2 sliver entirely outside the region: 0.0003 m3 < the 1 dm3 tolerance; 'billed' would rest only on
    # the tolerance being larger than the piece itself -> refused
    sliver = box(5.00, 0.0, 5.005, 0.10)
    with pytest.raises(R.Refused):
        R.place_in_add(sliver, REGION, 0.030, DA)


def test_add_without_depth_is_refused():
    with pytest.raises(R.Refused):
        R.place_in_add(STRIP, REGION, 0.030, None)


@pytest.mark.parametrize("op", ["mirror", "rotate", "mm"])
def test_placement_invariant_under_mirror_rotation_and_units(op):
    # mm: the drawing in millimetres is converted to metres (x 0.001) before any measure, as the census does
    f = {"mirror": lambda g: affinity.scale(g, -1, 1, origin=(0, 0)),
         "rotate": lambda g: affinity.rotate(g, 37, origin=(0, 0)),
         "mm": lambda g: affinity.scale(affinity.scale(g, 1000, 1000, origin=(0, 0)), 0.001, 0.001, origin=(0, 0))}[op]
    rec = R.place_in_add(f(STRIP), f(REGION), 0.030, DA)
    assert rec["verdict"] == "BILLED_BY_ADD"
    assert rec["in_add_m2"] == pytest.approx(0.050, rel=1e-9)
    assert R.place_in_add(f(STRIP), f(REGION), 0.020, DA)["verdict"] == "ADD_REGION_DISAGREES"


def test_run_value_decomposes_into_its_named_terms_and_a_missing_term_is_refused():
    # GF-like run: rectangles 3.1039 + 0.6832, gap 0.1163, end 0.1812 = 4.0846 (no single 'add' value is a region)
    assert R.decompose_run(4.0846, {"rect": 3.1039, "held": 0.6832, "gap": 0.1163, "end": 0.1812}) == \
        pytest.approx(0.0, abs=1e-9)
    with pytest.raises(R.Refused):
        R.decompose_run(4.0846, {"rect": 3.1039, "held": 0.6832, "gap": 0.1163})


# ---- (c) end gap: A's top face stops at x 3.975 inside a crossing beam C (face y = 0.15), its bottom face y = 0
#  runs on to column K2 at x 4.00. Region x 3.975 .. 4.00, y 0 .. 0.15 = 0.025 x 0.15 = 0.00375 m2 -> 0.00225 m3.
K2 = box(4.00, 0.0, 4.40, 0.30)
C_BAND = box(3.80, 0.15, 4.00, 1.50)                       # crossing beam C's drawn band (its face at y = 0.15)
BAND_STRIP = box(3.975, 0.0, 4.00, 0.30)
SHARED = LineString([(3.975, 0.0), (3.975, 0.30)])
LINES = [LineString([(0.0, 0.0), (10.0, 0.0)]),            # A's bottom face, drawn on to the column and past it
         LineString([(3.80, 0.15), (4.00, 0.15)]),         # C's face
         LineString([(4.00, 0.0), (4.00, 0.30)])]          # K2's outline face


def test_end_gap_enclosed_by_drawn_lines_is_measured_for_the_band():
    reg = R.end_gap_region(BAND_STRIP, [C_BAND], [K2])
    assert reg.area == pytest.approx(0.00375, abs=1e-12)
    cov = R.drawn_cover(reg, LINES, shared=SHARED)
    assert cov == pytest.approx(1.0, abs=1e-9)
    rec = R.classify_end_gap(reg, cov, DA)
    assert rec["state"] == "MEASURED" and rec["m3"] == pytest.approx(0.00225, abs=1e-12)


def test_adverse_end_gap_with_an_undrawn_side_stays_held_never_zero():
    reg = R.end_gap_region(BAND_STRIP, [C_BAND], [K2])
    cov = R.drawn_cover(reg, LINES[1:], shared=SHARED)      # the bottom face is not drawn there
    rec = R.classify_end_gap(reg, cov, DA)
    assert rec["state"] == "HELD" and rec["m3"] is None and rec["bound_m3"] == pytest.approx(0.00225, abs=1e-12)


def test_end_gap_without_depth_is_held():
    reg = R.end_gap_region(BAND_STRIP, [C_BAND], [K2])
    assert R.classify_end_gap(reg, 1.0, None)["state"] == "HELD"


# ---- (d) a band skewed 5 deg meeting an orthogonal 0.20 x 1.00 column: the wedge between the rectangle's square
#  end and the column face. Faces end on the column -> drawn wedge, valued, even below T-229 SQUARE_MAX 0.002 m2.
def test_wedge_is_measured_when_the_drawn_faces_reach_the_column_even_below_the_square_threshold():
    col = box(10.0, -0.30, 10.20, 0.70)
    a = math.radians(5.0)
    w = 0.40 * 0.40 * math.tan(a) / 2           # 0.40 wide band: wedge 0.5 x 0.40 x 0.40 tan 5 = 0.006999 m2
    small = 0.15 * 0.15 * math.tan(a) / 2       # 0.15 wide band: 0.000984 m2 (< 0.002)
    ends = [(10.0, 0.0), (10.0, 0.40)]
    assert R.faces_reach_column(ends, col)
    assert R.classify_wedge(w, True, 0.75)["m3"] == pytest.approx(w * 0.75, abs=1e-12)
    rec = R.classify_wedge(small, True, 0.75)
    assert rec["class"] == "DRAWN_WEDGE" and rec["t229_would_call_square"] is True


def test_adverse_wedge_whose_faces_stop_short_of_the_column_is_not_valued():
    col = box(10.0, -0.30, 10.20, 0.70)
    assert not R.faces_reach_column([(9.97, 0.0), (9.97, 0.40)], col)      # 30 mm short
    assert R.classify_wedge(0.001, False, 0.75)["class"] == "FIT_RESIDUAL"
    assert R.classify_wedge(0.004, False, 0.75)["m3"] is None               # unexplained: never a value


# ---- (e) a junction square deducted from one band and inside the other's rectangle
OWNER = box(0.0, 0.0, 3.0, 0.90)            # deeper beam rectangle (0.85), billed whole
OTHER_BILLED = box(3.0, 0.0, 5.0, 0.20)     # shallow beam billed plan with the square deducted
TIP = box(2.98, 0.0, 3.0, 0.076)            # 0.00152 m2 inside OWNER only


def test_tip_inside_the_owner_rectangle_is_billed_once_and_the_companion_closes_to_zero():
    rec = R.junction_tip(TIP, OWNER, 2.5, OWNER.area * 0.85, OTHER_BILLED, 0.85)
    assert rec["state"] == "BILLED_ONCE_BY_OWNER" and rec["companion_m3"] == 0.0


def test_adverse_tip_billed_by_both_lines_is_a_double_and_an_unproved_owner_stays_unresolved():
    both = OTHER_BILLED.union(TIP)
    assert R.junction_tip(TIP, OWNER, 2.5, OWNER.area * 0.85, both, 0.85)["state"] == "DOUBLE"
    # the owner's value does not carry its whole rectangle: no proof, the range is kept (never a point)
    assert R.junction_tip(TIP, OWNER, 2.5, OWNER.area * 0.85 - 0.01, OTHER_BILLED, 0.85)["state"] == "UNRESOLVED"


# ---- the committed development-villa result (arithmetic only; the build needs the private drawing)
@pytest.fixture(scope="module")
def res():
    return json.loads(RES.read_text(encoding="utf-8"))


def test_a_cb4_excess_is_the_drawn_triangle_billed_once(res):
    a = res["a_CB4"]
    assert a["verdict"] == "ENGINE_RIGHT"
    assert abs(a["excess_m3"] - a["triangle_x_depth_m3"]) <= 1e-5
    assert a["triangle_m2"] == pytest.approx(0.5 * 0.2 * (a["edge_lengths_m"][0] - a["edge_lengths_m"][1]), abs=2e-6)
    assert a["billed_by_other_lines_m2"] == 0.0 and a["in_other_t229_regions_m2"] == 0.0
    assert a["boundary_drawn_share"] >= R.DRAWN_COVER_MIN


def test_b_five_pairs_closed(res):
    v = {(p["storey"], p["mark"], p["column"]): p["verdict"] for p in res["b_pairs"]}
    assert v == {("GF", "B28", "C27"): "ENGINE_RIGHT", ("GF", "B26", "C27"): "ENGINE_RIGHT",
                 ("GF", "B26", "C25"): "ENGINE_WRONG_OMISSION", ("GF", "B27", "C8"): "ENGINE_RIGHT",
                 ("1F", "B19", "C15"): "ENGINE_WRONG_OMISSION"}
    for p in res["b_pairs"]:
        if p["verdict"] == "ENGINE_RIGHT":
            assert p["placement"] == "BILLED_BY_ADD" and p["residual_m3"] <= R.ADD_TOL_M3
            assert abs(p["region_vs_add_m3"]) <= R.tol_m3(p["t229_add_m3"])
        else:
            assert p["faces_end_on_column"] and p["wedge_billed_by_any_line_m2"] == 0.0
            assert p["omission_m3"] == pytest.approx(p["wedge_m2"] * p["depth_m"], abs=2e-6)
    for r in res["b_run_decomposition"]:
        assert abs(r["residual_m3"]) <= 1e-4


def test_c_tip_billed_once_and_the_range_closes_to_its_low_end(res):
    c = res["c_B27_tip"]
    assert c["verdict"] == "ENGINE_RIGHT" and c["companion_m3"] == 0.0
    assert c["tip_in_B27_rectangle_m2"] == pytest.approx(c["tip_m2"], abs=1e-6)
    assert c["route_g_junction_deduction_on_B1"][0]["area_m2"] == pytest.approx(c["tip_m2"], abs=1e-6)
    assert float(c["B1_value_m3"]) == pytest.approx(c["B1_rebuilt_m3"], abs=1e-4)
    assert res["b10_effect"]["after_c_m3"] == res["b10_effect"]["v14_after_total_m3"][0]


def test_d_h1_has_an_owner_and_is_measured(res):
    d = res["d_H1"]
    assert d["verdict"] == "ENGINE_WRONG_OMISSION" and d["boundary_drawn_share"] >= R.DRAWN_COVER_MIN
    assert d["region_m2"] == pytest.approx(d["t614_held_m2"], abs=1e-5)
    assert d["run_printed_length_m"] == pytest.approx(d["hull_length_m"], abs=1e-4)
    assert d["billed_by_any_line_m2"] == 0.0 and d["in_any_t229_region_m2"] == 0.0


def test_fix_rows_re_add_and_b10_effect(res):
    fx = res["fix_rows"]
    assert [f["id"] for f in fx] == ["FR-T624-1", "FR-T624-2", "FR-T624-3"]
    tot = sum(f["change_m3"] for f in fx)
    assert res["b10_effect"]["fix_rows_m3"] == pytest.approx(tot, abs=1e-6)
    e = res["b10_effect"]
    assert e["after_t624_m3"] == pytest.approx(e["after_c_m3"] + tot, abs=1e-6)
    assert e["gap_to_his_m3"] == pytest.approx(e["after_t624_m3"] - e["his_m3"], abs=1e-6)
    for f in fx:
        assert f["change_m3"] > 0 and f["change_m3"] == pytest.approx(f["piece_m2"] * f["depth_m"], abs=2e-6)


def test_no_coordinates_in_the_tracked_output():
    for f in (RES, OUT / "T624_BEAM_END_OPEN_ITEMS.md"):
        text = f.read_text(encoding="utf-8")
        assert '"polygon"' not in text and '"hull"' not in text and "origin" not in text and "D2:" not in text


@pytest.mark.skipif(not PRIVATE_DXF.exists(), reason="private drawing absent")
def test_private_rebuild_equals_committed():
    import t624_alsenan as A
    d = A.build(str(PRIVATE_DXF))
    assert json.dumps(d, indent=1, sort_keys=True) + "\n" == RES.read_text(encoding="utf-8")
