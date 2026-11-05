# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)


## LEAD REPORT 2026-11-05 20:25 UTC

Drive read OK (no file created in the project folders since 16:00 UTC, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.58 c9570e6c / master 1.55.0 (NOT RELEASED), no candidate quantity moved since 04:15; released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %). All results below are Checker-verified pieces, UNWIRED. Development project 2: paused, not measured.
- Lintel reinforcement (structural, B9-02): 63.162 kg AT_LEAST -> two parts AT_LEAST: PRODUCED 6 = 38.761728 kg, FLAGGED 10 = 24.301496 kg (63.063224 kg; W18 -0.098504 kg, 32.7 mm of its opening is inside C8); bar ends / bends / hooks HELD (ST p.13 prints none; designer item), links PROVISIONAL. Freelancer: no lintel row (UNRESOLVED).
- Blockwork ends (structural, B9-04): END_CENSUS_V3 reads the wall pieces by plan role; 12+1 column ends reproduced, 118 interior junctions listed (117 = T-355 1:1): 0 m / 0 m2 / 0 blocks change; ties +30 nr and mesh +40.90 m.l have no BOQ line -> T-539 (missing category).
- Lintel glue host (structural / materials): rule R-T498-2 sound, REJECTED on one binding: D-GF-06 hi 1.54 m is a min-bearing figure, the ceiling is 1.899 m: GF glue [23.769, 23.895] -> [23.4459, 23.895] kg (low end -1.36 %); 1F host HELD (<= 451.60893 kg). Rework r2.
- Sand (materials): purchase unit = loose m3 (Q-45 / Q-53 / Q-78); villa installed >= 16.973531 .. 22.404053 m3, procurement >= 17.746996 .. 23.449040 m3 (+0.158314 vs T-523: stair allowance was bound as procurement); t / loads HELD (no sourced load size / density) -> T-540.
- Stair bed (finishes, B7): your Q-53 39.485 m2 vs 35.4313 m2 reconciled to 0 residual (tread per riser -3.000, width 1.20 vs 1.15 -0.660, full E1 riser -0.420, polygon -0.0006, scope +0.027); Gate A PASS, merge blocked 3 Checker runs by a test that pinned its live commit -> gate fix T-538. Risers / landings beds -> T-542.
- Roof WP vs freelancer: 209.658440 m2 once wired vs 285.00 m2 (-26.4 %), upturn 187.834160 vs 194.00 m (-3.2 %): component reconciliation T-541 for 12-13 Nov; your Q-34 top-roof hold stands (not re-asked).
- Learned (lessons rows PROPOSED): a bound carries its direction (a min-bearing figure is never a ceiling); a test never uses a live commit; a sub-5 mm sliver piece never sets an element property.
- Gates: lowest open gate 0 (t485 red behind the wrapper; T-538 new gate-0 row, no wrapper needed). 10 Nov end-to-end BOQ: LOW (about 10 Gate B packages, none can start; 18 verified pieces wait).
- Team health: 4 merged, 1 rejected (narrow, fault named), 0 blocked since 16:30; every run closed with a final line; 0 empty runs; Checker merged within 1 run of READY. Self-check codemap / t061 / freeze PASS. New rows 5 (I 1, S 1, A 3).

OWNER PACKAGE: none (no engineering item meets standard s.2.7).

