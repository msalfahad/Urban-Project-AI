"""PA04 report (directive §21 format) plus the FABLE_RECOMMENDATIONS,
PARALLELISM_RECOMMENDATION and PROJECT_3_ENTRY_CRITERIA artifacts.

    python3 -m research.qs_wall_treatment_01.pa04.report_v8
"""

from __future__ import annotations

import hashlib
import json

from research.qs_wall_treatment_01.pa04 import common as C

RECOMMENDATIONS = {
    "1_WORKING_BEST": "the source-hierarchy discipline (DWG entity ids > printed dims > raster > interpretation) with forward-only supersession ledgers: every PA02 error was correctable without rewriting history, and the DWG jamb lines settled a three-way disagreement on the NW window height in one deterministic query.",
    "2_BIGGEST_SYSTEMIC_WEAKNESS": "semantic identity (room names, beam labels, 'what object is this') still comes from visual reads of rasters; the DWG FF copy has no room text, the structural PDF has no text layer, so identity is the least reproducible layer and it sits under every trade quantity.",
    "3_REDESIGN_BEFORE_PROJECT_3": "a project ingestion contract: (a) stable geometric ids (anchor-keyed regions, entity handles) instead of run-order ids; (b) a frozen, hashed challenge kit assembled before any reader is spawned; (c) a sheet-role classifier (plan / elevation / section-elevation / schedule) so a cut ground storey is never read as a facade; (d) one register schema with mandatory SOURCE / STATE / UNIT / OWNER fields validated by the self-checks at write time, not after.",
    "4_AI_TASK_TO_REPLACE_WITH_CODE": "reading printed dimension chains on native crops (witness ownership): the DWG already carries authored dimension entities for both plans and the NW elevation; a chain-walker over dimension entities plus jamb / sill line detection replaces the orchestrator's crop reads for every sheet that has a DWG behind it.",
    "5_DETERMINISTIC_TASK_THAT_NEEDS_AI_REVIEW": "region merging (OPEN_GROUP): the flood fill cannot tell a missing door leaf from a genuinely open edge; a reader looking at the printed sheet can (it saw the two bedroom door arcs the DWG D layer lacks). Route every region that spans more than one printed label to a reader.",
    "6_RULES_FOR_URBAN_STANDARDS": ["floor opening and wall continuity are separate variables", "printed vs CAD reconciled by class, never averaged", "a QA overlay is never source", "open lattice = zero plaster; kerb separate", "girth, exposed height and area are three records", "ceiling starts from floor and deducts, never equals", "no global plaster height; scoped parameter table", "openings: actual overrides default, default never overwrites actual"],
    "7_RULES_THAT_STAY_P7757": ["3.20 m GF plaster height (owner project input)", "door 1.00 x 2.20 / window 1.50 x 1.50 temporary defaults", "half opening deduction / 3.60 / 3.40 / 12.90 contractor rules", "the +9.70 / +9.88 dual basis", "the SE roof-edge split at CAD-4808"],
    "8_SOURCE_WITH_GREATEST_UNRESOLVED_REDUCTION": "a finishes schedule (room-by-room wall finish and tile height) - it would turn every FF lm, every wet-room lm, the NE / NW / SE geometric faces and the parapet faces from lm / GEOMETRIC_REFERENCE_ONLY into areas; second: a section or stair detail through the reception opening (double-height category, ~17-45 m2).",
    "9_NEXT_3_PHASES": ["PA05 ingestion contract + DWG dimension-chain walker + sheet-role classifier (code, no new quantities)", "PA06 finish-eligibility layer: apply the owner's answers (FF height, external finish, tile height) as parameters and produce area lines with states; A22 on each", "PA07 blind Project-3 dry run on P7757 itself (fresh session, no artifacts) to measure reproducibility before a real Project 3"],
    "10_DISAGREEMENTS_WITH_INSTRUCTIONS": [
        "'Separate agents where useful' at STAGE A: for geometry extraction a second AI reader adds cost without independence (same drawings, same failure modes); keep AI for identity / semantics and cold challenge only.",
        "'Do not return to the owner after every small task' conflicts with 'cold challenge for any new room identity': room identity on the FF depends on the printed sheet only, so the owner (or a finishes schedule) is the cheaper authority than a second AI read; batch the identity questions into one owner card instead of a challenger pass.",
        "The 8 self-checks are mechanical and pass trivially when fields exist; the failures that matter (merged regions, cut storeys, label correspondence) are semantic and had to be written by hand. Replace SOURCE_COMPLETENESS / PROVENANCE with schema validation at write time and keep a separate 'semantic findings' list per workstream.",
        "Counting AI calls / deterministic ops as a performance metric measures activity, not value; the useful metric is 'quantity state upgraded per owner decision' and 'components moved out of NOT_ESTABLISHED per source obtained'.",
        "Running the architecture review after the freeze is right, but it should read the freeze manifests and metrics, not the invariants alone; otherwise it reviews intentions."],
}
PARALLELISM = {
    "SAFE_TO_PARALLELIZE": [{"TASK": "per-floor region / face extraction (GF, FF, ROOF copies)", "WHY": "independent plan copies, deterministic"},
                            {"TASK": "facade openings per elevation (SE, NE, NW)", "WHY": "different sheets; only the roof-edge register joins them later"},
                            {"TASK": "cold-challenge readers (reception, facades, rooms)", "WHY": "read-only over frozen kits; reconciliation is a serial join afterwards"},
                            {"TASK": "profile register, treatment sequences, height table", "WHY": "pure transforms of frozen registers"}],
    "PARALLELIZE_WITH_FREEZE_BARRIER": [{"TASK": "opening register v2 <- SE audit + NW facades + door arcs", "BARRIER": "facade registers frozen first"},
                                        {"TASK": "ceiling / floor regions <- room regions + PA03 void objects", "BARRIER": "void reconciliation and region extraction frozen"},
                                        {"TASK": "A22 increments <- each workstream", "BARRIER": "the workstream's register frozen"},
                                        {"TASK": "coverage / queue / report", "BARRIER": "all registers frozen"}],
    "MUST_BE_SERIAL": [{"TASK": "reception vertical model -> beam schedule -> overhanging faces -> double-height quantities", "WHY": "each step changes the face bottoms the next step uses"},
                       {"TASK": "region ids -> identity map -> challenge kit -> reconciliation", "WHY": "the kit must be frozen after the ids are stable (this batch broke it once)"},
                       {"TASK": "height parameters -> any area line", "WHY": "areas are meaningless before the scope's height exists"},
                       {"TASK": "owner answers -> finish eligibility -> trade areas", "WHY": "eligibility is an input to every area state"}],
}
PROJECT_3 = {
    "GEOMETRY": ["DWG decoded with entity handles preserved; three plan copies auto-detected (offset vector found by column-loop matching, not hand-coded)", "regions keyed by CAD anchors; door closure from swing arcs validated on >= 95 % of printed door arcs", "developed lengths for every arc / polyline; no bbox anywhere (test)"],
    "SEMANTIC_SAFETY": ["sheet-role classifier with a test set (plan / elevation / section-elevation / schedule / detail)", "room identity from DWG TEXT where present, else one owner card per floor; no AI-only identity in production", "every 'object X is Y' claim carries EXISTENCE / EXPOSURE / OWNERSHIP as three fields"],
    "MEASUREMENT_REGIONS": ["physical / topological / QS-measurement / trade layers enforced by schema", "virtual closures stamped MATERIAL_PRESENT=False", "ceiling and floor regions derived, never copied"],
    "TRADE_RULES": ["owner parameter table per scope with revision ids; no hard-coded heights", "treatment sequences per face kind; area counted once", "contractor rulebook kept as a parallel basis, never merged"],
    "SOURCE_COVERAGE": ["source inventory with role, page, text-layer availability and what each sheet cannot show", "a 'requested sources' list generated from NOT_ESTABLISHED states"],
    "QA_SAMPLING": ["render validity register on every crop; NOT_INFORMATIVE renders cannot support claims", "a fixed blind sample (e.g. 10 faces per floor) re-read cold after the freeze and scored against the registers"],
    "BENCHMARK_ISOLATION": ["benchmark figures sealed until the geometry freeze; leakage scan on every geometry artifact; A22 conditional on identity"],
    "OWNER_INPUT_SYSTEM": ["decision queue with dedupe, grouping, quantity impact and a stop gate; answers enter as parameters with revision ids, never as edits to registers"],
    "PERFORMANCE": ["a full deterministic rerun of a project under 10 minutes; AI readers only for identity / challenge; metrics reported as states upgraded per decision"],
    "ENTRY_TEST": "run PA01-PA04 on P7757 in a fresh session with no artifacts and reproduce the frozen registers' established lengths within 1 % before opening Project 3",
}


