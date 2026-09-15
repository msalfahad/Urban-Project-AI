"""§9, §10, §11: local priority-led matching, full decision records, and a
polygon built from vector sources only.
"""

import pytest

from engine import boundary_match as bm
from engine.region_boundary import BoundaryRun
from engine.space_objects import (
    SRC_DIAGNOSTIC_VECTOR, SRC_RASTER_ONLY, SRC_UNRESOLVED,
    SRC_VECTOR_OPENING_JAMB, SRC_VECTOR_WALL_FACE)


def _square_runs(fixed=0.0, size=5000.0, off=8.0):
    """A square traced ring, each run `off` mm inside the true faces."""
    return [
        BoundaryRun(1, "H", fixed + off, fixed, fixed + size, 100),
        BoundaryRun(2, "V", fixed + size - off, fixed, fixed + size, 100),
        BoundaryRun(3, "H", fixed + size - off, fixed, fixed + size, 100),
        BoundaryRun(4, "V", fixed + off, fixed, fixed + size, 100),
    ]


def _square_faces(fixed=0.0, size=5000.0, src=SRC_VECTOR_WALL_FACE):
    return [
        bm.VectorCandidate("W-N", "H", fixed, fixed, fixed + size, src),
        bm.VectorCandidate("W-E", "V", fixed + size, fixed, fixed + size,
                           src),
        bm.VectorCandidate("W-S", "H", fixed + size, fixed, fixed + size,
                           src),
        bm.VectorCandidate("W-W", "V", fixed, fixed, fixed + size, src),
    ]


def test_a_square_room_closes_on_its_drawn_faces():
    got = bm.match_region("RTR-1", _square_runs(), _square_faces())
    assert got.polygon_closed
    assert got.production_pct == 100.0
    # 5 m x 5 m from the FACES, not from the traced ring 8 mm inside them.
    assert got.area_m2 == pytest.approx(25.0, abs=1e-6)


def test_the_polygon_is_built_from_faces_not_from_the_traced_ring():
    """§11: the raster outline is never scaled, warped or offset."""
    runs = _square_runs(off=40.0)          # traced well inside the faces
    got = bm.match_region("RTR-1", runs, _square_faces())
    assert got.area_m2 == pytest.approx(25.0, abs=1e-6)
    # The traced ring would have measured 4.92 x 4.92 = 24.2 m².
    assert got.area_m2 > 24.9


def test_an_established_face_beats_a_nearer_diagnostic_one():
    """§9: priority-led, not global-nearest."""
    runs = _square_runs()
    faces = _square_faces()
    faces.append(bm.VectorCandidate(
        "DIAG-N", "H", 6.0, 0.0, 5000.0, SRC_DIAGNOSTIC_VECTOR))
    got = bm.match_region("RTR-1", runs, faces)
    north = got.intervals[0]
    assert north.chosen_object_id == "W-N"
    assert north.source_type == SRC_VECTOR_WALL_FACE
    assert ("DIAG-N", bm.REJ_PRIORITY) in north.rejected


def test_a_candidate_on_the_other_axis_is_never_chosen():
    runs = [BoundaryRun(1, "H", 8.0, 0.0, 5000.0, 100)]
    faces = [bm.VectorCandidate("V-LINE", "V", 8.0, 0.0, 5000.0)]
    got = bm.match_region("RTR-1", runs, faces)
    assert got.intervals[0].source_type == SRC_UNRESOLVED


def test_a_candidate_with_no_shared_extent_is_rejected():
    runs = [BoundaryRun(1, "H", 8.0, 0.0, 5000.0, 100)]
    faces = [bm.VectorCandidate("FAR", "H", 8.0, 90000.0, 95000.0)]
    got = bm.match_region("RTR-1", runs, faces)
    iv = got.intervals[0]
    assert iv.source_type == SRC_UNRESOLVED
    assert ("FAR", bm.REJ_SUPPORT) in iv.rejected


def test_a_candidate_outside_the_window_is_rejected_by_distance():
    runs = [BoundaryRun(1, "H", 8.0, 0.0, 5000.0, 100)]
    faces = [bm.VectorCandidate("FARY", "H", 900.0, 0.0, 5000.0)]
    got = bm.match_region("RTR-1", runs, faces)
    assert ("FARY", bm.REJ_WINDOW) in got.intervals[0].rejected


def test_every_interval_records_its_whole_decision():
    """§10: no black-box "snapped successfully"."""
    got = bm.match_region("RTR-1", _square_runs(), _square_faces())
    rec = got.record()["intervals"][0]
    assert rec["chosen_vector_object_id"] == "W-N"
    assert rec["distance_mm"] == 8.0
    assert rec["support_length_mm"] == 5000.0
    assert rec["orientation_difference_deg"] == 0.0
    assert "same axis" in rec["reason_chosen"]
    assert "candidate_vector_object_ids" in rec


def test_an_unmatched_run_leaves_the_candidate_partial_with_no_polygon():
    """§11: a polygon is never completed with a pixel coordinate."""
    runs = _square_runs()
    faces = _square_faces()[:3]            # the west face is missing
    got = bm.match_region("RTR-1", runs, faces)
    assert not got.polygon_closed
    assert got.area_m2 is None
    assert got.measurement_basis == ""
    assert len(got.unresolved_intervals) == 1
    assert "pixel coordinates" in got.why


def test_a_raster_only_interval_can_never_be_production_eligible():
    iv = bm.BoundaryInterval("BI-1", "H", 0.0, 0.0, 1000.0,
                             source_type=SRC_RASTER_ONLY)
    assert not iv.is_production_eligible


# --- fixture detours -----------------------------------------------------

