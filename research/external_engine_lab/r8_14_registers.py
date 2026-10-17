"""R8.14 lab registers: every JSON register of the R8.14 package from the r8_14_qortuba build (no number typed in).

Owner actions, owner method facts, door thresholds + transition policy + marble evidence, open-passage reveals +
soffit allocation, skirting method + readiness, V4-O1 / V4-O2, wall-band policy status, source anchor, closure
release, Q-13 / Q-14 status, six-row status, digest hierarchy, decision register (recommendation first, answers 1-36).
"""

from __future__ import annotations

import json
from pathlib import Path

import r8_14_qortuba as Q
from engine.source import closure_release as CR, door_transition as DT, opening_reveals as OR
from engine.source import owner_method_facts as MF, run_manifest as RM, topology_closures as TC
from engine.source import trade_strips as TS, wall_bands as WB, wall_contact_path as WC

ROOT = Path(__file__).resolve().parents[2]
GATES = {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO", "PRODUCTION_MIGRATION": "NO"}
R813_REG = ROOT / "tests/r8_13/registers"


def jl(p):
    return json.loads(Path(p).read_text())


def _strip_m2(aud, states):
    return round(sum(a["contribution_m2"] for a in aud if a["state"] in states), 6)


def _row_view(rid, row, dig, ctx):
    eff, aud = row["strip_effect"], row["strip_audit"]
    ta = row["trade_authority"]
    return {"row": rid, "STATE": row["state"], "VALUE": row["value"], "unit": "m2", "final": False,
            "BASE_SITE_AREA_M2": row["base_site_area_m2"],
            "THRESHOLD_CONTRIBUTION_M2": eff["threshold_contribution_m2"],
            "THRESHOLDS": [{"strip": a["strip"], "state": a["state"], "contribution_m2": a["contribution_m2"]}
                           for a in aud if a["kind"] == "THRESHOLD"],
            "PASSAGE_TREATMENT": {"soffit_exclusion_m2": eff["soffit_exclusion_m2"],
                                  "passages_included_in_site": eff["passages_included"],
                                  "head_unresolved": [a["strip"] for a in aud if a["state"] == TS.HEAD_UNRESOLVED]},
            "OBJECT_FOOTPRINT_POLICY": dig["ROW_AUTHORITY_DIGEST"]["footprint_policies"] or
            [f"NONE ({(row.get('footprint_authority') or {}).get('treatment') or 'no authority'})"],
            "SEMANTIC_CLASSES": None if rid == "Q-14" else Q.R13.ROW_CLASS[rid],
            "TRADE_AUTHORITY": [ta["rule"]] + ([ta["semantic_class_rule"]] if ta.get("semantic_class_rule") else []),
            "TOPOLOGY_POLICY": f"{WB.POLICY_ID} ({WB.policy_record()['digest'][:16]}) + {TC.POLICY_ID}",
            "TOPOLOGY_DIGEST": dig["TOPOLOGY_RUN_INPUT_DIGEST"],
            "ROW_AUTHORITY_DIGEST": dig["ROW_AUTHORITY_DIGEST"]["digest"],
            "RELEASE_INPUT_DIGEST": dig["RELEASE_INPUT_DIGEST"]["digest"],
            "PHYSICAL_SITES": [{"site": u["site"], "zones": u["zones"], "area_m2": u["area_m2"]}
                               for u in row["sites_used"]],
            "OWNER_FACTS_APPLIED": dig["ROW_AUTHORITY_DIGEST"]["owner_facts_applied"],
            "SOURCE_ANCHOR": row["source_anchor"], "RELEASE_BLOCKERS": row["release_blockers"],
            "COUNTERFACTUALS": {k: row[k] for k in ("counterfactual_if_not_an_obstacle", "counterfactual_unit_boundary")
                                if row.get(k) is not None},
            "blockers": row["blockers"], "blocker_classes": row["blocker_classes"]}


def registers(ctx):
    rows, dig, mf = ctx["rows_new"], ctx["dig"], ctx["mfacts"]
    rec = jl(ROOT / "research/external_engine_lab/r8_14_recommendation.json")
    B, FZ = ctx["blind"]["NEW_K2"], ctx["freeze"]
    ths = ctx["thresholds_new"]
    six = {rid: _row_view(rid, rows[rid], dig[rid], ctx) for rid in Q.ROWS}
    r813 = jl(R813_REG / "QORTUBA_R8_13_STATUS.json")
    regs = {}
    # ------------------------------------------------------------------ owner side
    prepared = [
        {"id": "QORTUBA_BED_ROOM_RECTANGLE_ROLE", "only_if": "release of Q-13 / Q-14 is requested",
         "question": "BED.ROOM: the 2.10 x 0.40 m double rectangle on the WALL layer (H2060 / H2061, dashed X inside) "
                     "- a built shaft / duct (floor and ceiling stop at it) or a drawn symbol / overhead item?",
         "effect": "0.84 m2 on Q-13 and on Q-14"},
        {"id": "QORTUBA_MB_DRESS_PASSAGE_HEAD", "only_if": "release of Q-14 is requested",
         "question": "M.B.ROOM / DRESS open passage (1.20 m): is there a head (soffit) over it, or is it full height?",
         "effect": "0.18 m2 on Q-14"},
        {"id": "QORTUBA_ENTRANCE_THRESHOLD", "only_if": "release of Q-13 is requested",
         "question": "flat entrance door (HALL -> common landing, 1.00 m): does the flat's porcelain stop at the door "
                     "centre like the dry / wet doors?", "effect": "0.075 m2 on Q-13 (0 / 0.075 / 0.15)"}]
    regs["OWNER_ACTION_REGISTER"] = {
        "SCHEMA": "URBAN_OWNER_ACTION_REGISTER_V11", "headline": "NO OWNER ACTION REQUIRED.", "required_now": [],
        "answered_this_round": [{"fact": f.ref, "kind": f.kind} for f in mf.values()],
        "why_none": "all six new-revision rows compute in SHADOW; what remains are release items carried as explicit "
                    "release blockers with counterfactual values",
        "prepared_for_release_stage_not_asked": prepared,
        "do_not_ask": ["the selected plan", "the unit", "7116-7119", "the xref scope", "H2430 / H2431",
                       "Hall / Lobby geometry and height", "the floor under wardrobes", "the 3.20 m height",
                       "basic skirting", "the door-threshold transition", "the Hall / Lobby soffit",
                       "any expected quantity"]}
    rule_refs = [{"ref": "QP-08 QORTUBA_FIXED_CABINET_DEDUCTION", "trade": "SKIRTING", "attribute": "DEDUCTION",
                  "value": "NONE"}, {"ref": "US-02 NO_SKIRTING_IN_A_FULLY_CERAMIC_ROOM", "trade": "SKIRTING",
                                     "attribute": "NO_SKIRTING", "value": "FULL_WALL_TILE"}]
    regs["OWNER_METHOD_FACT_REGISTER"] = {
        "SCHEMA": "URBAN_R8_14_OWNER_METHOD_FACT_REGISTER_V1", "policy": MF.policy_record(),
        "file": "data/registry/OWNER_METHOD_FACTS.json",
        "facts": [{"ref": f.ref, "kind": f.kind, "scope": f.scope, "statement": f.statement, "unit": f.unit,
                   "allowed_domains": list(f.allowed_domains), "transfer_forbidden": list(f.transfer_forbidden),
                   "binding": {"NEW_K2": b["binding"],
                               "OLD_K1": dict((g.ref, c["binding"]) for g, c in ctx["binds_old"])[f.ref]},
                   "relations": list(f.relations)} for f, b in ctx["binds_new"]],
        "reconciliation": [dict(r, fact=f.ref) for f in mf.values() for r in f.relations],
        "silent_contradictions": MF.conflicts(list(mf.values()), rule_refs),
        "never": ["a topology input", "a transfer to the old revision / DWG / another project", "an Urban default"]}
    # ------------------------------------------------------------------ thresholds
    def th_view(t):
        return {k: v for k, v in t.items() if k != "_alloc"}
    alloc_states = {}
    for t in ths:
        alloc_states[t["allocation_state"]] = alloc_states.get(t["allocation_state"], 0) + 1
    receiving = {t["threshold"]: {rid: a["contribution_m2"] for rid in Q.ROWS for a in rows[rid]["strip_audit"]
                                  if a["strip"] == t["threshold"] and a["contribution_m2"]} for t in ths}
    regs["DOOR_THRESHOLD_REGISTER"] = {
        "SCHEMA": "URBAN_R8_14_DOOR_THRESHOLD_REGISTER_V1", "revision": "QORTUBA_REV_NEW",
        "thresholds": [dict(th_view(t), receiving_rows=receiving[t["threshold"]]) for t in ths],
        "count": len(ths), "by_state": alloc_states,
        "allocated": sum(1 for t in ths if t["allocation_state"] in DT.RESOLVED),
        "reconciled_exactly": all(t["reconciles"] for t in ths),
        "outside_measured_unit": [t["threshold"] for t in ths if t["allocation_state"] == Q.OUTSIDE_UNIT],
        "unit_boundary": [t["threshold"] for t in ths if t["unit_boundary"]],
        "old_revision": [{"threshold": t["threshold"], "state": t["allocation_state"],
                          "why": "the R8.14 facts are scoped to the new revision (REJECTED_SCOPE on the old one)"}
                         for t in ctx["thresholds_old"]],
        "ceiling": "every door threshold is NOT_IN_TRADE for CEILING (the door head is the door's top reveal)"}
    regs["DOOR_TRANSITION_POLICY"] = {
        "SCHEMA": "URBAN_R8_14_DOOR_TRANSITION_POLICY_V1", "policy": DT.policy_record(),
        "strip_audit_policy": TS.policy_record_v2(),
        "plane_hierarchy_applied": {"1 AUTHORED_LEAF_PLANE": "NOT APPLICABLE on this source: every hinge lies on a "
                                                             "wall face (SYMBOL_ANCHORED_AT_FACE)",
                                    "2 authored jamb structure": "no frame / jamb line inside any reveal",
                                    "3 OWNER_CENTRED_DOOR": f"{mf[Q.F_SPLIT].ref} (door_centred, this Qortuba method "
                                                            "only) on the ESTABLISHED face pair (closures A / B)"},
        "unit_boundary_rule": {"rule": "a side whose site lies outside the measured unit is OUTSIDE_MEASURED_UNIT: the "
                                       "unit's finish meets it at the door plane; a threshold with both sides outside "
                                       "the unit is in no row",
                               "where": "lab scope input (research/external_engine_lab/r8_14_qortuba.py), not the "
                                        "engine", "decided": "AFTER the first Qortuba run (disclosed): release blocker "
                                                             "UNIT_BOUNDARY_THRESHOLD on the receiving row"},
        "never": DT.policy_record()["never"]}
    regs["MARBLE_THRESHOLD_EVIDENCE"] = ctx["marble"]
    # ------------------------------------------------------------------ reveals / soffit
    rv, hp, sa = ctx["reveals"], ctx["hall_passage"], ctx["soffit_audit"]
    mbp = [p for p in ctx["new"]["passages"] if p["passage_id"] != hp["passage_id"]]
    regs["OPEN_PASSAGE_REVEAL_REGISTER"] = {
        "SCHEMA": "URBAN_R8_14_OPEN_PASSAGE_REVEAL_REGISTER_V1", "policy": OR.policy_record(),
        "hall_lobby": dict(rv, passage_source={k: hp[k] for k in ("passage_id", "width_mm", "thickness_mm",
                                                                  "strip_in_site", "area_m2") if k in hp}),
        "surfaces": [{"surface": s["surface"], "area_m2": s["area_m2"], "finish": s["finish"], "trade": s["trade"]}
                     for s in rv["surfaces"]],
        "paint": "NOT ASSUMED (no paint authority)",
        "ownership_guard_double_claims": ctx["ownership_guard"],
        "us07_reconciliation": {"US-07 reveal depth": "0.25 m standard", "source wall thickness": rv["depth_m"],
                                "state": "RECORDED - reconciled when the plaster trade is computed; geometry from "
                                         "source"},
        "plaster_quantity": "NOT PRODUCED (no plaster face-set row this round; the surfaces are recorded once)",
        "other_passages": [{"passage": p["passage_id"], "width_mm": round(p["width_mm"], 2),
                            "site": p.get("strip_in_site"), "head": "NOT ESTABLISHED for this revision" if
                            p.get("strip_in_site") in {u["site"] for u in rows["Q-14"]["sites_used"]} else
                            "outside the measured unit"} for p in mbp]}
    regs["SOFFIT_ALLOCATION_POLICY"] = {
        "SCHEMA": "URBAN_R8_14_SOFFIT_ALLOCATION_POLICY_V1",
        "rule": "CEILING = ceiling region - OPEN_PASSAGE_SOFFIT_FOOTPRINT (WITH_HEAD); FULL_HEIGHT -> ceiling "
                "continues; head unknown -> UNRESOLVED_HEAD_CONDITION (release blocker)",
        "fact": [mf[Q.F_SOFFIT].ref, mf[Q.F_REVEAL].ref], "hall_lobby_audit": sa,
        "footprint_m2_from_source": rv["footprint_m2"],
        "derived_from": "the passage strip polygon (band end points of H2430 / H2431 closures) - never a target value",
        "q14_exclusion_m2": rows["Q-14"]["strip_effect"]["soffit_exclusion_m2"],
        "double_count_guard": ctx["ownership_guard"] or "PASS (one owner per footprint)"}
    # ------------------------------------------------------------------ skirting
    regs["SKIRTING_METHOD_POLICY"] = {
        "SCHEMA": "URBAN_R8_14_SKIRTING_METHOD_POLICY_V1", "policy": WC.policy_record(),
        "facts": {f: {"statement": mf[f].statement, "relations": list(mf[f].relations)} for f in (Q.F_SKIRT,
                                                                                                    Q.F_NOSKIRT)},
        "vs_QP_08": "REFINES (MORE_SPECIFIC) - the no-deduction rule is unchanged; the path and stops are stated",
        "vs_US_02": "CORROBORATING",
        "rooms_with_skirting": "DRY_INTERNAL_ROOM with a tiled floor (Q-13 sites)",
        "rooms_without": mf[Q.F_NOSKIRT].statement["rooms"] + ["PAINTRY (SERVICE_ROOM, QP-07)"],
        "behind_wardrobes": "YES (wardrobes / joinery / furniture are not site boundaries)",
        "across_doors_passages": "NO (DOOR_OPENING stops; TOPOLOGY_CLOSURE contributes zero; no synthetic segment)"}
    regs["SKIRTING_READINESS"] = ctx["skirting"]
    # ------------------------------------------------------------------ V4-O1 / V4-O2 / wall band
    ob = ctx["obstacles"]
    bed = next((o for o in ob if o["rows"]), None)
    regs["V4_O1_REGISTER"] = {
        "SCHEMA": "URBAN_R8_14_V4_O1_REGISTER_V1",
        "observation": "H2060 (2100 x 400 mm) with H2061 nested 100 mm inside it: closed LWPOLYLINEs on layer WALL "
                       "(GR-05 TOPOLOGY_BOUNDARY), touching no other admitted segment; a dashed X (H2062 / H2065, "
                       "hidden layer, GR-16 PRESENTATION_OVERHEAD) inside the inner one",
        "generic_test": "isolated closed loop: a closed single-entity loop whose segments touch no admitted segment of "
                        "another entity (within eps_n) - no thickness, size or location test",
        "v5_band_state": {"geometric_candidates": B["v4"]["geometric_candidates"],
                          "isolated_loops": B["v4"]["isolated_loops"],
                          "physical_authority_entities": B["v4"]["physical_authority_entities"]},
        "distinction": {"GEOMETRIC_BAND_CANDIDATE": "parallel faces at a wall-like width (recorded; no ends, "
                                                    "closures, passages or paired-face corroboration)",
                        "PHYSICAL_WALL_BAND_ESTABLISHED": "requires positive physical authority for the entity (an "
                                                          "applied part claim) or contact with the wall network"},
        "room_area_effect": ob, "material": bool(bed),
        "rows_affected": bed["rows"] if bed else [],
        "counterfactual_if_not_an_obstacle": {rid: rows[rid].get("counterfactual_if_not_an_obstacle")
                                              for rid in (bed["rows"] if bed else [])},
        "state": "UNRESOLVED - NON-AUTHORITATIVE: the hole stays as TS01 computes it (role admission is not changed "
                 "after a blind run); OBSTACLE_AUTHORITY_UNPROVEN release blocker on each affected row",
        "next": "R8.15: role-admission authority for isolated closed loops on wall layers (frozen, blind)"}
    regs["V4_O2_REGISTER"] = {
        "SCHEMA": "URBAN_R8_14_V4_O2_REGISTER_V1",
        "observation": "a square run (run == ratio x separation; pair 545 / 549 old revision, 150 x 150 mm) was "
                       "decided by binary floating-point noise at the elongation equality (V3 and V4)",
        "v5_rule": WB.PARAMS["elongation_tie"],
        "implementation": "wall_bands._elongated(length, d, eps_r) -> True / None / False; the raw pre-check treats "
                          "None as not elongated (no run is formed); a local run at the boundary is UNSUPPORTED with "
                          f"reason {WB.BOUNDARY_CASE}",
        "synthetic_tests": [t for t in FZ["v5_synthetic_tests"] if any(w in t for w in ("tie", "square", "within",
                                                                                         "margin", "boundary"))],
        "blind_result": {"NEW_K2_boundary_cases": B["v4"]["boundary_cases"],
                         "OLD_K1_boundary_cases": ctx["blind"]["OLD_K1"]["v4"]["boundary_cases"],
                         "pair_545_549": "no band in either revision under V5 (the only band on 549 is 546 / 549)"},
        "observability_gap": "raw-stage ties are dropped as 'not elongated' without a record; boundary_cases counts "
                             "local-run ties only - recorded for R8.15 (no effect on any row)",
        "material": False, "state": "RESOLVED (deterministic, fail closed)"}
    regs["WALL_BAND_POLICY_STATUS"] = {
        "SCHEMA": "URBAN_R8_14_WALL_BAND_POLICY_STATUS_V1", "policy": WB.policy_record(),
        "closure_policy": TC.policy_record(), "version": "V5", "supersedes": FZ["supersedes"], "freeze": FZ,
        "lab_reproduces_blind": ctx["reproduces"], "v4_to_v5": ctx["band_diff_v4_v5"],
        "h2430_h2431": [{k: c[k] for k in ("closure_id", "release", "geometry", "evidence")} |
                        {"separated_m2": [p["area_m2"] for p in c["safety"]["separated_pieces"]]} for c in B["closures"]],
        "h1316": "NOT_WALL_CAP (no closure carries 1316)" if not any("1316" in c["evidence"] for c in B["closures"])
        else "CHANGED", "hall_m2": B["hall"]["area_m2"],
        "labelled_sites_unchanged_vs_v4": jl(R813_REG / "BLIND_QORTUBA_V4_RESULT.json")["NEW_K2"]["labelled_sites"] ==
        B["labelled_sites"], "determinism": ctx["det"]}
    regs["SOURCE_ANCHOR_STATUS"] = ctx["source_anchor"]
    regs["CLOSURE_RELEASE_STATUS"] = {
        "SCHEMA": "URBAN_R8_14_CLOSURE_RELEASE_STATUS_V1", "policy": CR.policy_record(),
        "closures": ctx["closure_release"], "ceiling": "REVIEWED_RELEASE_CANDIDATE at most; never production",
        "reached": sorted({v["level"] for v in ctx["closure_release"].values()}),
        "missing": sorted({m for v in ctx["closure_release"].values() for m in v["missing_for_reviewed"]}),
        "released": []}
    # ------------------------------------------------------------------ rows
    q13, q14 = rows["Q-13"], rows["Q-14"]
    regs["Q13_STATUS"] = dict(
        six["Q-13"], SCHEMA="URBAN_R8_14_Q13_STATUS_V1",
        rebuild="from the TS01 sites of the frozen V5 run + the threshold allocations; no R8.13 value is used",
        regression_vs_r8_13={"R8.13": r813["six_rows"]["Q-13"]["VALUE"], "R8.14": q13["value"],
                             "delta_m2": None if q13["value"] is None else
                             round(q13["value"] - r813["six_rows"]["Q-13"]["VALUE"], 4), "is_target": False},
        thresholds=[{"threshold": t["threshold"], "state": t["allocation_state"], "regions": t["regions"]}
                    for t in ths if receiving[t["threshold"]].get("Q-13")],
        historical_matching="NONE")
    regs["Q14_STATUS"] = dict(
        six["Q-14"], SCHEMA="URBAN_R8_14_Q14_STATUS_V1",
        rebuild="ceiling sites of the frozen V5 run minus the Hall / Lobby soffit footprint; door thresholds "
                "NOT_IN_TRADE; no R8.13 value is used",
        regression_vs_r8_13={"R8.13": r813["six_rows"]["Q-14"]["VALUE"], "R8.14": q14["value"],
                             "delta_m2": None if q14["value"] is None else
                             round(q14["value"] - r813["six_rows"]["Q-14"]["VALUE"], 4), "is_target": False},
        soffit=regs["SOFFIT_ALLOCATION_POLICY"]["hall_lobby_audit"], historical_matching="NONE")
    regs["QORTUBA_R8_14_STATUS"] = {
        "SCHEMA": "URBAN_R8_14_QORTUBA_STATUS_V1", "six_rows": six,
        "rows_new": {rid: {k: v for k, v in rows[rid].items() if k != "strip_audit"} for rid in Q.ROWS},
        "rows_old": {rid: {"state": v["state"], "value": v["value"]} for rid, v in ctx["rows_old"].items()},
        "old_revision_unchanged_vs_r8_13": {rid: (ctx["rows_old"][rid]["state"], ctx["rows_old"][rid]["value"]) ==
                                            (r813["rows_old"][rid]["state"], r813["rows_old"][rid]["value"])
                                            for rid in Q.ROWS},
        "r8_13_rows_new": {rid: (v["STATE"], v["VALUE"]) for rid, v in r813["six_rows"].items()},
        "pantry_service_rows": {rid: {"thresholds_touching": [a["strip"] for a in rows[rid]["strip_audit"]
                                                              if a["kind"] == "THRESHOLD"]} for rid in ("Q-03P", "Q-12")},
        "determinism": ctx["det"], "lab_reproduces_blind": ctx["reproduces"], "final": "SHADOW only: no row is FINAL"}
    d13 = jl(R813_REG / "DIGEST_HIERARCHY.json")["rows"]
    regs["DIGEST_HIERARCHY"] = {
        "SCHEMA": "URBAN_R8_14_DIGEST_HIERARCHY_V1", "layers": list(RM.DIGEST_LAYERS), "rows": dig,
        "vs_r8_13": {rid: {layer: ("CHANGED" if (dig[rid][layer] if layer == "TOPOLOGY_RUN_INPUT_DIGEST" else
                                                 dig[rid][layer]["digest"]) !=
                                   (d13[rid][layer] if layer == "TOPOLOGY_RUN_INPUT_DIGEST" else d13[rid][layer]["digest"])
                                   else "SAME") for layer in ("TOPOLOGY_RUN_INPUT_DIGEST", "ROW_AUTHORITY_DIGEST",
                                                              "RELEASE_INPUT_DIGEST")} for rid in Q.ROWS},
        "reasons": {"TOPOLOGY_RUN_INPUT_DIGEST": "every row: WALL_BAND_POLICY_V4 -> V5 is a TS01 input",
                    "ROW_AUTHORITY_DIGEST": "every row through the topology digest; additionally Q-03 / Q-11 / Q-13 "
                                            "by the threshold facts (allocations), Q-14 by the soffit fact, and every "
                                            "row by the strip-audit V2 method",
                    "RELEASE_INPUT_DIGEST": "row digest + release blockers (thresholds resolved; soffit; obstacle "
                                            "authority; passage head; unit boundary)"},
        "facts_never_topology": "the owner method facts are never TS01 inputs: the topology digest is the frozen blind "
                                "V5 digest (lab reproduces it)",
        "lab_reproduces_blind_digest": ctx["reproduces"]["topology_digest"]}
    regs["R8_14_DECISION_REGISTER"] = decision_register(regs, ctx, rec, six)
    return regs, ctx


def decision_register(regs, ctx, rec, six):
    T, M = regs["DOOR_THRESHOLD_REGISTER"], regs["MARBLE_THRESHOLD_EVIDENCE"]
    RV, SO = regs["OPEN_PASSAGE_REVEAL_REGISTER"], regs["SOFFIT_ALLOCATION_POLICY"]
    O1, O2, WS = regs["V4_O1_REGISTER"], regs["V4_O2_REGISTER"], regs["WALL_BAND_POLICY_STATUS"]
    SK = regs["SKIRTING_READINESS"]
    ths = ctx["thresholds_new"]
    split = [t for t in ths if t["allocation_state"] == DT.SPLIT]
    cont = [t for t in ths if t["allocation_state"] == DT.CONTINUOUS]
    still = [t["threshold"] for t in ths if t["allocation_state"] not in DT.RESOLVED + (Q.OUTSIDE_UNIT,)]
    answers = {
        "1_physical_vs_trade": "ONE physical OPENING_SITE per door (the reveal strip between the two face closures, "
                               "a TS01 site); the finish transition is a TRADE subdivision of that site "
                               "(DOOR_TRANSITION_POLICY_V1) - the building topology is never split",
        "2_dry_dry_area": f"{len(cont)} dry <-> dry thresholds: CONTINUOUS_SAME_FINISH, the whole strip once to the "
                          f"dry porcelain row Q-13 ({round(sum(t['strip_m2'] for t in cont), 6)} m2)",
        "3_dry_wet_geometry": "the established parallel face pair (closures A and B, from the wall jamb caps) with the "
                              "owner-centred plane (level 3); level 1 does not apply - every hinge lies ON a face",
        "4_midpoint_assumption": "YES, but only as the owner's scoped DOOR_CENTRED fact applied to the established "
                                 "face pair (OWNER_CENTRED_DOOR) - never thickness / 2 by default",
        "5_explicit_marble": M["result"],
        "6_continuity_rule_applied": f"YES ({M['applies']}; {ctx['mfacts'][Q.F_CONT].ref})",
        "7_thresholds_allocated": f"{T['allocated']} of {T['count']} (by state {T['by_state']}); the remaining one "
                                  "lies wholly outside the measured unit (common landing) and is in no row",
        "8_areas_reconciled": T["reconciled_exactly"],
        "9_q03_q11_contribution": {rid: six[rid]["THRESHOLD_CONTRIBUTION_M2"] for rid in ("Q-03", "Q-11")} |
        {"how": "the wet halves only: " + ", ".join(f"{t['threshold']} {r['area_m2']} m2" for t in split
                                            for r in t["regions"] if r["treatment"] == "CERAMIC_WET_FLOOR")},
        "10_q13_contribution": six["Q-13"]["THRESHOLD_CONTRIBUTION_M2"],
        "11_threshold_still_blocker": still or "NONE blocks; the entrance threshold carries a UNIT_BOUNDARY_THRESHOLD "
                                               "release blocker (post-run scope decision, disclosed)",
        "12_soffit_representation": "OPENING_REVEAL_SURFACE TOP_SOFFIT (plaster), footprint from the source passage "
                                    f"strip ({round(SO['footprint_m2_from_source'], 6)} m2); recorded once",
        "13_q14_excluded_soffit": SO["hall_lobby_audit"]["state"],
        "14_q14_value": f"{six['Q-14']['STATE']} {six['Q-14']['VALUE']} m2 (SHADOW)",
        "15_reveal_surfaces": RV["surfaces"],
        "16_paint_assumed": "NO",
        "17_passage_still_open": "YES - the Hall / Lobby passage stays an OPEN_PASSAGE_SITE (floor continues; no wall, "
                                 "no closure material)",
        "18_skirting_method_explicit": "YES - all real walls of tiled dry rooms, stops at doors / passages / gaps, "
                                       "no wardrobe deduction (scoped fact, REFINES QP-08)",
        "19_behind_wardrobes": "YES",
        "20_across_doors_passages": "NO",
        "21_rooms_no_skirting": regs["SKIRTING_METHOD_POLICY"]["rooms_without"],
        "22_skirting_quantity": SK["quantity"],
        "23_missing_component": SK["missing_components"],
        "24_v4_o1_what": O1["observation"],
        "25_v4_o1_policy_change": "YES for the BAND (V5 GEOMETRIC_BAND_CANDIDATE: no ends / closures / passages); "
                                  "NO for the ROOM HOLE (role admission unchanged after a blind run): material "
                                  f"{O1['material']} -> OBSTACLE_AUTHORITY_UNPROVEN on {O1['rows_affected']} with "
                                  f"counterfactuals {O1['counterfactual_if_not_an_obstacle']}",
        "26_v4_o2_what": O2["observation"],
        "27_equality_deterministic": O2["v5_rule"],
        "28_v4_or_v5": f"V5 ({WS['policy']['digest'][:16]}), frozen at {WS['freeze']['frozen_commit'][:12]} before "
                       "the blind run",
        "29_h2430_h2431_regression": WS["h2430_h2431"],
        "30_source_anchor": ctx["source_anchor"]["state"] + " - " + ctx["source_anchor"]["correction"],
        "31_closure_release": regs["CLOSURE_RELEASE_STATUS"]["reached"],
        "32_six_values": {rid: (v["STATE"], v["VALUE"]) for rid, v in six.items()},
        "33_blockers_per_row": {rid: v["RELEASE_BLOCKERS"] for rid, v in six.items()},
        "34_new_silent_error": [
            "R8.13 kept the M.B.ROOM / DRESS passage strip (0.18 m2) inside the normal ceiling because both sides "
            "agreed - for a ceiling the head condition decides; R8.14 makes it PASSAGE_HEAD_CONDITION_NOT_ESTABLISHED",
            "the BED.ROOM 0.84 m2 hole stands on a layer-only isolated loop (V4-O1) - now an explicit "
            "OBSTACLE_AUTHORITY_UNPROVEN release blocker on Q-13 and Q-14",
            "the flat entrance threshold (HALL -> common landing) was counted as a dry <-> dry door in the pre-run "
            "prediction; the run shows its far side is outside the measured unit - recorded, not hidden"],
        "35_r8_15": rec["10_r8_15"],
        "36_disagreements": rec["9_disagreements_with_chatgpt"]}
    return {"SCHEMA": "URBAN_R8_14_DECISION_REGISTER_V1", "recommendation_before_coding": rec,
            "order": ["recommendation written (r8_14_recommendation.json)",
                      f"V5 + synthetic tests committed: {ctx['freeze']['frozen_commit'][:12]}",
                      "freeze record committed", "blind run committed (BLIND_QORTUBA_V5_RESULT.json)",
                      "trade modules + owner method facts + synthetic tests committed before the Qortuba rebuild",
                      "rebuild, registers afterwards"],
            "decisions": [
                {"id": "R814-D01", "decision": "WALL_BAND_POLICY_V5: elongation tie against eps_r (V4-O2) + "
                                               "GEOMETRIC_BAND_CANDIDATE for isolated closed loops (V4-O1 band side)"},
                {"id": "R814-D02", "decision": "DOOR_TRANSITION_POLICY_V1: plane hierarchy with the leaf strictly "
                                               "inside the reveal; owner-centred plane only as a scoped fact"},
                {"id": "R814-D03", "decision": "STRIP_ALLOCATION V2: thresholds resolved by allocation; CEILING door "
                                               "thresholds NOT_IN_TRADE; passage head condition required for CEILING"},
                {"id": "R814-D04", "decision": "Hall / Lobby soffit out of Q-14, recorded as TOP_SOFFIT plaster; "
                                               "jambs as LEFT / RIGHT_JAMB; no paint"},
                {"id": "R814-D05", "decision": "skirting: path classifier built and tested; NO quantity (no frozen, "
                                               "blind-tested path policy; no jamb-return rule)"},
                {"id": "R814-D06", "decision": "V4-O1 room hole kept, release blocker + counterfactual; role admission "
                                               "deferred to R8.15"},
                {"id": "R814-D07", "decision": "entrance threshold: unit-boundary split at the owner-centred plane "
                                               "(post-run lab scope decision, disclosed, release blocker)"}],
            "gates": GATES, "answers": answers}
