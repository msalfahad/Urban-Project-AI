# T-543 B9 blockwork reconciliation vs the freelancer, by component (research, unwired)

Worker 1 (lane S), 2026-11-06, claim 01:21 UTC, run session_01E6cPneUBEJ7VefEpkRToG3. Files: `t543_reconcile.py`
(R-T543-1, any villa), `t543_inputs.py` (merged repository files + the freelancer's section sub-totals only),
`t543_alsenan.py` (the table), `out/T543_BLOCKWORK_RECONCILE.json`, `tests/t543_blockwork_reconcile/` (17 tests).
No engine module, method, rule / knowledge version, registry or candidate file changed; no quantity moves.

## 1. Physical element and the two sides

Every laid masonry face, by wall, thickness and material, from the structural top of the plate under it to the soffit
of the member over it (Q-60 A, Q-72), net of every actual opening (Q-73). Engine: candidate of record V3.0.58, item
MAS.BLOCK: 13 valued lines **467.7925 m2** (GF 159.2369, 1F 308.5556) + 15 HELD lines, blank (V3.0.58 changes roof WP
only, R-T507-1 (e): the masonry lines are V3.0.57's, byte-identical). Per wall: T-288 register V4 + T-488 (2F on the
roof datum D-39, GF-W22 CONFLICT D-27): sums equal the line index per floor and thickness exactly (asserted).

Freelancer: Drive "Alsenan chalet project", masonry workbook, one sheet, read this run through the Drive text reader
(R-T541-1). Three sections: external (no thickness printed) 559.80, internal 15 cm 617.25, internal 20 cm 83.64;
printed total 1,260.69. The exact sum of his row products is **1,260.6895** (his section prints are roundings of
559.8015 / 617.2480 / 83.6400). One flat height per floor and zone (GF 4.00 / 3.50, 1F 3.70 / 3.45, 2F 3.45 / 3.70).
Inside his masonry sections he also books five non-wall rows: the boundary wall (74.40), three parapet rows (172.93),
1F "projections" (41.25); his 20 cm section deducts 9.84 of openings without naming a floor.

| | Owner manual method | Drawing-derived method (engine) |
|---|---|---|
| Height | storey to the underside of the member over the wall (Q-72, Q-60 A) | per member: GF 4.50 / 1F 4.20 structural storeys, printed soffit depths; 2F 4.25 - b_r (D-39) |
| Openings | every actual opening deducted (Q-73) | per wall, from the opening census |
| Parapets | not masonry unless the detail says so (Q-65 C designer) | RC upstand >= 0.30 (P1 detail), block only as an alternative above it, HELD |

## 2. The table (R-T543-1): 1,260.6895 - 467.7925 = 792.8970 m2, exact (Decimal)

| # | Component | Engine m2 + status | His basis m2 | Difference | Class |
|---|---|---|---|---|---|
| 1 | GF storey walls, net | 159.2369 valued + 31 walls HELD | 466.9550 (L 134.28 m, gross 515.395, openings 48.44) | +307.7181 | split 1a-1k |
| 2 | 1F storey walls, net | 308.5556 valued + walls HELD | 391.0595 (L 120.31, gross 441.4095, openings 50.35) | +82.5039 | split 2a-2h |
| 3 | 2F storey walls, net | HELD (all 9 walls; D-39) | 123.9350 (L 39.10, gross 137.695, openings 13.76) | +123.9350 | split 3a-3g |
| 4 | boundary wall | not MAS.BLOCK: EXT.FENCE.WALL 97.9705 valued + 2 HELD planes | 74.40 | +74.4000 | RULE_DIFFERENCE (family placement) |
| 5 | parapets (3 rows) | STR.CONC.PARAPET HELD BLANK; block alternative records | 172.93 | +172.9300 | split 5a-5d |
| 6 | 1F "projections" | no masonry element identified | 41.25 | +41.2500 | UNRESOLVED |
| 7 | his 20 cm openings, no floor | (engine deducts per wall) | -9.84 | -9.8400 | UNRESOLVED |
| | **Total** | **467.7925** | **1,260.6895** | **+792.8970** | |

Beside the table, outside every sum: engine-only HELD scope not in his sheet: below-ground masonry
HOUSE_BELOW_NG:MAIN_S / ANNEX_S (T-407), blank lines (never 0).

Storey-wall splits (R-T543-1 (d); held figures are the T-228 register V2 carried figures, NOT quantities):

| Row | GF | 1F | 2F | Class |
|---|---|---|---|---|
| a annex storey datum (Q-54 B / D-39): GF-W00, W02, W04, W06, W17, W18, W23-W25, W27, W35 | +130.7450 | | | HELD |
| b lift tie beam size (ST p.8 n.19): GF-W08, W09, W13, W14 | +41.1710 | | | HELD |
| c sunken-panel drops d (D-41): GF-W12, W16, W20, W31, W32, W34 | +46.6930 | | | HELD |
| d held openings: GF-W15, W26 / 1F-W07, W14+15, W16 / 2F-W00 | +41.8070 | +45.9140 | +6.8400 | HELD |
| e CB2 width conflict (D-27): GF-W22 | +12.9210 | | | HELD |
| f held increments of part-valued walls | +8.2725 | +2.2693 | | HELD |
| g no member drawn above: 1F-W11 (F-T543-1) | | -0.8720 | | HELD |
| h roof datum b_r (D-39), at the b_r = 0.05 what-if: 2F-W01 .. W08 | | | +104.7910 | HELD |
| i held length with no height x engine mean height | +23.9655 | +41.6475 | +20.7067 | HELD |
| j version drift (V2 figure - V3.0.58 value, valued walls) | -0.1204 | -1.8989 | 0.0000 | TOLERANCE |
| k height: his flat heights vs clear height per member | +2.5241 | -7.2986 | -4.4769 | RULE_DIFFERENCE |
| l openings census (his - engine deductions) | -5.7800 | -8.4990 | -2.1650 | UNRESOLVED |
| m RESIDUAL: wall-length census + rounding | +5.5193 | +11.2416 | -1.7608 | UNRESOLVED |

Mean heights: GF his 3.8382 vs engine 3.8192 m; 1F 3.6689 vs 3.7312; 2F 3.5216 vs 3.6347. Lengths (engine with a
gross + held length): GF 126.567 + 6.275 vs his 134.28 m; 1F 106.084 + 11.162 vs 120.31; 2F 33.903 + 5.697 vs 39.10.

Parapet split (row 5): 5a block alternative above the RC upstand, upper end, material HELD (Q-65 C) +60.4129; 5b RC
upstand 0.30 m on every run (P1 detail: concrete, never masonry) +41.0513 ENGINE_RIGHT; 5c print rounding -0.0000005
TOLERANCE; 5d RESIDUAL +71.4658 UNRESOLVED (parapet height below the finished roof, b_edge HELD D-39, + length).
Engine: 25 runs, centreline 136.8376 m (upper ends), face above the finished roof 101.4642 m2.

**By class:** HELD **587.2845** (74.1 %), UNRESOLVED 101.4319 (12.8 %), RULE_DIFFERENCE 65.1486 (8.2 %: boundary
74.40, heights -9.2514), ENGINE_RIGHT 41.0513 (5.2 %), TOLERANCE -2.0193; ENGINE_WRONG **none found**.

## 3. How unique is this (ERS s.2 step 4)

The partition of his total is HIS (section rows); the engine side is exact. Row 1-3 decompositions are an identity
(gross = length x mean height), so the split between rows k (height) and m (length) depends on the mean-height
definition; the HELD rows are carried figures on the established pieces and change when the held facts are printed.
Parapet hypothesis H1 (not a component): his 42.85 m x 1.80 = the 1F roof chain (+9.70: engine 49.233 m, mean 1.171 m
above finish); his 66 m x 1.00 = the GF terrace + annex chains (58.555 m at 0.50); his unlabelled 29.80 m x 1.00 =
2 x (8.100 + 6.800), the +13.90 roof's outer parapet faces (2F chain 29.050 m centreline at 0.50). Under H1 his height
exceeds the printed height above the finished roof by 0.50 m on three chains and 0.63 m on the 1F roof: he measures
parapets from the slab, i.e. through the roof build-up b_edge the engine holds (D-39). His 0.50 is never adopted.

Openings (rows l + 7, -26.28 m2 in all): his openings total 112.55 + 9.84 = 122.39 m2 vs the engine's established
deductions 96.106 m2 (GF 42.660, 1F 41.851, 2F 11.595; held openings are not deducted, they hold their wall). He
takes every door at 2.40 m (25.40 m of door width at 2.40 in his sheet); the engine uses the owner fallback 2.20 m
(Q-55 C, fact OPENING.DOOR.FALLBACK_HEIGHT) where no head height is printed: at most 25.40 x 0.20 = 5.08 m2 of the
-26.28 is that rule difference (beside, not a row: his doors are not matched to engine walls here). Projections
(row 6): candidates from merged work are the facade frames (T-172: NW pool-court arch frame based at +5.50, SE
stair-tower frame), both HELD on their profile; no 7.50 x 5.50 masonry element was read this run (drawings not
re-opened).

## 4. Verdict proposals (for the Checker)

- 1-3 storey walls: HELD scope dominates (GF 307.72 of which 305.58 HELD; 1F 82.50 of which 88.96 HELD; 2F 123.94 of
  which 132.34 HELD); after HELD the per-floor remainder is RULE_DIFFERENCE (heights) + UNRESOLVED (openings census
  -16.44, length census +15.00): no ENGINE_WRONG and no fix row. Engine wall figures were not re-measured here.
- 4 boundary wall: RULE_DIFFERENCE (classification); compare under EXT.FENCE.*, not B9.
- 5 parapets: RC upstand ENGINE_RIGHT (P1 detail, Checker's own p.14 read, T-319); block part HELD (Q-65 C);
  height below finish HELD (D-39). Freelancer books concrete as block.
- 6 projections: UNRESOLVED: no physical element identified (T-225 also found no wall run).
- The V3.0.41 'RANGE_OPEN, no %' pair is now a closed table: 74 % of the 792.90 m2 gap is HELD scope (never 0), 13 %
  UNRESOLVED and named, 8 % rule difference, 5 % concrete that is not masonry.

F-T543-1: register V2 carries 1F-W11 at gross 0.888 - deductions 1.760 = -0.872 (the held opening's deduction set
against the established piece, while the opening sits in its held length 4.010 m); no line effect (the wall is HELD);
a carried figure below 0 is a register artefact to be fixed when the wall is closed.

## 5. Lesson row (proposed, ERS s.7)

| 2026-11-06 | the blockwork pair stayed 'RANGE_OPEN, no %' from V3.0.20 to V3.0.58 | his total mixes walls, a boundary wall, parapets and a facade row; the engine side was HELD by wall | R-T543-1 (every villa): partition the freelancer total into his own rows, partition the engine's valued lines onto the same components (both exact), decompose storey walls into HELD-by-cause + drift + height + openings + one named length residual; HELD never 0 or agreement; engine-only HELD scope beside the table | tests/t543_blockwork_reconcile (B543 by hand; adverse held-as-0, held-as-agreement, partition / stale totals, lm / mm, tampered split, unallocated deduction) | proposed |

Missing: the held facts (annex roof datum, lift tie beam size, drops d, b_r, b_edge, held openings, parapet material),
the 1F projections element, his opening schedule by wall, an independent re-measure of the engine wall figures.
