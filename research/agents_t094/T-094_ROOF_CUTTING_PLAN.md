# T-094 Roof membrane cutting plans by hand, each roof alone (Alsenan, development villa; NO REPO CODE)

Worker 1, 2026-10-20. Hand truth for the roof roll counts of the membrane cutting plan (MEMBRANE_CUTTING_PLAN_V1) and
the roof rolls the wiring task releases. Read from Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip (P7757.dxf,
sha256 ab54dd55...31cc4, the same file T-062 traced), roof plans of the first and second floor; outlines re-measured line
by line from the parapet and wall lines (layer of the parapets, door-layer face lines, column outlines), independent of
the engine's tracer. Calculation: a scratch calculator outside the repository (shapely polygons, an exact branch and bound
roll packing); nothing of it is engine code. Only dimensions are given here, no coordinates, no client data.
Not an accuracy claim: Alsenan is the development villa.

## Rules applied

Q-24 + addendum (roof like a bathroom: whole 1.00 x 10.00 m strips, 0.10 m lap between strips, 0.20 m upturn at the
parapets and walls, edges cut), UP-WP-001 / 002 / 003 (roll, 0.10 m lap incl. the end lap of a splice, 0.20 m upturn),
Q-25 (each drafting gap covered by the membrane: 0.075 / 0.200 / 0.405 m, as T-062 listed), Q-29 (dome positions are open
skylights, membrane stops with a 0.20 m upturn round each opening), Q-44 (ring beam B4 stays: it carries that upturn),
Q-49 A (each roof alone, the layout with the fewest rolls, tie: shorter metres; cutting plan, leftover metres), Q-34
(2F block top roof HELD, listed, never 0), UP-QTY-STATUS-001.

## Hand method (the owner's strip method, written out)

Upturn unfolded flat: the floor outline widened 0.20 m on every edge (mitred corners), less the opening widened 0.20 m
into the opening (disc of radius r - 0.20). Strips run in one direction; bands of 1.00 m at a pitch of 0.90 m (0.10 m lap)
from the start wall; the last band is cut to what is left (narrow strip). A strip's length is the extent, along the strip,
of what that band must cover that the previous strip does not already cover (its 0.10 m lap zone is covered by the
previous strip); where a band's need falls apart into separate pieces (a block, an opening that crosses the whole band),
each piece is its own strip. A strip over 10.00 m is spliced: 10.00 m pieces, every next piece carries the 0.10 m end lap
(19.27 m -> 10.00 + 9.37). Pieces are packed whole into 10.00 m rolls (no piece cut across two rolls), minimum found by
exact branch and bound; lower bound L1 = ceil(metres incl. end laps / 10.00). Four layouts per roof: strips along x or
along y, from either start wall.
Check of the method on the owner's own examples (not Alsenan): kitchen 3.00 x 4.00 along 4 x 4.40 m = 2 rolls, leftover
2.40 m; across 5 x 3.40 m = 3 rolls; 12.00 x 1.50 roof along 2 x 12.40 m spliced 10.00 + 2.50 = 25.00 m, 3 rolls; across
14 x 1.90 m = 26.60 m, 3 rolls. Same numbers as the T-089 hand fixtures.
Adversarial checks on the 2F roof: mirrored, turned 90 deg and taken through millimetres and back give the same 18 rolls
and 164.51 m (layout names swap as they should). One defect of the calculator itself was found and fixed: a band edge
that only touches an outline vertex (zero width) made an extra 2.10 m strip in a non-chosen layout; a zero-width touch is
now no need.

## Roof outlines (re-measured; floor = inside the parapet's inner face, Q-24)

