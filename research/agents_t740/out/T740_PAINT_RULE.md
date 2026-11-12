# T-740 paint area rule UP-FIN-PAINT-002 1.0.0 on ARCH_TAKEOFF_V3.0.74 (generated; research, unwired)

Rule: paint m2 = plaster m2 of the same face - band above a false ceiling - tiled part; corners and edges are lm, never area. Ends paired by scenario (low with low).

## Totals (m2; FIN.PLASTER / FIN.PAINT, every non-excluded line once)

| | plaster | engine paint | rule paint |
|---|---|---|---|
| all | 1495.532957 .. 1690.753177 | 822.198159 .. 927.214521 | 841.260635 .. 929.204847 |
| 1F | 654.887610 .. 678.321310 | 370.157300 .. 386.529400 | 376.685650 .. 390.834550 |
| 2F | 181.164910 .. 189.910910 | 125.817200 .. 133.247200 | 128.307150 .. 133.247150 |
| EXT | - | - | - |
| GF | 659.480437 .. 822.520957 | 326.223659 .. 407.437921 | 336.267835 .. 405.123147 |
| paint lines engine RELEASED (4) | | 217.208100 .. 217.208100 | 217.208150 .. 217.208150 |
| paint lines engine HELD (38) | | 604.990059 .. 710.006421 | 624.052485 .. 711.996697 |

Blank faces: {'plaster': 14, 'engine_paint': 14, 'rule_paint': 14}

## By class

| class | plaster | engine paint | rule paint | band | tiled |
|---|---|---|---|---|---|
| DOUBLE_HEIGHT | 0.839412 .. 0.870912 | 3.344721 .. 3.525121 | 3.344721 .. 3.525121 | -2.505309 .. -2.654209 | 0.000000 .. 0.000000 |
| DRY | 818.306324 .. 897.516936 | 677.199438 .. 743.719400 | 676.011914 .. 745.709726 | 142.294410 .. 151.807210 | 0.000000 .. 0.000000 |
| EXCLUDED | - | - | - | - | - |
| EXTERIOR | - | - | - | - | - |
| RETURN | 24.150000 .. 24.150000 | 0.000000 .. 24.150000 | 20.250000 .. 24.150000 | 0.000000 .. 0.000000 | 3.900000 .. 0.000000 |
| SHAFT | 143.604000 .. 157.770000 | 141.654000 .. 155.820000 | 141.654000 .. 155.820000 | 1.950000 .. 1.950000 | 0.000000 .. 0.000000 |
| WET_BAND | 75.314715 .. 122.008029 | 0.000000 .. 0.000000 | 0.000000 .. 0.000000 | 75.314715 .. 122.008029 | 0.000000 .. 0.000000 |
| WET_RENDER | 433.318506 .. 488.437300 | 0.000000 .. 0.000000 | 0.000000 .. 0.000000 | 0.000000 .. 0.000000 | 433.318506 .. 488.437300 |

## Gap allocation (plaster - engine paint = band + tiled - (engine - rule), per end)

- low: gap 673.334798 = band 217.053816 + tiled 437.218506 - (engine - rule) {'BEAM_END_BELOW_CEILING': '0.315000', 'LEDGER_ROUNDING': '0.000250', 'OPENING_BASIS_MISMATCH': '0.872274', 'RETURN_RULE_RESTATED': '-20.250000'}; residual 0.000000
- high: gap 763.538656 = band 273.111030 + tiled 488.437300 - (engine - rule) {'LEDGER_ROUNDING': '0.000250', 'OPENING_BASIS_MISMATCH': '-1.990576'}; residual 0.000000

## Dry rooms (per end)

