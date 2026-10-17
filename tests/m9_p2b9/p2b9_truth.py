"""Phase 2B-9 hand truth for the worked examples (p2b9_fixtures). Every value is arithmetic on the construction
situation (the coordinates and the stated heights), written out step by step - nothing is read from the engine.

Conventions (the established owner rules, cited):
    wall finish  gross = the room's whole boundary run (openings included) x the finish height; each opening
                 deducted by its own rectangle inside the finish band: width x (min(head, H) - max(sill, 0))
                 (UP-CER-009 / F-24); a reveal is never inside the main wall-face area
    paint        to the finished ceiling (URBAN-PAINT-TO-FINISHED-CEILING); plaster to the structural soffit
    door jamb    2 jambs x wall thickness x door height + head soffit x wall thickness x opening width,
                 PROVISIONAL (the frame detail decides how much is plastered; UP-FIN-PLASTER-001)
    window       reveal depth = the distance from the room's wall face to the glazing line (actual geometry);
    reveal       the jambs (2 x depth x window height) and the head soffit (depth x width, only where wall remains
                 above the window inside the finish height) are plaster (UP-REF-REVEAL-001: plaster by default);
                 the internal sill surface (depth x width) is its own item (marble / plaster by the window detail);
                 for floor-level glazing the strip between the wall face and the glazing is FLOOR, not sill
    skirting     the room boundary - door / passage openings - floor-level glazing (a sill window is skirted);
                 none where the wall tile is full height (UP-CER-004 / UP-FIN-WALL-001)
    waterproofing  the Phase 2B-3 WP-B proof (research/urban_m9_p2b3/WP2_BATHROOM_3x4_PROOF.md)
"""

from __future__ import annotations

import math

H = 3.00                    # the finished-ceiling and structural-soffit height of the examples' section (m)
T = 0.20                    # every wall's thickness
DOOR_H = 2.20               # D1 in the schedule: 1000 x 2200 mm

# --------------------------------------------------------------------------------------- Example 1 (sill window)
E1_L, E1_B = 4.00, 3.00
E1_PERIM = 2 * (E1_L + E1_B)                          # 14.00 m
E1_GROSS = E1_PERIM * H                               # 42.00 m2
E1_DOOR_W = 1.00
E1_DOOR_A = E1_DOOR_W * DOOR_H                        # 2.20 m2
E1_WIN_W, E1_WIN_H, E1_SILL = 1.50, 1.20, 1.00        # W1 1500 x 1200, sill 1000
E1_WIN_A = E1_WIN_W * E1_WIN_H                        # 1.80 m2 (head 2.20 <= 3.00: the whole rectangle)
E1_NET = E1_GROSS - E1_DOOR_A - E1_WIN_A              # 38.00 m2: the main wall face (plaster and paint)
E1_REVEAL_D = 0.10                                    # inner face y 3.20 m to the glazing line y 3.30 m
E1_REVEAL_JAMBS = 2 * E1_REVEAL_D * E1_WIN_H          # 0.24 m2
E1_REVEAL_HEAD = E1_REVEAL_D * E1_WIN_W               # 0.15 m2 (wall above the head: 3.00 - 2.20 = 0.80 m)
E1_REVEAL_PLASTER = E1_REVEAL_JAMBS + E1_REVEAL_HEAD  # 0.39 m2 - its own line, never inside the 38.00
E1_SILL_SURFACE = E1_REVEAL_D * E1_WIN_W              # 0.15 m2 - the internal sill, its own item
E1_DOOR_JAMB_PLASTER = 2 * T * DOOR_H + T * E1_DOOR_W  # 0.88 + 0.20 = 1.08 m2 (PROVISIONAL)
E1_SKIRTING = E1_PERIM - E1_DOOR_W                    # 13.00 m (the sill window is skirted under its sill)
E1_FLOOR = E1_L * E1_B                                # 12.00 m2
E1_ABOVE_WINDOW_WALL = E1_WIN_W * (H - (E1_SILL + E1_WIN_H))   # 1.20 m2 (inside the 38.00, not a reveal)
E1_BELOW_SILL_WALL = E1_WIN_W * E1_SILL               # 1.50 m2 (inside the 38.00)

