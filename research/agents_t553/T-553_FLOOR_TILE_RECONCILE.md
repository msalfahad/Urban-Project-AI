# T-553 B3 floor tile vs the freelancer, room by room and by tile size (research, unwired)

Worker 2 (lane A), 2026-11-06, claim 10:40 UTC. Files: `t553_floor_tile_reconcile.py` (R-T553-1, any villa),
`t553_inputs.py` (element ids; values read from the sha256-pinned line index, never typed; his cells by sheet row;
no coordinate, no client name), `t553_alsenan.py` (`--check` reproduces `out/FLOOR_TILE_RECONCILE_T553.json`),
`tests/t553_floor_tile_reconcile/` (24 tests incl. a drawing check on P7757.dxf). No engine module, method, rule /
knowledge version, registry or candidate file changed; no quantity moves. Drawing by Drive title only ("Alsenan
chalet project", P7757_DXF_COMPRESSED.zip -> P7757.dxf, decoded this run into .work/private).

## 1. Physical element, the two sides, and the size dimension

Element: the INSTALLED finished floor of every tiled interior room (dry porcelain, wet tile, or a floor whose finish
is not established), net of what another trade owns (stair footprint / arrivals B7, door thresholds B3-04, lift
thresholds B6) and of what is not floor (walls / columns inside a gross outline).

Candidate: V3.0.58 = V3.0.57 index for every floor line (T-507 moved roof WP only; the 58 floor tile lines are
identical V3.0.45 .. V3.0.57): FIN.FLOOR.PORCELAIN 305.020973 + WET_TILE 75.945577 + FINISH_HELD 6.1275 =
**387.094050 m2**, 1 HELD (GF-ST-CN 0 .. 0.23). Freelancer: tiles sheet H70 = D31 dry 337.57 + H65 wet 72.01 =
**409.58 m2** (cover B15, m2). His floor rows are installed m2: D = area, no multiplier, no waste (test).

Tile size: no row of his carries a size; the drawings print none (R-T455-3: 0 of 276 DXF texts). Every row on both
sides is TILE_SIZE_NOT_GIVEN, so the size table has one class. Areas do not depend on the size; adhesive (5 / 3 / 3 m2
per bag) and boxes stay HELD by size (FINISH_MATERIALS_TABLE_V4), never defaulted to 60 x 60.

## 2. Result: engine - freelancer = -22.485950 m2 (-5.49 %), split exactly, residual 0

| Cause | m2 | What it is |
|---|---|---|
| RULE_DIFFERENCE | -15.941912 | stair footprint GF round stair -6.124412 (UP-CER-001; B7 treads); arrivals 1F -4.9225 (Q-66 B) and 2F -4.875 (Q-70 A); lift-threshold certain parts 3 x -0.300 (UP-ELEV-005); basin reveal -0.220 (threshold piece); engine-only door strips +1.100 (GF 0.35, 1F 0.57, 2F 0.18) |
| HELD | -9.705 | GF garden band 9.101 + curb 0.604 (D-48 planter or floor), in his reception row; bound 0 .. +9.705 tile |
| ENGINE_WRONG | -2.970 | **F-T553-1**: 1F dressing 1.65 x 1.80 has no floor tile line (only ARCH.SPACE L-390e3b9f 2.970, ceiling and skirting present); his 'bed room 2' 19.46 = 16.34 + 2.97 + 0.15 exactly |
| ENGINE_RIGHT | -0.797732 | printed / drawn sizes vs his typed cells: walls / columns in his gross GF outline -0.880, maid 300 x 645 -0.23, GF master -0.110, dewaneya +0.100, 1F west +0.05, 500 x 365 -0.035, 10 wet rooms +0.307 |
| TOLERANCE | +0.028416 | his 2-dp truncation, each < 0.010 |
| UNRESOLVED | +6.900278 | GF stair-room floors +6.1275 (in none of his floor rows; material HELD); 1F curved room +1.726545 (T-218); his GF open room above the drawn outline -0.302303; 1F living row unsplit -0.326464; 2F corridor -0.325 |

Class: engine DRY 305.020973 / WET 75.945577 / FINISH_HELD 6.1275 vs his DRY 337.57 / WET 72.01. Two CLASS MOVES, zero
area effect: the open pantry 13.454868 (our WET, Q-37 A; his dry reception row) and **F-T553-2**: the GF kitchen
floor 9.630001 is coded FIN.FLOOR.PORCELAIN although its bed (BED.WET), membrane, threshold and owner scope (Q-30 A,
UP-WET-001) are wet and he lists it wet: T-218 proposal 1 was never integrated (adhesive / dry-wet subtotals only).

Corrected (F-T553-1 as a FIN.FLOOR.FINISH_HELD 2.970 line): 390.064050 vs 409.58 = -19.51595 (-4.76 %); with the
garden band as floor (D-48 upper end) 399.76905 (-2.40 %). Like for like (no RULE_DIFFERENCE, HELD, scope rows):
the 25 paired rooms differ by ENGINE_RIGHT + TOLERANCE + the three named UNRESOLVED remainders.

## 3. Room table (m2; his tiles-sheet row)

| Room | Engine | His (row) | Delta | Split |
|---|---|---|---|---|
| GF open room incl. pantry and entrance zone (7 lines) | 130.648285 | 147.96 (13 + 15) | -17.311715 | stair -6.124412, lift -0.300, band HELD -9.705, wall / columns -0.880, UNRESOLVED -0.302303 |
| GF dewaneya | 24.940332 | 24.84 (16) | +0.100332 | 4.00 x 6.30 less R1.10 corner (dims 568 / 57F) |
| GF master | 16.54964 | 16.66 (14) | -0.11036 | drawn face, two routes (T-153 / T-147) |
| GF driver | 7.875 | 7.87 (17) | +0.005 | 1.75 x 4.50 (53A / 5C9), TOLERANCE |
| GF stair room hall + lobby | 6.1275 | none | +6.1275 | UNRESOLVED (material HELD) |
| GF / 1F / 2F door strips | 0.35 / 0.57 / 0.18 | none | +1.10 | RULE_DIFFERENCE (UP-THR-001 dry) |
| 1F living | 33.411036 | 38.96 (21) | -5.548964 | arrival -4.9225, lift -0.300, UNRESOLVED -0.326464 |
| 1F curved room | 19.016545 | 17.29 (22) | +1.726545 | UNRESOLVED (T-218) |
| 1F 380 x 430 + strip OP-011 | 16.49 | 19.46 (23) | -2.970 | dressing ENGINE_WRONG |
| 1F 500 x 365 / west 425 x 450 | 18.215001 / 19.05 | 18.25 / 19 (24 / 25) | -0.034999 / +0.05 | column notches, printed |
| 2F maid | 19.350001 | 19.58 (28) | -0.229999 | printed 300 x 645 |
| 2F lobby | 2.2 | 7.7 (29) | -5.5 | arrival -4.875, lift -0.300, UNRESOLVED -0.325 |
| 17 wet rooms (incl. kitchen) | 72.120710 | 72.01 (42-63) | +0.110710 | as T-546 (same drawn faces): reveal -0.22, ENGINE_RIGHT +0.307294, TOL +0.023416 |

Stair marble is owned once: every B7 / B6 area is a component naming its line (8 owner lines, each once, test); no
FIN.MARBLE / FIN.STAIR line can enter the table. Outdoor (outside his 409.58): interlock 119.5416 + side-walk
porcelain 21.0142 + HELD pool deck 6.548912 / porch 10.6785 vs his one unsplit yard row 151.80 (interlock court, a
chalet: not tile, OWNER_RULE_OUTDOOR_FLOORS); only the side walk 21.0142 is tile; no pair is formed.

## 4. Verdict proposals (Checker)

- Dressing -2.970: ENGINE_WRONG (missing floor item; corrected quantity +2.970 FINISH_HELD, its dry bed with it).
- Kitchen code: ENGINE_WRONG on class only (0 m2): recode L-83609efc to FIN.FLOOR.WET_TILE (lane I).
- Stair / arrival / lift / reveal / strips: RULE_DIFFERENCE. Garden band: HELD (D-48). Sizes: ENGINE_RIGHT on printed
  dimensions. 0 FREELANCER_RIGHT. UNRESOLVED +6.900278 named in five parts (none chosen by figure).

## 5. Rule, lesson, what is missing

R-T553-1 (module docstring): floor tile lines only (stair marble as a named owned component, each owner line once);
installed only (procurement / waste / multiplier refused); size class with source or TILE_SIZE_NOT_GIVEN, sides must
match; UNRESOLVED named, never absorbed; totals from the pinned index (stale refused); completeness join (space with a
ceiling and no floor line). Lesson proposal (ERS s.7): *a space that carries ceiling, paint and skirting lines but no
floor line is a missing floor item; join the finish families by element before reconciling* (T-223 found it 14 days
ago; it is still absent); tests `test_completeness_join_*` (normal) + the Alsenan join (adverse: finds 1F-RFFE7AF).
Missing: GF master printed size not re-derived this run (two drawing routes used); the GF stair-room material and his
landing row; D-48; the curved room; tile sizes (no source) for adhesive / boxes.
