"""The gate is graded against the output this engine published before this round, and it must reject it.

A gate written after the fix, checked only against the fix, proves that the fix is self-consistent.  The R4
document is kept as a committed fixture for exactly this reason: it is the real thing the review objected to,
and every one of the ten checks has to be able to see what was wrong with it.
"""

from __future__ import annotations

import json
import pathlib

from engine.qs_core import acceptance, pipeline, synthetic as S

R4 = json.loads(pathlib.Path("tests/fixtures/r4_packaged_output.json").read_text("utf-8"))


def r4_document():
    """The R4 output, mapped into the shape the gate reads - faithfully, including what it did not contain."""
    return {
        "WALL_ROWS": R4["WALL_ROWS"],
        "PUBLISHED_QUANTITIES": [{"REF": q["QUANTITY"], "QUANTITY": q["NEW_M2"]}
                                 for q in R4["PUBLISHED_TOTALS"]],
        "OPENING_REGISTER_ROWS": R4["OPENING_CANDIDATES"],
        "WALL_GEOMETRY_INCLUDES_OPENINGS": False,
    }


def r7_document():
    result = S.run(S.small_plan("R1"), wall_height=3.0, room_category_mapping=S.LABEL_TO_CATEGORY,
                   standard_table=S.STANDARD_TABLE)
    return pipeline.acceptance_document(result, metamorphic={
        "RIGID_MOTION": {"EQUIVALENT": True}, "SEGMENTATION": {"EQUIVALENT": True},
        "REPRESENTATION": {"EQUIVALENT": True}})


def test_the_r4_output_fails_every_check_the_review_raised():
    graded = acceptance.grade(r4_document())
    failed = {c["CHECK"] for c in graded["CHECKS"] if c["RESULT"] == acceptance.FAIL}
    assert not graded["ALL_PASS"]
    assert {f"A{i}" for i in range(1, 32)} == failed, failed


def test_the_r4_output_published_a_figure_over_rows_that_were_all_blocked():
    """The specific defect, read straight off the packaged artifact rather than asserted."""
    statuses = {r["STATUS"] for r in R4["WALL_ROWS"]}
    assert "FINAL_QUANTITY_AVAILABLE" not in statuses
    published = [q for q in R4["PUBLISHED_TOTALS"] if q["NEW_M2"]]
    assert published, "R4 did publish engine figures"
    a1 = next(c for c in acceptance.grade(r4_document())["CHECKS"] if c["CHECK"] == "A1")
    assert a1["RESULT"] == acceptance.FAIL and a1["FOUND"]["BLOCKED_ROWS"] == len(R4["WALL_ROWS"])


def test_the_r4_output_billed_thicknesses_nothing_established():
    thicknesses = sorted({round((r["THICKNESS_M"] or 0) * 1000) for r in R4["WALL_ROWS"]})
    assert 50 in thicknesses or 100 in thicknesses or 126 in thicknesses, thicknesses
    a6 = next(c for c in acceptance.grade(r4_document())["CHECKS"] if c["CHECK"] == "A6")
    assert a6["RESULT"] == acceptance.FAIL and a6["FOUND"]["HAS_IDENTITY_REGISTER"] is False


def test_the_r4_openings_carried_no_admission_decision_at_all():
    assert all("CLASSIFICATION" not in c for c in R4["OPENING_CANDIDATES"])
    a2 = next(c for c in acceptance.grade(r4_document())["CHECKS"] if c["CHECK"] == "A2")
    assert a2["RESULT"] == acceptance.FAIL


def test_the_r4_output_asserted_one_opening_basis_for_the_whole_drawing():
    bases = {r["GROSS_BASIS"] for r in R4["WALL_ROWS"]}
    assert len(bases) == 1, "one sentence, repeated on every row, is one assumption"
    a5 = next(c for c in acceptance.grade(r4_document())["CHECKS"] if c["CHECK"] == "A5")
    assert a5["RESULT"] == acceptance.FAIL


def test_the_current_engine_passes_the_same_gate():
    graded = acceptance.grade(r7_document())
    assert graded["OF"] == 31
    assert graded["ALL_PASS"], graded["BLOCKERS"]


def test_the_gate_reads_only_the_document():
    doc = r7_document()
    assert all(not hasattr(v, "__dict__") for v in doc.values() if not isinstance(v, (dict, list, str)))
    json.dumps(doc, default=str)          # a document, not an object graph


