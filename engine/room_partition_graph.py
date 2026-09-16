"""Rooms found by geometry first, and named afterwards.

Every round so far started from a label: find a room stamp, flood outwards
from it, see what closes. That is backwards, and §11 says so:

    DERIVE SUPPORTED BOUNDED PHYSICAL-SPACE CANDIDATES FROM GEOMETRY FIRST.
    THEN ATTACH SEMANTIC IDENTITY.

A room whose name is stored in an SHX font this decoder cannot read is
still a room. A store cupboard nobody labelled is still a bounded physical
space. Requiring a readable stamp made the measurement hostage to the text
layer, and on P7757 sixteen of thirty-three identities are unreadable.

So the order is now:

    the region's own supported wall bands, plus the portals that earned the
    right to close something, are assembled into ONE local arrangement;
    its bounded faces ARE the physical-space candidates;
    the frozen enclosure measures each one from a point inside it;
    identity is attached last, and its absence costs no geometry.

WHAT IS NOT A SPACE

A face lying entirely within the profile's own wall band is the INSIDE OF
A WALL — the material, not a space. That is not a room-size prior: it is
the same paired-face band that defined what a wall is in the first place,
used for the one thing it was measured for.

MULTIPLE LABELS IN ONE FACE ARE NOT MULTIPLE ROOMS (§8)

If two identities sit inside one face with no supported partition between
them, the honest answer is ONE PHYSICAL SPACE with FUNCTIONAL ZONES. It is
not a licence to manufacture a wall between them, and it is not a reason
to throw one identity away.

THE THREE TOPOLOGIES STAY APART (§6)

Material, room partition and navigability are asked separately, through
the frozen `space_topologies` model. A door closes a room boundary with
ZERO material across it, and a doorless opening resolves neither relation
(§7) — it stays ROOM_PARTITION_UNRESOLVED, which blocks release and
invents nothing.
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from engine import cad_openings as op
from engine import cad_profile as cprofile
from engine import space_enclosure as enc
from engine import space_topologies as topo
from engine.boundary_match import VectorCandidate
from engine.evidence_tiers import PORTAL_DRAWING_VALIDATED, PORTAL_UNVALIDATED
from engine.space_objects import SRC_VECTOR_OPENING_JAMB

GRAPH = "REGION_LOCAL_ROOM_PARTITION_GRAPH_V1"

# A face no wider than the wall band this engine already measured is the
# inside of a wall, not a space. The constant is the profile's, unchanged.
MATERIAL_FACE_MAX_MM = cprofile.MAX_WALL_THICKNESS_MM

# How near an opening must lie to a face's boundary to be ON it. The
# opening classifier's own correspondence reach.
ON_BOUNDARY_MM = op.JAMB_REACH_MM

MATERIAL_FACE = "WALL_MATERIAL_OR_DETAIL_FACE"
SPACE_FACE = "BOUNDED_PHYSICAL_SPACE_CANDIDATE"


@dataclass(frozen=True)
class Zone:
    """One functional zone inside a physical space. NOT a separate room."""

    zone_id: str
    identity: object
    label_observations: tuple

    def record(self) -> dict:
        return {"zone_id": self.zone_id,
                "labels": list(self.label_observations),
                "reconciled_concept": (self.identity.normalized_identity
                                       if self.identity else ""),
                "identity_status": (self.identity.identity_status
                                    if self.identity else ""),
                "this_is_not": ("a separate physical space. No partition "
                                "was drawn between these zones and none "
                                "was manufactured")}


@dataclass(frozen=True)
class SpaceNode:
    """One bounded physical space, before anything is known about its name."""

    node_id: str
    region_id: str
    seed_mm: tuple
    face_wkt: str
    enclosure: object
    face_kind: str = SPACE_FACE
    boundary_openings: tuple = ()
    recovered_on_boundary: tuple = ()
    zones: tuple = ()
    identity: object = None

    @property
    def is_complete(self) -> bool:
        return bool(self.enclosure and self.enclosure.is_complete)

    def record(self) -> dict:
        return {"node_id": self.node_id, "drawing_region_id": self.region_id,
                "face_kind": self.face_kind,
                "seed_mm": [round(v, 1) for v in self.seed_mm],
                "complete": self.is_complete,
                "boundary_openings": list(self.boundary_openings),
                "recovered_spans_on_this_boundary": list(
                    self.recovered_on_boundary),
                "functional_zones": [z.record() for z in self.zones]}


@dataclass
class GraphReport:
    region_id: str = ""
    spaces: list = field(default_factory=list)
    material_faces: int = 0
    relations: list = field(default_factory=list)
    open_plan_connections: list = field(default_factory=list)
    portal_boundaries: list = field(default_factory=list)
    closures: list = field(default_factory=list)
    recovered: list = field(default_factory=list)
    quantities: dict = field(default_factory=dict)
    notes: dict = field(default_factory=dict)

    def counts(self) -> dict:
        rel = [r["ROOM_PARTITION_TOPOLOGY"] for r in self.relations]
        return {
            "graph_cycles": len(self.spaces) + self.material_faces,
            "physical_space_candidates": len(self.spaces),
            "wall_material_faces": self.material_faces,
            "portal_partition_boundaries": len(self.portal_boundaries),
            "recovered_partition_lines": len(self.recovered),
            "open_plan_connections": len(self.open_plan_connections),
            "functional_zone_groups": sum(1 for s in self.spaces
                                          if len(s.zones) > 1),
            "relations": len(self.relations),
            "relation_counts": dict(Counter(
                r["ROOM_PARTITION_RELATION"] for r in rel)),
        }

    def record(self, *, limit: int = 40) -> dict:
        return {
            "graph": GRAPH,
            "ROOM_PARTITION_GRAPH_HASH": graph_hash(),
            "drawing_region_id": self.region_id,
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "spaces": [s.record() for s in self.spaces[:limit]],
            "relations": self.relations[:limit],
            "open_plan_connections": self.open_plan_connections[:limit],
            "portal_partition_boundaries": [
                b.record() for b in self.portal_boundaries[:limit]],
            "order": ("geometry first, identity afterwards. A physical "
                      "space does not need a readable label to exist"),
            "notes": dict(self.notes),
        }


def frozen_parameters() -> dict:
    return {
        "GRAPH": GRAPH,
        "MATERIAL_FACE_MAX_MM": MATERIAL_FACE_MAX_MM,
        "ON_BOUNDARY_MM": ON_BOUNDARY_MM,
        "why": {
            "MATERIAL_FACE_MAX_MM": (
                "the profile's own maximum wall thickness, compared "
                "against the face's MEAN THICKNESS (twice area over "
                "perimeter). A face no thicker than that is the inside of "
                "a wall. This is the material model, not a room-size "
                "prior — no space is rejected for being small in AREA"),
            "ON_BOUNDARY_MM": (
                "the opening classifier's correspondence reach, unchanged"),
            "no_seed_required": (
                "faces come from the arrangement. A label localises and "
                "names; it is never a condition of physical existence"),
        },
    }


def graph_hash() -> str:
    parts = [GRAPH, str(MATERIAL_FACE_MAX_MM), str(ON_BOUNDARY_MM),
             MATERIAL_FACE, SPACE_FACE, topo.ROOM_PARTITION_TOPOLOGY,
             topo.REL_ONE_SPACE, topo.REL_TWO_SPACES, topo.REL_UNRESOLVED]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------------- the closures

def closure_candidates(openings, host_status) -> list:
    """Lines that close a validated opening — with ZERO material across it.

    One line per wall face, because a room on either side is bounded by the
    face nearest it. The object id says PORTAL so no downstream stage can
    mistake this for drawn material, and the source type is the opening
    jamb tier the ontology already had.
    """
    out = []
    for o in openings:
        if not o.may_close_boundary:
            continue
        if host_status.get(o.opening_id) != "HOST_ESTABLISHED":
            continue
        faces = o.wall_faces_mm or (o.fixed_mm,)
        for i, f in enumerate(faces):
            out.append(VectorCandidate(
                object_id=f"PORTAL-{o.opening_id}-F{i}",
                axis=o.axis, fixed_mm=f,
                start_mm=o.start_mm, end_mm=o.end_mm,
                source_type=SRC_VECTOR_OPENING_JAMB,
                validation_class="ESTABLISHED"))
    return out


def _faces(candidates):
    """The bounded faces the lines enclose — the local arrangement."""
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union

    segs = []
    for c in candidates:
        lo, hi = sorted((c.start_mm, c.end_mm))
        if hi - lo <= 0:
            continue
        if c.axis == "H":
            segs.append(LineString([(lo, c.fixed_mm), (hi, c.fixed_mm)]))
        elif c.axis == "V":
            segs.append(LineString([(c.fixed_mm, lo), (c.fixed_mm, hi)]))
    if not segs:
        return []
    return list(polygonize(unary_union(segs)))


def _mean_thickness_mm(face) -> float:
    """Twice area over perimeter — how thick this face is, on average.

    A bounding box will not do. The ring of a perimeter wall has a bbox the
    size of the whole building and is still 200 mm of blockwork; this
    measure reads it as 200 mm, reads a 200 x 900 door cavity as 163 mm,
    and reads a 5 x 4 m room as 2.2 m.
    """
    per = face.length
    return 0.0 if per <= 0 else 2.0 * face.area / per


def _is_material(face) -> bool:
    """Is this face the inside of a wall rather than a space?"""
    return _mean_thickness_mm(face) <= MATERIAL_FACE_MAX_MM


@dataclass(frozen=True)
class Anchor:
    """A point the geometry itself says is inside something bounded."""

    x: float
    y: float
    semantic_class: str = "GEOMETRIC_FACE_NO_LABEL"


def interior_anchors(candidates) -> list:
    """Points inside the bounded faces, with no label involved.

    §11, taken to its conclusion. The boundary authority asks "does
    removing this ring leave a room unenclosed", and a room used to mean a
    label. On a drawing whose stamps this decoder cannot read that made the
    question unanswerable and the whole region unmeasurable.

    The faces of the arrangement answer it without a single string. This is
    used ONLY where a region carries no readable room observation at all —
    and it can release nothing by itself, because a face with no label can
    never be a PHYSICAL_ROOM_CANDIDATE.
    """
    out = []
    for f in _faces(candidates):
        if _is_material(f):
            continue
        pt = f.representative_point()
        out.append(Anchor(pt.x, pt.y))
    return out


def _line_on_boundary(face, cand) -> bool:
    """Does this candidate line lie ON this face's boundary?

    Asked of the GEOMETRY rather than read off the enclosure's edge
    attribution. The frozen enclosure names one drawn piece per side — the
    one covering most of it — which is the right answer for provenance and
    the wrong one for "did a recovered span hold this room shut".
    """
    from shapely.geometry import LineString

    lo, hi = sorted((cand.start_mm, cand.end_mm))
    if hi - lo <= 0:
        return False
    if cand.axis == "H":
        line = LineString([(lo, cand.fixed_mm), (hi, cand.fixed_mm)])
    elif cand.axis == "V":
        line = LineString([(cand.fixed_mm, lo), (cand.fixed_mm, hi)])
    else:
        return False
    return face.exterior.distance(line) <= ON_BOUNDARY_MM


def _on_boundary(face, o) -> bool:
    """Does this opening lie on this face's boundary?"""
    from shapely.geometry import LineString

    if o.axis == "H":
        line = LineString([(o.start_mm, o.fixed_mm), (o.end_mm, o.fixed_mm)])
    else:
        line = LineString([(o.fixed_mm, o.start_mm), (o.fixed_mm, o.end_mm)])
    faces = o.wall_faces_mm or (o.fixed_mm,)
    for f in faces:
        if o.axis == "H":
            line2 = LineString([(o.start_mm, f), (o.end_mm, f)])
        else:
            line2 = LineString([(f, o.start_mm), (f, o.end_mm)])
        if face.exterior.distance(line2) <= ON_BOUNDARY_MM:
            return True
    return face.exterior.distance(line) <= ON_BOUNDARY_MM


