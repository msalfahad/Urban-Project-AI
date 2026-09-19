"""Canonicalise the frozen sample and build the blind reference packages.

Order matters and is enforced here: the scoring protocol is written and
hashed first, the clustering uses source geometry only, and the reference
packages are assembled with no A19 answer and no E1.4 classification in
them. Nothing in this file opens an A19 output.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from research.semantic_edge_scoring_01 import protocol as P

EXP = Path("data/experiments/SEMANTIC_EDGE_EXPERIMENT_01")
OUT = Path("data/experiments/SEMANTIC_EDGE_SCORING_01")

# Tokens that could only appear if an ANSWER had leaked in. The shared
# vocabularies (FEATURE_ASSEMBLY_TYPES, ENTITY_SUB_ROLES, RELATIONS) are
# the question and must be present; naming one of them here would be
# checking that the reference was never asked anything.
FORBIDDEN_IN_A_REFERENCE_PACKAGE = (
    "PASS_A", "PASS_B", "CHECKER", "E1_4", "A19",
    "ASSEMBLY_CONFIDENCE", "YOUR_FROZEN", "SEMANTIC_ROLE",
)


def write(path: Path, body) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (body if isinstance(body, str)
            else json.dumps(body, indent=2, ensure_ascii=False,
                            default=str) + "\n")
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def parent_of(interval_id: str) -> str:
    """The CAD entity an interval is a stretch of. Source identity only."""
    body = interval_id.split(":", 1)[-1]
    return body.rsplit("#", 1)[0]


def _overlap(a, b) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


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


def canonicalise(groups):
    ids = sorted(g["FEATURE_GROUP_ID"] for g in groups)
    by_id = {g["FEATURE_GROUP_ID"]: g for g in groups}
    prim_ent = {i: {parent_of(x) for x in by_id[i]["PRIMARY_ENTITY_IDS"]}
                for i in ids}
    all_ent = {i: {parent_of(x) for x in (by_id[i]["PRIMARY_ENTITY_IDS"]
                                          + by_id[i]["CONTEXT_ENTITY_IDS"])}
               for i in ids}
    prim_iv = {i: set(by_id[i]["PRIMARY_ENTITY_IDS"]) for i in ids}
    box = {i: by_id[i]["LOCAL_TOPOLOGY"]["bounding_box_mm"] for i in ids}

    declared, why = [], {}
    sens_interval, sens_any = [], []
    for n, a in enumerate(ids):
        for b in ids[n + 1:]:
            shared = prim_ent[a] & prim_ent[b]
            if shared and _overlap(box[a], box[b]):
                declared.append((a, b))
                why[(a, b)] = sorted(shared)
            if prim_iv[a] & prim_iv[b]:
                sens_interval.append((a, b))
            if all_ent[a] & all_ent[b]:
                sens_any.append((a, b))

    clusters = sorted(_closure(ids, declared), key=lambda c: c[0])
    rows = []
    for n, c in enumerate(sorted(clusters, key=lambda c: c[0]), start=1):
        reasons = []
        for (a, b), ents in why.items():
            if a in c and b in c:
                reasons.append({"GROUP_A": a, "GROUP_B": b,
                                "SHARED_PARENT_ENTITIES": ents,
                                "BOUNDING_BOXES_OVERLAP": True})
        pu, cu = set(), set()
        for g in c:
            pu |= set(by_id[g]["PRIMARY_ENTITY_IDS"])
            cu |= set(by_id[g]["CONTEXT_ENTITY_IDS"])
        rows.append({
            "CANONICAL_FEATURE_CLUSTER_ID": f"{P.CANONICAL_ID_PREFIX}{n:03d}",
            "MEMBER_FEATURE_GROUP_IDS": c,
            "PRIMARY_ENTITY_UNION": sorted(pu),
            "CONTEXT_ENTITY_UNION": sorted(cu),
            "PRIMARY_PARENT_ENTITY_UNION": sorted(
                {parent_of(x) for x in pu}),
            "OVERLAP_REASON": (reasons if reasons else
                               [{"WHY": "no other group shares a primary "
                                        "parent entity within an "
                                        "overlapping extent"}]),
            "STRATA": sorted({by_id[g]["STRATUM"] for g in c}),
        })
    return rows, {
        "DECLARED_RULE_CLUSTERS": len(clusters),
        "SENSITIVITY_SHARED_PRIMARY_INTERVAL_CLUSTERS":
            len(_closure(ids, sens_interval)),
        "SENSITIVITY_SHARED_ANY_MEMBER_ENTITY_CLUSTERS":
            len(_closure(ids, sens_any)),
        "groups": len(ids),
    }


def curve_artefact(groups, tasks):
    """§3 - which curve questions were asked with no curve to answer about."""
    rows = []
    for g in groups:
        gid = g["FEATURE_GROUP_ID"]
        t = tasks[gid]
        if not t["CURVE_FAMILY_IS_REQUIRED"]:
            continue
        kinds = {m["GEOMETRY_KIND"] for m in t["MARKED_MEMBERS"]}
        curved = bool(kinds & {"ARC", "CIRCLE"})
        rows.append({
            "FEATURE_GROUP_ID": gid,
            "STRATUM": g["STRATUM"],
            "MARKED_MEMBER_GEOMETRY_KINDS": sorted(kinds),
            "A_MARKED_MEMBER_IS_A_CURVE": curved,
            "SCORING_STATUS": (None if curved
                               else P.CURVE_QUESTION_NOT_APPLICABLE),
        })
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    proto_hash = write(OUT / "00_SCORING_PROTOCOL.json", P.record())

    groups = json.loads((EXP / "02_FEATURE_GROUP_REGISTER.json")
                        .read_text(encoding="utf-8"))["GROUPS"]
    crops = {r["FEATURE_GROUP_ID"]: r["CROPS"] for r in json.loads(
        (EXP / "03_CROP_REGISTER.json").read_text(encoding="utf-8"))[
            "BY_GROUP"]}
    tasks = {}
    for g in groups:
        gid = g["FEATURE_GROUP_ID"]
        tasks[gid] = json.loads(
            (EXP / "a19" / "pass_a_sandbox" / gid / "TASK.json")
            .read_text(encoding="utf-8"))

    rows, counts = canonicalise(groups)
    artefact = curve_artefact(groups, tasks)
    cl_hash = write(OUT / "01_CANONICAL_FEATURE_CLUSTER_REGISTER.json", {
        "SCORING_ID": P.SCORING_ID,
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "THE_FROZEN_EXPERIMENT_IS_NOT_ALTERED": True,
        "RULE": P.CANONICAL_RULE,
        "why_parent_entity_and_not_interval":
            P.WHY_PARENT_ENTITY_AND_NOT_INTERVAL,
        "why_the_bounding_box_condition": P.WHY_THE_BOUNDING_BOX_CONDITION,
        "NO_SEMANTIC_ANSWER_WAS_USED_TO_CLUSTER": True,
        "the_count_is_reported_not_assumed": P.THE_COUNT_IS_REPORTED_NOT_ASSUMED,
        "frozen_feature_groups": counts["groups"],
        "canonical_features": counts["DECLARED_RULE_CLUSTERS"],
        "SENSITIVITY": {
            "SHARED_PRIMARY_INTERVAL":
                counts["SENSITIVITY_SHARED_PRIMARY_INTERVAL_CLUSTERS"],
            "SHARED_ANY_MEMBER_ENTITY":
                counts["SENSITIVITY_SHARED_ANY_MEMBER_ENTITY_CLUSTERS"],
            "RULES": list(P.SENSITIVITY_RULES),
            "these_are_reported_and_not_used": True,
        },
        "CURVE_QUESTION_ARTEFACT": {
            "RULE": P.CURVE_ARTEFACT_RULE,
            "groups_asked_the_curve_question": len(artefact),
            "of_which_had_no_marked_curve": sum(
                1 for r in artefact if not r["A_MARKED_MEMBER_IS_A_CURVE"]),
            "THIS_IS_A_SAMPLING_PROTOCOL_DEFECT_NOT_A_READER_ERROR": True,
            "ROWS": artefact,
        },
        "CLUSTERS": rows,
    })

    # ---- the reference packages, blind ------------------------------
    box = OUT / "reference_sandbox"
    if box.exists():
        shutil.rmtree(box)
    manifest = []
    for c in rows:
        cid = c["CANONICAL_FEATURE_CLUSTER_ID"]
        d = box / cid
        d.mkdir(parents=True)
        members, files = [], []
        for gid in c["MEMBER_FEATURE_GROUP_IDS"]:
            sub = d / gid
            sub.mkdir()
            for cr in crops[gid]:
                shutil.copy(EXP / "crops" / gid / cr["FILE"],
                            sub / cr["FILE"])
                files.append(f"{gid}/{cr['FILE']}")
            for m in tasks[gid]["MARKED_MEMBERS"]:
                members.append({
                    "FEATURE_GROUP_ID": gid,
                    "MEMBER_LABEL": m["MEMBER_LABEL"],
                    "IS_PRIMARY": m["IS_PRIMARY"],
                    "LAYER": m["LAYER"],
                    "ENTITY_TYPE": m["ENTITY_TYPE"],
                    "GEOMETRY_KIND": m["GEOMETRY_KIND"],
                    "LINETYPE": m["LINETYPE"],
                    "BLOCK": m["BLOCK"],
                })
        task = {
            "CANONICAL_FEATURE_CLUSTER_ID": cid,
            "WHAT_YOU_ARE_LOOKING_AT": (
                "one local architectural feature of a ground floor plan. "
                "Where more than one folder is present they are different "
                "views of the SAME feature, marked through different "
                "members, and they are deliberately shown together"),
            "VIEWS": c["MEMBER_FEATURE_GROUP_IDS"],
            "CROPS": sorted(files),
            "MARKED_MEMBERS": members,
            "FEATURE_ASSEMBLY_TYPES": list(P.FEATURE_ASSEMBLY_TYPES),
            "ENTITY_SUB_ROLES": list(P.ENTITY_SUB_ROLES),
            "RELATIONS": list(P.RELATIONS),
            "CONFIDENCE_CLASSES": list(P.CONFIDENCE_CLASSES),
            "ANSWER_SCHEMA": {
                "CANONICAL_FEATURE_CLUSTER_ID": "copied from this file",
                "REFERENCE_ROLE": "one FEATURE_ASSEMBLY_TYPE",
                "REFERENCE_CONFIDENCE": "one CONFIDENCE_CLASS",
                "REFERENCE_EVIDENCE": "prose: what in the picture says so",
                "NEEDS_ADDITIONAL_CONTEXT": "true or false",
                "ENTITY_REFERENCE": [{
                    "FEATURE_GROUP_ID": "as given in MARKED_MEMBERS",
                    "MEMBER_LABEL": "as given in MARKED_MEMBERS",
                    "REFERENCE_ROLE": "one ENTITY_SUB_ROLE",
                    "REFERENCE_CONFIDENCE": "one CONFIDENCE_CLASS",
                    "REFERENCE_EVIDENCE": "prose"}],
                "REFERENCE_RELATIONS": [{
                    "RELATION": "one RELATION",
                    "MEMBER_LABELS": ["FEATURE_GROUP_ID/MEMBER_LABEL", "..."],
                    "REFERENCE_EVIDENCE": "prose"}],
            },
        }
        write(d / "REFERENCE_TASK.json", task)
        write(d / "BRIEF.txt", BRIEF)
        shutil.copy(EXP / "a19" / "pass_a_sandbox"
                    / c["MEMBER_FEATURE_GROUP_IDS"][0] / "FLOOR_CONTEXT.txt",
                    d / "FLOOR_CONTEXT.txt")
        manifest.append({
            "CANONICAL_FEATURE_CLUSTER_ID": cid,
            "VIEWS": c["MEMBER_FEATURE_GROUP_IDS"],
            "marked_members": len(members),
            "crops": len(files),
            "TASK_SHA256": sha(d / "REFERENCE_TASK.json"),
            "BRIEF_SHA256": sha(d / "BRIEF.txt"),
            "FLOOR_CONTEXT_SHA256": sha(d / "FLOOR_CONTEXT.txt"),
        })

    # prove the sandbox carries nothing it must not
    leaks = []
    for p in sorted(box.rglob("*")):
        if p.is_file() and p.suffix in (".json", ".txt"):
            text = p.read_text(encoding="utf-8", errors="replace")
            for bad in FORBIDDEN_IN_A_REFERENCE_PACKAGE:
                if bad in text:
                    leaks.append({"file": str(p.relative_to(box)),
                                  "carries": bad})
    if leaks:
        raise SystemExit(f"the reference sandbox is not blind: {leaks[:5]}")

    man_hash = write(OUT / "02_REFERENCE_INPUT_MANIFEST.json", {
        "SCORING_ID": P.SCORING_ID,
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "PACKAGE_CONTAINS": list(P.REFERENCE_PACKAGE_CONTAINS),
        "PACKAGE_MUST_NOT_CONTAIN": list(P.REFERENCE_PACKAGE_MUST_NOT_CONTAIN),
        "THE_SANDBOX_WAS_SEARCHED_FOR_EVERY_FORBIDDEN_TOKEN": list(
            FORBIDDEN_IN_A_REFERENCE_PACKAGE),
        "NOTHING_FORBIDDEN_WAS_FOUND": True,
        "read_cold": P.THE_REFERENCE_IS_READ_COLD,
        "may_not_guess": P.THE_REFERENCE_MAY_NOT_GUESS,
        "canonical_features": len(manifest),
        "TASKS": manifest,
    })

    print(json.dumps({
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "00_SCORING_PROTOCOL_SHA256": proto_hash,
        "01_CANONICAL_CLUSTER_REGISTER_SHA256": cl_hash,
        "02_REFERENCE_INPUT_MANIFEST_SHA256": man_hash,
        "frozen_feature_groups": counts["groups"],
        "canonical_features": counts["DECLARED_RULE_CLUSTERS"],
        "sensitivity_shared_primary_interval":
            counts["SENSITIVITY_SHARED_PRIMARY_INTERVAL_CLUSTERS"],
        "sensitivity_shared_any_member_entity":
            counts["SENSITIVITY_SHARED_ANY_MEMBER_ENTITY_CLUSTERS"],
        "curve_questions_asked": len(artefact),
        "curve_questions_with_no_marked_curve": sum(
            1 for r in artefact if not r["A_MARKED_MEMBER_IS_A_CURVE"]),
    }, indent=2))
    return 0


BRIEF = """\
INDEPENDENT REFERENCE READING OF ONE LOCAL ARCHITECTURAL FEATURE.

