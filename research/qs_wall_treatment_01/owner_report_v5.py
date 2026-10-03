"""OWNER REPORT v5 - the parapet assembly phase in the §29 format.

    python3 -m research.qs_wall_treatment_01.owner_report_v5
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)


def build() -> str:
    asm = json.loads((OUT / "PARAPET_ASSEMBLY_REGISTER.json").read_text("utf-8"))
    faces = json.loads((OUT / "FACE_MEASUREMENT_REGISTER.json").read_text("utf-8"))["FACES"]
    tr = json.loads((OUT / "PLASTER_QUANTITY_TRACE.json").read_text("utf-8"))
    st = json.loads((OUT / "STRUCTURAL_SOURCE_CHECK.json").read_text("utf-8"))
    link = json.loads((OUT / "ROOF_EDGE_PLAN_TO_ELEVATION_LINK_REGISTER.json").read_text("utf-8"))
    q = json.loads((OUT / "OWNER_DECISION_QUEUE.json").read_text("utf-8"))
    led = json.loads((OUT / "REVISION_SUPERSESSION_LEDGER.json").read_text("utf-8"))
    a22 = json.loads((OUT / "A22_RECONCILIATION_REGISTER.json").read_text("utf-8"))
    L = ["# P7757 - owner report v5 (parapet assembly, four-layer measurement, D2 structural check)", "",
         "PHASE: PA01 - parapet assembly model, roof-edge geometry from the DWG and the structural set, four-layer measurement architecture, plaster category pass v4",
         "STATUS: COMPLETE for the automatic work; six non-blocking owner decisions queued; no hard stop reached", "",
         "## WHAT WAS PROVEN", ""]
    sol = link["PORTIONS_PROPOSED"]["SOLID_PORTION_NE"]
    lat = link["PORTIONS_PROPOSED"]["LATTICE_KERB_PORTION_SW"]
    L += [f"- The SE roof edge exists in the DWG roof-plan copy as authored lines: outer face {link['PLAN_RUN_LENGTH']['OUTER_FACE_M']} m, "
          f"roof-side floor line {link['PLAN_RUN_LENGTH']['ROOF_SIDE_FLOOR_LINE_M']} m (= the printed 129 + 2 x R221 + 139 chain exactly), "
          f"a 250 mm line that runs {lat['KERB_ZONE_LINE_LENGTH_M']} m from the SW corner and stops (the frozen raster's UNK-01), and the SW corner arc r = 0.231 m.",
          f"- Solid portion (NE part): {sol['OUTER_FACE_LENGTH_M']} m outer / {sol['ROOF_SIDE_FACE_LENGTH_M']} m roof-side; lattice / kerb portion {lat['KERB_ZONE_LINE_LENGTH_M']} m. "
          "The split is PROPOSED_CORRESPONDENCE (the B-B cut lands inside it; the elevation proportion agrees to ~0.3 m).",
          "- The structural set ST7757.pdf is an exact 1:100 vector plot: its column plan registers to the architectural DWG by translation alone "
          f"({st['REGISTRATION_p1']['INLIERS']}/{st['REGISTRATION_p1']['CAD_LOOPS']} columns, max residual {st['REGISTRATION_p1']['MAX_RESIDUAL_MM']} mm); "
          f"its roof-slab sheet gives the SE edge as {st['SE_ROOF_EDGE_STRUCTURE']['OUTER_EDGE_LENGTH_M']} m and the +13.90 slab outline as "
          f"{st['TOWER_ROOF_13_90_OUTLINE_p6']['DEVELOPED_PERIMETER_M']} m exterior ring; its edge detail is an RC beam 45 x 75 with a 20 x 20 upstand, "
          "and the engineer defers the parapet above to the architectural detail.",
          "- D2: a 30 x 60 structural column stands exactly on the architectural loop LOOP-059 (COLUMN_EXISTS ESTABLISHED); it is free-standing 1.3 m off the "
          "neighbour wall with ground and ceiling beams to it, so COLUMN_EXPOSED_TO_ROOM = ESTABLISHED_PROVISIONAL (4 faces); it does not own the SALOON "
          "clear face (NO). The 1.3 m dashed line is the overhead beam line, not a wall.",
          "- The drawn base line at +9.88 is a level line 0.18 m above the +9.70 slab on both the frozen raster and the DWG elevation (finish-level candidate).",
          "- 104 and 139 remain separate printed dimensions; 130 is on B-B only; 155 is the tower/dome feature; 50 (SE) is a chain link. None enters plaster arithmetic.",
          "", "## WHAT CHANGED", "",
          f"- PARAPET_ASSEMBLY_REGISTER: {len(asm['COMPONENTS'])} components (slab datum, structural edge, solid parapet, kerb, balustrade, handrail, coping, pier, facade, "
          "tower/dome feature, external finish face, roof-side face, tower ring, NE / SW parapets, NW thin element) - what material exists before any quantity.",
          f"- FACE_MEASUREMENT_REGISTER: {len(faces)} faces with FACE_BOTTOM / FACE_TOP / FACE_HEIGHT / FACE_SIDE / FACE_MATERIAL / FACE_PLASTER_ELIGIBILITY; balustrade and handrail faces are zero by construction.",
          "- Four-layer architecture in production: PHYSICAL_GEOMETRY -> TOPOLOGICAL_RELATION -> QS_MEASUREMENT_GEOMETRY (virtual closures: MATERIAL_PRESENT = PHYSICAL_WALL = GEOMETRY_AUTHORITY = False) -> TRADE_QUANTITY; "
          "OPENING_REGISTER with PHYSICAL_OPENING / MEASUREMENT_CLOSURE / OPENING_DEDUCTION / REVEAL_QUANTITY apart.",
          "- PLASTER_QUANTITY_TRACE v4: every line carries one of the five quantity states; totals per unit and per state only.",
          "- A22_RECONCILIATION_REGISTER v4 with drivers and classes; contractor basis kept parallel and conditional (IF_BENCHMARK_IS_P7757).",
          "- OWNER_DECISION_QUEUE, REVISION_SUPERSESSION_LEDGER, SOURCE_COVERAGE, BENCHMARK_LEAKAGE_GUARD (geometry artifacts clean), VISUAL_QA overlays on the original pages.",
          "", "## WHAT WAS WITHDRAWN / CORRECTED", ""]
    for e in led["ENTRIES"]:
        L.append(f"- {e['LEDGER_ID']} {e['MARK']}: \"{e['PREVIOUS_STATEMENT']}\" -> {e['REPLACED_BY']}")
    L += ["- All earlier freezes hash unchanged: " + ", ".join(k for k, v in led["FROZEN_ARTIFACTS_UNCHANGED"].items() if v["OK"]) + ".",
          "", "## QUANTITIES NOW AVAILABLE (partial; never a total)", "",
          "| category | unit | state | value |", "|---|---|---|---|"]
    for c, v in tr["BY_CATEGORY"].items():
        for u, states in v["TOTALS_BY_UNIT_AND_STATE"].items():
            for s_, val in states.items():
                L.append(f"| {c} | {u} | {s_} | {val} |")
    L += ["", "Key lines: SALOON 22.88 m2 OWNER_PARAMETRIC (unchanged); SE solid parapet roof-side 4.88 m2 and external 5.16 m2 PROVISIONAL; kerb 1.10 / 1.78 m2 PROVISIONAL; "
          "coping 0.74 top + 1.43 edges PROVISIONAL; NE parapet roof-side 31.17 m2 PROVISIONAL (18.87 x 1.65 from one A-A cut); tower ring roof-side 14.20 / external 14.90 m2 PROVISIONAL; "
          "D2 column bonding 1.80 lm and 5.76 m2 PROVISIONAL.",
          "", "## WHAT REMAINS UNRESOLVED", ""]
    for u in tr["UNRESOLVED_SCOPE"]:
        L.append(f"- {u['CATEGORY']} / {u.get('FACE_ID')}: {u['WHY']}")
    L += ["", "Technical follow-ups (not owner decisions): " + "; ".join(t["WHAT"] for t in q["TECHNICAL_FOLLOW_UPS_NOT_OWNER"]) + ".",
          "", "## OWNER DECISIONS REQUIRED", "", "None blocks the next phase (STOP_GATE: no stop). Batched:", ""]
    for i, d in enumerate(q["QUEUE"], 1):
        L += [f"**{i}. {d['DECISION_ID']}** ({d['PRIORITY']}) - {d['QUESTION']}",
              f"   - A: {d['OPTION_A']}", f"   - B: {d['OPTION_B']}" + (f"; C: {d['OPTION_C_IF_REQUIRED']}" if d.get("OPTION_C_IF_REQUIRED") else ""),
              f"   - impact: {d['QUANTITY_IMPACT_IF_KNOWN']}; recommendation: {d.get('TECHNICAL_RECOMMENDATION') or '-'}; card: {d['VISUAL_CARD']}", ""]
    L += ["## NEXT AUTOMATIC PHASE", "",
          "Trace the sections for the RECEPTION double height and the stair wells (component faces, never 12.90), trace the SE facade openings to net the 40.5 m2 gross, "
          "author the kerb profile, register the roof-plan raster with declared pairs, and extend the assembly model to the FF/annex roof edges - all without owner input. "
          "Contractor basis stays parallel; A22 reruns on the new faces only.", "",
          "A22 items this phase: " + "; ".join(f"{i['ITEM_ID']} {i['CLASS']}" for i in a22["ITEMS"]) + "."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    p = OUT / "OWNER_REPORT_V5.md"
    p.write_text(build(), encoding="utf-8")
    print(json.dumps({"OWNER_REPORT_V5_SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}))
