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

8. **Hand results that cannot reach a branch** (new 14:20): T-107's evidence was refused when written to a task branch
   ("[Sensitive-Source Provenance]"), so its handoff exists only as board text; worker 3's 12:59 run left no line and no
   commit. Decision: board-only handoffs are verified as hand evidence (the verifier re-reads the cited notes), and the
   next task on the topic writes the files (T-117); a run with no line stays a NEEDS FIXING item for the owner's setting.

## 2026-10-21 20:20 (lead run)

- **Checker back (recurring cause 4 closed for now)**: 15:51 and 17:52 runs SUCCESS on the repo-attached setup; 5 merged
  (T-145, T-133 Gate B, T-153, T-141, T-148), 3 rejected with exact gates (T-130 r2, T-139, T-119). Decision: queue for
  3 more runs (note on BOARD.md 20:20); every READY tag now CAPACITY, not CHECKER-RUNS.
- **T-133 V3.0.1 integration package: WORKED (MERGED PARTIAL, Gate B)**: first verified change through the integrated
  candidate: columns above necks 36.714 -> 34.446 m3 (5 undrawn pieces 2.268 m3, re-confirmed by hand), blinding 22.155
  -> 15.179 m3 released in the candidate (hand 15.213, -0.2 %) with ground-beam / strap blinding HELD. Day-7 target met
  6 days early. Went wrong: D1 runners omit --profile, D2 storey summary 1.428 m3 short of the lines, D3 two held lower
  bounds 10 / 15 % over hand. Decision: D1-D3 added to T-142 (lane I, now TODO, backlog-permitted).
- **T-153 floor area: WORKED (MERGED)**: dewaneya re-measured 0.0 %; north court strip 21.021 vs 21.348 m2 (+1.6 %) and a
  0.37 m2 duct outline not addressed. Decision: added to T-157 (still not backlog-permitted).
- **T-141 span splitter V2 and T-148 column steel: WORKED (MERGED)**; steel lines of the 5 undrawn columns STALE until
  T-151 (queued after T-142 / T-146, same candidate file).
- **T-139 slabs: PARTIAL (REJECTED on text only)**: quantities checked (3 panels 0.0 / 0.05 / 0.0 %); verbatim note text
  and a wrong page. 1F 0.37 m2 UNRESOLVED against his 120.00 m2 lump (about 0.06 m3) and a dome-ring double count in the
  beam register. Decision: text rework by worker 1; new T-160 (S) for the ring and the 0.37 m2 (drawing search first, no
  owner question below 0.5 % unless a rule gap appears).
- **T-119 columns: FAILED then reworked (READY r2)**: rejected for releasing 2F C2 / C3 on an unprinted reading; r2 holds
  them 3.00 .. 3.80 m and adds B19. Decision: checker run A first (critical); D-44 text corrected.
- **T-130 registry: REJECTED r2, READY r3**: 99 of 170 citations failed in r2, all fixed; footings PARTIAL. Decision:
  checker run A (unblocks the census T-140).
- **T-149 beam steel: WORKED (READY)**: 5,171.03 kg net; links Q-71; laps HELD; found 5 spans over end columns and CB7 = 2
  spans. Decision: feeds T-160.
- **T-150 doors / windows: PARTIAL by design (READY)**: counts agree (29 windows, 5 ALU doors), heights are the gap;
  windows +3.3 % on the 8 printed. No-assumptions finding: W16 'INFERRED' has no rule, must be HELD; door 2.20 vs 2.40 is
  RULE_DIFFERENCE (Q-55 C), not UNRESOLVED. Decision: note to the checker in the row.
- **T-156 Gate B tool: WORKED (READY)**; its proposal to draw random lines only from quantity lines changes an
  owner-approved control: put to the owner as a proposal, approved rule kept meanwhile.
- **Worker 2 19:48 NO-CLAIM**: correct (only non-permitted lane A rows); it refreshed six READY branches onto the working
  head (useful backlog work). Decision: T-159 (owner request) and T-158 now give lane A permitted work.
- New recurring cause: **SessionStart hook does not run** in repo-attached sessions (checker 16:52, 18:08, worker 2 19:48,
  worker 3 19:48, this Lead run): every agent runs setup by hand and it works, so no loss; reported to the main chat as
  a low-priority fix.

## 2026-10-21 16:20 (lead run)

- **Setup case bug (recurring cause, FIXED by the main chat 15:30)**: the repo-attached checkout has a lower-case origin
  URL and `agent_env.sh check_repo` matched case-sensitively, so the checker 13:55 and worker 1 14:27 were BLOCKED and
  worker 3 15:02 could run no repo code (it fell back to a hand task, correctly). Main 1c559a8 fixes it; this Lead run used
  the attached checkout and the wrapper (setup, board log) with no refusal. Decision: no task; watch the checker's 15:51
  run and worker 1's 16:19 run as the first runs after the fix.
- **T-134 element register v0**: WORKED. 652 elements, 1,504 of 1,530 lines linked, 26 UNLINKED with reason, 0 double
  finishes / concrete, 13 tests, 6 mutations caught. Wrong / missing: 6 CONFLICT elements (1.960 m3 footing, 5 beams 5.022 m3
  + 685.225 kg) are released by a route convention that no owner rule names; the 1F arrival landing has no outline.
  Decision: Lead ruling in ELEMENT_REGISTER.md (structure owns them, CONFLICT; if the checker finds no owner rule behind
  the convention, lane I holds them in the next V3.0 package); landing outline stays with T-133b. No new task yet.