# ------------------------------------------------------------- Example 1 height variants (the trade's own height)
# paint runs to the finished ceiling, plaster to the structural soffit (U/S SLAB +3.00 in every section variant)
E1_PAINT_AT_280 = E1_PERIM * 2.80 - E1_DOOR_A - E1_WIN_A       # 39.20 - 2.20 - 1.80 = 35.20 m2 (head 2.20 < 2.80)
E1_PAINT_AT_270 = E1_PERIM * 2.70 - E1_DOOR_A - E1_WIN_A       # 37.80 - 2.20 - 1.80 = 33.80 m2 (C.H. 2.70 note)
# the sill tag SILL 0.90 governs the schedule's 1.00: head 0.90 + 1.20 = 2.10 <= 3.00, the deduction is unchanged
E1_SILL_TAG = 0.90
E1_SILL_TAG_HEAD = E1_SILL_TAG + E1_WIN_H                      # 2.10 m
E1_SILL_TAG_BELOW_SILL_WALL = E1_WIN_W * E1_SILL_TAG           # 1.35 m2 (inside the 38.00)
# no window height / sill (no schedule): the window's deduction is unknown inside [0, H] -> a range
E1_UNKNOWN_WIN_LOW = E1_GROSS - E1_DOOR_A - E1_WIN_W * H       # 42.00 - 2.20 - 4.50 = 35.30 m2 (full height)
E1_UNKNOWN_WIN_HIGH = E1_GROSS - E1_DOOR_A                     # 39.80 m2 (nothing deducted)
E1_UNKNOWN_SILL_SKIRTING = E1_PERIM - E1_DOOR_W - E1_WIN_W     # 11.50 m certain (no reading skirts less)
E1_UNKNOWN_SILL_SKIRTING_RANGE = (0.0, E1_WIN_W)               # + 0 .. 1.50 m (sill window: skirted; glazing: not)

# a window whose head rises above the finished ceiling (W1 1.50 x 1.90 sill 1.00 -> head 2.90) under F.C.L. +2.80 and
# U/S SLAB +3.00: each trade deducts only the window's part inside its own band, min(head, H) - max(sill, 0)
E1_CLIP_WIN_H = 1.90
E1_CLIP_HEAD = E1_SILL + E1_CLIP_WIN_H                         # 2.90 m
E1_CLIP_PLASTER = E1_PERIM * 3.00 - E1_DOOR_A - E1_WIN_W * (min(E1_CLIP_HEAD, 3.00) - E1_SILL)   # 42.00-2.20-2.85
E1_CLIP_PAINT = E1_PERIM * 2.80 - E1_DOOR_A - E1_WIN_W * (min(E1_CLIP_HEAD, 2.80) - E1_SILL)     # 39.20-2.20-2.70
E1_CLIP_REVEALS = 2 * E1_REVEAL_D * E1_CLIP_WIN_H + E1_REVEAL_D * E1_WIN_W     # 0.38 + 0.15 (wall above to 3.00)

# ------------------------------------------------------------------------- Example 1 variant: floor-to-ceiling glazing
E1F_WIN_H, E1F_SILL = 3.00, 0.00                      # W2 1500 x 3000, sill 0
E1F_WIN_A = E1_WIN_W * E1F_WIN_H                      # 4.50 m2
E1F_NET = E1_GROSS - E1_DOOR_A - E1F_WIN_A            # 42.00 - 2.20 - 4.50 = 35.30 m2
E1F_SKIRTING = E1_PERIM - E1_DOOR_W - E1_WIN_W        # 14.00 - 1.00 - 1.50 = 11.50 m (no skirting at the glazing)
E1F_REVEAL_JAMBS = 2 * E1_REVEAL_D * E1F_WIN_H        # 0.60 m2
E1F_REVEAL_HEAD = 0.0                                 # head = 3.00 = the ceiling: no wall above, no head soffit
E1F_REVEAL_PLASTER = E1F_REVEAL_JAMBS + E1F_REVEAL_HEAD   # 0.60 m2
E1F_FLOOR_STRIP = E1_REVEAL_D * E1_WIN_W              # 0.15 m2: the strip to the glazing is FLOOR (no sill)
E1F_SILL_SURFACE = 0.0

