"""The three first synthetic villas of T-019 (own geometry, no client drawing). Every coordinate is in metres in the
plan's LOCAL frame (outer face lower-left at 0, 0); the writer turns, mirrors and scales the plan at write time.

A room is the polygon of its wall FACES (counter-clockwise); a vertex (x, y, b) carries the LWPOLYLINE bulge b of the
edge to the next vertex (b = tan(sweep / 4); a quarter circle bulging outwards is +tan(22.5 deg)). Walls are the gaps
between room faces and the outer face. An opening sits in a straight wall: axis "x" is a vertical wall occupying
x in [lo, hi] with the gap y in [s0, s1]; axis "y" a horizontal wall with the gap x in [s0, s1]. `opens` is the side
the leaf swings into ("+" towards hi, "-" towards lo); `hand` "R" draws the door block mirrored (yscale -1).

HAND is written by hand from the coordinates below (the derivations are in the comments). It is compared in the tests
with the formulas of `truth.py` (shoelace + circular segments), two independent ways to the same number; nothing
here or there comes from the engine.
"""

from __future__ import annotations

import math

Q = math.tan(math.radians(22.5))          # bulge of a quarter circle


def _o(oid, kind, axis, lo, hi, s0, s1, rooms, opens="+", hand="L"):
    return {"id": oid, "kind": kind, "axis": axis, "lo": lo, "hi": hi, "s0": s0, "s1": s1, "rooms": rooms,
            "opens": opens, "hand": hand}


def _r(poly, label, probe, code, wet, kind):
    return {"poly": poly, "label": label, "probe": probe, "code": code, "wet": wet, "kind": kind}


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# ---------------------------------------------------------------------------------------------------------------
# SV-A: one ground floor, walls 0.20 (exterior and two partitions) and one 0.10 partition; English + Arabic labels.
#   outer 12.4 x 8.4; inner 0.2..12.2 x 0.2..8.2; partition x 6.2..6.4 full height; y 4.2..4.4 from x 6.4 to 12.2;
#   0.10 partition x 9.3..9.4 from y 0.2 to 4.2.
SV_A = {
    "villa_id": "SV-A",
    "floors": {
        "GF": {
            "title": "GROUND FLOOR PLAN", "level": "+0.00",
            "outer": _rect(0, 0, 12.4, 8.4),
            "rooms": {
                "A-LIV": _r(_rect(0.2, 0.2, 6.2, 8.2), "LIVING ROOM", (3.0, 6.0), "LIVING", False, "DRY"),
                "A-KIT": _r(_rect(6.4, 0.2, 9.3, 4.2), "مطبخ", (7.8, 2.6), "KITCHEN", False, "SERVICE"),
                "A-BTH": _r(_rect(9.4, 0.2, 12.2, 4.2), "حمام", (10.8, 3.0), "BATHROOM", True, "WET"),
                "A-BED": _r(_rect(6.4, 4.4, 12.2, 8.2), "BEDROOM", (9.0, 6.8), "BEDROOM", False, "DRY"),
            },
            "openings": [
                _o("A-D1", "DOOR", "y", 0.0, 0.2, 2.0, 3.0, ["A-LIV"], "+"),               # entrance 1.00
                _o("A-D2", "DOOR", "x", 6.2, 6.4, 1.0, 1.9, ["A-LIV", "A-KIT"], "+", "R"),  # 0.90 mirrored block
                _o("A-D3", "DOOR", "x", 6.2, 6.4, 5.5, 6.4, ["A-LIV", "A-BED"], "+"),       # 0.90
                _o("A-D4", "DOOR", "y", 4.2, 4.4, 10.0, 10.8, ["A-BED", "A-BTH"], "-"),     # 0.80 into the bath
                _o("A-W1", "WINDOW", "x", 0.0, 0.2, 3.0, 4.5, ["A-LIV"]),                   # 1.50
                _o("A-W2", "WINDOW", "y", 8.2, 8.4, 8.0, 9.5, ["A-BED"]),                   # 1.50
                _o("A-W3", "WINDOW", "y", 0.0, 0.2, 7.0, 8.2, ["A-KIT"]),                   # 1.20
                _o("A-W4", "WINDOW", "x", 12.2, 12.4, 1.5, 2.1, ["A-BTH"]),                 # 0.60
            ],
        },
    },
}

