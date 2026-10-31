# T-386 Benchmark-provenance correction (Checker O-T384-C1 / -C2) and sweep for benchmark figures framed as residuals or proof

Worker 2, 2026-10-31. Lane A, gate 0, research / tests text only. No engine file, rule version, candidate line, family
master or quantity changes. Statement-of-evidence fix under ERS s.2.4 (a benchmark figure is evidence to reconcile,
never proof and never an engine residual). Figures from the hits below are NOT repeated here: each is cited by file:line.

## 1. The physical element and the source (ERS s.2.1, s.2.2)

Element: B12-01 showers (pcs) on Alsenan, 6 drawn shower positions (3 tray + 3 screened walk-in), DRAWING-CONFIRMED by
merged T-369 / T-370. The compared count is a tiling-LABOUR row of undefined unit; it is not a physical element.

Source, re-established from the registers (the provenance step T-380 skipped):

| Check | Evidence | Result |
|---|---|---|
| What is 'Alsenan Chalet_by_category.xlsx'? | T-225 sources register S4 ("OWNER COST RECORD, neither the freelancer BOQ nor a takeoff"); BENCHMARK_SOURCE_MANIFEST.json key WEB, kind WEB_APP_COMMERCIAL_REPORT, title "Cost By Category" | Urban Projects' own cost record (xlsx form of the web-app report), not a freelancer file |
| Do the T-380 / T-370 rows come from it? | tests/alsenan/registers_b1/WEB_APP_ROWS.json: shower = WEB-018; floor gratings = WEB-019; the six sanitary rows = WEB-055 .. WEB-060 in the same order and quantities as T-380 s.5 | yes, row for row |
| Did the freelancer measure them? | same register: all eight rows mapping_class NO_FREELANCER_ITEM or LUMP_SUM, source_freelancer_items = [], freelancer_qty = null | no freelancer item |
| Any shower / sanitary / tank row in his six workbooks? | FREELANCER_RAW_ROWS.json, 885 rows, searched for the Arabic labels of sanitary, tank, pump, shower, gratings, plumber, drainage, heater: one hit only, the pool sheet's pump-ROOM WALLS (concrete); T-369 (research/agents_t369/T-369_SHOWER_FLOOR_TANKING.md:96) read his finishes workbook: no shower, tray or tanking row | none |

Conclusion: the 11 is a figure of Urban's own cost record. "Shower 11 vs 6" is NOT an engine-vs-freelancer residual:
the freelancer has no shower row. It is a count of undefined basis compared with a drawn count: **UNRESOLVED scope**,
no verdict of ENGINE_RIGHT / FREELANCER_RIGHT possible, nothing rests on it (B12-01 showers 6 DRAWING-CONFIRMED; B8-04
shower floor extra 0.000 m2, Q-40 A).

## 2. Corrections made (acceptance a, b)

| File:line (new) | Before | After |
|---|---|---|
| research/agents_t380/T-380_DRAINAGE_SOURCE_CENSUS.md:1 | title "... the freelancer's shower residual" | "... the cost-record shower count (UNRESOLVED scope)" |
| same, s.5 (lines 86-133) | "Freelancer comparison and the shower residual"; table "Freelancer row / Freelancer"; "his rate is private workbook content" | "Benchmark comparison ..."; provenance paragraph with register ids; "Cost-record row (register id) / Cost record"; "Cost-record shower count 11 vs 6 drawn: UNRESOLVED scope, not a residual"; no rate mentioned at all; the freelancer's own wet-room table (a genuine freelancer source) kept and labelled as his |
| same, s.6 line 140 | pool drainage "(the pool is a freelancer lump sum)" (unsourced) | cost record pool = one subcontract lump sum (WEB-072); his pool sheet is concrete only (rows read) |
| research/agents_t380/t380_alsenan.py:13-17 | `FREELANCER = ... by_category.xlsx (a cost record) and ...` | COST RECORD and FREELANCER sources named separately |
| same :135-156 | `FREELANCER_SANITARY`, `FREELANCER_SHOWER = 11  # ... his rate ...` | `COST_RECORD_SANITARY`, `COST_RECORD_SHOWER = 11`, `COST_RECORD_SHOWER_SOURCE` (WEB-018, URBAN_COST_RECORD, NO_FREELANCER_ITEM, UNRESOLVED_SCOPE); `FREELANCER_SHOWER` kept ONLY as an alias so the merged tests/t380 runs unchanged (marked NOT his figure) |
| research/agents_t380/summary.json `freelancer` block | freelancer: shower / pit covers / tanks | `benchmark`: provenance_correction, `freelancer.rows = 0`, `urban_cost_record` with register ids; shower comparison UNRESOLVED_SCOPE |
| tests/t384_currency_guard/test_t384_currency_guard.py:34, 46, 65 (O-T384-C2) | adverse strings paired the T-380 quantity with the removed rate | synthetic quantities and rates (7 qty, an invented rate); normal line synthetic (`DRAWN_SHOWERS = 6`) |
| same :90-106 | rate-gone check by fixed line numbers (100 / 143) | located by content (one marker line each, no currency figure in either file) + new test that no adverse string pairs the T-380 quantity with a figure |