# ------------------------------------------------------------------------------------------ Example 2 (wet room)
E2_FLOOR = 4.00 * 3.00                                # 12.00 m2 (wet floor tile; membrane floor)
E2_PERIM = 2 * (4.00 + 3.00)                          # 14.00 m
E2_DOOR_W = 1.00
E2_DOOR_A = E2_DOOR_W * DOOR_H                        # 2.20 m2
E2_TILE_H = H                                         # full height to the finished ceiling (UP-FIN-WALL-001)
E2_WALL_TILE = E2_PERIM * E2_TILE_H - E2_DOOR_A       # 42.00 - 2.20 = 39.80 m2
E2_PLASTER = E2_PERIM * H - E2_DOOR_A                 # 39.80 m2: the substrate behind the porcelain (soffit 3.00)
E2_PAINT = 0.0                                        # no paint over full-height porcelain (UP-FIN-PAINT-001)
E2_SKIRTING = 0.0                                     # none: the wall tile is full height (UP-CER-004)
E2_WP_UPTURN_RUN = E2_PERIM - E2_DOOR_W               # 13.00 m (the doorway is not a wall)
E2_WP_UPTURN = E2_WP_UPTURN_RUN * 0.20                # 2.60 m2 (UP-WP-003)
E2_WP_DOORWAY = E2_DOOR_W * T                         # 0.20 m2 (UP-WP-DOOR-001: door width x wall depth)
E2_WP_SUBTOTAL = E2_FLOOR + E2_WP_UPTURN + E2_WP_DOORWAY   # 14.80 m2 proven geometric subtotal
# the WP-B cutting plan (Phase 2B-3, strip by strip): 5 strips ALONG_Y of 3.00 m, band segment 2.80 m
E2_WP_LAPS = 4 * 3.00 * 0.10 + 13.00 * 0.10 + 4 * 0.30 * 0.10 + 1.00 * 0.10   # 1.20 + 1.30 + 0.12 + 0.10 = 2.72
E2_WP_INSTALLED = E2_WP_SUBTOTAL + E2_WP_LAPS         # 17.52 m2
E2_WP_CONSUMED = (5 * 3.00 + 2.80) * 1.00             # 17.80 m2
E2_WP_WASTE = E2_WP_CONSUMED - E2_WP_INSTALLED        # 0.28 m2
E2_WP_ROLLS = 2                                       # 17.80 m of a 10.00 m roll, cut as 9.00 + 8.80
E2_WP_REMAINDERS = (10.00 - 9.00) + (10.00 - 8.80)    # 1.00 + 1.20 m of full-width stock
E2_CORNERS = 4                                        # internal corners: treatment WITHHELD (no detail)

# ------------------------------------------------------------------------- Example 3 (collinear stubs, south wall)
# south wall y 0..200: door x 400..1400, window W3 x 1650..3950; the wall between them on BOTH faces:
E3_STUBS = {"west_return": 0.400 - 0.200, "pier": 1.650 - 1.400, "east_return": 4.200 - 3.950}   # 0.20/0.25/0.25
E3_STUB_LM = sum(E3_STUBS.values())                   # 0.70 m of wall (both faces drawn)
E3_WALL_RUN = 4.00 + 3.00 + 3.00 + E3_STUB_LM          # north + east + west + the stubs = 10.70 m
E3_WIN_W = 2.30
E3_NET = 2 * (4.00 + 3.00) * H - E1_DOOR_W * DOOR_H - E3_WIN_W * 1.20   # 42.00 - 2.20 - 2.76 = 37.04 m2
E3_SKIRTING = 14.00 - E1_DOOR_W                       # 13.00 m (the stubs' faces are in it)

