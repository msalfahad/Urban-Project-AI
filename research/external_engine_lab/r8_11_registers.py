"""R8.11 lab: owner actions (V8), engineering actions, and the decision register (recommendation, decisions,
findings, gates, answers 1-30).

    python3 research/external_engine_lab/r8_11_registers.py <register_dir>

Reads the registers r8_11_qortuba.py wrote into the same directory; every number here comes from them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def jl(p):
    return json.loads(Path(p).read_text())


def owner_actions(q13):
    return {
        "SCHEMA": "URBAN_OWNER_ACTION_REGISTER_V8", "required_now": [], "owner_review_open": [],
        "headline": "NO OWNER ACTION REQUIRED.",
        "prepared_not_asked": [
            {"action_id": "QORTUBA_FLOOR_UNDER_BUILT_IN_WARDROBES",
             "question": "Qortuba porcelain floor: is it laid over the whole room, under the built-in wardrobes of "
                         "the dressing room and under loose furniture as well? YES - whole room / NO - the wardrobe "
                         "footprint is deducted / NOT SURE",
             "why_not_asked": "the sole-blocker test fails: Q-13 is also blocked by " +
                              ", ".join(q13["sole_blocker_test"]["other_blockers"]) +
                              " - an answer now would not release Q-13", "never": "an expected quantity"},
            {"action_id": "QORTUBA_CORRECTED_DRAWING_HALL_LOBBY_CAPS",
             "request": "a corrected drawing with the Hall / Lobby wall-end lines on the WALL layer meeting the faces",
             "why_not_asked": "a new drawing is a new source revision (every claim re-anchored); the engine route "
                              "(E-R8.12-01) is tried first"}],
        "do_not_ask": ["7116-7119", "the selected plan", "the units", "the two xrefs", "the Q-14 ceiling condition",
                       "FIRNTUR / SF3 meaning", "threshold or passage allocation", "any expected quantity"]}


def engineering_actions():
    return {"SCHEMA": "URBAN_ENGINEERING_ACTION_REGISTER_R8_11_V1", "actions": [
        {"id": "E-R8.12-01", "priority": 1, "title": "fragment-aware wall bands",
         "what": "mutual nearest over the OVERLAP (not the whole face) and collinear face fragments treated as one face "
                 "in the closure safety test; synthetic tests first (fragmented faces, T-junction fragments, a column "
                 "inside one fragment's strip), freeze, THEN a blind Qortuba re-run",
         "why": "H2430's band is not established only because the lower face is drawn as H470 + H471",
         "never": "tuning to the 0.3813 m2 core or to a Q-14 value"},
        {"id": "E-R8.12-02", "priority": 2, "title": "source anchor",
         "what": "establish (or refuse) DWG e4babbc2... <-> DXF df0e1d69... identity; re-anchor claims only through a "
                 "reviewed transfer record"},
        {"id": "E-R8.12-03", "priority": 3, "title": "reviewed closure / correction workflow",
         "what": "REVIEWED and AUTHORISED_FOR_RELEASE as signed records over a TopologyClosure; SOURCE_CORRECTION "
                 "claims as a separate kind (never merged with closures)"},
        {"id": "E-R8.12-04", "priority": 4, "title": "trade-layer claims in the engine manifest",
         "what": "the Q-14 claim, the space-class rule and footprint policies act in the lab trade layer; R8.11 binds "
                 "them per row (row_input_digest); move the row manifest into engine/source"},
        {"id": "E-R8.12-05", "priority": 5, "title": "passage vs open room side",
         "what": "a strip between a band end and a perpendicular face 3.45 m away is recorded like a 1.2 m passage "
                 "(no size rule, by design); a structural rule (both jambs belong to the same wall line, or the strip "
                 "separates label zones) is needed before any allocation"},
        {"id": "E-R8.12-06", "priority": 6, "title": "reveal / soffit allocation",
         "what": "jamb faces and a soffit (only with a head) are opening surfaces for wall-treatment trades; never "
                 "also room wall perimeter or ceiling area"},
        {"id": "E-R8.12-07", "priority": 7, "title": "floor object-footprint authority",
         "what": "when it is the sole Q-13 blocker, ask the one prepared owner question; record the answer as a "
                 "TradeObjectFootprintPolicy (FLOOR_FINISH), never as a quantity"}]}


def decision_register(regdir):
    R = {n: jl(regdir / f"{n}.json") for n in (
        "QORTUBA_R8_11_STATUS", "WALL_BAND_REGISTER", "TOPOLOGY_CLOSURE_REGISTER", "NEAR_MISS_REGISTER",
        "OPEN_PASSAGE_SITE_REGISTER", "THRESHOLD_SITE_REGISTER", "OBJECT_FOOTPRINT_POLICY", "SEMANTIC_CLASS_REGISTER",
        "QTO_RUN_MANIFEST", "Q13_STATUS", "Q14_STATUS")}
    q = R["QORTUBA_R8_11_STATUS"]
    rows = q["rows"]["NEW_K2_R8_11"]
    caps = R["WALL_BAND_REGISTER"]["cap_analysis"]
    leak = R["TOPOLOGY_CLOSURE_REGISTER"]["leak"]
    applied = R["TOPOLOGY_CLOSURE_REGISTER"]["applied"]["NEW_K2"]
    tc = next(c for c in R["TOPOLOGY_CLOSURE_REGISTER"]["NEW_K2"] if c["closure_id"] in applied)
    man = R["QTO_RUN_MANIFEST"]["NEW_K2"]
    q13, q14 = R["Q13_STATUS"], R["Q14_STATUS"]
    pas = R["OPEN_PASSAGE_SITE_REGISTER"]
    computed = {r: v["value"] for r, v in rows.items() if v["state"] == "COMPUTED_SHADOW"}
    rec = {
        "1_most_important_blocker": "the HALL wall core behind H2430 (0.3813 m2): the frozen band rule cannot pair a "
                                    "face drawn in two fragments; Q-14 is blocked by that alone",
        "2_h2430_h2431_by_evidence_backed_topology": "YES - as a derived zero-material closure on an ESTABLISHED band "
                                                     "end, its geometry taken from the FACE end points (never from the "
                                                     "cap line, never a moved end point)",
        "3_wall_band_model_right": "YES, as topology-obstacle geometry from structure only; it must survive fragmented "
                                   "faces (not yet: E-R8.12-01)",
        "4_closure_separate_from_correction": "YES: A source geometry / B topology closure / C source correction claim",
        "5_safer_alternative": "the closure's AUTHORISED_FOR_SHADOW level requires drawn-cap corroboration AND a "
                               "consequence safety test (label partition unchanged, only pure band interior removed, "
                               "area balance) - stronger than any distance rule",
        "6_disagreements": ["the target state 'Q-14 COMPUTED_SHADOW' is not reached and must not be forced: the frozen "
                            "rule fails on H2430 for a structural reason",
                            "the closure must not follow H2431's coordinates (9.2 mm short); it follows the faces",
                            "an OPEN_PASSAGE_SITE is a record inside the adjacent site, not a separate TS01 site - a "
                            "separate site would close the passage topologically",
                            "the code commit is provenance, not part of RUN_INPUT_DIGEST (CODE_BOUND_DIGEST)",
                            "the space-class rule comes from the existing owner rule store (US-01, QP-07, QP-14); "
                            "no new rule is invented"],
        "7_resolved_from_source_code": ["H2431 (closure)", "H1316 (window jamb, not a cap)",
                                        "M.B.ROOM / DRESS passage 1.200 m", "the semantic class chain",
                                        "the ceiling footprint policy from the existing Q-14 claim",
                                        "the false wall-core passages (amendment A1)"],
        "8_owner_input_necessary": "NO",
        "9_new_issue": ["face fragmentation defeats mutual-nearest pairing (H2430)",
                        "T-junction / merged-core band ends produced false 150-200 mm passages through wall cores "
                        "(fixed: A1)", "proven object footprints are implicitly inside every floor area",
                        "trade-layer claims are outside the TS01 run manifest (bound per row in R8.11)"],
        "10_r8_12": "fragment-aware wall bands frozen with synthetic tests then a blind re-run (E-R8.12-01); the "
                    "DWG <-> DXF anchor (E-R8.12-02); reviewed closure records (E-R8.12-03); still no migration"}
    answers = {
        "1_what_is_a_wall_band": "two admitted TOPOLOGY_BOUNDARY faces that are parallel within eps_r over their "
                                 "overlap, overlap and separation > eps_r, elongated (overlap > separation), mutual "
                                 "nearest on one side only, with an empty strip (no label, crossing boundary or arc), "
                                 "neither self-dimensioned: TOPOLOGY_OBSTACLE_GEOMETRY, not masonry",
        "2_identity_source_derived": "YES: 'WB-' + digest(revision, region, sorted face source ids); identical across "
                                     "shuffled source order (" +
                                     str(R["QTO_RUN_MANIFEST"]["determinism_shuffled_source_order"]["same_bands"]) + ")",
        "3_h2430_h2431_established_caps": {"H2431": caps["2431"]["classification"],
                                           "H2430": caps["2430"]["classification"],
                                           "H1316": caps["1316"]["classification"]},
        "4_evidence": {"H2431": f"band {caps['2431']['band_id']} (faces {caps['2431']['faces']}, "
                                f"{caps['2431']['band_width_mm']} mm), aligned free end; the DIM line lies across "
                                f"the end, {caps['2431']['gap_to_face_ends_mm']} mm from the face end points",
                       "H2430": caps["2430"]["pairing"]["finding"],
                       "H1316": caps["1316"]["reason"]},
        "5_h2431_closure": f"YES: {tc['closure_id']} {tc['release']}",
        "6_closure_geometry": f"{tc['geometry']} - the start points of faces "
                              f"{caps['2431']['faces']} (source coordinates of the faces)",
        "7_source_geometry_altered": "NO",
        "8_wall_material_added": f"NO (physical_material={tc['physical_material']}, affects_wall_quantity="
                                 f"{tc['affects_wall_quantity']}, affects_finish_quantity="
                                 f"{tc['affects_finish_quantity']})",
        "9_the_0_6493_leak": f"separated as a pure band interior ({tc['safety']['separated_pieces']}); HALL "
                             f"{leak['hall_area_r8_10_m2']} -> {leak['hall_area_r8_11_m2']} m2",
        "10_label_changed_sides": "NO (label_partition_unchanged=" +
                                  str(tc["safety"]["label_partition_unchanged"]) + ")",
        "11_h1316": f"{caps['1316']['classification']}: glazing {caps['1316']['glazing_ending_on_it']} ends on it; no "
                    "closure; its near-miss lies in an unlabelled window-strip site no row uses",
        "12_50mm_band_review_only": "YES: it grades caps and flags gaps; it never joins anything",
        "13_q14_computed_shadow": f"NO: {q14['state']}",
        "14_q14_blocker": q14["blockers"],
        "15_q13_computed_shadow": f"NO: {q13['state']}",
        "16_q13_blockers": q13["blockers"],
        "17_wardrobe_floor_sole_owner_fact": "NO: " + ", ".join(q13["sole_blocker_test"]["other_blockers"]),
        "18_sf3_floor": "ROLE_UNRESOLVED and material to FLOOR_FINISH (no footprint authority): blocks the HALL for "
                        "Q-13; non-material to the ceiling (Q-14 policy)",
        "19_firntur_floor": "ROLE_UNRESOLVED and material to FLOOR_FINISH: blocks M.B.ROOM + DRESS for Q-13; "
                            "non-material to the ceiling",
        "20_open_passage_explicit": f"YES: {len(pas['NEW_K2'])} OPEN_PASSAGE_SITE records (new), {len(pas['OLD_K1'])} "
                                    "(old), each with width, thickness, polygon, jamb faces, head condition, adjacent "
                                    "sites and allocation",
        "21_vs_door_threshold": R["THRESHOLD_SITE_REGISTER"]["distinction"],
        "22_reveal_soffit_provenance": "YES: jamb faces per passage, soffit only if a head exists (source: "
                                       "NOT_ESTABLISHED), double-count guard recorded; QP-18 / QP-19 corroboration only",
        "23_raw_label_strings": "NO for the R8.11 path: label -> class (" + R["SEMANTIC_CLASS_REGISTER"]["rule"]
                                ["rule_id"] + ") -> treatment; 'Bath' / 'BATH ' map to nothing",
        "24_run_input_digest": ["canonical input digest", "revision + anchor sha256", "region", "frame",
                                "unit claim + scale", "claims offered / applied / rejected (with outcomes)",
                                "evidence version", "every policy id + digest", "method + contract version",
                                "closure policy", "decoder route", "installed kernel versions"],
        "25_offered_and_applied": f"YES: offered {len(man['claims_offered'])}, applied {len(man['claims_applied'])}, "
                                  f"rejected {len(man['claims_rejected'])} (old revision: the new-revision claims "
                                  "are offered and rejected as SOURCE_SCOPE_MISMATCH)",
        "26_policy_digests": f"YES: {sorted(man['policies'])}",
        "27_dwg_unanchored": "YES: DWG e4babbc2... identity with DXF df0e1d69... NOT_ESTABLISHED",
        "28_new_silent_error_path": rec["9_new_issue"],
        "29_next_round": rec["10_r8_12"],
        "30_disagree_with_chatgpt": rec["6_disagreements"]}
    return {
        "SCHEMA": "URBAN_R8_11_DECISION_REGISTER_V1", "recommendation_before_coding": rec,
        "order": ["wall-band, cap, near-miss and closure rules frozen with 24 synthetic tests: commit 5895981",
                  "first Qortuba run (rules as frozen): " + json.dumps(R["WALL_BAND_REGISTER"]["frozen_v1_first_run"]
                                                                      ["NEW_K2"]["rows"]),
                  "amendment A1 (independent source defect: false wall-core passages), its own tests, commit",
                  "re-run: authorised closures and row values unchanged"],
        "decisions": [
            {"id": "R811-D01", "decision": "wall bands = topology-obstacle geometry from structure only"},
            {"id": "R811-D02", "decision": "zero-material TopologyClosure from face end points; release levels; "
                                           "AUTHORISED_FOR_SHADOW needs cap corroboration + the safety test"},
            {"id": "R811-D03", "decision": "amendment A1: RECEIVING_FACE_JUNCTION (removes candidates only)"},
            {"id": "R811-D04", "decision": "H2430 stays UNRESOLVED; fragment-aware pairing deferred to R8.12 "
                                           "(anti-calibration)"},
            {"id": "R811-D05", "decision": "OPEN_PASSAGE_SITE records, NOT_ALLOCATED; thresholds stay TS01 sites"},
            {"id": "R811-D06", "decision": "semantic class authority + object-footprint policies; implicit inclusion "
                                           "is a release blocker"},
            {"id": "R811-D07", "decision": "QTO run manifest; RUN_INPUT_DIGEST without the commit; row_input_digest "
                                           "for trade-layer authority"},
            {"id": "R811-D08", "decision": "no owner question (sole-blocker test fails); no row FINAL"}],
        "rows": {r: (v["state"], v["value"]) for r, v in rows.items()}, "computed_shadow": computed,
        "findings": rec["9_new_issue"],
        "gates": {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO", "PRODUCTION_MIGRATION": "NO",
                  "TS01": "SHADOW", "R9_RULES_AS_DATA": "NOT_STARTED", "NEW_DWG_SOURCE_IDENTITY": "NOT_ESTABLISHED"},
        "answers": answers}


def main(regdir):
    regdir = Path(regdir)
    q13 = jl(regdir / "Q13_STATUS.json")
    for name, obj in (("OWNER_ACTION_REGISTER", owner_actions(q13)), ("ENGINEERING_ACTION_REGISTER",
                                                                       engineering_actions()),
                      ("R8_11_DECISION_REGISTER", decision_register(regdir))):
        (regdir / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str) + "\n")
    print("ok")


if __name__ == "__main__":
    main(sys.argv[1])
