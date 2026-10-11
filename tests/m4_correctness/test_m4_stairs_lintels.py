"""M4 generic stair and lintel measurement with hand-derived truth (stdlib geometry; no project data).

Stairs (tread lines drawn in a stair zone):
    straight  9 parallel lines 1.2 m long at a 0.30 m pitch -> FLIGHT, going 0.30, drawn span 8 x 0.30 = 2.40 m
              LINES_PLUS_ONE: 10 risers over 1.80 m = 0.18 m, 9 treads: flight plan 9 x 0.30 x 1.2 = 3.24 m2
              section = 9 step triangles (0.30 x 0.18 / 2) + waist strip 2.70 x (0.15 / cos(pitch)), x 1.2 width
              landing = zone 4.50 - 3.24 = 1.26 m2 x 0.15 (the flight's last tread is never counted twice)
    LINES     9 risers = 0.20 m (inside the band), plan 8 treads
    partial   a 4.20 m rise over 10 risers (0.42 m) -> PARTIAL_STAIR, nothing measured
    winder    18 radial lines every 20 deg, r 0.25 - 1.20 m -> WINDER, sweep 340 deg, going on r 0.725 m
    no fan    lines tangent to a 0.5 m circle meet in no point -> not a stair run
Lintels (printed schedule rows by opening width in cm, bounds inclusive):
    0.90 opening, 0.20 wall, masonry both ends: length 0.90 + 2 x bearing (0.15 / 0.20 / 0.25)
    a column jamb takes no bearing; 1.005 m falls between two bands; 3.50 m is above the schedule
    census: a column standing inside a wall gap bounds the opening at its face (1.2 m, not 1.6 m)
"""

from __future__ import annotations

import math

import pytest

from engine.source import lintel_measure as LMS             # noqa: E402
from engine.source import lintel_qto as LQ                  # noqa: E402
from engine.source import opening_census as OC              # noqa: E402
from engine.source import stair_measure as SM               # noqa: E402

U = 0.001


def _straight():
    return [{"a": (x, 0.0), "b": (x, 1200.0)} for x in range(0, 2401, 300)]


def test_straight_flight_from_treads():
    run = SM.flight(_straight(), U)
    assert run["kind"] == "FLIGHT" and run["n_lines"] == 9
    assert (run["going_m"], run["width_m"], run["run_m"]) == pytest.approx((0.3, 1.2, 2.4))
    q = SM.quantities(4.5, run, 1.8, 0.15)
    assert q["state"] == "MEASURED" and q["risers"] == 10 and q["riser_m"] == pytest.approx(0.18)
    g, R, w, t = 0.3, 0.18, 1.2, 0.15
    hand = w * (9 * g * R / 2 + 9 * g * t * math.hypot(g, R) / g)
    assert q["flight_m3"] == pytest.approx(hand)
    assert q["flight_plan_m2"] == pytest.approx(9 * g * w)
    assert q["landing_m2"] == pytest.approx(4.5 - 3.24) and q["landing_m3"] == pytest.approx(1.26 * t)
    assert q["flight_plan_m2"] + q["landing_m2"] == pytest.approx(4.5)          # the zone, once
    assert q["riser_face_m2"] == pytest.approx(10 * R * w)


def test_riser_rule_and_partial_zone():
    run = SM.flight(_straight(), U)
    q = SM.quantities(4.5, run, 1.8, 0.15, riser_rule="LINES")
    assert q["risers"] == 9 and q["riser_m"] == pytest.approx(0.2) and q["flight_plan_m2"] == pytest.approx(2.88)
    p = SM.quantities(4.5, run, 4.2, 0.15)
    assert p["state"] == "PARTIAL_STAIR" and "flight_m3" not in p
    small = SM.quantities(2.0, run, 1.8, 0.15)                     # the flight outgrows the zone: reported
    assert small["landing_m2"] == 0.0 and small["overflow_m2"] == pytest.approx(3.24 - 2.0)


