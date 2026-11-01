# T-406 Concrete reconciliation roll-up r3 (research only)

The T-385 r2 cause closure (candidate ARCH_TAKEOFF_V3.0.29 vs the freelancer's concrete workbook; merge 5f99bfc3)
restated component by component with the Checker-MERGED traces only, one current table per family. No quantity, line,
state or released cell is changed. Engine-side figures and residual splits in m3 only; the per-component table of the
unchanged components is in `.work/private/t406/ROLLUP_T406.csv` (freelancer-derived).

**r3 (narrow rework, Checker REWORK r2 text only):** SD-DOME domes A + B +0.561362 m3 is TRACED (class from the merged
T-398 board VERDICT, ENGINE_RIGHT on the Checker's own cap calculation; new rule R-T406-8), so SD-DOME = traced
+0.561362 / HELD -2.260 / unexplained 0; O-T406-1 ruled by the Checker (BM-1F SCOPE +0.7552 stays TRACED, label
ENGINE_RIGHT, class unchanged); V3.0.34 (T-399) moved no concrete line. Nothing else changes.

## Inputs and reproduction

- BEFORE: T-385 r2 rebuilt this run from committed data + the Drive workbook (Drive: Urban BOQ private data / Alsenan
  chalet project / the concrete + rebar workbook), never from memory: the V3.0.29 concrete lines = the committed
  `research/agents_t332/CANDIDATE_V3021_CONCRETE_LINES.json` (521 lines, asserted equal by id, element id, state and value
  to the V3.0.29 binding `research/agents_t387/BINDING_T387.csv`: 0 differences) + the 4 parapet RC lines of that binding
  (HELD blank), the V3.0.29 downgrades (`verdicts/V3.0.29/DOWNGRADES.json`), then `t385_extract.py` + `t385_alsenan.py`
  into `.work/private/t406/t385out`. Reproduced exactly: 525 lines, 3 downgrades, 47 components, residual -114.464428,
  named +0.252401, HELD -77.593000, unexplained -37.123829 (= the Checker's T-385 r2 headline).
- TRACES (read from the merged summaries, `t406_alsenan.traces()`; no figure typed except the Checker's 2.35 / 0.28 m
  split of the upper G.B length): T-391 c3fe8ec8, T-394 e27c5d78, T-395 8cf46e7d, T-398 fe6a238d, T-401 23f948bb,
  T-403 a72a7282. Each trace's source residual equals the T-385 r2 contribution of its component (asserted, 0.001 m3).
- BOARD VERDICTS (r3, R-T406-8): SD-DOMES-AB area term +0.561362 m3: package summary UNTRACED, merged T-398 verdict
  (Verifier 2026-10-31T17:00Z, Gate A PASS) ENGINE_RIGHT: R_o = (2.21^2 + 1.90^2) / 3.80 = 2.235289, outer cap
  18.1679 - inner cap (R_i 2.135289, rise 1.80) 15.6273 = 2.5406 m3 per dome; the other side's shell area is a
  hemisphere reading on the 1.90 rise, not a drawn area. The figure is T-398's own, unchanged.
- CONFIRMATIONS (merged, no figure moves): T-392 cc3c7f08 (pool lines carry no out-of-pool part of B7 / 8D; ring B7
  billed once; O-T385-1 closed), T-402 1b4c18fc (27 held beam lines: 8 BOUNDED, 18 HELD, 1 VALUE proposal BM-GF-059
  0.549284 m3 not in the candidate; the beam HELD parts stay HELD).
- CANDIDATE MOVES V3.0.29 -> V3.0.33 (T-397 Gate B PASS, 4492fd59, read from `summary_t397.json`; V3.0.29 .. V3.0.32
  identical for concrete): columns GF 4 lines 2.475 and 1F 11 lines 5.964 m3 withdrawn from valued into CONFLICT ranges
  (GF 2.070 .. 2.475, 1F 5.964 .. 7.644) = HELD -8.439; GF beams +0.003174 ENGINE_RIGHT (GAP / DOUBLE corrections);
  ground-slab held bound 3.929788 -> 0 .. 3.560540 and the HELD lift-pit wall line: held engine side only, no move.
- V3.0.33 -> V3.0.34 (T-399 Gate B PASS, abf3de76; read and asserted from `summary_t399.json`): 1 line changed
  (FIN.PAINT L-c3f7e68ce91a436802e2), 4689 identical, no concrete line: the current table holds on V3.0.34 unchanged.

## Method (t406_rules.py, R-T406-1 .. 8; every villa)

A trace restates a component's residual, never moves it: its parts (cause, m3, verdict) re-add to the T-385 r2
contribution within 0.001 m3. The class of a part follows from its verdict (TRACED: AGREE / ENGINE_RIGHT /
FREELANCER_RIGHT / RULE_DIFFERENCE / FREELANCER_ARITHMETIC / SCOPE; HELD; UNEXPLAINED: UNRESOLVED / UNTRACED). Refused: a
trace or move from a task not in the merged register, a part counted in a class its verdict does not give (UNRESOLVED or
HELD counted as traced), a HELD part of 0, a ratio cause, an unknown component. A held engine part withdrawn by a later
candidate is a HELD named item (the withheld engine quantity), printed in its own CANDIDATE MOVE column. R-T406-8 (r3): a part's class is read from the Checker VERDICT on the board
when the package summary differs; the re-class names the merged task, member, m3 and verdict reference, never moves
the figure and never classes a HELD part as traced (refused otherwise).

## Result per family (m3, engine - freelancer; residual = traced + HELD + unexplained)

| Family | Before (T-385 r2): traced / HELD / unexplained | After traces (V3.0.29) | Current V3.0.33 (+ moves) | Cause closes |
|---|---|---|---|---|
| BLINDING | 0 / -47.055 / 0 | unchanged | unchanged | yes |
| FOOTING (less the boundary band) | +0.628 / -10.564 / 0 (band inside) | +0.628 / -1.960 / 0 | unchanged | yes |
| BOUNDARY BELOW N.G. (own row, T-403) | (in FOOTING / GROUND: HELD -16.164) | -3.984 / -11.984 / -0.196 | unchanged | no |
| GROUND (slab + ground beams, less boundary G.B) | 0 / -7.560 / -22.664 (G.B inside) | -4.844 / -13.251 / -4.569 | unchanged | no |
| COLUMN (+ necks, lift) | 0 / -12.186 / +0.650 | +4.501 / -15.899 / -0.138 | +4.501 / -24.338 / -0.138 | no |
| BEAM | +0.128 / 0 / +0.224 | +8.095 / -7.376 / -0.367 | +8.099 / -7.376 / -0.367 | no |
| SLAB | +0.463 / 0 / 0 | unchanged | unchanged | yes |
| STAIR / DOME | 0 / 0 / -11.383 | +0.233 / -5.788 / -5.828 | unchanged | no |
| POOL | -0.966 / -0.228 / -3.951 | -0.966 / -3.708 / -0.471 | unchanged | no |
| PARAPET RC (no freelancer row) | 0 / 0 / 0 (4 held lines) | unchanged | unchanged | yes |
| **Total** | **+0.252 / -77.593 / -37.124 = -114.464** | **+4.125 / -107.021 / -11.568 = -114.464** | **+4.128 / -115.460 / -11.568 = -122.900** (V3.0.33 = V3.0.34 for concrete) | 4 / 10 |

Bookkeeping closure (every component bound once, parts re-add) holds in all 10 rows; cause closure in 4. The traces
moved 25.556 m3 out of unexplained (net): +3.873 to traced and -29.428 to HELD. HELD grew because a held engine part that T-385
r2 had inside an UNRESOLVED lump is now named (held runs, held cell, held members, pump room, stair pieces). Held is
never agreement and never 0; the current HELD -115.460 includes the 8.439 m3 the V3.0.33 column ranges withdrew.

## Component changes (each cited to its merged verdict)

| Component | T-385 r2 | After (traced / HELD / unexplained) | Source |
|---|---|---|---|
| GS-SLAB | UNRESOLVED -12.309316 | -7.188210 strips under his plate ENGINE_RIGHT / -3.560540 held cell panels / -1.560570 (stair panel -0.837230 + faces -0.084700 UNRESOLVED, his area beyond the network -0.638640) | T-391 |
| GB-MAIN | UNRESOLVED -10.354614 | +2.343707 section (D 0.95 / 0.40 / 0.30 printed) ENGINE_RIGHT + plan +0.000013 AGREE / -9.690354 held runs / -3.007980 length basis untraced | T-391 |
| CL-GF | UNRESOLVED +0.530 | +2.5925 (count -0.5625, base +0.1925, global +0.11875 ENGINE_RIGHT; joint + head +2.69375 RULE_DIFFERENCE; split open +0.150) / -2.0625 / 0 | T-394 |
| CL-1F | UNRESOLVED +2.520 | +2.658 (count +0.918, global +0.180, joint + head +1.080, split open +0.480) / 0 / -0.138 C9 section | T-394 |
| CL-LIFT | UNRESOLVED -2.400 | -0.750 columns in his ring ENGINE_RIGHT / -1.650 net ring at his depth / 0 | T-401 (= T-394) |
| BM-GF | UNRESOLVED -3.553798 | +2.003362 (through support -2.903179 RULE_DIFFERENCE, run count +0.210119, engine-only marks +4.696422) / -5.430918 / -0.126242 | T-395 |
| BM-1F | UNRESOLVED +5.535302 | +6.496819 (through support -1.593362, run count +1.908946, engine-only marks +5.426035, SCOPE dome ring +0.7552) / -0.808 / -0.153516 | T-395 |
| BM-2F | UNRESOLVED -1.757500 | -0.532760 through support / -1.137500 / -0.087240 | T-395 |
| SD-DOME | UNRESOLVED -1.698638 | +0.561362 domes A + B area term ENGINE_RIGHT (board verdict, R-T406-8) / -2.260 DOME-3 / 0 | T-398 (verdict) |
| SD-STAIR | UNRESOLVED -9.683919 | -0.328145 (thickness basis, ownership, D1 steps) / -3.528 (MS1-L + winders, turns, ST-03 E1) / -5.827775 (ST-02 -3.974175, ST-01 flight length -2.016, landing area +0.1624) | T-398 |
| PL-PUMP | UNRESOLVED -3.480 | 0 / -3.480 pump room drawn on no sheet / 0 | T-398 |
| GB-BOUNDARY (moved) | HELD -7.560 | -3.984 (width -2.6442, depth -1.7628, length 2.35 m +0.423 ENGINE_RIGHT) / -3.5256 engine gross held / -0.0504 (length 0.28 m) | T-403 |
| BW-BAND (moved) | HELD -8.604 | 0 / -8.4588 owner method A (engine range 5.6392 .. 11.0328, DG-6dd9f1caba1ca77d) / -0.1452 (length 1.21 m) | T-403 |

The other 34 components (15 AGREE, 9 ENGINE_RIGHT, 9 HELD, BM-ARITH +0.128 FREELANCER_ARITHMETIC as ENGINE_RIGHT)
carry their T-385 r2 split unchanged; PL-WALLS keeps its untraced -0.471346 (wall height above the drawn rim + base).

## What remains unexplained (-11.568 m3) and why

| Part | m3 | Why it is not traced |
|---|---|---|
| ST-02 round stair | -3.974 | his developed length 16.4 m vs at most 9.06 m drawn (Checker): the curved geometry is not traced to one cause |
| GB-MAIN length basis | -3.008 | his two lump lengths cannot be split run by run (envelope 193.758 .. 231.908 m) |
| ST-01 flight length | -2.016 | his 5.3 m vs the drawn 3.30 m run |
| GS stair-zone panel | -0.837 | F2: whether a slab runs under the curved flight foot is drawn nowhere (designer item, RFI draft) |
| GS his area beyond the network | -0.639 | a bare number with no drawn element |
| PL-WALLS wall height | -0.471 | 0.20 m of his height above rim + base traced to no drawn level |
| beams length untraced | -0.367 | beyond the drawn support allowance (GF -0.126, 1F -0.154, 2F -0.087) |
| landing area | +0.162 | ST-01 landings, area term untraced |
| boundary lengths | -0.196 | upper G.B 0.28 m, lower band 1.21 m not traced to a drawn run |
| C9 section | -0.138 | schedule vs drawn section, designer item |
| GS valued faces | -0.085 | three small reads (member overlap, court-side, lift-side panels) |

## Observations and proposals (for the Checker; no figure changed by them)

- **O-T406-1 RULED (Checker r2)**: no row of the other side carries a dome ring (beam rows are straight marks; the dome
  is one shell row): BM-1F SCOPE +0.7552 stays TRACED, label ENGINE_RIGHT (engine-only count of the drawn ring, T-395
  verdict); class unchanged.
- **P-1 APPLIED (r3)**: domes A + B +0.561362 m3 TRACED by the T-398 board verdict (R-T406-8): traced +3.564 -> +4.125,
  unexplained -11.007 -> -11.568 m3 (a positive term leaves; the negative unexplained parts are unchanged, never offset
  by its sign).
- **V3.0.33 column restatement**: the 8.439 m3 the CONFLICT ranges withdrew is printed as HELD in its own move column;
  how T-394's traced column terms split between the 15 CONFLICT members and the rest is not re-bound here (it needs
  T-394's private per-mark table with its own outline read); the move changes no traced or unexplained figure.

## Engineering statement (engine vs freelancer)

On V3.0.29 the concrete residual is -114.464 m3 (engine valued 285.027 vs freelancer 399.491, -28.65 %); after the
merged traces it is +4.125 m3 traced (engine right or a rule difference, each with its drawn figure), -107.021 m3 HELD
(named items the engine withholds: blinding, necks, held members / runs / cells, pump room, boundary below N.G.,
stair pieces) and -11.568 m3 unexplained (named above). On the current candidate V3.0.33 (= V3.0.34 for concrete) the
residual is -122.900 m3 because 8.439 m3 of conflicted columns moved into held ranges. No figure here is a verified BOQ quantity or a release.

## Proposed lessons-register row (ERS section 7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-31 | After six merged trace packages the board still carried T-385 r2's -37.124 m3 'unexplained', and the packages' own figures were never put back into one family table (T-406) | each trace closed its own component; no step restated the closure, and a later candidate (V3.0.33) moved the engine side without a statement of its effect on the residual | a roll-up restates components only from merged traces whose parts re-add to the earlier contribution (a trace never moves residual); a later candidate's change of the engine side is a separate CANDIDATE MOVE with its class (withdrawn valued = HELD); the table is printed on the earlier and the current candidate side by side (scope: every reconciliation; provenance T-406) | tests/t406_concrete_rollup (unmerged trace / move refused, UNRESOLVED or HELD counted as traced refused, held as 0 refused, residual-moving trace refused, ratio refused) | PROPOSED |
| 2026-11-01 | The r2 roll-up carried domes A + B +0.561 m3 as unexplained although the merged T-398 verdict ruled it ENGINE_RIGHT (Checker r2 REWORK) | the roll-up read each part's class from the package summary only, which still printed the term UNTRACED | (Checker addendum) a part's class is read from the Checker VERDICT on the board, not from the package's own summary, when the two differ; the re-class names the merged task, member, m3 and verdict reference and never moves the figure (scope: every reconciliation roll-up; provenance T-406 r3, R-T406-8) | tests/t406_concrete_rollup (hand dome fixture; unmerged task / other member / no reference / moved m3 / unknown verdict / HELD part re-classed: refused) | PROPOSED |
