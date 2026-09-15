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


def _on_grid(geom, grid: float):
    """Put a barrier on the SAME coordinate grid as the wall solid.

    The audit caught this: wall polygons were snapped before the union and
    barriers were not, so `solid - barriers` left slivers of 2-25 mm2 and free
    space overlapped the very barriers meant to exclude it. The fix is a
    coherent obstacle set, not a wider tolerance — an invariant one may widen
    to pass is not an invariant.
    """
    if not grid:
        return geom
    from shapely import set_precision
    return set_precision(geom, grid)


# ------------------------------------------------------------ the barriers

BARRIER_ACCEPTED = "BARRIER_ACCEPTED"
BARRIER_REJECTED = "BARRIER_REJECTED"
BARRIER_UNRESOLVED = "BARRIER_UNRESOLVED"

REJECT_OPEN_PLAN = "OPEN_PLAN_TRANSITION_IS_ONE_PHYSICAL_SPACE"
REJECT_GEOMETRY = "PORTAL_GEOMETRY_UNRESOLVED"
REJECT_NO_HOST = "PORTAL_HAS_NO_HOSTED_JAMB_GEOMETRY"

# Topology-only geometry, never material. The name is deliberately awkward.
TOPOLOGY_ONLY_NOT_MATERIAL = "TOPOLOGY_ONLY_NOT_MATERIAL"

# A barrier is accepted geometrically long before it is trustworthy enough to
# let a quantity out of the door. These two classes keep that apart.
#
# A PORTAL_PROBABLE may generate a space HYPOTHESIS: closing it produces a
# component someone can look at, name and argue about, and that is useful.
# What it may NOT do is make the resulting space releasable, because the
# entire space depends on an opening that only one evidence family supports.
# If the portal is not really there, the space is not really there — and a
# released quantity carries no memory of which portal it rested on.
DIAGNOSTIC_PARTITION_BARRIER = "DIAGNOSTIC_PARTITION_BARRIER"
RELEASABLE_PARTITION_BARRIER = "RELEASABLE_PARTITION_BARRIER"
BARRIER_RELEASE_UNRESOLVED = "BARRIER_RELEASE_UNRESOLVED"

# A component no barrier bounds. The policy is silent about it, and silence
# is not a clearance.
NOT_CONSTRAINED_BY_A_BARRIER = "NOT_CONSTRAINED_BY_A_BARRIER"

RELEASE_CLASSES = (DIAGNOSTIC_PARTITION_BARRIER,
                   RELEASABLE_PARTITION_BARRIER,
                   BARRIER_RELEASE_UNRESOLVED,
                   NOT_CONSTRAINED_BY_A_BARRIER)


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

    @property
    def release_class(self) -> str:
        """May a space that depends on this barrier be released?

        Only if the portal's EXISTENCE is validated — two independent
        evidence families, not one family twice. Geometry being sufficient
        is necessary and nowhere near enough: a barrier can be drawn to the
        millimetre across an opening that is not there.
        """
        from engine.space_boundary import (EXISTENCE_VALIDATED,
                                           GEOMETRY_SUFFICIENT)
        if self.status != BARRIER_ACCEPTED:
            return BARRIER_RELEASE_UNRESOLVED
        if (self.existence_status == EXISTENCE_VALIDATED
                and self.geometry_status in GEOMETRY_SUFFICIENT):
            return RELEASABLE_PARTITION_BARRIER
        return DIAGNOSTIC_PARTITION_BARRIER

    @property
    def release_blocker(self) -> str:
        from engine.space_boundary import (EXISTENCE_VALIDATED,
                                           GEOMETRY_SUFFICIENT)
        if self.status != BARRIER_ACCEPTED:
            return f"the barrier itself is {self.status}"
        if self.existence_status != EXISTENCE_VALIDATED:
            return (f"portal existence is {self.existence_status}: "
                    f"{len(self.existence_evidence)} evidence item(s), and "
                    "no SECOND INDEPENDENT FAMILY confirms the opening is "
                    "real. Four geometric observations of the same gap are "
                    "one family, not four proofs")
        if self.geometry_status not in GEOMETRY_SUFFICIENT:
            return (f"portal geometry is {self.geometry_status}: the jambs "
                    "are not established, so the barrier's own extent is a "
                    "hypothesis")
        return ""

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
                "release_class": self.release_class,
                "release_blocker": self.release_blocker,
                "may_release_a_space": (
                    self.release_class == RELEASABLE_PARTITION_BARRIER),
                "vertices": len(self.ring),
                "why": self.why}


