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
