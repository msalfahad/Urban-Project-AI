# T-114 Second-floor roof: does the 0.70 x 6.97 m side trim cover the 4.60 m parapet step? Pantry cutting plan. (Alsenan, development villa; NO REPO CODE)

Worker 1, 2026-10-20. Hand proof asked by owner Q-58 = A, CONDITIONAL (directive 2026-10-20, Part 3 / Part 4 (1)) and
directive item X4 (pantry). Read from Drive "Alsenan chalet project": P7757_DXF_COMPRESSED.zip (P7757.dxf, sha256
ab54dd55...31cc4, the file T-094 / T-096 used), Alsenan_Architectural_P7757_Pages_05-06 page 1 (second-floor plan, scan),
p7757_arch_sheet03.pdf (ground-floor plan, scan), p7757_arch_sheet10.pdf (section A-A). Outlines re-read line by line from
the DXF in a scratch calculator outside the repository (shapely, exact branch-and-bound roll packing); nothing here is engine
code. Only dimensions in a local frame (metres from the inner south-west corner of the roof); no coordinates, no client data.
Not an accuracy claim: Alsenan is the development villa. Every strip, piece, roll position and opening piece of every plan is
in T-114_CUTTING_PLANS.csv (254 rows).

## Rules applied

Q-58 A (suitable offcuts reused within the same roof or room; roll 1.00 x 10.00 m; 0.10 m overlap; 0.20 m upturn folded
from the same strip; physical strip layouts, never net area / 10), UP-WP-005 1.0.0 OWNER_APPROVED ("upturn bands with a lap
onto the floor membrane; pieces cut from rolls with offcut reuse; installed, overlap, cutting waste, reusable offcuts ...
reported separately; whole rolls from the cutting plan"), material spec MEM-URBAN-DEFAULT-1x10 (side and end lap 0.10 m;
corner_treatment null: "corner, penetration and detailing pieces follow the selected system and are UNRESOLVED until it is
named"), Q-24 (roof like a bathroom, inside the parapet, 0.20 m upturn), Q-25 (drafting gap covered: 0.075 m here), Q-29 /
Q-44 (dome positions are openings with a 0.20 m upturn), Q-49 A (each roof / room alone, fewest rolls), Q-35 C and Q-37 A
(pantry), Q-34 (2F block top roof HELD, untouched), UP-QTY-STATUS-001.

## 1. The parapet step, read from two drawings

| Item | DXF (P7757.dxf) | Second drawing |
|---|---|---|
| West part of the roof along the strips | west parapet inner face to the 2F block west wall face: 4.200 m (the parapet line itself stops 0.075 m short: Q-25 gap) | scan of the 2F plan: the same wall face scales 4.19 m from the parapet inner face (dome diameter R221 x 2 = 4.42 m as the scale bar; the 0.075 m short line scales 4.13, the block wall inner face 4.41) - no printed figure for this length |
| West part across the strips | 2.100 m (5.000 main band + 2.100 = 7.100 m from the south parapet inner face) | printed chain 139 + 442 + 129 = 710 cm to the same inner face |
| The step edge | the north parapet of the west part, inner face straight over the whole 4.20 m, parallel to the strips; inside corner with the west parapet at one end, inside corner with the 2F block wall (which runs on past it) at the other | scan: same, parapet printed 20 thick |
| Its upturn | 4.20 + 2 x 0.20 (corner squares) = **4.60 m long x 0.20 m** | - |
| Opening (dome) circles | r 2.211 m, each tangent to the end parapet's inner face (west and east) | printed R221 |

## 2. Is the 0.70 x 6.97 m trim enough? Check by check

The trim is the side cut of the last strip of the east wing (S25: band 11.50-11.80, installed 0.30 x 6.97 m cut from a
1.00 x 6.97 m piece). The piece it must give (S19) is the band 7.00-7.30 over the west part.

| Check | Need | Trim gives | Result |
|---|---|---|---|
| Width | 0.10 side lap onto S17 + 0.20 upturn = 0.30 m | 0.70 m | OK, 0.40 m spare |
| Length | 4.20 + 0.20 + 0.20 = 4.60 m | 6.97 m | OK, 2.37 m spare |
| Overlap | 0.10 m side lap over the full 4.60 m onto the floor strip S17 (UP-WP-005, MEM spec 0.10) | same as a piece from a new roll | OK |
| Upturn geometry | 0.20 m up the parapet inner face, 4.20 m straight, no slant, no curve | - | OK; the piece is a straight 0.30 x 4.60 band |
| Corners and terminations | both ends turn 0.20 m into inside corners (west parapet; block wall that continues): corner squares 0.20 x 0.20 are inside the 4.60 m; the 0.075 m drafting gap is covered (Q-25) | identical in the 17- and 18-roll plans | geometry OK; any extra corner reinforcement piece and the top-edge termination are UNRESOLVED by the material spec (system not named) - the same in both plans, so they do not decide 17 vs 18 |
| Seam arrangement | in the strict layout the band edge falls exactly on the parapet foot (7.30 = 7 x 0.90 + 1.00 above the start line): the side seam S17 / S19 lies in the last 0.10 m of floor before the angle; the east-wing S24 / S25 seam is the same and is in every plan already | identical whether S19 is cut from the trim or from a new roll | see section 4: shifting the strips 0.05 m moves both seams 0.05-0.15 m out of the angle at no roll cost |
| Is a piece allowed there? | S19 is not a patch: it is a full-length band of its own strip line, an "upturn band with a lap onto the floor membrane" (UP-WP-005), cut from this roof's own offcut (Q-58 A) | - | allowed by UP-WP-005 + Q-58 A; no owner question needed |

So the trim covers the step. **But the trim alone does not make 17 in every layout** (section 3).

## 3. Rolls: what really decides 17 or 18 (exact packing, each roof alone)

| Plan | Opening upturn round the two domes | S19 from | Roll metres | Rolls (lower bound) | Full-width roll ends left |
|---|---|---|---|---|---|
| P0-B (strict, T-094 H1) | folded from the strips that reach it | new roll | 164.50 | **18** (17) | 15.50 m |
| P0-B' strict + trim | folded from the strips | S25 trim | 159.90 | **18** (16) | 20.10 m |
| P0-A (engine-like) | strips stop at the opening edge; 16 flap pieces 0.772 m2 from this roof's roll ends | S25 trim | 154.87 | **17** (16) | 15.13 m before the flap pieces |
| **P05-A (recommended)** | as P0-A, 16 flap pieces 0.817 m2 | S25 trim (needs 0.35 x 4.60 of a 0.65 x 6.97 trim) | 155.03 | **17** (16) | 14.97 m before / 9.26 m after the flap pieces |
| P05-B | as P05-A, every piece from a roll | new roll | 159.63 | **18** (16) | - |

Why the strict layout stays 18 with the trim: its pieces over 3.03 m that do not share a roll with a 10.00 / 9.37 / 6.97
piece are 4.60, 4.60 and the 3.249 m tail of the 13.15 m strip S4 (12.45 m together, more than one roll); every 6.97 m roll
leaves only 3.03 m. Taking S19 out leaves 4.60 + 4.60 + 3.249, still two rolls. When the strips stop at the opening edge
(P0-A / P05-A) the S4 tail is 2.30 / 2.48 m, fits a 3.03 m end, and the two 4.60 m pieces share one roll -> 17. (17 is also
reached in the strict layout only by splicing S4 a second time from two 3.03 m roll ends: 3 pieces, one more end lap.)
All 17-roll plans use offcuts of this roof only (Q-58 A); every B plan is 18.

Flap pieces round the openings (P05-A): 4 x 0.56 x 0.23, 4 x 0.23 x 0.54, 4 x 0.19 x 0.18, 4 x 0.18 x 0.80 m (net 0.817 m2);
cut with a 0.10 m lap all round they take 5.71 m of full-width roll end in 14 rows of at most 0.431 m: rolls 13 and 14 ends
(3.03 m each: 3.014 + 2.698 m). The same pieces are in the T-096 engine run as patches (8 there, 0.063 m2, different cut rule).

## 4. Recommended plan P05-A, reported as Q-58 asks (installed separate from purchase)

Strips across the 18.87 m length from the south parapet, the first strip cut to 0.95 m (so no band edge falls on a parapet
foot): every parapet upturn parallel to the strips is folded from a strip that also carries floor (S19 and S25: 0.10 lap +
0.05 floor + 0.20 upturn = 0.35 m), and their side seams lie 0.05 - 0.15 m out from the angle instead of 0 - 0.10 m.
The shift is robust: any first-strip cut between 0.02 and 0.08 m gives the same 17 (checked as drawn, mirrored east-west,
moved 1.2 km, taken through millimetres); 0.10 m and more needs 18 (the block-wall upturn then needs an extra band).

| Installed (BOQ) | Value |
|---|---|
| Net roof floor inside the parapets less the two openings | 115.81 m2 (engine 115.83, T-094 115.817) |
| Upturn, unfolded with corner squares (parapets / walls 65.14 lm + openings 27.78 lm) | 18.49 m2 |
| Membrane surface to cover | 134.31 m2 |
| Strips | 25 strips (widths 0.95 / 1.00 x 22 / 0.35 x 2) + 16 opening flap pieces, every one dimensioned in the CSV |

| Purchase / cutting (separate) | Value |
|---|---|
| Rolls 1.00 x 10.00 m | **17** (lower bound 16; 17 proven minimum for this layout by exact search) |
| Gross cut from rolls for strips | 155.03 m = 155.03 m2 (6 strips spliced: 6 end laps x 0.10 m2 = 0.60 m2) |
| Cut from this roof's offcuts | S19 0.35 x 4.60 m (1.61 m2) from the S25 side trim; flap pieces 4.68 m2 cut (0.82 m2 net) from rolls 13 and 14 ends |
| Side-lap double cover | 13.14 m2 |
| Cut away over the openings (curved, unusable) | 3.91 m2 |
| Narrow trims | S1 0.05 x 19.27 m (0.96 m2, unusable sliver); S25 trim after S19: 0.30 x 4.60 m and 0.65 x 2.37 m |
| Full-width roll ends left after all cutting | 9.26 m: 3.03, 3.03 (rolls 15, 16), 1.435 (roll 12), 0.80 (roll 17), 0.33 (roll 14), and five ends of 0.06 - 0.17 m |

Freelancer: one roof line of 285.00 m2 and 194.00 lm of upturn, no roll count, no cutting plan: rolls are not comparable
(not measured on his side). Roof floor on the drawn plans 204.11 vs 285.00 m2 (-80.89 m2, -28.4 %), unchanged by this task
(2F block top roof HELD, Q-34).

## 5. Verdict on the second-floor roof

**17 rolls PROVEN under Q-58 A**, with a cutting plan in which (i) the 4.60 m parapet-step band is cut from the side trim of
the east-wing last strip (width 0.30-0.35 needed of 0.65-0.70, length 4.60 of 6.97, 0.10 m lap, 0.20 m upturn, inside-corner
ends) and (ii) the strips stop at the opening edge and the 16 small flap pieces round the two dome openings are cut from this
roof's own 3.03 m roll ends. The trim alone is not enough: in the strict layout where strips reach round the openings the
count stays 18 (proof in section 3). Under Q-58 B (no offcut reuse) every layout is 18. Roofs drawn: 8 + 6 + 17 = 31 under
Q-58 A (2F block top roof HELD, Q-34).
Engine V2.12 shows this roof HELD 17 (A) / 18 (B, C), 162.69 m: its counts equal the hand counts (ENGINE_RIGHT on rolls);
its metres differ (its own opening and strip cut rule, no shift). Proposal for the verifier / Lead: the line may be released
at 17 by a method version that cites Q-58 A, prints this cutting plan (or its own plan with the trim and flap pieces named)
and keeps the B figure 18 beside it. Until then it stays HELD 17 / 18 as the board says.

Not decided by the drawings and the same in the 17- and 18-roll plans (so not a reason to hold 17): the solid height of
the west part's north parapet is not printed (the plan draws a solid 0.20 - 0.40 m parapet; section A-A draws the +9.70
roof parapets as solid walls far above 0.20 m on the other faces); corner reinforcement pieces and the top-edge termination
of the upturn are UNRESOLVED until the membrane system is named (MEM-URBAN-DEFAULT-1x10); which long edge of the roll carries
the factory lap edge depends on the product (not specified on any sheet).

