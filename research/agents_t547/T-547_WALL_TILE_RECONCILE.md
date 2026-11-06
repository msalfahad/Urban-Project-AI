# T-547 B4 wet-room wall tile vs the freelancer, room by room (research, unwired)

Worker 2 (lane A), 2026-11-06, claim 06:41 UTC. Files: `t547_wall_tile_reconcile.py` (R-T547-1, any villa),
`t547_inputs.py` (line ids / values, his cells by sheet row, faces / openings from the Checker-verified T-312 ledger;
no coordinate, no client name), `out/WALL_TILE_RECONCILE_T547.json`, `tests/t547_wall_tile_reconcile/` (16 tests incl.
a drawing check on P7757.dxf). No engine module, method, rule / knowledge version, registry or candidate file changed;
no quantity moves. Drawing by Drive title and handle only ("Alsenan chalet project", P7757_DXF_COMPRESSED.zip).

## 1. Physical element, the two sides, and the restatement

Element: porcelain on every inner face of a wet room from the finished floor to the underside of the 0.15 decor
ceiling (Q-48 A; owner formula slab-to-slab - 0.60 - 0.15 - 0.10: GF 3.65, 1F / 2F 3.35, G1), net of the part of each
opening inside the band (Q-73), open sides untiled (no wall). The 2026-11-02 height rule (plaster to the slab, paint to
the finished ceiling) does not move the tile top: tile ends at the decor ceiling (Q-48 A); the band above the ceiling is
backing / plaster, not tile.

