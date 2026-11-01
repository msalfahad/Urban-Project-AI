# T-429 integration package: stair tread / step binding (T-425 + T-434) into ARCH_TAKEOFF_V3.0.39

Worker 3 (lane I), 2026-11-01, branch `agents/task-T-429`. **Integration package for Checker Gate B.** Integrates:
T-425 (MERGED 6f159091, Gate A PASS, finding F-C-T425-1) and T-434 (MERGED a6b325b3, Gate A PASS: section A-A governs
the ST-01 winder turn). Candidate of record before: ARCH_TAKEOFF_V3.0.38 (json `57cca61c`, T-421 Gate B, merge
bc9f293c). NOT RELEASED; the released default V2.9 + route G is unchanged; rollback = V3.0.38 / V2.9. Development villa
(Alsenan), not an accuracy claim; the method (R-T429-1) is for every villa. Drawings are cited by Drive folder and title
only.

## 0. Run identity

Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip (`ab54dd55`), 'ST7757 dxf.dxf' (`9f9d1179`),
decoded by the wrapper into `.work/private`. Own fresh `research/agents_t167/v304_run.py`, then
`research/agents_t429/v3039_run.py` (Python 3.11.18): **V3_0_36 `d462203f`, V3_0_37 `733f2efb` and V3_0_38 `57cca61c`
reproduced** (the T-246 / T-420 / T-421 Gate B figures), **V3_0_39_BOQ_LINES.json `8d1bbe5d`** written beside
them (4,829 lines; `summary_t429.json`, built by `t429_summary.py` from that run). Inputs:
`research/agents_t429/t429_inputs.py` reads ONLY the merged files, each pinned by sha256 (LINE_TABLE_T425.csv,
FLIGHT_TABLE_T425.csv, BINDING_T425.json, ALSENAN_TURN_T434.json); typed there: the flight levels (cited to T-184 /
T-425 / T-434 / T-415) and the riser-line dispositions the Checker verdicts name.

## 1. The physical element and who owns it (ERS s.2.1)

A TREAD is the going surface behind one drawn front (nosing) edge; a landing or floor edge is the top nosing of a flight
and has no tread behind it (T-412 R-T412-1). B7-02 (tread marble, m2) and B7-06 (commercial step, lm, UP-STAIR-008) are
owned by the FLIGHT, one physical run of steps between two levels. The engine reads flights per storey plan, so one
physical flight can appear up to three times: below the cut on its own plan (OWN), hidden above the cut on the plan
below (PARTIAL), and again on the plan above, seen down through the opening (SEEN_THROUGH). B7-03 (visible riser) has
one line per reading too; every riser line is BLOCKED_RFI (riser height basis open), so no m2 moves on it here.

Owner trade: B7 STAIRS for every line in this package (no cross-trade move; the T-410 notch deduction 0.1175 m2 stays
outside these figures, as in T-425; the landing marble B7-04 bounds are untouched).

## 2. What the package does, per line (ERS s.2.2: owner manual method and drawing-derived method side by side)

| | Owner manual method | Drawing-derived method (merged ledgers) |
|---|---|---|
| Tread m2 | drawn treads x going x stair width, every flight once (OWNER_RULE_STAIRS s.1) | each candidate reading bound to a drawn flight by handle (T-425: run positions, both layers, levels); treads = drawn fronts; one carrier per flight |
| Step lm | number of steps x width (UP-STAIR-008) | drawn fronts x drawn width 1.150 |
| Winder turn | never generated, HELD (S-9) | section A-A governs 5 winders (Q-46 A, T-434); plans draw a 4-riser fan: subdivision not drawn -> HELD |
| Round stair curved part | HELD (Q-50 A cond) | 12 radial treads reconstructed from the plans -> HELD |

Actions (one per line; `V3_0_39_INTEGRATION_LEDGER.csv`): KEEP (asserted, not rewritten), CORRECT (carrier to the drawn
figure, same id, SOURCE_DERIVED), SUPERSEDE (DOUBLE_COUNT / FOLDED: NOT_APPLICABLE_WITH_EVIDENCE, owned by the carrier,
never deleted), HOLD (BLOCKED_RFI blank with the cause and the figure(s) beside, never 0).

