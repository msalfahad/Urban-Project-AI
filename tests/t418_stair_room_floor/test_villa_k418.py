"""T-418: STAIR_ROOM_FLOOR_V1 on a hand-calculated NON-Alsenan fixture (villa K418) with adverse cases.

Villa K418 stair room, 3.00 x 6.00 = 18.000 m2 (no notch), storey FFL 0.00:
  hall at the foot (floor, FFL 0.00, level mark inside): 3.00 x 1.00 + 1.30 x 0.60 = 3.780 m2
  west flight below the cut (B7): 1.30 x 3.00 = 3.900 m2      landing between flights (B7): 3.00 x 1.40 = 4.200 m2
  central wall (SOLID): 0.40 x 3.60 = 1.440 m2                east lane under the upper flight, unread (UNREAD): 1.30 x 3.60 = 4.680 m2
  re-add 3.780 + 3.900 + 4.200 + 1.440 + 4.680 = 18.000; floor 3.780; HELD 0 .. 4.680 (never 0)."""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t418"))
import stair_room_floor_v1 as SR  # noqa: E402


def R(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


HALL = [(0, 0), (3.0, 0), (3.0, 1.0), (1.3, 1.0), (1.3, 1.6), (0, 1.6)]


def room(hall_level=0.0, tf=lambda p: p):
    T = lambda pts: [tf(p) for p in pts]  # noqa: E731
    return {"id": "K-ST", "storey_ffl": 0.0, "face": T(R(0, 0, 3.0, 6.0)), "parts": [
        {"id": "K-HALL", "kind": "FLOOR", "poly": T(HALL), "level": hall_level, "level_src": "mark 0.00 inside",
         "finish": "PORCELAIN", "finish_rule": "dry default", "finish_status": SR.STATUS_OWNER},
        {"id": "K-FL", "kind": "B7", "poly": T(R(0, 1.6, 1.3, 4.6))},
        {"id": "K-LD", "kind": "B7", "poly": T(R(0, 4.6, 3.0, 6.0))},
        {"id": "K-WALL", "kind": "SOLID", "poly": T(R(1.3, 1.0, 1.7, 4.6))},
        {"id": "K-UNDER", "kind": "UNREAD", "poly": T(R(1.7, 1.0, 3.0, 4.6))}]}


def test_normal_hand_values():
    res = SR.partition(room())
    a = {r["part"]: r for r in res["rows"]}
    assert res["face_m2"] == pytest.approx(18.0)
    assert res["closure_m2"] == pytest.approx(0.0, abs=1e-9)
    assert res["floor_m2"] == pytest.approx(3.78)
    assert a["K-HALL"]["family"] == "B3-01" and a["K-HALL"]["status"] == SR.STATUS_DC
    assert a["K-FL"]["family"] == "B7" and a["K-LD"]["family"] == "B7"
    assert res["held_bound"] == pytest.approx([0.0, 4.68])
    assert a["K-UNDER"]["status"] == "HELD" and a["K-UNDER"]["bound"][1] == pytest.approx(4.68)


@pytest.mark.parametrize("units,k", [("m", 1.0), ("mm", 1000.0)])
@pytest.mark.parametrize("deg", [0.0, 37.0, 90.0])
@pytest.mark.parametrize("mirror", [False, True])
def test_units_rotation_mirror(units, k, deg, mirror):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))

    def tf(p):
        x, y = (-p[0] if mirror else p[0]), p[1]
        return ((x * c - y * s) * k + 50 * k, (x * s + y * c) * k - 20 * k)
    res = SR.partition(room(tf=tf), units=units)
    assert res["face_m2"] == pytest.approx(18.0, abs=1e-6)
    assert res["floor_m2"] == pytest.approx(3.78, abs=1e-6)
    assert res["held_bound"][1] == pytest.approx(4.68, abs=1e-6)


def test_adverse_tread_counted_as_floor_refused():
    with pytest.raises(SR.Refused, match="stair element counted as floor"):
        SR.partition(room(), others=[{"id": "K-FLIGHT-LINE", "class": "B7", "poly": R(0, 1.3, 1.3, 1.9)}])


def test_adverse_porch_counted_inside_refused():
    with pytest.raises(SR.Refused, match="exterior space counted inside"):
        SR.partition(room(), others=[{"id": "K-PORCH", "class": "EXTERIOR", "poly": R(0, -1.0, 3.0, 0.2)}])


def test_adverse_floor_counted_twice_refused():
    with pytest.raises(SR.Refused, match="floor counted twice"):
        SR.partition(room(), others=[{"id": "K-ENTRY", "class": "FLOOR", "poly": R(2.0, -2.0, 3.0, 0.5)}])


def test_adverse_unlevelled_floor_is_held_never_zero():
    res = SR.partition(room(hall_level=None))
    hall = [r for r in res["rows"] if r["part"] == "K-HALL"][0]
    assert hall["kind"] == "UNREAD" and hall["status"] == "HELD" and hall["bound"] == pytest.approx([0.0, 3.78])
    assert res["floor_m2"] == 0.0 and res["held_bound"][1] == pytest.approx(3.78 + 4.68)


def test_adverse_parts_must_close_and_not_overlap():
    r = room()
    r["parts"] = [p for p in r["parts"] if p["id"] != "K-UNDER"]          # 4.680 m2 dropped silently
    with pytest.raises(SR.Refused, match="do not re-add"):
        SR.partition(r)
    r = room()
    r["parts"][1]["poly"] = R(0, 1.5, 1.3, 4.6)                           # flight over the hall by 0.13 m2
    with pytest.raises(SR.Refused, match="overlaps"):
        SR.partition(r)


def test_adverse_floor_without_finish_status_refused():
    r = room()
    r["parts"][0]["finish_status"] = None
    with pytest.raises(SR.Refused, match="finish"):
        SR.partition(r)


def test_census_silent_omission_and_wrong_binding():
    res = SR.partition(room())
    c = SR.census([res], {})
    assert c == [{"room": "K-ST", "part": "K-HALL", "m2": pytest.approx(3.78), "line": None,
                  "state": "SILENT_OMISSION"}]
    assert SR.census([res], {"K-HALL": "L-1"})[0]["state"] == "BOUND"
    with pytest.raises(SR.Refused, match="B7 part"):
        SR.census([res], {"K-FL": "L-2"})
    assert res["findings"][0]["finding"] == "SILENT_OMISSION"