Quantities: none changed. FREELANCER_SHOWER / COST_RECORD_SHOWER value unchanged; every T-380 count unchanged.

## 3. Sweep (acceptance c): research/ and tests/, every villa

Method: (1) the new scanner `research/agents_t386/provenance_guard.py` (a line naming the freelancer beside the cost-record
workbook, or beside the label of a cost-record row the register maps to NO_FREELANCER_ITEM, without a negation);
(2) targeted reads of every line naming the freelancer together with: `residual` (30 lines), agreement / confirmation /
proof wording (25 + 2 lines), `by_category` / web-app / cost record (41 lines), and every `assert` against a freelancer
value in tests/ (59 lines). Classes:

- **PROVENANCE_MISLABEL**: an Urban cost-record figure attributed to the freelancer (the T-380 error).
- **AGREEMENT_AS_PROOF**: a benchmark figure used as the expected value of an engine / drawn quantity, or agreement
  stated as support for a quantity that has no independent basis on that line.
- **RESIDUAL_FRAMING**: a figure of undefined basis presented as an engine residual.
- **COMPLIANT**: a reconciliation that decomposes the benchmark into named causes (ERS s.2.4), or a corroboration
  stated AFTER an independent basis (drawing / schedule / owner rule / hand calculation), or a pinned benchmark cell.

### 3.1 Findings

| File:line | Class | Fix / why none |
|---|---|---|
| research/agents_t380/T-380_DRAINAGE_SOURCE_CENSUS.md:1, 86-117 (old) | PROVENANCE_MISLABEL + RESIDUAL_FRAMING | fixed here (s.2) |
| research/agents_t380/t380_alsenan.py:13, 132-143 (old); summary.json:129-147 (old) | PROVENANCE_MISLABEL | fixed here (s.2) |
| research/agents_t370/T-370_SANITARY_FIXTURE_REGISTER.md:81-91 | PROVENANCE_MISLABEL (section "Freelancer comparison": the by_category file called "the only freelancer file with sanitary content"; gratings row WEB-019 and shower row WEB-018 under "Freelancer row") + the shower row framed as a -45 % difference | NOT in T-386's files: follow-up row proposed (relabel to the Urban cost record; shower = UNRESOLVED scope; gratings = reconciliation of a cost-record count, not a freelancer RULE_DIFFERENCE). Listed in PROVENANCE_BASELINE_T386.json so the guard fails on any NEW case meanwhile |
| research/agents_t370/t370_alsenan.py:155-161 | PROVENANCE_MISLABEL (dict `FREELANCER` holds cost-record rows) | same follow-up row; baseline-listed |
| tests/t370_sanitary_fixture_count/test_t370_fixture_count.py:174-177 | PROVENANCE_MISLABEL in name / comment; the assert pairs a cost-record count with the sum of two drawn counts | no quantity rests on it: both drawn counts are pinned independently at :168, so it is a reconciliation pin, not proof; rename in the same follow-up row |
| research/agents_t150/T-150_DOORS_WINDOWS_BOQ.md:154 | AGREEMENT_AS_PROOF (window and aluminium-door counts "already agree" with the freelancer) | superseded: merged T-198 settles the windows by drawing with W02 HELD (range shown beside the freelancer, tests/t198_census_r3:56). Historical text; no quantity rests on it; no edit (outside files) |
| research/agents_t065/T-065_FOUNDATION_MEMBERS.md:123 | AGREEMENT_AS_PROOF (strap beams: "register and freelancer agree" as the reason the register is preferred) | superseded: T-073 (research/agents_t073/T-073_RESULT.md:85) re-derived the strap from the drawn F10 + F outline by hand; the line now rests on that. No edit |
| board text (not research / tests; Lead / Checker-owned): BOARD.md rows T-370 (line 515), T-380 (line 525), Lead note line 62, this row's own acceptance (a) (line 531); RUN_LOG.md lines written by the T-370 / T-380 runs | PROVENANCE_MISLABEL ("freelancer shower 11 vs 6") | for the Lead: restate as "cost-record shower count vs 6 drawn, UNRESOLVED scope" at the next touch; RUN_LOG is append-only and stays as history |
| research/agents_t384/CURRENCY_BASELINE_T384.json:18, T-384_CURRENCY_SWEEP.md:11 | names the variable `FREELANCER_SHOWER` (no figure) | historical record of T-384; the variable is now an alias; no edit (outside files) |

