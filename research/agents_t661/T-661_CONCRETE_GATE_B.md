# T-661 CONCRETE GATE B: integration package ARCH_TAKEOFF_V3.0.62 (B10 held lines from the merged member ledgers)

Worker 3 (lane I), 2026-11-10, branch `agents/task-T-661`. **Integration package for Checker Gate B.** Opt-in
candidate only: the released default V2.9 + route G is untouched; nothing is released; no rule, owner decision or
frozen file changes. Development villa, not an accuracy claim. ERS s.2-5, WORKFLOW_CONTROLS s.1 / s.5, UP-QTY-STATUS-001.

## 0. What was wired, from what

| Source (Checker-merged) | Merge | Checker run | Lines | Wired as |
|---|---|---|---|---|
| T-657 neck ledger (`research/agents_t657/out/T657_NECK_LEDGER.json`, sha 06555295) | d96a2958 | Verifier 2026-11-09T21:56Z Gate A PASS (5 necks by hand AGREE) | 36 | 32 BOUND, 4 LOWER_ONLY |
| T-660 beam ledger (`research/agents_t660/out/T660_BEAM_LEDGER.json`, sha 807dfb5b) | 9c91709f | Verifier 2026-11-09T23:57Z Gate A PASS (5 of 5 re-measured from the dxf) | 27 | 1 VALUE, 5 BOUND, 12 HELD_BLANK, 8 CONFIRM, 1 not wired |
| T-659 small B10 ledger (`research/agents_t659/out/T659_LEDGER.json`, sha 50e51242) | 907ace46 | Verifier 2026-11-09T21:54Z Gate A PASS | 16 | 15 CONFIRM, 1 not wired |
| T-655 line index V3.0.61 (`research/agents_t655/out/LINE_INDEX_V3_0_61.json`, sha 10e5f116) | bfea3449 | (binding only) | 5,073 | reproduced byte for byte by this run |

T-658 r2 (columns / ground beams / footing) is NOT in this package: it MERGED (2cec1520, Verifier 2026-11-10T02:10Z) after this package's run of record; the branch carries that merge (base merged at fe7f5392, targeted tests pass) and T-658 is restaged into this same package as its next round (V3.0.62 extended, one package).

**Not wired, named (never 0):**
- `L-6290a9f3` STR.CONC.BOUNDARY_WALL band: the T-659 drawn bound 5.6392 .. 11.0328 m3 is NOT wired. The Checker's T-659
  residual says T-661 must first settle a cross-trade fact: on side 1, the lower street (6.70) and lower sea (7.90)
  stretches the building stands on the plot line with its own 0.30 exterior G.B; whether the foundation band continues
  below them is not printed. If it does not, 5.6392 is not a lower bound; if it does, the band overlaps building G.B
  lines (double count). No merged ledger settles it, so the line keeps its V3.0.61 state (7.2204 closed range) and the
  item stays open (WAITING `T661_BOUNDARY_BAND`). Proposal for the Lead: a lane S row (re-read the GF plan / ST p.14
  along those stretches, net the band of the building G.B, one owner per prism).
- T-642 GF BAND0030.2 depth companion (0 .. 0.025 m3): a trial-BOQ r4 overlay line, not a candidate line; it enters with
  the T-642 split wiring (L-efd3f780 0.04 .. 0.12 stays as in V3.0.61). This is exactly the difference between the T-660
  ledger's after-bound (5.983085 .. 8.412278) and this candidate's (6.023085 .. 8.507278): +0.04 / +0.095 = the unsplit
  L-efd3f780 range less the companion.
- Pool blinding (ST p.7 '10cm PLAIN CONCRETE'): MISSING from the candidate (T-659), needs a lane S row.

## 1. Owner manual method beside the drawing-derived method

