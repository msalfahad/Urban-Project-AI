# Pool, staircases and domes: engineering reconciliation (Alsenan; owner teaching case 2026-10-22)

Owner directive 2026-10-22 (main chat): understand the physical construction, read architecture and structure together,
reconstruct each element, never adjust to the freelancer, generalise into rules and regression tests. This file is the
WORKING reconciliation: the main chat seeded it from the freelancer's own cells and the team's merged ledgers; T-183
(pool), T-184 (staircases), T-185 (domes) complete it; the Checker re-measures every material row (T-180 slot).
Statuses per WORKFLOW_CONTROLS section 5. Released default unchanged; nothing here is released.

## 1. Freelancer, cell by cell (FREELANCER_RAW_ROWS.json, RC workbook; numbers are his, not truth)

| Reference line | His component | His formula | His m3 |
|---|---|---|---|
| Stair + dome 21.833 | Main stair flights "الدرج + البلاطة" | 4 x 1.2 x 5.3 x 0.28 | 7.123 |
| | Main stair landings | 3 x 1.2 x 1.4 x 0.20 | 1.008 |
| | "سلم 2" (second stair) | 1.2 x 16.4 x 0.28 | 5.510 |
| | Entrance stair "سلم المدخل" | 1.8 x 2.8 x 0.28 | 1.411 |
| | Domes "القبه" | 3 x 22.6 m2 x 0.10 | 6.780 |
| Pool 12.348 | Pool floor | 10.8 m2 x 0.40 | 4.320 |
| | Pool walls | 12 m x 1.8 x 0.20 | 4.320 |
| | Pump-room walls "حوائط المضخة" | 3 m x 1.8 x 0.20 | 1.080 |
| | Pool steps "درج الحمام" | 0.3 x 2 x 0.38 | 0.228 |
| | Pump-room floor "ارضيه الغرفه" | 3 x 2 x 0.40 | 2.400 |

Observations (to be investigated, not conclusions): his stair figures use one 0.28 m "slab + step" thickness for every stair
and a 5.3 m flight length that T-111 found on no drawing; "سلم 2" is one 16.4 m run, not flights; the pool total includes a
PUMP ROOM (3.48 m3) whose existence and structure in the drawings is not yet established; his pool wall height 1.8 m
differs from the architectural depth (rim +0.30, floor -0.85: 1.15 m water depth, owner Q-26 A).

## 2. Team evidence so far (merged, checker-verified where stated)

| Element | Evidence | Quantity | Status |
|---|---|---|---|
| ST-01 main dog-leg stair (GF->1F->2F) | T-111 ledger, section A-A sheet 10, checker re-measure 0.0 % on the 1F flight | 4.920 m3 owner basis / 4.746 drawn | DRAWING-CONFIRMED / VERIFIED (flight re-measured); winder slab and well strip HELD |
| Round stair (reception), GF -> 1F | T-111, Q-50 A conditional: 28 risers to +5.50, no section | straight parts 1.561 m3 CALCULATED; curved part HELD (cand. steps 0.330) | partly HELD |
| Entrance stair | T-111 | 0.357 m3 | HELD on a missing drawing (no waist printed) |
| Main stair steel | T-166 by bar population | 294.73 / 307.01 / 337.71 kg (Q-71 range) | HELD range |
| Pool | T-049 scope + CONCRETE_LEDGER_V2 records: wall plan 2.357 m2, floor plan 10.936 m2, floor 0.40 m printed (p.7), depth per Q-26 A | not yet reconstructed (indicative only: floor 10.936 x 0.40 = 4.374 m3 + walls 2.357 x wall height, height basis to establish) | HELD |
| Pool steel | T-166: R1 888.90 .. 927.54 kg, R2 615.34 .. 639.45 kg | HELD (p.7 two-zone detail vs Q-26 A flat floor) | HELD |
| Domes | ST p.7 dome detail (442 / 190 / 10), owner Q-27 A: 3 domes (third without detail), Q-29: client wants no concrete domes (open skylights); ring beams T-160 | approved design: not reconstructed; client-change scenario: 0 dome shell | scenario split required (section 4) |

## 3. Engine side

Released baseline A: STR.CONC.STAIR + STR.CONC.DOME = 12.01 m3; STR.CONC.POOL = 3.50 m3. Their line-level composition
(which stairs, which domes, which pool parts) is established by T-180 / T-183 / T-184 from BOQ_LINES.csv of the pinned
baseline manifest, never from this file.

## 4. Scenarios (owner 2026-10-22: never silently remove the dome from the approved-design baseline)

