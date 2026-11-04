"""T-501 stair skirting home: rules R-T501-1 .. 4 (research/agents_t501/t501_stair_skirting_home.py).

Hand villa K501 (not Alsenan).
  Stair K-A: straight flight between two walls, +0.00 -> +1.70, 10 risers x 0.170, 9 goings x 0.280 (run 2.520).
    Each wall side, by hand: zigzag 2.520 + 10 x 0.170 = 4.220 lm; sloped hypot(2.520, 1.700) = sqrt(9.2404) =
    3.039803 lm. Two lines (left, right), never both forms valued: zigzag B7-07 8.440 / sloped B7-08 6.079606.
  Stair K-B: dog-leg, flight B1 on wall face X (s 0 .. 2.520, +0.00 -> +1.70), the other side OPEN (rail);
    half landing +1.70 against face X (s 2.520 .. 3.720, 1.200) and the end wall face Y (s 0 .. 2.400): level,
    FIN.SKIRTING, 1.200 + 2.400 = 3.600 lm; the corner X/Y counted once (no return piece). Flight B2 stacked over B1 on
    face X one storey up, +3.40 -> +5.10 over s 0 .. 2.520: a different strip from B1 (levels apart).
  Room K-R: floor +3.40 line measured along face X s 0 .. 3.720 by mistake (no floor there: B1 / landing below, B2
    above): retired only when the stair pieces cover it (B1 or B2 0 .. 2.520 + landing 2.520 .. 3.720 = 3.720).
"""
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t501"))
import t501_stair_skirting_home as K  # noqa: E402

RUN, RISE, N, R = 2.52, 1.70, 10, 0.17


def fl(pid, face, s0, s1, lv0, lv1, risers=N, cls=K.WALL, cause="", **kw):
    return K.Piece(pid, "K", face, K.FLIGHT, cls, s0, s1, lv0, lv1, risers, R, RUN, RISE, 0.0, cause, "", **kw)


def lvl(pid, face, s0, s1, lv, kind=K.LANDING, cls=K.WALL, cause="", **kw):
    return K.Piece(pid, "K", face, kind, cls, s0, s1, lv, lv, 0, 0.0, 0.0, 0.0, 0.0, cause, "", **kw)


# ------------------------------------------------------------------ normal
def test_straight_flight_between_walls_hand_values():
    left, right = fl("KA.L", "L", 0, RUN, 0, RISE), fl("KA.R", "R", 0, RUN, 0, RISE)
    K.check_one_owner([left, right])
    for p in (left, right):
        assert K.zigzag(p) == pytest.approx(4.220, abs=1e-9)
        assert K.sloped(p) == pytest.approx(math.sqrt(9.2404), abs=1e-9)
        assert K.sloped(p) == pytest.approx(3.039803, abs=1e-6)
    rows = [K.line(p) for p in (left, right)]
    assert all(r["status"] == K.FORM_HELD and r["value_lm"] is None and r["family"] == "B7-07 | B7-08" for r in rows)
    zz = [K.line(p, "zigzag") for p in (left, right)]
    sl = [K.line(p, "sloped") for p in (left, right)]
    assert {r["family"] for r in zz} == {"B7-07"} and sum(r["value_lm"] for r in zz) == pytest.approx(8.44)
    assert {r["family"] for r in sl} == {"B7-08"} and sum(r["value_lm"] for r in sl) == pytest.approx(6.079606, abs=1e-6)
    K.check_lines(rows + zz)


def test_dogleg_landing_level_once_and_stacked_flights():
    b1 = fl("KB1.X", "X", 0, RUN, 0, RISE)
    b2 = fl("KB2.X", "X", 0, RUN, 2 * RISE, 3 * RISE)  # stacked one storey over B1, levels apart
    lx = lvl("KB-LD.X", "X", RUN, RUN + 1.2, RISE)
    ly = lvl("KB-LD.Y", "Y", 0, 2.4, RISE)
    K.check_one_owner([b1, b2, lx, ly])
    rows = [K.line(p) for p in (lx, ly)]
    assert [r["family"] for r in rows] == ["FIN.SKIRTING"] * 2
    assert sum(r["value_lm"] for r in rows) == pytest.approx(3.600)


def test_retire_room_line_by_closure():
    b2 = fl("KB2.X", "X", 0, RUN, 2 * RISE, 3 * RISE)
    lx = lvl("KB-LD.X", "X", RUN, RUN + 1.2, RISE)
    rows = K.retire([("K-R X", "X", 0.0, 3.72, 2 * RISE, "certain")], [b2, lx])
    assert rows[0]["decision"].startswith("NOT_APPLICABLE") and rows[0]["residual_lm"] == pytest.approx(0, abs=1e-9)
    # one piece missing: the room figure stays (never dropped)
    rows = K.retire([("K-R X", "X", 0.0, 3.72, 2 * RISE, "certain")], [b2])
    assert rows[0]["decision"].startswith("KEEP") and rows[0]["residual_lm"] == pytest.approx(1.2)


