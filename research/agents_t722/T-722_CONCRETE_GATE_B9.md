# T-722: CONCRETE GATE B ROUND 9 integration package, ARCH_TAKEOFF_V3.0.73 (lane I)

Worker 3, 2026-11-12. INTEGRATION PACKAGE for Checker Gate B. Base: the candidate of record V3.0.72 (T-703, Gate B
PASS, merge da1a8906, BOQ_FAMILY_MASTER 1.73.0); released default V2.9 + route G untouched; nothing released. No
drawing, workbook, client name or coordinate here; Drive files named by folder and title only.

## 1. What is wired (Checker-merged only)

| source | merge | Checker | wired as |
|---|---|---|---|
| T-707 `out/T707_COLUMN_TAIL.json` (R-T707-1 plate transfer, R-T707-2 tank columns) | f34a5baa | Verifier 2026-11-11T15:58Z Gate A PASS, own ST decode (B8 outline, 7 panels, T 18 in P1 / P2, adjacency) | NARROW x 5, AT_LEAST x 2 |
| T-711 `out/T711_LEDGER.json` (R-T711-1..3, blank concrete tail) | 1e06f656 | Verifier 2026-11-11T17:58Z Gate A PASS, own re-measure (lift pit 1.903 AGREE) | AT_LEAST x 3 (lift pit, GF parapet restated, stair), NAMED x 4, confirmed x 8 |
| T-712 `out/T712_LEDGER.json` (R-T712-1..3, ground-beam floors) | dfeb0240 | Verifier 2026-11-11T20:55Z Gate A PASS, own ST re-measure by handle | AT_LEAST x 4 (1 new, 3 restated), NAMED x 3, confirmed x 13 |
| T-721 `out/T721_LEDGER.json` (R-T721-1..3, beam blanks, east ring) | 9e1ed6c5 | Verifier 2026-11-11T22:05Z Gate A PASS, own ring re-measure 0.115155 AGREE | AT_LEAST x 1, NAMED x 11 |
| T-723 `out/T723_READINESS.json` (R-T723-1 map, hub T-722, 54 rows) | 5d00f738 | Verifier 2026-11-11T23:51Z Gate A PASS | the line-by-line map; F-T723-1 .. -3 handled below |

Every ledger is sha-pinned and REBUILT by its own merged builder (`t707_alsenan` / `t711_alsenan` / `t712_alsenan` /
`t721_alsenan`.build()) and asserted equal to the committed file before any entry is formed (`t722_inputs.py`).

## 2. Method (R-T722-1, every villa; module `engine/source/arch_v3073.py`)

- Physical element first (ERS s.2.1): each line is one member (a column shaft to the slab top, a ground-beam band
  stretch, a parapet RC above the slab top, a lift pit wall ring, a stair remainder, a ring beam, an edge projection).
  Its line quantity is a value in [lo, hi] (bounded), or a blank with a LOWER end only (the upper end open by a named
  designer item), or a blank with the deciding item named.
- NARROW: a held column whose low is raised by a slab-top lower bound on ONE plane (R-T707-1): low = least section
  reading x least height, RECOMPUTED here from the ledger's terms (Decimal, floored at 6 dp, R-T696-1) and asserted
  equal to the ledger; the high end kept; the new range inside the old (never widened); a range from 0 refused.
- AT_LEAST: a figure > 0 BESIDE a blank line, never in it, never a range, never summed into a code total.
- One live statement per line (R-T723-1 (4)): the LIVE record is the latest version that restated the line (V3.0.23
  parapet record, then the concrete rounds V3.0.62 .. V3.0.71 in order; a later range / value / blank clears an earlier
  figure). The SAME figure already live -> confirmed in the run log (never restated); a DIFFERENT live figure -> the
  entry must name it (record + value) and is restated (concrete records moved under `superseded`; the V3.0.23 parapet
  record kept as history because it also holds the upper reading and the block alternative); undeclared -> refused.
- NAMED: a blank line with no live figure gains the exact holding item and, where the ledger states it, a measure per
  unit of the missing datum (information only); a NAMED entry on a line with a live figure is refused.
- Totals: only STR.CONC.*|m3 move, each exactly by the restatement (asserted); released never moves (asserted).

