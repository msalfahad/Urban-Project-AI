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

## Status (Lead, 2026-10-22 04:20; re-estimated each run from what merged and was verified)

Baseline (Lead ruling 04:20, from T-165): the RELEASED baseline is run A (V2.9 + route G, no profile, 1,455 lines); run B
(profiled, 1,621 lines) is the comparison base for V3.0.x line pairing. Every Gate B verdict gives both diffs.

| Plan | Board | State | Note |
|---|---|---|---|
| P-01 | owner + auditor | in progress, improving | Worker 1, Checker, Worker 3 migrated and run clean; Lead repo-attached since 00:12 (two clean runs incl. this one); Worker 2 next. 00:20 - 04:20: 9 of 9 closed slots STARTED + SUCCESS, every self-check PASS |
| P-02 | T-130 r3 MERGED; T-140 census V2 READY; T-165 baseline READY | DONE (registry); census and baseline waiting for the checker | baseline ruled (run A) |
| P-03 | T-133, T-142 MERGED (Gate B); T-151 V3.0.3 READY (Gate B, 3 slices); T-167 TODO after T-151; T-146 QUEUED after T-167 | third extension waiting for Gate B | V3.0.3: column steel 1,887.13 kg + ground beams 1,252.91 + beams 5,171.03 kg DRAWING-CONFIRMED (13 lines VERIFIED), rest HELD / UNKNOWN; route steel 14,219 kg superseded, not summed |
| P-04 | T-132 (checker) | TODO, after READY <= 3, on baseline A + the candidate | |
| P-05 | T-126 / T-133 | DONE | |
| P-06 | T-144 MERGED; T-128 REJECTED -> r2 TODO | rework | curved rooms re-walked on verified boundaries |
| P-07 | T-125, T-143 MERGED; T-169 TODO (defect fix); T-108 QUEUED | hand truth merged; automation after T-169 | net on Q-73, black count on Q-75 |
| P-08 | T-136, T-138 r2, T-148, T-149, T-152, T-155 r2 MERGED; T-166 READY | footings, ground beams, columns, beams, slabs DONE as verified hand pieces; stairs / pool / tank waiting | 6.74 .. 7.15 t held on Q-71 |
| P-09 | T-134 MERGED; register rulings +14 (04:20) | DONE (v0 code); content grows each run | |
| (Gate B tooling) | T-156 MERGED; T-168 TODO after T-165 | v2 queued | manifests checked |
| P-10 | T-163 formwork TODO (permitted); T-170 levels for excavation TODO | started (missing categories) | excavation needs the Q-21 C level chain first |
| P-11 | T-147, T-159, T-161 MERGED; T-157, T-162 READY; T-150 r2 TODO; T-164 TODO | ahead of week 3 | main door and W16 HELD |
| (gate 1) | T-153 MERGED; T-157 READY | floor area VERIFIED in part; outside areas waiting | porch floor 10.680 vs soffit 19.181 explained |
| (concrete gap) | T-049 TODO (pool) | queued | pool 3.50 vs 12.35 m3 |

Day-7 target (2026-10-27): **MET on 2026-10-21 17:40**. Day-14 target (2026-11-03, measurable increase in verified coverage):
on track: V3.0.2 merged through Gate B 00:30; V3.0.3 (steel) in Gate B over the next two checker runs; measurement needs
SCOREBOARD v2 (T-132) on baseline A, which waits only on READY <= 3.