def test_a_single_smuggled_value_is_enough_to_fail_the_gate():
    doc = r7_document()
    key = sorted(doc["PUBLICATION"]["SUBTOTALS"])[0]
    doc["PUBLICATION"]["SUBTOTALS"][key] = dict(doc["PUBLICATION"]["SUBTOTALS"][key],
                                                FINAL_QUANTITY=99.0, ROWS_BLOCKED=1)
    graded = acceptance.grade(doc)
    assert not graded["ALL_PASS"] and graded["BLOCKERS"][0]["CHECK"] == "A1"


# ------------------------------------------------------------------ one mutation per new check
def _mutate(**changes):
    doc = r7_document()
    for path, value in changes.items():
        node, *rest = path.split("/")
        target = doc[node]
        for part in rest[:-1]:
            target = target[part] if not part.isdigit() else target[int(part)]
        key = rest[-1] if rest else None
        if key is None:
            doc[node] = value
        elif key.isdigit():
            target[int(key)] = value
        else:
            target[key] = value
    return doc


def _fails(doc, check):
    graded = acceptance.grade(doc)
    codes = {b["CHECK"] for b in graded["BLOCKERS"]}
    assert check in codes, f"{check} did not object; blockers were {sorted(codes)}"


def test_a11_catches_a_named_opening_missing_from_the_population():
    doc = r7_document()
    doc["OPENING_POPULATION"] = dict(doc["OPENING_POPULATION"],
                                     NAMED_BY_THE_SOURCE=["GHOST-1"] +
                                     doc["OPENING_POPULATION"]["NAMED_BY_THE_SOURCE"],
                                     NAMED_BY_THE_SOURCE_COUNT=99)
    _fails(doc, "A11")


def test_a12_catches_a_population_that_does_not_add_up():
    doc = r7_document()
    doc["OPENING_POPULATION"] = dict(doc["OPENING_POPULATION"], CANDIDATES_IN=99)
    _fails(doc, "A12")


def test_a13_catches_a_named_door_dropped_for_want_of_a_host():
    """The R5 defect, put back: the object exists, its host does not resolve, and it is discarded."""
    doc = r7_document()
    pop = doc["OPENING_POPULATION"]
    ref = pop["PHYSICAL_OPENING_REFS"][0]
    rows = [dict(r, CLASSIFICATION="NON_OPENING_GAP") if r["CANDIDATE_REF"] == ref else r
            for r in pop["POPULATION"]]
    doc["OPENING_POPULATION"] = dict(pop, POPULATION=rows,
                                     PHYSICAL_OPENING_REFS=[r for r in pop["PHYSICAL_OPENING_REFS"]
                                                            if r != ref])
    _fails(doc, "A13")


def test_a14_catches_height_coverage_claimed_over_a_population_that_was_not_read():
    doc = r7_document()
    doc["OPENING_REGISTER_ROWS"] = []
    _fails(doc, "A14")


def test_a15_catches_a_superseded_claim_winning():
    doc = r7_document()
    rows = []
    for o in doc["OPENING_REGISTER_ROWS"]:
        adm = dict(o.get("ADMISSION") or {})
        h = dict(adm.get("HEIGHT_EVIDENCE") or {})
        if h.get("STATUS") == "ESTABLISHED":
            h["CONSIDERED"] = [dict(c, STATUS="SUPERSEDED") if c.get("REFERENCE") == h.get("REFERENCE") else c
                               for c in h.get("CONSIDERED", [])]
            adm["HEIGHT_EVIDENCE"] = h
        rows.append(dict(o, ADMISSION=adm))
    doc["OPENING_REGISTER_ROWS"] = rows
    _fails(doc, "A15")


def test_a16_catches_a_category_with_no_host_room_behind_it():
    doc = r7_document()
    reg = doc["ROOM_CATEGORY_REGISTER"]
    rows = [dict(r, CATEGORY=dict(r["CATEGORY"], CATEGORY="SOMETHING",
                                  ROOM=dict(r["CATEGORY"]["ROOM"], ROOM_ID=None)))
            for r in reg["REGISTER"]] or [{"OPENING_REF": "X",
                                           "CATEGORY": {"CATEGORY": "SOMETHING", "ROOM": {"ROOM_ID": None},
                                                        "SOURCE": None}}]
    doc["ROOM_CATEGORY_REGISTER"] = dict(reg, REGISTER=rows, OPENINGS=len(rows))
    _fails(doc, "A16")


