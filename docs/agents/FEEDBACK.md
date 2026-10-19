# Feedback: what came back from each task and what the Lead decided (newest first, last 20 entries)

Lead writes after every run (owner, 2026-10-18). WORKED = met its acceptance check; PARTIAL = some parts held, refused
or only partly compared; FAILED = did not deliver. Recurring causes decide the next tasks and RESEARCH_REQUESTS.md.

## Recurring causes (lead 2026-10-19 00:15)

1. **Merges are refused by the session permission check** (T-001b verifier push 22:58; T-019 worker merge 22:44 and
   worker cross-branch checkout 23:03). 0 merges in the last 5 h while 3 tasks are READY. Owner setting; reported under
   NEEDS FIXING. Until fixed, new tasks touch only new files.
2. **Missing project facts / storeys stop quantities, not code** (T-001b: plaster, paint and floor area HELD, basement
   not found). Tasks T-035, T-038; research request R-01, R-03.
3. **No Urban rule for a classification** (T-010: WC linework vs chair). Correctly stopped and asked (Q-13).

## 2026-10-19 00:15 (lead run)

| Task | Result | What went well | What went wrong and why (numbers) | Decision | Tasks created |
|---|---|---|---|---|---|
| T-001b Alsenan scoreboard run | PARTIAL | Real run on Drive DXFs (sha = manifest), 1455 lines, verifier reproduced WAPE independently; units never converted, held never compared | Only 3 of 13 keyed lines compared: concrete WAPE 17.03 % on 3 lines (pool -8.85, stairs + domes -9.83, footing -0.37 m3, all UNRESOLVED); 5 concrete lines HELD (columns 118 / 118 held, ground beams 61 / 84); plaster 1151.14 m2 and paint 1191.13 m2 HELD (no facts file); floor 409.58 m2 HELD (3 wet / dry review sets); doors 12.0 and windows 116.9 m2 refused (engine nr); basement storey not found; merge refused | Facts file from printed section heights (UP-HGT-001); held-concrete census; Q-12 hand calc; basement census; window / door m2 lines under UP-OPEN-SCHED-001 / UP-DOOR-AREA-001; merge to the owner | T-035, T-036, T-037, T-038, T-040 |
| T-034 ARCH_TAKEOFF_V2.10 (pool not a bathroom) | WORKED | One file, V2.9 byte-for-byte unchanged, L4 failing ids 390 = 390, synthetic villa with pool / master bath / car wash, held room keeps its 17.92 m2 | Nothing; tag_of / lost_labels still V1 (planned later slice) | Verifier next; merge waits on the permission fix | - |
| T-029 storey-title vocabulary | WORKED | 62 tests, 39 bilingual hand titles, unplaceable titles HELD (PENTHOUSE, LEVEL 00), opt-in only | Keeps V1 mis-reads in the new path: 'الدور الثاني عشر' -> 2F, '2ND BASEMENT' -> BASEMENT, 'LOWER GROUND' -> GF (no rule maps them); new ids 4F-10F unknown to later stages | Hold those titles in a V2 vocabulary; wire into a method version after T-034 | T-039 (queued) |
| T-010 WC vs chair | PARTIAL (blocked) | Stopped at the rule gap instead of inventing a threshold; nothing coded | Both shapes pass UP-WET-002's WC profile (pan 0.32-0.42, cistern 0.10); no rule separates them | Owner question Q-13 (asked by worker 1) | - |
| T-019 synthetic villas | FAILED (environment) | Code done earlier (3302bbc, 49 tests, 9 villa cases, 0 silent omissions) | Only the CODEMAP conflict remains; three runs refused by the permission check on merge / checkout | BLOCKED-OWNER (permission), owner merges it or allows merges | - |
