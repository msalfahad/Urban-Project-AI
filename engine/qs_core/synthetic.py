"""Synthetic drawings: small plans with a known answer, owing nothing to any real project.

These exist so the algorithms can be proved before a real drawing is allowed anywhere near them.  Each builder
returns the same shape of input the adapters produce from a real source, so the pipeline under test is the
production pipeline.
"""

from __future__ import annotations

from engine.qs_core import geom
from engine.qs_core.entities import (GeometryComponent, KIND_COLUMN, KIND_EXTERNAL, KIND_FLOOR_REGION,
                                     KIND_WALL_BAND, Label, Opening)
from engine.qs_core.spaces import Barrier

FLOOR = "LEVEL_1"
TOL = 0.005                  # 5 mm: a drawing authored to the millimetre
SLIVER_MIN = 0.30            # nothing narrower than 300 mm is a space
MAX_OPENING_SPAN = 3.00      # the widest gap in a wall line these fixtures ever put an opening in
WALL_GEOMETRY_SPANS_OPENINGS = True   # these fixtures draw a wall straight through its own doorway


def floor_region(ref, rects, floor=FLOOR, revision="R1", kind=KIND_FLOOR_REGION):
    return GeometryComponent(ref, kind, [geom.Rect(*r) for r in rects], floor, revision)


def wall_band(ref, rect, thickness, axis, floor=FLOOR, revision="R1", layer="WALL"):
    return GeometryComponent(ref, KIND_WALL_BAND, [geom.Rect(*rect)], floor, revision,
                             thickness=thickness, axis=axis, layer=layer)


def opening(ref, rect, axis, width, height, kind="DOOR", floor=FLOOR, revision="R1"):
    return Opening(ref, geom.Rect(*rect), floor, revision, opening_type=kind, width=width, height=height,
                   width_source="MEASURED_FROM_DRAWING", height_source="MEASURED_FROM_DRAWING", axis=axis)


# ------------------------------------------------------------------ opening-to-host fixtures
def two_band_plan(thickness_a=0.15, thickness_b=0.20):
    """A T junction: one band along x of thickness A, one along y of thickness B, meeting at a corner."""
    band_a = wall_band("W-A", (0.0, 0.0, 6.0, thickness_a), thickness_a, geom.AXIS_X)
    band_b = wall_band("W-B", (6.0, 0.0, 6.0 + thickness_b, 5.0), thickness_b, geom.AXIS_Y)
    return [band_a, band_b]


def door_in_band(band, along=2.0, width=0.90):
    """An opening drawn through a band: as wide as the door, as deep as the wall."""
    b = band.bbox
    if band.axis == geom.AXIS_X:
        return opening("OP-1", (b.x0 + along, b.y0, b.x0 + along + width, b.y1), geom.AXIS_X, width, 2.10)
    return opening("OP-1", (b.x0, b.y0 + along, b.x1, b.y0 + along + width), geom.AXIS_Y, width, 2.10)


# ------------------------------------------------------------------ semantic-space fixtures
def two_rooms_with_a_thick_wall():
    """Two rooms either side of a 200 mm wall: they do not touch, so nothing can merge them."""
    left = floor_region("C-L", [(0.0, 0.0, 4.0, 3.0)])
    wall = wall_band("W-1", (4.0, 0.0, 4.2, 3.0), 0.20, geom.AXIS_Y)
    right = floor_region("C-R", [(4.2, 0.0, 8.0, 3.0)])
    labels = [Label("OFFICE", 2.0, 1.5), Label("STORE", 6.0, 1.5)]
    return [left, wall, right], [], [], labels


def one_room_in_two_fragments():
    """One room the extractor cut in two at a grid line, with nothing physical on the seam."""
    a = floor_region("C-1", [(0.0, 0.0, 3.0, 3.0)])
    b = floor_region("C-2", [(3.0, 0.0, 5.0, 3.0)])
    return [a, b], [], [], [Label("MEETING", 1.5, 1.5)]


def two_spaces_through_a_doorway():
    """Two rooms whose floors meet only in the doorway, with the door drawn in that gap.

    The wall stands either side of the opening, so the only place the two floors touch is the reveal - which is
    exactly the seam the engine has to read as "a door", not as "one room".
    """
    a = floor_region("C-1", [(0.0, 0.0, 3.0, 3.0), (3.0, 1.0, 3.2, 1.9)])
    below = wall_band("W-BELOW", (3.0, 0.0, 3.2, 1.0), 0.20, geom.AXIS_Y)
    above = wall_band("W-ABOVE", (3.0, 1.9, 3.2, 3.0), 0.20, geom.AXIS_Y)
    b = floor_region("C-2", [(3.2, 0.0, 6.2, 3.0)])
    door = opening("OP-1", (3.0, 1.0, 3.2, 1.9), geom.AXIS_Y, 0.90, 2.10)
    return [a, below, above, b], [], [door], [Label("HALL", 1.5, 1.5), Label("KITCHEN", 4.7, 1.5)]


def single_line_partition():
    """Two rooms separated by a partition drawn as one line with no thickness."""
    a = floor_region("C-1", [(0.0, 0.0, 3.0, 3.0)])
    b = floor_region("C-2", [(3.0, 0.0, 6.0, 3.0)])
    barrier = Barrier(geom.AXIS_Y, 3.0, 0.0, 3.0, Barrier.BACKED_BY_MATERIAL, FLOOR, component_ref="W-LINE")
    return [a, b], [barrier], [], [Label("BED", 1.5, 1.5), Label("BATH", 4.5, 1.5)]


