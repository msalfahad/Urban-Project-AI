# Compare: ARCH_TAKEOFF_V3.0.88 + MAIN_CHAT_FIX_ROWS (18 rows applied, 23 skipped as older than the index) vs the freelancer (number (b))

REFERENCE ONLY, never engineering verification. Built by compare_md.py from the Compare sheet of build_boq.py (freelancer totals from RECONCILED_STATEMENT_T635 / T001C key map / BENCHMARK_NORMALISED; engine = this line index; class columns are the V12 statement split in the section's unit, not recomputed).

| Section | Trade (freelancer label) | Unit | Item codes | Freelancer | Engine now: calculated | Engine now: held low | Engine now: held high | Blank lines now | Difference (calc - freelancer) | % of freelancer (calc only) | ENGINE_RIGHT | ENGINE_WRONG | RULE_DIFFERENCE | HELD (V12) | UNRESOLVED (V12) | Reading |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T-541/membrane | B8 roof waterproofing | m2 | FIN.WP.ROOF | 285.00 | 324.09 |  |  | 0.00 | 39.09 | 13.7 | -5.55 | 0.00 | 45.99 | 34.39 | 0.52 | engine higher by 39.1 (13.7 %) |
| T-541/upturn | B8 roof waterproofing | lm | FIN.WP.ROOF_UPTURN | 194.00 | 228.99 |  |  | 0.00 | 34.99 | 18.0 | -6.25 | 0.00 | -27.79 | 28.30 | 11.89 | engine higher by 35.0 (18.0 %) |
| T-534/stair-bed | B7 stair marble bed | m2 | FIN.MARBLE.TREAD, FIN.MARBLE.RISER, FIN.MARBLE.LANDING |  | 64.88 |  |  | 0.00 |  |  | 4.08 | 1.44 | -14.87 | 13.40 | 0.00 | no freelancer row |
| T-543/blockwork | B9 blockwork | m2 | MAS.BLOCK | 1,260.69 | 981.35 |  |  | 0.00 | -279.34 | -22.2 | 113.54 | 0.00 | 67.95 | 561.22 | 52.21 | engine lower by 279.3 (22.2 %) |
| T-546/floor | B8 wet-room waterproofing | m2 | FIN.WP.FLOOR | 72.01 | 85.58 |  |  | 0.00 | 13.57 | 18.8 | -0.31 | 0.00 | -13.23 | 0.00 | 0.00 | engine higher by 13.6 (18.8 %) |
| T-546/upturn | B8 wet-room waterproofing | lm | FIN.WP.WALL_UPTURN | 144.61 | 31.69 |  |  | 0.00 | -112.92 | -78.1 | -0.52 | 0.00 | 3.56 | 13.90 | 1.60 | engine lower by 112.9 (78.1 %) [engine unit m2, his lm: not like for like] |
| T-545/beams | B10-07 beam concrete | m3 | STR.CONC.BEAM | 66.09 | 76.05 |  |  | 0.00 | 9.95 | 15.1 | -12.64 | 0.00 | 4.92 | 7.38 | 0.12 | engine higher by 10.0 (15.1 %) |
| T-547/wall-tile | B4 wet-room wall tile | m2 | FIN.WALL.TILE | 433.83 | 442.12 |  |  | 0.00 | 8.29 | 1.9 | 30.67 | 0.00 | -75.54 | 138.39 | 0.00 | engine higher by 8.3 (1.9 %) |
| T-552/plaster-internal | B5 wall plaster | m2 | FIN.PLASTER | 1,209.38 | 1,622.00 |  |  | 0.00 | 412.62 | 34.1 | -4.39 | 1.62 | 68.22 | 856.76 | 46.89 | engine higher by 412.6 (34.1 %) |
| T-552/plaster-external | B5 wall plaster external | m2 | FIN.EXT.FINISH, ARCH.FACADE, EXT.FENCE.PLASTER | 1,502.84 | 1,305.59 |  |  | 0.00 | -197.25 | -13.1 | 68.09 | 0.00 | 194.64 | 1,160.37 | 79.74 | engine lower by 197.2 (13.1 %) |
| T-551/columns | B10 column concrete | m3 | STR.CONC.COLUMN | 28.55 | 33.83 |  |  | 0.00 | 5.29 | 18.5 | 1.52 | 0.00 | -2.67 | 10.35 | -0.43 | engine higher by 5.3 (18.5 %) |
| T-551/necks | B10 neck concrete | m3 | STR.CONC.NECK | 8.80 | 10.34 |  |  | 0.00 | 1.54 | 17.4 | 0.00 | 0.00 | 0.00 | 8.80 | 0.00 | engine higher by 1.5 (17.4 %) |
| T-551/lift-walls | B10 lift pit wall concrete | m3 | STR.CONC.LIFT | 2.40 | 2.30 |  |  | 0.00 | -0.10 | -4.2 | 0.75 | 0.00 | 0.00 | 1.65 | 0.00 | engine lower by 0.1 (4.2 %) |
| T-551/footing-line | B10 footing line concrete (pads + straps + boundary band) | m3 | STR.CONC.FOOTING, STR.CONC.STRAP, STR.CONC.BOUNDARY_WALL | 77.63 | 79.09 |  |  | 0.00 | 1.46 | 1.9 | -0.63 | 0.00 | 0.00 | 10.56 | 0.00 | engine higher by 1.5 (1.9 %) |
| T-551/blinding | B10 blinding (plain concrete, never structural) | m3 | STR.CONC.BLINDING | 47.05 | 29.69 |  |  | 0.00 | -17.37 | -36.9 | 0.00 | 0.00 | 0.00 | 34.32 | 0.00 | engine lower by 17.4 (36.9 %) |
| T-553/floor-tile | B3 floor tile (installed) | m2 | FIN.FLOOR.PORCELAIN, FIN.FLOOR.WET_TILE, FIN.FLOOR.FINISH_HELD | 409.58 | 387.32 |  |  | 0.00 | -22.26 | -5.4 | 0.80 | 2.97 | 15.94 | 0.00 | 2.80 | engine lower by 22.3 (5.4 %) |
| T-561/paint-internal | B6 wall paint internal | m2 | FIN.PAINT | 1,209.38 | 828.81 |  |  | 0.00 | -380.58 | -31.5 | -4.39 | 23.07 | 69.85 | 856.76 | 46.89 | engine lower by 380.6 (31.5 %) |
| T-561/stair-soffit | B6 stair soffit paint (CEILING class, in his wall-paint rows 18-19) | m2 | FIN.STAIR.SOFFIT | 39.99 | 31.66 |  |  | 0.00 | -8.33 | -20.8 | 0.00 | 0.00 | 0.00 | 22.15 | 17.84 | engine lower by 8.3 (20.8 %) |
| CONC.GROUND | CONCRETE (key map T001C; total ground beams and ground slab) | m3 | STR.CONC.GROUND_BEAM, STR.CONC.GROUND_SLAB | 75.09 | 58.54 |  |  | 0.00 | -16.55 | -22.0 |  |  |  |  |  | engine lower by 16.5 (22.0 %) |
| CONC.SLAB | CONCRETE (key map T001C; slabs) | m3 | STR.CONC.SLAB | 59.82 | 60.28 |  |  | 0.00 | 0.46 | 0.8 |  |  |  |  |  | engine higher by 0.5 (0.8 %) |
| CONC.STAIR_DOME | CONCRETE (key map T001C; stairs + dome) | m3 | STR.CONC.STAIR, STR.CONC.DOME | 21.83 | 16.65 |  |  | 0.00 | -5.18 | -23.7 |  |  |  |  |  | engine lower by 5.2 (23.7 %) |
| CONC.POOL | CONCRETE (key map T001C; swimming pool) | m3 | STR.CONC.POOL | 12.35 | 7.43 |  |  | 0.00 | -4.92 | -39.8 |  |  |  |  |  | engine lower by 4.9 (39.8 %) |
| DOORS.ALUMINIUM | DOORS (key map T001C; total doors m2) | pcs | DOOR.EXTERNAL.ALUMINIUM | 12.00 | 6.00 |  |  | 0.00 | -6.00 | -50.0 |  |  |  |  |  | engine lower by 6.0 (50.0 %) |
| WINDOWS.ALUMINIUM | WINDOWS (key map T001C; total windows m2) | pcs | ARCH.WINDOW | 116.90 | 29.00 |  |  | 0.00 | -87.90 | -75.2 |  |  |  |  |  | engine lower by 87.9 (75.2 %) |

24 rows.

## Package lines of T-770 r11 not in the Compare sheet (no section / key; hand-added from the merged fix-row summaries)

| Item code | Unit | V3.0.87 | V3.0.88 | Label | Freelancer | Difference | Verdict proposal |
|---|---|---|---|---|---|---|---|
| FIN.CEILING.CORNICE | lm | 302.88 | 426.31 | ESTIMATE | 427.46 (dry 282.85 + wet 144.61) | -1.15 (-0.27 %) | open zones +123.43 FREELANCER_RIGHT (T-788 r2); residual within 1 % |
| FIN.WALL.TILE.EDGE door jambs | lm | HELD 0 .. 73.1 | 115.2 | DEFAULT | no row (T-368) | n/a | RULE_DIFFERENCE (scope) |
| FIN.FLOOR.FINISH_HELD stair corner | m2 | HELD 0 .. 0.23 | 0.23 | DRAWING-READ | inside his B3 floor tile | +0.23 into T-553 | below 1 % (materiality) |
| ARCH.SPACE (2 lines) | m2 | HELD 0.604 / 6.124 (low = high) | 0.604 / 6.124 | MEASURED | n/a (space areas) | n/a | points carried, no change in figure |
