"""Inside the building, outside it, or not established. Never by area.

Round 5 released a 5.6 m² strip that the benchmark says is a garden. It was
not misclassified — **nothing in the engine could say "outside the
building" at all.** Across nine drawing regions the boundary authority
found 57 envelope bands and zero site boundaries, and DR-002's drawn lines
bound one connected 1,130 m² component with every released polygon inside
it. An absent capability, not a wrong answer.

    NO AREA RULE. A 5 m² strip and a 500 m² strip are classified the same
    way, and if the evidence does not reach, the answer is UNRESOLVED.

The evidence is §7's list, each token recorded and none decisive alone:

    ENVELOPE_CONTAINMENT     inside the ring the authority calls the fabric
    OUTSIDE_THE_ENVELOPE     inside the site, outside the fabric
    EXTERIOR_ADJACENCY       it opens onto the unbounded outside
    DOOR_CONNECTIVITY        reachable through a portal from inside
    WALL_TOPOLOGY            bounded by envelope bands rather than partitions
    EXTERNAL_SEMANTICS       a garden, terrace, courtyard, roof or balcony
    INTERIOR_SEMANTICS       a room concept sits in it
    SITE_RELATIONSHIP        it lies between the site line and the fabric
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import architectural_ontology as onto
from engine import boundary_authority as authority

MODEL = "ENVELOPE_EVIDENCE_INTERIOR_EXTERIOR_V1"

INTERIOR = "INTERIOR"
EXTERIOR = "EXTERIOR"
UNRESOLVED = "INTERIOR_EXTERIOR_UNRESOLVED"

# ROUND 6A §9. Two questions, not one. Whether a piece of geometry is
# inside the BUILDING is answered by the envelope. How far the ground
# around it EXTENDS is answered by the site boundary, and only by that.
# P7757 draws no site boundary anywhere, and that must not make its garden
# strip interior: it makes its EXTENT unknown, which is enough to keep it
# out of an internal floor finish and not enough to measure a yard.
INSIDE_BUILDING = "INSIDE_BUILDING"
OUTSIDE_BUILDING = "OUTSIDE_BUILDING"
BUILDING_UNKNOWN = "BUILDING_EXTENT_UNKNOWN"
SITE_ESTABLISHED = "SITE_EXTENT_ESTABLISHED"
SITE_UNKNOWN = "SITE_EXTENT_UNKNOWN"

BUILDING_VERDICTS = (INSIDE_BUILDING, OUTSIDE_BUILDING, BUILDING_UNKNOWN)
SITE_VERDICTS = (SITE_ESTABLISHED, SITE_UNKNOWN)

EV_ENVELOPE_CONTAINMENT = "INSIDE_THE_BUILDING_ENVELOPE"
EV_OUTSIDE_ENVELOPE = "INSIDE_THE_SITE_AND_OUTSIDE_THE_ENVELOPE"
EV_EXTERIOR_ADJACENCY = "OPENS_ONTO_THE_UNBOUNDED_OUTSIDE"
EV_DOOR_CONNECTIVITY = "REACHABLE_THROUGH_A_PORTAL_FROM_AN_INTERIOR_SPACE"
EV_WALL_TOPOLOGY = "BOUNDED_MAINLY_BY_ENVELOPE_BANDS"
EV_EXTERNAL_SEMANTICS = "AN_EXTERNAL_SPACE_CONCEPT_SITS_IN_IT"
EV_INTERIOR_SEMANTICS = "A_ROOM_CONCEPT_SITS_IN_IT"
EV_SITE_RELATIONSHIP = "BETWEEN_THE_SITE_LINE_AND_THE_FABRIC"
EV_NO_ENVELOPE = "NO_BUILDING_ENVELOPE_WAS_ESTABLISHED_IN_THIS_REGION"

EVIDENCE = (EV_ENVELOPE_CONTAINMENT, EV_OUTSIDE_ENVELOPE,
            EV_EXTERIOR_ADJACENCY, EV_DOOR_CONNECTIVITY, EV_WALL_TOPOLOGY,
            EV_EXTERNAL_SEMANTICS, EV_INTERIOR_SEMANTICS,
            EV_SITE_RELATIONSHIP, EV_NO_ENVELOPE)

# The ontology's own external concepts. Nothing is added to the vocabulary.
EXTERNAL_CLASS = onto.EXTERNAL_SPACE


@dataclass
class EnvelopeModel:
    """One region's fabric and ground, as far as the drawing establishes."""

    region_id: str = ""
    envelope = None                 # shapely geometry or None
    site = None
    bands: dict = field(default_factory=dict)
    exterior_faces: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    @property
    def has_envelope(self) -> bool:
        return self.envelope is not None

    def record(self) -> dict:
        return {"drawing_region_id": self.region_id,
                "envelope_established": self.has_envelope,
                "site_established": self.site is not None,
                "envelope_area_m2": (None if self.envelope is None
                                     else round(self.envelope.area / 1e6, 2)),
                "site_area_m2": (None if self.site is None
                                 else round(self.site.area / 1e6, 2)),
                "exterior_faces_between_site_and_fabric": len(
                    self.exterior_faces),
                "notes": dict(self.notes)}


