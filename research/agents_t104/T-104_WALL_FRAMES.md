# T-104: membrane strips laid in every wall frame of an area (MEMBRANE_FOLD_V4)

Worker 3, 2026-10-20. Opt-in piece, read by no released method (the released ARCH_TAKEOFF_V2.12 figures do not move).
Development villa figures below are a check, not an accuracy claim. Lengths, counts and engine room ids only.

## What changed and why

MEMBRANE_FOLD_V2 / V3 lay strips only along and across an area's LONGEST wall (4 layouts: 2 directions x 2 start walls).
Owner Q-49 A asks for the layout with the fewest whole rolls (tie: shorter strip metres) with no restriction to one wall.
A room with a 45 degree wall (wedge W.C., chamfered lobby, trapezoid) can need fewer metres, or fewer rolls, laid
parallel / square to its other wall. T-098's hand plan found this on one Alsenan wedge W.C. (5.45 vs 5.95 m).

`engine/source/membrane_fold_v4.py` (new; V2, V3 and MEMBRANE_CUTTING_PLAN_V2 untouched):
- frames: every distinct edge direction of the outline and its holes (V2's 0.5 degree classes, mod 90), each turned at
  the exact angle of its own longest edge; the longest-wall frame first and laid exactly as V3 (tested: same 4 layouts);
  no length / share filter (a filter would be an assumption; Q-49 A chooses).
- per frame V3's 4 layouts (main strips, upturn-only strips, patches, coverage check = 0, the three owner Q-58 counts).
- choice per Q-58 reading: fewest rolls, then shorter strip metres, then smaller cut m2, then listed order. Same count
  under A / B / C -> RELEASED; else HELD_Q58 with low / high (never 0). The V3 choice and what V4 saves are shown beside.
- patches typed: a triangle (3 corners after V2's clean_ring) is CORNER_TRIANGLE with its sides (0.083 / 0.083 / 0.117 m
  at a 45 degree wall; the mitred 45 degree acute corner 0.283 / 0.283 / 0.400 m); other pieces PIECE.
- V3 defect found and corrected inside V4 (V3 not edited): V3 takes a patch's size from the bounds of the raw residual;
  where a sheet edge lies on the upturn's outer line shapely leaves a 5e-17 m wide tail, so a 0.04 m2 corner triangle
  (0.283 x 0.283 m) was listed 3.08 m long and Q-58 A / B cut it as a 3.08 m piece (+1 roll in that layout). V4 measures
  each patch on the residual snapped to V2's EPS grid (1e-9 m): same pieces, same m2, true size. On Alsenan it moved no
  chosen layout; flagged V3_PATCH_SIZE_TAIL_CLEANED / V3_COUNT_CORRECTED_IN_ITS_OWN_FRAME when it moves a count.

## Hand fixtures (not Alsenan; tests/t104_wall_frames, 36 tests)

| Fixture | V3 (longest-wall frame) | V4 (every frame) | Hand |
|---|---|---|---|
| owner's kitchen 4.00 x 3.00 | 2 rolls, 17.60 m | 2 rolls, 17.60 m (one frame) | 4 x 4.40 (1.00/1.00/1.00/0.70) |
| wedge (0,0)(2.40,0)(0.60,1.80)(0,1.80), longest wall the 45 deg one | 1 roll, 6.1581 m (3.3698 + 2.1941 + 0.5941) | 1 roll, 5.30 m (2.20 + 2.00 + 1.10), -0.8581 m | each strip by band clipping, docstring |
| trapezoid (0,0)(3.50,0)(1.00,2.50)(0,2.50) | 2 rolls every reading, 10.7441 m | 9.80 m: Q-58 A 1, B 2, C 1 -> HELD_Q58 low 1 / high 2 | 2.90 + 2.90 + 2.20 + 1.30 + 0.50; patches 0.283 + 2 x 0.083 m long; 9.80 + 0.4485 > 10 under B |
| wedge, V3's own frame, layout from the opposite corner | V3 counts A 2 / B 2 / C 1 (tail defect) | 1 / 1 / 1 | 8.4125 + 0.283 + 2 x 0.117 = 8.93 m |

Adversarial: millimetres (unit 0.001), mirrored, rotated 30 / -63 deg, other start vertex: same choice, same counts.
A column hole at 45 deg adds its frame. Held, never 0: no outline, missing lap, lap >= roll width, collinear points,
self-crossing outline. Never worse than V3 under any reading (5 outlines); every cutting plan re-packs to its count.

## Alsenan (Drive "Alsenan chalet project", P7757 DXF sha ab54dd55..., run research/agents_t104/alsenan_v4_run.py)

| Area | V3 (released V2.12) | V4 | Hand (T-098) | Verdict |
|---|---|---|---|---|
| GF W.C. wedge 289 x 167 (GF-RF38DAF) | 1 roll, 5.9489 m | 1 roll, 5.4521 m: 1.00 x 2.4416 + 1.00 x 1.9552 + 0.955 x 1.0552, strips parallel to the 1.73 m 45 deg door wall | 1 roll, 2.442 + 1.955 + 1.055 = 5.452 m | ENGINE_RIGHT (V4 = hand strip by strip) |
| the other 16 wet areas | 18 rolls | unchanged (same layout, same metres) | = V3 | unchanged |
| 17 wet areas | 19 rolls, 123.04 m | 19 rolls, 122.55 m (-0.50 m, -0.4 %), 67.45 m of roll left (65.81 m after cutting the patches, Q-58 B) | 19 rolls, 122.50 m | rolls confirmed; the 0.05 m left is the 1F bath by the laundry, 6.60 (V3, T-096: a 0.15 m step upturn needs its own strip) vs 6.55 m by hand, already verified at T-096 merge |
| 1F roofs (2) | 6 + 8 rolls, 49.80 + 76.35 m | unchanged | 6 + 8 (T-094) | unchanged |
| 2F roof (held under Q-58 / Q-34) | A 17 / B 18 / C 18, 162.69 m | A 17 / B 18 / C 18, 162.21 m (-0.48 m) in a frame at 91.69 deg | not measured | rolls unchanged; see note |

Freelancer: his waterproofing rows give floor m2 and boundary lm only, no strips or rolls: floor 72.12 vs 72.01 m2
(+0.16 %), unchanged; rolls cannot be compared.

Note for the Lead (2F roof): the roof outline has 108 edge directions (curved parts drawn as chords); V4 tries all
(432 layouts; the whole read-only run takes 170 s) and its tie-break picks a frame 1.69 deg off the straight walls,
saving 0.48 m of strip at the same 17 / 18 rolls. Q-49 A allows it (fewest rolls, then shorter metres); whether a
skewed layout set from a curve's chord is acceptable on site is not settled by any Urban rule. It moves no count and the
roof is already held, so no owner question was added; if the layout is wired for roofs, the Lead may want one (options:
every edge direction / only straight walls of at least V2's 1 m and 10 % / owner chooses per roof).

## What is missing

- Not wired: no released method reads V4 (wiring = a new ARCH_TAKEOFF version reading `purchase`).
- Q-58 still open: the trapezoid fixture shows a case where another frame changes the count only under A / C.
