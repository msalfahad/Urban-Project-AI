"""A closed polygon is not a room. What it IS, decided structurally.

Round 1 released a 443.841 m² space labelled `W.C`. Every gate it faced
passed: the enclosure was complete, the identity came from an authored
block, and no dimension contradicted it. It was the plot — its boundary was
the site line, fully drawn, so its vector support was 100%.

The missing question was never asked: **what KIND of enclosure is this?**

    SITE_OR_PLOT_ENCLOSURE   the ground the building stands on
    BUILDING_ENVELOPE        the fabric, containing rooms
    SUPER_REGION             several rooms with partitions between them,
                             enclosed together by something outer
    PHYSICAL_ROOM_CANDIDATE  one space a person occupies
    VOID_OR_SHAFT            enclosed, unoccupied, unlabelled
    DETAIL_OR_ANNOTATION     a frame round a drawing, not round a space
    UNRESOLVED               none of the above is established

THE DECIDING TEST IS CONTAINMENT, NOT SIZE

Nothing here compares an area against an expected room size, and nothing
may. A 40 m² space can be a saloon or a small plot, and the difference is
not the number.

What separates them is what the polygon CONTAINS:

  * a polygon containing several independently supported room observations,
    with supported partition material between them, cannot be ONE room —
    it is a super-region, an envelope or a site, and the distinction
    between those is further containment;
  * a polygon containing another enclosure is not a leaf and cannot be a
    room;
  * a polygon containing exactly one room-like observation, no nested
    enclosure and no internal partition network is a room CANDIDATE.

That is §3's invariant, and it is scale-free: it fires the same way on a
2 m² shaft and on a 500 m² plot.

FALSE RELEASE IS WORSE THAN ZERO RELEASE. Every ambiguity below resolves to
UNRESOLVED, and UNRESOLVED releases nothing.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

CLASSIFIER = "ENCLOSURE_ROLE_CLASSIFIER_V1"

SITE_OR_PLOT = "SITE_OR_PLOT_ENCLOSURE"
BUILDING_ENVELOPE = "BUILDING_ENVELOPE"
PHYSICAL_ROOM = "PHYSICAL_ROOM_CANDIDATE"
VOID_OR_SHAFT = "VOID_OR_SHAFT"
DETAIL_OR_ANNOTATION = "DETAIL_OR_ANNOTATION"
SUPER_REGION = "SUPER_REGION"
UNRESOLVED = "UNRESOLVED"

# Only one of these may ever be released as a room.
RELEASABLE_ROLE = PHYSICAL_ROOM

# A partition counts as separating two observations when drawn material
# lies between them. Half a metre of it: shorter than any built partition
# and long enough that a dimension tick cannot masquerade as one.
MIN_SEPARATING_MATERIAL_MM = 500.0

WHY = {
    SITE_OR_PLOT: (
        "it contains at least one other enclosure that itself contains "
        "rooms, and nothing contains it. It is the ground, not a space"),
    BUILDING_ENVELOPE: (
        "it contains several room observations separated by partitions, and "
        "it sits inside a larger enclosure. It is the fabric, not a room"),
    SUPER_REGION: (
        "it contains several independently supported room observations with "
        "supported partition material between them. Whatever it is, it is "
        "not ONE physical room"),
    PHYSICAL_ROOM: (
        "it contains exactly one room-like observation, no nested "
        "enclosure, and no internal partition network. It is a candidate — "
        "which is not the same as released"),
    VOID_OR_SHAFT: (
        "it is fully enclosed and carries no room-like observation at all"),
    DETAIL_OR_ANNOTATION: (
        "what it contains is annotation rather than space"),
    UNRESOLVED: (
        "the evidence does not establish a role. Nothing is released from "
        "here, because a false release is worse than no release"),
}


@dataclass(frozen=True)
class RoleVerdict:
    """One enclosure's role, with the structural evidence behind it."""

    enclosure_id: str
    role: str
    contained_room_observations: int
    nested_enclosures: int
    separating_partitions: int
    contained_by: tuple
    evidence: tuple
    interior_voids: int = 0

    @property
    def may_release(self) -> bool:
        return self.role == RELEASABLE_ROLE

    def record(self) -> dict:
        return {
            "enclosure_id": self.enclosure_id,
            "enclosure_role": self.role,
            "why": WHY.get(self.role, ""),
            "contains_room_observations": self.contained_room_observations,
            "contains_other_enclosures": self.nested_enclosures,
            "internal_separating_partitions": self.separating_partitions,
            "interior_voids": self.interior_voids,
            "contained_by": list(self.contained_by),
            "evidence": list(self.evidence),
            "may_release_as_a_room": self.may_release,
        }


