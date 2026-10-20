# Feedback: what came back from each task and what the Lead decided (newest first, last 20 entries)

Lead writes after every run (owner, 2026-10-18). WORKED = met its acceptance check; PARTIAL = some parts held, refused
or only partly compared; FAILED = did not deliver. Recurring causes decide the next tasks and RESEARCH_REQUESTS.md.

## Recurring causes (lead 2026-10-20 10:20)

1. **Merged pieces not wired into the released run** (still the main reason released numbers do not move): beam fix,
   typed drawing values, plot-edge members, tile count, room levels / wall heights are merged but read by no released
   method; released concrete 92.77 vs 111.81 m3 unchanged since 2026-10-19. Decision: wiring chain T-105 (carries the
   rejected T-097 ledger V3 and T-056 stairs) -> T-101 (typed values, queued); plaster / paint T-095 after the owner's
   height answers (T-096 now merged).
7. **New modules trip whole-repo guard tests that the task's own tests do not run** (new 10:20): T-097 and T-056 both
   passed their own and L2 / L3 tests but each failed the rebar-firewall declaration test in the L4 suite (any engine
   module mentioning rebar / reinforcement must be declared). Decision: T-105 fixes both; every new-module task row from
   now on adds "run tests/structural_comparison_engine/test_rebar_product_firewall.py" to its acceptance check.
2. **A new ledger version inherits the holds of the one under it**: T-097 V3 carries the V2 holds (footing band Q-28 A
   provisional, pool), so its compared concrete shrinks to stairs + domes (12.01 vs 21.83 m3) and its released total over
   all keys drops 236.27 -> 229.57 m3 while beams rise +4.02 m3. Decision: every ledger handoff states released and held
   m3 per key against the RELEASED route, not only against the previous ledger; T-101 checks it.
3. **Drawings that contradict themselves block whole lines** (new, structural): 18 beam pieces (4.25 - 9.18 m3) keep the
   beam line uncompared. Decision: printed section cuts first (T-102), the rest to the owner (Q-61).
4. **Execution refusals at random** (unchanged): since 06:20, 3 of 6 code runs refused (worker 2 07:06 venv, 07:43 clone;
   verifier 07:58 install), one worker run left no line (worker 1 06:19). Decision: three READY tasks ordered for the next
   verifier run with execution; BOARD.md cut from 375 KB to 80 KB so a refused run can still claim or log through the
   connector; owner setting still under NEEDS FIXING.
5. **Trades never started**: blockwork (old estimate about 140 m short, -36.5 %) and blinding (22.16 vs 47.06 m3) had no
   task. Decision: T-027 + T-103 (blockwork, heights Q-60), T-100 (blinding by hand).
6. **Offcut reuse and heights still need rules**: Q-52 to Q-59 open (membrane 1 roll, tiles 15 - 20 %, plaster 1151.14 /
   paint 1191.13 m2 held).

## 2026-10-20 12:20 (lead run)

- **T-103 blockwork metres by hand: WORKED, MERGED 79bd397.** Hand centreline minus columns GF 143.16 / 1F 120.75 /
  2F 39.78 m vs freelancer 134.28 / 120.31 / 39.10 m = +6.6 / +0.4 / +1.7 % (the handoff gave -6.2 / -0.4 / -1.7 %, the
  opposite sign; corrected on the row, auditor 10:29). Parapets 108.55 vs 108.85 m; fence 46.37 vs 37.20 m (no sea-side
  row in his BOQ). No-assumption check: passes (block m2 / m3 HELD on Q-60, now answered A). Decision: T-107 (engine piece
  vs this table, block type per wall from the notes), T-108 queued (block m2 / m3 / counts).
- **T-099, T-016a, T-091: WORKED, MERGED 677c740 / aee6803 / 6319aca** (classified at 10:20; verifier reproduced the
  census and the OP-010 reading on the Drive DXF). Decision: none new.
- **T-027 masonry centreline piece: PARTIAL (READY 1c9cb52, NOT VERIFIED).** Synthetic villas = hand (SV-A 54.60 m vs
  the V2.9 face run 44.40, -18.7 %); Alsenan metres not measured: the DXF decode was refused "[PII Data Handling]".
  Cause: one refused step, not the method. Decision: the Alsenan acceptance line moves to T-107 (TODO, with a hand
  fallback); the verifier judges the piece on its fixtures.