| Line | Code | Reading (plan) | Flight | Role | Action | V3.0.38 | V3.0.39 | Evidence status | Beside / owner |
|---|---|---|---|---|---|---|---|---|---|
| L-151d92470a81dd1c450b | B7-02 m2 | SITE-3759f2457b22cb4a:F1 (GF) | MS1-L | OWN | CORRECT | 2.415 | 3.105 | VERIFIED | - |
| L-d4d764ae7bb07b474b6f | B7-06 lm | SITE-3759f2457b22cb4a:F1 (GF) | MS1-L | OWN | CORRECT | 8.05 | 10.35 | VERIFIED | - |
| L-b4660de0ddd98ad0ffc2 | B7-02 m2 | SITE-a95bf979baf4cfae:F5 (1F) | MS1-T | SEEN_THROUGH | HOLD | 1.495 | HELD blank | HELD | beside 1.495; governing count 5 |
| L-e085c168dee5fb19a7fb | B7-06 lm | SITE-a95bf979baf4cfae:F5 (1F) | MS1-T | SEEN_THROUGH | HOLD | 4.7815 | HELD blank | HELD | beside 4.7815 / 4.14365; governing count 5 |
| L-e1eb8b9a7cb92508ccc9 | B7-02 m2 | SITE-a95bf979baf4cfae:F3 (1F) | MS1-U | OWN | CORRECT | 3.45 | 3.795 | DRAWING-CONFIRMED | - |
| L-0aa47300a16de572c967 | B7-06 lm | SITE-a95bf979baf4cfae:F3 (1F) | MS1-U | OWN | CORRECT | 11.5 | 12.65 | DRAWING-CONFIRMED | - |
| L-79beb9688604887c59c5 | B7-02 m2 | SITE-d7254c68fd33723d:F1 (2F) | MS2-L | SEEN_THROUGH | SUPERSEDE | 3.45 | listed, no qty | NOT_APPLICABLE | owned by L-65806b4d02d476603bc5 (DOUBLE_COUNT) |
| L-1e88ac0d4ba0b4e8a950 | B7-06 lm | SITE-d7254c68fd33723d:F1 (2F) | MS2-L | SEEN_THROUGH | SUPERSEDE | 11.5 | listed, no qty | NOT_APPLICABLE | owned by L-23651ecfef77992ec8d4 (DOUBLE_COUNT) |
| L-07f00d5b0c4e1924aaf5 | B7-02 m2 | SITE-d7254c68fd33723d:F2 (2F) | MS2-U | OWN | CORRECT | 3.45 | 3.45 | DRAWING-CONFIRMED | + 0.345 m2 HELD beside |
| L-60fc97c4306696c74c38 | B7-06 lm | SITE-d7254c68fd33723d:F2 (2F) | MS2-U | OWN | CORRECT | 11.5 | 12.65 | DRAWING-CONFIRMED | - |
| L-1dac5d9b574d7608d80d | B7-02 m2 | SITE-735e111dcf9b22c8:F4 (GF) | RS-A | PARTIAL | CORRECT | 1.035 | 1.38 | DRAWING-CONFIRMED | - |
| L-f145a2d130cba9450a24 | B7-06 lm | SITE-735e111dcf9b22c8:F4 (GF) | RS-A | PARTIAL | CORRECT | 3.45 | 4.6 | DRAWING-CONFIRMED | - |
| L-fa534ec5f9dc14947899 | B7-02 m2 | SITE-735e111dcf9b22c8:F1 (GF) | RS-C | OWN | HOLD | 4.094413 | HELD blank | HELD | beside 4.094413; governing count 12 |
| L-95b9555dd144951b071e | B7-06 lm | SITE-735e111dcf9b22c8:F1 (GF) | RS-C | OWN | HOLD | 13.7964 | HELD blank | HELD | beside 13.7964; governing count 12 |
| L-89c84fdd4964dec8a323 | B7-02 m2 | SITE-735e111dcf9b22c8:F2 (GF) | RS-S | PARTIAL | CORRECT | 2.07 | 3.45 | DRAWING-CONFIRMED | - |
| L-59354cfe423b026db61a | B7-06 lm | SITE-735e111dcf9b22c8:F2 (GF) | RS-S | PARTIAL | CORRECT | 6.9 | 11.5 | DRAWING-CONFIRMED | - |
| L-0ec429f1783f1f15e700 | B7-02 m2 | SITE-735e111dcf9b22c8:F3 (GF) | RS-S | PARTIAL | SUPERSEDE | 1.035 | listed, no qty | NOT_APPLICABLE | owned by L-89c84fdd4964dec8a323 (FOLDED) |
| L-fef9ec154deaec502498 | B7-06 lm | SITE-735e111dcf9b22c8:F3 (GF) | RS-S | PARTIAL | SUPERSEDE | 3.45 | listed, no qty | NOT_APPLICABLE | owned by L-59354cfe423b026db61a (FOLDED) |
| L-7adf1ccd0c407b61221a | B7-03 m2 | SITE-d7254c68fd33723d:F1 (2F) | MS2-L | SEEN_THROUGH | SUPERSEDE | HELD blank | listed, no qty | NOT_APPLICABLE | owned by L-0f060e9951c28c4cf074 (DOUBLE_COUNT) |
| L-820baecf7f726b4d8f1e | B7-03 m2 | SITE-a95bf979baf4cfae:F5 (1F) | MS1-T | SEEN_THROUGH | HOLD | HELD blank | HELD blank | HELD | governing count 5 |

