"""Topology recovery — a gap is classified, never discarded.

The correction that produced this module: I reported 32 same-space gaps as
phantoms. That was wrong, and wrong in a way that mattered. This segmentation is
already known to merge real spaces — the washroom is inside a neighbour and
BED-04 contains an unseparated bathroom — so a gap whose two sides land in one
region is exactly what an opening inside an under-segmented region looks like.
Rejecting the class threw away the recovery signal for both known defects.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from engine.topology import (AMBIGUOUS, DRAWING_NOISE, EXTERIOR_OPENING,
                             INSUFFICIENT_OVERLAP, INTERIOR_OPENING,
                             INTRA_REGION, KEPT, NOT_MUTUAL,
                             NO_PARTNER_IN_RANGE, TOPOLOGY_BOUNDARY, TOO_THICK,
                             UNMAPPED_SPACE, UNRESOLVED, GapCandidate,
                             SplitCandidate, WallPair, classify_gap,
                             gaps_along_pairs, pairing_diagnostic, wall_pairs)

# One 200 mm wall running along y, its two faces at x=1000 and x=1200.
WALL = [("V", 1000.0, 0.0, 5000.0), ("V", 1200.0, 0.0, 5000.0)]


def gap(**kw) -> GapCandidate:
    base = dict(gap_id="GC-1", pair_id="WP-1", axis="V", centreline_mm=1100.0,
                start_mm=2000.0, end_mm=2900.0, thickness_mm=200.0)
    base.update(kw)
    return GapCandidate(**base)


# --- pair identity ------------------------------------------------------------

def test_two_faces_of_one_wall_become_a_pair_that_knows_both_sides():
    pairs = wall_pairs(WALL, D(1))
    assert len(pairs) == 1
    p = pairs[0]
    assert p.thickness_mm == 200.0 and p.centreline_mm == 1100.0
    assert {p.face_a_mm, p.face_b_mm} == {1000.0, 1200.0}


def test_a_fixture_line_does_not_pair_with_a_wall_face():
    """Mutual-nearest: the wall's own nearest face is its other side."""
    lines = WALL + [("V", 1420.0, 0.0, 5000.0)]      # 220 mm from the far face
    pairs = wall_pairs(lines, D(1))
    assert len(pairs) == 1
    assert 1420.0 not in {pairs[0].face_a_mm, pairs[0].face_b_mm}


def test_two_unrelated_features_on_one_line_cannot_form_a_gap():
    """The phantom-gap defect: collinear within 12 mm is not one wall."""
    pairs = wall_pairs(WALL, D(1))
    runs = {("V", round(1000.0 / 12)): [(0.0, 2000.0)],
            ("V", round(1200.0 / 12)): [(2900.0, 5000.0)]}
    # face A stops at 2000, face B starts at 2900 — the faces are interrupted in
    # different places, so there is no shared break.
    assert gaps_along_pairs(pairs, runs) == []


def test_a_gap_needs_both_faces_interrupted_at_the_same_place():
    pairs = wall_pairs(WALL, D(1))
    runs = {("V", round(1000.0 / 12)): [(0.0, 2000.0), (2900.0, 5000.0)],
            ("V", round(1200.0 / 12)): [(0.0, 2000.0), (2900.0, 5000.0)]}
    gaps = gaps_along_pairs(pairs, runs)
    assert len(gaps) == 1
    assert gaps[0].width_mm == 900.0
    assert "BOTH_FACES_INTERRUPTED" in gaps[0].evidence[0]


def test_one_face_stopping_alone_is_a_recess_not_an_opening():
    pairs = wall_pairs(WALL, D(1))
    runs = {("V", round(1000.0 / 12)): [(0.0, 2000.0), (2900.0, 5000.0)],
            ("V", round(1200.0 / 12)): [(0.0, 5000.0)]}
    assert gaps_along_pairs(pairs, runs) == []


# --- classification: nothing is thrown away -----------------------------------

def _at(left, right):
    return lambda axis, fixed, along, side: left if side < 0 else right


