"""§H–§L. The elevator marble objects, declared and measured correctly.

The owner's standard has three separate things at every elevator landing,
and merging any two of them is a double count or a lost quantity:

    ELEVATOR_LANDING_MARBLE_ASSEMBLY  one per landing DOOR. An elevator
                                      serving four floors is four
                                      stations; two doors on one floor
                                      are two assemblies. The shaft is
                                      never the count
    ELEVATOR_DOOR_SURROUND            marble on LEFT, TOP and RIGHT of
                                      the outer landing door, 0.50 m
                                      wide by Urban Projects default and
                                      by the drawing wherever it says
    ELEVATOR_THRESHOLD_MARBLE         the marble step at the door, its
                                      own object, its own area, and
                                      never part of the surround

THE SURROUND IS AN AREA, AND THE AREA COMES FROM A POLYGON. Three sides
times 0.50 m as a linear run counts both top corners twice: the left jamb
and the top band overlap in a 0.50 x 0.50 square, and so do the right and
the top. So the three bands are built as rectangles and UNIONED, which is
the same arithmetic a tiler does on the wall.

    union = (left + right + top) - the two corner squares

WHAT THIS MODULE DOES NOT DO: find an elevator in a drawing. Detection
belongs to the trade and BOQ phase. This module is the vocabulary, the
required geometry and the calculation — so that when the geometry arrives
the method is already the owner's, and so that a station whose geometry is
NOT established produces a question rather than a number.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from engine import rule_library as rules

MODEL = "ELEVATOR_LANDING_MARBLE_V1"

LANDING_ASSEMBLY = "ELEVATOR_LANDING_MARBLE_ASSEMBLY"
DOOR_SURROUND = "ELEVATOR_DOOR_SURROUND"
THRESHOLD = "ELEVATOR_THRESHOLD_MARBLE"
OBJECTS = (LANDING_ASSEMBLY, DOOR_SURROUND, THRESHOLD)

LEFT, TOP, RIGHT = "LEFT", "TOP", "RIGHT"
THREE_SIDES = (LEFT, TOP, RIGHT)

SURROUND_NOT_ESTABLISHED = "ELEVATOR_SURROUND_GEOMETRY_NOT_ESTABLISHED"
WIDTH_NOT_ESTABLISHED = "ELEVATOR_SURROUND_WIDTH_NOT_ESTABLISHED"
THRESHOLD_DEPTH_NOT_ESTABLISHED = "ELEVATOR_THRESHOLD_DEPTH_NOT_ESTABLISHED"
STATIONS_NOT_ESTABLISHED = "ELEVATOR_STATIONS_NOT_ESTABLISHED"
EQUIVALENCE_NOT_ESTABLISHED = "STATION_EQUIVALENCE_NOT_ESTABLISHED"

MEASURED = "MEASURED_NET"
FROM_A_POLYGON = "THE_UNION_AREA_OF_THE_SURROUND_POLYGON"
NEVER_LINEAR = (
    "three sides times a width is wrong in both directions: taken along "
    "the door edge it MISSES the two top corners (a 1.00 x 2.10 door "
    "with 0.50 m sides gives 2.60 m2 instead of 3.10), and taken as "
    "three full bands it counts them TWICE (3.60). The bands are built "
    "and unioned, which is the arithmetic the tiler does on the wall")

# The invariant §L states, alongside the stair's own.
THRESHOLD_IS_NOT_FLOOR = "ELEVATOR_THRESHOLD_MARBLE_AREA_IS_NOT_PORCELAIN"

REQUIRED_GEOMETRY = (
    "elevator_id", "floor_or_station", "door_clear_width",
    "door_clear_height", "left_surround_width", "right_surround_width",
    "top_surround_width", "surround_polygon", "openings_or_deductions",
    "measurement_basis", "source_geometry",
)


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "OBJECTS": list(OBJECTS),
        "THREE_SIDES": list(THREE_SIDES),
        "REQUIRED_GEOMETRY": list(REQUIRED_GEOMETRY),
        "why": {
            "a_station_is_a_door_not_a_shaft": (
                "an elevator serving four floors is four landing "
                "stations, and two doors on one floor are two "
                "assemblies. Counting shafts counts one"),
            "an_area_is_not_a_perimeter": NEVER_LINEAR,
            "the_threshold_is_its_own_object": (
                "the marble step at the door is measured apart from the "
                "vertical surround and taken out of the porcelain floor"),
            "typical_times_count_needs_equivalence": (
                "one verified station may stand for many only once the "
                "doors, the surrounds, the detail and the finish are "
                "established equal, and every station id survives it"),
        },
    }


def model_hash() -> str:
    parts = ([MODEL] + list(OBJECTS) + list(THREE_SIDES)
             + list(REQUIRED_GEOMETRY)
             + [SURROUND_NOT_ESTABLISHED, WIDTH_NOT_ESTABLISHED,
                THRESHOLD_DEPTH_NOT_ESTABLISHED, STATIONS_NOT_ESTABLISHED,
                EQUIVALENCE_NOT_ESTABLISHED, THRESHOLD_IS_NOT_FLOOR])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


@dataclass
class Surround:
    """The marble on three sides of one outer landing door."""

    station_id: str = ""
    door_width_mm: float | None = None
    door_height_mm: float | None = None
    left_mm: float | None = None
    top_mm: float | None = None
    right_mm: float | None = None
    width_source: str = WIDTH_NOT_ESTABLISHED
    area_m2: float | None = None
    edge_lm: float | None = None
    polygon_wkt: str = ""
    deductions_m2: float = 0.0
    status: str = SURROUND_NOT_ESTABLISHED
    what_is_missing: tuple = ()

    def record(self) -> dict:
        return {
            "object": DOOR_SURROUND,
            "elevator_station_id": self.station_id,
            "door_clear_width_mm": self.door_width_mm,
            "door_clear_height_mm": self.door_height_mm,
            "left_surround_width_mm": self.left_mm,
            "top_surround_width_mm": self.top_mm,
            "right_surround_width_mm": self.right_mm,
            "surround_width_source": self.width_source,
            # THE AREA, which is what this is bought by.
            "ELEVATOR_SURROUND_AREA_M2": (
                None if self.area_m2 is None else round(self.area_m2, 4)),
            # Kept BESIDE it, for a commercial basis that asks for it,
            # and never substituted for it.
            "ELEVATOR_SURROUND_EDGE_LM": (
                None if self.edge_lm is None else round(self.edge_lm, 3)),
            "deductions_m2": round(self.deductions_m2, 4),
            "measurement_basis": FROM_A_POLYGON,
            "polygon_wkt_mm": self.polygon_wkt,
            "status": self.status,
            "what_is_missing": list(self.what_is_missing),
            "an_area_is_not_a_perimeter": NEVER_LINEAR,
        }


@dataclass
class Threshold:
    """The marble step at the door. Its own object (§L)."""

    station_id: str = ""
    width_mm: float | None = None
    depth_mm: float | None = None
    area_m2: float | None = None
    exposed_edge_lm: float | None = None
    depth_source: str = THRESHOLD_DEPTH_NOT_ESTABLISHED
    status: str = THRESHOLD_DEPTH_NOT_ESTABLISHED
    what_is_missing: tuple = ()

    def record(self) -> dict:
        return {
            "object": THRESHOLD,
            "elevator_station_id": self.station_id,
            "threshold_width_mm": self.width_mm,
            "threshold_depth_mm": self.depth_mm,
            "ELEVATOR_THRESHOLD_AREA_M2": (
                None if self.area_m2 is None else round(self.area_m2, 4)),
            "exposed_front_edge_lm": (
                None if self.exposed_edge_lm is None
                else round(self.exposed_edge_lm, 3)),
            "depth_source": self.depth_source,
            "status": self.status,
            "what_is_missing": list(self.what_is_missing),
            "not_part_of_the_surround": (
                "the threshold is a floor quantity of its own and is "
                "never merged into the vertical door surround"),
            "invariant": THRESHOLD_IS_NOT_FLOOR,
        }


@dataclass
class Station:
    """One landing door of one elevator, on one floor."""

    station_id: str = ""
    elevator_id: str = ""
    floor_level: str = ""
    door_index: int = 1
    surround: Surround = field(default_factory=Surround)
    threshold: Threshold = field(default_factory=Threshold)
    source_geometry: str = ""
    exceptions: tuple = ()

    def record(self) -> dict:
        return {
            "object": LANDING_ASSEMBLY,
            "elevator_station_id": self.station_id,
            "elevator_id": self.elevator_id,
            "floor": self.floor_level,
            "door_index": self.door_index,
            "surround": self.surround.record(),
            "threshold": self.threshold.record(),
            "source_geometry": self.source_geometry,
            "exceptions": list(self.exceptions),
        }


def surround_polygon(door_w, door_h, *, left, top, right):
    """The three bands as one polygon, with the corners counted once."""
    from shapely.geometry import box
    from shapely.ops import unary_union

    if None in (door_w, door_h, left, top, right):
        return None
    # the door sits with its sill at y = 0 and its left jamb at x = 0
    bands = [
        box(-left, 0.0, 0.0, door_h),                      # LEFT
        box(door_w, 0.0, door_w + right, door_h),          # RIGHT
        box(-left, door_h, door_w + right, door_h + top),  # TOP
    ]
    return unary_union(bands)


def measure_surround(station_id: str, *, door_width_mm=None,
                     door_height_mm=None, left_mm=None, top_mm=None,
                     right_mm=None, width_source=WIDTH_NOT_ESTABLISHED,
                     deductions_m2: float = 0.0) -> Surround:
    """§I, §J. The area of the actual polygon, or an honest refusal."""
    out = Surround(
        station_id=station_id, door_width_mm=door_width_mm,
        door_height_mm=door_height_mm, left_mm=left_mm, top_mm=top_mm,
        right_mm=right_mm, width_source=width_source,
        deductions_m2=deductions_m2)
    missing = [name for name, v in (
        ("door_clear_width", door_width_mm),
        ("door_clear_height", door_height_mm),
        ("left_surround_width", left_mm),
        ("top_surround_width", top_mm),
        ("right_surround_width", right_mm)) if v is None]
    if missing:
        out.what_is_missing = tuple(missing)
        out.status = SURROUND_NOT_ESTABLISHED
        return out
    poly = surround_polygon(door_width_mm, door_height_mm, left=left_mm,
                            top=top_mm, right=right_mm)
    out.polygon_wkt = poly.wkt
    out.area_m2 = max(poly.area / 1e6 - deductions_m2, 0.0)
    # The OUTER edge of the cladding, for a commercial basis that wants
    # a length. It is not the area and never replaces it.
    out.edge_lm = (door_height_mm + left_mm + top_mm
                   + door_width_mm + top_mm + right_mm
                   + door_height_mm) / 1000.0
    out.status = MEASURED
    return out


def measure_threshold(station_id: str, *, width_mm=None, depth_mm=None,
                      depth_source=THRESHOLD_DEPTH_NOT_ESTABLISHED,
                      exposed_edge: bool = True) -> Threshold:
    """§L. The marble step, measured apart, and asked about when unknown."""
    out = Threshold(station_id=station_id, width_mm=width_mm,
                    depth_mm=depth_mm, depth_source=depth_source)
    missing = [name for name, v in (("threshold_width", width_mm),
                                    ("threshold_depth", depth_mm))
               if v is None]
    if missing:
        out.what_is_missing = tuple(missing)
        out.status = (THRESHOLD_DEPTH_NOT_ESTABLISHED
                      if depth_mm is None else rules.OWNER_RULE_REQUEST)
        return out
    out.area_m2 = width_mm * depth_mm / 1e6
    out.exposed_edge_lm = (width_mm / 1000.0 if exposed_edge else None)
    out.status = MEASURED
    return out


def stations(spec, *, library=None) -> dict:
    """§H, §K. One assembly per landing DOOR, with its ids preserved.

    `spec` is what the project establishes: an elevator, the floors it
    serves, and the doors on each. Nothing is detected here and nothing
    is multiplied: a typical station stands for many only when the
    caller has established their equivalence, and the ids survive it.
    """
    lib = library if library is not None else rules.load()
    out, exceptions = [], []
    for elevator in (spec or {}).get("elevators", ()):
        eid = elevator.get("elevator_id", "")
        served = list(elevator.get("floors_served", ()))
        if not served:
            exceptions.append(rules.owner_rule_request(
                eid or "<elevator>", where="the project specification",
                question=("which floors does this elevator serve, and "
                          "how many landing doors are on each?"),
                kind="ELEVATOR"))
            continue
        for floor in served:
            doors = elevator.get("doors_per_floor", {}).get(floor, 1)
            for i in range(1, int(doors) + 1):
                sid = f"{eid}-{floor}" + (f"-{i}" if doors > 1 else "")
                door = (elevator.get("doors", {}) or {}).get(sid, {})
                # THE DRAWING FIRST, then what the owner said about this
                # project, then the Urban Projects default — which the
                # library states in METRES, because that is how the
                # owner states it.
                width = rules.resolve(
                    lib, "UP-ELEV-002",
                    drawing=door.get("surround_width_mm_drawn"),
                    project=door.get("surround_width_mm_project"))
                if width.value is None:
                    default_mm = None
                elif width.source == rules.SRC_STANDARD:
                    default_mm = float(width.value) * 1000.0
                else:
                    default_mm = float(width.value)
                sur = measure_surround(
                    sid,
                    door_width_mm=door.get("door_clear_width_mm"),
                    door_height_mm=door.get("door_clear_height_mm"),
                    left_mm=door.get("left_surround_width_mm", default_mm),
                    top_mm=door.get("top_surround_width_mm", default_mm),
                    right_mm=door.get("right_surround_width_mm",
                                      default_mm),
                    width_source=width.source)
                thr = measure_threshold(
                    sid, width_mm=door.get("threshold_width_mm"),
                    depth_mm=door.get("threshold_depth_mm"),
                    depth_source=door.get("threshold_depth_source",
                                          THRESHOLD_DEPTH_NOT_ESTABLISHED))
                if thr.status != MEASURED:
                    exceptions.append(rules.owner_rule_request(
                        sid, where=door.get("source_geometry", "unknown"),
                        question=("what is the marble threshold depth at "
                                  "this elevator door? Neither drawing "
                                  "nor detail establishes it, and Urban "
                                  "Projects has no confirmed default"),
                        kind="ELEVATOR_THRESHOLD"))
                out.append(Station(
                    station_id=sid, elevator_id=eid, floor_level=floor,
                    door_index=i, surround=sur, threshold=thr,
                    source_geometry=door.get("source_geometry", ""),
                    exceptions=tuple(
                        ([SURROUND_NOT_ESTABLISHED]
                         if sur.status != MEASURED else [])
                        + ([THRESHOLD_DEPTH_NOT_ESTABLISHED]
                           if thr.status != MEASURED else []))))
    total = ([s.surround.area_m2 for s in out]
             if out else [])
    return {
        "model": MODEL,
        "ELEVATOR_MARBLE_HASH": model_hash(),
        "stations": [s.record() for s in out],
        "station_count": len(out),
        "ELEVATOR_SURROUND_AREA_M2": (
            None if not total or any(v is None for v in total)
            else round(sum(total), 4)),
        "exceptions": exceptions,
        "status": (STATIONS_NOT_ESTABLISHED if not out else MEASURED),
        "this_is_not_a_boq": (
            "the objects, the required geometry and the method. No "
            "elevator is detected in any drawing here, and no price, "
            "waste factor or procurement quantity exists"),
    }
