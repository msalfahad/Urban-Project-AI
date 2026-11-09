"""T-642: Checker T-180 P02 / P04 fix rows + STR.CONC.PARAPET HELD-blank lines (no new rule; R-T610-1, R-T624-1,
R-T619-1, UP-QTY-STATUS-001 applied). Synthetic non-Alsenan fixtures (hand-calculated) + the committed
development-villa result (internal arithmetic only, no coordinates)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t642"))
import t642_rules as R  # noqa: E402

RES = ROOT / "research" / "agents_t642" / "out" / "T642_FIX_ROWS.json"

# ---- fixture (hand), not the training villa.
#  Beam P 0.30 wide (y 0 .. 0.30) hangs 0.70 m; its route G pieces P.1 (x 0 .. 3.00) and P.2 (x 3.40 .. 7.00) stop at
#  column Q 0.40 x 0.20 (x 3.00 .. 3.40, y 0 .. 0.20), flush with P's south face. The 0.10 strip beside Q inside P:
#  x 3.00 .. 3.40, y 0.20 .. 0.30 = 0.040 m2 -> x 0.70 = 0.028 m3.
#  An unlabelled straight 0.20 x 0.60 stub (0.120 m2) joins a 0.45-deep band (faces continuous) to a 0.80-deep arc.
DP = 0.70
Q = box(3.00, 0.0, 3.40, 0.20)
STRIP = box(3.00, 0.20, 3.40, 0.30)
P1, P2 = box(0.0, 0.0, 3.00, 0.30), box(3.40, 0.0, 7.00, 0.30)


def _covers(strip, plans):
    return {k: g.intersection(strip).area for k, g in plans.items() if g.intersection(strip).area > R.EPS_M2}


def test_unbilled_strip_between_two_bands_is_an_omission():
    st, own = R.owners_of(STRIP.area, _covers(STRIP, {"L-P1": P1, "L-P2": P2}))
    assert (st, own) == ("OMISSION", [])
    assert STRIP.area * DP == pytest.approx(0.028, abs=1e-12)


def test_strip_billed_by_its_named_term_region_is_billed_once():
    region = box(3.00, 0.0, 3.40, 0.30).difference(Q)        # the gap between P.1 and P.2, net of the column
    st, own = R.owners_of(STRIP.area, _covers(STRIP, {"L-P1": P1.union(region), "L-P2": P2}))
    assert (st, own) == ("BILLED_ONCE", ["L-P1"])


@pytest.mark.parametrize("deg", [0, 37, 90, 180])
@pytest.mark.parametrize("mirror", [False, True])
def test_rotation_and_mirror_do_not_change_the_strip(deg, mirror):
    g = box(3.00, 0.0, 3.40, 0.30).difference(Q)
    if mirror:
        g = affinity.scale(g, xfact=-1, origin=(0, 0))
    g = affinity.rotate(g, deg, origin=(0, 0))
    assert g.area == pytest.approx(0.040, abs=1e-12)
    assert R.value_omission(g.area, [{"mark": "P", "depth_m": DP, "source": "schedule row P"}])["set_m3"] == \
        pytest.approx(0.028, abs=1e-12)


def test_units_mm_depth_refused():
    with pytest.raises(R.Refused):
        R.value_omission(0.040, [{"mark": "P", "depth_m": 700.0, "source": "schedule row P"}])


def test_adverse_strip_billed_by_two_lines_refused():
    with pytest.raises(R.Refused, match="two lines"):
        R.owners_of(STRIP.area, {"L-P1": STRIP.area, "L-X": STRIP.area})


def test_adverse_owned_and_partly_billed_again_refused():
    with pytest.raises(R.Refused, match="partly billed again"):
        R.owners_of(STRIP.area, {"L-P1": STRIP.area, "L-X": 0.01})


def test_two_sourced_depths_give_low_end_and_companion():
    v = R.value_omission(0.120, [{"mark": "M1", "depth_m": 0.45, "source": "faces continuous with M1"},
                                 {"mark": "M2", "depth_m": 0.80, "source": "arc lead-in of M2"}])
    assert v["state"] == "RANGE_LOW_SET"
    assert v["set_m3"] == pytest.approx(0.054, abs=1e-12)
    assert v["companion_high_m3"] == pytest.approx(0.042, abs=1e-12)
    assert v["companion_low_m3"] == 0.0


def test_adverse_unsourced_depth_used_as_a_point_refused():
    with pytest.raises(R.Refused, match="no drawing source"):
        R.value_omission(0.120, [{"mark": "M2", "depth_m": 0.80, "source": ""}])


def test_missing_depth_never_zero():
    with pytest.raises(R.Refused, match="HELD"):
        R.value_omission(0.120, [])


def test_compare_with_line_uses_the_line_terms_not_the_band():
    # band 3.00 x 0.30 x 0.70 = 0.630; line = band + term 0.0285 (fitted region); own strip 0.028
    c = R.compare_with_line(0.028, 0.6585, 0.630, {"gap term": 0.0285}, piece_term="gap term")
    assert c["delta_vs_term_m3"] == pytest.approx(-0.0005, abs=1e-12)
    assert c["within_add_tol"] is True
    whole = R.compare_with_line(0.6580, 0.6585, 0.630, {"gap term": 0.0285})
    assert whole["delta_vs_band_m3"] == pytest.approx(0.028, abs=1e-12)     # what a band-only check would 'find'
    assert whole["delta_vs_line_m3"] == pytest.approx(-0.0005, abs=1e-12)


def test_adverse_line_that_does_not_decompose_refused():
    with pytest.raises(R.Refused, match="decompose"):
        R.compare_with_line(0.028, 0.70, 0.630, {"gap term": 0.0285})


def test_held_line_needs_a_cause_and_no_figure():
    ok = R.class_held_line({"line_id": "L-1", "measured_net": None}, "MATERIAL HELD (designer)", {"at_least_m3": 0.3})
    assert ok["class"] == "HELD_WITH_CAUSE" and ok["quantity"] is None
    with pytest.raises(R.Refused, match="no cause"):
        R.class_held_line({"line_id": "L-1", "measured_net": None}, "  ")
    with pytest.raises(R.Refused, match="figure"):
        R.class_held_line({"line_id": "L-1", "measured_net": 0.0}, "cause")
    with pytest.raises(R.Refused, match="floor"):
        R.class_held_line({"line_id": "L-1", "measured_net": None}, "cause", {"at_least_m3": None})


# ---- the committed development-villa result (internal arithmetic only)
@pytest.fixture(scope="module")
def res():
    return json.loads(RES.read_text(encoding="utf-8"))


def test_alsenan_a_billed_once_by_the_t229_term(res):
    a = res["items"]["a"]
    assert a["state"] == "BILLED_ONCE" and a["owners"] == [a["engine"]["line_id"]]
    assert a["drawn"]["strip_m2"] == pytest.approx(0.05 * 0.9 - 0.05 * 0.25, abs=1e-9)
    assert a["drawn"]["own_m3"] == pytest.approx(0.024375, abs=1e-9)
    assert a["engine"]["strip_in_term_region_m2"] == pytest.approx(a["drawn"]["strip_m2"], abs=1e-9)
    assert a["engine"]["other_lines_billing_strip_m2"] == {}
    assert abs(a["engine"]["decomposition_residual_m3"]) <= 1e-4
    assert abs(a["delta_own_minus_term_m3"]) <= R.ADD_TOL_M3
    assert a["fix_row"]["change_m3"] == 0.0


def test_alsenan_b_held_range_narrowed_low_end_set(res):
    b = res["items"]["b"]
    assert b["drawn"]["strip_m2"] == pytest.approx(0.100, abs=1e-9)
    assert b["engine"]["line"]["class"] == "HELD"
    assert b["fix_row"]["change_m3"] == pytest.approx(0.100 * 0.50, abs=1e-9)
    assert b["fix_row"]["companion"]["held_m3"] == [0.0, pytest.approx(0.100 * (0.75 - 0.50), abs=1e-9)]
    assert len(b["owners"]) == 1


def test_alsenan_c_and_d_engine_right(res):
    c, d = res["items"]["c"], res["items"]["d"]
    e = c["drawn"]["edges_m"]
    assert c["drawn"]["plan_m2"] == pytest.approx(0.2 * (e[0] + e[1]) / 2, abs=1e-6)
    assert abs(c["delta_own_minus_line_m3"]) <= R.ADD_TOL_M3
    assert d["drawn"]["plan_m2"] == pytest.approx(3.141592653589793 / 4 * (1.3 ** 2 - 1.1 ** 2), abs=1e-6)
    assert d["printed_mark"]["text"] == "B7" and d["printed_mark"]["distance_to_ring_m"] < 0.15
    assert d["printed_mark"]["distance_to_ring_m"] < min(d["printed_mark"]["distance_to_B2_band_m"],
                                                         d["printed_mark"]["distance_to_CB6_face_m"])
    assert d["delta_own_minus_line_m3"] == pytest.approx(0.0, abs=1e-6)


def test_alsenan_e_four_parapets_classed_with_cause(res):
    e = res["items"]["e"]["lines"]
    assert len(e) == 4 and all(x["class"] == "HELD_WITH_CAUSE" and x["quantity"] is None and x["cause"] for x in e)
    assert res["items"]["e"]["total_at_least_m3"] == pytest.approx(sum(x["bound_beside"]["at_least_m3"] for x in e),
                                                                   abs=1e-6)
    for x in e:
        lo, hi = x["bound_beside"]["all_rc_printed_part_m3"]
        assert x["bound_beside"]["at_least_m3"] <= lo <= hi
