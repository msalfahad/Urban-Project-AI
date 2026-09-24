"""Synthetic drawings: small plans with a known answer, owing nothing to any real project.

These exist so the algorithms can be proved before a real drawing is allowed anywhere near them.  Each builder
returns the same shape of input the adapters produce from a real source, so the pipeline under test is the
production pipeline.
"""

from __future__ import annotations

from engine.qs_core import admission as AD, evidence as EV, geom
from engine.qs_core.entities import (GeometryComponent, KIND_COLUMN, KIND_EXTERNAL, KIND_FLOOR_REGION,
                                     KIND_WALL_BAND, Label, Opening)
from engine.qs_core.spaces import Barrier

FLOOR = "LEVEL_1"
TOL = 0.005                  # 5 mm: a drawing authored to the millimetre
SLIVER_MIN = 0.30            # nothing narrower than 300 mm is a space
MAX_OPENING_SPAN = 3.00      # the widest gap in a wall line these fixtures ever put an opening in
DRAFTING_RESOLUTION = 0.05   # these fixtures are drawn to 50 mm; anything finer is two lines that did not meet
WALL_HEIGHT = EV.resolve("wall height", [EV.Claim(3.0, EV.OWNER_PROJECT_INPUT, "FIXTURE_WALL_HEIGHT")], TOL)


def floor_region(ref, rects, floor=FLOOR, revision="R1", kind=KIND_FLOOR_REGION):
    return GeometryComponent(ref, kind, [geom.Rect(*r) for r in rects], floor, revision)


def wall_band(ref, rect, thickness, axis, floor=FLOOR, revision="R1", layer="WALL"):
    return GeometryComponent(ref, KIND_WALL_BAND, [geom.Rect(*rect)], floor, revision,
                             thickness=thickness, axis=axis, layer=layer)


def opening(ref, rect, axis, width, height, kind="DOOR", floor=FLOOR, revision="R1"):
    o = Opening(ref, geom.Rect(*rect), floor, revision, opening_type=kind, width=width, height=height,
                width_source=EV.MEASURED_GEOMETRY, height_source=EV.DRAWING_DIMENSION, axis=axis)
    o.admission = {"CLASSIFICATION": AD.CONFIRMED_OPENING,
                   "PROVENANCE": [{"KIND": AD.PROV_BLOCK, "REFERENCE": f"BLOCK::{kind}"}],
                   "WIDTH_EVIDENCE": EV.resolve("width", [EV.Claim(width, EV.MEASURED_GEOMETRY, ref)], TOL),
                   "HEIGHT_EVIDENCE": EV.resolve("height", [EV.Claim(height, EV.DRAWING_DIMENSION,
                                                                     f"SCHEDULE::{ref}")], TOL)}
    return o


def candidate(ref, rect, axis, kind="DOOR", floor=FLOOR, revision="R1", height=2.10, block=True,
              schedule_ref=None, layer=None, origin="EXTRACTED_GEOMETRY"):
    """A thing that might be an opening, as an extractor hands it over: geometry plus whatever vouches for it."""
    c = AD.Candidate(ref, geom.Rect(*rect), floor, revision, axis=axis, opening_type=kind, origin=origin,
                     block_ref=f"BLOCK::{kind}::{ref}" if block else None,
                     schedule_ref=schedule_ref, layer=layer)
    if height is not None:
        c.height_claims = [EV.Claim(height, EV.DRAWING_DIMENSION, f"SCHEDULE::{ref}",
                                    {"WHAT": "height stated for this opening type"})]
    return c


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
    openings_.append(candidate("OP-A", (1.0, 4.0, 1.9, 4.15), geom.AXIS_X, revision=revision))
    openings_.append(candidate("OP-B", (5.0, 4.0, 5.9, 4.15), geom.AXIS_X, revision=revision))
    openings_.append(candidate("OP-W", (4.0, 1.0, 4.2 + shift, 2.2), geom.AXIS_Y, kind="WINDOW",
                               height=1.50, revision=revision))
    labels.append(Label("ROOM A", 2.0, 2.0))
    labels.append(Label("ROOM B", 6.0, 2.0))
    labels.append(Label("CORRIDOR", 4.0, 4.9))
    return {"COMPONENTS": comps, "BARRIERS": barriers, "CANDIDATES": openings_, "LABELS": labels,
            "REVISION": revision, "TOLERANCE_M": TOL, "SLIVER_MIN_DIMENSION_M": SLIVER_MIN,
            "FLOOR": FLOOR}


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
    ops = [candidate("X-OP", (2.0, 3.0, 2.1, 3.9), geom.AXIS_Y, revision=revision)]
    labels = [Label("WORKSHOP", 1.0, 1.0), Label("OFFICE", 3.5, 3.5)]
    return {"COMPONENTS": comps, "BARRIERS": [], "CANDIDATES": ops, "LABELS": labels,
            "REVISION": revision, "TOLERANCE_M": TOL, "SLIVER_MIN_DIMENSION_M": SLIVER_MIN,
            "FLOOR": FLOOR}


