# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)

## LEAD REPORT 2026-11-13 00:13 UTC

Drive read OK (no file in the private project folders modified since 12:00 UTC 12 Nov, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.76 / master 1.77.0 (NOT RELEASED; released V2.9 + route G untouched). 3 pieces merged since 20:14, each with the Checker's own re-measure on the drawings.
- WATERPROOFING (m2): roof membrane correction now applied in the candidate: 115.832 released -> HELD 115.656 .. 115.814 (Checker re-measured the dome circles r 2.211 and the roof outline 146.375 AGREE); released roof WP 209.019 -> 93.187. No freelancer verdict moves.
- PLASTER BEADS (m.l): new family in the candidate, 14 lines all HELD: 165.45 .. 165.65 bounded + at least 128.63 where an arris is not drawn (never closed, never 0); vs freelancer +9.8 % like for like unchanged. Ceiling: one duplicated face excluded (0 m2 moves; released ceiling 411.337 unchanged).
- EXTERIOR PAINT EDGES (lm, research): corners 168.50 .. 182.05 -> 178.14 .. 179.34; window edges 103.68 (arched heads along their curve; 106.02 was rectangles, -2.34 ENGINE_RIGHT); entrance stone surround is not on the painted face (paint deduction 0). Door edges 0 .. 12.20 and 1F slab edge still HELD -> new task. Not yet wired.
- DRAINAGE (lm, research): plan runs HELD (sheets print 'not to scale'); risers 32.40 MEASURED + 13.50 .. 15.60 BOUNDED.
- Learned (section 7 ADOPTED): an opening edge is walked along its drawn outline, never its bounding box; a hub version reads the Checker record file before building its index, and a line with a blank part is AT_LEAST; a sheet that disclaims its scale yields no MEASURED length; a symbol is classified by content, not its block name.
- Missing: paint by the owner rule not in the candidate yet (next package, now TODO); tiles, exterior plaster, WP after it. Idle slots: special-metalwork and joinery censuses (nothing priced, nothing released).
- Team health: 12 runs since 20:14, all closed with a final line; self-check PASS everywhere incl. this run. Three idle worker runs (21:00-23:20) because every next row waited on a READY task; fixed by releasing T-749 / T-752 and two new lane A rows. Queue check 16 actionable, 0 flagged, 0 stall.
- Gates: lowest open gate 1 (paint wiring, exterior edge residuals). M3 estimate 14-17 Nov (beads + ceiling landed a day early).

OWNER PACKAGE: none today (no item meets section 2.7).

NEEDS FIXING (owner only): none new. Approved scheduled-task edits remain impossible under the repository settings (unchanged).

## LEAD REPORT 2026-11-12 20:14 UTC

Drive read OK (no file in the private project folders modified since 12:00 UTC today, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.75 / master 1.76.0 (NOT RELEASED; released V2.9 + route G untouched). 7 MERGED since 16:20 (formwork + concrete package, sanitary census, label fix, opening edges, readiness, exterior paint); 1 rejected.
- FORMWORK (m2): in the candidate: released 1,027.977 -> 1,061.104 (+33.127, +3.2 %); 32 lines bounded 107.201 .. 132.786; no freelancer formwork row (not comparable). Concrete released 291.476 m3 unchanged.
- WATERPROOFING (m2): the Checker found the new candidate still shows the roof membrane 115.832 as released; the correction record exists (band 115.656 .. 115.814). The next candidate package carries it; the full waterproofing package is now written as its own task.
- PAINT (m2, research, not wired): interior by your rule 821.011 .. 905.055 (window / door edges moved to metres); exterior = render of the same faces 1,006.633 .. 1,085.613 vs freelancer 1,469.97 (-31.5 .. -26.2 %, rule difference: his figure is not explained by faces); exterior edges in lm still bounded (corners 168.5 .. 182.05, windows 103.683 vs 106.020): a closure task is set.
- DRAINAGE (lm): the sanitary sheets say 'not to scale' and an earlier ruling forbids scaled pipe lengths, so plan runs stay HELD (designer list item 16); risers from printed levels are kept. Learned: a sheet that disclaims its scale gives no measured length.
- Missing families: the measurable ones are all drafted; next idle slot is the special-metalwork census (canopies, pergolas, gates).
- Team health: 13 runs since 16:20, all closed with a final line; self-check PASS everywhere incl. this run; one idle Worker 1 run (queue too thin; fixed). Checker wrote two verdict times later than its own run end: told to correct. Queue check 17 actionable, 0 flagged, 0 stall.
- Gates: lowest open gate 1 (beads + ceiling package, exterior edges). M3 (reconciled quantities + scorecard) estimate 14-16 Nov stands; hub chain beads -> paint -> tiles -> exterior plaster -> waterproofing -> disposal.

OWNER PACKAGE: none today (no item meets section 2.7).

NEEDS FIXING (owner only): none new. Approved scheduled-task edits remain impossible under the repository settings (unchanged).

## LEAD REPORT 2026-11-12 16:20 UTC

Drive read OK (no file in the private project folders modified since 12:00 UTC today, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.74 (NOT RELEASED; released V2.9 + route G untouched). 4 MERGED since 12:20 (T-741, T-740, T-739 r2, T-742; ancestors of 1370c295 checked); READY 2 (T-729 Gate B in the running Checker run, T-743).
- PAINT (m2): your rule as UP-FIN-PAINT-002 (rulebook 1.2.0, normal + adverse test): engine 822.198 .. 927.215 -> rule 841.261 .. 929.205 (+2.32 / +0.21 %); plaster-paint gap 673.335 / 763.539 allocated 100 % to bands, tiled faces and named causes (returns -20.25, 1F-11 W17 ENGINE_WRONG +0.861 / -4.305, GF-01 W11/W12, beam ends 0.315), residual 0. Checker 3 faces AGREE. Not wired. Opening edges ruled lm by your rule (no question) -> T-746; exterior paint -> T-747; wiring T-749.
- WATERPROOFING (m2): roof membrane L-636fd3ff 115.832 RELEASED -> HELD by Checker record DG-a429c160 (+0.018026 above its band 115.656474 .. 115.813974, dome chord). First downgrade-only record issued by the new path (T-741).
- FORMWORK / CONCRETE: T-729 package READY: STR.FORMWORK released 1,027.977 -> 1,061.104 m2 (54 verified fix rows), 32 bounded 107.201 .. 132.786, 40 at least >= 122.485; MS1-L 1.213428 m3; L4 24,051 pass 0 fail by the worker; Checker Gate B running.
- ALL TRADES: statement on V3.0.74 MERGED: 5,155 lines, 2,797 HELD each with a pinned cause, B4 m2 released 1,353.36 + bounded 1,711.94 .. 2,012.18 + 27 blank; never summed across states. Restated on V3.0.75 in T-748.
- MASONRY: parapet blocks 25 runs by handle, 4 lines HELD 0 .. 101.464 m2 (material Q-65 C / D-39); freelancer 172.93 m2 has an unresolved material, datum ENGINE_RIGHT.
- MEP (census only): WC 12, basin 17, trays 3 + walk-in 3, FD 19; sink / washing point HELD; 9 phantom fixtures from room-name tag blocks -> T-744 fix; lesson L-T743-1 PROPOSED; F-T730-1/-2 ADOPTED.
- Team health: 13 runs since 12:20, all closed (one Verifier INCOMPLETE by the overlap guard, correct); self-check PASS everywhere incl. this run; 0 rejects. Queue check 20 actionable, 0 flagged, 0 stall.
- Gates: lowest open gate 1 (T-729, T-746, T-744). M3 estimate 14-16 Nov stands.

OWNER PACKAGE: none today (no item meets section 2.7).

NEEDS FIXING (owner only): none new. Approved scheduled-task edits remain impossible under the repository settings (unchanged).
