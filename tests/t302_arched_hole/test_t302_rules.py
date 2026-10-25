"""R-T302-1 on a hand villa (V-302, not Alsenan): a semicircular head on a 3.00 m chord in a curved wall.

HAND CALCULATION (metres). Reference (drawn) face radius R = 4.00, jambs at u = +-1.50, hole from the floor (sill 0),
head = springing s = 1.00 + semicircle a = 1.50: H(u) = 1.00 + sqrt(1.50^2 - u^2).
- Plan jamb half angle alpha = asin(1.50 / 4.00) = 0.3843967745 rad; developed width = 2 R alpha = 3.0751741958 m.
- Developed area = integral H(4 sin phi) 4 dphi = integral H(u) du / sqrt(1 - u^2 / R^2).
  Rectangle part: s x developed width = 3.0751741958 m2.
  Arch part: integral sqrt(a^2 - u^2) (1 - u^2/R^2)^(-1/2) du, binomial series, k = a^2 / R^2 = 0.140625:
    (pi a^2 / 2) (1 + k/8 + 3 k^2/64 + 25 k^3/1024 + 0.0149536 k^4 + ...)
    = 3.5342917353 x (1 + 0.0175781250 + 0.0009269714 + 0.0000678946 + 0.0000058480) = 3.5342917353 x 1.0185788390
    = 3.5999551 m2 (next term below 6e-7 relative).
  Developed hole = 3.0751742 + 3.5999551 = 6.6751293 m2.
- Projected (elevation) area = 3.00 x 1.00 + pi 1.50^2 / 2 = 6.5342917 m2 (NOT the hole on a curved face).
- Room face 0.20 outside, R' = 4.20, RADIAL soffit: the same h(phi) on a 1.05 times longer arc: 7.0088858 m2.
The polyline head uses 4000 chords (chord error on the semicircle area below 1e-6 relative).
"""
import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "research" / "agents_t302"
sys.path.insert(0, str(HERE))
import t302_arched_hole as R  # noqa: E402

A, S, RR = 1.50, 1.00, 4.00
ALPHA = math.degrees(math.asin(A / RR))
A1, A2 = 180 - ALPHA, 180 + ALPHA          # u = R sin(phi): +1.5 at a1, -1.5 at a2
HAND_DEV, HAND_PROJ, HAND_ROOM = 6.6751293, 6.5342917, 7.0088858
HAND_WIDTH = 3.0751741958


def semicircle(n=4000, ext=0.0, scale=1.0):
    pts = [(-A - ext, S)] if ext else []
    for i in range(n + 1):
        t = math.pi * i / n
        pts.append((-A * math.cos(t), S + A * math.sin(t)))
    if ext:
        pts.append((A + ext, S))
    return R.HeadProfile([(u * scale, h * scale) for u, h in pts])


ELEV = R.Elevation(origin=(0.0, 0.0), e=(0.0, 1.0))


def test_hand_developed_hole_on_the_drawn_face():
    v = R.developed_hole(semicircle(), ELEV, (0, 0), RR, A1, A2, 0.0, "RADIAL", RR)
    assert v == pytest.approx(HAND_DEV, abs=2e-5)
    assert R.developed_hole(semicircle(), ELEV, (0, 0), RR, A1, A2, 0.0, "PRISMATIC") == pytest.approx(v, abs=1e-9)


def test_hand_projected_area_is_less_and_is_refused_as_the_hole():
    p = semicircle().projected_area(-A, A)
    assert p == pytest.approx(HAND_PROJ, abs=2e-5)
    assert p < HAND_DEV
    with pytest.raises(R.Refused) as x:
        R.check_deduction(p, "PROJECTED", HAND_WIDTH, S + A)
    assert x.value.code == "PROJECTED_AS_DEVELOPED"


def test_hand_room_face_radial_scales_with_radius():
    v = R.developed_hole(semicircle(), ELEV, (0, 0), 4.20, A1, A2, 0.0, "RADIAL", RR)
    assert v == pytest.approx(HAND_ROOM, abs=2e-5)


def test_face_record_reference_confirmed_other_face_bounded():
    prof = semicircle(ext=0.40)             # the drawn head carries on past the jambs (as a bay end does)
    ok, res = R.register(ELEV, (0, 0), RR, A1, A2, (-A, A), tol=1e-6)
    assert ok and max(abs(r) for r in res) < 1e-9
    ref = R.face_record("ref", prof, ELEV, (0, 0), RR, A1, A2, RR, 0.0, registered=ok)
    assert ref["status"] == R.STATUS_CONFIRMED and ref["lo"] == pytest.approx(HAND_DEV, abs=2e-5)
    room = R.face_record("room", prof, ELEV, (0, 0), 4.20, A1, A2, RR, 0.0, registered=ok)
    assert room["status"] == R.STATUS_BOUNDED
    assert room["prismatic"] < room["radial"] == pytest.approx(HAND_ROOM, abs=2e-5)
    assert room["hi"] <= 4.20 * math.radians(A2 - A1) * (S + A)