KEEP (asserted unchanged, 11 lines): D1 GF F2 tread / step 1.035 / 3.450; MS2-L 1F F2 tread / step 3.795 / 12.650 (VERIFIED carrier) and its riser L-0f060e9951c28c4cf074 (BLOCKED_RFI, owner of the superseded 2F riser); the six BOUNDED_EXPOSURE 1F readings of RS-C / RS-S / RS-A (not valued before or after).

## 3. Reconciliation in units (ERS s.2.4)

B7-02 valued 27.324413 -> 20.010 m2 (-7.314413 m2, -26.8 %):
- double count removed -3.450 (MS2-L read again on 2F; the 1F reading 3.795 stays the carrier, VERIFIED);
- held by name -5.589413 (RS-C 4.094413 + MS1-T 1.495; beside, never 0);
- folded -1.035 (RS-S GF F3, a partial reading) and its flight carrier RS-S GF F2 +1.380 (2.070 -> 3.450 = 10 drawn);
- treads not read +0.690 (MS1-L, 7 -> 9) +0.345 (MS1-U, 10 -> 11) +0.345 (RS-A, 3 -> 4);
- MS2-U 3.450 unchanged in m2 (10 valued) with the 11th tread 0.345 m2 HELD beside (going drawn on no sheet).
Check: 27.324413 - 3.450 - 5.589413 - 1.035 + 1.380 + 0.690 + 0.345 + 0.345 = 20.010.

B7-06 valued 91.0279 -> 67.850 lm (-23.1779 lm): double -11.500, held -18.5779 (13.7964 + 4.7815), folded -3.450 with
the RS-S carrier +4.600 (6.900 -> 11.500), unread +2.300 (MS1-L) +1.150 (MS1-U) +1.150 (MS2-U, its 11th front drawn)
+1.150 (RS-A). Check: 91.0279 - 11.5 - 18.5779 - 3.45 + 4.6 + 2.3 + 1.15 + 1.15 + 1.15 = 67.850.

Hand check of the carriers (drawn fronts x 0.300 x 1.150 = 0.345 m2 per tread; x 1.150 lm per step): MS1-L 9 -> 3.105 /
10.350; MS1-U 11 -> 3.795 / 12.650; MS2-L 11 -> 3.795 / 12.650; MS2-U 10 valued (+1 held) -> 3.450 / 11 -> 12.650; D1 3
-> 1.035 / 3.450; RS-S 10 -> 3.450 / 11.500; RS-A 4 -> 1.380 / 4.600. Sum 20.010 m2 / 67.850 lm.

## 4. The two acceptance items that differ from the row text (stated with their cause)

- **MS1-T beside figures.** The row asks for '4.144 lm / 1.495 m2 beside'. 1.495 m2 is the T-434 drawn region (1.150 x
  1.200 + 0.100 x 1.150, invariant to the subdivision) and equals the candidate's own figure: carried. 4.144 lm
  (T-434 `winder_fronts.beside_lm` 4.14365) is the length of the three DRAWN winder fronts: a B7-05 nosing basis, not
  a step count. The B7-06 line therefore carries BOTH beside, each labelled: 4.7815 lm (the candidate's own reading, 4
  radial treads, ENGINE_WRONG -1 piece against the governing 5) and 4.14365 lm (drawn winder fronts, nosing basis).
  Neither is valued; the governing count 5 is on every MS1-T line (tread, step, riser). No number is picked.
