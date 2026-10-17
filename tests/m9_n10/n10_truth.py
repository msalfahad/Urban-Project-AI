"""Phase N10 hand truth for the curved-opening fixtures (n10_fixtures). Every value is arithmetic on the construction
situation (the coordinates and the stated heights), written out step by step - nothing is read from the engine.
Conventions: the Phase 2B-9 ones (tests/m9_p2b9/p2b9_truth.py) - wall finish gross = the room's boundary run x the
finish height, each opening deducted by width x (min(head, H) - max(sill, 0)); a reveal is never inside the main face;
skirting = the boundary - door / passage openings - floor-level glazing (a sill window is skirted); plus, for a curved
opening (UP-OPEN-CURVED-001): the room ends at its OWN wall face (never at the glazing line) and the opening's width on
that room is the arc of that face; the strip between the face and the glazing is the reveal / sill strip.
"""

from __future__ import annotations

import math

H = 3.00                     # F.C.L. +3.00 and U/S SLAB +3.00 (the fixtures' SECTION A-A)
T = 0.20
R_IN, R_OUT, R_GLAZ = 3.00, 3.20, 3.10
QUARTER = math.pi / 2
DOOR1_W, DOOR1_H = 1.00, 2.20                          # D1 in the schedule: 1000 x 2200

# ------------------------------------------------------------------------------------------- the room
FLOOR = QUARTER * R_IN ** 2 / 2                        # 7.068583 m2: the quarter disc inside the inner face (r 3.00)
PERIM = 3.00 + 3.00 + R_IN * QUARTER                   # 10.712389 m: the two straight inner faces + the inner arc
GROSS = PERIM * H                                      # 32.137167 m2

# ------------------------------------------------------------------------------------------- WINDOW (W4)
STUB_RAD = 0.20 / R_IN                                 # 0.066667 rad: a 0.20 m stub on the inner face at each end
WIN_RAD = QUARTER - 2 * STUB_RAD                       # 1.437463 rad
WIN_INNER = R_IN * WIN_RAD                             # 4.312389 m: the window on the room face (ROOM_SIDE_ARC)
WIN_GLAZ = R_GLAZ * WIN_RAD                            # 4.456135 m: the glazing arc (MID_BAND_ARC here)
WIN_OUTER = R_OUT * WIN_RAD                            # 4.599882 m
WIN_CHORD = 2 * R_IN * math.sin(WIN_RAD / 2)           # 3.950583 m: the room-face chord
REVEAL_STRIP = WIN_RAD * (R_GLAZ ** 2 - R_IN ** 2) / 2         # 0.438423 m2: face to glazing (the sill surface)
EXTERNAL_STRIP = WIN_RAD * (R_OUT ** 2 - R_GLAZ ** 2) / 2      # 0.452795 m2: glazing to the outer face
FLOOR_IF_CLOSED_AT_GLAZING = FLOOR + REVEAL_STRIP      # 7.507006 m2: the V2.8 reading with roles declared (D-P9-02)
REVEAL_DEPTH = R_GLAZ - R_IN                           # 0.10 m (radial)
W4_H, W4_SILL = 1.20, 1.00                             # W4 4312 x 1200, sill 1000 (head 2.20 <= 3.00)
W4_DEDUCT = WIN_INNER * W4_H                           # 5.174867 m2
W4_PLASTER = GROSS - DOOR1_W * DOOR1_H - W4_DEDUCT     # 32.137167 - 2.20 - 5.174867 = 24.762300 m2 (paint the same)
W4_SKIRTING = PERIM - DOOR1_W                          # 9.712389 m (the sill window is skirted under its sill)
W4_REVEAL_JAMBS = 2 * REVEAL_DEPTH * W4_H              # 0.24 m2
W4_REVEAL_HEAD = REVEAL_STRIP                          # 0.438423 m2: the curved head soffit is the strip itself
W4_REVEAL_PLASTER = W4_REVEAL_JAMBS + W4_REVEAL_HEAD   # 0.678423 m2
# no window height (no W4 row / tag): the deduction is unknown inside [0, H]
W4_UNKNOWN_LOW = GROSS - DOOR1_W * DOOR1_H - WIN_INNER * H     # 17.000000 m2
W4_UNKNOWN_HIGH = GROSS - DOOR1_W * DOOR1_H                    # 29.937167 m2
W4_UNKNOWN_SKIRTING = PERIM - DOOR1_W - WIN_INNER              # 5.40 m certain + a 0 .. 4.312389 m range

