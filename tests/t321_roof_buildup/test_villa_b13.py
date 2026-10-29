"""T-321 hand-calculated fixture, NOT Alsenan: villa 'B13' with two roof zones.

R-MAIN: a 10.00 x 6.00 m roof inside its parapet faces on three sides, the upper floor's wall on the fourth (y = 6),
one outlet at the south-west corner, printed fall 1 %, membrane printed with a 0.20 m upturn, protection screed printed
0.03 m, insulation printed WITHOUT a thickness, finish hatch stopping 0.10 m short of the wall (a sill line).
  plan to the faces           10.00 x 6.00                       = 60.000 m2
  finish to its own edge      10.00 x 5.90                       = 59.000 m2
  sloped surface at 1 %       60.000 x sqrt(1 + 0.01^2)          = 60.0030 m2
  vertical faces round it     parapet 10 + 6 + 6 = 22, wall 10   = 32.000 lm (the upturn, its own item)
  protection screed volume    60.000 x 0.03                      =  1.800 m3
  insulation volume           thickness not printed              -> HELD (never a default, never 0)
  falls rise (outlet (0, 0))  EIKONAL 0.01 x sqrt(10^2 + 6^2) = 0.1166 m; AXIS 0.01 x (10 + 6) = 0.1600 m
R-STRIP: an L strip 8.00 x 1.50 + 1.50 x 2.50 = 12.000 + 3.750 = 15.750 m2.
Adverse cases: the membrane booked as insulation, an unprinted thickness defaulted, the upturn folded into the flat
area, a held quantity carried as 0, a fall given as a percentage number, mm units, mirror / rotation, a closure with an
unnamed residual."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t321"))
sys.path.insert(0, str(ROOT / "research" / "agents_t221"))
import roof_buildup as RB  # noqa: E402
import roof_falls_v1 as RF  # noqa: E402

MAIN = [(0, 0), (10, 0), (10, 6), (0, 6)]
STRIP = [(0, 0), (8, 0), (8, 4), (6.5, 4), (6.5, 1.5), (0, 1.5)]


def _main_zone():
    return RB.Zone("R-MAIN", (60.0, 60.0), (59.0, 59.0), {}, (32.0, 32.0), 0.01, "printed SLOPE 1%")


def _layers():
    return [RB.Layer("FALLS_SCREED", "PRINTED", "section 1-1"),
            RB.Layer("MEMBRANE", "PRINTED", "detail 3", upturn_height_m=0.20, upturn_source="detail 3",
                     line_id="L-wp-main"),
            RB.Layer("INSULATION", "PRINTED", "detail 3 (no thickness printed)"),
            RB.Layer("PROTECTION", "PRINTED", "detail 3", thickness_m=0.03, thickness_source="detail 3 '30 mm'"),
            RB.Layer("FINISH", "PRINTED", "finish hatch")]


def _row(rows, layer):
    return next(r for r in rows if r["layer"] == layer)


def test_hand_areas_and_owner_trades():
    assert RB.exact_area(MAIN) == pytest.approx(60.0)
    assert RB.exact_area(STRIP) == pytest.approx(15.75)
    rows = RB.zone_ledger(_main_zone(), _layers())
    assert [r["layer"] for r in rows] == list(RB.LAYERS)
    m = _row(rows, "MEMBRANE")
    assert m["owner_trade"] == "WATERPROOFING B8-06" and m["in_b13_01"] is False and m["line_state"] == "IN_LINE"
    assert m["plan_area_lo"] == 60.0 and m["sloped_area_lo"] == pytest.approx(60.003, abs=1e-4)
    assert m["upturn_lm_lo"] == 32.0 and m["upturn_height_m"] == 0.20
    f = _row(rows, "FINISH")
    assert f["edge_basis"] == "finish" and f["plan_area_lo"] == 59.0 and f["owner_trade"] == "FLOOR FINISH"
    for name in RB.B13_LAYERS:
        assert _row(rows, name)["in_b13_01"] is True


def test_printed_thickness_gives_volume_unprinted_stays_held():
    rows = RB.zone_ledger(_main_zone(), _layers())
    p = _row(rows, "PROTECTION")
    assert p["volume_lo_m3"] == pytest.approx(1.8) and p["thickness_status"] == "PRINTED"
    i = _row(rows, "INSULATION")
    assert i["thickness_m"] is None and i["volume_lo_m3"] is None and i["thickness_status"] == "HELD"
    assert i["plan_area_lo"] == 60.0          # the area is measured, the volume is held


def test_falls_rise_hand_check_and_screed_volume_held_without_t0():
    f = RF.falls_field(MAIN, [(0, 0)], 0.01, step=0.05)
    assert f["models"]["EIKONAL"]["rise_max_m"] == pytest.approx(0.01 * math.hypot(10, 6), abs=2e-3)
    assert f["models"]["AXIS"]["rise_max_m"] == pytest.approx(0.16, abs=2e-3)
    v = RB.falls_screed_volume(60.0, None, (0.05, 0.08))
    assert v["total_m3"] is None and v["status"].startswith("HELD")
    assert v["above_t0_m3"] == pytest.approx((3.0, 4.8))
    v2 = RB.falls_screed_volume(60.0, 0.04, (0.05, 0.08))
    assert v2["total_m3"] == pytest.approx((5.4, 7.2))


def test_unknown_scope_is_a_row_not_a_zero():
    lay = [RB.Layer("INSULATION", "UNKNOWN", "searched: sections, details, notes")]
    r = RB.zone_ledger(_main_zone(), lay)[0]
    assert r["status"] == "UNKNOWN" and r["volume_lo_m3"] is None
    with pytest.raises(RB.Refused):
        RB.refuse_held_as_zero(0, r["status"])
    assert RB.refuse_held_as_zero(None, r["status"])


def test_zone_hold_blanks_every_quantity():
    z = RB.Zone("R-TOP", (49.0, 49.0), None, {}, (28.0, 28.0), None, "", False, "outline on no plan")
    for r in RB.zone_ledger(z, _layers()):
        assert r["status"] == "HELD" and r["plan_area_lo"] is None and r["upturn_lm_lo"] is None


def test_adverse_membrane_booked_as_insulation_refused():
    with pytest.raises(RB.Refused, match="double count"):
        RB.check_layer(RB.Layer("MEMBRANE", "PRINTED", "detail 3", booked_trade="ROOFING B13-01"))


def test_adverse_default_thickness_refused():
    with pytest.raises(RB.Refused, match="never a default"):
        RB.check_layer(RB.Layer("INSULATION", "PRINTED", "detail 3", thickness_m=0.05))
    with pytest.raises(RB.Refused):
        RB.check_layer(RB.Layer("INSULATION", "PRINTED", "detail 3", thickness_m=0.0, thickness_source="x"))


def test_adverse_upturn_folded_into_flat_area_refused():
    with pytest.raises(RB.Refused, match="folded"):
        RB.refuse_folded_upturn(60.0, 32.0, 0.20, 60.0 + 32.0 * 0.20)
    assert RB.refuse_folded_upturn(60.0, 32.0, 0.20, 60.0)


def test_adverse_fall_as_percentage_number_refused():
    with pytest.raises(RB.Refused):
        RB.slope_factor(1.0)


def test_adverse_layer_twice_refused():
    with pytest.raises(RB.Refused):
        RB.zone_ledger(_main_zone(), [RB.Layer("FINISH", "PRINTED", "a"), RB.Layer("FINISH", "PRINTED", "b")])


def test_mm_units_mirror_and_rotation():
    mm = [(x * 1000, y * 1000) for x, y in STRIP]
    assert RB.exact_area(mm, scale=0.001) == pytest.approx(15.75)
    assert RB.exact_area([(-x, y) for x, y in STRIP][::-1]) == pytest.approx(15.75)
    rot = [(-y, x) for x, y in STRIP]
    assert RB.exact_area(rot) == pytest.approx(15.75)


def test_convex_arc_corner_exact():
    # 2 x 2 square whose north-east corner is a convex quarter circle r 1 (centre (1, 1)): 4 - 1 + pi / 4
    spec = [(0, 0), (2, 0), (2, 1), ("ARC", (1, 1), 1.0, 0.0, 90.0), (0, 2)]
    assert RB.exact_area(spec) == pytest.approx(3.0 + math.pi / 4, abs=1e-9)
    mm = [(0, 0), (2000, 0), (2000, 1000), ("ARC", (1000, 1000), 1000.0, 0.0, 90.0), (0, 2000)]
    assert RB.exact_area(mm, scale=0.001) == pytest.approx(3.0 + math.pi / 4, abs=1e-9)


def test_closure_names_every_unit():
    c = RB.closure(55.560, 52.848, [("strip", 2.0787), ("band", 0.6368)], tol=1e-3)
    assert not c["closes"] and c["unexplained"] == pytest.approx(-0.0035, abs=1e-4)
    c2 = RB.closure(60.0, 59.0, [("sill strip 10 x 0.10", 1.0)])
    assert c2["closes"]
