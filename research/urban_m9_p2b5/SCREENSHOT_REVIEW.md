# Review of the four V2.5 waterproofing diagrams

**What was reviewed.** The program refers to four screenshots. The owner's own screenshot files were not available
in this session, so they were **not seen** and nothing below describes them. What was reviewed instead are the four
V2.5 diagrams the screenshots most likely show. They were regenerated from the Phase 2B-3 generator at the audited
commit and rendered headless (Chromium) for inspection:

| # | diagram | room |
|---|---|---|
| 1 | WP-B layout | 3.00 x 4.00 m bathroom, one 1.00 m door |
| 2 | WP-B rolls | its two rolls |
| 3 | WP-E layout | 3.60 x 3.00 m wet area, two doors, a pipe sleeve |
| 4 | WP-D layout | L-shaped bathroom, 3.00 x 3.00 m less 1.00 x 1.00 m |

If the owner's screenshots show something else (another room, another version, a hand mark-up), this review does
not cover it. The owner's files should be added to the next review.

## What the V2.5 diagrams show, and what they leave out

| # | shows | does not show (V2.5) | consequence | V2.6 |
|---|---|---|---|---|
| 1 | floor strips with their lap zones; the upturn as an outline around the room; the door | the band pieces, their joints, the doorway piece, the corners | a reader cannot see that two band joints sit exactly on floor-seam ends (four layers, F-03), or that the doorway piece meets the band end to end at both jambs (F-04) | `IX-02_install.svg`: band pieces B1-B5 drawn on their runs, joints in red, corners marked, the doorway piece and both jamb junctions, and the open flags listed under the plan |
| 2 | each roll as a bar with labelled lengths ("floor strip 5 3.00", "upturn lanes 2.80") | the rips across the roll, the lanes, the pieces cut from each lane, the rip remainder, the lane ends | "upturn lanes 2.80" hides that the 2.80 m cut is ripped into three 0.30 m lanes plus a 0.10 m residue, and that each lane is cross-cut into band pieces; the 0.28 m2 of true waste cannot be located (F-02, F-07) | `IX-02_cutting.svg`: each roll to scale, every cut, every rip into lanes, every cross-cut into pieces; offcuts shaded by class (true waste / reusable subject to N-7) and the untouched stock dashed |
| 3 | strips, the two doors, the sleeve marker | the joint 0.02 m short of an internal corner, the sleeve's clearances, the four jamb junctions | the near-corner joint is invisible, and so is the fact that a centred collar up to 0.60 m stays clear of every seam and flange (F-03, F-06) | `IX-03_install.svg`: the joint and its corner distance, the sleeve with its clearance, four jamb junctions |
| 4 | the L outline and its strips | strip S3 is clipped at the step, so the 1.00 x 0.80 m material beyond the wall line is not drawn; the "S5 0.40" label collides with the "3.00 m" dimension; a band piece starting on an internal corner | the reusable 0.80 m2 offcut (a doorway piece could be cut from it) is not visible; the corner start is not visible (F-02, F-03, F-07) | `IX-04_install.svg` and `IX-04_cutting.svg`: the external corner marked; the offcut `S3.o1` 0.80 x 1.00 drawn in place inside strip S3 and shaded REUSABLE_SUBJECT_TO_N7; labels kept clear of the band |

## Defects found in the new diagrams while reviewing them (fixed)

| defect | fix |
|---|---|
| the floor offcut beyond the wall line appeared only as a text label in the cutting plan, not as a shaded rectangle | the offcut now carries its position inside the strip (`in_piece_m`); the cutting plan draws it to scale with its class colour |
| "S5 0.40x3.00" overran the 0.40 m upright strip and ran into the band | narrow upright strips show their id only; the size stays in the piece table |
| text overflow, a band drawn on the wall line, hidden labels (found earlier in this phase) | corrected before the first commit of the generator |

## What no diagram can show yet

- The floor-to-wall junction is open (N-11 / P-1). The diagrams draw the plan's separate-upstand band. They do not
  claim it is the detail to be built; the alternatives are in `JUNCTION_ALTERNATIVES.md`.
- Corner, jamb, penetration and termination treatments are product details. They are marked and listed, never drawn as
  finished work.
- Falls are not on the plan. The lay order is shown only where exactly one drain is drawn.
