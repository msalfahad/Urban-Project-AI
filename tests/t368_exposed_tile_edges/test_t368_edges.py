"""T-368: exposed wall-tile edges (B4-10, UP-CER-006 / 007). Non-Alsenan villa E368 with hand calculations, adverse
cases (mirror, rotation, units, missing band, both finishes summed, internal corner as exposed, edge under a frame,
door exposed without frame evidence), then the development-villa ledger pins (committed inputs only)."""

import importlib.util
import json
import math
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "research", "agents_t368")


def _load(name):
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load("t368_edge_rules")
A = _load("t368_alsenan")

OA = R.OA
B310 = R.Band(3.10, "fixture storey: floor-to-floor 3.95 - 0.60 - 0.15 - 0.10 (Q-48 A form)", OA)
B300 = R.Band(3.00, "fixture storey 3.00", OA)
BHELD = R.Band(None, "", R.HELD, "fixture: storey height not drawn")

# villa E368 bath: 2.40 x 1.80 m, a column 0.40 x 0.30 standing proud from the north wall (drawn in mm)
BATH_MM = [(0, 0), (2400, 0), (2400, 1800), (1400, 1800), (1400, 1500), (1000, 1500), (1000, 1800), (0, 1800)]


def _xform(pts, angle=0.0, mirror=False, scale=1.0):
    c, s = math.cos(angle), math.sin(angle)
    out = []
    for x, y in pts:
        x = -x if mirror else x
        out.append(((x * c - y * s) * scale, (x * s + y * c) * scale))
    return out


def _bath_edges(band=B310, door_frame="NOT_DRAWN"):
    ext, inn = R.corner_classes(BATH_MM)
    edges = R.corner_edges("B1", ext, inn, band, "L-E368-B1", "fixture outline")
    edges.append(R.opening_edge("B1", R.Opening("D1", "door", 0.80, 2.20, 0.0, door_frame, "fixture"), band,
                                "L-E368-B1"))
    edges.append(R.opening_edge("B1", R.Opening("W1", "window", 0.60, 2.40, 1.60, "FLUSH", "fixture: depth_in 0"),
                                band, "L-E368-B1"))
    edges.append(R.top_edge("B1", 9.0, band, "L-E368-B1", "fixture decor ceiling"))
    return edges


# ------------------------------------------------------------------------------------------- normal cases

def test_bath_corners_hand():
    assert R.corner_classes(BATH_MM) == (2, 6)          # two column arrises proud, six concave corners


@pytest.mark.parametrize("angle", [0.0, 0.5, math.pi / 2, 2.0])
@pytest.mark.parametrize("mirror", [False, True])
def test_corners_invariant_under_rotation_mirror_and_units(angle, mirror):
    assert R.corner_classes(_xform(BATH_MM, angle, mirror)) == (2, 6)
    assert R.corner_classes(_xform(BATH_MM, angle, mirror, 0.001)) == (2, 6)   # the same room in metres
    assert R.corner_classes(list(reversed(BATH_MM))) == (2, 6)                 # clockwise input


def test_bath_ledger_hand():
    edges = _bath_edges()
    tot = R.check_ledger(edges)
    assert tot["EXPOSED_m"] == pytest.approx(2 * 3.10)               # 6.20 m.l: column arrises only
    assert tot["by_type"] == {"EXTERNAL_CORNER": 6.2}
    door = [e for e in edges if e.edge_id == "B1#D1"][0]
    assert door.exposed == "HELD" and door.length_m is None
    assert door.range_m == (0.0, pytest.approx(2 * 2.20 + 0.80))      # 0 .. 5.20, frame detail not drawn
    win = [e for e in edges if e.edge_id == "B1#W1"][0]
    assert win.exposed == "NOT_EXPOSED" and win.etype == "UNDER_FRAME"
    assert win.length_m == pytest.approx(2 * (2.40 - 1.60) + 0.60 + 0.60)   # 2.80 listed, never exposed