def test_prismatic_outside_the_drawn_head_is_held_not_extrapolated():
    room = R.face_record("room", semicircle(), ELEV, (0, 0), 4.20, A1, A2, RR, 0.0)
    assert room["status"] == R.STATUS_HELD and room["lo"] is None and room["hi"] is None
    assert room["radial"] == pytest.approx(HAND_ROOM, abs=2e-5)
    with pytest.raises(R.Refused) as x:
        R.developed_hole(semicircle(), ELEV, (0, 0), 4.20, A1, A2, 0.0, "PRISMATIC")
    assert x.value.code == "OUTSIDE_HEAD"


def test_window_area_offered_as_the_hole_is_refused():
    with pytest.raises(R.Refused) as x:
        R.check_deduction(3.0 * 2.5, "WINDOW_LINE", HAND_WIDTH, S + A)
    assert x.value.code == "WINDOW_AREA_AS_HOLE"


def test_hole_larger_than_the_rectangle_over_the_jambs_is_refused():
    with pytest.raises(R.Refused) as x:
        R.check_deduction(HAND_WIDTH * (S + A) + 0.01, "DEVELOPED", HAND_WIDTH, S + A)
    assert x.value.code == "HOLE_EXCEEDS_RECTANGLE"
    assert R.check_deduction(HAND_DEV, "DEVELOPED", HAND_WIDTH, S + A) == HAND_DEV


def test_missing_radius_is_held_never_zero():
    rec = R.face_record("room", semicircle(), ELEV, (0, 0), None, A1, A2, RR, 0.0)
    assert rec["status"] == R.STATUS_HELD and rec["lo"] is None and rec["radial"] is None
    with pytest.raises(R.Refused) as x:
        R.developed_hole(semicircle(), ELEV, (0, 0), None, A1, A2)
    assert x.value.code == "MISSING_RADIUS"
    with pytest.raises(R.Refused):
        R.check_deduction(None, "DEVELOPED", HAND_WIDTH, S + A)
    with pytest.raises(R.Refused):
        R.piece_net(10.0, None, None)


def test_unregistered_elevation_holds_the_face():
    ok, res = R.register(ELEV, (0, 0), RR, A1, A2, (-A - 0.02, A), tol=0.001)
    assert not ok
    rec = R.face_record("ref", semicircle(), ELEV, (0, 0), RR, A1, A2, RR, 0.0, registered=ok)
    assert rec["status"] == R.STATUS_HELD and "A5" in rec["held_item"]


def test_mirror_rotation_and_units_leave_the_hole_unchanged():
    base = R.developed_hole(semicircle(), ELEV, (0, 0), RR, A1, A2, 0.0, "RADIAL", RR)
    # mirror y -> -y: angles 360 - phi, the elevation's +u axis mirrored
    mir = R.developed_hole(semicircle(), R.Elevation((0, 0), (0, -1)), (0, 0), RR, 360 - A2, 360 - A1, 0.0,
                           "RADIAL", RR)
    assert mir == pytest.approx(base, abs=1e-9)
    # rotate the whole plan by 30 deg about a remote point; centre and axis rotate with it
    th = math.radians(30)
    c = (12.0 * math.cos(th) - 5.0 * math.sin(th), 12.0 * math.sin(th) + 5.0 * math.cos(th))
    rot = R.developed_hole(semicircle(), R.Elevation(c, (-math.sin(th), math.cos(th))), c, RR, A1 + 30, A2 + 30,
                           0.0, "RADIAL", RR)
    assert rot == pytest.approx(base, abs=1e-9)
    # millimetres: everything x 1000, area x 1e6
    mm = R.developed_hole(semicircle(scale=1000.0), ELEV, (0, 0), RR * 1000, A1, A2, 0.0, "RADIAL", RR * 1000)
    assert mm / 1e6 == pytest.approx(base, abs=1e-6)


def test_sill_and_profile_guards():
    with pytest.raises(R.Refused) as x:
        R.HeadProfile([(0, 1), (0, 2)])
    assert x.value.code == "BAD_PROFILE"
    with pytest.raises(R.Refused) as x:
        R.developed_hole(semicircle(), ELEV, (0, 0), RR, A1, A2, sill=1.2, model="RADIAL", r_ref=RR)
    assert x.value.code == "HEAD_BELOW_SILL"
    with pytest.raises(R.Refused) as x:
        R.developed_hole(semicircle(), ELEV, (0, 0), RR, A2, A1, 0.0, "RADIAL", RR)
    assert x.value.code == "BAD_RANGE"


def test_piece_net_takes_the_larger_hole_for_its_low_end():
    assert R.piece_net(11.0, 8.7, 9.0) == pytest.approx((2.0, 2.3))
    with pytest.raises(R.Refused) as x:
        R.piece_net(8.0, 8.7, 9.0)
    assert x.value.code == "HOLE_EXCEEDS_FACE"
