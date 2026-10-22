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
| M2 | 2026-10-28 | 1 | 0 silent omissions of rooms and openings on every development villa; wet vs dry correct (T-022, T-010, T-023, T-028, T-029, T-004, T-025) | on track (lead 2026-10-22 12:20): doors / windows rework READY since 05:46, ranked second in the next checker run; railings / shutters census still waits for READY <= 3 (6 now). Earlier: on track (lead 2026-10-22 08:20): outside areas by hand MERGED 554c1c4 (checker porch 10.680 m2, 0.0 %); doors / windows rework READY with the main door HELD and D-GF-06 ruled (rectangle with fallback height, arched head held on D-58); railings / shutters census still waits for READY <= 3. Earlier: on track (lead 2026-10-22 04:20): photo review MERGED (railings / shutters a missing category, census queued); outside areas by hand READY (court 119.542 interlock, porch 10.680, side walk 21.021 porcelain, yard like for like -0.37 %); doors / windows rejected for rework (main door and W16 must be HELD). Earlier: on track (lead 2026-10-22 00:20): outside finishes answered by the owner rule (court interlock, sides porcelain, steps marble), finish lines in lane A; railings and shutters found missing from every BOQ by the image review (new gate-1 census task). Earlier: on track (lead 2026-10-21 20:20): floor area room by room MERGED bfa0f71 (checker re-measured the dewaneya 0.0 %; north court strip 21.021 vs 21.348 m2, split HELD); outside areas classification and finishes still open (OQ-04, D-48). Earlier: on track, checker-bound (lead 2026-10-21 16:20): floor area room by room READY for all 41 labels, 0 silent (interior 376.86 .. 376.98 m2; wet 85.62 vs 72.01 = pantry by Q-37 A; dry like for like -0.12 %); one released-method defect found (open side passage counted inside); nothing merged since 05:05. Earlier: on track (lead 2026-10-21 04:10): membrane coverage proof MERGED 18913db (688 layouts, 0 bare surface, roll counts unchanged); stair flight counted once and stair ledger merged (c0e8443); wiring into the V3.0 candidate next (V3.0 MERGED b1a6d6d) |
| M3 | 2026-11-11 | 2 | Architectural ledger: blockwork (centreline T-027, heights T-013), plaster, paint, tiles, waterproofing, doors, windows at target WAPE with a verdict on every difference | started (lead 2026-10-22 12:20): wall-stub fix MERGED (3a229f5, checker 0.0 %); corners and parapets as physical items READY with the Sigma comparison r2 (corners one m.l line, payable half apart); plaster / paint r2 READY; block openings by physical scope first in lane A. Earlier: started (lead 2026-10-22 08:20): plaster / paint both methods r2 READY (dry walls drawing-derived 1,129.09 .. 1,155.22 vs his 1,209.39 m2), wall-stub fix READY; owner directive 08:05: block openings by physical scope (T-175), corners as m.l items (T-172), stair shaft (T-173) and black block units (T-176) in work. Earlier: started (lead 2026-10-22 04:20): facade per side, block area by hand, ceilings and the centreline V2 piece MERGED; plaster / paint both methods REJECTED (curved rooms) and doors / windows REJECTED (statuses), both in rework; Sigma reconciliation READY. Earlier: started (lead 2026-10-22 00:20): opening heights MERGED 75be4ad; facade per side READY (1,022.534 m2 vs his walls 968.237, +5.6 %, rule difference); Sigma reconciliation opened from the owner's notes; block / plaster / ceilings / doors still in the checker queue. Earlier: started (lead 2026-10-21 20:20): doors / windows by hand READY (29 windows, 5 ALU doors, counts agree with the freelancer; windows 56.771 vs 54.931 m2 on the 8 printed, +3.3 %); facade per side asked by the owner (new); ceilings, openings, block, plaster / paint hand results queued for the checker (it runs again since 15:51). Earlier: started (lead 2026-10-21 12:20): ceilings measured by hand for the first time (388.14 vs 409.58 m2, -5.2 %), window sills / heads for 9 openings, both waiting for the checker; doors / windows and floor area by hand on the board; block net on owner Q-73 / Q-75; nothing merged since 05:07 (checker outage). Earlier: started (lead 2026-10-21 08:20): block wall area by hand READY (gross 955.63 vs his 1,094.50 m2, -12.7 %; net on owner Q-73, black count Q-75); wall run V2 READY (GF -1.3 % vs hand with the pool glass line); plaster / paint both methods READY; all wait for the checker (no run since 05:07) |
| M4 | 2026-11-25 | 3 | Structural ledger: concrete census and rebar by bar population from schedules (T-009 split), formwork, excavation | started (lead 2026-10-22 12:20): pool shell measured by hand and re-measured by the checker (base 4.374 m3 VERIFIED; walls 2.828 m3 at the 1.20 structural height, rework; line PARTIALLY VERIFIED, rebar held); formwork rejected once (column joint faces +12 %), rework; per-metre footing notation READY (2,769 .. 2,830 kg held on the leg diameter); both staircases (owner priority) next. Earlier: started (lead 2026-10-22 08:20): stair / pool / tank steel and dome rings MERGED; steel package V3.0.3 MERGED through Gate B (47df193) after one fixed fault; formwork by hand READY (missing category, first figures); "per metre" notation now investigation T-171; strap axis length T-174; slab / stair steel integration T-179 queued after V3.0.4. Earlier: started (lead 2026-10-22 04:20): footing steel MERGED through Gate B in the candidate (V3.0.2); slab steel MERGED; column / ground-beam / beam steel in the V3.0.3 Gate B package; stair / pool / tank steel READY; formwork, pool concrete and the excavation level chain on the board. Earlier: started (lead 2026-10-22 00:20): columns to the controlling member and beam steel (5,171 kg net) MERGED; footing steel in the V3.0.2 package (Gate B pending); slab steel READY (bottom 2,853 .. 3,068 kg on Q-71); stair / pool / tank steel and formwork queued. Earlier: started (lead 2026-10-21 20:20): column steel and ground-beam span splitter MERGED (8a22eec, 6ab7719); V3.0.1 columns 36.714 -> 34.446 m3 and blinding 15.179 m3 VERIFIED through Gate B (967d6d5, opt-in); beam steel by hand READY (5,171 kg net); slab steel next. Earlier: started (lead 2026-10-21 12:20): column steel by hand READY (1.887 t net + 1.552 t held), slab leftovers READY (beams 65.060 vs 65.97 m3); beam and slab steel by hand on the board; nothing merged since 05:07 (checker outage). Earlier: started (lead 2026-10-21 08:20): columns to the controlling member by hand READY (28.816 .. 28.979 vs 28.547 m3), ground-beam span splitter READY (-43.96 kg), slabs by hand READY; footing and ground-beam steel MERGED; column steel next (T-148); straps on owner Q-74 |
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
