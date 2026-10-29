"""R-T335-1 on a hand-calculated NON-Alsenan fixture (villa K) with adverse cases.

Villa K (hand truth, every figure by hand):
  LOUNGE 6.00 x 4.50 = 27.00 m2 plan, light well 2.00 x 2.00 = 4.00 m2 (VOID) in one corner -> decor 23.00 m2 (the
    underside of beam B1 included: it is decor, R-T295-1). Decor underside 3.00, slab soffit 3.15 (decor 0.15, Q-48 A).
    Beam B1 crosses the 4.50 width, free on both sides: 2 x 4.50 = 9.00 m of free edge; owner bulkhead face (Q-48 A +
    Q-43) 9.00 x 0.15 = 1.35 m2 (ASSUMED - OWNER-APPROVED); drawing-derived (beam bottom 2.55: drop 0.45) 4.05 m2 is an
    alternative, never in a total. Walls: perimeter 21.00 m x 3.00 = 63.00 less door 1.00 x 2.20 = 2.20 -> 60.80 m2
    plaster and 60.80 m2 paint. Hidden band 21.00 x 0.15 = 3.15 m2: HELD 0 .. 3.15 (Q-52 C).
  STORE 2.00 x 1.50 = 3.00 m2, NO decor ceiling; the fixture's specification prints 'plastered and painted soffit':
    exposed soffit plaster 3.00 + paint 3.00. Walls to the soffit 3.15 (its 'decor underside' is the soffit itself):
    perimeter 7.00 x 3.15 = 22.05 less door 0.80 x 2.20 = 1.76 -> 20.29 m2 each layer; band 0.
  BATH 2.50 x 2.00 = 5.00 m2 decor (board type HELD by name, the area DRAWING-CONFIRMED), tile to the decor underside
    2.70, soffit 2.85: perimeter 9.00 x 2.70 = 24.30 less door 0.70 x 2.10 = 1.47 -> 22.83 m2 tile; band 0 .. 1.35.
  STAIR flight underside 3.60 m2 (STAIR_SOFFIT: the stair finish), not in any ceiling or wall line.
Totals: board 28.00 (decor) + 1.35 (bulkhead); ceiling paint 28.00 + 1.35 (when a ceiling paint line exists); exposed
plaster 3.00, paint 3.00; double count 0.000 m2.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t335"))
import ceiling_cross_trade as X  # noqa: E402

DC, AOA = "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED"


def lounge_decor_m2(transform=None):
    room = Polygon([(0, 0), (6.0, 0), (6.0, 4.5), (0, 4.5)])
    well = Polygon([(4.0, 2.5), (6.0, 2.5), (6.0, 4.5), (4.0, 4.5)])
    if transform:
        room, well = transform(room), transform(well)
    return room.difference(well).area, well.area


def villa():
    S = {
        "LNG|decor": {"surface_id": "LNG|decor", "room_id": "LNG", "kind": X.DECOR, "m2": 23.0, "status": DC},
        "LNG|well": {"surface_id": "LNG|well", "room_id": "LNG", "kind": X.VOID, "m2": 4.0, "status": DC},
        "LNG|B1": {"surface_id": "LNG|B1", "room_id": "LNG", "kind": X.BULKHEAD, "m2": 1.35, "status": AOA,
                   "source": "Q-48 A + Q-43"},
        "LNG|walls": {"surface_id": "LNG|walls", "room_id": "LNG", "kind": X.WALL, "m2": 60.8, "status": AOA,
                      "top_m": 3.00, "length_m": 21.0},
        "STR|soffit": {"surface_id": "STR|soffit", "room_id": "STR", "kind": X.EXPOSED, "m2": 3.0, "status": DC},
        "STR|walls": {"surface_id": "STR|walls", "room_id": "STR", "kind": X.WALL, "m2": 20.29, "status": DC,
                      "top_m": 3.15, "length_m": 7.0},
        "BTH|decor": {"surface_id": "BTH|decor", "room_id": "BTH", "kind": X.DECOR, "m2": 5.0, "status": DC},
        "BTH|walls": {"surface_id": "BTH|walls", "room_id": "BTH", "kind": X.WALL, "m2": 22.83, "status": AOA,
                      "top_m": 2.70, "length_m": 9.0},
        "STA|soffit": {"surface_id": "STA|soffit", "room_id": "STA", "kind": X.STAIR_SOFFIT, "m2": 3.6,
                       "status": "HELD", "held_item": "stair soffit finish line (none in the candidate)"},
    }
    L = {lid: {"line_id": lid, "item_code": code} for lid, code in (
        ("L-ceil-lng", "FIN.CEILING"), ("L-ceil-bth", "FIN.CEILING"), ("L-ceilpaint-lng", "FIN.PAINT"),
        ("L-pl-lng", "FIN.PLASTER"), ("L-pa-lng", "FIN.PAINT"), ("L-pl-str", "FIN.PLASTER"), ("L-pa-str", "FIN.PAINT"),
        ("L-tile-bth", "FIN.WALL.TILE"), ("L-pl-str-soffit", "FIN.PLASTER"), ("L-pa-str-soffit", "FIN.PAINT"))}
    for lid in ("L-ceilpaint-lng", "L-pl-str-soffit", "L-pa-str-soffit"):
        L[lid]["role"] = "CEILING"      # a ceiling paint / soffit plaster line declares the surface it measures
    C = [
        {"surface_id": "LNG|decor", "layer": X.BOARD, "line_id": "L-ceil-lng"},
        {"surface_id": "LNG|B1", "layer": X.BOARD, "line_id": "L-ceil-lng"},
        {"surface_id": "LNG|decor", "layer": X.PAINT, "line_id": "L-ceilpaint-lng"},
        {"surface_id": "LNG|B1", "layer": X.PAINT, "line_id": "L-ceilpaint-lng"},
        {"surface_id": "LNG|walls", "layer": X.PLASTER, "line_id": "L-pl-lng"},
        {"surface_id": "LNG|walls", "layer": X.PAINT, "line_id": "L-pa-lng"},
        {"surface_id": "STR|soffit", "layer": X.PLASTER, "line_id": "L-pl-str-soffit"},
        {"surface_id": "STR|soffit", "layer": X.PAINT, "line_id": "L-pa-str-soffit"},
        {"surface_id": "STR|walls", "layer": X.PLASTER, "line_id": "L-pl-str"},
        {"surface_id": "STR|walls", "layer": X.PAINT, "line_id": "L-pa-str"},
        {"surface_id": "BTH|decor", "layer": X.BOARD, "line_id": "L-ceil-bth"},
        {"surface_id": "BTH|walls", "layer": X.TILE, "line_id": "L-tile-bth"},
    ]
    return S, C, L


# ----------------------------------------------------------------------------------------------- normal cases
def test_hand_truth_and_no_double_count():
    S, C, L = villa()
    assert X.validate(C, S, L)
    assert X.overlaps(C, S) == []
    r = X.cross_trade("LNG", S, C, L, decor_underside_m=3.00, band_top_m=3.15)
    assert r["carried_m2"] == {"BULKHEAD / BOARD / FIN.CEILING": 1.35, "BULKHEAD / PAINT / FIN.PAINT": 1.35,
                               "DECOR / BOARD / FIN.CEILING": 23.0, "DECOR / PAINT / FIN.PAINT": 23.0,
                               "WALL / PAINT / FIN.PAINT": 60.8, "WALL / PLASTER / FIN.PLASTER": 60.8}
    assert r["band_m2"] == (0.0, 3.15) and r["gap_m2"] == 0.0 and r["double_count_m2"] == 0.0
    s = X.cross_trade("STR", S, C, L, decor_underside_m=3.15, band_top_m=3.15)
    assert s["carried_m2"]["EXPOSED_SOFFIT / PLASTER / FIN.PLASTER"] == 3.0
    assert s["band_m2"] == (0.0, 0.0)
    b = X.cross_trade("BTH", S, C, L, decor_underside_m=2.70, band_top_m=2.85)
    assert b["band_m2"] == (0.0, 1.35) and b["carried_m2"]["WALL / TILE / FIN.WALL.TILE"] == 22.83
    board = sum(S[c["surface_id"]]["m2"] for c in C if c["layer"] == X.BOARD)
    assert board == pytest.approx(29.35, abs=1e-9)          # 23.00 + 5.00 decor + 1.35 bulkhead


def test_hand_wall_areas():
    assert 21.0 * 3.00 - 1.00 * 2.20 == pytest.approx(60.80)
    assert 7.0 * 3.15 - 0.80 * 2.20 == pytest.approx(20.29)
    assert 9.0 * 2.70 - 0.70 * 2.10 == pytest.approx(22.83)
    assert 9.0 * 0.15 == pytest.approx(1.35) and 9.0 * 0.45 == pytest.approx(4.05)


@pytest.mark.parametrize("name,tf", [
    ("identity", None),
    ("mirror", lambda g: affinity.scale(g, xfact=-1, yfact=1, origin=(0, 0))),
    ("rot37+move", lambda g: affinity.translate(affinity.rotate(g, 37, origin=(0, 0)), 812.4, -95.3)),
    ("mirror+rot-90", lambda g: affinity.rotate(affinity.scale(g, xfact=1, yfact=-1, origin=(0, 0)), -90,
                                                  origin=(0, 0))),
])
def test_decor_area_invariant_under_mirror_rotation_translation(name, tf):
    d, w = lounge_decor_m2(tf)
    assert d == pytest.approx(23.0, abs=1e-6) and w == pytest.approx(4.0, abs=1e-6)


def test_layers_on_one_face_are_not_a_double_count():
    S, C, L = villa()                          # board + paint on the lounge decor: two layers, two lines
    assert [c["line_id"] for c in C if c["surface_id"] == "LNG|decor"] == ["L-ceil-lng", "L-ceilpaint-lng"]
    assert X.overlaps(C, S) == []


def test_band_declared_held_is_a_range_not_a_quantity():
    S, C, L = villa()
    S["LNG|walls"] = dict(S["LNG|walls"], top_m=3.15, band_held=True)
    r = X.cross_trade("LNG", S, C, L, decor_underside_m=3.00, band_top_m=3.15)
    assert r["band_m2"] == (0.0, 3.15)


def test_wall_below_decor_leaves_a_named_gap():
    S, C, L = villa()
    S["LNG|walls"] = dict(S["LNG|walls"], top_m=2.95)
    r = X.cross_trade("LNG", S, C, L, decor_underside_m=3.00, band_top_m=3.15)
    assert r["gap_m2"] == pytest.approx(1.05)                # 21.00 x 0.05


# ---------------------------------------------------------------------------------------------- adverse cases
def _refuse(code, C, S, L):
    with pytest.raises(X.CrossTradeError) as e:
        X.validate(C, S, L)
    assert str(e.value).startswith(code), str(e.value)


def test_soffit_plastered_behind_a_gypsum_ceiling_refused():
    S, C, L = villa()
    # in a ceiling-role plaster line (a soffit plaster line): the layer does not fit a gypsum ceiling
    _refuse("PLASTER_BEHIND_DECOR", C + [{"surface_id": "LNG|decor", "layer": X.PLASTER, "line_id": "L-pl-str-soffit"}],
            S, L)
    # in the room's wall plaster line: a horizontal face in a wall line
    _refuse("HORIZONTAL_IN_WALL_LINE", C + [{"surface_id": "LNG|decor", "layer": X.PLASTER, "line_id": "L-pl-lng"}], S,
            L)


def test_exposed_soffit_in_the_ceiling_board_line_refused():
    S, C, L = villa()
    _refuse("BOARD_ON_EXPOSED", C + [{"surface_id": "STR|soffit", "layer": X.BOARD, "line_id": "L-ceil-lng"}], S, L)


def test_soffit_in_plaster_and_ceiling_lines_twice_refused():
    S, C, L = villa()      # the same exposed soffit plaster in its soffit line AND in the room's wall plaster line
    C2 = C + [{"surface_id": "STR|soffit", "layer": X.PLASTER, "line_id": "L-pl-str"}]
    with pytest.raises(X.CrossTradeError) as e:
        X.validate(C2, S, L)
    assert str(e.value).startswith("HORIZONTAL_IN_WALL_LINE")
    # a second soffit line of the same layer (not a wall line) is the plain double count
    L2 = dict(L, **{"L-pl-str-soffit-2": {"line_id": "L-pl-str-soffit-2", "item_code": "FIN.CEILING"}})
    C3 = C + [{"surface_id": "LNG|decor", "layer": X.BOARD, "line_id": "L-ceil-bth"}]
    with pytest.raises(X.CrossTradeError) as e:
        X.validate(C3, S, L2)
    assert str(e.value).startswith("LAYER_TWICE") and "23.0 m2" in str(e.value)
    assert X.cross_trade("LNG", S, C3, L2)["double_count_m2"] == 23.0


def test_bulkhead_band_counted_in_a_wall_line_refused():
    S, C, L = villa()
    _refuse("BULKHEAD_IN_WALL_LINE", C + [{"surface_id": "LNG|B1", "layer": X.PLASTER, "line_id": "L-pl-lng"}], S, L)


def test_wall_line_to_the_soffit_books_the_hidden_band_refused():
    S, C, L = villa()
    S["LNG|walls"] = dict(S["LNG|walls"], top_m=3.15)
    with pytest.raises(X.CrossTradeError) as e:
        X.cross_trade("LNG", S, C, L, decor_underside_m=3.00, band_top_m=3.15)
    assert str(e.value).startswith("BAND_IN_WALL_LINE") and "3.15 m2" in str(e.value)


def test_void_or_dome_finished_refused():
    S, C, L = villa()
    _refuse("HORIZONTAL_IN_WALL_LINE", C + [{"surface_id": "LNG|well", "layer": X.PAINT, "line_id": "L-pa-lng"}], S, L)
    _refuse("VOID_FINISHED", C + [{"surface_id": "LNG|well", "layer": X.BOARD, "line_id": "L-ceil-lng"}], S, L)


def test_stair_soffit_in_ceiling_or_wall_line_refused():
    S, C, L = villa()
    S["STA|soffit"] = dict(S["STA|soffit"], status=DC)
    _refuse("STAIR_SOFFIT_IN_CEILING", C + [{"surface_id": "STA|soffit", "layer": X.BOARD, "line_id": "L-ceil-lng"}],
            S, L)
    _refuse("STAIR_SOFFIT_IN_WALL", C + [{"surface_id": "STA|soffit", "layer": X.PAINT, "line_id": "L-pa-lng"}], S, L)


def test_held_surface_booked_or_carried_as_zero_refused():
    S, C, L = villa()
    _refuse("HELD_AS_ZERO", C + [{"surface_id": "STA|soffit", "layer": X.PAINT, "line_id": "L-pa-str-soffit"}], S, L)
    S["STA|soffit"] = dict(S["STA|soffit"], carried=0.0)
    with pytest.raises(X.CrossTradeError) as e:
        X.check_surface(S["STA|soffit"])
    assert str(e.value).startswith("HELD_AS_ZERO")
    S["STA|soffit"] = {k: v for k, v in S["STA|soffit"].items() if k not in ("carried", "held_item")}
    with pytest.raises(X.CrossTradeError) as e:
        X.check_surface(S["STA|soffit"])
    assert str(e.value).startswith("HELD_UNNAMED")


def test_millimetres_refused():
    S, C, L = villa()
    S["LNG|decor"] = dict(S["LNG|decor"], m2=23000000.0)
    _refuse("BAD_UNITS", C, S, L)
    S, C, L = villa()
    S["LNG|walls"] = dict(S["LNG|walls"], top_m=3000.0)
    _refuse("BAD_UNITS", C, S, L)


def test_decor_above_soffit_refused():
    S, C, L = villa()
    with pytest.raises(X.CrossTradeError) as e:
        X.wall_band(S["LNG|walls"], 3.20, 3.15)
    assert str(e.value).startswith("DECOR_ABOVE_SOFFIT")


def test_unknown_line_and_layer_refused():
    S, C, L = villa()
    _refuse("UNKNOWN_LINE", C + [{"surface_id": "LNG|decor", "layer": X.BOARD, "line_id": "L-nowhere"}], S, L)
    _refuse("UNKNOWN_LAYER", C + [{"surface_id": "LNG|decor", "layer": "VARNISH", "line_id": "L-ceil-lng"}], S, L)
    assert math.isclose(sum(s["m2"] for s in S.values() if s["kind"] == X.DECOR), 28.0)


def test_line_roles_stairwell_and_exterior():
    S, C, L = villa()
    S["STA|soffit"] = dict(S["STA|soffit"], status=DC)
    L["L-stairwell"] = {"line_id": "L-stairwell", "item_code": "FIN.CEILING", "role": "STAIRWELL"}
    L["L-ext"] = {"line_id": "L-ext", "item_code": "FIN.CEILING", "role": "EXTERIOR"}
    # the stair-well ceiling / soffit line (its scope names the soffit) may hold the stair underside
    assert X.validate(C + [{"surface_id": "STA|soffit", "layer": X.PLASTER, "line_id": "L-stairwell"}], S, L)
    # an exterior soffit over outside air holds no interior face
    _refuse("INTERIOR_IN_EXTERIOR_LINE", C + [{"surface_id": "BTH|decor", "layer": X.PAINT, "line_id": "L-ext"}], S, L)
    assert X.ceiling_role("GF-R1:ceiling") == "CEILING"
    assert X.ceiling_role("1F-R2:ceiling over void") == "CEILING"
    assert X.ceiling_role("GF-R3:stairwell ceiling") == "STAIRWELL"
    assert X.ceiling_role("SOFFIT:GF:PL-01") == "EXTERIOR"
    with pytest.raises(X.CrossTradeError) as e:
        X.ceiling_role("GF-R4:bulkhead")
    assert str(e.value).startswith("UNKNOWN_CEILING_LINE")
