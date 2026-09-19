"""E59 — two bounded faces of a planar subdivision cannot overlap.

The fixtures here are the regression test the walker never had. They are kept
after the production path moves to the free-space method, because the theorem
does not stop being true.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from engine.planar import (attach_holes, build_half_edges, resolve_unbounded,
                           walk_faces)
from engine.planar_falsifiers import (INV_AREA_RECONCILES, INV_EULER,
                                      INV_HALF_EDGE_COVERAGE,
                                      INV_NO_AMBIGUOUS_ROTATION,
                                      INV_NO_FACE_OVERLAP,
                                      INV_NO_UNNODED_CROSSING, PlanarFalsified,
                                      assert_planar, check_no_ambiguous_rotation,
                                      check_no_face_overlap,
                                      check_no_unnoded_crossing, falsify)
from engine.topology import WallPair
from engine.wall_graph import build
from engine.wall_noding import node_and_split


def pairs(lines):
    out = []
    for i, (axis, fixed, lo, hi) in enumerate(lines, 1):
        out.append(WallPair(f"WP-{i:03d}", axis, fixed - 1.0, fixed + 1.0, lo, hi))
    return out


def box(x0, y0, x1, y1):
    return [("H", y0, x0, x1), ("H", y1, x0, x1),
            ("V", x0, y0, y1), ("V", x1, y0, y1)]


def faces_of(lines):
    noded = node_and_split(build(pairs(lines)))
    hes = build_half_edges(noded)
    res = attach_holes(resolve_unbounded(walk_faces(hes)))
    return hes, res, noded


# --- the clean case ---------------------------------------------------------

def test_a_single_room_satisfies_every_invariant():
    hes, res, noded = faces_of(box(0, 0, 4000, 3000))
    rep = falsify(hes, res.faces, noded=noded)
    assert rep.holds, rep.record()["by_invariant"]
    assert "faces of a planar subdivision" in rep.record()["interpretation"]
    assert_planar(hes, res.faces, noded=noded)


def test_two_rooms_sharing_a_wall_satisfy_every_invariant():
    lines = box(0, 0, 4000, 3000) + box(4000, 0, 8000, 3000)
    hes, res, noded = faces_of(lines)
    assert falsify(hes, res.faces, noded=noded).holds


# --- D: the definitional invariant ------------------------------------------

@dataclass(frozen=True)
class Fake:
    face_id: str
    polygon_mm: tuple
    kind: str = "BOUNDED_FACE"
    planar_component_id: str = "PC-0001"
    half_edge_ids: tuple = ()


def test_two_overlapping_bounded_faces_are_refused_as_faces():
    """Faces are connected components of the plane minus the graph, and
    components are disjoint. This is definitional, not empirical."""
    a = Fake("F-A", ((0, 0), (4000, 0), (4000, 3000), (0, 3000)))
    b = Fake("F-B", ((2000, 0), (6000, 0), (6000, 3000), (2000, 3000)))
    got = check_no_face_overlap([a, b])
    assert len(got) == 1
    assert got[0].invariant == INV_NO_FACE_OVERLAP
    assert got[0].measure == pytest.approx(2000 * 3000)
    assert "DISJOINT" in got[0].detail


def test_faces_that_only_share_a_boundary_do_not_violate_it():
    a = Fake("F-A", ((0, 0), (4000, 0), (4000, 3000), (0, 3000)))
    b = Fake("F-B", ((4000, 0), (8000, 0), (8000, 3000), (4000, 3000)))
    assert check_no_face_overlap([a, b]) == []


def test_a_face_wholly_inside_another_still_violates_it():
    """The AR-00 case: a building boundary walked as a bounded face overlaps
    every room inside it."""
    outer = Fake("F-OUT", ((0, 0), (10000, 0), (10000, 10000), (0, 10000)))
    inner = Fake("F-IN", ((1000, 1000), (3000, 1000), (3000, 3000), (1000, 3000)))
    got = check_no_face_overlap([outer, inner])
    assert len(got) == 1
    assert got[0].measure == pytest.approx(2000 * 2000)


# --- F: the rotation system -------------------------------------------------

@dataclass(frozen=True)
class HE:
    half_edge_id: str
    origin_node: str
    target_node: str
    source_edge_id: str
    angle: float


def test_two_outgoing_half_edges_at_one_angle_are_an_ill_defined_rotation():
    """What a portal closure laid on its host wall's own centreline produces
    at a jamb, and what a duplicate band produces everywhere."""
    hes = {"a": HE("a", "N1", "N2", "E1", 0.0),
           "b": HE("b", "N1", "N3", "E2", 0.0),
           "c": HE("c", "N1", "N4", "E3", 1.57)}
    got = check_no_ambiguous_rotation(hes)
    assert len(got) == 1
    assert got[0].invariant == INV_NO_AMBIGUOUS_ROTATION
    assert got[0].nodes == ("N1",)
    assert "arbitrary" in got[0].detail


def test_distinct_angles_at_a_node_are_fine():
    hes = {"a": HE("a", "N1", "N2", "E1", 0.0),
           "b": HE("b", "N1", "N3", "E2", 1.57)}
    assert check_no_ambiguous_rotation(hes) == []


# --- E: crossings without a node --------------------------------------------

def test_a_crossing_with_no_node_is_not_a_planar_embedding():
    @dataclass(frozen=True)
    class E:
        edge_id: str
        axis: str
        centreline_mm: float
        start_mm: float
        end_mm: float

    @dataclass
    class G:
        edges: list = field(default_factory=list)
        nodes: list = field(default_factory=list)

    g = G(edges=[E("H1", "H", 5000.0, 0.0, 10000.0),
                 E("V1", "V", 5000.0, 0.0, 10000.0)])
    got = check_no_unnoded_crossing(g)
    assert len(got) == 1
    assert got[0].invariant == INV_NO_UNNODED_CROSSING
    assert "pass through each other" in got[0].detail


def test_a_crossing_with_a_node_present_is_fine():
    @dataclass(frozen=True)
    class E:
        edge_id: str
        axis: str
        centreline_mm: float
        start_mm: float
        end_mm: float

    @dataclass(frozen=True)
    class N:
        x_mm: float
        y_mm: float

    @dataclass
    class G:
        edges: list = field(default_factory=list)
        nodes: list = field(default_factory=list)

    g = G(edges=[E("H1", "H", 5000.0, 0.0, 10000.0),
                 E("V1", "V", 5000.0, 0.0, 10000.0)],
          nodes=[N(5000.0, 5000.0)])
    assert check_no_unnoded_crossing(g) == []


# --- the invariants are asserted, not merely available ----------------------

def test_assert_planar_raises_with_the_mathematical_interpretation():
    a = Fake("F-A", ((0, 0), (4000, 0), (4000, 3000), (0, 3000)))
    b = Fake("F-B", ((2000, 0), (6000, 0), (6000, 3000), (2000, 3000)))
    with pytest.raises(PlanarFalsified, match="not the faces of a planar"):
        assert_planar({}, [a, b])


def test_the_report_names_the_failing_invariants_by_identity():
    a = Fake("F-A", ((0, 0), (4000, 0), (4000, 3000), (0, 3000)))
    b = Fake("F-B", ((2000, 0), (6000, 0), (6000, 3000), (2000, 3000)))
    rep = falsify({}, [a, b])
    assert INV_NO_FACE_OVERLAP in rep.by_invariant()
    assert rep.for_faces("F-A")
    assert "CYCLES OF THE ABSTRACT GRAPH" in rep.record()["interpretation"]


def test_every_invariant_has_a_name_in_the_report():
    from engine.planar_falsifiers import INVARIANTS
    rep = falsify({}, [])
    assert set(rep.record()["invariants_checked"]) == set(INVARIANTS)
    assert INV_HALF_EDGE_COVERAGE in INVARIANTS
    assert INV_EULER in INVARIANTS
    assert INV_AREA_RECONCILES in INVARIANTS
