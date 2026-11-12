# T-726 plaster shaft residual 13.50 m2 on ARCH_TAKEOFF_V3.0.72 (generated; research, unwired)

## (1) Which element the row belongs to (R-T726-1)

PLS row 24 2.5 x 5.4 = 13.500000 is in group rows [23, 24] (sum I 204.420000 = J 204.420000: ESTABLISHED); the group's first row is 14.8 x 12.9 = 190.920000 (stair-house walls). PNT row 25: group [24, 25], J 204.420000.

## (2) Faces of the stair-house family against the row (R-T726-2)

Result: **NO_FACE (OUT_OF_SCOPE matches only)** (width tol 0.10 m, height tol 0.054 m).

| face | width m | exposed height m | carried by |
|---|---|---|---|
| ST-01 N face (26E / ADE / 127E) | 2.5 | 12.74 .. 13.44 | ST_GF / ST_1F / ST_2F bands |
| ST-01 S face, GF only (220) | 2.5 | 4.24 .. 4.34 | ST_GF band |
| ST-01 W face u 0 .. 5.20 (298 / AF1 / 12B7) | 5.2 | 12.74 .. 12.90 | ST bands |
| ST-01 E face = lift wall, stair side (21C / B16 / 129A) | 5.2 | 12.74 .. 13.44 | ST bands |
| 1F arrival wall across the landing (AEA / AEB) | 2.5 | 3.99 .. 4.04 | 1F-13 |
| 2F arrival wall across the landing (1282 / 1283) | 2.5 | 3.79 .. 4.04 | 2F-01 |
| W face south of u 5.20, 1F / 2F (C21 / 12B7) | 1.250000 | 3.79 .. 4.04 | 1F-13 / 2F-01 |
| lift shaft V-03 inner face (each of 4, every floor) | 1.8 | HELD | none (lining needs a specification, T-719) |
| lift shaft outer width, GF (21C .. 222) | 2.2 | HELD | neighbouring rooms |
| ST-02 well west run (T-709 E3E) | 4.00 | 3.99 .. 4.29 | 1F-13 |
| ST-02 well south run (T-709 D7B) | 7.02 | 3.99 .. 4.29 | 1F-13 |

Width matches: ['ST-01 N face (26E / ADE / 127E)', 'ST-01 S face, GF only (220)', '1F arrival wall across the landing (AEA / AEB)', '2F arrival wall across the landing (1282 / 1283)']; nearest heights: ST-01 S face, GF only (220) gap 1.060000; 1F arrival wall across the landing (AEA / AEB) gap 1.360000; 2F arrival wall across the landing (1282 / 1283) gap 1.360000; ST-01 N face (26E / ADE / 127E) gap 7.340000

Printed levels inside the element: ['+0.30', '+1.00', '+3.50', '+5.34', '+5.50', '+7.516', '+7.684', '+9.70', '+13.74', '+13.90']; intervals of 5.4 inside: none.
Intervals using a level outside the element: [['0.15', '5.50'], ['4.30', '9.70']] (sources {'+0.15': ['242C SE_ELEVATION', '2883 NW_ELEVATION', '394 GF outside the ST-01 box', '407 GF outside the ST-01 box', '409 GF outside the ST-01 box', '40B GF outside the ST-01 box', '40D GF outside the ST-01 box', '4AE GF outside the ST-01 box'], '+4.30': ['244B SE_ELEVATION', "D20 1F beside the annex 'ROOF' block (B8D)"], '+5.50': ['1251 1F outside the ST-01 box', '2887 NW_ELEVATION', 'D16 1F outside the ST-01 box', 'D1B 1F outside the ST-01 box', 'D1D 1F outside the ST-01 box'], '+9.70': ['1350 2F outside the ST-01 box', '1352 2F outside the ST-01 box']}).

## (3) Shaft faces carried once (R-T726-3)

| room | chain lm | room face lm | shaft faces walked | open edges | expected | room - expected | result |
|---|---|---|---|---|---|---|---|
| 1F-13 | 52.44 | 39.45 | 5.2 + 2.5 + 5.2 + 0.10 | - | 39.440000 | 0.010000 | ONCE |
| 2F-01 | 12.9 | 9.009 | 0.700000 + 0.700000 | 2.5 | 9.000000 | 0.009000 | ONCE |
| GF | - | - | - | - | - | - | ONCE: the GF stair-hall lines (GF-R31F8AE) are EXCLUDED on the candidate; the ST_GF shaft lines alone carry the GF band |

Candidate lines read (V3.0.72):

| line | code | element | class | low | high |
|---|---|---|---|---|---|
| L-bacbf7fd | FIN.PAINT | 2F-R4D1B62:stair hall paint | EXCLUDED | None | None |
| L-83f2ef17 | FIN.PAINT | GF-R31F8AE:stair hall paint | EXCLUDED | None | None |
| L-be48ea84 | FIN.PAINT | HL:WALL_FINISH:1F_13:PAINT | HELD | 111.0177 | 114.3677 |
| L-c74cfb4e | FIN.PAINT | HL:WALL_FINISH:2F_01:PAINT | HELD | 22.6502 | 26.0002 |
| L-2ab93d50 | FIN.PAINT | HL:WALL_FINISH:ST_1F:PAINT | HELD | 45.317 | 46.564 |
| L-5a7a5c6f | FIN.PAINT | HL:WALL_FINISH:ST_2F:PAINT | HELD | 45.392 | 46.822 |
| L-145bd239 | FIN.PAINT | HL:WALL_FINISH:ST_GF:PAINT | HELD | 50.945 | 62.434 |
| L-7afc2b10 | FIN.PLASTER | 2F-R4D1B62:stair hall plaster | EXCLUDED | None | None |
| L-acc2563d | FIN.PLASTER | GF-R31F8AE:stair hall plaster | EXCLUDED | None | None |
| L-9b4a7bab | FIN.PLASTER | HL:WALL_FINISH:1F_13:PLASTER | HELD | 135.6255 | 139.6155 |
| L-ae0cdd79 | FIN.PLASTER | HL:WALL_FINISH:2F_01:PLASTER | HELD | 27.35991 | 31.76591 |
| L-0eac839f | FIN.PLASTER | HL:WALL_FINISH:ST_1F:PLASTER | HELD | 45.317 | 46.564 |
| L-418121a4 | FIN.PLASTER | HL:WALL_FINISH:ST_2F:PLASTER | HELD | 47.342 | 48.772 |
| L-95f2c45c | FIN.PLASTER | HL:WALL_FINISH:ST_GF:PLASTER | HELD | 50.945 | 62.434 |

## (4) Reconciliation in units

His stair-house gross 204.420000 - engine gross 177.07 (T-173) = 27.350000:

- south side (open above +5.50, his box wall over 12.90): 20.11
- north (his 2.40 / +1.00 vs printed 2.50 / +0.30 lobby, heights): -2.64
- west / east (his 5.00 x 12.90 x 2 vs faces to 5.20, lobby, soffit): -3.62
- his row 24 2.5 x 5.4: NO_FACE (OUT_OF_SCOPE matches only): 13.500000
- sum 27.350000 (closes)

Like for like plaster (T-701): engine vs his ['-15.81', '-9.88'] %; with the unbound row named apart ['-14.83', '-8.82'] %. Engine change: 0 m2. PNT row 25 13.500000 m2: the same row (group [24, 25]), same result.

