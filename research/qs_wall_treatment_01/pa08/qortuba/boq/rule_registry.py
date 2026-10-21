"""URBAN_BOQ_RULE_REGISTRY: what one previous project did, held apart from what Urban Projects always does.

A rule read off an old bill is a precedent, not a standard.  It was agreed with one contractor, on one project, for one trade,
and it may have been a negotiating position rather than a company practice.  Promoting it silently to a universal rule is the
quiet way a house style becomes a fiction, so every rule here carries a level:

    HISTORICAL_PRECEDENT   observed on a previous project's bill, and binding on nothing
    QORTUBA_PROJECT_RULE   adopted for Qortuba because the owner said so
    URBAN_STANDARD         company practice, which needs evidence from more than one project or an owner's declaration

Nothing in this registry is at URBAN_STANDARD.  One project is one project, and no owner has declared otherwise yet.

Rules are also held apart by trade.  The plaster invoice deducts openings at half; that says nothing about ceramic, blockwork,
paint or waterproofing, whose own sheets either state a different rule or state none.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
PRC = Path(PR.OUT_DIR) / "pa08_qortuba_pricing"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"

RULE_LEVELS = ("HISTORICAL_PRECEDENT", "QORTUBA_PROJECT_RULE", "URBAN_STANDARD")
SAFETY = ("TRADE_SPECIFIC", "CONTRACTOR_SPECIFIC", "PROJECT_SPECIFIC", "SAFE_URBAN_STANDARD_CANDIDATE")
STATUSES = ("FINAL_QUANTITY_AVAILABLE", "ONE_INPUT_REQUIRED", "PROJECT_RULE_REQUIRED", "SPEC_REQUIRED",
            "DRAWING_REQUIRED", "NOT_APPLICABLE")

W = {"W1": "0449714f-_________________1.xlsx", "W2": "45f2a378-__________.xlsx", "W3": "5a3370bb-_____.xls",
     "W5": "85f545ca-____________________________1.xlsx", "W6": "b324a3e7-______________________.xls",
     "W7": "c52a77de-_______.xlsx"}

# ---------------------------------------------------------------------------- §2 the rules, one row each
# (id, trade, item, description, unit, basis, deduction, addition, wb, sheet, source item, applies, approval, safety, notes)
RULES = [
    ("R-01", "مساح داخلى", "INTERNAL_PLASTER",
     "internal wall plaster is priced by area, built as wall run length x storey height",
     "M2", "wall face length x plaster height", None, None, "W6", "الفاتورة", "مساح م2",
     True, False, "SAFE_URBAN_STANDARD_CANDIDATE",
     "an area unit for an area trade is unremarkable; the arithmetic, not the convention, is what this rule carries"),
    ("R-02", "مساح داخلى", "INTERNAL_PLASTER",
     "openings are deducted at HALF their area, not in full",
     "M2", "gross plaster area", "خصم بالنصف: half the opening area is deducted", None, "W6", "الفاتورة", "مساح م2",
     False, True, "CONTRACTOR_SPECIFIC",
     "a commercial allowance for the labour of working around an opening, agreed with one subcontractor.  It is not a "
     "physical fact and it does not follow from the geometry, so Qortuba must not inherit it without the owner saying so"),
    ("R-03", "مساح داخلى", "PLASTER_CORNERS_AND_ENDS",
     "corner and end beads are measured as running length and then halved",
     "LM", "running length of corners and of wall ends, tracked in two columns per room",
     "2م=1م, written in the deduction column: the measured length is halved to give the net", None,
     "W6", "الفاتورة", "زوايا ونهايات م.ط",
     False, True, "CONTRACTOR_SPECIFIC",
     "a pricing convention with no geometric meaning at all: two measured metres are paid as one.  It is the clearest "
     "example in the library of a rule that must never be generalised"),
    ("R-04", "مساح داخلى", "RENDER_TO_WET_ROOMS",
     "tile backing render to bathrooms and kitchens is a separate priced item from the finish plaster",
     "M2", "wet room wall face length x height", None, None, "W6", "الفاتورة", "طرطشة حمامات ومطابخ م2",
     True, False, "SAFE_URBAN_STANDARD_CANDIDATE",
     "separating a backing coat from a finish coat is ordinary practice and Qortuba already measures the two faces apart"),
    ("R-05", "مساح داخلى", "RENDER_UNDER_SKIRTING",
     "a render band behind the skirting is its own priced item",
     "M2", "skirting run x band height", None, None, "W6", "الفاتورة", "طرطشة تحت نعلة م2",
     True, False, "TRADE_SPECIFIC",
     "Qortuba has the skirting run; the band height is a project input and is not in the drawing"),
    ("R-06", "مساح داخلى", "DOOR_JAMB_PLASTER",
     "plaster to door reveals is measured as an area, count x girth x depth, not as a length",
     "M2", "count x reveal girth x reveal depth", None, None, "W6", "البيــــــــــــان", "شرشوب أبواب",
     True, False, "SAFE_URBAN_STANDARD_CANDIDATE",
     "this corrects a Qortuba assumption that carried reveals in linear metres"),
    ("R-07", "مساح خارجي", "EXTERNAL_PLASTER",
     "external plaster is priced by area with openings deducted at half, on the same invoice as the internal work",
     "M2", "elevation run x height", "خصم بالنصف", None, "W6", "الفاتورة", "مساح خارجى م2",
     False, True, "CONTRACTOR_SPECIFIC",
     "same half deduction as the internal plaster and the same caution applies"),
    ("R-08", "مساح خارجي", "EXTERNAL_CORNERS_JOINTS_AND_BEADS",
     "external corners, movement joints and rounded beads are measured by length and halved",
     "LM", "running length", "2م =1م", None, "W6", "الفاتورة", "زوايا وفواصل ومبروم م.ط",
     False, True, "CONTRACTOR_SPECIFIC", "the external twin of R-03"),
    ("R-09", "صبغ", "WALL_PAINT",
     "wall paint is priced by area, built as wall run x storey height, with openings deducted at half",
     "M2", "paint eligible wall length x height", "خصم بالنصف", None, "W3", "الفاتورة", "صبغ الحوائط م2",
     False, True, "CONTRACTOR_SPECIFIC",
     "the paint invoice carries its own half deduction.  That it matches the plaster invoice is evidence the same "
     "subcontractor negotiated both, not evidence of a company standard"),
    ("R-10", "صبغ", "DECOR_PAINT_WITH_COVE_LIGHT",
     "paint to the decorative ceiling, including the cove light detail, is a separate item from wall paint",
     "M2", "decor ceiling area", None, None, "W3", "الفاتورة", "صبغ الديكور مع الكوف لايت",
     True, False, "TRADE_SPECIFIC",
     "the house prices no flat ceiling paint at all: paint follows the decor area"),
    ("R-11", "مبانى", "BLOCKWORK_BY_THICKNESS",
     "blockwork is priced by area, one item per thickness, built as count x length x height",
     "M2", "count x wall length x wall height", "خصم فراغات, with كلى and نصف columns per wall row", None,
     "W7", "الغلاف", "مبانى سمك 15سم م2 / مبانى سمك 20 سم م2",
     True, False, "SAFE_URBAN_STANDARD_CANDIDATE",
     "pricing blockwork by area per thickness is ordinary; which deduction column is used is the negotiated part"),
    ("R-12", "مبانى", "BLOCKWORK_EXTERNAL",
     "external blockwork is a priced item of its own, separate from the thickness items",
     "M2", "count x wall length x wall height", "خصم فراغات", None, "W7", "الغلاف", "مبانى الخارجي م2",
     True, False, "SAFE_URBAN_STANDARD_CANDIDATE",
     "Qortuba's takeoff already records each wall's rooms on both sides, so the split is available without new measurement"),
    ("R-13", "مبانى", "BLOCKWORK_OPENING_DEDUCTION",
     "openings are deducted against each wall row, with a full column and a half column available",
     "M2", "opening width x opening height", "خصم فراغات كلى or نصف, chosen per row", None, "W7", "الكميات", "خصم فراغات",
     False, True, "CONTRACTOR_SPECIFIC",
     "the blockwork sheet offers both columns and does not state when each is used, so the rule is not readable from the "
     "sheet alone.  Qortuba cannot infer it"),
    ("R-14", "ألمنيوم", "ALUMINIUM_BY_AREA",
     "aluminium is priced by area, built as count x width x height; the count is a multiplier and never the quantity",
     "M2", "count x opening width x opening height", None, None, "W2", "الغلاف",
     "اجمالي الأبواب م2 / اجمالي الشبابيك م2",
     True, False, "SAFE_URBAN_STANDARD_CANDIDATE",
     "corrects the Qortuba row that carried a count of seven as a priced quantity"),
    ("R-15", "ألمنيوم", "ALUMINIUM_TWO_COVER_ITEMS",
     "the bill carries two cover items, doors and windows, with the individual openings as detail rows",
     "M2", "sum of the detail rows", None, None, "W2", "الغلاف", "اجمالي الأبواب / اجمالي الشبابيك",
     True, False, "TRADE_SPECIFIC", "a row-shape rule, not a measurement rule"),
    ("R-16", "عازل حمام+مطابخ", "WET_AREA_WATERPROOFING_FLOOR",
     "wet area floor waterproofing is priced by area",
     "M2", "bathroom and kitchen floor areas", None, None, "W5", "الغلاف", "عازل ارضيات حمامات",
     True, False, "SAFE_URBAN_STANDARD_CANDIDATE", "Qortuba already holds these areas in this unit"),
    ("R-17", "عازل حمام+مطابخ", "WET_AREA_WATERPROOFING_UPTURN",
     "the upturn is priced by LINEAR METRE, so no upturn height enters the quantity",
     "LM", "the wet room perimeter", None, None, "W5", "الغلاف", "نعلات العازل للحمامات",
     True, False, "TRADE_SPECIFIC",
     "the most useful correction in the library: Qortuba carried this as an area awaiting a height that the house never "
     "needed.  Whether the perimeter runs through a doorway or stops at it is NOT stated on the sheet"),
    ("R-18", "عازل سطح", "ROOF_WATERPROOFING",
     "roof and annexe waterproofing is priced by area, with the upturn as a separate linear item",
     "M2", "roof and annexe areas", None, None, "W5", "الغلاف", "عازل اسطح و ملاحق",
     True, False, "SAFE_URBAN_STANDARD_CANDIDATE", "Qortuba has the roof and terrace areas"),
    ("R-19", "عازل سطح", "ROOF_WATERPROOFING_UPTURN",
     "the roof upturn is priced by linear metre, as a separate item from the area",
     "LM", "the roof perimeter", None, None, "W5", "الغلاف", "نعلات العازل الاسطح",
     True, False, "TRADE_SPECIFIC",
     "Qortuba measured the roof AREA but never its perimeter, so this quantity does not exist yet and is not a missing "
     "input so much as a missing measurement"),
    ("R-20", "رخام", "STAIR_AND_LANDING_COMBINED",
     "stairs and landings are one combined area item; treads and risers are not priced separately",
     "M2", "steps as count x tread width, plus landing areas", None, None, "W5", "الغلاف", "اجمالي الدرج والبسطات",
     True, False, "TRADE_SPECIFIC",
     "a row-shape rule that collapses five Qortuba rows into one"),
    ("R-21", "رخام", "STAIR_SKIRTING",
     "stair skirting is priced by linear metre", "LM", "sloped developed length along the flight", None, None,
     "W5", "الغلاف", "اجمالي النعلات (رخام)", True, False, "SAFE_URBAN_STANDARD_CANDIDATE", None),
    ("R-22", "رخام", "STAIR_SIDE_PIECE",
     "the stair side piece is COUNTED, one per step, not measured by length",
     "NR", "one per tread", None, None, "W5", "الغلاف", "اجمالي التواشيح",
     True, False, "TRADE_SPECIFIC",
     "corrects a Qortuba row that carried nosing in linear metres"),
    ("R-23", "ديكور جبس", "DECOR_AREA_PLUS_CORNICE",
     "ceiling decor is two items per zone: an area and a cornice run",
     "M2 and LM", "ceiling area, and room perimeter for the cornice", None, None, "W5", "الغلاف",
     "ديكور + كرانيش", True, False, "SAFE_URBAN_STANDARD_CANDIDATE",
     "Qortuba holds both the ceiling area and the room perimeter already"),
    ("R-24", "ديكور جبس", "DECOR_DRY_WET_SPLIT",
     "decor is split into dry rooms against bathrooms and kitchens, as separate priced lines",
     "M2 and LM", "the same measurement, cut by zone", None, None, "W5", "الغلاف",
     "الصالات والغرف / الحمامات والمطابخ", True, False, "TRADE_SPECIFIC",
     "Qortuba already classifies every room dry or wet, so the split needs no new measurement"),
    ("R-25", "سيراميك", "FLOOR_CERAMIC_BY_AREA",
     "floor ceramic is priced by area, with no deduction column used on the cover",
     "M2", "room floor areas summed", "none applied on the cover: gross equals net", None, "W5", "الغلاف",
     "اجمالي الارضيات", True, False, "SAFE_URBAN_STANDARD_CANDIDATE",
     "that this cover shows no deduction is evidence about this bill, not a rule that ceramic is never deducted"),
    ("R-26", "سيراميك", "SKIRTING_BY_LENGTH",
     "ceramic skirting is priced by linear metre", "LM", "running length per room",
     "none applied on the cover", None, "W5", "الغلاف", "اجمالي النعلات (سيراميك)",
     True, False, "SAFE_URBAN_STANDARD_CANDIDATE", None),
    ("R-27", "سيراميك", "WALL_CERAMIC_BY_AREA",
     "wall ceramic is priced by area, built as wall run x tiling height",
     "M2", "wall run length x tiling height", None, None, "W5", "الغلاف", "اجمالي الحوائط",
     True, False, "SAFE_URBAN_STANDARD_CANDIDATE", None),
    ("R-28", "سيراميك", "NAMED_SPECIAL_ROOM_LINE",
     "a named special room is given its own cover line rather than folded into a total",
     "M2", "that room's own area", None, None, "W5", "الغلاف", "ارضيات حمام السباحه",
     True, False, "TRADE_SPECIFIC", "a row-shape rule; Qortuba's three bathrooms could follow it"),
    ("R-29", "الحوش", "COURTYARD_AS_ITS_OWN_SCOPE",
     "a courtyard is a scope of its own on the cover, with floors and skirtings, not part of the internal totals",
     "M2 and LM", "courtyard floor area and skirting run", None, None, "W5", "الغلاف",
     "ارضيات الحوش / نعلات الحوش", True, False, "PROJECT_SPECIFIC",
     "whether Qortuba's terraces are a حوش in this sense is a scope question for the owner, not a reading of the drawing"),
    ("R-30", "درابزين", "RAILING_BY_LENGTH",
     "railing is one priced item by linear metre, with no split between sloped and horizontal",
     "LM", "running length", None, None, "W5", "الغلاف", "دربزين داخلي",
     True, False, "TRADE_SPECIFIC", "collapses two Qortuba rows into one"),
    ("R-31", "خرسانة", "CONCRETE_BY_VOLUME",
     "concrete is priced by volume, built as width x length x height x count, with a deduction volume column",
     "M3", "element volumes by structural type", "خصم as a volume and a count column", None, "W1", "القواعد",
     "حصر خرسانة القواعد المسلحة", True, False, "SAFE_URBAN_STANDARD_CANDIDATE", None),
    ("R-32", "حديد", "STEEL_AS_A_COLUMN",
     "reinforcement is carried in tonnes as a column beside the concrete items, not as a bill of its own",
     "TON", "reinforcement weight", None, None, "W1", "ورقة1", "كميات الحديد(طن)",
     True, False, "TRADE_SPECIFIC", "a workbook organisation rule"),
    ("R-33", "عام", "SUMMARY_AND_DETAIL_SHAPE",
     "each trade package is one workbook: a summary invoice carrying priced items, and detail sheets measuring element by "
     "element under storey headings",
     None, "n/a", None, None, "W5", "الغلاف / الكميات", "the workbook structure itself",
     True, False, "SAFE_URBAN_STANDARD_CANDIDATE",
     "the same shape appears in all six workbooks, which is the strongest multi-source evidence in the library.  It is "
     "still not declared a standard: it is a format, and the owner has not said it is fixed"),
    ("R-34", "عام", "LUMP_SUM_INSIDE_A_MEASURED_BILL",
     "a lump sum line may sit inside a measured bill, marked مقطوعية",
     "NR", "not measured", None, None, "W6", "الفاتورة", "فرفيس مقطوعية",
     True, False, "SAFE_URBAN_STANDARD_CANDIDATE", "permits a shape Qortuba currently has no way to express"),
    ("R-35", "عام", "ADDITION_COLUMN",
     "an addition column sits beside the deduction columns, so an addition is never folded into the measured figure",
     None, "n/a", None, "إضافة as its own column", "W7", "الكميات", "إضافة",
     True, False, "SAFE_URBAN_STANDARD_CANDIDATE",
     "matches the Qortuba principle that a measured figure is never edited, only accompanied"),
]

# ---------------------------------------------------------------------------- §5/§4 the conversion map
# (input id, trade, boq item, measured value key, input unit, target unit, formula, missing, commercial rule, status)
def conversion_rows(v):
    R = []

    def add(iid, trade, item, val, iu, tu, formula, missing, rule, status, notes=None):
        R.append({"MEASUREMENT_INPUT_ID": iid, "TRADE": trade, "BOQ_ITEM": item,
                  "MEASURED_INPUT": val, "INPUT_UNIT": iu, "TARGET_PRICING_UNIT": tu,
                  "CONVERSION_FORMULA": formula, "MISSING_INPUT": missing,
                  "COMMERCIAL_RULE_REQUIRED": rule, "CURRENT_STATUS": status,
                  "PHYSICAL_MEASUREMENT": {"VALUE": val, "UNIT": iu,
                                           "STATE": "SOURCE_ESTABLISHED" if val is not None else "NOT_MEASURED"},
                  "COMMERCIAL_MEASUREMENT_RULE": {"VALUE": None, "STATE": "PROJECT_RULE_REQUIRED" if rule else "NOT_REQUIRED",
                                                  "CANDIDATE": rule},
                  "FINAL_BOQ_QUANTITY": {"VALUE": None, "UNIT": tu},
                  "NOTES": notes})

    # A blockwork, one row per thickness, kept separate
    for t, m in sorted(v["WALL_BY_THK"].items(), key=lambda kv: -kv[1]):
        add(f"CM-B{t}", "مبانى", f"BLOCKWORK_{t}", m, "M", "M2",
            "plan length x wall height, less opening areas per the approved deduction column",
            "the blockwork wall height", "R-13: which deduction column, full or half", "ONE_INPUT_REQUIRED",
            "thicknesses are never merged")
    add("CM-BEXT", "مبانى", "BLOCKWORK_EXTERNAL", None, None, "M2",
        "external wall length x height",
        "the blockwork wall height, and the external/internal split applied to the existing wall rows",
        "R-13", "ONE_INPUT_REQUIRED",
        "the split needs no new measurement: each wall row already names its rooms on both sides")

    # B internal plaster
    add("CM-IP1", "مساح داخلى", "INTERNAL_PLASTER", v["PLASTER_NORMAL_LM"], "LM", "M2",
        "face length x plaster height, less openings per the approved rule, plus reveals",
        "the internal plaster height", "R-02: half opening deduction, or full engineering deduction",
        "ONE_INPUT_REQUIRED", "physical gross area and commercial payable area are two different numbers")
    add("CM-IP2", "مساح داخلى", "RENDER_TO_WET_ROOMS", v["PLASTER_WET_LM"], "LM", "M2",
        "wet room face length x plaster height", "the internal plaster height", None, "ONE_INPUT_REQUIRED", None)
    add("CM-IP3", "مساح داخلى", "RENDER_UNDER_SKIRTING", v["SKIRTING_LM"], "LM", "M2",
        "skirting run x render band height", "the render band height", None, "ONE_INPUT_REQUIRED",
        "a house item Qortuba did not have; the run already exists")
    add("CM-IP4", "مساح داخلى", "DOOR_JAMB_PLASTER", len(v["DOOR_OPS"]), "NR", "M2",
        "count x reveal girth x reveal depth", "the opening heights and the reveal depth", None, "DRAWING_REQUIRED",
        "the house measures this as an area, not a length")
    add("CM-IP5", "مساح داخلى", "PLASTER_CORNERS_AND_ENDS", None, None, "LM",
        "running length of internal corners and wall ends, halved if the 2م=1م rule is adopted",
        "a cut of the boundary geometry into corners and ends, which Qortuba has never made",
        "R-03: the 2م=1م halving", "PROJECT_RULE_REQUIRED",
        "the geometry exists inside the boundary segments but was never counted as corners")

    # C paint
    add("CM-PT1", "صبغ", "WALL_PAINT", v["PAINT_LM"], "LM", "M2",
        "paint eligible length x wall height, less openings per the approved rule",
        "the wall height for paint", "R-09: half opening deduction, decided independently of plaster",
        "ONE_INPUT_REQUIRED", "paint must not inherit the plaster decision by default")
    add("CM-PT2", "صبغ", "DECOR_PAINT_WITH_COVE_LIGHT", None, None, "M2",
        "decor ceiling area", "the ceiling design, which establishes the decor area", None, "DRAWING_REQUIRED",
        "the house prices no flat ceiling paint, so Qortuba's flat ceiling area is not this quantity")

    # D aluminium
    wins = [b for b in v["BLUE"] if b["TYPE"] == "WINDOW_WITH_WALL_BELOW"]
    unres = [b for b in v["BLUE"] if b["TYPE"] == "UNRESOLVED"]
    add("CM-AL1", "ألمنيوم", "ALUMINIUM_WINDOWS", round(sum(b["WIDTH_MM"] for b in wins) / 1000, 3), "M (widths)",
        "M2", "count x width x height, summed to one windows item",
        "the opening heights and the system specification", None, "DRAWING_REQUIRED",
        f"{len(wins)} measured widths, all of them classed as windows; the count is a multiplier, never the quantity")
    add("CM-AL3", "ألمنيوم", "ALUMINIUM_UNCLASSIFIED_GLAZED_ELEMENT",
        round(sum(b["WIDTH_MM"] for b in unres) / 1000, 3), "M (widths)", "M2",
        "the same arithmetic once the element is classed",
        "the elevation or the aluminium schedule, to say what "
        + ", ".join(b["BLUE_ELEMENT_ID"] for b in unres) + " is",
        None, "DRAWING_REQUIRED",
        "the house bills doors and windows as two separate cover items, so an unclassified glazed element cannot be "
        "added to either.  It is held out of CM-AL1 rather than folded into it")
    add("CM-AL2", "ألمنيوم", "ALUMINIUM_DOORS", len(v["DOOR_OPS"]), "NR", "M2",
        "count x width x height, summed to one doors item",
        "the opening heights", None, "DRAWING_REQUIRED", "door widths are measured; heights are not")

    # E waterproofing
    add("CM-WP1", "عازل حمام+مطابخ", "WET_AREA_WATERPROOFING_FLOOR", v["WET_FLOOR_M2"], "M2", "M2",
        "the measured bathroom floor areas, unchanged", None, None, "FINAL_QUANTITY_AVAILABLE",
        "the house bills عازل ارضيات حمامات by area with no deduction, Qortuba holds that area, and the two units are the "
        "same, so the conversion is the identity.  The membrane specification is still outstanding, but it sets the RATE "
        "and not the quantity, which is why this row is final and the ceramic rows above it are not")
    add("CM-WP2", "عازل حمام+مطابخ", "WET_AREA_WATERPROOFING_UPTURN", v["BATH_HOST_LM"], "LM", "LM",
        "the wet room perimeter, unchanged: the house needs no upturn height",
        None, "the doorway treatment: gross perimeter through the opening, or net stopping at the jamb",
        "PROJECT_RULE_REQUIRED",
        "the measured figure is the net path, which stops at the doorway.  Whether the house takes it gross is not "
        "written on the sheet, so this is a project rule and not yet a final quantity")
    add("CM-WP3", "عازل سطح", "ROOF_WATERPROOFING", v["ROOF_M2"], "M2", "M2",
        "the measured roof area, unchanged", None, None, "SPEC_REQUIRED",
        "scope confirmation and the membrane specification remain")
    add("CM-WP4", "عازل سطح", "ROOF_WATERPROOFING_TERRACE", v["TERRACE_M2"], "M2", "M2",
        "the measured terrace area, unchanged, under the ملاحق part of the roof item", None, None, "SPEC_REQUIRED", None)
    add("CM-WP5", "عازل سطح", "ROOF_WATERPROOFING_UPTURN", None, None, "LM",
        "the roof perimeter", "the roof perimeter, which Qortuba never measured", None, "NOT_APPLICABLE",
        "a missing measurement rather than a missing input; it would need a new takeoff, which this phase does not do")

    # F stairs and marble
    add("CM-MR1", "رخام", "STAIR_AND_LANDING_COMBINED", v["STAIR_M2"], "M2 (plan footprint)", "M2",
        "steps as count x tread width, plus landing areas, per the house's combined item",
        "the stair section, giving the riser count", None, "DRAWING_REQUIRED",
        "the plan footprint is NOT this quantity and must not be used as it")
    add("CM-MR2", "رخام", "STAIR_SKIRTING", None, None, "LM",
        "sloped developed length along each flight", "the stair section", None, "DRAWING_REQUIRED", None)
    add("CM-MR3", "رخام", "STAIR_SIDE_PIECE", None, None, "NR",
        "one per tread", "the stair section, giving the step count", None, "DRAWING_REQUIRED",
        "counted, not measured by length")

    # G ceiling decor
    add("CM-CL1", "ديكور جبس", "GYPSUM_DECOR_DRY_ROOMS", None, None, "M2",
        "the part of the ceiling the design assigns to decor, dry rooms only",
        "the ceiling design", None, "DRAWING_REQUIRED",
        f"Qortuba holds {v['CEILING_M2']} m2 of flat ceiling geometry, which is not a decor quantity")
    add("CM-CL2", "ديكور جبس", "CORNICE_DRY_ROOMS", v["CEILING_PERIM_DRY_LM"], "LM", "LM",
        "the perimeter stretches the design runs cornice along, dry rooms",
        "the ceiling design, to say where cornice actually runs", None, "DRAWING_REQUIRED",
        "the unit is already right and the dry perimeter is measured; only the design extent is missing")
    add("CM-CL3", "ديكور جبس", "CORNICE_WET_ROOMS", v["CEILING_PERIM_WET_LM"], "LM", "LM",
        "the same, bathrooms and kitchens", "the ceiling design", None, "DRAWING_REQUIRED", None)

    # ceramic
    add("CM-C1", "سيراميك", "FLOOR_CERAMIC_TOTAL", v["DRY_FLOOR_M2"], "M2", "M2",
        "the room areas the finishes schedule assigns to ceramic", "the finishes schedule", None, "SPEC_REQUIRED",
        "unit already correct; the scope within it is not drawn")
    add("CM-C2", "سيراميك", "FLOOR_CERAMIC_BATHROOMS", v["WET_FLOOR_M2"], "M2", "M2",
        "the bathroom areas, as their own cover line per R-28", "the finishes schedule", None, "SPEC_REQUIRED", None)
    add("CM-C3", "سيراميك", "WALL_CERAMIC_BATHROOMS", v["BATH_HOST_LM"], "LM", "M2",
        "net host wall x tiling height", "the wall tiling height", None, "ONE_INPUT_REQUIRED", None)
    add("CM-C4", "سيراميك", "WALL_CERAMIC_PREPARATION", v["PREP_HOST_LM"], "LM", "M2",
        "net host wall x tiling height", "the wall tiling height", None, "ONE_INPUT_REQUIRED", None)
    add("CM-C5", "سيراميك", "SKIRTING_BY_LENGTH", v["SKIRTING_LM"], "LM", "LM",
        "the eligible wall path, adjusted by the approved deduction rule if any",
        None, "whether the house's no-deduction cover practice applies to Qortuba", "PROJECT_RULE_REQUIRED",
        "unit and geometry both ready; only the commercial basis is open")

    # H black profile, no precedent
    add("CM-PR1", "بروفايل", "PROFILE_ABOVE_SKIRTING", v["PROFILE_LM"], "LM", "LM",
        "the skirting path, if the owner confirms the profile shares it",
        None, "whether the payable profile path is exactly the payable skirting path",
        "PROJECT_RULE_REQUIRED",
        "a NEW candidate item with no historical precedent; see the candidate item register")

    # railings
    add("CM-RL1", "درابزين", "RAILING_BY_LENGTH", None, None, "LM",
        "running length of railing", "a railing layout and specification", None, "DRAWING_REQUIRED",
        "one house item, not two")
    # concrete and steel
    add("CM-CN1", "خرسانة", "CONCRETE_BY_VOLUME", None, None, "M3",
        "width x length x height x count per element", "the structural drawings", None, "DRAWING_REQUIRED", None)
    add("CM-ST1", "حديد", "STEEL_AS_A_COLUMN", None, None, "TON",
        "reinforcement weight beside the concrete items", "the structural drawings", None, "DRAWING_REQUIRED", None)
    return R


# ---------------------------------------------------------------------------- §5H the one item with no precedent at all
# same tuple shape as RULES, plus the level it is entered at
CANDIDATE_RULES = [
    ("R-36", "بروفايل", "PROFILE_ABOVE_SKIRTING",
     "a black profile run directly above the skirting is a priced item of its own, measured by linear metre",
     "LM", "the same eligible wall path the skirting runs along, issued under its own item number",
     None, None, None, None, None,
     True, True, "PROJECT_SPECIFIC",
     "NO HISTORICAL PRECEDENT EXISTS.  Nothing in the six workbooks prices a profile above a skirting; the nearest item, "
     "كرانيش, is a ceiling cornice and a different product.  The unit is proposed by analogy with نعلات, which the house "
     "does price by م.ط, and the path comes from the owner's physical statement that the profile sits directly above the "
     "skirting.  It is entered as a Qortuba project rule and stands as a candidate for an Urban standard, but one project "
     "is not a standard and the owner has not approved it",
     "QORTUBA_PROJECT_RULE"),
]

CANDIDATE_ITEM_AR = "بروفايل أعلى النعلة"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
    return name


def reg(folder, name):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


def verify_inputs():
    """Read nothing until every frozen input verifies byte for byte."""
    checked = []
    for folder, name in ((QS, "PA08_QORTUBA_ROOM_BY_ROOM_QS_01"),
                         (PRC, "QORTUBA_FINAL_PRICING_AUDIT"),
                         (OUT, "URBAN_PROJECTS_BOQ_SCHEMA_LIBRARY"),
                         (OUT, "QORTUBA_VERSUS_HOUSE_BOQ_SCHEMA")):
        fr = json.loads((folder / f"FREEZE_{name}.json").read_text("utf-8"))
        bad = [n for n, h in fr["CONTENTS"].items()
               if not (folder / f"{n}.json").exists() or _sha(folder / f"{n}.json") != h]
        if bad:
            raise SystemExit(f"{name} changed on disk, refusing to build a rule registry on it: {bad}")
        checked.append({"FREEZE": name, "DIGEST": fr["DIGEST"], "ARTIFACTS": len(fr["CONTENTS"]), "VERIFIED": True})
    return checked


# ---------------------------------------------------------------------------- the frozen Qortuba measurement inputs
def sources():
    """Every Qortuba number this phase is allowed to see, read from the frozen workpapers and not recomputed."""
    summ = reg(QS, "QORTUBA_QS01_SUMMARY_TOTALS")
    inv = reg(QS, "QORTUBA_ROOM_REGISTER")["ROWS"]
    skirt = reg(QS, "QORTUBA_QS01_SKIRTING_TAKEOFF")["ROWS"]
    plaster = reg(QS, "QORTUBA_QS01_PLASTER_AND_PAINT_TAKEOFF")["ROWS"]
    walls = reg(QS, "QORTUBA_QS01_BLOCK_WALL_TAKEOFF")
    blue = reg(QS, "QORTUBA_QS01_BLUE_ELEMENT_SCHEDULE")["ROWS"]

    zones = defaultdict(float)
    for x in inv:
        if not x["INSIDE_APARTMENT"]:
            zones[x["ZONE_KIND"]] += x["RASTER_AREA_M2"]
    zones = {k: round(v, 3) for k, v in zones.items()}

    # the ceiling cornice runs along the room's own wall line, so it inherits the skirting register's GROSS perimeter -
    # not the net skirting run, which stops at every doorway.  Splitting it dry against wet is the house's R-24 shape.
    perim = defaultdict(float)
    for x in skirt:
        perim[x["WET_OR_DRY"]] += x["GROSS_WALL_LINE_PERIMETER_LM"]

    return {
        "DRY_FLOOR_M2": summ["A_DRY_INTERNAL_FLOOR_AREA_M2"]["VALUE"],
        "WET_FLOOR_M2": summ["B_WET_INTERNAL_FLOOR_AREA_M2"]["VALUE"],
        "SKIRTING_LM": summ["D_TOTAL_SKIRTING_LM"]["VALUE"],
        "PROFILE_LM": summ["E_TOTAL_BLACK_PROFILE_LM"]["VALUE"],
        "CEILING_M2": summ["F_TOTAL_CEILING_GEOMETRY_M2"]["VALUE"],
        "BATH_HOST_LM": summ["H_TOTAL_BATHROOM_HOST_WALL_LM"]["VALUE"],
        "PREP_HOST_LM": summ["I_TOTAL_PREPARATION_HOST_WALL_LM"]["VALUE"],
        "PAINT_LM": summ["N_TOTAL_PAINT_ELIGIBLE_FACE_LENGTH_LM"]["VALUE"],
        "CEILING_PERIM_DRY_LM": round(perim["DRY"], 3),
        "CEILING_PERIM_WET_LM": round(perim["WET"], 3),
        "PLASTER_NORMAL_LM": round(sum(p["NORMAL_INTERNAL_PLASTER_FACE_LM"] for p in plaster), 3),
        "PLASTER_WET_LM": round(sum(p["WET_ROOM_TILE_PREP_FACE_LM"] for p in plaster), 3),
        "PLASTER_COLUMN_LM": round(sum(p["COLUMN_FACE_LM"] for p in plaster), 3),
        "WALL_BY_THK": walls["TOTAL_LENGTH_M_BY_THICKNESS"],
        "DOOR_OPS": [o for w in walls["ROWS"] for o in w["OPENINGS"] if "DOOR" in o["CLASS"]],
        "BLUE": blue,
        "ROOF_M2": zones.get("OPEN_ROOF"),
        "TERRACE_M2": zones.get("EXTERNAL_TERRACE"),
        "STAIR_M2": round(zones.get("STAIR", 0.0) + zones.get("STAIR_LANDING", 0.0), 3),
    }


# ---------------------------------------------------------------------------- §2 the registry itself
def registry_rows():
    rows, wbs = [], {w["KEY"]: w for w in reg(OUT, "URBAN_PROJECTS_BOQ_SCHEMA_LIBRARY")["WORKBOOKS"]}
    for t in RULES + CANDIDATE_RULES:
        (rid, trade, item, desc, unit, basis, ded, addn, wb, sheet, src, applies, approval, safety, notes) = t[:15]
        level = t[15] if len(t) > 15 else "HISTORICAL_PRECEDENT"
        rows.append({
            "RULE_ID": rid, "TRADE": trade, "ITEM": item, "RULE_DESCRIPTION": desc,
            "PRICING_UNIT": unit, "QUANTITY_BASIS": basis,
            "DEDUCTION_RULE": ded, "ADDITION_RULE": addn,
            "SOURCE_WORKBOOK": (W[wb] if wb else None),
            "SOURCE_WORKBOOK_TITLE_AR": (wbs[wb]["TITLE_AR"] if wb else None),
            "SOURCE_SHEET": sheet, "SOURCE_ITEM": src,
            "RULE_LEVEL": level,
            "APPLIES_TO_QORTUBA": applies,
            "OWNER_APPROVAL_REQUIRED": approval,
            "GENERALISATION_SAFETY": safety,
            "NOTES": notes,
        })
    return rows


# ---------------------------------------------------------------------------- §7 what may and may not be generalised
SAFETY_MEANING = {
    "TRADE_SPECIFIC": "true of this trade on this project's bill and of nothing else; it must never be carried to another "
                      "trade, however similar the arithmetic looks",
    "CONTRACTOR_SPECIFIC": "a commercial allowance agreed with one subcontractor.  It has no geometric meaning, it was "
                           "probably priced into the rate, and it must not be applied to Qortuba without the owner",
    "PROJECT_SPECIFIC": "a scope decision belonging to one project's design, not a measurement convention at all",
    "SAFE_URBAN_STANDARD_CANDIDATE": "ordinary practice, consistent with how the trade is measured generally, and a "
                                     "reasonable candidate to become an Urban standard once a second project or the "
                                     "owner confirms it.  It is NOT a standard yet",
}


def safety_register(rows):
    out = []
    for s in SAFETY:
        members = [r for r in rows if r["GENERALISATION_SAFETY"] == s]
        out.append({
            "SAFETY_CLASS": s, "MEANING": SAFETY_MEANING[s], "COUNT": len(members),
            "RULES": [{"RULE_ID": r["RULE_ID"], "TRADE": r["TRADE"], "ITEM": r["ITEM"],
                       "RULE_DESCRIPTION": r["RULE_DESCRIPTION"]} for r in members],
            # §T, the owner's correction: a candidate is not a standard, and only a standard applies on its own.
            "MAY_BE_APPLIED_TO_QORTUBA_WITHOUT_OWNER": False,
            "WHY_NOT_APPLIED": "a candidate never applies automatically.  Only an APPROVED_URBAN_STANDARD may act on "
                               "its own, and then only below a project drawing and an owner override",
            "MAY_BE_PROMOTED_TO_URBAN_STANDARD_NOW": False,
            "WHY_NOT_PROMOTED": "every rule here was read off ONE previous project.  A second project, or the owner "
                                "declaring it company practice, is what turns a precedent into a standard",
        })
    return out


# ---------------------------------------------------------------------------- §6 what only the owner can answer
# Each entry matches on the blocker text the conversion rows already carry, so the rows it unlocks are counted and not
# claimed.  A missing drawing is not a decision and does not belong here: those are listed separately as documents.
DECISIONS = [
    ("D-01", "PROJECT_INPUT", "What is the clear wall height used for blockwork?",
     ["the blockwork wall height"],
     "every blockwork item is priced by area as length x height.  Qortuba has measured 138.730 m of wall in eight "
     "thicknesses and can convert none of it without one number",
     ["a single storey height in millimetres", "a height per storey if they differ"]),
    ("D-02", "PROJECT_INPUT", "What is the internal plaster height?",
     ["the internal plaster height"],
     "plaster and the wet-room backing render are both priced by area and both have their run length measured.  The "
     "height may differ from the blockwork height if plaster stops at a ceiling line",
     ["the same as the wall height", "a separate plaster height in millimetres"]),
    ("D-03", "PROJECT_INPUT", "To what height are the bathroom and preparation walls tiled?",
     ["the wall tiling height"],
     "38.750 m of net host wall is measured and waiting on one number to become an area",
     ["full height to ceiling", "a stated height in millimetres", "a height per room"]),
    ("D-04", "PROJECT_INPUT", "What is the wall height for paint?",
     ["the wall height for paint"],
     "paint is priced by area over 107.625 m of measured eligible face.  It is asked separately from D-01 only because "
     "paint may stop at a cornice",
     ["the same as the wall height", "a separate paint height"]),
    ("D-05", "PROJECT_INPUT", "What are the door and window opening heights?",
     ["the opening heights"],
     "aluminium is priced by area as count x width x height.  Seven glazed widths and eight door widths are measured; "
     "no height exists anywhere in the drawing set",
     ["a standard height for all openings", "a schedule of heights"]),
    ("D-06", "PROJECT_INPUT", "What is the height of the render band behind the skirting?",
     ["the render band height"],
     "the house prices طرطشة تحت نعلة as an area and Qortuba already holds the 106.075 m run",
     ["a band height in millimetres", "the item does not apply to Qortuba"]),
    ("D-07", "PROJECT_RULE", "Does the black profile follow exactly the same payable path as the skirting?",
     ["whether the payable profile path is exactly the payable skirting path"],
     "the owner has already said the profile sits directly above the skirting, which is why the two share a geometric "
     "path.  What is NOT established is whether they share a payable path: if the profile crosses a doorway head or "
     "stops short of one, its billed length differs from the skirting's while the geometry stays the same",
     ["yes: the profile is billed on the skirting path, 106.075 lm",
      "no: the profile path differs and needs its own rule"]),
    ("D-08", "PROJECT_RULE", "Does the skirting quantity take a deduction, or is it billed as measured?",
     ["whether the house's no-deduction cover practice applies to Qortuba"],
     "the historical cover shows اجمالي النعلات with no deduction column used.  That is evidence about one bill, not a "
     "rule.  Qortuba's 106.075 m is already net of doorways as a matter of geometry; whether the bill takes it further "
     "is commercial",
     ["billed as measured, 106.075 lm", "a stated deduction applies"]),
    ("D-09", "PROJECT_RULE", "Does the bathroom waterproofing upturn run through the doorway or stop at it?",
     ["the doorway treatment"],
     "the house prices نعلات العازل للحمامات by linear metre, so no upturn height is needed and 27.600 m is measured "
     "and ready.  The only open question is one of path: the measured figure stops at each doorway",
     ["gross, running through the openings", "net, stopping at each doorway, 27.600 lm"]),
    ("D-10", "PROJECT_RULE", "How are openings deducted from blockwork: the full column or the half column?",
     ["R-13"],
     "the historical blockwork sheet offers a كلى column and a نصف column and never says which applies when.  The rule "
     "cannot be read off the sheet, so it cannot be inferred for Qortuba",
     ["full opening area deducted", "half the opening area deducted", "no deduction"]),
    ("D-11", "PROJECT_RULE", "Does Qortuba inherit the half-deduction of openings for plaster?",
     ["R-02"],
     "خصم بالنصف appears on one previous project's plaster invoice.  It is a commercial allowance agreed with one "
     "subcontractor, it has no geometric meaning, and it may already be priced into that project's rate",
     ["yes, half", "no, deduct openings in full", "no deduction"]),
    ("D-12", "PROJECT_RULE", "Does Qortuba inherit the half-deduction of openings for paint?",
     ["R-09"],
     "the paint invoice carries its own half deduction.  That it matches the plaster invoice is evidence the same "
     "subcontractor negotiated both, not evidence of a company rule, so paint is asked separately on purpose",
     ["yes, half", "no, deduct openings in full", "no deduction"]),
    ("D-13", "PROJECT_RULE", "Does the 2م=1م halving of corners and wall ends apply to Qortuba?",
     ["R-03"],
     "two measured metres paid as one is the clearest contractor-specific convention in the library.  It is asked last "
     "because Qortuba has not cut its boundary geometry into corners and ends, so the answer unlocks nothing yet",
     ["yes, halve the measured length", "no, pay the measured length", "the item does not apply"]),
]


def owner_decisions(conv):
    out = []
    for did, kind, q, keys, why, options in DECISIONS:
        hit, alone = [], []
        for r in conv:
            blockers = [r["MISSING_INPUT"], r["COMMERCIAL_RULE_REQUIRED"]]
            mine = [b for b in blockers if b and any(k in b for k in keys)]
            if not mine:
                continue
            hit.append(r)
            # a blocker that names two needs is not satisfied by one answer, so a compound string never counts as final
            if all((b is None or b in mine) for b in blockers) and not any(" and " in b for b in mine):
                alone.append(r)
        measured = [r for r in hit if r["MEASURED_INPUT"] is not None]
        out.append({
            "DECISION_ID": did, "DECISION_KIND": kind, "QUESTION": q, "WHY_IT_MATTERS": why, "OPTIONS": options,
            "ROWS_AFFECTED": [r["MEASUREMENT_INPUT_ID"] for r in hit],
            "ROWS_AFFECTED_COUNT": len(hit),
            "ROWS_CARRYING_A_MEASURED_VALUE": len(measured),
            "ROWS_THIS_ANSWER_ALONE_MAKES_FINAL": [r["MEASUREMENT_INPUT_ID"] for r in alone if r["MEASURED_INPUT"] is not None],
            "IF_NOT_ANSWERED": "the affected rows stay at their current status.  No default is applied and no historical "
                               "value is substituted",
        })
    out.sort(key=lambda d: (-len(d["ROWS_THIS_ANSWER_ALONE_MAKES_FINAL"]), -d["ROWS_CARRYING_A_MEASURED_VALUE"],
                            d["DECISION_ID"]))
    return out


def documents_required(conv):
    """Not decisions: things that exist on paper somewhere and simply have not been supplied."""
    acc = defaultdict(list)
    for r in conv:
        b = r["MISSING_INPUT"]
        if b and r["CURRENT_STATUS"] in ("DRAWING_REQUIRED", "SPEC_REQUIRED"):
            key = ("the finishes schedule" if "finishes schedule" in b else
                   "the reflected ceiling plan or ceiling design" if "ceiling design" in b else
                   "the stair section" if "stair section" in b else
                   "the structural drawings" if "structural drawings" in b else
                   "the aluminium and door schedules" if "opening heights" in b else b)
            acc[key].append(r["MEASUREMENT_INPUT_ID"])
    return [{"DOCUMENT": k, "ROWS_WAITING": sorted(set(vv)), "COUNT": len(set(vv))}
            for k, vv in sorted(acc.items(), key=lambda kv: -len(set(kv[1])))]


# ---------------------------------------------------------------------------- §8 readiness, per trade
def readiness(conv):
    out = []
    for trade in sorted({r["TRADE"] for r in conv}):
        rows = [r for r in conv if r["TRADE"] == trade]
        final = [r for r in rows if r["CURRENT_STATUS"] == "FINAL_QUANTITY_AVAILABLE"]
        na = [r for r in rows if r["CURRENT_STATUS"] == "NOT_APPLICABLE"]
        blocked = [r for r in rows if r not in final and r not in na]
        out.append({
            "TRADE": trade,
            "BOQ_ITEMS": len(rows),
            "FINAL_BOQ_QUANTITY_AVAILABLE": len(final),
            "BLOCKED": len(blocked),
            "WHAT_BLOCKS_IT": sorted({(r["MISSING_INPUT"] or r["COMMERCIAL_RULE_REQUIRED"] or "") for r in blocked} - {""}),
            "TRADE_READY_TO_PRICE": bool(final) and not blocked,
        })
    return out


# ---------------------------------------------------------------------------- §5H the new candidate BOQ item
def candidate_items(v):
    return [{
        "CANDIDATE_ITEM_ID": "NEW-01",
        "ITEM_AR": CANDIDATE_ITEM_AR,
        "ITEM_EN": "black profile above the skirting",
        "TRADE_AR": "بروفايل",
        "PROPOSED_PRICING_UNIT": "LM",
        "PROPOSED_PRICING_UNIT_AR": "م.ط",
        "RULE_ID": "R-36",
        "RULE_LEVEL": "QORTUBA_PROJECT_RULE",
        "URBAN_STANDARD_CANDIDATE": True,
        "PROMOTED_TO_URBAN_STANDARD": False,
        "OWNER_APPROVAL_REQUIRED": True,
        "HISTORICAL_PRECEDENT": None,
        "WHY_NO_PRECEDENT": "no item in the six historical workbooks prices a profile above a skirting.  The search was "
                            "made across every trade cover and every detail sheet, not only the ceramic package.  The "
                            "nearest match by name, كرانيش, is a gypsum ceiling cornice and a different product",
        "UNIT_BASIS": "proposed by analogy with نعلات, which the house prices م.ط, and because the element is a run",
        "QUANTITY_IF_APPROVED": {"VALUE": v["PROFILE_LM"], "UNIT": "LM",
                                 "CONDITIONAL_ON": "D-07: that the payable profile path is the payable skirting path"},
        "GEOMETRY_SOURCE": "QORTUBA_QS01_PROFILE_TAKEOFF, which inherits the skirting's eligible wall path under its own "
                           "trade id.  It was not measured a second time and no second perimeter was invented",
        "SEPARATE_ITEM_FROM_SKIRTING": True,
        "WHY_SEPARATE": "one path, two trades: the skirting and the profile are bought, fixed and priced separately even "
                        "where they run along the same line",
    }]


def apply_final_quantities(conv):
    """A final BOQ quantity is written only where the conversion is the identity and nothing is outstanding."""
    n = 0
    for r in conv:
        if r["CURRENT_STATUS"] == "FINAL_QUANTITY_AVAILABLE" and r["MEASURED_INPUT"] is not None:
            r["FINAL_BOQ_QUANTITY"] = {"VALUE": r["MEASURED_INPUT"], "UNIT": r["TARGET_PRICING_UNIT"],
                                       "STATE": "FINAL",
                                       "WHY": "the measured unit and the house pricing unit are the same and the house "
                                              "bills this item with no deduction, so the conversion is the identity"}
            n += 1
    return n


def finish():
    ver = verify_inputs()
    v = sources()
    rules = registry_rows()
    conv = conversion_rows(v)
    finals = apply_final_quantities(conv)
    dec = owner_decisions(conv)
    docs = documents_required(conv)
    safe = safety_register(rules)
    rdy = readiness(conv)
    cand = candidate_items(v)

    registry = {
        "ARTIFACT": "URBAN_BOQ_RULE_REGISTRY",
        "PURPOSE": "hold what one previous project's bills actually did, at a level that says how far it may be carried",
        "LEVEL_MEANING": {
            "HISTORICAL_PRECEDENT": "observed on a previous project's bill.  Binding on nothing",
            "QORTUBA_PROJECT_RULE": "adopted for Qortuba, because the owner said so or because the item exists nowhere else",
            "URBAN_STANDARD": "company practice.  Needs more than one project, or the owner's declaration",
        },
        "TRADE_ISOLATION_RULE": "a rule belongs to the trade it was read from.  The plaster half deduction says nothing "
                                "about ceramic, blockwork, paint or waterproofing, each of which has its own sheet",
        "ROWS": rules, "COUNT": len(rules),
        "BY_LEVEL": dict(Counter(r["RULE_LEVEL"] for r in rules)),
        "BY_TRADE": dict(Counter(r["TRADE"] for r in rules)),
        "BY_SAFETY": dict(Counter(r["GENERALISATION_SAFETY"] for r in rules)),
        "RULES_AT_URBAN_STANDARD": [r["RULE_ID"] for r in rules if r["RULE_LEVEL"] == "URBAN_STANDARD"],
        "RULES_NEEDING_OWNER_APPROVAL": [r["RULE_ID"] for r in rules if r["OWNER_APPROVAL_REQUIRED"]],
        "APPLIES_TO_QORTUBA_NOW": [r["RULE_ID"] for r in rules if r["APPLIES_TO_QORTUBA"]],
    }

    cmap = {
        "ARTIFACT": "QORTUBA_BOQ_CONVERSION_MAP",
        "PURPOSE": "one row per Qortuba measurement input, saying what stands between it and a final BOQ quantity",
        "THREE_LAYERS": {
            "PHYSICAL_MEASUREMENT": "what the drawing says.  Never edited by a commercial rule",
            "COMMERCIAL_MEASUREMENT_RULE": "what the bill does with it.  Empty until the owner sets it",
            "FINAL_BOQ_QUANTITY": "the payable figure.  Written only when the first two agree and nothing is outstanding",
        },
        "ROWS": conv, "COUNT": len(conv),
        "BY_STATUS": dict(Counter(r["CURRENT_STATUS"] for r in conv)),
        "FINAL_QUANTITIES_WRITTEN": finals,
        "QORTUBA_QUANTITIES_RECOMPUTED": 0,
        "NEW_QUANTITIES_INVENTED": 0,
        "MEASURED_INPUTS_READ": {k: (len(x) if isinstance(x, (list, dict)) else x) for k, x in sorted(v.items())},
    }

    decisions = {
        "ARTIFACT": "QORTUBA_OWNER_DECISIONS_REQUIRED",
        "RULE": "only questions whose answer changes a quantity.  A question the drawing already answers is not asked, "
                "and a missing document is listed as a document, not as a decision",
        "ROWS": dec, "COUNT": len(dec),
        "RANKED_BY": "how many rows carrying a measured value this answer alone makes final",
        "DOCUMENTS_NOT_DECISIONS": docs,
        "HIGHEST_VALUE_THREE": [d["DECISION_ID"] for d in dec[:3]],
    }

    safety = {"ARTIFACT": "QORTUBA_RULE_SAFETY_REGISTER",
              "RULE": "a precedent is promoted by evidence, not by convenience",
              "ROWS": safe, "COUNT": len(safe),
              "PROMOTIONS_MADE_IN_THIS_PHASE": 0}

    ready = {
        "ARTIFACT": "QORTUBA_FINAL_BOQ_READINESS",
        "ROWS": rdy, "COUNT": len(rdy),
        "TRADES_READY_TO_PRICE": [r["TRADE"] for r in rdy if r["TRADE_READY_TO_PRICE"]],
        "TOTAL_BOQ_ITEMS": sum(r["BOQ_ITEMS"] for r in rdy),
        "TOTAL_FINAL_QUANTITIES": sum(r["FINAL_BOQ_QUANTITY_AVAILABLE"] for r in rdy),
        "NO_SINGLE_READINESS_PERCENTAGE": "readiness is per item.  One number across trades would hide which item is "
                                          "priceable and which is not, which is the whole point of this table",
    }

    candidates = {"ARTIFACT": "QORTUBA_CANDIDATE_BOQ_ITEMS", "ROWS": cand, "COUNT": len(cand),
                  "PROMOTED_TO_URBAN_STANDARD": 0}

    written = [write(o["ARTIFACT"], o) for o in (registry, cmap, decisions, safety, ready, candidates)]

    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip().splitlines()
    fr = {"ARTIFACT": "FREEZE_URBAN_BOQ_RULE_REGISTRY",
          "INPUT_FREEZES_VERIFIED": ver,
          "QORTUBA_GEOMETRY_CHANGED": "NONE",
          "QORTUBA_QUANTITIES_RECOMPUTED": 0,
          "NEW_TAKEOFF_PHASES_CREATED": 0,
          "HISTORICAL_QUANTITIES_USED_AS_QORTUBA_INPUTS": 0,
          "RULES_PROMOTED_TO_URBAN_STANDARD": 0,
          "GIT_HEAD_AT_FREEZE": head,
          "WORKING_TREE_AT_FREEZE": {"CLEAN": not dirty, "UNCOMMITTED_PATHS": [l[3:] for l in dirty][:20]},
          "CONTENTS": {n: _sha(OUT / f"{n}.json") for n in written},
          "COUNT": len(written)}
    fr["DIGEST"] = hashlib.sha256(json.dumps({k: x for k, x in fr.items() if k != "DIGEST"},
                                             sort_keys=True, default=str).encode()).hexdigest()
    write("FREEZE_URBAN_BOQ_RULE_REGISTRY", fr)
    return {"REGISTRY": registry, "CONVERSION_MAP": cmap, "DECISIONS": decisions, "SAFETY": safety,
            "READINESS": ready, "CANDIDATES": candidates, "FREEZE": fr, "SOURCES": v}


if __name__ == "__main__":
    o = finish()
    print("FREEZE", o["FREEZE"]["DIGEST"][:16])
    print("rules", o["REGISTRY"]["COUNT"], o["REGISTRY"]["BY_LEVEL"], "| at URBAN_STANDARD:",
          o["REGISTRY"]["RULES_AT_URBAN_STANDARD"] or "none")
    print("safety", o["REGISTRY"]["BY_SAFETY"])
    print("conversion rows", o["CONVERSION_MAP"]["COUNT"], o["CONVERSION_MAP"]["BY_STATUS"])
    print()
    print("FINAL BOQ QUANTITIES:")
    for r in o["CONVERSION_MAP"]["ROWS"]:
        if r["CURRENT_STATUS"] == "FINAL_QUANTITY_AVAILABLE":
            f = r["FINAL_BOQ_QUANTITY"]
            print(f"   {r['MEASUREMENT_INPUT_ID']:8s} {r['BOQ_ITEM']:34s} {f['VALUE']} {f['UNIT']}")
    print()
    print("OWNER DECISIONS, ranked:")
    for d in o["DECISIONS"]["ROWS"]:
        print(f"   {d['DECISION_ID']} [{d['DECISION_KIND']:13s}] makes final now: "
              f"{len(d['ROWS_THIS_ANSWER_ALONE_MAKES_FINAL'])}  affects {d['ROWS_AFFECTED_COUNT']:2d}  {d['QUESTION']}")
    print()
    print("READINESS BY TRADE:")
    for r in o["READINESS"]["ROWS"]:
        print(f"   {r['TRADE']:22s} items {r['BOQ_ITEMS']:2d}  final {r['FINAL_BOQ_QUANTITY_AVAILABLE']}  "
              f"blocked {r['BLOCKED']:2d}  ready={r['TRADE_READY_TO_PRICE']}")
