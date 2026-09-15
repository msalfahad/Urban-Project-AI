"""E31E — the global space boundary graph, and faces walked on it."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from engine.space_boundary import (CLEAR_INTERNAL_FINISH_FACE,
                                   GEOMETRY_UNRESOLVED, HOST_WALL_OPENING,
                                   PHYSICAL_WALL, PortalCandidate,
                                   classify_gap)
from engine.space_graph import (MATERIAL_WALL_GRAPH, REFUSED_OPEN_PLAN,
                                SPACE_BOUNDARY_GRAPH, VIRTUAL_SEPARATION_MM,
                                assign_spaces, build_space_boundary_graph,
                                compare, containment, global_portals,
                                material_edges, portal_edges)
from engine.space_graph import walk as walk_space


@dataclass(frozen=True)
class Band:
    wall_band_id: str
    axis: str
    centreline_mm: float
    start_mm: float
    end_mm: float
    wall_face_separation_mm: float = 200.0
    source_object_ids: tuple = ()
    supporting_evidence: tuple = ()
    validation_status: str = "VALIDATED"
    face_a_ids: tuple = ("FA",)
    face_b_ids: tuple = ("FB",)

    @property
    def face_a_mm(self) -> float:
        return self.centreline_mm - self.wall_face_separation_mm / 2

    @property
    def face_b_mm(self) -> float:
        return self.centreline_mm + self.wall_face_separation_mm / 2


def room(prefix="R", x0=0.0, y0=0.0, x1=4000.0, y1=3000.0, door=None):
    """Four walls, optionally with a gap in the south one."""
    south = [Band(f"{prefix}-S", "H", y1, x0, x1)]
    if door:
        a, b = door
        south = [Band(f"{prefix}-S1", "H", y1, x0, a),
                 Band(f"{prefix}-S2", "H", y1, b, x1)]
    return [Band(f"{prefix}-N", "H", y0, x0, x1),
            Band(f"{prefix}-W", "V", x0, y0, y1),
            Band(f"{prefix}-E", "V", x1, y0, y1)] + south


# --- edges ------------------------------------------------------------------

def test_a_wall_edge_carries_every_length_and_they_coincide():
    e = material_edges(room())[0]
    assert e.boundary_type == PHYSICAL_WALL
    L = e.length_mm
    assert e.lengths.material_present_mm == L
    assert e.lengths.host_wall_gross_mm == L
    assert e.lengths.space_boundary_mm == L
    assert e.lengths.opening_mm == 0.0


def test_the_edge_id_is_the_band_id_not_a_position():
    """ORDER IS NEVER IDENTITY. A face must be able to name the band it walked."""
    ids = [e.edge_id for e in material_edges(room("BED"))]
    assert set(ids) == {"BED-N", "BED-W", "BED-E", "BED-S"}


def test_a_portal_closure_edge_has_no_thickness_because_it_has_no_material():
    p = classify_gap("X", "south", "H", 3000.0, 1500.0, 2400.0,
                     bands_face_each_other=True, other_sides_complete=True,
                     host_wall_band_id="R-S1",
                     closure_basis=CLEAR_INTERNAL_FINISH_FACE)
    kept, refused = portal_edges([p])
    assert not refused
    e = kept[0]
    assert e.boundary_type == HOST_WALL_OPENING
    assert e.separation_mm == VIRTUAL_SEPARATION_MM
    assert e.lengths.material_present_mm == 0.0
    assert e.lengths.opening_mm == pytest.approx(900.0)


def test_a_portal_whose_geometry_is_unresolved_gets_no_edge():
    """Existence is not enough. A boundary edge is a piece of geometry."""
    p = PortalCandidate("PT-1", "X", "south", "H", 0.0, 0.0, 900.0,
                        "PORTAL_VALIDATED",
                        existence_status="PORTAL_EXISTENCE_VALIDATED",
                        geometry_status=GEOMETRY_UNRESOLVED)
    kept, refused = portal_edges([p])
    assert not kept
    assert refused[0]["existence_status"] == "PORTAL_EXISTENCE_VALIDATED"


def test_an_open_plan_transition_is_refused_before_geometry_is_discussed():
    """No amount of geometry makes a zone boundary a physical wall."""
    p = classify_gap("OPEN-01", "north", "H", 0.0, 0.0, 6053.0,
                     bands_face_each_other=True, other_sides_complete=False)
    kept, refused = portal_edges([p])
    assert not kept
    assert refused[0]["refused"] == REFUSED_OPEN_PLAN


# --- the two graphs ---------------------------------------------------------

def test_a_room_with_a_door_closes_on_the_space_graph_and_not_the_material_one():
    """THE EXPERIMENT. Same walker, two inputs, and only the input differs."""
    bands = room(door=(1500.0, 2400.0))
    p = classify_gap("R", "south", "H", 3000.0, 1500.0, 2400.0,
                     bands_face_each_other=True, other_sides_complete=True,
                     host_wall_band_id="R-S1",
                     closure_basis=CLEAR_INTERNAL_FINISH_FACE)

    m_noded, m_index, _ = build_space_boundary_graph(bands, [])
    s_noded, s_index, _ = build_space_boundary_graph(bands, [p])

    m_res, m_faces = walk_space(m_noded, m_index,
                                graph_type=MATERIAL_WALL_GRAPH, run_id="T")
    s_res, s_faces = walk_space(s_noded, s_index,
                                graph_type=SPACE_BOUNDARY_GRAPH, run_id="T")
    assert not m_faces
    assert len(s_faces) == 1
    f = s_faces[0]
    assert f.portal_edge_ids
    assert f.graph_type == SPACE_BOUNDARY_GRAPH

    diff = compare(m_res, m_faces, s_res, s_faces)
    assert diff["faces_gained_by_closing_portals"] == 1
    assert diff["space_faces_depending_on_a_portal"] == 1


def test_a_face_keeps_its_four_lengths_apart():
    bands = room(door=(1500.0, 2400.0))
    p = classify_gap("R", "south", "H", 3000.0, 1500.0, 2400.0,
                     bands_face_each_other=True, other_sides_complete=True,
                     host_wall_band_id="R-S1",
                     closure_basis=CLEAR_INTERNAL_FINISH_FACE)
    noded, index, _ = build_space_boundary_graph(bands, [p])
    _, faces = walk_space(noded, index, graph_type=SPACE_BOUNDARY_GRAPH,
                          run_id="T")
    f = faces[0]
    assert f.opening_length_m == pytest.approx(0.9, abs=0.05)
    assert f.material_wall_length_m == pytest.approx(
        f.space_boundary_length_m - f.opening_length_m, abs=0.05)


def test_a_face_never_carries_a_room_name():
    """§5 — geometry first. A label must not decide where a boundary runs."""
    noded, index, _ = build_space_boundary_graph(room(), [])
    _, faces = walk_space(noded, index, graph_type=SPACE_BOUNDARY_GRAPH,
                          run_id="T")
    rec = faces[0].record()
    assert "room_type" not in rec and "space_id" not in rec
    assert rec["provenance"]["raster_used"] is False
    assert faces[0].releasable is False


def test_duplicate_edge_ids_are_refused_because_identity_is_the_join_key():
    from engine.space_graph import SpaceGraphError
    dup = room() + [Band("R-N", "H", 0.0, 0.0, 4000.0)]
    with pytest.raises(SpaceGraphError, match="share an id"):
        build_space_boundary_graph(dup, [])


# --- identity, established after geometry -----------------------------------

def _faces_for_two_rooms():
    bands = room("A", 0, 0, 4000, 3000) + room("B", 6000, 0, 10000, 3000)
    noded, index, _ = build_space_boundary_graph(bands, [])
    return walk_space(noded, index, graph_type=SPACE_BOUNDARY_GRAPH,
                      run_id="T")[1]


def test_a_face_holding_two_labelled_rooms_is_not_either_room_s_face():
    """Bounding-box overlap put every room inside the 989 m2 building face."""
    faces = _faces_for_two_rooms()
    regions = {1: {"space_id": "A-1", "centroid_mm": (2000.0, 1500.0),
                   "area_m2": 12.0, "bbox_mm": (0, 0, 4000, 3000)},
               2: {"space_id": "B-1", "centroid_mm": (8000.0, 1500.0),
                   "area_m2": 12.0, "bbox_mm": (6000, 0, 10000, 3000)}}
    got = assign_spaces(faces, regions)
    assert got["A-1"] != got["B-1"]

    held = {c["space_face_id"]: c for c in containment(faces, regions)}
    assert all(c["labelled_regions_contained"] <= 1 for c in held.values())


def test_a_region_no_face_encloses_gets_no_face_rather_than_the_nearest_one():
    faces = _faces_for_two_rooms()
    regions = {9: {"space_id": "OUTSIDE", "centroid_mm": (50000.0, 50000.0),
                   "area_m2": 1.0, "bbox_mm": (0, 0, 1, 1)}}
    assert assign_spaces(faces, regions) == {}


# --- portals found without a bounding box -----------------------------------

def test_the_sheet_detector_finds_a_gap_between_collinear_bands():
    bands = [Band("W1", "H", 3000.0, 0.0, 1500.0),
             Band("W2", "H", 3000.0, 2400.0, 4000.0)]
    got = global_portals(bands)
    assert len(got) == 1
    assert got[0].span_mm == pytest.approx(900.0)
    assert got[0].hosted.host_wall_band_id == "W1"


def test_a_swing_arc_lifts_a_gap_to_validated_geometry():
    """GEOMETRY + SYMBOL. The first portal validation available without the
    door schedule."""
    from engine.space_boundary import GEOMETRY_VALIDATED
    bands = [Band("W1", "H", 3000.0, 0.0, 1500.0),
             Band("W2", "H", 3000.0, 2400.0, 4000.0)]
    arcs = [{"path_id": "VP-1", "span_mm": 900.0,
             "centre_mm": (1950.0, 3100.0)}]
    got = global_portals(bands, arcs=arcs)
    assert got[0].geometry_status == GEOMETRY_VALIDATED
    assert "DOOR_SWING_ARC_NEARBY" in got[0].evidence


def test_the_sheet_detector_knows_nothing_about_rooms():
    """It walks wall lines. No bbox, no side names, no region ids."""
    bands = [Band("W1", "V", 100.0, 0.0, 1500.0),
             Band("W2", "V", 100.0, 2400.0, 4000.0)]
    got = global_portals(bands)
    assert got[0].space_id.startswith("GV")
    assert got[0].side == "line"
