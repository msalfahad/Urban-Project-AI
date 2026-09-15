"""E78 — two recall numbers, because a hypothesis must not inflate one.

`PROJECT_SPACE_RECALL = 9 / 17` answered a question nobody asked. It counted
components holding exactly one labelled room on the DIAGNOSTIC geometry —
which includes rooms that exist only because unestablished wall material was
treated as masonry, and rooms whose partition rests on a portal only one
evidence family supports.

So there are two, and they are not the same measurement:

    DIAGNOSTIC_SPACE_GEOMETRY_RECALL
        how many rooms the engine can produce a plausible polygon for.
        Useful: it says how much of the floor is within reach.

    RELEASE_ELIGIBLE_SPACE_GEOMETRY_RECALL
        how many rooms have a polygon EVERY boundary contributor of which
        satisfies production-level evidence:
            established wall material
            releasable portal geometry
            a validated measurement basis
            exactly one labelled space inside
        This is the number a quantity may be built on.

The gap between them is the size of the hypothesis. Reporting only the first
would let a diagnostic guess count as a measured room.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DIAGNOSTIC_RECALL = "DIAGNOSTIC_SPACE_GEOMETRY_RECALL"
RELEASE_RECALL = "RELEASE_ELIGIBLE_SPACE_GEOMETRY_RECALL"

# Why a single-label component is not release-eligible.
BLOCK_UNESTABLISHED = "BOUNDARY_RESTS_ON_UNESTABLISHED_WALL_MATERIAL"
BLOCK_DIAGNOSTIC_BARRIER = "PARTITION_DEPENDS_ON_A_DIAGNOSTIC_PORTAL"
BLOCK_MULTI_LABEL = "COMPONENT_HOLDS_MORE_THAN_ONE_LABELLED_SPACE"
BLOCK_NO_BASIS = "MEASUREMENT_BASIS_NOT_VALIDATED"
BLOCK_ROLE = "GEOMETRY_ROLE_IS_NOT_AN_OCCUPIABLE_SPACE"

BLOCKS = (BLOCK_UNESTABLISHED, BLOCK_DIAGNOSTIC_BARRIER, BLOCK_MULTI_LABEL,
          BLOCK_NO_BASIS, BLOCK_ROLE)

VALID_BASIS = "CLEAR_INTERNAL_FINISH_FACE"


@dataclass(frozen=True)
class SpaceEligibility:
    space_geometry_id: str
    space_ids: tuple[str, ...]
    area_m2: float
    blocks: tuple[str, ...] = ()
    unestablished_m: float = 0.0
    barrier_release_class: str = ""
    why: str = ""

    @property
    def release_eligible(self) -> bool:
        return not self.blocks

    def record(self) -> dict:
        return {"space_geometry_id": self.space_geometry_id,
                "space_ids": list(self.space_ids),
                "clear_internal_area_m2": round(self.area_m2, 3),
                "release_eligible": self.release_eligible,
                "blocks": list(self.blocks),
                "unestablished_boundary_m": round(self.unestablished_m, 3),
                "barrier_release_class": self.barrier_release_class,
                "why": self.why}


@dataclass
class Report:
    in_scope_spaces: int = 0
    rows: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    @property
    def diagnostic_count(self) -> int:
        return sum(1 for r in self.rows if len(r.space_ids) == 1)

    @property
    def release_count(self) -> int:
        return sum(1 for r in self.rows if r.release_eligible)

    def _pct(self, n: int):
        if not self.in_scope_spaces:
            return None
        return round(100.0 * n / self.in_scope_spaces, 1)

    def record(self) -> dict:
        from collections import Counter
        blocked = [r for r in self.rows
                   if len(r.space_ids) == 1 and not r.release_eligible]
        return {
            DIAGNOSTIC_RECALL: {
                "spaces_with_their_own_polygon": self.diagnostic_count,
                "in_scope_spaces": self.in_scope_spaces,
                "pct": self._pct(self.diagnostic_count),
                "basis": ("components of the DIAGNOSTIC free space holding "
                          "exactly one labelled space. Says how much of the "
                          "floor is within reach, not how much is measured"),
            },
            RELEASE_RECALL: {
                "spaces_with_a_releasable_polygon": self.release_count,
                "in_scope_spaces": self.in_scope_spaces,
                "pct": self._pct(self.release_count),
                "basis": ("every boundary contributor satisfies "
                          "production-level evidence: established wall "
                          "material, releasable portal geometry, a "
                          "validated measurement basis, and exactly one "
                          "labelled space inside"),
            },
            "the_gap_is_the_hypothesis": {
                "spaces": self.diagnostic_count - self.release_count,
                "why": ("this many rooms have a plausible polygon that no "
                        "quantity may be built on. Reporting only the "
                        "diagnostic figure would let a guess count as a "
                        "measured room"),
            },
            "single_label_but_blocked": [r.record() for r in blocked][:40],
            "block_reasons": dict(Counter(
                b for r in blocked for b in r.blocks)),
            "notes": dict(self.notes),
        }


def assess(candidates, *, labels_inside, dependency_of=None,
           release_of=None, in_scope_spaces: int = 0,
           occupiable_role: str = "OCCUPIABLE_SPACE_CANDIDATE") -> Report:
    """Both recalls, from the states that actually determine each."""
    rep = Report(in_scope_spaces=in_scope_spaces)
    for c in candidates:
        gid = c.space_geometry_id
        ids = tuple(labels_inside.get(gid, ()))
        blocks, dep_m, rel_class = [], 0.0, ""

        if getattr(c, "geometry_role", occupiable_role) != occupiable_role:
            blocks.append(BLOCK_ROLE)
        if len(ids) != 1:
            blocks.append(BLOCK_MULTI_LABEL)
        if getattr(c, "measurement_basis", VALID_BASIS) != VALID_BASIS:
            blocks.append(BLOCK_NO_BASIS)

        dep = dependency_of(c) if dependency_of is not None else None
        if dep and dep.get("depends_on_unestablished_material"):
            blocks.append(BLOCK_UNESTABLISHED)
            dep_m = dep.get("unestablished_boundary_length_m") or 0.0

        rel = release_of(c) if release_of is not None else None
        if rel:
            rel_class = rel.get("release_class", "")
            if rel_class == "DIAGNOSTIC_PARTITION_BARRIER":
                blocks.append(BLOCK_DIAGNOSTIC_BARRIER)

        rep.rows.append(SpaceEligibility(
            space_geometry_id=gid, space_ids=ids, area_m2=c.area_m2,
            blocks=tuple(blocks), unestablished_m=dep_m,
            barrier_release_class=rel_class,
            why=("every boundary contributor satisfies production-level "
                 "evidence" if not blocks else
                 "blocked by " + ", ".join(blocks))))
    rep.notes["candidates_examined"] = len(rep.rows)
    return rep
