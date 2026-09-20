"""PA08_QORTUBA_ROOM_BY_ROOM_QS_01: the rules that keep a room-by-room takeoff honest once the benchmark is known.

The contractor's aggregate totals were seen in an earlier phase, so this phase cannot claim to be blind.  What it can prove is
that the room numbers were derived from named geometry, that nothing in the takeoff can see a contractor figure, and that the
totals are the sum of the rows rather than a target with rows fitted under it.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.qs01 import takeoff as TK

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"
SRC = Path("research/qs_wall_treatment_01/pa08/qortuba/qs01/takeoff.py")

# every quantity printed on the contractor sheet.  They live here, in the test, and must NOT appear in the takeoff source.
CONTRACTOR_AGGREGATES = ("107.76", "76.90", "76.9", "159.28", "153.28", "153.2775", "26.35", "12.00", "1611.266", "421.513")


def reg(name):
    return json.loads((OUT / f"{name}.json").read_text("utf-8"))


def _imports(path):
    out = set()
    for n in ast.walk(ast.parse(Path(path).read_text("utf-8"))):
        if isinstance(n, ast.Import):
            out |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.add(n.module)
    return out


def test_the_takeoff_cannot_see_a_contractor_figure():
    mods = _imports(SRC)
    assert not any("ext01" in m or "contractor" in m.lower() or "compare" in m for m in mods), sorted(mods)


def test_no_contractor_aggregate_is_written_into_the_takeoff_source():
    """A number fitted to a benchmark usually arrives as a literal.  None of the contractor's totals is in this file."""
    text = SRC.read_text("utf-8")
    found = [v for v in CONTRACTOR_AGGREGATES if re.search(r"(?<![\d.])" + re.escape(v) + r"(?![\d])", text)]
    assert not found, found


def test_the_freeze_declares_the_source_only_calculation_complete():
    fr = reg("FREEZE_PA08_QORTUBA_ROOM_BY_ROOM_QS_01")
    assert fr["SOURCE_ONLY_CALCULATION_COMPLETE"] is True
    assert fr["CONTRACTOR_AGGREGATE_USED_AS_A_TARGET"] is False
    for n, h in fr["CONTENTS"].items():
        assert TK._sha(OUT / f"{n}.json") == h, f"{n} changed after the freeze"


def test_every_floor_formula_reproduces_its_own_area():
    """The formula is the audit trail.  If it does not multiply out to the area, it is decoration."""
    for row in reg("QORTUBA_QS01_FLOOR_CALCULATIONS")["ROWS"]:
        a = row["METHOD_A_CAD_POLYGON_AREA_M2"]
        if a is None:
            continue
        total = sum(q["W_MM"] * q["D_MM"] for q in row["RECTANGLES"]) / 1e6
        assert abs(total - a) < 5e-4, (row["ROOM"], total, a)
        assert row["FORMULA"].endswith("m2") and " x " in row["FORMULA"]


def test_merging_rectangles_never_changes_an_area():
    rects = [{"X_MM": [0, 1000], "Y_MM": [0, 500], "W_MM": 1000, "D_MM": 500, "AREA_M2": 0.5},
             {"X_MM": [0, 1000], "Y_MM": [500, 900], "W_MM": 1000, "D_MM": 400, "AREA_M2": 0.4},
             {"X_MM": [1000, 1600], "Y_MM": [0, 500], "W_MM": 600, "D_MM": 500, "AREA_M2": 0.3}]
    merged = TK.merge_rectangles(rects)
    assert abs(sum(q["AREA_M2"] for q in merged) - 1.2) < 1e-9
    assert len(merged) < len(rects)


def test_the_unlabelled_internal_lobby_is_in_the_apartment_on_door_evidence():
    rows = reg("QORTUBA_ROOM_REGISTER")["ROWS"]
    lob = [x for x in rows if x["ZONE_KIND"] == "UNLABELLED_INTERNAL_SPACE"]
    assert lob, "the takeoff must not drop an unlabelled internal space"
    for x in lob:
        assert x["INSIDE_APARTMENT"] and "door" in x["WHY"].lower()
    ids = {f["ROOM_ID"] for f in reg("QORTUBA_QS01_FLOOR_CALCULATIONS")["ROWS"]}
    assert all(x["ROOM_ID"] in ids for x in lob), "it is in the inventory but not measured"


