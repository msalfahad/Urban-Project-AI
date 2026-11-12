"""T-725: stair formwork lines (R-T725-1 .. 3). Villa V725 is hand-made (not the development villa): storey 3.00 m,
18 risers (rise 0.166667), going 0.28, waist T 0.15, lane 1.10; a straight flight of 8 riser lines starting on the
ground-floor slab; a quarter turn drawn as a 1.10 x 1.25 region with 3 winders whose fronts are not drawn; a curved
flight whose rise no section prints. Hand figures are written out in each test. The last tests rebuild the
development-villa ledger from committed files (the drawing facts are constants in the builder; no drawing is opened)."""
from __future__ import annotations

import json
import math
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest
from shapely.affinity import rotate, scale
from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t725"))
import t725_rules as R  # noqa: E402
import t725_alsenan as A  # noqa: E402

G, T, W = 0.28, 0.15, 1.10
V725 = R.Reading("V725", 3.00, (("F1", 8), ("TURN", 3), ("F2", 7)), "section", "section 18", total_declared=18)
r = V725.rise                     # 3.00 / 18 = 0.1666667
SEC = math.hypot(G, r) / G        # 1.1637476
TS = T * SEC                      # 0.1745621 vertical waist thickness


# ---------------------------------------------------------------- R-T725-1
def test_reading_rise_is_one_count():
    assert V725.total == 18 and abs(r - 3.00 / 18) < 1e-15


def test_adverse_count_from_one_source_rise_from_another_refused():
    # plan draws 9 + 3 + 7 = 19 risers, the section's rise is 3.00 / 18: not one stair
    with pytest.raises(R.Refused, match="R-T725-1"):
        R.Reading("mixed", 3.00, (("F1", 9), ("TURN", 3), ("F2", 7)), "plan", "section 18", total_declared=18)


def test_adverse_units_mm_refused():
    with pytest.raises(R.Refused, match="not a riser"):
        R.Reading("mm", 3000.0, (("F1", 18),), "section", "section", total_declared=18)
    with pytest.raises(R.Refused):
        R.riser_forms([1100.0], 166.7, drawn=True)


# ---------------------------------------------------------------- R-T725-2 geometry by hand
def test_v725_side_profile_methods_o_and_d():
    # 8 lines -> 7 goings, L = 1.96: triangles 7 x 1/2 x 0.28 x 0.166667 = 0.163333; waist band T x sloped L =
    # 0.15 x 1.96 x 1.163748 = 0.342142 -> O = 0.505475; D clips the foot below the slab top:
    # 1/2 x TS^2 x g / r = 1/2 x 0.174562^2 x 1.68 = 0.025596 -> D = 0.479879
    o = R.side_profile(r, G, T, 8, 0.0, 7 * G, clip_floor=False)
    d = R.side_profile(r, G, T, 8, 0.0, 7 * G, clip_floor=True)
    hand_o = 7 * 0.5 * G * r + T * 7 * G * SEC
    hand_d = hand_o - 0.5 * TS ** 2 * G / r
    assert abs(o - hand_o) < 1e-12 and abs(d - hand_d) < 1e-12
    assert round(o, 6) == 0.505475 and round(d, 6) == 0.479879


def test_v725_strips_sum_to_the_whole_and_d_is_never_larger():
    e = 7 * G
    parts = [R.side_profile(r, G, T, 8, a, b, clip_floor=True) for a, b in ((0, 0.1), (0.1, 0.9), (0.9, e))]
    assert abs(sum(parts) - R.side_profile(r, G, T, 8, 0, e, clip_floor=True)) < 1e-12
    for a, b in ((0, 0.05), (0.2, 0.6), (1.5, e)):
        assert R.side_profile(r, G, T, 8, a, b, clip_floor=True) <= R.side_profile(r, G, T, 8, a, b, clip_floor=False)


def test_v725_soffit_o_and_d_never_the_plan_area():
    plan = 7 * G * W                                    # 2.156 m2
    o = R.soffit_true(plan, r, G)                       # 2.156 x 1.163748 = 2.509040
    d = R.soffit_d(plan, W, r, G, T, foot_on_slab=True)  # (2.156 - 1.10 x 1.68 x 0.174562) x sec = 2.133625
    assert round(o, 6) == 2.509040
    assert abs(d - (plan - W * (G / r) * TS) * SEC) < 1e-12 and round(d, 6) == 2.133625
    assert o > plan and d < o
    assert R.soffit_d(plan, W, r, G, T, foot_on_slab=False) == pytest.approx(o)


def test_v725_risers_and_winder_floor():
    assert R.riser_forms([W] * 8, r, drawn=True) == pytest.approx(8 * 1.10 * 3.00 / 18)       # 1.466667
    # 3 winders, fronts not drawn, region 1.10 x 1.25 drawn: each front >= 1.10 -> 3 x 1.10 x r = 0.55
    assert R.winder_floor(3, min(1.10, 1.25), r, region_drawn=True) == pytest.approx(0.55)
    assert R.warped_floor(1.10 * 1.25, region_drawn=True) == pytest.approx(1.375)


def test_adverse_generated_winder_and_undrawn_region_give_no_figure():
    with pytest.raises(R.Refused, match="S-9"):
        R.riser_forms([1.30, 1.55, 1.30], r, drawn=False)
    with pytest.raises(R.Refused, match="S-9"):
        R.winder_floor(3, 1.10, r, region_drawn=False)
    with pytest.raises(R.Refused):
        R.warped_floor(None, region_drawn=True)


