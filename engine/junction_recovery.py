"""A wall that stops two millimetres short still meets the wall it meets.

A drafter's line ends where the mouse let go. On a real drawing the end of
a partition overshoots the wall it runs into, or stops just short of it,
and the arrangement then has a hairline slot that a flood walks straight
through — which is one of the ways a floor of rooms becomes one 194 m²
face.

    A GRAPHICAL ENDPOINT MISSING BY A HAIR MUST NOT DESTROY A PHYSICAL
    JUNCTION.

    AND A REAL GAP BETWEEN TWO WALLS MUST NOT BECOME ONE.

The distance between those two statements is the whole difficulty, and §12
says where the boundary may come from: local wall geometry, line precision
and CAD drafting resolution — **never a millimetre constant taken from one
client's drawing.** So the tolerance here is DERIVED and REPORTED on every
junction:

    drafting_resolution_mm   measured from the drawing's own coordinates:
                             the finest unit that nearly all of them are
                             multiples of
    local_thickness_mm       the thinner of the two walls meeting
    tolerance = max(of those two)

A miss smaller than the thinner wall's own thickness lands inside the
junction's material. A miss larger than it is a space between two walls,
and a space between two walls is a space.

COLUMNS (§13)

A column is a small closed figure of wall material — both of its extents
inside the profile's own wall band. It is not a room, it does not break a
partition that terminates into it, and nothing here begins a structural
quantity. This is architectural topology only.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import physical_wall as pw

MODEL = "DERIVED_TOLERANCE_JUNCTION_RECOVERY_V1"

L_CORNER = "L_CORNER"
T_JUNCTION = "T_JUNCTION"
CROSS_JUNCTION = "CROSS_JUNCTION"
INTO_ENVELOPE = "ENDS_INTO_AN_EXTERNAL_WALL"
INTO_COLUMN = "ENDS_INTO_A_COLUMN"
AT_PORTAL_JAMB = "ENDS_AT_A_PORTAL_JAMB"
FREE_END = "FREE_END"
UNRESOLVED_END = "UNRESOLVED_END"

KINDS = (L_CORNER, T_JUNCTION, CROSS_JUNCTION, INTO_ENVELOPE, INTO_COLUMN,
         AT_PORTAL_JAMB, FREE_END, UNRESOLVED_END)

MET = "JUNCTION_DRAWN"
RECOVERED = "JUNCTION_RECOVERED_WITHIN_THE_DERIVED_TOLERANCE"
NOT_RECOVERED = "SEPARATION_EXCEEDS_THE_DERIVED_TOLERANCE"

# The decade ladder the drafting resolution is read off. Nothing is chosen
# from it by hand: the drawing's own coordinates pick the rung.
RESOLUTION_LADDER = (0.001, 0.01, 0.1, 1.0, 10.0)

# How much of the coordinates must be multiples of a rung for it to BE the
# drawing's resolution. Not a tuning knob — it is what "nearly all of them"
# means, and a drawing that fails every rung reports the finest one.
RESOLUTION_SHARE = 0.99


@dataclass(frozen=True)
class Column:
    """A small closed figure of wall material. Not a room, ever."""

    column_id: str
    x0: float
    y0: float
    x1: float
    y1: float

    def contains(self, x: float, y: float, *, pad: float = 0.0) -> bool:
        return (self.x0 - pad <= x <= self.x1 + pad
                and self.y0 - pad <= y <= self.y1 + pad)

    def record(self) -> dict:
        return {"column_id": self.column_id,
                "extent_mm": [round(self.x0, 1), round(self.y0, 1),
                              round(self.x1, 1), round(self.y1, 1)],
                "size_mm": [round(self.x1 - self.x0, 1),
                            round(self.y1 - self.y0, 1)],
                "this_is": ("a closed figure whose BOTH extents lie inside "
                            "the profile's wall band. It may not become a "
                            "room, and no structural quantity begins here")}


@dataclass(frozen=True)
class Junction:
    """One end of one wall, and what it runs into."""

    junction_id: str
    wall_id: str
    region_id: str
    axis: str
    at_mm: float
    kind: str
    status: str
    separation_mm: float
    tolerance_mm: float
    drafting_resolution_mm: float
    local_thickness_mm: float
    met_wall_id: str = ""
    recovered_to_mm: float | None = None
    faces_mm: tuple = ()
    why: str = ""

    @property
    def is_recovered(self) -> bool:
        return self.status == RECOVERED

    def record(self) -> dict:
        return {
            "junction_id": self.junction_id,
            "wall_id": self.wall_id,
            "drawing_region_id": self.region_id,
            "kind": self.kind,
            "status": self.status,
            "end_at_mm": round(self.at_mm, 2),
            "separation_mm": round(self.separation_mm, 2),
            "DERIVED_TOLERANCE_MM": round(self.tolerance_mm, 2),
            "tolerance_came_from": {
                "drafting_resolution_mm": self.drafting_resolution_mm,
                "local_wall_thickness_mm": round(self.local_thickness_mm, 1),
                "rule": ("the larger of the two. A miss smaller than the "
                         "thinner wall's own thickness lands inside the "
                         "junction's material; a larger one is a space"),
            },
            "meets_wall": self.met_wall_id,
            "recovered_to_mm": (None if self.recovered_to_mm is None
                                else round(self.recovered_to_mm, 2)),
            "why": self.why,
        }


@dataclass
class JunctionReport:
    region_id: str = ""
    junctions: list = field(default_factory=list)
    columns: list = field(default_factory=list)
    drafting_resolution_mm: float = 0.0
    notes: dict = field(default_factory=dict)

    def recovered(self) -> list:
        return [j for j in self.junctions if j.is_recovered]

    def counts(self) -> dict:
        return {
            "wall_ends_examined": len(self.junctions),
            "by_kind": dict(Counter(j.kind for j in self.junctions
                                    ).most_common()),
            "by_status": dict(Counter(j.status for j in self.junctions
                                      ).most_common()),
            "junctions_recovered": len(self.recovered()),
            "columns_observed": len(self.columns),
            "DRAFTING_RESOLUTION_MM": self.drafting_resolution_mm,
        }

    def record(self, *, limit: int = 30) -> dict:
        return {
            "model": MODEL,
            "JUNCTION_RECOVERY_HASH": junction_hash(),
            "drawing_region_id": self.region_id,
            "kinds": list(KINDS),
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "junctions": [j.record() for j in self.junctions[:limit]],
            "columns": [c.record() for c in self.columns[:limit]],
            "the_tolerance": (
                "derived per junction from the drawing's own coordinate "
                "resolution and the thickness of the walls meeting there, "
                "and reported on every one. No millimetre constant from any "
                "client drawing appears in this module"),
            "notes": dict(self.notes),
        }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "RESOLUTION_LADDER": list(RESOLUTION_LADDER),
        "RESOLUTION_SHARE": RESOLUTION_SHARE,
        "TOLERANCE_RULE": ("max(drafting_resolution_mm, "
                           "min(thickness_a, thickness_b))"),
        "why": {
            "RESOLUTION_LADDER": (
                "the drawing picks its own rung. A model drawn to the "
                "millimetre reports 1 mm; one drawn to a tenth reports 0.1"),
            "TOLERANCE_RULE": (
                "a miss smaller than the thinner wall's own thickness is "
                "inside the junction's material. A larger one is a space "
                "between two walls, and a space between two walls is a "
                "space"),
            "no_client_constant": (
                "nothing here is 2 mm, 5 mm or any other number taken from "
                "a drawing that had to come out right"),
        },
    }


def junction_hash() -> str:
    parts = [MODEL, "|".join(KINDS), MET, RECOVERED, NOT_RECOVERED,
             ",".join(str(v) for v in RESOLUTION_LADDER),
             str(RESOLUTION_SHARE), pw.wall_band_hash()]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def drafting_resolution(candidates) -> float:
    """The finest unit nearly all of this drawing's coordinates sit on."""
    values = []
    for c in candidates:
        values += [c.fixed_mm, c.start_mm, c.end_mm]
    if not values:
        return RESOLUTION_LADDER[0]
    for unit in reversed(RESOLUTION_LADDER):
        hits = sum(1 for v in values
                   if abs(v / unit - round(v / unit)) < 1e-6)
        if hits >= RESOLUTION_SHARE * len(values):
            return unit
    return RESOLUTION_LADDER[0]


