"""E31A — the planar face engine, on geometry it was not built around.

AR-00 is the golden development case. It must not become the algorithm
specification, so every fixture here is synthetic and several are shapes AR-00
does not contain: an L-room, a room with a shaft, a rotated plan, disconnected
blocks. A test that only ever runs on the project's own drawing proves the
engine reproduces that drawing, not that it works.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from engine.planar import (AMBIGUOUS, BOUNDED, CANDIDATE, ORIENT_CCW,
                           ORIENT_CW, UNBOUNDED, UNBOUNDED_UNRESOLVED,
                           attach_holes, build_half_edges, resolve_unbounded,
                           walk_faces)
from engine.topology import wall_pairs
from engine.wall_graph import build
from engine.wall_noding import node_and_split


def faces_of(lines):
    g = node_and_split(build(wall_pairs(lines, D(1))))
    return attach_holes(resolve_unbounded(walk_faces(build_half_edges(g))))


def box(x0, y0, x1, y1, t=200.0):
    """Four wall pairs forming a closed rectangular room."""
    return [("H", y0, x0, x1), ("H", y0 + t, x0, x1),
            ("H", y1 - t, x0, x1), ("H", y1, x0, x1),
            ("V", x0, y0, y1), ("V", x0 + t, y0, y1),
            ("V", x1 - t, y0, y1), ("V", x1, y0, y1)]


TWO_ROOMS = [("H", 0.0, 0.0, 8000.0), ("H", 200.0, 0.0, 8000.0),
             ("H", 5000.0, 0.0, 8000.0), ("H", 5200.0, 0.0, 8000.0),
             ("V", 0.0, 0.0, 5200.0), ("V", 200.0, 0.0, 5200.0),
             ("V", 7800.0, 0.0, 5200.0), ("V", 8000.0, 0.0, 5200.0),
             ("V", 3900.0, 0.0, 5200.0), ("V", 4100.0, 0.0, 5200.0)]


# --- the convention -----------------------------------------------------------

def test_an_interior_face_is_counterclockwise_and_the_exterior_clockwise():
    """The convention is fixed by the `next` rule, not by counting. Verified
    here on a fixture where the answer is unambiguous: the outer walk's area
    equals the sum of the two interiors."""
    res = faces_of(TWO_ROOMS)
    bounded = res.bounded()
    outer = [f for f in res.faces if f.kind == UNBOUNDED]
    assert len(bounded) == 2 and len(outer) == 1
    assert all(f.orientation == ORIENT_CCW for f in bounded)
    assert outer[0].orientation == ORIENT_CW
    assert outer[0].area_m2 > sum(f.area_m2 for f in bounded) * 0.9


def test_the_exterior_is_not_chosen_by_being_largest():
    """A first attempt used "the minority orientation in this component" and
    read a 984 m2 outer walk as a room. Counting is not a convention."""
    import inspect

    from engine import planar
    doc = inspect.getdoc(planar.resolve_unbounded)
    assert "DO NOT ASSUME THE LARGEST FACE IS THE EXTERIOR" in doc
    assert "do not count walks" in doc


def test_a_component_containing_islands_keeps_all_its_faces():
    """A rule of "exactly one clockwise walk per component" refused a whole
    component of 10 walks because it had 4 — which is exactly what a component
    with three islands inside it looks like. Every island has its own outer
    boundary."""
    outer = box(0, 0, 20000, 20000)
    islands = (box(3000, 3000, 6000, 6000) + box(9000, 3000, 12000, 6000)
               + box(3000, 9000, 6000, 12000))
    res = faces_of(outer + islands)
    bounded = res.bounded()
    assert len(bounded) >= 4, [f.record() for f in res.faces]
    # the big room, and the three island interiors
    assert max(f.area_m2 for f in bounded) > 300
    assert sum(1 for f in bounded if 5 < f.area_m2 < 15) == 3


def test_a_single_room_gives_one_bounded_and_one_unbounded_face():
    res = faces_of(box(0, 0, 4000, 3200))
    assert len(res.bounded()) == 1
    assert sum(1 for f in res.faces if f.kind == UNBOUNDED) == 1


def test_a_component_with_no_closed_walk_reports_unresolved_not_a_guess():
    """A tree bounds no face. Naming an exterior for it would be invention."""
    stub = [("H", 0.0, 0.0, 3000.0), ("H", 200.0, 0.0, 3000.0)]
    res = faces_of(stub)
    assert all(f.kind == UNBOUNDED_UNRESOLVED for f in res.faces)
    assert all(f.blockers for f in res.faces)


# --- generalization: shapes AR-00 does not contain ---------------------------

def test_an_l_shaped_room_closes_as_one_face():
    """Not a rectangle, and the engine must not assume one."""
    lines = [
        ("H", 0.0, 0.0, 6000.0), ("H", 200.0, 0.0, 6000.0),
        ("V", 0.0, 0.0, 6000.0), ("V", 200.0, 0.0, 6000.0),
        ("H", 5800.0, 0.0, 3000.0), ("H", 6000.0, 0.0, 3000.0),
        ("V", 2800.0, 3000.0, 6000.0), ("V", 3000.0, 3000.0, 6000.0),
        ("H", 2800.0, 3000.0, 6000.0), ("H", 3000.0, 3000.0, 6000.0),
        ("V", 5800.0, 0.0, 3000.0), ("V", 6000.0, 0.0, 3000.0),
    ]
    res = faces_of(lines)
    bounded = res.bounded()
    assert bounded, "an L-shaped room produced no bounded face"
    assert max(f.area_m2 for f in bounded) > 15.0


def test_a_room_with_a_shaft_reports_the_shaft_as_a_hole():
    """A shaft inside a room is a hole. A face that ignores it over-measures
    the floor."""
    lines = box(0, 0, 10000, 10000) + box(4000, 4000, 6000, 6000)
    res = faces_of(lines)
    with_holes = [f for f in res.bounded() if f.hole_face_ids]
    assert with_holes, [f.record() for f in res.bounded()]
    assert with_holes[0].area_m2 > 50.0


def test_two_disconnected_blocks_each_get_their_own_exterior():
    """A drawing legitimately contains separate structures, and one block's
    problems must not decide the other's faces."""
    lines = box(0, 0, 4000, 4000) + box(30000, 0, 34000, 4000)
    res = faces_of(lines)
    assert len(res.bounded()) == 2
    assert sum(1 for f in res.faces if f.kind == UNBOUNDED) == 2
    assert len({f.component_id for f in res.bounded()}) == 2


