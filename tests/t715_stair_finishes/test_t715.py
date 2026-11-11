"""T-715: stair finish lines by cause (R-T715-1 .. 4). Villa V715 is hand-made (not the development villa): storey
3.40 m / 20 risers (r 0.17), a straight flight of 10 risers / 9 goings 0.28 x 1.00 wide, tread marble 0.02, a corner turn
1.00 x 1.00 with 4 section risers, a skirting stretch of 0.56 m plan with 2 risers and 0.05 returns. The last tests
rebuild the development-villa census from committed files only."""
from __future__ import annotations

import json
import random
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t715"))
import t715_rules as R  # noqa: E402

BR = R.BR
F = dict(rise_m=(X("3.40"), 20), risers=10, goings=9, width_m="1.00", going_m="0.28", tread_t_m="0.02")


def r6(x):
    return BR.round_point(x)


# ------------------------------------------------------------------ R-T715-1 normal (hand)
def test_straight_flight_hand():
    f = R.straight_flight(**F)
    assert f["riser_m"] == X("0.17") and f["visible_m"] == X("0.15")
    assert r6(f["riser_m2"]) == X("1.500000")                 # 10 x 1.00 x 0.15
    assert r6(f["pitch_lm"]) == X("2.948101")                 # 9 x sqrt(0.28^2 + 0.17^2) = 9 x 0.3275668
    assert r6(f["step_lm"]) == X("9.000000")


def test_flight_ending_on_winder_takes_goings_equal_risers():
    f = R.straight_flight(**{**F, "goings": 10})
    assert r6(f["step_lm"]) == X("10.000000")


@pytest.mark.parametrize("bad", [dict(goings=8), dict(risers=None), dict(width_m=None), dict(tread_t_m="0.17"),
                                 dict(rise_m=(X("3.40"), 0)), dict(going_m="-0.28"), dict(unit="mm"),
                                 dict(rise_m=(None, 20))])
def test_straight_flight_refusals(bad):
    with pytest.raises(R.Refused):
        R.straight_flight(**{**F, **bad})


# ------------------------------------------------------------------ R-T715-2 turn region
def test_turn_tiling_and_floors_hand():
    t = R.turn_region(region_m2="1.00", risers_section=4, risers_plan=3, treads=4, lane_width_m="1.00",
                      riser_m="0.17", tread_t_m="0.02")
    assert t["tread_m2"] == X("1.00")                         # region area whatever the subdivision
    assert r6(t["step_lm_at_least"]) == X("4.000000") and r6(t["riser_m2_at_least"]) == X("0.600000")
    assert t["pitch"].startswith("HELD")


def test_turn_needs_section_count():
    with pytest.raises(R.Refused):
        R.turn_region(region_m2="1.00", risers_section=4, governing="PLAN", treads=4, lane_width_m="1.00",
                      riser_m="0.17", tread_t_m="0.02")
    with pytest.raises(R.Refused):                            # missing region: never 0
        R.turn_region(region_m2=None, risers_section=4, treads=4, lane_width_m="1.00", riser_m="0.17",
                      tread_t_m="0.02")
    with pytest.raises(R.Refused):                            # treads not risers or risers - 1
        R.turn_region(region_m2="1.00", risers_section=4, treads=2, lane_width_m="1.00", riser_m="0.17",
                      tread_t_m="0.02")


def test_tiling_is_subdivision_independent():
    # any split of a 1.00 x 1.00 region into wedges from the inner corner sums to the region (4 random fans)
    rnd = random.Random(715)
    for _ in range(4):
        cuts = sorted(rnd.uniform(0, 2) for _ in range(3))           # positions along the 2.00 m outer boundary
        pts = [0.0] + cuts + [2.0]
        area = 0.0
        for a, b in zip(pts, pts[1:]):                                # triangle (inner corner, boundary a, boundary b)
            def xy(s):
                return (s, 1.0) if s <= 1.0 else (1.0, 2.0 - s)
            (x1, y1), (x2, y2) = xy(a), xy(b)
            if a < 1.0 < b:                                           # wedge crosses the outer corner: split it
                area += abs(x1 * 1.0 - y1 * 1.0) / 2 + abs(1.0 * y2 - 1.0 * x2) / 2
            else:
                area += abs(x1 * y2 - y1 * x2) / 2
        assert abs(area - 1.0) < 1e-12


# ------------------------------------------------------------------ R-T715-3 carrier
def test_carrier_normal_and_adverse():
    lines = {("GF:f2", "FIN.MARBLE.RISER"): "HELD", ("GF:f3", "FIN.MARBLE.TREAD"): "EXCLUDED"}
    assert R.carrier_check("1F:f4", "GF:f2", "FIN.MARBLE.RISER", lines)["class_after"] == "NOT_APPLICABLE"
    with pytest.raises(R.Refused):                            # no carrier line of the same code
        R.carrier_check("1F:f4", "GF:f2", "FIN.STAIR.FLIGHT", lines)
    with pytest.raises(R.Refused):                            # carrier itself excluded
        R.carrier_check("1F:f9", "GF:f3", "FIN.MARBLE.TREAD", lines)
    with pytest.raises(R.Refused):
        R.carrier_check("GF:f2", "GF:f2", "FIN.MARBLE.RISER", lines)


