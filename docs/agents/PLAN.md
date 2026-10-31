# Plan: an engine that is right on any Kuwait villa (owner, 2026-10-18)

Every scheduled agent reads this file after MISSION.md and TEAM.md. MISSION.md says WHAT (gates, scoring, who is
right); this file says HOW FAST and WHO DOES WHAT EACH DAY. The owner can change any target in a session or in
OWNER_QUESTIONS.md.

## The goal

**The product is the engine, not a project.** Alsenan is one development sample. Success means: give the engine the
drawings of a villa it has never seen and get a correct, evidenced, unpriced BOQ for concrete, rebar, blockwork,
plaster, paint, floor areas, wet vs dry areas, waterproofing, tiles, doors and windows.

Engine targets (per villa, per trade and unit; MISSION.md scoring):

| Measure | Target |
|---|---|
| Silent omissions (room, opening, element with no engine line) | 0 |
| WAPE, finishes and blockwork | <= 3 % (95 % floor = 5 %) |
| WAPE, concrete | <= 2 % |
| WAPE, rebar (counted from schedules, never kg/m3) | <= 3 % |
| WAPE, waterproofing | <= 3 %, no wet room missed |
| Doors, windows | exact counts |
| Floor area | <= 1-2 %, no room lost |
| Differences against the engine (FREELANCER_RIGHT + UNRESOLVED) | trending to 0; ENGINE_RIGHT needs a hand calculation |

A trade counts as **done** only when it meets its target on **every villa in the development set** (at least 3 real
villas + the T-019 synthetic villas), not on Alsenan alone. A change that helps one villa and hurts another is a
regression.

## Development set (the engine is judged on all of it)

1. Alsenan (structural + architectural + freelancer BOQ per trade): Drive "Urban BOQ private data" / "Alsenan chalet
   project".
1b. Development project 2 (owner, 2026-10-18): a finishing-only apartment in its own subfolder of "Urban BOQ private
   data" (the lead finds it by listing that folder; never write its client name in this repo). Architectural plan as a
   DWG (owner, Q-10; file name ends in -STR.dwg: confirm by a read-only CAD audit that it holds the floor plans) and as
   a 2-page vector PDF whose text is drawn as outlines (no text layer, no raster image; lead checked 2026-10-18: Claude reads it visually, rooms, Arabic / English labels and printed mm dimensions are legible; the title block names a different source DWG than the uploaded -STR.dwg, so the CAD audit must confirm which file holds the plans), plus a manual QS takeoff for finishes (tiles, plaster, paint,
   decor and waterproofing, finishing invoice). No concrete or rebar. Use: reference for finishes trades
   (tiles, plaster, paint, floor area, wet vs dry, doors, windows) measured from the DWG; the PDF is a second, independent check through the plan reader (T-003, gate 4). Score it only on
   the trades it covers.
2. T-019 synthetic villas (hand truth, other layer names, units, rotation, mirror, Arabic / English).
3. Two or more further real villas (owner, 2026-10-18: plans only, no freelancer BOQ and no structural drawings). Each
   becomes its own subfolder of "Urban BOQ private data". They have no reference BOQ, so they are scored differently:
   - silent omissions and counts: every room, wet room, door and window the plan reader and a hand check find on the
     drawing must appear in the engine output (measured, held or unsupported); this is fully measurable;
   - quantities: the verifier hand-calculates a sample (at least 3 rooms and 3 walls per villa, from printed dimensions)
     and scores the engine against it; never against the engine's own output;
   - no regression: a change may not make any villa worse.
   Until they arrive, every fix must pass a synthetic fixture that is not Alsenan.

## Milestones (targets, not promises; the lead re-dates them when evidence says so)

