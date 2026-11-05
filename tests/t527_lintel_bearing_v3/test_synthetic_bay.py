"""LINTEL_BEARING_V3 on a synthetic villa (not the development villa): a 0.20 m band, a 1.20 m window, a curved bay.

Hand calculation (metres, band along x, faces y = -0.10 / +0.10, window jambs x = 3.00 / 4.20):
  bay centre (7.00, -1.20), face arcs r_in 2.00 / r_out 2.20 (WALL layer), glazing arc r 2.10 (WINDOW layer, 60..120 deg,
  wholly above the band).
  drawn masonry end on the far face  y = -0.10: x = 7 - sqrt(2.00^2 - 1.10^2) = 7 - sqrt(2.79) = 5.329671 m
  on the near face y = +0.10:                     x = 7 - sqrt(2.00^2 - 1.30^2) = 7 - sqrt(2.31) = 5.480132 m
  full thickness ends at the first of the two:  a_END = 5.329671 - 4.20 = 1.129671 m  (V3)
  V2 chord point (bay centreline circle r 2.10 meets the band centreline y = 0): 7 - sqrt(2.10^2 - 1.20^2)
  = 7 - sqrt(2.97) = 5.276631 m -> a_END = 1.076631 m (V2): V3 - V2 = +0.053040 m.
  START: no bay on that side, the band runs to x = 0 -> a_START = 3.000 m under V2 and V3 alike (search 3.0 m capped).
Adverse: mirrored and rotated copies give the same reach; the bay arc meeting the far face exactly at the jamb gives
a = 0 (FLAGGED downstream, never the 0.40 minimum); no WALL arcs, a single face arc, two candidate centres, arcs in mm
against a band in metres, or a circle that only touches the band face: no drawn end -> None (HELD by name, never the
chord value, never 0); a negative or missing radius is refused.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest
from shapely.affinity import rotate, scale
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t527"))
import lintel_bearing_v3 as V3  # noqa: E402
import lintel_bearing_v2 as V2  # noqa: E402

HALF = 0.10
A_END = 7.0 - math.sqrt(2.79) - 4.20
A_END_V2 = 7.0 - math.sqrt(2.97) - 4.20


def rect(x0, x1, h):
    return Polygon([(x0, -h), (x1, -h), (x1, h), (x0, h)])


def arcs(c=(7.0, -1.2), r_in=2.0, r_out=2.2, unit=1.0, extra=()):
    d = math.radians
    return [{"c": (c[0] * unit, c[1] * unit), "r": r_in * unit, "role": "WALL", "a0": d(30), "a1": d(60)},
            {"c": (c[0] * unit, c[1] * unit), "r": r_out * unit, "role": "WALL", "a0": d(30), "a1": d(60)},
            {"c": (c[0] * unit, c[1] * unit), "r": 2.1 * unit, "role": "WINDOW", "a0": d(60), "a1": d(120)}] + list(extra)


def case(arc_list, chord=None):
    """V2 masonry of the band (T-516 construction: band rect minus its own gaps) and the V3 masonry."""
    x_chord = 7.0 - math.sqrt(2.97) if chord is None else chord
    band = rect(0.0, 12.0, HALF)
    window = rect(3.0, 4.2, HALF + 0.01)
    chord_rect = rect(x_chord, 14.0 - x_chord, HALF + 0.01)
    M2 = band.difference(unary_union([window, chord_rect]))
    grp, region = V3.match_bay(V3.arc_groups(arc_list), band, chord_rect)
    if grp is None:
        return M2, None, region
    M3 = V3.masonry_v3(M2, "B", band, chord_rect, region, [], [window])
    return M2, M3, [("BAY", region)], grp, window


def run(M, bays, jamb, sign, window, a=(0.0, 0.0), u=(1.0, 0.0)):
    return V3.reach_v3(M, a, u[0], u[1], jamb, sign, HALF, [], [("W", window)], bays)


def test_end_reads_the_drawn_inner_face_not_the_chord():
    M2, M3, bays, grp, window = case(arcs())
    assert grp["wall_r"] == [2.0, 2.2]
    e3, capped, stop, sid = run(M3, bays, 4.2, +1, window)
    assert not capped and abs(e3 - A_END) < 2e-5 and (stop, sid) == ("END_OF_MASONRY", "CURVED_BAY:BAY")
    e2, _c = V2.reach(M2, (0.0, 0.0), 1.0, 0.0, 4.2, +1, HALF)
    assert abs(e2 - A_END_V2) < 2e-5
    assert abs((e3 - e2) - 0.053040) < 3e-5


def test_far_side_without_bay_is_unchanged():
    M2, M3, bays, grp, window = case(arcs())
    e3, capped3, stop3, _ = run(M3, bays, 3.0, -1, window)
    e2, capped2 = V2.reach(M2, (0.0, 0.0), 1.0, 0.0, 3.0, -1, HALF)
    assert (e3, capped3) == (e2, capped2) and e3 == V2.SEARCH_M and stop3 == "SEARCH_LIMIT"


def test_face_crossings_are_the_hand_values():
    _M2, _M3, _b, grp, _w = case(arcs())
    fc = V3.face_crossings(grp, (0.0, 0.0), 1.0, 0.0, HALF)
    assert abs(fc["face_minus"][0] - (7 - math.sqrt(2.79))) < 1e-9
    assert abs(fc["face_plus"][0] - (7 - math.sqrt(2.31))) < 1e-9


@pytest.mark.parametrize("deg", [30.0, 117.0, -45.0])
def test_rotation_gives_the_same_reach(deg):
    M2, M3, bays, grp, window = case(arcs())
    R = lambda g: rotate(g, deg, origin=(0, 0), use_radians=False)
    t = math.radians(deg)
    e, _c, stop, _s = run(R(M3), [("BAY", R(bays[0][1]))], 4.2, +1, R(window), u=(math.cos(t), math.sin(t)))
    assert abs(e - A_END) < 2e-5 and stop == "END_OF_MASONRY"


def test_mirror_gives_the_same_reach_from_the_start_side():
    M2, M3, bays, grp, window = case(arcs())
    Mx = lambda g: scale(g, xfact=-1, yfact=1, origin=(0, 0))
    # mirrored: the band runs from 0 to -12; along u = (-1, 0) the window jamb 4.2 becomes the END side again
    e, _c, stop, _s = V3.reach_v3(Mx(M3), (0.0, 0.0), -1.0, 0.0, 4.2, +1, HALF, [], [("W", Mx(window))],
                                  [("BAY", Mx(bays[0][1]))])
    assert abs(e - A_END) < 2e-5 and stop == "END_OF_MASONRY"


def test_bay_meeting_the_far_face_at_the_jamb_gives_zero_never_the_minimum():
    # centre chosen so that the inner circle cuts y = -0.10 exactly at the jamb x = 4.20
    cx = 4.2 + math.sqrt(2.79)
    lst = arcs(c=(cx, -1.2))
    x_chord = cx - math.sqrt(2.97)
    _M2, M3, bays, grp, window = case(lst, chord=x_chord)
    e, _c, stop, sid = run(M3, bays, 4.2, +1, window)
    assert e < 1e-4 and stop == "END_OF_MASONRY" and sid == "CURVED_BAY:BAY"


@pytest.mark.parametrize("lst, why", [
    ([a for a in arcs() if a["role"] != "WALL"], "no WALL face arcs"),
    ([a for a in arcs() if a["r"] != 2.2], "one face arc only"),
    (arcs() + arcs(c=(7.3, -1.2)), "two candidate centres"),
    (arcs(unit=1000.0), "arcs in mm, band in metres"),
    (arcs(c=(7.0, 2.1)), "circle only touches the near face (disk above y = +0.10)"),
])
def test_no_drawn_end_is_held(lst, why):
    out = case(lst)
    assert out[1] is None, why
    assert "drawn bay centres" in out[2]


@pytest.mark.parametrize("r", [None, -2.0, float("nan"), True])
def test_bad_radius_refused(r):
    with pytest.raises(V3.BearingV3Error):
        V3.arc_groups([{"c": (0.0, 0.0), "r": r, "role": "WALL", "a0": 0.0, "a1": 1.0}])


def test_v2_module_untouched_and_v3_tolerances_are_v2s():
    assert V2.VERSION == "LINTEL_BEARING_V2" and V3.VERSION == "LINTEL_BEARING_V3"
    assert V3.V2 is V2 and V2.TOL_M == 0.0005 and V2.PROBE_M == 0.003