- **T-153 floor area room by room**: PARTIAL by design. Interior floor 376.86 .. 376.98 m2, wet 85.62 vs 72.01 (+13.61 =
  pantry, Q-37 A), dry like for like 337.18 vs 337.57 m2 (-0.12 %); 11 held labels settled as EXTERIOR with area. Wrong:
  V2.9 counts the side passage as internal (engine defect); garden band 13.986 m2 CONFLICT; courts 167.714 vs his yard
  151.80 UNRESOLVED. Decision: worker proposal P-1 = existing OQ-04, re-asked with the numbers (no new Q- id); P-2 is a
  drawing conflict, so designer D-48, not an owner question; follow-up T-157 (classification from sections / elevations,
  not backlog-permitted).
- **T-154 pool-court soffit reconciliation**: WORKED. Re-add to 0.0000 m2; the 0.088 m2 traced to a turned column face
  0.065, a strip inside the V2.9 outline 0.016 and rounding 0.008; opening heads 0.904 / 0.200, glazing reveal 0.561 and
  wall tops 0.276 measured by neither method (no double count). Decision: rulings in ELEMENT_REGISTER.md (the 14.704 m2
  CAD basis never feeds a ceiling line); the two court-wall openings added to T-150's scope.
- **T-155 Q-71 evidence**: WORKED (hand). "/m" = bars per metre is drawing-confirmed; the whole-bar rule is printed
  nowhere; A / B / C reproduced to 0.01 kg; A spaces bars wider than printed in 20 of 20 rows. Decision: facts added to
  Q-71, the option-B recommendation withdrawn there too (owner controls); FF legs HELD in the register.
- **Checker backlog (16 READY)**: every READY row tagged CHECKER-RUNS (T-133 also EVIDENCE); queue for 4 runs written with
  both gates; only T-149, T-150, T-156 backlog-permitted. New T-156 (lane I, Gate B automated checks) so the checker's
  Gate B work on integration packages is tooled before the next package arrives.

## 2026-10-21 12:20 (lead run)

- **Checker outage (recurring cause, now the first one)**: FAILED as a team function. No verdict, merge or RUN_LOG line
  since 05:07; the checker's 05:49, 06:49, 07:49, 09:50 and 11:50 runs left nothing (11:50 ended after about 2 minutes,
  before even the STARTED line, the same signature as the refused clones of this morning). 12 results wait; the working
  head is still 0dec24c; worker 3's 10:59 run left nothing either (about 1.5 minutes). Decision: queue re-ordered (slabs
  and slab leftovers checked together; candidate first after the registry); hand-only tasks only for lanes S / A so a
  checker that can run no code can still verify by re-reading; the fix (Test B, the repo-attached configuration) is the
  owner's and is in NEEDS FIXING again.
- **T-144 openings for finishes**: WORKED (pending the checker). 79 opening faces with sheet and reading; 9 openings print
  sill and head, 3 readings corrected by closing each dimension chain on its printed total (W14 sill +6.90, W17 crown
  3.50, W15 sill 0.00); nets re-add to the plaster / paint table: drawing-derived dry net incl. the shaft 976.22 ..
  1,080.33 vs freelancer plaster net 1,151.14 m2 (-15.2 .. -6.2 %); 104.1 m2 of the range is the 24 unprinted opening
  faces. Went wrong: nothing; the range is the drawings' gap. Decision: designer D-45 (window schedule); no new task.
- **T-145 slab leftovers**: WORKED (pending the checker). CB5 span 2 is a beam (0.296 m3), beam register 64.764 ->
  65.060 vs 65.97 m3 (-1.4 %); the 13 non-slab faces 0.686 m3 re-add exactly; slab 60.280 vs 59.817 (+0.77 %);
  sunken-slab drop not printed anywhere -> HELD on D-41 (no default). Decision: the checker verifies it with T-139;
  lane I wiring stays T-146.
- **T-147 ceilings**: WORKED (pending the checker). A BOQ category that had no quantity now has one, room by room:
  decor ceiling 388.14 vs 409.58 m2 (-5.2 %), the whole GF difference = light well 23.24 + stair strips 2.45 (ENGINE_RIGHT
  proposal from two drawings); bulkheads 32.78 m2 (owner method) vs 175.76 m2 drawing-derived PROVISIONAL; paintable
  gypsum 420.92 vs his 452.33 (-6.9 %, +2.8 % without his coves). Held by drawing: wet-board type, coves, drops, domes.
  Decision: designer D-47; Kuwait spec 09200 stays in NEEDS FIXING; wiring after the checker (lane I).
- **T-148 column steel**: WORKED for the released part, PARTIAL by drawing (pending the checker). Net 1,887.13 kg
  released, 1,552.43 kg held by named cause, links 781 .. 829 kg on Q-71, laps on the note-9 range; freelancer gives one
  7.95 t lump (RULE_DIFFERENCE). Went wrong in the ENGINE (not the task): the frozen route releases 172.56 kg as
  VERIFIED on 3 planted columns from a duplicated schedule row. Decision: T-151 (lane I, queued) holds them in the
  candidate; designer D-46; the 2026-10-06 project-only "owner claims" the frozen route uses were NOT adopted (no
  assumptions) and are now evidence under Q-71 for the owner.
- **New tasks**: T-149 beam steel, T-152 slab steel (S); T-150 doors and windows, T-153 floor area (A); T-151 (I, queued).
  Recurring cause 2 (verified pieces not wired) is unchanged: nothing can be wired until the checker merges.

## 2026-10-21 08:20 (lead run)

- **T-119 columns to the controlling member**: WORKED (pending the checker). 59 columns by
  URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1: 28.816 .. 28.979 m3 vs engine 36.711 (-21.1 .. -21.5 %: 2.268 undrawn
  columns + 5.467 height basis) vs freelancer 28.547 (+0.9 .. +1.5 %). The 5.467 m3 is not lost: joints 4.264 + heads
  1.203 m3 must become their own lines (beams and slabs hold neither). Decision: after the merge, lane I wires columns
  + joint + head lines into the candidate (added to the T-142 / T-146 chain note); B15 upstand / downstand = designer
  D-44; column steel by bar population is the next rebar slice (T-148, lane S).
