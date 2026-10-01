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


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "locations": [SEPARATE_SITE, INSIDE_SITE],
           "states": [INCLUDED, EXCLUDED, ALLOCATED, SIDES_DIFFER, SIDE_UNRESOLVED, NOT_IN_ROW],
           "blocking": list(BLOCKING), "release_blockers": list(RELEASE),
           "never": ["a strip absorbed into a row without a record", "a strip dropped from every row without a "
                     "release blocker", "a strip allocated by its size", "a threshold given the floor finish of a "
                     "neighbouring room without an allocation authority"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
