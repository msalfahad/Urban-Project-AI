"""T-061: room labels in no closed room face are HELD (engine/source/room_label_guard.py), against hand truth.

Hand plan (metres, not a client drawing): a 12 x 8 m single-line plan. Four closed faces:
    R1 (0..6, 0..4) BEDROOM        R2 (6..12, 0..4) Arabic kitchen 'مطبخ'
    R3 (0..6, 4..8) Arabic living 'صالة'   R4 (6..9, 4..8) Arabic bathroom 'حمام'
East of R4 an open COURTYARD (9..12, 4..8): its top wall stops at x = 11.70 and the east wall ends at (12, 8), so the
linework has exactly one open gap, 12.00 - 11.70 = 0.30 m. Labels planted:
    COURTYARD at (10.5, 6)   -> HELD ROOM_LABEL_NO_FACE; nearest gap 0.30 m; distance to the gap = to its end
                                (11.7, 8): sqrt(1.2^2 + 2.0^2) = 2.332381 m; closing that gap encloses the label
    'حديقة' (garden) at (15, 4) outside the building -> HELD ROOM_LABEL_NO_FACE; same gap, distance to (12, 8):
                                sqrt(3^2 + 4^2) = 5.000 m; closing it does NOT enclose the label
    CORRIDOR at (6, 2) on the R1 / R2 shared wall line -> HELD ROOM_LABEL_AMBIGUOUS, candidates R1 and R2
    '1:100' (not a room label) -> not guarded, counted
Expected: 4 IN_FACE (faces untouched), 3 HELD, 0 dropped. Variants: millimetres, rotated 37 degrees, mirrored, and
combinations; adversarial: units missing, no position, nested faces, overlapping faces, holes, unreadable face,
closed-polygon repeat vertex, no linework, closed linework, Arabic presentation forms, held compound.
"""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import room_label_guard as G                   # noqa: E402

FACES = [
    ("R1", [(0, 0), (6, 0), (6, 4), (0, 4)]),
    ("R2", [(6, 0), (12, 0), (12, 4), (6, 4)]),
    ("R3", [(0, 4), (6, 4), (6, 8), (0, 8)]),
    ("R4", [(6, 4), (9, 4), (9, 8), (6, 8)]),
]
SEGS = [
    ("S-bottom", (0, 0), (12, 0)), ("S-east", (12, 0), (12, 8)), ("S-west", (0, 0), (0, 8)),
    ("S-top-a", (0, 8), (9, 8)), ("S-top-b", (9, 8), (11.7, 8)),
    ("S-mid", (0, 4), (12, 4)), ("S-x6", (6, 0), (6, 8)), ("S-x9", (9, 4), (9, 8)),
]
LABELS = [
    ("L1", "BEDROOM", (3, 2)), ("L2", "مطبخ", (9, 2)), ("L3", "صالة", (3, 6)), ("L4", "حمام", (7.5, 6)),
    ("L5", "COURTYARD", (10.5, 6)), ("L6", "حديقة", (15, 4)), ("L7", "CORRIDOR", (6, 2)), ("L8", "1:100", (1, 1)),
]
IN = {"L1": "R1", "L2": "R2", "L3": "R3", "L4": "R4"}
HELD = {"L5": "ROOM_LABEL_NO_FACE", "L6": "ROOM_LABEL_NO_FACE", "L7": "ROOM_LABEL_AMBIGUOUS"}
GAP_M = 0.30
DIST_M = {"L5": math.hypot(1.2, 2.0), "L6": 5.0}
CLOSES = {"L5": True, "L6": False}


def _xf(p, scale, deg, mirror):
    x, y = p[0] * scale, p[1] * scale
    if mirror:
        x = -x
    a = math.radians(deg)
    return (x * math.cos(a) - y * math.sin(a) + 5000.0 * scale / 1000.0,
            x * math.sin(a) + y * math.cos(a) - 3000.0 * scale / 1000.0)


def _plan(scale=1.0, deg=0.0, mirror=False):
    f = lambda p: _xf(p, scale, deg, mirror)                       # noqa: E731
    faces = [{"face_id": i, "polygon": [f(p) for p in poly]} for i, poly in FACES]
    segs = [{"id": i, "a": f(a), "b": f(b)} for i, a, b in SEGS]
    labels = [{"id": i, "value": v, "x": f(p)[0], "y": f(p)[1]} for i, v, p in LABELS]
    return faces, labels, segs


