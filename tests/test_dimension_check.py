"""§18: two instruments, one question, and never an average.

What is compared is the room's CLEAR EXTENT between opposite matched faces
— which is what a dimension printed on a plan actually dimensions. An
earlier version compared each matched interval's own length and produced
137 "material disagreements" on AR-00 that were entirely an artefact of the
pairing.
"""

import pytest

from engine import dimension_check as dc
from engine.document_observations import (
    GLYPH_OUTLINE, ObservationError, PrintedDimensionObservation,
    USE_FOR_IDENTITY)
from engine.space_objects import (BoundaryInterval, MeasuredSpaceCandidate,
                                  SRC_UNRESOLVED, SRC_VECTOR_WALL_FACE)


def _obs(oid, value, anchor, orientation="HORIZONTAL"):
    return PrintedDimensionObservation(
        observation_id=oid, raw_text=str(int(value)), parsed_value_mm=value,
        unit_as_printed="mm", orientation=orientation, anchor_mm=anchor,
        text_source=GLYPH_OUTLINE, confidence=0.95)


def _room(width=3850.0, depth=2500.0, src=SRC_VECTOR_WALL_FACE):
    """A rectangular room whose four faces are all matched."""
    ivs = (
        BoundaryInterval("BI-N", "H", 0.0, 0.0, width, source_type=src),
        BoundaryInterval("BI-S", "H", depth, 0.0, width, source_type=src),
        BoundaryInterval("BI-W", "V", 0.0, 0.0, depth, source_type=src),
        BoundaryInterval("BI-E", "V", width, 0.0, depth, source_type=src),
    )
    return MeasuredSpaceCandidate(
        candidate_id="MSC-1", region_id="RTR-1", intervals=ivs,
        area_m2=width * depth / 1e6,
        measurement_basis="CLEAR_INTERNAL_FINISH_FACE", polygon_closed=True)


def _split_side_room(width=3850.0, depth=2500.0):
    """The same room with its north side drawn as THREE intervals.

    The case that broke the old comparison: each piece is ~1283 mm, and
    comparing the printed 3850 against each of them looked like three
    material disagreements.
    """
    src = SRC_VECTOR_WALL_FACE
    third = width / 3.0
    ivs = tuple(
        BoundaryInterval(f"BI-N{k}", "H", 0.0, k * third, (k + 1) * third,
                         source_type=src) for k in range(3))
    ivs += (
        BoundaryInterval("BI-S", "H", depth, 0.0, width, source_type=src),
        BoundaryInterval("BI-W", "V", 0.0, 0.0, depth, source_type=src),
        BoundaryInterval("BI-E", "V", width, 0.0, depth, source_type=src),
    )
    return MeasuredSpaceCandidate(
        candidate_id="MSC-2", region_id="RTR-2", intervals=ivs,
        area_m2=width * depth / 1e6,
        measurement_basis="CLEAR_INTERNAL_FINISH_FACE", polygon_closed=True)


# --- the extents ----------------------------------------------------------

def test_the_clear_extents_come_from_opposite_matched_faces():
    got = dc.clear_extents(_room(3850.0, 2500.0))
    assert got["width"]["value_mm"] == 3850.0
    assert got["depth"]["value_mm"] == 2500.0


def test_a_side_drawn_in_three_pieces_still_gives_one_extent():
    got = dc.clear_extents(_split_side_room(3850.0, 2500.0))
    assert got["width"]["value_mm"] == 3850.0
    assert got["depth"]["value_mm"] == 2500.0


def test_one_face_on_an_axis_gives_no_extent_on_that_axis():
    iv = BoundaryInterval("BI-N", "H", 0.0, 0.0, 3850.0,
                          source_type=SRC_VECTOR_WALL_FACE)
    cand = MeasuredSpaceCandidate("MSC-3", "RTR-3", intervals=(iv,))
    assert dc.clear_extents(cand) == {}


def test_unmatched_faces_do_not_contribute_an_extent():
    got = dc.clear_extents(_room(src=SRC_UNRESOLVED))
    assert got == {}


# --- the comparison -------------------------------------------------------

def test_a_printed_value_matching_the_clear_extent_agrees():
    rows = dc.compare_extents(
        _room(3850.0, 2500.0),
        [_obs("DO-1", 3850.0, (1900.0, 1200.0), "HORIZONTAL")])
    width = [r for r in rows if r.subject == "width"][0]
    assert width.verdict == dc.AGREE
    assert width.printed_mm == 3850.0
    assert not width.blocks_release


def test_a_split_side_no_longer_manufactures_disagreements():
    """The regression this rewrite exists for."""
    rows = dc.compare_extents(
        _split_side_room(3850.0, 2500.0),
        [_obs("DO-1", 3850.0, (1900.0, 1200.0), "HORIZONTAL")])
    assert [r.verdict for r in rows if r.subject == "width"] == [dc.AGREE]
    assert not any(r.verdict == dc.DISAGREE for r in rows)


