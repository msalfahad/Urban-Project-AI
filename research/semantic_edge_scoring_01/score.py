"""Score A19 against the frozen independent reference.

This file refuses to run until 03_REFERENCE_LABEL_REGISTER.json exists.
That is the whole guarantee: the reference was established and hashed
before any A19 answer was opened for comparison.

Nothing here modifies E1.4, feeds a semantic finding into geometry,
computes an area, or opens a quantity benchmark.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.semantic_edge_experiment_01 import protocol as SE
from research.semantic_edge_scoring_01 import protocol as P

EXP = Path("data/experiments/SEMANTIC_EDGE_EXPERIMENT_01")
OUT = Path("data/experiments/SEMANTIC_EDGE_SCORING_01")
SC = OUT / "scores"

FAMILY_OF = {}
for fam, roles in P.ROLE_FAMILIES.items():
    for r in roles:
        FAMILY_OF[r] = fam


def write(path: Path, body) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                               default=str) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _j(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _count(rows, key):
    out = {}
    for r in rows:
        out[str(r.get(key))] = out.get(str(r.get(key)), 0) + 1
    return out


def _frac(n, d):
    return {"n": n, "of": d,
            "as_written": (f"{n} of {d}" if d else "no cases to judge on")}


# ------------------------------------------------------------- assembly

def assembly_outcome(ref_role, a19_roles):
    """One canonical feature's outcome. Declared rules, applied as written."""
    if ref_role is None:
        return P.REFERENCE_UNRESOLVED
    if ref_role == SE.UNRESOLVED_FEATURE:
        return P.REFERENCE_UNRESOLVED
    if not a19_roles:
        return P.A19_UNRESOLVED
    if set(a19_roles) == {SE.UNRESOLVED_FEATURE}:
        return P.A19_UNRESOLVED

    def one(a):
        if a == SE.UNRESOLVED_FEATURE:
            return P.A19_UNRESOLVED
        if a == ref_role:
            return P.EXACT_MATCH
        if SE.MIXED_FEATURE in (a, ref_role):
            return P.COMPATIBLE_PARENT_MATCH
        return P.WRONG_ASSEMBLY

    outs = {one(a) for a in a19_roles}
    if len(outs) == 1:
        return outs.pop()
    return P.INCONSISTENT_WITHIN_CLUSTER