def test_drawn_architrave_and_frameless_doorway():
    arch = R.opening_edge("B1", R.Opening("D1", "door", 0.8, 2.2, 0.0, "ARCHITRAVE", "detail 5"), B310, "L")
    assert arch.exposed == "NOT_EXPOSED"
    bare = R.opening_edge("B1", R.Opening("P1", "doorway", 0.9, 2.4, 0.0, "NONE", "drawn arris, no frame"), B310,
                          "L")
    assert bare.exposed == "EXPOSED" and bare.length_m == pytest.approx(2 * 2.4 + 0.9)


def test_open_pantry_ends_hand():
    edges = R.corner_edges("P1", 1, 3, B300, "L-E368-P1", "fixture")
    edges += R.end_edges("P1", 1, 1, B300, "L-E368-P1", "fixture")
    tot = R.check_ledger(edges)
    assert tot["EXPOSED_m"] == pytest.approx(9.0)
    assert tot["by_type"] == {"EXTERNAL_CORNER": 3.0, "WALL_END": 3.0, "FLAT_STOP": 3.0}


def test_finish_alternatives_never_summed():
    f = R.finish_alternatives(6.2)
    assert f["choice"] == "HELD"
    assert f["alternative_MITRED_45_DEGREE_EDGE"] == 6.2 and f["alternative_STEEL_EDGE_PROFILE"] == 6.2
    p = R.finish_alternatives(6.2, R.PROFILE)
    assert p[R.PROFILE] == 6.2 and p[R.MITRE] == 0.0
    assert R.refuse_summed_finishes(6.2, 2.0, 4.2)        # a split edge by edge is fine


def test_window_head_above_band_and_sill_on_floor():
    b = R.Band(2.60, "x", OA)
    assert R.opening_perimeter(R.Opening("W", "window", 1.0, 3.0, 1.0, "NOT_DRAWN"), b) == pytest.approx(
        2 * 1.6 + 1.0)                                    # head above the tile top: no head edge, sill edge kept
    assert R.opening_perimeter(R.Opening("W", "window", 1.0, 2.0, 0.0, "NOT_DRAWN"), b) == pytest.approx(
        2 * 2.0 + 1.0)                                    # floor-level window: no sill edge


# ------------------------------------------------------------------------------------------- adverse cases

def test_band_held_is_never_zero():
    edges = _bath_edges(BHELD)
    ext = [e for e in edges if e.etype == "EXTERNAL_CORNER"][0]
    assert ext.count == 2 and ext.length_m is None and ext.exposed == "HELD"
    tot = R.check_ledger(edges)
    assert tot["EXPOSED_m"] == 0.0 and tot["HELD_count"] == 3


def test_band_in_mm_refused():
    with pytest.raises(R.EdgeError):
        R.corner_edges("B1", 2, 6, R.Band(3100.0, "mm by mistake", OA), "L", "x")


def test_width_in_mm_refused():
    with pytest.raises(R.EdgeError):
        R.opening_perimeter(R.Opening("D", "door", 800.0, 2.2), B310)


def test_both_finishes_summed_refused():
    with pytest.raises(R.EdgeError):
        R.refuse_summed_finishes(6.2, 6.2, 0.1)    # 0.1 m of edge carries both finishes
    with pytest.raises(R.EdgeError):
        R.refuse_summed_finishes(6.2, 6.2, 6.2)


def test_internal_corner_counted_as_exposed_refused():
    e = R.Edge("B1#INT", "B1", "INTERNAL_CORNER", 6, 18.6, None, "EXPOSED", OA, "x", "L")
    with pytest.raises(R.EdgeError):
        R.check_ledger([e])


def test_edge_under_frame_counted_refused():
    e = R.Edge("B1#W1", "B1", "UNDER_FRAME", 1, 2.8, None, "EXPOSED", R.DC, "x", "L")
    with pytest.raises(R.EdgeError):
        R.check_ledger([e])


def test_door_exposed_without_frame_evidence_refused():
    e = R.Edge("B1#D1", "B1", "OPENING_DOOR", 1, 5.2, None, "EXPOSED", OA, "default", "L")
    with pytest.raises(R.EdgeError):
        R.check_ledger([e])