def test_two_different_spaces_is_an_interior_opening():
    g = classify_gap(gap(), region_at=_at(7, 8),
                     space_of={7: "BTH-03", 8: "COR-03"}.get,
                     outside_ids=frozenset({1}))
    assert g.gap_class == INTERIOR_OPENING
    assert set(g.space_ids) == {"BTH-03", "COR-03"}


def test_the_same_region_on_both_sides_is_a_split_candidate_not_a_phantom():
    """The correction. BED-04 and the washroom look exactly like this."""
    g = classify_gap(gap(), region_at=_at(7, 7), space_of={7: "BED-04"}.get,
                     outside_ids=frozenset({1}))
    assert g.gap_class == INTRA_REGION
    assert g.suggests_split
    assert "under-segmented" in g.note


def test_outside_on_one_side_is_an_exterior_opening_candidate():
    g = classify_gap(gap(), region_at=_at(1, 7), space_of={7: "BED-01"}.get,
                     outside_ids=frozenset({1}))
    assert g.gap_class == EXTERIOR_OPENING


def test_an_unmapped_region_both_sides_is_its_own_class_not_noise():
    """56 of the spike's 94 gaps landed here and were called noise."""
    g = classify_gap(gap(), region_at=_at(99, 99), space_of=lambda r: None,
                     outside_ids=frozenset({1}))
    assert g.gap_class == UNMAPPED_SPACE
    assert g.gap_class != DRAWING_NOISE


def test_neither_side_resolving_is_unresolved_not_rejected():
    g = classify_gap(gap(), region_at=_at(None, None), space_of=lambda r: None,
                     outside_ids=frozenset({1}))
    assert g.gap_class == UNRESOLVED


def test_one_mapped_side_and_one_unresolved_is_unresolved():
    g = classify_gap(gap(), region_at=_at(7, None), space_of={7: "BED-01"}.get,
                     outside_ids=frozenset({1}))
    assert g.gap_class == UNRESOLVED


def test_only_intra_region_gaps_suggest_a_split():
    for cls, regions in ((INTERIOR_OPENING, (7, 8)), (EXTERIOR_OPENING, (1, 7))):
        g = classify_gap(gap(), region_at=_at(*regions),
                         space_of={7: "A", 8: "B"}.get,
                         outside_ids=frozenset({1}))
        assert not g.suggests_split


# --- the rejection diagnostic -------------------------------------------------

def test_the_diagnostic_accounts_for_every_line():
    lines = WALL + [("V", 9000.0, 0.0, 100.0), ("H", 500.0, 0.0, 4000.0)]
    d = pairing_diagnostic(lines, D(1))
    assert sum(d.values()) == len(lines)


def test_a_lone_line_is_recorded_as_having_no_partner():
    d = pairing_diagnostic([("V", 9000.0, 0.0, 5000.0)], D(1))
    assert d[NO_PARTNER_IN_RANGE] == 1 and d[KEPT] == 0


def test_a_partner_beyond_the_thickness_range_is_recorded_as_too_thick():
    d = pairing_diagnostic([("V", 0.0, 0.0, 5000.0), ("V", 3000.0, 0.0, 5000.0)],
                           D(1))
    assert d[TOO_THICK] == 2


def test_a_short_overlap_is_recorded_as_such_rather_than_as_no_partner():
    d = pairing_diagnostic([("V", 0.0, 0.0, 5000.0), ("V", 200.0, 4900.0, 5000.0)],
                           D(1))
    assert d[INSUFFICIENT_OVERLAP] == 2


def test_the_diagnostic_reports_reasons_rather_than_a_pass_rate():
    """Loosening a tolerance before knowing which one rejected the lines is
    tuning in the dark."""
    d = pairing_diagnostic(WALL, D(1))
    assert d[KEPT] == 2
    assert set(d) >= {KEPT, NO_PARTNER_IN_RANGE, TOO_THICK, NOT_MUTUAL,
                      INSUFFICIENT_OVERLAP}


# --- split candidates ---------------------------------------------------------

