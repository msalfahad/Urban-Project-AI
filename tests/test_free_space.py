"""E60/E61 — walls are polygons, and a room is a hole in their union."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from engine.free_space import (BARRIER_ACCEPTED, BARRIER_REJECTED,
                               BARRIER_UNRESOLVED, CLEAR_INTERNAL_FINISH_FACE,
                               ENVELOPE_FROM_WALL_SOLID_HULL,
                               ENVELOPE_UNRESOLVED, EXTERNAL_FREE_SPACE,
                               GEOMETRY_VALID, OCCUPIABLE_SPACE_CANDIDATE,
                               SHAFT_CANDIDATE, TOPOLOGY_ONLY_NOT_MATERIAL,
                               WALL_CAVITY, BuildingEnvelope,
                               assert_non_overlapping, build_free_space,
                               envelope_from_wall_solid, partition_barriers)
from engine.space_boundary import CLEAR_INTERNAL_FINISH_FACE as CIFF
from engine.space_boundary import classify_gap
from engine.wall_solid import (GEOMETRY_REJECTED, GEOMETRY_VALID as WP_VALID,
                               NO_SECOND_FACE, ZERO_SEPARATION, build_solid,
                               wall_polygons)


@dataclass(frozen=True)
class Band:
    wall_band_id: str
    axis: str
    centreline_mm: float
    start_mm: float
    end_mm: float
    wall_face_separation_mm: float | None = 200.0
    separation_basis: str = "MEASURED_BETWEEN_TWO_DRAWN_FACES"
    source_object_ids: tuple = ()
    supporting_evidence: tuple = ("PAIRED_FACES",)
    validation_status: str = "VALIDATED"
    face_a_intervals: tuple = ()
    face_b_intervals: tuple = ()
    extensions: tuple = ()
    single: bool = False

    @property
    def face_a_ids(self):
        return (f"{self.wall_band_id}-A",)

    @property
    def face_b_ids(self):
        return () if self.single else (f"{self.wall_band_id}-B",)

    @property
    def face_a_mm(self):
        return self.centreline_mm - (self.wall_face_separation_mm or 0) / 2

    @property
    def face_b_mm(self):
        if self.single:
            return None
        return self.centreline_mm + (self.wall_face_separation_mm or 0) / 2


def rect(x0, y0, x1, y1, t=200.0, prefix="R"):
    """Four walls on the given CENTRELINES."""
    return [Band(f"{prefix}-N", "H", y0, x0 - t / 2, x1 + t / 2, t),
            Band(f"{prefix}-S", "H", y1, x0 - t / 2, x1 + t / 2, t),
            Band(f"{prefix}-W", "V", x0, y0 - t / 2, y1 + t / 2, t),
            Band(f"{prefix}-E", "V", x1, y0 - t / 2, y1 + t / 2, t)]


def spaces_of(bands, portals=()):
    wps = wall_polygons(bands, drawing_id="TEST", revision="R1")
    solid = build_solid(wps)
    bars = partition_barriers(list(portals), wps, drawing_id="TEST")
    env = envelope_from_wall_solid(solid, bars)
    cands, health = build_free_space(env, solid, bars, wps, run_id="T")
    return cands, health, wps, solid, bars, env


# --- wall polygons ----------------------------------------------------------

def test_a_wall_polygon_is_the_rectangle_between_the_two_drawn_faces():
    wp = wall_polygons([Band("WB-1", "H", 0.0, 0.0, 4000.0, 200.0)])[0]
    assert wp.geometry_status == WP_VALID
    assert wp.thickness_mm == pytest.approx(200.0)
    assert set(wp.ring) == {(0.0, -100.0), (4000.0, -100.0),
                            (4000.0, 100.0), (0.0, 100.0)}
    assert wp.source_face_ids == ("WB-1-A", "WB-1-B")
    assert wp.drawing_id == "TEST" or wp.drawing_id == ""


def test_a_single_face_band_gets_no_polygon_and_says_why():
    """NEVER MANUFACTURE A WALL THICKNESS from an assumed centreline."""
    wp = wall_polygons([Band("WB-1", "H", 0.0, 0.0, 4000.0, single=True)])[0]
    assert wp.geometry_status == GEOMETRY_REJECTED
    assert wp.unresolved_reason == NO_SECOND_FACE
    assert not wp.is_resolved
    assert "NEVER INVENT THE MISSING HALF" in wp.why


def test_two_coincident_faces_are_one_line_found_twice_not_a_wall():
    wp = wall_polygons([Band("WB-1", "H", 0.0, 0.0, 4000.0, 2.0)])[0]
    assert wp.unresolved_reason == ZERO_SEPARATION


def test_a_refused_band_is_a_row_never_a_silent_drop():
    wps = wall_polygons([Band("WB-1", "H", 0.0, 0.0, 4000.0, 200.0),
                         Band("WB-2", "H", 500.0, 0.0, 4000.0, single=True)])
    assert len(wps) == 2
    solid = build_solid(wps)
    assert solid.valid == 1
    assert len(solid.unresolved) == 1
    assert solid.unresolved[0]["wall_band_id"] == "WB-2"


def test_the_solid_keeps_a_mapping_back_to_its_source_bands():
    _, _, wps, solid, _, _ = spaces_of(rect(0, 0, 4000, 3000))
    assert solid.components == 1
    bands = next(iter(solid.source_of.values()))
    assert set(bands) == {"R-N", "R-S", "R-W", "R-E"}


# --- the room is a hole in the union ---------------------------------------

def test_one_room_measures_its_clear_internal_area_with_no_conversion():
    """Centreline 4.0 x 3.0 with 200 mm walls: clear internal is 3.8 x 2.8.
    No offset, no ownership, no corner correction, no mean thickness."""
    cands, health, _, _, _, env = spaces_of(rect(0, 0, 4000, 3000))
    rooms = [c for c in cands
             if c.geometry_role == OCCUPIABLE_SPACE_CANDIDATE]
    assert len(rooms) == 1
    r = rooms[0]
    assert r.measurement_basis == CLEAR_INTERNAL_FINISH_FACE
    assert r.area_m2 == pytest.approx(3.8 * 2.8, abs=1e-6)
    assert r.perimeter_m == pytest.approx(2 * (3.8 + 2.8), abs=1e-6)
    assert r.provenance["centreline_offset_used"] is False
    assert r.provenance["scalar_conversion_used"] is False
    assert r.provenance["bbox_derived_edges"] == 0
    assert r.provenance["raster_derived_edges"] == 0
    assert set(r.bounding_band_ids) == {"R-N", "R-S", "R-W", "R-E"}


def test_a_concave_room_needs_no_corner_handling_at_all():
    """The L-shape that broke the scalar formula. 18.84 m2, and this engine
    does not know what a corner is."""
    t = 200.0
    bands = [Band("L-N", "H", 0.0, -t / 2, 6000 + t / 2, t),
             Band("L-E1", "V", 6000.0, -t / 2, 2000 + t / 2, t),
             Band("L-NOTCH", "H", 2000.0, 3000 - t / 2, 6000 + t / 2, t),
             Band("L-E2", "V", 3000.0, 2000 - t / 2, 5000 + t / 2, t),
             Band("L-S", "H", 5000.0, -t / 2, 3000 + t / 2, t),
             Band("L-W", "V", 0.0, -t / 2, 5000 + t / 2, t)]
    cands, _, _, _, _, _ = spaces_of(bands)
    rooms = [c for c in cands
             if c.geometry_role == OCCUPIABLE_SPACE_CANDIDATE]
    assert len(rooms) == 1
    # x 100..5900 by y 100..1900, plus x 100..2900 by y 1900..4900
    assert rooms[0].area_m2 == pytest.approx(5.8 * 1.8 + 2.8 * 3.0, abs=1e-6)
    assert rooms[0].area_m2 == pytest.approx(18.84, abs=1e-6)


def test_mixed_wall_thicknesses_need_no_single_thickness():
    bands = [Band("M-N", "H", 0.0, -150.0, 4150.0, 100.0),
             Band("M-S", "H", 3000.0, -150.0, 4150.0, 300.0),
             Band("M-W", "V", 0.0, -150.0, 3150.0, 200.0),
             Band("M-E", "V", 4000.0, -150.0, 3150.0, 200.0)]
    cands, _, _, _, _, _ = spaces_of(bands)
    rooms = [c for c in cands
             if c.geometry_role == OCCUPIABLE_SPACE_CANDIDATE]
    # x 100..3900 = 3.8 ; y 50..2850 = 2.8
    assert rooms[0].area_m2 == pytest.approx(3.8 * 2.8, abs=1e-6)


def test_free_space_components_cannot_overlap():
    """The property the old planar path could not provide. Connected
    components of one geometry are disjoint by construction."""
    bands = rect(0, 0, 4000, 3000, prefix="A") + \
        rect(10000, 0, 14000, 3000, prefix="B")
    cands, _, _, _, _, _ = spaces_of(bands)
    assert_non_overlapping(cands)
    rooms = [c for c in cands
             if c.geometry_role == OCCUPIABLE_SPACE_CANDIDATE]
    assert len(rooms) == 2


# --- portal partition barriers ---------------------------------------------

def _door_room():
    t = 200.0
    return [Band("D-N", "H", 0.0, -t / 2, 4000 + t / 2, t),
            Band("D-S1", "H", 3000.0, -t / 2, 1500.0, t),
            Band("D-S2", "H", 3000.0, 2400.0, 4000 + t / 2, t),
            Band("D-W", "V", 0.0, -t / 2, 3000 + t / 2, t),
            Band("D-E", "V", 4000.0, -t / 2, 3000 + t / 2, t)]


def test_a_supported_portal_plugs_the_doorway_on_the_walls_own_faces():
    """§7 — no closure rule needed. The barrier spans the host wall's own
    thickness, so the boundary runs continuously along its drawn faces."""
    p = classify_gap("R", "south", "H", 3000.0, 1500.0, 2400.0,
                     bands_face_each_other=True, other_sides_complete=True,
                     host_wall_band_id="D-S1", closure_basis=CIFF)
    cands, health, _, _, bars, _ = spaces_of(_door_room(), [p])
    assert health["barriers_accepted"] == 1
    b = bars[0]
    assert b.status == BARRIER_ACCEPTED
    assert b.material_role == TOPOLOGY_ONLY_NOT_MATERIAL
    assert b.host_wall_band_id == "D-S1"
    assert b.opening_width_mm == pytest.approx(900.0)
    rooms = [c for c in cands
             if c.geometry_role == OCCUPIABLE_SPACE_CANDIDATE]
    assert len(rooms) == 1
    assert rooms[0].area_m2 == pytest.approx(3.8 * 2.8, abs=1e-6)
    assert "D-S1" in rooms[0].bounding_band_ids
    assert p.portal_id in rooms[0].bounding_portal_ids


def test_without_the_barrier_the_room_leaks_through_the_doorway():
    """Proof the barrier is doing the work: same walls, no portal."""
    cands, _, _, _, _, _ = spaces_of(_door_room())
    rooms = [c for c in cands
             if c.geometry_role == OCCUPIABLE_SPACE_CANDIDATE]
    assert not rooms or rooms[0].area_m2 != pytest.approx(3.8 * 2.8, abs=1e-3)


def test_an_open_plan_transition_gets_no_barrier():
    """One physical space. A barrier there would invent a room."""
    p = classify_gap("OPEN-01", "north", "H", 0.0, 0.0, 6053.0,
                     bands_face_each_other=True, other_sides_complete=False)
    bars = partition_barriers([p], wall_polygons(rect(0, 0, 4000, 3000)))
    assert bars[0].status == BARRIER_REJECTED
    assert not bars[0].ring
    assert "ONE physical space" in bars[0].why


def test_a_portal_with_unresolved_geometry_gets_no_barrier():
    p = classify_gap("X", "south", "H", 0.0, 0.0, 900.0,
                     bands_face_each_other=False, other_sides_complete=False)
    bars = partition_barriers([p], wall_polygons(_door_room()))
    assert bars[0].status == BARRIER_UNRESOLVED
    assert "jambs are not located" in bars[0].why


def test_a_portal_with_no_host_polygon_gets_no_barrier():
    p = classify_gap("R", "south", "H", 3000.0, 1500.0, 2400.0,
                     bands_face_each_other=True, other_sides_complete=True,
                     host_wall_band_id="NOT-A-BAND", closure_basis=CIFF)
    bars = partition_barriers([p], wall_polygons(_door_room()))
    assert bars[0].status == BARRIER_UNRESOLVED
    assert "no wall thickness for the barrier to span" in bars[0].why


# --- the envelope -----------------------------------------------------------

def test_an_unresolved_envelope_refuses_to_produce_free_space():
    """Do not invent a bounding rectangle."""
    env = BuildingEnvelope()
    assert env.basis == ENVELOPE_UNRESOLVED
    cands, health = build_free_space(env, build_solid([]), [], [])
    assert cands == []
    assert health["free_space"] is None
    assert "bounding rectangle" in health["why"]


def test_the_wall_solid_envelope_states_its_own_caveat():
    _, _, _, solid, _, env = spaces_of(rect(0, 0, 4000, 3000))
    assert env.basis == ENVELOPE_FROM_WALL_SOLID_HULL
    assert env.is_resolved
    assert "where MATERIAL is" in env.caveat


# --- geometry roles, not semantics -----------------------------------------

def test_a_narrow_void_is_a_cavity_not_a_room():
    t = 200.0
    bands = [Band("C-N", "H", 0.0, -t / 2, 4000 + t / 2, t),
             Band("C-S", "H", 600.0, -t / 2, 4000 + t / 2, t),
             Band("C-W", "V", 0.0, -t / 2, 600 + t / 2, t),
             Band("C-E", "V", 4000.0, -t / 2, 600 + t / 2, t)]
    cands, _, _, _, _, _ = spaces_of(bands)
    inner = [c for c in cands if not c.touches_envelope_boundary]
    assert inner and inner[0].geometry_role == WALL_CAVITY


def test_a_small_compact_void_is_a_shaft_candidate():
    cands, _, _, _, _, _ = spaces_of(rect(0, 0, 1700, 1700))
    inner = [c for c in cands if not c.touches_envelope_boundary]
    assert inner and inner[0].geometry_role == SHAFT_CANDIDATE


def test_a_geometry_role_never_names_a_room():
    from engine.free_space import GEOMETRY_ROLES
    for role in GEOMETRY_ROLES:
        assert "BATHROOM" not in role and "BEDROOM" not in role
        assert "STORE" not in role and "KITCHEN" not in role


def test_geometry_alone_never_releases_a_quantity():
    cands, _, _, _, _, _ = spaces_of(rect(0, 0, 4000, 3000))
    assert all(not c.releasable for c in cands)


def test_a_component_with_no_wall_support_is_ambiguous_not_valid():
    """A boundary not supported by drawn geometry is not a measurement."""
    cands, _, _, _, _, _ = spaces_of(rect(0, 0, 4000, 3000))
    for c in cands:
        if not c.bounding_band_ids:
            assert c.geometry_status != GEOMETRY_VALID
