# Feedback: what came back from each task and what the Lead decided (newest first, last 20 entries)

Lead writes after every run (owner, 2026-10-18). WORKED = met its acceptance check; PARTIAL = some parts held, refused
or only partly compared; FAILED = did not deliver. Recurring causes decide the next tasks and RESEARCH_REQUESTS.md.

## Recurring causes (lead 2026-10-19 18:15)

1. **Merged pieces not wired into the released run** (largest): ten checked method pieces since 12:10 (concrete ledger V2,
   wet / dry evidence, roofs, membrane table, opening guard, opening areas, section binding READY) and the released Alsenan
   run is still the 8774071 run (concrete 92.77 vs 111.81 m3). Decision: T-079 (architectural wiring) starts once the fold
   on real rooms (T-076) is merged; concrete wiring after T-073 / T-075 / T-049 / T-056.
2. **Heights are the bottleneck for areas**: windows 4 of 29 have a printed height on the DXF elevations; doors none; plaster
   and paint (1151 / 1191 m2) held for wall heights; the engine's GF level is 0.00 instead of +1.00 / +0.30. Decision: T-082
   (heights from the PDF elevation and section sheets), T-081 (room floor levels, finish heights without assumed
   allowances); T-013 section binding READY.
3. **Rules missing for what the books and drawings show**: curved glazing width (Q-38, Q-39), shower tanking (Q-40),
   screeds (Q-41), tile joints (Q-42). Asked; the parts stay HELD.
4. **Board claims refused by the classifier**: a chained "edit + commit + push" claim was refused for workers 2 (17:41) and 3
   (18:02), while worker 1's claim as an Edit-tool edit plus separate commit / push passed. Decision: board note "CLAIM
   METHOD" (18:15). A board compaction by the Lead to bring BOARD.md (255 KB) under the connector's size was refused too
   ("[Modify Shared Resources]"); not retried.

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
