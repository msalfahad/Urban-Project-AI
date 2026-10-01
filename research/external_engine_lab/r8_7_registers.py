"""R8.7 registers: source revisions, owner actions (V4), owner project claims, input schema, decisions.

Reads committed registers / claims and the proof registers written by r8_7_proof.py into the same directory.

    python3 research/external_engine_lab/r8_7_registers.py <register_dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_7_canonical as R7                                                      # noqa: E402
from engine.source import canonical_input as CI, owner_scope as OS              # noqa: E402

R86A = ROOT / "tests/r8_6a/registers"
R86 = ROOT / "tests/r8_6/registers"
RESOLVED_BY = "explicit owner input recorded as an authorised claim (release V3)"


def load(p):
    return json.loads(Path(p).read_text())


def revisions(out):
    prov = load(R86A / "DXF_PROVENANCE_REGISTER.json")["files"]["QORTUBA"]
    variants = load(R86A / "QORTUBA_ROUND1_DXF_RESULTS.json")["plan_variants"]
    cls = load(out / "REGION_CLASSIFICATION_NEW_REVISION.json")
    delta = load(out / "QORTUBA_REVISION_DELTA.json")
    return {
        "SCHEMA": "URBAN_R8_7_QORTUBA_SOURCE_REVISION_REGISTER_V1",
        "rule": "a measurement consumes exactly one revision; revisions are never mixed (canonical_input SOURCE_REVISION_MISMATCH)",
        "revisions": {
            R7.REV_OLD_ID: {
                "status": "HISTORICAL_VALIDATED_REVISION", "anchor_kind": CI.EXACT_SOURCE, "dwg_sha256": R7.OLD_DWG,
                "unit": {"native_to_mm": 10.0, "claim": R7.OLD_UNIT_CLAIM, "state": "CONFIRMED_BY_HUMAN (exact source)"},
                "plan_count": 1, "tracked_plan": "one SECOND FLOOR PLAN (title handle 0x1AC, frame occurrence H156)",
                "proof": {"R8_6_six_row_canonical_rebuild": "VALID_FOR_REVISION_OLD",
                          "classification_now": "SUPERSEDED_SOURCE_BASELINE",
                          "useful_for": ["revision delta analysis", "regression history", "explaining what changed"],
                          "is_not": "CURRENT_QORTUBA_QUANTITY_TRUTH",
                          "reproduced_through_the_contract": delta["runs"]["OLD_K1"]["six_contract_rows"]}},
            R7.REV_NEW_ID: {
                "status": "OWNER_SELECTED_CURRENT_REVISION", "anchor_kind": CI.DERIVED_PENDING_SOURCE,
                "scope_label": "QORTUBA_NEW_REVISION_PENDING_DWG", "dxf_sha256": R7.NEW_DXF,
                "matching_original_dwg": "PENDING_EXTERNAL_INPUT",
                "relationship_to_old": ["SAME_DRAWING_LINEAGE", "LATER_REVISION", "OWNER_SELECTED_CURRENT_REVISION"],
                "lineage_evidence": {"fingerprintguid_equal": prov["revision"]["fingerprintguid_equal"],
                                     "versionguid_equal": prov["revision"]["versionguid_equal"],
                                     "added_editing_time_seconds": prov["editing_time_evidence"]["added_editing_time_seconds"]},
                "converter": "CONVERTER_UNKNOWN (not asked again)", "parser_independence": "NOT_ESTABLISHED",
                "plan_count": 4,
                "plan_variants": {v: {"frame_occurrence": h, "extent": cls["frames"][v]["extent"]} for v, h in R7.VARIANT_FRAMES.items()},
                "selected": {"variant": "PLAN_VARIANT_4_SELECTED", "rank": "bottom-most / 4 of 4", "title_handle": "0x1AC",
                             "region_id": R7.REGION_ID, "frame_occurrence": R7.FRAME_INSERT,
                             "measurement_clip": cls["frames"]["PLAN_VARIANT_4_SELECTED"]["extent"],
                             "claim": "QORTUBA-PLAN-SELECTION-OWNER-001"},
                "unit": {"native_to_mm": 10.0, "claim": R7.NEW_UNIT_CLAIM,
                         "state": "OWNER_CONFIRMED_PENDING_EXACT_DWG_ANCHOR"},
                "region_classification": cls["counts"],
                "allowed_use": "SHADOW / DIAGNOSTIC only until the matching DWG is anchored",
                "when_the_dwg_arrives": ["hash it", "compare it to DXF df0e1d69 (identity, handles, fidelity)",
                                         "re-anchor revision identity", "re-anchor the plan selection",
                                         "re-anchor the unit claim (supersede, history kept)",
                                         "re-anchor the Q-14 scoped claim", "re-measure the canonical quantities on the DWG"],
                "variants_from_R8_6A": [v["variant_id"] for v in variants["variants"]]}},
        "region_candidate_note": ("the region candidate's recorded bounds lie ~36 units inside the frame's corner marks; "
                                  "the measurement clip is the frame occurrence's own extent; clipping to the candidate "
                                  "bounds cuts the frame occurrence and is refused (REVIEW_REQUIRED)")}


def owner_actions():
    prev = {a["action_id"]: a for a in load(R86A / "OWNER_ACTION_REGISTER.json")["actions"]}
    acts = []

    def carry(aid, **kw):
        a = dict(prev[aid])
        a.update(kw)
        acts.append(a)
    carry("CONFIRM_QORTUBA_NATIVE_UNIT", note="historical revision only; unchanged")
    acts.append({"action_id": "CONFIRM_QORTUBA_AUTHORITATIVE_REVISION", "project": "QORTUBA",
                 "question": "Which Qortuba drawing is the current design?", "status": "RESOLVED",
                 "answer": "the newer four-layout drawing (QORTUBA_REV_NEW); the older 2ec3a9c8 stays historical",
                 "resolved_by_claim": "QORTUBA-AUTHORITATIVE-REVISION-OWNER-001", "exact_source_hash": R7.NEW_DXF,
                 "supersedes_action": "DECIDE_QORTUBA_DRAWING_REVISION", "what_is_blocked": [], "urgency": "-"})
    acts.append({"action_id": "SELECT_QORTUBA_BOTTOM_MOST_PLAN", "project": "QORTUBA",
                 "question": "Which of the four stacked SECOND FLOOR PLAN layouts is measured?", "status": "RESOLVED",
                 "answer": "PLAN_VARIANT_4_SELECTED (bottom-most, title 0x1AC, region RC:MODEL_SPACE:4267:540:1649)",
                 "resolved_by_claim": "QORTUBA-PLAN-SELECTION-OWNER-001", "exact_source_hash": R7.NEW_DXF,
                 "supersedes_action": "REVIEW_QORTUBA_SECOND_FLOOR_PLAN_DESIGNATION", "what_is_blocked": [], "urgency": "-",
                 "use_limit": "SHADOW / DIAGNOSTIC until ANCHOR_SELECTED_PLAN_TO_EXACT_NEW_DWG"})
    acts.append({"action_id": "CONFIRM_QORTUBA_NEW_REVISION_NATIVE_UNIT", "project": "QORTUBA",
                 "question": "What is the native unit of the newer drawing?", "status": "RESOLVED",
                 "answer": "1 native unit = 1 cm (native_to_mm 10.0)", "resolved_by_claim": R7.NEW_UNIT_CLAIM,
                 "exact_source_hash": R7.NEW_DXF, "what_is_blocked": [], "urgency": "-",
                 "anchor_state": "OWNER_CONFIRMED_PENDING_EXACT_SOURCE_ANCHOR"})
    carry("REVIEW_QORTUBA_Q14_CEILING_CONDITIONS", status="RESOLVED",
          answer="ceiling footprint = floor footprint for the ten Q-14 spaces of the selected apartment layout only",
          resolved_by_claim=R7.Q14_CLAIM, exact_source_hash=R7.NEW_DXF,
          scope="QORTUBA_REV_NEW / RC:MODEL_SPACE:4267:540:1649 / ten labelled spaces / Q-14 only; never a floor-wide, "
                "villa-wide or company rule")
    acts.append({"action_id": "SUPPLY_QORTUBA_NEW_REVISION_DWG", "project": "QORTUBA",
                 "question": "Please send the original DWG of the newer four-layout Qortuba drawing (the file 'qurtoba villah.dxf' was made from), unchanged.",
                 "why_needed": "every new-revision claim and value is anchored to the DXF only; the DWG anchors revision identity, "
                               "plan selection, unit, the Q-14 claim and the quantities",
                 "exact_source_hash": R7.NEW_DXF, "choices": None, "status": "OPEN", "urgency": "HIGH",
                 "what_is_blocked": ["ANCHOR_SELECTED_PLAN_TO_EXACT_NEW_DWG", "any release of a new-revision quantity"],
                 "supersedes_action": "SUPPLY_QORTUBA_SOURCE_DWG_OF_DXF", "resolved_only_by": "a file, then hash + identity checks"})
    acts.append({"action_id": "ANCHOR_SELECTED_PLAN_TO_EXACT_NEW_DWG", "project": "QORTUBA", "status": "OPEN",
                 "question": "(Urban task, no owner input) re-anchor revision, plan selection, unit and Q-14 claims to the DWG hash",
                 "exact_source_hash": R7.NEW_DXF, "what_is_blocked": ["production publication of the new revision"],
                 "urgency": "AFTER_SUPPLY", "blocked_by": ["SUPPLY_QORTUBA_NEW_REVISION_DWG"]})
    acts.append({"action_id": "APPROVE_QORTUBA_NEW_ROUND1_BASELINE", "project": "QORTUBA", "status": "OPEN_AFTER_REMEASUREMENT",
                 "question": "Approve the new-revision round-1 rows as the baseline (after they are established on the DWG)",
                 "exact_source_hash": R7.NEW_DXF, "what_is_blocked": ["migration transaction step 1"],
                 "urgency": "LATER", "supersedes_action": "APPROVE_QORTUBA_ROUND1_BASELINE",
                 "note": "the diagnostic remeasurement does not yet establish Q-13 / Q-14 (rooms not established) and flags "
                         "Q-03 / Q-11 (merged labelled space)"})
    for aid in ("SUPPLY_INDEPENDENT_P7757_DXF", "DECIDE_ALRASHED_COLUMN_DEDUCTION_METHOD", "CONFIRM_P7757_NATIVE_UNIT",
                "RESOLVE_ALRASHED_UNIT", "REVIEW_ALRASHED_FLOOR_WINDOWS"):
        carry(aid)
    retired = ["DECIDE_QORTUBA_DRAWING_REVISION (answered: CONFIRM_QORTUBA_AUTHORITATIVE_REVISION)",
               "REVIEW_QORTUBA_SECOND_FLOOR_PLAN_DESIGNATION (answered: SELECT_QORTUBA_BOTTOM_MOST_PLAN)",
               "SUPPLY_QORTUBA_SOURCE_DWG_OF_DXF (renamed SUPPLY_QORTUBA_NEW_REVISION_DWG)",
               "SUPPLY_INDEPENDENT_QORTUBA_DXF (retired: a DXF is not asked for again; the DWG is)",
               "SUPPLY_DXF_CONVERSION_RECORD (retired: the owner does not know the converter; CONVERTER_UNKNOWN stays)",
               "APPROVE_QORTUBA_ROUND1_BASELINE (old revision; superseded by APPROVE_QORTUBA_NEW_ROUND1_BASELINE)"]
    return {"SCHEMA": "URBAN_R8_7_OWNER_ACTION_REGISTER_V4", "rule": "no action is resolved without explicit owner input",
            "supersedes": "tests/r8_6a/registers/OWNER_ACTION_REGISTER.json (V3; unchanged)",
            "open": sum(a["status"].startswith("OPEN") for a in acts), "resolved": sum(a["status"] == "RESOLVED" for a in acts),
            "actions": acts, "retired_or_superseded": retired}


def project_claims():
    rec = load(R7.CLAIMS)
    cl = R7.claims()
    checks = {}
    for cid, c in cl.items():
        checks[cid] = {
            "own_scope": OS.applies(c, project=c.project, revision_id=c.revision_id, purpose=OS.SHADOW_DIAGNOSTIC,
                                    region_id=c.region_id, space_id=next(iter(sorted(c.space_ids)), None),
                                    item=next(iter(sorted(c.items)), None))["state"],
            "old_revision": OS.applies(c, project=c.project, revision_id=R7.REV_OLD_ID, purpose=OS.SHADOW_DIAGNOSTIC,
                                       region_id=c.region_id, space_id=next(iter(sorted(c.space_ids)), None),
                                       item=next(iter(sorted(c.items)), None))["state"],
            "release_use": OS.applies(c, project=c.project, revision_id=c.revision_id, purpose=OS.RELEASE,
                                      region_id=c.region_id, space_id=next(iter(sorted(c.space_ids)), None),
                                      item=next(iter(sorted(c.items)), None))["state"]}
    old_unit = R7.unit_for(R7.rev_old())
    transfer = R7.unit_for(CI.SourceRevision(R7.REV_NEW_ID, CI.EXACT_SOURCE, "0" * 64))
    return dict(rec, scope_checks=checks,
                historical_unit_claim={"claim": R7.OLD_UNIT_CLAIM, "file": "data/registry/OWNER_UNIT_CLAIMS.json (unchanged)",
                                       "applies_to_old_revision": old_unit[1] == R7.OLD_UNIT_CLAIM},
                no_transfer_check={"new_revision_with_another_anchor": transfer[1]})


def decisions(out):
    delta = load(out / "QORTUBA_REVISION_DELTA.json")
    q14 = load(out / "Q14_SCOPED_CEILING_RULE.json")
    abl = load(out / "FAIL_CLOSED_ABLATION_RESULTS.json")["ablations"]
    hall = next(a for a in abl if a["field"] == "parts.block_identity+parts.source_part_id")
    rows = {r["row"]: r for r in delta["rows"]}
    d = [
        ("R87-D01", "QORTUBA_REV_OLD (2ec3a9c8) and QORTUBA_REV_NEW (DXF df0e1d69, DWG pending) are separate revisions; a "
                    "measurement consumes exactly one."),
        ("R87-D02", "The R8.6 six-row proof is VALID_FOR_REVISION_OLD and is now the SUPERSEDED_SOURCE_BASELINE; it is not "
                    "current quantity truth."),
        ("R87-D03", "Owner decisions recorded as scoped claims: authoritative revision, plan selection (PLAN_VARIANT_4_SELECTED), "
                    "new-revision unit (cm), Q-14 ceiling footprint (selected apartment only). All SHADOW_DIAGNOSTIC until the "
                    "DWG is anchored."),
        ("R87-D04", "CANONICAL_MEASUREMENT_INPUT implemented in engine/source (canonical_input, canonical_build, owner_scope); "
                    "every QS01 declared field fails closed."),
        ("R87-D05", f"The R8.6 silent HALL case (block identity + part identity lost) now returns {hall['guarded_state']} "
                    f"with no quantity; the unguarded method would have published HALL 25.0925."),
        ("R87-D06", "Part identity is source-derived (revision | handle | insert path | kind | index); the coordinate hash is gone "
                    "from the canonical path. Block lineage carries insert + block-record handles."),
        ("R87-D07", "Region membership is judged per top-level occurrence; the measurement clip is the selected plan's own "
                    "frame occurrence (H156)."),
        ("R87-D08", "NEW_REVISION_DXF_DIAGNOSTIC: Q-03P / Q-12 unchanged (11.685); Q-03 / Q-11 37.3882 REVIEW_REQUIRED (merged "
                    "BED.ROOM / BATH); Q-13 / Q-14 BLOCKED (M.B.ROOM, HALL, UNLABELLED not established)."),
        ("R87-D09", "Q-14 owner rule applies only inside its scope; it does not rescue missing geometry; CEILING_NET_PLAN_AREA "
                    "recorded as a future requirement."),
        ("R87-D10", "Converter stays CONVERTER_UNKNOWN; nothing qualifies; the owner is not asked about the converter again."),
        ("R87-D11", "MIGRATION_PLANNING_READY = YES; MIGRATION_EXECUTION_READY = NO; PRODUCTION_MIGRATION = NO."),
    ]
    findings = [
        {"id": "F-R87-01", "risk": "silent quantity error (route sensitivity)",
         "finding": "one WALL segment (H584) horizontal to 4e-11 in K1 and exactly horizontal in K2 moves 1.6425 m2 between "
                    "BED.ROOM and the unlabelled space; Q-13 / Q-14 move by +0.0225. The QS01 room split is not stable across "
                    "routes at the 1e-11 level", "action": "method robustness round (tolerance-explicit axis / junction tests)"},
        {"id": "F-R87-02", "risk": "silent quantity error (region clipping)",
         "finding": "clipping to the region candidate's recorded bounds drops the frame's corner marks; the method then measures "
                    "the title block as a 90.327 m2 'room' (Q-13 199.2895, Q-14 228.837). Fixed: occurrence-level membership "
                    "makes it REVIEW_REQUIRED; the clip is the frame occurrence", "action": "fixed (canonical_build.assemble)"},
        {"id": "F-R87-03", "risk": "room decomposition (new revision)",
         "finding": "205 bound-xref furniture parts ('MY BLOCKS$0$...') added in the master bedroom; the method no longer "
                    "establishes M.B.ROOM", "action": "method must ignore furniture by role, not by layer name"},
        {"id": "F-R87-04", "risk": "room decomposition (new revision)",
         "finding": "the BED.ROOM (16.54) / BATH (5.1) partition changed; the method returns one WET space 'BED.ROOM / BATH' "
                    "24.6257 holding two label occurrences", "action": "MERGED_LABELLED_SPACES -> REVIEW_REQUIRED"},
        {"id": "F-R87-05", "risk": "legacy hard-coded names",
         "finding": "owner_rules.APARTMENT_ROOMS hard-codes 'HALL / whgm'; in the new revision the label texts land in two "
                    "regions ('whgm' 34.609 and a 6 cm 'HALL' sliver), so name-based legacy logic would mis-scope",
         "action": "the canonical contract carries label identity; legacy name sets stay out of new methods"},
        {"id": "F-R87-06", "risk": "unsafe human-claim propagation",
         "finding": "the Q-14 claim is label-scoped; it applies to the new revision only if the remeasured label multiset matches; "
                    "it currently does not (BED.ROOM / BATH, whgm, HALL)", "action": "re-check after the DWG"},
    ]
    gates = {"PRODUCTION_MIGRATION": "NO", "MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO",
             "QORTUBA_CURRENT_REVISION": R7.REV_NEW_ID, "QORTUBA_REV_NEW_ANCHOR": "DXF_ONLY_PENDING_DWG",
             "QORTUBA_PLAN_SELECTION": "RESOLVED (PLAN_VARIANT_4_SELECTED; SHADOW until anchored)",
             "QORTUBA_REV_NEW_UNIT": "OWNER_CONFIRMED_PENDING_EXACT_DWG_ANCHOR", "QORTUBA_Q14_CEILING": "RESOLVED_SCOPED",
             "CANONICAL_MEASUREMENT_INPUT": "IMPLEMENTED_SHADOW", "QS01_FAIL_CLOSED": "YES",
             "INDEPENDENT_REAL_RECONCILIATION": "BLOCKED_EXTERNAL_PROVENANCE", "SIGNATURES_QUALIFIED": 0,
             "ALRASHED_COLUMN_RULE": "TRADE_DEDUCTION_RULE_UNDECIDED"}
    answers = {
        "1_new_revision_authoritative_design": "YES, by owner claim; anchored to the DXF only until the DWG arrives",
        "2_bottom_plan_owner_approved": "YES (PLAN_VARIANT_4_SELECTED)",
        "3_new_revision_unit_owner_confirmed": "YES (1 cm), pending exact DWG anchor",
        "4_q14_ceiling_resolved": "YES, scoped to the selected apartment's ten labelled spaces and Q-14",
        "5_ceiling_condition_prevented_from_leaking": "YES: OWNER_SCOPE_MISMATCH for another region, revision, project, space "
                                                      "or item; PURPOSE_NOT_AUTHORISED for release",
        "6_unanchored_because_dwg_missing": ["revision identity", "plan selection", "unit", "Q-14 claim", "every new value"],
        "7_canonical_input_implemented": "YES (engine/source/canonical_input.py, canonical_build.py, owner_scope.py)",
        "8_qortuba_room_method_requires": {
            "proven_by_ablation": [f for f, e in load(out / "QS01_METHOD_INPUT_CONTRACT.json")["contract"]["evidence"].items()
                                   if e == "CHANGES_OUTPUT" and "+" not in f and "(" not in f]
            + ["input.region (membership by the selected frame occurrence)"],
            "declared_by_policy_no_change_on_this_source": [f for f, e in load(out / "QS01_METHOD_INPUT_CONTRACT.json")["contract"]["evidence"].items()
                                                            if e == "NO_CHANGE_ON_THIS_SOURCE" and "not declared" not in f],
            "not_required": ["texts.text_height", "linetype", "lineweight", "HATCH", "instances / block definition / layer tables"]},
        "9_every_required_missing_field_fails_closed": all(a["guarded_state"] != CI.COMPLETE for a in abl
                                                           if a["field"] != "texts.text_height (not declared)"),
        "10_hall_silent_change_possible": "NO through the contract; the unguarded legacy path still would",
        "11_part_identity_source_based": "YES",
        "12_text_dimension_inputs_canonical": "YES (placed through the insert path, with identity, layer, visibility)",
        "13_revisions_can_mix_accidentally": "NO (SOURCE_REVISION_MISMATCH)",
        "14_new_plan_remeasured": "YES, as NEW_REVISION_DXF_DIAGNOSTIC",
        "15_rows_changed": {k: v["state"] for k, v in rows.items()},
        "16_causes": {k: v["causes"] for k, v in rows.items()},
        "17_q14_changes": q14["state"],
    }
    return {"SCHEMA": "URBAN_R8_7_DECISION_REGISTER_V1",
            "decisions": [{"id": i, "decision": t, "status": "DECIDED"} for i, t in d],
            "findings": findings, "gates": gates, "answers": answers,
            "recommendation": {"next": "SUPPLY the new DWG (external), then: anchor + DWG remeasure; in parallel a QS01 robustness "
                                       "round (route-stable axis/junction tolerances, furniture by role, merged-label refusal) "
                                       "proven on both revisions before any baseline approval",
                               "not_now": ["R9 ceiling trade rules", "migration", "parser qualification"]}}


def main(out):
    out = Path(out)
    dump = lambda n, o: (out / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")  # noqa: E731
    dump("QORTUBA_SOURCE_REVISION_REGISTER", revisions(out))
    dump("OWNER_ACTION_REGISTER", owner_actions())
    dump("OWNER_PROJECT_CLAIMS", project_claims())
    dump("CANONICAL_MEASUREMENT_INPUT_SCHEMA", dict(CI.SCHEMA, qs01_contract=CI.contract_record(R7.QS01)))
    dump("R8_7_DECISION_REGISTER", decisions(out))
    a = load(out / "OWNER_ACTION_REGISTER.json")
    print("actions", len(a["actions"]), "open", a["open"], "resolved", a["resolved"])


if __name__ == "__main__":
    main(sys.argv[1])
