# Progress toward the goal (owner-facing; the Lead rewrites this every run)

Plain words, no task numbers. Measured numbers come from SCOREBOARD.md; anything not measured says so.
Last update: 2026-10-21 08:20 UTC (Lead). Previous version: 2026-10-21 06:30 UTC.

## Where we are on the five gates
| Gate | In plain words | Due | Done so far | State |
|---|---|---|---|---|
| 0 | Measure the engine against the freelancer on a real villa; synthetic test villas | 21 Oct | done: Alsenan measured on the newest code, capability matrix, synthetic villas with hand truth; the apartment waits by your order | done for Alsenan |
| 1 | No room, door or window missed; wet and dry rooms right (floor area, tiles, waterproofing) | 28 Oct | wet / dry within 0.2 % on Alsenan; 29 of 29 windows accounted for; room levels from the marks; membrane rolls released (each room / roof alone); rooms-that-vanish guard and two hand checks of 24 older engine changes merged (22 right). NEW: the checker read the drawing and confirmed the ground-floor facade run misses the 1.20 m open-air side passage (engine 98.887 vs 105.887 m, -6.6 %): fix checked and merged (= hand; not wired); NEW: the slab plans show the passage roofed over its whole length, so whether it is outside at all is asked of you. The first-floor living gap is traced to 0.0001 m2 (engine 44.869 vs 38.588 m2: stair openings and stair well counted as floor, plus a small engine defect on winder steps 0.296 m2): fix checked and merged (38.459 .. 38.979 m2 vs hand 38.588 .. 38.990; not wired); with your marble answer for the landing the porcelain becomes 33.584 .. 34.104 m2, room-by-room proof on the board | on track |
| 2 | Blockwork, plaster, paint, tiles, waterproofing, doors, windows within target | 11 Nov | membrane table, fold, cutting plan, strips along a room's own wall (wedge W.C. 5.95 -> 5.45 m = hand), window areas for 6 windows, room levels, tiling table, plaster / paint per room by hand, tile count, blockwork metres by hand and the centreline code piece merged. NEW: every wall typed white / black from the structural notes and your fallback (no architectural sheet names a block type); skirting: all 28 nets right, 17.04 m of deductions not listed (fix queued). NEW: the code wall run checked against the hand table wall by wall (merged): not ready, it runs walls across open floor (+16.63 m on GF) and misses doorways at free wall ends (-10.37 m); a corrected version is on the board; the glass walls (12.05 m) asked of you. Membrane release version built (2F roof 17, pantry 2), waiting for the checker to run it on the drawing; an audit of every roll count for an offcut booked twice is on the board | started |
| 3 | Structural: concrete census, rebar from schedules, formwork, excavation | 25 Nov | concrete ledger, footings, columns / necks, beams and stairs by hand, beam fix, typed drawing values, plot-edge members merged. NEW: blinding and columns by hand merged: the freelancer's blinding is a plate under the whole plot that no drawing shows; the engine counts 5 columns the upper slab plans do not draw. Next: columns to the deepest beam at each column (your existing rule), beam register, stairs flight by flight, beam / stair rework. Released concrete still 92.77 vs 111.81 m3 | started |
| 4 | Read scanned and PDF plans | 9 Dec | the vector-PDF height reader is merged, but the Alsenan PDF sheets are scans; a scan reader that releases a number only when its dimension chain adds up exactly is now on the board | started (one task) |

