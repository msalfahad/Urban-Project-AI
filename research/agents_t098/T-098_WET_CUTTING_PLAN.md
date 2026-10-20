# T-098: wet-area membrane cutting plans by hand, each room alone (Alsenan, development villa)

Worker 2, 2026-10-20 06:35-07:30 UTC. NO REPO CODE run: the code self-check was refused by the session permission
check ("Permission for this action was denied by the Claude Code auto mode classifier. Reason: [Code from External]."
on clone + venv), so no engine module, test or tool of the repository was run. Hand reading of the drawing and hand
calculation only, with my own scratch helpers (a DXF text reader, a 1 mm raster for the coverage check, an exact
slab clip for strip lengths, an exhaustive roll packer). Development villa, NOT an accuracy claim. Dimensions, strips
and roll positions only: no coordinates, no client data.

Sources (Drive "Alsenan chalet project", read-only): P7757_DXF_COMPRESSED.zip (P7757.dxf, sha256 ab54dd55...,
same file as T-074 / T-089) for every outline; p7757_arch_sheet03.pdf (ground floor) and p7757_arch_sheet04.pdf
(first floor) for the printed sizes (second reading). Engine figures: the released V2.11 per-room choice as printed
by the merged T-089 cutting-plan run (research/agents_t089/ALSENAN_CUTTING_PLANS.txt), 17 areas 19 rolls 122.99 m.

Rules used and nothing else: UP-WP-001 (roll 1.00 x 10.00 m, whole strips), UP-WP-002 (0.10 m lap), UP-WP-003 and
owner Q-03 / Q-30 (0.20 m upturn folded from the same strip; first strip covers 0.80 m of floor, each next full strip
0.90 m, the last strip cut to remaining floor + lap + upturn; strip length = floor run + 0.20 + 0.20), Q-35 C (strips
0.20 m longer at both ends whatever sits in the wall: doorways and open edges included), Q-37 A (pantry inside its
printed 4.50 x 3.00 with the upturn on all four sides), Q-40 A (no extra shower height), Q-49 A (each room alone, the
layout with the fewest rolls, tie: shorter strip metres), Q-58 (open: both outcomes shown), UP-QTY-STATUS-001.

## 1. Outlines (second reading on the printed sheets)

All 17 wet areas and the pantry were re-traced from the wall-face lines (layer `1`), the column outlines and the door
jambs, and checked against the printed sizes on sheets 03 / 04: 150 x 210, 150 x 225, 130 x 150, kitchen 300 x 270
+ 105 x 150 (450 overall), pantry 300 x 450, 135 x 175, 110 x 135, wedge W.C.s 289 x 167 and 245 x 167, core lobby
205 with the 132 diagonal, 210 (master bath), 245 x 205 (twice), laundry 185 / 300 / 347 / 305, 147 x 180, 210 x 225:
all agree. Column notches read from the drawing: wash by the dewaneya 0.35 x 0.05, kitchen piers 0.05 x 0.40 and
0.05 x 0.50, wedge W.C. 245 x 167 corner 0.58 x 0.05, bathroom by the laundry 0.45 x 0.05, laundry passage 0.05 x 0.80.
Floor 72.121 m2 and boundary 144.727 lm for the 17 areas = T-074 hand table (72.122 / 144.729) and the engine
(72.12): the outlines are the same.

## 2. Method of the hand layout (per room, each alone)

- Every room laid in both strip directions of its own wall frame (along and across the longest wall) and from both
  start walls; a room with 45 degree walls (the two wedge W.C.s, the core lobby, the master bath) also in the 45 degree
  frame, both directions, both start walls: 4 layouts per rectangular room, 8 per room with 45 degree walls.
- Strip length = the floor's extent inside the strip's band (exact slab clip of the outline) + 0.20 + 0.20; the last
  band takes the remaining floor + lap + upturn; a band left with no floor (span + upturn reaches past the last full
  strip) gets the upturn-only strip at the far wall, as the owner's count does.
- Coverage check (no assumption taken as proof): the developed surface (floor + a 0.20 m flap outward of every edge,
  wall, door or open edge alike) against the union of the strips, on a 1 mm raster (sheets grown 2 mm for raster edge
  noise; pieces under 1 cm2 ignored).
