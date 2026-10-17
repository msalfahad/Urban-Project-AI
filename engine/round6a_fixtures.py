"""Round 6A — which face does a room stop at, and what is not a wall.

Nine drawings whose answers are known because the fixture drew them, and
none of which contains a coordinate from any real project. Each is here
because a real failure would otherwise pass unnoticed:

    A  two rooms share a 200 mm wall and take OPPOSITE faces of it
    B  a room on an external wall takes the INTERNAL face
    C  a wall drawn with finish and detail lines beside it
    D  a doorway interrupts a wall and the faces run on to the jambs
    E  four walls of four different thicknesses round one room
    F  a column standing in a room's corner
    G  a finish line 20 mm inside the structural face
    H  one wall between two rooms of different clear widths
    I  ground outside the building envelope with NO site boundary

The measured answer is checked against the fixture's own arithmetic. There
is no tolerance band and no expected range: the clear internal rectangle
of a room whose walls this file placed is known exactly.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from engine import round4_fixtures as r4
from engine.cad_fixtures import Builder

W, D, G, TXT = r4.W, r4.D, r4.G, r4.TXT


@dataclass(frozen=True)
class Case:
    name: str
    what_it_tests: str
    decode: dict
    expect: dict = field(default_factory=dict)


def _shell(b, w, h, *, t=200.0, door=True):
    openings = [("S", w / 2 - 450, w / 2 + 450)] if door else []
    r4._ring(b, 0, 0, w, h, layer=W, t=t, openings=openings)
    if door:
        r4._door(b, "DENT", w / 2 - 450, 0, 900, rotation=1.5707963267948966)


# ------------------------------------------------------------------- cases

def _a():
    """One 200 mm wall, two rooms, two different faces of it."""
    b = Builder()
    _shell(b, 9000, 5000)
    r4._partition_v(b, 4000, 0, 5000, t=200.0,
                    gaps=[(2000, 2900)])
    r4._door(b, "DA", 4000, 2000, 900)
    r4._stamp(b, "S1", ["KITCHEN"], 2000, 2500)
    r4._stamp(b, "S2", ["STORE"], 6500, 2500)
    return Case(
        "A_TWO_ROOMS_SHARE_ONE_WALL",
        "each room stops at the face of the shared wall that faces IT",
        b.build(),
        # the ring's INNER faces are at 0 and at w/h, so the west room is
        # x 0..4000 by y 0..5000 and the east room x 4200..9000 by the same
        expect={"clear_areas_m2": [4.0 * 5.0, 4.8 * 5.0],
                "no_centreline_area": True,
                "opposite_faces_of_one_wall": True})


def _b():
    """A room on an external wall takes the internal face, not the outer."""
    b = Builder()
    _shell(b, 6000, 4000, t=300.0)
    r4._stamp(b, "S1", ["BEDROOM"], 3000, 2000)
    return Case(
        "B_EXTERNAL_WALL_INTERNAL_FACE",
        "the internal face bounds the floor; the external face never does",
        b.build(),
        expect={"clear_areas_m2": [6.0 * 4.0],
                "no_external_face_used": True})


def _c():
    """A skirting line and a tile joint drawn beside the wall face."""
    b = Builder()
    _shell(b, 7000, 5000)
    # two detail lines standing inside the room, parallel to the west wall
    r4._run(b, "V", 340.0, 400.0, 4600.0, W)
    r4._run(b, "V", 500.0, 400.0, 4600.0, W)
    # and one along the north wall
    r4._run(b, "H", 4700.0, 400.0, 6600.0, W)
    r4._stamp(b, "S1", ["SALOON"], 3500, 2500)
    return Case(
        "C_FINISH_AND_DETAIL_LINES_BESIDE_A_WALL",
        "a line with floor on both sides bounds nothing",
        b.build(),
        expect={"clear_areas_m2": [7.0 * 5.0],
                "lines_standing_inside_a_space": 3})


def _d():
    """A doorway interrupts a wall; the faces run on to the jambs."""
    b = Builder()
    _shell(b, 9000, 5000)
    r4._partition_v(b, 4000, 0, 5000, t=200.0, gaps=[(1500, 2400)])
    r4._door(b, "DA", 4000, 1500, 900)
    r4._stamp(b, "S1", ["OFFICE"], 2000, 2500)
    r4._stamp(b, "S2", ["FILE"], 6500, 2500)
    return Case(
        "D_A_DOORWAY_DOES_NOT_SHORTEN_THE_ROOM",
        "a room's face runs the full wall, and the portal closes the hole",
        b.build(),
        expect={"clear_areas_m2": [4.0 * 5.0, 4.8 * 5.0],
                "no_truncation_at_the_opening": True})


def _e():
    """Four walls, four thicknesses, one room."""
    b = Builder()
    # south 100, north 250, west 150, east 300 — built by hand
    r4._wall(b, "H", 0.0, -100.0, 0.0, 6000.0, W)
    r4._wall(b, "H", 4000.0, 4250.0, 0.0, 6000.0, W)
    r4._wall(b, "V", 0.0, -150.0, -100.0, 4250.0, W)
    r4._wall(b, "V", 6000.0, 6300.0, -100.0, 4250.0, W)
    r4._stamp(b, "S1", ["HALL"], 3000, 2000)
    return Case(
        "E_FOUR_WALLS_FOUR_THICKNESSES",
        "each side stops at its own wall's inner face, whatever its depth",
        b.build(),
        expect={"clear_areas_m2": [6.0 * 4.0],
                "no_centreline_area": True})


def _f():
    """A column in a room's corner is not the room's boundary."""
    b = Builder()
    _shell(b, 7000, 5000)
    # a 400 x 400 column standing clear of the walls
    r4._run(b, "V", 1200.0, 1200.0, 1600.0, W)
    r4._run(b, "V", 1600.0, 1200.0, 1600.0, W)
    r4._run(b, "H", 1200.0, 1200.0, 1600.0, W)
    r4._run(b, "H", 1600.0, 1200.0, 1600.0, W)
    r4._stamp(b, "S1", ["LOBBY"], 4000, 3000)
    return Case(
        "F_A_COLUMN_STANDING_IN_A_ROOM",
        "a column does not become the face the floor stops at",
        b.build(),
        expect={"clear_bounds_mm": [0.0, 0.0, 7000.0, 5000.0],
                "no_centreline_area": True})


def _g():
    """A finish line 20 mm inside the structural face."""
    b = Builder()
    _shell(b, 6000, 4000)
    r4._run(b, "V", 220.0, 220.0, 3800.0, W)
    r4._run(b, "H", 220.0, 220.0, 5800.0, W)
    r4._stamp(b, "S1", ["STUDY"], 3000, 2000)
    return Case(
        "G_A_FINISH_LINE_INSIDE_THE_STRUCTURAL_FACE",
        "a 20 mm skim is not a wall and does not move the boundary",
        b.build(),
        expect={"measurement_basis": "CLEAR_INTERNAL_FINISH_FACE",
                "lines_standing_inside_a_space": 2})


def _h():
    """One wall, two rooms, different clear widths."""
    b = Builder()
    _shell(b, 10000, 4000)
    r4._partition_v(b, 3000, 0, 4000, t=200.0, gaps=[(1500, 2400)])
    r4._door(b, "DA", 3000, 1500, 900)
    r4._stamp(b, "S1", ["NARROW"], 1500, 2000)
    r4._stamp(b, "S2", ["WIDE"], 6500, 2000)
    return Case(
        "H_ONE_WALL_TWO_DIFFERENT_CLEAR_WIDTHS",
        "the two rooms measure different widths from the same wall",
        b.build(),
        expect={"clear_areas_m2": [3.0 * 4.0, 6.8 * 4.0],
                "opposite_faces_of_one_wall": True})


def _i():
    """Ground outside the envelope, with no site boundary anywhere."""
    b = Builder()
    _shell(b, 8000, 5000)
    r4._partition_v(b, 3500, 0, 5000, t=200.0, gaps=[(1500, 2400)])
    r4._door(b, "DA", 3500, 1500, 900)
    r4._stamp(b, "S1", ["BEDROOM"], 1800, 2500)
    r4._stamp(b, "S2", ["MAJLIS"], 6000, 2500)
    # a paved strip OUTSIDE the building, bounded on three sides only —
    # there is no site ring, so how far the ground goes is unknown
    r4._run(b, "H", -1400.0, 0.0, 8000.0, W)
    r4._run(b, "V", 0.0, -1400.0, -200.0, W)
    r4._run(b, "V", 8000.0, -1400.0, -200.0, W)
    r4._stamp(b, "S3", ["GARDEN"], 4000, -800)
    return Case(
        "I_OUTSIDE_THE_ENVELOPE_WITH_NO_SITE_RING",
        "no site boundary does not make outside-the-building interior",
        b.build(),
        expect={"site_extent": "SITE_EXTENT_UNKNOWN",
                "nothing_outside_is_interior": True,
                "no_invented_site": True})


def cases() -> list:
    return [_a(), _b(), _c(), _d(), _e(), _f(), _g(), _h(), _i()]


def freeze_hash() -> str:
    parts = []
    for c in cases():
        parts.append(f"{c.name}|{c.what_it_tests}|{sorted(c.expect)}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
