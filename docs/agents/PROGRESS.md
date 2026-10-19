# Progress toward the goal (owner-facing; the Lead rewrites this every run)

Plain words, no task numbers. Measured numbers come from SCOREBOARD.md; anything not measured says so.
Last update: 2026-10-19 20:15 UTC (Lead). Previous version: 2026-10-19 18:15 UTC.

## Where we are on the five gates
| Gate | In plain words | Due | Done so far | State |
|---|---|---|---|---|
| 0 | Measure the engine against the freelancer on a real villa; synthetic test villas | 21 Oct | done: Alsenan measured on the newest code, capability matrix, synthetic villas with hand truth; the apartment waits by your order | done for Alsenan |
| 1 | No room, door or window missed; wet and dry rooms right (floor area, tiles, waterproofing) | 28 Oct | wet / dry evidence within 0.2 % on Alsenan; roofs measured on your rule; 29 of 29 windows, all door elements accounted for; room floor levels now read from the mark inside each room (GF +1.00 / +0.30, waits for the checker). Still open: none of it is wired into the released BOQ; 21 of 27 rooms print no level of their own (asked you) | at risk (wiring; code runs refused) |
| 2 | Blockwork, plaster, paint, tiles, waterproofing, doors, windows within target | 11 Nov | membrane table and hand table of all 17 wet areas merged; window areas from printed heights (4 windows); floor-to-floor heights merged (GF 4.50 m printed, 1F 4.20 m); finish heights without assumed allowances built (waits for the checker); book checks merged | started |
| 3 | Structural: concrete census, rebar from schedules, formwork, excavation | 25 Nov | concrete ledger, footings by member, columns / necks merged (not in the released BOQ); all 24 held beam spans read by hand (waits for the checker): 5 released by drawing evidence, 19 held with reasons | started |
| 4 | Read scanned and PDF plans | 9 Dec | waiting its turn | waiting its turn |

