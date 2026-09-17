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
#
# THREE GEOMETRIES ARE KEPT APART HERE, and the role is what keeps them
# apart:
#
#   MATERIAL_GEOMETRY   things built: wall faces, columns, glazing,
#                       structural boundaries. These carry material length
#   SPACE_TOPOLOGY      lines that separate spaces without being built. A
#                       doorway needs one so that two rooms can be two
#                       rooms, and it is NOT material
#   FUNCTIONAL/TRADE    not E1's business at all, and not invented here
MATERIAL_WALL_FACE = "MATERIAL_WALL_FACE"
CURVED_MATERIAL_FACE = "CURVED_MATERIAL_FACE"
GLAZING_BOUNDARY = "GLAZING_BOUNDARY"
COLUMN_FACE = "COLUMN_FACE"
OPENING = "OPENING"
PORTAL = "PORTAL"
VIRTUAL_PORTAL_BOUNDARY = "VIRTUAL_PORTAL_BOUNDARY"
OPEN_EDGE = "OPEN_EDGE"
STAIR_CUT_PLANE = "STAIR_CUT_PLANE"
ANNOTATION_ONLY = "ANNOTATION_ONLY"
DIMENSION_WITNESS = "DIMENSION_WITNESS"
CAD_JUNCTION_REPAIR = "CAD_JUNCTION_REPAIR"
ROLE_UNRESOLVED = "UNRESOLVED"
ROLES = (MATERIAL_WALL_FACE, CURVED_MATERIAL_FACE, GLAZING_BOUNDARY,
         COLUMN_FACE, OPENING, PORTAL, VIRTUAL_PORTAL_BOUNDARY, OPEN_EDGE,
         STAIR_CUT_PLANE, ANNOTATION_ONLY, DIMENSION_WITNESS,
         CAD_JUNCTION_REPAIR, ROLE_UNRESOLVED)

# Which roles are built material. Everything else contributes ZERO wall
# length, and the register computes that rather than trusting a caller.
MATERIAL_ROLES = (MATERIAL_WALL_FACE, CURVED_MATERIAL_FACE,
                  GLAZING_BOUNDARY, COLUMN_FACE)

# Roles that exist only to let topology close. A doorway closure is one.
TOPOLOGY_ONLY_ROLES = (VIRTUAL_PORTAL_BOUNDARY, OPEN_EDGE,
                       CAD_JUNCTION_REPAIR)

A_VIRTUAL_BOUNDARY_IS_NOT_WALL_MATERIAL = (
    "a line inserted across a doorway lets two spaces be two spaces. "
    "Nothing was built along it, so it contributes no wall material "
    "length, and the register computes that from the role rather than "
    "trusting whoever inserted it")

RENDERING_ONLY = "RENDERING_ONLY"

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

