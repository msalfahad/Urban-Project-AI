# Progress toward the goal (owner-facing; the Lead rewrites this every run)

Plain words, no task numbers. Measured numbers come from SCOREBOARD.md; anything not measured says so.
Last update: 2026-10-20 08:20 UTC (Lead). Previous version: 2026-10-20 06:20 UTC.

## Where we are on the five gates
| Gate | In plain words | Due | Done so far | State |
|---|---|---|---|---|
| 0 | Measure the engine against the freelancer on a real villa; synthetic test villas | 21 Oct | done: Alsenan measured on the newest code, capability matrix, synthetic villas with hand truth; the apartment waits by your order | done for Alsenan |
| 1 | No room, door or window missed; wet and dry rooms right (floor area, tiles, waterproofing) | 28 Oct | wet / dry within 0.2 % on Alsenan; 29 of 29 windows accounted for; room floor levels read from the mark in each room; membrane rolls in the released BOQ (each room / roof alone). NEW: the fix for the uncovered parapet-step upturn is built and waits for the checker (2F roof 0.84 m2 now covered by a 4.60 m strip; its count shown as 17 or 18 until you answer, every other roof and wet room unchanged); the hand plan of every wet room confirms 19 rolls. Next: rooms that vanish (a labelled W.C. under 1 m2, an unlabelled room) | at risk: one released roof count waits for the checker and your answer |
| 2 | Blockwork, plaster, paint, tiles, waterproofing, doors, windows within target | 11 Nov | membrane table, fold, cutting plan, window areas for 6 windows by hand, room levels with your wall-height rule, the tiling table, plaster / paint per room by hand and the tile count merged (tiles held: no printed size; offcut rule asked). NEW: blockwork started for the first time (wall metres per floor and thickness by hand and in code; the block height asked you) | started |
| 3 | Structural: concrete census, rebar from schedules, formwork, excavation | 25 Nov | concrete ledger, footings by member, columns / necks, beams by hand, stairs by hand, beam fix, typed drawing values and plot-edge members merged. NEW: the beam fix is now read by a new concrete ledger (waits for the checker): beams 68.84 vs his 65.97 m3, but 18 pieces still held, so the beam line is not compared yet (16 of them asked you); blinding by hand started (22.16 vs his 47.06 m3). Released concrete still 92.77 vs 111.81 m3 | started |
| 4 | Read scanned and PDF plans | 9 Dec | the vector-PDF height reader is merged, but the Alsenan PDF sheets are scans; a scan reader that releases a number only when its dimension chain adds up exactly is now on the board | started (one task) |

