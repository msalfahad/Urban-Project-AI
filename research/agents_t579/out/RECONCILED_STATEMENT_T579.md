# T-579 reconciled-quantities statement V5 (generated; reference - engine, + = in the reference only)

V5 = statement V4 (T-570, rebuilt and equal to its committed output; 18 sections, only T-543/blockwork restated) + the sections below. Development villa; not an accuracy claim; nothing released.

## V4 sections (as carried)

| Section | Unit | Reference | Engine valued | Difference | UNRESOLVED |
|---|---|---|---|---|---|
| T-541/membrane | m2 | 285 | 209.65844 | 75.34156 | 0.523 |
| T-541/upturn | lm | 194 | 187.83416 | 6.16584 | 11.893 |
| T-534/stair-bed | m2 | 39.485 | 35.4313 | 4.0537 | 0 |
| T-543/blockwork | m2 | 1260.6895 | 467.7925 | 792.897 | 52.206437 |
| T-546/floor | m2 | 72.01 | 85.57571 | -13.56571 | 0 |
| T-546/upturn | lm | 144.61 | 126.072925 | 18.537075 | 1.6 |
| T-545/beams | m3 | 66.093875 | 66.321054 | -0.227179 | 0.120452 |
| T-547/wall-tile | m2 | 433.83 | 340.3038 | 93.5262 | 0 |
| T-552/plaster-internal | m2 | 1209.385 | 240.2781 | 969.1069 | 46.89 |
| T-552/plaster-external | m2 | 1502.84 | 0 | 1502.84 | 79.7435 |
| T-551/columns | m3 | 28.5465 | 19.7765 | 8.77 | -0.435 |
| T-551/necks | m3 | 8.805 | 0 | 8.805 | 0 |
| T-551/lift-walls | m3 | 2.4 | 0 | 2.4 | 0 |
| T-551/footing-line | m3 | 77.6305 | 67.6945 | 9.936 | 0 |
| T-551/blinding | m3 | 47.055 | 12.734438 | 34.320562 | 0 |
| T-553/floor-tile | m2 | 409.58 | 387.09405 | 22.48595 | 2.804722 |
| T-561/paint-internal | m2 | 1209.385 | 217.2081 | 992.1769 | 46.89 |
| T-561/stair-soffit | m2 | 39.99 | 0 | 39.99 | 17.840966 |

T-543/blockwork restated by T-568 (F-T579-1, class only, deltas unchanged): the 8 T-559 opening rows (+6.30 m2) UNRESOLVED -> ENGINE_RIGHT +6.54 / RULE_DIFFERENCE -0.24; section classes now ENGINE_RIGHT 113.541080, ENGINE_WRONG 0, HELD 561.2232755, RULE_DIFFERENCE 67.945508, TOLERANCE -2.0193005, UNRESOLVED 52.206437.

## New sections (V5)

| Section | Kind | Unit | Reference | Engine valued | Difference | % of ref. | By class (non-zero; net / gross abs) |
|---|---|---|---|---|---|---|---|
| T-560/rebar | DIFFERENCE | t | 44.190000 | 9.375306 | 34.814694 | none | RULE_DIFFERENCE 34.814694 / 34.814694 |
| T-568/alu-doors-nr | DIFFERENCE | nr | 5 | 6 | -1 | -20.00 | ENGINE_RIGHT -1 / 1 |
| T-568/alu-doors-m2 | DIFFERENCE | m2 | 12.0 | 12.76 | -0.76 | -6.33 | ENGINE_RIGHT -1.720 / 2.680, RULE_DIFFERENCE 0.960 / 0.960 |
| T-568/windows-nr | DIFFERENCE | nr | 29 | 28 | 1 | none | HELD 1 / 1 |
| T-568/windows-m2 | DIFFERENCE | m2 | 116.900 | 76.256 | 40.644 | none | ENGINE_RIGHT 3.975 / 7.615, HELD 36.669 / 36.669 |
| T-568/internal-doors-nr | CROSS_REFERENCE_COUNT_CHECK | nr | 18 | 15 | 3 | none | ENGINE_RIGHT -2 / 2, HELD 5 / 5 |
| T-568/internal-doors-m2 | CROSS_REFERENCE_COUNT_CHECK | m2 | 36.96 | 28.60 | 8.36 | none | ENGINE_RIGHT -3.960 / 3.960, HELD 9.84 / 9.84, RULE_DIFFERENCE 2.480 / 2.480 |
| T-572/measured-columns_GF | LIKE_FOR_LIKE_MEASURED_SET | m3 | 11.531250 | 12.705000 | -1.173750 | -10.18 | ENGINE_RIGHT 0.860000 / 1.202500, RULE_DIFFERENCE -1.883750 / 1.883750, UNRESOLVED -0.150000 / 0.150000 |
| T-572/measured-columns_1F | LIKE_FOR_LIKE_MEASURED_SET | m3 | 2.553000 | 3.108000 | -0.555000 | -21.74 | ENGINE_RIGHT -0.095000 / 0.095000, RULE_DIFFERENCE -0.385000 / 0.385000, UNRESOLVED -0.075000 / 0.075000 |
| T-572/measured-footing_pads_and_straps | LIKE_FOR_LIKE_MEASURED_SET | m3 | 67.066500 | 67.694500 | -0.628000 | -0.94 | - |
| T-572/measured-necks | ONE_SIDED | m3 | 8.805000 | AT_LEAST 8.869500 (high OPEN) | none | none | BELOW_DRAWN_LOWER |
| T-573/ceiling-board | DIFFERENCE | m2 | 409.58 | 366.891177 | 42.688823 | none | ENGINE_RIGHT -0.1162 / 30.0030, HELD 36.5200 / 36.5200, TOLERANCE 0.124317 / 0.803981, UNRESOLVED 6.160706 / 6.160706 |
| T-573/ceiling-cove | DIFFERENCE | lm | 427.46 | 0 | 427.46 | none | UNRESOLVED 427.46 / 427.46 |
| T-573/ceiling-stair-soffit | CROSS_REFERENCE | m2 | counted in T-561/stair-soffit | | | none | |
| T-573/ceiling-exterior-soffit | CROSS_REFERENCE | m2 | counted in T-552/plaster-external (his row 73: RULE_DIFFERENCE 12.834; ENGINE_RIGHT 6.32) | | | none | |
| T-573/ceiling-paint | DIFFERENCE | m2 | 452.325 | 394.825677 | 57.499323 | none | ENGINE_RIGHT -0.1162 / 0.1162, HELD 36.5200 / 36.5200, RULE_DIFFERENCE 42.745 / 42.745, TOLERANCE 0.124317 / 0.124317, UNRESOLVED -21.773794 / 34.095206 |

