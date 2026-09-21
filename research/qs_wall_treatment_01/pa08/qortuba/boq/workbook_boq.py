"""Write the Qortuba BOQ workbook in the house's own column structure, with the owner's rules applied.

Fifteen columns, in Arabic, because that is the shape the Urban Projects bills already use.  Three of them carry
quantities and they are never merged: كمية القياس is what the drawing measured, قاعدة التحويل is what the rule does to
it, and الكمية النهائية is the payable figure.

The bill is trade based.  Every recalculated row names the RULE_ID and the PARAMETER_SOURCE that produced it, in the
audit sheet, so a figure can always be walked back to the rule and the parameter that set it.  The room-by-room takeoff
stays at the back as calculation backup.
"""

from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"
FILE = OUT / "QORTUBA_BOQ_CONVERSION_WORKBOOK.xlsx"

NAVY = PatternFill("solid", fgColor="1F3A5F")
GREEN = PatternFill("solid", fgColor="D6EBD6")       # a final BOQ quantity
MINT = PatternFill("solid", fgColor="E8F4E0")        # partially calculated: a real value with a named residual
CREAM = PatternFill("solid", fgColor="FFF2CC")       # a measured input, not yet payable
PEACH = PatternFill("solid", fgColor="FBDBC8")       # a drawing or specification is missing
BLUE = PatternFill("solid", fgColor="DCE6F1")        # a rule decision is missing
GREY = PatternFill("solid", fgColor="E6E6E6")
SUB = PatternFill("solid", fgColor="F2F5F9")
THIN = Border(*[Side(style="thin", color="BFC9D4")] * 4)

STATUS_FILL = {"FINAL_QUANTITY_AVAILABLE": GREEN, "PARTIALLY_CALCULATED": MINT, "ONE_INPUT_REQUIRED": CREAM,
               "PROJECT_RULE_REQUIRED": BLUE, "SPEC_REQUIRED": PEACH, "DRAWING_REQUIRED": PEACH,
               "SOURCE_REQUIRED": PEACH, "NOT_APPLICABLE": GREY, "CLOSED_BY_OWNER_RULE": GREY,
               "GEOMETRIC_REFERENCE_ONLY": GREY}
STATUS_AR = {"FINAL_QUANTITY_AVAILABLE": "كمية نهائية جاهزة", "PARTIALLY_CALCULATED": "محسوبة جزئياً",
             "ONE_INPUT_REQUIRED": "ينقصه مُدخل واحد", "PROJECT_RULE_REQUIRED": "ينقصه قرار قاعدة",
             "SPEC_REQUIRED": "ينقصه مواصفة", "DRAWING_REQUIRED": "ينقصه مخطط", "SOURCE_REQUIRED": "ينقصه مصدر",
             "NOT_APPLICABLE": "لا ينطبق", "CLOSED_BY_OWNER_RULE": "مغلق بقاعدة المالك",
             "GEOMETRIC_REFERENCE_ONLY": "مرجع هندسي فقط"}

# §9/§W: the fifteen columns, in the order the house bills use
COLS = ["البند", "الوصف", "وحدة التسعير", "كمية القياس", "وحدة القياس", "قاعدة التحويل", "الكمية النهائية",
        "% الهالك", "كمية الشراء", "سعر الوحدة", "الإجمالي", "مصدر القياس", "قاعدة القياس التجاري",
        "حالة الاعتماد", "ملاحظات"]
WIDTHS = [11, 34, 11, 13, 12, 54, 14, 9, 12, 11, 12, 30, 30, 20, 66]

LEVEL_AR = {"HISTORICAL_PRECEDENT": "سابقة مشروع سابق", "QORTUBA_PROJECT_RULE": "قاعدة مشروع قرطبة",
            "URBAN_STANDARD": "معيار أوربان", "APPROVED_TEMPORARY_DEFAULT": "قيمة مؤقتة معتمدة"}