# ---------------------------------------------------------------------------------------------------------------
# SV-B: two floors, exterior 0.30, partitions 0.20 and 0.15; Arabic titles and labels (one English per floor);
#   outer 10.6 x 9.6 on both floors; inner 0.3..10.3 x 0.3..9.3; 0.20 partition x 5.3..5.5 full height and
#   y 5.3..5.5 from x 5.5 to 10.3.
SV_B = {
    "villa_id": "SV-B",
    "floors": {
        "GF": {
            # 0.15 partitions: y 6.3..6.45 from x 0.3 to 5.3; x 2.3..2.45 from y 6.45 to 9.3
            "title": "مسقط الدور الأرضي", "level": "+0.00",
            "outer": _rect(0, 0, 10.6, 9.6),
            "rooms": {
                "B0-MAJ": _r(_rect(0.3, 0.3, 5.3, 6.3), "مجلس", (2.8, 4.8), "MAJLIS", False, "DRY"),
                "B0-WC": _r(_rect(0.3, 6.45, 2.3, 9.3), "W.C.", (1.3, 8.6), "BATHROOM", True, "WET"),
                "B0-STO": _r(_rect(2.45, 6.45, 5.3, 9.3), "مخزن", (3.9, 8.6), "STORE", False, "DRY"),
                "B0-LIV": _r(_rect(5.5, 0.3, 10.3, 5.3), "صالة", (7.9, 4.0), "LIVING", False, "DRY"),
                "B0-STR": _r(_rect(5.5, 5.5, 10.3, 9.3), "درج", (7.9, 8.6), "STAIR", False, "STAIR"),
            },
            "openings": [
                _o("B0-D1", "DOOR", "x", 10.3, 10.6, 1.5, 2.5, ["B0-LIV"], "-"),               # entrance 1.00
                _o("B0-D2", "DOOR", "x", 5.3, 5.5, 1.0, 2.0, ["B0-LIV", "B0-MAJ"], "-"),       # 1.00
                _o("B0-D3", "DOOR", "y", 6.3, 6.45, 1.0, 1.8, ["B0-MAJ", "B0-WC"], "+"),       # 0.80
                _o("B0-D4", "DOOR", "y", 6.3, 6.45, 3.5, 4.3, ["B0-MAJ", "B0-STO"], "+", "R"), # 0.80 mirrored block
                _o("B0-P1", "PASSAGE", "y", 5.3, 5.5, 6.0, 7.2, ["B0-LIV", "B0-STR"]),         # 1.20, no door
                _o("B0-W1", "WINDOW", "x", 0.0, 0.3, 2.0, 4.0, ["B0-MAJ"]),                    # 2.00
                _o("B0-W2", "WINDOW", "y", 0.0, 0.3, 7.0, 9.0, ["B0-LIV"]),                    # 2.00
                _o("B0-W3", "WINDOW", "x", 0.0, 0.3, 7.5, 8.1, ["B0-WC"]),                     # 0.60
                _o("B0-W4", "WINDOW", "x", 10.3, 10.6, 6.5, 8.0, ["B0-STR"]),                  # 1.50
            ],
        },
        "1F": {
            # 0.15 partition: y 2.85..3.0 from x 0.3 to 5.3
            "title": "مسقط الدور الأول", "level": "+3.60",
            "outer": _rect(0, 0, 10.6, 9.6),
            "rooms": {
                "B1-BTH": _r(_rect(0.3, 0.3, 5.3, 2.85), "BATHROOM", (2.8, 1.5), "BATHROOM", True, "WET"),
                "B1-BED": _r(_rect(0.3, 3.0, 5.3, 9.3), "غرفة نوم", (2.8, 8.0), "BEDROOM", False, "DRY"),
                "B1-MST": _r(_rect(5.5, 0.3, 10.3, 5.3), "غرفة نوم رئيسية", (7.9, 4.0), "MASTER_BEDROOM", False,
                             "DRY"),
                "B1-STR": _r(_rect(5.5, 5.5, 10.3, 9.3), "درج", (7.9, 6.4), "STAIR", False, "STAIR"),
            },
            "openings": [
                _o("B1-D1", "DOOR", "x", 5.3, 5.5, 7.0, 7.9, ["B1-STR", "B1-BED"], "-"),       # 0.90
                _o("B1-D2", "DOOR", "y", 2.85, 3.0, 1.0, 1.8, ["B1-BED", "B1-BTH"], "-"),      # 0.80
                _o("B1-D3", "DOOR", "y", 5.3, 5.5, 8.0, 8.9, ["B1-STR", "B1-MST"], "-"),       # 0.90
                _o("B1-W1", "WINDOW", "x", 0.0, 0.3, 5.0, 6.5, ["B1-BED"]),                    # 1.50
                _o("B1-W2", "WINDOW", "y", 0.0, 0.3, 2.0, 2.6, ["B1-BTH"]),                    # 0.60
                _o("B1-W3", "WINDOW", "x", 10.3, 10.6, 1.5, 3.5, ["B1-MST"]),                  # 2.00
                _o("B1-W4", "WINDOW", "y", 0.0, 0.3, 7.0, 8.5, ["B1-MST"]),                    # 1.50
                _o("B1-W5", "WINDOW", "y", 9.3, 9.6, 7.0, 8.0, ["B1-STR"]),                    # 1.00
            ],
        },
    },
}

