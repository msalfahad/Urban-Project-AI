"""DUAL BASIS - ENGINEERING_QS beside CONTRACTOR_SITE_MEASUREMENT (§1-§10).

Builds, on the same frozen face sets:

  * the CONTRACTOR RULEBOOK, read from the site record as SITE_RECORD /
    CONTRACTOR_MEASUREMENT_RULE entries (never geometry)
  * HEIGHT_BASIS records: ENGINEERING_HEIGHT, CONTRACTOR_HEIGHT,
    DRAWING_STOREY_HEIGHT, SOURCE, SCOPE, MEASUREMENT_BASIS - no averaging
  * both quantities per face set, the delta, and its decomposition by
    driver (HEIGHT, OPENING_DEDUCTION, DOOR_DIMENSION, REVEALS, ...)
  * layered items with every §10 layer present
  * the stair-well continuity check (§7), parapet and facade parallel
    records (§8, §9), the benchmark identity evidence table (§11)

    python3 -m research.qs_wall_treatment_01.dual_basis
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine import contractor_measurement as C
from engine import quantity_layers as Q
from engine import wall_treatment_engine as E
from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)
SITE_RECORD = "contractor statement of executed plaster works, invoice No. 5 " \
              "(BENCHMARK_RECONCILIATION.json / BENCHMARK_ACCESS_LOG.json)"


def _r(rid, value, unit, scope, src="SITE_RECORD", note=None):
    return C.rule(rid, value, unit, source_type=src, reference=SITE_RECORD, scope=scope, note=note)


def contractor_rulebook() -> dict:
    R = "CONTRACTOR_MEASUREMENT_RULE"
    rb = {
        "HEIGHT_GROUND": _r("HEIGHT_GROUND", 3.60, "m", "ground-floor rooms as the record used"),
        "HEIGHT_FIRST": _r("HEIGHT_FIRST", 3.40, "m", "first-floor rooms as the record used"),
        "HEIGHT_LIVING": _r("HEIGHT_LIVING", 3.50, "m", "the living area line"),
        "HEIGHT_ROOF_ROOM": _r("HEIGHT_ROOF_ROOM", 3.40, "m", "roof maid room / corridor"),
        "HEIGHT_STAIRWELL": _r("HEIGHT_STAIRWELL", 12.90, "m", "stair-well walls, one line",
                               note="equals the drawing's +1.00 to +13.90; not adopted as "
                                    "engineering height (§7)"),
        "OPENING_DEDUCTION_RULE": _r("OPENING_DEDUCTION_RULE", "HALF_OPENING_DEDUCTION", None,
                                     "all listed openings", src=R,
                                     note="116.495 m2 listed, 58.2475 deducted"),
        "DOOR_WIDTH": _r("DOOR_WIDTH", 1.00, "m", "doors as listed"),
        "DOOR_HEIGHT": _r("DOOR_HEIGHT", 2.30, "m", "doors as listed"),
        "WINDOW_WIDTH": _r("WINDOW_WIDTH", 1.50, "m", "the 1.5 x 1.5 windows; other sizes listed"),
        "WINDOW_HEIGHT": _r("WINDOW_HEIGHT", 1.50, "m", "the 1.5 x 1.5 windows; other sizes listed"),
        "DOOR_REVEAL_DEPTH": _r("DOOR_REVEAL_DEPTH", 0.20, "m", "door reveals (شرشوب أبواب)"),
        "DOOR_REVEAL_GIRTH": _r("DOOR_REVEAL_GIRTH", 5.70, "m", "door reveals, girth per door"),
        "EXTERNAL_REVEAL_DEPTH": _r("EXTERNAL_REVEAL_DEPTH", 0.28, "m", "external reveals (شرشوب م2)"),
        "CORNER_ENDING_RULE": _r("CORNER_ENDING_RULE", "2m=1m", None, "corners and endings in lm",
                                 src=R, note="770.75 lm internal -> 385.375; 1297.35 external -> 648.675"),
        "PARAPET_MAIN_HEIGHT": _r("PARAPET_MAIN_HEIGHT", 1.70, "m", "main roof parapet (دروة)"),
        "PARAPET_ANNEX_HEIGHT": _r("PARAPET_ANNEX_HEIGHT", 0.70, "m", "annex roof parapets"),
        "FACADE_BASIS": _r("FACADE_BASIS", "WHOLE_FACADE_HEIGHT", None,
                           "external plaster measured as whole facades", src=R,
                           note="heights 14.40 / 10.00 / 6.00 / 5.25 / 4.80 x lengths"),
        "TARTUSHA_BASIS": _r("TARTUSHA_BASIS", "BATHROOMS_AND_KITCHENS_M2", None,
                             "433.83 m2 plus 70.7125 under skirting", src=R),
    }
    return rb


def height_basis_records() -> list:
    def rec(item, eng, eng_src, con, con_src, drw, drw_src, scope):
        return {"ITEM": item, "ENGINEERING_HEIGHT": eng, "ENGINEERING_SOURCE": eng_src,
                "CONTRACTOR_HEIGHT": con, "CONTRACTOR_SOURCE": con_src,
                "DRAWING_STOREY_HEIGHT": drw, "DRAWING_SOURCE": drw_src, "SCOPE": scope,
                "MEASUREMENT_BASIS": {"ENGINEERING": "ENGINEERING_QS",
                                      "CONTRACTOR": "CONTRACTOR_SITE_MEASUREMENT"},
                "CLASS": "MEASUREMENT_BASIS_DIFFERENCE", "AVERAGED": False}
    return [
        rec("normal internal plaster, ground floor", 3.20, "OWNER_PROJECT_INPUT", 3.60,
            "SITE_RECORD", 4.50, "DIM-16 / LVL +1.00 -> +5.50 (CASE-1)", "normal rooms"),
        rec("normal internal plaster, first floor", 3.20, "OWNER_PROJECT_INPUT", 3.40,
            "SITE_RECORD", 4.20, "DIM-17 +5.50 -> +9.70", "normal rooms"),
        rec("living area, first floor", 3.20, "OWNER_PROJECT_INPUT", 3.50, "SITE_RECORD",
            4.20, "DIM-17", "one line in the record"),
        rec("roof room", 3.20, "OWNER_PROJECT_INPUT", 3.40, "SITE_RECORD", 4.20,
            "DIM-09 (CASE-6) +9.70 -> +13.90", "roof maid room / corridor"),
        rec("stair well", None, "STAIR_WELL_PLASTER_HEIGHT UNKNOWN; component-based",
            12.90, "SITE_RECORD", 12.90, "level chain +1.00 -> +13.90 (numerically equal)",
            "stair-well walls; continuity NOT established, see STAIRWELL_CONTINUITY"),
        rec("SE terrace parapet external solid face", "1.22 / 1.42 AMBIGUOUS",
            "DIM-21, DIM-20, base line +9.88 (CASE-6)", 1.70, "SITE_RECORD (main parapet)",
            None, "no storey height applies", "what the 1.70 includes is UNRESOLVED"),
        rec("tower parapet +13.90", 0.50, "DIM-14 / DIM-08 / DIM-10 / DIM-11", 0.70,
            "SITE_RECORD (annex parapets)", None, "-", "site vs drawing"),
        rec("external plaster, ground", 4.00, "OWNER_PROJECT_INPUT", "whole facade 14.40 / 10.00 / 6.00 ...",
            "SITE_RECORD", 4.50, "DIM-16", "per floor vs whole facade"),
        rec("external plaster, first", 4.50, "OWNER_PROJECT_INPUT", "(inside the whole-facade height)",
            "SITE_RECORD", 4.20, "DIM-17", "per floor vs whole facade"),
        rec("external plaster, second / roof room", 4.00, "OWNER_PROJECT_INPUT",
            "(inside the whole-facade height)", "SITE_RECORD", 4.20, "DIM-09", "per floor vs whole facade"),
    ]


def stairwell_continuity(reg: dict) -> dict:
    """§7: is one continuous plasterable wall traced across +1.00 -> +13.90?"""
    tr = [t for t in reg["TRACES"] if t["CASE_ID"] == "CASE-4-STAIR"]
    walls = [t for t in tr if t["EFFECTIVE_CLAIM_TYPE"] == "WALL_SEGMENT"]
    sections = [t for t in tr if t["SHEET_ID"] in ("SECTION_A_A", "SECTION_B_B",
                                                   "NORTH_EAST_ELEVATION")]
    interruptions = [t["TRACE_ID"] + " " + t["SHEET_ID"] for t in sections
                     if t["EFFECTIVE_CLAIM_TYPE"] in ("STAIR",) ]
    landing_dim = [t["TRACE_ID"] for t in tr if t["TRACE_ID"] == "DIM-18"]
    return {
        "QUESTION": "does one continuous plasterable wall span +1.00 -> +13.90?",
        "WALL_TRACES": [{"ID": t["TRACE_ID"], "SHEET": t["SHEET_ID"],
                         "DIMENSION_STATUS": t.get("DIMENSION_STATUS")} for t in walls],
        "WALL_TRACES_ON_SECTIONS_SPANNING_THE_RANGE": [],
        "INTERRUPTIONS_TRACED_IN_THE_WELL": interruptions,
        "LANDING_CLEAR_HEIGHT_DIMENSION": landing_dim,
        "CHECKS": {
            "STAIR_WALL_CONTINUITY": "NOT_ESTABLISHED: every stair wall trace is on a plan sheet; "
                                     "no wall trace on a section spans the range",
            "FLOOR_SLAB_INTERRUPTIONS": "slabs at +5.50 and +9.70 are traced on the sections "
                                        "(LVL marks); whether the well wall passes them "
                                        "uninterrupted is not traced",
            "OPENINGS": "not traced in the well",
            "LANDINGS": "service stair flights and waists traced on A-A (STR-06); DIM-18 3.20 "
                        "clear under a landing",
            "VOIDS": "the main stair rises in the reception VOID bay (CASE-1 UNK-01/02)",
            "BALUSTRADES": "BAL-02 traced against the main stair (open, no plaster)",
            "NON_PLASTER_SURFACES": "not established",
            "WALL_OWNERSHIP_CHANGES": "not established across floors",
        },
        "CONTINUOUS_PLASTERABLE_WALL_STATUS": "NOT_ESTABLISHED",
        "ENGINEERING": "component-based, UNRESOLVED (no printed stair-wall face lengths; "
                       "STAIR_WELL_PLASTER_HEIGHT UNKNOWN)",
        "CONTRACTOR": {"HEIGHT_M": 12.90, "LENGTH_LM": 14.8, "AREA_M2": 190.92,
                       "BASIS": "CONTRACTOR_MEASUREMENT_BASIS"},
        "12_90_IS_NOT_ADOPTED": "arithmetic equality with two levels is not wall continuity",
    }


def parapet_parallel_records() -> dict:
    return {
        "ENGINEERING": {
            "SE_TERRACE_PARAPET": {"SOLID_FACE_HEIGHT": "1.22 to the band underside / 1.42 with "
                                                        "the band - AMBIGUOUS (DIM-21, DIM-20)",
                                   "KERB_UNDER_LATTICE": "0.19 to 0.80 varying (PAR-11), "
                                                         "nowhere printed",
                                   "CAPPING_BAND": "0.20 wide (DIM-20/DIM-01), separate item",
                                   "BALUSTRADE": "PLASTERABLE_SOLID_FACE = 0 (BAL-03)",
                                   "RUN_LENGTH": "7.10 chain-derived, PROVISIONAL",
                                   "STATUS": "UNRESOLVED (face height ambiguity)"},
            "TOWER_PARAPET_1390": {"HEIGHT": 0.50, "SOURCE": "DIM-14 / DIM-08 / DIM-10 / DIM-11",
                                   "LENGTH": "not printed", "STATUS": "UNRESOLVED (length)"},
        },
        "CONTRACTOR": {
            "MAIN_PARAPET": {"LENGTH_LM": 48.47, "HEIGHT_M": 1.70, "AREA_M2": 82.399,
                             "CORNERS_LM": 96.94, "ENDINGS_LM": 48.47},
            "ANNEX_PARAPETS": [{"LENGTH_LM": 28.4, "HEIGHT_M": 0.7, "AREA_M2": 19.88},
                               {"LENGTH_LM": 36.2, "HEIGHT_M": 0.7, "AREA_M2": 25.34},
                               {"LENGTH_LM": 27.2, "HEIGHT_M": 0.7, "AREA_M2": 19.04}],
            "BASIS": "CONTRACTOR_MEASUREMENT_BASIS (site record)",
        },
        "WHAT_THE_CONTRACTOR_1_70_INCLUDES": {
            "SOLID_FACE": "unknown", "CURVED_OGEE_PORTION": "unknown", "COPING": "unknown",
            "ROOF_BUILD_UP": "unknown", "BOTH_FACES": ("corners 96.94 = 2 x 48.47 suggests two "
                                                       "edges counted; not established"),
            "PAYMENT_CONVENTION": "unknown",
            "STATUS": "UNRESOLVED - hypotheses raised after the unseal stay UNCONFIRMED",
        },
        "COMPARABLE_AS_HEIGHTS": False,
        "CLASS": "MEASUREMENT_BASIS_DIFFERENCE (pending basis identification)",
    }


def facade_parallel_records() -> dict:
    return {
        "ENGINEERING": {"BASIS": "floor by floor, facade run by facade run; owner storey heights "
                                 "GROUND 4.00 / FIRST 4.50 / SECOND-ROOF 4.00; each floor its own "
                                 "geometry and setbacks", "ESTABLISHED_M2": 0.0,
                        "WHY": "no facade face with an established plastered exposure in the "
                               "traced subset"},
        "CONTRACTOR": {"BASIS": "whole facade heights x lengths",
                       "LINES": [("واجهة مرتفعة", 14.4, 7.9, 113.76), ("واجهة متوسطة", 10.0, 6.9, 69.0),
                                 ("واجهة جنوبية", 14.4, 6.75, 97.2), ("مرتفعة", 10.0, 19.2, 192.0),
                                 ("واجهة السطح", 4.7, 17.75, 83.425)],
                       "GROSS_M2": 1502.84, "NET_M2": 1469.9675},
        "DRAWING": {"OVERALL_HEIGHT": 14.40, "SOURCE": "DIM-13 (CASE-6)",
                    "STOREY_HEIGHTS": [4.50, 4.20, 4.20]},
        "OWNER_STOREY_SUM_M": 12.50,
        "NOTE": "the owner storey sum (12.50) is below the drawing overall (14.40): the "
                "difference is parapets / roof rooms / plinth, which the engineering basis "
                "measures as their own items",
        "CLASS": "MEASUREMENT_BASIS_DIFFERENCE",
        "WHY_TOTALS_DIFFER": "segmented per-floor faces with owner heights vs whole-facade "
                             "heights that include parapet, roof-room and plinth zones",
    }


def benchmark_identity(rec: dict, curves: dict) -> dict:
    rows = rec["HUMAN_DERIVATION"]["STATEMENT_ROWS"]
    names = sorted({r["DESCRIPTION"] for r in rows if r["DESCRIPTION"]})
    cad_labels = ["DEWANEYA", "DRIVER", "SALOON", "RECEPTION", "DINING", "KITCHEN", "PANTRY",
                  "MASTER BED ROOM", "Wash", "W.C", "COURT", "GARDEN", "swimming pool"]
    evidence = [
        {"KIND": "project identifier", "FOUND": "none in the workbook", "WEIGHT": "none"},
        {"KIND": "room names", "FOUND": "الديوانية / غرفة السائق / صالة / مغسلة / غرفة رئيسية x4 / "
                                       "معيشة / غرفة خدامة السطح / حمام السباحة / قبة / مصاعد",
         "MATCHES_P7757": "DEWANEYA, DRIVER, SALOON, Wash, MASTER BED ROOM, LIVING AREA (A21 "
                          "first floor), maid room on the roof (tower block), swimming pool, "
                          "domes (roof plan), elevator (round 6E-A objects)", "WEIGHT": "strong"},
        {"KIND": "floor structure", "FOUND": "ground rooms / first-floor bedrooms and living / "
                                            "roof maid room and corridor / annex roofs",
         "MATCHES_P7757": "GF, FF, +9.70 roof terrace with tower block at +13.90, annex at +4.30",
         "WEIGHT": "strong"},
        {"KIND": "level chain", "FOUND": "stair well 12.90", "MATCHES_P7757": "+1.00 -> +13.90 = 12.90 "
                                                                              "exactly (LVL marks)",
         "WEIGHT": "strong"},
        {"KIND": "overall height", "FOUND": "facade 14.40", "MATCHES_P7757": "DIM-13 1440 exactly",
         "WEIGHT": "strong"},
        {"KIND": "site", "FOUND": "صباح الأحمد البحرية (Sabah Al-Ahmad Sea City)",
         "MATCHES_P7757": "'SEA VIEW' label on the plans; pool; sea-side villa", "WEIGHT": "medium"},
        {"KIND": "curved elements", "FOUND": "قبة (dome) inside and outside, roof above the pool",
         "MATCHES_P7757": "domes on the roof plan (DIM-04 R221); pool curve CS-2", "WEIGHT": "medium"},
        {"KIND": "workbook metadata", "FOUND": ".xls, no author/title fields read; invoice serial "
                                              "date 46195", "WEIGHT": "weak"},
        {"KIND": "previously supplied manual QS workbook", "FOUND": "no registry entry names one "
                                                                    "for P7757 (P7757_PROJECT_RULES "
                                                                    "sources: DESIGN_* only)",
         "WEIGHT": "none"},
    ]
    return {"EVIDENCE": evidence, "ROW_DESCRIPTIONS": names,
            "PROJECT_IDENTITY": "REPOSITORY_EVIDENCE_CONSISTENT_WITH_P7757; OWNER_CONFIRMATION_REQUESTED",
            "OWNER_CONFIRMATION_REQUEST": (
                "Is the workbook 'كشف حصر مقاسات تنفيذ أعمال: مساح داخلي وخارجي' by شركة التسنيم "
                "(invoice No. 5, Sabah Al-Ahmad Sea City, sha256 bf6e3123...) the executed-works "
                "plaster statement for P7757? Its room set, level chain (12.90) and overall "
                "height (14.40) match the P7757 drawings exactly."),
            "QUANTITIES_USED_TO_CHANGE_FROZEN_GEOMETRY": False}


def run() -> dict:
    est = json.loads((OUT / "P7757_WALL_TREATMENT_ESTIMATE_v2.json").read_text("utf-8"))
    rec = json.loads((OUT / "BENCHMARK_RECONCILIATION.json").read_text("utf-8"))
    curves = json.loads((OUT / "CAD_CURVE_REGISTER.json").read_text("utf-8"))
    reg = json.loads(Path(P.TRACE_REGISTER).read_text("utf-8"))
    rb = contractor_rulebook()
    params = est["PARAMETER_REGISTRY"]
    side, items = [], []
    for s in est["SETS"]:
        plan, fs, sh = s["PLAN"], s["FACE_SET"], s["SHEET"]
        floor = {"GROUND": "GROUND", "FIRST": "FIRST"}.get(plan["FLOOR"], plan["FLOOR"])
        applicable = plan["TRADE"] in ("NORMAL_INTERNAL_PLASTER", "COLUMN_BONDING_PLUS_PLASTER")
        con = (C.calculate_contractor(fs, rb, treatment=plan["TRADE"], floor=floor)
               if applicable else None)
        eng_v = sh["RESULT"]["ESTABLISHED_SUBTOTAL_M2"]
        con_v = con["RESULT"]["CONTRACTOR_MEASUREMENT_QUANTITY_M2"] if con else None
        dec = (C.decompose(fs, sh, params, rb, treatment=plan["TRADE"], floor=floor,
                           engine_calculate=E.calculate) if con else
               {"DECOMPOSABLE": False, "WHY": "the contractor record has no line at this "
                                              "trade granularity (SCOPE)"})
        reason = ("HEIGHT rule 3.20 vs 3.60 on the same faces; no openings on established faces"
                  if dec.get("DECOMPOSABLE") else dec.get("WHY"))
        if con and eng_v is None and con_v is None:
            reason = "no established face on either basis"
        side.append({"SET_ID": plan["SET_ID"], "TRADE": plan["TRADE"], "FLOOR": plan["FLOOR"],
                     "ZONE": plan["ZONE"],
                     "ENGINEERING_M2": eng_v, "ENGINEERING_STATE": sh["QUANTITY_STATE"]["ESTABLISHED_SUBTOTAL"],
                     "ENGINEERING_PROVISIONAL_M2": sh["RESULT"]["PROVISIONAL_SUBTOTAL_M2"],
                     "CONTRACTOR_M2": con_v,
                     "CONTRACTOR_STATUS": con["STATUS"] if con else "NOT_APPLICABLE_AT_THIS_GRANULARITY",
                     "DELTA_M2": (round(con_v - eng_v, 4) if isinstance(eng_v, (int, float))
                                  and isinstance(con_v, (int, float)) else None),
                     "REASON": reason, "DECOMPOSITION": dec,
                     "COVERAGE": fs["COVERAGE_STATUS"],
                     "COMPLETE_TOTAL_STATUS": fs["COMPLETE_TOTAL_STATUS"]})
        items.append(Q.layered_item(
            item_id=plan["SET_ID"], trade=plan["TRADE"], unit="m2",
            physical={"ESTABLISHED_FACES_LM": fs["GROSS_BASIS"]["ESTABLISHED_LM"],
                      "PROVISIONAL_FACES_LM": fs["GROSS_BASIS"]["PROVISIONAL_LM"],
                      "UNRESOLVED_FACES": [u["FACE_ID"] for u in fs["UNRESOLVED_FACES"]],
                      "STATUS": fs["COVERAGE_STATUS"]},
            measured_net={"VALUE": eng_v, "STATE": sh["QUANTITY_STATE"]["ESTABLISHED_SUBTOTAL"],
                          "RULES": ["FULL_OPENING_DEDUCTION", "reveals separate",
                                    "height " + str(params.get("NORMAL_INTERNAL_PLASTER_HEIGHT", {}).get("VALUE"))
                                    if plan["TRADE"] in ("NORMAL_INTERNAL_PLASTER", "COLUMN_BONDING_PLUS_PLASTER")
                                    else "height per treatment parameter"],
                          "PROVISIONAL_APART": sh["RESULT"]["PROVISIONAL_SUBTOTAL_M2"]},
            contractor=({"VALUE": con_v, "RULES": list(con["RULES_USED"].keys()),
                         "SOURCE_TYPE": "SITE_RECORD", "STATUS": con["STATUS"]} if con else None),
            waste_factor=None, rate=None))
    proj_eng = est["AGGREGATES"]["PROJECT"]["ESTABLISHED_SUBTOTAL_M2"]
    proj_con = round(sum(x["CONTRACTOR_M2"] for x in side if isinstance(x["CONTRACTOR_M2"], (int, float))), 4)
    drivers = {d: 0.0 for d in Q.DRIVERS}
    for x in side:
        d = x["DECOMPOSITION"]
        if d.get("DECOMPOSABLE"):
            for k, v in d["DRIVERS"].items():
                drivers[k] = round(drivers[k] + v, 4)
    body = {
        "PHASE_ID": P.PHASE_ID, "ARTIFACT": "DUAL_BASIS",
        "BASES": Q.BASES, "LAYERS": Q.LAYERS,
        "CONTRACTOR_RULEBOOK": rb,
        "HEIGHT_BASIS_RECORDS": height_basis_records(),
        "SIDE_BY_SIDE": side,
        "LAYERED_ITEMS": items,
        "PROJECT": {"ENGINEERING_ESTABLISHED_SUBTOTAL_M2": proj_eng,
                    "CONTRACTOR_ON_THE_SAME_FACES_M2": proj_con,
                    "DELTA_ON_COMPARABLE_FACES_M2": round(proj_con - proj_eng, 4),
                    "DRIVERS_ON_COMPARABLE_FACES_M2": drivers,
                    "CONTRACTOR_WHOLE_HOUSE_INTERNAL_NET_M2": 1151.1375,
                    "SCOPE_NOT_COVERED_BY_THE_TRACED_SUBSET_M2": round(1151.1375 - proj_con, 4),
                    "NOTE": "the whole-house figure minus the contractor basis on the traced faces "
                            "is SCOPE, not error; nothing is a total"},
        "STAIRWELL_CONTINUITY": stairwell_continuity(reg),
        "PARAPETS": parapet_parallel_records(),
        "FACADES": facade_parallel_records(),
        "REVEAL_RULE": "ENGINEERING: host wall thickness first (0.20 SEG-02/SEG-03; 0.15 the "
                       "reception north wall), TEMPORARY_DEFAULT only when unknown; CONTRACTOR: 0.20 "
                       "girth 5.70. Agreement where the wall is 0.20; retained difference where 0.15",
        "BENCHMARK_IDENTITY": benchmark_identity(rec, curves),
        "RATE": {"STATUS": "NO_RATE_HAS_BEEN_QUOTED_FOR_THIS_PROJECT",
                 "SOURCE": "data/rate_cards/P7757_RATE_CARD.json", "KWD_IMPACT": None},
        "NO_BASIS_OVERWRITES_THE_OTHER": True, "NOT_AN_APPROVED_BOQ": True,
    }
    p = OUT / "DUAL_BASIS.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"DUAL_BASIS_SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "PROJECT": body["PROJECT"],
            "SIDE_BY_SIDE": [(x["SET_ID"], x["ENGINEERING_M2"], x["CONTRACTOR_M2"], x["DELTA_M2"])
                             for x in side if x["CONTRACTOR_M2"] is not None or x["ENGINEERING_M2"]]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
