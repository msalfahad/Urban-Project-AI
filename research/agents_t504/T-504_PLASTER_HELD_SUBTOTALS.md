# T-504: PLASTER_MATERIALS_TABLE_V3 (R-T504-1, HELD subtotals never partial)

Unwired producer (no candidate or released line moves). V1 / V2 untouched; V3 carries their rows byte-identical and
replaces only the coat subtotals.

## Defect reproduced (F-T499-1)
Merged T-454 / T-489 ledger rebuilt from its sha256-pinned inputs (candidate line index V3.0.45). The plaster lines
(FIN.PLASTER, EXT.FENCE.PLASTER: 83 lines) are identical in the V3.0.46 index, and V3.0.47 / .48 / .50 name no plaster
item code, so the case holds on the candidate of record V3.0.50.
- V1 WALL_PLASTER `mortar_m3` 4.726962 m3 printed as the total over 25 of 52 coat rows (27 HELD: 11 dry lines HELD +
  16 faces whose class is not established).
- V2 sensitivity sums over the same 25 rows (1:3 45.265391 bags, ...) with no HELD marker.

## Rule R-T504-1 (proposed; R-T499-1 applied to plaster)
Per coat and per key (area_m2, mortar_m3, cement_bags, sand_m3, each sensitivity ratio): COMPUTED only when every row
has an exact figure (then = the V1 / V2 sum, unchanged); else HELD, value None, at_least = exact part + AT_LEAST bounds
(None when there is neither, never 0), bound_rows / held_rows listed, bound_complete when no row lacks both.

## Subtotals that change status on the ledger (17; V3 value None, status HELD, known part AT_LEAST)
| coat | key | V1 / V2 printed | V3 at_least | rows | held | bound |
|---|---|---|---|---|---|---|
| BOND_COAT | area_m2 | V1 576.6519 | 576.6519 | 70 | 33 | 0 |
| WALL_PLASTER | area_m2 | V1 236.3481 | 236.3481 | 52 | 27 | 0 |
| WALL_PLASTER | mortar_m3 | V1 4.726962 | 4.726962 | 52 | 27 | 0 |
| WALL_PLASTER | sensitivity 1:3 / 1:4 / 1:5 bags | V2 45.265391 / 36.212306 / 30.176923 | same | 52 | 27 | 0 |
| WALL_PLASTER | sensitivity 1:3 / 1:4 / 1:5 sand m3 | V2 4.715145 / 5.029485 / 5.239049 | same | 52 | 27 | 0 |
| LEVELLING_RENDER | area_m2 | V1 340.3038 | 340.3038 | 34 | 22 | 0 |
| LEVELLING_RENDER | mortar_m3_at_least | V1 5.104557 | 5.104557 (all bound) | 34 | 22 | 12 |
| LEVELLING_RENDER | sensitivity 1:3 / 1:4 / 1:5 bags | V2 48.881239 / 39.10499 / 32.587491 | same | 34 | 22 | 12 |
| LEVELLING_RENDER | sensitivity 1:3 / 1:4 / 1:5 sand m3 | V2 5.091794 / 5.43125 / 5.65755 | same | 34 | 22 | 12 |
Unchanged: cement / sand totals of every coat (V2 already None; V3 adds status HELD, at_least None: no mix sourced);
bond-coat mortar (no thickness: None, never 0). s.5 status of every coat: HELD.

## Hand fixture villa P (tests/t504_plaster_held_subtotals)
Dry 50.00 + 30.00 m2, wet 20.00 m2, dry face area HELD; wall plaster 0.020 m, render 0.015 m minimum, synthetic 1:4
mix for wall plaster only. Normal: 80.00 m2 x 0.020 = 1.600 m3 -> 12.25728 bags, 1.7024 m3 sand, COMPUTED = V1 / V2.
Adverse: wall plaster >= 80.00 m2 / >= 1.600 m3 / >= 12.25728 bags HELD (V1 printed 1.6 as the total); render >= 0.300
m3 bound-complete, bags None (mix HELD); bond coat >= 100.00 m2, mortar None; all-HELD -> at_least None, never 0.

## Open
Not wired: T-498 (iii) reads V3 instead of V1 / V2 sums. The T-454 held-line range bounds beside (8 dry lines) are not
summed here (they are a separate bound beside a HELD line, R-T454-2).
