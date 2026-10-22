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
| Pool floor | | | | 4.320 | | | |
| Pool walls | | | | 4.320 | | | |
| Pool steps / benches | | | | 0.228 | | | |
| Pump room walls + floor (exists?) | | | | 3.480 | | | |
| Blinding under pool (separate line) | | | | (not in his pool) | | | |
