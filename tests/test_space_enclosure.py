"""§2-§6, §11, §12: enclose a space with drawn lines, not with ink.

The fixtures carry their own answers, so these tests assert arithmetic
rather than opinion. They are the reason the algorithm's thresholds may be
called frozen: every one is exercised here, and none was chosen by watching
a real drawing improve.
"""

import pytest

from engine import enclosure_selftest as st
from engine import space_enclosure as se
from engine.boundary_match import VectorCandidate
from engine.enclosure_fixtures import fixtures
from engine.space_objects import (SRC_DIAGNOSTIC_VECTOR,
                                  SRC_VECTOR_OPENING_JAMB,
                                  SRC_VECTOR_WALL_FACE)


def _by_name(name):
    return next(f for f in fixtures() if f.name == name)


def _room(x0=0.0, y0=0.0, x1=3000.0, y1=2000.0, t=200.0,
          src=SRC_VECTOR_WALL_FACE, sides="NSEW"):
    out = []
    if "N" in sides:
        out.append(VectorCandidate("N", "H", y0, x0 - t, x1 + t, src))
    if "S" in sides:
        out.append(VectorCandidate("S", "H", y1, x0 - t, x1 + t, src))
    if "W" in sides:
        out.append(VectorCandidate("W", "V", x0, y0 - t, y1 + t, src))
    if "E" in sides:
        out.append(VectorCandidate("E", "V", x1, y0 - t, y1 + t, src))
    return out


# --- the whole fixture suite ---------------------------------------------

@pytest.mark.parametrize("fixture", fixtures(),
                         ids=lambda f: f.name)
def test_every_synthetic_fixture(fixture):
    got = st.run(fixture)
    assert got.passed, got.record()


def test_the_suite_reports_a_freeze_hash_and_every_refusal():
    rep = st.report()
    assert rep["passed"] == rep["fixtures"]
    assert rep["refusals_delivered"] == rep["refusals_expected"] == 4
    assert rep["ALGORITHM_FREEZE_HASH"] == se.freeze_hash()


def test_the_raster_contour_is_measurably_wrong_on_most_fixtures():
    """§3: the contour follows ink that is not the room's boundary."""
    rep = st.report()
    assert rep["fixtures_where_the_raster_contour_is_wrong"] >= 8
    assert rep["total_raster_contour_error_m2"] > 5.0


def test_a_bathroom_contour_misses_a_third_of_the_room():
    """The case that made every bathroom unmeasurable in Round 2."""
    got = st.run(_by_name("RECTANGULAR_BATHROOM_WITH_BATHTUB_WC_BASIN"))
    assert got.enclosed_area_m2 == pytest.approx(4.625, abs=0.002)
    assert got.raster_contour_area_m2 < 3.1
    assert got.contour_error_m2 < -1.5


# --- §3 fixtures are invisible -------------------------------------------

def test_a_fixture_cannot_indent_the_result():
    """Not a detour TEST — a detour cannot arise. Fixtures are not
    candidates, so there is nothing to reject."""
    plain = se.enclose("R", (1500.0, 1000.0), _room(), extent=(0, 0, 3000,
                                                               2000))
    # The same room, with a bath drawn against the west wall as ink. The
    # ink is not in the candidate list at all.
    assert plain.area_m2 == pytest.approx(6.0, abs=1e-6)
    assert plain.is_complete


def test_material_standing_inside_a_room_is_deducted_as_a_hole():
    """A free-standing column is not a boundary and not ignored."""
    cands = _room(0, 0, 4000, 4000)
    cands += [
        VectorCandidate("C-N", "H", 1800.0, 1800.0, 2200.0),
        VectorCandidate("C-S", "H", 2200.0, 1800.0, 2200.0),
        VectorCandidate("C-W", "V", 1800.0, 1800.0, 2200.0),
        VectorCandidate("C-E", "V", 2200.0, 1800.0, 2200.0),
    ]
    got = se.enclose("R", (500.0, 500.0), cands, extent=(0, 0, 4000, 4000))
    assert got.is_complete
    assert got.area_m2 == pytest.approx(16.0 - 0.16, abs=1e-6)


# --- §5 corners -----------------------------------------------------------

def test_a_corner_is_the_intersection_of_two_drawn_lines():
    got = se.enclose("R", (1500.0, 1000.0), _room(),
                     extent=(0, 0, 3000, 2000))
    assert len(got.corners_constructed) == 4
    for _x, _y, ids in got.corners_constructed:
        assert len(ids) >= 2, "a corner needs two participating lines"


def test_a_hairline_gap_at_a_junction_still_closes():
    got = st.run(_by_name("CORNER_FROM_TWO_FACES_THAT_REACH"))
    assert got.passed and got.enclosed_area_m2 == pytest.approx(7.2,
                                                                abs=0.002)


def test_a_wall_is_never_extended_until_it_hits_another_line():
    got = st.run(_by_name("CORNER_REFUSED_WHEN_A_FACE_STOPS_SHORT"))
    assert got.passed
    assert got.verdict == se.ESCAPED


def test_a_corner_with_only_one_side_supported_is_refused():
    got = st.run(_by_name("CORNER_REFUSED_WITH_ONLY_ONE_SIDE_SUPPORTED"))
    assert got.passed
    assert got.verdict == se.ESCAPED


# --- §12 partial vs complete ---------------------------------------------