### 3.2 Reviewed and COMPLIANT (no change)

| File:line | Why compliant |
|---|---|
| research/agents_t225/T-225_BLOCKWORK_SOURCES_REGISTER.md:22, SOURCES.csv:5, build_t225.py:362 | the cost record correctly classed OWNER COST RECORD, "neither the freelancer BOQ nor a takeoff" (the model for the fix) |
| research/agents_t384/CURRENCY_BASELINE_T384.json:132, 225; T-384_CURRENCY_SWEEP.md:39, 49 | cost record correctly called Urban Projects' own |
| research/external_engine_lab/* (B1 package / registers / recommendations) | separates freelancer manual QS from the web-app report; "a web-app quantity is never a second confirmation of a freelancer quantity" |
| research/agents_t241/T-241_BEAM_LINE_CLOSURE.md:100, research/agents_t252/T-252_BEAM_LEDGER_R2.md:107 | explicitly "a coincidence, not agreement" with the compensating causes named |
| research/agents_t218/T-218_FLOOR_RESIDUALS.md:54-56; research/agents_t223/T-223_FLOOR_TYPING.md:107; research/agents_t233, t234, t242, t258 closures; research/agents_t205/neck_ends_v1.py:234; research/agents_t321/t321_alsenan.py:337 | freelancer total decomposed into named physical / rule causes, verdict on the printed sizes, residual named (ERS s.2.4 order) |
| research/agents_t042 :117, :220; research/agents_t097/README.md:75; research/agents_t073:85; research/agents_t106:84; research/agents_t080:97-98; research/agents_t099:36; research/agents_t147:120; research/alsenan_ground_system_rebar_s5/post_freeze/S5_POST_FREEZE_COMPARISON.md:23 | the basis is stated first (printed schedule, owner rule, hand calculation, drawn faces); the freelancer is a corroboration after it, not the reason |
| research/agents_t182/T-182_FIVE_MEASURES.md:23; research/agents_t177/T-177_SCOREBOARD_V2_SCRIPT.md:24 | explicitly refuse freelancer agreement as verification |
| research/agents_t166/T-166_STAIR_POOL_TANK_STEEL.md:52; research/agents_t369 (s. "No shower, tray or tanking row") | state that the freelancer has NO row |
| tests asserting freelancer values (59 lines, e.g. t205, t209, t241, t260, t312, t329, t184, t198, t207, t238) | pin his own cell values or the decomposition of his figure into named causes; none uses a freelancer value as the expected value of an engine / drawn quantity (t260:46 and t184:223 assert residual 0 of the DECOMPOSITION, not engine = freelancer) |

Counts: 3 files PROVENANCE_MISLABEL fixed (T-380 x3), 3 files PROVENANCE_MISLABEL outside the files (T-370 report,
script, test: one follow-up row), 2 superseded AGREEMENT_AS_PROOF lines (no quantity rests on them), board text for the
Lead; RESIDUAL_FRAMING found only in T-380 (fixed). No quantity in the candidate or the released run rests on any hit.

## 4. Rule, test and lessons row (ERS s.4, s.7)

Rule proposal R-T386-1 (research and tests text, any villa; provenance T-380 / T-384 / T-386): *every compared figure
names its source class from the benchmark manifest (FREELANCER_MANUAL_QS / URBAN_COST_RECORD / drawing / owner rule)
and, where a register exists, its register id; a cost-record row whose register entry has no freelancer source cell is
never "the freelancer's"; a figure whose basis or unit is not defined is compared as UNRESOLVED scope, never as an engine
residual; agreement with any benchmark is never proof.*

Test: tests/t386_provenance_guard (normal: a negated statement, a genuine freelancer row, a quantity line; adverse:
freelancer beside the cost-record file name or beside a NO_FREELANCER_ITEM row label, a new unclassified file refused,
a cost-record row offered as a freelancer figure refused, an unknown source kind refused; repository: no unlisted hit,
baseline not stale, the three tokens anchored to register rows, T-380 corrected).

Lessons row proposal: "2026-10-31 | a cost-record labour count was reported for two days as 'the freelancer's shower
residual' | the source was named from the file's folder, not from the register (WEB_APP_ROWS maps it NO_FREELANCER_ITEM)
| name a benchmark figure's source class and register id before comparing; a figure of undefined basis is UNRESOLVED
scope, never a residual; agreement is never proof (scope every villa; provenance T-386) | tests/t386_provenance_guard |
PROPOSED".
