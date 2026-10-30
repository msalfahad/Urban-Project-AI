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
   REPEATED 2026-10-30 20:20 (T-344 tools/label_census_v2.py merged 29 Oct 17:10 without a default-guard class:
   t212_guard_property red on the working head since; L3 of a new tools/ file did not include t212. Fix T-379 gate 0;
   the Checker's gate b now adds t212 for every new engine/ or tools/ file).
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

## 2026-10-30 20:20 (lead run; covers 16:30 - 20:20)

- T-326 r2 reveals into the candidate (Gate B): WORKED (18:26, PASS on the exact r1 fault; CANDIDATE OF RECORD V3.0.28; ARCH.WINDOW_REVEAL 12.6364 -> 12.4389 m2, -1.56 %; 3,953 lines byte-identical; one Gate B round lost at r1). Decision: none; T-327 next in lane I.
- T-377 arched-opening audit: WORKED (Gate A 18:26, first time; T-162 arrises 21.30 vs outline 18.96 m (+12.3 %), spatter on reveals +0.1975 m2, 1F-W00 mesh cut at full width; carriers T-314 / T-363 / T-364). Decision: carriers already in those rows; T-327 reads R-T377-1 / -2 for sills.
- T-373 note-9 lap binding: WORKED (Gate A 19:57, first time; the Checker's own classifier finds the same 351 lines, 0 kg mismatches; 3,001.680 .. 5,359.210 kg borrowed basis). Decision: Checker issues DGP-T373-LAP on V3.0.28 (queue item 1); T-327 applies it as a downgrade-only step; F-T373-2 (22 stair lines) -> NEW T-378 first in lane S.
- READY at 20:20 (not yet judged): T-374 straight-bar schedule, T-369 shower tanking, T-370 sanitary count. Follow-ups already routed: T-370 residuals -> NEW T-380 / T-381; T-374 F-T374-1 / -2 -> Checker items.
- Recurring: (1) guard test not run on a new tools/ file (cause 7 REPEATED) -> T-379; (2) the Drive connector's output form varies (raw bytes for Worker 1 18:17, base64 JSON for the Checker 19:58): wrapper fix for the owner / main chat; (3) Worker 1 found the venv empty at 19:22 and re-ran setup (setup reliability, main chat).

## 2026-10-30 16:30 (lead run; covers 12:38 - 16:30)

- T-359 r2 bar-detail census: WORKED (Gate A 13:59; 110 / 110 bar labels cited; R2 outer vertical COUNTABLE_AFTER RFI-B-S11; R1 d12 vs d14 CONFLICT confirmed, designer). Decision: its gaps go into T-376 RFI rows.
- T-368 r2 exposed wall-tile edges: WORKED (Gate A 13:59; Checker's own ST strip query: no beam under the GF-14 HIDDEN pair, edges HELD by name, determinate 31.65 m.l). Decision: integration rides with T-327 (already an acceptance add).
- T-361 fencing / gates / guards census: WORKED (Gate A 15:37; street 8.30 = 2.50 + 5.80, sea gate 1.00, north 31.37). Decision: none now; integration row when a lane I slot frees (not queued yet: research only, leafs / infill HELD).
- T-366 lap-authority census: WORKED (Gate A 15:56; only 3 printed lap sources; frozen _with_laps splice-count defect confirmed, 0.000 kg Alsenan). Decision: F-T366-2 (470 candidate lines on note 9 outside its starter group) -> NEW T-373 gate 2 first in lane S (downgrade-only input); defect -> NEW T-375; F-T366-1 conflict -> T-376.
- T-371 bar-shape census: WORKED (Gate A 15:57; 7 populations schedulable now, all straight, 442 lines). Decision: NEW T-374 straight-bar cutting schedule; G-T371-0 .. 7 and F-T371-1 / -4 -> NEW T-376 designer RFI rows.
- T-326 reveals into the candidate (Gate B): FAILED narrow at r1 (15:35, D-T326-1: arched W15 / W16 / W26 outside jambs + head on the band-crown rectangle, +13 % on 3 of 70 lines; 67 lines agree with the Checker's own DXF depths). Decision: TODO r2 first in lane I with NEEDS (a)-(d); cause lies in a merged Gate A ledger (T-313 r2) -> NEW T-377 audits every other trade line of the arched set (gate 2, first in lane A).
- Recurring: (1) the Drive connector's raw download still needs base64-encoding before 'agent_env.sh decode' (6 runs reported it since 12:38); workaround works, no private file left .work/private; wrapper fix for the owner / main chat; (2) an opening's SHAPE (arch) was again a hidden input: the size table carries the band-crown rectangle, the outline record carries the arch; T-377 + lessons row.

## 2026-10-30 12:40 (lead run; covers 08:25 - 12:40)

- T-318 slab bar ends into the candidate (Gate B): WORKED first pass (11:35; Checker re-derived all 196 changed + 138 added lines by his own script from the merged ledgers, 0 mismatches; CANDIDATE OF RECORD V3.0.27). Decision: T-326 TODO first in lane I; F-T318-1 (legs bounded by D less note-22 covers) goes to T-371 as a proposal only.
- T-358 excavation support / dewatering: WORKED (Gate A 09:00). Decision: T-350 reads it (scope items, quantities None).
- T-362 white AAC mesh strip / lintel bearings: WORKED (Gate A 09:00; own 4.0786 m.l). Decision: T-363 integrates it (already queued).
- T-367 masonry mortar: PARTIAL (Gate A 09:58, line 1/2 verified: F-T367-1 perimeter joints +5.5 .. +13.4 % held by name; cement / sand HELD). Decision: new T-372 integration QUEUED last in lane I with F-T367-1 held per junction; the masonry mix goes to the owner package (ERS s.2.7: material genuinely unspecified, Urban method).
- T-365 movement joints / sealants: WORKED (Gate A 09:58, NO_QUANTITY_BOTH). Decision: none; no line.
- T-360 facade cladding: FAILED narrow at r1 (09:02, D-T360-1 single outlines read as double), WORKED at r2 (11:40: D-T360-1 did not reproduce on the Checker's own handle check; face 1.5149 m2 HELD). Decision: none.
- T-359 bar-detail census: FAILED narrow (12:04, D-T359-1: eight exploded bar-shape labels on the p.7 pool detail uncited). Decision: TODO r2 first in lane S with the Checker's four NEEDS.
- T-368 exposed wall-tile edges: FAILED narrow (12:02, D-T368-1: 7.30 m.l at GF-14 given the full band under a HIDDEN overhead pair). Decision: TODO r2 first in lane A; the T-312 GF-14 open-side finding written into T-327 as an acceptance add.
- Recurring: (1) two r1 rejections today share one cause: a label / linetype inside the detail's extent not read (shape row; HIDDEN linetype): lessons rows proposed in the Lead report; (2) Drive raw binaries: Worker 1 copied a raw download straight into .work/private after the wrapper mangled it (still private, sha recorded): everyone uses base64-encode-then-decode; wrapper fix is NEEDS FIXING.

## 2026-10-30 08:25 (lead run; covers 04:25 - 08:25)

- T-279 blockwork walls into the candidate (Gate B): WORKED first pass (07:50; Checker's own run V3.0.25 3064078a / V3.0.26 8959989c, 3,697 lines byte-identical, every DC / OA wall re-measured from the drawings, largest line deviation 0.03 %; MAS.BLOCK 0 -> 579.1011 m2). Decision: T-318 first in lane I; F-T279-1 (GF-W28 open end 0.063 m unnamed) -> T-363 ACCEPTANCE ADDED.
- T-351 kitchen / laundry / pantry tile zones: WORKED (Gate A 06:05; own laundry 52.5290 / pantry 32.3750 m2). Decision: F-T351-1 (+0.0328 m2 pantry) carried as a named correction in T-326's row for the next FIN.WALL.TILE package.
- T-354 soil treatment: WORKED (Gate A 06:05; own absence search incl. Arabic notes). Decision: none; B1-05 has no line, none to make.
- Checker light work: RFI B citations (18 OK, 5 CORRECTED, 1 WRONG S12, 2 PARTIAL); downgrade records issued on V3.0.25. Decision: Lead applies the B corrections next run (nothing sent); T-350 reads verdicts/V3.0.25/DOWNGRADES.json.
- Handed in, no verdict yet: T-358 (S), T-360 (A), T-362 (I worker on a lane A row). READY = 3 = target: new rows T-365 .. T-368 are backlog-permitted research only.
- Recurring: (1) Drive binaries still arrive raw (every worker base64-wraps before decode; T-351's first decode failed 'AGENT_ENV FAIL: base64 decode failed'): working, not blocking; (2) NEW this run: the Lead session's venv has no pytest ('No module named pytest'), self-check t061 FAIL; other agents' runs PASS; watch whether it recurs in any session.

## 2026-10-30 04:25 (lead run; covers 00:25 - 04:25)

- T-347 earthworks binding: WORKED (Gate A PASS 01:05; Checker's own pit union 129.234375 m2, AT_LEAST 188.017207 m3, 256 bindings unique). Decision: none beyond T-350 (F-T347-1); note N-T347-1 (F8 in pool beyond plot excluded twice, 0.10 m3 low on the bound) carried in T-350.
- T-356 buried-concrete ranges: WORKED (Gate A PASS 01:59; own S-BOUN 91.94 / 21.45 m; strap blinding 0 .. 0.912684; band UNSUPPORTED BASIS; GB D-34 range). Decision: T-350 ACCEPTANCE ADDED; downgrade records DGP-T356-BAND / -GB-D34 queued for the Checker (VERIFIER QUEUE item 2); pad-overlap ownership ruled in ELEMENT_REGISTER.
- T-355 masonry accessories: PARTIAL then WORKED (REJECTED 02:02 D-T355-1: over-lintel width held at 21 levels; r2 PASS 03:03, +15.43 m.l measured). Decision: NEW T-362 (white AAC courses, lintel bearings, 7 unknown walls) and T-363 (integration, after T-279 and T-362); lessons row.
- T-343 r2 outdoor floors (Gate B): WORKED on the second pass (03:32; deck 6.5489118 own vs 6.548912; 3,710 lines byte-identical + 8 added; candidate of record V3.0.25). Decision: T-279 TODO first in lane I.
- T-349 spatter dash binding: WORKED (Gate A PASS 03:37; closure on T-317 residual 0). Decision: F-T349-1 -> T-314 ACCEPTANCE ADDED; NEW T-364 integration (after T-314 and T-326).
- T-357 existing ground / plot / site clearance: WORKED (Gate A PASS 03:53; own plot 470.55 m2, 6 corner marks). Decision: F-T357-3 -> NEW T-358 (groundwater / excavation support); EG coefficients into T-350; client survey item C-1 in RFI B (owner approval needed to send).
- Checker light runs: RFI A citations 36 / 36 checked (21 OK, 15 CORRECTED, 0 WRONG). Decision: Lead applied all corrections in A; wrote B_REMAINING_RFI.md; Checker checks B next.
- Recurring: (1) research-script reproduction refused by the 'run' wrapper (only two tools allowed): covered by each task's test_outputs_reproduce; (2) Drive binaries arrive raw and 'decode' expects base64; one garbled copy (T-356) caught by sha: workers record the decoded sha. Both need only the owner's main chat to change the wrapper if he wants; not blocking.

## 2026-10-30 00:25 (lead run; covers 20:30 - 00:25)

- T-333 r2 blockwork status labels: WORKED (Gate A PASS 20:59; 3 parts 47.3866 m2 -> ASSUMED — OWNER-APPROVED (Q-55 2.20 m door deductions), 156.5697 m2 unchanged; own door widths 0.000 %). Decision: T-279 (blockwork into the candidate) unblocked, after T-343 in lane I.
- T-346 freelancer exterior rows 65/68/69: WORKED (Gate A PASS 20:59; 93.150 = 79.213 bound + 9.000 his double count by position + 4.937 named; ENGINE_RIGHT on the double count). Decision: none.
- T-332 r2 formwork FILL: WORKED (Gate A PASS 22:02; 201 HELD rows blank, unbounded blank; stair row 1.440 .. 1.562 understated -> blank, ENGINE_WRONG corrected). Decision: none; T-199 consumes it (lo/hi exclude HELD_FROM faces: Checker note carried).
- T-348 faces above the pool: PARTIAL then WORKED (REJECTED 22:02 D-T348-1 pier corner arc +0.170 m; r2 PASS 23:10, residual 0). Decision: none; T-314 consumes the new faces.
- T-343 outdoor floor lines (Gate B): PARTIAL (REJECTED 23:05, narrow D-T343-1: deck 7.105836 includes the SX-02 recess 0.561447 m2 that T-127 / T-154 give to the glazing reveal strip; deck by the band face 6.548911 m2; 7 of 8 lines agree by hand). Decision: rework r2 with the exact fault (deck input + closure text + rule + test only); status set to TODO first in lane I (status-word lesson); lessons row added (Checker's).
- T-352 stair formwork side faces: WORKED (Gate A PASS 00:05; 7 / 7 valued faces agree within 2e-6 m2; 16 HELD 0 .. area). Decision: T-199 ACCEPTANCE ADDED (FILL addendum by face id, N-T352-1 V-slot note, F-T352-1 / -2); lessons row added.
- T-347 earthworks binding: READY 23:56 (CHECKER-RUNS, first in queue). Decision ahead of the verdict: F-T347-1 (SB3 held range) -> T-350 acceptance; F-T347-2 / -3 / -4 -> NEW T-356 (lane S investigation); existing-ground reference + site clearance -> NEW T-357.
- Owner decisions applied: T-318 BLOCKED-OWNER -> TODO (option B, lane I after T-279); T-355 first in lane A with the owner's four answers; RFI package revalidated (rfi/A_PRIORITY_RFI.md, C_UNLOCK_MATRIX.md, D_REMOVED_REVISED.md; B next run).
- Recurring: none new; every run since 20:30 closed with a final line; worker 3 took a lane S row (T-347) correctly under the throughput rule while T-343 was not yet rejected.

## 2026-10-29 20:30 (lead run; covers 16:30 - 20:30)

- T-340 reveals / sills / thresholds FILL: WORKED (Gate A PASS 16:58; W02 head 6.331578 x 0.080 = 0.506526 vs 0.5064 own (0.025 %), D-1F-03 / D-1F-04 thresholds 0.000 %; D-GF-10 0.797 width proposal NOT ADOPTED: the wall line overruns the 0.800 frame by 2.961 mm). Decision: none; T-326 / T-327 consume it in lane I order.
- T-339 roof build-up FILL: WORKED (Gate A PASS 17:01; 1F terrace zone 38.355 / footprint 5.553 / finish hatch 31.6433 m2 own; D band ranged). Decision: none; T-328 consumes it.
- T-344 label census V2: WORKED (Gate A PASS 17:10; own run 41 = 28 / 1 / 1 / 11, SILENT_OMISSION 0, V1 byte-identical). Decision: none.
- T-345 porcelain trace: WORKED (Gate A PASS 19:02; 5.890817 m2 traced to 0.000000: concave winder clipped convex +0.353736, F1 / F4 overlap deducted twice -0.057558, residue 2.034669 + footprint 3.559930; net 33.711036 unchanged). Decision: T-246 SCOPE ADDED (consume the trace rows; write a re-netted line's list with its net in the new candidate version file).
- T-338 export line-state text (V3.0.24): WORKED (Gate B PASS FIRST TIME 20:14; 366 lines text / state only, quantities byte-identical; T-334 check 351 REFUSED + 15 FLAG -> 0; L4 NEW 0). Decision: T-343 TODO on V3.0.24, first in lane I; the 4 PROVISIONAL finish lines without canonical deductions go with T-246.
- T-333 r2 / T-346: READY 19:05 / 19:01 (CHECKER-RUNS). T-346 found no missing face (93.150 = 79.213 drawn + 9.000 double count + 4.937 named, residual 0); F-T346-1 -> NEW T-348.
- T-332 r2: NOT CLAIMED for 4 h. Cause: its status cell began 'REJECTED (rework r2 CLAIMABLE ...)'; Worker 1 at 19:21 read every row as non-claimable and idled. Decision: a CLAIMABLE rework now always begins with TODO (row fixed); worker 1 takes it first.
- Missing categories (BOQ_FAMILY_MASTER 1.19.0: 18 NOT_IMPLEMENTED): NEW T-347 earthworks binding + T-350 lines, T-349 spatter dash binding, T-351 kitchen / laundry / pantry tile zones, T-352 stair formwork, T-353 foundation WP lines, T-354 soil treatment evidence.
- Recurring (unchanged, every code agent): Drive raw binary vs base64-only decode (4 runs since 16:30 worked round by hand); the auto prepare left the venv without pytest once more (Worker 1 19:21, repaired by setup).

## 2026-10-29 16:30 (lead run; covers 12:30 - 16:30)

- T-342 M2 label binding: WORKED (Gate A PASS 14:39; Checker own census 41 labels reproduced; AT19 = pool by position inside the water D; pool is a D not a circle, deck 7.9392 -> 7.1058 m2; M2 MET on rooms and openings for P7757 on this ledger). Decisions: NEW T-343 outdoor floor lines (lane I, after T-338), NEW T-344 census tool v2 (lane A) so the tool stops printing SILENT_OMISSION for bound labels; lessons row ADOPTED (research scope).
- T-319 parapet RC line family: WORKED (Gate B PASS FIRST TIME 15:45; candidate of record V3.0.23; 4 lines HELD BLANK with bound >= 8.050943 m3; 2F ring 5.415 m2 -> 1.6245 m3 0.000 %; 3,706 lines byte-identical; L4 NEW 0). Decision: T-338 TODO on V3.0.23; F-T311-C2 band and divider CEC / CED placed in the element register.
- T-341 deductions FILL: WORKED (Gate A PASS 15:45; 40 / 41 lines close; 1F-01 plaster 51.415 own 0.000 %). PARTIAL element: 1F porcelain L-b06400d4 5.890817 m2 UNEXPLAINED, correctly left unfilled. Decision: NEW T-345 trace (lane S) before T-246.
- T-337 exterior plaster / Sigma FILL: WORKED (Gate A PASS 16:06; 2F ring 125.160 / 14.900 own 0.000 %; closure 1,017.948 residual 0). Freelancer rows 65 / 68 / 69 93.150 m2 with no drawn face. Decision: NEW T-346 investigation (lane A).
- T-332 formwork binding: PARTIAL (REJECTED 13:25, narrow r2: FILL writer turns 201 HELD rows into 0.000000 and 25 unbounded rows into 0 .. 0; every re-measure sound). Decision: rework r2 CLAIMABLE, worker 1 first; acceptance = blank m2 / bounds where no bound, test on the committed CSV.
- T-333 blockwork binding: PARTIAL (REJECTED 13:30, narrow r2: 3 established parts 47.3866 m2 deduct a Q-55 2.20 m door yet carry DRAWING-CONFIRMED). Decision: rework r2 CLAIMABLE, worker 3 first (blocks T-279); rule in binding_fill.py with normal + adverse test.
- T-339 roof layers binding / T-340 reveals binding: READY 16:21 / 16:02 (CHECKER-RUNS).
- Supervision note: the 12:30 lane order did not yet carry the two 13:25 reworks, so worker 1 took T-339 next (in its order) and the reworks waited 3 h: no fault of the worker; reworks now first in their lanes.
- Recurring (every code agent, every run): Drive connector saves raw binary, `agent_env.sh decode` accepts only base64; worked round by hand in scratch (5 runs today). The automatic prepare leaves the venv without pytest (Worker 1 16:21, Worker 2 13:44, Verifier earlier; fixed by one `setup`). Both stay in NEEDS FIXING (wrapper is the owner's main chat's file).

## 2026-10-29 12:30 (lead run; covers 08:20 - 12:30)

- T-330 export canonical-deductions check: WORKED (Gate A PASS 09:48; Checker re-ran on V3.0.21: 41 FLAG / 0 REFUSED, hand check L-af9621f4 +15.33 % over-read with an empty list). Decision: FILL table NEW T-341 (lane S) for T-246.
- T-331 wet-room backing fill: WORKED (Gate B PASS FIRST TIME 11:38, V3.0.22; 12 lines hand-checked <= 0.0002 m2, 1F-12 26.305 m2 0.000 %; L4 NEW 0). Decision: T-319 promoted to TODO on V3.0.22.
- T-334 line-state check: WORKED (Gate A PASS 11:42; 350 rebar lines 'held:' text reproduced, quantities consistent). Decision: NEW T-338 (lane I, text / state fix, after T-319); lessons row PROPOSED.
- T-335 ceiling binding: WORKED (Gate A PASS 11:41; kitchen ceiling own 9.630 m2 = decor). Feeds T-284 unchanged.
- T-336 wet-area WP binding: WORKED (Gate A PASS 11:58; pantry floor 13.455, thresholds 0.120 / 0.200 by own handle read, 0.000 %). Feeds T-310; the 10 window up-turns ASSUMED-OA with the drawing reading HELD 0 .. 1.380 m2 stay as passed.
- T-332 formwork binding / T-333 blockwork binding: READY 12:15 (CHECKER-RUNS). T-333 was taken by worker 3 (lane I had no claimable row): allowed by the cross-lane rule.
- Checker M2 census statement: written 10:00, M2 NOT MET on 8 room labels. Decision: NEW T-342 (lane A, gate 1, AT19 first).
- Recurring (every code agent, every run): Drive connector saves raw binary, `agent_env.sh decode` accepts only base64 and no spaces in names; worked round by hand; still in NEEDS FIXING. New this run: this Lead session's venv had no pytest after the automatic prepare (self-check t061 FAIL 'No module named pytest'), repaired by one `setup` (same as 28 Oct 20:20).

## 2026-10-29 08:20 (lead run; covers 04:15 - 08:20)

- T-325 (sills / thresholds ledger) WORKED: Checker own re-measure of 2 doors by their decimal door-symbol handle, W18 sill 0.040 m2, W15 / W16 0.2484 m2 outside the TERRACE-550 outline (no double count); materials UNKNOWN kept. Decision: T-327 (lane I) stays queued after T-326.
- T-315 r2 (wall-tile integration, Gate B) WORKED: candidate of record V3.0.21; pantry base owned once (skirting 185.52 -> 180.12 lm, -2.91 %), every split piece re-measured by hand 0.00 %. Decision: lessons row ADOPTED; cosmetic cut note text -> T-331.
- T-329 (wet-room backing plaster ledger) WORKED: 340.3038 m2 at tile height (owner method, ASSUMED — OWNER-APPROVED), band above tile HELD 0 .. 23.097 m2 (Q-52 C); Checker GF-12 own 25.3011 = ledger. Decision: NEW T-331 (lane I, first) with the Checker's 'band beside every fill' condition verbatim; lessons row ACCEPTED.
- T-330 (canonical deductions check) READY: 92 lines with gross+net, 30 FLAG (plaster / paint 42.302 m2 listed nowhere, skirting 13.569 lm, porcelain 39.308 m2). Decision: Gate A first; its fill folded into T-246.
- Idle runs (Workers 1 / 2 / 3, 06:41 - 07:22): the board had 0 TODO because lane I is serial on the integration files and lanes S / A had no unblocked rows. Decision: binding tables T-332 / T-333 / T-335 / T-336 / T-337 (the measured content each queued lane I package needs, on the current candidate's line ids) + T-334 line-state check; lane I packages then only wire.
- Checker observation (random draw): a STR.REBAR line SOURCE_DERIVED with a 'held:' formula string. Decision: NEW T-334 (population check, no line changed).
- Gap found by the Lead: verdict records (incl. downgrade DG-3521554d) not yet re-bound to V3.0.21 (no verdicts/V3.0.21 folder). Decision: Checker queue item (1).
- Recurring tool issue (unchanged, every code agent, every run): Drive downloads arrive raw binary, `decode` expects base64 (NEEDS FIXING (1)).

## 2026-10-29 04:15 (lead run; covers 00:15 - 04:15)

- T-313 r2 (opening reveal ledger) WORKED: 20 door reveals bound to FIN.PLASTER (17.740 m2 EQUAL), missing scope 13.637 m2 own-confirmed; D-GF-07 line low end 1.28 ENGINE_WRONG (printed 1.400). Decision: NEW T-326 (lane I, reveals into the candidate).
- T-321 (roof build-up) WORKED: T-221 ROOF-430 short by 2.0787 m2 and ROOF-970 on the outer face, both CONFIRMED. Decision: NEW T-328 (lane I).
- T-224 r2 (sunken-slab step) WORKED: free-edge concrete only from a printed step detail; Alsenan effect 0 m3. F-T224-C2 stays with the unwired module.
- T-324 (parapet components) WORKED: inner faces 94.123 .. 99.558, tops 26.836 .. 26.973 m2; coping / drip / beads UNKNOWN -> RFI A13.
- T-322 (FF / lift base) WORKED: the Checker DOWNGRADED the verified footing-blinding component 14.990 -> 12.734438 m3 + FF HELD >= 2.070. Decision: Checker-issued downgrade record on the candidate line; RFI S23; T-319 acceptance checks the export.
- T-323 (slab hatches vs panels) WORKED: no candidate line reads a hatch (ENGINE_RIGHT).
- T-315 Gate B PARTIAL (REJECTED narrow: pantry base carried twice, skirting under full-height tile; tile figures sound). Decision: TODO r2 with the Checker's 4 items, first in lane I; lessons row PROPOSED.
- T-325 (sills / thresholds) READY: 0 DIFFERS, 32 fill proposals, external materials UNKNOWN. Decision: Gate A first; then T-327; RFI A13.
- Recurring cause (new): cross-trade attribution by room name / note instead of by source entity (T-315). Decision: lessons row; T-329 / T-326 acceptance carry 'by id, never twice'.
- Recurring tool issue (unchanged): Drive downloads arrive raw binary, `decode` expects base64; every agent re-encodes by hand (NEEDS FIXING (1)).

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
