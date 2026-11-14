# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)

## LEAD REPORT 2026-11-14 08:15 UTC
Drive readable; no new files or photos (newest project file 21 Oct). Candidate of record V3.0.83 (not released); V2.9 + route G untouched. V3.0.84 with the Checker.
- Lines with no figure (non-rebar): 211 (V3.0.82, merged) -> 124 (V3.0.83, merged) -> 56 in V3.0.84 (READY). The last FILL round V3.0.85 wires exterior render / paint (81 lines merged 13 Nov but never wired: found by worker 3 at r7), roof layers, wet-room WP; parapet masonry (HELD 0 .. 101.46 m2) and dome extrados (about 83.2 m2, no line) have rows.
- Concrete (m3): 406.79 vs 352.44 (+15.4 %), all named except UNRESOLVED +7.14 beams / -5.84 other: new row (worker 1) to find each piece on the drawings.
- Masonry (m2): 981.35 vs 1,260.69 (-22.2 %) = his parapets 172.93 + boundary 74.40 in masonry (RULE_DIFFERENCE / ours HELD), our below-ground 18.39 ENGINE_RIGHT, his 1F projections 41.25 UNRESOLVED; storey walls -0.94 %. Checker re-read his workbook row by row: AGREE.
- Plaster (m2): dry + shafts 1,017.65 vs 1,169.13 (-12.96 %): his flat height -150.0 and part deductions +152.3 RULE_DIFFERENCE, lengths +55.8 ENGINE_RIGHT, shaft rows 54.0 UNRESOLVED.
- Roof (m2): finish 238.48 / membrane 244.03 vs 285 = dome footprints 45.99 RULE_DIFFERENCE + pool court -5.55 ENGINE_RIGHT + 0.52 residual (0.18 %); Checker DXF re-measure AGREE.
- Wet-room WP: floor 85.58 vs 72.01 m2 (+18.84 %) = pantry 13.455 (Q-37 rule) + 0.31 ENGINE_RIGHT; upturn now in his unit 135.57 vs 144.61 lm (-6.25 %, doorways on their own lines). Checker re-measured three rooms: AGREE.
- Ceilings / windows (V3.0.84): gypsum 426.82 vs 409.58 m2 (+4.2 %); windows 90.18 + one ranged vs 116.9 m2 (-14 %, ENGINE_RIGHT). Cornice 302.9 vs 427.5 lm (-29.1 %) UNRESOLVED: new row.
- GENERALISE: one command runs the Drive drawings to the workbook in about 65 s; 21.6 % of non-rebar lines reached straight from geometry (reach, not correctness); backlog 118 item rows, formwork largest.
- Decisions: r8 content fixed (T-760 + T-771 spatter + T-780 + T-785, own Drive chain required); new rows T-786 concrete residuals, T-787 dome extrados, T-788 cornice, T-789 parapet / projections; folded rows T-750, T-509, T-363, T-364, T-513 closed with r5 / r6.
- Team: every run since 04:20 closed with a final line; one Checker overlap-guard INCOMPLETE at 06:51 (by design, previous run still active); Checker 07:51 still running; stamps written ahead of the clock corrected by the Checker (and by me in this run). Selfcheck PASS (codemap, t061, freeze 0); queue check 14 actionable, 0 flagged, 0 stall.
OWNER PACKAGE: none new (designer list incl. the dome build-up item when T-787 adds it, stair skirting form, 2F top roof, release switch remain with you).
NEEDS FIXING: none new. The fill_from_index.py formwork step was fixed by your main chat's 04:34 audit (overlay formwork rows dropped, T-762 governs).

## LEAD REPORT 2026-11-14 04:20 UTC
Drive readable; no new files or photos (newest file in the project folder 21 Oct). Candidate of record V3.0.81 (not released); V2.9 + route G untouched. V3.0.82 (earthworks, waterproofing, fence / site) with the Checker now.
- Lines with no figure (non-rebar): 295 (V3.0.81) -> 211 in V3.0.82 (READY). The merged, not yet wired sets cover masonry, plaster / paint, concrete points (round .83) and stairs, openings / ceilings / domes, missing families (round .84); FILL ends with those two rounds.
- Concrete (m3): 406.79 vs freelancer 352.44 (+54.36, +15.4 %), residual 0: +55.47 is scope outside his RC total (blinding, RC parapets, lintels, safety line). Paired beams +13.28 = ENGINE_RIGHT +14.47 / RULE_DIFFERENCE -8.32 (his columns stop under beams) / UNRESOLVED +7.14 (unmarked pieces at default depth, projection strips D-05 / D-26); other elements -18.86 = ENGINE_RIGHT -17.99 / RULE_DIFFERENCE +4.97 / UNRESOLVED -5.84. Checker re-measured C11, F3, the C11 necks and two beams by hand: AGREE.
- Windows (m2): 100.05 vs 116.9 (-14.4 %) split to 0: W02 head -13.29, drawn heads -5.72 (ENGINE_RIGHT, Checker AGREE on W02), others +2.16. Domes 2 x 24.15, shutters 12.50, no freelancer line. External doors 12 vs 6 pcs still a classification question: new row.
- Stairs (m2 / lm): landings 20.69 vs 12.74, skirting 28.52 vs 29.87 lm (-4.5 %), soffit 31.66 vs 39.99 (-20.8 %), tread + riser vs his per-step lump RULE_DIFFERENCE; sloped skirting waits on your stair skirting form ruling.
- Missing families: 39 -> 0 uncovered (23 new lines). Gypsum ceilings 411.3 vs 409.6 m2 (+0.4 %); sanitary 12 WC / 17 basins / 6 showers / 19 floor drains measured; spatter dash 1,622 m2 inside vs his 504.5 RULE_DIFFERENCE; cornice 302.9 vs 427.5 lm (-29.1 %, UNRESOLVED, next difference row after wiring).
- Masonry -22.2 % (981.4 vs 1,260.7 m2) and plaster +5.8 % unchanged: split task next for worker 2. Roof membrane -10 % / finish -12.7 %: next for worker 1. Wet-room membrane +19 % and upturn in different units (ours 126 lm equivalent vs his 144.6 lm): new row.
- Decisions: your 14 Nov plan started: one-command skeleton + smoke test (worker 1), one opening table (worker 2), project inputs sheet (worker 3 after wiring), wall-band masonry as the second method (after those two), schedule-first structure started (worker 1). Room table waits for week 2.
- Team: every run since 00:20 closed with a final line (the Checker run of 23:51 closed at 01:05 after merging V3.0.81); Checker 03:51 still running; selfcheck PASS (codemap, t061, freeze 0); queue check 19 actionable, 0 flagged, 0 stall.
OWNER PACKAGE: none new (designer list, stair skirting form, 2F top roof and the release switch remain with you).
NEEDS FIXING: docs/agents/boq/fill_from_index.py formwork step (whole-member ratio on partial lines) still unchanged since 13 Nov 14:18; the wired lines are correct, but fix it before any rebuild on a newer index.

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
