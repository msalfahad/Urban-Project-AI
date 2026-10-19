# Feedback: what came back from each task and what the Lead decided (newest first, last 20 entries)

Lead writes after every run (owner, 2026-10-18). WORKED = met its acceptance check; PARTIAL = some parts held, refused
or only partly compared; FAILED = did not deliver. Recurring causes decide the next tasks and RESEARCH_REQUESTS.md.

## Recurring causes (lead 2026-10-19 10:15)

1. **Verified work does not reach the working branch** (9 tasks: T-029, T-034, T-011, T-033, T-036, T-037, T-041, T-044 r2,
   T-047 r2; plus T-019). Why not earlier: 22:58 - 01:20 the session check refused the verifier's merge pushes; since 02:00
   merges work, but every task regenerates docs/CODEMAP.md, so each merge makes every other READY branch conflict in that
   generated file, the verifier's own instructions say "if it conflicts, do not resolve it", the r2 rebuild route (T-052)
   was refused (cross-branch fetch) and the verifier checks at most 2 tasks a run. Merged today: 6 (T-001b, T-035, T-025a,
   T-038, T-048, T-004a), none of the 8 the owner listed. Decision: the owner's merge instruction (regenerate the maps
   with the tool, then merge) is now in TEAM.md and at the top of the board with a merge order; NEEDS FIXING by the owner:
   the verifier's scheduled instructions (step 4) still say not to resolve conflicts.
2. **Scheduled sessions refuse steps**: this lead run's `git clone` of agents/control and a raw-file download were refused
   ("[Untrusted Code Integration]"); a docs-only sparse clone worked. Worker 1 claimed nothing from 07:29 to 10:20 (its 09:19
   run lasted 3.6 min with 9 claimable TODO); its instructions are the older text (private-repository clone first, no
   parallel rule, no Drive-first). NEEDS FIXING by the owner: give worker 1 the same instructions as workers 2 and 3.
3. **Arabic SHX text**: decoder verified (121 / 121); the second family (47 architectural room labels) is unread (R-02).
4. **Values the drawing does not print stop quantities**: the owner answered all eight open questions (Q-12 - Q-17,
   Q-20, Q-21); each became a task that reads the drawings first and holds what stays unprinted.
5. **Silent loss of drawn elements**: footing edge band explained (5-point sample, not covered length) and guarded
   (T-058 READY); room labels in no room (T-061 TODO).
6. **Thin tasks**: owner rule 2026-10-19: one package of at least 50 minutes per worker run; slices folded (T-030 into
   T-010, T-054 into T-016a; T-043 + Q-16 spans; T-042 + foundation levels; T-056 steps + waist + landings).

## 2026-10-19 10:15 (lead run)

| Task | Result | What went well | What went wrong and why (numbers) | Decision | Tasks created |
|---|---|---|---|---|---|
| T-004a room label census | WORKED (merged 2622ddd) | Verifier reproduced the real census on the Drive DXF: 41 labels, 28 measured, 1 held, 1 unsupported, 11 silent, 47 unread SHX | 11 labelled spaces have no line | Guard and diagnostic already tasked | (T-061, T-062 TODO) |
| T-047 r2 Arabic SHX decoder | WORKED (verified 09:55, not merged) | L3 0 new failures; 121 of 121 Arabic SHX texts decoded on the real probe | Map-only conflict with 2622ddd (cause 1) | Verifier merges with map regeneration; no r3 | - |
| T-058 footing-edge guard | WORKED, pending verification (READY 10:14) | 26 hand tests (20 x 10 plot 59.20 m / 7.104 m3, rotated, mirrored, mm); Alsenan band 91.94 m = 78.54 m measured (9.425 m3) + 13.40 m held (1.608 m3) vs frozen 60.17 m (7.220 m3), freelancer 71.7 m (8.604 m3); cause named | Run took 14 min (owner wants 50-minute packages); runner reads only closed outlines on two member layers; handoff says 10:45 UTC for a 10:14 commit; band still counted against Q-12 (c), which the owner has now answered | Verifier next; wiring T-060 after merge; member split T-065 | T-065 |
| T-057 r2 pool check list | in progress (worker 2, 09:40) | - | - | Owner question for the generic pump label | Q-22 |
| Worker 1 runs 08:19, 09:19 | FAILED (no claim) | - | No claim, no push; old instructions (its 10:19 run then claimed T-061) | Owner aligns the instructions | - |
| Owner answers Q-12 - Q-17, Q-20, Q-21 | decided | Answers name exact sheets and procedures | - | Q-12 -> T-065; Q-13 -> T-010 TODO (+T-030); Q-14 -> T-063, T-013 note; Q-15 -> T-066; Q-16 -> T-043; Q-17 -> T-064; Q-20 -> T-056; Q-21 -> T-042, T-045 / T-046 held | T-063, T-064, T-065, T-066 |