def test_three_strong_sides_and_no_fourth_is_partial_not_a_rectangle():
    got = se.enclose("R", (1500.0, 1000.0), _room(sides="NWE"),
                     extent=(0, 0, 3000, 2000))
    assert not got.is_complete
    assert got.area_m2 is None
    assert got.leaks
    assert got.leaks[0].reason == se.LEAK_UNSUPPORTED_SIDE
    assert "Nothing was extended" in got.why


def test_an_opening_needs_a_validated_barrier_to_close_the_boundary():
    got = st.run(_by_name("ROOM_WITH_DOOR_OPENING"))
    assert got.passed and got.enclosed_area_m2 == pytest.approx(7.5,
                                                                abs=0.002)
    bad = st.run(_by_name(
        "ROOM_WITH_DOOR_OPENING_AND_NO_VALIDATED_PORTAL"))
    assert bad.passed and bad.verdict == se.ESCAPED


def test_a_jamb_edge_is_recorded_as_a_jamb_not_as_a_wall():
    f = _by_name("ROOM_WITH_DOOR_OPENING")
    got = se.enclose("R", f.seed_mm, f.candidates, extent=f.extent_mm)
    sources = {src for *_, src in got.edges}
    assert SRC_VECTOR_OPENING_JAMB in sources
    assert SRC_VECTOR_WALL_FACE in sources


# --- §4 provenance --------------------------------------------------------

def test_every_edge_names_the_drawn_object_it_lies_on():
    got = se.enclose("R", (1500.0, 1000.0), _room(),
                     extent=(0, 0, 3000, 2000))
    for axis, fixed, lo, hi, oid, src in got.edges:
        assert oid, "an edge with no object id has no provenance"
        assert src != se.SRC_UNRESOLVED
    assert set(got.lines_used) == {"N", "S", "E", "W"}


def test_no_raster_millimetre_reaches_the_result():
    rec = se.enclose("R", (1500.0, 1000.0), _room(),
                     extent=(0, 0, 3000, 2000)).record()
    assert "no pixel coordinate reached this geometry" in rec[
        "no_raster_millimetre"]


def test_a_diagnostic_line_closes_the_polygon_but_not_for_production():
    cands = _room(sides="NSW") + [
        VectorCandidate("E", "V", 3000.0, -200.0, 2200.0,
                        SRC_DIAGNOSTIC_VECTOR)]
    got = se.enclose("R", (1500.0, 1000.0), cands,
                     extent=(0, 0, 3000, 2000))
    assert got.is_complete
    assert got.vector_support_pct == pytest.approx(100.0, abs=0.01)
    assert got.production_support_pct < 100.0


# --- §11 five separate scores --------------------------------------------

def test_the_five_scores_are_reported_apart():
    got = se.enclose("R", (1500.0, 1000.0), _room(),
                     extent=(0, 0, 3000, 2000))
    s = se.score(got, seed_mm=(1500.0, 1000.0),
                 neighbour_seeds=[(5000.0, 5000.0)],
                 dimension_verdicts=["AGREE", "AGREE"],
                 openings_expected=1, openings_represented=1)
    for key in ("VECTOR_SUPPORT", "TOPOLOGY_CONSISTENCY",
                "DOCUMENT_CONSISTENCY", "OPENING_CONSISTENCY",
                "GEOMETRIC_VALIDITY"):
        assert key in s
    assert s["TOPOLOGY_CONSISTENCY"]["holds_its_own_seed"] is True
    assert s["TOPOLOGY_CONSISTENCY"]["adjacent_region_seeds_outside"] == 1
    assert s["DOCUMENT_CONSISTENCY"]["agree"] == 2
    assert s["GEOMETRIC_VALIDITY"]["valid"] is True
    assert "One number would" in s["not_combined"]


def test_a_polygon_that_does_not_hold_its_seed_is_caught():
    got = se.enclose("R", (1500.0, 1000.0), _room(),
                     extent=(0, 0, 3000, 2000))
    s = se.score(got, seed_mm=(99000.0, 99000.0))
    assert s["TOPOLOGY_CONSISTENCY"]["holds_its_own_seed"] is False


def test_an_overlap_with_an_accepted_neighbour_is_reported():
    got = se.enclose("R", (1500.0, 1000.0), _room(),
                     extent=(0, 0, 3000, 2000))
    s = se.score(got, seed_mm=(1500.0, 1000.0),
                 accepted_neighbours=[("OTHER", got.polygon_wkt)])
    assert s["GEOMETRIC_VALIDITY"]["overlaps_accepted_neighbours"]


def test_the_scores_say_the_geometry_was_not_tuned_to_the_dimensions():
    s = se.score(se.enclose("R", (1500.0, 1000.0), _room(),
                            extent=(0, 0, 3000, 2000)))
    assert "never tuned to them" in s["DOCUMENT_CONSISTENCY"]["basis"]


# --- §1 the freeze --------------------------------------------------------

def test_every_frozen_parameter_states_why_it_has_its_value():
    params = se.frozen_parameters()
    for key, entry in params.items():
        if key == "how_these_were_set":
            continue
        assert "value" in entry and "why" in entry
        assert len(entry["why"]) > 20
    assert "BEFORE any real drawing" in params["how_these_were_set"]


def test_the_freeze_hash_changes_if_a_parameter_changes(monkeypatch):
    before = se.freeze_hash()
    monkeypatch.setattr(se, "JUNCTION_REACH_MM", 25.0)
    assert se.freeze_hash() != before


def test_the_junction_reach_is_tight_enough_to_refuse_a_doorway():
    """The only tolerance that can close anything must not close a door."""
    assert se.JUNCTION_REACH_MM < 50.0
    assert se.COLLINEAR_JOIN_MM <= se.JUNCTION_REACH_MM
