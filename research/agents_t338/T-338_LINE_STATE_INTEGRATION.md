# T-338 LINE-STATE TEXT INTEGRATION: ARCH_TAKEOFF_V3.0.24 (integration package, Gate B)

integrates: T-334 (MERGED 39092d8d, Verifier 2026-10-29 11:42 UTC Gate A PASS: the line-state consistency check and its
findings on the candidate). Opt-in candidate ARCH_TAKEOFF_V3.0.24 = the SAME candidate V3.0.23 (candidate of record,
T-319 MERGED 06e46b11, BOQ_LINES json `19f654bd`) + ONE piece, LINE_STATE_TEXT. Released default unchanged (V2.9 +
route G); rollback = run V2.9. **No quantity, state word, range, rfi or line id moves; a status never rises.**

## 1. What the piece fixes (each line from its own record, never a new reading)

| Kind | T-334 finding | Lines | What changes on the line |
|---|---|---|---|
| REBAR_FORMULA | VALUED_WITH_HELD_TEXT | 350 STR.REBAR kg SOURCE_DERIVED (beams 230 / 5,171.031 kg, ground beams + straps 88 / 1,252.907, columns 32 / 1,887.128; = 8,311.066 of 9,185.928 kg released, 90.5 %) | formula `held: ` (the arch_v303.py:235 fallback, empty reasons) -> `count x length_m m x kg/m (d mm, kg/m = d^2 / 162) = net kg (...)` |
| NA_GROSS | HELD_WITH_FIGURE | 1 FIN.SKIRTING lm NOT_APPLICABLE (L-af6fb2d3, GF-RC06FED) | gross 7.6 -> None (kept in calculation.inputs.line_state_v3024.before_gross; base_ownership_v3021.before keeps it too) |
| FORMULA_END | FORMULA_FIGURE_DISAGREES | 15: FIN.PLASTER + FIN.PAINT PROVISIONAL x 2 each (GF-R75FBAE net 56.0131, 1F-RB72F22 net 51.415 m2), BOUNDED x 5 each (GF-RC99C2A, 1F-R0E919A, 1F-R3CFCFD, 1F-R78C367, 2F-R4D1B62), ARCH.SPACE L-554a525e held 1.364 | formula keeps its text (the gross / the garden band's 13.986 m2 stay as readings) and ends `; ARCH_TAKEOFF_V3.0.24: this line net X m2` or `held net LOW m2 .. HIGH m2` |

Every fixed line gets calculation.inputs.line_state_v3024 (kind, before formula / gross, source T-334 file + sha256 +
merge + Checker run, rule R-LINE-STATE-1 / T-338) and one note. Per line: research/agents_t338/V3_0_24_LINE_STATE_FIXES.csv
(engine ids and quantities only).

## 2. The rebar arithmetic, checked line by line (the physical / mathematical cause, ERS s.2.3)

kg/m = d^2 / 162 (engine/source/rebar_unit_mass.py D2_OVER_162; the method of the merged hand ledgers T-138 r2 /
T-148 / T-149, whose unit-mass functions are d*d/162). Diameter from the line's subtrade `<element> / <d> mm`
(arch_v303 writes it from the record's dia_mm). Diameters: 12 mm 89 lines, 14 mm 71, 16 mm 142, 18 mm 47, 20 mm 1.

Reconciled: on 348 / 350 lines `count x length_m x d^2/162` equals the net within 0.0005 kg (the net's 3-decimal
rounding). The other 2 differ by 0.000533 and 0.000800 kg. **Cause found, not a defect:** the ledgers print length_m
to 4 decimals and compute kg from the UNROUNDED length. T-149 R047 CB1 support 1 (L-f80a1217): printed `0.22 x Ln1
7.4500 + support 1 0.5020 + 0.22 x Ln2 5.6010 = 3.3732 m`; unrounded 1.639 + 0.502 + 1.23222 = 3.37322 m; 8 x 3.37322
x 2.000 = 53.97152 -> 53.972 kg (the line's net), while 8 x 3.3732 x 2.000 = 53.9712. T-149 R073 CB9 span 2 top corner
(L-cd587b92): 2 x 1.6338 printed, 2.904 kg; any length 1.63375 .. 1.63378 gives 2.904. Rule applied: the product of
the printed figures must equal the net within the rounding of what is printed, 0.0005 + count x kg/m x 0.5 x 10^-4
(length_decimals 4 named in the inputs with this source); a length printed beyond 4 decimals, or a residual beyond the
bound, is refused (a state question for the Lead, never a text fix). Max residual 0.0008 kg, every line inside its
bound. The formula states both: `= 2.904 kg (the released ledger record's kg, from its unrounded length; the printed
figures multiply to 2.904533, within their rounding 0.000589)`.

## 3. Owner manual method beside the drawing-derived method; evidence status

- Owner manual method: the owner's take-off prints per row the arithmetic that gives the row's figure (count x length x
  unit mass for steel; length x height less openings for faces); a row it does not take carries no figure. Same rule.
- Drawing-derived method: no drawing is read in this package; each line is corrected from its own record. The
  quantities are those of V3.0.23.
- Evidence status (WORKFLOW_CONTROLS s.5): unchanged on every line (the 350 rebar lines keep the V3.0.3 ledger statuses,
  VERIFIED / DRAWING-CONFIRMED as recorded at integration; the finish / space lines keep PROVISIONAL / HELD; the
  skirting line stays NOT_APPLICABLE, ASSUMED — OWNER-APPROVED Q-37 / Q-48). Nothing promoted, nothing released.
- Checker records (docs/agents/verdicts/V3.0.22: 9 verdicts V2 + 2 downgrades, LINE_CONTENT_V1): none binds any of the
  366 changed lines (checked id by id), so every bound line is byte-identical in V3.0.24 and each record re-binds
  mechanically (the Checker's act); no record silently follows a changed line.

## 4. Run and identity (own run, Python 3.11.18)

Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`) and "ST7757 dxf.dxf" (`9f9d1179`),
decoded into the private folder only; research/agents_t167/v304_run.py then research/agents_t319/v3023_run.py:
V3_0_21 json `be22a4e4`, V3_0_22 `7199c8b6`, **V3_0_23 json `19f654bd` / csv `a819c9f8` = the candidate of record,
reproduced**. Then research/agents_t338/v3024_direct.py on it: **V3_0_24_BOQ_LINES json `19394733` / csv `3bd1c5c6`**,
DIFF `6256baef`, INTEGRATION_LEDGER csv `41877846` / json `97068868`, RUN `923eb18f`. FULL CLI: section 7.

Identity (V3_0_24_RUN.json): 3,710 lines = 3,710; replaced 366 (REBAR_FORMULA 350, NA_GROSS 1, FORMULA_END 15), added
0; the 3,344 other lines byte-identical to V3.0.23 (asserted; outside_rows_sha256 `309c3b83`). DIFF vs V3.0.23: SAME
3,344, CHANGED_TEXT_ONLY 366, CHANGED 0, ADDED 0. DIFF vs released V2.9: NOT_IN_RELEASED 2,120, QUANTITY_DIFFERS 899,
SAME_QUANTITY 691 = V3.0.23's, unchanged. Totals moved by code: none (asserted). Inside each changed line only
calculation.formula, its own calculation.inputs record and notes change (and gross on the NA line): asserted per line.
Default guard over the 3,710 lines: CONVENTION_WHERE_PRINTED 87, PARTIAL_FOOTPRINT 2, PRINTED_VALUES_DISAGREE 75,
SEARCH_INCOMPLETE 1,039 = V3.0.23's, none on a changed line. Parapet family 4 blank lines, floor 8.050943 m3 and the
wall-tile family (18 lines, 340.3038 m2) unchanged.

## 5. Acceptance (row T-338)

- (a) T-334 check on V3.0.24: **3,710 OK, 0 REFUSED, 0 FLAG** (was 351 REFUSED + 15 FLAG on V3.0.23, reproduced
  3,344 / 351 / 15); 5 notes NOTE_OPEN_RFI_ON_VALUED (the Q-68 C soffits, by design) unchanged. The NA skirting line
  carries no gross.
- (b) every quantity byte-identical to V3.0.23: qty / unit / state on all 3,710 lines (DIFF CHANGED 0); only formula /
  notes text and the NA gross change.
- (c) T-330 deductions check: V3.0.23 and V3.0.24 identical (OK 74, EMPTY_DEDUCTIONS 20, EXPORT_TOTAL_BLANK 11,
  NOT_SUMMING 10, NOT_APPLICABLE 3,595; 41 FLAG, 0 REFUSED; findings list byte-equal). Never worse.
- (d) verdict records: none binds a changed line (section 3); none promoted.
- (e) L4: section 7.
- (f) this package.

Export: the guarded export (tools/t334_line_state_check.py export) now WRITES on V3.0.24 (exit 0; it refused V3.0.23,
exit 2, nothing written). tools/boq_export_v1.py with the V3.0.22 verdict + downgrade sets, V3.0.23 vs V3.0.24: BOQ.csv
3,710 rows each; exactly ONE row differs outside the candidate-version column: L-af6fb2d3 FIN.SKIRTING gross 7.600 ->
blank (engine_gross too) and its excluded reason gains the note; BOQ_TRADE_SUMMARY, BOQ_CONTRACT_TOTALS and
BOQ_AUDIT_UNSUPPORTED_BASIS byte-equal.

## 6. Missing / held / for the Lead (nothing fixed here that is a state question)

- for_lead: none: every line T-334 found is one of the three text kinds (no valued line under a hold text outside the
  released ledger records, no held line with a figure outside NOT_APPLICABLE).
- The 4 PROVISIONAL plaster / paint lines (GF-R75FBAE 56.0131, 1F-RB72F22 51.415 m2 per trade) still print a gross
  `less N opening(s)` without canonical deductions (T-330 EMPTY_DEDUCTIONS): the formula now ends on the net, the
  deduction list is T-246's (EXPORT DEDUCTIONS), not this package's.
- Latent (not on V3.0.24): the same `formula or 'held: ...'` fallback in arch_v302.py:272, arch_v305.py:210,
  arch_v307.py:324, arch_v308.py:306, arch_v309.py:290 (frozen versions, not edited); their released records on the
  candidate carry a formula. Any later version that adds released ledger lines must write the arithmetic (the T-334
  check refuses the export otherwise).
- Downstream: none in quantity. SCOREBOARD cells: not re-run (no quantity moved; the Checker owns the scoreboard).

## 7. Validation

- **Full CLI run** (research/agents_t338/v3024_run.py, one process, `tools/urban_boq_m9.py arch --method
  ARCH_TAKEOFF_V3.0.24`) on ff2dcc41 (the code and inputs of the hand-in): V3_0_23 json `19f654bd` reproduced on the
  way; every V3_0_24_* file byte-identical to v3024_direct.py (json `19394733`, csv `3bd1c5c6`, DIFF `6256baef`,
  ledger csv `41877846` / json `97068868`, RUN `923eb18f`); totals moved {}.
- **L4 full suite** (tests/ + agents/, one session) on ff2dcc41: 396 FAILED / ERROR in 43 files; the 43 files re-run
  on the base engine head 25c1f52c: 395 fail there (the known private-input / environment failures, the same 395
  T-319 reported). **NEW 1** = tests/codemap/test_codemap.py::test_repository_maps_are_current: the maps were stale
  while that session ran (new files, rebuilt by the tool in a3f9af29); passes on a3f9af29 and on the merge head.
  **NEW 0.**
- Merge head 5ed524fa (= a3f9af29 + working head 6bd0385c, T-344; map-only conflict rebuilt by the tool): tests/
  t338_line_state_v3024 (31), t319_parapet_rc_integration, t344_label_census_v2, t334_line_state_check,
  t330_deductions_check, m9_kb, codemap, structural_comparison_engine/test_rebar_product_firewall.py,
  t130_family_master, t061_room_label_guard: all pass; freeze 0 differing; codemap stale none.
- tests/t338_line_state_v3024 (villa VG-338 by hand, not Alsenan): normal (3 released rebar lines incl. the 4-decimal
  length case, NA gross, PROVISIONAL and BOUNDED formula ends, 4 clean lines byte-identical, shuffle, a for_lead line
  kept, the merged T-334 check as the judge: clean after, 6 findings before); adverse (product not the net, length in
  mm, 5-decimal length, no diameter, no count, a non-released valued line under hold text, a bounded line with a gross,
  unlisted finding, stale listing, wrong kind, twice, fixed and for_lead, declared totals, unit-mass method / source /
  length precision, a quantity / rfi / calculation change in integrate, a fixed line still stating two states, schema
  / project / source); master 1.19.0 (builder, copies 1.18.0, checks clean, dropping the entry is stale); inputs pins
  (366 fixes, edited findings file stops the build).

## 8. Lessons-register row (proposed)

| 2026-10-29 | 350 released rebar lines printed 'held: ' and 2 of them do not reproduce from their printed inputs to the net's rounding (0.000533 / 0.000800 kg) (T-338) | the ledgers round length_m to 4 decimals for print and compute kg from the unrounded length, so the printed product carries the length's rounding as well as the net's | a line's printed arithmetic is checked against its figure within the rounding of everything printed (net 0.0005 + count x kg/m x 0.5 x 10^-length_decimals, the precision named with its source), never within the net's rounding alone and never with an open tolerance; beyond it, the line is a state question, not a text fix (every villa) | tests/t338_line_state_v3024 (normal: 1.6338 m printed, 2.904 kg accepted at 0.000589; adverse: 2.903 refused, a 5-decimal length refused, a mm length refused, another unit-mass method refused) | PROPOSED |

Verdict proposal: not a who-is-right item (export integrity; no quantity against the freelancer changed).
