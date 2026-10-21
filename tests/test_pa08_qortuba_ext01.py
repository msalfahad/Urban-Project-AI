"""PA08_QORTUBA_EXTERNAL_RECONCILIATION_01: the rules that make an external comparison worth anything.

A benchmark comparison is easy to fake, in two directions.  A transcription can drift toward the engine's answer, and the
engine can be quietly edited until it matches.  These tests assert that neither happened, and that the phase's own arithmetic
is honest about what the contractor sheet does and does not say.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.ext01 import reconcile as RC, transcribe as TR

EXT = Path(PR.OUT_DIR) / "pa08_qortuba_ext01"
R3 = Path(PR.OUT_DIR) / "pa08_qortuba_r3"
SRC = Path("research/qs_wall_treatment_01/pa08/qortuba/ext01")


def _mods(path):
    tree = ast.parse(Path(path).read_text("utf-8"))
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.add(n.module)
    return out


def test_the_transcription_cannot_have_been_shaped_by_the_engine():
    """The module that reads the contractor sheet imports no engine and no R3 code, so no engine number was in scope."""
    mods = _mods(SRC / "transcribe.py")
    assert not any("engine" in m or "r3" in m or "r2" in m or "r1" in m for m in mods), sorted(mods)


def test_no_engine_quantity_is_written_into_the_contractor_registers():
    comm = json.loads((EXT / "QORTUBA_CONTRACTOR_COMMERCIAL_REGISTER.json").read_text("utf-8"))
    reg = json.loads((R3 / "PA08_QORTUBA_R3_FLOOR_MEASUREMENT_REGION_REGISTER.json").read_text("utf-8"))
    engine_numbers = {r["AREA_M2"]["VALUE"] for r in reg["ROWS"]}
    printed = {r["QUANTITY"] for r in comm["ROWS"]} | {r["NET"] for r in comm["ROWS"]}
    assert not (engine_numbers & printed), "a contractor row carries an engine area verbatim"


def test_the_kiyal_register_is_empty_because_the_kiyal_was_not_supplied():
    """An empty register is the honest artifact.  Decomposing a summary into rooms would be inventing the source."""
    k = json.loads((EXT / "QORTUBA_CONTRACTOR_KIYAL_REGISTER.json").read_text("utf-8"))
    assert k["COUNT"] == 0 and k["STATUS"] == "SOURCE_NOT_PROVIDED"
    assert k["MISSING_SOURCES"] and k["WHAT_THE_KIYAL_WOULD_HAVE_ANSWERED"]


def test_the_transcription_was_frozen_before_the_comparison():
    fr = json.loads((EXT / "CONTRACTOR_TRANSCRIPTION_FREEZE.json").read_text("utf-8"))
    for n, h in fr["CONTENTS"].items():
        assert RC._sha(EXT / f"{n}.json") == h, f"{n} changed after it was frozen"


def test_the_reconciliation_leaves_every_r3_artifact_byte_for_byte():
    _, _, bad = RC.r3_fingerprint()
    assert bad == [], bad


def test_contractor_arithmetic_is_preserved_never_corrected_in_place():
    """Where the sheet's amount does not follow from its printed quantity, both are kept and the difference is stated."""
    comm = TR.commercial_register()
    for r in comm["ROWS"]:
        assert r["AMOUNT"] == next(x["AMOUNT"] for x in TR.COMMERCIAL_ROWS if x["ROW_ID"] == r["ROW_ID"])
        if r["ARITHMETIC_STATUS"] == "CONSISTENT_WITH_AN_UNROUNDED_QUANTITY":
            assert r["CONTRACTOR_ARITHMETIC_DIFFERENCE"] is not None and r["IMPLIED_UNROUNDED_NET"] is not None
            assert abs(r["IMPLIED_UNROUNDED_NET"] - r["NET"]) <= 0.005


def test_the_sheet_total_reproduces_from_its_own_rows():
    comm = TR.commercial_register()
    assert comm["TOTAL_CHECK"]["STATUS"] == "EXACT", comm["TOTAL_CHECK"]


def test_the_profile_difference_is_fully_accounted_for():
    """Every metre of the profile-to-skirting gap is named.  An unexplained remainder would mean the diagnosis is incomplete."""
    p = json.loads((EXT / "QORTUBA_EXT01_PROFILE_RECONCILIATION.json").read_text("utf-8"))
    d = p["DECOMPOSITION"]
    assert d["EXACT"] and abs(d["RESIDUAL_LM"]) < 5e-4, d
    assert abs(d["R3_SKIRTING_DRY_NET_LM"] + d["PROFILE_ONLY_LENGTH_LM"] - d["R3_PROFILE_TOTAL_LM"]) < 5e-4
    for s in p["PROFILE_ONLY_SEGMENTS"]:
        assert s["CLASSIFICATION"] in RC.PROFILE_SEGMENT_CLASSES, s["CLASSIFICATION"]


def test_no_corrected_profile_length_is_released_as_a_quantity():
    """The corrected arithmetic locates the defect.  It is not a quantity, and it never becomes one in this phase."""
    p = json.loads((EXT / "QORTUBA_EXT01_PROFILE_RECONCILIATION.json").read_text("utf-8"))
    assert "NOT_APPLIED" in p["IF_THE_TRADE_RULE_FOLLOWED_THE_OWNER"]
    assert p["ACTION"] == "ENGINE_TRADE_RULE_FIX_REQUIRED" and p["DEFER"]
    pf = json.loads((R3 / "PA08_QORTUBA_R3_PROFILE_MEASUREMENT_REGISTER.json").read_text("utf-8"))
    assert pf["SUBTOTAL_LM"] == p["AGGREGATE"]["ENGINE_VALUE_LM"], "R3's profile total was altered"