- **T-016b V2.8 -> V2.9, 14 changes by hand: WORKED (READY 98cf0ec, NOT VERIFIED).** 12 VERIFIED, 2 CONTRADICTED: GF
  facade run engine 98.887 vs hand 105.787 m (-6.5 %: a 1.20 m open-air side passage at +0.15 is bridged, +7.000 m;
  a reveal pocket -0.100 m) and the 1F curved-window hold reason (sill on the 1F floor; source trail cites another
  window). Decision: verifier settles the passage first; T-109 queued; trail defect in Later.
- **T-014 facade gaps (FACADE_GAP_CLOSURE_V1): PARTIAL (READY 0ecef42, NOT VERIFIED).** 1F 63.169 -> 63.009 m
  (-0.160 m, -0.25 %) = hand = independent reader; 39 tests. But it disagrees with T-016b on the GF: its reader
  "establishes" 98.887 m and keeps the 0.10 m pocket, where T-016b's hand reading gives 105.787 m and -0.100 m. Cause:
  both readers walk the same drawn lines, so they share the passage blind spot (directive Part 4 (6)). Decision: the
  question is put on both rows for the verifier, who reads sheet 03 himself; no owner question (a drawing reading).
- **T-104 membrane strips in every wall frame (MEMBRANE_FOLD_V4): WORKED on the worker's evidence (READY 17f27d6,
  not verified).** Wedge W.C. 5.95 -> 5.45 m = hand; 17 wet areas 19 rolls unchanged, 122.55 m (hand 122.50); 2F roof
  HELD 17 / 18 unchanged; a V3 patch-sizing tail (+1 roll in one unused layout) corrected inside V4. Decision: verifier
  after the other three; wiring with the next ARCH_TAKEOFF version.
- **Verifier 11:53: FAILED to execute** (codemap check, pytest, freeze check refused "[Code from External]"; static review
  only). Second refused verifier run of three today. Decision: the three READY pieces are ordered for its next run; all
  six new TODO tasks allow hand work so refused runs still produce evidence.
- **Owner directive (Q-50..Q-63) and 12:15 correction.** Decision: questions moved to Answered; DECISION_REGISTER.md and
  DESIGNER_CLARIFICATIONS.md (designer list, missing scope, status mapping) written; new tasks T-110 to T-114 by the
  directive's priority, each naming its answer; T-095 and T-115 wait for the owner's reconciliation; nothing released
  changes.

Recurring cause 8 (new, 12:20): two readers agreeing is not proof when they walk the same lines (T-014 vs T-016b on the
GF facade). Decision: when a hand reading contradicts an "independent" code reader, the verifier reads the drawing itself
before either merges.

## 2026-10-20 10:20 (lead run)

- **T-096 membrane step-upturn fix (ARCH_TAKEOFF_V2.12): WORKED, MERGED 54bd6a4.** Verifier re-ran V2.11 vs V2.12 on the
  Drive DXF: 1 of 578 lines changed, 2F roof rolls 17 released -> HELD 17 / 18 (Q-58), wet 19 and 1F roofs 8 + 6
  unchanged. No-assumption check: passes. Decision: T-104 (wall frames) promoted to TODO on top of it.
- **T-098 wet-room cutting plans by hand: WORKED, MERGED 42123d8.** 19 rolls = engine; strip 122.50 vs 122.99 m (-0.4 %).
  Decision: none beyond T-104 (already tasked).
- **T-097 concrete ledger V3: FAILED the L4 gate (REJECTED).** Content as handed off (beams 68.84 vs freelancer 65.97 m3
  on the released part, 18 pieces held) but the new module trips the rebar-firewall declaration test. Cause: whole-repo
  guard not in the task's test set. Decision: rework T-105 (with T-056, same registry file); T-101 now after T-105.
