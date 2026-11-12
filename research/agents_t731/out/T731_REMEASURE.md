# T-731 ST-01 re-measure and restated MS1-L bounds on ARCH_TAKEOFF_V3.0.73 (research, unwired)

## Readings (R-T731-1)

| reading | source | segments (n x r = rise) | state |
|---|---|---|---|
| A | section A-A sheet 10 (owner Q-46 A: the section counts) | GF->LD 15 x 0.166667 = 2.50; LD->1F 12 x 0.166667 = 2.00 | COHERENT |
| B | ST p.4: 12 straight lines 45A .. 25E + winders 2F6 / 2F4 / 2F5 + closing 2F3 + 12 lines 25B .. 459 | GF->LD 16 x 0.156250 = 2.50; LD->1F 12 x 0.166667 = 2.00 | COHERENT |
| P | architectural GF plan 10 + 4 + 11 (Q-46: a check only) | - | REFUSED: R-T731-1 (d): P counts 11 risers on MS1-U, drawn 12 on every source read |
| B28-uniform | T-725 'coherent B': ST p.4 count 28 at 4.50 / 28 over the storey | - | REFUSED: R-T731-1 (c): one rise 0.160714 over a printed half landing: reaches +3.571429 at the landing printed +3.50 (miss +0.071429 m), and carries MS1-U at 0.160714 against its VERIFIED 2.00 / 12 |
| B27-as-recorded | T-258 / T-281 / T-352 / T-711 MS1-L part | - | REFUSED: R-T725-1: reading B27-as-recorded counts 28 risers (ST p.4) but takes its rise from a total of 27 (section A-A 27): not one stair |

## Restated lines

| line | item | piece | old | new | note |
|---|---|---|---|---|---|
| L-7863355dfcb68a681d2d | STR.CONC.STAIR m3 | MS1-L + winders + turn | lo 1.213429 hi  cap  | lo 1.213428 hi  cap  | floor from reading A; B (16 risers to +3.50 at 2.50 / 16 = 0.15625) is above it; no AT_MOST (warped turn soffit, C-ST-3); componentwise min mixes readings (refused, information only) 1.209143 -> 1.205928. T-711 printed 1.213429 half-up; the exact reading A sum 1.213428296 floors to 1.213428 (R-T696-1): -0.000001 m3, rounding only |
| L-9c3643da524267bf47f6 | STR.FORMWORK.STAIR m2 | MS1-L well side | lo 0.679193 hi 0.854426 cap  | lo 0.679193 hi 0.843465 cap  | high = reading B method O on the coherent 0.15625 (T-725 0.854426 used 4.50 / 28 uniform) |
| L-d9790e457fd530487553 | STR.FORMWORK.STAIR m2 | MS1-L west wall + well-end junction | lo  hi  cap 0.873917 | lo  hi  cap 0.862807 | cap = reading B method O on the coherent 0.15625; low stays blank (sequence not printed) |
| L-ffd491ad529ee2251982 | STR.FORMWORK.STAIR m2 | MS1-L risers + soffit + winder turn | lo 7.678894 hi  cap  | lo 7.678894 hi  cap  | low = reading A method D (unchanged); the B readings move with the coherent rise but stay above |

## Re-measure of ST-01 pieces (own read, ST7757 dxf by handle + section A-A)

| piece | own m3 | ledger | ledger m3 | residual | ledger state | released line | basis |
|---|---|---|---|---|---|---|---|
| MS2-LD-W half landing +7.516 | 0.239200 | ST01-MS2-LD-W | 0.239200 | 0.0 | DRAWING-CONFIRMED | L-2416e65f (0.4696 with MS2-LD-E) | p.5 5E3 -> 5E2 1.300 x 632 -> 5C0 1.150 x T 0.16 (Q-47 A); level 5.50 + 12 x 4.20 / 25 |
| MS2-LD-E half landing +7.684 | 0.230400 | ST01-MS2-LD-E | 0.230400 | 0.0 | DRAWING-CONFIRMED | L-2416e65f (0.4696 with MS2-LD-W) | p.5 5E2 -> 5D4 1.200 x 62F -> 5C0 1.200 x 0.16; level 9.70 - 12 x 0.168 |
| MS1-LD half landing +3.50 | 0.230400 | ST01-MS1-LD | 0.230400 | 0.0 | VERIFIED | L-e37d81a8 (1.227952 with MS1-U) | p.4 25A -> 296 1.200 x 25B -> 279 1.200 x 0.16; level printed by section A-A (320 above +0.30) |
| D1 steps (ST-01b) +0.30 -> +1.00 | 0.100286 | ST01b-D1-STEPS | 0.100286 | 0.0 | DRAWING-CONFIRMED | L-85f64587 (0.100286) | p.3 1C7 / 1C6 / 1C5 / 1C4 at 0.300, 1.150 long, lane 1C3 -> 15F 1.200; r = 0.70 / 4 = 0.175 (section A-A +0.30 / +1.00); 4 x 1/2 x r x 0.30 x 1.20 = 0.126000 - arrival wedge in GS-08 0.025714 (Q-62 A cond) |
| MS1-U flight geometry |  | ST01-MS1-U | 0.997552 |  | VERIFIED | L-e37d81a8 | p.4 12 lines 459 .. 25B at 0.300 (handles in the ledger), 459 0.200 inside B20 (2C6); r 2.00 / 12 on both coherent readings = the VERIFIED basis |
| MS2-L flight geometry |  | ST01-MS2-L | 1.033444 |  | VERIFIED | L-67e4b048 | p.5 12 lines 646 .. 632 at 0.300, 646 0.150 inside B20 (5E1); 3.300 = T-258 basis |
| MS2-U flight geometry |  | ST01-MS2-U | 1.001373 |  | VERIFIED | L-bb0e57b1 | p.5 11 drawn lines 644 .. 62F at 0.300, 62F -> 5E1 3.100; arrival line from p.4 459 (T-258) |
| MS1-L flight geometry (HELD) |  | ST01-MS1-L |  |  | HELD |  | p.4 12 lines 45A .. 25E at 0.300 (B), 10 lines 26C .. 25E (A, from 0.600), 45A 0.150 short of B20 face 2C6, lane 284 -> 256 1.200, head 25E 0.050 short of the well end |
| MS1-T turn region (HELD) |  | ST01-MS1-T-SLAB |  |  | HELD |  | p.4 284 -> 2F3 1.300 x 25E -> 279 1.150 = 1.495 m2; winder lines 2F6 1.2587 / 2F4 1.6263 / 2F5 1.2587, closing 2F3 1.1500; soffit not drawn (C-ST-3) |
