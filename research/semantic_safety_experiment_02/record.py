"""Ingest a pass's answers, screen them, and write the frozen registers.

    --stage reference_a   the first blind reference over every feature
    --stage reference_b   the second blind reference, geometry-changing only
    --stage a19           A19's relation-first answers
    --stage checker       the narrow separator question

The reference registers are written before any A19 output is opened by
any scoring code, and the scorer refuses to run until they exist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from research.semantic_safety_experiment_02 import protocol as P

OUT = Path("data/experiments/SEMANTIC_SAFETY_EXPERIMENT_02")

_COORD = re.compile(r"[-+]?\d{4,}\s*[,;]\s*[-+]?\d{4,}")
_QUANTITY = re.compile(
    r"\b\d+(\.\d+)?\s*(m2|m²|sqm|square\s+met|metre|meter|m\b|mm\b|cm\b)",
    re.I)
_PERCENT = re.compile(r"\b\d+(\.\d+)?\s*%")
_PROBABILITY = re.compile(r"\b(0\.\d+|1\.0+)\b")


def screen(text: str) -> list:
    out = []
    for rx, name in ((_COORD, "A_COORDINATE_PAIR"),
                     (_QUANTITY, "A_MEASURED_QUANTITY"),
                     (_PERCENT, "A_PERCENTAGE"),
                     (_PROBABILITY, "A_PROBABILITY")):
        if rx.search(text or ""):
            out.append(name)
    return out


def write(path: Path, body) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                               default=str) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tasks():
    man = json.loads((OUT / "03_REFERENCE_INPUT_MANIFEST.json")
                     .read_text("utf-8"))
    out = {}
    for t in man["TASKS"]:
        fid = t["CANONICAL_FEATURE_ID"]
        task = json.loads((OUT / "blind_sandbox" / fid / "TASK.json")
                          .read_text("utf-8"))
        out[fid] = {
            "labels": {m["MEMBER_LABEL"] for m in task["MARKED_MEMBERS"]},
            "stratum": t["STRATUM"],
            "applies": task["QUESTIONS_THAT_APPLY_HERE"],
            "untagged": task.get(
                "MEMBERS_SHOWN_BUT_NOT_INDIVIDUALLY_TAGGED", 0),
        }
    return out


def _load(prefix, raw):
    rows = []
    for p in sorted((OUT / raw).glob(f"{prefix}*.json")):
        got = json.loads(p.read_text("utf-8"))
        for r in (got if isinstance(got, list) else [got]):
            rows.append((p.name, r))
    return rows


def _count(rows, key):
    out = {}
    for r in rows:
        out[str(r.get(key))] = out.get(str(r.get(key)), 0) + 1
    return out


def _validate_reference(row, info) -> list:
    bad = []
    if row.get("REFERENCE_RELATION") not in P.PHYSICAL_RELATIONS:
        bad.append(f"NOT_A_RELATION:{row.get('REFERENCE_RELATION')}")
    if row.get("REFERENCE_CONFIDENCE") not in P.CONFIDENCE_CLASSES:
        bad.append(f"NOT_A_CONFIDENCE:{row.get('REFERENCE_CONFIDENCE')}")
    at = row.get("ASSEMBLY_TYPE")
    if at is not None and at not in P.ASSEMBLY_TYPES:
        bad.append(f"NOT_AN_ASSEMBLY_TYPE:{at}")
    for e in row.get("ENTITY_REFERENCE") or ():
        if e.get("MEMBER_LABEL") not in info["labels"]:
            bad.append(f"NOT_A_TAGGED_MEMBER:{e.get('MEMBER_LABEL')}")
        if e.get("REFERENCE_ROLE") not in P.ENTITY_SUB_ROLES:
            bad.append(f"NOT_A_SUB_ROLE:{e.get('REFERENCE_ROLE')}")
    return bad


def reference(stage) -> dict:
    info = _tasks()
    prefix = ("REFERENCE_A_" if stage == "a" else "REFERENCE_B_")
    kept, refused = [], []
    for src, row in _load(prefix, "reference_raw"):
        fid = row.get("CANONICAL_FEATURE_ID")
        problems = screen(json.dumps(row, ensure_ascii=False))
        if fid not in info:
            problems.append(f"NOT_A_FEATURE_IN_THIS_EXPERIMENT:{fid}")
        else:
            problems += _validate_reference(row, info[fid])
        if problems:
            refused.append({"CANONICAL_FEATURE_ID": fid, "source_file": src,
                            "REFUSED_BECAUSE": sorted(set(problems))})
            continue
        row["source_file"] = src
        row["STRATUM"] = info[fid]["stratum"]
        kept.append(row)

    ent = [{"CANONICAL_FEATURE_ID": r["CANONICAL_FEATURE_ID"], **e}
           for r in kept for e in (r.get("ENTITY_REFERENCE") or ())]
    changing = sorted(r["CANONICAL_FEATURE_ID"] for r in kept
                      if r["REFERENCE_RELATION"]
                      in P.GEOMETRY_CHANGING_RELATIONS)
    name = "04_REFERENCE_A.json" if stage == "a" else "05_REFERENCE_B.json"
    h = write(OUT / name, {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "STAGE": ("FIRST_INDEPENDENT_REFERENCE" if stage == "a"
                  else "SECOND_INDEPENDENT_REFERENCE"),
        "NO_A19_OUTPUT_WAS_OPENED_TO_PRODUCE_THIS": True,
        "may_not_guess": P.THE_REFERENCE_MAY_NOT_GUESS,
        "answers_the_relation_first": P.REFERENCE_ANSWERS_THE_RELATION_FIRST,
        "glazing_is_not_masonry_and_is_not_a_hole":
            P.GLAZING_IS_NOT_MASONRY_AND_IS_NOT_A_HOLE,
        "features_read": len(kept),
        "readings_refused": len(refused),
        "REFUSED": refused,
        "RELATION_DISTRIBUTION": _count(kept, "REFERENCE_RELATION"),
        "CONFIDENCE_DISTRIBUTION": _count(kept, "REFERENCE_CONFIDENCE"),
        "ASSEMBLY_DISTRIBUTION": _count(kept, "ASSEMBLY_TYPE"),
        "NEEDS_ADDITIONAL_CONTEXT_DISTRIBUTION": _count(
            kept, "NEEDS_ADDITIONAL_CONTEXT"),
        "entity_references": len(ent),
        "ENTITY_ROLE_DISTRIBUTION": _count(ent, "REFERENCE_ROLE"),
        "GEOMETRY_CHANGING_RELATIONS": list(P.GEOMETRY_CHANGING_RELATIONS),
        "DUAL_REFERENCE_RULE": P.DUAL_REFERENCE_RULE,
        "FEATURES_NEEDING_A_SECOND_INDEPENDENT_READING": changing,
        "READINGS": kept,
        "ENTITY_REFERENCES": ent,
    })
    return {"features_read": len(kept), "refused": len(refused),
            "RELATION_DISTRIBUTION": _count(kept, "REFERENCE_RELATION"),
            "features_needing_a_second_reading": len(changing),
            "SECOND_READING_LIST": changing,
            f"{name}_SHA256": h}


def conflicts() -> dict:
    """Where the two independent readings disagree, the reference says so.

    A conflict is not resolved by picking one, by taking a majority or by
    asking a third reader whose answer would then be selected for
    agreeing. It is recorded as REFERENCE_CONFLICT and that feature is
    excluded from PRIMARY scoring, because there is no established truth
    at it to score against.
    """
    a = json.loads((OUT / "04_REFERENCE_A.json").read_text("utf-8"))
    b = json.loads((OUT / "05_REFERENCE_B.json").read_text("utf-8"))
    ra = {r["CANONICAL_FEATURE_ID"]: r for r in a["READINGS"]}
    rb = {r["CANONICAL_FEATURE_ID"]: r for r in b["READINGS"]}
    required = set(a["FEATURES_NEEDING_A_SECOND_INDEPENDENT_READING"])

    rows, agreed, conflict, missing = [], [], [], []
    for fid in sorted(required):
        first = ra[fid]["REFERENCE_RELATION"]
        if fid not in rb:
            missing.append(fid)
            rows.append({"CANONICAL_FEATURE_ID": fid,
                         "REFERENCE_A_RELATION": first,
                         "REFERENCE_B_RELATION": None,
                         "STATUS": "SECOND_READING_MISSING"})
            continue
        second = rb[fid]["REFERENCE_RELATION"]
        same = first == second
        (agreed if same else conflict).append(fid)
        rows.append({
            "CANONICAL_FEATURE_ID": fid,
            "STRATUM": ra[fid].get("STRATUM"),
            "REFERENCE_A_RELATION": first,
            "REFERENCE_A_CONFIDENCE": ra[fid].get("REFERENCE_CONFIDENCE"),
            "REFERENCE_B_RELATION": second,
            "REFERENCE_B_CONFIDENCE": rb[fid].get("REFERENCE_CONFIDENCE"),
            "STATUS": "AGREED" if same else P.REFERENCE_CONFLICT,
        })

    h = write(OUT / "06_REFERENCE_CONFLICTS.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "DUAL_REFERENCE_RULE": P.DUAL_REFERENCE_RULE,
        "no_manufactured_truth": P.NO_MANUFACTURED_TRUTH,
        "GEOMETRY_CHANGING_RELATIONS": list(P.GEOMETRY_CHANGING_RELATIONS),
        "features_requiring_a_second_reading": len(required),
        "agreed": len(agreed),
        "in_conflict": len(conflict),
        "second_reading_missing": len(missing),
        "ESTABLISHED": sorted(agreed),
        "IN_CONFLICT_AND_THEREFORE_NOT_ESTABLISHED": sorted(conflict),
        "SECOND_READING_MISSING": sorted(missing),
        "ROWS": rows,
    })
    return {"features_requiring_a_second_reading": len(required),
            "agreed": len(agreed), "in_conflict": len(conflict),
            "second_reading_missing": len(missing),
            "IN_CONFLICT": sorted(conflict),
            "06_REFERENCE_CONFLICTS.json_SHA256": h}


def _validate_a19(row, info) -> list:
    bad = []
    if row.get("A19_RELATION") not in P.PHYSICAL_RELATIONS:
        bad.append(f"NOT_A_RELATION:{row.get('A19_RELATION')}")
    if row.get("A19_CONFIDENCE") not in P.CONFIDENCE_CLASSES:
        bad.append(f"NOT_A_CONFIDENCE:{row.get('A19_CONFIDENCE')}")
    at = row.get("ASSEMBLY_TYPE")
    if at is not None and at not in P.ASSEMBLY_TYPES:
        bad.append(f"NOT_AN_ASSEMBLY_TYPE:{at}")
    for e in row.get("ENTITY_ASSERTIONS") or ():
        if e.get("MEMBER_LABEL") not in info["labels"]:
            bad.append(f"NOT_A_TAGGED_MEMBER:{e.get('MEMBER_LABEL')}")
        if e.get("A19_SUB_ROLE") not in P.ENTITY_SUB_ROLES:
            bad.append(f"NOT_A_SUB_ROLE:{e.get('A19_SUB_ROLE')}")
    return bad


def a19() -> dict:
    """A19's answers, screened and split into the four registers.

    A19 owns no geometry here and is given none. It reads the same crops
    and the same tags the reference read, under a different brief, and
    every answer it returns names a tagged member or the feature as a
    whole - nothing else.
    """
    info = _tasks()
    kept, refused, esc = [], [], []
    for src, row in _load("A19_", "a19_raw"):
        fid = row.get("CANONICAL_FEATURE_ID")
        problems = screen(json.dumps(row, ensure_ascii=False))
        if fid not in info:
            problems.append(f"NOT_A_FEATURE_IN_THIS_EXPERIMENT:{fid}")
        else:
            problems += _validate_a19(row, info[fid])
        if problems:
            refused.append({"CANONICAL_FEATURE_ID": fid, "source_file": src,
                            "REFUSED_BECAUSE": sorted(set(problems))})
            continue
        row["source_file"] = src
        row["STRATUM"] = info[fid]["stratum"]
        kept.append(row)
        if row.get("ESCALATION"):
            esc.append({"CANONICAL_FEATURE_ID": fid, **row["ESCALATION"]})

    d = OUT / "a19"
    hashes = {}
    hashes["INPUT_MANIFEST.json"] = write(d / "INPUT_MANIFEST.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "A19_SAW_EXACTLY_WHAT_THE_REFERENCE_SAW": (
            "the same crops and the same tags, from the same sandbox, "
            "under a different brief"),
        "A19_DID_NOT_SEE": ["the reference's answers", "the checker's "
                            "answers", "E1.4", "any register", "any "
                            "coordinate", "any quantity"],
        "a19_owns_no_geometry": P.IT_ONLY_INTERPRETS_WHAT_IS_TAGGED,
        "features_offered": len(info),
        "features_answered": len(kept),
        "FEATURES": sorted(info),
    })
    hashes["PRIMARY_RELATIONS.json"] = write(d / "PRIMARY_RELATIONS.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "the_primary_output_is_the_relation":
            P.THE_PRIMARY_OUTPUT_IS_THE_RELATION,
        "abstaining_is_not_an_error": P.ABSTAINING_IS_NOT_AN_ERROR,
        "features_answered": len(kept),
        "answers_refused": len(refused),
        "REFUSED": refused,
        "RELATION_DISTRIBUTION": _count(kept, "A19_RELATION"),
        "CONFIDENCE_DISTRIBUTION": _count(kept, "A19_CONFIDENCE"),
        "ROWS": [{k: v for k, v in r.items()
                  if k not in ("ENTITY_ASSERTIONS", "ESCALATION")}
                 for r in kept],
    })
    hashes["ASSEMBLY_ASSERTIONS.json"] = write(
        d / "ASSEMBLY_ASSERTIONS.json", {
            "EXPERIMENT_ID": P.EXPERIMENT_ID,
            "PROTOCOL_HASH": P.protocol_hash(),
            "ASSEMBLY_DISTRIBUTION": _count(kept, "ASSEMBLY_TYPE"),
            "ROWS": [{"CANONICAL_FEATURE_ID": r["CANONICAL_FEATURE_ID"],
                      "STRATUM": r["STRATUM"],
                      "ASSEMBLY_TYPE": r.get("ASSEMBLY_TYPE"),
                      "ASSEMBLY_CONFIDENCE": r.get("ASSEMBLY_CONFIDENCE"),
                      "WHY": r.get("ASSEMBLY_WHY")} for r in kept],
        })
    ent = [{"CANONICAL_FEATURE_ID": r["CANONICAL_FEATURE_ID"], **e}
           for r in kept for e in (r.get("ENTITY_ASSERTIONS") or ())]
    hashes["ENTITY_ASSERTIONS.json"] = write(d / "ENTITY_ASSERTIONS.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "A_MEMBER_WITHOUT_A_TAG_CARRIES_NO_ROLE": (
            "no role may be inferred for a member merely because another "
            "coincident member was tagged"),
        "entity_assertions": len(ent),
        "SUB_ROLE_DISTRIBUTION": _count(ent, "A19_SUB_ROLE"),
        "ROWS": ent,
    })
    hashes["CONTEXT_ESCALATIONS.json"] = write(
        d / "CONTEXT_ESCALATIONS.json", {
            "EXPERIMENT_ID": P.EXPERIMENT_ID,
            "PROTOCOL_HASH": P.protocol_hash(),
            "ESCALATION_RULE": P.ESCALATION_RULE,
            "ESCALATION_FACTOR": P.ESCALATION_FACTOR,
            "ESCALATION_MIN_HALF_MM": P.ESCALATION_MIN_HALF_MM,
            "ESCALATIONS_ALLOWED": P.ESCALATIONS_ALLOWED,
            "escalations_taken": len(esc),
            "MORE_THAN_ONE_WAS_TAKEN_ANYWHERE": any(
                _count(esc, "CANONICAL_FEATURE_ID")[k] > P.ESCALATIONS_ALLOWED
                for k in _count(esc, "CANONICAL_FEATURE_ID")),
            "ROWS": esc,
        })
    return {"features_answered": len(kept), "refused": len(refused),
            "RELATION_DISTRIBUTION": _count(kept, "A19_RELATION"),
            "CONFIDENCE_DISTRIBUTION": _count(kept, "A19_CONFIDENCE"),
            "escalations_taken": len(esc), "SHA256": hashes}


def checker() -> dict:
    """The narrow separator question, answered blind of everything else.

    One question, one vocabulary. The checker never sees A19's answer, so
    it cannot agree with it by construction, and agreement with it is not
    treated as evidence of correctness anywhere.
    """
    info = _tasks()
    kept, refused = [], []
    for src, row in _load("CHECKER_", "checker_raw"):
        fid = row.get("CANONICAL_FEATURE_ID")
        problems = screen(json.dumps(row, ensure_ascii=False))
        if fid not in info:
            problems.append(f"NOT_A_FEATURE_IN_THIS_EXPERIMENT:{fid}")
        if row.get("CHECKER_ANSWER") not in P.CHECKER_ANSWERS:
            problems.append(f"NOT_AN_ANSWER:{row.get('CHECKER_ANSWER')}")
        if row.get("CHECKER_CONFIDENCE") not in P.CONFIDENCE_CLASSES:
            problems.append(
                f"NOT_A_CONFIDENCE:{row.get('CHECKER_CONFIDENCE')}")
        if problems:
            refused.append({"CANONICAL_FEATURE_ID": fid, "source_file": src,
                            "REFUSED_BECAUSE": sorted(set(problems))})
            continue
        row["source_file"] = src
        row["STRATUM"] = info[fid]["stratum"]
        kept.append(row)

    h = write(OUT / "checker" / "CHECKER_ANSWERS.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "CHECKER_QUESTION": P.CHECKER_QUESTION,
        "CHECKER_SEES": list(P.CHECKER_SEES),
        "CHECKER_DOES_NOT_SEE": list(P.CHECKER_DOES_NOT_SEE),
        "no_voting": P.NO_VOTING,
        "why_the_checker_was_redesigned": P.WHY_THE_CHECKER_WAS_REDESIGNED,
        "features_answered": len(kept),
        "answers_refused": len(refused),
        "REFUSED": refused,
        "ANSWER_DISTRIBUTION": _count(kept, "CHECKER_ANSWER"),
        "CONFIDENCE_DISTRIBUTION": _count(kept, "CHECKER_CONFIDENCE"),
        "ROWS": kept,
    })
    return {"features_answered": len(kept), "refused": len(refused),
            "ANSWER_DISTRIBUTION": _count(kept, "CHECKER_ANSWER"),
            "CHECKER_ANSWERS.json_SHA256": h}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", required=True,
                    choices=("reference_a", "reference_b", "conflicts",
                             "a19", "checker"))
    a = ap.parse_args(argv)
    if a.stage == "conflicts":
        got = conflicts()
    elif a.stage == "a19":
        got = a19()
    elif a.stage == "checker":
        got = checker()
    else:
        got = reference("a" if a.stage == "reference_a" else "b")
    print(json.dumps(got, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
