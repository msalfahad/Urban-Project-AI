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

## Status (Lead, 2026-10-21 20:20; re-estimated each run from what merged and was verified)

| Plan | Board | State | Note |
|---|---|---|---|
| P-01 | owner + auditor | in progress, improving | Worker 1 (16:19, 18:21) and the checker (17:52) ran clean on the repo-attached setup; Worker 3 migrates at its 20:59 run; Lead next. Since 15:51 every slot has a final line; the SessionStart hook still does not run by itself (agents run setup by hand, it works) |
| P-02 | T-130 r3 (lane I) | READY 3f23e23, checker run A | r2 rejected 16:45 (footings must be PARTIAL, 3 wrong citations); census T-140 after it |
| P-03 | T-133 MERGED 967d6d5 (Gate B, PARTIAL); T-142 TODO (+ defects D1-D3); T-146, T-151 QUEUED | **first extension VERIFIED and merged** | columns above necks 36.714 -> 34.446 m3, blinding 15.179 m3 released in the candidate (hand -0.2 %); opt-in only, released default unchanged |
| P-04 | T-132 (verifier) | TODO, after READY <= 3 | checker figures 17:40: concrete WAPE V2.9 18.17 % (5 compared / 3 held), V3.0.1 15.38 % (3 / 5): the drop is only blinding moving to HELD, not an accuracy gain |
| P-05 | T-126 MERGED, wired in T-133 | DONE (verified through Gate B) | |
| P-06 | T-128, T-144 READY | waiting for the checker | |
| P-07 | T-125, T-143 READY; T-108 QUEUED | waiting for the checker | net on owner Q-73, black count on Q-75 |
| P-08 | T-136, T-138 r2, T-148 MERGED; T-141 MERGED (not wired); T-149 READY; T-152 TODO (permitted); T-160 TODO | footings, ground beams, columns DONE as verified hand pieces; beams waiting; slabs next | links / per-metre counts on Q-71 |
| P-09 | T-134 READY; rulings in ELEMENT_REGISTER.md (20:20 added 9 elements) | v0 code waiting since 13:24 | checker run A |
| (Gate B tooling) | T-156 READY | waiting, checker run A | proposal on the random-line pool goes to the owner |
| P-11 | T-147, T-150 READY; T-159 TODO (owner request, facade per side) | started ahead of week 3 | windows 56.771 vs 54.931 m2 on the 8 printed (+3.3 %); counts agree; heights on D-45 |
| (gate 1) | T-153 MERGED bfa0f71; T-157 TODO | floor area room by room VERIFIED in part (dewaneya 0.0 %); north strip split HELD | outside finishes on OQ-04 |
| (gate 3 check) | T-145 MERGED; T-139 REJECTED (text); T-119 r2 READY | slabs checked 0.0 / 0.05 / 0.0 % on 3 panels; columns HELD range at the tank | |

Day-7 target (2026-10-27): **MET on 2026-10-21 17:40** (6 days early): the checker verified the V3.0.1 integration
package through Gate B (hand checks of every safety line plus 2 random lines) and merged it. Day-14 target (2026-11-03,
measurable increase in verified coverage): on track if T-142 (footing steel, membrane evidence, soffits) and T-146 / T-151
pass Gate B; measurement needs SCOREBOARD v2 (T-132), which the checker starts once READY falls to 3.