Owner manual method vs drawing-derived method, side by side (per family): owner = member section x storey height /
run (columns, beams, ground beams, parapets), steps + waist (stairs), a datum the drawings do not print held with the
designer list (no generic value); drawing = the merged ledgers: a column low from the one-plane 2F roof slab top
(plate P1 .. P7 thickness by panel, base +9.65) x the least section reading; a blank member's AT_LEAST from the drawn
plan area or section x the least printed depth / height that must exist (+0.25 annex literal, least title 0.30 /
0.40 m on a loaded run, upstand 0.30, the printed bar stack 0.064 m, the pit height 1.73 m = +0.95 - (-0.78)).

## 3. Lines (m3; beside figures never summed)

| family / line | V3.0.72 | V3.0.73 | hand (ledger terms) | held on |
|---|---|---|---|---|
| COLUMN C9 2F 418 L-53f223b0 | 0.4242 .. 0.595 | **0.45738** .. 0.595 | 0.14 x 3.267 | D-39 high end |
| COLUMN C2 2F 41B L-26f6b6f2 | 0.303 .. 0.425 | **0.3287** .. 0.425 | 0.10 x 3.287 | D-39 |
| COLUMN C2 2F 41E L-33a9b772 | 0.303 .. 0.425 | **0.3267** .. 0.425 | 0.10 x 3.267 | D-39 |
| COLUMN C1 2F 421 L-d79d17d1 | 0.303 .. 0.425 | **0.3287** .. 0.425 | 0.10 x 3.287 | D-39 |
| COLUMN PC-2F 778 L-541c7e56 | 0.1824 .. 0.35 | **0.20136** .. 0.35 | min(0.08, 0.10) x 2.517 | D-39, D-66 section |
| COLUMN C2 / C3 2F tank L-0ede77cf / L-c10e2945 | blank | blank, AT_LEAST 0.3287 each | 0.10 x 3.287 | D-44 (B15 up / down stand) |
| LIFT pit walls L-684fcad3 | blank, 1.1 m2 plan (V3.0.33) | + AT_LEAST 1.903 | (1.6 - 0.5) x 1.73 | D-43 / D-63 pit depth |
| LIFT GF tie beam L-5ae06fda | blank, 5.5 m (V3.0.46) | NAMED D-43 | 5.500 m3 per m2 of section | D-43 |
| PARAPET GF terrace L-b5ffc172 | blank, V3.0.23 floor 1.677887 | AT_LEAST **1.677886** (restated) | 5.592956 x 0.30 = 1.6778868 floored | Q-65 C + D-39 |
| PARAPET annex / 1F / 2F roof | V3.0.23 floors 1.799103 / 2.949453 / 1.6245 | confirmed (same) | tops x 0.30 | Q-65 C + D-39 |
| STAIR ST-01 GF -> 1F L-7863355d | blank | AT_LEAST 1.213429 | reading A (27 risers) | C-ST-4, D-67 / C-ST-3 |
| STAIR E1 L-061e18cf | AT_LEAST 0.355017 (V3.0.66) | confirmed | 0.357 - 0.001983 | S-9 |
| STAIR MS2 turn / D1 lobby / ST-02 | blank | NAMED C-ST-3 / S-9 / D-08 | per-unit text | designer |
| GROUND_BEAM L-e16c9807 | AT_LEAST 0.135473 (V3.0.63) | **0.135481** (restated) | 0.541924732 x 0.25 | D-35 |
| GROUND_BEAM L-0bb78acc / L-d53e5eb0 | AT_LEAST 0.242309 / 0.147657 | **0.242308 / 0.147656** | area x 0.30, floored | D-33 |
| GROUND_BEAM junction L-be6708e0 | blank | AT_LEAST 0.0075 | 0.10 x 0.30 x 0.25 | D-35 |
| GROUND_BEAM 13 others | AT_LEAST (V3.0.63 / .64) | confirmed (same) | T-712 = live figure | D-33 / D-35 |
| GROUND_BEAM court x 3 | blank | NAMED D-35 (court) | 0.18 / 1.14 / 0.39-0.415 m3 per m depth | D-35 |
| BEAM east dome ring L-ab37afa1 | blank | AT_LEAST 0.115155 | 1.7993 x 0.064 | D-28 |
| BEAM edge projections x 11 | blank | NAMED D-05 / D-26 | m3 per m of depth | D-05 / D-26 |
| NECK lift necks x 4 | AT_LEAST 0.173 x 3 / 0.4325 (V3.0.62) | confirmed | | D-43 / D-63 |