def test_a17_catches_one_category_for_every_room():
    doc = r7_document()
    reg = doc["ROOM_CATEGORY_REGISTER"]
    doc["ROOM_CATEGORY_REGISTER"] = dict(reg, DISTINCT_CATEGORY_COUNT=1,
                                         DISTINCT_ROOMS=["R1", "R2", "R3"],
                                         REGISTER=reg["REGISTER"] or [{"OPENING_REF": "X", "CATEGORY": {
                                             "CATEGORY": "ONE", "SOURCE": "PROJECT_WIDE_DEFAULT",
                                             "ROOM": {"ROOM_ID": "R1"}}}],
                                         OPENINGS=max(1, reg["OPENINGS"]))
    _fails(doc, "A17")


def test_a18_catches_material_established_by_something_that_cannot_state_one():
    doc = r7_document()
    doc["WALL_IDENTITY_REGISTER"] = [dict(r, MATERIAL_EVIDENCE=dict(r["MATERIAL_EVIDENCE"] or {},
                                                                    EVIDENCE_SOURCE="THICKNESS_FAMILY"))
                                     for r in doc["WALL_IDENTITY_REGISTER"]]
    _fails(doc, "A18")


def test_a18_catches_a_thickness_family_recorded_as_material_proof():
    doc = r7_document()
    doc["WALL_IDENTITY_REGISTER"] = [dict(r, THICKNESS_FAMILY_PROVES_MATERIAL=True)
                                     for r in doc["WALL_IDENTITY_REGISTER"]]
    _fails(doc, "A18")


def test_a19_catches_the_same_fact_counted_twice():
    doc = r7_document()
    qs = doc["QUESTIONS"]
    root = {"ROOT_QUESTION_ID": "RQ::HOST_WALL_UNRESOLVED::D-1", "KIND": "HOST_WALL_UNRESOLVED",
            "SUBJECT_REF": "D-1"}
    doc["QUESTIONS"] = dict(qs, ROOT_QUESTIONS=[root, dict(root)], ROOT_QUESTION_COUNT=2)
    _fails(doc, "A19")


def test_a19_catches_an_impact_with_no_root_question():
    doc = r7_document()
    doc["QUESTIONS"] = dict(doc["QUESTIONS"], IMPACTS_WITHOUT_A_ROOT_QUESTION=["RQ::NOWHERE::X"])
    _fails(doc, "A19")


def test_a20_catches_a_narrative_that_contradicts_its_own_register():
    doc = r7_document()
    doc["NARRATIVE_ASSERTIONS"] = [{"STATEMENT": "nothing in the source names an opening",
                                    "REGISTER_PATH": "OPENING_POPULATION.NAMED_BY_THE_SOURCE_COUNT",
                                    "VALUE": 0}]
    _fails(doc, "A20")


def test_a20_is_the_check_that_would_have_caught_the_last_rounds_report():
    """R5's headline said the source named none of the thirty-five doors.  Its own register said otherwise."""
    doc = r7_document()
    named = doc["OPENING_POPULATION"]["NAMED_BY_THE_SOURCE_COUNT"]
    doc["NARRATIVE_ASSERTIONS"] = [
        {"STATEMENT": "the source names no opening at these locations",
         "REGISTER_PATH": "OPENING_POPULATION.NAMED_BY_THE_SOURCE_COUNT", "VALUE": 0}]
    graded = acceptance.grade(doc)
    a20 = next(c for c in graded["CHECKS"] if c["CHECK"] == "A20")
    assert a20["RESULT"] == acceptance.FAIL
    assert a20["FOUND"]["DISAGREEMENTS"][0]["REGISTER_SAYS"] == named


def test_a21_catches_a_row_called_blocked_beside_a_line_called_released():
    """The R5 report said one hundred and forty-three rows were blocked and one hundred and eleven released."""
    doc = r7_document()
    final_row = next(r for r in doc["WALL_ROWS"] if r["STATUS"] == "FINAL_QUANTITY_AVAILABLE")
    ref = final_row["COMPONENT_REF"]
    doc["WALL_LINE_STATUS"] = {
        "BLOCKED": doc["WALL_LINE_STATUS"]["BLOCKED"] + [ref],
        "NOT_BLOCKED": [r for r in doc["WALL_LINE_STATUS"]["NOT_BLOCKED"] if r != ref]}
    graded = acceptance.grade(doc)
    a21 = next(c for c in graded["CHECKS"] if c["CHECK"] == "A21")
    assert a21["RESULT"] == acceptance.FAIL
    assert a21["FOUND"]["CONTRADICTIONS"][0]["COMPONENT_REF"] == ref


