# Feedback: what came back from each task and what the Lead decided (newest first, last 20 entries)

Lead writes after every run (owner, 2026-10-18). WORKED = met its acceptance check; PARTIAL = some parts held, refused
or only partly compared; FAILED = did not deliver. Recurring causes decide the next tasks and RESEARCH_REQUESTS.md.

## Recurring causes (lead 2026-10-19 22:20)

1. **Merged pieces not wired into the released run** (largest): fifteen checked method pieces (now also the beam hand
   reading, the membrane fold on real rooms and the PDF opening-height reader) and the released Alsenan run is still the
   8774071 run (concrete 92.77 vs 111.81 m3). Decision: T-079 (wire wet areas and roofs) is TODO now and FIRST CODE TASK;
   the rolls-to-buy line stays HELD on owner Q-49, the area lines are ruled and released.
2. **Heights are the bottleneck for areas**: plaster 1151.14 / paint 1191.13 m2 HELD; windows 4 of 29; doors none. New
   since 20:15: the owner gave the wall-height rule (slab to slab - 0.60 - 0.15..0.20 - 0.10) and the unmarked-room rule,
   so plaster and paint can now be measured. Decision: T-081 rework (code) and T-088 (hand truth, NO REPO CODE).
3. **The Alsenan PDF sheets are raster scans** (new, verifier 21:58: sheet 09 = one image, 0 words, 0 vectors): no code
   path reads heights from them until an OCR plan reader exists (gate 4). Decision: T-083 (hand table) is the route for
   the 23 held windows and the doors; R-01 updated for OCR of dimension text on scanned elevations.
4. **Rules missing for what the owner asked**: wet-wall tile height and decor depth (Q-48), roll layout for purchase (Q-49),
   expansion-joint spacing (asked when the roof tile count exists). Asked; those parts HELD.
5. **Code runs refused for one worker**: since 20:20, workers 1 and 2 and the verifier passed every self-check step
   (worker 1 20:50 and 21:35, worker 2 22:05, verifier 22:08); worker 3 was refused twice (21:25 clone
   "[Untrusted Code Integration]", 22:03 venv "[Code from External]") and the verifier once (20:29). Better than 18:20 -
   20:20 (1 of 6). Decision: two NO REPO CODE rows kept on the board (T-088, T-083) so a refused run still moves a
   quantity; owner setting (option 2) stays under NEEDS FIXING.
6. **A run that leaves no trace** (worker 2, run fired 20:39: claimed T-083 at 20:42, no branch, no handoff, no RUN_LOG
   line). Decision: released; reported to the owner as a team-health item.
7. **Wrong times in agent text**: verifier wrote 22:30 / 22:35 for a run that pushed at 22:08; the owner's main chat
   entries are stamped about 55 minutes ahead of their commits (22:55 committed 22:01). Decision: board note (take
   `date -u`); reported in the Lead report.

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

## 2026-10-19 20:15 (lead run)

- **T-013 section binding: WORKED.** Merged 44e1502 (verifier 18:55). GF floor-to-floor 4.50 m printed, 1F 4.20 m derived,
  2F and annex HELD, slab 0.16 m owner rule. Not wired: no quantity moved. Decision: wired with T-081's room levels in T-079.
- **T-080 reference-book checks: PARTIAL.** Merged cb7407a. Book items turned into Q-40 / Q-41 / Q-42 and test spec
  T80-HGT-1; the Kuwait specification chapters 07100 / 09200 / 09300 / 09400 / 09900 are unread (file over the connector
  limit). Decision: owner upload under NEEDS FIXING (already asked; repeated); no new task until the parts exist.