## Recurring causes (lead 2026-10-19 08:15, superseded)

1. **Verified work does not reach the working branch** (worse: 8 -> 11 tasks). T-036, T-033, T-029, T-034, T-011, T-037,
   T-041, T-044-r2 verified; T-047, T-057 reviewed; T-050 rejected on the stale map only. Every task regenerates
   docs/CODEMAP.md, so each merge makes every other READY branch conflict. Decision: verifier merges T-004a first (built
   on the current head); r2 rows for the two code tasks (T-047, T-057); the docs-only ones wait. NEEDS FIXING by the
   owner: merge them in his session, or let the verifier regenerate docs/CODEMAP.md and docs/ROUTING.md with the tool
   when a merge conflicts only in those two generated files.
2. **Scheduled sessions refuse steps** (now the verifier too): worker 1 07:24 refused cloning the working branch; worker 3
   07:00 claimed T-058 and pushed nothing, its 08:00 run ended in 3.5 min; verifier 07:55 refused running task-branch
   tests (gates b, c not run on T-047, T-057). Decision: reported to the owner (team health); claims without a push go
   back to TODO each lead run.
3. **Arabic SHX text is invisible** (T-044, T-033, T-004a: 47 x-arab1b room labels unread): T-047 r2; R-02 updated.
4. **Values the drawing does not print stop quantities** (Q-14, Q-17, Q-20, Q-21; roof edge basis after T-062).
5. **Silent loss of drawn elements** (T-037, T-050, T-048, T-004a): strips explained by a member, curved pairs, labels in
   no closed room. Decision: T-058 (strip guard), T-060 (wiring, queued), T-061 (label guard), T-062 (diagnostic).
6. **The 37.5 MB Alsenan architectural PDF is over the 10 MB Drive limit**: NEEDS FIXING (owner), still open.

## 2026-10-19 08:15 (lead run)

| Task | Result | What went well | What went wrong and why (numbers) | Decision | Tasks created |
|---|---|---|---|---|---|
| T-048 curved strips | WORKED (merged fd0d5dd) | 30 hand tests, verifier's own bulge check 1.947787 m2; widths never defaulted | Not wired yet | Wire after T-058 | (T-060 waits on T-058 only) |
| T-050 footing ring edges | WORKED in substance; REJECTED gate c (map stale) | Verifier ran edge_trace.py: 31.77 m / 3.81 m3 silent loss confirmed | Docs-only r2 is cause 1 | Fix is T-058; note waits for the owner's map-merge fix | - |
| T-047 Arabic SHX decoder | WORKED (static review; not merged) | 18 hand tests; unknown font / unmapped code HELD, never guessed | Map conflict with fd0d5dd; verifier could not run tests (cause 2) | r2 rebuild | T-047 row back to TODO (r2) |
| T-057 pool check list | PARTIAL (static review; not merged) | 47 tests; Alsenan POOL_PUMP_ROOM_NOT_FOUND matches the owner's hand check | Any bare PUMP label (water / booster pump) would count as the pool pump room, so the Q-19 check could never report NOT_FOUND on such a villa | r2 rework: other-use pumps excluded, generic pump label HELD (owner decides), adversarial tests | T-057 row back to TODO (r2) |
| T-004a room label census | WORKED (READY, clean on the head) | Planted omission found; 41 labels: 28 measured, 1 held, 1 unsupported | 11 labels silently lost (yards 4, pool 2, roof 4, void 1); 47 x-arab1b labels unread | Label guard; diagnostic with A / B roof areas before the owner question; pool vocab already in T-034; yard scope OQ-04 unresolved, nothing released | T-061, T-062 |
| T-058 strip guard | FAILED (claim, no push) | - | Worker 3 07:00 run pushed no branch and no handoff | Back to TODO, same scope | - |

