# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)

## LEAD REPORT 2026-11-13 20:20 UTC
Drive readable; no new files or photos since 12 Nov. Candidate of record V3.0.79 (exterior render + paint, master 1.80.0; not released); V2.9 + route G untouched. Package V3.0.81 with the Checker now.
- Lines with no figure (non-rebar): 691 in V3.0.79 -> 295 in V3.0.81 (READY); the merged fix rows for earthworks (18), waterproofing (50) and fence / site (37) go in the next round.
- Concrete (m3): blank 80 -> 0 (+58.42 + 1.00 SAFETY). Beams 78.2 .. 80.6 vs freelancer 66.09 (+18 %, UNRESOLVED): new beam-by-beam task.
- Formwork (m2): 1,098.0 -> 2,226.9 ESTIMATE/DEFAULT; main-fill double count CONFIRMED by the Checker on one beam (38.5 m2 against a physical 12.5 .. 15.4), so the face set is wired instead. No freelancer line.
- Exterior render / paint (m2): 1,008.6 .. 1,085.6 each, in the candidate; vs freelancer 1,469.97 = -26 .. -31 % RULE_DIFFERENCE.
- Roof finish 248.8 vs 285 m2 (-12.7 %, open). WP wet floor 85.58 vs 72.01 m2: pantry 13.46 RULE_DIFFERENCE, rest +0.15 %.
- Earthworks (m3): excavation 336.5, backfill 327.5, disposal 9.0 (replaces the main-fill 105.6 .. 115.5 that left out zone 2); no freelancer line.
- Fence (m2): block 95.44 vs 74.40 (+28.3 %), plaster 95.66 vs 107.24 (-10.8 %): cause queued in the boundary task.
- Found: boundary excavation dug at 0.40 m everywhere, but structural sheet 14 section A-A draws the fence-run base 0.90 m wide (up to +58.9 m3 if every metre were a fence run). New task splits the boundary into under-building (your Q-28 A band) and fence runs before any change; owner question only if two sheets contradict on one run.
- Plaster / paint fill r1 rejected: wet-room ceiling default 2.70 replaced and default door widths where widths are drawn; r2 queued first for worker 2. Plaster 1,212.2 vs 1,169.1 m2 (+3.7 %) pending that.
- Decisions: T-750's held waterproofing stage superseded by the merged fix rows (folded into the next wiring round); concrete-range task restated on your 0.05 m3 rule, no new rule file.
- Team: every run since 16:31 closed with a final line; selfcheck PASS (codemap, t061, freeze 0); queue check 20 actionable, 0 flagged, 0 stall.
OWNER PACKAGE: none new (designer list, stair skirting form, 2F top roof and the release switch remain with you).
NEEDS FIXING: the formwork step of docs/agents/boq/fill_from_index.py applies a whole member's ratio to each partial line (Checker confirmed); fix it before the next rebuild on a newer index (told 16:4x, still open).

## LEAD REPORT 2026-11-13 16:40 UTC
Drive readable; no new files or photos since 12 Nov. Candidate V3.0.78 (not released); default V2.9 + route G untouched.
- Concrete (m3): blank 80 -> 0 in the merged fix-row set (+58.42 m3 DEFAULT/ESTIMATE + 1.00 m3 SAFETY), not yet wired; beam 78.2 .. 80.6 vs freelancer 66.09 (+18 %, UNRESOLVED: same-mark / 0.60 defaults).
- Formwork (m2): blank 336 -> 0 handed in (1,098.0 -> 2,226.9 m2 ESTIMATE/DEFAULT); no freelancer line to compare.
- Exterior render + paint (m2): 1,008.6 .. 1,085.6 each, verified; vs freelancer 1,469.97 = -26 .. -31 % RULE_DIFFERENCE (face-by-face vs run x height); merge blocked only by the coverage-registry step.
- Main fill (owner set, 207 lines): blank non-rebar lines 692 -> 551 on its branch; roof finish 248.8 vs freelancer 285 m2 (-12.7 %); dry-room plaster 866.1 m2 DEFAULT, paint 675.8 m2; disposal 105.6 .. 115.5 m3 held.
- Worse / found: worker 1 reports the main-fill formwork rows apply a whole host's ratio to each partial line: 472.8 m2 vs 240.6 m2 on the same 126 lines (about +232 m2). Sent to the Checker to settle by hand before wiring.
- Decisions: hub order exterior render (registry fix, worker 2) -> main fill round 2 (worker 3, formwork per the Checker ruling) -> waterproofing -> roof/earthworks. Plaster task trimmed to lines the main fill does not cover.
- Team: all agents ran and closed their runs since 12:30; selfcheck PASS (codemap, t061, freeze 0); queue check 24 actionable, 0 flagged.
OWNER PACKAGE: none new (designer list, stair skirting form, 2F top roof and the release switch remain with you).
NEEDS FIXING: if the Checker confirms the formwork double count, the formwork step of docs/agents/boq/fill_from_index.py needs your fix before any rebuild on a newer index.

## LEAD REPORT 2026-11-13 12:30 UTC

Drive read OK (no file created or modified in the private project folders since 12:00 UTC 12 Nov, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.77 / master 1.78.0 unchanged (NOT RELEASED; released V2.9 + route G untouched). Your delivery reset of 12:00 is applied on the board.
- EXTERIOR RENDER / PAINT (m2, your gap no. 1, 0 in the candidate today): face ledger merged 10:00 (research, 2 of 126 faces re-measured by hand by the Checker): render = paint face by face 1,009.11 .. 1,087.62 m2, 6 first-floor slab-edge faces held; corners 176.94 .. 178.14 lm. Freelancer 1,469.97 m2 (-31 .. -26 %) stays a rule difference. It goes into the candidate in the next package (Worker 2, started now).
- TILES + STAIR FINISHES (m2 / lm): tooling fix handed in 09:46; quantities already agreed by the Checker (stair-core wall tile 18.44 .. 44.77 m2, risers 13.09 .. 13.74 m2); waiting 2.7 h for the Checker (see team health).
- CONCRETE (m3): released 291.48 unchanged. Your 0.1 m3 rule applies to 72 of the 194 held lines (range narrower than 0.1 m3): about +19.69 m3 would be released at their measured low bounds, 3.83 m3 of ignored ranges logged, safety allowance max(1.0, 3.83) = 3.83 m3. New task for Worker 1; not in the candidate yet. The other 122 held lines still wait for designer dimensions.
- ROOF LAYERS: insulation and protection are printed nowhere; screed at least 10.63 m3. They need your company default values (approved in principle 13 Nov); no agent invents one.
- Designer list correction handed in (38 lines re-filed to their live cause; no quantity moves); you send the list, the agents do not.
- Waiting to go in: waterproofing (Worker 3, built in parallel now), earthworks after it. Rebar parked.
- Team health: the Checker's 09:52 run merged the face ledger but wrote no final line (INCOMPLETE), and Worker 1's 09:19 run also has no final line (its work was taken up at 11:21); W2 10:40 and W3 11:00 were idle because the shared candidate takes one package at a time. Fix: two packages are now built side by side on the tiles package, with reserved version numbers, still checked one at a time. Self-check PASS 3/3.

OWNER PACKAGE: none (no item meets section 2.7). Pending from you already, no new question: the company default values (roof insulation / protection first).

NEEDS FIXING (owner only): none new. Approved scheduled-task edits remain impossible under the repository settings (unchanged).