def release_policy(barriers, candidates=(), bounding_of=None) -> dict:
    """Which space geometries rest on a barrier that cannot release.

    A component's boundary may run through several barriers. It is only
    releasable if EVERY barrier it depends on is, because one unproven
    opening is enough to make the whole component the wrong shape.
    """
    accepted = [b for b in barriers if b.status == BARRIER_ACCEPTED]
    by_id = {b.portal_id: b for b in accepted}
    rows = []
    for c in candidates:
        ids = list(bounding_of(c) if bounding_of is not None
                   else getattr(c, "bounding_portal_ids", ()))
        mine = [by_id[i] for i in ids if i in by_id]
        blocking = [b for b in mine
                    if b.release_class != RELEASABLE_PARTITION_BARRIER]
        if not mine:
            # This policy has nothing to say about a component that no
            # barrier bounds. Calling it releasable would turn silence into
            # a clearance — and most of AR-00's components are merged blobs
            # that no barrier touches.
            cls = NOT_CONSTRAINED_BY_A_BARRIER
            why = ("no accepted barrier bounds this component, so the "
                   "barrier release policy does not apply to it. That is "
                   "NOT a clearance: whatever else blocks this geometry "
                   "blocks it still")
        elif blocking:
            cls = DIAGNOSTIC_PARTITION_BARRIER
            why = (f"{len(blocking)} of {len(mine)} barrier(s) rest on "
                   "portal existence that is not validated, so this "
                   "component's shape depends on an opening nobody has "
                   "confirmed")
        else:
            cls = RELEASABLE_PARTITION_BARRIER
            why = ("every barrier this component's boundary runs through "
                   "has validated portal existence")
        rows.append({
            "space_geometry_id": c.space_geometry_id,
            "barriers_depended_on": len(mine),
            "barriers_that_cannot_release": [b.portal_id for b in blocking],
            "release_class": cls,
            "why": why,
        })
    return {
        "policy": ("a PORTAL_PROBABLE may generate a space HYPOTHESIS. It "
                   "may NOT make the resulting space releasable: if the "
                   "portal is not there the space is not there, and a "
                   "released quantity carries no memory of which portal it "
                   "rested on"),
        "accepted_barriers": len(accepted),
        "releasable_barriers": sum(
            1 for b in accepted
            if b.release_class == RELEASABLE_PARTITION_BARRIER),
        "diagnostic_barriers": sum(
            1 for b in accepted
            if b.release_class == DIAGNOSTIC_PARTITION_BARRIER),
        "blockers_by_reason": dict(Counter(
            b.release_blocker for b in accepted if b.release_blocker)),
        "space_geometries": rows,
        "releasable_space_geometries": sum(
            1 for r in rows
            if r["release_class"] == RELEASABLE_PARTITION_BARRIER),
        "space_geometries_no_barrier_bounds": sum(
            1 for r in rows
            if r["release_class"] == NOT_CONSTRAINED_BY_A_BARRIER),
        "space_geometries_blocked_by_a_barrier": sum(
            1 for r in rows
            if r["release_class"] == DIAGNOSTIC_PARTITION_BARRIER),
    }


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
ENVELOPE_FROM_EXTERNAL_WALL_RING = "EXTERNAL_WALL_RING_INNER_EXTENT"
ENVELOPE_FROM_CAD = "CAD_FLOOR_BOUNDARY"
ENVELOPE_FROM_PRINTED = "PRINTED_OVERALL_DIMENSIONS"