## 6. Pantry (ground floor), its own cutting plan, each room alone

| Item | Value |
|---|---|
| Size | 3.00 x 4.50 m: DXF wall faces 3.000 x 4.500; sheet 03 prints 450 and 300. Walls on west (two windows), south and north (one door opening, DXF line gap 1.00 m; sheet 03 prints 80 next to it); the east 4.50 m side is open to the dining room (layer of furniture / counter lines only) |
| Net floor (Q-37 A, printed size) | 13.50 m2 (counters not deducted, like every wet area) |
| Membrane outline (Q-35 C purchase: strips 0.20 m longer at both ends, whatever is at the edge; Q-37 A upturn across the open side too) | 3.40 x 4.90 m = 16.66 m2 |
| Layout chosen (Q-49 A) | strips along the 4.50 m walls: 4 strips x 4.90 m, installed widths 1.00 / 1.00 / 1.00 / 0.70, side laps 3 x 0.10 x 4.90 = 1.47 m2 |
| Rolls | **2** (roll 1: S1 + S2 = 9.80 m; roll 2: S3 + S4 = 9.80 m); lower bound ceil(19.60 / 10) = 2, optimal |
| Gross cut | 19.60 m2; side trim 0.30 x 4.90 = 1.47 m2; full-width roll ends 0.20 + 0.20 m |
| Other layout | across: 6 strips x 3.40 m (last 0.40 wide) = 20.40 m, 3 rolls (not chosen) |
| Robustness | without the upturn across the open side (3.20 x 4.90): still 4 strips, 2 rolls; any start wall: 2 rolls |
| BOQ upturn (Q-35 C, walls only) | west 4.50 + south 3.00 + north 3.00 less the door: 9.50 lm with the DXF 1.00 m opening; one doorway transition line; the 4.50 m open side as a threshold line (Q-37 A). The door width (DXF 1.00 vs the printed 80 beside it) is not settled here; it moves only these lines, not the rolls |

