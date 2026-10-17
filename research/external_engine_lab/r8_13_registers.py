"""R8.13 lab registers: every JSON register of the R8.13 package from the r8_13_qortuba build (no number typed in).

Owner actions, owner finish facts + reconciliation, the floor object-footprint policy, semantic space classes,
the V4 policy, V3 defect resolution, Q-13 / Q-14 status, the six-row status, digest hierarchy, source anchor,
closure release model, decision register (recommendation first, answers 1-31).
"""

from __future__ import annotations

import json
from pathlib import Path

import r8_13_qortuba as Q
from engine.source import closure_release as CR, owner_facts as OF, owner_method_facts as MF, run_manifest as RM
from engine.source import topology_closures as TC, trade_regions as TR, trade_strips as TS, wall_bands as WB

ROOT = Path(__file__).resolve().parents[2]
GATES = {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO", "PRODUCTION_MIGRATION": "NO"}


def _row_view(rid, row, dig, ctx):
    fp = row["footprint_authority"]
    return {"row": rid, "STATE": row["state"], "VALUE": row["value"], "unit": "m2", "final": False,
            "TOPOLOGY_POLICY": f"{WB.POLICY_ID} ({WB.policy_record()['digest'][:16]}) + {TC.POLICY_ID}",
            "RUN_DIGEST": dig["TOPOLOGY_RUN_INPUT_DIGEST"],
            "ROW_AUTHORITY_DIGEST": dig["ROW_AUTHORITY_DIGEST"]["digest"],
            "RELEASE_INPUT_DIGEST": dig["RELEASE_INPUT_DIGEST"]["digest"],
            "PHYSICAL_SITES": [{"site": u["site"], "zones": u["zones"], "area_m2": u["area_m2"]}
                               for u in row["sites_used"]],
            "SEMANTIC_CLASSES": None if rid == "Q-14" else Q.ROW_CLASS[rid],
            "TRADE_RULES": [row["trade_authority"]["rule"]] + ([row["trade_authority"]["semantic_class_rule"]]
                                                               if row["trade_authority"].get("semantic_class_rule")
                                                               else []),
            "OBJECT_FOOTPRINT_POLICY": dig["ROW_AUTHORITY_DIGEST"]["footprint_policies"] or
            [f"NONE ({fp.get('treatment') or 'no authority'})"],
            "THRESHOLD_PASSAGE_TREATMENT": {"policy": TS.POLICY_ID, **row["strip_effect"],
                                            "audit": row["strip_audit"]},
            "OWNER_FACTS_CLAIMS": {"row_claims": row["claims_applied"],
                                   "facts_applied_to_row": dig["ROW_AUTHORITY_DIGEST"]["owner_facts_applied"],
                                   "facts_applied_at_release": dig["RELEASE_INPUT_DIGEST"]["owner_facts_applied"],
                                   "fact_outcomes": {f: v["rows"][rid] for f, v in ctx["outcomes"].items()}},
            "SOURCE_ANCHOR": row["source_anchor"], "RELEASE_BLOCKERS": row["release_blockers"],
            "blockers": row["blockers"], "blocker_classes": row["blocker_classes"]}


def registers(ctx):
    rows, dig, r812 = ctx["rows_new"], ctx["dig"], ctx["r812"]
    new, old = ctx["new"], ctx["old"]
    blind, freeze = ctx["blind"], ctx["freeze"]
    rec = json.loads((ROOT / "research/external_engine_lab/r8_13_recommendation.json").read_text())
    ff, fp = ctx["floor_fact"], ctx["q13_policy"]
    B = blind["NEW_K2"]
    c30 = next(c for c in B["closures"] if "2430" in c["evidence"])
    c31 = next(c for c in B["closures"] if "2431" in c["evidence"])
    b12 = json.loads((ROOT / "tests/r8_12/registers/BLIND_QORTUBA_RESULT.json").read_text())["NEW_K2"]
    c30_12 = next(c for c in b12["closures"] if "2430" in c["evidence"])
    c31_12 = next(c for c in b12["closures"] if "2431" in c["evidence"])
    w30 = next(b for b in B["watched_bands"] if "2430" in json.dumps(b["ends"]))
    hallp = next(p for p in B["passages"] if abs(p["width_mm"] - 1196.45) < 0.01)
    q13, q14 = rows["Q-13"], rows["Q-14"]
    regs = {}
    # ------------------------------------------------------------------ owner side
    regs["OWNER_ACTION_REGISTER"] = {
        "SCHEMA": "URBAN_OWNER_ACTION_REGISTER_V10", "headline": "NO OWNER ACTION REQUIRED.", "required_now": [],
        "answered": [{"action_id": "QORTUBA_FLOOR_UNDER_BUILT_IN_WARDROBES", "answer": ff.statement["text"],
                      "recorded_as": f"{ff.ref} -> {fp.policy_id}@v{fp.version} {fp.trade} {fp.treatment}"}],
        "why_none": "all six new-revision rows compute in SHADOW; every remaining item is an engineering / release "
                    "item (source anchor, strip allocation, passage soffit, cross-route, human review)",
        "do_not_ask": ["the selected plan", "the unit", "7116-7119", "the xref scope", "H2430 / H2431",
                       "the Hall / Lobby passage", "passage width / height", "the Q-14 ceiling footprint",
                       "the floor under wardrobes / furniture", "any expected quantity"]}
    rule_refs = [{"ref": "QP-01 QORTUBA_WALL_TILE_HEIGHT = 3.00 m", "trade": "WALL_TILE", "attribute": "HEIGHT_M",
                  "value": 3.00, "scope": "Qortuba (old revision rule store)"},
                 {"ref": "QP-14 QORTUBA_DRY_FLOOR_FINISH = PORCELAIN", "trade": "FLOOR_FINISH",
                  "attribute": "FINISH", "value": "PORCELAIN", "scope": "Qortuba dry floor"}]
    conflicts = MF.conflicts([f for f in ctx["mfacts"]], [{k: v for k, v in r.items() if k != "scope"}
                                                          for r in rule_refs])
    regs["OWNER_FINISH_FACT_REGISTER"] = {
        "SCHEMA": "URBAN_R8_13_OWNER_FINISH_FACT_REGISTER_V1", "policy": MF.policy_record(),
        "file": "data/registry/OWNER_FINISH_FACTS.json",
        "facts": [{"ref": f.ref, "kind": f.kind, "scope": f.scope, "statement": f.statement, "unit": f.unit,
                   "allowed_domains": list(f.allowed_domains), "transfer_forbidden": list(f.transfer_forbidden),
                   "binding": {"NEW_K2": b["binding"], "OLD_K1": dict((g.ref, c["binding"]) for g, c in
                                                                     ctx["binds_old"])[f.ref]},
                   "relations": list(f.relations), "row_outcomes": ctx["outcomes"][f.ref]["rows"]}
                  for f, b in ctx["binds_new"]],
        "reconciliation": [dict(r, fact=f.ref) for f in ctx["mfacts"] for r in f.relations],
        "silent_contradictions": conflicts,
        "rule": "same meaning -> CORROBORATING / MORE_SPECIFIC; a change -> SUPERSEDED_IN_SCOPE with its exact scope; "
                "never two in-force statements of different value",
        "physical_fact_unchanged": {"ref": ctx["pfact"].ref, "domains": ctx["outcomes"][ctx["pfact"].ref]["domains"]}}
    regs["TRADE_OBJECT_FOOTPRINT_POLICY"] = {
        "SCHEMA": "URBAN_R8_13_TRADE_OBJECT_FOOTPRINT_POLICY_V1",
        "policies": [{"policy": f"{p.policy_id}@v{p.version}", "trade": p.trade, "object_class": p.object_class,
                      "treatment": p.treatment, "authority": p.authority, "scope": p.scope,
                      "source_refs": list(p.source_refs)} for p in (Q.Q11.CEILING_FOOTPRINT, fp)],
        "applied_to": {"Q-13": f"{fp.policy_id}@v{fp.version}", "Q-14": f"{Q.Q11.CEILING_FOOTPRINT.policy_id}@v"
                       f"{Q.Q11.CEILING_FOOTPRINT.version}", "Q-03 / Q-03P / Q-11 / Q-12": "NONE (out of scope: "
                       "wet / service floors)"},
        "leak_check_other_rows_changed": ctx["leak"],
        "q13_without_the_policy": ctx["q13_without"],
        "blockers_cleared_by_the_policy": [
            {"site": x["site"], "zones": x["zones"], "cleared": sorted({f"{b['class']}:{b['issue']}" + (
                f":{b['detail'].get('source')}" if isinstance(b["detail"], dict) and b["detail"].get("source") else "")
                for b in x["blockers"]})} for x in ctx["q13_without"]["blockers"]],
        "never": ["'ignore furniture globally'", "a role for SF3 / FIRNTUR", "a topology input",
                  "a transfer to another revision / project"]}
    regs["SEMANTIC_SPACE_CLASS_REGISTER"] = {
        "SCHEMA": "URBAN_R8_13_SEMANTIC_SPACE_CLASS_REGISTER_V1",
        "rule": {"id": f"{Q.SPACE_CLASSES_V2.rule_id}@v{Q.SPACE_CLASSES_V2.version}", "authority":
                 Q.SPACE_CLASSES_V2.authority, "refs": list(Q.SPACE_CLASSES_V2.source_refs),
                 "scope": Q.SPACE_CLASSES_V2.scope, "by_label": Q.SPACE_CLASSES_V2.by_label,
                 "otherwise_class": Q.SPACE_CLASSES_V2.otherwise_class,
                 "scope_labels": list(Q.SPACE_CLASSES_V2.scope_labels)},
        "supersedes": "QORTUBA-SPACE-CLASS@v1 (BATH -> WET_ROOM renamed WET_SERVICE_ROOM; PAINTRY keeps SERVICE_ROOM "
                      "under QP-07; DRY_INTERNAL_ROOM unchanged)",
        "classes": {"DRY_INTERNAL_ROOM": "floor porcelain (QP-14) + skirting lm; object footprints INCLUDED (R8.13)",
                    "WET_SERVICE_ROOM": "floor + wall ceramic / porcelain to 3.20 m (this Qortuba revision only)",
                    "SERVICE_ROOM": "PAINTRY: QP-07 kitchen / preparation zone - floor + wall ceramic; the 3.20 m "
                                    "reaches it through QP-07 (the owner's KITCHEN)",
                    "PASSAGE": "an OPEN_PASSAGE_SITE strip (inside a site; audited per row)",
                    "THRESHOLD": "a door-threshold site (separate site; audited per row)",
                    "OBSTACLE_INTERIOR": "the interior of a proven obstacle (no finish trade)"},
        "owner_room_types": Q.OWNER_ROOM_TYPES,
        "floor_treatment_by_class": Q.FLOOR_BY_CLASS_V2,
        "never": ["word similarity ('BATHROOM' ~ 'BATH' is NOT how BATH is mapped: the exact label text is listed)",
                  "a universal English classifier", "a raw label as a trade identity"]}
    wet = next(f for f in ctx["mfacts"] if f.kind == "FINISH_SCOPE")
    dry = next(f for f in ctx["mfacts"] if f.kind == "MEASUREMENT_UNIT")
    regs["WET_SERVICE_FINISH_SCOPE"] = {
        "SCHEMA": "URBAN_R8_13_WET_SERVICE_FINISH_SCOPE_V1", "fact": wet.ref, "statement": wet.statement,
        "scope": wet.scope, "transfer_forbidden": list(wet.transfer_forbidden),
        "wall_finish_height_m": wet.statement["wall_finish_height_m"],
        "applies_to_labels": {"BATH": "WET_SERVICE_ROOM", "PAINTRY": "SERVICE_ROOM via QP-07"},
        "quantity": "NOT_COMPUTED: no tested wall-ceramic face-set path for this revision; never gross perimeter x "
                    "3.20", "supersession": [r for r in wet.relations if r["relation"] == MF.SUPERSEDED_IN_SCOPE]}
    regs["SKIRTING_METHOD_FACT"] = {
        "SCHEMA": "URBAN_R8_13_SKIRTING_METHOD_FACT_V1", "fact": dry.ref, "statement": dry.statement,
        "unit": "lm", "quantity": "NONE (no skirting row in R8.13)", "behind_wardrobe_path": "NOT INVENTED",
        "method": "UNCHANGED (QP-08: no wardrobe / joinery deduction from skirting or profile)"}
    # ------------------------------------------------------------------ topology side
    bd = ctx["band_diff"]
    regs["WALL_BAND_V4_POLICY"] = {"SCHEMA": "URBAN_R8_13_WALL_BAND_V4_POLICY_V1", "policy": WB.policy_record(),
                                   "closure_policy": TC.policy_record(), "freeze": freeze}
    nv = B["v4"]
    regs["V3_DEFECT_RESOLUTION"] = {
        "SCHEMA": "URBAN_R8_13_V3_DEFECT_RESOLUTION_V1",
        "V3_D1": {"root_cause": "the V3 chain id was revision + region + ENTITY + extent: the sub-part index was "
                                "stripped (_entity) and the supporting line was not in it, so the parallel sides of "
                                "one closed polyline with the same extent shared an id; detect() then indexed chains "
                                "and candidates by that id (byc / cand), collapsing two chains into one entry",
                  "fix": "V4: keep the V3 id where unique; chains of the same entities and extent are told apart by "
                         "their supporting line; band ids from the two chain ids; collisions fail closed",
                  "blind_result": {"chain_id_collisions": nv["chain_id_collisions"],
                                   "line_disambiguated": nv["chains_line_disambiguated"],
                                   "chain_ids_unique": nv["chain_ids_unique"], "band_ids_unique": nv["band_ids_unique"]},
                  "state": "RESOLVED"},
        "V3_D2": {"root_cause": "elongation was tested on the RAW chain overlap (215 native) while the pair 574 / 584 is "
                                "locally mutual nearest only across the core of the perpendicular end wall (570 / 579): "
                                "a 150 mm local run against a 1800 mm separation - another wall's core seen crosswise",
                  "fix": "V4 ASSEMBLY_STRUCTURAL_SUPPORT on the LOCAL run (inherited only across a full-width "
                         "structural loop from a self-supported run of the same pair); structural passage sides",
                  "blind_result": {"unsupported_touching_findings": nv["unsupported_touching_r8_12_findings"],
                                   "inherited_support_used": nv["inherited"],
                                   "false_passage_OP_a38c9a827025e4a9": "GONE" if not any(
                                       p["width_mm"] == 6000.0 for p in B["passages"]) else "PRESENT",
                                   "old_revision_false_passages": "GONE: OP-c624f362e720d083 (6000 x 1800) and "
                                   "OP-09badb0314071752 (4600 x 600, pair 551 / 817, 150 mm run vs 600 mm)"
                                   if not any(p["width_mm"] in (6000.0, 4600.0) for p in blind["OLD_K1"]["passages"])
                                   else "PRESENT"},
                  "state": "RESOLVED"},
        "band_diff_v3_to_v4": bd,
        "post_blind_observations_for_r8_14": [
            {"id": "V4-O1", "what": "H2060 (2100 x 400 mm closed polyline, WALL layer) with H2061 nested inside it "
                                    "100 mm in on every side: V4 reads the 100 mm ring as ESTABLISHED bands (V3 showed "
                                    "them AMBIGUOUS only because of the D1 dictionary collapse)",
             "effect": "no closure, no passage, no row", "question": "a ring between nested closed polylines on a wall "
                                                                      "layer: shaft wall or symbol? (role, not band "
                                                                      "geometry)", "action": "R8.14, not patched"},
            {"id": "V4-O2", "what": "a square local run (run == separation, pair 545 / 549 old revision, 150 x 150 mm) "
                                    "is decided by floating-point noise at the elongation equality (V3 and V4 alike)",
             "effect": "old revision only; no row", "action": "R8.14: state an explicit tie rule for "
                                                                "elongation_ratio (a policy parameter), not patched"}]}
    regs["BLIND_COMPARISON"] = {
        "SCHEMA": "URBAN_R8_13_BLIND_COMPARISON_V1", "order": "blind record committed (c522916) before this comparison",
        "lab_reproduces_blind": ctx["reproduces"],
        "counts": {"R8.12_V3": b12["counts"], "R8.13_V4": B["counts"]},
        "h2430": {"band": w30["band_id"], "faces": w30["faces"],
                  "intervals": [(iv["class"], iv["by"]) for iv in w30["intervals"]],
                  "ends": [e["kind"] for e in w30["ends"]], "closure_v4": {k: c30[k] for k in ("closure_id", "release",
                                                                                                "geometry", "material")},
                  "separated_m2": [p["area_m2"] for p in c30["safety"]["separated_pieces"]],
                  "same_geometry_as_v3": c30["geometry"] == c30_12["geometry"],
                  "same_area_as_v3": [p["area_m2"] for p in c30["safety"]["separated_pieces"]] ==
                  [p["area_m2"] for p in c30_12["safety"]["separated_pieces"]],
                  "support": "SELF_SUPPORTED (one run; the H718 column interval inside it)"},
        "h2431": {"closure_v4": {k: c31[k] for k in ("closure_id", "release", "geometry", "material")},
                  "separated_m2": [p["area_m2"] for p in c31["safety"]["separated_pieces"]],
                  "same_geometry_as_v3": c31["geometry"] == c31_12["geometry"],
                  "same_area_as_v3": [p["area_m2"] for p in c31["safety"]["separated_pieces"]] ==
                  [p["area_m2"] for p in c31_12["safety"]["separated_pieces"]],
                  "passage_open": {"passage": hallp["passage_id"], "width_mm": hallp["width_mm"],
                                   "thickness_mm": hallp["thickness_mm"]}},
        "h1316": {"closures_with_1316": [c for c in B["closures"] if "1316" in c["evidence"]],
                  "classification": "NOT_WALL_CAP (unchanged)"},
        "hall_m2": {"R8.12": b12["hall"]["area_m2"], "R8.13": B["hall"]["area_m2"]},
        "labelled_site_areas_unchanged": b12["labelled_sites"] == B["labelled_sites"],
        "ids": "band / closure / passage / site ids changed (version bump: band ids from chain ids) - geometry is "
               "compared, old ids are never forced",
        "passages": {"R8.12": [p["passage_id"] for p in b12["passages"]], "R8.13": [p["passage_id"] for p in
                                                                                   B["passages"]]},
        "topology_digest": {"R8.12": b12["run_input_digest"], "R8.13": B["run_input_digest"],
                            "changed_because": "the wall-band policy (V3 -> V4) is a TS01 input"}}
    # ------------------------------------------------------------------ rows
    six = {rid: _row_view(rid, rows[rid], dig[rid], ctx) for rid in Q.ROWS}
    old12 = r812["OLD_K1_R8_12"]
    q14_change = "SAME" if q14["value"] == Q.Q14_R8_12 else "CHANGED"
    regs["Q14_STATUS"] = dict(six["Q-14"], SCHEMA="URBAN_R8_13_Q14_STATUS_V1",
                              regression={"R8.12": Q.Q14_R8_12, "R8.13": q14["value"], "result": q14_change,
                                          "reason": "V4 changed no apartment site: the two authorised closures keep "
                                                    "their geometry and every labelled site its area; the removed "
                                                    "pseudo-band / passage lay outside the apartment"
                                          if q14_change == "SAME" else "see sites",
                                          "is_target": False},
                              sites_r8_12=[u for u in r812["NEW_K2_R8_12"]["Q-14"]["sites_used"]])
    regs["Q13_STATUS"] = dict(six["Q-13"], SCHEMA="URBAN_R8_13_Q13_STATUS_V1",
                              without_the_floor_fact={k: v for k, v in ctx["q13_without"].items()
                                                      if k != "blockers"},
                              r8_12={k: r812["NEW_K2_R8_12"]["Q-13"][k] for k in ("state", "value", "blocker_classes")},
                              object_footprints={"policy": f"{fp.policy_id}@v{fp.version}", "treatment": fp.treatment,
                                                 "implicit_objects": q13["implicit_object_footprints"],
                                                 "roles": "SF3 / FIRNTUR / joinery stay ROLE_UNRESOLVED; "
                                                          "ROLE_UNRESOLVED_BUT_NON_MATERIAL_TO_TRADE for Q-13"},
                              strips={"thresholds_excluded": [a for a in q13["strip_audit"] if a["state"] == TS.EXCLUDED],
                                      "passages_included": [a for a in q13["strip_audit"] if a["state"] == TS.INCLUDED],
                                      "blocking": q13["strip_effect"]["blocking"]},
                              historical_matching="NONE")
    regs["QORTUBA_R8_13_STATUS"] = {
        "SCHEMA": "URBAN_R8_13_QORTUBA_STATUS_V1", "six_rows": six,
        "rows_new": {rid: {k: v for k, v in rows[rid].items() if k not in ("strip_audit",)} for rid in Q.ROWS},
        "rows_old": {rid: {"state": v["state"], "value": v["value"]} for rid, v in ctx["rows_old"].items()},
        "old_revision_unchanged": {rid: (ctx["rows_old"][rid]["state"], ctx["rows_old"][rid]["value"]) ==
                                   (old12[rid]["state"], old12[rid]["value"]) for rid in Q.ROWS},
        "r8_12_rows_new": {rid: {"state": v["state"], "value": v["value"]} for rid, v in r812["NEW_K2_R8_12"].items()},
        "determinism": ctx["det"], "lab_reproduces_blind": ctx["reproduces"], "owner_passage": ctx["owner_passage"],
        "final": "SHADOW only: no row is FINAL"}
    regs["DIGEST_HIERARCHY"] = {
        "SCHEMA": "URBAN_R8_13_DIGEST_HIERARCHY_V1", "layers": list(RM.DIGEST_LAYERS), "rows": dig,
        "q13_row_authority_without_the_floor_fact": ctx["dig_q13_without_fact"]["ROW_AUTHORITY_DIGEST"]["digest"],
        "floor_fact": {"topology": "never a TS01 input -> TOPOLOGY digest identical with and without it",
                       "row": "Q-13 ROW_AUTHORITY only (footprint policy + owner fact applied)",
                       "other_rows": "absent from every other row digest (scoped out; leak check)",
                       "release": "inherits through the Q-13 row digest"},
        "changed_in_r8_13": {"TOPOLOGY_RUN_INPUT_DIGEST": "CHANGED for every row (V3 -> V4 is a topology input)",
                             "ROW_AUTHORITY_DIGEST": "CHANGED for every row (topology + class rule v2 + strip audit "
                                                     "method); Q-13 additionally by the floor fact",
                             "RELEASE_INPUT_DIGEST": "CHANGED for every row (row digest + STRIP_ALLOCATION blockers)"},
        "generic_in_engine": ["run_manifest.row_authority_digest / release_input_digest",
                              "owner_method_facts (binding, scope, policies_for, row_outcome, conflicts)",
                              "trade_strips (strip allocation audit)", "closure_release (evaluator)"],
        "still_lab": "the Qortuba row assembly (site selection by treatment, the six rows)"}
    regs["SOURCE_ANCHOR_STATUS"] = ctx["source_anchor"]
    regs["CLOSURE_RELEASE_MODEL"] = {"SCHEMA": "URBAN_R8_13_CLOSURE_RELEASE_MODEL_V1", "policy": CR.policy_record(),
                                     "closures": ctx["closure_release"],
                                     "cross_route_note": "the new revision exists only as a DXF (one decode route, "
                                                         "K2 / ezdxf); a second independent route needs the DWG "
                                                         "anchor or a pinned second DXF reader",
                                     "released": []}
    regs["ENGINEERING_ACTION_REGISTER"] = {"SCHEMA": "URBAN_ENGINEERING_ACTION_REGISTER_R8_13_V1", "actions": [
        {"id": "E-R8.14-01", "priority": 1, "title": "door-threshold strip allocation rule (Q-13 / Q-11 / Q-14 release)"},
        {"id": "E-R8.14-02", "priority": 1, "title": "DWG <-> DXF source anchor with a pinned decoder"},
        {"id": "E-R8.14-03", "priority": 2, "title": "passage soffit vs ceiling allocation (Q-14 release)"},
        {"id": "E-R8.14-04", "priority": 2, "title": "REVIEWED_FOR_RELEASE_CANDIDATE: cross-route + signed human "
                                                     "review record for the two closures"},
        {"id": "E-R8.14-05", "priority": 3, "title": "V4-O1 nested closed polylines on a wall layer (role)"},
        {"id": "E-R8.14-06", "priority": 3, "title": "V4-O2 explicit elongation tie rule"},
        {"id": "E-R8.14-07", "priority": 4, "title": "wall ceramic 3.20 m only on a tested face-set path"},
        {"id": "E-R8.14-08", "priority": 4, "title": "closure-id rounding into the closure policy record"}]}
    regs["R8_13_DECISION_REGISTER"] = decision_register(regs, ctx, rec, six)
    return regs, ctx


def decision_register(regs, ctx, rec, six):
    V = regs["V3_DEFECT_RESOLUTION"]
    BC = regs["BLIND_COMPARISON"]
    q13, q14 = regs["Q13_STATUS"], regs["Q14_STATUS"]
    D = regs["DIGEST_HIERARCHY"]
    ff = ctx["floor_fact"]
    answers = {
        "1_v3_d1_cause": V["V3_D1"]["root_cause"],
        "2_v4_identity_fix": V["V3_D1"]["fix"],
        "3_collisions": V["V3_D1"]["blind_result"],
        "4_v3_d2_cause": V["V3_D2"]["root_cause"],
        "5_short_span_handling": "spans are never tested alone: the LOCAL run (spans + column overlaps + nodes) "
                                 "carries elongation; a short run inherits only across a full-width structural loop "
                                 "from a self-supported run of the same pair (blind: inherited used "
                                 f"{len(V['V3_D2']['blind_result']['inherited_support_used'])} times)",
        "6_freeze": {k: ctx["freeze"][k] for k in ("frozen_commit", "wall_band_policy", "synthetic_test_digest",
                                                   "v4_synthetic_test_count", "qortuba_before_freeze")},
        "7_h2430": BC["h2430"],
        "8_h2431": BC["h2431"],
        "9_h1316": BC["h1316"],
        "10_false_passage": V["V3_D2"]["blind_result"]["false_passage_OP_a38c9a827025e4a9"] + "; old revision: " +
                            V["V3_D2"]["blind_result"]["old_revision_false_passages"],
        "11_new_defect": V["post_blind_observations_for_r8_14"],
        "12_q14_value": f"{q14['STATE']} {q14['VALUE']} m2 (SHADOW)",
        "13_q14_change": q14["regression"],
        "14_floor_policy_recorded": f"{ff.ref} -> {regs['TRADE_OBJECT_FOOTPRINT_POLICY']['applied_to']['Q-13']}",
        "15_includes_under_wardrobes": ff.statement["includes"],
        "16_topology_unchanged_by_the_fact": D["floor_fact"]["topology"],
        "17_q13_state": f"{q13['STATE']} {q13['VALUE']} m2 (SHADOW); without the fact: "
                        f"{q13['without_the_floor_fact']['state']}",
        "18_q13_blocker": q13["blocker_classes"] or "none for SHADOW",
        "19_threshold_passage_separate": {"thresholds": f"{len(q13['strips']['thresholds_excluded'])} separate sites, "
                                                        "excluded, STRIP_ALLOCATION release blocker",
                                          "passages": f"{len(q13['strips']['passages_included'])} inside the site, "
                                                      "same treatment on every side, INCLUDED and recorded"},
        "20_semantic_classes": regs["SEMANTIC_SPACE_CLASS_REGISTER"]["rule"]["by_label"],
        "21_3_20_scope": regs["WET_SERVICE_FINISH_SCOPE"]["scope"],
        "22_skirting_lm": regs["SKIRTING_METHOD_FACT"]["unit"],
        "23_no_raw_label_generic_rule": "the engine holds no room name: labels map to classes by an exact-text, "
                                        "scoped SemanticClassRule in the lab; the 3.20 m, the class names and the "
                                        "footprint decision are data",
        "24_which_digest_changed": D["changed_in_r8_13"],
        "25_source_anchor": ctx["source_anchor"]["state"] + " - " + ctx["source_anchor"]["why"],
        "26_q14_release_blockers": q14["RELEASE_BLOCKERS"],
        "27_q13_release_blockers": q13["RELEASE_BLOCKERS"],
        "28_six_row_states": {rid: (v["STATE"], v["VALUE"]) for rid, v in six.items()},
        "29_new_silent_error": "door-threshold strips (6 sites, "
                               f"{six['Q-13']['THRESHOLD_PASSAGE_TREATMENT']['excluded_area_m2']} m2) were LISTED in "
                               "the R8.12 rows but blocked nothing: the floor under the doors was in no row and in "
                               "no release blocker. R8.13 makes it an explicit STRIP_ALLOCATION release blocker",
        "30_r8_14": rec["10_r8_14_if_r8_13_succeeds"],
        "31_disagreements": rec["8_disagreements_with_chatgpt"]}
    return {"SCHEMA": "URBAN_R8_13_DECISION_REGISTER_V1", "recommendation_before_coding": rec,
            "order": ["recommendation written (r8_13_recommendation.json)",
                      f"V4 + synthetic tests committed: {ctx['freeze']['frozen_commit'][:12]}",
                      "freeze record committed", "blind run committed (BLIND_QORTUBA_V4_RESULT.json)",
                      "comparison, owner finish facts, rows afterwards"],
        "decisions": [
            {"id": "R813-D01", "decision": "WALL_BAND_POLICY_V4 (D1 identity, D2 local-run support, structural "
                                           "passage sides), frozen before the Qortuba run"},
            {"id": "R813-D02", "decision": "TOPOLOGY_CLOSURE_POLICY_V1 unchanged"},
            {"id": "R813-D03", "decision": "owner floor answer -> scoped FLOOR_FINISH FOOTPRINT_INCLUDED policy, "
                                           "applied ONLY to Q-13 after the frozen topology"},
            {"id": "R813-D04", "decision": "3.20 m: scoped wet / service finish fact (supersedes QP-01 in the new "
                                           "revision only); no wall quantity"},
            {"id": "R813-D05", "decision": "door thresholds excluded + STRIP_ALLOCATION release blocker; passage "
                                           "strips included only when every side agrees"},
            {"id": "R813-D06", "decision": "V4-O1 / V4-O2 recorded for R8.14; V4 not edited after the blind run"}],
        "gates": GATES, "answers": answers}
