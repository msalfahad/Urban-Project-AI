"""One moment, one set of numbers.

R6 resolved four window heights from the room standard after it had already built the opening register, the
deductions, the dependency graph and the question register.  The height evidence lived in a dict the opening
shared with its admission record, so that dict read ESTABLISHED while the registers beside it still carried a
null area and a question asking for the height that had just been answered.  Every record was internally
consistent; together they described two different moments.
"""

from __future__ import annotations

from engine.qs_core import evidence as EV, final_state as FS, pipeline, synthetic as S


def a_flat():
    return S.run(S.a_flat_with_four_different_room_uses("R1"), wall_height=3.0,
                 room_category_mapping=S.LABEL_TO_CATEGORY, standard_table=S.STANDARD_TABLE,
                 space_role=S.space_role)


def test_the_room_standard_answers_before_the_registers_are_built():
    r = a_flat()
    answered = [o for o in r["FINAL_OPENING_STATE"]["OPENINGS"]
                if o["HEIGHT_EVIDENCE"]["SOURCE"] == EV.APPROVED_GUIDE]
    assert answered, "this fixture exists so that a standard answers some heights"
    by_ref = {o["OPENING_REF"]: o for o in r["OPENING_REGISTER"]["REGISTER"]}
    for o in answered:
        row = by_ref[o["OPENING_REF"]]
        assert row["HEIGHT_M"] == o["HEIGHT_M"]
        assert row["AREA_M2"] == o["AREA_M2"] is not None


def test_an_answered_height_leaves_no_question_asking_for_it():
    r = a_flat()
    answered = {o["OPENING_REF"] for o in r["FINAL_OPENING_STATE"]["OPENINGS"]
                if o["HEIGHT_EVIDENCE"]["STATUS"] == EV.ESTABLISHED}
    asked = {q["SUBJECT_REF"] for q in r["QUESTIONS"]["ROOT_QUESTIONS"]
             if q["KIND"] == "OPENING_HEIGHT_NOT_ESTABLISHED"}
    assert answered and not (answered & asked), sorted(answered & asked)


def test_an_unanswered_height_leaves_exactly_one_question():
    """The same fixture with no standard supplied: the heights are unresolved and each is asked once."""
    r = S.run(S.a_flat_with_four_different_room_uses("R1"), wall_height=3.0, space_role=S.space_role)
    unresolved = [o for o in r["FINAL_OPENING_STATE"]["OPENINGS"]
                  if o["HEIGHT_EVIDENCE"]["STATUS"] != EV.ESTABLISHED
                  and o["HOST_ASSIGNMENT_STATUS"] == "HOST_ASSIGNED"]
    assert unresolved
    asked = [q for q in r["QUESTIONS"]["ROOT_QUESTIONS"]
             if q["KIND"] == "OPENING_HEIGHT_NOT_ESTABLISHED"]
    assert sorted(q["SUBJECT_REF"] for q in asked) == sorted(o["OPENING_REF"] for o in unresolved)
    assert len(asked) == len({q["ROOT_QUESTION_ID"] for q in asked})


def test_answering_a_question_removes_it_and_its_blockers_deterministically():
    """Supply the standard and the question goes, with the rows it was holding up."""
    without = S.run(S.a_flat_with_four_different_room_uses("R1"), wall_height=3.0, space_role=S.space_role)
    with_guide = a_flat()
    q_before = {q["ROOT_QUESTION_ID"] for q in without["QUESTIONS"]["ROOT_QUESTIONS"]
                if q["KIND"] == "OPENING_HEIGHT_NOT_ESTABLISHED"}
    q_after = {q["ROOT_QUESTION_ID"] for q in with_guide["QUESTIONS"]["ROOT_QUESTIONS"]
               if q["KIND"] == "OPENING_HEIGHT_NOT_ESTABLISHED"}
    assert q_before and not q_after
    blocked_before = {n for n, rec in without["BLOCKER_SETS"]["NODES"].items()
                      if any(b in q_before for b in rec["BLOCKER_IDS"])}
    assert blocked_before
    for node in blocked_before:
        rec = with_guide["BLOCKER_SETS"]["NODES"].get(node)
        if rec is not None:
            assert not (set(rec["BLOCKER_IDS"]) & q_before)


def test_every_derived_register_records_the_evidence_version_it_was_built_from():
    r = a_flat()
    version = r["EVIDENCE_VERSION"]
    for reg in (r["OPENING_REGISTER"], r["DEPENDENCY_GRAPH"], r["QUESTIONS"]):
        assert reg[FS.VERSION_FIELD] == version


def test_the_barrier_notices_evidence_that_arrives_after_it():
    """The mutation the gate has to catch, performed on the engine's own objects."""
    r = a_flat()
    final = r["FINAL_OPENING_STATE"]
    openings = [o for o in r["OPENING_REGISTER"]["REGISTER"]]
    assert FS.verify(final, r["CONFIRMED_OPENINGS"])["UNCHANGED"] is True
    late = r["CONFIRMED_OPENINGS"][0]
    late.admission["HEIGHT_EVIDENCE"] = {"STATUS": EV.ESTABLISHED, "VALUE": 9.9,
                                         "SOURCE": EV.APPROVED_GUIDE, "REFERENCE": "LATE"}
    drift = FS.verify(final, r["CONFIRMED_OPENINGS"])
    assert drift["UNCHANGED"] is False
    assert drift["DRIFTED"][0]["OPENING_REF"] == late.opening_ref
    assert drift["VERSION_NOW"] != final["EVIDENCE_VERSION"]
    del openings


def test_the_area_is_the_product_of_the_two_established_dimensions_or_it_is_null():
    for r in (a_flat(), S.run(S.small_plan("R1"), wall_height=3.0)):
        for o in r["FINAL_OPENING_STATE"]["OPENINGS"]:
            if o["WIDTH_M"] is not None and o["HEIGHT_M"] is not None:
                assert abs(o["AREA_M2"] - o["WIDTH_M"] * o["HEIGHT_M"]) < 1e-9
            else:
                assert o["AREA_M2"] is None


def test_the_document_the_gate_reads_carries_the_final_state_and_the_versions():
    doc = pipeline.acceptance_document(a_flat())
    assert doc["FINAL_OPENING_STATE"]["EVIDENCE_VERSION"]
    assert set(doc["EVIDENCE_VERSIONS"]) == {"OPENING_REGISTER", "DEPENDENCY_GRAPH", "QUESTIONS"}
    assert len(set(doc["EVIDENCE_VERSIONS"].values())) == 1