- Rolls: the strip lengths packed into 10 m rolls by exhaustive search (no piece across two rolls); lower bound
  L1 = ceil(strip metres / 10).
- Method fixtures (synthetic, not Alsenan): the owner's 3 x 4 kitchen gives 4 strips 1.00 / 1.00 / 1.00 / 0.70 x 4.40,
  16.28 m2 cut, 17.60 m, 2 rolls (his figures); across: 5 x 3.40 = 17.00 m, 3 rolls by length; the same kitchen turned
  37 degrees and mirrored: identical; an L outline whose step edge runs parallel to the strips exactly at a band edge
  (6 x 2.5 + 2 x 1.5) reproduces the T-094 roof defect: 3.80 x 0.10 = 0.38 m2 of upturn unreached in one start
  wall, 0 from the other; a 3 m right triangle shows 3 corner triangles of 0.0034 m2 (section 4).

## 3. Result per room: hand vs released engine (V2.11)

| Area | Floor m2 | Hand layout (fewest rolls, tie shorter m) | Hand strips (w x L, m) | Hand rolls / m / left | Engine rolls / m | Diff m | Verdict |
|---|---|---|---|---|---|---|---|
| GF wash by the dewaneya | 3.1325 | along the 2.10 wall | 1.00x2.50 + 1.00x2.50 | 1 / 5.00 / 5.00 | 1 / 5.00 | 0 | ENGINE_RIGHT |
| GF W.C. by the dewaneya | 3.3750 | along the 2.25 wall | 1.00x2.65 x 2 | 1 / 5.30 / 4.70 | 1 / 5.30 | 0 | ENGINE_RIGHT |
| GF W.C. of the driver | 1.9500 | across the 1.50 wall | 1.00x1.70 x 2 | 1 / 3.40 / 6.60 | 1 / 3.40 | 0 | ENGINE_RIGHT |
| GF kitchen | 9.6300 | across the 3.00 wall, from the far wall | 1.00x3.10 x 4 + 1.00x1.45 + 0.40x1.45 | 2 / 15.30 / 4.70 | 2 / 15.30 | 0 | ENGINE_RIGHT |
| GF W.C. stair core | 2.3625 | along the 1.75 wall | 1.00x2.15 + 0.85x2.15 | 1 / 4.30 / 5.70 | 1 / 4.30 | 0 | ENGINE_RIGHT |
| GF basin space by the stair | 1.4850 | across the 1.35 wall | 1.00x1.50 + 0.85x1.50 | 1 / 3.00 / 7.00 | 1 / 3.00 | 0 | ENGINE_RIGHT |
| GF W.C. wedge 289 x 167 | 2.6753 | parallel to the 1.73 m 45 deg wall (door wall) | 1.00x2.44 + 1.00x1.96 + 0.96x1.05 | 1 / 5.45 / 4.55 | 1 / 5.95 | -0.50 | HAND_RIGHT on metres, rolls equal |
| GF W.C. wedge 245 x 167 | 2.3677 | across the 2.36 m 45 deg wall | 1.00x2.10 + 1.00x1.89 + 0.96x1.06 | 1 / 5.06 / 4.94 | 1 / 5.06 | 0 | ENGINE_RIGHT |
| GF core wash lobby | 4.7306 | parallel to the 1.32 m 45 deg wall | 1.00x1.72 + 1.00x2.08 + 1.00x2.45 + 1.00x1.91 + 0.31x0.43 | 1 / 8.59 / 1.41 | 1 / 8.59 | 0 | ENGINE_RIGHT |
| GF master bath | 3.7177 | across the 2.10 wall | 1.00x2.40 x 2 + 0.70x1.82 | 1 / 6.62 / 3.38 | 1 / 6.62 | 0 | ENGINE_RIGHT |
| 1F bath west (upper) | 5.0225 | along the 2.45 wall | 1.00x2.85 x 2 + 0.65x2.85 | 1 / 8.55 / 1.45 | 1 / 8.55 | 0 | ENGINE_RIGHT |
| 1F bath west (lower) | 5.0225 | along the 2.45 wall | 1.00x2.85 x 2 + 0.65x2.85 | 1 / 8.55 / 1.45 | 1 / 8.55 | 0 | ENGINE_RIGHT |
| 1F laundry | 10.1510 | across the 3.05 wall, from the far wall | 1.00x2.25 x 2 + 1.00x3.87 x 2 + 1.00x1.87 + 0.90x1.82 | 2 / 15.93 / 4.07 | 2 / 15.93 | 0 | ENGINE_RIGHT |
| 1F W.C. by the laundry | 2.6460 | along the 1.80 wall | 1.00x2.20 + 0.97x2.20 | 1 / 4.40 / 5.60 | 1 / 4.40 | 0 | ENGINE_RIGHT |
| 1F bath by the laundry | 3.5775 | across the 2.00 wall | 1.00x2.20 x 2 + 0.60x2.15 | 1 / 6.55 / 3.45 | 1 / 6.55 | 0 | ENGINE_RIGHT |
| 1F bath east | 4.7250 | across the 2.25 wall | 1.00x2.50 x 2 + 0.85x2.50 | 1 / 7.50 / 2.50 | 1 / 7.50 | 0 | ENGINE_RIGHT |
| 2F W.C. roof floor | 5.5500 | across the 3.00 wall | 1.00x2.25 x 3 + 0.70x2.25 | 1 / 9.00 / 1.00 | 1 / 9.00 | 0 | ENGINE_RIGHT |
| **17 wet areas** | **72.121** | | cut 116.005 m2, side trim 6.494 m2 | **19 / 122.50 / 67.50** | **19 / 122.99** | **-0.49 m (-0.4 %)** | rolls confirmed |
| GF pantry (Q-37 A) | 13.5000 | along the 4.50 wall | 1.00x4.90 x 3 + 0.70x4.90 | 2 / 19.60 / 0.40 | 2 / 19.60 | 0 | ENGINE_RIGHT |
| **with the pantry** | **85.621** | | | **21 / 142.10 / 67.90** | **21 / 142.59** | -0.49 m | |

