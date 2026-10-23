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

## 2026-10-23 20:10 (lead run)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-231 (V3.0.8 Gate B) | WORKED | MERGED 3b042470 (Checker 17:52 run, verdict 19:04): L4 suite to the end NEW 0, 21 lines by hand, straps 3.3905 vs freelancer 3.3925 m3 (-0.06 %), columns 34.446 -> 33.606 | T-211 promoted to TODO, first in lane I; the SB3 / F3 held bound in V3.0.8 is stale (T-230 range) -> carried in T-199 as named |
| T-233 (CONC.FOOTING + BLINDING whole lines) | WORKED (lines PARTIALLY VERIFIED by design) | MERGED 2ecb5bf0; Checker own 26 outlines, 25 footings 64.304 m3 and blinding 15.179 m3 0.0 %; D-32 ruled from the drawing; two PARTIAL REMEASURE records in the verdict file (owner 19:00 (3) met) | footing line waits on Q-31 C (F10 + F), Q-28 A band C1 and D-15 strap level; blinding on D-14, D-15, Q-21 C: all consultant / designer items on record, no new task; D-32 closed in DESIGNER_CLARIFICATIONS; T-235 part (4) may proceed on PARTIAL records only (no VERIFIED claim) |
| T-216 (floor-area line scored) | WORKED | MERGED bebd1241; A COMPARED 385.634 vs 409.58 m2; scorer byte-identical without the flag; candidates rightly HELD (0 .. 0.520 m2, D-13 / D-23) | T-180 slot moved to the FLOOR AREA whole line on run A (Checker 19:05 reading); T-223 (curved room +1.727 UNRESOLVED) first new lane A row |
| T-222 (block HELD bounds part 2) | PARTIAL | MERGED 769cad40; P-GF-05 2.640 m2 Checker 0.0 %; bay basis (+1.481 m2), 1F-W14+W15 junction (+0.302 m2) and the B-B occlusion for P-1F-01 not re-measured (SOURCE-SUPPORTED) | D-60 removed (drawings answer it); D-64 conflict withdrawn by the Lead on two independent readings (B-B occlusion + T-017 census head lines), consultant row 9 narrowed to the P-1F-01 head level, send-ready; T-228 lists the junction piece |
| T-227 (blockwork 3/4) | FAILED on one wall (narrow) | REJECTED 20:14: W16 deducted 4.805 (surround-band crown) vs true arched opening 4.362 m2 (+0.443, 1F-W00 net +3.7 %); 3 other walls AGREE | rework r2 FIRST in lane A (exact fault named in the row); the same misreading sits in merged T-150 / T-175 / T-201: new fix T-238 (gate 1, census of every arched / banded opening, delta ledger, UP-OPEN-ARCH-001); T-211 / T-232 hold W15 / W16 as 4.362 .. 4.805 / 4.650 .. 4.805 until T-238 merges; rows 7 / 8 and the GF-W10 ruling NOT given (3rd run): first items of the 20:49 Checker run |
| T-017 (independent masonry census) | WORKED (held by the backlog rule, correctly) | 59 / 75 walls within 0.05 m, thickness 71 / 71; 9 corner-square RULE_DIFFERENCE; residual 0.000 m per floor x thickness after named items | hand in at worker 2's 20:39 run (READY now 0); UP-MAS-CORNER-001 input to T-228 |
| Process | PARTIAL | two same-agent overlaps (Checker 17:52 run 73 min -> 18:50 stand-down; Worker 1 18:21 run 80 min -> 19:19 IDLE): runs longer than the hourly slot; guard worked, no concurrent work | no schedule change (owner 19:00 / 19:45 Checker exception); reported in team health |

