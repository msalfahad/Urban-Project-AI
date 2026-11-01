# T-421 integration package: stair-room floor parts (T-418) and lift-entrance marble (T-413) into ARCH_TAKEOFF_V3.0.38

Worker 3 (lane I), 2026-11-01, branch `agents/task-T-421`. **Integration package for Checker Gate B.** Integrates:
T-418 (MERGED 361f6e47), T-413 (MERGED ae87deb1); the beds by the T-420 method (MERGED 4c01fe06, R-T420-1) with the
T-414 owner ranges (MERGED 4f81eda1). Candidate of record before: ARCH_TAKEOFF_V3.0.37 (json `733f2efb`). NOT
RELEASED; the released default V2.9 + route G is unchanged; rollback = V3.0.37 / V2.9. Development villa (Alsenan), not
an accuracy claim; the method (R-T421-1) is for every villa. Drawings are cited by Drive folder and title only.

## 0. Run identity

Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip (`ab54dd55`), 'ST7757 dxf.dxf' (`9f9d1179`),
decoded by the wrapper into `.work/private`. Own fresh `research/agents_t167/v304_run.py`, then
`research/agents_t421/v3038_run.py` (Python 3.11.18): **V3_0_36 `d462203f` and V3_0_37 `733f2efb` reproduced** (the
T-246 / T-420 Gate B figures), **V3_0_38_BOQ_LINES.json `57cca61c`** written beside them (4,829 lines;
`summary_t421.json`, built by `t421_summary.py` from that run). Inputs:
`research/agents_t421/t421_inputs.py` reads ONLY the merged tables, each pinned by sha256 (SPACE_TABLE_T418.csv,
T-418 summary.json, STATION_TABLE_T413.csv, T-413 summary.json, ROOM_TABLE_T414.csv, floor_bed_v1.py).

## 1. The physical elements (ERS s.2.1) and who owns them

| Element | Owner trade (register) | Line(s) in V3.0.38 |
|---|---|---|
| Floor at the foot of MS1-L / top of D1, GF stair room, +1.00 | FLOOR FINISHES B3-01 (ROOM WITH NO FLOOR-FINISH LINE) | NEW FIN.FLOOR.FINISH_HELD 4.805 m2: area DRAWING-CONFIRMED, material HELD by name (porcelain if a floor, marble if a landing: UP-STAIR-005; no printed landing depth, no finish schedule) |
| Back-door lobby under the +3.50 half landing, +0.30 | B3-01 | NEW FIN.FLOOR.FINISH_HELD 1.3225 m2, as above |
| 0.200 strip north of the divider end | unread (T-418) | NEW FIN.FLOOR.FINISH_HELD BOUNDED_EXPOSURE 0 .. 0.2300 (never 0; no bed; stays inside the landing bound: it may be landing or under the winders) |
| 2F lobby beyond the stair width, +9.70 | B3-01, porcelain by owner Q-70 A | NEW FIN.FLOOR.PORCELAIN gross 2.500, net 2.200 m2 (lift threshold floor part out, s.2) |
| Landings of the two walled stair rooms | STAIRS (B7) | FIN.MARBLE.LANDING bounds 0 .. 9.050 -> **0 .. 2.9225** (GF) and 0 .. 11.725 -> **0 .. 9.225** (2F), in the same step (Checker condition on T-418) |
| Lift threshold at each landing door (GF / 1F / 2F) | B6 (LIFT LANDING THRESHOLD) | NEW FIN.MARBLE.LIFT_THRESHOLD 0.500 m2 + 1.000 m.l each (width drawn, depth ASSUMED — OWNER-APPROVED UP-ELEV-005) |
| Lift door surround (left / top / right) | B6 | NEW FIN.MARBLE.LIFT_SURROUND HELD 1.000 .. 5.000, 1.000 .. 4.700, 0.750 .. 4.280 m2 (door height printed nowhere; 2F right band 0 .. 0.400) |
| Wall band 1.000 x 0.200 in the shaft wall | inside the B6-07 footprint | ARCH.THRESHOLD LIFT_LANDING x 3: 0.200 m2 HELD -> **listed, no quantity** (NOT_APPLICABLE_WITH_EVIDENCE, owned by the threshold line) |
| Threshold's floor part on the landing floor | B6-07 | GF L-7625f35c 109.778417 -> 109.478417, 1F L-b06400d4 33.711036 -> 33.411036, 2F lobby 2.500 -> 2.200: the CERTAIN part 1.000 x (0.500 - 0.200) = 0.300 m2 each deducted (named deduction, id = the threshold line), the position-dependent rest 0 .. 0.200 each HELD beside |
| Cement-sand bed under each floor line | FINISHES B3-05 (R-T420-1) | NEW bed pairs on the three new valued floor lines; the GF / 1F landing beds RESTATED to the new nets |

