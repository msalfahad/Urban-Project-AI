"""Twenty-two drawings whose answers are known before the engine sees them.

Round 3's fixtures proved a room could be measured. These exist for the one
thing round 4 adds and the one thing it must not do:

    an opening may close a room that no continuous wall closes
    A GAP IS NOT AN OPENING

Every case below states its own required result, and several of them
require NOTHING to happen — E's wall gap, S's floating swing, T's
annotation arc and Q's site gate all exist so that a change which starts
bridging gaps fails here rather than on a client's drawing.

No case states an expected room count for P7757, an expected area, or any
size a room ought to be. Where a case names an area it is the arithmetic of
the rectangle drawn.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from engine.cad_fixtures import Builder

WALL_T = 200.0
W = "W"            # the wall layer. Its NAME means nothing to the engine
D = "D"            # door symbols
G = "G"            # glazing
TXT = "TXT"


@dataclass(frozen=True)
class Case:
    name: str
    what_it_tests: str
    decode: dict
    expect: dict


# ----------------------------------------------------------------- drawing

def _run(b, axis, fixed, lo, hi, layer, gaps=()):
    """One line with intervals cut out of it."""
    pos = lo
    for a, c in sorted(gaps):
        if a > pos:
            _emit(b, axis, fixed, pos, a, layer)
        pos = max(pos, c)
    if pos < hi:
        _emit(b, axis, fixed, pos, hi, layer)


def _emit(b, axis, fixed, lo, hi, layer):
    if axis == "H":
        b.line(lo, fixed, hi, fixed, layer)
    else:
        b.line(fixed, lo, fixed, hi, layer)


def _wall(b, axis, f0, f1, lo, hi, layer=W, *, gaps=(), jambs=True,
          outer_extend=0.0):
    """A wall drawn as two faces, optionally pierced, optionally revealed."""
    _run(b, axis, f0, lo, hi, layer, gaps)
    _run(b, axis, f1, lo - outer_extend, hi + outer_extend, layer, gaps)
    if not jambs:
        return
    cross = "V" if axis == "H" else "H"
    for a, c in gaps:
        for station in (a, c):
            _emit(b, cross, station, min(f0, f1), max(f0, f1), layer)


def _ring(b, x0, y0, x1, y1, layer=W, t=WALL_T, *, openings=(), jambs=True):
    """A closed rectangular wall, with openings cut through named sides."""
    def g(side):
        return [(a, c) for s, a, c in openings if s == side]

    _wall(b, "H", y0, y0 - t, x0, x1, layer, gaps=g("S"), jambs=jambs,
          outer_extend=t)
    _wall(b, "H", y1, y1 + t, x0, x1, layer, gaps=g("N"), jambs=jambs,
          outer_extend=t)
    _wall(b, "V", x0, x0 - t, y0, y1, layer, gaps=g("W"), jambs=jambs,
          outer_extend=t)
    _wall(b, "V", x1, x1 + t, y0, y1, layer, gaps=g("E"), jambs=jambs,
          outer_extend=t)


def _partition_v(b, x, y0, y1, layer=W, t=WALL_T, *, gaps=(), jambs=True):
    _wall(b, "V", x, x + t, y0, y1, layer, gaps=gaps, jambs=jambs)


def _partition_h(b, y, x0, x1, layer=W, t=WALL_T, *, gaps=(), jambs=True):
    _wall(b, "H", y, y + t, x0, x1, layer, gaps=gaps, jambs=jambs)


def _door(b, name, x, y, width, *, rotation=0.0, scale=1.0, nested=False,
          layer=D):
    """A door assembly: a leaf and its swing, placed by ONE transform."""
    leaf = b.line(0.0, 0.0, width, 0.0, layer)
    arc = b.arc(0.0, 0.0, width, 0.0, math.pi / 2, layer)
    if nested:
        b.block(f"{name}_ASSY", [leaf, arc])
        inner = b.insert(f"{name}_ASSY", 0.0, 0.0)
        b.block(name, [inner])
    else:
        b.block(name, [leaf, arc])
    b.insert(name, x, y, rotation=rotation, scale=(scale, scale))


def _window(b, axis, lo, hi, f0, f1, *, layer=G, block=""):
    """Two lines parallel to the wall, spanning the opening.

    They sit 30 mm apart — below the smallest separation this engine will
    call a wall — so the glazing can never be mistaken for blockwork.
    """
    base = min(f0, f1)
    t = abs(f1 - f0)
    a = base + t * 0.35
    c = a + 30.0
    if block:
        h1 = _emit_h(b, axis, a, lo, hi, layer)
        h2 = _emit_h(b, axis, c, lo, hi, layer)
        b.block(block, [h1, h2])
        b.insert(block, 0.0, 0.0)
    else:
        _emit(b, axis, a, lo, hi, layer)
        _emit(b, axis, c, lo, hi, layer)


def _emit_h(b, axis, fixed, lo, hi, layer):
    if axis == "H":
        return b.line(lo, fixed, hi, fixed, layer)
    return b.line(fixed, lo, fixed, hi, layer)


def _stamp(b, block, texts, x, y, layer=TXT):
    handles = [b.text(t, 0.0, i * -300.0, 250.0, layer)
               for i, t in enumerate(texts)]
    b.block(block, handles)
    b.insert(block, x, y)


# ------------------------------------------------------------------- cases

def _a():
    b = Builder()
    _ring(b, 0, 0, 10000, 4000)
    _partition_v(b, 4900, 0, 4000, gaps=[(1500, 2400)])
    _door(b, "D90", 4900, 1500, 900)
    _stamp(b, "S1", ["SALOON"], 2400, 2000)
    _stamp(b, "S2", ["KITCHEN"], 7500, 2000)
    return Case("A_TWO_ROOMS_ONE_HINGED_DOOR",
                "a door closes two rooms that no continuous wall closes",
                b.build(),
                {"min_released": 2, "door_candidates": 1,
                 "opening_classes": ["DOOR_WITH_LEAF"],
                 "relation_present": "TWO_DISTINCT_PHYSICAL_SPACES",
                 "no_merged_super_room": True})


def _b():
    b = Builder()
    _ring(b, 0, 0, 10000, 4000)
    _partition_v(b, 4900, 0, 4000, gaps=[(1300, 3100)])
    _door(b, "D90A", 4900, 1300, 900)
    _door(b, "D90B", 4900, 3100, 900, rotation=math.pi)
    _stamp(b, "S1", ["MAJLIS"], 2400, 2000)
    _stamp(b, "S2", ["DINING"], 7500, 2000)
    return Case("B_TWO_ROOMS_DOUBLE_DOOR",
                "two leaves in one interruption are ONE opening",
                b.build(),
                {"min_released": 2, "door_candidates": 1,
                 "opening_width_mm": 1800.0,
                 "no_merged_super_room": True})


def _c():
    b = Builder()
    _ring(b, 0, 0, 6000, 4000, openings=[("S", 2000, 3200)])
    _window(b, "H", 2000, 3200, 0.0, -WALL_T)
    _stamp(b, "S1", ["BEDROOM"], 3000, 2000)
    return Case("C_ROOM_WITH_AN_EXTERNAL_WINDOW",
                "a window closes the boundary and is not a passage",
                b.build(),
                {"min_released": 1, "window_candidates": 1,
                 "door_candidates": 0,
                 "window_is_not_navigable": True,
                 "opening_classes": ["WINDOW_OPENING"]})


def _d():
    b = Builder()
    _ring(b, 0, 0, 8000, 5000,
          openings=[("S", 1000, 2200), ("S", 4000, 5200), ("E", 2000, 2900)])
    _window(b, "H", 1000, 2200, 0.0, -WALL_T)
    _window(b, "H", 4000, 5200, 0.0, -WALL_T)
    _door(b, "D90", 8000, 2000, 900)
    _stamp(b, "S1", ["BEDROOM"], 4000, 2500)
    return Case("D_TWO_WINDOWS_AND_A_DOOR",
                "windows and doors are counted and treated differently",
                b.build(),
                {"min_released": 1, "window_candidates": 2,
                 "door_candidates": 1})


def _e():
    b = Builder()
    _ring(b, 0, 0, 10000, 4000)
    _partition_v(b, 4900, 0, 4000, gaps=[(1500, 2400)], jambs=False)
    _stamp(b, "S1", ["SALOON"], 2400, 2000)
    _stamp(b, "S2", ["KITCHEN"], 7500, 2000)
    return Case("E_WALL_GAP_WITH_NO_DOOR_EVIDENCE",
                "a gap alone closes nothing and releases nothing",
                b.build(),
                {"releases_nothing": True,
                 "opening_classes": ["UNRESOLVED_WALL_GAP"],
                 "no_opening_may_close": True,
                 "grade_d_present": True})


def _f():
    b = Builder()
    _ring(b, 0, 0, 12000, 5000)
    _partition_v(b, 5900, 0, 5000, gaps=[(1500, 3500)])
    _stamp(b, "S1", ["LIVING AREA"], 2800, 2500)
    _stamp(b, "S2", ["DINING AREA"], 9000, 2500)
    return Case("F_WIDE_DOORLESS_OPENING_BETWEEN_ZONES",
                "a doorless opening resolves neither one space nor two",
                b.build(),
                {"releases_nothing": True,
                 "opening_classes": ["DOORLESS_ARCHWAY"],
                 "relation_present": "ROOM_PARTITION_RELATION_UNRESOLVED",
                 "min_complete": 2})


def _g():
    b = Builder()
    _ring(b, 0, 0, 12000, 5000)
    _partition_v(b, 5900, 0, 5000, gaps=[(1800, 3200)])
    _stamp(b, "S1", ["SALOON"], 2800, 2500)
    _stamp(b, "S2", ["MAJLIS"], 9000, 2500)
    return Case("G_ARCHWAY_BETWEEN_TWO_ROOM_IDENTITIES",
                "an archway measures both spaces and releases neither",
                b.build(),
                {"releases_nothing": True,
                 "opening_classes": ["DOORLESS_ARCHWAY"],
                 "relation_present": "ROOM_PARTITION_RELATION_UNRESOLVED",
                 "min_complete": 2})


def _h():
    b = Builder()
    _ring(b, 0, 0, 9000, 5000)
    _stamp(b, "S1", ["KITCHEN"], 2500, 2500)
    _stamp(b, "S2", ["DINING AREA"], 6500, 2500)
    return Case("H_OPEN_PLAN_WITH_NO_SEPARATOR",
                "two labels in one face are one space and two zones",
                b.build(),
                {"releases_nothing": True,
                 "functional_zone_groups": 1,
                 "no_openings_at_all": True,
                 "min_complete": 1})


def _i():
    b = Builder()
    _ring(b, 0, 0, 12000, 7000)
    _partition_h(b, 4000, 0, 12000,
                 gaps=[(1500, 2400), (5500, 6400), (9500, 10400)])
    _partition_v(b, 3900, 0, 4000)
    _partition_v(b, 7900, 0, 4000)
    for x in (1500.0, 5500.0, 9500.0):
        _door(b, f"D{int(x)}", x, 4000, 900, rotation=-math.pi / 2)
    _stamp(b, "S0", ["CORRIDOR"], 6000, 5500)
    _stamp(b, "S1", ["BEDROOM"], 1900, 2000)
    _stamp(b, "S2", ["STORE"], 5900, 2000)
    _stamp(b, "S3", ["PANTRY"], 9900, 2000)
    return Case("I_CORRIDOR_WITH_DOORS_TO_THREE_ROOMS",
                "three doors on one wall stay three openings",
                b.build(),
                {"min_released": 4, "door_candidates": 3,
                 "no_merged_super_room": True})


def _j():
    b = Builder()
    _ring(b, 0, 0, 10000, 4000)
    _partition_v(b, 4900, 0, 4000, gaps=[(1500, 2400)])
    _door(b, "D90", 4900, 1500, 900)
    _stamp(b, "S1", ["SALOON"], 2400, 2000)
    return Case("J_UNLABELLED_ROOM_WITH_A_VALID_DOOR",
                "a physical space does not need a readable name to exist",
                b.build(),
                {"min_released": 1,
                 "validated_geometry_unknown_identity": 1,
                 "min_complete": 2})


def _k():
    b = Builder()
    _ring(b, 0, 0, 10000, 4000)
    _partition_v(b, 4900, 0, 4000, gaps=[(1500, 2400)])
    _door(b, "D90", 4900, 1500, 900)
    _stamp(b, "S1", ["KITCHEN", "مطبخ"], 2400, 2000)
    _stamp(b, "S2", ["BEDROOM"], 7500, 2000)
    return Case("K_BILINGUAL_LABELLED_ROOM_WITH_A_DOOR",
                "two languages for one room are one identity, not a conflict",
                b.build(),
                {"min_released": 2, "identity_relationship": "SAME_CONCEPT",
                 "independent_statements": 2})


def _l():
    b = Builder()
    _ring(b, 0, 0, 8000, 8000)
    _partition_h(b, 3900, 0, 8000, gaps=[(3000, 3900)])
    _door(b, "D90", 3000, 3900, 900, rotation=-math.pi / 2)
    _stamp(b, "S1", ["BEDROOM"], 4000, 1800)
    _stamp(b, "S2", ["SALOON"], 4000, 6000)
    return Case("L_DOOR_BLOCK_ROTATED_90_DEGREES",
                "the transform is resolved before anything is matched",
                b.build(),
                {"min_released": 2, "door_candidates": 1,
                 "opening_classes": ["DOOR_WITH_LEAF"]})


def _m():
    b = Builder()
    _ring(b, 0, 0, 8000, 8000)
    _partition_h(b, 3900, 0, 8000, gaps=[(3000, 4080)])
    _door(b, "D90", 3000, 3900, 900, rotation=-math.pi / 2, scale=1.2)
    _stamp(b, "S1", ["BEDROOM"], 4000, 1800)
    _stamp(b, "S2", ["SALOON"], 4000, 6000)
    return Case("M_DOOR_BLOCK_SCALED",
                "a scaled insert measures 1080 mm, not the 900 it was drawn",
                b.build(),
                {"min_released": 2, "door_candidates": 1,
                 "opening_width_mm": 1080.0})


def _n():
    b = Builder()
    _ring(b, 0, 0, 10000, 4000)
    _partition_v(b, 4900, 0, 4000, gaps=[(1500, 2400)])
    _door(b, "D90", 4900, 1500, 900, nested=True)
    _stamp(b, "S1", ["SALOON"], 2400, 2000)
    _stamp(b, "S2", ["KITCHEN"], 7500, 2000)
    return Case("N_NESTED_DOOR_INSERT",
                "an INSERT inside an INSERT resolves to the same door",
                b.build(),
                {"min_released": 2, "door_candidates": 1,
                 "opening_classes": ["DOOR_WITH_LEAF"]})


def _o():
    """A swing at a corner where two walls are both pierced under it.

    The vertical partition's opening ends at (5100, 3000) and the
    horizontal partition's opening begins at the same point. One swing is
    drawn there, both openings are 900 mm, and nothing on the drawing says
    which wall it belongs to. A nearest-wall rule would pick one and be
    right half the time.
    """
    b = Builder()
    _ring(b, 0, 0, 12000, 7000)
    _partition_v(b, 4900, 0, 7000, gaps=[(2100, 3000)])
    _partition_h(b, 3000, 0, 12000, gaps=[(5100, 6000)])
    arc = b.arc(5100.0, 3000.0, 900.0, 0.0, math.pi / 2, D)
    b.block("DAMB", [arc])
    b.insert("DAMB", 0.0, 0.0)
    _stamp(b, "S1", ["SALOON"], 2400, 1500)
    _stamp(b, "S2", ["KITCHEN"], 8500, 1500)
    _stamp(b, "S3", ["MAJLIS"], 6000, 5000)
    return Case("O_OPENING_NEAR_TWO_POSSIBLE_HOST_WALLS",
                "an unresolved host is an answer, not a nearest-wall guess",
                b.build(),
                {"ambiguous_hosts_at_least": 2,
                 "no_release_through_an_ambiguous_portal": True})


def _p():
    b = Builder()
    _ring(b, 0, 0, 7000, 4500, openings=[("N", 2500, 3700)])
    _window(b, "H", 2500, 3700, 4500.0, 4500.0 + WALL_T, block="W120")
    _stamp(b, "S1", ["BEDROOM"], 3500, 2200)
    return Case("P_WINDOW_SYMBOL_IN_A_WALL_INTERRUPTION",
                "a window block is a window, and never a room-to-room portal",
                b.build(),
                {"min_released": 1, "window_candidates": 1,
                 "door_candidates": 0,
                 "window_is_not_navigable": True})


def _q():
    b = Builder()
    _ring(b, 0, 0, 40000, 30000, layer="PLOT",
          openings=[("S", 18000, 22000)])
    _ring(b, 10000, 8000, 26000, 20000)
    _partition_v(b, 17900, 8000, 20000, gaps=[(12000, 12900)])
    _door(b, "D90", 17900, 12000, 900)
    _stamp(b, "S1", ["SALOON"], 13000, 14000)
    _stamp(b, "S2", ["KITCHEN"], 22000, 14000)
    return Case("Q_SITE_GATE_IN_A_PLOT_BOUNDARY",
                "a gate in the plot wall is never an internal room separator",
                b.build(),
                {"min_released": 2,
                 "gate_not_on_a_released_boundary": True,
                 "site_must_not_close_a_room": True})


def _r():
    b = Builder()
    _ring(b, 0, 0, 12000, 6000, openings=[("S", 5000, 6100)])
    _door(b, "D110", 5000, 0, 1100, rotation=math.pi / 2)
    _partition_v(b, 5900, 0, 6000, gaps=[(2500, 3400)])
    _door(b, "D90", 5900, 2500, 900)
    _stamp(b, "S1", ["HALL"], 2800, 3000)
    _stamp(b, "S2", ["SALOON"], 9000, 3000)
    return Case("R_BUILDING_ENTRANCE_DOOR",
                "an entrance closes the envelope instead of leaking it",
                b.build(),
                {"min_released": 2, "door_candidates": 2,
                 "external_wall_may_close": True})


def _s():
    b = Builder()
    _ring(b, 0, 0, 8000, 5000)
    b.arc(4000.0, 2500.0, 900.0, 0.0, math.pi / 2, D)
    _stamp(b, "S1", ["SALOON"], 3000, 2000)
    return Case("S_DOOR_SWING_TOUCHING_NO_WALL",
                "a swing with no wall to pierce is not a door",
                b.build(),
                {"min_released": 1, "door_candidates": 0,
                 "unmatched_symbols_at_least": 1})


def _t():
    b = Builder()
    _ring(b, 0, 0, 8000, 5000)
    # An arc drawn beside an unbroken wall — a north point, a revision
    # cloud, a detail marker. It looks like a swing and pierces nothing.
    b.arc(1200.0, 300.0, 800.0, 0.0, math.pi / 2, "ANNO")
    _stamp(b, "S1", ["SALOON"], 4000, 2500)
    return Case("T_ANNOTATION_ARC_RESEMBLING_A_SWING",
                "looking like a door is not being one",
                b.build(),
                {"min_released": 1, "door_candidates": 0,
                 "no_openings_at_all": True,
                 "unmatched_symbols_at_least": 1})


def _u():
    b = Builder()
    for k, dx in enumerate((0.0, 200000.0)):
        _ring(b, dx, 0, dx + 10000, 4000)
        _partition_v(b, dx + 4900, 0, 4000, gaps=[(1500, 2400)])
        _door(b, f"D90_{k}", dx + 4900, 1500, 900)
        _stamp(b, f"S{k}A", ["SALOON"], dx + 2400, 2000)
        _stamp(b, f"S{k}B", ["KITCHEN"], dx + 7500, 2000)
    return Case("U_TWO_UNRELATED_DRAWING_REGIONS",
                "no wall, portal or containment relationship crosses a region",
                b.build(),
                {"min_regions": 2, "min_released": 4,
                 "no_relationship_crosses_a_region": True})


def _v():
    b = Builder()
    _ring(b, 0, 0, 14000, 9000, openings=[("S", 6000, 6900)])
    _door(b, "D90E", 6000, 0, 900, rotation=math.pi / 2)
    _partition_v(b, 4900, 4900, 9000)
    _partition_h(b, 4900, 0, 5100, gaps=[(1800, 2700)])
    _door(b, "D90I", 1800, 4900, 900, rotation=-math.pi / 2)
    _stamp(b, "S1", ["BEDROOM"], 2400, 7000)
    _stamp(b, "S2", ["HALL"], 9000, 4500)
    return Case("V_EXTERNAL_WALL_PARTITIONS_AND_A_DOORWAY",
                "two external walls and two partitions make one room",
                b.build(),
                {"min_released": 1, "external_wall_may_close": True,
                 "door_candidates": 2})


_BUILDERS = (_a, _b, _c, _d, _e, _f, _g, _h, _i, _j, _k, _l, _m, _n, _o,
             _p, _q, _r, _s, _t, _u, _v)


def cases() -> list:
    return [fn() for fn in _BUILDERS]


def freeze_hash() -> str:
    parts = []
    for c in cases():
        payload = "|".join(
            f"{k}={c.expect[k]}" for k in sorted(c.expect))
        parts.append(f"{c.name}|{payload}|{len(c.decode['OBJECTS'])}")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:24]