## 2026-10-23 18:20 (lead run)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-229 (beam runs at planted columns) | WORKED | MERGED 3803684e; Checker own B27 4.1927 vs 4.1918 m3 (+0.02 %), B26 +0.13 %; census 1.818 m3 unbilled, 0.278 m3 billed twice | R-BEAM-CONT-1 PROPOSED; wiring is a later lane I package (after T-231 / T-211 / T-232 / T-199, owner order); slab / beam ownership carried into T-234 |
| T-226 (blockwork 2/4) | PARTIAL (by the owner's rule, not a fault) | MERGED a04f8e21; GF-W07 4.458 m2 VERIFIED (first VERIFIED block net; worker 4.468, -0.23 %, cause: sampled piece boundary), 1F-W05 gross 23.223 VERIFIED (worker -0.13 %, cause: last 0.10 m under B23 spread at mean height), net 19.303 SOURCE-SUPPORTED; GF-W10 2 / 4 pieces; D-12 census and column-cut audit not re-measured; the owner's 18:00 GF-W10 ruling (T-201 heads -> 47.425) not given | GF-W10 ruling queued for the 18:49 Checker run with T-227; T-228 carries 4.458 (not 4.468) and 19.303; lesson row (3) accepted (sampled height piece) |
| T-230 (strap / GB ends) | WORKED | MERGED 17ed6f92; Checker own lift-ring ends 2.900 / 3.228 / 5.020 m 0.0 %, SB3 / F3 0.0295 .. 0.2683 m3 HELD (D-15 narrowed), drafting double 0.030 m2 = worker; board text quoted raw coordinates | standing BOARD TEXT rule written (handles and printed values only); ground-beam end corrections wait for a lane I package; T-233 takes the footing side of these intersections as ruled |
| T-227 (blockwork 3/4) | READY | 4 nets newly SOURCE-SUPPORTED (+126.8 m2 with a figure), annex 13 rows HELD on Q-54 B test, lift tie beam HELD | Checker 18:49 (second, after T-231); decides consultant rows 7 / 8 |
| T-231 (V3.0.8 Gate B) | READY | straps 3.3905 m3, columns released 34.446 -> 33.606, planted columns already carried by route G (superseded, not added) | Checker 18:49 FIRST; then T-211 |
| Scout R-09 / R-10 / R-12 (owner one-off) | WORKED | answers + supplements in RESEARCH_LOG 17:50 / 17:55; all PRACTITIONER level | R-12: slab / stair '/m' keeps the A..B range until a project note decides (no task: no project evidence to read); R-10 splice formula (idea 27) used by the next steel procurement task, not now (concrete whole lines first, owner 17:50); R-09 grid reader (idea 26) stays an idea; idea 29 (session id hook) and idea 30 (L4 suite in the background, up to 2 h) need the owner's main chat: NEEDS FIXING (idea 30 is how the complete-suite rule can be met in one Checker run) |

## 2026-10-23 16:20 (lead run)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-212 r2 (gate 0 fix) | WORKED | MERGED b5716930; t202 unedited + t212 + firewall pass on the merged head, own adverse P4 refused; red guard closed after ~14 h | none; hand-in rule (validate on the CURRENT head) kept, 0 rejections since |
| T-215 part 1 (block ends) | WORKED | MERGED 8a9b4b48; Checker own J-A 0.023237 m2 (+0.08 %), Y node 0.0 %; heights not re-measured (DRAWING-CONFIRMED) | part 2 = T-222 now claimable; heights re-measured in T-226 |
| T-174 (straps, Q-74) | WORKED | MERGED 984ebbe1; SB2 / SB3 Checker 0.0 %, strap 3.3905 vs freelancer 3.3925 m3 | integrate (T-231); SB3-in-F3 overlap and all strap ends -> T-230 |
| T-176 (black block units, Q-75) | PARTIAL (by design) | MERGED 41847bff; units / mortar PROVISIONAL; waste, cement, sand HELD (no rule) | stays PROVISIONAL until supplier face + joint are on record (owner 14:20); no new task |
| T-203 r2 (registry 1.2.0) | WORKED | MERGED 40de7c7f; own re-derivation pool / domes / stair retirement, adverse refused | none |
| T-220 (planted columns) | WORKED | MERGED 579e613d; PC-1F-A 0.588 m3 Checker 0.0 %; 5 lines NOT_DRAWN agreed | integrate (T-231); B27 / B26 route G cuts -> T-229; PC-2F double joint -> T-229 |
| T-225 (blockwork 1/4) | WORKED | MERGED 48e6f08a; Checker re-added 74 walls 0.000 m2, both gaps reproduced to cause | T-226 / T-227 promoted (owner order); follow-up evidence 96500525 feeds T-017, not merged separately |

## 2026-10-23 14:20 (lead run)

- **Worker 1 11:25 -> 11:42 / Checker 12:51 -> 13:11**: T-213 MERGED 0ec8c496 -> **WORKED** (one set of 6 sunken panels
  under two storey conventions, residual 298 -0.0100 m2; slab concrete 3.9658 m3 unchanged; checker own hatch re-measure
  0.0 %; drop HELD under D-41). Decision: the M8 SLAB_STEP bound becomes T-224 (lane I, new method version, queued).
- **Worker 2 11:41 -> 12:02 / Checker 13:11**: T-209 MERGED 949c2312 -> **WORKED** (wet-wall tiles 340.41 m2 owner method on
  12 rooms, 6 HELD; like for like +4.28 % decomposed to 0). Decision: into the finishes package T-211 (V3.0.9).
- **Worker 2 10:41 -> 11:17 / Checker 13:11**: T-212 r1 REJECTED -> **PARTIAL** (property right, validated on d5df7d1f; on
  the head merged with V3.0.7 the new property caught arch_v307.py unclassified). Worker 3 13:01 -> 13:56: r2 READY
  (GUARD_HOST + new P4 import property) -> first at 14:49, on the head merged with 0a622a86.
- **Worker 3 11:00 -> 11:30 / Checker 13:11**: T-203 r1 REJECTED -> **PARTIAL** (registry right as_of V3.0.6, but V3.0.7
  merged first and changes B10-09 / B10-10 by the file's own definitions). Decision: narrow r2 first in lane I.
- **Worker 1 12:27 -> 12:44 / Checker 13:53 -> 14:07**: T-214 MERGED b29060c2 -> **WORKED** (0.05 m drawn layer under every
  dry FFL, DRAWING-CONFIRMED by the checker on DWF geometry + a 400 dpi scan; wet / sunken / roof HELD). Decision: the
  held zones become T-221 (lane S).
- **Worker 1 13:23 -> 13:46 / Checker 14:07**: T-217 MERGED 65fef8fa -> **WORKED** (26 CONFLICT member-storeys, C8 0.900 ..
  1.0125 m3 GF, lift necks 0.55 .. 0.75 m3/m; 6 drafting notes ENGINE_RIGHT; 3 planted columns no line; 5 released upper
  lines UNKNOWN). Decision: planted columns + the 5 lines = T-220, first in lane S (they block the column line together
  with D-16 / D-63, which stay with the designer; D-16 / D-63 rows updated).
- **Worker 2 12:41 -> 13:07 / Checker 14:07**: T-218 MERGED 0a622a86 -> **WORKED** (kitchen 9.630 m2 WET by Q-30 A: wet
  62.49 -> 72.12 vs 72.01 m2, +0.15 %; bedrooms re-paired; floor like for like +2.464 m2 closed to named parts). Decision:
  the kitchen re-code joins T-211; the curved 1F room +1.727 m2 UNRESOLVED + dressing / strip = T-223, first in lane A.
- **Worker 2 13:42 -> 14:08**: T-215 part 1 READY -> pending (GF ends + G-T108-1 closed from drawn faces, +1.214 .. +1.241
  m2 gross). Decision: part 2 (1F bay, P-1F-01, P-GF-05) = T-222 after T-215 merges; P-1F-01 plan / section conflict =
  designer item D-64 (new).
- **Process**: 7 / 7 slots since 12:20 STARTED + final SUCCESS; 5 merged, 2 rejected (both narrow, both because the hand-in
  was validated on a head older than the latest merge). Decision: every hand-in now merges the CURRENT head just before
  the push and lists the merges since the claim (board note 14:20). Checker row / scoreboard stamps ran 5 - 28 min ahead
  of its commit times: told to stamp with `date -u`.

## 2026-10-23 12:20 (lead run)

- **Worker 1 10:20 -> 10:39 / Checker 10:53 -> 11:52**: T-205 MERGED 5f40dfdb -> **WORKED** (necks released 10.855 vs
  freelancer 8.805 m3, +2.0505, reconciled to 0.000 in four named causes; drawing-derived neck = footing top -> GB top,
  every neck HELD on two unprinted terms; checker re-derived 0.0 %). Decision: the two printed section conflicts it found
  (C8 D-16, lift group new D-63) become T-217; the build-up term b is T-214 (now first in lane S). Lessons row added.
- **Worker 2 09:40 -> 10:02 / Checker 11:52**: T-208 MERGED 54cb4c42 -> **WORKED** (3 hand-wash spaces bound WET by Q-06 A,
  9.348 m2, checker 0.0 % on 2 of 3). But the scoreboard still shows floor area NOT YET MEASURED: no scorer reads the
  binding. Decision: T-216 (key-map opt-in path, first in lane I); its named residuals (1F bedrooms -1.379, strips
  +1.300) and the FOUND kitchen dry-vs-Q-30 A -> T-218.
- **Worker 3 09:01 -> 10:05 / Checker 11:52**: T-193 Gate B MERGED e866328a -> **WORKED** (V3.0.7: pool base + walls 7.202
  and terrace dome shells 5.081 m3 in the candidate, DOME-B billed once, 3,535 lines byte-identical, all 10 changed lines
  0.0 % by hand). Decision: T-199 (V3.0.8 formwork + railings) promoted to TODO.
- **Worker 2 10:41 -> 11:17**: T-212 READY (gate 0 fix of the red guard test) -> pending verdict; first in the 12:49 queue.
- **Worker 3 11:00 -> 11:30**: T-203 READY (registry 1.2.0) -> pending; as_of V3.0.6 while V3.0.7 merged meanwhile: the
  checker passes it only with the as_of stated and unchanged states, else a narrow rework.
- **Worker 1 11:25 -> 11:42**: T-213 READY (one set of sunken panels under two storey conventions, residual -0.0100 m2;
  step concrete 0 by geometry; drop HELD) -> pending. Its note on the opt-in M8 SLAB_STEP bound (4 sqrt(A) wrong twice)
  goes to 'Later' for lane I, after T-213 merges.
- **Worker 2 11:41 -> 12:02**: T-209 READY (wet-wall tiles 340.41 m2 on 12 rooms, 6 HELD; like for like +4.28 % fully
  decomposed, residual 0) -> pending.
- **Process**: every slot since 10:20 closed (8 / 8 STARTED + final, plus one checker overlap-guard run at 11:50 that
  stood down correctly). The red guard test stayed on the working branch about 3 h because the fix went READY after the
  10:53 checker run had started (it was not in that run's queue); now first. Row stamps of T-203 / T-205 disagree with
  their RUN_LOG lines (cosmetic; workers told to stamp with `date -u`).

## 2026-10-23 10:20 (lead run)

- **Worker 1 08:20 -> 08:42**: T-204 MERGED 4fbf7627 (Checker 09:11) -> **WORKED** (lift pit drawn and detailed on ST PDF
  p.14, missed by the DXF-only search: ring 1.600 m2 gross / 1.100 m2 net of the 4 column sections, checker own 0.0 %;
  freelancer lift walls 2.400 m3 bill 0.500 m2 of columns twice, ENGINE_RIGHT on ownership; pit depth 'as per lift
  manufacturer' HELD; roof tank not drawn, HELD). Lessons row added (absence only after every format, incl. image-only PDF).
- **Worker 2 08:40 -> 09:02**: T-207 MERGED e081911c -> **WORKED** (W11 / W12 4.290 m2 each between the shutter leaves,
  checker VERIFIED, freelancer 7.800 used the frame height: ENGINE_RIGHT; windows like for like 88.081 vs 89.681 m2 on 28,
  -1.78 %; W02 one opening on every drawing, HELD on the render only; P-GF-05 needs a lintel). Remaining masonry above
  the leafless openings -> T-215.
- **Worker 2 07:40 -> 07:56 / Checker 08:51 -> 09:11**: T-108 r2 MERGED 01eeafd0 -> engineering **WORKED** (2F-W08
  11.400 / 9.640 m2 and GF-W22 2.887 m own = ledger 0.0 %; established net 337.412 m2, 58.366 m3; junction piece inside a
  HELD bound, G-T108-1), process **PARTIAL**: the merge turned tests/t202_guard_sweep red on the working branch (Checker
  09:59 G-T206-2; no quantity effect). Decision: gate-0 fix row T-212 (first in lane I, any worker may claim it); gate b
  now runs the guard tests on the head MERGED with the working branch (VERIFIER QUEUE 10:20 + lessons row); held bounds
  -> T-215.
- **Worker 1 09:20 -> 09:42 / Checker 09:51 -> 09:59**: T-206 MERGED d5df7d1f -> **WORKED** as an investigation (footing
  underlay 5 / 2 / 10 cm read from the vector PDF, checker own read: footing bottom = formation + 0.17; formation and
  existing ground still HELD by Q-21 C; 6 sunken wet panels found, drop not printed; B20 / B23 condition NOT PROVEN).
  Decisions: T-213 (sunken panels, reconciled with T-139 / D-41: GF + 1F there vs 1F + 2F here), T-214 (floor build-up,
  drawing-derived beside Q-43's 0.10 within its own scope; D-40 / D-39 not duplicated); T-170 now after T-205.
- **Worker 3 09:01 -> 10:05**: T-193 (V3.0.7) READY -> pending Gate B (first in the 10:49 run). **Worker 2 09:40 ->
  10:02**: T-208 READY -> pending Gate A (second).
- Checker T-180 slot: columns 17 -> 23 / 59 own-measured, all 0.0 % (COL-2F-51 / -53, COL-GF-06, COL-GF-15, COL-GF-18,
  COL-2F-55); line PARTIALLY VERIFIED.
- **Recurring cause 7 RECURRED** (new module trips a whole-repo guard test the task's own tests do not run): this time the
  test passed on the task head and failed only on the merged head. Decision above; the Checker's own gate b is part of
  the fix, not only the worker's.

## 2026-10-23 08:20 (lead run)

- **Checker 05:51 -> 06:28**: T-187 (Gate B, V3.0.6) MERGED 8a6d604a -> **WORKED** (own reproduction of three runs,
  3,527 lines identical + 7 changed + 6 added, all 13 by hand within 0.0 %; MS2-U now VERIFIED 1.0014 m3; the 4.451 m3
  'winder' confirmed a dome, held MISREAD; 2 evidence findings G-T187-1 / -2 carried into T-193). T-197 MERGED 97cd747e
  -> **WORKED** (4 curved-geometry cases from DXF handles; no quantity moved). T-191 r2 MERGED bc0ab0cb -> **WORKED** (base
  mats A .. B, R1 824.89 .. 883.59 kg, R2 572.45 .. 617.96 kg, counts = checker 0.000 kg; line HELD on D-57). T-196 r2
  MERGED f933ef8a -> **WORKED** (one element per physical column: GF C2 12 -> 4; elements 834 -> 656).
- **Worker 2 05:40 -> 06:15**: T-201 MERGED 5dade783 -> **WORKED** (window heads 8 -> 26 / 29 from the never-opened
  vector DWF; checker 0 mm on W09 / W10 / W24; windows on the 18 new 22.730 vs his 26.950 m2, -15.66 %, his flat 2.00 m
  height). The 3 still HELD -> T-207.
- **Worker 1 06:21 -> 06:42**: T-200 MERGED d699b650 -> **WORKED** (level chain; arch and structural one datum; every
  structural level and the foundation chain HELD; 4 known errors re-found). Run 2 not done and the necks UNRESOLVED ->
  T-205 (necks), T-206 (ST PDF levels, per-footing chains); T-170 now after T-206.
- **Worker 2 06:40 -> 06:57**: T-108 REJECTED 07:13 -> **FAILED as handed in** (gates e + h: the hand run used where the
  physical T-stem run governs). Decision: rework r2, done in 43 min, READY 07:56 (established net 337.412 m2, -5.8 %;
  hand run kept as comparison), first in the 08:49 checker run.
- **Worker 3 07:00 -> 07:42**: T-202 MERGED 210ce4f0 -> **WORKED** (48 merges swept; firewall registry complete; ledger
  explains all 396 failing ids, none from the window). Follow-ups K1 decision record, pymupdf registration, worktree gitdir
  -> T-210; 'known_failures check: NEW 0' now required in every READY gate b.
- **Worker 1 07:21 -> 07:39**: T-188 MERGED fb3a4623 -> **WORKED** (element inventory + storey continuity; 4 known cases
  reproduced; NEW: lift walls / pit and the roof tank have no structural line in any state). Decision: T-204 first in
  lane S; register rulings LIFT-01 / TANK-01.
- Recurring cause 8 (stale map) did not recur in this window (every handoff regenerated the map last). New process gap:
  pilot_metrics.py counts 0 merges in a window with 8 (auditor to fix; Lead edits no dashboard code).

## 2026-10-23 04:20 (lead run)

- **Checker 23:51 -> 01:15**: T-179 r2 (Gate B V3.0.5) MERGED 90d0b769 -> **WORKED** (22 stair / strip highs on count B,
  each re-derived 0.00 kg; released rebar 10,250.17 kg and beams 65.294 m3 unchanged; NOT RELEASED); T-163 r3, T-194,
  T-195 MERGED -> **WORKED** (classified 00:20).
- **Main chat 00:32 / checker 01:52**: T-190 MERGED 465e0015 -> **PARTIAL**: the gate fix WORKED (firewall green on the
  working head again after 9 h red), but parts 2-3 (sweep list, KNOWN_FAILURES ledger) not delivered. Decision: T-202
  (lane I, gate 1).
- **Worker 1 00:20 -> 00:46**: T-192 MERGED 86fd5f42 (01:57) -> **WORKED** (MS2-L 1.0589 -> 1.0334 m3 VERIFIED by the
  checker's own riser / B20 face read, 0.0 %; system 6.6479 m3 PARTIALLY VERIFIED). Board slip: the row stayed READY
  after the merge; the Lead restored it from the merge commit and the checker's RUN_LOG line.
- **Worker 3 01:00 -> 01:52**: T-196 REJECTED 02:08 -> **PARTIAL**: the crosswalk is right on footings (F4 2 x 1.76 =
  3.52, 0.0 %) but counts ~3 register elements per physical column (GF C2 12 vs 4 drawn): element identity, not the
  crosswalk logic. Decision: r2 first in lane I (collapse to one element per column per storey + adverse tests); register
  ruling 04:20.
- **Worker 2 01:40 -> 02:02**: T-198 MERGED 57bb0411 (03:56) -> **WORKED** (checker own DXF: W01 1.00 / 3.00, W03 0.00 /
  4.30 above FFL; deltas re-derived). Follow-up for the 21 headless windows and the three new openings' heads: T-201.
- **Worker 1 02:20 -> 02:35**: T-191 REJECTED 03:58 -> **PARTIAL** (walls, hoops and outline re-measure 0.0 %; base mats
  counted only at max spacing + 1, an interpretation proven for footings carried to a mesh without its own evidence (ERS
  s.3), low end about -14.45 kg R1 / -10.63 kg R2; codemap stale). Decision: r2 first in lane S, narrow.
- **Worker 3 03:00 -> 03:55**: T-187 (V3.0.6) READY -> pending Gate B (first at 05:49). Lead review: found that the
  candidate's 1F 'winder stair' 4.451 m3 is a dome outline: a misread element in the released-route lineage; HELD here,
  retired in T-193 (register ruling).
- **Worker 2 03:40 -> 04:02**: T-197 READY -> pending Gate A (second at 05:49).
- **Checker T-180 slot**: columns 8 / 59 re-measured own, all 0.0 % (COL-GF-10 0.750, COL-1F-44 0.444, COL-1F-36
  0.380, COL-GF-11 0.9375, COL-GF-17 0.700, COL-2F-54 0.380 m3 this cycle).
- **Recurring cause 8 (new name): stale docs/CODEMAP.md at handoff** (D-T179-2 at 21:04, D-T191-1 at 03:58; the workers'
  self-gate said 'c PASS' both times): the map is built, then a file is added or the working branch merged after it.
  Decision: every row now says "regenerate docs/CODEMAP.md as the LAST commit and run `codemap check` on the pushed
  head"; the queue note repeats it. If it repeats again, the Lead asks the main chat for a pre-push check in the wrapper.
- **Recurring cause 9 (new): worker clock stamps in rows** (T-197 '04:40' written at 04:02, T-187 '04:10' at 03:55):
  harmless today, but the dashboard's READY-age measure reads them. Decision: queue note asks for `date -u` stamps.

## 2026-10-23 00:20 (lead run)

- **Checker 19:51 SUCCESS (21:04)**: T-164 MERGED -> **WORKED** (RL-02 4.921 / RL-03 7.967 m own DXF, 0.0 %; RL-04 kept
  HELD in both chains). T-179 r1 (Gate B V3.0.5) REJECTED -> **PARTIAL**: runs reproduced, west ring 0.7552 m3 confirmed,
  but 22 stair / strip held highs used count A at both ends (-65.02 kg) and codemap stale. The checker named its own 06:25
  miss (it merged the T-166 ledger with that fault). Decision: r2 by worker 3 (done 23:39, READY); lesson row below.
- **Worker 3 21:01 -> 22:00**: T-181 MERGED 21:56 -> **WORKED** (doors / windows like for like, windows 56.771 vs 54.931
  m2 on the same 8, +3.35 %; window pcs set HELD by the checker: W02 unclassified). Decision: T-150's '29 AGREE' becomes
  HELD in the census r3 (T-198).
- **Worker 1 20:21 -> 20:40**: T-163 r2 REJECTED 22:00 -> **PARTIAL** (column joint fix verified, -0.06 %, but dome shell
  formwork set to 0 on the client change and the dome-opening band counted in both slab edges and the ring). r3 (22:20 ->
  22:27) MERGED 00:10 -> **WORKED** (S0 soffit 2 x 24.150 m2 checker 0.00 %; band owned by the ring; ScenarioLeak guard +
  adverse tests). Register ruling 00:20.
- **Worker 2 21:40 -> 22:12**: T-194 MERGED 00:09 -> **WORKED** (R6: 71 openings, all four elevations bound; checker own
  W14 / W17 0 mm). Findings become work: T-198 (three openings missing from the list, W01 / W03 levels on the wrong datum,
  windows pcs HELD) and D-59 / D-60; T-176 now waits on T-198 (its net area changes).
- **Worker 2 23:40 -> 00:01**: T-195 MERGED 00:50 (checker stamp) -> **WORKED** (R9: 31 sheets, 0 citation outside the
  register; no revision printed anywhere). Decision: D-61 (two dates in the ST set) and D-62 (sheets not issued) to the
  designer list; scope cross-check R7 opened as T-196 (lane I).
- **Worker 3 23:00 -> 23:39**: T-179 r2 READY (fixed count B high end, +65.04 kg; NOT RELEASED); first in the checker's
  open run. Lane I chain T-190 -> T-187 -> T-193 -> T-199 waits on this merge; T-168 promoted so worker 3 has claimable
  non-chain work.
- **Firewall test**: still red on the working head since the T-186 merge (17:00; every run since reports the same single
  failure). It cannot be fixed before T-179 merges (same registry file). Decision: unchanged, T-190 first in lane I; the
  checker treats it as gate 0 the moment it is READY. Recurring cause 7 holds; every new-module row carries the firewall
  test in its acceptance.
- **STALL_CHECK T-176**: worker 2 passed it twice by its lowest-gate-first rule (gate 3 vs the gate-1 review rows): a
  reprioritisation, not a failure; it now waits on T-198 for a real dependency.
- Lessons rows proposed (standard s.7; the main chat owns the register): (1) T-179 r1: a held count A .. B gives a range
  whose high end uses count B; a ledger copying one count into both ends is a wrong range, not a narrow one -> check the
  high end against the high count (tests in t179 ledgers); (2) T-163 r2: a client-change scenario leaked into a derived
  trade (formwork 0 for the domes) -> a scenario tag carries into every derived trade (ScenarioLeak guard, t163); (3)
  T-194: a listed sill / head is a notation without its datum until bound to a level-marker block (t194); (4) T-195: a set
  with no printed revision is controlled by file identity; cite set + page, not part-file page (t195).

## 2026-10-22 20:20 (lead run)

- **Checker 15:51 (closed 16:30)**: T-158 MERGED 16:28 -> **WORKED** (owner stair rule UP-STAIR-015 in overlay URBAN_RULES
  1.6.0 + unwired calculator; owner table 6 / 6; L4 396 = 396 same ids).
- **Checker 16:52 SUCCESS (17:20)**: T-186 MERGED -> **PARTIAL**: guard right (villa Q ring 3.883573, pool 10.865210 m3
  re-derived), but the merge 18b12176 broke a whole-repo gate: `test_every_rebar_module_in_engine_is_declared` fails on
  the working head (default_guard.py undeclared; Lead re-ran it 20:15). Recurring cause 7 REPEATED (first T-097 / T-056 on
  2026-10-20): the row's acceptance did not name the firewall test and the Checker's gate b ran only the impact-level
  folders. Decision: fix task T-190 at the top of lane I (after T-179, same registry file) with a known-failure register;
  every new-module row now names the firewall test (T-194 does); the queue note tells the Checker to run it in gate b.
  T-182 MERGED -> **WORKED** (five measures, default layout unchanged). T-175 MERGED -> **WORKED** (own DXF deductions
  3.520 / 3.960 m2, 0.0 %). T-173 MERGED -> **WORKED** (W face own 66.049 vs 66.15 m2, -0.16 %; D-T173-1 roof panel T 18,
  below 1 %; open south side ENGINE_RIGHT). T-180 slot found the stair / beam double count D-CHK-T180-1 (-0.115 m3) ->
  owner made it T-189.
- **Checker 17:52 SUCCESS (18:01)**: T-128 r3 MERGED -> **WORKED** (1F-11 contour 22.1507 vs 22.149 m, owner net 59.45 m2,
  0.0 %; a third room 0.0 %). T-185 MERGED -> **WORKED** (2 terrace dome shells 5.081 m3 VERIFIED; engine 7.372 ENGINE
  WRONG +2.291; tower dome, rings, shell bars HELD). Decision: verified pool + dome concrete into the candidate as T-193.
- **Worker 3 17:00 -> 18:26**: T-179 READY (V3.0.5 Gate B package; rebar quantity lines 12,834.52 -> 10,250.17 kg with the
  route slab provisional superseded; beams 64.820 -> 65.294 m3, west ring double count removed). Finding: pool steel
  BLOCKED because T-166 lengths stand on the 1.15 m finished depth while T-183 r2 verified 1.20. Decision: T-191 (pool
  bar populations rev2 on the verified geometry). New lesson: a verified change must flag every ledger derived from it.
- **Checker 19:51 (open at 20:20)**: T-189 MERGED 20:25 (B20 / B23 own 0.990 / 1.11375 m3, 0.0 %) -> **WORKED**;
  follow-ups (route G stair line into B20 about 0.065 m3, flight feet and landings vs slabs) -> T-192, now claimable.
  T-178 MERGED 20:35 -> **WORKED** (7 lessons, each with a broken variant failing). T-179 still in the run.
- **Worker 2 19:40 -> 20:11**: T-164 READY (railings 38.916 lm DRAWING-CONFIRMED, shutters 6 leaves, m2 HELD; GF sea strip
  RL-04 conflicts with the T-162 parapet chain). Decision: register ruling (HELD in both, quantity in neither) and a
  checker item in the queue.
- Lane S / A had no claimable new piece after T-189 / T-164 except reworks: added T-191, T-192 (S), T-194, T-195 (A, owner
  review plan R6 / R9), T-193 (I); T-176 and T-181 claimable (T-175, T-182 merged). Queue check 0 flagged.

## 2026-10-22 16:20 (lead run)

- **Checker 13:52 SUCCESS (15:04)**: T-184 MERGED -> **WORKED** (staircases: ST-01 = stair beside the lift GF -> 2F, ST-02 =
  round stair GF -> 1F; own flights MS2-L 1.059 / RS-S 0.972 m3 = ledger 0.0 %; engine storey loss D-T184-1 -2.598 m3
  confirmed in code). Decision: the fix enters the candidate through new T-187 (with the default guard), after T-179; the
  storey-continuity check becomes T-188 (owner review plan R2 / R3). T-171 MERGED -> **WORKED** (per-metre = max spacing;
  kg HELD on the unprinted leg diameter only). T-150 r2 MERGED -> **WORKED** (W14 0.0 %). T-167 Gate B PASS -> **WORKED**
  (V3.0.4: 84 profile-based lines HELD, 3,048 byte-identical, 2 random lines OK, 0 defects). Decision: T-179 TODO now.
- **Checker 15:51 (open at 16:20)**: T-172 + T-162 r2 MERGED as one pair -> **WORKED**. T-183 r2 MERGED 16:14 ->
  **WORKED** (condition (c) 1.200 m and the upstand 1.350 m2 re-read by the Checker from the cut, 0.0 %; concrete scope
  VERIFIED, line PARTIALLY VERIFIED on the held steel; side finding: the architectural cut draws the base 0.15 vs the
  structural 0.40: structure governs thickness, architecture the levels, consultant item C10). T-128 r2 REJECTED ->
  **PARTIAL**: GF master bed 0.02 %, but 1F-11 contour 22.350 vs 22.150 m (+0.9 %; owner net +1.25 %) from a polygon leak
  into the glazing-frame cavity at both W17 jambs, plus the jamb fillet arcs mislabelled VIRTUAL. Decision: rework r3
  exactly as the Checker listed (first in lane A); everything else in r2 stands.
- **Worker 1 12:23 / 14:21**: T-184 READY (above) and T-183 r2 READY in an 11-minute run (small exact rework; fine).
- **Worker 2 13:42 / 15:41**: T-175 READY (43 walls carry a net, 28 openings HELD; 2 openings missing from the T-150
  census found) and T-173 READY (shaft walls: owner manual 142.22 gross beside drawing-derived 171.88 .. 175.14 m2; his
  204.42 closes to 0). Decision: T-176 waits for the T-175 verdict (needs its net area); T-164 made backlog-permitted.
- **Worker 3 13:01 / 15:03**: T-186 READY (default guard; on baseline A it holds 14.554 m3 and 1,885.36 kg and finds 3
  silent omissions) and T-182 READY (five measures as opt-in v2.1 layout; dashboard parser not yet reading the v2.1
  heading: main chat). Decision: both in checker RUN 1 (unblock T-187 and T-181).
- **Owner session 15:15 / 15:55** applied, nothing undone: T-185 first in lane S; T-183 r2 first for the Checker (done);
  WORKFLOW_CONTROLS section 10 file ownership respected (the standard's lessons register is the main chat's file now: the
  Lead proposes rows in its report instead of editing it).

## 2026-10-22 12:20 (lead run)

- **Checker 11:51 SUCCESS (12:07)**: owner 11:50 item first. T-183 pool REJECTED -> **PARTIAL**: base 10.9356 m2 x 0.40 =
  4.374 m3 VERIFIED, ring, curved part, no pump room and no steps in any document all AGREED; one real fault: the 1.15 m
  finished water depth used as the RC wall height (structure line gives 1.20: walls 2.828 not 2.710 m3, pool 7.202 not
  7.084, -1.6 %) and a 0.15 m upstand denied. Decision: rework r2 (exact two faults + adverse test), second in lane S after
  T-184 (owner order); lessons row added. T-177 MERGED -> **WORKED** (scoreboard v2 by script; checker reproduced baseline A
  b96185d4 and the held column by hand). T-163 formwork REJECTED -> **PARTIAL**: bay GF-032 and shaft faces 0.0 %; column
  joint faces +12.0 % on COL-GF-19 (through / flush beam taken at full face width, oblique B27). Decision: rework r2, third in
  lane S; joint line 14.224 m2 and beam sides 288.711 m2 NOT VERIFIED meanwhile; lessons row added.
- **Checker 09:52 SUCCESS (10:24)**: T-140 MERGED -> **WORKED** (head merge only). T-169 MERGED -> **WORKED** (GF-W29 0.553 m
  = engine 0.0 %). T-162 r1 REJECTED -> **FAILED** on gate h (corners in m2 after the 07:10 correction; parapets not split):
  reworked by worker 2 as r2 (READY 11:53, corners one m.l line, payable half kept apart). T-180 pool slot: causes in m3
  handed to T-183.
- **Worker 1 08:32 / 10:38**: T-171 READY (notation = maximum c/c spacing; 2,769.06 .. 2,829.83 kg HELD on the unprinted leg
  diameter; Q-71 option arithmetic shown wrong in two of three) and T-183 READY (above). Both within the standard (element,
  reconciliation, rule, test, lessons row). No owner question raised: correct under 2.7.
- **Worker 2 10:09 / 11:53**: T-172 READY (parapets and corners as physical items; his 1,297.35 m.l reconciled cell by cell
  to 271.962 m.l of parapet arrises etc.; payable 648.675 and the 1.25 KWD rate kept apart) and T-162 r2 READY. Decision:
  checked as ONE pair (T-172 owns the physical items; register 12:20).
- **Worker 3 09:01 SUCCESS; 11:01 STARTED, no final line yet** (scheduler PENDING, T-167 CLAIMED 11:08): still running at
  12:20, not yet an INCOMPLETE run; re-check at the next Lead run.
- **Owner session 09:05 / 09:40 / 11:50** applied, nothing undone: T-184 first in lane S, T-049 marked SUPERSEDED (pool by
  T-183, domes stay in S0 by T-185; its "dome part closed" text withdrawn), T-186 first claimable in lane I after T-167.

## 2026-10-22 08:20 (lead run)

- **Checker 07:51 SUCCESS (finished 08:17, during this Lead run)**: T-132 SCOREBOARD v2 written (concrete WAPE A 17.03 % / V3.0.3
  15.38 % on 3 of 8 compared; verified share 0 / 8 whole reference lines; doors / windows m2 refused: engine counts pcs);
  MERGED T-151 r2 (Gate B a-c PASS, 47df193) and T-157 (554c1c4, porch 10.680 m2 own 0.0 %); T-140 all gates PASS but a merge
  conflict in rebar_product_registry.py. Decisions: T-157 WORKED; T-151 r2 WORKED (Gate B); T-140 back to worker 3 for the
  head merge only; the checker's new T-177 (scoreboard columns by script) ranked first in lane I; my integration task
  renumbered T-179.
- **Checker 06:23 SUCCESS**: MERGED T-166, T-160, T-165, REJECTED T-151 (slice a); own re-measures 0.0 % (stair MS1-U 59.656 kg,
  pool R1 verticals 165.03 kg, west dome ring 0.7553 m3); both baselines reproduced byte-identical. Running since 07:51 (T-132 first).
- **T-166 stair / pool / tank steel: WORKED (MERGED a9e1d63)**. Pool steel HELD on D-57, tank walls not drawn. Into T-179.
- **T-160 dome rings: WORKED (MERGED b5da75b)**: no double count; risk noted (frozen M8 _dome uses the full annulus, 0 on
  Alsenan). Decision: lesson + regression test in T-178; integration in T-179.
- **T-165 release baseline: WORKED (MERGED 37124da)**: the 04:20 ruling (run A released, run B comparison base) now rests on
  merged pinned specs. Decision: T-168 claimable now.
- **T-151 V3.0.3: PARTIAL (REJECTED slice a, D-T151-1: 18 link lines dropped their upper-path readings, held upper bound
  understated by 415.62 kg)**. Worker 3 fixed exactly that (r2 READY 34765d8, only 18 records differ, highs only, new test
  fails any dropped reading). r2 MERGED 08:12; T-167 -> T-179 -> T-146 now open in that order.
- **READY since 04:20, pending the checker (Lead review, no fault found)**: T-163 formwork 1,038.533 m2 above ground +
  held ranges (draft face rule overstates beam sides +13.4 %: learned, the hand walker deducts junctions); T-169 jamb-stub
  fix (68 of 72 runs byte-identical); T-150 r2 (Lead ruling on F22 / D-GF-06: rectangular 2.200 m2 with fallback height,
  arched-head increment HELD on D-58); T-158 stair rule calculator (owner table 6/6); T-128 r2 (GF master contour = checker
  0.0 %; shaft HELD -> T-173).
- **Owner directive 08:05 (engineering reasoning standard)**: Q-71 / Q-72 / Q-75 became investigations, Q-73 / Q-74 answered,
  corners settled by the 07:10 notes correction. Decision: the 04:20 owner-package items (Q-71, corners) are withdrawn;
  R-11 closed; R-12 opened for T-171 ("n ø d/m" meaning, evidence level 4 only); new T-178 carries section 4 rules + tests
  for merged pieces; transition rule for the 9 READY rows written in the VERIFIER QUEUE.
- **Recurring cause 9 (new)**: worker board rows carry clock times 40-60 min ahead of their own RUN_LOG lines (T-128 r2 row
  "09:05" written 08:08; T-150 r2 "06:35" vs 05:46; T-163 "05:20" vs 04:44; T-169 "05:52" vs 05:11). No quantity affected.
  Decision: report to the main chat (prompt wording "UTC time" should say "from `date -u`").

## 2026-10-22 04:20 (lead run)

- **Checker 00:38 / 02:45 / 04:02 SUCCESS**: 11 merged since 00:20 (T-155 r2, T-142 Gate B, T-139 r2, T-152, T-125, T-143,
  T-147, T-154, T-159, T-161; T-155 counted at 23:53), 2 rejected (T-128, T-150). It cleared every item queued for it, in order.
- **T-142 V3.0.2: WORKED (MERGED 5de8657, Gate B PASS)**: one evidence-text defect D4, fixed inside T-151.
- **T-152 slab steel, T-139 r2 slabs, T-155 r2: WORKED (MERGED)**.
- **T-125 MASONRY_CENTRELINE_V2: PARTIAL (MERGED, defect D-T125-1)**: a 0.053 m jamb stub absorbed into a free-end doorway.
  Decision: new T-169 (lane A, permitted) before T-108.
- **T-143 block by hand: PARTIAL by design (MERGED)**: 214.36 m2 PROVISIONAL counted HELD by the checker; net on Q-73, black
  count on Q-75. Decision: the checker's status mapping binds T-108; nothing else.
- **T-147 ceilings: PARTIAL by design (MERGED)**: drawing-derived bulkheads 175.76 m2 HELD (D-40), coves / wet board HELD.
  No action beyond the designer list.
- **T-154, T-159, T-161: WORKED (MERGED)**. T-161 defect D-T161-1 (main door must be HELD after its own DIFFERS finding) and
  the checker's observation on T-159 (0.200 m projecting outline outside the SE faces) -> T-150 r2 and T-164.
- **T-128 plaster / paint both methods: FAILED (gate e)**: walked the straight court line, not the curved glazing (+1.7 % on
  the checker's room); one door with two widths. Decision: T-128 r2 rework with the exact faults (permitted).
- **T-150 doors / windows: FAILED (gate f)**: W16 kept as INFERRED 4.805 m2 (not a s.5 status), main door not HELD after the
  render finding. My 00:20 register line kept the main door as printed: that was wrong under WORKFLOW_CONTROLS s.8;
  corrected. Decision: T-150 r2 (permitted), four exact faults.
- **T-165 release baseline: WORKED pending** (both runs reproduced, provenance traced). Decision: Lead RULING, released
  baseline = run A (no profile), run B = comparison base; new T-167 (V3.0.4 holds candidate lines resting on DIFFERENT /
  NOT_PRINTED profile values; Q-17 A data file = spec C) and T-168 (Gate B tool checks manifests).
- **T-151 V3.0.3 steel package: WORKED pending Gate B, OVERSIZED** (1,880 structural rows). Decision: three Gate B slices.
- **T-157 outdoor areas: WORKED pending**: porch floor 10.680 vs the owner's "about 19.181" = the soffit over porch + entrance
  stair (19.220); yard like for like -0.37 %. Decisions: register rulings; thresholds HELD to the designer (D-55), riser
  flag D-56 (no owner question).
- **T-160 dome rings, T-166 stair / pool / tank steel: WORKED pending**. Pool population vs the flat floor -> D-57.
- **T-162 exterior Sigma: WORKED pending**: corners in m.l (457.095 measured vs his 1,297.35); conversion is the owner's own
  flagged item -> OWNER PACKAGE (not a numbered question: 5 are open).
- **Pool concrete** is now the largest single concrete gap (3.50 vs 12.35 m3). Decision: T-049 promoted (hand ledger first).
- **Excavation / backfill** missing: T-170 builds the level chain Q-21 C requires first.

## 2026-10-22 00:20 (lead run)

- **Checker 20:33 / 22:16 SUCCESS, 23:51 running**: 7 merged since 20:20 (T-119 r2, T-130 r3, T-134, T-156, T-149, T-144,
  T-155 r2 at 23:53), 1 rejected (T-155 r1, text and evidence, now merged as r2). Every READY row CAPACITY.
- **T-119 r2 columns: WORKED (MERGED 0f32ff8)**: tank columns HELD 3.00 .. 3.80 m; re-measured 0.0 %.
- **T-130 r3 registry 1.1.0 and T-140 census V2: WORKED / READY**: T-140 found that "released V2.9 + route G" names two runs
  (no profile 1,455 lines vs profiled 1,621 lines, 8 family figures differ). Decision: new T-165 (lane I, permitted) pins
  one baseline by provenance; until then every diff names its run (register note).
- **T-134 element register v0, T-156 Gate B tool: WORKED (MERGED)**. Checker note: 58 lines change only the knowledge
  rule_set id vs V2.9 and are listed changed-unflagged (seen, not hidden): no action.
- **T-149 beam steel: WORKED (MERGED 4972ac5)** with two integration conditions (RELEASED -> DRAWING-CONFIRMED, end-support
  top bars UNKNOWN). Decision: added to T-151, which is re-sequenced ahead of T-146 (all inputs merged) and claimable the
  moment T-142 merges.
- **T-144 opening heights: WORKED (MERGED 75be4ad)**.
- **T-155 r2 Q-71 evidence: WORKED (MERGED 15fd913)**: BOXED cells and closed-cage symbols described; leg lengths HELD.
- **T-142 V3.0.2 integration package: pending Gate B** (footing steel 3,735.91 -> 874.86 kg drawing-confirmed + 2,742.51 ..
  2,836.40 held; soffits 44.446 m2; D1-D3 fixed).
- **T-152 slab steel: pending (PARTIAL by design)**: bottom 2,853.00 .. 3,068.05 kg on Q-71; top bars HELD on a sheet-note
  vs typical-detail conflict; a frozen file labels two statements as owner decisions that the owner never recorded.
  Decision: D-49 .. D-52 filed for the designer; the AD2 statements and the slab share added to Q-71 as evidence (no new
  question); T-160 now permitted (lane S had nothing claimable).
- **T-159 facade per side: pending**: 1,022.534 m2 vs freelancer walls 968.237 (+5.6 %, RULE_DIFFERENCE). The owner's Sigma
  checks (openings, corners, domes, pool ceiling) were not part of it. Decision: new T-162 (lane A, permitted) and R-11 (c)/(d)
  for the corner and half-opening conventions.
- **T-161 photo review: pending**: renders show the 3 drawn domes (BOQ unchanged by the client change); missing BOQ
  categories railings and shutters. Decision: new T-164 (lane A, gate 1, not permitted yet), D-53 / D-54 filed.
- **Lane S running dry** (worker 1 had no permitted row after T-152). Decision: T-160 permitted now, T-166 (stair / pool / tank
  steel) and T-163 (formwork, a missing category) queued behind it.

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