| Element | Owner / freelancer manual method | Drawing-derived method (wired) |
|---|---|---|
| Neck (B10-03) | one flat 1.50 m x section (freelancer 8.805 m3 on 34 necks) | h from top + 1.50 printed minimum - 0.17 stack - H_max (low) to 2.50 - H_min of the single-row ST p.13 detail (high) x schedule section (R-T657-1); lift necks: lower end only, pit raft depth by the supplier (D-43, R-T657-2) |
| Beam piece past col 335 (B10-07) | 0.5 x 0.75 x 1.501 = 0.562875 | 1.500 x (0.500 x 0.75 - 0.20^2 (1 - pi/4)) = 0.549624 (R-T660-1), Checker re-measured |
| Unlabelled pieces | the neighbour's section continued | breadth-0.20 schedule rows 0.40 .. 1.20 x face-to-face length (R-T660-2) |
| Strips with no mark / bars / depth, east dome ring | no row | HELD BLANK, plan area beside (R-T660-3), one-family guard with the parapet family; old beam-schedule envelope set aside 'not drawn' |

## 2. Evidence status (WORKFLOW_CONTROLS s.5)

- VERIFIED: 1 line (BM-GF-059 0.549624 m3, Checker own dxf re-measure; component).
- DRAWING-CONFIRMED bounds, HELD: 32 necks (bounds from printed minimum and printed detail; the founding level itself is
  not printed), 5 unlabelled beam pieces (Q-61 C(4) open).
- HELD (blank) with the drawn measure beside: 4 lift necks (AT_LEAST 0.9515 m3, D-43), 12 strips / ring (plan 8.7464
  m2, D-26 / Q-61 C(3) / C(5)).
- UNCHANGED (CONFIRM, byte-identical): 8 beam lines (7 width conflicts D-27 / D-02, 1 two marks Q-61 C(2)), 15 small
  B10 lines (parapets Q-65 C, pads, blinding, dome 3 Q-27 A, pool steps, lift tie beam / pit D-43).
- ASSUMED - OWNER-APPROVED: none. UNKNOWN: none new.

## 3. B10 before -> after (m3; V3.0.61 run of record 2bc99980 -> V3.0.62 56207c79, 5,073 lines each)

| Code | Released | Held bounded low .. high (lines) | Held blank (lines) |
|---|---|---|---|
| STR.CONC.NECK | 0 -> 0 | 3.075 .. 15.375 (35) -> **8.7724 .. 11.3460 (32)** | 1 -> 4 (lift necks, AT_LEAST 0.9515 beside) |
| STR.CONC.BEAM (137 lines) | 66.321054 -> **66.870678** (+0.549624) | 8.372829 .. 13.779510 (22) -> **6.023085 .. 8.507278 (14)** | 5 -> 12 (plan 8.7464 m2 beside) |
| every other STR.CONC.* code | unchanged | unchanged | unchanged |

Reconciliation (exact): NECK low 3.075 - 2.7 (32 old) - 0.375 (4 lift old) + 8.7724 = 8.7724; high 15.375 - 13.5 - 1.875 +
11.346 = 11.346. BEAM low 8.372829 - 0.375 (valued) - 1.975 (envelope set aside) + 0.000256 (face-to-face term) =
6.023085; high 13.779510 - 0.5625 - 4.7095 - 0.000232 = 8.507278. Asserted in the run by `check_totals` against the
changes alone; no other code total moved (asserted).

Released V2.9 + route G beside: the diff against the released configuration moves only on the changed lines
(QUANTITY_DIFFERS 1,016 -> 1,030, SAME_QUANTITY 576 -> 562: the 14 restated lines that V2.9 carries at a quantity).

## 4. Line-by-line diff vs V3.0.61 (every other line byte-identical: 5,019 SAME, asserted)

