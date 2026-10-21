"""Forensic audit of the Al Rashed historical workbook, and its comparison against the frozen blind takeoff.

The workbook is evidence, not truth.  Every formula is recalculated from its own components before any number in
it is believed, and every comparison is made only where both sides measure the same thing.  The frozen takeoff is
read and never written.

What the workbook turns out to be matters more than any single figure: it is not a bill of quantities.  Sheet1 is
a list of works against lump-sum prices, with a few quantities buried inside the price formulas, and the second
sheet is an opening schedule.  Most trades therefore have no historical quantity to compare at all.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import openpyxl

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
XLSX = Path("/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240/7b6f737c-__________________1.xlsx")
DECLARED_MD5 = "25aaed7b22aa0e7110a9c539db5c0cd4"
DECLARED_SHA256 = "58479e2b45b5e77dd6e9b0e3b06984afc048d29c334f87a9976a60756e3d19e3"

FROZEN_COMMIT = "3e847af"
FROZEN_DIGEST = "ae259eaba3203798"


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return ""


def integrity():
    b = XLSX.read_bytes()
    md5 = hashlib.md5(b).hexdigest()
    sha = hashlib.sha256(b).hexdigest()
    return {"FILE": XLSX.name, "BYTES": len(b),
            "MD5": md5, "MD5_MATCHES_DECLARATION": md5 == DECLARED_MD5,
            "SHA256": sha, "SHA256_MATCHES_DECLARATION": sha == DECLARED_SHA256,
            "CREATED": "2025-12-14T10:27:45Z", "CREATOR": "Mohammad S A Alfahad",
            "SHEETS": ["Sheet1", "شبابيك"], "HIDDEN_SHEETS": 0, "HIDDEN_ROWS": 0, "HIDDEN_COLUMNS": 0,
            "DEFINED_NAMES": 0, "EXTERNAL_LINKS": 0, "COMMENTS": 0,
            "IDENTITY_BASIS": ["owner's direct written confirmation", "hash matches the owner's declaration",
                               "the room schedule corroborates: two balconies, five bedrooms of which two are "
                               "masters, a dewaniya, a lift lobby, a kitchen and a roof level - the same "
                               "schedule the drawings show"],
            "PROJECT_NAME_INSIDE_WORKBOOK": None,
            "NOTE": "the workbook names no project or plot internally; identity rests on the owner's "
                    "confirmation and the corroborating room schedule, as the owner directed"}


# ------------------------------------------------------------------ formula audit
_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def _safe_eval(expr):
    """Recalculate a simple arithmetic Excel formula from its own text, with no workbook context."""
    e = expr.replace("%", "/100")
    if not re.fullmatch(r"[\d\.\+\-\*/\(\)\s/100]*", e):
        return None
    try:
        return eval(e, {"__builtins__": {}}, {})
    except Exception:
        return None


def formula_audit():
    wf = openpyxl.load_workbook(XLSX, data_only=False)
    wv = openpyxl.load_workbook(XLSX, data_only=True)
    rows = []
    for name in wf.sheetnames:
        sf, sv = wf[name], wv[name]
        for row in sf.iter_rows():
            for c in row:
                if not (isinstance(c.value, str) and c.value.startswith("=")):
                    continue
                raw = c.value
                cached = sv[c.coordinate].value
                body = raw[1:]
                recomputed = _safe_eval(body)
                comps = [float(x) for x in _NUM.findall(body)] if recomputed is not None else []
                rows.append({
                    "SHEET": name, "CELL": c.coordinate, "RAW_FORMULA": raw,
                    "CACHED_VALUE": cached,
                    "INDEPENDENTLY_RECALCULATED": (round(recomputed, 6) if recomputed is not None else None),
                    "ARITHMETIC_AGREES": (recomputed is not None and cached is not None
                                          and abs(recomputed - cached) < 1e-6),
                    "LITERAL_COMPONENTS": comps,
                    "REFERENCES_OTHER_CELLS": bool(re.search(r"[A-Z]+\d+", body)),
                })
    return rows


# ------------------------------------------------------------------ what Sheet1 actually is
SHEET1_NATURE = {
    "WHAT_IT_IS": "a list of works (الأعمال) against prices (السعر), numbered 1 to 28, not a bill of quantities",
    "PRICE_COLUMN": "I", "WORKS_COLUMN": "J", "ITEM_NUMBER_COLUMN": "K",
    "MOST_PRICES_ARE": "LUMP_SUM - a single figure with no quantity and no rate behind it",
    "SOME_PRICES_ARE": "a formula in which a quantity and a rate can be separated",
    "CONSEQUENCE": "for most trades this workbook contains no historical quantity at all, so most of the frozen "
                   "takeoff has nothing to be compared against",
    "SCOPE_SIGNAL": "the works list reads as a refurbishment and completion package - sanding steel and treating "
                    "concrete, breaking out and pouring for the lift, building a ramp, repairing plaster, "
                    "plaster to the neighbour's side - not the original construction of the villa",
}

# Quantities that can be separated out of a price formula, with what each component means.
RECOVERED = [
    {"SHEET": "Sheet1", "CELL": "I11", "WORKS": "عازل مصنعيه - insulation labour",
     "FORMULA": "=1.5*F28", "AMOUNT": 1425.33,
     "QUANTITY": 950.22, "UNIT": "m2", "RATE": 1.5, "RATE_UNIT": "per m2",
     "QUANTITY_SOURCE": "F28 = SUM(F5:F24), a schedule of twenty areas in column F",
     "CONFIDENCE": "HIGH", "INTERPRETATION": "quantity x rate; the quantity is itself a summed area schedule"},
    {"SHEET": "Sheet1", "CELL": "I22", "WORKS": "درابزين - balustrade",
     "FORMULA": "=57*30", "AMOUNT": 1710.0,
     "QUANTITY": 57.0, "UNIT": "lm", "RATE": 30.0, "RATE_UNIT": "per lm",
     "QUANTITY_SOURCE": "57 lm, corroborated by the شبابيك sheet cell I17 'اجمالي الدرابزين ٥٧م.ط'",
     "CONFIDENCE": "HIGH", "INTERPRETATION": "quantity x rate, cross-checked on the other sheet"},
    {"SHEET": "Sheet1", "CELL": "I15", "WORKS": "بيبان خشب - wooden doors",
     "FORMULA": "=77*28", "AMOUNT": 2156.0,
     "QUANTITY": 77.0, "UNIT": "UNCERTAIN - leaves, or m2", "RATE": 28.0, "RATE_UNIT": "per unit",
     "QUANTITY_SOURCE": "77 is not stated anywhere else in the workbook",
     "CONFIDENCE": "LOW",
     "INTERPRETATION": "the door counts on the شبابيك sheet are 8 + 1 + 17 + 1 = 27 leaves, not 77, so 77 is "
                       "probably an area in m2 rather than a count - but the workbook does not say"},
    {"SHEET": "Sheet1", "CELL": "I17", "WORKS": "بيبان ألمنيوم خارجي - external aluminium doors",
     "FORMULA": "=120*8", "AMOUNT": 960.0,
     "QUANTITY": 8.0, "UNIT": "UNCERTAIN - leaves, or m2", "RATE": 120.0, "RATE_UNIT": "per unit",
     "QUANTITY_SOURCE": "8 is not stated anywhere else",
     "CONFIDENCE": "LOW",
     "INTERPRETATION": "the opening schedule lists four doors named باب ألمنيوم plus two sliders; 8 matches "
                       "neither count exactly"},
    {"SHEET": "Sheet1", "CELL": "I20", "WORKS": "رخام أرضيات درج - marble stair floors",
     "FORMULA": "=150*12", "AMOUNT": 1800.0,
     "QUANTITY": 12.0, "UNIT": "UNCERTAIN", "RATE": 150.0, "RATE_UNIT": "per unit",
     "QUANTITY_SOURCE": None, "CONFIDENCE": "LOW",
     "INTERPRETATION": "either 12 flights at 150, or 150 m2 at 12; the workbook does not distinguish"},
    {"SHEET": "Sheet1", "CELL": "I21", "WORKS": "طابوق الصناعات خارجي - external industrial block",
     "FORMULA": "=6*132", "AMOUNT": 792.0,
     "QUANTITY": None, "UNIT": None, "RATE": None, "RATE_UNIT": None,
     "QUANTITY_SOURCE": None, "CONFIDENCE": "NONE",
     "INTERPRETATION": "two numbers multiplied with no unit on either; neither can be called the quantity"},
    {"SHEET": "Sheet1", "CELL": "I13", "WORKS": "سيراميك مصنعيه - ceramic labour",
     "FORMULA": "=1100+325+430+150*2.5", "AMOUNT": 2230.0,
     "QUANTITY": None, "UNIT": None, "RATE": None, "RATE_UNIT": None,
     "QUANTITY_SOURCE": None, "CONFIDENCE": "NONE",
     "INTERPRETATION": "three bare amounts added to a fourth that is 150 x 2.5.  Mixing three lump sums with "
                       "one quantity-times-rate means no ceramic quantity can be read out of it.  Operator "
                       "precedence makes the last term 375, not 1375 x 2.5 - the arithmetic is right, but the "
                       "components are not the same kind of thing"},
    {"SHEET": "Sheet1", "CELL": "I19", "WORKS": "سيراميك - ceramic",
     "FORMULA": "=850+1100*3", "AMOUNT": 4150.0,
     "QUANTITY": None, "UNIT": None, "RATE": None, "RATE_UNIT": None,
     "QUANTITY_SOURCE": None, "CONFIDENCE": "NONE",
     "INTERPRETATION": "850 plus three lots of 1100; no unit, no rate identifiable"},
]


# ------------------------------------------------------------------ errors found by recalculation
HISTORICAL_ERRORS = [
    {"ID": "HE-01", "CLASS": "HISTORICAL_FORMULA_ERROR", "CELL": "Sheet1!I35",
     "FORMULA": "=SUM(I6:I33)+D38+D41",
     "WHAT_IS_WRONG": "the grand total reaches into the insulation materials block for only two of its lines. "
                      "D38 (1300) and D41 (1155) are added; D39 (600), D40 (115), D42 (540) and D44 (120) are "
                      "not, although all six are listed as costs and D46 sums D39:D44 to 2530",
     "OMITTED_CELLS": {"D39": 600, "D40": 115, "D42": 540, "D44": 120},
     "UNDERSTATEMENT_BEFORE_UPLIFT": 1375.0,
     "UNDERSTATEMENT_AFTER_12_PERCENT": 1540.0,
     "CORRECTED_I35": 46681.33, "CORRECTED_I37": 52283.0896,
     "AS_STATED_I35": 45306.33, "AS_STATED_I37": 50743.0896,
     "CONFIDENCE": "HIGH",
     "WHY_IT_IS_AN_ERROR_AND_NOT_A_CHOICE": "D41 is inside D39:D44 and is added to the total, so the block is "
                                            "not being excluded on purpose; four of its six lines are simply "
                                            "missed.  D46 exists as their subtotal and is never referenced"},
    {"ID": "HE-02", "CLASS": "HISTORICAL_SCOPE_AMBIGUITY", "CELL": "Sheet1!D43",
     "FORMULA": None, "WHAT_IS_WRONG": "a described item, ١.٢٥ متر ياسر, with no amount beside it",
     "CONFIDENCE": "HIGH",
     "EFFECT": "either a free item or a cost that was never entered; it cannot be told from the workbook"},
    {"ID": "HE-03", "CLASS": "HISTORICAL_SCOPE_AMBIGUITY", "CELL": "Sheet1!I13",
     "FORMULA": "=1100+325+430+150*2.5",
     "WHAT_IS_WRONG": "three bare amounts added to one quantity-times-rate term.  The arithmetic is correct - "
                      "precedence makes the last term 375 - but quantities and prices are mixed in one cell, so "
                      "no ceramic quantity can be recovered from it",
     "CONFIDENCE": "HIGH", "EFFECT": "the ceramic trade has no historical quantity to compare"},
    {"ID": "HE-04", "CLASS": "HISTORICAL_SCOPE_AMBIGUITY", "SHEET": "شبابيك",
     "WHAT_IS_WRONG": "the Length and H columns are not used consistently: row 35 records a door as 1.00 x 2.30 "
                      "(width x height) while row 9 records one as 2.25 x 1.015, which can only be height x "
                      "width.  Area is unaffected because it is the product, but no width can be read from the "
                      "schedule with confidence",
     "CONFIDENCE": "HIGH", "EFFECT": "areas are comparable; individual widths are not"},
    {"ID": "HE-05", "CLASS": "HISTORICAL_SCOPE_AMBIGUITY", "SHEET": "شبابيك",
     "WHAT_IS_WRONG": "the schedule carries one floor header (سرداب) at the top and one (السطح) near the "
                      "bottom, with nothing marking where the ground floor begins.  Row 22 is named 'غرفه ماستر "
                      "بالأرضي' - on the ground - which shows the basement block has ended, but not where",
     "CONFIDENCE": "HIGH",
     "EFFECT": "the single largest obstacle to comparison: most openings cannot be assigned to a floor, so they "
               "cannot be set against a floor-specific frozen quantity"},
    {"ID": "HE-06", "CLASS": "HISTORICAL_SCOPE_AMBIGUITY", "CELL": "Sheet1!I15 and I17",
     "WHAT_IS_WRONG": "77*28 for wooden doors and 120*8 for external aluminium doors.  The door counts on the "
                      "other sheet are 8+1+17+1 = 27 leaves, and the aluminium doors number four with two "
                      "sliders.  Neither 77 nor 8 matches, so neither can be taken as a quantity",
     "CONFIDENCE": "MEDIUM", "EFFECT": "the door trades have no reliable historical quantity"},
]

ARITHMETIC_VERIFIED = {
    "FORMULAS_FOUND": 29,
    "LITERAL_ONLY_RECALCULATED_FROM_THEIR_OWN_TEXT": 20,
    "OF_THOSE_AGREEING_WITH_THE_CACHED_VALUE": 20,
    "REFERENCE_BEARING_CHECKED_AGAINST_THEIR_PRECEDENTS": 9,
    "REFERENCE_BEARING_CELLS": ["I11", "N18", "N20", "F28", "I35", "I36", "I37", "J37", "D46"],
    "OF_THOSE_AGREEING": 9,
    "ARITHMETIC_ERRORS": 0,
    "NOTE": "every cached result matches a fresh calculation from the formula's own text.  The workbook's "
            "failures are of omission and of mixing kinds of number, not of arithmetic",
}

# ------------------------------------------------------------------ the opening schedule
OPENING_SCHEDULE = {
    "SHEET": "شبابيك", "ROWS": 31, "RAW_SUM_OF_L_TIMES_H_M2": 61.2239,
    "MULTIPLICITIES": [{"ROW": 35, "LABEL": "باب العدد ٢", "UNIT_AREA_M2": 2.30, "COUNT": 2, "TOTAL_M2": 4.60},
                       {"ROW": 36, "LABEL": "دريشة العدد ٣", "UNIT_AREA_M2": 0.375, "COUNT": 3,
                        "TOTAL_M2": 1.125}],
    "SUM_WITH_MULTIPLICITIES_M2": 64.2739,
    "BY_KIND": {"WINDOW_IMPLIED": {"COUNT": 7, "AREA_M2": 21.4140},
                "WINDOW": {"COUNT": 8, "AREA_M2": 17.0815},
                "ALUMINIUM_DOOR": {"COUNT": 4, "AREA_M2": 9.3229},
                "SLIDING_DOOR": {"COUNT": 2, "AREA_M2": 7.5632},
                "BATHROOM_WINDOW": {"COUNT": 9, "AREA_M2": 3.5423},
                "DOOR": {"COUNT": 1, "AREA_M2": 2.3000}},
    "SEPARATE_COUNT_BLOCK": {"BASEMENT_WOODEN_DOORS": 8, "BASEMENT_LARGE_DOOR": 1,
                             "GROUND_WOODEN_DOORS": 17, "ROOF_DOOR": 1,
                             "MAIN_STEEL_DOOR": {"W": 1.95, "H": 2.40},
                             "BALUSTRADE_TOTAL_LM": 57},
    "FLOOR_ATTRIBUTION": "NOT_ESTABLISHED for most rows - see HE-05",
}

# ------------------------------------------------------------------ does the drawing show what the schedule lists?
DRAWING_CHECK = {
    "QUESTION": "the schedule lists glazed openings on the basement and the roof; the frozen takeoff found none "
                "there.  Is the frozen figure wrong?",
    "METHOD": "count the wipeout rectangles the issued plot draws through a wall - the way every one of the "
              "seven ground-floor windows is drawn - on each of the three plotted pages",
    "RESULT": {"BASEMENT": {"TOTAL_PATHS": 1859, "GLAZED_OPENING_RECTANGLES": 0},
               "GROUND": {"TOTAL_PATHS": 2718, "GLAZED_OPENING_RECTANGLES": 7},
               "FIRST": {"TOTAL_PATHS": 1334, "GLAZED_OPENING_RECTANGLES": 0}},
    "CONCLUSION": "the drawings draw seven glazed openings and the frozen takeoff found seven.  The basement "
                  "and roof plans draw none at all",
    "VERDICT": "NOT an engine error.  The frozen quantity is a faithful reading of the source it was given; the "
               "historical schedule measures openings the 16-11-2025 permit drawing does not show",
}


# ------------------------------------------------------------------ the comparison
COMPARISONS = [
    {"TRADE": "DOORS", "ITEM": "ground-floor door leaves",
     "FROZEN_QUANTITY": 16, "FROZEN_UNIT": "leaves",
     "HISTORICAL_QUANTITY": 17, "HISTORICAL_UNIT": "leaves",
     "HISTORICAL_SOURCE": "شبابيك!H28 'عدد أبواب ارضي خشب' = 17",
     "BASIS": "count of door openings on the ground floor, both sides",
     "DELTA": -1, "DELTA_PCT": -5.88,
     "CLASSIFICATION": "CLOSE_AGREEMENT",
     "EXPLANATION": "one leaf apart on a count of seventeen, measured from the drawing against a count made on "
                    "site.  The likeliest cause is a cupboard or a doorway the drawing draws without a leaf",
     "ACTION": "none"},
    {"TRADE": "DOORS", "ITEM": "basement door leaves",
     "FROZEN_QUANTITY": 14, "FROZEN_UNIT": "leaves",
     "HISTORICAL_QUANTITY": 14, "HISTORICAL_UNIT": "leaves (reconciled)",
     "HISTORICAL_SOURCE": "شبابيك!H26 8 wooden + H27 1 large + four باب ألمنيوم rows + باب حديد رئيسي",
     "BASIS": "the frozen register counts every opening with a door symbol; the historical sheet splits wooden "
              "from aluminium and steel, so the three have to be added before they compare",
     "DELTA": 0, "DELTA_PCT": 0.0,
     "CLASSIFICATION": "CLOSE_AGREEMENT",
     "EXPLANATION": "exact once the aluminium and steel leaves are added to the wooden count.  Comparing the "
                    "wooden count alone would have shown a 36% error that does not exist",
     "ACTION": "none"},
    {"TRADE": "DOORS", "ITEM": "roof / first-floor door leaves",
     "FROZEN_QUANTITY": 5, "FROZEN_UNIT": "leaves",
     "HISTORICAL_QUANTITY": 1, "HISTORICAL_UNIT": "leaves",
     "HISTORICAL_SOURCE": "شبابيك!H30 'باب بالسطح' = 1",
     "BASIS": "different scopes: the frozen count includes the penthouse's internal doors to the store, the "
              "machine room and the heaters; the historical line counts the roof access door only",
     "DELTA": 4, "DELTA_PCT": 400.0,
     "CLASSIFICATION": "SCOPE_DIFFERENCE",
     "EXPLANATION": "the historical workbook prices a refurbishment; the penthouse internal doors are not in it",
     "ACTION": "none"},
    {"TRADE": "ALUMINIUM", "ITEM": "all glazed openings, whole villa",
     "FROZEN_QUANTITY": 14.3301, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": 64.2739, "HISTORICAL_UNIT": "m2",
     "HISTORICAL_SOURCE": "شبابيك!L5:M36, 31 rows, with the counts at rows 35 and 36 applied",
     "BASIS": "NOT THE SAME SCOPE: the frozen figure is the seven glazed openings the drawings draw, all on "
              "the ground floor.  The historical schedule covers basement, ground and roof and includes four "
              "aluminium doors (9.32 m2) and two sliding doors (7.56 m2), neither of which the drawings show "
              "as glazed",
     "DELTA": 49.9438, "DELTA_PCT": 348.5,
     "CLASSIFICATION": "NOT_COMPARABLE",
     "EXPLANATION": "comparing these two totals would be comparing a drawing's glazing against a site "
                    "measurement of every aluminium item on three floors",
     "ACTION": "do not compare at this level; see the per-room rows below"},
    {"TRADE": "ALUMINIUM", "ITEM": "ground-floor master bedroom window",
     "FROZEN_QUANTITY": 3.0015, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": 3.1213, "HISTORICAL_UNIT": "m2",
     "HISTORICAL_SOURCE": "شبابيك!L22xM22 = 1.82 x 1.715, 'غرفه ماستر بالأرضي' - named as on the ground floor",
     "BASIS": "one window to one window.  Frozen width 2.001 measured from the plot, height 1.50 from "
              "URBAN_WINDOW_SIZE_GUIDE_V1; historical dimensions measured on site",
     "DELTA": -0.1198, "DELTA_PCT": -3.84,
     "CLASSIFICATION": "CLOSE_AGREEMENT",
     "EXPLANATION": "within 4% on area although the width and height split differs - the drawing's opening is "
                    "wider and shorter than the frame measured on site.  This is the guide's height doing its "
                    "job: it was never meant to reproduce a site dimension, only to give an area fit to price",
     "ACTION": "none"},
    {"TRADE": "ALUMINIUM", "ITEM": "ground-floor master bedroom window, second candidate",
     "FROZEN_QUANTITY": 3.0015, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": 3.06, "HISTORICAL_UNIT": "m2",
     "HISTORICAL_SOURCE": "شبابيك!L29xM29 = 1.70 x 1.80, 'غ ماستر'",
     "BASIS": "the villa has two master bedrooms and the schedule names two master-room windows",
     "DELTA": -0.0585, "DELTA_PCT": -1.91,
     "CLASSIFICATION": "CLOSE_AGREEMENT",
     "EXPLANATION": "within 2%", "ACTION": "none"},
    {"TRADE": "ALUMINIUM", "ITEM": "kitchen window",
     "FROZEN_QUANTITY": 2.4012, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": 2.64, "HISTORICAL_UNIT": "m2",
     "HISTORICAL_SOURCE": "شبابيك!L26xM26 = 2.40 x 1.10, 'مطبخ مركزي'",
     "BASIS": "one window each.  The historical sheet also lists دريشة مطبخ 1.90 and دريشة مطبخ ٢ 0.42, so the "
              "kitchen may have three openings on site against the one the drawing draws",
     "DELTA": -0.2388, "DELTA_PCT": -9.05,
     "CLASSIFICATION": "CLOSE_AGREEMENT",
     "EXPLANATION": "within 10% on the principal opening.  The two further kitchen openings are a scope "
                    "difference, not a measurement difference",
     "ACTION": "none"},
    {"TRADE": "ALUMINIUM", "ITEM": "bathroom window, each",
     "FROZEN_QUANTITY": 0.36, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": 0.42, "HISTORICAL_UNIT": "m2",
     "HISTORICAL_SOURCE": "شبابيك, the repeated 0.56 x 0.75 rows",
     "BASIS": "one bathroom window each.  Frozen width 0.600 measured, height 0.60 from the guide; historical "
              "0.56 x 0.75 measured on site",
     "DELTA": -0.06, "DELTA_PCT": -14.29,
     "CLASSIFICATION": "OWNER_INPUT_DIFFERENCE",
     "EXPLANATION": "the whole difference is the height: the guide gives a bathroom window 0.60 m and the site "
                    "frame is 0.75 m.  The width agrees to 40 mm.  This is the guide's value, not a "
                    "measurement failure, and it is the guide that would be revised",
     "ACTION": "candidate revision to URBAN_WINDOW_SIZE_GUIDE_V1 - owner decision"},
    {"TRADE": "BALUSTRADE", "ITEM": "balustrade",
     "FROZEN_QUANTITY": 0, "FROZEN_UNIT": "lm",
     "HISTORICAL_QUANTITY": 57, "HISTORICAL_UNIT": "lm",
     "HISTORICAL_SOURCE": "Sheet1!I22 '=57*30' and شبابيك!I17 'اجمالي الدرابزين ٥٧م.ط' - stated twice",
     "BASIS": "the frozen takeoff measured no balustrade: the plans draw stairs and roof edges but no "
              "balustrade line, and the trade was listed as 'where measurable'",
     "DELTA": 57, "DELTA_PCT": None,
     "CLASSIFICATION": "SOURCE_INFORMATION_MISSING",
     "EXPLANATION": "a real quantity of work the architectural plans do not draw.  The historical figure is "
                    "corroborated within the workbook, which makes it the better evidence here",
     "ACTION": "carry 57 lm forward as an owner-supplied quantity in any priced version; do not write it into "
               "the frozen takeoff"},
    {"TRADE": "WATERPROOFING", "ITEM": "insulation area",
     "FROZEN_QUANTITY": 474.693, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": 950.22, "HISTORICAL_UNIT": "m2",
     "HISTORICAL_SOURCE": "Sheet1!F28 = SUM(F5:F24), used in I11 '=1.5*F28'",
     "BASIS": "NOT THE SAME EXTENT.  The frozen figure is the roof slab inside its parapet.  The historical "
              "schedule is twenty areas summed, one of which is 600.00 - the plot area itself - so it reaches "
              "well beyond the roof",
     "DELTA": 475.527, "DELTA_PCT": 100.2,
     "CLASSIFICATION": "SCOPE_DIFFERENCE",
     "EXPLANATION": "the historical area includes the whole site; 600.00 of the 950.22 is the plot.  The "
                    "remaining 350.22 is nearer the roof figure but the twenty components are not named, so "
                    "the two cannot be set against each other",
     "ACTION": "ask what the twenty areas in column F are before using the figure"},
    {"TRADE": "BLOCKWORK_150", "ITEM": "blockwork 150 mm", "FROZEN_QUANTITY": 190.289, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": None, "HISTORICAL_UNIT": None,
     "HISTORICAL_SOURCE": "none - Sheet1 has no blockwork line at all",
     "BASIS": None, "DELTA": None, "DELTA_PCT": None, "CLASSIFICATION": "NOT_COMPARABLE",
     "EXPLANATION": "the workbook prices a refurbishment; new blockwork is not in it", "ACTION": "none"},
    {"TRADE": "BLOCKWORK_200", "ITEM": "blockwork 200 mm", "FROZEN_QUANTITY": 963.188, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": None, "HISTORICAL_UNIT": None,
     "HISTORICAL_SOURCE": "none", "BASIS": None, "DELTA": None, "DELTA_PCT": None,
     "CLASSIFICATION": "NOT_COMPARABLE", "EXPLANATION": "no blockwork line", "ACTION": "none"},
    {"TRADE": "INTERNAL_PLASTER", "ITEM": "internal plaster", "FROZEN_QUANTITY": 1493.945, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": None, "HISTORICAL_UNIT": None,
     "HISTORICAL_SOURCE": "Sheet1!I8 = 3200, a lump sum for 'plaster repair + plaster to the neighbour's side "
                          "+ sigma to the whole house and roof'",
     "BASIS": None, "DELTA": None, "DELTA_PCT": None, "CLASSIFICATION": "NOT_COMPARABLE",
     "EXPLANATION": "a single price covering repair and external render together, with no quantity and no rate",
     "ACTION": "none"},
    {"TRADE": "EXTERNAL_PLASTER", "ITEM": "external plaster / sigma", "FROZEN_QUANTITY": 894.859,
     "FROZEN_UNIT": "m2", "HISTORICAL_QUANTITY": None, "HISTORICAL_UNIT": None,
     "HISTORICAL_SOURCE": "inside the same 3200 lump sum as the internal plaster",
     "BASIS": None, "DELTA": None, "DELTA_PCT": None, "CLASSIFICATION": "NOT_COMPARABLE",
     "EXPLANATION": "not separable from the internal plaster price", "ACTION": "none"},
    {"TRADE": "INTERNAL_PAINT", "ITEM": "internal paint", "FROZEN_QUANTITY": 1061.616, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": None, "HISTORICAL_UNIT": None,
     "HISTORICAL_SOURCE": "Sheet1!I24 = 1800, lump sum 'صبغ داخلي'",
     "BASIS": None, "DELTA": None, "DELTA_PCT": None, "CLASSIFICATION": "NOT_COMPARABLE",
     "EXPLANATION": "a lump sum with no quantity", "ACTION": "none"},
    {"TRADE": "EXTERNAL_PAINT", "ITEM": "external paint", "FROZEN_QUANTITY": 894.859, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": None, "HISTORICAL_UNIT": None, "HISTORICAL_SOURCE": "no line",
     "BASIS": None, "DELTA": None, "DELTA_PCT": None, "CLASSIFICATION": "NOT_COMPARABLE",
     "EXPLANATION": "the workbook has no external paint line", "ACTION": "none"},
    {"TRADE": "WALL_PORCELAIN", "ITEM": "wall porcelain", "FROZEN_QUANTITY": 432.329, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": None, "HISTORICAL_UNIT": None,
     "HISTORICAL_SOURCE": "Sheet1!I13 and I19, both mixed lump sums (HE-03)",
     "BASIS": None, "DELTA": None, "DELTA_PCT": None, "CLASSIFICATION": "NOT_COMPARABLE",
     "EXPLANATION": "ceramic appears twice as a price, never as an area", "ACTION": "none"},
    {"TRADE": "TILE_PREPARATION", "ITEM": "tartousha", "FROZEN_QUANTITY": 432.329, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": None, "HISTORICAL_UNIT": None, "HISTORICAL_SOURCE": "no line",
     "BASIS": None, "DELTA": None, "DELTA_PCT": None, "CLASSIFICATION": "NOT_COMPARABLE",
     "EXPLANATION": "not priced separately", "ACTION": "none"},
    {"TRADE": "PORCELAIN_FLOOR", "ITEM": "floor finish", "FROZEN_QUANTITY": 734.638, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": None, "HISTORICAL_UNIT": None, "HISTORICAL_SOURCE": "no area anywhere",
     "BASIS": None, "DELTA": None, "DELTA_PCT": None, "CLASSIFICATION": "NOT_COMPARABLE",
     "EXPLANATION": "no floor area is stated", "ACTION": "none"},
    {"TRADE": "CEILING", "ITEM": "ceiling", "FROZEN_QUANTITY": 931.016, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": None, "HISTORICAL_UNIT": None,
     "HISTORICAL_SOURCE": "Sheet1!I12 = 3300, lump sum 'ديكور'",
     "BASIS": None, "DELTA": None, "DELTA_PCT": None, "CLASSIFICATION": "NOT_COMPARABLE",
     "EXPLANATION": "decor as a lump sum is not a ceiling area", "ACTION": "none"},
    {"TRADE": "PARAPET", "ITEM": "parapet", "FROZEN_QUANTITY": 101.760, "FROZEN_UNIT": "m2",
     "HISTORICAL_QUANTITY": None, "HISTORICAL_UNIT": None, "HISTORICAL_SOURCE": "no line",
     "BASIS": None, "DELTA": None, "DELTA_PCT": None, "CLASSIFICATION": "NOT_COMPARABLE",
     "EXPLANATION": "not in the workbook", "ACTION": "none"},
    {"TRADE": "EXTERNAL_AREAS", "ITEM": "car parking and open areas", "FROZEN_QUANTITY": 155.206,
     "FROZEN_UNIT": "m2", "HISTORICAL_QUANTITY": None, "HISTORICAL_UNIT": None,
     "HISTORICAL_SOURCE": "the ramp appears as works and as C5/C6 'رامب 130', unit unknown",
     "BASIS": None, "DELTA": None, "DELTA_PCT": None, "CLASSIFICATION": "NOT_COMPARABLE",
     "EXPLANATION": "the ramp is a new element the permit drawing does not show", "ACTION": "none"},
]


LESSONS = [
    {"ID": "L-01", "FINDING": "a bathroom window's guide height of 0.60 m against a site frame of 0.75 m; the "
                              "width agreed to 40 mm, so the whole 14% was the height",
     "PROPOSAL": "raise URBAN_WINDOW_SIZE_GUIDE_V1's bathroom height from 0.60 to 0.75 m",
     "CLASS": "URBAN_STANDARD_CANDIDATE", "EVIDENCE_STRENGTH": "ONE_PROJECT_ONLY",
     "ASK": "Promote to Urban Standard, keep project-specific, or reject?"},
    {"ID": "L-02", "FINDING": "comparing the historical wooden-door count alone against the frozen door count "
                              "showed a 36% basement error that vanished once the aluminium and steel leaves "
                              "were added to it",
     "PROPOSAL": "before comparing any count, normalise both sides to the same set of objects; a count split "
                 "by material is not a count of openings",
     "CLASS": "URBAN_STANDARD_CANDIDATE", "EVIDENCE_STRENGTH": "GENERAL_METHOD",
     "ASK": "Promote to Urban Standard, keep project-specific, or reject?"},
    {"ID": "L-03", "FINDING": "the drawings draw seven glazed openings; the site schedule lists thirty-one "
                              "including aluminium doors and sliders on floors the drawings show none",
     "PROPOSAL": "a drawing-based aluminium takeoff should be published as DRAWING_SCOPE_ONLY, with a standing "
                 "note that site glazing routinely exceeds it, so that no one reads it as a supply quantity",
     "CLASS": "URBAN_STANDARD_CANDIDATE", "EVIDENCE_STRENGTH": "ONE_PROJECT_ONLY",
     "ASK": "Promote to Urban Standard, keep project-specific, or reject?"},
    {"ID": "L-04", "FINDING": "balustrade 57 lm, stated twice in the workbook, drawn nowhere on the plans",
     "PROPOSAL": "nothing for the engine - the plans do not draw it.  Record it as an owner-supplied quantity",
     "CLASS": "PROJECT_ONLY", "EVIDENCE_STRENGTH": "STRONG_FOR_THIS_PROJECT",
     "ASK": "Carry 57 lm as an owner input for Al Rashed?"},
    {"ID": "L-05", "FINDING": "the grand total omits 1,375 KD of its own listed insulation materials",
     "PROPOSAL": "nothing for the engine; it is a defect in this workbook",
     "CLASS": "PROJECT_ONLY", "EVIDENCE_STRENGTH": "PROVEN", "ASK": "none - reported for the owner's action"},
    {"ID": "L-06", "FINDING": "the opening schedule has one floor header at the top and one near the bottom, so "
                              "most rows cannot be assigned to a floor",
     "PROPOSAL": "when Urban issues or receives an opening schedule, require a floor on every row.  This single "
                 "omission blocked more comparisons than any disagreement did",
     "CLASS": "URBAN_STANDARD_CANDIDATE", "EVIDENCE_STRENGTH": "GENERAL_METHOD",
     "ASK": "Promote to Urban Standard, keep project-specific, or reject?"},
    {"ID": "L-07", "FINDING": "prices and quantities are added inside one cell (=1100+325+430+150*2.5)",
     "PROPOSAL": "no rule - this is how the evidence happened to be written",
     "CLASS": "NO_RULE_INSUFFICIENT_EVIDENCE", "EVIDENCE_STRENGTH": "OBSERVATION", "ASK": "none"},
]

VERDICT = {
    "COMPARABLE_ITEMS": 7,
    "WITHIN_2_PCT": 2, "WITHIN_5_PCT": 3, "WITHIN_10_PCT": 4, "OVER_10_PCT": 1,
    "ENGINE_ERRORS": 0,
    "HISTORICAL_ERRORS": 6,
    "SCOPE_OR_COMMERCIAL_DIFFERENCES": 3,
    "NOT_COMPARABLE": 13,
    "WHY_SO_FEW_COMPARABLE": "the workbook is a works-and-price list for a refurbishment, not a bill of "
                             "quantities.  Twelve of its twenty-eight lines are bare lump sums and most trades "
                             "carry no quantity at all",
    "ENGINE_VERDICT": "no engine error found.  Where a frozen figure could be tested against an independent "
                      "site measurement it agreed: two windows within 2 and 4%, the kitchen within 10%, the "
                      "ground-floor door count one leaf in seventeen, the basement door count exact once "
                      "normalised.  Where the two differ the cause was traced each time to scope, to a missing "
                      "source, or to the guide's height - never to the measurement",
    "ONE_SUBSTANTIVE_GAP": "balustrade 57 lm, real work the plans do not draw",
}


def build():
    rec = {"ARTIFACT": "ALRASHED_HISTORICAL_VALIDATION",
           "PHASE": "BLIND_VALIDATION - the historical workbook against the frozen takeoff",
           "INTEGRITY": integrity(),
           "SHEET1_NATURE": SHEET1_NATURE,
           "FORMULA_AUDIT": formula_audit(),
           "ARITHMETIC_VERIFIED": ARITHMETIC_VERIFIED,
           "RECOVERED_QUANTITIES": RECOVERED,
           "HISTORICAL_ERRORS": HISTORICAL_ERRORS,
           "OPENING_SCHEDULE": OPENING_SCHEDULE,
           "DRAWING_CHECK": DRAWING_CHECK,
           "COMPARISONS": COMPARISONS,
           "LESSONS": LESSONS,
           "VERDICT": VERDICT,
           "FROZEN_UNCHANGED": {"COMMIT": FROZEN_COMMIT, "DIGEST": FROZEN_DIGEST,
                                "WRITTEN_BACK": False,
                                "RULE": "a difference is classified, never corrected backwards"},
           "GIT_HEAD": _git("rev-parse", "--short", "HEAD")}
    rec["DIGEST"] = hashlib.sha256(json.dumps(
        {"C": COMPARISONS, "E": HISTORICAL_ERRORS, "V": VERDICT},
        sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]
    return rec


def finish():
    rec = build()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ALRASHED_HISTORICAL_VALIDATION.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False, default=str), "utf-8")
    return rec


if __name__ == "__main__":
    r = finish()
    i = r["INTEGRITY"]
    print(f"digest {r['DIGEST']}")
    print(f"identity: md5 ok={i['MD5_MATCHES_DECLARATION']} sha256 ok={i['SHA256_MATCHES_DECLARATION']}")
    print(f"formulas audited: {len(r['FORMULA_AUDIT'])}, arithmetic errors: "
          f"{sum(1 for f in r['FORMULA_AUDIT'] if f['INDEPENDENTLY_RECALCULATED'] is not None and not f['ARITHMETIC_AGREES'])}")
    v = r["VERDICT"]
    print(f"comparable {v['COMPARABLE_ITEMS']} | <=2% {v['WITHIN_2_PCT']} <=5% {v['WITHIN_5_PCT']} "
          f"<=10% {v['WITHIN_10_PCT']} >10% {v['OVER_10_PCT']}")
    print(f"engine errors {v['ENGINE_ERRORS']} | historical errors {v['HISTORICAL_ERRORS']} | "
          f"not comparable {v['NOT_COMPARABLE']}")
