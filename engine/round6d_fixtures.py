"""Round 6D — eight drawings about a pantry, ten about a stair.

The owner's correction to round 6C is that a PANTRY label does not imply
four walls. An American pantry opens onto the dining, saloon or living
space it serves, and the tiles on its walls are measured on the walls
that are actually there:

    A  a closed pantry with four walls
    B  an American pantry open to the dining, with L-shaped host walls
    C  an American pantry with U-shaped host walls
    D  a pantry with an island and no wall at the island
    E  a counter against a physical wall
    F  a counter standing inside an open room
    G  a pantry label sitting in the counter's own geometry
    H  a pantry whose openness the drawing does not settle
    I  the tiled shape, which comes from the units and nothing else

And a stair is not a room floor. Where the stair finish is marble and the
floor around it is porcelain — P7757's rule, not every project's — the
treads, the risers, the landing and the nosing are four quantities and
the floor is a fifth:

    A  a straight single flight
    B  two flights and a landing
    C  a U-shaped stair
    D  an L-shaped stair
    E  a winder, whose treads are wedges
    F  a flight whose tread polygons are unequal
    G  a stair beside a floor that must not count its area twice
    H  a stair with no vertical information at all
    I  a stair whose plan and section disagree
    J  decorative parallel lines that are not treads

Cases F and G of the pantry set, and H, I and J of the stair set, exist
to be REFUSED. No coordinate in this file comes from any real project.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field

from engine import round4_fixtures as r4
from engine.cad_fixtures import Builder

W, D, G, TXT = r4.W, r4.D, r4.G, r4.TXT
TITLE_H = 600.0


@dataclass(frozen=True)
class Case:
    name: str
    what_it_tests: str
    decode: dict = None
    expect: dict = field(default_factory=dict)
    sections: dict = field(default_factory=dict)
    rows: tuple = ()          # a ZONE case: the register rows are its drawing
    labels: tuple = ()


def _shell(b, ox, oy, w, h, *, t=200.0, door=True):
    openings = [("S", ox + w / 2 - 450, ox + w / 2 + 450)] if door else []
    r4._ring(b, ox, oy, ox + w, oy + h, layer=W, t=t, openings=openings)
    if door:
        r4._door(b, f"DR{int(ox)}{int(oy)}", ox + w / 2 - 450, oy, 900,
                 rotation=math.pi / 2)


def _title(b, text, x, y):
    b.text(text, x, y, TITLE_H, TXT)


def _counter(b, axis, face, lo, hi, depth, *, layer=W):
    """A fitting standing ON a wall face: one line, and one return."""
    r4._emit(b, axis, face + depth, lo, hi, layer)
    cross = "V" if axis == "H" else "H"
    f0, f1 = min(face, face + depth), max(face, face + depth)
    r4._emit(b, cross, hi, f0, f1, layer)


def _island(b, x0, y0, x1, y1, layer=W):
    """A free-standing island: four lines touching no wall."""
    r4._emit(b, "H", y0, x0, x1, layer)
    r4._emit(b, "H", y1, x0, x1, layer)
    r4._emit(b, "V", x0, y0, y1, layer)
    r4._emit(b, "V", x1, y0, y1, layer)


def _treads(b, axis, first, count, going, lo, hi, layer=W, goings=None):
    """A run of tread lines. `goings` overrides a constant pitch."""
    pos = first
    out = []
    for i in range(count):
        r4._emit(b, axis, pos, lo, hi, layer)
        out.append(pos)
        pos += (goings[i] if goings and i < len(goings) else going)
    return out


# ------------------------------------------------------- §15 the pantry

def _p_a():
    """A closed pantry: four walls and a door."""
    b = Builder()
    _shell(b, 0, 0, 9000, 6000)
    r4._partition_v(b, 3000, 0, 3000, t=200.0, gaps=[(900, 1800)])
    r4._door(b, "DA", 3000, 900, 900)
    r4._partition_h(b, 3000, 0, 3200, t=200.0)
    r4._stamp(b, "S1", ["PANTRY"], 1500, 1500)
    r4._stamp(b, "S2", ["DINING"], 6000, 4000)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "PA_A_CLOSED_PANTRY_WITH_FOUR_WALLS",
        "four walls and a door make a pantry an ordinary physical space",
        b.build(),
        expect={"pantry_openness": "CLOSED_PANTRY",
                "wall_tile_shape": "CLOSED_ON_FOUR_SIDES",
                "zone_creates_no_wall": True})


def _p_b():
    """An American pantry open to the dining, against two walls."""
    b = Builder()
    _shell(b, 0, 0, 10000, 6000)
    _counter(b, "H", 0.0, 0.0, 3000.0, 600.0)
    _counter(b, "V", 0.0, 0.0, 2500.0, 600.0)
    r4._stamp(b, "S1", ["PANTRY"], 1200, 1200)
    r4._stamp(b, "S2", ["DINING"], 7000, 3000)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "PB_AN_AMERICAN_PANTRY_OPEN_TO_THE_DINING",
        "a pantry open to the space it serves is a zone, not a room",
        b.build(),
        expect={"pantry_openness": "OPEN_AMERICAN_PANTRY",
                "zone_without_a_closed_room": True,
                "open_edge_tiles_nothing": True,
                "tile_length_not_established": True})


def _p_c():
    """An American pantry in a recess of the saloon it serves."""
    b = Builder()
    _shell(b, 0, 0, 11000, 6000)
    # a peninsula that makes the recess and does not close it
    r4._partition_h(b, 3000, 0, 2600, t=200.0)
    r4._stamp(b, "S1", ["PANTRY"], 1300, 4400)
    r4._stamp(b, "S2", ["SALOON"], 7000, 3000)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "PC_AN_AMERICAN_PANTRY_IN_A_RECESS_OF_THE_SALOON",
        "a recess is a zone of the space it opens onto, not a room",
        b.build(),
        expect={"pantry_openness": "OPEN_AMERICAN_PANTRY",
                "open_edge_tiles_nothing": True,
                "tile_length_not_established": True,
                "zone_creates_no_wall": True})


def _p_d():
    """A pantry with an island. The island is not a wall."""
    b = Builder()
    _shell(b, 0, 0, 10000, 7000)
    _counter(b, "H", 0.0, 0.0, 4000.0, 600.0)
    _island(b, 2000, 2500, 4500, 3400)
    r4._stamp(b, "S1", ["PANTRY"], 1500, 1200)
    r4._stamp(b, "S2", ["LIVING"], 7000, 4000)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "PD_A_PANTRY_WITH_AN_ISLAND_AND_NO_WALL_AT_IT",
        "an island stands in a room. It does not divide one",
        b.build(),
        expect={"pantry_openness": "OPEN_AMERICAN_PANTRY",
                "island_is_not_a_wall": True,
                "zone_creates_no_wall": True})


def _p_e():
    """A counter against a wall: the room is measured to the wall."""
    b = Builder()
    _shell(b, 0, 0, 6000, 5000)
    _counter(b, "H", 0.0, 0.0, 3000.0, 600.0)
    r4._stamp(b, "S1", ["KITCHEN"], 3000, 3000)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "PE_A_COUNTER_AGAINST_A_PHYSICAL_WALL",
        "the room a fitting stands in is measured to the wall behind it",
        b.build(),
        expect={"clear_areas_m2": [6.0 * 5.0],
                "counter_creates_no_wall": True,
                "no_release_below_m2": 2.0})


def _p_f():
    """A counter standing inside an open room, against nothing."""
    b = Builder()
    _shell(b, 0, 0, 9000, 6000)
    _island(b, 3000, 2500, 6000, 3100)
    r4._stamp(b, "S1", ["SALOON"], 4500, 4500)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "PF_A_COUNTER_STANDING_INSIDE_AN_OPEN_ROOM",
        "a fitting that stands on nothing still divides nothing",
        b.build(),
        expect={"clear_areas_m2": [9.0 * 6.0],
                "counter_creates_no_wall": True})


def _p_g():
    """The PANTRY label sitting in the counter's own geometry."""
    b = Builder()
    _shell(b, 0, 0, 8000, 6000)
    _counter(b, "H", 0.0, 0.0, 4000.0, 600.0)
    r4._stamp(b, "S1", ["PANTRY"], 2000, 300)
    r4._stamp(b, "S2", ["DINING"], 5500, 3500)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "PG_A_PANTRY_LABEL_INSIDE_THE_COUNTER_GEOMETRY",
        "a label in the units names the room, never the units",
        b.build(),
        expect={"label_never_names_a_fitting_strip": ["PANTRY"],
                "counter_creates_no_wall": True})