def test_an_implied_height_is_diagnostic_and_never_source_established():
    w = json.loads((EXT / "QORTUBA_EXT01_WET_ROOM_RECONCILIATION.json").read_text("utf-8"))
    h = w["IMPLIED_CONTRACTOR_HEIGHT"]
    assert h["STATE"] == "DERIVED_FROM_CONTRACTOR_KIYAL"
    for q in ("NOT_SOURCE_ESTABLISHED", "NOT_AN_URBAN_RULE", "NOT_A_QORTUBA_DRAWING_FACT"):
        assert q in h["QUALIFIERS"]
    assert len(h["SCENARIOS"]) >= 3, "one implied height presented alone reads as a finding"
    wet = json.loads((R3 / "PA08_QORTUBA_R3_WET_ROOM_GEOMETRY_REGISTER.json").read_text("utf-8"))
    assert all(r["WALL_TILE_AREA_M2"]["STATE"] == "NOT_ESTABLISHED" for r in wet["ROWS"])


def test_no_room_level_agreement_is_claimed_without_a_room_level_source():
    f = json.loads((EXT / "QORTUBA_EXT01_CERAMIC_FLOORING_RECONCILIATION.json").read_text("utf-8"))
    assert f["ROOM_LEVEL_COMPARISONS_POSSIBLE"] == 0
    for r in f["BY_ROOM"]:
        assert r["CONTRACTOR_KIYAL_AREA_M2"] is None and r["DELTA_M2"] is None
        assert r["ACTION"] == "MORE_SOURCE_REQUIRED"
    m = json.loads((EXT / "QORTUBA_EXT01_EXTERNAL_VALIDATION_METRICS.json").read_text("utf-8"))
    a = m["A_GEOMETRY_AGREEMENT"]
    assert a["MATCH"] == 0 and a["WITHIN_TOLERANCE"] == 0 and a["NOT_COMPARABLE"] == 9


def test_the_metrics_report_separate_axes_and_no_single_score():
    m = json.loads((EXT / "QORTUBA_EXT01_EXTERNAL_VALIDATION_METRICS.json").read_text("utf-8"))
    assert "NO_SINGLE_SCORE" in m
    for axis in ("A_GEOMETRY_AGREEMENT", "B_FLOORING_SCOPE_AGREEMENT", "C_SKIRTING_AGREEMENT",
                 "D_PROFILE_AGREEMENT", "E_SAFE_REFUSAL", "F_SILENT_WRONG_QUANTITY"):
        assert axis in m, axis
    scored = [k for k in m if k not in ("ARTIFACT", "NO_SINGLE_SCORE")
              and ("ACCURACY" in k.upper() or "SCORE" in k.upper())]
    assert not scored, scored


def test_the_silent_wrong_count_holds_only_demonstrated_items():
    """Unexplained differences stay out of the count.  Padding it is as dishonest as hiding from it."""
    m = json.loads((EXT / "QORTUBA_EXT01_EXTERNAL_VALIDATION_METRICS.json").read_text("utf-8"))
    f = m["F_SILENT_WRONG_QUANTITY"]
    assert f["COUNT"] == len(f["ITEMS"]) == 1
    it = f["ITEMS"][0]
    assert it["EXCEPTION_RAISED"] is False and it["GEOMETRY_CORRECT"] is True
    assert f["UNRESOLVED_CANDIDATES"] == 2 and f["UNRESOLVED_CANDIDATE_NOTE"]


def test_every_a22_row_carries_three_bases_and_a_named_action():
    a = json.loads((EXT / "A22_QORTUBA_EXTERNAL_RECONCILIATION.json").read_text("utf-8"))
    assert a["COUNT"] >= 6
    for r in a["ROWS"]:
        assert r["ACTION"] in RC.ACTIONS, r["ACTION"]
        assert all(c in RC.DIFFERENCE_CLASSES for c in r["CLASSIFICATION"]), r["CLASSIFICATION"]
        assert "ENGINE_BASIS" in r and "CONTRACTOR_KIYAL_BASIS" in r and "COMMERCIAL_BASIS" in r
        assert r["ROOT_CAUSE"] and len(r["ROOT_CAUSE"]) > 20, r["ITEM_ID"]
        assert r["CLASSIFICATION"] != ["UNRESOLVED"] or r["ROOT_CAUSE"], "doesn't match is not a classification"


def test_no_engine_fix_was_made_in_this_phase():
    fr = json.loads((EXT / "FREEZE_PA08_QORTUBA_EXTERNAL_RECONCILIATION_01.json").read_text("utf-8"))
    assert fr["ENGINE_CHANGED_IN_THIS_PHASE"].startswith("NONE")
    r4 = json.loads((EXT / "QORTUBA_EXT01_RECOMMENDED_R4_FIXES.json").read_text("utf-8"))
    assert r4["IMPLEMENTED_IN_THIS_PHASE"] == "NONE"
    assert all(x["DO_NOT_IMPLEMENT_NOW"] for x in r4["ROWS"])


def test_the_freeze_records_that_r3_was_not_rewritten():
    fr = json.loads((EXT / "FREEZE_PA08_QORTUBA_EXTERNAL_RECONCILIATION_01.json").read_text("utf-8"))
    assert fr["R3_NOT_REWRITTEN"]["HASHES_VERIFIED_BEFORE_AND_AFTER"] and fr["R3_NOT_REWRITTEN"]["MISMATCHES"] == []
    r3 = json.loads((R3 / "FREEZE_PA08_QORTUBA_R3.json").read_text("utf-8"))
    assert fr["R3_NOT_REWRITTEN"]["FREEZE_DIGEST"] == r3["DIGEST"]