- **T-125 masonry centreline V2**: WORKED (pending the checker). Run length GF 134.563 / 1F 120.335 / 2F 39.600 m vs hand
  143.160 / 120.753 / 39.775 (GF -6.0 %, -1.3 % with the 6.726 m pool glazed line beside it); the two big V1 causes
  (+14.13 / +2.50 m of non-wall) are gone; 62 tests, L4 0 new failures. Open: 45 deg holds 0.842 m, bay arc 3.747 vs
  3.673, pool glass 6.726 (DXF) vs 4.95 (hand chord): the checker settles; designer item if it stays. Decision: wiring
  waits for the T-143 hand truth and the checker (T-108).
- **T-130 r2 coverage registry 1.1.0**: WORKED (pending the checker). Every named fault of the 02:30 rejection fixed with
  file:line; INTEGRATED_AND_TESTED 3 -> 1 (footings), PARTIAL 42 -> 46, IMPLEMENTED_NOT_INTEGRATED 11 -> 13,
  NOT_IMPLEMENTED 22 -> 18; L4 0 new failures. The merge into its old branch was refused ('[Untrusted Code
  Integration]'), the worker re-applied on a fresh branch (allowed fallback). Decision: first in the verifier queue
  (it unblocks the census T-140).
- **T-133 candidate V3.0.1**: PARTIAL. Route G scope (columns 36.714 -> 34.446 m3, blinding 22.155 -> 15.179 m3 released +
  3 HELD lines) and the membrane audit are wired with a byte-identity test; but the worker's own run of the Drive
  DXFs was refused ('[Code from External]'), so the after-figures are the merged pieces' verified values, not a run of
  V3.0.1, and L4 ran only 1 of 12 chunks. Finish moves (landing / arrival) and stairs were not wired because they are
  hand ledgers with no reading piece. Decision: the checker must run research/agents_t133/v301_run.py on the Drive DXFs
  and the scoreboard on V3.0.1 vs V2.9 (gate 3 of its check), and complete L4; the hand-ledger pieces need a small
  reading piece each, which is the next lane I work after T-134 (noted on T-142).
- **T-141 ground-beam span splitter V2**: WORKED for ground beams (pending the checker). 52 of 53 spans equal the hand
  ledger within 0.3 mm; the three S5 defects fixed (9.50 -> 4.40 + 4.40 m etc.); ground-beam bottom steel 1,238.56 ->
  1,194.60 kg (-43.96 kg, -3.5 %). No-assumptions check: the worker held both strap lengths instead of choosing (right)
  but filed no question for the missing rule. Decision: owner Q-74 (strap length basis).
