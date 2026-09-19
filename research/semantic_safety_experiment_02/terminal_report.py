"""The experiment stops here, and this says why.

SAFETY_SAMPLE_03 met its sampling targets, passed its render gate and was
read blind by three sealed readers. The reference then established one
OPENING_IN_SEPARATOR against a declared requirement of five, so the
pre-frozen sufficiency rule stops the work before A19 is ever run.

This module writes the terminal report. It computes nothing new: it reads
the frozen registers and states what they say.

    python3 -m research.semantic_safety_experiment_02.terminal_report
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from research.semantic_safety_experiment_02 import protocol as P

OUT = Path("data/experiments/SEMANTIC_SAFETY_EXPERIMENT_02")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ref = json.loads((OUT / "04_REFERENCE_A.json").read_text("utf-8"))
    suf = json.loads((OUT / "10_SUFFICIENCY_VERDICT.json").read_text("utf-8"))
    samp = json.loads((OUT / "SAMPLE_FREEZE.json").read_text("utf-8"))
    feats = json.loads((OUT / "01_CANONICAL_FEATURE_REGISTER.json")
                       .read_text("utf-8"))
    qa = json.loads((OUT / "02_RENDER_QA_REGISTER.json").read_text("utf-8"))

    cross = defaultdict(Counter)
    for r in ref["READINGS"]:
        cross[r["STRATUM"]][r["REFERENCE_RELATION"]] += 1

    rec = {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "SAMPLE_ID": P.SAMPLE_ID,
        "PROTOCOL_VERSION": P.PROTOCOL_VERSION,
        "PROTOCOL_HASH": P.protocol_hash(),
        "SAMPLE_FREEZE_SHA256": samp["SAMPLE_FREEZE_SHA256"],
        "REFERENCE_A_SHA256": sha(OUT / "04_REFERENCE_A.json"),
        "ANCESTRY": [dict(a) for a in P.ANCESTRY],

        "OUTCOME": P.SOURCE_POPULATION_LIMITATION,
        "THE_QUESTION_THAT_WAS_ASKED": P.THE_QUESTION,
        "WHAT_STOPPED_IT": (
            "the reference established ONE OPENING_IN_SEPARATOR across "
            "forty features. The declared requirement, hashed before any "
            "reader opened the sample, was five. The central safety "
            "question is PHYSICAL SEPARATOR against OPENING, and one "
            "example of one side cannot test it"),
        "WHAT_IS_NOT_CLAIMED": (
            "nothing here says A19 is safe, and nothing here says it is "
            "unsafe. A19 was never run on this sample. The experiment "
            "stopped before it, which is the point of stopping"),

        "WHY_ONLY_ONE_OPENING_IS_STRUCTURAL_NOT_BAD_LUCK": (
            "AN OPENING IS AN ABSENCE OF GEOMETRY. The sampling unit of "
            "this experiment is a canonical feature, and a canonical "
            "feature is built from DRAWN INTERVALS. A doorway is where "
            "the wall lines STOP. So where a doorway is nothing but a "
            "gap, the feature has no members of its own to be marked: "
            "the nearest geometry is the wall faces that terminate at "
            "the jamb, and a reader calling those PHYSICAL_SEPARATOR is "
            "CORRECT, not mistaken.\n\n"
            "The one opening the reference did establish, CAF-0007, is "
            "the one place the drawing DRAWS the opening: a true arc on "
            "the door layer inside a door block, a leaf swung open. It "
            "is samplable because it has ink.\n\n"
            "That is why all three rounds returned exactly one opening. "
            "It is not a sampling accident to be fixed by a fourth "
            "draw. A feature-based unit can only offer an opening where "
            "the drawing gives the opening its own geometry"),

        "WHAT_THE_DOOR_STRATUM_ACTUALLY_CAUGHT": {
            "target": 6, "admitted": 6,
            "read_as": dict(cross["DOOR_OR_OPENING_CANDIDATE"]),
            "EXPLANATION": (
                "three were dimension chains that pass NEAR or ACROSS a "
                "door - one runs straight across a door swing without "
                "stopping - which is exactly the weak-proxy problem "
                "SAFETY_SAMPLE_01 exposed, surviving here in the one "
                "signal that cannot be strengthened: proximity to a "
                "door is not the same as being the door. Two were wall "
                "faces that terminate at a jamb, correctly read as "
                "separator. One was the drawn door"),
        },

        "WHAT_DID_WORK": {
            "THE_STRATIFICATION": (
                "SOLID_SEPARATOR_CANDIDATE returned six separating "
                "features out of six - four solid, two glazed. "
                "DIMENSION_OR_ANNOTATION_CANDIDATE returned three "
                "annotation out of three. The role-based strata predict "
                "their categories well where the category HAS drawn "
                "geometry"),
            "THE_SHEET_FILTER": (
                "thirteen sheet intervals removed in feature "
                "construction; no admitted feature touches the drawing "
                "region's boundary. The frame and title block that "
                "consumed a whole stratum of SAFETY_SAMPLE_02 do not "
                "appear here"),
            "THE_RENDER_AND_TAG_GATE": {
                "features_offered": qa["features_offered_to_the_gate"],
                "admitted": qa["features_admitted"],
                "refused": qa["features_refused"],
                "partial_tagging_admissions":
                    qa["features_admitted_with_partial_tagging"],
                "geometrically_distinguishable_but_unplaced": 0,
            },
            "THE_REGRESSION_CASE": (
                "CAF-0007, the doorway that carried the prior critical "
                "false positive, was read OPENING_IN_SEPARATOR at HIGH "
                "confidence by a blind reader that was never told it "
                "was a regression case. The regression rule did its job "
                "even though the round stops"),
        },

        "REFERENCE_A_RELATION_DISTRIBUTION": ref["RELATION_DISTRIBUTION"],
        "STRATUM_AGAINST_WHAT_THE_REFERENCE_READ":
            {k: dict(v) for k, v in sorted(cross.items())},
        "CLASSES_SHORT_OF_THE_THRESHOLD":
            suf["CLASSES_SHORT_OF_THE_THRESHOLD"],
        "CLASSES_TOO_THIN_TO_CARRY_A_RATE":
            suf["CLASSES_TOO_THIN_TO_CARRY_A_RATE"],
        "features_admitted": samp["features_admitted"],
        "canonical_features_on_the_floor":
            feats["canonical_features_on_the_floor"],

        "WHAT_WOULD_BE_NEEDED_TO_ANSWER_THIS_QUESTION": (
            "a floor whose openings are drawn - door blocks, leaves and "
            "swings - rather than left as gaps, OR a sampling unit that "
            "can point at an absence: a feature defined by a recorded "
            "gap in the frozen gap register, marked by its two jambs and "
            "the void between them, rather than by drawn members. The "
            "second is an apparatus change of real size and it is not "
            "attempted here",
        ),
        "NO_SAFETY_SAMPLE_04": P.THIS_IS_THE_LAST_SAMPLE_REDESIGN,
        "what_a_source_population_limitation_means":
            P.WHAT_A_SOURCE_POPULATION_LIMITATION_MEANS,

        "KNOWN_LIMITATION_RECORDED_SEPARATELY": (
            "09_RENDER_GATE_LIMITATION_NOTED.json - the render gate "
            "proves a TAG is legible, not that the MEMBER it points at "
            "is visible. One feature's member lies inside solid poche"),
        "STANDING_PROHIBITIONS_HELD": [
            "E1.4 was not modified", "E1.5 was not created",
            "E2 was not started", "no area was calculated",
            "no BOQ or quantity benchmark was opened",
            "no A19 output was fed into geometry",
            "the A19_NOT_READY gate from SEMANTIC_EDGE_SCORING_01 stands "
            "untouched and unweakened",
        ],
    }
    p = OUT / "TERMINAL_REPORT.json"
    p.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")

    files = {str(x.relative_to(OUT)): sha(x) for x in sorted(OUT.rglob("*"))
             if x.is_file() and x.name != "FREEZE.json"}
    freeze = hashlib.sha256(json.dumps(
        {k: files[k] for k in sorted(files)}, sort_keys=True).encode()
    ).hexdigest()
    (OUT / "FREEZE.json").write_text(json.dumps({
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "SAMPLE_ID": P.SAMPLE_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "OUTCOME": P.SOURCE_POPULATION_LIMITATION,
        "TERMINAL_REPORT_SHA256": sha(p),
        "SUFFICIENCY_VERDICT_SHA256": sha(OUT / "10_SUFFICIENCY_VERDICT.json"),
        "REFERENCE_A_SHA256": sha(OUT / "04_REFERENCE_A.json"),
        "SAMPLE_FREEZE_SHA256": samp["SAMPLE_FREEZE_SHA256"],
        "A19_WAS_NEVER_RUN_ON_THIS_SAMPLE": True,
        "files": len(files),
        "FREEZE_SHA256": freeze,
        "FILES": {k: files[k] for k in sorted(files)},
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"OUTCOME": rec["OUTCOME"],
                      "openings_established": ref["RELATION_DISTRIBUTION"]
                          .get(P.OPENING_IN_SEPARATOR, 0),
                      "required": P.MIN_EXAMPLES_TO_CARRY_A_RATE,
                      "TERMINAL_REPORT_SHA256": sha(p),
                      "FREEZE_SHA256": freeze,
                      "files": len(files)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
