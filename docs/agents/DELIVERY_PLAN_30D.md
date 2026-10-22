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

## Status (Lead, 2026-10-22 12:20; re-estimated each run from what merged and was verified)

Baseline: the RELEASED baseline is run A (V2.9 + route G, no profile, 1,455 lines), pinned by T-165 (37124da); run B
(profiled, 1,621 lines) is the comparison base for V3.0.x line pairing. The engineering reasoning standard (owner 08:05)
governs every item; the owner's teaching case (pool, domes, two staircases, 09:40 / 11:50) is the structural priority.

| Plan | Board | State | Note |
|---|---|---|---|
| P-01 | owner + auditor | in progress, improving | 08:20 - 12:20: 7 closed slots STARTED + SUCCESS (checker 2, worker 1 2, worker 2 2, worker 3 1); worker 3's 11:01 run still open (T-167); every self-check PASS |
| P-02 | T-130 r3, T-165, T-140 (c3273f1) MERGED | DONE (registry, baseline, census V2) | |
| P-03 | T-133, T-142, T-151 r2 MERGED (V3.0.3); T-167 V3.0.4 CLAIMED 11:08; T-179 after T-167; T-146 after T-179; T-186 default guard (owner pool lesson) | V3.0.4 in work | no Gate B package READY now |
| P-04 | T-132 DONE; T-177 MERGED 12:01 (130e2e3, script); T-180 standing slot 1 / 8 reconciled, 0 / 8 VERIFIED; T-182 / T-181 next | DONE by script | pool PARTIALLY VERIFIED, not counted (owner 11:50 whole-line rule) |
| P-05 | T-126 / T-133 | DONE | |
| P-06 | T-144 MERGED; T-128 r2 READY; T-173 stair shaft TODO | rework waiting for the checker | |
| P-07 | T-125, T-143, T-169 MERGED; T-175 openings first in lane A; T-176 units; T-108 QUEUED | hand truth merged | net block after T-175 |
| P-08 | populations MERGED; T-171 notation READY; T-174 straps TODO | notation answered by investigation, Checker next run | 2,769.06 .. 2,829.83 kg HELD on the unprinted leg diameter |
| P-09 | T-134 MERGED; register rulings +5 (12:20: pool shell, staircases / shaft, domes S0, column joints, parapets / corners) | DONE (v0 code); content grows each run | |
| (Gate B tooling) | T-156 MERGED; T-168 QUEUED | after lane I's 4 TODO | |
| P-10 | T-163 formwork REJECTED (joint faces +12 %), r2 in lane S; T-170 QUEUED | started; first figures not yet verified | |
| P-11 | T-147, T-159, T-161, T-157 MERGED; T-162 r2, T-172, T-150 r2 READY; T-164 TODO | ahead of week 3 | |
| (concrete gap) | T-183 pool (rework r2), T-184 staircases, T-185 domes S0 / S1 / S2 | pool 7.202 m3 own (checker) vs engine 3.495 vs freelancer 12.348 | released numbers unchanged |

Day-7 target (2026-10-27): **MET on 2026-10-21 17:40**. Day-14 target (2026-11-03, measurable increase in verified coverage):
on track: V3.0.2 merged through Gate B 00:30; V3.0.3 (steel) merged through Gate B 08:12; SCOREBOARD v2 written 08:15
(verified share 0 / 8 whole reference lines: the day-14 measure is the rise of that share and of coverage).