VARIANTS = [
    pytest.param(1.0, 1.0, 0.0, False, id="m"),
    pytest.param(1000.0, 0.001, 0.0, False, id="mm"),
    pytest.param(1.0, 1.0, 37.0, False, id="m-rot37"),
    pytest.param(1.0, 1.0, 0.0, True, id="m-mirror"),
    pytest.param(1000.0, 0.001, 37.0, True, id="mm-rot37-mirror"),
]


@pytest.mark.parametrize("scale,unit_m,deg,mirror", VARIANTS)
def test_hand_plan_every_label_reported_once(scale, unit_m, deg, mirror):
    faces, labels, segs = _plan(scale, deg, mirror)
    before = copy.deepcopy(faces)
    out = G.guard(faces, labels, frame="GF", unit_m=unit_m, segments=segs)
    assert faces == before                                         # the measured faces are untouched
    by = {r["text_id"]: r for r in out["records"]}
    assert set(by) == set(IN) | set(HELD)                          # '1:100' is not a room label
    for tid, fid in IN.items():
        assert by[tid]["status"] == "IN_FACE" and by[tid]["face_id"] == fid
    for tid, reason in HELD.items():
        r = by[tid]
        assert r["status"] == "HELD" and r["reason"] == reason and r["area_m2"] is None
        assert r["frame"] == "GF" and r["area_status"] == "NOT_COMPUTED"
    assert sorted(by["L7"]["candidate_faces"]) == ["R1", "R2"]
    for tid in ("L5", "L6"):
        g = by[tid]["nearest_gap"]
        assert by[tid]["gap_status"] == "GAP_FOUND"
        assert g["size_m"] == pytest.approx(GAP_M, abs=1e-6)
        assert g["distance_m"] == pytest.approx(DIST_M[tid], abs=1e-6)
        assert sorted(g["segments"]) == ["S-east", "S-top-b"]
        assert g["closes_around_label"] is CLOSES[tid]
    assert by["L5"]["code"] == "GARDEN" and by["L6"]["code"] == "GARDEN" and by["L7"]["code"] == "CORRIDOR"
    s = out["summary"]
    assert (s["room_labels"], s["in_face"], s["held"], s["dropped"]) == (7, 4, 3, 0)
    assert s["held_by_reason"] == {"ROOM_LABEL_NO_FACE": 2, "ROOM_LABEL_AMBIGUOUS": 1, "ROOM_LABEL_NO_POSITION": 0}
    assert s["texts_not_room_labels"] == 1 and s["open_gaps"] == 1


def test_units_missing_keeps_geometry_but_converts_nothing():
    faces, labels, segs = _plan(1000.0, 37.0, False)
    out = G.guard(faces, labels, unit_m=None, segments=segs)
    by = {r["text_id"]: r for r in out["records"]}
    assert {t for t, r in by.items() if r["status"] == "HELD"} == set(HELD)
    g = by["L5"]["nearest_gap"]
    assert g["size_m"] is None and g["distance_m"] is None         # missing units never become metres
    assert g["size_du"] == pytest.approx(300.0, abs=1e-6)
    assert by["L5"]["unit_status"] == "UNITS_MISSING" and out["summary"]["unit_status"] == "UNITS_MISSING"


@pytest.mark.parametrize("bad", [0, -1.0, "mm"])
def test_bad_unit_is_refused(bad):
    with pytest.raises(ValueError):
        G.guard([], [], unit_m=bad)


def test_label_without_position_is_held_not_dropped():
    out = G.guard([{"face_id": "A", "polygon": [(0, 0), (4, 0), (4, 4), (0, 4)]}],
                  [{"id": "T", "value": "ROOF", "x": None, "y": 2.0}], unit_m=1.0)
    (r,) = out["records"]
    assert (r["status"], r["reason"], r["area_m2"]) == ("HELD", "ROOM_LABEL_NO_POSITION", None)


def test_nested_faces_take_the_innermost():
    outer = {"face_id": "HALL", "polygon": [(0, 0), (10, 0), (10, 10), (0, 10)]}
    inner = {"face_id": "WC", "polygon": [(2, 2), (4, 2), (4, 4), (2, 4)]}
    out = G.guard([outer, inner], [{"id": "T", "value": "BATHROOM", "x": 3, "y": 3}], unit_m=1.0)
    (r,) = out["records"]
    assert r["status"] == "IN_FACE" and r["face_id"] == "WC"


