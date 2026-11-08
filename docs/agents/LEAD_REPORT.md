# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)

## LEAD REPORT 2026-11-08 04:15 UTC

Drive read OK (no file created or modified in the project folders since 20:00 UTC 7 Nov, no photo task). Training villa: candidate ARCH_TAKEOFF_V3.0.58 / master 1.55.0 (NOT RELEASED), no candidate quantity moved since 00:15; released V2.9 + route G unchanged.
- Beams / columns (m3): residual 2.248826 UNRESOLVED (unchanged), now split per mark as capacity bounds with each crossing node booked once (GF B27 node 0.243784 vs 0.375801 entered; B22 0.074690; 1F 0.067425; Checker re-added all three). Only B2 / CB5 / CB7 RULE_DIFFERENCE at checked columns.
- Beam ends (m3): CB11 +0.018750 and CB8 col 4 +0.002140 ENGINE_WRONG OMISSION confirmed by the Checker; CB8 col 2 east +0.002309 was wrongly called billed (ledger model tolerance 0.01 m3 > piece): rework r2. Checker withdrew its own col 3 claim (credited, ENGINE_RIGHT).
- Lintels (nr): his 54 vs engine 60 split by opening: ENGINE_RIGHT 3..5 plus W17 (curved band, sagitta 0.711 m: no straight stock lintel), UNRESOLVED 2..4. No lintel added or dropped.
- Scorecard (12-13 Nov tables, statement V10): 36 lines in 20 trade/unit tables; lines VERIFIED 1, rows VERIFIED 21; B11 rebar 44.19 vs 9.375306 t UNKNOWN (798 engine lines HELD blank); floor tile 409.58 vs 387.09405 m2 (+5.49 % printed, not a verdict) 41 rows UNKNOWN; wall tile 433.83 vs 340.3038 m2, 138.39 HELD; external plaster 1502.84 vs 0 (candidate line BLOCKED_RFI, integration T-314 behind PR #4).
- Lift landing head: printed nowhere; bounded above by ring beam soffits (GF 3.70 / 1F 3.40 / 2F 3.75 est.), low end HELD; READY with the Checker; 0.000 m2 candidate change.
- Learned (ERS s.7): node capacity once / balancing term never a cause ADOPTED; status caps (bare stamp is not a re-measure) ADOPTED; count residual split by opening, curved band no straight lintel ADOPTED; billing only inside the line's measured extent PROPOSED (T-614 r2).
- Next: evidence rows so whole lines can close: floor tile 41 rows, wall tile 47, beams 12 + columns 6; statement + scorecard V11; Q-80 15 cm walls out of HELD.
- Missing / gate: wiring (Gate B) waits on PR #4; 10 Nov end-to-end LOW (2 days); 12-13 Nov tables HIGH.
TEAM HEALTH: 10 runs since 00:15 (W1 2, W2 2, W3 2, Verifier 4), all closed, 0 empty, all ran code, self-check PASS (this run codemap / t061 / freeze PASS); 3 merged, 2 rejected (T-613 r1 merged r2; T-614 r1 rework), 1 READY; queue check 23 actionable, 0 flagged, 0 stall checks.
OWNER PACKAGE: none new (all settled by drawings, your Q-80 answer or delegated rules; ORR-007 stair skirting form still with you).
NEEDS FIXING (only you): (1) merge PR #4 (open, mergeable, run allow-list for research/agents_t*/ scripts) - blocks every Gate B and the 10 Nov milestone; (2) freelancer floors / rails workbooks + 1990 spec when ready (not blockers).

## LEAD REPORT 2026-11-08 00:15 UTC

Drive read OK (no file created in the project folders since 20:00 UTC 7 Nov, no photo task). Training villa: candidate ARCH_TAKEOFF_V3.0.58 / master 1.55.0 (NOT RELEASED), no candidate quantity moved since 20:18; released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %). Whole lines independently verified in the candidate: slab 60.28 m3 + footing-pit blinding 12.73 m3; released 0.
- Beams / columns (m3): residual 2.369278 UNRESOLVED (unchanged). Split r1 REJECTED: B27 oblique node booked as carrier from B4 and B5 (0.180 vs drawn 1.120 x 0.20 x 0.50 = 0.112), SHORT -2.427 GF used as a cause -> r2 FIRST. Proven: 1F 69D joint >= 0.075 m3 (settles 0.385 / 0.460 as a set choice). NEW F-C-P02-3 CB11 corner-column omission +0.018750 m3 ENGINE_WRONG -> beam-end census (T-614). Beam crossings: billed once, UNDER -0.005957 .. -0.007252 m3 (PV).
- Footings (m3): FN 180C notch owned by F9, pair 5.307 = Checker own read; his 5.349 (+0.042) ENGINE_RIGHT; side forms 7.46 .. 7.685 m2 HELD.
- Skirting (lm): manifest V13 209.728592 -> 198.558592 (-5.33 %) when wired. GF open room +0.10 ENGINE_RIGHT VERIFIED; his -17.013904 (-23.3 % of that room) UNRESOLVED (no drawn reading gives 72.92). Small residuals 2.78 lm -> T-618.
- Stairs (lm / nr): steps + nosing 8.40 lm / 7 nr one cause, ENGINE_RIGHT once (56 drawn risers), never summed across lines.
- Openings (pcs): 3 lift landing doors DRAWING-CONFIRMED; ARCH.PASSAGE 9 -> 6 (FR-T608-1); landing door supply HELD x 3; head height unprinted keeps 2 x 3.35 m2 plaster / paint ranges -> T-617 reads the sections before any RFI. Lintels 60 AT_MOST vs his implied 54: -6 nr by opening -> T-616.
- Blockwork: your Q-80 A applied next (T-615): 175.9 m2 of 15 cm walls leave HELD (about 2,198 units, 1.946 m3 panel mortar, 16.3 cement bags, to be reproduced).
- Learned (ERS s.7): node capacity once across marks, a balancing term is never a cause (PROPOSED); a beam owns its band beyond a narrow column (PROPOSED); skirting-where-floor and crossing-union ADOPTED.
- Missing / gate: wiring (Gate B) waits on PR #4; 12-13 Nov tables on track (V10 merged, T-613 next).
TEAM HEALTH: 10 working runs since 20:15 (W1 2, W2 2, W3 2, Verifier 4), all closed, 0 empty, all ran code, self-check PASS (this run codemap / t061 / freeze PASS); 7 merged, 2 rejected (T-609 r1 merged on rework, T-600 r1 reworked next); READY 0; 8 TODO (S 3, A 3, I 2); queue check 22 actionable, 0 flagged, 0 stall.
OWNER PACKAGE: none new (all settled by drawings, your Q-80 answer or delegated rules; ORR-007 stair skirting form still with you).
NEEDS FIXING (only you): (1) merge PR #4 (run allow-list for research/agents_t*/ scripts; PR #3 merged, thank you) - blocks every Gate B; 10 Nov milestone LOW; (2) freelancer floors / rails workbooks and the 1990 spec (coming, not blockers); (3) privacy switch of the public repo.

