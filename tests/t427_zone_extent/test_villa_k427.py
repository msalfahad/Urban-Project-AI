"""K427: a hand-made villa (not Alsenan) for ZONE_EXTENT_V1 / R-T427-1.

Living room 12.00 x 7.00 (m). Along its south wall a planter band is DRAWN from x 5.00 to x 11.00, 1.20 deep, with a
0.20 curb on its north side (two drawn lines y 1.20 / 1.40) and both ends drawn (x 5.00, x 11.00). The engine prolonged
the band edge west to the room's west wall (x 0.00) and cut off:
  W  = 0.00 .. 5.00 x 0.00 .. 1.20 = 6.000 m2 (engine ZONE)       -> floor (no drawn line to the room)
  WS = 0.00 .. 5.00 x 1.20 .. 1.40 = 1.000 m2 (engine STRIP)      -> floor
  B  = 5.00 .. 11.00 x 0.00 .. 1.20 = 7.200 m2 (engine ZONE)      -> stays HELD (drawn on every side)
  C  = 5.00 .. 11.00 x 1.20 .. 1.40 = 1.200 m2 (engine STRIP)     -> stays HELD with the band (curb)
  room floor (seed) = 0.00 .. 12.00 x 1.40 .. 7.00 = 67.200 m2 plus the east piece 11.00 .. 12.00 x 0 .. 1.40 = 1.400
  (east of the band, open to the room across x 11.00 above y 1.40? no: drawn end x 11.00 runs 0 .. 1.40, so the east
  piece joins the room only across its undrawn north edge y 1.40, 1.00 m long).
By hand: moved to floor 6.000 + 1.000 + 1.400 = 8.400 m2; held 7.200 + 1.200 = 8.400 m2; closure 0.
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t427"))
import zone_extent_v1 as Z  # noqa: E402


def R(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def villa(scale=1.0, xf=None):
    xf = xf or (lambda p: p)
    P = lambda pts: [xf((x * scale, y * scale)) for x, y in pts]  # noqa: E731
    pieces = [
        {"id": "room", "engine_class": "ROOM_FLOOR", "poly": P(R(0, 1.4, 12, 7))},
        {"id": "W", "engine_class": "ZONE", "zone": "planter", "poly": P(R(0, 0, 5, 1.2))},
        {"id": "WS", "engine_class": "STRIP", "zone": "planter", "poly": P(R(0, 1.2, 5, 1.4))},
        {"id": "B", "engine_class": "ZONE", "zone": "planter", "poly": P(R(5, 0, 11, 1.2))},
        {"id": "C", "engine_class": "STRIP", "zone": "planter", "poly": P(R(5, 1.2, 11, 1.4))},
        {"id": "E", "engine_class": "ZONE", "zone": "planter", "poly": P(R(11, 0, 12, 1.4))},
    ]
    drawn = [((0, 0), (12, 0)), ((0, 0), (0, 7)), ((12, 0), (12, 7)), ((0, 7), (12, 7)),   # walls
             ((5, 0), (5, 1.4)), ((11, 0), (11, 1.4)),                                     # band ends
             ((5, 1.2), (11, 1.2)), ((5, 1.4), (11, 1.4))]                                 # curb lines
    drawn = [(xf((a[0] * scale, a[1] * scale)), xf((b[0] * scale, b[1] * scale))) for a, b in drawn]
    return pieces, drawn


def rows(res):
    return {r["id"]: r for r in res["rows"]}


def check_normal(res):
    a = rows(res)
    assert a["W"]["physical_class"] == "ROOM_FLOOR" and a["W"]["changed"] and a["W"]["status"] == Z.STATUS_DC
    assert a["WS"]["physical_class"] == "ROOM_FLOOR" and a["WS"]["joined_via"] == "room"
    assert a["W"]["joined_via"] == "WS"                                   # propagation through the strip
    assert a["E"]["physical_class"] == "ROOM_FLOOR"                       # east piece open across y 1.40 (1.00 m)
    assert a["B"]["physical_class"] == "ZONE" and a["B"]["status"] == Z.STATUS_HELD
    assert a["C"]["physical_class"] == "STRIP" and a["C"]["status"] == Z.STATUS_HELD
    assert res["moved_to_floor_m2"] == pytest.approx(6.0 + 1.0 + 1.4)
    assert res["held_m2"] == pytest.approx(7.2 + 1.2)
    assert res["closure_m2"] == pytest.approx(0.0, abs=1e-9)
    assert a["B"]["area_m2"] == pytest.approx(7.2)                        # HELD keeps its area, never 0


def test_normal_metres():
    check_normal(Z.classify(*villa()))


def test_normal_millimetres():
    p, d = villa(scale=1000.0)
    check_normal(Z.classify(p, d, unit="mm"))


@pytest.mark.parametrize("deg", [0, 37, 90, 211])
@pytest.mark.parametrize("mirror", [False, True])
def test_rotation_mirror_shift(deg, mirror):
    t = math.radians(deg)

    def xf(p):
        x, y = p
        if mirror:
            x = -x
        return (x * math.cos(t) - y * math.sin(t) + 250.0, x * math.sin(t) + y * math.cos(t) - 80.0)
    check_normal(Z.classify(*villa(xf=xf)))


def test_adverse_band_fully_drawn_moves_nothing():
    # the designer draws the curb along the whole length (x 0 .. 12) and the east end: every piece is separated
    p, d = villa()
    d = d + [((0, 1.2), (5, 1.2)), ((0, 1.4), (5, 1.4)), ((11, 1.4), (12, 1.4))]
    res = Z.classify(p, d)
    a = rows(res)
    assert res["moved_to_floor_m2"] == pytest.approx(0.0)
    assert {a[k]["physical_class"] for k in ("W", "B", "E")} == {"ZONE"}
    assert res["held_m2"] == pytest.approx(6.0 + 1.0 + 7.2 + 1.2 + 1.4)


def test_adverse_drafting_gap_below_min_open_is_not_open():
    # the curb line stops 0.10 m short of the wall: a drafting gap, not an open edge
    p, d = villa()
    d = d + [((0.1, 1.2), (5, 1.2)), ((0.1, 1.4), (5, 1.4)), ((11, 1.4), (12, 1.4))]
    res = Z.classify(p, d)
    assert rows(res)["WS"]["physical_class"] == "STRIP" and res["moved_to_floor_m2"] == pytest.approx(0.0)


def test_adverse_solid_never_joins():
    p, d = villa()
    p[3] = {"id": "B", "engine_class": "SOLID", "poly": R(5, 0, 11, 1.2)}
    d = [s for s in d if s != ((5, 1.2), (11, 1.2))]                     # even with an open edge to the curb
    a = rows(Z.classify(p, d))
    assert a["B"]["physical_class"] == "SOLID" and a["B"]["status"] == "NOT_FLOOR"


def test_adverse_engine_zone_line_is_not_a_drawn_line():
    # passing the engine's own prolonged band edge as 'drawn' would hide the defect: the rule input is drawn lines only,
    # so the same pieces with the prolonged line give the wrong (old) answer -> the test pins the difference
    p, d = villa()
    wrong = Z.classify(p, d + [((0, 1.2), (5, 1.2)), ((0, 1.4), (5, 1.4))])
    right = Z.classify(p, d)
    assert rows(wrong)["W"]["physical_class"] == "ZONE" and rows(right)["W"]["physical_class"] == "ROOM_FLOOR"


def test_refusals():
    p, d = villa()
    with pytest.raises(Z.Refused):                                        # no seed
        Z.classify([x for x in p if x["engine_class"] != "ROOM_FLOOR"], d)
    with pytest.raises(Z.Refused):                                        # overlap: one m2, one piece
        Z.classify(p + [{"id": "dup", "engine_class": "ZONE", "poly": R(1, 0.2, 2, 1.0)}], d)
    with pytest.raises(Z.Refused):                                        # unknown unit
        Z.classify(p, d, unit="ft")
    with pytest.raises(Z.Refused):                                        # unknown class
        Z.classify(p + [{"id": "x", "engine_class": "GARDEN", "poly": R(20, 0, 21, 1)}], d)
    with pytest.raises(Z.Refused):                                        # missing polygon
        Z.classify(p + [{"id": "x", "engine_class": "ZONE", "poly": None}], d)
    with pytest.raises(Z.Refused):                                        # same id twice
        Z.classify(p + [dict(p[1])], d)


def test_close_residual():
    r = Z.close_residual(100.0, [("floor", 90.0, "TRACED"), ("band", 7.2, "HELD"), ("columns", 0.8, "NOT_FLOOR")])
    assert r["unexplained_m2"] == pytest.approx(2.0)                      # named, never forced to 0
    with pytest.raises(Z.Refused):
        Z.close_residual(100.0, [("band", None, "HELD")])                 # a HELD part with no figure
    with pytest.raises(Z.Refused):
        Z.close_residual(100.0, [("band", 7.2, "MAYBE")])