# conversion-map rows the owner's rules have replaced, and what replaced them
SUPERSEDED_BY = {
    "CM-C5": "Q-01", "CM-PR1": "Q-02", "CM-WP1": "Q-03", "CM-WP2": "Q-04",
    "CM-C3": "Q-05", "CM-C4": "Q-06", "CM-IP1": "Q-08", "CM-PT1": "Q-09",
    "CM-IP2": "Q-10", "CM-C1": "Q-13", "CM-C2": "Q-11",
}
CLOSED_BY_RULE = {"CM-IP3": ("QP-05", "Qortuba carries no render band behind the skirting, so the item does not arise")}


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
    ws.row_dimensions[r].height = 30
    ws.freeze_panes = ws.cell(r + 1, 1)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    return r + 1


def _put(ws, r, vals, fill=None, size=9):
    for c, v in enumerate(vals, 1):
        cell = ws.cell(r, c, v)
        cell.border = THIN
        cell.font = Font(size=size)
        cell.alignment = Alignment(vertical="top", wrap_text=True)
        if fill:
            cell.fill = fill
    return r + 1


def _band(ws, r, text, ncols):
    ws.cell(r, 1, text).font = Font(bold=True, size=11, color="1F3A5F")
    for c in range(1, ncols + 1):
        ws.cell(r, c).fill = SUB
        ws.cell(r, c).border = THIN
    return r + 1


def bill_rows(qs, cm):
    """Trade-based bill: the owner-recalculated rows first, then every conversion row they did not replace."""
    rows = []
    for x in qs["ROWS"]:
        rules = ", ".join(x["RULE_ID"]) if x["RULE_ID"] else "—"
        res = x["RESIDUAL_OPENINGS"]
        note = " | ".join(z for z in (
            x["NOTE"],
            (f"{len(res)} opening(s) still without a height" if res else None),
            (x["TEMPORARY_DEFAULT_WARNING"] if x["USES_TEMPORARY_DEFAULT"] else None),
            (f"supersedes {x['SUPERSEDES']['PREVIOUS']} {x['SUPERSEDES']['UNIT']}: {x['SUPERSEDES']['WHY']}"
             if x["SUPERSEDES"] and x["SUPERSEDES"]["PREVIOUS"] is not None else None),
        ) if z)
        rows.append({
            "TRADE": x["TRADE"], "ID": x["QUANTITY_ID"], "ITEM": x["BOQ_ITEM"], "UNIT": x["UNIT"],
            "MEASURED": x["MEASURED_NET_QUANTITY"], "MEASURED_UNIT": x["UNIT"],
            "FORMULA": x["FORMULA"],
            "FINAL": (x["MEASURED_NET_QUANTITY"] if x["STATUS"] == "FINAL_QUANTITY_AVAILABLE" else None),
            "SOURCE": "QORTUBA_QS01 (frozen) + " + rules,
            "COMMERCIAL": rules, "STATUS": x["STATUS"], "NOTE": note,
        })
    covered = set(SUPERSEDED_BY) | set(CLOSED_BY_RULE)
    blocked_prefix = tuple(k for k in SUPERSEDED_BY if k.startswith("CM-B"))
    for x in cm["ROWS"]:
        i = x["MEASUREMENT_INPUT_ID"]
        if i in covered or i.startswith("CM-B") or i in blocked_prefix:
            continue
        rows.append({
            "TRADE": x["TRADE"], "ID": i, "ITEM": x["BOQ_ITEM"], "UNIT": x["TARGET_PRICING_UNIT"],
            "MEASURED": x["MEASURED_INPUT"], "MEASURED_UNIT": x["INPUT_UNIT"],
            "FORMULA": x["CONVERSION_FORMULA"],
            "FINAL": x["FINAL_BOQ_QUANTITY"].get("VALUE"),
            "SOURCE": ("QORTUBA_QS01 (frozen)" if x["MEASURED_INPUT"] is not None else "لم يُقَس / not measured"),
            "COMMERCIAL": x["COMMERCIAL_RULE_REQUIRED"] or "—",
            "STATUS": x["CURRENT_STATUS"],
            "NOTE": " | ".join(z for z in (x["MISSING_INPUT"], x["NOTES"]) if z),
        })
    for i, (rule, why) in CLOSED_BY_RULE.items():
        x = next((y for y in cm["ROWS"] if y["MEASUREMENT_INPUT_ID"] == i), None)
        if x:
            rows.append({"TRADE": x["TRADE"], "ID": i, "ITEM": x["BOQ_ITEM"], "UNIT": x["TARGET_PRICING_UNIT"],
                         "MEASURED": None, "MEASURED_UNIT": None, "FORMULA": "—", "FINAL": None,
                         "SOURCE": rule, "COMMERCIAL": rule, "STATUS": "CLOSED_BY_OWNER_RULE", "NOTE": why})
    rows.sort(key=lambda z: (z["TRADE"], z["ID"]))
    return rows


