"""E85 — a frozen control is only frozen if something checks it every run.

BED-01's diagnostic result is frozen: 21.034 m², and no round may tune it.
A freeze that lives in a directive and a docs table is not a freeze — it is
a hope. So the pin is declared in code and asserted on every run.

The pin carries TWO hashes on purpose. The geometry hash changed once, at
the Round 1.5 geometry-authority unification, when the clear-internal
polygon was re-derived through one authority instead of two paths. The AREA
did not move: 21.034 m² before and after. Recording only the current hash
would erase that history, and recording only the original would fail every
run. Both are named, with the commit that superseded one.

The AREA is the invariant that matters, because it is the measurement. A
hash change with an unchanged area means the polygon was re-expressed; a
changed area means the result was tuned, which is refused.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- the pin -------------------------------------------------------------

FROZEN_SPACE_ID = "BED-01"
FROZEN_AREA_M2 = 21.034
# Tolerance is the reporting precision of the frozen figure itself, not a
# tuning allowance: 21.034 was stated to 3 dp, so anything that rounds to
# it is the same number and anything else is a different result.
FROZEN_AREA_TOLERANCE_M2 = 0.0005

# The hash as frozen in TOPOLOGY_REFACTOR_ROUND_1, and the hash since the
# Round 1.5 unification. Either is the frozen geometry; a third is not.
HASH_AS_ORIGINALLY_FROZEN = "6ef3d4fc44a410d0fb1f2452"
HASH_SINCE_ROUND_1_5 = "415a3d1f0b56188cdd2c9ff4"
HASH_SUPERSEDED_AT = "162a7de"
ACCEPTED_HASHES = (HASH_AS_ORIGINALLY_FROZEN, HASH_SINCE_ROUND_1_5)

HELD = "FROZEN_RESULT_HELD"
RE_EXPRESSED = "FROZEN_RESULT_HELD_UNDER_A_RE_EXPRESSED_GEOMETRY"
MOVED = "FROZEN_RESULT_MOVED"
ABSENT = "FROZEN_CONTROL_NOT_PRESENT_IN_THIS_RUN"


@dataclass(frozen=True)
class Check:
    space_id: str
    status: str
    observed_area_m2: float | None
    observed_hash: str
    why: str

    @property
    def holds(self) -> bool:
        return self.status in (HELD, RE_EXPRESSED)

    def record(self) -> dict:
        return {
            "space_id": self.space_id,
            "FROZEN_RESULT_STATUS": self.status,
            "holds": self.holds,
            "pinned_area_m2": FROZEN_AREA_M2,
            "observed_area_m2": self.observed_area_m2,
            "observed_geometry_hash": self.observed_hash,
            "accepted_geometry_hashes": list(ACCEPTED_HASHES),
            "hash_history": {
                "as_originally_frozen": HASH_AS_ORIGINALLY_FROZEN,
                "since_round_1_5": HASH_SINCE_ROUND_1_5,
                "superseded_at_commit": HASH_SUPERSEDED_AT,
                "why_two_hashes": (
                    "the polygon was re-derived through one geometry "
                    "authority at the Round 1.5 unification. The AREA did "
                    "not move, so the result is the same result under a "
                    "re-expressed geometry — not a tuned one"),
            },
            "what_a_new_polygon_requires": (
                "if independently supported recovery ever produces a "
                "different BED-01 polygon, it becomes a NEW geometry record "
                "with a NEW hash. The frozen one is not mutated, and this "
                "check is not widened to accept it"),
            "why": self.why,
        }


def check(frozen_rows) -> Check:
    """Assert the pin against whatever this run actually produced."""
    row = next((r for r in frozen_rows
                if r.get("space_id") == FROZEN_SPACE_ID), None)
    if row is None:
        return Check(FROZEN_SPACE_ID, ABSENT, None, "",
                     "no frozen-control row for this space in this run, so "
                     "the pin could not be asserted. That is a failure to "
                     "check, not a pass")

    area = row.get("clear_internal_area_m2")
    got_hash = row.get("geometry_hash") or ""
    moved = (area is None
             or abs(float(area) - FROZEN_AREA_M2) > FROZEN_AREA_TOLERANCE_M2)

    if moved:
        return Check(
            FROZEN_SPACE_ID, MOVED, area, got_hash,
            f"the frozen result is {FROZEN_AREA_M2} m² and this run "
            f"produced {area} m². A frozen diagnostic result may not be "
            "altered by any repair, recovery or tolerance change")
    if got_hash in ACCEPTED_HASHES:
        return Check(
            FROZEN_SPACE_ID, HELD, area, got_hash,
            f"{FROZEN_AREA_M2} m² under a known geometry hash. Nothing "
            "this round touched the frozen control")
    return Check(
        FROZEN_SPACE_ID, RE_EXPRESSED, area, got_hash,
        f"the area is unchanged at {FROZEN_AREA_M2} m², but the geometry "
        f"hash {got_hash} is neither of the two on record. The measurement "
        "holds and the polygon's expression changed — which needs a stated "
        "reason before the new hash is added to the pin")
