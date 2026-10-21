"""engine/source/lintel_release_audit.py - synthetic known answers only (no project data)."""

from __future__ import annotations

import pytest

from engine.source import lintel_release_audit as LA


def test_straight_wall_reaches_the_cap():
    r = LA.bearing_reach([(0, 2000)], [(0, 2000)], cap=1200)
    assert r == {"available": 1200, "terminator": LA.REACH, "at": 1200}


def test_t_junction_stops_at_the_cross_walls_far_face():
    r = LA.bearing_reach([(0, 73.7)], [(0, 73.7)], [(223.7, True, True)], cap=1200)
    assert (r["available"], r["terminator"]) == (223.7, LA.T_JUNCTION)


def test_l_corner_and_cap_line():
    r = LA.bearing_reach([(0, 189.1)], [(0, 39.1)], [(189.1, False, True)], cap=1200)
    assert (r["available"], r["terminator"]) == (189.1, LA.L_CORNER)
    r = LA.bearing_reach([(0, 300)], [(0, 300)], [(300, False, False)], cap=1200)
    assert (r["available"], r["terminator"]) == (300, LA.WALL_END)      # a cap is not a cross wall


def test_crossing_wall_is_masonry_but_an_opening_is_not():
    r = LA.bearing_reach([(0, 73.3), (223.3, 1200)], [(0, 73.3), (223.3, 1200)], cap=1200)
    assert r["terminator"] == LA.REACH                                   # a 150 mm crossing
    r = LA.bearing_reach([(0, 100), (900, 1200)], [(0, 100), (900, 1200)], cap=1200)
    assert (r["available"], r["terminator"]) == (100, LA.WALL_END)       # an 800 mm gap is an opening
    r = LA.bearing_reach([(0, 100), (250, 1200)], [(0, 100)], cap=1200)
    assert r["available"] == 100 or r["terminator"] != LA.REACH         # only one face resumes: no crossing


def test_t_junction_with_continuing_wall_reaches_through():
    r = LA.bearing_reach([(0, 60), (220, 1200)], [(0, 60), (220, 1200)], cap=1200)
    assert r["terminator"] == LA.REACH


def test_column_ends_the_masonry():
    r = LA.bearing_reach([(0, 100)], [(0, 300)], [(300, True, False)], [(100, 300)], cap=1200)
    assert (r["available"], r["terminator"]) == (100, LA.COLUMN)
    r = LA.bearing_reach([(0, 500)], [(0, 500)], [(650, True, True)], [(450, 650)], cap=1200)
    assert (r["available"], r["terminator"]) == (450, LA.COLUMN)


def test_oblique_junction_is_not_verified():
    r = LA.bearing_reach([(0, 372.7)], [(0, 278.7)], oblique_at=[278.7, 372.7], cap=1200)
    assert r["terminator"] == LA.OBLIQUE_JUNCTION
    assert LA.classify_end(r["available"], r["terminator"], 400) == LA.BEARING_NOT_VERIFIED
    assert LA.classify_end(500, LA.OBLIQUE_JUNCTION, 400) == LA.MASONRY_OK


@pytest.mark.parametrize("avail,term,conn,exp", [
    (400, LA.T_JUNCTION, False, LA.MASONRY_OK), (399.9, LA.T_JUNCTION, False, LA.BEARING_SHORT),
    (100, LA.COLUMN, False, LA.COLUMN_CONNECTION_MISSING), (100, LA.COLUMN, True, LA.BEARING_SHORT),
    (1200, LA.REACH, False, LA.MASONRY_OK)])
def test_classify_end(avail, term, conn, exp):
    assert LA.classify_end(avail, term, 400, conn) == exp


def test_classify_lintel_precedence():
    assert LA.classify_lintel([LA.MASONRY_OK, LA.MASONRY_OK]) == LA.CONFIRMED
    assert LA.classify_lintel([LA.MASONRY_OK, LA.COLUMN_CONNECTION_MISSING]) == LA.BLOCKED_COLUMN
    assert LA.classify_lintel([LA.COLUMN_CONNECTION_MISSING, LA.BEARING_SHORT]) == LA.BLOCKED_BEARING
    assert LA.classify_lintel([LA.BEARING_NOT_VERIFIED, LA.MASONRY_OK]) == LA.BLOCKED_BEARING
    with pytest.raises(LA.LintelAuditError):
        LA.classify_lintel([])
    with pytest.raises(LA.LintelAuditError):
        LA.classify_end(100, LA.REACH, 0)


def test_stirrup_readings():
    c = LA.stirrup_counts(1600, 5, 800)
    assert c == {"EQUIVALENT_RATE": 8.0, "RATE_COUNT": 8, "SPACING_WITH_ENDS": 9, "CLEAR_SPAN_RATE": 4}
    c = LA.stirrup_counts(2100, 5)
    assert c["EQUIVALENT_RATE"] == pytest.approx(10.5) and c["RATE_COUNT"] == 11 and c["SPACING_WITH_ENDS"] == 12
    with pytest.raises(LA.LintelAuditError):
        LA.stirrup_counts(0, 5)


def test_one_owner_per_shared_volume():
    assert LA.assign_overlap("A", "B", {"A", "B"}) == "A"
    assert LA.assign_overlap("A", "B", {"B"}) == "B"
    assert LA.assign_overlap("B", "A", {"B"}) == "B"
    assert LA.assign_overlap("A", "B", set()) is None
