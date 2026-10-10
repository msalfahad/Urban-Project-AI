"""OWNER REPORT v7 - the PA03 source-review gate report (directive §29 format).

    python3 -m research.qs_wall_treatment_01.owner_report_v7
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)


def build() -> str:
    void = json.loads((OUT / "VOID_GEOMETRY_RECONCILIATION.json").read_text("utf-8"))
    rv = json.loads((OUT / "RECEPTION_VERTICAL_FACE_REGISTER.json").read_text("utf-8"))
    st = json.loads((OUT / "STAIR_COMPONENT_REGISTER_V2.json").read_text("utf-8"))
    col = json.loads((OUT / "COLUMN_VERTICAL_EXPOSURE_REGISTER.json").read_text("utf-8"))["COLUMNS"][0]
    ne = json.loads((OUT / "NE_ELEVATION_FINISH_ELIGIBILITY_REGISTER.json").read_text("utf-8"))["FACES"][0]
    se = json.loads((OUT / "SE_OPENING_DIMENSION_OWNERSHIP_AUDIT.json").read_text("utf-8"))
    sl = json.loads((OUT / "PA02_SOURCE_REVIEW_SUPERSESSION_LEDGER.json").read_text("utf-8"))
    qa = json.loads((OUT / "QA_RENDER_VALIDITY_REGISTER.json").read_text("utf-8"))
    dep = json.loads((OUT / "PA03_DEPENDENT_QUANTITIES.json").read_text("utf-8"))
    a22 = json.loads((OUT / "A22_RECONCILIATION_REGISTER_v6.json").read_text("utf-8"))
    gate = json.loads((OUT / "PA03_GATE.json").read_text("utf-8"))
    objs = void["OBJECTS_PRESERVED"]
    elem = st["STAIRS"][1]["MID_ELEMENT"]
    L = ["# P7757 - owner report v7 (PA03 source-review gate)", "",
         "PHASE: PA03 - forward source-review / correction layer over PA02 (void reconciliation, reception vertical faces, double-height status, 10 cm stair element, stair face sets, D2 column exposed height, NE elevation eligibility, SE opening ownership audit, QA render validity)",
         f"STATUS: correction layer frozen; no historical freeze rewritten; owner queue rebuilt to {len(gate['OWNER_DECISION_QUEUE_V3'])} items, none blocking", "",
         "## SOURCE-REVIEW CORRECTIONS", ""]
    for e in sl["ENTRIES"]:
        if e["STATUS"] in ("REOPENED", "WITHDRAWN", "SUPERSEDED", "QUALIFIED"):
            L.append(f"- {e['ITEM']} {e['STATUS']}: {e['PA02_STATEMENT']} -> {e['REPLACED_OR_QUALIFIED_BY']}")
    L += ["", "## WHAT PA02 REMAINED VALID", ""]
    for e in sl["ENTRIES"]:
        if e["STATUS"] in ("UNCHANGED", "CONFIRMED", "CONFIRMED_AND_NARROWED", "CONFIRMED_IN_PART", "CONFIRMED_AS_DERIVED_PROVISIONAL"):
            L.append(f"- {e['ITEM']} {e['STATUS']}: {e['PA02_STATEMENT']}" + (f" ({e['REPLACED_OR_QUALIFIED_BY']})" if e["REPLACED_OR_QUALIFIED_BY"] else ""))
    L += ["", "## WHAT WAS REOPENED", ""]
    for e in sl["ENTRIES"]:
        if e["STATUS"] in ("REOPENED", "WITHDRAWN"):
            L.append(f"- {e['ITEM']} {e['STATUS']}: {e['PA02_STATEMENT']}")
    L += ["", "## VOID RECONCILIATION", "",
          f"- PRINTED_VOID_WIDTH 5.87 / PRINTED_VOID_DEPTH 4.00: both are authored DWG dimension entities (geometry 5870 / 4000, no text override), not raster-only readings.",
          f"- WIDTH: {void['RECONCILIATION']['WIDTH']['CLASSIFICATION']} - {void['RECONCILIATION']['WIDTH']['EXPLANATION']}",
          f"- DEPTH: {void['RECONCILIATION']['DEPTH']['CLASSIFICATION']} - {void['RECONCILIATION']['DEPTH']['EXPLANATION']}",
          "", "| object | width m | depth m | area m2 | basis | state |", "|---|---|---|---|---|---|"]
    for k, o in objs.items():
        L.append(f"| {k} | {o['WIDTH_M']} | {o['DEPTH_M']} | {o.get('AREA_M2', round(o['WIDTH_M'] * o['DEPTH_M'], 3))} | {o['BASIS']} | {o['QUANTITY_STATE']} |")
    L += ["", f"- structural p4 'Open To Below' X: {objs['SLAB_OPENING']['STRUCTURAL_P4_X_M'][0]} x {objs['SLAB_OPENING']['STRUCTURAL_P4_X_M'][1]} m (independent author, agrees with the architectural X).",
          "- Neither value is averaged or substituted; PA02's 5.82 x 2.75 named the SLAB_OPENING only.",
          "", "## RECEPTION VERTICAL MODEL", "",
          f"- Section coverage: {rv['SECTION_CUT_RELATIONSHIP']['CONSEQUENCE']}.",
          f"- DOUBLE_HEIGHT_WALL_STATUS = {rv['DOUBLE_HEIGHT']['DOUBLE_HEIGHT_WALL_STATUS']}; candidate edges {rv['DOUBLE_HEIGHT']['CANDIDATE_EDGES']}; L-10_STATUS = {rv['L-10_STATUS']}.",
          "", "| edge | length m | GF face | FF face | opening | wall continues | railing FF | open | stair | column | status |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in rv["EDGES"]:
        L.append(f"| {e['EDGE_ID']} | {e['LENGTH_M']} | {e['GROUND_FLOOR_PHYSICAL_FACE'][:70]} | {e['FIRST_FLOOR_PHYSICAL_FACE'][:70]} | {e['VOID_FLOOR_OPENING']} | {e['WALL_CONTINUES_VERTICALLY']} | {e['RAILING_AT_FIRST_FLOOR']} | {e['OPEN_EDGE']} | {e['STAIR_EDGE']} | {e['COLUMN']} | {e['STATUS'][:60]} |")
    L += ["", "| face | plan edge | start | top | continues to FF | above FF | open to void | length m | height | state |", "|---|---|---|---|---|---|---|---|---|---|"]
    for f in rv["VERTICAL_FACES"]:
        L.append(f"| {f['FACE_ID']} | {f['PLAN_EDGE']} | {f['GROUND_START_LEVEL']} | {f['TOP_LEVEL']} | {f['CONTINUES_TO_FIRST_FLOOR']} | {f['CONTINUES_ABOVE_FIRST_FLOOR']} | {f['OPEN_TO_VOID']} | {f['LENGTH_M']} | {f['HEIGHT']['VALUE_M']} ({f['HEIGHT']['STATE']}) | {f['QUANTITY_STATE']} |")
    L += ["", "## STAIR MODEL", "",
          f"- Main curved stair: curved flight (arcs r 1.53-2.78), straight flight along the NE wall ({objs['STRAIGHT_FLIGHT_STRIP']['TREADS']} treads x 0.30 in a 1.15 strip), a short run in the east strip (PROPOSED), railings zero plaster; the only wall faces are RVF-S-B and RVF-W-FF (NOT_ESTABLISHED).",
          f"- Block stair: printed 120 + 10 + 120 x 645 kept (authored DWG dimensions). 10 cm element ROLE = {elem['ROLE']}; excluded: {'; '.join(elem['EXCLUDED_ROLES'])}; remaining: {', '.join(elem['CANDIDATE_ROLES_REMAINING'])}; plaster eligibility {elem['PLASTER_WALL_ELIGIBILITY']}.",
          f"- Block stair faces: 12 faces with exposure / openings / railing / landing / occlusion fields; per-storey reference gross {st['STAIRS'][1]['STOREY_REFERENCE_GROSS_M2']} m2 is GEOMETRIC_REFERENCE_ONLY (not a quantity, never perimeter x storey).",
          "", "## COLUMN HEIGHT MODEL", "",
          f"- COLUMN_EXPOSED_GIRTH_LM = {col['COLUMN_EXPOSED_GIRTH_LM']['VALUE']} ({col['COLUMN_EXPOSED_GIRTH_LM']['STATE']}; 0.85 on the structural 300 depth; PA02's 1.80 superseded: walls CAD-822 / 823 abut the W face, CAD-783 covers 150 of the E face; the S face is external).",
          f"- COLUMN_EXPOSED_HEIGHT_M = {col['COLUMN_EXPOSED_HEIGHT_M']['VALUE']} ({col['COLUMN_EXPOSED_HEIGHT_M']['STATE']}): " + "; ".join(col["COLUMN_EXPOSED_HEIGHT_M"]["EVIDENCE"]) + ".",
          f"- COLUMN_BONDING_AREA_M2 = {col['COLUMN_BONDING_AREA_M2']['VALUE']} ({col['COLUMN_BONDING_AREA_M2']['STATE']}); OWNER_PARAMETRIC {col['OWNER_PARAMETRIC_AREA_M2']['VALUE']} m2 labelled parametric, not physical. {col['PA02_5_76_STATUS']}",
          "", "## NEW / CHANGED QUANTITIES (per line; states; never a total)", "", "| line | unit | value | state | supersedes |", "|---|---|---|---|---|"]
    for l in dep["LINES"]:
        L.append(f"| {l['LINE_ID']} | {l['UNIT']} | {l['VALUE']} | {l['QUANTITY_STATE']} | {l['SUPERSEDES'] or '-'} |")
    c = dep["CEILING_EXCLUSION_INFORMATIONAL"]
    L += ["", f"- Ceiling exclusion (informational, computed after the void freeze): zone {c['VOID_STAIR_ZONE_M2']} m2, slab opening {c['SLAB_OPENING_M2']} m2, flight strip {c['STRAIGHT_FLIGHT_STRIP_M2']} m2, curved flight footprint {c['CURVED_FLIGHT_FOOTPRINT_M2_PROVISIONAL']} m2 (PROVISIONAL).",
          "", "## SE OPENING OWNERSHIP AUDIT", "", "| dim | printed | owner | witness | status |", "|---|---|---|---|---|"]
    for d in se["DIMENSIONS"]:
        L.append(f"| {d['DIM_ID']} | {d['PRINTED_VALUE']} | {d['OWNER']} | {d['WITNESS_FROM']} -> {d['WITNESS_TO']} | {d['STATUS']} |")
    L += ["", f"- {se['PA02_OPENING_STATUS']}.", "", "## NE ELEVATION", "",
          f"- ELEVATION_SOURCE_EXISTS = {ne['ELEVATION_SOURCE_EXISTS']} ({ne['ELEVATION_PAGE']}); FINISH_SYSTEM_ESTABLISHED = {ne['FINISH_SYSTEM_ESTABLISHED']}; SOLID_FACE_TOP {ne['SOLID_FACE_TOP_STATUS']['STATUS']}; BAND_EXISTS {ne['BAND_EXISTS_STATUS']['STATUS']}; BAND_HEIGHT {ne['BAND_HEIGHT_STATUS']['STATUS']} ({ne['BAND_HEIGHT_STATUS']['VALUE_M']}); BAND_TRADE_ROLE {ne['BAND_TRADE_ROLE']['STATUS']}; state {ne['QUANTITY_STATE']}.",
          f"- {ne['PA02_QUEUE_WORDING_WITHDRAWN']}",
          "", "## QA RENDER VALIDITY", "", "| image | kind | ink | target visible | validity |", "|---|---|---|---|---|"]
    for r in qa["SOURCE_CROPS"] + qa["DERIVED_QA_OVERLAYS"]:
        L.append(f"| {r['IMAGE']} | {r['KIND']} | {r['INK_FRACTION']} | {r['TARGET_VISIBLE']} | {r['VALIDITY']} |")
    L += ["", f"- {qa['NE_BAND_CLAIM']}", "", "## A22 FINDINGS (incremental v6, conditional IF_BENCHMARK_IS_P7757)", ""]
    for i in a22["ITEMS"]:
        if "ENGINEERING" in i:
            L.append(f"- {i['ITEM_ID']}: engineering {i['ENGINEERING']} vs contractor {i['CONTRACTOR']} -> {i['CLASS']}. {i.get('NOTE') or ''}")
        else:
            L.append(f"- {i['ITEM_ID']}: {i.get('CLASS') or i.get('CONSEQUENCE')}; {i['SOURCE_INDEPENDENCE'] if 'SOURCE_INDEPENDENCE' in i else i.get('SOURCE_DEPENDENCE')}")
    L += ["", "## COVERAGE", "", "| floor | zone | trade | status |", "|---|---|---|---|"]
    for r in dep["COVERAGE_MATRIX_ROWS_CORRECTED"]:
        L.append(f"| {r['FLOOR']} | {r['ZONE']} | {r['TRADE']} | {r['COVERAGE_STATUS']} |")
    L += ["", "Other PA02 coverage rows unchanged (TRADES_WET_OPENINGS_FLOORS_COVERAGE.json). A subtotal is not a project total.",
          "", "## OWNER DECISIONS STILL REQUIRED", "", "Withdrawn / rewritten: " + "; ".join(gate["WITHDRAWN_FROM_QUEUE"]) + ". D3 is kept open, not re-asked.", ""]
    for n, d in enumerate(gate["OWNER_DECISION_QUEUE_V3"], 1):
        L += [f"**{n}. {d['DECISION_ID']}** ({d['PRIORITY']})", f"- location: {d['LOCATION']}", f"- card: {d['VISUAL_CARD']}",
              f"- known: {'; '.join(d['AVAILABLE_EVIDENCE'])}", f"- unknown: {d['QUESTION']}", f"- why sources cannot decide: {d['WHY_SOURCE_HIERARCHY_FAILED']}",
              f"- A: {d['OPTION_A']}", f"- B: {d['OPTION_B']}" + (f"; C: {d['OPTION_C_IF_REQUIRED']}" if d.get("OPTION_C_IF_REQUIRED") else ""),
              f"- impact: {d['QUANTITY_IMPACT_IF_KNOWN']}; blocks: {d['BLOCKS_WHAT']}", f"- recommendation: {d.get('TECHNICAL_RECOMMENDATION') or '-'}", ""]
    L += ["## NEXT AUTOMATIC PHASE", "",
          "Work that does not depend on the reception / void model: first-floor room faces (DWG FF copy chains), wet-room lengths on the FF, external opening netting on the NE / NW facades, the annex parapet run, "
          "the remaining roof edges, the block-stair face deductions once the element role and landing geometry are read, beam depths from the structural schedules (T-BEAM-DEPTHS) for the column and the overhanging faces; "
          "incremental A22 on each; contractor basis parallel; nothing priced, no total."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    p = OUT / "OWNER_REPORT_V7.md"
    p.write_text(build(), encoding="utf-8")
    print(json.dumps({"OWNER_REPORT_V7_SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}))
