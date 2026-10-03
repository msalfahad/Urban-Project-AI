"""E52 — a bounding box is an index, never a room.

The forensic result that retired the bbox model:

    STR-01   fills  67.6%  of its bounding box
    OPEN-01         69.4%
    BED-01          77.3%
    BTH-05          89.4%

STR-01's "2606 mm missing wall" was never a missing wall. STR-01 is L-shaped,
and the east edge of its bounding box runs through open space where the
building never had a wall:

        +-----------+ . . . . +          the dotted run is the bbox edge.
        |           |         .          No wall was ever meant to be there,
        |           +---------+          and measuring the room against it
        |                     |          invented a defect.
        +---------------------+

The engine measured a room against a rectangle it is not, then reported the
difference as a construction fact. That is a whole class of error, not one bad
number, so the class is closed here rather than the number patched.

    BBOX IS NEVER PHYSICAL GEOMETRY.

A bounding box may still index, search and debug. It may NEVER produce a room
side, a room perimeter, a room closure, a room area, or a missing-wall
conclusion — unless the space has been INDEPENDENTLY PROVEN rectangular, which
is a separate fact with its own evidence and is not the default.

The same refusal applies one step along, to the obvious next move: "the bbox
was wrong, so use the raster outline as the room boundary". A raster region can
have the wrong physical identity — WSH-01's region is the shaft beside the
washroom — so a raster outline localises a search and compares against a
result. It does not construct one. See `engine.space_graph`, where the real
polygons come from wall bands, supported portals and planar topology.
"""

from __future__ import annotations

from dataclasses import dataclass

# How a bounding box may be used. The first three are safe at any time; the
# last four are the physical claims this module exists to refuse.
INDEXING = "SPATIAL_INDEXING"
LOCAL_SEARCH = "LOCAL_SEARCH"
DEBUG = "DEBUG_DISPLAY"

PERMITTED_USES = (INDEXING, LOCAL_SEARCH, DEBUG)

ROOM_SIDES = "ROOM_SIDES"
ROOM_PERIMETER = "ROOM_PERIMETER"
ROOM_CLOSURE = "ROOM_CLOSURE"
ROOM_AREA = "ROOM_AREA"
MISSING_WALL = "MISSING_WALL_CONCLUSION"

PHYSICAL_USES = (ROOM_SIDES, ROOM_PERIMETER, ROOM_CLOSURE, ROOM_AREA,
                 MISSING_WALL)

# How a space earned the right to be treated as its own bounding box.
RECTANGULARITY_UNPROVEN = "RECTANGULARITY_UNPROVEN"
RECTANGULAR_BY_VECTOR_FACE = "RECTANGULAR_BY_VECTOR_FACE"
RECTANGULAR_BY_PRINTED_DIMENSIONS = "RECTANGULAR_BY_PRINTED_DIMENSIONS"

RECTANGULARITY_PROOFS = (RECTANGULAR_BY_VECTOR_FACE,
                         RECTANGULAR_BY_PRINTED_DIMENSIONS)

# A fill ratio this high does not PROVE a rectangle. It is the threshold below
# which the engine will not even discuss one, and it is reported so a reader
# can see how far a region is from the box that contains it.
FILL_RATIO_WORTH_REPORTING = 0.85


class BoundingBoxError(RuntimeError):
    """A bounding box was asked to be a room."""


