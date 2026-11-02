# T-350 integration package: EARTHWORKS B1-02 / B1-03 / B1-04 (T-347, T-356, T-357) into ARCH_TAKEOFF_V3.0.43

Worker 3 (lane I, stream S), 2026-11-02, branch `agents/task-T-350`. **Integration package for Checker Gate B.**
Integrates T-347 (MERGED 509f90c2, Gate A PASS, own re-measure of the 24 pits / D-14 / pool envelope), T-356 (MERGED
15fc9ad4, Gate A PASS, strap range LEDGER_RIGHT, SB1 re-measured), T-357 (MERGED 90135e91, Gate A PASS, existing-ground
datum and coefficients) over T-320 / T-170. Candidate of record before: ARCH_TAKEOFF_V3.0.42 (`1793266d`, T-442).
**NOT RELEASED**; released default V2.9 + route G unchanged; rollback = V3.0.42 / V2.9. Development villa (Alsenan),
not an accuracy claim; the method (R-T350-1) is for every villa. Drawings cited by Drive folder and title only.

integrates: T-347, T-356, T-357, T-320, T-170

## 0. Run identity

Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip (`ab54dd55`) and 'ST7757 dxf.dxf' (`9f9d1179`),
decoded by the wrapper into `.work/private`. Own fresh `research/agents_t167/v304_run.py`, then
`research/agents_t350/v3043_run.py` (Python 3.11.18): **V3_0_42_BOQ_LINES.json `1793266d` reproduced** (= the T-442
Gate B candidate, 4,839 lines); **V3_0_43_BOQ_LINES.json `6f534d5e`** (4,857 lines; `summary_t350.json` by
`t350_summary.py`). The full hub run on 54770249 reproduced the direct module calls byte for byte (then `aec251a3`); the
only later change renames the three codes to STR.EARTH.* (the code-literal census scans the STR prefix; L4 finding), so
the lines were rebuilt by the same module calls on the same V3.0.42 file (`6f534d5e`); the hub wiring is unchanged. Inputs: `t350_inputs.py` reads ONLY the merged FILL / coefficient files, pinned by sha256.

```
.work/venv/bin/python -I research/agents_t167/v304_run.py <P7757.dxf> <ST7757.dxf> --out <private>/t167
.work/venv/bin/python -I research/agents_t350/v3043_run.py <P7757.dxf> <ST7757.dxf> --out <private>/t350 --t167 <private>/t167
.work/venv/bin/python -I research/agents_t350/t350_summary.py <private>/t350/v3043 --write
```

## 1. The physical elements (ERS s.2.1) and who owns them

- **Excavation** (B1-02, EARTHWORKS): the soil removed from the existing ground (EG) down to the formation of each pit /
  trench / pool envelope, plus working space. The drawings print the neat plans (DXF outlines), the minimum depth
  'not less than 1.50 m below the existing plot level' (ST p.9 note 1; Q-21 C: a minimum, not the founding level) and
  the pool formation -1.50. They print NO founding level, NO working space, no pits-vs-bulk decision (OQ-13 / RFI S1).
- **Backfill** (B1-03): excavation - the buried structure below EG (blinding, membrane + screed, footings net of the
  F9/FN and F8/FN overlaps, necks, ground beams): R-BACKFILL-DISP-1. Zone Z2 (fill above EG under the GF slab, 'from
  excavation material', p.13) is a separate zone, never merged into Z1.
- **Disposal** (B1-04): excavation - backfill re-used - Z2 re-use; bulking only by an answered rule (none: R-T347-5).
- **Buried structure**: displacement only; each component stays its concrete / blinding / WP line's (ELEMENT_REGISTER
  'Buried structure' row). The earthworks lines NAME those lines (bound_lines), never re-measure them.
- **Site clearance** (B1-01): NOT IN DRAWN SCOPE (T-357: 31 sheets searched): no line.

## 2. Owner manual method and drawing-derived method side by side

| | Owner manual method | Drawing-derived method (merged ledgers) |
|---|---|---|
| excavation | plan (neat + working space) x depth EG -> formation | neat plans net of real overlaps 129.234375 m2 (Checker), less D-14 beyond plot 1.890 and F8 in pool 1.99957 = 125.344805 m2 x printed minimum 1.50 = AT_LEAST bound; formation and working space HELD |
| backfill | excavation - structure below EG | excavation HELD -> HELD; displacement known 65.842438 m3 + necks >= 4.3278 (T-320) |
| disposal | excavation - re-used fill (x bulking by rule) | HELD (no bulking rule, Z2 not formed, excavation held) |
| range fixes | held line shows the range the printed sources allow | T-356 own strip (B + 0.20) x axis clear; T-230 / T-233 SB3 ledger |

