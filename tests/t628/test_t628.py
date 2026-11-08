"""T-628: the footing-line and lift-wall residual rows re-measured from the drawing (R-T628-1 .. 5).
Hand villa "V628" (not the training villa: two footings sharing an edge with a ground beam over both, a strap, a lift
pit), adverse cases, then the development villa from the committed output (the private rebuild only when the private
inputs are present)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from shapely.affinity import rotate, scale
from shapely.geometry import LineString, box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t628"))
import t628_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t628" / "out" / "T628_FOOTING_LIFT_ROWS.json"
STATEMENT = ROOT / "research" / "agents_t620" / "out" / "RECONCILED_STATEMENT_T620.json"
PRIV = ROOT.parent / "private"
PRIVATE = (PRIV / "ST7757.dxf", PRIV / "concrete_rebar.xlsx")
D = Decimal

# ---- villa "V628" (hand, metres) ---------------------------------------------------------------------------------
# FA 2.00 x 2.00 x 0.50 (x 0 .. 2), FB 1.50 x 2.00 x 0.40 (x 2 .. 3.5): they SHARE the edge x = 2 (no overlap)
#   concrete 2.000 + 1.200 = 3.200 m3
# ground beam GB 0.30 wide x 4.50 long (x -0.5 .. 4.0, y 0.85 .. 1.15) over both footings
#   case 1: GB 0.60 deep sitting on the footing tops (bottom +0.50 over FA, FA top +0.50, FB top +0.40): shares 0
#           -> 0.81 m3, total 4.010
#   case 2: GB from +0.30 to +1.10 (0.80 deep, cast into the footings): shares FA 0.60 m2 x 0.20 = 0.120,
#           FB 0.45 m2 x 0.10 = 0.045 -> footing owns, beam 1.080 - 0.165 = 0.915, total 4.115
FA, FB = box(0, 0, 2.0, 2.0), box(2.0, 0, 3.5, 2.0)
GB = box(-0.5, 0.85, 4.0, 1.15)


def test_v628_shared_edge_is_not_an_overlap():
    assert R.plans_once({"FA": FA, "FB": FB}) == []
    assert R.mark_volume([("FA", FA.area)], "0.50") + R.mark_volume([("FB", FB.area)], "0.40") == D("3.200000")


def test_v628_beam_over_both_at_another_elevation_shares_nothing():
    v = {"FA": "2.0", "FB": "1.2", "GB": str(4.5 * 0.3 * 0.6)}
    sa = R.crossing_volume(GB.intersection(FA).area, 0.0, 0.50, 0.50, 1.10)
    sb = R.crossing_volume(GB.intersection(FB).area, 0.0, 0.40, 0.50, 1.10)
    assert sa == sb == D("0")
    assert R.total_once(v, {("FA", "GB"): sa, ("FB", "GB"): sb}, {}) == D("4.010000")


def test_v628_beam_cast_into_footings_counted_once():
    sa = R.crossing_volume(GB.intersection(FA).area, 0.0, 0.50, 0.30, 1.10)
    sb = R.crossing_volume(GB.intersection(FB).area, 0.0, 0.40, 0.30, 1.10)
    assert (sa, sb) == (D("0.120000"), D("0.045000"))
    v = {"FA": "2.0", "FB": "1.2", "GB": "1.08"}
    own = {("FA", "GB"): "FA", ("FB", "GB"): "FB"}
    assert R.total_once(v, {("FA", "GB"): sa, ("FB", "GB"): sb}, own) == D("4.115000")


def test_adverse_overlap_billed_twice_refused():
    with pytest.raises(R.Refused, match="billed twice"):
        R.total_once({"FA": "2.0", "GB": "1.08"}, {("FA", "GB"): "0.12"}, {})
    with pytest.raises(R.Refused, match="billed twice"):
        R.total_once({"FA": "2.0", "GB": "1.08"}, {("FA", "GB"): "0.12"}, {("FA", "GB"): "FB"})


def test_adverse_crossing_level_missing_is_held_not_deducted():
    with pytest.raises(R.Refused, match="HELD"):
        R.crossing_volume(0.6, 0.0, 0.5, None, 1.1)


def test_overlapping_outlines_are_reported():
    pairs = R.plans_once({"A": box(0, 0, 2, 2), "B": box(1.9, 0, 3, 2)})
    assert len(pairs) == 1 and round(pairs[0][2], 9) == 0.2


def test_mirror_and_rotation_keep_plans_and_volumes():
    for g in (lambda p: rotate(p, 30, origin=(0, 0)), lambda p: scale(p, -1, 1, origin=(0, 0))):
        a, b = g(FA), g(FB)
        assert R.plans_once({"FA": a, "FB": b}) == []
        assert R.mark_volume([("FA", a.area)], "0.50") == D("2.000000")


def test_notched_outline_owned_by_the_other_footing():
    big = box(0, 0, 3.4, 2.7)
    fn = box(3.0, 2.35, 4.0, 3.35).difference(big)
    st, miss = R.outline_status(fn, [big], 1.0, 1.0)
    assert st == "NOTCHED" and round(miss, 9) == 0.14
    assert R.d6(D("4") * D("0.30") - R.mark_volume([("n1", 1.0), ("n2", 1.0), ("n3", 1.0), ("n4", fn.area)],
                                                   "0.30")) == D("0.042000")
    with pytest.raises(R.Refused, match="no other outline"):
        R.outline_status(fn, [], 1.0, 1.0)


def test_count_needs_the_schedule_size():
    with pytest.raises(R.Refused, match="SECTION"):
        R.outline_status(box(0, 0, 1.7, 1.4), [], 1.6, 1.4)
    assert R.outline_status(box(0, 0, 1.4, 1.6), [], 1.6, 1.4)[0] == "FULL"   # either orientation
    assert R.count_delta(1, 2, "0.672") == D("-0.672000")
    with pytest.raises(R.Refused):
        R.count_delta(1, 1.5, "0.672")


def test_conflict_outline_is_held_bound_never_zero():
    assert R.conflict_bound(["2.176", "2.275"]) == (D("2.176000"), D("2.275000"))
    with pytest.raises(R.Refused):
        R.conflict_bound(["2.176"])
    with pytest.raises(R.Refused, match="HELD as 0"):
        R.conflict_bound(["0", "2.275"])


def test_strap_clear_axis_and_section():
    f1, f2 = box(0, 0, 3.0, 1.5), box(0, 3.75, 2.2, 6.35)
    fa = ((1.0, 0.3), (0.0, 5.3))
    fb = ((2.0, 0.3), (1.0, 5.3))
    ax = R.strap_axis(fa, fb)
    import math
    L = R.strap_clear_length(ax, f1.union(f2))
    assert abs(L - 2.25 / math.sin(math.atan2(5.0, 1.0))) < 1e-9
    w = LineString(fa).distance(LineString(fb).interpolate(0.5, normalized=True))
    assert R.strap_section([(1.0, 0.5), (0.8, 0.5)], w) == (1.0, 0.5)
    with pytest.raises(R.Refused, match="SECTION_CONFLICT"):
        R.strap_section([(1.0, 0.5), (0.98, 0.5)], 0.99)
    with pytest.raises(R.Refused):
        R.strap_section([], 0.99)
    assert R.strap_volume(1.0, 0.5, 2.2) == D("1.100000")


def test_pit_ring_columns_owned_once():
    outer, inner = box(0, 0, 2.2, 2.2), box(0.2, 0.2, 2.0, 2.0)
    cols = [box(0, 0, 0.2, 0.5), box(2.0, 1.7, 2.2, 2.2)]
    g, c, n = R.pit_ring(outer, inner, cols)
    assert (round(g, 9), round(c, 9), round(n, 9)) == (1.6, 0.2, 1.4)
    assert R.scope_double(c, "1.50") == D("0.300000")
    with pytest.raises(R.Refused):
        R.pit_ring(inner, outer, cols)


def test_unsupported_held_bound_replaced_by_drawing_range():
    hb = R.held_bound(7.2204, "UNSUPPORTED BASIS", ("5.6392", "11.0328"), "range")
    assert hb["bound"] == ["5.639200", "11.032800"] and hb["replaced"] == "7.220400"
    assert R.position("8.604", *hb["bound"]) == "INSIDE"
    assert R.position("8.604", "7.2204", "7.2204") == "ABOVE"
    with pytest.raises(R.Refused):
        R.held_bound(7.2204, "UNSUPPORTED BASIS", None, None)
    assert R.held_bound(2.176, None, None, None)["basis"] == "engine held line"


def test_adverse_split_and_statuses():
    with pytest.raises(R.Refused, match="balancing"):
        R.split_exact("1.0", {"BALANCE": ("TOLERANCE", "1.0")})
    with pytest.raises(R.Refused, match="open sum"):
        R.split_exact("1.0", {"COUNT": ("ENGINE_RIGHT", "0.9")})
    with pytest.raises(R.Refused, match="HELD as 0"):
        R.split_exact("0", {"band": ("HELD", "0")})
    with pytest.raises(R.Refused, match="m3 only"):
        R.split_exact("1.0", {"COUNT": ("ENGINE_RIGHT", "1.0")}, unit="kg")
    with pytest.raises(R.Refused, match="never 0"):
        R.d6(None)
    with pytest.raises(R.Refused, match="HELD as 0"):
        R.row_status("0", "0", held_by="D-43")
    with pytest.raises(R.Refused, match="by name"):
        R.row_status("1.65", "1.65", held_by=" ")
    with pytest.raises(R.Refused, match="no named physical cause"):
        R.row_status("0.05", "0.0")
    with pytest.raises(R.Refused, match="no named physical cause"):
        R.row_status("0.05", "0.0", drift_cause="REMAINDER")
    with pytest.raises(R.Refused, match="never 0"):
        R.mark_volume([("A", 1.0)], None)
    with pytest.raises(R.Refused, match="twice"):
        R.mark_volume([("A", 1.0), ("A", 1.0)], "0.3")


# ---- development villa (committed output) ------------------------------------------------------------------------
def _doc():
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_dev_seven_rows_classed_and_split_exact():
    d = _doc()
    st = {s["section_id"]: s for s in json.loads(STATEMENT.read_text(encoding="utf-8"))["sections"]}
    n = 0
    for sid, ln in d["lines"].items():
        assert len(ln["rows"]) == len(st[sid]["rows"])
        for r in ln["rows"]:
            n += 1
            assert r["class"] in R.CLASSES and r["status"] in ("RE-MEASURED", "HELD")
            if r["class"] == "HELD":
                assert D(r["own_delta"]) != 0
            assert abs(D(r["drift"])) <= R.TOL_M3
        tot = sum(D(v) for _, v in ln["split"].values())
        assert tot == R.d6(st[sid]["difference"])
    assert n == 7


def test_dev_pads_and_overlaps():
    d = _doc()
    assert d["pads_total_m3"] == "64.304000" and d["outline_count"] == 26 and d["overlapping_outline_pairs"] == 0
    fl = d["lines"]["T-551/footing-line"]["rows"]
    assert fl[3]["evidence"]["notch_owner"] == ["180F"] and fl[3]["evidence"]["notch_m3"] == "0.042000"
    assert fl[0]["evidence"]["outlines"] == ["166B", "166C"]
    assert fl[1]["evidence"]["held_bound_m3"] == ["2.176000", "2.275000"]
    band = fl[2]["evidence"]
    assert band["free_m"] == "70.490000" and band["inside_footings_m"] == "21.450000"
    assert band["quoted_bound"]["bound"] == ["5.639200", "11.032800"] and band["reference_position"] == "INSIDE"
    s = fl[4]["evidence"]["straps"]
    assert s["SB2"]["selected"] == "2ABA" and s["SB2"]["schedule_rows"] == 2
    lw = d["lines"]["T-551/lift-walls"]["rows"]
    assert lw[0]["evidence"]["column_pieces_m2"] == "0.500000" and lw[1]["evidence"]["net_ring_m2"] == "1.100000"
    assert d["fix_rows"][0]["corrected_engine_bounded"] == ["75.539200", "81.655600"]
    sb1 = d["lines"]["T-551/footing-line"]["beside_zero_components"]["SB1 in F10 + F"]
    assert sb1["agree_high"] and sb1["column_pieces_m2"] == {"10E8": "0.035000"}


def test_dev_no_coordinates_or_reference_rows_tracked():
    txt = OUT.read_text(encoding="utf-8")
    for bad in ("71.7", "31.37", "15.00", '"x"', '"y"', "coords", "his_rows"):
        assert bad not in txt


@pytest.mark.skipif(not all(p.exists() for p in PRIVATE), reason="private drawing / workbook not present")
def test_private_rebuild_equals_committed():
    import t628_alsenan as A
    d = A.build(str(PRIVATE[0]), str(PRIVATE[1]))
    assert json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True) + "\n" == OUT.read_text(encoding="utf-8")
