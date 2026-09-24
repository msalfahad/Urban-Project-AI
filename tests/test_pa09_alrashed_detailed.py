"""The detailed takeoff workbook: readable arithmetic that still adds up to the frozen measurement.

The workbook's promise is that a reader can follow every area without AutoCAD, so the tests evaluate the
workbook's own formulas - not the Python that wrote them - and check the results against the frozen artifact.  A
sheet that looks right and totals wrong would pass a shape test and fail these.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from openpyxl import load_workbook

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import detailed_takeoff as DT

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
XL = OUT / "ALRASHED_DETAILED_QUANTITY_TAKEOFF.xlsx"
REF = re.compile(r"(?:'([^']+)'!)?\$?([A-Z]{1,3})\$?(\d+)")


@pytest.fixture(scope="module")
def wb():
    return load_workbook(XL)


@pytest.fixture(scope="module")
def rec():
    return json.loads((OUT / "ALRASHED_DETAILED_QUANTITY_TAKEOFF.json").read_text("utf-8"))


@pytest.fixture(scope="module")
def export():
    return json.loads((OUT / "ALRASHED_DETAILED_QUANTITY_EXPORT.json").read_text("utf-8"))


@pytest.fixture(scope="module")
def frozen():
    return json.loads((OUT / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json").read_text("utf-8"))


# ------------------------------------------------------------------ a small evaluator for the workbook's own maths
def value(wb, sheet, coord, depth=0):
    """Evaluate a cell the way a spreadsheet would, so the test checks the workbook rather than the writer."""
    assert depth < 40, "formula recursion"
    v = wb[sheet][coord].value
    if not isinstance(v, str) or not v.startswith("="):
        return v
    f = v[1:]
    if f.startswith("IF"):
        return "BLANK_UNTIL_PRICED"

    def rng(m):
        sh = m.group(1) or sheet
        a, b = m.group(2), m.group(3)
        c0, r0 = REF.match(a).group(2, 3)
        c1, r1 = REF.match(b).group(2, 3)
        assert c0 == c1, "only single-column ranges are used"
        total = 0.0
        for r in range(int(r0), int(r1) + 1):
            x = value(wb, sh, f"{c0}{r}", depth + 1)
            if isinstance(x, (int, float)):
                total += x
        return repr(total)

    f = re.sub(r"SUM\((?:'([^']+)'!)?([A-Z]{1,3}\d+):([A-Z]{1,3}\d+)\)", rng, f)

    def one(m):
        sh = m.group(1) or sheet
        x = value(wb, sh, f"{m.group(2)}{m.group(3)}", depth + 1)
        return repr(float(x)) if isinstance(x, (int, float)) else "0.0"

    f = REF.sub(one, f)
    assert re.fullmatch(r"[0-9eE+\-*/.() ]+", f), f
    return eval(f)  # noqa: S307 - the pattern above admits arithmetic only


# ------------------------------------------------------------------ shape
def test_the_workbook_has_the_thirteen_arabic_sheets_and_all_read_right_to_left(wb):
    assert wb.sheetnames == DT.SHEETS
    assert len(wb.sheetnames) == 13
    for name in wb.sheetnames:
        assert wb[name].sheet_view.rightToLeft, name


# ------------------------------------------------------------------ the decomposition
def test_every_room_is_shown_as_rectangles_that_add_back_to_its_frozen_area(wb, frozen):
    ws = wb["حصر المساحات"]
    frozen_area = {r["ROOM_REF"]: r["AREA_M2"] for f in frozen["FLOORS"] for r in f["ROOMS"]}
    seen = 0
    for row in range(2, ws.max_row + 1):
        if ws.cell(row, 5).value != "إجمالي الغرفة":
            continue
        ref = ws.cell(row, 2).value
        total = value(wb, ws.title, f"H{row}")
        cad = ws.cell(row, 10).value
        assert abs(total - cad) < 5e-5, (ref, total, cad)
        assert abs(total - frozen_area[ref]) < 5e-5, (ref, total, frozen_area[ref])
        seen += 1
    assert seen == len(frozen_area) == 135


def test_a_reader_can_follow_the_arithmetic_without_autocad(wb):
    ws = wb["حصر المساحات"]
    parts = 0
    for row in range(2, ws.max_row + 1):
        text = ws.cell(row, 9).value
        if not text or "×" not in text:
            continue
        lhs, rhs = text.split("=")
        a, b = (float(x) for x in lhs.split("×"))
        # the cell holds the exact dimension and the text shows it to four places, so a reader multiplying the
        # printed numbers lands on the printed area to within the rounding of what is printed
        assert abs(a * b - float(rhs)) < 2e-3, text
        assert abs(value(wb, ws.title, f"H{row}") - float(rhs)) < 1e-3
        parts += 1
    assert parts == 184


def test_floor_totals_and_the_project_total_are_live_formulas(wb, rec):
    ws = wb["حصر المساحات"]
    floors, project = {}, None
    for row in range(2, ws.max_row + 1):
        if ws.cell(row, 5).value == "إجمالي الدور":
            floors[ws.cell(row, 1).value] = value(wb, ws.title, f"H{row}")
        elif ws.cell(row, 5).value == "إجمالي المشروع":
            project = value(wb, ws.title, f"H{row}")
    assert len(floors) == 3
    # the sheet adds exact room areas; the record adds the same areas after each is rounded to four places
    for f in rec["FLOORS"]:
        assert abs(floors[DT.FLOORS_AR[f["FLOOR"]]] - f["AREA_M2"]) < 1e-3
    assert abs(project - rec["PROJECT_TOTAL_M2"]) < 1e-3
    assert abs(project - sum(floors.values())) < 1e-6


# ------------------------------------------------------------------ the trades
@pytest.mark.parametrize("code,key", [
    ("AR-WP-01", "WALL_PORCELAIN_NET_M2"), ("AR-WP-02", "TILE_PREPARATION_M2"),
    ("AR-IN-01", "WATERPROOFING_M2"), ("AR-BL-01", "BLOCKWORK_150_NET_M2"),
    ("AR-BL-02", "BLOCKWORK_200_NET_M2"), ("AR-PL-01", "INTERNAL_PLASTER_NET_M2"),
    ("AR-PT-01", "INTERNAL_PAINT_M2"), ("AR-PL-02", "EXTERNAL_PLASTER_NET_M2"),
    ("AR-PT-02", "EXTERNAL_PAINT_M2"), ("AR-CL-01", "CEILING_M2"),
    ("AR-RF-01", "PARAPET_BLOCKWORK_M2"), ("AR-RF-02", "PARAPET_PLASTER_M2"),
    ("AR-RF-03", "PARAPET_PAINT_M2"), ("AR-AL-01", "ALUMINIUM_M2"),
    ("AR-DR-01", "DOOR_AREA_M2"), ("AR-EX-01", "EXTERNAL_OPEN_AREA_M2"),
])
def test_each_boq_quantity_traces_through_its_sheet_back_to_the_frozen_total(wb, frozen, code, key):
    """Every BOQ line is a formula down to a measured dimension, and lands on the frozen total.

    The tolerance is 0.01 m2 because the trade sheets rebuild their totals from the dimensions as published -
    a wall length printed to the millimetre - rather than from the engine's floating point.  That is rounding in
    the presentation, not a restatement: the largest line here is 963 m2 and the largest drift is 3 mm2.
    """
    ws = wb["BOQ حسب البند"]
    row = next(r for r in range(2, ws.max_row + 1) if ws.cell(r, 1).value == code)
    assert abs(value(wb, ws.title, f"E{row}") - frozen["TOTALS"][key]) < 0.01


def test_the_floor_finish_line_covers_the_rooms_the_frozen_takeoff_calls_internal(wb, frozen):
    ws = wb["BOQ حسب البند"]
    row = next(r for r in range(2, ws.max_row + 1) if ws.cell(r, 1).value == "AR-FL-01")
    assert abs(value(wb, ws.title, f"E{row}") - frozen["TOTALS"]["INTERNAL_FLOOR_AREA_M2"]) < 0.01


def test_the_wall_cladding_sheet_deducts_each_rooms_own_openings(wb, frozen):
    ws = wb["كسوة الجدران"]
    wet = {x["ROOM_REF"]: x for x in frozen["WET_ROOM_RECONCILIATION"]}
    rows = 0
    for r in range(2, ws.max_row + 1):
        ref = ws.cell(r, 2).value
        if ref not in wet:
            continue
        gross = value(wb, ws.title, f"F{r}")
        net = value(wb, ws.title, f"H{r}")
        prep = value(wb, ws.title, f"I{r}")
        assert abs(gross - wet[ref]["GROSS_WALL_PORCELAIN_M2"]) < 1e-3
        assert abs(net - wet[ref]["NET_WALL_PORCELAIN_M2"]) < 1e-3, ref
        assert prep == net, "the preparation sits behind the same faces"
        assert net < gross or wet[ref]["OPENING_DEDUCTIONS_M2"] == 0
        rows += 1
    assert rows == 13


# ------------------------------------------------------------------ DS-01
def test_no_cell_holds_a_rate_a_waste_or_an_amount(wb):
    ws = wb["BOQ حسب البند"]
    for r in range(2, ws.max_row + 1):
        for col in (6, 8):
            assert ws.cell(r, col).value is None, (r, col)
        amount = ws.cell(r, 9).value
        assert amount is None or (isinstance(amount, str) and amount.startswith("=IF"))


def test_procurement_and_amount_stay_blank_until_a_waste_and_a_rate_are_entered(wb):
    ws = wb["BOQ حسب البند"]
    row = next(r for r in range(2, ws.max_row + 1) if ws.cell(r, 1).value == "AR-BL-01")
    assert value(wb, ws.title, f"G{row}") == "BLANK_UNTIL_PRICED"
    assert value(wb, ws.title, f"I{row}") == "BLANK_UNTIL_PRICED"


def test_the_export_keeps_quantity_waste_rate_and_amount_in_separate_fields(export):
    for r in export["RECORDS"]:
        assert r["WASTE_PERCENT"] is None and r["PROCUREMENT_QUANTITY"] is None
        assert r["UNIT_RATE"] is None and r["AMOUNT"] is None
        assert r["APPROVAL_STATUS"] == "DRAFT"
        assert r["MEASURED_UNIT"] in ("m2", "lm")
        assert isinstance(r["MEASURED_QUANTITY"], (int, float))
    assert export["RECORD_COUNT"] == len(export["RECORDS"]) == 265


# ------------------------------------------------------------------ what the workbook is not built from
def test_no_historical_quantity_reached_the_takeoff(export, rec):
    assert rec["HISTORICAL_QUANTITY_USED"] is False
    banned = {950.22, 57.0, 1375.0, 600.16, 0.75}
    for r in export["RECORDS"]:
        assert r["MEASURED_QUANTITY"] not in banned
        assert r["HISTORICAL_DATA_USED"] is False


def test_the_frozen_takeoff_is_unchanged(rec, frozen):
    assert frozen["DIGEST"] == DT.FROZEN_DIGEST
    assert rec["FROZEN_UNCHANGED"]["MATCHES"] is True


def test_the_derived_skirting_is_marked_as_not_part_of_the_frozen_takeoff(export, rec):
    sk = [r for r in export["RECORDS"] if r["TRADE"] == "SKIRTING"]
    assert len(sk) == 49
    for r in sk:
        assert r["STATUS"] == "DERIVED_NOT_IN_FROZEN_TAKEOFF"
        assert r["VERIFIED_AGAINST_FROZEN"] is False
    assert rec["SKIRTING_LM"] > 0


def test_the_profile_line_asks_for_a_source_rather_than_inventing_a_length(export):
    assert DT.PROFILE_STEEL["QUANTITY"] is None
    assert DT.PROFILE_STEEL["STATUS"] == "SOURCE_REQUIRED"
    assert not [r for r in export["RECORDS"] if r["TRADE"] == "PROFILE"]


# ------------------------------------------------------------------ the fifteen checks
def test_all_fifteen_quality_checks_pass(rec):
    q = rec["WORKBOOK"]["QA"]
    assert q["OF"] == 15 and q["PASSED"] == 15 and q["ALL_PASS"]
    assert [c["CHECK"] for c in q["CHECKS"]] == sorted(c["CHECK"] for c in q["CHECKS"])
