"""E31E — the global SPACE_BOUNDARY_GRAPH, and faces walked on it.

The per-space interval model proved the concept and could not do more than
that. It walked four sides taken from a bounding box, and a room that fills
67.6% of its box has sides the box invented. So the closure it reported was a
property of the model.

This module builds the real thing:

    MATERIAL_WALL_GRAPH
        + every GEOMETRY-SUPPORTED host-wall opening, as a ZERO-MATERIAL edge
        = SPACE_BOUNDARY_GRAPH

and then runs the SAME face walker over both. The face walker is not touched.
That is the point of the experiment: if normal rooms become bounded faces on
the space graph and stay open on the material graph, the difference is caused
by the INPUT GRAPH, which is the hypothesis. Changing the walker to produce the
expected answer would have destroyed the only evidence available.

WHAT DOES NOT GO IN:

    open-plan semantic boundaries.  A dining zone and a saloon are one physical
                                    space. An edge drawn between them would
                                    create a face the building has not got.
    portals whose GEOMETRY is unresolved.  A door proven to exist by a schedule
                                    entry and a swing symbol has no located
                                    jambs. Its closure line would be invented.
    raster region outlines.         They localise and compare. They never
                                    construct — WSH-01 proves a raster region
                                    can carry the wrong physical identity.

Every edge carries its boundary type, its geometry, its measurement bases, its
source ids, its evidence and its validation status, so a face can say what it
was made of rather than only how big it is.

IDENTITY IS BY ID. A space-boundary edge is joined to its noded split edges
through `pair_id`, never through list position — the positional join that
scored every component against another component's numbers is a repository
rule now, not a memory.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from engine.lengths import LengthSet
from engine.planar import (attach_holes, build_half_edges, resolve_unbounded,
                           walk_faces)
from engine.space_boundary import (GAP_OPEN_PLAN, GEOMETRY_SUFFICIENT,
                                   HOST_WALL_OPENING, PHYSICAL_WALL)
from engine.topology import WallPair
from engine.wall_graph import build
from engine.wall_noding import node_and_split

MATERIAL_WALL_GRAPH = "MATERIAL_WALL_GRAPH"
SPACE_BOUNDARY_GRAPH = "SPACE_BOUNDARY_GRAPH"

GRAPH_TYPES = (MATERIAL_WALL_GRAPH, SPACE_BOUNDARY_GRAPH)

# A virtual closure edge has no thickness because it has no material. Two wall
# faces 2 mm apart would be a very thin wall; zero separation is the honest
# encoding of "there is nothing here".
VIRTUAL_SEPARATION_MM = 0.0

# Why an edge was refused entry to the space graph. Each is reported, never
# silently dropped: the count of refusals is the more interesting number.
REFUSED_GEOMETRY_UNRESOLVED = "PORTAL_GEOMETRY_UNRESOLVED"
REFUSED_OPEN_PLAN = "OPEN_PLAN_SEMANTIC_BOUNDARY_IS_NOT_PHYSICAL_TOPOLOGY"
REFUSED_NO_HOST = "PORTAL_HAS_NO_NAMED_HOST_WALL"


class SpaceGraphError(RuntimeError):
    """An edge was asked to join the space graph without earning it."""


@dataclass(frozen=True)
class SpaceBoundaryEdge:
    """One edge of the space graph, carrying everything a face needs to explain
    itself.

    `edge_id` is the pair id the noded graph will stamp on every split
    fragment, so a face can name its boundary edges by identity.
    """

    edge_id: str
    boundary_type: str
    axis: str
    centreline_mm: float
    start_mm: float
    end_mm: float
    lengths: LengthSet
    separation_mm: float = 0.0
    source_wall_band_ids: tuple[str, ...] = ()
    source_object_ids: tuple[str, ...] = ()
    portal_id: str = ""
    host_wall_band_id: str = ""
    evidence: tuple[str, ...] = ()
    validation_status: str = ""
    # The two drawn faces of the host wall, so the clear-internal engine can
    # name the room-facing one instead of recomputing an offset.
    face_a_mm: float | None = None
    face_b_mm: float | None = None
    face_a_ids: tuple[str, ...] = ()
    face_b_ids: tuple[str, ...] = ()
    geometry_status: str = ""
    existence_status: str = ""
    closure_basis: str = ""
    why: str = ""

    @property
    def length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    @property
    def is_virtual(self) -> bool:
        return self.boundary_type != PHYSICAL_WALL

    def to_pair(self) -> WallPair:
        """The geometric form the graph builder consumes.

        A physical edge keeps its two wall faces. A virtual closure has one
        line and no thickness, because there is nothing there to be thick.
        """
        sep = VIRTUAL_SEPARATION_MM if self.is_virtual else self.separation_mm
        return WallPair(self.edge_id, self.axis,
                        self.centreline_mm - sep / 2,
                        self.centreline_mm + sep / 2,
                        self.start_mm, self.end_mm)

    def record(self) -> dict:
        return {"edge_id": self.edge_id, "boundary_type": self.boundary_type,
                "axis": self.axis,
                "centreline_mm": round(self.centreline_mm, 1),
                "start_mm": round(self.start_mm, 1),
                "end_mm": round(self.end_mm, 1),
                "length_mm": round(self.length_mm, 1),
                "is_virtual": self.is_virtual,
                "separation_mm": round(self.separation_mm, 1),
                "face_a_mm": self.face_a_mm, "face_b_mm": self.face_b_mm,
                "face_a_ids": list(self.face_a_ids),
                "face_b_ids": list(self.face_b_ids),
                "source_wall_band_ids": list(self.source_wall_band_ids),
                "source_object_ids": list(self.source_object_ids),
                "portal_id": self.portal_id,
                "host_wall_band_id": self.host_wall_band_id,
                "evidence": list(self.evidence),
                "validation_status": self.validation_status,
                "geometry_status": self.geometry_status,
                "existence_status": self.existence_status,
                "closure_basis": self.closure_basis,
                **self.lengths.record(), "why": self.why}


def material_edges(bands) -> list[SpaceBoundaryEdge]:
    """Every wall band, as a physical boundary edge.

    A wall is all four lengths at once and they coincide: it encloses, it is
    the gross line, material stands on it, and it contains no opening.
    """
    out = []
    for b in bands:
        if b.wall_face_separation_mm is None:
            continue
        L = abs(b.end_mm - b.start_mm)
        out.append(SpaceBoundaryEdge(
            edge_id=b.wall_band_id, boundary_type=PHYSICAL_WALL, axis=b.axis,
            centreline_mm=b.centreline_mm, start_mm=b.start_mm,
            end_mm=b.end_mm,
            lengths=LengthSet(space_boundary_mm=L, host_wall_gross_mm=L,
                              material_present_mm=L, opening_mm=0.0),
            source_wall_band_ids=(b.wall_band_id,),
            face_a_mm=b.face_a_mm, face_b_mm=b.face_b_mm,
            face_a_ids=tuple(b.face_a_ids), face_b_ids=tuple(b.face_b_ids),
            source_object_ids=tuple(b.source_object_ids),
            evidence=tuple(b.supporting_evidence),
            validation_status=b.validation_status,
            separation_mm=b.wall_face_separation_mm,
            why="a paired wall band: material stands on this line"))
    return out


def portal_edges(portals) -> tuple[list, list]:
    """Geometry-supported openings only, plus the refusals and why.

    Existence is not enough. A boundary edge is a piece of geometry, so the
    gate is PORTAL_GEOMETRY_STATUS: a door the schedule proves exists but whose
    jambs nobody has located does not get a line drawn for it.
    """
    kept, refused = [], []
    for p in portals:
        # Open plan is checked FIRST. It is a statement about what the space
        # IS, and it holds however good the geometry gets — a reader told only
        # "geometry unresolved" would reasonably try to improve the geometry.
        if p.gap_class == GAP_OPEN_PLAN:
            refused.append({"portal_id": p.portal_id,
                            "refused": REFUSED_OPEN_PLAN,
                            "existence_status": p.existence_status,
                            "geometry_status": p.geometry_status,
                            "why": ("an open-plan transition is one physical "
                                    "space. An edge here would create a face "
                                    "the building has not got, and no amount "
                                    "of geometry would make it right")})
            continue
        if p.geometry_status not in GEOMETRY_SUFFICIENT:
            refused.append({"portal_id": p.portal_id,
                            "refused": REFUSED_GEOMETRY_UNRESOLVED,
                            "existence_status": p.existence_status,
                            "geometry_status": p.geometry_status,
                            "why": p.geometry_why})
            continue
        host = p.hosted.host_wall_band_id if p.hosted and p.hosted.has_host else ""
        L = p.span_mm
        kept.append(SpaceBoundaryEdge(
            edge_id=p.portal_id, boundary_type=HOST_WALL_OPENING, axis=p.axis,
            centreline_mm=p.fixed_mm, start_mm=p.start_mm, end_mm=p.end_mm,
            # FOUR FACTS, kept apart. Zero material, a real opening, a valid
            # space closure, and — only with a named host — part of that
            # wall's gross line.
            lengths=LengthSet(space_boundary_mm=L,
                              host_wall_gross_mm=(L if host else None),
                              material_present_mm=0.0, opening_mm=L),
            portal_id=p.portal_id, host_wall_band_id=host,
            evidence=tuple(p.evidence), geometry_status=p.geometry_status,
            existence_status=p.existence_status,
            closure_basis=(p.hosted.closure_basis if p.hosted else ""),
            separation_mm=VIRTUAL_SEPARATION_MM,
            why=("a geometry-supported opening: ZERO material, and the space "
                 "closes across it")))
    return kept, refused


# --------------------------------------------- portals, found WITHOUT a bbox

# A gap this long between two collinear bands is worth examining. Wide,
# because width is EVIDENCE and never a test.
MIN_GLOBAL_GAP_MM = 500.0
MAX_GLOBAL_GAP_MM = 2500.0
# Two bands are on the same wall line within this much.
COLLINEAR_TOL_MM = 60.0
# A swing arc this far from the gap's line is not this gap's swing.
ARC_REACH_MM = 1100.0


def swing_arcs(drawing, *, min_span: float = 500.0,
               max_span: float = 1600.0) -> list[dict]:
    """Door swing arcs, grouped per drawn path.

    A swing is one path, decomposed into several bezier items; measuring items
    individually reads a quarter-arc as a small curve and throws the symbol
    away. AR-00 holds 2,399 curves and only a handful of door-scale paths,
    which is exactly why a swing is SUPPORTING evidence and never a condition:
    sliding doors, pocket doors and open transitions have no arc at all.
    """
    by_path: dict = {}
    for c in drawing.curves:
        by_path.setdefault(c.path_id, []).append(c)
    out = []
    for pid, cs in sorted(by_path.items()):
        x0 = min(c.x0_mm for c in cs)
        x1 = max(c.x1_mm for c in cs)
        y0 = min(c.y0_mm for c in cs)
        y1 = max(c.y1_mm for c in cs)
        span = max(x1 - x0, y1 - y0)
        if min_span <= span <= max_span:
            out.append({"path_id": pid, "span_mm": round(span, 1),
                        "centre_mm": ((x0 + x1) / 2, (y0 + y1) / 2)})
    return out


def global_portals(bands, *, caps=(), arcs=(), component_of=None,
                   closure_basis: str = ""):
    """Gaps between collinear wall bands, found on the WHOLE SHEET.

    The per-space detector walked four sides of a bounding box, so it could
    only ever find doors on the sides a rectangle happens to have — and a room
    that fills 68% of its box has sides the rectangle invented. This one knows
    nothing about rooms. It looks along wall lines.

    Evidence stays in families, as everywhere:

        the two bands terminate facing each other      GEOMETRY
        the span is in the door range                  GEOMETRY
        an end cap at each jamb                        GEOMETRY
        a door swing arc across the gap                SYMBOL
        both jambs lie in one graph component          TOPOLOGY

    and GEOMETRY + SYMBOL is what finally reaches a validated opening geometry
    without the door schedule.
    """
    from engine.space_boundary import classify_gap
    lines: dict = {}
    for b in bands:
        if b.wall_face_separation_mm is None:
            continue
        key = (b.axis, round(b.centreline_mm / COLLINEAR_TOL_MM))
        lines.setdefault(key, []).append(b)

    out = []
    for (axis, _), group in sorted(lines.items(), key=lambda kv: str(kv[0])):
        group = sorted(group, key=lambda b: b.start_mm)
        for a, b in zip(group, group[1:]):
            lo, hi = a.end_mm, b.start_mm
            gap = hi - lo
            if not (MIN_GLOBAL_GAP_MM <= gap <= MAX_GLOBAL_GAP_MM):
                continue
            fixed = (a.centreline_mm + b.centreline_mm) / 2
            # Arcs near THIS wall line, projected onto it.
            near = [c["centre_mm"][0] if axis == "H" else c["centre_mm"][1]
                    for c in arcs
                    if abs((c["centre_mm"][1] if axis == "H"
                            else c["centre_mm"][0]) - fixed) <= ARC_REACH_MM]
            same_component = False
            if component_of:
                ca = component_of.get(a.wall_band_id)
                cb = component_of.get(b.wall_band_id)
                same_component = bool(ca) and ca == cb
            p = classify_gap(
                f"G{axis}{int(fixed)}", "line", axis, fixed, lo, hi,
                caps=caps, bands_face_each_other=True,
                other_sides_complete=same_component, swing_arcs=near,
                host_wall_band_id=a.wall_band_id,
                closure_basis=closure_basis)
            out.append(p)
    return out


def build_space_boundary_graph(bands, portals):
    """MATERIAL edges + supported portal closures, noded into one graph.

    Returns the noded graph, the edge index (by id), and the refusals.
    """
    mat = material_edges(bands)
    virt, refused = portal_edges(portals)
    edges = mat + virt
    index = {e.edge_id: e for e in edges}
    if len(index) != len(edges):
        raise SpaceGraphError(
            "two space-boundary edges share an id. Identity is the join key "
            "for every face in this graph, so a duplicate id would silently "
            "attribute one edge's material to another")
    pairs = [e.to_pair() for e in edges]
    noded = node_and_split(build(pairs))
    return noded, index, refused


# --------------------------------------------------------------- the faces

# What a face is allowed to claim about itself. Never a room name.
GEOMETRY_CLOSED = "SPACE_FACE_CLOSED"
GEOMETRY_DEPENDS_ON_VIRTUAL = "SPACE_FACE_CLOSED_VIA_PORTAL_CLOSURE"
GEOMETRY_MICRO = "SPACE_FACE_BELOW_MICRO_THRESHOLD"


@dataclass(frozen=True)
class SpaceFace:
    """A polygon the graph produced, with no idea what room it is.

    §5 — E31A generates GEOMETRY FIRST. Attaching BATHROOM or BEDROOM during
    face creation would let a label decide where a boundary runs, which is the
    same failure as seeding a face from a raster region with a different
    physical identity. Identity is established afterwards, in
    `engine.space_correspondence`, and it can disagree.
    """

    space_face_id: str
    graph_type: str
    topology_run_id: str
    # The GRAPH component (GC-) and the PLANAR component (PC-) are different
    # objects. §26 found a FACE id sitting in a component field; each now has
    # its own namespace and its own column.
    component_id: str
    polygon_mm: tuple
    area_m2: float
    perimeter_m: float
    planar_component_id: str = ""
    hole_face_ids: tuple[str, ...] = ()
    boundary_edge_ids: tuple[str, ...] = ()
    # The same edges IN WALK ORDER, one per polygon segment. The sorted set
    # above is for membership; a boundary has to be walked in order or its
    # corners come out meaningless.
    boundary_edges_in_order: tuple[str, ...] = ()
    physical_wall_edge_ids: tuple[str, ...] = ()
    portal_edge_ids: tuple[str, ...] = ()
    material_wall_length_m: float = 0.0
    host_wall_gross_length_m: float | None = None
    opening_length_m: float = 0.0
    space_boundary_length_m: float = 0.0
    geometry_status: str = GEOMETRY_CLOSED
    blockers: tuple[str, ...] = ()
    provenance: dict = field(default_factory=dict)

    @property
    def face_id(self) -> str:
        """The name `engine.face_qa` joins on. One identity, two readers."""
        return self.space_face_id

    @property
    def bbox_mm(self) -> tuple[float, float, float, float]:
        """The containing box, for INDEXING and COMPARISON only.

        Permitted by `engine.bbox`: it localises a search and overlaps against
        a raster region. It never supplies this face's sides, perimeter or
        area — those come from `polygon_mm`, which the graph produced.
        """
        xs = [pt[0] for pt in self.polygon_mm]
        ys = [pt[1] for pt in self.polygon_mm]
        return (min(xs), min(ys), max(xs), max(ys))

    @property
    def releasable(self) -> bool:
        """Still False. A face is geometry; a release needs a signed rule."""
        return False

    def record(self) -> dict:
        return {"space_face_id": self.space_face_id,
                "graph_type": self.graph_type,
                "topology_run_id": self.topology_run_id,
                "component_id": self.component_id or "",
                "planar_component_id": self.planar_component_id,
                "area_m2": round(self.area_m2, 3),
                "perimeter_m": round(self.perimeter_m, 3),
                "holes": list(self.hole_face_ids),
                "boundary_edges": list(self.boundary_edge_ids),
                "boundary_edges_in_order": list(self.boundary_edges_in_order),
                "physical_wall_edges": list(self.physical_wall_edge_ids),
                "portal_edges": list(self.portal_edge_ids),
                "material_wall_length_m": round(self.material_wall_length_m, 3),
                "host_wall_gross_length_m": (
                    None if self.host_wall_gross_length_m is None
                    else round(self.host_wall_gross_length_m, 3)),
                "opening_length_m": round(self.opening_length_m, 3),
                "space_boundary_length_m": round(
                    self.space_boundary_length_m, 3),
                "geometry_status": self.geometry_status,
                "blockers": list(self.blockers),
                "releasable": self.releasable,
                "provenance": dict(self.provenance)}


def walk(noded, index, *, graph_type: str, run_id: str):
    """Run the UNCHANGED face walker, then describe each face by its edges.

    Only the input graph differs between the two runs. Nothing here tunes the
    walker, and nothing here closes a walk that did not close.
    """
    res = attach_holes(resolve_unbounded(walk_faces(
        build_half_edges(noded),
        edge_status={e.edge_id: e.validation_status for e in noded.edges})))
    by_split = {e.edge_id: e for e in noded.edges}
    faces = []
    for i, f in enumerate(sorted(res.bounded(), key=lambda f: -f.area_m2), 1):
        mat = opening = space = 0.0
        host: float | None = 0.0
        phys, ports, ids = [], [], []
        # WALK ORDER, from the half-edge chain the face closed on. The set
        # below is the same edges without order; both are kept because they
        # answer different questions.
        ordered = []
        for hid in f.half_edge_ids:
            he = res.half_edges.get(hid)
            split = by_split.get(he.source_edge_id) if he else None
            owner = index.get(split.pair_id) if split else None
            ordered.append(owner.edge_id if owner else "")
        for sid in f.source_wall_edge_ids:
            split = by_split.get(sid)
            if split is None:
                continue
            # IDENTITY BY ID: the split fragment names its parent pair, and the
            # pair id is the space-boundary edge's own id.
            owner = index.get(split.pair_id)
            if owner is None:
                continue
            ids.append(owner.edge_id)
            L = split.length_mm / 1000
            space += L
            if owner.boundary_type == PHYSICAL_WALL:
                phys.append(owner.edge_id)
                mat += L
                if host is not None:
                    host += L
            else:
                ports.append(owner.edge_id)
                opening += L
                if owner.lengths.host_wall_gross_mm is None:
                    # One unhosted opening makes the whole face's gross line
                    # unestablished. It is NOT zero and NOT the material sum.
                    host = None
                elif host is not None:
                    host += L
        status = (GEOMETRY_DEPENDS_ON_VIRTUAL if ports else GEOMETRY_CLOSED)
        blockers = list(f.blockers)
        if ports:
            blockers.append(
                f"closes across {len(set(ports))} portal closure(s): the "
                "polygon depends on opening geometry, not on wall material "
                "alone")
        faces.append(SpaceFace(
            space_face_id=f"SF-{run_id}-{i:04d}", graph_type=graph_type,
            topology_run_id=run_id, component_id=f.component_id,
            planar_component_id=f.planar_component_id,
            polygon_mm=f.polygon_mm, area_m2=f.area_m2,
            perimeter_m=f.perimeter_m, hole_face_ids=f.hole_face_ids,
            boundary_edge_ids=tuple(sorted(set(ids))),
            boundary_edges_in_order=tuple(ordered),
            physical_wall_edge_ids=tuple(sorted(set(phys))),
            portal_edge_ids=tuple(sorted(set(ports))),
            material_wall_length_m=mat, host_wall_gross_length_m=host,
            opening_length_m=opening, space_boundary_length_m=space,
            geometry_status=status, blockers=tuple(blockers),
            provenance={"walker": "engine.planar (unchanged)",
                        "graph_type": graph_type,
                        "planar_face_id": f.face_id,
                        "raster_used": False}))
    return res, faces


def _point_in(poly, x: float, y: float) -> bool:
    """Ray casting. No tolerance, because a near-miss is not a containment."""
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y):
            xt = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < xt:
                inside = not inside
    return inside


def assign_spaces(faces, regions) -> dict:
    """Which generated face a labelled region falls INSIDE. Not which box it
    overlaps.

    Bounding-box overlap put every room in the villa inside the 989 m2
    whole-building face, because that face's box contains every other box. The
    same bbox error, one level up: a container is not an identity.

    So the test is containment of the region's CENTROID in the face POLYGON,
    and the answer is the SMALLEST containing face — the innermost room rather
    than the building that also contains it. The centroid is raster, and it is
    used exactly as §2 allows: to localise, never to construct. The polygon it
    is tested against was generated before this function ran.
    """
    labelled = [(r["space_id"], r["centroid_mm"]) for r in regions.values()
                if r.get("space_id")]
    # A face that contains two labelled rooms is not either room's face — it is
    # something larger that also contains them, and on this drawing that is the
    # 989 m2 building envelope. The test is topological: no areas are compared,
    # so nothing here can be tuned by the reference answers.
    holds = {f.space_face_id: sum(
        1 for _, (cx, cy) in labelled if _point_in(list(f.polygon_mm), cx, cy))
        for f in faces}
    out: dict = {}
    for sid, (cx, cy) in sorted(labelled):
        hits = [f for f in faces
                if holds[f.space_face_id] == 1
                and _point_in(list(f.polygon_mm), cx, cy)]
        if not hits:
            continue
        out[sid] = min(hits, key=lambda f: f.area_m2).space_face_id
    return out


def containment(faces, regions) -> list[dict]:
    """Per face: which labelled rooms fall inside it, and therefore what it is.

    The single most useful diagnostic once real faces exist. A face holding one
    labelled room is a room polygon; a face holding six is a group of rooms
    whose dividing walls are still missing from extraction; a face holding none
    is either a circulation space nobody labelled or a sliver.
    """
    labelled = [(r["space_id"], r["centroid_mm"]) for r in regions.values()
                if r.get("space_id")]
    out = []
    for f in faces:
        poly = list(f.polygon_mm)
        inside = sorted(sid for sid, (cx, cy) in labelled
                        if _point_in(poly, cx, cy))
        out.append({
            "space_face_id": f.space_face_id, "graph_type": f.graph_type,
            "area_m2": round(f.area_m2, 3),
            "perimeter_m": round(f.perimeter_m, 2),
            "labelled_regions_contained": len(inside),
            "space_ids": inside,
            "portal_edges": len(f.portal_edge_ids),
            "verdict": ("SINGLE_ROOM_CANDIDATE" if len(inside) == 1 else
                        "MULTI_ROOM_FACE_DIVIDING_WALLS_MISSING"
                        if len(inside) > 1 else
                        "NO_LABELLED_ROOM_INSIDE"),
        })
    return sorted(out, key=lambda d: -d["area_m2"])


def portal_over_closure_audit(faces, index, nested=(), *, regions=None,
                              adjacency=None) -> list[dict]:
    """Every portal a multi-space cycle leaned on, and whether it earned it.

    A portal closure is allowed to close a doorway. A FALSE portal does
    something else entirely: it merges two spaces into one cycle, or it
    creates a cycle that has no room behind it. Three of this run's cycles
    close across several portals at once, which is exactly the shape a
    false closure produces — so each one is audited rather than trusted for
    being PROBABLE.

    `removing_it_changes_the_face` is the question that matters. A portal the
    face does not need is a portal whose correctness has not been tested by
    anything.
    """
    klass = {n.space_face_id: n.cycle_class for n in nested}
    holders = {n.space_face_id: n.labelled_space_ids for n in nested}
    adjacency = dict(adjacency or {})
    out = []
    for f in faces:
        cls = klass.get(f.space_face_id, "")
        if not f.portal_edge_ids:
            continue
        spaces = holders.get(f.space_face_id, ())
        for pid in f.portal_edge_ids:
            e = index.get(pid)
            if e is None:
                continue
            expected = adjacency.get(e.portal_id or pid)
            connects = (None if expected is None
                        else bool(set(expected) & set(spaces)))
            out.append({
                "space_face_id": f.space_face_id,
                "cycle_class": cls,
                "portal_id": e.portal_id or pid,
                "edge_id": pid,
                "existence_status": e.existence_status,
                "geometry_status": e.geometry_status,
                "host_wall_band_id": e.host_wall_band_id or "HOST_UNRESOLVED",
                "evidence": list(e.evidence),
                "opening_mm": round(e.lengths.opening_mm or 0.0, 1),
                # Removing ANY single boundary edge opens the walk: a closed
                # cycle has no spare edges. Stated rather than recomputed, so
                # nobody reads a tautology as a test.
                "removing_it_changes_the_face": True,
                "removal_note": ("every edge of a closed cycle is load-"
                                 "bearing, so this alone proves nothing. The "
                                 "informative columns are the two statuses "
                                 "and whether it joins the expected spaces"),
                "labelled_spaces_in_this_face": list(spaces),
                "connects_expected_adjacent_spaces": connects,
                "risk": _portal_risk(cls, e, len(spaces)),
            })
    return out


def _portal_risk(cycle_class: str, edge, label_count: int) -> str:
    """How much this portal is being asked to carry."""
    if cycle_class == "ENCLOSURE_CYCLE" and label_count > 1:
        return ("OVER_CLOSURE_SUSPECT: this closure helps merge "
                f"{label_count} labelled rooms into one cycle")
    if edge.geometry_status == "PORTAL_GEOMETRY_VALIDATED":
        return "GEOMETRY_VALIDATED: an independent symbol or document agrees"
    if not edge.host_wall_band_id:
        return ("HOST_UNRESOLVED: a closure between two unrelated walls is "
                "not a hole in either of them")
    return "GEOMETRY_PROBABLE: correlated families only"


def compare(material_res, material_faces, space_res, space_faces) -> dict:
    """What changed when the doors were closed — the whole experiment.

    The interesting number is not how many faces the space graph has. It is how
    many faces it has that the material graph does not, because those are the
    rooms whose only missing boundary was a doorway.
    """
    m, s = material_res.health(), space_res.health()
    return {
        "material_wall_graph": m,
        "space_boundary_graph": s,
        "bounded_faces_material": m["bounded_faces"],
        "bounded_faces_space": s["bounded_faces"],
        "faces_gained_by_closing_portals": (
            s["bounded_faces"] - m["bounded_faces"]),
        "unclosed_walks_material": m["unclosed_walks"],
        "unclosed_walks_space": s["unclosed_walks"],
        "space_faces_depending_on_a_portal": sum(
            1 for f in space_faces if f.portal_edge_ids),
        "space_faces_from_material_only": sum(
            1 for f in space_faces if not f.portal_edge_ids),
        "faces_by_status_space": dict(Counter(
            f.geometry_status for f in space_faces)),
        "note": ("the face walker is IDENTICAL in both runs. Only the input "
                 "graph differs, which is what makes the difference evidence"),
    }