def _detour_runs():
    """A square whose north edge detours around a fixture."""
    return [
        BoundaryRun(1, "H", 8.0, 0.0, 2000.0, 40),
        BoundaryRun(2, "V", 2000.0, 8.0, 600.0, 12),   # into the room
        BoundaryRun(3, "H", 600.0, 2000.0, 3000.0, 20),
        BoundaryRun(4, "V", 3000.0, 8.0, 600.0, 12),   # back out
        BoundaryRun(5, "H", 8.0, 3000.0, 5000.0, 40),
        BoundaryRun(6, "V", 4992.0, 8.0, 5000.0, 100),
        BoundaryRun(7, "H", 4992.0, 0.0, 5000.0, 100),
        BoundaryRun(8, "V", 8.0, 8.0, 5000.0, 100),
    ]


def test_a_fixture_detour_collapses_onto_the_line_drawn_across_it():
    faces = _square_faces()
    got = bm.match_region("RTR-1", _detour_runs(), faces)
    assert got.polygon_closed, got.why
    assert got.area_m2 == pytest.approx(25.0, abs=1e-6)
    north = [i for i in got.intervals
             if i.chosen_object_id == "W-N"][0]
    assert "fixture detour" in north.reason_chosen


def test_a_doorway_is_not_bridged_because_the_line_stops_there():
    """The discriminator: at an opening the drawn face has a GAP."""
    faces = [
        # The north face is drawn in two pieces with a 1 m doorway between.
        bm.VectorCandidate("W-N1", "H", 0.0, 0.0, 2000.0),
        bm.VectorCandidate("W-N2", "H", 0.0, 3000.0, 5000.0),
        bm.VectorCandidate("W-E", "V", 5000.0, 0.0, 5000.0),
        bm.VectorCandidate("W-S", "H", 5000.0, 0.0, 5000.0),
        bm.VectorCandidate("W-W", "V", 0.0, 0.0, 5000.0),
    ]
    got = bm.match_region("RTR-1", _detour_runs(), faces)
    assert not got.polygon_closed, (
        "bridged a doorway: the drawn face stops at the opening")


def test_bridging_can_be_switched_off():
    got = bm.match_region("RTR-1", _detour_runs(), _square_faces(),
                          bridge_fixture_detours=False)
    assert not got.polygon_closed


def test_line_coverage_needs_continuity_not_just_two_pieces():
    faces = [bm.VectorCandidate("A", "H", 0.0, 0.0, 1000.0),
             bm.VectorCandidate("B", "H", 0.0, 2000.0, 3000.0)]
    assert bm._line_covers(faces, "H", 0.0, 0.0, 900.0)
    assert not bm._line_covers(faces, "H", 0.0, 0.0, 2500.0)


# --- diagnosis ------------------------------------------------------------

def test_the_diagnosis_separates_nothing_drawn_from_out_of_window():
    runs = [BoundaryRun(1, "H", 8.0, 0.0, 5000.0, 100),
            BoundaryRun(2, "V", 8.0, 0.0, 5000.0, 100)]
    faces = [bm.VectorCandidate("NEAR_BUT_FAR", "H", 700.0, 0.0, 5000.0)]
    got = bm.match_region("RTR-1", runs, faces)
    rows = bm.diagnose_unresolved(runs, got, faces)
    by = {r["axis"]: r["reason"] for r in rows}
    assert by["H"] == bm.UNRES_TOO_FAR
    assert by["V"] == bm.UNRES_NOTHING_DRAWN
    s = bm.unresolved_summary([rows])
    assert s["by_reason"][bm.UNRES_TOO_FAR] == 1
    assert "tolerance" in s["what_this_decides"]


# --- candidate building ---------------------------------------------------

class _WP:
    def __init__(self):
        self.wall_band_id = "WB-0001"
        self.axis = "H"
        self.face_a_mm, self.face_b_mm = 0.0, 200.0
        self.start_mm, self.end_mm = 0.0, 5000.0
        self.face_a_intervals = ((0.0, 2000.0), (3000.0, 5000.0))
        self.face_b_intervals = ((0.0, 5000.0),)


def test_wall_faces_become_candidates_over_their_DRAWN_extent_only():
    got = bm.candidates_from_walls([_WP()])
    a = sorted([c for c in got if "-A" in c.object_id],
               key=lambda c: c.start_mm)
    assert [(c.start_mm, c.end_mm) for c in a] == [(0.0, 2000.0),
                                                   (3000.0, 5000.0)]
    assert all(c.fixed_mm == 0.0 for c in a)


class _Cap:
    cap_id, axis, at_mm, span_mm = "EC-1", "V", 2500.0, (0.0, 200.0)


def test_a_wall_end_cap_is_a_candidate_line():
    got = bm.candidates_from_caps([_Cap()])
    assert len(got) == 1
    assert got[0].axis == "V" and got[0].fixed_mm == 2500.0
    assert got[0].validation_class == "ESTABLISHED_END_CAP"


class _Barrier:
    portal_id, axis, geometry_status = "PT-1", "H", "GEOMETRY_CANDIDATE"

    @property
    def polygon(self):
        from shapely.geometry import box
        return box(1000.0, 0.0, 2000.0, 200.0)


def test_a_portal_barrier_yields_two_jamb_candidates():
    got = bm.candidates_from_portals([_Barrier()])
    assert len(got) == 2
    assert {c.source_type for c in got} == {SRC_VECTOR_OPENING_JAMB}


def test_the_sensitivity_sweep_reports_what_a_wider_window_costs():
    got = bm.sensitivity(_square_runs(), _square_faces())
    assert got["in_use_mm"] == bm.SEARCH_WINDOW_MM
    assert {r["search_window_mm"] for r in got["rows"]} >= {20.0, 200.0}
    assert "wrong room" in got["why_not_wider"]
