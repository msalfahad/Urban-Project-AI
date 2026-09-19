"""OWNER REVIEW v4 - v3 plus the second owner manual source check (SOUTH
EAST ELEVATION / D1): the native re-check, the dimension trace audit,
the 104 / 139 / 130 / 93-97 / 155 / 50 source statuses, the roof-edge
material audit, D1 as one card, D2 provisional resolution, D3 unchanged.

    python3 -m research.qs_wall_treatment_01.owner_review_v4
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P
from research.qs_wall_treatment_01.owner_review_v3 import build as build_v3

OUT = Path(P.OUT_DIR)


def _pt(p):
    return "-" if p is None else f"({p[0]},{p[1]})"


def build() -> str:
    se = json.loads((OUT / "SE_ELEVATION_SOURCE_AUDIT.json").read_text("utf-8"))
    est = json.loads((OUT / "P7757_WALL_TREATMENT_ESTIMATE_v3.json").read_text("utf-8"))
    ag = est["AGGREGATES"]["PROJECT"]
    ts = se["TEXT_SOURCE_STATUS"]
    d1, d2, d3 = se["D1"], se["D2"], se["D3"]
    mat = se["SE_ROOF_EDGE_MATERIAL_AUDIT"]
    L = ["# P7757 wall treatment - owner review v4 (SE elevation source check)", "",
         "Second owner manual source check, applied as a new evidence layer "
         "(SOURCE = SOUTH_EAST_ELEVATION / SECTION_B_B / SECTION_A_A native scans, "
         "INTERPRETATION = OWNER_VERIFIED_TEXT_EXISTENCE). No frozen output was rewritten; "
         "the SALOON layer and estimate v3 are untouched.", "",
         "## NATIVE SOURCE CHECK", "",
         "| sheet | original PDF page (1-based) | embedded image sha256 | matches frozen SOURCE_FILE_HASH |",
         "|---|---|---|---|"]
    for k, v in se["NATIVE_SOURCE"].items():
        L.append(f"| {k} | {v['ORIGINAL_PAGE']} | {v['EMBEDDED_IMAGE_SHA256'][:16]}... | "
                 f"{v['MATCHES_TRACE_SOURCE_FILE_HASH']} |")
    L += ["", "## DIMENSION TRACE AUDIT (ownership by witness-line termination, not proximity)", "",
          "| trace | sheet | text | read status | end A terminates on | end B terminates on | "
          "owner candidate | owner status (termination) | owner status (deterministic) | usable as plaster height | cross-sheet |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in se["DIMENSION_TRACE_AUDIT"]:
        L.append(f"| {r['TRACE_ID']} | {r['SHEET_ID']} p{r['ORIGINAL_PAGE']} | {r['READ_TEXT']} | "
                 f"{r['TEXT_READ_STATUS']} | {r['END_A_TERMINATES_ON']} | {r['END_B_TERMINATES_ON']} | "
                 f"{r['OWNER_OBJECT_CANDIDATE']} | {r['DIMENSION_OWNER_STATUS_TERMINATION_BASED']} | "
                 f"{r['DIMENSION_OWNER_STATUS_DETERMINISTIC']} | {r['USABLE_AS_PLASTER_HEIGHT']} | "
                 f"{r['CROSS_SHEET_RELATION_STATUS']} |")
    L += ["", "Every row carries SOURCE_HASH, PRESENTATION_HASH, TEXT_BBOX, DIMENSION_LINE_TRACE, "
              "tick endpoints (processed and native) and a native evidence crop in "
              "`SE_ELEVATION_SOURCE_AUDIT.json` / `decision_cards/se_native/`.",
          "", "## TEXT SOURCE STATUS (owner observations reconciled)", "",
          f"- **104**: {ts['104_SOURCE_STATUS']['STATUS']}. {ts['104_SOURCE_STATUS']['WHERE']}. "
          f"Evidence `{ts['104_SOURCE_STATUS']['EVIDENCE']}`. Misread of 139: "
          f"{ts['104_SOURCE_STATUS']['IS_IT_A_MISREAD_OF_139']}. Forward use: "
          f"{ts['104_SOURCE_STATUS']['STAYS_IN_FORWARD_USE']}.",
          f"- **139**: {ts['139_SOURCE_STATUS']['STATUS']}, owner {ts['139_SOURCE_STATUS']['OWNER']}, "
          f"independent of 104: {ts['139_SOURCE_STATUS']['INDEPENDENT_OF_104']}.",
          f"- **130**: {ts['130_SOURCE_STATUS']['STATUS']}; on the SE elevation: "
          f"{ts['130_SOURCE_STATUS']['SE_ELEVATION']}. B-B sheet preserved as it is.",
          f"- **93 / 97**: {ts['93_97_SOURCE_STATUS']['STATUS']}. {ts['93_97_SOURCE_STATUS']['WHERE']}. "
          f"Relation to the parapet: {ts['93_97_SOURCE_STATUS']['RELATION_TO_PARAPET']}.",
          f"- **155**: {ts['155_50_SAFETY']['155']}.",
          f"- **50 (SE)**: {ts['155_50_SAFETY']['50 (SE)']}.",
          f"- DIMENSION_TEXT_CORRECTION: {ts['DIMENSION_TEXT_CORRECTION']}.",
          "", "## PARAPET / BALUSTRADE MATERIAL AUDIT (SE roof edge)", "",
          "| element | material | height / face | length |", "|---|---|---|---|"]
    for e in mat["SOLID_PLASTERABLE"]:
        h = e.get("EXTERNAL_FACE_TOP") or e.get("HEIGHT") or e.get("ROOF_SIDE_FACE") or e.get("STATUS")
        L.append(f"| {e['ELEMENT']} | {e['MATERIAL']} | {h} | {e.get('LENGTH', '-')} |")
    for e in mat["OPEN_ZERO_PLASTER"]:
        L.append(f"| {e['ELEMENT']} | open | PLASTERABLE_SOLID_FACE = {e['PLASTERABLE_SOLID_FACE']} | - |")
    L += ["", f"- Solid upstand under the balustrade: {mat['SOLID_UPSTAND_UNDER_BALUSTRADE']}",
          f"- Horizontal band: {mat['HORIZONTAL_BAND']['STATUS']} ({mat['HORIZONTAL_BAND']['EVIDENCE']})",
          f"- Curved / ogee portion: {mat['CURVED_OGEE_PORTION']}",
          f"- Internal vs external face heights: {mat['INTERNAL_VS_EXTERNAL_FACE_HEIGHTS']}",
          f"- Double count: {mat['PARENT_CHILD']}",
          "", "## CROSS-SHEET RELATIONS", ""]
    for k, v in se["CROSS_SHEET_RELATIONS"].items():
        L.append(f"- {k}: {v}")
    opts = d1["RESIDUAL"]["OPTIONS"]
    qd = d1["RESIDUAL"]["QUANTITY_DIFFERENCE_PER_METRE_RUN_M2"]
    L += ["", "---", "", "# OWNER CARD D1 - SE parapet face basis", "",
          f"D1_STATUS: **{d1['D1_STATUS']}**", "",
          "**WHAT IS UNRESOLVED**: where the facade face ends and the parapet face begins on the "
          "full-height solid portion of the SE roof edge. The face top (+11.10, band underside) is "
          "established; the band is capping (0.20); the lattice is zero; the old 1.22 / 1.42 figures "
          "applied over the 7.10 run are withdrawn.", "",
          f"**SOURCE IMAGE**: `{se['CARD']['IMAGE']}` (original SE elevation page 4, native scan, "
          "hash-verified; B-B cut inset). Green = solid plasterable, orange = open balustrade (zero), "
          "blue = band / capping (provisional), magenta = printed dimension + text, grey = base line.", "",
          "**DIMENSION TRACES**: 155 = tower top -> dome apex; 193 = dome apex -> rail top; "
          "104 = rail top -> base line (balustrade assembly, printed inside the lattice zone); "
          "139 = base line -> window head; 20 = band thickness; 680 = +4.30 -> +11.10 solid face top; "
          "50 (SE) = top link of 100 + 870 + 420 + 50 = 1440 (not a parapet height by proximity); "
          "130 is on B-B only (NW edge, different location).", "",
          f"**OPTION A** - split at the +9.70 slab-top datum: face {opts['A_SPLIT_AT_SLAB_TOP_DATUM_9_70']['FACE_M']} m "
          f"({opts['A_SPLIT_AT_SLAB_TOP_DATUM_9_70']['WHY']}).", "",
          f"**OPTION B** - split at the drawn base line +9.88: face {opts['B_SPLIT_AT_BASE_LINE_9_88']['FACE_M']} m "
          f"({opts['B_SPLIT_AT_BASE_LINE_9_88']['WHY']}).", "",
          f"**QUANTITY DIFFERENCE**: A - B = {qd['A_minus_B']} m2 per metre run of the solid portion; "
          f"the solid portion's length is {d1['RESIDUAL']['LENGTH_STATUS'].split(';')[0]}, so "
          "no established m2 changes today on either option. Estimate v3 impact: "
          f"{d1['ESTIMATE_V3_IMPACT']}.", "",
          f"**WHY THE SOURCE HIERARCHY CANNOT DECIDE**: {d1['RESIDUAL']['WHY_SOURCE_HIERARCHY_CANNOT_DECIDE']}.", "",
          f"**TECHNICAL RECOMMENDATION**: {d1['RESIDUAL']['TECHNICAL_RECOMMENDATION']}.", "",
          "---", "", "## DECISION D2 - resolved provisionally by the source hierarchy", "",
          f"- D2_STATUS: {d2['D2_STATUS']}",
          f"- Classification: {d2['CLASSIFICATION']}",
          f"- Plasterable face: {d2['PLASTERABLE_FACE']}",
          f"- Residual: {d2['RESIDUAL']}",
          f"- Owner decision required: {d2['OWNER_DECISION_REQUIRED']}",
          "", "## DECISION D3 - benchmark identity", "",
          f"- {json.dumps(d3) if not isinstance(d3, dict) else d3.get('D3_STATUS', d3)}",
          "", "## ESTIMATE v3 (unchanged by this check)", "",
          f"- established {ag['ESTABLISHED_SUBTOTAL_M2']} m2, provisional {ag['PROVISIONAL_SUBTOTAL_M2']} m2 "
          "(traced subset; never a total).",
          f"- Frozen outputs rewritten: {se['FROZEN_OUTPUTS_REWRITTEN']}; SALOON work reopened: "
          f"{se['SALOON_WORK_REOPENED']}.",
          "", "---", "", "# Appendix: review v3 (unchanged)", ""]
    return "\n".join(L) + "\n" + build_v3()


if __name__ == "__main__":
    p = OUT / "OWNER_REVIEW_V4.md"
    p.write_text(build(), encoding="utf-8")
    print(json.dumps({"OWNER_REVIEW_V4_SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}))