# ------------------------------------------------------------------------------- FLOOR_GLAZING (W5, sill 0)
W5_H = 3.00
W5_PLASTER = GROSS - DOOR1_W * DOOR1_H - WIN_INNER * W5_H      # 17.000000 m2
W5_SKIRTING = PERIM - DOOR1_W - WIN_INNER                      # 5.40 m (no skirting at floor-level glazing)
W5_FLOOR_STRIP = REVEAL_STRIP                                  # 0.438423 m2: the strip to the glazing is floor
W5_REVEAL_PLASTER = 2 * REVEAL_DEPTH * W5_H                    # 0.60 m2 (head = ceiling: no head soffit)

# ------------------------------------------------------------------------------------ DOOR (D2) / PASSAGE
GAP_RAD = 1.00 / R_IN                                  # 0.333333 rad: 1.00 m on the inner face
GAP_INNER = R_IN * GAP_RAD                             # 1.00 m
DOORWAY_STRIP = GAP_RAD * (R_OUT ** 2 - R_IN ** 2) / 2         # 0.206667 m2: the whole wall thickness in the gap
D2_H = 2.20                                            # no D2 row: the owner reference 2.20 m (HEIGHT_ASSUMED)
D2_PLASTER = GROSS - DOOR1_W * DOOR1_H - GAP_INNER * D2_H      # 27.737167 m2
PASSAGE_PLASTER = GROSS - DOOR1_W * DOOR1_H - GAP_INNER * H    # 26.937167 m2 (a passage is deducted full height)
GAP_SKIRTING = PERIM - DOOR1_W - GAP_INNER                     # 8.712389 m

# ------------------------------------------------------------------------------------- masonry (masonry_room)
# Phase 2B-9 example 1: outer 4.40 x 3.40 m, inner 4.00 x 3.00 m, 0.20 m walls; door D1 1.00 m (south), window W1
# 1.50 m (north); SECTION A-A: F.F.L. +-0.00, T.O.S. -0.10, U/S SLAB +3.10, (B.O.B. +2.60)
MAS_T = 0.20
MAS_PLAN = 4.40 * 3.40 - 4.00 * 3.00 - 1.00 * MAS_T - 1.50 * MAS_T     # 2.46 m2 wall mass in plan (gaps are open)
MAS_RUN_EQ = MAS_PLAN / MAS_T                                           # 12.30 m = centreline 14.80 - 1.00 - 1.50
MAS_PANEL = 3.10 - (-0.10)                                              # 3.20 m: T.O.S. to U/S SLAB
MAS_BUILDUP = 0.00 - (-0.10)                                            # 0.10 m: F.F.L. - T.O.S.
MAS_DOOR_IN_PANEL = 2.20 + MAS_BUILDUP                                  # 2.30 m: the door opening stands on the slab
MAS_ABOVE_DOOR = 1.00 * (MAS_PANEL - MAS_DOOR_IN_PANEL)                 # 0.90 m2 of wall over the door
MAS_WIN_WALL = 1.50 * (MAS_PANEL - 1.20)                                # 3.00 m2 of wall below and above the window
MAS_AREA = MAS_RUN_EQ * MAS_PANEL + MAS_ABOVE_DOOR + MAS_WIN_WALL       # 39.36 + 0.90 + 3.00 = 43.26 m2
MAS_AREA_CENTRELINE_CHECK = 2 * (4.20 + 3.20) * MAS_PANEL - 1.00 * MAS_DOOR_IN_PANEL - 1.50 * 1.20   # 43.26 m2 too
MAS_VOLUME = MAS_AREA * MAS_T                                           # 8.652 m3
# with a beam bottom B.O.B. +2.60 (0.50 m below the soffit) and no plan of which walls carry it: a range
MAS_PANEL_BEAM = 2.60 - (-0.10)                                         # 2.70 m
MAS_AREA_LOW = MAS_RUN_EQ * MAS_PANEL_BEAM + 1.00 * (MAS_PANEL_BEAM - MAS_DOOR_IN_PANEL) + \
    1.50 * (MAS_PANEL_BEAM - 1.20)                                      # 33.21 + 0.40 + 2.25 = 35.86 m2
# a 0.15 m partition x 3.00 .. 3.15 between the south and north inner faces: two thickness families, the four 0.20
# corners (4 x 0.20 x 0.20 = 0.16 m2) are not given to a thickness
MAS_PART_T = 0.15
MAS_PART_AREA = (MAS_PART_T * 3.00) / MAS_PART_T * MAS_PANEL            # 3.00 m x 3.20 = 9.60 m2
MAS_PART_VOLUME = MAS_PART_AREA * MAS_PART_T                            # 1.44 m3
MAS_EXT_AREA_WITH_PART = (MAS_PLAN - 4 * MAS_T * MAS_T) / MAS_T * MAS_PANEL + MAS_ABOVE_DOOR + MAS_WIN_WALL  # 40.70
MAS_JUNCTION_VOLUME = 4 * MAS_T * MAS_T * MAS_PANEL                     # 0.512 m3
