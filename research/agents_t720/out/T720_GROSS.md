# T-720 gross / covered floor area per storey (B2-03; research, unwired)

Own read by handle on the architectural DXF beside the released V2.9 floor plate. Areas m2. Gross = to the outer face of the external envelope (R-T720-1); voids / shafts named, not deducted.

| storey | component | gross | engine plate | own - engine | named causes | residual | state |
|---|---|---|---|---|---|---|---|
| GF | GF house 217.788972 + GF annex (single storey) 60.477319 | 278.266291 | 284.1465 | -5.880209 | -5.880000 | -0.000209 | RESIDUAL_NAMED |
| 1F | 1F 209.839104 | 209.839104 | 209.8017 | +0.037404 | +0.037384 | +0.000020 | RESIDUAL_NAMED |
| 2F | 2F roof structures (stair, lift, maid room) 55.080000 | 55.080000 | 55.0800 | +0.000000 | +0.000000 | +0.000000 | BALANCED |

All storeys (enclosed gross): **543.185395**

## GF ground outside the envelope (R-T720-3 / -4)

- plot to the outer face of the boundary walls 470.550; outside the GF envelope 192.283710
- side passage 5.880 (OUTSIDE_ENVELOPE): under the 1F floor 4.080, rest 1.800 HELD (Q-67 reading: GF-roof slab panel 1.56 to the boundary beam + the 0.24 mouth band under the layer-5 boundary lines 86 / 105 / 106; slab outline not read here)
- COVERED_BY_FLOOR: entrance zone under the 1F west wing (porch, entrance stair) 17.480000
- COVERED_BY_FLOOR: pool court strip and the GF curved bay under the 1F floor 8.465133
- HELD slabs named without an outline: Q-68 pool court slab projection (18.393 gross, VOID 4.373: cited); Q-68 1F roof-slab edges 6.791 (cited); Q-67 GF-roof panel over the passage 1.56 (cited)
- not under the 1F floor 162.258577; OPEN_TO_SKY HELD (upper bound 160.458577) until the slab projections are read
- 1F roof not under the 2F 154.759104 (OPEN_TO_SKY (a roof, not a floor)); GF roof not under the 1F 98.452319

## Named inside, not deducted

- GF: lift shaft 3.240 (T-719 V-03, stacked; not deducted: gross)
- GF: garden band 13.986 inside the outer wall line (engine EXTERNAL 9.101 + MERGED 4.885; D-48 designer classification open; its cover is the GF roof slab per the Q-67 reading, cited)
- GF: curved glazing bay on the pool court: outline follows the outermost glazing line 280 (bulge 0.867, r 2.330 m) as the engine plate does (its arc correction on the same polyline: 6.995 m2 out of the rectangle)
- 1F: V-01 ST-02 light well 26.240 (T-719; engine VOID 16.005 + flights seen 6.772 + residue 3.453): inside the 1F gross, not deducted
- 1F: lift shaft 3.240 (T-719 V-03)
- 1F: concave curved wall BD0 / BCD r 1.935 m: opening bridged on the same circle (R-T720-1)
- 2F: lift shaft 3.240 (T-719 V-03)
- 2F: ST-01 stair box inside (T-719 V-04)

## Second source: printed dimensions on the same sheets

- A67: faces 107 / 9B own 15.000 m vs printed 15.000 m (+0.000 mm)
- 598: faces 10A / 98 own 8.300 m vs printed 8.300 m (+0.000 mm)
- 5F9: faces 298 / B6 own 15.970 m vs printed 15.970 m (+0.000 mm)
- D87: faces 107 / B3A own 10.600 m vs printed 10.600 m (-0.000 mm)
- 143C: faces 1291 / B5D own 6.770 m vs printed 6.770 m (+0.000 mm)

## Findings

- F-T720-1 ENGINE_RIGHT: GF / 1F / 2F engine plates agree with the own handle read after the named causes, residual GF -0.000209, 1F +0.000020, 2F +0.000000 m2 (engine plate printed to 4 dp)
- F-T720-2 ENGINE_WRONG (reconciliation only, no BOQ line): north-arrow block NR1 (inserts 1612 / 19A2 / 19A3, lines on layers 1/5) is read as a wall network on every plan: plate_top_level and the face categories carry 0.6581 m2 per plan (1.9743 m2 in all) that is not building (R-T720-2)
- F-T720-3 RULE_DIFFERENCE: engine plate includes the side passage 5.880 (threshold closure); R-T720-4 / Q-67 A keep it beside the gross, covered 4.080 by the 1F floor