def test_a_small_difference_still_agrees():
    rows = dc.compare_extents(
        _room(3871.0, 2500.0),
        [_obs("DO-1", 3850.0, (1900.0, 1200.0), "HORIZONTAL")])
    width = [r for r in rows if r.subject == "width"][0]
    assert width.verdict == dc.AGREE
    assert width.difference_mm == pytest.approx(-21.0)


def test_a_disagreement_needs_an_unambiguous_pairing():
    """Two candidate strings and no agreement is AMBIGUOUS, not DISAGREE.

    On AR-00 BTH-01's depth was paired against the 2350 belonging to the
    dressing room beside it, and reported as a material disagreement.
    """
    rows = dc.compare_extents(
        _room(3600.0, 2500.0),
        [_obs("DO-1", 3850.0, (1800.0, 1200.0)),
         _obs("DO-2", 2350.0, (1810.0, 1210.0))])
    width = [r for r in rows if r.subject == "width"][0]
    assert width.verdict == dc.AMBIGUOUS
    assert not width.blocks_release
    assert "not established" in width.why


def test_a_near_miss_beyond_tolerance_disagrees_and_blocks_release():
    rows = dc.compare_extents(
        _room(3600.0, 2500.0),
        [_obs("DO-1", 3850.0, (1800.0, 1200.0), "HORIZONTAL")])
    width = [r for r in rows if r.subject == "width"][0]
    assert width.verdict == dc.DISAGREE
    assert width.blocks_release
    assert "nobody yet knows which" in width.why


def test_a_dimension_nowhere_near_the_extent_is_ambiguous_not_a_disagreement():
    """A printed 6400 beside a 2500 room dimensions something else."""
    rows = dc.compare_extents(
        _room(2500.0, 2500.0),
        [_obs("DO-1", 6400.0, (1200.0, 1200.0), "HORIZONTAL")])
    width = [r for r in rows if r.subject == "width"][0]
    assert width.verdict == dc.AMBIGUOUS
    assert not width.blocks_release
    assert "not established" in width.why


def test_a_dimension_of_the_wrong_orientation_is_not_paired():
    """A distance is dimensioned by a string written ALONG it.

    An x-extent pairs with a wide (HORIZONTAL) string. Pairing it with a
    tall one inverted every room on AR-00 — width checked against depth —
    and reported the whole sheet as disagreeing.
    """
    rows = dc.compare_extents(
        _room(3850.0, 2500.0),
        [_obs("DO-1", 3850.0, (1900.0, 1200.0), "VERTICAL")])
    width = [r for r in rows if r.subject == "width"][0]
    assert width.verdict == dc.NOT_PRESENT


def test_no_dimension_nearby_is_not_present_not_a_disagreement():
    rows = dc.compare_extents(
        _room(3850.0, 2500.0),
        [_obs("DO-1", 3850.0, (900000.0, 900000.0), "HORIZONTAL")])
    assert {r.verdict for r in rows} == {dc.NOT_PRESENT}
    assert "not a disagreement" in rows[0].why


def test_the_two_values_are_never_averaged():
    rows = dc.compare_extents(
        _room(3850.0, 2500.0),
        [_obs("DO-1", 3850.0, (1900.0, 1200.0), "HORIZONTAL")])
    rec = [r for r in rows if r.subject == "width"][0].record()
    assert rec["printed_mm"] == 3850.0
    assert rec["vector_measured_mm"] == 3850.0
    assert "mean" in rec["never_averaged"]
    assert rec["supports"] == "GEOMETRY_VALIDATION_ONLY_NOT_IDENTITY"


def test_a_dimension_may_not_be_used_as_identity_evidence():
    """The WSH-01 error in a new costume, refused at the type level."""
    with pytest.raises(ObservationError):
        _obs("DO-1", 1850.0, (0.0, 0.0)).require_use(USE_FOR_IDENTITY)


def test_the_report_counts_verdicts_and_says_what_it_compared():
    rep = dc.assess([("BTH-01", _room(3600.0, 2500.0))],
                    [_obs("DO-1", 3850.0, (1800.0, 1200.0), "HORIZONTAL")])
    rec = rep.record()
    assert rec["DISAGREE"] == 1
    assert rec["material_disagreements_blocking_release"] == 1
    assert "CLEAR EXTENT" in rec["notes"]["what_is_compared"]
    assert "manufactures disagreements" in rec["notes"]["what_is_compared"]
    assert "average the two" in rec["what_this_may_never_do"]
    assert "instruments" in rec["tolerance_basis"]
