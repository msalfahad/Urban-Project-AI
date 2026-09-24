"""ALRASHED_DETAILED_QUANTITY_TAKEOFF - the frozen measurement, opened up so it can be read without AutoCAD.

Nothing here is a new measurement.  Every room area in this workbook is the frozen area; what is new is that the
area is shown as the rectangles it is actually made of, so a reader can follow 6.30 x 4.00 = 25.20 rather than
trust a single number.  The decomposition is exact by construction - the plan is axis-aligned, a room is a whole
number of grid cells, and the greedy maximal-rectangle cover sums back to the frozen figure to the micrometre.

The historical workbook supplied no quantity to this file.  Its only appearance is by name, in the sources sheet,
as the thing this takeoff is NOT built from.
"""

from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import (final_takeoff as FT, geometry as G, owner_inputs as OI,
                                                          quantities as Q, takeoff as TK, validation_amendment as VA,
                                                          window_standard as WS)

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
H = OI.AR01_WALL_HEIGHT_M
FROZEN_DIGEST = "ae259eaba3203798"
FROZEN_COMMIT = "3e847af"
PART_LETTERS = ("أ", "ب", "ج", "د", "هـ", "و", "ز", "ح", "ط", "ي", "ك", "ل", "م", "ن", "س", "ع")

FLOORS_AR = {"BASEMENT": "السرداب", "GROUND": "الأرضي", "FIRST": "الأول", "ROOF": "السطح"}
ROLES_AR = {
    "INTERNAL_ROOM": "غرفة داخلية", "WET_ROOM": "غرفة رطبة", "KITCHEN": "مطبخ",
    "EXTERNAL_OR_OPEN": "خارجي / مكشوف", "STAIR_OR_LANDING": "درج / بسطة",
    "UNNAMED_ON_DRAWING": "غير مسماة على المخطط", "WALL_MATERIAL_OR_SLIVER": "مادة جدار",
}


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return ""


# ------------------------------------------------------------------ the decomposition
def rectangles(cells, xs, ys):
    """Cover a room's cells with the fewest large rectangles, greedily and deterministically.

    At each step the largest rectangle of unused cells is taken.  Because the cells tile the room exactly and a
    rectangle is a whole number of them, the areas sum to the room's area with no tolerance at all - the cover
    only changes how the same number is written down.
    """
    rem = set(cells)
    out = []
    while rem:
        best = None
        for i0, j0 in sorted(rem):
            hi = i0
            while (hi + 1, j0) in rem:
                hi += 1
            j1 = j0
            while True:
                area = (xs[hi + 1] - xs[i0]) * (ys[j1 + 1] - ys[j0])
                if best is None or area > best[0] + 1e-12:
                    best = (area, i0, j0, hi, j1)
                nj = j1 + 1
                lo = i0 - 1
                for i in range(i0, hi + 1):
                    if (i, nj) in rem:
                        lo = i
                    else:
                        break
                if lo < i0:
                    break
                hi, j1 = lo, nj
        _a, i0, j0, i1, j1 = best
        out.append({"X0": xs[i0], "Y0": ys[j0], "X1": xs[i1 + 1], "Y1": ys[j1 + 1],
                    "LENGTH_EXACT": xs[i1 + 1] - xs[i0], "WIDTH_EXACT": ys[j1 + 1] - ys[j0],
                    "LENGTH_M": round(xs[i1 + 1] - xs[i0], 4), "WIDTH_M": round(ys[j1 + 1] - ys[j0], 4),
                    "AREA_EXACT": (xs[i1 + 1] - xs[i0]) * (ys[j1 + 1] - ys[j0])})
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                rem.discard((i, j))
    out.sort(key=lambda r: -r["AREA_EXACT"])
    for k, r in enumerate(out):
        r["PART"] = f"جزء {PART_LETTERS[k]}" if k < len(PART_LETTERS) else f"جزء {k + 1}"
        r["AREA_M2"] = round(r["AREA_EXACT"], 4)
        r["CALCULATION"] = f"{r['LENGTH_M']:.4f} × {r['WIDTH_M']:.4f} = {r['AREA_EXACT']:.4f}"
    return out


def _openings_by_room(ents, floor, g, rooms, by_ref):
    """Which openings sit on which room's boundary - the same proximity test the frozen wet-room pass used."""
    xs, ys = g["XS"], g["YS"]
    ops = Q.opening_register(ents, floor, g, Q._block_names())
    out = collections.defaultdict(list)
    for r in rooms:
        c = by_ref.get(r["ROOM_REF"])
        cells = set(c["CELLS"]) if c else set()
        for o in ops:
            if o["WIDTH_M"] is None:
                continue
            hit = False
            for d in (0.15, 0.35):
                for s in (-1, 1):
                    px, py = ((o["X"], o["Y"] + s * d) if o["RUNS"] == "ALONG_X" else (o["X"] + s * d, o["Y"]))
                    for i, j in cells:
                        if xs[i] <= px <= xs[i + 1] and ys[j] <= py <= ys[j + 1]:
                            hit = True
                            break
                    if hit:
                        break
                if hit:
                    break
            if hit:
                out[r["ROOM_REF"]].append(o)
    return out


def room_model(ents):
    """Every room of every floor, its frozen area, and the rectangles that make it up."""
    floors = []
    for floor in TK.FLOORS:
        g = G.grid(ents, G.WINDOWS[floor])
        comps = G.rooms(g)
        _g, _tr, _labs, rows, closure = TK.floor_rows(ents, floor)
        by_ref = {f"{floor[:2]}-{k:03d}": c for k, c in enumerate(comps)}
        ops = _openings_by_room(ents, floor, g, rows, by_ref)
        out = []
        for r in rows:
            c = by_ref[r["ROOM_REF"]]
            parts = rectangles(c["CELLS"], g["XS"], g["YS"])
            exact = sum(p["AREA_EXACT"] for p in parts)
            cad = sum((g["XS"][i + 1] - g["XS"][i]) * (g["YS"][j + 1] - g["YS"][j]) for i, j in c["CELLS"])
            doors = [o for o in ops.get(r["ROOM_REF"], []) if o["TYPE"] == "DOOR"]
            row = dict(r)
            row.update({
                "PARTS": parts,
                "PARTS_SUM_M2": round(exact, 4),
                "CAD_POLYGON_AREA_M2": r["AREA_M2"],
                "DECOMPOSITION_VARIANCE_M2": round(exact - cad, 9),
                "ROUNDING_DISPLAY_VARIANCE_M2": round(round(exact, 4) - r["AREA_M2"], 6),
                "DOOR_WIDTH_ON_BOUNDARY_M": round(sum(o["WIDTH_M"] for o in doors), 3),
                "DOOR_COUNT_ON_BOUNDARY": len(doors),
                "FLOOR_AR": FLOORS_AR[floor], "ROLE_AR": ROLES_AR.get(r["ROLE"], r["ROLE"]),
                "MEASUREMENT_BASIS": "exact rectilinear decomposition of the drawn wall faces",
            })
            out.append(row)
        out.sort(key=lambda x: (-x["AREA_M2"], x["ROOM_REF"]))
        floors.append({"FLOOR": floor, "FLOOR_AR": FLOORS_AR[floor], "LEVEL_M": TK.LEVELS[floor],
                       "ROOMS": out, "CLOSURE": closure,
                       "FLOOR_TOTAL_M2": round(sum(x["AREA_M2"] for x in out), 4)})
    return floors


# ------------------------------------------------------------------ one derived item the frozen file does not carry
SKIRTING_ROLES = ("INTERNAL_ROOM", "STAIR_OR_LANDING", "UNNAMED_ON_DRAWING")


def skirting(floors):
    """Skirting length per room: the room's own perimeter less the doors on it.

    This is NOT in the frozen takeoff.  It is derived from the frozen geometry and published as a draft line so
    the owner can accept or reject the scope; wet rooms are excluded because US-18 says a fully tiled face carries
    no skirting.  The profile (بروفايل) has no drawn evidence at all and is left as a source request.
    """
    rows = []
    for f in floors:
        for r in f["ROOMS"]:
            if r["ROLE"] not in SKIRTING_ROLES:
                continue
            net = r["PERIMETER_M"] - r["DOOR_WIDTH_ON_BOUNDARY_M"]
            rows.append({"FLOOR": r["FLOOR"], "FLOOR_AR": r["FLOOR_AR"], "ROOM_REF": r["ROOM_REF"],
                         "ROOM": r["NAME"], "ROLE": r["ROLE"],
                         "PERIMETER_M": r["PERIMETER_M"],
                         "DOOR_DEDUCTION_M": r["DOOR_WIDTH_ON_BOUNDARY_M"],
                         "SKIRTING_LENGTH_M": round(net, 3),
                         "STATUS": "DERIVED_NOT_IN_FROZEN_TAKEOFF",
                         "RULE": "perimeter less the door openings on the same room",
                         "NOTES": "wet and service rooms are excluded: US-18 puts porcelain on the whole face"})
    return rows


PROFILE_STEEL = {
    "ITEM": "بروفايل / حديد مشغول", "UNIT": "lm", "QUANTITY": None,
    "STATUS": "SOURCE_REQUIRED",
    "WHY": "no profile, balustrade or handrail is drawn on the three issued plans.  The historical workbook "
           "claims 57 lm; that claim is FIELD_VERIFICATION_REQUIRED and is not turned into a quantity here",
}


def build():
    a = FT.assemble()
    ents = a["ents"]
    floors = room_model(ents)
    sk = skirting(floors)
    model = {"assembly": a, "floors": floors, "skirting": sk}
    model["project_total_m2"] = round(sum(f["FLOOR_TOTAL_M2"] for f in floors), 4)
    return model


