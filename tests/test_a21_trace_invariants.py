"""CI invariants for the A21 trace / source-sufficiency architecture.

These run without the client data: everything here is synthetic or reads
only tracked code. Where a test needs the frozen P7757 artifacts it skips
cleanly when data/ is absent, so CI on a clean checkout still proves the
generic mechanisms.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.a21_trace_sufficiency_01 import parameters as PM
from research.a21_trace_sufficiency_01 import protocol as P
from research.a21_trace_sufficiency_01 import visual_trace as VT

DATA = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")


# ------------------------------------------------------------------
# transform: exact inversion, on a synthetic sheet record
# ------------------------------------------------------------------
def _rec(w=4672, h=6624, tx=280, ty=298, k=0.3308):
    return {"SHEET_ID": "SYN", "ORIGINAL_PDF_PAGE": 1,
            "ORIGINAL_PAGE_COORDINATE_TRANSFORM": {
                "W_orig": w, "H_orig": h, "trim_x0": tx, "trim_y0": ty,
                "scale": k}}


def test_transform_round_trips_exactly():
    tr = VT.SheetTransform(_rec())
    for x, y in ((0, 0), (17.5, 903.25), (1999, 1367), (1234.5, 6.75)):
        ox, oy = tr.to_original(x, y)
        bx, by = tr.to_processed(ox, oy)
        assert abs(bx - x) < 1e-9 and abs(by - y) < 1e-9


def test_transform_is_a_pure_rotation_not_a_reflection():
    # processed top-left after a +90 CCW came from the original's
    # top-RIGHT corner region: x_orig ~ W-1, y_orig ~ 0
    tr = VT.SheetTransform(_rec(tx=0, ty=0, k=1.0))
    ox, oy = tr.to_original(0, 0)
    assert ox == pytest.approx(4671) and oy == pytest.approx(0)


# ------------------------------------------------------------------
# status model: record / locatability / semantic are never collapsed
# ------------------------------------------------------------------
SHEETS = {"GROUND_FLOOR_PLAN": {}}
FIVE = dict(GEOMETRY_STATUS="ESTABLISHED", IDENTITY_STATUS="ESTABLISHED",
            DIMENSION_STATUS="NOT_ESTABLISHED", TREATMENT_STATUS="NOT_ESTABLISHED",
            PARAMETER_STATUS="NOT_ESTABLISHED")


def test_valid_but_non_locatable_trace_is_valid():
    t = dict(TRACE_ID="UNK-01", CASE_ID="C", CLAIM_TYPE="UNRESOLVED_FEATURE",
             SHEET_ID="GROUND_FLOOR_PLAN",
             VISUAL_TRACE_STATUS="TRACE_NOT_ESTABLISHED", **FIVE)
    status, reasons = VT.record_status(t, SHEETS)
    assert status == "VALID" and reasons == []
    assert VT.locatability_status(t) == "NOT_ESTABLISHED"


def test_dimension_geometry_is_the_dimension_fields():
    t = dict(TRACE_ID="DIM-01", CASE_ID="C", CLAIM_TYPE="PRINTED_DIMENSION",
             SHEET_ID="GROUND_FLOOR_PLAN", TEXT="558", VALUE_M=5.58,
             TEXT_BBOX=[1, 1, 9, 9], DIMENSION_LINE_TRACE=[[0, 5], [10, 5]],
             VISUAL_TRACE_STATUS="TRACE_ESTABLISHED", **FIVE)
    assert VT.validate_trace(t, SHEETS) == []
    assert VT.locatability_status(t) == "LOCATABLE"


def test_dimension_chain_without_single_value_is_valid_when_ambiguous():
    t = dict(TRACE_ID="DIM-14", CASE_ID="C", CLAIM_TYPE="PRINTED_DIMENSION",
             SHEET_ID="GROUND_FLOOR_PLAN", TEXT="125 / 120 / 77", VALUE_M=None,
             TEXT_BBOX=[1, 1, 9, 9],
             VISUAL_TRACE_STATUS="TRACE_AMBIGUOUS", **FIVE)
    assert VT.validate_trace(t, SHEETS) == []


def test_established_dimension_must_carry_a_value():
    t = dict(TRACE_ID="DIM-02", CASE_ID="C", CLAIM_TYPE="PRINTED_DIMENSION",
             SHEET_ID="GROUND_FLOOR_PLAN", TEXT="558", VALUE_M=None,
             TEXT_BBOX=[1, 1, 9, 9],
             VISUAL_TRACE_STATUS="TRACE_ESTABLISHED", **FIVE)
    assert any("no VALUE_M" in r for r in VT.validate_trace(t, SHEETS))


def test_vertical_relation_is_a_view_not_an_edit():
    t = dict(CLAIM_TYPE="UNRESOLVED_FEATURE", RELATION="VOID_ABOVE")
    assert VT.effective_claim_type(t) == "VERTICAL_RELATION"
    assert t["CLAIM_TYPE"] == "UNRESOLVED_FEATURE"      # raw untouched


def test_unknown_claim_type_is_invalid():
    t = dict(TRACE_ID="X", CASE_ID="C", CLAIM_TYPE="BANANA",
             SHEET_ID="GROUND_FLOOR_PLAN", PIXEL_POINT=[1, 1],
             VISUAL_TRACE_STATUS="TRACE_ESTABLISHED", **FIVE)
    assert VT.record_status(t, SHEETS)[0] == "INVALID"


# ------------------------------------------------------------------
# cross-sheet contradiction gating
# ------------------------------------------------------------------
def test_projection_difference_is_only_a_potential_contradiction():
    a = dict(CLAIM_TYPE="UNRESOLVED_FEATURE", SHEET_ID="FIRST_FLOOR_PLAN",
             PIXEL_BBOX=[0, 0, 1, 1])
    b = dict(CLAIM_TYPE="WALL_SEGMENT", SHEET_ID="NORTH_EAST_ELEVATION",
             PIXEL_POLYLINE=[[0, 0], [1, 1]])
    assert VT.classify_contradiction(
        a, b, "SAME_PHYSICAL_LOCATION_PROVISIONAL", True, True
    ) == "POTENTIAL_CROSS_SHEET_CONTRADICTION"
    assert VT.classify_contradiction(
        a, b, "SAME_PHYSICAL_LOCATION_ESTABLISHED", True, True
    ) == "ESTABLISHED_CROSS_SHEET_CONTRADICTION"
    # an untraced claim can never be promoted
    a2 = dict(CLAIM_TYPE="UNRESOLVED_FEATURE", SHEET_ID="FIRST_FLOOR_PLAN")
    assert VT.classify_contradiction(
        a2, b, "SAME_PHYSICAL_LOCATION_ESTABLISHED", True, True
    ) == "POTENTIAL_CROSS_SHEET_CONTRADICTION"


# ------------------------------------------------------------------
# parameters: weakest input wins, provenance cannot be faked
# ------------------------------------------------------------------
def test_drawing_parameter_cannot_be_owner_confirmed():
    with pytest.raises(ValueError):
        PM.parameter("H", 3.0, "m", "DRAWING", "ref", owner_confirmed=True)


def test_default_must_be_marked_default():
    with pytest.raises(ValueError):
        PM.parameter("H", 2.2, "m", "TEMPORARY_DEFAULT", "ref")


def test_owner_input_never_becomes_source_established():
    reg = PM.default_registry()
    reg = PM.with_owner_value(reg, "APPLICABLE_PLASTER_HEIGHT", 3.0, "m", 2,
                              "synthetic owner value for the test")
    p = reg["APPLICABLE_PLASTER_HEIGHT"]
    assert p["SOURCE_TYPE"] == "OWNER_PROJECT_INPUT"
    assert p["DEFAULT_OR_ACTUAL"] == "PROJECT_INPUT"
    assert p["STATUS"] == "ESTABLISHED_FOR_PROJECT"
    geom = [{"ITEM_ID": "W", "CASE_ID": "S", "TREATMENT": "T",
             "LENGTH_M": 4.0, "SOURCE_TYPE": "DRAWING",
             "HEIGHT_PARAMETER": "APPLICABLE_PLASTER_HEIGHT"}]
    line = PM.compute(geom, reg)["LINES"][0]
    assert line["AREA_M2"] == 12.0
    assert line["QUANTITY_STATE"] == "OWNER_PARAMETRIC_QUANTITY"


def test_one_default_makes_the_whole_line_provisional():
    reg = PM.default_registry()
    geom = [{"ITEM_ID": "D", "CASE_ID": "S", "TREATMENT": "T",
             "LENGTH_M": 1.0, "SOURCE_TYPE": "DRAWING",
             "HEIGHT_PARAMETER": "DOOR_HEIGHT"}]
    assert PM.compute(geom, reg)["LINES"][0]["QUANTITY_STATE"] == \
        "PROVISIONAL_DEFAULT_QUANTITY"


def test_unknown_height_stays_not_established():
    reg = PM.default_registry()
    geom = [{"ITEM_ID": "W", "CASE_ID": "S", "TREATMENT": "T",
             "LENGTH_M": 4.0, "SOURCE_TYPE": "DRAWING",
             "HEIGHT_PARAMETER": "APPLICABLE_PLASTER_HEIGHT"}]
    line = PM.compute(geom, reg)["LINES"][0]
    assert line["AREA_M2"] is None
    assert line["QUANTITY_STATE"] == "NOT_ESTABLISHED"


def test_plaster_height_unknown_reason_is_project_evidence_not_history():
    reason = PM.default_registry()["APPLICABLE_PLASTER_HEIGHT"]["SOURCE_REFERENCE"]
    assert "24" not in reason and "reader" not in reason.lower()
    assert "project source" in reason.lower()


# ------------------------------------------------------------------
# frozen P7757 artifacts, when present
# ------------------------------------------------------------------
@pytest.mark.skipif(not (DATA / "TRACE_REGISTER.json").exists(),
                    reason="client data not present")
def test_register_reports_three_statuses_separately():
    reg = json.loads((DATA / "TRACE_REGISTER.json").read_text("utf-8"))
    assert reg["VALID_TRACE_RECORDS"] == (
        reg["LOCATABLE_TRACES"] + reg["NON_LOCATABLE_VALID_TRACES"])
    assert reg["DANGLING_SUPPORTED_BY"] == []
    assert reg["SOURCE_ACCESS_ALL_WITHIN_SANDBOX"] is True


@pytest.mark.skipif(not (DATA / "case_sandbox").exists(),
                    reason="client data not present")
def test_reader_visible_task_carries_no_pre_read_interpretation():
    ctrl = json.loads(
        (DATA / "CONTROLLER_SOURCE_REQUIREMENTS.json").read_text("utf-8"))
    reasons = [r.get("REASON_VISUAL_PREREAD") or ""
               for c in ctrl["CASE_SOURCE_REQUIREMENTS"]["CASES"]
               for r in c["SOURCE_REQUIREMENTS"]]
    banned = [w for w in ("curved main stair", "VOID over", "only sheet")
              if any(w.lower() in r.lower() for r in reasons)]
    assert banned, "controller record should carry the interpretations"
    for task in DATA.glob("case_sandbox/*/TASK.json"):
        text = task.read_text("utf-8").lower()
        for w in banned:
            assert w.lower() not in text, f"{task}: leaked '{w}'"


@pytest.mark.skipif(not (DATA / "CASE_SANDBOX_MANIFESTS.json").exists(),
                    reason="client data not present")
def test_sandbox_mounts_exactly_the_declared_union():
    req = json.loads((DATA / "CASE_SOURCE_REQUIREMENTS.json").read_text("utf-8"))
    for c in req["CASES"]:
        d = DATA / "case_sandbox" / c["CASE_ID"]
        mounted = sorted(p.stem for p in d.glob("*.jpeg"))
        assert mounted == sorted(c["CONSERVATIVE_UNION_MOUNTED"])
