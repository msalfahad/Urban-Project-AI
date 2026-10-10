"""R8.18 lab registers: every JSON register of the R8.18 package from the r8_18_qortuba build (no number typed in).

Published numbers come from the REBUILD (ctx["r8_18"]: the frozen policies with the one disclosed WF2-L1 wiring
correction); the blind record is quoted beside them. The blind record (WALL_FACE_V2_BLIND_RESULT) and the freeze record
(R8_18_FREEZE -> WALL_FACE_V2_FREEZE in the package) are committed before this module ran and are never rewritten here.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import r8_17_registers as R17G
import r8_18_qortuba as Q
from engine.source import owner_method_facts as MF, reveal_finish as RF, run_manifest as RM
from engine.source import wall_faces as V1, wall_faces_v2 as WF, wall_height as WH, waterproofing as WP

ROOT = Path(__file__).resolve().parents[2]
GATES = {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO", "PRODUCTION_MIGRATION": "NO"}
REG17 = ROOT / "tests/r8_17/registers"
ROWS = Q.R17.R15.ROWS
DRY_FACT = "QORTUBA-NEW-DRY-WALL-FINISH-HEIGHT-OWNER-001"
WET_FACT = "QORTUBA-NEW-WET-SERVICE-FINISH-OWNER-001"
FLOOR = "the selected SECOND FLOOR apartment (PLAN_VARIANT_4_SELECTED, region RC:MODEL_SPACE:4267:540:1649)"
SHADOW = "SHADOW_ONLY: no baseline approval, no migration transaction, no release gate passed"
ANCHOR = "SOURCE_ANCHOR: DXF anchored, DWG identity NOT_ESTABLISHED"
COL_Q = "QORTUBA_NEW_COLUMN_FACE_FINISH"
DUCT_WHY = ("the duct is on the owner's do-not-ask list for R8.18 and no finish for its faces is stated in any rule or "
            "fact: reported UNRESOLVED, not asked again")
ANTI_CAL = {"what": "a pre-freeze repository grep for 'waterproof' surfaced historical OLD-revision figures in "
                    "APPROVED_QUANTITIES.json (bathroom upturn 30.225 lm, PAINTRY 11.150 lm)",
            "effect": "NONE: the waterproofing policy has no tunable parameter (floor = certified site area; upturn = "
                      "gross site boundary; 0.15 m from US-04); the frozen run was blind (expected_value_given False, "
                      "historical_quantities_used False); the R8.18 values are not compared to them",
            "is_target": False}
WP_LABEL = ("the PAINTRY window / sliding-door spans carry the label FLOOR_CONTACT_UNPROVEN in perimeter_by_class_m "
            "because classify_v4 was called without the floor-contact map: a LABEL only - the length is in the gross "
            "upturn either way (doorways and openings are never deducted)")


def jl(p):
    return json.loads(Path(p).read_text())


def r6(v):
    return None if v is None else round(v, 6)


def fsum(xs):
    return r6(math.fsum(xs))


def trade_register(rb, trade, schema, extra=None):
    row = rb["trade_rows"][trade]
    rooms = {sid: dict(v, floor=FLOOR) for sid, v in row["rooms"].items()}
    recon = {"sum_of_rooms_m2": fsum(v["authorised_m2"] for v in rooms.values()),
             "AUTHORISED_SUBTOTAL_M2": row["AUTHORISED_SUBTOTAL_M2"]}
    recon["reconciles"] = abs(recon["sum_of_rooms_m2"] - row["AUTHORISED_SUBTOTAL_M2"]) < 1e-6
    for sid, v in rooms.items():
        parts = fsum([v["wall_plane_net_m2"], v["jamb_reveals_m2"], v["head_reveals_m2"]])
        v["components_reconcile"] = abs(parts - v["authorised_m2"]) < 1e-6
    unres = fsum(x["area_m2"] for x in row["unresolved_contributors"])
    return dict({"SCHEMA": schema, "row": trade, "unit": "m2", "state": row["state"],
                 "AUTHORISED_SUBTOTAL_M2": row["AUTHORISED_SUBTOTAL_M2"], "COMPLETE_M2": row["COMPLETE_M2"],
                 "complete_row_rule": "COMPLETE is null while ANY contributor is UNRESOLVED (zero materiality "
                                      "tolerance); the authorised subtotal is published with the unresolved list",
                 "per_floor": {FLOOR: {"AUTHORISED_SUBTOTAL_M2": row["AUTHORISED_SUBTOTAL_M2"],
                                       "rooms": sorted(rooms)}},
                 "per_room": rooms, "reconciliation": recon,
                 "unresolved_contributors": row["unresolved_contributors"], "unresolved_area_m2": unres,
                 "unresolved_reveals": row["unresolved_reveals"], "blocked_rooms": row["blocked_rooms"],
                 "release_blockers": [f"{len(row['unresolved_contributors'])} UNRESOLVED contributors "
                                      f"({unres} m2: column / duct finish authority)", ANCHOR, SHADOW],
                 "final": False}, **(extra or {}))


def registers(ctx):
    base17, _ = R17G.registers(ctx)
    rb, blind, fz = ctx["r8_18"], ctx["r8_18_blind"], ctx["r8_18_freeze"]
    wm = fz["qortuba_wall_face_method"]
    rows, dig = ctx["rows_new"], ctx["dig"]
    rec = jl(ROOT / "research/external_engine_lab/r8_18_recommendation.json")
    six = {rid: R17G.R16G.R15G._row_view(rid, rows[rid], dig[rid]) for rid in ROWS}
    s17 = jl(REG17 / "QORTUBA_R8_17_STATUS.json")
    facts = {f["fact_id"]: f for f in jl(ROOT / "data/registry/OWNER_METHOD_FACTS.json")["facts"]}
    rules = {r["rule_id"]: r for r in jl(ROOT / "data/registry/URBAN_OWNER_METHOD_RULES.json")["rules"]}
    r13 = next(x for x in rec["inspected"] if "R-13 (" in x)
    rv = rb["reveals"]
    per = rb["per_site"]
    regs = {}
    # ------------------------------------------------------------------ owner side
    col_unres = [x for t in ("PLASTER", "WALL_TILE") for x in rb["trade_rows"][t]["unresolved_contributors"]
                 if x["class"] == V1.COLUMN_FACE]
    duct_unres = [x for x in rb["trade_rows"]["PLASTER"]["unresolved_contributors"] if x["class"] == V1.OBSTACLE_FACE]
    regs["OWNER_ACTION_REGISTER"] = {
        "SCHEMA": "URBAN_OWNER_ACTION_REGISTER_V15",
        "headline": "NO OWNER ACTION REQUIRED FOR THE AUTHORISED SUBTOTALS. ONE NEW QUESTION TO COMPLETE THE "
                    "PLASTER / PAINT / WALL_TILE ROWS.",
        "required_now": [],
        "needed_to_complete_rows": [
            {"id": COL_Q, "blocks": "COMPLETE_M2 of PLASTER, PAINT, WALL_TILE and WET_WALL_TILE_PREP (the authorised "
                                    "subtotals are published without it)",
             "question": "Are the exposed column faces finished like the wall around them - plaster and paint in the "
                         "dry rooms, wall tile in the bathrooms and the PAINTRY?",
             "why_new": "no rule or fact states a column-face finish: R-13 is the blockwork sheet's full-deduction "
                        "column (R8.17 misread it), owner_rules section E is skirting only",
             "area_at_stake_m2": {"dry_columns": fsum(x["area_m2"] for x in col_unres
                                                      if x["site"] in rb["trade_rows"]["PLASTER"]["rooms"]),
                                  "wet_service_columns": fsum(x["area_m2"] for x in col_unres
                                                              if x["site"] in rb["trade_rows"]["WALL_TILE"]["rooms"])},
             "current": "UNRESOLVED contributors listed with their areas; never silently excluded or included"}],
        "not_asked": [{"item": "duct face finish", "why": DUCT_WHY,
                       "area_m2": fsum(x["area_m2"] for x in duct_unres)}],
        "answered_this_round": [f"{DRY_FACT}@v1 (dry plaster / paint 3.15 m)", "URBAN-WALL-FINISH-HEIGHT-METHOD@v1",
                                "URBAN-REVEAL-FINISH-METHOD@v1"],
        "do_not_ask": ["dry-room Qortuba wall height = 3.15 m", "dynamic floor-by-floor height method",
                       "wet wall-tile height = 3.20 m", "default reveal = plaster",
                       "porcelain reveals only when specifically required",
                       "sliding-door profile-dependent reveal treatment", "Hall / Pantry sliding glass door",
                       "normal windows", "skirting", "marble", "duct", "passage heads"]}
    regs["OWNER_METHOD_RULE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_18_OWNER_METHOD_RULE_REGISTER_V1",
        "new_urban_rules": [rules["URBAN-WALL-FINISH-HEIGHT-METHOD"], rules["URBAN-REVEAL-FINISH-METHOD"]],
        "kept_urban_rules": sorted(k for k in rules if k not in ("URBAN-WALL-FINISH-HEIGHT-METHOD",
                                                                  "URBAN-REVEAL-FINISH-METHOD")),
        "new_project_fact": facts[DRY_FACT], "fact_policy": MF.POLICY_ID,
        "superseded_in_scope": facts[DRY_FACT].get("relations"),
        "kept_separate": f"{WET_FACT}@v1 (wet / service wall tile 3.20 m) - never replaced by 3.15 m",
        "never": rules["URBAN-WALL-FINISH-HEIGHT-METHOD"]["never"] + rules["URBAN-REVEAL-FINISH-METHOD"]["never"]}
    # ------------------------------------------------------------------ heights
    regs["WALL_HEIGHT_AUTHORITY_POLICY"] = {
        "SCHEMA": "URBAN_R8_18_WALL_HEIGHT_AUTHORITY_POLICY_V1", "policy": WH.policy_record(),
        "urban_rule": rules["URBAN-WALL-FINISH-HEIGHT-METHOD"],
        "no_company_constant": "no URBAN_DEFAULT_WALL_HEIGHT (or equivalent) exists in engine/ or the rule store",
        "future_derivation": rec["7_future_derivation"]}
    regs["QORTUBA_WALL_HEIGHT_REGISTER"] = {
        "SCHEMA": "URBAN_R8_18_QORTUBA_WALL_HEIGHT_REGISTER_V1", "floor": FLOOR,
        "scopes": rb["heights"],
        "governing": {k: {"value_m": v["value_m"], "governing": v["governing"], "authority": v["authority"],
                          "state": v["state"]} for k, v in rb["heights"].items()},
        "derivation": {k: next((c for c in v["candidates"] if c["kind"] == "DERIVED_CLEAR_HEIGHT"), None)
                       for k, v in rb["heights"].items()},
        "owner_rationale": facts[DRY_FACT]["statement"]["owner_rationale"],
        "rationale_is_formula": False,
        "conflicts": rb["height_conflicts"],
        "conflict_action": "flag only: WALL_TILE stays 3.20 m, never clipped to 3.15 m; not asked (the wet height is "
                           "on the do-not-ask list)",
        "never": wm["never"], "blind_equal": blind["heights"] == rb["heights"]}
    # ------------------------------------------------------------------ WF-O1 / V2
    v2_recon = {sid: {t: f["reconciliation"] for t, f in v["faces"].items()} for sid, v in per.items()}
    regs["WF_O1_ROOT_CAUSE"] = {
        "SCHEMA": "URBAN_R8_18_WF_O1_ROOT_CAUSE_V1", "id": "WF-O1", "found": "R8.17 (its own fail-closed check)",
        "root_cause": rec["1_wf_o1_cause"], "detail": rec["inspected"][0],
        "v1_failure_on_qortuba": ctx["wf_o1"],
        "v1_failure_on_a_synthetic_window": "test_r8_18_wall_faces_v2::test_22 runs the frozen V1 on the same window "
                                            "fixture and asserts AREA_RECONCILIATION_FAILED (and test_03 asserts V2 "
                                            "state == COMPUTED with below-sill and above-opening surfaces)",
        "why_it_passed_the_r8_17_freeze": "the synthetic window test asserted the area of the primary form, never "
                                          "state == COMPUTED",
        "fix": rec["2_v2_fix"], "v2_reconciliation_on_qortuba": v2_recon,
        "all_sites_reconcile": rb["all_sites_reconcile"],
        "special_cased": "NOTHING: no handle, project or site id in engine/source/wall_faces_v2.py"}
    regs["WALL_FACE_V2_POLICY"] = {
        "SCHEMA": "URBAN_R8_18_WALL_FACE_V2_POLICY_V1", "policy": WF.policy_record(),
        "method": wm, "freeze": {k: fz[k] for k in ("frozen_commit", "policies", "synthetic_test_count", "order",
                                                    "rule", "amendments")},
        "v1_unchanged": fz["unchanged"], "topology_effect": "NONE (trade layer only)"}
    tclosure = [s for v in per.values() for f in v["faces"].values() for s in f["surfaces"]
                if any(str(x).startswith("TCLOSURE|") for x in s.get("sources", ()))]
    regs["WALL_SURFACE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_18_WALL_SURFACE_REGISTER_V1", "policy": WF.POLICY_ID, "floor": FLOOR,
        "per_site": {sid: {"zones": v["zones"], "class": v["class"], "trades": v["trades"],
                           "passages_in_site": v["passages_in_site"],
                           "faces": {t: {k: f.get(k) for k in ("state", "height_m", "height_authority", "lengths_m",
                                                               "areas_m2", "openings", "head_faces", "surfaces",
                                                               "reconciliation", "conservation", "blockers")}
                                     for t, f in v["faces"].items()}} for sid, v in per.items()},
        "all_sites_reconcile": rb["all_sites_reconcile"], "double_count_guard": rb["double_count_guard"],
        "topology_closures": {"surfaces_from_topology_closures": len(tclosure),
                              "area_m2": fsum(s["area_m2"] for s in tclosure),
                              "zero_closure_lengths_m": {sid: {t: f["lengths_m"].get(V1.ZERO, 0.0)
                                                               for t, f in v["faces"].items()}
                                                         for sid, v in per.items()},
                              "door_and_glazed_closure_spans": sum(1 for v in per.values() for f in
                                                                   list(v["faces"].values())[:1] for sp in f["spans"]
                                                                   if any(str(x).startswith("CLOSURE|")
                                                                          for x in sp["sources"])),
                              "door_and_glazed_closure_spans_are": "OPENING spans: the opening rectangle is "
                                                                   "deducted, the closure line itself has no material",
                              "rule": "ZERO material, ZERO area (class ZERO_TOPOLOGY_CLOSURE, never wall plane)"},
        "blind_equal_per_site": blind["per_site"] == rb["per_site"]}
    # ------------------------------------------------------------------ trades
    pl = rb["trade_rows"]["PLASTER"]
    regs["PLASTER_REGISTER"] = trade_register(rb, "PLASTER", "URBAN_R8_18_PLASTER_REGISTER_V1", {
        "row_id": "DRY_WALL_PLASTER", "height": rb["heights"]["DRY_INTERNAL_ROOM|PLASTER"]["value_m"],
        "height_authority": rb["heights"]["DRY_INTERNAL_ROOM|PLASTER"]["authority"],
        "WET_SERVICE_REVEAL_PLASTER": {
            "unit": "m2", "AUTHORISED_M2": pl["wet_service_owned_reveal_plaster_m2"],
            "reveals": pl["wet_service_owned_reveals"],
            "unresolved_reveals": pl["wet_service_owned_unresolved_reveals"],
            "why_separate": "reveals owned by a wet / service room are PLASTER_DEFAULT (owner rule), never tile and "
                            "never paint; kept apart from DRY_WALL_PLASTER and from WALL_TILE",
            "blind": blind["trade_rows"]["PLASTER"]["wet_service_owned_reveal_plaster_m2"]},
        "kept_separate_from": ["WET_WALL_TILE_PREP", "WALL_TILE"]})
    regs["PAINT_REGISTER"] = trade_register(rb, "PAINT", "URBAN_R8_18_PAINT_REGISTER_V1", {
        "height": rb["heights"]["DRY_INTERNAL_ROOM|PAINT"]["value_m"],
        "height_authority": rb["heights"]["DRY_INTERNAL_ROOM|PAINT"]["authority"],
        "vs_dry_plaster": {"PAINT_M2": rb["trade_rows"]["PAINT"]["AUTHORISED_SUBTOTAL_M2"],
                           "DRY_WALL_PLASTER_M2": pl["AUTHORISED_SUBTOTAL_M2"],
                           "equal": rb["trade_rows"]["PAINT"]["AUTHORISED_SUBTOTAL_M2"] ==
                           pl["AUTHORISED_SUBTOTAL_M2"],
                           "why": "every dry-owned wall surface and reveal is PLASTER_AND_PAINT at the same 3.15 m; "
                                  "the wet / service-owned reveals are plaster only (no paint invented)"},
        "paintry": "NO PAINT: the PAINTRY keeps QP-07 (kitchen / preparation zone for the ceramic takeoff) - full wall "
                   "tile to 3.20 m; no PAINTRY paint height is established, so no PAINTRY paint is computed"})
    regs["WALL_TILE_REGISTER"] = trade_register(rb, "WALL_TILE", "URBAN_R8_18_WALL_TILE_REGISTER_V1", {
        "height": rb["heights"]["WET_SERVICE_ROOM|WALL_TILE"]["value_m"],
        "height_authority": {k: rb["heights"][k]["authority"] for k in ("WET_SERVICE_ROOM|WALL_TILE",
                                                                         "SERVICE_ROOM|WALL_TILE")},
        "WET_WALL_TILE_PREP": trade_register(rb, "WET_WALL_TILE_PREP", "URBAN_R8_18_WET_WALL_TILE_PREP_V1"),
        "prep_equals_tile": rb["trade_rows"]["WET_WALL_TILE_PREP"]["AUTHORISED_SUBTOTAL_M2"] ==
        rb["trade_rows"]["WALL_TILE"]["AUTHORISED_SUBTOTAL_M2"],
        "prep_why": "the same physical surface set (US-03 preparation under the tile), a separate BOQ item",
        "reveals": "wet / service reveals are PLASTER_DEFAULT (never tile without explicit authority) - see "
                   "PLASTER_REGISTER.WET_SERVICE_REVEAL_PLASTER",
        "height_conflict": rb["height_conflicts"]})
    # ------------------------------------------------------------------ reveals
    regs["REVEAL_FINISH_POLICY"] = {"SCHEMA": "URBAN_R8_18_REVEAL_FINISH_POLICY_V1", "policy": RF.policy_record(),
                                    "urban_rule": rules["URBAN-REVEAL-FINISH-METHOD"],
                                    "qortuba": wm["reveal_finish"]}
    by_finish = {}
    for x in rv:
        b = by_finish.setdefault(x["finish"], {"count": 0, "area_m2": 0.0})
        b["count"] += 1
        b["area_m2"] = r6(b["area_m2"] + (x["area_m2"] or 0.0))
    passages = {x["opening"]: [] for x in rv if x["kind"].startswith("OPEN_PASSAGE")}
    for x in rv:
        if x["opening"] in passages:
            passages[x["opening"]].append({k: x.get(k) for k in ("surface", "owner_zones", "finish", "depth_m",
                                                             "area_m2")})
    hall_soffit = next(x["area_m2"] for x in rv if x["kind"] == "OPEN_PASSAGE_WITH_HEAD" and
                       x["surface"] == "TOP_REVEAL")
    regs["REVEAL_FINISH_REGISTER"] = {
        "SCHEMA": "URBAN_R8_18_REVEAL_FINISH_REGISTER_V1", "policy": RF.POLICY_ID, "reveals": rv, "count": len(rv),
        "by_finish": by_finish,
        "porcelain": [x for x in rv if x["finish"] == RF.PORCELAIN_EXPLICIT] or "NONE (no explicit authority)",
        "unresolved": [x for x in rv if x["finish"] == RF.UNRESOLVED],
        "sliding_door_split": rb["sliding_door_split"],
        "sliding_door": "tracks H542 (flush with the HALL face) and H533 (0.05 m from the PAINTRY face): HALL owns no "
                        "reveal, PAINTRY owns 0.05 m; the north jamb face is drawn by a wall line, the south jamb face "
                        "only by H480 (FIXTURE) -> UNRESOLVED (WF2-L1)",
        "passages": passages,
        "hall_lobby_soffit_vs_q14": {"reveal_soffit_m2": hall_soffit,
                                     "q14_soffit_exclusion_m2": six["Q-14"]["SOFFIT_EXCLUSION_M2"],
                                     "equal": abs(hall_soffit - six["Q-14"]["SOFFIT_EXCLUSION_M2"]) < 1e-6},
        "blind_vs_rebuild": ctx["blind_vs_rebuild"],
        "double_count_guard": rb["double_count_guard"],
        "never": RF.policy_record()["never"]}
    regs["COLUMN_DUCT_FINISH_REGISTER"] = {
        "SCHEMA": "URBAN_R8_18_COLUMN_DUCT_FINISH_REGISTER_V1",
        "method": {"column_faces": wm["column_faces"], "obstacle_faces": wm["obstacle_faces"],
                   "why": wm["unresolved_why"]},
        "columns": col_unres, "duct_faces": duct_unres,
        "column_area_m2": {"dry": regs["OWNER_ACTION_REGISTER"]["needed_to_complete_rows"][0]["area_at_stake_m2"]
                           ["dry_columns"],
                           "wet_service": regs["OWNER_ACTION_REGISTER"]["needed_to_complete_rows"][0]
                           ["area_at_stake_m2"]["wet_service_columns"]},
        "duct_area_m2": fsum(x["area_m2"] for x in duct_unres),
        "r8_17_misreading": {"disclosed": True, "what": r13,
                             "effect": "no R8.17 value was published on it (PLASTER / PAINT were BLOCKED; WALL_TILE "
                                       "unpublished); corrected here: column faces UNRESOLVED in every trade"},
        "owner_question": COL_Q, "duct_note": DUCT_WHY,
        "rule": "never excluded silently, never finished by assumption: listed, with areas, as UNRESOLVED contributors"}
    # ------------------------------------------------------------------ waterproofing
    w = rb["waterproofing"]
    wrooms = {sid: dict(v, floor=FLOOR, perimeter_reconciles=abs(fsum(v["perimeter_by_class_m"].values()) -
                                                                 v[WP.UPTURN]) < 1e-6)
              for sid, v in w["rooms"].items()}
    sk = ctx["skirting_v4"]
    regs["WATERPROOFING_POLICY"] = {"SCHEMA": "URBAN_R8_18_WATERPROOFING_POLICY_V1", "policy": WP.policy_record(),
                                    "method": wm["waterproofing"], "recommendation": rec["12_waterproofing"]}
    regs["WATERPROOFING_REGISTER"] = {
        "SCHEMA": "URBAN_R8_18_WATERPROOFING_REGISTER_V1", "state": "COMPUTED_SHADOW"
        if all(v["state"] == "COMPUTED" for v in wrooms.values()) else "BLOCKED",
        "rows": {WP.FLOOR: {"unit": "m2", "value": w["totals"][WP.FLOOR]},
                 WP.UPTURN: {"unit": "lm", "value": w["totals"][WP.UPTURN],
                             "upturn_height_m": wm["waterproofing"]["upturn_height_m"]}},
        "per_floor": {FLOOR: w["totals"]}, "per_room": wrooms,
        "doorways_deducted": any(v["doorways_deducted"] for v in wrooms.values()),
        "opening_lengths_in_upturn_m": {sid: fsum(L for c, L in v["perimeter_by_class_m"].items()
                                                  if c not in ("REAL_WALL_FACE", "COLUMN_FACE", "HOLE_PERIMETER"))
                                        for sid, v in wrooms.items()},
        "skirting_path_used": False,
        "vs_skirting": {"skirting_payable_lm": sk["PAYABLE_LM"],
                        "independent": "the upturn is the GROSS site boundary of the wet / service rooms; skirting is "
                                       "the dry payable path - different sites, different policy"},
        "marble": {"separate": True, "marble_quantities": ctx["marble_quantities"],
                   "effect_on_waterproofing": "NONE (no explicit rule links a threshold to the membrane)"},
        "label_note": WP_LABEL, "anti_calibration": ANTI_CAL,
        "blind_equal": blind["waterproofing"] == rb["waterproofing"],
        "release_blockers": [ANCHOR, SHADOW], "final": False}
    # ------------------------------------------------------------------ regression rows
    v17 = {rid: v["VALUE"] for rid, v in s17["six_rows"].items()}
    q13, q14 = rows["Q-13"], rows["Q-14"]
    regs["Q13_STATUS"] = dict(six["Q-13"], SCHEMA="URBAN_R8_18_Q13_STATUS_V1",
                              regression_vs_r8_17={"R8.17": v17["Q-13"], "R8.18": q13["value"],
                                                   "delta_m2": round(q13["value"] - v17["Q-13"], 4),
                                                   "is_target": False}, historical_matching="NONE")
    regs["Q14_STATUS"] = dict(six["Q-14"], SCHEMA="URBAN_R8_18_Q14_STATUS_V1",
                              regression_vs_r8_17={"R8.17": v17["Q-14"], "R8.18": q14["value"],
                                                   "delta_m2": round(q14["value"] - v17["Q-14"], 4),
                                                   "wall_face_effect": "NONE (wall-face, reveal and waterproofing "
                                                                       "are trade layers; no ceiling input changed)",
                                                   "is_target": False},
                              preserved=["duct exclusion", "Hall / Lobby soffit exclusion (= the passage soffit reveal "
                                         "surface, counted once in the wall trade, never in the ceiling)",
                                         "M.B.ROOM / DRESS full-height ceiling", "I1471 door strip NOT_IN_TRADE"],
                              historical_matching="NONE")
    sk17 = jl(REG17 / "SKIRTING_REGISTER.json")
    regs["SKIRTING_REGISTER"] = dict(base17["SKIRTING_REGISTER"], SCHEMA="URBAN_R8_18_SKIRTING_REGISTER_V1",
                                     regression_vs_r8_17={"R8.17": sk17["SKIRTING_LM"], "R8.18": sk["PAYABLE_LM"],
                                                          "unchanged": ctx["skirting_v4_vs_r8_17"]["payable"],
                                                          "v4_edited": False, "is_target": False})
    hp17 = jl(REG17 / "HIDDEN_PROFILE_REGISTER.json")
    regs["HIDDEN_PROFILE_REGISTER"] = dict(base17["HIDDEN_PROFILE_REGISTER"],
                                           SCHEMA="URBAN_R8_18_HIDDEN_PROFILE_REGISTER_V1",
                                           regression_vs_r8_17={"R8.17": hp17["HIDDEN_PROFILE_LM"],
                                                                "R8.18": sk["PAYABLE_LM"],
                                                                "unchanged": hp17["HIDDEN_PROFILE_LM"] ==
                                                                sk["PAYABLE_LM"]})
    mq17 = jl(REG17 / "MARBLE_THRESHOLD_REGISTER.json")["quantities"]
    regs["MARBLE_THRESHOLD_REGISTER"] = dict(base17["MARBLE_THRESHOLD_REGISTER"],
                                             SCHEMA="URBAN_R8_18_MARBLE_THRESHOLD_REGISTER_V1",
                                             regression_vs_r8_17={"R8.17": mq17, "R8.18": ctx["marble_quantities"],
                                                                  "unchanged": mq17 == ctx["marble_quantities"],
                                                                  "waterproofing": "independent"})
    regs["SECOND_PROJECT_REGRESSION"] = dict(base17["SECOND_PROJECT_REGRESSION"],
                                             SCHEMA="URBAN_R8_18_SECOND_PROJECT_REGRESSION_V1",
                                             substitute="the generic synthetic families of R8.13-R8.17 plus the 22 "
                                                        "wall-face V2, 7 waterproofing and 7 height / reveal "
                                                        "synthetic tests of R8.18 (frozen before the Qortuba run)",
                                             why_not_run="no second project has a resolved unit AND a certified "
                                                         "topology; running one anyway would need an adopted unit "
                                                         "(a calibration) or an uncertified topology",
                                             next="R8.19: a second project with a resolved unit and certified "
                                                  "topology")
    regs["SOURCE_ANCHOR_STATUS"] = dict(base17["SOURCE_ANCHOR_STATUS"], SCHEMA="URBAN_R8_18_SOURCE_ANCHOR_STATUS_V1")
    regs["CLOSURE_RELEASE_STATUS"] = dict(base17["CLOSURE_RELEASE_STATUS"],
                                          SCHEMA="URBAN_R8_18_CLOSURE_RELEASE_STATUS_V1", production="NO")
    d17 = jl(REG17 / "DIGEST_HIERARCHY.json")["rows"]

    def dg(d, layer):
        return d[layer] if layer == "TOPOLOGY_RUN_INPUT_DIGEST" else d[layer]["digest"]
    digest_vs_r8_17 = {rid: {layer: "CHANGED" if dg(dig[rid], layer) != dg(d17[rid], layer) else "SAME"
                             for layer in RM.DIGEST_LAYERS} for rid in ROWS}
    tr = rb["trade_rows"]

    def trow(t, reg):
        return {"state": tr[t]["state"], "AUTHORISED_SUBTOTAL_M2": tr[t]["AUTHORISED_SUBTOTAL_M2"],
                "COMPLETE_M2": tr[t]["COMPLETE_M2"], "release_blockers": regs[reg]["release_blockers"]}
    extra = {"SKIRTING": {"state": regs["SKIRTING_REGISTER"]["state"], "value_lm": sk["PAYABLE_LM"],
                          "release_blockers": regs["SKIRTING_REGISTER"]["release_blockers"]},
             "HIDDEN_PROFILE": {"state": regs["HIDDEN_PROFILE_REGISTER"]["state"], "value_lm": sk["PAYABLE_LM"],
                                "release_blockers": regs["HIDDEN_PROFILE_REGISTER"]["release_blockers"]},
             "MARBLE_THRESHOLD": {"state": "COMPUTED_SHADOW", **ctx["marble_quantities"],
                                  "release_blockers": regs["MARBLE_THRESHOLD_REGISTER"]["release_blockers"]},
             "DRY_WALL_PLASTER": trow("PLASTER", "PLASTER_REGISTER"),
             "WET_SERVICE_REVEAL_PLASTER": {"state": "COMPUTED_SHADOW_WITH_UNRESOLVED"
                                            if pl["wet_service_owned_unresolved_reveals"] else "COMPUTED_SHADOW",
                                            "AUTHORISED_M2": pl["wet_service_owned_reveal_plaster_m2"],
                                            "unresolved_reveals": pl["wet_service_owned_unresolved_reveals"],
                                            "release_blockers": [ANCHOR, SHADOW]},
             "PAINT": trow("PAINT", "PAINT_REGISTER"),
             "WALL_TILE": trow("WALL_TILE", "WALL_TILE_REGISTER"),
             "WET_WALL_TILE_PREP": trow("WET_WALL_TILE_PREP", "WALL_TILE_REGISTER"),
             WP.FLOOR: {"state": regs["WATERPROOFING_REGISTER"]["state"], "value_m2": w["totals"][WP.FLOOR],
                        "release_blockers": [ANCHOR, SHADOW]},
             WP.UPTURN: {"state": regs["WATERPROOFING_REGISTER"]["state"], "value_lm": w["totals"][WP.UPTURN],
                         "release_blockers": [ANCHOR, SHADOW]}}
    regs["QORTUBA_R8_18_STATUS"] = {
        "SCHEMA": "URBAN_R8_18_QORTUBA_STATUS_V1", "six_rows": six, "extra_rows": extra,
        "rows_old": {rid: {"state": v["state"], "value": v["value"]} for rid, v in ctx["rows_old"].items()},
        "old_revision_unchanged_vs_r8_17": {rid: (ctx["rows_old"][rid]["state"], ctx["rows_old"][rid]["value"]) ==
                                            (s17["rows_old"][rid]["state"], s17["rows_old"][rid]["value"])
                                            for rid in ROWS},
        "vs_r8_17": {rid: {"R8.17": v17[rid], "R8.18": six[rid]["VALUE"], "delta": round(six[rid]["VALUE"] -
                                                                                         v17[rid], 4)} for rid in ROWS},
        "digest_vs_r8_17": digest_vs_r8_17, "determinism": ctx["det"],
        "reproduces": {"r8_18_blind": ctx["reproduces_r8_18_blind"], "v4_blind": ctx["reproduces_v4_blind"],
                       "r8_16": ctx["reproduces_r8_16"]},
        "blind_vs_rebuild": ctx["blind_vs_rebuild"], "final": "SHADOW only: no row is FINAL",
        "production_migration": "NO"}
    regs["R8_18_DECISION_REGISTER"] = decision_register(regs, ctx, rec, six)
    return regs, ctx


def decision_register(regs, ctx, rec, six):
    rb, fz = ctx["r8_18"], ctx["r8_18_freeze"]
    st, rr = regs["QORTUBA_R8_18_STATUS"], regs["REVEAL_FINISH_REGISTER"]
    pl, pa, wt = regs["PLASTER_REGISTER"], regs["PAINT_REGISTER"], regs["WALL_TILE_REGISTER"]
    wp, cd, hr = regs["WATERPROOFING_REGISTER"], regs["COLUMN_DUCT_FINISH_REGISTER"], regs["QORTUBA_WALL_HEIGHT_REGISTER"]
    rv = rb["reveals"]
    pr = {f"{'/'.join(sorted(v['zones']))} ({sid})": v["authorised_m2"] for sid, v in pl["per_room"].items()}
    tile_rooms = {sid: (v["zones"], v["authorised_m2"]) for sid, v in wt["per_room"].items()}
    mb = [x for x in rv if x["kind"] == "OPEN_PASSAGE_FULL_HEIGHT"]
    hall_p = [x for x in rv if x["kind"] == "OPEN_PASSAGE_WITH_HEAD"]
    slide = [x for x in rv if x["kind"] == "SLIDING_GLAZED_DOOR"]
    remaining = {rid: v["RELEASE_BLOCKERS"] for rid, v in six.items()}
    remaining |= {k: v.get("release_blockers") for k, v in st["extra_rows"].items()}
    changed = {rid: st["vs_r8_17"][rid] for rid in ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14")}
    answers = {
        "1_height_scoped_authority": "YES: WALL_HEIGHT_AUTHORITY_POLICY_V1 resolves one height per (project, revision, "
                                     "floor / region, plan, space class, trade) from ranked candidates; no Urban "
                                     "constant exists",
        "2_315_scope": f"YES: {hr['governing']['DRY_INTERNAL_ROOM|PLASTER']['value_m']} m "
                       f"({hr['governing']['DRY_INTERNAL_ROOM|PLASTER']['governing']}, "
                       f"{hr['governing']['DRY_INTERNAL_ROOM|PLASTER']['authority']}) for DRY_INTERNAL_ROOM PLASTER "
                       "and PAINT only (Qortuba new revision, selected plan / region)",
        "3_rationale_not_formula": "YES: 4.00 - 0.60 - 0.15 - 0.10 stored as OWNER_RATIONALE; the rank-3 derivation "
                                   "is BLOCKED (beam, ceiling and build-up components have no source authority)",
        "4_320_preserved": f"YES: WALL_TILE {hr['governing']['WET_SERVICE_ROOM|WALL_TILE']['value_m']} m from "
                           f"{WET_FACT}@v1; conflict flagged {[c['state'] for c in hr['conflicts']]}, never clipped",
        "5_wf_o1_cause": rec["1_wf_o1_cause"],
        "6_v2_fix": rec["2_v2_fix"],
        "7_frozen_before_results": f"YES: freeze {fz['frozen_commit'][:7]} (amendments {fz['amendments'] or 'NONE'}), "
                                   "blind record committed before any comparison",
        "8_every_fixture_both_checks": f"YES: {fz['synthetic_test_count']} synthetic tests; every valid wall-face "
                                       "fixture asserts state == COMPUTED and reconciliation PASS; test_22 feeds a "
                                       "broken surface list and gets FAIL",
        "9_blind_run_reconciles": f"YES: all_sites_reconcile {rb['all_sites_reconcile']}, double-count guard "
                                  f"{rb['double_count_guard']['state']}",
        "10_dry_plaster_published": f"YES as SHADOW authorised subtotal ({pl['state']}); COMPLETE_M2 null",
        "11_plaster_total_and_per_room": {"DRY_WALL_PLASTER_AUTHORISED_M2": pl["AUTHORISED_SUBTOTAL_M2"],
                                          "per_room": pr,
                                          "WET_SERVICE_REVEAL_PLASTER_M2": pl["WET_SERVICE_REVEAL_PLASTER"]
                                          ["AUTHORISED_M2"]},
        "12_paint_published": f"YES as SHADOW authorised subtotal ({pa['state']}); COMPLETE_M2 null",
        "13_paint_total_and_difference": {"PAINT_AUTHORISED_M2": pa["AUTHORISED_SUBTOTAL_M2"],
                                          "why": pa["vs_dry_plaster"]["why"]},
        "14_tile_published": f"YES as SHADOW authorised subtotal ({wt['state']}); COMPLETE_M2 null; "
                             f"WET_WALL_TILE_PREP {wt['WET_WALL_TILE_PREP']['AUTHORISED_SUBTOTAL_M2']} m2 separate",
        "15_bathroom_tile": {sid: v for sid, v in tile_rooms.items() if "BATH" in v[0]},
        "16_paintry_tile": {sid: v for sid, v in tile_rooms.items() if "PAINTRY" in v[0]},
        "17_reveals_separate_surfaces": f"YES: {rr['count']} reveal records (opening, owning side, surface), each "
                                        "its own identity; the double-count guard covers wall surfaces and reveals",
        "18_default_reveal": "PLASTER (URBAN-REVEAL-FINISH-METHOD@v1); PLASTER_AND_PAINT only on a painted dry owner",
        "19_porcelain_only_explicit": f"YES: porcelain reveals {rr['porcelain']}",
        "20_sliding_door_reveals": rr["sliding_door"],
        "21_profile_resolved_ownership": f"YES for the depth split ({rb['sliding_door_split']}); the south "
                                         "PAINTRY-side jamb face is not drawn by a wall line -> UNRESOLVED",
        "22_ambiguous_reveals": [f"{x['opening']} {x['surface']} ({(x.get('owner_zones') or ['-'])[0]})"
                                 for x in rr["unresolved"]],
        "23_column_faces_assigned": f"NO: UNRESOLVED in every trade (dry {cd['column_area_m2']['dry']} m2, wet / "
                                    f"service {cd['column_area_m2']['wet_service']} m2)",
        "24_duct_assigned": f"NO: UNRESOLVED ({cd['duct_area_m2']} m2)",
        "25_why_blocked": cd["method"]["why"] | {"r8_17_misreading": cd["r8_17_misreading"]["what"]},
        "26_hall_lobby_jambs_soffit": {"jambs": [(x["surface"], x["area_m2"]) for x in hall_p
                                                 if x["surface"] != "TOP_REVEAL"],
                                       "soffit": rr["hall_lobby_soffit_vs_q14"]},
        "27_mb_dress_no_invented_jamb": f"YES: {[(x['surface'], x['area_m2']) for x in mb]} - one physical jamb, "
                                        "full height, no soffit; the H518 side is wall plane, never a jamb",
        "28_closures_zero": f"YES: {regs['WALL_SURFACE_REGISTER']['topology_closures']['surfaces_from_topology_closures']}"
                            " surfaces from topology closures, area "
                            f"{regs['WALL_SURFACE_REGISTER']['topology_closures']['area_m2']} m2",
        "29_waterproofing_implemented": f"YES: {WP.POLICY_ID} (own policy, frozen, blind), {wp['state']}",
        "30_waterproofing_floor_m2": wp["rows"][WP.FLOOR]["value"],
        "31_waterproofing_upturn_lm": wp["rows"][WP.UPTURN]["value"],
        "32_upturn_15cm": f"YES: {wp['rows'][WP.UPTURN]['upturn_height_m']} m (US-04)",
        "33_doorways_not_deducted": f"YES: doorways_deducted {wp['doorways_deducted']}; door lengths in the upturn "
                                    f"{wp['opening_lengths_in_upturn_m']} (doors, the sliding door and the window, all kept)",
        "34_marble_separate": "YES: " + wp["marble"]["effect_on_waterproofing"],
        "35_floor_ceiling_rows_changed": changed,
        "36_skirting_hidden_profile_changed": {"SKIRTING": regs["SKIRTING_REGISTER"]["regression_vs_r8_17"],
                                               "HIDDEN_PROFILE": regs["HIDDEN_PROFILE_REGISTER"]
                                               ["regression_vs_r8_17"]},
        "37_marble_changed": regs["MARBLE_THRESHOLD_REGISTER"]["regression_vs_r8_17"],
        "38_second_project": regs["SECOND_PROJECT_REGRESSION"]["state"] + " - " +
                             regs["SECOND_PROJECT_REGRESSION"]["why_not_run"],
        "39_source_anchor": regs["SOURCE_ANCHOR_STATUS"]["state"],
        "40_release_blockers": remaining,
        "41_new_silent_errors": [
            "WF2-L1 (blind-script wiring, found after the blind run): the reveal-face check accepted ANY drawn line, so "
            "H480 (FIXTURE) 'closed' the PAINTRY-side south jamb of the sliding door. Rebuild reads admitted wall / "
            "structural parts only: that one reveal 0.11 m2 PLASTER_DEFAULT -> UNRESOLVED; WET_SERVICE_REVEAL_PLASTER "
            f"{ctx['blind_vs_rebuild']['trade_row_differences']['PLASTER']['blind']['wet_service_owned_reveal_plaster_m2']}"
            f" -> {pl['WET_SERVICE_REVEAL_PLASTER']['AUTHORISED_M2']}; every authorised subtotal unchanged",
            "R8.17 cited R-13 as column-face finish authority (a misreading; no value was published on it)",
            WP_LABEL,
            ANTI_CAL["what"] + " - " + ANTI_CAL["effect"]],
        "42_r8_19": rec["14_r8_19"],
        "43_disagreements": rec["13_disagreements_with_chatgpt"]}
    return {"SCHEMA": "URBAN_R8_18_DECISION_REGISTER_V1", "recommendation_before_coding": rec,
            "order": fz["order"] + ["blind (583d726)", "rebuild / registers (WF2-L1 disclosed)"],
            "decisions": [
                {"id": "R818-D01", "decision": "WALL_HEIGHT_AUTHORITY_POLICY_V1: height is a scoped evidence object; "
                                               "Qortuba dry plaster / paint 3.15 m (owner fact, rank 4); no constant"},
                {"id": "R818-D02", "decision": "wet / service tile 3.20 m kept; the 3.15 / 3.20 relation flagged, "
                                               "never clipped"},
                {"id": "R818-D03", "decision": "WALL_FACE_SURFACE_POLICY_V2: one plane identity, two independent area "
                                               "paths, fail closed (WF-O1 fixed generically)"},
                {"id": "R818-D04", "decision": "REVEAL_FINISH_POLICY_V1: ownership from frame / leaf / track position, "
                                               "finish default plaster, porcelain only explicit"},
                {"id": "R818-D05", "decision": "PLASTER / PAINT / WALL_TILE / WET_WALL_TILE_PREP published as SHADOW "
                                               "authorised subtotals; COMPLETE null (columns, duct)"},
                {"id": "R818-D06", "decision": "WATERPROOFING_POLICY_V1: floor = wet site area, upturn = gross "
                                               "boundary, 0.15 m, doorways not deducted"},
                {"id": "R818-D07", "decision": "second-project regression NOT_RUN (no clean fixture)"}],
            "gates": GATES, "answers": answers}
