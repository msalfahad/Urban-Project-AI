"""R8.9 lab: owner actions (V6), engineering actions, decision register (recommendation, findings, gates, answers).

    python3 research/external_engine_lab/r8_9_registers.py <register_dir>

Reads the registers written by r8_9_qortuba.py and r8_9_p7757.py in the same directory.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
R88_OWNER = ROOT / "tests/r8_8/registers/OWNER_ACTION_REGISTER.json"
R88_ENG = ROOT / "tests/r8_8/registers/ENGINEERING_ACTION_REGISTER.json"
NEW_DXF = "df0e1d690285f5455b3b5acebe7e20eaee2d1c8aa3743b633a9fd257c6d6f315"
REGION = "RC:MODEL_SPACE:4267:540:1649"


def load(regdir, name):
    return json.loads((Path(regdir) / f"{name}.json").read_text())


def owner_actions(regdir):
    v5 = json.loads(R88_OWNER.read_text())
    keep = []
    for a in v5["actions"]:
        a = dict(a)
        if a["action_id"] == "CONFIRM_P7757_NATIVE_UNIT":
            a["note"] = ("R8.9: the second-family shadow ran without it (UNIT_UNRESOLVED certificate); evidence is "
                         "consistent with mm (INSUNITS 4, DIMLFAC 0.1) but is not confirmation. NOT asked now: no "
                         "P7757 quantity is in scope")
        keep.append(a)
    q = load(regdir, "QORTUBA_R8_9_STATUS")
    xref_rows = {r: v["state"] for r, v in q["rows"]["NEW_K2"].items()}
    new = [
        {"action_id": "CONFIRM_QORTUBA_NEW_ATTACHED_XREFS_OUTSIDE_PLAN", "project": "QORTUBA", "status": "OPEN",
         "needed_for_next_coding_round": False, "outstanding_request": True, "type": "OWNER_REVIEW",
         "question": "The new Qortuba file has two ATTACHED drawings whose content is not inside the file: 'block' "
                     "(..\\Autocad blocks\\block.dwg) and the facade-details drawing (Arabic name). Do they show "
                     "anything inside the selected SECOND FLOOR plan?",
         "choices": ["NO - they are not part of this plan", "YES - they draw something in this plan", "NOT SURE"],
         "why_the_source_cannot_decide": "an attached xref's content lives in another file; the DXF only holds the "
                                         "insert at (0, 0) - its content could lie anywhere",
         "affects": {"rows": ["Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14"], "now": xref_rows,
                     "if_NO": q["if_xrefs_confirmed_outside_the_plan"]["rows"]},
         "scope": {"source_revision": "QORTUBA_REV_NEW", "anchor": NEW_DXF, "region": REGION,
                   "plan": "PLAN_VARIANT_4_SELECTED"},
         "never": "an expected quantity"},
        {"action_id": "CONFIRM_QORTUBA_NEW_DIM_LINES_ARE_WALLS", "project": "QORTUBA", "status": "OPEN",
         "needed_for_next_coding_round": False, "outstanding_request": True, "type": "OWNER_REVIEW",
         "question": "In the new revision, four lines on the DIM (dimension) layer lie exactly where the old revision "
                     "drew the bathroom and bedroom walls next to the HALL (picture: 19_OWNER_REVIEW_DIM_WALLS.png). "
                     "Are they walls?",
         "choices": ["YES - they are walls (drawn on the wrong layer)", "NO - those walls were removed",
                     "NOT SURE"],
         "why_the_source_cannot_decide": "the layer says dimension; the geometry says wall (exact match with the old "
                                         "walls, 150 mm face pairs, connecting wall to wall, door 2044 still there); "
                                         "only the designer's intent decides",
         "affects": {"rows": ["Q-03", "Q-11", "Q-13"],
                     "if_YES_and_xrefs_NO": q["if_xrefs_confirmed_outside_the_plan"]["and_if_dim_lines_are_walls"]},
         "scope": {"source_revision": "QORTUBA_REV_NEW", "anchor": NEW_DXF, "parts": ["7116", "7117", "7118", "7119"]},
         "never": "an expected quantity"}]
    return {"SCHEMA": "URBAN_R8_9_OWNER_ACTION_REGISTER_V6", "supersedes": "URBAN_R8_8_OWNER_ACTION_REGISTER_V5",
            "rule": "ask only what the source cannot decide; one question each, YES / NO / NOT SURE, with its scope and "
                    "the rows it unblocks; never an expected quantity",
            "required_now": [], "owner_review_open": [a["action_id"] for a in new],
            "headline": "TWO OWNER REVIEWS (YES / NO) WOULD UNBLOCK THE NEW-REVISION ROWS; NO OWNER ACTION IS NEEDED "
                        "FOR THE NEXT CODING ROUND",
            "actions": keep + new}


def engineering_actions(regdir):
    v1 = json.loads(R88_ENG.read_text())
    done = {"TS01_SECOND_DRAWING_FAMILY_SHADOW": "DONE_R8_9 (P7757_R8_9_SHADOW)",
            "ADMIT_BLOCK_HOSTED_BUILDING_GEOMETRY": "DONE_R8_9 (building-assembly occurrence contexts, GR-17)",
            "SEMANTIC_SUBDIVISION_OF_CONNECTED_SPACES": "DONE_R8_9 (semantic_zones; subdivision only from authored "
                                                        "evidence)",
            "ROLE_EVIDENCE_FOR_UNKNOWN_GEOMETRY": "PARTLY_DONE_R8_9 (role authority, consequence check, source-scoped "
                                                  "claims; FIRNTUR / SF3 remain candidates)"}
    acts = []
    for a in v1["actions"]:
        a = dict(a)
        if a["action_id"] in done:
            a["status"] = done[a["action_id"]]
        acts.append(a)
    acts += [
        {"action_id": "DERIVE_DOOR_REACH_FROM_SYMBOL_GEOMETRY", "status": "PROPOSED",
         "what": "replace the fixed 0.25 x radius reach by the door symbol's own frame / jamb geometry; Qortuba doors "
                 "need 1/15 of the radius and no rejected hypothesis closes within a radius"},
        {"action_id": "P7757_SOURCE_SCOPED_ROLE_EVIDENCE", "status": "PROPOSED",
         "what": "P7757 layers W / D / TOI / ST / 5 / 1: source-scoped role evidence (network connectivity, paired "
                 "faces, door signatures inside the D### door blocks) leading to reviewed claims for that source only"},
        {"action_id": "P7757_INPUT_COMPLETENESS", "status": "OPEN",
         "what": "P7757 canonical input misses 6 part layers and 181 text values (METHOD_INPUT_INCOMPLETE even with a "
                 "unit): decode-level investigation"},
        {"action_id": "WALL_CORE_OBSTACLE_INTERIOR", "status": "PROPOSED",
         "what": "identify the two faces of one wall as one obstacle (source object / paired-face evidence) so its core "
                 "can be OBSTACLE_INTERIOR; columns are done"},
        {"action_id": "PLACEMENT_EVIDENCE_IN_THE_KERNELS", "status": "PROPOSED",
         "what": "move ACIS / spline placement evidence from the lab into the kernels as a recorded capability"},
        {"action_id": "OBTAIN_QORTUBA_XREF_FILES", "status": "ALTERNATIVE_TO_OWNER_REVIEW",
         "what": "if the project folder (..\\Autocad blocks\\) is ever available, read the two xrefs instead of asking"}]
    return {"SCHEMA": "URBAN_R8_9_ENGINEERING_ACTION_REGISTER_V2", "rule": "work Urban does itself", "actions": acts}


def decision_register(regdir):
    q = load(regdir, "QORTUBA_R8_9_STATUS")
    p = load(regdir, "P7757_R8_9_SHADOW")
    xc = load(regdir, "TOPOLOGY_CROSSCHECK_V2")
    door = load(regdir, "DOOR_CLOSURE_AUDIT")
    eff = load(regdir, "EFFECTIVE_LAYER_REGISTER")
    un = load(regdir, "UNREALISED_ENTITY_REGISTER")
    new_rows = q["rows"]["NEW_K2"]
    return {
        "SCHEMA": "URBAN_R8_9_DECISION_REGISTER_V1",
        "recommendation_before_coding": {
            "1_biggest_silent_risk": "role decisions by layer name alone in BOTH directions - R8.8 questioned admission "
                                     "(GR-05/06/07) but exclusion (GR-09 .. GR-16) is equally layer-only: the new "
                                     "revision's bath / bedroom walls are on the DIM layer and were silently excluded; "
                                     "only the three labels in one space revealed it. With one label it would have "
                                     "been a certified, silently wrong room",
            "2_role_vs_arithmetic": "YES, role authority - and source completeness (attached xrefs); polygon arithmetic "
                                    "is cross-checked. But the HALL + BED.ROOM + BATH space is a ROLE conflict, not a "
                                    "semantic-zone question",
            "3_three_objects": "YES; with one guard: a multi-label space must pass a separator-candidate search before "
                               "it is accepted as an open plan",
            "4_disagreements": ["§4 'independent evidence per wall line' would block nearly every drawing; grade edges "
                                "and check consequences instead", "the multi-label cases should not all be treated as "
                                "semantic: one of the two is a missing separator"],
            "5_what_differently": ["consequence check of layer-only exclusion (a diagnostic arrangement)",
                                   "network connectivity as role evidence (unconnected lines are candidates)",
                                   "text roles from structure (tag occurrences, same-source tag family)",
                                   "positive placement evidence for unrealised entities (ACIS / spline extents)"],
            "6_resolved_from_source": ["effective layer", "full-extent eps_n", "cross-check V2", "unrealised accounting "
                                       "(all 38 old-revision OFFICE NAME entities placed)", "stubs", "thresholds",
                                       "door-reach audit", "text roles (PAINTRY by tag family)", "P7757 to UNIT_UNRESOLVED"],
            "7_unavoidable_owner_input": ["are the two attached xrefs outside the plan?",
                                          "are the four DIM-layer lines walls?"],
            "8_not_mentioned": ["layer-only EXCLUSION (DIM walls)", "attached xrefs whose content is not in the file "
                                "(R8.8 skipped them silently)", "duplicate SF3 insert (double count for counted trades)",
                                "P7757: the generic lexicon admits almost nothing (W / D / 5 / 1 layers)"]},
        "decisions": [
            {"id": "R89-D01", "decision": "effective layer is a canonical record field (effective_layer + authority); "
                                          "role admission reads it; the R8.8 insert_layers argument is removed"},
            {"id": "R89-D02", "decision": "role authority stage: boundary grades, unconnected lines not admitted, "
                                          "consequence check of layer-only exclusion and of unknown geometry"},
            {"id": "R89-D03", "decision": "source-scoped layer role claims (revision id AND anchor hash; candidates never "
                                          "change a role; claims never edit geometry)"},
            {"id": "R89-D04", "decision": "building-assembly occurrences from positive evidence (GR-17); unknown "
                                          "occurrences fail closed"},
            {"id": "R89-D05", "decision": "unrealised entities excluded only on positive evidence; the R8.8 "
                                          "layer-peer disposition and its test are superseded"},
            {"id": "R89-D06", "decision": "text roles before labels; only ROOM_LABEL_ESTABLISHED names a space"},
            {"id": "R89-D07", "decision": "physical site / semantic zone / trade region are separate objects; "
                                          "subdivision only from authored SEMANTIC_BOUNDARY (GR-18) or a claim"},
            {"id": "R89-D08", "decision": "threshold sites kept; allocation TRADE_RULE_REQUIRED"},
            {"id": "R89-D09", "decision": "GEOS cross-check V2: all phases; PHASE_SENSITIVE_INCONCLUSIVE never reported "
                                          "as agreement; no buffer(0); the R8.8 any-phase tests are superseded"},
            {"id": "R89-D10", "decision": "eps_n from the full exact extent"},
            {"id": "R89-D11", "decision": "1 mm authored precision = ENGINE_METHOD_PARAMETER (Urban method rule approval "
                                          "recommended later, not now)"},
            {"id": "R89-D12", "decision": "geometry role policy V2 (effective layer, GR-17, GR-18); the frozen topology "
                                          "tolerance policy is unchanged (digest 263d2adf...)"}],
        "findings": [
            {"id": "F-R89-01", "finding": "the effective-layer gap is real (insert_layers never supplied; top level only) "
                                          "but latent in Qortuba (0 layer-0 children inside inserts); in P7757 it "
                                          f"decides {p['effective_layers']['layer0_children_inside_inserts']} parts"},
            {"id": "F-R89-02", "finding": "new Qortuba: DIM lines 7116 / 7117 / 7118 / 7119 lie on the faces of the old "
                                          "walls H467 / H465 / H817 / H513 (150 mm pairs); the layer-only exclusion "
                                          "merged BATH + BED.ROOM into the HALL space"},
            {"id": "F-R89-03", "finding": "new Qortuba carries two attached xrefs (block.dwg, facade details) whose "
                                          "content is not in the file; R8.8 skipped them silently - they now block the "
                                          "region (BLOCKED_SOURCE_COMPLETENESS)"},
            {"id": "F-R89-04", "finding": "the 37 + 1 OFFICE NAME entities (ACIS REGIONs + a spline) are placed by their "
                                          "own geometry in the title / logo strip, outside every bounded site, "
                                          "identically from the K1 decode and the new DXF"},
            {"id": "F-R89-05", "finding": "FIRNTUR: MB wardrobe joinery candidate (rectangle-with-diagonal, 600 mm deep); "
                                          "roof double lines unresolved; the same token hosts proven furniture in this "
                                          "source - a source-scoped candidate, never a lexicon entry"},
            {"id": "F-R89-06", "finding": "SF3 / PM: furniture candidate (3-seat sofa outline 2385 x 995 mm, same library "
                                          "as BED 3); two of three occurrences are exact duplicates - a double-count "
                                          "risk for any counted trade"},
            {"id": "F-R89-07", "finding": "M.B.ROOM + DRESS: one connected space with two zones; no authored subdivision "
                                          "(legitimate open zone)"},
            {"id": "F-R89-08", "finding": "door reach: Qortuba closures need 1/15 of the leaf radius; the 0.25 ratio "
                                          "decides nothing here (NEEDS_MORE_EVIDENCE)"},
            {"id": "F-R89-09", "finding": f"GEOS V2: all phases agree on every site (old K1 / K2 "
                                          f"{xc['runs']['OLD_K1']['counts']['ALL_PHASES_AGREE']}, new "
                                          f"{xc['runs']['NEW_K2']['counts']['ALL_PHASES_AGREE']}); the R8.8 any-phase "
                                          "rule was never needed on Qortuba"},
            {"id": "F-R89-10", "finding": "P7757: the generic exact-token lexicon admits ~5% of parts (layers W, D, 5, "
                                          "1, TOI, ST); doors are D### blocks on layer D - no door is proven; the role "
                                          "machinery fails closed, as it must"},
            {"id": "F-R89-11", "finding": "PAINTRY is a misspelled room name; it is established only through its tag "
                                          "family (TR-04), never through the vocabulary"},
            {"id": "F-R89-12", "finding": "the new revision leaves a 1.196 m gap between the H471 / H477 and H2296 / "
                                          "H2297 wall faces, and the jamb cap H2045 and H1316 float (not admitted)"}],
        "post_r8_8_changes": {"tolerance_numbers": "unchanged", "policy_digest": "263d2adf1d17... unchanged",
                              "old_revision_rows": q["old_revision_rows_regression"],
                              "superseded_tests": ["R8.8 inspired-risks layer-peer unrealised test (R89-D05)",
                                                   "R8.8 grid-phase / real-data cross-check assertions (R89-D09)"]},
        "gates": {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO", "PRODUCTION_MIGRATION": "NO",
                  "TS01": "SHADOW", "QS01": "LEGACY_RESEARCH_ONLY", "R9_RULES_AS_DATA": "NOT_STARTED",
                  "NEW_DWG_SOURCE_IDENTITY": "NOT_ESTABLISHED", "P7757_TS01_CERTIFICATE": p["ts01_certificate"]},
        "answers": {
            "1_effective_layer_problem_found": "YES: confirmed in code (admit() took insert_layers, TS01 never passed "
                                               "it, and only the top-level insert was read); latent in Qortuba, real in "
                                               "P7757",
            "2_effective_layer_canonical_nested_safe": "YES: canonical record field with authority, whole insert chain, "
                                                       "both routes (tests A-F)",
            "3_layer_name_sole_wall_authority": "NO longer alone: an admitted line must also join the boundary network "
                                                "(unconnected -> CANDIDATE, not admitted); exclusions answer to their "
                                                "consequence. A connected single line on a wall layer is still "
                                                "admitted (NETWORK grade) - stated, not hidden",
            "4_authority_paths": ["layer + type + context + network connectivity (NETWORK)", "derived opening closures "
                                  "(STRUCTURAL)", "building-assembly children (GR-17)", "reviewed source-scoped claim "
                                  "(STRUCTURAL)"],
            "5_firntur": "this source's furniture / joinery layer: MB wardrobe symbols (candidate); roof double lines "
                         "unresolved",
            "6_sf3_pm": "a furniture candidate (sofa) from the MY BLOCKS library; ROLE_UNRESOLVED",
            "7_established_or_unresolved": "both UNRESOLVED as authority (source-scoped candidates with evidence, not "
                                           "applied); neither changes a row",
            "8_block_hosted_plans": "YES when the occurrence is established as a building assembly from positive "
                                    "evidence; otherwise fail closed (tests)",
            "9_unrealised_cleared_by_absence": "NO (R89-D05)",
            "10_37_acis_regions_excluded": "YES, positively: their own ACIS geometry (vertices + B-spline control points "
                                           "through the body transform) lies in the title / logo strip, outside every "
                                           "bounded site",
            "11_arbitrary_notes_as_labels": "NO: only ROOM_LABEL_ESTABLISHED texts name a space; candidates and unknown "
                                            "texts raise semantic review",
            "12_physical_vs_semantic_separate": "YES: PHYSICAL_TOPOLOGICAL_SITE, SEMANTIC_ZONE_CANDIDATE, "
                                                "TRADE_MEASUREMENT_REGION with separate ids",
            "13_interpretations": {"HALL + BED.ROOM + BATH": q["multi_label_investigation"]["A_HALL_BED_BATH"]
                                   ["interpretation"],
                                   "M.B.ROOM + DRESS": q["multi_label_investigation"]["B_MB_ROOM_DRESS"]["interpretation"]},
            "14_subdivision_established": "NO: no authored finish / zone / threshold line exists in either space",
            "15_threshold_strip": "kept as its own THRESHOLD site; allocation TRADE_RULE_REQUIRED; not moved into the bath",
            "16_max_abs_coordinate": "YES: full exact extent (test)",
            "17_geos_phase_policy": "ALL_PHASES_AGREE / PHASE_SENSITIVE_INCONCLUSIVE / ALL_PHASES_DISAGREE / "
                                    "NOT_APPLICABLE_CURVE / CHECK_INPUT_INVALID; only all-disagree blocks; inconclusive "
                                    "is never reported as agreement. Qortuba: all phases agree before and after",
            "18_buffer0_removed": "YES",
            "19_jamb_ratio": door["verdict"],
            "20_authored_precision_class": "ENGINE_METHOD_PARAMETER; recommend later approval as an Urban method rule",
            "21_p7757_progress": "canonical input, effective layers, roles, occurrence contexts, text roles, unrealised "
                                 "accounting, door search, numeric checks and an uncertified eps_n arrangement - "
                                 "certificate UNIT_UNRESOLVED; input also incomplete (6 layers, 181 text values)",
            "22_p7757_unit_needed": "NOT NOW: only when P7757 quantities are in scope; even then role evidence for its "
                                    "W / D layers is the larger blocker",
            "23_new_rows_computable": [r for r, v in new_rows.items() if v["state"] == "COMPUTED_SHADOW"],
            "24_what_blocks": {r: v["state"] for r, v in new_rows.items()},
            "25_new_issue": ["layer-only exclusion of real walls (DIM)", "attached xrefs not in the file",
                             "duplicate SF3 insert", "P7757 lexicon failure"],
            "26_next_round": "R8.10: owner answers (xrefs, DIM walls) applied as source-scoped claims and re-run; "
                             "source-scoped role evidence for P7757 (W / D); door reach from symbol geometry; "
                             "wall-core obstacle identity - still no migration",
            "27_disagree_with_chatgpt": ["the HALL + BED.ROOM + BATH case is a role conflict, not semantic subdivision",
                                         "per-line independent evidence for every wall would block real drawings; "
                                         "grade + consequence instead",
                                         "the GEOS phase concern was right in principle but changed nothing on Qortuba"]},
        "recommendation": "stay in shadow; ask the owner the two YES / NO reviews when convenient; next round applies "
                          "them as source-scoped claims and builds source-scoped role evidence for P7757"}


def main(regdir):
    regdir = Path(regdir)
    regs = {"OWNER_ACTION_REGISTER": owner_actions(regdir), "ENGINEERING_ACTION_REGISTER": engineering_actions(regdir),
            "R8_9_DECISION_REGISTER": decision_register(regdir)}
    for k, v in regs.items():
        (regdir / f"{k}.json").write_text(json.dumps(v, indent=1, ensure_ascii=False, default=str) + "\n")
    print(sorted(regs))


if __name__ == "__main__":
    main(sys.argv[1])