def _portal_boundary(o, node_ids) -> topo.PortalPartitionBoundary:
    grade = (PORTAL_DRAWING_VALIDATED if o.may_partition_rooms
             else PORTAL_UNVALIDATED)
    return topo.PortalPartitionBoundary(
        boundary_id=f"PPB-{o.opening_id}", portal_id=o.opening_id,
        axis=o.axis, fixed_mm=o.fixed_mm, start_mm=o.start_mm,
        end_mm=o.end_mm,
        host_wall_band_id=(o.host_bands[0] if o.host_bands else ""),
        evidence_grade=grade,
        why=(f"{o.opening_class} on {o.grade}. It closes the room boundary "
             "across the opening with ZERO material"))


def _shared_length_mm(face_wkt: str, o) -> float:
    """How much of THIS opening actually lies on THIS space's boundary.

    An opening's full width is not its contribution to one room: a long
    interruption may run past a small room and touch only part of it. A
    first version summed the whole width, and on P7757 that produced a
    5.5 m² space whose openings totalled 11.05 m against a 9.4 m
    perimeter — more opening than boundary, which is not a measurement.
    """
    from shapely.geometry import LineString
    from shapely.wkt import loads

    try:
        face = loads(face_wkt)
    except Exception:       # noqa: BLE001
        return 0.0
    best = 0.0
    for f in (o.wall_faces_mm or (o.fixed_mm,)):
        if o.axis == "H":
            line = LineString([(o.start_mm, f), (o.end_mm, f)])
        else:
            line = LineString([(f, o.start_mm), (f, o.end_mm)])
        shared = line.intersection(
            face.exterior.buffer(ON_BOUNDARY_MM))
        best = max(best, getattr(shared, "length", 0.0))
    return min(best, o.opening_length_mm)


