"""What the declared canonicalisation rule failed to merge, and why.

A reference reader reported that three canonical features are the same
window in the bath/court wall. They are, and the rule let them through.

THE DEFECT IS IN THE RULE I DECLARED

    two frozen groups are one canonical feature when their PRIMARY members
    include intervals of the SAME PARENT CAD ENTITY and their extents
    overlap

That requires a shared entity - and a window run is several parallel lines
which are several different entities. So the rule contradicts the premise
the whole experiment rests on:

    ENTITY IS NOT ARCHITECTURAL FEATURE

and it under-merges in exactly the place that premise predicts: wherever
one feature is built from distinct neighbouring entities.

THE RULE IS NOT CHANGED

It was hashed into the scoring protocol before the sample was clustered
and it stays as written; re-clustering after seeing what the reference
said would make the canonicalisation depend on the answer, which is the
one thing it must not do. What happens instead is that the residual is
measured geometrically, reported, and carried beside every per-feature
rate, so nobody reads a denominator that counts one window four times as
though it were four windows.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.semantic_edge_scoring_01 import protocol as P

EXP = Path("data/experiments/SEMANTIC_EDGE_EXPERIMENT_01")
OUT = Path("data/experiments/SEMANTIC_EDGE_SCORING_01")

HIGH_OVERLAP = 0.5
VERY_HIGH_OVERLAP = 0.8


def _iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1])
    ub = (b[2] - b[0]) * (b[3] - b[1])
    union = ua + ub - inter
    return (inter / union) if union > 0 else 0.0


def _closure(ids, related):
    parent = {i: i for i in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in related:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    comps = {}
    for i in ids:
        comps.setdefault(find(i), []).append(i)
    return [sorted(v) for v in comps.values()]


def main() -> int:
    cl = json.loads((OUT / "01_CANONICAL_FEATURE_CLUSTER_REGISTER.json")
                    .read_text("utf-8"))
    groups = {g["FEATURE_GROUP_ID"]: g for g in json.loads(
        (EXP / "02_FEATURE_GROUP_REGISTER.json").read_text("utf-8"))["GROUPS"]}

    box = {}
    for c in cl["CLUSTERS"]:
        cid = c["CANONICAL_FEATURE_CLUSTER_ID"]
        xs, ys = [], []
        for g in c["MEMBER_FEATURE_GROUP_IDS"]:
            b = groups[g]["LOCAL_TOPOLOGY"]["bounding_box_mm"]
            xs += [b[0], b[2]]
            ys += [b[1], b[3]]
        box[cid] = [min(xs), min(ys), max(xs), max(ys)]

    ids = sorted(box)
    pairs = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            v = _iou(box[a], box[b])
            if v >= HIGH_OVERLAP:
                pairs.append({"A": a, "B": b,
                              "bounding_box_overlap_share": round(v, 4),
                              "VERY_HIGH": v >= VERY_HIGH_OVERLAP})
    high = [(p["A"], p["B"]) for p in pairs]
    vhigh = [(p["A"], p["B"]) for p in pairs if p["VERY_HIGH"]]
    cl_high = [c for c in _closure(ids, high) if len(c) > 1]
    cl_vhigh = [c for c in _closure(ids, vhigh) if len(c) > 1]

    body = {
        "SCORING_ID": P.SCORING_ID,
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "THE_DECLARED_RULE": P.CANONICAL_RULE,
        "THE_DEFECT_IN_IT": (
            "it requires a SHARED PARENT CAD ENTITY, and one architectural "
            "feature is routinely built from several distinct entities - a "
            "window run is several parallel lines. The rule therefore "
            "contradicts the premise the experiment rests on, ENTITY IS "
            "NOT ARCHITECTURAL FEATURE, and under-merges wherever that "
            "premise bites"),
        "IT_WAS_A_REFERENCE_READER_WHO_NOTICED": (
            "a reader reported that three canonical features are the same "
            "window in the bath/court wall, before this measurement "
            "existed. That is the second time a blind reader has found a "
            "defect in this apparatus rather than in the drawing"),
        "THE_RULE_IS_NOT_CHANGED": (
            "it was hashed into the scoring protocol before the sample was "
            "clustered. Re-clustering now, after seeing what the reference "
            "said, would make the canonicalisation depend on the answer - "
            "the one thing it must not do. The residual is measured and "
            "carried instead"),
        "WHAT_A_LATER_ROUND_SHOULD_DO": (
            "declare a canonicalisation rule that merges on geometric "
            "proximity as well as shared entity, so that a feature made of "
            "neighbouring distinct entities is one feature. The overlap "
            "measure below is a candidate and is NOT used here"),
        "MEASURE": ("share of the union of two canonical features' extents "
                    "that both occupy. Geometry only, no semantic answer"),
        "HIGH_OVERLAP_THRESHOLD": HIGH_OVERLAP,
        "VERY_HIGH_OVERLAP_THRESHOLD": VERY_HIGH_OVERLAP,
        "canonical_features_as_scored": len(ids),
        "pairs_overlapping_at_least_half": len(pairs),
        "pairs_overlapping_at_least_four_fifths": sum(
            1 for p in pairs if p["VERY_HIGH"]),
        "SENSITIVITY_IF_HIGH_OVERLAP_WERE_MERGED": {
            "clusters_that_would_merge": len(cl_high),
            "canonical_features_inside_them": sum(len(c) for c in cl_high),
            "canonical_features_would_become": len(ids) - sum(
                len(c) - 1 for c in cl_high),
            "GROUPS": cl_high,
        },
        "SENSITIVITY_IF_VERY_HIGH_OVERLAP_WERE_MERGED": {
            "clusters_that_would_merge": len(cl_vhigh),
            "canonical_features_inside_them": sum(len(c) for c in cl_vhigh),
            "canonical_features_would_become": len(ids) - sum(
                len(c) - 1 for c in cl_vhigh),
            "GROUPS": cl_vhigh,
        },
        "THESE_SENSITIVITIES_ARE_REPORTED_AND_NOT_USED": True,
        "EFFECT_ON_EVERY_PER_FEATURE_RATE": (
            "a feature sampled several times and left unmerged contributes "
            "several times to both numerator and denominator. Where those "
            "repeats are the same window, a per-feature accuracy is partly "
            "a measurement of one window. Every rate in the decision report "
            "must be read with this register beside it"),
        "PAIRS": pairs,
    }
    p = OUT / "07_CANONICALISATION_RESIDUAL_REGISTER.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    print(json.dumps({k: v for k, v in body.items()
                      if k not in ("PAIRS",)}, indent=2)[-1500:])
    print("SHA256", hashlib.sha256(p.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