- **T-081 room floor levels + finish heights V2: WORKED (READY, verifier next).** Acceptance met: GF split +1.00 / +0.30
  (engine was 0.00 from plot marks), GF +1.00 zone 4.50 m printed (was 5.50 m), 1F 4.20 m, 2F HELD; 24 non-Alsenan hand
  cases; the 0.150 m allowance and 0.10 m build-up are refused inputs (no-assumptions rule met). What did not move:
  plaster 1151.14 / paint 1191.13 m2 stay HELD (no soffit, build-up or ceiling level printed) and 21 of 27 rooms print no
  level. Decision: owner Q-43 (worker's question, kept as written); wiring in T-079.
- **T-043 beams by hand: WORKED (READY, NO REPO CODE).** 24 of 24 spans classified with sheet evidence; 5 released by
  printed sections and marks, 3.691 m3, plus 0.240 m3 of upstands the engine lacks; 19 HELD (4.25 - 9.18 m3) with reasons.
  No value from an assumption (sections read from A-A / B-B; no neighbour depth copied, owner Q-16 A). Decision: owner
  Q-44 (dome ring beam after the skylight change), engine follow-up T-085 (planted-column split, missed mark, upstands),
  designer RFIs kept HELD and listed in the report.
- **Worker runs with no result: FAILED x4.** Worker 1 18:22 (venv refused, claim refused), worker 2 18:50 (claimed T-043,
  freeze check refused, released), worker 1 19:25 (claimed T-043, DXF read refused "[PII Data Handling]", released),
  worker 3 20:03 (self-check refused, no NO REPO CODE row left). Cause 5 above. Decision: SELF-CHECK METHOD note, T-083 and
  T-084 as NO REPO CODE rows, owner setting (NEEDS FIXING).

## 2026-10-19 18:15 (lead run)

- **T-072 membrane purchase table: PARTIAL.** Merged 7b8ccfd. 14 wet areas 62.77 vs 62.43 m2 (+0.5 %), 13 rolls provisional,
  9 rows HELD never 0; the owner's 3 x 4 m kitchen reproduced exactly (16.28 m2, 2 rolls), but the strip fold ran on 0 of
  14 real rooms. Decision: T-076 (already tasked) now claimable, with the owner's Q-35 C and Q-37 A answers written in.
- **T-074 wet-area hand table: WORKED.** Merged 3d420e6. 17 areas: floor 72.122 vs 72.01 m2 (+0.16 %), boundary 144.729 vs
  144.61 lm (+0.08 %), equal to the engine piece within 0.002; walls only 127.07 lm (the Q-35 C basis). It is the truth for
  T-076.
- **T-077 lost windows: WORKED.** Merged c564481. Windows 29 drawn = 27 measured + 2 HELD (was 27 with 2 silent); doors 28
  elements, 0 silent. Width of the curved pool glazing asked (Q-38).
- **T-078 window / door m2: PARTIAL.** Merged 5f07bf0. 4 windows 13.892 vs 14.350 m2 (-3.2 %; ENGINE_RIGHT on printed
  2.30 / 1.60 vs his 2.00, and on the arched 1F living window 4.812 vs 4.650 under Q-32 A); 23 windows and all doors
  HELD: 15 on facades with no DXF elevation, 5 drawn on none, doors without height. Decision: T-082 (heights from the PDF
  elevations and section A-A); curved window width asked (Q-39).
- **T-013 section binding: WORKED (READY, verifier next).** GF +1.00 / +0.30 split, GF floor-to-floor 4.50 m printed, 1F
  4.20 m derived, 2F held, slab 0.16 owner rule; matches the hand census. Finding: engine GF plan level 0.00 from plot
  marks. Decision: T-081.
- **T-080 reference-book checks: PARTIAL (READY).** Supervisor's-eye book and waterproofing manual checked item by item
  (40 items with rule id or NO RULE); Q-40, Q-41 asked by the worker; L-1 (tile joints) asked by the Lead as Q-42; L-2 ..
  L-6 (movement joints, ground-slab DPM, primers / coats of a named system, wet-room FFL check, junction mesh) are scope
  items with no engine quantity today: kept in research/agents_t080 for later, no question now. The finish-height
  allowance 0.150 m contradicts Q-14: written into T-079 and T-081. Kuwait specification chapters not readable: owner
  asked for parts under 6 MB.
- **T-075 column schedule text rows: FAILED twice (no claim).** Classifier refused the chained claim; see cause 4.

## 2026-10-19 16:15 (lead run)

- **T-060 concrete ledger V2: WORKED.** Merged 9671133. Band 91.94 m and pool ring 2.357 m2 recovered, held per owner rules;
  1452 of 1455 lines identical. Not wired (cause 1).
- **T-065 foundations by member: WORKED.** Merged b09c06a. Isolated footings 64.346 m3 by hand = engine (freelancer 65.634,
  -2.0 %, ENGINE_RIGHT on F3 counted twice); F10 conflict -> Q-31 (filed under Answered by mistake; moved back to Open).
- **T-042 columns / necks / datum: PARTIAL.** Merged b842ec2. CN neck-only columns found (T-075 tasks it); datum not printed
  as a full arrangement, so necks / excavation / backfill stay HELD; section A-A is now on Drive as a single sheet (T-056
  reads it for stairs; the founding datum stays HELD as T-042 found).
- **T-010 wet / dry evidence: WORKED.** Merged 8fcabe0. Wet floor 72.12 vs 72.01 m2 (+0.2 %, was -12.8 %), upturn 144.73 vs
  144.61 lm, by the piece only (cause 1 -> T-079).
- **T-071 roofs: PARTIAL.** Merged 4054509. Three plan roofs 204.11 m2 = hand (ENGINE_RIGHT), total -28.4 % vs 285.00 m2
  because the 2F top roof is on no plan -> Q-34 (verifier). No-assumptions check: the 0.45 m parapet-end reach is an
  engine constant, not an owner rule; gaps above it stay HELD, so no assumed value enters a quantity (noted on T-079).
- **T-040 doors / windows: PARTIAL.** Merged 2c86de1 (research). Windows with printed heights 9.08 vs 9.70 m2 (-6.4 %,
  ENGINE_RIGHT proposals); 19 HELD (no printed height), 4 arched on Q-32, material on Q-33; 2 windows silently lost and the
  cause not traced (25-minute run, under the 50-minute rule). Decision: T-077, T-078.
- **T-072 membrane purchase table: READY, PARTIAL on its face.** 14 wet areas 62.77 vs 62.43 m2 (+0.5 %), 13 rolls
  provisional, 9 HELD rows never 0; owner's kitchen reproduced exactly; fold on 0 of 14 real rooms -> T-076; billed upturn
  110.33 vs 122.61 lm (-10.0 %) is a rule conflict, not a result -> Q-35. Verifier checks next.

## 2026-10-19 14:30 (lead run)

| Task | Result | What went well | What went wrong and why (numbers) | Decision | Tasks created |
|---|---|---|---|---|---|
| T-060 new concrete ledger (strip guard + curved strips) | WORKED (READY 662ab95) | Footing band recovered to its drawn 91.94 m (frozen 60.17 m) = 73.64 m pending + 18.30 m inside 17 members; pool wall plan 2.357 m2 = hand ring (frozen 1.24); 32 tests incl. a non-Alsenan ring and D pool, 60 synthetic villas conserve; 1452 of 1455 lines identical; freeze 0 | No quantity released by design: footing (77.27 vs 77.63 m3) and pool (3.50 vs 12.35) lines go from compared to HELD, so concrete is compared on 1 line (stair + dome 12.01 vs 21.83, WAPE 45.01 %) instead of 3 (17.03 %); 18.30 m inside members vs the hand reading 21.45 m not reconciled | Verifier merges; band volumes wait on Q-28, pool volumes now possible (Q-26 answered: flat 1.15 m, floor 0.40) via T-049; reconciliation in T-073 | T-073; T-049 promoted |
| T-065 foundations by member (hand reading) | WORKED (READY 9ea0aa0) | Isolated footings by hand 64.346 m3 = engine register (freelancer 65.634: F3 counted twice, F10 at the schedule size); straps 3.391 = freelancer 3.3925; band explained edge by edge (91.94 m, 21.45 m inside 9 footings, 70.49 m free); all from sheet evidence; own stdlib census with mirrored self-test | Section conflict B.W 20 x 60 vs typical 20 x 40 + pads (owner Q-28 asked by the worker, correctly); natural-ground boundary beam 3.526 vs freelancer 7.560 m3 (-53.4 %) not checked against the engine; engine straps 3.781 (+0.39) untraced; maps not rebuilt (repo code refused) | Verifier merges with a map rebuild; follow-up engine task for members as separate lines | T-073 |
| T-042 columns, necks, ground cell, foundation datum (hand reading) | PARTIAL (READY f826c38, 21-minute run) | Found that the column type CN is printed (neck 0.30 x 0.30, no column above ground) but drawn as plain text, so the engine drops it: 5 held CN 'columns' should be no line (freelancer 0), 6 CN necks get 0.090 m2; under every footing 10 cm plain concrete + membrane + 5 cm screed is printed; blinding 22.155 vs freelancer 47.055 m3 (-52.9 %, freelancer covers the whole plot) | Section A-A part could not be downloaded (6.37 MB, connector limit), so the founding datum stays unread; necks UNRESOLVED (engine 10.856 released + 8 held vs freelancer 8.805 m3); run far shorter than the 50-minute package | Verifier checks depth; engine fix for schedule rows drawn as text; owner asked again for single-page uploads | T-075 |
| Owner answers Q-23..Q-27 (main chat 12:55 - 14:15) | applied | Roof = bathroom rule (inside parapet + 0.20 m upturn, whole strips, 0.10 m laps); gaps covered by membrane; pool flat at 1.15 m; three domes; renovation test cancelled | "domes will not be concrete" conflicts with two structural dome shells and the freelancer's 6.78 m3: asked Q-29 | T-071, T-049 unblocked; T-068 cancelled; T-003 queued | - |
| Owner requirement: membrane purchase table | tasked | Engine already has the schedule and cutting plan | Kitchens have no waterproofing rule: asked Q-30 | Engine table + Alsenan hand truth | T-072, T-074 |

## 2026-10-19 12:20 (lead run)

| Task | Result | What went well | What went wrong and why (numbers) | Decision | Tasks created |
|---|---|---|---|---|---|
| T-058 footing-edge guard | WORKED (merged 8774071) | Verifier reproduced the Alsenan band: 91.94 m = 78.54 m measured (9.425 m3) + 13.40 m held under footings (1.608 m3) vs frozen 60.17 m; depth-checked | Not wired: concrete still 92.77 vs 111.81 m3 (-17.03 %) | Wire with the curved strips and measure (member types per Q-12 from T-065) | T-060 rewritten, TODO |
| T-061 room-label guard | WORKED (merged 362630a) | Real run: 41 labels = 30 in a room + 11 HELD (4 yard, 4 roof, 2 pool, 1 void), none lost | Not wired into a released method; roofs and pool still have no closed room | T-062 (claimed) traces why; wiring after T-010 | - |
| T-057 r2 pool check list | WORKED (merged 15de9c4) | Only a pool-named room counts (owner Q-22 = A); Alsenan: pool pump room NOT FOUND + one "use not stated" | - | none | - |
| T-019 synthetic villas | WORKED (merged 8094fcd) | 49 tests, hand truth, other layer names, rotation, mirror | - | Basis for the renovation pairs | T-068 |
| T-066 project 2 conversion loss | WORKED (READY 4c9bc0b) | 27,504 lost entities (57 %) explained: 16-bit handle mask in the pinned converter (12,567 collisions) + bare *U block names (54 doors, 50 windows, 85 room tags); with the fix 48,574 / 48,576 exact; acceptance check C1-C11 with 6 adversarial self-tests | Claimed 3 min after the owner's Alsenan-first direction; finishes not measured (no DXF passes) | Verify and merge (research only); no more project 2 work; two general defects queued | T-069, T-070 |
| T-062 roof, pool, void trace | WORKED (READY d3d5587) | Cause found for all 7 labels (outlines on a layer the room builder ignores; parapet gaps 0.075 - 0.405 m); roofs measured by hand on both edges: A 204.10 m2, B 226.21 m2 vs freelancer 285 m2 (-28.4 % / -20.6 %); synthetic fixture passes mm / m / rotated / mirrored | Handoff B total (225.947) does not equal the sum of its own roof values (226.207): verifier re-checks; no rule for the roof edge or for closing drafting gaps | Asked the owner (Q-24, Q-25); fix task held for the answers | T-071 (BLOCKED-OWNER) |
| T-067 time-boxed sheet list | FAILED (never claimed) | - | Worker 3 could not push its claim (permission refusals, 3 runs) | Folded into T-063, which worker 1 claimed at 12:25; owner asked to fix worker 3 | - |
| Owner renovation direction (11:21) | decided | Clear scope: Alsenan first, then one sealed renovation villa | No renovation rule exists | Readiness tasks provable without the villa; scope question asked | T-003 promoted, T-068, Q-23 |

## 2026-10-19 10:15 (lead run)

| Task | Result | What went well | What went wrong and why (numbers) | Decision | Tasks created |
|---|---|---|---|---|---|
| T-004a room label census | WORKED (merged 2622ddd) | Verifier reproduced the real census on the Drive DXF: 41 labels, 28 measured, 1 held, 1 unsupported, 11 silent, 47 unread SHX | 11 labelled spaces have no line | Guard and diagnostic already tasked | (T-061, T-062 TODO) |
| T-047 r2 Arabic SHX decoder | WORKED (verified 09:55, not merged) | L3 0 new failures; 121 of 121 Arabic SHX texts decoded on the real probe | Map-only conflict with 2622ddd (cause 1) | Verifier merges with map regeneration; no r3 | - |
| T-058 footing-edge guard | WORKED, pending verification (READY 10:14) | 26 hand tests (20 x 10 plot 59.20 m / 7.104 m3, rotated, mirrored, mm); Alsenan band 91.94 m = 78.54 m measured (9.425 m3) + 13.40 m held (1.608 m3) vs frozen 60.17 m (7.220 m3), freelancer 71.7 m (8.604 m3); cause named | Run took 14 min (owner wants 50-minute packages); runner reads only closed outlines on two member layers; handoff says 10:45 UTC for a 10:14 commit; band still counted against Q-12 (c), which the owner has now answered | Verifier next; wiring T-060 after merge; member split T-065 | T-065 |
| T-057 r2 pool check list | in progress (worker 2, 09:40) | - | - | Owner question for the generic pump label | Q-22 |
| Worker 1 runs 08:19, 09:19 | FAILED (no claim) | - | No claim, no push; old instructions (its 10:19 run then claimed T-061) | Owner aligns the instructions | - |
| Owner answers Q-12 - Q-17, Q-20, Q-21 | decided | Answers name exact sheets and procedures | - | Q-12 -> T-065; Q-13 -> T-010 TODO (+T-030); Q-14 -> T-063, T-013 note; Q-15 -> T-066; Q-16 -> T-043; Q-17 -> T-064; Q-20 -> T-056; Q-21 -> T-042, T-045 / T-046 held | T-063, T-064, T-065, T-066 |