## Engine vs freelancer BOQ: Alsenan Chalet (released concrete run, commit 8774071, unchanged; waterproofing released in ARCH_TAKEOFF_V2.11)
Since 06:20 three checked pieces were merged (roof cutting plans by hand, the typed drawing values file, plot-edge foundation
members); none changes a released quantity. Three more wait for the checker, whose code run was refused at 07:58: the
parapet-step membrane fix, the wet-room hand plans and the beam fix read by a new concrete ledger ("waits for checker" below).
"piece" = a merged, checked method piece run on the real drawing; "hand" = a reading of the drawing.
| Trade | Unit | Engine | Freelancer | Difference | Change since last report | Target | State |
|---|---|---|---|---|---|---|---|
| Concrete, 3 lines compared (footings, stairs + domes, pool) | m3 | 92.77 | 111.81 | -19.04 (-17.03 %) | none | within 2 % | released run unchanged; new pieces not wired |
| Isolated footings (hand = engine register) | m3 | 64.346 | 65.634 | -1.29 (-2.0 %) | none | within 2 % | engine right (freelancer counts one footing twice); F10 HELD with a designer request |
| Foundation straps (piece, merged; checker ran it on the drawing) | m3 | 3.390 | 3.3925 | -0.0025 (-0.07 %) | now confirmed by the checker (engine right) | within 2 % | the released run still gives 3.781: one strap runs into an open footing outline (+0.39); the new piece is not wired |
| Beams (new concrete ledger, waits for checker) | m3 | 68.84 released + 18 pieces held (4.25 - 9.18 m3 if counted) | 65.97 | +2.87 (+4.4 %) on the released part only; line not compared while 18 pieces are held | was 64.82 (-1.7 %): +4.018 m3, each by hand (B26 3.905 and B27 3.787 as single spans, B7 strip 0.255 + arc 0.066, 1F ring beams 0.755 + 0.900, upstands 0.240) | within 2 % | 2 pieces settled by printed sections (1.91 m3, on the board); 16 pieces the drawings contradict or leave unmarked: asked you |
| Neck-only columns CN (piece, merged) | m3 | 5 column lines now "not present" (were held); 6 necks 0.090 m2 each, height held | 0 columns; 0.810 m3 necks at an unprinted 1.50 m | columns agree; necks unresolved | merged (was waiting for the checker) | within 2 % | neck height waits for a printed founding level (your earlier answer) |
| Stairs (hand merged; code piece waits for checker) | m3 | main stair 5.011 (steps 1.386 + sloping slabs 2.885 + landings 0.740), now also from the code piece; entrance steps 0.357 (its sloping slab held: not printed), lobby steps 0.126 | main stair 8.131; entrance 1.411; round stair 5.510 | main stair -3.12 (-38.4 %) | code piece = hand (new) | within 2 % | his flights are longer than drawn; winder steps and the round stair asked you; the last riser inside the arrival slab (0.163 m3) asked you |
| Blinding (typed drawing values, merged, not wired) | m3 | 22.155 (from values read off the drawings, not released) | 47.055 | -24.90 (-52.9 %) | new row | within 2 % | the largest single concrete difference: hand reading per footing, beam and wall footing is on the board (which members he blinds, printed projection and thickness) |
| Pool | m3 | 3.50 (released) | 12.35 | -8.85 | none | within 2 % | volume from the printed sizes is on the board |
| Domes | m3 | none (your answer: not concrete) | 6.78 | rule difference | none | - | settled |
| Wet-area waterproofing floor, 17 areas (piece + hand) | m2 | 72.12 | 72.01 | +0.11 (+0.16 %) | none | within 3 % | not yet in the released BOQ (wiring is first on the board) |
| Wet-area upturn, walls only (piece) | lm | 125.57 (your doorway answer) | 144.61 (full boundary) | rule difference | now from the strip method on real rooms (hand 127.07) | within 3 % | full boundary 144.73 = his 144.61 (+0.08 %) |
| Wet-area membrane rolls to buy (released, your answer: each room alone) | rolls | 19 for 17 wet areas; 122.99 m of strips, 67.01 m left over | not given | not comparable | hand plan of every wet room (waits for checker): 19 = 19, strips 122.50 m (-0.4 %); with the pantry 21 rolls | exact | the only general gap: a wedge W.C. laid along its 45 deg wall saves 0.50 m of strip (same roll); queued after the membrane fix |
| Roof waterproofing membrane (released) | m2 | 204.11 (3 roofs drawn on plans) + the second-floor top roof as a HELD line (your answer); rolls released 31 (17 + 6 + 8), by hand 32 (8 + 6 + 18) | 285.00 | -80.89 (-28.4 %) | fix built (waits for checker): 2F roof covered completely, its count shown as 17 or 18 until you answer; 1 of 578 BOQ lines changes | within 3 % | 17 only if the 4.60 m parapet piece may come from that roof's own 0.70 m side trim (asked you) |
| Roof upturn (released) | lm | 181.59 | 194.00 | -12.41 (-6.4 %) | now released | within 3 % | top roof held (your answer) |
| Windows with a printed height, 6 of 29 (hand, merged) | m2 | 26.485 | 24.280 | +2.205 (+9.1 %) | was 4 of 29, 13.892 vs 14.350 | exact | engine right on 4 printed heights, 1 rule difference (curved window, your answer); 23 HELD (scans); the curved pool glazing is 6.57 m wide by your answer, height 4.30 m |
| Windows counted | pcs | 29 (27 measured + 2 held) | 29 | 0 | none | exact | - |
| Doors, windows (aluminium) | m2 | windows 26.49 of 116.9; doors: main entrance 2.00 x 2.50 = 5.00 only | 116.9 / 12.0 | not comparable yet | windows from 13.89 | exact | no other door height is printed: asked you |
| Floor-to-floor heights (piece) | m | GF 4.50, 1F 4.20, 2F 4.20 (your answer: +9.70 to +13.90) | not in his BOQ | - | 2F now given by you | exact | - |
| Plaster / paint wall height (your rule) | m | GF 3.65 (3.60), 1F and 2F 3.35 (3.30) | not in his BOQ | - | new rule | exact | rework of the finish-height piece on the board |
| Rebar | t | not re-measured | 44.19 (earlier) | earlier estimate 26.24 t (-40.6 %) | none | within 3 % | not started |
| Blockwork | m | not measured yet | - | earlier estimate about 140 m short (-36.5 %) | NEW: wall metres per floor and thickness by hand and in code are on the board | within 3 % | metres first; block m2 needs your height answer (asked) |
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

