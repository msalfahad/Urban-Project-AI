# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)

## LEAD REPORT 2026-11-14 00:20 UTC
Drive readable; no new files or photos since 12 Nov. Candidate of record V3.0.79 (not released); V2.9 + route G untouched. V3.0.81 (concrete / formwork / main fill) with the Checker now (one-test fix, content already verified).
- Lines with no figure (non-rebar): 691 in V3.0.79 -> 295 in V3.0.81; merged fix rows waiting to be wired: earthworks, waterproofing, fence / site, boundary split (V3.0.82), concrete points, plaster / paint, masonry (V3.0.83). Still unfilled: stair finishes, openings / ceilings / domes, roof annex, missing families.
- Concrete (m3): 114 ranged lines -> points: 405.60 + 1.20 SAFETY vs freelancer 352.4 (+15.1 %, UNRESOLVED). Beams 79.24 vs 66.09 (+19.9 %); the other elements about +40 (blinding the other way, RULE_DIFFERENCE). Two cause-split tasks.
- Masonry (m2): block 467.8 -> 981.4 (blank 91 -> 0) vs freelancer 1,260.7 (-22.2 %): RULE_DIFFERENCE (full opening deduction, Q-73) + residual UNRESOLVED; black units 2,571 -> 7,226 pcs.
- Plaster (m2, ex wet render): 1,236.8 vs 1,169.1 (+5.8 %, UNRESOLVED; he 3.6 m flat): queued with masonry.
- Fence (m2): block 95.44 vs 74.40: +24.18 printed height 2.65 vs his 2.00 ENGINE_RIGHT, +4.77 RULE_DIFFERENCE, -3.18 columns UNRESOLVED, residual 0. Boundary excavation 47.09 -> 46.32 m3 (fence 44.07 / under-building 44.37 / sea gap 3.50 m).
- Roof (m2): membrane 255.4 vs 285.0 (-10 %: annex roof about 54.9 without a line), finish 248.8 vs 285 (-12.7 %): new row.
- Exterior render / paint 1,008.6 .. 1,085.6 vs 1,469.97 (-26 .. -31 %, RULE_DIFFERENCE), unchanged.
- Decisions: compare-sheet row closed as done by your main chat (Compare sheet + 13 Nov table); new rows beams first, then other concrete, roof (worker 1), blockwork / plaster (worker 2); wiring order V3.0.81 -> .82 -> .83.
- Team: all runs since 20:20 closed with a final line except the Checker run started 23:51 (still running: merged boundary + masonry, now on V3.0.81); selfcheck PASS (codemap, t061, freeze 0); queue check 19 actionable, 0 flagged, 0 stall.
OWNER PACKAGE: none new (designer list, stair skirting form, 2F top roof and the release switch remain with you).
NEEDS FIXING: the formwork step of docs/agents/boq/fill_from_index.py (whole-member ratio on each partial line) is still unchanged since 13 Nov 14:18; fix it before any rebuild on a newer index.

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