# ---------------------------------------------------------------------------------------------------------------
# SV-C: one floor; the north-east corner is a CURVED wall (concentric quarter circles about (10.0, 8.0): inner face
#   r 2.0, outer face r 2.2); an L-shaped living room; one room drawn WITHOUT a label (its design intent, a dining
#   room, is not on the drawing). Exterior and partitions 0.20; one 0.10 partition.
#   outer 12.2 x 10.2; inner 0.2..12.0 x 0.2..10.0; partitions: y 4.0..4.2 full width; x 5.0..5.2 and x 9.0..9.1
#   (0.10) from y 0.2 to 4.0; the bedroom block: x 7.0..7.2 from y 4.2 to 7.2 and y 7.0..7.2 from x 0.2 to 7.2.
SV_C = {
    "villa_id": "SV-C",
    "floors": {
        "GF": {
            "title": "GROUND FLOOR PLAN", "level": "+0.00",
            "outer": [(0, 0), (12.2, 0), (12.2, 8.0, Q), (10.0, 10.2), (0, 10.2)],
            "rooms": {
                "C-KIT": _r(_rect(0.2, 0.2, 5.0, 4.0), "KITCHEN", (2.6, 3.0), "KITCHEN", False, "SERVICE"),
                "C-DIN": _r(_rect(5.2, 0.2, 9.0, 4.0), None, (7.1, 2.5), None, False, "DRY"),
                "C-BTH": _r(_rect(9.1, 0.2, 12.0, 4.0), "دورة مياه", (10.5, 3.0), "BATHROOM", True, "WET"),
                "C-LIV": _r([(7.2, 4.2), (12.0, 4.2), (12.0, 8.0, Q), (10.0, 10.0), (0.2, 10.0), (0.2, 7.2),
                             (7.2, 7.2)], "LIVING / صالة", (4.0, 8.6), "LIVING", False, "DRY"),
                "C-BED": _r(_rect(0.2, 4.2, 7.0, 7.0), "غرفة نوم", (3.5, 6.0), "BEDROOM", False, "DRY"),
            },
            "openings": [
                _o("C-D1", "DOOR", "y", 10.0, 10.2, 3.0, 4.0, ["C-LIV"], "-"),               # entrance 1.00
                _o("C-D2", "DOOR", "x", 5.0, 5.2, 1.0, 1.9, ["C-KIT", "C-DIN"], "+"),        # 0.90
                _o("C-D3", "DOOR", "y", 4.0, 4.2, 7.5, 8.4, ["C-DIN", "C-LIV"], "+"),        # 0.90
                _o("C-D4", "DOOR", "y", 4.0, 4.2, 10.0, 10.8, ["C-LIV", "C-BTH"], "-"),      # 0.80
                _o("C-D5", "DOOR", "x", 7.0, 7.2, 5.0, 5.9, ["C-LIV", "C-BED"], "-", "R"),   # 0.90 mirrored block
                _o("C-W1", "WINDOW", "y", 0.0, 0.2, 1.5, 3.0, ["C-KIT"]),                    # 1.50
                _o("C-W2", "WINDOW", "y", 0.0, 0.2, 6.0, 7.5, ["C-DIN"]),                    # 1.50
                _o("C-W3", "WINDOW", "x", 12.0, 12.2, 1.5, 2.1, ["C-BTH"]),                  # 0.60
                _o("C-W4", "WINDOW", "x", 0.0, 0.2, 5.0, 6.5, ["C-BED"]),                    # 1.50
                _o("C-W5", "WINDOW", "x", 12.0, 12.2, 5.0, 7.0, ["C-LIV"]),                  # 2.00
            ],
        },
    },
}

VILLAS = {"SV-A": SV_A, "SV-B": SV_B, "SV-C": SV_C}

# the first run's variant of each villa (T-019): A plain (mm, AIA layers); B in metres, Arabic layer names, mirrored;
# C turned 37 degrees, with its curved wall and its unlabelled room
FIRST_RUN = {
    "SV-A": {"units": "mm", "layers": "AIA", "rotate_deg": 0.0, "mirror": False},
    "SV-B": {"units": "m", "layers": "ARABIC", "rotate_deg": 0.0, "mirror": True},
    "SV-C": {"units": "mm", "layers": "AIA", "rotate_deg": 37.0, "mirror": False},
}

