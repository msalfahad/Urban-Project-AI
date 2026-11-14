# T-779 blockwork -22.2 % and internal plaster +5.8 % vs the freelancer: named causes (research, unwired)

Worker 2 (lane A), 2026-11-14, claim 04:45 UTC. Files: `t779_split.py` (R-T779-1, every villa; inputs sha256-pinned,
`--check`), `out/T779_SPLIT.json` (every table), `out/FIX_ROWS.json` (one basis-text fix row). No engine module,
method, rule / knowledge version, registry or candidate file changed; no quantity moves. A reference comparison:
freelancer agreement is never proof. His figures are the numeric cells already parsed into the repository
(tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json: masonry and plaster workbooks; T-543 section sub-totals),
re-checked this run row by row (Drive "Alsenan chalet project" listing read OK; no workbook text stored).

## 1. Blockwork: ours 981.348 vs his 1,260.6895 m2 (-279.342, -22.16 %), exact

Ours = V3.0.82 MAS.BLOCK released lines (467.79) + T-765 fix rows (MERGED 3b9f35a6): GF 442.127, 1F 391.526,
2F 129.306, below ground 18.389. His sheet (three sections, one flat height per floor and zone: GF 4.00 / 3.50
annex / 3.25, 1F 3.70 / 3.45, 2F 3.45 / 3.70; every door at 2.40 high).

| # | Cause (his - ours, m2) | m2 | % of his | Class |
|---|---|---|---|---|
| 1 | his three parapet rows (42.85 x 1.80, 66.00 x 1.00, 29.80 x 1.00) booked as block | +172.930 | 13.7 | RULE_DIFFERENCE: RC upstand 0.30 = concrete (P1 detail, ENGINE_RIGHT 41.05); block above HELD Q-65 C; his height from the slab (T-543 5a-5d) |
| 2 | his boundary wall row 37.20 x 2.00 | +74.400 | 5.9 | RULE_DIFFERENCE: family placement; ours under EXT.FENCE.WALL |
| 3 | his 1F 'projections' row 7.50 x 5.50 | +41.250 | 3.3 | UNRESOLVED: no masonry element (facade frames HELD, T-172) |
| 4 | his 20 cm openings with no floor | -9.840 | -0.8 | UNRESOLVED (inside his storey walls below) |
| 5 | below-ground block under the neighbour-side beams (note p.1 n.2), ours only | -18.389 | -1.5 | ENGINE_RIGHT on scope; value ESTIMATE |
| 6 | storey walls GF / 1F / 2F (table 1b) | +18.991 | 1.5 | split below |
| | **total** | **+279.342** | **22.16** | closes exactly |

**Like for like (storey walls, his 9.84 openings included): ours 962.959 vs his 972.110 m2: -9.151, -0.94 %.**
The -22 % is scope: 288.58 m2 of his masonry total is parapets, a boundary wall and a facade row that are not
storey walls; we also carry 18.39 m2 of below-ground block he omits.

1b. Storey walls per floor (T-543 identity carried; every HELD carried figure replaced by the T-765 value of the same
walls):

| Row (his - ours) | GF | 1F | 2F | Class |
|---|---|---|---|---|
| his net / ours | 466.955 / 442.127 | 391.060 / 391.526 | 123.935 / 129.306 | |
| height: his flat heights vs clear height under each member | +2.524 | -7.299 | -4.477 | RULE_DIFFERENCE (Q-60 A / Q-72) |
| openings census (his deductions - ours, established walls) | -5.780 | -8.499 | -2.165 | UNRESOLVED (of which at most 25.40 m x 0.20 = 5.08: his 2.40 door head vs company default 2.20) |
| wall-length census (his length - ours) | +5.519 | +11.242 | -1.761 | UNRESOLVED |
| fill: openings now deducted on held-opening walls (GF W15 / W26; 1F W07 / W14+15 / W16) | +7.200 | +4.300 | | FILL_CHANGE (Q-73) |
| fill: lift walls, T-761 tie-beam faces + lift doors deducted | +7.330 | | | FILL_CHANGE |
| fill: glazed strips H01 / H02 / W37 = 0 block; W03 / W30 / W36 filled | +7.507 | | | FILL_CHANGE (main chat 13 Nov default) |
| fill: sunken-panel drop walls, recess 0.30 default | +2.274 | | | FILL_CHANGE (D-41 default) |
| fill: annex walls at 3.84 / 4.00 - beam | -1.619 | | | FILL_CHANGE |
| fill: dome / member pieces at the ring soffit | | +1.689 | | FILL_CHANGE |
| fill: 2F at the owner +13.90 datum (b_r 0) vs the old b_r 0.05 what-if | | | +3.032 | FILL_CHANGE |
| version drift / print rounding | -0.121 | -1.899 | 0.000 | TOLERANCE |
| **sum** | **+24.828** | **-0.466** | **-5.371** | exact |

Storey-wall totals by class: FILL_CHANGE +31.705 (what the fills did to the carried figures), RULE_DIFFERENCE
-9.251, UNRESOLVED -1.444 net (openings -16.444, length +15.000), TOLERANCE -2.019.

Colour (procurement, beside): ours white 400.30 / black 581.05 m2; his external section 559.80 (518.55 without the
projections row) / internal 15 + 20 cm 700.89 (453.56 without boundary and parapets). His 'external' is wider than
our white set by about 118 m2 (annex and drop walls we class black under Q-60 fallback / drawing notes): a block-count
split, not an area difference; UNRESOLVED (no per-wall rows on his side).