# Node coincidence. A quarter-arc computed from centre and angle lands at
# x = 1.2e-13 rather than 0, and polygonize needs nodes to MEET, so a
# quarter-disc built from three lines and an arc produced no face at all.
# The linework is snapped to this grid before topology - declared, like
# the densification, and applied to nothing that is stored.
NODE_SNAP_MM = 0.001

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
    evidence: tuple = ()
    confidence: str = ""

    @property
    def material_present(self) -> bool:
        return self.role in MATERIAL_ROLES

    @property
    def wall_length_contribution_mm(self) -> float:
        """Zero unless something was actually built along this piece."""
        return self.length_mm if self.material_present else 0.0

    @property
    def sweep(self) -> float:
        """The angle actually swept, in the direction this arc runs.

        A boundary ring may walk an arc either way round. Assuming CCW
        turned a recovered quarter-round into a 270 degree sweep, so the
        direction is carried on the segment and honoured here.
        """
        if self.kind == CIRCLE:
            return 2 * math.pi
        if self.kind != ARC:
            return 0.0
        if self.ccw:
            return (self.end_angle - self.start_angle) % (2 * math.pi)
        return (self.start_angle - self.end_angle) % (2 * math.pi)

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
        """RENDERING_ONLY / topology tessellation. Never the geometry.

        The analytical geometry of an arc is its centre, radius and
        angles, which this object keeps. These chords exist so a face can
        be found and a picture drawn, and no chord may become measurement
        geometry.
        """
        if self.kind == LINE:
            return [(self.x1, self.y1), (self.x2, self.y2)]
        sweep = self.sweep or 2 * math.pi
        if not self.ccw:
            sweep = -sweep
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
        out = {"kind": self.kind, "boundary_role": self.role,
               "length_mm": round(self.length_mm, 3),
               "material_present": self.material_present,
               "wall_length_contribution_mm": round(
                   self.wall_length_contribution_mm, 3),
               "entity": {"object_id": self.object_id,
                          "dwg_handle": self.dwg_handle,
                          "layer": self.layer,
                          "entity_type": self.entity_type}}
        if self.evidence:
            out["evidence"] = list(self.evidence)
        if self.confidence:
            out["confidence"] = self.confidence
        if self.role in TOPOLOGY_ONLY_ROLES:
            out["why_no_material"] = A_VIRTUAL_BOUNDARY_IS_NOT_WALL_MATERIAL
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
            out["analytical_geometry"] = "THE_ORIGINAL_CURVE"
            out["tessellation"] = RENDERING_ONLY
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

    @property
    def material_length_mm(self) -> float:
        return sum(s.wall_length_contribution_mm for s in self.segments)

    @property
    def topology_only_length_mm(self) -> float:
        return sum(s.length_mm for s in self.segments
                   if s.role in TOPOLOGY_ONLY_ROLES)

    def by_role(self) -> dict:
        out = {}
        for seg in self.segments:
            out[seg.role] = round(out.get(seg.role, 0.0) + seg.length_mm, 3)
        return out

    @property
    def contains_artificial_topology(self) -> bool:
        return any(s.role in (VIRTUAL_PORTAL_BOUNDARY, CAD_JUNCTION_REPAIR)
                   for s in self.segments)

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
            "material_length_mm": round(self.material_length_mm, 3),
            "topology_only_length_mm": round(self.topology_only_length_mm, 3),
            "length_by_boundary_role": self.by_role(),
            "contains_artificial_topology":
                self.contains_artificial_topology,
            "a_virtual_boundary_is_not_wall_material":
                A_VIRTUAL_BOUNDARY_IS_NOT_WALL_MATERIAL,
            "BOUNDARY_SEGMENTS": [s.record() for s in self.segments],
            "GEOMETRY_HASH": self.geometry_hash(),
            "densification": {
                "tolerance_mm": self.densify_tol_mm,
                "used_for": RENDERING_ONLY + "_AND_TOPOLOGY",
                "not_used_for": "THE_STORED_BOUNDARY",
                "why": WHY_A_CURVE_STAYS_A_CURVE},
            "bounding_box": self.bbox_for_indexing_only(),
        }


def _noded(geom):
    """Snap linework to the node grid so that meeting ends actually meet."""
    try:
        from shapely import set_precision
        return set_precision(geom, NODE_SNAP_MM)
    except Exception:
        return geom


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
        "NODE_SNAP_MM": NODE_SNAP_MM,
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

GLAZING_LAYERS_DEFAULT = ()
COLUMN_LAYERS_DEFAULT = ("S-COL.BON",)


def _material_role(prim, *, glazing_layers=GLAZING_LAYERS_DEFAULT,
                   column_layers=COLUMN_LAYERS_DEFAULT) -> str:
    """The material role of one drawn primitive, by shape and layer.

    A curved material face is not a straight one, and the register says
    which it is rather than leaving a reviewer to infer it from the
    parameters.
    """
    layer = prim.provenance.layer
    if layer in column_layers:
        return COLUMN_FACE
    if layer in glazing_layers:
        return GLAZING_BOUNDARY
    if prim.kind in ("ARC", "CIRCLE"):
        return CURVED_MATERIAL_FACE
    return MATERIAL_WALL_FACE


