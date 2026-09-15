"""E55 — the clear-internal polygon, measured rather than adjusted."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from engine.clear_internal import (CLEAR_INTERNAL_FINISH_FACE,
                                   OWNERSHIP_AMBIGUOUS, OWNERSHIP_UNRESOLVED,
                                   OWNERSHIP_VALIDATED, WALL_CENTRELINE_FACE,
                                   ClearInternalError)
from engine.clear_internal import build as build_clear
from engine.clear_internal import own_wall_side, summary
from engine.space_boundary import (CLEAR_INTERNAL_FINISH_FACE as CIFF,
                                   classify_gap)
from engine.space_graph import (SPACE_BOUNDARY_GRAPH,
                                build_space_boundary_graph)
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
    face_a_ids: tuple = ()
    face_b_ids: tuple = ()

    def __post_init__(self):
        object.__setattr__(self, "face_a_ids",
                           self.face_a_ids or (f"{self.wall_band_id}-A",))
        object.__setattr__(self, "face_b_ids",
                           self.face_b_ids or (f"{self.wall_band_id}-B",))

    @property
    def face_a_mm(self) -> float:
        return self.centreline_mm - self.wall_face_separation_mm / 2

    @property
    def face_b_mm(self) -> float:
        return self.centreline_mm + self.wall_face_separation_mm / 2


def rect(x0, y0, x1, y1, t=200.0, prefix="R"):
    return [Band(f"{prefix}-N", "H", y0, x0, x1, t),
            Band(f"{prefix}-S", "H", y1, x0, x1, t),
            Band(f"{prefix}-W", "V", x0, y0, y1, t),
            Band(f"{prefix}-E", "V", x1, y0, y1, t)]


def one_face(bands, portals=()):
    noded, index, _ = build_space_boundary_graph(bands, list(portals))
    res, faces = walk_space(noded, index, graph_type=SPACE_BOUNDARY_GRAPH,
                            run_id="T")
    assert faces, "the fixture produced no bounded face"
    return faces[0], index


# --- the basis is never converted -------------------------------------------

def test_a_uniform_rectangle_measures_its_clear_internal_area_exactly():
    """Centreline 4.0 x 3.0 with 200 mm walls: clear internal is 3.8 x 2.8."""
    face, index = one_face(rect(0, 0, 4000, 3000))
    p = build_clear("SF-1", face, index)
    assert p.geometry_basis == CLEAR_INTERNAL_FINISH_FACE
    assert p.is_complete
    assert p.area_m2 == pytest.approx(3.8 * 2.8, abs=1e-6)
    assert p.perimeter_m == pytest.approx(2 * (3.8 + 2.8), abs=1e-6)
    assert p.provenance["scalar_conversion_used"] is False


def test_the_scalar_formula_is_wrong_where_this_engine_is_right():
    """CENTRELINE_AREA - PERIMETER x HALF_THICKNESS has no corner term.

    On a 4.0 x 3.0 centreline rectangle it under-measures by exactly the four
    corner squares — 4 x 0.1 x 0.1 = 0.04 m2. The polygon does not need to
    know that; it just intersects its own offset lines.
    """
    face, index = one_face(rect(0, 0, 4000, 3000))
    exact = build_clear("SF-1", face, index).area_m2
    centre_area = 4.0 * 3.0
    centre_perim = 2 * (4.0 + 3.0)
    scalar = centre_area - centre_perim * 0.1
    assert exact == pytest.approx(10.64, abs=1e-6)
    assert scalar == pytest.approx(10.60, abs=1e-6)
    assert exact - scalar == pytest.approx(0.04, abs=1e-9)


def test_mixed_wall_thicknesses_each_offset_by_their_own_face():
    """There is no single thickness to take half of, so the scalar form has
    nothing correct to use. Each edge follows its own drawn face."""
    bands = [Band("M-N", "H", 0.0, 0.0, 4000.0, 100.0),
             Band("M-S", "H", 3000.0, 0.0, 4000.0, 300.0),
             Band("M-W", "V", 0.0, 0.0, 3000.0, 200.0),
             Band("M-E", "V", 4000.0, 0.0, 3000.0, 200.0)]
    face, index = one_face(bands)
    p = build_clear("SF-1", face, index)
    assert p.is_complete
    # x from 100 to 3900 = 3.8 ; y from 50 to 2850 = 2.8
    assert p.area_m2 == pytest.approx(3.8 * 2.8, abs=1e-6)


def test_a_concave_room_keeps_both_corner_signs():
    """An inside corner and an outside corner contribute with opposite sign.
    An L-shape is where the scalar adjustment loses the wrong amount."""
    bands = [Band("L-1", "H", 0.0, 0.0, 6000.0),          # north
             Band("L-2", "V", 6000.0, 0.0, 2000.0),       # east upper
             Band("L-3", "H", 2000.0, 3000.0, 6000.0),    # the notch
             Band("L-4", "V", 3000.0, 2000.0, 5000.0),    # notch side
             Band("L-5", "H", 5000.0, 0.0, 3000.0),       # south
             Band("L-6", "V", 0.0, 0.0, 5000.0)]          # west
    face, index = one_face(bands)
    p = build_clear("SF-1", face, index)
    assert p.is_complete
    assert face.area_m2 == pytest.approx(21.0, abs=1e-6)

    # The clear polygon is the union of x 100..5900 by y 100..1900 and
    # x 100..2900 by y 1900..4900 — every edge on its own drawn face.
    assert p.area_m2 == pytest.approx(5.8 * 1.8 + 2.8 * 3.0, abs=1e-6)
    assert p.area_m2 == pytest.approx(18.84, abs=1e-6)

    # The scalar form gives 18.80. It is out by exactly the corner terms this
    # L-shape has: five outside corners at +0.01 and one INSIDE corner at
    # -0.01 gives 0.04, and a formula with no corner term cannot produce that.
    scalar = 21.0 - p_centre_perimeter(face) * 0.1
    assert scalar == pytest.approx(18.80, abs=1e-6)
    assert p.area_m2 - scalar == pytest.approx(0.04, abs=1e-9)


def p_centre_perimeter(face) -> float:
    return face.perimeter_m


# --- ownership --------------------------------------------------------------

def test_the_room_facing_face_is_chosen_by_which_side_the_room_is_on():
    face, index = one_face(rect(0, 0, 4000, 3000))
    p = build_clear("SF-1", face, index)
    by_band = {o.wall_band_id: o for o in p.ownership}
    assert all(o.ownership_status == OWNERSHIP_VALIDATED
               for o in p.ownership)
    # the north wall's room-facing face is the SOUTH one (inside the room)
    north = by_band["R-N"]
    assert north.room_facing_mm == pytest.approx(100.0)
    assert north.opposite_mm == pytest.approx(-100.0)
    assert north.room_facing_face_id == "R-N-B"
    assert north.measurement_basis == CLEAR_INTERNAL_FINISH_FACE


def test_a_single_face_band_is_ambiguous_rather_than_assumed():
    """NEVER INVENT THE MISSING HALF. The line is known; which side of a wall
    it bounds is not."""
    @dataclass(frozen=True)
    class Edge:
        edge_id = "WB-1"
        axis = "H"
        centreline_mm = 0.0
        start_mm = 0.0
        end_mm = 4000.0
        face_a_mm = 0.0
        face_b_mm = None
        face_a_ids = ("S-1",)
        face_b_ids = ()
    own = own_wall_side("SF-1", Edge(), [(0, 0), (4000, 0), (4000, 3000),
                                         (0, 3000)])
    assert own.ownership_status == OWNERSHIP_AMBIGUOUS
    assert "NEVER INVENT THE MISSING HALF" in own.why


# --- portal closure on the same basis ---------------------------------------

def test_a_door_closes_on_the_clear_face_not_the_centreline():
    """§7 — closing a finish-face polygon to a centreline endpoint puts a step
    half a wall wide into the boundary at every door."""
    bands = [Band("D-N", "H", 0.0, 0.0, 4000.0),
             Band("D-S1", "H", 3000.0, 0.0, 1500.0),
             Band("D-S2", "H", 3000.0, 2400.0, 4000.0),
             Band("D-W", "V", 0.0, 0.0, 3000.0),
             Band("D-E", "V", 4000.0, 0.0, 3000.0)]
    portal = classify_gap("R", "south", "H", 3000.0, 1500.0, 2400.0,
                          bands_face_each_other=True,
                          other_sides_complete=True,
                          host_wall_band_id="D-S1", closure_basis=CIFF)
    face, index = one_face(bands, [portal])
    p = build_clear("SF-1", face, index)
    assert p.portal_closures
    c = p.portal_closures[0]
    assert c["closure_basis"] == CLEAR_INTERNAL_FINISH_FACE
    assert c["host_wall_band_id"] == "D-S1"
    # the closure line sits on the host wall's ROOM-FACING face (y = 2900),
    # not on its centreline (y = 3000)
    assert c["closure_line_mm"] == pytest.approx(2900.0)
    # and the room still measures as one clean rectangle
    assert p.area_m2 == pytest.approx(3.8 * 2.8, abs=1e-6)


def test_a_portal_with_no_host_leaves_the_boundary_unresolved():
    bands = [Band("N-N", "H", 0.0, 0.0, 4000.0),
             Band("N-S1", "H", 3000.0, 0.0, 1500.0),
             Band("N-S2", "H", 3000.0, 2400.0, 4000.0),
             Band("N-W", "V", 0.0, 0.0, 3000.0),
             Band("N-E", "V", 4000.0, 0.0, 3000.0)]
    portal = classify_gap("R", "south", "H", 3000.0, 1500.0, 2400.0,
                          bands_face_each_other=True,
                          other_sides_complete=True)   # no host named
    face, index = one_face(bands, [portal])
    p = build_clear("SF-1", face, index)
    assert not p.is_complete
    assert any("centreline endpoint" in u["why"] for u in p.unresolved_edges)


# --- the two geometries stay separate ---------------------------------------

def test_the_centreline_face_is_kept_and_never_silently_converted():
    face, index = one_face(rect(0, 0, 4000, 3000))
    p = build_clear("SF-1", face, index)
    assert face.area_m2 == pytest.approx(12.0, abs=1e-6)
    assert p.area_m2 == pytest.approx(10.64, abs=1e-6)
    assert WALL_CENTRELINE_FACE != p.geometry_basis
    assert p.provenance["centreline_face_id"] == face.space_face_id


def test_a_degenerate_face_is_refused_rather_than_offset():
    @dataclass(frozen=True)
    class Tiny:
        space_face_id = "SF-X"
        polygon_mm = ((0.0, 0.0), (1.0, 0.0))
        half_edge_ids = ()
        boundary_edge_ids = ()
        boundary_edges_in_order = ()
    with pytest.raises(ClearInternalError, match="three vertices"):
        build_clear("SF-X", Tiny(), {})


def test_the_summary_counts_what_was_refused():
    face, index = one_face(rect(0, 0, 4000, 3000))
    out = summary([build_clear("SF-1", face, index)])
    assert out["complete_clear_internal_polygons"] == 1
    assert out["geometry_basis"] == CLEAR_INTERNAL_FINISH_FACE
    assert out["ownership_by_status"][OWNERSHIP_VALIDATED] == 4
