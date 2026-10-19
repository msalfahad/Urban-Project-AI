# Progress toward the goal (owner-facing; the Lead rewrites this every run)

Plain words, no task numbers. Measured numbers come from SCOREBOARD.md; anything not measured says so.
Last update: 2026-10-19 22:20 UTC (Lead). Previous version: 2026-10-19 20:15 UTC.

## Where we are on the five gates
| Gate | In plain words | Due | Done so far | State |
|---|---|---|---|---|
| 0 | Measure the engine against the freelancer on a real villa; synthetic test villas | 21 Oct | done: Alsenan measured on the newest code, capability matrix, synthetic villas with hand truth; the apartment waits by your order | done for Alsenan |
| 1 | No room, door or window missed; wet and dry rooms right (floor area, tiles, waterproofing) | 28 Oct | wet / dry within 0.2 % on Alsenan; the membrane strip method now runs on all 17 real wet areas; roofs on your rule; 29 of 29 windows accounted for; room floor levels read from the mark in each room. Your wall-height and unmarked-room answers turn the held levels and heights into work now. Still open: none of it is wired into the released BOQ (the wiring step is now free and first on the board) | at risk (wiring not started) |
| 2 | Blockwork, plaster, paint, tiles, waterproofing, doors, windows within target | 11 Nov | membrane table and fold, 17 wet areas, window areas for 4 windows, floor-to-floor heights, book checks merged; plaster / paint measurable now by your height rule (rework on the board); room-by-room tiling table with cement, sand and adhesive, and tile counts with your joints, on the board | started |
| 3 | Structural: concrete census, rebar from schedules, formwork, excavation | 25 Nov | concrete ledger, footings by member, columns / necks merged (not in the released BOQ); 24 held beam spans read by hand and merged; neck-only columns read from the schedule (waits for the checker); stairs by hand (waits for the checker, your step-count and slab-thickness answers apply) | started |
| 4 | Read scanned and PDF plans | 9 Dec | the vector-PDF height reader is merged, but the Alsenan PDF sheets are scans: an OCR reader is needed | waiting its turn |

## Engine vs freelancer BOQ: Alsenan Chalet (released run, commit 8774071; the released numbers did not change this run)
Three more checked pieces were merged at 21:58 (beam hand reading, membrane strip method on real rooms, PDF height
reader) and two wait for the checker (neck-only columns, stairs). None is wired into the released BOQ yet.
"piece" = a merged, checked method piece run on the real drawing; "hand" = a reading of the drawing.
| Trade | Unit | Engine | Freelancer | Difference | Change since last report | Target | State |
|---|---|---|---|---|---|---|---|
| Concrete, 3 lines compared (footings, stairs + domes, pool) | m3 | 92.77 | 111.81 | -19.04 (-17.03 %) | none | within 2 % | released run unchanged; new pieces not wired |
| Isolated footings (hand = engine register) | m3 | 64.346 | 65.634 | -1.29 (-2.0 %) | none | within 2 % | engine right (freelancer counts one footing twice); F10 HELD with a designer request |
| Foundation straps (hand) | m3 | 3.391 | 3.3925 | 0.0 % | none | within 2 % | the released run gives 3.781 (+0.39 untraced) |
| Beams, 24 held spans (hand, merged) | m3 | 3.691 released by drawing evidence + 0.240 upstands the engine lacks; 19 spans held (4.25 - 9.18 m3) | not compared (beam line held) | not measured | merged (was waiting for the checker) | within 2 % | engine fix for planted columns and the missed mark is free to claim; dome-opening ring beam stays by your answer (about 1.45 m3 per opening, to be measured) |
| Neck-only columns CN (piece, waits for the checker) | m3 | 5 column lines now "not present" (were held); 6 necks 0.090 m2 each, height held | 0 columns; 0.810 m3 necks at an unprinted 1.50 m | columns agree; necks unresolved | new | within 2 % | neck height waits for a printed founding level (your earlier answer) |
| Stairs (hand, waits for the checker) | m3 | steps released 0.483 (entrance 0.357, lobby flight 0.126); main stair 5.131 by your step-count and "T 16" answers | main stair 8.131; entrance 1.411; round stair 5.510 | main stair -3.00 (-36.9 %) | new | within 2 % | his flights are 37 - 54 % longer than drawn; round stair held (no section) |
| Pool | m3 | 3.50 (released) | 12.35 | -8.85 | none | within 2 % | volume from the printed sizes is on the board |
| Domes | m3 | none (your answer: not concrete) | 6.78 | rule difference | none | - | settled |
| Wet-area waterproofing floor, 17 areas (piece + hand) | m2 | 72.12 | 72.01 | +0.11 (+0.16 %) | none | within 3 % | not yet in the released BOQ (wiring is first on the board) |
| Wet-area upturn, walls only (piece) | lm | 125.57 (your doorway answer) | 144.61 (full boundary) | rule difference | now from the strip method on real rooms (hand 127.07) | within 3 % | full boundary 144.73 = his 144.61 (+0.08 %) |
| Wet-area membrane rolls to buy (piece) | rolls | 13 / 14 / 15 by layout (with the pantry 15 / 16 / 17) | not given | - | new | exact | which layout is bought: asked you |
| Roof waterproofing membrane (piece) | m2 | 204.11 (3 roofs drawn on plans); 29 / 30 / 32 rolls by layout | 285.00 | -80.89 (-28.4 %) | none | within 3 % | top roof HELD by your answer |
| Roof upturn (piece) | lm | 181.59 | 194.00 | -12.41 (-6.4 %) | none | within 3 % | same cause |
| Windows with a printed height, 4 of 29 (piece) | m2 | 13.892 | 14.350 | -0.458 (-3.2 %) | none | exact | engine right on all four; 23 HELD: the PDF sheets are scans, hand reading next |
| Windows counted | pcs | 29 (27 measured + 2 held) | 29 | 0 | none | exact | - |
| Doors, windows (aluminium) | m2 | windows 13.89 of 116.9; doors 0 of 12.0 comparable | 116.9 / 12.0 | not comparable yet | none | exact | heights by hand from the scanned elevations next |
| Floor-to-floor heights (piece) | m | GF 4.50, 1F 4.20, 2F 4.20 (your answer: +9.70 to +13.90) | not in his BOQ | - | 2F now given by you | exact | - |
| Plaster / paint wall height (your rule) | m | GF 3.65 (3.60), 1F and 2F 3.35 (3.30) | not in his BOQ | - | new rule | exact | rework of the finish-height piece on the board |
| Rebar | t | not re-measured | 44.19 (earlier) | earlier estimate 26.24 t (-40.6 %) | none | within 3 % | not started |
| Blockwork | m | not re-measured | - | earlier estimate about 140 m short (-36.5 %) | none | within 3 % | gate 2 |
| Wall tile | m2 | not measured; wet walls about 447 - 473 m2 by hand depending on your tile-height answer | - | - | new estimate range (hand) | within 3 % | tile height asked you |
| Plaster | m2 | held | 1151.14 | - | none | within 3 % | measurable now by your height rule: code and hand table on the board |
| Paint | m2 | held | 1191.13 | - | none | within 3 % | same |
| Floor area | m2 | held | not compared | - | none | within 1 - 2 % | 11 labelled spaces held instead of lost; room-by-room table on the board |