def test_stairs_terrace_roof_and_lift_are_outside_every_apartment_total():
    rows = reg("QORTUBA_ROOM_REGISTER")["ROWS"]
    for k in ("STAIR", "OPEN_ROOF", "EXTERNAL_TERRACE", "COMMON_CIRCULATION_WITH_LIFT"):
        for x in [z for z in rows if z["ZONE_KIND"] == k]:
            assert not x["INSIDE_APARTMENT"], (k, x["ROOM_ID"])
    s = reg("QORTUBA_QS01_SUMMARY_TOTALS")
    named = {c["ROOM"] for c in s["C_TOTAL_INTERNAL_APARTMENT_FLOOR_AREA_M2"]["COMPONENTS"]}
    assert not {"ROOF", "STAIR"} & named


def test_the_totals_are_the_sum_of_the_rows():
    s = reg("QORTUBA_QS01_SUMMARY_TOTALS")
    floors = reg("QORTUBA_QS01_FLOOR_CALCULATIONS")["ROWS"]
    dry = sum(f["METHOD_A_CAD_POLYGON_AREA_M2"] for f in floors if f["WET_OR_DRY"] == "DRY" and f["METHOD_A_CAD_POLYGON_AREA_M2"])
    wet = sum(f["METHOD_A_CAD_POLYGON_AREA_M2"] for f in floors if f["WET_OR_DRY"] == "WET" and f["METHOD_A_CAD_POLYGON_AREA_M2"])
    assert abs(s["A_DRY_INTERNAL_FLOOR_AREA_M2"]["VALUE"] - dry) < 5e-4
    assert abs(s["B_WET_INTERNAL_FLOOR_AREA_M2"]["VALUE"] - wet) < 5e-4
    assert abs(s["C_TOTAL_INTERNAL_APARTMENT_FLOOR_AREA_M2"]["VALUE"] - (dry + wet)) < 5e-4
    sk = reg("QORTUBA_QS01_SKIRTING_TAKEOFF")["ROWS"]
    assert abs(s["D_TOTAL_SKIRTING_LM"]["VALUE"] - sum(x["NET_SKIRTING_LM"] for x in sk if x["WET_OR_DRY"] == "DRY")) < 5e-4


def test_every_skirting_row_arithmetic_closes():
    for x in reg("QORTUBA_QS01_SKIRTING_TAKEOFF")["ROWS"]:
        parts = (x["DOOR_WIDTH_DEDUCTION_LM"] + x["SLIDING_DOOR_DEDUCTION_LM"] + x["OPEN_PASSAGE_DEDUCTION_LM"]
                 + x["NON_SKIRTING_EDGE_LM"] + x["COLUMN_FACE_LM"] + x["WET_ROOM_EDGE_LM"] + x["UNRESOLVED_LM"]
                 + x["NET_SKIRTING_LM"])
        assert abs(parts - x["GROSS_WALL_LINE_PERIMETER_LM"]) < 5e-3, (x["ROOM"], parts, x["GROSS_WALL_LINE_PERIMETER_LM"])


def test_a_wet_room_carries_a_wall_edge_and_no_skirting():
    for x in reg("QORTUBA_QS01_SKIRTING_TAKEOFF")["ROWS"]:
        if x["WET_OR_DRY"] == "WET":
            assert x["NET_SKIRTING_LM"] == 0.0 and x["WET_ROOM_EDGE_LM"] > 0
            assert x["NORMAL_SKIRTING_STATUS"]["STATE"] == "SOURCE_REQUIRED"


def test_the_profile_reads_the_same_path_as_the_skirting():
    sk = {x["ROOM_ID"]: x for x in reg("QORTUBA_QS01_SKIRTING_TAKEOFF")["ROWS"]}
    for p in reg("QORTUBA_QS01_PROFILE_TAKEOFF")["ROWS"]:
        assert p["PROFILE_GEOMETRIC_PATH_LM"] == sk[p["ROOM_ID"]]["NET_SKIRTING_LM"]
        assert p["DIFFERENCE_LM"] == 0.0 and p["SEPARATE_BOQ_ITEM"] and p["SHARES_PATH_WITH_SKIRTING"]
        assert p["PROFILE_PATH_ID"] != p["SKIRTING_PATH_ID"], "two BOQ items need two ids"


