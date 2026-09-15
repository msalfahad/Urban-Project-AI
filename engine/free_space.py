"""E61 — a room is a connected component of the free space, and nothing else.

    BARRIERS    = WALL_SOLID + supported PORTAL_PARTITION_BARRIERS
    FREE_SPACE  = BUILDING_ENVELOPE - BARRIERS
    SPACES      = connected polygon components of FREE_SPACE

The boundary of each component lies ON the drawn wall faces, because the walls
were subtracted as the polygons they actually are. So the result is already on
the CLEAR_INTERNAL_FINISH_FACE basis with no offsetting, no room-facing-face
determination, no corner correction and no mean-thickness adjustment. The
corners are right because nothing computed them.

A PORTAL PARTITION BARRIER is the one piece of geometry here that is not
material. A doorway is still four facts — zero wall material, a real opening,
part of the gross host-wall line, and a boundary between spaces — and the
barrier serves only the fourth. It exists to stop free space flowing through
the door, it is tagged as topology-only, and no quantity may ever read it as
wall.

    A BARRIER IS NOT MATERIAL. An open-plan transition gets none: it is one
    physical space, and a barrier there would invent a room.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

CLEAR_INTERNAL_FINISH_FACE = "CLEAR_INTERNAL_FINISH_FACE"

# ------------------------------------------------------------ the barriers

BARRIER_ACCEPTED = "BARRIER_ACCEPTED"
BARRIER_REJECTED = "BARRIER_REJECTED"
BARRIER_UNRESOLVED = "BARRIER_UNRESOLVED"

REJECT_OPEN_PLAN = "OPEN_PLAN_TRANSITION_IS_ONE_PHYSICAL_SPACE"
REJECT_GEOMETRY = "PORTAL_GEOMETRY_UNRESOLVED"
REJECT_NO_HOST = "PORTAL_HAS_NO_HOSTED_JAMB_GEOMETRY"

# Topology-only geometry, never material. The name is deliberately awkward.
TOPOLOGY_ONLY_NOT_MATERIAL = "TOPOLOGY_ONLY_NOT_MATERIAL"


@dataclass(frozen=True)
class PortalPartitionBarrier:
    """A temporary partition across a doorway, for space separation only."""

    portal_id: str
    ring: tuple
    host_wall_band_id: str
    jamb_a_mm: float
    jamb_b_mm: float
    axis: str
    closure_basis: str
    existence_status: str
    geometry_status: str
    existence_evidence: tuple[str, ...] = ()
    geometry_evidence: tuple[str, ...] = ()
    drawing_id: str = ""
    drawing_revision: str = ""
    status: str = BARRIER_UNRESOLVED
    material_role: str = TOPOLOGY_ONLY_NOT_MATERIAL
    why: str = ""

    @property
    def opening_width_mm(self) -> float:
        return abs(self.jamb_b_mm - self.jamb_a_mm)

    def record(self) -> dict:
        return {"portal_id": self.portal_id, "status": self.status,
                "host_wall_band_id": self.host_wall_band_id,
                "axis": self.axis,
                "jamb_a_mm": round(self.jamb_a_mm, 1),
                "jamb_b_mm": round(self.jamb_b_mm, 1),
                "opening_width_mm": round(self.opening_width_mm, 1),
                "closure_basis": self.closure_basis,
                "existence_status": self.existence_status,
                "geometry_status": self.geometry_status,
                "existence_evidence": list(self.existence_evidence),
                "geometry_evidence": list(self.geometry_evidence),
                "drawing_id": self.drawing_id,
                "drawing_revision": self.drawing_revision,
                "material_role": self.material_role,
                "vertices": len(self.ring),
                "why": self.why}


def partition_barriers(portals, wall_polys, *, drawing_id: str = "",
                       revision: str = "") -> list:
    """One barrier per geometry-supported hosted portal. Refusals included.

    The barrier spans the HOST WALL'S OWN THICKNESS, between the two jambs —
    so it plugs exactly the hole the wall solid leaves at the doorway, and the
    free-space boundary runs continuously along the wall's drawn faces through
    it. That is §7's "same finish-face basis", achieved by construction
    instead of by a closure rule.
    """
    from engine.space_boundary import GAP_OPEN_PLAN, GEOMETRY_SUFFICIENT
    by_band = {wp.wall_band_id: wp for wp in wall_polys}
    out = []
    for p in portals:
        host = by_band.get(
            p.hosted.host_wall_band_id if p.hosted else "", None)
        common = dict(
            portal_id=p.portal_id, axis=p.axis,
            host_wall_band_id=(host.wall_band_id if host else ""),
            jamb_a_mm=min(p.start_mm, p.end_mm),
            jamb_b_mm=max(p.start_mm, p.end_mm),
            closure_basis=CLEAR_INTERNAL_FINISH_FACE,
            existence_status=p.existence_status,
            geometry_status=p.geometry_status,
            existence_evidence=tuple(p.evidence),
            geometry_evidence=tuple(p.evidence),
            drawing_id=drawing_id, drawing_revision=revision)

        if p.gap_class == GAP_OPEN_PLAN:
            out.append(PortalPartitionBarrier(
                ring=(), status=BARRIER_REJECTED, why=(
                    "an open-plan transition is ONE physical space. A barrier "
                    "here would invent a room the building has not got"),
                **{**common, "host_wall_band_id": REJECT_OPEN_PLAN}))
            continue
        if p.geometry_status not in GEOMETRY_SUFFICIENT:
            out.append(PortalPartitionBarrier(
                ring=(), status=BARRIER_UNRESOLVED, why=(
                    "the portal may exist, but its jambs are not located. A "
                    "barrier drawn from non-geometric evidence would be an "
                    "invented measurement: " + p.geometry_why),
                **{**common, "host_wall_band_id": REJECT_GEOMETRY}))
            continue
        if host is None or not host.is_resolved:
            out.append(PortalPartitionBarrier(
                ring=(), status=BARRIER_UNRESOLVED, why=(
                    "no host wall polygon: there is no wall thickness for the "
                    "barrier to span, so the doorway cannot be plugged on the "
                    "wall's own faces"),
                **{**common, "host_wall_band_id": REJECT_NO_HOST}))
            continue

        lo = min(p.start_mm, p.end_mm)
        hi = max(p.start_mm, p.end_mm)
        f0 = min(host.face_a_mm, host.face_b_mm)
        f1 = max(host.face_a_mm, host.face_b_mm)
        ring = (((lo, f0), (hi, f0), (hi, f1), (lo, f1)) if host.axis == "H"
                else ((f0, lo), (f1, lo), (f1, hi), (f0, hi)))
        out.append(PortalPartitionBarrier(
            ring=ring, status=BARRIER_ACCEPTED, why=(
                "plugs the doorway across the HOST WALL'S OWN THICKNESS, so "
                "the free-space boundary runs continuously along that wall's "
                "drawn faces. Topology only: it is never wall material"),
            **common))
    return out


# ------------------------------------------------------------ the envelope

ENVELOPE_UNRESOLVED = "BUILDING_ENVELOPE_UNRESOLVED"
ENVELOPE_FROM_WALL_SOLID_HULL = "OUTER_BOUNDARY_OF_THE_WALL_SOLID"
ENVELOPE_FROM_CAD = "CAD_FLOOR_BOUNDARY"
ENVELOPE_FROM_PRINTED = "PRINTED_OVERALL_DIMENSIONS"

ENVELOPE_BASES = (ENVELOPE_FROM_WALL_SOLID_HULL, ENVELOPE_FROM_CAD,
                  ENVELOPE_FROM_PRINTED)


@dataclass(frozen=True)
class BuildingEnvelope:
    """The floor's outer extent, with the basis it was established on.

    The wall solid's outer boundary is NOT the usable floor envelope — it is
    where material is. Using it as the envelope is a stated approximation, and
    the free-space result carries that caveat rather than hiding it.

    A bounding rectangle is never acceptable here. BBOX IS NEVER PHYSICAL
    GEOMETRY, and an envelope invented that way would put free space where the
    building has none.
    """

    geometry: object = None
    basis: str = ENVELOPE_UNRESOLVED
    evidence: tuple[str, ...] = ()
    caveat: str = ""
    why: str = ""

    @property
    def is_resolved(self) -> bool:
        return self.geometry is not None and self.basis in ENVELOPE_BASES

    @property
    def area_m2(self) -> float:
        return 0.0 if self.geometry is None else self.geometry.area / 1e6

    def record(self) -> dict:
        return {"basis": self.basis, "is_resolved": self.is_resolved,
                "area_m2": round(self.area_m2, 3),
                "evidence": list(self.evidence),
                "caveat": self.caveat, "why": self.why}


def envelope_from_wall_solid(solid, barriers=()) -> BuildingEnvelope:
    """The filled outer boundary of the barrier set, as a stated approximation.

    The BARRIERS matter here, not just the wall solid. A ring of walls with a
    doorway in it is not a closed ring: its union is a C-shape, and filling a
    C's exterior returns the C, not the floor it encloses. Plugging the
    doorways first is what makes the outline closed — which is the same
    geometry the free-space subtraction uses, so the two cannot disagree.

    EVERY component is kept. Taking only the largest silently discards a
    second structure on the same sheet, and a drawing legitimately contains
    more than one.
    """
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    parts = [g for g in ([solid.geometry] if solid.geometry is not None
                         else []) if g is not None and not g.is_empty]
    parts += [Polygon(list(b.ring)) for b in barriers
              if b.status == BARRIER_ACCEPTED and b.ring]
    if not parts:
        return BuildingEnvelope(
            basis=ENVELOPE_UNRESOLVED,
            why=("no wall solid, so no envelope. Space extraction must say "
                 "so: a bounding rectangle is NOT an acceptable substitute"))
    closed = unary_union(parts)
    geoms = (list(closed.geoms) if closed.geom_type == "MultiPolygon"
             else [closed])
    filled = unary_union([Polygon(g.exterior) for g in geoms])
    return BuildingEnvelope(
        geometry=filled, basis=ENVELOPE_FROM_WALL_SOLID_HULL,
        evidence=("the filled outer rings of the wall solid plus the accepted "
                  "portal partition barriers",),
        caveat=("this is where MATERIAL is, not a surveyed floor boundary. An "
                "unclosed run of external wall makes it too small, and free "
                "space outside a genuine external wall would be included by "
                "it. Every candidate carries that caveat"),
        why=("derived, not assumed. An independent envelope from CAD or from "
             "printed overall dimensions would replace it and is preferred"))


# ---------------------------------------------------------- the free space

# What a free-space component turns out to be. GEOMETRY ROLE, NOT SEMANTICS:
# nothing here says BATHROOM.
OCCUPIABLE_SPACE_CANDIDATE = "OCCUPIABLE_SPACE_CANDIDATE"
SHAFT_CANDIDATE = "SHAFT_CANDIDATE"
SERVICE_VOID = "SERVICE_VOID"
WALL_CAVITY = "WALL_CAVITY"
EXTERNAL_FREE_SPACE = "EXTERNAL_FREE_SPACE"
ROLE_UNRESOLVED = "UNRESOLVED"

GEOMETRY_ROLES = (OCCUPIABLE_SPACE_CANDIDATE, SHAFT_CANDIDATE, SERVICE_VOID,
                  WALL_CAVITY, EXTERNAL_FREE_SPACE, ROLE_UNRESOLVED)

# Narrower than this cannot be occupied floor at any scale a house uses.
MIN_HABITABLE_MM = 700.0
# Smaller than this is a cavity or a void, not a room.
MIN_ROOM_AREA_M2 = 1.2
# A shaft is small but genuinely enterable-shaped.
MAX_SHAFT_AREA_M2 = 3.0
# Longer than this multiple of its width is a cavity between two walls.
CAVITY_ASPECT = 6.0

# §19 — four geometry states. Identity lives in engine.space_identity and
# stays there.
GEOMETRY_CANDIDATE = "GEOMETRY_CANDIDATE"
GEOMETRY_VALID = "GEOMETRY_VALID"
GEOMETRY_AMBIGUOUS = "GEOMETRY_AMBIGUOUS"
GEOMETRY_REJECTED = "GEOMETRY_REJECTED"


@dataclass(frozen=True)
class SpaceGeometryCandidate:
    """One connected component of the free space.

    Its boundary is on the drawn wall faces by construction, so
    `measurement_basis` is CLEAR_INTERNAL_FINISH_FACE with no conversion and
    no adjustment term anywhere in the type.
    """

    space_geometry_id: str
    geometry: object
    geometry_role: str
    geometry_status: str
    measurement_basis: str = CLEAR_INTERNAL_FINISH_FACE
    bounding_band_ids: tuple[str, ...] = ()
    bounding_portal_ids: tuple[str, ...] = ()
    hole_count: int = 0
    min_extent_mm: float = 0.0
    aspect: float = 0.0
    touches_envelope_boundary: bool = False
    blockers: tuple[str, ...] = ()
    provenance: dict = field(default_factory=dict)
    why: str = ""

    @property
    def area_m2(self) -> float:
        return self.geometry.area / 1e6

    @property
    def perimeter_m(self) -> float:
        return self.geometry.length / 1000

    @property
    def polygon_mm(self) -> tuple:
        return tuple(self.geometry.exterior.coords)[:-1]

    @property
    def releasable(self) -> bool:
        """Geometry alone never releases. Identity is a separate question."""
        return False

    def record(self) -> dict:
        return {"space_geometry_id": self.space_geometry_id,
                "geometry_role": self.geometry_role,
                "geometry_status": self.geometry_status,
                "measurement_basis": self.measurement_basis,
                "clear_internal_area_m2": round(self.area_m2, 3),
                "clear_internal_perimeter_m": round(self.perimeter_m, 3),
                "vertices": len(self.polygon_mm),
                "holes": self.hole_count,
                "min_extent_mm": round(self.min_extent_mm, 1),
                "aspect": round(self.aspect, 2),
                "bounding_band_ids": list(self.bounding_band_ids),
                "bounding_portal_ids": list(self.bounding_portal_ids),
                "touches_envelope_boundary": self.touches_envelope_boundary,
                "blockers": list(self.blockers),
                "releasable": self.releasable,
                "provenance": dict(self.provenance),
                "why": self.why}


def _role(poly, *, min_extent: float, aspect: float, touches_env: bool
          ) -> tuple[str, str]:
    """The GEOMETRY role. Never a room name."""
    area = poly.area / 1e6
    if touches_env:
        return EXTERNAL_FREE_SPACE, (
            "this component reaches the envelope boundary, so it is outside "
            "the enclosed floor or the envelope is under-established")
    if min_extent < MIN_HABITABLE_MM:
        return WALL_CAVITY, (
            f"{min_extent:.0f} mm across at its narrowest: too narrow to be "
            "occupied floor at any scale a house uses")
    if aspect >= CAVITY_ASPECT:
        return WALL_CAVITY, (
            f"aspect {aspect:.1f}: a long thin void between two walls")
    if area < MIN_ROOM_AREA_M2:
        return SERVICE_VOID, (
            f"{area:.3f} m2 is below the smallest usable room on this floor")
    if area <= MAX_SHAFT_AREA_M2:
        return SHAFT_CANDIDATE, (
            f"{area:.3f} m2 and compact: shaft-sized rather than room-sized")
    return OCCUPIABLE_SPACE_CANDIDATE, (
        f"{area:.3f} m2, {min_extent:.0f} mm at its narrowest: a candidate "
        "occupiable space. WHICH space is a separate question")


def build_free_space(envelope, solid, barriers, wall_polys, *,
                     run_id: str = "") -> tuple[list, dict]:
    """Subtract the barriers from the envelope; each component is a candidate."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    health = {"envelope": envelope.record(),
              "barriers_accepted": 0, "barriers_rejected": 0,
              "barriers_unresolved": 0}
    for b in barriers:
        key = {BARRIER_ACCEPTED: "barriers_accepted",
               BARRIER_REJECTED: "barriers_rejected",
               BARRIER_UNRESOLVED: "barriers_unresolved"}[b.status]
        health[key] += 1

    if not envelope.is_resolved:
        health["free_space"] = None
        health["why"] = (
            "the building envelope is unresolved, so free space cannot be "
            "computed. It is NOT approximated by a bounding rectangle")
        return [], health

    accepted = [Polygon(list(b.ring)) for b in barriers
                if b.status == BARRIER_ACCEPTED and b.ring]
    parts = ([solid.geometry] if solid.geometry is not None else []) + accepted
    obstacles = unary_union(parts) if parts else None
    free = (envelope.geometry.difference(obstacles) if obstacles is not None
            else envelope.geometry)

    geoms = (list(free.geoms) if free.geom_type == "MultiPolygon"
             else ([free] if not free.is_empty else []))
    by_band = {wp.wall_band_id: Polygon(list(wp.ring))
               for wp in wall_polys if wp.is_resolved}
    by_portal = {b.portal_id: Polygon(list(b.ring)) for b in barriers
                 if b.status == BARRIER_ACCEPTED and b.ring}
    # The envelope may be several structures on one sheet, so its boundary is
    # the union of their outlines rather than one exterior ring.
    env_boundary = unary_union([
        g.exterior for g in (
            list(envelope.geometry.geoms)
            if envelope.geometry.geom_type == "MultiPolygon"
            else [envelope.geometry])])

    out = []
    for i, g in enumerate(sorted(geoms, key=lambda p: -p.area), 1):
        if g.is_empty or g.area <= 0:
            continue
        x0, y0, x1, y1 = g.bounds
        w, h = x1 - x0, y1 - y0
        small, large = min(w, h), max(w, h)
        aspect = (large / small) if small else 0.0
        touches = g.exterior.intersection(env_boundary).length > 1.0
        role, why = _role(g, min_extent=small, aspect=aspect,
                          touches_env=touches)
        # Lineage: which drawn walls and which barriers bound this component.
        bands = tuple(sorted(
            bid for bid, p in by_band.items()
            if g.exterior.intersection(p).length > 1.0))
        ports = tuple(sorted(
            pid for pid, p in by_portal.items()
            if g.exterior.intersection(p).length > 1.0))
        blockers = []
        status = GEOMETRY_VALID
        if not g.is_valid:
            status, blockers = GEOMETRY_AMBIGUOUS, ["the polygon is invalid"]
        if not bands:
            status = GEOMETRY_AMBIGUOUS
            blockers.append(
                "no drawn wall face bounds this component, so its boundary is "
                "not supported by physical geometry")
        if touches:
            blockers.append(envelope.caveat)
        out.append(SpaceGeometryCandidate(
            space_geometry_id=f"SG-{run_id}-{i:04d}" if run_id
            else f"SG-{i:04d}",
            geometry=g, geometry_role=role, geometry_status=status,
            bounding_band_ids=bands, bounding_portal_ids=ports,
            hole_count=len(g.interiors), min_extent_mm=small, aspect=aspect,
            touches_envelope_boundary=touches, blockers=tuple(blockers),
            provenance={"method": "ENVELOPE_MINUS_WALL_SOLID_AND_BARRIERS",
                        "geometry_kernel": "GEOS via shapely",
                        "envelope_basis": envelope.basis,
                        "bbox_derived_edges": 0,
                        "raster_derived_edges": 0,
                        "centreline_offset_used": False,
                        "scalar_conversion_used": False},
            why=why))

    health["free_space"] = {
        "components": len(out),
        "by_role": dict(Counter(c.geometry_role for c in out)),
        "by_geometry_status": dict(Counter(c.geometry_status for c in out)),
        "total_free_area_m2": round(sum(c.area_m2 for c in out), 3),
        "occupiable_candidates": sum(
            1 for c in out if c.geometry_role == OCCUPIABLE_SPACE_CANDIDATE),
        "components_with_no_wall_support": sum(
            1 for c in out if not c.bounding_band_ids),
    }
    return out, health


def assert_non_overlapping(candidates) -> None:
    """Free-space components cannot overlap. Checked, not assumed.

    They are connected components of one geometry, so they are disjoint by
    construction — which is exactly the property the old planar path could not
    provide. Asserting it costs nothing and would catch a regression.
    """
    for i, a in enumerate(candidates):
        for b in candidates[i + 1:]:
            if a.geometry.intersection(b.geometry).area > 1.0:
                raise ValueError(
                    f"{a.space_geometry_id} and {b.space_geometry_id} overlap. "
                    "Connected components of one geometry are disjoint, so "
                    "this means the free space was not built from a single "
                    "difference operation")
