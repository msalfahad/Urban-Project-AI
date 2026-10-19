# Progress toward the goal (owner-facing; the Lead rewrites this every run)

Plain words, no task numbers. Measured numbers come from SCOREBOARD.md; anything not measured says so.
Last update: 2026-10-19 18:15 UTC (Lead). Previous version: 2026-10-19 16:15 UTC.

## Where we are on the five gates
| Gate | In plain words | Due | Done so far | State |
|---|---|---|---|---|
| 0 | Measure the engine against the freelancer on a real villa; synthetic test villas | 21 Oct | done: Alsenan measured on the newest code, capability matrix, synthetic villas with hand truth; the apartment waits by your order | done for Alsenan |
| 1 | No room, door or window missed; wet and dry rooms right (floor area, tiles, waterproofing) | 28 Oct | wet / dry evidence within 0.2 % on Alsenan; roofs measured on your rule; the 11 lost spaces and the 2 lost windows are now held and visible (29 of 29 windows, all door elements accounted for). Still open: none of it is wired into the released BOQ yet; the GF floor level is read as 0.00 instead of +1.00 / +0.30 | at risk (wiring) |
| 2 | Blockwork, plaster, paint, tiles, waterproofing, doors, windows within target | 11 Nov | membrane purchase table and the hand table of all 17 wet areas checked and merged; window areas from printed heights checked (4 windows); floor-to-floor heights read from the elevations (waits for the checker); book checks done | started |
| 3 | Structural: concrete census, rebar from schedules, formwork, excavation | 25 Nov | new concrete ledger, footings by member and the column / neck reading merged (not yet in the released BOQ); stairs, pool, plot-edge members, column schedule rows and beams on the board | started |
| 4 | Read scanned and PDF plans | 9 Dec | waiting its turn; the third Drive project folder is not opened (your answer: ignore it) | waiting its turn |

## Engine vs freelancer BOQ: Alsenan Chalet (released run, commit 8774071; the released numbers did not change this run)
Four more checked pieces were merged since 16:15 (membrane table, wet-area hand table, lost windows, window areas), but
none is yet wired into the released BOQ. "piece" = a merged, checked method piece run on the real drawing; "hand" = a
reading of the drawing checked by the checker.
| Trade | Unit | Engine | Freelancer | Difference | Change since last report | Target | State |
|---|---|---|---|---|---|---|---|
| Concrete, 3 lines compared (footings, stairs + domes, pool) | m3 | 92.77 | 111.81 | -19.04 (-17.03 %) | none | within 2 % | released run unchanged; footings and pool HELD in the new ledger until their members and depths are applied |
| Isolated footings (hand = engine register) | m3 | 64.346 | 65.634 | -1.29 (-2.0 %) | none | within 2 % | engine right (freelancer counts one footing twice); F10 now HELD with a request to the designer by your answer, flagged in the final BOQ; provisional 2.275 m3 allowed if marked |
| Foundation straps (hand) | m3 | 3.391 | 3.3925 | 0.0 % | none | within 2 % | the released run gives 3.781 (+0.39 untraced) |
| Pool | m3 | 3.50 (released) | 12.35 | -8.85 | none | within 2 % | volume from the printed sizes (flat 1.15 m, 0.40 m floor) is on the board |
| Domes | m3 | none (your answer: not concrete) | 6.78 | rule difference | none | - | settled |
| Wet-area waterproofing floor, 17 areas (piece + hand) | m2 | 72.12 | 72.01 | +0.11 (+0.16 %) | hand table now checked: same within 0.002 | within 3 % | not yet in the released BOQ |
| Wet-area membrane table, 14 measured areas (piece) | m2 | 62.77 | 62.43 | +0.34 (+0.5 %) | now checked and merged | within 3 % | 13 rolls to buy, provisional; the strip method has not yet run on the real rooms (next on the board) |
| Wet-area upturn, 17 areas (hand) | lm | 127.07 walls only (your answer) | 144.61 (full boundary) | rule difference | your answer: walls only plus one doorway line per door | within 3 % | full boundary 144.73 = his 144.61 (+0.08 %); the 17.66 lm of doorways and open edges become doorway / threshold lines |
| Pantry (hand) | m2 | 13.50 by your answer | none | rule difference | new | - | waterproofed like a kitchen with its open side as a threshold line |
| Roof waterproofing membrane (piece) | m2 | 204.11 (3 roofs drawn on plans) | 285.00 | -80.89 (-28.4 %) | none | within 3 % | top roof HELD by your answer (asked again only at a milestone) |
| Roof upturn (piece) | lm | 181.59 | 194.00 | -12.41 (-6.4 %) | none | within 3 % | same cause |
| Windows with a printed height, 4 of 29 (piece) | m2 | 13.892 | 14.350 | -0.458 (-3.2 %) | was 3 windows 9.08 vs 9.70 | exact | engine right on all four (printed 2.30 / 1.60 vs his 2.00; arched 1F window to the drawn crown 4.81 vs 4.65); 23 HELD for no printed height on the DXF, curved ones on your answers |
| Windows counted | pcs | 29 (27 measured + 2 held) | 29 | 0 | was 27, 2 silently lost | exact | the 2 lost windows are found and held |
| Doors, windows (aluminium) | m2 | windows 13.89 of 116.9; doors 0 of 12.0 comparable | 116.9 / 12.0 | not comparable yet | windows now aluminium by your answer | exact | heights from the PDF elevations next |
| Rebar | t | not re-measured | 44.19 (earlier) | earlier estimate 26.24 t (-40.6 %) | none | within 3 % | not started |
| Blockwork | m | not re-measured | - | earlier estimate about 140 m short (-36.5 %) | none | within 3 % | gate 2 |
| Wall tile | m2 | not re-measured | - | earlier estimate about -15 % | none | within 3 % | gate 2 |
| Plaster | m2 | held | 1151.14 | - | none | within 3 % | floor-to-floor heights now read (4.50 / 4.20 m), wall heights next |
| Paint | m2 | held | 1191.13 | - | none | within 3 % | same |
| Floor area | m2 | held | not compared | - | none | within 1 - 2 % | 11 labelled spaces held instead of lost |

