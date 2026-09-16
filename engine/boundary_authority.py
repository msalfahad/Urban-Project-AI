"""Which wall-like lines may close a ROOM — decided by nesting, not by name.

Round 1 flooded a washroom seed out to the plot boundary and released
443 m². Round 2 stopped the release but not the flood, and named the cause:

    the wall candidate set contains geometry that is wall-like but is not
    necessarily a ROOM BOUNDARY

A site wall and a partition are both two parallel faces a consistent
distance apart. The paired-face test cannot separate them, because it is
asking about how the line is DRAWN and the difference is what the line
DOES.

WHAT SEPARATES THEM IS WHAT THEY HOLD IN

§6 states the rule directly, so the test states it directly too:

    Take the outermost boundary of everything the drawn lines enclose.
    Remove the bands lying on it and look again. If every room observation
    is STILL enclosed by something, that outer ring was never needed to
    hold a room in — it bounds ground, and it may not close a room. If
    removing it leaves a room unenclosed, the building boundary coincides
    with it, §6's exception applies, and it stays eligible.

That is containment. It compares no sizes, so a plot far larger than its
building and a plot barely larger than it are handled the same way.

    ROOM_BOUNDARY_ELIGIBLE = a band the rooms actually need

This is why §5's warning is satisfied without a special case. Where there
is no site line, the outermost boundary IS the building envelope, removing
it leaves the rooms open, and it stays eligible — so a corner room may be
closed by two external walls. Only a ring the rooms do not need is dropped.

    A WALL MAY HOLD MORE THAN ONE ROLE. A building envelope is
    BUILDING_ENVELOPE and ROOM_BOUNDARY_ELIGIBLE at once, because those
    answer different questions.

AN EARLIER VERSION OF THIS COUNTED RAY CROSSINGS and was wrong. An open
partition adds crossings on one side only, so a point between the plot and
the building could score the same depth as a point inside a room. The
synthetic cases caught it; a count of crossings is not a nesting depth.

NOTHING HERE READS A NAME, A LAYER OR AN AREA.
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field

AUTHORITY = "NESTING_DEPTH_BOUNDARY_AUTHORITY_V1"

# Roles. A band may carry several.
SITE_BOUNDARY = "SITE_BOUNDARY"
BUILDING_ENVELOPE = "BUILDING_ENVELOPE"
INTERNAL_PARTITION = "INTERNAL_PARTITION"
ROOM_BOUNDARY_ELIGIBLE = "ROOM_BOUNDARY_ELIGIBLE"
DETAIL_GEOMETRY = "DETAIL_GEOMETRY"
UNRESOLVED = "UNRESOLVED"

# How near a band must lie to the outermost boundary to be counted as part
# of it. Larger than any wall this engine admits (the profile's paired-face
# band tops out at 600 mm), so both faces of one outer wall are recognised
# as that wall; smaller than any room, so an internal partition beside the
# envelope is never mistaken for it.
PROBE_OFFSET_MM = 700.0

# A band shorter than this is a jamb, a tick or a fragment. It is not
# dropped — it is marked DETAIL_GEOMETRY and kept out of the depth model,
# where a stray 40 mm mark would otherwise add a phantom ring.
MIN_STRUCTURAL_LENGTH_MM = 300.0

WHY = {
    SITE_BOUNDARY: "removing it leaves every room still enclosed, so it was "
                   "never holding one in. §6 forbids it from closing a room",
    BUILDING_ENVELOPE: "removing it leaves a room unenclosed — the building "
                       "boundary coincides with it, so it may form a side",
    INTERNAL_PARTITION: "it lies inside the outermost boundary and divides "
                        "the fabric",
    ROOM_BOUNDARY_ELIGIBLE: "the rooms need it, so it may close one",
    DETAIL_GEOMETRY: "too short to be structure. Kept out of the model so "
                     "it cannot invent a boundary",
    UNRESOLVED: "nothing established what it does. It closes nothing",
}


@dataclass(frozen=True)
class BandAuthority:
    """One wall-like band, its measured depths, and the roles it holds."""

    band_id: str
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    depth_low: int
    depth_high: int
    roles: tuple
    evidence: tuple

    @property
    def inner_depth(self) -> int:
        return max(self.depth_low, self.depth_high)

    @property
    def may_close_a_room(self) -> bool:
        return ROOM_BOUNDARY_ELIGIBLE in self.roles

    def record(self) -> dict:
        return {"band_id": self.band_id, "axis": self.axis,
                "fixed_mm": round(self.fixed_mm, 2),
                "interval_mm": [round(self.start_mm, 2),
                                round(self.end_mm, 2)],
                "exterior_depth_each_side": [self.depth_low, self.depth_high],
                "roles": list(self.roles),
                "may_close_a_room": self.may_close_a_room,
                "evidence": list(self.evidence)}


@dataclass
class AuthorityReport:
    bands: list = field(default_factory=list)
    room_depth: int | None = None      # 2 when a site ring was separated
    notes: dict = field(default_factory=dict)

    def eligible(self) -> list:
        return [b for b in self.bands if b.may_close_a_room]

    def by_role(self) -> dict:
        return dict(Counter(r for b in self.bands
                            for r in b.roles).most_common())

    def record(self, *, limit: int = 30) -> dict:
        return {
            "authority": AUTHORITY,
            "ROOM_BOUNDARY_AUTHORITY_HASH": authority_hash(),
            "bands_classified": len(self.bands),
            "room_observation_depth": self.room_depth,
            "by_role": self.by_role(),
            "room_boundary_eligible": len(self.eligible()),
            "frozen_parameters": frozen_parameters(),
            "sample": [b.record() for b in self.bands[:limit]],
            "notes": dict(self.notes),
            "never": ("no layer name, no block name and no area takes part "
                      "in any verdict here. The question is whether the "
                      "rooms still hold without this band"),
        }


def frozen_parameters() -> dict:
    return {
        "AUTHORITY": AUTHORITY,
        "PROBE_OFFSET_MM": PROBE_OFFSET_MM,
        "MIN_STRUCTURAL_LENGTH_MM": MIN_STRUCTURAL_LENGTH_MM,
        "why": {
            "PROBE_OFFSET_MM": (
                "smaller than any room, larger than any wall the profile "
                "admits, so the probe lands beside the wall rather than "
                "inside it or two rooms away"),
            "MIN_STRUCTURAL_LENGTH_MM": (
                "a jamb or a tick is not a ring. Short marks are kept out "
                "of the depth model so they cannot invent one"),
            "no_size_prior": (
                "the test is containment — does removing this band leave a "
                "room unenclosed. No area, no dimension and no expected "
                "room size takes part in it"),
        },
    }


def authority_hash() -> str:
    parts = [AUTHORITY, str(PROBE_OFFSET_MM), str(MIN_STRUCTURAL_LENGTH_MM),
             SITE_BOUNDARY, BUILDING_ENVELOPE, INTERNAL_PARTITION,
             ROOM_BOUNDARY_ELIGIBLE, DETAIL_GEOMETRY, UNRESOLVED]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _segments(candidates):
    """Every structural band as a LineString, with its id."""
    from shapely.geometry import LineString

    out = []
    for c in candidates:
        lo, hi = sorted((c.start_mm, c.end_mm))
        if hi - lo < MIN_STRUCTURAL_LENGTH_MM:
            continue
        if c.axis == "H":
            geom = LineString([(lo, c.fixed_mm), (hi, c.fixed_mm)])
        else:
            geom = LineString([(c.fixed_mm, lo), (c.fixed_mm, hi)])
        out.append((c.object_id, geom))
    return out


def _faces(segments):
    """The closed faces the drawn lines bound, as polygons."""
    from shapely.ops import polygonize, unary_union

    if not segments:
        return []
    merged = unary_union([g for _oid, g in segments])
    return list(polygonize(merged))


def _encloses_all(faces, observations) -> bool:
    """Does some face still contain every room observation?"""
    from shapely.geometry import Point

    if not observations:
        return False
    for o in observations:
        pt = Point(o.x, o.y)
        if not any(f.contains(pt) for f in faces):
            return False
    return True


def _on_ring(geom, ring, tol: float) -> bool:
    """Is this band part of the given outer boundary?"""
    return geom.distance(ring) <= tol


def _outer_rings(faces):
    """The exterior boundary of everything the drawn lines bound."""
    from shapely.ops import unary_union

    if not faces:
        return None
    built = unary_union(faces)
    parts = getattr(built, "geoms", None) or [built]
    from shapely.geometry import MultiLineString

    rings = [p.exterior for p in parts if hasattr(p, "exterior")]
    return MultiLineString(rings) if rings else None


def classify(candidates, observations=()) -> AuthorityReport:
    """Give every wall-like band its roles, from what it encloses.

    THE TEST IS §6's RULE, DIRECTLY. Take the outermost boundary of
    everything the drawn lines enclose. Remove the bands lying on it and
    look again: if every room observation is STILL enclosed by something,
    that outer ring was never needed to hold a room in — it is a site line,
    and it may not close a room. If removing it leaves a room unenclosed,
    the building boundary coincides with it, and §6's exception applies: it
    is the building envelope and it stays eligible.

    No count of crossings, no size, no name. An earlier version of this
    counted ray crossings and was wrong: an open partition adds crossings
    asymmetrically, so a point between the plot and the building could
    score the same depth as a point inside a room.
    """
    rep = AuthorityReport()
    segs = _segments(candidates)
    faces = _faces(segs)
    ring = _outer_rings(faces)

    on_outer = set()
    if ring is not None:
        for oid, geom in segs:
            if _on_ring(geom, ring, PROBE_OFFSET_MM):
                on_outer.add(oid)

    # Does the drawing still hold its rooms without the outer ring?
    inner_faces = _faces([(oid, g) for oid, g in segs if oid not in on_outer])
    rooms_held_without_outer = _encloses_all(inner_faces, observations)
    rep.room_depth = (0 if not observations
                      else (2 if rooms_held_without_outer else 1))

    structural = {oid for oid, _g in segs}
    for c in candidates:
        lo, hi = sorted((c.start_mm, c.end_mm))
        roles, ev = [], []
        if c.object_id not in structural:
            # SHORT IS NOT THE SAME AS IRRELEVANT. A short run is kept out
            # of the RING model, where a stray mark would invent a boundary
            # — but it is still drawn wall and may still close a room. A
            # first version excluded these outright and stripped 1,313 of
            # 2,877 bands from a drawing whose wall runs average 462 mm,
            # after which nothing enclosed at all.
            roles.extend([DETAIL_GEOMETRY, INTERNAL_PARTITION,
                          ROOM_BOUNDARY_ELIGIBLE])
            ev.append(f"only {hi - lo:.0f} mm long, so it takes no part in "
                      "finding the outermost boundary — but it is drawn "
                      "wall and may still form part of a room's side")
        elif not observations:
            roles.append(UNRESOLVED)
            ev.append("no room observation exists, so there is nothing to "
                      "ask whether this band encloses")
        elif c.object_id in on_outer and rooms_held_without_outer:
            roles.append(SITE_BOUNDARY)
            ev.append("it lies on the outermost boundary, and every room "
                      "observation stays enclosed without it. It was never "
                      "needed to hold a room in, so it bounds ground")
        elif c.object_id in on_outer:
            roles.extend([BUILDING_ENVELOPE, ROOM_BOUNDARY_ELIGIBLE])
            ev.append("it lies on the outermost boundary, and removing it "
                      "leaves a room unenclosed — the building boundary "
                      "coincides with it, so its inner face may form a "
                      "room side")
        else:
            roles.extend([INTERNAL_PARTITION, ROOM_BOUNDARY_ELIGIBLE])
            ev.append("it lies inside the outermost boundary, so it divides "
                      "the fabric rather than bounding it")

        rep.bands.append(BandAuthority(
            band_id=c.object_id, axis=c.axis, fixed_mm=c.fixed_mm,
            start_mm=lo, end_mm=hi,
            depth_low=0 if c.object_id in on_outer else 1,
            depth_high=1 if c.object_id in on_outer else 2,
            roles=tuple(roles), evidence=tuple(ev)))

    rep.notes["how_the_site_line_is_found"] = (
        "remove the outermost boundary and look again. If every room "
        "observation is still enclosed, that boundary was never holding a "
        "room in — it is ground, not fabric. This is §6's rule stated "
        "directly, and it compares no sizes")
    rep.notes["multiple_roles"] = (
        "a band may hold several roles at once. A building envelope is "
        "BUILDING_ENVELOPE and ROOM_BOUNDARY_ELIGIBLE, because those answer "
        "different questions")
    return rep