- **Landing nosing ST01-MS1T-N05 1.150 lm (iii).** There is no B7-05 line in V3.0.38 (registry 1.33.0: B7-05
  NOT_IN_CANDIDATE); B7-05 enters with T-424. Its DRAWING-CONFIRMED status (T-434) is recorded in this version's
  WAITING note `T429_NOSING_BINDS_HERE` so that T-424 binds its nosing lines to this tread set; no line can move here.

## 5. Rule and check (R-T429-1, module docstring; every villa)

ONE physical flight, ONE valued tread line and ONE valued step line. (a) Cross-plan class by LEVEL (F-C-T425-1): two
readings on different plans whose flights span the same levels are the same flight (SEEN_THROUGH): one valued, the other
SUPERSEDED; a repeat is STACKED (a new flight) only when its level span differs (`level_class`: MS2-L 1F +5.50 ->
+7.516 vs 2F the same span = SEEN_THROUGH; MS2-U +7.684 -> +9.70 over MS1-U +3.50 -> +5.50 = STACKED, both valued).
(b) The carrier's count = drawn fronts on both layers, never lines - 1; step lm = drawn count x width and tread m2 =
valued treads x going x width are asserted on the inputs. (c) A held flight is never valued in any reading. (d) Held
never 0. `check_flights()` runs on the integrated lines (superseded = no quantity and owned by a valued line of its
code; held = blank with its reason; per flight and code at most one valued line).

## 6. Diffs and regression

- vs V3.0.38: **4,829 -> 4,829 lines; 0 ADDED, 20 CHANGED (all named in section 2), 4,809
  byte-identical** (asserted in `integrate()` and `write()`; outside-rows sha256 `951db386876cbc1d..` in the summary). Totals moved
  only in FIN.MARBLE.TREAD, FIN.STAIR.STEP_LM and FIN.MARBLE.RISER (asserted):

| Code / unit | V3.0.38 valued (lines) | V3.0.39 valued (lines) | Held blank | Listed, no qty | Bounded (unchanged) |
|---|---|---|---|---|---|
| FIN.MARBLE.TREAD m2 | 30.683813 (12) | 23.3694 (8) | 2 | 2 | 0 .. 8.924413 (3) |
| FIN.STAIR.STEP_LM lm | 91.0279 (11) | 67.850 (7) | 2 | 2 | 0 .. 29.8964 (3) |
| FIN.MARBLE.RISER m2 | 1.96 (1, E1) | 1.96 (1, E1) | 13 | 1 | - |

  The FIN.MARBLE.TREAD code total includes the separate E1 line L-314c3ac6d45431b687c5 3.3594 m2 (unchanged; T-425 s.3.2
  AGREE): over the 14 flight readings B7-02 is 27.324413 -> **20.010 m2** and B7-06 91.0279 -> **67.850 lm**, the
  acceptance figures exactly.
- vs released V2.9 + route G: every one of the 20 changed lines exists in V2.9 with its V3.0.38 figure (the stair lines
  were base lines); after this package they differ from V2.9 (QUANTITY_DIFFERS). Whole file: {'NOT_IN_RELEASED': 3239, 'QUANTITY_DIFFERS': 976, 'SAME_QUANTITY': 614}.
- Older chain guards: every V3.0.14 .. V3.0.38 guard (`_family_guards`, roof, ceilings, corrections, zones, fence, lists,
  beds, lift, landing) runs unchanged on the V3.0.39 lines and passes; `check_flights()` (new): corrected 10, superseded 5,
  held 5, one valued tread and one valued step line per flight (7 flights valued).
- T-330 deductions check (`tools/t330_deductions_check.py`, unchanged): V3.0.38 4,829 lines 6 FLAG (5 EMPTY, 1
  NOT_SUMMING) / 0 REFUSED -> V3.0.39 the same 6 / 0: no new finding (the corrected lines carry gross = net).
- Export (`tools/boq_export_v1.py`, unchanged) on V3.0.39: 4,829 rows; carriers MEASURED UNVERIFIED; MS1-T and RS-C HELD
  with the reason, blank; 2F F1 and RS-S F3 EXCLUDED with the SUPERSEDED reason (listed, no quantity); nothing shown as 0.
- Tests: `tests/t429_tread_binding_integration` (hand villa K429, not Alsenan: 25 method tests + 6 registry tests); L3
  folders and the whole-repo guards (handoff); L4 full suite on the final commit compared id by id with the working
  branch (handoff).

