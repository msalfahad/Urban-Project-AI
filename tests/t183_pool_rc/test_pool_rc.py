"""T-183 POOL_RC_COMPONENTS on hand-calculated synthetic pools (NOT Alsenan: other shapes, sizes, units).

Hand values worked on paper from the fixtures' own numbers. Regression guards (ENGINEERING_REASONING_STANDARD s.4 C),
each with a normal and an adverse case:
  - pool walls omitted from concrete (a base with no wall line, walls 0, or the curved half of the ring lost),
  - base vs blinding double count (blinding inside the RC base or the RC total),
  - an RC pool classified as blockwork.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t183_pool_rc", ROOT / "research" / "agents_t183" / "t183_pool_rc.py")
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

RECT = {"unit": "mm", "outline": {"kind": "RECT", "a": 4000, "b": 6000}, "wall_t": 250, "base_t": 300,
        "wall_h": 1400, "blinding_t": 100, "screed_t": 50, "membrane_t": 10, "casting_method": "CAST_IN_PLACE"}


def approx(x):
    return pytest.approx(x, abs=1e-9)


# ---------------------------------------------------------------- normal case: a rectangular pool, mm input

def test_rect_pool_components_by_hand():
    led = P.ledger(RECT)
    c = led["concrete"]
    # base 4.00 x 6.00 x 0.30 = 7.20; water 3.50 x 5.50 = 19.25; band 24 - 19.25 = 4.75; walls 4.75 x 1.40 = 6.65
    assert c["C_BASE"]["m3"] == approx(7.2)
    assert c["D_WALLS"]["plan_m2"] == approx(4.75)
    assert c["D_WALLS"]["m3"] == approx(6.65)
    assert led["rc_total_m3"] == approx(13.85)
    # the shell is counted once: outer x (base + h) - water x h = 24 x 1.70 - 19.25 x 1.40 = 40.80 - 26.95 = 13.85
    assert led["rc_total_m3"] == approx(24 * 1.70 - 19.25 * 1.40)
    f = led["formwork"]
    assert f["outer_face_m2"] == approx(20 * 1.70) and f["water_face_m2"] == approx(18 * 1.40)
    s = led["surfaces"]
    assert s["finish_floor_m2"] == approx(19.25) and s["finish_walls_m2"] == approx(18 * 1.40)


def test_same_pool_in_m_cm_mm_gives_the_same_quantities():
    m = dict(RECT, unit="m", outline={"kind": "RECT", "a": 4, "b": 6}, wall_t=0.25, base_t=0.30, wall_h=1.40,
             blinding_t=0.10, screed_t=0.05, membrane_t=0.01)
    cm = dict(RECT, unit="cm", outline={"kind": "RECT", "a": 400, "b": 600}, wall_t=25, base_t=30, wall_h=140,
              blinding_t=10, screed_t=5, membrane_t=1)
    for other in (m, cm):
        assert P.ledger(other)["rc_total_m3"] == approx(P.ledger(RECT)["rc_total_m3"])


def test_rotation_swaps_the_sides_not_the_quantities():
    rot = dict(RECT, outline={"kind": "RECT", "a": 6000, "b": 4000})
    assert P.ledger(rot)["rc_total_m3"] == approx(13.85)
    assert P.ledger(rot)["formwork"]["m2"] == approx(P.ledger(RECT)["formwork"]["m2"])


def test_d_pool_matches_the_frozen_generic_split():
    from engine.source import pool_qto as F
    d = P.Outline("D", r=2.0, b=1.2)            # back 4.00, rectangle 1.20, half circle r 2.00
    inner = d.inset(0.25)                       # r 1.75, b 0.95
    assert d.area() == approx(4.0 * 1.2 + math.pi * 4.0 / 2)
    assert inner.area() == approx(3.5 * 0.95 + math.pi * 1.75 ** 2 / 2)
    lines = P.concrete_components(d, 0.25, 0.35, 1.30)
    band = d.area() - inner.area()
    frozen = F.wall_base_split(d.area(), band, 0.35, 1.30, footprint_authority=F.CAD_GEOMETRY,
                               band_authority=F.CAD_GEOMETRY, base_t_authority=F.STATED, wall_h_authority=F.STATED)
    assert P.rc_total(lines) == approx(frozen["shell_m3"])
    # a mirrored D (half circle on the other side) is the same outline
    assert P.Outline("D", r=2.0, b=1.2).perimeter() == approx(4.0 + 2.4 + math.pi * 2.0)


def test_d_mesh_exact_density_and_chords_by_hand():
    d = P.Outline("D", r=1.0, b=1.0)            # back 2.00, rect 1.00, half circle r 1.00; area 2 + pi / 2
    ch = d.chords("across_back", 2.0)           # extent 2.00 -> n = 4 strips, midpoints u = -0.75 -0.25 0.25 0.75
    hand = sum(1.0 + math.sqrt(1 - u * u) for u in (-0.75, -0.25, 0.25, 0.75))
    assert ch["A"] == (4, approx(hand))
    assert ch["C"][1] == approx(2.0 * (2 + math.pi / 2))
    al = d.chords("along_back", 2.0)            # extent 2.00 (b + r): midpoints 0.25 0.75 (2.00 each) 1.25 1.75
    hand_al = 2 + 2 + 2 * math.sqrt(1 - 0.25 ** 2) + 2 * math.sqrt(1 - 0.75 ** 2)
    assert al["A"] == (4, approx(hand_al))


# ---------------------------------------------------------------- guard 1: walls omitted

def test_walls_present_normal():
    assert P.assert_complete(P.concrete_components(P.Outline("RECT", a=4, b=6), 0.25, 0.30, 1.40))


def test_walls_omitted_is_refused():
    lines = P.concrete_components(P.Outline("RECT", a=4, b=6), 0.25, 0.30, 1.40)
    del lines["D_WALLS"]
    with pytest.raises(P.PoolError, match="R-POOL-2"):
        P.assert_complete(lines)


def test_walls_zero_is_refused_and_unknown_height_is_held_not_zero():
    lines = P.concrete_components(P.Outline("RECT", a=4, b=6), 0.25, 0.30, 1.40)
    lines["D_WALLS"]["m3"] = 0.0
    with pytest.raises(P.PoolError, match="never 0"):
        P.assert_complete(lines)
    held = P.concrete_components(P.Outline("RECT", a=4, b=6), 0.25, 0.30, None)
    assert held["D_WALLS"]["m3"] is None and held["D_WALLS"]["status"] == P.HELD
    assert P.rc_total(held) is None                                   # never base-only, never 0
    assert P.formwork(P.Outline("RECT", a=4, b=6), 0.25, 0.30, None, "CAST_IN_PLACE")["m2"] is None
    with pytest.raises(P.PoolError):
        P.rebar({"wall_v_out": (5, 12)}, P.Outline("RECT", a=4, b=6), 0.25, 0.30, None)


def test_curved_half_of_the_ring_lost_is_refused():
    d = P.Outline("D", r=2.0, b=1.2)
    inner = d.inset(0.25)
    full = d.area() - inner.area()
    assert P.check_wall_band(d, inner, full)
    straight_only = 0.25 * (4.0 + 2 * 1.2)        # the straight strip alone (the released engine's reading)
    with pytest.raises(P.PoolError, match="outer - water"):
        P.check_wall_band(d, inner, straight_only)


# ---------------------------------------------------------------- guard 2: base vs blinding double count

def test_blinding_is_its_own_line_and_never_in_the_rc_total():
    o = P.Outline("RECT", a=4, b=6)
    thin = P.concrete_components(o, 0.25, 0.30, 1.40, blinding_t=0.05, screed_t=0.05, membrane_t=0.01)
    thick = P.concrete_components(o, 0.25, 0.30, 1.40, blinding_t=0.15, screed_t=0.05, membrane_t=0.01)
    assert P.rc_total(thin) == approx(P.rc_total(thick)) == approx(13.85)
    # lower bound = (24 + 20 x 0.06 + pi 0.06^2) x 0.15; projection not given -> HELD, None, never 0
    assert thick["B_BLINDING"]["m3_lower_bound"] == approx((24 + 1.2 + math.pi * 0.0036) * 0.15)
    assert thick["B_BLINDING"]["m3"] is None and thick["B_BLINDING"]["status"] == P.HELD
    given = P.concrete_components(o, 0.25, 0.30, 1.40, blinding_t=0.10, screed_t=0.05, membrane_t=0.01,
                                  blinding_projection=0.10)
    assert given["B_BLINDING"]["m3"] == approx((24 + 20 * 0.16 + math.pi * 0.16 ** 2) * 0.10)


def test_blinding_inside_the_base_is_refused():
    lines = P.concrete_components(P.Outline("RECT", a=4, b=6), 0.25, 0.30, 1.40)
    lines["C_BASE"]["basis"] = "base 0.30 + blinding 0.10 as one slab"
    with pytest.raises(P.PoolError, match="R-POOL-3"):
        P.assert_complete(lines)


# ---------------------------------------------------------------- guard 3: an RC pool is never blockwork

def test_rc_pool_never_blockwork():
    assert P.concrete_components(P.Outline("RECT", a=4, b=6), 0.25, 0.30, 1.40)["C_BASE"]["m3"] == approx(7.2)
    for cls in ("BLOCKWORK", "MASONRY"):
        with pytest.raises(P.PoolError, match="R-POOL-1"):
            P.ledger(dict(RECT, element_class=cls))


# ---------------------------------------------------------------- scope and steel

def test_undrawn_steps_and_pump_room_add_nothing():
    led = P.ledger(dict(RECT, steps_drawn=False, pump_room_drawn=False))
    assert led["concrete"]["E_STEPS"]["status"] == P.NOT_DRAWN and led["concrete"]["E_STEPS"]["m3"] is None
    assert led["concrete"]["K_PUMP_ROOM"]["m3"] is None
    assert led["rc_total_m3"] == approx(13.85)


def test_formwork_only_for_a_documented_cast_in_place_pool():
    o = P.Outline("RECT", a=4, b=6)
    for method in (None, "SHOTCRETE"):
        assert P.formwork(o, 0.25, 0.30, 1.40, method)["status"] == P.UNKNOWN


def test_wall_hoops_over_the_height_above_the_base_only():
    o = P.Outline("RECT", a=4, b=6)
    rows, _ = P.rebar({"wall_h_out": (0.20, 10)}, o, 0.25, 0.30, 1.40)
    # 1.40 / 0.20 = 7 exactly: A 7, B 8, C 7.0 (not 1.70 / 0.20 = 8.5 -> 9 over base + wall)
    assert rows[0]["count"] == {"A": 7, "B": 8, "C": approx(7.0)}
    assert rows[0]["length_m"] == approx(20.0)


def test_closed_loop_verticals_and_soil_cover():
    o = P.Outline("RECT", a=4, b=6)
    rows, tot = P.rebar({"wall_v_out": (5, 12)}, o, 0.25, 0.30, 1.40)
    # outer face 20.00 m x 5 / m = 100 bars (closed loop: B = A), 1.70 m each, kg/m 144 / 162
    assert rows[0]["count"]["A"] == rows[0]["count"]["B"] == 100
    assert tot["A"] == approx(100 * 1.70 * 144 / 162)
    rows_c, _ = P.rebar({"wall_v_out": (5, 12)}, o, 0.25, 0.30, 1.40, soil_cover=0.075)
    # bar line inset 0.075: (3.85 + 5.85) x 2 = 19.40 m -> 97 bars of 1.70 - 0.075 = 1.625 m
    assert rows_c[0]["count"]["A"] == 97 and rows_c[0]["length_m"] == approx(1.625)


def test_refusals():
    with pytest.raises(P.PoolError):
        P.to_m(-1, "m")
    with pytest.raises(P.PoolError):
        P.to_m(1, "inch")
    with pytest.raises(P.PoolError):
        P.Outline("D", r=1.0, b=1.0).inset(1.5)
    with pytest.raises(P.PoolError):
        P.Outline("RECT", a=1.0, b=1.0).chords("diagonal", 5)
