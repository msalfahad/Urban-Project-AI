# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)



## LEAD REPORT 2026-11-07 04:15 UTC

Drive read OK (no file created or modified in the project folders since 00:00 UTC 7 Nov, no photo task). Training villa: candidate ARCH_TAKEOFF_V3.0.58 / master 1.55.0 (NOT RELEASED), no candidate quantity moved; released V2.9 + route G unchanged. Six merged, one rejected since 00:15 (3 WORKED, 3 PARTIAL, 1 FAILED):
- Steps (lm / m2 / nr): E1 entrance 4 x 2.80 = 11.20 lm, nr 4: ENGINE_OMISSION VERIFIED by the Checker's own DXF read. External door steps = one element (threshold nosing + riser): 3.50 lm / 0.390 m2 at 4 doors (+D-GF-09 riser HELD 0 .. 0.27 m2); payable length open (edge 3.50 vs stone 3.80 lm) -> T-592. Stair steps ours / his: ST-01 51.75 / 75.60 lm, ST-02 16.10 / 33.60 lm, causes close exactly. PARTIAL (4 / 5 openings re-read).
- Rails / guards (lm): ours 54.869 vs his 18.95 (a lone typed constant): -35.919 closed: guards -19.150, ST-01 rail -15.953, D1 -1.042 ENGINE_RIGHT scope, +0.226 UNRESOLVED. Nosing ours 87.35 + 20 HELD vs his 123.20 lm closed by cause; nr 69 vs 96. PARTIAL: his workbook over the connector limit, his side not re-read.
- Columns (m3): 1F +0.555 (+21.74 %) = RULE_DIFF +0.460 (head depth 0.75 / 3.45) + ENGINE_RIGHT +0.095; GF +1.174 (+10.18 %) = RULE_DIFF +2.034 + ENGINE_RIGHT -0.860 (4 of his rows with no drawn member, 1 C11 missed); Checker's own hatch count CONFIRMS COUNT -1.031. PARTIAL: RULE_DIFF parts worker-proposed -> T-589 / T-590.
- Dome / ring / lift-wall bars (t): every component valued, bounded or HELD by name; lift verticals 62 .. 78; strict low 0.733792 -> 0.767783 t; laps (no printed length), hooks, ring depth HELD; valued 0; his TYPED_LUMP NOT_COMPARABLE.
- Lintels: 16 lines classed for wiring (6 AT_LEAST 0.502 m3, 10 HELD, 0 RELEASED; released 1.016 -> 0 m3 on wiring). Width basis REJECTED: D-GF-09 frame 1.00 over a 0.90 masonry gap is a drawing conflict (lintel 1.20 .. 1.50, +0.3 lm), not ENGINE_RIGHT -> T-581 r2.
- Statement V6: 25 sections residual 0. Learned (ADOPTED): stair steps count x length, bound every bar component, statements restated row by row, measured-set % split by cause; PROPOSED: frame drawn over masonry = DRAWING CONFLICT, never resolved by method.
- Missing: lintel width (r2), yard / stair skirting, door-step payable length; statement V7, manifest V9; rule provenance of every RULE_DIFF (new audit, both lanes); all wiring.
- Team health: 6 merged / 1 rejected since 00:15; every run closed; all agents ran code (self-check PASS; venv empty at start in 3 worker runs, self-repaired by setup); READY 0; TODO 9 (S 3, A 3, I 2 + T-581 r2) + 4 blocked; queue check 22 actionable, 0 flagged, 0 stall.
- 10 Nov (every trade wired): LOW, 3 days, wrapper only (T-582 cleared the readiness findings). 12-13 Nov tables: HIGH (23 trades closed, 3 open).
OWNER PACKAGE: no new decision today. Still open: Q-80 (15 cm black block face size; 15 walls 175.9 m2 HELD).
NEEDS FIXING (owner only): wrapper allow-list on main scripts/agent_env.sh:211 (run of research/agents_t*/ scripts) blocks every Gate B package (T-498, T-423 r2, T-525, T-563), now their only blocker; notified 04:15 5 Nov, not re-notified. Freelancer floors / rails workbooks over the 6.2 MB connector limit (Checker cannot re-read his side): a zipped or split copy on Drive. Also: Kuwait 1990 spec copy under 6 MB; repository privacy switch; PyMuPDF decision; PR #3 clean-up.

## LEAD REPORT 2026-11-07 00:15 UTC

