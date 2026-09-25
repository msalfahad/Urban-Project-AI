"""The R6 engine, run over a real drawing, and graded by the independent gate.

These tests read the registers the R6 regression produced.  Every one of them checks BEHAVIOUR - that a door
the source names is admitted whether or not its host can be found, that depth arrives from a host and never
from an extractor's grid, that material is never read off a shape, that a superseded owner input does not win,
that one unanswered fact is one question - and none of them checks a quantity against a number reported
earlier.  Where a frozen figure appears at all, it is to prove the frozen artifact was not touched.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from engine.qs_core import acceptance, admission as AD, evidence as EV, invariants, masonry as MA
from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import regression_r6 as RG

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
FROZEN_SHA = "7e9a3eba636ea95b77fce2bbb7dccad79d6971047af455bb2f542ee62165493f"
REC = OUT / "ALRASHED_GENERIC_ENGINE_VALIDATION_R6.json"

pytestmark = pytest.mark.skipif(not REC.exists(),
                                reason="run research.qs_wall_treatment_01.pa09.alrashed.regression_r6 first")


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


def test_no_blocked_row_reaches_any_published_subtotal(rec):
    for floor, pub in rec["FINAL_VERSUS_BLOCKED"]["BY_FLOOR"].items():
        if not pub:
            continue
        for key, sub in pub["SUBTOTALS"].items():
            if sub["FINAL_QUANTITY"] is not None:
                assert sub["ROWS_BLOCKED"] == 0, (floor, key)


# ------------------------------------------------------------------ §1, §2  existence is not hosting
def test_every_opening_the_source_names_is_admitted_as_a_physical_opening(rec):
    pop = register("OPENING_ADMISSION_REGISTER")["BY_FLOOR"]
    for floor, p in pop.items():
        named = set(p["NAMED_BY_THE_SOURCE"])
        physical = set(p["PHYSICAL_OPENING_REFS"])
        assert named and named <= physical, (floor, sorted(named - physical))


def test_a_named_door_whose_host_is_unresolved_keeps_its_place_in_the_population(rec):
    pop = register("OPENING_ADMISSION_REGISTER")["BY_FLOOR"]
    unresolved = [c for p in pop.values() for c in p["POPULATION"]
                  if c["CLASSIFICATION"] == AD.OPENING_CONFIRMED_HOST_CONFIRMED or
                  c["CLASSIFICATION"] == AD.OPENING_CONFIRMED_HOST_UNRESOLVED]
    assert unresolved, "the drawing does carry named openings"
    for c in unresolved:
        assert c["EXISTENCE"] == AD.EXISTS_CONFIRMED
        assert any(p["KIND"] in AD.NAMING_PROVENANCE for p in c["PROVENANCE"]), c["CANDIDATE_REF"]


def test_failing_to_overlap_wall_material_is_never_evidence_against_an_opening(rec):
    pop = register("OPENING_ADMISSION_REGISTER")["BY_FLOOR"]
    for p in pop.values():
        for c in p["POPULATION"]:
            for e in c["EVIDENCE"]:
                text = json.dumps(e).lower()
                assert "no wall material" not in text or c["EXISTENCE"] != AD.DOES_NOT_EXIST


def test_the_five_published_classes_are_the_ones_the_review_asked_for(rec):
    pop = register("OPENING_ADMISSION_REGISTER")
    assert set(pop["CLASSES"]) >= {AD.OPENING_CONFIRMED_HOST_CONFIRMED,
                                   AD.OPENING_CONFIRMED_HOST_UNRESOLVED,
                                   AD.OPENING_CANDIDATE_UNRESOLVED, AD.NON_OPENING_GAP, AD.DRAWING_NOISE}


# ------------------------------------------------------------------ §3  source features, depth after hosting
def test_the_source_opening_objects_carry_no_depth_and_no_rectangle(rec):
    src = register("SOURCE_OPENING_POPULATION_REGISTER")["BY_FLOOR"]
    objects = [o for floor in src.values() for o in floor]
    assert objects
    for o in objects:
        assert set(o) >= {"CENTRE", "SPAN_M", "AXIS", "BLOCK_REF", "LAYER"}
        assert "DEPTH_M" not in o and "RECT" not in o, o


def test_a_resolved_host_supplies_the_depth_and_says_so(rec):
    hosts = register("OPENING_TO_HOST_REGISTER")["BY_FLOOR"]
    confirmed = [r for f in hosts.values() for r in f["REGISTER"] if r["HOST_STATUS"] == "HOST_CONFIRMED"]
    assert confirmed
    for r in confirmed:
        assert r["DEPTH_M"] == r["HOST_THICKNESS_M"]
        assert r["DEPTH_SOURCE"].startswith("the host wall's own thickness")


def test_a_confirmed_opening_can_prove_two_collinear_segments_are_one_wall(rec):
    hosts = register("OPENING_TO_HOST_REGISTER")["BY_FLOOR"]
    bracketed = [r for f in hosts.values() for r in f["REGISTER"]
                 if r.get("RELATION") == "BRACKETED_BY_TWO_COLLINEAR_WALL_ENDS"]
    assert bracketed, "the drawing does stop its walls at the jambs"
    for r in bracketed:
        assert r["HOST_BRACKETING_SEGMENT_REFS"] and len(r["HOST_BRACKETING_SEGMENT_REFS"]) == 2
    deductions = register("OPENING_TO_HOST_REGISTER")["DEDUCTION_REGISTER"]
    for floor, reg in deductions.items():
        for o in reg["REGISTER"]:
            if o["HOST_ASSIGNMENT_STATUS"] == "HOST_ASSIGNED":
                assert o["HOST_COMPONENT_REF"], (floor, o["OPENING_REF"])


# ------------------------------------------------------------------ §4  real ambiguity is preserved
def test_an_unresolved_host_lists_its_competing_groups_and_their_scores(rec):
    hosts = register("OPENING_TO_HOST_REGISTER")["BY_FLOOR"]
    open_ones = [r for f in hosts.values() for r in f["REGISTER"] if r["HOST_STATUS"] != "HOST_CONFIRMED"]
    assert open_ones, "the drawing does contain openings the geometry does not settle"
    for r in open_ones:
        assert r["HOST_SEGMENT_REFS"] == [] and r["DEPTH_M"] is None
        assert r["WHY"]
        for c in r["CANDIDATES"]:
            assert c["SCORE"] is not None and c["EVIDENCE"]["WEIGHTS"]


def test_proximity_is_never_the_reason_a_host_was_chosen(rec):
    reg = register("OPENING_TO_HOST_REGISTER")
    assert reg["WEIGHTS"]["PROXIMITY"] <= 0.05
    for f in reg["BY_FLOOR"].values():
        for r in f["REGISTER"]:
            if r["HOST_STATUS"] == "HOST_CONFIRMED":
                assert r["CANDIDATES"][0]["EVIDENCE"]["STRUCTURAL_FIT"] >= f["STRUCTURAL_FIT_MIN"]


# ------------------------------------------------------------------ §5  conservation
def test_no_named_source_object_is_lost_between_admission_hosting_and_publication(rec):
    pop = register("OPENING_ADMISSION_REGISTER")["BY_FLOOR"]
    hosts = register("OPENING_TO_HOST_REGISTER")
    for floor, p in pop.items():
        check = invariants.named_source_openings_are_conserved(
            p, hosts["BY_FLOOR"][floor], hosts["DEDUCTION_REGISTER"][floor])
        assert check["PASS"], (floor, check["RESULT"])


def test_host_failure_never_retracts_an_admitted_object(rec):
    pop = register("OPENING_ADMISSION_REGISTER")["BY_FLOOR"]
    hosts = register("OPENING_TO_HOST_REGISTER")["BY_FLOOR"]
    for floor, p in pop.items():
        check = invariants.existence_is_not_retracted_by_host_failure(p, hosts[floor])
        assert check["PASS"], (floor, check["RESULT"])


# ------------------------------------------------------------------ §6, §11  questions and impacts
def test_one_unanswered_fact_is_one_root_question(rec):
    q = register("ROOT_QUESTION_REGISTER")
    ids = [r["ROOT_QUESTION_ID"] for r in q["ROOT_QUESTIONS"]]
    assert ids and len(ids) == len(set(ids))
    subjects = [(r["KIND"], r["SUBJECT_REF"]) for r in q["ROOT_QUESTIONS"]]
    assert len(subjects) == len(set(subjects))
    assert q["IMPACTS_WITHOUT_A_ROOT_QUESTION"] == []


def test_a_dependency_impact_is_a_consequence_and_never_another_question(rec):
    impacts = register("DEPENDENCY_IMPACT_REGISTER")["DEPENDENCY_IMPACTS"]
    roots = {r["ROOT_QUESTION_ID"] for r in register("ROOT_QUESTION_REGISTER")["ROOT_QUESTIONS"]}
    assert impacts and len(impacts) > len(roots)
    for i in impacts:
        assert i["ROOT_QUESTION_ID"] in roots
        assert i["NODE"] and i["EFFECT"]


def test_one_answer_about_a_wall_type_closes_every_wall_of_that_type(rec):
    """Asking per line would report fifty-four questions where the source has one gap."""
    q = register("ROOT_QUESTION_REGISTER")
    material = [r for r in q["ROOT_QUESTIONS"] if r["KIND"] == "WALL_MATERIAL_NOT_ESTABLISHED"]
    assert material
    for r in material:
        assert r["SUBJECT_KIND"] == "THICKNESS_FAMILY"
        assert r["SUBJECT_REF"].startswith("THICKNESS_FAMILY::")


# ------------------------------------------------------------------ §7  evidence lifecycle
def test_a_superseded_owner_input_does_not_answer_inside_the_scope_it_was_retired_in(rec):
    life = register("EVIDENCE_CLAIM_LIFECYCLE_REGISTER")
    superseded = [c for c in life["CLAIMS"] if c["STATUS"] == EV.SUPERSEDED]
    assert superseded, "the project does record a supersession"
    for c in superseded:
        assert c["SUPERSEDED_BY"] and c["SUPERSEDED_REASON"] and c["SCOPE"]
    hosts = register("OPENING_TO_HOST_REGISTER")["DEDUCTION_REGISTER"]
    retired = {c["REFERENCE"] for c in superseded}
    for floor, reg in hosts.items():
        for o in reg["REGISTER"]:
            h = (o.get("ADMISSION") or {}).get("HEIGHT_EVIDENCE") or {}
            if h.get("STATUS") == EV.ESTABLISHED and h.get("REFERENCE") in retired:
                ineligible = {i["REFERENCE"] for i in h.get("INELIGIBLE", [])}
                assert h["REFERENCE"] not in ineligible, (floor, o["OPENING_REF"])
                raise AssertionError((floor, o["OPENING_REF"], "a retired claim answered a height"))


def test_every_established_height_names_the_record_that_answered_it(rec):
    hosts = register("OPENING_TO_HOST_REGISTER")["DEDUCTION_REGISTER"]
    for floor, reg in hosts.items():
        for o in reg["REGISTER"]:
            h = (o.get("ADMISSION") or {}).get("HEIGHT_EVIDENCE") or {}
            if h.get("STATUS") == EV.ESTABLISHED:
                assert h.get("REFERENCE") and h.get("SOURCE"), (floor, o["OPENING_REF"])


# ------------------------------------------------------------------ §8  categories from host rooms
def test_no_single_category_is_asserted_for_every_window(rec):
    cats = register("WINDOW_ROOM_AND_CATEGORY_REGISTER")["BY_FLOOR"]
    resolved = [r for f in cats.values() for r in f["REGISTER"]
                if r["CATEGORY"]["STATUS"] == "CATEGORY_RESOLVED"]
    assert resolved, "some windows do resolve"
    distinct = {r["CATEGORY"]["CATEGORY"] for r in resolved}
    rooms = {r["ROOM"]["LABEL"] for r in resolved}
    assert len(distinct) > 1 or len(rooms) == 1, (distinct, rooms)
    for r in resolved:
        assert r["ROOM"]["ROOM_ID"] and r["ROOM"]["STATUS"] == "HOST_ROOM_RESOLVED"


def test_a_window_whose_room_is_ambiguous_publishes_no_category(rec):
    cats = register("WINDOW_ROOM_AND_CATEGORY_REGISTER")["BY_FLOOR"]
    for f in cats.values():
        for r in f["REGISTER"]:
            if r["ROOM"]["STATUS"] != "HOST_ROOM_RESOLVED":
                assert r["CATEGORY"]["CATEGORY"] is None, r["OPENING_REF"]
                assert r["ROOM"]["WHY"]
                assert r["ROOM"]["CANDIDATES"] or r["ROOM"]["STATUS"] == "HOST_ROOM_NOT_FOUND"


# ------------------------------------------------------------------ §9  geometry is not material
def test_a_thickness_family_appearing_twice_is_not_material_proof(rec):
    mat = register("WALL_MATERIAL_REGISTER")["BY_FLOOR"]
    for floor, m in mat.items():
        for row in m["REGISTER"]:
            assert row["THICKNESS_FAMILY_PROVES_MATERIAL"] is False
            if row["MATERIAL_IDENTITY"] != MA.MATERIAL_UNKNOWN:
                assert row["MATERIAL_EVIDENCE"], (floor, row["COMPONENT_REF"])


def test_the_two_identity_axes_are_reported_separately(rec):
    geom_reg = register("WALL_GEOMETRY_REGISTER")["BY_FLOOR"]
    mat = register("WALL_MATERIAL_REGISTER")["BY_FLOOR"]
    for floor in geom_reg:
        for row in geom_reg[floor]["REGISTER"]:
            assert not any(k.startswith("MATERIAL") for k in row), (floor, row["COMPONENT_REF"])
        assert set(geom_reg[floor]["COUNTS"]) <= set(MA.GEOMETRY_IDENTITIES)
        assert set(mat[floor]["COUNTS"]) <= set(MA.MATERIAL_IDENTITIES)


def test_nothing_is_billed_as_masonry_without_a_document_that_states_a_material(rec):
    quantities = register("OPENING_TO_HOST_REGISTER")["WALL_LINE_QUANTITIES"]
    for floor, rows in quantities.items():
        for r in rows:
            if r["STATUS"] == "FINAL_QUANTITY_AVAILABLE":
                assert r["WALL_MATERIAL_IDENTITY"] in MA.BILLABLE_MATERIAL, (floor, r["COMPONENT_REF"])
                assert r["MATERIAL_EVIDENCE"], (floor, r["COMPONENT_REF"])


# ------------------------------------------------------------------ §11  the two status counts agree
def test_the_row_categories_and_the_line_blocking_reconcile(rec):
    fb = rec["FINAL_VERSUS_BLOCKED"]
    assert fb["HOW_THE_TWO_COUNTS_AGREE"]["RECONCILES"], fb["HOW_THE_TWO_COUNTS_AGREE"]
    cats = fb["ROW_CATEGORIES"]
    assert cats["FINAL"] + cats["BLOCKED"] + cats["EXCLUDED"] == cats["OF"]
    assert fb["WALL_LINE_STATUS"]["OF"] == cats["OF"]


def test_an_excluded_band_does_not_block_a_subtotal(rec):
    excluded = rec["FINAL_VERSUS_BLOCKED"]["EXCLUDED_ROWS"]
    assert excluded, "the drawing does contain bands that are not walls"
    for row in excluded:
        assert row["WALL_GEOMETRY_IDENTITY"] == MA.NON_WALL_ARTEFACT
        assert row["WHY"] and row["REASON_KIND"]


# ------------------------------------------------------------------ the gate, the metamorphic and provenance
def test_the_independent_acceptance_gate_passes_on_every_floor(rec):
    assert rec["ACCEPTANCE_GATE"]["ALL_PASS"], rec["ACCEPTANCE_GATE"]["BLOCKERS"]
    for floor, g in rec["ACCEPTANCE_GATE"]["BY_FLOOR"].items():
        assert g["OF"] == 21 and g["PASSED"] == 21, (floor, g["BLOCKERS"])
        assert {c["CHECK"] for c in g["CHECKS"]} == {f"A{i}" for i in range(1, 22)}


def test_the_same_gate_rejects_a_smuggled_figure(rec):
    doc = {"WALL_ROWS": register("OPENING_TO_HOST_REGISTER")["WALL_LINE_QUANTITIES"]["GROUND"],
           "PUBLISHED_QUANTITIES": [{"REF": "BLOCKWORK", "QUANTITY": 999.9}]}
    graded = acceptance.grade(doc)
    assert not graded["ALL_PASS"]
    assert any(b["CHECK"] == "A1" for b in graded["BLOCKERS"])


def test_the_answers_do_not_move_when_the_real_drawing_is_described_differently(rec):
    for key, rt in rec["METAMORPHIC"].items():
        assert rt["EQUIVALENT"], (key, rt["BY_FLOOR"])


def test_the_engine_carries_no_project_name_room_reference_or_known_total(rec):
    audit = rec["ANTI_CALIBRATION_AUDIT"]
    assert audit["PASS"], audit
    assert audit["TOKEN_SCAN"]["RESULT"]["HITS"] == []
    assert audit["PROJECT_BRANCH_SCAN"]["HITS"] == []
    assert audit["WHAT_IT_DOES_NOT_PROVE"]


def test_the_invariants_hold_on_the_real_drawing(rec):
    assert rec["INVARIANTS"]["ALL_PASS"], rec["INVARIANTS"]["FAILURES"]
    assert rec["INVARIANTS"]["OF"] >= 3 * 20


def test_an_identical_rerun_changes_no_identity(rec):
    assert set(rec["LINEAGE_ON_AN_IDENTICAL_RERUN"]) == {"UNCHANGED"}, \
        rec["LINEAGE_ON_AN_IDENTICAL_RERUN"]


def test_the_provenance_keeps_four_different_things_apart(rec):
    p = rec["PROVENANCE"]
    assert set(p) >= {"GENERATING_COMMIT", "SOURCE_ARTIFACT_COMMIT", "FROZEN_ARTIFACT", "PACKAGING_COMMIT"}
    assert p["FROZEN_ARTIFACT"]["SHA256"] == FROZEN_SHA


def test_the_before_and_after_table_says_what_changed_and_why(rec):
    ba = rec["BEFORE_AND_AFTER"]
    assert ba["OPENINGS"]
    for row in ba["OPENINGS"]:
        assert row["R5_CLASSIFICATION"] and row["R6_CLASSIFICATION"]
        assert row["SOURCE_EVIDENCE_FOR_THE_CHANGE"]
        assert row["AUTOMATIC_OR_QUESTION"] in ("AUTOMATIC", "REMAINS_A_ROOT_QUESTION")


def test_no_quantity_is_published_while_its_dependency_chain_is_open(rec):
    project = rec["FINAL_VERSUS_BLOCKED"]["WHOLE_PROJECT"]
    for key, sub in project["SUBTOTALS"].items():
        if sub["FINAL_QUANTITY"] is None:
            assert sub["WAITING_ON"], key
        else:
            assert sub["ROWS_BLOCKED"] == 0, key