- **T-056 stair concrete V1: FAILED the L4 gate (REJECTED), quantities confirmed.** Verifier's own hand calculation =
  main stair 5.011 m3 (freelancer 8.131, -38.4 %, RULE_DIFFERENCE). Same firewall cause. Decision: T-105, with a depth
  re-check of 3 acceptance cases (the original run took 11 minutes).
- **T-099 rooms that vanish (ROOM_CENSUS_GUARD_V1): WORKED on the worker's evidence (READY b631855, not verified).** 741
  faces each reported once; 0 Alsenan labelled faces under 1 m2 (freelancer's smallest rows 1.70 wet / 7.70 dry m2, so
  none lost there either); 3 unlabelled rooms 8.13 m2 HELD; hand-wash spaces 9.348 m2 typed wet vs freelancer 9.58 m2
  (-2.4 %). Learned: any face under about 0.81 m2 is typed WALL before the SLIVER test, so a labelled 0.80 m2 W.C. was
  invisible; now held. No-assumption check: passes. Decision: verifier first.
- **T-016a 10 old changes V2.6 -> V2.7.1: WORKED (READY 5ccb73b).** All 10 are one door record (1F OP-010, jamb span
  0.800 m), all VERIFIED by hand, ENGINE_RIGHT. New defect found: 20 of 28 V2.11 skirting lines list deductions that do
  not add back (17.035 m unexplained). Decision: T-106 (skirting deduction audit); T-016b (the 14 V2.8 -> V2.9 changes)
  with the worker's head start; T-014 promoted for the 1F facade +0.160 m and the GF 0.10 m pocket.
- **T-091 printed finishing-notes census: WORKED (READY b1dbb49).** Every sheet read (Pages_03-04 refused by the Drive
  connector as too large; the single sheets used): 0 printed tile sizes, finishes, skirting, ceilings, joints or door
  schedules; 1 door height. Findings: roof falls printed 1 % (owner said 0.5 %: told the owner, drawing precedence
  applies, no number moves); the freelancer's stair marble 295.44 m2 contains the 151.80 m2 court twice (his own
  formulas: stairs and landings alone 143.64 m2, and his step rows are metres added to m2); the freelancer's 1F living
  38.96 m2 = living 22.20 + corridor 7.04 + landing 4.88 + connector 4.80 (38.92). Decision: Q-56 rewritten with the
  printed pieces; Q-55 given the "not to scale" fact; the engine's extra 5.95 m2 on 1F to be traced in the T-086 wiring.
- **Runs with no RUN_LOG line**: worker 3 08:59 and worker 2 09:39 (2 min). Same pattern as the overnight silent runs
  (a run that stops on a permission card and times out). Decision: reported under NEEDS FIXING (owner setting), not new.

## 2026-10-20 08:20 (lead run)

- **T-056 stair concrete V1: WORKED on the worker's evidence (READY 3b8c549 at 08:13 after an 11-minute run; not
  verified).** Main stair 5.011 m3 = hand T-084 (steps 1.386 + waists 2.885 + landings 0.740) vs freelancer 8.131 (-38.4 %);
  entrance steps 0.357 vs 1.411 (waist HELD, not printed); round stair all HELD (Q-50 / Q-51); 15 named held lines, none 0;
  15 synthetic tests + L2 stairs. No-assumption check: passes; the worker found a rule conflict (last-riser wedge inside the
  arrival slab, 0.163 m3) and held it. Decision: owner Q-62; verifier fourth with a depth check (short run); wiring must
  replace the frozen S8.7 0.517 m3, not add to it (noted for the wiring task).
- **T-096 step-upturn fix, ARCH_TAKEOFF_V2.12: WORKED on the worker's evidence (READY 77e89d7, NOT VERIFIED: verifier
  07:58 refused).** 2F roof residual 0.84 -> 0 m2 with a 4.60 m upturn strip (= hand T-094 exactly); 2F roof rolls released
  17 -> HELD 17 / 18 under Q-58; 1F roofs 8 / 6 and wet 19 unchanged; 1 of 578 BOQ lines changed; 17 hand tests, L4 0 new
  failures, freeze 0. No-assumption check: passes (own-leftover piece held on the open question, not assumed). Decision:
  verifier checks it first; T-104 (wall frames) queued on top of it.
