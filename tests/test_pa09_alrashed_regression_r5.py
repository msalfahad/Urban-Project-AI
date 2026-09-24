"""The generic engine, run over a real drawing, and graded by the independent gate.

These tests read the registers the regression produced.  They check BEHAVIOUR - that every candidate was
classified before anything was hosted, that no blocked row reached a total, that a band was not billed for
having a thickness, that the quantities do not move when the drawing is described differently - and never that
a quantity matches a number someone reported earlier.  Where a frozen figure is mentioned at all, it is to prove
the frozen artifact was not touched.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from engine.qs_core import acceptance, admission as AD, invariants, masonry as MA, quantities as QY
from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import regression_r5 as RG

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
FROZEN_SHA = "7e9a3eba636ea95b77fce2bbb7dccad79d6971047af455bb2f542ee62165493f"
REC = OUT / "ALRASHED_GENERIC_ENGINE_VALIDATION.json"

pytestmark = pytest.mark.skipif(not REC.exists(),
                                reason="run research.qs_wall_treatment_01.pa09.alrashed.regression_r5 first")


@pytest.fixture(scope="module")
def rec():
    return json.loads(REC.read_text("utf-8"))


def register(name):
    return json.loads((OUT / f"ALRASHED_{name}.json").read_text("utf-8"))


# ------------------------------------------------------------------ the frozen artifact
def test_the_frozen_takeoff_was_read_and_never_written(rec):
    assert rec["FROZEN_UNCHANGED"]["REWRITTEN"] is False
    assert rec["FROZEN_UNCHANGED"]["SHA256_BEFORE"] == rec["FROZEN_UNCHANGED"]["SHA256_AFTER"] == FROZEN_SHA
    assert hashlib.sha256(RG.FROZEN.read_bytes()).hexdigest() == FROZEN_SHA


# ------------------------------------------------------------------ the publication contract on real output
def test_no_blocked_row_reaches_any_published_subtotal(rec):
    project = rec["FINAL_VERSUS_BLOCKED"]["WHOLE_PROJECT"]
    for key, sub in project["SUBTOTALS"].items():
        if sub["ROWS_BLOCKED"]:
            assert sub["FINAL_QUANTITY"] is None, key
            assert sub["WAITING_ON"], key
    if project["BLOCKED_SUBTOTAL_COUNT"]:
        assert project["PUBLISHED_TOTAL"] is None


def test_a_diagnostic_figure_is_never_presented_as_a_quantity(rec):
    for sub in rec["FINAL_VERSUS_BLOCKED"]["WHOLE_PROJECT"]["SUBTOTALS"].values():
        diag = [k for k in sub if k.startswith(QY.DIAGNOSTIC_PREFIX)]
        assert diag, "the arithmetic is kept, under a name that cannot be summed"
        if sub["STATUS"] != QY.STATUS_FINAL:
            assert sub["FINAL_QUANTITY"] is None


def test_the_comparison_with_the_frozen_artifact_states_what_is_comparable(rec):
    lines = rec["COMPARISON_WITH_THE_FROZEN_ARTIFACT"]["BLOCKWORK_LINES"]
    assert lines
    for line in lines:
        assert "COMPARABLE" in line and "TRACE" in line
        if not line["COMPARABLE"]:
            assert line["ENGINE_FINAL_M2"] is None
            assert line["WAITING_ON"] or line["ENGINE_STATUS"] == "NOT_PRODUCED"


# ------------------------------------------------------------------ admission, on the real population
def test_every_candidate_was_classified_before_anything_was_hosted(rec):
    pop = register("OPENING_ADMISSION_REGISTER")["BY_FLOOR"]
    for floor, p in pop.items():
        check = invariants.every_candidate_leaves_admission_classified(p)
        assert check["PASS"], (floor, check["RESULT"])
        assert p["CANDIDATES_IN"] == len(p["POPULATION"]), floor


def test_the_two_objects_the_review_named_are_now_classified_rather_than_carried(rec):
    """A 2 mm gap and a 0.60 m object with no host: neither is deleted, and neither is a deduction."""
    pop = register("OPENING_ADMISSION_REGISTER")["BY_FLOOR"]
    rows = [c for p in pop.values() for c in p["POPULATION"]]
    tiny = [c for c in rows if c["DRAWN_WIDTH_M"] < RG.DRAFTING_RESOLUTION_M]
    assert tiny, "the drawing does contain sub-resolution candidates"
    for c in tiny:
        assert c["CLASSIFICATION"] in (AD.DRAWING_NOISE, AD.OPENING_CANDIDATE_UNRESOLVED)
        assert c["EVIDENCE"]
    assert all(c["CLASSIFICATION"] != AD.CONFIRMED_OPENING for c in tiny)


def test_a_confirmed_opening_carries_width_evidence_and_height_evidence_separately(rec):
    reg = register("OPENING_TO_HOST_REGISTER")["BY_FLOOR"]
    for floor, r in reg.items():
        check = invariants.deductions_trace_to_width_and_height_evidence(r)
        assert check["PASS"], (floor, check["RESULT"])


def test_a_window_height_comes_from_the_projects_own_evidence_record(rec):
    """Reconstructed through the hierarchy, with the record that answered it - never an area copied back."""
    reg = register("OPENING_TO_HOST_REGISTER")["BY_FLOOR"]
    windows = [o for r in reg.values() for o in r["REGISTER"] if o["TYPE"] == "WINDOW"]
    for o in windows:
        h = (o.get("ADMISSION") or {}).get("HEIGHT_EVIDENCE") or {}
        assert h.get("STATUS") == "ESTABLISHED", o["OPENING_REF"]
        assert h.get("REFERENCE"), o["OPENING_REF"]
        assert h.get("SOURCE") in ("DRAWING_DIMENSION", "MEASURED_GEOMETRY", "OWNER_PROJECT_INPUT")
        assert h.get("CONSIDERED"), "the records it passed over are recorded too"


# ------------------------------------------------------------------ identity before measurement
def test_no_band_is_billed_as_masonry_for_having_a_thickness(rec):
    ident = register("MASONRY_IDENTITY_REGISTER")["BY_FLOOR"]
    rows = register("OPENING_TO_HOST_REGISTER")["WALL_LINE_QUANTITIES"]
    for floor, reg in ident.items():
        check = invariants.unusual_band_is_not_billed_on_thickness_alone(reg, rows[floor])
        assert check["PASS"], (floor, check["RESULT"])


def test_the_thickness_families_are_discovered_from_the_whole_source(rec):
    fams = rec["THICKNESS_FAMILIES_OF_THE_WHOLE_SOURCE"]["FAMILIES"]
    assert fams
    proved = {k for k, v in fams.items() if v["PROVED"]}
    singletons = {k for k, v in fams.items() if not v["PROVED"]}
    assert proved and singletons, "the drawing contains both real families and one-off bands"
    for k in singletons:
        assert fams[k]["MEMBER_COUNT"] < MA.FAMILY_MIN_MEMBERS


def test_a_band_that_is_not_masonry_is_excluded_rather_than_blocking_a_subtotal(rec):
    excluded = rec["FINAL_VERSUS_BLOCKED"]["EXCLUDED_ROWS"]
    assert excluded, "the drawing does contain bands that are not masonry"
    for row in excluded:
        assert row["WALL_IDENTITY"] in MA.IDENTITIES and row["WALL_IDENTITY"] not in MA.BILLABLE
        assert row["WHY"]


# ------------------------------------------------------------------ continuity and basis
def test_no_wall_line_was_joined_across_a_gap_without_evidence(rec):
    graph = register("DEPENDENCY_AND_BLOCKING_REGISTER")
    assert graph["BY_FLOOR"]
    basis = register("PER_WALL_OPENING_BASIS_REGISTER")["BY_FLOOR"]
    for floor, b in basis.items():
        for ref, r in b.items():
            assert r["BASIS"], (floor, ref)
            if r["BASIS"] in ("MATERIAL_SPANS_ITS_OPENINGS", "MATERIAL_STOPS_AT_THE_JAMBS"):
                assert r["OPENINGS_TESTED"], (floor, ref)


def test_the_basis_is_recorded_line_by_line_and_not_asserted_for_the_source(rec):
    basis = register("PER_WALL_OPENING_BASIS_REGISTER")
    assert "REPLACES" in basis
    lines = sum(len(b) for b in basis["BY_FLOOR"].values())
    assert lines == sum(f["WALL_LINES"] for f in rec["FLOORS"])


# ------------------------------------------------------------------ scoped blocking
def test_every_blocked_wall_line_names_the_question_that_blocks_it(rec):
    graph = register("DEPENDENCY_AND_BLOCKING_REGISTER")["BY_FLOOR"]
    for floor, g in graph.items():
        for node in g["BLOCKED_WALL_LINES"]:
            reasons = g["BLOCKED"][node]["REASONS"]
            assert reasons and all(r.get("KIND") and r.get("WHY") for r in reasons), (floor, node)


def test_something_survives_every_open_question(rec):
    """Scoped blocking has to leave work released, or it is the old blanket block under a new name."""
    graph = register("DEPENDENCY_AND_BLOCKING_REGISTER")["BY_FLOOR"]
    released = sum(len(g["RELEASED_WALL_LINES"]) for g in graph.values())
    blocked = sum(len(g["BLOCKED_WALL_LINES"]) for g in graph.values())
    assert released > 0 and blocked > 0
    assert released > blocked, (released, blocked)


def test_an_opening_that_cannot_be_associated_with_any_wall_is_reported_separately(rec):
    graph = register("DEPENDENCY_AND_BLOCKING_REGISTER")["BY_FLOOR"]
    stray = [u for g in graph.values() for u in g["UNASSOCIATED_OPENINGS"]]
    for u in stray:
        assert u["WHY"] and u["RISK"]
    questions = [q for q in rec["UNRESOLVED"]
                 if q["KIND"] == "UNRESOLVED_OPENING_NOT_ASSOCIATED_WITH_ANY_WALL"]
    assert len(questions) == len(stray)


# ------------------------------------------------------------------ space assembly, graded honestly
def test_the_space_assembly_outcome_distinguishes_ran_from_validated(rec):
    val = register("SPACE_ASSEMBLY_VALIDATION")["BY_FLOOR"]
    from engine.qs_core import space_validation as SV
    for floor, v in val.items():
        assert v["OUTCOME"] in (SV.VALIDATED, SV.NO_CASE, SV.CONTRADICTION), floor
        assert v["OUTCOME"] != SV.CONTRADICTION, (floor, v["MULTI_COMPONENT_DETAIL"])
        assert v["SINGLE_COMPONENT_SPACES"] + v["MULTI_COMPONENT_SPACES"] == v["SPACES"]


def test_fragments_kept_apart_carry_the_evidence_that_kept_them_apart(rec):
    val = register("SPACE_ASSEMBLY_VALIDATION")["BY_FLOOR"]
    apart = [k for v in val.values() for k in v["ADJACENT_FRAGMENTS_KEPT_SEPARATE"]]
    assert apart
    for k in apart:
        assert k["RELATION"] and k["WHY"]


# ------------------------------------------------------------------ the independent gate and the metamorphic
def test_the_independent_acceptance_gate_passes_on_every_floor(rec):
    assert rec["ACCEPTANCE_GATE"]["ALL_PASS"], rec["ACCEPTANCE_GATE"]["BLOCKERS"]
    for floor, g in rec["ACCEPTANCE_GATE"]["BY_FLOOR"].items():
        assert g["OF"] == 10 and g["PASSED"] == 10, (floor, g["BLOCKERS"])
        assert {c["CHECK"] for c in g["CHECKS"]} == {f"A{i}" for i in range(1, 11)}


def test_the_quantities_do_not_move_when_the_real_drawing_is_described_differently(rec):
    for key, rt in rec["METAMORPHIC"].items():
        assert rt["EQUIVALENT"], (key, rt["BY_FLOOR"])


def test_the_engine_carries_no_project_name_or_known_total(rec):
    audit = rec["ANTI_CALIBRATION_AUDIT"]
    assert audit["PASS"], audit
    assert audit["TOKEN_SCAN"]["RESULT"]["HITS"] == []
    assert audit["PROJECT_BRANCH_SCAN"]["HITS"] == []
    assert audit["WHAT_IT_DOES_NOT_PROVE"]


def test_the_package_provenance_keeps_four_different_things_apart(rec):
    p = rec["PROVENANCE"]
    assert p["GENERATING_COMMIT"]["SHA"]
    assert p["FROZEN_ARTIFACT"]["SHA256"] == FROZEN_SHA
    assert set(p) >= {"GENERATING_COMMIT", "SOURCE_ARTIFACT_COMMIT", "FROZEN_ARTIFACT", "PACKAGING_COMMIT"}


def test_the_invariants_hold_on_the_real_drawing(rec):
    assert rec["INVARIANTS"]["ALL_PASS"], rec["INVARIANTS"]["FAILURES"]
    assert rec["INVARIANTS"]["OF"] >= 3 * 20


def test_an_identical_rerun_changes_no_identity(rec):
    summary = rec["LINEAGE_ON_AN_IDENTICAL_RERUN"]
    assert set(summary) == {"UNCHANGED"}, summary


def test_the_question_register_is_finite_and_every_question_names_what_it_blocks(rec):
    qs = rec["UNRESOLVED"]
    assert qs
    for q in qs:
        assert q["QUESTION"] and q["KIND"] and q["BLOCKS"] and q["EVIDENCE"]


def test_the_gate_would_reject_this_output_if_a_figure_were_smuggled_in(rec):
    """The gate that passes here has to be the same gate that fails on a published blocked subtotal."""
    doc = {"WALL_ROWS": register("OPENING_TO_HOST_REGISTER")["WALL_LINE_QUANTITIES"]["GROUND"],
           "PUBLISHED_QUANTITIES": [{"REF": "BLOCKWORK", "QUANTITY": 999.9}]}
    graded = acceptance.grade(doc)
    assert not graded["ALL_PASS"]
    assert any(b["CHECK"] == "A1" for b in graded["BLOCKERS"])