@dataclass(frozen=True)
class BoundingBox:
    """A rectangle that CONTAINS a space. It is not the space.

    Construct one freely — indexing needs them everywhere. The guard is on the
    way out: `physical(use)` refuses every physical question unless this box
    carries an independent proof that the space really is rectangular.
    """

    space_id: str
    x0_mm: float
    y0_mm: float
    x1_mm: float
    y1_mm: float
    fill_ratio: float | None = None
    rectangularity: str = RECTANGULARITY_UNPROVEN
    proof: str = ""

    @property
    def width_mm(self) -> float:
        return abs(self.x1_mm - self.x0_mm)

    @property
    def height_mm(self) -> float:
        return abs(self.y1_mm - self.y0_mm)

    @property
    def is_proven_rectangular(self) -> bool:
        return self.rectangularity in RECTANGULARITY_PROOFS and bool(self.proof)

    def index_extent(self) -> tuple[float, float, float, float]:
        """The box, for searching and indexing. Always allowed."""
        return (self.x0_mm, self.y0_mm, self.x1_mm, self.y1_mm)

    def physical(self, use: str) -> tuple[float, float, float, float]:
        """The box as physical geometry — refused unless rectangularity is proven.

        The refusal names STR-01 on purpose. The next person to reach for a
        bbox side will be doing it for a good local reason, and the message has
        to be specific enough to stop them.
        """
        if use not in PHYSICAL_USES:
            raise BoundingBoxError(
                f"unknown physical use {use!r}. Known: {PHYSICAL_USES}. If it "
                "is not a physical question, use index_extent()")
        if not self.is_proven_rectangular:
            pct = ("" if self.fill_ratio is None
                   else f" It fills {100 * self.fill_ratio:.0f}% of this box.")
            raise BoundingBoxError(
                f"{self.space_id} has not been proven rectangular, so its "
                f"bounding box may not supply {use}.{pct} BBOX IS NEVER "
                "PHYSICAL GEOMETRY: STR-01's 2606 mm 'missing wall' was the "
                "east edge of a box cutting through open space in an L-shaped "
                "room. Build the boundary from wall bands, supported portals "
                "and planar topology instead")
        return (self.x0_mm, self.y0_mm, self.x1_mm, self.y1_mm)

    def record(self) -> dict:
        return {"space_id": self.space_id,
                "bbox_mm": [round(v, 1) for v in self.index_extent()],
                "fill_ratio": self.fill_ratio,
                "rectangularity": self.rectangularity,
                "proof": self.proof,
                "may_supply_physical_geometry": self.is_proven_rectangular,
                "permitted_uses": list(PERMITTED_USES)}


def prove_rectangular(box: BoundingBox, *, basis: str, proof: str
                      ) -> BoundingBox:
    """Grant one box the right to act as physical geometry, with its evidence.

    Deliberately explicit and deliberately per-space. There is no global switch
    and no threshold that grants it automatically: a fill ratio of 0.98 is a
    strong hint and still not a proof, because the missing 2% is exactly where
    a notch, a duct or a stub wall lives.
    """
    if basis not in RECTANGULARITY_PROOFS:
        raise BoundingBoxError(
            f"{basis!r} is not an accepted rectangularity proof. Accepted: "
            f"{RECTANGULARITY_PROOFS}. A fill ratio is NOT a proof: the "
            "missing few percent is exactly where a notch or a stub wall is")
    if not proof:
        raise BoundingBoxError(
            "a rectangularity proof must say what proved it. An unattributed "
            "proof is an assumption with better manners")
    return BoundingBox(**{**box.__dict__, "rectangularity": basis,
                          "proof": proof})


# --------------------------------------------------------- the raster rule

RASTER_MAY = (
    "localise the search for vector geometry",
    "compare against a face after it has been generated",
    "identify likely neighbourhoods to look in",
    "diagnose topology that is missing",
)
RASTER_MAY_NOT = (
    "construct the final vector room polygon",
    "supply a room side, perimeter, closure or area",
    "seed a planar face",
)


def raster_outline_refusal(space_id: str) -> str:
    """Why the raster outline is not the replacement for the bbox."""
    return (
        f"the raster outline for {space_id} may localise and compare, but it "
        "may not construct the physical polygon. WSH-01 proves a raster region "
        "can carry the wrong physical identity — its region is the shaft "
        "beside the washroom — so a raster boundary is a hint about where to "
        "look, never the answer. Final space geometry comes from WALL BANDS + "
        "SUPPORTED PORTALS + PLANAR TOPOLOGY")
