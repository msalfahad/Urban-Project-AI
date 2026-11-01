# T-246 Integration package: canonical deduction lists into ARCH_TAKEOFF_V3.0.36 (Gate B)

Worker 3 (lane I), 2026-11-01. Integration package for Checker Gate B. Candidate ARCH_TAKEOFF_V3.0.36 built on the
candidate of record V3.0.35 (json `b011bace`, reproduced byte for byte in this run); NOT RELEASED; the released default
stays ARCH_TAKEOFF_V2.9 + route G (rollback: run V2.9). Drawings named by Drive folder and title only; no coordinate,
image, client name or note text in any committed file. **No quantity, evidence state, range or code total moves**: this
is a traceability fill (ERS 2026-10-22 s.2.4: reconcile in units to named causes, never a plug).

## 0. Inputs and reproduction

Drive folder "Alsenan chalet project": 'ST7757 dxf.dxf' (sha256 `9f9d1179`), P7757_DXF_COMPRESSED.zip -> P7757.dxf
(`ab54dd55`), private copies in `.work/private` only. Python 3.11.18.

```
python3 -I research/agents_t167/v304_run.py <P7757.dxf> <ST7757 dxf.dxf> --out <private>/t167
python3 -I research/agents_t246/v3036_run.py <P7757.dxf> <ST7757 dxf.dxf> --out <private>/t246 --t167 <private>/t167
python3 -I tools/t330_deductions_check.py check --lines <private>/t246/v3036/V3_0_36_BOQ_LINES.json
```

V3_0_35_BOQ_LINES.json of this run = the candidate of record `b011bace` (cmp identical to an own V3.0.35 run);
V3_0_36_BOQ_LINES.json **`d462203f`** (the CLI run and an in-process run of the same module agree byte for byte).

`t246_inputs.py` builds URBAN_V3036_INPUTS_V1 ONLY from Checker-merged files pinned by sha256 (an edited file stops):

| Task | Merge | Checker verdict | File read |
|---|---|---|---|
| T-341 | 5fbf8677 | Verifier 2026-10-29 15:46 UTC Gate A PASS (fill 41 FLAG -> 1 FLAG on copies) | research/agents_t341/FILL_TABLE_T341.csv, FILL_LINES_T341.csv |
| T-345 | f2225238 | Verifier 2026-10-29 19:02 UTC Gate A PASS (5.890817 m2 traced, residual 0) | research/agents_t345/TRACE_ROWS_T345.csv, TRACE_LINES_T345.csv |
| T-296 | 57c31ae4 | Verifier 2026-10-25 16:08 UTC Gate A PASS (own re-measure 1F-01 15.900 lm, W14 sill AGREE) | research/agents_t296/WINDOW_CAUSES_T296.csv |

The ledgers were read on V3.0.22; the module binds every line as the ledger read it (item, element, valued state, gross
field, net to 1e-6): 39 of 41 still stand in V3.0.35. The 2 that V3.0.32 (T-284 ceiling fill) restated since are set
aside by name in the inputs, never forced (s.4 below).

## 1. What changed (R-T246-1), per family

| Family (unit) | Lines | Gross (after) | Net (unchanged) | Listed (ded - add) | Rows | Source |
|---|---|---|---|---|---|---|
| FIN.PLASTER (m2) | 4 | 259.510050 | 217.208100 | 42.3019 | 12 openings by id | owner-method lists (T-341) |
| FIN.PAINT (m2) | 4 | 259.510050 | 217.208100 | 42.3019 | 12 (same openings) | T-341 |
| FIN.WALL.TILE (m2) | 12 | 374.273550 | 340.303800 | 33.9700 | 25 openings by id + face | T-341 |
| FIN.SKIRTING (lm) | 10 | 254.959095 | 180.116658 | 74.842439 | 64 (doors by opening id, window halves, tiled-face bases, 1 addition) | T-341 (T-296 ledger) + T-296 readings |
| FIN.FLOOR.PORCELAIN (m2) | 2 | **202.910698** (was 143.489453) | 143.489453 | 59.421245 | 24 | T-341 (GF) + T-345 (1F) |
| ARCH.WALL_RUN (lm) | 7 | 337.848728 | 216.931061 | 120.917667 | 7 (one aggregate per line, by element) | T-341 |
| **39 lines** | | | | | **144** | |