def test_winder_and_lines_that_do_not_fan():
    segs = []
    for k in range(18):
        a = math.radians(20 * k)
        segs.append({"a": (250 * math.cos(a), 250 * math.sin(a)), "b": (1200 * math.cos(a), 1200 * math.sin(a))})
    run = SM.flight(segs, U)
    assert run["kind"] == "WINDER" and run["n_lines"] == 18
    assert run["sweep_deg"] == pytest.approx(340.0)
    assert run["going_m"] == pytest.approx(0.725 * math.radians(340) / 17)
    assert run["plan_m2"] == pytest.approx(0.5 * math.radians(340) * (1.2 ** 2 - 0.25 ** 2))
    q = SM.quantities(5.0, run, 19 * 0.18, 0.15)
    full = math.pi * (1.2 ** 2 - 0.25 ** 2)                       # 18 treads of 20 deg: one full turn, never more
    assert q["state"] == "MEASURED" and q["flight_plan_m2"] == pytest.approx(full)
    th = math.atan2(0.18, run["going_m"])
    assert q["flight_m3"] == pytest.approx(full * (0.15 / math.cos(th) + 0.09))
    tangent = []
    for k in range(8):
        a = math.radians(25 * k)
        px, py = 500 * math.cos(a), 500 * math.sin(a)
        dx, dy = -math.sin(a), math.cos(a)
        tangent.append({"a": (px - 600 * dx, py - 600 * dy), "b": (px + 600 * dx, py + 600 * dy)})
    assert SM.flight(tangent, U) is None
    assert SM.flight(_straight()[:4], U) is None                  # fewer than five lines: no run


ROWS = [{"row_id": "L1", "lo": 0, "hi": 100, "D_m": 0.20, "bottom": (2, 12), "top": (2, 10), "stirrup_rate": (5, 8)},
        {"row_id": "L2", "lo": 101, "hi": 200, "D_m": 0.20, "bottom": (2, 14), "top": (2, 12), "stirrup_rate": (5, 8)},
        {"row_id": "L3", "lo": 201, "hi": 300, "D_m": 0.30, "bottom": (3, 16), "top": (3, 14), "stirrup_rate": (5, 8)}]


def _op(width, start=OC.MASONRY_JAMB, end=OC.MASONRY_JAMB):
    return {"width_m": width, "wall_t_m": 0.2, "start_jamb": start, "end_jamb": end}


def test_lintel_by_schedule_row():
    lt = LMS.lintel(_op(0.9), ROWS)
    assert lt["state"] == "MEASURED" and lt["row"] == "L1" and lt["bearing_ends"] == 2
    assert lt["length_m"] == pytest.approx((1.2, 1.3, 1.4))
    assert lt["concrete_m3"] == pytest.approx((0.2 * 0.2 * 1.2, 0.2 * 0.2 * 1.3, 0.2 * 0.2 * 1.4))
    bars = {b[0]: b for b in lt["bars"]}
    assert bars["BOTTOM"][1:3] == (2, 12) and bars["BOTTOM"][3][1] == pytest.approx(1.3 - 2 * 0.025)
    assert lt["stirrups"]["count"] == (6, 7, 7)                     # ceil(5 / m x length)
    col = LMS.lintel(_op(0.9, end=OC.COLUMN_JAMB), ROWS)
    assert col["bearing_ends"] == 1 and col["length_m"][1] == pytest.approx(1.1)
    assert LMS.lintel(_op(1.5), ROWS)["row"] == "L2"
    assert LMS.lintel(_op(1.005), ROWS)["state"] == LQ.BOUNDARY_GAP     # 100.5 cm: between two printed bands
    assert LMS.lintel(_op(3.5), ROWS)["state"] == LQ.ABOVE_SCHEDULE     # never extrapolated