def columns(candidates) -> list:
    """Closed figures of wall material, small in BOTH directions."""
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
    out = []
    for n, face in enumerate(polygonize(unary_union(segs)), 1):
        x0, y0, x1, y1 = face.bounds
        w, h = x1 - x0, y1 - y0
        if (pw.MIN_WALL_MM <= w <= pw.MAX_WALL_MM
                and pw.MIN_WALL_MM <= h <= pw.MAX_WALL_MM):
            out.append(Column(f"COL-{n:03d}", x0, y0, x1, y1))
    return out


def _band(wall) -> tuple:
    return (min(wall.face_a_mm, wall.face_b_mm),
            max(wall.face_a_mm, wall.face_b_mm))


def recover(walls, *, region_id: str = "DR-001", candidates=(),
            openings=(), cols=None) -> JunctionReport:
    """Classify every wall end, and recover the ones a hair short."""
    rep = JunctionReport(region_id=region_id)
    rep.drafting_resolution_mm = drafting_resolution(candidates)
    rep.columns = list(cols if cols is not None else columns(candidates))
    wall_list = list(walls)

    jamb_stations = []
    for o in openings:
        if o.may_close_boundary:
            jamb_stations.append((o.axis, o.start_mm, o.wall_faces_mm))
            jamb_stations.append((o.axis, o.end_mm, o.wall_faces_mm))

    for wall in wall_list:
        lo, hi = wall.observed_extent
        for label, at in (("lo", lo), ("hi", hi)):
            best, best_gap, kind = None, None, FREE_END
            for other in wall_list:
                if other.wall_id == wall.wall_id or other.axis == wall.axis:
                    continue
                o_lo, o_hi = other.observed_extent
                w_lo, w_hi = _band(wall)
                if o_hi < w_lo or o_lo > w_hi:
                    continue        # it does not reach this wall's band
                b_lo, b_hi = _band(other)
                if b_lo <= at <= b_hi:
                    gap = 0.0
                else:
                    gap = min(abs(at - b_lo), abs(at - b_hi))
                if best_gap is None or gap < best_gap:
                    best, best_gap = other, gap

            tol_thickness = (min(wall.thickness_mm, best.thickness_mm)
                             if best else wall.thickness_mm)
            tol = max(rep.drafting_resolution_mm, tol_thickness)

            column = next((c for c in rep.columns
                           if _end_in_column(wall, at, c, tol)), None)
            at_jamb = any(
                axis == wall.axis and abs(station - at) <= tol
                for axis, station, _faces in jamb_stations)

            if column is not None:
                kind, status, why = (
                    INTO_COLUMN, MET,
                    "this wall ends into a column. The partition is "
                    "continuous through it, and no structural quantity "
                    "begins here")
                met, to = column.column_id, None
            elif best is None:
                kind, status = FREE_END, MET
                met, to = "", None
                why = ("no wall of the other direction reaches this end. It "
                       "stands free, and a free end is not a missed "
                       "junction")
            elif best_gap <= 0.0:
                kind = _kind(wall, best, at)
                status, met, to = MET, best.wall_id, None
                why = "the end lies inside the other wall's own band"
            elif best_gap <= tol:
                kind = _kind(wall, best, at)
                status, met = RECOVERED, best.wall_id
                b_lo, b_hi = _band(best)
                to = b_lo if abs(at - b_lo) < abs(at - b_hi) else b_hi
                why = (f"the end misses by {best_gap:.2f} mm against a "
                       f"derived tolerance of {tol:.2f} mm. That is inside "
                       "the junction's own material, so the junction "
                       "stands")
            elif at_jamb:
                kind, status, met, to = AT_PORTAL_JAMB, MET, "", None
                why = ("this end is a portal jamb. The opening explains it, "
                       "and nothing is recovered across an opening")
            else:
                kind, status, met, to = UNRESOLVED_END, NOT_RECOVERED, \
                    best.wall_id, None
                why = (f"the nearest wall of the other direction is "
                       f"{best_gap:.0f} mm away against a derived tolerance "
                       f"of {tol:.0f} mm. A space between two walls is a "
                       "space, and it is not closed here")

            rep.junctions.append(Junction(
                junction_id=f"JCT-{wall.wall_id}-{label}",
                wall_id=wall.wall_id, region_id=region_id, axis=wall.axis,
                at_mm=at, kind=kind, status=status,
                separation_mm=(best_gap if best_gap is not None else 0.0),
                tolerance_mm=tol,
                drafting_resolution_mm=rep.drafting_resolution_mm,
                local_thickness_mm=tol_thickness, met_wall_id=met,
                recovered_to_mm=to, faces_mm=(wall.face_a_mm,
                                              wall.face_b_mm),
                why=why))

    rep.notes["what_is_not_recovered"] = (
        "an end whose nearest crossing wall is further away than the "
        "derived tolerance. That is a real separation, and closing it would "
        "invent a room")
    rep.notes["columns"] = (
        "a column may not become a room and may not break a partition that "
        "terminates into it. This module observes columns; it starts no "
        "structural quantity")
    return rep