ENVELOPE_BASES = (ENVELOPE_FROM_EXTERNAL_WALL_RING, ENVELOPE_FROM_CAD,
                  ENVELOPE_FROM_PRINTED)

# Kept so an older reader does not silently get the new meaning: Round 1's
# envelope filled EVERY wall-solid component's outer ring and unioned them.
ENVELOPE_FROM_WALL_SOLID_HULL = "OUTER_BOUNDARY_OF_THE_WALL_SOLID_SUPERSEDED"

# A component qualifies as an external wall ring only if filling its outer
# ring creates INTERIOR that its own material does not occupy. A solid
# rectangle of wall has hull == material, so its ratio is exactly 1.0; any
# genuine ring is above it.
#
# The threshold is deliberately just above 1.0 rather than "large", because
# the ratio is SIZE-DEPENDENT and a large threshold would reject small
# buildings: AR-00's external ring scores 38.7, a 4 x 3 m room's scores 4.8,
# and a 1 x 1 m closet's scores 1.5. Excluding a small building for being
# small would be a bug, not a safeguard.
MIN_RING_ENCLOSURE_RATIO = 1.2


@dataclass(frozen=True)
class BuildingEnvelope:
    """The floor's outer extent, with the basis it was established on.

    ROUND 1 GOT THIS WRONG, and the audit found it. It filled the outer ring
    of every wall-solid component and unioned the lot. On AR-00 that produced
    1002.290 m2 — but only 18 of the 46 filled hulls lie inside the external
    ring at all, so the other 28 contributed 2.19 m2 of envelope that is not
    floor. Filling a disconnected INTERNAL partition's hull and calling it
    footprint is exactly what a floor envelope must not be built from.

    The envelope now comes from the EXTERNAL WALL RING and nothing else: the
    component whose own outer ring encloses far more area than its material,
    which is what a ring of external wall looks like. Components whose hulls
    fall outside it are reported as unresolved exterior geometry, not absorbed.

    A bounding rectangle and a convex hull are both refused. BBOX IS NEVER
    PHYSICAL GEOMETRY, and a hull would bridge every re-entrant corner of the
    footprint.
    """

    geometry: object = None
    basis: str = ENVELOPE_UNRESOLVED
    evidence: tuple[str, ...] = ()
    external_band_ids: tuple[str, ...] = ()
    external_portal_ids: tuple[str, ...] = ()
    unresolved_exterior: tuple = ()
    ring_component_material_m2: float | None = None
    enclosure_ratio: float | None = None
    caveat: str = ""
    why: str = ""

    validation_status: str = ""

    @property
    def is_resolved(self) -> bool:
        return self.geometry is not None and self.basis in ENVELOPE_BASES

    @property
    def status(self) -> str:
        """What may be claimed about this envelope.

        An envelope built from the external ring with nothing left over is a
        different object from one built beside unexplained exterior geometry,
        and an area quoted from the second should carry that with it.
        """
        if self.validation_status:
            return self.validation_status
        if not self.is_resolved:
            return "ENVELOPE_UNRESOLVED"
        if self.unresolved_exterior:
            return "ENVELOPE_GEOMETRY_ACCEPTED_WITH_UNRESOLVED_EXTERIOR"
        return "ENVELOPE_GEOMETRY_ACCEPTED"

    @property
    def area_m2(self) -> float:
        return 0.0 if self.geometry is None else self.geometry.area / 1e6

    @property
    def perimeter_m(self) -> float:
        return 0.0 if self.geometry is None else self.geometry.length / 1000

    def record(self) -> dict:
        return {"basis": self.basis, "is_resolved": self.is_resolved,
                "validation_status": self.status,
                "area_m2": round(self.area_m2, 3),
                "perimeter_m": round(self.perimeter_m, 3),
                "evidence": list(self.evidence),
                "external_wall_band_ids": len(self.external_band_ids),
                "external_wall_band_sample": list(self.external_band_ids[:12]),
                "external_portal_closures": list(self.external_portal_ids),
                "unresolved_exterior": list(self.unresolved_exterior),
                "ring_component_material_m2": (
                    None if self.ring_component_material_m2 is None
                    else round(self.ring_component_material_m2, 3)),
                "enclosure_ratio": (None if self.enclosure_ratio is None
                                    else round(self.enclosure_ratio, 1)),
                "bbox_used": False, "convex_hull_used": False,
                "internal_components_filled": False,
                "caveat": self.caveat, "why": self.why}