def _quantities(node, openings_on_boundary, recovered_by_id=None) -> dict:
    """§10, kept apart rather than collapsed into one perimeter number."""
    e = node.enclosure
    boundary_mm = (0.0 if not e or e.perimeter_m is None
                   else e.perimeter_m * 1000)
    shared = {o.opening_id: _shared_length_mm(node.face_wkt, o)
              for o in openings_on_boundary}
    opening_mm = min(sum(shared.values()), boundary_mm)
    # A side held shut by a RECOVERED span is a side nobody drew. It is
    # boundary, and it is not measurable material — reporting it inside
    # MATERIAL_PRESENT_LENGTH would be the silent BOQ creation §6 exists to
    # stop.
    rec = recovered_by_id or {}
    recovered_mm = 0.0
    for oid in node.recovered_on_boundary:
        cand = rec.get(oid)
        if cand is not None:
            recovered_mm += abs(cand.end_mm - cand.start_mm)
    recovered_mm = min(recovered_mm, max(0.0, boundary_mm - opening_mm))
    # HOST_WALL_GROSS_LENGTH may include the opening span ONLY where the
    # host wall's continuation past the opening is independently
    # established — which is exactly what a THROUGH interruption with named
    # flanking bands establishes, and what a single-face gap does not.
    gross_established = [
        o for o in openings_on_boundary
        if op.E_THROUGH_INTERRUPTION in o.evidence and len(o.host_bands) >= 2]
    return {
        "SPACE_BOUNDARY_LENGTH_MM": round(boundary_mm, 1),
        "OPENING_LENGTH_MM": round(opening_mm, 1),
        "MATERIAL_PRESENT_LENGTH_MM": round(max(0.0,
                                                boundary_mm - opening_mm), 1),
        "RECOVERED_BOUNDARY_LENGTH_MM": round(recovered_mm, 1),
        "MATERIAL_AUTHORITY_ESTABLISHED_LENGTH_MM": round(
            max(0.0, boundary_mm - opening_mm - recovered_mm), 1),
        "HOST_WALL_GROSS_LENGTH_MM": round(
            sum(shared[o.opening_id] for o in gross_established), 1),
        "HOST_WALL_GROSS_ESTABLISHED_FOR": len(gross_established),
        "HOST_WALL_GROSS_NOT_ESTABLISHED_FOR": (
            len(openings_on_boundary) - len(gross_established)),
        "never": ("the room polygon's perimeter is NOT the material wall "
                  "length. Material stops at every opening, it is absent "
                  "along every recovered span, and both differences are "
                  "stated rather than assumed"),
    }