def test_a_split_candidate_starts_ambiguous_and_names_its_printed_reference():
    s = SplitCandidate("TC-1", 361, "WSH-01", "V", 1100.0, 2000.0, 2900.0,
                       printed_reference="1500 x 2400 mm = 3.600 m2")
    assert s.status == AMBIGUOUS
    assert s.boundary_kind == TOPOLOGY_BOUNDARY
    assert "3.600" in s.record()["printed_reference"]


def test_a_dashed_boundary_is_not_typed_as_a_door_on_detection():
    """A dashed line may be a threshold, a kerb, a finish change or a bulkhead.
    What matters first is whether it can split a region."""
    s = SplitCandidate("TC-2", 400, "BED-04", "H", 5000.0, 1000.0, 2600.0,
                       evidence=["DASHED_RUN"])
    assert s.boundary_kind == TOPOLOGY_BOUNDARY


# --- fragment merging ---------------------------------------------------------

from engine.topology import merge_collinear


def test_fragments_of_one_drawn_line_are_rejoined():
    """The diagnostic's finding: 28,566 of 35,355 segments are under 100 mm, and
    95.6% of lines were rejected for insufficient overlap against a 300 mm
    minimum. A 40 mm fragment cannot overlap anything by 300 mm; forty of them in
    a row are a wall face two metres long."""
    frag = [("V", 1000.0, i * 40.0, i * 40.0 + 38.0) for i in range(50)]
    merged = merge_collinear(frag)
    assert len(merged) == 1
    assert merged[0][3] - merged[0][2] > 1900


def test_merging_never_joins_across_a_doorway():
    """Joining across the break would erase the thing this module looks for."""
    door = [("V", 1000.0, 0.0, 2000.0), ("V", 1000.0, 2900.0, 5000.0)]
    assert len(merge_collinear(door)) == 2


def test_merging_respects_the_join_limit_exactly():
    near = [("V", 0.0, 0.0, 100.0), ("V", 0.0, 120.0, 200.0)]     # 20 mm apart
    far = [("V", 0.0, 0.0, 100.0), ("V", 0.0, 200.0, 300.0)]      # 100 mm apart
    assert len(merge_collinear(near, join_mm=25.0)) == 1
    assert len(merge_collinear(far, join_mm=25.0)) == 2


def test_lines_on_different_lines_are_never_merged():
    assert len(merge_collinear([("V", 0.0, 0.0, 100.0),
                                ("V", 500.0, 0.0, 100.0)])) == 2


def test_merging_keeps_orientations_apart():
    assert len(merge_collinear([("V", 0.0, 0.0, 100.0),
                                ("H", 0.0, 0.0, 100.0)])) == 2


def test_merging_is_input_preparation_not_a_loosened_tolerance():
    """The pairing thresholds are untouched; the input is assembled first."""
    import inspect
    src = inspect.getsource(merge_collinear)
    assert "min_thickness" not in src and "min_overlap" not in src


def test_a_wide_gap_is_flagged_as_a_probable_wall_termination():
    """21 of 45 intra-region candidates on AR-00 were wider than 2 m. A wall
    ending at a corner interrupts both faces in exactly the same way a doorway
    does, and perpendicular junction detection is not built."""
    from engine.topology import WALL_TERMINATION_SUSPECT_MM
    pairs = wall_pairs(WALL, D(1))
    runs = {("V", round(1000.0 / 12)): [(0.0, 2000.0), (5000.0, 8000.0)],
            ("V", round(1200.0 / 12)): [(0.0, 2000.0), (5000.0, 8000.0)]}
    g = gaps_along_pairs(pairs, runs)[0]
    assert g.width_mm > WALL_TERMINATION_SUSPECT_MM
    assert "corner or junction" in g.note


def test_a_door_scale_gap_carries_no_termination_warning():
    pairs = wall_pairs(WALL, D(1))
    runs = {("V", round(1000.0 / 12)): [(0.0, 2000.0), (2900.0, 5000.0)],
            ("V", round(1200.0 / 12)): [(0.0, 2000.0), (2900.0, 5000.0)]}
    assert gaps_along_pairs(pairs, runs)[0].note == ""