# ---------------------------------------------------------------------------------------------------------------
# HAND truth (m2, lm), written from the coordinates above. Wall convention: per thickness, the centreline length of
# the exterior ring plus the clear length of each partition between the faces it meets (a T or L junction piece is
# counted once, in the wall that runs through), openings NOT deducted (gross); net = gross - the opening widths in
# walls of that thickness. Check: sum(t x gross) = outer area - sum(room areas) (the wall mass, doorway pieces in).
PI = math.pi
HAND = {
    "SV-A": {"GF": {
        "outer_m2": 12.4 * 8.4,                                  # 104.16
        "rooms_m2": {"A-LIV": 48.0, "A-KIT": 11.6, "A-BTH": 11.2, "A-BED": 22.04},
        # 0.20: exterior ring 2 x (12.2 + 8.2) = 40.8; x 6.3 clear 8.0; y 4.3 clear 5.8 -> 54.6
        # 0.20 openings: 1.0 + 0.9 + 0.9 + 0.8 + 1.5 + 1.5 + 1.2 + 0.6 = 8.4; 0.10: x 9.35 clear 4.0, none
        "walls": {"0.20": {"gross_lm": 54.6, "openings_lm": 8.4}, "0.10": {"gross_lm": 4.0, "openings_lm": 0.0}},
        "counts": {"DOOR": 4, "WINDOW": 4, "PASSAGE": 0, "rooms": 4, "wet": 1},
    }},
    "SV-B": {
        "GF": {
            "outer_m2": 10.6 * 9.6,                              # 101.76
            "rooms_m2": {"B0-MAJ": 30.0, "B0-WC": 5.7, "B0-STO": 8.1225, "B0-LIV": 24.0, "B0-STR": 18.24},
            # 0.30 ring 2 x (10.3 + 9.3) = 39.2; 0.20: x 5.4 clear 9.0 + y 5.4 clear 4.8 = 13.8;
            # 0.15: y 6.375 clear 5.0 + x 2.375 clear 2.85 = 7.85
            "walls": {"0.30": {"gross_lm": 39.2, "openings_lm": 1.0 + 2.0 + 2.0 + 0.6 + 1.5},
                      "0.20": {"gross_lm": 13.8, "openings_lm": 1.0 + 1.2},
                      "0.15": {"gross_lm": 7.85, "openings_lm": 0.8 + 0.8}},
            "counts": {"DOOR": 4, "WINDOW": 4, "PASSAGE": 1, "rooms": 5, "wet": 1},
        },
        "1F": {
            "outer_m2": 10.6 * 9.6,
            "rooms_m2": {"B1-BTH": 12.75, "B1-BED": 31.5, "B1-MST": 24.0, "B1-STR": 18.24},
            # 0.30 ring 39.2; 0.20 as GF 13.8; 0.15: y 2.925 clear 5.0
            "walls": {"0.30": {"gross_lm": 39.2, "openings_lm": 1.5 + 0.6 + 2.0 + 1.5 + 1.0},
                      "0.20": {"gross_lm": 13.8, "openings_lm": 0.9 + 0.9},
                      "0.15": {"gross_lm": 5.0, "openings_lm": 0.8}},
            "counts": {"DOOR": 3, "WINDOW": 5, "PASSAGE": 0, "rooms": 4, "wet": 1},
        },
    },
    "SV-C": {"GF": {
        # outer: 12.2 x 10.2 less the corner square 2.2^2 plus the quarter disc pi 2.2^2 / 4
        "outer_m2": 12.2 * 10.2 - 2.2 ** 2 * (1 - PI / 4),
        # living: 11.8 x 5.8 - the bedroom block 7.0 x 3.0 - the corner 2.0^2 (1 - pi / 4)
        "rooms_m2": {"C-KIT": 18.24, "C-DIN": 14.44, "C-BTH": 11.02, "C-BED": 19.04,
                     "C-LIV": 11.8 * 5.8 - 7.0 * 3.0 - 4.0 * (1 - PI / 4)},
        # 0.20: centreline ring 2 x (12.0 + 10.0) - 2 x 2.1 + the quarter arc (pi / 2) 2.1; partitions y 4.1 clear
        # 11.8, x 5.1 clear 3.8, y 7.1 clear 7.0, x 7.1 clear 2.8; 0.10: x 9.05 clear 3.8
        "walls": {"0.20": {"gross_lm": 44.0 - 4.2 + PI / 2 * 2.1 + 11.8 + 3.8 + 7.0 + 2.8,
                           "openings_lm": 1.0 + 0.9 + 0.9 + 0.8 + 0.9 + 1.5 + 1.5 + 0.6 + 1.5 + 2.0},
                  "0.10": {"gross_lm": 3.8, "openings_lm": 0.0}},
        "curved_wall": {"thickness_m": 0.2, "centreline_r_m": 2.1, "sweep_deg": 90.0,
                        "centreline_lm": PI / 2 * 2.1},
        "counts": {"DOOR": 5, "WINDOW": 5, "PASSAGE": 0, "rooms": 5, "wet": 1, "unlabelled": 1},
    }},
}
