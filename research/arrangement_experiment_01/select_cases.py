"""Apply the pre-declared case-selection rules, and report what they did.

The rules were frozen in 00_EXPERIMENT_PROTOCOL.json before this ran.
Two of them collided with cases already chosen, and one of them was
stated twice in the protocol in two different forms. Neither is hidden:
the literal output of every rule is recorded beside what was finally
used, and every amendment is marked as made AFTER the collision was
seen.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.arrangement_experiment_01 import protocol as P

# The window a candidate's own crop covers in the frozen run. Recorded
# because "within its own crop window" has to mean a number somewhere.
CROP_HALF_MM = 5000.0

AMENDMENT_1 = (
    "CASE 6 was stated twice in the frozen protocol: CASE_TOKEN named "
    "DRIVER, and CASE_6_RULE described a mechanical choice by stair "
    "geometry. The mechanical rule was used, because a token hint chosen "
    "by hand is the thing the mechanical rule exists to replace. The "
    "token entry is recorded as UNUSED rather than deleted")

AMENDMENT_2 = (
    "CASE 6's mechanical winner and CASE 7's mechanical winner were each "
    "already selected for an earlier case. The protocol did not "
    "anticipate a collision. The amendment - made after the collision "
    "was seen, and recorded as such - is the least selective one "
    "available: keep the same ordering and take the next candidate that "
    "is not already selected. The literal winner is recorded beside it")


def _near(seed, points, half=CROP_HALF_MM):
    return [p for p in points
            if abs(p[0] - seed[0]) <= half and abs(p[1] - seed[1]) <= half]


def select(run_dir) -> dict:
    run = Path(run_dir)
    chain = json.loads((run / "E1_4_PHYSICAL_BOUNDARY_CHAIN_REGISTER.json")
                       .read_text(encoding="utf-8"))["CANDIDATES"]
    v2 = json.loads((run / "E1_4_VISUAL_V2_REGISTER.json")
                    .read_text(encoding="utf-8"))["answers"]
    doors = json.loads((run / "E1_4_DOOR_ENTITY_REGISTER.json")
                       .read_text(encoding="utf-8"))["DOORS"]
    ivs = json.loads((run / "E1_4_ATOMIC_INTERVAL_ROLE_REGISTER.json")
                     .read_text(encoding="utf-8"))["INTERVALS"]

    by_id = {c["CANDIDATE_ID"]: c for c in chain}
    v2_by = {a["candidate_id"]: a for a in v2}
    stair_pts = [tuple(x["START_MM"]) for x in ivs
                 if x["ROLE"] == "STAIR_GEOMETRY"]
    door_pts = [tuple(x["at_mm"]) for x in doors]

    stat = {}
    for c in chain:
        s = c.get("SEED_MM")
        if not s:
            continue
        stat[c["CANDIDATE_ID"]] = {
            "identity": c["IDENTITY_AS_DRAWN"],
            "stair_intervals_in_window": len(_near(s, stair_pts)),
            "door_entities_in_window": len(_near(s, door_pts)),
            "E1_4_BOUNDARY_BASIS": c["BOUNDARY_BASIS"],
        }

    chosen, rows = {}, []

    def take(case, cid, rule, literal=None, note=None):
        chosen[case] = cid
        rows.append({
            "CASE": case, "CANDIDATE_ID": cid,
            "IDENTITY_AS_DRAWN": (stat.get(cid) or {}).get("identity"),
            "E1_4_BOUNDARY_BASIS": (stat.get(cid) or {}).get(
                "E1_4_BOUNDARY_BASIS"),
            "RULE_APPLIED": rule,
            "LITERAL_RULE_WINNER": literal,
            "AMENDMENT_NOTE": note,
        })

    # cases 1-5, by the token the drawing carries
    def by_token(token, released_only=False):
        got = [c["CANDIDATE_ID"] for c in chain
               if c["IDENTITY_AS_DRAWN"] == token
               and (not released_only
                    or c["BOUNDARY_BASIS"] == "ENCLOSED_BY_DRAWN_MATERIAL")]
        return sorted(got)

    c1 = by_token("W.C", released_only=True)
    take(P.CASE_CATEGORIES[0], c1[0] if c1 else None,
         "lowest stable id among candidates carrying W.C that E1.4 released")
    take(P.CASE_CATEGORIES[1], (by_token("KITCHEN") or [None])[0],
         "lowest stable id carrying KITCHEN")
    take(P.CASE_CATEGORIES[2], (by_token("PANTRY") or [None])[0],
         "lowest stable id carrying PANTRY")
    cluster = sorted(by_token("SALOON") + by_token("RECEPTION")
                     + by_token("DINING"))
    take(P.CASE_CATEGORIES[3], (by_token("SALOON") or [None])[0],
         "lowest stable id carrying SALOON; the cluster it anchors is "
         "SALOON + RECEPTION + DINING")
    rows[-1]["CLUSTER_MEMBER_IDS"] = cluster
    take(P.CASE_CATEGORIES[4], (by_token("SWIMMING POOL") or [None])[0],
         "lowest stable id carrying SWIMMING POOL")

    taken = set(x for x in chosen.values() if x) | set(cluster)

    # case 6, by the mechanical stair rule
    order6 = sorted(stat.items(),
                    key=lambda kv: (-kv[1]["stair_intervals_in_window"], kv[0]))
    with_stair = [k for k, v in order6 if v["stair_intervals_in_window"] > 0]
    literal6 = with_stair[0] if with_stair else None
    pick6 = next((k for k in with_stair if k not in taken), None)
    if not with_stair:
        take(P.CASE_CATEGORIES[5], None,
             "no candidate carries stair geometry in its window",
             note="NOT_PRESENT_ON_THIS_FLOOR; the experiment runs with six "
                  "cases and says so")
    else:
        take(P.CASE_CATEGORIES[5], pick6,
             "most stair-geometry intervals within the crop window, ties "
             "by lowest stable id; skipping candidates already selected",
             literal=literal6,
             note=None if pick6 == literal6 else AMENDMENT_2)
        rows[-1]["STAIR_INTERVALS_IN_WINDOW"] = (
            stat[pick6]["stair_intervals_in_window"] if pick6 else None)
        rows[-1]["PROTOCOL_STATED_THIS_CASE_TWICE"] = AMENDMENT_1
        rows[-1]["UNUSED_TOKEN_HINT"] = P.CASE_TOKEN.get(
            P.CASE_CATEGORIES[5])
    if pick6:
        taken.add(pick6)

    # case 7, by the cold-review rule
    falsely = sorted(a["candidate_id"] for a in v2
                     if "WALL_FALSELY_REMOVED" in a["statuses"])
    with_door = [c for c in falsely
                 if stat.get(c, {}).get("door_entities_in_window", 0) > 0]
    relaxed = False
    pool = with_door
    if not pool:
        pool, relaxed = falsely, True
    literal7 = pool[0] if pool else None
    pick7 = next((c for c in pool if c not in taken), None)
    take(P.CASE_CATEGORIES[6], pick7,
         "first by stable id among candidates whose frozen cold V2 answer "
         "carries WALL_FALSELY_REMOVED and which carry drawn door evidence "
         "in the crop window; skipping candidates already selected",
         literal=literal7,
         note=None if pick7 == literal7 else AMENDMENT_2)
    rows[-1]["ALL_WALL_FALSELY_REMOVED_IN_ID_ORDER"] = falsely
    rows[-1]["DOOR_CONDITION_RELAXED"] = relaxed
    rows[-1]["V2_STATUSES"] = (v2_by.get(pick7) or {}).get("statuses")

    return {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "THE_RULES_WERE_FROZEN_BEFORE_THIS_RAN": True,
        "CROP_HALF_MM": CROP_HALF_MM,
        "AMENDMENTS_MADE_AFTER_SEEING_THE_RESULT": [AMENDMENT_1, AMENDMENT_2],
        "CASES": rows,
        "CANDIDATE_STATISTICS_USED_BY_THE_RULES": stat,
        "no_expected_area_was_used_to_choose_any_case": True,
    }