def test_mirror_invariance():
    a = fl("M.a", "X", 0.0, RUN, 0.0, RISE)
    b = fl("M.b", "X", 10.0 - RUN, 10.0, RISE, 0.0)    # the same flight mirrored along the face
    assert K.zigzag(a) == pytest.approx(K.zigzag(b)) and K.sloped(a) == pytest.approx(K.sloped(b))


def test_split_conflict_keeps_parts_and_carrier():
    p = fl("KC", "X", 0, RUN, 0, RISE)
    a, b = K.split(p, 2.24, K.CONFLICT, "plan ends at the 9th riser, sheet 2 draws one more tread", 9)
    assert a.plan + b.plan == pytest.approx(RUN) and a.risers + b.risers == N
    assert K.zigzag(a) + K.zigzag(b) == pytest.approx(K.zigzag(p))
    b.beside["carried_by"] = ["ROOM"]
    room = lvl("ROOM", "X", 2.24, 4.0, RISE, kind=K.ROOM)
    K.check_one_owner([a, b, room])
    r = K.line(b)
    assert r["status"] == K.CONFLICT and r["value_lm"] is None and r["zigzag_lm"] is not None


# ------------------------------------------------------------------ adverse
def test_open_side_is_no_line():
    p = fl("O", "X", 0, RUN, 0, RISE, cls=K.OPEN)
    with pytest.raises(K.RuleError, match="open side"):
        K.line(p)


def test_landing_return_counted_twice_refused():
    lx = lvl("KB-LD.X", "X", RUN, RUN + 1.2, RISE)
    again = lvl("KB-LD.X-return", "X", RUN + 1.0, RUN + 1.2, RISE)
    with pytest.raises(K.RuleError, match="two owners"):
        K.check_one_owner([lx, again])


def test_flight_and_floor_same_level_refused():
    top = fl("T", "X", 0, RUN, 0, RISE)
    floor = lvl("F", "X", RUN - 0.3, 4.0, RISE, kind=K.ROOM)   # floor zone starting inside the flight's top tread
    with pytest.raises(K.RuleError, match="two owners"):
        K.check_one_owner([top, floor])


def test_conflict_without_carrier_refused():
    p = fl("KC", "X", 0, RUN, 0, RISE)
    a, b = K.split(p, 2.24, K.CONFLICT, "cause", 9)
    room = lvl("ROOM", "X", 2.24, 4.0, RISE, kind=K.ROOM)
    with pytest.raises(K.RuleError, match="two owners"):
        K.check_one_owner([a, b, room])


def test_retire_where_floor_stands_refused():
    land = lvl("L", "X", 0, 1.2, 1.7)
    with pytest.raises(K.RuleError, match="floor's own level"):
        K.retire([("R", "X", 0, 1.2, 1.7, "certain")], [land])


def test_side_is_not_a_form():
    p = fl("S", "X", 0, RUN, 0, RISE)
    for bad in ("wall side", "open side", "B7-07"):
        with pytest.raises(K.RuleError, match="form"):
            K.line(p, bad)


def test_held_never_carries_a_value_and_confirmed_never_zero():
    p = fl("H", "X", 0, RUN, 0, RISE, cls=K.HELD, cause="window beside the flight")
    r = K.line(p)
    assert r["value_lm"] is None
    r["value_lm"] = 0.0
    with pytest.raises(K.RuleError, match="carries a value"):
        K.check_lines([r])
    ok = K.line(lvl("L", "X", 0, 1.2, 1.7))
    ok["value_lm"] = 0.0
    with pytest.raises(K.RuleError, match="positive"):
        K.check_lines([ok])


def test_value_neither_form_refused():
    r = K.line(fl("V", "X", 0, RUN, 0, RISE), "zigzag")
    r["value_lm"] = (r["zigzag_lm"] + r["sloped_lm"]) / 2          # an average of the two forms
    with pytest.raises(K.RuleError, match="neither form"):
        K.check_lines([r])


def test_held_without_cause_and_millimetres_refused():
    with pytest.raises(K.RuleError, match="without a cause"):
        fl("H", "X", 0, RUN, 0, RISE, cls=K.HELD)
    with pytest.raises(K.RuleError, match="millimetres"):
        fl("MM", "X", 0, 2520, 0, RISE)
    with pytest.raises(K.RuleError, match="run and rise"):
        K.Piece("NR", "K", "X", K.FLIGHT, K.WALL, 0, RUN, 0, RISE, N, R, 0.0, 0.0)