# ------------------------------------------------------------------ the workbook
SHEETS = ["ملخص الحصر", "حصر المساحات", "الأرضيات", "كسوة الجدران", "النعلة والبروفايل", "العازل",
          "الأسقف", "الأبواب والشبابيك", "المباني", "المساح والصبغ", "السطح والخارجي",
          "BOQ حسب البند", "المصادر والمراجعة"]
FLOOR_FINISH_ROLES = ("INTERNAL_ROOM", "WET_ROOM", "KITCHEN", "STAIR_OR_LANDING", "UNNAMED_ON_DRAWING")
HEAD_FILL = "2F5597"
BAND_FILL = "D9E2F3"
TOTAL_FILL = "FFF2CC"


def _style(ws, widths, freeze="A2"):
    from openpyxl.styles import Alignment, Font, PatternFill
    ws.sheet_view.rightToLeft = True
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF", size=11)
        c.fill = PatternFill("solid", fgColor=HEAD_FILL)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 30
    for col, w in zip("ABCDEFGHIJKLMNOP", widths):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = freeze


def _fill_row(ws, r, colour, bold=True, last="L"):
    from openpyxl.styles import Font, PatternFill
    for c in ws[r]:
        if c.column_letter > last:
            continue
        c.fill = PatternFill("solid", fgColor=colour)
        if bold:
            c.font = Font(bold=True)


def area_sheet(ws, m):
    """FLOOR -> ROOM -> the rectangles the room is made of -> room total -> floor total -> project total."""
    ws.append(["الدور", "رمز الغرفة", "اسم الغرفة", "التصنيف", "الجزء", "الطول (م)", "العرض (م)",
               "المساحة (م²)", "طريقة الحساب", "مساحة المضلع من الكاد (م²)", "الفرق (م²)", "الأساس / ملاحظات"])
    room_cell, floor_cell = {}, {}
    for f in m["floors"]:
        for r in f["ROOMS"]:
            first = ws.max_row + 1
            for p in r["PARTS"]:
                ws.append([r["FLOOR_AR"], r["ROOM_REF"], r["NAME"] or "—", r["ROLE_AR"], p["PART"],
                           p["LENGTH_EXACT"], p["WIDTH_EXACT"], None, p["CALCULATION"], None, None,
                           r["MEASUREMENT_BASIS"]])
                rr = ws.max_row
                ws.cell(rr, 8).value = f"=F{rr}*G{rr}"
                for col in (6, 7):
                    ws.cell(rr, col).number_format = "0.0000"
                ws.cell(rr, 8).number_format = "0.000"
            last = ws.max_row
            ws.append([r["FLOOR_AR"], r["ROOM_REF"], r["NAME"] or "—", r["ROLE_AR"], "إجمالي الغرفة",
                       None, None, None, f"مجموع {len(r['PARTS'])} جزء",
                       r["CAD_POLYGON_AREA_M2"], None,
                       "المساحة المجمدة كما هي؛ التقسيم يوضح الحساب ولا يغيّره"])
            t = ws.max_row
            ws.cell(t, 8).value = f"=SUM(H{first}:H{last})"
            ws.cell(t, 11).value = f"=H{t}-J{t}"
            _fill_row(ws, t, BAND_FILL)
            room_cell[r["ROOM_REF"]] = f"'{ws.title}'!H{t}"
        refs = [room_cell[r["ROOM_REF"]].split("!")[1] for r in f["ROOMS"]]
        ws.append([f["FLOOR_AR"], None, None, None, "إجمالي الدور", None, None, None,
                   f"{len(f['ROOMS'])} فراغ", None, None,
                   f"منسوب {f['LEVEL_M']} م — كل متر مربع في نافذة المخطط يخص فراغاً واحداً فقط"])
        t = ws.max_row
        ws.cell(t, 8).value = "=" + "+".join(refs)
        _fill_row(ws, t, TOTAL_FILL)
        floor_cell[f["FLOOR"]] = f"'{ws.title}'!H{t}"
    ws.append([None, None, None, None, "إجمالي المشروع", None, None, None,
               "مجموع الأدوار الثلاثة", None, None, "لا يشمل السطح؛ السطح في ورقة السطح والخارجي"])
    t = ws.max_row
    ws.cell(t, 8).value = "=" + "+".join(c.split("!")[1] for c in floor_cell.values())
    _fill_row(ws, t, TOTAL_FILL)
    _style(ws, (12, 12, 20, 18, 10, 11, 11, 13, 26, 20, 11, 46))
    return {"ROOM": room_cell, "FLOOR": floor_cell, "PROJECT": f"'{ws.title}'!H{t}"}


def _room_finish_sheet(ws, m, ref, item_ar, rule_id, note, roles, extra_roles=()):
    """One row per room, its quantity taken by formula from the room total in the area sheet."""
    ws.append(["الدور", "رمز الغرفة", "اسم الغرفة", "التصنيف", "البند", "الوحدة", "الكمية (م²)",
               "مصدر الكمية", "معرف القاعدة", "الحالة", "ملاحظات"])
    first = ws.max_row + 1
    for f in m["floors"]:
        for r in f["ROOMS"]:
            if r["ROLE"] not in roles:
                continue
            ws.append([r["FLOOR_AR"], r["ROOM_REF"], r["NAME"] or "—", r["ROLE_AR"], item_ar, "م²", None,
                       "مساحة الغرفة في ورقة حصر المساحات", rule_id or "—", "DRAFT", note])
            ws.cell(ws.max_row, 7).value = "=" + ref["ROOM"][r["ROOM_REF"]]
    last = ws.max_row
    ws.append([None, None, None, None, "الإجمالي", "م²", None, None, None, "DRAFT", None])
    t = ws.max_row
    ws.cell(t, 7).value = f"=SUM(G{first}:G{last})"
    _fill_row(ws, t, TOTAL_FILL, last="K")
    if extra_roles:
        ws.append([])
        ws.append(["فراغات خارج هذا البند — تُدرج للاكتمال ولا تدخل الإجمالي أعلاه", None, None, None,
                   None, None, None, None, None, None, None])
        _fill_row(ws, ws.max_row, BAND_FILL, last="K")
        xf = ws.max_row + 1
        for f in m["floors"]:
            for r in f["ROOMS"]:
                if r["ROLE"] not in extra_roles:
                    continue
                ws.append([r["FLOOR_AR"], r["ROOM_REF"], r["NAME"] or "—", r["ROLE_AR"],
                           "غير مصنّف بعد", "م²", None, "مساحة الغرفة في ورقة حصر المساحات", "—",
                           "FINISH_CLASSIFICATION_PENDING",
                           "الدرج يأخذ درجات لا أرضية، والفراغ غير المسمى يحتاج تصنيفاً من المالك"])
                ws.cell(ws.max_row, 7).value = "=" + ref["ROOM"][r["ROOM_REF"]]
        xl = ws.max_row
        ws.append([None, None, None, None, "إجمالي غير المصنّف", "م²", None, None, None,
                   "FINISH_CLASSIFICATION_PENDING", None])
        ws.cell(ws.max_row, 7).value = f"=SUM(G{xf}:G{xl})"
        _fill_row(ws, ws.max_row, BAND_FILL, last="K")
    _style(ws, (12, 12, 20, 18, 22, 8, 13, 30, 14, 26, 46))
    return f"'{ws.title}'!G{t}"


def wall_sheet(ws, m):
    perim = {r["ROOM_REF"]: r["PERIMETER_M"] for f in m["floors"] for r in f["ROOMS"]}
    ws.append(["الدور", "رمز الغرفة", "الغرفة", "محيط الغرفة (م)", "الارتفاع (م)", "الكمية الإجمالية (م²)",
               "خصم الفتحات (م²)", "صافي بورسلان الجدران (م²)", "طرطشة تحضير (م²)", "عدد الفتحات",
               "معرف القاعدة", "الحالة", "ملاحظات"])
    for x in m["assembly"]["wet"]:
        ws.append([FLOORS_AR[x["FLOOR"]], x["ROOM_REF"], x["ROOM"],
                   perim.get(x["ROOM_REF"], x["CERAMIC_HOST_LENGTH_M"]), x["HEIGHT_M"],
                   None, x["OPENING_DEDUCTIONS_M2"], None, None, x["OPENINGS_ON_THIS_ROOM"],
                   "US-18", "DRAFT",
                   "الطرطشة خلف نفس الأوجه التي يغطيها البورسلان، فالمضيف واحد"])
        r = ws.max_row
        ws.cell(r, 6).value = f"=D{r}*E{r}"
        ws.cell(r, 8).value = f"=F{r}-G{r}"
        ws.cell(r, 9).value = f"=H{r}"
    ws.append([None, None, "الإجمالي", None, None, None, None, None, None, None, None, "DRAFT", None])
    t = ws.max_row
    for col in ("F", "G", "H", "I"):
        ws.cell(t, {"F": 6, "G": 7, "H": 8, "I": 9}[col]).value = f"=SUM({col}2:{col}{t - 1})"
    _fill_row(ws, t, TOTAL_FILL, last="M")
    _style(ws, (12, 12, 18, 16, 12, 18, 16, 20, 18, 12, 12, 12, 44))
    return {"PORCELAIN": f"'{ws.title}'!H{t}", "PREP": f"'{ws.title}'!I{t}"}