def _as_segment(prim, *, role=ROLE_UNRESOLVED) -> BoundarySegment:
    """One adapter primitive, carried across without losing its shape."""
    prov = prim.provenance
    common = dict(object_id=prim.object_id, dwg_handle=prov.handle,
                  layer=prov.layer, entity_type=prov.entity_type, role=role)
    if prim.kind == "SEGMENT":
        return BoundarySegment(kind=LINE, x1=prim.x1, y1=prim.y1,
                               x2=prim.x2, y2=prim.y2, **common)
    if prim.kind == "ARC":
        if common["role"] == MATERIAL_WALL_FACE:
            common["role"] = CURVED_MATERIAL_FACE
        return BoundarySegment(kind=ARC, cx=prim.cx, cy=prim.cy,
                               radius=prim.radius,
                               start_angle=prim.start_angle,
                               end_angle=prim.end_angle, **common)
    if prim.kind == "CIRCLE":
        if common["role"] == MATERIAL_WALL_FACE:
            common["role"] = CURVED_MATERIAL_FACE
        return BoundarySegment(kind=CIRCLE, cx=prim.cx, cy=prim.cy,
                               radius=prim.radius, **common)
    raise CadGeometryError(
        f"{prim.kind} is not a shape this register can carry. It is not "
        "stored as an approximation of one either")


