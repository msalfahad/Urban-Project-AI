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
| M2 | 2026-10-28 | 1 | 0 silent omissions of rooms and openings on every development villa; wet vs dry correct (T-022, T-010, T-023, T-028, T-029, T-004, T-025) | on track (lead 2026-10-25 16:15): no floor or opening line moved (candidate of record still V3.0.17; stairs V3.0.18 in work); ceiling and skirting ledgers MERGED both name the 1F dressing omission (ceiling 2.970 m2, skirting) for T-284 / T-246; no other new silent omission. (lead 2026-10-25 14:15): candidate of record V3.0.17 (Gate B 13:35); floor / opening lines byte-identical to V3.0.16; ceiling face-to-line ledger READY found one 1F dressing ceiling 2.970 m2 with no line (an omission, now named for T-284); no other new silent omission. (lead 2026-10-25 12:15): no flooron track (lead 2026-10-25 12:15): no floor or opening line moved; candidate of record V3.0.16 with Checker records issued (0 whole lines countable in the export until T-298 fixes the completeness join); no new silent omission. (lead 2026-10-25 10:22): V3.0.16 MERGED ef3305f1 (first real export, one identity on 3,699 lines). (lead 2026-10-25 10:15): pantry zone 1.100 m2 WET MERGED e861e390 (carried by the stairs package T-266); V3.0.16 r2 in Gate B; no new silent omission of rooms or openings. (lead 2026-10-25 08:15): V3.0.16 Gate B REJECTED narrow 07:58 on stale maps only (every other check passed on the real candidate); r2 first for worker 3 08:59; pantry zone 1.100 m2 settled WET from the drawing (T-286 READY); no new silent omission found. (lead 2026-10-25 06:15): the one-identity candidate V3.0.16 (first real export, 3,699 rows, every quantity byte-identical to V3.0.15) handed in for Gate B 06:13; no new silent omission found. (lead 2026-10-25 04:15): candidate of record now V3.0.15 (floor lines unchanged from V3.0.14); no new silent omission found this cycle. (lead 2026-10-25 02:15): floor area V3.0.14 in the candidate (internal 380.364 vs released 385.634 m2, -1.37 %); scoring key T001C MERGED 6366b754 (scores 380.364, -7.13 % vs freelancer 409.58); windows line: only D-53 (W02) left after Q-76 A; 1F landing marble material line missing (T-266 acceptance); no new silent omission of rooms or openings |
| M3 | 2026-11-11 | 2 | Architectural ledger: blockwork (centreline T-027, heights T-013), plaster, paint, tiles, waterproofing, doors, windows at target WAPE with a verdict on every difference | started (lead 2026-10-25 16:15): whole verified lines in the export still 1 (CONC.SLAB); plaster / paint r2 MERGED a9754a67 (1F-11 HELD 60.6011 .. 62.3352 m2, W17 developed hole = new T-302), ceiling MERGED 964c5ebe, skirting MERGED 57c31ae4 (+5.802 lm sill-window thresholds ENGINE_WRONG, wet pantry NOT_APPLICABLE, for T-246); WP whole line waits on T-301 (worker 2 next). (lead 2026-10-25 14:15): first WHOLE verified line in the real export (CONC.SLAB 60.280155 m3, completeness 62 = 62, T-298 MERGED 274885e6); plaster / paint ledger REJECTED narrow (module name clash + W17 under Q-76 A), r2 in work; ceiling face-to-line READY (79 faces, 36 lines, engine 403.163 vs decor 362.006 m2 every m2 named); WP whole line waits on T-301. (lead 2026-10-25 12:15): blockwork wall-to-linestarted (lead 2026-10-25 12:15): blockwork wall-to-line ledger MERGED 0c6b2ba5 (422.5314 m2 determinate ready for T-279); plaster / paint face-to-line ledger READY (703.30 .. 768.81 m2 range; one released room line becomes HELD on W17); waterproofing scope inventory added (T-301) so a WP line can count whole. (lead 2026-10-25 10:15): blockwork wall-to-line ledger READY: the candidate's 21 masonry lines are BLOCKED blank, 422.5314 m2 determinate ready to replace them after Gate A (T-291 -> T-279); ceiling (T-295) and skirting (T-296) ledgers added. (lead 2026-10-25 08:15): integration-dependency ledgers for blockwork (T-291) and plaster / paint (T-292) on the board so T-279 / T-244 are mechanical packages; no quantity moved. (lead 2026-10-25 06:15): ceilings r3 (decor 361.229 m2), stair soffits V1 and blockwork register v4 (449.6007 - 7.9131 d m2) MERGED as research ledgers; buried ground-beam WP 45.4682 m2 now a VERIFIED COMPONENT (32 / 32 faces own), its line still PARTIALLY VERIFIED; integration of ceilings and blockwork waits only on the lane I chain. (lead 2026-10-25 04:15): WATERPROOFING.FOUNDATION family MERGED into candidate V3.0.15 (04d34378, Gate B PASS: 7 VERIFIED lines, buried liquid 45.4682 m2 PARTIALLY VERIFIED 9 / 32 faces, 11 HELD BLANK); ceilings r3 READY (decor 361.229 m2), stair soffits measured (T-281, waiting for a READY slot); register v4 in work (T-288). (lead 2026-10-25 02:15): blockwork register v3 MERGED (established 449.5934 m2, overstated by 7.913 d m2 HELD on D-41 under sunken panels -> register v4 T-288 before T-279), Checker VERIFIED 297.847 m2 on 18 walls; waterproofing foundation family V3.0.15 r2 in work (T-270), buried faces 45.468 m2 DC; ceilings r3 in work (T-283 -> T-284); plaster blockers T-286 |
| M4 | 2026-11-25 | 3 | Structural ledger: concrete census and rebar by bar population from schedules (T-009 split), formwork, excavation | started (lead 2026-10-25 16:15): ring GB end rule closed from the drawing (1.7349 -> 1.746943 m3, carried by T-255); rebar basis ledger MERGED 5408da97 (8.311 t DRAWING_CONFIRMED, 1.939 t CONVENTION) with r2 narrow on 4 2F lines 0.159 t (D-39); footing PART F READY (first in queue); stairs V3.0.18 CLAIMED. (lead 2026-10-25 14:15): exterior GB basis correction INTEGRATED (V3.0.17, Gate B PASS 7c49e890: main-house exterior 8.1642 -> 15.9575 m3 DRAWING-CONFIRMED; columns 33.606 -> 28.2155 m3 with 2F / annex HELD); formwork part 1 MERGED 294da634 (part 2 TODO); rebar: tonnes in the export, read-only reconciliation r1 MERGED 05ad6d02 (0 double counts), footing PART F next, completeness safeguard after T-297. (lead 2026-10-25 12:15): stairs / domes basis MERGEDstarted (lead 2026-10-25 12:15): stairs / domes basis MERGED 891dbd4d; excavation ledger MERGED 2991be3d (all volumes HELD); formwork face-to-member part 1 READY (414 faces, residual 0.000 m2; boundary G.B 35.256 m2 untied, no concrete line); rebar Stage B: tonne export (T-298), read-only reconciliation (T-299) first, completeness safeguard (T-300) after. (lead 2026-10-25 10:15): structural basis ledger MERGED 455c93c4 (main-house exterior GB 15.9600 m3 DRAWING-CONFIRMED vs engine 8.1642, Checker own re-derive); stairs / domes basis ledger READY (7.585779 vs released 8.064447 m3, drums omission); rebar line-to-member ledger added (T-297). (lead 2026-10-25 08:15): CB5 columns VERIFIED 1.430 m3 (component, MERGED 542b64c7); column-core rebar LOWER bounds MERGED 86fdc315 (734.779 kg on 26, 10 HELD); structural basis ledger READY (main-house exterior GB 8.1642 -> 15.9600 m3 drawn, +95.5 %); excavation ledger complete, all volumes HELD (T-170); formwork face-to-member ledger (T-293) and stairs / domes basis ledger (T-290) on the board. (lead 2026-10-25 06:15): formwork end faces r3 MERGED; column-core rebar restated on the printed level chain READY (26 cores 801.321 -> 734.781 kg as a lower bound, 10 HELD); excavation ledger promoted (depth HELD, Q-21 C). (lead 2026-10-25 04:15): formwork end faces r3 READY (1AA and lift-pit ring ends withdrawn); stair soffit forms to be checked against the T-281 polygons. (lead 2026-10-25 02:15): beam width census MERGED (7 / 137 CONFLICT = D-02 + D-27, both readings); links and laps + t MERGED, all HELD; formwork end faces r3 narrow (T-282, one row); D-41 now holds CONC.BEAM tops of 2 shared beams 3.006 .. 3.036 x d m3 (slab unaffected); designer RFI gaps (T-287); core datum (T-280); excavation QUEUED behind the formation answer (T-170) |
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