You are establishing what the drawing actually shows, so that someone
else's reading of the same picture can later be graded against yours. You
have not been shown that reading and you must not look for it.

WHAT YOU HAVE

  crops of the source drawing at up to three scales. Where several view
  folders are present they are the SAME feature marked through different
  members - look at all of them
  the marked members, each with an index label, its CAD layer, linetype,
  entity type and block where the drawing exposes them
  a general note about the floor. It does not tell you what any line is

Members are drawn in red with index labels; unlabelled blue members are
context to look at, not to answer about.

ONE CAD LINE IS NOT ONE ARCHITECTURAL THING

A window is usually glass, frame, jambs, wall returns, sometimes
mullions. A door is a leaf, a swing, jambs, an opening, maybe a
threshold. A pool is a water boundary, a coping, a rim, and often setting
out curves that mean nothing built. Answer the ASSEMBLY first, then its
members.

WHAT TO ANSWER

  REFERENCE_ROLE          what the marked group is, as a whole
  REFERENCE_CONFIDENCE    HIGH, MEDIUM, LOW or UNRESOLVED - a word, never
                          a number or a percentage
  REFERENCE_EVIDENCE      what in the picture establishes it
  NEEDS_ADDITIONAL_CONTEXT  true if the crops do not settle it
  ENTITY_REFERENCE        per labelled member, where the drawing settles
                          it. A member is named by its view folder and its
                          label
  REFERENCE_RELATIONS     how the members go together

DO NOT GUESS

This is the whole point of your reading. Where the drawing does not
establish whether something is glazing or frame, a water edge or a
coping, a wall or a low partition, answer UNRESOLVED and say why. A
fabricated answer here silently corrupts everything computed from it, and
it looks exactly like a good result.

WHAT YOU MAY NOT DO

  do not state or invent a coordinate, a dimension, an area, a perimeter,
  a length or any quantity, and put no numbers in your prose
  do not propose a corrected line, a polygon or a closed room
  do not choose a reading because it would make a space close neatly
  do not give a probability
"""


if __name__ == "__main__":
    raise SystemExit(main())