def skirting_sheet(ws, m):
    ws.append(["الدور", "رمز الغرفة", "الغرفة", "المحيط (م)", "خصم عرض الأبواب (م)", "طول النعلة (م.ط)",
               "الحالة", "القاعدة", "ملاحظات"])
    for x in m["skirting"]:
        ws.append([FLOORS_AR[x["FLOOR"]], x["ROOM_REF"], x["ROOM"] or "—", x["PERIMETER_M"],
                   x["DOOR_DEDUCTION_M"], None, x["STATUS"], x["RULE"], x["NOTES"]])
        r = ws.max_row
        ws.cell(r, 6).value = f"=D{r}-E{r}"
    ws.append([None, None, "الإجمالي", None, None, None, "DRAFT", None,
               "بند مشتق من الهندسة المجمدة، وليس جزءاً من الحصر المجمد — يحتاج قرار المالك على النطاق"])
    t = ws.max_row
    ws.cell(t, 6).value = f"=SUM(F2:F{t - 1})"
    _fill_row(ws, t, TOTAL_FILL, last="I")
    ws.append([])
    ws.append([PROFILE_STEEL["ITEM"], None, None, None, None, "—", PROFILE_STEEL["STATUS"], None,
               PROFILE_STEEL["WHY"]])
    _style(ws, (12, 12, 20, 14, 20, 18, 28, 34, 60))
    return f"'{ws.title}'!F{t}"


def insulation_sheet(ws, m):
    rp = m["assembly"]["rp"]
    ws.append(["الموقع", "البند", "الوحدة", "الطول (م)", "العرض (م)", "الكمية", "مصدر الكمية",
               "الحالة", "ملاحظات"])
    ws.append(["السطح", "عازل مائي للسطح", "م²", None, None, rp["WATERPROOFING_AREA_M2"],
               "مساحة السطح المحصورة داخل الدروة", "DRAFT",
               "المساحة نهائية؛ نوع العازل ونظامه قرار مواصفات"])
    roof = f"'{ws.title}'!F{ws.max_row}"
    ws.append(["الغرف الرطبة", "عازل أرضيات الغرف الرطبة", "م²", None, None, None,
               "غير مرسوم على المخططات الثلاثة", "SOURCE_REQUIRED",
               "لا يوجد تفصيل عزل أرضيات في المخططات المصدرية — لا تُخترع كمية"])
    ws.append([])
    ws.append(["مرجع تاريخي", "أساس تجاري تاريخي 950.22 م²", "—", None, None, None,
               "Sheet1!F28 = SUM(F5:F24) ويُستهلك في I11 '=1.5*F28'", "HISTORICAL_COMMERCIAL_BASIS",
               "ليست كمية غشاء: أحد مكوناتها 600.00 وهي مساحة القسيمة. لا تُقارن بكمية مقاسة ولا تدخل أي بند"])
    _style(ws, (16, 30, 8, 12, 12, 14, 40, 30, 62))
    return roof


def openings_sheet(ws, m):
    ws.append(["النوع", "الرمز", "الدور", "الغرفة", "العرض (م)", "مصدر العرض", "الارتفاع (م)",
               "مصدر الارتفاع", "المساحة (م²)", "تصنيف الدليل", "الحالة", "ملاحظات"])
    first_d = ws.max_row + 1
    for d in m["assembly"]["doors"]:
        ws.append(["باب", d["DOOR_ID"], FLOORS_AR[d["FLOOR"]], "—", d["WIDTH_M"], d["WIDTH_SOURCE"],
                   d["HEIGHT_M"], d["HEIGHT_SOURCE"], None, "—", "DRAFT", d["NOTES"]])
        r = ws.max_row
        ws.cell(r, 9).value = f"=E{r}*G{r}"
    last_d = ws.max_row
    ws.append([None, "إجمالي الأبواب", None, f"العدد {len(m['assembly']['doors'])}", None, None, None, None,
               None, None, "DRAFT", "كمية الفتحة فقط؛ نوع الضلفة ومادتها قرار شراء"])
    td = ws.max_row
    ws.cell(td, 9).value = f"=SUM(I{first_d}:I{last_d})"
    _fill_row(ws, td, BAND_FILL)
    first_w = ws.max_row + 1
    for w in m["assembly"]["windows"]:
        ws.append(["شباك", w["WINDOW_ID"], FLOORS_AR[w["FLOOR"]], w["ROOM"], w["WIDTH_M"], w["WIDTH_SOURCE"],
                   w["HEIGHT_M"], w["HEIGHT_SOURCE"], None, w["GUIDE_CATEGORY"], "DRAFT", w["NOTES"]])
        r = ws.max_row
        ws.cell(r, 9).value = f"=E{r}*G{r}"
    last_w = ws.max_row
    ws.append([None, "إجمالي الشبابيك / الألمنيوم", None, f"العدد {len(m['assembly']['windows'])}", None, None,
               None, None, None, None, "DRAFT",
               "نطاق المخطط فقط (US-21): زجاج الموقع يتجاوزه عادةً وليست كمية توريد"])
    tw = ws.max_row
    ws.cell(tw, 9).value = f"=SUM(I{first_w}:I{last_w})"
    _fill_row(ws, tw, TOTAL_FILL)
    _style(ws, (10, 12, 12, 18, 12, 30, 13, 34, 13, 22, 12, 56))
    return {"DOORS": f"'{ws.title}'!I{td}", "WINDOWS": f"'{ws.title}'!I{tw}"}


def blockwork_sheet(ws, m):
    ws.append(["الدور", "السماكة (مم)", "هوية العنصر", "طول الجدار (م)", "الارتفاع (م)",
               "الكمية الإجمالية (م²)", "خصم الفتحات (م²)", "الصافي (م²)", "الحالة", "ملاحظات"])
    cells = {150: [], 200: []}
    for b in m["assembly"]["block"]:
        ws.append([FLOORS_AR[b["FLOOR"]], b["THICKNESS_MM"], "جدار مباني", b["PLAN_LENGTH_M"], b["HEIGHT_M"],
                   None, b["OPENING_DEDUCTIONS_M2"], None, "DRAFT",
                   "الخصم موزّع على الجدران المؤكدة بنسبة طولها"])
        r = ws.max_row
        ws.cell(r, 6).value = f"=D{r}*E{r}"
        ws.cell(r, 8).value = f"=F{r}-G{r}"
        cells[b["THICKNESS_MM"]].append(f"H{r}")
    tot = {}
    for t_mm in (150, 200):
        ws.append([None, t_mm, f"إجمالي مباني {t_mm // 10} سم", None, None, None, None, None, "DRAFT", None])
        r = ws.max_row
        ws.cell(r, 8).value = "=" + "+".join(cells[t_mm])
        _fill_row(ws, r, TOTAL_FILL, last="J")
        tot[t_mm] = f"'{ws.title}'!H{r}"
    ws.append([])
    ws.append(["مستبعد — ليست جدراناً", None, None, None, None, None, None, None, "NOT_BILLED",
               "سماكات لا يبعّدها المخطط أبداً، تنشأ عند تقاطع جدارين أو رسم خط مرتين"])
    _fill_row(ws, ws.max_row, BAND_FILL, last="J")
    for x in m["assembly"]["excluded"]:
        ws.append([FLOORS_AR[x["FLOOR"]], x["THICKNESS_MM"], x["OBJECT_IDENTITY"], x["LENGTH_M"], None,
                   None, None, None, "NOT_BILLED", x["WHY"]])
    _style(ws, (12, 14, 18, 16, 12, 18, 18, 14, 14, 56))
    return tot


def plaster_sheet(ws, m):
    ws.append(["الدور", "طول الأوجه الداخلية (م)", "طول الأوجه الخارجية (م)", "الارتفاع (م)",
               "مساح داخلي إجمالي (م²)", "خصم الأبواب (م²)", "مساح داخلي صافي (م²)",
               "أوجه مكسوة بالبورسلان (م²)", "صبغ داخلي (م²)", "مساح خارجي إجمالي (م²)",
               "خصم الشبابيك (م²)", "مساح خارجي صافي (م²)", "صبغ خارجي (م²)", "الحالة"])
    first = ws.max_row + 1
    for p in m["assembly"]["pp"]:
        ws.append([FLOORS_AR[p["FLOOR"]], p["INTERNAL_FACE_LENGTH_M"], p["EXTERNAL_FACE_LENGTH_M"], p["HEIGHT_M"],
                   None, round(p["INTERNAL_PLASTER_GROSS_M2"] - p["INTERNAL_PLASTER_NET_M2"], 3), None,
                   p["TILED_FACE_AREA_M2"], None, None, p["WINDOW_DEDUCTION_M2"], None, None, "DRAFT"])
        r = ws.max_row
        ws.cell(r, 5).value = f"=B{r}*D{r}"
        ws.cell(r, 7).value = f"=E{r}-F{r}"
        ws.cell(r, 9).value = f"=G{r}-H{r}"
        ws.cell(r, 10).value = f"=C{r}*D{r}"
        ws.cell(r, 12).value = f"=J{r}-K{r}"
        ws.cell(r, 13).value = f"=L{r}"
    last = ws.max_row
    ws.append(["الإجمالي"] + [None] * 13)
    t = ws.max_row
    for idx, col in ((5, "E"), (6, "F"), (7, "G"), (8, "H"), (9, "I"), (10, "J"), (11, "K"), (12, "L"), (13, "M")):
        ws.cell(t, idx).value = f"=SUM({col}{first}:{col}{last})"
    _fill_row(ws, t, TOTAL_FILL, last="N")
    _style(ws, (12, 20, 20, 12, 20, 16, 20, 20, 16, 20, 16, 20, 16, 12))
    return {"INT_PLASTER": f"'{ws.title}'!G{t}", "INT_PAINT": f"'{ws.title}'!I{t}",
            "EXT_PLASTER": f"'{ws.title}'!L{t}", "EXT_PAINT": f"'{ws.title}'!M{t}"}


