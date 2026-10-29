"""T-324 rules on a NON-Alsenan hand fixture (villa P): an L-shaped roof parapet, outer legs 6.00 + 4.00 m (10.00 m),
1.10 m above the finished roof, 0.20 m thick, one convex corner, the 6.00 leg's far end FREE, the 4.00 leg's end
against a higher wall.

Hand calculation (m, m2):
  outer run 6.00 + 4.00 = 10.000; inner run (mitred corner) 5.80 + 3.80 = 9.600; centreline 5.90 + 3.90 = 9.800
  outer face 10.000 x 1.10 = 11.000 (facade line, not a parapet item); inner face 9.600 x 1.10 = 10.560
  upturn 0.20 above the membrane; build-up above the membrane c unprinted -> exposed upturn e = 0 .. 0.20:
    upturn zone 0 .. 9.600 x 0.20 = 0 .. 1.920; face above the upturn 10.560 - 1.920 = 8.640 .. 10.560
    printed c = 0.05 -> e = 0.15: zone 1.440, above 9.120; c = 0.25 -> e = 0: zone 0, above 10.560
  top 9.800 x 0.20 = 1.960; top arrises 10.000 + 9.600 = 19.600 m.l (2.0 per metre of centreline, never 3)
  free end: stop-end 2 x 1.10 + 0.20 = 2.400 m.l, end face 0.20 x 1.10 = 0.220; abutting end: 0
  half-rate payment: 19.600 x 0.5 = 9.800 m.l payable, physical stays 19.600 m.l; never 9.800 m2
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t324"))
from parapet_components import (Book, RefusedError, Row, inner_face_split, ml_to_m2,  # noqa: E402
                                parapet_from_outer, payable_ml, stop_end, top_surface)

OUTER = [(0.0, 0.0), (6.0, 0.0), (6.0, 4.0)]
T, H = 0.20, 1.10


def _rot(pts, deg):
    a = math.radians(deg)
    return [(x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)) for x, y in pts]


def test_runs_hand_values():
    o, i, c = parapet_from_outer(OUTER, T, "left")
    assert (round(o, 6), round(i, 6), round(c, 6)) == (10.0, 9.6, 9.8)


@pytest.mark.parametrize("deg", [0, 30, -121, 47])
def test_rotation_mirror_mm_do_not_move(deg):
    o, i, c = parapet_from_outer(_rot(OUTER, deg), T, "left")
    assert (round(o, 6), round(i, 6), round(c, 6)) == (10.0, 9.6, 9.8)
    mir = [(-x, y) for x, y in _rot(OUTER, deg)]
    o2, i2, c2 = parapet_from_outer(mir, T, "right")
    assert (round(o2, 6), round(i2, 6), round(c2, 6)) == (10.0, 9.6, 9.8)
    mm = [(x * 1000, y * 1000) for x, y in _rot(OUTER, deg)]
    o3, i3, c3 = parapet_from_outer(mm, T, "left", scale=0.001)
    assert (round(o3, 6), round(i3, 6), round(c3, 6)) == (10.0, 9.6, 9.8)


def test_inner_face_split_unprinted_build_up_is_a_held_range():
    s = inner_face_split(9.6, H)
    assert round(s["total"], 6) == 10.56
    assert (round(s["zone_lo"], 6), round(s["zone_hi"], 6)) == (0.0, 1.92)
    assert (round(s["above_lo"], 6), round(s["above_hi"], 6)) == (8.64, 10.56)
    assert s["split_status"] == "HELD"
    # the split never changes the face total (no deduction, no double)
    assert round(s["above_lo"] + s["zone_hi"], 6) == round(s["total"], 6)


@pytest.mark.parametrize("c,zone,above", [(0.05, 1.44, 9.12), (0.25, 0.0, 10.56), (0.20, 0.0, 10.56)])
def test_inner_face_split_printed_build_up(c, zone, above):
    s = inner_face_split(9.6, H, cover_above_membrane_m=c)
    assert round(s["zone_lo"], 6) == round(s["zone_hi"], 6) == zone
    assert round(s["above_lo"], 6) == above
    assert s["split_status"] == "DRAWING-CONFIRMED"


def test_low_parapet_zone_capped_by_its_height():
    s = inner_face_split(2.0, 0.15)
    assert round(s["zone_hi"], 6) == 0.30 and round(s["above_lo"], 6) == 0.0


def test_top_from_drawn_thickness_and_projection_excess():
    top, ex = top_surface(9.8, T)
    assert round(top, 6) == 1.96 and ex is None
    top, ex = top_surface(9.8, T, plan_area_m2=2.95)
    assert round(ex, 6) == 0.99            # belongs to the projecting element, not the parapet top


def test_top_from_default_width_refused():
    with pytest.raises(RefusedError):
        top_surface(9.8, None)
    with pytest.raises(RefusedError):
        top_surface(9.8, T, plan_area_m2=1.0)  # outline narrower than the drawn wall: re-read, never accept


def test_stop_ends():
    assert stop_end(H, T, True) == {"ml": (2.4, 2.4), "m2": (0.22, 0.22), "status": "DRAWING-CONFIRMED"}
    assert stop_end(H, T, False)["ml"] == (0.0, 0.0)
    held = stop_end(H, T, None)
    assert held["status"] == "HELD" and held["ml"] == (0.0, 2.4)


def test_corner_ml_never_m2_and_payable_kept_apart():
    with pytest.raises(RefusedError):
        ml_to_m2(19.6)
    assert round(payable_ml(19.6, 0.5), 6) == 9.8      # payable m.l; the physical length is unchanged


def _book():
    b = Book()
    b.add(Row("P/1/OUTER_FACE", "OUTER_FACE", "m2", 11.0, 11.0, "DRAWING-CONFIRMED", "IN_LINE", "FIN.EXT.FINISH",
              "L-x", edge="P/1/outer_face"))
    b.add(Row("P/1/TOP", "TOP_SURFACE", "m2", 1.96, 1.96, "DRAWING-CONFIRMED", "NO_LINE", "FIN.EXT.FINISH", "NO LINE",
              edge="P/1/top"))
    b.add(Row("P/1/OUTER_TOP_ARRIS", "OUTER_TOP_ARRIS", "m.l", 10.0, 10.0, "DRAWING-CONFIRMED", "NO_LINE", "CORNERS",
              "NO LINE", edge="P/1/outer_top_edge"))
    b.add(Row("P/1/INNER_TOP_ARRIS", "INNER_TOP_ARRIS", "m.l", 9.6, 9.6, "DRAWING-CONFIRMED", "NO_LINE", "CORNERS",
              "NO LINE", edge="P/1/inner_top_edge"))
    b.add(Row("P/1/UPTURN", "UPTURN_ML", "m.l", 9.6, 9.6, "DRAWING-CONFIRMED", "IN_LINE", "WATERPROOFING", "L-wp",
              edge="P/1/inner_base"))
    return b


def test_book_normal():
    b = _book()
    lo, hi = b.total("OUTER_TOP_ARRIS", "m.l")
    lo2, _ = b.total("INNER_TOP_ARRIS", "m.l")
    assert round(lo + lo2, 6) == 19.6


def test_outer_face_in_exterior_and_parapet_refused():
    b = _book()
    with pytest.raises(RefusedError):
        b.add(Row("P/1/PARAPET_OUTER", "OUTER_FACE", "m2", 11.0, 11.0, "DRAWING-CONFIRMED", "NO_LINE",
                  "PLASTER_PARAPET", "NO LINE", edge="P/1/outer_face"))


def test_bead_as_second_length_refused():
    b = _book()
    with pytest.raises(RefusedError):
        b.add(Row("P/1/BEAD", "CORNER_BEAD", "m.l", 10.0, 10.0, "DRAWING-CONFIRMED", "NO_LINE", "CORNERS", "NO LINE",
                  edge="P/1/outer_top_edge"))


def test_base_junction_as_arris_refused():
    b = _book()
    with pytest.raises(RefusedError):
        b.add(Row("P/1/BASE_ARRIS", "INNER_BASE_ARRIS", "m.l", 9.6, 9.6, "DRAWING-CONFIRMED", "NO_LINE", "CORNERS",
                  "NO LINE", edge="P/1/inner_base"))


def test_unknown_coping_carries_no_number_and_held_never_zero():
    b = _book()
    b.add(Row("P/ALL/COPING", "COPING", "m.l", None, None, "UNKNOWN", "NO_LINE", "COPING", "NO LINE"))
    with pytest.raises(RefusedError):
        b.add(Row("P/ALL/DRIP", "DRIP", "m.l", 9.8, 9.8, "UNKNOWN", "NO_LINE", "FIN", "NO LINE"))
    with pytest.raises(RefusedError):
        b.add(Row("P/1/ZONE", "INNER_FACE_UPTURN_ZONE", "m2", 0.0, 0.0, "HELD", "NO_LINE", "WP", "NO LINE"))
    with pytest.raises(RefusedError):
        b.add(Row("P/1/TOP", "TOP_SURFACE", "m2", 1.96, 1.96, "DRAWING-CONFIRMED", "NO_LINE", "X", "NO LINE"))


def test_missing_values_refused():
    with pytest.raises(RefusedError):
        inner_face_split(None, H)
    with pytest.raises(RefusedError):
        inner_face_split(9.6, None)
    with pytest.raises(RefusedError):
        parapet_from_outer(OUTER, None, "left")
