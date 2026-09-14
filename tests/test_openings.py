"""E34 spike — an opening candidate accumulates evidence; no signal decides alone.

Raster bridging failed here because one signal (a door-width gap between two
ink runs) was treated as sufficient, and printed fixtures supply that signal in
abundance. These tests hold the shape that prevents a repeat: candidates seed
only from PAIRED wall faces, and validation needs several independent signals
including two genuinely different mapped spaces.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from engine.openings import (AMBIGUOUS, DOOR, DOUBLE_DOOR, E_JAMB_BOTH,
                             E_JAMB_ONE, E_LEAF, E_PAIRED_GAP, E_SWING,
                             E_TWO_SPACES, E_WIDTH, OPEN_TRANSITION, PROBABLE,
                             REJECTED, STRONG, UNCLASSIFIED, VALIDATED,
                             OpeningCandidate, find_candidates,
                             gaps_in_paired_faces, summarise)

# A horizontal wall at y=1000 with a 900 mm hole between x=2000 and x=2900.
FACES = [("H", 1000.0, 0.0, 2000.0), ("H", 1000.0, 2900.0, 5000.0)]


def cand(**kw) -> OpeningCandidate:
    base = dict(opening_candidate_id="OC-1", axis="H", fixed_mm=1000.0,
                start_mm=2000.0, end_mm=2900.0)
    base.update(kw)
    return OpeningCandidate(**base)


# --- the seed must be a paired wall face --------------------------------------

def test_a_gap_between_collinear_paired_faces_is_found():
    gaps = gaps_in_paired_faces(FACES)
    assert len(gaps) == 1
    ori, fixed, a, b = gaps[0]
    assert (ori, fixed, a, b) == ("H", 1000.0 - 1000.0 % 12 or 996.0, 2000.0, 2900.0) \
        or (ori, a, b) == ("H", 2000.0, 2900.0)


def test_faces_on_different_lines_never_form_a_gap():
    """A fixture 300 mm off the wall line is not the other side of a doorway."""
    assert gaps_in_paired_faces(
        [("H", 1000.0, 0.0, 2000.0), ("H", 1300.0, 2900.0, 5000.0)]) == []


def test_a_gap_too_small_or_too_large_is_not_offered():
    assert gaps_in_paired_faces(
        [("H", 1000.0, 0.0, 2000.0), ("H", 1000.0, 2100.0, 5000.0)]) == []   # 100 mm
    assert gaps_in_paired_faces(
        [("H", 1000.0, 0.0, 2000.0), ("H", 1000.0, 9000.0, 12000.0)]) == []  # 7 m


def test_overlapping_faces_merge_before_gaps_are_measured():
    runs = [("H", 1000.0, 0.0, 2000.0), ("H", 1000.0, 1500.0, 2000.0),
            ("H", 1000.0, 2900.0, 5000.0)]
    assert len(gaps_in_paired_faces(runs)) == 1


# --- no single signal validates -----------------------------------------------

def test_a_bare_gap_is_ambiguous_not_a_door():
    """The raster-bridging mistake: a 900 mm hole in a wall is a hole in a wall."""
    c = cand(evidence=[E_PAIRED_GAP, E_WIDTH])
    assert c.confidence_status == AMBIGUOUS


def test_two_strong_signals_reach_probable_only():
    c = cand(evidence=[E_PAIRED_GAP, E_WIDTH, E_JAMB_BOTH])
    assert c.confidence_status == PROBABLE


def test_three_strong_signals_without_two_spaces_stay_probable():
    """An opening between a room and a duct is not a door. This project has
    four duct slots that would otherwise qualify."""
    c = cand(evidence=[E_PAIRED_GAP, E_JAMB_BOTH, E_SWING, E_WIDTH])
    assert E_TWO_SPACES not in c.evidence
    assert c.confidence_status == PROBABLE


def test_validation_needs_three_strong_signals_and_two_mapped_spaces():
    c = cand(evidence=[E_PAIRED_GAP, E_JAMB_BOTH, E_TWO_SPACES, E_WIDTH],
             adjacent_space_ids=("BTH-03", "COR-03"))
    assert c.confidence_status == VALIDATED


def test_a_width_band_is_not_strong_evidence_on_its_own():
    assert E_WIDTH not in STRONG
    c = cand(evidence=[E_WIDTH])
    assert c.confidence_status == REJECTED


def test_an_implausible_width_is_rejected_however_much_else_agrees():
    c = cand(start_mm=0.0, end_mm=120.0,
             evidence=[E_PAIRED_GAP, E_JAMB_BOTH, E_SWING, E_TWO_SPACES])
    assert c.confidence_status == REJECTED


# --- a swing is supporting evidence, never a condition ------------------------

def test_an_opening_validates_with_no_swing_arc_at_all():
    """Sliding doors, pocket doors, double doors and open transitions may have
    no arc drawn. Requiring one would miss them."""
    c = cand(evidence=[E_PAIRED_GAP, E_JAMB_BOTH, E_TWO_SPACES, E_WIDTH])
    assert E_SWING not in c.evidence and c.confidence_status == VALIDATED


def test_a_swing_arc_alone_does_not_validate_anything():
    c = cand(evidence=[E_SWING])
    assert c.confidence_status == AMBIGUOUS


# --- what a candidate may and may not assert ----------------------------------

def test_a_candidate_never_invents_a_height():
    c = cand(evidence=[E_PAIRED_GAP])
    assert c.height_mm is None


def test_a_width_in_two_bands_stays_unclassified_rather_than_picking_one():
    c = find_candidates(FACES)[0]          # 900 mm sits in DOOR and WINDOW
    assert len(c.proposed_types()) > 1
    assert c.candidate_type == UNCLASSIFIED


def test_a_wide_gap_proposes_an_open_transition():
    wide = [("H", 1000.0, 0.0, 2000.0), ("H", 1000.0, 5000.0, 8000.0)]
    c = find_candidates(wide)[0]
    assert OPEN_TRANSITION in c.proposed_types()


def test_a_candidate_records_every_signal_for_audit():
    r = find_candidates(FACES)[0].record()
    for field in ("evidence", "strong_evidence_count", "confidence_status",
                  "geometry_sources", "proposed_types", "width_mm"):
        assert field in r


def test_one_sided_candidates_say_they_may_open_onto_a_duct():
    c = find_candidates(FACES, space_at=lambda *a: None)[0]
    assert "duct" in c.note


# --- signals are assembled from real geometry ---------------------------------

def test_jambs_at_both_ends_are_detected_and_one_end_is_distinguished():
    both = [("V", 2000.0, 900.0, 1100.0), ("V", 2900.0, 900.0, 1100.0)]
    c = find_candidates(FACES, jambs=both)[0]
    assert E_JAMB_BOTH in c.evidence
    one = find_candidates(FACES, jambs=both[:1])[0]
    assert E_JAMB_ONE in one.evidence and E_JAMB_BOTH not in one.evidence


def test_two_different_mapped_spaces_produce_the_two_spaces_signal():
    def space_at(axis, fixed, along, side):
        return "BTH-03" if side < 0 else "COR-03"
    c = find_candidates(FACES, space_at=space_at)[0]
    assert E_TWO_SPACES in c.evidence
    assert set(c.adjacent_space_ids) == {"BTH-03", "COR-03"}


def test_the_same_space_on_both_sides_is_not_two_spaces():
    c = find_candidates(FACES, space_at=lambda *a: "BTH-03")[0]
    assert E_TWO_SPACES not in c.evidence


def test_the_summary_counts_statuses_and_evidence():
    s = summarise(find_candidates(FACES))
    assert s["candidates"] == 1 and "by_status" in s and "by_evidence" in s