def main() -> int:
    ref_path = OUT / "03_REFERENCE_LABEL_REGISTER.json"
    if not ref_path.exists():
        raise SystemExit("the reference is not frozen; scoring may not run")

    clusters = _j(OUT / "01_CANONICAL_FEATURE_CLUSTER_REGISTER.json")
    ref = _j(ref_path)
    conf = _j(OUT / "04_REFERENCE_CONFLICT_REGISTER.json")
    a19_feat = _j(EXP / "a19" / "PASS_A_FEATURE_ASSERTIONS.json")
    a19_ent = _j(EXP / "a19" / "PASS_A_ENTITY_ASSERTIONS.json")
    a19_rel = _j(EXP / "a19" / "PASS_A_RELATIONS.json")
    checker = _j(EXP / "optional_checker" / "CHECKER_COMPARISON.json")
    artefact = {r["FEATURE_GROUP_ID"]: r for r in
                clusters["CURVE_QUESTION_ARTEFACT"]["ROWS"]}

    cluster_of = {}
    members_of = {}
    for c in clusters["CLUSTERS"]:
        cid = c["CANONICAL_FEATURE_CLUSTER_ID"]
        members_of[cid] = c["MEMBER_FEATURE_GROUP_IDS"]
        for g in c["MEMBER_FEATURE_GROUP_IDS"]:
            cluster_of[g] = cid

    ref_by = {r["CANONICAL_FEATURE_CLUSTER_ID"]: r for r in ref["READINGS"]}
    conflict = {r["CANONICAL_FEATURE_CLUSTER_ID"] for r in
                conf.get("ROWS", []) if r["VERDICT"] == P.REFERENCE_CONFLICT}
    a19_by = {r["FEATURE_GROUP_ID"]: r for r in a19_feat["ANSWERS"]}

    # ---------------- feature assembly ------------------------------
    rows, per_question = [], []
    for cid in sorted(members_of):
        r = ref_by.get(cid) or {}
        ref_role = r.get("REFERENCE_ROLE")
        gs = members_of[cid]
        a19s = [a19_by[g] for g in gs if g in a19_by]
        roles = [a["FEATURE_ASSEMBLY_TYPE"] for a in a19s]
        confs = sorted({a["ASSEMBLY_CONFIDENCE"] for a in a19s})
        if cid in conflict:
            outcome = P.REFERENCE_CONFLICT
        else:
            outcome = assembly_outcome(ref_role, roles)
        rows.append({
            "CANONICAL_FEATURE_CLUSTER_ID": cid,
            "MEMBER_FEATURE_GROUP_IDS": gs,
            "REFERENCE_ROLE": ref_role,
            "REFERENCE_CONFIDENCE": r.get("REFERENCE_CONFIDENCE"),
            "REFERENCE_NEEDS_ADDITIONAL_CONTEXT":
                r.get("NEEDS_ADDITIONAL_CONTEXT"),
            "A19_ROLES": roles,
            "A19_CONFIDENCES": confs,
            "A19_CONFIDENCE": confs[0] if len(confs) == 1 else "MIXED",
            "OUTCOME": outcome,
        })
        for a in a19s:
            if cid in conflict:
                o = P.REFERENCE_CONFLICT
            else:
                o = assembly_outcome(ref_role, [a["FEATURE_ASSEMBLY_TYPE"]])
            per_question.append({
                "FEATURE_GROUP_ID": a["FEATURE_GROUP_ID"],
                "CANONICAL_FEATURE_CLUSTER_ID": cid,
                "REFERENCE_ROLE": ref_role,
                "A19_ROLE": a["FEATURE_ASSEMBLY_TYPE"],
                "A19_CONFIDENCE": a["ASSEMBLY_CONFIDENCE"],
                "OUTCOME": o,
            })

    judgeable = [r for r in rows if r["OUTCOME"] not in
                 (P.REFERENCE_UNRESOLVED, P.REFERENCE_CONFLICT)]
    correct = [r for r in judgeable if r["OUTCOME"] in
               (P.EXACT_MATCH, P.COMPATIBLE_PARENT_MATCH)]
    hi_q = [q for q in per_question if q["A19_CONFIDENCE"] == SE.HIGH
            and q["OUTCOME"] not in (P.REFERENCE_UNRESOLVED,
                                     P.REFERENCE_CONFLICT)]
    hi_correct = [q for q in hi_q if q["OUTCOME"] in
                  (P.EXACT_MATCH, P.COMPATIBLE_PARENT_MATCH)]
    hi_wrong = [q for q in hi_q if q["OUTCOME"] == P.WRONG_ASSEMBLY]
    med_q = [q for q in per_question if q["A19_CONFIDENCE"] == SE.MEDIUM
             and q["OUTCOME"] not in (P.REFERENCE_UNRESOLVED,
                                      P.REFERENCE_CONFLICT)]
    med_correct = [q for q in med_q if q["OUTCOME"] in
                   (P.EXACT_MATCH, P.COMPATIBLE_PARENT_MATCH)]

    fa_hash = write(SC / "FEATURE_ASSEMBLY_SCORE.json", {
        "SCORING_ID": P.SCORING_ID,
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "THE_REFERENCE_WAS_FROZEN_BEFORE_A19_WAS_OPENED": True,
        "REFERENCE_LABEL_REGISTER_SHA256": hashlib.sha256(
            ref_path.read_bytes()).hexdigest(),
        "OUTCOMES": list(P.ASSEMBLY_OUTCOMES),
        "COMPATIBILITY_RULE": P.COMPATIBILITY_RULE,
        "why_inconsistent_within_cluster_exists":
            P.WHY_INCONSISTENT_WITHIN_CLUSTER_EXISTS,
        "high_confidence_wrong_is_the_risk": P.HIGH_CONFIDENCE_WRONG_IS_THE_RISK,
        "do_not_hide_the_denominator": P.DO_NOT_HIDE_THE_DENOMINATOR,
        "canonical_features": len(rows),
        "OUTCOME_DISTRIBUTION": _count(rows, "OUTCOME"),
        "reference_unresolved": sum(
            1 for r in rows if r["OUTCOME"] == P.REFERENCE_UNRESOLVED),
        "reference_conflict": sum(
            1 for r in rows if r["OUTCOME"] == P.REFERENCE_CONFLICT),
        "FEATURE_ASSEMBLY_ACCURACY": _frac(len(correct), len(judgeable)),
        "PER_QUESTION": {
            "questions": len(per_question),
            "OUTCOME_DISTRIBUTION": _count(per_question, "OUTCOME"),
            "BY_A19_CONFIDENCE": {
                c: _count([q for q in per_question
                           if q["A19_CONFIDENCE"] == c], "OUTCOME")
                for c in P.REPORT_BY_A19_CONFIDENCE},
            "HIGH_CONFIDENCE_ACCURACY": _frac(len(hi_correct), len(hi_q)),
            "HIGH_CONFIDENCE_CORRECT": len(hi_correct),
            "HIGH_CONFIDENCE_WRONG": len(hi_wrong),
            "HIGH_CONFIDENCE_WRONG_ROWS": hi_wrong,
            "MEDIUM_CONFIDENCE_ACCURACY": _frac(len(med_correct), len(med_q)),
            "ROWS": per_question,
        },
        "ROWS": rows,
    })

    # ---------------- entity sub-roles -------------------------------
    ref_ent = {}
    for e in ref["ENTITY_REFERENCES"]:
        ref_ent[(e["FEATURE_GROUP_ID"], e["MEMBER_LABEL"])] = e
    ent_rows = []
    for a in a19_ent["ASSERTIONS"]:
        key = (a["FEATURE_GROUP_ID"], a["MEMBER_LABEL"])
        r = ref_ent.get(key)
        a_role, r_role = a.get("SUB_ROLE"), (r or {}).get("REFERENCE_ROLE")
        if r is None or r_role in (None, "UNRESOLVED"):
            out = P.REFERENCE_UNRESOLVED
        elif a_role == "UNRESOLVED":
            out = P.A19_UNRESOLVED
        elif a_role == r_role:
            out = P.EXACT_ROLE_MATCH
        elif (FAMILY_OF.get(a_role) and
              FAMILY_OF.get(a_role) == FAMILY_OF.get(r_role)):
            out = P.COMPATIBLE_ROLE_FAMILY
        else:
            out = P.ROLE_MISMATCH
        ent_rows.append({
            "FEATURE_GROUP_ID": a["FEATURE_GROUP_ID"],
            "CANONICAL_FEATURE_CLUSTER_ID": cluster_of.get(
                a["FEATURE_GROUP_ID"]),
            "MEMBER_LABEL": a["MEMBER_LABEL"],
            "A19_SUB_ROLE": a_role,
            "A19_CONFIDENCE": a.get("CONFIDENCE"),
            "REFERENCE_ROLE": r_role,
            "REFERENCE_CONFIDENCE": (r or {}).get("REFERENCE_CONFIDENCE"),
            "A19_FAMILY": FAMILY_OF.get(a_role),
            "REFERENCE_FAMILY": FAMILY_OF.get(r_role),
            "OUTCOME": out,
        })
    judge_e = [r for r in ent_rows if r["OUTCOME"] not in
               (P.REFERENCE_UNRESOLVED,)]
    ok_e = [r for r in judge_e if r["OUTCOME"] in
            (P.EXACT_ROLE_MATCH, P.COMPATIBLE_ROLE_FAMILY)]
    by_family = {}
    for r in ent_rows:
        fam = r["REFERENCE_FAMILY"] or "REFERENCE_UNRESOLVED"
        by_family.setdefault(fam, {})
        by_family[fam][r["OUTCOME"]] = by_family[fam].get(r["OUTCOME"], 0) + 1
    er_hash = write(SC / "ENTITY_ROLE_SCORE.json", {
        "SCORING_ID": P.SCORING_ID,
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "OUTCOMES": list(P.ROLE_OUTCOMES),
        "ROLE_FAMILIES": {k: list(v) for k, v in P.ROLE_FAMILIES.items()},
        "do_not_mix_the_two_levels": P.DO_NOT_MIX_THE_TWO_LEVELS,
        "do_not_hide_the_denominator": P.DO_NOT_HIDE_THE_DENOMINATOR,
        "a19_entity_assertions": len(ent_rows),
        "reference_entity_references": len(ref_ent),
        "OUTCOME_DISTRIBUTION": _count(ent_rows, "OUTCOME"),
        "ENTITY_ROLE_ACCURACY_EXACT_OR_FAMILY": _frac(
            len(ok_e), len(judge_e)),
        "EXACT_ONLY": _frac(sum(1 for r in judge_e
                                if r["OUTCOME"] == P.EXACT_ROLE_MATCH),
                            len(judge_e)),
        "BY_REFERENCE_FAMILY": by_family,
        "ROWS": ent_rows,
    })

    # ---------------- critical error matrix --------------------------
    crit = {n: [] for n, _, _ in P.CRITICAL_ERRORS}
    for r in ent_rows:
        if r["OUTCOME"] == P.REFERENCE_UNRESOLVED:
            continue
        for name, ref_set, a19_set in P.CRITICAL_ERRORS:
            if r["REFERENCE_ROLE"] in ref_set and r["A19_SUB_ROLE"] in a19_set:
                crit[name].append(r)
    sep_rows = {k: [] for k in P.SEPARATION_ERRORS}
    ref_sep = {}
    for x in ref["REFERENCE_RELATIONS"]:
        if x["RELATION"] in P.SEPARATOR_CLAIMS:
            ref_sep[x["CANONICAL_FEATURE_CLUSTER_ID"]] = \
                P.SEPARATOR_CLAIMS[x["RELATION"]]
    for x in a19_rel["RELATIONS"]:
        if x["RELATION"] not in P.SEPARATOR_CLAIMS:
            continue
        cid = cluster_of.get(x["FEATURE_GROUP_ID"])
        if cid not in ref_sep:
            continue
        a_says = P.SEPARATOR_CLAIMS[x["RELATION"]]
        r_says = ref_sep[cid]
        if a_says == r_says:
            continue
        key = ("PHYSICAL_SEPARATOR_AS_NON_SEPARATOR" if r_says
               else "NON_SEPARATOR_AS_PHYSICAL_SEPARATOR")
        sep_rows[key].append({"CANONICAL_FEATURE_CLUSTER_ID": cid,
                              "FEATURE_GROUP_ID": x["FEATURE_GROUP_ID"],
                              "A19_RELATION": x["RELATION"],
                              "REFERENCE_SAYS_IT_SEPARATES": r_says})
    total_crit = sum(len(v) for v in crit.values()) + sum(
        len(v) for v in sep_rows.values())
    ce_hash = write(SC / "CRITICAL_ERROR_MATRIX.json", {
        "SCORING_ID": P.SCORING_ID,
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "why": P.CRITICAL_ERRORS_MATTER_MORE,
        "THESE_ARE_NEVER_AVERAGED_WITH_SUBTYPE_DISAGREEMENTS": True,
        "critical_errors_total": total_crit,
        "COUNTS": {**{n: len(v) for n, v in crit.items()},
                   **{k: len(v) for k, v in sep_rows.items()}},
        "DEFINITIONS": [{"NAME": n, "REFERENCE_ESTABLISHED": sorted(a),
                         "A19_SAID": sorted(b)}
                        for n, a, b in P.CRITICAL_ERRORS],
        "ROWS": {**{n: v for n, v in crit.items() if v},
                 **{k: v for k, v in sep_rows.items() if v}},
    })

    # ---------------- fenestration -----------------------------------
    fen_rows = []
    for r in rows:
        if r["REFERENCE_ROLE"] != SE.WINDOW_OR_GLAZING_ASSEMBLY:
            continue
        if r["OUTCOME"] == P.REFERENCE_CONFLICT:
            got = P.REFERENCE_CONFLICT
        elif SE.WINDOW_OR_GLAZING_ASSEMBLY in r["A19_ROLES"]:
            got = "A19_DETECTED_ASSEMBLY"
        elif set(r["A19_ROLES"]) <= {SE.UNRESOLVED_FEATURE}:
            got = "A19_UNRESOLVED"
        else:
            got = "A19_MISSED_ASSEMBLY"
        fen_rows.append({**{k: r[k] for k in
                            ("CANONICAL_FEATURE_CLUSTER_ID", "A19_ROLES",
                             "A19_CONFIDENCE", "REFERENCE_CONFIDENCE")},
                         "FENESTRATION_OUTCOME": got})
    sub = [r for r in ent_rows
           if r["REFERENCE_FAMILY"] == "WINDOW"]
    fen_hash = write(SC / "FENESTRATION_SCORE.json", {
        "SCORING_ID": P.SCORING_ID,
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "why": P.WHY_FENESTRATION_HAS_ITS_OWN_SCORE,
        "not_inferred_from_closure": P.FENESTRATION_IS_NOT_INFERRED_FROM_CLOSURE,
        "E1_4_ESTABLISHES_NO_GLAZING_ON_THIS_FLOOR": True,
        "canonical_features_the_reference_calls_fenestration": len(fen_rows),
        "OUTCOME_DISTRIBUTION": _count(fen_rows, "FENESTRATION_OUTCOME"),
        "SUB_ROLE_LEVEL": {
            "reference_window_family_members": len(sub),
            "OUTCOME_DISTRIBUTION": _count(sub, "OUTCOME"),
            "A19_SUB_ROLE_DISTRIBUTION": _count(sub, "A19_SUB_ROLE"),
            "REFERENCE_SUB_ROLE_DISTRIBUTION": _count(sub, "REFERENCE_ROLE"),
            "ROWS": sub,
        },
        "ROWS": fen_rows,
    })

    # ---------------- relations --------------------------------------
    ref_rel_by = {}
    for x in ref["REFERENCE_RELATIONS"]:
        ref_rel_by.setdefault(x["CANONICAL_FEATURE_CLUSTER_ID"],
                              set()).add(x["RELATION"])
    a19_rel_by = {}
    for x in a19_rel["RELATIONS"]:
        cid = cluster_of.get(x["FEATURE_GROUP_ID"])
        if cid:
            a19_rel_by.setdefault(cid, set()).add(x["RELATION"])
    rel_rows = []
    for cid in sorted(members_of):
        a = a19_rel_by.get(cid, set())
        rr = ref_rel_by.get(cid, set())
        for rel in P.RELATIONS_SCORED:
            if rel not in a and rel not in rr:
                continue
            rel_rows.append({
                "CANONICAL_FEATURE_CLUSTER_ID": cid,
                "RELATION": rel,
                "OUTCOME": ("BOTH_ASSERT" if rel in a and rel in rr
                            else "A19_ONLY" if rel in a else "REFERENCE_ONLY"),
            })
    both = sum(1 for r in rel_rows if r["OUTCOME"] == "BOTH_ASSERT")
    rel_hash = write(SC / "RELATION_SCORE.json", {
        "SCORING_ID": P.SCORING_ID,
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "why": P.RELATIONS_MAY_BE_THE_USEFUL_OUTPUT,
        "RELATIONS_SCORED": list(P.RELATIONS_SCORED),
        "WHAT_THIS_MEASURES": (
            "whether A19 and an independent reference make the same "
            "grouping and separation claims about the same feature. A "
            "relation only one of them makes is reported as such, not as "
            "an error, because neither was required to make every claim"),
        "claims_compared": len(rel_rows),
        "OUTCOME_DISTRIBUTION": _count(rel_rows, "OUTCOME"),
        "RELATION_AGREEMENT": _frac(both, len(rel_rows)),
        "BY_RELATION": {rel: _count(
            [r for r in rel_rows if r["RELATION"] == rel], "OUTCOME")
            for rel in P.RELATIONS_SCORED},
        "ROWS": rel_rows,
    })

    # ---------------- the checker's value ----------------------------
    q_by_group = {q["FEATURE_GROUP_ID"]: q for q in per_question}
    chk_rows = []
    for c in checker.get("ROWS", []):
        gid = c["FEATURE_GROUP_ID"]
        q = q_by_group.get(gid)
        if q is None:
            continue
        if q["OUTCOME"] in (P.REFERENCE_UNRESOLVED, P.REFERENCE_CONFLICT):
            cell = "REFERENCE_UNRESOLVED"
        else:
            ok = q["OUTCOME"] in (P.EXACT_MATCH, P.COMPATIBLE_PARENT_MATCH)
            agree = c["COMPARISON"] == "AGREE"
            cell = ("A19_CORRECT_CHECKER_AGREES" if ok and agree else
                    "A19_WRONG_CHECKER_AGREES" if (not ok) and agree else
                    "A19_CORRECT_CHECKER_DISAGREES" if ok else
                    "A19_WRONG_CHECKER_DISAGREES")
        chk_rows.append({"FEATURE_GROUP_ID": gid,
                         "CANONICAL_FEATURE_CLUSTER_ID": cluster_of.get(gid),
                         "A19_OUTCOME": q["OUTCOME"],
                         "CHECKER_COMPARISON": c["COMPARISON"],
                         "CELL": cell})
    cells = _count(chk_rows, "CELL")
    caught = cells.get("A19_WRONG_CHECKER_DISAGREES", 0)
    missed = cells.get("A19_WRONG_CHECKER_AGREES", 0)
    chk_hash = write(SC / "CHECKER_VALUE_SCORE.json", {
        "SCORING_ID": P.SCORING_ID,
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "CELLS": list(P.CHECKER_CELLS),
        "what_it_answers": P.WHAT_THE_CHECKER_TABLE_ANSWERS,
        "CHECKER_AGREEMENT_IS_NEVER_TRUTH": True,
        "agreement_is_not_accuracy": P.AGREEMENT_IS_NOT_ACCURACY,
        "groups_in_the_checker_round": len(chk_rows),
        "CELL_DISTRIBUTION": cells,
        "MISTAKES_THE_CHECKER_CAUGHT": caught,
        "MISTAKES_THE_CHECKER_WAS_BLIND_TO": missed,
        "ROWS": chk_rows,
    })

    # ---------------- coverage analysis, §17 -------------------------
    hi_ok_clusters = sorted({q["CANONICAL_FEATURE_CLUSTER_ID"] for q in hi_correct})
    covered_intervals = set()
    for cid in hi_ok_clusters:
        for c in clusters["CLUSTERS"]:
            if c["CANONICAL_FEATURE_CLUSTER_ID"] == cid:
                covered_intervals |= set(c["PRIMARY_ENTITY_UNION"])
    sample_intervals = set()
    for c in clusters["CLUSTERS"]:
        sample_intervals |= set(c["PRIMARY_ENTITY_UNION"])

    # ---------------- readiness --------------------------------------
    n_judge = len(judgeable)
    hi_acc = (len(hi_correct) / len(hi_q)) if hi_q else 0.0
    ent_acc = (len(ok_e) / len(judge_e)) if judge_e else 0.0
    hi_impact_conflicts = sum(
        1 for r in conf.get("ROWS", [])
        if r["VERDICT"] == P.REFERENCE_CONFLICT)

    if total_crit or hi_acc <= 0.5 or n_judge < 5:
        readiness = P.A19_NOT_READY
    elif hi_acc < 0.8 or hi_wrong:
        readiness = P.A19_DIAGNOSTIC_ONLY
    elif hi_impact_conflicts == 0 and ent_acc >= 0.8:
        readiness = P.A19_STRONG_SEMANTIC_EVIDENCE
    else:
        readiness = P.A19_CANDIDATE_SEMANTIC_EVIDENCE

    which = next(r for c, r in P.READINESS_RULES if c == readiness)
    dec_hash = write(OUT / "DECISION_REPORT.json", {
        "SCORING_ID": P.SCORING_ID,
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "E1_4_IS_NOT_MODIFIED": True,
        "E1_4_RUN_HASH": P.E1_4_RUN_HASH,
        "NO_GEOMETRY_WAS_MODIFIED_BY_ANY_OF_THIS": True,
        "nothing_is_fed_back": P.NOTHING_IS_FED_BACK,
        "no_quantity_benchmark": P.NO_QUANTITY_BENCHMARK,
        "agreement_is_not_accuracy": P.AGREEMENT_IS_NOT_ACCURACY,

        "CANONICAL_FEATURES": len(rows),
        "REFERENCE_RESOLVED_FEATURES": n_judge,
        "REFERENCE_UNRESOLVED_FEATURES": sum(
            1 for r in rows if r["OUTCOME"] == P.REFERENCE_UNRESOLVED),
        "REFERENCE_CONFLICT_FEATURES": sum(
            1 for r in rows if r["OUTCOME"] == P.REFERENCE_CONFLICT),
        "REFERENCE_UNRESOLVED_RATE": _frac(
            len(rows) - n_judge, len(rows)),

        "FEATURE_ASSEMBLY_ACCURACY": _frac(len(correct), n_judge),
        "HIGH_CONFIDENCE_FEATURE_ACCURACY": _frac(len(hi_correct), len(hi_q)),
        "MEDIUM_CONFIDENCE_FEATURE_ACCURACY": _frac(
            len(med_correct), len(med_q)),
        "HIGH_CONFIDENCE_WRONG": len(hi_wrong),
        "ENTITY_ROLE_ACCURACY": _frac(len(ok_e), len(judge_e)),
        "RELATION_AGREEMENT": _frac(both, len(rel_rows)),
        "FENESTRATION": _count(fen_rows, "FENESTRATION_OUTCOME"),
        "CRITICAL_ERRORS_TOTAL": total_crit,
        "CRITICAL_ERROR_COUNTS": {
            **{n: len(v) for n, v in crit.items() if v},
            **{k: len(v) for k, v in sep_rows.items() if v}},
        "CHECKER": {
            "CELL_DISTRIBUTION": cells,
            "MISTAKES_THE_CHECKER_CAUGHT": caught,
            "MISTAKES_THE_CHECKER_WAS_BLIND_TO": missed},

        "COVERAGE_ANALYSIS": {
            "QUESTION": (
                "if only A19 HIGH-confidence findings were admitted, and "
                "only where an independent reference supports them, how "
                "much of the sampled semantic problem would that address"),
            "canonical_features_with_a_supported_high_confidence_reading":
                len(hi_ok_clusters),
            "of_canonical_features": len(rows),
            "source_intervals_they_cover": len(covered_intervals),
            "of_source_intervals_in_the_sample": len(sample_intervals),
            "the_sample_is_not_random": P.THE_SAMPLE_IS_NOT_RANDOM,
            "SO_THIS_MAY_NOT_BE_MULTIPLIED_OUT_TO_THE_FLOOR": True,
            "analysis_only": P.COVERAGE_ANALYSIS_IS_ANALYSIS_ONLY,
        },

        "READINESS": readiness,
        "THE_RULE_THAT_DECIDED_IT": which,
        "RULES_WERE_WRITTEN_BEFORE_THE_SCORES_EXISTED": True,
        "use_evidence_not_optimism": P.USE_EVIDENCE_NOT_OPTIMISM,
        "do_not_hide_the_denominator": P.DO_NOT_HIDE_THE_DENOMINATOR,
    })

    got = {
        "canonical_features": len(rows),
        "reference_resolved": n_judge,
        "reference_unresolved": sum(
            1 for r in rows if r["OUTCOME"] == P.REFERENCE_UNRESOLVED),
        "reference_conflict": sum(
            1 for r in rows if r["OUTCOME"] == P.REFERENCE_CONFLICT),
        "OUTCOME_DISTRIBUTION": _count(rows, "OUTCOME"),
        "FEATURE_ASSEMBLY_ACCURACY": _frac(len(correct), n_judge),
        "HIGH_CONFIDENCE_ACCURACY": _frac(len(hi_correct), len(hi_q)),
        "HIGH_CONFIDENCE_WRONG": len(hi_wrong),
        "MEDIUM_CONFIDENCE_ACCURACY": _frac(len(med_correct), len(med_q)),
        "ENTITY_ROLE_ACCURACY": _frac(len(ok_e), len(judge_e)),
        "RELATION_AGREEMENT": _frac(both, len(rel_rows)),
        "FENESTRATION": _count(fen_rows, "FENESTRATION_OUTCOME"),
        "CRITICAL_ERRORS_TOTAL": total_crit,
        "CHECKER_CELLS": cells,
        "READINESS": readiness,
        "hashes": {"FEATURE_ASSEMBLY_SCORE": fa_hash,
                   "ENTITY_ROLE_SCORE": er_hash,
                   "CRITICAL_ERROR_MATRIX": ce_hash,
                   "FENESTRATION_SCORE": fen_hash,
                   "RELATION_SCORE": rel_hash,
                   "CHECKER_VALUE_SCORE": chk_hash,
                   "DECISION_REPORT": dec_hash},
    }
    print(json.dumps(got, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
