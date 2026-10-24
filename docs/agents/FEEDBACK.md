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

## 2026-10-24 08:15 (lead run)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-253 boundary / exterior ground beams | WORKED | MERGED dff9cb79 (Verifier 07:20): own 8.8140 m2 x 0.40 = 3.5256 m3 (0.0 %); five D-35 readings re-read; 6 / 17 main runs own-measured 0.000 m; 15.960 DRAWING-CONFIRMED proposal | T-254 scope fixed (boundary line added; main house DRAWING-CONFIRMED, not VERIFIED); remaining 11 runs to the T-180 slot; formwork T-264, rebar T-265, coat T-263 |
| T-210 guard follow-ups | WORKED | MERGED dadf8446 (Verifier 07:28): own AST 28 - 4 by_design = 24 records; christiannp id closed; KNOWN 396 -> 395 | T-257 promoted to TODO |
| T-256 15 CONFLICT columns + 5 not-drawn lines | WORKED (research; line PARTIAL by design) | MERGED 74c966b1 (Verifier 07:52): 15 / 15 outlines own, 0 / 15 third prints, 5 / 5 positions empty | NOT_PRESENT removal in T-254; D-65 confirmation only; NEW D-66 for the 13-column band question (T-217's 'D-64' label retired) |
| T-250 plaster / paint face crosswalk | READY (not yet classified) | handoff 06:48: 465.385 m on 32 / 32 rooms; W03 room-side 6.726 .. 6.738 (T-128 right); W06 / W19 / W20 / west-bath doors on the wrong room; GF-16 over two wall strips | Gate A 4th; the room-label defect -> T-262 (gate 1, lane A first) |
| T-219 foundation / pit waterproofing | READY (not yet classified) | handoff 07:54: underlay 109.85 m2 + 5.4925 m3 DRAWING-CONFIRMED proposal; pit layers; footing sides HELD by detail; buried-concrete coat found | Gate A 5th; buried-concrete coat -> T-263 |
| T-258 stairs / domes closable split | evidence complete, not handed in (READY at target) | worker 1 07:15: closable 10.856 m3; ST-02 2.089 UNRESOLVED; ST-03 released on a convention in V3.0.11 | hand-in at READY <= 2; candidate fix T-266 after it merges |

## 2026-10-24 06:15 (lead run)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-251 gate-0 fix (t130 guard red since T-236) | WORKED | MERGED fee98d9a (Verifier 04:19): railing codes read from the item master, t130 green unchanged, full suite NEW 0 / KNOWN 396 | gate break closed; the full-suite rule on every hand-in stays; residual 8 implemented-family literals harmless to every guard (no follow-up) |
| T-252 CONC.BEAM ledger r2 | WORKED | MERGED b37be82d (Verifier 05:37): own re-measure = r2 66.3206 m3; ring 0.666406 m2 exact, the Checker's 0.66676 withdrawn (not averaged) | integrate with T-146 in one package, now first in lane I |
| T-239 V3.0.11 footing two-tag outline | WORKED | MERGED 3c9b1484 (Verifier 06:12, Gate B): 2 lines changed, 3,608 identical; HELD 2.176 .. 2.275 / blinding 0.552 .. 0.590; released-in-candidate footing 64.304 = 25 verified | line stays PARTIALLY VERIFIED (Q-31 C designer, D-14 clip): no new task; D-14 clip stays named on the line |
| T-253 boundary / exterior ground beams | READY (not yet classified) | handoff 05:13: boundary G.B 3.5256 m3 DRAWING-CONFIRMED proposal; D-35 main house read as N.G. (15.960 m3) | first in the Checker queue; T-254 takes it if merged |
| T-228 blockwork register v2 | READY (not yet classified) | handoff 05:04: net 494.189 m2, 38 held walls with items; GF-W10 stair-foot finding | Checker queue 2nd; follow-up T-261 queued after it |
| T-210 guard follow-ups | READY (not yet classified) | handoff 06:04: sandbox fixed (2 causes), K1 record 24 / 24, pymupdf not registered (AGPL) | K1 assertion NOT re-scoped (weakening); declarations -> T-257 after merge |

## 2026-10-24 04:15 (lead run)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-232 doors / windows pcs + m2 (Gate B, V3.0.10) | WORKED | Gate B PASS a0cd9bbc (Verifier 02:44: windows 76.256 m2 on 27 re-derived by hand incl. W03 28.251 and W18 1.080, -3.975 m2 / -4.95 % vs freelancer, residual 0; doors / windows rows leave 'unit refused'; 3,539 lines byte-identical) | doors / windows now scoreable in the candidate (HELD: W17 Q-76, W02 D-53, 7 doors); T-255 RE-SCOPED to the deduction side (the window line already carries W18 / W03); lessons row: gap claims name the version they were measured on |
| T-249 opening inventory from the drawings | WORKED | Gate A PASS 2a2d15af (Verifier 02:48: own leaf count 27 doors + 1 gate from swing arcs; W18 / W03 own reads) | none beyond T-255 |
| T-248 CONC.COLUMN + necks whole line | WORKED (line PARTIAL by design) | Gate A PASS 567dc972 (Verifier 03:19: 6 own re-measures 0.0 %, 1B1B identity accepted; 04:02: closable component 28 / 28 own-measured = 18.3465 m3, sections confirmed by the printed schedule ST p.9) | candidate columns -> T-254 (closable 28 incl. 2 planted 1.008 m3; 2F / annex HELD); CONFLICT 15 + UNKNOWN 5 -> new T-256 (lane S); necks stay HELD on Q-21 C |
| T-251 t130 gate-0 fix | pending | READY 03:46 (railing codes from the item master, +27 tests, t130 green unchanged, full suite NEW 0 / KNOWN 396) | Gate A first; residual (8 implemented-family literals) a follow-up only if a guard can trip on them |
| T-252 CONC.BEAM ledger r2 | pending | READY 03:51 (66.0161 -> 66.3206 m3, +0.3045 vs Checker +0.3049) | Gate A settles the 0.0004 m3 ring difference; T-247 takes r2 with the slab band-53 piece 0.0322 leaving with the ring |

## 2026-10-24 02:10 (lead run)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-243 t195 gate-0 fix | WORKED | Gate A PASS cebb269b (Verifier 01:15: root cause re-derived, inputs pinned by sha256 + git blob, 203 files; t195 28 / 28) | none; lessons row adopted (a snapshot test names its inputs by content) |
| T-242 CONC.GROUND whole line | PARTIAL | Gate A PASS 9455a63d (Verifier 01:21: interior 5 runs 2.2683 m3 re-measured face to face = ledger; line BLOCKED BY CONSULTANT D-33 / D-34 / D-35 / M4) | the drawing-settleable rest (boundary G.B at N.G. <= 3.5256 m3 in no line, court runs, annex CONFLICT, consultant rows narrowed to runs) -> T-253 (lane S); the candidate releasing 24 exterior beams 11.93 m3 at the interior depth -> T-254 (lane I, gate 1) |
| T-236 trade completeness (merged 00:10) | FAILED (gate, after merge) | t130_family_master red on 1cc1a153 and 9455a63d (Verifier 01:15 / 02:14): FIN.HANDRAIL literal at trade_completeness_v1.py:165 | gate-0 fix T-251 FIRST in lane A; RECURRING CAUSE 7 again (a new engine/source module trips a whole-repo guard its own tests do not run): every hand-in now runs the FULL suite on the merged head, and the Checker's Gate A includes every guard folder that scans engine/source (t130, t186, t202, t212) |
| T-232 doors / windows pcs + m2 (Gate B) | pending | READY 02:00 | Checker next (Gate B); W18 / W03 carried by T-255 |
| T-249 opening inventory from the drawings | pending | READY 01:59 (row stamp 02:55 typo) | Gate A next; W18 / W03 +29.331 m2 -> T-255 |
| T-248 CONC.COLUMN + necks whole line | pending | READY 02:13 | Gate A the run after; candidate columns on unprinted heights (2F to finished roof, annex at 4.50) -> T-254 |

## 2026-10-24 00:10 (lead run)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-211 V3.0.9a plaster / paint | WORKED | Gate B PASS 55fc11ec (Verifier 22:42: L4 to the end, NEW 1 = t195 pre-existing; 6 released lines by hand 0.0 %) | integrated; part 4 deltas next as T-244 (after T-250 evidence) |
| T-238 arched-opening fix | WORKED | Gate A PASS 242e50b2 (W26 1.8745, W17 reading confirmed) | DELTA_T238 wired by T-232; W17 -> owner Q-76 (ERS 2.7, section 6) |
| T-234 CONC.SLAB whole line | WORKED | MERGED 3224f68a; Checker own 62 panels 60.2804 m3 = worker 0.000 %; D-41 does not block the solid | engine side closes with T-146 (+ T-247 one package) |
| T-017 masonry census | WORKED | MERGED 345f408b after the handle evidence (hex lookup reproduces both corner conventions) | corner rule UP-MAS-CORNER-001 + oblique junctions go into T-228 |
| T-223 floor typing | WORKED | MERGED 48d1d846; curved room 19.0165 own = engine; side passage 5.640 exterior | T-240 carries dressing, sills, side passage, 0.280 strip |
| T-236 trade completeness | PARTIAL | MERGED 54ae8b5f; footing 1B1B identity UNRESOLVED; window inventory seeded from the engine (named limit); W18 / W03 29.331 m2 in no line; skirting 13.569 lm unlisted | T-248 (d) footing identity; T-249 tag inventory; T-232 W18 / W03; T-246 skirting listing |
| T-235 r1 BOQ export | PARTIAL | MERGED d7d232b9 (tool right on synthetic and adverse cases); real candidate export refused: two identities | T-245 identity fix; r2 + part (4) stays TODO |
| T-241 CONC.BEAM whole line | PARTIAL | MERGED f0250164; Checker own B25 / B22 / CB5 span 2 0.0 %; CONFLICT and HELD items are designer items D-02 / D-27 / D-26 | T-247 integration; Checker beam batch per storey (T-180 slot); consultant rows unchanged |
| T-237 wall-face crosswalk | PARTIAL | MERGED 1cc1a153; W03 room-side line, W06 wedge, 18 roof-datum faces HELD; face length per wall missing | T-250 evidence; T-244 integration |
| t195 document-register check | FAILED (on the working branch) | red since at least 63f4d90e (Verifier 22:42); Lead re-run 00:13 on 1cc1a153: 1 failed / 21 passed | T-243 gate 0 fix, first in lane A |

## 2026-10-23 22:10 (lead run)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-227 r2 (blockwork 3/4) | WORKED | MERGED ebce3d97 (Checker 21:05): own walk W15 / W16 4.3629 m2 each (crown 3.00), W18 1.080; 1F-W00 net 12.863 SOURCE-SUPPORTED | T-228 PROMOTED (claimable now); W15 / W16 window area stays 4.650 by Q-32 A |
| T-221 (roof / wet structural tops) | WORKED (zones HELD by design) | MERGED 63f4d90e: +5.50 falls rise 0.190 .. 0.203 m own = worker; its strip area 32.387 NOT verified (Checker own 31.681 finish hatch / 32.721 screed-membrane, HELD by layer); D-44 drawn on no sheet (8 searched) | the layer split goes to T-219 (waterproofing); consultant row 2 (D-44) send-ready; no new task |
| T-017 (masonry census) | PARTIAL (evidence) | NOT CHECKED 21:05: its D2:nnn references are capture indices, not P7757.dxf handles (gate e) | delay cause EVIDENCE; first in worker 2's next run (handles only); process lesson: every re-measure reference is a handle the Checker can open |
| T-211 (V3.0.9a plaster / paint, Gate B) | READY | paint 0 -> 166.88 m2 released (2 rooms VERIFIED, 1 ASSUMED - OWNER-APPROVED), 8 HELD ranges 529.47 .. 595.05 m2 + 4 HELD without a figure; 3,527 lines byte-identical | Gate B first in the next Checker run; 9b waits (same files); worker 3 takes T-235 parts (1)-(3) |
| T-234 (CONC.SLAB whole line) | READY | 60.2804 m3 DRAWING-CONFIRMED, CLOSABLE; released A +1.2710 (NEW defect: 2F 'T 18' tag spread +0.625, 13 non-slab faces +0.646); candidate +0.6388 (the faces); freelancer +0.4630 (+0.77 %) named, 1F lump residual 0.059 UNRESOLVED | second Gate A slot (23:49 at the latest); T-146 now carries the 13 faces after T-234 MERGED; new T-241 CONC.BEAM closure (CB5 band 0.296 m3 in no line); R-SLAB-T-1 lessons row proposed |
| T-238 (arched-opening fix) | READY | 68 openings censused: W15 / W16 window 4.650 (FREELANCER_RIGHT), finishes 4.363 per face; W26 1.875 (arch, not 1.20 x 1.70); W17 HELD 9.870 .. 11.515 (45 = archivolt?); windows 45.101 vs his 45.481 on 7 (-0.84 %) | gate 1 critical, with T-211 in the next Checker run; W17: the Checker rules the 305 / 45 reading first, owner item only after that (the Q-39 answer quoted a height the question text supplied) |
| T-180 floor area (Checker) | PARTIAL (line findings) | 20 / 47 pieces VERIFIED 0.0 %; dressing 2.970 m2 in no floor line (scope), sills 0.550 m2 carried as porcelain (class); curved room ENGINE_RIGHT on geometry | T-223 acceptance extended; new T-240 (lane I wiring of both findings) |

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