def _p_h():
    """A pantry with a side no wall accounts for, and nothing named beyond.

    Built as register rows: in a real decode a pantry is either a closed
    cell or a zone of an open space, and the case the owner asked about —
    OPENNESS THE DRAWING DOES NOT SETTLE — is a statement about the rule
    rather than about any drawing. So the rule is what this tests.
    """
    from shapely.geometry import box

    rows = ({
        "space_id": "PS-Z-001", "region_id": "DR-Z",
        "polygon": box(0, 0, 3000, 4000), "area_m2": 12.0,
        "basis": "CLEAR_INTERNAL_FINISH_FACE", "label_raw": "PANTRY",
        "principal_dims_mm": [3000.0, 4000.0], "blockers": [],
        "release_status": "RELEASE_ELIGIBLE_GEOMETRY",
        "identity_authority": "IDENTITY_ESTABLISHED",
        "geometry_authority": "MEASUREMENT_COMPLETE",
        "normalized_identity": "STORE", "wall_band_ids": [],
        "face_contacts": [], "cad_provenance": [],
        "boundary_faces": [
            {"axis": "V", "fixed_mm": 0.0, "length_mm": 4000.0,
             "basis": "CLEAR_INTERNAL_FINISH_FACE",
             "wall_band_id": "PW-Z-V-0.0-200.0", "face_id": "F1"},
            {"axis": "H", "fixed_mm": 0.0, "length_mm": 3000.0,
             "basis": "CLEAR_INTERNAL_FINISH_FACE",
             "wall_band_id": "PW-Z-H-0.0-200.0", "face_id": "F2"},
            {"axis": "H", "fixed_mm": 4000.0, "length_mm": 3000.0,
             "basis": "CLEAR_INTERNAL_FINISH_FACE",
             "wall_band_id": "PW-Z-H-4000.0-200.0", "face_id": "F3"},
            {"axis": "V", "fixed_mm": 3000.0, "length_mm": 4000.0,
             "basis": "CLEAR_INTERNAL_FINISH_FACE",
             "wall_band_id": "", "face_id": "F4"},
        ],
    },)
    return Case(
        "PH_A_PANTRY_WHOSE_OPENNESS_IS_UNKNOWN",
        "open to what, nobody says. That is UNKNOWN, not American",
        None,
        expect={"pantry_openness_in": ["PANTRY_OPENNESS_UNKNOWN"],
                "owner_rule_request_present": True,
                "tile_length_not_established": True},
        rows=rows, labels=(("PANTRY", 1500.0, 2000.0),))


