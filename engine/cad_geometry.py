"""E1 — CAD entities own exact design geometry. Nothing else does.

The boundary machinery this project grew before E1 could not hold a
curve. `boundary_match.VectorCandidate` carries an axis and a fixed
coordinate; `space_enclosure` floods an axis-aligned grid and emits
axis-aligned edges. The adapter reads this drawing's 345 arcs and 106
circles faithfully and then they are dropped, so every room polygon the
project produced was rectilinear BY CONSTRUCTION. A curved wall came out
as a rectangle and nothing in the record said so.

So this module carries geometry the way the drawing does:

    LINE             two points
    ARC              centre, radius, start and end angle, direction
    CIRCLE           centre, radius
    COMPOSITE_CURVE  an ordered run of the above, closed or not

An arc stays an arc all the way into the register. Where topology needs a
polygon — to decide which face a seed point falls in — the arcs are
densified at a DECLARED tolerance, and that densified form is used for
THAT QUESTION ONLY. It never becomes the stored boundary, and the
tolerance is recorded beside every region so a reviewer can see what was
approximated and by how much.

Three rules the register enforces rather than states:

    A BOUNDING BOX IS NOT MEASUREMENT GEOMETRY. It is stored for indexing
    and refuses to be read as a boundary.

    A LINE IS NOT A WALL UNTIL ITS LAYER SAYS SO. Furniture, cabinetry,
    counters, dimension lines, leaders, hatch and annotation are recorded
    where they bound the ink, and never counted as a physical face.

    EVERY SEGMENT NAMES ITS ENTITY. A boundary that cannot be traced back
    to a DWG handle is not CAD-derived, whatever it looks like.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field

MODEL = "CAD_ENTITIES_OWN_EXACT_DESIGN_GEOMETRY_V1"

# --- how a boundary piece may be shaped ---------------------------------
LINE = "LINE"
ARC = "ARC"
CIRCLE = "CIRCLE"
POLYLINE = "POLYLINE"
COMPOSITE_CURVE = "COMPOSITE_CURVE"
KINDS = (LINE, ARC, CIRCLE, POLYLINE, COMPOSITE_CURVE)

# --- what a boundary piece is doing -------------------------------------
ROLE_WALL_FACE = "PHYSICAL_WALL_FACE"
ROLE_OPEN_EDGE = "OPEN_EDGE_NO_DRAWN_BARRIER"
ROLE_OPENING = "OPENING_IN_A_HOST_WALL"
ROLE_COLUMN = "COLUMN_FACE"
ROLE_SHAFT = "SHAFT_FACE"
ROLE_UNRESOLVED = "LINEWORK_ROLE_UNRESOLVED"
ROLE_NOT_A_WALL = "NOT_A_WALL_ANNOTATION_OR_FITTING"
ROLES = (ROLE_WALL_FACE, ROLE_OPEN_EDGE, ROLE_OPENING, ROLE_COLUMN,
         ROLE_SHAFT, ROLE_UNRESOLVED, ROLE_NOT_A_WALL)

# --- topology ------------------------------------------------------------
TOPOLOGY_CLOSED = "BOUNDARY_CLOSED_BY_DRAWN_GEOMETRY"
TOPOLOGY_CLOSED_WITH_OPEN_EDGES = "CLOSED_ONLY_ACROSS_AN_OPEN_EDGE"
TOPOLOGY_NOT_CLOSED = "BOUNDARY_NOT_CLOSED_BY_DRAWN_GEOMETRY"
TOPOLOGY_NO_SEED = "NO_INTERIOR_POINT_TO_TRACE_FROM"
TOPOLOGY_ESCAPED = "TRACE_ESCAPED_THE_NEIGHBOURHOOD"
TOPOLOGY_STATES = (TOPOLOGY_CLOSED, TOPOLOGY_CLOSED_WITH_OPEN_EDGES,
                   TOPOLOGY_NOT_CLOSED, TOPOLOGY_NO_SEED, TOPOLOGY_ESCAPED)

# --- geometry ------------------------------------------------------------
GEOMETRY_EXACT = "EXACT_FROM_CAD_ENTITIES"
GEOMETRY_PARTIAL = "PARTIALLY_FROM_CAD_ENTITIES"
GEOMETRY_NOT_ESTABLISHED = "NOT_ESTABLISHED_FROM_CAD"
GEOMETRY_STATES = (GEOMETRY_EXACT, GEOMETRY_PARTIAL,
                   GEOMETRY_NOT_ESTABLISHED)

# --- clear-face basis ----------------------------------------------------
BASIS_DRAWN_FACE = "THE_DRAWN_FACE_THE_TRACE_STOPPED_ON"
BASIS_NOT_ESTABLISHED = "CLEAR_FACE_NOT_ESTABLISHED"

# --- the declared approximation -----------------------------------------
# Used to answer "which face is this point in", never to store a boundary.
DENSIFY_TOL_MM = 1.0
SNAP_MM = 0.5
OWNER_TOL_MM = 2.0

A_BOUNDING_BOX_IS_NOT_MEASUREMENT_GEOMETRY = (
    "a bounding box is stored for indexing and nothing else. The largest "
    "enclosing rectangle of a stepped or curved room is not that room, and "
    "reading one as a boundary is the error this field exists to prevent")

A_LINE_IS_NOT_A_WALL_UNTIL_ITS_LAYER_SAYS_SO = (
    "furniture, cabinetry, counters, dimension lines, leaders, hatch and "
    "annotation all bound ink. They are recorded where they do, and never "
    "counted as a physical face without layer or entity evidence")

WHY_A_CURVE_STAYS_A_CURVE = (
    "an arc is stored as centre, radius and angles - the parameters the "
    "author drew. Densification happens only to decide which face a point "
    "falls in, at a declared tolerance, and never becomes the boundary")


class CadGeometryError(RuntimeError):
    """Something asked this module to store geometry it cannot vouch for."""


def model_hash() -> str:
    parts = ([MODEL] + list(KINDS) + list(ROLES) + list(TOPOLOGY_STATES)
             + list(GEOMETRY_STATES)
             + [f"{DENSIFY_TOL_MM}", f"{SNAP_MM}", f"{OWNER_TOL_MM}"])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# --------------------------------------------------------------- segments

@dataclass(frozen=True)
class BoundarySegment:
    """One piece of a boundary, shaped as the drawing shaped it."""

    kind: str
    object_id: str = ""
    dwg_handle: int | None = None
    layer: str = ""
    entity_type: str = ""
    role: str = ROLE_UNRESOLVED
    # LINE
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    # ARC / CIRCLE
    cx: float = 0.0
    cy: float = 0.0
    radius: float = 0.0
    start_angle: float = 0.0
    end_angle: float = 0.0
    ccw: bool = True

    @property
    def sweep(self) -> float:
        if self.kind == CIRCLE:
            return 2 * math.pi
        if self.kind != ARC:
            return 0.0
        return (self.end_angle - self.start_angle) % (2 * math.pi)

    @property
    def length_mm(self) -> float:
        if self.kind == LINE:
            return math.hypot(self.x2 - self.x1, self.y2 - self.y1)
        return abs(self.radius * self.sweep)

    def endpoints(self) -> tuple:
        if self.kind == LINE:
            return ((self.x1, self.y1), (self.x2, self.y2))
        if self.kind == CIRCLE:
            p = (self.cx + self.radius, self.cy)
            return (p, p)
        return (
            (self.cx + self.radius * math.cos(self.start_angle),
             self.cy + self.radius * math.sin(self.start_angle)),
            (self.cx + self.radius * math.cos(self.end_angle),
             self.cy + self.radius * math.sin(self.end_angle)))

    def points(self, *, tol_mm: float = DENSIFY_TOL_MM) -> list:
        """Densified points — for topology and drawing, never for storage."""
        if self.kind == LINE:
            return [(self.x1, self.y1), (self.x2, self.y2)]
        sweep = self.sweep or 2 * math.pi
        if self.radius <= 0:
            return []
        # chord error = r(1 - cos(step/2)) <= tol  =>  step = 2*acos(1-tol/r)
        ratio = max(-1.0, min(1.0, 1.0 - tol_mm / self.radius))
        step = 2 * math.acos(ratio) if self.radius > tol_mm else sweep
        n = max(2, int(math.ceil(abs(sweep) / max(step, 1e-9))))
        out = []
        for i in range(n + 1):
            a = self.start_angle + sweep * i / n
            out.append((self.cx + self.radius * math.cos(a),
                        self.cy + self.radius * math.sin(a)))
        return out

    def record(self) -> dict:
        out = {"kind": self.kind, "role": self.role,
               "length_mm": round(self.length_mm, 3),
               "entity": {"object_id": self.object_id,
                          "dwg_handle": self.dwg_handle,
                          "layer": self.layer,
                          "entity_type": self.entity_type}}
        if self.kind == LINE:
            out["start_mm"] = [round(self.x1, 4), round(self.y1, 4)]
            out["end_mm"] = [round(self.x2, 4), round(self.y2, 4)]
        else:
            out["centre_mm"] = [round(self.cx, 4), round(self.cy, 4)]
            out["radius_mm"] = round(self.radius, 4)
            out["start_angle_rad"] = round(self.start_angle, 9)
            out["end_angle_rad"] = round(self.end_angle, 9)
            out["sweep_rad"] = round(self.sweep, 9)
            out["sweep_deg"] = round(math.degrees(self.sweep), 6)
            out["direction"] = "CCW" if self.ccw else "CW"
            out["exact_parameters_retained"] = True
        return out


# ------------------------------------------------------------- boundaries

@dataclass
class CompositeBoundary:
    """An ordered run of segments. Closed where the drawing closes it."""

    segments: tuple = ()
    closed: bool = False
    densify_tol_mm: float = DENSIFY_TOL_MM

    @property
    def kind(self) -> str:
        kinds = {s.kind for s in self.segments}
        if not kinds:
            return ""
        if kinds == {LINE}:
            return POLYLINE
        if kinds == {CIRCLE} and len(self.segments) == 1:
            return CIRCLE
        return COMPOSITE_CURVE

    @property
    def arc_count(self) -> int:
        return sum(1 for s in self.segments if s.kind in (ARC, CIRCLE))

    @property
    def has_curves(self) -> bool:
        return self.arc_count > 0

    @property
    def perimeter_mm(self) -> float:
        return sum(s.length_mm for s in self.segments)

    def points(self) -> list:
        out = []
        for seg in self.segments:
            pts = seg.points(tol_mm=self.densify_tol_mm)
            if out and pts and _close(out[-1], pts[0]):
                pts = pts[1:]
            out += pts
        return out

    def bbox_for_indexing_only(self) -> dict:
        pts = self.points()
        if not pts:
            return {"note": A_BOUNDING_BOX_IS_NOT_MEASUREMENT_GEOMETRY}
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return {"extent_mm": [round(min(xs), 3), round(min(ys), 3),
                              round(max(xs), 3), round(max(ys), 3)],
                "BOUNDING_BOX_IS_NOT_MEASUREMENT_GEOMETRY": True,
                "why": A_BOUNDING_BOX_IS_NOT_MEASUREMENT_GEOMETRY}

    def geometry_hash(self) -> str:
        rows = sorted(
            f"{s.kind}|{s.object_id}|{s.x1:.4f},{s.y1:.4f},{s.x2:.4f},"
            f"{s.y2:.4f}|{s.cx:.4f},{s.cy:.4f},{s.radius:.4f},"
            f"{s.start_angle:.9f},{s.end_angle:.9f}"
            for s in self.segments)
        return hashlib.sha256("|".join(rows).encode("utf-8")).hexdigest()[:24]

    def record(self) -> dict:
        return {
            "representation": self.kind,
            "closed": self.closed,
            "segments": len(self.segments),
            "line_segments": sum(1 for s in self.segments if s.kind == LINE),
            "arc_segments": sum(1 for s in self.segments if s.kind == ARC),
            "circle_segments": sum(1 for s in self.segments
                                   if s.kind == CIRCLE),
            "has_curves": self.has_curves,
            "perimeter_mm": round(self.perimeter_mm, 3),
            "BOUNDARY_SEGMENTS": [s.record() for s in self.segments],
            "GEOMETRY_HASH": self.geometry_hash(),
            "densification": {
                "tolerance_mm": self.densify_tol_mm,
                "used_for": "TOPOLOGY_AND_RENDERING_ONLY",
                "not_used_for": "THE_STORED_BOUNDARY",
                "why": WHY_A_CURVE_STAYS_A_CURVE},
            "bounding_box": self.bbox_for_indexing_only(),
        }


def _close(a, b, tol=SNAP_MM) -> bool:
    return math.hypot(a[0] - b[0], a[1] - b[1]) <= tol


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "KINDS": list(KINDS),
        "ROLES": list(ROLES),
        "TOPOLOGY_STATES": list(TOPOLOGY_STATES),
        "GEOMETRY_STATES": list(GEOMETRY_STATES),
        "DENSIFY_TOL_MM": DENSIFY_TOL_MM,
        "SNAP_MM": SNAP_MM,
        "OWNER_TOL_MM": OWNER_TOL_MM,
        "why": {
            "a_curve_stays_a_curve": WHY_A_CURVE_STAYS_A_CURVE,
            "a_bounding_box_is_not_measurement_geometry":
                A_BOUNDING_BOX_IS_NOT_MEASUREMENT_GEOMETRY,
            "a_line_is_not_a_wall_until_its_layer_says_so":
                A_LINE_IS_NOT_A_WALL_UNTIL_ITS_LAYER_SAYS_SO,
            "what_the_previous_pipeline_could_not_do": (
                "the axis-aligned enclosure engine emitted only V and H "
                "edges, so this drawing's 345 arcs and 106 circles could "
                "not appear in any boundary it produced"),
        },
    }


# ------------------------------------------------------------- the tracer

def _as_segment(prim, *, role=ROLE_UNRESOLVED) -> BoundarySegment:
    """One adapter primitive, carried across without losing its shape."""
    prov = prim.provenance
    common = dict(object_id=prim.object_id, dwg_handle=prov.handle,
                  layer=prov.layer, entity_type=prov.entity_type, role=role)
    if prim.kind == "SEGMENT":
        return BoundarySegment(kind=LINE, x1=prim.x1, y1=prim.y1,
                               x2=prim.x2, y2=prim.y2, **common)
    if prim.kind == "ARC":
        return BoundarySegment(kind=ARC, cx=prim.cx, cy=prim.cy,
                               radius=prim.radius,
                               start_angle=prim.start_angle,
                               end_angle=prim.end_angle, **common)
    if prim.kind == "CIRCLE":
        return BoundarySegment(kind=CIRCLE, cx=prim.cx, cy=prim.cy,
                               radius=prim.radius, **common)
    raise CadGeometryError(
        f"{prim.kind} is not a shape this register can carry. It is not "
        "stored as an approximation of one either")


def _sub_arc(seg: BoundarySegment, p_from, p_to) -> BoundarySegment:
    """The part of an arc between two points on it, still an arc."""
    a1 = math.atan2(p_from[1] - seg.cy, p_from[0] - seg.cx)
    a2 = math.atan2(p_to[1] - seg.cy, p_to[0] - seg.cx)
    return BoundarySegment(kind=ARC, object_id=seg.object_id,
                           dwg_handle=seg.dwg_handle, layer=seg.layer,
                           entity_type=seg.entity_type, role=seg.role,
                           cx=seg.cx, cy=seg.cy, radius=seg.radius,
                           start_angle=a1, end_angle=a2, ccw=seg.ccw)


def trace(seed_mm, primitives, *, wall_layers=(), tol_mm=DENSIFY_TOL_MM,
          role_of=None, extra_segments=()) -> dict:
    """The exact CAD face a point falls in, with each edge's entity.

    Only primitives whose layer carries an established wall-like role are
    offered to the trace, because A LINE IS NOT A WALL UNTIL ITS LAYER
    SAYS SO. Everything excluded is counted and named, so a reader can see
    what was kept out and why.
    """
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import polygonize, unary_union
    from shapely.strtree import STRtree

    admitted, excluded = [], {}
    for prim in primitives:
        if prim.kind not in ("SEGMENT", "ARC", "CIRCLE"):
            excluded[prim.provenance.layer] = excluded.get(
                prim.provenance.layer, 0) + 1
            continue
        if wall_layers and prim.provenance.layer not in wall_layers:
            excluded[prim.provenance.layer] = excluded.get(
                prim.provenance.layer, 0) + 1
            continue
        admitted.append(prim)

    if seed_mm is None:
        return {"topology_status": TOPOLOGY_NO_SEED,
                "geometry_status": GEOMETRY_NOT_ESTABLISHED,
                "boundary": None, "excluded_by_layer": excluded,
                "why": "no interior point was supplied to trace from"}

    segs, lines = [], []
    # Opening barriers and junction repairs come in as segments, already
    # graded, and are carried with role OPENING so nothing downstream can
    # read one as a physical wall face.
    for extra in extra_segments:
        pts = extra.points(tol_mm=tol_mm)
        if len(pts) >= 2:
            segs.append(extra)
            lines.append(LineString(pts))
    for prim in admitted:
        seg = _as_segment(prim, role=(role_of or {}).get(
            prim.provenance.layer, ROLE_UNRESOLVED))
        pts = seg.points(tol_mm=tol_mm)
        if len(pts) < 2:
            continue
        segs.append(seg)
        lines.append(LineString(pts))

    if not lines:
        return {"topology_status": TOPOLOGY_NOT_CLOSED,
                "geometry_status": GEOMETRY_NOT_ESTABLISHED,
                "boundary": None, "excluded_by_layer": excluded,
                "why": ("no admitted wall-role geometry lies near this "
                        "point, so nothing drawn can bound it")}

    faces = list(polygonize(unary_union(lines)))
    seed = Point(float(seed_mm[0]), float(seed_mm[1]))
    holding = [f for f in faces if f.contains(seed)]
    if not holding:
        return {"topology_status": TOPOLOGY_NOT_CLOSED,
                "geometry_status": GEOMETRY_NOT_ESTABLISHED,
                "boundary": None, "faces_built": len(faces),
                "excluded_by_layer": excluded,
                "why": ("the admitted geometry builds no closed face "
                        "around this point. The space is not closed by "
                        "drawn wall-role lines")}
    face = min(holding, key=lambda f: f.area)

    tree = STRtree(lines)
    ring = list(face.exterior.coords)
    owned, unowned_mm = [], 0.0
    for a, b in zip(ring, ring[1:]):
        mid = Point((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        best, best_d = None, None
        for idx in tree.query(mid.buffer(OWNER_TOL_MM)):
            d = lines[int(idx)].distance(mid)
            if best_d is None or d < best_d:
                best, best_d = int(idx), d
        if best is None or best_d > OWNER_TOL_MM:
            owned.append((None, a, b))
            unowned_mm += math.hypot(b[0] - a[0], b[1] - a[1])
        else:
            owned.append((best, a, b))

    # Collapse consecutive edges that share an owner, recovering the exact
    # shape: a run of chords on one arc becomes ONE arc again.
    boundary, i = [], 0
    while i < len(owned):
        idx, a, _b = owned[i]
        j = i
        while j + 1 < len(owned) and owned[j + 1][0] == idx:
            j += 1
        end = owned[j][2]
        if idx is None:
            boundary.append(BoundarySegment(
                kind=LINE, x1=a[0], y1=a[1], x2=end[0], y2=end[1],
                role=ROLE_OPEN_EDGE, object_id="", layer="",
                entity_type="CONSTRUCTED_NOT_A_DRAWN_ENTITY"))
        else:
            src = segs[idx]
            if src.kind == LINE:
                boundary.append(BoundarySegment(
                    kind=LINE, object_id=src.object_id,
                    dwg_handle=src.dwg_handle, layer=src.layer,
                    entity_type=src.entity_type, role=src.role,
                    x1=a[0], y1=a[1], x2=end[0], y2=end[1]))
            else:
                boundary.append(_sub_arc(src, a, end))
        i = j + 1

    comp = CompositeBoundary(segments=tuple(boundary), closed=True,
                             densify_tol_mm=tol_mm)
    open_mm = sum(s.length_mm for s in comp.segments
                  if s.role == ROLE_OPEN_EDGE)
    status = (TOPOLOGY_CLOSED if open_mm <= SNAP_MM
              else TOPOLOGY_CLOSED_WITH_OPEN_EDGES)
    return {
        "topology_status": status,
        "geometry_status": (GEOMETRY_EXACT if open_mm <= SNAP_MM
                            else GEOMETRY_PARTIAL),
        "boundary": comp,
        "faces_built": len(faces),
        "faces_holding_the_seed": len(holding),
        "densified_area_m2_topology_only": round(face.area / 1e6, 6),
        "open_edge_length_mm": round(open_mm, 3),
        "constructed_edge_length_mm": round(unowned_mm, 3),
        "excluded_by_layer": excluded,
        "clear_face_basis": (BASIS_DRAWN_FACE if open_mm <= SNAP_MM
                             else BASIS_NOT_ESTABLISHED),
        "why": ("every edge of this boundary lies on a drawn entity, and "
                "each one names it" if open_mm <= SNAP_MM else
                "part of this boundary is not on any drawn wall-role "
                "entity, and those stretches are marked as open edges"),
    }


# ------------------------------------------------------- opening closure

# GENERAL construction rule, not a project dimension: a single leaf is at
# most about 1.2 m and a double leaf about 2.4 m. A gap wider than that,
# with no door entity standing in it, is not a door — it is an open edge,
# and calling it a door would close a boundary the architect left open.
MAX_SINGLE_LEAF_MM = 1200.0
MAX_DOUBLE_LEAF_MM = 2400.0

# A gap this small is not an opening. It is a line that stops short of its
# junction - drafting imprecision - and closing it is a repair, recorded as
# one. Calling a 2 mm gap a doorway would put 141 imaginary doors in this
# drawing, which is what the first version of this rule did.
JUNCTION_GAP_MM = 20.0

# A DOOR GAP LIES ALONG THE WALL. Two dangling ends are only candidates if
# each one's wall runs TOWARD the other: the gap continues both lines. The
# first version of this rule paired ends by distance alone and cheerfully
# joined unrelated ends metres apart across a room.
COLLINEAR_DEG = 5.0

JUNCTION_REPAIR = "A_LINE_STOPS_SHORT_OF_ITS_JUNCTION"
OPENING_GRADE_DOOR_ENTITY = "A_DOOR_ENTITY_STANDS_IN_THE_GAP"
OPENING_GRADE_JAMB_PAIR = "TWO_WALL_ENDS_FACE_EACH_OTHER_ACROSS_IT"
OPENING_GRADE_NONE = "NO_OPENING_EVIDENCE"

WHY_A_WIDE_GAP_IS_NOT_A_DOOR = (
    "a gap wider than a double leaf with no door entity in it is an open "
    "edge. Closing it would invent a boundary the author did not draw, and "
    "an open-plan room would come out as a closed one")


def close_openings(primitives, *, wall_layers=(), door_layers=(),
                   tol_mm=DENSIFY_TOL_MM,
                   max_barrier_mm=MAX_DOUBLE_LEAF_MM) -> dict:
    """Barriers across wall gaps that carry opening evidence.

    A door in plan is a GAP between two wall ends. Nothing closes a room
    across it, so a trace leaks through every doorway and out of the
    building. This finds the gaps by their geometry - two dangling wall
    ends facing each other - and closes only those that carry evidence,
    recording the entity ids on both sides and what licensed the closure.

    A barrier is never a wall. It is stored with role OPENING so that no
    later stage can read it as a physical face.
    """
    from shapely.geometry import LineString, Point
    from shapely.ops import unary_union
    from shapely.strtree import STRtree

    wall_prims = [p for p in primitives
                  if p.kind in ("SEGMENT", "ARC", "CIRCLE")
                  and (not wall_layers or p.provenance.layer in wall_layers)]
    door_prims = [p for p in primitives
                  if p.kind in ("SEGMENT", "ARC", "CIRCLE")
                  and door_layers and p.provenance.layer in door_layers]
    if not wall_prims:
        return {"barriers": [], "rows": [], "note": "no wall-role geometry"}

    segs = [_as_segment(p, role=ROLE_WALL_FACE) for p in wall_prims]
    lines = [LineString(s.points(tol_mm=tol_mm)) for s in segs
             if len(s.points(tol_mm=tol_mm)) >= 2]
    noded = unary_union(lines)
    parts = (list(noded.geoms) if hasattr(noded, "geoms") else [noded])

    def key(pt):
        return (round(pt[0] / SNAP_MM), round(pt[1] / SNAP_MM))

    degree, where, heading = {}, {}, {}
    for part in parts:
        cs = list(part.coords)
        for pt, inward in ((cs[0], cs[1]), (cs[-1], cs[-2])):
            k = key(pt)
            degree[k] = degree.get(k, 0) + 1
            where[k] = pt
            # the direction the wall runs AWAY from this end, so a gap that
            # continues the line points the other way
            dx, dy = pt[0] - inward[0], pt[1] - inward[1]
            n = math.hypot(dx, dy) or 1.0
            heading[k] = (dx / n, dy / n)
    dangling = [where[k] for k, n in degree.items() if n == 1]

    door_lines = [LineString(_as_segment(p).points(tol_mm=tol_mm))
                  for p in door_prims
                  if len(_as_segment(p).points(tol_mm=tol_mm)) >= 2]
    door_tree = STRtree(door_lines) if door_lines else None
    wall_tree = STRtree(lines) if lines else None

    cos_lim = math.cos(math.radians(COLLINEAR_DEG))

    def continues(a, b, gap):
        """Does the gap a->b continue BOTH walls, along their own lines?"""
        ux, uy = (b[0] - a[0]) / gap, (b[1] - a[1]) / gap
        ha, hb = heading[key(a)], heading[key(b)]
        return (ha[0] * ux + ha[1] * uy >= cos_lim
                and hb[0] * -ux + hb[1] * -uy >= cos_lim)

    pairs, rejected_not_collinear = [], 0
    for i, a in enumerate(dangling):
        for b in dangling[i + 1:]:
            gap = math.hypot(b[0] - a[0], b[1] - a[1])
            if not (SNAP_MM < gap <= max_barrier_mm):
                continue
            if not continues(a, b, gap):
                rejected_not_collinear += 1
                continue
            pairs.append((gap, a, b))
    pairs.sort(key=lambda r: r[0])

    used, rows, barriers = set(), [], []
    for gap, a, b in pairs:
        ka, kb = key(a), key(b)
        if ka in used or kb in used:
            continue
        mid = Point((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        span = LineString([a, b])
        door_hits = []
        if door_tree is not None:
            for idx in door_tree.query(span.buffer(gap / 2.0 + 50.0)):
                if door_lines[int(idx)].distance(mid) <= gap / 2.0 + 50.0:
                    door_hits.append(int(idx))
        if gap <= JUNCTION_GAP_MM:
            grade = JUNCTION_REPAIR
        elif door_hits:
            grade = OPENING_GRADE_DOOR_ENTITY
        elif gap <= max_barrier_mm:
            grade = OPENING_GRADE_JAMB_PAIR
        else:
            grade = OPENING_GRADE_NONE
        if grade == OPENING_GRADE_NONE:
            continue
        sides = []
        if wall_tree is not None:
            for pt in (a, b):
                p = Point(pt)
                near = [(lines[int(i)].distance(p), int(i))
                        for i in wall_tree.query(p.buffer(SNAP_MM * 4))]
                near.sort()
                if near:
                    sides.append(segs[near[0][1]].object_id)
        used.add(ka)
        used.add(kb)
        bar = BoundarySegment(
            kind=LINE, x1=a[0], y1=a[1], x2=b[0], y2=b[1],
            role=ROLE_OPENING, object_id="",
            entity_type=("JUNCTION_REPAIR_NOT_A_DRAWN_ENTITY"
                         if grade == JUNCTION_REPAIR
                         else "OPENING_BARRIER_NOT_A_DRAWN_ENTITY"),
            layer="|".join(sorted({s for s in sides})))
        barriers.append(bar)
        rows.append({
            "opening_id": f"OPN-{len(rows) + 1:03d}",
            "gap_mm": round(gap, 2),
            "at_mm": [round(mid.x, 2), round(mid.y, 2)],
            "grade": grade,
            "leaf_class": ("SINGLE_LEAF_WIDTH_OR_LESS"
                           if gap <= MAX_SINGLE_LEAF_MM
                           else "UP_TO_A_DOUBLE_LEAF"),
            "wall_entities_either_side": sides,
            "door_entities_in_the_gap": [
                door_prims[i].object_id for i in door_hits][:6],
            "barrier_is_not_a_wall": True,
        })

    wide = [(round(g, 1), [round(a[0], 1), round(a[1], 1)])
            for g, a, _b in pairs if g > max_barrier_mm]
    return {
        "barriers": barriers,
        "rows": rows,
        "dangling_wall_ends": len(dangling),
        "collinear_candidate_pairs": len(pairs),
        "pairs_rejected_not_collinear": rejected_not_collinear,
        "gaps_closed": len(rows),
        "junction_repairs": sum(1 for r in rows
                                if r["grade"] == JUNCTION_REPAIR),
        "openings": sum(1 for r in rows if r["grade"] != JUNCTION_REPAIR),
        "gaps_left_open_because_too_wide": len(wide),
        "rule": {
            "JUNCTION_GAP_MM": JUNCTION_GAP_MM,
            "COLLINEAR_DEG": COLLINEAR_DEG,
            "MAX_SINGLE_LEAF_MM": MAX_SINGLE_LEAF_MM,
            "MAX_DOUBLE_LEAF_MM": MAX_DOUBLE_LEAF_MM,
            "a_door_gap_lies_along_the_wall": (
                "both wall ends must run toward each other within "
                f"{COLLINEAR_DEG} degrees. Pairing by distance alone joins "
                "unrelated ends across a room"),
            "a_small_gap_is_a_junction_not_a_door": (
                f"at or below {JUNCTION_GAP_MM} mm the line stops short of "
                "its junction. That is a drafting repair and is recorded as "
                "one, never as an opening"),
            "scope": "A GENERAL construction rule, not a project dimension",
            "why_a_wide_gap_is_not_a_door": WHY_A_WIDE_GAP_IS_NOT_A_DOOR,
        },
    }