def _sub_arc(seg: BoundarySegment, p_from, p_to) -> BoundarySegment:
    """The part of an arc between two points on it, still an arc.

    The ring may traverse the arc either way. Whichever direction gives a
    sweep that FITS INSIDE the source arc is the direction this piece
    runs; taking CCW on faith reported a quarter-round as 270 degrees.
    """
    a1 = math.atan2(p_from[1] - seg.cy, p_from[0] - seg.cx)
    a2 = math.atan2(p_to[1] - seg.cy, p_to[0] - seg.cx)
    two_pi = 2 * math.pi
    ccw_sweep = (a2 - a1) % two_pi
    cw_sweep = (a1 - a2) % two_pi
    source = seg.sweep or two_pi
    eps = 1e-6
    if ccw_sweep <= source + eps and cw_sweep > source + eps:
        ccw = True
    elif cw_sweep <= source + eps and ccw_sweep > source + eps:
        ccw = False
    else:
        ccw = ccw_sweep <= cw_sweep
    return BoundarySegment(kind=ARC, object_id=seg.object_id,
                           dwg_handle=seg.dwg_handle, layer=seg.layer,
                           entity_type=seg.entity_type, role=seg.role,
                           evidence=seg.evidence, confidence=seg.confidence,
                           cx=seg.cx, cy=seg.cy, radius=seg.radius,
                           start_angle=a1, end_angle=a2, ccw=ccw)


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

    faces = list(polygonize(_noded(unary_union(lines))))
    seed = Point(float(seed_mm[0]), float(seed_mm[1]))
    holding = sorted((f for f in faces if f.contains(seed)),
                     key=lambda f: f.area)
    if not holding:
        return {"topology_status": TOPOLOGY_NOT_CLOSED,
                "geometry_status": GEOMETRY_NOT_ESTABLISHED,
                "candidates": [], "faces_built": len(faces),
                "excluded_by_layer": excluded,
                "why": ("the admitted geometry builds no closed face "
                        "around this point. The space is not closed by "
                        "drawn wall-role lines, and that is a result "
                        "rather than a failure to be repaired")}

    tree = STRtree(lines)

    def boundary_of(face):
        ring = list(face.exterior.coords)
        owned, unowned_mm = [], 0.0
        for a, b in zip(ring, ring[1:]):
            mid = Point((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
            best, best_d = None, None
            for idx in tree.query(mid.buffer(OWNER_TOL_MM)):
                dd = lines[int(idx)].distance(mid)
                if best_d is None or dd < best_d:
                    best, best_d = int(idx), dd
            if best is None or best_d > OWNER_TOL_MM:
                owned.append((None, a, b))
                unowned_mm += math.hypot(b[0] - a[0], b[1] - a[1])
            else:
                owned.append((best, a, b))

        # A run of chords on ONE arc becomes that arc again, with its own
        # centre, radius and angles. No chord becomes geometry.
        out, i = [], 0
        while i < len(owned):
            idx, a, _b = owned[i]
            j = i
            while j + 1 < len(owned) and owned[j + 1][0] == idx:
                j += 1
            end = owned[j][2]
            if idx is None:
                out.append(BoundarySegment(
                    kind=LINE, x1=a[0], y1=a[1], x2=end[0], y2=end[1],
                    role=OPEN_EDGE, object_id="", layer="",
                    entity_type="NOT_ON_ANY_DRAWN_ENTITY",
                    evidence=("no drawn wall-role entity lies along this "
                              "stretch",)))
            else:
                src = segs[idx]
                if src.kind == LINE:
                    out.append(BoundarySegment(
                        kind=LINE, object_id=src.object_id,
                        dwg_handle=src.dwg_handle, layer=src.layer,
                        entity_type=src.entity_type, role=src.role,
                        evidence=src.evidence, confidence=src.confidence,
                        x1=a[0], y1=a[1], x2=end[0], y2=end[1]))
                else:
                    out.append(_sub_arc(src, a, end))
            i = j + 1
        return CompositeBoundary(segments=tuple(out), closed=True,
                                 densify_tol_mm=tol_mm), unowned_mm

    candidates = []
    for rank, face in enumerate(holding, start=1):
        comp, unowned_mm = boundary_of(face)
        open_mm = sum(x.length_mm for x in comp.segments
                      if x.role == OPEN_EDGE)
        candidates.append({
            "candidate_rank_by_area": rank,
            "topology_status": (TOPOLOGY_CLOSED if open_mm <= SNAP_MM
                                else TOPOLOGY_CLOSED_WITH_OPEN_EDGES),
            "geometry_status": (GEOMETRY_EXACT if open_mm <= SNAP_MM
                                else GEOMETRY_PARTIAL),
            "boundary": comp,
            "densified_area_m2_rendering_only": round(face.area / 1e6, 6),
            "open_edge_length_mm": round(open_mm, 3),
            "not_on_a_drawn_entity_mm": round(unowned_mm, 3),
            "material_length_mm": round(comp.material_length_mm, 3),
            "topology_only_length_mm": round(comp.topology_only_length_mm, 3),
            "contains_artificial_topology":
                comp.contains_artificial_topology,
            "clear_face_basis": (BASIS_DRAWN_FACE if open_mm <= SNAP_MM
                                 else BASIS_NOT_ESTABLISHED),
        })

    return {
        "topology_status": candidates[0]["topology_status"],
        "geometry_status": candidates[0]["geometry_status"],
        "candidates": candidates,
        "faces_built": len(faces),
        "faces_holding_the_seed": len(holding),
        "excluded_by_layer": excluded,
        "ownership_is_not_decided_here": (
            "a seed inside a face does NOT mean the face owns the labelled "
            "space. Every face containing the point is returned with its "
            "own boundary and evidence, and the region layer decides - or "
            "withholds"),
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

GRADE_JUNCTION = "A_LINE_STOPS_SHORT_OF_ITS_JUNCTION"
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

    segs = [_as_segment(p, role=_material_role(p))
            for p in wall_prims]
    lines = [LineString(s.points(tol_mm=tol_mm)) for s in segs
             if len(s.points(tol_mm=tol_mm)) >= 2]
    noded = _noded(unary_union(lines))
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

    # TWO DIFFERENT GEOMETRIES, so two passes.
    #
    # A DOORWAY lies ALONG a wall: both ends run toward each other and the
    # gap continues the line. A JUNCTION gap sits at a CORNER, where the
    # two ends are perpendicular - so requiring collinearity correctly
    # rejects it, and a corner repair needs its own proximity rule. One
    # rule for both would either miss the corners or invent doors.
    pairs, rejected_not_collinear = [], 0
    for i, a in enumerate(dangling):
        for b in dangling[i + 1:]:
            gap = math.hypot(b[0] - a[0], b[1] - a[1])
            if not (NODE_SNAP_MM < gap <= max_barrier_mm):
                continue
            if gap <= JUNCTION_GAP_MM:
                pairs.append((gap, a, b))          # a corner, any angle
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
            grade = GRADE_JUNCTION
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
        is_repair = grade == GRADE_JUNCTION
        ev = [grade, f"gap_mm={round(gap, 2)}"]
        ev += [f"host_wall={i}" for i in sides]
        ev += [f"door_entity={door_prims[i].object_id}" for i in door_hits[:4]]
        bar = BoundarySegment(
            kind=LINE, x1=a[0], y1=a[1], x2=b[0], y2=b[1],
            role=(CAD_JUNCTION_REPAIR if is_repair
                  else VIRTUAL_PORTAL_BOUNDARY),
            object_id="",
            entity_type=("CAD_JUNCTION_REPAIR_NOT_AN_ORIGINAL_CAD_ENTITY"
                         if is_repair
                         else "VIRTUAL_PORTAL_BOUNDARY_NOTHING_WAS_BUILT_HERE"),
            layer="|".join(sorted({s for s in sides})),
            evidence=tuple(ev), confidence=("HIGH" if door_hits else "MEDIUM"))
        barriers.append(bar)
        rows.append({
            "portal_id": (f"REPAIR-{len(rows) + 1:03d}" if is_repair
                          else f"PORTAL-{len(rows) + 1:03d}"),
            "class": (CAD_JUNCTION_REPAIR if is_repair
                      else "PORTAL_OR_OPENING_CANDIDATE"),
            "boundary_role": (CAD_JUNCTION_REPAIR if is_repair
                              else VIRTUAL_PORTAL_BOUNDARY),
            "material_present": False,
            "wall_length_contribution_mm": 0.0,
            "gap_mm": round(gap, 2),
            "at_mm": [round(mid.x, 2), round(mid.y, 2)],
            "grade": grade,
            "leaf_class": ("SINGLE_LEAF_WIDTH_OR_LESS"
                           if gap <= MAX_SINGLE_LEAF_MM
                           else "UP_TO_A_DOUBLE_LEAF"),
            "host_wall_faces": sides,
            "jamb_endpoints_mm": [[round(a[0], 3), round(a[1], 3)],
                                  [round(b[0], 3), round(b[1], 3)]],
            "opening_width_mm": round(gap, 2),
            "door_entities_in_the_gap": [
                door_prims[i].object_id for i in door_hits][:6],
            "confidence": ("HIGH" if door_hits else "MEDIUM"),
            "threshold_geometry": "NOT_ESTABLISHED_IN_E1",
            "why_no_material": A_VIRTUAL_BOUNDARY_IS_NOT_WALL_MATERIAL,
            "original_vs_repaired": ("REPAIRED_TOPOLOGY" if is_repair
                                     else "VIRTUAL_TOPOLOGY"),
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
                                if r["grade"] == GRADE_JUNCTION),
        "openings": sum(1 for r in rows if r["grade"] != GRADE_JUNCTION),
        "gaps_left_open_because_too_wide": len(wide),
        "rule": {
            "JUNCTION_GAP_MM": JUNCTION_GAP_MM,
            "COLLINEAR_DEG": COLLINEAR_DEG,
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
