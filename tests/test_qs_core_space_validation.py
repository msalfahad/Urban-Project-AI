"""Did the drawing exercise multi-component room assembly, or merely run past it?

R4 reported 50 semantic spaces on the real villa, each containing exactly one component, and presented that as
the multi-component room problem being solved.  Fifty single-component spaces validate nothing.
"""

from __future__ import annotations

from engine.qs_core import pipeline, space_validation as SV, spaces as SP, synthetic as S

RUN = dict(max_opening_span=S.MAX_OPENING_SPAN, drafting_resolution_m=S.DRAFTING_RESOLUTION)


def assemble(fixture):
    comps, barriers, ops, labels = fixture
    return SP.assemble_semantic_spaces(comps, barriers, ops, labels, S.TOL, S.SLIVER_MIN, "R1")


def validate(fixture):
    a = assemble(fixture)
    return SV.validate(a["SPACES"], a["MEMBERSHIP"], a["SEAMS"]), a


def test_a_drawing_with_a_genuine_two_fragment_room_is_graded_validated():
    rec, _a = validate(S.one_room_in_two_fragments())
    assert rec["OUTCOME"] == SV.VALIDATED
    assert rec["MULTI_COMPONENT_SPACES"] == 1 and rec["SINGLE_COMPONENT_SPACES"] == 0
    assert rec["MULTI_COMPONENT_DETAIL"][0]["CONTINUOUS_SEAM_COUNT"] >= 1


def test_a_drawing_whose_rooms_all_arrive_whole_is_graded_as_supplying_no_case():
    rec, _a = validate(S.two_rooms_with_a_thick_wall())
    assert rec["OUTCOME"] == SV.NO_CASE
    assert rec["MULTI_COMPONENT_SPACES"] == 0
    assert "remains unproved ON THIS SOURCE" in rec["WHAT_THIS_MEANS"][SV.NO_CASE]


def test_every_merge_shows_the_seam_that_justified_it():
    rec, _a = validate(S.one_room_in_two_fragments())
    detail = rec["MULTI_COMPONENT_DETAIL"][0]
    seam = detail["SEAMS_BETWEEN_MEMBERS"][0]
    assert seam["RELATION"] == SP.SEAM_CONTINUOUS
    assert seam["LENGTH_M"] > 0 and seam["SHARES"]["FREE"] == 1.0
    assert detail["SUPPORTED"]


def test_fragments_kept_apart_say_what_kept_them_apart():
    rec, _a = validate(S.two_spaces_through_a_doorway())
    apart = rec["ADJACENT_FRAGMENTS_KEPT_SEPARATE"]
    assert apart and all(k["WHY"] for k in apart)
    assert any(k["RELATION"] in (SP.SEAM_OPENING, SP.SEAM_WALL) for k in apart)


def test_a_seam_the_source_does_not_explain_is_listed_as_an_open_continuation():
    rec, _a = validate(S.ambiguous_seam())
    assert rec["UNRESOLVED_CANDIDATE_CONTINUATIONS"] or rec["OUTCOME"] == SV.CONTRADICTION


def test_the_lineage_of_every_component_to_its_room_is_reported():
    rec, a = validate(S.one_room_in_two_fragments())
    assert len(rec["COMPONENT_TO_ROOM_LINEAGE"]) == len(a["MEMBERSHIP"])
    assert all(r["ROOM_ID"] for r in rec["COMPONENT_TO_ROOM_LINEAGE"])


def test_the_grade_is_carried_by_the_pipeline_not_computed_by_the_report_writer():
    r = pipeline.run(S.small_plan("R1"), **RUN)
    assert r["SPACE_VALIDATION"]["OUTCOME"] in (SV.VALIDATED, SV.NO_CASE, SV.CONTRADICTION)
    assert r["SPACE_VALIDATION"]["SINGLE_COMPONENT_SPACES"] + \
        r["SPACE_VALIDATION"]["MULTI_COMPONENT_SPACES"] == len(r["SPACES"])


def test_a_merge_with_no_continuous_seam_behind_it_is_called_a_contradiction():
    """Not a result to report: a defect to fix.  The grade has to be able to say so."""
    a = assemble(S.one_room_in_two_fragments())
    seams = [dict(s, RELATION=SP.SEAM_WALL) for s in a["SEAMS"]]
    rec = SV.validate(a["SPACES"], a["MEMBERSHIP"], seams)
    assert rec["OUTCOME"] == SV.CONTRADICTION
    assert not rec["MULTI_COMPONENT_DETAIL"][0]["SUPPORTED"]