| # | By | Gate | Exit (measured, not claimed) | Status (lead 2026-10-19 12:20) |
|---|---|---|---|---|
| M1 | 2026-10-21 | 0 | Scoreboard measured on Alsenan from real files (T-001b); capability matrix merged; synthetic villas merged (T-019) | done (lead 2026-10-19 12:20): scoreboard measured on Alsenan (b5475db, re-measured 8774071), capability matrix 5be347d, synthetic villas merged 8094fcd (T-019). Development project 2 deferred by the owner (Alsenan first, 11:21); its conversion-loss cause found and its DXF acceptance check written (T-066 READY) |
| M2 | 2026-10-28 | 1 | 0 silent omissions of rooms and openings on every development villa; wet vs dry correct (T-022, T-010, T-023, T-028, T-029, T-004, T-025) | MET on rooms and openings for P7757 on this ledger, 1 day late (lead 2026-10-29 16:30): the checker's own census (14:40) accounts for all 41 room labels: 28 measured, 1 held, 1 unsupported, 11 bound to a line, not applicable with drawing evidence, or missing with their scope named; 0 silent omissions; the one wet-room misreading (the pool label read as a bathroom) is corrected. Open, not omission: the census tool itself still flags the 11 (tool upgrade queued) and the outdoor court and pool deck floors must be added as lines (queued). Development project 2 paused, not assessed. Earlier: LATE, NOT MET on rooms (lead 2026-10-29 12:30): the checker's census statement (10:00) finds 0 silent opening omissions (met on openings) but 8 room labels no candidate line cites (a ground-floor bathroom label first, then pool, four garden, a void and a roof label), named, never 0; new census-binding task first in lane A decides each label (line, not applicable with drawing evidence, or missing). Earlier (08:20): exit = the checker's census statement, not yet written in his 05:50 / 07:50 runs. Earlier (04:15): the opening reveal ledger r2 merged at 01:29 (20 door reveals bound to plaster, missing scope 13.637 m2 named, no silent omission); exit now = the checker's one-paragraph census statement on the development villa, asked in his queue for the next light run. Earlier (00:15): exit pieces checked: the plaster / paint opening outlines (V3.0.20, Gate B PASS 21:19) and the wall-tile face ledger (MERGED 8943b5ed) cleared the checker after the outage; the opening reveal ledger (every opening x side once) is in rework r2 READY after the checker found 22 door reveals already carried by plaster (no silent omission, a would-be double count); exit = the checker's census statement on the development villa once the reveal ledger passes (earliest next Checker run 00:49); development project 2 stays paused by the owner. Earlier (28 Oct 20:20): not confirmed on its date (outage 60.5 h) |
| M3 | 2026-11-11 | 2 | Architectural ledger: blockwork (centreline T-027, heights T-013), plaster, paint, tiles, waterproofing, doors, windows at target WAPE with a verdict on every difference | started (lead 2026-10-31 12:30): candidate V3.0.31 adds the roof build-up (roof finish 202.220 m2 MEASURED, screed HELD, insulation / protection UNKNOWN blank); face-length residuals traced to walk tolerance (0.000 m2, READY); ceilings next in lane I; boundary fence blockwork opened as a missing category |
| M4 | 2026-11-25 | 3 | Structural ledger: concrete census and rebar by bar population from schedules (T-009 split), formwork, excavation | started (lead 2026-10-31 12:30): concrete reconciliation r2 merged (traced +0.252 / HELD -77.593 / unexplained -37.124 m3); ground slab + ground beams measured (READY: 22.664 m3 unresolved -> traced -4.844 / HELD -13.251 / unexplained -4.569); columns, beams, stairs / domes reconciliations opened; at risk for 25 Nov but improving |
| M5 | 2026-12-09 | 4 | Intake matrix: vector PDF, DWF, scanned PDF and images through the plan reader (T-003), nothing fabricated | started (lead 2026-10-20 00:30): scanned-dimension reader with an exact chain-sum check on the board (from scout answer R-01); Arabic notes on scans asked of the scout (R-06) |
| -  | owner | 5-7 | Blind benchmark, pilot, product: owner only | owner |

## Daily targets per agent

| Agent (cadence) | Daily target | Quality bar |
|---|---|---|
| **Workers 1-3** (each hourly, staggered :19 / :39 / :59; up to 72 runs) | >= 20 tasks to READY per day together; never idle while a TODO exists | each task: general rule (no project constant), non-Alsenan hand fixture, tests at `impact` level, freeze check 0; rework rate <= 1 in 4 |
| **Verifier** (hourly at :49, 24 runs) | no READY task waits more than 2 h; scoreboard re-measured after every merge and at least once a day, **per villa** | a who-is-right verdict for every new engine-vs-reference difference; rejects any logic that only holds for Alsenan; no trade gets worse on any villa |
| **Lead** (every 2 h, 12 runs) | board always at 8-12 TODO (max 2 Track B, no two sharing an engine file); >= 15 new tasks a day drawn from the largest scoreboard gaps (money at risk first); milestone table kept current | every task small (one run), names gate, gap, modules, acceptance; owner questions <= 5, each one sentence with options |
| **Research scout** (daily) | <= 5 entries, at least 1 aimed at the current biggest scoreboard gap | licence and security checked; ideas only, nothing installed |

Weekly (lead, Sunday run): one line per milestone in BOARD.md: on track / late (why) / done (commit); tasks merged this
week; scoreboard trend per trade and villa.

## Roles (no overlap)

- **Owner**: decisions only an owner can make (measurement basis, scope, missing drawings, UNRESOLVED verdicts,
  gates 5-7). Answers in OWNER_QUESTIONS.md or the hub chat.
- **Lead**: chooses what is worked on and in what order, keeps the board, the milestones and the questions; never code.
- **Worker**: builds one task per run on its own branch; never merges, never grades itself.
- **Verifier**: the only one who merges and the only one who writes the scoreboard; judges who is right.
- **Research scout**: finds techniques and tools for the current biggest gap; never runs downloaded code.

## How the next tasks are chosen (lead)

1. A merge that broke a gate (fix first).
2. Lowest open gate.
3. Inside a gate, money at risk: rebar, concrete, waterproofing, aluminium / windows, blockwork, then finishes.
4. Generality: a gap seen on two villas beats a gap seen on one.
5. Track B (product agents) gets at most one TODO slot.

## Owner decisions so far (2026-10-18)

Q-09 measured + waste + total columns on every line (T-032); Q-06 basin-only hand-wash spaces are wet (T-030);
Q-07 facade height slab top to slab top (T-031). Full list: OWNER_QUESTIONS.md "Answered".

## Owner questions

Only what no drawing, rule or evidence settles; at most 5 open; every new one also goes to the owner in the run's final
message and push notification (lead) or through the hub chat.
How to write them (owner, 2026-10-18): plain words, the real example from the drawing (file, floor, room, numbers) and how the owner checks it by hand; format and example in OWNER_QUESTIONS.md "How to write a question for the owner". The hub report and every notification use the same plain wording.
