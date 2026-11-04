# T-511: cement / sand producer census and cross-trade binding on candidate V3.0.57 (research, unwired)

Worker 2, 2026-11-04. `t511_cement_sand_census.py` + `out/CEMENT_SAND_CENSUS_T511.{json,csv}` +
`tests/t511_cement_sand_census/` (21 tests). No engine, rule, knowledge, registry or candidate file changed; no
candidate or released (V2.9 + route G) line moves. Inputs sha256-pinned (10 files); drawings not re-read (every
producer table is merged and Checker-verified; this task binds and audits them). Rebuild: `python3 -I
research/agents_t511/t511_cement_sand_census.py` (byte-identical, tested); `--check` exits 1 on any failure.

Candidate: the row asked for V3.0.56 (4e25c54f); T-310 merged V3.0.57 (25a8b406, 87ef8718) during this run, so the
census runs on V3.0.57 = T-310's V3.0.56 line index + the T-310 change set, with two proofs: the 365 cement / sand
host and partner lines are identical in V3.0.55 and V3.0.56 (T-508 touched skirting only), and T-310 adds one host
(the pool protection screed); every other T-310 row is waterproofing membrane (not a key).

## 1. Physical element (ERS s.2.1)

The 50 kg cement bags and loose sand bought for SITE-MIXED cement : sand layers: block laying mortar, plaster coats
(bond coat, wall plaster, wet-wall levelling render), floor-tile bed, stone beds, screeds, outdoor beds. Not this key:
ready-mix concrete (bought as concrete m3), precast lintels, tile adhesive (20 kg product; T-455 carries no cement or
sand key, checked), AAC glue (25 kg product). Kept apart per row: installed (theoretical), waste, procurement.

## 2. Rules R-T511-1..6 (every villa; full text in the module docstring)

1 every item code classified HOST / PARTNER / NOT_A_KEY / SCOPE_OPEN (an unclassified code fails); 2 one producer per
PHYSICAL key (host element, layer, material, stage): a bed is keyed on its floor-finish host, so a finish-table row
on the host is a second producer unless it is a READER that agrees; no key on a wall-tile line (UPC-WETWALL-001);
3 freshness: a producer figure whose line is now HELD / EXCLUDED / absent / re-netted leaves the sum and stays
BESIDE; 4 bags / loose m3 only, HELD never 0; 5 subtotals by R-T499-1 (engine FINISH_MATERIALS_TABLE_V5.subtotal) per
trade, stage and range end, whole bags only over a COMPUTED project figure; 6 every host line ends PRODUCED, HELD
(named) or NOT_APPLICABLE (with evidence).

## 3. Result on V3.0.57 (0 failures)

Census: 1,272 keys; keys with two producers 0; reader divergences 0 (88 keys bound twice: T-500 PRODUCER + the
FINISH_MATERIALS_TABLE V1 `materials()` READER at procurement stage on the 44 bed hosts, agreement within 1e-5).
279 host lines: 46 PRODUCED, 74 NOT_APPLICABLE, 160 HELD.

| trade | producer | installed cement bags | installed sand m3 | status | held contributors |
|---|---|---|---|---|---|
| block laying mortar | T-453 r2 (R-T506-2) | >= 10.155552 | >= 1.396388 | HELD | 23 (7 0.15 m module, 7 parent lines, 2 stale, 2 house below NG, 5 fence) |
| plaster coats | T-489 (T-454 beside) | none known | none known | HELD | 159 (no coat mix readable, T-489; 3 FIN.EXT.FINISH no producer) |
| floor-tile bed | T-500 | >= 99.748616 .. 137.562192 | >= 13.715435 .. 18.914801 | HELD | 1 (GF-ST-CN bed MISSING) |
| stone beds (marble) | none | none | none | HELD | 51 m2 lines (Q-45 / Q-53 C stairs: no bed line, no table) |
| screeds | none | none | none | HELD | 8 (3 RELEASED m3: footing 5.4925, lift pit 1.035, pool 1.5245 = 8.0520 m3, mix not printed) |
| outdoor beds | none (T-495 options beside) | none | none | HELD | 4 |
| **PROJECT** | | **HELD, known part >= 109.904168 .. 147.717744** | **HELD, >= 15.111823 .. 20.311189** | HELD | 246 |

Waste: only the tile bed has a sourced factor (5 %, >= 4.987 .. 6.878 bags); procurement known part >= 104.736 ..
144.440 bags (tile bed only). No bags-to-buy figure exists for any trade or the project: every group has a HELD
member (R-T499-1).

