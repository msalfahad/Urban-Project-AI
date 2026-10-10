"""E77 — a tolerance is safe or not by TOPOLOGY, never by area.

Last round reported the 0.05 mm grid as safe because it changed the wall
solid's total area by 0.0003 m2. That is the wrong test. Snapping moves
vertices onto a grid, and two vertices that land on the same grid node
become one node — which CONNECTS two pieces of geometry that were apart.
A connection is a topological event with no area cost at all, so an
area-based safety argument cannot see it.

The consequence is not academic. A connection created by rounding is a wall
where the drawing has none, and it closes a space the drawing leaves open.
It changes which rooms exist.

So the two grids are run and every connection present at the coarser grid
and absent at the finer one is found and classified:

    NUMERICAL_NOISE_JOIN     the two pieces were already within the
                             measured coordinate-noise floor: one node
                             recorded twice, and joining them is correct
    VALID_PHYSICAL_JUNCTION  an explicit junction patch covers this place
                             on its own evidence, so the join is right —
                             but it should come from the patch, not the
                             rounding
    FALSE_JOIN               the pieces are further apart than anything
                             the drawing's own coordinates justify, and
                             nothing supports a junction: rounding invented
                             a wall
    UNRESOLVED_JOIN          nothing available decides

Until every join is one of the first two, production uses the MEASURED
tolerance and physical junctions are repaired by JUNCTION_PATCH.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

NOISE_JOIN = "NUMERICAL_NOISE_JOIN"
VALID_JUNCTION = "VALID_PHYSICAL_JUNCTION"
FALSE_JOIN = "FALSE_JOIN"
UNRESOLVED_JOIN = "UNRESOLVED_JOIN"

JOIN_CLASSES = (NOISE_JOIN, VALID_JUNCTION, FALSE_JOIN, UNRESOLVED_JOIN)

# Only the first two make a coarser grid defensible.
BENIGN_JOINS = (NOISE_JOIN, VALID_JUNCTION)

# How close a join must be to a validated junction patch to be that patch's.
PATCH_REACH_MM = 50.0


@dataclass(frozen=True)
class Join:
    """One connection the coarser grid created and the finer one did not."""

    join_id: str
    join_class: str
    separation_mm: float
    noise_floor_mm: float | None
    fine_pieces: int
    patch_ids: tuple[str, ...] = ()
    centroid_mm: tuple = ()
    merged_area_m2: float = 0.0
    why: str = ""

    @property
    def is_benign(self) -> bool:
        return self.join_class in BENIGN_JOINS

    def record(self) -> dict:
        return {"join_id": self.join_id, "join_class": self.join_class,
                "separation_mm": round(self.separation_mm, 6),
                "measured_noise_floor_mm": self.noise_floor_mm,
                "pieces_joined": self.fine_pieces,
                "junction_patch_ids": list(self.patch_ids),
                "centroid_mm": [round(v, 1) for v in self.centroid_mm],
                "merged_component_area_m2": round(self.merged_area_m2, 4),
                "benign": self.is_benign, "why": self.why}


@dataclass
class Report:
    fine_grid_mm: float = 0.0
    coarse_grid_mm: float = 0.0
    fine_components: int = 0
    coarse_components: int = 0
    fine_area_m2: float = 0.0
    coarse_area_m2: float = 0.0
    joins: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    @property
    def coarse_is_defensible(self) -> bool:
        return all(j.is_benign for j in self.joins)

    def record(self) -> dict:
        return {
            "fine_grid_mm": self.fine_grid_mm,
            "coarse_grid_mm": self.coarse_grid_mm,
            "fine_components": self.fine_components,
            "coarse_components": self.coarse_components,
            "components_merged_by_the_coarser_grid": (
                self.fine_components - self.coarse_components),
            "fine_area_m2": round(self.fine_area_m2, 6),
            "coarse_area_m2": round(self.coarse_area_m2, 6),
            "area_difference_m2": round(
                self.coarse_area_m2 - self.fine_area_m2, 6),
            "why_area_is_not_the_test": (
                "a connection is a topological event with no area cost, so "
                "an area-based safety argument cannot see it. A "
                "microscopic change can still decide which rooms exist"),
            "joins": len(self.joins),
            "by_class": dict(Counter(j.join_class for j in self.joins)),
            "coarse_grid_is_defensible": self.coarse_is_defensible,
            "verdict": (
                "every join the coarser grid creates is either recorded "
                "coordinate noise or a place an explicit junction patch "
                "already justifies"
                if self.coarse_is_defensible else
                "at least one join is not justified by the measured noise "
                "floor or by a junction patch. Production uses the MEASURED "
                "tolerance, and physical junctions are repaired by "
                "JUNCTION_PATCH rather than by a larger global snap"),
            "detail": [j.record() for j in sorted(
                self.joins, key=lambda j: -j.separation_mm)][:40],
            "notes": dict(self.notes),
        }


def _pieces(geom) -> list:
    if geom is None or geom.is_empty:
        return []
    return (list(geom.geoms) if geom.geom_type.startswith("Multi")
            else [geom])


def diff(shapes, *, fine_mm: float, coarse_mm: float,
         noise_floor_mm: float | None = None, patches=()) -> Report:
    """Union the same shapes at two grids and classify every new join.

    `shapes` are the wall polygons as geometry, unsnapped. The comparison is
    of the two unions, so a join is a group of finely-snapped pieces that
    the coarse union merged into one component.
    """
    from shapely import set_precision
    from shapely.ops import unary_union

    raw = unary_union(list(shapes))
    fine = set_precision(raw, fine_mm) if fine_mm else raw
    coarse = set_precision(raw, coarse_mm) if coarse_mm else raw
    if not fine.is_valid:
        fine = fine.buffer(0)
    if not coarse.is_valid:
        coarse = coarse.buffer(0)

    fp, cp = _pieces(fine), _pieces(coarse)
    rep = Report(fine_grid_mm=fine_mm, coarse_grid_mm=coarse_mm,
                 fine_components=len(fp), coarse_components=len(cp),
                 fine_area_m2=fine.area / 1e6,
                 coarse_area_m2=coarse.area / 1e6)

    validated = [p for p in patches if p.is_validated and p.polygon is not None]
    n = 0
    for c in cp:
        # Which finely-snapped pieces this coarse component swallowed.
        held = [f for f in fp if f.representative_point().within(c)
                or f.intersection(c).area > 0.5 * f.area]
        if len(held) < 2:
            continue
        n += 1
        # How far apart the pieces it joined actually were, BEFORE snapping.
        sep = min(
            (a.distance(b) for i, a in enumerate(held)
             for b in held[i + 1:]), default=0.0)
        pt = c.representative_point()
        near = tuple(sorted(
            p.patch_id for p in validated
            if p.polygon.distance(c) <= PATCH_REACH_MM))
        cls, why = _classify(sep, noise_floor_mm, near, len(held))
        rep.joins.append(Join(
            join_id=f"SJ-{n:04d}", join_class=cls, separation_mm=sep,
            noise_floor_mm=noise_floor_mm, fine_pieces=len(held),
            patch_ids=near, centroid_mm=(pt.x, pt.y),
            merged_area_m2=c.area / 1e6, why=why))

    rep.notes["validated_patches_considered"] = len(validated)
    rep.notes["input_shapes"] = len(list(shapes))
    return rep


def _classify(sep: float, floor: float | None, patches: tuple,
              pieces: int) -> tuple[str, str]:
    if floor is not None and sep <= floor:
        return NOISE_JOIN, (
            f"the {pieces} pieces were {sep:.6g} mm apart, within the "
            f"measured {floor} mm coordinate-noise floor. This is one node "
            "recorded twice, and joining it is correct. The separation is "
            "quantised to the fine grid, so it is a bound rather than an "
            "exact distance: what it establishes is that the pieces are "
            "indistinguishable AT the measured noise floor")
    if patches:
        return VALID_JUNCTION, (
            f"an explicit junction patch ({', '.join(patches)}) covers this "
            "place on its own evidence, so the join is right. It should "
            "come from the patch rather than from the rounding, which "
            "cannot be reviewed or removed")
    if floor is not None:
        return FALSE_JOIN, (
            f"the {pieces} pieces were {sep:.6g} mm apart — further than "
            f"the measured {floor} mm noise floor — and no junction patch "
            "supports a physical junction here. The rounding invented a "
            "wall, and a wall the drawing does not have closes a space the "
            "drawing leaves open")
    return UNRESOLVED_JOIN, (
        f"{pieces} pieces {sep:.6g} mm apart, with no measured noise floor "
        "to compare against and no junction patch. Nothing available "
        "decides whether this join is real")