def test_overlapping_faces_that_do_not_nest_are_ambiguous():
    a = {"face_id": "A", "polygon": [(0, 0), (6, 0), (6, 4), (0, 4)]}
    b = {"face_id": "B", "polygon": [(4, 0), (10, 0), (10, 4), (4, 4)]}
    out = G.guard([a, b], [{"id": "T", "value": "STORE", "x": 5, "y": 2}], unit_m=1.0)
    (r,) = out["records"]
    assert r["reason"] == "ROOM_LABEL_AMBIGUOUS" and sorted(r["candidate_faces"]) == ["A", "B"]


def test_label_on_outer_wall_line_is_ambiguous():
    a = {"face_id": "A", "polygon": [(0, 0), (6, 0), (6, 4), (0, 4)]}
    out = G.guard([a], [{"id": "T", "value": "BALCONY", "x": 6.0, "y": 2.0}], unit_m=1.0)
    (r,) = out["records"]
    assert r["reason"] == "ROOM_LABEL_AMBIGUOUS" and r["candidate_faces"] == ["A"]


def test_label_in_a_hole_is_in_no_face():
    a = {"face_id": "A", "polygon": [(0, 0), (10, 0), (10, 10), (0, 10)],
         "hole_polygons": [[(3, 3), (7, 3), (7, 7), (3, 7)]]}
    out = G.guard([a], [{"id": "T", "value": "VOID", "x": 5, "y": 5}], unit_m=1.0)
    (r,) = out["records"]
    assert r["reason"] == "ROOM_LABEL_NO_FACE" and r["gap_status"] == "NO_LINEWORK_GIVEN" and r["nearest_gap"] is None


def test_unreadable_face_is_named_on_the_held_label():
    good = {"face_id": "A", "polygon": [(0, 0), (4, 0), (4, 4), (0, 4)]}
    bad = {"face_id": "Z", "polygon": [(10, 10), (12, 10)]}
    out = G.guard([good, bad], [{"id": "T", "value": "ROOF", "x": 11, "y": 11}], unit_m=1.0)
    (r,) = out["records"]
    assert r["reason"] == "ROOM_LABEL_NO_FACE" and r["unreadable_faces"] == ["Z"]
    assert out["summary"]["unreadable_faces"] == ["Z"]


def test_closed_polygon_with_repeated_first_vertex():
    a = {"face_id": "A", "polygon": [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)]}
    out = G.guard([a], [{"id": "T", "value": "BEDROOM", "x": 0.5, "y": 0.5}], unit_m=1.0)
    assert out["records"][0]["status"] == "IN_FACE"


def test_closed_linework_has_no_open_gap():
    segs = [{"id": i, "a": a, "b": b} for i, (a, b) in
            enumerate([((0, 0), (4, 0)), ((4, 0), (4, 4)), ((4, 4), (0, 4)), ((0, 4), (0, 0))])]
    out = G.guard([], [{"id": "T", "value": "ROOF", "x": 9, "y": 9}], unit_m=1.0, segments=segs)
    (r,) = out["records"]
    assert r["gap_status"] == "NO_OPEN_GAP_IN_LINEWORK" and r["nearest_gap"] is None


def test_presentation_forms_and_held_compound_are_guarded():
    labels = [{"id": "P", "value": "ﺣﻤﺎﻡ", "x": 50, "y": 50}, {"id": "C", "value": "غسيل سيارات", "x": 60, "y": 60},
              {"id": "N", "value": "N", "x": 1, "y": 1}]
    out = G.guard([], labels, unit_m=1.0)
    by = {r["text_id"]: r for r in out["records"]}
    assert by["P"]["code"] == "BATHROOM" and by["P"]["reason"] == "ROOM_LABEL_NO_FACE"
    assert by["C"]["code"] is None and by["C"]["vocab_status"] == "HELD_COMPOUND" and by["C"]["status"] == "HELD"
    assert "N" not in by and out["summary"]["texts_not_room_labels"] == 1


def test_empty_input():
    out = G.guard([], [])
    assert out["records"] == [] and out["summary"]["room_labels"] == 0 and out["summary"]["dropped"] == 0


def test_census_rows_carry_no_coordinates():
    faces, labels, segs = _plan()
    rows = G.census_rows(G.guard(faces, labels, frame="GF", unit_m=1.0, segments=segs))
    assert len(rows) == 3
    for row in rows:
        assert not {"x", "y", "polygon", "a", "b"} & set(row)
    assert {r["text_id"]: r["gap_closes_label"] for r in rows} == {"L5": True, "L6": False, "L7": None}
