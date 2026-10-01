"""STRIP ALLOCATION AUDIT (R8.13) - a door threshold or an open-passage strip is never silently absorbed into, or
silently dropped from, a trade row.

Two topological facts decide where a strip already sits:
  SEPARATE_SITE   the strip is its own TS01 site (a door threshold between two door closures): a room-sum row does
                  NOT contain it by construction
  INSIDE_SITE     the strip lies inside a measured site (an open passage strip): a room-sum row DOES contain it

Per row, with the trade treatment of every side of the strip:
  INCLUDED_IN_SITE_SAME_TREATMENT     inside a row site and every side carries the row's treatment: the strip is
                                      in the row total, and that is recorded (never silent)
  EXCLUDED_SEPARATE_SITE              its own site; the row total excludes it; a STRIP_ALLOCATION release blocker is
                                      carried until an allocation authority exists (an allocation policy may set it)
  ALLOCATED_BY_POLICY                 an allocation authority assigns the strip (to a row, a side, or a separate item)
  BLOCKED_SIDES_DIFFER                inside a row site but its sides carry different treatments: the row cannot
                                      know which trade the strip belongs to -> BLOCKED_TRADE_RULE
  BLOCKED_SIDE_UNRESOLVED             a side has no authoritative treatment -> BLOCKED_TRADE_RULE
  NOT_IN_ROW                          no side belongs to the row

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "STRIP_ALLOCATION_AUDIT_V1"
SEPARATE_SITE, INSIDE_SITE = "SEPARATE_SITE", "INSIDE_SITE"
INCLUDED = "INCLUDED_IN_SITE_SAME_TREATMENT"
EXCLUDED = "EXCLUDED_SEPARATE_SITE"
ALLOCATED = "ALLOCATED_BY_POLICY"
SIDES_DIFFER = "BLOCKED_SIDES_DIFFER"
SIDE_UNRESOLVED = "BLOCKED_SIDE_UNRESOLVED"
NOT_IN_ROW = "NOT_IN_ROW"
BLOCKING = (SIDES_DIFFER, SIDE_UNRESOLVED)
RELEASE = (EXCLUDED,)


def audit(strip: dict, row_sites, side_treatments: dict, row_treatment: str, allocation=None) -> dict:
    """One strip for one row.
    strip: {"id", "kind" (THRESHOLD / OPEN_PASSAGE), "location" (SEPARATE_SITE / INSIDE_SITE), "sides": [site ids],
    "site" (the containing site for INSIDE_SITE), "area_m2"}; row_sites: the row's site ids; side_treatments:
    {site id: treatment or None}; allocation: an allocation authority record {"ref", "to"} or None."""
    sides = list(strip.get("sides") or ([strip["site"]] if strip.get("site") else []))
    rec = {"strip": strip["id"], "kind": strip["kind"], "location": strip["location"], "area_m2": strip["area_m2"],
           "sides": {s: side_treatments.get(s) for s in sides}}
    row_sites = set(row_sites)
    touches = (strip["location"] == INSIDE_SITE and strip.get("site") in row_sites) or \
        (strip["location"] == SEPARATE_SITE and row_sites & set(sides))
    if not touches:
        return dict(rec, state=NOT_IN_ROW, in_row_total=False)
    if allocation is not None:
        return dict(rec, state=ALLOCATED, in_row_total=allocation.get("to") == "ROW", allocation=allocation)
    if strip["location"] == SEPARATE_SITE:                 # outside every row site whatever its sides carry
        return dict(rec, state=EXCLUDED, in_row_total=False,
                    why="the strip is its own site; no allocation authority assigns it to a room")
    treats = [side_treatments.get(s) for s in sides]
    if any(t is None for t in treats):
        return dict(rec, state=SIDE_UNRESOLVED, in_row_total=True)
    if any(t != row_treatment for t in treats):
        return dict(rec, state=SIDES_DIFFER, in_row_total=True)
    return dict(rec, state=INCLUDED, in_row_total=True,
                why="inside the measured site and every side carries the row's treatment")


def row_effect(audits) -> dict:
    """What the audits mean for a row: blocking strips, release strips and the area of each."""
    blk = [a for a in audits if a["state"] in BLOCKING]
    rel = [a for a in audits if a["state"] in RELEASE]
    inc = [a for a in audits if a["state"] == INCLUDED]
    return {"blocking": [a["strip"] for a in blk], "release": [a["strip"] for a in rel],
            "included": [a["strip"] for a in inc],
            "excluded_area_m2": round(sum(a["area_m2"] for a in rel), 6),
            "included_area_m2": round(sum(a["area_m2"] for a in inc), 6)}


# ======================================================================== V2 (R8.14): allocations and heads
POLICY_ID_V2 = "STRIP_ALLOCATION_AUDIT_V2"
CEILING = "CEILING"
NOT_IN_TRADE = "NOT_IN_TRADE"
SOFFIT_EXCLUDED = "SOFFIT_EXCLUDED_FROM_CEILING"
HEAD_UNRESOLVED = "UNRESOLVED_HEAD_CONDITION"
RESOLVED_V2 = ("CONTINUOUS_SAME_FINISH", "SPLIT_AT_DOOR_PLANE", "MARBLE_THRESHOLD_EXPLICIT")
BLOCKING_V2 = BLOCKING + ("UNRESOLVED_TRANSITION_PLANE", "UNRESOLVED_FINISH", "UNRESOLVED_GEOMETRY")
RELEASE_V2 = (EXCLUDED, HEAD_UNRESOLVED)


def audit_v2(strip: dict, row_sites, side_treatments: dict, row_treatment: str, *, trade: str, allocation=None,
             head=None) -> dict:
    """V2: as audit(), plus (a) a door threshold with an authoritative transition allocation (door_transition) gives
    the row exactly its region(s); (b) for a CEILING trade a door threshold is the door's top reveal (NOT_IN_TRADE);
    (c) for a CEILING trade an open-passage strip needs its head condition: WITH_HEAD -> the soffit footprint leaves
    the ceiling, FULL_HEIGHT -> ceiling continues, unknown -> UNRESOLVED_HEAD_CONDITION (release blocker)."""
    sides = list(strip.get("sides") or ([strip["site"]] if strip.get("site") else []))
    rec = {"strip": strip["id"], "kind": strip["kind"], "location": strip["location"], "area_m2": strip["area_m2"],
           "sides": {x: side_treatments.get(x) for x in sides}, "trade": trade, "contribution_m2": 0.0}
    row_sites = set(row_sites)
    touches = (strip["location"] == INSIDE_SITE and strip.get("site") in row_sites) or \
        (strip["location"] == SEPARATE_SITE and row_sites & set(sides))
    if not touches:
        return dict(rec, state=NOT_IN_ROW, in_row_total=False)
    if strip["location"] == SEPARATE_SITE:
        if trade == CEILING:
            return dict(rec, state=NOT_IN_TRADE, in_row_total=False,
                        why="a door threshold's top is the door head reveal, never room ceiling")
        if allocation is None:
            return dict(rec, state=EXCLUDED, in_row_total=False, why="no allocation authority")
        st = allocation["state"]
        if st in RESOLVED_V2:
            c = sum(r["area"] for r in allocation["regions"] if r["treatment"] == row_treatment)
            return dict(rec, state=st, in_row_total=c > 0, contribution_m2=c, regions=allocation["regions"],
                        plane=allocation["plane"])
        return dict(rec, state=st, in_row_total=False, plane=allocation.get("plane"))
    if trade == CEILING:
        if head == "WITH_HEAD":
            return dict(rec, state=SOFFIT_EXCLUDED, in_row_total=False, contribution_m2=-strip["area_m2"])
        if head != "FULL_HEIGHT":
            return dict(rec, state=HEAD_UNRESOLVED, in_row_total=True,
                        why="the strip is inside the ceiling site but its head condition is not established")
    treats = [side_treatments.get(x) for x in sides]
    if any(t is None for t in treats):
        return dict(rec, state=SIDE_UNRESOLVED, in_row_total=True)
    if any(t != row_treatment for t in treats):
        return dict(rec, state=SIDES_DIFFER, in_row_total=True)
    return dict(rec, state=INCLUDED, in_row_total=True,
                why="inside the measured site and every side carries the row's treatment")


def row_effect_v2(audits) -> dict:
    blk = [a for a in audits if a["state"] in BLOCKING_V2]
    rel = [a for a in audits if a["state"] in RELEASE_V2]
    return {"blocking": [a["strip"] for a in blk], "release": [a["strip"] for a in rel],
            "release_area_m2": round(sum(a["area_m2"] for a in rel), 6),
            "threshold_contribution_m2": round(sum(a["contribution_m2"] for a in audits
                                                   if a["state"] in RESOLVED_V2), 6),
            "soffit_exclusion_m2": round(-sum(a["contribution_m2"] for a in audits if a["state"] == SOFFIT_EXCLUDED), 6),
            "passages_included": [a["strip"] for a in audits if a["state"] == INCLUDED],
            "not_in_trade": [a["strip"] for a in audits if a["state"] == NOT_IN_TRADE],
            "adjustment_m2": round(sum(a["contribution_m2"] for a in audits), 6)}


def policy_record_v2() -> dict:
    rec = {"policy_id": POLICY_ID_V2, "extends": POLICY_ID, "resolved": list(RESOLVED_V2),
           "blocking": list(BLOCKING_V2), "release_blockers": list(RELEASE_V2),
           "ceiling": {"door_threshold": NOT_IN_TRADE, "passage_with_head": SOFFIT_EXCLUDED,
                       "passage_full_height": INCLUDED, "passage_head_unknown": HEAD_UNRESOLVED},
           "never": ["a strip counted twice", "a strip in no row without a record", "a soffit as ceiling",
                     "a head condition transferred from another revision"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "locations": [SEPARATE_SITE, INSIDE_SITE],
           "states": [INCLUDED, EXCLUDED, ALLOCATED, SIDES_DIFFER, SIDE_UNRESOLVED, NOT_IN_ROW],
           "blocking": list(BLOCKING), "release_blockers": list(RELEASE),
           "never": ["a strip absorbed into a row without a record", "a strip dropped from every row without a "
                     "release blocker", "a strip allocated by its size", "a threshold given the floor finish of a "
                     "neighbouring room without an allocation authority"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
