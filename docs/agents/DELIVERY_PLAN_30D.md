# 30-day delivery plan, 2026-10-20 to 2026-11-19 (owned by the Lead; started by the main chat)

**Basis:**

- Today the throughput of released, verified BOQ changes is 0 a week; the merge throughput is 25–40 a day.
- The checker merges 3–4 tasks per run.
- The plan therefore does not add volume. It routes existing verified work into one consolidated, opt-in candidate:
  `ARCH_TAKEOFF_V3.0` plus route G, owned by Worker 3.
- No released default changes without the owner.

**Rules:**

- At most 3 tasks READY at a time.
- Each worker claims only its own lane, marked in the board's trade column: S (structural), A (architectural /
  finishes), I (integration). If its own lane is empty, a worker takes a TODO from another lane, without touching that
  lane's CLAIMED files.

## Week 1 (by 2026-10-27). Target: one verified improvement through the integrated pipeline

| Plan | Lane | Deliverable | Acceptance | Verification |
|---|---|---|---|---|
| P-01 | owner + auditor | in progress, good | pilot 12:20 - 14:20: 7 / 7 slots STARTED + final SUCCESS, 5 merged, 2 narrow rejections (validated on an older head; hand-in rule tightened 14:20), READY 2; the t202 guard fix (T-212 r2) first at 14:49. Earlier, pilot (owner 06:15): 08:20 - 10:20 every slot STARTED + final SUCCESS (worker 1 08:20, 09:20; worker 2 08:40, 09:40; worker 3 09:01 -> 10:05; checker 08:51, 09:51), run lock taken and released, 0 IDLE, every self-check PASS, 0 refusals. ONE regression merged (t202 guard test red since 01eeafd0, no quantity effect): a pilot rollback trigger for the auditor's 12:15 check-in; fix T-212 at the top of the board |
| P-02 | I | BOQ_FAMILY_MASTER 1.1.0 refreshed from code and releases (evidence per family) | every family has a status with a file:line or commit | checker spot-checks 10 |
| P-03 | V3.0.4, V3.0.5 r2, V3.0.6 and V3.0.7 MERGED (V3.0.7 e866328a 11:49, Gate B PASS: verified pool 7.202 + dome shells 5.081 m3 in, DOME-B billed once; verification -> integration 19.6 h for the pool (T-183 merged 22 Oct 16:14) and 17.6 h for the dome shells (T-185 18:15)); Lead 18:20: V3.0.8 = T-231 READY 18:01 (verified straps 3.3905 m3 + planted columns; Gate B first at 18:49); then owner order 17:50: T-211 plaster / paint (+ wet-wall tiles, kitchen) -> T-216 floor-area line -> T-232 doors / windows pcs AND m2 -> T-199 formwork / railings; earlier: V3.0.7 READY 10:03, first in the 10:49 checker run; next V3.0.8 formwork + railings (T-199), V3.0.9 plaster / paint (T-211), then slab faces (T-146) | candidate grows by verified pieces only | NOT RELEASED |
| P-04 | checker | SCOREBOARD v2: per trade and unit WAPE, coverage, verified share, held = UNKNOWN share; no mixed units | table on the board | Lead reviews |
| P-05 | S | blinding scope (under ground beams and straps) and the 5 columns not on the roof-slab plans, fed into V3.0 | blinding within the hand range 20.71–26.37 m3; columns −2.27 m3 | checker hand |

## Week 2 (by 2026-11-03). Target: measurable increase in verified coverage

| Plan | Lane | Deliverable | Acceptance |
|---|---|---|---|
| P-06 | A | plaster and paint by both methods (owner manual heights G1 and drawing-derived), room by room | both results with the difference explained; checker re-measures 3 rooms |
| P-07 | T-215 part 1 READY (GF ends closed +1.214 .. +1.241 m2), part 2 T-222; T-125, T-143, T-169, T-175, T-194, T-198, T-201, T-207 and T-108 r2 MERGED (01eeafd0: established net 337.412 m2, 58.366 m3, white units 303.1 / 394.7; checker 0.0 % on 2F-W08 / GF-W22) | engine module DONE (unwired); held bounds T-215, independent census T-017, black units T-176 | into the candidate after T-211 |
| P-08 | S | rebar by bar population, footings and columns first, from the schedules | rebar lines with bar marks; checker hand on 10 bars |
| P-09 | Lead + I | element register v0: stable ids for floors, rooms, walls, openings and structural elements, linked to BOQ lines (built from existing outputs, no rewrite) | every V3.0 line carries an element id plus a drawing reference |

## Weeks 3–4 (by 2026-11-19). Target: a full-villa BOQ candidate for the principal trades

