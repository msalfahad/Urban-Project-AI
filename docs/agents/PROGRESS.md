# Progress toward the goal (owner-facing; the Lead rewrites this every run)

Plain words, no task numbers. Measured numbers come from SCOREBOARD.md; anything not measured says so.
Last update: 2026-10-20 04:20 UTC (Lead). Previous version: 2026-10-20 02:10 UTC.

## Where we are on the five gates
| Gate | In plain words | Due | Done so far | State |
|---|---|---|---|---|
| 0 | Measure the engine against the freelancer on a real villa; synthetic test villas | 21 Oct | done: Alsenan measured on the newest code, capability matrix, synthetic villas with hand truth; the apartment waits by your order | done for Alsenan |
| 1 | No room, door or window missed; wet and dry rooms right (floor area, tiles, waterproofing) | 28 Oct | wet / dry within 0.2 % on Alsenan; the membrane strip method now runs on all 17 real wet areas; roofs on your rule; 29 of 29 windows accounted for; room floor levels read from the mark in each room. Your wall-height and unmarked-room answers turn the held levels and heights into work now. Still open: none of it is wired into the released BOQ; the checker sent the wiring back at 02:25 for two faults (the roll count must follow your 'each room alone' answer; the top roof must show as held, not vanish); the fix is first on the board | at risk (wiring back for rework) |
| 2 | Blockwork, plaster, paint, tiles, waterproofing, doors, windows within target | 11 Nov | membrane table and fold, window areas for 6 windows by hand, room levels with your wall-height rule, the room-by-room tiling table (cement, sand, adhesive) and plaster / paint per room under each beam option all merged; plaster / paint wait on your beam, annex, door-height and ceiling answers; tile counts and cutting plans on the board | started |
| 3 | Structural: concrete census, rebar from schedules, formwork, excavation | 25 Nov | concrete ledger, footings by member, columns / necks merged (not in the released BOQ); 24 held beam spans read by hand and merged; neck-only columns read from the schedule and stairs by hand (main stair 5.011 vs 8.131 m3) merged; round stair and turning steps wait on your answers | started |
| 4 | Read scanned and PDF plans | 9 Dec | the vector-PDF height reader is merged, but the Alsenan PDF sheets are scans; a scan reader that releases a number only when its dimension chain adds up exactly is now on the board | started (one task) |