def build(*, region_id, candidates, openings=(), host_status=None,
          identity_groups=(), extent=None, recovered=()) -> GraphReport:
    """Assemble ONE region's room-partition topology.

    `candidates` are that region's room-boundary-eligible wall bands.
    `openings` are its opening hypotheses, `host_status` the matcher's
    verdict per opening. Nothing from another region may appear in either.
    """
    rep = GraphReport(region_id=region_id)
    status = dict(host_status or {})
    closures = closure_candidates(openings, status)
    rep.closures = closures
    # ROUND 5. Recovered partition spans enter the arrangement exactly like
    # drawn ones, and their ids say RECOVERED so nothing downstream can
    # mistake an inference for a line somebody drew. What they may DO is
    # decided by the authorities that travel with them.
    rep.recovered = list(recovered)
    arrangement = list(candidates) + closures + list(recovered)

    faces = _faces(arrangement)
    closing = [o for o in openings
               if o.may_close_boundary
               and status.get(o.opening_id) == "HOST_ESTABLISHED"]

    space_faces = []
    for f in faces:
        if _is_material(f):
            rep.material_faces += 1
            continue
        space_faces.append(f)

    on_face = defaultdict(list)
    nodes = []
    for n, f in enumerate(sorted(space_faces,
                                 key=lambda g: (-g.bounds[3], g.bounds[0])),
                          1):
        pt = f.representative_point()
        node_id = f"PS-{region_id}-{n:03d}"
        box = f.bounds
        pad = enc.NEIGHBOURHOOD_MARGIN_MM
        e = enc.enclose(node_id, (pt.x, pt.y), arrangement,
                        extent=(box[0] - pad, box[1] - pad,
                                box[2] + pad, box[3] + pad),
                        enclosure_id=f"LSE-{node_id}")
        mine = [o for o in closing if _on_boundary(f, o)]
        for o in mine:
            on_face[o.opening_id].append(node_id)
        mine_rec = [c.object_id for c in recovered
                    if _line_on_boundary(f, c)]
        nodes.append(SpaceNode(
            node_id=node_id, region_id=region_id, seed_mm=(pt.x, pt.y),
            face_wkt=f.wkt, enclosure=e,
            boundary_openings=tuple(o.opening_id for o in mine),
            recovered_on_boundary=tuple(mine_rec)))

    # ---- identity, attached LAST (§11) ---------------------------------
    from shapely.geometry import Point
    from shapely.wkt import loads

    shapes = {}
    for node in nodes:
        try:
            shapes[node.node_id] = loads(node.face_wkt)
        except Exception:      # noqa: BLE001
            continue

    out = []
    for node in nodes:
        shape = shapes.get(node.node_id)
        inside = [g for g in identity_groups
                  if shape is not None and shape.contains(Point(g.x, g.y))]
        zones = tuple(Zone(zone_id=f"{node.node_id}-Z{i}", identity=g,
                           label_observations=tuple(
                               o.text for o in g.observations))
                      for i, g in enumerate(inside, 1))
        out.append(SpaceNode(**{**node.__dict__, "zones": zones,
                                "identity": (inside[0] if len(inside) == 1
                                             else None)}))
    rep.spaces = out

    # ---- §8: several identities in one face is ONE space with zones ----
    for node in rep.spaces:
        if len(node.zones) > 1:
            rep.open_plan_connections.append({
                "space_id": node.node_id,
                "drawing_region_id": region_id,
                "opening_class": op.OPEN_PLAN_CONNECTION,
                "functional_zones": [z.record() for z in node.zones],
                "ROOM_PARTITION_RELATION": topo.REL_ONE_SPACE,
                "basis": ("these identities share ONE geometric face and no "
                          "supported partition lies between them. The "
                          "drawing says one space; the labels say it is "
                          "used for several things"),
                "what_was_not_done": (
                    "no wall and no portal was manufactured between them, "
                    "and no identity was discarded"),
            })

    # ---- §6 and §7: the three topologies, per opening ------------------
    for o in closing:
        pair = on_face.get(o.opening_id, [])
        pb = _portal_boundary(o, pair)
        rep.portal_boundaries.append(pb)
        if o.opening_class == op.WINDOW_OPENING:
            rep.relations.append({
                "between": (pair + ["EXTERIOR_OR_UNMEASURED"])[:2],
                "opening_id": o.opening_id,
                "opening_class": o.opening_class,
                topo.MATERIAL_GEOMETRY: {
                    "model": topo.MATERIAL_GEOMETRY, "connected": True,
                    "basis": "no wall material stands across a window",
                    "status": ""},
                topo.NAVIGABLE_FREE_SPACE: {
                    "model": topo.NAVIGABLE_FREE_SPACE, "connected": False,
                    "basis": ("a window is not a passage. §9: it may not "
                              "leak a room polygon to exterior space"),
                    "status": ""},
                topo.ROOM_PARTITION_TOPOLOGY: {
                    "model": topo.ROOM_PARTITION_TOPOLOGY,
                    "ROOM_PARTITION_RELATION": topo.REL_TWO_SPACES,
                    "is_one_space": False, "is_two_spaces": True,
                    "is_resolved": True,
                    "status": topo.PARTITION_RELEASABLE,
                    "basis": ("the room boundary runs across the window. "
                              "Inside stays inside"),
                    "established_by": topo.ESTABLISHES_TWO_SPACES},
                "ROOM_PARTITION_RELATION": topo.REL_TWO_SPACES,
            })
            continue
        a, b = (pair + ["", ""])[:2]
        row = topo.answer_pair(
            a or f"{o.opening_id}-SIDE-A", b or f"{o.opening_id}-SIDE-B",
            portal=(pb if o.may_partition_rooms else None))
        row = dict(row)
        row["opening_id"] = o.opening_id
        row["opening_class"] = o.opening_class
        row["ROOM_PARTITION_RELATION"] = \
            row[topo.ROOM_PARTITION_TOPOLOGY]["ROOM_PARTITION_RELATION"]
        rep.relations.append(row)

    by_id = {o.opening_id: o for o in openings}
    rec_by_id = {c.object_id: c for c in rep.recovered}
    rep.quantities = {
        s.node_id: _quantities(s, [by_id[i] for i in s.boundary_openings
                                   if i in by_id], rec_by_id)
        for s in rep.spaces}

    rep.notes["what_closed_what"] = (
        f"{len(closures)} portal closure line(s) entered this region's "
        "arrangement, each carrying ZERO material. Every other boundary is "
        "a line somebody drew")
    rep.notes["unresolved_is_not_a_lean"] = (
        "a doorless opening leaves the room-partition relation UNRESOLVED. "
        "That blocks release and asserts neither one space nor two")
    return rep
