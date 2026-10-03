"""Freeze the Method 1b failure evidence. Nothing here is rescued.

Method 1b was the one corrected attempt. It ran under rules hashed before
it was built, it did not survive its own survival criteria, and that is
the end of the arrangement hypothesis in this experiment. This binds every
artifact to its hash so the failure can be checked rather than believed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.arrangement_experiment_01 import method1b_protocol as R
from research.arrangement_experiment_01 import protocol as P

OUT = Path("data/experiments/ARRANGEMENT_EXPERIMENT_01")
M1B = OUT / "method1b"


def main() -> int:
    arts = {}
    for p in sorted(M1B.rglob("*")):
        if p.is_file() and p.name != "FREEZE.json":
            arts[str(p.relative_to(M1B))] = hashlib.sha256(
                p.read_bytes()).hexdigest()

    surv = json.loads((M1B / "SURVIVAL_ASSESSMENT.json").read_text("utf-8"))
    diag = json.loads((M1B / "UNKNOWN_ROLE_DIAGNOSTIC.json").read_text("utf-8"))
    rep = json.loads((M1B / "TOPOLOGY_REPORT.json").read_text("utf-8"))

    body = {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "METHOD": R.METHOD,
        "METHOD_1B_PROTOCOL_HASH": R.protocol_hash(),
        "E1_4_IS_NOT_MODIFIED": True,
        "E1_4_RUN_HASH": P.E1_4_RUN_HASH,

        "VERDICT": surv["VERDICT"],
        "criteria_met": f"{surv['criteria_met']}/{surv['criteria']}",
        "CRITERIA_NOT_MET": [c["CRITERION"] for c in surv["CRITERIA"]
                             if not c["MET"]],
        "CRITERIA_MET": [c["CRITERION"] for c in surv["CRITERIA"]
                         if c["MET"]],

        "WHAT_HAPPENED": (
            "the atomic arrangement closed the small enclosed rooms and "
            "nothing else. Two of the seven selected cases have a "
            "meaningful atomic cell; the other five have no cell at all, "
            "because their label anchor falls in the unbounded exterior. "
            "The whole floor encloses 52.0 m2 across 116 faces, of which "
            "26.1 m2 is free space"),

        "WHERE_THE_FAILURE_LIVES": (
            "not in the partition-capability model. The census below is "
            "the finding: a third of the drawn linework carries no "
            "established semantic role, 839 of those intervals are "
            "continuous linework the line semantics place squarely in the "
            "cut plane, and the role layer establishes no glazing "
            "anywhere on this floor. A room whose fourth side is a window "
            "has no fourth side, and leaks into the exterior. An "
            "arrangement cannot partition a plane with geometry its "
            "evidence layer never classified"),

        "AND_WIDENING_THE_ROLE_LAYER_WOULD_NOT_HAVE_RESCUED_IT": (
            "the diagnostic measured it. Admitting the unclassified "
            "in-cut-plane linework raises the floor from 116 faces and "
            "52.0 m2 to 284 faces and 1130.0 m2, and all seven anchors "
            "then land in a bounded face - but four of them land in the "
            "SAME face of 376.72 m2. That is the site envelope closing, "
            "not the interior partitioning. The open-plan cases would "
            "still have no atomic cell of their own"),

        "THE_NON_FLOOR_EDGES_DID_ALMOST_NOTHING_HERE": (
            "three arcs entered as NON_FLOOR_REGION_BOUNDARY. They close "
            "no non-floor region, no side of any of them is classified "
            "NON_FLOOR, one borders no cell at all, and their net effect "
            "is three faces out of 116. Their three centres differ by up "
            "to 450 mm, so they are not rings of one round object however "
            "the curve semantics grouped them. The 207.8 m2 the earlier "
            "diagnostic attributed to this class was closure produced by "
            "arcs that do not trace the drawn pool, which is exactly why "
            "the protocol forbade arguing from the size of the effect"),

        "THE_ARRANGEMENT_HYPOTHESIS_IN_THIS_EXPERIMENT": "FAILS",
        "NO_METHOD_1C_1D_OR_1E_WAS_BUILT": True,
        "NO_RULE_WAS_CHANGED_AFTER_THE_FIRST_CELL_RESULT": True,
        "IMPLEMENTATION_DEFECT_FOUND_AND_CORRECTED":
            surv["IMPLEMENTATION_DEFECT_FOUND_AND_CORRECTED"],

        "METHOD_1A_IS_PRESERVED_EXACTLY_AS_RUN": True,
        "THE_B_C_D_MEASUREMENTS_REMAIN": "DEVELOPMENT_DIAGNOSTIC_ONLY",
        "THE_UNKNOWN_ROLE_MEASUREMENT_IS": diag["CLASSIFICATION"],

        "THE_LESSON_THIS_EXPERIMENT_PRESERVES":
            R.THE_LESSON_THIS_METHOD_EXISTS_TO_RECORD,
        "it_is_learned_even_though_the_hypothesis_failed": (
            "separating PLANAR_PARTITION_CAPABILITY from clear-room-face "
            "capability was right, and it is what let this run say WHERE "
            "the floor went instead of only that it was missing. E1.4 is "
            "not weakened by any of this: it withheld exactly the regions "
            "whose boundary the drawing does not establish, and the "
            "arrangement independently found the same regions unbounded"),

        "TOPOLOGY": rep["TOPOLOGY"],
        "CELLS_BY_CLASS": rep["CELLS_BY_CLASS"],
        "THE_ROLE_CENSUS": diag["THE_ROLE_CENSUS"],

        "nothing_is_scored_yet": R.NOTHING_IS_SCORED_YET,
        "no_benchmark_or_expected_area_was_opened": True,
        "ARTIFACTS": arts,
    }
    p = M1B / "FREEZE.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    print(json.dumps({"VERDICT": body["VERDICT"],
                      "criteria_met": body["criteria_met"],
                      "artifacts": len(arts),
                      "FREEZE_SHA256": hashlib.sha256(
                          p.read_bytes()).hexdigest()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