## Engine vs freelancer BOQ: Alsenan Chalet (released run, commit 8774071; the released numbers did not change this run)
Two more checked pieces were merged since 18:15 (floor-to-floor heights from the sections, book checks), and two more
wait for the checker (room floor levels with finish heights; the beam hand reading). None is wired into the released BOQ
yet. "piece" = a merged, checked method piece run on the real drawing; "hand" = a reading of the drawing.
| Trade | Unit | Engine | Freelancer | Difference | Change since last report | Target | State |
|---|---|---|---|---|---|---|---|
| Concrete, 3 lines compared (footings, stairs + domes, pool) | m3 | 92.77 | 111.81 | -19.04 (-17.03 %) | none | within 2 % | released run unchanged; new pieces not wired |
| Isolated footings (hand = engine register) | m3 | 64.346 | 65.634 | -1.29 (-2.0 %) | none | within 2 % | engine right (freelancer counts one footing twice); F10 HELD with a designer request by your answer |
| Foundation straps (hand) | m3 | 3.391 | 3.3925 | 0.0 % | none | within 2 % | the released run gives 3.781 (+0.39 untraced) |
| Beams, 24 held spans (hand, waits for the checker) | m3 | 3.691 released by drawing evidence + 0.240 upstands the engine lacks; 19 spans held (4.25 - 9.18 m3) | not compared (beam line held on the scoreboard) | not measured | new: 5 spans released from printed sections and marks | within 2 % | 2 beams split wrongly at planted columns, 1 printed mark missed by the engine; dome ring beam asked you; 5 designer requests |
| Pool | m3 | 3.50 (released) | 12.35 | -8.85 | none | within 2 % | volume from the printed sizes is on the board |
| Domes | m3 | none (your answer: not concrete) | 6.78 | rule difference | none | - | settled; the ring beam round each opening asked you |
| Wet-area waterproofing floor, 17 areas (piece + hand) | m2 | 72.12 | 72.01 | +0.11 (+0.16 %) | none | within 3 % | not yet in the released BOQ |
| Wet-area membrane table, 14 measured areas (piece) | m2 | 62.77 | 62.43 | +0.34 (+0.5 %) | none | within 3 % | 13 rolls provisional; strip method on real rooms not yet claimed (code runs refused) |
| Wet-area upturn, 17 areas (hand) | lm | 127.07 walls only (your answer) | 144.61 (full boundary) | rule difference | none | within 3 % | full boundary 144.73 = his 144.61 (+0.08 %) |
| Roof waterproofing membrane (piece) | m2 | 204.11 (3 roofs drawn on plans) | 285.00 | -80.89 (-28.4 %) | none | within 3 % | top roof HELD by your answer |
| Roof upturn (piece) | lm | 181.59 | 194.00 | -12.41 (-6.4 %) | none | within 3 % | same cause |
| Windows with a printed height, 4 of 29 (piece) | m2 | 13.892 | 14.350 | -0.458 (-3.2 %) | none | exact | engine right on all four; 23 HELD (no height on the DXF; PDF elevations next) |
| Windows counted | pcs | 29 (27 measured + 2 held) | 29 | 0 | none | exact | - |
| Doors, windows (aluminium) | m2 | windows 13.89 of 116.9; doors 0 of 12.0 comparable | 116.9 / 12.0 | not comparable yet | none | exact | heights from the PDF elevations next |
| Floor-to-floor heights (piece) | m | GF 4.50 printed (engine's old figure 5.50 from a 0.00 level); 1F 4.20; 2F held | not in his BOQ | - | merged; room levels wait for the checker | exact | plaster / paint still need soffit or ceiling levels (not printed) |
| Rebar | t | not re-measured | 44.19 (earlier) | earlier estimate 26.24 t (-40.6 %) | none | within 3 % | not started |
| Blockwork | m | not re-measured | - | earlier estimate about 140 m short (-36.5 %) | none | within 3 % | gate 2 |
| Wall tile | m2 | not re-measured | - | earlier estimate about -15 % | none | within 3 % | gate 2 |
| Plaster | m2 | held | 1151.14 | - | none | within 3 % | still held: no soffit, floor build-up or ceiling level printed; 21 rooms have no own floor level |
| Paint | m2 | held | 1191.13 | - | none | within 3 % | same |
| Floor area | m2 | held | not compared | - | none | within 1 - 2 % | 11 labelled spaces held instead of lost |

## Engine vs freelancer BOQ: development project 2 (apartment)
Not measured, and paused by your order (Alsenan first).

## What the team has learned so far
- There is no basement on the Alsenan drawings; the freelancer's "basement" concrete is two stairs and three domes.
- The footing band is drawn closed all round the plot (91.94 m); the released engine loses one side (60.17 m kept).
- The freelancer counts one footing twice; footing F10 is drawn longer than its schedule row.
- Neck-only columns (type CN) are printed in the schedule as plain text, so the engine holds 5 columns that do not exist.
- All 17 wet areas by hand agree with the freelancer's floor (72.12 vs 72.01 m2) and full boundary (144.73 vs 144.61 lm).
- The ground floor is a split level (+1.00 / +0.30); only 6 of 27 rooms print their own floor level.
- Beams: the engine splits a beam where a planted column (P.C) sits on it, and the beam sections A-A / B-B on the slab
  sheets print sizes and 20 x 20 upstands that the engine never reads; the dome detail ring (442 cm) is the plan's inner
  circle, not its outer one.
- Unattended code runs are refused at random again: since 18:20 only 1 of 6 worker runs could run the project's code.

## Being worked on now
- Checker (running since 19:49): room floor levels and finish heights; the beam hand reading.
- Next free workers whose code runs pass: the strip method on real wet-room outlines (it unlocks wiring the wet-area,
  roof and membrane pieces into the released BOQ), window heights from the PDF elevations, neck-only columns, plot-edge
  foundation members, the beam split at planted columns.
- Workers whose code runs are refused: hand tables of every window / door height on the PDF elevations and of the
  stairs in section A-A (the truth the code tasks are checked against).
- Research scout (tonight 23:50 UTC): section heights, schedules, footings drawn as blocks, roll cutting.

## What is missing
- Reliable code runs for the scheduled workers (the setting change below).
- Opening heights for 23 windows and all doors (PDF elevations next).
- Floor levels for 21 unmarked rooms (asked); soffit / ceiling levels for plaster and paint (not printed).
- The second-floor top roof outline (held by your answer).
- The Kuwait specification chapters on waterproofing, floors, wall tiles and paint (file too big: parts needed).

## Waiting for the owner
- NEW: the ring beam round each dome opening after the skylight change: keep the plan's B4 20 x 50 ring, wait for the designer, or none (recommendation: keep B4, ask the designer to confirm).
- NEW (from a worker): a room with no floor level printed: take the floor's only level, or hold (recommendation: one-level floors take it, the split ground floor holds).
- Curved glass wall in a straight opening: printed 6.57 m or the glass line (recommendation: printed 6.57 m).
- Window curved on plan: chord, inner arc or outer arc (recommendation: inner arc).
- Showers: waterproofing higher than 0.20 m (recommendation: one height you give).
- Screeds under and over the membrane as BOQ lines (recommendation: both, thickness from the detail).
- Tile joints in the tile count (recommendation: not counted).
- Setting: run the four coding agents as Claude Code scheduled tasks with the repository attached (code runs refused).
- Upload the Kuwait specification chapters 07100, 09200, 09300, 09400, 09900 as separate PDFs under 6 MB.