def roof_sheet(ws, m):
    rp, ref = m["assembly"]["rp"], {}
    ws.append(["الموقع", "البند", "الوحدة", "الطول (م)", "الارتفاع / العرض (م)", "المعامل", "الكمية",
               "مصدر الكمية", "الحالة", "ملاحظات"])
    ws.append(["السطح", "مساحة السطح", "م²", None, None, None, rp["ROOF_AREA_ENCLOSED_M2"],
               "المساحة المحصورة داخل حد السطح المرسوم", "DRAFT", "مادة التشطيب غير محددة على المخطط"])
    ref["ROOF"] = f"'{ws.title}'!G{ws.max_row}"
    ws.append(["السطح", "مباني الدروة", "م²", rp["PARAPET_RUN_M"], rp["PARAPET_HEIGHT_M"], 1, None,
               "طول الدروة × ارتفاعها (AR-06)", "DRAFT", rp["PARAPET_RUN_BASIS"]])
    r = ws.max_row
    ws.cell(r, 7).value = f"=D{r}*E{r}*F{r}"
    ref["PARAPET_BLOCK"] = f"'{ws.title}'!G{r}"
    for item, key in (("مساح الدروة (الوجهين)", "PARAPET_PLASTER"), ("صبغ الدروة (الوجهين)", "PARAPET_PAINT")):
        ws.append(["السطح", item, "م²", rp["PARAPET_RUN_M"], rp["PARAPET_HEIGHT_M"], 2, None,
                   "طول الدروة × ارتفاعها × وجهين", "DRAFT", rp["PLASTER_AND_PAINT_BASIS"]])
        r = ws.max_row
        ws.cell(r, 7).value = f"=D{r}*E{r}*F{r}"
        ref[key] = f"'{ws.title}'!G{r}"
    ws.append([])
    ws.append(["المساحات الخارجية والمواقف", None, None, None, None, None, None, None, None, None])
    _fill_row(ws, ws.max_row, BAND_FILL, last="J")
    first = ws.max_row + 1
    for f in m["floors"]:
        for x in f["ROOMS"]:
            if x["ROLE"] != "EXTERNAL_OR_OPEN":
                continue
            ws.append([x["FLOOR_AR"], x["NAME"] or "—", "م²", None, None, None, x["AREA_M2"],
                       f"مساحة مقاسة — {x['ROOM_REF']}", "FINISH_CLASSIFICATION_PENDING",
                       "المساحة نهائية؛ لا مادة تشطيب منصوصة على المخطط (AR-08)"])
    last = ws.max_row
    ws.append([None, "إجمالي المساحات الخارجية", "م²", None, None, None, None, None, "DRAFT", None])
    t = ws.max_row
    ws.cell(t, 7).value = f"=SUM(G{first}:G{last})"
    _fill_row(ws, t, TOTAL_FILL, last="J")
    ref["EXTERNAL"] = f"'{ws.title}'!G{t}"
    _style(ws, (22, 26, 8, 14, 18, 10, 14, 34, 28, 54))
    return ref


# ------------------------------------------------------------------ the BOQ, one line per item
def boq_items(m, ref):
    t = m["assembly"]["totals"]
    I = [
        ("AR-FL-01", "الأرضيات", "بورسلان / سيراميك أرضيات — جميع الفراغات الداخلية", "م²",
         ref["FLOORS"], t["INTERNAL_FLOOR_AREA_M2"] + t["STAIR_PLAN_AREA_M2"] + t["UNNAMED_ON_DRAWING_M2"],
         "مجموع مساحات الغرف في ورقة حصر المساحات", None, "PRICING_BASIS_REQUIRED",
         "تقسيم البورسلان عن السيراميك قرار أسعار لا قياس"),
        ("AR-FL-02", "الأرضيات", "منها أرضيات الغرف الرطبة والخدمية", "م²", None,
         t["WET_AND_SERVICE_FLOOR_AREA_M2"], "مساحات مقاسة", "US-18", "FINAL_QUANTITY_AVAILABLE",
         "مضمّنة داخل البند أعلاه ولا تُجمع معه"),
        ("AR-WP-01", "كسوة الجدران", "بورسلان جدران بكامل الارتفاع في الغرف الرطبة", "م²",
         ref["PORCELAIN"], t["WALL_PORCELAIN_NET_M2"], "محيط الغرفة × 3.60 ناقص فتحاتها", "US-18",
         "FINAL_QUANTITY_AVAILABLE", ""),
        ("AR-WP-02", "كسوة الجدران", "طرطشة تحضير خلف بورسلان الجدران", "م²",
         ref["PREP"], t["TILE_PREPARATION_M2"], "نفس مضيف البورسلان", "US-18",
         "FINAL_QUANTITY_AVAILABLE", ""),
        ("AR-IN-01", "العازل", "عازل مائي للسطح", "م²", ref["INSULATION"], t["WATERPROOFING_M2"],
         "مساحة السطح المحصورة داخل الدروة", None, "FINAL_QUANTITY_AVAILABLE",
         "عزل أرضيات الغرف الرطبة غير مرسوم — طلب مصدر"),
        ("AR-BL-01", "المباني", "مباني 15 سم", "م²", ref["BLOCK150"], t["BLOCKWORK_150_NET_M2"],
         "طول الجدار × 3.60 ناقص الفتحات", None, "FINAL_QUANTITY_AVAILABLE", ""),
        ("AR-BL-02", "المباني", "مباني 20 سم", "م²", ref["BLOCK200"], t["BLOCKWORK_200_NET_M2"],
         "طول الجدار × 3.60 ناقص الفتحات", None, "FINAL_QUANTITY_AVAILABLE", ""),
        ("AR-PL-01", "المساح والصبغ", "مساح داخلي", "م²", ref["INT_PLASTER"], t["INTERNAL_PLASTER_NET_M2"],
         "أوجه الجدران الداخلية × 3.60 ناقص الأبواب", None, "FINAL_QUANTITY_AVAILABLE", ""),
        ("AR-PT-01", "المساح والصبغ", "صبغ داخلي", "م²", ref["INT_PAINT"], t["INTERNAL_PAINT_M2"],
         "المساح الداخلي ناقص الأوجه المكسوة بالكامل", "US-18", "FINAL_QUANTITY_AVAILABLE",
         "الوجه المكسو بالبورسلان لا يُصبغ"),
        ("AR-PL-02", "المساح والصبغ", "مساح خارجي", "م²", ref["EXT_PLASTER"], t["EXTERNAL_PLASTER_NET_M2"],
         "أوجه الجدران الخارجية × 3.60 ناقص الشبابيك", None, "FINAL_QUANTITY_AVAILABLE", ""),
        ("AR-PT-02", "المساح والصبغ", "صبغ خارجي", "م²", ref["EXT_PAINT"], t["EXTERNAL_PAINT_M2"],
         "مساحة المساح الخارجي", None, "FINAL_QUANTITY_AVAILABLE", ""),
        ("AR-CL-01", "الأسقف", "سقف عادي (مساح وصبغ)", "م²", ref["CEILING"], t["CEILING_M2"],
         "المساحة المسقوفة المحصورة", None, "FINAL_QUANTITY_AVAILABLE",
         "الأسقف المعلقة أو الديكورية تحتاج مخطط أسقف ولم تُقَس"),
        ("AR-RF-01", "السطح والخارجي", "مباني الدروة", "م²", ref["PARAPET_BLOCK"], t["PARAPET_BLOCKWORK_M2"],
         "طول الدروة × 1.00 (AR-06)", None, "FINAL_QUANTITY_AVAILABLE", ""),
        ("AR-RF-02", "السطح والخارجي", "مساح الدروة — الوجهين", "م²", ref["PARAPET_PLASTER"],
         t["PARAPET_PLASTER_M2"], "طول الدروة × 1.00 × 2", None, "FINAL_QUANTITY_AVAILABLE", ""),
        ("AR-RF-03", "السطح والخارجي", "صبغ الدروة — الوجهين", "م²", ref["PARAPET_PAINT"],
         t["PARAPET_PAINT_M2"], "طول الدروة × 1.00 × 2", None, "FINAL_QUANTITY_AVAILABLE", ""),
        ("AR-AL-01", "الألمنيوم", "شبابيك ألمنيوم — نطاق المخطط", "م²", ref["WINDOWS"], t["ALUMINIUM_M2"],
         "عرض مقاس من المخطط × ارتفاع من الدليل", WS.RULE_ID, "DRAWING_SCOPE_ONLY",
         "US-21: ليست كمية توريد؛ زجاج الموقع يتجاوز نطاق المخطط عادةً"),
        ("AR-DR-01", "الأبواب", "فتحات الأبواب", "م²", ref["DOORS"], t["DOOR_AREA_M2"],
         "عرض مقاس بين القائمين × 2.20 (AR-02)", None, "PRICING_BASIS_REQUIRED",
         f"{t['DOOR_COUNT']} باباً؛ مادة الضلفة ونوعها قرار شراء"),
        ("AR-EX-01", "السطح والخارجي", "مساحات خارجية ومواقف", "م²", ref["EXTERNAL"], t["EXTERNAL_OPEN_AREA_M2"],
         "مساحات مقاسة (AR-08)", None, "FINISH_CLASSIFICATION_PENDING",
         "المساحة نهائية والمادة غير منصوصة"),
        ("AR-SK-01", "النعلة والبروفايل", "نعلة (وزرة) للغرف غير الرطبة", "م.ط", ref["SKIRTING"],
         round(sum(x["SKIRTING_LENGTH_M"] for x in m["skirting"]), 3),
         "محيط الغرفة ناقص عروض أبوابها", None, "DERIVED_NOT_IN_FROZEN_TAKEOFF",
         "بند مشتق — يحتاج قرار المالك على النطاق قبل اعتماده"),
        ("AR-SK-02", "النعلة والبروفايل", "بروفايل / حديد مشغول", "م.ط", None, None,
         "لا يوجد على المخططات", None, "SOURCE_REQUIRED",
         "ادّعاء تاريخي بـ 57 م.ط يحتاج تحقق ميداني ولا يُحوَّل إلى كمية"),
    ]
    return I