### B11 reinforcement (T-560, t; TYPED_LUMP: RULE_DIFFERENCE, quantity UNRESOLVED, no %)

| Group | His (t) | Engine valued | Engine held range | Held blank | His - valued | Residual after bounded held | Omission of a line |
|---|---|---|---|---|---|---|---|
| G1_SUBSTRUCTURE | 15.550000 | 2.317147 | 4.039645 .. 5.105957 | 196 | 13.232853 | 8.126896 .. 9.193208 | - |
| G2_COLUMNS_NECKS_WALLS | 7.950000 | 1.887128 | 1.280992 .. 2.119349 | 238 | 6.062872 | 3.943523 .. 4.781880 | lift-pit walls |
| G3_BEAMS | 9.890000 | 5.171031 | 4.247223 .. 6.120242 | 128 | 4.718969 | -1.401273 .. 0.471746 | - |
| G4_SLABS | 5.400000 | 0 | 3.671229 .. 4.857659 | 199 | 5.400000 | 0.542341 .. 1.728771 | - |
| G5_STAIRS_DOME | 3.900000 | 0 | 1.039160 .. 1.443671 | 17 | 3.900000 | 2.456329 .. 2.860840 | dome shells + rings |
| G6_POOL | 1.500000 | 0 | none | 20 | 1.500000 | 1.500000 .. 1.500000 | - |
| Total | 44.190000 | 9.375306 | 14.278249 .. 19.646878 | 799 (incl. tank 1) | 34.814694 | | |

Tank: his NO_ROW, NOT_COMPARABLE.

Windows like for like (T-568): 80.231 vs 76.256 m2 on 27, difference 3.975 (4.95 % of ref.; engine vs reference -4.95 %); EXPECTED after the V8 W17 row (beside only): 89.681 vs 86.126 on 28 (-3.96 %).

### B10 / B1 HELD bounds (T-572, m3, engine side; a one-sided end is AT_LEAST, high OPEN)

| Family | V4 section | Valued | Held n | Both ends drawn | Lower end only | No drawn bound | Family held |
|---|---|---|---|---|---|---|---|
| B10 COLUMN | T-551/columns | 19.776500 | 29 | 15: 8.034000 .. 10.119000 | 0 | 14 | not stateable |
| B10 NECK | T-551/necks | 0.000000 | 36 | 0: none | 36: AT_LEAST 9.723900 | 0 | AT_LEAST 9.723900 |
| B10 LIFT | T-551/lift-walls | 0.000000 | 2 | 0: none | 1: AT_LEAST 1.903000 | 1 | not stateable |
| B10 FOOTING LINE | T-551/footing-line | 67.694500 | 5 | 4: 7.844500 .. 13.961300 | 0 | 1 | not stateable |
| B10 BLINDING (plain) | T-551/blinding | 12.734438 | 6 | 5: 7.640374 .. 13.466198 | 0 | 1 | not stateable |
| B1-02 EXCAVATION | not_comparable:T-565 | 225.941333 | 10 | 1: 1.069269 .. 1.176467 | 4: AT_LEAST 37.575000 | 5 | not stateable |
| B1-03 BACKFILL | not_comparable:T-565 | 0.000000 | 7 | 0: none | 3: AT_LEAST 99.645011 | 4 | not stateable |
| B1-04 DISPOSAL | not_comparable:T-565 | 0.000000 | 1 | 0: none | 0 | 1 | not stateable |

