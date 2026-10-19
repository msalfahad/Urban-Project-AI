# Feedback: what came back from each task and what the Lead decided (newest first, last 20 entries)

Lead writes after every run (owner, 2026-10-18). WORKED = met its acceptance check; PARTIAL = some parts held, refused
or only partly compared; FAILED = did not deliver. Recurring causes decide the next tasks and RESEARCH_REQUESTS.md.

## Recurring causes (lead 2026-10-19 04:10)

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

## Recurring causes (lead 2026-10-19 02:20, superseded)

1. **Generated maps conflict on every second merge.** After the verifier merged T-001b and T-035 at 02:00, the verified
   T-034, T-029 and T-036 each conflict only in the generated docs/CODEMAP.md, which the verifier does not resolve.
   The earlier block (merge pushes refused) is gone; this one is structural and needs an owner decision (merge them in
   his session, or let the verifier regenerate generated maps on merge). Reported under NEEDS FIXING.
2. **Values the engine does not read from the drawing stop quantities, not code.** T-035: no wall height is printed
   (Q-14); T-036: 167 of 205 held concrete lines need storey heights, neck levels, typical ground-beam sections and
   blinding thickness that only a person-typed profile supplies (Q-17, T-044, T-046, T-045). Research R-01, R-02.
3. **No Urban rule for a classification.** T-010 (WC vs chair, Q-13), T-036 C10 (unlabelled beam span, Q-16). Stopped
   and asked; nothing assumed.

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
