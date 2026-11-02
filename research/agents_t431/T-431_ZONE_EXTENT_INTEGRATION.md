# T-431 integration package: GF dining floor along the south facade (T-427 zone extent) into ARCH_TAKEOFF_V3.0.41

Worker 3 (lane I), 2026-11-02, branch `agents/task-T-431`. **Integration package for Checker Gate B.** Integrates T-427
(MERGED 65ce8f6d, Gate A PASS 2026-11-01 12:01 UTC with the Checker's own DXF re-measure of the 5.645 m2 piece) with the
cross-trade pieces its row names: the skirting base of the piece's own faces (T-440 MERGED 3c65489c: open-room net
24.671589 lm, the +3.90 lm outside the pantry box), the piece's ceiling face (T-283 r3 MERGED 6e141df6: GF-RFD4E1D 4.885
m2 plan area, bulkhead edges 6.5428 m) and the B3-05 bed method (T-414 / T-420). Candidate of record before:
ARCH_TAKEOFF_V3.0.40 (json `aa6aa927`, T-430 Gate B, merge 3fe8f974). **NOT RELEASED**; the released default V2.9 +
route G is unchanged; rollback = V3.0.40 / V2.9. Development villa (Alsenan), not an accuracy claim; the method
(R-T431-1) is for every villa. Drawings are cited by Drive folder and title only.

## 0. Run identity

Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip (`ab54dd55`) and 'ST7757 dxf.dxf' (`9f9d1179`),
decoded by the wrapper into `.work/private`. Own fresh `research/agents_t167/v304_run.py`, then
`research/agents_t431/v3041_run.py` (Python 3.11.18): **V3_0_36 `d462203f`, V3_0_37 `733f2efb`, V3_0_38 `57cca61c`,
V3_0_39 `8d1bbe5d` and V3_0_40 `aa6aa927` reproduced** (every Gate B figure up to T-430), **V3_0_41_BOQ_LINES.json
`5176c7c4`** written beside them (4,838 lines; `summary_t431.json`, built by `t431_summary.py` from that run).
Inputs: `research/agents_t431/t431_inputs.py` reads ONLY the merged files, each pinned by sha256 (T-427 summary.json
`a87b3b5a`, T-440 summary.json `df7982c3`, T-283 CEILING_LEDGER_R3_EXPORT.json `fc8873cf`, T-414 ROOM_TABLE `7bc3752c`
+ floor_bed_v1.py `5238ca1c`); typed there: the line ids the merged texts name (bound by the module: stale binding
stops), the piece id and the wording of the held reasons.

```
.work/venv/bin/python -I research/agents_t167/v304_run.py <P7757.dxf> <ST7757.dxf> --out <private>/t167
.work/venv/bin/python -I research/agents_t431/v3041_run.py <P7757.dxf> <ST7757.dxf> --out <private>/t431 --t167 <private>/t167
.work/venv/bin/python -I research/agents_t431/t431_summary.py <private>/t431/v3041 <private>/t167 --write
```

## 1. The physical element and who owns it (ERS s.2.1)

The garden band along the inside of the GF south facade is drawn between its own end lines 310 (west) and 30F (east),
7.020 m, with a curb 0.20 east of 310. West of 310, for 3.80 m to the pantry line B3, **no line is drawn** at the band
edge (T-427, Checker re-measure: every entity crossing the strip listed). The engine prolonged the band edge to B3 and
cut the dining floor there into a held band face (GF-RFD4E1D, 3.80 x 1.30 - column notch 1.10 x 0.05 = 4.885) and a
held strip (3.80 x 0.20 = 0.760). Physically this is **dining floor** (R-T427-1): one piece 5.645 m2, its own south wall
face (the facade wall 104) and the three exposed faces of column 2FCF, and the ceiling over it.

