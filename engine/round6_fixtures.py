"""Eighteen drawings for round 6. Most of them say what must NOT happen.

Round 5's four releases were wrong, and the benchmark said so. The root
cause was not the four numbers: 845 drawn lines became 3,272 "wall bands"
because every parallel pair inside 50-600 mm was called a wall, and the
phantom partitions that followed sliced the floor. So the cases here are
mostly about restraint:

    a line may serve two walls only where they occupy DISJOINT stretches
    a detail line beside a wall is not a second wall
    nobody naming a space is not evidence that it is a void
    a room with no door on any boundary is suspicious, not a room

and a few about the thing round 6 is for:

    a legitimate recess belongs to the floor it is part of
    an open plan is one floor zone; walls still split one

EVERY CASE DECLARES ITS STAGE. The geometry cases are asserted from step 4
onward. The trade cases are recorded now and asserted when the trade layer
lands, and until then they are reported as NOT YET IMPLEMENTED rather than
quietly passing.

NOTHING HERE ENCODES A P7757 NUMBER. No 9.675, no 3.375, no coordinate and
no thickness taken from that drawing.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field

from engine import round4_fixtures as r4
from engine import round5_fixtures as r5
from engine.cad_fixtures import Builder

WALL_T = r4.WALL_T
W, D, G, TXT = r4.W, r4.D, r4.G, r4.TXT

GEOMETRY = "GEOMETRY_STAGE"      # asserted now (steps 3-5)
TRADE = "TRADE_STAGE"            # recorded now, asserted at steps 6-12


@dataclass(frozen=True)
class Case:
    name: str
    what_it_tests: str
    decode: dict
    stage: str
    expect: dict = field(default_factory=dict)
    expect_trade: dict = field(default_factory=dict)


def _shell(b, w, h, *, door=True, layer=W):
    """A closed building with one entrance, so openings evidence exists."""
    openings = [("S", w / 2 - 450, w / 2 + 450)] if door else []
    r4._ring(b, 0, 0, w, h, layer=layer, openings=openings)
    if door:
        r4._door(b, "DENT", w / 2 - 450, 0, 900, rotation=math.pi / 2)


# ------------------------------------------------------------------- cases

def _a():
    """A kitchen whose entrance recess is outside its main rectangle."""
    b = Builder()
    _shell(b, 12000, 7000)
    # main kitchen 3.0 x 2.7 with a 1.05 x 1.5 recess on its east side
    r4._partition_v(b, 3000, 0, 2700)
    r4._partition_h(b, 2700, 0, 3200, gaps=[(1000, 2050)])
    r4._partition_v(b, 3200, 2700, 4200)
    r4._partition_h(b, 4200, 3200, 4250)
    r4._partition_v(b, 4250, 2700, 4200)
    r4._stamp(b, "S1", ["KITCHEN"], 1500, 1300)
    r4._stamp(b, "S2", ["HALL"], 8000, 4000)
    return Case("A_KITCHEN_WITH_AN_ENTRANCE_RECESS",
                "a recess outside the main rectangle still belongs to it",
                b.build(), GEOMETRY,
                expect={"no_phantom_partition_inside_a_room": True,
                        "min_interior_spaces": 2},
                expect_trade={"one_floor_zone_covering": ["KITCHEN"],
                              "zone_includes_the_recess": True})


def _b():
    """An L-shaped room. One face, one area, no phantom cut across it."""
    b = Builder()
    _shell(b, 14000, 9000)
    r4._partition_v(b, 5000, 0, 5000)
    r4._partition_h(b, 5000, 0, 5200)
    r4._stamp(b, "S1", ["SALOON"], 2000, 6500)
    r4._stamp(b, "S2", ["STORE"], 2000, 2000)
    return Case("B_L_SHAPED_ROOM",
                "an L is one space, not two rectangles",
                b.build(), GEOMETRY,
                expect={"no_phantom_partition_inside_a_room": True,
                        "an_l_shaped_face_exists": True})


def _c():
    b = Builder()
    _shell(b, 14000, 8000)
    r4._stamp(b, "S1", ["SALOON"], 3000, 4000)
    r4._stamp(b, "S2", ["DINING"], 7000, 4000)
    r4._stamp(b, "S3", ["RECEPTION"], 11000, 4000)
    return Case("C_OPEN_SALON_DINING_RECEPTION",
                "three labels, no walls, one physical space",
                b.build(), GEOMETRY,
                expect={"max_interior_spaces": 1, "functional_zones": 3,
                        "no_phantom_partition_inside_a_room": True},
                expect_trade={"one_floor_zone_covering":
                              ["SALOON", "DINING", "RECEPTION"]})


def _d():
    b = Builder()
    _shell(b, 14000, 8000)
    r4._partition_v(b, 4500, 0, 8000, gaps=[(3000, 3900)])
    r4._door(b, "D1", 4500, 3000, 900)
    r4._partition_v(b, 9300, 0, 8000, gaps=[(3000, 3900)])
    r4._door(b, "D2", 9300, 3000, 900)
    r4._stamp(b, "S1", ["SALOON"], 2200, 5500)
    r4._stamp(b, "S2", ["DINING"], 7000, 5500)
    r4._stamp(b, "S3", ["RECEPTION"], 11800, 5500)
    return Case("D_THE_SAME_LABELS_WITH_REAL_WALLS",
                "walls still split what labels never could",
                b.build(), GEOMETRY,
                expect={"min_interior_spaces": 3,
                        "no_phantom_partition_inside_a_room": True},
                expect_trade={"separate_floor_zones": 3})


def _e():
    b = Builder()
    _shell(b, 12000, 7000)
    r4._partition_v(b, 3000, 0, 7000, gaps=[(2500, 3400)])
    r4._door(b, "D1", 3000, 2500, 900)
    r4._stamp(b, "S1", ["BATHROOM"], 1500, 4000)
    r4._stamp(b, "S2", ["HALL"], 7500, 4000)
    return Case("E_WET_ROOM_BESIDE_AN_OPEN_HALL",
                "a door does not make a bathroom part of the hall",
                b.build(), GEOMETRY,
                expect={"min_interior_spaces": 2,
                        "no_phantom_partition_inside_a_room": True},
                expect_trade={"separate_floor_zones": 2})


def _f():
    """A strip between the plot wall and the building. Not interior."""
    b = Builder()
    r4._ring(b, 0, 0, 24000, 16000, layer="PLOT")
    r4._ring(b, 4000, 4000, 20000, 12000,
             openings=[("S", 11500, 12400)])
    r4._door(b, "DENT", 11500, 4000, 900, rotation=math.pi / 2)
    r4._stamp(b, "S1", ["SALOON"], 12000, 8000)
    r4._stamp(b, "S2", ["GARDEN"], 12000, 2000)
    return Case("F_AN_EXTERIOR_STRIP_INSIDE_THE_SITE",
                "outside the building is not interior floor",
                b.build(), GEOMETRY,
                expect={"an_exterior_space_is_identified": True,
                        "no_exterior_space_called_interior": True},
                expect_trade={"no_floor_zone_on_exterior": True})


def _g():
    b = Builder()
    _shell(b, 12000, 7000)
    r4._partition_v(b, 4000, 0, 7000, gaps=[(2500, 3400)])
    r4._door(b, "D1", 4000, 2500, 900)
    r4._stamp(b, "S2", ["HALL"], 8000, 3500)
    return Case("G_AN_INTERIOR_ROOM_NOBODY_NAMED",
                "UNKNOWN is not VOID",
                b.build(), GEOMETRY,
                expect={"unnamed_interior_space_role":
                        "INTERIOR_SPACE_UNCLASSIFIED",
                        "nothing_called_void_without_evidence": True})


def _h():
    """A labelled shaft, enclosed, no door, repeated on a second plan."""
    b = Builder()
    for dx in (0.0, 60000.0):
        r4._ring(b, dx, 0, dx + 12000, 7000,
                 openings=[("S", dx + 5500, dx + 6400)])
        r4._door(b, f"DE{int(dx)}", dx + 5500, 0, 900, rotation=math.pi / 2)
        r4._ring(b, dx + 1000, 1000, dx + 2600, 2600)
        r4._stamp(b, f"SH{int(dx)}", ["SHAFT"], dx + 1800, 1800)
        r4._stamp(b, f"HL{int(dx)}", ["HALL"], dx + 7000, 4000)
    return Case("H_A_SHAFT_WITH_EVIDENCE",
                "a shaft is a claim, and here the claim is supported",
                b.build(), GEOMETRY,
                expect={"a_shaft_is_identified": True,
                        "nothing_called_void_without_evidence": True})


def _i():
    """The same geometry with no label at all: enclosed, no door, repeated."""
    b = Builder()
    for dx in (0.0, 60000.0):
        r4._ring(b, dx, 0, dx + 12000, 7000,
                 openings=[("S", dx + 5500, dx + 6400)])
        r4._door(b, f"DE{int(dx)}", dx + 5500, 0, 900, rotation=math.pi / 2)
        r4._ring(b, dx + 1000, 1000, dx + 2600, 2600)
        r4._stamp(b, f"HL{int(dx)}", ["HALL"], dx + 7000, 4000)
    return Case("I_AN_UNLABELLED_VERTICAL_PENETRATION",
                "enclosed, no door, repeated across plans — evidence, not a "
                "guess",
                b.build(), GEOMETRY,
                expect={"a_vertical_penetration_is_identified": True,
                        "nothing_called_void_without_evidence": True})


def _j():
    b = Builder()
    _shell(b, 14000, 9000)
    r4._ring(b, 9000, 5000, 13000, 8000)          # a stair enclosure
    r4._stamp(b, "S1", ["HALL"], 4000, 4000)
    r4._stamp(b, "S2", ["STAIR"], 11000, 6500)
    return Case("J_A_STAIR_INSIDE_AN_OPEN_HALL",
                "the stair is its own space and not part of the hall floor",
                b.build(), GEOMETRY,
                expect={"min_interior_spaces": 1,
                        "no_phantom_partition_inside_a_room": True},
                expect_trade={"stair_excluded_from_the_hall_zone": True})


def _k():
    b = Builder()
    _shell(b, 12000, 7000)
    r4._stamp(b, "S1", ["KITCHEN"], 3000, 3500)
    r4._stamp(b, "S2", ["DINING AREA"], 8000, 3500)
    return Case("K_TWO_ZONES_ONE_FINISH",
                "two zones sharing one floor are one measurement",
                b.build(), TRADE,
                expect_trade={"one_floor_zone_covering":
                              ["KITCHEN", "DINING AREA"]})


def _l():
    b = Builder()
    _shell(b, 14000, 7000)
    r4._partition_v(b, 6000, 0, 7000, gaps=[(2500, 3400)])
    r4._door(b, "D1", 6000, 2500, 900)
    r4._stamp(b, "S1", ["SALOON"], 3000, 4500)
    r4._stamp(b, "S2", ["BATHROOM"], 10000, 4500)
    return Case("L_TWO_SPACES_DIFFERENT_FINISHES",
                "a declared finish change splits a floor measurement",
                b.build(), TRADE,
                expect_trade={"separate_floor_zones": 2})


def _m():
    b = Builder()
    _shell(b, 12000, 7000)
    r4._partition_v(b, 4000, 0, 7000, gaps=[(2500, 3400)])
    r4._door(b, "D1", 4000, 2500, 900)
    r4._stamp(b, "S1", ["Q™ZX¢"], 2000, 3500)   # undecodable
    r4._stamp(b, "S2", ["HALL"], 8000, 3500)
    return Case("M_VALID_GEOMETRY_UNREADABLE_IDENTITY",
                "an unreadable name costs the identity, not the geometry",
                b.build(), GEOMETRY,
                expect={"min_interior_spaces": 2,
                        "unnamed_interior_space_role":
                            "INTERIOR_SPACE_UNCLASSIFIED",
                        "nothing_called_void_without_evidence": True})


def _n():
    """A detail line 50 mm inside a wall face, not reaching the corners."""
    b = Builder()
    _shell(b, 12000, 7000)
    b.line(300.0, 50.0, 11700.0, 50.0, W)
    r4._stamp(b, "S1", ["SALOON"], 6000, 3500)
    return Case("N_A_DETAIL_LINE_BESIDE_A_WALL_FACE",
                "a line beside a wall is not a second wall",
                b.build(), GEOMETRY,
                expect={"wall_bands_at_most": 8,
                        "no_phantom_partition_inside_a_room": True,
                        "no_line_serves_overlapping_walls": True})


def _o():
    """One long line offered three partners: two disjoint, one overlapping."""
    b = Builder()
    _shell(b, 16000, 10000)
    b.line(6000.0, 0.0, 6000.0, 10000.0, W)        # the shared line
    b.line(6200.0, 0.0, 6200.0, 4000.0, W)         # partner 1, lower half
    b.line(6400.0, 6000.0, 6400.0, 10000.0, W)     # partner 2, upper half
    b.line(6550.0, 0.0, 6550.0, 4000.0, W)         # competes with partner 1
    r4._stamp(b, "S1", ["SALOON"], 3000, 5000)
    r4._stamp(b, "S2", ["MAJLIS"], 11000, 5000)
    return Case("O_ONE_LINE_OFFERED_THREE_PARTNERS",
                "a line serves two walls only over disjoint stretches",
                b.build(), GEOMETRY,
                expect={"no_line_serves_overlapping_walls": True,
                        "shared_line_wall_count": 2})


def _p():
    """A closed region with no opening anywhere on its boundary."""
    b = Builder()
    _shell(b, 12000, 8000)
    r4._ring(b, 7000, 4000, 10500, 7000)
    r4._stamp(b, "S1", ["SALOON"], 3000, 4000)
    r4._stamp(b, "S2", ["STORE"], 8750, 5500)
    return Case("P_A_ROOM_WITH_NO_DOOR_ANYWHERE",
                "a room with no way in is reported, not released",
                b.build(), GEOMETRY,
                expect={"a_space_with_no_opening_is_flagged": True})


def _q():
    b = Builder()
    _shell(b, 10000, 6000)
    r4._stamp(b, "S1", ["SALOON"], 5000, 3000)
    return Case("Q_NO_WASTE_FACTOR_SUPPLIED",
                "an unsupplied waste factor is not a default",
                b.build(), TRADE,
                expect_trade={"procurement_quantity": "NOT_ESTABLISHED"})


def _r():
    """Every wall 300 mm. Nothing may assume 200."""
    b = Builder()
    r4._ring(b, 0, 0, 14000, 8000, t=300.0,
             openings=[("S", 6550, 7450)])
    r4._door(b, "DENT", 6550, 0, 900, rotation=math.pi / 2)
    r4._partition_v(b, 5000, 0, 8000, t=300.0, gaps=[(3000, 3900)])
    r4._door(b, "D1", 5000, 3000, 900)
    r4._stamp(b, "S1", ["SALOON"], 2500, 4000)
    r4._stamp(b, "S2", ["MAJLIS"], 9500, 4000)
    return Case("R_A_DRAWING_WHOSE_WALLS_ARE_ALL_300",
                "the thicknesses are read off the drawing, not assumed",
                b.build(), GEOMETRY,
                expect={"min_interior_spaces": 2,
                        "observed_thickness_mode": 300.0,
                        "no_phantom_partition_inside_a_room": True})


_BUILDERS = (_a, _b, _c, _d, _e, _f, _g, _h, _i, _j, _k, _l, _m, _n, _o,
             _p, _q, _r)


def cases() -> list:
    return [fn() for fn in _BUILDERS]


def geometry_cases() -> list:
    return [c for c in cases() if c.stage == GEOMETRY]


def trade_cases() -> list:
    return [c for c in cases() if c.stage == TRADE]


def freeze_hash() -> str:
    rows = []
    for c in cases():
        payload = "|".join(f"{k}={c.expect[k]}" for k in sorted(c.expect))
        trade = "|".join(f"{k}={c.expect_trade[k]}"
                         for k in sorted(c.expect_trade))
        rows.append(f"{c.name}|{c.stage}|{payload}|{trade}|"
                    f"{len(c.decode['OBJECTS'])}")
    return hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")
                          ).hexdigest()[:24]
