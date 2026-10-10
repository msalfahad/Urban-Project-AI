"""Round 6B — twelve drawings about one drawn line.

Round 6A set aside every line with floor on both sides of it. That is
right about a worktop and wrong about a 100 mm block wall drawn once, and
these twelve cases are the difference:

    A  one partition line between two established walls
    B  a single line terminating at a T junction
    C  a worktop that looks exactly like a partition
    D  a dimension line crossing a room
    E  a single partition with a door in it
    F  a single line continuing a known 200 mm wall
    G  an isolated decorative line
    H  topology established, thickness unknown
    I  topology AND clear face established, by continuation
    J  the same geometry with the evidence removed
    K  a topology-only partition creates ZERO material
    L  two rooms separated, and neither allowed blockwork

Cases C, D, G and J exist to be REFUSED. A round that only tested the
lines it wanted to accept would accept everything.
"""

from __future__ import annotations

import hashlib
import math
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
        r4._door(b, "DENT", w / 2 - 450, 0, 900, rotation=math.pi / 2)


def _line(b, axis, fixed, lo, hi, layer=W):
    r4._run(b, axis, fixed, lo, hi, layer)


# ------------------------------------------------------------------- cases

def _a():
    """One line, wall to wall, a named room on each side of it."""
    b = Builder()
    _shell(b, 9000, 5000)
    _line(b, "V", 4500.0, 0.0, 5000.0)
    r4._stamp(b, "S1", ["BEDROOM"], 2200, 2500)
    r4._stamp(b, "S2", ["STORE"], 6800, 2500)
    return Case(
        "A_ONE_PARTITION_LINE_BETWEEN_TWO_WALLS",
        "a named room on each side of a wall-to-wall line is a partition",
        b.build(),
        expect={"topology_established_at_least": 1,
                "two_spaces_at_least": 2,
                "material_length_m": 0.0})


def _b():
    """A single line meeting an established partition at a T."""
    b = Builder()
    _shell(b, 10000, 6000)
    r4._partition_v(b, 5000, 0, 6000, t=200.0, gaps=[(2000, 2900)])
    r4._door(b, "DA", 5000, 2000, 900)
    _line(b, "H", 3000.0, 5200.0, 10000.0)
    r4._stamp(b, "S1", ["MAJLIS"], 2500, 3000)
    r4._stamp(b, "S2", ["BED ONE"], 7500, 1500)
    r4._stamp(b, "S3", ["BED TWO"], 7500, 4500)
    return Case(
        "B_A_SINGLE_LINE_AT_A_T_JUNCTION",
        "a line landing on an established wall, with a room each side",
        b.build(),
        expect={"topology_established_at_least": 1,
                "two_spaces_at_least": 3,
                "material_length_m": 0.0})


def _c():
    """A worktop: wall to wall, and nothing named behind it."""
    b = Builder()
    _shell(b, 7000, 5000)
    _line(b, "V", 600.0, 0.0, 5000.0)
    r4._stamp(b, "S1", ["KITCHEN"], 3800, 2500)
    return Case(
        "C_A_WORKTOP_THAT_LOOKS_LIKE_A_PARTITION",
        "spanning the room is what a fitting does. It is not a partition",
        b.build(),
        expect={"topology_established_exactly": 0,
                "clear_areas_m2": [7.0 * 5.0],
                "material_length_m": 0.0})


def _d():
    """A dimension line laid across a room on its own layer."""
    b = Builder()
    _shell(b, 6000, 4000)
    _line(b, "H", 2000.0, 0.0, 6000.0, layer="DIM")
    r4._stamp(b, "S1", ["SALOON"], 3000, 1000)
    return Case(
        "D_A_DIMENSION_LINE_CROSSING_A_ROOM",
        "a dimension divides the drawing and separates nothing",
        b.build(),
        expect={"topology_established_exactly": 0,
                "clear_areas_m2": [6.0 * 4.0],
                "material_length_m": 0.0})


def _e():
    """A single partition with a door through it."""
    b = Builder()
    _shell(b, 9000, 5000)
    _line(b, "V", 4500.0, 0.0, 1800.0)
    _line(b, "V", 4500.0, 2700.0, 5000.0)
    r4._door(b, "DA", 4500, 1800, 900)
    r4._stamp(b, "S1", ["OFFICE"], 2200, 2500)
    r4._stamp(b, "S2", ["FILE"], 6800, 2500)
    return Case(
        "E_A_SINGLE_PARTITION_WITH_A_DOOR",
        "a door through a line is the architect calling it a wall",
        b.build(),
        expect={"topology_established_at_least": 1,
                "two_spaces_at_least": 2,
                "material_length_m": 0.0})