def _p_i():
    """The tiled shapes, stated exactly: one wall, an L and a U.

    Also register rows. Which stretch of an open space's perimeter is
    the pantry's is a question the UNITS answer, so this case gives the
    units and checks the shape that follows from them.
    """
    from shapely.geometry import box

    rows = ({
        "space_id": "PS-Y-001", "region_id": "DR-Y",
        "polygon": box(0, 0, 6000, 5000), "area_m2": 30.0,
        "basis": "CLEAR_INTERNAL_FINISH_FACE",
        "label_raw": "PANTRY | DINING",
        "principal_dims_mm": [6000.0, 5000.0], "blockers": [],
        "release_status": "RELEASE_ELIGIBLE_GEOMETRY",
        "identity_authority": "IDENTITY_ESTABLISHED",
        "geometry_authority": "MEASUREMENT_COMPLETE",
        "normalized_identity": "STORE", "wall_band_ids": [],
        "face_contacts": [], "cad_provenance": [],
        "boundary_faces": [
            {"axis": "H", "fixed_mm": 0.0, "length_mm": 6000.0,
             "basis": "CLEAR_INTERNAL_FINISH_FACE",
             "wall_band_id": "PW-Y-H-0.0-200.0", "face_id": "F1"},
            {"axis": "V", "fixed_mm": 0.0, "length_mm": 5000.0,
             "basis": "CLEAR_INTERNAL_FINISH_FACE",
             "wall_band_id": "PW-Y-V-0.0-200.0", "face_id": "F2"},
        ],
    },)
    return Case(
        "PI_THE_TILED_SHAPE_COMES_FROM_THE_UNITS",
        "one run of units is one wall; two are an L; three are a U",
        None,
        expect={"pantry_openness": "OPEN_AMERICAN_PANTRY",
                "wall_tile_shape": "L_SHAPE",
                "wall_tile_length_m": 3.0 + 2.5,
                "host_walls_at_least": 2},
        rows=rows,
        labels=(("PANTRY", 1000.0, 1000.0), ("DINING", 4500.0, 3500.0)))


# -------------------------------------------------------- §16 the stair

def _s_a():
    """A straight single flight in its own cell."""
    b = Builder()
    _shell(b, 0, 0, 9000, 6000)
    r4._partition_v(b, 3000, 0, 6000, t=200.0, gaps=[(5000, 5900)])
    r4._door(b, "DA", 3000, 5000, 900)
    _treads(b, "H", 300.0, 9, 300.0, 0.0, 3000.0)
    r4._stamp(b, "S1", ["STAIR"], 1500, 1400)
    r4._stamp(b, "S2", ["LOBBY"], 6000, 3000)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "SA_A_STRAIGHT_SINGLE_FLIGHT",
        "nine tread lines are eight treads, each measured from its own",
        b.build(),
        expect={"assemblies": 1, "flights": 1, "treads": 8,
                "tread_m2": 8 * 3.0 * 0.3,
                "riser_quantity_not_established": True,
                "configuration": "STRAIGHT"})