## LEAD REPORT 2026-11-07 20:18 UTC

Drive read OK (no file created in the project folders since 16:00 UTC 7 Nov, no photo task). Training villa: candidate ARCH_TAKEOFF_V3.0.58 / master 1.55.0 (NOT RELEASED), no candidate quantity moved since 16:17; released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %). Whole lines independently verified in the candidate: slab 60.28 m3 + footing-pit blinding 12.73 m3; released 0.
- Beams / columns (m3): joint rule UP-CONC-JOINT-001 1.0.0 MERGED (Checker own ST read AGREE): matched joint RULE_DIFFERENCE signed 0 / gross 5.3325; residual 2.248826 + B7 0.120452 = 2.369278 UNRESOLVED -> T-600 by column mark; 1F head read 0.385 vs 0.460 (P.C 20x50 0.075) to settle there. Full suite = baseline (t374 x2 order-dependent, t485).
- Skirting (lm): 1F living -9.693 was a net: +8.40 well walls ENGINE_RIGHT, +0.20 notches, and NEW F-T606-1 ENGINE_WRONG 11.17 lm on stair-opening walls with no floor (Checker re-measured): when wired 209.728592 -> 198.558592 (-5.33 %) -> T-611. Unexplained left: GF open room 16.914, 1F curved 0.739, 2F corridor 0.70 -> T-612.
- Beam overlap (m3): Checker P03 GF found B27 / B1 billed twice at col 35C, ENGINE_WRONG -0.005295 (immaterial alone) -> T-610 census of every crossing on every floor.
- Wiring list V12 MERGED (0 stale; skirting +0.30 lm). With the Checker (READY): footing overlap (no line moves; FN row +0.042 m3 ENGINE_RIGHT), step / nosing 8.40 lm one cause counted once (ENGINE_RIGHT proposal), statement V10.
- Learned (ERS s.7): a residual is a net until split by face (ADOPTED); skirting only where a floor meets the wall (PROPOSED, T-611); crossing members by union of drawn outlines (PROPOSED, T-610).
- Missing / gate: wiring (Gate B) waits on the wrapper; 12-13 Nov tables on track (V10 READY, T-613 next).
TEAM HEALTH: 10 runs since 16:12 (W1 2, W2 2, W3 2, Verifier 4 incl. 1 overlap-guard skip by design), all closed, 0 empty, every working run ran code, self-check PASS (this run codemap / t061 / freeze PASS); 3 merged, 0 rejected; READY 3 (CHECKER-RUNS); 6 TODO (S 2, A 2, I 2); queue check 23 actionable, 0 flagged, 0 stall.
OWNER PACKAGE: none new today (all settled by drawings, delegated rules or Lead rulings; ORR-007 and Q-80 already with you).
NEEDS FIXING (only you): (1) wrapper allow-list for research/agents_t*/ scripts in main scripts/agent_env.sh:211 (CRITICAL, notified 5 Nov; blocks every Gate B; 10 Nov milestone LOW); (2) freelancer floors / rails workbooks over 6.2 MB (zipped copy); (3) privacy switch of the public repo.
