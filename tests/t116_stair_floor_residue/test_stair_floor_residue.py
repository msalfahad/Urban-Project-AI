"""STAIR_FLOOR_RESIDUE_V1 on hand-calculated synthetic fixtures (not Alsenan): an upper-floor open hall with a dog-leg
stair and a winder, an upper-floor room with a stair opening (void) and two flights of the plan below, the same hall
on the lowest storey, missing outlines; each mirrored, rotated and in mm.

Hand calculations (m, m2):
HALL (0..8 x 0..5 = 40.00), dog-leg continuing from the storey below (stacked_over):
    west flight 1.00 wide, treads y 2.00 .. 4.00 ............................................ 2.00
    east flight 1.00 wide (x 1.20 .. 2.20), treads y 2.30 .. 4.00 ............................ 1.70
    winder 1.00 x 1.00 (x 0 .. 1, y 4 .. 5) in two quads, one NOT convex .................... 1.00  treads 4.70
    well gap between the flights 0.20 x 2.00, closed at both ends ........................... 0.40  stair
    turning landing x 1.00 .. 2.20, y 4.00 .. 5.00 (closed by the stringer x = 2.20) ........ 1.20  stair
    foot of the east flight 1.00 x 0.30 (y 2.00 .. 2.30), open to the hall .................. 0.30  HELD
    floor 40.00 - 4.70 - 0.40 - 1.20 = 33.70 (high), less 0.30 = 33.40 (low)
OPENING ROOM (0..10 x 0..8 = 80.00): outlined void x 0 .. 4, y 3 .. 6 (12.00); slab edge line y = 6.05 (x 0 .. 4.05)
and x = 4.05 (y 0 .. 6.05): the opening 4.05 x 6.05 = 24.5025; flight of the plan below seen in it, x 0 .. 1,
y 0.5 .. 3.0 (2.50); arriving flight of the plan below beside it, x 5 .. 6, y 0 .. 2 (2.00) with a 0.05 balustrade
x 6.00 .. 6.05, y 0 .. 2 (0.10):
    opening residue 24.5025 - 12.00 - 2.50 = 10.0025 (strips 0.2025 + 0.15, band 9.65)
    balustrade beside one flight, open to the floor: 0.10 HELD
    floor 80 - 12 - 2.5 - 2.0 - 10.0025 = 53.4975 (high), less 0.10 = 53.3975 (low)
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_floor as AF  # noqa: E402
from engine.source import stair_floor_residue as SFR  # noqa: E402

TOL = 1e-3


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _flight(fid, kind, quads, layer="STAIR-A", **marks):
    d = {"flight_id": fid, "kind": kind, "layer": layer, "tread_quads": quads}
    d.update(marks)
    return d


def _straight_y(fid, x0, x1, y0, y1, n, **marks):
    g = (y1 - y0) / n
    return _flight(fid, "STRAIGHT", [_rect(x0, y0 + k * g, x1, y0 + (k + 1) * g) for k in range(n)], **marks)


def _straight_x(fid, x0, x1, y0, y1, n, **marks):
    g = (x1 - x0) / n
    return _flight(fid, "STRAIGHT", [_rect(x0 + k * g, y0, x0 + (k + 1) * g, y1) for k in range(n)], **marks)


def _seg(a, b, layer="STAIR-A"):
    return {"layer": layer, "a": a, "b": b}


BELOW = {"floor": "LOWER", "reading": "STACKED"}
SEEN = {"floor": "LOWER", "reading": "SEEN_THROUGH_VOID"}
WINDER_Q1 = [(1.0, 4.0), (0.0, 4.0), (0.0, 5.0), (0.4, 4.4)]        # reflex vertex at (0.4, 4.4): not convex
WINDER_Q2 = [(1.0, 4.0), (0.4, 4.4), (0.0, 5.0), (1.0, 5.0)]


def hall(stacked=True):
    m = {"stacked_over": BELOW} if stacked else {}
    flights = [_straight_y("H:F1", 0.0, 1.0, 2.0, 4.0, 8, **m),
               _straight_y("H:F2", 1.2, 2.2, 2.3, 4.0, 6, **m),
               _flight("H:F3", "RADIAL", [WINDER_Q1, WINDER_Q2], **m)]
    segs = [_seg((1.0, 2.0), (1.0, 4.0)), _seg((1.2, 2.0), (1.2, 4.0)), _seg((1.0, 2.0), (1.2, 2.0)),
            _seg((1.0, 4.0), (2.2, 4.0)), _seg((2.2, 2.0), (2.2, 5.0)),
            _seg((3.0, 1.0), (3.5, 1.0), layer="FURNITURE")]                 # another layer: ignored
    face = {"face_id": "HALL", "room_id": "HALL", "polygon": _rect(0, 0, 8, 5), "hole_polygons": [], "area_m2": 40.0,
            "voids": [], "symbols_inside": {"stair_flights": flights}}
    return face, [], segs


def opening_room():
    flights = [_straight_y("O:F1", 0.0, 1.0, 0.5, 3.0, 8, drawn_on_plan_below=SEEN),
               _straight_y("O:F2", 5.0, 6.0, 0.0, 2.0, 7, drawn_on_plan_below=SEEN)]
    segs = [_seg((0.0, 6.05), (4.05, 6.05)), _seg((4.05, 6.05), (4.05, 0.0)),
            _seg((6.0, 0.0), (6.0, 2.0)), _seg((6.05, 0.0), (6.05, 2.0)), _seg((6.0, 2.0), (6.05, 2.0)),
            _seg((0.0, 3.0), (4.0, 6.0)), _seg((0.0, 6.0), (4.0, 3.0))]       # the X of the void
    face = {"face_id": "OPEN", "room_id": "OPEN", "polygon": _rect(0, 0, 10, 8), "hole_polygons": [], "area_m2": 80.0,
            "voids": [{"void_id": "V1"}], "symbols_inside": {"stair_flights": flights}}
    voids = [{"void_id": "V1", "corners": _rect(0.0, 3.0, 4.0, 6.0)}]
    return face, voids, segs


# ---------------------------------------------------------------- transforms (mirror, rotation, units)
def _tf(fn, face, voids, segs, scale=1.0):
    P = lambda pts: [fn(p) for p in pts]  # noqa: E731
    f = dict(face, polygon=P(face["polygon"]), hole_polygons=[P(h) for h in face["hole_polygons"]],
             area_m2=face["area_m2"])
    f["symbols_inside"] = {"stair_flights": [dict(fl, tread_quads=[P(q) for q in fl["tread_quads"]])
                                             for fl in face["symbols_inside"]["stair_flights"]]}
    v = [dict(x, corners=P(x["corners"])) for x in voids]
    s = [dict(x, a=fn(x["a"]), b=fn(x["b"])) for x in segs]
    return f, v, s


def _variants(builder):
    c, sn = math.cos(math.radians(30)), math.sin(math.radians(30))
    yield "plain_m", builder(), 1.0
    yield "mirrored", _tf(lambda p: (-p[0], p[1]), *builder()), 1.0
    yield "rotated_30", _tf(lambda p: (p[0] * c - p[1] * sn, p[0] * sn + p[1] * c), *builder()), 1.0
    yield "mm_rotated_mirrored", _tf(lambda p: (1000 * (p[1] * c + p[0] * sn), 1000 * (p[1] * sn - p[0] * c)),
                                     *builder()), 0.001


def _run(parts, unit):
    face, voids, segs = parts
    return SFR.face_residue(face, voids=voids, segments=segs, unit_m=unit)


@pytest.mark.parametrize("name,parts,unit", list(_variants(hall)))
def test_dog_leg_hall_upper_storey(name, parts, unit):
    r = _run(parts, unit)
    assert r["scope"] == "STAIR_PASSES_THROUGH_SLAB"
    assert r["stair_flights_m2"] == pytest.approx(4.70, abs=TOL), name
    assert r["stair_footprint_m2"] == pytest.approx(0.40 + 1.20, abs=TOL), name
    assert r["void_residue_m2"] == pytest.approx(0.0, abs=TOL)
    assert [h["category"] for h in r["held"]] == ["STAIR_FOOT_UNSETTLED"]
    assert r["held_m2"] == pytest.approx(0.30, abs=TOL)
    assert r["held"][0]["dims_m"] == pytest.approx([1.00, 0.30], abs=TOL)
    assert r["status"] == "HELD_RANGE" and r["floor_net_m2"] is None          # held, never a number, never 0
    assert r["floor_net_low_m2"] == pytest.approx(33.40, abs=TOL)
    assert r["floor_net_high_m2"] == pytest.approx(33.70, abs=TOL)
    assert r["conservation"]["state"] == "BALANCED"


@pytest.mark.parametrize("name,parts,unit", list(_variants(opening_room)))
def test_stair_opening_upper_storey(name, parts, unit):
    r = _run(parts, unit)
    assert r["void_m2"] == pytest.approx(12.0, abs=TOL), name
    assert r["stair_below_seen_m2"] == pytest.approx(4.50, abs=TOL)
    assert r["stair_flights_m2"] == pytest.approx(0.0, abs=TOL)
    assert r["void_residue_m2"] == pytest.approx(10.0025, abs=TOL), name
    assert r["stair_footprint_m2"] == pytest.approx(0.0, abs=TOL)
    assert [h["category"] for h in r["held"]] == ["SIDE_ELEMENT_UNSETTLED"]
    assert r["held_m2"] == pytest.approx(0.10, abs=TOL)
    assert r["floor_net_low_m2"] == pytest.approx(53.3975, abs=TOL)
    assert r["floor_net_high_m2"] == pytest.approx(53.4975, abs=TOL)
    assert r["conservation"]["state"] == "BALANCED"


def test_lowest_storey_is_not_assessed_only_treads_deducted():
    r = _run(hall(stacked=False), 1.0)
    assert r["scope"] == "LOWEST_STOREY_NOT_ASSESSED"
    assert r["pieces"] == [] and r["held"] == []
    assert r["status"] == "RELEASED" and r["floor_net_m2"] == pytest.approx(40.0 - 4.70, abs=TOL)
    assert sum(x["m2"] for x in r["not_assessed"]) == pytest.approx(1.60, abs=TOL)   # gap + landing, listed only


def test_exact_union_fixes_the_non_convex_winder_and_the_double_count():
    face, _, _ = hall()
    f = dict(face, polygon_m=face["polygon"], hole_polygons_m=[])
    legacy, _ = AF._treads(f, f["symbols_inside"]["stair_flights"], [], 1.0)
    exact = SFR.face_residue(face, segments=[], unit_m=1.0)["stair_flights_m2"]
    assert exact == pytest.approx(4.70, abs=1e-6)
    assert abs(legacy - exact) > 0.05          # the clipped non-convex quad: the arch_floor defect this piece replaces
    # two flights drawn over each other: counted once
    dup = dict(face, symbols_inside={"stair_flights": face["symbols_inside"]["stair_flights"] +
                                     [_straight_y("H:F9", 0.0, 1.0, 3.0, 4.0, 4, stacked_over=BELOW)]})
    r = SFR.face_residue(dup, segments=[], unit_m=1.0)
    assert r["stair_flights_m2"] == pytest.approx(4.70, abs=1e-6)
    assert r["treads_quad_sum_m2"] == pytest.approx(5.70, abs=1e-6)


def test_missing_stair_outline_is_held_never_zero():
    face, voids, segs = hall()
    face["symbols_inside"]["stair_flights"].append(_flight("H:F4", "STRAIGHT", []))
    r = SFR.face_residue(face, voids=voids, segments=segs, unit_m=1.0)
    assert r["status"] == "HELD" and r["floor_net_m2"] is None and r["floor_net_low_m2"] is None
    assert "STAIR_OUTLINE_MISSING" in r["reason"]


def test_missing_void_outline_is_held_never_zero():
    face, voids, segs = opening_room()
    r = SFR.face_residue(face, voids=[], segments=segs, unit_m=1.0)
    assert r["status"] == "HELD" and r["floor_net_m2"] is None
    assert "VOID_OUTLINE_MISSING" in r["reason"]


def test_room_without_stair_or_void_keeps_its_own_area():
    face = {"face_id": "R", "polygon": _rect(0, 0, 3.3, 4.1), "hole_polygons": [], "area_m2": 13.53, "voids": []}
    r = SFR.face_residue(face, unit_m=1.0)
    assert r["status"] == "RELEASED" and r["floor_net_m2"] == 13.53 and r["scope"] == "NO_STAIR_NO_VOID"


def test_a_door_point_keeps_a_closed_cell_as_floor():
    face, voids, segs = hall()
    # a closed cell beside the landing reached only through stair lines, but a door opens into it: floor, not stair
    segs = segs + [_seg((2.2, 4.0), (3.2, 4.0)), _seg((3.2, 4.0), (3.2, 5.0))]
    r0 = SFR.face_residue(face, voids=voids, segments=segs, unit_m=1.0)
    r1 = SFR.face_residue(face, voids=voids, segments=segs, unit_m=1.0, floor_points=[(2.7, 4.95)])
    assert r1["stair_footprint_m2"] == pytest.approx(1.60, abs=TOL)
    assert r0["stair_footprint_m2"] == pytest.approx(2.60, abs=TOL)      # closed by stair lines, no door: stair


def test_policy_record_says_not_wired():
    p = SFR.policy_record()
    assert p["policy_id"] == "STAIR_FLOOR_RESIDUE_V1" and p["wired"] is False