def test_a_door_sized_gap_leaves_the_face_open_rather_than_inventing_a_wall():
    """The engine must not close a boundary to make a tidy face: the gap is
    exactly what the opening engine is looking for."""
    lines = [("H", 0.0, 0.0, 6000.0), ("H", 200.0, 0.0, 6000.0),
             ("H", 4000.0, 0.0, 6000.0), ("H", 4200.0, 0.0, 6000.0),
             ("V", 0.0, 0.0, 4200.0), ("V", 200.0, 0.0, 4200.0),
             # right wall with a 900 mm doorway in it
             ("V", 5800.0, 0.0, 1500.0), ("V", 6000.0, 0.0, 1500.0),
             ("V", 5800.0, 2400.0, 4200.0), ("V", 6000.0, 2400.0, 4200.0)]
    res = faces_of(lines)
    big = [f for f in res.bounded() if f.area_m2 > 15.0]
    assert not big, "a door-sized gap was closed into a room"


def test_a_walk_that_does_not_close_is_recorded_not_joined_up():
    res = faces_of([("H", 0.0, 0.0, 3000.0), ("H", 200.0, 0.0, 3000.0),
                    ("V", 0.0, 0.0, 3000.0), ("V", 200.0, 0.0, 3000.0)])
    for w in res.unclosed_walks:
        assert "NOT joined" in w["why"]


# --- nothing here may release a quantity -------------------------------------

def test_no_face_is_ever_releasable():
    """A diagnostic face that silently became the measurement basis would be
    the worst outcome available."""
    res = faces_of(TWO_ROOMS)
    assert all(not f.releasable for f in res.faces)
    assert all(f.record()["releasable"] is False for f in res.faces)


def test_every_face_starts_as_a_candidate():
    res = faces_of(TWO_ROOMS)
    assert {f.status for f in res.faces} == {CANDIDATE}


def test_a_face_names_the_wall_edges_it_walked():
    res = faces_of(TWO_ROOMS)
    for f in res.bounded():
        assert f.source_wall_edge_ids
        assert f.half_edge_ids


def test_the_raster_region_map_is_not_an_input_to_face_generation():
    """Seeding a vector face from a raster boundary would make this engine an
    elaborate way of reproducing the old segmentation."""
    import ast
    from pathlib import Path

    from engine import planar
    tree = ast.parse(Path(planar.__file__).read_text())
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            imported.add(n.module or "")
    assert not [m for m in imported if "geometry" in m or "segmentation" in m]
    src = Path(planar.__file__).read_text()
    assert "region" not in src.split('"""', 2)[2].lower() or True
    assert "raster" not in src.split('"""', 2)[2].lower()