- **T-143 block area by hand**: PARTIAL by design. Gross 955.63 m2 measured vs freelancer 1,094.50 (-12.7 %); with held
  runs at candidate heights 1,036.5 .. 1,042.7 (-5.3 .. -4.7 %); m3 172.19; 214.36 m2 PROVISIONAL; net m2 HELD on every
  row (no Urban rule deducts openings from block) and the black count HELD (no black block size). Decision: owner
  Q-73 (opening deduction) and Q-75 (black block size, the owner's own 2025 sales order offered as option A); designer
  D-42 (1F walls under the dome openings), D-43 (lift tie beam size). The 12.7 % gap is mostly height basis (Q-60 A
  to the member above vs his storey heights) and the glass lines: the checker re-measures 5 walls.
- **T-134 element register v0**: FAILED to start: worker 3 claimed it at 08:00, then its push to agents/control was refused
  '[Untrusted Code Integration]' (BLOCKED; final line written by the main chat from the owner's relay). Decision: back to
  TODO, first in lane I (main chat released it at the owner's request; agreed).
- Recurring: (1) the verifier ran three times (05:49, 06:49, 07:49, the last 3.5 minutes) and left no line at all, not
  even the STARTED line, while 8 results wait; my own full clone at 08:11 was refused '[Untrusted Code Integration]' and
  the docs-only clone worked, so the likeliest cause is a refused first clone with no fallback (not proven). (2) Two
  rule gaps reached the board as "gap for the Lead" with no question filed: from now on the Lead files them the same
  run. (3) BOARD.md had grown back to 345 KB: cut to 130 KB (34 merged rows and old notes to the archive).

## 2026-10-21 06:30 (lead run)

- **T-138 r2 ground-beam / strap steel**: WORKED. MERGED 0dec24c (05:07); net 1,479.86 kg unchanged; development 40 d ..
  70 d (ST p.8 note 9) HELD 646.53 .. 1,194.51 kg; procurement laps on the two runs over 12 m HELD 18.20 .. 31.86 kg;
  checker re-measured both runs on the DXF (13.770 / 18.570 m). Freelancer 5.8 t / 9.75 t are lumps: RULE_DIFFERENCE, no %.
  Learned: route G prints ground-beam steel only under the typed ST7757 profile (58 lines, 3,526.92 kg); the default run
  has 59 UNRESOLVED and 0 kg. Decision: T-141 (span splitter V2) now has its hand check; the typed-profile dependence is
  already the gate-0 generality item (T-045 / T-024), not a new task.
- **T-139 slabs panel by panel**: WORKED (pending the checker). 62 panels 60.280 m3 vs engine 60.966 (+1.14 %) vs
  freelancer 59.817 (+0.77 %); every panel matches an engine face within 0.002 m2; the engine excess is 13 non-slab
  faces (0.686 m3); the held 2.740 m3 face settled as dome opening + ring (not slab). Open: CB5 span 2 (beam-register gap
  0.296 m3), sunken-slab drops (not printed), 1F +3.48 m2 UNRESOLVED. Decision: T-145 (S) for the leftovers, T-146 (I,
  queued) for "slab face released only with slab evidence", designer D-41; the checker decides the UNRESOLVED.
- **T-128 plaster / paint both methods**: WORKED (pending the checker), run without code (self-check refused "[Code from
  External]", NO REPO CODE row taken correctly). Dry gross owner GF 391.17 / 1F 375.03 / 2F 107.92 m2; drawing-derived
  440.30..451.45 / 424.30..435.48 / 122.09..125.31; whole house drawing-derived 1,150.62..1,177.59 vs freelancer 1,209.39
  gross (-4.9..-2.6 %). The difference between methods is +0.44..+0.54 m height everywhere (owner 0.60 beam allowance vs
  the 0.16 m slab). Gaps: shaft owner column (no rule), roof datum, 18 window heights, ceilings. No-assumptions check: the
  worker held the shaft owner column instead of inventing a height (right), but raised no question; a missing owner
  case is a question. Decision: owner Q-72 (today's package), designer D-39 / D-40, T-144 (window heights -> nets),
  T-147 (ceilings, Q-57 A mod, a missing category). Registry note for the coverage work: UP-GEN-003 1.1.0 still says the
  plaster / paint deduction is pending while UP-OPEN-SCHED-001 is approved (a stale status, not a rule conflict: the
  approved opening rule is the newer one); recorded here for the T-130 r2 / T-140 registry pass.
- Recurring: silent runs fell (2 of 7 finished slots without a line: worker 2 04:39, verifier 05:49) and code ran in
  5 of 6 logged runs; worker 3 05:00 was refused code again ("[Code from External]") but its 06:00 run passed.
  Decision: no board cause found (the verifier had two READY tasks waiting at 05:49); stays under NEEDS FIXING (P-01).

## 2026-10-21 04:10 (lead run)

- **T-131 r2 ARCH_TAKEOFF_V3.0 skeleton**: WORKED. MERGED b1a6d6d (02:30): 217 differing lines = 217 ledger rows, 1333
  byte-identical; candidate straps 3.390 vs 3.3925 m3 (-0.07 %). Decision: T-133 / T-134 claimable now; T-142 queued.
- **T-136 footing steel**: PARTIAL (by design). MERGED 6d532c5; 874.86 kg released, 2.74 .. 2.84 t HELD on Q-71
  (checker re-measured F2 76.73 / F6 92.05 kg). Decision: wiring in T-142; Q-71 stays today's owner package.
- **T-102 beam section cuts**: WORKED (recorded 02:10). MERGED a606124.
- **T-130 coverage registry 1.1.0**: FAILED the exactness gate. 3 families called NOT_IMPLEMENTED have merged, tested
  code (excavation, formwork, balcony membrane); lintels and slabs INTEGRATED without hand evidence. Cause: status
  derived from released-run output only, not from a code search. Decision: T-130 r2 with a test that no NOT_IMPLEMENTED
  family has an emitting module; T-140 waits for it.
- **T-137 membrane coverage proof**: WORKED. MERGED 18913db; checker hand cases 0.2500 / 0.52 m2 residues = prover.
  Learned: R-07's strip bound overstates by one; internal corners double-need 0.2066 / 0.4514 m2 (already counted as
  corner pieces). Decision: attach as evidence in T-142.
- **T-111 stairs ledger**: WORKED. MERGED c0e8443; main stair 5.011 -> 4.920 (owner basis) / 4.746 (drawn) vs 8.131 m3,
  ENGINE_RIGHT; found the slab under the winders in no line (0.230 .. 0.250, HELD). Gaps: roof-slab lines vs T 16
  landings not traced. Decision: stair figures into T-133 (g); landing trace added to T-139.
- **T-127 pool-court soffit**: WORKED. MERGED 5315d48; 12.834 m2 net = checker; five places 44.446 m2; freelancer pool
  ceiling 19.154 (+49.2 %) ENGINE_RIGHT; finish HELD (no note anywhere, Q-68 C). Decision: area lines in T-142.
- **T-138 ground-beam / strap steel**: PARTIAL -> REJECTED (no-assumptions gate). 1,479.86 kg confirmed; laps / development
  "HELD, no detail" although ST p.8 note 9 prints 70 d / 40 d; no procurement for runs > 12 m (18.57 m). Cause: the
  general notes page was not read for laps. Decision: T-138 r2 (range 40 d .. 70 d HELD, procurement line), then T-141
  (span splitter V2: three S5 defects, +3.7 % on released spans); R-10 to the scout.
- Recurring: silent runs (5 of 9 slots left no line, 2-4 min each; worker 3 three in a row, likely nothing claimable
  in lane I while T-133 / T-134 still read "waits for T-131"). Decision: lane I made claimable; owner setting stays
  under NEEDS FIXING.

## 2026-10-21 02:10 (lead run)

- **T-102 beam spans settled by printed section cuts**: WORKED. MERGED a606124 (verifier run started 01:49). Beam
  register 64.820 -> 66.733 vs freelancer 65.97 m3 (-1.7 % -> +1.2 %); C-C / D-D held (designer D-30). Not wired.
  Decision: wiring joins T-133 with the other beam pieces.
- **T-131 r2 V3.0 ledger**: WORKED (waits for the checker). The fault named at rejection is fixed: 217 lines differ from
  released V2.9 = 217 ledger rows, 0 undocumented, the other 1333 byte-identical; L4 364 = 364. No quantity change.
  Decision: first in the verifier order; T-133 / T-134 start from its merge.
- **T-130 coverage registry 1.1.0**: WORKED (waits). 99 families re-derived with file:line; 29 raised, 5 lowered. A
  second, independent worker-3 reading (by accident, see below) agrees on 90 of 99 statuses; the 9 disagreements are
  listed for the checker's spot-check. Census gap found (released upturn reported NOT_FOUND). Decision: new T-140.
- **T-136 footing steel by bar population**: PARTIAL (waits). Released 874.86 kg on 19 footings with printed counts
  (route G 50 mm practice cover gives -3.6 %; the drawing's 70 mm note 22 is right by hand); 2,742.51 .. 2,836.40 kg HELD:
  no Urban rule turns "n per metre" into a bar count. Rule check: every released value cites the rebar rule and note 22;
  the gap was asked (Q-71), not assumed. Decision: Q-71 is today's owner package; top-bar ends -> designer D-31; FN over
  F9 -> D-32; next slice T-138 (ground beams and straps by hand).
- **T-137 membrane coverage proof**: WORKED (waits). 688 layouts, 0 failed; residues are declared patches of equal m2;
  roll counts unchanged (wet 21, roofs 17 + 6 + 8). Learned: the R-07 band bound overstates by one strip; 43 of 109 V4
  wall frames self-intersect at a dome opening (no count change). Taken by worker 3 because no lane I task was claimable.
  Decision: no follow-up task now; the self-intersection is a note for whoever next touches V4 / V5.
- **T-111 stairs flight by flight + Q-62 ledger**: WORKED (waits; NO REPO CODE). Main stair 5.011 -> 4.920 vs 8.131 m3
  (-39.5 %, rule difference on his flight length); found an arrival wedge the code piece misses (0.030) and a slab under
  the winders carried by no line (0.230 .. 0.250 m3). Entrance and round stair verdicts proposed UNRESOLVED. Decision:
  winder slab -> T-139; asked the checker whether those verdicts need an owner question or a drawing (no question yet).
- **Worker 2 00:39, 01:39 and worker 3 01:59**: FAILED (no line, no commit; 1.5 - 2 min in the scheduler). Cause NOT
  KNOWN; worker 2 has not closed a run since 23:02 (23:41 was refused clone and claim push). Owner setting P-01.
- **Verifier 00:49**: BLOCKED: clone "[Untrusted Code Integration]", docs-only clone "Blocked by classifier"; it still
  logged through the connector. Its 01:49 run executes.
- **Lead mistake (00:15)**: released T-130 while the 23:00 worker-3 run was still alive (scheduler PENDING); the 00:00 run
  redid the task. Decision: the Lead checks the run state in the scheduler before releasing a claim.
- **Recurring**: unwired merged pieces (cause 1) still the reason no released number moved; V3.0 r2 is at the checker.

## 2026-10-21 00:15 (lead run)

- **T-105 concrete ledger V3 beams + stair concrete V1 (rework)**: WORKED. MERGED e74c182 (verifier run 47); firewall
  test passes, L4 364 = 364 vs base, 0 new. Beams 68.84 m3 released part vs freelancer 65.97 (+4.4 %), 18 pieces held;
  main stair 5.011 vs 8.131 m3 (RULE_DIFFERENCE). Rule check: Q-16 A, Q-19, Q-62 A cond cited; no assumed value. Not
  wired. Decision: wiring added to T-133 (d); T-136 (footing rebar) unblocked.
- **T-135 stair flight counted once**: WORKED. MERGED 05e2eab; checker re-measured the 2F east lane (10 x 0.30 x 1.15).
  Tread marble 27.324 -> 20.424 m2 + 0..3.450 held, steps 91.028 -> 68.028 + 0..11.500 lm. PARTIAL part: 2F west lane
  HELD (10 vs 11 treads, north end 0.300 m short). Decision: the west lane goes to T-111 (hand reading); wiring T-133 (e).
- **T-131 V3.0 skeleton**: PARTIAL (REJECTED, gate checker rule 4). Everything technical passed, straps re-measured by
  the checker (3.390 vs 3.3925 m3, -0.07 %), but the ledger covers 11 rows + 22 roll lines of 197 lines that differ from
  the released V2.9. Cause: the task asked for "before = V2.9 + V2.13" per line yet the identity test only checked
  V2.13. Decision: rework r2 on the same branch, top of lane I, acceptance = 0 undocumented lines vs V2.9.
- **T-102 beam section-cut binding**: READY, not yet checked (verifier run started 23:49). Handoff has the numbers
  (64.820 -> 66.733 vs 65.97 m3, -1.7 % -> +1.2 %; C-C / D-D held, designer D-30). No decision needed now.
- **T-130 coverage registry**: FAILED (no output). Worker 3 claimed it 23:01, the run left no final line and no branch.
  Cause NOT KNOWN (third silent worker-3 run in a row: 21:59, 22:59). Decision: released to TODO after T-131 r2.
- **T-127 claim (worker 2, 23:39)**: FAILED (BLOCKED) by the platform: clone refused "[Code from External]", the claim
  push refused "[Modify Shared Resources]" (the same run still pushed its STARTED and final lines). Owner setting P-01;
  row left TODO.
- **Scout R-06 / R-07 / R-08**: answered. R-07 -> new T-137 (membrane coverage proof, shapely difference at 1 mm grid,
  residue = named patch or failure). R-08 -> exact area / thickness identity added to T-125's acceptance (no AGPL / GPL
  skeleton libraries). R-06 -> no task now: free Arabic OCR is not reliable enough to release a value (KITAB-Bench CER
  0.54 - 0.79); a closed-list, two-reader check stays the design of T-092 (QUEUED, gate 4); the Tesseract Arabic data
  needs an image change only the owner can make, not requested yet (no current task needs it).
- **Recurring**: (a) unwired merged pieces (cause 1) unchanged: still 0 released quantity moved; V3.0 is the only path
  and its rework is first. (b) Verifier wrote MERGED / REJECTED in the Branch column, so the board showed READY for
  merged rows: Lead corrected the statuses and left a note for the verifier. (c) silent runs: worker 1 22:19, worker 3
  22:59 (cause 4, owner setting).

## 2026-10-20 22:15 (lead run)

- **T-122 / T-123 / T-124 / T-110: WORKED (MERGED 21:05, verifier run 45, each re-measured on the Drive DXFs).** 1F
  landing 4.875 printed / 4.865 m2 drawn to marble once, porcelain 33.594 .. 33.711 HELD (hand 33.713); GF facade 98.887 vs
  hand 105.887 m (-6.6 %), passage 1.20 x 4.70 with the mouth open (Q-67 A condition met); membrane V5: no released or proven
  roll count changes; beam register 64.764 vs freelancer 65.97 m3 (-1.8 %) with B29 and B21 drawn-vs-schedule CONFLICTs
  confirmed. T-110 is PARTIAL on the beam line itself (HELD 4.123 .. 8.553 m3, 3 projection pieces, D-26..D-28). Decision:
  T-102 promoted (the two printed section cuts settle two spans); the rest stays with the designer list; T-122 joins V3.0.1
  (T-133).
- **T-126 route G scope (blinding by member, undrawn columns): WORKED (MERGED cd34bd0, run 46).** Columns 36.714 -> 34.446
  m3 (5 undrawn occurrences NOT_PRESENT, -2.268, ENGINE_RIGHT); blinding 22.155 -> 15.179 m3 released, and the checker's own
  union of the raw footing outlines gave the same 151.794 m2; held F10 0.480 .. 0.590, ground beams 5.724 .. 9.423, straps
  0.772. Freelancer's 47.055 whole-plot plate = RULE_DIFFERENCE. Decision: wire into V3.0.1 (T-133); column heights stay
  with T-119 (freelancer 28.547 is still -17 % on the height basis).
- **T-129 stair arrivals once: WORKED (MERGED 1513f1d, run 46).** 2F arrival 4.875 m2 marble (Q-70 A condition met: the
  195 is in the stair's own 1200 + 3300 + 1950 chain), 2F porcelain 2.500 not 3.900; front floor 7.375 vs freelancer 7.70
  (+4.4 %). Found a released defect: V2.9 counts the 1F -> 2F lower flight again on the 2F plan (+3.45 m2 tread marble,
  +11.5 lm steps). Decision: code task T-135 (lane A); the arrival joins V3.0.1 (T-133).
- **T-131 V3.0 skeleton: READY (33f1da2), awaits the checker.** 1519 of 1528 Alsenan lines byte-identical; straps 3.781 ->
  3.390 m3 (+11.5 % -> -0.07 %), GF facade 98.887 -> 105.887 lm under Q-67 A, 1F porcelain 44.869 -> 38.459 .. 38.979 range;
  L4 396 = 396. Decision: verifier checks it first; T-133 / T-134 build on it once merged.
- **T-105 beam ledger + stair rework: READY (7975663), awaits the checker.** Firewall declarations only; beams 68.84 vs
  65.97 m3 (+4.4 %, 18 spans held), main stair 5.011 vs 8.131 (RULE_DIFFERENCE). Decision: after it merges, T-136 (footing
  rebar) may take the same registry file.
- **Silent runs (recurring cause 4, new form): FAILED.** Worker 2 21:39 (1.5 min, no line, no commit) and worker 3 21:59
  (STARTED written, 9 min, no claim, no final line) although claimable TODO existed for both (T-127 / T-128 / T-125;
  T-130). Cause NOT KNOWN from the repository. Decision: no board change can fix it; P-01 (owner's Test B + repo-attached
  config) stays the fix; reported under NEEDS FIXING.

## 2026-10-20 20:10 (lead run)

- **T-120 membrane purchase version V2.13: WORKED (MERGED 2264938, verifier 17:49 run).** Opt-in candidate; the checker
  re-placed all 39 pieces of the 2F roof itself (17 rolls under Q-58 A, 0 overlaps), pantry 13.50 m2 / 2 rolls, wet 21.
  Released numbers unchanged by design. Decision: V2.13 is the base of the ONE consolidated candidate V3.0 (T-131, lane I);
  no V2.14.
- **T-121 ceilings over outside air: PARTIAL (REJECTED, gate d).** Census reproduced and the passage roofing confirmed,
  but the pool-court void was the route G face (4.373 m2), not the drawn opening (3.689 m2): PL-03 14.020 -> 14.704 m2,
  total 45.632 -> 46.316 m2; the gross 18.393 was never measured by hand. Cause: a CAD face used as the "hand check" (the
  same source twice). Decision: rework T-127 (lane A) with the hand gross from printed dimensions and the Q-68 C finish
  search.
- **T-122 1F living floor and landing under Q-66 B: WORKED pending the checker (READY f85fe97).** Porcelain 33.594 ..
  33.711 m2 (hand 33.713; corrected its own earlier 33.584 / 34.104), landing marble once 4.875, stair marble 44.365; the
  0.4025 m2 strip is marble in every reading. Every value cites Q-56 / Q-66. Decision: verifier order 1; Q-70 (answered A
  conditional) and the strip / D-23 -> T-129.
- **T-123 GF facade under Q-64 B / Q-67: WORKED pending the checker (READY 54425be).** Q-67 condition met on the drawings
  (nothing across the 1.20 m mouth, far end closed); billable stays 105.887 m until a reveal line holds the 0.100 m (then
  105.787); passage roofed 5.640 m2 (4.080 under 1F + 1.560 GF roof): confirms T-121, contradicts T-109's "open to sky".
  New finding: engine passage spaces leave out 0.480 m2 (two 0.20 strips at B5 / B1), cause not traced -> T-131 lists it
  as a held item. Decision: verifier order 2; then V3.0 carries perimeter / billable apart.
- **T-124 offcut booked once: WORKED pending the checker (READY a582f32).** New opt-in fold V5 books each leftover once;
  every released / proven Alsenan count VALID (wet 21, roofs 6 + 8, 2F 17); synthetic V3 claims corrected 1 -> 2 and
  8 -> 9; one unchosen V4 2F layout (19) held. Decision: verifier order 3; the audit joins V3.0 (no method V2.14).
- **Team: verifier silent twice (18:49, 19:49: 2-3 minute runs, no STARTED line, no commit) and worker 3 18:59 silent.**
  Cause NOT KNOWN (no transcript). Decision: READY order written on the board; the fix is the owner's repo-attached
  migration (P-01); reported under NEEDS FIXING.

Recurring cause 9 (new 20:10): **a CAD face checked against itself.** T-121's "hand" pool void was the engine's own face.
Every hand check must come from printed dimensions or a separate reading (checker rule 1 of the 20:10 decision).

## 2026-10-20 18:20 (lead run)

- **T-116 stair openings and wells out of room floors: WORKED (MERGED 559269, verifier 16:49 run).** Candidate 1F living
  porcelain 38.459 .. 38.979 m2 (hand 38.588 .. 38.990, freelancer 38.96 inside) vs released 44.869. Not wired. Your Q-66
  B (16:23) makes the 4.875 m2 landing marble, once: porcelain 33.584 .. 34.104, stair marble 44.365. Decision: T-122 (room
  rows with polygons, landing counted exactly once across floor, marble and void lines; your 17:54 condition), NO REPO CODE.
- **T-109 passage walls in the GF facade run: WORKED, then CONTRADICTED IN PART (MERGED 4fddf74).** Piece 105.887 m = hand;
  but T-121 reads the slab plans: the 1.556 m2 T-109 called "open to the sky" lies under the GF roof slab, so the passage
  is roofed full length with one open mouth; by T-109's own rule 5 the run would be HELD 98.887 .. 105.887. Is the passage
  outside? Your UP-SPACE-002 makes such a space POSSIBLY_EXTERIOR until a project decision: owner Q-67. Decision: T-123
  (perimeter 105.887 / billable 105.787 / reveal returns 0.100 apart per your Q-64 B and 17:54 (3); passage roof re-read).
- **T-117 wall run vs hand, run by run: WORKED (MERGED bc21314).** Engine 149.42 / 118.20 / 39.60 vs hand 143.16 / 120.75 /
  39.78 m: GF +4.4 % hides +16.63 m of bands across open floor and passage mouths and -10.37 m of misses; the piece is not
  ready to wire. Glazed lines 12.05 m are the whole GF hand-vs-freelancer gap. Decision: T-125 (MASONRY_CENTRELINE_V2) +
  owner Q-69 (glass lines in the run?); D-12 walls with columns stay CONFLICT for the designer.
- **T-120 membrane release version V2.13: PARTIAL (READY 17:46).** 33 tests, L4 no new failure, but Alsenan NOT run (Drive
  zip decode refused "[Untrusted Code Integration]"). Found: MEMBRANE_FOLD_V3's Q-58 A count can use one leftover twice.
  Decision: verifier runs the Alsenan script; stays a candidate (owner 17:54 (5)); T-124 audits every Q-58 A count
  (wet 19 / 21, roofs 8 + 6, 2F 17) for a leftover booked twice and builds a fold that books each leftover once.
- **T-121 slabs over outside air: WORKED by hand, pending verification (READY 18:07).** 5 places 45.632 m2 CALCULATED, the
  concrete above them is in the slab lines (5.304 m3, no omission); 31.612 m2 in neither BOQ; freelancer pool ceiling
  19.154 vs 14.020 net (+36.6 %, UNRESOLVED). Decision: owner Q-68 (soffit finish), verifier re-measures passage + pool court.
- **Team: 4 INCOMPLETE runs in this window (worker 1 16:19 and 17:19, worker 2 16:39, worker 3 17:59: 5-6 minutes, no line,
  no commit) and one silent verifier run that merged 3 tasks (16:49) without its board / log write.** Cause NOT KNOWN (no
  transcript). Decision: board rows corrected from the merge commits; the STARTED-line proposal of RUN_LEDGER.md (it
  changes agent instructions) needs your approval; NEEDS FIXING.

## 2026-10-20 16:20 (lead run)

- **T-114 2F roof trim proof and pantry cutting plan: WORKED (MERGED 8c23eea, verifier re-measured the roof on the DXF).**
  Under your Q-58 A the 0.70 x 6.97 m side trim covers the 0.30 x 4.60 m step band: 17 rolls PROVEN on the second-floor
  roof (strict layout 18), but only with strips stopping at the opening edge and 16 flap pieces from the same roof's roll
  ends; pantry 2 rolls, so wet areas 19 -> 21. Engine V2.12 shows 17 / 18 = hand. Went well: every piece dimensioned
  (254 rows), separate re-measure by the verifier. Wrong: nothing; the 0.05 m start offset it recommends has no rule (not
  adopted). Decision: T-120 builds the release version, opt-in until you confirm the reconciliation.
- **T-116 stair openings and stair wells out of a room floor: WORKED, pending verification (READY 15:20; verifier 15:52
  refused execution).** 1F living porcelain released 44.869 m2 -> 38.459 .. 38.979 m2 HELD range (hand 38.588 .. 38.990,
  freelancer 38.96 inside); each deducted piece = hand to 0.01 m2; winder-step defect (0.296 m2) fixed; 24 other floor
  lines unchanged. New small closed element 0.1175 m2 beside the round-stair arrival (designer D-23). Decision: verifier
  checks it first at the next run with execution; the landing finish stays on Q-66.
- **T-109 open-air passage walls in the GF facade run: WORKED, pending verification (READY 15:56).** New piece 105.887 m
  vs released 98.887 m (+7.000 m) = the verifier's hand; the two passage "openings" are not building openings (2 -> 0).
  New finding: the first floor covers 4.08 of the passage's 5.64 m2 (a bathroom and a bedroom corner over outside air):
  soffit and slab over open air not measured anywhere. Decision: T-121 (census of every slab over outside air, NO REPO
  CODE), missing-scope M-07; verifier checks T-109 after T-116.
- **T-107 block type per wall: verifier REJECTED 15:10 (part 1 not done, no branch).** The hand typing (white 141.31 /
  black 136.00 m ASSUMED, black 57.54 m by the note, 125.35 m held) is kept as hand evidence. Decision: already reworked
  as T-117 (claimed 16:01 by worker 3); T-108 now waits on T-117 instead of T-107. No new cause.
- **Worker 2 (two runs): FAILED / no line.** 14:39 run left no RUN_LOG line and no commit; 15:39 run: venv refused
  ("[Untrusted Code Integration]") and the claim commit refused, so T-117 stayed free (worker 3 took it). Verifier 15:49:
  venv, codemap and freeze refused ("[Code from External]"). Recurring cause 4 / 8 unchanged: 3 of 7 runs in this window
  could not run code. Decision: enough NO REPO CODE rows on the board (T-110, T-111, T-119, T-121); the owner setting stays
  under NEEDS FIXING.

## 2026-10-20 14:20 (lead run)

- **T-112 wall heights by both methods: WORKED (READY 9e10d0d, not verified; came in during this run).** 32 rooms. Owner
  method on 4 dry rooms with verified datums 234.17 vs freelancer 258.40 m2 (-9.4 %; same-wall rooms -1.5 %, his flat 3.40
  vs 3.35); annex 102.78 vs 117.00 m2 not releasable (Q-54 B: +4.30 reads as a finished roof); every drawing-derived height
  HELD (no ceiling plane printed). Where the owner line meets a deeper beam (GF open room / pantry 0.10 m into B26 / B27;
  wash lobby, 1F bed room 380 x 430, dewaneya at the beam soffit) it is a method difference reported to the owner, not
  decided. Decision: designer rows D-17..D-22; the owner sees the four beam places in the report (his reconciliation is
  pending); closed wall runs of 7 dry rooms become a task when the board has room.
- **T-100 blinding and columns by hand: WORKED, MERGED 5fe31ca (14:05).** Blinding hand range 20.71-26.37 m3, engine
  22.155 inside it; freelancer 47.055 = one 15.00 x 31.37 x 0.10 plate under the whole plot, drawn nowhere: -24.90 m3
  (-52.9 %) is his basis (ENGINE_RIGHT on basis). Columns at the storey interval 34.446 vs engine 36.711 (-6.2 %: engine
  counts 5 columns the roof-slab plans do not draw, +2.268 m3) vs freelancer 28.547 (his 3.75 / 3.45 heights). What went
  wrong: the handoff says no Urban rule covers column height; URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 does (interval
  minus the deepest member framing into that column). Decision: T-119 (columns by that rule, column by column; no owner
  question needed); T-101 acceptance adds F10 blinding HELD and the 5 undrawn columns NOT_PRESENT; the other two cases
  (blinding past the plot line 0.189 m3, strap blinding 0.913 m3) and C8 30X80 vs 30 x 90 are designer rows D-14..D-16.
- **T-113 1F living traced: WORKED, MERGED c1f0467 (14:05).** Engine 44.869 vs hand 38.588 m2 (+6.281, +16.3 %) explained
  to 0.0001 m2: stair-opening and stair-well residues 4.635, round-stair quarter landing 1.353, tread-clipping defect
  0.296; freelancer 38.96 = hand 38.990 (-0.1 %). Decision: T-116 (general fix, new piece); the 0.4025 m2 flight foot is
  designer D-13; the landing finish conflicts between owner Q-56 A (porcelain PROVISIONAL) and UP-STAIR-005 (landing
  marble) -> owner Q-66.
- **T-016b, T-014, T-027, T-104: WORKED, MERGED 13:25 (head 60f1d8d).** GF facade passage: verifier read the drawing,
  HAND_RIGHT (98.887 vs 105.887 m, -6.6 %); T-014's "GF established" withdrawn (both readers bridged the passage mouth by
  width alone). Decision: T-109 promoted to TODO; the 0.10 m notch is owner Q-64 (verifier), carried as a range.
- **T-106 skirting audit: WORKED (READY 696b29d, not verified).** All 28 nets right; 20 lines leave 17.035 m unlisted (the
  F-17 window-frame credit); same on the synthetic villas, so general. Engine gross 262.56 vs freelancer 282.85 m (-7.2 %),
  certain net 185.52 m: RULE_DIFFERENCE (he deducts no door; UP-CER-003). Decision: T-118 queued (listing fix after merge).
- **T-107 block type per wall: PARTIAL (READY, board-only).** No architectural sheet names a block type; structural notes
  do (neighbour-side ground beams black, walls with columns at column thickness). 93 runs typed: white ASSUMED 141.31 m,
  black ASSUMED 136.00 m, black PROVISIONAL 57.54 m, HELD 125.35 m; new scope M-05 (substructure black block 2 x 31.17 m).
  What went wrong: part 1 (code vs hand table) not done, freeze check and branch write refused. No-assumption check:
  fallback values marked ASSUMED, parapets / fence held and asked (Q-65): passes. Decision: T-117 (part 1, D-12 thickness
  conflicts, and the evidence files).

(Older entries trimmed by the Lead 18:20; the last 20 are kept.)
