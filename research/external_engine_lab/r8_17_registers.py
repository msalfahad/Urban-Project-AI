"""R8.17 lab registers: every JSON register of the R8.17 package from the r8_17_qortuba build (no number typed in).

Owner actions, the sliding-door physical fact, method rules, V3-O1, skirting V4 policy / register, hidden profile,
opening reveals, Q-13 / Q-14 / marble regression, the wall-face engine design / readiness / surface register, the
second-project regression, source anchor, closure release, row status and the decision register (answers 1-42).
The blind records (SKIRTING_V4_BLIND_RESULT, WALL_FACE_BLIND_RESULT) and the two freeze records are committed before
this module ran and are never rewritten here.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import r8_16_registers as R16G
import r8_17_qortuba as Q
from engine.source import opening_facts as OPF, owner_facts as OF, owner_method_facts as MF, run_manifest as RM
from engine.source import wall_contact_path as WC, wall_faces as WF

ROOT = Path(__file__).resolve().parents[2]
GATES = {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO", "PRODUCTION_MIGRATION": "NO"}
REG16 = ROOT / "tests/r8_16/registers"
REG17 = ROOT / "tests/r8_17/registers"
ROWS = Q.R15.ROWS
SLIDE = Q.B17.SLIDE
WIN = "QORTUBA-NEW-NORMAL-WINDOWS-ABOVE-FLOOR-OWNER-001"


def jl(p):
    return json.loads(Path(p).read_text())


def r6(v):
    return None if v is None else round(v, 6)


def wall_tile(wf, wm):
    """The WALL_TILE trade row over the wet / service sites (frozen engine output, rebuild wiring)."""
    sites = {sid: v for sid, v in wf["per_site"].items() if "WALL_TILE" in v["faces"]}
    per = {}
    for sid, v in sites.items():
        f = v["faces"]["WALL_TILE"]
        a = f.get("areas_m2") or {}
        per[sid] = {"zones": v["zones"], "class": v["class"], "state": f["state"], "blockers": f["blockers"],
                    "height_m": f["height_m"], "height_authority": f["height_authority"],
                    "wall_face_net_m2": a.get("WALL_FACE_NET"), "column_face_m2": a.get("COLUMN_FACE"),
                    "openings": [{k: o.get(k) for k in ("opening", "kind", "width_m", "height_m", "height_authority",
                                                        "sill_m", "deduction_m2", "lintel_m2", "state")}
                                 for o in f["openings"]],
                    "conservation": f["conservation"], "lengths_m": f["lengths_m"]}
    ok = all(v["state"] == WF.COMPUTED for v in per.values())
    cf = round(math.fsum((v["wall_face_net_m2"] or 0.0) + (v["column_face_m2"] or 0.0) for v in per.values()), 6) \
        if all(v["wall_face_net_m2"] is not None for v in per.values()) else None
    computed = {sid: round(v["wall_face_net_m2"] + v["column_face_m2"], 6) for sid, v in per.items()
                if v["state"] == WF.COMPUTED}
    return {"state": "COMPUTED_SHADOW" if ok else "BLOCKED", "value_m2": cf if ok else None, "per_room": per,
            "computed_rooms_m2": computed, "counterfactual_all_rooms_primary_form_m2": cf,
            "column_faces": wm["column_faces"]["WALL_TILE"], "column_authority": wm["column_authority"],
            "reveals": wm["reveal_inclusion"]["WALL_TILE"]}


def registers(ctx):
    base16, _ = R16G.registers(ctx)
    rows, dig = ctx["rows_new"], ctx["dig"]
    rec = jl(ROOT / "research/external_engine_lab/r8_17_recommendation.json")
    six = {rid: R16G.R15G._row_view(rid, rows[rid], dig[rid]) for rid in ROWS}
    s16 = jl(REG16 / "QORTUBA_R8_16_STATUS.json")
    sk16 = jl(REG16 / "SKIRTING_REGISTER.json")
    fz4, fzw = ctx["r8_17_v4_freeze"], ctx["r8_17_wall_freeze"]
    wm = fzw["qortuba_wall_face_method"]
    sk, wf = ctx["skirting_v4"], ctx["wall_faces"]
    phys = {f["fact_id"]: f for f in jl(ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json")["facts"]}
    meth = [f for f in jl(ROOT / "data/registry/OWNER_METHOD_FACTS.json")["facts"] if f["fact_id"] == WIN]
    rules = {r["rule_id"]: r for r in jl(ROOT / "data/registry/URBAN_OWNER_METHOD_RULES.json")["rules"]}
    sf = OF.from_record(phys[SLIDE])
    sbind = OF.bind(sf, ctx["inp_new"])
    regs = {}
    # ------------------------------------------------------------------ owner side
    regs["OWNER_ACTION_REGISTER"] = {
        "SCHEMA": "URBAN_OWNER_ACTION_REGISTER_V14",
        "headline": "NO OWNER ACTION REQUIRED FOR THE SHADOW ROWS. TWO NEW QUESTIONS FOR THE WALL-FINISH TRADES.",
        "required_now": [],
        "needed_for_wall_finish_rows": [
            {"id": "QORTUBA_NEW_DRY_ROOM_WALL_FINISH_HEIGHT", "blocks": "PLASTER and PAINT (every dry room)",
             "question": "For the current selected Qortuba plan, up to what height are the dry rooms (bedrooms, "
                         "M.B.ROOM / DRESS, HALL / LOBBY) plastered and painted - 3.00 m as in the old drawing's "
                         "rule (QP-03 / QP-04), or 3.20 m like the new wet-room tile, or another height?",
             "why_new": "QP-03 / QP-04 were set on the OLD revision; for the new revision the owner raised the "
                        "wet / service tile height to 3.20 m and stated no plaster / paint height. Source exhausted "
                        "(no section, elevation or height text in the DXF)",
             "current": "BLOCKED (no area published); counterfactual at QP-03 3.00 m recorded, never published"},
            {"id": "QORTUBA_NEW_WET_ROOM_REVEAL_FINISH", "blocks": "the wet / service reveal surfaces only",
             "question": "Inside the bathrooms and the PAINTRY, are the door / sliding-door / window reveals (the "
                         "sides and top of each opening) tiled with the wall tile, or plastered?",
             "why_new": "no rule states it: US-07 covers plaster / paint reveals, US-01 the wall faces",
             "current": "reveal surfaces recorded with areas, trade NOT_ESTABLISHED, not in WALL_TILE"}],
        "answered_this_round": [{"fact": sf.ref, "kind": OPF.KIND}],
        "do_not_ask": ["HALL / PAINTRY glass", "normal windows", "door jamb skirting", "doorless-opening jamb "
                       "skirting", "duct", "marble", "Hall / Lobby passage", "M.B.ROOM / DRESS passage",
                       "selected plan", "any expected quantity"]}
    regs["OWNER_PHYSICAL_FACT_REGISTER"] = {
        "SCHEMA": "URBAN_R8_17_OWNER_PHYSICAL_FACT_REGISTER_V1", "file": "data/registry/OWNER_PHYSICAL_FACTS.json",
        "new_fact": phys[SLIDE], "binding": sbind, "policy": OPF.policy_record(),
        "physical_fact_policy": OF.POLICY_ID + " (unchanged: the opening class is its own versioned domain)",
        "topology_effect": "NONE (the glazed closures and strip sites already existed; no TS01 input changed)",
        "never": phys[SLIDE]["never"]}
    regs["OWNER_METHOD_RULE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_17_OWNER_METHOD_RULE_REGISTER_V1",
        "urban_rules": [rules["URBAN-SKIRTING-OPENING-METHOD"]], "window_fact_versions": meth,
        "window_fact_v2": "the SAME owner statement (sill ~1.00 m, normal windows), trade scope widened to wall-face "
                          "surfaces for POSITION only (a window lies inside a stated wall-finish height); v1 stays "
                          "for the frozen R8.16 skirting record; CORROBORATING, never a conflict",
        "fact_policy": MF.POLICY_ID,
        "rule_store_used_for_wall_faces": ["US-01", "US-03", "US-06", "US-07", "US-10", "US-11", "US-16", "US-17",
                                           "QP-07", "QP-12", "QP-21", "QP-22", "QP-23", "R-13"],
        "rule_store_not_transferred": ["QP-01 tile 3.00 m (superseded in scope by the 3.20 m fact)",
                                       "QP-02 / QP-03 / QP-04 3.00 m (old revision; counterfactual only)",
                                       "QP-09 window deduction (superseded in scope, R8.16)"]}
    # ------------------------------------------------------------------ sliding door / V3-O1
    hall = next(sid for sid, v in sk["per_site"].items() if "HALL" in v["zones"])
    pai = next(sid for sid, v in wf["per_site"].items() if "PAINTRY" in v["zones"])
    pf = wf["per_site"][pai]["faces"]["WALL_TILE"]
    regs["HALL_PAINTRY_SLIDING_DOOR_REGISTER"] = {
        "SCHEMA": "URBAN_R8_17_HALL_PAINTRY_SLIDING_DOOR_REGISTER_V1", "fact": sf.ref, "binding": sbind["binding"],
        "source": {"glazing_lines": ["H533 (x = 1095980.8)", "H542 (x = 1096080.8, on the HALL face)"],
                   "wall": "150 mm (faces x = 1095930.8 / 1096080.8)", "length_mm": 2750.0,
                   "closures": phys[SLIDE]["statement"]["occurrence"]["closures"],
                   "strip_sites": "two unlabelled TS01 sites between the face closures (the glazing tracks)",
                   "old_revision": "the same handles H533 / H542 and the same 2.75 m width"},
        "classification": {"physical_class": "SLIDING_GLAZED_DOOR", "floor_contact": "OPENING_TO_FLOOR",
                           "path_class": WC.SLIDING_GLAZED_DOOR_TO_FLOOR,
                           "window_fact": f"{WIN} does NOT apply (resolution order: physical class first)"},
        "skirting": {"HALL_excluded_lm": sk["per_site"][hall]["excluded_lm"].get(WC.SLIDING_GLAZED_DOOR_TO_FLOOR),
                     "payable_lm": 0.0, "PAINTRY": "NO_SKIRTING (full wall tile)",
                     "R8.16": "WITHHELD 2.75 lm (FLOOR_CONTACT_UNPROVEN) -> now EXCLUDED_AS_FLOOR_REACHING_DOOR"},
        "jambs": sk["sliding_door_fact"]["glazed_door_jambs"],
        "jamb_note": "both jambs (150 mm wall ends) bound the strip sites, not HALL: zero skirting by rule, nothing "
                     "subtracted twice",
        "hidden_profile": "excluded across the 2.75 m (same path, US-08)",
        "wall_face": {"PAINTRY": next((o for o in pf["openings"] if o["kind"] == WF.SLIDING_DOOR), None),
                      "height_authority": wm["opening_heights"]["SLIDING_GLAZED_DOOR"]["authority"],
                      "low_wall": "NONE (the opening reaches the floor: sill 0)"},
        "ceiling_q14": "unchanged: no trade or topology change touches the ceiling",
        "marble": "NONE (dry <-> service glazed door; no marble rule or explicit evidence applies)"}
    mb = next(sid for sid, v in sk["per_site"].items() if "M.B.ROOM" in v["zones"])
    regs["SKIRTING_V3_O1_REGISTER"] = {
        "SCHEMA": "URBAN_R8_17_SKIRTING_V3_O1_REGISTER_V1", "id": "V3-O1", "found": "R8.16 (after its blind run)",
        "root_cause": rec["6_v3_o1_root_cause"], "design_error": rec["inspected"][1],
        "fix": rec["7_generic_v4_rule"], "policy": WC.POLICY_ID_V4,
        "evidence": {"site": mb, "zones": sk["per_site"][mb]["zones"],
                     "V3_payable_lm": jl(REG16 / "SKIRTING_BLIND_RESULT.json")["per_site"][mb]["payable_lm"],
                     "V4_payable_lm": sk["per_site"][mb]["payable_lm"],
                     "V4_annotations": sk["per_site"][mb]["opening_side_annotations"],
                     "V4_conservation": sk["per_site"][mb]["conservation"]},
        "special_cased": "NOTHING: no handle, no project, no site id in the rule (engine/source has no project name)",
        "tests": [t for t in fz4["synthetic_tests"] if t.split("_")[1] in ("02", "03", "04", "05", "15")],
        "topology_effect": "NONE"}
    regs["SKIRTING_V4_POLICY"] = {"SCHEMA": "URBAN_R8_17_SKIRTING_V4_POLICY_V1", "policy": WC.policy_record_v4(),
                                  "method": fz4["qortuba_method"], "opening_class_policy": OPF.policy_record()}
    blk = ctx["skirting_v4_blockers"]
    comp = sk["components_lm"]
    recon = {"R8.16_SKIRTING_LM": sk16["SKIRTING_LM"], "+ V3-O1 continuous face restored":
             round(sk["components_lm"][WC.REAL_WALL_FACE] - sk16["breakdown_lm"]["wall"], 6),
             "R8.16 withheld 2.75 lm -> excluded (not payable)": 0.0}
    recon["= R8.17"] = r6(math.fsum(v for v in recon.values()))
    recon["reconciles"] = abs(recon["= R8.17"] - sk["PAYABLE_LM"]) < 1e-6
    recon["is_target"] = False
    regs["SKIRTING_REGISTER"] = {
        "SCHEMA": "URBAN_R8_17_SKIRTING_REGISTER_V1", "row": "SKIRTING (hidden skirting, QP-06)", "unit": "lm",
        "state": "COMPUTED_SHADOW" if not sk["withheld"] else "COMPUTED_SHADOW_WITH_WITHHELD_SPANS",
        "SKIRTING_LM": sk["PAYABLE_LM"], "reproduces_blind": ctx["reproduces_v4_blind"],
        "per_room": {sid: {k: v.get(k) for k in ("zones", "state", "payable_lm", "components_lm", "excluded_lm",
                                                 "withheld", "jambs", "opening_side_annotations", "conservation")}
                     for sid, v in sk["per_site"].items()},
        "breakdown_lm": {"real_walls": comp[WC.REAL_WALL_FACE], "columns": comp[WC.COLUMN_FACE],
                         "duct": comp[WC.AUTHORISED_OBSTACLE_FACE], "normal_window_continuity":
                         comp[WC.WINDOW_ABOVE_FLOOR], "doorless_jambs": comp[WC.PHYSICAL_OPENING_JAMB], "other": 0.0},
        "excluded_lm": sk["excluded_lm"], "withheld": sk["withheld"], "withheld_lm": sk["withheld_lm"],
        "conservation_all_sites": sk["conservation_all_sites"], "method": sk["method"], "policy": sk["policy"],
        "reconciliation_vs_r8_16": recon, "known_defects_open": [], "release_blockers": blk,
        "never": fz4["qortuba_method"]["never"]}
    regs["HIDDEN_PROFILE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_17_HIDDEN_PROFILE_REGISTER_V1", "row": "HIDDEN_PROFILE_LM", "unit": "lm",
        "authority": ["US-08: two BOQ items on the SAME payable path, never merged", "QP-06 QORTUBA skirting = HIDDEN"],
        "state": regs["SKIRTING_REGISTER"]["state"], "HIDDEN_PROFILE_LM": sk["PAYABLE_LM"],
        "path": "IDENTICAL to SKIRTING (certified V4 path: no withheld span, no open path defect)",
        "per_room_lm": {sid: v["payable_lm"] for sid, v in sk["per_site"].items()}, "release_blockers": blk,
        "merged_with_skirting": False, "why_separate": "a separate BOQ item (the aluminium profile); equal by method "
                                                       "(same path), priced and listed separately (US-08)"}
    # ------------------------------------------------------------------ rows
    v16 = {rid: v["VALUE"] for rid, v in s16["six_rows"].items()}
    q13, q14 = rows["Q-13"], rows["Q-14"]
    regs["Q13_STATUS"] = dict(six["Q-13"], SCHEMA="URBAN_R8_17_Q13_STATUS_V1",
                              regression_vs_r8_16={"R8.16": v16["Q-13"], "R8.17": q13["value"],
                                                   "delta_m2": round(q13["value"] - v16["Q-13"], 4),
                                                   "is_target": False}, historical_matching="NONE")
    regs["Q14_STATUS"] = dict(six["Q-14"], SCHEMA="URBAN_R8_17_Q14_STATUS_V1",
                              regression_vs_r8_16={"R8.16": v16["Q-14"], "R8.17": q14["value"],
                                                   "delta_m2": round(q14["value"] - v16["Q-14"], 4),
                                                   "sliding_door_effect": "NONE (no trade or topology change "
                                                                          "touches the ceiling)",
                                                   "is_target": False},
                              preserved=["duct exclusion", "Hall / Lobby soffit exclusion",
                                         "M.B.ROOM / DRESS full-height ceiling", "I1471 door strip NOT_IN_TRADE"],
                              historical_matching="NONE")
    mq16 = jl(REG16 / "MARBLE_THRESHOLD_REGISTER.json")["quantities"]
    regs["MARBLE_THRESHOLD_REGISTER"] = dict(
        base16["MARBLE_THRESHOLD_REGISTER"], SCHEMA="URBAN_R8_17_MARBLE_THRESHOLD_REGISTER_V1",
        regression_vs_r8_16={"R8.16": mq16, "R8.17": ctx["marble_quantities"],
                             "unchanged": mq16 == ctx["marble_quantities"],
                             "sliding_door": "no marble (a door is not a marble threshold by itself)"})
    # ------------------------------------------------------------------ wall faces
    rv = wf["reveals"]
    regs["OPENING_REVEAL_REGISTER"] = {
        "SCHEMA": "URBAN_R8_17_OPENING_REVEAL_REGISTER_V1", "policy": WF.POLICY_ID,
        "reveals": rv, "count": len(rv),
        "by_trade": {t: r6(math.fsum(x.get("area_m2") or 0.0 for x in rv if x["trade"].startswith(t[:8])))
                     for t in ("PLASTER", "NOT_ESTABLISHED")},
        "blocked": [f"{x['opening']} {x['surface']}" for x in rv if x["state"] == WF.BLOCKED],
        "skirting": "independent: door / sliding-door jambs carry ZERO skirting while their reveal surfaces exist",
        "depth": wm["window_reveal_depth"] | {"doors / passages / sliding door": "SOURCE (strip / band thickness)"},
        "never": ["the sill as a reveal (US-07)", "a non-physical passage side as a jamb (V3-O1)",
                  "a reveal counted per room"], "double_count_guard": wf["double_count_guard"]}
    wt = wall_tile(wf, wm)
    regs["WALL_FACE_ENGINE_DESIGN"] = {
        "SCHEMA": "URBAN_R8_17_WALL_FACE_ENGINE_DESIGN_V1", "policy": WF.policy_record(),
        "method": wm, "freeze": {k: fzw[k] for k in ("frozen_commit", "wall_face_policy", "synthetic_tests",
                                                     "synthetic_test_count", "order", "rule", "amendments")},
        "layers": ["PHYSICAL (wall_faces.site_faces / opening_reveals: geometry, heights with authority, "
                   "reconciliation)", "TRADE (trade_assignment from rule DATA: which trade on which class, at which "
                   "authorised height)"]}
    dry = {sid: v for sid, v in wf["per_site"].items() if v["class"] == "DRY_INTERNAL_ROOM"}
    regs["WALL_FACE_ENGINE_READINESS"] = {
        "SCHEMA": "URBAN_R8_17_WALL_FACE_ENGINE_READINESS_V1", "implemented": True, "frozen": fzw["frozen_commit"],
        "blind_run": True,
        "trades": {"WALL_TILE": {"state": wt["state"], "blockers": sorted({b for v in wt["per_room"].values()
                                                                            for b in v["blockers"]}) +
                                 ["WF-O1: the engine's second-form area check omits the wall plane across a window - "
                                  "the PAINTRY (the only wet / service room with a window) fails closed",
                                  "WET_REVEAL_TREATMENT_NOT_ESTABLISHED (owner question)"]},
                   "PLASTER": {"state": "BLOCKED", "blockers": ["DRY_WALL_HEIGHT_NOT_ESTABLISHED (owner question)",
                                                                "WF-O1 (every dry room has a window)"]},
                   "PAINT": {"state": "BLOCKED", "blockers": ["DRY_WALL_HEIGHT_NOT_ESTABLISHED (owner question)",
                                                              "WF-O1", "column / duct paint authority not stated"]}},
        "ready_for_publication": False,
        "next": "R8.18: WALL_FACE_SURFACE_POLICY_V2 (WF-O1 fixed, the blind-script wiring of R8.17 folded into the "
                "frozen lab path) -> synthetic -> freeze -> blind; then the owner's height and reveal answers"}
    regs["WALL_SURFACE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_17_WALL_SURFACE_REGISTER_V1",
        "per_site": {sid: {"zones": v["zones"], "class": v["class"], "trades": v["trades"],
                           "passages_in_site": v["passages_in_site"],
                           "faces": {t: {k: f.get(k) for k in ("state", "height_m", "height_authority", "lengths_m",
                                                               "areas_m2", "openings", "head_faces", "conservation",
                                                               "blockers")} for t, f in v["faces"].items()},
                           "counterfactual": v.get("counterfactual")} for sid, v in wf["per_site"].items()},
        "WALL_TILE": wt, "WF_O1": ctx["wf_o1"], "blind_vs_rebuild": ctx["wall_face_blind_vs_rebuild"],
        "dry_counterfactual_note": "the dry-room areas at QP-03 / QP-04 3.00 m are COUNTERFACTUALS (old-revision "
                                   "rule; their own engine check also fails by WF-O1) - never published",
        "dry_lengths_m": {sid: v["faces"]["PLASTER"]["lengths_m"] for sid, v in dry.items()},
        "double_count_guard": wf["double_count_guard"],
        "topology_closures": "ZERO material, ZERO area (class ZERO_TOPOLOGY_CLOSURE)"}
    regs["SECOND_PROJECT_REGRESSION"] = {
        "SCHEMA": "URBAN_R8_17_SECOND_PROJECT_REGRESSION_V1", "state": "NOT_RUN",
        "candidates": {"P7757": "UNIT_UNRESOLVED (R8.9 / R8.10: no eps_r, so no certified topology and no sites; "
                                "adopting the candidate mm unit would itself be a calibration)",
                       "Al Rashed": "physical values not computable (R8.5: IMAGE / OLE content, unmapped regions)"},
        "substitute": "the generic synthetic families (R8.13 V3-D2, R8.11 H1316, R8.16 offset door / passages, R8.17 "
                      "glazed door) run through V4 and the wall-face engine in the frozen tests",
        "next": "a second project with a resolved unit and certified topology (R8.18)"}
    regs["SOURCE_ANCHOR_STATUS"] = dict(base16["SOURCE_ANCHOR_STATUS"], SCHEMA="URBAN_R8_17_SOURCE_ANCHOR_STATUS_V1")
    regs["CLOSURE_RELEASE_STATUS"] = dict(base16["CLOSURE_RELEASE_STATUS"],
                                          SCHEMA="URBAN_R8_17_CLOSURE_RELEASE_STATUS_V1",
                                          tracked=["I1471 (DOOR_OPENING_CLOSURE_POLICY_V2 offset jambs)", "H2430",
                                                   "H2431"], production="NO")
    d16 = jl(REG16 / "DIGEST_HIERARCHY.json")["rows"]

    def dg(d, layer):
        return d[layer] if layer == "TOPOLOGY_RUN_INPUT_DIGEST" else d[layer]["digest"]
    regs["DIGEST_HIERARCHY"] = {
        "SCHEMA": "URBAN_R8_17_DIGEST_HIERARCHY_V1", "layers": list(RM.DIGEST_LAYERS), "rows": dig,
        "vs_r8_16": {rid: {layer: "CHANGED" if dg(dig[rid], layer) != dg(d16[rid], layer) else "SAME"
                           for layer in RM.DIGEST_LAYERS} for rid in ROWS},
        "reason": "no TS01 input changed in R8.17 (V4 and the wall-face engine are trade layers)"}
    extra = {"SKIRTING": {"state": regs["SKIRTING_REGISTER"]["state"], "value_lm": sk["PAYABLE_LM"],
                          "release_blockers": blk},
             "HIDDEN_PROFILE": {"state": regs["HIDDEN_PROFILE_REGISTER"]["state"], "value_lm": sk["PAYABLE_LM"],
                                "release_blockers": blk},
             "MARBLE_THRESHOLD": {"state": "COMPUTED_SHADOW", **ctx["marble_quantities"],
                                  "release_blockers": regs["MARBLE_THRESHOLD_REGISTER"]["release_blockers"]},
             "WALL_TILE": {"state": wt["state"], "value_m2": wt["value_m2"],
                           "blockers": regs["WALL_FACE_ENGINE_READINESS"]["trades"]["WALL_TILE"]["blockers"]},
             "PLASTER": {"state": "BLOCKED", "value_m2": None,
                         "blockers": regs["WALL_FACE_ENGINE_READINESS"]["trades"]["PLASTER"]["blockers"]},
             "PAINT": {"state": "BLOCKED", "value_m2": None,
                       "blockers": regs["WALL_FACE_ENGINE_READINESS"]["trades"]["PAINT"]["blockers"]}}
    regs["QORTUBA_R8_17_STATUS"] = {
        "SCHEMA": "URBAN_R8_17_QORTUBA_STATUS_V1", "six_rows": six, "extra_rows": extra,
        "rows_old": {rid: {"state": v["state"], "value": v["value"]} for rid, v in ctx["rows_old"].items()},
        "old_revision_unchanged_vs_r8_16": {rid: (ctx["rows_old"][rid]["state"], ctx["rows_old"][rid]["value"]) ==
                                            (s16["rows_old"][rid]["state"], s16["rows_old"][rid]["value"])
                                            for rid in ROWS},
        "vs_r8_16": {rid: {"R8.16": v16[rid], "R8.17": six[rid]["VALUE"], "delta": round(six[rid]["VALUE"] -
                                                                                         v16[rid], 4)} for rid in ROWS},
        "doors_without_threshold_site": ctx["doors_without_threshold"], "determinism": ctx["det"],
        "reproduces": {"r8_16_blind": ctx["reproduces_r8_16"], "v4_blind": ctx["reproduces_v4_blind"]},
        "final": "SHADOW only: no row is FINAL"}
    regs["R8_17_DECISION_REGISTER"] = decision_register(regs, ctx, rec, six)
    return regs, ctx


def decision_register(regs, ctx, rec, six):
    sk, hp, sd = regs["SKIRTING_REGISTER"], regs["HIDDEN_PROFILE_REGISTER"], regs["HALL_PAINTRY_SLIDING_DOOR_REGISTER"]
    st, ws, rd = regs["QORTUBA_R8_17_STATUS"], regs["WALL_SURFACE_REGISTER"], regs["WALL_FACE_ENGINE_READINESS"]
    b = ctx["skirting_v4_blind"]
    per = sk["per_room"]
    hall = next(v for v in per.values() if "HALL" in v["zones"])
    mbd = next(v for v in per.values() if "M.B.ROOM" in v["zones"])
    i1471 = [j for j in b["jamb_records"] if j["opening"] == "I1471"]
    door_jambs = [j for j in b["jamb_records"] if j["kind"] in ("DOOR", "GLAZED_DOOR")]
    on_path = [j for v in per.values() for j in v.get("jambs") or [] if j["kind"] in ("DOOR", "GLAZED_DOOR")]
    remaining = {rid: v["RELEASE_BLOCKERS"] for rid, v in six.items()}
    remaining |= {k: v.get("release_blockers", v.get("blockers")) for k, v in st["extra_rows"].items()}
    answers = {
        "1_hall_paintry_authoritative_sliding_door": f"YES: {sd['fact']} binds H533 / H542 ({sd['binding']})",
        "2_reaches_the_floor": "YES: floor_contact OPENING_TO_FLOOR from the owner fact; wall below NONE",
        "3_removed_from_withheld": f"YES: withheld {sk['withheld_lm']} lm; the 2.75 m is EXCLUDED "
                                   f"({sd['skirting']['HALL_excluded_lm']} lm SLIDING_GLAZED_DOOR_TO_FLOOR)",
        "4_any_of_it_payable": "NO: 0.0 lm",
        "5_its_jambs_carry_skirting": f"NO: {len(sd['jambs'])} glazed-door jamb records, 0.0 lm each (they bound "
                                      "the strip sites, nothing subtracted twice)",
        "6_window_rule_applies": "NO: physical class resolved first; the window fact excludes sliding doors itself",
        "7_v3_o1_root_cause": regs["SKIRTING_V3_O1_REGISTER"]["root_cause"],
        "8_generic_v4_rule": regs["SKIRTING_V3_O1_REGISTER"]["fix"],
        "9_h518_payable": f"YES: M.B.ROOM / DRESS {mbd['payable_lm']} lm (V3 "
                          f"{regs['SKIRTING_V3_O1_REGISTER']['evidence']['V3_payable_lm']}); the H518 side is an "
                          "OPENING_SIDE annotation with consumed 0.0",
        "10_v4_frozen_before_qortuba": f"YES: freeze {ctx['r8_17_v4_freeze']['frozen_commit'][:7]} (no amendment), "
                                       "blind run committed before any comparison",
        "11_blind_v4_result": f"{b['PAYABLE_LM']} lm, {b['state']}, conservation {b['conservation_all_sites']}",
        "12_rebuilt_result": f"{sk['SKIRTING_LM']} lm; reproduces the blind record {sk['reproduces_blind']}",
        "13_breakdown": sk["breakdown_lm"],
        "14_withheld": sk["withheld"] or "NONE",
        "15_known_skirting_defects_open": sk["known_defects_open"] or "NONE",
        "16_hidden_profile_lm": hp["HIDDEN_PROFILE_LM"],
        "17_why_separate": hp["why_separate"],
        "18_doors_zero_jamb": f"YES: {len(door_jambs)} door / glazed-door jamb records, skirting 0.0 each; "
                              f"{len(on_path)} of them lie on a room path (they bound the door strip sites), so "
                              "nothing is subtracted and nothing is added",
        "19_doorless_jambs_kept": [f"{j['opening']} {j['side']} {j['end_kind']} {j['counted_lm']}"
                                   for v in per.values() for j in v.get("jambs") or [] if j["kind"] == "DOORLESS"],
        "20_hall_lobby_regress": f"NO: {hall['payable_lm']} lm, both jambs counted, closure 0",
        "21_mb_dress_regress": f"NO (fixed): {mbd['payable_lm']} lm",
        "22_i1471_regress": f"NO: its door strip site is kept (closure V2 offset rule), {len(i1471)} jamb records at "
                            "zero skirting, DOOR_PRESENT on both sides",
        "23_sliding_door_affects_q14": "NO",
        "24_q14": six["Q-14"]["VALUE"],
        "25_floor_rows_changed": {rid: st["vs_r8_16"][rid] for rid in ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13")},
        "26_marble_changed": f"NO: {regs['MARBLE_THRESHOLD_REGISTER']['regression_vs_r8_16']['R8.17']}",
        "27_wall_face_engine_implemented": "YES: WALL_FACE_SURFACE_POLICY_V1 (engine/source/wall_faces.py), 14 "
                                           f"synthetic tests, frozen {ctx['r8_17_wall_freeze']['frozen_commit'][:7]}, "
                                           "blind Qortuba run committed",
        "28_surface_classes": WF.policy_record()["physical_classes"] + ["OPENING (DOOR / SLIDING_GLAZED_DOOR / "
                                                                       "FLOOR_REACHING_GLAZING / WINDOW)"],
        "29_plaster_published": "NO: " + "; ".join(rd["trades"]["PLASTER"]["blockers"]),
        "30_paint_published": "NO: " + "; ".join(rd["trades"]["PAINT"]["blockers"]),
        "31_wall_tile_published": f"NO: {ws['WALL_TILE']['state']} - the three BATH rooms compute "
                                  f"({ws['WALL_TILE']['computed_rooms_m2']} m2 incl. column faces), the PAINTRY fails "
                                  "the engine's own check (WF-O1); wet reveals NOT_ESTABLISHED",
        "32_exact_blockers": rd["trades"],
        "33_deductions": "US-06 full opening area inside the trade height: door width x 2.20 (QP-21), sliding door "
                         "2.75 x 2.20 (QP-12, same occurrence), window width x 1.50 (QP-22) with its position proven "
                         "by the sill fact v2; the wall above a door is a lintel face; never width alone",
        "34_reveals": "their own surfaces per opening (left / right jamb + top, never the sill), source depth first "
                      "(door / glazed strip / band thickness), US-07 0.25 m only for windows (no source depth); "
                      "dry reveals -> PLASTER, wet / service / outside reveals NOT_ESTABLISHED; the M.B.ROOM / DRESS "
                      "far side (H518) is wall face, never a jamb",
        "35_closures_zero": "YES: TOPOLOGY_CLOSURE 0.0 lm in skirting; ZERO_TOPOLOGY_CLOSURE area 0.0 in wall faces",
        "36_waterproofing": "DEFERRED: " + rec["11_waterproofing"],
        "37_second_project": regs["SECOND_PROJECT_REGRESSION"]["state"] + " - " +
                             "; ".join(f"{k}: {v}" for k, v in regs["SECOND_PROJECT_REGRESSION"]["candidates"].items()),
        "38_source_anchor": regs["SOURCE_ANCHOR_STATUS"]["state"],
        "39_release_blockers": remaining,
        "40_new_silent_error": [
            "WF-O1 (frozen wall-face engine, found by its own fail-closed check in the blind run): the second form of "
            "the two-way area check leaves out the wall plane across WINDOW spans, so every room with a window "
            "reports AREA_RECONCILIATION_FAILED (the primary US-06 form is correct: verified independently, "
            f"{[x['agree_when_the_window_plane_is_included'] for x in ctx['wf_o1']].count(True)} / "
            f"{len(ctx['wf_o1'])} sites agree once the window plane is included). Not fixed inside the frozen V1",
            "WF-L1 / WF-L2 (blind-script wiring, no engine change): passage-head constants mismatched and a door's own "
            "strip site counted as a room - both corrected in the rebuild and disclosed with the blind-vs-rebuild "
            "difference list",
            "the synthetic window test asserted the area but not the state - the reason WF-O1 passed the freeze"],
        "41_r8_18": rec["13_r8_18"] + " First item: WALL_FACE_SURFACE_POLICY_V2 (WF-O1) with a state assertion in "
                                       "every area test.",
        "42_disagreements": rec["12_disagreements_with_chatgpt"]}
    return {"SCHEMA": "URBAN_R8_17_DECISION_REGISTER_V1", "recommendation_before_coding": rec,
            "order": ["recommendation (88d5ac1)", "V4 + facts + tests (e636c77)", "V4 freeze (d3f9f85)",
                      "V4 blind (be98f71)", "wall-face engine + tests (e0d2781)", "wall-face freeze (8bbc21a)",
                      "wall-face blind (after one pre-output crash amendment)", "rebuild / registers"],
            "decisions": [
                {"id": "R817-D01", "decision": "HALL / PAINTRY = SLIDING_GLAZED_DOOR to the floor (owner, source-bound):"
                                               " zero across, zero jambs, never a window"},
                {"id": "R817-D02", "decision": "WALL_CONTACT_PATH_POLICY_V4: only physical jambs consume path; edge "
                                               "conservation; physical class before sill"},
                {"id": "R817-D03", "decision": "HIDDEN_PROFILE_LM on the certified V4 path, separate row"},
                {"id": "R817-D04", "decision": "WALL_FACE_SURFACE_POLICY_V1 frozen + blind; no trade row published "
                                               "(dry height, WF-O1, wet reveals)"},
                {"id": "R817-D05", "decision": "waterproofing deferred to its own frozen policy"},
                {"id": "R817-D06", "decision": "second-project regression NOT_RUN (no clean fixture)"}],
            "gates": GATES, "answers": answers}