def test_held_edge_with_figure_refused_and_duplicate_and_no_line():
    with pytest.raises(R.EdgeError):
        R.check_ledger([R.Edge("x", "B1", "EXTERNAL_CORNER", 2, 0.0, None, "HELD", "HELD", "x", "L")])
    e = R.Edge("x", "B1", "EXTERNAL_CORNER", 2, 6.2, None, "EXPOSED", OA, "x", "L")
    with pytest.raises(R.EdgeError):
        R.check_ledger([e, e])
    with pytest.raises(R.EdgeError):
        R.check_ledger([R.Edge("y", "B1", "EXTERNAL_CORNER", 2, 6.2, None, "EXPOSED", OA, "x", "")])


def test_degenerate_polygon_and_unit_refused():
    with pytest.raises(R.EdgeError):
        R.corner_classes([(0, 0), (1, 0)])
    with pytest.raises(R.EdgeError):
        R.to_m(1, "ft")


# ------------------------------------------------------------------------------------------- development villa

def test_alsenan_rebuild_is_byte_identical():
    for name, text in A.outputs().items():
        with open(os.path.join(HERE, name), encoding="utf-8", newline="") as f:
            assert f.read() == text, name


def test_alsenan_totals_pinned():
    s = json.loads(A.outputs()["summary.json"])
    assert s["exposed_determinate_m"] == pytest.approx(38.95)
    assert s["exposed_by_type_m"] == {"EXTERNAL_CORNER": 24.35, "FLAT_STOP": 7.3, "WALL_END": 7.3}
    assert s["door_exposure_held_range_m"] == [0.0, pytest.approx(73.1)]
    assert s["finish"]["choice"] == "HELD"
    assert s["freelancer"]["rows"] == 0


def test_alsenan_every_room_bound_to_its_wall_tile_line():
    import csv
    lines = {r["rooms"]: r["line_id"] for r in csv.DictReader(open(
        os.path.join(ROOT, "research", "agents_t312", "LINE_SUMMARY_T312.csv"), encoding="utf-8"))}
    s = json.loads(A.outputs()["summary.json"])
    assert set(s["rooms"]) == set(A.CORNERS)
    for room, r in s["rooms"].items():
        if room == "GF-07":
            assert r["line_id"] == A.PANTRY_LINE
        else:
            assert r["line_id"] == lines[room], room


def test_alsenan_held_rooms_stay_held():
    edges = A.build()
    for e in edges:
        if e.room in ("GF-02", "GF-03", "GF-05", "GF-06", "GF-10", "GF-11") and e.count and e.exposed != \
                "NOT_EXPOSED":
            assert e.exposed == "HELD" and e.length_m is None, e.edge_id
    kitchen = [e for e in edges if e.edge_id == "GF-06#EXT"][0]
    assert kitchen.count == 4 and kitchen.length_m is None


def test_alsenan_windows_flush_never_exposed():
    for e in A.build():
        if e.edge_id.split("#")[1][:1] == "W" and e.edge_id.split("#")[1][1:2].isdigit():
            assert e.etype == "UNDER_FRAME" and e.exposed == "NOT_EXPOSED", e.edge_id


# ------------------------------------------------------------------------------------------- R-T368-6 (F-T368-2)

PANTRY_MM = [(0, 0), (3000, 0), (3000, 500), (1500, 500), (1500, 4500), (0, 4500)]   # closes on a counter (L-shape)
PANTRY_CLASSES = ["WALL", "COUNTER", "COUNTER", "COUNTER", "OPEN", "WALL"]


def test_counter_reflex_is_not_a_wall_corner():
    assert R.corner_classes(PANTRY_MM)[0] == 1                       # the bare polygon sees one reflex
    ext, inn, other = R.wall_corner_classes(PANTRY_MM, PANTRY_CLASSES)
    assert ext == 0 and other >= 1                                   # it is a counter end, not a tile arris


@pytest.mark.parametrize("mirror", [False, True])
def test_wall_corner_classes_on_the_bath(mirror):
    pts = _xform(BATH_MM, 0.7, mirror)
    classes = ["WALL", "WALL", "WALL", "COLUMN", "COLUMN", "COLUMN", "WALL", "WALL"]
    assert R.wall_corner_classes(pts, classes)[:2] == (2, 6)


def test_wall_corner_classes_needs_one_class_per_edge():
    with pytest.raises(R.EdgeError):
        R.wall_corner_classes(BATH_MM, ["WALL"] * 3)