## 4. Run of record, census, diff

Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) and 'ST7757 dxf.dxf'
(9f9d1179), decoded by the wrapper into the private folder only: own fresh t167 `v304_run.py` (about 25 min) ->
`research/agents_t722/v3073_run.py` (exit 0): every earlier version re-run and asserted (V3_0_70 e8e001de, V3_0_71
fc0bd98f by the T-703 / T-704 wrappers), **V3_0_72 f9578744 (asserted = the T-703 run of record by its line index)**
-> **V3_0_73 c5a0b128**, 5,123 lines; replaced 33 (NARROW 5, AT_LEAST 10, NAMED 18), added 0, outside 5,090
byte-identical (asserted); 21 lines confirmed unchanged (figure, record and line sha in the run log). Diff vs V3.0.72:
CHANGED 33, SAME 5,090. vs released V2.9 + route G: NOT_IN_RELEASED 3,531, QUANTITY_DIFFERS 1,054, SAME_QUANTITY 538,
unchanged from V3.0.72. Totals moved (asserted equal to the restatement): **STR.CONC.COLUMN|m3 held low 11.67283 ->
11.80007 (+0.12724)**, held high 15.5015, released 19.7765, 27 bounded / 2 blocked: unchanged; no other code total
moves. Census `t479_registry_census.py` (unchanged; verdicts board verdicts/V3.0.44 b3b08dd7, downgrades 81732639) on
V3_0_72 reproduces `research/agents_t703/out/LINE_INDEX_V3_0_72.json` byte for byte; on V3_0_73 ->
`out/LINE_INDEX_V3_0_73.json` (af8d567d), issues {}, complete map, 0 stale blocks; vs V3.0.72 exactly the 5 column lows
differ (a beside figure or a name is not in the index). `t722_package_families.py` (chain 72 -> 73): B10-06 changed
(COLUMN 5 + 2 record), record B10-04 / B10-07 / B10-10 / B10-12 / B7-12. Summary `out/T722_SUMMARY.json` (rows,
census before / after, confirmed, restated; no element coordinates).

STR.CONC census (m3; beside figures are a run-record sum, never summed into released or a range):

| code | released | bounded low .. high | blank | blank with AT_LEAST beside V3.0.72 -> V3.0.73 |
|---|---|---|---|---|
| COLUMN | 30, 19.7765 | 27, 11.67283 -> **11.80007** .. 15.5015 | 2 | 0 -> 2 (0.6574) |
| GROUND_BEAM | 32, 23.760555 | 8, 1.178378 .. 1.571171 | 21 (incl. L-fb7a6431, a 0 .. 3.5256 record) | 16 (5.092339) -> 17 (**5.099845**) |
| BEAM | 112, 66.920677 | 14, 5.983229 .. 8.41271 | 12 | 0 -> 1 (0.115155) |
| STAIR | 6, 5.368881 | 0 | 5 | 1 (0.355017) -> 2 (1.568446) |
| PARAPET | 0 | 0 | 4 | 4 (8.050943, V3.0.23) -> 4 (**8.050942**) |
| LIFT | 0 | 0 | 2 | 0 -> 1 (1.903) |
| NECK | 0 | 32, 8.7724 .. 11.346 (T-723 index census) | 4 | 4 (0.9515) confirmed, no NECK line changed |

GROUND_BEAM beside 5.092339 on V3.0.72 (= T-723) -> 5.099845 = the T-712 family figure (+0.0075 junction L-be6708e0,
+8e-6 / -1e-6 / -1e-6 restated). PARAPET 8.050943 -> 8.050942 (the GF terrace floor restated down by 1e-6).

## 5. Findings, held / missing, downstream, verdicts

- **F-T722-1 (two concrete records on one line).** V3.0.64 restated 6 lines without removing the V3.0.63 record
  (5 BOUND beams, ground beam L-6bf14711: V3.0.63 AT_LEAST 0.09 and V3.0.64 AT_LEAST 0.1125 both in the inputs). The
  T-723 register (rebuilt from the builders) took the later one; the module now reads the LIVE record the same way
  (latest version present), so L-6bf14711 is confirmed at 0.1125 and the 0.09 is history. No line changed by this.
