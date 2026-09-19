"""A22 re-run with MEASUREMENT BASIS explicit (§16 B, F, G).

Every comparison names the basis on each side. A difference between
ENGINEERING_QS and CONTRACTOR_SITE_MEASUREMENT is MEASUREMENT_BASIS_DIFFERENCE
by default; ENGINE_ERROR, VISUAL_QS_ERROR or HUMAN_MEASUREMENT_ERROR are
never assigned automatically. The contractor workbook is not an oracle.

    python3 -m research.qs_wall_treatment_01.a22_dual_basis
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)


def run() -> dict:
    dual = json.loads((OUT / "DUAL_BASIS.json").read_text("utf-8"))
    links = json.loads((OUT / "CAD_TRACE_LINKS.json").read_text("utf-8"))
    a22 = json.loads((OUT / "A22_STRUCTURAL_COMPARISON.json").read_text("utf-8"))
    rec = json.loads((OUT / "BENCHMARK_RECONCILIATION.json").read_text("utf-8"))
    side = dual["SIDE_BY_SIDE"]
    rows = []
    for x in side:
        rows.append({"COMPONENT": x["SET_ID"], "TRADE": x["TRADE"],
                     "ENGINEERING": {"BASIS": "ENGINEERING_QS", "M2": x["ENGINEERING_M2"],
                                     "STATE": x["ENGINEERING_STATE"],
                                     "PROVISIONAL_APART_M2": x["ENGINEERING_PROVISIONAL_M2"]},
                     "CONTRACTOR": {"BASIS": "CONTRACTOR_SITE_MEASUREMENT", "M2": x["CONTRACTOR_M2"],
                                    "STATUS": x["CONTRACTOR_STATUS"]},
                     "DELTA_M2": x["DELTA_M2"],
                     "REASON": x["REASON"],
                     "DRIVERS": (x["DECOMPOSITION"].get("DRIVERS") if x["DECOMPOSITION"].get("DECOMPOSABLE")
                                 else {"SCOPE": None}),
                     "CLASS": ("MEASUREMENT_BASIS_DIFFERENCE" if x["DELTA_M2"] not in (None, 0.0)
                               else "AGREEMENT" if x["DELTA_M2"] == 0.0 else "SCOPE_DIFFERENCE")})
    # whole-record components with no engineering counterpart at this granularity
    whole = [
        {"COMPONENT": "stair well walls", "ENGINEERING": {"BASIS": "ENGINEERING_QS", "M2": None,
                                                          "STATE": "UNRESOLVED (continuity not established)"},
         "CONTRACTOR": {"BASIS": "CONTRACTOR_SITE_MEASUREMENT", "M2": 190.92 + 13.5},
         "DELTA_M2": None, "REASON": "12.90 x 14.8 + 5.4 x 2.5 on the record; engineering component-based",
         "DRIVERS": {"HEIGHT": "12.90 basis", "SCOPE": "no printed stair-wall lengths"},
         "CLASS": "MEASUREMENT_BASIS_DIFFERENCE"},
        {"COMPONENT": "roof parapets", "ENGINEERING": {"BASIS": "ENGINEERING_QS", "M2": None,
                                                       "STATE": "UNRESOLVED (face ambiguity, lengths)"},
         "CONTRACTOR": {"BASIS": "CONTRACTOR_SITE_MEASUREMENT", "M2": 82.399 + 19.88 + 25.34 + 19.04},
         "DELTA_M2": None, "REASON": "1.70 / 0.70 site heights on unstated basis vs 1.22/1.42 face and 0.50",
         "DRIVERS": {"PARAPET_BASIS": "unknown inclusion", "GEOMETRY": "face ambiguity"},
         "CLASS": "MEASUREMENT_BASIS_DIFFERENCE"},
        {"COMPONENT": "external plaster", "ENGINEERING": {"BASIS": "ENGINEERING_QS per floor", "M2": 0.0,
                                                          "STATE": "no established facade face"},
         "CONTRACTOR": {"BASIS": "CONTRACTOR whole facade", "M2": 1469.9675},
         "DELTA_M2": None, "REASON": dual["FACADES"]["WHY_TOTALS_DIFFER"],
         "DRIVERS": {"FACADE_BASIS": "whole vs segmented", "HEIGHT": "14.40 vs 4.00/4.50/4.00", "SCOPE": "subset"},
         "CLASS": "MEASUREMENT_BASIS_DIFFERENCE"},
        {"COMPONENT": "opening deductions", "ENGINEERING": {"BASIS": "FULL_OPENING_DEDUCTION"},
         "CONTRACTOR": {"BASIS": "HALF_OPENING_DEDUCTION", "M2": 58.2475},
         "DELTA_M2": None, "REASON": "convention; on the traced faces no opening is deductible on either basis",
         "DRIVERS": {"OPENING_DEDUCTION": "0.5 factor"}, "CLASS": "MEASUREMENT_BASIS_DIFFERENCE"},
        {"COMPONENT": "door dimension", "ENGINEERING": {"BASIS": "TEMPORARY_DEFAULT 1.00 x 2.20"},
         "CONTRACTOR": {"BASIS": "SITE_RECORD 1.00 x 2.30"}, "DELTA_M2": None,
         "REASON": "hierarchy: drawing/schedule > owner input > default; the record does not override it",
         "DRIVERS": {"DOOR_DIMENSION": "0.10 height"}, "CLASS": "MEASUREMENT_BASIS_DIFFERENCE"},
        {"COMPONENT": "door reveals", "ENGINEERING": {"BASIS": "host wall thickness first (0.20 / 0.15)"},
         "CONTRACTOR": {"BASIS": "0.20 x girth 5.70", "M2": 15.96}, "DELTA_M2": None,
         "REASON": "agreement where the host wall is 0.20; retained difference where 0.15",
         "DRIVERS": {"REVEALS": "depth rule"}, "CLASS": "MEASUREMENT_BASIS_DIFFERENCE"},
        {"COMPONENT": "tartusha", "ENGINEERING": {"BASIS": "ENGINEERING_QS", "M2": None,
                                                  "STATE": "no wet room traced"},
         "CONTRACTOR": {"BASIS": "CONTRACTOR", "M2": 433.83 + 70.7125}, "DELTA_M2": None,
         "REASON": "outside the traced subset", "DRIVERS": {"SCOPE": "subset"}, "CLASS": "SCOPE_DIFFERENCE"},
        {"COMPONENT": "corners / endings / profiles", "ENGINEERING": {"BASIS": "eligible lm per category; "
                                                                               "rule UNKNOWN", "LM": 0},
         "CONTRACTOR": {"BASIS": "2m=1m", "LM": 385.375 + 648.675}, "DELTA_M2": None,
         "REASON": "no established profile edge; convention halves lm", "DRIVERS": {"OTHER": "convention"},
         "CLASS": "MEASUREMENT_BASIS_DIFFERENCE"},
    ]
    resolved = {k: v for k, v in links["ITEMS"].items()}
    body = {
        "PHASE_ID": P.PHASE_ID, "ARTIFACT": "A22_DUAL_BASIS",
        "PREVIOUS_A22_SHA256": hashlib.sha256((OUT / "A22_STRUCTURAL_COMPARISON.json").read_bytes()).hexdigest(),
        "BASES_COMPARED": ["ENGINEERING_QS", "CONTRACTOR_SITE_MEASUREMENT", "CAD_GEOMETRY (A21 corroboration)"],
        "SIDE_BY_SIDE_TRACED_FACES": rows,
        "SIDE_BY_SIDE_WHOLE_RECORD": whole,
        "DRIVERS_ON_COMPARABLE_FACES_M2": dual["PROJECT"]["DRIVERS_ON_COMPARABLE_FACES_M2"],
        "WHOLE_HOUSE_DIFFERENCE_ATTRIBUTION": {
            "CONTRACTOR_INTERNAL_NET_M2": 1151.1375,
            "ENGINEERING_ESTABLISHED_SUBTOTAL_M2": dual["PROJECT"]["ENGINEERING_ESTABLISHED_SUBTOTAL_M2"],
            "CONTRACTOR_ON_TRACED_FACES_M2": dual["PROJECT"]["CONTRACTOR_ON_THE_SAME_FACES_M2"],
            "HEIGHT_M2": dual["PROJECT"]["DRIVERS_ON_COMPARABLE_FACES_M2"]["HEIGHT"],
            "OPENING_DEDUCTION_M2": dual["PROJECT"]["DRIVERS_ON_COMPARABLE_FACES_M2"]["OPENING_DEDUCTION"],
            "DOOR_DIMENSION_M2": dual["PROJECT"]["DRIVERS_ON_COMPARABLE_FACES_M2"]["DOOR_DIMENSION"],
            "REVEALS_M2": 0.0, "PARAPET_BASIS_M2": "not comparable", "FACADE_BASIS_M2": "not comparable",
            "GEOMETRY_M2": 0.0,
            "SCOPE_M2": dual["PROJECT"]["SCOPE_NOT_COVERED_BY_THE_TRACED_SUBSET_M2"],
            "OTHER_M2": dual["PROJECT"]["DRIVERS_ON_COMPARABLE_FACES_M2"]["OTHER"],
        },
        "T2_T3_T9": {k: {"CLASS": v["CLASS"], "OWNER_DECISION_NEEDED": v["OWNER_DECISION_NEEDED"],
                         "RESOLVED_BY": v["RESOLVED_BY"]} for k, v in resolved.items()},
        "PREVIOUS_VERDICTS_RECLASSIFIED": {
            "T2": "BASIS_DIFFERENCE -> CAD_MAPPING_DIFFERENCE (locator artefact); resolved",
            "T3": "GEOMETRY_DIFFERENCE -> DIMENSION_OWNERSHIP_DIFFERENCE; resolved",
            "T9": "HUMAN_REVIEW_REQUIRED -> DIMENSION_OWNERSHIP_DIFFERENCE; column line "
                  "retired, CAD exposed faces PROVISIONAL",
            "R1/R4/R5/R6/R8": "HEIGHT/OPENING/BASIS differences -> MEASUREMENT_BASIS_DIFFERENCE "
                              "on two retained bases; no owner choice needed",
        },
        "NOT_AN_ERROR_ORACLE": True, "ESTIMATE_CHANGED_BY_THE_RECORD": False,
    }
    p = OUT / "A22_DUAL_BASIS.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"A22_DUAL_BASIS_SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "ATTRIBUTION": body["WHOLE_HOUSE_DIFFERENCE_ATTRIBUTION"]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