def build():
    ff = C.read("FF_PHYSICAL_FACE_REGISTER.json"); wet = C.read("WET_ROOM_REGISTER_V2.json"); fac = C.read("FACADE_OPENINGS_NE_NW_PRIMARY.json"); roof = C.read("ROOF_EDGE_REGISTER_V2.json")
    st = C.read("STAIR_GEOMETRY_V3.json"); stx = C.read("STRUCTURAL_EXPOSURE_REGISTER.json"); cc = C.read("COLD_CHALLENGE_RECONCILIATION.json"); sc = C.read("PA04_SELF_CHECKS.json")
    a22 = C.read("A22_RECONCILIATION_REGISTER_v7.json"); cov = C.read("COVERAGE_PA04.json"); q = C.read("OWNER_DECISION_QUEUE_V4.json"); m = C.read("PA04_METRICS.json")
    op = C.read("OPENING_REGISTER_V2.json"); pf = C.read("PROFILE_STEEL_REGISTER_V2.json"); ceil = C.read("CEILING_MEASUREMENT_REGION_REGISTER.json"); ht = C.read("HEIGHT_PARAMETER_TABLE.json")
    L = ["# P7757 - PA04 MULTI_DOMAIN_QS_EXPANSION report", "", "PHASE: PA04 - seven workstreams (A-G), ceiling / floor regions, openings v2, profiles v2, treatment sequences, height table, cold challenges, A22 v7, coverage, queue v4",
         "STATUS: all workstreams run and self-checked; three cold challenges reconciled; quantities frozen (FREEZE_PA04); PA03 preserved unchanged", "",
         "## WORKSTREAM RESULTS A-G", "",
         f"- A: {len(ff['ROOMS'])} FF regions with faces; by class: " + "; ".join(f"{k}: {v['ROOMS']} rooms, host wall {v['HOST_WALL_LM']} lm" for k, v in ff["BY_ROOM_CLASS"].items()) + ". Areas not computed (FF height NOT_ESTABLISHED).",
         f"- B: {len(wet['ROOMS'])} wet rooms project-wide; host-wall lm by floor {wet['TOTALS']['GROSS_HOST_WALL_LM_BY_FLOOR']}; tile height / area NOT_ESTABLISHED.",
         f"- C: NW openings from authored DWG dims: " + "; ".join(f"{o['OPENING_ID']} {o['WIDTH_M']} x {o['HEIGHT_M']} ({o['AREA_M2']} m2, {o['CONFIDENCE']})" for o in fac["NW_OPENINGS"]) + f". NW faces: " + "; ".join(f"{f['FACE_ID']} gross {f['GROSS_GEOMETRIC_FACE_M2']} net {f['NET_GEOMETRIC_FACE_M2']}" for f in fac["NW_FACADE_FACES"]) + ". NE: raster only, no printed opening dimensions. Sheets 6 / 7 are section-elevations (GF cut). All GEOMETRIC_REFERENCE_ONLY.",
         f"- D: six roof edges with the full field set: " + "; ".join(f"{e['EDGE_ID']}: {e['STATUS']}" for e in roof["EDGES"]) + ".",
         f"- E: main stair {st['STAIRS'][0]['COMPONENTS']['TREAD']['TOTAL_TREADS']} treads, riser {st['STAIRS'][0]['COMPONENTS']['RISER']['HEIGHT_M']} (PROVISIONAL), soffits {st['STAIRS'][0]['COMPONENTS']['SOFFIT']['CURVED_M2']} / {st['STAIRS'][0]['COMPONENTS']['SOFFIT']['STRAIGHT_M2']} / {st['STAIRS'][0]['COMPONENTS']['SOFFIT']['EAST_RUN_M2']} m2 PROVISIONAL; block stair per storey {st['STAIRS'][1]['PER_STOREY']['GF']['RISERS']} risers; 10 cm element role UNRESOLVED, plaster eligibility UNKNOWN.",
         f"- F: beam schedules read (simple + continuous); CB7 20x75 over the D2 column line -> exposed height {stx['D2_COLUMN']['COLUMN_EXPOSED_HEIGHT_M']['VALUE']} PROVISIONAL, bonding area {stx['D2_COLUMN']['COLUMN_BONDING_AREA_M2']['VALUE']} m2 PROVISIONAL; CB6 20x75 on the opening's north edge (new candidate beam face); P.C 20x70 at the garden opening (LOW).",
         f"- G: cold challenge on the reception: {cc['RECEPTION']['STATUS']}; agreed edges {cc['RECEPTION'].get('EDGES_AGREED')}; unresolved {cc['RECEPTION'].get('EDGES_UNRESOLVED')}; faces: {cc['RECEPTION']['VERTICAL_FACE_MODEL_V2']}.",
         "", "## SELF-CHECK FAILURES FOUND", ""]
    for f in sc["SEMANTIC_FAILURES_RECORDED"]:
        L.append(f"- [{f['WORKSTREAM']}] {f['CHECK']}: {f['FINDING']}")
    L += [f"- mechanical checks: {'all pass' if sc['ALL_MECHANICAL_PASS'] else 'failures ' + str({k: v['FAILED'] for k, v in sc['BY_WORKSTREAM'].items() if v['FAILED']})}", "", "## COLD-CHALLENGE FINDINGS", ""]
    for it in cc["RECEPTION"]["ITEMS"]:
        L.append(f"- reception {it['ITEM_ID']}: {it['STATUS']}; open fields {it['OPEN_FIELDS']}; challenger: {str(it['NOTE'].get('CHALLENGER_FF'))[:140]}")
    for it in cc["FACADES"].get("NW_ITEMS", []):
        L.append(f"- facade {it['ITEM_ID']}: {it['STATUS']}; open {it['OPEN_FIELDS']}")
    L.append(f"- facade NE: challenger listed {len(cc['FACADES'].get('NE_CHALLENGER_ELEMENTS', []))} elements, none with a printed dimension; finish notes drawn: {cc['FACADES'].get('NE_FINISH_NOTES_DRAWN')}")
    L.append(f"- FF rooms: {len(cc['FF_ROOMS'].get('AGREED', []))} agreed, {len(cc['FF_ROOMS'].get('OPEN', []))} open; {cc['FF_ROOMS'].get('PROCESS_FINDING')}")
    L += ["", "## NEW QUANTITIES AVAILABLE (states; never a total)", "", "| item | unit | value | state |", "|---|---|---|---|"]
    for k, v in ff["BY_ROOM_CLASS"].items():
        L.append(f"| FF {k} host-wall faces ({v['ROOMS']} regions) | lm | {v['HOST_WALL_LM']} | SOURCE_ESTABLISHED (identity PROVISIONAL) |")
    for fl, v in wet["TOTALS"]["GROSS_HOST_WALL_LM_BY_FLOOR"].items():
        L.append(f"| wet-room host walls {fl} | lm | {v} | {'SOURCE_ESTABLISHED' if fl == 'GF' else 'PROVISIONAL'} |")
    L += [f"| D2 column exposed height / bonding area | m / m2 | {stx['D2_COLUMN']['COLUMN_EXPOSED_HEIGHT_M']['VALUE']} / {stx['D2_COLUMN']['COLUMN_BONDING_AREA_M2']['VALUE']} | PROVISIONAL |",
          f"| NW FF windows (3) + tower arch + GF screen | m2 | {round(sum(o['AREA_M2'] for o in fac['NW_OPENINGS']), 3)} | GEOMETRIC_REFERENCE_ONLY |",
          f"| NW facade FF faces gross / net | m2 | {sum(f['GROSS_GEOMETRIC_FACE_M2'] or 0 for f in fac['NW_FACADE_FACES'])} / {sum(f['NET_GEOMETRIC_FACE_M2'] or 0 for f in fac['NW_FACADE_FACES'])} | GEOMETRIC_REFERENCE_ONLY |",
          f"| main stair soffits (3 flights) | m2 | {round(sum(v for v in (st['STAIRS'][0]['COMPONENTS']['SOFFIT']['CURVED_M2'], st['STAIRS'][0]['COMPONENTS']['SOFFIT']['STRAIGHT_M2'], st['STAIRS'][0]['COMPONENTS']['SOFFIT']['EAST_RUN_M2']) if v), 3)} | PROVISIONAL |",
          f"| annex parapet plan run (wall-bounded) | lm | {roof['EDGES'][4]['PLAN_RUN_LENGTH']['WALL_BOUNDED_M']} | SOURCE_ESTABLISHED (height NOT_ESTABLISHED) |",
          f"| profile steel | lm | {pf['TOTAL_LM_BY_STATE']} | by state |",
          f"| openings register v2 | nr | {op['COUNT']} | mixed |",
          f"| ceiling regions with net geometry | nr | {sum(1 for z in ceil['ZONES'] if z['NET_CEILING_GEOMETRY_M2'] > 0)} | GEOMETRY_ONLY |",
          "", "## A22 FINDINGS (v7, field by field, conditional IF_BENCHMARK_IS_P7757)", ""]
    for i in a22["ITEMS"]:
        L.append(f"- {i['ITEM_ID']}: {i['CLASS']}; " + "; ".join(f"{f['FIELD']} {f['VERDICT']}" for f in i["FIELDS"]) + f". {i.get('NOTE') or ''}")
    L += ["", "## COVERAGE (component counts by state)", "", "| floor | trade | zone | SE | OP | PR | NE | NS |", "|---|---|---|---|---|---|---|---|"]
    for r in cov["ROWS"]:
        L.append(f"| {r['FLOOR']} | {r['TRADE']} | {r['ZONE'][:40]} | {r['SOURCE_ESTABLISHED']} | {r['OWNER_PARAMETRIC']} | {r['PROVISIONAL']} | {r['NOT_ESTABLISHED']} | {r['NOT_STARTED']} |")
    L += [f"| TOTAL | | | {cov['TOTAL_COMPONENT_COUNTS']['SOURCE_ESTABLISHED']} | {cov['TOTAL_COMPONENT_COUNTS']['OWNER_PARAMETRIC']} | {cov['TOTAL_COMPONENT_COUNTS']['PROVISIONAL']} | {cov['TOTAL_COMPONENT_COUNTS']['NOT_ESTABLISHED']} | {cov['TOTAL_COMPONENT_COUNTS']['NOT_STARTED']} |",
          "", "No combined accuracy score is produced.", "", "## OWNER DECISIONS REMAINING (v4, grouped, none blocking)", ""]
    for d in q["QUEUE"]:
        L += [f"**{d['DECISION_ID']}** [{d.get('GROUP')}] ({d['PRIORITY']}): {d['QUESTION']}", f"- impact: {d['QUANTITY_IMPACT_IF_KNOWN']}", f"- recommendation: {d.get('TECHNICAL_RECOMMENDATION') or '-'}", ""]
    L += ["## FABLE_RECOMMENDATIONS", ""]
    for k, v in RECOMMENDATIONS.items():
        L.append(f"- {k}: " + (v if isinstance(v, str) else "; ".join(v)))
    L += ["", "## PARALLELISM_RECOMMENDATION", ""]
    for k, v in PARALLELISM.items():
        L.append(f"- {k}: " + "; ".join(f"{x['TASK']} ({x.get('WHY') or x.get('BARRIER')})" for x in v))
    L += ["", "## PROJECT_3_ENTRY_CRITERIA", ""]
    for k, v in PROJECT_3.items():
        L.append(f"- {k}: " + (v if isinstance(v, str) else "; ".join(v)))
    L += ["", "## HEIGHT PARAMETER TABLE", "", "| scope | value | status |", "|---|---|---|"] + [f"| {p['SCOPE']} | {p['VALUE']} | {p['STATUS']} |" for p in ht["PARAMETERS"]]
    L += ["", "## METRICS", "", f"- runtime per workstream (s): { {k: v.get('RUNTIME_S') for k, v in m['PER_WORKSTREAM'].items()} }", f"- AI calls: {m['AI_CALLS']}", f"- deterministic operations: {m['DETERMINISTIC_OPERATIONS']}",
          f"- owner decisions: {m['OWNER_DECISIONS']}", f"- source requests: {m['SOURCE_REQUESTS']}", f"- artifacts: {len(m['ARTIFACTS_WRITTEN'])}", "",
          "## NEXT 3 PHASES", ""] + [f"- {p}" for p in RECOMMENDATIONS["9_NEXT_3_PHASES"]]
    return "\n".join(L) + "\n"


def run():
    C.write("FABLE_RECOMMENDATIONS.json", {"ARTIFACT": "FABLE_RECOMMENDATIONS", "RECOMMENDATIONS": RECOMMENDATIONS, "PARALLELISM_RECOMMENDATION": PARALLELISM})
    C.write("PROJECT_3_ENTRY_CRITERIA.json", {"ARTIFACT": "PROJECT_3_ENTRY_CRITERIA", "CRITERIA": PROJECT_3, "PROJECT_3_STARTED": False})
    p = C.OUT4 / "OWNER_REPORT_V8.md"
    p.write_text(build(), encoding="utf-8")
    return {"OWNER_REPORT_V8_SHA256": hashlib.sha256(p.read_bytes()).hexdigest()[:16]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