- **F-T722-2 (V3.0.23 parapet floors are live figures).** The T-723 BESIDE rows on the 4 parapets carried
  CONFIRM_ON_LIVE: the live V3.0.23 record already states the floor. 3 are equal (confirmed, not restated: same lesson
  as F-T704-1); the GF terrace floor 1.677887 was rounded half-UP above the exact lower end 1.6778868 (by 2e-7 m3):
  restated to 1.677886 (R-T696-1), the V3.0.23 record kept as history with its upper reading and block alternative.
  The lift pit's earlier figure is a 1.1 m2 PLAN (V3.0.33) and the tie beam's a 5.5 m LENGTH (V3.0.46), not m3
  figures: the AT_LEAST 1.903 m3 sits beside them (1.1 x 1.73), no conflict.
- **F-T723-3 answered (form of L-fb7a6431).** The boundary G.B at N.G. line is BLOCKED_RFI (blank) with a 0 .. 3.5256
  record in its bounded_range field (V3.0.17 / V3.0.35): the code totals and this census count it blank; no merged
  ledger restates it, so it is untouched here (a range from 0 is not a bound, R-T722-1 (f)). For the Lead: a lane S
  row may give it a drawn lower end (gross 44.07 x 0.2 x 0.4 less the column joints once counted) or name it.
  T-724 (MERGED cfca9394 after this row was claimed; research, unwired) now states its one form: HELD BLANK with the
  gross 3.5256 as a cap beside (R-T724-3), plus 4 NAMED blank roof-edge children (0.378618 m2) and the T-714 soffit
  scale fix: these are concrete round 10 / the formwork hub, not this package (no T-724 line is in the T-723 map). T-724
  keeps the east ring floor 0.115155 (F-V721-1): consistent with the line wired here.
- Held: every changed line stays HELD (5 bounded, 28 blank); every upper end open on its named designer item (D-39,
  D-44, D-43 / D-63, Q-65 C + D-39, C-ST-4 / D-67 / C-ST-3, S-9, D-08, D-33, D-35, D-28, D-05 / D-26).
- Downstream: the formwork lines of the 5 restated columns follow in the T-714 formwork package (WAITING
  T722_FORMWORK); no formwork, masonry or finish line moves here.
- Freelancer: lift walls 8.00 x 0.20 x 1.50 = 2.400 incl. column pieces 0.750, net 1.650 < drawn floor 1.903:
  ENGINE_RIGHT on the low end (his flat 1.50 is not a printed height; the drawn minimum is 1.73). Ground beams: his
  section on the 20 drawn plans 11.116685 m3 sits above the AT_LEAST 5.099845 (no contradiction; depth UNRESOLVED on
  D-33 / D-35). Columns / parapets / ring: no comparable freelancer row (NOT_COMPARABLE).
- Verdict proposals: 5 NARROW ENGINE_RIGHT as bounds (Checker AGREE on the plate / adjacency in T-707 Gate A), 10
  AT_LEAST ENGINE_RIGHT as lower ends (4 Checker re-measured in Gate A), 18 NAMED UNRESOLVED with the item named.

Lesson row (ERS s.7, proposed): | 2026-11-12 | a register built from round builders showed one figure per line, the
live line carried two concrete records (V3.0.63 + V3.0.64) and a V3.0.23 parapet floor outside the register | a
restatement record left the earlier record in place; a non-concrete record carried an m3 floor | the live statement
of a line is its LATEST record (version order), read on the live line before BESIDE / RESTATE / CONFIRM; a lower end
printed from a half-up rounding is restated floored (R-T696-1) | tests/t722_concrete_side test_later_concrete_record_
is_the_live_one / test_v3023_figure_restated_only_when_named | PROPOSED |

Tests (`tests/t722_concrete_side`, villa C722 by hand, non-Alsenan): normal (2 column lows 0.325 / 0.28051, tank
AT_LEAST 0.33, ground beam restated 0.135473 -> 0.135481, same figure confirmed, parapet half-up floor restated
1.677887 -> 1.677886 with the V3.0.23 record kept, NAMED with per-unit text, totals COLUMN held_low +0.02551 only,
outside lines byte-identical, mirror order, census, written files); adverse (low not recomputed, high moved, widened,
unmoved, cm2 / mm unit slips, range from 0, stale binding, blank line narrowed, AT_LEAST 0 / negative / slip / range,
undeclared second figure, wrong restated value, restating a line with no figure, same figure restated, confirm wrong
value, NAMED over a figure, released / non-concrete line, unknown action, schema, project, applied twice, tampered
line; later record live, later range clears); inputs (pins, ledgers rebuilt, 33 + 21, recomputed lows +0.12724, GB
family 5.099845, adverse map action / ledger figure); family master 1.74.0 (pending; builder; adverse as T-703).