def _f():
    """A single line continuing an established 200 mm wall."""
    b = Builder()
    _shell(b, 11000, 5000)
    # a real two-face wall for the lower half
    r4._wall(b, "V", 5000.0, 5200.0, 0.0, 2000.0, W)
    # and ONE line continuing its inner face for the rest
    _line(b, "V", 5000.0, 2000.0, 5000.0)
    r4._stamp(b, "S1", ["DINING"], 2500, 2500)
    r4._stamp(b, "S2", ["LIVING"], 8000, 2500)
    return Case(
        "F_A_SINGLE_LINE_CONTINUING_A_200_WALL",
        "the face position comes from the band it continues, not itself",
        b.build(),
        expect={"topology_established_at_least": 1,
                "clear_face_established_at_least": 1,
                "material_length_m": 0.0})


def _g():
    """An isolated decorative line in the middle of a room."""
    b = Builder()
    _shell(b, 8000, 5000)
    _line(b, "H", 2500.0, 2000.0, 5000.0)
    r4._stamp(b, "S1", ["LOBBY"], 4000, 3800)
    return Case(
        "G_AN_ISOLATED_DECORATIVE_LINE",
        "a line touching nothing, with nothing named behind it",
        b.build(),
        expect={"topology_established_exactly": 0,
                "clear_areas_m2": [8.0 * 5.0],
                "material_length_m": 0.0})


def _h():
    """Topology established, thickness unknown: the area may NOT release."""
    b = Builder()
    _shell(b, 9000, 5000)
    _line(b, "V", 4500.0, 0.0, 5000.0)
    r4._stamp(b, "S1", ["BEDROOM"], 2200, 2500)
    r4._stamp(b, "S2", ["STORE"], 6800, 2500)
    return Case(
        "H_TOPOLOGY_ESTABLISHED_THICKNESS_UNKNOWN",
        "two spaces, and no clear floor area for either of them",
        b.build(),
        expect={"topology_established_at_least": 1,
                "spaces_with_clear_face_not_established_at_least": 2,
                "no_clear_area_released_beside_the_partition": True,
                "material_length_m": 0.0})


def _i():
    """Topology AND the clear face, through continuation evidence."""
    b = Builder()
    _shell(b, 11000, 5000)
    r4._wall(b, "V", 5000.0, 5200.0, 0.0, 2000.0, W)
    _line(b, "V", 5000.0, 2000.0, 5000.0)
    r4._stamp(b, "S1", ["DINING"], 2500, 3500)
    r4._stamp(b, "S2", ["LIVING"], 8000, 3500)
    return Case(
        "I_CLEAR_FACE_FROM_CONTINUATION",
        "a continued band gives the face a line cannot give itself",
        b.build(),
        expect={"clear_face_established_at_least": 1,
                "material_length_m": 0.0})


def _j():
    """The same geometry as I, with the established band taken away."""
    b = Builder()
    _shell(b, 11000, 5000)
    _line(b, "V", 5000.0, 2000.0, 5000.0)
    r4._stamp(b, "S1", ["DINING"], 2500, 3500)
    return Case(
        "J_THE_SAME_GEOMETRY_WITHOUT_THE_EVIDENCE",
        "remove the band and the continuation evidence goes with it",
        b.build(),
        expect={"clear_face_established_exactly": 0,
                "material_length_m": 0.0})


def _k():
    """A topology-only partition must create no material at all."""
    b = Builder()
    _shell(b, 9000, 5000)
    _line(b, "V", 4500.0, 0.0, 5000.0)
    r4._stamp(b, "S1", ["BEDROOM"], 2200, 2500)
    r4._stamp(b, "S2", ["STORE"], 6800, 2500)
    return Case(
        "K_A_TOPOLOGY_ONLY_PARTITION_MAKES_NO_MATERIAL",
        "zero blockwork, zero plaster, zero paint, zero wall ceramic",
        b.build(),
        expect={"topology_established_at_least": 1,
                "material_length_m": 0.0,
                "every_candidate_material_not_established": True})


def _l():
    """Two rooms separated, and neither of them allowed any blockwork."""
    b = Builder()
    _shell(b, 12000, 6000)
    _line(b, "V", 4000.0, 0.0, 6000.0)
    _line(b, "V", 8000.0, 0.0, 6000.0)
    r4._stamp(b, "S1", ["BED ONE"], 2000, 3000)
    r4._stamp(b, "S2", ["BED TWO"], 6000, 3000)
    r4._stamp(b, "S3", ["BED THREE"], 10000, 3000)
    return Case(
        "L_SEPARATED_ROOMS_WITH_NO_BLOCKWORK_EITHER_SIDE",
        "the partition is real and the wall quantity is still unknown",
        b.build(),
        expect={"topology_established_at_least": 2,
                "two_spaces_at_least": 3,
                "material_length_m": 0.0,
                "every_candidate_material_not_established": True})


def cases() -> list:
    return [_a(), _b(), _c(), _d(), _e(), _f(), _g(), _h(), _i(), _j(),
            _k(), _l()]


def freeze_hash() -> str:
    rows = [f"{c.name}|{c.what_it_tests}|{sorted(c.expect)}"
            for c in cases()]
    return hashlib.sha256("|".join(rows).encode("utf-8")).hexdigest()[:24]
