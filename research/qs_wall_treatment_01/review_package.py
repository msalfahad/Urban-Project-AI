"""OWNER REVIEW PACKAGE (§41) - one concise document over the frozen
artifacts, in the §45 reporting shape. Written beside the artifacts
(gitignored client data) and hashed into FREEZE_FINAL.

    python3 -m research.qs_wall_treatment_01.review_package
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)


def _j(name):
    return json.loads((OUT / name).read_text("utf-8"))


def build() -> str:
    est = _j("P7757_WALL_TREATMENT_ESTIMATE.json")
    a22 = _j("A22_STRUCTURAL_COMPARISON.json")
    rec = _j("BENCHMARK_RECONCILIATION.json")
    ov = _j("OVERLAP_AUDIT.json")
    own = _j("DIMENSION_OWNER_REGISTER.json")
    src = _j("SOURCE_INVENTORY.json")
    cur = _j("CAD_CURVE_REGISTER.json")
    fz = _j("FREEZE_A22.json")
    sens = _j("SENSITIVITY.json")
    ag = est["AGGREGATES"]
    L = [f"# {P.PHASE_ID} - owner review package", "",
         "PHASE: P7757 wall-treatment estimate from the frozen A21 traces, with the "
         "overlap audit, dimension-owner register, CAD curve register, A22 structural "
         "comparison and the benchmark reconciliation.",
         "", "STATUS: COMPLETE for the traced subset; frozen; benchmark opened after the "
         "A22 freeze; nothing tuned.", "",
         "## WHAT WAS PROVEN", "",
         f"- Overlap audit over {sum(len(c['TRACES_AUDITED']) for c in ov['PER_CASE'].values())} "
         f"material traces: {ov['TOTALS']}. Material contradictions beyond junction "
         f"slivers: {sum(len(c['MATERIAL_CONTRADICTIONS_BEYOND_JUNCTIONS']) for c in ov['PER_CASE'].values())}.",
         f"- Dimension owner (deterministic, from traced extension lines): {own['SUMMARY']}. "
         "The orchestrator's visual re-check of every CASE-6 height agreed with the register "
         "on every value and corrected one prose owner (155 ends at the dome apex).",
         f"- CAD curve register: {len(cur['CURVE_SETS'])} curve sets ESTABLISHED_FROM_DWG "
         "(pool arcs, curved main stair); correspondence to traces PROPOSED only.",
         f"- A22 verdicts: {a22['COUNTS']}. Items for human review: {a22['ITEMS_FOR_HUMAN_REVIEW']}.",
         f"- Benchmark: {rec['BENCHMARK']['TYPE']}; independence {rec['BENCHMARK']['EVIDENCE_INDEPENDENCE']}; "
         f"verdicts {rec['COUNTS']}; leak: {rec['BENCHMARK_LEAK'][:4]}.",
         "", "## WHAT CHANGED", "",
         "- New engine modules: material_role_audit, dimension_owner, wall_face_set, "
         "wall_treatment_engine, cad_curve_register. New phase research/qs_wall_treatment_01.",
         "- Owner parameters registered (3.20 normal; 4.00 / 4.50 / 4.00 external; opening and "
         "reveal defaults). APPLICABLE_PLASTER_HEIGHT of the frozen experiments stays UNKNOWN "
         "and is superseded for normal rooms.",
         "", "## WHAT FAILED / IS UNRESOLVED", ""]
    for k, v in ag["BY_TRADE"].items():
        L.append(f"- {k}: established {v['ESTABLISHED_SUBTOTAL_M2']} m2, provisional "
                 f"{v['PROVISIONAL_SUBTOTAL_M2']} m2 apart, coverage {v['COVERAGE_STATUS']}, "
                 f"complete total {v['COMPLETE_TOTAL_STATUS']}")
    L += ["", "## QUANTITIES AVAILABLE (established subtotals; never totals)", "",
          f"- Project, traced subset: **{ag['PROJECT']['ESTABLISHED_SUBTOTAL_M2']} m2** established, "
          f"{ag['PROJECT']['PROVISIONAL_SUBTOTAL_M2']} m2 provisional apart; "
          f"COMPLETE_TOTAL_STATUS {ag['PROJECT']['COMPLETE_TOTAL_STATUS']}.",
          f"- Sensitivity (scenario mode, official parameter unchanged): "
          f"{ {k: v['PROJECT_ESTABLISHED_SUBTOTAL_M2'] for k, v in sens['SCENARIOS'].items()} }",
          "", "## UNRESOLVED ITEMS", ""]
    seen = set()
    for u in ag["PROJECT"]["UNRESOLVED_SCOPE"]:
        key = (u["SET_ID"], u["FACE_ID"])
        if key in seen or u["FACE_ID"] == "*":
            continue
        seen.add(key)
        L.append(f"- {u['SET_ID']} / {u['FACE_ID']}: {u['WHY']}")
    L += [f"- Source documents NOT PROVIDED: {', '.join(src['SOURCE_NOT_PROVIDED'])}",
          "", "## NEXT AUTOMATIC PHASE", "",
          "- none without an owner decision: every remaining face needs a source document, "
          "an owner parameter, or a human link (CAD curve set to traced face).",
          "", "## OWNER DECISION REQUIRED", ""]
    for i in rec["ITEMS"]:
        if i["VERDICT"] in ("HEIGHT_DIFFERENCE", "OPENING_DIFFERENCE", "BASIS_DIFFERENCE",
                            "HUMAN_REVIEW_REQUIRED", "TREATMENT_DIFFERENCE"):
            L.append(f"- {i['ITEM_ID']} {i['SUBJECT']}: {i['VERDICT']} - {i['WHY']}")
    for i in a22["ITEMS"]:
        if i["ITEM_ID"] in a22["ITEMS_FOR_HUMAN_REVIEW"]:
            L.append(f"- A22 {i['ITEM_ID']} {i['SUBJECT']}: {i['VERDICT']} - {i['WHY']}")
    L += ["- Confirm the benchmark workbook is P7757's statement "
          f"({rec['BENCHMARK']['PROJECT_IDENTITY_STATUS']}).",
          "- Which CAD curve set corresponds to which traced face (SEMANTIC_LINK_STATUS "
          "NOT_ESTABLISHED for all).",
          "", "## HASHES", "",
          f"- FREEZE_A22 digest: `{fz['FREEZE_DIGEST_SHA256']}`",
          f"- estimate: `{fz['ARTIFACT_SHA256']['P7757_WALL_TREATMENT_ESTIMATE.json']}`",
          f"- A22: `{fz['ARTIFACT_SHA256']['A22_STRUCTURAL_COMPARISON.json']}`",
          "", "No BOQ was produced. Nothing was written to Firebase. E1.4 was read only by "
          "A22, after A21 froze."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    p = OUT / "OWNER_REVIEW_PACKAGE.md"
    p.write_text(build(), encoding="utf-8")
    print(json.dumps({"OWNER_REVIEW_PACKAGE_SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}))