NEEDS FIXING (owner only, unchanged since 04:15, not re-notified): the run wrapper (scripts/agent_env.sh on main, line 211, still at eafbb0f6) lets `run` start only the scoreboard and key-map tools; every integration package and the registry gate fix need research/agents_t*/ scripts. Needed: widen `run` to research/agents_t*/*.py, or name another approved path. This alone decides the 10 Nov milestone. Also open: Kuwait 1990 spec over the connector limit; repository privacy switch; PyMuPDF decision; PR #3 clean-up.

## LEAD REPORT 2026-11-05 16:30 UTC

Drive read OK (no file created in the project folders since 12:00 UTC, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.58 c9570e6c / master 1.55.0 (NOT RELEASED), no candidate quantity moved since 04:15; released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %). All results below are Checker-verified pieces, UNWIRED. Development project 2: paused, not measured.
- Waterproofing (architectural, B8-06): pool-court ledge 0 .. 0.639573 m2 HELD -> 0.639573 m2 MEASURED (Checker own DXF AGREE; 100 % under the +9.70 cover but open to the void: balcony condition of UP-WP-ROOF-001); FIN.WP.ROOF 209.018867 -> 209.658440 m2 (+0.31 %) and upturn +0.551614 lm once wired. Freelancer roof WP 285.00 m2 single line: RULE_DIFFERENCE / UNRESOLVED (-26.7 % -> -26.4 % if wired).
- Lintels (structural, B9-02): curved-bay pier W18 END 0.478 -> 0.578 m (V2 chord was not drawn; V3 reads the drawn face, Checker 0.577992 AGREE); no state moves: 6 PRODUCED / 10 HELD, end concrete 0.372692 .. 0.437542 m3 unchanged; only the W18 RC ceiling 0.978 -> 1.077 m. Freelancer: no lintel row (UNRESOLVED).
- Blockwork (structural, B9-04): 12 run ends abut RC columns that the junction censuses missed; wall length / m2 / blocks delta 0 (gap 0), perimeter mortar +0.007021 m3 (1F-W09), ties +30 nr, mesh +40.90 m.l, rest HELD by name. 0.15 m walls' module still HELD (new row T-533).
- Materials: stair 1:3 bed per your Q-53 C: 9.576 bags + 0.9975 m3 sand per m3; on 35.4313 m2 = 1.062939 m3, 10.18 bags (procurement 10.69); your question quoted 39.49 m2: 4.06 m2 (10.3 %) unexplained -> T-534 before wiring. Sand has no sourced purchase unit -> T-535.
- Learned (lessons rows added 16:30): a constructed chord is never a masonry end (ADOPTED); covered-in-plan is not dry: a ledge open at a side is the balcony rule (ADOPTED; my own row's 0.48 m2 expectation was wrong, worker right at 1.20 m2 on the fixture); use the exact owner-rule derivation, the rounded figure only as a label (PROPOSED).
- Gates: lowest open gate 0 (t485 red, T-525 BLOCKED by the wrapper); Gate 2 integration stalled. 10 Nov end-to-end BOQ: LOW (about 10 Gate B packages, none can start; 14 verified pieces wait).
- Team health: 5 merged, 0 rejected, 1 blocked (correct stop) since 12:20; every run closed with a final line; 0 empty runs; Checker merged within 1 run of READY. 6 new rows (S 2 + T-531 first, A 2, I 2). Self-check codemap / t061 / freeze PASS. Queue check: 20 actionable rows, 0 flagged, 0 stall checks.

OWNER PACKAGE: none (no engineering item meets standard s.2.7).

NEEDS FIXING (owner only, unchanged since 04:15, not re-notified): the run wrapper (scripts/agent_env.sh on main, line 211, still at eafbb0f6) lets `run` start only the scoreboard and key-map tools; every integration package and the registry gate fix need their research/agents_t*/ scripts. Needed: widen `run` to research/agents_t*/*.py, or name another approved path. This alone now decides the 10 Nov milestone. Also open: Kuwait 1990 spec over the connector limit; repository privacy switch; PyMuPDF decision; PR #3 clean-up.

## LEAD REPORT 2026-11-05 12:20 UTC

Drive read OK (no file created in the project folders since 08:00 UTC, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.58 c9570e6c / master 1.55.0 (NOT RELEASED), no candidate quantity moved since 04:15; released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %). All results below are Checker-verified pieces, UNWIRED.
- Lintels (structural): project RC schedule governs 16/16: 6 PRODUCED, 10 HELD on short bearings; lintel concrete at the 10 short ends 0.514 -> 0.372692 .. 0.437542 m3 (0.037838 m3 already inside column lines, 0.01686 lintel-on-lintel once, 0.02176 not buildable as drawn: designer item, HELD). Checker found the curved-bay pier end W18 0.578 vs 0.478 m (no state moved) -> bearing V3.
- Black-block mortar (structural): joints at column faces and soffits +0.098145 m3 on 1.269444 m3 (+7.73 %, COMPUTED, Checker own DXF AGREE on 2 junctions); 0.15 m walls 0.0786 .. 0.0899 m3 HELD (module); 4 run ends at columns missing from the junction censuses -> new census row.
- Pool court (architectural): bath window sill '84' printed -> window upturn 0.500 lm MEASURED (roof upturn 186.783 -> 187.283 lm, +0.27 % if wired); ledge upturn 0 .. 3.528 -> 0 .. 0.552 lm + 2.977 lm glazing transition; ledge membrane 0 .. 0.640 m2 HELD (exposure rule needs a version from the drawn cover outline, not an angle).
- Materials: tile-bed mortar installed without the 5 % (20 m2 dry floor 0.600 .. 0.800 m3), loss its own account; project cement procurement AT_LEAST 130.82 .. 172.29 bags (was 120.66 .. 162.13); stair bed cement still HELD although your Q-53 answer (C) covers it -> FINISH V7 row. Freelancer: no cement / lintel rows (RULE_DIFFERENCE / UNRESOLVED, not compared).
- Learned (lessons rows PROPOSED): a printed value can sit in a DIMENSION block, not only in text (search both); an end volume inside another element is owned by that element's line once, never by default the minimum bearing.
- Gate 0 found: tests/t485 red on the working branch (merged pool-court WP package still 'pending' in the newest registry) -> fix row first in lane I. Gate 2 (integration). 10 Nov end-to-end BOQ: HIGH RISK (about 10 Gate B packages in 4.5 days, all behind the wrapper item; 9 verified pieces wait).
- Team health: 6 merged, 0 rejected since 08:15; every run closed with a final line; 0 empty runs; 7 new rows (S 3, A 2, I 2). Self-check codemap / t061 / freeze PASS. Queue check: see final RUN_LOG line.

OWNER PACKAGE: none (no engineering item meets standard s.2.7).

NEEDS FIXING (owner only, unchanged since 04:15, not re-notified): the run wrapper (scripts/agent_env.sh on main, line 211) still lets `run` start only the scoreboard and key-map tools; every integration package needs its research/agents_t*/ scripts, and the registry fix row may need one too. Needed: widen `run` to research/agents_t*/*.py, or name another approved path. Also open: Kuwait 1990 spec over the connector limit; repository privacy switch; PyMuPDF decision; PR #3 clean-up.