# The envelope must not move by more than this when internal barriers are
# removed. ABSOLUTE: a percentage on a 1000 m2 floor would wave through a
# square metre of footprint invented by an internal doorway.
ENVELOPE_SENSITIVITY_TOLERANCE_MM2 = 10_000.0

# How close a barrier must lie to the envelope's boundary to count as
# closing an EXTERNAL opening rather than an internal one.
ENVELOPE_BOUNDARY_REACH_MM = 1.0

ENVELOPE_SENSITIVITY_PASS = "INTERNAL_BARRIERS_DO_NOT_MOVE_THE_FOOTPRINT"
ENVELOPE_SENSITIVITY_FAIL = "INTERNAL_BARRIERS_ALTER_THE_FOOTPRINT"
ENVELOPE_SENSITIVITY_NA = "NO_INTERNAL_BARRIERS_TO_TEST"


def envelope_barrier_sensitivity(solid, barriers, wall_polys) -> dict:
    """Does an INTERNAL doorway change the floor's outer extent?

    It must not. A portal barrier exists to stop free space leaking between
    two rooms; a barrier inside the building cannot add or remove floor. If
    removing the internal barriers moves the envelope, then the envelope is
    being derived from internal geometry somewhere, and every area computed
    against it is wrong by an amount nobody can see.

    So the envelope is rebuilt three ways and the areas compared:

      ALL       every accepted barrier, as the run uses it
      EXTERNAL  only barriers hosted on the external wall ring
      NONE      no barriers at all

    ALL vs EXTERNAL is the test, and it is a hard one. NONE is reported for
    context and is EXPECTED to differ: a ring of external wall with a
    doorway in it is not closed, so its own outer ring is a C-shape. That
    difference is the barriers doing their job on the envelope's boundary,
    which is a different thing from internal geometry moving it.
    """
    from shapely.geometry import Polygon

    all_env = envelope_from_wall_solid(solid, barriers, wall_polys)
    accepted = [b for b in barriers
                if b.status == BARRIER_ACCEPTED and b.ring]

    # A barrier is EXTERNAL if it sits ON the envelope's boundary — that is
    # what closing a doorway in the external wall looks like. Membership of
    # the ring COMPONENT is not the test: on AR-00 that component carries 197
    # of the bands, because every internal wall touching the external ring
    # belongs to the same connected solid, and classifying by it made the
    # test vacuous by finding no internal barriers at all.
    ext, internal = [], []
    boundary = (None if all_env.geometry is None
                else all_env.geometry.boundary)
    for b in accepted:
        poly = Polygon(list(b.ring))
        on_boundary = (boundary is not None
                       and poly.distance(boundary)
                       <= ENVELOPE_BOUNDARY_REACH_MM)
        (ext if on_boundary else internal).append(b)

    ext_env = envelope_from_wall_solid(solid, ext, wall_polys)
    none_env = envelope_from_wall_solid(solid, (), wall_polys)

    a_all = all_env.geometry.area if all_env.geometry is not None else 0.0
    a_ext = ext_env.geometry.area if ext_env.geometry is not None else 0.0
    a_none = none_env.geometry.area if none_env.geometry is not None else 0.0
    delta = a_all - a_ext

    if not internal:
        status = ENVELOPE_SENSITIVITY_NA
    elif abs(delta) <= ENVELOPE_SENSITIVITY_TOLERANCE_MM2:
        status = ENVELOPE_SENSITIVITY_PASS
    else:
        status = ENVELOPE_SENSITIVITY_FAIL

    return {
        "status": status,
        "accepted_barriers": len(accepted),
        "external_barriers": len(ext),
        "internal_barriers": len(internal),
        "internal_barrier_portal_ids": [b.portal_id for b in internal][:20],
        "external_barrier_portal_ids": [b.portal_id for b in ext][:20],
        "how_external_was_decided": (
            "a barrier lying within "
            f"{ENVELOPE_BOUNDARY_REACH_MM} mm of the envelope's own boundary "
            "closes an external opening. Membership of the wall solid's ring "
            "COMPONENT is not the test: that component carries almost every "
            "band, because internal walls touching the external ring are "
            "part of the same connected solid"),
        "envelope_with_all_barriers_m2": round(a_all / 1e6, 4),
        "envelope_with_external_barriers_only_m2": round(a_ext / 1e6, 4),
        "envelope_with_no_barriers_m2": round(a_none / 1e6, 4),
        "delta_from_internal_barriers_m2": round(delta / 1e6, 6),
        "delta_from_internal_barriers_mm2": round(delta, 1),
        "tolerance_mm2": ENVELOPE_SENSITIVITY_TOLERANCE_MM2,
        "basis_with_all_barriers": all_env.basis,
        "basis_with_external_only": ext_env.basis,
        "basis_with_no_barriers": none_env.basis,
        "the_test": ("ALL vs EXTERNAL must agree to within an absolute "
                     "tolerance. NONE is context and is expected to differ, "
                     "because an external ring with an unclosed doorway is a "
                     "C-shape rather than a ring"),
        "why_it_matters": (
            "a barrier inside the building cannot add or remove floor. If "
            "removing the internal ones moves the envelope, the envelope is "
            "being derived from internal geometry and every area measured "
            "against it is wrong by an amount nobody can see"),
    }