| room | end | plaster | engine paint | band | rule paint | named (engine - rule) | residual |
|---|---|---|---|---|---|---|---|
| GF-01 | low | 47.949844 | 36.911738 | 11.048930 | 36.900914 | OPENING_BASIS_MISMATCH 0.010824 (W11 + W12) | 0.000000 |
| GF-01 | high | 66.249856 | 56.925700 | 11.638930 | 54.610926 | OPENING_BASIS_MISMATCH 2.314774 (W11 + W12) | 0.000000 |
| GF-04 | low | 34.330000 | 26.958600 | 7.371400 | 26.958600 | - | 0.000000 |
| GF-04 | high | 43.780000 | 36.405000 | 7.375000 | 36.405000 | - | 0.000000 |
| GF-15 | low | 66.528990 | 56.013100 | 10.515840 | 56.013150 | LEDGER_ROUNDING -0.000050 (paint line vs its own ledger (L x H - deductions)) | 0.000000 |
| GF-15 | high | 66.528990 | 56.013100 | 10.515840 | 56.013150 | LEDGER_ROUNDING -0.000050 (paint line vs its own ledger (L x H - deductions)) | 0.000000 |
| GF-08 | low | 178.220570 | 152.050500 | 26.325120 | 151.895450 | BEAM_END_BELOW_CEILING 0.065000 (beam B26); BEAM_END_BELOW_CEILING 0.090000 (beam B27); LEDGER_ROUNDING 0.000050 (paint line vs its own ledger (L x H - deductions)) | 0.000000 |
| GF-08 | high | 211.805270 | 178.805000 | 33.000320 | 178.804950 | LEDGER_ROUNDING 0.000050 (paint line vs its own ledger (L x H - deductions)) | 0.000000 |
| 1F-01 | low | 62.573000 | 51.415000 | 11.158000 | 51.415000 | - | 0.000000 |
| 1F-01 | high | 62.607000 | 51.415000 | 11.192000 | 51.415000 | - | 0.000000 |
| 1F-04 | low | 63.141000 | 52.005000 | 11.136000 | 52.005000 | - | 0.000000 |
| 1F-04 | high | 63.141000 | 52.005000 | 11.136000 | 52.005000 | - | 0.000000 |
| 1F-10 | low | 58.026000 | 48.940000 | 9.086000 | 48.940000 | - | 0.000000 |
| 1F-10 | high | 62.050000 | 52.290000 | 9.760000 | 52.290000 | - | 0.000000 |
| 1F-11 | low | 74.776510 | 61.462600 | 14.175360 | 60.601150 | OPENING_BASIS_MISMATCH 0.861450 (W17) | 0.000000 |
| 1F-11 | high | 80.198410 | 61.717700 | 14.175360 | 66.023050 | OPENING_BASIS_MISMATCH -4.305350 (W17) | 0.000000 |
| 1F-13 | low | 135.625500 | 111.017700 | 24.608000 | 111.017500 | LEDGER_ROUNDING 0.000200 (paint line vs its own ledger (L x H - deductions)) | 0.000000 |
| 1F-13 | high | 139.615500 | 114.367700 | 25.248000 | 114.367500 | LEDGER_ROUNDING 0.000200 (paint line vs its own ledger (L x H - deductions)) | 0.000000 |
| 2F-03 | low | 69.775000 | 57.775000 | 12.000000 | 57.775000 | - | 0.000000 |
| 2F-03 | high | 69.775000 | 57.775000 | 12.000000 | 57.775000 | - | 0.000000 |
| 2F-01 | low | 27.359910 | 22.650200 | 4.869760 | 22.490150 | BEAM_END_BELOW_CEILING 0.160000 (beam B15); LEDGER_ROUNDING 0.000050 (paint line vs its own ledger (L x H - deductions)) | 0.000000 |
| 2F-01 | high | 31.765910 | 26.000200 | 5.765760 | 26.000150 | LEDGER_ROUNDING 0.000050 (paint line vs its own ledger (L x H - deductions)) | 0.000000 |

## Faces