def ambiguous_seam():
    """Half the seam is a partition and half is open: neither reading wins, so neither is taken."""
    a = floor_region("C-1", [(0.0, 0.0, 3.0, 3.0)])
    b = floor_region("C-2", [(3.0, 0.0, 6.0, 3.0)])
    barrier = Barrier(geom.AXIS_Y, 3.0, 0.0, 1.5, Barrier.BACKED_BY_MATERIAL, FLOOR, component_ref="W-LINE")
    return [a, b], [barrier], [], [Label("LOUNGE", 1.5, 1.5)]


def room_with_a_sliver_and_a_column():
    a = floor_region("C-1", [(0.0, 0.0, 4.0, 3.0)])
    sliver = floor_region("C-THIN", [(4.0, 0.0, 4.10, 3.0)])
    column = GeometryComponent("COL-1", KIND_COLUMN, [geom.Rect(1.0, 1.0, 1.4, 1.4)], FLOOR, "R1")
    return [a, sliver, column], [], [], [Label("SALON", 2.0, 1.5)]


def internal_meets_external():
    inside = floor_region("C-IN", [(0.0, 0.0, 4.0, 3.0)])
    outside = floor_region("C-OUT", [(4.0, 0.0, 7.0, 3.0)], kind=KIND_EXTERNAL)
    return [inside, outside], [], [], [Label("LIVING", 2.0, 1.5)]


def conflicting_labels_in_one_space():
    a = floor_region("C-1", [(0.0, 0.0, 3.0, 3.0)])
    b = floor_region("C-2", [(3.0, 0.0, 6.0, 3.0)])
    return [a, b], [], [], [Label("STUDY", 1.5, 1.5), Label("GUEST", 4.5, 1.5)]


# ------------------------------------------------------------------ a whole small plan, for end-to-end use
def small_plan(revision="R1", shift=0.0):
    """Two rooms and a corridor, with doors, a column, a sliver and an external terrace.

    `shift` moves one internal wall, which is how the revision tests produce a drawing that is the same building
    drawn slightly differently.
    """
    comps, barriers, openings_, labels = [], [], [], []
    comps.append(floor_region("C-ROOM-A", [(0.0, 0.0, 4.0, 4.0)], revision=revision))
    comps.append(wall_band("W-A-B", (4.0, 0.0, 4.2 + shift, 4.0), 0.20 + shift, geom.AXIS_Y, revision=revision))
    comps.append(floor_region("C-ROOM-B", [(4.2 + shift, 0.0, 8.0, 4.0)], revision=revision))
    comps.append(wall_band("W-CORRIDOR", (0.0, 4.0, 8.0, 4.15), 0.15, geom.AXIS_X, revision=revision))
    comps.append(floor_region("C-CORRIDOR", [(0.0, 4.15, 8.0, 5.65)], revision=revision))
    comps.append(floor_region("C-RECESS", [(8.0, 4.15, 9.2, 5.65)], revision=revision))
    comps.append(GeometryComponent("COL-1", KIND_COLUMN, [geom.Rect(3.4, 3.4, 3.8, 3.8)], FLOOR, revision))
    comps.append(floor_region("C-TERRACE", [(0.0, 6.0, 8.0, 8.0)], revision=revision, kind=KIND_EXTERNAL))
    openings_.append(opening("OP-A", (1.0, 4.0, 1.9, 4.15), geom.AXIS_X, 0.90, 2.10, revision=revision))
    openings_.append(opening("OP-B", (5.0, 4.0, 5.9, 4.15), geom.AXIS_X, 0.90, 2.10, revision=revision))
    openings_.append(opening("OP-W", (4.0, 1.0, 4.2 + shift, 2.2), geom.AXIS_Y, 1.20, 1.50, kind="WINDOW",
                             revision=revision))
    labels.append(Label("ROOM A", 2.0, 2.0))
    labels.append(Label("ROOM B", 6.0, 2.0))
    labels.append(Label("CORRIDOR", 4.0, 4.9))
    return {"COMPONENTS": comps, "BARRIERS": barriers, "OPENINGS": openings_, "LABELS": labels,
            "REVISION": revision, "TOLERANCE_M": TOL, "SLIVER_MIN_DIMENSION_M": SLIVER_MIN}


def second_plan(revision="S1"):
    """An unrelated plan, drawn differently: an L-shaped workshop, an office behind a 100 mm partition, one door.

    It exists to show the same code paths run on a drawing that shares nothing with the first: different shapes,
    a thickness neither of the other fixtures uses, and a room that is not a rectangle.
    """
    comps = [
        # the L, including the door reveal, which belongs to the room the door opens from
        floor_region("X-1", [(0.0, 0.0, 5.0, 2.0), (0.0, 2.0, 2.0, 5.0), (2.0, 3.0, 2.1, 3.9)],
                     revision=revision),
        wall_band("X-W-H", (2.1, 2.0, 5.0, 2.1), 0.10, geom.AXIS_X, revision=revision),
        wall_band("X-W-BELOW", (2.0, 2.0, 2.1, 3.0), 0.10, geom.AXIS_Y, revision=revision),
        wall_band("X-W-ABOVE", (2.0, 3.9, 2.1, 5.0), 0.10, geom.AXIS_Y, revision=revision),
        floor_region("X-2", [(2.1, 2.1, 5.0, 5.0)], revision=revision),
    ]
    ops = [opening("X-OP", (2.0, 3.0, 2.1, 3.9), geom.AXIS_Y, 0.90, 2.10, revision=revision)]
    labels = [Label("WORKSHOP", 1.0, 1.0), Label("OFFICE", 3.5, 3.5)]
    return {"COMPONENTS": comps, "BARRIERS": [], "OPENINGS": ops, "LABELS": labels,
            "REVISION": revision, "TOLERANCE_M": TOL, "SLIVER_MIN_DIMENSION_M": SLIVER_MIN}
