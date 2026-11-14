# T-796: MAIN FILL overlay precedence + B1-04 disposal (lane S; Alsenan; method every villa)

## 1. Overlay precedence (R-T796-1, board tools)

Defect: `docs/agents/boq/build_boq.py` (old lines 7-16) and `blank_lines.py` (old lines 109-116) applied every
MAIN_FILL_ALL.json row (written on V3.0.78) over the newest index unconditionally. Rule: a row applies only where the
index line still carries the row's `before` state and no later `fill_basis`; a line already at the row's `after` is a
no-op; anything else is skipped and logged (the index value stands). Code: `overlay_precedence.py` here; the board copy
`docs/agents/boq/overlay.py` is byte-identical (sha256 6908cfde...262a). Reproduction: the old tools on
LINE_INDEX_V3_0_86 regenerate the committed BLANK_LINES_V3.0.86.md byte for byte.

On V3.0.86 (107 rows): ALREADY 66 (floor bed 44, plaster 11, paint 11), APPLY 18 (TILE_300 17 = owner 13 Nov wall
tile 3.00 m, W17 Q-76 A: NOT yet wired in the candidate, still shown through the overlay), SKIPPED 23 (a newer wired
value was being overridden). Per family, old overlay - index (units):

| family | rows | index | old overlay | old - index |
|---|---|---|---|---|
| STR.EARTH.DISPOSAL | 1 | 10.477 m3 RELEASED | HELD 105.632 .. 115.546 | +100.11 (midpoint) |
| ARCH.FACADE | 4 | 946.978 m2 | 868.138 | -78.84 |
| FIN.EXT.FINISH | 3 | 758.512 m2 | 762.251 | +3.74 |
| FIN.ROOF.FINISH | 1 | 34.390 m2 | 46.589 | +12.20 |
| FIN.ROOF.INSULATION / PROTECTION | 4 + 4 | 238.484 m2 each | 248.809 | +10.32 each |
| FIN.ROOF.SCREED | 4 | 17.886 m3 | 18.661 | +0.77 |
| FIN.WP.ROOF | 2 | 150.204 m2 | 162.246 | +12.04 |

Workbook effect (V3.0.86, fixed tool): disposal HELD 105.6 .. 115.5 -> 10.477 m3 CALCULATED; roof membrane
336.13 -> 324.09 m2 vs freelancer 285 (+17.9 % -> +13.7 %); external render (Compare: FIN.EXT.FINISH + ARCH.FACADE plinth
+ fence) 1,343.47 -> 1,305.59 m2 vs 1,502.84 (-10.6 % -> -13.1 %; plinth faces 105.89 old row vs 71.75 wired);
roof layers 577.67 -> 557.02 m2. True blank / held (non-rebar): 14 / 4 (was shown 14 / 5: Earthworks 0 / 1 -> 0 / 0).

## 2. Disposal (R-T796-2)

Physical element: excavated soil (in situ m3) not placed back. V3.0.86 B1 lines, all RELEASED: excavation E 335.756
(pits 208.165, boundary trench 46.315, lift pit 34.155, pool 17.777, straps 13.036, F10F 8.392, annex 5.768, ext GB
1.123, court 1.026); backfill Z1 175.089 (pits 124.303, other trenches 30.423, lift pit 15.067, F10F 5.296) + Z2 placed
fill EG -> slab underside 150.190. Drawing note (ST p.13, per T-764): fill "from excavation material" -> both fills from
the spoil. Balance at k = 1: 335.756 - 175.089 - 150.190 = 10.477 m3 in situ = the wired line (ESTIMATE).

The MAIN FILL 105.632 .. 115.546 used the same formula on V3.0.78, when 8 excavation and 6 backfill lines were blank:
E 234.28 .. 235.51 (pits + pool + F10F range + trench clip) - backfill 119.96 .. 128.64 (= the pits range only). Cause in
units: excavation +100.25 .. +101.48 (the 5 lines filled later: boundary 46.32, lift 34.16, straps 13.04, annex 5.77,
court 1.03, F10F / trench to points) and backfill +196.64 .. +205.32 (Z2 150.19 + Z1 50.79 + pits range -> midpoint):
net -95.16 .. -105.07 -> 10.48. Verdict: the wired 10.48 is physically right on the drawings' reuse note; the MAIN FILL
row is a stale snapshot (its own basis said the range widens as lines fill).

Named residual (not a reason to hold the line): k = in-situ m3 per compacted m3 is not sourced (T-505: MPW s.02220 /
02223 give none). The surplus turns into an import at k_break = 335.756 / 325.280 = 1.032; any k above that gives
disposal 0 and import (325.28 - 335.756 / k) compacted. If Z2 were imported (no drawing says so) disposal would be
160.667 m3 and import 150.190. No freelancer earthworks line: UNRESOLVED vs freelancer (no comparison).

## 3. Tests

tests/t796_overlay_precedence (9): normal (blank -> applies; pending RELEASED at before -> applies), adverse (newer
RELEASED with fill_basis skipped, index byte-identical; moved line skipped; absent line logged; HELD row keeps its
range, never 0), disposal hand villa (E 80, Z1 30, Z2 42 -> 8.0; stale Z2-blank error = +42; k 1.2 -> import 5.333;
Z2 imported -> 50 / 42; k <= 0 refused; HELD line never summed as 0).

## 4. Lessons row (proposed, s.7)

A board overlay written on one index version is checked against each newer index by the row's own `before` state,
never applied blindly: a stale fix row silently reverses a wired correction (here 100 m3 of disposal).
