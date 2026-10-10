"""Write the audited pricing matrix as the trade-ordered workbook an estimator opens.

Three quantity columns, never one: what the drawing measured, what the BOQ will be priced by, and the unit that second
number has to arrive in.  The middle column is empty on every row in this project, and that is the finding rather than an
omission: no measured input has yet been converted into a pricing quantity, because each needs a height, a scope decision, a
specification or a drawing that does not exist in this set.

Rate and amount columns are created and left empty. No rate has been supplied.
"""

from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_pricing"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"
FILE = OUT / "QORTUBA_PRICING_INPUT_MATRIX.xlsx"

NAVY = PatternFill("solid", fgColor="1F3A5F")
BAND = PatternFill("solid", fgColor="DCE6F1")
GREEN = PatternFill("solid", fgColor="D6EBD6")       # a measured input that is solid
CREAM = PatternFill("solid", fgColor="FFF2CC")       # final BOQ quantity: awaited
PEACH = PatternFill("solid", fgColor="FBDBC8")       # information required
GREY = PatternFill("solid", fgColor="E6E6E6")        # not applicable
SUB = PatternFill("solid", fgColor="F2F5F9")
THIN = Border(*[Side(style="thin", color="BFC9D4")] * 4)

CLASS_FILL = {"FINAL_PRICING_QUANTITY": GREEN, "MEASUREMENT_INPUT": CREAM, "SCOPE_NOT_CONFIRMED": CREAM,
              "SOURCE_REQUIRED": PEACH, "SPEC_REQUIRED": PEACH, "NOT_APPLICABLE": GREY}
CLASS_LABEL = {"FINAL_PRICING_QUANTITY": "Final quantity", "MEASUREMENT_INPUT": "Measurement input",
               "SCOPE_NOT_CONFIRMED": "Scope not confirmed", "SOURCE_REQUIRED": "Information required",
               "SPEC_REQUIRED": "Specification required", "NOT_APPLICABLE": "Not applicable"}

COLS = ["البند\nItem No.", "الوصف\nItem", "Description", "الوحدة\nUnit",
        "كمية القياس\nMeasured Input", "الكمية النهائية\nFinal BOQ Quantity",
        "% الهالك\nWaste %", "كمية الشراء\nPurchase Qty", "سعر الوحدة\nRate", "الإجمالي\nAmount",
        "مصدر الكمية\nSource", "حالة الاعتماد\nStatus", "ملاحظات\nNotes"]
WIDTHS = [11, 30, 40, 9, 17, 19, 10, 13, 12, 12, 34, 22, 62]


def _head(ws, cols, widths, title=None, sub=None):
    r = 1
    if title:
        ws.cell(1, 1, title).font = Font(bold=True, size=13, color="1F3A5F")
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(cols))
        if sub:
            ws.cell(2, 1, sub).font = Font(italic=True, size=9, color="666666")
            ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(cols))
        r = 4
    for i, c in enumerate(cols, 1):
        cell = ws.cell(r, i, c)
        cell.font = Font(bold=True, color="FFFFFF", size=9)
        cell.fill = NAVY
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = THIN
    ws.row_dimensions[r].height = 32
    ws.freeze_panes = ws.cell(r + 1, 1)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    return r + 1


