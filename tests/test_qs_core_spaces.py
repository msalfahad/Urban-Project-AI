"""A room is assembled from evidence, not read off whichever fragment happens to hold its label.

Every case here is a small plan with an answer a surveyor would agree on, and the interesting half are the cases
where the right answer is "the drawing does not say".
"""

from __future__ import annotations

import pytest

from engine.qs_core import invariants, spaces as sp, synthetic as syn
from engine.qs_core.entities import (ASSIGNED_TO_SPACE, EXTERNAL_OPEN_AREA, KIND_SLIVER, NON_ROOM_GEOMETRY,
                                     SPACE_LABEL_CONFLICT, SPACE_NAMED, SPACE_UNNAMED, UNRESOLVED)


def assemble(fixture):
    comps, barriers, openings, labels = fixture
    return sp.assemble_semantic_spaces(comps, barriers, openings, labels, syn.TOL, syn.SLIVER_MIN, "R1")


def by_ref(result):
    return {m["COMPONENT_REF"]: m for m in result["MEMBERSHIP"]}


# ------------------------------------------------------------------ one room, several fragments
def test_one_room_cut_into_fragments_is_reassembled_and_keeps_its_label():
    r = assemble(syn.one_room_in_two_fragments())
    assert len(r["SPACES"]) == 1
    space = r["SPACES"][0]
    assert sorted(space.component_refs) == ["C-1", "C-2"]
    assert space.label == "MEETING" and space.label_status == SPACE_NAMED
    assert space.area == pytest.approx(3 * 3 + 2 * 3)
    assert space.evidence[0].rule == "LABEL_APPLIES_TO_THE_WHOLE_SPACE"


def test_the_unlabelled_fragment_is_not_left_as_its_own_unnamed_space():
    r = assemble(syn.one_room_in_two_fragments())
    assert all(m["ROOM_ID"] == r["SPACES"][0].room_id for m in r["MEMBERSHIP"])
    assert not [s for s in r["SPACES"] if s.label_status == SPACE_UNNAMED]


# ------------------------------------------------------------------ two rooms, by wall and by door
def test_two_rooms_either_side_of_a_thick_wall_stay_two_rooms():
    r = assemble(syn.two_rooms_with_a_thick_wall())
    labels = sorted(s.label for s in r["SPACES"])
    assert labels == ["OFFICE", "STORE"]
    assert by_ref(r)["W-1"]["STATUS"] == NON_ROOM_GEOMETRY


def test_two_rooms_separated_by_a_single_line_partition_stay_two_rooms():
    r = assemble(syn.single_line_partition())
    assert sorted(s.label for s in r["SPACES"]) == ["BATH", "BED"]
    seam = r["SEAMS"][0]
    assert seam["RELATION"] == sp.SEAM_WALL and seam["SHARES"]["MATERIAL"] == pytest.approx(1.0)


def test_two_spaces_joined_only_by_a_doorway_stay_two_spaces():
    r = assemble(syn.two_spaces_through_a_doorway())
    assert sorted(s.label for s in r["SPACES"]) == ["HALL", "KITCHEN"]
    seam = r["SEAMS"][0]
    assert seam["RELATION"] == sp.SEAM_OPENING
    assert seam["REFS"]["OPENINGS"] == ["OP-1"]


# ------------------------------------------------------------------ what must never become floor
def test_a_sliver_and_a_column_never_join_a_room():
    r = assemble(syn.room_with_a_sliver_and_a_column())
    m = by_ref(r)
    assert m["C-THIN"]["KIND"] == KIND_SLIVER and m["C-THIN"]["STATUS"] == NON_ROOM_GEOMETRY
    assert m["COL-1"]["STATUS"] == NON_ROOM_GEOMETRY
    assert m["C-1"]["STATUS"] == ASSIGNED_TO_SPACE
    assert len(r["SPACES"]) == 1 and r["SPACES"][0].component_refs == ["C-1"]
    assert invariants.no_wall_material_as_floor(r["MEMBERSHIP"])["PASS"]


def test_a_column_inside_a_room_is_excluded_from_the_rooms_area():
    r = assemble(syn.room_with_a_sliver_and_a_column())
    assert r["SPACES"][0].area == pytest.approx(4.0 * 3.0)


