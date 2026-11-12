# T-717: PLASTER / PAINT GATE B ROUND 2 integration package, ARCH_TAKEOFF_V3.0.74 (lane I, hub H1)

Worker 3, 2026-11-12. INTEGRATION PACKAGE for Checker Gate B. Base: the candidate of record V3.0.73 (T-722, Gate B PASS,
merge 931dc8d9, BOQ_FAMILY_MASTER 1.74.0); released default V2.9 + route G untouched; nothing released, nothing
VERIFIED. No drawing, workbook, client name or coordinate here; Drive files named by folder and title only.

## 1. What is wired (Checker-merged only, T-723 map hub T-717: 36 rows, stale 0)

| source | merge | Checker | wired as |
|---|---|---|---|
| T-701 `out/T701_RECONCILE.json` R-T701-2 (annex ENGINE_WRONG, bound too narrow) | 65083ee7 | Verifier 2026-11-11T10:03Z Gate A PASS, own re-measure GF-04 12.500 lm, 34.33 .. 43.78 AGREE; GF-01 arithmetic AGREE | BOUND x 2 (GF-01, GF-04) |
| T-702 `out/T702_TILES_ROUND3.json` part (c) beam crossings / sunken panels | b90d85af | Verifier 2026-11-11T12:01Z Gate A PASS | BOUND x 2 (GF-07, GF-14 wet bands) |
| T-709 `out/T709_RESIDUALS.json` R-T709-1 band, R-T709-4 return paint, F-T709-1 W12 | fe461c6e | Verifier 2026-11-11T13:59Z Gate A PASS, own well run 11.170 lm, band by hand 0.840 .. 0.8715 AGREE, W12 arithmetic AGREE | RETURN_PAINT x 30 (ADD), DH_BAND x 2 (ADD), F-T709-1 on GF-01 |
| T-719 `out/T719_VOIDS.json` (V-01 light well, walls AF7 4.00 / AEC 7.02) | 302e002d | Verifier 2026-11-11T23:53Z Gate A PASS | band prerequisite 1 (void named; union, deducted once) |
| T-723 `out/T723_READINESS.json` (R-T723-1 map) | 5d00f738 | Verifier 2026-11-11T23:51Z Gate A PASS | line-by-line map (4 CHANGE, 32 ADD) |

Each ledger is sha-pinned and REBUILT by its own merged builder (`t701_alsenan` / `t702_alsenan` / `t709_alsenan` /
`t719_alsenan` / `t723_alsenan`.build()) and asserted equal to the committed file (`t717_inputs.py`). Band
prerequisite 2 (the GF-08 region carries the GF face under the 1F well wall): checked on the run's own V2.9 rooms by
`v3074_run.py` REGION_CHECK: face 336 (2.650 m, read by handle) lies on the boundary of the one GF room carrying the
V01 double height (GF-RC99C2A, 126.928 m2, double height 16.005 m2) over its full 2.650 m, the room on the well side
only: **PASS**. So the band continues the GF-08 face; the larger omission T-709 named (3.997 x 4.29) does not arise.

## 2. Method (R-T717-1, every villa; module `engine/source/arch_v3074.py`)

- Physical element first (ERS s.2.1): a room's plaster face to the structural soffit (annex on the bounded datum); a
  wet-room band between the finished ceiling and the soffit; the plastered return face of an opening and its paint; a
  wall through a slab-free stairwell, one face from the lower floor to the upper floor.
- FIN_RESTATE (BOUND): the candidate range each ledger started from is asserted to 1e-6 (stale = stop); the line takes
  the ledger bound; a named correction (finding + delta) is applied to both ends exactly (Decimal); never a value.
- RETURN_PAINT: one FIN.PAINT line per plaster return face id, HELD 0 .. the face's plaster m2 on the live line (low 0
  = the frame / casing over the whole jamb, the only extreme the drawings allow while the frame-covered depth is
  printed nowhere; allowed on this piece only) or HELD blank where the face is blank; flags kept.
- DH_BAND: low .. high RECOMPUTED from run x (upper - lower) - landing piece (low) + column returns (high), Decimal,
  asserted equal to the ledger; bound by id to the room line of its own code, never summed into it.