**Wet areas with the pantry: 19 + 2 = 21 rolls** (the 17 released wet areas keep 19, T-098 / V2.12; earlier hand plan 21
confirmed, not 19). Leftover full-width roll ends with the pantry: wet areas 64.73 + 0.40 = 65.13 m (Lead hand table) - the
pantry adds 0.40 m. Freelancer: no pantry waterproofing (his wet-area membrane has no pantry line): engine HELD vs freelancer 0;
hand 13.50 m2 floor / 2 rolls. Directive X4: the pantry hold has no drawing reason left; release through a method version.

## Learned / missing

- A side trim covering a step is necessary but not sufficient: the roll count is a packing result of the whole plan; here the
  saving needs the opening pieces from roll ends as well. "17 with trim, 18 without" is true only for layouts that stop at the
  opening edge.
- A band edge that lands exactly on a parapet foot puts a side seam in the angle (twice on this roof); a 0.02 - 0.08 m first
  strip cut removes it at no roll cost. Proposal for a later code task: the cutting plan tries a small start offset and prefers
  the layout whose seams are not within 0.10 m of a parallel wall foot at equal rolls (no owner question: UP-WP-005 already
  allows upturn bands; this is a tie-break).
- Missing: 2F block top roof (Q-34); the membrane system (corners, termination, lap edge); parapet solid height on the west
  part's north side; the pantry door width.