## Engine vs freelancer BOQ: Alsenan Chalet (released concrete run, commit 8774071, unchanged; waterproofing released in ARCH_TAKEOFF_V2.11)
Since 06:30 (Lead 08:20): nothing was checked or merged: the checker ran three times and left no record, so eight
results now wait for it. New hand results this morning (waiting for the checker): columns to the deepest member at each
column 28.816 .. 28.979 m3 (his 28.547, +0.9 .. +1.5 %); block wall area gross 955.63 m2 (his 1,094.50, -12.7 %; with
the held walls at their candidate heights -5.3 .. -4.7 %); ground-beam spans split at the columns that stand on them
(bottom steel -43.96 kg, -3.5 %); the wall run version 2 (GF 134.56 m vs hand 143.16, -1.3 % once the pool glass line is
counted beside it). No released number changed; the released default stays until you switch it.
"piece" = a merged, checked method piece run on the real drawing; "hand" = a reading of the drawing.
| Trade | Unit | Engine | Freelancer | Difference | Change since last report | Target | State |
|---|---|---|---|---|---|---|---|
| Concrete, 3 lines compared (footings, stairs + domes, pool) | m3 | 92.77 | 111.81 | -19.04 (-17.03 %) | none | within 2 % | released run unchanged; new pieces not wired |
| Suspended slabs, 62 panels on the three roof-slab plans (hand, waiting for the checker) | m3 | engine slab faces 60.966; hand 60.280 (every panel matches an engine face within 0.002 m2) | 59.817 | hand +0.463 (+0.77 %); engine +1.149 (+1.92 %) | NEW row | within 2 % | engine's extra 0.686 m3 is 13 faces that are not slab (edge strips, a beam span, a ring piece, slivers): being sorted; the held 2.740 m3 face is the west dome opening and ring, not slab; sunken-slab step edges HELD (drop not printed) |
| Isolated footings (hand = engine register) | m3 | 64.346 | 65.634 | -1.29 (-2.0 %) | none | within 2 % | engine right (freelancer counts one footing twice); F10 HELD with a designer request |
| Foundation straps (piece, merged; checker ran it on the drawing) | m3 | 3.390 | 3.3925 | -0.0025 (-0.07 %) | now confirmed by the checker (engine right) | within 2 % | the released run still gives 3.781: one strap runs into an open footing outline (+0.39); the new piece is not wired |
| Beams (new concrete ledger, MERGED 23:28 after its rework; not wired yet) | m3 | 68.84 released + 18 pieces held (4.25 - 9.18 m3 if counted) | 65.97 | +2.87 (+4.4 %) on the released part only; line not compared while 18 pieces are held | was 64.82 (-1.7 %): +4.018 m3, each by hand (B26 3.905 and B27 3.787 as single spans, B7 strip 0.255 + arc 0.066, 1F ring beams 0.755 + 0.900, upstands 0.240) | within 2 % | 2 pieces settled by printed sections (1.91 m3, on the board); 16 pieces the drawings contradict or leave unmarked: asked you |
| Neck-only columns CN (piece, merged) | m3 | 5 column lines now "not present" (were held); 6 necks 0.090 m2 each, height held | 0 columns; 0.810 m3 necks at an unprinted 1.50 m | columns agree; necks unresolved | merged (was waiting for the checker) | within 2 % | neck height waits for a printed founding level (your earlier answer) |
| Stairs (flight-by-flight ledger MERGED 04:03, checker re-measured one flight 0.7248 m3 and both arrival wedges; not wired yet) | m3 | main stair 4.920 by your method / 4.746 by the drawing (was 5.011: three arrival wedges now counted once); slab under the winders in no line: HELD 0.230 .. 0.250; entrance steps 0.357 (its sloping slab held: not printed), lobby steps 0.126 | main stair 8.131; entrance 1.411; round stair 5.510 | main stair -3.211 (-39.5 %) | was -3.12 (-38.4 %): wedges counted once; checker: engine right (his 5.3 m flights are on no drawing) | within 2 % | his flights are longer than drawn; winder steps and the round stair asked you; the last riser inside the arrival slab (0.163 m3) asked you |
| Blinding (piece, merged; checker re-measured) | m3 | 15.179 released under the 25 released footings (checker's own outline union 151.794 m2 x 0.10) + HELD: F10 0.480 .. 0.590, under ground beams 5.724 .. 9.423, under straps 0.772 (released run still 22.155) | 47.055 | not comparable: his figure is one plate under the whole plot, drawn nowhere (rule difference) | NEW: piece checked and merged | within 2 % | held parts wait on your Q-21 / Q-31 answers (C) and the designer; never shown as 0 |
| Columns (piece, merged; checker re-measured) | m3 | 34.446 (piece: the 5 occurrences no upper slab plan draws removed, -2.268); released run still 36.714 | 28.547 | piece +5.90 (+20.7 %); released +8.17 (+28.6 %) | NEW: piece checked and merged (engine right on the 5 columns); in the next candidate step | within 2 % | the rest is height: he takes storey minus 0.75 m everywhere; the Urban rule takes the deepest beam at each column: column-by-column table on the board |
| Columns to the deepest member framing into each column (hand, waiting for the checker; your rule) | m3 | 28.816 .. 28.979 (range = column C8 drawn 30x80 vs schedule 30x90, designer); the 5.467 m3 between the old and new heights is joint 4.264 + column heads 1.203, to become their own lines, not lost | 28.547 | +0.27 .. +0.43 (+0.9 .. +1.5 %) | NEW row | within 2 % | 33 columns calculated, 26 held on a held beam, a projection depth, the annex level or C8 |
| Pool | m3 | 3.50 (released) | 12.35 | -8.85 | none | within 2 % | volume from the printed sizes is on the board |
| Domes | m3 | none (your answer: not concrete) | 6.78 | rule difference | none | - | settled |
| Wet-area waterproofing floor, 17 areas (piece + hand) | m2 | 72.12 | 72.01 | +0.11 (+0.16 %) | none | within 3 % | not yet in the released BOQ (wiring is first on the board) |
| Wet-area upturn, walls only (piece) | lm | 125.57 (your doorway answer) | 144.61 (full boundary) | rule difference | now from the strip method on real rooms (hand 127.07) | within 3 % | full boundary 144.73 = his 144.61 (+0.08 %) |
| Wet-area membrane rolls to buy (released, your answer: each room alone) | rolls | 19 for 17 wet areas; 122.99 m of strips, 67.01 m left over | not given | not comparable | NEW: pantry cutting plan by hand merged: 2 rolls, so 21 with the pantry (your answer: waterproof it); release version on the board | exact | the only general gap: a wedge W.C. laid along its 45 deg wall saves 0.50 m of strip (same roll); now on the board |
| Roof waterproofing membrane (released) | m2 | 204.11 (3 roofs drawn on plans) + the second-floor top roof as a HELD line (your answer); rolls 8 + 6 released, 2F roof HELD 17 or 18; by hand 32 (8 + 6 + 18) | 285.00 | -80.89 (-28.4 %) | fix merged: 2F roof covered completely, its count shown as 17 or 18 until you answer; 1 of 578 BOQ lines changed | within 3 % | NEW: proven by hand and re-measured by the checker: with your answer (trim from the same roof) the 2F roof needs 17 rolls (strips stop at the opening edge, 16 flap pieces from its own roll ends; strict layout 18). Release version on the board; it stays opt-in until you confirm the reconciliation |
| Roof upturn (released) | lm | 181.59 | 194.00 | -12.41 (-6.4 %) | now released | within 3 % | top roof held (your answer) |
| Windows with a printed height, 6 of 29 (hand, merged) | m2 | 26.485 | 24.280 | +2.205 (+9.1 %) | was 4 of 29, 13.892 vs 14.350 | exact | engine right on 4 printed heights, 1 rule difference (curved window, your answer); 23 HELD (scans); the curved pool glazing is 6.57 m wide by your answer, height 4.30 m |
| Windows counted | pcs | 29 (27 measured + 2 held) | 29 | 0 | none | exact | - |
| Doors, windows (aluminium) | m2 | windows 26.49 of 116.9; doors: main entrance 2.00 x 2.50 = 5.00 only | 116.9 / 12.0 | not comparable yet | windows from 13.89 | exact | no other door height is printed: asked you |
| Floor-to-floor heights (piece) | m | GF 4.50, 1F 4.20, 2F 4.20 (your answer: +9.70 to +13.90) | not in his BOQ | - | 2F now given by you | exact | - |
| Plaster / paint wall height (both methods) | m | your manual method: GF 3.65, annex 3.15 (provisional), 1F and 2F 3.35; drawing-derived (hand, waiting for the checker): GF 4.09 .. 4.19, 1F / 2F 3.79 .. 3.89 to the decor ceiling | GF 3.60, upper 3.40 (flat) | drawing-derived is 0.44 .. 0.54 m higher everywhere: your 0.60 m beam allowance against the 0.16 m slab where no beam crosses | NEW: drawing-derived heights measured | exact | rooms under a roof wait on the roof level (designer); floor build-up not printed (0 .. 0.10 m range) |
| Facade run (pieces merged, not wired) | m | 1F 63.009 (released 63.169); GF released 98.887, merged piece 105.887 = hand (geometric perimeter); billable by your Q-64 B 105.787, reveal returns 0.100 apart | no run row (he prices exterior plaster per elevation) | 1F -0.160 (-0.25 %) = hand; GF engine -7.000 (-6.6 %) vs hand | NEW: GF fix checked and merged; the passage is roofed full length by the slab plans: outside or inside asked you (98.887 if inside) | exact | GF: the open-air side passage walls were missing; new finding: the first floor covers 4.08 m2 of that passage (soffit and slab over outside air measured nowhere: census on the board); a 0.10 m notch at the pool glass asked you (105.787 or 105.887) |
| Ceilings over outside air (hand, MERGED 04:03; checker re-measured the pool court 12.834 from the printed dimensions) | m2 | 44.446 (porch 19.181, side passage 5.640, pool court 12.834 = 16.525 gross less the drawn opening 3.690, 1F edges 4.374 + 2.417); opening heads and frame recess 1.665 listed apart; finish HELD (no note on any sheet; your Q-68 C, option A provisional only) | 19.154 (pool ceiling only) | pool ceiling his +6.320 (+49.2 % over hand): engine right | was 46.316 (checker basis that added the court walls' tops) | exact | finish waits on the Kuwait specification chapters / designer |
| Rebar | t | footings (piece MERGED 02:29): 0.875 t on 19 footings printed with a bar count + 2.743 .. 2.836 t HELD (your Q-71); ground beams and straps (hand, MERGED 05:07): 1.480 t net + laps / development 0.647 .. 1.195 t HELD + stock-length splices 0.018 .. 0.032 t HELD | footings + straps + ground beams one lump 5.8 t; total 44.19 t | not comparable (his lumps mix elements) | ground-beam steel now merged with its lap range | within 2 % | the drawing prints the lap rule (40 d / 70 d) but not which bars are in tension: a range, not a guess |
| Ground-beam spans split at the columns standing on them (code piece, waiting for the checker) | kg | ground-beam bottom steel 1,194.60 (was 1,238.56 by the released splitter, -43.96 kg, -3.5 %); 52 of 53 spans = the hand ledger within 0.3 mm | lump of another scope | not comparable | NEW row | - | two oblique straps HELD on their length (asked you Q-74) |
| Blockwork wall metres (hand, merged; code piece run on Alsenan, merged: 149.42 / 118.20 / 39.60, not ready to wire) | m | GF 143.16, 1F 120.75, 2F 39.78 (hand) | 134.28, 120.31, 39.10 | +8.88 (+6.6 %), +0.44 (+0.4 %), +0.68 (+1.7 %) | NEW: every wall typed: white 141.31 m and black 136.00 m by your fallback (ASSUMED), black 57.54 m by the structural note, 125.35 m held (parapets, street fence: asked you; sea-side 7.00 m) | within 3 % | GF over target: explained wall by wall, the two glass walls (12.05 m) are the whole gap: asked you; 3 walls drawn 0.15 hold a column the notes say must be built at column thickness (designer); he gives no block type on any row; a below-ground black block run (2 x 31.17 m) is in neither BOQ |
| Block wall area, gross before openings (hand, waiting for the checker; your Q-60 A height to the member above) | m2 | 955.63 measured (GF 460.07, 1F 371.83, 2F 123.73); with the held walls at their candidate heights 1,036.5 .. 1,042.7; m3 172.19; white blocks 2,512 (62.5x25) or 3,268 (60x20) | 1,094.50 (GF 515.40, 1F 441.41, 2F 137.70) | -138.9 (-12.7 %); with held walls -5.3 .. -4.7 % | NEW row | within 3 % | net area HELD: no rule deducts openings from block (asked you Q-73); black count HELD (block size, asked Q-75); 12.91 m of walls with no height (designer) |
| Skirting (released run, audited by a merged-pending piece) | m | gross 262.56; certain net 185.52 (212.65 with held window edges) | 282.85 (gross, no door deduction) | gross -20.29 (-7.2 %) | new row | within 3 % | rule difference: your rule deducts doors, he does not; all 28 engine nets right, 17.04 m of window-frame credit not listed on the lines (listing fix queued) |
| Plaster / paint, dry walls gross (hand, both methods, waiting for the checker) | m2 | your method: GF 391.17, 1F 375.03, 2F 107.92 (874.12 + stair shaft HELD); drawing-derived: 1,150.62 .. 1,177.59 whole house incl. the shaft | 1,209.39 gross plaster rows (paint 1,191.13) | drawing-derived -58.8 .. -31.8 (-4.9 .. -2.6 %); your method per floor: GF +0.8 %, 1F -15.0 % (his 1F open zone has 55.70 m of wall where the drawing has 38.61 m) | was held | within 3 % | nets (after doors and windows) wait on 18 window heights and arch heads; the stair shaft under your method asked you (Q-72) |
| Wall tile in wet rooms (hand, your method) | m2 | 483.44 (+2 rooms HELD on level); drawing-derived 546.24 .. 560.53 | 433.83 (one spatter area at 3.00 m flat) | +49.61 (+11.4 %) on your method; not comparable room by room | NEW | within 3 % | his total is one figure at a flat 3.00 m height |
| Ceilings (decor ceilings, bulkheads, coves) | m2 | not measured | 452.33 painted (comparison only) | - | none | within 3 % | your Q-57 answer gives the method; the room-by-room table is now on the board |
| Dry-room floor tiles, 10 rooms (piece, merged) | m2 | 194.98 | 189.61 | +5.37 (+2.83 %) | NEW: fix merged: 1F living 38.459 .. 38.979 (candidate range) vs hand 38.588 .. 38.990; under your Q-66 B porcelain 33.584 .. 34.104 | within 1 - 2 % | first-floor living 44.869 vs hand 38.588 (38.990 if the foot of the east flight is landing) vs his 38.96: the engine counts the round-stair opening (2.10), the stair well (2.53) and the round-stair quarter landing (1.35) as floor, and loses 0.30 on winder steps; fix on the board. Landing finish: asked you (your two rules differ). Second-floor lobby 8.775 vs 7.70 engine right |
| Floor tile count per room (piece, merged) | tiles | held in all 25 floor rooms: no tile size printed on any Alsenan sheet; for 60x60 on 23 rooms 697 tiles without offcut reuse (+21 % over net m2) or 611 with reuse in the same room (+6 %) | not given | not comparable | new | exact | tile size per room and offcut reuse asked you |
| Stair marble (piece, merged; flight-once piece merged 23:33: released tread marble 27.324 -> 20.424 m2 + 0 .. 3.450 held, steps 91.028 -> 68.028 lm + 0 .. 11.500 held) | m2 | 39.49 (treads, risers, landings) | 295.44, of which 151.80 is the court paving counted a second time; stairs and landings alone 143.64 | not comparable: his step rows are metres added to m2 | NEW: his double count found in his own formulas | exact | turning steps and round stair held (your answers pending) |
| Tiling materials (piece, PROVISIONAL) | bags / m3 | cement 80 - 111 bags, sand 10.91 - 15.21 m3, adhesive 58 bags of 20 kg | not given | - | new | - | provisional by your answer; stair bed held on the 1:3 question |
| Floor area | m2 | held | not compared | - | none | within 1 - 2 % | 11 labelled spaces held instead of lost; room-by-room table on the board |

## Engine vs freelancer BOQ: development project 2 (apartment)
Not measured, and paused by your order (Alsenan first).

## What the team has learned so far
- (21 Oct, 08:20) The column rule moves 5.467 m3 out of the column line, but it is not lost: it is exactly the joints
  (4.264) and the column heads (1.203), which no beam or slab line holds yet, so they must become their own lines. Block
  area to the member above each wall is 12.7 % under the freelancer, most of it his storey heights; the block BOQ cannot be
  finished until two of your rules exist (opening deduction, black block size).
- (21 Oct, morning) Measured room by room, your manual heights and the drawing-derived heights differ by the same
  0.44 .. 0.54 m everywhere: the 0.60 m beam allowance against a 0.16 m slab where no beam crosses the room; crossing
  beams are bulkheads, a ceiling item. Every room under a roof has the annex's level problem. The 62 slab panels agree
  with the engine to 0.002 m2; the engine's extra concrete is 13 faces that are not slab, so a slab face should be
  released only with slab evidence.
- (21 Oct, night) A candidate built on the newest opt-in version still has to show every line that differs from the
  RELEASED method, not only from the version under it; the checker counts 197 such lines. On Alsenan a printed beam
  section cut also crosses the 0.20 m projection strip, so "the one span at the printed width" decides, not "the span the
  cut crosses". Arabic notes on scans: free OCR misreads too much (published error rates 54 - 79 %); only closed lists
  (tile sizes, room names) checked by two readers may release a value.
- (20 Oct, late) A stair flight drawn on the upper floor plan for orientation is measured again by the released method
  (+3.45 m2 marble); the 2F "stair lobby 450 x 195" was two dimensions read as one room: the 1.95 m belongs to the stair's
  own dimension chain, so the arrival is landing. The freelancer's blinding plate covers the whole plot; the drawings give
  blinding only under footings, ground beams and straps.
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
- The whole Alsenan set prints no tile size, no floor finish, no skirting, no ceiling and no door schedule; the only
  door height is the main entrance (2.50 m), and the sanitary sheets say "not to scale". The roof falls are printed 1 %.
- The freelancer's stair marble (295.44 m2) contains the court paving (151.80 m2) a second time, by his own formulas.
- A new engine piece can pass all of its own tests and still break a repository-wide guard (two pieces this morning);
  every new piece now runs that guard before it is handed in.
- Blockwork by hand is close to the freelancer on the upper floors (+0.4 %, +1.7 %) and 6.6 % over him on the ground
  floor; the old "140 m short" figure was an artefact of the engine's face-band run (a centreline run fixes it on the
  test villas: 54.60 m vs 44.40 m).
- Two readers agreeing is not proof: the code's independent reader and the engine agree on the ground-floor facade, but a
  hand reading finds a 1.20 m open-air passage both of them bridge (+7.00 m). The checker now reads the drawing itself.

- The freelancer's blinding (47.06 m3) is a plate under the whole plot; the drawings blind only under footings and the
  four ground-beam sections (20.7 - 26.4 m3 by hand).
- No architectural sheet names a block type; the structural notes do (neighbour-side ground-beam walls black, walls that
  hold columns at column thickness), so a block-type reader must read the structural notes, decoding the CAD Arabic.
- A room's floor area can include the stair opening and stair well inside it: on the first floor that is 4.6 m2 of the
  6.3 m2 the engine gives too much.

- The second-floor roof needs 17 rolls under your trim answer only if the strips stop at the opening edge and the step
  band is covered by flap pieces from that roof's own roll ends; a layout that looks the same with full strips needs 18.
- An open-air passage can sit partly under the floor above: on Alsenan 4.08 m2 of the side passage is roofed by a
  first-floor bathroom and bedroom, an exterior ceiling and a slab over outside air that no BOQ line measures yet.

- A wall band can run across open floor: the code's wall run on the ground floor joins two walls 12.2 m apart and crosses
  both passage mouths, so a total close to the hand (+4.4 %) hid +16.6 m too much and -10.4 m too little.
- Two drawings can disagree on whether a space is roofed: the slab plan puts a panel over the part of the side passage
  the architectural reading called open to the sky; only reading the slab plan settles which outside spaces are covered.
- A roll count can book the same leftover twice: one fold method claimed 8 rolls where the pieces cannot fit; every
  proven count is being re-checked piece by piece.
- Where a ground-beam plan has no marks and the sections are chosen by span length, a column the splitter misses changes
  the bars, not only the length (three such columns on Alsenan); and the structural general notes carry the lap and
  development lengths, so a steel ledger is not complete until it has read them.

## Being worked on now
- Checker (next run 08:49): eight results wait, in this order: the coverage registry, the first candidate extension
  (columns -2.268 m3, blinding split into released and held lines; the checker must run it on the drawings itself),
  the slabs by hand, the columns by hand, then the ground-beam splitter, the wall run version 2, plaster / paint by both
  methods and the block area. Its last three runs left no record (see Waiting for the owner).
- Integration (worker 3): the element register (stable ids for rooms, walls, openings, membrane zones, footings and
  columns, each linked to its BOQ lines); then footing steel and membrane evidence into the candidate, after the checker.
- Structural (worker 1): the slab leftovers (a beam span with a 0.296 m3 register gap, sunken-slab edges, held edge
  strips); NEW column steel by bar population from the column schedule (the next rebar slice after the footings).
- Architecture and finishes (worker 2): window heights from the elevations and sections so the plaster / paint and
  block nets can be measured; ceilings room by room under your Q-57 answer (a category with no quantity yet).
- Research scout (next run 21 Oct 23:50 UTC): footing schedules from CAD tables; laps in bar schedules; NEW the exact
  measurement-standard clauses behind the block-opening and strap-length questions.

## What is missing
- Block walls: net area (openings rule, asked), black-block count (size, asked), wall tops under the dome openings and the lift tie beam (designer).
- Ceilings over outside air: area settled (44.446 m2); the finish has no note on any sheet (specification / designer).
- Slab under the main-stair winders (0.23 .. 0.25 m3) in no line yet; 16 beam pieces the drawings contradict or leave unmarked (designer list).
- Roof levels and roof build-up (rooms under a roof), decor-ceiling levels and floor build-up, sunken-slab drops: three new
  designer requests (D-39, D-40, D-41).
- Columns by the deepest-beam rule (table on the board); the engine's 5 undrawn columns removed when the ledger is rewired.
- Blockwork: the code on Alsenan, the walls that hold columns, block m2 / m3; parapet and street-fence block type (asked).
- Opening heights for 23 windows (scans) and every door but the main entrance (not printed).
- Tile sizes per room (none printed), ceiling layout, annex roof datum, round-stair section (designer list).
- Screed thickness on roofs and balconies; marble adhesive coverage; expansion-joint spacing (to ask later).
- The Kuwait specification chapters on waterproofing, floors, wall tiles and paint (file too big: parts needed).

## Waiting for the owner
- NEW today (one package with Q-71 and Q-72): Q-73 openings in block walls (A deduct every opening, recommended; B only
  openings over 0.50 m2; C none, gross 955.63 m2); Q-74 oblique strap length (A along the strap axis face to face,
  2.293 / 3.258 m, recommended; B projected 1.829 / 2.838 m; C centre to centre); Q-75 black block size (A the 40 x 20
  module of your 2025 sales order, 12.5 per m2, about 7,040 blocks on the gross black area, recommended; B another size;
  C keep the count held).
- Q-72 the main stair shaft under your manual plaster / paint method (A 136.14, B 163.93 .. 165.35 recommended, C 157.66 m2).
- Q-71 footing bars printed per metre (A 2,742.51, B 2,836.40 recommended, C 2,797.81 kg for the five footings).
- Setting (P-01): finish Test B and approve the repo-attached configuration. Since 06:30 the checker ran at 06:49 and
  07:49 and left no record at all (it also missed 05:49), and worker 3's 08:00 run had its board push refused after claiming its task;
  6 of 9 finished slots closed SUCCESS (67 %, target 90 %). My own first clone this run was refused "[Untrusted Code
  Integration]"; the docs-only clone worked.
- Your confirmation of the reconciliation proposal (manual and drawing methods side by side); until then nothing released
  changes.
- Designer requests to forward when you choose: DESIGNER_CLARIFICATIONS.md (new D-42 walls under the dome openings,
  D-43 lift tie-beam size, D-44 beam B15 upstand or downstand).
- Upload the Kuwait specification chapters 07100, 09200, 09300, 09400, 09900 as separate PDFs under 6 MB (also needed for
  the soffit finish under your Q-68 C).