def envelope_from_wall_solid(solid, barriers=(), wall_polys=()
                             ) -> BuildingEnvelope:
    """The external wall ring's own interior. One component, named.

    `barriers` are accepted only where an EXTERNAL stretch needs closing;
    internal portal barriers must not move the footprint, and a sensitivity
    test in the pipeline checks that they do not.
    """
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    if solid.geometry is None or solid.geometry.is_empty:
        return BuildingEnvelope(
            basis=ENVELOPE_UNRESOLVED,
            why=("no wall solid, so no envelope. Space extraction must say "
                 "so: a bounding rectangle is NOT an acceptable substitute"))
    # Ring detection runs on the CLOSED obstacle set — wall solid plus the
    # accepted barriers — because that is the geometry free space is computed
    # against, and because a ring of wall with a doorway in it is not closed:
    # its union is a C-shape whose hull is the C itself. Internal barriers sit
    # inside the ring and cannot move its hull, which is what the pipeline's
    # sensitivity test verifies rather than assumes.
    grid = getattr(solid, "snap_grid_mm", 0.0)
    accepted = [_on_grid(Polygon(list(b.ring)), grid) for b in barriers
                if b.status == BARRIER_ACCEPTED and b.ring]
    closed = unary_union([solid.geometry] + accepted)
    geoms = (list(closed.geoms) if closed.geom_type == "MultiPolygon"
             else [closed])

    # EVERY component that qualifies as a ring is kept — a sheet legitimately
    # holds more than one structure. What is NOT kept is a component that is
    # merely large: Round 1 filled all 46 and added 2.19 m2 of non-floor.
    rings, rejected = [], []
    for g in sorted(geoms, key=lambda g: -Polygon(g.exterior).area):
        hull = Polygon(g.exterior)
        ratio = (hull.area / g.area) if g.area else 0.0
        interior = hull.difference(g)
        if ratio >= MIN_RING_ENCLOSURE_RATIO and \
                interior.area / 1e6 >= MIN_ROOM_AREA_M2:
            rings.append((hull, g, ratio))
        else:
            rejected.append((hull, g, ratio))
    if not rings:
        big = max(geoms, key=lambda g: Polygon(g.exterior).area)
        hull = Polygon(big.exterior)
        ratio = (hull.area / big.area) if big.area else 0.0
        return BuildingEnvelope(
            basis=ENVELOPE_UNRESOLVED, enclosure_ratio=ratio,
            why=(f"no wall-solid component is a ring: the largest encloses "
                 f"{ratio:.2f}x its own material and leaves "
                 f"{hull.difference(big).area / 1e6:.3f} m2 of interior. It "
                 "is a solid body of geometry, not a boundary. Neither a "
                 "bounding box nor a convex hull may stand in for one"))

    ring_union = unary_union([h for h, _, _ in rings])
    # Anything whose hull falls outside every ring is unresolved exterior
    # geometry: a terrace, an adjacent structure, or extraction noise.
    outside = []
    for hull, g, ratio in rejected:
        if ring_union.buffer(1.0).contains(hull):
            continue
        outside.append({
            "material_m2": round(g.area / 1e6, 3),
            "hull_m2": round(hull.area / 1e6, 3),
            "enclosure_ratio": round(ratio, 2),
            "centroid_mm": [round(v, 1) for v in (g.centroid.x, g.centroid.y)],
            "why": ("this wall geometry lies outside every external ring: a "
                    "terrace, an adjacent structure, or extraction noise. It "
                    "is NOT filled into the floor envelope")})

    material = sum(g.area for _, g, _ in rings) / 1e6
    ratio = max(r for _, _, r in rings)
    band_ids = tuple(sorted(
        wp.wall_band_id for wp in wall_polys
        if wp.is_resolved
        and any(g.intersects(Polygon(list(wp.ring))) for _, g, _ in rings)))
    # An accepted barrier that touches a ring's own boundary is closing an
    # EXTERNAL stretch; one wholly inside is internal and changes nothing.
    ext_portals = tuple(
        b.portal_id for b in barriers
        if b.status == BARRIER_ACCEPTED and b.ring
        and ring_union.exterior.distance(
            Polygon(list(b.ring))) < 1.0
        if ring_union.geom_type == "Polygon")
    geometry = ring_union

    return BuildingEnvelope(
        geometry=geometry, basis=ENVELOPE_FROM_EXTERNAL_WALL_RING,
        evidence=(f"{len(rings)} ring component(s) holding "
                  f"{material:.3f} m2 of material and enclosing "
                  f"{geometry.area / 1e6:.3f} m2 — a best enclosure ratio of "
                  f"{ratio:.1f}, which is what a ring of external wall looks "
                  "like. {n} component(s) outside were NOT filled".format(
                      n=len(outside)),),
        external_band_ids=band_ids, external_portal_ids=ext_portals,
        unresolved_exterior=tuple(outside),
        ring_component_material_m2=material, enclosure_ratio=ratio,
        caveat=("the OUTER face of the external wall ring bounds this, so the "
                "envelope includes the external wall's own thickness. Free "
                "space is measured after that wall is subtracted, so a room "
                "is unaffected — but the envelope area is not a floor area"),
        why=("derived from ONE named component, not from filling every "
             "disconnected partition. An independent envelope from CAD or "
             "from printed overall dimensions would replace it and is "
             "preferred"))


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

    grid = getattr(solid, "snap_grid_mm", 0.0)
    accepted = [_on_grid(Polygon(list(b.ring)), grid) for b in barriers
                if b.status == BARRIER_ACCEPTED and b.ring]
    parts = ([solid.geometry] if solid.geometry is not None else []) + accepted
    obstacles = unary_union(parts) if parts else None
    free = (envelope.geometry.difference(obstacles) if obstacles is not None
            else envelope.geometry)

    geoms = (list(free.geoms) if free.geom_type == "MultiPolygon"
             else ([free] if not free.is_empty else []))
    by_band = {wp.wall_band_id: Polygon(list(wp.ring))
               for wp in wall_polys if wp.is_resolved}
    by_portal = {b.portal_id: _on_grid(Polygon(list(b.ring)), grid)
                 for b in barriers
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