- Totals: only FIN.PLASTER|m2 / FIN.PAINT|m2 move, each exactly by the changes (asserted); released never moves; every
  other line byte-identical (asserted); V3.0.64 .. V3.0.73 state checks re-run on the result.

Owner manual method vs drawing-derived method (per piece): owner = wall face lm x height (plaster to the slab
underside Q-72, paint to the finished ceiling Q-48 A) - every opening in full (Q-73); return = jambs + head x wall
thickness less the frame-covered depth; stairwell wall one face floor to floor (Q-72). Drawing = the merged ledgers:
annex S over the R-T678-2 / T-686 datum bound (Q-54 B: bounds only); W12 1.95492 x 2.20 = 4.300824 (F-T709-1); GF wet
bands with beam B27 / B11 crossings and sunken panels 280 / 287 / 275 / 276 (drop printed nowhere, D-41); returns by
handle (T-634); band run 336 2.650 + columns 0.800 + 0.547201 = 3.997201 m, plaster +5.29 (GF soffit T-556) .. +5.50
(1F floor), paint +4.65 (GF ceiling G1) .. +5.50.

## 3. Lines (m2; evidence status per WORKFLOW_CONTROLS s.5: every line HELD)

| line | V3.0.73 | V3.0.74 | hand (ledger terms) | held on |
|---|---|---|---|---|
| GF-01 plaster L-b1529955 | 61.46433 .. 65.25433 | **47.949844 .. 66.249856** | T-701 datum bound 47.960668 .. 66.26068 - 0.010824 (W12 4.29 -> 4.300824) | annex datum Q-54 B; A-GF-01 arch D-45 |
| GF-04 plaster L-1ddc23d5 | 43.155 (held point) | **34.33 .. 43.78** | 12.5 x 3.084 - 4.22 .. 12.5 x 3.84 - 4.22 | annex datum Q-54 B |
| GF-07 wet band L-ea586fea | 2.853686 .. 6.918815 | **0.499037 .. 6.186806** | T-702 (c): B27 fills 1.143764 lm, sunken 280 / 287 over 4.476 lm at 0 .. full | D-39 / DCR-6, D-41 |
| GF-14 wet band L-ef7a1666 | 5.05488 .. 5.29088 | **3.892324 .. 5.005988** | T-702 (c): B11 square + oblique, sunken 275 / 276 over 1.718 lm | D-41 |
| 27 return-paint lines (ADD) | - | 0 .. face, sum **0 .. 24.150** | high = the face's plaster m2 (released) | frame-covered depth (designer) |
| 3 return-paint lines (ADD) | - | blank | A-GF-01 / A-1F-01 / D-GF-15 plaster faces blank | D-45 / D-53 |
| stairwell plaster band (ADD) L-b10c1b35 | - | **0.839412 .. 0.870912** | 3.997201 x 0.21 (+ 0.15 x 0.21) | beam faces below held by name |
| stairwell paint band (ADD) L-ab4ed432 | - | **3.344721 .. 3.525121** | 3.997201 x 0.85 - 0.0529 (+ 0.15 x 0.85) | as above |

5 return lines carry NOT_ESTABLISHED (wet rooms both sides: 1F OP-010, GF OP-017 / OP-018, reveals D-GF-02 /
D-GF-10; R-T701-3 one finish per face): whether the return is painted at all is not established; the 0 .. face bound
covers both outcomes (Gate B statement asked by T-723).

## 4. Run of record, census, diff

Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) and 'ST7757 dxf.dxf'
(9f9d1179), decoded by the wrapper into the private folder only: own fresh t167 `v304_run.py` -> `v3074_run.py`
(exit 0): every earlier version re-run and asserted by its own wrapper (V3_0_72 f9578744), **V3_0_73 c5a0b128
(asserted = the T-722 run of record by its line index) -> V3_0_74 bea5be02**, 5,155 lines; replaced 4, added 32,
outside 5,119 byte-identical (asserted). Diff vs V3.0.73: CHANGED 4, ADDED 32, SAME 5,119. vs released V2.9 + route G:
NOT_IN_RELEASED 3,563 (+32, the added lines), QUANTITY_DIFFERS 1,054, SAME_QUANTITY 538 (unchanged). Census
`t479_registry_census.py` (verdicts board verdicts/V3.0.44 b3b08dd7, downgrades 81732639): on V3_0_73 it reproduces
`research/agents_t722/out/LINE_INDEX_V3_0_73.json` byte for byte; on V3_0_74 -> `out/LINE_INDEX_V3_0_74.json`
(6733cbc1), issues {}, complete map, 0 stale blocks. `t717_package_families.py` (chain 73 -> 74): B4-03 FIN.PLASTER
changed 4 + added 1; B4-06 FIN.PAINT added 31. Summary `out/T717_SUMMARY.json`.

