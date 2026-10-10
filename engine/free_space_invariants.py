"""E66 — the replacement spine has no rotation system, and still needs proof.

The old path failed because nobody checked it. Removing the rotation system
removes one class of defect; it does not remove the obligation. So the
free-space path gets its own falsifiers, and the important one is the last:

    AREA(ENVELOPE) == AREA(BARRIERS INSIDE ENVELOPE) + AREA(FREE SPACE)

Every square millimetre of the envelope is either obstacle or space. If the
identity does not close, geometry was lost between the subtraction and the
components — and that loss would be invisible in every other report.

    THE TOLERANCE IS ABSOLUTE, NOT A PERCENTAGE. A percentage on a 1000 m2
    envelope hides 5 m2 of lost topology inside "0.5% agreement". The whole
    point is to catch small absolute losses on a large floor.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

INV_WALL_POLYGON_VALID = "A_EVERY_WALL_POLYGON_VALID_OR_EXPLICITLY_REJECTED"
INV_SOLID_VALID = "B_WALL_SOLID_IS_VALID"
INV_FREE_VALID = "C_EVERY_FREE_SPACE_POLYGON_IS_VALID"
INV_NO_FREE_OVERLAP = "D_ACCEPTED_FREE_SPACE_POLYGONS_DO_NOT_OVERLAP"
INV_INSIDE_ENVELOPE = "E_EVERY_FREE_SPACE_POLYGON_LIES_INSIDE_THE_ENVELOPE"
INV_NO_SOLID_INTERSECTION = "F_NO_FREE_SPACE_INTERSECTS_THE_WALL_SOLID"
INV_NO_BARRIER_INTERSECTION = "G_NO_FREE_SPACE_INTERSECTS_A_PORTAL_BARRIER"
INV_AREA_CONSERVED = "H_ENVELOPE_AREA_EQUALS_BARRIERS_PLUS_FREE_SPACE"

INVARIANTS = (INV_WALL_POLYGON_VALID, INV_SOLID_VALID, INV_FREE_VALID,
              INV_NO_FREE_OVERLAP, INV_INSIDE_ENVELOPE,
              INV_NO_SOLID_INTERSECTION, INV_NO_BARRIER_INTERSECTION,
              INV_AREA_CONSERVED)

# ABSOLUTE tolerances, in mm^2 and mm. Chosen from what GEOS does on this
# coordinate range, not from what would make a report pass.
#
# 10,000 mm^2 is one square centimetre. On a 1000 m2 envelope that is
# 0.00001% — deliberately far tighter than any percentage anybody would
# write, because the failure mode being hunted is a SMALL ABSOLUTE LOSS on a
# LARGE FLOOR.
AREA_TOLERANCE_MM2 = 10_000.0
# Positive-area overlap below this is a shared-boundary artefact.
OVERLAP_TOLERANCE_MM2 = 1.0
# A polygon may poke this far outside the envelope before it counts: the
# envelope's own ring is built from the same coordinates.
CONTAINMENT_TOLERANCE_MM = 1.0


class FreeSpaceFalsified(RuntimeError):
    """An invariant of the free-space construction does not hold."""


@dataclass(frozen=True)
class Violation:
    invariant: str
    detail: str
    ids: tuple[str, ...] = ()
    measure: float | None = None

    def record(self) -> dict:
        return {"invariant": self.invariant, "detail": self.detail,
                "ids": list(self.ids),
                "measure": (None if self.measure is None
                            else round(self.measure, 3))}


@dataclass
class Report:
    violations: list = field(default_factory=list)
    checked: dict = field(default_factory=dict)

    @property
    def holds(self) -> bool:
        return not self.violations

    def by_invariant(self) -> dict:
        return dict(Counter(v.invariant for v in self.violations))

    def record(self) -> dict:
        return {"holds": self.holds,
                "invariants_checked": list(INVARIANTS),
                "violations": len(self.violations),
                "by_invariant": self.by_invariant(),
                "failing_invariants": sorted(self.by_invariant()),
                "absolute_tolerances": {
                    "area_mm2": AREA_TOLERANCE_MM2,
                    "overlap_mm2": OVERLAP_TOLERANCE_MM2,
                    "containment_mm": CONTAINMENT_TOLERANCE_MM},
                "checked": dict(self.checked),
                "detail": [v.record() for v in self.violations[:60]],
                "note": ("tolerances are ABSOLUTE. A percentage on a 1000 m2 "
                         "envelope would hide several square metres of lost "
                         "topology inside an agreeable-looking figure")}


def falsify(wall_polys, solid, barriers, envelope, candidates) -> Report:
    """Every invariant. Repairs nothing."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from shapely.validation import explain_validity
    from engine.free_space import BARRIER_ACCEPTED

    rep = Report()
    v = rep.violations

    # A — a wall polygon is valid, or it was explicitly refused.
    for wp in wall_polys:
        if not wp.is_resolved:
            if not wp.unresolved_reason:
                v.append(Violation(
                    INV_WALL_POLYGON_VALID,
                    f"{wp.wall_band_id} has no ring and no stated reason. A "
                    "band that produced nothing must say why",
                    ids=(wp.wall_band_id,)))
            continue
        p = Polygon(list(wp.ring))
        if not p.is_valid:
            v.append(Violation(
                INV_WALL_POLYGON_VALID,
                f"{wp.wall_band_id} is resolved but invalid: "
                f"{explain_validity(p)}", ids=(wp.wall_band_id,)))

    # B — the union.
    if solid.geometry is not None and not solid.geometry.is_valid:
        v.append(Violation(
            INV_SOLID_VALID,
            f"the wall solid is invalid: {explain_validity(solid.geometry)}"))

    # C / D / E / F / G — the components.
    # The SAME grid the obstacle set was built on. Checking an unsnapped
    # barrier against a snapped difference would be checking two different
    # geometries and calling the discrepancy a violation.
    from engine.free_space import _on_grid
    grid = getattr(solid, "snap_grid_mm", 0.0)
    accepted = [_on_grid(Polygon(list(b.ring)), grid) for b in barriers
                if b.status == BARRIER_ACCEPTED and b.ring]
    barrier_union = unary_union(accepted) if accepted else None
    for c in candidates:
        cid = c.space_geometry_id
        if not c.geometry.is_valid:
            v.append(Violation(
                INV_FREE_VALID,
                f"{cid} is not a valid polygon: "
                f"{explain_validity(c.geometry)}", ids=(cid,)))
        if envelope.geometry is not None:
            outside = c.geometry.difference(
                envelope.geometry.buffer(CONTAINMENT_TOLERANCE_MM))
            if outside.area > OVERLAP_TOLERANCE_MM2:
                v.append(Violation(
                    INV_INSIDE_ENVELOPE,
                    f"{cid} has {outside.area / 1e6:.4f} m2 outside the "
                    "building envelope. Free space cannot exist where the "
                    "floor does not",
                    ids=(cid,), measure=outside.area))
        if solid.geometry is not None:
            hit = c.geometry.intersection(solid.geometry)
            if hit.area > OVERLAP_TOLERANCE_MM2:
                v.append(Violation(
                    INV_NO_SOLID_INTERSECTION,
                    f"{cid} overlaps the wall solid by "
                    f"{hit.area / 1e6:.4f} m2. Space and material cannot "
                    "occupy the same millimetre",
                    ids=(cid,), measure=hit.area))
        if barrier_union is not None:
            hit = c.geometry.intersection(barrier_union)
            if hit.area > OVERLAP_TOLERANCE_MM2:
                v.append(Violation(
                    INV_NO_BARRIER_INTERSECTION,
                    f"{cid} overlaps a portal partition barrier by "
                    f"{hit.area / 1e6:.4f} m2. A barrier is there precisely "
                    "to keep free space out",
                    ids=(cid,), measure=hit.area))
    ids = [c.space_geometry_id for c in candidates]
    for i, a in enumerate(candidates):
        for b in candidates[i + 1:]:
            hit = a.geometry.intersection(b.geometry)
            if hit.area > OVERLAP_TOLERANCE_MM2:
                v.append(Violation(
                    INV_NO_FREE_OVERLAP,
                    f"{a.space_geometry_id} and {b.space_geometry_id} share "
                    f"{hit.area / 1e6:.4f} m2. Connected components of one "
                    "geometry are disjoint, so this means the free space was "
                    "not built from a single difference",
                    ids=(a.space_geometry_id, b.space_geometry_id),
                    measure=hit.area))

    # H — the conservation identity. The barrier union is CLIPPED to the
    # envelope and taken as a union, so overlapping barriers are counted once
    # and geometry outside the floor is not counted at all.
    if envelope.geometry is not None:
        env_area = envelope.geometry.area
        parts = ([solid.geometry] if solid.geometry is not None else []) \
            + accepted
        obstacles = unary_union(parts) if parts else None
        inside = (obstacles.intersection(envelope.geometry)
                  if obstacles is not None else None)
        obstacle_area = inside.area if inside is not None else 0.0
        free_area = sum(c.geometry.area for c in candidates)
        residual = env_area - (obstacle_area + free_area)
        rep.checked["area_conservation"] = {
            "envelope_m2": round(env_area / 1e6, 4),
            "obstacles_inside_envelope_m2": round(obstacle_area / 1e6, 4),
            "free_space_m2": round(free_area / 1e6, 4),
            "residual_m2": round(residual / 1e6, 6),
            "residual_mm2": round(residual, 1),
            "tolerance_mm2": AREA_TOLERANCE_MM2,
            "identity": ("ENVELOPE = OBSTACLES INSIDE ENVELOPE + FREE SPACE. "
                         "The obstacle term is a UNION clipped to the "
                         "envelope, so overlapping barriers count once"),
        }
        if abs(residual) > AREA_TOLERANCE_MM2:
            v.append(Violation(
                INV_AREA_CONSERVED,
                f"{residual / 1e6:.4f} m2 of the envelope is neither obstacle "
                f"nor free space ({abs(residual):.0f} mm2 against an absolute "
                f"tolerance of {AREA_TOLERANCE_MM2:.0f} mm2). Geometry was "
                "lost between the subtraction and the components",
                measure=residual))

    rep.checked.update({
        "wall_polygons": len(wall_polys),
        "resolved_wall_polygons": sum(1 for w in wall_polys if w.is_resolved),
        "accepted_barriers": len(accepted),
        "free_space_components": len(candidates),
        "component_ids": ids[:20],
    })
    return rep


def assert_sound(wall_polys, solid, barriers, envelope, candidates) -> None:
    rep = falsify(wall_polys, solid, barriers, envelope, candidates)
    if not rep.holds:
        raise FreeSpaceFalsified(
            "the free-space construction does not hold:\n  - "
            + "\n  - ".join(v.detail for v in rep.violations[:10]))