Drive read OK (no file created or modified in the project folders since 20:00 UTC 6 Nov, no photo task). Training villa: candidate ARCH_TAKEOFF_V3.0.58 / master 1.55.0 (NOT RELEASED), no candidate quantity moved; released V2.9 + route G unchanged. Six merged since 20:14 (4 WORKED, 2 PARTIAL, 0 rejected):
- Lintels (nr / lm): freelancer has NO lintel row (Checker CONFIRMED): NOT_COMPARABLE as a figure; his 54 deducted openings through the owner rule = 27/17/8/1/1 nr, 84.9 lm vs engine 60 AT_MOST, 91.5 lm; +6 nr closed by named cause (width read 3 openings, W17 not in masonry, engine-only identities; closure re-derived by the Checker). One door on a mixed width basis (attribution only) -> T-581.
- Skirting (lm): 197.279 vs 282.85 (-85.571): RULE_DIFF -43.62 (doors / passages), ENGINE_RIGHT -32.08, UNRESOLVED -9.69 named; gross vs gross -2.37 %. Stairs 12.15 vs 29.87 (flights HELD >= 17.009); yard 81.32 lm scope open -> T-585. PARTIAL: 1 / 11 outlines re-measured.
- Marble / thresholds / sills, units apart: m2 18.04 vs 26.80, lm 56.83 vs 21.70, nr 67 vs 11, causes close; his 'm2' total is 164.54 area + 130.9 count x length (UNIT). E1 step 11.20 lm ENGINE_OMISSION PLAUSIBLE, external door steps undefined -> T-584. PARTIAL: engine side 0 / 8 groups re-measured.
- Dome shell / ring / lift-pit wall bars (t): first measurement from ST sheets, 0.734 .. 1.162 HELD_RANGE (valued 0), Checker 3 / 3 classes AGREE; lift-wall low not strict (62-bar reading 0.156642 t/m), laps / links HELD -> T-583. His 44.19 t TYPED_LUMP: no %.
- Wiring dry run: V2-V8 rows apply cleanly on a V3.0.58 copy (0 STALE, 0 double-written lines); targets plaster 580.5819 -> 363.3738 m2, windows +9.870 m2. Lintel rows lack a class (1.016 -> 0 vs 0.502 m3 released): fixed in T-582 before T-498 Gate B. Statement V5: 17 sections residual 0.
- Learned: ADOPTED ceilings by face class; PROPOSED (Checker-accepted) overlay before Gate B, class each reference cell by its own unit, bar-sphere dome counting, outline vs deduction terms, check the reference row exists first, restate statements row by row.
- Missing: handrails / nosing, 1F columns +21.7 %, steps, yard skirting, lintel width basis, dome-bar laps; statement V6; all wiring.
- Team health: 6 merged / 0 rejected since 20:14; every run closed; all agents ran code (self-check PASS); READY 0; TODO 8 (S 3, A 3, I 2) + 4 blocked; queue check 22 actionable, 0 flagged, 0 stall. One Verifier text with workbook cell values refused by the session check and rewritten (no leak).
- 10 Nov (every trade wired): LOW, 3 days, wrapper. 12-13 Nov tables: HIGH (19 trades closed, 6 open).
OWNER PACKAGE: no new decision today. Still open: Q-80 (15 cm black block face size; 15 walls 175.9 m2 HELD).
NEEDS FIXING (owner only): wrapper allow-list on main scripts/agent_env.sh (run of research/agents_t*/ scripts) blocks every Gate B package (T-498, T-423 r2, T-525, T-563); notified 04:15 5 Nov, not re-notified. Also: Kuwait 1990 spec copy under 6 MB; repository privacy switch; PyMuPDF decision; PR #3 clean-up.

## LEAD REPORT 2026-11-06 20:14 UTC

Drive read OK (no file created or modified in the project folders since 16:00 UTC, no photo task). Training villa: candidate ARCH_TAKEOFF_V3.0.58 / master 1.55.0 (NOT RELEASED), no candidate quantity moved; released V2.9 + route G unchanged. Six merged since 16:17, all WORKED:
- Rebar (B11, t): freelancer 44.19 t = 7 typed lumps, no bar row: RULE_DIFF, NOT_COMPARABLE, no %; engine 9.375 t valued + 14.278 .. 19.647 t held + 799 blank lines. ENGINE_OMISSION confirmed: dome shells / rings / lift-pit walls have no rebar line (V8 HELD rows; measure T-575).
- Doors / windows (nr and m2 apart): 1F doors 10 vs his 8, Checker's own census of 27 drawn leaves: ENGINE_RIGHT; windows 28 (+W02 HELD) vs 29 nr, like for like -3.975 m2 (-4.95 %); W17 9.870 m2 (Q-76 A) into V8.
- Ceilings (m2): board 366.891 vs 409.58 (-10.42 %, not a verdict): HELD -36.52, light-well slab opening he ceils 16.005 m2 (ENGINE_RIGHT, Checker exact); like for like -0.33 %; 6.161 m2 UNRESOLVED named.
- Structural HELD bounds (m3): necks >= 9.724 (printed minimum excavation only: LOWER_ONLY), pit backfill >= 99.645; measured set GF columns +10.2 % (-6.2 % net JOINT_HEAD), 1F columns +21.7 % without a cause split: material, investigation T-576 (no owner question; ERS 2.7 not met).
- Statement V4 + manifest V8 merged (return paint 23.070 m2 HELD rows, dressing A08 ESTIMATED, pier returns 2.253 m2, rebar rows). RFI-A08 text corrected (F-T569-2, no quantity).
- Learned (ADOPTED): gross vs gross only; plastered dry face implies a paint face; class the benchmark's basis first; count openings by drawn leaves. PROPOSED: ceilings by face class; a printed minimum is a one-sided bound.
- Missing: lintel count, skirting, thresholds / sills, handrails / nosing vs freelancer; dome / lift-pit bars; statement V5; wiring of everything (new rows T-575 .. T-580).
- Team health: 6 merged / 0 rejected since 16:17; every run closed; all agents ran code (self-check PASS); READY 0; TODO 8 (S 3, A 3, I 2) + 4 blocked; queue check 22 actionable, 0 flagged, 0 stall.
- 10 Nov (every trade wired): LOW, 4 days, Gate B behind the wrapper; T-580 dry-runs the V6-V8 rows so packages merge at once. 12-13 Nov tables: HIGH (16 trades closed, 6 open).
OWNER PACKAGE: no new decision today. Still open: Q-80 (15 cm black block face size; 15 walls 175.9 m2 HELD).
NEEDS FIXING (owner only): wrapper allow-list on main scripts/agent_env.sh (run of research/agents_t*/ scripts) blocks every Gate B package (T-498, T-423 r2, T-525, T-563); notified 04:15 5 Nov, not re-notified. Also: Kuwait 1990 spec copy under 6 MB; repository privacy switch; PyMuPDF decision; PR #3 clean-up.

