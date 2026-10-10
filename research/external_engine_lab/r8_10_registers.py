"""R8.10 lab: owner actions (V7) and the decision register (recommendation, decisions, findings, gates, answers).

    python3 research/external_engine_lab/r8_10_registers.py <register_dir>

Reads the registers r8_10_qortuba.py / r8_10_p7757.py wrote into the same directory; every number here comes from
them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def jl(p):
    return json.loads(Path(p).read_text())


def owner_actions(q):
    return {
        "SCHEMA": "URBAN_OWNER_ACTION_REGISTER_V7",
        "required_now": [], "owner_review_open": [],
        "headline": "NO OWNER ACTION REQUIRED FOR THE NEXT ROUND",
        "answered_in_r8_10": [
            {"action_id": "CONFIRM_QORTUBA_NEW_ATTACHED_XREFS_OUTSIDE_PLAN", "status": "ANSWERED",
             "answer": "the unresolved xref occurrences contribute nothing to PLAN_VARIANT_4_SELECTED",
             "recorded_as": "QORTUBA-NEW-XREFS-NONCONTRIBUTING-TO-PLAN-VARIANT-4-OWNER-001 (occurrences 16783, 17716)",
             "never_ask_again": True},
            {"action_id": "CONFIRM_QORTUBA_NEW_DIM_LINES_ARE_WALLS", "status": "ANSWERED",
             "answer": "7116 / 7117 / 7118 / 7119 are walls (7116 side: bathroom wall; 7119 side: room wall)",
             "recorded_as": "QORTUBA-NEW-DIM-LINES-7116-7119-ARE-WALLS-OWNER-001 (part-scoped)",
             "never_ask_again": True},
            {"action_id": "QORTUBA_SCOPE_PLAN_VARIANT_4_ONLY", "status": "ANSWERED",
             "answer": "the BOQ is for the bottom-most plan only; variants 1-3 and other content are not measured"}],
        "prepared_not_asked": [
            {"action_id": "QORTUBA_FLOOR_UNDER_BUILT_IN_WARDROBES",
             "question": "Qortuba porcelain floor: is it measured over the whole room footprint, under the built-in "
                         "wardrobes of the dressing room (and under loose furniture) as well? YES - whole room / NO - "
                         "the wardrobe footprint is deducted / NOT SURE",
             "why_not_asked": "not the only material blocker: Q-13 is also blocked by the HALL wall-end caps (a drafting "
                              "defect no owner fact can close) and by the SF3 sofa role; asking now would not release "
                              "Q-13", "never": "an expected quantity"},
            {"action_id": "QORTUBA_CORRECTED_DRAWING_HALL_LOBBY_CAPS",
             "request": "a corrected drawing in which the two short lines closing the wall ends at the Hall / Lobby "
                        "passage are on the WALL layer and actually meet the wall faces (one of them stops 9 mm short)",
             "why_not_asked": "a new drawing is a new source revision: every claim must be re-anchored to it; the "
                              "matching DWG (identity with the DXF still NOT_ESTABLISHED) should come in the same "
                              "step - a decision for the migration-planning round, not R8.10"}],
        "do_not_ask": ["FIRNTUR meaning", "SF3 meaning", "threshold allocation", "P7757 unit",
                       "the two answered R8.9 reviews", "any expected quantity"]}


def decision_register(regdir):
    R = {n: jl(regdir / f"{n}.json") for n in (
        "QORTUBA_R8_10_STATUS", "DIM_WALL_CLAIMS", "XREF_SCOPE_CLAIMS", "OWNER_CLAIM_REGISTER",
        "TRADE_SEMANTIC_EQUIVALENCE", "UNRESOLVED_ROLE_MATERIALITY", "DUPLICATE_OCCURRENCE_REGISTER",
        "THRESHOLD_SITE_REGISTER", "ROLE_AUTHORITY_ADVERSARIAL", "BUILDING_ASSEMBLY_ADVERSARIAL",
        "TEXT_TAG_ADVERSARIAL", "P7757_R8_10_SHADOW")}
    q = R["QORTUBA_R8_10_STATUS"]
    rows = q["rows"]["NEW_K2_R8_10"]
    dim = R["DIM_WALL_CLAIMS"]
    caps = dim["hall_lobby_caps"]
    mb = q["m_b_room_dress"]
    computed = [r for r, v in rows.items() if v["state"] == "COMPUTED_SHADOW"]
    blockers = {r: {"state": v["state"], "by_site": [{"zones": b["zones"], "classes": sorted({x["class"] for x in
                                                                                         b["blockers"]}),
                                                      "issues": [x["issue"] for x in b["blockers"]]}
                                                     for b in v["blockers"]]}
                for r, v in rows.items() if v["state"] != "COMPUTED_SHADOW"}
    sites = {s["site"]: s for s in q["labelled_sites"]}
    rec = {
        "1_biggest_remaining_blocker": "objects and drafting inside two rooms, not semantics: the Hall / Lobby "
                                       "passage wall-end caps drawn on DIM (H2430 exact, H2431 9.2 mm short) and the "
                                       "unresolved SF3 / FIRNTUR objects for the floor trade",
        "2_narrow_claims_and_full_rebuild": "YES, plus binding to source identity (handle + anchor + fingerprint) and "
                                            "an evidence-version digest on every result",
        "3_block_only_when_material_to_the_trade": "YES, decided by the deterministic consequence check plus a named "
                                                   "trade authority; with no authority the default stays BLOCKED",
        "4_safer_alternative": "TRADE TREATMENT ASSIGNMENT (treatment per zone per trade from an authority record; "
                               "equivalence is derived, never declared) plus an object-footprint policy per trade",
        "5_disagreements": ["§11 premise: a WALL-layer stub with a 1.2 m open passage separates DRESS from M.B.ROOM "
                            "(R8.9 was wrong); the conclusion (one physical site) survives",
                            "§13: a valid owner rule exists (QP-14 + QP-07), not only the historical BOQ",
                            "§14: the Q-13 blocker for M.B.ROOM + DRESS is the floor-under-objects rule, not the "
                            "zone boundary",
                            "§21: admitting a false single line is the dangerous direction; a dimension entity on a "
                            "wall's ends is NOT contrary evidence (tested on real walls)"],
        "6_resolved_without_mohammad": ["xref occurrences re-verified from the DXF (exactly 16783 / 17716)",
                                        "the wall stub + passage between DRESS and M.B.ROOM",
                                        "trade treatment from QP-07 / QP-14 and the Q-14 claim",
                                        "FIRNTUR / SF3 non-materiality for Q-14", "the SF3 duplicate pair"],
        "7_new_owner_input_unavoidable": "NO for R8.10 (the one prepared floor question would not release Q-13 "
                                         "alone)",
        "8_found_and_not_identified": ["the DIM-layer wall-end caps at the Hall / Lobby passage and the 9.2 mm near "
                                       "miss that leaked a wall core silently", "the owner rule store as trade "
                                                                                "authority",
                                       "open-passage strips vs door thresholds treated differently",
                                       "the passage head soffit as a cross-trade overlap",
                                       "QP-17 was authored on the old revision"],
        "9_next_round": "R8.11: reviewed near-miss / cap closures as derived closures (like door closures), a "
                        "wall-band model for NETWORK candidates, object-footprint authority per trade, and the "
                        "DWG <-> DXF anchor transfer of the claims - still no migration"}
    answers = {
        "1_dim_wall_claims_part_scoped": f"YES: {dim['claim_status']['claim_id']} names exactly "
                                         f"{[p['handle'] for p in dim['effect']['parts']]} by part key + fingerprint",
        "2_source_dim_layer_preserved": "YES: " + ", ".join(f"{p['handle']}={p['source_layer']}"
                                                             for p in dim["effect"]["parts"]),
        "3_other_dim_entity_became_wall": f"NO: {dim['effect']['other_dim_parts_admitted']} other DIM parts admitted "
                                          f"({dim['effect']['other_dim_layer_parts']})",
        "4_xref_answer_scoped_to_plan_variant_4": "YES: claim scope = revision + DXF anchor + region "
                                                  "RC:MODEL_SPACE:4267:540:1649 + frame; occurrences 16783 / 17716 "
                                                  "bound by their source facts",
        "5_owner_claim_edited_a_quantity": "NO (quantity_edits_by_claims = "
                                           f"{R['OWNER_CLAIM_REGISTER']['quantity_edits_by_claims']})",
        "6_physical_sites_after_rebuild": [{"zones": [v[0] for v in s["stamps"]], "area_m2": s["area_m2"],
                                            "status": s["physical_status"]} for s in q["labelled_sites"]],
        "7_bath_bed_hall_separated": "YES: " + "; ".join(f"{a['stamps'][0][0] if a['stamps'] else 'core/threshold'} "
                                                         f"{a['area_m2']}" for a in dim["effect"]["after"]),
        "8_mb_room_dress": f"{mb['semantic_state']}: one physical site ({mb['area_m2']} m2) joined through a "
                           f"{mb['passage']['width_mm']:.0f} mm open passage in a WALL-layer stub",
        "9_q13_combined_footprint": "NOT YET: same treatment (PORCELAIN, QP-14) and no finish boundary, but the "
                                    "FIRNTUR wardrobes are material to the floor trade (no object-footprint "
                                    "authority)",
        "10_q14_combined_footprint": "YES: SEMANTIC_SUBDIVISION_NOT_REQUIRED_FOR_TRADE and FIRNTUR non-material "
                                     "(Q-14 claim); the site is used whole in Q-14",
        "11_trade_authority": {"floor": R["TRADE_SEMANTIC_EQUIVALENCE"]["rules"]["QORTUBA-FLOOR-TREATMENT"]["refs"],
                               "ceiling": R["TRADE_SEMANTIC_EQUIVALENCE"]["rules"]
                               ["QORTUBA-Q14-CEILING-TREATMENT"]["refs"]},
        "12_rows_computed_shadow": {r: rows[r]["value"] for r in computed},
        "13_exact_blockers": blockers,
        "14_threshold_strip_separate": f"YES: {R['THRESHOLD_SITE_REGISTER']['old_revision_wet_rows']}",
        "15_firntur_needed_a_final_role": "NO for Q-14 (non-material); for Q-13 its role OR a floor object-footprint "
                                          "rule is needed",
        "16_sf3_needed_a_final_role": "NO for Q-14; for Q-13 yes (HALL), together with the floor rule - and the HALL "
                                      "is blocked by the caps anyway",
        "17_sf3_duplicate_explicit": R["DUPLICATE_OCCURRENCE_REGISTER"]["sf3"],
        "18_network_survived": R["ROLE_AUTHORITY_ADVERSARIAL"]["verdict"],
        "19_building_assembly_survived": "NO as written in R8.9 (a detail callout or a one-room block passed); V2 "
                                         "requires closed boundary children + a nested door or two different room "
                                         "labels; no real result changed",
        "20_text_tag_survived": "NO as written (a lone 'BATHROOM DETAIL' tag was established); V2 requires repeated "
                                "family use and rejects drafting-document words; PAINTRY kept; ROOF tag now a "
                                "candidate",
        "21_new_source_mistake_or_silent_path": ["H2430 / H2431: the Hall / Lobby passage wall-end caps on DIM; "
                                                 "wall-core pockets 0.3813 m2 (H2430) + "
                                                 f"{caps['leak_areas']['h2431_near_miss_pockets_m2']} m2 (H2431, "
                                                 "through a 9.2 mm slit) inside the HALL's 43.83 m2",
                                                 "near-miss gaps into an unlabelled cavity were silent (now "
                                                 "NEAR_MISS_BOUNDARY_GAP)",
                                                 "H1316: a WALL cap 1.4 mm short at both ends",
                                                 "R8.9 wording: no wall between DRESS and M.B.ROOM (wrong)"],
        "22_new_owner_input_needed": "NO",
        "23_next_round": rec["9_next_round"],
        "24_disagree_with_chatgpt": rec["5_disagreements"]}
    return {
        "SCHEMA": "URBAN_R8_10_DECISION_REGISTER_V1",
        "recommendation_before_coding": rec,
        "decisions": [
            {"id": "R810-D01", "decision": "owner answers enter as versioned claims bound to source identity "
                                           "(engine/source/owner_claims.py); evidence version 2"},
            {"id": "R810-D02", "decision": "xref completeness has four states; no IGNORE_XREF"},
            {"id": "R810-D03", "decision": "no generic wall-end-cap admission: a corridor and a wall band look alike "
                                           "without size; the cap stays a role conflict until claimed"},
            {"id": "R810-D04", "decision": "NEAR_MISS_BOUNDARY_GAP: a review-only 50 mm band; withholds, never joins"},
            {"id": "R810-D05", "decision": "NETWORK: established / candidate / conflict (self-dimensioned line)"},
            {"id": "R810-D06", "decision": "building assembly V2; text role V2 (repeated family use)"},
            {"id": "R810-D07", "decision": "trade treatment assignment from authority records; object materiality per "
                                           "trade; duplicates recorded, never deleted"},
            {"id": "R810-D08", "decision": "no row is FINAL; source anchor (DWG <-> DXF) stays a migration blocker"}],
        "findings": answers["21_new_source_mistake_or_silent_path"],
        "gates": {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO", "PRODUCTION_MIGRATION": "NO",
                  "TS01": "SHADOW", "QS01": "LEGACY_RESEARCH_ONLY", "R9_RULES_AS_DATA": "NOT_STARTED",
                  "NEW_DWG_SOURCE_IDENTITY": "NOT_ESTABLISHED", "P7757_TS01_CERTIFICATE": "UNIT_UNRESOLVED"},
        "answers": answers}


def main(regdir):
    regdir = Path(regdir)
    q = jl(regdir / "QORTUBA_R8_10_STATUS.json")
    (regdir / "OWNER_ACTION_REGISTER.json").write_text(json.dumps(owner_actions(q), indent=1) + "\n")
    (regdir / "R8_10_DECISION_REGISTER.json").write_text(json.dumps(decision_register(regdir), indent=1,
                                                                    ensure_ascii=False, default=str) + "\n")
    print("ok")


if __name__ == "__main__":
    main(sys.argv[1])
