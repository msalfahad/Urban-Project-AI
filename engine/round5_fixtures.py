"""Twenty-three drawings about one question: is the wall there or not?

Round 4's fixtures were about openings. These are about the wall BETWEEN
the openings — the one drawn in eleven pieces, or on one face only, or
stopping two millimetres short of the wall it meets.

The cases split cleanly in two, and both halves are load-bearing:

    IT IS THERE      A, B, G, I, J, M, N, W — fragmented, half-drawn or a
                     hair short, and the room topology must come back
    IT IS NOT        C, D, E, F, H, K, Q, R, S, T, U, V — an opening, a
                     termination, an unexplained gap, an open plan, an
                     annotation line. Nothing may be invented

A round that recovered everything would pass the first half and destroy the
second. That is why there are more cases in the second.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from engine import round4_fixtures as r4
from engine.cad_fixtures import Builder

WALL_T = r4.WALL_T
W, D, G, TXT = r4.W, r4.D, r4.G, r4.TXT


@dataclass(frozen=True)
class Case:
    name: str
    what_it_tests: str
    decode: dict
    expect: dict


def _frag_v(b, x, y0, y1, *, t=WALL_T, a_gaps=(), b_gaps=(), layer=W):
    """A vertical wall whose two faces may be broken in different places."""
    r4._run(b, "V", x, y0, y1, layer, a_gaps)
    r4._run(b, "V", x + t, y0, y1, layer, b_gaps)


def _frag_h(b, y, x0, x1, *, t=WALL_T, a_gaps=(), b_gaps=(), layer=W):
    r4._run(b, "H", y, x0, x1, layer, a_gaps)
    r4._run(b, "H", y + t, x0, x1, layer, b_gaps)


def _two_room_shell(b, w=10000.0, h=4000.0):
    r4._ring(b, 0, 0, w, h)
    r4._stamp(b, "S1", ["SALOON"], w * 0.24, h / 2)
    r4._stamp(b, "S2", ["KITCHEN"], w * 0.75, h / 2)


# ------------------------------------------------------------------- cases

def _a():
    b = Builder()
    _two_room_shell(b)
    _frag_v(b, 4900, 0, 4000, b_gaps=[(1200, 2600)])
    return Case("A_ONE_CONTINUOUS_FACE_ONE_FRAGMENTED",
                "one drawn face carries the wall; the other is not invented",
                b.build(),
                {"min_released": 2, "continuity_verdicts": ["ESTABLISHED"],
                 "material_authority_blocked_somewhere": True,
                 "subdivision_needed_recovery": True})


def _b():
    b = Builder()
    _two_room_shell(b)
    # Both faces broken, in different places: between them the wall is
    # covered everywhere, so no span is undrawn on both sides at once.
    _frag_v(b, 4900, 0, 4000, a_gaps=[(600, 1600)], b_gaps=[(2400, 3400)])
    return Case("B_BOTH_FACES_FRAGMENTED_BUT_OVERLAPPING",
                "two broken faces can still describe one continuous wall",
                b.build(),
                {"min_released": 2, "continuity_verdicts": ["ESTABLISHED"],
                 "no_unresolved_gap": True})


def _c():
    b = Builder()
    _two_room_shell(b)
    _frag_v(b, 4900, 0, 4000, a_gaps=[(1200, 2100)], b_gaps=[(1200, 2100)])
    r4._emit(b, "H", 1200, 4900, 5100, W)
    r4._emit(b, "H", 2100, 4900, 5100, W)
    r4._door(b, "D90", 4900, 1200, 900)
    return Case("C_THE_SAME_GAP_WITH_A_VALIDATED_DOOR_IN_IT",
                "a door in the gap is why the gap is empty",
                b.build(),
                {"min_released": 2,
                 "continuity_verdicts": ["OPENING_INTERRUPTION"],
                 "no_material_across_openings": True,
                 "door_candidates": 1})


def _d():
    b = Builder()
    r4._ring(b, 0, 0, 6000, 4000, openings=[("S", 2000, 3200)])
    r4._window(b, "H", 2000, 3200, 0.0, -WALL_T)
    r4._stamp(b, "S1", ["BEDROOM"], 3000, 2000)
    return Case("D_THE_SAME_GAP_WITH_A_WINDOW_IN_IT",
                "a window explains the gap and is not a passage",
                b.build(),
                {"min_released": 1, "window_candidates": 1,
                 "continuity_verdicts": ["OPENING_INTERRUPTION"],
                 "no_material_across_openings": True})


def _e():
    b = Builder()
    r4._ring(b, 0, 0, 12000, 6000)
    # A spur wall that genuinely stops in the middle of the room.
    _frag_v(b, 5900, 0, 2500)
    r4._stamp(b, "S1", ["SALOON"], 6000, 4000)
    return Case("E_A_TRUE_WALL_TERMINATION",
                "a wall that ends is not a wall with a gap in it",
                b.build(),
                {"releases_nothing": False, "no_unsupported_recovery": True,
                 "no_continuation_or_nothing": True})


def _f():
    b = Builder()
    _two_room_shell(b)
    _frag_v(b, 4900, 0, 4000, a_gaps=[(1200, 2600)], b_gaps=[(1200, 2600)])
    return Case("F_AN_UNRESOLVED_COLLINEAR_GAP",
                "collinearity is not evidence. The gap stays a gap",
                b.build(),
                {"releases_nothing": True,
                 "continuity_verdicts": ["UNRESOLVED_GAP"],
                 "no_unsupported_recovery": True,
                 "undersegmentation_outcome": "ROOM_PARTITION_UNRESOLVED"})


def _g():
    b = Builder()
    r4._ring(b, 0, 0, 10000, 6000)
    _frag_v(b, 4900, 0, 5998)          # stops 2 mm short of the north wall
    r4._stamp(b, "S1", ["SALOON"], 2400, 3000)
    r4._stamp(b, "S2", ["KITCHEN"], 7500, 3000)
    return Case("G_T_JUNCTION_WITH_A_TWO_MILLIMETRE_MISS",
                "a hair short is still a junction",
                b.build(),
                {"min_released": 2, "junction_recovered": True})


def _h():
    b = Builder()
    r4._ring(b, 0, 0, 10000, 6000)
    _frag_v(b, 4900, 0, 4500)          # stops 1.5 m short — a real opening
    r4._stamp(b, "S1", ["SALOON"], 2400, 3000)
    r4._stamp(b, "S2", ["KITCHEN"], 7500, 3000)
    return Case("H_T_JUNCTION_WITH_A_LARGE_SEPARATION",
                "a metre and a half is a space, and a space is not a miss",
                b.build(),
                {"releases_nothing": True, "junction_recovered": False,
                 "no_unsupported_recovery": True})


def _i():
    b = Builder()
    r4._ring(b, 0, 0, 10000, 6000)
    # A column standing where the partition meets the north wall.
    r4._ring(b, 4900, 5400, 5300, 5800, layer=W, t=0.0)
    _frag_v(b, 4900, 0, 5400)
    r4._stamp(b, "S1", ["SALOON"], 2400, 3000)
    r4._stamp(b, "S2", ["KITCHEN"], 7500, 3000)
    return Case("I_WALL_TERMINATING_INTO_A_COLUMN",
                "a column does not break the partition that dies into it",
                b.build(),
                {"columns_observed_at_least": 1,
                 "no_column_released_as_a_room": True})


def _j():
    b = Builder()
    r4._ring(b, 0, 0, 12000, 8000)
    _frag_v(b, 5900, 0, 8000)
    # The horizontal partition's east half is drawn on one face only.
    r4._run(b, "H", 3900, 0, 12000, W, ())
    r4._run(b, "H", 4100, 0, 6100, W, ())
    r4._stamp(b, "S1", ["BEDROOM"], 2800, 1800)
    r4._stamp(b, "S2", ["STORE"], 9000, 1800)
    r4._stamp(b, "S3", ["SALOON"], 2800, 6000)
    r4._stamp(b, "S4", ["MAJLIS"], 9000, 6000)
    return Case("J_ONE_MISSING_FACE_WOULD_HAVE_MERGED_TWO_ROOMS",
                "four rooms, and the fourth depends on a face nobody drew",
                b.build(),
                {"min_released": 4, "subdivision_needed_recovery": True,
                 "material_authority_blocked_somewhere": True})


def _k():
    b = Builder()
    r4._ring(b, 0, 0, 9000, 5000)
    r4._stamp(b, "S1", ["KITCHEN"], 2500, 2500)
    r4._stamp(b, "S2", ["DINING AREA"], 6500, 2500)
    return Case("K_OPEN_PLAN_WITH_NO_PARTITION_AT_ALL",
                "several concepts in one open space are zones, not rooms",
                b.build(),
                {"releases_nothing": True, "functional_zone_groups": 1,
                 "undersegmentation_outcome": "ONE_PHYSICAL_SPACE",
                 "no_unsupported_recovery": True})


def _l():
    b = Builder()
    _two_room_shell(b)
    r4._partition_v(b, 4900, 0, 4000, gaps=[(1500, 2400)])
    r4._door(b, "D90", 4900, 1500, 900)
    return Case("L_TWO_ROOMS_A_WALL_AND_A_DOOR",
                "round 4's answer must still be round 4's answer",
                b.build(),
                {"min_released": 2, "door_candidates": 1})


def _m():
    b = Builder()
    r4._ring(b, 0, 0, 15000, 4000)
    _frag_v(b, 4900, 0, 4000, b_gaps=[(900, 1900)])
    _frag_v(b, 9900, 0, 4000, a_gaps=[(2200, 3100)])
    r4._stamp(b, "S1", ["SALOON"], 2400, 2000)
    r4._stamp(b, "S2", ["KITCHEN"], 7400, 2000)
    r4._stamp(b, "S3", ["PANTRY"], 12400, 2000)
    return Case("M_THREE_ROOMS_ON_FRAGMENTED_WALL_FACES",
                "two half-drawn partitions still make three rooms",
                b.build(),
                {"min_released": 3, "subdivision_needed_recovery": True})


def _n():
    b = Builder()
    r4._ring(b, 0, 0, 8000, 5000, openings=[("N", 3000, 4500)])
    r4._window(b, "H", 3000, 4500, 5000.0, 5000.0 + WALL_T)
    r4._stamp(b, "S1", ["BEDROOM"], 4000, 2500)
    return Case("N_EXTERNAL_WALL_FRAGMENTED_AROUND_A_WINDOW",
                "the window explains the break in the external wall",
                b.build(),
                {"min_released": 1, "window_candidates": 1,
                 "no_material_across_openings": True})


def _o():
    b = Builder()
    r4._ring(b, 0, 0, 12000, 7000)
    r4._partition_h(b, 4000, 0, 12000,
                    gaps=[(1500, 2400), (5500, 6400), (9500, 10400)])
    r4._partition_v(b, 3900, 0, 4000)
    r4._partition_v(b, 7900, 0, 4000)
    for x in (1500.0, 5500.0, 9500.0):
        r4._door(b, f"D{int(x)}", x, 4000, 900, rotation=-math.pi / 2)
    r4._stamp(b, "S0", ["CORRIDOR"], 6000, 5500)
    r4._stamp(b, "S1", ["BEDROOM"], 1900, 2000)
    r4._stamp(b, "S2", ["STORE"], 5900, 2000)
    r4._stamp(b, "S3", ["PANTRY"], 9900, 2000)
    return Case("O_CORRIDOR_WITH_REPEATED_DOORS",
                "three doors on one wall stay three doors",
                b.build(),
                {"min_released": 4, "door_candidates": 3})


def _p():
    b = Builder()
    r4._ring(b, 0, 0, 20000, 12000)
    r4._partition_v(b, 9900, 0, 12000, gaps=[(4000, 4900)])
    r4._door(b, "D90", 9900, 4000, 900)
    r4._partition_h(b, 5900, 0, 10100, gaps=[(2000, 2900)])
    r4._door(b, "D91", 2000, 5900, 900, rotation=-math.pi / 2)
    r4._stamp(b, "S1", ["SALOON"], 4500, 2800)
    r4._stamp(b, "S2", ["MAJLIS"], 4500, 9000)
    r4._stamp(b, "S3", ["KITCHEN"], 15000, 6000)
    return Case("P_AN_ENVELOPE_CONTAINING_SEVERAL_ROOMS",
                "the envelope is not one of the rooms it contains",
                b.build(),
                {"min_released": 3, "no_envelope_released": True})


def _q():
    b = Builder()
    r4._ring(b, 0, 0, 16000, 10000)
    r4._ring(b, 6000, 4000, 10000, 7000)          # an internal courtyard
    r4._stamp(b, "S1", ["COURTYARD"], 8000, 5500)
    r4._stamp(b, "S2", ["SALOON"], 2500, 5000)
    return Case("Q_A_COURTYARD",
                "an external space inside the fabric is not a room",
                b.build(),
                {"no_external_space_released": True})


def _r():
    b = Builder()
    r4._ring(b, 0, 0, 12000, 8000)
    r4._ring(b, 5000, 3000, 6200, 4400)           # an unlabelled shaft
    r4._stamp(b, "S1", ["SALOON"], 2500, 6000)
    return Case("R_A_SHAFT",
                "a bounded space nobody named is not released as a room",
                b.build(),
                {"no_unlabelled_face_released": True})


def _s():
    b = Builder()
    r4._ring(b, 0, 0, 9000, 5000)
    r4._stamp(b, "S1", ["SALOON"], 4500, 2500)
    # A title-block rule running past the building on its own layer.
    b.line(-1500.0, -1500.0, 10500.0, -1500.0, "TITLE")
    b.line(-1500.0, -1500.0, -1500.0, 6500.0, "TITLE")
    b.text("GROUND FLOOR PLAN 1:100", 4500.0, -1200.0, 300.0, "TITLE")
    return Case("S_A_TITLE_BLOCK_LINE_BESIDE_THE_BUILDING",
                "a sheet rule is not a wall and does not become one",
                b.build(),
                {"min_released": 1, "layer_not_wall_like": "TITLE"})


def _t():
    b = Builder()
    r4._ring(b, 0, 0, 9000, 5000)
    r4._stamp(b, "S1", ["SALOON"], 4500, 2500)
    # A lone line parallel to the south wall, at a plausible thickness.
    b.line(500.0, 300.0, 8500.0, 300.0, "ANNO")
    return Case("T_AN_ANNOTATION_LINE_THAT_LOOKS_LIKE_A_WALL_FACE",
                "one line parallel to a wall does not make a second wall",
                b.build(),
                {"min_released": 1, "layer_not_wall_like": "ANNO"})


def _u():
    b = Builder()
    r4._ring(b, 0, 0, 20000, 6000)
    # Two stubs on one line with eight metres of room between them.
    _frag_v(b, 9900, 0, 1500)
    _frag_v(b, 9900, 4500, 6000)
    r4._stamp(b, "S1", ["SALOON"], 5000, 3000)
    return Case("U_COLLINEAR_WALLS_WITH_REAL_SPACE_BETWEEN_THEM",
                "eight metres of room is not a drafting break",
                b.build(),
                {"no_unsupported_recovery": True,
                 "continuity_verdicts": ["UNRESOLVED_GAP"]})


def _v():
    b = Builder()
    r4._ring(b, 0, 0, 14000, 5000)
    _frag_v(b, 6900, 0, 5000, a_gaps=[(1800, 3200)], b_gaps=[(1800, 3200)])
    r4._stamp(b, "S1", ["SALOON"], 3400, 2500)
    r4._stamp(b, "S2", ["MAJLIS"], 10400, 2500)
    return Case("V_TWO_SPACES_THROUGH_AN_AMBIGUOUS_GAP",
                "unresolved means unresolved, on both sides of it",
                b.build(),
                {"releases_nothing": True,
                 "undersegmentation_outcome": "ROOM_PARTITION_UNRESOLVED",
                 "no_unsupported_recovery": True})


def _w():
    b = Builder()
    _two_room_shell(b)
    _frag_v(b, 4900, 0, 4000, b_gaps=[(400, 3600)])
    return Case("W_TOPOLOGY_RECOVERED_MATERIAL_STILL_INSUFFICIENT",
                "a room may be measurable while its blockwork is not",
                b.build(),
                {"min_released": 2,
                 "material_authority_blocked_somewhere": True,
                 "material_release_blocked_on_a_released_space": True})


_BUILDERS = (_a, _b, _c, _d, _e, _f, _g, _h, _i, _j, _k, _l, _m, _n, _o,
             _p, _q, _r, _s, _t, _u, _v, _w)


def cases() -> list:
    return [fn() for fn in _BUILDERS]


def freeze_hash() -> str:
    rows = []
    for c in cases():
        payload = "|".join(f"{k}={c.expect[k]}" for k in sorted(c.expect))
        rows.append(f"{c.name}|{payload}|{len(c.decode['OBJECTS'])}")
    return hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")
                          ).hexdigest()[:24]
