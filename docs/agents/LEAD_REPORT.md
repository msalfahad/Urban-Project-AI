# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)



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

## LEAD REPORT 2026-11-07 16:17 UTC

Drive read OK (no file created in the project folders since 12:00 UTC 7 Nov, no photo task). Training villa: candidate ARCH_TAKEOFF_V3.0.58 / master 1.55.0 (NOT RELEASED), no candidate quantity moved since 12:16; released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %). Whole lines verified in the candidate: 2 (CONC.SLAB 60.28 m3, footing blinding 12.73 m3); released 0.
- B1 earthworks plan (m2): 24 pits union 129.234375 (overlap counted once), ours outside the pool 124.648614, pool envelope 11.851050: Checker own ST read AGREE to 1e-6 (engine -0.000941, arc chords, immaterial). Plans VERIFIED (plan only), depths HELD (no survey), his side NO_ROW. FN 180C drawn notched under F9 -> concrete overlap counted once: T-605.
- External steps (lm): street gate G-01 step 2.500 lm + riser 0.375 m2 ENGINE_OMISSION (Checker own read); ours 7.30 vs his 7.70 lm (-0.40, -5.19 %) UNRESOLVED (his rows name no opening); count 6 = 6. Fix row into wiring list V12.
- Skirting (lm): A-1F-01 doorless jambs +0.30 (209.428592 -> 209.728592, +0.14 %) FREELANCER_RIGHT; GF OP-011 / 1F OP-007 are lift landing doors (label PASSAGE wrong, no skirting) -> T-608 scope by trade. Room residual 9.693 lm still UNRESOLVED (1 / 11 outlines re-measured) -> T-606.
- Beams / columns (m3): joint rule record REJECTED once: it promoted whole beam rows (2.248826 m3 of residual) to SOURCED. Rework: rule cites only the matched joint (gross 5.3325); GF matched source ruled T-551 2.28125 (V9 reading of record), other readings to T-600. Beam packs P01 / P02 / P03 1F VERIFIED by the Checker; 2F 0.420 m3 named (B1 footprint netted with an un-rowed run).
- Statement V9 merged (residual 0; stair skirting a range 17.009 .. 23.300 lm, never summed; rebar 34.815 t UNRESOLVED, no %). Wiring list V11 merged (0 stale).
- Learned (5 rows ADOPTED, ERS s.7): a rule reclasses only the part of a row it explains; census plot-boundary gaps too; a kind label is never evidence; drawn outlines, not schedule rectangles, for overlaps; restatements move only what they restate.
- Missing / gate: wiring (Gate B) waits on the wrapper; reconciliation tables on track for 12-13 Nov (V10 after V12).
TEAM HEALTH: 10 runs since 12:12 (W1 2, W2 2, W3 2, Verifier 4), all closed, 0 empty, every agent ran code, self-check PASS (this run codemap / t061 / freeze PASS); 5 merged, 1 rejected (T-599, fix row first in S); READY 0; 8 TODO (S 3, A 3, I 2); queue check 22 actionable, 0 flagged, 0 stall.
OWNER PACKAGE: none new today (all decisions settled by drawings or delegated rules; ORR-007 stair skirting form and Q-80 already with you).
NEEDS FIXING (only you): (1) wrapper allow-list for research/agents_t*/ scripts in main scripts/agent_env.sh:211 (CRITICAL, notified 5 Nov; blocks every Gate B; 10 Nov milestone LOW); (2) freelancer floors / rails workbooks over 6.2 MB (zipped copy); (3) privacy switch of the public repo.

## LEAD REPORT 2026-11-07 12:16 UTC

Drive read OK (no file created in the project folders since 08:00 UTC 7 Nov, no photo task). Training villa: candidate ARCH_TAKEOFF_V3.0.58 / master 1.55.0 (NOT RELEASED), no candidate quantity moved since 08:15; released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %). Whole lines verified in the candidate: 2 (CONC.SLAB 60.28 m3, footing blinding 12.73 m3); released 0.
- Stair nosing (lm): 88.500 -> 107.371 valued vs his 123.20; -15.829 lm closed by cause (width 1.150 both plans + ST vs his 1.20, his extra pieces, curtail +1.621 he omits), residual 0; 4 winder fronts 4.600 .. 6.943 HELD (designer). Checker own DXF read AGREE.
- Finishes provenance: 119 RULE_DIFF rows, 40 cited, 76 citation-corrected, 1 our error: A-1F-01 doorless jambs 0.30 lm FREELANCER_RIGHT (UP-SKIRT-001); GF OP-011 / 1F OP-007 depth HELD. -> T-601 census, T-604 fix rows.
- Structural provenance: 44 rows, 0 with a recorded source; 6 column / beam joint rows +2.369 m3 signed UNRESOLVED; 6 rebar groups 34.815 t HIS_SIDE_UNREADABLE (typed lump). LEAD RULING (Q-62 A delegates; ERS 2.7 not met, no owner question): column owns the joint to the slab top, beam face to face (engine, ERS 10-31 ADOPTED, T-394 / T-395 verdicts); my 11-06 register entry was wrong and is corrected. -> T-599 rule version, T-600 residuals GF -0.620 / 1F -1.208 m3.
- Restatements: dome ring bars both faces, bounded low 0.789554 t; F10 + F S02 1.960 .. 2.275 m3, footing low 7.6285 m3 (Checker AGREE). Statement V8 residual 0; his door steps 2.90 lm UNRESOLVED -> T-602.
- Learned: a delegated convention must be written once as a rule version before rows cite it (lessons row ADOPTED); two drawn forms of one skirting are never summed (F-C-T593-1, guard in T-603 and T-498 Gate B).
- Missing / gate: wiring of every merged piece (Gate B) waits on the wrapper; scorecard tables on track for 12-13 Nov.
TEAM HEALTH: 10 runs since 08:12 (W1 2, W2 2, W3 2, Verifier 4), all closed, 0 empty, 0 rejected, every agent ran code, self-check PASS (this run PASS / PASS / PASS); 6 merged; READY 0; 8 TODO (S 3, A 2, I 3); queue check 22 actionable, 0 flagged, 0 stall.
OWNER PACKAGE: none new today (joint ownership settled under Q-62 A; stair skirting form ORR-007 and Q-80 already with you).
NEEDS FIXING (only you): (1) wrapper allow-list for research/agents_t*/ scripts in main scripts/agent_env.sh:211 (CRITICAL, notified 5 Nov; blocks every Gate B and the 10 Nov milestone, now LOW); (2) freelancer floors / rails workbooks over 6.2 MB (zipped copy); (3) privacy switch of the public repo.
