# T-090: plaster, paint and wall-tile m2 per Alsenan room under each wall-height option (hand table, NO REPO CODE)

Worker 3, 2026-10-20 01:00-02:00 UTC. Gate 2 (architectural coverage: plaster, paint). Development villa (Alsenan), NOT an
accuracy claim. Hand reading only: no engine module was run or changed (this run's `uv pip install` was refused, so no
repo code ran); nothing is released. One row per drawn room: `ROOMS_T090.csv` (32 rows, the same ids as T-088), produced
by `calc.py` (standard library; every input typed in it with its sheet). No client names, no coordinates, no images.

Purpose: the owner's height rule waits on Q-52 (no 0.60 m beam is drawn) and Q-54 (annex slab). This table turns his
answer into m2 the same hour: pick the option, read the column.

## 1. Rules applied (and nothing else)

| Item | Rule | Effect here |
|---|---|---|
| Wall height | owner heights rule 2026-10-19 21:40 (Q-43 answer): slab-to-slab - beam - 0.15 decor (Q-48 A) - 0.10 floor finishing | H per option below |
| Beam deducted | NO RULE: owner Q-52 (A 0.60 always; B deepest beam drawn at the room; C a beam deeper than 0.60 only where it crosses the ceiling, else 0.60) | three columns |
| Annex slab-to-slab | NO RULE: owner Q-54 (A +0.30 to +4.30 = 4.00 m; B hold) | the 6 annex rooms have numbers only under Q-54 A |
| Plaster and paint faces | UP-FIN-PAINT-001 (dry room: plaster + paint on the same face; wet room: full-height tile, no paint) | one m2 serves plaster and paint |
| Wet-room walls | UP-FIN-WALL-001, owner Q-48 A (tiles to the decor ceiling, same height) | wet rows give wall-tile m2, not plaster |
| Opening deductions | UP-GEN-003 (deducted where applicable) and UP-OPEN-SCHED-001 `wall_finish_deduction` = opening length x (min(head, H) - max(sill, 0)), OWNER_APPROVED; UP-CER-005 for wall tiles | applied only where width, sill and head are printed (T-083); doors: no height printed (Q-55), so every room's NET is HELD |
| Ceilings | URBAN-CEILING-QUANTITY-WITHOUT-MATERIAL@v1 (area published, finish BY_SPEC), UP-CEIL-001 | ceiling AREA given for the 6 closed dry rooms; plaster / paint ON a ceiling: no Urban rule, HELD |
| Held never 0 | UP-QTY-STATUS-001 | every unknown is HELD with its reason |

Rule note for the Lead (not an owner question): `URBAN-PLASTER-TO-MASONRY-TERMINATION@v1` (method register V1, listed in
V3 `v1_methods`) says internal plaster runs to the structural soffit, above a false ceiling. The owner's later explicit
statement (2026-10-19 21:40: "3.65 m, the height that plastering and paint count") gives plaster the same height as
paint. The owner decision governs (it is newer, explicit and outranks a method); please record that V1 method as
superseded for plaster height so a code task does not revive it.

## 2. Heights per option (m)

| Zone | Slab to slab | A (0.60) | B (deepest drawn) | C (deep beam crossing, else 0.60) |
|---|---|---|---|---|
| GF main house | 4.50 (A-A sheet 10, B-B page 11) | 3.65 | 3.50 with 0.75; 3.40 with 0.85; 3.75 with 0.50 | 3.65; 3.50 where a 0.75 crosses (core wash lobby); 3.40 where a 0.85 crosses (open room, pantry) |
| GF annex (Q-54 A only) | 4.00 (B-B page 11 "400") | 3.15 | 3.00 (all 0.75) | 3.15; 3.00 in the dewaneya (CB6 crosses) |
| 1F | 4.20 | 3.35 | 3.20 with 0.75; 3.45 with 0.50 | 3.35; 3.20 in the master bed room 380 x 430 (B19 0.75 crosses, diagonal) |
| 2F | 4.20 | 3.35 | 3.20 with 0.75 | 3.35 |