def test_a21_catches_a_stated_row_count_that_the_rows_do_not_support():
    doc = r7_document()
    doc["PUBLICATION"]["ROW_CATEGORIES"] = dict(doc["PUBLICATION"]["ROW_CATEGORIES"], FINAL=7)
    graded = acceptance.grade(doc)
    a21 = next(c for c in graded["CHECKS"] if c["CHECK"] == "A21")
    assert a21["RESULT"] == acceptance.FAIL
    assert a21["FOUND"]["MISCOUNTED"]["FINAL"]["SAID"] == 7


# ------------------------------------------------------------------ R7: one moment, one set of numbers
def _blocker(check, doc):
    return next(c for c in acceptance.grade(doc)["CHECKS"] if c["CHECK"] == check)


def test_a22_catches_the_r6_defect_a_height_resolved_after_the_register_was_built():
    """The exact defect: resolve a dimension after the opening register exists, and do not rebuild it."""
    doc = r7_document()
    row = doc["OPENING_REGISTER_ROWS"][0]
    ref = row["OPENING_REF"]
    frozen = next(o for o in doc["FINAL_OPENING_STATE"]["OPENINGS"] if o["OPENING_REF"] == ref)
    # the room standard arrives late and answers the height; the register keeps its pre-category snapshot
    frozen["HEIGHT_EVIDENCE"] = {"STATUS": "ESTABLISHED", "VALUE": 1.2, "SOURCE": "ACTIVE_PROJECT_STANDARD",
                                 "REFERENCE": "GUIDE::KITCHEN"}
    frozen["HEIGHT_M"], frozen["AREA_M2"] = 1.2, round(frozen["WIDTH_M"] * 1.2, 9)
    a22 = _blocker("A22", doc)
    assert a22["RESULT"] == acceptance.FAIL
    assert any(d.get("OPENING_REF") == ref for d in a22["FOUND"]["DISAGREEMENTS"])


def test_a23_catches_a_question_asking_for_an_answer_the_document_already_holds():
    doc = r7_document()
    ref = doc["FINAL_OPENING_STATE"]["OPENINGS"][0]["OPENING_REF"]
    doc["QUESTIONS"]["ROOT_QUESTIONS"] = list(doc["QUESTIONS"]["ROOT_QUESTIONS"]) + [
        {"ROOT_QUESTION_ID": f"RQ::OPENING_HEIGHT_NOT_ESTABLISHED::{ref}",
         "KIND": "OPENING_HEIGHT_NOT_ESTABLISHED", "SUBJECT_REF": ref}]
    a23 = _blocker("A23", doc)
    assert a23["RESULT"] == acceptance.FAIL
    assert a23["FOUND"]["ANSWERED_BUT_STILL_ASKED"][0]["OPENING_REF"] == ref


def test_a24_catches_an_unresolved_dimension_nobody_asks_about():
    doc = r7_document()
    o = doc["FINAL_OPENING_STATE"]["OPENINGS"][0]
    o["HEIGHT_EVIDENCE"] = {"STATUS": "NOT_ESTABLISHED", "VALUE": None, "SOURCE": None, "REFERENCE": None}
    o["HEIGHT_M"], o["AREA_M2"] = None, None
    a24 = _blocker("A24", doc)
    assert a24["RESULT"] == acceptance.FAIL
    assert a24["FOUND"]["UNANSWERED_AND_UNASKED"][0]["OPENING_REF"] == o["OPENING_REF"]


def test_a25_catches_two_registers_built_from_two_different_moments():
    doc = r7_document()
    doc["EVIDENCE_VERSIONS"]["QUESTIONS"] = "EV-anearliermoment0000"
    a25 = _blocker("A25", doc)
    assert a25["RESULT"] == acceptance.FAIL
    assert "QUESTIONS" in a25["FOUND"]["MISMATCHED"]


def test_a26_catches_a_duplicated_dependency_impact():
    doc = r7_document()
    doc["QUESTIONS"]["DEPENDENCY_IMPACTS"] = [
        {"ROOT_QUESTION_ID": "RQ::X::Y", "NODE": "N", "NODE_KIND": "WALL_LINE", "EFFECT": "e"},
        {"ROOT_QUESTION_ID": "RQ::X::Y", "NODE": "N", "NODE_KIND": "WALL_LINE", "EFFECT": "e"}]
    a26 = _blocker("A26", doc)
    assert a26["RESULT"] == acceptance.FAIL and a26["FOUND"]["DUPLICATES"]


