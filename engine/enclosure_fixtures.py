"""E97 — ten known-answer rooms, each with ink that is not its boundary.

§6. The enclosure mechanism is built and frozen against these BEFORE any
real drawing is evaluated, because a threshold chosen by watching AR-00
rooms improve is a threshold fitted to one sheet.

Every fixture is built in millimetres from the room outward, so the right
answer is arithmetic rather than opinion: the walls are placed, the clear
internal area follows from where their faces are, and the fixture ink is
added afterwards where a draughtsman would put it — a bathtub against a
wall, a stair nosing across a landing, a kitchen run along two sides.

Each fixture carries BOTH representations:

    mask        what a renderer would produce, fixtures included
    candidates  the wall faces, caps and jambs a vector reader would find

A fixture's mask deliberately makes the raster contour wrong. The test is
that the enclosure ignores it and still returns the arithmetic answer — and,
for MISSING_WALL, that it refuses.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from engine.boundary_match import VectorCandidate
from engine.space_objects import (SRC_VECTOR_OPENING_JAMB,
                                  SRC_VECTOR_WALL_FACE)

PX_MM = 10.0                    # a coarse, honest pixel for the fixtures


@dataclass
class Fixture:
    """One room whose answer is known by construction."""

    name: str
    seed_mm: tuple
    extent_mm: tuple
    candidates: list = field(default_factory=list)
    expected_area_m2: float | None = None
    expect_complete: bool = True
    expected_leak_reason: str = ""
    fixture_ink: list = field(default_factory=list)   # boxes in mm
    # Areas that are NOT part of this region at all — the bite out of an
    # L-shaped room is another space, not ink inside this one. Kept apart
    # from fixture_ink so the mask matches what the walls describe.
    void_mm: list = field(default_factory=list)
    room_mm: tuple = (0.0, 0.0, 0.0, 0.0)
    note: str = ""

    def mask(self, *, px_mm: float = PX_MM) -> np.ndarray:
        """The render: free space inside the walls, minus the fixture ink.

        This is what the raster stage sees. Its contour detours around
        every fixture, which is exactly the input the enclosure must not
        follow.
        """
        x0, y0, x1, y1 = self.extent_mm
        w = int((x1 - x0) / px_mm) + 2
        h = int((y1 - y0) / px_mm) + 2
        free = np.zeros((h, w), bool)

        rx0, ry0, rx1, ry1 = self.room_mm
        free[_px(ry0 - y0, px_mm):_px(ry1 - y0, px_mm),
             _px(rx0 - x0, px_mm):_px(rx1 - x0, px_mm)] = True
        for fx0, fy0, fx1, fy1 in list(self.void_mm) + list(
                self.fixture_ink):
            free[_px(fy0 - y0, px_mm):_px(fy1 - y0, px_mm),
                 _px(fx0 - x0, px_mm):_px(fx1 - x0, px_mm)] = False
        return free

    def record(self) -> dict:
        return {"fixture": self.name,
                "expected_area_m2": self.expected_area_m2,
                "expect_complete": self.expect_complete,
                "expected_leak_reason": self.expected_leak_reason,
                "fixture_ink_boxes": len(self.fixture_ink),
                "candidate_lines": len(self.candidates),
                "note": self.note}


def _px(mm: float, px_mm: float) -> int:
    return max(int(round(mm / px_mm)), 0)


def _walls(x0, y0, x1, y1, *, thickness=200.0, prefix="W",
           sides="NSEW", src=SRC_VECTOR_WALL_FACE):
    """The four faces of a room's enclosing walls, as drawn lines.

    The room is x0..x1 by y0..y1 CLEAR, so the faces are exactly on those
    coordinates and each face is drawn across the full side plus the wall
    thickness at each end — which is how a wall is actually drawn: its face
    runs past the corner into the junction.
    """
    out = []
    t = thickness
    if "N" in sides:
        out.append(VectorCandidate(f"{prefix}-N", "H", y0, x0 - t, x1 + t,
                                   src))
    if "S" in sides:
        out.append(VectorCandidate(f"{prefix}-S", "H", y1, x0 - t, x1 + t,
                                   src))
    if "W" in sides:
        out.append(VectorCandidate(f"{prefix}-W", "V", x0, y0 - t, y1 + t,
                                   src))
    if "E" in sides:
        out.append(VectorCandidate(f"{prefix}-E", "V", x1, y0 - t, y1 + t,
                                   src))
    return out


# --------------------------------------------------------------- the ten

def bedroom_with_furniture() -> Fixture:
    """A 4.0 x 3.0 m bedroom with a wardrobe and a bed drawn inside."""
    x0, y0, x1, y1 = 0.0, 0.0, 4000.0, 3000.0
    return Fixture(
        name="RECTANGULAR_BEDROOM_WITH_FURNITURE",
        seed_mm=(2000.0, 1500.0), extent_mm=(x0, y0, x1, y1),
        room_mm=(x0, y0, x1, y1),
        candidates=_walls(x0, y0, x1, y1),
        expected_area_m2=12.0,
        fixture_ink=[(0.0, 0.0, 600.0, 2400.0),        # wardrobe on the west
                     (1400.0, 2100.0, 3400.0, 3000.0)],  # bed on the south
        note=("the wardrobe and the bed touch the walls, so the raster "
              "contour steps around both. Neither is a boundary"))


def bathroom_with_sanitary_ware() -> Fixture:
    """2.5 x 1.85 m — the case that made every bathroom unmeasurable."""
    x0, y0, x1, y1 = 0.0, 0.0, 2500.0, 1850.0
    return Fixture(
        name="RECTANGULAR_BATHROOM_WITH_BATHTUB_WC_BASIN",
        seed_mm=(1600.0, 900.0), extent_mm=(x0, y0, x1, y1),
        room_mm=(x0, y0, x1, y1),
        candidates=_walls(x0, y0, x1, y1),
        expected_area_m2=4.625,
        fixture_ink=[(0.0, 0.0, 700.0, 1700.0),        # bath along the west
                     (1900.0, 0.0, 2500.0, 400.0),     # WC in the corner
                     (1000.0, 1500.0, 1600.0, 1850.0)],  # basin
        note=("three sanitary fittings against three different walls. The "
              "clear internal area is the room, not the room minus the "
              "bath"))


def room_with_door_opening() -> Fixture:
    """A doorway: the wall face stops, and a validated jamb closes it."""
    x0, y0, x1, y1 = 0.0, 0.0, 3000.0, 2500.0
    walls = _walls(x0, y0, x1, y1, sides="NSW")
    # The east wall is drawn in two pieces with a 900 mm doorway between.
    walls += [
        VectorCandidate("W-E1", "V", x1, y0 - 200.0, 800.0,
                        SRC_VECTOR_WALL_FACE),
        VectorCandidate("W-E2", "V", x1, 1700.0, y1 + 200.0,
                        SRC_VECTOR_WALL_FACE),
        # The threshold line across the opening, from portal geometry.
        VectorCandidate("PT-1-J", "V", x1, 800.0, 1700.0,
                        SRC_VECTOR_OPENING_JAMB),
    ]
    return Fixture(
        name="ROOM_WITH_DOOR_OPENING",
        seed_mm=(1500.0, 1250.0), extent_mm=(x0, y0, x1, y1),
        room_mm=(x0, y0, x1, y1), candidates=walls,
        expected_area_m2=7.5,
        fixture_ink=[(2700.0, 700.0, 3000.0, 1800.0)],   # the door leaf
        note=("the clear internal boundary crosses the opening on the "
              "jamb line. Without the portal the room is not enclosed"))


def room_with_door_opening_unvalidated() -> Fixture:
    """The same room with NO portal geometry: it must refuse."""
    got = room_with_door_opening()
    got.name = "ROOM_WITH_DOOR_OPENING_AND_NO_VALIDATED_PORTAL"
    got.candidates = [c for c in got.candidates
                      if c.source_type != SRC_VECTOR_OPENING_JAMB]
    got.expected_area_m2 = None
    got.expect_complete = False
    got.note = ("an opening nobody has validated is a hole in the "
                "boundary. The space is PARTIAL, not 7.5 m²")
    return got


def l_shaped_room() -> Fixture:
    """An L: 5.0 x 4.0 m with a 2.0 x 1.5 m bite out of one corner."""
    x0, y0, x1, y1 = 0.0, 0.0, 5000.0, 4000.0
    bx, by = 3000.0, 2500.0          # the inner corner of the L
    cands = [
        VectorCandidate("L-N", "H", y0, x0 - 200.0, x1 + 200.0,
                        SRC_VECTOR_WALL_FACE),
        VectorCandidate("L-W", "V", x0, y0 - 200.0, y1 + 200.0,
                        SRC_VECTOR_WALL_FACE),
        VectorCandidate("L-S", "H", y1, x0 - 200.0, bx + 200.0,
                        SRC_VECTOR_WALL_FACE),
        VectorCandidate("L-E", "V", x1, y0 - 200.0, by + 200.0,
                        SRC_VECTOR_WALL_FACE),
        VectorCandidate("L-INNER-H", "H", by, bx - 200.0, x1 + 200.0,
                        SRC_VECTOR_WALL_FACE),
        VectorCandidate("L-INNER-V", "V", bx, by - 200.0, y1 + 200.0,
                        SRC_VECTOR_WALL_FACE),
    ]
    return Fixture(
        name="L_SHAPED_ROOM",
        seed_mm=(1000.0, 1000.0), extent_mm=(x0, y0, x1, y1),
        room_mm=(x0, y0, x1, y1), candidates=cands,
        expected_area_m2=(5.0 * 4.0) - (2.0 * 1.5),
        void_mm=[(bx, by, x1, y1)],          # the bite is another space
        fixture_ink=[(0.0, 3400.0, 1200.0, 4000.0)],
        note="six sides, and the inner corner is a real feature not a jog")


def mixed_wall_thicknesses() -> Fixture:
    """Four walls of four thicknesses. The clear area is unaffected."""
    x0, y0, x1, y1 = 0.0, 0.0, 3600.0, 2800.0
    cands = [
        VectorCandidate("M-N", "H", y0, x0 - 100.0, x1 + 100.0,
                        SRC_VECTOR_WALL_FACE),
        VectorCandidate("M-S", "H", y1, x0 - 300.0, x1 + 300.0,
                        SRC_VECTOR_WALL_FACE),
        VectorCandidate("M-W", "V", x0, y0 - 150.0, y1 + 150.0,
                        SRC_VECTOR_WALL_FACE),
        VectorCandidate("M-E", "V", x1, y0 - 440.0, y1 + 440.0,
                        SRC_VECTOR_WALL_FACE),
    ]
    return Fixture(
        name="MIXED_WALL_THICKNESSES",
        seed_mm=(1800.0, 1400.0), extent_mm=(x0, y0, x1, y1),
        room_mm=(x0, y0, x1, y1), candidates=cands,
        expected_area_m2=3.6 * 2.8,
        fixture_ink=[(3200.0, 1000.0, 3600.0, 1800.0)],
        note=("a 100 mm partition and a 440 mm external wall bound the same "
              "room. Thickness changes nothing about the clear area"))


def room_with_window() -> Fixture:
    """A window is drawn in the wall and does not open the boundary."""
    x0, y0, x1, y1 = 0.0, 0.0, 4200.0, 3200.0
    cands = _walls(x0, y0, x1, y1)
    return Fixture(
        name="ROOM_WITH_WINDOW",
        seed_mm=(2100.0, 1600.0), extent_mm=(x0, y0, x1, y1),
        room_mm=(x0, y0, x1, y1), candidates=cands,
        expected_area_m2=4.2 * 3.2,
        fixture_ink=[(1200.0, 0.0, 3000.0, 120.0)],     # the window symbol
        note=("the window's sill and frame lines sit inside the room's "
              "north face. The face is continuous, so the room closes"))


def open_plan_living_dining() -> Fixture:
    """One physical space, two functional zones. No barrier between them."""
    x0, y0, x1, y1 = 0.0, 0.0, 9000.0, 5000.0
    cands = _walls(x0, y0, x1, y1)
    # A column stands free in the middle: real material, not a partition.
    cands += [
        VectorCandidate("COL-N", "H", 2400.0, 4200.0, 4600.0,
                        SRC_VECTOR_WALL_FACE),
        VectorCandidate("COL-S", "H", 2800.0, 4200.0, 4600.0,
                        SRC_VECTOR_WALL_FACE),
        VectorCandidate("COL-W", "V", 4200.0, 2400.0, 2800.0,
                        SRC_VECTOR_WALL_FACE),
        VectorCandidate("COL-E", "V", 4600.0, 2400.0, 2800.0,
                        SRC_VECTOR_WALL_FACE),
    ]
    return Fixture(
        name="OPEN_PLAN_LIVING_DINING",
        seed_mm=(1500.0, 1500.0), extent_mm=(x0, y0, x1, y1),
        room_mm=(x0, y0, x1, y1), candidates=cands,
        # 9.0 x 5.0 LESS the 0.4 x 0.4 column: the column is material
        # standing in the room, and a clear internal floor area deducts it.
        # This expectation was 45.0 until the algorithm returned 44.84 and
        # was right — the column came back as a 0.16 m² hole.
        expected_area_m2=9.0 * 5.0 - 0.4 * 0.4,
        fixture_ink=[(4200.0, 2400.0, 4600.0, 2800.0),
                     (6000.0, 3600.0, 8400.0, 5000.0)],
        note=("two labels do not make two rooms. The free-standing column "
              "is material inside one space: it is DEDUCTED as a hole, not "
              "treated as a boundary and not ignored"))


def shaft_beside_bathroom() -> Fixture:
    """A 0.9 x 0.9 m shaft sharing a wall with a bathroom."""
    x0, y0, x1, y1 = 0.0, 0.0, 900.0, 900.0
    return Fixture(
        name="SHAFT_BESIDE_BATHROOM",
        seed_mm=(450.0, 450.0), extent_mm=(x0, y0, x1, y1),
        room_mm=(x0, y0, x1, y1),
        candidates=_walls(x0, y0, x1, y1, prefix="SH"),
        expected_area_m2=0.81,
        fixture_ink=[(0.0, 0.0, 900.0, 200.0)],          # hatching
        note=("a shaft encloses perfectly well. Whether it is a WASHROOM "
              "is an identity question this stage never asks"))


def partial_missing_wall() -> Fixture:
    """Three sides drawn, the fourth absent. It MUST refuse."""
    x0, y0, x1, y1 = 0.0, 0.0, 3500.0, 2600.0
    return Fixture(
        name="PARTIAL_MISSING_WALL",
        seed_mm=(1750.0, 1300.0), extent_mm=(x0, y0, x1, y1),
        room_mm=(x0, y0, x1, y1),
        candidates=_walls(x0, y0, x1, y1, sides="NWE"),
        expected_area_m2=None, expect_complete=False,
        fixture_ink=[(200.0, 2200.0, 1400.0, 2600.0)],
        note=("the south wall was never drawn. A rectangle would be "
              "convenient and is not evidence, so the answer is PARTIAL"))


def stair_nosing_inside_region() -> Fixture:
    """A landing whose nosing lines cross the region."""
    x0, y0, x1, y1 = 0.0, 0.0, 2800.0, 4000.0
    return Fixture(
        name="STAIR_NOSING_DETAIL_INSIDE_REGION",
        seed_mm=(1400.0, 500.0), extent_mm=(x0, y0, x1, y1),
        room_mm=(x0, y0, x1, y1),
        candidates=_walls(x0, y0, x1, y1, prefix="ST"),
        expected_area_m2=2.8 * 4.0,
        fixture_ink=[(0.0, 1200.0 + k * 280.0, 2800.0,
                      1200.0 + k * 280.0 + 60.0) for k in range(9)],
        note=("nine nosing lines cross the whole region, cutting the "
              "raster mask into ten strips. None of them is a wall"))


def corner_from_two_faces_that_reach() -> Fixture:
    """§12: two supported faces that meet define the corner between them.

    The south face stops 1.5 mm short of the west face — a hairline
    plotting gap at a junction, inside the frozen reach. The corner is the
    intersection of two independently drawn lines, so it may be created.
    """
    x0, y0, x1, y1 = 0.0, 0.0, 3000.0, 2400.0
    cands = _walls(x0, y0, x1, y1, sides="NWE")
    cands.append(VectorCandidate("C-S", "H", y1, x0 + 1.5, x1 + 200.0,
                                 SRC_VECTOR_WALL_FACE))
    return Fixture(
        name="CORNER_FROM_TWO_FACES_THAT_REACH",
        seed_mm=(1500.0, 1200.0), extent_mm=(x0, y0, x1, y1),
        room_mm=(x0, y0, x1, y1), candidates=cands,
        expected_area_m2=3.0 * 2.4,
        note=("a 1.5 mm hairline at the junction is plotting noise. Both "
              "faces exist as drawing geometry and their extents reach the "
              "junction, so the corner is constructed, not invented"))


def corner_refused_when_a_face_stops_short() -> Fixture:
    """§5: a wall is never extended arbitrarily until it hits something."""
    x0, y0, x1, y1 = 0.0, 0.0, 3000.0, 2400.0
    cands = _walls(x0, y0, x1, y1, sides="NWE")
    cands.append(VectorCandidate("C-S", "H", y1, x0 + 50.0, x1 + 200.0,
                                 SRC_VECTOR_WALL_FACE))
    return Fixture(
        name="CORNER_REFUSED_WHEN_A_FACE_STOPS_SHORT",
        seed_mm=(1500.0, 1200.0), extent_mm=(x0, y0, x1, y1),
        room_mm=(x0, y0, x1, y1), candidates=cands,
        expected_area_m2=None, expect_complete=False,
        note=("50 mm is not plotting noise, it is a gap. Closing it would "
              "be extending a wall until it hit another line"))


def corner_refused_with_only_one_side_supported() -> Fixture:
    """§5: do NOT create a corner if only one side is supported."""
    x0, y0, x1, y1 = 0.0, 0.0, 3000.0, 2400.0
    cands = _walls(x0, y0, x1, y1, sides="NWS")
    return Fixture(
        name="CORNER_REFUSED_WITH_ONLY_ONE_SIDE_SUPPORTED",
        seed_mm=(1500.0, 1200.0), extent_mm=(x0, y0, x1, y1),
        room_mm=(x0, y0, x1, y1), candidates=cands,
        expected_area_m2=None, expect_complete=False,
        note=("the north and south faces both run past where the east "
              "wall would be. Two parallel lines do not make a corner, and "
              "nothing supported closes the east side"))


ALL = (bedroom_with_furniture, bathroom_with_sanitary_ware,
       room_with_door_opening, room_with_door_opening_unvalidated,
       l_shaped_room, mixed_wall_thicknesses, room_with_window,
       open_plan_living_dining, shaft_beside_bathroom,
       partial_missing_wall, stair_nosing_inside_region,
       corner_from_two_faces_that_reach,
       corner_refused_when_a_face_stops_short,
       corner_refused_with_only_one_side_supported)


def fixtures() -> list:
    return [make() for make in ALL]