# ------------------------------------------------------------------ the cases the engine must refuse
def test_an_ambiguous_seam_is_left_for_review_rather_than_decided():
    r = assemble(syn.ambiguous_seam())
    seam = r["SEAMS"][0]
    assert seam["RELATION"] == sp.SEAM_MIXED
    assert seam["SHARES"]["MATERIAL"] == pytest.approx(0.5) and seam["SHARES"]["FREE"] == pytest.approx(0.5)
    assert r["REVIEW_PAIRS"] == [("C-1", "C-2")]
    assert all(s.status == UNRESOLVED for s in r["SPACES"] if len(s.component_refs) > 1) or \
           all(s.status == ASSIGNED_TO_SPACE for s in r["SPACES"])
    assert len(r["SPACES"]) == 2, "a seam the engine cannot read must not be merged through"


def test_two_labels_in_one_continuous_area_are_a_question_not_a_choice():
    r = assemble(syn.conflicting_labels_in_one_space())
    assert len(r["SPACES"]) == 1
    s = r["SPACES"][0]
    assert s.label_status == SPACE_LABEL_CONFLICT and s.label is None
    assert sorted(s.labels_seen) == ["GUEST", "STUDY"]
    assert s.status == UNRESOLVED


def test_an_internal_space_that_runs_into_an_external_area_is_flagged():
    r = assemble(syn.internal_meets_external())
    m = by_ref(r)
    assert m["C-OUT"]["STATUS"] == UNRESOLVED
    assert any(s.status == UNRESOLVED for s in r["SPACES"])
    assert ("C-IN", "C-OUT") in r["REVIEW_PAIRS"]


def test_an_external_area_with_a_wall_between_stays_external():
    comps, barriers, openings, labels = syn.internal_meets_external()
    barriers = [sp.Barrier("Y", 4.0, 0.0, 3.0, sp.Barrier.BACKED_BY_MATERIAL, syn.FLOOR, component_ref="W")]
    r = sp.assemble_semantic_spaces(comps, barriers, openings, labels, syn.TOL, syn.SLIVER_MIN, "R1")
    assert by_ref(r)["C-OUT"]["STATUS"] == EXTERNAL_OPEN_AREA


# ------------------------------------------------------------------ the whole-plan guarantees
def test_every_component_ends_in_exactly_one_state():
    for fixture in (syn.one_room_in_two_fragments(), syn.two_rooms_with_a_thick_wall(),
                    syn.room_with_a_sliver_and_a_column(), syn.internal_meets_external(),
                    syn.ambiguous_seam(), syn.conflicting_labels_in_one_space()):
        r = assemble(fixture)
        check = invariants.every_component_resolved_once(r["MEMBERSHIP"])
        assert check["PASS"], check["RESULT"]
        assert len(r["MEMBERSHIP"]) == len(fixture[0])


def test_a_space_area_is_always_the_sum_of_its_own_components():
    comps, barriers, openings, labels = syn.one_room_in_two_fragments()
    r = sp.assemble_semantic_spaces(comps, barriers, openings, labels, syn.TOL, syn.SLIVER_MIN, "R1")
    assert invariants.space_areas_match_members(r["SPACES"], comps, 1e-9)["PASS"]


def test_the_seam_register_records_what_was_on_every_seam():
    r = assemble(syn.two_spaces_through_a_doorway())
    assert r["SEAMS"]
    for seam in r["SEAMS"]:
        assert set(seam["SHARES"]) == {"MATERIAL", "OPENING", "CANDIDATE_OPENING", "FREE"}
        assert sum(seam["SHARES"].values()) == pytest.approx(1.0)


def test_a_gap_the_source_draws_but_does_not_explain_is_a_question_not_a_merge():
    """A wall that simply stops: a doorway, an archway or a missing line all look like this."""
    a = syn.floor_region("C-1", [(0.0, 0.0, 3.0, 3.0)])
    b = syn.floor_region("C-2", [(3.0, 0.0, 6.0, 3.0)])
    closure = sp.Barrier("Y", 3.0, 0.0, 3.0, sp.Barrier.VIRTUAL_CLOSURE, syn.FLOOR, component_ref="GAP")
    r = sp.assemble_semantic_spaces([a, b], [closure], [], [syn.Label("LOUNGE", 1.5, 1.5)],
                                    syn.TOL, syn.SLIVER_MIN, "R1")
    assert r["SEAMS"][0]["RELATION"] == sp.SEAM_CANDIDATE_OPENING
    assert len(r["SPACES"]) == 2
    assert ("C-1", "C-2") in r["REVIEW_PAIRS"]