| code (m2) | released n / m2 | bounded n, low .. high V3.0.73 | V3.0.74 | blank |
|---|---|---|---|---|
| FIN.PLASTER | 43 / 388.58436 (unchanged) | 34, 1,131.965876 .. 1,300.69428 | **35, 1,106.948597 .. 1,302.168817** (low -25.017279, high +1.474537) | 3 -> 3 |
| FIN.PAINT | 4 / 217.2081 (unchanged) | 10, 601.645338 .. 682.3313 | **38, 604.990059 .. 710.006421** (low +3.344721, high +27.675121) | 0 -> 3 |

By hand: plaster low -13.514486 - 8.825 - 2.354649 - 1.162556 + 0.839412 = -25.017279; high +0.995526 + 0.625 -
0.732009 - 0.284892 + 0.870912 = +1.474537; paint low = band 3.344721, high 24.150 + 3.525121 = 27.675121 (asserted by
the module's totals check). T-701's Checker forecast 1,109.637 .. 1,302.326 if wired: the same less W12 (0.010824)
and the T-702 / band rows.

## 5. Like-for-like scoreboard line (T-701 dry + shaft; T-726 ruling: his 13.50 row shown apart)

| layer | engine V3.0.73 (T-701) | engine V3.0.74 | his gross | vs his gross | his 13.50 NO_FACE row apart (1,155.625) |
|---|---|---|---|---|---|
| plaster | 984.249810 .. 1,053.666410 | **961.910324 .. 1,055.286936** | 1,169.125 | -17.72 .. -9.74 % | **-16.76 .. -8.68 %** (was -14.83 .. -8.82) |
| paint | 818.853438 .. 899.539400 | unchanged (GF-01 / GF-04 paint not in the map) | 1,169.125 | -29.96 .. -23.06 % | -29.14 .. -22.16 % |

The 13.50 is never added to the engine and never removed from his total (T-726 R-T726-1..3: continuation of his
stair-house row, no drawn face); the stairwell band and the return-paint lines are new elements the T-701 set does not
hold: shown beside, never added to his comparison.

## 6. Findings, held / missing, downstream, verdicts

- **F-T717-1 (GF-01 paint, F-T709-1).** The same W12 deduction puts the GF-01 PAINT line 0.010824 m2 high; it is not in
  the T-723 H1 map, so it is not touched here (named in WAITING T717_PAINT_GF01_W12; next GF-01 paint restatement).
- **F-T717-2 (band prerequisite 2 settled).** REGION_CHECK PASS on the run's own rooms (section 1); the T-709 named
  uncertainty is closed for the band; the beam faces under the 1F well walls (south 3.020 lm, west 4.000 lm) stay HELD
  by name (structural GF roof slab plan not read); no line opened for them.
- **F-V709-1 carried, not applied.** Checker GF solid 4.000 m vs ledger 3.997201 (2.8 mm frame offset): +0.000588 /
  +0.0024 m2 on the plaster / paint band; immaterial, wired as merged, named.
- Held: every changed / added line HELD (35 bounded, 3 blank of the 36); annex datum Q-54 B, D-39 / DCR-6, D-41, D-45,
  D-53, frame-covered jamb depth (designer), NOT_ESTABLISHED x 5.
- Downstream: no tile, WP, skirting, bead or material line moves; the coat materials stay MISSING (T-364); beads H2
  bind plaster heights by host (T-728) and read the restated GF-01 / GF-04 bounds at their own wiring.
- Freelancer: annex GF-01 72.00 (20 x 3.60) / GF-04 45.00 vs 47.949844 .. 66.249856 / 34.33 .. 43.78: RULE_DIFFERENCE
  (his flat 3.60 and half deductions vs Q-72 / Q-73; T-701). Wet bands and the stairwell band: no row of his
  (NOT_COMPARABLE; the band is ENGINE_RIGHT as the closed T-709 omission). Returns: T-709 bridge stands (count
  FREELANCER omission, unit RULE_DIFFERENCE); paint returns not priced apart by him (NOT_COMPARABLE).
- Verdict proposals: 2 annex BOUND ENGINE_RIGHT as bounds (Checker AGREE in T-701 Gate A; GF-01 W12 arithmetic AGREE
  in T-709), 2 wet bands ENGINE_RIGHT as bounds (T-702), 2 stairwell bands ENGINE_RIGHT as bounds, 27 return-paint
  bounds HELD (low 0 until the depth is printed), 3 blank HELD, 5 NOT_ESTABLISHED.

Lesson row (ERS s.7, proposed): | 2026-11-12 | a band prerequisite ('the region carries the face') sat open across two
rounds as a reading task | the readiness map named the uncertainty but no step tested it on the run of record | test a
geometric prerequisite on the run's own regions in the integration run (face by handle on the room boundary, room on
one side), fail the run of record on FAIL, never wire on a named uncertainty | v3074_run.region_check; tests/t717_
finish_gate_b2 | PROPOSED.

