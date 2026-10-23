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

## Status (Lead, 2026-10-23 00:20; re-estimated each run from what merged and was verified)

Baseline: the RELEASED baseline is run A (V2.9 + route G, no profile, 1,455 lines), pinned by T-165 (37124da); run B
(profiled, 1,621 lines) is the comparison base for V3.0.x line pairing. The engineering reasoning standard (owner 08:05)
governs every item; the owner's teaching case (pool, domes, two staircases, 09:40 / 11:50) is the structural priority;
WORKFLOW_CONTROLS section 10 (owner 15:15: faster execution, same evidence) governs how work flows.

| Plan | Board | State | Note |
|---|---|---|---|
| P-01 | owner + auditor | in progress, improving | 20:20 - 00:20: 8 closed slots STARTED + final SUCCESS (worker 1 2, worker 2 2, worker 3 2, checker 2: 19:51 closed 21:04, 21:50 closed 22:00); checker 23:51 open at 00:20 (3 merges committed); every self-check PASS; 0 refusals; one board rebase conflict (worker 1 20:21, resolved) |
| P-02 | T-130 r3, T-165, T-140 MERGED | DONE (registry, baseline, census V2) | |
| P-03 | V3.0.4 MERGED (Gate B cf5819c); T-179 V3.0.5 r1 REJECTED 21:04 (stair range high end on count A, -65.02 kg), r2 READY 23:39 (held 15,250.79 .. 21,621.55 kg; candidate rebar quantity lines 10,250.17 kg; beams 65.294 m3; NOT RELEASED); chain T-190 (firewall fix) -> T-187 V3.0.6 -> T-193 V3.0.7 (verified pool 7.202 + dome shells 5.081 m3) -> T-199 V3.0.8 (formwork + railings, missing categories) -> T-146; T-168 Gate B tool v2 promoted | V3.0.5 r2 at the checker | integrates: T-152, T-166, T-160 / T-186, T-184, T-189 / T-183, T-185 / T-163, T-164 |
| P-04 | T-132 DONE; T-177 and T-182 (five measures, 50991742) MERGED; T-181 claimable; T-180 slot: pool and 2 stair flights reconciled, 0 / 8 VERIFIED | script DONE; five measures in the checker queue | whole-line rule (owner 11:50) |
| P-05 | T-126 / T-133 | DONE | |
| P-06 | T-128 r3 MERGED a6ac2c66 (3 rooms checker 0.0 %); T-173 stair shaft MERGED 8b4d2c83 | hand package DONE; engine line not yet (scoreboard plaster / paint NOT YET MEASURED until a candidate line exists) | integration task to plan once the candidate chain frees lane I |
| P-07 | T-125, T-143, T-169, T-175 (b903360c) MERGED; T-194 opening consistency MERGED (3 openings missing from the list); T-198 census r3 first in lane A, T-176 units after it; T-108 QUEUED | net block candidate on 43 walls | 43 walls carry a net (476.21 m2 candidate), 28 openings HELD |
| P-08 | populations MERGED; T-171 notation MERGED 701d227 (2,769.06 .. 2,829.83 kg HELD on the unprinted leg diameter); T-174 straps TODO | notation DONE by investigation | |
| P-09 | T-134 MERGED; register rulings +7 (16:20: staircase identity corrected, shaft walls, opening deductions, pool upstand, 1F-11 curved glazing, default guard, corners pair) | DONE (v0 code); content grows each run | |
| (Gate B tooling) | T-156 MERGED; T-168 QUEUED (after T-182, same scorer) | | |
| P-10 | T-163 formwork r3 MERGED 659f889f (above ground calculated 1,078.274 m2; dome soffits checker 0.00 %; joint faces PARTIALLY VERIFIED 2 / 27); into the candidate by T-199; T-170 excavation levels QUEUED | formwork hand package DONE; excavation not started | |
| P-11 | T-147, T-159, T-161, T-157, T-150 r2, T-172, T-162 r2, T-164 (390fabf4), T-181 (faa04202) MERGED; T-198 census r3 | ahead of week 3 | |
| (concrete gap) | T-183 r2 pool MERGED 6380294 (7.202 m3); T-184 staircases MERGED 924c2bd (6.790 m3 measured + held; engine storey loss -2.598 m3); T-185 domes MERGED 94e39ee6 (2 shells 5.081 m3 VERIFIED); T-189 stair / beam ownership MERGED 3369f30e (system 6.675 m3); T-191 pool steel rev2, T-192 stair feet / landings vs slabs | pool, stairs, domes reconstructed; into the candidate via T-187 / T-193 | released numbers unchanged |
| (review plan R1-R9, owner 15:00) | R1 = T-186 MERGED (wiring T-187, firewall fix T-190); R2 + R3 = T-188 TODO; R4 = T-197 TODO; R6 = T-194 MERGED; R7 = T-196 TODO; R9 = T-195 MERGED; R5 = T-170 QUEUED; R8 in place (scenario rule) | 2 of 9 merged, 1 in place | |

Day-7 target (2026-10-27): **MET on 2026-10-21 17:40**. Day-14 target (2026-11-03, measurable increase in verified coverage):
on track: V3.0.2, V3.0.3 and V3.0.4 merged through Gate B; SCOREBOARD v2 by script (verified share still 0 / 8 whole
reference lines: the day-14 measure is the rise of that share and of coverage; the pool and stair lines are now
reconstructed and partly re-measured, so CONC.POOL is the first candidate to become whole-line VERIFIED).
