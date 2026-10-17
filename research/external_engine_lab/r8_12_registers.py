"""R8.12 lab: owner actions (V9), engineering actions, decision register (recommendation first, answers 1-29).

    python3 research/external_engine_lab/r8_12_registers.py <register_dir>

Every number comes from the registers r8_12_qortuba.py wrote into the same directory.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def jl(p):
    return json.loads(Path(p).read_text())


QUESTION = ("Qortuba porcelain floor: is it laid over the whole room, including under the built-in wardrobes in the "
            "dressing room and under loose furniture? YES - whole room / NO - the wardrobe footprint is left out / "
            "NOT SURE")


def owner_actions(q13):
    sole = q13["sole_blocker_test"]["answer"] == "YES"
    return {
        "SCHEMA": "URBAN_OWNER_ACTION_REGISTER_V9",
        "required_now": [{"action_id": "QORTUBA_FLOOR_UNDER_BUILT_IN_WARDROBES", "question": QUESTION,
                          "why_now": "the sole-blocker counterfactual: with YES every remaining Q-13 blocker clears "
                                     f"({q13['sole_blocker_test']['counterfactual']['YES_WHOLE_ROOM']['state']}); "
                                     "with NO Q-13 stays blocked until the wardrobe footprint is measured",
                          "records_as": "a FLOOR_FINISH TradeObjectFootprintPolicy (never a quantity)"}] if sole else [],
        "headline": "ONE OWNER QUESTION" if sole else "NO OWNER ACTION REQUIRED.",
        "do_not_ask": ["H2430 / H2431 physical construction", "the Hall / Lobby passage", "the passage width",
                       "the 2.20 m head", "7116-7119", "the Qortuba unit", "the selected plan", "the xref scope",
                       "any expected quantity"]}


def engineering_actions():
    return {"SCHEMA": "URBAN_ENGINEERING_ACTION_REGISTER_R8_12_V1", "actions": [
        {"id": "E-R8.13-01", "title": "V3-D1 chain-id collision", "priority": 1,
         "what": "parallel sides of ONE closed polyline with the same extent get the same chain id (H2060 / H2061): add "
                 "the supporting-line offset or the sub-part set to the chain id; version bump; synthetic test first",
         "impact_now": "only the already-ambiguous H2060 / H2061 rectangles; no closure, no row"},
        {"id": "E-R8.13-02", "title": "V3-D2 elongation on the local run", "priority": 2,
         "what": "test elongation on the contiguous LOCAL RUN (spans + overlaps + nodes), not the raw chain overlap: "
                 "removes the 1.80 m pseudo-band (574 / 584, 150 mm local run) and its false 6.0 m passage",
         "impact_now": "outside the apartment; no closure, no row"},
        {"id": "E-R8.13-03", "title": "source anchor", "priority": 1,
         "what": "DWG e4babbc2... <-> DXF df0e1d69... identity: the release blocker on every new-revision row"},
        {"id": "E-R8.13-04", "title": "REVIEWED closure release level as a signed record", "priority": 3},
        {"id": "E-R8.13-05", "title": "closure-id rounding into the closure policy record (version bump)",
         "priority": 4},
        {"id": "E-R8.13-06", "title": "owner physical facts + row / release digests into the engine row manifest",
         "priority": 3, "what": "the generic model exists (engine/source/owner_facts.py, run_manifest digest "
                                "layers); the row computation itself is still lab code"},
        {"id": "E-R8.13-07", "title": "passage soffit vs ceiling allocation rule", "priority": 5}]}


def decision_register(regdir):
    R = {n: jl(regdir / f"{n}.json") for n in (
        "BLIND_QORTUBA_RESULT", "R8_12_FRAGMENT_BAND_FREEZE", "TOPOLOGY_CLOSURE_REGISTER", "OWNER_FACT_COMPARISON",
        "Q14_STATUS", "Q13_STATUS", "DIGEST_HIERARCHY", "POLICY_PROVENANCE_AUDIT", "FACE_CHAIN_REGISTER",
        "WALL_BAND_ASSEMBLY_REGISTER", "QORTUBA_R8_12_STATUS", "FRAGMENT_FACE_POLICY")}
    rec = jl(ROOT / "research/external_engine_lab/r8_12_recommendation.json")
    B = R["BLIND_QORTUBA_RESULT"]["NEW_K2"]
    w = next(b for b in B["watched_bands"] if "2430" in str(b["ends"]))
    e = next(b for b in B["watched_bands"] if "2431" in str(b["ends"]))
    c30 = next(c for c in B["closures"] if "2430" in c["evidence"])
    c31 = next(c for c in B["closures"] if "2431" in c["evidence"])
    q14, q13 = R["Q14_STATUS"], R["Q13_STATUS"]
    S = R["QORTUBA_R8_12_STATUS"]
    op = S["owner_passage"]
    oc = R["OWNER_FACT_COMPARISON"]
    d = R["DIGEST_HIERARCHY"]
    answers = {
        "1_model": "C - FACE CHAINS (strict numeric contiguity, typed nodes) + LOCAL BAND SPANS (local mutual nearest "
                   "per elementary interval) + WALL-BAND ASSEMBLIES; crossings subdivide a strip",
        "2_safer_than_collinear_merging": "a chain joins only touching fragments (eps_n, same occurrence, no opening at "
                                          "the joint); pairing never needs a chain to bridge anything; a gap of any "
                                          "size stays a gap; every span keeps exact source intervals",
        "3_openings_not_merged": "gap -> no join; glazing / opening closure at a touching joint -> OPENING_BREAK; the "
                                 "50 mm review band is never continuity (tests B, C, D, opening break)",
        "4_branches_t_junctions": "BRANCH_NODE / CROSSING_NODE on the chain (the face continues); a crossing wall's "
                                  "core is a CROSSING_WALL_NODE interval of the strip",
        "5_one_face_many_fragments": "YES: local pairing per elementary interval (test: one face against two "
                                     "opening-broken chains -> two bands)",
        "6_span_identity": "YES: revision + region + source ENTITIES + extent along the canonical direction (no "
                           "ordinals, no ranks)",
        "7_reordering": f"NO change: synthetic shuffles and the Qortuba shuffles ({S['determinism']})",
        "8_column_718": "YES: only [" + ", ".join(f"{iv['s'][0]:.2f}-{iv['s'][1]:.2f}" for iv in w["intervals"]
                                                   if iv["class"] == "OBSTACLE_OVERLAP") +
                        "] is OBSTACLE_OVERLAP by H718; the spans either side stay valid",
        "9_blind_h2430": {"band": w["band_id"], "faces": w["faces"], "intervals": [(iv["class"], iv["s"]) for iv in
                                                                                    w["intervals"]],
                          "ends": [(x["kind"], x["caps"]) for x in w["ends"]],
                          "closure": {k: c30[k] for k in ("closure_id", "release", "geometry", "material")},
                          "separated": c30["safety"]["separated_pieces"]},
        "10_owner_fact_in_blind_test": "NO (" + json.dumps(R["BLIND_QORTUBA_RESULT"]["blind"]) + ")",
        "11_owner_fact_agrees": f"YES: {oc['matrix_states']}",
        "12_fallback_role_claim": "NOT REQUIRED (the engine established H2430 itself)",
        "13_west_core_0_3813": f"separated by {c30['closure_id']} (zero material, pure band interior "
                               f"{c30['safety']['separated_pieces'][0]['area_m2']} m2); HALL {S['hall']['r8_11_m2']} -> "
                               f"{S['hall']['r8_12_m2']} m2",
        "14_h2431": f"{c31['closure_id']} {c31['release']}, geometry {c31['geometry']} (face end points; same as R8.11: "
                    f"{R['TOPOLOGY_CLOSURE_REGISTER']['h2431_regression']['same_geometry']}), "
                    f"{c31['safety']['separated_pieces'][0]['area_m2']} m2",
        "15_h1316": f"NOT_WALL_CAP; closures touching it: {R['TOPOLOGY_CLOSURE_REGISTER']['h1316_control']['closures_with_1316']}",
        "16_passage_open": f"YES: {op['engine_detection']}; nothing crosses it",
        "17_passage_width": f"{op['engine_width_mm']} mm engine-measured (owner record "
                            f"{op['clear_width_mm_measured']} mm)",
        "18_q14": f"{q14['state']} {q14['value']} m2 (SHADOW, not FINAL)",
        "19_q14_blocker": "none for SHADOW; release blockers: " + "; ".join(q14["release_blockers"]),
        "20_q13_blockers": q13["blocker_set"],
        "21_wardrobe_floor_sole": f"{q13['sole_blocker_test']['answer']}: " +
                                  json.dumps(q13["sole_blocker_test"]["counterfactual"]),
        "22_digest_hierarchy": d["definition"],
        "23_fact_changes_topology_digest": "NO - " + d["hall_lobby_fact"]["topology"],
        "24_fact_changes_row_digest": "NO in R8.12 (corroborating only); it changes the Q-14 RELEASE digest - " +
                                      d["hall_lobby_fact"]["r8_11_difference"],
        "25_owner_facts_generic": "PARTLY: engine/source/owner_facts.py (fact model, binding, six outcomes, engine/owner "
                                  "matrix, policy digest); the row computation that consumes them is still lab code "
                                  "(E-R8.13-06)",
        "26_constants_in_policy": "YES for wall_bands (PARAMS; AST-checked); closure-id rounding found in "
                                  "topology_closures (identity only) -> E-R8.13-05",
        "27_new_silent_error": [R["FACE_CHAIN_REGISTER"]["finding_V3_D1"],
                                R["WALL_BAND_ASSEMBLY_REGISTER"]["finding_V3_D2"],
                                "local pairing can turn an unlabelled slice of a room into a band (found and guarded "
                                "BEFORE the freeze: a label in the raw pair strip rejects the pair)"],
        "28_r8_13": rec["10_after_r8_12"] + "; fix V3-D1 / V3-D2 as WALL_BAND_POLICY_V4 under the same freeze protocol",
        "29_disagree_with_chatgpt": rec["8_disagree_with_prompt"] + [
            "the owner fact should NOT stay in the row layer once the engine resolves the same reading - it becomes "
            "corroboration (outside the row digest) and only its passage attributes stay applied (release layer)"]}
    return {
        "SCHEMA": "URBAN_R8_12_DECISION_REGISTER_V1", "recommendation_before_coding": rec,
        "order": ["recommendation written (r8_12_recommendation.json)",
                  f"V3 + synthetic tests committed: {R['R8_12_FRAGMENT_BAND_FREEZE']['frozen_commit'][:12]}",
                  "freeze record committed", "blind run committed (BLIND_QORTUBA_RESULT.json)",
                  "owner fact compared afterwards", "rows rebuilt"],
        "decisions": [
            {"id": "R812-D01", "decision": "WALL_BAND_POLICY_V3: chains + local spans + assemblies, frozen before Qortuba"},
            {"id": "R812-D02", "decision": "TOPOLOGY_CLOSURE_POLICY_V1 unchanged (digest identical)"},
            {"id": "R812-D03", "decision": "the owner fact is CORROBORATING_ONLY for topology and rows; APPLIED for "
                                           "passage attributes (release layer); no owner role claim"},
            {"id": "R812-D04", "decision": "digest hierarchy TOPOLOGY / ROW_AUTHORITY / RELEASE_INPUT"},
            {"id": "R812-D05", "decision": "V3-D1 and V3-D2 recorded for R8.13; V3 not edited after the blind run"},
            {"id": "R812-D06", "decision": "Q-14 COMPUTED_SHADOW (not FINAL); Q-13: one owner question"}],
        "rows": {r: (v["state"], v["value"]) for r, v in S["rows"]["NEW_K2_R8_12"].items()},
        "gates": {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO", "PRODUCTION_MIGRATION": "NO"},
        "answers": answers}


def main(regdir):
    regdir = Path(regdir)
    q13 = jl(regdir / "Q13_STATUS.json")
    for name, obj in (("OWNER_ACTION_REGISTER", owner_actions(q13)), ("ENGINEERING_ACTION_REGISTER",
                                                                       engineering_actions()),
                      ("R8_12_DECISION_REGISTER", decision_register(regdir))):
        (regdir / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str) + "\n")
    print("ok")


if __name__ == "__main__":
    main(sys.argv[1])
