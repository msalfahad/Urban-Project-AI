# Progress toward the goal (owner-facing; the Lead rewrites this every run)

Plain words, no task numbers. Measured numbers come from SCOREBOARD.md; anything not measured says so.
Last update: 2026-10-20 20:10 UTC (Lead). Previous version: 2026-10-20 18:20 UTC.

## Where we are on the five gates
| Gate | In plain words | Due | Done so far | State |
|---|---|---|---|---|
| 0 | Measure the engine against the freelancer on a real villa; synthetic test villas | 21 Oct | done: Alsenan measured on the newest code, capability matrix, synthetic villas with hand truth; the apartment waits by your order | done for Alsenan |
| 1 | No room, door or window missed; wet and dry rooms right (floor area, tiles, waterproofing) | 28 Oct | wet / dry within 0.2 % on Alsenan; 29 of 29 windows accounted for; room levels from the marks; membrane rolls released (each room / roof alone); rooms-that-vanish guard and two hand checks of 24 older engine changes merged (22 right). NEW: the checker read the drawing and confirmed the ground-floor facade run misses the 1.20 m open-air side passage (engine 98.887 vs 105.887 m, -6.6 %): fix checked and merged (= hand; not wired); NEW: the slab plans show the passage roofed over its whole length, so whether it is outside at all is asked of you. The first-floor living gap is traced to 0.0001 m2 (engine 44.869 vs 38.588 m2: stair openings and stair well counted as floor, plus a small engine defect on winder steps 0.296 m2): fix checked and merged (38.459 .. 38.979 m2 vs hand 38.588 .. 38.990; not wired); with your marble answer for the landing the porcelain becomes 33.584 .. 34.104 m2, room-by-room proof on the board | on track |
| 2 | Blockwork, plaster, paint, tiles, waterproofing, doors, windows within target | 11 Nov | membrane table, fold, cutting plan, strips along a room's own wall (wedge W.C. 5.95 -> 5.45 m = hand), window areas for 6 windows, room levels, tiling table, plaster / paint per room by hand, tile count, blockwork metres by hand and the centreline code piece merged. NEW: every wall typed white / black from the structural notes and your fallback (no architectural sheet names a block type); skirting: all 28 nets right, 17.04 m of deductions not listed (fix queued). NEW: the code wall run checked against the hand table wall by wall (merged): not ready, it runs walls across open floor (+16.63 m on GF) and misses doorways at free wall ends (-10.37 m); a corrected version is on the board; the glass walls (12.05 m) asked of you. Membrane release version built (2F roof 17, pantry 2), waiting for the checker to run it on the drawing; an audit of every roll count for an offcut booked twice is on the board | started |
| 3 | Structural: concrete census, rebar from schedules, formwork, excavation | 25 Nov | concrete ledger, footings, columns / necks, beams and stairs by hand, beam fix, typed drawing values, plot-edge members merged. NEW: blinding and columns by hand merged: the freelancer's blinding is a plate under the whole plot that no drawing shows; the engine counts 5 columns the upper slab plans do not draw. Next: columns to the deepest beam at each column (your existing rule), beam register, stairs flight by flight, beam / stair rework. Released concrete still 92.77 vs 111.81 m3 | started |
| 4 | Read scanned and PDF plans | 9 Dec | the vector-PDF height reader is merged, but the Alsenan PDF sheets are scans; a scan reader that releases a number only when its dimension chain adds up exactly is now on the board | started (one task) |