Note for the owner's reading of Q-52 C: the question's example names only the dewaneya and the saloon, but by the beam
table (T-088) option C also lowers the 1F master bed room 380 x 430 (B19 crosses it) and, for wall tiles, the GF core
wash lobby (B11) and the pantry (B27). Under option B the 0.50 m beams RAISE eight wet rooms (GF 3.75, 1F 3.45).

## 3. Dry rooms: plaster m2 = paint m2 (gross, before openings)

Lengths from printed dimensions only (T-088, re-checked: the five rectangles below were found on the architectural DXF
as dimension entities whose measured value equals the printed number, with wall-face linework on all four sides of each
at the dimensioned coordinates, 49-120 % of each side covered; the gaps are the openings). The same automatic check
(two perpendicular printed dimensions of the room's sizes on the same floor, wall-face lines on all four sides) found 9
wet rooms too (GF 150 x 210, 150 x 225, 130 x 150, 175 x 135; 1F both 245 x 205, 147 x 180, 210 x 225; 2F 300 x 185) and
the 1F master bed room 380 x 430; it did NOT find the GF basin space 110 x 135 as a closed rectangle (it is open to its
passage on one side), so its 4.90 m is an upper bound (the room is held on its level anyway). 15 of the 23 rooms with a
length are DXF-confirmed; the other 8 are the 7 T-074 hand traces (kitchen, two core wedges, wash lobby, master bath,
laundry, bath by the laundry) and the open basin space.

| Room | Printed length | Freelancer | A | B | C | Freelancer m2 | A vs him |
|---|---|---|---|---|---|---|---|
| GF dewaneya (annex) | 20.128 m (400 x 630, R1.10 corner) | 20.0 x 3.60 | 63.40 | 60.38 | 60.38 | 72.00 | -8.60 (-11.9 %) |
| GF driver (annex) | 12.50 (175 x 450) | 12.5 x 3.60 | 39.38 | 37.50 | 39.38 | 45.00 | -5.63 (-12.5 %) |
| 1F master bed 425 x 450 | 17.50 | 17.5 x 3.40 | 58.63 | 56.00 | 58.63 | 59.50 | -0.88 (-1.5 %) |
| 1F master bed 500 x 365 | 17.30 | 17.3 x 3.40 | 57.96 | 55.36 | 57.96 | 58.82 | -0.87 (-1.5 %) |
| 2F maid room 300 x 645 | 18.90 | 18.9 x 3.40 | 63.32 | 60.48 | 63.32 | 64.26 | -0.95 (-1.5 %) |
| **5 rooms, same walls** | 86.328 vs his 86.20 m | | **282.67** | **269.72** | **279.65** | **299.58** | A -16.91 (-5.6 %); B -29.86 (-10.0 %); C -19.93 (-6.7 %) |
| 1F master bed 380 x 430 | 16.20 (room rectangle) | 22.3 x 3.40 | 54.27 | 51.84 | 51.84 | 75.82 | allocation (below) |
| **6 rooms** | 102.528 m | | **336.94** | **321.56** | **331.49** | **375.40** | A -38.46 (-10.2 %); B -53.84 (-14.3 %); C -43.91 (-11.7 %) |
| 6 rooms + the 1.47 x 3.05 passage walls (2 x 3.05 printed) given to 1F-10 as he does | 108.628 m | | 357.38 | 341.08 | 351.01 | 375.40 | A -18.02 (-4.8 %); B -9.1 %; C -6.5 % |

The A-column sums reproduce the figures printed in Q-52 (282.67 / 269.72 / 279.65 m2): the question and this table agree.

Hand check (A): 20.128 x 3.15 = 63.403; 12.50 x 3.15 = 39.375; (17.50 + 17.30 + 18.90) x 3.35 = 179.895; 16.20 x 3.35 =
54.270; sum 336.943 m2.

HELD dry rooms (never 0), with his figure for the same part: GF open room (dining / reception / saloon: not closed,
reception double height under the 1F void; his 195.30), GF master bed room (1.85 m lobby and the wall stubs beside the
curved pool glazing not closed by printed runs; his 75.78), 1F corridor (open to stair and living), 1F east master bed
room (curved wall round W17 not dimensioned as a wall; his 74.46), 1F living area (open to the void and the curved stair;
his 140.88), stair halls GF / 1F / 2F (no owner height rule for a stair-shaft wall; his stair core 204.42 + stair wall
40.50 + 2F lobby 30.60). His "basins corridor" 31.79 and GF "wash" 24.30 are basin spaces: wet by owner Q-06, no plaster /
paint line (RULE_DIFFERENCE).

## 4. Openings (UP-OPEN-SCHED-001): what can be deducted

Printed in this table's rooms: W14 in the 1F master bed room 425 x 450 (2.45 x 1.60, sill 1.20, head 2.80 above +5.50:
inside every option's height): -3.92 m2 under A, B and C; W18 in the 1F sea-side bath (wall tile; 0.50 x 2.16, sill 0.84,
head 3.00): -1.08 m2. Every room also has at least one door, and no door height is printed except the GF main entrance
(owner Q-55), and the other windows of these rooms print no height (T-083): so the NET of every room is HELD. The
freelancer deducts his openings at HALF (116.495 m2 of openings, 58.2475 m2 deducted, 1 209.39 -> 1 151.14 m2): no Urban
rule deducts half; UP-OPEN-SCHED-001 deducts the full band (RULE_DIFFERENCE, recorded for the verifier). Door jamb / head
plaster (UP-FIN-PLASTER-001, his 15.96 m2) needs the door height too: HELD.

