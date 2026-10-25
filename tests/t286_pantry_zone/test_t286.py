"""T-286: engine 'doorway' / zone pieces inside an open room closed by what is drawn (R-T286-1), the room-side line of a
curved opening from its drawn line (R-T286-2), held never summed as 0 (R-T286-3). Fixtures are NOT Alsenan; hand truth:

Villa S open kitchen (metres): printed box 4.00 x 2.50 = 10.000 m2, a column notch 0.50 x 0.10 = 0.050 in its corner.
A counter L drawn on the fixture layer; the engine cut a piece P = (0,0)-(2.0,0)-(2.0,1.0)-(1.4,1.0)-(1.4,0.6)-(0,0.6):
  area 2.0 x 0.6 + 0.6 x 0.4 = 1.440 m2, perimeter 2.0 + 1.0 + 0.6 + 0.4 + 1.4 + 0.6 = 6.000 m; edges: wall face 2.0,
  box edge 1.0, undrawn zone line 0.6, counter outline 0.4 + 1.4 + 0.6. Box closes 10.000 - 0.050 - 1.440 - 8.510 = 0.
Villa S curved window, room on the CONCAVE side: band outer (garden) face r 3.00, room-side glass r 2.80, one sweep
  1.5 rad: outer 4.500, room arc 4.200; glass returns 0.05 + 0.05; a 0.15 partition stands on the glass -> room side
  4.200 + 0.100 - 0.150 = 4.150 m, SHORTER than the outer face 4.500 (-0.350); printed width 4.50 shown beside only.
Villa S wedge room: faces 3.00 and 2.20 drawn (DRAWING-CONFIRMED), the oblique face HELD -> established 5.200, held 1.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t286"
sys.path.insert(0, str(HERE))
import pantry_zone as PZ  # noqa: E402

P = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (1.4, 1.0), (1.4, 0.6), (0.0, 0.6)]
BOUNDS = [{"kind": "WALL_FACE", "length_m": 2.0, "ref": "w1"}, {"kind": "ROOM_EDGE", "length_m": 1.0, "ref": "e1"},
          {"kind": "ZONE_LINE_UNDRAWN", "length_m": 0.6, "ref": None},
          {"kind": "FIXTURE_OUTLINE", "length_m": 0.4, "ref": "c1"},
          {"kind": "FIXTURE_OUTLINE", "length_m": 1.4, "ref": "c2"},
          {"kind": "FIXTURE_OUTLINE", "length_m": 0.6, "ref": "c3"}]
BOX = [(0.0, 0.0), (2.0, 0.0), (2.0, 4.0), (-0.5, 4.0), (-0.5, 0.0)]  # 2.50 x 4.00, the piece in its south-east part


def _room(cls="WET", src="villa S decision D-S1 (open kitchen wet within its printed box)", box=BOX):
    return [{"id": "S-KITCHEN", "box_m": box, "floor_class": cls, "class_source": src}]


def _piece(pts=P, area=1.44):
    return {"id": "S-P", "polygon_m": pts, "area_m2": area, "engine_class": "UNATTRIBUTED"}


def _tf(pts, f):
    return [f(p) for p in pts]


def _rot(deg, dx=1000.0, dy=-500.0):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return lambda p: (c * p[0] - s * p[1] + dx, s * p[0] + c * p[1] + dy)


# ------------------------------------------------------------------------------------------------- R-T286-1 normal
def test_piece_bounded_by_counter_joins_wet_room_floor():
    r = PZ.reclass_piece(_piece(), BOUNDS, _room())
    assert r["disposition"] == "TO_ROOM_FLOOR_WET" and r["status"] == "DRAWING-CONFIRMED"
    assert r["area_m2"] == pytest.approx(1.44, abs=1e-9)
    assert r["fixture_outline_m"] == pytest.approx(2.4) and r["undrawn_m"] == pytest.approx(0.6)


def test_dry_room_takes_dry_class():
    assert PZ.reclass_piece(_piece(), BOUNDS, _room("DRY"))["disposition"] == "TO_ROOM_FLOOR_DRY"


@pytest.mark.parametrize("f", [lambda p: (-p[0], p[1]), _rot(30.0), _rot(-127.0, -3e5, 8e5)])
def test_mirror_and_rotation_same_result(f):
    r = PZ.reclass_piece(_piece(_tf(P, f)), BOUNDS, _room(box=_tf(BOX, f)))
    assert r["disposition"] == "TO_ROOM_FLOOR_WET" and r["area_m2"] == pytest.approx(1.44, abs=1e-6)


def test_box_closure_names_every_piece():
    c = PZ.box_closure(10.0, {"column": 0.05}, {"S-P": 1.44, "rest": 8.51})
    assert c["closes"] and abs(c["residual_m2"]) < 1e-9


# ------------------------------------------------------------------------------------------------ R-T286-1 adverse
def test_opening_jamb_keeps_strip_treatment():
    b = [dict(x) for x in BOUNDS]
    b[3] = {"kind": "OPENING_JAMB", "length_m": 0.4, "ref": "j1"}
    r = PZ.reclass_piece(_piece(), b, _room())
    assert r["disposition"] == "DOORWAY_STRIP" and r["status"] == "UNCHANGED"


def test_piece_across_box_is_held_with_area_kept():
    small = [(0.0, 0.0), (2.0, 0.0), (2.0, 0.8), (-0.5, 0.8), (-0.5, 0.0)]
    r = PZ.reclass_piece(_piece(), BOUNDS, _room(box=[(0.0, 0.0), (1.0, 0.0), (1.0, 4.0), (0.0, 4.0)]))
    assert r["status"] == "HELD" and r["area_m2"] == pytest.approx(1.44)
    r2 = PZ.reclass_piece(_piece(), BOUNDS, _room(box=[(5.0, 5.0), (6.0, 5.0), (6.0, 6.0)]))
    assert r2["status"] == "HELD" and "no printed room box" in r2["reason"] and r2["area_m2"] > 0
    assert PZ.reclass_piece(_piece(), BOUNDS, _room(box=small))["status"] == "HELD"  # piece reaches y 1.0


def test_two_boxes_and_held_class():
    two = _room() + [{"id": "S-2", "box_m": BOX, "floor_class": "DRY", "class_source": "x"}]
    assert PZ.reclass_piece(_piece(), BOUNDS, two)["status"] == "HELD"
    r = PZ.reclass_piece(_piece(), BOUNDS, _room("HELD", None))
    assert r["status"] == "HELD" and r["area_m2"] == pytest.approx(1.44)


def test_class_without_source_refused():
    with pytest.raises(PZ.ZoneError):
        PZ.reclass_piece(_piece(), BOUNDS, _room("WET", None))


def test_millimetres_refused():
    with pytest.raises(PZ.ZoneError, match="millimetres"):
        PZ.reclass_piece(_piece([(x * 1000, y * 1000) for x, y in P]), BOUNDS, _room())


@pytest.mark.parametrize("area", [1.5, None])
def test_stated_area_must_match(area):
    with pytest.raises(PZ.ZoneError):
        PZ.reclass_piece(_piece(area=area), BOUNDS, _room())


def test_bounds_must_close_and_cite():
    with pytest.raises(PZ.ZoneError, match="perimeter"):
        PZ.reclass_piece(_piece(), BOUNDS[:-1], _room())
    b = [dict(x) for x in BOUNDS]
    b[0]["ref"] = None
    with pytest.raises(PZ.ZoneError, match="reference"):
        PZ.reclass_piece(_piece(), b, _room())
    b = [dict(x) for x in BOUNDS]
    b[1]["kind"] = "DOOR?"
    with pytest.raises(PZ.ZoneError):
        PZ.reclass_piece(_piece(), b, _room())


def test_closure_refuses_none_and_shows_missing_piece():
    with pytest.raises(PZ.ZoneError, match="never 0"):
        PZ.box_closure(10.0, {"column": 0.05}, {"S-P": None, "rest": 8.51})
    c = PZ.box_closure(10.0, {"column": 0.05}, {"rest": 8.51})
    assert not c["closes"] and c["residual_m2"] == pytest.approx(1.44)


# --------------------------------------------------------------------------------------------- R-T286-2 room side
def _arc_poly(r, sweep=1.5, a0=0.3, ret=0.05, scale=1.0, mirror=False):
    a1 = a0 + sweep
    p0 = (r * math.cos(a0), r * math.sin(a0))
    p1 = (r * math.cos(a1), r * math.sin(a1))
    q0 = ((r + ret) * math.cos(a0), (r + ret) * math.sin(a0))
    q1 = ((r + ret) * math.cos(a1), (r + ret) * math.sin(a1))
    bu = math.tan(sweep / 4)
    pts = [(q0[0], q0[1], 0.0), (p0[0], p0[1], bu), (p1[0], p1[1], 0.0), (q1[0], q1[1], 0.0)] if ret else \
        [(p0[0], p0[1], bu), (p1[0], p1[1], 0.0)]
    if mirror:
        pts = [(-x, y, -b) for x, y, b in pts]
    return [(x * scale, y * scale, b) for x, y, b in pts]


ROOM_FACE = {"source": "DRAWN_LINE", "ref": "g1", "polyline_xyb": _arc_poly(2.80), "room_touches": True}
OUTER = {"ref": "o1", "polyline_xyb": _arc_poly(3.00, ret=0)}
PART = [{"ref": "p1", "length_m": 0.15}]


def test_room_side_shorter_than_outer_face():
    r = PZ.room_side_line(ROOM_FACE, PART, OUTER, printed_width_m=4.5)
    assert r["arcs"][0][1] == pytest.approx(4.2, abs=1e-6)
    assert r["room_side_m"] == pytest.approx(4.15, abs=1e-4)
    assert r["other_face_m"] == pytest.approx(4.5, abs=1e-4) and r["room_minus_other_m"] == pytest.approx(-0.35, abs=1e-4)
    assert r["room_minus_printed_m"] == pytest.approx(-0.35, abs=1e-4)


def test_room_side_mirror_same():
    f = dict(ROOM_FACE, polyline_xyb=_arc_poly(2.80, mirror=True))
    assert PZ.room_side_line(f, PART)["room_side_m"] == pytest.approx(4.15, abs=1e-4)


def test_partition_end_from_arc_points():
    c, r = (0.0, 0.0), 2.80
    th = 0.15 / r
    p1, p2 = (r * math.cos(1.0), r * math.sin(1.0)), (r * math.cos(1.0 + th), r * math.sin(1.0 + th))
    assert PZ.arc_between(c, r, p1, p2) == pytest.approx(0.15, abs=1e-9)
    with pytest.raises(PZ.ZoneError, match="not on the arc"):
        PZ.arc_between(c, r, p1, (3.0, 0.0))


@pytest.mark.parametrize("src", ["SCHEDULE", "DIMENSION_TEXT", None])
def test_schedule_or_text_width_refused(src):
    with pytest.raises(PZ.ZoneError, match="refused"):
        PZ.room_side_line(dict(ROOM_FACE, source=src), PART)


def test_other_face_offered_as_room_face_refused():
    with pytest.raises(PZ.ZoneError, match="no room touches"):
        PZ.room_side_line({"source": "DRAWN_LINE", "ref": "o1", "polyline_xyb": OUTER["polyline_xyb"],
                           "room_touches": False}, PART)


def test_units_refused():
    with pytest.raises(PZ.ZoneError, match="millimetres"):
        PZ.room_side_line(dict(ROOM_FACE, polyline_xyb=_arc_poly(2.80, scale=1000.0)), PART)
    with pytest.raises(PZ.ZoneError, match="metres"):
        PZ.room_side_line(ROOM_FACE, [{"ref": "p1", "length_m": 150.0}])


# ------------------------------------------------------------------------------------------------ R-T286-3 totals
def test_wedge_room_held_face_kept_apart():
    t = PZ.line_total([{"id": "f1", "status": "DRAWING-CONFIRMED", "quantity": 3.0},
                       {"id": "f2", "status": "DRAWING-CONFIRMED", "quantity": 2.2},
                       {"id": "f3-oblique", "status": "HELD", "quantity": None}])
    assert t["established"] == pytest.approx(5.2) and t["held"] == ["f3-oblique"] and not t["whole"]


@pytest.mark.parametrize("it", [{"id": "f3", "status": "HELD", "quantity": 0},
                                {"id": "f3", "status": "UNKNOWN", "quantity": 0.0},
                                {"id": "f3", "status": "DRAWING-CONFIRMED", "quantity": None},
                                {"id": "f3", "status": "OK", "quantity": 1.0}])
def test_held_as_zero_or_bad_status_refused(it):
    with pytest.raises(PZ.ZoneError):
        PZ.line_total([{"id": "f1", "status": "VERIFIED", "quantity": 3.0}, it])


# ------------------------------------------------------------------------------------------ committed Alsenan output
def test_committed_summary_consistent():
    s = json.loads((HERE / "summary_t286.json").read_text())
    p = s["pantry"]
    assert p["closure"]["closes"] and abs(p["closure"]["residual_m2"]) <= PZ.TOL_M2
    rc = p["doorway_zone"]["reclass"]
    assert rc["disposition"] == "TO_ROOM_FLOOR_WET" and rc["area_m2"] == pytest.approx(1.1, abs=1e-6)
    assert p["doorway_zone"]["outside_east_counter_m2"] < 0.001
    assert all(x > 0 for x in p["band_edge_lines_west_end_m_east_of_box"])
    assert 6.726 <= s["w03"]["room_side_m"] <= 6.738
    txt = (HERE / "summary_t286.json").read_text()
    assert not any(abs(float(t)) > 1000 for t in __import__("re").findall(r"-?\d+\.\d+", txt))