## Engine vs freelancer BOQ: Alsenan Chalet (released run, commit 8774071; the released numbers did not change this run)
Nothing merged since 02:10. The membrane cutting plan (rolls, strips and leftover per wet room and roof, each alone)
is built and waits for the checker, whose code run was refused at 03:50; the wet-area / roof wiring fix is being built.
"piece" = a merged, checked method piece run on the real drawing; "hand" = a reading of the drawing.
| Trade | Unit | Engine | Freelancer | Difference | Change since last report | Target | State |
|---|---|---|---|---|---|---|---|
| Concrete, 3 lines compared (footings, stairs + domes, pool) | m3 | 92.77 | 111.81 | -19.04 (-17.03 %) | none | within 2 % | released run unchanged; new pieces not wired |
| Isolated footings (hand = engine register) | m3 | 64.346 | 65.634 | -1.29 (-2.0 %) | none | within 2 % | engine right (freelancer counts one footing twice); F10 HELD with a designer request |
| Foundation straps (hand) | m3 | 3.391 | 3.3925 | 0.0 % | none | within 2 % | the released run gives 3.781 (+0.39 untraced) |
| Beams, 24 held spans (hand, merged) | m3 | 3.691 released by drawing evidence + 0.240 upstands the engine lacks; 19 spans held (4.25 - 9.18 m3) | not compared (beam line held) | not measured | merged (was waiting for the checker) | within 2 % | engine fix for planted columns and the missed mark is free to claim; dome-opening ring beam stays by your answer (about 1.45 m3 per opening, to be measured) |
| Neck-only columns CN (piece, merged) | m3 | 5 column lines now "not present" (were held); 6 necks 0.090 m2 each, height held | 0 columns; 0.810 m3 necks at an unprinted 1.50 m | columns agree; necks unresolved | merged (was waiting for the checker) | within 2 % | neck height waits for a printed founding level (your earlier answer) |
| Stairs (hand, merged) | m3 | main stair 5.011 (steps 1.386 + sloping slabs 2.885 + landings 0.740, checked by the verifier); entrance and lobby steps 0.483 | main stair 8.131; entrance 1.411; round stair 5.510 | main stair -3.12 (-38.4 %) | was 5.131 (-36.9 %): checker's recount of the steps | within 2 % | his flights are longer than drawn; winder steps and the round stair asked you |
| Pool | m3 | 3.50 (released) | 12.35 | -8.85 | none | within 2 % | volume from the printed sizes is on the board |
| Domes | m3 | none (your answer: not concrete) | 6.78 | rule difference | none | - | settled |
| Wet-area waterproofing floor, 17 areas (piece + hand) | m2 | 72.12 | 72.01 | +0.11 (+0.16 %) | none | within 3 % | not yet in the released BOQ (wiring is first on the board) |
| Wet-area upturn, walls only (piece) | lm | 125.57 (your doorway answer) | 144.61 (full boundary) | rule difference | now from the strip method on real rooms (hand 127.07) | within 3 % | full boundary 144.73 = his 144.61 (+0.08 %) |
| Wet-area membrane rolls to buy (hand, your answer: each room alone) | rolls | 19 for 17 wet areas (21 with the pantry); engine cutting plan 19 = hand, 122.99 m of strips vs 125.27 by hand (-1.8 %, same rolls, a better start wall in 4 rooms), 67.01 m left over | not given | not comparable | engine plan now equals the hand count (not yet checked) | exact | wiring fix being built; patches at dome openings / slanted corners (1.15 m2 on the 2F roof) asked you |
| Roof waterproofing membrane (piece) | m2 | 204.11 (3 roofs drawn on plans); 31 rolls each roof alone (17 + 6 + 8), engine cutting plan 31 = hand, 25.76 m left over | 285.00 | -80.89 (-28.4 %) | none | within 3 % | top roof HELD by your answer; the checker found the engine drops it silently instead of showing it held: being fixed |
| Roof upturn (piece) | lm | 181.59 | 194.00 | -12.41 (-6.4 %) | none | within 3 % | same cause |
| Windows with a printed height, 6 of 29 (hand, merged) | m2 | 26.485 | 24.280 | +2.205 (+9.1 %) | was 4 of 29, 13.892 vs 14.350 | exact | engine right on 4 printed heights, 1 rule difference (curved window, your answer); 23 HELD (scans); the curved pool glazing is 6.57 m wide by your answer, height 4.30 m |
| Windows counted | pcs | 29 (27 measured + 2 held) | 29 | 0 | none | exact | - |
| Doors, windows (aluminium) | m2 | windows 26.49 of 116.9; doors: main entrance 2.00 x 2.50 = 5.00 only | 116.9 / 12.0 | not comparable yet | windows from 13.89 | exact | no other door height is printed: asked you |
| Floor-to-floor heights (piece) | m | GF 4.50, 1F 4.20, 2F 4.20 (your answer: +9.70 to +13.90) | not in his BOQ | - | 2F now given by you | exact | - |
| Plaster / paint wall height (your rule) | m | GF 3.65 (3.60), 1F and 2F 3.35 (3.30) | not in his BOQ | - | new rule | exact | rework of the finish-height piece on the board |
| Rebar | t | not re-measured | 44.19 (earlier) | earlier estimate 26.24 t (-40.6 %) | none | within 3 % | not started |
| Blockwork | m | not re-measured | - | earlier estimate about 140 m short (-36.5 %) | none | within 3 % | gate 2 |
| Wall tile | m2 | not measured; wet walls about 447 - 473 m2 by hand depending on your tile-height answer | - | - | new estimate range (hand) | within 3 % | tile height asked you |
| Plaster | m2 | held | 1151.14 | - | none | within 3 % | waits on your beam-depth, annex and door-height answers; 6 closed dry rooms by hand: 336.94 (0.60 m always) / 321.56 (deepest beam) / 331.49 (deep beam where it crosses) vs his 375.40 m2 (-10.2 / -14.3 / -11.7 %); he deducts openings at half, your rule takes the full opening |
| Paint | m2 | held | 1191.13 | - | none | within 3 % | same walls as plaster; ceilings have no rule yet (he paints 452.33 m2 of decor ceilings): asked you |
| Dry-room floor tiles, 10 rooms (piece, merged) | m2 | 194.98 | 189.61 | +5.37 (+2.83 %) | new | within 1 - 2 % | first-floor living 44.87 vs 38.96 holds the corridor / landing he has in no row: asked you; second-floor lobby 8.775 vs 7.70 engine right (printed 4.50 x 1.95) |
| Stair marble (piece, merged) | m2 | 39.49 | not compared | - | new | exact | turning steps and round stair held (your answers pending) |
| Tiling materials (piece, PROVISIONAL) | bags / m3 | cement 80 - 111 bags, sand 10.91 - 15.21 m3, adhesive 58 bags of 20 kg | not given | - | new | - | provisional by your answer; stair bed held on the 1:3 question |
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
- No beam on the Alsenan roof-slab plans is 0.60 m deep (0.40, 0.50, 0.75, 0.85, 1.20 m), so your 0.60 m rule needs a
  choice for real beams; the ground-floor annex roof (+4.30) may or may not be a slab level.
