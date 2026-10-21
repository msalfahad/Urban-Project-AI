"""R8.6A — owner actions, decisions, canonical-input-contract review and additional findings (research lab).

Reads only committed registers (tests/r8_6/registers, tests/r8_6a/registers, data/registry/OWNER_UNIT_CLAIMS.json)
and writes OWNER_ACTION_REGISTER.json and R8_6A_DECISION_REGISTER.json to tests/r8_6a/registers. Run it outside
any test session (the determinism guard forbids test-time writes).

    python3 research/external_engine_lab/r8_6a_registers.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R86 = ROOT / "tests/r8_6/registers"
OUT = ROOT / "tests/r8_6a/registers"
CLAIMS = ROOT / "data/registry/OWNER_UNIT_CLAIMS.json"

QORTUBA_DWG = "2ec3a9c8b66eb2e129275b87010f4a8d79d7e5bdcc31c1897c14fd7e5647d355"
QORTUBA_DXF = "df0e1d690285f5455b3b5acebe7e20eaee2d1c8aa3743b633a9fd257c6d6f315"
P7757_DWG = "7f61f3acdd62d62dc745f8b522f8136cb41c575df36ec6d9f27c2fe48fea41e3"
P7757_DXF = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
ST7757_DWG = "3f7a556c69786834c16c355504437b5abcd1f5aa3a9625b33a2c5b14213f0227"
ST7757_DXF = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
RESOLVED_BY = "explicit owner input recorded as an authorised claim (release V3)"
# R8.6 ids renamed by the R8.6A brief (§28); the old id is kept on the row so nothing is lost
RENAMED = {"CONFIRM_Q14_CEILING_HAS_NO_VOID_OR_OPENING": "REVIEW_QORTUBA_Q14_CEILING_CONDITIONS",
           "APPROVE_QORTUBA_ROUND1_BASELINE_ROWS": "APPROVE_QORTUBA_ROUND1_BASELINE",
           "DECIDE_COLUMN_DEDUCTION_METHOD": "DECIDE_ALRASHED_COLUMN_DEDUCTION_METHOD",
           "RESOLVE_ALRASHED_UNIT_CONFLICT": "RESOLVE_ALRASHED_UNIT",
           "REVIEW_ALRASHED_ADAPTER_WINDOWS": "REVIEW_ALRASHED_FLOOR_WINDOWS"}


def load(p):
    return json.loads(Path(p).read_text())


def owner_actions():
    prev = {a["action_id"]: a for a in load(R86 / "OWNER_ACTION_REGISTER.json")["actions"]}
    prov = load(OUT / "DXF_PROVENANCE_REGISTER.json")["files"]
    fid = load(OUT / "SOURCE_FIDELITY_RESULTS.json")["files"]
    qv = load(OUT / "QORTUBA_ROUND1_DXF_RESULTS.json")
    claim = next(c for c in load(CLAIMS)["claims"] if c["evidence_id"] == "QORTUBA-NATIVE-UNIT-OWNER-001")
    acts = []

    def carry(old_id, **change):
        a = dict(prev[old_id])
        new_id = RENAMED.get(old_id, old_id)
        if new_id != old_id:
            a["action_id"], a["previous_action_id"] = new_id, old_id
        a.update(change)
        acts.append(a)

    carry("CONFIRM_QORTUBA_NATIVE_UNIT",
          binds_only_to=QORTUBA_DWG,
          not_transferred_to=[QORTUBA_DXF, "the DWG the Qortuba DXF was converted from (not supplied)", P7757_DWG,
                              ST7757_DWG],
          note="unchanged by R8.6A; the later Qortuba revision needs its own unit claim if it is ever measured")
    assert acts[0]["status"] == "RESOLVED" and acts[0]["resolved_by_claim"] == claim["evidence_id"]
    carry("REVIEW_QORTUBA_SECOND_FLOOR_PLAN_DESIGNATION",
          question="Is this the correct Qortuba second-floor plan view that Urban should use for quantity measurement?",
          choices=["YES", "NO", "NOT SURE"],
          review_image="QORTUBA_SECOND_FLOOR_PLAN_OWNER_REVIEW.png",
          candidate={"region_id": "RC:MODEL_SPACE:4267:540:1649", "title_text_handle_in_dwg": "0x1AC (428)",
                     "bounds": qv["plan_variants"]["tracked_dwg_region"]["bounds"],
                     "variant_in_dxf": "PLAN_VARIANT_4_SELECTED_CANDIDATE (bottom-most)"},
          owner_context_recorded=("owner said the drawing holds four similar SECOND FLOOR PLAN layouts stacked "
                                  "vertically and the last / bottom-most is the one to use; recorded as context, not as "
                                  "a designation"),
          conflict_reported=("the measured DWG 2ec3a9c8 contains ONE 'SECOND FLOOR PLAN' layout (handle 0x1AC); the four "
                             "stacked layouts exist only in the later revision behind DXF df0e1d69. The bottom-most "
                             "layout there is the same title handle at the same position, so the selection agrees; "
                             "'last' by creation order would instead be the top copy (0x3690)"),
          binds_to=QORTUBA_DWG,
          note=("an answer is recorded for the exact source hash it was asked about; it is not transferred to the later "
                "revision"))
    carry("CONFIRM_Q14_CEILING_HAS_NO_VOID_OR_OPENING",
          question=("In these ten second-floor spaces, is there any ceiling void, stair opening, shaft, open-to-above area or "
                    "change of ceiling (bulkhead / drop) that is NOT the same as the floor area shown?"),
          choices=["NO (ceiling = floor area)", "YES (name the spaces)", "NOT SURE"],
          review_image="QORTUBA_Q14_CEILING_OWNER_REVIEW.png",
          affected_spaces=[[x["room_id"], x["room"], x["preview_area_m2"]] for x in next(
              r for r in load(R86 / "QORTUBA_ROUND1_PROOF.json")["rows"] if r["row_id"].startswith("Q-14"))["formula_inputs"]])
    carry("APPROVE_QORTUBA_ROUND1_BASELINE_ROWS",
          depends_on=["DECIDE_QORTUBA_DRAWING_REVISION"],
          note=("the six rows were measured on DWG 2ec3a9c8; the later revision changes 10 of their source observations "
                "(HALL, BED.ROOM 18.7525, BATH 5.1, UNLABELLED 4.51), so approve only after the revision decision"))
    acts.append({
        "action_id": "DECIDE_QORTUBA_DRAWING_REVISION", "project": "QORTUBA",
        "question": ("The Qortuba DXF you sent is a LATER version of the drawing than the DWG Urban measured (about 12.6 "
                     "hours more editing; 21 measured lines are gone and 19 new ones are in the second-floor plan). Which "
                     "version should Urban measure?"),
        "choices": ["THE LATER VERSION (send that DWG)", "THE MEASURED DWG 2ec3a9c8", "NOT SURE"],
        "why_needed": "the round-1 rows are tied to one exact drawing revision; Urban must not pick it",
        "exact_source_hash": QORTUBA_DXF, "compared_with": QORTUBA_DWG,
        "evidence": {"revision": prov["QORTUBA"]["revision"], "revision_evidence": prov["QORTUBA"]["revision_evidence"],
                     "editing_time_evidence": prov["QORTUBA"]["editing_time_evidence"]},
        "what_is_blocked": ["which revision round 1 measures", "round-1 baseline approval", "any use of DXF df0e1d69"],
        "urgency": "HIGH", "status": "OPEN", "resolved_only_by": RESOLVED_BY})
    acts.append({
        "action_id": "SUPPLY_QORTUBA_SOURCE_DWG_OF_DXF", "project": "QORTUBA",
        "question": ("Please send the DWG file that 'qurtoba villah.dxf' was made from (the one with four SECOND FLOOR "
                     "PLAN layouts), unchanged."),
        "why_needed": ("the DXF cannot be checked against the DWG it came from; with that DWG Urban can test fidelity and, "
                       "if chosen, re-anchor round 1 to it. That DWG will also need its own unit confirmation"),
        "exact_source_hash": QORTUBA_DXF, "choices": None,
        "what_is_blocked": ["source fidelity of DXF df0e1d69 against its own DWG (NOT_ESTABLISHED)",
                            "re-anchoring round 1 to the later revision"],
        "urgency": "HIGH", "status": "OPEN", "resolved_only_by": "a file whose bytes match the request, then its own claims"})
    carry("SUPPLY_INDEPENDENT_QORTUBA_DXF",
          FILE_RECEIVED={"state": "RECEIVED", "sha256": QORTUBA_DXF,
                         "but": "SOURCE_REVISION_MISMATCH: a later revision, not an export of 2ec3a9c8"},
          INDEPENDENT_PROVENANCE_ESTABLISHED="NO",
          admission=prov["QORTUBA"]["admission_v2"]["status"],
          note="a file existing does not resolve this action")
    carry("SUPPLY_INDEPENDENT_P7757_DXF",
          FILE_RECEIVED={"state": "RECEIVED", "sha256": P7757_DXF,
                         "source_fidelity": fid["P7757"]["result"], "intake_class": fid["P7757"]["intake_class"]},
          INDEPENDENT_PROVENANCE_ESTABLISHED="NO",
          admission=prov["P7757"]["admission_v2"]["status"],
          note="high-fidelity file received; independence still unproven, so nothing qualifies")
    acts.append({
        "action_id": "SUPPLY_DXF_CONVERSION_RECORD", "project": "ALL",
        "question": ("For the three DXFs: which program and version wrote them (on which computer), with which "
                     "settings? A screenshot of the program's About box and the save dialog, or its log, is enough."),
        "why_needed": ("the files carry AutoCAD/ODA-family format traits and were written on a computer whose clock was "
                       "UTC+3 at 2026-10-01 18:27-18:41 UTC; that is consistent with a desktop CAD program but does not "
                       "name it. Parser independence needs the tool named with evidence"),
        "exact_source_hash": P7757_DXF, "also_for": [QORTUBA_DXF, ST7757_DXF], "choices": None,
        "what_is_blocked": ["INDEPENDENT_PROVENANCE_ESTABLISHED for every DXF", "every signature qualification"],
        "urgency": "HIGH", "status": "OPEN",
        "resolved_only_by": "a conversion record with hashed evidence (tool, version, settings), never a description alone"})
    for old in ("DECIDE_COLUMN_DEDUCTION_METHOD", "CONFIRM_P7757_NATIVE_UNIT", "RESOLVE_ALRASHED_UNIT_CONFLICT",
                "REVIEW_ALRASHED_ADAPTER_WINDOWS"):
        carry(old)
    p7 = next(a for a in acts if a["action_id"] == "CONFIRM_P7757_NATIVE_UNIT")
    p7["note"] = ("the P7757 DXF declares $INSUNITS 4 (mm), the same declaration the DWG carries; a declaration is not "
                  "a confirmation")
    return {"SCHEMA": "URBAN_R8_6A_OWNER_ACTION_REGISTER_V3",
            "rule": "no action is marked resolved without explicit owner input; a received file is not a resolution",
            "supersedes": "tests/r8_6/registers/OWNER_ACTION_REGISTER.json (V2; unchanged)",
            "open": sum(a["status"] == "OPEN" for a in acts), "resolved": sum(a["status"] == "RESOLVED" for a in acts),
            "actions": acts}


CONTRACT_FIELDS = [
    # field, carried by the R8.6 canonical rebuild?, how, fail-closed today?
    ("block identity along the instance path", "YES", "block names derived from the K1 instance path (D1 INSERT -> block record)", "NO"),
    ("stable source part id", "PARTIAL", "sub_id = hash(K1 obs id + canonical coordinates): unique within one decode, "
     "NOT stable across revisions or after any coordinate change", "NO"),
    ("source observation id", "YES", "K1 lineage obs_id", "NO"),
    ("instance path", "YES", "K1 lineage instance_path", "NO"),
    ("placed text identity", "YES", "D1 TEXT/MTEXT placed through K1 instance paths (lab mapping)", "NO"),
    ("placed dimension identity", "YES", "D1 definition points + measurement (lab mapping)", "NO"),
    ("layer", "YES", "K1 lineage layer", "NO"),
    ("visibility", "PARTIAL", "K1 removes hidden entities into rg.hidden; the method input carries no visibility flag", "NO"),
    ("curve identity", "YES", "one primitive per K1 segment / arc / circle with its lineage", "NO"),
    ("source handle / correlation identity", "YES", "K1 lineage source_handle", "NO"),
]


def decisions():
    prov = load(OUT / "DXF_PROVENANCE_REGISTER.json")["files"]
    fid = load(OUT / "SOURCE_FIDELITY_RESULTS.json")["files"]
    q = load(OUT / "QORTUBA_ROUND1_DXF_RESULTS.json")
    p = load(OUT / "P7757_DXF_RESULTS.json")
    nq = sum(1 for v in q["signatures"]["signature_states"].values() if v["state"] != "PROVENANCE_NOT_INDEPENDENT")
    npp = sum(1 for v in p["signatures"]["signature_states"].values() if v["state"] != "PROVENANCE_NOT_INDEPENDENT")
    assert nq == npp == 0
    d = [
        ("R86A-D01", "Files identified by SHA-256 only. Qortuba df0e1d69, P7757 ab54dd55, ST7757 9f9d1179 found; no re-upload "
                     "requested."),
        ("R86A-D02", "Writer, decoder and source metadata are recorded as three separate facts. All three DXFs: DXF_WRITER = "
                     "AUTOCAD_OR_ODA_FAMILY_FORMAT, DWG_DECODER = CONVERTER_UNKNOWN, SOURCE_METADATA_LASTSAVEDBY = 'Msalf'."),
        ("R86A-D03", "Qortuba DXF is SAME_LINEAGE_DIFFERENT_REVISION of DWG 2ec3a9c8 (same FINGERPRINTGUID, different "
                     "VERSIONGUID, +45,537 s editing time, 21 measured entities missing, 19 added in the plan region): "
                     "SOURCE_FIDELITY_FAIL against 2ec3a9c8, NOT_ESTABLISHED against its own DWG, admission REJECTED."),
        ("R86A-D04", f"P7757 and ST7757 DXFs: SOURCE_FIDELITY_PASS (P7757: {fid['P7757']['identity']['same_handle_type_layer']}/"
                     f"{fid['P7757']['identity']['d1_model_space_entities']} model-space entities same handle/type/layer; "
                     "geometry PASS; 0x929 kept as ARC_DIMENSION), class HIGH_FIDELITY_PROVENANCE_UNVERIFIED_DXF."),
        ("R86A-D05", "No signature qualified (Qortuba 0/10, P7757 0). Every signature reads PROVENANCE_NOT_INDEPENDENT with "
                     "its diagnostic outcome kept beside it. No numerical-percentage qualification."),
        ("R86A-D06", "INDEPENDENT_QORTUBA_RECONCILIATION = BLOCKED_EXTERNAL_PROVENANCE (and SOURCE_REVISION_MISMATCH)."),
        ("R86A-D07", "ST7757 is structural supporting evidence only; nothing from it enters architectural quantities."),
        ("R86A-D08", "The owner's unit claim stays bound to 2ec3a9c8; it is not transferred to the DXF or the later DWG."),
        ("R86A-D09", "Plan selection: bottom-most layout = PLAN_VARIANT_4_SELECTED_CANDIDATE, the same title handle and "
                     "position as the measured plan. A candidate only; the designation stays PENDING_OWNER."),
        ("R86A-D10", "K2 (ezdxf route) fixed to read optional attributes without raising (RTEXT has no layer in ezdxf): one "
                     "unknown entity type no longer stops the route. SHADOW code; no quantity path touched."),
        ("R86A-D11", "Next coding round: A (CANONICAL_MEASUREMENT_INPUT contract, fail-closed) now; independent "
                     "qualification (B) when a conversion record and the right Qortuba DWG arrive."),
        ("R86A-D12", "MIGRATION_PLANNING_READY = YES (round 1 must be re-anchored after the revision decision); "
                     "MIGRATION_EXECUTION_READY = NO; PRODUCTION_MIGRATION = NO."),
    ]
    findings = [
        {"id": "F-R86A-01", "risk": "silent quantity error / source omission",
         "finding": ("the Qortuba drawing has moved on: the owner's current file is a later revision than the DWG the six "
                     "rows were measured on; 10 round-1 source observations are gone (HALL, BED.ROOM 18.7525, BATH 5.1, "
                     "UNLABELLED 4.51 are built from them). Approving the R8.6 rows as baseline now would freeze an "
                     "outdated drawing"),
         "action": "DECIDE_QORTUBA_DRAWING_REVISION"},
        {"id": "F-R86A-02", "risk": "incorrect region authority",
         "finding": ("the owner's 'four stacked layouts' description fits the later revision, not the measured DWG (one "
                     "layout). A designation answer must bind to one exact hash; 'last' is ambiguous (bottom-most vs most "
                     "recently created copy 0x3690)"),
         "action": "REVIEW_QORTUBA_SECOND_FLOOR_PLAN_DESIGNATION"},
        {"id": "F-R86A-03", "risk": "false parser qualification",
         "finding": ("the three DXFs were written within 14 minutes on a machine with a UTC+3 clock, by a program that keeps "
                     "TDINDWG and writes AC1032 with ACDSDATA; P7757/ST7757 were open 21 s / 10 s. This narrows the "
                     "story (a desktop CAD program, not a Python library) but names no tool: still CONVERTER_UNKNOWN"),
         "action": "SUPPLY_DXF_CONVERSION_RECORD"},
        {"id": "F-R86A-04", "risk": "identity loss",
         "finding": ("sub_id in the canonical rebuild hashes coordinates: unique within a decode but not stable across "
                     "revisions. A cross-revision comparison must correlate by handle + instance path, never by sub_id"),
         "action": "CANONICAL_MEASUREMENT_INPUT contract (next round)"},
        {"id": "F-R86A-05", "risk": "source omission (diagnostic route)",
         "finding": ("the K2 route raised on RTEXT (no 'layer' attribute in ezdxf) and stopped for the whole document; "
                     "fixed so the entity reaches the UNHANDLED finding"),
         "action": "fixed in engine/source/cad/kernel_ezdxf.py (SHADOW)"},
        {"id": "F-R86A-06", "risk": "test nondeterminism",
         "finding": ("intake paths under the session upload folder were kept out of frozen truth: registers record file "
                     "names and hashes only, tests read committed registers"),
         "action": "none (guard holds)"},
        {"id": "F-R86A-07", "risk": "incorrect frame authority",
         "finding": ("the Qortuba DXF declares $INSUNITS 5 (cm) like the DWG; that agreement is not a confirmation for the "
                     "later revision, which needs its own owner unit claim"),
         "action": "SUPPLY_QORTUBA_SOURCE_DWG_OF_DXF"},
    ]
    return {"SCHEMA": "URBAN_R8_6A_DECISION_REGISTER_V1",
            "decisions": [{"id": i, "decision": t, "status": "DECIDED"} for i, t in d],
            "canonical_input_contract_review": {
                "lesson": "identical segments with lossy provenance changed HALL 36.37 -> 25.0925 m2 (R8.6 ablation)",
                "fields": [{"field": f, "carried_now": c, "how": h, "fail_closed_today": fc} for f, c, h, fc in CONTRACT_FIELDS],
                "gap": ("the method accepts a primitive with a blank block path or colliding part id and silently changes "
                        "rooms; no input declares its required provenance"),
                "proposal": ("CANONICAL_MEASUREMENT_INPUT: each method declares the provenance fields it reads; the adapter "
                             "refuses (fail closed, named field) when a declared field is absent or not unique; part id = "
                             "(source handle, instance path, part index), never a coordinate hash"),
                "recommendation": "A",
                "why": ["B cannot start: no DXF has proven decoder provenance and the Qortuba DXF is the wrong revision",
                        "A is fully inside our control and removes a proven silent-error path (HALL 36.37 -> 25.09)",
                        "A defines what a qualified parser must deliver, so B qualifies against the real contract",
                        "C would couple an internal change with an external dependency and stall on the external part"]},
            "findings": findings,
            "gates": {"PRODUCTION_MIGRATION": "NO", "MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO",
                      "INDEPENDENT_REAL_RECONCILIATION": "BLOCKED_EXTERNAL_PROVENANCE",
                      "INDEPENDENT_QORTUBA_RECONCILIATION": "BLOCKED_EXTERNAL_PROVENANCE",
                      "INDEPENDENT_P7757_RECONCILIATION": "BLOCKED_EXTERNAL_PROVENANCE",
                      "QORTUBA_DXF_REVISION": prov["QORTUBA"]["revision"]["state"],
                      "QORTUBA_SOURCE_FIDELITY": fid["QORTUBA"]["result"], "P7757_SOURCE_FIDELITY": fid["P7757"]["result"],
                      "ST7757_SOURCE_FIDELITY": fid["ST7757"]["result"],
                      "SIGNATURES_QUALIFIED": 0, "QORTUBA_UNIT_CONTEXT": "CONFIRMED_BY_HUMAN",
                      "QORTUBA_REGION_DESIGNATION": "PENDING_OWNER", "QORTUBA_MEASUREMENT_FRAME": "UNCONFIRMED",
                      "ALRASHED_COLUMN_RULE": "TRADE_DEDUCTION_RULE_UNDECIDED"}}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, obj in (("OWNER_ACTION_REGISTER", owner_actions()), ("R8_6A_DECISION_REGISTER", decisions())):
        (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")
    a = load(OUT / "OWNER_ACTION_REGISTER.json")
    print("actions", len(a["actions"]), "open", a["open"], "resolved", a["resolved"])


if __name__ == "__main__":
    main()
