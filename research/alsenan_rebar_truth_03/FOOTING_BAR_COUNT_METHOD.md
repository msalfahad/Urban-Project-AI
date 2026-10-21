# Footing bar-count method (two-layer FTB footings and FF)

Round 3 replaces the old reading of `6 Ø 14/m` as "6 bars". Every FTB field (TOP short, TOP long, BOTTOM short, BOTTOM long) is a **rate in bars per metre** (schedule header and cell text `14/m`).

## Rule (`COUNT_PER_METRE_LB_PLUS_END_BAR`, `engine/source/rebar_model.bar_count`)

| Quantity | Definition | Source / authority |
|---|---|---|
| cover c | 0.07 m | ST7757 p.8 note 22: concrete in contact with soil ≥ 7 cm (`COVER-SOIL-70`) |
| bar length | the side the bar runs along − 2c (straight) | p.13 typical isolated footing: bottom bars straight; top-layer end shape not detailed → separate BLOCKED component (FTB) / PROVISIONAL legs (FF, p.14 closed loop) |
| distribution width d | the *other* side − 2c | bars are placed inside the cover on both edges |
| spacing s | 1000 / rate mm | the rate means ≥ rate bars per metre |
| **verified count** | **ceil(rate × d)** | the fewest bars that still give `rate` bars per metre over d: a defensible LOWER BOUND |
| convention count | ceil(d / s) + 1 | the usual bar-at-both-edges rule; **PROVISIONAL** (not stated in the source, p.8 is silent) |
| unit weight | D² / 162 kg/m | no early rounding |

The project drawing states no count convention, and the p.13/p.14 details are not dimensioned. Engineering practice gives the +1 end bar. So the end bar is published as a bounded PROVISIONAL addition, never folded into the verified count. Nothing was chosen to approach any benchmark.

## Worked results (frozen register `FOOTING_REBAR_REGISTER_V3.json`)

### FF — FOOTING:FF#10 (VERIFIED_PARTIAL_LOWER_BOUND)
L = 4.60 m, W = 4.50 m, D = 0.55 m, c = 0.07 m

| set | rate /m | d (m) | verified n | convention n | bar length (m) | kg/m | verified kg | provisional kg | state |
|---|---|---|---|---|---|---|---|---|---|
| TOP_SHORT Ø14 | 6 | 4.46 | 27 | 28 | 4.36 | 1.2099 | 142.43 | 5.28 | PARTIAL |
| TOP_LONG Ø14 | 6 | 4.36 | 27 | 28 | 4.46 | 1.2099 | 145.69 | 5.40 | PARTIAL |
| BOTTOM_SHORT Ø14 | 9 | 4.46 | 41 | 42 | 4.36 | 1.2099 | 216.28 | 5.28 | PARTIAL |
| BOTTOM_LONG Ø14 | 9 | 4.36 | 40 | 41 | 4.46 | 1.2099 | 215.84 | 5.40 | PARTIAL |
| PERIMETER_CLOSURE_LEGS | | | 54 | 56 | 0.82 | | 0.00 | 55.56 | PROVISIONAL |
| LIFT_PIT_WALLS | | |  |  |  | | 0.00 | 0.00 | BLOCKED — pit walls 20 cm, 6Ø12/m + 6Ø16/m vertical: wall height 'as per lift manufacturer recommendations' - not in the source |
| PIT_WALL_BASE_BARS_2D16 | | |  |  |  | | 0.00 | 0.00 | BLOCKED — 2Ø16 at each wall base: length follows the pit walls |

**Total:** verified 720.24 kg (≥, lower bound) + provisional 76.90 kg. The frozen V3b method gave 0.00 kg (top rate read as an absolute count, bottom layer dropped as 'boxed'; FF cell unread → 0).

### F14 — FOOTING:F14#16 (VERIFIED_PARTIAL_LOWER_BOUND)
L = 3.80 m, W = 3.30 m, D = 0.50 m, c = 0.07 m

| set | rate /m | d (m) | verified n | convention n | bar length (m) | kg/m | verified kg | provisional kg | state |
|---|---|---|---|---|---|---|---|---|---|
| TOP_SHORT Ø14 | 6 | 3.66 | 22 | 23 | 3.16 | 1.2099 | 84.11 | 3.82 | PARTIAL |
| TOP_LONG Ø14 | 6 | 3.16 | 19 | 20 | 3.66 | 1.2099 | 84.13 | 4.43 | PARTIAL |
| BOTTOM_SHORT Ø14 | 9 | 3.66 | 33 | 34 | 3.16 | 1.2099 | 126.17 | 3.82 | PARTIAL |
| BOTTOM_LONG Ø14 | 9 | 3.16 | 29 | 30 | 3.66 | 1.2099 | 128.42 | 4.43 | PARTIAL |
| TOP_LAYER_END_DETAIL | | |  |  |  | | 0.00 | 0.00 | BLOCKED — two-layer footing top mesh: end legs / bends not detailed (p.13 shows a boxed cage for the typical footing only) |