## Engine vs freelancer BOQ: development project 2 (apartment)
Not measured, and paused by your order (Alsenan first).

## What the team has learned so far
- There is no basement on the Alsenan drawings; the freelancer's "basement" concrete is two stairs and three domes.
- The footing band is drawn closed all round the plot (91.94 m); the released engine loses one side (60.17 m kept).
- The freelancer counts one footing twice; footing F10 is drawn longer than its schedule row.
- Neck-only columns (type CN) are typed in the schedule as plain text; read now, they are 5 columns that do not exist.
- All 17 wet areas by hand agree with the freelancer's floor (72.12 vs 72.01 m2) and full boundary (144.73 vs 144.61 lm).
- The membrane layout (direction and start wall) changes the rolls as much as the room size: 13 to 15 rolls for the same
  17 wet areas; the strip count by length beats the count by area (a laundry needs 3 rolls, not 2).
- The ground floor is a split level (+1.00 / +0.30); only 6 of 27 rooms print their own floor level.
- The Alsenan PDF sheets are scans: no code can read their heights until an OCR reader exists.
- Stairs: the section, the architectural plan and the structural plan each draw a different step count; the freelancer's
  main-stair flights are 37 - 54 % longer than the drawn ones.
- Beams: the engine splits a beam where a planted column sits on it, and misses beam upstands printed in the sections.

## Being worked on now
- Checker (next run): neck-only columns from the schedule text, then the stairs by hand with your two stair answers.
- Workers whose code runs pass: wiring the wet-area and roof waterproofing pieces into the released BOQ (first: it moves
  the scoreboard), the plaster / paint wall heights with your rule, the beam fixes with the dome-opening ring beam, the
  room-by-room tiling table with cement, sand and adhesive, tile counts with your joints, plot-edge foundation members,
  stairs and pool in code, the controlled data file for typed drawing values.
- Workers whose code runs are refused: every room's floor level and wall height by hand; every window / door height by
  hand from the scanned elevations.
- Research scout (tonight 23:50 UTC): reading dimensions from scanned elevations, schedules, footings drawn as blocks.

## What is missing
- The wiring step: nothing merged reaches the released BOQ yet.
- Opening heights for 23 windows and all doors (scans: hand reading next).
- Wet-wall tile height and the decor-ceiling depth per room (asked); the roll layout for purchase (asked).
- Screed thickness on roofs and balconies; marble adhesive coverage; expansion-joint spacing (asked later).
- The second-floor top roof outline (held by your answer).
- The Kuwait specification chapters on waterproofing, floors, wall tiles and paint (file too big: parts needed).

## Waiting for the owner
- NEW: wet-room wall tiles: up to the decor ceiling with 0.15 m (about 453 m2), 0.20 m in wet rooms (about 447 m2), or up
  to the beam (about 473 m2) (recommendation: to the decor ceiling, 0.15 m).
- NEW: membrane rolls to buy: fewest per room with a cutting plan (13 wet / 29 roofs), one layout across (14 / 32), or the
  highest (15 / 32) (recommendation: fewest per room, with the cutting plan beside the BOQ line).
- Setting: run the four coding agents as Claude Code scheduled tasks with the repository attached (one worker still refused).
- Upload the Kuwait specification chapters 07100, 09200, 09300, 09400, 09900 as separate PDFs under 6 MB.
