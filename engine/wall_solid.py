"""E60 — walls are polygons, and a room is a hole in their union.

THE REPLACEMENT SPINE. The old one reconstructed a planar graph from wall
centrelines and extracted faces from a hand-written rotation system. Six
invariants now say why that failed: 46 nodes with an ill-defined rotation, 40
crossings with no vertex, 92 half-edges in no walk at all.

The deeper problem was not the bugs. It was that planar face extraction is a
GLOBAL, FRAGILE mechanism computing a LOCAL, ROBUST fact. One ambiguous node
anywhere corrupts faces on the other side of the building.

So:

    each wall band  ->  the POLYGON between its two DRAWN faces
    all of them     ->  WALL_SOLID (a robust union)
    envelope - solid - portal barriers  ->  FREE SPACE
    connected components of free space  ->  SPACE GEOMETRY CANDIDATES

and a room's boundary is the boundary of its free-space component, which lies
ON the drawn wall faces by construction. No centreline offsets. No room-facing
face to determine. No corner correction. No mean thickness. The corners are
correct because they were never computed.

GEOS does the numerical geometry. This module owns construction meaning,
provenance, evidence and measurement basis — not intersection algorithms.

    NEVER MANUFACTURE A WALL THICKNESS. A band whose second face was never
    drawn has no polygon, and says WALL_POLYGON_UNRESOLVED rather than
    inventing one from an assumed centreline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Which geometry a polygon is measured on. Unchanged meaning, and the reason
# the free-space boundary needs no conversion: it already IS the finish face.
CLEAR_INTERNAL_FINISH_FACE = "CLEAR_INTERNAL_FINISH_FACE"
WALL_FACE_PAIR = "WALL_FACE_PAIR"

# Why a band could not become a polygon.
WALL_POLYGON_UNRESOLVED = "WALL_POLYGON_UNRESOLVED"
NO_SECOND_FACE = "ONLY_ONE_DRAWN_FACE"
ZERO_SEPARATION = "THE_TWO_FACES_COINCIDE"
ZERO_LENGTH = "NO_RUN_ALONG_THE_WALL_LINE"
INVALID_RING = "THE_RING_IS_NOT_A_VALID_POLYGON"

# What a band's geometry is worth once formed.
GEOMETRY_CANDIDATE = "GEOMETRY_CANDIDATE"
GEOMETRY_VALID = "GEOMETRY_VALID"
GEOMETRY_AMBIGUOUS = "GEOMETRY_AMBIGUOUS"
GEOMETRY_REJECTED = "GEOMETRY_REJECTED"

GEOMETRY_STATES = (GEOMETRY_REJECTED, GEOMETRY_AMBIGUOUS, GEOMETRY_CANDIDATE,
                   GEOMETRY_VALID)

# A band shorter or thinner than this is not a wall run worth unioning; it is
# reported, never deleted.
MIN_WALL_LENGTH_MM = 50.0
MIN_WALL_THICKNESS_MM = 40.0


class WallSolidError(RuntimeError):
    """A solid was asked to include geometry that was never established."""


@dataclass(frozen=True)
class WallPolygon:
    """One wall band as the rectangle between its two DRAWN faces.

    `ring` is in vector millimetres. The two long sides are the faces the
    architect actually drew — which is the whole point: the room boundary will
    run along them, not along an offset from a centreline.
    """

    wall_band_id: str
    ring: tuple
    axis: str
    face_a_mm: float | None
    face_b_mm: float | None
    start_mm: float
    end_mm: float
    thickness_mm: float | None = None
    separation_basis: str = ""
    geometry_basis: str = WALL_FACE_PAIR
    geometry_status: str = GEOMETRY_CANDIDATE
    source_face_ids: tuple[str, ...] = ()
    source_object_ids: tuple[str, ...] = ()
    drawing_id: str = ""
    drawing_revision: str = ""
    validation_status: str = ""
    evidence: tuple[str, ...] = ()
    occupied_intervals: tuple = ()
    extensions: tuple = ()
    unresolved_reason: str = ""
    why: str = ""

    @property
    def is_resolved(self) -> bool:
        return bool(self.ring) and not self.unresolved_reason

    @property
    def length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    def record(self) -> dict:
        return {"wall_band_id": self.wall_band_id,
                "geometry_basis": self.geometry_basis,
                "geometry_status": self.geometry_status,
                "axis": self.axis,
                "face_a_mm": (None if self.face_a_mm is None
                              else round(self.face_a_mm, 1)),
                "face_b_mm": (None if self.face_b_mm is None
                              else round(self.face_b_mm, 1)),
                "thickness_mm": (None if self.thickness_mm is None
                                 else round(self.thickness_mm, 1)),
                "separation_basis": self.separation_basis,
                "length_mm": round(self.length_mm, 1),
                "vertices": len(self.ring),
                "source_face_ids": list(self.source_face_ids),
                "source_object_ids": list(self.source_object_ids),
                "drawing_id": self.drawing_id,
                "drawing_revision": self.drawing_revision,
                "validation_status": self.validation_status,
                "evidence": list(self.evidence),
                "occupied_intervals": [list(i) for i in
                                       self.occupied_intervals],
                "extension_provenance": list(self.extensions),
                "is_resolved": self.is_resolved,
                "unresolved_reason": self.unresolved_reason,
                "why": self.why}


def wall_polygons(bands, *, drawing_id: str = "", revision: str = "",
                  min_length: float = MIN_WALL_LENGTH_MM,
                  min_thickness: float = MIN_WALL_THICKNESS_MM) -> list:
    """Every band, resolved to a polygon or refused with a stated reason.

    A refusal is a row, never a silent drop. The count of refusals is the more
    interesting number: it says how much of the drawing the pairing engine
    could not turn into material.
    """
    out = []
    for b in bands:
        a_mm, b_mm = b.face_a_mm, b.face_b_mm
        lo, hi = min(b.start_mm, b.end_mm), max(b.start_mm, b.end_mm)
        common = dict(
            wall_band_id=b.wall_band_id, axis=b.axis,
            face_a_mm=a_mm, face_b_mm=b_mm, start_mm=lo, end_mm=hi,
            separation_basis=b.separation_basis,
            source_face_ids=tuple(b.face_a_ids) + tuple(b.face_b_ids),
            source_object_ids=tuple(b.source_object_ids),
            drawing_id=drawing_id, drawing_revision=revision,
            validation_status=b.validation_status,
            evidence=tuple(b.supporting_evidence),
            occupied_intervals=(tuple(b.face_a_intervals)
                                + tuple(b.face_b_intervals)),
            extensions=tuple(b.extensions))

        def refuse(reason: str, why: str):
            return WallPolygon(ring=(), thickness_mm=None,
                               geometry_status=GEOMETRY_REJECTED,
                               unresolved_reason=reason, why=why, **common)

        if a_mm is None or b_mm is None:
            out.append(refuse(
                NO_SECOND_FACE,
                "only one face of this wall was drawn. NEVER INVENT THE "
                "MISSING HALF: a thickness manufactured from an assumed "
                "centreline would put material where nothing was drawn"))
            continue
        t = abs(b_mm - a_mm)
        if t < min_thickness:
            out.append(refuse(
                ZERO_SEPARATION,
                f"the two faces are {t:.1f} mm apart, below the {min_thickness:.0f} "
                "mm a wall needs to be. They are more likely one line found twice"))
            continue
        if hi - lo < min_length:
            out.append(refuse(
                ZERO_LENGTH,
                f"{hi - lo:.1f} mm of run is not a wall length"))
            continue
        f0, f1 = min(a_mm, b_mm), max(a_mm, b_mm)
        ring = (((lo, f0), (hi, f0), (hi, f1), (lo, f1)) if b.axis == "H"
                else ((f0, lo), (f1, lo), (f1, hi), (f0, hi)))
        out.append(WallPolygon(
            ring=ring, thickness_mm=t, geometry_status=GEOMETRY_VALID,
            why=("the rectangle between the two faces the architect drew. The "
                 "room boundary will run along these lines, not along an "
                 "offset from a centreline"),
            **common))
    return out


# ------------------------------------------------------------ the wall solid

REPAIRED_BY_BUFFER0 = "REPAIRED_BY_ZERO_BUFFER"

# NODE SNAP GRID. Two wall polygons that genuinely touch can come out of the
# coordinate pipeline 0.003 mm apart — three microns, on a drawing whose pixel
# is 10.8 mm and whose thinnest wall is 100 mm. GEOS then reports them as two
# disconnected components, and free space leaks between two rooms that share a
# wall.
#
# So coordinates are snapped to a grid before the union. The magnitude is the
# whole argument: at 0.05 mm this is 1/200 of a pixel and 1/2000 of the
# thinnest wall, and it moved AR-00's total wall area by 0.0003 m2 — three
# square centimetres. It cannot bridge an architectural gap, and it is not
# permitted to: anything that needs more than this is a REAL separation and is
# reported as one.
#
# 0.05 mm is also where the effect saturates on AR-00 — 0.01 gives 49
# components, 0.05 and 0.1 both give 46 — so it is the smallest value that
# does the job rather than a value chosen for its answer.
NODE_SNAP_GRID_MM = 0.05
# Above this a "snap" would be closing a gap rather than removing noise, and
# build_solid refuses to be asked.
MAX_DEFENSIBLE_SNAP_MM = 1.0


@dataclass
class WallSolid:
    """The union of the wall polygons, with its lineage kept.

    `source_of` maps each union component to the band ids that contributed to
    it, so a boundary can always be traced back to drawn objects.
    """

    geometry: object = None
    input_polygons: int = 0
    valid: int = 0
    invalid: int = 0
    repaired: list = field(default_factory=list)
    unresolved: list = field(default_factory=list)
    source_of: dict = field(default_factory=dict)
    included_band_ids: tuple = ()
    snap_grid_mm: float = 0.0
    unsnapped_components: int | None = None
    area_change_from_snap_m2: float = 0.0

    @property
    def area_m2(self) -> float:
        return 0.0 if self.geometry is None else self.geometry.area / 1e6

    @property
    def components(self) -> int:
        if self.geometry is None or self.geometry.is_empty:
            return 0
        return (len(self.geometry.geoms)
                if self.geometry.geom_type == "MultiPolygon" else 1)

    def record(self) -> dict:
        return {
            "input_wall_polygons": self.input_polygons,
            "valid": self.valid, "invalid": self.invalid,
            "repaired": self.repaired,
            "unresolved": self.unresolved,
            "union_components": self.components,
            "union_area_m2": round(self.area_m2, 3),
            "node_snap_grid_mm": self.snap_grid_mm,
            "components_without_snapping": self.unsnapped_components,
            "components_merged_by_snap": (
                None if self.unsnapped_components is None
                else self.unsnapped_components - self.components),
            "area_change_from_snap_m2": round(
                self.area_change_from_snap_m2, 6),
            "included_band_ids": len(self.included_band_ids),
            "source_coverage_pct": (
                round(100 * self.valid / self.input_polygons, 1)
                if self.input_polygons else None),
            "note": ("GEOS union. Nothing is deleted: an invalid ring is "
                     "repaired and reported, and an unresolved band is listed "
                     "rather than dropped"),
        }


def build_solid(polys, *, snap_grid_mm: float = NODE_SNAP_GRID_MM) -> WallSolid:
    """Union the resolved wall polygons. Robustly, and with a paper trail."""
    from shapely import set_precision
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from shapely.validation import explain_validity

    if snap_grid_mm > MAX_DEFENSIBLE_SNAP_MM:
        raise WallSolidError(
            f"a {snap_grid_mm} mm snap grid is not noise removal — it would "
            f"close gaps up to {snap_grid_mm} mm and manufacture material "
            "between walls that do not meet. The defensible ceiling is "
            f"{MAX_DEFENSIBLE_SNAP_MM} mm")
    solid = WallSolid(input_polygons=len(polys), snap_grid_mm=snap_grid_mm)
    shapes, ids = [], []
    for wp in polys:
        if not wp.is_resolved:
            solid.unresolved.append({"wall_band_id": wp.wall_band_id,
                                     "reason": wp.unresolved_reason,
                                     "why": wp.why})
            continue
        p = Polygon(list(wp.ring))
        if not p.is_valid:
            solid.invalid += 1
            why = explain_validity(p)
            p = p.buffer(0)
            solid.repaired.append({"wall_band_id": wp.wall_band_id,
                                   "how": REPAIRED_BY_BUFFER0,
                                   "was": why,
                                   "still_invalid": not p.is_valid})
        if p.is_empty:
            solid.unresolved.append({"wall_band_id": wp.wall_band_id,
                                     "reason": INVALID_RING,
                                     "why": "the ring is empty after repair"})
            continue
        solid.valid += 1
        shapes.append(set_precision(p, snap_grid_mm) if snap_grid_mm else p)
        ids.append(wp.wall_band_id)

    solid.included_band_ids = tuple(ids)
    if not shapes:
        return solid
    solid.geometry = unary_union(shapes)
    # What the snap actually did, so the choice is auditable rather than
    # trusted. An unsnapped union is computed only to report the difference.
    if snap_grid_mm:
        raw = unary_union([Polygon(list(wp.ring)) for wp in polys
                           if wp.is_resolved])
        solid.unsnapped_components = (
            len(raw.geoms) if raw.geom_type == "MultiPolygon" else 1)
        solid.area_change_from_snap_m2 = (
            solid.geometry.area - raw.area) / 1e6
    # Lineage: which bands touch each union component.
    geoms = (list(solid.geometry.geoms)
             if solid.geometry.geom_type == "MultiPolygon"
             else [solid.geometry])
    for i, comp in enumerate(geoms, 1):
        solid.source_of[f"WS-{i:04d}"] = tuple(
            bid for bid, shp in zip(ids, shapes) if comp.intersects(shp))
    return solid
