"""Write SAFETY_SAMPLE_01's result record, and verify it still stands.

SAFETY_SAMPLE_01 is not a failed draft and is not superseded. It was run
honestly, start to finish, and it measured something true about the
sampling strategy. It is preserved exactly as run, hashed, and never
re-scored or re-read. This module records its finding and confirms the
preserved files have not moved since.

    python3 -m research.semantic_safety_experiment_02.apparatus_result_01
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from research.semantic_safety_experiment_02 import protocol as P

OUT = Path("data/experiments/SEMANTIC_SAFETY_EXPERIMENT_02")
KEEP = OUT / "safety_sample_01_apparatus_result"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    if not KEEP.exists():
        raise SystemExit(f"SAFETY_SAMPLE_01 is not preserved at {KEEP}")

    ref = json.loads((KEEP / "04_REFERENCE_A.json").read_text("utf-8"))
    dist = ref["RELATION_DISTRIBUTION"]
    files = {str(p.relative_to(KEEP)): sha(p)
             for p in sorted(KEEP.rglob("*"))
             if p.is_file() and p.name != "APPARATUS_RESULT.json"}

    rec = {
        "SAMPLE_ID": "SAFETY_SAMPLE_01",
        "RESULT_CLASS": "APPARATUS_AND_SAMPLING_RESULT",
        "THIS_IS_NOT_A_FAILED_DRAFT": (
            "it was run honestly, start to finish, and it measured "
            "something true about the sampling strategy. It is preserved "
            "exactly as run and it is not overwritten, re-scored or "
            "re-read"),
        "THE_FINDING": (
            "THE SOURCE-SIGNATURE SAMPLING STRATEGY DID NOT PROVIDE "
            "ENOUGH OPENING AND GLAZED_PHYSICAL_SEPARATOR EXAMPLES TO "
            "ANSWER THE SAFETY QUESTION"),
        "WHAT_THE_BLIND_REFERENCE_ACTUALLY_READ": dist,
        "features_read": ref.get("features_read"),
        "openings_found": dist.get(P.OPENING_IN_SEPARATOR, 0),
        "glazed_separators_found": dist.get(P.GLAZED_PHYSICAL_SEPARATOR, 0),
        "annotation_found": dist.get(P.ANNOTATION_OR_DIMENSION, 0),
        "WHY_THAT_CANNOT_ANSWER_THE_QUESTION": (
            "a question about PHYSICAL SEPARATOR against OPENING cannot "
            "be answered on one opening and one glazed separator. An "
            "authority level rested on them would be a number standing "
            "in for evidence that is not there"),
        "WHY_THE_SIGNATURES_WERE_TOO_WEAK": (
            "they were mechanical properties of the drawing - a pair at "
            "a wall thickness, a member on an opening layer, door "
            "geometry near, a fitted-unit offset - chosen to make a "
            "category likely without presupposing it. On this drawing an "
            "annotation line can sit near a door, cross a wall thickness "
            "and run along the envelope, and it does"),
        "PROTOCOL_VERSION": 3,
        "PROTOCOL_HASH": P.SUPERSEDED_PROTOCOL_V3_HASH,
        "SUCCESSOR": {
            "SAMPLE_ID": P.SAMPLE_ID,
            "RELATION": "NEW_TARGETED_ROUND_NOT_A_CORRECTION",
            "safety_sample_02_is_a_new_round":
                P.SAFETY_SAMPLE_02_IS_A_NEW_ROUND,
        },
        "ITS_ANSWERS_TOOK_NO_PART_IN_SELECTING_SAFETY_SAMPLE_02": (
            "selecting on the answer is the one thing that would make "
            "the new round worthless. SAFETY_SAMPLE_02 is stratified on "
            "frozen deterministic evidence only, and this reference's "
            "labels are not among the inputs to that selection"),
        "files": len(files),
        "FILES": files,
    }
    (KEEP / "APPARATUS_RESULT.json").write_text(
        json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    old = KEEP / "WHY_THIS_SAMPLE_IS_SUPERSEDED.json"
    if old.exists():
        old.unlink()          # the sample is a result, not a supersession
    print(json.dumps({
        "SAMPLE_ID": "SAFETY_SAMPLE_01",
        "features_read": rec["features_read"],
        "openings_found": rec["openings_found"],
        "glazed_separators_found": rec["glazed_separators_found"],
        "annotation_found": rec["annotation_found"],
        "files_preserved": len(files),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