Hand checks: masonry 2.8202 (1F 0.20 black, 23.90 m2) + 7.335352 (GF 0.20 black, 62.164 m2) = 10.155552 bags =
1.269444 m3 x 8 (= the fresh 0.20 m mortar T-498 restates; sand 0.387777 + 1.008611 = 1.396388). Tile bed = T-500
PROJECT exactly. Project = 10.155552 + 99.748616 = 109.904168 .. + 137.562192 = 147.717744.

## 4. Findings

- **F-T511-1 STALE PRODUCER (masonry, 2 lines).** T-453 r2 read V3.0.45; T-488 (V3.0.55) made 2F 0.20 black
  L-76a4d8e5 (21.66 m2, 2.55588 bags) and the 2F-W05 piece L-a6eedf5e (3.80 m2, range 0.408 .. 0.448 bags) HELD (D-39).
  Their T-453 figures leave the sum and stay BESIDE: the 0.20 m black mortar falls 1.588929 -> 1.269444 m3 (-0.319485
  m3, -20.1 %), the same as T-498's staged restatement. A wiring that reads T-453 r2 as written would release mortar
  on two HELD walls.
- **F-T511-2 TILE BED subtotal is HELD, not 105 .. 145 bags.** T-500 printed PROJECT to-buy 105 .. 145 over its 44
  determinate rows while the GF-ST-CN host has no bed (finish HELD, area 0 .. 0.23 m2). By R-T499-1 the trade is HELD;
  the residual is immaterial (at most 0.23 x 0.06 x 8 = 0.1104 bags, 0.0152 m3 sand) but stays named, never 0.
- **F-T511-3 NO PRODUCER for three released screed volumes** (8.0520 m3 installed: footing protection, lift-pit base,
  pool protection; printed '5 cm screed', no mix) and for the marble beds (51 lines; Q-45 stairs 3 cm 1:3 and the
  Q-53 C conversion exist, but no bed line or table), the released outdoor porcelain walk (21.0142 m2; T-495's basis
  would give 5.043 .. 6.725 bags BESIDE, not a producer) and the fence / house-below-NG masonry. Sensitivity only, NOT
  A QUANTITY: 8.052 m3 of screed at the owner's 1:4 figures would be about 64 bags.
- **F-T511-4 two conversion conventions for one cement key.** Floors / blocks use the owner's 1:4 practice value
  (8.0 bags, 1.1 m3 sand per m3: Q-45 B, Q-78); T-489 converts any ratio with the Q-53 C formula (1:4 -> 7.6608
  bags, 1.064 m3). Today no plaster figure exists (mix HELD), so nothing diverges; when a coat mix is sourced, a 1:4
  coat must use the owner's 1:4 figure (Q-53 C is the 1:3 rule: 'never use the 1:4 rate for 1:3', and the reverse
  holds), or the cement total mixes two bases for one product (-4.2 % on that coat).
- FINISH_MATERIALS_TABLE V1 / V2 `materials(WET_WALL)` still computes a 0.02 m 1:4 'bed' on wet walls (the levelling
  render, T-457): R-T511-2 refuses any cement key on a FIN.WALL.TILE line (tested).

## 5. Freelancer and verdict proposal

The freelancer workbooks carry no cement / sand rows (T-367 s.6, T-420 s.7, T-500 s.4): materials are engine-only.
Verdict proposal: RULE_DIFFERENCE (scope), no numeric verdict; the census itself moves no quantity.

## 6. For the wiring rows (Lead)

- T-498: read masonry cement / sand only from fresh producer rows (V3.0.56 lines); 1.269444 m3 / 10.155552 bags agrees.
- A cross-trade cement / sand line can only be HELD with its known part AT_LEAST today; the census JSON lists every
  held contributor by line and reason.
- New producer rows needed (not here): screed materials (mix source), stone-bed materials (B7 / B6, Q-53 C 1:3),
  outdoor porcelain bed.

## 7. Lessons row (proposed, ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-04 | One cement key fed by five tables on three candidate versions; two masonry figures sat on lines the candidate had since HELD, and the tile-bed to-buy ignored a MISSING bed | each table checked its own lines at its own version; nobody keyed the shared product by physical layer across trades or re-checked a producer against the current candidate | R-T511-1..6 (every villa): classify every code, one producer per physical (host, layer, material, stage), readers agree, stale figures leave the sum and stay beside, HELD subtotal never partial, completeness by host | tests/t511_cement_sand_census (normal P511 by hand; adverse: held bed, second producer, divergent / lone reader, wall-tile key, stale class / net / absent, kg for bags, HELD as 0, range order, unclassified code, host without state, mirror / rotation / mm) | proposed |
