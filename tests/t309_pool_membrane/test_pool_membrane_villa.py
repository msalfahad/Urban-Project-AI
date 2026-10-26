"""T-309 pool membrane / protection screed, face by face, on hand-calculated NON-Alsenan pools.

Villa P309 (rectangle 5.00 x 3.00 outer, walls 0.25, base 0.30, levels underside -1.50 / base top -1.20 / rim +0.20,
screed 0.04, membrane 0.03) and villa D309 (D: back 4.00, sides 2.00, half circle r 2.00). Hand values worked on paper
from the fixtures' own numbers. Normal and adverse cases (ENGINEERING_REASONING_STANDARD s.4 C).
"""

from __future__ import annotations

import copy
import importlib.util
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t309_pool_membrane",
                                               ROOT / "research" / "agents_t309" / "t309_pool_membrane.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

LV = {"rim": 0.20, "base_top_structural": -1.20, "base_underside": -1.50, "deck_finish": 0.05}
LAYERS = {"screed_t": 0.04, "membrane_t": 0.03}
COV = {"base_underside": True, "outer_walls": True, "outer_walls_to": "WALL_TOP", "water_faces": False,
       "wall_top": False, "source": "villa P309 pool detail"}


def approx(x):
    return pytest.approx(x, abs=1e-9)


def rect(edges=("NO_DECK",) * 4, order=(0, 1, 2, 3)):
    segs = [{"id": "N", "kind": "STRAIGHT", "length": 5.0, "edge": edges[0], "square_corners": 1},
            {"id": "E", "kind": "STRAIGHT", "length": 3.0, "edge": edges[1], "square_corners": 1},
            {"id": "S", "kind": "STRAIGHT", "length": 5.0, "edge": edges[2], "square_corners": 1},
            {"id": "W", "kind": "STRAIGHT", "length": 3.0, "edge": edges[3], "square_corners": 1}]
    return {"unit": "m", "wall_face_basis": "STRUCTURAL", "outer_area": 15.0, "outer_perimeter": 16.0,
            "water_area": 11.25, "water_perimeter": 14.0, "base_t": 0.30, "levels": dict(LV),
            "segments": [segs[i] for i in order]}


# ------------------------------------------------------------------------------------------------ normal cases

def test_rect_no_deck_by_hand():
    led = M.ledger(rect(), LAYERS, COV)
    # membrane on the protected faces: base 15.00 + outer 16.00 x (0.20 + 1.50) = 15.00 + 27.20 = 42.20 m2
    assert led["membrane"]["quantity"] == approx(42.2)
    assert led["membrane"]["status"] == M.DRAWING_CONFIRMED
    # screed: sheet (15 + 16 x 0.04 + 4 x 0.04^2) x 0.04 = 15.6464 x 0.04 = 0.625856
    #         bands (16 x 0.04 + 4 x 0.0016) x 1.70 = 0.6464 x 1.70 = 1.09888  -> 1.724736 m3
    assert led["screed"]["quantity"] == approx(1.724736)
    # closure: 15 + 27.2 + 11.25 + 14 x 1.40 + 3.75 = 76.80 m2, residual 0
    c = led["closure"]
    assert c["shell_total_m2"] == approx(76.8)
    assert c["residual_m2"] == approx(0.0)
    assert c["by_status_m2"][M.COVERED] == approx(42.2)
    assert c["by_status_m2"][M.NOT_COVERED] == approx(11.25 + 19.6 + 3.75)
    # information: membrane inner surface 15.6464 + (16 + 8 x 0.04) x 1.74 = 15.6464 + 28.3968 = 44.0432
    assert led["membrane"]["layer_surface_info"]["membrane_inner_surface_m2"] == approx(44.0432)


def test_rect_deck_on_two_long_sides_upstand_unresolved():
    led = M.ledger(rect(edges=("DECK", "NO_DECK", "DECK", "NO_DECK")), LAYERS, COV)
    # upstand +0.05 -> +0.20 on 2 x 5.00: 1.50 m2 UNRESOLVED (blank), covered 42.20 - 1.50 = 40.70
    assert led["membrane"]["quantity"] == approx(40.7)
    assert led["membrane"]["unresolved_bound_m2"] == [0.0, approx(1.5)]
    # screed: each long band (5 x 0.04 + 0.0016) x 0.15 = 0.03024 left out -> 1.724736 - 0.06048 = 1.664256
    assert led["screed"]["quantity"] == approx(1.664256)
    assert led["screed"]["unresolved_bound_m3"] == [0.0, approx(0.06048)]
    up = [r for r in led["rows"] if r["status"] == M.UNRESOLVED]
    assert len(up) == 2 and all(r["membrane_m2"] is None and r["screed_m3"] is None for r in up)
    assert led["closure"]["residual_m2"] == approx(0.0)


