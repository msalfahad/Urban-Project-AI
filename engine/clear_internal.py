"""E55 — the clear-internal room polygon, built from the wall faces themselves.

The previous round converted a centreline area to a clear-internal one like
this:

    CLEAR_AREA  ~=  CENTRELINE_AREA - PERIMETER x MEAN_HALF_THICKNESS

which is close on a single rectangle of uniform thickness and wrong everywhere
else. It has no corner terms, and the corners are real geometry: an inside
corner and an outside corner contribute with OPPOSITE sign, so on an L-shaped
room the formula loses the wrong amount. Mixed 100 / 150 / 200 mm walls break
it again, because there is no single thickness to take half of. Holes, shafts,
T-junctions and bands with unequal face extents break it further.

So it is retired as a measurement basis and kept only as
DIAGNOSTIC_APPROXIMATION, for comparison against this engine's answer.

WHAT THIS DOES INSTEAD. We already hold everything needed to draw the real
boundary: each wall band's two drawn faces, the separation between them, the
portal jambs and the closure lines. For a candidate room the polygon walks

    room-facing wall face
      -> portal closure on the SAME basis
        -> next room-facing wall face
          -> ...

and the corners come from INTERSECTING consecutive offset lines, which is what
makes inside and outside corners both come out right without a special case
for either.

    NO SCALAR CONVERSION. The area is measured from the polygon.

Two rules the walk will not break:

    THE ROOM-FACING FACE IS CHOSEN ON EVIDENCE, never by being nearer. The
    test is which side of the wall the room is actually on, answered by
    point-in-polygon against the face the graph already produced.

    A PORTAL CLOSES ON THE SAME BASIS AS THE WALLS IT JOINS. Closing a
    finish-face polygon to a centreline endpoint would put a step the width of
    half a wall into the boundary at every door.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from engine.space_boundary import PHYSICAL_WALL

# Which geometry a polygon is measured on. They are different objects, kept
# side by side, and nothing converts silently between them.
WALL_CENTRELINE_FACE = "WALL_CENTRELINE_FACE"
CLEAR_INTERNAL_FINISH_FACE = "CLEAR_INTERNAL_FINISH_FACE"
# Named now so a later basis cannot quietly reuse one of the above.
STRUCTURAL_FACE = "STRUCTURAL_FACE"
SITE_MEASURED_FACE = "SITE_MEASURED_FACE"

GEOMETRY_BASES = (WALL_CENTRELINE_FACE, CLEAR_INTERNAL_FINISH_FACE,
                  STRUCTURAL_FACE, SITE_MEASURED_FACE)

# How sure we are which face of a wall belongs to this room.
OWNERSHIP_VALIDATED = "OWNERSHIP_VALIDATED"
OWNERSHIP_PROBABLE = "OWNERSHIP_PROBABLE"
OWNERSHIP_AMBIGUOUS = "OWNERSHIP_AMBIGUOUS"
OWNERSHIP_UNRESOLVED = "OWNERSHIP_UNRESOLVED"

OWNERSHIP_STATES = (OWNERSHIP_UNRESOLVED, OWNERSHIP_AMBIGUOUS,
                    OWNERSHIP_PROBABLE, OWNERSHIP_VALIDATED)

FACE_A = "FACE_A"
FACE_B = "FACE_B"

# Two consecutive edges whose offset lines are parallel cannot be intersected.
# When their offsets differ the boundary really does step, and the step is
# inserted rather than averaged away.
PARALLEL_EPS = 1e-6
# A step smaller than this is a rounding artefact of two faces on one line.
MIN_STEP_MM = 1.0


class ClearInternalError(RuntimeError):
    """A clear-internal boundary could not be built without inventing it."""


@dataclass(frozen=True)
class WallSideOwnership:
    """Which face of one wall band belongs to this room, and on what evidence.

    `room_facing_face_id` names a DRAWN OBJECT. That is the point: the room's
    boundary runs along a line the architect drew, not along an offset this
    engine computed.
    """

    space_face_id: str
    wall_band_id: str
    room_facing_side: str
    room_facing_face_id: str
    opposite_face_id: str
    room_facing_mm: float | None
    opposite_mm: float | None
    measurement_basis: str = CLEAR_INTERNAL_FINISH_FACE
    ownership_status: str = OWNERSHIP_UNRESOLVED
    why: str = ""

    def record(self) -> dict:
        return {"space_face_id": self.space_face_id,
                "wall_band_id": self.wall_band_id,
                "space_face_side": self.room_facing_side,
                "room_facing_face_id": self.room_facing_face_id,
                "opposite_face_id": self.opposite_face_id,
                "room_facing_mm": (None if self.room_facing_mm is None
                                   else round(self.room_facing_mm, 1)),
                "opposite_mm": (None if self.opposite_mm is None
                                else round(self.opposite_mm, 1)),
                "measurement_basis": self.measurement_basis,
                "ownership_status": self.ownership_status,
                "why": self.why}


@dataclass(frozen=True)
class ClearInternalPolygon:
    """One room boundary on the clear-internal finish face.

    It carries its own area and perimeter, measured from the polygon. There is
    no adjustment term anywhere in this type, because there is no conversion:
    the boundary was built on this basis from the start.
    """

    space_face_id: str
    geometry_basis: str
    polygon_mm: tuple
    ownership: tuple = ()
    portal_closures: tuple = ()
    steps_inserted: int = 0
    unresolved_edges: tuple = ()
    blockers: tuple = ()
    provenance: dict = field(default_factory=dict)

    @property
    def area_m2(self) -> float:
        return abs(_signed_area(list(self.polygon_mm))) / 1_000_000

    @property
    def perimeter_m(self) -> float:
        pts = list(self.polygon_mm)
        return sum(math.dist(a, b)
                   for a, b in zip(pts, pts[1:] + pts[:1])) / 1000

    @property
    def is_complete(self) -> bool:
        """Every boundary edge resolved to a room-facing face."""
        return not self.unresolved_edges and len(self.polygon_mm) >= 3

    def record(self) -> dict:
        return {"space_face_id": self.space_face_id,
                "geometry_basis": self.geometry_basis,
                "vertices": len(self.polygon_mm),
                "clear_internal_area_m2": round(self.area_m2, 3),
                "clear_internal_perimeter_m": round(self.perimeter_m, 3),
                "ownership": [o.record() for o in self.ownership],
                "portal_closures": list(self.portal_closures),
                "steps_inserted": self.steps_inserted,
                "unresolved_edges": list(self.unresolved_edges),
                "is_complete": self.is_complete,
                "blockers": list(self.blockers),
                "provenance": dict(self.provenance)}


def _signed_area(poly) -> float:
    s = 0.0
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        s += x0 * y1 - x1 * y0
    return s / 2.0


def _point_in(poly, x: float, y: float) -> bool:
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y):
            xt = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < xt:
                inside = not inside
    return inside


def _inward_sign(poly, axis: str, fixed: float, lo: float, hi: float) -> int:
    """Which way is INTO the room from this wall line: -1, +1, or 0 if unclear.

    Answered by stepping a short distance each way from the edge's midpoint
    and testing containment in the polygon the graph produced. Evidence, not
    "the nearer face" — and when both or neither side is inside, it says 0
    rather than picking one.
    """
    mid = (lo + hi) / 2
    step = max(1.0, min(50.0, abs(hi - lo) / 4))
    probes = {}
    for sign in (-1, 1):
        if axis == "H":
            pt = (mid, fixed + sign * step)
        else:
            pt = (fixed + sign * step, mid)
        probes[sign] = _point_in(list(poly), pt[0], pt[1])
    if probes[-1] and not probes[1]:
        return -1
    if probes[1] and not probes[-1]:
        return 1
    return 0


def own_wall_side(space_face_id: str, edge, poly) -> WallSideOwnership:
    """Which drawn face of this band the room is on.

    A single-face band has no second face to choose between, so ownership is
    AMBIGUOUS rather than validated: we know the line, not which side of the
    wall it bounds.
    """
    a_id = edge.face_a_ids[0] if edge.face_a_ids else ""
    b_id = edge.face_b_ids[0] if edge.face_b_ids else ""
    if edge.face_a_mm is None or edge.face_b_mm is None:
        return WallSideOwnership(
            space_face_id, edge.edge_id, FACE_A, a_id, b_id,
            edge.face_a_mm, edge.face_b_mm,
            ownership_status=OWNERSHIP_AMBIGUOUS,
            why=("this band has only one drawn face. NEVER INVENT THE MISSING "
                 "HALF: the line is known, which side of a wall it bounds is "
                 "not"))
    sign = _inward_sign(poly, edge.axis, edge.centreline_mm,
                        edge.start_mm, edge.end_mm)
    if sign == 0:
        return WallSideOwnership(
            space_face_id, edge.edge_id, FACE_A, a_id, b_id,
            edge.face_a_mm, edge.face_b_mm,
            ownership_status=OWNERSHIP_UNRESOLVED,
            why=("neither side of this wall tests as inside the face, or both "
                 "do. The room-facing face is not chosen by being nearer"))
    # The room-facing face is the one on the inward side of the centreline.
    a_inward = (edge.face_a_mm - edge.centreline_mm) * sign > 0
    side = FACE_A if a_inward else FACE_B
    facing, other = ((a_id, b_id) if a_inward else (b_id, a_id))
    facing_mm, other_mm = ((edge.face_a_mm, edge.face_b_mm) if a_inward
                           else (edge.face_b_mm, edge.face_a_mm))
    return WallSideOwnership(
        space_face_id, edge.edge_id, side, facing, other, facing_mm, other_mm,
        ownership_status=OWNERSHIP_VALIDATED,
        why=(f"the room lies on the {'negative' if sign < 0 else 'positive'} "
             f"side of this wall line, so {side} is the room-facing face"))


@dataclass(frozen=True)
class _Seg:
    """One boundary edge as an offset supporting line, in walk order."""

    edge_id: str
    axis: str
    line_mm: float          # the room-facing line's constant coordinate
    a: tuple
    b: tuple
    boundary_type: str
    portal_id: str = ""


def _offset_line(edge, sign: int) -> float:
    """The room-facing line for a physical wall: its own drawn face."""
    half = abs((edge.face_b_mm or 0.0) - (edge.face_a_mm or 0.0)) / 2
    return edge.centreline_mm + sign * half


def build(space_face_id: str, face, index, *, host_offsets=None
          ) -> ClearInternalPolygon:
    """The clear-internal polygon for one candidate face.

    `face` is the CENTRELINE face the planar walker produced. `index` maps
    boundary edge id -> SpaceBoundaryEdge. `host_offsets` optionally supplies,
    per portal edge id, the host band id whose face basis the closure must
    follow — §7: a door closes on the same basis as the walls it joins.
    """
    poly = list(face.polygon_mm)
    if len(poly) < 3:
        raise ClearInternalError(
            f"{space_face_id} has fewer than three vertices: there is no "
            "boundary to offset")
    host_offsets = dict(host_offsets or {})

    # Walk order: half-edge i runs from poly[i] to poly[i+1].
    segs: list[_Seg] = []
    ownership: list[WallSideOwnership] = []
    unresolved: list[dict] = []
    closures: list[dict] = []
    edge_for = _edges_in_walk_order(face, index)
    for i, edge in enumerate(edge_for):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        if edge is None:
            unresolved.append({
                "vertex_index": i,
                "why": ("this boundary segment has no space-boundary edge "
                        "behind it, so no room-facing face can be named")})
            continue
        if edge.boundary_type == PHYSICAL_WALL:
            own = own_wall_side(space_face_id, edge, poly)
            ownership.append(own)
            if own.ownership_status != OWNERSHIP_VALIDATED:
                unresolved.append({
                    "edge_id": edge.edge_id,
                    "ownership_status": own.ownership_status,
                    "why": own.why})
                continue
            segs.append(_Seg(edge.edge_id, edge.axis, own.room_facing_mm,
                             a, b, edge.boundary_type))
        else:
            # §7 — the closure follows the HOST wall's room-facing face, so
            # the boundary does not step by half a wall at every doorway.
            host_id = host_offsets.get(edge.edge_id) or edge.host_wall_band_id
            host = index.get(host_id)
            if host is None or host.face_a_mm is None or host.face_b_mm is None:
                unresolved.append({
                    "edge_id": edge.edge_id, "portal_id": edge.portal_id,
                    "why": ("this portal names no host band with two drawn "
                            "faces, so its closure has no basis to follow. "
                            "A finish-face polygon must not close to a "
                            "centreline endpoint")})
                continue
            sign = _inward_sign(poly, host.axis, host.centreline_mm,
                                host.start_mm, host.end_mm)
            if sign == 0:
                unresolved.append({
                    "edge_id": edge.edge_id, "portal_id": edge.portal_id,
                    "why": "the host wall's room-facing side is unresolved"})
                continue
            line = _offset_line(host, sign)
            segs.append(_Seg(edge.edge_id, edge.axis, line, a, b,
                             edge.boundary_type, edge.portal_id))
            closures.append({
                "portal_id": edge.portal_id, "edge_id": edge.edge_id,
                "host_wall_band_id": host_id,
                "closure_basis": CLEAR_INTERNAL_FINISH_FACE,
                "closure_line_mm": round(line, 1),
                "jamb_a_mm": round(min(edge.start_mm, edge.end_mm), 1),
                "jamb_b_mm": round(max(edge.start_mm, edge.end_mm), 1),
                "why": ("closed between the two clear-finish jamb points on "
                        "the host wall's room-facing face")})

    blockers = []
    if unresolved:
        blockers.append(
            f"{len(unresolved)} of {len(edge_for)} boundary segments could "
            "not be resolved to a room-facing face, so this polygon is NOT "
            "the clear-internal boundary of the whole room")
    pts, steps = _corners(segs)
    return ClearInternalPolygon(
        space_face_id=space_face_id,
        geometry_basis=CLEAR_INTERNAL_FINISH_FACE,
        polygon_mm=tuple(pts), ownership=tuple(ownership),
        portal_closures=tuple(closures), steps_inserted=steps,
        unresolved_edges=tuple(unresolved), blockers=tuple(blockers),
        provenance={"built_from": "wall band faces + portal closures",
                    "centreline_face_id": face.space_face_id,
                    "scalar_conversion_used": False,
                    "raster_used": False})


def _edges_in_walk_order(face, index) -> list:
    """The space-boundary edge behind each boundary segment, in walk order.

    Joined through the half-edge's source edge and that split edge's parent
    pair id. IDENTITY BY ID, never by position in a sorted list.
    """
    out = []
    order = getattr(face, "boundary_edges_in_order", None)
    if order:
        return [index.get(e) for e in order]
    for eid in getattr(face, "boundary_edge_ids", ()):
        out.append(index.get(eid))
    return out


def _corners(segs) -> tuple[list, int]:
    """Intersect consecutive offset lines. The corners ARE the geometry.

    Perpendicular neighbours give one intersection, which is correct for an
    inside corner and an outside corner alike — the sign works itself out, and
    that is exactly what the scalar formula could not do. Parallel neighbours
    on different lines are a genuine step in the boundary, so a step is
    inserted; parallel on the same line is one continuous run.
    """
    if len(segs) < 3:
        return [], 0
    pts: list[tuple] = []
    steps = 0
    n = len(segs)
    for i, cur in enumerate(segs):
        nxt = segs[(i + 1) % n]
        if cur.axis != nxt.axis:
            pts.append(_meet(cur, nxt))
            continue
        if abs(cur.line_mm - nxt.line_mm) < MIN_STEP_MM:
            continue                      # one continuous run
        # A real step: leave the current line at the shared end, then arrive
        # on the next one. Both points are on drawn faces.
        shared = _shared_coord(cur, nxt)
        if cur.axis == "H":
            pts.append((shared, cur.line_mm))
            pts.append((shared, nxt.line_mm))
        else:
            pts.append((cur.line_mm, shared))
            pts.append((nxt.line_mm, shared))
        steps += 1
    return pts, steps


def _meet(cur: _Seg, nxt: _Seg) -> tuple:
    """Where two perpendicular offset lines cross."""
    if cur.axis == "H":
        return (nxt.line_mm, cur.line_mm)
    return (cur.line_mm, nxt.line_mm)


def _shared_coord(cur: _Seg, nxt: _Seg) -> float:
    """The along-axis coordinate the two collinear runs meet at."""
    if cur.axis == "H":
        ends = (cur.a[0], cur.b[0])
        nexts = (nxt.a[0], nxt.b[0])
    else:
        ends = (cur.a[1], cur.b[1])
        nexts = (nxt.a[1], nxt.b[1])
    best, bd = ends[1], 1e18
    for e in ends:
        for f in nexts:
            d = abs(e - f)
            if d < bd:
                best, bd = (e + f) / 2, d
    return best


def summary(polys) -> dict:
    """What the clear-internal engine produced, and what it refused to."""
    done = [p for p in polys if p.is_complete]
    return {
        "candidates": len(polys),
        "complete_clear_internal_polygons": len(done),
        "incomplete": len(polys) - len(done),
        "total_unresolved_edges": sum(len(p.unresolved_edges) for p in polys),
        "ownership_by_status": dict(Counter(
            o.ownership_status for p in polys for o in p.ownership)),
        "portal_closures_on_clear_face": sum(
            len(p.portal_closures) for p in polys),
        "steps_inserted": sum(p.steps_inserted for p in polys),
        "geometry_basis": CLEAR_INTERNAL_FINISH_FACE,
        "note": ("areas here are measured FROM THE POLYGON. No scalar "
                 "centreline-to-clear conversion is used, and the corner "
                 "terms the old formula was missing are just intersections"),
    }