- A new ledger version must be judged against the released run, not only against the ledger under it: the beam fix adds
  4.02 m3, but the new ledger also carries older holds, so its released concrete over all items is 229.57 m3, not 236.27.
- Two pieces of the drawings settle beams by themselves: sections A-A and B-B cut the B20 and B23 west spans and print
  their sizes; a third of the held beam pieces are contradictions only the designer or you can settle.

## Being worked on now
- Waiting for the checker (its code run was refused at 07:58; first at its next run): the parapet-step membrane fix
  (2F roof held at 17 / 18 rolls), the wet-room hand plans (19 rolls confirmed) and the new concrete ledger with the beam
  fix (beams 68.84 vs his 65.97 m3).
- Also waiting for the checker: stair concrete in code (main stair 5.011 m3 = the hand figure; his 8.131 m3).
- Free for workers whose code runs pass: rooms that vanish (labelled faces under 1 m2, unlabelled rooms), blockwork
  centreline metres in code, beam spans settled by printed section cuts (1.91 m3), pool and dome sizes from the printed
  details, the scan reader.
- Free for workers whose code runs are refused (hand work): blockwork metres per floor and thickness, blinding and columns
  by hand (22.16 vs his 47.06 m3), the list of printed finishing notes, tile sizes and door heights, and the check of ten
  older engine changes against the drawing.
- Queued: typed drawing values into the concrete ledger (after the beam ledger and the blinding hand table); plaster and
  paint into the released BOQ (after the membrane fix and your height answers); membrane strips along a 45 deg wall.
- Research scout (next run 23:50 UTC): Arabic / English notes on scans; proving strip coverage; wall centrelines from
  double-line walls (new).

## What is missing
- The checker's verdict on the membrane fix, the wet-room hand plans and the beam ledger (refused at 07:58).
- 16 beam pieces the drawings contradict or leave unmarked (asked you); 2 more need the section-cut piece (on the board).
- Blockwork: never measured; metres now on the board, block height asked you.
- Blinding: 22.16 vs his 47.06 m3, not explained yet (hand reading on the board).
- Opening heights for 23 windows (scans) and all doors but the main entrance (not printed: asked).
- Tile sizes per room (none printed) and the offcut rule (asked).
- The beam depth for your wall-height rule, the annex slab height and a ceiling rule (asked).
- Screed thickness on roofs and balconies; marble adhesive coverage; expansion-joint spacing (asked later).
- The second-floor top roof outline (held by your answer).
- The Kuwait specification chapters on waterproofing, floors, wall tiles and paint (file too big: parts needed).

## Waiting for the owner
- NEW: stairs: the last riser of a flight sits inside the slab it arrives on (0.163 m3 on Alsenan): measure each flight to
  the face of the slab or landing (recommendation; main stair 5.011 -> 4.951 m3), take it out of the slab instead, or count
  it twice as today.
- NEW: blockwork height: each wall up to the underside of the beam or slab above it (recommendation; GF 3.75 m under a
  20 x 75 beam, 4.34 m under slab only), one height per floor (slab to slab - 0.60 m: GF 3.90 m), or slab to slab minus
  the slab only (GF 4.34 m everywhere).
- NEW: 16 beam pieces the drawings contradict or leave unmarked (4.25 - 9.18 m3; beams 68.84 vs his 65.97 m3): hold and
  ask the designer for the unmarked ones, take the printed schedule width for CB10 (0.744 m3) and treat the two strips
  whose own section shows no concrete as not beams (recommendation); or count the bigger reading as provisional (+9.18 m3).
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
- Setting: run the four coding agents as Claude Code scheduled tasks with the repository attached (since 06:20, 3 of 6
  code runs were refused: the checker at 07:58, worker 2 at 07:06 and 07:43; one worker run left no log line).
- Upload the Kuwait specification chapters 07100, 09200, 09300, 09400, 09900 as separate PDFs under 6 MB.