# ------------------------------------------------------------------ admission fixtures (US-20)
def millimetre_drafting_gap():
    """Two wall segments that miss each other by 2 mm.  Nothing names it; it is not a door."""
    wall = wall_band("W-1", (0.0, 0.0, 6.0, 0.20), 0.20, geom.AXIS_X)
    c = AD.Candidate("CAND-GAP", geom.Rect(3.0, 0.0, 3.002, 0.20), FLOOR, "R1", axis=geom.AXIS_X)
    return [wall], [c], []


def a_real_narrow_opening():
    """A 600 mm opening - narrow, and drawn as a named block with a schedule row.  It is real."""
    wall = wall_band("W-1", (0.0, 0.0, 6.0, 0.20), 0.20, geom.AXIS_X)
    c = candidate("CAND-NARROW", (2.0, 0.0, 2.6, 0.20), geom.AXIS_X, kind="DOOR")
    schedule = [{"SCHEDULE_REF": "D-09", "FLOOR": FLOOR, "TYPE": "DOOR", "WIDTH_M": 0.60, "HEIGHT_M": 2.10}]
    return [wall], [c], schedule


def the_same_door_drawn_twice():
    """One physical door: once as extracted geometry, once from the drawing's own opening register."""
    wall = wall_band("W-1", (0.0, 0.0, 6.0, 0.20), 0.20, geom.AXIS_X)
    a = candidate("CAND-GEOM", (2.0, 0.0, 2.9, 0.20), geom.AXIS_X)
    b = candidate("CAND-REGISTER", (2.01, 0.0, 2.91, 0.20), geom.AXIS_X, origin="DRAWING_REGISTER",
                  schedule_ref="D-01")
    schedule = [{"SCHEDULE_REF": "D-01", "FLOOR": FLOOR, "TYPE": "DOOR", "WIDTH_M": 0.90, "HEIGHT_M": 2.10}]
    return [wall], [a, b], schedule


def an_unlabelled_wall_gap():
    """The wall stops and starts again.  Nothing says whether it is a door, an archway or a missing line."""
    left = wall_band("W-L", (0.0, 0.0, 2.0, 0.20), 0.20, geom.AXIS_X)
    right = wall_band("W-R", (3.0, 0.0, 6.0, 0.20), 0.20, geom.AXIS_X)
    c = AD.Candidate("CAND-UNNAMED", geom.Rect(2.0, 0.0, 3.0, 0.20), FLOOR, "R1", axis=geom.AXIS_X)
    return [left, right], [c], []


def two_different_openings_of_the_same_width():
    """Same width, different places.  Two doors, not one drawn twice."""
    wall = wall_band("W-1", (0.0, 0.0, 10.0, 0.20), 0.20, geom.AXIS_X)
    a = candidate("CAND-A", (1.0, 0.0, 1.9, 0.20), geom.AXIS_X)
    b = candidate("CAND-B", (7.0, 0.0, 7.9, 0.20), geom.AXIS_X)
    return [wall], [a, b], []


def a_candidate_in_open_space():
    """A gap in nothing: it intersects no wall, so there is nothing for it to be a hole in."""
    wall = wall_band("W-1", (0.0, 0.0, 6.0, 0.20), 0.20, geom.AXIS_X)
    c = AD.Candidate("CAND-FLOATING", geom.Rect(2.0, 3.0, 2.9, 3.2), FLOOR, "R1", axis=geom.AXIS_X)
    return [wall], [c], []


def a_scheduled_opening_nobody_drew():
    wall = wall_band("W-1", (0.0, 0.0, 6.0, 0.20), 0.20, geom.AXIS_X)
    schedule = [{"SCHEDULE_REF": "W-14", "FLOOR": FLOOR, "TYPE": "WINDOW", "WIDTH_M": 1.20, "HEIGHT_M": 1.50}]
    return [wall], [], schedule


# ------------------------------------------------------------------ wall continuity fixtures
def two_unrelated_walls_two_metres_apart():
    """Collinear, same thickness, 2 m of open space between them, and nothing spanning it.

    Below the maximum opening span, so a rule that bridges on span alone joins them into one wall that was never
    built - and then measures it, deducts from it, and bills it.
    """
    a = wall_band("W-A", (0.0, 0.0, 3.0, 0.20), 0.20, geom.AXIS_X)
    b = wall_band("W-B", (5.0, 0.0, 9.0, 0.20), 0.20, geom.AXIS_X)
    return [a, b]


def two_segments_with_a_door_between_them():
    """The same shape, with a confirmed door filling the gap: one wall, and the door is in it."""
    a = wall_band("W-A", (0.0, 0.0, 3.0, 0.20), 0.20, geom.AXIS_X)
    b = wall_band("W-B", (3.9, 0.0, 9.0, 0.20), 0.20, geom.AXIS_X)
    door = opening("OP-D", (3.0, 0.0, 3.9, 0.20), geom.AXIS_X, 0.90, 2.10)
    return [a, b], [door]


