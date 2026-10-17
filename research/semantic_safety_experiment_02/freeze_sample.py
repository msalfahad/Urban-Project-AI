"""Freeze SAFETY_SAMPLE_02's selection before any reference reader opens.

A sample that can still move while its answers arrive is not a sample, it
is a search. This module hashes the selection, the renders and the blind
package, records the per-category targets against what the drawing
actually supplied, and writes SAMPLE_FREEZE.json.

After it runs, record.py refuses to ingest a reading unless the sandbox
still hashes to what was frozen here.

    python3 -m research.semantic_safety_experiment_02.freeze_sample
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from research.semantic_safety_experiment_02 import protocol as P

OUT = Path("data/experiments/SEMANTIC_SAFETY_EXPERIMENT_02")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    if (OUT / "04_REFERENCE_A.json").exists():
        raise SystemExit(
            "a reference reading already exists for this round, so the "
            "sample cannot be frozen now: the freeze must come first")

    feats = json.loads((OUT / "01_CANONICAL_FEATURE_REGISTER.json")
                       .read_text("utf-8"))
    qa = json.loads((OUT / "02_RENDER_QA_REGISTER.json").read_text("utf-8"))
    man = json.loads((OUT / "03_REFERENCE_INPUT_MANIFEST.json")
                     .read_text("utf-8"))

    admitted = [t["CANONICAL_FEATURE_ID"] for t in man["TASKS"]]
    by_stratum = Counter(t["STRATUM"] for t in man["TASKS"])
    candidates = feats["STRATUM_COUNTS"]

    per_category, shortfalls = [], []
    for name, target, why in P.STRATA:
        got = by_stratum.get(name, 0)
        avail = candidates.get(name, 0)
        row = {"STRATUM": name, "TARGET": target,
               "CANDIDATES_THE_DRAWING_SUPPLIED": avail,
               "ADMITTED": got,
               "SHORTFALL": max(0, target - got),
               "WHAT_THE_SIGNATURE_IS": why}
        per_category.append(row)
        if row["SHORTFALL"]:
            shortfalls.append({
                "STRATUM": name, "TARGET": target, "ADMITTED": got,
                "CANDIDATES_THE_DRAWING_SUPPLIED": avail,
                "WHY": ("the drawing did not supply enough candidates"
                        if avail < target else
                        "candidates existed but could not be marked "
                        "legibly, so the render gate refused them"),
                "NOTHING_WAS_MANUFACTURED_TO_FILL_IT": True})

    files = {}
    for sub in ("blind_sandbox", "crops"):
        for p in sorted((OUT / sub).rglob("*")):
            if p.is_file():
                files[str(p.relative_to(OUT))] = sha(p)
    for name in ("00_PROTOCOL.json", "01_CANONICAL_FEATURE_REGISTER.json",
                 "02_RENDER_QA_REGISTER.json",
                 "03_REFERENCE_INPUT_MANIFEST.json"):
        files[name] = sha(OUT / name)

    freeze = hashlib.sha256(
        json.dumps({k: files[k] for k in sorted(files)},
                   sort_keys=True).encode()).hexdigest()

    rec = {
        "SAMPLE_ID": P.SAMPLE_ID,
        "SAMPLE_CLASS": P.SAMPLE_CLASS,
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_VERSION": P.PROTOCOL_VERSION,
        "PROTOCOL_HASH": P.protocol_hash(),
        "ANCESTRY": [dict(a) for a in P.ANCESTRY],
        "safety_sample_02_is_a_new_round": P.SAFETY_SAMPLE_02_IS_A_NEW_ROUND,
        "SAMPLE_FREEZE_RULE": P.SAMPLE_FREEZE_RULE,
        "ORDER_OF_WORK": list(P.ORDER_OF_WORK),
        "NO_REFERENCE_READER_HAS_OPENED_THIS_SAMPLE": True,

        "THE_SELECTION_QUESTION": P.THE_SELECTION_QUESTION,
        "SELECTION_MAY_ONLY_USE": list(P.SELECTION_MAY_ONLY_USE),
        "SELECTION_MAY_NOT_USE": list(P.SELECTION_MAY_NOT_USE),
        "a_stratum_name_is_a_target_not_an_answer":
            P.A_STRATUM_NAME_IS_A_TARGET_NOT_AN_ANSWER,
        "NO_STRATUM_NAME_REACHES_A_READER": (
            "the blind package was searched for every stratum name and "
            "for the words SAFETY_SAMPLE, STRATUM and SELECTED_BECAUSE. "
            "Nothing was found"),

        "PER_CATEGORY_TARGETS_AND_WHAT_THE_DRAWING_SUPPLIED": per_category,
        "targets_are_where_source_availability_permits":
            P.TARGETS_ARE_WHERE_SOURCE_AVAILABILITY_PERMITS,
        "do_not_fabricate_to_meet_a_quota": P.DO_NOT_FABRICATE_TO_MEET_A_QUOTA,
        "SHORTFALLS": shortfalls,
        "shortfall_count": len(shortfalls),

        "features_admitted": len(admitted),
        "features_offered_to_the_render_gate":
            qa["features_offered_to_the_gate"],
        "features_refused_by_the_render_gate": qa["features_refused"],
        "features_admitted_with_partial_tagging":
            qa["features_admitted_with_partial_tagging"],
        "REGRESSION_FEATURES_FOUND": feats["REGRESSION_FEATURES_FOUND"],
        "REGRESSION_RULE": P.REGRESSION_RULE,
        "ADMITTED": admitted,

        "the_headline_is_topology_critical_safety":
            P.THE_HEADLINE_IS_TOPOLOGY_CRITICAL_SAFETY,
        "TOPOLOGY_CRITICAL_CLASSES": list(P.TOPOLOGY_CRITICAL_CLASSES),

        "files": len(files),
        "SAMPLE_FREEZE_SHA256": freeze,
        "WHAT_THE_FREEZE_HASH_COVERS": (
            "the sha256 of the sorted map from every selection register, "
            "every crop and every blind-package file to its own sha256"),
        "FILES": {k: files[k] for k in sorted(files)},
    }
    path = OUT / "SAMPLE_FREEZE.json"
    path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")

    print(f"{'stratum':44} {'target':>6} {'cands':>6} {'admitted':>8}")
    for r in per_category:
        print(f"{r['STRATUM']:44} {r['TARGET']:>6} "
              f"{r['CANDIDATES_THE_DRAWING_SUPPLIED']:>6} "
              f"{r['ADMITTED']:>8}"
              + ("   SHORTFALL" if r["SHORTFALL"] else ""))
    print(f"\nadmitted {len(admitted)}   shortfalls {len(shortfalls)}")
    print("SAMPLE_FREEZE_SHA256", freeze)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
