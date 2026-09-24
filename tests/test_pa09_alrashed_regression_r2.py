"""The generic engine, run over a real drawing.

These tests read the registers the regression produced.  They check behaviour - that every opening went to one
host or to none, that every component ended in exactly one state, that identity survives a rerun - and never that
a quantity matches a number someone reported earlier.  Where they mention a frozen figure at all, it is to prove
the frozen artifact was not touched.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from engine.qs_core import invariants
from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import regression_r2 as RG

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
FROZEN_SHA = "7e9a3eba636ea95b77fce2bbb7dccad79d6971047af455bb2f542ee62165493f"


@pytest.fixture(scope="module")
def rec():
    return json.loads((OUT / "ALRASHED_GENERIC_ENGINE_REGRESSION.json").read_text("utf-8"))


def register(name):
    return json.loads((OUT / f"ALRASHED_{name}.json").read_text("utf-8"))


# ------------------------------------------------------------------ the frozen artifact
def test_the_frozen_takeoff_was_read_and_never_written(rec):
    assert rec["FROZEN_UNCHANGED"]["REWRITTEN"] is False
    assert rec["FROZEN_UNCHANGED"]["SHA256_BEFORE"] == rec["FROZEN_UNCHANGED"]["SHA256_AFTER"] == FROZEN_SHA
    assert hashlib.sha256(RG.FROZEN.read_bytes()).hexdigest() == FROZEN_SHA


# ------------------------------------------------------------------ Problem B on real geometry
def test_every_opening_went_to_one_host_or_to_none(rec):
    for floor, reg in rec["OPENING_REGISTER"].items():
        check = invariants.one_host_per_opening(reg)
        assert check["PASS"], (floor, check["RESULT"])
        assert reg["ASSIGNED_COUNT"] + reg["UNRESOLVED_COUNT"] == reg["OPENING_COUNT"]
        assert reg["ALLOCATION_RULE"].startswith("an opening is deducted from exactly one host")


def test_no_deduction_was_divided_between_wall_lines(rec):
    for floor, reg in rec["OPENING_REGISTER"].items():
        rows = rec["WALL_LINES"][floor]
        assert invariants.deductions_match_band_by_band(reg, rows, 1e-9)["PASS"], floor
        assert invariants.unresolved_never_allocated(reg, rows, 1e-9)["PASS"], floor


def test_a_floor_with_an_unresolved_host_blocks_its_wall_split(rec):
    for floor, reg in rec["OPENING_REGISTER"].items():
        if reg["UNRESOLVED_COUNT"] == 0:
            continue
        rows = rec["WALL_LINES"][floor]
        assert all(r["STATUS"] != "FINAL_QUANTITY_AVAILABLE" for r in rows), floor


def test_every_unresolved_opening_became_a_question_with_its_quantity(rec):
    unresolved = sum(r["UNRESOLVED_COUNT"] for r in rec["OPENING_REGISTER"].values())
    questions = [q for q in rec["UNRESOLVED"] if q["KIND"] == "HOST_WALL_UNRESOLVED"]
    assert len(questions) == unresolved
    for q in questions:
        assert q["EVIDENCE"] and q["BLOCKS"]


# ------------------------------------------------------------------ Problem C on real geometry
def test_every_component_ended_in_exactly_one_state(rec):
    for floor, membership in rec["MEMBERSHIP_REGISTER"].items():
        check = invariants.every_component_resolved_once(membership)
        assert check["PASS"], (floor, check["RESULT"])


def test_no_wall_material_or_column_became_floor(rec):
    for floor, membership in rec["MEMBERSHIP_REGISTER"].items():
        assert invariants.no_wall_material_as_floor(membership)["PASS"], floor


def test_a_room_label_covers_the_whole_room_it_names(rec):
    for floor in rec["SEAM_REGISTER"]:
        check = invariants.continuous_floor_is_one_space(rec["SEAM_REGISTER"][floor],
                                                         rec["MEMBERSHIP_REGISTER"][floor])
        assert check["PASS"], (floor, check["RESULT"])


def test_a_gap_the_drawing_does_not_explain_is_surfaced_rather_than_merged(rec):
    seams = [s for floor in rec["SEAM_REGISTER"] for s in rec["SEAM_REGISTER"][floor]]
    assert seams, "a real plan has seams between its components"
    candidates = [s for s in seams if s["RELATION"] == "CANDIDATE_OPENING_REVIEW_REQUIRED"]
    assert candidates, "this drawing spans gaps in its wall lines; they must not be read as open floor"
    for s in candidates:
        assert s["SHARES"]["CANDIDATE_OPENING"] > 0.5


def test_spaces_are_reported_with_their_evidence_and_their_doubts(rec):
    spaces = [s for floor in rec["SPACES"] for s in rec["SPACES"][floor]]
    assert spaces
    for s in spaces:
        assert s["EVIDENCE"]
        assert s["LABEL_STATUS"] in ("NAMED", "UNNAMED_ON_DRAWING", "CONFLICTING_LABELS")
        if s["LABEL_STATUS"] == "CONFLICTING_LABELS":
            assert s["STATUS"] == "UNRESOLVED" and s["LABEL"] is None


# ------------------------------------------------------------------ Problem A on real geometry
def test_an_identical_rerun_changes_no_identity(rec):
    summary = rec["LINEAGE_ON_AN_IDENTICAL_RERUN"]
    assert set(summary) == {"UNCHANGED"}, summary
    assert summary["UNCHANGED"] > 100


def test_the_lineage_register_names_every_entity_it_carried(rec):
    reg = register("ENTITY_LINEAGE_REGISTER")
    assert reg["SUMMARY"] == rec["LINEAGE_ON_AN_IDENTICAL_RERUN"]
    for r in reg["RECORDS"][:50]:
        assert r["PERSISTENT_ID"] and r["STATE"]


# ------------------------------------------------------------------ the engine stays generic
def test_the_adapter_declares_its_source_parameters_and_the_engine_holds_none_of_them(rec):
    p = rec["DECLARED_SOURCE_PARAMETERS"]
    assert set(p) >= {"TOLERANCE_M", "SLIVER_MIN_DIMENSION_M", "MAX_OPENING_SPAN_M", "WALL_HEIGHT_M"}
    assert "argument to the engine" in p["NOTE"]
    core = sorted(Path("engine/qs_core").glob("*.py"))
    check = invariants.no_comparison_input(core, ["ALRASHED", "16-11-2025", "AL RASHED"])
    assert check["PASS"], check["RESULT"]["HITS"]

    # and the source parameters reach the engine as arguments with no defaults to fall back on
    import inspect
    from engine.qs_core import pipeline as pl
    sig = inspect.signature(pl.run)
    assert sig.parameters["max_opening_span"].default is inspect.Parameter.empty
    assert sig.parameters["wall_geometry_includes_openings"].default is None
    with pytest.raises(ValueError):
        pl.run({"COMPONENTS": [], "BARRIERS": [], "OPENINGS": [], "LABELS": [], "REVISION": "X",
                "TOLERANCE_M": 0.005, "SLIVER_MIN_DIMENSION_M": 0.3}, max_opening_span=1.0, wall_height=3.0)


def test_all_invariants_passed_on_the_real_drawing(rec):
    assert rec["INVARIANTS"]["ALL_PASS"], rec["INVARIANTS"]["FAILURES"]
    assert rec["INVARIANTS"]["OF"] >= 30


def test_the_comparison_is_labelled_as_comparison_and_carries_a_trace(rec):
    c = rec["COMPARISON_WITH_THE_FROZEN_ARTIFACT"]
    assert "not corrections" in c["RULE"]
    for d in c["BLOCKWORK_DELTAS"]:
        assert d["TRACE"] and d["WHY"]
        assert set(d) >= {"FROZEN_M2", "NEW_M2", "DELTA_M2"}


@pytest.mark.slow
def test_one_floor_re_measured_from_the_drawing_reproduces_its_register(rec):
    ents = RG.G.load()
    res = RG.run_floor(ents, "FIRST")
    stored = rec["OPENING_REGISTER"]["FIRST"]
    assert res["OPENING_REGISTER"]["OPENING_COUNT"] == stored["OPENING_COUNT"]
    assert res["OPENING_REGISTER"]["ASSIGNED_COUNT"] == stored["ASSIGNED_COUNT"]
    assert res["INVARIANTS"]["ALL_PASS"]
