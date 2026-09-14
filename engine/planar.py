"""E31A — directed half-edge (DCEL) planar face extraction.

The graph is not globally healthy and this engine is built anyway, because the
two questions were being conflated:

    can we safely BUILD and TEST the face engine?      -> yes, locally
    can 23010 RELEASE quantities from its results?     -> no, and not soon

43 independent cycles exist in 12 components and 14 of 17 in-scope regions have
a possible enclosure. That is enough to learn whether the face walker works.
Waiting for 109 unresolved termini to be classified first would have meant
building it blind.

SO EVERY FACE THIS ENGINE PRODUCES IS A HYPOTHESIS. A face carries CANDIDATE,
PROBABLE, VALIDATED or AMBIGUOUS, it names the evidence it depended on, and
nothing here may release a quantity or replace the current geometry source. A
diagnostic face that silently became the measurement basis would be the worst
outcome available.

HOW IT WORKS, and the one rule that keeps it honest:

    VECTOR WALL GRAPH -> DIRECTED HALF-EDGES -> CLOSED FACE WALKS

    The raster region map is NOT an input. It is used afterwards, for
    comparison only. Seeding a vector face from a raster boundary would make
    this engine an elaborate way of reproducing the old segmentation, and the
    whole point is to find out whether the vector graph can stand alone.

Each undirected wall edge becomes two half-edges. At every node the outgoing
half-edges are sorted by angle, and `next(h)` is the half-edge immediately
clockwise from `twin(h)` around h's destination. Walking `next` until it
returns to the start yields one face. Orientation comes from the signed area of
the walk, never from its size:

    DO NOT ASSUME THE LARGEST FACE IS THE EXTERIOR.

A component whose exterior cannot be identified by orientation reports
UNBOUNDED_FACE_UNRESOLVED rather than guessing.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

# What a face is worth. None of these releases a quantity.
CANDIDATE = "CANDIDATE"
PROBABLE = "PROBABLE"
VALIDATED = "VALIDATED"
AMBIGUOUS = "AMBIGUOUS"

FACE_STATUSES = (CANDIDATE, PROBABLE, VALIDATED, AMBIGUOUS)

# Which way a closed walk turns. The sign of the signed area, in the drawing's
# own frame — reported rather than interpreted, because a y-down coordinate
# system inverts the usual reading and a silent assumption there swaps every
# interior for an exterior.
ORIENT_CW = "CLOCKWISE"
ORIENT_CCW = "COUNTERCLOCKWISE"
ORIENT_DEGENERATE = "DEGENERATE_ZERO_AREA"

# The outer walk of a component, and the honest answer when it cannot be told.
UNBOUNDED = "UNBOUNDED_FACE"
BOUNDED = "BOUNDED_FACE"
UNBOUNDED_UNRESOLVED = "UNBOUNDED_FACE_UNRESOLVED"

# A face small enough to need classifying before anything is done with it.
# NOT a deletion threshold — see `classify_micro_faces`.
MICRO_FACE_M2 = 0.5
SLIVER_ASPECT = 8.0


class PlanarError(RuntimeError):
    """A face walk could not be completed without inventing topology."""


@dataclass(frozen=True)
class HalfEdge:
    """One direction of one wall edge."""

    half_edge_id: str
    source_edge_id: str
    origin_node: str
    target_node: str
    x0_mm: float
    y0_mm: float
    x1_mm: float
    y1_mm: float
    twin_id: str = ""
    next_id: str = ""
    face_id: str = ""

    @property
    def angle(self) -> float:
        """Direction of travel, in radians. Used only for ordering at a node."""
        return math.atan2(self.y1_mm - self.y0_mm, self.x1_mm - self.x0_mm)

    @property
    def length_mm(self) -> float:
        return math.hypot(self.x1_mm - self.x0_mm, self.y1_mm - self.y0_mm)

    def record(self) -> dict:
        return {"half_edge_id": self.half_edge_id,
                "source_edge_id": self.source_edge_id,
                "origin_node": self.origin_node, "target_node": self.target_node,
                "twin_id": self.twin_id, "next_id": self.next_id,
                "face_id": self.face_id,
                "length_mm": round(self.length_mm, 1)}


@dataclass(frozen=True)
class Face:
    """One closed walk, and everything it depended on to close.

    `status` is never VALIDATED from geometry alone: a face is only as good as
    the edges it walked, and an edge whose validation status is PROBABLE makes
    the face a hypothesis however cleanly it closes.
    """

    face_id: str
    component_id: str
    half_edge_ids: tuple[str, ...]
    polygon_mm: tuple[tuple[float, float], ...]
    signed_area_mm2: float
    perimeter_mm: float
    orientation: str
    kind: str
    source_wall_edge_ids: tuple[str, ...] = ()
    topology_boundary_candidate_ids: tuple[str, ...] = ()
    hole_face_ids: tuple[str, ...] = ()
    status: str = CANDIDATE
    geometry_confidence: str = ""
    edge_validation_summary: dict = field(default_factory=dict)
    blockers: tuple[str, ...] = ()
    provenance: dict = field(default_factory=dict)
    micro_class: str = ""

    @property
    def area_m2(self) -> float:
        return abs(self.signed_area_mm2) / 1_000_000

    @property
    def perimeter_m(self) -> float:
        return self.perimeter_mm / 1000

    @property
    def bbox_mm(self) -> tuple[float, float, float, float]:
        xs = [p[0] for p in self.polygon_mm]
        ys = [p[1] for p in self.polygon_mm]
        return (min(xs), min(ys), max(xs), max(ys))

    @property
    def releasable(self) -> bool:
        """Always False in this engine, on purpose.

        A diagnostic face must not become the measurement basis by accident.
        Migration is explicit: E31A_CANDIDATE -> independently validated ->
        PHYSICAL_SPACE_GEOMETRY_ACCEPTED -> quantity engines may consume it.
        """
        return False

    def record(self) -> dict:
        return {"face_id": self.face_id, "component_id": self.component_id,
                "status": self.status, "kind": self.kind,
                "orientation": self.orientation,
                "area_m2": round(self.area_m2, 3),
                "perimeter_m": round(self.perimeter_m, 2),
                "half_edges": len(self.half_edge_ids),
                "boundary_half_edges": list(self.half_edge_ids),
                "source_wall_edge_ids": list(self.source_wall_edge_ids),
                "topology_boundary_candidate_ids": list(
                    self.topology_boundary_candidate_ids),
                "holes": list(self.hole_face_ids),
                "geometry_confidence": self.geometry_confidence,
                "edge_validation_summary": dict(self.edge_validation_summary),
                "blockers": list(self.blockers),
                "micro_class": self.micro_class,
                "releasable": self.releasable,
                "provenance": dict(self.provenance)}


@dataclass
class PlanarResult:
    half_edges: dict = field(default_factory=dict)
    faces: list = field(default_factory=list)
    unclosed_walks: list = field(default_factory=list)
    components: dict = field(default_factory=dict)

    def bounded(self) -> list[Face]:
        return [f for f in self.faces if f.kind == BOUNDED]

    def by_component(self) -> dict:
        out: dict = {}
        for f in self.faces:
            out.setdefault(f.component_id, []).append(f)
        return out

    def health(self) -> dict:
        return {
            "half_edges": len(self.half_edges),
            "faces": len(self.faces),
            "bounded_faces": len(self.bounded()),
            "unbounded_faces": sum(1 for f in self.faces
                                   if f.kind == UNBOUNDED),
            "unbounded_unresolved": sum(1 for f in self.faces
                                        if f.kind == UNBOUNDED_UNRESOLVED),
            "by_status": dict(Counter(f.status for f in self.faces)),
            "by_orientation": dict(Counter(f.orientation for f in self.faces)),
            "unclosed_walks": len(self.unclosed_walks),
            "faces_with_holes": sum(1 for f in self.faces if f.hole_face_ids),
            "micro_faces": sum(1 for f in self.faces if f.micro_class),
            "total_bounded_area_m2": round(
                sum(f.area_m2 for f in self.bounded()), 3),
        }


def _point_of(edge, at: float) -> tuple[float, float]:
    return ((at, edge.centreline_mm) if edge.axis == "H"
            else (edge.centreline_mm, at))


def build_half_edges(noded) -> dict:
    """Two directed half-edges per wall edge, linked by `next` around nodes.

    `next(h)` is the outgoing half-edge immediately CLOCKWISE from `twin(h)` at
    h's destination. That single rule is what turns a set of edges into a set
    of faces, and getting it wrong produces walks that wander the graph instead
    of closing.
    """
    node_at: dict[tuple, str] = {}
    for n in noded.nodes:
        node_at[(round(n.x_mm, 1), round(n.y_mm, 1))] = n.node_id

    def node_for(pt):
        key = (round(pt[0], 1), round(pt[1], 1))
        if key in node_at:
            return node_at[key]
        # Nearest node within a tolerance; a half-edge whose end is not a node
        # cannot participate in a face walk and is reported, never invented.
        best, bd = None, 1e18
        for n in noded.nodes:
            d = math.hypot(n.x_mm - pt[0], n.y_mm - pt[1])
            if d < bd:
                best, bd = n.node_id, d
        return best if bd <= 200.0 else ""

    hes: dict[str, HalfEdge] = {}
    for e in noded.edges:
        lo, hi = min(e.start_mm, e.end_mm), max(e.start_mm, e.end_mm)
        a, b = _point_of(e, lo), _point_of(e, hi)
        na, nb = node_for(a), node_for(b)
        if not na or not nb or na == nb:
            continue
        fid, rid = f"HE-{e.edge_id}-F", f"HE-{e.edge_id}-R"
        hes[fid] = HalfEdge(fid, e.edge_id, na, nb, a[0], a[1], b[0], b[1],
                            twin_id=rid)
        hes[rid] = HalfEdge(rid, e.edge_id, nb, na, b[0], b[1], a[0], a[1],
                            twin_id=fid)

    # Outgoing half-edges at each node, sorted by direction.
    out_at: dict[str, list] = {}
    for h in hes.values():
        out_at.setdefault(h.origin_node, []).append(h.half_edge_id)
    for nid in out_at:
        out_at[nid].sort(key=lambda hid: hes[hid].angle)

    linked: dict[str, HalfEdge] = {}
    for h in hes.values():
        ring = out_at.get(h.target_node, [])
        twin = h.twin_id
        if twin not in ring or len(ring) == 0:
            linked[h.half_edge_id] = h
            continue
        i = ring.index(twin)
        # Clockwise from twin = the PREVIOUS entry in an angle-ascending ring.
        nxt = ring[(i - 1) % len(ring)]
        linked[h.half_edge_id] = HalfEdge(
            h.half_edge_id, h.source_edge_id, h.origin_node, h.target_node,
            h.x0_mm, h.y0_mm, h.x1_mm, h.y1_mm, twin_id=h.twin_id, next_id=nxt)
    return linked


def _signed_area(poly) -> float:
    s = 0.0
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        s += x0 * y1 - x1 * y0
    return s / 2.0


def walk_faces(half_edges: dict, *, component_of=None,
               edge_status=None, max_steps: int = 20000) -> PlanarResult:
    """Follow `next` until it returns to the start. Each cycle is one face.

    A walk that exceeds `max_steps` or leaves the `next` chain is recorded as
    an UNCLOSED WALK. It is never closed by joining its ends: a face invented
    that way would bound a room the building does not have.
    """
    res = PlanarResult(half_edges=half_edges)
    seen: set = set()
    n = 0
    for start in sorted(half_edges):
        if start in seen:
            continue
        walk, cur, steps = [], start, 0
        ok = True
        while True:
            if cur in walk:
                if cur != start:
                    ok = False
                break
            walk.append(cur)
            seen.add(cur)
            nxt = half_edges[cur].next_id
            steps += 1
            if not nxt or steps > max_steps:
                ok = False
                break
            if nxt == start:
                break
            cur = nxt
        if not ok or len(walk) < 3:
            res.unclosed_walks.append({
                "started_at": start, "half_edges": len(walk),
                "why": ("the next-chain did not return to its start, so this "
                        "boundary does not close. It is NOT joined up: a face "
                        "invented that way bounds a room the building has not "
                        "got")})
            continue

        poly = tuple((half_edges[h].x0_mm, half_edges[h].y0_mm) for h in walk)
        area = _signed_area(list(poly))
        per = sum(half_edges[h].length_mm for h in walk)
        src = tuple(sorted({half_edges[h].source_edge_id for h in walk}))
        comp = ""
        if component_of:
            comps = {component_of.get(half_edges[h].source_edge_id, "")
                     for h in walk}
            comp = sorted(c for c in comps if c)[0] if comps else ""
        orient = (ORIENT_DEGENERATE if abs(area) < 1.0
                  else ORIENT_CCW if area > 0 else ORIENT_CW)
        n += 1
        summary = {}
        if edge_status:
            summary = dict(Counter(edge_status.get(s, "UNKNOWN") for s in src))
        res.faces.append(Face(
            face_id=f"FACE-{n:04d}", component_id=comp,
            half_edge_ids=tuple(walk), polygon_mm=poly,
            signed_area_mm2=area, perimeter_mm=per, orientation=orient,
            kind=BOUNDED, source_wall_edge_ids=src,
            edge_validation_summary=summary))
    return res


def resolve_unbounded(res: PlanarResult) -> PlanarResult:
    """Mark each component's outer walk, from ORIENTATION — not from size.

    The convention is fixed by construction, not by counting: with
    `next` = clockwise-from-twin, an interior face is traversed
    COUNTERCLOCKWISE (positive signed area) and the unbounded walk CLOCKWISE
    (negative). Verified on a two-room fixture where the answer is unambiguous
    because the outer walk's area equals the sum of the two interiors, and
    asserted by a test so the convention cannot drift.

    DO NOT ASSUME THE LARGEST FACE IS THE EXTERIOR. On a plan with a courtyard
    the largest bounded face can rival its own outer walk, and a first attempt
    here used "the minority orientation in this component" — which read a
    984 m² outer walk as a room because that component happened to hold more
    clockwise walks than counterclockwise ones. Counting is not a convention.

    A component with no negative-area walk, or with more than one, reports
    UNBOUNDED_FACE_UNRESOLVED rather than guessing.
    """
    # Group faces into planar components from the graph itself: two faces
    # sharing a wall edge are on the same component. Relying on a
    # caller-supplied map meant that with none supplied every face on the sheet
    # landed in one group, and two separate buildings then had two clockwise
    # walks between them and neither could name its exterior.
    parent: dict[str, str] = {f.face_id: f.face_id for f in res.faces}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    owner: dict[str, str] = {}
    for f in res.faces:
        for e in f.source_wall_edge_ids:
            if e in owner:
                ra, rb = find(owner[e]), find(f.face_id)
                if ra != rb:
                    parent[rb] = ra
            else:
                owner[e] = f.face_id
    groups: dict[str, list] = {}
    for f in res.faces:
        groups.setdefault(find(f.face_id), []).append(f)

    out: list[Face] = []
    for root, faces in groups.items():
        comp = faces[0].component_id or root
        outer = [f for f in faces if f.orientation == ORIENT_CW]
        if len(outer) != 1:
            why = ("no clockwise walk, so this component has no identifiable "
                   "exterior" if not outer else
                   f"{len(outer)} clockwise walks, so exactly one exterior "
                   "cannot be identified")
            for f in faces:
                out.append(Face(**{**f.__dict__, "component_id": comp,
                                   "kind": UNBOUNDED_UNRESOLVED,
                                   "blockers": f.blockers + (why,)}))
            continue
        outer_id = outer[0].face_id
        for f in faces:
            out.append(Face(**{**f.__dict__,
                               "component_id": comp,
                               "kind": UNBOUNDED if f.face_id == outer_id
                               else BOUNDED}))
    res.faces = out
    return res


def _contains(outer: Face, inner: Face) -> bool:
    """Is `inner`'s first vertex inside `outer`? Ray casting, no tolerance."""
    x, y = inner.polygon_mm[0]
    poly = outer.polygon_mm
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y):
            xt = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < xt:
                inside = not inside
    return inside


def attach_holes(res: PlanarResult) -> PlanarResult:
    """A bounded face fully inside another is that face's hole.

    A shaft inside a room is a hole, not a separate room, and a face that
    reports its own area without subtracting a shaft over-measures the floor.
    """
    bounded = res.bounded()
    holes: dict[str, list] = {}
    for inner in bounded:
        for outer in bounded:
            if inner.face_id == outer.face_id:
                continue
            if outer.area_m2 <= inner.area_m2:
                continue
            if _contains(outer, inner):
                holes.setdefault(outer.face_id, []).append(inner.face_id)
    if holes:
        res.faces = [
            Face(**{**f.__dict__,
                    "hole_face_ids": tuple(sorted(holes.get(f.face_id, ())))})
            for f in res.faces]
    return res
