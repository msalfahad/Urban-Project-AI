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

## Status (Lead, 2026-10-22 00:20; re-estimated each run from what merged and was verified)

| Plan | Board | State | Note |
|---|---|---|---|
| P-01 | owner + auditor | in progress, improving | Worker 1, Checker, Worker 3 migrated and ran clean; Lead's first repo-attached run is this one (setup by hand again: .work absent at start); Worker 2 next. 20:20 - 00:20: every closed slot has STARTED + final line; checker 23:51 still running |
| P-02 | T-130 r3 MERGED 78f0aac; T-140 census V2 READY | DONE (registry); census waiting | T-140: two runs are both called released V2.9 + route G -> T-165 pins the baseline |
| P-03 | T-133 MERGED (Gate B); T-142 V3.0.2 READY (Gate B); T-151 TODO after T-142 (steel); T-146 QUEUED after T-151 + T-139 r2 | second extension waiting for Gate B | V3.0.2: footing steel 3,735.91 -> 874.86 kg drawing-confirmed + 2,742.51 .. 2,836.40 HELD; soffits 44.446 m2; 1,647 lines byte-identical |
| P-04 | T-132 (checker) | TODO, after READY <= 3, on the T-165 baseline | |
| P-05 | T-126 / T-133 | DONE | |
| P-06 | T-144 MERGED; T-128 READY | waiting for the checker | stair shaft on Q-72 |
| P-07 | T-125, T-143 READY; T-108 QUEUED | waiting for the checker | net on Q-73, black count on Q-75 |
| P-08 | T-136, T-138 r2, T-148, T-149, T-155 r2 MERGED; T-152 READY; T-166 TODO | footings, ground beams, columns, beams DONE as verified hand pieces; slabs waiting; stairs / pool / tank next | counts on Q-71 (now 6.38 .. 6.73 t of held steel) |
| P-09 | T-134 MERGED 0c8eae7; register rulings +12 (00:20) | DONE (v0 code); content grows each run | |
| (Gate B tooling) | T-156 MERGED a9c47f1 | DONE | |
| P-10 | T-163 formwork TODO; excavation not started (OQ-13 / Q-21 C) | queued (missing category) | formwork alternatives OQ-10 / OQ-11 side by side |
| P-11 | T-147, T-150, T-159, T-161 READY; T-157, T-162, T-164 TODO | started ahead of week 3 | outdoor finish lines by the owner rule; railings / shutters missing category |
| (gate 1) | T-153 MERGED; T-157 TODO (permitted) | floor area VERIFIED in part | OQ-04 answered |

Day-7 target (2026-10-27): **MET on 2026-10-21 17:40**. Day-14 target (2026-11-03, measurable increase in verified coverage):
on track if T-142 passes Gate B in the next checker run and T-151 (steel) follows within two days; measurement needs SCOREBOARD
v2 (T-132) on one pinned baseline (T-165).