| Roof | Outline (m) | Floor m2 | Edge for the upturn m | Floor + upturn (perimeter x 0.20) m2 | Widened outline m2 (with corner squares) |
|---|---|---|---|---|---|
| 1F west (+4.30) | 11.80 x 1.30 south band + 10.40 x 3.20 + 4.00 x 1.80 with an r 1.10 curved corner | 55.560 | 35.728 | 62.706 | 62.857 (+0.24 %) |
| 1F south-east (+5.50) | L: 18.97 x 1.30 + leg 1.30 x 6.20 | 32.721 | 52.940 | 43.309 | 43.469 (+0.37 %) |
| 2F (+9.70) | 18.87 x 5.00 + 4.20 x 2.10 (west part) + 6.57 x 6.60 (east wing), less two openings r 2.211 | 115.817 | 65.140 + 27.784 round the openings | 134.402 | 134.310 (-0.07 %) |
| 2F block top roof (+13.90) | no plan draws it | HELD (Q-34) | HELD | HELD | HELD |

Second drawing (printed dimensions on the scanned PDF plans, read by eye; Drive "Alsenan chalet project",
Alsenan_Architectural_P7757_Pages_05-06 page 1 = 2nd floor plan, p7757_arch_sheet04.pdf = 1st floor plan):
- 2F roof: openings printed R221 (DXF 2.211 m); across the west part 129 + 442 + 139 = 710 cm (DXF 1.29 + 4.42 + 1.39 =
  7.10 m inside the parapets); east wing 677 to the parapet outer face less the 20 parapet = 6.57 m (DXF 6.57); 645 + 15
  = 6.60 m (DXF 6.60). All agree.
- 1F west roof: 1060 printed from the west parapet's outer face to the building face, less 20 = 10.40 m (DXF 10.40, the
  column face after the 0.200 m Q-25 closure); 150 from the wall to the south parapet's outer face, less 20 = 1.30 m.
- 1F south-east roof: 150 printed on both the south band and the east leg, less 20 = 1.30 m (DXF 1.30).

The widened outline is what the strips must cover; it differs from floor + perimeter x 0.20 only by the corner squares
and the curved edges, within 0.5 % on every roof (acceptance). Every chosen layout covers it fully (shortfall 0.000 m2).
Same outlines as T-062 / T-071 (55.56 / 32.72 / 115.81 m2): confirmed.

## Result per roof (chosen layout, hand)

| Roof | Chosen layout | Strips (width x length m) | Rolls | L1 | Metres cut incl. end laps | Leftover m | Engine (cutting plan V1) |
|---|---|---|---|---|---|---|---|
| 1F west | along the 11.80 m side, from the south wall | 2 x 12.20 (10.00 + 2.30), 4 x 10.80 (10.00 + 0.90), 1 x 4.40, 0.40 x 3.93 | **8** | 8 (optimal) | 76.53 | 3.47 (rolls 7, 8: 0.77 + 2.70) | 8 rolls, 76.35 m, 3.65 m |
| 1F south-east | across the long band, from the far (north) wall | 2 x 7.90, 19 x 1.70, 0.47 x 1.70 | **6** | 5 | 49.80 | 10.20 | 6 rolls, 49.80 m, 10.20 m (identical) |
| 2F | along the 18.87 m side, from the south wall | 2 x 19.27, then per band round the openings 1.76 / 13.15 / 1.76, 0.67 / 10.96 / 0.67, 0.56 / 10.76 / 0.56, 1.33 / 12.29 / 1.33, then 3 x (4.60 + 6.97), 5 x 6.97, 0.30 x 6.97 | **18** | 17 | 164.51 | 15.49 | 17 rolls, 158.09 m, 11.91 m |
| 2F block top roof | - | HELD (Q-34) | HELD | - | HELD | HELD | HELD |
| **Total (3 roofs drawn)** | | | **32** | | 290.84 | 29.16 | 31 rolls, 284.24 m, 25.76 m |

Every strip, piece, roll and position on the roll (from - to m) is in ROOF_CUTTING_PLAN.csv, with all four layouts of
each roof (rolls, L1, metres, leftover, cut m2, shortfall).
Proof of the counts above L1: 1F south-east: a 7.90 m piece leaves 2.10 m, room for one 1.70 m piece; the other 18 x 1.70
fit 5 to a roll -> 2 + 4 = 6. 2F: six 10.00 m pieces (6 rolls), two 9.37 m (2 rolls), eight 6.97 m (8 rolls: no other
piece over 3.03 m fits beside one), three 4.60 m (two fit one roll, the third needs another: 2 rolls) -> at least 18,
and 18 is reached.