def a_gap_spanned_by_a_lintel():
    a = wall_band("W-A", (0.0, 0.0, 3.0, 0.20), 0.20, geom.AXIS_X)
    b = wall_band("W-B", (5.0, 0.0, 9.0, 0.20), 0.20, geom.AXIS_X)
    lintel = geom.Rect(2.9, 0.0, 5.1, 0.20)
    return [a, b], [lintel]


# ------------------------------------------------------------------ mixed opening-basis fixture
def one_wall_spans_its_door_and_another_stops_at_the_jambs():
    """Two walls in one drawing, drawn by different hands.  One Boolean cannot be right for both."""
    spanning = wall_band("W-SPAN", (0.0, 0.0, 6.0, 0.20), 0.20, geom.AXIS_X)
    door_in_spanning = opening("OP-S", (2.0, 0.0, 2.9, 0.20), geom.AXIS_X, 0.90, 2.10)
    left = wall_band("W-STOP-L", (0.0, 5.0, 2.0, 5.20), 0.20, geom.AXIS_X)
    right = wall_band("W-STOP-R", (2.9, 5.0, 6.0, 5.20), 0.20, geom.AXIS_X)
    door_in_stopping = opening("OP-J", (2.0, 5.0, 2.9, 5.20), geom.AXIS_X, 0.90, 2.10)
    return [spanning, left, right], [door_in_spanning, door_in_stopping]


# ------------------------------------------------------------------ masonry identity fixtures
def a_drawing_with_artefacts_among_its_walls():
    """Real walls of two thicknesses, plus the things every extractor also produces."""
    walls = [
        wall_band("M-A", (0.0, 0.0, 8.0, 0.20), 0.20, geom.AXIS_X),
        wall_band("M-B", (0.0, 5.0, 8.0, 5.20), 0.20, geom.AXIS_X),
        wall_band("M-C", (0.0, 0.0, 0.15, 5.20), 0.15, geom.AXIS_Y),
        wall_band("M-D", (7.85, 0.0, 8.0, 5.20), 0.15, geom.AXIS_Y),
        # the little square where two walls cross: as short as it is thick, inside the wall that crosses it
        wall_band("M-JUNCTION", (0.0, 0.0, 0.15, 0.15), 0.15, geom.AXIS_X),
        # a band with a thickness nothing else in the drawing uses, one cell long
        wall_band("M-ODD", (3.0, 2.0, 3.30, 2.13), 0.13, geom.AXIS_X),
    ]
    return walls


def the_same_wall_drawn_on_two_layers():
    """One wall traced twice, the second copy 30 mm out of register - far enough not to be one line."""
    a = wall_band("M-A", (0.0, 0.0, 8.0, 0.20), 0.20, geom.AXIS_X, layer="WALL")
    b = wall_band("M-A-COPY", (0.0, 0.03, 7.5, 0.23), 0.20, geom.AXIS_X, layer="ARCH")
    c = wall_band("M-B", (0.0, 5.0, 8.0, 5.20), 0.20, geom.AXIS_X)
    return [a, b, c]


def a_wall_traced_twice_on_the_same_line():
    """Two segments on exactly one line, overlapping: the same material, offered twice."""
    a = wall_band("M-A", (0.0, 0.0, 8.0, 0.20), 0.20, geom.AXIS_X, layer="WALL")
    b = wall_band("M-A-COPY", (0.0, 0.0, 7.5, 0.20), 0.20, geom.AXIS_X, layer="ARCH")
    return [a, b]


# ------------------------------------------------------------------ metamorphic transformations
# The transformations themselves live in the engine, because the real adapter runs them against the real
# drawing: a metamorphic check that only ever runs on fixtures proves nothing about production.
from engine.qs_core.transforms import (quantity_fingerprint, resegment_plan,  # noqa: E402,F401
                                       transform_plan)


def run(plan, wall_height=3.0, **kw):
    """Run the production pipeline over a fixture with this fixture family's declared source facts.

    Every argument the engine refuses to default is supplied here, in one place, so a test reads as a statement
    about the building rather than a list of parameters - and so that changing what the engine demands changes
    one function rather than every test.
    """
    from engine.qs_core import pipeline

    annotations = kw.pop("annotations", None)
    if annotations is None:
        annotations = {c.component_ref: {"MATERIAL": "BLOCKWORK", "LAYER": "WALL"}
                       for c in plan["COMPONENTS"] if c.kind == KIND_WALL_BAND}
    height = (EV.resolve("wall height", [EV.Claim(wall_height, EV.OWNER_PROJECT_INPUT, "FIXTURE_INPUT")], TOL)
              if wall_height is not None else None)
    return pipeline.run(plan, max_opening_span=MAX_OPENING_SPAN, drafting_resolution_m=DRAFTING_RESOLUTION,
                        wall_height_evidence=height, annotations=annotations,
                        masonry_materials=("BLOCKWORK",), **kw)