## 7. Missing / held (never 0)

- MS1-T winder turn: tread 1.495 m2, step 4.7815 lm (candidate) / 4.14365 lm (drawn fronts), riser: HELD, governing count
  5 (designer: plan subdivision of the 5 winders, C-ST-3).
- RS-C curved part 4.094413 m2 / 13.7964 lm HELD (Q-50 A cond; RFI-S27).
- MS2-U 11th tread m2 0.345 HELD beside (the 2F floor edge position: designer).
- Every riser line (B7-03) stays BLOCKED_RFI (riser height basis); none valued before or after.
- NOT done here, named for the Lead: the FIN.STAIR.FLIGHT line of the 2F F1 reading (L-0c2df36a42803126d3b9, BLOCKED_RFI,
  no figure) and of the RS-S GF F3 reading (L-d827589991777fe63819), and the RS-S GF F3 riser line
  (L-2efa4a4f4cc2aad9a2f2), are readings of the same SEEN_THROUGH / PARTIAL flights; they carry no figure today, so no
  quantity is at stake, but by R-T425-1 they should take the same disposition before any of them is valued. Not in the
  Checker's verdicts: left unchanged.
- ST-02 straight-part drawing conflict (T-432 / T-438): not settled here; no RS-S / RS-A line moved on it.

## 8. Engine vs freelancer (quantities only; T-425 s.4, T-434; workbooks not re-opened)

| Family | Engine V3.0.38 | Engine V3.0.39 | Freelancer | Verdict proposal |
|---|---|---|---|---|
| B7-02 tread marble | 27.324 m2 (MS2-L twice, held flights valued) | 20.010 m2 valued + 5.589 m2 HELD beside + 0.345 HELD | no m2 row (ST-01 63 pieces x 1.20) | not comparable by figure |
| B7-06 steps (ST-01 pieces) | 4 readings of the main stair incl. MS2-L twice | drawn 56 risers ST-01 (Q-46 A), valued treads per flight | 63 pieces | ENGINE_RIGHT 56 / RULE_DIFFERENCE +7 (storey height / 150 .. 155 mm riser estimate, T-425 s.4; cause not proven) |
| B7-06 width | 1.150 drawn | 1.150 | 1.20 | ENGINE_RIGHT (T-412) |

## 9. Lessons row (proposed, ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | wiring a verified tread binding into the candidate could have left the seen-through 2F reading's riser line free to be valued later, or valued a held winder turn through its step line while the tread line was held | the binding was verified per tread line; the step and riser lines of the same reading were separate engine lines with their own state | one reading, one disposition across B7-02 / B7-06 / B7-03; a flight's class decided by its level span (any villa) | tests/t429_tread_binding_integration (normal: K429 hand figures, seen-through listed and owned, held blank with beside, undrawn going held beside, level test both ways, only named lines change, order invariance, files; adverse: the same flight valued on two plans, seen-through as carrier, held as 0, held flight valued, mm width, mm levels, step not count x width, lines - 1 count, unknown flight, zero treads, stale binding, wrong flight id, applied twice, carrier of another flight, superseded with quantity, two valued readings, change outside own codes) | proposed |

## 10. Gate B hand-check list (always by hand)

1. Every moved line (all are B7, at least 5 % moved or new disposition): MS1-L 3.105 / 10.350 (9 fronts DC .. C5 at 0.300,
   P7757.dxf; Checker T-425 re-measured); MS2-L 1F 3.795 / 12.650 carrier and 2F 3.450 / 11.500 SUPERSEDED (1387 .. 135F
   = AC0 .. A97 after dx -44.852655); MS1-U 11 fronts A92 .. ABE (ABE's going on ST p.4); MS2-U 11 fronts 135B .. 1386;
   RS-S 10 (1F B43 .. B4D); RS-A 4 (1F B59 .. D22).
2. Held: MS1-T (section A-A 5 winders, sheet 10), RS-C (Q-50 A cond): blank, beside figures as listed.
3. Totals: 20.010 m2 / 67.850 lm (section 3 arithmetic).
4. Riser lines L-7adf1ccd0c407b61221a (SUPERSEDED, owned by L-0f060e9951c28c4cf074) and L-820baecf7f726b4d8f1e (HELD).
5. Random lines: Checker's own selection (WORKFLOW_CONTROLS s.1.2) from the remaining lines.
