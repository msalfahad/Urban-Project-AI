"""PA08_QORTUBA_EXTERNAL_RECONCILIATION_01, step 1: transcribe the contractor sources.

This module reads the contractor documents and nothing else.  It does not import the engine, it does not import R3, and it
holds no engine quantity, so a row here cannot have been shaped by what the engine happened to produce.  That independence is
the whole point of transcribing before comparing, and it is asserted by a test.

Arithmetic on the sheet is preserved exactly as written.  Where the printed amount does not follow from the printed quantity
and rate, the row keeps both the original and a RECOMPUTED_VALUE with the difference stated; the source is never rewritten.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_ext01"

# ---------------------------------------------------------------------------- the source documents actually supplied
SOURCES = [
    {"SOURCE_ID": "CONTRACTOR-COMMERCIAL-01",
     "KIND": "CONTRACTOR_COMMERCIAL_BASIS",
     "DESCRIPTION": "photograph of a one-page priced takeoff sheet, letterhead 'شركه المناخ المتحده - للتجارة العامة والمقاولات', "
                    "sub-heading 'القسم الهندسي للقياسات المعمارية', measurer 'كيال معماري ممدوح (ابويوسف) 99517647'",
     "FILE": "/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240/8ef1e970-image.png",
     "SHA256": "7a33d6daa9f7cd0d9c3c80780642fa592c76cddc6550fdd200dd8c9f57d0d9e3",
     "READ_METHOD": "read visually from the photograph; no OCR pass and no second reader",
     "READ_STATUS": "READ_COMPLETE_SINGLE_READER"},
]

MISSING_SOURCES = [
    {"SOURCE_ID": "CONTRACTOR-KIYAL-01",
     "KIND": "CONTRACTOR_MEASUREMENT_BASIS",
     "DESCRIPTION": "the كيال working sheets: the room-by-room dimensions, formulae, gross quantities, deductions and additions "
                    "behind the summary quantities on the priced sheet",
     "STATUS": "NOT_PROVIDED",
     "WHY": "the reconciliation directive names two contractor sources; one document was supplied, the priced summary sheet. "
            "No working sheet accompanied it, and none is present among this session's files.",
     "CONSEQUENCE": "every question this phase must answer from the كيال - which rooms were included, which excluded, what "
                    "deduction rule was applied, what dimensional basis was measured - is SOURCE_REQUIRED, not UNRESOLVED. "
                    "A summary quantity cannot be decomposed into room scope without inventing the decomposition."},
]

# ---------------------------------------------------------------------------- the sheet header
HEADER = {
    "COMPANY_AR": "شركه المناخ المتحده",
    "COMPANY_EN_LITERAL": "United Climate Company",
    "COMPANY_TRADE_LINE_AR": "للتجارة العامه والمقاولات",
    "DEPARTMENT_AR": "القسم الهندسي للقياسات المعمارية",
    "DEPARTMENT_EN_LITERAL": "engineering department for architectural measurement",
    "MEASURER_AR": "كيال معماري ممدوح (ابويوسف)",
    "MEASURER_ROLE": "KIYAL: a trade measurer who takes site quantities for finishing works",
    "MEASURER_PHONE": "99517647",
    "SHEET_TITLE_AR": "كشف حصر مقاسات",
    "SHEET_TITLE_EN_LITERAL": "schedule of measured quantities",
    "SHEET_SUBJECT_AR": "سيراميك",
    "SHEET_SUBJECT_EN_LITERAL": "ceramic",
    "AREA_AR": "قرطبه ق١ ش١ ج٦",
    "AREA_EN_LITERAL": "Qortuba, block 1, street 1, gada (lane) 6",
    "OWNER_AR": "ملك السيد: محمد الفهد",
    "CONTRACTOR_AR": "مقاولات: علي",
    "DATE_AS_WRITTEN": "23.9.2025",
    "STOREY_DESIGNATION": None,
    "STOREY_STATUS": "NOT_STATED_ON_THE_SHEET",
    "STOREY_WHY": "the sheet carries a plot address and no floor, storey or level designation anywhere on it, so whether it "
                  "covers one floor or the whole villa is not established by the document",
}

# ---------------------------------------------------------------------------- the priced rows, right to left as printed
# Columns as printed (Arabic sheet, right to left):
#   البيان | الكميات | خصم نصف | خصم كامل | اجمالى الخصم | الصافى | العدد | سعر الوحدة | المستحق
COMMERCIAL_ROWS = [
    {"ROW_ID": "CC-01", "RAW_ARABIC_TEXT": "ارضيات سيراميك",
     "CANONICAL_INTERPRETATION": "ceramic floor tiling",
     "QUANTITY": 107.76, "UNIT": "M2", "UNIT_WRITTEN_ON_SHEET": None,
     "HALF_DISCOUNT": None, "FULL_DISCOUNT": None, "TOTAL_DISCOUNT": None, "NET": 107.76,
     "COUNT": None, "RATE": 2.750, "AMOUNT": 296.340,
     "OTHER_NOTES": "no unit is printed on this row; an area unit is inferred from the item being floor tiling and from the "
                    "sheet printing 'متر طولي' explicitly on the rows that are linear",
     "READ_STATUS": "READ_CLEAR",
     "AMBIGUITY": "UNIT_INFERRED_NOT_PRINTED"},

    {"ROW_ID": "CC-02", "RAW_ARABIC_TEXT": "نعله مخفي",
     "CANONICAL_INTERPRETATION": "concealed / shadow-gap skirting",
     "QUANTITY": 76.90, "UNIT": "LM", "UNIT_WRITTEN_ON_SHEET": "متر طولي",
     "HALF_DISCOUNT": None, "FULL_DISCOUNT": None, "TOTAL_DISCOUNT": None, "NET": 76.90,
     "COUNT": None, "RATE": 2.750, "AMOUNT": 211.475,
     "OTHER_NOTES": "'متر طولي' is printed once, spanning this row and the profile row beneath it",
     "READ_STATUS": "READ_CLEAR",
     "AMBIGUITY": "NONE"},

    {"ROW_ID": "CC-03", "RAW_ARABIC_TEXT": "بروفيل اعلي نعله",
     "CANONICAL_INTERPRETATION": "profile above the skirting",
     "QUANTITY": 76.90, "UNIT": "LM", "UNIT_WRITTEN_ON_SHEET": "متر طولي",
     "HALF_DISCOUNT": None, "FULL_DISCOUNT": None, "TOTAL_DISCOUNT": None, "NET": 76.90,
     "COUNT": None, "RATE": 2.750, "AMOUNT": 211.475,
     "OTHER_NOTES": "the owner confirms this is the black profile sitting above the skirting; the sheet bills it at exactly "
                    "the same length as the skirting row above, to the centimetre",
     "READ_STATUS": "READ_CLEAR",
     "AMBIGUITY": "NONE"},

    {"ROW_ID": "CC-04", "RAW_ARABIC_TEXT": "حمامات ومطابخ",
     "CANONICAL_INTERPRETATION": "bathrooms and kitchens",
     "QUANTITY": 159.28, "UNIT": "M2", "UNIT_WRITTEN_ON_SHEET": None,
     "HALF_DISCOUNT": 6.00, "FULL_DISCOUNT": None, "TOTAL_DISCOUNT": 6.00, "NET": 153.28,
     "COUNT": None, "RATE": 2.750, "AMOUNT": 421.513,
     "OTHER_NOTES": "the only row carrying a deduction, and it is entered in the 'خصم نصف' (half deduction) column, not the "
                    "'خصم كامل' (full deduction) column.  The row does not say what the 6.00 is deducted for, and it does not "
                    "say whether the 159.28 is wall tiling, floor tiling, or both.",
     "READ_STATUS": "READ_CLEAR",
     "AMBIGUITY": "BASIS_NOT_STATED: wall area, floor area or wall+floor is not distinguishable from the sheet"},

    {"ROW_ID": "CC-05", "RAW_ARABIC_TEXT": "زوايا +جروف",
     "CANONICAL_INTERPRETATION": "corners plus grooves / recessed bands",
     "QUANTITY": 26.35, "UNIT": "LM", "UNIT_WRITTEN_ON_SHEET": "متر طولي",
     "HALF_DISCOUNT": None, "FULL_DISCOUNT": None, "TOTAL_DISCOUNT": None, "NET": 26.35,
     "COUNT": None, "RATE": 2.750, "AMOUNT": 72.463,
     "OTHER_NOTES": "'متر طولي' is printed once, spanning this row and the chamfer row beneath it. 'جروف' is read as grooves / "
                    "recessed bands; it can also be read as ledges, and the sheet does not disambiguate.",
     "READ_STATUS": "READ_CLEAR",
     "AMBIGUITY": "TERM_AMBIGUOUS: جروف reads as groove or as ledge"},

    {"ROW_ID": "CC-06", "RAW_ARABIC_TEXT": "زوايا شطف",
     "CANONICAL_INTERPRETATION": "chamfered / mitred corners",
     "QUANTITY": 12.00, "UNIT": "LM", "UNIT_WRITTEN_ON_SHEET": "متر طولي",
     "HALF_DISCOUNT": None, "FULL_DISCOUNT": None, "TOTAL_DISCOUNT": None, "NET": 12.00,
     "COUNT": None, "RATE": 2.750, "AMOUNT": 33.000,
     "OTHER_NOTES": "a 45 degree mitre where two tiled faces meet at an external corner, measured as a length",
     "READ_STATUS": "READ_CLEAR",
     "AMBIGUITY": "NONE"},

    {"ROW_ID": "CC-07", "RAW_ARABIC_TEXT": "بلاعه",
     "CANONICAL_INTERPRETATION": "floor drain / gully",
     "QUANTITY": None, "UNIT": "NR", "UNIT_WRITTEN_ON_SHEET": None,
     "HALF_DISCOUNT": None, "FULL_DISCOUNT": None, "TOTAL_DISCOUNT": None, "NET": None,
     "COUNT": 7, "RATE": 5.000, "AMOUNT": 35.000,
     "OTHER_NOTES": "counted item: the tiling work around a floor drain, not the drain itself",
     "READ_STATUS": "READ_CLEAR",
     "AMBIGUITY": "NONE"},

    {"ROW_ID": "CC-08", "RAW_ARABIC_TEXT": "حوض قدم",
     "CANONICAL_INTERPRETATION": "foot basin / footbath",
     "QUANTITY": None, "UNIT": "NR", "UNIT_WRITTEN_ON_SHEET": None,
     "HALF_DISCOUNT": None, "FULL_DISCOUNT": None, "TOTAL_DISCOUNT": None, "NET": None,
     "COUNT": 2, "RATE": 15.000, "AMOUNT": 30.000,
     "OTHER_NOTES": "counted item: the tiled foot-washing basin built into the floor",
     "READ_STATUS": "READ_CLEAR",
     "AMBIGUITY": "NONE"},

    {"ROW_ID": "CC-09", "RAW_ARABIC_TEXT": "روشنه",
     "CANONICAL_INTERPRETATION": "roshana: a wall niche / recessed shelf",
     "QUANTITY": None, "UNIT": "NR", "UNIT_WRITTEN_ON_SHEET": None,
     "HALF_DISCOUNT": None, "FULL_DISCOUNT": None, "TOTAL_DISCOUNT": None, "NET": None,
     "COUNT": 4, "RATE": 30.000, "AMOUNT": 120.000,
     "OTHER_NOTES": "counted item: tiling a recessed niche, commonly a shower shelf",
     "READ_STATUS": "READ_CLEAR",
     "AMBIGUITY": "TERM_AMBIGUOUS: روشنه reads as niche or as a small window opening"},

    {"ROW_ID": "CC-10", "RAW_ARABIC_TEXT": "شباك",
     "CANONICAL_INTERPRETATION": "window: the tiled reveal and sill of a window opening",
     "QUANTITY": None, "UNIT": "NR", "UNIT_WRITTEN_ON_SHEET": None,
     "HALF_DISCOUNT": None, "FULL_DISCOUNT": None, "TOTAL_DISCOUNT": None, "NET": None,
     "COUNT": 3, "RATE": 30.000, "AMOUNT": 90.000,
     "OTHER_NOTES": "counted item: the tiling around a window opening inside a tiled room",
     "READ_STATUS": "READ_CLEAR",
     "AMBIGUITY": "NONE"},

    {"ROW_ID": "CC-11", "RAW_ARABIC_TEXT": "سيفون",
     "CANONICAL_INTERPRETATION": "siphon: the concealed WC cistern enclosure",
     "QUANTITY": None, "UNIT": "NR", "UNIT_WRITTEN_ON_SHEET": None,
     "HALF_DISCOUNT": None, "FULL_DISCOUNT": None, "TOTAL_DISCOUNT": None, "NET": None,
     "COUNT": 3, "RATE": 30.000, "AMOUNT": 90.000,
     "OTHER_NOTES": "counted item: tiling the boxed-in concealed cistern behind a wall-hung WC",
     "READ_STATUS": "READ_CLEAR",
     "AMBIGUITY": "NONE"},
]

PRINTED_TOTAL = 1611.266


def arithmetic_check(rows, printed_total):
    """Check the sheet's own arithmetic without touching it.

    Each row keeps what is printed.  Where quantity x rate, or count x rate, does not reproduce the printed amount, the row
    gains a RECOMPUTED_VALUE and a CONTRACTOR_ARITHMETIC_DIFFERENCE.  Nothing is corrected in place.
    """
    out = []
    for r in rows:
        row = dict(r)
        basis = None
        if row["COUNT"] is not None:
            recomputed, basis = row["COUNT"] * row["RATE"], f"{row['COUNT']} x {row['RATE']:.3f}"
        elif row["NET"] is not None:
            recomputed, basis = row["NET"] * row["RATE"], f"{row['NET']} x {row['RATE']:.3f}"
        else:
            recomputed = None
        row["RECOMPUTED_VALUE"] = round(recomputed, 3) if recomputed is not None else None
        row["RECOMPUTED_BASIS"] = basis
        diff = None if recomputed is None else round(row["AMOUNT"] - recomputed, 4)
        row["CONTRACTOR_ARITHMETIC_DIFFERENCE"] = diff
        if diff is None:
            row["ARITHMETIC_STATUS"] = "NOT_CHECKABLE"
        elif abs(diff) < 5e-4:
            row["ARITHMETIC_STATUS"] = "EXACT"
        elif abs(diff) <= 0.02:
            # a printed quantity is rounded to two decimals; the amount was computed from the unrounded quantity
            implied = row["AMOUNT"] / row["RATE"]
            row["ARITHMETIC_STATUS"] = "CONSISTENT_WITH_AN_UNROUNDED_QUANTITY"
            row["IMPLIED_UNROUNDED_NET"] = round(implied, 4)
            row["IMPLIED_UNROUNDED_WHY"] = ("the printed amount divides by the rate to give a quantity that rounds to the "
                                            "printed one, so the sheet computed from an unrounded figure and printed it to "
                                            "two decimals.  The source is kept as printed.")
        else:
            row["ARITHMETIC_STATUS"] = "DIFFERS"
        out.append(row)
    summed = round(sum(r["AMOUNT"] for r in out), 3)
    total = {"PRINTED_TOTAL": printed_total, "SUM_OF_PRINTED_AMOUNTS": summed,
             "DIFFERENCE": round(summed - printed_total, 4),
             "STATUS": "EXACT" if abs(summed - printed_total) < 5e-4 else "DIFFERS"}
    return out, total


def commercial_register():
    rows, total = arithmetic_check(COMMERCIAL_ROWS, PRINTED_TOTAL)
    return {"ARTIFACT": "QORTUBA_CONTRACTOR_COMMERCIAL_REGISTER",
            "BASIS": "CONTRACTOR_COMMERCIAL_BASIS",
            "SOURCES": SOURCES, "HEADER": HEADER,
            "ROWS": rows, "COUNT": len(rows),
            "TOTAL_CHECK": total,
            "CURRENCY": {"VALUE": None, "STATE": "NOT_STATED_ON_THE_SHEET",
                         "WHY": "the sheet prints rates and amounts with no currency symbol or word; the project is in Kuwait, "
                                "which makes KWD the likely unit, but likely is not stated"},
            "RULE": "the sheet is transcribed as printed.  Arithmetic is checked, never corrected in place; a disagreement is "
                    "recorded as RECOMPUTED_VALUE plus CONTRACTOR_ARITHMETIC_DIFFERENCE beside the original.",
            "INDEPENDENCE": "this register was written from the contractor document alone.  No engine quantity was consulted "
                            "while reading it, and this module imports no engine or R3 code."}


def kiyal_register():
    """The كيال register, which has no rows because the كيال was not supplied.

    An empty register is the honest artifact here.  The alternative - decomposing the summary quantities into rooms so the
    register looks populated - would be inventing the measurement working the phase exists to read.
    """
    return {"ARTIFACT": "QORTUBA_CONTRACTOR_KIYAL_REGISTER",
            "BASIS": "CONTRACTOR_MEASUREMENT_BASIS",
            "ROWS": [], "COUNT": 0,
            "STATUS": "SOURCE_NOT_PROVIDED",
            "MISSING_SOURCES": MISSING_SOURCES,
            "WHAT_THE_KIYAL_WOULD_HAVE_ANSWERED": [
                "which rooms are inside the ceramic floor quantity and which are outside it",
                "whether the pantry / kitchen floor is billed in the floor row or in the bathrooms-and-kitchens row",
                "whether the dress room is inside the ceramic scope at all",
                "what the 6.00 half deduction on the bathrooms-and-kitchens row is deducted for",
                "whether the bathrooms-and-kitchens quantity is wall tiling, floor tiling or both, and to what height",
                "which wall stretches carry the skirting and which are excluded for fitted joinery",
                "what dimensional basis was measured on site: clear finish face, wall face, centre line or printed dimension",
                "whether thresholds, door recesses and stairs are in or out",
            ],
            "RULE": "no row may be created in this register from arithmetic on the summary sheet.  A quantity decomposed to "
                    "make it match an engine figure is not a transcription.",
            "INDEPENDENCE": "this module imports no engine or R3 code."}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
    return name


def freeze():
    """Write both transcriptions and freeze them BEFORE any comparison reads them."""
    names = [write("QORTUBA_CONTRACTOR_COMMERCIAL_REGISTER", commercial_register()),
             write("QORTUBA_CONTRACTOR_KIYAL_REGISTER", kiyal_register())]
    contents = {n: _sha(OUT / f"{n}.json") for n in names}
    fr = {"ARTIFACT": "CONTRACTOR_TRANSCRIPTION_FREEZE", "PROJECT_ALIAS": "QORTUBA",
          "SEQUENCE": "frozen before the comparison ran, so no row can have been reinterpreted to improve a match",
          "SOURCES": SOURCES, "MISSING_SOURCES": MISSING_SOURCES,
          "CONTENTS": contents, "COUNT": len(contents),
          "TRANSCRIBER": "single reader, visual, no OCR and no second pass",
          "RULE": "an unclear contractor row is never re-read because another reading agrees better with the engine"}
    fr["DIGEST"] = hashlib.sha256(json.dumps({k: v for k, v in fr.items() if k != "DIGEST"}, sort_keys=True, default=str).encode()).hexdigest()
    write("CONTRACTOR_TRANSCRIPTION_FREEZE", fr)
    return fr


if __name__ == "__main__":
    fr = freeze()
    cr = commercial_register()
    print("CONTRACTOR_TRANSCRIPTION_FREEZE", fr["DIGEST"][:16])
    for r in cr["ROWS"]:
        q = r["NET"] if r["NET"] is not None else r["COUNT"]
        print(f"  {r['ROW_ID']} {r['RAW_ARABIC_TEXT']:16s} {str(q):9s} {r['UNIT']:3s} rate {r['RATE']:.3f} amount {r['AMOUNT']:9.3f} {r['ARITHMETIC_STATUS']}")
    print("  TOTAL", cr["TOTAL_CHECK"])
