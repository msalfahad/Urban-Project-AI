"""OWNER REVIEW v2 (§17): only the residual items that need owner judgment,
each with image, both bases, why different, impact, options and a
technical recommendation; then what was resolved automatically and why.

    python3 -m research.qs_wall_treatment_01.owner_review_v2
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)


def build() -> str:
    cards = json.loads((OUT / "DECISION_CARDS.json").read_text("utf-8"))
    dual = json.loads((OUT / "DUAL_BASIS.json").read_text("utf-8"))
    a22 = json.loads((OUT / "A22_DUAL_BASIS.json").read_text("utf-8"))
    L = ["# P7757 wall treatment - owner review v2 (dual basis)", "",
         "Two quantity bases are kept in parallel and neither overwrites the other: "
         "ENGINEERING_QS (geometry + approved project parameters, full opening deduction, "
         "reveals separate) and CONTRACTOR_SITE_MEASUREMENT (the site record's conventions). "
         "Differences between them are MEASUREMENT_BASIS_DIFFERENCE unless a basis "
         "comparison shows an error. No rate is quoted for P7757, so no KWD impact exists.",
         "", "## DECISIONS REQUIRED", ""]
    for c in cards["CARDS"]:
        if not c["OWNER_DECISION_REQUIRED"]:
            continue
        L += [f"### {c['CARD_ID']} - {c['TITLE']}", "",
              f"- DECISION REQUIRED: {c.get('DECISION_REQUIRED')}",
              f"- DRAWING / TRACE IMAGE: {c.get('IMAGE') or 'n/a'}",
              f"- ENGINEERING BASIS: {c.get('ENGINEERING_BASIS')}",
              f"- CONTRACTOR BASIS: {c.get('CONTRACTOR_BASIS')}",
              f"- WHY DIFFERENT: {c.get('WHY_DIFFERENT')}",
              f"- QUANTITY IMPACT: {json.dumps(c.get('QUANTITY_IMPACT_M2'), ensure_ascii=False)}",
              f"- KWD IMPACT: {c.get('KWD_IMPACT')}",
              f"- OPTION A: {c.get('OPTION_A')}", f"- OPTION B: {c.get('OPTION_B')}",
              f"- TECHNICAL RECOMMENDATION: {c.get('TECHNICAL_RECOMMENDATION')}", ""]
    L += ["## RESOLVED AUTOMATICALLY BY THE SOURCE HIERARCHY", ""]
    for c in cards["CARDS"]:
        if c["OWNER_DECISION_REQUIRED"]:
            continue
        L += [f"- **{c['CARD_ID']}** {c['TITLE']}: {c['CLASS']}. {c['CAD_INTERPRETATION']} "
              f"Impact: {json.dumps(c['QUANTITY_IMPACT_M2'])}. Image: {c['IMAGE']}"]
    L += ["", "## SIDE BY SIDE (traced faces; established subtotals, never totals)", "",
          "| component | engineering m2 | contractor m2 | delta | reason |", "|---|---|---|---|---|"]
    for r in a22["SIDE_BY_SIDE_TRACED_FACES"]:
        if r["ENGINEERING"]["M2"] or r["CONTRACTOR"]["M2"]:
            L.append(f"| {r['COMPONENT']} | {r['ENGINEERING']['M2']} ({r['ENGINEERING']['STATE']}) | "
                     f"{r['CONTRACTOR']['M2']} | {r['DELTA_M2']} | {r['REASON']} |")
    for r in a22["SIDE_BY_SIDE_WHOLE_RECORD"]:
        L.append(f"| {r['COMPONENT']} | {r['ENGINEERING'].get('M2')} ({r['ENGINEERING'].get('STATE', r['ENGINEERING']['BASIS'])}) | "
                 f"{r['CONTRACTOR'].get('M2', r['CONTRACTOR'].get('LM'))} | {r['DELTA_M2']} | {r['REASON']} |")
    at = a22["WHOLE_HOUSE_DIFFERENCE_ATTRIBUTION"]
    L += ["", "## WHERE THE DIFFERENCE COMES FROM", "",
          f"- HEIGHT on comparable faces: {at['HEIGHT_M2']} m2 (3.20 engineering vs 3.60 site record)",
          f"- OPENING DEDUCTION on comparable faces: {at['OPENING_DEDUCTION_M2']} m2",
          f"- DOOR DIMENSION: {at['DOOR_DIMENSION_M2']} m2; REVEALS: {at['REVEALS_M2']} m2; GEOMETRY: {at['GEOMETRY_M2']} m2",
          f"- PARAPET BASIS / FACADE BASIS: not comparable yet (basis of the site heights unresolved)",
          f"- SCOPE (whole house beyond the traced faces): {at['SCOPE_M2']} m2",
          "", "## HEIGHT BASIS RECORDS (no averaging)", "",
          "| item | engineering | contractor | drawing storey | class |", "|---|---|---|---|---|"]
    for h in dual["HEIGHT_BASIS_RECORDS"]:
        L.append(f"| {h['ITEM']} | {h['ENGINEERING_HEIGHT']} ({h['ENGINEERING_SOURCE']}) | "
                 f"{h['CONTRACTOR_HEIGHT']} ({h['CONTRACTOR_SOURCE']}) | {h['DRAWING_STOREY_HEIGHT']} | {h['CLASS']} |")
    sc = dual["STAIRWELL_CONTINUITY"]
    L += ["", f"Stair well: CONTINUOUS_PLASTERABLE_WALL_STATUS = {sc['CONTINUOUS_PLASTERABLE_WALL_STATUS']}; "
              f"engineering {sc['ENGINEERING']}; contractor 12.90 kept as CONTRACTOR_MEASUREMENT_BASIS.",
          f"Parapets: {dual['PARAPETS']['CLASS']}; what the 1.70 includes: "
          f"{dual['PARAPETS']['WHAT_THE_CONTRACTOR_1_70_INCLUDES']['STATUS']}.",
          f"Facades: {dual['FACADES']['CLASS']} - {dual['FACADES']['WHY_TOTALS_DIFFER']}.",
          "", "Nothing here is an approved BOQ; nothing was written to Firebase; no contractor "
              "convention became geometry; no project rule became an Urban-wide rule."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    p = OUT / "OWNER_REVIEW_V2.md"
    p.write_text(build(), encoding="utf-8")
    print(json.dumps({"OWNER_REVIEW_V2_SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}))