## 2026-10-19 06:15 (lead run)

| Task | Result | What went well | What went wrong and why (numbers) | Decision | Tasks created |
|---|---|---|---|---|---|
| T-038 basement census | WORKED (merged fa93ec2) | Storeys ENGINE_RIGHT (no basement drawn) | Lift walls 2.40 m3 UNRESOLVED (no lift drawn) | Storey check queued | (T-051) |
| T-037 Q-12 hand calculation | WORKED (verified, not merged: map conflict) | Verdicts recorded: pool floor and wall plan FREELANCER_RIGHT; pool, stair + dome, edge strip UNRESOLVED | Cannot merge (cause 1) | Owner merge | - |
| T-044-r2 profile audit | WORKED (verified, not merged: map conflict) | SHX Arabic decoded by hand: 15 PRINTED, 1 DIFFERENT, 1 NOT_PRINTED; bucket D empty | Printed 1.50 m is an excavation level; whether the blinding sits inside it is set by no rule (28 necks, 10 cm each) | Owner question, not decided by the team | Q-21 |
| T-041 lost ground band | WORKED (verified, not merged) | No silent omission; handle matching method | - | - | - |
| T-048 curved strips | WORKED (READY) | 30 hand tests (D pool 1.319469 m2, round pool 3.110177 m2, rotated, mirrored, mm / m, held, ambiguous); widths never defaulted; freeze 0 | Not wired; Alsenan pool (2.358 m2 drawn) not run | Wire after merge | T-060 (queued) |
| T-050 footing ring edges | PARTIAL (READY) | All 8 edges traced by handle: 91.94 m drawn, 60.17 m kept; drop at concrete_completeness.py:864-868 then :1274 | Script not run (session refused running repo code); 31.77 m / 3.81 m3 silently lost | Guard task; verifier runs the script | T-058 |
| T-052 r2 rebuilds | FAILED (permission refusal) | Worker stopped cleanly and reported the exact refusal | Cross-branch fetch refused | Owner fixes; not retried | - |

## Recurring causes (lead 2026-10-19 04:10, superseded)

1. **Generated maps conflict on merge.** Still holds T-036, T-033, T-029, T-034 (and T-019). Clean merges work again
   (T-025a merged 2748ffe because it was built on the head). Decision: T-052 rebuilds the docs-only ones as r2 branches
   (TEAM.md rule, blob by blob, no merge, no checkout); if refused, the refusal text goes to the owner.
2. **Arabic SHX text is invisible** (new, two villas): T-044's audit missed a printed founding depth because the Arabic
   note is in an SHX font stored as Latin keyboard codes; T-033 saw the same on development project 2. Decision: T-047
   decoder; R-02 updated.
3. **Engine conventions make numbers where the drawing prints nothing** (new): T-037 found pool floor 0.25 (0.40 printed),
   dome rise and shell guessed (3.69 vs 2.54 m3 per dome by hand), stair waist unprinted but released. Decision: owner
   Q-19, Q-18; T-049 (printed detail dimensions outrank conventions).
4. **Values not read from the drawing stop quantities** (Q-14, Q-17, T-044, T-046, T-045; R-01, R-02).
5. **The 37.5 MB Alsenan architectural PDF is over the 10 MB Drive download limit** (T-035, T-037, T-038 could not read
   it: pool depth "as per architectural", stairs, lift walls). Only the owner can fix it (split under 10 MB): NEEDS FIXING.