## Engine vs freelancer BOQ: Alsenan Chalet (released concrete run, commit 8774071, unchanged; waterproofing released in ARCH_TAKEOFF_V2.11)
Since 18:20 the checker merged the membrane purchase version as an opt-in candidate (2F roof 17 rolls re-placed by the
checker itself, pantry 2, wet 21) and sent the ceilings census back (pool-court void 3.689, not 4.373 m2). Three hand
results wait for it (landing / porcelain, facade passage condition, offcut-once audit). No released number changed. Your
20:10 decision: verified pieces now flow into ONE opt-in candidate (V3.0); the released default stays until you switch it.
"piece" = a merged, checked method piece run on the real drawing; "hand" = a reading of the drawing.
| Trade | Unit | Engine | Freelancer | Difference | Change since last report | Target | State |
|---|---|---|---|---|---|---|---|
| Concrete, 3 lines compared (footings, stairs + domes, pool) | m3 | 92.77 | 111.81 | -19.04 (-17.03 %) | none | within 2 % | released run unchanged; new pieces not wired |
| Isolated footings (hand = engine register) | m3 | 64.346 | 65.634 | -1.29 (-2.0 %) | none | within 2 % | engine right (freelancer counts one footing twice); F10 HELD with a designer request |
| Foundation straps (piece, merged; checker ran it on the drawing) | m3 | 3.390 | 3.3925 | -0.0025 (-0.07 %) | now confirmed by the checker (engine right) | within 2 % | the released run still gives 3.781: one strap runs into an open footing outline (+0.39); the new piece is not wired |
| Beams (new concrete ledger, sent back for one guard-test declaration, rework on the board) | m3 | 68.84 released + 18 pieces held (4.25 - 9.18 m3 if counted) | 65.97 | +2.87 (+4.4 %) on the released part only; line not compared while 18 pieces are held | was 64.82 (-1.7 %): +4.018 m3, each by hand (B26 3.905 and B27 3.787 as single spans, B7 strip 0.255 + arc 0.066, 1F ring beams 0.755 + 0.900, upstands 0.240) | within 2 % | 2 pieces settled by printed sections (1.91 m3, on the board); 16 pieces the drawings contradict or leave unmarked: asked you |
| Neck-only columns CN (piece, merged) | m3 | 5 column lines now "not present" (were held); 6 necks 0.090 m2 each, height held | 0 columns; 0.810 m3 necks at an unprinted 1.50 m | columns agree; necks unresolved | merged (was waiting for the checker) | within 2 % | neck height waits for a printed founding level (your earlier answer) |
| Stairs (hand merged; code piece = checker's own hand figure, sent back for one guard-test declaration) | m3 | main stair 5.011 (steps 1.386 + sloping slabs 2.885 + landings 0.740), now also from the code piece; entrance steps 0.357 (its sloping slab held: not printed), lobby steps 0.126 | main stair 8.131; entrance 1.411; round stair 5.510 | main stair -3.12 (-38.4 %) | code piece = hand (new) | within 2 % | his flights are longer than drawn; winder steps and the round stair asked you; the last riser inside the arrival slab (0.163 m3) asked you |
| Blinding (typed drawing values, not wired; hand reading merged) | m3 | 22.155 (hand range 20.71 - 26.37: footings 15.179 ready, under ground beams 5.53 - 9.69 by the founding level, straps 0.913 held) | 47.055 | -24.90 (-52.9 %) | NEW: cause found | within 2 % | his 47.055 is one 15.00 x 31.37 x 0.10 plate under the whole plot, drawn nowhere: engine right on basis. The engine releases footing F10's blinding (0.48) while F10 is held: fix in the ledger task. Strap blinding and blinding past the plot line: designer questions |
| Columns (hand, merged) | m3 | 36.711 (engine); hand 34.446 at the full storey height | 28.547 | engine +8.16 (+28.6 %); hand +5.90 (+20.7 %) | new row | within 2 % | engine counts 5 columns the first / second roof-slab plans do not draw (+2.27); the rest is height: he takes storey minus 0.75 m everywhere (hand at his heights 28.536, -0.04 %); the Urban rule takes the deepest beam at each column: column-by-column table on the board |
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
| Plaster / paint wall height (your rule) | m | your manual method: GF 3.65 (3.60), 1F and 2F 3.35 (3.30); drawing-derived per room: not measured yet | not in his BOQ | - | your correction: both methods shown side by side | exact | per-room table with both heights on the board |
| Facade run (pieces merged, not wired) | m | 1F 63.009 (released 63.169); GF released 98.887, merged piece 105.887 = hand (geometric perimeter); billable by your Q-64 B 105.787, reveal returns 0.100 apart | no run row (he prices exterior plaster per elevation) | 1F -0.160 (-0.25 %) = hand; GF engine -7.000 (-6.6 %) vs hand | NEW: GF fix checked and merged; the passage is roofed full length by the slab plans: outside or inside asked you (98.887 if inside) | exact | GF: the open-air side passage walls were missing; new finding: the first floor covers 4.08 m2 of that passage (soffit and slab over outside air measured nowhere: census on the board); a 0.10 m notch at the pool glass asked you (105.787 or 105.887) |
| Ceilings over outside air (hand, sent back by the checker) | m2 | 46.316 per the checker (porch 19.181, side passage 5.640, pool court 14.704 = 18.393 less the drawn opening 3.689, roof-slab edges 6.791); finish HELD (your Q-68 C: search the specification first, A only as provisional) | 19.154 (pool ceiling only) | pool court +4.450 (+30.3 %) over the checker's net; 31.612 m2 in neither BOQ | was 45.632 / pool 14.020: the void deducted was the engine's own face, not the drawn opening | exact | rework on the board: pool-court gross by hand from printed dimensions, finish evidence per place |
| Rebar | t | not re-measured | 44.19 (earlier) | earlier estimate 26.24 t (-40.6 %) | none | within 3 % | not started |
| Blockwork wall metres (hand, merged; code piece run on Alsenan, merged: 149.42 / 118.20 / 39.60, not ready to wire) | m | GF 143.16, 1F 120.75, 2F 39.78 (hand) | 134.28, 120.31, 39.10 | +8.88 (+6.6 %), +0.44 (+0.4 %), +0.68 (+1.7 %) | NEW: every wall typed: white 141.31 m and black 136.00 m by your fallback (ASSUMED), black 57.54 m by the structural note, 125.35 m held (parapets, street fence: asked you; sea-side 7.00 m) | within 3 % | GF over target: explained wall by wall, the two glass walls (12.05 m) are the whole gap: asked you; 3 walls drawn 0.15 hold a column the notes say must be built at column thickness (designer); he gives no block type on any row; a below-ground black block run (2 x 31.17 m) is in neither BOQ |
| Skirting (released run, audited by a merged-pending piece) | m | gross 262.56; certain net 185.52 (212.65 with held window edges) | 282.85 (gross, no door deduction) | gross -20.29 (-7.2 %) | new row | within 3 % | rule difference: your rule deducts doors, he does not; all 28 engine nets right, 17.04 m of window-frame credit not listed on the lines (listing fix queued) |
| Wall tile | m2 | not measured; wet walls about 447 - 473 m2 by hand depending on your tile-height answer | - | - | new estimate range (hand) | within 3 % | tile height asked you |
| Plaster | m2 | held | 1151.14 | - | none | within 3 % | waits on your beam-depth, annex and door-height answers; 6 closed dry rooms by hand: 336.94 (0.60 m always) / 321.56 (deepest beam) / 331.49 (deep beam where it crosses) vs his 375.40 m2 (-10.2 / -14.3 / -11.7 %); he deducts openings at half, your rule takes the full opening |
| Paint | m2 | held | 1191.13 | - | none | within 3 % | same walls as plaster; ceilings have no rule yet (he paints 452.33 m2 of decor ceilings): asked you |
| Dry-room floor tiles, 10 rooms (piece, merged) | m2 | 194.98 | 189.61 | +5.37 (+2.83 %) | NEW: fix merged: 1F living 38.459 .. 38.979 (candidate range) vs hand 38.588 .. 38.990; under your Q-66 B porcelain 33.584 .. 34.104 | within 1 - 2 % | first-floor living 44.869 vs hand 38.588 (38.990 if the foot of the east flight is landing) vs his 38.96: the engine counts the round-stair opening (2.10), the stair well (2.53) and the round-stair quarter landing (1.35) as floor, and loses 0.30 on winder steps; fix on the board. Landing finish: asked you (your two rules differ). Second-floor lobby 8.775 vs 7.70 engine right |
| Floor tile count per room (piece, merged) | tiles | held in all 25 floor rooms: no tile size printed on any Alsenan sheet; for 60x60 on 23 rooms 697 tiles without offcut reuse (+21 % over net m2) or 611 with reuse in the same room (+6 %) | not given | not comparable | new | exact | tile size per room and offcut reuse asked you |
| Stair marble (piece, merged) | m2 | 39.49 (treads, risers, landings) | 295.44, of which 151.80 is the court paving counted a second time; stairs and landings alone 143.64 | not comparable: his step rows are metres added to m2 | NEW: his double count found in his own formulas | exact | turning steps and round stair held (your answers pending) |
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

## Being worked on now
- Checker (next run 20:49; its 18:49 and 19:49 runs left nothing): three hand results in this order: first-floor living
  porcelain 33.594 .. 33.711 m2 with the landing marble once (4.875); the GF side passage shown open to outside air on the
  drawings (perimeter 105.887 m, billable 105.787 m once a reveal line holds the 0.100 m); every roll count re-checked so
  each leftover is used once (all released and proven counts valid). Then its own new task: a scoreboard per trade and unit
  with the independently verified share and the held share shown as unknown.
- Integration (worker 3's lane): build the ONE opt-in candidate V3.0 from the pieces the checker already merged (straps
  3.390 m3, GF facade passage walls, first-floor stair residue range, the membrane version), every changed line with before
  / after, drawing reference, both methods and the checker's evidence; then refresh the coverage registry. Worker 3 is
  finishing the beam member register by hand first (beams 68.84 released vs his 65.97 m3, 18 pieces held).
- Structural (worker 1's lane): blinding by member (footings 15.179 m3 ready, ground beams and straps held) and the 5
  columns no upper slab plan draws (-2.268 m3); columns to the deepest beam at each column (34.45 hand vs 28.55 his m3);
  stairs flight by flight; the beam / stair rework.
- Architecture and finishes (worker 2's lane): pool-court soffit by hand and the soffit finish search; the second-floor
  stair arrival (your Q-70 A: marble only if the geometry shows it is the landing; stair marble 49.240 m2 candidate);
  plaster and paint room by room by both methods; the corrected wall run with your five lengths (Q-69 B).
- Queued: block m2 / counts, skirting listing, mortar from the mix, typed values, scan reader; element register (design
  written, code after V3.0).
- Research scout (next run 23:50 UTC): Arabic / English notes on scans; proving strip coverage; wall centrelines.

## What is missing
- Ceilings over outside air: 45.632 m2 measured by hand (waits for the checker); finish asked you.
- Beam ledger and stair concrete back from rework; 16 beam pieces the drawings contradict or leave unmarked (designer list).
- Columns by the deepest-beam rule (table on the board); the engine's 5 undrawn columns removed when the ledger is rewired.
- Blockwork: the code on Alsenan, the walls that hold columns, block m2 / m3; parapet and street-fence block type (asked).
- Opening heights for 23 windows (scans) and every door but the main entrance (not printed).
- Tile sizes per room (none printed), ceiling layout, annex roof datum, round-stair section (designer list).
- Screed thickness on roofs and balconies; marble adhesive coverage; expansion-joint spacing (to ask later).
- The Kuwait specification chapters on waterproofing, floors, wall tiles and paint (file too big: parts needed).

## Waiting for the owner
- No question open: Q-67 (passage outside if the drawings confirm it: they do, the checker re-reads it), Q-68 (soffit
  finish from the specification, A provisional), Q-69 (physical block length beside the 143.16 m manual run) and Q-70
  (2F arrival marble if it is the landing) are answered and on the board. New decisions will come as one daily package.
- Setting (P-01): finish Test B and approve the repo-attached configuration; until then runs keep ending silently (the
  checker twice since 18:49, worker 3 once).
- Your confirmation of the reconciliation proposal (manual and drawing methods side by side); until then nothing released
  changes.
- Designer requests to forward when you choose: DESIGNER_CLARIFICATIONS.md.
- Upload the Kuwait specification chapters 07100, 09200, 09300, 09400, 09900 as separate PDFs under 6 MB (also needed for
  the soffit finish under your Q-68 C).
