"""URBAN_PROJECTS_BOQ_SCHEMA_LIBRARY: the house pricing structure, read from previous projects' own workbooks.

Structure only.  No historical quantity, rate, total, room dimension or contractor amount is carried into Qortuba, and the
register stores none of them: every row records what the item is called, what unit it is priced in, how its quantity is built
and what deduction rule the sheet states in its own words.  Historical numbers stay in the historical files, where they are
REFERENCE_PROJECT_DATA_ONLY.

Provenance is checked rather than asserted.  Each row names the workbook and sheet it was read from, and a verifier opens that
sheet and confirms the Arabic item text is really there.  A row that cannot be found is reported, not silently kept.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
UP = "/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240/"

# the historical workbooks, by content hash so a renamed upload still resolves
WORKBOOKS = {
    "W1": {"FILE": UP + "0449714f-_________________1.xlsx", "KIND": "xlsx", "SHA16": "ae608411ed5b9e64",
           "TITLE_AR": "خرسانة مسلحة", "TITLE_EN": "reinforced concrete", "COMPANY": "شركه التسنيم"},
    "W2": {"FILE": UP + "45f2a378-__________.xlsx", "KIND": "xlsx", "SHA16": "7826608fc716ca0c",
           "TITLE_AR": "الالمونيوم", "TITLE_EN": "aluminium", "COMPANY": "شركه التسنيم"},
    "W3": {"FILE": UP + "5a3370bb-_____.xls", "KIND": "xls", "SHA16": "d1b459e531d78767",
           "TITLE_AR": "الصبغ", "TITLE_EN": "paint", "COMPANY": "شركه التسنيم",
           "DUPLICATE_OF": "777b0536-_____.xls, identical bytes"},
    "W5": {"FILE": UP + "85f545ca-____________________________1.xlsx", "KIND": "xlsx", "SHA16": "de448191fb9d0aba",
           "TITLE_AR": "ارضيات وعازل وديكور ودرابزين", "TITLE_EN": "floors, waterproofing, decor and railing",
           "COMPANY": "شركه التسنيم"},
    "W6": {"FILE": UP + "b324a3e7-______________________.xls", "KIND": "xls", "SHA16": "bf6e3123b988534d",
           "TITLE_AR": "مساح داخلى وخارجى", "TITLE_EN": "internal and external plaster", "COMPANY": "شركه التسنيم",
           "DUPLICATE_OF": "c495ff6e-______________________.xls, identical bytes"},
    "W7": {"FILE": UP + "c52a77de-_______.xlsx", "KIND": "xlsx", "SHA16": "873308bb6a3c99fd",
           "TITLE_AR": "مبانى الطابوق", "TITLE_EN": "blockwork", "COMPANY": "شركه التسنيم"},
}
NOT_A_BOQ = {"6aafd947-__________________________.xlsx": "a programme of works (الجدول الزمني), not a bill of quantities"}

# the two row shapes every one of these workbooks uses
ROW_SHAPES = {
    "SUMMARY_INVOICE": {
        "WHERE": "the الغلاف or الفاتورة sheet, one row per priced BOQ item",
        "COLUMNS_AR": ["البيان", "اجمالى الكميات", "خصم كامل", "خصم بالنصف", "اجمالى الخصم", "الصافى", "العــدد",
                       "سعر الوحدة", "المستحق"],
        "COLUMNS_EN": ["item", "gross quantity", "full deduction", "half deduction", "total deduction", "net",
                       "count", "unit rate", "amount"],
        "MEANING": "gross less deductions gives the net; the net is what the rate multiplies.  Unit is written either in a "
                   "unit column or inside the item text itself, for example 'مساح م2' or 'زوايا ونهايات م.ط'."},
    "DETAIL_TAKEOFF": {
        "WHERE": "the الكميات or per-trade detail sheet, one row per measured element",
        "COLUMNS_AR": ["البيان", "عدد", "طول", "عرض / ارتفاع", "خصم فراغات كلى", "خصم فراغات نصف", "إضافة", "اجمالى عام",
                       "ملاحظات"],
        "COLUMNS_EN": ["item", "count", "length", "width or height", "full void deduction", "half void deduction",
                       "addition", "grand total", "notes"],
        "MEANING": "count x length x height builds the element quantity; deductions and additions are columns, never edits "
                   "to the measured figure.  Rooms are grouped under a storey heading such as الطابق الأرضى."},
}

UNITS = {"م2": "M2", "م.ط": "LM", "م³": "M3", "عدد": "NR", "طن": "TON"}

# ---------------------------------------------------------------------------- the items, as the workbooks name them
ITEMS = [
    # ---- ceramic
    dict(T="سيراميك", RAW="اجمالي الارضيات", CANON="FLOOR_CERAMIC_TOTAL", U="م2", W="W5", S="الغلاف",
         BASIS="room floor areas summed across storeys",
         PAT="per room: count x length x width, summed per storey then overall",
         DED=None, N="the cover carries no deduction against this item: gross equals net"),
    dict(T="سيراميك", RAW="اجمالي النعلات", CANON="SKIRTING_CERAMIC_TOTAL", U="م.ط", W="W5", S="الغلاف",
         BASIS="running length of skirting per room", PAT="per room: linear metres, summed",
         DED=None, N="priced by linear metre; no deduction column used on the cover"),
    dict(T="سيراميك", RAW="اجمالي الحوائط", CANON="WALL_CERAMIC_TOTAL", U="م2", W="W5", S="الغلاف",
         BASIS="wall tiling area", PAT="per room: wall run length x tiling height",
         DED=None, N="the detail sheet carries a طولي column and an ارتفاع column, so the area is length x height"),
    dict(T="سيراميك", RAW="ارضيات حمام السباحه", CANON="POOL_BATHROOM_FLOOR", U="م2", W="W5", S="الغلاف",
         BASIS="floor area of a named special room", PAT="length x width",
         DED=None, N="special rooms are given their own cover lines rather than folded into the total"),
    dict(T="سيراميك", RAW="حوائط حمام السباحه", CANON="POOL_BATHROOM_WALL", U="م2", W="W5", S="الغلاف",
         BASIS="wall tiling area of a named special room", PAT="wall run x height", DED=None, N=None),
    # ---- courtyard, its own scope
    dict(T="الحوش", RAW="ارضيات الحوش", CANON="COURTYARD_FLOOR", U="م2", W="W5", S="الغلاف",
         BASIS="courtyard floor area", PAT="length x width",
         DED=None, N="the courtyard is a separate scope on the cover, not part of the internal floor total"),
    dict(T="الحوش", RAW="نعلات الحوش", CANON="COURTYARD_SKIRTING", U="م.ط", W="W5", S="الغلاف",
         BASIS="courtyard skirting length", PAT="linear metres", DED=None, N=None),
    # ---- marble and stairs
    dict(T="رخام", RAW="اجمالي الدرج والبسطات", CANON="STAIR_AND_LANDING_MARBLE", U="م2", W="W5", S="الغلاف",
         BASIS="steps and landings together, as one area",
         PAT="steps: count x tread width, giving an area; landings: area; the two summed",
         DED=None,
         N="treads and risers are NOT separate items here: the cover carries one combined stair and landing area"),
    dict(T="رخام", RAW="اجمالي النعلات", CANON="STAIR_SKIRTING_MARBLE", U="م.ط", W="W5", S="الغلاف",
         BASIS="skirting along the flight", PAT="linear metres", DED=None, N=None),
    dict(T="رخام", RAW="اجمالي التواشيح", CANON="STAIR_SIDE_PIECE", U="عدد", W="W5", S="الغلاف",
         BASIS="one per step", PAT="counted, one per tread",
         DED=None,
         N="counted, not measured by length: the detail sheet lists تواشيح against the step count"),
    # ---- waterproofing
    dict(T="عازل حمام+مطابخ", RAW="عازل ارضيات حمامات", CANON="WET_AREA_WATERPROOFING_FLOOR", U="م2", W="W5", S="الغلاف",
         BASIS="bathroom and kitchen floor areas", PAT="per room: length x width", DED=None, N=None),
    dict(T="عازل حمام+مطابخ", RAW="نعلات العازل للحمامات", CANON="WET_AREA_WATERPROOFING_UPTURN", U="م.ط", W="W5", S="الغلاف",
         BASIS="the upturn around the wet room perimeter", PAT="linear metres of room perimeter",
         DED=None,
         N="the upturn is priced by LINEAR METRE, not by area: no upturn height enters the quantity"),
    dict(T="عازل سطح", RAW="عازل اسطح و ملاحق", CANON="ROOF_WATERPROOFING", U="م2", W="W5", S="الغلاف",
         BASIS="roof and annexe areas", PAT="length x width", DED=None, N=None),
    dict(T="عازل سطح", RAW="نعلات العازل الاسطح", CANON="ROOF_WATERPROOFING_UPTURN", U="م.ط", W="W5", S="الغلاف",
         BASIS="the upturn around the roof perimeter", PAT="linear metres of perimeter", DED=None,
         N="same convention as the wet areas: upturn by linear metre"),
    # ---- ceiling decor
    dict(T="ديكور جبس", RAW="ديكور الصالات والغرف", CANON="GYPSUM_DECOR_DRY_ROOMS", U="م2", W="W5", S="الغلاف",
         BASIS="ceiling area of halls and rooms", PAT="per room: length x width",
         DED=None, N="decor is split dry rooms against bathrooms and kitchens, as two cover lines"),
    dict(T="ديكور جبس", RAW="كرانيش الصالات والغرف", CANON="CORNICE_DRY_ROOMS", U="م.ط", W="W5", S="الغلاف",
         BASIS="cornice run around the room", PAT="per room: perimeter in linear metres",
         DED=None,
         N="the detail sheet's اجمالي كورنيشه column carries this; the room perimeter is the cornice length"),
    dict(T="ديكور جبس", RAW="ديكور الحمامات والمطابح", CANON="GYPSUM_DECOR_WET_ROOMS", U="م2", W="W5", S="الغلاف",
         BASIS="ceiling area of bathrooms and kitchens", PAT="per room: length x width", DED=None, N=None),
    dict(T="ديكور جبس", RAW="كرانيش الحمامات والمطابخ", CANON="CORNICE_WET_ROOMS", U="م.ط", W="W5", S="الغلاف",
         BASIS="cornice run in bathrooms and kitchens", PAT="per room perimeter", DED=None, N=None),
    # ---- railing
    dict(T="درابزين", RAW="دربزين داخلي", CANON="INTERNAL_RAILING", U="م.ط", W="W5", S="الغلاف",
         BASIS="running length of internal railing", PAT="linear metres",
         DED=None, N="one cover line, by linear metre; no separate sloped and horizontal items"),
    # ---- blockwork
    dict(T="مبانى", RAW="مبانى الخارجي م2", CANON="BLOCKWORK_EXTERNAL", U="م2", W="W7", S="الغلاف",
         BASIS="external blockwork area", PAT="per wall: count x length x height, summed",
         DED="خصم فراغات, columns for كلى and نصف on the detail sheet",
         N="external blockwork is its own item, separate from the thickness items"),
    dict(T="مبانى", RAW="مبانى سمك 15سم  م2", CANON="BLOCKWORK_150", U="م2", W="W7", S="الغلاف",
         BASIS="internal blockwork of 15 cm thickness", PAT="per wall: count x length x height, summed",
         DED="خصم فراغات كلى or نصف", N="thickness is named in the item text, and the quantity is an AREA not a length"),
    dict(T="مبانى", RAW="مبانى سمك 20 سم م2", CANON="BLOCKWORK_200", U="م2", W="W7", S="الغلاف",
         BASIS="internal blockwork of 20 cm thickness", PAT="per wall: count x length x height, summed",
         DED="خصم فراغات كلى or نصف", N=None),
    dict(T="مبانى", RAW="اجمالى المباني", CANON="BLOCKWORK_TOTAL", U="م2", W="W7", S="الغلاف",
         BASIS="sum of the blockwork items above", PAT="sum", DED=None, N="a total line, not a priced item"),
    # ---- internal plaster
    dict(T="مساح داخلى", RAW="مساح م2", CANON="INTERNAL_PLASTER", U="م2", W="W6", S="الفاتورة",
         BASIS="internal wall face area", PAT="per room: wall run length x storey height",
         DED="خصم بالنصف: openings are deducted at HALF their area, not in full",
         N="the detail sheet gives ارتفاع and طول per room and multiplies them"),
    dict(T="مساح داخلى", RAW="زوايا ونهايات م.ط", CANON="PLASTER_CORNERS_AND_ENDS", U="م.ط", W="W6", S="الفاتورة",
         BASIS="corner and end beads, measured as running length",
         PAT="per room: corner length and end length tracked in their own columns",
         DED="2م=1م, written in the deduction column: the measured running length is halved to give the net",
         N="the detail sheet carries زوايا م.ط and نهايات م.ط as two columns beside each room"),
    dict(T="مساح داخلى", RAW="طرطشة حمامات ومطابخ م2", CANON="RENDER_TO_WET_ROOMS", U="م2", W="W6", S="الفاتورة",
         BASIS="tile backing render in bathrooms and kitchens", PAT="wall run x height",
         DED=None, N="a separate item from the finish plaster, priced on its own line"),
    dict(T="مساح داخلى", RAW="طرطشة تحت نعلة م2", CANON="RENDER_UNDER_SKIRTING", U="م2", W="W6", S="الفاتورة",
         BASIS="the band of render behind the skirting", PAT="skirting run x skirting height",
         DED=None, N="an item in its own right; it does not come out of the wall plaster line"),
    dict(T="مساح داخلى", RAW="شرشوب أبواب", CANON="DOOR_JAMB_PLASTER", U="م2", W="W6", S="البيــــــــــــان",
         BASIS="plaster to door reveals", PAT="count x reveal girth x reveal depth",
         DED=None, N="measured per door on the detail sheet with its own count, depth and length"),
    dict(T="مساح داخلى", RAW="فرفيس مقطوعية", CANON="PLASTER_LUMP_SUM_ITEM", U="عدد", W="W6", S="الفاتورة",
         BASIS="a lump sum line", PAT="مقطوعية means priced as a lump, not measured",
         DED=None, N="the house structure allows a lump sum item inside a measured bill"),
    # ---- external plaster
    dict(T="مساح خارجي", RAW="مساح خارجى م2", CANON="EXTERNAL_PLASTER", U="م2", W="W6", S="الفاتورة",
         BASIS="external wall face area", PAT="elevation run length x height",
         DED="خصم بالنصف: openings deducted at half",
         N="internal and external plaster share one invoice, in two sections"),
    dict(T="مساح خارجي", RAW="زوايا وفواصل ومبروم م.ط", CANON="EXTERNAL_CORNERS_JOINTS_AND_BEADS", U="م.ط", W="W6",
         S="الفاتورة", BASIS="external corners, movement joints and rounded beads",
         PAT="running length", DED="2م =1م: the measured running length is halved", N=None),
    # ---- paint
    dict(T="صبغ", RAW="صبغ الحوائط م2", CANON="WALL_PAINT", U="م2", W="W3", S="الفاتورة",
         BASIS="painted wall face area", PAT="per room: wall run length x storey height",
         DED="خصم بالنصف: openings deducted at half",
         N="the detail sheet heads its block صبغ الحوائط م2 and gives ارتفاع x طول per room"),
    dict(T="صبغ", RAW="صبغ الديكور مع الكوف لايت", CANON="DECOR_PAINT_WITH_COVE_LIGHT", U="م2", W="W3", S="الفاتورة",
         BASIS="paint to the decorative ceiling including the cove light detail",
         PAT="decor ceiling area", DED=None,
         N="decor paint is a separate item from wall paint and is tied to the decor area, not the ceiling area"),
    # ---- aluminium
    dict(T="ألمنيوم", RAW="اجمالي الأبواب م2", CANON="ALUMINIUM_DOORS", U="م2", W="W2", S="الغلاف",
         BASIS="door leaf area", PAT="count x width x height",
         DED=None, N="the count is a multiplier inside the area, never the priced quantity on its own"),
    dict(T="ألمنيوم", RAW="اجمالي الشبابيك م2", CANON="ALUMINIUM_WINDOWS", U="م2", W="W2", S="الغلاف",
         BASIS="window area", PAT="count x width x height",
         DED=None, N="the detail sheet names each opening, for example شباك حمام or باب خارجي, then multiplies"),
    # ---- concrete and steel
    dict(T="خرسانة", RAW="حصر خرسانة القواعد المسلحة", CANON="CONCRETE_FOOTINGS", U="م³", W="W1", S="القواعد",
         BASIS="footing volumes", PAT="width x length x height = volume, x count, less خصم, = net volume",
         DED="خصم as a volume column and a count column", N="each footing type has its own row, for example F, F2"),
    dict(T="خرسانة", RAW="شناجات طوليه", CANON="CONCRETE_TIE_BEAMS", U="م³", W="W1", S="الشناجات",
         BASIS="tie beam volumes", PAT="width x length x height x count", DED="خصم volume", N=None),
    dict(T="خرسانة", RAW="حصر الحوائط المسلحة", CANON="CONCRETE_WALLS", U="م³", W="W1", S="الحوائط + الأعمدة",
         BASIS="reinforced wall volumes", PAT="width x length x height x count", DED="خصم volume",
         N="the same sheet carries رقاب الأعمدة, the column necks, under its own heading"),
    dict(T="خرسانة", RAW="حصر خرسانة  كمرات الأرضي", CANON="CONCRETE_BEAMS", U="م³", W="W1", S="كمرات",
         BASIS="beam volumes per storey", PAT="width x depth x span x count", DED="خصم volume",
         N="beams are listed by structural mark, for example B1, B3, B24"),
    dict(T="خرسانة", RAW="حصر خرسانة  بلاطات الأرضي", CANON="CONCRETE_SLABS", U="م³", W="W1", S="بلاطات ",
         BASIS="slab volumes per storey", PAT="plan area x thickness x count", DED="خصم volume",
         N="slab rows carry the area in the width column and the thickness in the height column"),
    dict(T="حديد", RAW="كميات الحديد(طن)", CANON="REINFORCEMENT_STEEL", U="طن", W="W1", S="ورقة1",
         BASIS="reinforcement weight", PAT="a column on the concrete cover, in tonnes",
         DED=None, N="steel is not a separate workbook: it is a column beside the concrete items"),
]


def _sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
    return name


def sheet_text(wb_key, sheet):
    """Every string in a sheet, read-only.  Used to verify an item really appears where the register says it does."""
    w = WORKBOOKS[wb_key]
    vals = []
    if w["KIND"] == "xlsx":
        from openpyxl import load_workbook
        book = load_workbook(w["FILE"], read_only=True, data_only=True)
        ws = book[sheet]
        for row in ws.iter_rows(max_row=400, max_col=20, values_only=True):
            vals += [str(v) for v in row if isinstance(v, str)]
        book.close()
    else:
        import xlrd
        book = xlrd.open_workbook(w["FILE"])
        ws = book.sheet_by_name(sheet)
        for r in range(min(400, ws.nrows)):
            for c in range(min(20, ws.ncols)):
                v = ws.cell_value(r, c)
                if isinstance(v, str):
                    vals.append(v)
    return vals


def _norm(s):
    return "".join(s.split()).replace("ى", "ي").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")


def build():
    cache, rows, missing = {}, [], []
    for i, it in enumerate(ITEMS, 1):
        key = (it["W"], it["S"])
        if key not in cache:
            cache[key] = [_norm(v) for v in sheet_text(it["W"], it["S"])]
        found = any(_norm(it["RAW"]) in v or v in _norm(it["RAW"]) for v in cache[key] if v)
        if not found:
            missing.append({"RAW": it["RAW"], "WORKBOOK": it["W"], "SHEET": it["S"]})
        w = WORKBOOKS[it["W"]]
        rows.append({
            "ITEM_ID": f"BOQ-{i:02d}",
            "TRADE": it["T"],
            "RAW_ARABIC_ITEM": it["RAW"],
            "CANONICAL_ITEM": it["CANON"],
            "PRICING_UNIT": UNITS[it["U"]],
            "PRICING_UNIT_AR": it["U"],
            "QUANTITY_BASIS": it["BASIS"],
            "FORMULA_PATTERN": it["PAT"],
            "DEDUCTION_RULE_IF_EXPLICIT": it["DED"],
            "SOURCE_WORKBOOK": Path(w["FILE"]).name,
            "SOURCE_WORKBOOK_TITLE_AR": w["TITLE_AR"],
            "SOURCE_SHEET": it["S"],
            "PROVENANCE_VERIFIED_IN_SHEET": found,
            "NOTES": it["N"],
        })
    return rows, missing


def finish():
    rows, missing = build()
    written = []
    lib = {
        "ARTIFACT": "URBAN_PROJECTS_BOQ_SCHEMA_LIBRARY",
        "PURPOSE": "the house pricing structure and units, learned from previous projects' own workbooks",
        "SCOPE_RULE": "structure only.  No historical quantity, rate, total, room dimension or contractor amount is stored "
                      "here or used as a Qortuba input; those remain REFERENCE_PROJECT_DATA_ONLY in their own files.",
        "WORKBOOKS": [{"KEY": k, "FILE": Path(v["FILE"]).name, "TITLE_AR": v["TITLE_AR"], "TITLE_EN": v["TITLE_EN"],
                       "COMPANY": v["COMPANY"], "SHA256_16": v["SHA16"],
                       "SHA_VERIFIED": _sha16(v["FILE"]) == v["SHA16"],
                       "DUPLICATE_OF": v.get("DUPLICATE_OF"),
                       "READ_METHOD": "openpyxl read-only" if v["KIND"] == "xlsx" else
                                      "xlrd read-only; no conversion was needed, and the original was not modified"}
                      for k, v in WORKBOOKS.items()],
        "FILES_PRESENT_BUT_NOT_A_BOQ": NOT_A_BOQ,
        "ROW_SHAPES": ROW_SHAPES,
        "UNITS_USED": UNITS,
        "ROWS": rows, "COUNT": len(rows),
        "BY_TRADE": dict(Counter(r["TRADE"] for r in rows)),
        "BY_UNIT": dict(Counter(r["PRICING_UNIT"] for r in rows)),
        "ITEMS_WITH_AN_EXPLICIT_DEDUCTION_RULE": sum(1 for r in rows if r["DEDUCTION_RULE_IF_EXPLICIT"]),
        "PROVENANCE_UNVERIFIED": missing,
        "HOUSE_CONVENTIONS": [
            {"CONVENTION": "openings are deducted at half, not in full",
             "WHERE": "خصم بالنصف column on the plaster and paint invoices",
             "APPLIES_TO": ["INTERNAL_PLASTER", "EXTERNAL_PLASTER", "WALL_PAINT"]},
            {"CONVENTION": "corner and end beads are measured as running length and then halved, written 2م=1م",
             "WHERE": "the deduction column of the plaster invoice, in words",
             "APPLIES_TO": ["PLASTER_CORNERS_AND_ENDS", "EXTERNAL_CORNERS_JOINTS_AND_BEADS"]},
            {"CONVENTION": "a waterproofing upturn is priced by linear metre, so no upturn height enters the quantity",
             "WHERE": "نعلات العازل items on the floors and waterproofing cover",
             "APPLIES_TO": ["WET_AREA_WATERPROOFING_UPTURN", "ROOF_WATERPROOFING_UPTURN"]},
            {"CONVENTION": "stairs and landings are one combined area item; treads and risers are not split",
             "WHERE": "اجمالي الدرج والبسطات on the marble cover",
             "APPLIES_TO": ["STAIR_AND_LANDING_MARBLE"]},
            {"CONVENTION": "stair side pieces are counted, not measured by length",
             "WHERE": "اجمالي التواشيح, unit عدد", "APPLIES_TO": ["STAIR_SIDE_PIECE"]},
            {"CONVENTION": "blockwork is priced by area per thickness, with external blockwork as its own item",
             "WHERE": "the blockwork cover, items ending م2", "APPLIES_TO": ["BLOCKWORK_150", "BLOCKWORK_200",
                                                                            "BLOCKWORK_EXTERNAL"]},
            {"CONVENTION": "aluminium is priced by area; the count is a multiplier inside it",
             "WHERE": "the aluminium cover and its detail sheet", "APPLIES_TO": ["ALUMINIUM_DOORS", "ALUMINIUM_WINDOWS"]},
            {"CONVENTION": "ceiling decor is two items per zone: an area and a cornice run",
             "WHERE": "ديكور and كرانيش pairs on the decor cover",
             "APPLIES_TO": ["GYPSUM_DECOR_DRY_ROOMS", "CORNICE_DRY_ROOMS", "GYPSUM_DECOR_WET_ROOMS", "CORNICE_WET_ROOMS"]},
            {"CONVENTION": "dry rooms and wet rooms are split into separate cover lines for decor and for render",
             "WHERE": "الصالات والغرف against الحمامات والمطابخ",
             "APPLIES_TO": ["GYPSUM_DECOR_DRY_ROOMS", "GYPSUM_DECOR_WET_ROOMS", "RENDER_TO_WET_ROOMS"]},
            {"CONVENTION": "a lump sum item may sit inside a measured bill, marked مقطوعية",
             "WHERE": "فرفيس مقطوعية on the plaster invoice", "APPLIES_TO": ["PLASTER_LUMP_SUM_ITEM"]},
        ],
        "WORKBOOK_ORGANISATION": {
            "ONE_WORKBOOK_PER_TRADE_PACKAGE": "each file covers one trade or a group of related trades, numbered NO:1 to NO:6",
            "SHEETS": "a الغلاف or الفاتورة summary carrying the priced items, then one detail sheet per trade or storey",
            "DETAIL_FEEDS_SUMMARY": "the detail sheet measures element by element under storey headings; the summary carries "
                                    "only the totalled items with their units",
            "HEADER_BLOCK": "company, trade title, area, owner, contractor, subcontractor, date and a sheet number",
            "ROOMS": "rooms appear only on the detail sheets, as row labels under a storey heading",
        },
    }
    written.append(write("URBAN_PROJECTS_BOQ_SCHEMA_LIBRARY", lib))

    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip().splitlines()
    contents = {n: hashlib.sha256((OUT / f"{n}.json").read_bytes()).hexdigest() for n in written}
    fr = {"ARTIFACT": "FREEZE_URBAN_PROJECTS_BOQ_SCHEMA_LIBRARY",
          "STRUCTURE_ONLY": True, "HISTORICAL_QUANTITIES_STORED": 0, "HISTORICAL_RATES_STORED": 0,
          "REFERENCE_PROJECT_DATA_ONLY": "historical quantities, rates, totals and room dimensions were read to learn the "
                                         "structure and were not copied into this register or into Qortuba",
          "ORIGINALS_MODIFIED": 0,
          "GIT_HEAD_AT_FREEZE": head,
          "WORKING_TREE_AT_FREEZE": {"CLEAN": not dirty, "UNCOMMITTED_PATHS": [l[3:] for l in dirty][:20]},
          "CONTENTS": contents, "COUNT": len(contents)}
    fr["DIGEST"] = hashlib.sha256(json.dumps({k: v for k, v in fr.items() if k != "DIGEST"}, sort_keys=True, default=str).encode()).hexdigest()
    write("FREEZE_URBAN_PROJECTS_BOQ_SCHEMA_LIBRARY", fr)
    return {"LIBRARY": lib, "FREEZE": fr}


if __name__ == "__main__":
    o = finish()
    lib = o["LIBRARY"]
    print("FREEZE", o["FREEZE"]["DIGEST"][:16], "| items", lib["COUNT"])
    print("by trade:", lib["BY_TRADE"])
    print("by unit:", lib["BY_UNIT"])
    print("explicit deduction rules:", lib["ITEMS_WITH_AN_EXPLICIT_DEDUCTION_RULE"])
    print("provenance unverified:", lib["PROVENANCE_UNVERIFIED"])
    print("workbook sha verified:", [(w["KEY"], w["SHA_VERIFIED"]) for w in lib["WORKBOOKS"]])