Candidate: 18 FIN.WALL.TILE lines, **12 valued = 340.3038 m2, 6 HELD blank**; identical on V3.0.41 .. V3.0.58 (line
index V3.0.57; T-507's V3.0.58 moved only roof WP lines). Freelancer: his ceramic sheet, wet-room block rows 42-63, 17
rows, G = C (lm) x F (3.00) per room, **G66 = 433.83 m2** (to H72 'walls', unit m2: here his F is a height, unlike his
waterproofing sheet in T-546). Gap **-93.5262 m2 (-21.56 %)**, residual **0.0000**.

## 2. The gap by cause (exact; components fixed by R-T547-1 (b): length at his height, height on our face)

| Cause | m2 | What it is |
|---|---|---|
| HELD | -138.390 | his 6 rooms whose engine line is blank (annex x 4: tile top not established, +4.30 roof mark, G2 / Q-54 B; GF-10 / GF-11: floor level +0.30 or +1.00 not drawn, T-088). Not 0: each carries a bound (section 4) |
| RULE_DIFFERENCE | +75.536 | height owner 3.65 / 3.35 vs his flat 3.00 (printed nowhere) on 11 rooms +43.1934; open pantry +32.3422 (Q-37 A wet + UP-PANTRY-003; he keeps it in his dry reception row) |
| ENGINE_RIGHT | -30.672 | doors -23.100 (13 leaves x 2.20 head, Q-55 C) and windows -4.920 (9 windows, T-201 heads): he deducts no opening (Q-73); GF-14 open side to the stair hall 1.245 m x 3.00 = -3.735 (no wall); faces vs his rounded lm +1.083 (2F W.C. printed 185 -> 9.70 vs his 9.75: -0.15; the rest +0.036 .. +0.33) |
| TOLERANCE | +0.0002 | per-face 4-dp rounding of the lines (each < 0.0002) |

Like for like (11 rooms both value): 307.9616 vs 295.44, **+12.5216 m2 (+4.24 %)** = height +43.1934, openings
-28.020, open side -3.735, length +1.083, rounding +0.0002. Reproduces T-312 / T-315 exactly (no stale value).

## 3. Room table (m2; his row = ceramic sheet row)

| Room | Line | Engine | His (row) | Delta | Split |
|---|---|---|---|---|---|
| GF-12 wedge W.C. 289 | L-c3469447 | 25.3011 | 22.20 (46) | +3.1011 | len +0.042, h +4.8191, door -1.76 |
| GF-13 wedge W.C. 245 | L-a3cb2c8a | 22.6165 | 20.10 (45) | +2.5165 | len +0.33, h +4.4265, door -1.76, W06 -0.48 |
| GF-14 wash lobby | L-fa408571 | 26.6544 | 28.50 (42) | -1.8456 | open -3.735, len +0.036, h +5.37355, doors -3.52, rnd -0.00015 |
| GF-16 master bath | L-ca4e74c5 | 25.5912 | 22.80 (44) | +2.7912 | len +0.075, h +4.95625, door -1.76, W07 -0.48, rnd -0.00005 |
| 1F-02 west bath upper | L-a34d0920 | 27.9101 | 27.00 (58) | +0.9101 | h +3.15, door -1.76, W20 -0.48, rnd +0.0001 |
| 1F-03 west bath lower | L-88ed2535 | 27.9100 | 26.70 (59) | +1.2100 | len +0.30, h +3.15, door -1.76, W19 -0.48 |
| 1F-07 laundry | L-b2077eee | 52.5290 | 50.55 (60) | +1.9790 | len +0.27, h +5.929, doors -3.74, W21 -0.48 |
| 1F-08 W.C. 147 x 180 | L-1090bb5c | 19.6691 | 19.44 (57) | +0.2291 | len +0.18, h +2.289, door -1.76, W22 -0.48, rnd +0.0001 |
| 1F-09 bath by laundry | L-086e7220 | 23.2201 | 22.80 (56) | +0.4201 | h +2.66, door -1.76, W23 -0.48, rnd +0.0001 |
| 1F-12 east bath | L-82cd58d4 | 26.3051 | 26.10 (55) | +0.2051 | h +3.045, door -1.76, W18 -1.08, rnd +0.0001 |
| 2F-02 roof-floor W.C. | L-065bafe1 | 30.2550 | 29.25 (63) | +1.0050 | len -0.15, h +3.395, door -1.76, W28 -0.48 |
| GF-07 open pantry | L-f5c5a1a9 | 32.3422 | none | +32.3422 | SCOPE, RULE_DIFFERENCE (Q-37 A) |
| GF-02 / 03 / 05 / 06 annex | L-d0858b30 / L-96d9839b / L-88c11c5d / L-c330b8dc | HELD | 21.60 / 22.50 / 16.74 / 43.05 (51 / 50 / 49 / 48) | -103.89 | HELD, bound below |
| GF-10 / GF-11 stair core | L-1341e041 / L-de4088e7 | HELD | 18.60 / 15.90 (47 / 43) | -34.50 | HELD, bound below |

## 4. The six HELD lines, each bounded (outside both totals; never 0, never a released figure)

Each end is R-T547-1 (a) at a named height. Annex: upper end = owner formula with +4.30 as the highest possible
structural datum (3.15; a finished-roof reading can only lower it); lower end = the decor ceiling runs above the
highest opening head in the room (door 2.20 Q-55 C; kitchen W08 head 2.50 T-201). GF-10 / GF-11: the two drawn level
candidates under the 1F floor +5.50 by the owner formula: +1.00 -> 3.65, +0.30 -> 4.35 (W05 band moves with the floor).

| Room | lo | hi | his | Held by |
|---|---|---|---|---|
| GF-02 wash | 11.880 (H 2.20, arch at full band) | 20.920 (H 3.15, arch head 0) | 21.60 | G2 / Q-54 B; arch A-GF-01 head not printed |
| GF-03 W.C. | 14.740 | 21.865 | 22.50 | G2 / Q-54 B |
| GF-05 driver W.C. | 10.560 | 15.880 | 16.74 | G2 / Q-54 B |
| GF-06 kitchen | 31.7985 (H 2.50) | 41.2235 | 43.05 | G2 / Q-54 B |
| GF-10 W.C. 175 x 135 | 20.390 (+1.00) | 24.730 (+0.30) | 18.60 | T-088 floor level |
| GF-11 basin 110 x 135 | 12.840 (+1.00, doorway full) | 19.555 (+0.30, doorway head 0) | 15.90 | T-088 level; P-GF-01 head |
| **6 rooms** | **102.2085** | **144.1735** | **138.39** | |

Engine with the HELD bounds: **442.5123 .. 484.4773 m2 vs 433.83 (+2.00 % .. +11.67 %)**. In every annex room his
cell exceeds even our upper end (by 0.635 .. 1.8265): at 3.15 vs his 3.00 the height adds +0.84 .. +2.175 m2 (and the
faces +0.06 / +0.45 on GF-05 / kitchen) but the door / window deductions he omits (1.76 .. 4.4515 m2) are larger; so on the annex the direction is set (ENGINE below his)
whatever the roof datum turns out to be. GF-10 at either level is above his cell (+1.79 .. +6.13): his 3.00 is below
both owner heights.

Drawing check (own read this run, P7757.dxf, test): the printed DIMENSIONs of the HELD rooms exist with these values:
GF-10 726 = 1750 / 749 = 1350 -> 6.20 m; GF-11 70F = 1100 / 749 -> 4.90 m; GF-05 61E = 1300 / 658 = 1500 -> 5.60 m;
GF-03 5A4 = 2250 / 551 = 1500 -> 7.50 m; GF-02 5BD = 2100 / 551 -> 7.20 m; kitchen 523 = 2700, 635 = 3000, 641 = 1050
(its 14.50 m face is the T-312 walk, not a rectangle; not asserted). The nearest level marks to the GF-10 / GF-11
dimensions are +0.30 (4AC) and +1.00 (413) at 1.7 .. 3.8 m on both: the plan does not settle the level (T-088 stands).
Supporting indication only: at +0.30 the W05 head would sit 3.20 above the floor; at +1.00 it is 2.50, like every other
W-type window of the wet rooms (1.70 / 2.50).

## 5. Verdict proposals (Checker)

- Height (+43.1934): RULE_DIFFERENCE (Q-48 A owner tile top vs his flat 3.00).
- Openings (-28.020): ENGINE_RIGHT (Q-73 every actual opening; he deducts none).
- GF-14 open side (-3.735): ENGINE_RIGHT (no wall, no tile). Length (+1.083): ENGINE_RIGHT (printed / drawn faces).
- Pantry (+32.3422): RULE_DIFFERENCE (Q-37 A; T-546 class). 0 FREELANCER_RIGHT; 0 UNRESOLVED; HELD -138.39 bounded.

## 6. Rule, lesson, what is missing

R-T547-1 (module docstring): room-by-room split derived from the physical element (fixed component order; a line equal
to its gross area with openings refused; a line off F x H - openings by >= 0.010 refused; HELD = his whole cell as a
HELD component plus the engine's own sourced bound, never 0). Lesson proposal (ERS s.7): *a HELD line against a
freelancer cell is reported as HELD = his cell with the engine's own bound beside it, not dropped from the pair*
(the scoreboard's 'RANGE_OPEN, no %' hid that 138.39 of the 93.53 gap is HELD rooms, and that the open pair closes at
+2.00 .. +11.67 %); test: tests/t547 `test_held_is_never_zero_and_carries_its_bound` (normal) + HELD-with-0 refused
(adverse). Missing / named: the annex roof datum and GF-10 / GF-11 level (owner items already answered B / HOLD: no new
question); arch A-GF-01 and doorway P-GF-01 heads; open side 1.245 m (wall face, T-312) vs 1.256 m (floor edge, T-546),
0.011 m, two ledgers measure different edges, no line moves; F-T351-1 pantry face 10.491 vs 10.500 (+0.0328 m2) stays
open; the drawing-derived method stays HELD on every room (roof datum, sunken panels, T-209).