@dataclass
class RoleReport:
    verdicts: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def by_role(self) -> dict:
        return dict(Counter(v.role for v in self.verdicts).most_common())

    def record(self) -> dict:
        return {
            "classifier": CLASSIFIER,
            "ENCLOSURE_ROLE_CLASSIFIER_HASH": classifier_hash(),
            "enclosures_classified": len(self.verdicts),
            "by_role": self.by_role(),
            "releasable_role": RELEASABLE_ROLE,
            "verdicts": [v.record() for v in self.verdicts],
            "frozen_parameters": frozen_parameters(),
            "notes": dict(self.notes),
            "invariant": (
                "a candidate containing several independently supported "
                "physical-space observations separated by supported "
                "partitions can NEVER be released as one physical room"),
        }


def frozen_parameters() -> dict:
    return {
        "CLASSIFIER": CLASSIFIER,
        "MIN_SEPARATING_MATERIAL_MM": MIN_SEPARATING_MATERIAL_MM,
        "why": {
            "MIN_SEPARATING_MATERIAL_MM": (
                "shorter than any built partition, long enough that a "
                "dimension tick cannot masquerade as one"),
            "no_size_test_exists": (
                "no area, no principal dimension and no expected room size "
                "takes part in any decision here. A 40 m2 polygon may be a "
                "saloon or a small plot and the number does not say which"),
        },
    }


