# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)

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

## LEAD REPORT 2026-11-12 12:20 UTC

Drive read OK (no file in the private project folders modified since 16:00 UTC 10 Nov, no photo task). Training villa: candidate of record now ARCH_TAKEOFF_V3.0.74 / master 1.75.0 (NOT RELEASED; released V2.9 + route G untouched). Development project 2 paused.
- PLASTER / PAINT (m2): package PASSED Gate B (full suite to the end, 0 fail; own chain reproduced). FIN.PLASTER held 1,106.949 .. 1,302.169 (like for like -16.76 .. -8.68 % vs his figure, his 13.50 row apart); FIN.PAINT held 604.990 .. 710.006 (like for like -31.25 .. -24.48 %, unchanged); released figures unchanged. Your paint rule of today (paint = plaster of the same faces minus the band above false ceilings and minus tiled faces) becomes a new rule version with a normal and an adverse test; the about 500 m2 plaster-paint gap must be explained in full by bands, tiles, omissions and exterior faces (gate 1, first in finishes).
- CONCRETE (m3): released 317 lines = 291.476251 unchanged. The 7 formwork lines with two disagreeing figures are settled from the drawing, one figure each (e.g. column 412 4.183916 .. 5.532116 m2; beam band 0.102019 m2 instead of 0); formwork + concrete round 10 is next in the candidate (V3.0.75).
- EXTERIOR PLASTER (m2): ready against the current candidate (3 facade hosts live; 2F gross 125.160 checked by hand); one facade width printed two ways (GF upper bound -5.000 m2 if 2.00 governs) goes on the designer list.
- WATERPROOFING (m2): roof membrane released 115.832 is 0.018026 above its own measured band (dome chord); a correction record is ready but the Checker's tool path refuses it: a small task gives the Checker that path.
- EARTHWORKS (m3): your plan x depth 183.948 against engine 136.901 .. 163.479 reconciled over 90 terms to drawn causes (annex -31.560, unprinted lobby / court levels -18.522 .. 0, beam columns +3.036 .. +11.092; residual 0.000002); every density HELD (none printed).
- Learned: any output rebuilt from candidate records must be rebuilt on the latest head just before hand-in (lesson adopted after its second occurrence).
- Team health: 18 runs since 08:16, every one closed with a final line; self-check PASS everywhere; Checker 4 Gate A + 1 Gate B passed, 1 reject in 4 h. Board: queue check 18 actionable, 0 flagged, 0 stall.
- Gates: lowest open gate 1 (formwork package, paint rule). M3 (reconciled quantities + scorecard): plaster / paint in the candidate today (done); formwork 13-14 Nov; all-trade statement redo 13 Nov; beads, tiles 15-16 Nov. Estimate 14-16 Nov stands.

OWNER PACKAGE: none today (no item meets section 2.7). Two items added to DESIGNER_QUESTIONS.md (14, 15); send it when you choose.

NEEDS FIXING (owner only): none new. PR #6 (decode) is merged, thank you: workers no longer re-encode by hand. Approved scheduled-task edits remain impossible under the repository settings (unchanged).