Estimates checked: white face 6.4 / m2 stays ESTIMATE (Q-60 gives two supplier faces, 62.5 x 25 -> 6.4 and 60 x 20
-> 8.33; no block size printed on the sheets read by T-225 / T-670). Below-ground 0.70 m is NOT a printed depth: it
is the lower bound h >= 0.70 derived in T-407 (footing top -0.85 vs slab -0.10 + 0.80); the T-765 basis text says
'the only printed depth' -> fix row F-T779-1 (basis text only, value 11.389 unchanged, ESTIMATE kept).

## 2. Internal plaster: the +5.8 % is a class mix; like for like ours is -13.0 %

Ours = V3.0.81 FIN.PLASTER + T-763 r2 fix rows = 1,622.000 m2: dry rooms 866.126, stair shaft 151.521, wet render
417.520 (incl. the pantry GF-07 levelling render 32.342 under full-height porcelain, T-740 / T-329), wet band above the
tile top 159.364, returns 26.614, GF-08 band share 0.855. His plaster statement rows 4-26 = 1,209.385: dry rooms
924.205, stair 244.920, a wash room (wet) 24.300, door returns 15.960; his 1,169.125 = dry + stair.

Board pair 1,236.822 vs 1,169.125 (+67.70), split (his - ours):

| Cause | m2 | Class |
|---|---|---|
| dry rooms (11) | +58.079 | split 2b |
| stair shaft | +93.399 | split 2c |
| pantry render counted as dry in the board figure (it is wet render; his pantry is in his tile / spatter rows) | -32.342 | KEYMAP (F-T779-2) |
| wet-room band above the 3.00 tile top to the soffit: ours only (he has no band row) | -159.364 | RULE_DIFFERENCE (scope) |
| returns by id (his row 26, 15.96, sits outside his 1,169.1) | -26.614 | RULE_DIFFERENCE (scope) |
| GF-08 band share | -0.855 | TOLERANCE |
| **sum** | **-67.697** | exact |

**Like for like (dry + shaft): ours 1,017.647 vs his 1,169.125 m2: -151.478, -12.96 %.**

2b. Dry rooms, per room (his L x H vs ours L x H - openings - beam ends, MAIN_FILL_2 bases), totals:
LENGTH +55.789 (1F-10 +20.74 and 1F-13 +35.33 his longer runs; ENGINE_RIGHT on the T-128 two traces; others
-1.75 .. +3.82), HEIGHT -150.043 (his 3.60 / 3.40 / 3.50 flat vs owner 4.34 / 3.84 annex / 4.04: RULE_DIFFERENCE,
ours on the owner height rule), DEDUCTIONS +152.333 (we deduct every opening and beam end in full, Q-73; his gross
deducts none: RULE_DIFFERENCE), rounding -0.001.

2c. Shaft (his rows 8, 23, 24 = 244.92 vs ours 151.521): his box 14.8 x 12.9 vs the drawn faces (T-680 gross 177.07)
+13.85 ENGINE_RIGHT; our deductions (openings, winder body, B20 / B23 ends) and the storey - slab face model +25.549
RULE_DIFFERENCE; his rows 11.25 x 3.60 and 2.50 x 5.40 with no drawn face +54.00 **UNRESOLVED** (4.6 % of his
1,169.1). Observation, not adopted: his box height 12.9 = 4.50 + 4.20 + 4.20, the full structural height from GF, so
the GF stair faces are already inside his row 23; row 8 is a second GF stair face (a duplicate is possible; T-173 /
T-634 found no drawn face for it).

## 3. Verdict proposals (Checker)

- Blockwork: like-for-like storey walls -0.94 % (inside the 1 % floor); the -22.2 % is RULE_DIFFERENCE scope (his
  parapets 172.93 and boundary wall 74.40 in masonry) + UNRESOLVED projections 41.25 + ENGINE_RIGHT below-ground
  18.39. Residual named and unresolved: openings census -16.44 vs length census +15.00 (net -1.44, 0.11 % of his).
- Plaster: the +5.8 % headline compares different classes. Report dry + shaft vs his 1,169.1 (-12.96 %): height
  RULE_DIFFERENCE (owner rule), deductions RULE_DIFFERENCE (Q-73), lengths ENGINE_RIGHT, 54.00 UNRESOLVED.
  Wet band (159.36) and returns (26.61) beside, ours only; pantry 32.34 belongs to wet render.
- No line of ours was shown wrong by a drawing this run (no drawing re-measure; values rest on merged, Checker-passed
  ledgers). Fix rows: F-T779-1 basis text only. Keymap finding F-T779-2 for the Lead / T-180 workbook.

## 4. Lesson row (proposed, ERS s.7)

| 2026-11-14 | blockwork read -22 % and plaster +5.8 % after the fills | both headline pairs compared different face classes (his parapets / fence / facade row in masonry; our wet band, returns and pantry render in plaster) | R-T779-1: put both totals on the same face classes first; a class only one side books is a scope row; storey walls by the T-543 identity with each carried HELD figure replaced by the released fill | `t779_split.py --check` (all identities assert exact) | proposed |

Missing: his opening schedule by wall (to split the openings / length censuses), the 1F 'projections' element, the
two stair rows by id, an own drawing re-measure of the engine walls.
