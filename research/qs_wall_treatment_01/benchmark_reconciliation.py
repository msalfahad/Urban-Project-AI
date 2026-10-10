"""BENCHMARK RECONCILIATION (§39-§40) - the human statement against the
frozen estimate, structurally, after the A22 freeze. Nothing is tuned.

The survey identified one workbook (two identical uploads) as the human
wall-treatment benchmark: a contractor's measurement statement of EXECUTED
internal and external plaster works ("كشف حصر مقاسات تنفيذ أعمال: مساح
داخلي وخارجي"). It is a site measurement of what was built, not a drawing
take-off; that makes it the first genuinely independent source this
project has for plaster (EVIDENCE_INDEPENDENCE = INDEPENDENT_SITE_RECORD)
and also means most items differ in basis before any number is compared.

The human derivation is extracted row by row (description, count, height,
width, length, area, group total) and compared against PATH_A's
derivation item by item with the A22 vocabulary. A number the human has
and the estimate has not is reported as the human's number and never
becomes the estimate's total.

    python3 -m research.qs_wall_treatment_01.benchmark_reconciliation
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P
from research.qs_wall_treatment_01 import source_inventory as SI
from research.qs_wall_treatment_01.a22_structural_comparison import VERDICTS

OUT = Path(P.OUT_DIR)
BENCHMARK_FILE = "b324a3e7-______________________.xls"
DUPLICATE_UPLOAD = "c495ff6e-______________________.xls"
STATEMENT_SHEET = "البيــــــــــــان"
INVOICE_SHEET = "الفاتورة"
# columns of the statement sheet (0-based): endings lm, corners lm, -,
# description, count, height, width, length, area, group total
COLS = {"ENDINGS_LM": 0, "CORNERS_LM": 1, "DESCRIPTION": 3, "COUNT": 4,
        "HEIGHT_M": 5, "WIDTH_M": 6, "LENGTH_M": 7, "AREA_M2": 8, "GROUP_TOTAL_M2": 9}


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _num(v):
    try:
        return float(v) if v not in ("", None) else None
    except (TypeError, ValueError):
        return None


def extract(path: Path) -> dict:
    import xlrd
    wb = xlrd.open_workbook(path, on_demand=True)
    ws = wb.sheet_by_name(STATEMENT_SHEET)
    rows = []
    section = None
    for r in range(ws.nrows):
        cells = [ws.cell_value(r, c) for c in range(min(10, ws.ncols))]
        desc = str(cells[COLS["DESCRIPTION"]]).strip()
        if not any(str(c).strip() for c in cells):
            continue
        if desc and all(_num(cells[i]) is None for i in (5, 7, 8)) and not _num(cells[9]):
            if desc in ("المساح الداخلى", "طرطشة الداخلى م2", "سجما خارجى م2", "الفراغات"):
                section = desc
        rec = {"ROW": r + 1, "SECTION": section, "DESCRIPTION": desc,
               "COUNT": _num(cells[4]), "HEIGHT_M": _num(cells[5]),
               "WIDTH_M": _num(cells[6]), "LENGTH_M": _num(cells[7]),
               "AREA_M2": _num(cells[8]), "GROUP_TOTAL_M2": _num(cells[9]),
               "ENDINGS_LM": _num(cells[0]), "CORNERS_LM": _num(cells[1])}
        rows.append(rec)
    inv = wb.sheet_by_name(INVOICE_SHEET)
    invoice = []
    for r in range(inv.nrows):
        cells = [str(inv.cell_value(r, c)).strip() for c in range(inv.ncols)]
        if any(cells):
            invoice.append({"ROW": r + 1, "CELLS": cells})
    return {"STATEMENT_ROWS": rows, "INVOICE_ROWS": invoice}


def _item(iid, subject, human, estimate, verdict, why, independence="INDEPENDENT_SITE_RECORD"):
    assert verdict in VERDICTS
    return {"ITEM_ID": iid, "SUBJECT": subject, "HUMAN_STATEMENT": human,
            "ESTIMATE_PATH_A": estimate, "VERDICT": verdict, "WHY": why,
            "EVIDENCE_INDEPENDENCE": independence,
            "ESTIMATE_CHANGED": False}


def run() -> dict:
    fz = json.loads((OUT / "FREEZE_A22.json").read_text("utf-8"))
    est = json.loads((OUT / "P7757_WALL_TREATMENT_ESTIMATE.json").read_text("utf-8"))
    if _sha(OUT / "P7757_WALL_TREATMENT_ESTIMATE.json") != \
            fz["ARTIFACT_SHA256"]["P7757_WALL_TREATMENT_ESTIMATE.json"]:
        raise SystemExit("estimate differs from the A22 freeze; refusing")
    path = SI.UPLOAD_DIR / BENCHMARK_FILE
    data = extract(path)
    rows = data["STATEMENT_ROWS"]
    by_desc = {}
    for r in rows:
        by_desc.setdefault(r["DESCRIPTION"], []).append(r)

    def first(desc):
        return (by_desc.get(desc) or [None])[0]

    aggr = est["AGGREGATES"]
    sets = {s["PLAN"]["SET_ID"]: s for s in est["SETS"]}
    params = est["PARAMETER_REGISTRY"]
    saloon = sets["GF-SALOON-NORMAL-PLASTER"]

    # human height rule by group, read from the statement rows
    heights = sorted({r["HEIGHT_M"] for r in rows
                      if r["SECTION"] == "المساح الداخلى" and r["HEIGHT_M"]
                      and r["LENGTH_M"] and r["AREA_M2"] and not r["COUNT"]})
    items = []
    items.append(_item(
        "R1", "internal plaster height rule",
        {"HEIGHTS_USED_M": heights,
         "EXAMPLES": [{"DESCRIPTION": r["DESCRIPTION"], "HEIGHT_M": r["HEIGHT_M"],
                       "LENGTH_M": r["LENGTH_M"], "AREA_M2": r["AREA_M2"]}
                      for r in rows if r["DESCRIPTION"] in
                      ("الديوانية", "صالة", "غرفة رئيسية 2", "معيشة", "غرفة خدامة    السطح")]},
        {"NORMAL_INTERNAL_PLASTER_HEIGHT": params["NORMAL_INTERNAL_PLASTER_HEIGHT"]["VALUE"],
         "SOURCE_TYPE": "OWNER_PROJECT_INPUT"},
        "HEIGHT_DIFFERENCE",
        "the human statement plasters ground-floor rooms at 3.60, first-floor rooms at "
        "3.40 (living 3.50) and roof rooms at 3.40; the owner parameter is 3.20 for "
        "normal rooms. Neither is drawing-derived (the drawing gives storey heights "
        "4.50 / 4.20). The parameter is not changed; the owner decides"))
    hall = first("صالة")
    items.append(_item(
        "R2", "SALOON / hall wall length",
        {"DESCRIPTION": "صالة", "LENGTH_LM": hall["LENGTH_M"] if hall else None,
         "HEIGHT_M": hall["HEIGHT_M"] if hall else None,
         "AREA_M2": hall["AREA_M2"] if hall else None,
         "ZONE_MAPPING": "unknown: 'صالة' may be the whole dining/reception/saloon band"},
        {"SET_ID": "GF-SALOON-NORMAL-PLASTER",
         "ESTABLISHED_FACES_LM": saloon["FACE_SET"]["GROSS_BASIS"]["ESTABLISHED_LM"],
         "ESTABLISHED_SUBTOTAL_M2": saloon["SHEET"]["RESULT"]["ESTABLISHED_SUBTOTAL_M2"],
         "COVERAGE": saloon["FACE_SET"]["COVERAGE_STATUS"]},
        "IDENTITY_MAPPING_DIFFERENCE",
        "the human line is one perimeter for a zone whose extent is not stated; the "
        "estimate is two printed faces of the SALOON. No zone mapping is established, "
        "so no number is compared. SCOPE_DIFFERENCE as well: the estimate is a subset"))
    stair = first("حوائط     بيت الدرج")
    items.append(_item(
        "R3", "stair-well walls",
        {"DESCRIPTION": "حوائط بيت الدرج", "LENGTH_LM": stair["LENGTH_M"] if stair else None,
         "HEIGHT_M": stair["HEIGHT_M"] if stair else None,
         "AREA_M2": stair["AREA_M2"] if stair else None,
         "NOTE": "12.90 equals the drawing's +1.00 to +13.90 level difference"},
        {"SETS": ["GF-SERVICE-STAIR-WALLS", "GF-MAIN-STAIR-WALLS", "FF-MAIN-STAIR-WALL"],
         "STAIR_WELL_PLASTER_HEIGHT": params["STAIR_WELL_PLASTER_HEIGHT"]["VALUE"],
         "ESTABLISHED_SUBTOTAL_M2": aggr["BY_TRADE"]["STAIR_WALL_PLASTER"]["ESTABLISHED_SUBTOTAL_M2"]},
        "SCOPE_DIFFERENCE",
        "the human plasters the stair well to the full 12.90 m; the estimate has no "
        "stair-well height and no printed stair-wall lengths, so it reports nothing. "
        "The human's 12.90 is a candidate OWNER input for STAIR_WELL_PLASTER_HEIGHT, "
        "not adopted here"))
    items.append(_item(
        "R4", "opening deduction rule",
        {"OPENINGS_LISTED_M2": first("شباك")["GROUP_TOTAL_M2"] if by_desc.get("شباك") else None,
         "RULE": "openings deducted at HALF (خصم بالنصف): 116.495 m2 listed, 58.2475 deducted",
         "DOOR_SIZE_USED": "1.00 x 2.30", "WINDOW_SIZES_USED": "1.50 x 1.50 and others",
         "DOOR_REVEALS": "شرشوب أبواب 14 x 0.20 x 5.70 = 15.96 m2 (depth 0.20)"},
        {"RULE": "full deduction of the opening area; reveals on their own line",
         "DOOR_HEIGHT": params["DOOR_HEIGHT"]["VALUE"], "DOOR_REVEAL_DEPTH":
         params["DOOR_REVEAL_DEPTH"]["VALUE"], "WINDOW": "1.50 x 1.50 TEMPORARY_DEFAULT"},
        "OPENING_DIFFERENCE",
        "the human deducts half of each opening and adds door reveals at 0.20 depth; "
        "the estimate deducts the whole opening and measures reveals separately. Door "
        "height 2.30 (human) vs 2.20 (temporary default). Rule and defaults are owner "
        "decisions; nothing is changed here"))
    par = first("دروة")
    par_annex = first("دروة سطح الملحق")
    items.append(_item(
        "R5", "roof parapets",
        {"MAIN_ROOF_PARAPET": {"LENGTH_LM": par["LENGTH_M"], "HEIGHT_M": par["HEIGHT_M"],
                               "AREA_M2": par["AREA_M2"]} if par else None,
         "ANNEX_ROOF_PARAPET": {"LENGTH_LM": par_annex["LENGTH_M"],
                                "HEIGHT_M": par_annex["HEIGHT_M"],
                                "AREA_M2": par_annex["AREA_M2"]} if par_annex else None,
         "THE_82_4": "the human's main-parapet figure is kept as the human's figure"},
        {"SE_PARAPET_EXTERNAL": "UNRESOLVED (face height AMBIGUOUS 1.22 / 1.42; run "
                                "length chain-derived 7.10 provisional)",
         "TOWER_PARAPET_1390": "height 0.50 ESTABLISHED (DIM-14), length not printed",
         "CAPPING_PROVISIONAL_M2": aggr["BY_TRADE"]["ROOF_PARAPET_CAPPING"]["PROVISIONAL_SUBTOTAL_M2"]},
        "HUMAN_REVIEW_REQUIRED",
        "the human measures the main roof parapet at 1.70 high (site) where the "
        "drawing shows a composite kerb + lattice + cap and a 1.22-1.42 solid face, and "
        "the annex parapet at 0.70 where the drawing prints 0.50. Site and drawing "
        "differ; neither is adopted over the other here"))
    items.append(_item(
        "R6", "external plaster basis",
        {"FACADES": [{"DESCRIPTION": r["DESCRIPTION"], "HEIGHT_M": r["HEIGHT_M"],
                      "LENGTH_M": r["LENGTH_M"], "AREA_M2": r["AREA_M2"]}
                     for r in rows if r["SECTION"] == "سجما خارجى م2" and r["HEIGHT_M"]
                     and r["LENGTH_M"] and "واجهة" in r["DESCRIPTION"]][:8],
         "BASIS": "whole-facade heights (14.40 / 10.00 / 6.00 / 5.25 / 4.80) x lengths"},
        {"BASIS": "per floor, owner storey heights 4.00 / 4.50 / 4.00 (12.50 total)",
         "ESTABLISHED_SUBTOTAL_M2": aggr["BY_TRADE"]["EXTERNAL_PLASTER"]["ESTABLISHED_SUBTOTAL_M2"],
         "NOTE": "the drawing's overall height 14.40 (DIM-13) equals the human's tallest "
                 "facade height"},
        "BASIS_DIFFERENCE",
        "whole-facade heights against per-storey owner heights, and the owner's storey "
        "sum (12.50) is below both the drawing's overall height and the human's; the "
        "estimate has no established facade face anyway. Owner decision"))
    items.append(_item(
        "R7", "steel corners, endings and profiles",
        {"INTERNAL_CORNERS_ENDINGS_LM": 770.75, "RULE": "2 m = 1 m (halved) -> 385.375",
         "EXTERNAL_LM": 1297.35, "HALVED": 648.675},
        {"PROFILE_ELIGIBLE_LM": "none established (no opening hosted in an established "
                                "face); STEEL_PROFILE_RULE UNKNOWN"},
        "SCOPE_DIFFERENCE", "the human counts corners and endings in lm at half; the "
                            "estimate has no established profile edge and no rule"))
    items.append(_item(
        "R8", "tartusha (tile preparation)",
        {"BATHROOMS_AND_KITCHENS_M2": 433.83, "UNDER_SKIRTING_M2": 70.7125},
        {"TILE_PREP_TARTUSHA": "no wet room in the traced subset; TARTUSHA_HEIGHT UNKNOWN"},
        "SCOPE_DIFFERENCE", "outside the traced subset"))
    items.append(_item(
        "R9", "double-height reception",
        {"DOUBLE_HEIGHT_ITEM": "none: rooms are at 3.60 / 3.40; the stair well at 12.90 is "
                               "the only tall item"},
        {"GF-RECEPTION-DOUBLE-HEIGHT": "VOID above ESTABLISHED (A21); height UNKNOWN; "
                                       "nothing estimated"},
        "TREATMENT_DIFFERENCE",
        "the visual path established a void over the reception; the human statement "
        "shows no double-height room. Whether the stair well line covers it is not "
        "established. Owner decision"))
    totals = {"HUMAN_INTERNAL_GROSS_M2": 1209.385, "HUMAN_INTERNAL_NET_M2": 1151.1375,
              "HUMAN_EXTERNAL_GROSS_M2": 1502.84, "HUMAN_EXTERNAL_NET_M2": 1469.9675,
              "ESTIMATE_ESTABLISHED_SUBTOTAL_M2": aggr["PROJECT"]["ESTABLISHED_SUBTOTAL_M2"],
              "ESTIMATE_COVERAGE": aggr["PROJECT"]["COVERAGE_STATUS"],
              "COMPARABLE": False,
              "WHY": "a whole-house executed-works statement against a four-case traced "
                     "subset with partial coverage: NOT_COMPARABLE at the total level, "
                     "and the estimate's subtotal is not a total"}
    counts = {v: sum(1 for i in items if i["VERDICT"] == v) for v in VERDICTS}
    body = {
        "PHASE_ID": P.PHASE_ID, "ARTIFACT": "BENCHMARK_RECONCILIATION",
        "OPENED_AFTER_FREEZE_A22": fz["FREEZE_DIGEST_SHA256"],
        "BENCHMARK": {
            "FILE": BENCHMARK_FILE, "SHA256": _sha(path),
            "DUPLICATE_UPLOAD_SAME_HASH": DUPLICATE_UPLOAD,
            "ISSUER": "شركة التسنيم للتجارة العامة والمقاولات - القسم الهندسي للقياسات",
            "TYPE": "measurement statement of EXECUTED internal and external plaster "
                    "works (site record), invoice No. 5",
            "AREA": "صباح الأحمد البحرية",
            "PROJECT_IDENTITY_STATUS": "NOT_ESTABLISHED_FROM_FILE: no project number in "
                                       "the workbook; consistent with a sea-view villa "
                                       "with a pool and a dome; the owner confirms",
            "EVIDENCE_INDEPENDENCE": "INDEPENDENT_SITE_RECORD (not the design family)",
        },
        "HUMAN_DERIVATION": data,
        "ITEMS": items, "COUNTS": {k: v for k, v in counts.items() if v},
        "TOTALS": totals,
        "BENCHMARK_LEAK": "NONE: the estimate was frozen (FREEZE_ESTIMATE, FREEZE_A22) "
                          "before this file was opened; no value here entered any "
                          "parameter or geometry",
        "NOTHING_WAS_TUNED": True,
    }
    p = OUT / "BENCHMARK_RECONCILIATION.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"BENCHMARK_RECONCILIATION_SHA256": _sha(p), "COUNTS": body["COUNTS"],
            "TOTALS": totals}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
