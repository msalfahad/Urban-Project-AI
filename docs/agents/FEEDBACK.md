# Feedback: what came back from each task and what the Lead decided (newest first, last 20 entries)

Lead writes after every run (owner, 2026-10-18). WORKED = met its acceptance check; PARTIAL = some parts held, refused
or only partly compared; FAILED = did not deliver. Recurring causes decide the next tasks and RESEARCH_REQUESTS.md.

## Recurring causes (lead 2026-10-19 02:20)

1. **Generated maps conflict on every second merge.** After the verifier merged T-001b and T-035 at 02:00, the verified
   T-034, T-029 and T-036 each conflict only in the generated docs/CODEMAP.md, which the verifier does not resolve.
   The earlier block (merge pushes refused) is gone; this one is structural and needs an owner decision (merge them in
   his session, or let the verifier regenerate generated maps on merge). Reported under NEEDS FIXING.
2. **Values the engine does not read from the drawing stop quantities, not code.** T-035: no wall height is printed
   (Q-14); T-036: 167 of 205 held concrete lines need storey heights, neck levels, typical ground-beam sections and
   blinding thickness that only a person-typed profile supplies (Q-17, T-044, T-046, T-045). Research R-01, R-02.
3. **No Urban rule for a classification.** T-010 (WC vs chair, Q-13), T-036 C10 (unlabelled beam span, Q-16). Stopped
   and asked; nothing assumed.

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