def boq_sheet(ws, m, ref):
    ws.append(["كود البند", "البند", "الوصف", "الوحدة", "الكمية المقاسة", "الهالك %", "كمية الشراء",
               "سعر الوحدة", "الإجمالي", "مصدر الكمية", "معرف القاعدة", "حالة الكمية", "حالة الاعتماد",
               "ملاحظات"])
    cells = {}
    for code, trade, desc, unit, cell, value, source, rule, status, notes in boq_items(m, ref):
        ws.append([code, trade, desc, unit, None, None, None, None, None, source, rule or "—", status,
                   "DRAFT", notes])
        r = ws.max_row
        ws.cell(r, 5).value = ("=" + cell) if cell else value
        ws.cell(r, 7).value = f'=IF(F{r}="","",E{r}*(1+F{r}/100))'
        ws.cell(r, 9).value = f'=IF(OR(G{r}="",H{r}=""),"",G{r}*H{r})'
        cells[code] = f"'{ws.title}'!E{r}"
    ws.append([None, None, "إجمالي المبالغ", None, None, None, None, None, None, None, None, None,
               "DRAFT", "يبقى فارغاً حتى تُدخل الأسعار — DS-01: لا خانة تجمع كمية وسعراً"])
    t = ws.max_row
    ws.cell(t, 9).value = f'=IF(COUNT(I2:I{t - 1})=0,"",SUM(I2:I{t - 1}))'
    _fill_row(ws, t, TOTAL_FILL, last="N")
    _style(ws, (12, 18, 46, 8, 15, 10, 14, 12, 14, 38, 14, 26, 14, 56))
    return cells


# ------------------------------------------------------------------ the fifteen checks
def qa(m, wbinfo):
    t = m["assembly"]["totals"]
    rooms = [r for f in m["floors"] for r in f["ROOMS"]]
    checks = []

    def add(key, ok, detail):
        checks.append({"CHECK": key, "PASS": bool(ok), "DETAIL": detail})

    add("QA-01_DECOMPOSITION_IS_EXACT",
        all(r["DECOMPOSITION_VARIANCE_M2"] == 0 for r in rooms),
        {"MAX_VARIANCE_M2": max(abs(r["DECOMPOSITION_VARIANCE_M2"]) for r in rooms),
         "ROOMS": len(rooms), "PARTS": sum(len(r["PARTS"]) for r in rooms)})
    add("QA-02_ROOM_TOTAL_EQUALS_FROZEN_AREA",
        all(abs(r["PARTS_SUM_M2"] - r["CAD_POLYGON_AREA_M2"]) < 5e-5 for r in rooms),
        "every room total in the workbook is the frozen room area")
    add("QA-03_FLOOR_TOTAL_EQUALS_SUM_OF_ROOMS",
        all(abs(f["FLOOR_TOTAL_M2"] - round(sum(r["AREA_M2"] for r in f["ROOMS"]), 4)) < 1e-6
            for f in m["floors"]),
        {f["FLOOR"]: f["FLOOR_TOTAL_M2"] for f in m["floors"]})
    add("QA-04_PROJECT_TOTAL_EQUALS_SUM_OF_FLOORS",
        abs(m["project_total_m2"] - sum(f["FLOOR_TOTAL_M2"] for f in m["floors"])) < 1e-6,
        {"PROJECT_TOTAL_M2": m["project_total_m2"]})
    refs = [r["ROOM_REF"] for r in rooms]
    add("QA-05_ROOM_REFS_ARE_UNIQUE", len(refs) == len(set(refs)), {"ROOMS": len(refs)})
    frozen_refs = {r["ROOM_REF"] for f in m["assembly"]["floors"] for r in f["ROOMS"]}
    add("QA-06_SAME_ROOM_SET_AS_THE_FROZEN_TAKEOFF", set(refs) == frozen_refs,
        {"ONLY_HERE": sorted(set(refs) - frozen_refs), "ONLY_FROZEN": sorted(frozen_refs - set(refs))})
    recomputed = {
        "INTERNAL_FLOOR_AREA_M2": round(sum(r["AREA_M2"] for r in rooms
                                            if r["ROLE"] in ("INTERNAL_ROOM", "WET_ROOM", "KITCHEN")), 3),
        "CEILING_M2": round(sum(r["AREA_M2"] for r in rooms if r["ROLE"] in FLOOR_FINISH_ROLES), 3),
        "EXTERNAL_OPEN_AREA_M2": round(sum(r["AREA_M2"] for r in rooms if r["ROLE"] == "EXTERNAL_OR_OPEN"), 3),
        "STAIR_PLAN_AREA_M2": round(sum(r["AREA_M2"] for r in rooms if r["ROLE"] == "STAIR_OR_LANDING"), 3),
    }
    add("QA-07_FROZEN_TRADE_TOTALS_REPRODUCED",
        all(abs(recomputed[k] - t[k]) < 1e-3 for k in recomputed),
        {k: {"WORKBOOK": v, "FROZEN": t[k]} for k, v in recomputed.items()})
    add("QA-08_NO_NEGATIVE_QUANTITY",
        all(r["AREA_M2"] > 0 for r in rooms)
        and all(x["NET_WALL_PORCELAIN_M2"] > 0 for x in m["assembly"]["wet"])
        and all(b["NET_AREA_M2"] > 0 for b in m["assembly"]["block"])
        and all(x["SKIRTING_LENGTH_M"] > 0 for x in m["skirting"]),
        "no area, no net wall quantity and no skirting length is zero or below")
    add("QA-09_NO_DEDUCTION_EXCEEDS_ITS_GROSS",
        all(x["OPENING_DEDUCTIONS_M2"] <= x["GROSS_WALL_PORCELAIN_M2"] for x in m["assembly"]["wet"])
        and all(b["DEDUCTION_GUARD_OK"] for b in m["assembly"]["block"])
        and all(x["DOOR_DEDUCTION_M"] < x["PERIMETER_M"] for x in m["skirting"]),
        "every deduction is smaller than the thing it is deducted from")
    add("QA-10_EVERY_BOQ_LINE_CARRIES_A_SOURCE",
        all(i[6] for i in boq_items(m, wbinfo["REF"])),
        f"{len(boq_items(m, wbinfo['REF']))} BOQ lines")
    add("QA-11_NO_RATE_NO_AMOUNT_NO_WASTE",
        wbinfo["RATES_WRITTEN"] == 0 and wbinfo["AMOUNTS_WRITTEN"] == 0 and wbinfo["WASTE_WRITTEN"] == 0,
        {"RATE_CELLS_WITH_A_VALUE": wbinfo["RATES_WRITTEN"], "AMOUNT_CELLS": wbinfo["AMOUNTS_WRITTEN"],
         "WASTE_CELLS": wbinfo["WASTE_WRITTEN"],
         "RULE": "DS-01 - quantity, waste, rate and amount are separate columns and only the quantity is filled"})
    add("QA-12_EVERY_RECORD_IS_DRAFT",
        all(r["APPROVAL_STATUS"] == "DRAFT" for r in wbinfo["EXPORT_ROWS"]),
        f"{len(wbinfo['EXPORT_ROWS'])} records, all DRAFT")
    hist = {950.22, 57.0, 1375.0, 600.16}
    leaked = sorted({r["MEASURED_QUANTITY"] for r in wbinfo["EXPORT_ROWS"]
                     if isinstance(r["MEASURED_QUANTITY"], (int, float)) and r["MEASURED_QUANTITY"] in hist})
    add("QA-13_NO_HISTORICAL_QUANTITY_ENTERED_A_LINE", not leaked,
        {"HISTORICAL_FIGURES_CHECKED": sorted(hist), "FOUND_IN_A_QUANTITY_FIELD": leaked})
    wet_refs = {x["ROOM_REF"] for x in m["assembly"]["wet"]}
    all_wet = {r["ROOM_REF"] for r in rooms if r["ROLE"] in ("WET_ROOM", "KITCHEN")}
    add("QA-14_EVERY_WET_ROOM_IS_UNDER_US_18", wet_refs == all_wet,
        {"WET_AND_KITCHEN_ROOMS": len(all_wet), "IN_THE_CLADDING_SHEET": len(wet_refs)})
    add("QA-15_THE_FROZEN_TAKEOFF_IS_UNCHANGED",
        wbinfo["FROZEN_DIGEST_NOW"] == FROZEN_DIGEST,
        {"DIGEST": wbinfo["FROZEN_DIGEST_NOW"], "EXPECTED": FROZEN_DIGEST,
         "MEANING": "this workbook re-presents the frozen measurement; it does not restate it"})
    return {"CHECKS": checks, "ALL_PASS": all(c["PASS"] for c in checks),
            "PASSED": sum(1 for c in checks if c["PASS"]), "OF": len(checks)}


# ------------------------------------------------------------------ the structured export
PROJECT_NAME = "Ahmad Abdullah Ali Al Rashed - Sabah Al Ahmad, Block D4, Plot 247"
DRAWING_REVISION = "16-11-2025, sheet row R3 - the row the issued PDF plots"
SOURCE_FILES = ["16-11-2025.dwg", "16-11-2025.pdf"]


def _rec(**kw):
    """One record of the export.  Quantity, waste, procurement, rate and amount are five separate fields (DS-01)."""
    base = {
        "PROJECT_ID": OI.PROJECT_ID, "PROJECT_NAME": PROJECT_NAME,
        "DRAWING_SET": "ARCHITECTURAL_PERMIT_SET", "DRAWING_REVISION": DRAWING_REVISION,
        "SOURCE_FILES": SOURCE_FILES,
        "FLOOR": None, "FLOOR_AR": None, "LEVEL_M": None, "ZONE": None,
        "ROOM_REF": None, "ROOM_NAME": None, "ROOM_ROLE": None,
        "TRADE": None, "ITEM_CODE": None, "ITEM": None, "SUBITEM": None,
        "COMPONENTS": None, "CALCULATION": None, "MEASUREMENT_BASIS": None,
        "DIMENSION_INPUTS": None,
        "MEASURED_QUANTITY": None, "MEASURED_UNIT": None,
        "WASTE_PERCENT": None, "PROCUREMENT_QUANTITY": None,
        "UNIT_RATE": None, "AMOUNT": None, "CURRENCY": "KWD",
        "QUANTITY_SOURCE": None, "SOURCE_TYPE": "PROJECT_DRAWING",
        "RULE_ID": None, "RULE_LEVEL": None,
        "STATUS": "FINAL_QUANTITY_AVAILABLE", "APPROVAL_STATUS": "DRAFT",
        "VERIFIED_AGAINST_FROZEN": True, "FROZEN_DIGEST": FROZEN_DIGEST,
        "HISTORICAL_DATA_USED": False,
        "GENERATED_BY": "URBAN_QS_ENGINE / ALRASHED_DETAILED_QUANTITY_TAKEOFF",
        "NOTES": None,
    }
    base.update(kw)
    return base