| Plan | Lane | Deliverable |
|---|---|---|
| P-10 | T-214 floor build-up MERGED b29060c2 (dry 0.05 DRAWING-CONFIRMED; wet / roof T-221); T-163 formwork r3 MERGED 659f889f (into the candidate by T-199); T-206 MERGED (footing underlay 5 / 2 / 10 cm VERIFIED; formation and existing ground HELD, Q-21 C); T-170 excavation QUEUED after T-205 (depth HELD until an existing-ground level exists) | formwork hand DONE; excavation geometry next, depth HELD | site level survey not in the set (D-62) |
| P-11 | A | doors and windows as BOQ lines (schedule + knowledge 1.5.0 2.20 m fallback), wall tiles (Q-48), ceilings (Q-68 C held finish, area measured) |
| P-12 | I | V3.x reproducible full Alsenan BOQ: all principal trades present; held and unknown items listed with reason; one command; xlsx + csv |
| P-13 | checker | verified-share report on V3.x; owner release package (switch-default request with evidence) |
| P-14 | owner | authorise the formal held-out evaluation (sealed URBAN_BLIND_V2 or Qortuba) or provide an independent QS villa |

Re-estimate after each week from what actually merged into V3.0 and was verified.

## Status (Lead, 2026-10-25 22:15; re-estimated each run from what merged and was verified)

Lead 2026-10-25 22:15: since 16:15 one ledger MERGED (footing reinforcement PART F + a downgrade-only record on the
874.862 kg footing line) and four pieces handed in (stairs V3.0.18 Gate B, rebar basis r2, WP foundation inventory,
formwork slab-level ledger); no candidate line moved, whole verified lines in the export stay 1. About 3.5 h lost to a
usage-limit outage (18:11 - 21:40; one Checker run without a verdict). Week 1 (27 Oct): the verified-improvement target
is met by CONC.SLAB (since 14:15); week 2 (3 Nov): T-266 Gate B now -> T-255 (windows + ring correction) -> T-294 ->
T-279 / T-284 / T-244 / T-246 -> T-199 (formwork with the CB5 span fix); risk: Checker capacity (READY 4) and the
usage limit, not engineering. New T-303 (WP wet / roof inventories) is the path to a second WHOLE WP line.

Lead 2026-10-25 16:15: since 14:15 four research ledgers MERGED (plaster / paint r2, ceilings, rebar basis r1, skirting)
and the ring GB end rule was closed from the drawing; no candidate line moved, whole verified lines in the export stay
1. Week 2 (3 Nov): T-266 stairs CLAIMED 15:05 (V3.0.18, Gate B next) -> T-255 (windows + the ring correction) -> T-279
(blockwork 422.5 m2) -> T-294; estimate T-279 integrated 26 - 27 Oct (unchanged). Second whole line: WP.FOUNDATION
after T-301 (worker 2 next, 16:39; estimate 26 Oct). Plaster / paint whole line now needs T-302 (W17 developed hole)
before T-244. Rebar: footing PART F READY, T-297 r2 narrow, T-300 safeguard after it; no steel quantity moves.
Risk unchanged: each lane I step needs a full Checker record re-issue until T-294 lands.

