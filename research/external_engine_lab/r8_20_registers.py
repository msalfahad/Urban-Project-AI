"""R8.20 lab registers: human closure reviews, the I1471 construction rationale, the release re-evaluation, the quantity
regression, the corrected BOQ shadow report + its XLSX view, the source-anchor plan, the donor review, the PDF roadmap,
the second-project plan and the production gates - every value from the r8_20_qortuba build (no number typed in).
"""

from __future__ import annotations

import datetime
import json
import tempfile
from pathlib import Path

import r8_19_registers as R19G
import r8_20_qortuba as Q
from engine import boq_xlsx as BX
from engine.source import boq_evidence as BE, boq_report as BR, closure_release as CR
from engine.source import closure_review as RV, owner_facts as OF, source_anchor as SA

ROOT = Path(__file__).resolve().parents[2]
GATES = {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO", "PRODUCTION_MIGRATION": "NO"}
REG19 = ROOT / "tests/r8_19/registers"
CREATED = datetime.datetime(2026, 10, 2)
DO_NOT_ASK = ["H2430 / H2431 closure review", "I1471 closure review", "I1471 150 / 200 mm wall geometry",
              "I1471 200 mm wall rationale", "column finish", "duct finish", "skirting", "sliding glass door", "marble",
              "wall heights already established"]


def jl(p):
    return json.loads(Path(p).read_text())


def boq20(regs19):
    sh, items = regs19["BOQ_REPORT_SHADOW"], regs19["BOQ_REPORT_SCHEMA"]["items"]
    ev = [dict(e, unresolved=BE.unresolved(e["blockers"], e["unresolved"])) for e in sh["evidence_rows"]]
    rep = BR.build(ev, items, run=sh["report"]["run"])
    val = BR.validate(rep, ev, items)
    before = {r["evidence_row"]: r["STATUS"] for r in sh["report"]["rows"] if r["ROW_KIND"] == "TOTAL"}
    after = {r["evidence_row"]: r["STATUS"] for r in rep["rows"] if r["ROW_KIND"] == "TOTAL"}
    changed = {k: {"R8.19": before[k], "R8.20": after[k]} for k in after if before[k] != after[k]}
    return ev, items, rep, val, changed


def xlsx(rep):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "URBAN_QTO_R8_20_SHADOW_BOQ.xlsx"
        w = BX.write(rep, p, created=CREATED)
        v = BX.validate(p, rep)
    return w, v


def registers(ctx):
    regs19, _ = R19G.registers(ctx)
    cl = ctx["closures_20"] = Q.closures(regs19["CLOSURE_RELEASE_STATUS"])
    rec = jl(ROOT / "research/external_engine_lab/r8_20_recommendation.json")
    ev, items, rep, val, changed = boq20(regs19)
    w, xv = xlsx(rep)
    fact, binding = ctx["i1471_fact"], ctx["i1471_fact_binding"]
    reviews = jl(ROOT / "data/registry/OWNER_CLOSURE_REVIEWS.json")
    regs = {}
    # ------------------------------------------------------------------ owner side
    regs["OWNER_ACTION_REGISTER"] = {
        "SCHEMA": "URBAN_OWNER_ACTION_REGISTER_V17",
        "headline": "ONE RECOMMENDED OWNER ACTION: A CONTROLLED AUTOCAD RE-EXPORT OF THE QORTUBA DWG (CLOSES THE SOURCE "
                    "ANCHOR; ENABLES CROSS-ROUTE AGREEMENT). NO QUESTION ABOUT THE MEASURED ROWS.",
        "required_now": [],
        "recommended_now": [{"id": "QORTUBA_CONTROLLED_REEXPORT", "protocol": SA.PROTOCOL,
                             "closes": ["DWG <-> DXF identity (SOURCE_ANCHOR)",
                                        "makes CROSS_ROUTE_AGREEMENT evaluable (K1 on the AC1027 DWG vs K2 on the DXF)"],
                             "effort": "one AutoCAD session, no editing; send 2 files + 4 hashes + the AutoCAD build"}],
        "when_available": [{"id": "UNSEEN_VILLA_FOR_BLIND_VALIDATION",
                            "what": "an unseen Kuwait villa: DWG + the same controlled export, the drawing unit, the "
                                    "plan scope; the QS quantities stay SEALED with the owner (send only their SHA-256) "
                                    "until our freeze is committed"}],
        "answered_this_round": [r["review_id"] + "@v1" for r in reviews["reviews"]] + [fact["fact_id"] + "@v1"],
        "do_not_ask": DO_NOT_ASK}
    regs["OWNER_PHYSICAL_FACT_REGISTER"] = {
        "SCHEMA": "URBAN_R8_20_OWNER_PHYSICAL_FACT_REGISTER_V1", "file": "data/registry/OWNER_PHYSICAL_FACTS.json",
        "new_fact": fact, "binding": binding, "allowed_domains": ctx["i1471_fact_domains"],
        "role": "CORROBORATING RATIONALE: explains WHY the admitted geometry exists; authorises no topology, geometry, "
                "quantity or trade change", "physical_fact_policy": OF.POLICY_ID + " (unchanged; no new domain)",
        "transfer_forbidden": fact["transfer_forbidden"], "urban_rule_created": False}
    regs["HUMAN_REVIEW_REGISTER"] = {
        "SCHEMA": "URBAN_R8_20_HUMAN_REVIEW_REGISTER_V1", "policy": RV.policy_record(),
        "file": "data/registry/OWNER_CLOSURE_REVIEWS.json", "reviews": reviews["reviews"],
        "states": {k: dict(v["review"], packet_digest_now=v["packet_digest_now"],
                           packet_digest_reviewed=v["packet_digest_reviewed"],
                           digest_match=v["packet_digest_now"] == v["packet_digest_reviewed"])
                   for k, v in cl.items()},
        "self_approved": False,
        "effect": "HUMAN_REVIEW condition only; geometry, topology, quantities and trades unchanged (QUANTITY_REGRESSION)"}
    pseg = regs19["COLUMN_DUCT_FINISH_REGISTER"]["columns"]["per_segment"]
    regs["I1471_COLUMN_CONCEALMENT_REGISTER"] = {
        "SCHEMA": "URBAN_R8_20_I1471_COLUMN_CONCEALMENT_REGISTER_V1", "geometry_evidence": ctx["i1471_evidence"],
        "owner_rationale": fact["fact_id"] + "@v1", "owner_statement": fact["statement"],
        "column_identity": "DETERMINISTIC from geometry" if ctx["i1471_evidence"]["column"]["deterministic"] else
        "NOT ESTABLISHED (rationale kept without a column handle)",
        "column_finish_unchanged": {k: v for k, v in pseg.items() if "|H716|" in k},
        "geometry_changed": False, "normalised_to_150mm": False, "quantity_effect": "NONE",
        "never": ["the 200 mm wall normalised to 150 mm", "the door centred", "a jamb or column moved",
                  "the stagger removed", "an Urban 'walls beside columns are 200 mm' rule"]}
    # ------------------------------------------------------------------ closures
    regs["CLOSURE_RELEASE_STATUS"] = {
        "SCHEMA": "URBAN_R8_20_CLOSURE_RELEASE_STATUS_V1", "policy": CR.policy_record(), "levels": list(CR.LEVELS),
        "released_level_exists": "RELEASED" in CR.LEVELS,
        "closures": {k: {"closure_id": v["closure_id"], "current_level_before_review": v["base_level"],
                         "maximum_justified_level": v["evaluation"]["level"],
                         "missing_for_next_level": v["evaluation"]["missing_for_reviewed"],
                         "evidence": v["evaluation"]["evidence"], "human_review": v["review"]["state"],
                         "releases_anything": v["evaluation"]["releases_anything"]} for k, v in cl.items()},
        "i1471_grading": "I1471 is graded under the model for the first time (TS01 door-strip closure, frozen "
                         "DOOR_OPENING_CLOSURE_POLICY_V2, base AUTHORISED_FOR_SHADOW as used by the shadow rows)",
        "cross_route": "NOT_ACHIEVABLE: REV_NEW has one input route (K2 ezdxf); K1 needs a decodable DWG",
        "production": "NO"}
    regs["QUANTITY_REGRESSION"] = dict(ctx["regression_20"], SCHEMA="URBAN_R8_20_QUANTITY_REGRESSION_V1",
                                       expected="no change: review / rationale change authority only")
    # ------------------------------------------------------------------ BOQ
    regs["BOQ_REPORT_SCHEMA"] = dict(regs19["BOQ_REPORT_SCHEMA"], SCHEMA="URBAN_R8_20_BOQ_REPORT_SCHEMA_V1",
                                     evidence_mapping=BE.policy_record())
    regs["BOQ_REPORT_SHADOW"] = {
        "SCHEMA": "URBAN_R8_20_BOQ_REPORT_SHADOW_V1", "report": rep, "validation": val, "evidence_rows": ev,
        "status_counts": {s: sum(1 for r in rep["rows"] if r["STATUS"] == s) for s in BR.STATUSES},
        "approved_for_boq": sum(1 for r in rep["rows"] if r["approved_for_boq"]),
        "status_changes_vs_r8_19": changed,
        "why": "R8.19 ignored quantity-affecting release blockers (OBJECT_FOOTPRINT_IMPLICIT) when deriving the status; "
               "BOQ_EVIDENCE_MAPPING_V1 keeps such rows at AUTHORISED_SUBTOTAL. Quantities unchanged",
        "banner": regs19["BOQ_REPORT_SHADOW"]["banner"]}
    regs["BOQ_XLSX_SCHEMA"] = {
        "SCHEMA": "URBAN_R8_20_BOQ_XLSX_SCHEMA_V1", "policy": BX.policy_record(),
        "sheets": {"00_READ_ME": "banner, how to read, status legend, no formulas / prices",
                   "01_BOQ_SUMMARY": "the TOTAL line of every item (one line per item)",
                   "02_ROOM_BREAKDOWN": "room lines of the same items, each marked 'BREAKDOWN OF <item> (not "
                                        "additive)'",
                   "03_TRACEABILITY": "one line per report row with every trace field",
                   "04_BLOCKERS_NOTES": "one line per blocker of every item",
                   "05_RUN_INFO": "run id, source revision, policies, report digest"},
        "why_not_the_suggested_trade_sheets": "trade sheets (floors / wall finishes / waterproofing) would repeat the "
                                              "summary quantities in a second place and invite adding them; there is "
                                              "no OPENINGS BOQ item (reveals are inside the finish rows)",
        "calculates": False, "pricing": None}
    regs["BOQ_XLSX_STATUS"] = {
        "SCHEMA": "URBAN_R8_20_BOQ_XLSX_STATUS_V1", "implemented": True, "file": "URBAN_QTO_R8_20_SHADOW_BOQ.xlsx "
        "(package)", "readback_validation": xv, "content_digest": w["content_digest"],
        "rows_exported": {"summary": xv["summary_lines"], "breakdown": xv["breakdown_lines"],
                          "traceability": xv["trace_lines"]},
        "statuses_visible": not xv["missing_status"], "formulas": xv["formulas"], "approved_lines": 0,
        "note": "the file bytes carry zip timestamps; identity is the content digest of every cell"}
    # ------------------------------------------------------------------ anchor / donors / roadmap / second project
    regs["SOURCE_ANCHOR_STATUS"] = dict(regs19["SOURCE_ANCHOR_STATUS"], SCHEMA="URBAN_R8_20_SOURCE_ANCHOR_STATUS_V1",
                                        r8_20="unchanged: NOT_ESTABLISHED; the identity tool and the controlled-export "
                                              "protocol are ready (SOURCE_ANCHOR_PLAN)")
    regs["SOURCE_ANCHOR_PLAN"] = {
        "SCHEMA": "URBAN_R8_20_SOURCE_ANCHOR_PLAN_V1", "policy": SA.policy_record(),
        "routes": {"A": {"what": "owner-controlled AutoCAD re-export (DXF + AC1027 DWG, no edits, hashes)",
                         "closes": ["SOURCE_ANCHOR", "enables CROSS_ROUTE_AGREEMENT"], "risk": "trusts AutoCAD as the "
                         "reference reader (the owner's own authoring tool)", "cost": "one session", "verdict": "BEST"},
                   "B": {"what": "native AutoCAD readback oracle via a pinned / reviewed MCP or COM lab route",
                         "closes": ["field-level readback of the DWG"], "risk": "a live tool in the loop; lab oracle "
                         "only, never a quantity authority", "verdict": "LATER (only if A is impossible)"},
                   "C": {"what": "another reproducibly built DWG decoder for AC1032",
                         "closes": ["SOURCE_ANCHOR (if it decodes)"], "risk": "unknown coverage; build provenance work",
                         "verdict": "NOT NOW"},
                   "D": {"what": "A + B", "verdict": "only if A shows differences"}},
        "recommended": "A", "tool_ready": "engine/source/source_anchor.py (SOURCE_EXPORT_IDENTITY_POLICY_V1), tested",
        "after_ingest": ["compare(current DXF, re-exported DXF)", "K1 on the AC1027 DWG vs K2 on the DXF: topology, "
                         "closures H2430 / H2431 / I1471", "re-evaluate CLOSURE_RELEASE_MODEL_V1"],
        "downloads": "NONE"}
    regs["MCP_DONOR_REVIEW"] = {
        "SCHEMA": "URBAN_R8_20_MCP_DONOR_REVIEW_V1", "lock": "research/external_engine_lab/DONORS.lock",
        "policy": "MCPs / public repos are DONORS, ORACLES, BENCHMARKS and RESEARCH ROUTES - never live production "
                  "quantity engines; nothing under engine/ imports them",
        "donors": {
            "U-C4N/Autocad-MCP": {"incorporated": ["OCS arbitrary-axis -> engine/source/cad/kernel_ocs.py "
                                                   "(CLEAN_REIMPLEMENTED, R8.1)",
                                                   "snapshot / topology / MINSERT / XREF rules (CLEAN_REIMPLEMENTED)"],
                                  "remaining": {"labels.plain (literal text decoding)": "COPY_ADAPTED when the "
                                                "document / PDF lane needs it (still PLANNED, licence notice kept)"},
                                  "rejected": "unit_of mm default, silent OCS identity, P&ID network as wall topology"},
            "Kentucky-ai/opentakeoff": {"incorporated": [],
                                        "remaining": {"scale-confirmed gating, schedule scan without silent row drop, "
                                                      "mixed-scale BLOCK": "CLEAN_REIMPLEMENT in the PDF lane",
                                                      "detectRooms / One-Click": "BENCHMARKED only"},
                                        "status": "DEFERRED to the PDF lane"},
            "beiming183-cloud/AutoCAD-MCP": {"incorporated": ["representation digest pattern -> run_manifest / "
                                                              "digests", "revision anchors -> canonical_input",
                                                              "field-level readback diff -> SOURCE_EXPORT_IDENTITY_"
                                                              "POLICY_V1 (CLEAN_REIMPLEMENTED, R8.20)"],
                                             "remaining": {"native readback oracle": "DEFERRED (route B only)"}},
            "Slacker-LLC/autocad-mcp": {"incorporated": [], "remaining": {"COM handle readback": "DEFERRED (route B "
                                                                                                 "lab oracle)"}},
            "puran-water/autocad-mcp": {"incorporated": [], "remaining": {"whole server": "BENCHMARK_REFERENCE only"}}},
        "duplicating_full_engines": False,
        "why": "only mechanisms are taken (clean reimplementation, tested); no external engine runs in the measurement "
               "path"}
    regs["PDF_ENGINE_ROADMAP"] = {
        "SCHEMA": "URBAN_R8_20_PDF_ENGINE_ROADMAP_V1",
        "start": "as a main track AFTER (1) the controlled re-export is ingested and (2) the first unseen-villa CAD blind "
                 "run is frozen and compared - target R8.22",
        "principle": "PDF / schedule / note / section / elevation evidence feeds the SAME SOURCE -> OBSERVATION -> "
                     "CLAIM -> EVIDENCE -> GEOMETRY -> TRADE -> QTO pipeline; no second BOQ calculator",
        "stages": [{"stage": 1, "what": "sections / elevations: clear and finish heights as WALL_HEIGHT_AUTHORITY rank "
                                        "1-2 candidates (replaces owner height facts where the drawings state them)"},
                   {"stage": 2, "what": "door / window schedules: opening heights and sills as source facts (replaces "
                                        "QP-21 / QP-22 owner parameters where scheduled)"},
                   {"stage": 3, "what": "finish schedules / notes: trade rules per room class as source claims"},
                   {"stage": 4, "what": "PDF-only plans with CONFIRMED scale as a geometry route (cross-route to CAD)"}],
        "donor_mechanisms": "OpenTakeoff: scale must be confirmed before any quantity; mixed scale blocks; schedule "
                            "rows never dropped silently",
        "never": ["a PDF quantity that bypasses the claim / evidence layer", "an unconfirmed scale", "OCR text as "
                  "authority without its source anchor"]}
    regs["SECOND_PROJECT_PLAN"] = {
        "SCHEMA": "URBAN_R8_20_SECOND_PROJECT_PLAN_V1",
        "requirements": ["resolved units (source declaration + owner statement)", "authoritative plan scope",
                         "certified source (hashed DWG + controlled DXF)", "no expected quantity visible before the "
                         "freeze", "comparable architectural trades"],
        "candidates": {
            "P7757": {"blind_eligible": False, "why": "UNIT_UNRESOLVED; its QS benchmark was unsealed in WT01.8 - it "
                                                      "can only be a NON-blind regression once its unit is stated"},
            "Al Rashed": {"blind_eligible": False, "why": "IMAGE / OLE content (not computable); its QS takeoff has "
                                                          "been seen"},
            "unseen Kuwait villa": {"blind_eligible": True, "why": "the only clean route", "recommended": True}},
        "protocol": ["owner sends DWG + controlled export + unit + plan scope + SHA-256 of the sealed QS file",
                     "intake, admission, unit / frame / region records", "engine + method FROZEN and committed",
                     "blind run, record committed", "owner sends the sealed QS file (hash checked)",
                     "comparison, metrics, disclosure - no tuning after gold"],
        "metrics": ["room detection completeness", "floor area error", "wall tile error", "skirting error",
                    "wall plaster error", "paint error", "opening count / size", "waterproofing", "ceiling",
                    "silent-error count"],
        "state": "NOT_RUN (no clean project yet)"}
    blocked = [k for k, v in regs["CLOSURE_RELEASE_STATUS"]["closures"].items()
               if v["maximum_justified_level"] != CR.REVIEWED]
    regs["PRODUCTION_GATE_STATUS"] = {
        "SCHEMA": "URBAN_R8_20_PRODUCTION_GATE_STATUS_V1",
        "gates": {"source_anchor_strategy": {"state": "PLAN_READY_NOT_EXECUTED", "met": False},
                  "closure_release_model_matured": {"state": f"human review recorded; {blocked} still miss "
                                                             "CROSS_ROUTE_AGREEMENT + SOURCE_ANCHOR", "met": False},
                  "multiple_blind_projects": {"state": "0 clean blind projects", "met": False},
                  "no_silent_critical_errors": {"state": "R8.20 found one (BOQ status mapping, quantity-neutral)",
                                                "met": False},
                  "boq_report_stable": {"state": f"shadow report + XLSX view validated ({val['state']} / "
                                                 f"{xv['state']})", "met": True},
                  "human_approval_workflow": {"state": "closure reviews recorded as versioned evidence; no BOQ approval "
                                                       "workflow yet", "met": False}},
        "firestore_approved_writes": "NONE", "production_migration": "NO"}
    regs["QORTUBA_R8_20_STATUS"] = {
        "SCHEMA": "URBAN_R8_20_QORTUBA_STATUS_V1",
        "six_rows": regs19["QORTUBA_R8_19_STATUS"]["six_rows"], "extra_rows": regs19["QORTUBA_R8_19_STATUS"]["extra_rows"],
        "quantity_regression": {"all_unchanged": ctx["regression_20"]["all_unchanged"],
                                "all_digests_same": ctx["regression_20"]["all_digests_same"]},
        "closures": regs["CLOSURE_RELEASE_STATUS"]["closures"], "boq_status_changes": changed,
        "final": "SHADOW only: no row is FINAL", "production_migration": "NO"}
    regs["R8_20_DECISION_REGISTER"] = decision(regs, ctx, rec, cl, changed, xv)
    return regs, ctx


def decision(regs, ctx, rec, cl, changed, xv):
    ev = ctx["i1471_evidence"]
    col = ev["column"]["column"]
    lvl = lambda k: {kk: regs["CLOSURE_RELEASE_STATUS"]["closures"][k][kk]                      # noqa: E731
                     for kk in ("current_level_before_review", "maximum_justified_level", "missing_for_next_level")}
    answers = {
        "1_h2430_review": cl["H2430"]["review"]["state"],
        "2_h2431_review": cl["H2431"]["review"]["state"],
        "3_i1471_review": cl["I1471"]["review"]["state"],
        "4_200mm_intentional": f"YES: owner fact {ctx['i1471_fact']['fact_id']}@v1; geometry: bands "
                               f"{ {k: v['width_mm'] for k, v in ev['bands'].items()} } mm, stagger {ev['stagger_mm']} mm",
        "5_rationale_recorded": f"YES: kind PHYSICAL_CONSTRUCTION_RATIONALE, allowed domains "
                                f"{ctx['i1471_fact_domains']}, binding {ctx['i1471_fact_binding']['binding']}; column "
                                f"{col} identified deterministically by geometry: "
                                f"{ev['column']['candidates'].get(col) if col else 'NOT ESTABLISHED'}",
        "6_geometry_changed": "NO",
        "7_quantity_changed": f"NO: all {len(ctx['regression_20']['rows'])} published rows unchanged "
                              f"({ctx['regression_20']['all_unchanged']}), digests same "
                              f"({ctx['regression_20']['all_digests_same']})",
        "8_i1471_level": lvl("I1471"), "9_h2430_level": lvl("H2430"), "10_h2431_level": lvl("H2431"),
        "11_what_prevents_next_level": "CROSS_ROUTE_AGREEMENT (one input route for REV_NEW) and SOURCE_ANCHOR (DWG "
                                       "not decodable) - for all three; no RELEASED level exists in the model",
        "12_human_review_satisfied": {k: v["review"]["satisfies_human_review"] for k, v in cl.items()},
        "13_cross_route_satisfied": "NO",
        "14_source_anchor_satisfied": "NO",
        "15_xlsx_implemented": f"YES: BOQ_XLSX_EXPORT_V1, readback {xv['state']}",
        "16_xlsx_calculates": "NO: plain values copied from report rows, no formulas (readback checks every cell)",
        "17_rows_exported": {"summary": xv["summary_lines"], "room_breakdown": xv["breakdown_lines"],
                             "traceability": xv["trace_lines"]},
        "18_statuses_visible": f"YES: every line has its STATUS cell (colour by status) and 'NO - SHADOW' in APPROVED; "
                               f"{regs['BOQ_REPORT_SHADOW']['status_counts']}",
        "19_traceable": "YES: 03_TRACEABILITY carries run id, source revision, trade row, sites, surface ids, "
                        "authority digest, rule ids, owner facts, release state, evidence row for every line",
        "20_source_anchor_route": regs["SOURCE_ANCHOR_PLAN"]["routes"]["A"]["what"],
        "21_reexport_now": "YES - it is the single action that materially closes the anchor and opens the cross-route "
                           "check; protocol in SOURCE_ANCHOR_PLAN",
        "22_donor_mechanisms_incorporated": {k: v["incorporated"] for k, v in regs["MCP_DONOR_REVIEW"]["donors"].items()
                                             if v["incorporated"]},
        "23_donor_mechanisms_remaining": {k: v["remaining"] for k, v in regs["MCP_DONOR_REVIEW"]["donors"].items()},
        "24_duplicating_engines": "NO",
        "25_pdf_main_track": regs["PDF_ENGINE_ROADMAP"]["start"],
        "26_second_project": "an unseen Kuwait villa (P7757 / Al Rashed are not blind-eligible)",
        "27_before_blind_validation": regs["SECOND_PROJECT_PLAN"]["requirements"],
        "28_production_blockers": {k: v["state"] for k, v in regs["PRODUCTION_GATE_STATUS"]["gates"].items()
                                   if not v["met"]},
        "29_new_silent_error": f"R8.19 BOQ status mapping: rows with a QUANTITY-AFFECTING release blocker "
                               f"(OBJECT_FOOTPRINT_IMPLICIT) were shown as COMPUTED_SHADOW_COMPLETE - corrected by "
                               f"BOQ_EVIDENCE_MAPPING_V1 (fail closed for unknown blockers): {changed}; quantities "
                               "unchanged",
        "30_r8_21": rec["14_r8_21"],
        "31_disagreements": rec["13_disagreements_with_chatgpt"]}
    return {"SCHEMA": "URBAN_R8_20_DECISION_REGISTER_V1", "recommendation_before_coding": rec,
            "decisions": [
                {"id": "R820-D01", "decision": "owner reviews recorded as versioned evidence bound to the closure "
                                               "digests; HUMAN_REVIEW satisfied for H2430 / H2431 / I1471"},
                {"id": "R820-D02", "decision": "I1471 rationale stored as a no-domain physical construction rationale; "
                                               "geometry untouched; column H716 identified by geometry"},
                {"id": "R820-D03", "decision": "no closure reaches REVIEWED_FOR_RELEASE_CANDIDATE (cross-route, "
                                               "anchor); nothing released"},
                {"id": "R820-D04", "decision": "BOQ evidence mapping corrected (Q-03P / Q-12 AUTHORISED_SUBTOTAL); "
                                               "XLSX view exported and validated"},
                {"id": "R820-D05", "decision": "source anchor: controlled DXF + AC1027 re-export recommended now"},
                {"id": "R820-D06", "decision": "second project: unseen villa with sealed QS gold"}],
            "gates": GATES, "answers": answers}
