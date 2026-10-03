"""Owner's corrections to the validation record, and the rule decisions that follow it.

The frozen measurement artifact is not touched.  What changes here is how the historical evidence was described:
CLOSE_AGREEMENT was used too generously, floors were inferred that the workbook never states, and two historical
figures were carried in language that made them sound like measurements.  Each is corrected to what it is.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
CLOSE_AGREEMENT_MAX_PCT = 2.0
REVISION = 2
REVISION_HISTORY = [
    {"REVISION": 1, "WHAT": "the owner's seven corrections and seven rule decisions"},
    {"REVISION": 2, "WHAT": "an external audit found the opening counts mixing two populations in one field.  "
                            "ROW_COUNT, MULTIPLICITY and PHYSICAL_OBJECT_COUNT are now separate fields and the "
                            "31 rows reconcile to 34 objects explicitly: 26 windows, 6 doors, 2 sliding doors",
     "WHAT_DID_NOT_CHANGE": "no classification, no rule decision and no restated figure moved"},
]


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return ""


OWNER_POSITION = {
    "THE_HISTORICAL_WORKBOOK_IS": "historical evidence, a source of calculation errors, and a list of items that "
                                  "may need verifying on site",
    "IT_IS_NOT": ["a quantity takeoff", "a calibration target", "a source of quantities for the new BOQ"],
    "WHY": "most of its prices are lump sums (مقطوعية) entered for budgeting or for pricing a contractor, not "
           "as measured architectural quantities",
    "FROZEN_COMMIT": "3e847af", "FROZEN_DIGEST": "ae259eaba3203798",
    "FROZEN_MAY_BE_AMENDED": False, "VALIDATION_RECORD_MAY_BE_AMENDED": True,
}

# ------------------------------------------------------------------ 1. CLOSE_AGREEMENT means 2% or better
RECLASSIFIED = [
    {"ITEM": "basement door leaves", "DELTA_PCT": 0.0,
     "WAS": "CLOSE_AGREEMENT", "NOW": "CLOSE_AGREEMENT", "CHANGED": False,
     "WHY": "exact once both sides count the same objects; inside the 2% band"},
    {"ITEM": "ground-floor master bedroom window, second candidate", "DELTA_PCT": -1.91,
     "WAS": "CLOSE_AGREEMENT", "NOW": "CLOSE_AGREEMENT", "CHANGED": False,
     "WHY": "inside the 2% band"},
    {"ITEM": "ground-floor master bedroom window", "DELTA_PCT": -3.84,
     "WAS": "CLOSE_AGREEMENT", "NOW": "OWNER_INPUT_DIFFERENCE", "CHANGED": True,
     "WHY": "outside 2%.  The cause is the split, not the measurement: the drawing's opening is 2.001 wide and "
            "the guide gives 1.50 high, while the site frame is 1.82 x 1.715.  The height is an owner-approved "
            "guide value, so the difference belongs to that input"},
    {"ITEM": "ground-floor door leaves", "DELTA_PCT": -5.88,
     "WAS": "CLOSE_AGREEMENT", "NOW": "SOURCE_INFORMATION_MISSING", "CHANGED": True,
     "WHY": "outside 2%.  One leaf in seventeen, and the drawing does not say which opening the site counted "
            "that the plan does not draw with a leaf.  Nothing in the sources resolves it"},
    {"ITEM": "kitchen window", "DELTA_PCT": -9.05,
     "WAS": "CLOSE_AGREEMENT", "NOW": "SCOPE_DIFFERENCE", "CHANGED": True,
     "WHY": "outside 2%.  The site schedule carries three kitchen openings (2.40x1.10, 1.00x1.90, 0.56x0.75) "
            "against the one the drawing draws, so the two are not measuring the same set"},
    {"ITEM": "bathroom window, each", "DELTA_PCT": -14.29,
     "WAS": "OWNER_INPUT_DIFFERENCE", "NOW": "OWNER_INPUT_DIFFERENCE", "CHANGED": False,
     "WHY": "already classified by cause; the height is the guide's 0.60 against a 0.75 site frame"},
]

# ------------------------------------------------------------------ 2. floors are not inferred
FLOOR_ATTRIBUTION_RULE = {
    "RULE": "an opening is assigned to a floor only on proof",
    "PROOF_IS": ["an explicit floor label on the row", "an unambiguous room match",
                 "drawing geometry", "owner confirmation"],
    "OTHERWISE": {"FLOOR": "UNKNOWN", "STATUS": "HISTORICAL_LOCATION_UNCONFIRMED"},
    "APPLIED_TO": "شبابيك rows L5:M36",
    "RESULT": {"PROVEN_GROUND": 2, "PROVEN_ROOF": 2, "UNKNOWN": 27},
    "PROVEN_ROWS": [
        {"ROW": 22, "LABEL": "غرفه ماستر بالأرضي", "FLOOR": "GROUND",
         "PROOF": "the row says بالأرضي - on the ground floor"},
        {"ROW": 29, "LABEL": "غ ماستر", "FLOOR": "GROUND",
         "PROOF": "the villa's only master bedrooms are on the ground floor in the drawings, and row 22 already "
                  "names one of the two as being there"},
        {"ROW": 35, "LABEL": "باب العدد ٢", "FLOOR": "ROOF", "PROOF": "under the السطح header at N34"},
        {"ROW": 36, "LABEL": "دريشة العدد ٣", "FLOOR": "ROOF", "PROOF": "under the السطح header at N34"},
    ],
    "WITHDRAWN": "the earlier reading that rows 5-21 were basement.  The sheet carries one header at the top and "
                 "nothing marking where the ground floor begins, so the boundary was inferred, not proven",
}

# ------------------------------------------------------------------ 3. counts, kept apart
# A row is not an object.  The schedule has 31 rows; two of those rows carry a count in their own text, so the
# same schedule describes 34 physical objects.  Each number lives in its own field and they are never summed
# across populations - which is what US-20 was promoted to prevent.
HISTORICAL_COUNTS = {
    "POPULATION": "the L/M opening schedule on the شبابيك sheet, rows 5 to 36",
    "FIELD_RULE": "ROW_COUNT, MULTIPLICITY and PHYSICAL_OBJECT_COUNT are three separate fields.  No field "
                  "holds a row count and an object count at the same time",
    "SCHEDULE_ROW_COUNT": {"WINDOWS": 24, "DOORS": 5, "SLIDING_DOORS": 2, "TOTAL": 31},
    "WINDOW_ROW_NOTE": "8 rows named دريشة + 7 rows named only by their room + 9 bathroom window rows = 24",
    "MULTIPLICITY": [
        {"ROW": 36, "LABEL": "دريشة العدد ٣", "KIND": "WINDOW",
         "ROW_COUNT": 1, "MULTIPLICITY": 3, "PHYSICAL_OBJECT_COUNT": 3,
         "EVIDENCE": "the row's own text states a count of three"},
        {"ROW": 35, "LABEL": "باب العدد ٢", "KIND": "DOOR",
         "ROW_COUNT": 1, "MULTIPLICITY": 2, "PHYSICAL_OBJECT_COUNT": 2,
         "EVIDENCE": "the row's own text states a count of two"},
    ],
    "PHYSICAL_OBJECT_COUNT": {"WINDOWS": 26, "DOORS": 6, "SLIDING_DOORS": 2, "TOTAL": 34},
    "RECONCILIATION": {
        "WINDOWS": "24 rows + 2 extra objects from row 36 (1 row -> 3 objects) = 26 objects",
        "DOORS": "5 rows + 1 extra object from row 35 (1 row -> 2 objects) = 6 objects",
        "SLIDING_DOORS": "2 rows -> 2 objects",
        "TOTAL": "31 rows -> 34 objects (26 + 6 + 2)",
    },
    "SEPARATE_LEAF_COUNT_BLOCK": {
        "WHAT_IT_COUNTS": "door LEAVES by material, in a different block on the same sheet",
        "BASEMENT_WOODEN": 8, "BASEMENT_LARGE": 1, "GROUND_WOODEN": 17, "ROOF": 1, "MAIN_STEEL": 1,
        "TOTAL_LEAVES": 28,
        "IS_THE_SAME_POPULATION_AS_THE_L_M_SCHEDULE": False,
        "NOTE": "a leaf is not an opening and this block is not the L/M schedule; the two must never be added "
                "together, and neither may be compared against the other without normalising first (US-20)",
    },
}

# ------------------------------------------------------------------ 4 and 5. two figures renamed to what they are
RESTATED = [
    {"FIGURE": 950.22, "UNIT": "m2", "WAS_CALLED": "historical waterproofing quantity",
     "NOW": "HISTORICAL_COMMERCIAL_BASIS",
     "SOURCE": "Sheet1!F28 = SUM(F5:F24), consumed by I11 '=1.5*F28'",
     "WHY": "a summed schedule of twenty unnamed areas used to price insulation labour.  One component is "
            "600.00 - the plot area - so it is not a physical membrane area and was never verified as one",
     "MAY_BE_COMPARED_AGAINST_A_MEASURED_AREA": False},
    {"FIGURE": 57.0, "UNIT": "lm", "WAS_CALLED": "historical balustrade quantity",
     "NOW": "FIELD_VERIFICATION_REQUIRED",
     "SOURCE": "Sheet1!I22 '=57*30' and شبابيك!I17",
     "WHY": "stated twice in the workbook and drawn nowhere on the permit drawings.  It is a historical claim "
            "about work that may exist on site",
     "ADDED_TO_FROZEN_QUANTITY": False,
     "ACTION": "verify on site before it enters any priced document"},
]

# ------------------------------------------------------------------ the owner's rule decisions
RULE_DECISIONS = [
    {"ID": "L-01", "SUBJECT": "bathroom window height 0.75 m from the site frame",
     "DECISION": "REJECT", "CLASS": "HISTORICAL_PROJECT_EVIDENCE_ONLY",
     "EFFECT": "URBAN_WINDOW_SIZE_GUIDE_V1 keeps 0.60 m.  The historical workbook is not reliable enough to "
               "override the approved guide or the project drawings"},
    {"ID": "L-02", "SUBJECT": "normalise both sides to identical objects before comparing",
     "DECISION": "PROMOTE", "RULE_ID": "US-20", "CLASS": "URBAN_STANDARD",
     "STATEMENT": "before any count or quantity is compared, both sides are reduced to the same population of "
                  "objects.  A count split by material, trade or supplier is not a count of openings",
     "EVIDENCE": "the basement door count showed a 36% error that fell to zero once the aluminium and steel "
                 "leaves were added to the wooden ones"},
    {"ID": "L-03", "SUBJECT": "architectural aluminium is drawing scope only",
     "DECISION": "PROMOTE", "RULE_ID": "US-21", "CLASS": "URBAN_STANDARD",
     "STATEMENT": "an aluminium quantity taken from architectural drawings is published as DRAWING_SCOPE_ONLY.  "
                  "Site glazing routinely exceeds it and it is never a supply quantity",
     "EVIDENCE": "the drawings draw 7 glazed openings; the site schedule lists 34 objects"},
    {"ID": "L-04", "SUBJECT": "57 lm balustrade",
     "DECISION": "PROJECT_ONLY", "CLASS": "HISTORICAL_CLAIM",
     "STATUS": "FIELD_VERIFICATION_REQUIRED", "EFFECT": "not added to any measured quantity"},
    {"ID": "L-05", "SUBJECT": "the 1,375 KD omission in the grand total",
     "DECISION": "HISTORICAL_WORKBOOK_ERROR_ONLY", "CLASS": "NO_RULE",
     "EFFECT": "reported to the owner; nothing in the engine changes"},
    {"ID": "L-06", "SUBJECT": "a floor on every opening-schedule row",
     "DECISION": "PROMOTE", "RULE_ID": "US-22", "CLASS": "URBAN_STANDARD",
     "STATEMENT": "every row of an opening schedule Urban generates carries a FLOOR.  Where the floor is not "
                  "established the value is UNKNOWN and the row is marked, never left blank or inferred",
     "EVIDENCE": "one missing header blocked 27 of 31 rows from being compared"},
    {"ID": "L-07", "SUBJECT": "quantity, unit, rate and amount are separate fields",
     "DECISION": "PROMOTE", "RULE_ID": "DS-01", "CLASS": "DATA_SCHEMA_RULE", "PERMANENT": True,
     "STATEMENT": "MEASURED_QUANTITY, MEASURED_UNIT, WASTE_PERCENT, PROCUREMENT_QUANTITY, UNIT_RATE and AMOUNT "
                  "occupy separate database fields and separate spreadsheet columns.  No cell or field ever "
                  "holds a quantity and a price together",
     "EVIDENCE": "=1100+325+430+150*2.5 - three lump sums added to one quantity-times-rate, from which no "
                 "ceramic quantity can be recovered"},
]

PROMOTED_RULE_IDS = ["US-20", "US-21", "US-22", "DS-01"]

CORRECTED_VERDICT = {
    "COMPARABLE_ITEMS": 7,
    "CLOSE_AGREEMENT_AT_2_PCT_OR_BETTER": 2,
    "OWNER_INPUT_DIFFERENCE": 2,
    "SOURCE_INFORMATION_MISSING": 2,
    "SCOPE_DIFFERENCE": 2,
    "NOT_COMPARABLE": 13,
    "ENGINE_ERRORS": 0,
    "HISTORICAL_ERRORS": 6,
    "NOTE": "the counts sum to more than seven because the balustrade and roof-door rows were already classified "
            "SOURCE_INFORMATION_MISSING and SCOPE_DIFFERENCE before this amendment",
    "WHAT_CHANGED": "three rows left CLOSE_AGREEMENT.  Only two differences in this validation are inside 2%",
}


def build():
    rec = {"ARTIFACT": "ALRASHED_VALIDATION_AMENDMENT_01",
           "REVISION": REVISION,
           "AMENDS": "ALRASHED_HISTORICAL_VALIDATION",
           "REVISION_HISTORY": REVISION_HISTORY,
           "OWNER_POSITION": OWNER_POSITION,
           "CLOSE_AGREEMENT_MAX_PCT": CLOSE_AGREEMENT_MAX_PCT,
           "RECLASSIFIED": RECLASSIFIED,
           "FLOOR_ATTRIBUTION_RULE": FLOOR_ATTRIBUTION_RULE,
           "HISTORICAL_COUNTS": HISTORICAL_COUNTS,
           "RESTATED": RESTATED,
           "RULE_DECISIONS": RULE_DECISIONS,
           "PROMOTED_RULE_IDS": PROMOTED_RULE_IDS,
           "CORRECTED_VERDICT": CORRECTED_VERDICT,
           "FROZEN_UNCHANGED": {"COMMIT": "3e847af", "DIGEST": "ae259eaba3203798", "TOUCHED": False},
           "GIT_HEAD": _git("rev-parse", "--short", "HEAD")}
    rec["DIGEST"] = hashlib.sha256(json.dumps(
        {"R": RECLASSIFIED, "D": RULE_DECISIONS, "S": RESTATED},
        sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]
    return rec


def finish():
    rec = build()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ALRASHED_VALIDATION_AMENDMENT_01.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False), "utf-8")
    return rec


if __name__ == "__main__":
    r = finish()
    print("digest", r["DIGEST"])
    for x in r["RECLASSIFIED"]:
        if x["CHANGED"]:
            print(f"  {x['DELTA_PCT']:+6.2f}%  {x['WAS']} -> {x['NOW']}  ({x['ITEM']})")
    print("  promoted:", r["PROMOTED_RULE_IDS"])
    print("  verdict:", r["CORRECTED_VERDICT"]["CLOSE_AGREEMENT_AT_2_PCT_OR_BETTER"], "at <=2%")
