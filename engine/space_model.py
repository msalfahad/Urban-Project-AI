"""E47 — three things the system was calling one thing.

The workbook said `WASHROOM = 1`. A human had verified that label, so the count
looked trustworthy. But the region it is attached to is the hatched shaft beside
the washroom: geometrically the engine has recovered ZERO validated washroom
polygons. The workbook was telling the owner "1 washroom detected" on the
strength of a label alone.

The error was not in the count. It was that one record was being asked to be
three different things at once:

    SEMANTIC_OBSERVATION   a name read off the drawing. Evidence that a room of
                           this kind EXISTS. Says nothing about geometry.
    PHYSICAL_SPACE         a polygon with validated identity and topology. The
                           only thing a quantity may be attributed to.
    FUNCTIONAL_ZONE        a use of space. A dining zone is real to the owner
                           and to the trades, and it may share one open polygon
                           with a saloon and a corridor.

Keeping them apart answers the question the owner actually asks — "how many
bathrooms?" — with three honest numbers instead of one misleading one:

    WASHROOM   semantic observations 1
               validated physical spaces 0
               topology unresolved 1

TWO RULES THIS MODULE ENFORCES:

  A LABEL IS NOT A ROOM. A semantic observation never becomes a physical space
  by being confident, human-verified, or repeated.

  A ZONE IS NOT A WALL. Functional zones subdivide use, never geometry. A
  dining zone inside an open-plan space must not create a boundary the building
  does not have — that would invent wall length, and inventing wall length is
  how a takeoff becomes fiction.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# How far a polygon has got. These are LAYERS, not one "geometry ready" flag —
# the dashboard reported 36 ready and 0 unresolved while the same workbook
# recorded WSH-01 as UNRESOLVED, because "a raster region exists" was being
# printed as "the physical space is validated".
RASTER_REGION_AVAILABLE = "RASTER_REGION_AVAILABLE"
WALL_GEOMETRY_AVAILABLE = "WALL_GEOMETRY_AVAILABLE"
REGION_IDENTITY_VALIDATED = "REGION_IDENTITY_VALIDATED"
PHYSICAL_TOPOLOGY_VALIDATED = "PHYSICAL_TOPOLOGY_VALIDATED"

GEOMETRY_LAYERS = (RASTER_REGION_AVAILABLE, WALL_GEOMETRY_AVAILABLE,
                   REGION_IDENTITY_VALIDATED, PHYSICAL_TOPOLOGY_VALIDATED)

# Why a physical space is not validated. Each is a different repair.
IDENTITY_WRONG_REGION = "REGION_IS_NOT_THIS_SPACE"
TOPOLOGY_MERGED = "REGION_MERGES_TWO_OR_MORE_SPACES"
TOPOLOGY_SPLIT = "SPACE_IS_SPLIT_ACROSS_REGIONS"
NOT_RECOVERED = "SPACE_NOT_RECOVERED_AT_ALL"
UNRESOLVED = "UNRESOLVED"

# Where a semantic label came from.
AI_INFERRED = "AI_INFERRED"
PDF_TEXT = "PDF_TEXT"
CAD_TEXT = "CAD_TEXT"
HUMAN_VERIFIED = "HUMAN_VERIFIED"
HUMAN_ASSIGNED = "HUMAN_ASSIGNED"
SEMANTIC_UNRESOLVED = "UNRESOLVED"


class SpaceModelError(RuntimeError):
    """A label was asked to be a room, or a zone was asked to be a wall."""


@dataclass(frozen=True)
class SemanticObservation:
    """A room name read off the drawing. Evidence, not geometry.

    It carries a `region_id` because that is where the name was seen — NOT
    because the name and the region have been shown to belong together. That
    is exactly the claim WSH-01 falsified.
    """

    observation_id: str
    room_type: str
    name_en: str = ""
    name_ar: str = ""
    source: str = SEMANTIC_UNRESOLVED
    seen_at_region: int | None = None
    confidence: float | None = None

    @property
    def is_human(self) -> bool:
        return self.source in (HUMAN_VERIFIED, HUMAN_ASSIGNED)

    def record(self) -> dict:
        return {"observation_id": self.observation_id,
                "room_type": self.room_type, "name_en": self.name_en,
                "source": self.source, "seen_at_region": self.seen_at_region,
                "confidence": self.confidence}


@dataclass(frozen=True)
class PhysicalSpace:
    """A polygon, and how far it has been validated as a real room.

    `validated` is the gate. Only a validated physical space may carry a
    released quantity; everything else may carry an OBSERVATION and nothing
    more.
    """

    space_id: str
    region_id: int | None
    scope: str
    layers: frozenset = frozenset()
    unresolved_reason: str = ""
    room_type: str = ""
    area_m2: float | None = None

    @property
    def validated(self) -> bool:
        """Both identity and topology. Either alone is not a room.

        Identity says the polygon is the space we named. Topology says it is
        the WHOLE of that space and ONLY that space. WSH-01 fails the first;
        BED-04 fails the second; both were released as ready.
        """
        return (REGION_IDENTITY_VALIDATED in self.layers
                and PHYSICAL_TOPOLOGY_VALIDATED in self.layers)

    @property
    def measurable(self) -> bool:
        """A polygon exists and can be measured — which is not the same thing
        as the measurement meaning what its name says."""
        return RASTER_REGION_AVAILABLE in self.layers

    def geometry_status(self) -> dict:
        """Each layer separately. Never collapsed into one KPI."""
        return {layer: layer in self.layers for layer in GEOMETRY_LAYERS}

    def record(self) -> dict:
        return {"space_id": self.space_id, "region_id": self.region_id,
                "scope": self.scope, "room_type": self.room_type,
                "area_m2": self.area_m2, "validated": self.validated,
                "unresolved_reason": self.unresolved_reason,
                **self.geometry_status()}


@dataclass(frozen=True)
class FunctionalZone:
    """A use of space. Shares a polygon; never creates one.

    OPEN-01 is one physical polygon holding a dining zone, a saloon zone and a
    circulation zone. The owner wants to count all three. Forcing the polygon to
    carry a single room_type loses two of them; letting a zone draw its own
    boundary would invent wall length that the building does not have.
    """

    zone_id: str
    physical_space_id: str
    function: str
    basis: str = ""
    area_m2: float | None = None
    boundary_is_physical: bool = False

    def __post_init__(self):
        if self.boundary_is_physical:
            raise SpaceModelError(
                f"{self.zone_id}: a functional zone may not declare a physical "
                "boundary. A dining zone inside an open-plan space is a use, "
                "not a wall, and giving it one would invent wall length the "
                "building does not have")

    def record(self) -> dict:
        return {"zone_id": self.zone_id,
                "physical_space_id": self.physical_space_id,
                "function": self.function, "basis": self.basis,
                "area_m2": self.area_m2,
                "creates_wall_boundary": False}


@dataclass
class SpaceModel:
    """The three layers together, and the counts that tell the truth."""

    observations: list[SemanticObservation] = field(default_factory=list)
    spaces: list[PhysicalSpace] = field(default_factory=list)
    zones: list[FunctionalZone] = field(default_factory=list)

    def zones_of(self, space_id: str) -> list[FunctionalZone]:
        return [z for z in self.zones if z.physical_space_id == space_id]

    def room_counts(self) -> list[dict]:
        """Per room type: what was SEEN, what was VALIDATED, and what is broken.

        These three numbers routinely disagree, and the disagreement is the
        useful part. A type with observations and no validated spaces is a room
        the engine believes exists and cannot measure.
        """
        types = sorted({o.room_type for o in self.observations}
                       | {s.room_type for s in self.spaces if s.room_type}
                       | {z.function for z in self.zones})
        out = []
        for rt in types:
            obs = [o for o in self.observations if o.room_type == rt]
            sp = [s for s in self.spaces if s.room_type == rt]
            validated = [s for s in sp if s.validated]
            unresolved = [s for s in sp if not s.validated]
            zones = [z for z in self.zones if z.function == rt]
            out.append({
                "room_type": rt,
                "semantic_observations": len(obs),
                "validated_physical_spaces": len(validated),
                "unresolved_physical_spaces": len(unresolved),
                "functional_zones": len(zones),
                "in_scope_validated": sum(1 for s in validated
                                          if s.scope == "IN_SCOPE"),
                "out_of_scope": sum(1 for s in sp if s.scope == "OUT_OF_SCOPE"),
                "ambiguous": sum(1 for s in sp if s.scope == "AMBIGUOUS"),
                "unresolved_reasons": sorted({s.unresolved_reason
                                              for s in unresolved
                                              if s.unresolved_reason}),
            })
        return out

    def geometry_summary(self) -> dict:
        """The dashboard's geometry block, one line per layer.

        "Geometry ready = 36" was true only of the first layer and was being
        printed as though it were the last.
        """
        out = {layer: sum(1 for s in self.spaces if layer in s.layers)
               for layer in GEOMETRY_LAYERS}
        out["total_spaces"] = len(self.spaces)
        out["validated_physical_spaces"] = sum(
            1 for s in self.spaces if s.validated)
        out["unresolved_reasons"] = dict(Counter(
            s.unresolved_reason for s in self.spaces
            if not s.validated and s.unresolved_reason))
        return out

    def check(self) -> list[str]:
        """Contradictions between the layers. Empty is the only good answer."""
        out = []
        ids = {s.space_id for s in self.spaces}
        for z in self.zones:
            if z.physical_space_id not in ids:
                out.append(f"{z.zone_id} names physical space "
                           f"{z.physical_space_id}, which does not exist")
        for s in self.spaces:
            if not s.validated and not s.unresolved_reason:
                out.append(f"{s.space_id} is not validated and does not say why")
            if s.validated and s.unresolved_reason:
                out.append(f"{s.space_id} is validated and still carries an "
                           f"unresolved reason: {s.unresolved_reason}")
        return out
