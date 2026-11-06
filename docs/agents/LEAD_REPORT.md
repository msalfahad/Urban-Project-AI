# Lead reports to the owner's main chat (newest first, last 3 entries; older in archive/LEAD_REPORT_older.md)


## LEAD REPORT 2026-11-06 12:18 UTC

Drive read OK (no file created in the project folders since 08:00 UTC, no photo task). Training villa: candidate ARCH_TAKEOFF_V3.0.58 / master 1.55.0 (NOT RELEASED), no candidate quantity moved; released V2.9 + route G unchanged (concrete 92.77 vs 111.81 m3, -17.03 %). Results below are Checker-verified pieces, UNWIRED. Development project 2: paused, not measured.
- Columns (B10, m3): engine 19.777 vs freelancer 28.547 = -8.770: HELD -12.129, head joints +2.666 RULE_DIFF, count -0.149, base / depth +0.406, open +0.435. Footing line 67.695 vs 77.631 = -9.936 (HELD F10 / band -10.564, F3 +0.672 ENGINE_RIGHT); 20 Oct -0.37 closed by name. PARTIAL: COUNT 5 / 9 marks; GF C1-C3 marks -> T-566.
- Floor tile (B3, m2): 387.094 vs 409.58 = -5.49 %, closed by room: rules -15.94, HELD band -9.705 (D-48), sizes -0.80, UNRESOLVED +6.90 named; ENGINE_WRONG 2: dressing floor missing 2.970 m2, kitchen dry class on a wet bed -> T-564 fix rows + census. Tile size printed on neither side: adhesive / boxes HELD.
- Plaster (B5, m2): height method version merged: 4 valued dry lines 217.2081 -> HELD 262.018 .. 262.052 (+20.6 %), 11 lines 840.65 .. 895.90; paint 217.2081 unchanged. Wiring row T-563 (Gate B) BLOCKED on wrapper.
- Blockwork (B9, m2): leftover 25.92 split by opening id and parapet run; 32 edge bands carried once in B10 (27 released, 5 HELD). Per-run heights 7.63 HELD in the statement (not yet re-measured).
- Learned: a space with ceiling + skirting and no floor line is a completeness defect (PROPOSED rule, census T-564); re-cut openings when a layer height changes (PROPOSED). ADOPTED: each layer has its own height rule.
- Missing: rebar t, paint, external plaster, earthworks, doors / windows vs freelancer (T-560, T-561, T-567, T-565, T-568); statement V3 (T-562).
- Team health: 6 merged / 0 rejected since 08:15; every run closed with a final line; all agents ran code (self-check PASS); READY 0; 10 TODO (S 3, A 3, I 2 + 2 blocked); queue check 22 actionable, 0 flagged, 0 stall. Gate: lowest open 0 (T-525, T-180).
- 10 Nov (every trade wired): LOW, 4 days, about 11 Gate B packages queued behind the wrapper. 12-13 Nov reconciliation tables: HIGH (9 trades closed, 5 open).
OWNER PACKAGE: no new decision today. Still open: Q-80 (15 cm black block face size; 15 walls 175.9 m2 HELD).
NEEDS FIXING (owner only): wrapper allow-list on main scripts/agent_env.sh (run of research/agents_t*/ scripts) blocks every Gate B package (T-498, T-423 r2, T-525, T-563); notified 04:15 5 Nov, not re-notified. Also: Kuwait 1990 spec copy under 6 MB; repository privacy switch; PyMuPDF decision; PR #3 clean-up.

## LEAD REPORT 2026-11-06 08:15 UTC