Only two gross fields change, both restated to the face the list starts from (RECONCILED_GROSS_RESTATED / TRACED):
GF porcelain L-7625f35c 109.778417 -> **126.927696** (face = the same engine face's ceiling gross; - treads 8.194412 -
pantry wet part 8.954867 = 109.778417 = net); 1F porcelain L-b06400d4 33.711036 -> **75.983002** (T-345: - void 16.005 -
own flights F2 / F3 / F5 8.690682 - flights below F1 / F4 / F6 6.714185 - VOID_RESIDUE 2.034669 - STAIR_FOOTPRINT
3.559930 - D-13 tread 0.345 - landing split out 4.9225 = 33.711036 = net). The stale base tread list (8.336981 /
6.771668) is replaced, not appended (the arch_v30 stair_changes defect is corrected in V3.0.36's list, never in frozen
arch_v30.py).

Skirting: the 8 lines short by their floor-level window-threshold half now list it by opening id (**13.068825 lm**; it
was 13.569 lm on V3.0.20, the pantry's 0.500 left with its line, NOT_APPLICABLE since V3.0.21). The band passage OP-003
wider than its stretch on the GF open-plan boundary is an ADDITION +1.400 lm, never a negative deduction.

T-330 check (tools/t330_deductions_check.py, unchanged): V3.0.35 **45 FLAG / 0 REFUSED / 74 OK** -> V3.0.36 **6 FLAG / 0
REFUSED / 113 OK**. The 6 left are the V3.0.32 ceiling lines (s.4). Every listed item now has an id and a `qty` the
export reads (deductions_total no longer blank on the 39 lines).

## 2. Physical check of the listed window deductions (flag only; T-246: "flag it UNRESOLVED, do not apply")

| T-296 reading | Windows | Rows | lm (both halves) | What it means | In V3.0.36 |
|---|---|---|---|---|---|
| SKIRTED (sill above the floor, DRAWING-CONFIRMED / PRINTED) | W04, W14, W24, W29 | 8 | **5.802094** | the wall base continues under the sill: the deduction is physically questioned | listed, `physical_check UNRESOLVED`, net unchanged |
| HELD (sill / owner not established) | W02, W11, W12, W13, W17, W25 | 12 | 15.730916 | unknown | listed, `UNRESOLVED` |
| NOT_SKIRTED (floor glazing / wet room) | W09, W15, W16 | 6 | 4.604640 | deduction right | listed, `CONSISTENT` |

The SKIRTED 5.802 lm is the T-296 "+5.802 lm thresholds released" acceptance: a QUANTITY change, not done here
(WAITING T246_SKIRTING_RELEASE). T-296's "W15 / W16 out of range (-3.105 lm of range)" also moves the held range lines:
not done here.

## 3. Owner manual method and drawing-derived method side by side

| | Owner manual method | Drawing-derived method (engine) |
|---|---|---|
| Plaster / paint / wall tile | face area less each opening by id: doors at the Q-55 C head 2.20 (ASSUMED - OWNER-APPROVED), windows by printed sill / head (T-144 / T-201) | engine face; the owner's own list is what the line now carries |
| Skirting | room perimeter less door widths by opening; the window base only where no wall continues under the sill (UP-SKIRT-001) | engine runs; band openings by engine id (T-249 census id beside); F-17 equal split of the window edge into glazing / threshold halves |
| Porcelain | room face less treads (marble, UP-STAIR-005), void, landing (Q-66 B), wet part (Q-37 A) | engine face; STAIR_FLOOR_RESIDUE_V1 exact cells (T-345) |
| Wall run | run less openings, ends and columns | engine aggregate per thickness (one row by element) |

Evidence status of every listed figure: the net is unchanged (its status unchanged); the list is DRAWING-CONFIRMED by
the merged T-341 / T-345 verdicts; window rows carry their T-296 status; ASSUMED - OWNER-APPROVED door heads keep their
basis text. Nothing is VERIFIED by this package; Gate B decides.

## 4. Missing, held and not in this package

1. **6 FIN.CEILING lines (V3.0.32, T-284)** still FLAG: 5 EMPTY_DEDUCTIONS (1F-R3CFCFD 0.341845, 1F-R48AA46 1.241,
   1F-R48CDA5 0.4472, 1F-R8BDA49 1.4227, 1F-RB72F22 11.5808 m2) and GF open plan NOT_SUMMING 9.785604 m2. Their gap is
   explained only through still_held items (dome positions, stair zones) whose numbers are rounded to 4 dp and, on the GF
   line, do not close (stair zone 9.8536 + 1.7719 vs 9.7856): a list there needs the T-284 ledger rows by id: proposed
   follow-up row (not guessed here).
2. T-296 quantity part (+5.802 lm released, W15 / W16 range, pantry NOT_APPLICABLE already in V3.0.21, 1F dressing
   MISSING line, rename of skirting_opening_rules.py), T-388 F1 / F3 and T-327 O-1 / O-2 (scope added to this row
   2026-10-25 .. 10-31): **not in this package**. They move quantities, states or line fields and are each checkable on
   their own; proposed split (WORKFLOW_CONTROLS s.3 OVERSIZED) into: (a) skirting threshold release + range restatement
   (T-296), (b) T-388 face-piece deductions + pantry paint N/A, (c) T-327 threshold material_state + measure_pair.
3. ARCH.WALL_RUN lists carry one aggregate per line (by element, as T-341 recorded): not split by opening.

## 5. Line-by-line diff and regression

- vs V3.0.35: 4,691 lines SAME (byte-identical; outside-rows sha256 `5c4368f7..`), 39 CHANGED_TEXT_ONLY (list, gross field,
  calculation record, notes), 0 CHANGED, 0 ADDED. `A304.code_totals` identical (totals_moved_by_code {}).
- vs released V2.9 + route G: SAME_QUANTITY 635, QUANTITY_DIFFERS 955, NOT_IN_RELEASED 3,140 (as V3.0.35: no quantity of
  this package moves).
- Files (private run): V3_0_36_BOQ_LINES.json / .csv, V3_0_36_INTEGRATION_LEDGER.json / .csv (per line: v2_9, v3_0_35,
  v3_0_36, gross before / after, list size before / after, sums, residual, unresolved item ids, verification),
  V3_0_36_DIFF.csv, V3_0_36_RUN.json.
- Tests: tests/t246_deduction_listing (22: hand villa V246 normal; adverse unlisted deduction, threshold twice, negative
  row, stale binding, restated gross below the field, held line, mm-as-m slip, applied twice, unknown source, moved
  quantity, mirrored order; inputs pinned / closing; family master 1.31.0). L3: m9_s6, m9_p2a, m9_s2_arch, m9_s4, m9_s5,
  m9_foundation, m9_kb, t131, t400, t330, t345, t341, t296, t246, t061, t130, t203: exit 0. Freeze 0 differing; codemap
  check stale none.
- Registry: rules/coverage/BOQ_FAMILY_MASTER_1.31.0.json = 1.30.0 + pending V3.0.36 (no family / code / state change);
  the 1.30.0 test reads a newer registry (the T-400 pattern).

## 6. Gate B hand-check list (WORKFLOW_CONTROLS s.1)

Lines moved >= 5 %: none (no quantity moves). New calculation method: the listing (R-T246-1). Unit / dimensional: none
new (units are the line's own). Cross-trade: skirting rows on the GF-07 tiled faces (3.500 lm, Q-37 A wall tile owns the
base) and the porcelain wet part (8.954867 m2 to the wet floor line). Suggested hand spot-checks (re-measure from the
ledger, not from this list): skirting L-c021ae79 17.700 - (OP-004 0.800 + OP-020 1.000 + W14 1.224887 x 2) = 13.450226;
plaster L-af9621f4 59.295 - (2.200 + 1.760 + 3.920) = 51.415; porcelain L-7625f35c and L-b06400d4 as s.1; skirting
L-71e2e002 56.006096 - 32.734507 + 1.400 = 24.671589; wall tile L-ca4e74c5 27.83125 - 2.240 = 25.59125 vs net 25.5912
(owner list at 4 dp, +0.00005 m2, inside 0.0005).

## 7. Lesson (proposed for ERS s.7)

| 2026-11-01 | a fill table read on one candidate (V3.0.22) met 2 lines restated by a later package (V3.0.32 ceilings) | ledgers bind to line content that later packages move | a listing binds item, element, state, gross and net to 1e-6 and stops on a stale line; set-asides are named in the inputs, never forced | tests/t246_deduction_listing test_stale_binding_stops / test_inputs_build_and_close | V3.0.36 |
