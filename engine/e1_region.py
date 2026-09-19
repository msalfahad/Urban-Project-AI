"""E1 — a label inside a polygon does not mean the polygon owns the space.

The first E1 trace bounded six of twenty labels and the framing called
that success. It was not. A room stamp sits wherever the drafter put it,
and the smallest closed face around it can be a stair enclosure, a
cupboard, a face that only exists because a doorway got closed, or the
whole site. So:

    LABEL_SEED_INSIDE_POLYGON  does not imply  POLYGON_OWNS_LABELLED_SPACE

This module decides an OUTCOME for each candidate region, from evidence,
and is allowed to decide that there is no closed polygon. A withheld or
open result is better than a false closed room, because a false closed
room is a quantity somebody will later measure.

Six outcomes, and only the first releases a polygon:

    CLOSED_PHYSICAL_REGION          material boundary closes it
    OPEN_PHYSICAL_REGION            CAD establishes an open connection
    PARTIAL_BOUNDARY_CHAIN          some boundary, not a closed ring
    MULTI_FUNCTION_PHYSICAL_REGION  one region, several functional labels
    NO_UNIQUE_PHYSICAL_REGION       no single region answers to this label
    UNRESOLVED                      the drawing does not settle it

Validation runs before anything is released, and a failure WITHHOLDS. It
never repairs geometry to obtain a closed polygon.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from engine import cad_geometry as cg

MODEL = "A_LABEL_INSIDE_A_POLYGON_DOES_NOT_OWN_IT_V1"

# --- outcomes -------------------------------------------------------------
CLOSED_PHYSICAL_REGION = "CLOSED_PHYSICAL_REGION"
OPEN_PHYSICAL_REGION = "OPEN_PHYSICAL_REGION"
PARTIAL_BOUNDARY_CHAIN = "PARTIAL_BOUNDARY_CHAIN"
MULTI_FUNCTION_PHYSICAL_REGION = "MULTI_FUNCTION_PHYSICAL_REGION"
NO_UNIQUE_PHYSICAL_REGION = "NO_UNIQUE_PHYSICAL_REGION"
UNRESOLVED = "UNRESOLVED"
OUTCOMES = (CLOSED_PHYSICAL_REGION, OPEN_PHYSICAL_REGION,
            PARTIAL_BOUNDARY_CHAIN, MULTI_FUNCTION_PHYSICAL_REGION,
            NO_UNIQUE_PHYSICAL_REGION, UNRESOLVED)

NO_CLOSED_PHYSICAL_POLYGON_FROM_CAD = "NO_CLOSED_PHYSICAL_POLYGON_FROM_CAD"

# --- ownership evidence ---------------------------------------------------
EV_ENCLOSING_MATERIAL = "ENCLOSING_MATERIAL_WALL_FACES"
EV_PORTAL_RELATION = "OPENING_OR_PORTAL_RELATIONSHIP"
EV_ROOM_STAMP = "CAD_ROOM_STAMP_INSIDE_IT"
EV_ADJACENCY = "ADJACENCY_CONSISTENT_WITH_ITS_NEIGHBOURS"
EV_WALL_TERMINATION = "WALL_TERMINATION_AT_ITS_CORNERS"
EV_CLEAR_FACE = "CLEAR_FACE_CONTINUITY"
EV_STAIR_SEMANTICS = "STAIR_OR_CUT_PLANE_SEMANTICS"
EV_A18_IDENTITY = "A18_SEMANTIC_IDENTITY"
OWNERSHIP_EVIDENCE = (EV_ENCLOSING_MATERIAL, EV_PORTAL_RELATION,
                      EV_ROOM_STAMP, EV_ADJACENCY, EV_WALL_TERMINATION,
                      EV_CLEAR_FACE, EV_STAIR_SEMANTICS, EV_A18_IDENTITY)

# A stamp alone is support, never proof.
A_SEED_IS_SUPPORTING_EVIDENCE = (
    "a text seed inside a face is supporting evidence of identity. It is "
    "not proof of boundary ownership, and on its own it releases nothing")

LABEL_POLYGON_OWNERSHIP_CONFLICT = "LABEL_POLYGON_OWNERSHIP_CONFLICT"

# --- how agreement between representations may be described -------------
#
# A raster sheet and the DWG it was plotted from are two REPRESENTATIONS of
# one design. When a blind raster reading and the CAD agree, that is worth
# recording, and it is NOT independent corroboration: both descend from the
# same design source family, so a designer's error appears in both.
CROSS_REPRESENTATION_CORROBORATION = "CROSS_REPRESENTATION_CORROBORATION"
INDEPENDENT_SOURCE_FAMILY_CORROBORATION = (
    "INDEPENDENT_SOURCE_FAMILY_CORROBORATION")
SAME_DESIGN_SOURCE_FAMILY = "SAME_DESIGN_SOURCE_FAMILY"

WHY_NOT_INDEPENDENT = (
    "the raster sheet and the DWG are two representations of ONE design. "
    "Agreement between them is cross-representation corroboration: it "
    "shows the reading was faithful, not that the design is right. "
    "Independent corroboration would need another source family, such as "
    "a site measurement or an as-built survey")


def corroboration(*, source_families) -> dict:
    """Name the agreement correctly, by how many source families it spans."""
    fams = sorted(set(source_families))
    kind = (INDEPENDENT_SOURCE_FAMILY_CORROBORATION if len(fams) > 1
            else CROSS_REPRESENTATION_CORROBORATION)
    return {"kind": kind, "source_families": fams,
            "representations_compared": len(source_families),
            "why": WHY_NOT_INDEPENDENT}

# How much of a candidate's boundary must be built material before it can
# be called a closed PHYSICAL region. A ring that is mostly virtual
# topology is a topological cell, not a physical room.
MIN_MATERIAL_SHARE = 0.60

# A face this much larger than the next candidate, holding other labels
# too, is a floor plate rather than the labelled room.
PLATE_AREA_M2 = 200.0

# --- validation -----------------------------------------------------------
V_CONTINUITY = "BOUNDARY_CONTINUITY"
V_PROVENANCE = "ENTITY_PROVENANCE_COMPLETENESS"
V_NO_ANNOTATION_WALL = "NO_ANNOTATION_OR_DIMENSION_WITNESS_AS_WALL"
V_NO_UNEXPLAINED_CLOSURE = "NO_UNEXPLAINED_ARTIFICIAL_CLOSURE"
V_PORTAL_DISTINGUISHED = "PORTAL_DISTINGUISHED_FROM_MATERIAL"
V_ARCS_PRESERVED = "ARCS_PRESERVED"
V_LABEL_OWNERSHIP = "LABEL_OWNERSHIP_PLAUSIBLE"
V_ADJACENCY = "ADJACENCY_CONSISTENT"
V_NO_SITE_LEAK = "NO_SITE_FACE_LEAKAGE"
V_NO_FOREIGN_LABELS = "NO_UNEXPLAINED_CONTAINMENT_OF_UNRELATED_LABELS"
V_NO_BBOX = "NO_BOUNDING_BOX_SUBSTITUTION"
V_NO_OVERLAP = "NO_OVERLAPPING_RELEASED_PHYSICAL_REGIONS"
CHECKS = (V_CONTINUITY, V_PROVENANCE, V_NO_ANNOTATION_WALL,
          V_NO_UNEXPLAINED_CLOSURE, V_PORTAL_DISTINGUISHED,
          V_ARCS_PRESERVED, V_LABEL_OWNERSHIP, V_ADJACENCY,
          V_NO_SITE_LEAK, V_NO_FOREIGN_LABELS, V_NO_BBOX, V_NO_OVERLAP)

PASS = "PASS"
FAIL = "FAIL"
NOT_APPLICABLE = "NOT_APPLICABLE"
WITHHELD = "WITHHELD"

WITHHOLD_RATHER_THAN_REPAIR = (
    "validation failing means the region is withheld. It does not mean the "
    "geometry gets repaired until it closes - a polygon obtained that way "
    "is a number nobody drew")

# Layers whose linework may never close a physical region, because what is
# on them is writing about the drawing rather than the building. This is a
# DEFAULT with evidence, not an invariant about layers of these names
# anywhere else.
ANNOTATION_DEFAULT_ROLES = (cg.ANNOTATION_ONLY, cg.DIMENSION_WITNESS)


def model_hash() -> str:
    parts = ([MODEL] + list(OUTCOMES) + list(OWNERSHIP_EVIDENCE)
             + list(CHECKS) + [f"{MIN_MATERIAL_SHARE}", f"{PLATE_AREA_M2}"])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


@dataclass
class Region:
    """One E1 physical-geometry result, released or withheld."""

    cad_geometry_id: str = ""
    a18_candidate_id: str = ""
    drawing_id: str = ""
    floor: str = ""
    label_as_drawn: str = ""
    outcome: str = UNRESOLVED
    boundary: object = None
    ownership_evidence: tuple = ()
    conflicts: tuple = ()
    validation: dict = field(default_factory=dict)
    released: bool = False
    labels_inside: tuple = ()
    candidates_considered: int = 0
    diagnostics: dict = field(default_factory=dict)
    why: str = ""

    def record(self) -> dict:
        out = {
            "CAD_GEOMETRY_ID": self.cad_geometry_id,
            "A18_CANDIDATE_ID": self.a18_candidate_id,
            "DRAWING_ID": self.drawing_id,
            "FLOOR": self.floor,
            "label_as_drawn": self.label_as_drawn,
            "OUTCOME": self.outcome,
            "RELEASED": self.released,
            "OWNERSHIP_EVIDENCE": list(self.ownership_evidence),
            "a_seed_is_supporting_evidence": A_SEED_IS_SUPPORTING_EVIDENCE,
            "CONFLICTS": list(self.conflicts),
            "VALIDATION": dict(self.validation),
            "labels_inside_this_region": list(self.labels_inside),
            "candidates_considered": self.candidates_considered,
            "diagnostics": dict(self.diagnostics),
            "why": self.why,
        }
        if self.boundary is not None:
            out["BOUNDARY"] = self.boundary.record()
        else:
            out["BOUNDARY"] = None
            out["no_polygon"] = NO_CLOSED_PHYSICAL_POLYGON_FROM_CAD
        return out


def _material_share(boundary) -> float:
    total = boundary.perimeter_mm or 0.0
    if not total:
        return 0.0
    return round(boundary.material_length_mm / total, 4)


def assess(*, cad_geometry_id, a18_candidate_id, drawing_id, floor,
           label, trace_result, labels_in_face=None, a18_identity=False,
           stair_semantics=False, adjacency_ok=None) -> Region:
    """Choose an outcome from evidence, or decline to choose."""
    cands = trace_result.get("candidates") or []
    reg = Region(cad_geometry_id=cad_geometry_id,
                 a18_candidate_id=a18_candidate_id,
                 drawing_id=drawing_id, floor=floor, label_as_drawn=label,
                 candidates_considered=len(cands))

    if not cands:
        reg.outcome = (OPEN_PHYSICAL_REGION
                       if trace_result.get("topology_status")
                       == cg.TOPOLOGY_NOT_CLOSED else UNRESOLVED)
        reg.why = (trace_result.get("why") or "")
        reg.diagnostics = {"faces_built": trace_result.get("faces_built"),
                           "excluded_by_layer":
                               trace_result.get("excluded_by_layer", {})}
        reg.ownership_evidence = ((EV_ROOM_STAMP,) if label else ())
        if a18_identity:
            reg.ownership_evidence += (EV_A18_IDENTITY,)
        return reg

    best = cands[0]
    boundary = best["boundary"]
    area = best["densified_area_m2_rendering_only"]
    inside = tuple(labels_in_face or ())
    share = _material_share(boundary)

    ev = []
    if boundary.material_length_mm > 0:
        ev.append(EV_ENCLOSING_MATERIAL)
    if boundary.contains_artificial_topology:
        ev.append(EV_PORTAL_RELATION)
    if label:
        ev.append(EV_ROOM_STAMP)
    if best["clear_face_basis"] == cg.BASIS_DRAWN_FACE:
        ev.append(EV_CLEAR_FACE)
    if a18_identity:
        ev.append(EV_A18_IDENTITY)
    if stair_semantics:
        ev.append(EV_STAIR_SEMANTICS)
    if adjacency_ok:
        ev.append(EV_ADJACENCY)
    reg.ownership_evidence = tuple(ev)
    reg.labels_inside = inside
    reg.diagnostics = {
        "material_share_of_perimeter": share,
        "densified_area_m2_rendering_only": area,
        "faces_holding_the_seed": trace_result.get(
            "faces_holding_the_seed"),
        "open_edge_length_mm": best["open_edge_length_mm"],
        "not_on_a_drawn_entity_mm": best["not_on_a_drawn_entity_mm"],
        "material_length_mm": best["material_length_mm"],
        "topology_only_length_mm": best["topology_only_length_mm"],
        "contains_artificial_topology":
            best["contains_artificial_topology"],
    }

    conflicts = []
    # A face that holds other rooms' stamps is not this room.
    foreign = [x for x in inside if label and x != label]
    if foreign:
        conflicts.append(LABEL_POLYGON_OWNERSHIP_CONFLICT)
    if area >= PLATE_AREA_M2:
        conflicts.append("FACE_IS_A_FLOOR_PLATE_OR_SITE_RATHER_THAN_A_ROOM")
    if share < MIN_MATERIAL_SHARE:
        conflicts.append("BOUNDARY_IS_MOSTLY_NOT_BUILT_MATERIAL")
    reg.conflicts = tuple(conflicts)

    if foreign and len(set(foreign)) >= 1 and area < PLATE_AREA_M2:
        reg.outcome = MULTI_FUNCTION_PHYSICAL_REGION
        reg.why = ("this one region holds more than one functional label, "
                   f"so it is not the polygon of {label!r} alone: "
                   f"{sorted(set(inside))}")
        reg.boundary = boundary
        return reg
    if area >= PLATE_AREA_M2:
        reg.outcome = NO_UNIQUE_PHYSICAL_REGION
        reg.why = ("the smallest closed face around this stamp is a floor "
                   "plate or the site, not a room. A seed inside a face "
                   "does not make the face the space")
        return reg
    if best["topology_status"] == cg.TOPOLOGY_CLOSED_WITH_OPEN_EDGES:
        reg.outcome = PARTIAL_BOUNDARY_CHAIN
        reg.boundary = boundary
        reg.why = ("part of this ring lies on no drawn entity, so it is a "
                   "boundary chain rather than a closed physical region")
        return reg
    if share < MIN_MATERIAL_SHARE:
        reg.outcome = PARTIAL_BOUNDARY_CHAIN
        reg.boundary = boundary
        reg.why = (f"only {share:.0%} of this ring is built material; the "
                   "rest is topology inserted to close it")
        return reg

    reg.outcome = CLOSED_PHYSICAL_REGION
    reg.boundary = boundary
    reg.why = ("a closed ring of drawn material, with every segment naming "
               "its entity")
    return reg


def validate(reg: Region, *, released_boundaries=(), site_area_m2=None
             ) -> Region:
    """Twelve checks. A failure withholds; it never repairs."""
    b = reg.boundary
    checks = {}

    def put(name, ok, note=""):
        checks[name] = {"result": (PASS if ok is True else
                                   NOT_APPLICABLE if ok is None else FAIL),
                        "note": note}

    if b is None:
        for name in CHECKS:
            put(name, None, "no polygon was released for this region")
        reg.validation = {"checks": checks, "verdict": reg.outcome,
                          "released": False,
                          "rule": WITHHOLD_RATHER_THAN_REPAIR}
        reg.released = False
        return reg

    put(V_CONTINUITY, bool(b.closed and b.segments))
    missing = [s.record()["entity"] for s in b.segments
               if s.role not in cg.TOPOLOGY_ONLY_ROLES and not s.object_id]
    put(V_PROVENANCE, not missing,
        f"{len(missing)} material segments name no entity" if missing
        else "every material segment names its DWG entity")
    bad_roles = [s.role for s in b.segments
                 if s.role in ANNOTATION_DEFAULT_ROLES]
    put(V_NO_ANNOTATION_WALL, not bad_roles,
        f"annotation roles on the ring: {sorted(set(bad_roles))}"
        if bad_roles else "no annotation or dimension witness in the ring")
    unexplained = [s for s in b.segments
                   if s.role in (cg.VIRTUAL_PORTAL_BOUNDARY,
                                 cg.CAD_JUNCTION_REPAIR) and not s.evidence]
    put(V_NO_UNEXPLAINED_CLOSURE, not unexplained,
        f"{len(unexplained)} inserted segments carry no evidence"
        if unexplained else "every inserted segment carries its evidence")
    put(V_PORTAL_DISTINGUISHED,
        all(s.wall_length_contribution_mm == 0.0 for s in b.segments
            if s.role in cg.TOPOLOGY_ONLY_ROLES),
        "topology-only segments contribute zero wall material")
    curved = [s for s in b.segments if s.kind in (cg.ARC, cg.CIRCLE)]
    put(V_ARCS_PRESERVED, all(s.radius > 0 for s in curved) if curved
        else None,
        f"{len(curved)} curved segments keep centre, radius and angles"
        if curved else "this boundary has no curved segment")
    put(V_LABEL_OWNERSHIP,
        LABEL_POLYGON_OWNERSHIP_CONFLICT not in reg.conflicts,
        "; ".join(reg.conflicts) or "no ownership conflict recorded")
    put(V_ADJACENCY, None if EV_ADJACENCY not in reg.ownership_evidence
        else True, "adjacency evidence recorded"
        if EV_ADJACENCY in reg.ownership_evidence
        else "adjacency was not established for this region")
    area = reg.diagnostics.get("densified_area_m2_rendering_only") or 0.0
    leaked = bool(site_area_m2 and area >= 0.9 * site_area_m2)
    put(V_NO_SITE_LEAK, not leaked,
        "the ring is the site face" if leaked else "the ring is not the site")
    put(V_NO_FOREIGN_LABELS,
        not [x for x in reg.labels_inside
             if reg.label_as_drawn and x != reg.label_as_drawn],
        f"labels inside: {sorted(set(reg.labels_inside))}")
    put(V_NO_BBOX, True,
        "the boundary is a segment chain; the bounding box is stored for "
        "indexing and flagged as not measurement geometry")
    overlap = 0
    for other in released_boundaries:
        if other is b:
            continue
        overlap += 1 if _overlaps(b, other) else 0
    put(V_NO_OVERLAP, overlap == 0,
        f"{overlap} released regions overlap this one" if overlap
        else "no released region overlaps this one")

    failed = [k for k, v in checks.items() if v["result"] == FAIL]
    reg.validation = {
        "checks": checks,
        "failed": failed,
        "verdict": (WITHHELD if failed else PASS),
        "released": not failed and reg.outcome == CLOSED_PHYSICAL_REGION,
        "rule": WITHHOLD_RATHER_THAN_REPAIR,
    }
    reg.released = reg.validation["released"]
    if failed:
        reg.why = (f"withheld: {', '.join(failed)}. "
                   + WITHHOLD_RATHER_THAN_REPAIR)
    return reg


def _overlaps(a, b) -> bool:
    from shapely.geometry import Polygon
    try:
        pa, pb = Polygon(a.points()), Polygon(b.points())
        if not (pa.is_valid and pb.is_valid):
            return False
        inter = pa.intersection(pb).area
        return inter > 0.01 * min(pa.area, pb.area)
    except Exception:
        return False


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "OUTCOMES": list(OUTCOMES),
        "OWNERSHIP_EVIDENCE": list(OWNERSHIP_EVIDENCE),
        "CHECKS": list(CHECKS),
        "MIN_MATERIAL_SHARE": MIN_MATERIAL_SHARE,
        "PLATE_AREA_M2": PLATE_AREA_M2,
        "why": {
            "a_seed_is_supporting_evidence": A_SEED_IS_SUPPORTING_EVIDENCE,
            "withhold_rather_than_repair": WITHHOLD_RATHER_THAN_REPAIR,
            "success_is_not_closure": (
                "E1 does not need every functional label to have a closed "
                "polygon. An OPEN, PARTIAL or UNRESOLVED result is "
                "preferable to manufactured geometry"),
        },
    }