## 3. Per line, V2.9 / V3.0.42 / V3.0.43 (V3_0_43_INTEGRATION_LEDGER.csv, 20 rows)

Every earthworks line is NOT_IN_RELEASED in V2.9, absent in V3.0.42, **BLOCKED_RFI blank** in V3.0.43 (evidence status
HELD, WORKFLOW_CONTROLS s.5); the bound is in `calculation.inputs.earthworks_v3043`, never in measured_net / range.

| Line | Element (EW-T350:...) | Bound beside (m3) | Held by (summary) | Bound lines |
|---|---|---|---|---|
| L-f38080bf | B1-02:Z1-PITS-24 | AT_LEAST 188.017207 (+129.234375 per m of d) | formation, working space, pits vs bulk, D-14 | 57 |
| L-a3275da1 | B1-02:Z1-PIT-FF | none (raft 20.700 m2 DC, no depth) | pit floor per lift supplier, RFI S23 | 8 |
| L-acaf8ffb | B1-02:Z1-PIT-F10F | none | Q-31 C open outline | 6 |
| L-a4243f6c | B1-02:Z1-POOL | AT_LEAST 17.776576 (EG coef +11.851051 per m) | blinding projection, working space, F-T320-05 | 2 |
| L-c529e154 | B1-02:Z1-TRENCH-EXT-GB-MAIN | none (neat cut = blinding 2.79956) | working space, trench / pit overlap | 17 |
| L-cb3dd2f7 | B1-02:Z1-TRENCH-INT-GB-MAIN-ZERO | ZERO_BY_BOUND while b_wet <= 0.30 | the condition (T-214 / T-221) | 14 |
| L-4c9634d0 | B1-02:Z1-TRENCH-INT-GB-MAIN-D33 | none | D-33 | 13 |
| L-d0345e4c | B1-02:Z1-TRENCH-ANNEX | none | D-34 / D-33 / D-35 | 13 |
| L-6419dac7 | B1-02:Z1-TRENCH-COURT | none | no court section | 3 |
| L-a8034fdf | B1-02:Z1-TRENCH-STRAPS | none (footprint 7.889 m2) | D-15 | 6 |
| L-497ba5ca | B1-02:Z1-TRENCH-BOUNDARY | none | depth not printed, Q-28 A provisional | 2 |
| L-d4eca831 | B1-02:Z1-LOWER-GB-ROW | none | exists only if d > 0.22 m | 0 |
| L-b8f080cb | B1-03:Z1-PITS-24 | none (+124.374375 per m of d) | excavation held; C8 neck; SB3 | 57 |
| L-5ee4aa12 | B1-03:Z1-POOL | none | all displacement inside the envelope | 2 |
| L-9ddebbb4 | B1-03:Z1-TRENCH-EXT-GB-MAIN | none | working space only | 17 |
| L-afedffeb | B1-03:Z1-OTHER-TRENCHES | none | as their excavation rows | 0 |
| L-f339fd40 | B1-03:Z2 | none | Z2 extent, wet-floor b, D-33 / D-34 | 0 |
| L-4a858846 | B1-04:ALL | none | no bulking rule; Z2 re-use; excavation held | 0 |
| L-35382b18 | STR.CONC.BLINDING strap | held range 0.377803 .. 0.771877 -> **0 .. 0.912684** | D-15 | - |
| L-c823e0db | STR.CONC.STRAP SB3 in F3 | held range 0.0295 .. 0.1181 -> **0.0295 .. 0.2683** | D-15 strap soffit | - |

Four lines sit in two B1-02 zones (L-98eb2d58 pits + FF; L-7a5214a3 / L-0e30aadb / L-fe78ae28 in two trench classes):
named in both lists, their components split once in the merged T-347 binding (256 components), listed in the run
identity `lines_in_two_zones`.

## 4. Evidence status, verification, statuses (WFC s.5)

- Bounds: pits / pool AT_LEAST = DRAWING-CONFIRMED plan x PRINTED minimum (Checker re-measure T-347); never VERIFIED as
  quantities. Existing ground: DERIVED +-0.00 (external datum; interior UNKNOWN, T-357).
- Strap blinding range: T-356 LEDGER_RIGHT, SB1 re-measured by the Checker (1 / 3 straps: PARTIALLY VERIFIED).
- SB3-in-F3 range: F-T347-1 ACCEPTED in the T-347 verdict, not re-measured: HELD range, ASSUMED nothing.
- Nothing released, nothing VERIFIED by this package.

## 5. Not wired, by name (WAITING in the module)

- T-356 (iii) neck-end ranges on L-0e852cca / L-0bb78acc: since V3.0.40 both lines are VALUED and named by the pending
  downgrade proposal DGP-T430-GB-D34-SHORT; the corrected ends (0.207 low; 0.295391 high) belong in that Checker
  record's audit range (lengths not re-measured), not in a line. **Checker: amend the record's audit range if issued.**
