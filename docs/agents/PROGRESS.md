# Progress toward the goal (owner-facing; the Lead rewrites this every run)

Plain words, no task numbers. Measured numbers come from SCOREBOARD.md; anything not measured says so.
Last update: 2026-10-20 06:20 UTC (Lead). Previous version: 2026-10-20 04:20 UTC.

## Where we are on the five gates
| Gate | In plain words | Due | Done so far | State |
|---|---|---|---|---|
| 0 | Measure the engine against the freelancer on a real villa; synthetic test villas | 21 Oct | done: Alsenan measured on the newest code, capability matrix, synthetic villas with hand truth; the apartment waits by your order | done for Alsenan |
| 1 | No room, door or window missed; wet and dry rooms right (floor area, tiles, waterproofing) | 28 Oct | wet / dry within 0.2 % on Alsenan; 29 of 29 windows accounted for; room floor levels read from the mark in each room. NEW: the membrane rolls are now in the released BOQ (each room / roof alone: 19 rolls for 17 wet areas, 31 for the three roofs drawn) and the second-floor top roof shows as a held line instead of vanishing. Found by the hand plan of the roofs: one straight parapet upturn on the second-floor roof (0.84 m2) gets no strip in the engine, so the released roof count is one roll short if no trim may be reused (17 vs 18): fix is first on the board, that count to be held until your answer | at risk (one released count wrong, fix first) |
| 2 | Blockwork, plaster, paint, tiles, waterproofing, doors, windows within target | 11 Nov | membrane table, fold and cutting plan, window areas for 6 windows by hand, room levels with your wall-height rule, the room-by-room tiling table and plaster / paint per room by hand merged; NEW: tile count per room with your joints merged (every room held: no Alsenan drawing prints a tile size; offcut reuse asked you); plaster / paint wait on your beam, annex, door-height and ceiling answers | started |
| 3 | Structural: concrete census, rebar from schedules, formwork, excavation | 25 Nov | concrete ledger, footings by member, columns / necks, beams by hand, stairs by hand merged; NEW: the beam fix (planted columns no longer split a beam, a missed mark, upstands, ring beams round the dome openings) merged, about +4.30 m3 of beams once a ledger reads it (now on the board); the typed-values data file is built and waits for the checker. None of it is in the released concrete yet (92.77 vs 111.81 m3) | started |
| 4 | Read scanned and PDF plans | 9 Dec | the vector-PDF height reader is merged, but the Alsenan PDF sheets are scans; a scan reader that releases a number only when its dimension chain adds up exactly is now on the board | started (one task) |

## Engine vs freelancer BOQ: Alsenan Chalet (released concrete run, commit 8774071, unchanged; waterproofing now released by the new method version)
Since 04:20 four checked pieces were merged: the membrane cutting plan, the release of the rolls (wet areas and roofs),
the tile count with your joints and the beam fix. Concrete and finishing areas below did not move (the beam fix is not wired yet).
"piece" = a merged, checked method piece run on the real drawing; "hand" = a reading of the drawing.
| Trade | Unit | Engine | Freelancer | Difference | Change since last report | Target | State |
|---|---|---|---|---|---|---|---|
| Concrete, 3 lines compared (footings, stairs + domes, pool) | m3 | 92.77 | 111.81 | -19.04 (-17.03 %) | none | within 2 % | released run unchanged; new pieces not wired |
| Isolated footings (hand = engine register) | m3 | 64.346 | 65.634 | -1.29 (-2.0 %) | none | within 2 % | engine right (freelancer counts one footing twice); F10 HELD with a designer request |
| Foundation straps (hand) | m3 | 3.391 | 3.3925 | 0.0 % | none | within 2 % | the released run gives 3.781 (+0.39 untraced) |
| Beams (hand + piece, merged) | m3 | by hand 3.691 released + 0.240 upstands; the merged beam fix binds GF B26 3.905 and B27 3.787 as single spans, B7 arc strip 0.255, upstands 0.240, 1F dome ring beams 0.755 + 0.900: about +4.30 m3 once a ledger reads it | not compared (beam line held) | not measured | beam fix merged (was free to claim) | within 2 % | wiring into the concrete ledger is now on the board; still held: spans with no printed section |
| Neck-only columns CN (piece, merged) | m3 | 5 column lines now "not present" (were held); 6 necks 0.090 m2 each, height held | 0 columns; 0.810 m3 necks at an unprinted 1.50 m | columns agree; necks unresolved | merged (was waiting for the checker) | within 2 % | neck height waits for a printed founding level (your earlier answer) |
| Stairs (hand, merged) | m3 | main stair 5.011 (steps 1.386 + sloping slabs 2.885 + landings 0.740, checked by the verifier); entrance and lobby steps 0.483 | main stair 8.131; entrance 1.411; round stair 5.510 | main stair -3.12 (-38.4 %) | was 5.131 (-36.9 %): checker's recount of the steps | within 2 % | his flights are longer than drawn; winder steps and the round stair asked you |
| Pool | m3 | 3.50 (released) | 12.35 | -8.85 | none | within 2 % | volume from the printed sizes is on the board |
| Domes | m3 | none (your answer: not concrete) | 6.78 | rule difference | none | - | settled |
| Wet-area waterproofing floor, 17 areas (piece + hand) | m2 | 72.12 | 72.01 | +0.11 (+0.16 %) | none | within 3 % | not yet in the released BOQ (wiring is first on the board) |
| Wet-area upturn, walls only (piece) | lm | 125.57 (your doorway answer) | 144.61 (full boundary) | rule difference | now from the strip method on real rooms (hand 127.07) | within 3 % | full boundary 144.73 = his 144.61 (+0.08 %) |
| Wet-area membrane rolls to buy (released, your answer: each room alone) | rolls | 19 for 17 wet areas (pantry held: its size is not drawn); 122.99 m of strips vs 125.27 by hand (-1.8 %, same rolls, a better start wall in 4 rooms; checker confirmed on the kitchen by hand), 67.01 m left over | not given | not comparable | now in the released BOQ (was a piece) | exact | tiny corners 0.003 - 0.010 m2 in 4 rooms not reached: a hand plan of every wet room is on the board |
| Roof waterproofing membrane (released) | m2 | 204.11 (3 roofs drawn on plans) + the second-floor top roof as a HELD line (your answer); rolls each roof alone released 31 (17 + 6 + 8), by hand 32 (8 + 6 + 18) | 285.00 | -80.89 (-28.4 %) | rolls now released; hand plan finds the 2F roof one roll short | within 3 % | 2F roof: a 4.20 m straight parapet upturn (0.84 m2) gets no strip; 17 rolls only if that piece is cut from the same roof's side trim (asked you), else 18; fix first on the board |
| Roof upturn (released) | lm | 181.59 | 194.00 | -12.41 (-6.4 %) | now released | within 3 % | top roof held (your answer) |
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
| Floor tile count per room (piece, merged) | tiles | held in all 25 floor rooms: no tile size printed on any Alsenan sheet; for 60x60 on 23 rooms 697 tiles without offcut reuse (+21 % over net m2) or 611 with reuse in the same room (+6 %) | not given | not comparable | new | exact | tile size per room and offcut reuse asked you |
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

