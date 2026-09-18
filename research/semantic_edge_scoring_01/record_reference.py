"""Ingest reference readings, screen them, and freeze the reference.

    python -m research.semantic_edge_scoring_01.record_reference --stage a
    python -m research.semantic_edge_scoring_01.record_reference --stage b

Stage A is the first independent reading of every canonical feature.
Stage B is the second independent reading of the features whose FIRST
reading landed in a category that could materially move geometry.

No A19 output is opened by this file. The frozen reference register it
writes is what scoring is later allowed to compare against, and scoring
refuses to run until it exists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from research.semantic_edge_scoring_01 import protocol as P

OUT = Path("data/experiments/SEMANTIC_EDGE_SCORING_01")
RAW = OUT / "reference_raw"

_COORD = re.compile(r"[-+]?\d{4,}\s*[,;]\s*[-+]?\d{4,}")
_QUANTITY = re.compile(
    r"\b\d+(\.\d+)?\s*(m2|m²|sqm|square\s+met|metre|meter|m\b|mm\b|cm\b)",
    re.I)
_PERCENT = re.compile(r"\b\d+(\.\d+)?\s*%")
_PROBABILITY = re.compile(r"\b(0\.\d+|1\.0+)\b")


def screen(text: str) -> list:
    out = []
    if _COORD.search(text or ""):
        out.append("A_COORDINATE_PAIR")
    if _QUANTITY.search(text or ""):
        out.append("A_MEASURED_QUANTITY")
    if _PERCENT.search(text or ""):
        out.append("A_PERCENTAGE")
    if _PROBABILITY.search(text or ""):
        out.append("A_PROBABILITY")
    return out


def write(path: Path, body) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                               default=str) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _members():
    man = json.loads((OUT / "02_REFERENCE_INPUT_MANIFEST.json")
                     .read_text(encoding="utf-8"))
    out = {}
    for t in man["TASKS"]:
        cid = t["CANONICAL_FEATURE_CLUSTER_ID"]
        task = json.loads((OUT / "reference_sandbox" / cid
                           / "REFERENCE_TASK.json").read_text("utf-8"))
        out[cid] = {f"{m['FEATURE_GROUP_ID']}/{m['MEMBER_LABEL']}"
                    for m in task["MARKED_MEMBERS"]}
    return out


def _validate(row, labels) -> list:
    bad = []
    if row.get("REFERENCE_ROLE") not in P.FEATURE_ASSEMBLY_TYPES:
        bad.append(f"NOT_AN_ASSEMBLY_TYPE:{row.get('REFERENCE_ROLE')}")
    if row.get("REFERENCE_CONFIDENCE") not in P.CONFIDENCE_CLASSES:
        bad.append(f"NOT_A_CONFIDENCE:{row.get('REFERENCE_CONFIDENCE')}")
    for e in row.get("ENTITY_REFERENCE") or ():
        key = f"{e.get('FEATURE_GROUP_ID')}/{e.get('MEMBER_LABEL')}"
        if key not in labels:
            bad.append(f"NOT_A_MARKED_MEMBER:{key}")
        if e.get("REFERENCE_ROLE") not in P.ENTITY_SUB_ROLES:
            bad.append(f"NOT_A_SUB_ROLE:{e.get('REFERENCE_ROLE')}")
        if e.get("REFERENCE_CONFIDENCE") not in P.CONFIDENCE_CLASSES:
            bad.append(f"NOT_A_CONFIDENCE:{e.get('REFERENCE_CONFIDENCE')}")
    for r in row.get("REFERENCE_RELATIONS") or ():
        if r.get("RELATION") not in P.RELATIONS:
            bad.append(f"NOT_A_RELATION:{r.get('RELATION')}")
    return bad


def _load(prefix):
    rows = []
    for p in sorted(RAW.glob(f"{prefix}*.json")):
        got = json.loads(p.read_text(encoding="utf-8"))
        for r in (got if isinstance(got, list) else [got]):
            rows.append((p.name, r))
    return rows


def _count(rows, key):
    out = {}
    for r in rows:
        out[str(r.get(key))] = out.get(str(r.get(key)), 0) + 1
    return out


def ingest(prefix, labels):
    kept, refused = [], []
    for src, row in _load(prefix):
        cid = row.get("CANONICAL_FEATURE_CLUSTER_ID")
        problems = screen(json.dumps(row, ensure_ascii=False))
        if cid not in labels:
            problems.append(f"NOT_A_CANONICAL_FEATURE:{cid}")
        else:
            problems += _validate(row, labels[cid])
        if problems:
            refused.append({"CANONICAL_FEATURE_CLUSTER_ID": cid,
                            "source_file": src,
                            "REFUSED_BECAUSE": sorted(set(problems))})
            continue
        row["source_file"] = src
        kept.append(row)
    return kept, refused


def stage_a() -> dict:
    labels = _members()
    kept, refused = ingest("REFERENCE_A_", labels)
    ent = [{"CANONICAL_FEATURE_CLUSTER_ID": r["CANONICAL_FEATURE_CLUSTER_ID"],
            **e} for r in kept for e in (r.get("ENTITY_REFERENCE") or ())]
    rel = [{"CANONICAL_FEATURE_CLUSTER_ID": r["CANONICAL_FEATURE_CLUSTER_ID"],
            **x} for r in kept for x in (r.get("REFERENCE_RELATIONS") or ())]
    high = sorted(r["CANONICAL_FEATURE_CLUSTER_ID"] for r in kept
                  if r["REFERENCE_ROLE"] in P.HIGH_IMPACT_ASSEMBLIES)
    h = write(OUT / "03_REFERENCE_LABEL_REGISTER.json", {
        "SCORING_ID": P.SCORING_ID,
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "STAGE": "FIRST_INDEPENDENT_REFERENCE",
        "NO_A19_OUTPUT_WAS_OPENED_TO_PRODUCE_THIS": True,
        "the_reference_freezes_first": P.THE_REFERENCE_FREEZES_FIRST,
        "may_not_guess": P.THE_REFERENCE_MAY_NOT_GUESS,
        "no_numeric_confidence": P.NO_NUMERIC_CONFIDENCE,
        "canonical_features_read": len(kept),
        "readings_refused": len(refused),
        "REFUSED": refused,
        "REFERENCE_ROLE_DISTRIBUTION": _count(kept, "REFERENCE_ROLE"),
        "REFERENCE_CONFIDENCE_DISTRIBUTION": _count(
            kept, "REFERENCE_CONFIDENCE"),
        "NEEDS_ADDITIONAL_CONTEXT_DISTRIBUTION": _count(
            kept, "NEEDS_ADDITIONAL_CONTEXT"),
        "entity_references": len(ent),
        "ENTITY_REFERENCE_ROLE_DISTRIBUTION": _count(ent, "REFERENCE_ROLE"),
        "ENTITY_REFERENCE_CONFIDENCE_DISTRIBUTION": _count(
            ent, "REFERENCE_CONFIDENCE"),
        "reference_relations": len(rel),
        "REFERENCE_RELATION_DISTRIBUTION": _count(rel, "RELATION"),
        "HIGH_IMPACT_ASSEMBLIES": list(P.HIGH_IMPACT_ASSEMBLIES),
        "why_these_are_high_impact": P.WHY_THESE_ARE_HIGH_IMPACT,
        "SECOND_REFERENCE_RULE": P.SECOND_REFERENCE_RULE,
        "FEATURES_NEEDING_A_SECOND_INDEPENDENT_READING": high,
        "READINGS": kept,
        "ENTITY_REFERENCES": ent,
        "REFERENCE_RELATIONS": rel,
    })
    return {"canonical_features_read": len(kept), "refused": len(refused),
            "REFERENCE_ROLE_DISTRIBUTION": _count(kept, "REFERENCE_ROLE"),
            "entity_references": len(ent), "reference_relations": len(rel),
            "features_needing_a_second_reading": len(high),
            "SECOND_READING_LIST": high,
            "03_REFERENCE_LABEL_REGISTER_SHA256": h}


def stage_b() -> dict:
    labels = _members()
    first = json.loads((OUT / "03_REFERENCE_LABEL_REGISTER.json")
                       .read_text(encoding="utf-8"))
    a_by = {r["CANONICAL_FEATURE_CLUSTER_ID"]: r for r in first["READINGS"]}
    kept, refused = ingest("REFERENCE_B_", labels)

    rows = []
    for r in kept:
        cid = r["CANONICAL_FEATURE_CLUSTER_ID"]
        a = a_by.get(cid) or {}
        ra, rb = a.get("REFERENCE_ROLE"), r.get("REFERENCE_ROLE")
        if ra == rb:
            verdict = "REFERENCE_AGREE"
        elif P.UNRESOLVED_FEATURE in (ra, rb):
            verdict = "ONE_REFERENCE_UNRESOLVED"
        else:
            verdict = P.REFERENCE_CONFLICT
        rows.append({
            "CANONICAL_FEATURE_CLUSTER_ID": cid,
            "FIRST_REFERENCE_ROLE": ra,
            "FIRST_REFERENCE_CONFIDENCE": a.get("REFERENCE_CONFIDENCE"),
            "SECOND_REFERENCE_ROLE": rb,
            "SECOND_REFERENCE_CONFIDENCE": r.get("REFERENCE_CONFIDENCE"),
            "VERDICT": verdict,
            "EXCLUDED_FROM_STRICT_ACCURACY": verdict == P.REFERENCE_CONFLICT,
        })
    counts = {}
    for r in rows:
        counts[r["VERDICT"]] = counts.get(r["VERDICT"], 0) + 1
    h = write(OUT / "04_REFERENCE_CONFLICT_REGISTER.json", {
        "SCORING_ID": P.SCORING_ID,
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "STAGE": "SECOND_INDEPENDENT_REFERENCE",
        "NO_A19_OUTPUT_WAS_OPENED_TO_PRODUCE_THIS": True,
        "THE_SECOND_READER_DID_NOT_SEE_THE_FIRST": True,
        "SECOND_REFERENCE_RULE": P.SECOND_REFERENCE_RULE,
        "no_automatic_vote": P.NO_AUTOMATIC_VOTE,
        "features_read_again": len(kept),
        "readings_refused": len(refused),
        "REFUSED": refused,
        "VERDICT_DISTRIBUTION": counts,
        "ROWS": rows,
        "SECOND_READINGS": kept,
    })
    return {"features_read_again": len(kept), "refused": len(refused),
            "VERDICT_DISTRIBUTION": counts,
            "04_REFERENCE_CONFLICT_REGISTER_SHA256": h}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", required=True, choices=("a", "b"))
    a = ap.parse_args(argv)
    print(json.dumps({"a": stage_a, "b": stage_b}[a.stage](), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