## Differences from the engine, explained (who is right)

1. **2F roof: 18 rolls by hand, 17 in the engine: engine defect: hand right, engine 1 roll short.**
   The west part of the 2F roof ends at a 4.20 m parapet (north side of the 4.20 x 2.10 part) that runs parallel to the
   strips. Its 0.20 m upturn lies in the band from 6.14 to 7.14 m above the start line, where there is no floor of the
   west part. The engine's strip rule (MEMBRANE_FOLD_V2 `strips`, `_bands`: a strip is made only where the band's floor
   interval [s0 + lap, s1] holds floor; only the far wall of the whole outline gets an upturn-only strip) makes no strip
   there, so 4.20 x 0.20 = **0.84 m2** of upturn is left uncovered. The engine's own coverage check reports exactly
   0.84 m2, and the cutting-plan write-up and owner question Q-58 call it "slanted (45 deg) parapet corners": the 2F roof
   has no slanted corner; it is a straight parapet upturn. Covering it needs one more strip of 4.60 m (4.20 + 2 x 0.20),
   which fits in no leftover (largest 3.03 m) -> **18 rolls, total roofs 32 (not 31)**. Any outline with a step edge
   parallel to the strips can hit this on any villa: it happens when the step's upturn falls in a band that holds no floor
   of that part (a geometric condition, not an Alsenan constant).
   If the owner allows cutting such a narrow piece from the side trim of the same roof (the 0.30 m last strip leaves
   0.70 x 6.97 m of side trim), the count could stay 17: that is the same kind of decision as Q-58 (patches from the same
   roof's offcut), not a hand result.
2. **2F roof metres: 164.51 vs 158.09 m (+6.42 m).** 4.60 m is the missing strip above; the rest (+1.82 m) is the
   strips round the two openings: by hand each strip reaches the 0.20 m upturn round the opening (no patch needed);
   the engine cuts the strips where the opening crosses the band and leaves 0.31 m2 of the opening upturn to own pieces
   (Q-58). Same rolls either way: with the engine's opening rule (variant H2 in the CSV) the hand count is still 18
   (159.49 m, 0.77 m2 of opening upturn left to patches by this calculator's cut rule).
3. **1F west roof: 8 = 8 rolls; metres 76.53 vs 76.35 (+0.18 m, +0.2 %).** The narrow last strip (0.40 m) must reach the
   upturn round the curved corner: 3.93 m by hand, 3.76 m in the engine, which leaves 0.009 m2 that its check reports.
   No roll effect. ENGINE_RIGHT on rolls, hand right on the last strip's length.
4. **1F south-east roof: identical** (6 rolls, 49.80 m, 10.20 m; all four layouts 50.84 / 68.61 / 56.00 / 49.80 m equal
   the engine's).
5. **Opening upturn (2F, two openings): 27.78 lm, 5.56 m2** by hand (2 x pi x 4.422 x 0.20 = 5.557 m2), as the engine.

Freelancer: one roof line of 285.00 m2 and 194.00 m of upturn; no rolls, no cutting plan, no leftover: the roll counts are
not comparable (not measured on his side). Roof floor drawn on plans 204.10 m2 vs 285.00 m2 (-80.90 m2, -28.4 %), unchanged:
the 2F block top roof (about 55 m2, Q-34) is HELD.

## What is missing

The 2F block top roof (Q-34, held). How the opening-upturn patches are cut (Q-58 open). Whether a narrow piece may be cut
from side trim (decides 17 vs 18 on the 2F roof): no Urban rule; for the Lead (it belongs with Q-58). Wet rooms were not
re-laid in this run; the engine's own check reports only 0.003 - 0.010 m2 on four GF wet areas, far less than one missed
step upturn (0.20 m x the edge length, at least about 0.1 m2 on a room wall), so those are not this defect.
