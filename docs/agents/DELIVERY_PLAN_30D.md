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

## Status (Lead, 2026-10-21 12:20; re-estimated each run from what merged and was verified)

| Plan | Board | State | Note |
|---|---|---|---|
| P-01 | owner + auditor | in progress, AT RISK (the critical path) | Test B ran 10:23 / 10:49 on agents/config-candidate (53468f6): BLOCKED on step 5; main config not approved. Since 08:20: SUCCESS worker 1 08:19 and 10:21, worker 2 09:40 and 11:40; no record at all: checker 09:50 and 11:50 (also 05:49, 06:49, 07:49), worker 3 10:59; worker 3 08:00 BLOCKED (push refused). 4 of 7 slots = 57 % vs 90 % |
| P-02 | T-130 r2 (lane I) | READY bead4db, first in the checker queue | census T-140 after it |
| P-03 | T-131 MERGED b1a6d6d; T-133 (V3.0.1) READY ec14d8b PARTIAL; T-142, T-146, T-151 QUEUED | skeleton DONE; first extension waiting for the checker | the checker must run V3.0.1 on the drawings itself |
| P-04 | T-132 (verifier) | TODO, not started | candidate WAPE 54.65 % on 2 concrete lines, released 17.03 % on 3 (unchanged) |
| P-05 | T-126 MERGED cd34bd0 | done as a piece; wired in T-133 (READY) | |
| P-06 | T-128, T-144 READY (lane A) | hand results waiting for the checker | drawing-derived dry net incl. shaft 976.22 .. 1,080.33 vs 1,151.14 m2; owner method on Q-72 for the shaft; 23 openings on D-45 |
| P-07 | T-125, T-143 READY; T-108 QUEUED | gross measured, waiting for the checker | net on owner Q-73, black count on Q-75 |
| P-08 | T-136, T-138 r2 MERGED; T-141, T-148 READY; T-149 (beams), T-152 (slabs) TODO | footings, ground beams, columns DONE as hand pieces; beams and slabs next | links / per-metre counts on Q-71 (now also columns 0.78 .. 0.83 t) |
| P-09 | T-134 (lane I) | TODO (worker 3 has delivered nothing since 07:37) | first in lane I |
| P-11 | T-147 READY (ceilings); T-150 (doors, windows) TODO | started ahead of week 3 | ceilings 388.14 vs 409.58 m2 (-5.2 %) |
| (gate 1) | T-153 TODO | floor area room by room, 11 held spaces | |
| (gate 3 check) | T-139, T-145, T-119 READY | slabs, slab leftovers and columns by hand waiting for the checker | slabs 60.280 vs 59.817; beams 65.060 vs 65.97; columns 28.816 .. 28.979 vs 28.547 m3 |

Day-7 target (2026-10-27): AT RISK on the checker only. The engineering for it (V3.0.1: columns -2.268 m3, blinding split
into released and held lines) has been READY since 07:37; the checker has merged nothing since 05:07. If it merges
V3.0.1 by 2026-10-24 the target holds; every extra day without the checker costs one day of the 6 days left.
