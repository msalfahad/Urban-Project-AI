"""A wall is continued across a gap only where the source says something spans it.

The previous rule bridged any gap no wider than the maximum opening span.  With a 3 m span that joins two walls
5 m apart at their far ends into one wall that was never built, and every quantity measured on it - its length,
its openings, its thickness subtotal - is then wrong in a way no total reveals, because the invented wall's area
is perfectly self-consistent.
"""

from __future__ import annotations

from engine.qs_core import invariants, openings as OP, synthetic as S

TOL, SPAN = S.TOL, S.MAX_OPENING_SPAN


def test_two_unrelated_walls_two_metres_apart_are_not_joined_into_one():
    bands = S.two_unrelated_walls_two_metres_apart()
    lines, gaps = OP.build_wall_lines(bands, TOL, SPAN, openings=[])
    assert len(lines) == 2, "a 2 m hole below the maximum span is not evidence of a wall"
    assert gaps[0]["RELATION"] == OP.GAP_NOT_BRIDGED_NO_EVIDENCE
    assert gaps[0]["GAP_M"] == 2.0 and gaps[0]["GAP_M"] < SPAN


def test_the_maximum_span_can_still_reject_a_join_it_cannot_prove():
    bands = S.two_unrelated_walls_two_metres_apart()
    _lines, gaps = OP.build_wall_lines(bands, TOL, 1.0, openings=[])
    assert gaps[0]["RELATION"] == OP.GAP_NOT_BRIDGED_TOO_WIDE


def test_a_confirmed_opening_in_the_gap_does_join_the_segments():
    bands, ops = S.two_segments_with_a_door_between_them()
    lines, gaps = OP.build_wall_lines(bands, TOL, SPAN, openings=ops)
    assert len(lines) == 1
    assert gaps[0]["RELATION"] == OP.GAP_BRIDGED_BY_CONFIRMED_OPENING
    assert lines[0].material_length == 8.1


def test_an_opening_too_small_to_explain_the_gap_does_not_join_it():
    """A 0.9 m door does not account for a 2 m hole, and the engine does not pretend that it does."""
    bands = S.two_unrelated_walls_two_metres_apart()
    small = S.opening("OP-SMALL", (3.0, 0.0, 3.9, 0.20), "X", 0.90, 2.10)
    lines, gaps = OP.build_wall_lines(bands, TOL, SPAN, openings=[small])
    assert len(lines) == 2
    assert gaps[0]["OPENING_OCCUPANCY"] < OP.GAP_OCCUPANCY


def test_continuation_geometry_over_the_gap_joins_the_segments():
    bands, lintels = S.a_gap_spanned_by_a_lintel()
    lines, gaps = OP.build_wall_lines(bands, TOL, SPAN, openings=[], continuation_geometry=lintels)
    assert len(lines) == 1
    assert gaps[0]["RELATION"] == OP.GAP_BRIDGED_BY_CONTINUATION_GEOMETRY


def test_the_source_declaring_two_segments_one_object_joins_them():
    bands = S.two_unrelated_walls_two_metres_apart()
    declared = [{"SEGMENTS": ["W-A", "W-B"], "REFERENCE": "CAD_ENTITY::4711"}]
    lines, gaps = OP.build_wall_lines(bands, TOL, SPAN, openings=[], cad_continuity=declared)
    assert len(lines) == 1
    assert gaps[0]["RELATION"] == OP.GAP_BRIDGED_BY_DECLARED_CAD_CONTINUITY
    assert gaps[0]["REFERENCE"] == "CAD_ENTITY::4711"


def test_the_invariant_catches_a_join_made_without_evidence():
    honest = OP.build_wall_lines(S.two_unrelated_walls_two_metres_apart(), TOL, SPAN, openings=[])[1]
    assert invariants.wall_continuity_is_proved_not_permitted(honest)["PASS"]
    smuggled = [dict(honest[0], BRIDGED=True, RELATION="BRIDGED_BECAUSE_IT_FITS_UNDER_THE_MAXIMUM_SPAN")]
    check = invariants.wall_continuity_is_proved_not_permitted(smuggled)
    assert not check["PASS"] and check["RESULT"]["BRIDGED_WITHOUT_EVIDENCE"]


def test_every_line_records_the_gaps_it_closed_and_why():
    bands, ops = S.two_segments_with_a_door_between_them()
    lines, _gaps = OP.build_wall_lines(bands, TOL, SPAN, openings=ops)
    closed = lines[0].evidence[0].detail["GAPS_CLOSED"]
    assert closed and closed[0]["OPENINGS"] == ["OP-D"]
