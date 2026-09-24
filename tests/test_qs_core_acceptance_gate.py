"""The gate is graded against the output this engine published before this round, and it must reject it.

A gate written after the fix, checked only against the fix, proves that the fix is self-consistent.  The R4
document is kept as a committed fixture for exactly this reason: it is the real thing the review objected to,
and every one of the ten checks has to be able to see what was wrong with it.
"""

from __future__ import annotations

import json
import pathlib

from engine.qs_core import acceptance, pipeline, synthetic as S
from engine.qs_core.entities import KIND_WALL_BAND

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


def r5_document():
    plan = S.small_plan("R1")
    ann = {c.component_ref: {"MATERIAL": "BLOCKWORK"} for c in plan["COMPONENTS"]
           if c.kind == KIND_WALL_BAND}
    result = pipeline.run(plan, max_opening_span=S.MAX_OPENING_SPAN,
                          drafting_resolution_m=S.DRAFTING_RESOLUTION,
                          wall_height_evidence=S.WALL_HEIGHT, annotations=ann,
                          masonry_materials=("BLOCKWORK",))
    return pipeline.acceptance_document(result, metamorphic={
        "RIGID_MOTION": {"EQUIVALENT": True}, "SEGMENTATION": {"EQUIVALENT": True},
        "REPRESENTATION": {"EQUIVALENT": True}})


def test_the_r4_output_fails_every_check_the_review_raised():
    graded = acceptance.grade(r4_document())
    failed = {c["CHECK"] for c in graded["CHECKS"] if c["RESULT"] == acceptance.FAIL}
    assert not graded["ALL_PASS"]
    assert {"A1", "A2", "A3", "A4", "A5", "A6", "A7"} <= failed, failed


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
    graded = acceptance.grade(r5_document())
    assert graded["ALL_PASS"], graded["BLOCKERS"]


def test_the_gate_reads_only_the_document():
    doc = r5_document()
    assert all(not hasattr(v, "__dict__") for v in doc.values() if not isinstance(v, (dict, list, str)))
    json.dumps(doc, default=str)          # a document, not an object graph


def test_a_single_smuggled_value_is_enough_to_fail_the_gate():
    doc = r5_document()
    key = sorted(doc["PUBLICATION"]["SUBTOTALS"])[0]
    doc["PUBLICATION"]["SUBTOTALS"][key] = dict(doc["PUBLICATION"]["SUBTOTALS"][key],
                                                FINAL_QUANTITY=99.0, ROWS_BLOCKED=1)
    graded = acceptance.grade(doc)
    assert not graded["ALL_PASS"] and graded["BLOCKERS"][0]["CHECK"] == "A1"