def _ring_geometry(candidates, band_ids):
    """The area enclosed by a named set of bands."""
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union

    segs = []
    for c in candidates:
        if c.object_id not in band_ids:
            continue
        lo, hi = sorted((c.start_mm, c.end_mm))
        if hi - lo <= 0:
            continue
        segs.append(LineString([(lo, c.fixed_mm), (hi, c.fixed_mm)])
                    if c.axis == "H"
                    else LineString([(c.fixed_mm, lo), (c.fixed_mm, hi)]))
    if not segs:
        return None
    faces = list(polygonize(unary_union(segs)))
    if not faces:
        return None
    return unary_union(faces)


def _closure_ids(closures) -> set:
    """Portal closures are admitted to whichever ring they fall on."""
    return {c.object_id for c in closures or ()}


def build(region_id: str, candidates, auth, *, closures=(),
          room_points=()) -> EnvelopeModel:
    """The region's envelope and site, from the authority's own verdicts."""
    m = EnvelopeModel(region_id=region_id)
    env_ids = {b.band_id for b in auth.bands
               if authority.BUILDING_ENVELOPE in b.roles}
    site_ids = {b.band_id for b in auth.bands
                if authority.SITE_BOUNDARY in b.roles}
    m.bands = {"envelope_bands_named_by_the_authority": len(env_ids),
               "site_bands": len(site_ids)}
    # A doorway in an external wall breaks its ring, and a broken ring
    # polygonises into slivers that then "contain" nothing. The portal
    # closures round 4 already validated are added so an entrance does not
    # cost a building its envelope.
    lines = list(candidates) + list(closures)
    # THE FABRIC IS WHAT IS LEFT WHEN THE GROUND IS TAKEN AWAY.
    #
    # The authority only labels bands on the OUTERMOST ring, so where a
    # site boundary exists the building's own ring is called an internal
    # partition and BUILDING_ENVELOPE is never assigned. Asking for the
    # outermost ring of everything that is NOT the site gets the fabric in
    # both cases, and uses the authority's own site verdict to do it.
    fabric_ids = ({c.object_id for c in lines} - site_ids)
    m.envelope = _ring_geometry(lines, fabric_ids)
    m.site = _ring_geometry(lines, site_ids | _closure_ids(closures))

    # AN ENVELOPE CONTAINS ROOMS. A ring that contains none of this
    # region's room observations is not the fabric — it is whatever else
    # the lines happened to close — and claiming it would put every room
    # outside the building, which is exactly what a broken ring did.
    if m.envelope is not None and room_points:
        from shapely.geometry import Point

        if not any(m.envelope.contains(Point(x, y)) for x, y in room_points):
            m.notes["envelope_rejected"] = (
                "a ring formed from the envelope bands, and it contains "
                "none of this region's room observations. The fabric "
                "contains rooms, so this is not the fabric")
            m.envelope = None
    # The ground between the site line and the fabric. These are not room
    # candidates and never were — but a floor trade has to KNOW about them
    # to leave them out, so they are enumerated rather than dropped.
    if m.envelope is not None and m.site is not None:
        try:
            ground = m.site.difference(m.envelope)
            parts = getattr(ground, "geoms", None) or [ground]
            for n, g in enumerate(parts, 1):
                if g.is_empty or g.area <= 0:
                    continue
                pt = g.representative_point()
                m.exterior_faces.append({
                    "face_id": f"EXT-{region_id}-{n:03d}",
                    "region_id": region_id,
                    "point": (pt.x, pt.y),
                    "wkt": g.wkt,
                    "why": ("inside the site boundary and outside the "
                            "building envelope")})
        except Exception:       # noqa: BLE001
            m.notes["ground_not_computable"] = (
                "the site and envelope rings did not subtract cleanly")

    if m.envelope is None:
        m.notes["no_envelope"] = (
            "this region has no band the authority calls a building "
            "envelope, so containment cannot be asked. Every verdict that "
            "would have rested on it is UNRESOLVED rather than guessed")
    return m


