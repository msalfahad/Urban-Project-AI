"""E76 — prove a repair is causal by removing everything else.

A leak localiser can point at a gap with complete confidence and still be
pointing at a symptom. The only way to know whether a repair matters is to
apply it, change NOTHING else, and see whether the partition improves.

    RUN A   the established wall solid
    RUN B   the same solid plus ONLY the named repairs

Same envelope construction, same barriers, same snap grid, same labels. If
the repairs are the dominant cause, the difference shows it. If they are
not, the run says so — which is the outcome this module exists to allow.

The comparison is of SPACE PARTITIONING, not of wall-solid component count.
A disconnected wall component is not automatically defective and 46 -> 1 is
not a goal.
"""

from __future__ import annotations

from dataclasses import dataclass, field

RUN_A = "ESTABLISHED_SOLID_ONLY"
RUN_B = "ESTABLISHED_SOLID_PLUS_NAMED_REPAIRS"


@dataclass
class Arm:
    """One arm of the experiment, and what its partition looks like."""

    name: str
    solid_area_m2: float = 0.0
    solid_components: int = 0
    free_components: int = 0
    occupiable: int = 0
    single_room: int = 0
    multi_room: int = 0
    labels_placed: int = 0
    largest_blob_labels: int = 0
    largest_blob_area_m2: float = 0.0
    blob_sizes: tuple = ()
    control_holders: dict = field(default_factory=dict)
    free_area_m2: float = 0.0

    def record(self) -> dict:
        return {"arm": self.name,
                "wall_solid_area_m2": round(self.solid_area_m2, 4),
                "wall_solid_components": self.solid_components,
                "free_space_components": self.free_components,
                "occupiable_candidates": self.occupiable,
                "single_room_candidates": self.single_room,
                "multi_room_candidates": self.multi_room,
                "labels_placed_in_a_component": self.labels_placed,
                "largest_blob_labels": self.largest_blob_labels,
                "largest_blob_area_m2": round(self.largest_blob_area_m2, 3),
                "multi_room_blob_label_counts": list(self.blob_sizes),
                "control_holder_label_counts": dict(self.control_holders),
                "free_space_area_m2": round(self.free_area_m2, 4)}


def observe(name: str, solid_geom, *, wall_polys, barriers, portals,
            regions, contains, controls=(), run_id="CF") -> Arm:
    """Run the free-space path on one solid and describe its partition."""
    from engine.free_space import (OCCUPIABLE_SPACE_CANDIDATE,
                                   build_free_space,
                                   envelope_from_wall_solid)

    class _Solid:
        def __init__(self, geom):
            self.geometry = geom
            self.snap_grid_mm = 0.0

    solid = _Solid(solid_geom)
    env = envelope_from_wall_solid(solid, barriers, wall_polys)
    cands, _ = build_free_space(env, solid, barriers, wall_polys,
                                run_id=run_id)

    inside = {}
    for c in cands:
        ids = tuple(sorted(
            r["space_id"] for r in regions.values() if r.get("space_id")
            and contains(c, r["centroid_mm"])))
        inside[c.space_geometry_id] = ids

    occ = [c for c in cands
           if c.geometry_role == OCCUPIABLE_SPACE_CANDIDATE]
    sizes = sorted((len(inside[c.space_geometry_id]) for c in cands
                    if len(inside[c.space_geometry_id]) > 1), reverse=True)
    biggest = max(
        ((len(inside[c.space_geometry_id]), c.area_m2) for c in cands),
        default=(0, 0.0))
    return Arm(
        name=name,
        solid_area_m2=(0.0 if solid_geom is None
                       else solid_geom.area / 1e6),
        solid_components=(0 if solid_geom is None else
                          len(solid_geom.geoms)
                          if solid_geom.geom_type.startswith("Multi") else 1),
        free_components=len(cands), occupiable=len(occ),
        single_room=sum(1 for c in cands
                        if len(inside[c.space_geometry_id]) == 1),
        multi_room=len(sizes),
        labels_placed=sum(len(v) for v in inside.values()),
        largest_blob_labels=biggest[0], largest_blob_area_m2=biggest[1],
        blob_sizes=tuple(sizes),
        control_holders={
            sid: len(inside[c.space_geometry_id])
            for sid in controls for c in cands
            if sid in inside[c.space_geometry_id]},
        free_area_m2=sum(c.area_m2 for c in cands))


def compare(a: Arm, b: Arm, *, repairs=()) -> dict:
    """Did the named repairs improve the PARTITION, or only the solid?"""
    gained = b.single_room - a.single_room
    split = a.largest_blob_labels - b.largest_blob_labels
    verdict = _verdict(gained, split, len(repairs))
    return {
        "run_a": a.record(),
        "run_b": b.record(),
        "repairs_applied": list(repairs),
        "repairs_applied_count": len(repairs),
        "delta": {
            "single_room_candidates": gained,
            "free_space_components": (b.free_components
                                      - a.free_components),
            "multi_room_candidates": b.multi_room - a.multi_room,
            "largest_blob_labels": -split,
            "largest_blob_area_m2": round(
                b.largest_blob_area_m2 - a.largest_blob_area_m2, 3),
            "wall_solid_area_m2": round(
                b.solid_area_m2 - a.solid_area_m2, 6),
            "free_space_area_m2": round(b.free_area_m2 - a.free_area_m2, 4),
        },
        "verdict": verdict[0],
        "why": verdict[1],
        "what_changed_between_the_arms": (
            "the named repairs and nothing else. Same envelope "
            "construction, same barriers, same snap grid, same labels"),
        "what_is_not_compared": (
            "wall-solid component count as a quality target. A "
            "disconnected wall component is not automatically defective, "
            "and the measure here is SPACE PARTITIONING"),
    }


DOMINANT = "REPAIRS_ARE_CAUSAL_AND_DOMINANT"
CONTRIBUTORY = "REPAIRS_ARE_CAUSAL_BUT_NOT_DOMINANT"
NOT_CAUSAL = "REPAIRS_CHANGED_NOTHING_IN_THE_PARTITION"


def _verdict(gained: int, split: int, n: int) -> tuple[str, str]:
    if gained <= 0 and split <= 0:
        return NOT_CAUSAL, (
            f"applying {n} repair(s) changed neither the number of "
            "single-room candidates nor the size of the largest merged "
            "component. Whatever merges those rooms, it is not these gaps — "
            "and the localiser pointing at them is not evidence that it is")
    if split >= 2 or gained >= 2:
        return DOMINANT, (
            f"{n} repair(s) split the largest component by {split} label(s) "
            f"and produced {gained} more single-room candidate(s)")
    return CONTRIBUTORY, (
        f"{n} repair(s) produced {gained} more single-room candidate(s) and "
        f"reduced the largest component by {split} label(s). Real, and not "
        "the dominant cause of the merging")
