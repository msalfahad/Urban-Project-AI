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
   REPEATED 2026-10-22 17:00 (T-186 default_guard.py merged undeclared; fix T-190 with a known-failure register; the
   Checker's gate b now runs the firewall test for every new engine/ module).
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

9. **Usage-limit outages stop the whole team** (new 2026-10-28 20:20): no agent ran from 26 Oct 06:41 to 28 Oct 19:19
   (about 60.5 h); the scheduler records FAILED / USAGE_LIMIT_REACHED (Scout 27 Oct 23:50, Dashboard and Worker 3 28 Oct);
   two worker runs (26 Oct 06:24 / 06:40) died without a final line. READY work aged 62 h. Decision: owner item in
   NEEDS FIXING (cadence vs usage budget is his call: the hourly pilot was to be reviewed after 24 - 48 h on 25 Oct);
   R-11 to the Scout (documented cost / usage controls for scheduled routines); the stale-lock recovery worked as designed.

## 2026-10-29 00:15 (lead run; covers 2026-10-28 20:15 - 2026-10-29 00:15)

- T-244 (Gate B, plaster / paint at the merged opening outlines, V3.0.20) WORKED: candidate of record V3.0.20; 1F-11 released 59.4511 m2 ENGINE_WRONG -> HELD 61.4626 .. 61.7177; paint released 166.8792 -> 217.2081 m2; Checker reproduced byte for byte. Decision: T-315 (wall tile) PROMOTED onto this base.
- T-312 (wall tile ledger) WORKED: Checker own 1F-12 26.305 = ledger, pantry 32.375 vs 32.3422 (+0.10 %). Decision: carried by T-315.
- T-311 (parapets / plinth) WORKED: parapet RC 8.040 .. 20.081 m3 MISSING confirmed by the Checker's own reading; F-T311-C1 (lower bound = max(0.30, build-up)) and C2 (second 0.200 strip) -> T-319 acceptance.
- T-316 (slab top-bar extent) WORKED: F-T316-01 / -02 ENGINE_WRONG -> T-318 acceptance (still BLOCKED-OWNER).
- T-317 (spatter dash / joint mesh) WORKED: spatter scope = every finished face (answered OD-V3B-4 .. 7). Joint mesh has no rule, note or specification -> OWNER PACKAGE item 2 (ERS s.2.7: contractual measurement decision).
- T-320 (backfill displacement) WORKED: 105.163 m3 established, closes 0.000; F-T320-03 (FF blinding) -> NEW T-322.
- T-313 r1 PARTIAL (REJECTED: door reveals booked NO_LINE although 22 FIN.PLASTER lines carry them = double count at integration). Rework r2 READY 23:59 (missing scope 36.78 -> 13.64 m2). Decision: Gate A first; thresholds -> NEW T-325.
- T-224 r1 PARTIAL (REJECTED narrow: free-edge web width a convention labelled DRAWING-CONFIRMED). Rework r2 CLAIMED by worker 1; F-T224-C1 (hatches cut by slab-tag circles) -> NEW T-323.
- T-321 (roof build-up) READY: no roof layer printed anywhere; falls-layer trade CONFLICT Q-41 vs Q-45 ruled by the Lead (one SCREED volume; Q-45 = mix); F-T321-02 (1.400 m boundary parapet) -> T-319.
- Recurring cause (new): a ledger searched one line family and called a component NO_LINE (T-313 r1). Decision: every ledger task row now asks for a search over every family by physical element before NO_LINE (lessons register 2026-10-28).

## 2026-10-28 20:20 (lead run; covers 2026-10-26 06:15 - 2026-10-28 20:15, of which about 60.5 h had no agent run)

- T-311 (parapets / plinth as physical elements): READY 20:09, Gate A pending (classification next run). Handoff reviewed: element defined run by run, 46 components each to one trade, DOUBLE 0, parapet RC 8.040 .. 20.081 m3 MISSING from every line, material HELD (Q-65 C), heights as printed; nothing assumed, so nothing sent back; one gap: the worker's full suite was NOT completed (lock window) -> the Checker runs it to the end before any PASS. Decision: NEW T-319 (lane I parapet RC line), T-199 acceptance (parapet formwork 81.589 .. 202.782 m2), register rows.
- T-244 (Gate B, V3.0.20) and T-312 (Gate A): still READY, 62 h, delay cause CHECKER-RUNS (outage). Decision: first and second in the VERIFIER QUEUE; Checker run 19:51 in progress.
- T-313: re-claimed by worker 2 at 19:44 after the stale 26 Oct claim (no branch had been pushed). Decision: none needed.
- New missing-category pieces: T-320 (backfill / disposal displacement ledger, NET of the T-170 overlaps), T-321 (roof build-up layer ledger incl. the unmeasured main roof outline).
- PARTIAL / FAILED: none classified (nothing reached a verdict). UNCLOSED runs: Worker 1 2026-10-26 06:24 and Worker 2 06:40 = INCOMPLETE. Tool issue (Worker 1 20:09): the decode wrapper expects base64 but the Drive connector now saves raw binary; worked around via scratch base64 (deleted) -> NEEDS FIXING (agent_env.sh lives on main, owner-only).

## 2026-10-26 06:15 (lead run; covers 04:15 - 06:15)

- T-305 (exterior plaster face-to-line): WORKED (MERGED 9d71ef09; Checker own parapet outer faces 48.237 of 66.428 m2 agree 0.000, GF two-F.F.L. +3.430 m2 confirmed). Decision: T-311 PROMOTED TODO (worker 1 next); T-314 stays in lane I after T-199.
- T-308 (formwork r5 rows): WORKED (MERGED efb38618; BAND0049 = curved B7 corner beam, Checker 2.927965 vs 2.927816 m2 ENGINE_RIGHT). Decision: T-199 consumes it (no change to its row).
- T-309 (pool membrane / screed): WORKED (MERGED 834ada3e; 29.582355 m2 / 1.524503 m3 = Checker; upstand 1.350 m2 HELD; function S8.2 open). Decision: T-310 consumes it after T-246.
- T-307 (slab bar-end census): WORKED (MERGED c48f7062; continuous 0 m and edge-beam straight 0.160 m = Checker on GF-135 x; Checker revised his own T-306 p.15 reading at 400 dpi). Decision: NEW T-316 (top-bar extent, 1,113.683 kg cause) and NEW T-318 (candidate split, BLOCKED-OWNER on the reinforcement implementation stage; OWNER PACKAGE item 1).
- T-312 (wall tile face-to-line): READY, Gate A pending (pantry 32.3422 m2 NO_LINE). Decision: NEW T-315 (lane I wall tile integration with a per-face tile / paint / plaster cross-trade check), after T-312 MERGED and T-244.
- PARTIAL / FAILED: none. Team: Worker 1 05:20 and Worker 2 05:40 IDLE on the run lock (correct); Worker 3 05:00 run open on T-244 (scheduler PENDING); every closed run self-check PASS.

## 2026-10-26 04:15 (lead run; covers 02:15 - 04:15)

- T-255 (Gate B, V3.0.19: ring BAND0043 end closure + W03 / W18 trace): WORKED (MERGED 01358449; ring ENGINE_WRONG chord -0.012043 m3 -> drawn faces, Checker -0.0015 %; 3,704 lines byte-identical). MISSING named: 27 reveal lines blank, no FIN.WALL.TILE row. Decisions: T-313 (reveal ledger), T-312 (wall tile ledger).
- T-304 (key map unit exclusion): WORKED (MERGED 01358449; scoreboard tool-scored again on V3.0.19, F-SCORE-01 closed).
- T-306 (slab steel spread by cause): WORKED (MERGED 01358449; F-T306-01 CONFIRMED on the Checker's own p.15 read; O-T306-01 'extend 50 % top reinf. where possible'). Decision: acceptance added to T-307 (now unblocked, worker 1 next).
- T-294 (records bound to their own lines): WORKED (MERGED 1157b8f8). Decision: the next package (T-244) carries the V3.0.19 whole-file records by one verdict-rebind run (Checker queue item 3).
- T-305 (exterior plaster face-to-line), T-308 (formwork r5 rows): READY, Gate A pending. T-305's finding (parapet / plinth / annex faces in no line) -> T-311 (lane S element definition) and T-314 (lane I face rows), both after T-305 merges.
- PARTIAL / FAILED: none. Team: Verifier 03:51 stood down on the overlap guard (correct), Worker 1 03:20 IDLE on the run lock (correct); every closed run self-check PASS.

## 2026-10-26 02:15 (lead run; covers 00:15 - 02:15)

- T-303 (WP wet-area / roof / pool-tank inventories): WORKED (MERGED 1d3f69b0; Checker own: 1F east bath upturn 1.580 vs engine 1.48 ENGINE_WRONG, 2 doors with two transition lines and 3 with none, pool membrane + screed printed and in no line = MISSING, tank NA with evidence). Decisions: T-310 (lane I fix), T-309 (pool membrane / screed ledger); O-T303-01 pantry 0.045 m2 carried in T-310.
- T-293 part 3 (stair / dome / tank formwork faces): WORKED (MERGED 02f3e47e; stair rows over-measure 3.624964 m2, 1.639289 double booking Checker own-checked; F-05 R-FW-P3-1 accepted). Decision: T-308 formwork r5 rows before T-199.
- V3.0.18 record set (Checker 01:25): WORKED (8 records + DG re-issued, ST-03 downgrade moot; whole verified lines 1).
- T-304 (key map 'item'), T-306 (slab steel spread by cause): READY, Gate A pending. T-306's F-T306-01 (no development drawn at continuous supports, 556.205 .. 1,027.310 kg on the dev lines) -> T-307 after T-306 merges.
- PARTIAL / FAILED: none. Team: Worker 2 01:39 IDLE on the run lock (correct); Dashboard 00:54 recovered after the 20:54 usage-limit failure.

## 2026-10-26 00:15 (lead run; covers 16:15 - 00:15; the 22:15 run recorded its loop in LEAD_REPORT only)

- T-299 PART F: WORKED (MERGED 5cb1e7e8 + downgrade DG-1b0eacce2d68f2a5); the audit-band challenge closed 23:02 (0.051 t = density vs max-spacing reading in 11 populations; a report wording defect, no number wrong).
- T-266 (V3.0.18, stairs / 1F landing marble / pantry piece): WORKED (Gate B PASS ceeb5135; 3,695 lines byte-identical; own re-measures agree).
- T-297 r2 (rebar basis, LB-10 datum join): WORKED (1647711d; 2F main bars 0.159288 t HELD on D-39, CB5 links HELD).
- T-301 (WP.FOUNDATION inventory): WORKED (ac811414; 416 faces, residual 0.000; lift-pit screed whole-countable once the export reads the inventory).
- T-293 part 2 (formwork slab-level ledger): WORKED (a1e0c43a; CB5 span 2 double count CONFIRMED -> T-199; BAND0049 UNRESOLVED). Part 3 now TODO.
- T-302 (W17 developed hole): WORKED (5c00a0f8; 1F-11 released 59.4511 low by 2.01 .. 2.27 m2 -> T-244).
- T-300 (beam rebar completeness safeguard): WORKED (196a7a0b; unwired, 0 kg invented). Non-blocking findings kept here for later rows: F-T300-01 B27 0.90 m wide single-link reading (designer RFI S20); F-T300-02 the route G sha depends on the input FILE NAME (reproducibility: two runs of one drawing under two names give two shas; candidate for the T-294 binding work or a tooling row once lane I frees); F-T300-03 CB filled TOP marks read on all spans.
- F-SCORE-01 (Verifier 22:49): the key map refuses unit 'item', so no candidate cell is tool-scored since V3.0.14 -> T-304.
- Recurring cause (Lead's own): a QUEUED "after T-xxx" row was not flipped to TODO when T-xxx merged between Lead runs, so worker 3 found no lane I TODO and took lane A T-303 (worker 2 then idle twice). Decision: every Lead run re-reads each "after T-xxx" row against the merges since its last run before writing the lane order.

## 2026-10-25 16:15 (lead run; covers 14:15 - 16:15)

- T-292 r2 plaster / paint face-to-line ledger: WORKED (Gate A PASS, MERGED a9754a67, Verifier 15:32; own W17 re-measure; the Checker withdrew its own 12:48 ask: the window area is not the hole). Finding F-T292-02: hole bounded below by the elevation projection (8.1239 m2), 1F-11 HELD 60.6011 .. 62.3352 m2, released 59.4511 at least 1.15 m2 low. Decision: T-244 acceptance holds the line; NEW T-302 measures the developed hole.
- T-295 ceiling face-to-line ledger: WORKED (MERGED 964c5ebe, Verifier 15:33; 1F dressing 2.970 m2 omission confirmed). Decision: T-284 adds the dressing line; exterior soffits / P-2 bands stay HELD both.
- T-297 rebar line-to-member basis ledger: PARTIAL (MERGED 5408da97, then gate (f) defect F-T297-04: 4 2F main-bar lines 0.159288 t labelled DRAWING_CONFIRMED on the held D-39 datum; the Lead's 14:15 challenge (a) named this and it was not met). Decision: r2 NARROW, worker 1 next; lessons row (one member, one datum status across trades).
- T-296 skirting opening-to-line ledger: WORKED (MERGED 57c31ae4, Verifier 16:08; own 1F-01 15.900 lm agrees 0.000). ENGINE_WRONG proposals (+5.802 lm sill windows, W15 / W16 range, wet pantry NOT_APPLICABLE) -> T-246 acceptance; module not task-prefixed again (unique today) -> rename in T-246.
- F-T254-01 ring ground beam end rule: closed by the Checker from the drawing (16:00): +0.012043 m3 (ENGINE_WRONG -0.69 %). Decision: correction + regression pair ride the T-255 package; lessons row.
- T-299 PART F footing reinforcement: READY 15:57, first in the Checker queue (owner-session item); Lead challenges: the downgrade conflict with the Checker's 15:35 note and the audit band 2.718 vs the owner's 2.769 t lower bound.
- Team: every run since 14:15 closed with a final line except the open Worker 3 15:00 (T-266) and Verifier 15:51 runs; Worker 2 15:40 IDLE on the run lock is correct (the 14:41 run worked 61 min). Recurring cause: a Lead challenge written into the queue note is not always read by the worker before hand-in (T-297 (a)); from now on challenges that change acceptance go into the ROW, not only the queue note.

## 2026-10-25 14:15 (lead run; covers 12:15 - 14:15)

- T-254 exterior ground-beam basis correction (integration package, V3.0.17): WORKED (Gate B PASS, MERGED 7c49e890, Verifier 13:35; own DXF re-measure of all 16 rebased lines agrees, main-house exterior GB 8.1642 -> 15.9575 m3 DRAWING-CONFIRMED, +95.5 %; 2F / annex columns and annex GB HELD blank, 5 members NOT_PRESENT, boundary G.B line added HELD). Open: F-T254-01 ring end rule, F-T254-02 PC-1F-B watch. Decision: both in ELEMENT_REGISTER; T-266 now TODO on V3.0.17.
- T-298 export completion (tonnes + slab join by panel id): WORKED (MERGED 274885e6, Verifier 13:54; own independent join 62 / 62). First WHOLE verified line in the real export (CONC.SLAB 60.280155 m3); reinforcement in t. Decision: WP part of the completeness gap stays with T-301.
- T-299 r1 read-only reinforcement reconciliation: WORKED (MERGED 05ad6d02, Verifier 14:00; 0 double counts, SB1 4.550 m own re-measure). Minor F-T299-01 (stale 'Q-71 open' hold wording). Decision: PART F (owner 13:16 / 13:25 footing requirements) TODO for worker 1 after T-297, carrying F-T299-01.
- T-293 formwork ledger part 1: WORKED (MERGED 294da634, 12:19). Decision: part 2 (slabs / stairs / domes / tank + boundary G.B tie) TODO after T-299 PART F.
- T-292 plaster / paint face-to-line ledger: PARTIAL (REJECTED narrow 12:48: test module name collides with T-293's on the merged head; 1F-11 W17 under Q-76 A). Decision: r2 with the exact fault (CLAIMED 13:44); new lessons row (task-prefixed module names, joint merged-head test run).
- T-295 ceiling face-to-line ledger: READY 14:12, classified at its verdict (first in the Checker queue).
- Team: every run since 12:15 has a final line except the open Worker 1 13:21 (T-297) and Worker 2 13:40 (T-292 r2) runs; no IDLE run since 11:40 (the 35-minute sizing is holding; lessons row stays OPEN for 24 h).

## 2026-10-25 12:15 (lead run; covers 10:15 - 12:15)

- T-290 stairs / domes basis ledger: WORKED (MERGED 891dbd4d, Verifier 11:05; D1 wedge 0.025714 and MS2-LD 0.4696 m3 agreed; E1 waist: section B-B draws it on ground, so soffit formwork NOT_APPLICABLE and concrete HELD both stand, not a conflict). Decision: T-266 consumes it unchanged.
- T-291 blockwork wall-to-line ledger: WORKED (MERGED 0c6b2ba5, Verifier 11:30; bindings / totals from register v4 agree, 422.5314 m2 determinate). Decision: T-279 consumes it after T-255 in the owner's lane I order.
- T-170 excavation / backfill ledger: WORKED (MERGED 2991be3d, Verifier 11:31, minor F-T170-01). Every volume stays HELD BLANK (formation bound only). Decision: no new row; the finding rides the next excavation row.
- V3.0.16 Checker records (8 V2 verdicts, 7 downgrades over 43 lines, 21.953969 m3 to HELD / CONFLICT): WORKED as records, PARTIAL in effect: 0 whole lines countable in the export (F-REC-01 slab completeness join on the V3.0.8 grain; F-REC-02 no waterproofing inventory). Decision: T-298 (owner row) FIRST for worker 2 cross-lane; NEW T-301 (WP inventory).
- T-292 (plaster / paint face-to-line) and T-293 (formwork face-to-member part 1): READY, classified at their verdicts; both hand-ins left the full suite unfinished (lock window). Decision: the Checker runs the suite to the end; new rows sized about 35 min + suite.
- Team: Worker 1 11:20 / Worker 2 11:40 IDLE on their own run locks (previous runs about 80 min). Recurring cause 'package + full suite longer than the cadence': lessons row OPEN, monitored 24 h.

## 2026-10-25 10:15 (lead run; covers 08:15 - 10:15)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-289 | WORKED | MERGED 455c93c4 (Verifier 09:33: own V3.0.15 csv a4dc01dd, all 43 ids, residual 0.000 m3; own re-derives L-e9a88532 1.80975 m3 and interior-typed L-27d104ca 1.2540 m3; 2F id set = 8 measured of 14) | main-house exterior GB 15.9600 m3 DRAWING-CONFIRMED (engine 8.1642, +95.5 %) goes to T-254 with the generic regression pair and F-T289-01; lessons row CLOSED on the rule |
| T-275 r2 | WORKED | MERGED 6c4c9700 (Verifier 09:46: sealed bytes as candidate-side MATERIAL_RESULTS.json -> exit 2, clean -> exit 0) | lessons row CLOSED; O-T275-01 (symlink name check) folded into T-294 part (g) |
| T-286 | WORKED | MERGED e861e390 (Verifier 09:51: own 1.100 m2, 0.0 %; box closure -0.0001 m2; W03 6.7292 m) | +1.100 m2 WET had no lane I carrier: now in T-266's acceptance; lessons row added CLOSED |
| T-245 r2 | WORKED | MERGED ef3305f1 (Verifier 10:17 Gate B PASS: full suite NEW 0 in 4 chunks, own run json 3181cf12 / csv a4dc01dd, one identity on 3,699 lines, F-T245-01 on the real 14 ids) | records not issued (lock margin): path named docs/agents/verdicts/<candidate>/, first in the 10:51 run; T-254 promoted; O-T245-03 -> T-294 (h); lessons json-hash row CLOSED |
| T-290, T-291 | (READY, not classified) | r2: F-T245-01 fixed, maps LAST, full suite NEW 0; T-290: 14 lines residual 0.000 m3, closable 2.864463 (not 2.915), drums omission, formwork r4 on retired readings; T-291: all 21 masonry lines BLOCKED blank, determinate 422.5314 m2 | VERIFIER QUEUE T-245 r2 -> T-290 -> T-291 with Lead challenges; T-266 / T-279 / T-293 acceptance extended |
| Worker 1 09:19, Worker 2 09:40 | (IDLE on own run lock; not a failure) | 08:20 / 08:40 runs took 101 / 84 min on packages sized about 50 min | stop points named in every new row (owner 04:38 sizing) |

## 2026-10-25 08:15 (lead run; covers 06:15 - 08:15)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-287 | WORKED | MERGED 542b64c7 (Verifier 07:58: own C5 / C3 on the CB5 ground beam, base +0.25, 1.430 m3 vs candidate 1.2375, -13.5 %) | CB5 pair VERIFIED AS A COMPONENT; T-254 carries 1.4300 m3; G2 / G3 are designer-package rows |
| T-280 | WORKED | MERGED 86fdc315 (Verifier 08:05: 2 chains by hand, 26 restated 734.779 vs 734.781 kg, LOWER bounds labelled, 10 HELD blank) | lessons row 'a bound is only as good as its datum' CLOSED; F-T280-01 into the element register (CN tops = T-214 slab top) |
| T-245 | PARTIAL | REJECTED narrow 07:58: full suite NEW 1 = codemap test (report committed after the maps); every other Gate B check PASSED on the real candidate (determinism across local names, one id + one revision set, export one command, invalidation STALE) | TODO r2 (worker 3 08:59): merge 86fdc315, F-T245-01 (EXCLUDED stays EXCLUDED + adverse test), maps LAST; REPEAT of the 'maps as the LAST commit' rule, written into every hand-in instruction; whole-file binding LIMIT -> T-294 (queued after T-255) |
| T-289 | (READY 07:10, not classified) | basis ledger, residual 0.000 m3 on all four; FOUND 3 exterior runs in interior-typed lines: main-house exterior GB 8.1642 -> 15.9600 m3 (+95.5 %); 2F columns 8 line ids vs the Checker's 14 | Gate A FIRST 08:51 with 5 Lead challenges; T-254 acceptance extended |
| T-275 r2, T-286, T-170 | (READY / set READY / complete, not classified) | guard on every census read (+4 tests); G4 settled from the drawing (+1.100 m2 WET floor); excavation ledger, every volume HELD blank | Gate A in order T-275 r2, T-286; T-170 next free slot |
| Worker 1 07:20, Worker 2 07:41 | FAILED (planning, Lead's) | both runs ended 'no claimable TODO row' (0 TODO, READY 5) | Lead fault: the queue held no row outside lane I; four integration-dependency rows added (T-290 .. T-293), each claimable while READY > 3 |

## 2026-10-25 06:15 (lead run; covers 04:15 - 06:15)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-288 | WORKED | MERGED 643b310b (Verifier 05:35, own GF-W16 re-clip 2.9500 m, register v4 449.6007 - 7.9131 d) | T-279 unblocked on research; waits only on the lane I chain; lessons row CLOSED |
| T-283 | WORKED | MERGED 6e141df6 (batched with T-281; one owner per piece under the round stair) | T-284 unblocked on research; lane I after T-279 |
| T-281 | WORKED | MERGED 40518c58 (own MS1-U 3.720 / 4.2555 m2, MS2-LD-W 1.495; formwork = finished soffit on 4 flights) | stair soffit line HELD BLANK in T-284 until verified whole |
| T-257 | WORKED | MERGED 6a8eea78 (re-pointed T-210 tests judged not weakened: same rules, same 24-module base) | none; 6 undeclarable modules stay red with fix proposals |
| T-275 | PARTIAL | REJECTED narrow 05:55: census side files outside guard_inputs; sealed-sha probe exit 0 | rework r2 (worker 2 after T-286, or worker 3 06:59 while T-245 is unmerged); lessons row OPEN |
| T-245 | (READY 06:13, not classified) | V3.0.16, json-hash cause named (local file name in source.documents[].file), export one command; full suite NOT run by the worker | Gate B first in the 06:49 Checker run with 6 Lead challenges |
| T-287, T-280 | (READY 05:59, not classified) | G1 settled from drawings (1.4300 m3); 26 cores -66.548 kg as a lower bound, 10 HELD | Gate A after T-245; T-280 within 2 Checker runs |


| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-270 r2 WP foundation into V3.0.15 (Gate B) | WORKED | MERGED 04d34378 (Verifier 03:46): 3,680 lines byte-identical, 19 added (7 VERIFIED, 1 DC, 11 HELD BLANK); BURIED_LIQUID 45.4682 m2 = own sum of the 32 T-276 DC faces, 4 more faces own -0.004 %; T-263 35.404 refused by adverse test; full suite NEW 0 | candidate of record V3.0.15 (not released); lessons row closed; json sha not reproducible run to run -> T-245 acceptance (canonical hash binding), new lessons row OPEN |
| T-278 floor-area scoring key | WORKED | MERGED 6366b754 (Verifier 01:28): own re-key 380.3641 m2 on 40 lines, -7.13 % vs freelancer 409.58; landing owned once | scoreboard runs on T001C; landing marble line gap -> T-266 acceptance |
| T-285 blockwork register v3 | WORKED on scope, PARTIAL as T-279 input | MERGED e418c5e0 (Verifier 01:41): established 449.5934 m2; Verifier 02:00: 7.913 m of GF wall under six sunken panels at the normal soffit (overstated 7.913 d m2, D-41) | NEW T-288 (register v4, CLAIMED 03:41); T-279 after T-288 |
| T-282 r3 formwork end faces | WORKED | r2 REJECTED narrow 01:31 (1AA not a free end); r3 MERGED aa3a7bb4 (Verifier 04:15): own five END contacts (7FE, lift ring 7C2) = 0.000, 10B+7D1#1 A 1.300 m agree, full suite NEW 0; research only, no BOQ line moved | closed; formwork stair soffit faces to be reconciled with T-281 at its check |
| T-283 ceilings r3 | handed in (READY 02:50) | decor 363.173 -> 361.229 m2 (-10.40 % vs released 403.163); 1.944 m2 hidden flight moved to stair zone HELD; bulkheads 27.935 m2 | batched with T-281 at Gate A; Lead challenge: one owner per piece vs T-281's 1.808 / 0.777 / 0.063 m2 |
| T-257 K1 boundary declarations | handed in (READY 03:35) | 18 modules declared by_design from T-210 records; 6 undeclarable stay red with fix proposals; 2 real-tree T-210 tests re-pointed | Gate A; Lead challenge: re-pointed tests must assert the same property over the same set, else weakened |
| T-281 stair soffits | complete, held back (READY limit) | ST-01 17.070 plan / 17.198 .. 17.243 true, MS1-L CONFLICT 3.215 .. 3.935; ST-02 8.479 plan, curved true HELD; GF stair zone 9.854 = 9.014 + 0.777 + 0.063 | hand-in authorised to the Checker when READY < 3; cross-check vs formwork r3 stair soffit faces |

## 2026-10-25 00:15 (lead run; covers 22:15 - 00:15)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-276 r2 buried faces traced | WORKED | MERGED 4d88681b (Verifier 22:54): own DXF 182+183 band end quadrilateral 0.03175 m2, 7C3#2 1.5585 m (-0.05 %), 17E+17F 0.4243 m; 32 DC faces 45.4682 m2; COL:255 neck face HELD | lessons row closed (prior); T-270 r2 takes LEDGER_T276 |
| T-277 beam width census | WORKED | MERGED 9446dfcb (Verifier 22:59): own band widths CB2 0.250 vs W20, B21 0.400 vs W45, CB10 0.20 / 0.30 vs W25 CONFLICT; B27, B7 AGREE; both readings carried | RFI S5 search closed; T-285 carries the four walls' crossing strips both ways |
| T-274 blockwork height pieces | WORKED | MERGED aba9399a (Verifier 00:06): own GF-W28 22.3386 vs 22.3384, 1F-W07 11.4599 = worker; register proposal 449.260 -> 449.565 m2 NOT applied | NEW T-285 (apply as register v3); T-279 after T-285; lessons row closed |
| T-270 r1 WP foundation into V3.0.15 (Gate B) | PARTIAL | REJECTED narrow r2 22:58 on WP.BURIED_LIQUID only (35.404 from T-263 run faces vs 45.4682 traced, -22.1 %, contains non-earth faces); every other figure own-verified byte-for-byte | r2 first in lane I (owner order 23:49); lessons row (integration takes the newest verified ledger) |
| T-282 r1 formwork faces at oblique / curved carriers | PARTIAL | REJECTED narrow r2 00:04: END faces booked on convex-hull diagonals joining unequal edge ends (170+7C3#4 0.2318 m = +0.2202 m2 FORMED; 1811+1812#1 0.0972 m); side faces agree | r2 first in lane S; lessons row (end face only on a drawn end or free section); element register row |
| T-278 floor-area scoring key | handed in (READY 23:50, Gate A) | T001C keys FLOOR.INTERNAL 380.364 m2 on 40 lines (was 372.472 on 38), -7.13 % vs freelancer; T001B outputs byte-identical | Gate A next; Lead challenge: 1F landing 4.9225 m2 not also in a marble / stair finish line |
| Checker T-180 slots 23:00 / 00:06 | findings | jamb scan: exactly one jamb inside a column (OP-1F-026, 32.7 mm, two routes); blockwork VERIFIED 95.633 -> 105.004 of 449.260 m2 (GF-W33 5.586, 1F-W01 2.832, GF-W12 1.953) | into T-285 (register v3 carries the VERIFIED values) |
| RFI package (owner 23:57) | Lead verification | 30 rows, 0 removed, 2 search notes closed, 4 missing rows G1-G4, 9 PRIORITY RFIs (6 ready) | NEW T-287 (G1-G3), T-286 (G4 + plaster blockers); not to be sent until both return |

## 2026-10-24 22:15 (lead run; covers 20:15 - 22:15)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-267 r2 stair rule store registration | WORKED | MERGED e7eaee64 (Verifier 20:24): full suite on d2135e30 to the end NEW 0 / KNOWN 395 / ABSENT 1; manifest sha = own sha of 1.7.0; SOFTWARE_VERIFIED, QUANTITY none, CODE_NOT_VERIFIED | closed; T-281 builds stair soffits on it (read-only) |
| T-272 r2 ground-beam links | WORKED | MERGED ba626832 (Verifier 20:24): links per drawn clear span; count 333 .. 392 and mass HELD, never 0 | lessons row CLOSED; cut length stays HELD (hook tail / bend unprinted, designer list) |
| T-273 r2 laps + metric ton | WORKED | MERGED 42e32cf3 (Verifier 20:58): boundary set 0 / 1 / 1 / 2 at 1.2 m in 4 input forms; 31 starter chains + 56 joints, each lap zone counted exactly twice; five categories; all laps HELD / PROVISIONAL, 0 released | NEW T-280 from finding F-T273R2-01 (core lower bound ignores the 0.17 m underlay, -74.381 kg at the formation limit) |
| T-271 r2b ceilings, GF light well | WORKED | MERGED 789ebbb4 (Verifier 21:58): GF-130 23.2371 = light well 13.392 + pocket 1.552 + stair zone 7.402 (HELD stair soffit) + slab 0.891, every part within 0.0014 m2; R2 decor 363.173 vs released 403.163 (-9.92 %), freelancer 409.58 (-11.33 %), not verified as a whole | NEW T-281 (stair soffits), T-283 (ceilings r3 integration-ready + hidden-stair test), T-284 (ceiling integration, QUEUED) |
| T-276 r1 buried faces traced | PARTIAL | REJECTED narrow 20:59: band 177 + 7CD cut square at the shorter edge -> 0.3708 m of false ring earth face + spurious end faces; COL:255 0.052 mm sliver taken as a 0.5948 m2 beam face; DC total <= 45.611 vs 46.521 m2, HELD; three checked runs agree to 0.03 % | TODO r2 claimed 21:45 (worker 2); cross-trade: NEW T-282 (the same check on formwork r4); lessons row |
| T-270 WP foundation into V3.0.15 | handed in (READY 21:58, Gate B) | 3,680 lines byte-identical + 19 added; 11 held lines BLANK | Gate B first; Lead challenge: the 35.404 m2 buried sub-line contains faces T-276 r1 showed are not earth faces |
| T-277 beam width census | handed in (READY 21:59, Gate A) | 137 runs: 105 AGREE / 7 CONFLICT = D-02 + D-27 exactly; CONC.BEAM drawn 5.4421 vs schedule 5.7665 m3 (-0.3244) | Gate A next; worker full suite not run to the end (10-min shell): Checker runs the level's suite |
| Checker T-180 slot 1F-W00 | finding | own net 12.935 vs register 12.863 m2: W18 deducted over 0.0327 m already inside column 2FD8 (0.0706 m2 removed twice); length ruled 6.571 m | added to T-274 acceptance (part-in-masonry deduction + register-wide jamb scan); T-279 carries 1F-W00 only after it |

## 2026-10-24 20:15 (lead run; covers 18:15 - 20:15)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-240 floor area V3.0.14 (Gate B) | WORKED | MERGED d07af773 (Verifier 18:44): 37 changed rows by hand, pantry wet 8.955 own, full suite NEW 0; internal 380.364 vs released 385.634 m2 (-1.37 %), NOT VERIFIED as a whole | T-278 (key map misses 7.8925 m2 typed spaces); T-270 unblocked, first in lane I |
| T-261 r3 blockwork split | WORKED | MERGED 164b189f (Verifier 18:56): 11 / 11 rising walls own (1F-W13 16.8073, 1F-W17 4.6943, 1F-W18 19.7326, 1F-W24 5.5401 + 1.0577 held) | T-274 promoted TODO; T-279 (walls into the candidate) queued after T-274 + T-270 |
| T-273 r1 laps + metric ton | PARTIAL | REJECTED narrow 18:59 against owner s.6 (18:38, after the 18:26 hand-in, not a worker fault): boundary tests 12.00 / 12.01 / 22.80 / 22.81 m at 1.2 m, 30 FOUNDATION LAP rows 288.897 kg vs STARTER 40 D on the same chains not reconciled, detailing categories | TODO r2; row was UNCLEAR_STATUS (note before the status word): fixed, first in lane S |
| T-272 r2 ground-beam links | WORKED | Gate A PASS 19:59: Checker own 7E0+FD#1 19 .. 23, 7D0+FC#2 36 .. 40, ring 35 .. 44 by radial admissibility (his 40 .. 45 withdrawn); count / mass HELD | merge after T-267 r2 (in the Checker run 19:51); lessons row |
| T-271 r1 ceilings r2 | PARTIAL | REJECTED narrow 19:59: light-well no-ceiling taken as face GF-130 23.237 where the slab plan's S-OPENING is 16.005 m2 (= released engine); bulkhead CB6 1.200 agrees | TODO r2 (files research/agents_t271 + tests/t271_*); lessons row |
| T-267 r2 stair manifest | handed in (READY 19:38) | manifest +1 AUTHORED entry, full suite NEW 0 | in the Checker run 19:51 (critical dependency, never delayed > 2 runs) |
| T-276 buried faces r2 | in work (CLAIMED 19:47) | worker 2 | Gate A when READY; feeds T-270 as a later delta |
| Row stamps | process fault | T-272 READY stamp 20:05 written by 19:35-19:59; worker 3 run-log 19:40 committed 19:36 | lessons row (stamp = `date -u` at writing); watch |

## 2026-10-24 18:15 (lead run; covers 16:15 - 18:15)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-263 buried-concrete liquid waterproofing | WORKED | MERGED c0ab564d (Verifier 17:59): 35.404 m2 DRAWING-CONFIRMED, own 7E9+7EA#1 2.535, 7E0+FD#1 2.8475, F12 top 13.690 agree; missing category in engine and freelancer | T-276 (remaining faces), T-270 scope extended (integration); lessons row |
| T-261 r2 blockwork split | PARTIAL | REJECTED 17:00: 7 / 9 rising walls agree own; 1F-W18 / 1F-W24 carried register gross on non-drawn extents | r3 CLAIMED 17:41 with the exact fault |
| T-272 ground-beam stirrups | PARTIAL | REJECTED 17:04: shape / hooks / cover agree; count envelope assumed links through crossing beams, ring as one run | TODO r2 narrow; lessons row |
| T-267 r1 stair finish-level module | PARTIAL (unchanged) | REJECTED 16:07 narrow (manifest); not reclaimed in two worker 1 runs | row set to TODO r2 (claim rule cause, see below), first in lanes S and I |
| T-240 floor area V3.0.14 | handed in (READY 17:52, Gate B) | internal 340.765 -> 380.364 m2 vs released 385.634 (-1.37 %), 3,643 / 3,680 lines byte-identical | Gate B next; the +39.6 m2 step to be reconciled piece by piece |
| Worker 1 lane order | process fault | claimed T-273 17:27 while two narrow reworks (status REJECTED) were first in lane S | rework rows now TODO rN (lessons row); T-273 continues |

## 2026-10-24 14:15 (lead run)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-264 formwork r4 | WORKED | MERGED 90203feb (Verifier 13:00): own ring B7 arcs, boundary 7FE#2 6.480, exterior outer faces 47.663 m2 = Checker 12:10 run lengths; no quantity moved | none; formwork stays research until T-199 integrates it |
| T-269 floor-area blockers | WORKED | MERGED 991f85fa (13:03): 1F living 38.6335 m2 own-VERIFIED (released A 44.8694 = +6.2359 ENGINE_WRONG; freelancer 38.96, -0.84 %); F3 + F4 2.070 floor, F1 + F2 6.1244 HELD (ST-02 undrawn) | T-240 WP2 / WP3 carry it; designer item for ST-02 stays with the stair consultant items; lessons row added |
| T-258 stairs / domes closure | FAILED r1 -> WORKED r2 (54 min) | r1 REJECTED 13:03: D1 arrival wedge 0.0315 m3 into the +1.00 slab neither deducted nor listed (gate e / f); r2 MERGED b1b72a50 (13:57): 0.025714 slab / 0.005786 stair, closable component 10.805259 m3 | T-266 now waits only on T-254; lessons row added (arrival treatment once per flight) |
| T-262 opening-to-room by geometry | WORKED | MERGED c8dba740 (14:00): W06 wedge 1.994 m2 with door 320, W19 + D-1F-01 west bath 4.658 m2, W20 + D-1F-04 east bath; name join swapped, 0.000 m2 every trade = ENGINE_RIGHT | no follow-up; geometric join is the rule (lessons row) |
| T-265 ground-beam rebar | handed in (READY 14:13 @ 4353552a) | boundary G.B 315.56 kg lower bound, exterior top / bottom 796.32 kg, side bars 199.08 and stirrups HELD | Gate A next (structural); new T-272 closes stirrups / side bars / laps from prints only |
| T-180 slot | nothing measurable left on CLOSABLE rows (Verifier 14:02) | every CLOSABLE row waits on lane I or consultant items | light runs go to the blockwork register v2 SS walls (verified share ahead of T-261) |
| Overlap IDLE lines (worker 1 12:20, worker 2 12:39) | team health, not a failure | the 11:20 / 11:40 runs still held their locks; each run takes > 1 h | no action (cadence is the owner's); each IDLE line carried its reason |

## 2026-10-24 12:15 (lead run)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-219 foundation / pit waterproofing | WORKED (line PARTIALLY VERIFIED) | MERGED de7c1c4c (Verifier 10:40): own footing membrane 109.85 m2 (24 sizes x tag count on 9 outlines), screed 5.4925 m3, pit 47.43 / 26.73 m2 / 1.035 m3 = worker 0.000; F10 / F, pit walls, sides, procurement HELD | new T-270 integrates the verified parts (HELD BLANK, owner 10:56); T-263 continues the buried-concrete coat |
| T-250 plaster / paint face crosswalk | WORKED | MERGED 47390c9b: own W03 room side 6.7294 m (T-128 6.731), W06 in GF-13, GF-16 strip 0.300 m2; no quantity change | T-244 may take its faces when lane I reaches it |
| T-260 aluminium doors evidence | WORKED | MERGED c6732efe (11:55): own both-face widths 1.000 x3 / 0.900, class ALUMINIUM x3 from the side spaces; line 12.760 m2 / 6 pcs vs freelancer 12.000 (+6.33 %: heights -1.000 Q-55 C, widths -0.440, count +2.200 ENGINE_RIGHT) | T-268 PROMOTED, first in lane I (one run, closes the line) |
| T-228 r2 blockwork register v2 | WORKED (after one rework) | MERGED bf4dd2a9 (11:59): 3 '(With Stair)' marks own, 1F-W10 HELD; established net 494.189 -> 449.260 m2 (-9.1 %), held-net walls 39 / 76 | T-261 PROMOTED (wall blockers the drawings settle); lessons row closed |
| T-235 r2 + part (4) V2 verdict / export | WORKED (tooling) | MERGED 3bd09b62 (12:01): own adversarial probe passed; no quantity | real export still refused by probe 10 until T-245 (lane I chain) |
| T-180 slot CONC.GROUND main exterior | PARTIAL (16 / 17) | Verifier 12:10: 15.9692 vs 15.9600 m3 (+0.06 %); stub strip 0.0026 m2 unconfirmed; ring +0.67 % = end-closure convention | both written into T-254's acceptance (show or drop the strip; state the end rule with a test) |
| T-240 WP1 floor area | progress (not a hand-in) | worker 3 11:48: V3.0.13 @ 5e12fa50, internal floor 340.7645 -> 342.6645 m2 (+0.56 %); GF OP-003 carried twice found | WP2 after T-268; twin strip in the element register |
| Worker 1 WIP | team health | T-258, T-264, T-265 all evidence complete, none READY (head moved twice: re-merge cost each time) | WIP limit: no new claim by worker 1 until the three are handed in (T-258 at 12:19) |

