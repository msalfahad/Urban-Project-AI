# T-299 Reinforcement ledger reconciliation by element id and bar group (READ ONLY; Alsenan; every villa)

Worker 1 (lane S), 2026-10-25. Owner Stage B Decision 2 (main chat 11:51, "approved, start now"). NOT new measuring:
merged research ledgers + route G read only. No candidate line, quantity, state, V2.9 cell, frozen module or released
value changes; nothing is wired. Development villa, not an accuracy claim. Drawings named by Drive folder and title only.

Files: `t299_ledger.py` (RECON_LEDGER_V1: pure rules, stdlib), `t299_route_g_extract.py` (route G read only ->
`ROUTE_G_ITEMS_T299.csv` + `ROUTE_G_SUMMARY_T299.json`; values and drawing handles, no coordinates), `t299_alsenan.py`
(-> `RECON_T299.csv`, 3,244 rows, + `RECON_SUMMARY_T299.json`; `--check` rebuilds and compares). Tests
`tests/t299_ledger` (15: villa K299 hand fixture normal + 8 adverse + Alsenan pin).

Repeat: `.work/venv/bin/python -I research/agents_t299/t299_route_g_extract.py <ST7757 dxf> research/agents_t299/ROUTE_G_ITEMS_T299.csv`
(Drive "Alsenan chalet project" / "ST7757 dxf.dxf", sha 9f9d1179, read this run), then
`python3 -I research/agents_t299/t299_alsenan.py --check`.

## 0. Engineering question

The same physical bars appear in several ledgers made at different times and on different bases. Per element id and
bar group: which ledger's figure stands (REPLACES), which is the only record (INDEPENDENT), which repeats bars another
ledger already carries (OVERLAPS, shared part named, counted once), and what has no quantity (HELD, blank, never 0)?
Quantities stay kg internally; t = kg / 1000 once, 6 decimals (OWNER_RULE_REBAR_2026-10-24 s.1).

## 1. Rules applied (RECON_LEDGER_V1, generic; Alsenan only supplies the data)

- One row per (element id, bar group, source); `source_kg` = the source's own number as stored (audit), `quantity_kg`
  blank for HELD / NOT_REQUIRED / COUNT_ONLY.
- A replaced row stays in the table, never counted; the replacing row names it (`replaces`) and the reason.
- In an overlap group only ONE source's rows are counted; a convention ledger (route G) and an alternative round (S3.1)
  are never counted; a restatement (T-273 nets) points at the rows it restates.
- Totals exist only per (family, status class): MEASURED / BOUND / PROVISIONAL / CONVENTION / SOURCE_LABEL. A bound is
  never added to a measured value; the five classes are never added into one figure.
- Residual per source = sum of its rows against its own named total; the stated tolerance is the storage rounding
  (n rows x half a unit of the last stored decimal, + half a unit of the named total's decimals), shown per source.
- Text association: route G's own label binding is kept as evidence; any binding other than BOUND (BOUND_WIDTH_CONFLICT,
  INHERITED_BY_SPAN_SEQUENCE, none) is FLAGGED PROXIMITY_ONLY (23 rows, all route G beams, none counted).
- Q-71 (owner 11:51) for link counts: N = 1 + floor((L - 2a) / s) only where the drawing prints the spacing, the
  first-link offset a and the support faces; otherwise the count stays HELD with the designer item named.

## 2. Columns: S3 vs T-280 (and S3.1, T-273, route G)

| Source | Rows | Relation | kg (source) | Counted |
|---|---|---|---|---|
| S3 FOUNDATION MAIN_CORE | 36 | REPLACED_BY T-280 (label LOWER_BOUND restated CONVENTION: footing underside at the formation limit, 0.17 m underlay omitted) | 974.831 | no |
| T-280 cores, bound | 26 | REPLACES S3 (+ S3.1) row of the same part | **734.781 = 0.734781 t** LOWER BOUND (formation limit + p.13 underlay 0.17 + H; upper OPEN) | yes (BOUND) |
| T-280 cores, HELD | 10 | REPLACES S3 row with HELD: pit depth 4, stopping-column top 3, unbound support 3 | blank (S3 had 173.510) | no |
| S3 other parts | 495 | OVERLAPS S3.1 (alternative round), INDEPENDENT of route G | 6,246.136 | yes (per class) |
| S3 BLOCKED parts | 36 | HELD | 258.197 modelled, not a quantity | no |
| S3.1 (d^2/162 round) | 611 | OVERLAPS S3 / REPLACED_BY T-280 / 44 transition parts HELD | 7,488.184 | never |
| T-273 column restatement | 7 aggregates | OVERLAPS (equals the S3 rows of each component and state: residual 0.000 kg on all 7) | 1,435.938 | never |
| Route G COLUMNS | 118 components | HELD: route G carries no column reinforcement at all (MISSING_DATA) | - | - |

