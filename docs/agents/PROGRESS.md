# Progress toward the goal (owner-facing; the Lead rewrites this every run)

Plain words, no task numbers. Measured numbers come from SCOREBOARD.md; anything not measured says so.
Last update: 2026-10-19 16:15 UTC (Lead). Previous version: 2026-10-19 14:30 UTC.

## Where we are on the five gates
| Gate | In plain words | Due | Done so far | State |
|---|---|---|---|---|
| 0 | Measure the engine against the freelancer on a real villa; synthetic test villas | 21 Oct | done: Alsenan measured on the newest code, capability matrix, synthetic villas with hand truth; the apartment waits by your order | done for Alsenan |
| 1 | No room, door or window missed; wet and dry rooms right (floor area, tiles, waterproofing) | 28 Oct | wet / dry evidence built and checked (Alsenan wet floor within 0.2 %); roofs measured on your rule; the 11 lost spaces are held and visible. Still open: 2 windows lost and 1 door element unexplained; the new pieces are not yet in the released BOQ | at risk |
| 2 | Blockwork, plaster, paint, tiles, waterproofing, doors, windows within target | 11 Nov | your membrane purchase table is built (14 wet areas, rolls to buy) and waits for the checker; door / window area method designed; printed floor levels read | started |
| 3 | Structural: concrete census, rebar from schedules, formwork, excavation | 25 Nov | new concrete ledger, footings by member and the column / neck reading are checked and merged (not yet in the released BOQ); stairs, pool / domes, plot-edge members and beams are next | started |
| 4 | Read scanned and PDF plans | 9 Dec | waiting its turn; a new project folder on Drive is not opened until you answer | waiting its turn |

## Engine vs freelancer BOQ: Alsenan Chalet (released run, commit 8774071; the released numbers did not change this run)
Six checked pieces were merged since 14:30, but none is yet wired into the released BOQ, so the released rows are the
same as before. Figures marked "piece" come from a merged, checked method piece run on the real drawing; "hand" from a
reading of the drawing; "not checked" from a worker result the checker has not yet verified.
| Trade | Unit | Engine | Freelancer | Difference | Change since last report | Target | State |
|---|---|---|---|---|---|---|---|
| Concrete, 3 lines compared (footings, stairs + domes, pool) | m3 | 92.77 | 111.81 | -19.04 (-17.03 %) | none | within 2 % | released run unchanged; in the new ledger footings and pool are HELD until their section / depth rules are applied |
| Isolated footings (hand = engine register) | m3 | 64.346 | 65.634 | -1.29 (-2.0 %) | checked and merged | within 2 % | engine right: the freelancer counts one footing twice (0.672 m3); footing F10 drawn 3.25 m vs scheduled 2.80 m waits on your answer (1.96 - 2.28 m3) |
| Foundation straps (hand) | m3 | 3.391 | 3.3925 | 0.0 % | none | within 2 % | the released run gives 3.781 (+0.39 untraced) |
| Pool | m3 | 3.50 (released) | 12.35 | -8.85 | none | within 2 % | ring now right in the new ledger; volume from the printed sizes (flat 1.15 m, 0.40 m floor) is next |
| Domes | m3 | none (your answer: not concrete, open skylights) | 6.78 | rule difference | settled | - | the freelancer's dome concrete is not in your design |
| Wet-area waterproofing floor (piece) | m2 | 72.12 | 72.01 | +0.11 (+0.2 %) | was -12.8 %, now checked and merged | within 3 % | wet / dry by label first, sanitary drawing second; not yet in the released BOQ |
| Wet-area membrane table, 14 measured areas (not checked) | m2 | 62.77 | 62.43 | +0.34 (+0.5 %) | new | within 3 % | 13 rolls to buy (16 if each area alone), provisional; 9 rows HELD (3 review spaces, 2 open plans with a pantry, 4 roofs), never 0 |
| Wet-area upturn | lm | 123.13 full boundary / 110.33 walls only | 122.61 | +0.4 % / -10.0 % | new | within 3 % | depends on whether the upturn crosses the door opening: new question to you |
| Roof waterproofing membrane (piece) | m2 | 204.11 (3 roofs drawn on plans) | 285.00 | -80.89 (-28.4 %) | was hand only, now checked and merged | within 3 % | the three plan roofs are right by hand; the second-floor top roof is on no plan: your question |
| Roof upturn (piece) | lm | 181.59 | 194.00 | -12.41 (-6.4 %) | new | within 3 % | same cause |
| Windows with a printed height, 3 of 29 (hand) | m2 | 9.08 | 9.70 | -0.62 (-6.4 %) | new | exact | the drawing prints 1.60 / 2.30 m where the freelancer used 2.00 m: engine right on these |
| Doors, windows (aluminium) | m2 | refused (engine gives pieces only) | 12.0 / 116.9 | - | none | exact | 19 windows have no printed height (held); 4 arched and the window material wait on your answers; 2 windows are lost (fix on the board) |
| Rebar | t | not re-measured | 44.19 (earlier) | earlier estimate 26.24 t (-40.6 %) | none | within 3 % | not started |
| Blockwork | m | not re-measured | - | earlier estimate about 140 m short (-36.5 %) | none | within 3 % | gate 2 |
| Wall tile | m2 | not re-measured | - | earlier estimate about -15 % | none | within 3 % | gate 2 |
| Plaster | m2 | held | 1151.14 | - | none | within 3 % | no printed wall height; heights from the sections next |
| Paint | m2 | held | 1191.13 | - | none | within 3 % | same |
| Floor area | m2 | held | not compared | - | none | within 1 - 2 % | 11 labelled spaces held instead of lost |

