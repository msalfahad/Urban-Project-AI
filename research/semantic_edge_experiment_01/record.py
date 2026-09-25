"""Ingest a pass's answers, screen them, and write the frozen registers.

    python -m research.semantic_edge_experiment_01.record --pass a
    python -m research.semantic_edge_experiment_01.record --pass b
    python -m research.semantic_edge_experiment_01.record --pass checker

An answer is prose and vocabulary. Anything that carries back a
coordinate, a measured quantity, a percentage or a probability is refused
and recorded as refused, because the one thing a semantic reader may not
do is own the geometry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from research.semantic_edge_experiment_01 import a19 as A19
from research.semantic_edge_experiment_01 import protocol as P

OUT = Path("data/experiments/SEMANTIC_EDGE_EXPERIMENT_01")
A19_DIR = OUT / "a19"
RAW = A19_DIR / "raw"


def write(path: Path, body) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                               default=str) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(prefix):
    rows = []
    for p in sorted(RAW.glob(f"{prefix}*.json")):
        got = json.loads(p.read_text(encoding="utf-8"))
        for r in (got if isinstance(got, list) else [got]):
            rows.append((p.name, r))
    return rows


def _labels_by_group():
    man = json.loads((A19_DIR / "PASS_A_INPUT_MANIFEST.json")
                     .read_text(encoding="utf-8"))
    out = {}
    for t in man["TASKS"]:
        d = A19_DIR / "pass_a_sandbox" / t["FEATURE_GROUP_ID"] / "TASK.json"
        task = json.loads(d.read_text(encoding="utf-8"))
        out[t["FEATURE_GROUP_ID"]] = {
            "labels": {m["MEMBER_LABEL"] for m in task["MARKED_MEMBERS"]},
            "stratum": t["STRATUM"],
            "fenestration_required": task["FENESTRATION_READING_IS_REQUIRED"],
            "curve_required": task["CURVE_FAMILY_IS_REQUIRED"],
        }
    return out


def _count(rows, key):
    out = {}
    for r in rows:
        v = r.get(key)
        out[str(v)] = out.get(str(v), 0) + 1
    return out


def pass_a() -> dict:
    meta = _labels_by_group()
    kept, refused = [], []
    for src, row in _load("PASS_A_"):
        gid = row.get("FEATURE_GROUP_ID")
        info = meta.get(gid)
        problems = A19.screen_answer(json.dumps(row, ensure_ascii=False))
        if info is None:
            problems.append(f"NOT_A_FEATURE_GROUP_IN_THIS_EXPERIMENT:{gid}")
        else:
            problems += A19.validate_pass_a(row, labels=info["labels"])
        if problems:
            refused.append({"FEATURE_GROUP_ID": gid, "source_file": src,
                            "REFUSED_BECAUSE": sorted(set(problems)),
                            "why": P.AI_IS_NEVER_THE_GEOMETRY_OWNER})
            continue
        row["ANSWER_SHA256"] = hashlib.sha256(
            json.dumps(row, sort_keys=True, ensure_ascii=False)
            .encode("utf-8")).hexdigest()
        row["source_file"] = src
        row["STRATUM"] = info["stratum"]
        kept.append(row)

    entity_rows, relation_rows = [], []
    for r in kept:
        for e in r.get("ENTITY_ROLES") or ():
            entity_rows.append({"FEATURE_GROUP_ID": r["FEATURE_GROUP_ID"],
                                "STRATUM": r["STRATUM"], **e})
        for rel in r.get("RELATIONS") or ():
            relation_rows.append({"FEATURE_GROUP_ID": r["FEATURE_GROUP_ID"],
                                  "STRATUM": r["STRATUM"], **rel})

    head = {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PASS": P.PASS_A,
        "PROTOCOL_HASH": P.protocol_hash(),
        "A19_BRIEF_HASH": A19.brief_hash(),
        "E1_4_IS_NOT_MODIFIED": True,
        "nothing_is_fed_back": P.NOTHING_IS_FED_BACK,
        "nothing_is_scored_here": P.NOTHING_IS_SCORED_HERE,
        "a19_has_no_numeric_field": P.A19_HAS_NO_NUMERIC_FIELD,
    }
    fh = write(A19_DIR / "PASS_A_FEATURE_ASSERTIONS.json", {
        **head,
        "groups_answered": len(kept),
        "answers_refused": len(refused),
        "REFUSED": refused,
        "FEATURE_ASSEMBLY_TYPE_DISTRIBUTION":
            _count(kept, "FEATURE_ASSEMBLY_TYPE"),
        "ASSEMBLY_CONFIDENCE_DISTRIBUTION":
            _count(kept, "ASSEMBLY_CONFIDENCE"),
        "NEEDS_MORE_CONTEXT_DISTRIBUTION": _count(kept, "NEEDS_MORE_CONTEXT"),
        "FENESTRATION_READING_DISTRIBUTION": _count(
            [r for r in kept
             if meta[r["FEATURE_GROUP_ID"]]["fenestration_required"]],
            "FENESTRATION_READING"),
        "CURVE_FAMILY_ANSWER_DISTRIBUTION": {
            str((r.get("CURVE_FAMILY") or {}).get(P.CURVE_FAMILY_QUESTION)):
                sum(1 for x in kept
                    if (x.get("CURVE_FAMILY") or {}).get(
                        P.CURVE_FAMILY_QUESTION)
                    == (r.get("CURVE_FAMILY") or {}).get(
                        P.CURVE_FAMILY_QUESTION))
            for r in kept
            if meta[r["FEATURE_GROUP_ID"]]["curve_required"]},
        "ANSWERS": kept,
    })
    eh = write(A19_DIR / "PASS_A_ENTITY_ASSERTIONS.json", {
        **head,
        "do_not_force_a_subtype": P.DO_NOT_FORCE_A_SUBTYPE,
        "entity_assertions": len(entity_rows),
        "SUB_ROLE_DISTRIBUTION": _count(entity_rows, "SUB_ROLE"),
        "CONFIDENCE_DISTRIBUTION": _count(entity_rows, "CONFIDENCE"),
        "ASSERTIONS": entity_rows,
    })
    rh = write(A19_DIR / "PASS_A_RELATIONS.json", {
        **head,
        "a_relation_is_semantic_evidence_and_not_geometry":
            P.A_RELATION_IS_SEMANTIC_EVIDENCE_AND_NOT_GEOMETRY,
        "relations": len(relation_rows),
        "RELATION_DISTRIBUTION": _count(relation_rows, "RELATION"),
        "RELATIONS": relation_rows,
    })
    return {"groups_answered": len(kept), "refused": len(refused),
            "entity_assertions": len(entity_rows),
            "relations": len(relation_rows),
            "PASS_A_FEATURE_ASSERTIONS_SHA256": fh,
            "PASS_A_ENTITY_ASSERTIONS_SHA256": eh,
            "PASS_A_RELATIONS_SHA256": rh}


def pass_b() -> dict:
    kept, refused = [], []
    for src, row in _load("PASS_B_"):
        problems = A19.screen_answer(json.dumps(row, ensure_ascii=False))
        problems += A19.validate_pass_b(row)
        if problems:
            refused.append({"FEATURE_GROUP_ID": row.get("FEATURE_GROUP_ID"),
                            "source_file": src,
                            "REFUSED_BECAUSE": sorted(set(problems))})
            continue
        row["source_file"] = src
        kept.append(row)
    counts = {}
    for r in kept:
        for s in r.get("STATUSES") or ():
            counts[s] = counts.get(s, 0) + 1
    h = write(A19_DIR / "PASS_B_CHALLENGE.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PASS": P.PASS_B,
        "PROTOCOL_HASH": P.protocol_hash(),
        "pass_b_may_not_edit_geometry": P.PASS_B_MAY_NOT_EDIT_GEOMETRY,
        "nothing_is_fed_back": P.NOTHING_IS_FED_BACK,
        "groups_answered": len(kept),
        "answers_refused": len(refused),
        "REFUSED": refused,
        "STATUS_DISTRIBUTION": counts,
        "ANSWERS": kept,
    })
    return {"groups_answered": len(kept), "refused": len(refused),
            "STATUS_DISTRIBUTION": counts, "PASS_B_CHALLENGE_SHA256": h}


def checker() -> dict:
    """§15 - a second cold reader, compared and never averaged."""
    a = {r["FEATURE_GROUP_ID"]: r for r in json.loads(
        (A19_DIR / "PASS_A_FEATURE_ASSERTIONS.json")
        .read_text(encoding="utf-8"))["ANSWERS"]}
    meta = _labels_by_group()
    kept, refused, rows = [], [], []
    for src, row in _load("CHECKER_"):
        gid = row.get("FEATURE_GROUP_ID")
        info = meta.get(gid)
        problems = A19.screen_answer(json.dumps(row, ensure_ascii=False))
        if info is None:
            problems.append(f"NOT_A_FEATURE_GROUP_IN_THIS_EXPERIMENT:{gid}")
        else:
            problems += A19.validate_pass_a(row, labels=info["labels"])
        if problems:
            refused.append({"FEATURE_GROUP_ID": gid, "source_file": src,
                            "REFUSED_BECAUSE": sorted(set(problems))})
            continue
        row["source_file"] = src
        kept.append(row)
        mine = a.get(gid) or {}
        t1 = mine.get("FEATURE_ASSEMBLY_TYPE")
        t2 = row.get("FEATURE_ASSEMBLY_TYPE")
        if P.UNRESOLVED_FEATURE in (t1, t2) and t1 != t2:
            verdict = "ONE_UNRESOLVED"
        elif t1 == t2:
            verdict = "AGREE"
        else:
            verdict = "DISAGREE"
        rows.append({
            "FEATURE_GROUP_ID": gid,
            "STRATUM": info["stratum"],
            "A19_FEATURE_ASSEMBLY_TYPE": t1,
            "CHECKER_FEATURE_ASSEMBLY_TYPE": t2,
            "COMPARISON": verdict,
            "BECOMES_HUMAN_REVIEW": verdict == "DISAGREE",
            "A19_FENESTRATION_READING": mine.get("FENESTRATION_READING"),
            "CHECKER_FENESTRATION_READING": row.get("FENESTRATION_READING"),
        })
    counts = {}
    for r in rows:
        counts[r["COMPARISON"]] = counts.get(r["COMPARISON"], 0) + 1
    d = OUT / "optional_checker"
    h = write(d / "CHECKER_COMPARISON.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "SEES": list(P.CHECKER_SEES),
        "DOES_NOT_SEE": list(P.CHECKER_DOES_NOT_SEE),
        "no_automatic_majority_vote": P.NO_AUTOMATIC_MAJORITY_VOTE,
        "HIGH_IMPACT_GROUPS_ARE": (
            "the groups whose stratum makes the fenestration or the curve "
            "family question required. That is a mechanical rule and it "
            "was fixed before any checker answer existed"),
        "groups_checked": len(rows),
        "answers_refused": len(refused),
        "REFUSED": refused,
        "COMPARISON_DISTRIBUTION": counts,
        "ROWS": rows,
        "CHECKER_ANSWERS": kept,
    })
    return {"groups_checked": len(rows), "refused": len(refused),
            "COMPARISON_DISTRIBUTION": counts,
            "CHECKER_COMPARISON_SHA256": h}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pass", dest="which", required=True,
                    choices=("a", "b", "checker"))
    a = ap.parse_args(argv)
    got = {"a": pass_a, "b": pass_b, "checker": checker}[a.which]()
    print(json.dumps(got, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
