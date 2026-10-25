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

## 2026-10-24 10:15 (lead run)

| Task | Result | Evidence | Decision |
|---|---|---|---|
| T-146 + T-247 slab / beam partition (Gate B, V3.0.12) | WORKED | MERGED 768ff1d6 (Verifier 09:37): candidate CONC.SLAB 60.2801 = Checker 62 panels 60.2804 m3 (-0.0005 %) -> first WHOLE LINE VERIFIED in the candidate (not released); vs freelancer 59.8174 +0.77 % (1F dome corners ENGINE_RIGHT, GF / 2F RULE_DIFFERENCE); CONC.BEAM r2 in, measured 66.3179 + CONFLICT 5.1448 .. 6.1110 + HELD 3.228 .. 7.6685 + 5 runs no value | release of the slab line is the owner's (released A 61.5514 stays a DISCREPANCY +2.11 %); lane I now goes to the next closable line: floor area (T-240 split WP1-WP4), then doors (T-268) |
| T-228 blockwork register v2 | FAILED (REJECTED, gate e + h) | Verifier 09:59: 1F-W10's B3 piece 2.500 m sits under a member printed 'B3 (With Stair)' on the FFRS frame (= GF-W10's stair-foot piece the package itself HELD as F1); v2 carried it in an established net 44.929 on a floor that does not exist on that line | narrow r2 (TODO r2, worker 2 first): 1F-W10 HELD by R-T228-2 (CB9 pieces 38.369 m2 gross in the bounds text), 2F-W02 B3 confirmed HELD, GF-W10 eastern pieces 39.1525 + W.C. 0 .. 0.945 HELD; plus a sibling test over every '(With Stair)' member on every storey frame |
| T-235 r2 + part (4) V2 verdict schema / export | READY (not yet classified) | handoff 09:14 / row 09:58: a line reads VERIFIED only with a COUNTED WHOLE V2 record + a passing completeness record; 12 broken bindings refused | Gate A 6th (backlog-permitted infrastructure) |
| T-262 opening-to-room by geometry | evidence complete, not handed in (suite unfinished, READY at target) | worker 2 09:31: 59 openings, 118 / 118 sides; 5 WRONG labels (W06 in GF-13; W19 + D-1F-01 in 1F-03, W20 + D-1F-04 in 1F-02); 0.000 m2 change (equal pairs) | after T-228 r2: full suite on 768ff1d6, READY when READY <= 2 |
| T-260 aluminium doors evidence | evidence complete, not handed in | worker 1 08:36: D-GF-01 / -05 / -06 class ALUMINIUM, D-GF-09 0.90 on both faces; 12.760 m2 / 6 pcs if ruled | hand in NOW as worker 1's one whole-line closure (owner 10:02 (c)); integration T-268 |
| T-258 stairs / domes closable split | evidence complete, not handed in | re-validated 08:34 on 74c966b1; head moved to 768ff1d6 | not a whole-line closure: normal rule, hand in at READY <= 2 after a re-merge |

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