## 2. Why the threshold deduction is 0.300 certain + 0 .. 0.200 held (ERS s.3, reconciliation in units)

B6-07 footprint = drawn clear width 1.000 x owner depth 0.500 = 0.500 m2. Its position across the 0.200 m shaft wall
band is not drawn: flush with the shaft face it covers the band 0.200 + floor 0.300; starting at the landing face it
covers floor 0.500 (and the band then holds the supplier's landing sill, not marble). In every position at least
0.300 m2 of floor lies under the threshold, so 0.300 leaves the porcelain net (never a double count); 0 .. 0.200 more
depends on the undrawn position and stays HELD by name (deduction 0.300 .. 0.500, T-413 s.3 floor overlap 0.900 ..
1.500 m2 for 3 stations). No number is picked: the net carries only the deduction every position shares.
Check (`check_lift`, asserted on the integrated lines): B6-07 m2 = width x depth; band line NOT_APPLICABLE owned by
the threshold; the floor line deducts its certain part exactly once; band part + certain floor part = footprint:
**overlap 0.000 m2** on all 3 stations.

## 3. Methods side by side (ERS s.2.2)

| Item | Owner manual method | Drawing-derived (merged ledgers) | Line |
|---|---|---|---|
| Stair-room floors | floor-finish area of every floored space by room; landing = marble (UP-STAIR-005) | face partitioned (R-T418-1): 12.475 = 4.805 + 1.3225 + 3.080 + 1.3225 + 1.035 + 0.680 + 0.230; 18.600 = 2.500 + 4.875 + 0.4025 + 10.8225 | area DRAWING-CONFIRMED; GF material HELD, 2F porcelain ASSUMED — OWNER-APPROVED (Q-70 A) |
| Lift threshold | drawn width x 0.50 depth + front edge (UP-ELEV-005) | width 1.000 between the drawn jambs; depth and position not printed | 0.500 m2 PROVISIONAL (ASSUMED — OWNER-APPROVED depth), 1.000 m.l SOURCE_DERIVED (drawn) |
| Lift surround | union of 0.50 bands, needs the door height | h printed nowhere; 2F right face only 0.400 to the internal corner | HELD bound, never 0 |
| Beds | floor m2 x Q-45 dry 0.03 .. 0.04 m | b of the storey's own zone (GF 0.050, 2F 0.050; the +0.30 lobby has no printed structural top: no bound) | m2 = finish net; m3 owner range ASSUMED — OWNER-APPROVED, drawn layer HELD beside |

## 4. Per-line before / after (V3.0.37 -> V3.0.38), evidence status, sources

Every row below is in `V3_0_38_INTEGRATION_LEDGER.csv` and `summary_t421.json` (line ids, v2_9 / v3_0_37 / v3_0_38
quantities, evidence status, still-held items, merged source and commit).

| Line | Code | Element | V3.0.37 | V3.0.38 | Evidence status | Source |
|---|---|---|---|---|---|---|
| L-c32effca | FIN.MARBLE.LIFT_THRESHOLD m2 | LIFT:ELV-01-GF | - | 0.500 | ASSUMED — OWNER-APPROVED | T-413 ae87deb1 |
| L-f2b76041 | FIN.MARBLE.LIFT_THRESHOLD lm | LIFT:ELV-01-GF:edge | - | 1.000 | DRAWING-CONFIRMED | T-413 |
| L-b66b8e76 | FIN.MARBLE.LIFT_SURROUND m2 | LIFT:ELV-01-GF:surround | - | HELD 1.000 .. 5.000 | HELD | T-413 |
| L-9840d1da / L-64dd750f / L-d788f643 | as above | ELV-01-1F | - | 0.500 / 1.000 / HELD 1.000 .. 4.700 | as above | T-413 |
| L-eba7ac43 / L-e29e5748 / L-fdbd9636 | as above | ELV-01-2F | - | 0.500 / 1.000 / HELD 0.750 .. 4.280 | as above | T-413 |
| L-6f5806ad / L-084df97d / L-3c5a3be2 | ARCH.THRESHOLD m2 | GF OP-011 / 1F OP-007 / 2F OP-002 band | HELD 0.200 .. 0.200 each | listed, no quantity | NOT_APPLICABLE (owned by B6-07) | register LIFT LANDING THRESHOLD |
| L-7625f35c | FIN.FLOOR.PORCELAIN | GF-RC99C2A:floor | 109.778417 | 109.478417 (+ 0 .. 0.200 HELD deduction) | area ASSUMED — OWNER-APPROVED (unchanged), deduction ASSUMED — OWNER-APPROVED | T-413 |
| L-b06400d4 | FIN.FLOOR.PORCELAIN | 1F-R78C367:floor | 33.711036 | 33.411036 (+ 0 .. 0.200 HELD) | as above | T-413 |
| L-f53d4986 | FIN.FLOOR.FINISH_HELD | GF-R31F8AE:GF-ST-HALL | - | 4.805 | area DRAWING-CONFIRMED, material HELD | T-418 361f6e47 |
| L-b4441a1b | FIN.FLOOR.FINISH_HELD | GF-R31F8AE:GF-ST-LOBBY030 | - | 1.3225 | as above | T-418 |
| L-a788de46 | FIN.FLOOR.FINISH_HELD | GF-R31F8AE:GF-ST-CN | - | HELD 0 .. 0.230 | HELD | T-418 |
| L-9bd25c0c | FIN.FLOOR.PORCELAIN | 2F-R4D1B62:2F-ST-LOBBY | - | 2.200 (gross 2.500 - 0.300; + 0 .. 0.200 HELD) | area DRAWING-CONFIRMED, finish ASSUMED — OWNER-APPROVED (Q-70 A) | T-418 + T-413 |
| L-1983e89d | FIN.MARBLE.LANDING | GF-R31F8AE:landings | HELD 0 .. 9.050 | HELD 0 .. 2.9225 | HELD | T-418 |
| L-5d2be30d | FIN.MARBLE.LANDING | 2F-R4D1B62:landings | HELD 0 .. 11.725001 | HELD 0 .. 9.225001 | HELD | T-418 |
| L-3e451bfc / L-bff6fe38 | FIN.FLOOR.BED.DRY m2 / m3 | GF-ST-HALL:bed | - | 4.805 / 0.14415 .. 0.1922 (bound 0 .. 0.24025) | DC / ASSUMED — OWNER-APPROVED | R-T420-1 |
| L-faa974d2 / L-b87fd07d | bed | GF-ST-LOBBY030:bed | - | 1.3225 / 0.039675 .. 0.0529 (no bound) | as above | R-T420-1 |
| L-35520a1a / L-6ad86fb8 | bed | 2F-ST-LOBBY:bed | - | 2.200 / 0.066 .. 0.088 (bound 0 .. 0.110) | as above | R-T420-1 |
| L-20a8e714 / L-77a18286 | bed (restated) | GF-RC99C2A:floor:bed | 109.778417 / 3.293353 .. 4.391137 | 109.478417 / 3.284353 .. 4.379137 (bound 5.473921) | as before | R-T420-1 |
| L-ebce765b / L-eaa8f305 | bed (restated) | 1F-R78C367:floor:bed | 33.711036 / 1.011331 .. 1.348441 | 33.411036 / 1.002331 .. 1.336441 (bound 1.703963) | as before | R-T420-1 |

Totals moved (only in the codes this package owns; `totals_moved_by_code`, own run):

| Code / unit | V3.0.37 | V3.0.38 | Move |
|---|---|---|---|
| FIN.FLOOR.PORCELAIN m2 (valued) | 297.775973 (20 lines) | 299.375973 (21) | +1.600 (+2.200 2F lobby, -0.300 GF, -0.300 1F) |
| FIN.FLOOR.FINISH_HELD m2 | - | 6.1275 valued + HELD 0 .. 0.230 | new (material HELD) |
| FIN.MARBLE.LIFT_THRESHOLD | - | 1.500 m2 / 3.000 m.l (3 + 3 lines) | new |
| FIN.MARBLE.LIFT_SURROUND m2 | - | HELD 2.750 .. 13.980 (3 lines) | new, HELD |
| ARCH.THRESHOLD m2 (held) | 1.910 .. 1.910 (9 bounded) | 1.310 .. 1.310 (6 bounded) | -0.600 held: the 3 bands now listed inside B6-07 |
| FIN.MARBLE.LANDING m2 (held high) | 0 .. 20.775001 | 0 .. 12.147501 | -8.6275 (the floor parts left the bounds; valued 10.1019 unchanged) |
| FIN.FLOOR.BED.DRY m2 | 288.145972 (19) | 295.873472 (22) | +7.7275 |
| FIN.FLOOR.BED.DRY m3 (owner range) | 8.644379 .. 11.525839 | 8.876204 .. 11.834939 | +0.231825 .. +0.309100 |

## 5. Diffs and regression

- vs V3.0.37: **4,810 -> 4,829 lines; 19 ADDED, 11 CHANGED (all named above: 3 bands, 2 landing floors, 2 landing
  bounds, 4 restated bed lines), 4,799 byte-identical**
  (asserted in `integrate()` and `write()`; outside-rows sha256 in the summary). Totals moved only in this package's
  codes (asserted).
- vs released V2.9 + route G: the 19 added lines are NOT_IN_RELEASED; the changed lines: the GF / 1F porcelain and the
  bands differ from V2.9 as they already did in V3.0.37 (diff counts in the summary).
- Older chain guards: the V3.0.14 floor-scope records on the three band lines (TO_THRESHOLD: 'area kept') and on the 1F
  porcelain line (SETTLE_RANGE: 'settled figure') would refuse the ruling the register made after them. They are NOT
  deleted or edited: each is kept whole under its key, wrapped `{"superseded_by": "ARCH_TAKEOFF_V3.0.38", "rule",
  "why", "record"}`, and `check_lift()` carries their invariants forward (the band area = the threshold's band part
  1.000 x 0.200; the settled figure = the net before the deduction; the net = that figure - 0.300). Every other V3.0.14
  / V3.0.24 / V3.0.29 / V3.0.36 guard runs unchanged on the V3.0.38 lines and passes (V3.0.24 line-state: the changed
  formulas conclude on their own figure).
- T-330 deductions check (`tools/t330_deductions_check.py`, unchanged): V3.0.37 4,810 lines 6 FLAG (5 EMPTY, 1
  NOT_SUMMING) / 0 REFUSED -> V3.0.38 4,829 lines the same 6 FLAG ids / 0 REFUSED: no new finding (the deducted floor
  lines and the 2F lobby close gross - deductions = net).
- Export (`tools/boq_export_v1.py`, unchanged) on V3.0.38: 4,829 rows; B6-07 MEASURED UNVERIFIED; B6-06 and the GF
  strip HELD with their bounds; the three bands EXCLUDED (listed, no quantity); nothing shown as 0.
- Tests: `tests/t421_stair_lift_integration` (hand villa K421, not Alsenan: 22 + 6 registry tests); L3 folders (s.7 of
  the handoff); L4 full suite on the final commit compared id by id with the working branch.

## 6. Missing / held (never 0)

- GF stair-hall material (porcelain vs marble landing): designer / finish-schedule item (Lead's list); area valued.
- GF strip 0 .. 0.230 m2 (unread lines).
- Lift door clear height (supplier, RFI L-1): surround HELD 2.750 .. 13.980 m2; 2F right band 0 .. 0.400 (architect).
- Threshold position across the band: 0 .. 0.600 m2 more porcelain deduction (3 x 0 .. 0.200), HELD.
- Drawn bed thickness HELD (D-40); the +0.30 lobby has no printed structural top (no drawing bound).
- Lift threshold bed (under the marble piece) and the threshold thickness / edge detail: not in any owner rule; no line.

## 7. Engine vs freelancer (quantities only; T-418 s.4, T-413 s.5 census, workbooks not re-opened: the finishes
workbook is above the Drive connector limit)

| Family | Engine V3.0.37 | Engine V3.0.38 | Freelancer | Difference | Verdict proposal |
|---|---|---|---|---|---|
| Dry floor finish area (porcelain + finish-held) | 288.1458 m2 | 295.8733 m2 (+6.1275 held-material, +1.600 porcelain) | 337.57 m2 | -41.6967 m2 (-12.35 %), was -49.4242 (-14.64 %) | components as T-418 s.4; the 0.900 m2 now B6-07 marble is a RULE_DIFFERENCE (UP-ELEV-005: threshold ≠ porcelain) |
| B6-07 lift threshold | no line | 1.500 m2 / 3.000 m.l | no row | engine-only | ENGINE_RIGHT on scope (UP-ELEV-005) |
| B6-06 lift surround | no line | HELD 2.750 .. 13.980 m2 | no row | engine-only | ENGINE_RIGHT on scope; quantity HELD |
| GF stair hall | no line | 6.1275 m2 material HELD | landing row 6.20 m2 (no breakdown) | not matched by figure | UNRESOLVED (T-418) |
| B3-05 bed | 288.1460 m2 dry | 295.8735 m2 dry | no row | engine-only | ENGINE_RIGHT on scope (T-420) |

## 8. Rule and lessons row (proposed, ERS s.7)

R-T421-1 (module docstring, every villa): one physical floor area, one quantity: (a) a stair-room floor part leaves
its landing bound in the same version; (b) a lift threshold is ONE B6-07 element, the band listed without a quantity,
the landing floor net of the certain part with the position-dependent rest HELD; (c) a bed pair always equals its
finish net (restated when the net moves); (d) an unsettled material is a HELD finish on a valued area; held never 0.

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | wiring the lift threshold would have left its band in ARCH.THRESHOLD and its floor part in porcelain (up to 0.500 m2 counted twice per door), and moving a finish net would have left its bed on the old net | pieces verified one by one each measured the same footprint from its own trade; a finish net and its bed were not tied at change time | R-T421-1 (any villa) | tests/t421_stair_lift_integration (normal: K421 hand figures, 0 overlap, landing bound reduced, only named lines change, mirror order, threshold on a new floor part, superseded scope records carried; adverse: stair face dropped whole, held part in a bound, bound exceeded, held as 0, unsettled finish as porcelain, depth without source, mm, band left with a quantity, floor not deducted, bed not restated, stale band, applied twice, two floor lines for a station, settled figure ≠ net, band area ≠ band part) | proposed |

## 9. Gate B hand-check list (always by hand: new scope, new methods, every moved line)

1. B6-07 per station: jamb lines 226 / 227, B96 / B97, 12AE / 12AF at 1.000 apart (P7757.dxf); 1.000 x 0.500 = 0.500.
2. Wall band 0.200 ('200' dim 672 on GF): certain floor part 1.000 x (0.500 - 0.200) = 0.300 per station.
3. GF L-7625f35c 126.927696 - 8.194412 - 8.954867 - 0.300 = 109.478417; 1F L-b06400d4 33.711036 - 0.300 = 33.411036.
4. GF stair room parts 4.805 = 2.50 x 0.45 + 1.15 x 0.70 + 1.15 x 2.50; 1.3225 = 1.15 x 1.15; 9.050 - 6.1275 = 2.9225.
5. 2F lobby (450 - 250) x 125 = 2.500; 11.725001 - 2.500 = 9.225001; net 2.200.
6. Beds: 4.805 x 0.03 / 0.04 / 0.05; 1.3225 x 0.03 / 0.04; 2.2 x 0.03 / 0.04 / 0.05; 109.478417 x 0.03 / 0.04 / 0.05;
   33.411036 x 0.03 / 0.04 / 0.051.
7. Surround bounds A(h) per station (T-413 s.3).