- A strip layout can look complete and still miss a piece: an outline step whose edge runs the same way as the
  strips leaves its upturn uncovered (0.84 m2 on the second-floor roof); only a full hand plan found it.
- Whether an offcut may be reused inside the same room is the open rule behind both the membrane rolls (one roll on
  this villa) and the tile count (15 - 20 % of the tiles bought).

## Being worked on now
- First on the board for workers whose code runs pass: the membrane fix (a strip for every parapet step, the 2F roof roll
  count held between 17 and 18 until your answer), then the beam fix into the concrete ledger (about +4.30 m3, measured
  against the 24 hand-read spans), then the scan reader, plot-edge foundation members, stairs and pool in code.
- Waiting for the checker: the roof cutting plans by hand (8 + 6 + 18 = 32 rolls; its checks were refused at 06:05) and
  the typed-values data file (of the 167 held concrete lines, 66 lines / 58.87 m3 rest only on values read from the
  drawings; blinding 22.155 vs his 47.055 m3 is unresolved).
- Waiting for the checker too: plot-edge foundation members (straps 3.390 vs his 3.3925 m3; the released +0.39 m3
  traced to one strap running into an open footing outline; natural-ground boundary beam 3.526 vs 7.560 m3).
- Free for workers whose code runs are refused: the wet-room cutting plans by hand, and the list of every printed
  finishing note, tile size and door height.
- Queued: plaster and paint into the released BOQ, after the membrane fix and your beam, annex, door-height, ceiling
  answers.
- Research scout (next run 23:50 UTC): Arabic and English notes on scanned plans; and how to prove a strip layout covers
  every piece.

## What is missing
- The membrane fix for parapet steps (first on the board); until then the released 2F roof roll count is not proven.
- The beam fix is merged but no concrete ledger reads it yet (on the board).
- Opening heights for 23 windows (scans) and all doors but the main entrance (not printed: asked).
- Tile sizes per room (none printed) and the offcut rule (asked).
- The beam depth for your wall-height rule, the annex slab height and a ceiling rule (asked).
- Screed thickness on roofs and balconies; marble adhesive coverage; expansion-joint spacing (asked later).
- The second-floor top roof outline (held by your answer).
- The Kuwait specification chapters on waterproofing, floors, wall tiles and paint (file too big: parts needed).

## Waiting for the owner
- CORRECTED: membrane pieces the strips do not reach. The 2F roof piece is a straight 4.20 m parapet upturn (0.84 m2),
  not a slanted corner: cut it (and the small dome-opening pieces, about 0.31 m2) from the same roof's own trim, no
  extra roll (recommendation; roofs 31 rolls), or always from a new roll (roofs 32), or ready-made collars at openings.
- NEW (from a worker): tiles: may the offcut of a cut tile be used for another cut piece in the same room? Reuse in the
  same room when the offcut is at least 20 cm (recommendation; 60x60 +6 % over net m2), no reuse (+21 %), or buy by m2
  plus your size waste only.
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
- Setting: run the four coding agents as Claude Code scheduled tasks with the repository attached (since 04:20 every
  run left a log line, but the checker was refused its freeze check and merge at 06:05 and a claim at 04:45).
- Upload the Kuwait specification chapters 07100, 09200, 09300, 09400, 09900 as separate PDFs under 6 MB.
