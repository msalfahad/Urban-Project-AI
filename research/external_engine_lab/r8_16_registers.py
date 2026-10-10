"""R8.16 lab registers: every JSON register of the R8.16 package from the r8_16_qortuba build (no number typed in).

Owner actions, the owner method rules, window floor contact, door / doorless jamb method, the I1471 source audit, the
offset closure policy, skirting V3 policy + register, hidden profile, Q-13 / Q-14 status, marble regression, opening
reveals, wall-face engine readiness, source anchor, closure release, row status, decision register (answers 1-36).
The two blind records (CLOSURE_BLIND_RESULT / SKIRTING_BLIND_RESULT) are committed before this module ran and are
never rewritten here.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import r8_15_registers as R15G
import r8_16_qortuba as Q
from engine.source import owner_method_facts as MF, run_manifest as RM, topology as T, wall_contact_path as WC

ROOT = Path(__file__).resolve().parents[2]
GATES = {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO", "PRODUCTION_MIGRATION": "NO"}
REG15 = ROOT / "tests/r8_15/registers"
REG16 = ROOT / "tests/r8_16/registers"
RULES = ROOT / "data/registry/URBAN_OWNER_METHOD_RULES.json"
FACTS = ROOT / "data/registry/OWNER_METHOD_FACTS.json"
WIN_FACT = "QORTUBA-NEW-NORMAL-WINDOWS-ABOVE-FLOOR-OWNER-001"
SUP_FACT = "QORTUBA-NEW-SKIRTING-WINDOW-FLOOR-CONTACT-OWNER-001"
ROWS = Q.R15.ROWS


def jl(p):
    return json.loads(Path(p).read_text())


def r6(v):
    return round(v, 6)


def registers(ctx):
    base, _ = R15G.registers(ctx)
    rows, dig = ctx["rows_new"], ctx["dig"]
    rec = jl(ROOT / "research/external_engine_lab/r8_16_recommendation.json")
    six = {rid: R15G._row_view(rid, rows[rid], dig[rid]) for rid in ROWS}
    s15 = jl(REG15 / "QORTUBA_R8_15_STATUS.json")
    sk15 = jl(REG15 / "SKIRTING_REGISTER.json")
    fz = ctx["r8_16_freeze"]
    sk, cl = ctx["skirting_v3"], ctx["closure_v2"]
    facts = {f["fact_id"]: f for f in jl(FACTS)["facts"]}
    rules = {r["rule_id"]: r for r in jl(RULES)["rules"]}
    srule = rules["URBAN-SKIRTING-OPENING-METHOD"]
    regs = {}
    # ------------------------------------------------------------------ owner side
    gl = [w for w in sk["windows"] if not w["hosted_on_wall_face_line"]]
    regs["OWNER_ACTION_REGISTER"] = {
        "SCHEMA": "URBAN_OWNER_ACTION_REGISTER_V13",
        "headline": "NO OWNER ACTION REQUIRED FOR THE SHADOW ROWS. ONE OPTIONAL QUESTION FOR THE SKIRTING RELEASE.",
        "required_now": [],
        "optional_for_release": [
            {"id": "QORTUBA_HALL_PAINTRY_GLAZED_SCREEN_FLOOR_CONTACT", "blocks": "SKIRTING / HIDDEN_PROFILE release only",
             "question": "The internal glazed opening between HALL and PAINTRY (2.75 m wide, no wall line under it in "
                         "the DXF): does the glass stand on a low wall (skirting continues under it) or reach the "
                         "floor (skirting stops)?",
             "why_new": "it is not a 'normal window' of the owner's 1.00 m statement: no wall face line runs across "
                        "it, it is an internal screen, and QP-12 gives it a 2.20 m HEIGHT (door-like), not a sill. "
                        "Source exhausted: no section, elevation, schedule or sill text in the DXF",
             "effect_lm": sum(w["length_mm"] for w in gl) / 1000, "current": "FLOOR_CONTACT_UNPROVEN (withheld, "
                                                                            "never guessed)",
             "occurrences": [{"site": w["site"], "sources": w["sources"], "length_mm": w["length_mm"]} for w in gl]}],
        "answered_this_round": [{"fact": f"{WIN_FACT}@v1", "kind": "WINDOW_FLOOR_CONTACT"},
                                {"fact": f"{SUP_FACT}@v1", "kind": "SKIRTING_PATH (scoped supersession of QP-09)"},
                                {"rule": "URBAN-SKIRTING-OPENING-METHOD@v1", "kind": "URBAN_OWNER_METHOD_RULE"}],
        "do_not_ask": ["window skirting", "window sill in the selected Qortuba scope", "door jamb skirting",
                       "doorless-opening jamb skirting", "duct", "marble", "M.B.ROOM / DRESS passage head",
                       "Hall / Lobby passage", "the selected plan", "the unit", "any expected quantity"]}
    regs["OWNER_METHOD_RULE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_16_OWNER_METHOD_RULE_REGISTER_V1",
        "files": ["data/registry/URBAN_OWNER_METHOD_RULES.json", "data/registry/OWNER_METHOD_FACTS.json"],
        "urban_rules": list(rules.values()),
        "qortuba_facts": [facts[WIN_FACT], facts[SUP_FACT]],
        "fact_policy": MF.POLICY_ID,
        "qp09": {"rule": "QP-09 QORTUBA_SKIRTING_WINDOW_DEDUCTION = DEDUCT_EVERY_WINDOW_WIDTH",
                 "state": "ON FILE, UNCHANGED; superseded only in the scope of " + SUP_FACT + "@v1",
                 "relation": facts[SUP_FACT]["relations"][0]},
        "transfer_forbidden": facts[WIN_FACT]["transfer_forbidden"],
        "never": srule.get("never")}
    # ------------------------------------------------------------------ windows / doors / doorless
    regs["WINDOW_FLOOR_CONTACT_REGISTER"] = {
        "SCHEMA": "URBAN_R8_16_WINDOW_FLOOR_CONTACT_REGISTER_V1", "fact_binding": sk["windows_fact_binding"],
        "source_exhaustion": {"searched": ["window schedule", "sill text / dimension", "section", "elevation",
                                           "block attributes"],
                              "found": "NONE (the only SILL / SCHEDULE hits are AutoCAD AEC class names)",
                              "heights_not_sills": ["QP-22 window HEIGHT 1.50 m", "QP-12 HALL / PAINTRY glazed opening "
                                                                                  "HEIGHT 2.20 m"]},
        "windows": [dict(w, span=("SKIRTING_CONTINUITY_UNDER_WINDOW" if w["floor_contact"]["state"] == WC.ABOVE_FLOOR
                                  else "WITHHELD"), topology_effect="NONE (trade-only span)") for w in sk["windows"]],
        "continuity_lm": sk["components_lm"][WC.WINDOW_ABOVE_FLOOR],
        "withheld_lm": sk["withheld_lm"],
        "never": ["the 1.00 m transferred to another project / revision / the DWG", "a plan cut as floor contact",
                  "a window as a topology closure"]}
    dj = [j for j in sk["jamb_records"] if j["kind"] == WC.DOOR_JAMB]
    regs["DOOR_SKIRTING_POLICY"] = {
        "SCHEMA": "URBAN_R8_16_DOOR_SKIRTING_POLICY_V1", "rule": srule["method"]["DOOR_PRESENT"],
        "method_parameter": fz["qortuba_method"]["parameters"]["door"],
        "door_jambs": [{"opening": j["opening"], "side": j.get("side"), "length_lm": r6(j["length"] * ctx_u(ctx)),
                        "skirting_lm": 0.0, "plaster_surface": "YES (independent)"} for j in dj],
        "excluded_across_doors_lm": sk["excluded_lm"][WC.DOOR_PRESENT],
        "never_measured": ["door swing", "door frame", "closure line"],
        "jamb_return_inferred": "GONE: replaced by explicit owner authority (URBAN-SKIRTING-OPENING-METHOD@v1)"}
    dlj = [dict(j, site=sid) for sid, v in sk["per_site"].items() for j in v.get("jambs", [])]
    regs["DOORLESS_JAMB_REGISTER"] = {
        "SCHEMA": "URBAN_R8_16_DOORLESS_JAMB_REGISTER_V1", "rule": srule["method"]["DOORLESS_OPENING"],
        "jambs": [dict(j, record=("LEFT_PHYSICAL_JAMB" if j["side"] == "LEFT" else "RIGHT_PHYSICAL_JAMB")
                       if j["physical"] else "NOT_A_JAMB (continuous wall face)") for j in dlj],
        "counted_lm": r6(math.fsum(j["counted_lm"] for j in dlj)),
        "across_opening_lm": 0.0, "topology_closure_lm": sk["excluded_lm"][WC.TOPOLOGY_CLOSURE],
        "hall_far_jamb": next((j for j in dlj if j["source"].startswith("BANDEND|WB-6c88")), None),
        "v3_o1": ctx["v3_o1"]}
    # ------------------------------------------------------------------ I1471 / closure policy
    regs["I1471_SOURCE_AUDIT"] = ctx["i1471"]
    regs["OFFSET_CLOSURE_POLICY"] = {
        "SCHEMA": "URBAN_R8_16_OFFSET_CLOSURE_POLICY_V1", "policy": T.door_closure_policy_record(),
        "freeze": {k: fz[k] for k in ("frozen_commit", "door_closure_policy", "unchanged", "order", "amendments")},
        "in_run_manifest": RM.policy_digests()["door_opening_closure"],
        "blind_result": {"closure_b_rules": cl["closure_b_rules"], "closure_b_missing": cl["closure_b_missing"],
                         "old_revision": ctx["closure_blind"]["OLD_K1"]["closure_b_rules"]},
        "reproduced_by_the_lab": ctx["reproduces_r8_16"]}
    # ------------------------------------------------------------------ skirting
    regs["SKIRTING_V3_POLICY"] = {"SCHEMA": "URBAN_R8_16_SKIRTING_V3_POLICY_V1", "policy": WC.policy_record_v3(),
                                  "method": fz["qortuba_method"],
                                  "freeze": {k: fz[k] for k in ("frozen_commit", "wall_contact_path_policy",
                                                                "synthetic_test_count", "order", "rule", "amendments")}}
    blk = ctx["skirting_blockers"]
    c15, e15 = sk15["components_lm"], sk15["excluded_lm"]
    i1471_caps = r6(sk15["SKIRTING_LM"] - sk15["counterfactuals"]["without_the_I1471_reveal_return_lm"])
    recon = {"R8.15_SKIRTING_LM": sk15["SKIRTING_LM"],
             "+ windows now continuous": sk["components_lm"][WC.WINDOW_ABOVE_FLOOR],
             "+ doorless physical jambs": sk["components_lm"][WC.PHYSICAL_OPENING_JAMB],
             "- I1471 jamb caps (R8.15 counted them as wall face; door jamb = 0)": -i1471_caps,
             "- V3-O1 continuous face consumed": -ctx["v3_o1"]["effect_lm"]}
    recon["= R8.16"] = r6(math.fsum(v for v in recon.values()))
    recon["reconciles"] = abs(recon["= R8.16"] - sk["PAYABLE_LM"]) < 1e-6
    recon["is_target"] = False
    regs["SKIRTING_REGISTER"] = {
        "SCHEMA": "URBAN_R8_16_SKIRTING_REGISTER_V1", "row": "SKIRTING (hidden skirting, QP-06)", "unit": "lm",
        "state": "COMPUTED_SHADOW_WITH_WITHHELD_SPANS" if sk["withheld"] else "COMPUTED_SHADOW",
        "SKIRTING_LM": sk["PAYABLE_LM"], "reproduces_blind": ctx["reproduces_r8_16"]["skirting"],
        "per_room": {sid: {k: v.get(k) for k in ("zones", "state", "payable_lm", "components_lm", "excluded_lm",
                                                 "withheld", "jambs")} for sid, v in sk["per_site"].items()},
        "breakdown_lm": {"wall": sk["components_lm"][WC.REAL_WALL_FACE], "column": sk["components_lm"][WC.COLUMN_FACE],
                         "duct": sk["components_lm"][WC.AUTHORISED_OBSTACLE_FACE],
                         "doorless_jamb": sk["components_lm"][WC.PHYSICAL_OPENING_JAMB],
                         "under_window": sk["components_lm"][WC.WINDOW_ABOVE_FLOOR]},
        "excluded_lm": sk["excluded_lm"], "withheld": sk["withheld"], "withheld_lm": sk["withheld_lm"],
        "method": sk["method"], "policy": WC.POLICY_ID_V3,
        "counterfactuals": {"with_v3_o1_fixed_lm": r6(sk["PAYABLE_LM"] + ctx["v3_o1"]["effect_lm"]),
                            "with_the_glazed_opening_continuous_lm": r6(sk["PAYABLE_LM"] + sk["withheld_lm"]),
                            "both_lm": r6(sk["PAYABLE_LM"] + sk["withheld_lm"] + ctx["v3_o1"]["effect_lm"])},
        "reconciliation_vs_r8_15": recon,
        "release_blockers": blk,
        "never": ["84.795214 / 9.091605 / 1.75 / 0.55 / 0.30 / QP-10 76.389 as a target", "a room polygon perimeter"]}
    regs["HIDDEN_PROFILE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_16_HIDDEN_PROFILE_REGISTER_V1", "row": "HIDDEN_PROFILE_LM", "unit": "lm",
        "authority": ["US-08: the hidden system is two BOQ items measured along the SAME payable path, kept as two "
                      "rows whose amounts are never merged", "QP-06 QORTUBA skirting system = HIDDEN"],
        "state": regs["SKIRTING_REGISTER"]["state"], "HIDDEN_PROFILE_LM": sk["PAYABLE_LM"],
        "path": "IDENTICAL to SKIRTING (same per-room path, same exclusions, same withheld spans)",
        "per_room_lm": {sid: v["payable_lm"] for sid, v in sk["per_site"].items()},
        "release_blockers": blk, "inherits_from": "SKIRTING", "merged_with_skirting": False,
        "why_separate": "a separate BOQ item (material + labour of the aluminium profile), never summed into the "
                        "skirting row; equal by method, not by coincidence",
        "never": ["a different path", "a rate", "a price"]}
    # ------------------------------------------------------------------ rows
    q13, q14 = rows["Q-13"], rows["Q-14"]
    v15 = {rid: v["VALUE"] for rid, v in s15["six_rows"].items()}
    i14 = ctx["i1471"]["strip_site"]
    regs["Q13_STATUS"] = dict(
        six["Q-13"], SCHEMA="URBAN_R8_16_Q13_STATUS_V1",
        rebuild="dry tiled TS01 sites of the closure-V2 run + only the dry <-> dry continuous thresholds; the I1471 "
                "strip is now a dry <-> dry CONTINUOUS_SAME_FINISH threshold (HALL shrinks by it, Q-13 takes it back)",
        regression_vs_r8_15={"R8.15": v15["Q-13"], "R8.16": q13["value"], "delta_m2": round(q13["value"] - v15["Q-13"],
                                                                                            4),
                             "why": f"HALL site -{i14['area_m2']} m2, I1471 continuous threshold +{i14['area_m2']} m2",
                             "is_target": False}, historical_matching="NONE")
    regs["Q14_STATUS"] = dict(
        six["Q-14"], SCHEMA="URBAN_R8_16_Q14_STATUS_V1",
        rebuild="ceiling sites of the closure-V2 run (duct out by owner authority) minus the Hall / Lobby soffit; "
                "M.B.ROOM / DRESS passage FULL_HEIGHT (ceiling continues); every door strip NOT_IN_TRADE - I1471 "
                "included, now that it is its own site",
        regression_vs_r8_15={"R8.15": v15["Q-14"], "R8.16": q14["value"], "delta_m2": round(q14["value"] - v15["Q-14"],
                                                                                            4),
                             "R8.15_counterfactual": s15["six_rows"]["Q-14"]["COUNTERFACTUALS"].get(
                                 "counterfactual_door_reveal_excluded"),
                             "why": f"the I1471 door reveal ({i14['area_m2']} m2) left the HALL ceiling site",
                             "is_target": False},
        door_strip_is_ceiling=[t["threshold"] for t in ctx["thresholds_new"]
                               if t["physical_site"] in {u["site"] for u in q14["sites_used"]}],
        historical_matching="NONE")
    mq15 = jl(REG15 / "MARBLE_THRESHOLD_REGISTER.json")["quantities"]
    regs["MARBLE_THRESHOLD_REGISTER"] = dict(
        base["MARBLE_THRESHOLD_REGISTER"], SCHEMA="URBAN_R8_16_MARBLE_THRESHOLD_REGISTER_V1",
        regression_vs_r8_15={"R8.15": mq15, "R8.16": ctx["marble_quantities"],
                             "unchanged": mq15 == ctx["marble_quantities"],
                             "i1471": next({k: t[k] for k in ("threshold", "classification", "allocation_state")}
                                           for t in ctx["thresholds_new"] if t["door_occurrence"] == "I1471"),
                             "why": "I1471 is HALL <-> M.B.ROOM (dry <-> dry): its new strip is porcelain, never "
                                    "marble"})
    rv = base["OPENING_REVEAL_REGISTER"]
    regs["OPENING_REVEAL_REGISTER"] = dict(
        rv, SCHEMA="URBAN_R8_16_OPENING_REVEAL_REGISTER_V1", door_reveals=ctx["door_reveals"],
        door_reveal_note="door jamb / head reveal surfaces exist for plaster independently of skirting (door jamb "
                         "skirting = 0); paint NOT ASSUMED; no wall-face row consumes them yet (R8.17)",
        i1471="its two jambs and its head reveal now exist as a door strip (was inside the HALL ceiling)")
    regs["WALL_FACE_ENGINE_READINESS"] = {
        "SCHEMA": "URBAN_R8_16_WALL_FACE_ENGINE_READINESS_V1", "ready_to_publish": False,
        "assessment": "DESIGN READY, NOT IMPLEMENTED: no plaster / paint / wall-tile quantity this round",
        "has": ["per-room wall face path (V3 edges, classified)", "door / passage strip sites with jamb and head "
                "reveal surfaces", "owner heights: 3.20 m wet / service tile (Qortuba new revision only), QP-21 door "
                "2.20 m, QP-12 glazed opening 2.20 m, QP-22 window 1.50 m", "PAINTRY = QP-07 service room",
                "Hall passage soffit / M.B full-height facts"],
        "missing": ["face sets per room side with height (ceiling height per room)", "US-06 opening deductions per "
                    "opening with its own height authority", "reveal adds (source depth first, US-07 fallback)",
                    "a frozen, blind-tested WALL_FACE_SURFACE policy", "the HALL / PAINTRY glazed opening sill"],
        "preserved": {"wet_service_tile_m": 3.20, "scope": "Qortuba new revision wet / service rooms only",
                      "paintry": "QP-07", "hall_plaster": "Hall / Lobby passage WITH_HEAD soffit facts"},
        "next": "R8.17 (design -> synthetic -> freeze -> blind)"}
    regs["SOURCE_ANCHOR_STATUS"] = dict(base["SOURCE_ANCHOR_STATUS"], SCHEMA="URBAN_R8_16_SOURCE_ANCHOR_STATUS_V1")
    regs["CLOSURE_RELEASE_STATUS"] = dict(base["CLOSURE_RELEASE_STATUS"], SCHEMA="URBAN_R8_16_CLOSURE_RELEASE_STATUS_V1",
                                          door_closures={"V2_offset": cl["closure_b_rules"][T.B_OFFSET_JAMB],
                                                         "V1_end_point": cl["closure_b_rules"][T.B_END_POINT],
                                                         "release": "SHADOW only (TS01 door strips are not "
                                                                    "release-graded closures)"})
    d15 = jl(REG15 / "DIGEST_HIERARCHY.json")["rows"]

    def dg(d, layer):
        return d[layer] if layer == "TOPOLOGY_RUN_INPUT_DIGEST" else d[layer]["digest"]
    regs["DIGEST_HIERARCHY"] = {
        "SCHEMA": "URBAN_R8_16_DIGEST_HIERARCHY_V1", "layers": list(RM.DIGEST_LAYERS), "rows": dig,
        "vs_r8_15": {rid: {layer: "CHANGED" if dg(dig[rid], layer) != dg(d15[rid], layer) else "SAME"
                           for layer in RM.DIGEST_LAYERS} for rid in ROWS},
        "reason": "the run manifest now records DOOR_OPENING_CLOSURE_POLICY_V2 (a TS01 input: the I1471 strip is a "
                  "new site) - every layer above changes with it"}
    extra = {"SKIRTING": {"state": regs["SKIRTING_REGISTER"]["state"], "value_lm": sk["PAYABLE_LM"],
                          "release_blockers": blk},
             "HIDDEN_PROFILE": {"state": regs["HIDDEN_PROFILE_REGISTER"]["state"], "value_lm": sk["PAYABLE_LM"],
                                "release_blockers": blk},
             "MARBLE_THRESHOLD": {"state": "COMPUTED_SHADOW", **ctx["marble_quantities"],
                                  "release_blockers": regs["MARBLE_THRESHOLD_REGISTER"]["release_blockers"]}}
    regs["QORTUBA_R8_16_STATUS"] = {
        "SCHEMA": "URBAN_R8_16_QORTUBA_STATUS_V1", "six_rows": six, "extra_rows": extra,
        "threshold_audit": [{k: t[k] for k in ("threshold", "door_occurrence", "classification", "allocation_state",
                                               "width_mm", "thickness_mm", "strip_m2", "reconciles")}
                            for t in ctx["thresholds_new"]],
        "doors_without_threshold_site": ctx["doors_without_threshold"],
        "rows_old": {rid: {"state": v["state"], "value": v["value"]} for rid, v in ctx["rows_old"].items()},
        "old_revision_unchanged_vs_r8_15": {rid: (ctx["rows_old"][rid]["state"], ctx["rows_old"][rid]["value"]) ==
                                            (s15["rows_old"][rid]["state"], s15["rows_old"][rid]["value"])
                                            for rid in ROWS},
        "vs_r8_15": {rid: {"R8.15": v15[rid], "R8.16": six[rid]["VALUE"],
                           "delta": round(six[rid]["VALUE"] - v15[rid], 4)} for rid in ROWS},
        "determinism": ctx["det"], "reproduces_r8_16_blind": ctx["reproduces_r8_16"],
        "final": "SHADOW only: no row is FINAL"}
    regs["R8_16_DECISION_REGISTER"] = decision_register(regs, ctx, rec, six)
    return regs, ctx


def ctx_u(ctx):
    return ctx["inp_new"].unit_native_to_mm / 1000


def decision_register(regs, ctx, rec, six):
    sk, hp = regs["SKIRTING_REGISTER"], regs["HIDDEN_PROFILE_REGISTER"]
    wf, dj, dl = regs["WINDOW_FLOOR_CONTACT_REGISTER"], regs["DOOR_SKIRTING_POLICY"], regs["DOORLESS_JAMB_REGISTER"]
    st, au = regs["QORTUBA_R8_16_STATUS"], regs["I1471_SOURCE_AUDIT"]
    q13, q14, mr = regs["Q13_STATUS"], regs["Q14_STATUS"], regs["MARBLE_THRESHOLD_REGISTER"]
    cl = ctx["closure_v2"]
    hosted = [w for w in wf["windows"] if w["hosted_on_wall_face_line"]]
    mbd = [p for p in ctx["new"]["passages"] if ctx["heads"].get(p["passage_id"]) == Q.R15.OR.FULL_HEIGHT]
    remaining = {rid: v["RELEASE_BLOCKERS"] for rid, v in six.items()}
    remaining |= {k: v["release_blockers"] for k, v in st["extra_rows"].items()}
    answers = {
        "1_window_rule_encoded": f"YES: {WIN_FACT}@v1 (WINDOW_FLOOR_CONTACT, sill 1.00 m, normal windows, scoped) + "
                                 f"{SUP_FACT}@v1 (skirting continues) + URBAN-SKIRTING-OPENING-METHOD@v1 "
                                 "WINDOW_ABOVE_FLOOR; engine: wall_contact_path.floor_contact / classify_v3",
        "2_windows_above_floor": f"{len(hosted)} normal windows ABOVE_FLOOR (owner fact binding: "
                                 f"{wf['fact_binding']}); 1 glazed opening FLOOR_CONTACT_UNPROVEN",
        "3_continuity_under_all_proven_windows": "YES: every window with floor-contact authority carries "
                                                 "SKIRTING_CONTINUITY_UNDER_WINDOW (" +
                                                 ", ".join(f"{w['length_mm'] / 1000:.4f}" for w in hosted) + " m)",
        "4_window_span_on_path": f"YES: {wf['continuity_lm']} lm WINDOW_ABOVE_FLOOR on the payable path, trade-only "
                                 "(no topology change)",
        "5_qp09_scoped": regs["OWNER_METHOD_RULE_REGISTER"]["qp09"]["state"],
        "6_door_zero_jamb": f"YES: {len(dj['door_jambs'])} door jamb records, skirting 0.0 each "
                            f"({dj['rule']})",
        "7_stop_at_door": f"YES: {dj['excluded_across_doors_lm']} lm across doors excluded; swing / frame / "
                          "closure never measured",
        "8_both_doorless_jambs": [f"{j['site']} {j['opening']} {j['side']} {j['end_kind']} {j['counted_lm']} lm "
                                  f"({j['record']})" for j in dl["jambs"]],
        "9_zero_across_passage": "YES: across_opening_lm = 0.0 (the passage width is never on the path)",
        "10_closures_zero": f"YES: TOPOLOGY_CLOSURE {dl['topology_closure_lm']} lm",
        "11_hall_far_jamb_recovered": "YES from the wall band (not the closure): " +
                                      json.dumps(dl["hall_far_jamb"], ensure_ascii=False),
        "12_i1471_root_cause": au["cause"],
        "13_generic_rule": rec["8_i1471_evidence"],
        "14_version_bump": f"YES: {T.DOOR_CLOSURE_POLICY_ID} ({T.door_closure_policy_record()['digest'][:16]}) in "
                           f"the run manifest; {WC.POLICY_ID_V3} ({WC.policy_record_v3()['digest'][:16]}); "
                           f"{MF.POLICY_ID}; WALL_BAND_POLICY_V5 / TOPOLOGY_CLOSURE_POLICY_V1 / V2 unchanged",
        "15_frozen_before_qortuba": f"YES: freeze {ctx['r8_16_freeze']['frozen_commit'][:12]} before the blind run; "
                                    f"2 amendments (blind-script formatting, crashes before any output)",
        "16_i1471_complete_site": f"YES: {au['v2_result']['rule']} (depth / stagger "
                                  f"{au['v2_result']['evidence']}); strip {au['strip_site']}",
        "17_q14_removed_the_reveal": f"YES: {q14['regression_vs_r8_15']}",
        "18_rebuilt_q14": six["Q-14"]["VALUE"],
        "19_effect_on_floor_rows": {rid: st["vs_r8_15"][rid] for rid in ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13")},
        "20_skirting_lm": sk["SKIRTING_LM"],
        "21_breakdown": sk["breakdown_lm"],
        "22_excluded_spans": sk["excluded_lm"],
        "23_withheld_spans": sk["withheld"],
        "24_still_shadow": f"YES: {sk['state']}",
        "25_hidden_profile_published": f"YES (SHADOW): HIDDEN_PROFILE_LM = {hp['HIDDEN_PROFILE_LM']} lm, "
                                       f"{hp['state']}",
        "26_why_equal_but_separate": hp["why_separate"] + " (US-08)",
        "27_marble_regression": f"unchanged: {mr['regression_vs_r8_15']['unchanged']} "
                                f"({mr['regression_vs_r8_15']['R8.16']}); I1471 = "
                                f"{mr['regression_vs_r8_15']['i1471']['classification']}",
        "28_h2430_h2431": "NO regression: topology closures reproduce the blind record "
                          f"({ctx['reproduces_r8_16']['closures']}); " + "; ".join(
                              f"{c['closure_id']} {c['release']} {c['separated_m2']}" for c in cl["topology_closures"]),
        "29_mb_full_height": [f"{p['passage_id']} FULL_HEIGHT -> ceiling continues" for p in mbd],
        "30_hall_soffit": f"excluded: {six['Q-14']['SOFFIT_EXCLUSION_M2']} m2",
        "31_source_anchor": regs["SOURCE_ANCHOR_STATUS"]["state"],
        "32_blockers": remaining,
        "33_new_silent_error": [
            f"V3-O1 (found after the blind run, NOT fixed inside the frozen V3): measure_v3 subtracts the overlap of "
            f"EVERY jamb record from the wall path, including a CONTINUOUS_WALL_FACE side that is not a jamb - at "
            f"M.B.ROOM / DRESS {ctx['v3_o1']['effect_lm']} lm of H518 wall face counts nowhere (also listed as "
            "DOORLESS_JAMB_NOT_COUNTED). Release blocker + counterfactual "
            f"{sk['counterfactuals']['with_v3_o1_fixed_lm']} lm; V4 next round"],
        "34_wall_face_engine_ready": regs["WALL_FACE_ENGINE_READINESS"]["assessment"],
        "35_r8_17": rec["12_r8_17"] + " Plus V3-O1 (skirting path V4: subtract only physical jamb overlaps).",
        "36_disagreements": rec["11_disagreements_with_chatgpt"]}
    return {"SCHEMA": "URBAN_R8_16_DECISION_REGISTER_V1", "recommendation_before_coding": rec,
            "order": ["recommendation (55a484e)", "closure V2 + skirting V3 + facts + rule + synthetic tests",
                      f"freeze ({ctx['r8_16_freeze']['frozen_commit'][:7]})", "blind Qortuba run committed (91cdb45)",
                      "rows / registers afterwards"],
            "decisions": [
                {"id": "R816-D01", "decision": "normal windows: trade-only SKIRTING_CONTINUITY_UNDER_WINDOW on owner "
                                               "floor-contact authority; QP-09 superseded in scope only"},
                {"id": "R816-D02", "decision": "HALL / PAINTRY glazed opening: FLOOR_CONTACT_UNPROVEN, withheld; one "
                                               "optional owner question for release"},
                {"id": "R816-D03", "decision": "doors: stop at opening, zero across, zero jambs (explicit rule)"},
                {"id": "R816-D04", "decision": "doorless: zero across, physical side jambs from band ends; closures "
                                               "zero"},
                {"id": "R816-D05", "decision": "I1471: DOOR_OPENING_CLOSURE_POLICY_V2 offset-jamb rule (topology, "
                                               "frozen, blind)"},
                {"id": "R816-D06", "decision": "HIDDEN_PROFILE_LM published as its own SHADOW row on the same path"},
                {"id": "R816-D07", "decision": "V3-O1 disclosed with counterfactual; no post-result edit"}],
            "gates": GATES, "answers": answers}