Drive read OK (no file created or modified in the project folders since 04:00 UTC 6 Nov, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.58 (NOT RELEASED), no candidate quantity moved; released V2.9 + route G unchanged. 6 merged, all Gate A research (unwired):
- Blockwork (B9): H1 MEASURED on the sections: his parapet h = printed height above finish + 0.50 m slab-edge downstand beam (Checker 0 mm). 68.42 m2 of his parapet masonry is beam concrete -> ENGINE_RIGHT; UNRESOLVED 101.43 -> 25.92 m2 (projections 41.25 m2: no element on any sheet yet). Edge beam ownership ruled to B10 in the register; ids -> T-559.
- Plaster (B5): internal his 1,209.385 vs valued 240.278 m2 closes, residual 0 (HELD 587.718, rule 90.153, lengths ENGINE_RIGHT 53.426, shaft 244.92 with 54.00 named). ENGINE_WRONG (first this round): 11 dry plaster lines at the paint height, 217.2081 -> 261.77..269.33 m2 HELD on the floor build-up (Q-72). Fix: T-556 method version, T-558 wiring row. External his 1,502.84 vs drawn 932.73..938.30 HELD.
- Wall tile (B4): 340.3038 vs 433.83 m2 (-21.56 %), residual 0: 6 HELD rooms -138.39 (bounded), height Q-48 A +43.19, pantry Q-37 A +32.34, openings ENGINE_RIGHT -28.02; like for like 11 rooms +4.24 %.
- Beams (B10-07): 66.321 vs 66.094 m3 (+0.34 %) is a cancellation: ENGINE_RIGHT +12.997, through-support rule -5.028, HELD -7.376, UNRESOLVED -0.365. Checker confirmed the omitted-mark class on B27 only (PARTIAL).
- Statement adapters (6 sections exact) and manifest V5 (glue group 34.89..36.23 bags HELD) merged.
- Learned (3 ADOPTED, 1 PROPOSED): a class comes from geometry, not a hatch; a small net % is not agreement (show gross components); bound HELD rooms and compare like for like before any %; two finish layers equal by construction = defect signal.
- Gates: lowest open gate 0 (t485 behind the wrapper). 10 Nov end-to-end BOQ: LOW (37 verified pieces wait, no Gate B can start). 12-13 Nov tables: 7 trades closed, 5 open (columns / footings, rebar, floor tile, paint, blockwork leftover): HIGH.
- Team health: 6 merged, 0 rejected, 0 blocked since 04:15; every run closed with a final line, 0 empty runs; each piece merged within 1 Checker run. Self-check codemap / t061 / freeze PASS. New rows T-556..T-561 (S 2, A 2, I 2). Queue check: 21 actionable rows, 0 flagged, 0 stall checks.

OWNER PACKAGE:
1. Q-80 (unchanged, filed 00:16, OWNER_QUESTIONS.md Open): face size of the 15 cm black block; 15 walls 175.9 m2 HELD (2,198 / 2,043 / 1,759 blocks by option). Nothing else waits on it.

NEEDS FIXING (owner only, unchanged since 04:15 5 Nov, not re-notified): the run wrapper (scripts/agent_env.sh on main, still at eafbb0f6) lets `run` start only the scoreboard and key-map tools; every integration package and the registry gate fix need research/agents_t*/ scripts. Needed: widen `run` to research/agents_t*/*.py, or name another approved path. This alone decides the 10 Nov milestone. Also open: Kuwait 1990 spec over the connector limit; repository privacy switch; PyMuPDF decision; PR #3 clean-up.

## LEAD REPORT 2026-11-06 04:15 UTC

Drive read OK (no file created or modified in the project folders since 00:00 UTC 6 Nov, no photo task). Training villa: candidate of record ARCH_TAKEOFF_V3.0.58 (NOT RELEASED), no candidate quantity moved; released V2.9 + route G unchanged. 6 merged, all Gate A research (unwired):
- Wet-room floor WP (finishes, B8): engine 85.575710 vs freelancer 72.01 m2 (+13.565710, +18.84 %) closes room by room, residual 0: pantry +13.455 (Q-37 A, rule difference), basin reveal -0.220, printed sizes +0.307 (engine right), tolerance +0.023. His upturn is lm ('m.l'), not m2: 144.61 vs 126.072925 lm = doorways 15.50 HELD + open edges / reveal by rule.
- Blockwork (B9): his 1,260.6895 vs our 467.7925 m2: HELD 587.28 (74 %), rule difference 65.15, engine right 41.05 (rests on his parapet datum H1), UNRESOLVED 101.43 named, engine wrong none. Next: T-550 traces the 101.43 m2 and settles H1.
- 1F lintel glue (B9-02): white AAC host HELD -> 437.88303 .. 451.60893 kg from 8 measured end ceilings; 2F (D-39) and lintel existence (D-45) stay HELD. No freelancer row.
- Stair bed (B7): whole stair AT_LEAST 56.3586 m2 (treads 35.4313 + risers 10.3386 + landings 10.5875) = 1.690758 m3, 16.19 bags.
- Statement builder (12-13 Nov) merged with one class correction: landing MS1-LD 1.500 m2 = engine miss 1.4375 + reference-size difference 0.0625. Manifest V4 merged, stale for T-544 -> V5.
- Learned (4 lessons rows ADOPTED): read the row's own unit label (lm x 1.00 is not m2); a shared pier is measured once; split a reference's own size error from the engine's; partition his total by element family and carry datum dependencies.
- Gates: lowest open gate 0 (t485 behind the wrapper). 10 Nov end-to-end BOQ: LOW (31 verified pieces wait, no Gate B can start). 12-13 Nov reconciliation tables: 4 trades closed, 6 open (beams, wall tile, plaster, floor tile, columns / footings, blockwork leftover): MEDIUM-HIGH.
- Team health: 6 merged, 0 rejected, 0 blocked since 00:20; every run closed with a final line, 0 empty runs, each piece merged within 1 Checker run. Self-check codemap / t061 / freeze PASS. New rows T-550..T-555 (S 2, A 2, I 2). Queue check: 21 actionable rows, 0 flagged, 0 stall checks.

OWNER PACKAGE:
1. Q-80 (unchanged, filed 00:16, OWNER_QUESTIONS.md Open): face size of the 15 cm black block; 15 walls 175.9 m2 HELD (2,198 / 2,043 / 1,759 blocks by option). Nothing else waits on it.

NEEDS FIXING (owner only, unchanged since 04:15 5 Nov, not re-notified): the run wrapper (scripts/agent_env.sh on main, still at eafbb0f6) lets `run` start only the scoreboard and key-map tools; every integration package and the registry gate fix need research/agents_t*/ scripts. Needed: widen `run` to research/agents_t*/*.py, or name another approved path. This alone decides the 10 Nov milestone. Also open: Kuwait 1990 spec over the connector limit; repository privacy switch; PyMuPDF decision; PR #3 clean-up.