def export_rows(m):
    t, rows = m["assembly"]["totals"], []
    for f in m["floors"]:
        for r in f["ROOMS"]:
            comp = [{"PART": p["PART"], "LENGTH_M": p["LENGTH_M"], "WIDTH_M": p["WIDTH_M"],
                     "AREA_M2": p["AREA_M2"]} for p in r["PARTS"]]
            calc = " + ".join(p["CALCULATION"] for p in r["PARTS"])
            common = dict(FLOOR=r["FLOOR"], FLOOR_AR=r["FLOOR_AR"], LEVEL_M=f["LEVEL_M"],
                          ROOM_REF=r["ROOM_REF"], ROOM_NAME=r["NAME"], ROOM_ROLE=r["ROLE"],
                          COMPONENTS=comp, CALCULATION=calc,
                          MEASUREMENT_BASIS=r["MEASUREMENT_BASIS"],
                          MEASURED_QUANTITY=r["AREA_M2"], MEASURED_UNIT="m2",
                          QUANTITY_SOURCE="exact rectilinear decomposition of the drawn wall faces")
            if r["ROLE"] in FLOOR_FINISH_ROLES:
                rows.append(_rec(ZONE="ROOM", TRADE="PORCELAIN_FLOOR", ITEM_CODE="AR-FL-01",
                                 ITEM="Floor finish", SUBITEM=r["ROOM_REF"],
                                 RULE_ID="US-18" if r["ROLE"] in ("WET_ROOM", "KITCHEN") else None,
                                 RULE_LEVEL="URBAN_STANDARD" if r["ROLE"] in ("WET_ROOM", "KITCHEN") else None,
                                 STATUS="PRICING_BASIS_REQUIRED",
                                 NOTES="area is final; the porcelain / ceramic split is a rate decision",
                                 **common))
                rows.append(_rec(ZONE="ROOM", TRADE="CEILING", ITEM_CODE="AR-CL-01", ITEM="Ceiling, plain",
                                 SUBITEM=r["ROOM_REF"],
                                 NOTES="plain ceiling on the enclosed plan area; no ceiling plan was supplied",
                                 **common))
            elif r["ROLE"] == "EXTERNAL_OR_OPEN":
                rows.append(_rec(ZONE="EXTERNAL", TRADE="EXTERNAL_AREAS", ITEM_CODE="AR-EX-01",
                                 ITEM="External / parking area", SUBITEM=r["ROOM_REF"],
                                 RULE_ID="AR-08", RULE_LEVEL="OWNER_CONFIRMED_PROJECT_INPUT",
                                 STATUS="FINISH_CLASSIFICATION_PENDING",
                                 NOTES="area is final; the drawing states no finish material", **common))
    for x in m["assembly"]["wet"]:
        for trade, code, item in (("WALL_PORCELAIN", "AR-WP-01", "Wall porcelain, full height"),
                                  ("TILE_PREPARATION", "AR-WP-02", "Tartousha behind the porcelain")):
            rows.append(_rec(FLOOR=x["FLOOR"], FLOOR_AR=FLOORS_AR[x["FLOOR"]], ZONE="WET_ROOM",
                             ROOM_REF=x["ROOM_REF"], ROOM_NAME=x["ROOM"], ROOM_ROLE="WET_ROOM",
                             TRADE=trade, ITEM_CODE=code, ITEM=item, SUBITEM=x["ROOM_REF"],
                             DIMENSION_INPUTS={"PERIMETER_M": x["CERAMIC_HOST_LENGTH_M"],
                                               "HEIGHT_M": x["HEIGHT_M"],
                                               "HEIGHT_SOURCE": "OWNER_CONFIRMED_PROJECT_INPUT (AR-01)",
                                               "OPENINGS": x["OPENINGS_ON_THIS_ROOM"]},
                             CALCULATION=f"{x['CERAMIC_HOST_LENGTH_M']} × {x['HEIGHT_M']} − "
                                         f"{x['OPENING_DEDUCTIONS_M2']} = {x['NET_WALL_PORCELAIN_M2']}",
                             MEASUREMENT_BASIS="room perimeter less that room's own openings",
                             MEASURED_QUANTITY=x["NET_WALL_PORCELAIN_M2"], MEASURED_UNIT="m2",
                             QUANTITY_SOURCE="measured room perimeter and its own openings",
                             RULE_ID="US-18", RULE_LEVEL="URBAN_STANDARD", NOTES=x["REASON"]))
    for x in m["skirting"]:
        rows.append(_rec(FLOOR=x["FLOOR"], FLOOR_AR=FLOORS_AR[x["FLOOR"]], ZONE="ROOM",
                         ROOM_REF=x["ROOM_REF"], ROOM_NAME=x["ROOM"], ROOM_ROLE=x["ROLE"],
                         TRADE="SKIRTING", ITEM_CODE="AR-SK-01", ITEM="Skirting", SUBITEM=x["ROOM_REF"],
                         DIMENSION_INPUTS={"PERIMETER_M": x["PERIMETER_M"],
                                           "DOOR_DEDUCTION_M": x["DOOR_DEDUCTION_M"]},
                         CALCULATION=f"{x['PERIMETER_M']} − {x['DOOR_DEDUCTION_M']} = {x['SKIRTING_LENGTH_M']}",
                         MEASUREMENT_BASIS=x["RULE"],
                         MEASURED_QUANTITY=x["SKIRTING_LENGTH_M"], MEASURED_UNIT="lm",
                         QUANTITY_SOURCE="frozen room perimeter and the doors on it",
                         STATUS=x["STATUS"], VERIFIED_AGAINST_FROZEN=False, NOTES=x["NOTES"]))
    for b in m["assembly"]["block"]:
        rows.append(_rec(FLOOR=b["FLOOR"], FLOOR_AR=FLOORS_AR[b["FLOOR"]], ZONE="WALLS",
                         TRADE=f"BLOCKWORK_{b['THICKNESS_MM']}",
                         ITEM_CODE="AR-BL-01" if b["THICKNESS_MM"] == 150 else "AR-BL-02",
                         ITEM=f"Blockwork {b['THICKNESS_MM']} mm",
                         SUBITEM=f"{b['FLOOR']}-{b['THICKNESS_MM']}",
                         DIMENSION_INPUTS={"PLAN_LENGTH_M": b["PLAN_LENGTH_M"], "HEIGHT_M": b["HEIGHT_M"]},
                         CALCULATION=f"{b['PLAN_LENGTH_M']} × {b['HEIGHT_M']} − {b['OPENING_DEDUCTIONS_M2']}"
                                     f" = {b['NET_AREA_M2']}",
                         MEASUREMENT_BASIS="wall cells of a thickness the drawing dimensions",
                         MEASURED_QUANTITY=b["NET_AREA_M2"], MEASURED_UNIT="m2",
                         QUANTITY_SOURCE="measured wall lengths less the openings in them",
                         NOTES="junction artefacts are excluded; only 150 and 200 mm are billed"))
    for p in m["assembly"]["pp"]:
        for trade, code, item, qty in (
                ("INTERNAL_PLASTER", "AR-PL-01", "Internal plaster", p["INTERNAL_PLASTER_NET_M2"]),
                ("INTERNAL_PAINT", "AR-PT-01", "Internal paint", p["INTERNAL_PAINT_M2"]),
                ("EXTERNAL_PLASTER", "AR-PL-02", "External plaster", p["EXTERNAL_PLASTER_NET_M2"]),
                ("EXTERNAL_PAINT", "AR-PT-02", "External paint", p["EXTERNAL_PAINT_M2"])):
            rows.append(_rec(FLOOR=p["FLOOR"], FLOOR_AR=FLOORS_AR[p["FLOOR"]], ZONE="WALL_FACES",
                             TRADE=trade, ITEM_CODE=code, ITEM=item, SUBITEM=p["FLOOR"],
                             DIMENSION_INPUTS={"INTERNAL_FACE_LENGTH_M": p["INTERNAL_FACE_LENGTH_M"],
                                               "EXTERNAL_FACE_LENGTH_M": p["EXTERNAL_FACE_LENGTH_M"],
                                               "HEIGHT_M": p["HEIGHT_M"],
                                               "HEIGHT_SOURCE": p["HEIGHT_SOURCE"]},
                             MEASUREMENT_BASIS="wall-face lengths × the owner's wall height, less openings",
                             MEASURED_QUANTITY=qty, MEASURED_UNIT="m2",
                             QUANTITY_SOURCE="measured wall faces and measured openings",
                             RULE_ID="US-18" if trade == "INTERNAL_PAINT" else None,
                             RULE_LEVEL="URBAN_STANDARD" if trade == "INTERNAL_PAINT" else None,
                             NOTES="a fully tiled face takes no paint" if trade == "INTERNAL_PAINT" else None))
    rp = m["assembly"]["rp"]
    for code, trade, item, qty, calc in (
            ("AR-IN-01", "WATERPROOFING", "Roof waterproofing", rp["WATERPROOFING_AREA_M2"],
             "the roof area enclosed by the parapet"),
            ("AR-RF-01", "PARAPET_BLOCKWORK", "Parapet blockwork", rp["PARAPET_BLOCKWORK_M2"],
             f"{rp['PARAPET_RUN_M']} × {rp['PARAPET_HEIGHT_M']}"),
            ("AR-RF-02", "PARAPET_PLASTER", "Parapet plaster, both faces", rp["PARAPET_PLASTER_M2"],
             f"{rp['PARAPET_RUN_M']} × {rp['PARAPET_HEIGHT_M']} × 2"),
            ("AR-RF-03", "PARAPET_PAINT", "Parapet paint, both faces", rp["PARAPET_PAINT_M2"],
             f"{rp['PARAPET_RUN_M']} × {rp['PARAPET_HEIGHT_M']} × 2")):
        rows.append(_rec(FLOOR="ROOF", FLOOR_AR=FLOORS_AR["ROOF"], ZONE="ROOF",
                         TRADE=trade, ITEM_CODE=code, ITEM=item, CALCULATION=calc,
                         DIMENSION_INPUTS={"PARAPET_RUN_M": rp["PARAPET_RUN_M"],
                                           "PARAPET_HEIGHT_M": rp["PARAPET_HEIGHT_M"],
                                           "HEIGHT_SOURCE": rp["PARAPET_HEIGHT_SOURCE"]},
                         MEASUREMENT_BASIS=rp["PARAPET_RUN_BASIS"],
                         MEASURED_QUANTITY=qty, MEASURED_UNIT="m2",
                         QUANTITY_SOURCE="the roof edge the drawing draws",
                         RULE_ID="AR-06", RULE_LEVEL="OWNER_CONFIRMED_PROJECT_INPUT"))
    for d in m["assembly"]["doors"]:
        rows.append(_rec(FLOOR=d["FLOOR"], FLOOR_AR=FLOORS_AR[d["FLOOR"]], ZONE="OPENING",
                         TRADE="DOORS", ITEM_CODE="AR-DR-01", ITEM="Door opening", SUBITEM=d["DOOR_ID"],
                         DIMENSION_INPUTS={"WIDTH_M": d["WIDTH_M"], "WIDTH_SOURCE": d["WIDTH_SOURCE"],
                                           "HEIGHT_M": d["HEIGHT_M"], "HEIGHT_SOURCE": d["HEIGHT_SOURCE"]},
                         CALCULATION=f"{d['WIDTH_M']} × {d['HEIGHT_M']} = {d['AREA_M2']}",
                         MEASUREMENT_BASIS="clear width jamb to jamb",
                         MEASURED_QUANTITY=d["AREA_M2"], MEASURED_UNIT="m2",
                         QUANTITY_SOURCE="measured from the project geometry",
                         RULE_ID="AR-02", RULE_LEVEL="OWNER_CONFIRMED_PROJECT_INPUT",
                         STATUS="PRICING_BASIS_REQUIRED", NOTES=d["NOTES"]))
    for w in m["assembly"]["windows"]:
        rows.append(_rec(FLOOR=w["FLOOR"], FLOOR_AR=FLOORS_AR[w["FLOOR"]], ZONE="EXTERNAL_WALL",
                         ROOM_REF=w["ROOM_REF"], ROOM_NAME=w["ROOM"],
                         TRADE="ALUMINIUM", ITEM_CODE="AR-AL-01", ITEM="Window", SUBITEM=w["WINDOW_ID"],
                         DIMENSION_INPUTS={"WIDTH_M": w["WIDTH_M"], "WIDTH_SOURCE": w["WIDTH_SOURCE"],
                                           "HEIGHT_M": w["HEIGHT_M"], "HEIGHT_SOURCE": w["HEIGHT_SOURCE"],
                                           "GUIDE_CATEGORY": w["GUIDE_CATEGORY"]},
                         CALCULATION=f"{w['WIDTH_M']} × {w['HEIGHT_M']} = {w['AREA_M2']}",
                         MEASUREMENT_BASIS="width measured from the plot, height from the Urban guide",
                         MEASURED_QUANTITY=w["AREA_M2"], MEASURED_UNIT="m2",
                         QUANTITY_SOURCE=f"width {w['WIDTH_SOURCE']}, height {w['HEIGHT_SOURCE']}",
                         RULE_ID=WS.RULE_ID, RULE_LEVEL="URBAN_STANDARD",
                         STATUS="DRAWING_SCOPE_ONLY",
                         NOTES="US-21: an aluminium quantity from architectural drawings is not a supply quantity"))
    return rows