Tests (`tests/t717_finish_gate_b2`, villa F717 by hand, non-Alsenan): normal (annex bound with correction 24.99 ..
35.99, wet band 0.5 .. 2.8, return 0 .. 0.8 / flagged 0 .. 0.78 / blank, bands 0.5 .. 0.52 and 1.96 .. 2.08, totals by
hand plaster -6.01 / +4.31 and paint +1.96 / +3.66 with released unchanged, outside lines byte-identical, mirror and
shuffled order, census and written files); adverse (stale binding, return low > 0, return high off its face, figure on
a blank face, band in mm, inverted band, band off its terms, VERIFIED / owner-approved status, applied twice, two
returns on one face, non-plaster restatement, released host, correction without finding or a unit slip, after not the
ledger + correction, band on a host of another code, missing host); family master 1.75.0 (pending; builder; adverse
as T-722).

## r2 (worker 3, 2026-11-12, after the Checker r1 verdict 07:50Z: one L4 failure only)

- Fault: `research/agents_t459/T459_CANDIDATE_BINDING.json` lacked `engine/source/arch_v3074.py` in
  `later_steps_tokens` (tests/t459_lap_rule::test_candidate_binding_rebuilds). Fixed by its own tool:
  `bash scripts/agent_env.sh run --tree task-T-717 research/agents_t459/t459_census.py candidate --write`
  (commit f4bd57cd): one key added, `arch_v3074.py: []`; `later_steps_touching` stays `[]`, lap-convention lines with a
  quantity stay 0. No quantity moves.
- Working branch 6143f30d merged first (T-720 / T-730..T-733: research + tests only); CODEMAP regenerated by the tool.
- Validation on the r2 head: tests/t459_lap_rule + tests/t717_finish_gate_b2 pass; L4 full suite to the end (931 items
  `ls -d tests/*/ tests/test_*.py`, 78 chunks of 12, every chunk exit 0): 23,915 pass, 0 fail, 700 skip, 105 xfail;
  freeze 0 differing; codemap stale none.
- Run of record reproduced from fresh Drive copies (P7757.dxf ab54dd55, ST7757 dxf 9f9d1179; own t167 v304_run.py, then
  v3074_run.py exit 0): V3_0_72 f9578744 -> V3_0_73 c5a0b128 -> **V3_0_74 bea5be02** (5,155 lines; CHANGED 4, ADDED 32,
  SAME 5,119), REGION_CHECK PASS (face 336 2.650 m on GF-RC99C2A, 16.005 m2 V01), censuses identical to section 4.
  Every r1 verdict part other than L4 stands unchanged.
- Lesson L-T717-1 (proposed): a Gate B package that adds an arch_v30xx module rebuilds every candidate-bound artefact
  that lists those modules (T459 binding, maps) by its tool in the run-of-record commit.