## Engine vs freelancer BOQ: development project 2 (apartment)
Not measured, and paused by your order (Alsenan first). Your re-exported DXF must pass the conversion check first.

## What the team has learned so far
- There is no basement on the Alsenan drawings; the freelancer's "basement" concrete is two stairs and three domes.
- The footing band is drawn closed all round the plot (91.94 m); the released engine loses one side (60.17 m kept).
- The freelancer counts one footing twice; footing F10 is drawn longer than its schedule row.
- Neck-only columns (type CN) are printed in the schedule as plain text, so the engine holds 5 columns that do not exist.
- Your kitchen example is reproduced number for number by the strip method, but it has not yet run on real room outlines.
- All 17 wet areas by hand agree with the freelancer's floor (72.12 vs 72.01 m2) and full boundary (144.73 vs 144.61 lm);
  the waterproofing book's "area / 8.91 x 1.10" roll ratio would buy 9 rolls where the cut strips need at least 12.
- The two lost windows were a curved glass wall set in a straight wall and a 0.50 m window clipped by a column outline.
- The ground floor is a split level (+1.00 and +0.30); the engine reads it as 0.00 from the plot corner marks.
- The DXF draws elevations for only part of the facades: most window heights must come from the PDF elevation sheets.

## Being worked on now
- Checker (next run 18:49): the floor-height reading from the elevations, then the book checks.
- Next free workers: the strip method on real wet-room outlines with your doorway and pantry answers; room floor levels
  and finish heights without assumed allowances; window and door heights from the PDF elevations; neck-only columns from
  the schedule text; plot-edge foundation members; stairs from section A-A; pool from its printed sizes; beams by hand.
- After the strip method is checked: wiring the wet-area, roof and membrane pieces into the released BOQ and re-measuring.
- Research scout (tonight 23:50 UTC): section heights and now opening heights from PDF elevations; schedules; footings
  drawn as blocks; roll cutting with offcuts reused.

## What is missing
- Opening heights for 23 windows and all doors (not on the DXF elevations; the PDF sheets are next).
- Wall heights per floor for plaster and paint (floor-to-floor now read; soffit and ceiling not printed).
- The second-floor top roof outline (held by your answer).
- The Kuwait specification chapters on waterproofing, floors, wall tiles and paint (file too big to read: parts needed).
- The apartment's DXF (paused by your order).

## Waiting for the owner
- Curved glass wall in a straight opening: printed 6.57 m, outer glass line 6.79 m or the middle 6.72 m (recommendation: the printed 6.57 m).
- Window curved on plan: straight chord 9.42 m2, inner arc 10.42 m2 or outer arc 11.51 m2 (recommendation: inner arc).
- Showers: waterproofing higher than 0.20 m on the shower walls, and to what height (recommendation: one height you give).
- Screeds under and over the membrane as BOQ lines (recommendation: both, thickness from the detail).
- NEW: tile joints in the tile count (recommendation: tiles by m2 plus waste, joint not counted).
- Upload the Kuwait specification chapters 07100, 09200, 09300, 09400, 09900 as separate PDFs under 6 MB.