| class | floor | plaster element | plaster | engine paint | rule paint | named | note |
|---|---|---|---|---|---|---|---|
| DRY | GF | HL:WALL_FINISH:GF_01:PLASTER | ['47.949844', '66.249856'] | ['36.911738', '56.925700'] | ['36.900914', '54.610926'] | low OPENING_BASIS_MISMATCH 0.010824; high OPENING_BASIS_MISMATCH 2.314774 | face 20.127 lm; residual 0.000000 / 0.000000 |
| DRY | GF | HL:WALL_FINISH:GF_04:PLASTER | ['34.330000', '43.780000'] | ['26.958600', '36.405000'] | ['26.958600', '36.405000'] | - | face 12.5 lm; residual 0.000000 / 0.000000 |
| DRY | GF | HL:WALL_FINISH:GF_15:PLASTER | ['66.528990', '66.528990'] | ['56.013100', '56.013100'] | ['56.013150', '56.013150'] | low LEDGER_ROUNDING -0.000050; high LEDGER_ROUNDING -0.000050 | face 21.537 lm; residual 0.000000 / 0.000000 |
| DRY | GF | HL:WALL_FINISH:GF_08:PLASTER | ['178.220570', '211.805270'] | ['152.050500', '178.805000'] | ['151.895450', '178.804950'] | low BEAM_END_BELOW_CEILING 0.065000; low BEAM_END_BELOW_CEILING 0.090000; low LEDGER_ROUNDING 0.000050; high LEDGER_ROUNDING 0.000050 | face 53.188 lm; residual 0.000000 / 0.000000 |
| DRY | 1F | HL:WALL_FINISH:1F_01:PLASTER | ['62.573000', '62.607000'] | ['51.415000', '51.415000'] | ['51.415000', '51.415000'] | - | face 17.7 lm; residual 0.000000 / 0.000000 |
| DRY | 1F | HL:WALL_FINISH:1F_04:PLASTER | ['63.141000', '63.141000'] | ['52.005000', '52.005000'] | ['52.005000', '52.005000'] | - | face 17.4 lm; residual 0.000000 / 0.000000 |
| DRY | 1F | HL:WALL_FINISH:1F_10:PLASTER | ['58.026000', '62.050000'] | ['48.940000', '52.290000'] | ['48.940000', '52.290000'] | - | face 16.2 lm; residual 0.000000 / 0.000000 |
| DRY | 1F | HL:WALL_FINISH:1F_11:PLASTER | ['74.776510', '80.198410'] | ['61.462600', '61.717700'] | ['60.601150', '66.023050'] | low OPENING_BASIS_MISMATCH 0.861450; high OPENING_BASIS_MISMATCH -4.305350 | face 22.149 lm; residual 0.000000 / 0.000000 |
| DRY | 1F | HL:WALL_FINISH:1F_13:PLASTER | ['135.625500', '139.615500'] | ['111.017700', '114.367700'] | ['111.017500', '114.367500'] | low LEDGER_ROUNDING 0.000200; high LEDGER_ROUNDING 0.000200 | face 39.45 lm; residual 0.000000 / 0.000000 |
| DRY | 2F | HL:WALL_FINISH:2F_03:PLASTER | ['69.775000', '69.775000'] | ['57.775000', '57.775000'] | ['57.775000', '57.775000'] | - | face 18.9 lm; residual 0.000000 / 0.000000 |
| DRY | 2F | HL:WALL_FINISH:2F_01:PLASTER | ['27.359910', '31.765910'] | ['22.650200', '26.000200'] | ['22.490150', '26.000150'] | low BEAM_END_BELOW_CEILING 0.160000; low LEDGER_ROUNDING 0.000050; high LEDGER_ROUNDING 0.000050 | face 9.009 lm; residual 0.000000 / 0.000000 |
| SHAFT | GF | HL:WALL_FINISH:ST_GF:PLASTER | ['50.945000', '62.434000'] | ['50.945000', '62.434000'] | ['50.945000', '62.434000'] | - | Q-72: full exposed height through the shaft, no false ceiling: no band |
| SHAFT | 1F | HL:WALL_FINISH:ST_1F:PLASTER | ['45.317000', '46.564000'] | ['45.317000', '46.564000'] | ['45.317000', '46.564000'] | - | Q-72: full exposed height through the shaft, no false ceiling: no band |
| SHAFT | 2F | HL:WALL_FINISH:ST_2F:PLASTER | ['47.342000', '48.772000'] | ['45.392000', '46.822000'] | ['45.392000', '46.822000'] | - | decor band under the roof 0.15 x 12.90 lm (T-173 faces W 5.20 + E 5.20 + N 2.50) + pier returns 0.015 (T-680) |
| DOUBLE_HEIGHT | GF | PLASTER-BAND@L-8cecb1d010d5aafbf25d | ['0.839412', '0.870912'] | ['3.344721', '3.525121'] | ['3.344721', '3.525121'] | low VOID_NO_CEILING -2.505309; high VOID_NO_CEILING -2.654209 | void strip 3.997201 .. 4.147201 lm x 0.64 (GF plaster 4.29 - paint 3.65); low end less the ST-02 landing contact 0.0529 (T-709, 0 .. 0.0529 bound: its low end), high end with the 0.15 lm column returns |
| EXTERIOR | EXT | 1F-FACADE:facade | None | None | None | - | one facade line per floor, finish and quantity HELD blank; Sigma = the exterior plaster area (owner notes 2026-10-21): external paint follows the external plaster face by face |
| RETURN | 1F | 1F-OPENING-OP-004:door jambs and head | ['0.780000', '0.780000'] | ['0.000000', '0.780000'] | ['0.780000', '0.780000'] | low RETURN_RULE_RESTATED -0.780000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | 1F | 1F-OPENING-OP-005:door jambs and head | ['0.795000', '0.795000'] | ['0.000000', '0.795000'] | ['0.795000', '0.795000'] | low RETURN_RULE_RESTATED -0.795000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | 1F | 1F-OPENING-OP-006:door jambs and head | ['0.795000', '0.795000'] | ['0.000000', '0.795000'] | ['0.795000', '0.795000'] | low RETURN_RULE_RESTATED -0.795000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | 1F | 1F-OPENING-OP-008:door jambs and head | ['1.060000', '1.060000'] | ['0.000000', '1.060000'] | ['1.060000', '1.060000'] | low RETURN_RULE_RESTATED -1.060000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | 1F | 1F-OPENING-OP-010:door jambs and head | ['0.780000', '0.780000'] | ['0.000000', '0.780000'] | ['0.000000', '0.780000'] | low TILED 0.780000 | reading A; HELD 0 .. plaster (tiled part not established) |
| RETURN | 1F | 1F-OPENING-OP-018:door jambs and head | ['0.780000', '0.780000'] | ['0.000000', '0.780000'] | ['0.780000', '0.780000'] | low RETURN_RULE_RESTATED -0.780000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | 1F | 1F-OPENING-OP-019:door jambs and head | ['0.780000', '0.780000'] | ['0.000000', '0.780000'] | ['0.780000', '0.780000'] | low RETURN_RULE_RESTATED -0.780000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | 1F | 1F-OPENING-OP-020:door jambs and head | ['0.810000', '0.810000'] | ['0.000000', '0.810000'] | ['0.810000', '0.810000'] | low RETURN_RULE_RESTATED -0.810000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| EXCLUDED | 1F | 1F-R0E919A:plaster | EXCLUDED | EXCLUDED | EXCLUDED | - | superseded room-route line (EXCLUDED in the candidate) |
| WET_RENDER | 1F | 1F-R26FA0D:plaster | ['52.529000', '52.529000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | 1F | 1F-R26FA0D:plaster band above ceiling | ['10.841600', '10.841600'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| EXCLUDED | 1F | 1F-R3CFCFD:plaster | EXCLUDED | EXCLUDED | EXCLUDED | - | superseded room-route line (EXCLUDED in the candidate) |
| WET_RENDER | 1F | 1F-R48AA46:plaster | ['27.910000', '27.910000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | 1F | 1F-R48AA46:plaster band above ceiling | ['3.510000', '6.210000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| WET_RENDER | 1F | 1F-R48CDA5:plaster | ['26.305100', '26.305100'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | 1F | 1F-R48CDA5:plaster band above ceiling | ['3.393000', '6.003000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| WET_RENDER | 1F | 1F-R52AC05:plaster | ['19.669100', '19.669100'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | 1F | 1F-R52AC05:plaster band above ceiling | ['4.185600', '4.185600'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| EXCLUDED | 1F | 1F-R78C367:plaster | EXCLUDED | EXCLUDED | EXCLUDED | - | superseded room-route line (EXCLUDED in the candidate) |
| WET_RENDER | 1F | 1F-R8BDA49:plaster | ['27.910100', '27.910100'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | 1F | 1F-R8BDA49:plaster band above ceiling | ['3.510000', '6.210000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| EXCLUDED | 1F | 1F-RB72F22:plaster | EXCLUDED | EXCLUDED | EXCLUDED | - | superseded room-route line (EXCLUDED in the candidate) |
| EXCLUDED | 1F | 1F-RED0D19:plaster | EXCLUDED | EXCLUDED | EXCLUDED | - | superseded room-route line (EXCLUDED in the candidate) |
| WET_RENDER | 1F | 1F-RED23B8:plaster | ['23.220100', '23.220100'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | 1F | 1F-RED23B8:plaster band above ceiling | ['4.275000', '4.981800'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| RETURN | 1F | 1F-REVEAL-A-1F-01:THROUGH:JAMBS_HEAD:HELD | None | None | None | - | plaster return blank: paint HELD by name |
| RETURN | 1F | 1F-REVEAL-D-1F-03:THROUGH:JAMBS_HEAD:VALUED | ['0.810000', '0.810000'] | ['0.000000', '0.810000'] | ['0.810000', '0.810000'] | low RETURN_RULE_RESTATED -0.810000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | 1F | 1F-REVEAL-D-1F-04:THROUGH:JAMBS_HEAD:VALUED | ['0.780000', '0.780000'] | ['0.000000', '0.780000'] | ['0.780000', '0.780000'] | low RETURN_RULE_RESTATED -0.780000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| EXTERIOR | EXT | 2F-FACADE:facade | None | None | None | - | one facade line per floor, finish and quantity HELD blank; Sigma = the exterior plaster area (owner notes 2026-10-21): external paint follows the external plaster face by face |
| RETURN | 2F | 2F-OPENING-OP-001:door jambs and head | ['0.810000', '0.810000'] | ['0.000000', '0.810000'] | ['0.810000', '0.810000'] | low RETURN_RULE_RESTATED -0.810000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | 2F | 2F-OPENING-OP-006:door jambs and head | ['0.780000', '0.780000'] | ['0.000000', '0.780000'] | ['0.780000', '0.780000'] | low RETURN_RULE_RESTATED -0.780000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | 2F | 2F-OPENING-OP-007:door jambs and head | ['1.060000', '1.060000'] | ['0.000000', '1.060000'] | ['1.060000', '1.060000'] | low RETURN_RULE_RESTATED -1.060000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| EXCLUDED | 2F | 2F-R1DB2D2:plaster | EXCLUDED | EXCLUDED | EXCLUDED | - | superseded room-route line (EXCLUDED in the candidate) |
| EXCLUDED | 2F | 2F-R4D1B62:stair hall plaster | EXCLUDED | EXCLUDED | EXCLUDED | - | superseded room-route line (EXCLUDED in the candidate) |
| WET_RENDER | 2F | 2F-RE83BED:plaster | ['30.255000', '30.255000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | 2F | 2F-RE83BED:plaster band above ceiling | ['3.783000', '6.693000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| EXTERIOR | EXT | FENCE:F-LOWER:FACE:OUTSIDE:PLASTER | None | None | None | - | fence face: paint = plaster face by face; both HELD blank |
| EXTERIOR | EXT | FENCE:F-LOWER:FACE:PLOT:PLASTER | None | None | None | - | fence face: paint = plaster face by face; both HELD blank |
| EXTERIOR | EXT | FENCE:F-NORTH:FACE:OUTSIDE:PLASTER | None | None | None | - | fence face: paint = plaster face by face; both HELD blank |
| EXTERIOR | EXT | FENCE:F-NORTH:FACE:PLOT:PLASTER | None | None | None | - | fence face: paint = plaster face by face; both HELD blank |
| EXTERIOR | EXT | FENCE:F-SEA:FACE:OUTSIDE:PLASTER | None | None | None | - | fence face: paint = plaster face by face; both HELD blank |
| EXTERIOR | EXT | FENCE:F-SEA:FACE:PLOT:PLASTER | None | None | None | - | fence face: paint = plaster face by face; both HELD blank |
| EXTERIOR | EXT | FENCE:F-STREET:FACE:OUTSIDE:PLASTER | None | None | None | - | fence face: paint = plaster face by face; both HELD blank |
| EXTERIOR | EXT | FENCE:F-STREET:FACE:PLOT:PLASTER | None | None | None | - | fence face: paint = plaster face by face; both HELD blank |
| EXTERIOR | EXT | GF-FACADE:facade | None | None | None | - | one facade line per floor, finish and quantity HELD blank; Sigma = the exterior plaster area (owner notes 2026-10-21): external paint follows the external plaster face by face |
| RETURN | GF | GF-OPENING-OP-005:door jambs and head | ['1.060000', '1.060000'] | ['0.000000', '1.060000'] | ['1.060000', '1.060000'] | low RETURN_RULE_RESTATED -1.060000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | GF | GF-OPENING-OP-008:door jambs and head | ['1.080000', '1.080000'] | ['0.000000', '1.080000'] | ['1.080000', '1.080000'] | low RETURN_RULE_RESTATED -1.080000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | GF | GF-OPENING-OP-009:door jambs and head | ['1.080000', '1.080000'] | ['0.000000', '1.080000'] | ['1.080000', '1.080000'] | low RETURN_RULE_RESTATED -1.080000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | GF | GF-OPENING-OP-010:door jambs and head | ['1.080000', '1.080000'] | ['0.000000', '1.080000'] | ['1.080000', '1.080000'] | low RETURN_RULE_RESTATED -1.080000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | GF | GF-OPENING-OP-012:door jambs and head | ['0.810000', '0.810000'] | ['0.000000', '0.810000'] | ['0.810000', '0.810000'] | low RETURN_RULE_RESTATED -0.810000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | GF | GF-OPENING-OP-013:door jambs and head | ['1.060000', '1.060000'] | ['0.000000', '1.060000'] | ['1.060000', '1.060000'] | low RETURN_RULE_RESTATED -1.060000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | GF | GF-OPENING-OP-017:door jambs and head | ['0.780000', '0.780000'] | ['0.000000', '0.780000'] | ['0.000000', '0.780000'] | low TILED 0.780000 | reading A; HELD 0 .. plaster (tiled part not established) |
| RETURN | GF | GF-OPENING-OP-018:door jambs and head | ['0.780000', '0.780000'] | ['0.000000', '0.780000'] | ['0.000000', '0.780000'] | low TILED 0.780000 | reading A; HELD 0 .. plaster (tiled part not established) |
| RETURN | GF | GF-OPENING-OP-021:door jambs and head | ['1.400000', '1.400000'] | ['0.000000', '1.400000'] | ['1.400000', '1.400000'] | low RETURN_RULE_RESTATED -1.400000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | GF | GF-OPENING-OP-025:door jambs and head | ['1.080000', '1.080000'] | ['0.000000', '1.080000'] | ['1.080000', '1.080000'] | low RETURN_RULE_RESTATED -1.080000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | GF | GF-OPENING-OP-026:door jambs and head | ['0.780000', '0.780000'] | ['0.000000', '0.780000'] | ['0.780000', '0.780000'] | low RETURN_RULE_RESTATED -0.780000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| EXCLUDED | GF | GF-R31F8AE:stair hall plaster | EXCLUDED | EXCLUDED | EXCLUDED | - | superseded room-route line (EXCLUDED in the candidate) |
| EXCLUDED | GF | GF-R51E127:plaster | EXCLUDED | EXCLUDED | EXCLUDED | - | superseded room-route line (EXCLUDED in the candidate) |
| EXCLUDED | GF | GF-R7512EA:plaster | EXCLUDED | EXCLUDED | EXCLUDED | - | superseded room-route line (EXCLUDED in the candidate) |
| EXCLUDED | GF | GF-R75FBAE:plaster | EXCLUDED | EXCLUDED | EXCLUDED | - | superseded room-route line (EXCLUDED in the candidate) |
| WET_RENDER | GF | GF-R8496F0:plaster | ['13.702800', '21.640000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | GF | GF-R8496F0:plaster band above ceiling | ['3.658000', '4.248000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| WET_RENDER | GF | GF-RA3AD49:plaster | ['31.720506', '42.673500'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | GF | GF-RA3AD49:plaster band above ceiling | ['8.545994', '8.555000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| WET_RENDER | GF | GF-RB28769:plaster | ['22.616500', '22.616500'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | GF | GF-RB28769:plaster band above ceiling | ['4.358400', '4.358400'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| WET_RENDER | GF | GF-RB62B55:plaster | ['16.945000', '22.615000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | GF | GF-RB62B55:plaster band above ceiling | ['4.425000', '4.425000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| EXCLUDED | GF | GF-RC06FED:plaster | EXCLUDED | EXCLUDED | EXCLUDED | - | superseded room-route line (EXCLUDED in the candidate) |
| WET_BAND | GF | GF-RC06FED:plaster band above ceiling | ['0.499037', '6.186806'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| EXCLUDED | GF | GF-RC99C2A:plaster | EXCLUDED | EXCLUDED | EXCLUDED | - | superseded room-route line (EXCLUDED in the candidate) |
| WET_RENDER | GF | GF-RD36087:plaster | ['7.040000', '19.555000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | GF | GF-RD36087:plaster band above ceiling | ['2.560000', '13.671000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| WET_RENDER | GF | GF-RD6F891:plaster | ['25.591200', '25.591200'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | GF | GF-RD6F891:plaster band above ceiling | ['2.244800', '5.085875'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| WET_RENDER | GF | GF-RDBD4F9:plaster | ['26.654400', '26.654400'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | GF | GF-RDBD4F9:plaster band above ceiling | ['3.892324', '5.005988'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| WET_RENDER | GF | GF-RDF7D28:plaster | ['11.400000', '25.210000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | GF | GF-RDF7D28:plaster band above ceiling | ['3.584000', '17.298000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| RETURN | GF | GF-REVEAL-A-GF-01:THROUGH:JAMBS_HEAD:HELD | None | None | None | - | plaster return blank: paint HELD by name |
| RETURN | GF | GF-REVEAL-D-GF-02:THROUGH:JAMBS_HEAD:VALUED | ['0.780000', '0.780000'] | ['0.000000', '0.780000'] | ['0.000000', '0.780000'] | low TILED 0.780000 | reading A; HELD 0 .. plaster (tiled part not established) |
| RETURN | GF | GF-REVEAL-D-GF-10:THROUGH:JAMBS_HEAD:VALUED | ['0.780000', '0.780000'] | ['0.000000', '0.780000'] | ['0.000000', '0.780000'] | low TILED 0.780000 | reading A; HELD 0 .. plaster (tiled part not established) |
| RETURN | GF | GF-REVEAL-D-GF-14:THROUGH:JAMBS_HEAD:VALUED | ['0.780000', '0.780000'] | ['0.000000', '0.780000'] | ['0.780000', '0.780000'] | low RETURN_RULE_RESTATED -0.780000 | reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) would give 0 m2 + lm: HELD for the Checker / Lead reading |
| RETURN | GF | GF-REVEAL-D-GF-15:THROUGH:JAMBS_HEAD:HELD | None | None | None | - | plaster return blank: paint HELD by name |
| WET_RENDER | GF | GF-RF38DAF:plaster | ['25.301100', '25.301100'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | GF | GF-RF38DAF:plaster band above ceiling | ['4.744960', '4.744960'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| WET_RENDER | GF | GF-RFAD3C4:plaster | ['12.206400', '16.440000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
| WET_BAND | GF | GF-RFAD3C4:plaster band above ceiling | ['3.304000', '3.304000'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | band above the ceiling: no paint (Q-72 / T-690) |
| WET_RENDER | GF | HL:WALL_FINISH:GF_07:PLASTER | ['32.342200', '32.342200'] | ['0.000000', '0.000000'] | ['0.000000', '0.000000'] | - | levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the ceiling; R-T701-3): the whole face is tiled, no paint face |