## 5. Ceilings

Ceiling area of the 6 closed dry rooms from the printed rectangles: 105.88 m2 (dewaneya 24.94 = 4.00 x 6.30 less the R1.10
corner 0.260; driver 7.875; 19.125; 18.25; 16.34; maid 19.35). Finish BY_SPEC (no drawing names gypsum or a ceiling
paint). Plaster or paint ON a ceiling: no Urban rule, HELD and listed. The freelancer paints the decor ceilings (rooms
337.57 + wet rooms 72.01 + cove light 28.29 + 14.46 = 452.33 m2): not comparable until a rule exists.

## 6. Wet rooms: wall-tile m2 (gross, before openings; same heights by Q-48 A)

15 wet rooms with a printed or hand-traced outline (T-074): A 450.10, B 445.88, C 448.67 m2. Held: pantry (open side,
Q-37), the two stair-core rooms GF-10 / GF-11 (level unclear, Q-43). Q-48's rough 453 m2 (17 rooms at A) is the same order.
The freelancer's wall tiles 433.83 m2 are one total, not per room: not compared room by room.

## 7. Against the freelancer, project level

Internal plaster 1 151.14 m2 and internal paint 1 191.13 m2 (his nets): engine HELD, not 0. What printed geometry can carry
today is 6 dry rooms, 336.94 m2 gross under A (321.56 B, 331.49 C) against his 375.40 m2 for the same rooms (31 % of his
1 209.39 m2 gross plaster rows). Change since the last report: none in released quantities (still held); new are the B and C
columns, the ceiling areas, the opening-deduction rule and the passage allocation, so the owner's Q-52 / Q-54 answer gives
m2 the same hour.

## 8. Who is right (proposals for the verifier)

- Lengths: driver, both 1F master bed rooms 425 x 450 / 500 x 365 and the maid room AGREE; dewaneya ENGINE_RIGHT +0.128 m
  (printed rectangle with its drawn R1.10 corner, he rounds 20.0).
- Heights 1F / 2F: RULE_DIFFERENCE (his flat 3.40 is not the owner's formula; 3.35 under A, -1.5 %).
- Heights GF annex: UNRESOLVED until Q-52 and Q-54 (his 3.60 is the main-house height on a storey printed 4.00 m high;
  3.15 under A + Q-54 A, -12 %).
- 1F master bed room 380 x 430: RULE_DIFFERENCE (he gives the two 3.05 m passage walls to the room; with them A is
  74.71 vs 75.82, -1.5 %).
- Opening deductions: RULE_DIFFERENCE (half vs full band).

## 9. Missing

Door heights (Q-55) for every net; the 7 not-closed rooms need the CAD outline (code task, T-081 rework / V2.9 faces) or a
rule for double-height and stair-shaft walls; Q-52 and Q-54 for every number above.