## Engine vs freelancer BOQ: development project 2 (apartment)
Not measured, and paused by your order (Alsenan first). Your re-exported DXF must pass the conversion check first.

## What the team has learned so far
- There is no basement on the Alsenan drawings; the freelancer's "basement" concrete is two stairs and three domes.
- The footing band is drawn closed all round the plot (91.94 m); the released engine loses one side (60.17 m kept).
- The freelancer counts one footing twice; footing F10 is drawn longer than its schedule row (asked).
- Neck-only columns (type CN) are printed in the schedule as plain text, so the engine holds 5 columns that do not exist.
- Your kitchen example (16.28 m2 cut, 2 rolls) is reproduced number for number by the engine's strip method; but on real
  rooms the method ran on none of the 14 Alsenan wet rooms (extra points on straight walls, two rooms at 45 degrees).
- Windows: the elevations print heights for only 3 of 29 windows; the freelancer used 2.00 m where 1.60 and 2.30 are printed.
- The three roofs drawn on the plans measure 204.11 m2 inside the parapets, exactly as by hand; the top roof is drawn nowhere.

## Being worked on now
- Checker (next run, 16:49): your membrane purchase table (14 wet areas, rolls to buy).
- Worker 3: the hand table of every Alsenan wet area (strips, cut membrane, rolls), the proof for the membrane table.
- Next free workers: the 2 lost windows and the unexplained door element; door / window areas from printed dimensions;
  the strip method on real room outlines; foundation members at the plot edge; stairs from section A-A; pool from its
  printed sizes; column schedule rows drawn as text; reading the supervisor's-eye book and the Kuwait specification
  chapters on waterproofing, floors, wall tiles and paint for checks.
- After the membrane table is checked: wiring the wet-area, roof and membrane pieces into the released BOQ, then a new
  scoreboard measurement.
- Research scout (tonight): section heights, schedules, footings drawn as blocks, roll cutting with offcuts reused.

## What is missing
- Printed wall heights per floor (plaster, paint).
- The second-floor top roof outline (no plan draws it).
- Heights for 19 windows (not printed anywhere).
- The apartment's DXF (paused by your order).

## Waiting for the owner
- Footing F10: drawn outline or schedule size (recommendation: hold and ask the designer).
- Arched windows: area to the arch top, to where the arch starts, or the true shape (recommendation: to the arch top).
- Windows aluminium by default (recommendation: yes, unless the drawing says otherwise).
- Second-floor top roof: from the 2F outer walls as a provisional figure (recommendation) or held for the designer.
- NEW: does the 0.20 m upturn run across the door opening (your kitchen example says yes, the registry doorway rule says
  no): 12.80 lm on Alsenan.
- NEW: the new project folder on Drive: may the team open it, and for what (recommendation: nobody opens it until you say).