def test_beam_over_opening():
    op = {"u": (1.0, 0.0), "n": (0.0, 1.0), "s0": 1000.0, "s1": 1900.0, "o0": -100.0, "o1": 100.0}

    def rect(x0, y0, x1, y1):
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    assert LMS.beam_over(op, [rect(0, -150, 3000, 150)]) == "FULL"
    assert LMS.beam_over(op, [rect(1500, -150, 3000, 150)]) == "PARTIAL"
    assert LMS.beam_over(op, [rect(0, 1000, 3000, 1300)]) == "NONE"
    assert LMS.beam_over(op, []) == "NONE"


def _plan():
    segs = []

    def L(a, b, lay="A-WALL"):
        segs.append({"id": len(segs), "layer": lay, "a": a, "b": b})
    # wall 1: a 0.90 opening between two masonry jambs (closing lines drawn)
    for a, b in (((0, 0), (2000, 0)), ((0, 200), (2000, 200)), ((2900, 0), (5000, 0)), ((2900, 200), (5000, 200)),
                 ((2000, 0), (2000, 200)), ((2900, 0), (2900, 200))):
        L(a, b)
    # wall 2: an opening from a masonry jamb to a column 4200 - 4600; the wall resumes behind the column
    for a, b in (((0, 3000), (3000, 3000)), ((0, 3200), (3000, 3200)), ((3000, 3000), (3000, 3200)),
                 ((4600, 3000), (7000, 3000)), ((4600, 3200), (7000, 3200))):
        L(a, b)
    # wall 3 plain; wall 4 with one face broken only (not an opening)
    for a, b in (((0, 6000), (5000, 6000)), ((0, 6200), (5000, 6200)), ((0, 9000), (5000, 9000)),
                 ((0, 9200), (2000, 9200)), ((3000, 9200), (5000, 9200))):
        L(a, b)
    L((0, -500), (5000, -500), "A-TEXT")                              # annotation never forms a wall
    return segs, [(4200, 2900, 4600, 3300)]


def test_opening_census_on_wall_layers():
    segs, cols = _plan()
    lays, score = LMS.wall_layers(segs, U)
    assert lays == ["A-WALL"]
    ops, rej = LMS.openings(segs, U, lays, cols)
    by = sorted((round(o["width_m"], 3), o["start_jamb"], o["end_jamb"], o["split_at_column"]) for o in ops)
    assert by == [(0.9, OC.MASONRY_JAMB, OC.MASONRY_JAMB, False), (1.2, OC.MASONRY_JAMB, OC.COLUMN_JAMB, True)]
    assert all(o["wall_t_m"] == pytest.approx(0.2) for o in ops)
    # without the column the gap runs to where the wall resumes (the M3 census reading, kept for comparison)
    ops0, _ = LMS.openings(segs, U, lays, [])
    assert sorted(round(o["width_m"], 3) for o in ops0) == [0.9, 1.6]


def test_column_inside_gap_middle_gives_two_openings():
    band = {"u": (1.0, 0.0), "n": (0.0, 1.0), "A": {"off": 0.0}, "B": {"off": 200.0}}
    g = {"s0": 1000.0, "s1": 4000.0, "width": 3000.0, "start_jamb": OC.MASONRY_JAMB, "end_jamb": OC.MASONRY_JAMB,
         "state": OC.OPENING}
    col = [("C", [(2000, -100), (2400, -100), (2400, 300), (2000, 300)])]
    out = LMS._split_at_columns(g, band, col, 500.0)
    assert [(o["s0"], o["s1"], o["start_jamb"], o["end_jamb"]) for o in out] == [
        (1000.0, 2000.0, OC.MASONRY_JAMB, OC.COLUMN_JAMB), (2400.0, 4000.0, OC.COLUMN_JAMB, OC.MASONRY_JAMB)]
    narrow = LMS._split_at_columns(dict(g, s1=2700.0, width=1700.0), band, col, 500.0)   # 0.3 m reach: dropped
    assert [(o["s0"], o["s1"]) for o in narrow] == [(1000.0, 2000.0)]
    unb = LMS._split_at_columns(dict(g, start_jamb=OC.UNBOUNDED, state=OC.REJECTED), band, col, 500.0)
    assert [o["state"] for o in unb] == [OC.REJECTED, OC.OPENING]