| Scenario | Domes | Status |
|---|---|---|
| S0 APPROVED DESIGN (drawings as issued) | 3 concrete domes (2 x detailed on ST p.7, 1 without detail: HELD) + rings + rebar | baseline; quantities to reconstruct |
| S1 CLIENT-REQUESTED CHANGE (owner Q-29, 2026-10-19) | no dome shell; each dome position an open skylight area; ring / edge beams, skylight glazing or opening edge, waterproofing upturns: scope to establish | PROPOSED: no consultant revision seen on Drive |
| S2 CONSULTANT-REVISED DESIGN | per revised drawings | UNKNOWN until revised drawings exist |

The BOQ shows S0 and S1 side by side; S1 is not released as the approved design until S2 confirms it.

## 5. Reconciliation table (filled by T-183 / T-184 / T-185; Checker columns by T-180)

| Component | Drawing reference | Own calculation | Engine m3 | Freelancer m3 | Difference and cause | Status | Checker |
|---|---|---|---|---|---|---|---|
| ST-01 flights | | | | 7.123 | | | |
| ST-01 landings | | | | 1.008 | | | |
| ST-02 (stair beside the lift; is it the round stair?) | | | | 5.510 | | | |
| Entrance stair | | | | 1.411 | | | |
| Domes S0 | | | | 6.780 | | | |
| Domes S1 | | 0 shell | | n/a | | | |
| Pool floor (RC base) | ST p.7 '40'; S-BW 7C6 outer D 3.50 x 1.75 + r 1.75; Q-26 A flat | 10.936 m2 x 0.40 = 4.374 (wall foot included) | 1.511 (6.045 m2 x convention 0.25) | 4.320 | his -0.054: typed 10.8 m2 vs 10.936 (residual unexplained); engine -2.863: half D lost + 0.25 not printed | DRAWING-CONFIRMED (T-183) | T-180: VERIFIED 4.374 |
| Pool walls | S-BW 7C6 / 7C5 band 2.357 m2 (all round, curved half included); 1.15 above base top (Q-26 A; NW cut 115) | 2.357 x 1.15 = 2.710 | 1.984 (straight strip 1.24 m2 x convention 1.60) | 4.320 | his +1.610: length 12 vs 11.784 (+0.050), base thickness counted again in 1.80 (+0.960), 0.25 m not drawn (+0.600); engine -0.726: curved half lost, height convention | DRAWING-CONFIRMED (T-183) | T-180: own 2.710 |
| Pool steps / benches | GF plan pool interior, p.7 (sloped profile excluded by Q-26 A) | none drawn | none | 0.228 | his scope, not drawn | NOT DRAWN (consultant C5: access) | |
| Pump room walls + floor (exists?) | S-BW (pool D + lift box only), GF plan, both DXF texts; owner Q-19 / Q-22 A | does not exist on the drawings | none | 3.480 | his scope, not drawn | NOT DRAWN | |
| Blinding under pool (separate line) | p.7 '10cm PLAIN CONCRETE' under 5 cm membrane + 5 cm screed; projection not dimensioned | >= 12.217 m2 x 0.10 = 1.222 (lower bound) | not separate | (not in his pool) | projection HELD (footing p.13 10 cm not extended: +0.134) | HELD (lower bound shown) | |

T-183 (worker 1, 2026-10-22 11:05 UTC, READY 8beaa6a): pool RC total 7.084 m3 (base 4.374 + walls 2.710), engine A 3.495, freelancer 12.348 (+5.264 closes to 0.000); formwork 32.101 m2, membrane 30.307 m2 net, water-face 21.309 m2; rebar R1 847.00 .. 885.64 / R2 586.25 .. 610.35 kg HELD (designer); T-166 hoops corrected (-41.90 / -29.09 kg). Full ledger: research/agents_t183/T-183_POOL_RC.md on agents/task-T-183.

## 6. Checker result so far (T-180, verifier run 2026-10-22 09:52-10:24; SCOREBOARD.md 'CONCRETE REFERENCE RECONCILIATION')

Pool reconstructed from the drawing: floor 10.935 m2 x printed 0.40 = 4.374 m3; walls 2.357 m2 ring plan x 1.15 (floor top -0.85 to rim +0.30) = 2.710 m3; total 7.084 m3, steps UNKNOWN. Engine A 3.495 (-3.589: curved half of the wall ring missed; conventions 0.25 floor / 1.60 walls / 6.045 m2 instead of the printed 0.40, 1.15 and 10.935 m2). Freelancer 12.348 (+5.264: pump room 3.480 m3 not drawn, wall height 1.80, steps 0.228). Verified concrete lines 1 / 8. T-183 builds the full component split (blinding, base, walls at the junction, steps, rebar, formwork, joints, waterproofing, finishes) on this basis; main chat spot-check 2026-10-22 10:55: arithmetic of every term re-done, consistent.
