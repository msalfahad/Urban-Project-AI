"""How much of the sample is the same feature seen twice? A measurement.

A Pass B reader noticed it before this code did: the same window appears
under two FEATURE_GROUP_IDs, and one stair flight edge under three. The
cause is in the frozen protocol, and it is worth stating plainly rather
than tidying away.

A group's identity is the SET of members assembled around its seed. Two
seeds a little apart assemble overlapping but not identical sets, so they
hash to two ids and the collision check - which only caught identical
sets - passed them both. The strata are populations of SEEDS, and a
population of seeds is not a population of features.

Nothing is renamed or merged here. The frozen registers stand as they
were produced. This measures the overlap so that a later scorer treats
thirty-four groups as thirty-four QUESTIONS and not as thirty-four
independent features.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.semantic_edge_experiment_01 import protocol as P

OUT = Path("data/experiments/SEMANTIC_EDGE_EXPERIMENT_01")


def main() -> int:
    groups = json.loads((OUT / "02_FEATURE_GROUP_REGISTER.json")
                        .read_text(encoding="utf-8"))["GROUPS"]
    prim = {g["FEATURE_GROUP_ID"]: set(g["PRIMARY_ENTITY_IDS"])
            for g in groups}
    allm = {g["FEATURE_GROUP_ID"]: set(g["PRIMARY_ENTITY_IDS"])
            | set(g["CONTEXT_ENTITY_IDS"]) for g in groups}
    stratum = {g["FEATURE_GROUP_ID"]: g["STRATUM"] for g in groups}

    ids = sorted(prim)
    pairs = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            shared_p = prim[a] & prim[b]
            shared_a = allm[a] & allm[b]
            if not shared_p and not shared_a:
                continue
            pairs.append({
                "GROUP_A": a, "GROUP_B": b,
                "STRATUM_A": stratum[a], "STRATUM_B": stratum[b],
                "shared_primary_members": len(shared_p),
                "shared_members_of_any_kind": len(shared_a),
                "A_PRIMARIES_ARE_A_SUBSET_OF_B": prim[a] <= prim[b],
                "B_PRIMARIES_ARE_A_SUBSET_OF_A": prim[b] <= prim[a],
                "THE_PRIMARY_SETS_ARE_EQUAL": prim[a] == prim[b],
            })

    # connected components under "share at least one primary member"
    parent = {i: i for i in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for p in pairs:
        if p["shared_primary_members"]:
            ra, rb = find(p["GROUP_A"]), find(p["GROUP_B"])
            if ra != rb:
                parent[ra] = rb
    comps = {}
    for i in ids:
        comps.setdefault(find(i), []).append(i)
    clusters = [sorted(v) for v in comps.values() if len(v) > 1]

    body = {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "WHAT_THIS_MEASURES": (
            "how many of the sampled feature neighbourhoods are the same "
            "drawn feature enumerated more than once"),
        "WHY_IT_HAPPENS": (
            "a group's identity is the SET of members assembled around its "
            "seed. Two seeds a little apart assemble overlapping but not "
            "identical sets, so they hash to two ids, and the protocol's "
            "collision check only caught identical sets. The ten strata "
            "are populations of SEEDS; a population of seeds is not a "
            "population of features"),
        "NOTHING_WAS_MERGED_OR_RENAMED": (
            "the frozen registers stand exactly as produced. The protocol "
            "was hashed before the sample existed and is not edited after "
            "seeing what it did"),
        "WHAT_A_LATER_SCORER_MUST_DO": (
            "treat the groups as QUESTIONS ASKED, not as independent "
            "features. Assembly accuracy averaged over a set that counts "
            "one window three times is not an average over windows"),
        "IT_WAS_A_READER_WHO_NOTICED": (
            "a Pass B reader reported that identical source intervals "
            "recur across different feature group ids before this "
            "measurement existed. That is the challenge round doing its "
            "job on the experiment's own apparatus, not only on E1.4"),
        "feature_groups": len(ids),
        "pairs_sharing_any_member": len(pairs),
        "pairs_sharing_a_primary_member": sum(
            1 for p in pairs if p["shared_primary_members"]),
        "pairs_with_identical_primary_sets": sum(
            1 for p in pairs if p["THE_PRIMARY_SETS_ARE_EQUAL"]),
        "clusters_of_groups_sharing_primaries": len(clusters),
        "groups_inside_such_a_cluster": sum(len(c) for c in clusters),
        "distinct_features_if_each_cluster_is_one_feature":
            len(ids) - sum(len(c) - 1 for c in clusters),
        "CLUSTERS": [{"GROUPS": c, "STRATA": sorted({stratum[g] for g in c})}
                     for c in clusters],
        "PAIRS": pairs,
    }
    p = OUT / "05_SAMPLE_REDUNDANCY.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    print(json.dumps({k: v for k, v in body.items()
                      if k not in ("PAIRS", "CLUSTERS")}, indent=2)[:1400])
    print("CLUSTERS", json.dumps(body["CLUSTERS"], indent=1)[:900])
    print("SHA256", hashlib.sha256(p.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