def build():
    a = json.loads((OUT / "QORTUBA_FINAL_PRICING_AUDIT.json").read_text("utf-8"))
    rd = json.loads((OUT / "QORTUBA_CORRECTED_READINESS.json").read_text("utf-8"))
    bl = json.loads((OUT / "QORTUBA_BLOCKED_FINAL_QUANTITIES.json").read_text("utf-8"))
    fr = json.loads((QS / "FREEZE_PA08_QORTUBA_ROOM_BY_ROOM_QS_01.json").read_text("utf-8"))
    wb = Workbook()

    # ---------------------------------------------------------------- cover
    ws = wb.active
    ws.title = "الغلاف Cover"
    ws["A1"] = "قرطبة - جدول الكميات والتسعير"
    ws["A1"].font = Font(bold=True, size=18, color="1F3A5F")
    ws["A2"] = "QORTUBA - SECOND FLOOR APARTMENT   |   Bill of Quantities and Pricing Input Matrix"
    ws["A2"].font = Font(size=11, color="555555")
    facts = [
        ("Project", "قرطبة ق1 ش1 ج6  /  Qortuba, block 1, street 1, lane 6"),
        ("Scope", fr["STOREY"] + " - apartment only; stairs, terrace and roof kept separate"),
        ("Workpaper", "PA08_QORTUBA_ROOM_BY_ROOM_QS_01"),
        ("Workpaper freeze", fr["DIGEST"]),
        ("Workpaper commit", fr["GIT_HEAD_AT_FREEZE"]),
        ("", ""),
        ("Trade rows", a["COUNT"]),
        ("Final pricing quantities available now", a["FINAL_PRICING_QUANTITIES_AVAILABLE_NOW"]),
        ("Rows carrying a measured input", a["BY_CLASS"].get("MEASUREMENT_INPUT", 0) + a["BY_CLASS"].get("SCOPE_NOT_CONFIRMED", 0)),
        ("Rows needing a drawing or specification", a["BY_CLASS"].get("SOURCE_REQUIRED", 0) + a["BY_CLASS"].get("SPEC_REQUIRED", 0)),
        ("Rates supplied", 0),
        ("", ""),
        ("THE RULE", "A row is ready only when the quantity is in the unit AND on the basis the bill prices that item by."),
        ("", "A length is not an area. A footprint is not a finish. A count is not an assembly."),
        ("", ""),
        ("WHAT THIS MEANS", a["WHAT_THAT_MEANS"]),
        ("", ""),
        ("Three columns", "MEASURED INPUT is what the drawing gives. FINAL BOQ QUANTITY is what gets priced. UNIT is the unit"),
        ("", "the second must arrive in. The middle column is empty throughout, which is the result, not an omission."),
        ("Not priced", "No rate has been supplied, so no rate or amount cell is filled anywhere in this workbook."),
    ]
    for i, (k, v) in enumerate(facts, start=4):
        ws.cell(i, 1, k).font = Font(bold=True, size=10)
        ws.cell(i, 2, v).alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 40
    ws.column_dimensions["B"].width = 120
    r = len(facts) + 6
    ws.cell(r, 1, "LEGEND").font = Font(bold=True)
    for j, (cls, lab) in enumerate(CLASS_LABEL.items()):
        ws.cell(r + 1 + j, 1, lab).fill = CLASS_FILL[cls]
        ws.cell(r + 1 + j, 1).border = THIN
        ws.cell(r + 1 + j, 2, {"FINAL_PRICING_QUANTITY": "ready to price in the correct unit and scope",
                               "MEASUREMENT_INPUT": "a real measured figure, not yet a pricing quantity",
                               "SCOPE_NOT_CONFIRMED": "the unit is right but the scope is not drawn",
                               "SOURCE_REQUIRED": "needs a drawing that does not exist in this set",
                               "SPEC_REQUIRED": "needs a specification",
                               "NOT_APPLICABLE": "carried so an exclusion is visible rather than silent"}[cls])

    # ---------------------------------------------------------------- readiness
    ws = wb.create_sheet("الجاهزية Summary")
    cols = ["#", "البند / Trade", "Trade (EN)", "الجاهزية / Readiness", "Final qty", "With a measured input",
            "Items", "لماذا / Why", "الحد الأدنى المطلوب / One minimum input"]
    r = _head(ws, cols, [5, 16, 24, 20, 11, 22, 8, 62, 52], "PRICING READINESS BY TRADE",
              "READY_TO_PRICE means a final BOQ quantity exists in the proper pricing unit and scope. "
              "Raw lengths and counts are never counted as final priceable rows.")
    for x in rd["ROWS"]:
        vals = [x["SECTION_NO"], x["TRADE_AR"], x["TRADE_EN"], x["READINESS"], x["FINAL_PRICING_QUANTITIES"],
                x["ITEMS_WITH_A_MEASURED_INPUT"], x["ITEMS"], x["WHY"], x["ONE_MINIMUM_INPUT"]]
        fill = GREEN if x["READINESS"] == "READY_TO_PRICE" else PEACH if x["READINESS"] == "NOT_READY" else CREAM
        for c, v in enumerate(vals, 1):
            cell = ws.cell(r, c, v)
            cell.border = THIN
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if c == 4:
                cell.fill = fill
                cell.font = Font(bold=True, size=9)
        r += 1

    # ---------------------------------------------------------------- blockers
    ws = wb.create_sheet("المطلوب Required")
    cols = ["المطلوب / Blocker", "يوقف عدد بنود / Blocks", "الترايدات / Trades", "البنود / Items"]
    r = _head(ws, cols, [56, 16, 44, 96], "WHAT IS BLOCKING EACH FINAL QUANTITY",
              "Grouped so one answer shows everything it releases. Nothing is asked for that no named row needs.")
    for x in bl["ROWS"]:
        for c, v in enumerate([x["BLOCKER"], x["BLOCKS_ITEMS"], "، ".join(x["TRADES"]), " | ".join(x["ITEMS"])], 1):
            cell = ws.cell(r, c, v)
            cell.border = THIN
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if c == 1:
                cell.fill = PEACH
        r += 1

    # ---------------------------------------------------------------- one sheet per trade
    for sec in a["SECTIONS"]:
        rows = [x for x in a["ROWS"] if x["SECTION_NO"] == sec["NO"]]
        if not rows:
            continue
        name = f'{sec["NO"]}- {sec["AR"]}'[:31]
        ws = wb.create_sheet(name)
        r = _head(ws, COLS, WIDTHS, f'{sec["NO"]}.  {sec["AR"]}  /  {sec["EN"]}',
                  "MEASURED INPUT is what the drawing gives.  FINAL BOQ QUANTITY is what is priced, in the UNIT column's unit.")
        for x in rows:
            mi = x["MEASURED_INPUT"]
            mtxt = None if mi["VALUE"] is None else (f'{mi["VALUE"]:.4f}'.rstrip("0").rstrip(".")
                                                     + (f' {mi["UNIT"].lower()}' if mi["UNIT"] and mi["UNIT"] != x["UNIT"] else ""))
            vals = [x["ITEM_NO"], x["ITEM_AR"], x["DESCRIPTION_EN"], x["UNIT"], mtxt, None, None, None, None, None,
                    x["SOURCE"], CLASS_LABEL[x["CLASS"]], x["NOTES"] or ""]
            for c, v in enumerate(vals, 1):
                cell = ws.cell(r, c, v)
                cell.border = THIN
                cell.alignment = Alignment(vertical="top", wrap_text=True,
                                           horizontal="center" if c in (1, 4, 5, 6) else "left")
                cell.font = Font(size=9)
            ws.cell(r, 5).fill = GREEN if mi["VALUE"] is not None else GREY
            ws.cell(r, 6).fill = CREAM
            for c in (7, 8, 9, 10):
                ws.cell(r, c).fill = GREY
            ws.cell(r, 12).fill = CLASS_FILL[x["CLASS"]]
            r += 1
            ws.cell(r, 3, "→ final quantity = " + (x["FINAL_QUANTITY_FORMULA"] or "not a quantity")
                    + (f'   |   blocked by: {x["BLOCKER"]}' if x["BLOCKER"] else ""))
            ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=13)
            ws.cell(r, 3).font = Font(italic=True, size=8, color="666666")
            ws.cell(r, 3).alignment = Alignment(vertical="top", wrap_text=True)
            for c in range(1, 14):
                ws.cell(r, c).fill = SUB
            r += 1

    # ---------------------------------------------------------------- room backup
    ws = wb.create_sheet("حساب الغرف Rooms")
    floors = json.loads((QS / "QORTUBA_QS01_FLOOR_CALCULATIONS.json").read_text("utf-8"))["ROWS"]
    sk = {x["ROOM_ID"]: x for x in json.loads((QS / "QORTUBA_QS01_SKIRTING_TAKEOFF.json").read_text("utf-8"))["ROWS"]}
    cols2 = ["الغرفة / Room", "رطب/جاف", "الشكل / Shape", "المعادلة / Formula", "المساحة م2",
             "محيط الجدار م", "خصم الأبواب م", "صافي النعلة م", "الحالة"]
    r = _head(ws, cols2, [26, 12, 24, 76, 13, 15, 15, 15, 21], "CALCULATION BACKUP - ROOM BY ROOM TAKEOFF",
              "These rows feed the trade totals. They are the workpaper, not the pricing output.")
    for f in floors:
        s = sk.get(f["ROOM_ID"], {})
        vals = [f["ROOM"], f["WET_OR_DRY"], f["SHAPE_TYPE"], f["FORMULA"], f["METHOD_A_CAD_POLYGON_AREA_M2"],
                s.get("GROSS_WALL_LINE_PERIMETER_LM"), s.get("DOOR_WIDTH_DEDUCTION_LM"), s.get("NET_SKIRTING_LM"),
                f["STATUS"]]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(r, c, v)
            cell.border = THIN
            cell.fill = SUB
            cell.font = Font(size=9)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
        for c in (5, 6, 7, 8):
            ws.cell(r, c).number_format = "0.000"
        r += 1

    OUT.mkdir(parents=True, exist_ok=True)
    wb.save(FILE)
    return FILE


if __name__ == "__main__":
    print("wrote", build())