def test_d_pool_by_hand_and_segment_order_mirror():
    lv = {"rim": 0.30, "base_top_structural": -1.00, "base_underside": -1.35, "deck_finish": 0.30}
    sh = M.d_shell(4.0, 2.0, 0.25, 0.35, lv)
    # outer A = 4 x 2 + pi 4 / 2 = 14.283185; P = 4 + 4 + 2 pi = 14.283185 (same number by coincidence of r = 2)
    assert sh["outer_area"] == approx(8 + 2 * math.pi)
    led = M.ledger(sh, {"screed_t": 0.05, "membrane_t": 0.05}, COV)
    P = 8 + 2 * math.pi
    # deck finish = rim: no upstand; membrane = A + P x 1.65
    assert led["membrane"]["quantity"] == approx(8 + 2 * math.pi + P * 1.65)
    # screed: bands = back 4 x 0.05 + 2 x 0.0025 + sides 2 x 2 x 0.05 + arc pi/2 (2.05^2 - 2^2) = 0.205 + 0.2 + 0.318086
    bands = 0.205 + 0.2 + math.pi / 2 * (2.05 ** 2 - 4.0)
    assert led["screed"]["quantity"] == approx((8 + 2 * math.pi + bands) * 0.05 + bands * 1.65)
    # mirror / order: reversing the segment list changes nothing
    sh2 = copy.deepcopy(sh)
    sh2["segments"] = list(reversed(sh2["segments"]))
    led2 = M.ledger(sh2, {"screed_t": 0.05, "membrane_t": 0.05}, COV)
    assert led2["membrane"]["quantity"] == approx(led["membrane"]["quantity"])
    assert led2["screed"]["quantity"] == approx(led["screed"]["quantity"])


def test_hatch_ending_below_the_rim_leaves_the_top_not_covered():
    cov = dict(COV, outer_walls_to=-0.10)
    led = M.ledger(rect(), LAYERS, cov)
    # covered 15 + 16 x 1.40 = 37.40; above the end 16 x 0.30 = 4.80 NOT_COVERED
    assert led["membrane"]["quantity"] == approx(37.4)
    assert led["closure"]["residual_m2"] == approx(0.0)


def test_consumer_shape_and_sourced_function():
    led = M.ledger(rect(), LAYERS, COV, function={"label": "waterproofing", "source": "spec clause 7.2"})
    lines = M.consumer_lines(led, "POOL-X", "villa P309 detail")
    assert [l["unit"] for l in lines] == ["m2", "m3"]
    assert lines[0]["key"].startswith("WP.POOL_TANK.POOL_MEMBRANE[m2]/POOL-X/")
    assert lines[0]["function"]["status"] == M.DRAWING_CONFIRMED


# ------------------------------------------------------------------------------------------------ adverse cases

def test_hatch_extended_to_a_face_it_does_not_cover_is_refused():
    led = M.ledger(rect(edges=("DECK", "NO_DECK", "DECK", "NO_DECK")), LAYERS, COV)
    for face in ("WATER-WALLS", "WATER-FLOOR", "WALL-TOP", "OUT-N-upstand"):
        with pytest.raises(M.RefusedInput):
            M.book(led, face, "membrane")
    assert M.book(led, "BASE-U", "membrane")["status"] == M.COVERED
    with pytest.raises(M.RefusedInput):
        M.ledger(rect(), LAYERS, dict(COV, water_faces=True))


def test_finished_wall_used_for_the_structural_face_is_refused():
    sh = rect()
    sh["wall_face_basis"] = "FINISHED"
    with pytest.raises(M.RefusedInput):
        M.ledger(sh, LAYERS, COV)
    sh = rect()
    sh["base_t"] = 0.25  # levels say 0.30
    with pytest.raises(M.RefusedInput):
        M.ledger(sh, LAYERS, COV)


def test_missing_layer_is_held_never_zero():
    led = M.ledger(rect(), {"screed_t": None, "membrane_t": 0.03}, COV)
    assert led["screed"]["quantity"] is None and led["screed"]["status"] == M.HELD
    assert led["membrane"]["quantity"] == approx(42.2)
    led = M.ledger(rect(), {"screed_t": 0.04, "membrane_t": None}, COV)
    assert led["membrane"]["quantity"] is None and led["membrane"]["status"] == M.HELD
    with pytest.raises(M.RefusedInput):
        M.ledger(rect(), {"screed_t": 0.0, "membrane_t": 0.03}, COV)


def test_function_label_without_source_is_refused():
    with pytest.raises(M.RefusedInput):
        M.ledger(rect(), LAYERS, COV, function={"label": "insulation"})
    with pytest.raises(M.RefusedInput):
        M.ledger(rect(), LAYERS, COV, function="waterproofing")
    assert M.ledger(rect(), LAYERS, COV)["membrane"]["function"]["status"] == M.HELD


def test_mm_units_are_refused():
    sh = rect()
    sh["unit"] = "mm"
    with pytest.raises(M.RefusedInput):
        M.ledger(sh, LAYERS, COV)
    with pytest.raises(M.RefusedInput):
        M.ledger(rect(), {"screed_t": 40, "membrane_t": 0.03}, COV)


def test_face_booked_twice_or_open_perimeter_is_refused():
    sh = rect()
    sh["segments"][1]["id"] = "N"
    with pytest.raises(M.RefusedInput):
        M.ledger(sh, LAYERS, COV)
    sh = rect()
    sh["segments"].pop()
    with pytest.raises(M.RefusedInput):
        M.ledger(sh, LAYERS, COV)