# ------------------------------------------------------------------ R-T715-4 skirting
def test_skirt_forms_hand():
    s = R.skirt_forms(plan_m="0.56", risers_in=2, riser_m="0.17", run_m="2.52", rise_m="1.70", returns_m="0.05")
    assert r6(s["zigzag_lm"]) == X("0.950000")                # 0.56 + 2 x 0.17 + 0.05
    assert r6(s["sloped_lm"]) == X("0.725512")                # 0.56 x 3.039803 / 2.52 + 0.05


def test_lone_step_has_no_sloped_figure():
    s = R.skirt_forms(plan_m="0", risers_in=1, riser_m="0.17", run_m=None, rise_m=None)
    assert s["zigzag_lm"] == X("0.17") and s["sloped_lm"] is None
    with pytest.raises(R.Refused):
        R.skirt_forms(plan_m="0", risers_in=0, riser_m="0.17", run_m=None, rise_m=None)


def test_sloped_never_exceeds_zigzag():
    rnd = random.Random(7150)
    for _ in range(200):
        run = X(str(round(rnd.uniform(0.6, 4.0), 3)))
        n = rnd.randint(2, 16)
        r = X(str(round(rnd.uniform(0.15, 0.19), 4)))
        plan = X(str(round(rnd.uniform(0.05, float(run)), 3)))
        k = min(n, int(float(plan) / float(run) * n) + 1)
        s = R.skirt_forms(plan_m=plan, risers_in=k, riser_m=r, run_m=run, rise_m=r * n)
        assert s["sloped_lm"] <= s["zigzag_lm"] + X("1e-30") or k == 0


def test_corner_turn_hand_and_mirror():
    c = R.corner_turn(plan_a_m="1.0", plan_b_m="1.0", turn_rise_m="0.68")
    assert r6(c["zig_pair"]) == X("2.680000")
    assert r6(c["slo_pair"][0]) == X("2.112439") and r6(c["slo_pair"][1]) == X("2.209297")
    m = R.corner_turn(plan_a_m="1.2", plan_b_m="0.9", turn_rise_m="0.5")
    n = R.corner_turn(plan_a_m="0.9", plan_b_m="1.2", turn_rise_m="0.5")     # mirror: walls swapped
    assert m["zig_pair"] == n["zig_pair"] and m["slo_pair"] == n["slo_pair"] and m["zig_a"] == n["zig_b"]
    with pytest.raises(R.Refused):
        R.corner_turn(plan_a_m="1.0", plan_b_m="1.0", turn_rise_m=None)


@pytest.mark.parametrize("kw", [dict(cls="AT_LEAST", low="0"), dict(cls="AT_MOST", high="0"),
                                dict(cls="BLANK_NAMED"), dict(cls="MEASURED"), dict(cls="RANGE", low="2", high="1"),
                                dict(cls="AT_LEAST", low="1", high="2"), dict(cls="WHATEVER")])
def test_statement_guards(kw):
    cls = kw.pop("cls")
    with pytest.raises(R.Refused):
        R.statement("L-x", cls, status="HELD", cause="c", **kw)


def test_statement_directed_rounding():
    assert R.statement("L-x", "AT_LEAST", low=X("1.0000009"), status="s", cause="c")["low"] == "1.000000"
    assert R.statement("L-x", "AT_MOST", high=X("1.0000001"), status="s", cause="c")["high"] == "1.000001"


# ------------------------------------------------------------------ development villa (committed inputs only)
import t715_alsenan as A  # noqa: E402

LED = A.build()
BYID = {r["line_id"]: r for r in LED["lines"]}


def _a(prefix):
    (r,) = [v for k, v in BYID.items() if k.startswith(prefix)]
    return r["after"]


def test_census_complete_by_id():
    assert len(LED["lines"]) == 85
    for r in LED["lines"]:
        a = r["after"]
        for k in ("value", "low", "high"):
            assert a[k] is None or X(a[k]) > 0, r["line_id"]           # never 0
        if a["class"] == "NOT_APPLICABLE":
            assert a["cause"]


def test_alsenan_pins():
    assert _a("L-ecc450d6cc")["value"] == "1.571667"        # MS1-L riser 10 x 1.15 x (4.50/27 - 0.03)
    assert _a("L-12f56cbfe7")["value"] == "1.904400"        # MS2-U riser 12 x 1.15 x 0.138
    assert _a("L-b4660de0dd")["value"] == "1.322500"        # MS1-T winder tread region (T-493)
    assert _a("L-e085c168de")["low"] == "5.750000"          # MS1-T step lm >= 5 x 1.15
    assert _a("L-95b9555dd1")["low"] == "13.796400"         # RS-C step lm smaller reading
    assert _a("L-1fcec3328c")["low"] == "20.423364"         # ST-01 soffit >= 17.197803 + 3.225561
    assert _a("L-c77e3887f7")["low"] == "4.460946"
    assert _a("L-6cf11c2d30")["class"] == "NOT_APPLICABLE"  # RS-C seen through from 1F
    assert _a("L-c6724654ee")["class"] == "BLANK_NAMED"     # MS1-T pitch line, D-67


def test_skirting_pair_matches_t508():
    p = LED["skirting_form_pair"]
    assert abs(X(p["sum_zigzag_lm"]) - X("23.300481")) < X("0.00001")
    assert abs(X(p["sum_sloped_lm"]) - X("17.009049")) < X("0.00001")
    assert X(p["payable_bound_lm"][0]) <= X(p["payable_bound_lm"][1])


def test_ledger_reproduces():
    js = json.dumps(LED, indent=1, sort_keys=True) + "\n"
    assert (ROOT / "research" / "agents_t715" / "out" / "T715_LEDGER.json").read_text() == js
