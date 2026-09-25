"""The unseal phase: what the historical evidence library actually contains, before any comparison is attempted.

The owner unsealed `الراشد صباح الاحمد.xlsx`.  That file is not in this session.  What is present is a complete
six-book contractor measurement set from one subcontractor for a Sabah Al Ahmad villa - and the villa it measures
is not the one the frozen takeoff measured.

Establishing that is the whole job of this pass.  A trade-by-trade scorecard against the wrong building would
produce percentages that look like a validation and mean nothing, which is the one failure the blind protocol was
built to prevent.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
UP = Path("/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240")

REQUESTED = "الراشد صباح الاحمد.xlsx"

# The upload replaces every non-ASCII character in a filename with an underscore, so an Arabic name cannot be read
# back from it.  The name requested is 18 characters; no uploaded file carries 18 underscores, and no workbook
# contains the string الراشد anywhere in its cells or shared strings.
NAME_SEARCH = {
    "REQUESTED_NAME": REQUESTED,
    "REQUESTED_NAME_LENGTH_CHARS": 18,
    "UPLOADED_UNDERSCORE_COUNTS": {"0449714f-...1.xlsx": 17, "45f2a378-....xlsx": 10,
                                   "6aafd947-....xlsx": 26, "85f545ca-...1.xlsx": 28,
                                   "c52a77de-....xlsx": 7, "5a3370bb-....xls": 5, "777b0536-....xls": 5,
                                   "b324a3e7-....xls": 22, "c495ff6e-....xls": 22},
    "EXACT_MATCH": None,
    "CONTENT_SEARCH_FOR_الراشد": "no hit in any sheet or shared-string table of any of the nine workbooks",
    "CONCLUSION": "the file the owner unsealed is not present in this session",
}

# What IS present: one subcontractor's measurement set, books NO:1 to NO:6, all dated June 2026.
LIBRARY = [
    {"BOOK": "NO:1", "TRADE": "خرسانة مسلحة - reinforced concrete", "FILE": "0449714f-...1.xlsx",
     "SHEETS": ["ورقة1", "القواعد", "الشناجات", "الحوائط + الأعمدة", "كمرات", "بلاطات", "السلم", "حمام السباحة"]},
    {"BOOK": "NO:2", "TRADE": "مبانى الطابوق - blockwork", "FILE": "c52a77de-....xlsx",
     "SHEETS": ["الغلاف", "الكميات"]},
    {"BOOK": "NO:3", "TRADE": "الالمونيوم - aluminium", "FILE": "45f2a378-....xlsx",
     "SHEETS": ["الغلاف", "الكميات"]},
    {"BOOK": "NO:3", "TRADE": "ارضيات وعازل وديكور ودرابزين - floors, insulation, decor, balustrade",
     "FILE": "85f545ca-...1.xlsx", "SHEETS": ["الغلاف", "العازل", "رخام+حوش", "ديكور", "سيراميك"]},
    {"BOOK": "NO:5", "TRADE": "مساح داخلى وخارجى - internal and external plaster", "FILE": "b324a3e7-....xls",
     "SHEETS": ["البيان", "فاتورة كبيرة", "الفاتورة"], "DUPLICATE_OF": "c495ff6e-....xls"},
    {"BOOK": "NO:6", "TRADE": "الصبغ - paint", "FILE": "5a3370bb-....xls",
     "SHEETS": ["البيان", "فاتورة كبيرة", "الفاتورة"], "DUPLICATE_OF": "777b0536-....xls"},
]

COMMON_HEADER = {
    "CONTRACTOR": "شركة التسنيم للتجارة العامة والمقاولات",
    "MEASURED_BY": "رافت فهيم عزيز - محاسب وقياس معمارى",
    "ENGINEER": "م. محمد سامى",
    "AREA_ON_EVERY_COVER": "صباح الأحمد البحرية",
    "DATES": ["2026-06-21", "2026-06-22"],
    "OWNER_NAME_CELL": "ملك السيد: - left blank on every cover",
}

# Seven independent reasons the measured villa is not Al Rashed.  Any one would be enough; together they settle it.
NOT_THE_SAME_BUILDING = [
    {"EVIDENCE": "SWIMMING_POOL",
     "IN_THE_WORKBOOKS": "حمام السباحة throughout: concrete 12.348 m3, pool floor 21 m2, pool walls 19.8 m2, "
                         "external plaster to the wall above the pool, a slab over the pool",
     "IN_THE_AL_RASHED_DRAWINGS": "no pool on any of the three plans",
     "WEIGHT": "DECISIVE"},
    {"EVIDENCE": "DOME",
     "IN_THE_WORKBOOKS": "قبة من الداخل والخارج 181.806 m2, and الدرج+القبة in the concrete book",
     "IN_THE_AL_RASHED_DRAWINGS": "no dome", "WEIGHT": "DECISIVE"},
    {"EVIDENCE": "BLOCKWORK_THICKNESS_PROFILE_IS_INVERTED",
     "IN_THE_WORKBOOKS": "150 mm 617.248 m2 and 200 mm 83.640 m2 - overwhelmingly 150",
     "IN_THE_AL_RASHED_DRAWINGS": "150 mm 190.289 m2 and 200 mm 963.188 m2 - overwhelmingly 200",
     "WEIGHT": "DECISIVE",
     "WHY": "a villa built mostly in 150 mm block is a different building from one built mostly in 200 mm; this "
            "is not a measurement difference"},
    {"EVIDENCE": "ROOM_SCHEDULE",
     "IN_THE_WORKBOOKS": "four master bedrooms, a living room, a roof maid's room, an annex (ملحق)",
     "IN_THE_AL_RASHED_DRAWINGS": "two master bedrooms, three bedrooms, no maid's room, no annex; the first "
                                  "floor is a store, a machine room and the heaters",
     "WEIGHT": "STRONG"},
    {"EVIDENCE": "DISTRICT",
     "IN_THE_WORKBOOKS": "صباح الأحمد البحرية (Marine) on every cover",
     "IN_THE_AL_RASHED_DRAWINGS": "صباح الأحمد السكنية (Residential), block D4, plot 247",
     "WEIGHT": "STRONG"},
    {"EVIDENCE": "ALUMINIUM_SCALE",
     "IN_THE_WORKBOOKS": "windows 116.90 m2, doors 12 m2",
     "IN_THE_AL_RASHED_DRAWINGS": "7 windows, 14.33 m2 - the drawings show seven glazed openings and no more",
     "WEIGHT": "STRONG"},
    {"EVIDENCE": "STOREY_HEIGHTS",
     "IN_THE_WORKBOOKS": "3.60 at the lower level, 3.40 at first floor, 3.50 to the living room, 12.90 to the "
                         "stairwell - a villa measured storey by storey",
     "IN_THE_AL_RASHED_DRAWINGS": "4.00 m floor to floor on all three levels",
     "WEIGHT": "SUPPORTING"},
]

# What the set does show, which is method rather than another project's numbers.
COMMERCIAL_CONVENTIONS_OBSERVED = [
    {"CONVENTION": "OPENINGS_DEDUCTED_AT_HALF",
     "SEEN_AS": "the invoice sheets carry خصم كامل and خصم بالنصف columns, and the plaster book deducts "
                "58.2475 against an opening schedule totalling 116.495 - exactly half",
     "MEANS": "this subcontractor deducts half an opening area, not the whole",
     "OUR_RULE": "we deduct the full opening",
     "CLASS": "COMMERCIAL_RULE_DIFFERENCE", "PROMOTE": "ASK_THE_OWNER"},
    {"CONVENTION": "CORNERS_AND_STOPS_MEASURED_IN_LINEAR_METRES",
     "SEEN_AS": "نهايات م.ط and زوايا م.ط columns beside every plaster line, invoiced at 2 m = 1 m",
     "MEANS": "arrises and stopped ends are a separate paid item at half rate",
     "OUR_RULE": "not measured at all",
     "CLASS": "SCOPE_DIFFERENCE", "PROMOTE": "ASK_THE_OWNER"},
    {"CONVENTION": "TARTOUSHA_UNDER_SKIRTING",
     "SEEN_AS": "طرطشة تحت نعلة م2 as its own invoice line",
     "MEANS": "preparation is measured behind skirting as well as behind wall tiling",
     "OUR_RULE": "preparation measured behind wall porcelain only",
     "CLASS": "SCOPE_DIFFERENCE", "PROMOTE": "ASK_THE_OWNER"},
    {"CONVENTION": "PLASTER_MEASURED_ROOM_BY_ROOM_AS_HEIGHT_X_RUNNING_LENGTH",
     "SEEN_AS": "every row is ارتفاع x طول - a height times a running wall length per room",
     "MEANS": "the same basis this engine uses",
     "OUR_RULE": "the same", "CLASS": "CLOSE_AGREEMENT", "PROMOTE": "NO_CHANGE_NEEDED"},
]

COMPARISON_STATUS = {
    "TRADE_COMPARISON_PERFORMED": False,
    "WHY_NOT": "the only historical evidence in the session measures a different villa.  Comparing a frozen "
               "takeoff of one building against a contractor's measurement of another would produce a "
               "scorecard whose every row is NOT_COMPARABLE while reading like an accuracy score",
    "ALL_TRADES_CLASSIFIED": "NOT_COMPARABLE - DIFFERENT_PROJECT",
    "BLIND_TAKEOFF_UNCHANGED": True,
    "FROZEN_COMMIT": "3e847af", "FROZEN_DIGEST": "ae259eaba3203798",
    "WHAT_IS_NEEDED": "the workbook named الراشد صباح الاحمد.xlsx, which is not among the nine spreadsheets "
                      "uploaded to this session",
}


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return ""


def build():
    rec = {"ARTIFACT": "ALRASHED_HISTORICAL_EVIDENCE_IDENTIFICATION",
           "PHASE": "BLIND_VALIDATION - unseal and identify, before any comparison",
           "REQUESTED_FILE": REQUESTED,
           "NAME_SEARCH": NAME_SEARCH,
           "LIBRARY_PRESENT": LIBRARY,
           "COMMON_HEADER": COMMON_HEADER,
           "NOT_THE_SAME_BUILDING": NOT_THE_SAME_BUILDING,
           "COMMERCIAL_CONVENTIONS_OBSERVED": COMMERCIAL_CONVENTIONS_OBSERVED,
           "COMPARISON_STATUS": COMPARISON_STATUS,
           "RULE": "identity before comparison.  A validation against the wrong building is worse than no "
                   "validation, because it produces numbers that look like evidence",
           "GIT_HEAD": _git("rev-parse", "--short", "HEAD")}
    rec["DIGEST"] = hashlib.sha256(json.dumps(
        {"N": NOT_THE_SAME_BUILDING, "L": LIBRARY}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    return rec


def finish():
    rec = build()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ALRASHED_HISTORICAL_EVIDENCE_IDENTIFICATION.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False), "utf-8")
    return rec


if __name__ == "__main__":
    r = finish()
    print(f"digest {r['DIGEST']}")
    print(f"requested: {r['REQUESTED_FILE']}  -> {r['NAME_SEARCH']['CONCLUSION']}")
    print(f"library present: {len(r['LIBRARY_PRESENT'])} books from {r['COMMON_HEADER']['CONTRACTOR'][:28]}")
    for e in r["NOT_THE_SAME_BUILDING"]:
        print(f"   {e['WEIGHT']:10s} {e['EVIDENCE']}")
    print(f"trade comparison performed: {r['COMPARISON_STATUS']['TRADE_COMPARISON_PERFORMED']}")
