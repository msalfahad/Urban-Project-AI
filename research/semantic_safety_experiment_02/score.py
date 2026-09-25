"""Score A19 against the established reference, under rules frozen first.

This module refuses to run until the reference registers exist, so that
no scoring rule can be written, adjusted or softened after seeing what
A19 said. The two scoring defects found in SEMANTIC_EDGE_SCORING_01 are
carried forward as fixed behaviour, not rediscovered:

  - a claim about a SET of members is compared MEMBER BY MEMBER, never
    joined to the feature last-one-wins
  - an ABSTENTION is not a false positive. UNRESOLVED asserts nothing,
    and the critical-error gate counts only what A19 ASSERTED

Run it with
    python3 -m research.semantic_safety_experiment_02.score
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.semantic_safety_experiment_02 import protocol as P

OUT = Path("data/experiments/SEMANTIC_SAFETY_EXPERIMENT_02")

REQUIRED_BEFORE_SCORING = (
    "04_REFERENCE_A.json",
    "05_REFERENCE_B.json",
    "06_REFERENCE_CONFLICTS.json",
)

SEPARATING = set(P.SEPARATING)
NOT_SEPARATING = set(P.NOT_SEPARATING)


def write(path: Path, body) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                               default=str) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(name):
    return json.loads((OUT / name).read_text("utf-8"))


def _gate():
    missing = [n for n in REQUIRED_BEFORE_SCORING
               if not (OUT / n).exists()]
    if missing:
        raise SystemExit(
            "the reference is not frozen yet, so nothing may be scored: "
            f"missing {missing}")


def established():
    """What the reference has ESTABLISHED, and what it has not.

    A geometry-changing relation needs two independent readings that
    agree. One reading, or two that disagree, is not truth and is not
    scored as truth.
    """
    a = _load("04_REFERENCE_A.json")
    conf = _load("06_REFERENCE_CONFLICTS.json")
    in_conflict = set(conf["IN_CONFLICT_AND_THEREFORE_NOT_ESTABLISHED"])
    unread = set(conf["SECOND_READING_MISSING"])

    out = {}
    for r in a["READINGS"]:
        fid = r["CANONICAL_FEATURE_ID"]
        rel = r["REFERENCE_RELATION"]
        if fid in in_conflict:
            state = P.REFERENCE_CONFLICT
        elif fid in unread:
            state = "SECOND_READING_MISSING"
        elif rel == P.RELATION_UNRESOLVED:
            state = P.REFERENCE_UNRESOLVED
        else:
            state = "ESTABLISHED"
        out[fid] = {"RELATION": rel, "STATE": state,
                    "STRATUM": r.get("STRATUM"),
                    "CONFIDENCE": r.get("REFERENCE_CONFIDENCE"),
                    "ASSEMBLY_TYPE": r.get("ASSEMBLY_TYPE"),
                    "ENTITY": {e["MEMBER_LABEL"]: e["REFERENCE_ROLE"]
                               for e in (r.get("ENTITY_REFERENCE") or ())}}
    return out


def _critical(a19_rel, ref_rel):
    """Which critical class this disagreement falls in, or None.

    Solid against glazed is NOT folded into either critical class: space
    is divided either way. Glazed against open IS critical: a person can
    walk through one and not the other.
    """
    if a19_rel == ref_rel:
        return None
    if a19_rel == P.RELATION_UNRESOLVED:
        return None          # an abstention asserts nothing
    both_separate = a19_rel in SEPARATING and ref_rel in SEPARATING
    if both_separate:
        return "GLAZED_CONFUSED_WITH_SOLID"
    if a19_rel == P.GLAZED_PHYSICAL_SEPARATOR \
            and ref_rel == P.OPENING_IN_SEPARATOR:
        return "GLAZED_CONFUSED_WITH_OPEN"
    if a19_rel == P.OPENING_IN_SEPARATOR \
            and ref_rel == P.GLAZED_PHYSICAL_SEPARATOR:
        return "GLAZED_CONFUSED_WITH_OPEN"
    if a19_rel in SEPARATING and ref_rel in NOT_SEPARATING:
        return P.CRITICAL_FALSE_SEPARATOR
    if a19_rel in NOT_SEPARATING and ref_rel in SEPARATING:
        return P.CRITICAL_MISSED_SEPARATOR
    return None              # an OBSTACLE disagreement is not a safety class


CRITICAL_CLASSES = (P.CRITICAL_FALSE_SEPARATOR,
                    P.CRITICAL_MISSED_SEPARATOR,
                    "GLAZED_CONFUSED_WITH_OPEN")


def primary():
    ref = established()
    rows_a19 = _load("a19/PRIMARY_RELATIONS.json")["ROWS"]
    got = {r["CANONICAL_FEATURE_ID"]: r for r in rows_a19}

    rows, matrix = [], []
    for fid in sorted(ref):
        r = ref[fid]
        a = got.get(fid)
        a_rel = (a or {}).get("A19_RELATION")
        a_conf = (a or {}).get("A19_CONFIDENCE")
        if a is None:
            outcome = "A19_DID_NOT_ANSWER"
        elif r["STATE"] == P.REFERENCE_CONFLICT:
            outcome = P.REFERENCE_CONFLICT
        elif r["STATE"] == "SECOND_READING_MISSING":
            outcome = "SECOND_READING_MISSING"
        elif r["STATE"] == P.REFERENCE_UNRESOLVED:
            outcome = P.REFERENCE_UNRESOLVED
        elif a_rel == P.RELATION_UNRESOLVED:
            outcome = P.A19_UNRESOLVED
        elif a_rel == r["RELATION"]:
            outcome = P.PHYSICAL_RELATION_EXACT_MATCH
        else:
            outcome = P.PHYSICAL_RELATION_WRONG

        crit = None
        if outcome in (P.PHYSICAL_RELATION_WRONG,
                       P.PHYSICAL_RELATION_EXACT_MATCH):
            crit = _critical(a_rel, r["RELATION"])
        row = {"CANONICAL_FEATURE_ID": fid, "STRATUM": r["STRATUM"],
               "REFERENCE_RELATION": r["RELATION"],
               "REFERENCE_STATE": r["STATE"],
               "A19_RELATION": a_rel, "A19_CONFIDENCE": a_conf,
               "OUTCOME": outcome, "CRITICAL_CLASS": crit,
               "A19_ASSERTED_IT": a_rel not in (None,
                                                P.RELATION_UNRESOLVED)}
        rows.append(row)
        if crit:
            matrix.append(row)

    judged = [r for r in rows if r["OUTCOME"] in
              (P.PHYSICAL_RELATION_EXACT_MATCH, P.PHYSICAL_RELATION_WRONG)]
    high = [r for r in judged if r["A19_CONFIDENCE"] == P.HIGH]
    right = [r for r in judged
             if r["OUTCOME"] == P.PHYSICAL_RELATION_EXACT_MATCH]
    high_right = [r for r in high
                  if r["OUTCOME"] == P.PHYSICAL_RELATION_EXACT_MATCH]

    def bucket(key):
        out = {}
        for r in rows:
            out[str(r[key])] = out.get(str(r[key]), 0) + 1
        return out

    score = {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "the_rules_were_frozen_before_any_answer_existed": True,
        "do_not_hide_the_denominator": P.DO_NOT_HIDE_THE_DENOMINATOR,
        "the_sample_is_not_random": P.THE_SAMPLE_IS_NOT_RANDOM,
        "abstaining_is_not_an_error": P.ABSTAINING_IS_NOT_AN_ERROR,
        "features_in_the_sample": len(ref),
        "OUTCOME_DISTRIBUTION": bucket("OUTCOME"),
        "REFERENCE_STATE_DISTRIBUTION": bucket("REFERENCE_STATE"),
        "relation_accuracy_numerator": len(right),
        "relation_accuracy_denominator": len(judged),
        "high_confidence_accuracy_numerator": len(high_right),
        "high_confidence_accuracy_denominator": len(high),
        "a19_abstained": len([r for r in rows
                              if r["OUTCOME"] == P.A19_UNRESOLVED]),
        "reference_unresolved": len([r for r in rows if r["OUTCOME"]
                                     == P.REFERENCE_UNRESOLVED]),
        "reference_conflict": len([r for r in rows if r["OUTCOME"]
                                   == P.REFERENCE_CONFLICT]),
        "ROWS": rows,
    }
    return score, rows, matrix


def critical_matrix(matrix):
    """Every critical error, split by whether A19 ASSERTED it.

    An abstention is not a false positive. This split is the fix carried
    forward from SEMANTIC_EDGE_SCORING_01, where counting every entry in
    this matrix turned three abstentions into three errors.
    """
    asserted = [r for r in matrix if r["A19_ASSERTED_IT"]]
    hard = [r for r in asserted if r["CRITICAL_CLASS"] in CRITICAL_CLASSES]
    high = [r for r in hard if r["A19_CONFIDENCE"] == P.HIGH]
    return {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "CRITICAL_DEFINITIONS": [list(x) for x in P.CRITICAL_DEFINITIONS],
        "the_asymmetric_gate": P.THE_ASYMMETRIC_GATE,
        "SOLID_AGAINST_GLAZED_IS_REPORTED_APART": (
            "space is divided either way, so it is never folded into a "
            "critical class"),
        "entries": len(matrix),
        "asserted_by_a19": len(asserted),
        "critical_errors": len(hard),
        "high_confidence_critical_errors": len(high),
        "BY_CLASS": {c: len([r for r in asserted
                             if r["CRITICAL_CLASS"] == c])
                     for c in [x[0] for x in P.CRITICAL_DEFINITIONS]},
        "HIGH_CONFIDENCE_CRITICAL_ERRORS": high,
        "EVERY_ENTRY": matrix,
    }, hard, high


def topology_critical(prim_rows):
    """THE HEADLINE. Per-class safety, each with its own denominator.

    An aggregate hides exactly the thing that matters. A reader right
    about thirty-five annotation lines and wrong about the one doorway
    scores well and builds the wrong building. So each topology-critical
    class is reported on its own, twice over:

      RECALL     of the features the reference ESTABLISHES as this class,
                 how many did A19 call this class? Missing them is the
                 dangerous direction for SEPARATOR and OPENING alike
      PRECISION  of the features A19 CALLS this class, how many does the
                 reference establish as it? This is where a false
                 separator shows up

    A class with two examples must not be able to look like a class with
    twenty, so every row carries its counts and never a bare rate.
    """
    rows = []
    for cls in P.TOPOLOGY_CRITICAL_CLASSES:
        judged = [r for r in prim_rows if r["OUTCOME"] in
                  (P.PHYSICAL_RELATION_EXACT_MATCH,
                   P.PHYSICAL_RELATION_WRONG, P.A19_UNRESOLVED)]
        ref_is = [r for r in judged if r["REFERENCE_RELATION"] == cls]
        a19_is = [r for r in judged if r["A19_RELATION"] == cls]
        hit = [r for r in ref_is if r["A19_RELATION"] == cls]
        missed = [r for r in ref_is if r["A19_RELATION"] != cls]
        false = [r for r in a19_is if r["REFERENCE_RELATION"] != cls]
        high_false = [r for r in false if r["A19_CONFIDENCE"] == P.HIGH]
        rows.append({
            "CLASS": cls,
            "reference_established_this_class": len(ref_is),
            "a19_called_this_class": len(a19_is),
            "recall_numerator": len(hit),
            "recall_denominator": len(ref_is),
            "precision_numerator": len(hit),
            "precision_denominator": len(a19_is),
            "A19_MISSED_IT": [r["CANONICAL_FEATURE_ID"] for r in missed],
            "A19_CALLED_IT_THIS_WRONGLY":
                [r["CANONICAL_FEATURE_ID"] for r in false],
            "high_confidence_false_calls": len(high_false),
            "THE_DENOMINATOR_IS_SMALL": len(ref_is) < 5,
        })
    thin = [r["CLASS"] for r in rows if r["THE_DENOMINATOR_IS_SMALL"]]
    return {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "SAMPLE_ID": P.SAMPLE_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "THIS_IS_THE_HEADLINE": P.THE_HEADLINE_IS_TOPOLOGY_CRITICAL_SAFETY,
        "aggregate_accuracy_is_reported_but_is_not_the_headline":
            P.AGGREGATE_ACCURACY_IS_REPORTED_BUT_IS_NOT_THE_HEADLINE,
        "BY_CLASS": rows,
        "CLASSES_WITH_TOO_FEW_EXAMPLES_TO_CARRY_A_RATE": thin,
        "WHAT_A_THIN_CLASS_MEANS": (
            "a class the drawing gave fewer than five established "
            "examples of cannot support a rate. Its counts are reported "
            "and no percentage is computed from them, because a "
            "percentage over three cases reads like a measurement and "
            "is not one"),
        "do_not_hide_the_denominator": P.DO_NOT_HIDE_THE_DENOMINATOR,
        "the_sample_is_not_random": P.THE_SAMPLE_IS_NOT_RANDOM,
    }, thin


def assembly():
    ref = established()
    rows = _load("a19/ASSEMBLY_ASSERTIONS.json")["ROWS"]
    got = {r["CANONICAL_FEATURE_ID"]: r for r in rows}
    out, right, judged = [], 0, 0
    for fid in sorted(ref):
        want = ref[fid]["ASSEMBLY_TYPE"]
        have = (got.get(fid) or {}).get("ASSEMBLY_TYPE")
        state = ("REFERENCE_DID_NOT_SAY" if want is None else
                 "A19_DID_NOT_SAY" if have is None else
                 "MATCH" if have == want else "WRONG")
        if state in ("MATCH", "WRONG"):
            judged += 1
            right += state == "MATCH"
        out.append({"CANONICAL_FEATURE_ID": fid,
                    "REFERENCE_ASSEMBLY_TYPE": want,
                    "A19_ASSEMBLY_TYPE": have, "OUTCOME": state})
    return {"EXPERIMENT_ID": P.EXPERIMENT_ID,
            "PROTOCOL_HASH": P.protocol_hash(),
            "assembly_accuracy_numerator": right,
            "assembly_accuracy_denominator": judged,
            "ROWS": out}


def checker_value(prim_rows):
    """What the checker was WORTH, not whether it agreed.

    CHECKER_AGREE is not CORRECT. The only question asked here is whether
    the checker caught an A19 mistake the reference confirms, and whether
    it missed one. Agreement with a correct A19 buys nothing and is
    reported separately so it cannot be read as corroboration.
    """
    path = OUT / "checker" / "CHECKER_ANSWERS.json"
    if not path.exists():
        return {"CHECKER_DID_NOT_RUN": True}
    got = {r["CANONICAL_FEATURE_ID"]: r
           for r in json.loads(path.read_text("utf-8"))["ROWS"]}

    def says_separator(ans):
        return {"YES": True, "GLAZED": True, "NO": False, "OPENING": False,
                "OBSTACLE": False}.get(ans)

    caught, missed, agreed_right, no_answer, rows = 0, 0, 0, 0, []
    for r in prim_rows:
        fid = r["CANONICAL_FEATURE_ID"]
        c = got.get(fid)
        if c is None:
            no_answer += 1
            continue
        if r["OUTCOME"] not in (P.PHYSICAL_RELATION_EXACT_MATCH,
                                P.PHYSICAL_RELATION_WRONG):
            continue
        ck = says_separator(c["CHECKER_ANSWER"])
        a19_sep = r["A19_RELATION"] in SEPARATING
        ref_sep = r["REFERENCE_RELATION"] in SEPARATING
        a19_wrong = r["OUTCOME"] == P.PHYSICAL_RELATION_WRONG
        verdict = "CHECKER_ABSTAINED" if ck is None else (
            "CAUGHT_AN_A19_MISTAKE" if (a19_wrong and ck == ref_sep
                                        and a19_sep != ref_sep) else
            "MISSED_AN_A19_MISTAKE" if (a19_wrong and ck == a19_sep
                                        and a19_sep != ref_sep) else
            "AGREED_WITH_A_CORRECT_A19" if (not a19_wrong
                                            and ck == ref_sep) else
            "DISAGREED_WITH_A_CORRECT_A19" if not a19_wrong else
            "BOTH_WRONG_ABOUT_SEPARATION")
        caught += verdict == "CAUGHT_AN_A19_MISTAKE"
        missed += verdict == "MISSED_AN_A19_MISTAKE"
        agreed_right += verdict == "AGREED_WITH_A_CORRECT_A19"
        rows.append({"CANONICAL_FEATURE_ID": fid,
                     "CHECKER_ANSWER": c["CHECKER_ANSWER"],
                     "CHECKER_CONFIDENCE": c["CHECKER_CONFIDENCE"],
                     "A19_RELATION": r["A19_RELATION"],
                     "REFERENCE_RELATION": r["REFERENCE_RELATION"],
                     "VERDICT": verdict})
    return {"EXPERIMENT_ID": P.EXPERIMENT_ID,
            "PROTOCOL_HASH": P.protocol_hash(),
            "CHECKER_QUESTION": P.CHECKER_QUESTION,
            "no_voting": P.NO_VOTING,
            "AGREEMENT_IS_NOT_ACCURACY": (
                "agreement with a correct A19 is reported apart and is "
                "never counted as corroboration"),
            "a19_mistakes_the_checker_caught": caught,
            "a19_mistakes_the_checker_missed": missed,
            "agreed_with_a_correct_a19": agreed_right,
            "features_the_checker_did_not_answer": no_answer,
            "ROWS": rows}


def confidence(prim_rows):
    """Is HIGH confidence worth anything here?"""
    out = {}
    for c in P.CONFIDENCE_CLASSES:
        judged = [r for r in prim_rows
                  if r["A19_CONFIDENCE"] == c and r["OUTCOME"] in
                  (P.PHYSICAL_RELATION_EXACT_MATCH,
                   P.PHYSICAL_RELATION_WRONG)]
        right = [r for r in judged
                 if r["OUTCOME"] == P.PHYSICAL_RELATION_EXACT_MATCH]
        out[c] = {"numerator": len(right), "denominator": len(judged)}
    return {"EXPERIMENT_ID": P.EXPERIMENT_ID,
            "PROTOCOL_HASH": P.protocol_hash(),
            "BY_CONFIDENCE": out,
            "do_not_hide_the_denominator": P.DO_NOT_HIDE_THE_DENOMINATOR}


def authority(prim, hard, high, checker):
    """The first declared rule that fits, read in order."""
    judged = prim["high_confidence_accuracy_denominator"]
    num = prim["high_confidence_accuracy_numerator"]
    acc = (num / judged) if judged else None
    resolved = prim["relation_accuracy_denominator"]
    reasons = []

    if high:
        level, why = P.LEVEL_0, ("a HIGH-confidence critical "
                                 "physical-relation error occurred")
    elif resolved < 10:
        level, why = P.LEVEL_0, ("fewer than ten reference-resolved "
                                 "features to judge on")
    elif acc is not None and acc <= 2 / 3:
        level, why = P.LEVEL_0, ("high-confidence relation accuracy at or "
                                 "below two thirds")
    elif hard:
        level, why = P.LEVEL_1, ("a critical error occurred below HIGH "
                                 "confidence")
    elif acc is not None and acc < 0.9:
        level, why = P.LEVEL_1, ("high-confidence relation accuracy below "
                                 "nine in ten")
    else:
        corroborated = (isinstance(checker, dict)
                        and not checker.get("CHECKER_DID_NOT_RUN")
                        and checker.get("a19_mistakes_the_checker_missed")
                        == 0
                        and checker.get("features_the_checker_did_not_"
                                        "answer") == 0)
        level = P.LEVEL_3 if corroborated else P.LEVEL_2
        why = ("no critical error at any confidence and high-confidence "
               "accuracy of nine in ten or better"
               + (", independently corroborated by the checker"
                  if corroborated else
                  ", but the checker does not corroborate every "
                  "high-confidence relation"))
    return {"AUTHORITY_LEVEL": level, "BECAUSE": why,
            "MEANING": P.LEVEL_MEANING[level],
            "high_confidence_accuracy_numerator": num,
            "high_confidence_accuracy_denominator": judged,
            "reference_resolved_features": resolved,
            "critical_errors": len(hard),
            "high_confidence_critical_errors": len(high),
            "level_4_is_not_reachable_here": P.LEVEL_4_IS_NOT_REACHABLE_HERE,
            "do_not_promote_on_one_project": P.DO_NOT_PROMOTE_ON_ONE_PROJECT,
            "reasons_in_declared_order": reasons}


def main() -> int:
    _gate()
    prim, rows, matrix = primary()
    mat, hard, high = critical_matrix(matrix)
    ck = checker_value(rows)
    topo, thin = topology_critical(rows)
    hashes = {
        "TOPOLOGY_CRITICAL_SCORE.json":
            write(OUT / "scores" / "TOPOLOGY_CRITICAL_SCORE.json", topo),
        "PRIMARY_RELATION_SCORE.json":
            write(OUT / "scores" / "PRIMARY_RELATION_SCORE.json", prim),
        "CRITICAL_ERROR_MATRIX.json":
            write(OUT / "scores" / "CRITICAL_ERROR_MATRIX.json", mat),
        "ASSEMBLY_SCORE.json":
            write(OUT / "scores" / "ASSEMBLY_SCORE.json", assembly()),
        "CHECKER_VALUE.json":
            write(OUT / "scores" / "CHECKER_VALUE.json", ck),
        "CONFIDENCE_SCORE.json":
            write(OUT / "scores" / "CONFIDENCE_SCORE.json",
                  confidence(rows)),
    }
    auth = authority(prim, hard, high, ck)
    hashes["AUTHORITY.json"] = write(OUT / "scores" / "AUTHORITY.json", auth)
    print(json.dumps({"THE_HEADLINE_PER_CLASS": [
                          {"CLASS": r["CLASS"],
                           "recall": [r["recall_numerator"],
                                      r["recall_denominator"]],
                           "precision": [r["precision_numerator"],
                                         r["precision_denominator"]]}
                          for r in topo["BY_CLASS"]],
                      "CLASSES_TOO_THIN_TO_CARRY_A_RATE": thin,
                      "relation_accuracy":
                      [prim["relation_accuracy_numerator"],
                       prim["relation_accuracy_denominator"]],
                      "high_confidence_accuracy":
                      [prim["high_confidence_accuracy_numerator"],
                       prim["high_confidence_accuracy_denominator"]],
                      "critical_errors": len(hard),
                      "high_confidence_critical_errors": len(high),
                      "AUTHORITY_LEVEL": auth["AUTHORITY_LEVEL"],
                      "SHA256": hashes}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