6. **Silent worker runs**: two runs (worker 2 01:40 on T-004a, worker 3 02:00 on T-016a) claimed and pushed nothing. Both
   tasks narrowed and back to TODO; every task text now says to push partial work and a handoff before the hour ends.

## 2026-10-19 04:10 (lead run)

| Task | Result | What went well | What went wrong and why (numbers) | Decision | Tasks created |
|---|---|---|---|---|---|
| T-025a CAD limit census | WORKED (merged 2748ffe) | 27 tests on hand DXF (4001 / 3999 / 6001 layers, rotated, mirrored, mm and m); every over-cap layer becomes a HELD LIMIT record; frozen files untouched; lead re-check of the head: maps stale none, freeze 0 | Not wired into a method yet; 4 caps outside its list still skip silently | Next slice | T-025b (queued) |
| T-044 route G profile audit | FAILED (rejected) | 17 keys classified with sheet evidence, 17 one-key ablations, buckets reproduced by the verifier | FOUNDING_DEPTH_M base 1.50 called NOT_PRINTED, but it is printed as an Arabic SHX note on the schedules sheet (28 necks, 10.856 m3 put in the wrong bucket); the Q-17 bullet built on it is wrong | Rework the same task with the exact fault named; build the SHX decoder | T-044 (TODO rework), T-047 |
| T-037 Q-12 hand calculation | WORKED (READY) | Term-by-term from printed dimensions; found the freelancer's "basement" is stairs + domes, not a storey | Engine pool 3.50 m3 misses the curved half and uses floor 0.25 vs printed 0.40; domes guessed 3.69 vs 2.54 m3 by hand; footing strip 2 of 8 edges lost (60.17 of 91.94 m); pool depth, stair waist not printed / in the unreadable architectural PDF | Fix tasks; owner questions for the dome basis and for conventions; PDF to the owner | T-048, T-049 (queued), T-050; Q-18, Q-19 |
| T-038 basement census | WORKED (READY) | 5 frames listed; no basement plan or level below 0.00 anywhere: storeys ENGINE_RIGHT proposed | Lift walls 2.40 m3 (freelancer "basement") have no drawn lift in either DXF; PDF unreadable | Storey completeness check as a general guard | T-051 (queued) |
| T-041 lost ground band | WORKED (READY) | Matched runs by source handles: all 59 bands accounted for, no silent omission | The T-036 "1 band lost" note was an id shift (width-order ids) | T-036 note corrected; handle matching reused in T-050 | - |
| T-011 knowledge 1.6.0 doors | PENDING (verifier checking) | 37 tests, 1.5.0 untouched, no method reads 1.6.0 | Full suite not completed by the worker (verifier runs L4) | Wire into a method after merge | T-055 (queued) |
| T-033 dev project 2 audit | WORKED (verified, not merged: CODEMAP conflict) | Reproduced by the verifier from Drive | Merge conflicts only in docs/CODEMAP.md | r2 rebuild | T-052 |
| T-004a, T-016a | FAILED (no delivery) | - | Runs claimed at 01:40 / 02:00, no branch, no handoff; next runs moved on (probably ran out of time: both tasks were large) | Narrowed (rooms only; 5 of 10 changes), back to TODO; second halves queued | T-053, T-054 (queued) |

## 2026-10-19 02:20 (lead run)

