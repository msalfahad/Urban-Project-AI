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

## Status (Lead, 2026-10-20 22:15; re-estimated each run from what merged and was verified)

| Plan | Board | State | Note |
|---|---|---|---|
| P-01 | owner + auditor | in progress, at risk | Test B and the main config not confirmed. Slots fired 20:19-21:59: 6 of 8 worker / verifier runs closed with STARTED + SUCCESS; worker 2 21:39 left nothing, worker 3 21:59 left a STARTED line only |
| P-02 | T-130 (lane I) | TODO | unclaimed: worker 3's 21:59 run ended silently |
| P-03 | T-131 (lane I) READY 33f1da2; T-133 (V3.0.1) TODO | READY for the checker | skeleton: straps 3.781 -> 3.390 m3, GF facade 98.887 -> 105.887 lm (Q-67 A), 1F porcelain range 38.459 .. 38.979; 1519 of 1528 lines byte-identical; L4 396 = 396. V3.0.1 adds the merged landing / arrival (Q-66 B, Q-70 A), columns -2.268 m3 and blinding 15.179 + held |
| P-04 | T-132 (verifier) | TODO | verifier only; run it on V3.0 once T-131 merges |
| P-05 | T-126 MERGED cd34bd0 | done as a piece; wiring in T-133 | checker re-measured the footing blinding union itself (151.794 m2 x 0.10 = 15.179 m3); columns -2.268 m3 |
| P-06 | T-128 (lane A) | TODO | |
| P-07 | T-125 then T-108 (lane A) | T-125 TODO | |
| P-08 | T-136 (lane S, first slice of T-009) | TODO, waits for T-105 to merge | footings by bar population first |
| P-09 | T-134 (lane I) | TODO, waits for T-131 | design v0 in ELEMENT_REGISTER.md |

Day-7 target (2026-10-27): ON TRACK IF the checker merges T-131 and re-measures 3 of its lines in one of its next runs; the
skeleton is the first improvement that can go through the integrated pipeline (straps -0.07 % against the freelancer).