54 lines replaced: 49 CHANGED (quantity), 5 CHANGED_TEXT_ONLY (blank -> blank with the plan area beside); 23 CONFIRM
lines asserted SAME. Line ids shortened to 10 characters (full ids, records and bases in `summary_t661.json` and the
run's V3_0_62_INTEGRATION_LEDGER).

| Line | Code | Action | Member | V3.0.61 | V3.0.62 | Beside / set aside |
|---|---|---|---|---|---|---|
| L-8d031491 | BEAM | BOUND | beam HL:BEAM_LEDGER:2F:BM-2F-015#BAND0001.3 (UNLABELLED, 2F) | 0.09 .. 0.271 | 0.090376 .. 0.271128 |  |
| L-f83c4a46 | BEAM | BOUND | beam U-C:BEAMS:1F:BAND0005.1 (UNLABELLED, 1F) | 0.064 .. 0.192 | 0.064016 .. 0.192048 |  |
| L-d62d2fcf | BEAM | BOUND | beam U-C:BEAMS:2F:BAND0006.1 (UNLABELLED, 2F) | 0.248 .. 0.744 | 0.247976 .. 0.743928 |  |
| L-dc8cbfc1 | BEAM | BOUND | beam U-C:BEAMS:2F:BAND0008.1 (UNLABELLED, 2F) | 0.112 .. 0.336 | 0.111944 .. 0.335832 |  |
| L-7c3edce2 | BEAM | BOUND | beam U-C:BEAMS:2F:BAND0011.1 (UNLABELLED, 2F) | 0.112 .. 0.336 | 0.111944 .. 0.335832 |  |
| L-67f3d325 | BEAM | HELD_BLANK | beam HL:BEAM_LEDGER:1F:BM-1F-033#BAND0013.1 (PROJECTION, 1F) | 0.24 .. 0.72 | blank | PLAN_AREA_M2 0.5997; set aside 0.24 .. 0.72 (not drawn) |
| L-54e397fe | BEAM | HELD_BLANK | beam HL:BEAM_LEDGER:1F:BM-1F-033#BAND0013.2 (PROJECTION, 1F) | 0.042 .. 0.126 | blank | PLAN_AREA_M2 0.1048; set aside 0.042 .. 0.126 (not drawn) |
| L-56d278be | BEAM | HELD_BLANK | beam HL:BEAM_LEDGER:1F:BM-1F-036#BAND0025 (PROJECTION, 1F) | 0.676 .. 1.015 | blank | PLAN_AREA_M2 1.5441; set aside 0.676 .. 1.015 (not drawn) |
| L-fbb65dfd | BEAM | HELD_BLANK | beam HL:BEAM_LEDGER:1F:BM-1F-037 (PROJECTION, 1F) | blank | blank | PLAN_AREA_M2 0.4 |
| L-377cb988 | BEAM | HELD_BLANK | beam HL:BEAM_LEDGER:1F:BM-1F-038 (PROJECTION, 1F) | blank | blank | PLAN_AREA_M2 0.569 |
| L-17c4238c | BEAM | HELD_BLANK | beam HL:BEAM_LEDGER:2F:BM-2F-019#2F-031 (PROJECTION, 2F) | blank | blank | PLAN_AREA_M2 0.435 |
| L-634cefe5 | BEAM | HELD_BLANK | beam HL:BEAM_LEDGER:GF:BM-GF-058#BAND0031.1 (PROJECTION, GF) | 0.24 .. 0.72 | blank | PLAN_AREA_M2 0.5998; set aside 0.24 .. 0.72 (not drawn) |
| L-331d4bbe | BEAM | HELD_BLANK | beam HL:BEAM_LEDGER:GF:BM-GF-058#BAND0031.2 (PROJECTION, GF) | 0.042 .. 0.126 | blank | PLAN_AREA_M2 0.105; set aside 0.042 .. 0.126 (not drawn) |
| L-aba59a21 | BEAM | HELD_BLANK | beam HL:BEAM_LEDGER:GF:BM-GF-061 (PROJECTION, GF) | blank | blank | PLAN_AREA_M2 0.82 |
| L-ab37afa1 | BEAM | HELD_BLANK | beam HL:DOME_RING:DOME-1F-E:RING:RING_BEAM_IN_BAY (RING, 1F) | blank | blank | PLAN_AREA_M2 1.7993 |
| L-a9d5e7dc | BEAM | HELD_BLANK | beam U-C:BEAMS:1F:BAND0014 (PROJECTION, 1F) | 0.6 .. 1.8 | blank | PLAN_AREA_M2 1.4999; set aside 0.6 .. 1.8 (not drawn) |
| L-bb49e831 | BEAM | HELD_BLANK | beam U-C:BEAMS:1F:BAND0023 (PROJECTION, 1F) | 0.135 .. 0.2025 | blank | PLAN_AREA_M2 0.2698; set aside 0.135 .. 0.2025 (not drawn) |
| L-8ea71184 | BEAM | VALUE | beam HL:BEAM_LEDGER:GF:BM-GF-059#BAND0046.2 (UNLABELLED_SECT | 0.375 .. 0.5625 | 0.549624 (MEASURED) |  |
| L-31494639 | NECK | BOUND | neck C at 10A4 on F10/F | 0.075 .. 0.375 | 0.267 .. 0.33 |  |
| L-85df35f1 | NECK | BOUND | neck C at 10A8 on F | 0.075 .. 0.375 | 0.192 .. 0.33 |  |
| L-734ff1a7 | NECK | BOUND | neck C at 10AB on F | 0.075 .. 0.375 | 0.192 .. 0.33 |  |
| L-53d0b6af | NECK | BOUND | neck C at 10B4 on F | 0.075 .. 0.375 | 0.192 .. 0.33 |  |
| L-bd741a3f | NECK | BOUND | neck C at 10B7 on F | 0.075 .. 0.375 | 0.2376 .. 0.33 |  |
| L-bbad8cdb | NECK | BOUND | neck C10 at 10E8 on F10/F | 0.105 .. 0.525 | 0.3738 .. 0.462 |  |
| L-b4c234c8 | NECK | BOUND | neck C11 at 10BA on F13 | 0.165 .. 0.825 | 0.5874 .. 0.66 |  |
| L-132cf605 | NECK | BOUND | neck C11 at 10DD on F11 | 0.165 .. 0.825 | 0.5874 .. 0.66 |  |
| L-3f7b9501 | NECK | BOUND | neck C2 at 1084 on F2 | 0.075 .. 0.375 | 0.2895 .. 0.3225 |  |
| L-5aec8a00 | NECK | BOUND | neck C2 at 1087 on F2 | 0.075 .. 0.375 | 0.2895 .. 0.3225 |  |
| L-48f2e06e | NECK | BOUND | neck C3 at 10A0 on F8 | 0.075 .. 0.375 | 0.267 .. 0.3 |  |
| L-dd3c32e4 | NECK | BOUND | neck C3 at 10AE on F15 | 0.075 .. 0.375 | 0.177 .. 0.315 |  |
| L-4ec473f7 | NECK | BOUND | neck C3 at 10B1 on F3 | 0.075 .. 0.375 | 0.192 .. 0.33 |  |
| L-f54b7b2a | NECK | BOUND | neck C3 at 10C5 on F3 | 0.075 .. 0.375 | 0.192 .. 0.33 |  |
| L-ae1bd9cb | NECK | BOUND | neck C3 at 10CC on F12 | 0.075 .. 0.375 | 0.237 .. 0.27 |  |
| L-516989b8 | NECK | BOUND | neck C3 at 10E4 on F14 | 0.075 .. 0.375 | 0.267 .. 0.3 |  |
| L-05a99150 | NECK | BOUND | neck C4 at 108D on F4 | 0.075 .. 0.375 | 0.235 .. 0.315 |  |
| L-46f2b702 | NECK | BOUND | neck C4 at 10D7 on F4 | 0.075 .. 0.375 | 0.282 .. 0.315 |  |
| L-5efd9ac6 | NECK | BOUND | neck C5 at 108A on F5 | 0.09 .. 0.45 | 0.3384 .. 0.378 |  |
| L-c1e80218 | NECK | BOUND | neck C5 at 10BD on F13 | 0.09 .. 0.45 | 0.1944 .. 0.36 |  |
| L-486cd9a0 | NECK | BOUND | neck C5 at 10D3 on F5 | 0.09 .. 0.45 | 0.3384 .. 0.378 |  |
| L-efe50185 | NECK | BOUND | neck C6 at 10C2 on F6 | 0.105 .. 0.525 | 0.3738 .. 0.42 |  |
| L-995eca94 | NECK | BOUND | neck C7 at 10C8 on F12 | 0.12 .. 0.6 | 0.3792 .. 0.432 |  |
| L-fc622ff3 | NECK | BOUND | neck C8 at 10D0 on F8 | 0.135 .. 0.675 | 0.4806 .. 0.54 |  |
| L-15b8ad39 | NECK | BOUND | neck C8 at 10E0 on F14 | 0.135 .. 0.675 | 0.4272 .. 0.54 |  |
| L-b21cbf65 | NECK | BOUND | neck C9 at 10DA on F9 | 0.15 .. 0.75 | 0.519 .. 0.585 |  |
| L-6a2040e0 | NECK | BOUND | neck CN at 10EE on FN | 0.045 .. 0.225 | 0.1152 .. 0.198 |  |
| L-34346cb4 | NECK | BOUND | neck CN at 10F6 on FN | 0.045 .. 0.225 | 0.1152 .. 0.198 |  |
| L-c8c07db4 | NECK | BOUND | neck CN at 10FE on FN | 0.045 .. 0.225 | 0.1152 .. 0.198 |  |
| L-15d9da9b | NECK | BOUND | neck CN at 17C5 on F8 | blank | 0.0972 .. 0.18 |  |
| L-4ef35980 | NECK | BOUND | neck CN at 17C8 on F4 | 0.045 .. 0.225 | 0.1062 .. 0.189 |  |
| L-1a9e4696 | NECK | BOUND | neck CN at 180A on FN | 0.045 .. 0.225 | 0.1152 .. 0.198 |  |
| L-12f3d8b9 | NECK | LOWER_ONLY | neck C1 at 1099 on FF | 0.075 .. 0.375 | blank | AT_LEAST_M3 0.173; set aside 0.075 .. 0.375 (not drawn) |
| L-dd6d1141 | NECK | LOWER_ONLY | neck C2 at 1093 on FF | 0.075 .. 0.375 | blank | AT_LEAST_M3 0.173; set aside 0.075 .. 0.375 (not drawn) |
| L-8eb74a02 | NECK | LOWER_ONLY | neck C2 at 1096 on FF | 0.075 .. 0.375 | blank | AT_LEAST_M3 0.173; set aside 0.075 .. 0.375 (not drawn) |
| L-953e87a3 | NECK | LOWER_ONLY | neck C9 at 1090 on FF | 0.15 .. 0.75 | blank | AT_LEAST_M3 0.4325; set aside 0.15 .. 0.75 (not drawn) |

## 5. Regression and validation

- Run of record (Drive copies 'P7757_DXF_COMPRESSED.zip' ab54dd55 / 'ST7757 dxf.dxf' 9f9d1179, decoded into the private
  folder only): t167 `v304_run.py` -> `research/agents_t661/v3062_run.py` (exit 0): V3_0_59 75331a76, V3_0_60 8c8a9642,
  **V3_0_61 2bc99980 (asserted = run of record)** -> **V3_0_62 56207c79**; every earlier version's identity check re-ran on
  the result (A3061.integrate chain) and passed.
- `t479_registry_census.py` (unchanged) on V3_0_61 reproduces `research/agents_t655/out/LINE_INDEX_V3_0_61.json` byte for
  byte; on V3_0_62 -> `out/LINE_INDEX_V3_0_62.json`, 5,073 lines, issues {}, complete map.
- `t661_package_families.py` (T-483 attribute unchanged, chain 61 -> 62): B10-03 STR.CONC.NECK 36 changed; B10-07
  STR.CONC.BEAM 13 changed + 5 record-only; nothing added or removed.
- Tests: `tests/t661_concrete_gate_b` (hand villa V661 + adverse, master 1.63.0) PASS. L4: every test folder and root
  test file (865) on ea7724b2 in two halves (odd / even): the only failure was t459
  test_candidate_binding_rebuilds (the new module adds its 'later_steps_tokens' entry) -> T459_CANDIDATE_BINDING.json
  rebuilt by its own tool (arch_v3062.py: no lap token, later_steps_touching []), t459 PASS on the final head; private
  inputs absent: 168 test phases skipped by the conftest (known, not new). Targeted re-run on the final head: t661, t485,
  t655, t563, t459, t328, t284, t199, t657, t659, t660 PASS; freeze 0 differing; codemap stale none; build_master
  --check equal, 0 problems; RULES_MANIFEST check [].

## 6. Registry: BOQ_FAMILY_MASTER_1.63.0 (pending now, promoted IN the merge)

`research/agents_t661/build_master_1_63_0.py`: 1.62.0 + V3.0.62 pending + B10-03 / B10-07 text (0 problems). The ADOPTED
lesson (a merged package must not stay pending, F-C-T563-1): in the merge commit the Verifier runs

    python3 -I research/agents_t661/t661_promotions_source.py --board .work/board/docs/agents --out research/agents_t661/out/PROMOTIONS_SOURCE_1_63_0.json
    python3 -I research/agents_t661/build_master_1_63_0.py --promote --write
    python3 -I research/agents_t661/write_manifest.py

which promotes T-661 (T-485 rule R-T485-1, T-483 r2 functions unchanged) with the committed census
`out/LINE_INDEX_V3_0_62.json` and line diff `out/T661_PACKAGE_FAMILIES.json`. Dry run with a simulated merge record:
candidate ARCH_TAKEOFF_V3.0.62, no pending package, B10-03 HELD_IN_CANDIDATE, B10-07 INTEGRATED_IN_CANDIDATE_AND_TESTED,
state counts unchanged 52 / 14 / 6 / 32, census problems [], check [].

## 7. First step F-T655-1 (gate 0)

`tests/t328_roof_buildup/test_family_master_1_26_0.py` and `tests/t284_ceiling_integration/test_family_master_1_27_0.py`:
`_own_head(written, extra, newer, texts)` keeps a code with its first OWN-HEAD writer in the same scan (written-code scan
or V3.0.x literal scan) when a newer module writes it first; only codes written by newer modules alone are set aside.
Normal + 2 adverse tests in each file. On this head the old helper does NOT fail (arch_v3062.py is first writer of no
code those scans judge: latent, as T-655 said); the adverse tests show the old drop and the new keep on a synthetic
newer first writer.

## 8. Rule and lessons row (proposed)

R-T661-1 (in `engine/source/arch_v3062.py`): bind every entry to the line as carried; only STR.CONC.* m3 changes; a
VALUE needs the Checker's re-measure; a retired bound leaves only with its replacement and stays in the record; CONFIRM
lines and every unnamed line byte-identical; only STR.CONC code totals move, by exactly the restatement.

Lessons row (ERS s.7, PROPOSED): | 2026-11-10 | a worker ledger's 'after' figures were stated on a trial-BOQ overlay
(r4), not on the candidate (an unsplit T-642 strip and a companion line), so its family totals differ from the wired
candidate by 0.04 / 0.095 m3 | the ledger was bound to the trial, not to the candidate it is wired into | an integration
binds every entry to the candidate line index and reconciles the ledger's totals to the candidate's in units, naming
each overlay line not wired (every package; provenance T-661) | tests/t661_concrete_gate_b | PROPOSED |
