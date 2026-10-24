"""T-219 villa U (synthetic, NOT Alsenan): every expected value by hand in the comments.

Villa U, footing detail chain printed: 5 cm screed / 2 cm membrane / 10 cm blinding, membrane and screed end at the
footing faces. Types: A 1.50 x 1.20 x 0.40, B 2.00 x 2.00 x 0.50, C 1.10 x 1.10 x 0.30 drawn notched 0.30 x 0.20 where
B lies (one bottom stack). Lift pit: base 3.10 x 3.40 x 0.60, ring outer 1.90 x 2.10, screed 5 cm.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t219"))
import foundation_wp_v1 as W  # noqa: E402

CHAIN = W.UnderlayChain(0.05, 0.02, 0.10, "FOOTING_OUTLINE", None, "villa U detail D-1")
SIDE_HELD = W.SideDetails("LIQUID_2_LAYERS", "SHEET_MEMBRANE", None, "detail depends on the formation (not printed)")


def rect(a, b):
    return [(0.0, 0.0), (a, 0.0), (a, b), (0.0, b)]


def villa_u(transform=lambda p: p, unit="m", k=1.0):
    def T(pts):
        return [tuple(c * k for c in transform(p)) for p in pts]
    notched = [(0.0, 0.0), (0.80, 0.0), (0.80, 0.20), (1.10, 0.20), (1.10, 1.10), (0.0, 1.10)]
    return [
        W.Footing("A1", ("A",), T(rect(1.50, 1.20)), unit, 0.40),
        W.Footing("B1", ("B",), T(rect(2.00, 2.00)), unit, 0.50,
                  contacts=(W.Contact("C1 clip", 0.50, 0.30, "DRAWING-CONFIRMED"),)),
        W.Footing("C1", ("C",), T(notched), unit, 0.30,
                  contacts=(W.Contact("B1 clip", 0.50, 0.30, "DRAWING-CONFIRMED"),)),
    ]


def run(fs, chain=CHAIN, side=SIDE_HELD):
    cs = [c for f in fs for c in W.footing_components(f, chain, side)]
    return cs, W.totals(cs)


def test_membrane_and_screed_by_hand():
    cs, t = run(villa_u())
    # A 1.50 x 1.20 = 1.80; B 2.00 x 2.00 = 4.00; C 1.21 - 0.30 x 0.20 = 1.15 -> 6.95 m2
    assert t["WP.FOOTING_MEMBRANE|m2"]["measured"] == pytest.approx(6.95)
    assert t["SCREED.FOOTING_PROTECTION|m2"]["measured"] == pytest.approx(6.95)
    assert t["SCREED.FOOTING_PROTECTION|m3"]["measured"] == pytest.approx(0.3475)      # 6.95 x 0.05
    assert all(c.status == W.DC for c in cs if c.item == "WP.FOOTING_MEMBRANE")


def test_side_faces_both_readings_held_never_zero():
    cs, t = run(villa_u())
    sides = {c.element: c for c in cs if c.item == "WP.FOOTING_SIDES"}
    # single (liquid, perimeter x H): A 5.40 x 0.40 = 2.16; B 8.00 x 0.50 - 0.50 x 0.30 = 3.85; C 4.40 x 0.30 - 0.15 = 1.17
    # double (sheet down to the blinding, H + 0.07): A 5.40 x 0.47 = 2.538; B 8 x 0.57 - 0.15 = 4.41; C 4.4 x 0.37 - 0.15
    exp = {"FTG:A1": (2.16, 2.538), "FTG:B1": (3.85, 4.41), "FTG:C1": (1.17, 1.478)}
    for el, (s, d) in exp.items():
        c = sides[el]
        assert c.status == W.HELD and c.qty is None
        assert c.readings["single:LIQUID_2_LAYERS"] == pytest.approx(s)
        assert c.readings["double:SHEET_MEMBRANE"] == pytest.approx(d)
        assert (c.low, c.high) == (pytest.approx(s), pytest.approx(d))
    assert t["WP.FOOTING_SIDES|m2"]["measured"] == 0.0 and t["WP.FOOTING_SIDES|m2"]["measured_n"] == 0
    assert t["WP.FOOTING_SIDES|m2"]["held_low"] == pytest.approx(7.18)
    assert t["WP.FOOTING_SIDES|m2"]["held_high"] == pytest.approx(8.426)


def test_side_faces_released_only_when_the_detail_is_selected():
    side = W.SideDetails("LIQUID_2_LAYERS", "SHEET_MEMBRANE", "single")
    cs, t = run(villa_u(), side=side)
    assert t["WP.FOOTING_SIDES|m2"]["measured"] == pytest.approx(7.18)
    assert t["WP.FOOTING_SIDES|m2"]["measured_n"] == 3


@pytest.mark.parametrize("name,tf", [
    ("rotate30", lambda p: (p[0] * math.cos(0.5236) - p[1] * math.sin(0.5236),
                            p[0] * math.sin(0.5236) + p[1] * math.cos(0.5236))),
    ("mirror", lambda p: (-p[0], p[1])),
    ("shift", lambda p: (p[0] + 1234.5, p[1] - 87.25)),
])
def test_rotation_mirror_shift_identical(name, tf):
    _, t0 = run(villa_u())
    _, t1 = run(villa_u(tf))
    for k in t0:
        assert t1[k]["measured"] == pytest.approx(t0[k]["measured"], abs=1e-9), (name, k)
        if t0[k]["held_low"] is not None:
            assert t1[k]["held_low"] == pytest.approx(t0[k]["held_low"], abs=1e-9)


def test_millimetres_declared_identical_undeclared_refused():
    _, t0 = run(villa_u())
    _, t1 = run(villa_u(unit="mm", k=1000.0))
    assert t1["WP.FOOTING_MEMBRANE|m2"]["measured"] == pytest.approx(t0["WP.FOOTING_MEMBRANE|m2"]["measured"])
    with pytest.raises(W.RefusedError, match="not declared"):
        run(villa_u(unit=None, k=1000.0))
    with pytest.raises(W.RefusedError, match="not an isolated footing"):
        run(villa_u(unit="m", k=1000.0))                                  # mm values declared as metres


def test_adverse_blinding_counted_as_membrane_refused():
    f = W.Footing("A1", ("A",), rect(1.50, 1.20), "m", 0.40, projection_m=0.10)
    with pytest.raises(W.RefusedError, match="BLINDING"):
        W.footing_components(f, CHAIN, SIDE_HELD)
    wider = W.UnderlayChain(0.05, 0.02, 0.10, "BLINDING_OUTLINE", None, "x")
    with pytest.raises(W.RefusedError, match="projection"):
        W.footing_components(W.Footing("A1", ("A",), rect(1.5, 1.2), "m", 0.4), wider, SIDE_HELD)


def test_adverse_upturn_invented_refused():
    f = W.Footing("A1", ("A",), rect(1.50, 1.20), "m", 0.40, upturn_m=0.20)
    with pytest.raises(W.RefusedError, match="UP-WP-003"):
        W.footing_components(f, CHAIN, SIDE_HELD)


def test_two_tags_on_one_outline_held_with_both_readings():
    # one 2.60 x 1.20 outline tagged A + C: outline 3.12; rows separately 1.80 + 1.21 = 3.01
    f = W.Footing("AC", ("A", "C"), rect(2.60, 1.20), "m", None, rows_separately_m2=1.80 + 1.21)
    cs = W.footing_components(f, CHAIN, SIDE_HELD)
    m = [c for c in cs if c.item == "WP.FOOTING_MEMBRANE"][0]
    assert m.status == W.HELD and m.qty is None
    assert (m.low, m.high) == (pytest.approx(3.01), pytest.approx(3.12))
    s3 = [c for c in cs if c.item == "SCREED.FOOTING_PROTECTION" and c.unit == "m3"][0]
    assert s3.status == W.HELD and (s3.low, s3.high) == (pytest.approx(0.1505), pytest.approx(0.156))
    t = W.totals(cs)
    assert t["WP.FOOTING_MEMBRANE|m2"]["measured"] == 0.0                # never inside a measured total


def test_nothing_printed_is_held_not_zero():
    none = W.UnderlayChain(None, None, 0.10, "FOOTING_OUTLINE", None, "no chain")
    cs = W.footing_components(W.Footing("A1", ("A",), rect(1.5, 1.2), "m", 0.4), none, SIDE_HELD)
    for c in cs:
        assert c.status == W.HELD and c.qty is None


def test_procurement_held_without_a_printed_product():
    cs, t = run(villa_u())
    p = [c for c in cs if c.item == "WP.FOOTING_MEMBRANE_PROCUREMENT"]
    assert all(c.status == W.HELD and "PRODUCT_NOT_PRINTED" in c.held_why for c in p)
    printed = W.UnderlayChain(0.05, 0.02, 0.10, "FOOTING_OUTLINE", "SBS 4 mm sheet", "spec")
    c = W.procurement("FTG:A1", printed)
    assert c.status == W.HELD and "UP-WP-LAY-001" in c.held_why          # layout belongs to the owner's layout rule


def _pit(h):
    return W.LiftPit("L1", rect(3.10, 3.40), [(0.6, 0.65), (2.5, 0.65), (2.5, 2.75), (0.6, 2.75)], "m", 0.60, 0.05, h)


def test_lift_pit_by_hand_height_printed():
    t = W.totals(W.lift_pit_components(_pit(1.20)))
    # base 3.10 x 3.40 = 10.54, perimeter 13.00; envelope 1.90 x 2.10 = 3.99, perimeter 8.00
    # membrane fixed 10.54 + 13.00 x 0.65 (8.45) + (10.54 - 3.99 = 6.55) = 25.54; walls 8.00 x 1.20 = 9.60
    assert t["WP.LIFT_PIT_MEMBRANE_FIXED|m2"]["measured"] == pytest.approx(25.54)
    assert t["WP.LIFT_PIT_MEMBRANE_WALLS|m2"]["measured"] == pytest.approx(9.60)
    assert t["WP.LIFT_PIT_BOARD_FIXED|m2"]["measured"] == pytest.approx(15.00)      # 8.45 + 6.55, none under the base
    assert t["WP.LIFT_PIT_BOARD_WALLS|m2"]["measured"] == pytest.approx(9.60)
    assert t["SCREED.LIFT_PIT_BASE|m3"]["measured"] == pytest.approx(0.527)          # 10.54 x 0.05


def test_lift_pit_without_height_is_held_never_zero():
    cs = W.lift_pit_components(_pit(None))
    walls = [c for c in cs if c.item in ("WP.LIFT_PIT_MEMBRANE_WALLS", "WP.LIFT_PIT_BOARD_WALLS")]
    assert len(walls) == 2 and all(c.status == W.HELD and c.qty is None for c in walls)
    assert all(c.readings["per_m_height"] == pytest.approx(8.0) for c in walls)
    t = W.totals(cs)
    assert t["WP.LIFT_PIT_MEMBRANE_WALLS|m2"]["held_open"] is True
    assert t["WP.LIFT_PIT_MEMBRANE_FIXED|m2"]["measured"] == pytest.approx(25.54)    # fixed parts stay measured


def test_lift_pit_envelope_outside_base_refused():
    bad = W.LiftPit("L1", rect(1.0, 1.0), rect(2.0, 2.0), "m", 0.6, 0.05, None)
    with pytest.raises(W.RefusedError, match="not inside"):
        W.lift_pit_components(bad)