def _end_in_column(wall, at: float, col: Column, tol: float) -> bool:
    centre = wall.centre_mm
    if wall.axis == "H":
        return col.contains(at, centre, pad=tol)
    return col.contains(centre, at, pad=tol)


def _kind(wall, other, at: float) -> str:
    o_lo, o_hi = other.observed_extent
    w_lo, w_hi = _band(wall)
    # Does the other wall pass THROUGH this one, or stop at it?
    through = o_lo < w_lo - pw.JOIN_MM and o_hi > w_hi + pw.JOIN_MM
    return CROSS_JUNCTION if through else T_JUNCTION


def recovered_candidates(report) -> list:
    """The short extensions a recovery adds. Inferred, never drawn."""
    from engine.boundary_match import VectorCandidate
    from engine.space_objects import SRC_VECTOR_OPENING_JAMB

    out = []
    for j in report.recovered():
        if j.recovered_to_mm is None:
            continue
        lo, hi = sorted((j.at_mm, j.recovered_to_mm))
        if hi - lo <= 0:
            continue
        for i, f in enumerate(j.faces_mm):
            out.append(VectorCandidate(
                object_id=f"RECOVERED-{j.junction_id}-F{i}", axis=j.axis,
                fixed_mm=f, start_mm=lo, end_mm=hi,
                source_type=SRC_VECTOR_OPENING_JAMB,
                validation_class="ESTABLISHED"))
    return out


def recovered_authorities(report) -> dict:
    """A recovered junction closes topology; its extension is not material."""
    from engine import partition_continuity as pc

    out = {}
    for j in report.recovered():
        if j.recovered_to_mm is None:
            continue
        row = {"TOPOLOGY_AUTHORITY": pc.TOPOLOGY_VALIDATED,
               "MATERIAL_AUTHORITY": pc.MATERIAL_CANDIDATE,
               "verdict": j.kind, "junction_id": j.junction_id,
               "wall_id": j.wall_id,
               "separation_mm": round(j.separation_mm, 2),
               "DERIVED_TOLERANCE_MM": round(j.tolerance_mm, 2)}
        for i, _f in enumerate(j.faces_mm):
            out[f"RECOVERED-{j.junction_id}-F{i}"] = row
    return out