- DGP-T356-BAND / DGP-T356-GB-D34: already Checker downgrade-only records (T374 V2 / DOWNGRADES snapshot); read, no
  line m3 edited (acceptance ii).
- RFI re-review S01 (ESTIMATED founding level) and S05 (SB3): owner condition 'the Checker verifies each basis before
  any line uses it' (T-180 open): not applied; S01 scenario beside: pits at d = 0 = the bound, +-0.10 m = +-12.923 m3.
- N-T347-1: the pits bound is 0.1018 m3 conservative (strip subtracted twice); stays as merged.

## 6. Diff and downstream

- vs V3.0.42: 18 ADDED, 2 CHANGED, 4,837 SAME (byte-identical, asserted; outside-rows sha in RUN.json).
- vs released V2.9: the 18 earthworks lines NOT_IN_RELEASED; released V2.9 untouched.
- Totals moved: STR.EARTH.EXCAVATION 12 / STR.EARTH.BACKFILL 5 / STR.EARTH.DISPOSAL 1 lines, all blocked, 0 released, 0 held range;
  STR.CONC.BLINDING held 5.879177 .. 10.784391 -> 5.501374 .. 10.925198 m3 (released 15.179437 unchanged);
  STR.CONC.STRAP held 0.0295 .. 0.5031 -> 0.0295 .. 0.6533 m3 (released 3.3905 unchanged). Asserted: no other code.
- Downstream: coverage B1-02 / 03 / 04 now own STR.EARTH.* (B1-03 / B1-04 capability -> IMPLEMENTED_NOT_INTEGRATED) (BOQ_FAMILY_MASTER_1.38.0, pending); the trade scoreboard /
  export see a new trade EARTHWORKS with held lines only (no released figure); T-445 (footing blinding) unaffected.
- Engine vs freelancer: earthworks missing from BOTH; verdict UNRESOLVED (formation, working space: RFI S1 / OQ-13).

## 7. Regression

- `tests/t350_earthworks_integration` (27): villa E350 by hand (pits 4.00 + 2.88 - overlap 0.32 = 6.56 m2 x 1.20 =
  AT_LEAST 7.872 m3; strap 0.10 .. 0.20 -> 0 .. 0.30); adverse: held zone with a value, held as 0, mm3, ZERO without a
  condition, minimum read as the founding level, unknown family / bound / source, zone twice, line twice, stale bound
  line, stale / valued range line, low > high, EG assumed, applied twice, tampered valued earthworks line, project
  mismatch, formula ending on a figure; zone order mirrored; committed FILL builds 18 held zones; master 1.38.0.
- L3 on 7ac09daf: 1887 passed, 22 skipped, 2 xfailed, 0 failed. L4 full suite on 7ac09daf: 7 failed; 5 are the known
  T-465 import-rule failures (r8_0 / r8_1 / r8_2), failing identically on the base 08d47b84; 2 were this package's and are
  fixed: the census guard of master 1.30.0 (a new code prefix EARTH outside the scanned prefixes -> codes renamed
  STR.EARTH.*) and the T-459 candidate binding (its committed census of later arch_v30* modules rebuilt by its own tool
  `t459_census.py candidate --write`: one new key arch_v3043.py with no lap token; later_steps_touching stays []). After
  the fix: every test folder that scans code literals or masters (37 folders) 1375 passed, 0 failed.
- With the STR.EARTH codes the t130 guard (a NOT_IMPLEMENTED family has no module writing its code) asked B1-03 /
  B1-04 to move: 1.38.0 raises them NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED (as B1-02); final L3 set (36
  folders incl. t130 / t140 / t400 / t459 / t469 / m9_*) re-run on the final head: see the board handoff.

## 8. Rule and proposed lessons row (ERS s.7)

R-T350-1 (every villa): (a) earthworks = excavated - displacement (backfill), - re-used fill (disposal); held blank
while formation / working space / extent are unprinted; (b) a printed minimum depth is an AT_LEAST bound beside the
line, never its quantity; (c) bulking only by an answered rule; (d) each zone once, shared lines listed; (e) a range fix
moves only a held range; (f) held never 0.

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-02 | three BOQ categories (excavation, backfill, disposal) absent from the candidate although their bounds were verified | a category with no printed formation was left out instead of being listed held | a missing category enters the BOQ as held-blank lines per zone with its proved bound beside; absence is never silence (every villa, earthworks and any category held by a designer item) | tests/t350_earthworks_integration (normal E350; adverse 'printed minimum as founding level', 'held as 0') | PROPOSED |