Counted column steel, by class (never summed together): SOURCE_LABEL (S3's own VERIFIED label, no Checker verdict cited)
3,360.903 kg = **3.360903 t**; BOUND 2,266.844 kg = **2.266844 t** (S3 lower bounds 1,532.063 + T-280 734.781);
PROVISIONAL 1,353.170 kg = **1.353170 t** (laps 40 D, starters, anchorages, owner 2026-10-24 s.6 (2)).
Hand check X01-Y01: S3 8 x 2.20 x 1.578336 = 27.779 kg REPLACED_BY T-280 8 x 2.03 x 1.578336 = 25.632 kg.
Finding (named, not fixed): T-280 restates S3 (exact density 7850) while S3.1, T-265, T-149 and T-138 use d^2/162; the
two column rounds differ by +9.054 kg project-wide. Which unit mass the integrated column line takes is lane I's choice
under the owner's unit rule; this ledger counts S3 only because T-280 restates S3's numbers.
Flag: the 17 ANCHORAGE_TOP_STOPPED rows sit at a top datum T-280 holds (stopping columns end in their closing member):
counted as the source states them, flagged T280_STOPPING_COLUMN_TOP_DATUM_HELD.

## 3. Ground beams: T-265 / T-272 vs route G (and T-138, T-273)

| Source | Relation | kg | Counted |
|---|---|---|---|
| T-265 boundary + main exterior TOP / BOTTOM / SIDE (78 rows) | INDEPENDENT of route G (no steel on SH08 bands); 54 of them OVERLAP a T-273 restatement | **1,310.960 = 1.310960 t** DRAWING-CONFIRMED lower bound | yes (BOUND) |
| T-138 face-to-face rows of the same axis pairs (38 rows) | REPLACED_BY T-265: 572.500 kg -> released T-265 rows (T-265 s.4); 320.440 kg -> T-265 HELD (annex CONFLICT, court no section) | 892.940 | no |
| T-138 interior ground beams (LT5M / LT2_5M detail, 36 rows) | INDEPENDENT (no other ledger; route G none) | 301.656 | yes (BOUND) |
| T-138 bars through 7 interior columns (14 rows) | INDEPENDENT of T-265 (outside its face-to-face scope); restated inside the T-273 chains | 58.311 | yes (BOUND) |
| T-265 STIRRUP_COUNT (22) | REPLACED_BY T-272 r2 (per drawn clear span) | count only | - |
| T-272 stirrups (22 runs) | REPLACES the T-265 counts; count HELD in its envelope (exterior 333 .. 392), mass HELD | blank | no |
| T-273 GB nets (60) | OVERLAPS: identical to the T-265 rows; the 6 chain rows = T-265 runs + T-138 through pieces (residual <= 0.002 kg, rounding) | 1,363.584 (net, restated) | never |
| T-273 GB laps (60) | HELD 32 / NOT_REQUIRED 28 (no lap rule printed for ground-beam bars) | blank | no |
| Route G GROUND_BEAMS SH08 (59 bands) | HELD: no steel item (MISSING_DATA) | - | - |

Counted ground-beam steel: BOUND 1,670.927 kg = **1.670927 t** (T-265 1,310.960 + T-138 interior 301.656 + through
58.311). Straps (route G's only ground-beam steel, SH10):

| Strap / group | T-138 (hand, clear between footing faces) | Route G (convention: + 2 anchorages, n/m x L + 1 links) |
|---|---|---|
| SB1 TOP 13ø18 / BOTTOM 7ø16 | 118.300 / 50.331 kg LOWER BOUND, counted (clear 4.55 m between footing faces) | 185.641 / 77.211 kg: bar length 5.70 + 2 x 40 d (low = 5.70 m, base 7.14 / 6.98 m); +67.341 / +26.880 kg = a 1.15 m longer span (5.70 vs 4.55 m) + two 40 d anchorages T-138 holds as ends 40 d .. 70 d |
| SB3 TOP 5ø18 / BOTTOM 5ø16 | 32.580 / 25.742 kg LOWER BOUND, counted | 47.120 / 35.966 kg |
| SB2 TOP / BOTTOM | HELD (drawing-resolved candidate, Checker to confirm) | 148.123 / 55.989 kg, blocker SCHEDULE_DUPLICATE_MARK |
| links SB1 / SB2 / SB3 | HELD (Q-71 count, inner legs not drawn, hooks) | 42.894 / 27.352 / 16.337 kg |

Straps counted: 226.953 kg = **0.226953 t** (BOUND); route G strap total 636.634 kg never counted (OVERLAPS).
Q-71 on ground-beam stirrups: p.13 / p.14 print the spacing only; no first-link offset and no support-face reference
for ground beams. The 7.5 cm offset is printed on the p.11 / p.12 continuous-beam details and is NOT carried to
another detail (ERS s.3): every GB stirrup count stays HELD in T-272's envelope; designer item S9
(CLARIFICATIONS_CONSULTANT_2026-10-24: "end zone and shape, hook / leg details").

## 4. Beams: T-149 vs route G (handed in as well; beams were the named stop point)

Overlap groups by (floor, mark, bar group); route G binding evidence kept; 23 route G rows FLAGGED PROXIMITY_ONLY.

| Bar group | T-149 net counted (DRAWING-CONFIRMED lower bound, face to face) | T-149 HELD | Route G (CONVENTION, never counted) |
|---|---|---|---|
| bottom | 3,565.939 | 563.658 (width conflicts, candidates) | 4,874.411 (net + 2 anchorage lengths) |
| top | 1,022.699 | 184.539 | 1,231.875 (net + 2 anchorages) |
| support bars over interior supports (0.22 Ln) | 376.707 | 14.590 | 340.458 |
| continuous top corner bars | 152.445 | 9.085 | UNRESOLVED (blank) |
| links | HELD (A 1,963.12 on released members) | 2,307.047 source kg, all HELD | 1,931.808 ((n/m x L + 1), code hooks) |
| side bars / MIDDLE REINT. | HELD (at least 361.94) | | none (T-300) |
| ends, note 9 | HELD 1,610.85 .. 2,818.98 | | inside the route G bottom / top lengths |

T-149 counted: 5,171.031 kg = **5.171031 t** (BOUND), of which 53.241 kg on 5 rows with no route G row of the same
mark / floor / group (INDEPENDENT). Every route G beam kg row (8,378.552 kg) falls in a T-149 group: route G has no
beam bar group that T-149 lacks. Q-71 on beam links: for the 30 continuous-beam link rows the printed 7.5 cm offset
applies: N = 1 + floor((L - 0.15) / s) with s = 1 / n read from the printed per-metre rate (a notation reading); it
equals the rate count ceil(n x zone) on 26 rows and differs by one on 4; count PROVISIONAL (junctions, zones, an extra
terminal link not re-checked); mass HELD (hooks S21, nested links S20). Simple-beam links (102 rows): no offset printed
-> count HELD (S21).

## 5. Residuals (each source against its own named totals; t at 6 decimals)

| Source (named total) | Rows kg | Named kg | Residual | Tolerance (storage rounding) |
|---|---|---|---|---|
| S3 (release register total) | 7,479.164 | 7,479.151 | +0.013 kg = 0.000013 t | 0.281 (560 rows at 3 dp) |
| S3.1 | 7,488.184 | 7,488.205 | -0.021 kg = -0.000021 t | 0.281 |
| T-280 bound rows | 734.781 | 734.781 | 0.000 | |
| T-265 families | 1,310.960 | 1,310.960 | 0.000 | |
| T-138 'Released total' | 1,479.860 | 1,479.86 | 0.000 | |
| T-149 RELEASED / HELD_DEFINED / links / ends / side / end column (9 named totals) | | | <= 0.003 kg each | <= 0.120 |
| T-273 nets HELD / NOT_REQUIRED, column restatement | | | 0.000 | |
| Route G kg items vs its summary PLANNING_BASE | 16,392.647170 | 16,392.647170 | 0.000000 | none |

Every residual is 0.000 t at three decimals; the non-zero kg residuals are the named storage rounding of the source
files (rows stored at 3 dp against totals summed unrounded), not a missing or doubled bar.

## 6. Duplicate bar groups found

- T-280 vs S3 (36 cores): REPLACES; S3's 974.831 kg never added to T-280's 734.781 kg.
- S3.1 vs S3 (531 parts): one bar population in two unit-mass rounds; S3.1 never counted.
- T-273 column summary vs S3 (7 state aggregates, 1,435.938 kg): pure restatement, residual 0.000.
- T-273 GB nets vs T-265 (54 rows) and the two chains vs T-265 runs + T-138 through pieces (6 rows).
- T-138 vs T-265 on 13 axis pairs (38 rows, 892.940 kg): T-265 replaces; join made at AXIS_PAIR level (run splits differ
  between the two registers), flagged PAIR_LEVEL_JOIN for the Checker.
- Route G straps vs T-138 (9 groups) and route G beams vs T-149 (by mark / floor / group): route G is a PROVISIONAL
  SUBTOTAL item set (owner 10:33 (2)), never counted.
- Within T-149: HELD_CANDIDATE rows are alternative schedule candidates of one span (176.86 .. 238.41 kg): never summed.

## 7. Engine vs freelancer; verdict proposals

No BOQ line moves. The freelancer's reinforcement is kg/m3 lumps (44.19 t total; beams 9.89 t, ground beams + GF
9.75 t, footings 5.8 t): no like-for-like line, **RULE_DIFFERENCE, no %** (URBAN-REBAR-NET-AND-PROCUREMENT@v1).
Route G 16.392647 t is a PROVISIONAL SUBTOTAL that omits every column bar (0 of 118 components) and every SH08 ground
beam (0 of 59): **ENGINE (route G) INCOMPLETE** on columns and ground beams, ENGINE_WRONG-by-convention on straps
(clear span + 2 anchorages released as one figure); T-280 over S3 on the 26 cores **ENGINE (S3 ledger) WRONG on its
label** (as T-280); T-265 over T-138 on the main-house exterior **T-265 RIGHT** (Checker-verified geometry).

## 8. Rule proposed (every villa; provenance T-299; a new rule version only when adopted)

**R-REBAR-RECON-1**: before any reinforcement line is integrated, each (element id, bar group) is reconciled across every
ledger that carries it: one row per source; a restatement REPLACES (the replaced row kept, never counted); an alternative
round, a restated net or a convention route OVERLAPS and is never counted; totals only per status class (a bound never
added to a measured figure, alternative ledgers never summed); HELD is blank, never 0; each source's rows reconcile to its
own named totals within the stated storage rounding; kg internally, t = kg / 1000 once at the export boundary; a link
count is computed only from a printed spacing, first-link offset and support faces of THAT detail (Q-71), else HELD.

## 9. Lessons-register row (proposed, ERS s.7)

2026-10-25 | Five reinforcement ledgers of the same Alsenan bars (S3, S3.1, T-280, T-138, T-265 / T-273) each looked
complete | Ledgers were written as restatements of earlier ones (new datum, new geometry, a lap count) without a row-level
link back, so a sum across them would count 974.831 kg of cores twice, 892.940 kg of ground beams twice and 1,363.584 kg
of nets again | Reconcile by (element id, bar group) with REPLACES / OVERLAPS links and per-class totals before any
integration (any villa) | tests/t299_ledger (villa K299 normal; replaced row added back, bound + measured, HELD as 0, kg
and t mixed, overlap counted twice, unflagged proximity, residual outside rounding: all refused) | PROPOSED.

## 10. Not done / uncertain (no quantity chosen; designer items, not owner questions: ERS 2.7 not met)

- Unit mass for the integrated column line (S3 exact density vs S3.1 d^2/162, +9.054 kg): lane I with the unit rule.
- T-138 -> T-265 join is by axis pair, not by run (the two registers split runs differently): the Checker re-checks one
  pair. Hand check 7D0+FC: T-138 4 runs TOP + BOTTOM 231.396 kg; T-265 4 runs 2.975 + 5.745 + 6.35 + 1.2 = 16.27 m x
  9ø16 x 256 / 162 = 231.400 kg (T-138 row rounding) + SIDE 16.27 x 4ø12 x 144 / 162 = 57.849 kg (new in T-265).
- GB stirrup counts / masses (S9), beam link hooks and nested links (S21 / S20), side bars (S19, T-300), beam bar ends
  (note 9 scope, S21), strap SB2 schedule row (D-38), footing '/m' rows (T-171, unchanged, owner asked back).
- Route G footings 3.735907 t, slabs 2.584350 t and ground slab 1.057203 t are listed (so the 16.39 t closes) but not
  reconciled here: no research ledger of those families is in this row's scope.
- S3's VERIFIED label (3.360903 t) is the source's own state; no Checker verdict is cited for it in this ledger.