# ------------------------------------------------------------------ sources, rules and review
def sources_sheet(ws, m, checks):
    a = m["assembly"]
    ws.append(["القسم", "البند", "التفصيل", "الحالة"])

    def sec(name, item, detail, status):
        ws.append([name, item, detail, status])

    for f in SOURCE_FILES:
        sec("المصادر", f, "ملف مشروع مقدَّم من المالك — القياس كله منه", "USED")
    sec("المصادر", "مراجعة المخطط", DRAWING_REVISION,
        "IDENTIFIED_BY_DIMENSION_CONTAINMENT_SCORE_1.000")
    sec("المصادر", "الملف التاريخي (إكسل)", "لم تُؤخذ منه أي كمية أو سعر أو معادلة في هذا الملف",
        "NOT_A_SOURCE_OF_QUANTITY")
    sec("المصادر", "دليل مقاسات الشبابيك", WS.VERSION + " — ارتفاعات فقط، والعرض من المخطط دائماً",
        "APPLIED_FOR_HEIGHT_ONLY")
    ws.append([])
    for k, v in OI.PROJECT_INPUTS.items():
        sec("مدخلات المالك", f"{v['FROM']} — {k}", f"{v['VALUE_M']} م — {v['KIND']}",
            "TRAVELS" if v.get("TRAVELS") else "PROJECT_VALUE_ONLY")
    sec("مدخلات المالك", "AR-07 — النطاق",
        "الإنشائي والصحي والكهربائي والتكييف خارج النطاق بقرار المالك", "OUT_OF_SCOPE_FOR_CURRENT_VALIDATION")
    sec("مدخلات المالك", "AR-08 — المساحات الخارجية", "تُقاس بالمساحة؛ لا تُخترع مادة تشطيب",
        "FINISH_CLASSIFICATION_PENDING")
    ws.append([])
    sec("القواعد", "US-18", OI.US_WET_ROOM_FINISH["STATEMENT"], "APPLIED")
    sec("القواعد", WS.RULE_ID, "دليل مقاسات الشبابيك — مرتبة أولوية 4، بعد أي مقاس مرسوم", "APPLIED")
    for d in VA.RULE_DECISIONS:
        if d["DECISION"] == "PROMOTE":
            sec("القواعد", d["RULE_ID"], d["STATEMENT"], "PROMOTED_BY_OWNER")
    sec("القواعد", "DS-01 — فصل الكمية عن السعر",
        "الكمية والهالك وكمية الشراء وسعر الوحدة والإجمالي خمسة أعمدة منفصلة، لا تجتمع في خانة واحدة",
        "ENFORCED_IN_THIS_WORKBOOK")
    ws.append([])
    sec("الحالة المجمدة", "Commit", FROZEN_COMMIT, "UNCHANGED")
    sec("الحالة المجمدة", "Digest", FROZEN_DIGEST, "UNCHANGED")
    sec("الحالة المجمدة", "Artifact", "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF",
        "هذا الملف يعيد عرض القياس المجمد ولا يعيد حسابه")
    sec("الحالة المجمدة", "فروق التقريب",
        "ورقة حصر المساحات تحمل الأبعاد بدقتها الكاملة فتطابق المجمد تماماً؛ أما أوراق البنود فتعيد الجمع من "
        "الأبعاد كما تُنشر (بالمليمتر)، فقد يظهر فرق تقريب أقصاه 0.003 م² في بند مساحته 963 م² — تقريب عرض "
        "لا إعادة قياس", "ROUNDING_ONLY")
    ws.append([])
    for c in checks["CHECKS"]:
        sec("فحوص الجودة", c["CHECK"], json.dumps(c["DETAIL"], ensure_ascii=False, default=str)[:300],
            "PASS" if c["PASS"] else "FAIL")
    ws.append([])
    sec("ما لم يُقَس", "عزل أرضيات الغرف الرطبة", "لا تفصيل على المخططات الثلاثة", "SOURCE_REQUIRED")
    sec("ما لم يُقَس", "بروفايل / درابزين", PROFILE_STEEL["WHY"], "SOURCE_REQUIRED")
    sec("ما لم يُقَس", "الأسقف المعلقة والديكورية", "تحتاج مخطط أسقف", "SOURCE_REQUIRED")
    sec("ما لم يُقَس", "الإنشائي والصحي والكهربائي والتكييف", "خارج النطاق بقرار المالك AR-07",
        "OUT_OF_SCOPE_FOR_CURRENT_VALIDATION")
    sec("ما لم يُقَس", "نوع تشطيب السطح والمساحات الخارجية", "المساحة نهائية والمادة غير منصوصة",
        "FINISH_CLASSIFICATION_PENDING")
    _style(ws, (18, 34, 86, 34))


