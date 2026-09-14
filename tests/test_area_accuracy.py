"""E53 — per-room accuracy as a distribution, never as one project number."""

from __future__ import annotations

import pytest

from engine.area_accuracy import (ADJ_HALF_THICKNESS, CLEAR_INTERNAL,
                                  NOT_AVAILABLE, SOURCE_PRINTED, SOURCE_RASTER,
                                  SOURCE_SITE, WALL_CENTRELINE, RoomAccuracy,
                                  distribution)


def r(sid, vec, ref, **kw):
    return RoomAccuracy(sid, f"SF-{sid}", "SPACE_BOUNDARY_LENGTH",
                        vector_area_m2=vec, raster_area_m2=ref,
                        vector_basis=CLEAR_INTERNAL,
                        reference_basis=CLEAR_INTERNAL, **kw)


def test_over_and_under_measurements_cancel_in_a_total():
    """The whole reason a project percentage is not evidence of accuracy."""
    rooms = [r("A", 12.0, 10.0), r("B", 8.0, 10.0)]
    d = distribution(rooms)
    assert d["secondary_total_diagnostic"]["total_pct"] == 0.0
    assert d["median_abs_pct"] == 20.0


def test_the_total_is_labelled_secondary_and_says_why():
    d = distribution([r("A", 12.0, 10.0)])
    assert "SECONDARY" in d["secondary_total_diagnostic"]["why"]
    assert "cancel" in d["secondary_total_diagnostic"]["why"]


def test_no_acceptance_threshold_is_defined_from_one_project():
    d = distribution([r("A", 10.1, 10.0)])
    assert d["acceptance_threshold"] is None
    assert "chosen to pass" in d["acceptance_note"]


def test_the_worst_room_is_named_not_averaged_away():
    rooms = [r("A", 10.1, 10.0), r("B", 20.0, 10.0), r("C", 10.2, 10.0)]
    d = distribution(rooms)
    assert d["worst_room"]["space_id"] == "B"
    assert d["max_abs_pct"] == 100.0


def test_a_room_with_no_face_is_a_row_not_a_deletion():
    """Dropping it would remove it from the average along with the table."""
    rooms = [r("A", 10.0, 10.0), r("B", None, 10.0)]
    d = distribution(rooms)
    assert d["rooms_with_a_vector_face"] == 1
    assert d["rooms_compared"] == 1


def test_a_room_with_no_reference_at_all_is_counted_as_such():
    room = RoomAccuracy("X", "SF-X", "B", vector_area_m2=10.0)
    assert room.best_reference == NOT_AVAILABLE
    assert distribution([room])["rooms_without_any_reference"] == 1


def test_the_strongest_reference_present_is_the_headline():
    room = RoomAccuracy("X", "SF-X", "B", vector_area_m2=10.0,
                        raster_area_m2=9.0, printed_area_m2=9.5,
                        site_area_m2=9.8, vector_basis=CLEAR_INTERNAL,
                        reference_basis=CLEAR_INTERNAL)
    assert room.best_reference == SOURCE_SITE
    assert room.headline_abs_pct == pytest.approx(2.04, abs=0.01)


# --- never compare unlike bases ---------------------------------------------

def test_a_centreline_area_is_not_compared_against_a_clear_internal_one():
    """A planar face walks wall centrelines; a raster region is the clear
    opening. On a 5.5 m bedroom the difference is ~10% of the area."""
    raw = RoomAccuracy("BED-03", "SF-2", "B", vector_area_m2=33.285,
                       vector_perimeter_m=28.299, raster_area_m2=30.119,
                       vector_basis=WALL_CENTRELINE,
                       reference_basis=CLEAR_INTERNAL)
    assert not raw.bases_match
    adjusted = RoomAccuracy(
        "BED-03", "SF-2", "B", vector_area_m2=33.285,
        vector_perimeter_m=28.299, raster_area_m2=30.119,
        vector_basis=WALL_CENTRELINE, reference_basis=CLEAR_INTERNAL,
        vector_area_basis_adjusted_m2=30.969, basis_adjustment_m2=2.316,
        basis_adjustment_method=ADJ_HALF_THICKNESS)
    assert adjusted.bases_match
    # the raw comparison would have read 10.5% error; the real figure is 2.8%
    assert raw.vs_raster[1] == pytest.approx(10.51, abs=0.05)
    assert adjusted.vs_raster[1] == pytest.approx(2.82, abs=0.05)


def test_the_report_counts_rooms_compared_on_unlike_bases():
    rooms = [RoomAccuracy("X", "SF-X", "B", vector_area_m2=10.0,
                          raster_area_m2=9.0, vector_basis=WALL_CENTRELINE,
                          reference_basis=CLEAR_INTERNAL)]
    assert distribution(rooms)["rooms_compared_on_unlike_bases"] == 1
