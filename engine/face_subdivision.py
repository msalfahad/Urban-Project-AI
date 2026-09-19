"""Splitting a face is a geometric act. Counting its labels is not.

P7757's labelled plan came out of round 4 as one 194 m² face holding all
thirty-eight label observations on it — every room stamp, English and
Arabic, inside a single polygon. It is obvious that the plan has more than
one room in it, and the obviousness is the trap:

    SEMANTIC OBSERVATIONS MAY DIAGNOSE UNDER-SEGMENTATION.
    THEY MAY NOT CREATE THE MISSING GEOMETRY.

A face is subdivided only by a partition boundary something supports — a
drawn wall, a recovered span that earned a topology authority, or a
validated portal. Never because it holds many labels, never because its
area looks too large, never because a room "should" be there, and never
because an expected room count or a human quantity says so.

    FALSE SUBDIVISION IS AS DANGEROUS AS FALSE MERGING.

OPEN-PLAN ARCHITECTURE IS THE REASON THIS MATTERS (§11)

A kitchen, a dining area and a saloon sharing one supported open polygon
are one physical space with three functional zones, and a Gulf villa is
full of exactly that. Splitting it because three concepts were found would
invent two rooms and two sets of walls that were never built. So a face
holding several identities is FLAGGED and left alone, and the flag has
three honest outcomes:

    ONE_PHYSICAL_SPACE          geometry establishes no partition in it
    MULTIPLE_PHYSICAL_SPACES    geometry did subdivide it
    ROOM_PARTITION_UNRESOLVED   partition hypotheses exist and none resolve

The third is the commonest and it is not a failure state.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import partition_continuity as pc

SUBDIVIDER = "SUPPORTED_PARTITION_FACE_SUBDIVISION_V1"

ONE_PHYSICAL_SPACE = "ONE_PHYSICAL_SPACE"
MULTIPLE_PHYSICAL_SPACES = "MULTIPLE_PHYSICAL_SPACES"
ROOM_PARTITION_UNRESOLVED = "ROOM_PARTITION_UNRESOLVED"

POSSIBLE_UNDERSEGMENTED = "POSSIBLE_UNDERSEGMENTED_SPACE"

OUTCOMES = (ONE_PHYSICAL_SPACE, MULTIPLE_PHYSICAL_SPACES,
            ROOM_PARTITION_UNRESOLVED)

WHAT_MAY_SUBDIVIDE = (
    "a drawn wall, a recovered span carrying a topology authority, or a "
    "validated portal. Nothing else — not a label, not an area, not an "
    "expected room count, and not a human quantity")


@dataclass(frozen=True)
class Diagnosis:
    """One face that holds more than one reconciled space observation."""

    space_id: str
    region_id: str
    area_m2: float | None
    observations: tuple
    supported_internal_partitions: tuple
    unresolved_internal_hypotheses: tuple
    open_plan_evidence: tuple
    portal_evidence: tuple
    outcome: str
    became: tuple = ()
    why: str = ""

    def record(self) -> dict:
        return {
            "flag": POSSIBLE_UNDERSEGMENTED,
            "polygon_id": self.space_id,
            "drawing_region_id": self.region_id,
            "area_m2": self.area_m2,
            "observations": list(self.observations),
            "observation_count": len(self.observations),
            "supported_internal_partitions": list(
                self.supported_internal_partitions),
            "unresolved_internal_partition_hypotheses": list(
                self.unresolved_internal_hypotheses),
            "open_plan_evidence": list(self.open_plan_evidence),
            "portal_evidence": list(self.portal_evidence),
            "classification": self.outcome,
            "subdivided_into": list(self.became),
            "why": self.why,
            "what_was_not_done": (
                "the polygon was not split because it holds several "
                "labels, and it was not split because of its area. "
                + WHAT_MAY_SUBDIVIDE),
        }


@dataclass
class SubdivisionReport:
    region_id: str = ""
    faces_before: int = 0
    faces_after: int = 0
    diagnoses: list = field(default_factory=list)
    subdivided: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def counts(self) -> dict:
        return {
            "faces_before_recovery": self.faces_before,
            "faces_after_recovery": self.faces_after,
            "faces_gained_by_recovery": max(
                0, self.faces_after - self.faces_before),
            "possible_undersegmented_spaces": len(self.diagnoses),
            "by_classification": dict(Counter(
                d.outcome for d in self.diagnoses).most_common()),
            "faces_actually_subdivided": len(self.subdivided),
        }

    def record(self, *, limit: int = 20) -> dict:
        return {
            "subdivider": SUBDIVIDER,
            "FACE_SUBDIVISION_HASH": subdivision_hash(),
            "drawing_region_id": self.region_id,
            "counts": self.counts(),
            "outcomes": list(OUTCOMES),
            "what_may_subdivide_a_face": WHAT_MAY_SUBDIVIDE,
            "diagnoses": [d.record() for d in self.diagnoses[:limit]],
            "open_plan_safety": (
                "a face holding several identities with no supported "
                "partition between them stays ONE physical space with "
                "functional zones. Splitting it would invent rooms and "
                "walls that were never built"),
            "notes": dict(self.notes),
        }


def subdivision_hash() -> str:
    parts = [SUBDIVIDER, "|".join(OUTCOMES), POSSIBLE_UNDERSEGMENTED,
             WHAT_MAY_SUBDIVIDE, pc.continuity_hash()]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _inside(wkt: str, x: float, y: float) -> bool:
    from shapely.geometry import Point
    from shapely.wkt import loads

    try:
        return loads(wkt).contains(Point(x, y))
    except Exception:       # noqa: BLE001
        return False


def _span_inside(wkt: str, span) -> bool:
    """Does this partition hypothesis lie within the face?"""
    from shapely.geometry import LineString
    from shapely.wkt import loads

    try:
        face = loads(wkt)
    except Exception:       # noqa: BLE001
        return False
    mid = (span.lo + span.hi) / 2.0
    for f in span.faces_mm:
        pt = (mid, f) if span.axis == "H" else (f, mid)
        if face.buffer(0).contains(LineString([pt, pt]).centroid):
            return True
    return False


def diagnose(before, after, *, continuity=None, region_id: str = "DR-001"
             ) -> SubdivisionReport:
    """Flag every multi-observation face, and say what happened to it.

    `before` are the faces the drawn geometry alone produced; `after` are
    the faces produced once recovered spans and validated portals were
    added. Nothing here splits anything: the splitting already happened in
    the arrangement, or it did not.
    """
    rep = SubdivisionReport(region_id=region_id)
    rep.faces_before = len(before)
    rep.faces_after = len(after)
    spans = list(continuity.spans) if continuity is not None else []

    for node in before:
        if len(node.zones) <= 1:
            continue
        wkt = node.face_wkt
        supported = [s.span_id for s in spans
                     if s.may_subdivide and _span_inside(wkt, s)]
        unresolved = [s.span_id for s in spans
                      if s.verdict == pc.UNRESOLVED_GAP
                      and _span_inside(wkt, s)]
        portals = list(node.boundary_openings)
        children = [n.node_id for n in after
                    if n.node_id != node.node_id
                    and any(_inside(n.face_wkt, z.identity.x, z.identity.y)
                            for z in node.zones if z.identity)]

        if len(children) >= 2:
            outcome = MULTIPLE_PHYSICAL_SPACES
            why = ("supported partition geometry divided this polygon. The "
                   "labels did not divide it; they were attached "
                   "afterwards")
        elif unresolved:
            outcome = ROOM_PARTITION_UNRESOLVED
            why = (f"{len(unresolved)} partition hypothesis(es) lie inside "
                   "this polygon and none of them resolved. Whether it is "
                   "one space or several is not established, and no split "
                   "was invented to settle it")
        elif supported:
            outcome = ROOM_PARTITION_UNRESOLVED
            why = ("supported partition geometry lies inside this polygon "
                   "but did not close a cycle, so the subdivision it "
                   "implies is not complete")
        else:
            outcome = ONE_PHYSICAL_SPACE
            why = ("no partition of any kind lies inside this polygon. "
                   "Several concepts share one supported open space, which "
                   "is what open-plan architecture looks like, and they are "
                   "reported as functional zones")

        rep.diagnoses.append(Diagnosis(
            space_id=node.node_id, region_id=region_id,
            area_m2=(None if not node.enclosure
                     or node.enclosure.area_m2 is None
                     else round(node.enclosure.area_m2, 3)),
            observations=tuple(t for z in node.zones
                               for t in z.label_observations),
            supported_internal_partitions=tuple(supported),
            unresolved_internal_hypotheses=tuple(unresolved),
            open_plan_evidence=(),
            portal_evidence=tuple(portals),
            outcome=outcome, became=tuple(children), why=why))
        if len(children) >= 2:
            rep.subdivided.append(node.node_id)

    rep.notes["semantics_are_a_diagnosis"] = (
        "a polygon holding several reconciled room concepts is FLAGGED "
        "POSSIBLE_UNDERSEGMENTED_SPACE. The flag reports a problem; it "
        "never supplies the geometry that would solve it")
    rep.notes["no_area_test"] = (
        "no area and no expected room count takes part in any "
        "classification above")
    return rep