def summary_sheet(ws, m, ref, boq_cells, checks):
    a = m["assembly"]
    ws.append(["ملخص حصر الكميات — فيلا أحمد عبدالله علي الراشد", None, None, None])
    ws.append(["صباح الأحمد — قطعة D4، قسيمة 247، مساحة القسيمة 600.00 م²", None, None, None])
    ws.append([f"المخطط: {DRAWING_REVISION}", None, None, None])
    ws.append([f"الحالة المجمدة: {FROZEN_COMMIT} / {FROZEN_DIGEST} — لم تتغير", None, None, None])
    ws.append(["الأسعار والهالك: فارغة عمداً — هذا حصر كميات لا تسعيرة", None, None, None])
    ws.append([])
    ws.append(["الدور", "عدد الفراغات", "المساحة (م²)", "المنسوب (م)"])
    _fill_row(ws, ws.max_row, HEAD_FILL, last="D")
    from openpyxl.styles import Font
    for c in ws[ws.max_row]:
        c.font = Font(bold=True, color="FFFFFF")
    for f in m["floors"]:
        ws.append([f["FLOOR_AR"], len(f["ROOMS"]), None, f["LEVEL_M"]])
        ws.cell(ws.max_row, 3).value = "=" + ref["FLOOR"][f["FLOOR"]]
    ws.append(["إجمالي المشروع", sum(len(f["ROOMS"]) for f in m["floors"]), None, None])
    ws.cell(ws.max_row, 3).value = "=" + ref["PROJECT"]
    _fill_row(ws, ws.max_row, TOTAL_FILL, last="D")
    ws.append([])
    ws.append(["البند", "الوحدة", "الكمية", "الحالة"])
    _fill_row(ws, ws.max_row, HEAD_FILL, last="D")
    for c in ws[ws.max_row]:
        c.font = Font(bold=True, color="FFFFFF")
    for code, trade, desc, unit, cell, value, source, rule, status, notes in boq_items(m, ref):
        ws.append([f"{code} — {desc}", unit, None, status])
        ws.cell(ws.max_row, 3).value = ("=" + boq_cells[code]) if code in boq_cells else value
    ws.append([])
    ws.append(["فحوص الجودة", f"{checks['PASSED']} / {checks['OF']}",
               "PASS" if checks["ALL_PASS"] else "FAIL", "التفصيل في ورقة المصادر والمراجعة"])
    _fill_row(ws, ws.max_row, TOTAL_FILL, last="D")
    ws.append(["حالة الاعتماد", "DRAFT", "كل السجلات",
               "المحرك لا يعتمد حصره بنفسه — الاعتماد قرار المالك"])
    ws.append(["بيانات تاريخية مستخدمة", "لا شيء", "0",
               "لم تدخل أي كمية أو سعر من الملف التاريخي إلى هذا الحصر"])
    ws.sheet_view.rightToLeft = True
    for col, w in zip("ABCD", (62, 16, 18, 46)):
        ws.column_dimensions[col].width = w
    ws["A1"].font = Font(bold=True, size=14)


def workbook(m, path, checks_placeholder=None):
    from openpyxl import Workbook
    wb = Workbook()
    wb.remove(wb.active)
    ws = {name: wb.create_sheet(name) for name in SHEETS}
    ref = area_sheet(ws["حصر المساحات"], m)
    ref["FLOORS"] = _room_finish_sheet(
        ws["الأرضيات"], m, ref, "بورسلان / سيراميك أرضيات", "US-18",
        "المساحة هي مساحة الغرفة المجمدة نفسها", ("INTERNAL_ROOM", "WET_ROOM", "KITCHEN"),
        ("STAIR_OR_LANDING", "UNNAMED_ON_DRAWING"))
    ref["CEILING"] = _room_finish_sheet(
        ws["الأسقف"], m, ref, "سقف عادي — مساح وصبغ", None,
        "المساحة المسقوفة المحصورة؛ لا مخطط أسقف معلقة", FLOOR_FINISH_ROLES)
    ref.update(wall_sheet(ws["كسوة الجدران"], m))
    ref["SKIRTING"] = skirting_sheet(ws["النعلة والبروفايل"], m)
    ref["INSULATION"] = insulation_sheet(ws["العازل"], m)
    op = openings_sheet(ws["الأبواب والشبابيك"], m)
    ref["DOORS"], ref["WINDOWS"] = op["DOORS"], op["WINDOWS"]
    blk = blockwork_sheet(ws["المباني"], m)
    ref["BLOCK150"], ref["BLOCK200"] = blk[150], blk[200]
    ref.update(plaster_sheet(ws["المساح والصبغ"], m))
    ref.update(roof_sheet(ws["السطح والخارجي"], m))
    boq_cells = boq_sheet(ws["BOQ حسب البند"], m, ref)

    filled = {"WASTE_WRITTEN": 0, "RATES_WRITTEN": 0, "AMOUNTS_WRITTEN": 0}
    b = ws["BOQ حسب البند"]
    for r in range(2, b.max_row + 1):
        for col, key in ((6, "WASTE_WRITTEN"), (8, "RATES_WRITTEN"), (9, "AMOUNTS_WRITTEN")):
            v = b.cell(r, col).value
            if v is not None and not (isinstance(v, str) and v.startswith("=")):
                filled[key] += 1
    rows = export_rows(m)
    info = dict(filled, REF=ref, EXPORT_ROWS=rows, FROZEN_DIGEST_NOW=frozen_digest())
    checks = qa(m, info)
    sources_sheet(ws["المصادر والمراجعة"], m, checks)
    summary_sheet(ws["ملخص الحصر"], m, ref, boq_cells, checks)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return {"PATH": str(path), "SHEETS": wb.sheetnames, "QA": checks, "EXPORT_ROWS": rows,
            "PRICING_COLUMNS_LEFT_BLANK": ["الهالك %", "كمية الشراء", "سعر الوحدة", "الإجمالي"],
            "RATES_SUPPLIED": 0, "WASTE_APPLIED": False, "BOQ_LINES": len(boq_cells)}


def frozen_digest():
    p = OUT / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json"
    return json.loads(p.read_text("utf-8"))["DIGEST"] if p.exists() else None


def finish():
    m = build()
    OUT.mkdir(parents=True, exist_ok=True)
    xl = OUT / "ALRASHED_DETAILED_QUANTITY_TAKEOFF.xlsx"
    wb = workbook(m, xl)
    rooms = [r for f in m["floors"] for r in f["ROOMS"]]
    export = {
        "ARTIFACT": "ALRASHED_DETAILED_QUANTITY_EXPORT",
        "PROJECT_ID": OI.PROJECT_ID, "PROJECT_NAME": PROJECT_NAME,
        "DRAWING_REVISION": DRAWING_REVISION, "SOURCE_FILES": SOURCE_FILES,
        "BASED_ON": {"ARTIFACT": "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF",
                     "COMMIT": FROZEN_COMMIT, "DIGEST": FROZEN_DIGEST, "RESTATED": False},
        "SCHEMA_RULE": "DS-01 - MEASURED_QUANTITY, MEASURED_UNIT, WASTE_PERCENT, PROCUREMENT_QUANTITY, "
                       "UNIT_RATE and AMOUNT are separate fields; none is ever combined",
        "APPROVAL_STATUS": "DRAFT",
        "RECORD_COUNT": len(wb["EXPORT_ROWS"]),
        "RECORDS": wb["EXPORT_ROWS"],
        "QA": wb["QA"],
    }
    export["GENERATED_AT"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (OUT / "ALRASHED_DETAILED_QUANTITY_EXPORT.json").write_text(
        json.dumps(export, indent=1, ensure_ascii=False, default=str), "utf-8")

    rec = {
        "ARTIFACT": "ALRASHED_DETAILED_QUANTITY_TAKEOFF",
        "PROJECT_ID": OI.PROJECT_ID, "PROJECT_NAME": PROJECT_NAME,
        "WORKBOOK": {k: v for k, v in wb.items() if k != "EXPORT_ROWS"},
        "FLOORS": [{"FLOOR": f["FLOOR"], "ROOMS": len(f["ROOMS"]),
                    "PARTS": sum(len(r["PARTS"]) for r in f["ROOMS"]),
                    "AREA_M2": f["FLOOR_TOTAL_M2"], "CLOSURE_RESIDUAL_M2": f["CLOSURE"]["RESIDUAL_M2"]}
                   for f in m["floors"]],
        "PROJECT_TOTAL_M2": m["project_total_m2"],
        "ROOM_COUNT": len(rooms), "COMPONENT_COUNT": sum(len(r["PARTS"]) for r in rooms),
        "RECORD_COUNT": len(wb["EXPORT_ROWS"]),
        "SKIRTING_LM": round(sum(x["SKIRTING_LENGTH_M"] for x in m["skirting"]), 3),
        "TRADE_TOTALS": m["assembly"]["totals"],
        "FROZEN_UNCHANGED": {"COMMIT": FROZEN_COMMIT, "DIGEST": frozen_digest(),
                             "MATCHES": frozen_digest() == FROZEN_DIGEST},
        "HISTORICAL_QUANTITY_USED": False,
        "GIT_HEAD": _git("rev-parse", "--short", "HEAD"),
    }
    rec["DIGEST"] = hashlib.sha256(json.dumps(
        {"F": rec["FLOORS"], "T": rec["TRADE_TOTALS"], "R": rec["RECORD_COUNT"]},
        sort_keys=True, default=str).encode()).hexdigest()[:16]
    (OUT / "ALRASHED_DETAILED_QUANTITY_TAKEOFF.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False, default=str), "utf-8")
    return rec, m


if __name__ == "__main__":
    r, m = finish()
    q = r["WORKBOOK"]["QA"]
    print(f"{r['ARTIFACT']}  digest {r['DIGEST']}")
    print(f"  rooms {r['ROOM_COUNT']}  components {r['COMPONENT_COUNT']}  records {r['RECORD_COUNT']}")
    print(f"  QA {q['PASSED']}/{q['OF']}  {'ALL PASS' if q['ALL_PASS'] else 'FAILURES'}")
    for c in q["CHECKS"]:
        if not c["PASS"]:
            print("   FAIL", c["CHECK"], json.dumps(c["DETAIL"], ensure_ascii=False, default=str)[:200])
    for f in r["FLOORS"]:
        print(f"   {f['FLOOR']:9s} rooms {f['ROOMS']:3d}  parts {f['PARTS']:3d}  area {f['AREA_M2']}")