Own re-read this run (P7757.dxf, handles, room-local mm, lengths only): 104 facade face; B3 and 310 are 3,800 apart;
2FCF spans 1,100 along the facade, 275 from B3, 50 proud of the wall face; A8 / A9 / 4B4 (band edge 1,500 / 1,450 /
1,300) start at 310 and run east only. Hence 3.80 x 1.50 - 1.10 x 0.05 = **5.645 m2**; skirting along the piece: wall
3.80 - 1.10 = 2.70 + column 0.05 + 1.10 + 0.05 = 1.20 = **3.90 lm** (AGREE with T-427 / T-440).

Owner trades: floor B3-01 (FIN.FLOOR.PORCELAIN), bed B3-05, skirting B3-06 (the open room's one line), ceiling B5-01,
ceiling paint B4-06, bulkhead B5-04; the zone lines are B2-02 ARCH.SPACE. The band proper (9.101) and its curb (0.604)
stay with the designer (D-48), HELD.

## 2. What the package does, per line (ERS s.2.2: owner manual method and drawing-derived method side by side)

| | Owner manual method | Drawing-derived method (merged ledgers) |
|---|---|---|
| floor piece | floor area of every floored space by room; finish by the owner's dry default (URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1); the printed chain 1082 was read as the band length (T-153) | the zone ends at its own drawn end line; a piece joined to the room across an undrawn edge is room floor (R-T427-1); parts re-add |
| bed | Q-45 dry 0.03 .. 0.04 m x area (a range) | the GF dry zone b 0.05 (T-414) as the drawing bound beside |
| skirting | wall + column faces of the dry room at floor level | the piece's own faces from the V2.9 face runs (T-440 own route) |
| ceiling | decor = plan area under the slab; paint = decor + bulkhead | T-283 r3 face area in the open room's class; bulkhead depth not decided for this face |

`V3_0_41_INTEGRATION_LEDGER.csv` (10 rows):

| Line | Element | Action | V2.9 | V3.0.40 | V3.0.41 | Evidence status (WFC s.5) |
|---|---|---|---|---|---|---|
| L-b5f3c3c3298063cbf921 (ADDED) | GF-RFD4E1D:SOUTH-FACADE-DINING FIN.FLOOR.PORCELAIN | ADD_FLOOR | not in V2.9 | - | **5.645 m2** SOURCE_DERIVED | area DRAWING-CONFIRMED (T-427 Checker); finish ASSUMED — OWNER-APPROVED (as L-7625f35c) |
| L-6b6412e885390b434819 | GF-RFD4E1D:space ARCH.SPACE | RETIRE_ZONE | 4.885 PROVISIONAL | 4.885 | NOT_APPLICABLE (owned by L-b5f3c3c3) | - |
| L-554a525edce9a9235bee | band strip (OP-003) ARCH.SPACE | SHRINK_ZONE | not in V2.9 | HELD 1.364 | **HELD 0.604** (curb) | HELD (D-48) |
| L-69085dcb63727e343150 (ADDED) | ...:bed FIN.FLOOR.BED.DRY m2 | ADD_BED | - | - | **5.645** | DRAWING-CONFIRMED |
| L-93a91d33816d3f613fb2 (ADDED) | ...:bed FIN.FLOOR.BED.DRY m3 | ADD_BED | - | - | **0.16935 .. 0.2258** (range) | ASSUMED — OWNER-APPROVED (Q-45); drawing bound 0 .. 0.28225 beside, HELD |
| L-71e2e002a3af624097f0 | GF-RC99C2A:skirting FIN.SKIRTING | ADD_SKIRTING | 28.171589 | 24.671589 | **28.571589 lm** | rows GF-RFD4E1D:wall 2.70 + :column 1.20 DRAWING-CONFIRMED |
| L-ba5ea9bd4bbd2f713ea0 (ADDED) | GF-RFD4E1D:decor FIN.CEILING | ADD_CEILING | - | - | **4.885 m2** PROVISIONAL | area DRAWING-CONFIRMED (T-283 face = T-427 piece); class as the open room (Q-48 A) |
| L-2a50551d7aab2e65f3f6 (ADDED) | GF-RFD4E1D:paint FIN.PAINT.CEILING | ADD_PAINT | - | - | **4.885 m2** PROVISIONAL | ASSUMED — OWNER-APPROVED (Q-57 A mod (6)); the bulkhead part HELD by name |
| L-31f9b7008ea883f1b78d (ADDED) | GF-RFD4E1D:bulkhead FIN.CEILING.BULKHEAD | ADD_BULKHEAD_HELD | - | - | HELD blank | HELD (edge 6.5428 m beside; depth not decided) |
| L-4b41debf41fff9e3faae (ADDED) | GF-RFD4E1D:west-strip:ceiling FIN.CEILING | ADD_CEILING_HELD | - | - | HELD blank | HELD (0.760 m2 floor beside; no ceiling reading) |

Every other V3.0.40 line: **4,828 byte-identical** (asserted by the module; DIFF: ADDED 7, CHANGED 3, SAME 4,828).

## 3. Reconciliation in units (ERS s.2.4)

- Floor piece = band west face 4.885 (L-6b6412e8 gives it whole) + west strip 0.760 (L-554a525e gives it; keeps the curb
  0.604) = **5.645 m2**; the zone lines lose exactly 4.885 + 0.760 = 5.645 (check_pieces overlap 0.000000).
- FIN.FLOOR.PORCELAIN valued 299.375973 -> **305.020973 m2** (+5.645, 21 -> 22 lines); bed m2 295.873472 -> 301.518472
  (+5.645 = the new finish net); bed m3 range 8.876204 .. 11.834939 -> 9.045554 .. 12.060739 (+0.16935 .. +0.2258).
- ARCH.SPACE valued 68.560696 -> 63.675696 (-4.885, the retired line); held 7.488412 -> 6.728412 (-0.760).
- FIN.SKIRTING valued 180.116658 -> **184.016658 lm** (+3.900, on L-71e2e002 only): 24.671589 (T-440 net, base of the
  pantry box already off, over-count 0.000) + 2.70 + 1.20 = **28.571589** (the row's binding figure; gross 56.006096 -
  deductions 32.734507 + additions 1.400 (the earlier PASSAGE_RUN_RESIDUAL row) + 2.700 + 1.200 = 28.571589, checked by
  the V3.0.36 list rule).
- FIN.CEILING valued 406.452177 -> **411.337177 m2** (+4.885), blocked lines 4 -> 5; FIN.PAINT.CEILING 389.940677 ->
  394.825677 (+4.885); FIN.CEILING.BULKHEAD valued unchanged 27.9345, blocked 0 -> 1. Ceiling of the piece: decor 4.885
  + HELD strip 0.760 = 5.645 = the floor piece (one plan area).
- Totals move ONLY in the codes this version owns (asserted): ARCH.SPACE, FIN.FLOOR.PORCELAIN, FIN.FLOOR.BED.DRY (m2,
  m3), FIN.SKIRTING, FIN.CEILING, FIN.PAINT.CEILING, FIN.CEILING.BULKHEAD.
- **Acceptance figure restated with its cause:** the row's 288.1458 -> 293.7908 is the T-427 dry basis on V3.0.36 =
  FIN.FLOOR.PORCELAIN 297.775973 less the GF wet-kind room GF-RA3AD49 billed in porcelain 9.630 (counted wet by T-427):
  288.145973. On the same basis: V3.0.40 = 299.375973 + 6.1275 (FIN.FLOOR.FINISH_HELD stair-room parts, T-421) - 9.630 =
  **295.873473** (= T-427's 296.7733 less the three V3.0.38 lift-threshold deductions 0.300 x 3 = 0.900) -> V3.0.41
  **301.518473** (+5.645; = T-427's corrected 302.4183 less the same 0.900).

## 4. Engine vs freelancer (dry floor, T-427 basis, freelancer FIN workbook tiles sheet 337.57 m2, quantities only)

| | engine m2 | freelancer m2 | difference | % |
|---|---|---|---|---|
| V3.0.40 | 295.8735 | 337.57 | -41.6965 | -12.35 % |
| **V3.0.41** | **301.5185** | 337.57 | **-36.0515** | **-10.68 %** |

The -36.05 m2 left is T-427's named residual (pantry -13.4549 RULE_DIFFERENCE, round-stair treads -6.1244
RULE_DIFFERENCE, band + curb -9.705 HELD D-48, 1F / 2F rule differences, +6.1275 stair-room parts UNRESOLVED, -0.6273
UNEXPLAINED) plus the 0.900 of lift thresholds now B6-07. **Verdict proposal: the 5.645 m2 ENGINE_WRONG -> corrected,
FREELANCER_RIGHT** (T-427 Checker own hand 3.80 x 1.30 - 1.10 x 0.05 + 3.80 x 0.20; own re-read here AGREES). Skirting
+3.90 lm: ENGINE_WRONG (silent omission) -> corrected; his open-plan skirting row is a gross perimeter (T-106
RULE_DIFFERENCE), not compared line by line. Ceiling +4.885 m2: ENGINE_WRONG (silent omission, T-435) -> corrected.

## 5. Completeness join after the package (acceptance ACCEPTANCE ADDS 16:15 / 20:17)

T-446 is MERGED (6eb62232): its census is cited (lift threshold B6-07 = CEILING_ON_HOST_FACE / OPENING_SOFFIT_IN_WALL /
DOORWAY_STRIP; stair-room parts on their parents L-2175a965 / L-47fa825d, T-443 lane I). The R-T446-1 join run on the
V3.0.40 and V3.0.41 lines (`summary_t431.json` join_v3_0_40 / join_v3_0_41, the T-446 code unchanged; for V3.0.41 the
dining piece's skirting carries the host reason SKIRTING_ON_HOST_FACE L-71e2e002, since its +3.90 lm lives on the open
room's one line by named rows):

| Space / layer | V3.0.40 | V3.0.41 |
|---|---|---|
| GF-RFD4E1D CEILING | SILENT 5.645 m2 | **PARTIAL** (L-ba5ea9bd 4.885 + HELD L-4b41debf): **0 silent m2** |
| GF-RFD4E1D SKIRTING | SILENT 3.900 lm | **REASON** (host line L-71e2e002, rows GF-RFD4E1D:wall / :column): 0 silent |
| GF-OP-003-NO-OPENING / GF-SITE-0a31 CEILING | SILENT 0.600 / 1.100 | unchanged (pantry strips, not this row) |
| GF-STRIP-OP-020 / -027 SKIRTING | SILENT 0.400 / 0.300 | unchanged (T-443 / T-460 rows) |

Ceiling silent m2: 7.345 -> **1.700**.

## 6. Held, missing, downstream

- HELD (never 0): band 9.101 (ARCH.EXTERIOR, unchanged) and curb 0.604 (L-554a525e) on D-48; bulkhead faces over the
  piece (edge 6.5428 m beside; depth / decor side not decided for this face, R-CEIL-R3-2 not run on it); ceiling over the
  0.760 west strip (no ceiling-ledger reading); the piece's tile thickness (bed drawing bound); finish material is the
  owner default (ASSUMED — OWNER-APPROVED), not a schedule.
- Downstream: plaster / paint of the dining wall faces are in the T-128 open-room ledger (it walks the region holding the
  whole band, T-427 s.5): not moved here. D-48 text 13.986 -> 9.705 m2 is a Lead / RFI text item. Export
  (`tools/boq_export_v1.py` + verdicts/V3.0.29/DOWNGRADES.json): 4,838 rows (EXCLUDED 806, HELD 2,559, MEASURED
  UNVERIFIED 1,473), every DG APPLIED, the retired line EXCLUDED with its reason, the held lines blank with reason.
- Registry: BOQ_FAMILY_MASTER_1.36.0 (pending V3.0.41; B2-02, B3-01, B3-05, B3-06, B4-06, B5-01, B5-04 evidence / reader
  / missing text only; no capability, owner or candidate state change).

## 7. Rule, tests, lessons

R-T431-1 (every villa; integrates R-T427-1 and R-T420-1; module `engine/source/arch_v3041.py`): ONE physical floor piece,
ONE quantity per layer: (a) the new floor line re-adds exactly the parts the zone lines give up; (b) a zone line gives
up only parts it held, by id, and keeps the rest in its own state (RETIRE / SHRINK); (c) bed m2 = finish net; (d) the
piece's skirting is added once, to the one line of the room it joins, on that line's merged net, as named rows; (e) the
piece's ceiling is one decor line, one paint line, its bulkhead and any unread part HELD blank with their figures beside;
(f) held is never 0. The R-T284-1 ceiling checks (A3032.check_ceilings) run on the new ceiling lines too.

Tests `tests/t431_zone_extent_integration` (23): villa K431 (not Alsenan) by hand (normal: floor 4.31, retire 3.56,
shrink 1.25 -> 0.50, skirting 28.00 -> 31.10, bed 0.1293 .. 0.1724, ceiling 3.56 + held 0.75); byte-identity of every
other line; overlap (zone before = piece + kept curb); input order / mirror free (no coordinate in the module); totals
only in own codes; ADVERSE 'a zone prolonged past its own drawn end' (the strip line keeps the west strip -> refused),
part held by no line, area not closed, HELD_AS_ZERO, mm / mm2 refused, missing owner bed / b / area status, stale
bindings (skirting net, floor template), applied twice, a face already carrying a ceiling, ceiling not one plan area,
RETIRE with a kept part, tampering caught by check_pieces (strip still carrying the part, held as 0, paint not decor);
registry 1.36.0 (6).

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-02 | the 5.645 m2 dining piece, its 3.90 lm skirting and 4.885 m2 ceiling were in no valued line of the candidate for 12 days after T-427 named them | a zone correction reaches every layer of the piece (floor, bed, skirting, ceiling, paint) only if they are integrated in ONE step; the ceiling ledger had held the face for its class only, and no line was ever built from it | R-T431-1 (every villa): a piece moved between zones is integrated with all its layers at once; the zone lines give the parts up by id; each layer closes against the floor piece (ceiling decor + held = floor; skirting rows = the piece's own faces) | tests/t431_zone_extent_integration | proposed |

## 8. Validation

- L1 / L2: `tests/t431_zone_extent_integration` 23 pass; t430 / t429 / t421 / t420 pass with the new registry.
- L3: the 73 test folders that import `tools/urban_boq_m9.py` or any `arch_v30*` module (impact HIGH on urban_boq_m9:
  V3041 named inside the cmd_arch / main hubs, `--v3041-inputs`, the v30 .. v3040 method tuples in cmd_arch extended by
  V3041; no new top-level statement, so the T-467 released-path freeze index V2 holds): **74 folders + t061 on 280208f3
  (after merging the working head d4f11fe2): 2,912 collected, 0 failed, 0 errors, 22 skipped (private inputs), 2
  xfailed; exit 0** (tests/t467_released_freeze included).
- freeze V1 0 and freeze V2 (`research/freeze_integrity/freeze_verify_v2.py check --index FREEZE_BASELINE_INDEX_V2.jsonl`)
  0; codemap check stale none; BOQ_FAMILY_MASTER_1.36.0 equals its builder, FMC.check problems [].
- The official run used the CLI before the V3041 name moved into the hub (identical behaviour: the same method string;
  `arch --help` lists ARCH_TAKEOFF_V3.0.41).

## 9. For the Checker (Gate B)

1. Reproduce: the three commands in section 0; expect V3_0_40 `aa6aa927` and V3_0_41 `5176c7c4`.
2. Re-measure on P7757.dxf: B3 -> 310 = 3.800; 2FCF 1.100 x 0.050 proud; A8 1.500 from 104 -> 5.645 m2; skirting 2.70 +
   1.20 = 3.90 lm.
3. Own line diff V3.0.40 -> V3.0.41: 3 CHANGED (L-6b6412e8, L-554a525e, L-71e2e002), 7 ADDED, 4,828 SAME.
4. `python3 -I research/agents_t431/build_master_1_36_0.py --check`.