def _s_b():
    """Two flights with a landing between them."""
    b = Builder()
    _shell(b, 0, 0, 10000, 8000)
    r4._partition_v(b, 3600, 0, 8000, t=200.0, gaps=[(6800, 7700)])
    r4._door(b, "DA", 3600, 6800, 900)
    _treads(b, "H", 300.0, 7, 300.0, 0.0, 1700.0)
    _treads(b, "H", 300.0, 7, 300.0, 1900.0, 3600.0)
    r4._stamp(b, "S1", ["STAIR"], 800, 1200)
    r4._stamp(b, "S2", ["HALL"], 7000, 4000)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "SB_TWO_FLIGHTS_AND_A_LANDING",
        "two flights in one cell are one staircase with a landing",
        b.build(),
        expect={"assemblies": 1, "flights_at_least": 2,
                # the 200 mm the two flights leave between them, over
                # the 1.8 m they both reach: 0.36 m2 and not one more
                "landing_m2": 0.2 * 1.8,
                "riser_quantity_not_established": True})


def _s_c():
    """A U-shaped stair: two parallel flights, a landing at the top."""
    b = Builder()
    _shell(b, 0, 0, 11000, 9000)
    r4._partition_v(b, 4000, 0, 9000, t=200.0, gaps=[(7800, 8700)])
    r4._door(b, "DA", 4000, 7800, 900)
    _treads(b, "H", 300.0, 8, 300.0, 0.0, 1800.0)
    _treads(b, "H", 300.0, 8, 300.0, 2200.0, 4000.0)
    r4._stamp(b, "S1", ["STAIR"], 900, 1500)
    r4._stamp(b, "S2", ["LOBBY"], 7500, 4500)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "SC_A_U_SHAPED_STAIR",
        "two flights side by side, and the landing they turn on",
        b.build(),
        expect={"assemblies": 1, "flights_at_least": 2,
                "configuration_in": ["U_SHAPED", "L_SHAPED"],
                "riser_quantity_not_established": True})


def _s_d():
    """An L-shaped stair: flights at right angles."""
    b = Builder()
    _shell(b, 0, 0, 11000, 9000)
    r4._partition_v(b, 4600, 0, 9000, t=200.0, gaps=[(7800, 8700)])
    r4._door(b, "DA", 4600, 7800, 900)
    _treads(b, "H", 300.0, 6, 300.0, 0.0, 1800.0)
    _treads(b, "V", 2400.0, 6, 300.0, 2200.0, 4600.0)
    r4._stamp(b, "S1", ["STAIR"], 900, 1200)
    r4._stamp(b, "S2", ["HALL"], 8000, 4500)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "SD_AN_L_SHAPED_STAIR",
        "flights on two axes are one stair that turns",
        b.build(),
        expect={"assemblies": 1, "flights_at_least": 2,
                "configuration_in": ["L_SHAPED"],
                "riser_quantity_not_established": True})


def _s_e():
    """A winder: the treads are wedges of different sizes."""
    b = Builder()
    _shell(b, 0, 0, 9000, 7000)
    r4._partition_v(b, 3400, 0, 7000, t=200.0, gaps=[(5800, 6700)])
    r4._door(b, "DA", 3400, 5800, 900)
    # each tread reaches a different distance, and the goings differ
    widths = (3400.0, 3100.0, 2800.0, 2500.0, 2200.0, 1900.0)
    pos = 300.0
    for i, w in enumerate(widths):
        r4._emit(b, "H", pos, 0.0, w, W)
        pos += 250.0 + i * 20.0
    r4._stamp(b, "S1", ["STAIR"], 700, 500)
    r4._stamp(b, "S2", ["LOBBY"], 6000, 3500)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "SE_A_WINDER_WHOSE_TREADS_ARE_WEDGES",
        "no constant width times a constant going times a count",
        b.build(),
        expect={"assemblies": 1, "configuration_in": ["WINDER"],
                "tread_areas_differ": True,
                "riser_quantity_not_established": True})