- Only one door height is printed on the whole Alsenan set (the main entrance, 2.50 m); the freelancer's 2.40 m is not
  printed anywhere.

## Being worked on now
- Worker 1 (since 03:20, its code runs passed): the wet-area / roof wiring fix: rolls released each room alone (19 wet,
  21 with the pantry, 31 roofs) and the top roof shown as held, not dropped.
- Waiting for the checker: the membrane cutting plan per room and roof (19 = 19 and 31 = 31 rolls against the hand
  table, strips 1.8 % shorter by a better start wall); the checker's code run was refused at 03:50, so it waits.
- Free for workers whose code runs pass: tile counts with your joints, beam fixes with the dome-opening ring beam, the
  scan reader with a chain-sum check, plot-edge foundation members, stairs and pool in code, the typed-values data file.
- Free for workers whose code runs are refused: the roof cutting plans by hand, and the list of every printed finishing
  note, tile size and door height (first-floor living room split from its landing by printed sizes).
- Queued: plaster and paint into the released BOQ, after the wiring fix and your beam, annex, door-height, ceiling answers.
- Research scout (next run 23:50 UTC): Arabic and English notes on scanned plans.

## What is missing
- The wet-area / roof wiring fix (first on the board): until it merges, no waterproofing quantity is in the released BOQ.
- Opening heights for 23 windows (scans) and all doors but the main entrance (not printed: asked).
- The beam depth for your wall-height rule, the annex slab height and a ceiling rule (asked).
- Screed thickness on roofs and balconies; marble adhesive coverage; expansion-joint spacing (asked later).
- The second-floor top roof outline (held by your answer).
- The Kuwait specification chapters on waterproofing, floors, wall tiles and paint (file too big: parts needed).

## Waiting for the owner
- NEW: membrane patches at the two dome openings and the slanted roof corners (about 1.15 m2 on the second-floor
  roof): cut from the same roof's leftover, no extra roll (recommendation; roofs stay 31 rolls), one extra roll per roof
  / room (roofs 32), or a ready-made collar / corner piece as its own line.
- First-floor living room: the corridor / stair landing in front of it (about 5.91 m2) is in no freelancer row:
  porcelain as its own row (recommendation), marble with the stair, or left out.
- Ceilings: paint every decor ceiling, no plaster (recommendation; 105.88 m2 on the 6 closed dry rooms), the same but
  no paint in wet rooms, or plaster and paint the slab soffit too.
- Wall height under real beams: always 0.60 m, the deepest beam at the room, or a deep beam only where it crosses the
  ceiling (recommendation: the last one; 6 rooms 336.94 / 321.56 / 331.49 m2 vs his 375.40).
- Annex rooms (+0.30 to +4.30): 4.00 m slab to slab (recommendation) or hold.
- Door height when none is printed: hold and ask the architect now, and give us your standard height for next time.
- Stair marble bed 1:3: about 10 bags and 1.0 m3 sand per m3 (recommendation), the 1:4 figures, or your own.
- Round stair with no section: use the plan count of 28 steps (recommendation) or hold.
- Turning steps: half riser x their plan area (0.120 m3 on the main stair, recommendation), part of the landing, or hold.
- Setting: run the four coding agents as Claude Code scheduled tasks with the repository attached (since 02:15: four of the
  five finished worker runs left no log line; the checker was refused its code run at 03:50 after passing at 02:26).
- Upload the Kuwait specification chapters 07100, 09200, 09300, 09400, 09900 as separate PDFs under 6 MB.