| Task | Result | What went well | What went wrong and why (numbers) | Decision | Tasks created |
|---|---|---|---|---|---|
| T-001b Alsenan scoreboard run | WORKED (merged b5475db) | First scoreboard measured on the working branch; verifier reproduced it | Same gaps as before (3 of 13 keys compared, concrete WAPE 17.03 %, 3 UNRESOLVED Q-12) | Gaps already tasked (T-035..T-040) | - |
| T-035 Alsenan facts file (heights) | WORKED (merged 56820cb) | Read every text of every readable sheet; refused floor-to-floor, beam depths and T = 10 cm as heights (UP-HGT-001); rerun identical, nothing assumed | Plaster 29 and paint 13 lines stay HELD: no wall height or height component printed; the 37.5 MB arch PDF is over the 10 MB limit | Owner question Q-14 (asked by the worker); section binding T-013 for the 2F level | - |
| T-036 held-concrete census | WORKED (verified, merge waits on CODEMAP conflict) | 205 held lines = 12 causes, counts reproduced by the verifier; found that 167 (81 %) are held only for want of the route G profile | With the typed profile 1 ground band (1.886 m2 plan) appears in no output: possible silent omission; neck lines rest on an unprinted founding depth 2.0 (OQ-13); run B WAPE 18.17 % on 5 lines, all UNRESOLVED | Trace the band first; audit the profile value by value; ask the owner whether a score may rest on typed values and how to size unlabelled spans; hand reads of the 27 still-held lines | T-041, T-044, T-042, T-043 (queued), T-045 (queued), T-046 (queued); Q-16, Q-17 |
| T-033 development project 2 CAD audit | PARTIAL | Pinned LibreDWG, per-entity counts, no data committed | Conversion lossy (21,072 of 48,576 entities kept, 57 % lost); the -STR.dwg is structural with an architectural background, 0 English room labels; the PDF names a different DWG | Re-ask the owner as Q-11's answer says | Q-15 |
| T-034, T-029 (verified 01:20) | WORKED (not merged) | All gates pass, L4 id for id | Merge conflicts in generated docs/CODEMAP.md after the 02:00 merges | Left READY for the owner (NEEDS FIXING) | - |

## 2026-10-19 00:15 (lead run)

| Task | Result | What went well | What went wrong and why (numbers) | Decision | Tasks created |
|---|---|---|---|---|---|
| T-001b Alsenan scoreboard run | PARTIAL | Real run on Drive DXFs (sha = manifest), 1455 lines, verifier reproduced WAPE independently; units never converted, held never compared | Only 3 of 13 keyed lines compared: concrete WAPE 17.03 % on 3 lines (pool -8.85, stairs + domes -9.83, footing -0.37 m3, all UNRESOLVED); 5 concrete lines HELD (columns 118 / 118 held, ground beams 61 / 84); plaster 1151.14 m2 and paint 1191.13 m2 HELD (no facts file); floor 409.58 m2 HELD (3 wet / dry review sets); doors 12.0 and windows 116.9 m2 refused (engine nr); basement storey not found; merge refused | Facts file from printed section heights (UP-HGT-001); held-concrete census; Q-12 hand calc; basement census; window / door m2 lines under UP-OPEN-SCHED-001 / UP-DOOR-AREA-001; merge to the owner | T-035, T-036, T-037, T-038, T-040 |
| T-034 ARCH_TAKEOFF_V2.10 (pool not a bathroom) | WORKED | One file, V2.9 byte-for-byte unchanged, L4 failing ids 390 = 390, synthetic villa with pool / master bath / car wash, held room keeps its 17.92 m2 | Nothing; tag_of / lost_labels still V1 (planned later slice) | Verifier next; merge waits on the permission fix | - |
| T-029 storey-title vocabulary | WORKED | 62 tests, 39 bilingual hand titles, unplaceable titles HELD (PENTHOUSE, LEVEL 00), opt-in only | Keeps V1 mis-reads in the new path: 'الدور الثاني عشر' -> 2F, '2ND BASEMENT' -> BASEMENT, 'LOWER GROUND' -> GF (no rule maps them); new ids 4F-10F unknown to later stages | Hold those titles in a V2 vocabulary; wire into a method version after T-034 | T-039 (queued) |
| T-010 WC vs chair | PARTIAL (blocked) | Stopped at the rule gap instead of inventing a threshold; nothing coded | Both shapes pass UP-WET-002's WC profile (pan 0.32-0.42, cistern 0.10); no rule separates them | Owner question Q-13 (asked by worker 1) | - |
| T-019 synthetic villas | FAILED (environment) | Code done earlier (3302bbc, 49 tests, 9 villa cases, 0 silent omissions) | Only the CODEMAP conflict remains; three runs refused by the permission check on merge / checkout | BLOCKED-OWNER (permission), owner merges it or allows merges | - |