T-572/measured-columns_GF: like for like -1.173750 m3 (-10.18 % of ref.), net of RULE_DIFFERENCE (JOINT_HEAD) 0.710000 (6.16 %).
T-572/measured-columns_1F: like for like -0.555000 m3 (-21.74 % of ref.), net of RULE_DIFFERENCE (JOINT_HEAD) -0.170000 (-6.66 %).

Ceiling board (T-573): headline -10.42 % engine vs reference is NOT a verdict; like for like 110.05 vs 109.691183 m2 (-0.33 %).

## NOT_COMPARABLE blocks (no difference, no %)

- T-565/earthworks (per family): reference NO_ROW
- T-560/rebar-tank (t): reference NO_ROW
- T-568/main-entrance (nr / m2): reference NO_ROW
- T-568/internal-doors-supply (nr / m2): reference NO_ROW (no supply row in his supply workbooks)
- T-568/lift-landings (nr / m2): reference his masonry deduction rows 3 nr / 7.2 m2 (terms of T-543/blockwork, R-T579-1 (f))
- T-573/ceiling-bulkhead (m2): reference NO_ROW (he lists no bulkhead)
- T-573/ceiling-dome (m2): reference NO_ROW

## Manifest V8 rows (beside; NOT candidate lines; valued columns unchanged)

| Row | Evidence status | Statement row | Switch condition |
|---|---|---|---|
| RETURN_PAINT_FACES | HELD (frame-covered depth not printed) | V4 T-561/paint-internal 'RETURN: return faces' (ENGINE_WRONG 23.07 m2, omission bound 0 .. 23.07) | the 30 FIN.PAINT return lines exist in the candidate (Gate B RETURN_PAINT_FACES): then the row restates ENGINE_WRONG -> HELD <= 23.07 (F-C-T570-1); until then it stays ENGINE_WRONG at the face area with the bound beside |
| FLOOR_CLASS_A08:1F-RFFE7AF | area DRAWING-CONFIRMED 2.970 m2; finish class ESTIMATED, NOT VERIFIED | V4 T-553/floor-tile beside expected_after_fix_T564 | label lands with the V7 package; EXPECTED stays beside, never valued |
| PIER_RETURNS_EXT | storey face DRAWING-CONFIRMED (length re-measured by the Checker 15:58, height from the printed levels); parapet face HELD (pier top not printed) | V4 T-552/plaster-external (engine 0, HELD) | none while the facade lines stay HELD (T-314) |
| W17_Q76A | ASSUMED - OWNER-APPROVED, source owner Q-76 A + Q-39 C | T-568/windows-m2 beside expected_after_V8_W17_row | the 1F settled line reads 33.155 in the candidate |
| REBAR_OMISSION | HELD blank (no figure, no bound): the omission is of a line, not of a measure | T-560/rebar G2 / G5 engine_omission_of_a_line | the rows exist: the omission note becomes 'HELD blank lines'; the group stays RULE_DIFFERENCE (TYPED_LUMP) |

Reclasses (R-T579-1): F-T579-1 T-543/blockwork openings GF: GF D-GF-03 vs his 1.00 x 2.40 / wid UNRESOLVED -> ENGINE_RIGHT -0.24; F-T579-1 T-543/blockwork openings GF: GF D-GF-09 (engine deducts; no unit UNRESOLVED -> ENGINE_RIGHT 1.98; F-T579-1 T-543/blockwork openings 20CM: 20CM D-GF-08 vs his 1.10 x 2.40 / UNRESOLVED -> RULE_DIFFERENCE -0.24; F-T579-1 T-543/blockwork openings 1F: 1F D-1F-03 vs his 0.90 x 2.40 / wid UNRESOLVED -> ENGINE_RIGHT 0.24; F-T579-1 T-543/blockwork openings 1F: 1F W18 (engine deducts; no unit of  UNRESOLVED -> ENGINE_RIGHT 1.08; F-T579-1 T-543/blockwork openings 1F: 1F D-1F-10 (engine deducts; no unit UNRESOLVED -> ENGINE_RIGHT 1.76; F-T579-1 T-543/blockwork openings 1F: 1F D-1F-02 (engine deducts; no unit UNRESOLVED -> ENGINE_RIGHT 2.2; F-T579-1 T-543/blockwork openings 1F: 1F his 0.60 x 0.80 (no engine openi UNRESOLVED -> ENGINE_RIGHT -0.48; F-T579-2 T-573/ceiling-cove his cornice runs (halls / rooms + kitchens / bat HELD -> UNRESOLVED 427.46; F-T579-3 T-573/ceiling-paint paint: bulkhead faces painted in ours; he paints NOT_IN_HIS_ROWS -> UNRESOLVED -27.9345.

Reports covered: T-541, T-534, T-543, T-550, T-546, T-542, T-545, T-547, T-552, T-551, T-553, T-556, T-559, T-561, T-564, T-565, T-566, T-567, T-560, T-568, T-569, T-572, T-573; pending: T-571, T-574.