def test_a27_catches_a_question_claiming_to_release_a_row_with_another_blocker():
    doc = r7_document()
    doc["BLOCKER_SETS"] = {
        "NODES": {"W-1": {"NODE": "W-1", "NODE_KIND": "WALL_LINE", "NODE_STATUS": "BLOCKED",
                          "BLOCKER_IDS": ["RQ::A::1", "RQ::B::2"], "BLOCKER_COUNT": 2,
                          "ANSWER_ALONE_RELEASES_NODE": "RQ::A::1"}},
        "BY_ROOT_QUESTION": {"RQ::A::1": {"RELEASES_NODES": ["W-1"]}}}
    a27 = _blocker("A27", doc)
    assert a27["RESULT"] == acceptance.FAIL and a27["FOUND"]["OVERCLAIMED"]


def test_a28_catches_a_material_question_keyed_on_thickness_alone():
    doc = r7_document()
    doc["QUESTIONS"]["ROOT_QUESTIONS"] = list(doc["QUESTIONS"]["ROOT_QUESTIONS"]) + [
        {"ROOT_QUESTION_ID": "RQ::WALL_MATERIAL_NOT_ESTABLISHED::THICKNESS_FAMILY::0.2",
         "KIND": "WALL_MATERIAL_NOT_ESTABLISHED", "SUBJECT_REF": "THICKNESS_FAMILY::0.2"}]
    a28 = _blocker("A28", doc)
    assert a28["RESULT"] == acceptance.FAIL
    assert a28["FOUND"]["QUESTIONS_KEYED_ON_THICKNESS_ALONE"]


def test_a28_catches_a_thickness_family_recorded_as_material_proof():
    doc = r7_document()
    doc["WALL_IDENTITY_REGISTER"][0]["THICKNESS_FAMILY_PROVES_MATERIAL"] = True
    assert _blocker("A28", doc)["RESULT"] == acceptance.FAIL


def test_a29_catches_a_band_excluded_from_the_trade_on_weak_evidence():
    doc = r7_document()
    row = doc["WALL_IDENTITY_REGISTER"][0]
    row["GEOMETRY_IDENTITY"] = "NON_WALL_ARTEFACT"
    row["GEOMETRY_ARTEFACT_REASON"] = "COLUMN_OR_STRUCTURE"
    row["GEOMETRY_CONFIDENCE"] = "WEAK"
    a29 = _blocker("A29", doc)
    assert a29["RESULT"] == acceptance.FAIL and a29["FOUND"]["EXCLUDED_ON_WEAK_EVIDENCE"]


def test_a30_catches_an_open_area_competing_with_a_room_for_the_standard():
    doc = r7_document()
    doc["ROOM_CATEGORY_REGISTER"] = {"REGISTER": [
        {"OPENING_REF": "OP-W", "ROOM": {"STATUS": "HOST_ROOM_AMBIGUOUS", "CANDIDATES": [
            {"ROOM_ID": "R1", "LABEL": "BED ROOM", "ROLE": "ENCLOSED_ROOM"},
            {"ROOM_ID": "R2", "LABEL": "ROOF", "ROLE": "EXTERNAL_OR_OPEN_AREA"}]}}]}
    a30 = _blocker("A30", doc)
    assert a30["RESULT"] == acceptance.FAIL
    assert a30["FOUND"]["AMBIGUOUS_BECAUSE_OF_AN_OPEN_AREA"][0]["OPENING_REF"] == "OP-W"


def test_a31_catches_a_report_claim_that_its_register_does_not_support():
    doc = r7_document()
    doc["REPORT_CLAIMS"]["CLAIMS"][0].update({"VALUE": 999, "REGISTER_SAYS": 3, "VERIFIED": False})
    a31 = _blocker("A31", doc)
    assert a31["RESULT"] == acceptance.FAIL and a31["FOUND"]["UNVERIFIED"]


def test_the_claim_register_does_not_claim_to_have_verified_the_prose():
    doc = r7_document()
    claims = doc["REPORT_CLAIMS"]
    assert claims["ALL_DECLARED_CLAIMS_AGREE"] is True
    assert "all prose verified" in claims["WHAT_THIS_CHECK_DOES_NOT_PROVE"]
    assert "undeclared claim" in claims["WHAT_THIS_CHECK_DOES_NOT_PROVE"]
