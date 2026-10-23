"""T-209: wet-room wall tile m2 on a NON-Alsenan hand fixture (villa T209-V) with adverse cases.

Villa T209-V (hand truth, m): bathroom 2.40 x 1.80, wall-face run 2 x (2.40 + 1.80) = 8.40 m, tile height H = 2.60
(floor to the underside of the decor ceiling), one door 0.80 (head not printed -> 2.20 owner fallback Q-55 C), one
window 0.60 wide, sill 1.50, head 2.70 above the finished floor: it crosses the tile line.
  gross 8.40 x 2.60 = 21.840; door 0.80 x 2.20 = 1.760; window inside the band 0.60 x (2.60 - 1.50) = 0.660;
  net 21.840 - 1.760 - 0.660 = 19.420 m2.
  Q-48 rough convention (8.40 - 0.80) x 2.60 - 0.660 = 19.100; difference = over-door band 0.80 x (2.60 - 2.20) = 0.320.
  wall mortar 19.42 x 0.02 = 0.3884 m3; owner 8 bags / m3 -> 3.1072 bags; sand 1.10 -> 0.42724 m3; adhesive 19.42 / 5
  = 3.884 bags (buy 4).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t209"))

import wet_wall_tiles as T                                               # noqa: E402

DOOR = {"id": "D1", "w": 0.80, "head": None, "fallback": True}
WIN = {"id": "W1", "w": 0.60, "sill": 1.50, "head": 2.70}


def test_normal_window_across_the_tile_line():
    r = T.room_tile(8.40, 2.60, [DOOR], [WIN])
    assert r["status"] == "OK"
    assert r["gross"] == 21.84 and r["doors_lo"] == 1.76 and r["windows"] == 0.66
    assert r["net_lo"] == r["net_hi"] == 19.42


def test_q48_rough_and_over_door_band_reconcile():
    rough = T.q48_rough(8.40, 2.60, [DOOR], [WIN])
    assert rough == 19.10
    assert T.over_door_band(2.60, [DOOR]) == 0.32
    assert round(T.room_tile(8.40, 2.60, [DOOR], [WIN])["net_lo"] - rough, 4) == 0.32


def test_adverse_window_above_the_band_deducts_nothing():
    high = {"id": "W2", "w": 0.60, "sill": 2.70, "head": 3.20}
    r = T.room_tile(8.40, 2.60, [DOOR], [high])
    assert r["windows"] == 0.0 and r["net_lo"] == 20.08


def test_adverse_window_head_above_band_only_the_part_inside_counts():
    tall = {"id": "W3", "w": 1.00, "sill": 0.00, "head": 3.00}
    assert T.window_band(1.00, 0.00, 3.00, 2.60) == pytest.approx(2.60)
    r = T.room_tile(8.40, 2.60, [], [tall])
    assert r["net_lo"] == pytest.approx(21.84 - 2.60)


def test_adverse_missing_room_height_is_held_never_zero():
    r = T.room_tile(8.40, None, [DOOR], [WIN])
    assert r["status"] == "HELD" and r["gross"] is None and r["net_lo"] is None and r["net_hi"] is None
    assert T.q48_rough(8.40, None, [DOOR], [WIN]) is None
    assert T.materials(None) is None


def test_adverse_missing_face_length_is_held():
    r = T.room_tile(None, 2.60, [DOOR], [WIN])
    assert r["status"] == "HELD" and r["net_lo"] is None


def test_adverse_window_without_sill_is_a_held_range():
    w = {"id": "W4", "w": 0.60, "sill": None, "head": None}
    r = T.room_tile(8.40, 2.60, [DOOR], [w])
    assert r["status"] == "HELD" and "W4" in r["why"]
    assert r["net_hi"] == pytest.approx(21.84 - 1.76)            # no deduction
    assert r["net_lo"] == pytest.approx(21.84 - 1.76 - 0.60 * 2.60)  # full band
    assert T.q48_rough(8.40, 2.60, [DOOR], [w]) is None


def test_adverse_unprinted_arch_without_fallback_is_a_held_range():
    arch = {"id": "A1", "w": 1.00, "head": None, "fallback": False}
    r = T.room_tile(8.40, 2.60, [arch], [])
    assert r["status"] == "HELD"
    assert r["net_hi"] == 21.84 and r["net_lo"] == pytest.approx(21.84 - 2.60)


def test_mirror_and_rotation_do_not_change_the_quantity():
    # the inputs are run lengths and opening sizes; a mirrored or rotated room gives the same runs in another order
    a = T.room_tile(8.40, 2.60, [DOOR], [WIN])
    b = T.room_tile(1.80 + 2.40 + 1.80 + 2.40, 2.60, [dict(DOOR)], [dict(WIN)])
    assert a["net_lo"] == b["net_lo"]


def test_adverse_millimetre_inputs_are_refused():
    with pytest.raises(ValueError):
        T.room_tile(8.40, 2600, [DOOR], [WIN])
    with pytest.raises(ValueError):
        T.room_tile(8400, 2.60, [DOOR], [WIN])
    with pytest.raises(ValueError):
        T.window_band(0.60, 2.70, 1.50, 2.60)


def test_materials_owner_and_theory_side_by_side():
    m = T.materials(19.42)
    assert m["mortar_m3"] == 0.3884 and m["cement_bags_owner"] == 3.1072 and m["sand_m3_owner"] == 0.4272
    assert m["mortar_m3_with_waste"] == pytest.approx(0.3884 * 1.05, abs=1e-4)
    assert m["cement_bags_theory"] == pytest.approx(0.3884 * 7.6608, abs=1e-3)
    assert m["adhesive_bags"] == 3.884 and T.buy(m["adhesive_bags"]) == 4
    assert T.buy(4.0) == 4
