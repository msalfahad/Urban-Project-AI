# The 3.60 x 3.00 m wet area: the two door transitions and the pipe sleeve

Room WP-E: inner faces 3.60 x 3.00 m. Door D1 is 0.90 m in the west wall (y 0.60 - 1.50); door D2 is 0.80 m in the
north wall (x 2.40 - 3.20). A PIPE SLEEVE text is anchored at (3.20, 0.40); wall depth at both doors is 0.20 m. The
upturn is 11.50 m in two open runs:
- **run 1 (3.90 m):** from the D2 west jamb, west to the NW corner (2.40), then down to the D1 north jamb;
- **run 2 (7.60 m):** from the D1 south jamb down to the SW corner (0.60), along the south wall to the SE corner (4.20),
  up to the NE corner (7.20), then west to the D2 east jamb.

The V2.5 plan was rebuilt piece by piece (WPE-A1) and every quantity was reproduced (`ENGINE_VS_REBUILD.md`):
- consumed 16.54 m2, installed 15.75 m2;
- laps: 0.90 side, 1.15 floor-to-wall flange, 0.09 band joints, 0.17 doorway pieces;
- true waste 0.79 m2, reusable 0, 2 rolls.

Diagrams: `diagrams/WPE-A1_install.svg`, `diagrams/WPE-A1_cutting.svg`, and `-ARR`, `-FJ`, `-B` for the alternatives.

## 1. Door D1 (west wall, 0.90 m)

| Check | Independent result | V2.5 | Finding |
|---|---|---|---|
| Doorway continuation piece | DW1 0.30 x 0.90, the first lane of a new 0.90 m full-width cut H | DW1 0.90 x 0.30 | PASS |
| Placement | 0.20 m in the opening (x -0.20 - 0) + 0.10 m lap onto strip S1 (x 0 - 0.10); it runs along S1 and crosses no floor seam | lap 0.90 m running | PASS |
| Junction with the upturn | run 1 ends at the north jamb (P2 ends at y 1.50) and run 2 starts at the south jamb (P3 starts at y 0.60): the doorway lap meets both flanges **edge to edge - 2 open butt joints** | not named | NOTE (F-04): part of the open doorway detail |
| Jamb reveals | not covered by any piece | - | needs the doorway detail |
| Threshold to the dry side | UNRESOLVED: upturn across the threshold 0.18 m2, continuation terminated 0 m2 + 0.90 m termination, or jamb returns 0.08 m2 | UNRESOLVED, range 0.00 - 0.18 | PASS: not completed |

## 2. Door D2 (north wall, 0.80 m)

| Check | Independent result | V2.5 | Finding |
|---|---|---|---|
| Doorway continuation piece | DW2 0.30 x 0.80, from the second lane of H (0.30 x 0.10 left, waste) | DW2 0.80 x 0.30 | PASS |
| Placement | in the opening (y 3.00 - 3.20) + 0.10 lap onto S3 and S4 (y 2.90 - 3.00). The lap **crosses the end of the S3/S4 floor seam** (x 2.70 - 2.80): a three-layer point | - | NOTE (F-08): product treatment of laps over laps |
| Junction with the upturn | run 1 starts at the west jamb (P1 at x 2.40) and run 2 ends at the east jamb (P5 at x 3.20): **2 open butt joints** | not named | NOTE (F-04) |
| Threshold to the dry side | UNRESOLVED (0.00 - 0.16 m2) | UNRESOLVED | PASS |

Four open jamb junctions in all. None is counted as complete, by V2.5 or by this audit.

## 3. The pipe sleeve

| Check | Independent result | Finding |
|---|---|---|
| Count and state | 1 PIPE_PENETRATION from the text; treatment WITHHELD (V2.5: count 1, treatment and quantity None) | PASS: not treated as completed |
| Position | only a text anchor (3.20, 0.40) - an annotation point, not a surveyed pipe centre; diameter unknown; floor or wall not stated | the collar cannot be designed from the drawing |
| As planned (A) | on strip S4 (x 2.70 - 3.60): 0.40 m from the S3/S4 seam, 0.30 m from the south and east band flanges | a centred square collar or patch **up to 0.60 x 0.60 m** stays clear of every seam and flange; a larger one would lap onto the flange |
| Continuous fold (B) | on strip S1: 0.30 m from the S1/S2 seam, 0.40 m from the fold lines | the same 0.60 m limit |
| Material | not included anywhere | the collar or patch size is product data (N-6) |

## 4. The band joints

The plan's own order, which V2.5 does not fix:
- run 1: P1 0.90 at 0 - 0.90, P2 3.10 at 0.80 - 3.90;
- run 2: P3 3.64 at 0 - 3.64, P4 3.64 at 3.54 - 7.18, P5 0.52 at 7.08 - 7.60.

The joint 7.08 - 7.18 ends **0.02 m short of the NE internal corner** (7.20), leaving a lap edge in the corner fold
(F-03, FAIL: unchecked). Rearranged with no material change (WPE-A1-ARR):
- run 1 laid from the D1 jamb, joint at 3.00 - 3.10, 0.60 m from the NW corner;
- run 2 in the order 3.64, 0.52, 3.64, joints at 3.54 - 3.64 and 3.96 - 4.06.

Every joint is then at least 0.14 m from a corner and from a floor-seam end. Whether 0.14 m is enough is product data
(N-12). The fewest-joints reading of UP-WP-LAY-001 gives one band joint for 16.80 m2 (WPE-A1-FJ): run 1 in one 3.90 m
piece and run 2 in two, with the joint 0.30 m from the SE corner.

## 5. Continuous fold (WPE-B)

Strips along X, 4.00 m: 4 strips, 2 per roll, 16.00 m2 consumed. Installed 14.80 m2 = 13.44 + 1.20 laps + 0.16
corner squares; the 0.30 x 4.00 m trim is reusable; 2 rolls, 3 seams. The D1 doorway flap is made of the ends of S1 and
S2: **the S1/S2 seam runs out through the doorway** into the opening. That is a seam crossing the threshold, and needs
the doorway detail. D2 is the flat flap of S4. There are 4 jamb slits.
