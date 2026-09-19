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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", required=True,
                    choices=("reference_a", "reference_b"))
    a = ap.parse_args(argv)
    got = reference("a" if a.stage == "reference_a" else "b")
    print(json.dumps(got, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
