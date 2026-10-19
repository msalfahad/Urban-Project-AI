# Feedback: what came back from each task and what the Lead decided (newest first, last 20 entries)

Lead writes after every run (owner, 2026-10-18). WORKED = met its acceptance check; PARTIAL = some parts held, refused
or only partly compared; FAILED = did not deliver. Recurring causes decide the next tasks and RESEARCH_REQUESTS.md.

## Recurring causes (lead 2026-10-19 14:30)

1. **Repo code refused for workers 2 and 3**: worker 2 at 14:02 again could not clone the working branch or pip-install
   ("[Untrusted Code Integration]") and delivered by hand reading and the GitHub connector; worker 3 claimed a hand-reading
   task at 14:00. list_triggers shows the same approval setting (auto) for all three workers and the verifier, so the
   refusals come from the per-command auto-mode check, not a visible task setting. Decision: NO REPO CODE rows kept on the
   board for them (T-074, T-043); owner asked to add explicit allow rules (lead report, NEEDS FIXING).
2. **Drawn members that the engine does not see as members**: footings drawn as block inserts on another layer or as open
   outlines (8.05 m of band wrongly measured, T-065); exterior outlines on an OTHER layer (T-062). Decision: T-073 (plot-edge
   members) and T-071 (exterior spaces); research request R-05 asks for general member detection from inserts and open outlines.
3. **Merged pieces not wired into the released run**: T-060 now gives one new concrete ledger version, but it is opt-in;
   the released Alsenan run still reads concrete 92.77 vs 111.81 m3. Wiring is an owner step once the member types (Q-28)
   and the dome basis (Q-29) are answered.
4. **Rules missing for what the drawing shows**: band section (Q-28), domes concrete or finish (Q-29), kitchen waterproofing
   (Q-30). Each asked; the affected lines stay HELD.
5. **Drive parts too big for the connector**: architectural PDF parts 03-04 (6.79 MB) and 09-10 (6.37 MB) cannot be read
   (practical limit about 6.2 MB); the stair section may be on them. Owner asked to upload single pages.

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