# ------------------------------------------------------------------- Example 3 variant: returns at the door jambs
# returns standing into the room: 0.20 m (x 0.80..1.00, y 0.20..0.40) and 0.35 m (x 2.00..2.20, y 0.20..0.55)
E3R_AREA = 12.00 - 0.20 * 0.20 - 0.20 * 0.35          # 11.89 m2
E3R_PERIM = (0.60 + 0.20 + 0.20 + 0.20) + 1.00 + (0.35 + 0.20 + 0.35) + 2.00 + 3.00 + 4.00 + 3.00   # 15.10 m
E3R_PLASTER = E3R_PERIM * H - E1_DOOR_W * DOOR_H      # 45.30 - 2.20 = 43.10 m2 (every return face plastered)
E3R_SKIRTING = E3R_PERIM - E1_DOOR_W                  # 14.10 m
E3R_RETURNS = {"short_return": 0.20, "long_return": 0.35}
# the wall bands: north 4.00, east 3.00, west 3.00, south 0.60 (x 0.20..0.80) + 2.00 (x 2.20..4.20), the 0.35 return
E3R_WALL_RUN_BANDS_ONLY = 4.00 + 3.00 + 3.00 + 0.60 + 2.00 + 0.35   # 12.95 m: the 0.20 m return is lost
E3R_WALL_RUN = E3R_WALL_RUN_BANDS_ONLY + 0.20         # 13.15 m with the short return measured as wall
E3R_SHORT_RETURN_PLAN_M2 = 0.20 * 0.20                # 0.04 m2 of masonry in plan (0.12 m3 at 3.00 m)

# ------------------------------------------------------------------------------------- Example 4 (curved wall)
R_IN, R_OUT = 3.00, 3.20
R_MID = (R_IN + R_OUT) / 2                            # 3.10 m
QUARTER = math.pi / 2
E4_ARC_INNER = QUARTER * R_IN                         # 4.712389 m (the room side)
E4_ARC_OUTER = QUARTER * R_OUT                        # 5.026548 m (the outside face)
E4_ARC_MID = QUARTER * R_MID                          # 4.869469 m (the centreline: masonry length)
E4_INNER_FACE_AREA = E4_ARC_INNER * H                 # 14.137167 m2
E4_OUTER_FACE_AREA = E4_ARC_OUTER * H                 # 15.079645 m2 (external finish: not in the internal scope)
E4_ARC_PLAN_M2 = (math.pi / 4) * (R_OUT ** 2 - R_IN ** 2)   # 0.973894 m2 = E4_ARC_MID x T
E4_FLOOR = math.pi * R_IN ** 2 / 4                    # 7.068583 m2
E4_PERIM = R_IN + R_IN + E4_ARC_INNER                 # 10.712389 m (3.00 + 3.00 + the inner arc)
E4_PLASTER = E4_PERIM * H - 1.00 * DOOR_H             # 32.137167 - 2.20 = 29.937167 m2
E4_SKIRTING = E4_PERIM - 1.00                         # 9.712389 m
# the straight wall bands: south 1.00 (x 0.20..1.20) + 1.00 (x 2.20..3.20), west 3.00 = 5.00 m
E4_WALL_RUN = 5.00 + E4_ARC_MID                       # 9.869469 m (the curved wall on its centreline)

# ------------------------------------------------- Example 4 variant: a window in the curved wall, two curved stubs
E4S_STUB_RAD = 0.20 / R_IN                            # 0.066667 rad each
E4S_WIN_RAD = QUARTER - 2 * E4S_STUB_RAD              # 1.437463 rad
E4S_STUB_INNER = R_IN * E4S_STUB_RAD                  # 0.20 m each (the room side)
E4S_STUB_MID = R_MID * E4S_STUB_RAD                   # 0.206667 m each (centreline)
E4S_WIN_INNER = R_IN * E4S_WIN_RAD                    # 4.312389 m: the window measured on the room face
E4S_GLAZ_R = 3.10
E4S_REVEAL_STRIP = E4S_WIN_RAD * (E4S_GLAZ_R ** 2 - R_IN ** 2) / 2   # 0.438423 m2 between the face and the glazing
E4S_FLOOR = E4_FLOOR                                  # 7.068583 m2: the strip is not floor (a sill window)
E4S_FLOOR_IF_CLOSED_AT_GLAZING = E4_FLOOR + E4S_REVEAL_STRIP        # 7.507006 m2 (the V2.7.1 reading)
E4S_WALL_RUN_CURVED_STUBS = 2 * E4S_STUB_MID           # 0.413333 m of curved wall the 0.30 m rule drops
