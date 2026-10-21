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
| P-01 | owner + auditor | Test B; main config; Worker 1 repo-attached routine, then the others | ≥ 90 % runs with STARTED + SUCCESS over 48 h | RUN_LEDGER |
| P-02 | I | BOQ_FAMILY_MASTER 1.1.0 refreshed from code and releases (evidence per family) | every family has a status with a file:line or commit | checker spot-checks 10 |
| P-03 | I | candidate V3.0 skeleton: one opt-in method that consolidates the already verified pieces: straps 3.390 m3; wet floors 72.12 m2; 2F roof 17 rolls and pantry 2 rolls (from V2.13); facade run under Q-64 B / Q-67 A; dry-floor tiles (merged piece); 1F porcelain / landing marble under Q-66 B; 2F arrival under Q-70 A conditional | before / after table per line; every other line byte-identical to V2.9 / V2.13; rollback = run V2.9 | checker re-runs the scoreboard on V3.0 and re-measures 3 lines by hand |
| P-04 | checker | SCOREBOARD v2: per trade and unit WAPE, coverage, verified share, held = UNKNOWN share; no mixed units | table on the board | Lead reviews |
| P-05 | S | blinding scope (under ground beams and straps) and the 5 columns not on the roof-slab plans, fed into V3.0 | blinding within the hand range 20.71–26.37 m3; columns −2.27 m3 | checker hand |

## Week 2 (by 2026-11-03). Target: measurable increase in verified coverage

| Plan | Lane | Deliverable | Acceptance |
|---|---|---|---|
| P-06 | A | plaster and paint by both methods (owner manual heights G1 and drawing-derived), room by room | both results with the difference explained; checker re-measures 3 rooms |
| P-07 | A | blockwork m2 by type and thickness (Q-60 block rules, Q-69 B physical run) | GF / 1F / 2F m2 plus blocks; checker hand on 5 walls |
| P-08 | S | rebar by bar population, footings and columns first, from the schedules | rebar lines with bar marks; checker hand on 10 bars |
| P-09 | Lead + I | element register v0: stable ids for floors, rooms, walls, openings and structural elements, linked to BOQ lines (built from existing outputs, no rewrite) | every V3.0 line carries an element id plus a drawing reference |

## Weeks 3–4 (by 2026-11-19). Target: a full-villa BOQ candidate for the principal trades

| Plan | Lane | Deliverable |
|---|---|---|
| P-10 | S | formwork and excavation / backfill lines from the element register |
| P-11 | A | doors and windows as BOQ lines (schedule + knowledge 1.5.0 2.20 m fallback), wall tiles (Q-48), ceilings (Q-68 C held finish, area measured) |
| P-12 | I | V3.x reproducible full Alsenan BOQ: all principal trades present; held and unknown items listed with reason; one command; xlsx + csv |
| P-13 | checker | verified-share report on V3.x; owner release package (switch-default request with evidence) |
| P-14 | owner | authorise the formal held-out evaluation (sealed URBAN_BLIND_V2 or Qortuba) or provide an independent QS villa |

Re-estimate after each week from what actually merged into V3.0 and was verified.

## Status (Lead, 2026-10-21 08:20; re-estimated each run from what merged and was verified)

| Plan | Board | State | Note |
|---|---|---|---|
| P-01 | owner + auditor | in progress, AT RISK | Test B and the main config not confirmed. Slots 05:40-08:00: SUCCESS worker 2 05:40 and 07:40, worker 3 06:00 and 07:01, worker 1 06:21 and 07:20; no line at all: verifier 06:49 and 07:49 (and 05:49); worker 3 07:59 BLOCKED (push refused after its claim). 6 of 9 = 67 % vs 90 % (was 71 %). The checker is the bottleneck: 8 results wait |
| P-02 | T-130 r2 (lane I) | READY bead4db, first in the checker queue | census T-140 after it |
| P-03 | T-131 MERGED b1a6d6d; T-133 (V3.0.1) READY ec14d8b, PARTIAL (its own Drive run refused; checker must run it); T-142, T-146 QUEUED | skeleton DONE; first extension built | finish moves and stairs need a reading piece each (not wired) |
| P-04 | T-132 (verifier) | TODO, unblocked, not started | candidate WAPE 54.65 % on 2 concrete lines, released 17.03 % on 3 (unchanged) |
| P-05 | T-126 MERGED cd34bd0 | done as a piece; wired in T-133 (READY) | |
| P-06 | T-128 READY 69c1a0a (lane A) | hand result waiting for the checker | nets on T-144 (window heights); shaft owner column on Q-72; ceilings T-147 |
| P-07 | T-125 READY 14f554b; T-143 READY ab543b1 (hand truth); T-108 QUEUED | gross measured, waiting for the checker | 955.63 m2 gross vs 1,094.50 (-12.7 %); net on owner Q-73, black count on Q-75 |
| P-08 | T-136, T-138 r2 MERGED; T-141 READY 4f609ad; T-148 (columns, lane S) TODO | footings and ground beams DONE as pieces; span splitter waiting for the checker | straps on owner Q-74; Q-71 decides 2.74 .. 2.84 t |
| P-09 | T-134 (lane I) | TODO again (08:00 run BLOCKED on a refused push) | first in lane I |
| (gate 3 check) | T-139 READY 84d156e; T-119 READY 444e943; T-145 TODO | slabs and columns by hand waiting for the checker | slabs 60.280 hand vs 60.966 engine vs 59.817; columns 28.816 .. 28.979 vs 36.711 vs 28.547 m3 |

Day-7 target (2026-10-27): AT RISK on the checker, not on the engineering: V3.0.1 (columns -2.268 m3, blinding split
into released and held lines) is built and READY, but the checker has not run since 05:07 and must also run V3.0.1 on
the drawings itself (the worker's run was refused). If the checker merges it by 2026-10-24 the day-7 target holds.