def test_adverse_missing_waist_never_zero():
    with pytest.raises(R.Refused, match="never computed with 0"):
        R.side_profile(r, G, None, 8, 0, 1.0, clip_floor=False)
    with pytest.raises(R.Refused):
        R.soffit_d(2.0, W, r, G, 0.0, foot_on_slab=True)


def test_mirror_and_rotation_do_not_change_the_going():
    lines = [LineString([(i * G, 0.0), (i * G, W)]) for i in range(8)]
    for geo in (lambda x: rotate(x, 37, origin=(0, 0)), lambda x: scale(x, -1, 1, origin=(0, 0))):
        moved = [geo(x) for x in lines]
        goings = [moved[i].distance(moved[i + 1]) for i in range(7)]
        assert all(abs(gg - G) < 1e-9 for gg in goings)
        assert all(abs(x.length - W) < 1e-9 for x in moved)


# ---------------------------------------------------------------- R-T725-3 line class
def _f(lo, hi, c="FORMED"):
    return R.Face("f", "K", lo, hi, "", c)


def test_class_bounded_at_least_blank():
    b = R.class_line("L1", {"A": [_f(0.5, 0.5)], "B": [_f(0.6, 0.6)]}, cause=None, live_items=set(), removed_items=set())
    assert (b.cls, b.low, b.high) == ("BOUNDED", X("0.500000"), X("0.600000"))
    a = R.class_line("L2", {"A": [_f(0.5, 0.5), _f(1.375, None)]}, cause=None, live_items=set(), removed_items=set())
    assert (a.cls, a.low, a.high) == ("AT_LEAST", X("1.875000"), None)
    z = R.class_line("L3", {"one": [_f(0.0, 0.4, "CAP_ONLY")]}, cause="sequence", live_items=set(), removed_items=set())
    assert (z.cls, z.low, z.high, z.cap) == ("BLANK_NAMED", None, None, X("0.400000"))


def test_adverse_winder_flight_stays_blank_and_never_zero():
    z = R.class_line("L4", {"one": [R.Face("w", "SIDE", None, None, "", "BLOCK")]}, cause="winders not drawn",
                     live_items=set(), removed_items=set())
    assert z.cls == "BLANK_NAMED" and z.low is None and z.cap is None
    with pytest.raises(R.Refused, match="cause"):
        R.class_line("L5", {"one": [_f(0.0, 0.4, "CAP_ONLY")]}, cause=None, live_items=set(), removed_items=set())


def test_adverse_removed_item_and_bad_faces_refused():
    with pytest.raises(R.Refused, match="removed"):
        R.class_line("L6", {"one": [_f(0.0, 0.4, "CAP_ONLY")]}, cause="x", live_items={"RFI-1"},
                     removed_items={"D-9"}, cited=("D-9",))
    for bad in (_f(-0.1, 0.2), _f(0.3, 0.2), _f(1500.0, 1500.0), _f(0.1, 0.4, "CAP_ONLY")):
        with pytest.raises(R.Refused):
            R.class_line("L7", {"one": [bad]}, cause="x", live_items=set(), removed_items=set())


# ---------------------------------------------------------------- development villa (committed inputs only)
@pytest.fixture(scope="module")
def built():
    return A.build()


def test_dev_villa_outputs_reproduce(built):
    js = json.dumps(built, indent=1, sort_keys=True, default=str) + "\n"
    assert A.OUT_JSON.read_text(encoding="utf-8") == js
    assert A.OUT_MD.read_text(encoding="utf-8") == A.census_md(built)


def test_dev_villa_census_20_by_id_none_zero(built):
    ls = built["lines"]
    assert len(ls) == 20 and len({x["line_id"] for x in ls}) == 20
    assert built["census"] == {"BOUNDED": 2, "AT_LEAST": 2, "BLANK_NAMED": 16}
    for x in ls:
        assert x["class_after"] in R.LINE_CLASSES
        if x["class_after"] == "BLANK_NAMED":
            assert x["low"] is None and x["high"] is None and x["cause"]
        else:
            assert X(x["low"]) > 0
        assert "D-56" not in x["cited"] and "D-68" not in x["cited"]


def test_dev_villa_pinned_values(built):
    by = {x["line_id"][:10]: x for x in built["lines"]}
    assert (by["L-9c3643da"]["low"], by["L-9c3643da"]["high"]) == ("0.679193", "0.854426")
    assert (by["L-77ecb282"]["low"], by["L-77ecb282"]["high"]) == ("1.904000", "2.380000")
    assert (by["L-ffd491ad"]["class_after"], by["L-ffd491ad"]["low"]) == ("AT_LEAST", "7.678894")
    assert (by["L-739ee9fe"]["class_after"], by["L-739ee9fe"]["low"]) == ("AT_LEAST", "0.193200")
    assert by["L-997777b3"]["cap"] is None and by["L-f19a44ba"]["cap"] is None
    f1 = built["findings"]["F-T725-1"]
    assert f1["floors_moved"] == 0 and "R-T725-1" in f1["refused"]


def test_dev_villa_pins_hold():
    A.check_pins()