def classifier_hash() -> str:
    parts = [CLASSIFIER, SITE_OR_PLOT, BUILDING_ENVELOPE, PHYSICAL_ROOM,
             VOID_OR_SHAFT, DETAIL_OR_ANNOTATION, SUPER_REGION, UNRESOLVED,
             str(MIN_SEPARATING_MATERIAL_MM)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _interior_voids(polygon_wkt: str) -> int:
    """How many enclosed things the flood could not enter."""
    from shapely.wkt import loads

    try:
        poly = loads(polygon_wkt)
    except Exception:       # noqa: BLE001
        return 0
    return len(getattr(poly, "interiors", ()) or ())


def _contains(outer, inner_pt) -> bool:
    from shapely.geometry import Point
    from shapely.wkt import loads

    try:
        return loads(outer).contains(Point(inner_pt))
    except Exception:       # noqa: BLE001 - an unreadable polygon contains nothing
        return False


def _separating(polygon_wkt: str, points, candidates) -> int:
    """Count drawn lines that run BETWEEN the observations inside a polygon.

    A partition separates two observations when a drawn line crosses the
    straight path from one to the other. That is a topological statement —
    "you cannot walk from this label to that one without crossing drawn
    material" — and it needs no size comparison.
    """
    if len(points) < 2:
        return 0
    from shapely.geometry import LineString
    from shapely.wkt import loads

    try:
        poly = loads(polygon_wkt)
    except Exception:       # noqa: BLE001
        return 0
    found = 0
    for i, a in enumerate(points):
        for b in points[i + 1:]:
            path = LineString([a, b])
            for c in candidates:
                if c.length_mm < MIN_SEPARATING_MATERIAL_MM:
                    continue
                if c.axis == "H":
                    seg = LineString([(c.start_mm, c.fixed_mm),
                                      (c.end_mm, c.fixed_mm)])
                else:
                    seg = LineString([(c.fixed_mm, c.start_mm),
                                      (c.fixed_mm, c.end_mm)])
                if not seg.intersects(path):
                    continue
                if not poly.intersects(seg):
                    continue
                found += 1
                break
    return found


def classify(enclosures, observations, candidates=()) -> RoleReport:
    """Give every enclosure a role from what it contains.

    `enclosures` are (enclosure_id, polygon_wkt) pairs. `observations` are
    the ROOM_LIKE semantic observations, each with `.x` and `.y`. Nothing
    here reads an area.
    """
    rep = RoleReport()
    polys = [(eid, wkt) for eid, wkt in enclosures if wkt]

    # Which observations, and which other enclosures, does each contain.
    inside_obs: dict = {}
    for eid, wkt in polys:
        inside_obs[eid] = [o for o in observations if _contains(wkt, (o.x, o.y))]

    nested: dict = {eid: [] for eid, _ in polys}
    containers: dict = {eid: [] for eid, _ in polys}
    from shapely.wkt import loads

    shapes = {}
    for eid, wkt in polys:
        try:
            shapes[eid] = loads(wkt)
        except Exception:   # noqa: BLE001
            continue
    for eid, shape in shapes.items():
        for other, other_shape in shapes.items():
            if other == eid:
                continue
            # A representative interior point avoids boundary-touch noise.
            if shape.contains(other_shape.representative_point()) and \
                    shape.area > other_shape.area:
                nested[eid].append(other)
                containers[other].append(eid)

    for eid, wkt in polys:
        obs = inside_obs.get(eid, [])
        pts = [(o.x, o.y) for o in obs]
        parts = _separating(wkt, pts, candidates)
        kids = nested.get(eid, [])
        owners = containers.get(eid, [])
        ev = [f"contains {len(obs)} room-like observation(s)",
              f"contains {len(kids)} other enclosure(s)",
              f"{parts} drawn partition(s) separate observations inside it",
              f"contained by {len(owners)} enclosure(s)"]

        # A HOLE IN THE POLYGON MEANS SOMETHING IS INSIDE IT.
        #
        # The flood could not enter it, so something enclosed stands there:
        # a courtyard, a shaft, a stair core, a column. Which of those it is
        # cannot be settled without a size comparison, and size comparisons
        # are forbidden here — so the enclosure is UNRESOLVED rather than
        # guessed at. This is deliberately conservative: a room with a
        # column in it will not release, and a false release is worse.
        voids = _interior_voids(wkt)
        if voids:
            ev.append(f"{voids} interior void(s): the flood could not enter "
                      "something enclosed inside this polygon. Whether that "
                      "is a courtyard, a shaft or a column is not "
                      "establishable without comparing sizes, which this "
                      "classifier may not do")
            rep.verdicts.append(RoleVerdict(
                enclosure_id=eid, role=UNRESOLVED,
                contained_room_observations=len(obs),
                nested_enclosures=len(kids), separating_partitions=parts,
                contained_by=tuple(owners), evidence=tuple(ev),
                interior_voids=voids))
            continue

        if len(obs) >= 2 and parts >= 1:
            # The invariant of §3, before anything else can claim it.
            if kids and not owners:
                role = SITE_OR_PLOT
                ev.append("it contains other enclosures and nothing contains "
                          "it, so it is the outermost thing on the sheet")
            elif kids:
                role = BUILDING_ENVELOPE
                ev.append("it contains other enclosures and sits inside a "
                          "larger one, so it is fabric rather than ground")
            else:
                role = SUPER_REGION
                ev.append("several supported room observations with drawn "
                          "material between them cannot be one room")
        elif kids:
            role = (SITE_OR_PLOT if not owners else BUILDING_ENVELOPE)
            ev.append("it contains another enclosure, so it is not a leaf "
                      "space and cannot be a room")
        elif len(obs) == 1 and parts == 0:
            role = PHYSICAL_ROOM
            ev.append("one room-like observation, nothing nested, no "
                      "internal partition — a candidate, not a release")
        elif not obs:
            role = VOID_OR_SHAFT
            ev.append("fully enclosed and carrying no room-like observation")
        else:
            role = UNRESOLVED
            ev.append("the evidence does not settle what this is")

        rep.verdicts.append(RoleVerdict(
            enclosure_id=eid, role=role,
            contained_room_observations=len(obs), nested_enclosures=len(kids),
            separating_partitions=parts, contained_by=tuple(owners),
            evidence=tuple(ev), interior_voids=voids))

    rep.notes["no_size_test"] = (
        "no area or dimension took part in any verdict above. The decision "
        "is containment, which is scale-free: it fires the same way on a "
        "2 m2 shaft and on a 500 m2 plot")
    return rep