- **T-098 wet-room cutting plans by hand: WORKED (READY 017701c, not verified; CODEMAP not rebuilt).** 17 areas 19 rolls =
  released 19; strip 122.50 vs 122.99 m (-0.4 %); every unreached piece explained (45 deg corner triangles 0.0034 m2);
  one general gap: a wedge W.C. laid in its 45 deg frame needs 0.50 m less strip (same roll). Pantry with Q-37 A: 21 rolls
  with it. Decision: verifier second (rebuild the map with the tool); T-104 queued for the frame selection.
- **T-097 concrete ledger V3 (beam binding wired): PARTIAL (READY 8691838, not verified).** Beams released 64.82 -> 68.84
  vs freelancer 65.97 m3 (-1.7 % -> +4.4 %), +4.018 m3 each line by hand (T-085's +4.30 counted 0.281 twice); held beam
  spans 24 -> 18, so the beam key stays HELD; V3 inherits V2 holds (compared concrete only stairs + domes 12.01 vs 21.83 m3;
  released over all keys 236.27 -> 229.57 m3); 24 tests, L3 801 with the 7 known failures. No-assumption check: passes
  (unprinted upstand heights held, owner Q-44 A cited for rings). Decision: verifier third; T-102 (section cuts, 1.91 m3),
  owner Q-61 (the other 16 pieces, 4.25 - 9.18 m3 with them), T-101 queued (typed values on top of V3).
- **T-094 roof cutting plans by hand: WORKED (MERGED 027a168).** Hand truth 8 / 6 / 18 rolls; verifier re-checked the CSV.
- **T-064 typed drawing values file: WORKED (MERGED 8ceeeb2), not wired.** Decision: T-100 hand truth for blinding and
  columns first, then T-101.
- **T-073 plot-edge foundation members: WORKED (MERGED c874c7b), not wired.** Straps 3.390 vs freelancer 3.3925 m3
  (-0.07 %, ENGINE_RIGHT by the verifier on the Drive DXF); band 70.49 m free + 13.50 in footings + 7.95 in open outlines;
  natural-ground beam 3.526 vs 7.560 m3 (not explained yet). Decision: the NG beam difference goes into T-100's member
  list (blinding under it) and the ledger follow-up.
- **Worker 2 07:43: FAILED (NO-CLAIM, clone refused "[Untrusted Code Integration]").** Could not edit the 369 KB board
  through the connector. Decision: board cut to 80 KB (closed rows to BOARD_ARCHIVE.md); T-091 stays first NO REPO CODE
  row of gate 2.
- **Worker 1 06:19 run: no RUN_LOG line, no claim, no push** (the 07:20 run worked normally). Decision: reported in team
  health; nothing lost on the board.

## 2026-10-20 06:20 (lead run)

- **T-093 membrane rolls released, top roof held line: WORKED (MERGED 9f14742).** Wet 19 rolls = hand 19, roofs 31
  released, 2F top roof now a held line beside 204.11 m2 (-28.4 % vs 285.00); L4 0 new failures. No-assumption check:
  its own handoff flagged that the 2F roof's fully covering layouts need 18 rolls and took 17 "within its own leftover",
  i.e. it assumed a patch may come from leftover (no rule). Decision: T-096 holds that count under Q-58.
- **T-089 membrane cutting plan V1: PARTIAL (MERGED 64e3ea7).** Counts and lower bounds right where its strips cover the
  outline; wrong cause named for the 0.84 m2 ("slanted corners"). Decision: fixed in T-096 (new version), Q-58 corrected.
- **T-087 tile count with the owner joints: WORKED as a method (MERGED 8de2a21), PARTIAL on Alsenan.** 20 hand tests;
  every Alsenan room HELD (0 printed tile sizes in 276 DXF texts); offcut reuse moves 60x60 from 697 to 611 tiles.
  Decision: Q-59 (worker 1) relayed; T-091 census looks for printed sizes on the scans.
- **T-085 beam binding V2: WORKED (MERGED cb4a66f), not wired.** B26 3.905 / B27 3.787 m3 single spans, B7 0.255 = hand,
  upstands 0.240 = hand, ring beams 0.755 + 0.900 (Q-44 A); about +4.30 m3 once wired; 38 tests, L3 381 passed.
  Decision: T-097 wires it into concrete ledger V3 and measures the 24 hand spans.
- **T-094 roof cutting plans by hand: WORKED (READY ee35a2a, not merged: verifier's freeze check and merge refused).**
  1F west 8 = 8, 1F south-east 6 = 6, 2F 18 vs engine 17 (proven minimum 18), outlines checked on the DXF and the printed
  dimensions; found a released-count defect. Decision: verifier merges it first; fix T-096; Q-58 rewritten.
- **T-064 typed-values data file: WORKED on its own evidence (READY 8ab8d95, not yet verified).** 13 DRAWING-VERIFIED,
  1 INFERRED, 3 HELD; of 167 held concrete lines 66 (58.866 m3) rest only on drawing-verified values (blinding 22.155 vs
  47.055 m3, UNRESOLVED), 88 (44.438 m3) stay held. Decision: verifier second; wiring after T-097 merges.

## 2026-10-20 04:20 (lead run)

- **T-089 membrane cutting plan per wet room and roof: WORKED on its own evidence, NOT YET VERIFIED (READY b8738a5).**
  Alsenan 17 wet areas 19 rolls = hand 19; strips 122.99 vs 125.27 m (-1.8 %: same rolls, the opposite start wall in 4
  rooms, e.g. GF kitchen 15.30 vs 16.60 m, ENGINE_RIGHT proposal); pantry 2 = 2; roofs 17 + 6 + 8 = 31 = 31, 25.76 m
  left over; top roof HELD (Q-34); each count with a lower-bound proof (scout R-05). 22 hand tests not Alsenan. Freelancer
  has no roll lines: not comparable. No-assumption check: lap and roll are rule inputs (UP-WP-002), Q-49 A applied; the
  patch pieces were left out of the count and named as unruled: correct. Concern: 13-minute run for a new module with 22
  tests and an SVG output (depth check). Decision: verifier first on the next code-capable run with a hand re-derivation;
  owner Q-58 for the patches. No new task (cause already tasked: wiring T-093, T-095).
- **T-093 wiring rework: in progress (worker 1, claimed 03:20, branch pushed 9ead6fd, run still open at 04:10).** No
  decision until its handoff.

## 2026-10-20 02:10 (lead run)

- **T-079 wet areas / roofs wiring (V2.11): FAILED its acceptance (REJECTED gate d).** Sound otherwise: wet floor 72.12 vs
  72.01 m2 (+0.16 %, reproduced by the verifier on the Drive DXF), upturn walls-only 125.57 vs 144.61 lm (RULE_DIFFERENCE
  Q-35 C), roofs 204.11 m2 / 181.59 lm, 0 V2.10 lines changed. Wrong: rolls held on "Q-49 open" (Q-49 = A answered
  22:40: hand 19 wet / 21 with pantry / 31 roofs), and the 2F top roof (Q-34 held) has no line, hiding ~80.9 m2. No-
  assumption check: every released value cites a rule; the faults are under-application of answers, not assumptions.
  Decision: rework T-093 (first code task) with hand truth T-094 for the roofs.
- **T-081 r2 room levels V2 + owner wall rule: WORKED (MERGED d52b5dd).** 21 of 27 Alsenan rooms levelled (was 6), 6 held
  with reasons; owner heights GF 3.65 / 1F-2F 3.35 m as diagnostics; plaster / paint still held vs 1151.14 / 1191.13 m2
  (Q-52, Q-54). Verifier note: registry 1.8.0 is built on 1.5.0 and not registered. Decision: T-095 builds 1.9.0 = 1.7.0
  + 1.8.0 and registers it after T-093.
- **T-086 room-by-room finishing table: PARTIAL (MERGED 6002856).** Wet floors 72.12 vs 72.01 m2 (+0.16 %); 10 dry rooms
  194.98 vs 189.61 m2 (+2.83 %); stairs 39.49 m2 marble; materials PROVISIONAL (cement 80 - 111 bags, sand 10.91 - 15.21
  m3, adhesive 58 bags). Held: open-plan room, wet walls (Q-52), stair cement / sand (Q-53). UNRESOLVED: 1F living 44.87
  vs 38.96 m2 (+15.2 %: the face holds the corridor / landing, which he has in no row). Decision: owner Q-56 filed; T-091
  splits the room by printed sizes.
- **T-090 plaster / paint per room by hand: PARTIAL (MERGED 2fb9553).** 6 closed dry rooms: Q-52 A 336.94 / B 321.56 /
  C 331.49 vs freelancer 375.40 m2 (-10.2 / -14.3 / -11.7 %); same-wall 5 rooms -5.6 / -10.0 / -6.7 %. Found: opening
  deduction full band (UP-OPEN-SCHED-001) vs his half = RULE_DIFFERENCE; ceilings have no plaster / paint rule (his
  painted decor ceilings 452.33 m2); the old V1 plaster-termination method conflicts with the owner's 21:40 rule (owner
  governs). Decision: owner Q-57 (ceilings); supersession recorded in T-095; totals wait on Q-52 / Q-54 / Q-55.
- **T-091 printed-notes census: not started (worker 1 claim push refused 01:25).** Stays TODO for a refused run.

## 2026-10-20 00:30 (lead run)

- **T-083 opening heights by hand: PARTIAL (MERGED ce74b98).** Windows with printed heights 6 of 29 (was 4): 26.485 vs
  freelancer 24.280 m2 (+9.1 %); W13, W14, W15, W18 ENGINE_RIGHT on the printed heights, W17 RULE_DIFFERENCE (Q-39 C); a
  1F bath window printed 0.50 x 2.16 where he takes 0.60 x 0.80. Held: 23 windows (scans give no height), the curved pool
  glazing width (answered by Q-38 A, record fixed: 6.57 m), the 2F stair window (PDF / DXF conflict), every door but the
  main entrance. Decision: owner Q-55 (door height), T-091 (notes census), T-092 (scan reader, check-only).
- **T-088 room levels and wall heights by hand: PARTIAL (MERGED 41f7da7).** 30 of 32 room levels read; floor-to-floor GF 4.50,
  annex 4.00, 1F / 2F 4.20 from sections A-A and B-B; but no 0.60 m beam on any slab plan, so every room held: plaster and
  paint stay HELD. The 5 rooms with printed lengths give 282.67 m2 by option A vs freelancer 299.58 m2 (-5.6 %).
  Decision: owner Q-52 (asked by worker 2), owner Q-54 (annex), hand table T-090 for all rooms under each option.
- **T-084 stairs by hand: PARTIAL (MERGED ad1eb36).** With Q-46 A / Q-47 A the main stair is 5.011 m3 by hand (steps
  1.386 + waists 2.885 + landings 0.740) vs freelancer 8.131 m3 (-38.4 %); winders 0.120 m3 and the round stair
  (freelancer 5.510 m3) UNRESOLVED. Decision: owner Q-50 / Q-51 (verifier), T-056 updated to reproduce 5.011 m3.
- **T-075 schedule text rows: WORKED (MERGED b87f4d6).** 5 CN column lines held -> not present (freelancer 0, agree);
  6 necks 0.540 m2 section agree; height held (Q-21 C). Not wired. Decision: wiring with the concrete ledger later (gate 3).
- **T-079 wet areas / roofs wiring (V2.11): READY, NOT VERIFIED.** Worker 1: wet floor membrane 72.12 vs 72.01 m2
  (+0.16 %), upturn walls only 125.57 vs 144.61 lm (-13.2 %, rule difference), roofs 204.11 vs 285.00 m2 (-28.4 %, top roof
  held), rolls held on Q-49 at the time; L4 = base failures + 2 fixed. Decision: verifier first item next run.
- **T-081 r2 room levels V2: READY, NOT VERIFIED.** 21 of 27 rooms levelled (was 6); owner heights in registry 1.8.0 as
  diagnostics; annex held (no slab read). Decision: verifier after T-079; annex -> Q-54.
- **Scout answers R-01, R-02, R-05 (00:02): used.** R-01 -> T-092 (scan reader with an exact chain-sum check; Tesseract
  CLI already in the image, no OpenCV). R-05 -> notes on T-089 (FFD + L1 lower-bound proof, no OR-Tools install) and T-073
  (virtual_entities, edgeminer at 1e-6 m only; larger gaps HELD, no Urban gap rule). R-02 (SHX glyph sheet): not tasked
  now: it needs the client's own font file and no Alsenan quantity is blocked by an unread label today; revisit if one is.
- **T-086 room-by-room finishing table: PARTIAL (READY 00:14, worker 3).** Wet floors 72.12 vs 72.01 m2 (+0.16 %) + pantry
  13.50 m2; 10 dry rooms 194.98 vs 189.61 m2 (+2.83 %); open-plan room and wet walls HELD (Q-52; wall candidate 403.02 vs
  433.83 m2); stairs 39.49 m2 marble; PROVISIONAL materials (owner Q-45): mortar 11.16 - 15.07 m3, cement 80 - 111 bags,
  sand 10.91 - 15.21 m3, adhesive 58 bags. Stair cement / sand held correctly: no 1:3 figures -> owner Q-53 (worker 3).
  Decision: verifier third after T-079 and T-081 r2; wet walls released when Q-52 is answered.
- **Worker 2 run 23:40: NO-CLAIM (execution refused, no NO REPO CODE row free).** Decision: T-090 and T-091 added.

## 2026-10-19 22:20 (lead run)

- **T-043 beams by hand: WORKED.** Merged 6975158; verifier re-read the 5 released spans (3.691 m3) and 0.240 m3 upstands
  on the Drive DXF. Not wired. Decision: T-085 claimable; owner Q-44 = A adds the B4 ring beam per dome opening to T-085.
- **T-076 membrane fold V2: WORKED.** Merged 8884287. Strip method on 17 of 17 real wet areas (was 0 of 14); 33 of 34 hand
  layouts reproduced; walls-only upturn 125.57 vs freelancer 144.61 lm (-13.2 %, RULE_DIFFERENCE by Q-35 C); rolls 13 /
  14 / 15 by layout. Decision: T-079 TODO; the layout choice is an owner rule gap -> Q-49.
- **T-082 opening heights from PDF: PARTIAL.** Merged 2dee954. The reader works on vector PDFs (25 hand cases), but the
  Alsenan sheets are scans: windows still 4 of 29 (13.892 vs 14.350 m2, -3.2 %), doors 0 of 12.0 m2. Decision: T-083 hand
  table released for any worker; R-01 updated (OCR of scanned dimension text); plan reader stays gate 4.
- **T-081 room levels + finish heights V2: PARTIAL (REJECTED by the owner's new rule).** Room levels pass every gate;
  finish heights refused the build-up and decor depth that the owner's 21:40 rule now sets. Decision: rework on its
  branch (owner values as OWNER_RULE inputs, unmarked rooms by the Q-43 answer, per-room plaster / paint ranges) and
  T-088 hand truth; wet-wall height -> Q-48.
- **T-084 stairs by hand: PARTIAL (READY, NO REPO CODE).** Steps released 0.483 m3; main stair held on two drawing
  conflicts, which the owner answered (Q-46 A, Q-47 A): hand main stair 5.131 vs freelancer 8.131 m3 (-36.9 %, his
  flights 37 - 54 % longer than drawn). Decision: verifier applies the answers and merges; T-056 rewritten with them.
- **T-075 column schedule text rows: WORKED (READY).** 5 CN column lines HELD -> NOT_PRESENT (freelancer 0, agree); 6 CN
  necks 0.090 m2 each, height HELD (Q-21 C; freelancer 0.810 m3 at an unprinted 1.50 m, UNRESOLVED). All self-check PASS.
  Decision: verifier checks it first; no value from an assumption.
- **T-083 opening heights by hand: FAILED (no trace).** Claimed 20:42, nothing pushed. Decision: released to TODO.
- **Worker 3 runs 21:25 / 22:03: PARTIAL / NO-CLAIM (refused).** 21:25 delivered T-084 by hand; 22:03 found no NO REPO
  CODE row free and asked for one. Decision: T-088 and T-083 are NO REPO CODE rows now.
- **T-050: CLOSED** (superseded by T-058, merged 8774071).
