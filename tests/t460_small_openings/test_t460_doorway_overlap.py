"""T-460 item 3: DOORWAY_OVERLAP_CHECK_V1 on a non-training hand fixture (villa K bathroom).

Hand calculation (mm drawing): bathroom floor face 2.000 x 2.500 = 5.000 m2 inside the room-side wall faces; door 0.800 m
in a 0.150 m wall below it: doorway piece 0.800 x 0.150 = 0.120 m2 in the wall thickness, OUTSIDE the floor face ->
overlap 0. Upturn (Q-35 C walls only): perimeter 9.000 lm - door 0.800 = 8.200 x 0.20 = 1.640 m2; doors included
9.000 x 0.20 = 1.800 m2 would double the 0.800 x 0.20 = 0.160 m2 doorway transition.
Adverse: the room face drawn to the wall's FAR face at the door (a notch into the wall thickness) -> overlap 0.120 m2
(the doorway piece counted twice); rotation, mirror and metre units read alike; missing inputs HELD, never 0.
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t460"))

import doorway_overlap_v1 as DO  # noqa: E402


def _xf(p, rot, mirror, scale):
    x, y = p
    if mirror:
        x = -x
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return ((x * c - y * s) * scale, (x * s + y * c) * scale)


def bath(rot=0.0, mirror=False, scale=1.0, notch=False):
    room = [(0, 0), (600, 0)] + ([(600, -150), (1400, -150)] if notch else []) + [(1400, 0), (2000, 0), (2000, 2500),
                                                                               (0, 2500)]
    room = [_xf(p, rot, mirror, scale) for p in room]
    ux, uy = _xf((1, 0), rot, mirror, 1.0)
    nx, ny = _xf((0, 1), rot, mirror, 1.0)
    # band frame of the wall: s along the wall, o across it; the wall occupies o -150 .. 0 under s 600 .. 1400
    op = {"u": (ux, uy), "n": (nx, ny), "s0": 600 * scale, "s1": 1400 * scale, "o0": -150 * scale, "o1": 0.0}
    return room, op, 0.001 / scale


@pytest.mark.parametrize("rot,mirror,scale", [(0.0, False, 1.0), (37.0, False, 1.0), (124.0, True, 0.001)])
def test_normal_doorway_piece_outside_the_floor(rot, mirror, scale):
    room, op, u = bath(rot, mirror, scale)
    r = DO.band_box_overlap(room, None, op, u)
    assert r["box_m2"] == pytest.approx(0.120, abs=1e-6)
    assert r["overlap_m2"] == pytest.approx(0.0, abs=1e-6) and r["state"] == "NO_OVERLAP"


@pytest.mark.parametrize("rot,mirror,scale", [(0.0, False, 1.0), (211.0, True, 0.001)])
def test_adverse_floor_face_into_the_wall_is_a_double_count(rot, mirror, scale):
    room, op, u = bath(rot, mirror, scale, notch=True)
    r = DO.band_box_overlap(room, None, op, u)
    assert r["overlap_m2"] == pytest.approx(0.120, abs=1e-6) and r["state"] == "OVERLAP"
    f = DO.face_overlap(room, None, DO.band_box(op), u)
    assert f["overlap_m2"] == pytest.approx(0.120, abs=1e-6)


def test_upturn_walls_only_and_doors_included_and_held():
    assert DO.upturn_check(9.0, 0.8, 0.20, 1.64) == {"walls_only_m2": 1.64, "with_doors_m2": 1.8, "state": "WALLS_ONLY"}
    assert DO.upturn_check(9.0, 0.8, 0.20, 1.80)["state"] == "DOORS_INCLUDED_DOUBLE_WITH_TRANSITION"
    assert DO.upturn_check(9.0, 0.8, 0.20, 1.48)["state"] == "NEITHER"
    assert DO.upturn_check(None, 0.8, 0.20, 1.64) == {"walls_only_m2": None, "with_doors_m2": None, "state": "HELD"}
    assert DO.upturn_check(9.0, 0.8, 0.20, None)["state"] == "HELD"