@dataclass(frozen=True)
class Verdict:
    space_id: str
    region_id: str
    verdict: str
    evidence: tuple = ()
    why: str = ""
    building: str = BUILDING_UNKNOWN
    site_extent: str = SITE_UNKNOWN

    @property
    def outside_building(self) -> bool:
        return self.building == OUTSIDE_BUILDING

    @property
    def extent_unresolved(self) -> bool:
        """Outside the building, with nothing to say how far it goes."""
        return (self.building == OUTSIDE_BUILDING
                and self.site_extent == SITE_UNKNOWN)

    def record(self) -> dict:
        return {"space_id": self.space_id,
                "drawing_region_id": self.region_id,
                "INTERIOR_EXTERIOR": self.verdict,
                "BUILDING": self.building,
                "SITE_EXTENT": self.site_extent,
                "evidence": list(self.evidence),
                "why": self.why,
                "never": "no area took part in this verdict",
                "two_questions": (
                    "the envelope says which side of the BUILDING this is; "
                    "the site boundary says how far the ground around it "
                    "extends. A missing site answers the second and not "
                    "the first")}


def classify_point(model, x: float, y: float, *, concepts=(),
                   space_id: str = "", reachable_from_interior=False
                   ) -> Verdict:
    """Inside, outside, or not established — for one point in one region."""
    from shapely.geometry import Point

    ev, verdict, why = [], UNRESOLVED, ""
    pt = Point(x, y)
    external = [c for c in concepts if c == EXTERNAL_CLASS]
    interior_sem = [c for c in concepts
                    if c == onto.ROOM or c == onto.FUNCTIONAL_ZONE]

    if external:
        ev.append(EV_EXTERNAL_SEMANTICS)
    if interior_sem:
        ev.append(EV_INTERIOR_SEMANTICS)
    if reachable_from_interior:
        ev.append(EV_DOOR_CONNECTIVITY)

    inside_env = model.has_envelope and model.envelope.contains(pt)
    inside_site = model.site is not None and model.site.contains(pt)
    if not model.has_envelope:
        ev.append(EV_NO_ENVELOPE)
    elif inside_env:
        ev.append(EV_ENVELOPE_CONTAINMENT)
    else:
        ev.append(EV_OUTSIDE_ENVELOPE)
        if inside_site:
            ev.append(EV_SITE_RELATIONSHIP)

    # ---- the rules, named and in order --------------------------------
    if external:
        verdict = EXTERIOR
        why = ("an external-space concept sits inside it. A garden with a "
               "roof over it would still be drawn as a garden, and the "
               "label is the architect's statement about use")
    elif model.has_envelope and not inside_env:
        verdict = EXTERIOR
        why = ("it lies outside the ring this region's authority calls the "
               "building envelope" + (", and inside the site boundary"
                                      if inside_site else ""))
    elif inside_env:
        verdict = INTERIOR
        why = "it lies inside the building envelope"
    elif interior_sem or reachable_from_interior:
        verdict = INTERIOR
        why = ("no envelope was established, but a room concept sits in it "
               "or it is reachable through a portal from a space that is "
               "interior")
    else:
        verdict = UNRESOLVED
        why = ("no envelope was established in this region and nothing else "
               "says which side of the building this is. UNRESOLVED is the "
               "answer, and an area comparison is not allowed to supply "
               "one")
    building = (BUILDING_UNKNOWN if not model.has_envelope
                else INSIDE_BUILDING if inside_env else OUTSIDE_BUILDING)
    if external and building == BUILDING_UNKNOWN:
        building = OUTSIDE_BUILDING
    site_extent = (SITE_ESTABLISHED if model.site is not None
                   else SITE_UNKNOWN)
    return Verdict(space_id=space_id, region_id=model.region_id,
                   verdict=verdict, evidence=tuple(ev), why=why,
                   building=building, site_extent=site_extent)


def frozen_parameters() -> dict:
    return {"MODEL": MODEL, "EVIDENCE": list(EVIDENCE),
            "why": {"no_area_rule": (
                "size is not evidence of being outdoors. The 5.6 m2 strip "
                "and a 500 m2 courtyard are asked the same questions"),
                "a_missing_site_is_not_an_interior": (
                    "outside the envelope with no site boundary is "
                    "OUTSIDE_BUILDING with SITE_EXTENT_UNKNOWN. That is "
                    "enough to keep it out of an internal floor finish and "
                    "not enough to measure a yard. No site polygon is "
                    "invented to fill the gap"),
                "unresolved_is_common": (
                    "where a drawing gives no envelope, this returns "
                    "UNRESOLVED rather than assuming interior. On P7757 "
                    "that is most of the drawing, and saying so is the "
                    "point")}}


def model_hash() -> str:
    parts = [MODEL, INTERIOR, EXTERIOR, UNRESOLVED,
             "|".join(BUILDING_VERDICTS), "|".join(SITE_VERDICTS),
             "|".join(EVIDENCE),
             authority.authority_hash(), onto.ontology_hash()]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