def build():
    qs = json.loads((OUT / "QORTUBA_RECALCULATED_QUANTITIES_V1.json").read_text("utf-8"))
    ow = json.loads((OUT / "URBAN_OWNER_RULES_V1.json").read_text("utf-8"))
    op = json.loads((OUT / "QORTUBA_OPENING_REGISTER.json").read_text("utf-8"))
    rm = json.loads((OUT / "QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC.json").read_text("utf-8"))
    bw = json.loads((OUT / "QORTUBA_BLOCKWORK_RECALC.json").read_text("utf-8"))
    ql = json.loads((OUT / "QORTUBA_QUESTION_LEDGER.json").read_text("utf-8"))
    reg = json.loads((OUT / "URBAN_BOQ_RULE_REGISTRY.json").read_text("utf-8"))
    cm = json.loads((OUT / "QORTUBA_BOQ_CONVERSION_MAP.json").read_text("utf-8"))
    fz = json.loads((OUT / "FREEZE_URBAN_OWNER_RULES_V1.json").read_text("utf-8"))
    qfz = json.loads((QS / "FREEZE_PA08_QORTUBA_ROOM_BY_ROOM_QS_01.json").read_text("utf-8"))
    wb = Workbook()

    # ---------------------------------------------------------------- cover
    ws = wb.active
    ws.title = "الغلاف Cover"
    ws["A1"] = "قرطبة - جدول الكميات بعد قواعد المالك"
    ws["A1"].font = Font(bold=True, size=18, color="1F3A5F")
    ws["A2"] = "QORTUBA - BOQ after OWNER RULES V1"
    ws["A2"].font = Font(size=11, color="555555")
    facts = [
        ("المشروع / Project", "قرطبة ق1 ش1 ج6  /  Qortuba, block 1, street 1, lane 6"),
        ("النطاق / Scope", qfz["STOREY"] + " - apartment only"),
        ("Measurement workpaper", "PA08_QORTUBA_ROOM_BY_ROOM_QS_01  " + qfz["DIGEST"][:16]),
        ("Owner rules freeze", fz["DIGEST"][:16]),
        ("Commit", fz["GIT_HEAD_AT_FREEZE"]),
        ("", ""),
        ("معايير أوربان / Urban standards", ow["COUNTS"]["URBAN_STANDARD"]),
        ("قواعد مشروع قرطبة / Qortuba project rules", ow["COUNTS"]["QORTUBA_PROJECT_RULE"]),
        ("قيم مؤقتة / Temporary defaults", ow["COUNTS"]["APPROVED_TEMPORARY_DEFAULT"]),
        ("سوابق ملغاة / Historical rules superseded", ow["COUNTS"]["SUPERSEDED"]),
        ("", ""),
        ("كميات نهائية / Final quantities", qs["BY_STATUS"]["FINAL_QUANTITY_AVAILABLE"]),
        ("محسوبة جزئياً / Partially calculated", qs["BY_STATUS"]["PARTIALLY_CALCULATED"]),
        ("أسئلة مغلقة / Questions closed", ql["CLOSED_COUNT"]),
        ("أسئلة مفتوحة / Questions still open", ql["STILL_OPEN_COUNT"]),
        ("Rates supplied", 0),
        ("", ""),
        ("ترتيب الأولوية / PRIORITY", " > ".join(p["LEVEL"] for p in ow["PRIORITY"])),
        ("", ow["WHERE_HISTORICAL_PRECEDENT_SITS"]),
        ("", ""),
        ("THREE QUANTITY COLUMNS", "كمية القياس is what the drawing measured. قاعدة التحويل is the rule applied to it. "
                                   "الكمية النهائية is the payable figure."),
        ("TEMPORARY DEFAULT", "Door height 2.20 m is TD-02, a placeholder and not a source dimension. Every figure it "
                              "touches is flagged and will move when a real height arrives."),
        ("NOT PRICED", "No rate has been supplied, so سعر الوحدة and الإجمالي are empty on every row."),
        ("NO WASTE", "§V: waste and procurement stay empty until a waste percentage is given."),
        ("NOT RECOMPUTED", "No geometry stage was re-run: " + ", ".join(ow["STAGES_NEVER_RERUN_BY_A_RULE_CHANGE"])),
    ]
    for i, (k, v) in enumerate(facts, start=4):
        ws.cell(i, 1, k).font = Font(bold=True, size=10)
        ws.cell(i, 2, v).alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 42
    ws.column_dimensions["B"].width = 120
    r = len(facts) + 6
    ws.cell(r, 1, "مفتاح الألوان / LEGEND").font = Font(bold=True)
    for j, st in enumerate(("FINAL_QUANTITY_AVAILABLE", "PARTIALLY_CALCULATED", "ONE_INPUT_REQUIRED",
                            "PROJECT_RULE_REQUIRED", "SPEC_REQUIRED", "NOT_APPLICABLE", "CLOSED_BY_OWNER_RULE")):
        ws.cell(r + 1 + j, 1, STATUS_AR[st]).fill = STATUS_FILL[st]
        ws.cell(r + 1 + j, 1).border = THIN
        ws.cell(r + 1 + j, 2, st)

    # ---------------------------------------------------------------- the bill, trade based
    ws = wb.create_sheet("جدول الكميات BOQ")
    r = _head(ws, COLS, WIDTHS, "QORTUBA - BILL OF QUANTITIES, OWNER RULES V1 APPLIED",
              "كمية القياس is a measurement. الكمية النهائية is a payable quantity. A partially calculated row carries "
              "a real value and a named list of openings that still have no height.")
    trade = None
    for x in bill_rows(qs, cm):
        if x["TRADE"] != trade:
            trade = x["TRADE"]
            r = _band(ws, r, trade, len(COLS))
        r = _put(ws, r, [x["ID"], x["ITEM"], x["UNIT"], x["MEASURED"], x["MEASURED_UNIT"], x["FORMULA"], x["FINAL"],
                         None, None, None, None, x["SOURCE"], x["COMMERCIAL"], STATUS_AR[x["STATUS"]], x["NOTE"]],
                 STATUS_FILL[x["STATUS"]])
        for c in (4, 7, 9, 10, 11):
            ws.cell(r - 1, c).number_format = "0.000"

    # ---------------------------------------------------------------- owner rules
    ws = wb.create_sheet("قواعد المالك Owner Rules")
    cols = ["الرقم", "المستوى", "القاعدة / Rule", "النص / Statement", "القيمة", "الوحدة", "بند المالك",
            "تُطبق تلقائياً", "تلغي / Supersedes"]
    r = _head(ws, cols, [9, 26, 34, 88, 11, 9, 13, 14, 30], "OWNER RULES V1",
              "Priority: " + " > ".join(p["LEVEL"] for p in ow["PRIORITY"]) + ".  " +
              ow["WHERE_HISTORICAL_PRECEDENT_SITS"])
    r = _band(ws, r, "معايير أوربان / URBAN STANDARDS - apply automatically below drawings and owner overrides", 9)
    for x in ow["URBAN_STANDARDS"]:
        r = _put(ws, r, [x["RULE_ID"], LEVEL_AR["URBAN_STANDARD"], x["TITLE"], x["STATEMENT"], None, None,
                         x["OWNER_SECTION"], "نعم", ", ".join(x["SUPERSEDES"]) or "—"], GREEN)
    r = _band(ws, r, "قواعد مشروع قرطبة / QORTUBA PROJECT RULES - this project only", 9)
    for x in ow["QORTUBA_PROJECT_RULES"]:
        r = _put(ws, r, [x["RULE_ID"], LEVEL_AR["QORTUBA_PROJECT_RULE"], x["PARAMETER"], x["WHY"], x["VALUE"],
                         x["UNIT"], x["OWNER_SECTION"], "قرطبة فقط", "—"], BLUE)
    r = _band(ws, r, "قيم مؤقتة / APPROVED TEMPORARY DEFAULTS - never source truth", 9)
    for x in ow["TEMPORARY_DEFAULTS"]:
        r = _put(ws, r, [x["RULE_ID"], LEVEL_AR["APPROVED_TEMPORARY_DEFAULT"], x["PARAMETER"], x["WHY"], x["VALUE"],
                         x["UNIT"], x["OWNER_SECTION"], "مؤقتاً", "—"], CREAM)
    r = _band(ws, r, "سوابق ملغاة / SUPERSEDED HISTORICAL PRECEDENT - reference only from here on", 9)
    for x in ow["SUPERSEDED_HISTORICAL_RULES"]:
        r = _put(ws, r, [x["RULE_ID"], x["NEW_FILE_STATUS"], x["TRADE"], x["WHAT"] + " — " + x["WHY"], None, None,
                         "—", "لا", x["SUPERSEDED_BY"]], GREY)

    # ---------------------------------------------------------------- openings
    ws = wb.create_sheet("الفتحات Openings")
    cols = ["الرقم", "النوع", "العرض م", "الارتفاع م", "حالة الارتفاع", "الجدار", "السمك مم", "الغرف",
            "الحالة", "ملاحظات"]
    r = _head(ws, cols, [22, 15, 10, 11, 24, 14, 10, 34, 26, 70], "OPENING REGISTER (§P)",
              f"{op['WITH_A_USABLE_HEIGHT']} of {op['COUNT']} openings carry a height, and every one of those comes "
              f"from the temporary default. The drawing set contains {op['HEIGHTS_IN_THE_DRAWING_SET']} opening "
              f"heights.")
    for x in op["ROWS"]:
        fill = GREEN if x["HEIGHT_M"] is not None else (PEACH if x["TYPE"] == "UNKNOWN" else CREAM)
        r = _put(ws, r, [x["OPENING_ID"], x["TYPE"], x["WIDTH_M"], x["HEIGHT_M"], x["HEIGHT_STATE"],
                         x["HOST_WALL_ID"], x["HOST_WALL_THICKNESS_MM"], ", ".join(x["ROOMS"]) or "—",
                         x["STATUS"], " | ".join(z for z in (x["NOTE"], x["TYPE_CONFLICT"]) if z)], fill)
        for c in (3, 4):
            ws.cell(r - 1, c).number_format = "0.000"

    # ---------------------------------------------------------------- audit backup: rule and parameter per figure
    ws = wb.create_sheet("تدقيق الحساب Audit")
    cols = ["الرقم", "البند", "الكمية", "الوحدة", "RULE_ID", "PARAMETER_SOURCE", "المعادلة / Formula",
            "قيمة مؤقتة", "فتحات معلقة", "يلغي قيمة سابقة", "الحالة"]
    r = _head(ws, cols, [9, 36, 12, 8, 30, 42, 92, 12, 40, 44, 22], "CALCULATION AUDIT (§W)",
              "Every recalculated figure, the rule that produced it and the parameter it consumed. "
              "No geometry stage was re-run.")
    for x in qs["ROWS"]:
        r = _put(ws, r, [x["QUANTITY_ID"], x["BOQ_ITEM"], x["MEASURED_NET_QUANTITY"], x["UNIT"],
                         ", ".join(x["RULE_ID"]) or "—", x["PARAMETER_SOURCE"], x["FORMULA"],
                         "نعم TD-02" if x["USES_TEMPORARY_DEFAULT"] else "لا",
                         ", ".join(f"{o.get('OPENING_ID', '')}({o.get('WIDTH_M', '')})"
                                   for o in x["RESIDUAL_OPENINGS"] if o.get("OPENING_ID")) or "—",
                         (f"{x['SUPERSEDES']['PREVIOUS']} {x['SUPERSEDES']['UNIT']} — {x['SUPERSEDES']['WHY']}"
                          if x["SUPERSEDES"] else "—"),
                         STATUS_AR[x["STATUS"]]], STATUS_FILL[x["STATUS"]])
        ws.cell(r - 1, 3).number_format = "0.0000"
    r = _band(ws, r + 1, "حساب المباني جدار بجدار / BLOCKWORK, WALL BY WALL", len(cols))
    for x in bw["ROWS"]:
        r = _put(ws, r, [x["WALL_ID"], ", ".join(x["ROOMS"]) or "—", x["NET_AREA_M2"], "M2", "US-06, QP-02",
                         f"height {x['HEIGHT_M']} m, thickness {x['THICKNESS_MM']} mm", x["ARITHMETIC"],
                         "نعم TD-02" if x["OPENINGS_DEDUCTED"] else "لا",
                         ", ".join(f"{o['OPENING_ID']}({o['W']})" for o in x["OPENINGS_PENDING"]) or "—",
                         "—", STATUS_AR[x["STATUS"]]], STATUS_FILL[x["STATUS"]])
        ws.cell(r - 1, 3).number_format = "0.0000"

    # ---------------------------------------------------------------- questions
    ws = wb.create_sheet("الأسئلة Questions")
    cols = ["الرقم", "الحالة", "السؤال / Question", "الجواب أو السبب", "ما الذي يعتمد عليه"]
    r = _head(ws, cols, [10, 22, 62, 96, 52], "QUESTION LEDGER (§R)", ql["RULE"])
    r = _band(ws, r, "مغلقة / CLOSED - do not ask again", 5)
    for x in ql["CLOSED"]:
        r = _put(ws, r, [x["DECISION_ID"], "مغلق / closed", x["QUESTION"], x["ANSWERED_BY"], "—"], GREEN)
    r = _band(ws, r, "مفتوحة / STILL OPEN", 5)
    for x in ql["STILL_OPEN"]:
        r = _put(ws, r, [x["ID"], x["KIND"], x["QUESTION"], x["WHY"], x["BLOCKS"]], PEACH)

    # ---------------------------------------------------------------- object identity, the audit's §3
    ident = json.loads((OUT / "QORTUBA_WALL_OBJECT_IDENTITY.json").read_text("utf-8"))
    ws = wb.create_sheet("هوية الجدران Identity")
    cols = ["الجدار", "السمك مم", "الطول م", "الصنف / Object class", "مباني؟", "طبقات CAD", "نوع الشريط",
            "أدوار الأوجه", "حالة السمك", "الغرف", "الدليل / Evidence", "الحالة"]
    r = _head(ws, cols, [14, 10, 10, 22, 10, 26, 16, 34, 26, 30, 96, 30],
              "WALL OBJECT IDENTITY - what each measured band actually is",
              "Two faces with a measured spacing are a geometric pair. Only a masonry wall may become a blockwork "
              "quantity: a column, a stair shaft and a drafting arrow all report a thickness too.")
    for x in sorted(ident["ROWS"], key=lambda z: (-z["THICKNESS_MM"], -z["LENGTH_M"])):
        r = _put(ws, r, [x["WALL_ID"], x["THICKNESS_MM"], x["LENGTH_M"], x["PHYSICAL_OBJECT_CLASS"],
                         "نعم" if x["BLOCKWORK_CONFIRMED"] else "لا", ", ".join(x["CAD_LAYERS"]), x["BAND_TYPE"],
                         " / ".join(x["FACE_ROLES"]), x["THICKNESS_STATUS"], ", ".join(x["ROOMS"]) or "—",
                         " | ".join(x["EVIDENCE"]), x["STATUS"]],
                 GREEN if x["BLOCKWORK_CONFIRMED"] else GREY)
        ws.cell(r - 1, 3).number_format = "0.000"

    # ---------------------------------------------------------------- historical registry, unchanged
    ws = wb.create_sheet("سوابق تاريخية Precedent")
    cols = ["الرقم", "البند / Trade", "البند / Item", "القاعدة / Rule", "وحدة التسعير", "الملف المصدر", "الورقة",
            "مستوى القاعدة", "أمان التعميم", "تُطبق بدون المالك"]
    r = _head(ws, cols, [8, 16, 30, 62, 11, 30, 16, 20, 26, 18], "URBAN PROJECTS HISTORICAL BOQ PRECEDENT",
              "Reference only. §T: a SAFE_URBAN_STANDARD_CANDIDATE never applies on its own — only an approved "
              "Urban standard does.")
    for x in reg["ROWS"]:
        r = _put(ws, r, [x["RULE_ID"], x["TRADE"], x["ITEM"], x["RULE_DESCRIPTION"], x["PRICING_UNIT"],
                         x["SOURCE_WORKBOOK_TITLE_AR"] or "لا سابقة", x["SOURCE_SHEET"],
                         LEVEL_AR[x["RULE_LEVEL"]], x["GENERALISATION_SAFETY"], "لا"],
                 GREY if x["GENERALISATION_SAFETY"] == "CONTRACTOR_SPECIFIC" else SUB)

    # ---------------------------------------------------------------- room backup, last
    ws = wb.create_sheet("حساب الغرف Rooms")
    floors = {f["ROOM_ID"]: f for f in json.loads((QS / "QORTUBA_QS01_FLOOR_CALCULATIONS.json").read_text("utf-8"))["ROWS"]}
    cols = ["الغرفة / Room", "التصنيف", "المساحة م2", "محيط الجدار م", "وجه الجدار م", "عرض الأبواب م",
            "عرض الزجاج م", "النعلة م.ط", "البروفايل م.ط", "مساحة الجدار م2", "خصم الأبواب م2", "الحساب"]
    r = _head(ws, cols, [26, 22, 12, 14, 13, 13, 13, 12, 13, 14, 14, 62],
              "CALCULATION BACKUP - ROOM BY ROOM", rm["RULE"] + ".  This is the workpaper, not the bill.")
    for x in rm["ROWS"]:
        f = floors.get(x["ROOM_ID"], {})
        r = _put(ws, r, [x["ROOM"], x["FINISH_CLASS"], f.get("METHOD_A_CAD_POLYGON_AREA_M2"),
                         x["GROSS_WALL_LINE_LM"], x["WALL_FACE_LM"], x["DOOR_OPENING_LM"], x["GLAZED_OPENING_LM"],
                         x["SKIRTING_LM"], x["HIDDEN_PROFILE_LM"], x["GROSS_WALL_AREA_M2"], x["DOOR_DEDUCTION_M2"],
                         x["SKIRTING_ARITHMETIC"]],
                 GREEN if x["FINISH_CLASS"] == "DRY_ROOM" else CREAM)
        for c in (3, 4, 5, 6, 7, 8, 9, 10, 11):
            ws.cell(r - 1, c).number_format = "0.000"

    OUT.mkdir(parents=True, exist_ok=True)
    wb.save(FILE)
    return FILE


if __name__ == "__main__":
    print("wrote", build())
