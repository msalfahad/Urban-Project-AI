"""Freeze the experiment: hash every artefact, then state the decision.

Nothing here computes a score or decides a level. It reads what the
frozen registers already say, records the sixteen items §20 asks for, and
hashes the lot. If a register is missing it says so rather than filling
the gap.

    python3 -m research.semantic_safety_experiment_02.freeze
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.semantic_safety_experiment_02 import protocol as P

OUT = Path("data/experiments/SEMANTIC_SAFETY_EXPERIMENT_02")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(path: Path, body) -> str:
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                               default=str) + "\n", encoding="utf-8")
    return sha(path)


def read(name):
    p = OUT / name
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def decision() -> dict:
    prim = read("scores/PRIMARY_RELATION_SCORE.json")
    mat = read("scores/CRITICAL_ERROR_MATRIX.json")
    auth = read("scores/AUTHORITY.json")
    ck = read("scores/CHECKER_VALUE.json")
    asm = read("scores/ASSEMBLY_SCORE.json")
    conf = read("scores/CONFIDENCE_SCORE.json")
    refa = read("04_REFERENCE_A.json")
    confl = read("06_REFERENCE_CONFLICTS.json")
    qa = read("02_RENDER_QA_REGISTER.json")
    feats = read("01_CANONICAL_FEATURE_REGISTER.json")
    esc = read("a19/CONTEXT_ESCALATIONS.json")
    missing = [n for n, v in (
        ("PRIMARY_RELATION_SCORE", prim), ("CRITICAL_ERROR_MATRIX", mat),
        ("AUTHORITY", auth), ("REFERENCE_A", refa),
        ("REFERENCE_CONFLICTS", confl)) if v is None]

    topo = read("scores/TOPOLOGY_CRITICAL_SCORE.json")
    samp = read("SAMPLE_FREEZE.json")
    return {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "SAMPLE_ID": P.SAMPLE_ID,
        "SAMPLE_CLASS": P.SAMPLE_CLASS,
        "ANCESTRY": [dict(a) for a in P.ANCESTRY],
        "safety_sample_02_is_a_new_round": P.SAFETY_SAMPLE_02_IS_A_NEW_ROUND,

        # ---- THE HEADLINE, first, before any aggregate ----
        "HEADLINE_TOPOLOGY_CRITICAL_SAFETY": {
            "this_is_the_headline":
                P.THE_HEADLINE_IS_TOPOLOGY_CRITICAL_SAFETY,
            "BY_CLASS": (topo or {}).get("BY_CLASS"),
            "CLASSES_WITH_TOO_FEW_EXAMPLES_TO_CARRY_A_RATE":
                (topo or {}).get(
                    "CLASSES_WITH_TOO_FEW_EXAMPLES_TO_CARRY_A_RATE"),
            "WHAT_A_THIN_CLASS_MEANS": (topo or {}).get(
                "WHAT_A_THIN_CLASS_MEANS"),
        },
        "SAMPLE_FREEZE_SHA256": (samp or {}).get("SAMPLE_FREEZE_SHA256"),
        "PER_CATEGORY_TARGETS_AND_WHAT_THE_DRAWING_SUPPLIED":
            (samp or {}).get(
                "PER_CATEGORY_TARGETS_AND_WHAT_THE_DRAWING_SUPPLIED"),
        "SAMPLE_SHORTFALLS": (samp or {}).get("SHORTFALLS"),

        "PROTOCOL_VERSION": P.PROTOCOL_VERSION,
        "PROTOCOL_HASH": P.protocol_hash(),
        "EXPERIMENT_CLASS": P.EXPERIMENT_CLASS,
        "THE_QUESTION": P.THE_QUESTION,
        "THIS_IS_BUILT_TO_FALSIFY_IT": P.THIS_IS_BUILT_TO_FALSIFY_IT,
        "REGISTERS_MISSING": missing,

        "1_SAMPLE_SIZE_AND_STRATA": {
            "features_admitted": (feats or {}).get("features_admitted"),
            "BY_STRATUM": (feats or {}).get("BY_STRATUM"),
            "the_sample_is_not_random": P.THE_SAMPLE_IS_NOT_RANDOM,
        },
        "2_RENDER_GATE": {
            "features_rejected_for_illegible_markup":
                (feats or {}).get("features_rejected"),
            "partial_tagging_admissions":
                (feats or {}).get("partial_tagging_admissions"),
            "the_reader_is_not_asked_to_work_around_bad_markup":
                P.THE_READER_IS_NOT_ASKED_TO_WORK_AROUND_BAD_MARKUP,
        },
        "3_REFERENCE_DISTRIBUTION":
            (refa or {}).get("RELATION_DISTRIBUTION"),
        "4_DUAL_REFERENCE": {
            "required": (confl or {}).get(
                "features_requiring_a_second_reading"),
            "agreed": (confl or {}).get("agreed"),
            "in_conflict": (confl or {}).get("in_conflict"),
            "no_manufactured_truth": P.NO_MANUFACTURED_TRUTH,
        },
        "5_A19_RELATION_DISTRIBUTION":
            (read("a19/PRIMARY_RELATIONS.json") or {}).get(
                "RELATION_DISTRIBUTION"),
        "6_AGGREGATE_RELATION_ACCURACY_NOT_THE_HEADLINE": {
            "why_it_is_not_the_headline":
                P.AGGREGATE_ACCURACY_IS_REPORTED_BUT_IS_NOT_THE_HEADLINE,
            "numerator": (prim or {}).get("relation_accuracy_numerator"),
            "denominator": (prim or {}).get(
                "relation_accuracy_denominator"),
        },
        "7_HIGH_CONFIDENCE_ACCURACY": {
            "numerator": (prim or {}).get(
                "high_confidence_accuracy_numerator"),
            "denominator": (prim or {}).get(
                "high_confidence_accuracy_denominator"),
        },
        "8_ABSTENTIONS": {
            "a19_abstained": (prim or {}).get("a19_abstained"),
            "abstaining_is_not_an_error": P.ABSTAINING_IS_NOT_AN_ERROR,
        },
        "9_REFERENCE_NOT_ESTABLISHED": {
            "reference_unresolved": (prim or {}).get("reference_unresolved"),
            "reference_conflict": (prim or {}).get("reference_conflict"),
            "do_not_hide_the_denominator": P.DO_NOT_HIDE_THE_DENOMINATOR,
        },
        "10_CRITICAL_ERRORS": {
            "critical_errors": (mat or {}).get("critical_errors"),
            "high_confidence_critical_errors":
                (mat or {}).get("high_confidence_critical_errors"),
            "BY_CLASS": (mat or {}).get("BY_CLASS"),
            "the_asymmetric_gate": P.THE_ASYMMETRIC_GATE,
        },
        "11_SOLID_AGAINST_GLAZED": (mat or {}).get("BY_CLASS", {}).get(
            "GLAZED_CONFUSED_WITH_SOLID"),
        "12_THE_REGRESSION_CASE": {
            "REGRESSION_SOURCE_INTERVALS":
                list(P.REGRESSION_SOURCE_INTERVALS),
            "REGRESSION_RULE": P.REGRESSION_RULE,
            "PARTIAL_TAGGING_RULE": P.PARTIAL_TAGGING_RULE,
        },
        "13_ASSEMBLY_ACCURACY": {
            "numerator": (asm or {}).get("assembly_accuracy_numerator"),
            "denominator": (asm or {}).get("assembly_accuracy_denominator"),
        },
        "14_CHECKER_VALUE": {
            "caught": (ck or {}).get("a19_mistakes_the_checker_caught"),
            "missed": (ck or {}).get("a19_mistakes_the_checker_missed"),
            "agreed_with_a_correct_a19":
                (ck or {}).get("agreed_with_a_correct_a19"),
            "AGREEMENT_IS_NOT_ACCURACY": (
                "agreement is reported, never counted as corroboration"),
        },
        "15_CONFIDENCE_CALIBRATION": (conf or {}).get("BY_CONFIDENCE"),
        "16_AUTHORITY_LEVEL": {
            "AUTHORITY_LEVEL": (auth or {}).get("AUTHORITY_LEVEL"),
            "BECAUSE": (auth or {}).get("BECAUSE"),
            "MEANING": (auth or {}).get("MEANING"),
            "level_4_is_not_reachable_here":
                P.LEVEL_4_IS_NOT_REACHABLE_HERE,
            "do_not_promote_on_one_project":
                P.DO_NOT_PROMOTE_ON_ONE_PROJECT,
        },
        "CONTEXT_ESCALATIONS_TAKEN": (esc or {}).get("escalations_taken"),
        "RENDER_QA_FEATURES": len((qa or {}).get("ROWS") or ()),
        "NOTHING_IS_FED_BACK": P.NOTHING_IS_FED_BACK,
        "NO_QUANTITY_BENCHMARK": P.NO_QUANTITY_BENCHMARK,
        "THE_GATE_IS_NOT_WEAKENED": P.THE_GATE_IS_NOT_WEAKENED,
    }


def main() -> int:
    dec = decision()
    dec_hash = write(OUT / "DECISION_REPORT.json", dec)

    files = {}
    for p in sorted(OUT.rglob("*")):
        if p.is_file() and p.name != "FREEZE.json":
            files[str(p.relative_to(OUT))] = sha(p)

    body = json.dumps({k: files[k] for k in sorted(files)},
                      sort_keys=True).encode()
    freeze = hashlib.sha256(body).hexdigest()
    write(OUT / "FREEZE.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_VERSION": P.PROTOCOL_VERSION,
        "PROTOCOL_HASH": P.protocol_hash(),
        "SUPERSEDED_PROTOCOL_V4_HASH": P.SUPERSEDED_PROTOCOL_V4_HASH,
        "SUPERSEDED_PROTOCOL_V3_HASH": P.SUPERSEDED_PROTOCOL_V3_HASH,
        "DECISION_REPORT_SHA256": dec_hash,
        "FREEZE_SHA256": freeze,
        "WHAT_THE_FREEZE_HASH_COVERS": (
            "the sha256 of the sorted map from every file in this "
            "experiment directory to its own sha256"),
        "files": len(files),
        "FILES": {k: files[k] for k in sorted(files)},
    })
    print(json.dumps({"SAMPLE_ID": P.SAMPLE_ID,
                      "HEADLINE_BY_CLASS": [
                          {"CLASS": r["CLASS"],
                           "recall": [r["recall_numerator"],
                                      r["recall_denominator"]],
                           "precision": [r["precision_numerator"],
                                         r["precision_denominator"]]}
                          for r in (dec["HEADLINE_TOPOLOGY_CRITICAL_SAFETY"]
                                    .get("BY_CLASS") or ())],
                      "FREEZE_SHA256": freeze, "files": len(files),
                      "AUTHORITY_LEVEL":
                          dec["16_AUTHORITY_LEVEL"]["AUTHORITY_LEVEL"],
                      "REGISTERS_MISSING": dec["REGISTERS_MISSING"]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
