# T-089 Membrane cutting plan per wet room and per roof, each alone (MEMBRANE_CUTTING_PLAN_V1)

Opt-in method beside MEMBRANE_FOLD_V2; no released method or quantity changed (wiring into the released BOQ is T-093 /
later). Code: `engine/source/membrane_cutting_plan.py`; tests: `tests/t089_cutting_plan/`; Alsenan run:
`research/agents_t089/alsenan_cutting_run.py` (outputs to a scratch folder; the drawings and the SVGs with room
outlines stay out of the repository; this folder holds areas, lengths and strip lists only).

## Rules applied

Owner Q-49 A (each wet room and each roof alone; the layout with the fewest whole 1 x 10 m rolls; tie: shorter strip
metres; cutting plan, leftover metres and totals shown), Q-30 strip method (kitchen worked example), Q-35 C, Q-37 A
(pantry 4.50 x 3.00), Q-24 + addendum (roofs like a bathroom), Q-29 (dome positions are open skylights with the 0.20 m
upturn round them), UP-WP-001 / 002 / 003 (roll, lap, upturn as inputs), UP-QTY-STATUS-001 (held never 0). Scout R-05:
per-area proof by the lower bound ceil(strip metres / 10.00 m), no new dependency.

## Method

Four layouts per area (along / across the longest wall x lower / opposite start wall), strips from MEMBRANE_FOLD_V2
`strips()`, pieces packed whole into rolls (`membrane_layout.pack_rolls`: first fit decreasing, then exact branch and
bound; a gap above the lower bound is searched again with 5 000 000 nodes). Per area: every strip (width x length),
each piece's roll and position on it (from - to m), rolls, leftover metres per roll and per area, side trim m2 of the
narrow strips, membrane cut m2 (splice laps included), proof line. Identity checked on every area: cut + side trim =
strip metres x roll width. A remaining tie (same rolls and metres) is listed with each tied layout's side trim.

## Hand fixtures (not Alsenan), all pass

| Case | Hand result | Engine |
|---|---|---|
| owner kitchen 3.00 x 4.00 | along: 4 x 4.40 m, 2 rolls, 1.20 + 1.20 m left, cut 16.28 m2, trim 1.32 m2; across 5 x 3.40 m = 3 rolls | same, along chosen |
| owner picture 3.00 x 3.00 | 4 x 3.40 m = 13.60 m, 2 rolls, 6.40 m left, cut 12.58 m2 | same (the picture's 1 roll omits the upturn and laps) |
| 12.00 x 1.50 roof | along 2 strips of 12.40 m spliced 10.00 + 2.50 = 25.00 m, 3 rolls; across 14 x 1.90 = 26.60 m, 3 rolls -> tie on rolls, along by metres | same |
| L room 4 x 2 + 2 x 2 | 3 x 4.40 + 2 x 2.40 = 18.00 m, 2 rolls, cut 17.52, trim 0.48 (other start 0.88, tie listed) | same |
| kitchen in mm, turned 0 / 30 / 117 deg, mirrored | the kitchen numbers | same |
| 8 x 6 roof, 2 x 2 skylight | 6 x 8.40 + 2 x 3.40 = 57.20 m -> 7 rolls (an 8.40 piece leaves 1.60 m), lower bound 6, gap proven; across 9 rolls; opening upturn 8.00 lm / 1.60 m2 | same |
| no outline, bow tie, missing lap / roll, lap >= roll | HELD with the reason, every quantity None | same |

## Alsenan (development villa), engine vs the hand table (docs/agents/research/ALSENAN_MEMBRANE_PER_WET_ROOM.csv)

| Group | Rolls engine / hand | Strip metres engine / hand | Leftover m engine / hand | Membrane cut m2 engine / hand |
|---|---|---|---|---|
| 17 wet areas, each alone | 19 / 19 | 122.99 / 125.27 (-2.28 m, -1.8 %) | 67.01 / 64.73 | 116.11 / 117.09 |
| pantry (Q-37 A, printed 4.50 x 3.00) | 2 / 2 | 19.60 / 19.60 | 0.40 / 0.40 | 18.13 / 18.13 |
| roofs: 2F roof, 1F south-east, 1F west | 17 + 6 + 8 = 31 / 31 | 158.09 + 49.80 + 76.35 = 284.24 | 11.91 + 10.20 + 3.65 = 25.76 | 276.21 |
| roof above the 2F block | HELD (no plan draws it, owner Q-34) | HELD | HELD | HELD |

Every wet area has the hand table's roll count. Where the strip metres differ, the engine found a layout with the same
rolls and less membrane taken off the roll (Q-49 A tie rule):
- GF kitchen (L: 2.70 x 3.00 m with a 1.05 x 1.50 m leg): across, from the opposite wall: span 4.50 + 0.40 -> 6
  strips; the 4 strips over the 2.70 m part (bands 0-0.80 ... 2.60-3.50 from the far wall, the 4th crossing the 3.00 m
  line) are 2.70 + 0.40 = 3.10 m, the 2 over the leg 1.05 + 0.40 = 1.45 m: 4 x 3.10 + 2 x 1.45 = 15.30 m against the
  hand table's 16.60 m (along), 2 rolls both. Verdict proposal ENGINE_RIGHT (same rolls, 1.30 m less roll used).
- GF wash lobby with 2 basins (45 deg walls): 8.59 vs 9.13 m, 1 roll both; GF master bath: 6.62 vs 7.02 m, 1 roll both;
  GF W.C. 289 x 167: 5.95 vs 5.98 m. All from the opposite start wall, which the hand table did not try (its own note).
  ENGINE_RIGHT on metres; rolls unchanged.
- 1F laundry: same layout and metres; cut 15.705 vs 15.748 m2 (the hand table's narrow-strip width; no roll effect).

Roofs: the 1F south-east roof's 6 rolls sit above the lower bound 5 (49.80 m): 2 pieces of 7.90 m each leave 2.10 m,
room for one 1.70 m piece; the other 18 pieces of 1.70 m fit 5 to a roll -> 4 rolls; 2 + 4 = 6, proven by the exact
search. The 2F roof's 17 rolls are above its lower bound 16 (158.09 m), proven the same way. Fold V2's coverage check
flags an upturn the straight strips do not reach (slanted 45 deg walls) on four GF wet areas (0.003 - 0.010 m2 each),
the 1F west roof (0.009 m2) and the 2F roof (0.84 m2): by detail, never 0. The 2F roof's two dome openings: upturn
27.78 lm / 5.56 m2, of which 5.24 m2 folds up from the strips and 0.31 m2 needs own pieces by detail, reported in m2
and not in the roll count (no Urban rule says how they are cut).

Freelancer: his workbook has membrane m2 lines only, no rolls, cutting plan or leftover: rolls and leftover are not
comparable (not measured on his side).

## What is missing

Wiring into the released BOQ (T-093 releases the roll counts; this plan is the printable part beside them); the
roof above the 2F block (Q-34); how the opening-upturn own pieces are cut (by detail).
