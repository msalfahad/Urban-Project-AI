"""R8.15 lab registers: every JSON register of the R8.15 package from the r8_15_qortuba build (no number typed in).

Owner actions, owner physical facts, the Urban method rule, duct authority, passage heads, marble threshold policy /
register / main entrance, skirting policy + register, opening reveals, the US-07 depth review, Q-13 / Q-14 status, the
six-row status, digests, source anchor, closure release, decision register (recommendation first, answers 1-34).
"""

from __future__ import annotations

import json
from pathlib import Path

import r8_15_qortuba as Q
from engine.source import closure_release as CR, door_transition as DT, marble_thresholds as MT
from engine.source import obstacle_authority as OA, opening_reveals as OR, owner_facts as OF, run_manifest as RM
from engine.source import topology_closures as TC, trade_strips as TS, wall_bands as WB, wall_contact_path as WC

ROOT = Path(__file__).resolve().parents[2]
GATES = {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO", "PRODUCTION_MIGRATION": "NO"}
REG14 = ROOT / "tests/r8_14/registers"
REG15 = ROOT / "tests/r8_15/registers"


def jl(p):
    return json.loads(Path(p).read_text())


def _row_view(rid, row, dig):
    eff, aud = row["strip_effect"], row["strip_audit"]
    ta = row["trade_authority"]
    return {"row": rid, "STATE": row["state"], "VALUE": row["value"], "unit": "m2", "final": False,
            "BASE_PHYSICAL_SITES": [{"site": u["site"], "zones": u["zones"], "area_m2": u["area_m2"]}
                                    for u in row["sites_used"]],
            "BASE_SITE_AREA_M2": row["base_site_area_m2"],
            "THRESHOLD_TREATMENT": [{"strip": a["strip"], "state": a["state"], "contribution_m2": a["contribution_m2"]}
                                    for a in aud if a["kind"] == "THRESHOLD"],
            "THRESHOLD_CONTRIBUTION_M2": eff["threshold_contribution_m2"],
            "MARBLE": {"thresholds": row["marble_thresholds_touching"],
                       "excluded_from_this_row_m2": round(sum(m["marble_area_m2"] for m in row["marble_thresholds_touching"]),
                                                          6), "marble_counted_in": "MARBLE_THRESHOLD row only"},
            "PASSAGE_TREATMENT": [{"strip": a["strip"], "state": a["state"], "area_m2": a["area_m2"],
                                   "head_authority": a.get("head_authority")} for a in aud if a["kind"] == "OPEN_PASSAGE"],
            "SOFFIT_EXCLUSION_M2": eff["soffit_exclusion_m2"],
            "DUCT_TREATMENT": row["duct_treatment"],
            "OBJECT_FOOTPRINT_POLICY": dig["ROW_AUTHORITY_DIGEST"]["footprint_policies"] or
            [f"NONE ({(row.get('footprint_authority') or {}).get('treatment') or 'no authority'})"],
            "SEMANTIC_CLASSES": None if rid == "Q-14" else Q.R13.ROW_CLASS[rid],
            "TRADE_AUTHORITY": [ta["rule"]] + ([ta["semantic_class_rule"]] if ta.get("semantic_class_rule") else []),
            "TOPOLOGY_POLICY": f"{WB.POLICY_ID} ({WB.policy_record()['digest'][:16]}) + {TC.POLICY_ID}",
            "TOPOLOGY_DIGEST": dig["TOPOLOGY_RUN_INPUT_DIGEST"],
            "ROW_AUTHORITY_DIGEST": dig["ROW_AUTHORITY_DIGEST"]["digest"],
            "RELEASE_INPUT_DIGEST": dig["RELEASE_INPUT_DIGEST"]["digest"],
            "OWNER_FACTS_APPLIED": dig["ROW_AUTHORITY_DIGEST"]["owner_facts_applied"],
            "SOURCE_ANCHOR": row["source_anchor"], "RELEASE_BLOCKERS": row["release_blockers"],
            "COUNTERFACTUALS": {k: row[k] for k in ("counterfactual_door_reveal_excluded",) if row.get(k) is not None},
            "blockers": row["blockers"], "blocker_classes": row["blocker_classes"]}


def registers(ctx):
    rows, dig = ctx["rows_new"], ctx["dig"]
    rec = jl(ROOT / "research/external_engine_lab/r8_15_recommendation.json")
    six = {rid: _row_view(rid, rows[rid], dig[rid]) for rid in Q.ROWS}
    r814 = jl(REG14 / "QORTUBA_R8_14_STATUS.json")
    ths = ctx["thresholds_new"]
    sk = ctx["skirting"]
    skr = sk["recomputed"]
    FZ = jl(REG15 / "R8_15_SKIRTING_FREEZE.json")
    pf = ctx["pfacts"]
    regs = {}
    # ------------------------------------------------------------------ owner side
    jr = sk["return_to_frame_counterfactual_lm"]
    regs["OWNER_ACTION_REGISTER"] = {
        "SCHEMA": "URBAN_OWNER_ACTION_REGISTER_V12", "headline": "NO OWNER ACTION REQUIRED.", "required_now": [],
        "answered_this_round": [{"fact": f.ref, "kind": f.kind} for f in pf.values() if f.fact_id != Q.R14.OF11.FACT_ID]
        + [{"rule": ctx["rule"].ref, "kind": "URBAN_OWNER_METHOD_RULE"}],
        "why_none": "every row - the six area rows, the skirting row and the marble threshold row - computes in "
                    "SHADOW; what remains are release items carried as explicit blockers with counterfactual values",
        "prepared_for_release_stage_not_asked": [
            {"id": "QORTUBA_SKIRTING_JAMB_RETURNS", "only_if": "release of the skirting row is requested",
             "question": "Hidden skirting at door and open-passage jambs: does it stop at the room face (as the "
                         "opening-width deduction implies) or return into the jamb up to the door frame?",
             "effect_lm": jr, "current": "NO_RETURN (rule-store method; no rule adds a return)"}],
        "do_not_ask": ["duct identity", "M.B.ROOM / DRESS head", "main entrance marble", "wet / service marble "
                       "threshold", "20 mm rise", "the selected plan", "the unit", "7116-7119", "H2430 / H2431",
                       "Hall / Lobby geometry and height", "floor under wardrobes", "the 3.20 m height",
                       "basic skirting", "window deduction (QP-09 closed it)", "any expected quantity"]}
    regs["OWNER_PHYSICAL_FACT_REGISTER"] = {
        "SCHEMA": "URBAN_R8_15_OWNER_PHYSICAL_FACT_REGISTER_V1", "policy": OF.policy_record(),
        "file": "data/registry/OWNER_PHYSICAL_FACTS.json",
        "facts": [{"ref": f.ref, "kind": f.kind, "scope": f.scope, "statement": f.statement,
                   "allowed_domains": list(f.allowed_domains), "parts_bound": len(f.parts),
                   "binding": {"NEW_K2": b["binding"],
                               "OLD_K1": dict((g.ref, c["binding"]) for g, c in ctx["pb_old"])[f.ref]}}
                  for f, b in ctx["pb_new"]],
        "topology_effect": "NONE: no fact is a TS01 input (the duct hole already exists; the passage strip and the "
                           "threshold sites already exist) - the topology digest is the frozen blind V5 digest",
        "never": ["a topology role", "a re-layered CAD entity", "a transfer to the old revision / DWG / another project"]}
    rr = jl(Q.RULES)["rules"][0]
    regs["OWNER_METHOD_RULE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_15_OWNER_METHOD_RULE_REGISTER_V1", "file": "data/registry/URBAN_OWNER_METHOD_RULES.json",
        "rules": [dict(rr, ref=ctx["rule"].ref)],
        "room_type_map_for_marble": {"BATH": Q.MARBLE_ROOM_TYPES["BATH"], "PAINTRY": Q.MARBLE_ROOM_TYPES["PAINTRY"],
                                     "dry rooms": Q.DRY_TYPE, "outside the unit": [None, "no apartment room type"]},
        "kitchen_ironing_laundry_in_this_plan": "no door of the selected plan serves a KITCHEN, IRONING or "
                                                "WASHING / LAUNDRY room (no such labels; PAINTRY has no doorway)",
        "supersession": "the R8.14 dry / wet 50 / 50 split is superseded ONLY where this rule applies (all three "
                        "BATH doors); the split fact stays in force for any dry / wet door the rule does not cover",
        "never": rr["never"]}
    # ------------------------------------------------------------------ duct / passage
    bed = next(o for o in ctx["obstacles_new"] if o["labels"])
    regs["DUCT_AUTHORITY_REGISTER"] = {
        "SCHEMA": "URBAN_R8_15_DUCT_AUTHORITY_REGISTER_V1", "policy": OA.policy_record(), "fact": pf[Q.DUCT].ref,
        "parts": [{"key": k, "reading": r} for k, _fp, r in pf[Q.DUCT].parts],
        "entity_authority": ctx["authority_new"], "holes": ctx["obstacles_new"],
        "footprint_from_source_m2": {"H2060 outer loop (shoelace)": ctx["loop_outer_area_m2"].get("2060"),
                                     "TS01 BED.ROOM hole": bed["hole_area_m2"],
                                     "agree": ctx["loop_outer_area_m2"].get("2060") == bed["hole_area_m2"]},
        "floor": "EXCLUDED_FROM_ROOM_FLOOR (Q-13)", "ceiling": "EXCLUDED_FROM_NORMAL_CEILING (Q-14)",
        "skirting": f"its {skr['components_lm'][WC.OBSTACLE_FACE]} lm room-facing perimeter is OBSTACLE_FACE on the "
                    "path, included by the frozen method (owner 'all real walls' + rule-store section E)",
        "v5_band_state": "GEOMETRIC_BAND_CANDIDATE (unchanged - desirable separation of geometry and authority)",
        "old_revision": {k: v["state"] for k, v in ctx["authority_old"].items()},
        "never": ["closed rectangle + X = duct", "a material", "a topology change"]}
    regs["PASSAGE_HEAD_REGISTER"] = {
        "SCHEMA": "URBAN_R8_15_PASSAGE_HEAD_REGISTER_V1",
        "passages": [{"passage": p["passage_id"], "width_mm": round(p["width_mm"], 2),
                      "thickness_mm": round(p["thickness_mm"], 2), "site": p["strip_in_site"],
                      "head": ctx["heads"].get(p["passage_id"]), "authority": ctx["head_why"].get(p["passage_id"]),
                      "ceiling": {OR.WITH_HEAD: "SOFFIT_EXCLUDED_FROM_CEILING", OR.FULL_HEIGHT: "CEILING_CONTINUES"}.get(
                          ctx["heads"].get(p["passage_id"]), "outside the measured unit" if p["strip_in_site"] not in
                          {u["site"] for u in rows["Q-14"]["sites_used"]} else "HEAD_NOT_ESTABLISHED")}
                     for p in ctx["new"]["passages"]],
        "qp18": "NOT used: it is old-revision and states the opposite for both passages",
        "two_conditions_coexist": "Hall / Lobby WITH_HEAD (soffit out) and M.B.ROOM / DRESS FULL_HEIGHT (ceiling "
                                  "continues) in one Q-14 row",
        "ownership_guard": ctx["ownership_guard"] or "PASS"}
    # ------------------------------------------------------------------ marble
    mrec = ctx["marble"]
    regs["MARBLE_THRESHOLD_POLICY"] = {"SCHEMA": "URBAN_R8_15_MARBLE_THRESHOLD_POLICY_V1", "policy": MT.policy_record(),
                                       "door_transition": DT.policy_record()["policy_id"] + " (unchanged: MARBLE state "
                                       "already in V1)", "strip_audit": TS.policy_record_v2()["policy_id"],
                                       "rule": ctx["rule"].ref, "explicit_fact": pf[Q.ENTR].ref}
    regs["MARBLE_THRESHOLD_REGISTER"] = {
        "SCHEMA": "URBAN_R8_15_MARBLE_THRESHOLD_REGISTER_V1", "trade": MT.TRADE, "state": "COMPUTED_SHADOW",
        "unit": {"area": "m2", "length": "lm"},
        "thresholds": [dict(t["marble"], door_occurrence=t["door_occurrence"],
                            room_types={k: v["type"] for k, v in t["room_types"].items()},
                            sides={"A": t["side_A"].get("zones"), "B": t["side_B"].get("zones")},
                            source_geometry={"face_closures": t["face_closures"], "physical_site": t["physical_site"]},
                            project_specific_entrance=t["classification"] == "MAIN_ENTRANCE_MARBLE_EXPLICIT")
                       for t in ths if t["marble"]],
        "quantities": ctx["marble_quantities"],
        "release_blockers": ["SOURCE_ANCHOR: DXF anchored, DWG identity NOT_ESTABLISHED",
                             "SHADOW_ONLY: no baseline approval, no migration transaction, no release gate passed"],
        "never": ["a price", "a rate", "a volume", "20 mm as a plan dimension"]}
    ent = next(t for t in ths if t["classification"] == "MAIN_ENTRANCE_MARBLE_EXPLICIT")
    regs["MAIN_ENTRANCE_THRESHOLD_REGISTER"] = {
        "SCHEMA": "URBAN_R8_15_MAIN_ENTRANCE_THRESHOLD_REGISTER_V1", "fact": pf[Q.ENTR].ref,
        "door_occurrence": ent["door_occurrence"], "threshold": ent["threshold"], "marble": ent["marble"],
        "r8_14": {"allocation": ent["r8_14_allocation_state"], "porcelain_m2_then": 0.075,
                  "now": "superseded by the explicit fact"},
        "floor_interfaces": pf[Q.ENTR].statement["floor_interface"], "q13_porcelain_from_threshold_m2": next(
            (a["contribution_m2"] for a in rows["Q-13"]["strip_audit"] if a["strip"] == ent["threshold"]), None),
        "rise": "NOT_STATED (the Urban 20 mm rule does not apply to the entrance)",
        "water_containment": "NOT CLAIMED", "photo": "type only, never dimensions"}
    # ------------------------------------------------------------------ skirting
    regs["SKIRTING_PATH_POLICY"] = {"SCHEMA": "URBAN_R8_15_SKIRTING_PATH_POLICY_V1", "policy": WC.policy_record_v2(),
                                    "freeze": FZ, "method": FZ["qortuba_method"]}
    regs["SKIRTING_REGISTER"] = {
        "SCHEMA": "URBAN_R8_15_SKIRTING_REGISTER_V1", "row": "SKIRTING (hidden skirting, QP-06)", "unit": "lm",
        "state": "COMPUTED_SHADOW" if skr["complete"] else "INCOMPLETE", "SKIRTING_LM": skr["SKIRTING_LM"],
        "reproduces_blind": sk["reproduces_blind"], "per_room": skr["per_site"], "components_lm": skr["components_lm"],
        "excluded_lm": skr["excluded_lm"], "method": skr["method"],
        "counterfactuals": {"jamb_returns_to_frame_lm": jr, "with_returns_lm": sk["SKIRTING_LM_WITH_RETURNS_COUNTERFACTUAL"],
                            "door_jamb_returns": sk["door_jamb_returns"], "passage_jambs_lm": sk["passage_jambs_lm"],
                            "without_the_I1471_reveal_return_lm": sk.get("counterfactual_without_that_return_lm")},
        "hidden_profile": "US-08: the hidden profile runs on the SAME payable path - its own BOQ row, not merged "
                          "(not published this round)",
        "release_blockers": ["SOURCE_ANCHOR: DXF anchored, DWG identity NOT_ESTABLISHED",
                             f"JAMB_RETURN_METHOD_INFERRED: NO_RETURN from the rule-store method (no rule adds a "
                             f"return); returns to the frame would add {jr} lm"] + sk.get("release_blockers", []) +
                            ["SHADOW_ONLY: no baseline approval, no migration transaction, no release gate passed"],
        "post_blind_observation": sk["post_blind_observation"],
        "never": ["QP-10 / QP-11 (old revision 76.389 lm) as a target", "a room polygon perimeter"]}
    # ------------------------------------------------------------------ reveals / US-07
    rv = ctx["reveals"]
    regs["OPENING_REVEAL_REGISTER"] = {
        "SCHEMA": "URBAN_R8_15_OPENING_REVEAL_REGISTER_V1", "policy": OR.policy_record(),
        "passages": {pid: {"head": r["head"], "surfaces": r["surfaces"], "missing": r["missing"],
                           "ownership": r["ownership"], "depth": r["depth"]} for pid, r in rv.items()},
        "paint": "NOT ASSUMED", "plaster_quantity": "NOT PRODUCED (no wall face-set row; the reveal surfaces are "
                                                    "recorded once for R8.16)",
        "door_reveals": "not in this register (doors carry US-07 left / right / top reveals in the R8.16 face-set "
                        "engine)", "double_count_guard": ctx["ownership_guard"] or "PASS"}
    us = []
    for pid, r in rv.items():
        for s in r["surfaces"]:
            us.append({"opening": pid, "surface": s["surface"], "source_depth_m": round(s["depth_m"], 6),
                       "us07_depth_m": Q.US07_DEPTH, "area_source_m2": None if s["area_m2"] is None else
                       round(s["area_m2"], 6), "area_us07_m2": None if s.get("area_at_default_depth_m2") is None else
                       round(s["area_at_default_depth_m2"], 6), "used": s["depth_basis"]})
    regs["US07_REVEAL_DEPTH_REVIEW"] = {
        "SCHEMA": "URBAN_R8_15_US07_REVEAL_DEPTH_REVIEW_V1",
        "rule": "US-07 PLASTER_AND_PAINT_REVEALS_AT_0_25_M (a method default)",
        "governing": "US-10 SOURCE_DIMENSIONS_OVERRIDE_DEFAULTS: 'an actual drawing dimension is never overwritten by a "
                     "default, and a default never becomes source truth'",
        "recommendation": "US-07 0.25 m becomes FALLBACK-ONLY: used where no source reveal depth exists; where the "
                          "wall thickness at the opening is source-measured, the source depth governs and 0.25 m is "
                          "kept as a counterfactual",
        "implemented": "opening_reveals.reveal_depth (OPENING_REVEAL_POLICY_V2)", "surfaces": us,
        "rule_store_change": "none (the rule text is unchanged; its application order is now explicit)"}
    # ------------------------------------------------------------------ rows
    q13, q14 = rows["Q-13"], rows["Q-14"]
    r13v, r14v = r814["six_rows"]["Q-13"]["VALUE"], r814["six_rows"]["Q-14"]["VALUE"]
    regs["Q13_STATUS"] = dict(
        six["Q-13"], SCHEMA="URBAN_R8_15_Q13_STATUS_V1",
        rebuild="the dry tiled TS01 sites of the frozen V5 run + only the dry <-> dry continuous thresholds; marble "
                "thresholds belong to the MARBLE_THRESHOLD row; no R8.14 value is used",
        regression_vs_r8_14={"R8.14": r13v, "R8.15": q13["value"], "delta_m2": round(q13["value"] - r13v, 4),
                             "why": "the three BATH dry halves (0.18) and the entrance half (0.075) left porcelain for "
                                    "marble", "is_target": False}, historical_matching="NONE")
    regs["Q14_STATUS"] = dict(
        six["Q-14"], SCHEMA="URBAN_R8_15_Q14_STATUS_V1",
        rebuild="the ceiling sites of the frozen V5 run (duct hole out by owner authority) minus the Hall / Lobby "
                "soffit; the M.B.ROOM / DRESS footprint stays ceiling (FULL_HEIGHT); door thresholds NOT_IN_TRADE",
        regression_vs_r8_14={"R8.14": r14v, "R8.15": q14["value"], "delta_m2": round(q14["value"] - r14v, 4),
                             "is_target": False}, historical_matching="NONE")
    regs["QORTUBA_R8_15_STATUS"] = {
        "SCHEMA": "URBAN_R8_15_QORTUBA_STATUS_V1", "six_rows": six,
        "extra_rows": {"SKIRTING": {"state": regs["SKIRTING_REGISTER"]["state"], "value_lm": skr["SKIRTING_LM"],
                                    "release_blockers": regs["SKIRTING_REGISTER"]["release_blockers"]},
                       "MARBLE_THRESHOLD": {"state": "COMPUTED_SHADOW", **ctx["marble_quantities"],
                                            "release_blockers": regs["MARBLE_THRESHOLD_REGISTER"]["release_blockers"]}},
        "threshold_audit": [{k: t[k] for k in ("threshold", "door_occurrence", "classification", "allocation_state",
                                               "room_types", "width_mm", "thickness_mm", "strip_m2", "regions",
                                               "reconciles", "r8_14_allocation_state")} for t in ths],
        "doors_without_threshold_site": ctx["doors_without_threshold"],
        "rows_old": {rid: {"state": v["state"], "value": v["value"]} for rid, v in ctx["rows_old"].items()},
        "old_revision_unchanged_vs_r8_14": {rid: (ctx["rows_old"][rid]["state"], ctx["rows_old"][rid]["value"]) ==
                                            (r814["rows_old"][rid]["state"], r814["rows_old"][rid]["value"])
                                            for rid in Q.ROWS},
        "r8_14_rows_new": {rid: (v["STATE"], v["VALUE"]) for rid, v in r814["six_rows"].items()},
        "determinism": ctx["det"], "lab_reproduces_blind_v5": ctx["reproduces"],
        "final": "SHADOW only: no row is FINAL"}
    d14 = jl(REG14 / "DIGEST_HIERARCHY.json")["rows"]
    regs["DIGEST_HIERARCHY"] = {
        "SCHEMA": "URBAN_R8_15_DIGEST_HIERARCHY_V1", "layers": list(RM.DIGEST_LAYERS), "rows": dig,
        "vs_r8_14": {rid: {layer: ("CHANGED" if (dig[rid][layer] if layer == "TOPOLOGY_RUN_INPUT_DIGEST" else
                                                 dig[rid][layer]["digest"]) !=
                                   (d14[rid][layer] if layer == "TOPOLOGY_RUN_INPUT_DIGEST" else d14[rid][layer]["digest"])
                                   else "SAME") for layer in ("TOPOLOGY_RUN_INPUT_DIGEST", "ROW_AUTHORITY_DIGEST",
                                                              "RELEASE_INPUT_DIGEST")} for rid in Q.ROWS},
        "reasons": {"TOPOLOGY_RUN_INPUT_DIGEST": "SAME for every row: no topology policy changed, no fact is a TS01 "
                                                 "input",
                    "ROW_AUTHORITY_DIGEST": "every row through the row method (marble / obstacle / reveal policies); "
                                            "Q-03 / Q-11 / Q-13 by the marble rule + entrance fact, Q-13 / Q-14 by the "
                                            "duct fact, Q-14 by the full-height fact",
                    "RELEASE_INPUT_DIGEST": "row digest + release blockers (three owner blockers removed; the door "
                                            "reveal blocker added on Q-14)"}}
    regs["SOURCE_ANCHOR_STATUS"] = dict(ctx["source_anchor"], SCHEMA="URBAN_R8_15_SOURCE_ANCHOR_STATUS_V1")
    regs["CLOSURE_RELEASE_STATUS"] = {
        "SCHEMA": "URBAN_R8_15_CLOSURE_RELEASE_STATUS_V1", "policy": CR.policy_record(),
        "closures": ctx["closure_release"], "reached": sorted({v["level"] for v in ctx["closure_release"].values()}),
        "missing": sorted({m for v in ctx["closure_release"].values() for m in v["missing_for_reviewed"]}),
        "released": [], "ceiling": "REVIEWED_RELEASE_CANDIDATE at most; never production"}
    regs["R8_15_DECISION_REGISTER"] = decision_register(regs, ctx, rec, six)
    return regs, ctx


def decision_register(regs, ctx, rec, six):
    ths = ctx["thresholds_new"]
    sk = regs["SKIRTING_REGISTER"]
    du, ph = regs["DUCT_AUTHORITY_REGISTER"], regs["PASSAGE_HEAD_REGISTER"]
    mr, me = regs["MARBLE_THRESHOLD_REGISTER"], regs["MAIN_ENTRANCE_THRESHOLD_REGISTER"]
    q14 = regs["Q14_STATUS"]
    mbp = next(p for p in ph["passages"] if p["head"] == OR.FULL_HEIGHT)
    hlp = next(p for p in ph["passages"] if p["head"] == OR.WITH_HEAD)
    rule_t = [t["threshold"] for t in ths if t["classification"] == "URBAN_WET_SERVICE_MARBLE_RULE"]
    expl_t = [t["threshold"] for t in ths if t["classification"] == "MAIN_ENTRANCE_MARBLE_EXPLICIT"]
    wet_left = [r for t in ths for r in t["regions"] if r["treatment"] == "CERAMIC_WET_FLOOR"]
    dry_in_marble = [r for t in ths if t["marble"] for r in t["regions"] if r["treatment"] == "PORCELAIN_DRY_FLOOR"]
    remaining = {rid: v["RELEASE_BLOCKERS"] for rid, v in six.items()}
    remaining["SKIRTING"] = sk["release_blockers"]
    remaining["MARBLE_THRESHOLD"] = mr["release_blockers"]
    answers = {
        "1_duct_authorised": f"YES: {du['fact']} binds all eight H2060 / H2061 segments -> "
                             f"{sorted({v['state'] for v in du['entity_authority'].values()})}",
        "2_084_excluded_floor_and_ceiling": f"YES: {du['footprint_from_source_m2']} (floor Q-13 and ceiling Q-14)",
        "3_mb_dress_full_height_authoritative": f"YES: {mbp['authority']}",
        "4_mb_dress_ceiling_included": f"YES: {mbp['ceiling']} ({mbp['passage']}, {mbp['width_mm']} x "
                                       f"{mbp['thickness_mm']} mm)",
        "5_hall_soffit_excluded": f"YES: {hlp['ceiling']} ({six['Q-14']['SOFFIT_EXCLUSION_M2']} m2)",
        "6_entrance_explicit_marble": f"YES: {me['threshold']} = MARBLE_THRESHOLD_EXPLICIT ({me['fact']})",
        "7_q13_entrance_porcelain": f"NO: {me['q13_porcelain_from_threshold_m2']} m2",
        "8_marble_count": len(rule_t) + len(expl_t),
        "9_from_urban_rule": rule_t,
        "10_from_explicit_evidence": expl_t,
        "11_full_door_width": "YES: width = the face-closure length (the doorway opening between the jamb caps: "
                              + ", ".join(f"{m['threshold']} {m['clear_width_mm']} mm" for m in mr["thresholds"]) + ")",
        "12_20mm_vertical": "YES: vertical_rise_mm = 20 on the three rule thresholds; NOT_STATED on the entrance",
        "13_horizontal_depth": "the separation of the two face closures = wall thickness at the doorway: " +
                               ", ".join(sorted({f"{m['depth_mm']} mm" for m in mr["thresholds"]})) + " (source)",
        "14_wet_tile_stops": f"YES: no CERAMIC_WET_FLOOR region remains in any threshold ({len(wet_left)})",
        "15_dry_porcelain_stops": f"YES: no PORCELAIN region inside a marble strip ({len(dry_in_marble)})",
        "16_marble_double_counted": "NO: one region per marble strip, counted only in the MARBLE_THRESHOLD row; "
                                    f"every threshold reconciles: {all(t['reconciles'] for t in ths)}",
        "17_q03_q11": {rid: six[rid]["VALUE"] for rid in ("Q-03", "Q-11")},
        "18_q13": six["Q-13"]["VALUE"],
        "19_q14": six["Q-14"]["VALUE"],
        "20_skirting_computed": f"YES (SHADOW): {sk['state']}, frozen policy + method, blind run reproduced: "
                                f"{sk['reproduces_blind']}",
        "21_skirting_total_and_provenance": {"lm": sk["SKIRTING_LM"], "components_lm": sk["components_lm"],
                                             "excluded_lm": sk["excluded_lm"], "method": sk["method"],
                                             "policy": regs["SKIRTING_PATH_POLICY"]["policy"]["policy_id"],
                                             "freeze": regs["SKIRTING_PATH_POLICY"]["freeze"]["frozen_commit"][:12]},
        "22_remaining_skirting_blocker": [b for b in sk["release_blockers"] if not b.startswith(("SOURCE_ANCHOR",
                                                                                                "SHADOW_ONLY"))],
        "23_behind_wardrobes": "YES (furniture / wardrobes / joinery are never site boundaries)",
        "24_stops_at_doors_passages": "YES: doors, passages, glazed openings and (QP-09) windows are off the path; "
                                      "topology closures are zero",
        "25_duct_contact_path": f"YES: {sk['components_lm'][WC.OBSTACLE_FACE]} lm OBSTACLE_FACE, included only "
                                "because the duct has owner physical authority (without it: withheld, no number)",
        "26_wet_rooms_no_skirting": [f"{v['zones']}: {v['state']}" for v in sk["per_room"].values()
                                     if v["state"] == WC.NO_SKIRTING],
        "27_us07_fallback_only": regs["US07_REVEAL_DEPTH_REVIEW"]["recommendation"],
        "28_topology_version_bump": "NO: WALL_BAND_POLICY_V5 and TOPOLOGY_CLOSURE_POLICY_V1 unchanged; the topology "
                                    "digest equals the frozen blind V5 digest. Versioned: OWNER_PHYSICAL_FACT_POLICY_V2, "
                                    "OPENING_REVEAL_POLICY_V2, WALL_CONTACT_PATH_POLICY_V2 (frozen), new "
                                    "OBSTACLE_AUTHORITY_POLICY_V1 / MARBLE_THRESHOLD_POLICY_V1",
        "29_h2430_h2431_regress": f"NO: closures reproduce the blind V5 record ({ctx['reproduces']})",
        "30_source_anchor": ctx["source_anchor"]["state"],
        "31_release_blockers_remaining": remaining,
        "32_new_silent_error": [
            f"door {d['door_occurrence']} ({d['width_mm']} x {d['reveal_depth_mm']} mm, HALL <-> M.B.ROOM) has only ONE "
            "face closure: its two wall faces are offset at the door, so the frozen closure policy never forms closure "
            f"B. Its {d['reveal_area_m2']} m2 reveal lies inside the HALL site - counted as normal CEILING in Q-14 "
            f"since R8.13, its {d['jamb_cap_lm_in_room']} lm of jamb caps on the skirting path, and a wet door in the "
            "same condition would silently miss its marble threshold. Carried as DOOR_REVEAL_INSIDE_ROOM_SITE with "
            f"counterfactual Q-14 = {q14['COUNTERFACTUALS'].get('counterfactual_door_reveal_excluded')}"
            for d in ctx["doors_without_threshold"]] + [
            "the Hall / Lobby passage record lists only one of its two jamb faces (V2-O1): no value effect, the "
            "return counterfactual adds it explicitly"],
        "33_r8_16": rec["10_r8_16"] + " Plus: a frozen closure-B rule for door jambs with offset faces (I1471), "
                                      "blind, before any further ceiling / marble release.",
        "34_disagreements": rec["9_disagreements_with_chatgpt"]}
    return {"SCHEMA": "URBAN_R8_15_DECISION_REGISTER_V1", "recommendation_before_coding": rec,
            "order": ["recommendation (4471a71)", "facts + rule + engine + synthetic tests (e3705b7)",
                      "skirting freeze record (eed6464)", "blind Qortuba skirting run committed (873fc3a)",
                      "rows / registers afterwards"],
            "decisions": [
                {"id": "R815-D01", "decision": "duct = source-bound owner OBSTACLE authority; no topology change"},
                {"id": "R815-D02", "decision": "M.B.ROOM / DRESS FULL_HEIGHT -> ceiling continues; QP-18 unused"},
                {"id": "R815-D03", "decision": "entrance = MARBLE_THRESHOLD_EXPLICIT (whole strip, own BOQ row, no "
                                               "rise / water claim)"},
                {"id": "R815-D04", "decision": "URBAN-WET-SERVICE-MARBLE-THRESHOLD@v1 on a trade-scoped room-type map; "
                                               "supersedes the 50 / 50 split only where it applies"},
                {"id": "R815-D05", "decision": "WALL_CONTACT_PATH_POLICY_V2 + QORTUBA-NEW-SKIRTING-METHOD@v1 frozen, "
                                               "blind; QP-09 window deduction; NO_RETURN with counterfactual"},
                {"id": "R815-D06", "decision": "US-07 0.25 m fallback-only under US-10"},
                {"id": "R815-D07", "decision": "door I1471 (no closure B): disclosed release blocker + counterfactual, "
                                               "no post-result topology edit"}],
            "gates": GATES, "answers": answers}