**Total:** verified 422.83 kg (≥, lower bound) + provisional 16.50 kg. The frozen V3b method gave 49.51 kg (top rate read as an absolute count, bottom layer dropped as 'boxed').

### F12 — FOOTING:F12#24 (VERIFIED_PARTIAL_LOWER_BOUND)
L = 4.40 m, W = 3.20 m, D = 0.70 m, c = 0.07 m

| set | rate /m | d (m) | verified n | convention n | bar length (m) | kg/m | verified kg | provisional kg | state |
|---|---|---|---|---|---|---|---|---|---|
| TOP_SHORT Ø14 | 10 | 4.26 | 43 | 44 | 3.06 | 1.2099 | 159.20 | 3.70 | PARTIAL |
| TOP_LONG Ø14 | 10 | 3.06 | 31 | 32 | 4.26 | 1.2099 | 159.78 | 5.15 | PARTIAL |
| BOTTOM_SHORT Ø16 | 9 | 4.26 | 39 | 40 | 3.06 | 1.5802 | 188.59 | 4.84 | PARTIAL |
| BOTTOM_LONG Ø16 | 9 | 3.06 | 28 | 29 | 4.26 | 1.5802 | 188.49 | 6.73 | PARTIAL |
| TOP_LAYER_END_DETAIL | | |  |  |  | | 0.00 | 0.00 | BLOCKED — two-layer footing top mesh: end legs / bends not detailed (p.13 shows a boxed cage for the typical footing only) |

**Total:** verified 696.05 kg (≥, lower bound) + provisional 20.42 kg. The frozen V3b method gave 88.56 kg (top rate read as an absolute count, bottom layer dropped as 'boxed').

### F13 — FOOTING:F13#25 (VERIFIED_PARTIAL_LOWER_BOUND)
L = 4.30 m, W = 2.40 m, D = 0.50 m, c = 0.07 m

| set | rate /m | d (m) | verified n | convention n | bar length (m) | kg/m | verified kg | provisional kg | state |
|---|---|---|---|---|---|---|---|---|---|
| TOP_SHORT Ø14 | 7 | 4.16 | 30 | 31 | 2.26 | 1.2099 | 82.03 | 2.73 | PARTIAL |
| TOP_LONG Ø14 | 7 | 2.26 | 16 | 17 | 4.16 | 1.2099 | 80.53 | 5.03 | PARTIAL |
| BOTTOM_SHORT Ø16 | 8 | 4.16 | 34 | 35 | 2.26 | 1.5802 | 121.43 | 3.57 | PARTIAL |
| BOTTOM_LONG Ø16 | 8 | 2.26 | 19 | 20 | 4.16 | 1.5802 | 124.90 | 6.57 | PARTIAL |
| TOP_LAYER_END_DETAIL | | |  |  |  | | 0.00 | 0.00 | BLOCKED — two-layer footing top mesh: end legs / bends not detailed (p.13 shows a boxed cage for the typical footing only) |

**Total:** verified 408.89 kg (≥, lower bound) + provisional 17.91 kg. The frozen V3b method gave 54.37 kg (top rate read as an absolute count, bottom layer dropped as 'boxed').

### F8 — FOOTING:F8#26 (VERIFIED_PARTIAL_LOWER_BOUND)
L = 4.00 m, W = 3.60 m, D = 0.50 m, c = 0.07 m

| set | rate /m | d (m) | verified n | convention n | bar length (m) | kg/m | verified kg | provisional kg | state |
|---|---|---|---|---|---|---|---|---|---|
| TOP_SHORT Ø14 | 6 | 3.86 | 24 | 25 | 3.46 | 1.2099 | 100.47 | 4.19 | PARTIAL |
| TOP_LONG Ø14 | 6 | 3.46 | 21 | 22 | 3.86 | 1.2099 | 98.07 | 4.67 | PARTIAL |
| BOTTOM_SHORT Ø14 | 9 | 3.86 | 35 | 36 | 3.46 | 1.2099 | 146.52 | 4.19 | PARTIAL |
| BOTTOM_LONG Ø14 | 9 | 3.46 | 32 | 33 | 3.86 | 1.2099 | 149.44 | 4.67 | PARTIAL |
| TOP_LAYER_END_DETAIL | | |  |  |  | | 0.00 | 0.00 | BLOCKED — two-layer footing top mesh: end legs / bends not detailed (p.13 shows a boxed cage for the typical footing only) |

**Total:** verified 494.50 kg (≥, lower bound) + provisional 17.71 kg. The frozen V3b method gave 53.14 kg (top rate read as an absolute count, bottom layer dropped as 'boxed').

Old frozen V3b for F8 + F12 + F13 + F14: 245.58 kg. This matches the 245.58 kg that Round 2 moved out of the verified total.