def test_a_window_with_wall_below_does_not_interrupt_the_floor_level_trades():
    blue = reg("QORTUBA_QS01_BLUE_ELEMENT_SCHEDULE")["ROWS"]
    assert blue, "the drawing has glazed elements"
    for b in blue:
        assert b["TYPE"] in TK.BLUE_ELEMENT_CLASSES
        if b["WALL_BELOW"]:
            assert "DOES NOT INTERRUPT" in b["SKIRTING_EFFECT"] and b["SKIRTING_EFFECT"] == b["PROFILE_EFFECT"]
        else:
            assert "INTERRUPTS" in b["SKIRTING_EFFECT"]
    interrupting = [b for b in blue if not b["WALL_BELOW"]]
    deducted = sum(x["SLIDING_DOOR_DEDUCTION_LM"] for x in reg("QORTUBA_QS01_SKIRTING_TAKEOFF")["ROWS"])
    assert (deducted > 0) == bool(interrupting)


def test_an_unresolved_glazing_type_still_states_the_trade_effect():
    """A plan cannot say whether glazing slides.  It can say there is no wall under it, which is what the trade needs."""
    for b in reg("QORTUBA_QS01_BLUE_ELEMENT_SCHEDULE")["ROWS"]:
        if b["TYPE"] == "UNRESOLVED":
            assert b["TYPE_CANDIDATES"] and b["TRADE_EFFECT_IS_THE_SAME_FOR_EVERY_CANDIDATE"]


def test_no_height_is_invented_anywhere():
    for name, key in (("QORTUBA_QS01_WALL_TILE_TAKEOFF", "WALL_TILE_AREA_STATE"),
                      ("QORTUBA_QS01_BLOCK_WALL_TAKEOFF", "BLOCKWORK_AREA_STATE")):
        assert reg(name)[key] == "NOT_ESTABLISHED"
    for t in reg("QORTUBA_QS01_WALL_TILE_TAKEOFF")["ROWS"]:
        assert t["WALL_TILE_HEIGHT"]["VALUE"] is None and t["NET_HOST_WALL_LM"] > 0
    for q in reg("QORTUBA_QS01_PLASTER_AND_PAINT_TAKEOFF")["ROWS"]:
        assert q["HEIGHT"]["VALUE"] is None
        assert q["PLASTER_AREA_M2"]["VALUE"] is None and q["PAINT_AREA_M2"]["VALUE"] is None
    s = reg("QORTUBA_QS01_SUMMARY_TOTALS")
    assert s["J_TOTAL_BATHROOM_AND_PREPARATION_WALL_CERAMIC_M2"]["VALUE"] is None


def test_paint_is_not_assumed_to_follow_plaster():
    rows = reg("QORTUBA_QS01_PLASTER_AND_PAINT_TAKEOFF")["ROWS"]
    assert any(q["TOTAL_PLASTERABLE_FACE_LM"] > 0 and q["PAINT_ELIGIBLE_FACE_LM"] == 0 for q in rows), \
        "every plastered face is being treated as painted"


def test_the_pantry_is_not_called_a_kitchen():
    for t in reg("QORTUBA_QS01_WALL_TILE_TAKEOFF")["ROWS"]:
        if "PAINTRY" in t["ROOM"].upper() or "PANTRY" in t["ROOM"].upper():
            assert t["ROOM_KIND"] == "PREPARATION_AREA_NOT_ASSUMED_TO_BE_A_KITCHEN"


def test_every_room_names_the_geometry_its_number_came_from():
    for row in reg("QORTUBA_QS01_ROOM_CALCULATION_PROVENANCE")["ROWS"]:
        g = row["METHOD_A_GEOMETRY_IDS"]
        assert g["CUT_LINES_X_MM"] and g["CUT_LINES_Y_MM"] and g["BOUNDARY_SEAL_INDEXES"]
        assert row["FORMULA"] and row["SKIRTING_SEAL_INDEXES"]


def test_an_envelope_check_is_never_reported_as_an_area_check():
    for d in reg("QORTUBA_QS01_DUAL_METHOD_CHECK")["ROWS"]:
        if d["METHOD_B_STRENGTH"] == "ENVELOPE_ONLY":
            assert d["METHOD_B_DIMENSION_ARITHMETIC_M2"] is None
            assert d["VERDICT"] == "ENVELOPE_CONFIRMED_AREA_NOT_INDEPENDENTLY_CHECKED"
            assert d["ENVELOPE_CHECK"]["WHAT_THIS_DOES_NOT_CHECK"]
        if d["METHOD_B_STRENGTH"] == "FULLY_AUTHORED":
            assert d["METHOD_B_DIMENSION_ARITHMETIC_M2"] is not None and d["DELTA_M2"] is not None