Lead 2026-10-25 14:15: WEEK 1 TARGET MET (27 Oct target, met 25 Oct 13:54): one verified improvement went through the
integrated pipeline: T-298 MERGED 274885e6 makes CONC.SLAB (60.280155 m3) the first WHOLE verified line in the real export
(completeness 62 = 62, Checker's own independent join), and T-254 MERGED 7c49e890 (Gate B) put the exterior ground-beam
correction into the candidate (V3.0.17, main-house exterior 8.1642 -> 15.9575 m3 DRAWING-CONFIRMED). Not released: the
default stays V2.9 + route G (owner only). Week 2 (3 Nov, measurable increase in verified coverage): lane I chain
T-266 (stairs, next for worker 3 at 14:59, about 1 h + Gate B) -> T-255 (windows) -> T-279 (blockwork 422.5 m2, 297.8
VERIFIED) -> T-294; estimate T-279 integrated 26 - 27 Oct if each Gate B passes first time (unchanged). Second whole
line candidate: WP.FOUNDATION once T-301 builds the inventory (worker 2, after T-292 r2 / T-296; estimate 26 Oct).
Reinforcement: no rebar quantity moves; footing PART F (owner 13:16) and the line-to-member ledger (T-297) are research.
Risk: each lane I step needs a full Checker record re-issue until T-294 lands.

### Earlier status (Lead, 2026-10-25 12:15)

Lead 2026-10-25 12:15: since 10:15 the Checker merged T-290 891dbd4d, T-291 0c6b2ba5 and T-170 2991be3d and issued the
V3.0.16 records (8 V2 verdicts, 7 downgrades; 21.953969 m3 moved to HELD / CONFLICT). Week 1 target (27 Oct, 'one verified
improvement through the integrated pipeline'): the first real export is merged with records, but it still counts 0 whole
verified lines because the completeness join reads an old slab grain (T-298, owner immediate priority, worker 2 12:39;
about 1 - 2 h + Gate A) and no waterproofing inventory exists (T-301). With T-298 merged the slab line (60.2804 m3) can be
the first whole verified line through the pipeline, estimate late 25 Oct: on track for 27 Oct. Exterior ground beams
(T-254, +7.80 m3 drawn) are in work for worker 3 (Gate B after). Week 2 (3 Nov): blockwork 422.5 m2 via T-279 behind
T-266 / T-255 in the owner's order, estimate 26 - 27 Oct, unchanged. Reinforcement: Stage B (tonnes, reconciliation) runs
now; no rebar quantity moves until the owner approves an implementation stage.

### Earlier status (Lead, 2026-10-25 10:15)

Lead 2026-10-25 10:15: since 08:15 the Checker merged 3 Gate A pieces (T-289 455c93c4 structural basis ledger with his own
re-derive, T-275 r2 6c4c9700, T-286 e861e390); T-245 r2 (first real export) is in Gate B in the 08:50 Checker run, about
2 h later than the 06:15 estimate. The week-2 target 'measurable increase in verified coverage' (3 Nov) now has its
largest single input ready: the blockwork ledger (T-291) shows the candidate carries no blockwork quantity, so T-279 adds
422.5 m2 determinate (297.8 m2 VERIFIED) to blank lines once T-291 passes Gate A; it sits behind T-254 / T-266 / T-255 in
the owner's lane I order, one package at a time (about 2 - 4 h each including Gate B), so it lands about 26 - 27 Oct if
each Gate B passes first time. Risk unchanged: verdict records bind to the whole candidate (T-294 after T-255).

Lead 2026-10-25 08:15: since 06:15 the Checker merged 2 Gate A pieces (T-287 542b64c7: CB5 columns VERIFIED 1.430 m3 as a
component; T-280 86fdc315: column-core rebar LOWER bounds) and rejected T-245 Gate B NARROW on stale maps only; every
other Gate B check passed on the real candidate. Week-1 target 'one verified improvement through the integrated
pipeline' (2026-10-27): evidence so far is V3.0.15 (7 Checker-VERIFIED foundation WP lines integrated, not released);
the week-2 entry 'first real export' now depends on T-245 r2
(worker 3 08:59, about 10 min) and its Gate B at 09:51, about 1.5 h later than the 06:15 estimate. Next integration
T-254 (exterior ground beams, a material +7.80 m3 / +95.5 % correction on the main house if the Checker confirms T-289)
can be handed in the same day T-245 merges. Risk named: verdict records bind to the whole candidate, so each lane I step
costs a full re-issue by the Checker (T-294 queued after T-255). Workers 1 / 2 now prepare the line-id ledgers for
T-266, T-279, T-244 and T-199 (T-290 .. T-293) so those packages are mechanical when their turn comes.

Lead 2026-10-25 06:15: since 04:15 the Checker merged 4 Gate A pieces (T-257 6a8eea78, T-283 6e141df6, T-281 40518c58,
T-288 643b310b; research ledgers, no candidate line moved), rejected T-275 narrow, and verified the buried ground-beam WP
component (32 / 32 faces own, +0.008 %). T-245 (ARCH_TAKEOFF_V3.0.16, one project identity, first real export, json-hash
cause named) is READY for Gate B 06:13: the week-2 entry condition 'first real export' depends on its Gate B in the 06:49 /
07:49 Checker runs (full suite still to run). Verified-share gains this week wait on the lane I chain (T-245 -> T-254 ->
T-266 -> T-255 -> T-279 blockwork -> T-284 ceilings), whose inputs are now all merged; that chain is the critical path for
the 3 Nov target. Lane S now prepares T-254's input (T-289) so that package needs no new measuring. WEEK-1 TARGET: MET.

Lead 2026-10-25 04:15: since 02:15 the Checker merged 1 Gate B package: T-270 r2, WATERPROOFING.FOUNDATION into candidate
ARCH_TAKEOFF_V3.0.15 (04d34378): 3,680 lines byte-identical, 19 added (7 VERIFIED, buried liquid 45.4682 m2 DRAWING-CONFIRMED /
PARTIALLY VERIFIED, 11 HELD BLANK); a scope missing in released A and in the freelancer BOQ, now in the integrated pipeline.
WEEK-1 TARGET (one verified improvement through the integrated pipeline by 27 Oct): MET (CONC.SLAB earlier; now also the
foundation waterproofing family, verification -> integration about 17 h for T-219's lines). Handed in: T-282 r3, T-283,
T-257 (READY 3 = target), T-281 complete and held back. Next in lane I: T-245 (one project identity, first real export,
canonical-hash binding of V2 verdict records; unblocked now), then T-254 -> T-266 -> T-255, T-279 (after T-288), T-284 (after
T-283 / T-281). Verified whole lines unchanged: candidate 1 / 13, released 0 / 13. Week 2 (3 Nov, measurable verified
coverage): depends on T-245 (export with every line's status), T-288 -> T-279 (blockwork into the candidate: 297.847 m2
already Checker-verified on 18 walls) and T-283 + T-281 -> T-284 (ceilings). Risk unchanged: lane I is serial (one package
per Worker 3 run, every 2 h); six packages queued before T-279.

(superseded) Lead 2026-10-25 02:15: since 00:15 the Checker merged 2 (T-278 floor-area scoring key T001C, FLOOR.INTERNAL keyed 380.3641
m2 on 40 lines, -7.13 % vs freelancer; T-285 blockwork register v3, established 449.5934 m2) and rejected 1 narrow (T-282 r2,
one END row). T-180 slot: blockwork VERIFIED share 105.004 -> 297.847 m2 on 18 walls; NEW FINDING: 7.913 m of GF wall under
six sunken panels booked at the normal soffit (established net overstated by 7.913 d m2, d HELD on D-41; GF-W12 VERIFIED
withdrawn) -> NEW T-288 (register v4) before T-279. Verified whole lines unchanged: candidate 1 / 13, released 0 / 13. Week-1
target (one verified improvement through the integrated pipeline by 27 Oct): T-270 r2 (Gate B, in work) is the next
integrated verified step; T-245 (first real export) follows. On track if T-270 r2 passes Gate B in the next 2 Checker runs.

(superseded) Lead 2026-10-25 00:15: since 22:15 the Checker merged 3 (T-276 r2 buried faces 45.4682 m2 DC on 32 faces; T-277 beam
width census, both readings kept; T-274 blockwork height pieces close every census run, register proposal 449.260 ->
449.565 m2 not applied) and rejected 2 narrow (T-270 Gate B on the buried sub-line only; T-282 formwork END faces on hull
diagonals). Handed in: T-278 (floor-area scoring key). Blockwork verified share 95.633 -> 105.004 m2. Verified whole lines
unchanged: candidate 1 / 13, released 0 / 13. OWNER 23:49 integration-first cycle applied: lane I T-270 r2 -> T-245 (first
real export, internal review candidate) -> T-254 -> T-266 -> T-255, then T-279 (after T-285 applies the wall register) and
T-284 (after T-283). Week 1 (27 Oct) met by CONC.SLAB. Week 2 (3 Nov, measurable verified coverage): depends on T-270 r2
Gate B (waterproofing family into the candidate), T-245 (the first real export with every line's status and the
structural revision UNCONFIRMED) and T-285 -> T-279. Risk: lane I is serial and now carries six packages in a fixed order
(about 2 h each, about 12 h of Worker 3 runs before T-279); the designer RFI package waits on T-286 / T-287 (G rows).

(previous) Lead 2026-10-24 22:15: since 20:15 the Checker merged 4 (T-267 r2 rule store 1.7.0; T-272 r2 ground-beam links, count /
mass HELD; T-273 r2 laps + t with the owner's s.6 acceptance, every lap HELD, 0.000 t on Alsenan; T-271 r2b ceilings, GF
light well split to 0.0014 m2, R2 decor 363.173 m2 DRAWING-CONFIRMED, not verified as a whole) and rejected 1 narrow
(T-276 r1 buried faces: square cut at a curved carrier + sub-mm sliver, total HELD <= 45.611 m2). Handed in: T-270
(Gate B, V3.0.15 WATERPROOFING.FOUNDATION, a scope missing in released A and in the freelancer BOQ) and T-277 (beam
width census, 7 / 137 conflicts = D-02 + D-27). Verified whole lines unchanged: candidate 1 / 13, released 0 / 13.
Week 1 target (one verified improvement through the integrated pipeline by 27 Oct) is met by CONC.SLAB; the week-2 target
(measurable increase in verified coverage by 3 Nov) depends on T-270 Gate B, T-274 -> T-279 (blockwork into the
candidate) and T-283 -> T-284 (ceilings into the candidate). New this run: T-280 (core datum), T-281 (stair soffits,
missing scope), T-282 (formwork faces at curved / oblique carriers), T-283, T-284. Risk: lane I is serial (one package per
2 h); T-279 and T-284 queue behind T-274 / T-283.

(previous) Lead 2026-10-24 20:15: since 18:15 the Checker merged T-240 (Gate B, floor area V3.0.14 internal 380.364 m2 vs released
385.634, -1.37 %; NOT VERIFIED as a whole, held pieces named) and T-261 r3 (blockwork split, 11 / 11 walls Checker own,
register proposal 449.260 -> 625.562 m2 not applied); passed T-272 r2 (links per drawn clear span, merge after T-267 r2);
rejected 2 narrow (T-273 r1 against the owner's 18:38 acceptance, after the hand-in; T-271 r1 light-well opening 23.237
vs the slab plan's 16.005 m2). Integration chain unblocked: T-270 (WATERPROOFING.FOUNDATION + WP.BURIED) first in lane I,
then T-278 (scoring key for 7.8925 m2 typed spaces), then T-279 (established blockwork walls into the candidate, after
T-274). Week 1 (by 27 Oct, one verified improvement through the pipeline) stays met (CONC.SLAB, Doors ALU 2 / 3); week 2
(3 Nov, measurable verified coverage): blockwork 95.633 m2 verified, waterproofing next into the candidate. No slip.

Lead 2026-10-24 18:15: since 16:15 the Checker merged T-263 (buried-concrete liquid waterproofing, a missing BOQ
category: 35.404 m2 DRAWING-CONFIRMED, PARTIALLY VERIFIED) and rejected 2 narrow (T-261 r2 blockwork split, T-272
stirrup count); T-240 floor area V3.0.14 READY for Gate B. Verified whole lines unchanged: 1 / 13 candidate (CONC.SLAB),
0 / 13 released. Blockwork verified share 67.574 -> 95.633 of 449.260 m2. Week-1 target (27 Oct, one verified improvement
through the integrated pipeline) is met by Doors ALU in V3.0.13 and, once Gate B passes, floor area V3.0.14; week-2 (3 Nov)
on track for floor area and doors, waterproofing integration (T-270) added; rebar laps / t in work (T-273).

Lead 2026-10-24 16:15: since 14:15 the Checker merged T-265 (ground-beam main + side bars, structural), T-268 (Gate B:
Doors aluminium into candidate V3.0.13, 12.760 m2 / 6 pcs, nothing held) and T-168 (Gate B tool v2), and rejected 2
narrow (T-261 blockwork split r1, T-267 stair module r1: both in rework). READY 0. Verified whole lines still 1 / 13 in
the candidate (CONC.SLAB); Doors ALU is the second line closed in the candidate but PARTIALLY VERIFIED 2 / 3 (heights
Q-55 C owner-approved), so it does not count as a whole verified line; 0 / 13 released. Blockwork verified share
4.458 -> 67.574 of 449.260 m2 established net (Checker light runs, 9 / 37 net walls). Week-2 target (3 Nov) on track for
floor area (T-240 WP2b in work) and doors; rebar is now on the owner's t unit (T-273 TODO). Next milestone 27 Oct.

Lead 2026-10-24 14:15: since 12:15 the Checker merged 4 Gate A tasks (T-264 formwork r4, T-269 floor-area blockers,
T-258 r2 stairs / domes closable split, T-262 opening-to-room by geometry) and rejected 1 (T-258 r1, fixed in 54 min);
READY 1 (T-265 ground-beam rebar, structural). Verified whole lines still 1 / 13 in the candidate (CONC.SLAB), 0 / 13
released. Week-2 target (3 Nov): the Doors aluminium line is in integration now (T-268, claimed 13:03; Gate B in the
next Checker runs): still on track to be the second whole line today, PARTIALLY VERIFIED 2 / 3 on the heights (Q-55 C
owner-approved). Floor area: the 1F living blocker closed (38.6335 m2 own); T-240 WP2 .. WP4 follow T-268. P-08: ground-
beam top / bottom steel at Gate A; stirrups / side bars / laps are T-272 (prints only). P-11: ceilings (no line in any
run) re-queued as T-271 on the merged evidence. Risk: lane I stays serial (one package per worker 3 run); every closable
row now waits on it or on consultant items. No milestone re-dated.

Lead 2026-10-24 12:15: since 10:15 the Checker merged 5 Gate A tasks (T-219 foundation / pit waterproofing, T-250
face crosswalk, T-260 aluminium-door rulings, T-228 r2 blockwork register v2, T-235 r2 verdict / export tooling),
rejected 0; READY 0. Verified whole lines still 1 / 13 in the candidate (CONC.SLAB), 0 / 13 released. Week-2 target
(3 Nov, 'measurable increase in verified coverage'): the Doors aluminium line is now closable in ONE integration run
(T-268, worker 3 12:59 -> Gate B about 13:49): on track to be the SECOND whole line today; floor area follows on T-240
WP2 .. WP4 (WP1 pushed). P-11 missing scope: foundation waterproofing now verified in pieces -> T-270 into the
candidate. P-05 / P-08: CONC.GROUND exterior component 16 / 17 own-measured (+0.06 %); the line stays BLOCKED BY
CONSULTANT. Risk: worker 1 holds three evidence-complete hand-ins (WIP limit set). No milestone re-dated.

Lead 2026-10-24 10:15: since 08:15 the Checker merged the T-146 + T-247 Gate B package (V3.0.12, 768ff1d6) and
rejected T-228 (blockwork register v2, narrow r2). WEEK-1 TARGET MET 3 days early: 'one verified improvement through
the integrated pipeline' = CONC.SLAB WHOLE LINE VERIFIED in the candidate (60.2801 vs Checker 60.2804 m3; not released,
release is the owner's). Verified whole lines 1 / 13 (candidate), 0 / 13 released. READY 3 (T-250, T-219, T-235).
Owner workflow approval 10:02 applied: P-03 lane I now ranks by closable lines: floor area (T-240, split WP1-WP4, Week-2
candidate for the second whole line if the Checker's 47 pieces all agree), then aluminium doors (T-260 evidence ->
T-268), then the non-closable corrections T-254 / T-266. Week-2 target 'measurable increase in verified coverage':
on track if floor area or doors closes by 3 Nov. Windows (Q-76 owner, D-53 designer) and every remaining concrete line
(consultant items) cannot close from the drawings alone. No milestone re-dated.

Lead 2026-10-24 08:15: since 06:15 the Checker merged 3 (T-253 boundary / exterior ground beams, T-210 guard
follow-ups, T-256 column evidence), rejected 0; READY 3 (T-228 blockwork register v2, T-250 face crosswalk, T-219
foundation waterproofing); T-258 (stairs / domes closable split) evidence complete, waiting for READY <= 2. Verified
whole lines still 0 / 13. P-03: the slab / beam package (T-146 + T-247) is being built (claimed 07:01) and stays the
Week-1 path (27 Oct: on track if it passes Gate B by 26 Oct). P-05 / P-08 / P-10: CONC.GROUND gained a drawing-confirmed
boundary beam (3.5256 m3, missing in both runs) and a confirmed outer-ground datum; candidate fix T-254 now has every
input merged; formwork r4 (T-264) and ground-beam rebar (T-265) added for the changed members. P-11 / missing scope:
foundation waterproofing handed in (T-219), buried-concrete coat added (T-263). Drawing interpretation: opening-to-room
by geometry (T-262, gate 1). No milestone re-dated.

Lead 2026-10-24 06:15: since 04:15 the Checker merged 3 (T-251 gate-0 fix, T-252 CONC.BEAM r2, T-239 Gate B V3.0.11
footing two-tag CONFLICT), rejected 0; READY 3 (T-253 boundary / exterior ground beams, T-228 blockwork register v2,
T-210 guard follow-ups). Verified whole lines still 0 / 13. P-03: V3.0.11 merged (released-in-candidate footing 64.304 =
the 25 verified footings). DECISION: the slab / beam partition (T-146 + T-247) moves to the head of lane I because
CONC.SLAB is the only line that can become a whole verified line now (Checker 60.2804 m3 on 62 panels); this is also
the Week-1 target 'one verified improvement through the integrated pipeline' (27 Oct, 3 days): on track if that package
passes Gate B by 26 Oct (lane I ships about one package per 2 h of worker 3 time). T-254 / T-255 follow. No milestone
re-dated.

Lead 2026-10-24 04:15: since 02:10 the Checker merged 3 (T-232 Gate B V3.0.10 doors / windows pcs AND m2, T-249 drawn
opening inventory, T-248 CONC.COLUMN whole-line ledger), rejected 0; READY 2 (T-251 gate-0 fix, T-252 CONC.BEAM r2).
Verified whole lines still 0 / 13; new verified COMPONENT: 28 columns 18.3465 m3 (Checker own re-measure 28 / 28).
P-03: V3.0.10 merged (doors / windows scoreable in the candidate; W18 / W03 already inside it, T-255 re-scoped to the
deduction side). P-11: doors / windows as candidate lines DONE except W17 (Q-76), W02 (D-53) and 7 held doors. Lane I
remains the bottleneck (T-239 in work, then T-254 with the column component). New T-256 narrows the 15 CONFLICT
columns. Day-14 (3 Nov) on track; the 27 Oct day-7 target was met on 21 Oct; no milestone re-dated.

Lead 2026-10-24 02:10: since 00:10 the Checker merged 2 (T-243 gate-0 fix, T-242 CONC.GROUND ledger), rejected 0; READY 3
(T-232 Gate B doors / windows pcs + m2, T-249 drawn opening inventory, T-248 CONC.COLUMN whole line). Verified whole
lines still 0 / 13. A merged check module (T-236) turned the t130 registry guard red: gate-0 fix T-251 first in lane A;
recurring cause 7 answered with a full-suite rule on every hand-in. CONC.GROUND moved to BLOCKED BY CONSULTANT
(D-33 / D-34 / D-35) except the boundary beam and the court / annex evidence (T-253); the candidate's unprinted depths
and heights (24 exterior ground beams, 2F and annex columns) become HELD in T-254. Lane I serial order: T-239, T-254,
T-255 (W18 / W03), T-245, T-146 + T-247 (takes the T-252 beam ledger r2), T-240 (floor-area class items added), T-244,
T-246, T-199. P-04: floor area fully re-measured (32 / 47 VERIFIED pieces), CONC.BEAM every calculated run re-measured.
Day-14 (27 Oct) on track for 'one verified improvement through the pipeline' only if T-146 or T-240 merges by then:
lane I is the bottleneck (one package per 2 h); no milestone re-dated.

Lead 2026-10-24 00:10: since 22:10 the Checker merged 9 (T-211 Gate B V3.0.9a, T-238, T-234, T-017, T-223, T-236,
T-235 r1, T-241, T-237), rejected 0; READY 0. Verified whole lines still 0 / 13 on the closable table; the next four
lines that can close do so through lane I (CONC.SLAB T-146, floor area T-240, plaster / paint T-244, doors / windows
T-232), so lane I (one package per 2 h) is now the delivery bottleneck: its serial order is on the board, and the two
pieces it can ship together (T-146 + T-247, one slab / beam partition) are named. P-03: V3.0.9a merged (plaster / paint
into the candidate; verification -> integration for the three checker rooms within 24 h). P-04: CONC.SLAB re-measured
whole. P-06: hand package DONE, candidate DONE for V3.0.9a, part 4 deltas next (T-244). Export (T-235 r1) merged; the
real-candidate export waits on one project identity (T-245). Gate 0 fix T-243 (a test red since at least 63f4d90e)
first in lane A. Day-14 on track; no milestone re-dated.

Baseline: the RELEASED baseline is run A (V2.9 + route G, no profile, 1,455 lines), pinned by T-165 (37124da); run B
(profiled, 1,621 lines) is the comparison base for V3.0.x line pairing. The engineering reasoning standard (owner 08:05)
governs every item; the owner's teaching case (pool, domes, two staircases, 09:40 / 11:50) is the structural priority;
WORKFLOW_CONTROLS section 10 (owner 15:15: faster execution, same evidence) governs how work flows.

| Plan | Board | State | Note |
|---|---|---|---|
| P-01 | owner + auditor | in progress, good | pilot (owner 06:15): 08:20 - 10:20 every slot STARTED + final SUCCESS (worker 1 08:20, 09:20; worker 2 08:40, 09:40; worker 3 09:01 -> 10:05; checker 08:51, 09:51), run lock taken and released, 0 IDLE, every self-check PASS, 0 refusals. ONE regression merged (t202 guard test red since 01eeafd0, no quantity effect): a pilot rollback trigger for the auditor's 12:15 check-in; fix T-212 at the top of the board |
| P-02 | T-130 r3, T-165, T-140 MERGED; T-203 registry 1.2.0 r2 MERGED 40de7c7f (as_of V3.0.7: states 13 / 3 / 34 / 49) | DONE | |
| P-03 | V3.0.4, V3.0.5 r2, V3.0.6 and V3.0.7 MERGED (V3.0.7 e866328a 11:49, Gate B PASS: verified pool 7.202 + dome shells 5.081 m3 in, DOME-B billed once; verification -> integration 19.6 h for the pool (T-183 merged 22 Oct 16:14) and 17.6 h for the dome shells (T-185 18:15)); Lead 18:20: V3.0.8 = T-231 READY 18:01 (verified straps 3.3905 m3 + planted columns; Gate B first at 18:49); then owner order 17:50: T-211 plaster / paint (+ wet-wall tiles, kitchen) -> T-216 floor-area line -> T-232 doors / windows pcs AND m2 -> T-199 formwork / railings; earlier: V3.0.7 READY 10:03, first in the 10:49 checker run; next V3.0.8 formwork + railings (T-199), V3.0.9 plaster / paint (T-211), then slab faces (T-146) | candidate grows by verified pieces only | NOT RELEASED |
| P-04 | T-132 DONE; T-177 and T-182 (five measures, 50991742) MERGED; T-181 claimable; T-180 slot: pool and 2 stair flights reconciled, 0 / 8 VERIFIED | script DONE; five measures in the checker queue | whole-line rule (owner 11:50) |
| P-05 | T-126 / T-133 | DONE | |
| P-06 | T-128 r3 MERGED a6ac2c66 (3 rooms checker 0.0 %); T-173 stair shaft MERGED 8b4d2c83 | hand package DONE; engine line: T-211 V3.0.9a READY 21:58 (Gate B first in the next Checker run; 9b wet-wall tiles + kitchen after it); cross-trade face check T-237; W15 / W16 deduction fix T-238 | scoreboard plaster / paint NOT YET MEASURED until T-211 merges |
| P-07 | T-125, T-143, T-169, T-175, T-194, T-198, T-201, T-207 and T-108 r2 MERGED (01eeafd0: established net 337.412 m2, 58.366 m3, white units 303.1 / 394.7; checker 0.0 % on 2F-W08 / GF-W22) | engine module DONE (unwired); held bounds T-215, independent census T-017, black units T-176 | into the candidate after T-211 |
| P-08 | populations MERGED; T-171 notation MERGED 701d227 (2,769.06 .. 2,829.83 kg HELD on the unprinted leg diameter); T-174 straps MERGED 984ebbe1 (axis length, 3.3905 m3; SB2 bars HELD D-38); T-230 strap / footing overlap TODO | notation DONE by investigation | |
| P-09 | T-134 MERGED; register rulings +7 (16:20: staircase identity corrected, shaft walls, opening deductions, pool upstand, 1F-11 curved glazing, default guard, corners pair) | DONE (v0 code); content grows each run | |
| (Gate B tooling) | T-156, T-202, T-212 r2 (b5716930, red guard closed) MERGED; T-224 slab-step method version queued; T-168 Gate B v2, T-210 guard follow-ups TODO | | |
| P-10 | T-163 formwork r3 MERGED 659f889f (into the candidate by T-199); T-206 MERGED (footing underlay 5 / 2 / 10 cm VERIFIED; formation and existing ground HELD, Q-21 C); T-170 excavation QUEUED after T-205 (depth HELD until an existing-ground level exists) | formwork hand DONE; excavation geometry next, depth HELD | site level survey not in the set (D-62) |
| P-11 | T-147, T-159, T-161, T-157, T-150 r2, T-172, T-162 r2, T-164 (390fabf4), T-181 (faa04202) MERGED; T-198 census r3 | ahead of week 3 | |
| (concrete gap) | T-217 section conflicts MERGED 65fef8fa (C8 / lift group CONFLICT ranges; planted columns + 5 lines -> T-220); T-213 sunken panels MERGED 0ec8c496; T-183 r2 pool MERGED 6380294 (7.202 m3); T-184 staircases MERGED 924c2bd (6.790 m3 measured + held; engine storey loss -2.598 m3); T-185 domes MERGED 94e39ee6 (2 shells 5.081 m3 VERIFIED); T-189 stair / beam ownership MERGED 3369f30e (system 6.675 m3); T-191 pool steel rev2, T-192 stair feet / landings vs slabs | pool, stairs, domes reconstructed; into the candidate via T-187 / T-193 | released numbers unchanged |
| (review plan R1-R9, owner 15:00) | R1 T-186 MERGED + wired (V3.0.6); R2 + R3 T-188 MERGED fb3a4623 (lift / tank gap -> T-204); R4 T-197 MERGED; R5 T-200 MERGED d699b650 (run 2 -> T-206, necks -> T-205); R6 T-194 + T-198 + T-201 MERGED (closure T-207); R7 T-196 r2 MERGED; R8 in place; R9 T-195 MERGED | 9 of 9 first passes merged | follow-ups on the board |

Day-7 target (2026-10-27): **MET on 2026-10-21 17:40**. Day-14 target (2026-11-03, measurable increase in verified coverage):
on track (22:10: since 20:10 the Checker merged T-227 r2 ebce3d97 and T-221 63f4d90e, 0 rejections; READY 4: V3.0.9a plaster / paint at Gate B (P-06 into the candidate), CONC.SLAB whole line 60.2804 m3 CLOSABLE (T-234), arched-opening fix (T-238), T-017 (evidence); floor area 20 / 47 pieces checker 0.0 %, closes after T-223 -> T-240; new whole-line closures CONC.BEAM T-241 and CONC.GROUND T-242; P-12 export T-235 now first in lane I) (20:10: V3.0.8 MERGED 3b042470 (Gate B; P-03 step 8); CONC.FOOTING and CONC.BLINDING PARTIALLY VERIFIED (25 / 26 footing outlines 64.304 m3 and footing blinding inside the plot 14.990 m3 checker 0.0 %, written to the verdict file; open: F10 + F Q-31 C, D-14, D-15, Q-21 C, band C1 Q-28 A); FLOOR AREA scoreable on the released run (385.634 vs 409.58 m2, T-216); 4 merges, 1 rejection (arched W16 read to its surround band: fix T-238 before plaster / paint / doors / windows integrate); next: T-211 plaster / paint V3.0.9 (P-06 into the candidate), checker floor-area whole line on run A) (18:20: the measure is now whole lines VERIFIED (owner 17:50): still 0 / 8 concrete; first VERIFIED block wall net 4.458 m2; footings / blinding (T-233) and slab (T-234) opened as the first concrete lines closable without a consultant answer; 3 merges, 0 rejections since 16:20) (16:20: 7 merges, 0 rejections in 2 h; straps and planted column verified -> candidate step 8 (T-231) first in lane I, then formwork / railings (T-199); blockwork programme step 1 merged, steps 2 / 3 claimable; whole lines still 0 / 8. 14:20: columns 27 / 59 re-measured, the column line blocked by D-16 / D-63 and the planted columns (T-220); finishes package V3.0.9 grows with wall tiles + kitchen; whole lines still 0 / 8. 10:20: V3.0.7 with the verified pool and dome shells at Gate B; columns 23 / 59 re-measured; floor-area line made scorable (Gate A pending); whole lines still 0 / 8): V3.0.2, V3.0.3 and V3.0.4 merged through Gate B; SCOREBOARD v2 by script (verified share still 0 / 8 whole
reference lines: the day-14 measure is the rise of that share and of coverage; the pool and stair lines are now
reconstructed and partly re-measured, so CONC.POOL is the first candidate to become whole-line VERIFIED).
