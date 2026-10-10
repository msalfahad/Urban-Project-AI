"""E54 — a closed polygon is not a room, and the label beside it is not proof.

The regression that forced this module:

    WSH-01  ->  VALIDATED_PHYSICAL_FACE

The engine found a genuinely valid closed vector cycle of 1.981 m2 and called
it a validated washroom. But WSH-01's associated raster region is the HATCHED
SHAFT BESIDE the washroom — an established project fact for several rounds. So
the cycle was probably a perfectly good shaft, and the washroom's geometry was
never recovered at all.

Nothing about the geometry was wrong. One field was answering two questions:

    IS THIS A VALID CLOSED FACE?        a question about geometry
    IS THIS FACE THE ROOM WE NAMED?     a question about identity

They are independent, and they fail independently:

    shaft cycle      geometry VALIDATED   identity as WASHROOM  REJECTED
    normal bedroom   geometry VALIDATED   identity as BEDROOM   PROBABLE
    sliver           geometry INVALID     identity              UNRESOLVED

So a quantity needs BOTH, and `PHYSICAL_SPACE_GEOMETRY_ACCEPTED` is the state
that requires both — never either one alone.

    A CLOSED POLYGON PLUS A LABEL NEARBY IS NOT A VALIDATED PHYSICAL SPACE.

And centroid containment is NOT identity evidence on its own. A face holding
exactly one label can still be a shaft, a closet, an adjacent enclosure, a
wrongly nested cycle, or the wrong side of a wall. One label inside one cycle
is a CANDIDATE and stays one until independent families agree.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

# ------------------------------------------------------------ geometry axis

# Is this a face at all, and is it sound?
CLOSED_VECTOR_CYCLE = "CLOSED_VECTOR_CYCLE"
VALIDATED_GEOMETRIC_FACE = "VALIDATED_GEOMETRIC_FACE"
AMBIGUOUS_GEOMETRIC_FACE = "AMBIGUOUS_GEOMETRIC_FACE"
INVALID_GEOMETRIC_FACE = "INVALID_GEOMETRIC_FACE"

GEOMETRY_STATES = (INVALID_GEOMETRIC_FACE, AMBIGUOUS_GEOMETRIC_FACE,
                   CLOSED_VECTOR_CYCLE, VALIDATED_GEOMETRIC_FACE)
GEOMETRY_RANK = {s: i for i, s in enumerate(GEOMETRY_STATES)}

# ------------------------------------------------------------ identity axis

# Is this face the space we named?
IDENTITY_VALIDATED = "IDENTITY_VALIDATED"
IDENTITY_PROBABLE = "IDENTITY_PROBABLE"
IDENTITY_AMBIGUOUS = "IDENTITY_AMBIGUOUS"
IDENTITY_REJECTED = "IDENTITY_REJECTED"
IDENTITY_UNRESOLVED = "IDENTITY_UNRESOLVED"

IDENTITY_STATES = (IDENTITY_REJECTED, IDENTITY_UNRESOLVED, IDENTITY_AMBIGUOUS,
                   IDENTITY_PROBABLE, IDENTITY_VALIDATED)
IDENTITY_RANK = {s: i for i, s in enumerate(IDENTITY_STATES)}

# The combined state a quantity may consume. It requires both axes and is
# never reachable from one of them.
PHYSICAL_SPACE_GEOMETRY_ACCEPTED = "PHYSICAL_SPACE_GEOMETRY_ACCEPTED"
NOT_ACCEPTED = "NOT_ACCEPTED"

MIN_GEOMETRY_FOR_ACCEPTANCE = VALIDATED_GEOMETRIC_FACE
MIN_IDENTITY_FOR_ACCEPTANCE = IDENTITY_PROBABLE

# ------------------------------------------------------- identity evidence

# Families, as everywhere. The point of naming them is that they must be
# INDEPENDENT of each other: a semantic label and the centroid containment of
# that same label are one observation seen twice.
E_LABEL_ANCHOR = "SEMANTIC_LABEL_ANCHORED_INSIDE_THE_FACE"
E_RASTER_CORRESPONDENCE = "RASTER_REGION_ONE_TO_ONE_WITH_THIS_FACE"
E_RASTER_OVERLAP = "VECTOR_FACE_RASTER_POLYGON_OVERLAP_ABOVE_THRESHOLD"
E_ADJACENCY = "WALL_AND_PORTAL_ADJACENCY_MATCHES_THE_EXPECTED_NEIGHBOURS"
E_PRINTED_DIMENSIONS = "PRINTED_DIMENSIONS_MATCH_THIS_FACE"
E_ROOM_SCHEDULE = "ROOM_SCHEDULE_ENTRY_MATCHES_THIS_FACE"
E_CAD_ROOM_OBJECT = "CAD_ROOM_OBJECT_NAMES_THIS_FACE"

FAMILY_SEMANTIC = "SEMANTIC"
FAMILY_RASTER = "RASTER"
FAMILY_TOPOLOGY = "TOPOLOGY"
FAMILY_DOCUMENT = "DOCUMENT"
FAMILY_CAD = "CAD_ENTITY"

EVIDENCE_FAMILY = {
    E_LABEL_ANCHOR: FAMILY_SEMANTIC,
    E_RASTER_CORRESPONDENCE: FAMILY_RASTER,
    E_RASTER_OVERLAP: FAMILY_RASTER,
    E_ADJACENCY: FAMILY_TOPOLOGY,
    E_PRINTED_DIMENSIONS: FAMILY_DOCUMENT,
    E_ROOM_SCHEDULE: FAMILY_DOCUMENT,
    E_CAD_ROOM_OBJECT: FAMILY_CAD,
}

# APPROVED COMBINATIONS. Read the exclusions first: SEMANTIC alone is what the
# WSH-01 regression was built on, and RASTER alone is what put the label on
# the shaft in the first place.
COMBINATIONS = {
    frozenset({FAMILY_SEMANTIC, FAMILY_DOCUMENT}): IDENTITY_VALIDATED,
    frozenset({FAMILY_CAD, FAMILY_SEMANTIC}): IDENTITY_VALIDATED,
    frozenset({FAMILY_CAD, FAMILY_DOCUMENT}): IDENTITY_VALIDATED,
    frozenset({FAMILY_SEMANTIC, FAMILY_RASTER,
               FAMILY_TOPOLOGY}): IDENTITY_VALIDATED,
    frozenset({FAMILY_SEMANTIC, FAMILY_RASTER}): IDENTITY_PROBABLE,
    frozenset({FAMILY_SEMANTIC, FAMILY_TOPOLOGY}): IDENTITY_PROBABLE,
    frozenset({FAMILY_RASTER, FAMILY_TOPOLOGY}): IDENTITY_AMBIGUOUS,
}


class SpaceIdentityError(RuntimeError):
    """An identity was asserted on evidence that cannot carry it."""


def _best(fams: frozenset):
    """The strongest approved combination CONTAINED IN this evidence.

    Monotonic on purpose: adding an observation must never lower a status.
    """
    hits = [(IDENTITY_RANK[v], v, k) for k, v in COMBINATIONS.items()
            if k <= fams]
    if not hits:
        return None
    _, status, key = max(hits, key=lambda h: (h[0], len(h[2])))
    return status, key


def identity_status(families, *, rejected_by: str = "") -> tuple[str, str]:
    """How well is this face's identity supported — and can it be rejected?

    `rejected_by` is a stated contradiction: a known defect, a golden fixture,
    or a reviewer saying this region is not that room. A rejection outranks
    every amount of supporting evidence, because the supporting evidence is
    exactly what was wrong.
    """
    if rejected_by:
        return IDENTITY_REJECTED, (
            f"rejected: {rejected_by}. A contradiction outranks accumulated "
            "support — the support is what was mistaken")
    fams = frozenset(families)
    if not fams:
        return IDENTITY_UNRESOLVED, "no identity evidence of any kind"
    best = _best(fams)
    if best is not None:
        status, key = best
        return status, (
            f"{'+'.join(sorted(key))} is an approved identity combination"
            + (f" (with {'+'.join(sorted(fams - key))} also present)"
               if fams - key else ""))
    if len(fams) == 1:
        only = next(iter(fams))
        return IDENTITY_AMBIGUOUS, (
            f"{only} alone. A face holding one semantic label can still be a "
            "shaft, a closet, an adjacent enclosure, a wrongly nested cycle "
            "or the wrong side of a wall")
    return IDENTITY_AMBIGUOUS, (
        f"{'+'.join(sorted(fams))} is not an approved identity combination")


@dataclass(frozen=True)
class SpaceIdentity:
    """One (face, claimed space) verdict on BOTH axes, kept apart."""

    space_face_id: str
    claimed_space_id: str
    geometry_status: str
    identity_status: str
    identity_evidence: tuple[str, ...] = ()
    geometry_blockers: tuple[str, ...] = ()
    identity_blockers: tuple[str, ...] = ()
    rejected_by: str = ""
    why_geometry: str = ""
    why_identity: str = ""

    @property
    def families(self) -> set:
        return {EVIDENCE_FAMILY[e] for e in self.identity_evidence
                if e in EVIDENCE_FAMILY}

    @property
    def acceptance(self) -> str:
        """PHYSICAL_SPACE_GEOMETRY_ACCEPTED requires BOTH axes. Never one."""
        geo_ok = (GEOMETRY_RANK[self.geometry_status]
                  >= GEOMETRY_RANK[MIN_GEOMETRY_FOR_ACCEPTANCE])
        id_ok = (IDENTITY_RANK[self.identity_status]
                 >= IDENTITY_RANK[MIN_IDENTITY_FOR_ACCEPTANCE])
        return (PHYSICAL_SPACE_GEOMETRY_ACCEPTED if geo_ok and id_ok
                else NOT_ACCEPTED)

    @property
    def accepted(self) -> bool:
        return self.acceptance == PHYSICAL_SPACE_GEOMETRY_ACCEPTED

    @property
    def why_not_accepted(self) -> str:
        if self.accepted:
            return ""
        geo_ok = (GEOMETRY_RANK[self.geometry_status]
                  >= GEOMETRY_RANK[MIN_GEOMETRY_FOR_ACCEPTANCE])
        id_ok = (IDENTITY_RANK[self.identity_status]
                 >= IDENTITY_RANK[MIN_IDENTITY_FOR_ACCEPTANCE])
        if geo_ok and not id_ok:
            return (f"the geometry is sound and the identity is not: this is "
                    f"a valid face whose claim to be {self.claimed_space_id} "
                    f"is {self.identity_status}")
        if id_ok and not geo_ok:
            return (f"the identity is supported and the geometry is "
                    f"{self.geometry_status}: there is no sound polygon to "
                    "attribute to it")
        return (f"neither axis is sufficient: geometry {self.geometry_status}, "
                f"identity {self.identity_status}")

    def record(self) -> dict:
        return {"space_face_id": self.space_face_id,
                "claimed_space_id": self.claimed_space_id,
                "vector_face_geometry_status": self.geometry_status,
                "physical_space_identity_status": self.identity_status,
                "identity_evidence": list(self.identity_evidence),
                "identity_families": sorted(self.families),
                "geometry_blockers": list(self.geometry_blockers),
                "identity_blockers": list(self.identity_blockers),
                "rejected_by": self.rejected_by,
                "acceptance": self.acceptance,
                "why_geometry": self.why_geometry,
                "why_identity": self.why_identity,
                "why_not_accepted": self.why_not_accepted}


def summary(verdicts) -> dict:
    """The two axes counted SEPARATELY, and the conjunction counted once.

    Reporting one number for "validated faces" is what produced a validated
    washroom that was a shaft.
    """
    return {
        "verdicts": len(verdicts),
        "by_geometry_status": dict(Counter(
            v.geometry_status for v in verdicts)),
        "by_identity_status": dict(Counter(
            v.identity_status for v in verdicts)),
        "geometry_sound_identity_not": sum(
            1 for v in verdicts
            if GEOMETRY_RANK[v.geometry_status]
            >= GEOMETRY_RANK[MIN_GEOMETRY_FOR_ACCEPTANCE] and not v.accepted),
        "physical_space_geometry_accepted": sum(
            1 for v in verdicts if v.accepted),
        "identity_rejected": sum(
            1 for v in verdicts if v.identity_status == IDENTITY_REJECTED),
        "note": ("a closed polygon plus a nearby label is NOT a validated "
                 "physical space. Both axes must pass, and they fail "
                 "independently"),
    }