Roll positions (where each strip is cut from its roll) and all 4 or 8 layouts per room are in WET_CUTTING_PLAN.csv.
Every room is at its lower bound L1 (the strips need no more rolls than their metres): the 19 is proven, not a
packing artefact. No strip is longer than 4.90 m, so no wet room needs a splice.

The one difference: on the 289 x 167 wedge W.C. the hand layout runs the strips parallel to the 1.73 m wall with the
door (45 degrees to the room's longest wall): 2.44 + 1.96 + 1.05 = 5.45 m. Hand check from the drawing: across that
direction the room spans 2.355 m (from the door wall to the far corner), so 3 bands (1.00, 1.00, 0.955 m); the long
diagonal wall is perpendicular to the strips, so every strip ends on it, and the other end runs along the 2.887 m
wall at 45 degrees: floor runs 2.042, 1.555 and 0.655 m, + 0.40 each = 2.442 + 1.955 + 1.055 = 5.452 m. The engine
selects only among its longest-wall frame (2.887 m wall: best 3.29 + 2.13 + 0.27 x 0.53 = 5.95 m); the 45 degree frame is
printed as "other frames" but never selected, although Q-49 A asks for the fewest-roll layout with the shorter metres.
Effect: same 1 roll, 0.50 m less strip, 0.50 m more leftover. On the 245 x 167 wedge and the lobby the engine's own
frame already is the 45 degree one (its ring splits the longest straight wall at a column / zone vertex), so they agree.

## 4. Every piece the strips do not reach (owner Q-58)

| Area (best hand layout) | Pieces | Size | Where and why |
|---|---|---|---|
| GF W.C. wedge 289 x 167 | 2 | right triangles, legs 0.083 m, 0.0034 m2 each (0.0069 m2) | at the square-cut strip ends on the 2.887 m wall, which runs at 45 deg to the strips, one at each of its 2 band boundaries |
| GF W.C. wedge 245 x 167 | 2 | same (0.0069 m2) | strip ends on the 1.87 m outside wall and the 0.58 m column face, which run at 45 deg to these strips (strips parallel to the 1.10 m door wall) |
| GF core wash lobby | 3 | same (0.0103 m2) | strip ends on the 2.05 m bottom edge (open edge to the stair hall + wall) (2) and the 0.84 m wall (1), which run at 45 deg to these strips (strips parallel to the 1.32 m wall) |
| GF master bath | 1 | same (0.0034 m2) | strip end on the 1.39 m diagonal wall (0.982 x 0.982) |
| the other 13 areas and the pantry | 0 | - | every edge reached in every layout (doorways, open edges, column notches, the kitchen piers, the laundry steps) |

Cause (geometry, every villa): where a wall runs at 45 degrees to the strips, the 0.20 m upturn folded up that wall
reaches sqrt(2) x 0.20 = 0.283 m past the floor corner measured along the strip, while the strip is cut square at
0.20 m past the floor's furthest point in its band; at each band boundary this leaves a right triangle with legs
(sqrt(2) - 1) x 0.20 = 0.083 m, area 0.0034 m2. These are the engine's own "0.003 - 0.010 m2 unreached in four ground-floor
wet areas" (its layouts give 0.0069, 0.0069, 0.0103, 0.0034 m2: the same four rooms, the same count). They are NOT the
roof defect of T-094/T-096 (an upturn of a step edge parallel to the strips with no strip at all): that case does not
occur in any wet area in any layout (checked on all 4 / 8 layouts per room).

Q-58 does not move the wet-area rolls: under A (patch from the room's own offcut: these four rooms have 1.41 - 4.94 m
left on their roll) the counts stay as in section 3; under B (every piece from a roll as full-width strip) the strip
ends on the 45 degree walls are cut 0.083 m longer: checked with ALL strip ends of the four rooms lengthened 0.083 m
(upper bound): uncovered 0 and still 1 roll each (5.95 / 5.55 / 9.22 / 7.12 m); under C (corner accessory) no membrane
is added. So the wet areas stay 19 rolls (21 with the pantry) whatever Q-58 answer; only the strip metres move by at
most +2.1 m (upper bound, 0.50 + 0.50 + 0.62 + 0.50) under B. The wet part of Q-58 needs no hold.

## 5. Against the freelancer

His waterproofing rows give floor m2 and boundary lm only (no strips, no rolls), so rolls cannot be compared.
Floor 72.12 hand vs 72.01 m2 freelancer (+0.11 m2, +0.16 %), boundary 144.73 vs 144.61 lm (+0.08 %), unchanged from
T-074. Rolls to buy: hand 19 (17 areas, each alone, Q-49 A) = engine 19; freelancer: none given.

## 6. What this means for the team

- Wet areas: released V2.11 count 19 rolls CONFIRMED by an independent hand layout of every room; strip metres
  122.99 -> 122.50 m (-0.49 m, -0.4 %) and leftover 67.01 -> 67.50 m once the 45 degree frame is selectable. With the
  pantry 21 rolls, 142.10 m, 67.90 m left (engine 142.59 / 67.41).
- Engine gap (general, every villa): MEMBRANE_FOLD_V2 computes the other wall frames of a room with 45 degree walls but
  never selects them for the cutting plan; Q-49 A asks for the fewest-roll, shorter-metre layout over all layouts.
  Proposed fix (small, next to T-096): include the other_frames layouts in the per-room choice. Alsenan effect: -0.50 m,
  rolls unchanged.
- The T-094 roof defect (step edge parallel to the strips) does not occur in the 17 wet areas or the pantry: T-096 can
  take this table as its wet-area non-regression truth (every room: rolls, metres and 0 uncovered beyond the 45 degree
  corner triangles).
- The corner triangles are a fixed geometric fact of square-cut strips against 45 degree walls (0.0034 m2 each with the
  owner's 0.20 m upturn); they never change a roll count while a roll has 0.083 m to spare per strip end.
- Lead note: the Q-49 text says the owner's kitchen laid across takes "6 strips of 3.40 m"; his method gives 5 strips
  (1.00 x 4 + 0.80) x 3.40 = 17.00 m, 3 rolls by length; the conclusion (3 rolls) is unchanged.
- Missing: nothing for the wet areas. Corner reinforcement and drain detailing remain outside the owner's method.
- Not done in this run (execution refused): docs/CODEMAP.md was not regenerated for the 2 new research files; the
  verifier rebuilds it with `python3 -I tools/codemap.py build` (map-only change) and runs the freeze check.

Files: WET_CUTTING_PLAN.csv (one row per area: outline size, chosen layout, every strip, roll positions, rolls, L1,
metres, leftover, cut, side trim, uncovered pieces, engine figures, verdict, all layouts), this write-up.