def _s_f():
    """A flight whose tread polygons are unequal."""
    b = Builder()
    _shell(b, 0, 0, 9000, 6000)
    r4._partition_v(b, 3200, 0, 6000, t=200.0, gaps=[(4800, 5700)])
    r4._door(b, "DA", 3200, 4800, 900)
    for pos, w in ((300.0, 3200.0), (600.0, 3200.0), (900.0, 2900.0),
                   (1200.0, 2900.0), (1500.0, 3200.0)):
        r4._emit(b, "H", pos, 0.0, w, W)
    r4._stamp(b, "S1", ["STAIR"], 700, 800)
    r4._stamp(b, "S2", ["HALL"], 6000, 3000)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "SF_UNEQUAL_TREAD_POLYGONS",
        "the total is the sum of the actual shapes, not count x one shape",
        b.build(),
        expect={"assemblies": 1, "tread_areas_differ": True,
                "tread_m2_is_the_sum": True,
                "riser_quantity_not_established": True})


def _s_g():
    """A stair beside a floor whose finish must not count it twice."""
    b = Builder()
    _shell(b, 0, 0, 10000, 6000)
    r4._partition_v(b, 3000, 0, 6000, t=200.0, gaps=[(4800, 5700)])
    r4._door(b, "DA", 3000, 4800, 900)
    _treads(b, "H", 300.0, 8, 300.0, 0.0, 3000.0)
    r4._stamp(b, "S1", ["STAIR"], 1500, 1200)
    r4._stamp(b, "S2", ["SALOON"], 6500, 3000)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "SG_A_STAIR_BESIDE_A_FLOOR",
        "marble on the stair means no porcelain on the same square metre",
        b.build(),
        expect={"assemblies": 1,
                "no_released_room_overlaps_a_stair": True,
                "riser_quantity_not_established": True})


def _s_h():
    """A stair with no vertical information anywhere."""
    b = Builder()
    _shell(b, 0, 0, 8000, 6000)
    r4._partition_v(b, 2800, 0, 6000, t=200.0, gaps=[(4800, 5700)])
    r4._door(b, "DA", 2800, 4800, 900)
    _treads(b, "H", 300.0, 7, 300.0, 0.0, 2800.0)
    r4._stamp(b, "S1", ["STAIR"], 1400, 1000)
    r4._stamp(b, "S2", ["LOBBY"], 5500, 3000)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "SH_A_STAIR_WITH_NO_VERTICAL_INFORMATION",
        "no riser height, no riser quantity, and no assumed rise",
        b.build(),
        expect={"assemblies": 1, "riser_quantity_not_established": True,
                "riser_m2_is_none": True})


def _s_i():
    """A stair whose section says a different number of treads."""
    b = Builder()
    _shell(b, 0, 0, 9000, 6000)
    r4._partition_v(b, 3000, 0, 6000, t=200.0, gaps=[(4800, 5700)])
    r4._door(b, "DA", 3000, 4800, 900)
    _treads(b, "H", 300.0, 7, 300.0, 0.0, 3000.0)
    r4._stamp(b, "S1", ["STAIR"], 1500, 1000)
    r4._stamp(b, "S2", ["HALL"], 6000, 3000)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "SI_PLAN_AND_SECTION_DISAGREE",
        "a disagreement is reported, never averaged and never picked",
        b.build(),
        expect={"assemblies": 1,
                "exception_present": "PLAN_AND_SECTION_DISAGREE"},
        sections={"DR-001": {"treads": 11, "risers": 12,
                             "riser_height_mm": 170.0}})


def _s_j():
    """Decorative parallel lines that are not treads."""
    b = Builder()
    _shell(b, 0, 0, 9000, 6000)
    # a hatched band out on the sheet, enclosed by nothing and named
    # nothing
    _treads(b, "H", -2000.0, 8, 300.0, 11000.0, 14000.0)
    r4._stamp(b, "S1", ["SALOON"], 4500, 3000)
    _title(b, "GROUND FLOOR PLAN", 500, -500)
    return Case(
        "SJ_DECORATIVE_PARALLEL_LINES",
        "parallel lines are a stair only where something says so",
        b.build(),
        expect={"assemblies": 0, "runs_refused_at_least": 1})


def pantry_cases() -> list:
    return [_p_a(), _p_b(), _p_c(), _p_d(), _p_e(), _p_f(), _p_g(),
            _p_h(), _p_i()]


def stair_cases() -> list:
    return [_s_a(), _s_b(), _s_c(), _s_d(), _s_e(), _s_f(), _s_g(),
            _s_h(), _s_i(), _s_j()]


def cases() -> list:
    return pantry_cases() + stair_cases()


def freeze_hash() -> str:
    rows = [f"{c.name}|{c.what_it_tests}|{sorted(c.expect)}"
            for c in cases()]
    return hashlib.sha256("|".join(rows).encode("utf-8")).hexdigest()[:24]
