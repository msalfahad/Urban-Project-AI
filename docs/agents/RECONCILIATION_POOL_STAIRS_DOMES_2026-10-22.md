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
| ST-01 flights (dog-leg BESIDE THE LIFT, GF -> 1F -> 2F, ends at 2F: ST p.6 slab over the shaft, section A-A) | ARCH GF / 1F / 2F, section A-A (Q-46 A 12 + 12), ST p.4 / p.5 'T 16' | 4 flights: steps + waist 4.126 - Q-62 0.090 = 4.036 (GF->1F 1.918, 1F->2F 2.118) | 2.786 (GF->1F only, turn by convention; 1F->2F flights folded away: D-T184-1, -2.598 incl. landing) | 7.123 | his +3.088 = length 4 x 5.3 = 21.2 m vs drawn sloped 14.428 m (+2.275; 5.3 = 1.95 floor landing + 3.30 flight on the 1F / 2F chain) + thickness 0.28 vs 0.233 drawn equivalent (+0.812); closes 0.000 | DRAWING-CONFIRMED (T-184); turn 0.120..0.130 + turn slab 0.230..0.250, closing riser, head clash 0.115, 'B3 (With Stair)' HELD | T-184 MERGED 924c2bd (Checker 15:00, own DXF re-measure): flight MS2-L 1.059 m3 = ledger (0.0 %); engine storey loss D-T184-1 -2.598 m3 confirmed in code; other flights, turn and landings NOT re-measured: line PARTIALLY VERIFIED (1 of 4 flights) [Lead 16:20] |
| ST-01 landings | T-111 DXF 1.20 x 1.20 + 2.50 x 1.20, T 16; floor arrivals 2 x 1.95 x 2.50 = FLOOR SLAB (not stair) | 4.44 m2 x 0.16 = 0.710 | (inside the 2.786) | 1.008 | his +0.298 = area 5.04 vs 4.44 m2 (+0.120) + thickness 0.20 vs T 16 (+0.178); closes 0.000 | DRAWING-CONFIRMED | |
| ST-02 = ROUND reception stair (NOT beside the lift; GF -> 1F, ends at 1F) | ARCH GF / 1F, DXF, ST p.4 'T 16'; Q-50 A cond | straight + corner landing + short 1.620 - Q-62 0.059 = 1.561 CALCULATED | 0.901 (8.37 m2 winder region on the ground-beam plan only) | 5.510 | his 1.2 x 16.4 x 0.28: no drawn length reaches 16.4 m (walking line 9.94 sloped, outer string 10.86): 5.54 m UNEXPLAINED; T 16 printed, not 0.28 | CALCULATED; curved treads (cand. 0.330) + helicoid soffit (not drawn) + CA junction HELD | T-184 MERGED 924c2bd (Checker 15:00, own DXF re-measure): straight flight RS-S 0.972 m3 = ledger (0.0 %); curved part, corner landing and short flight NOT re-measured: PARTIALLY VERIFIED [Lead 16:20] |
| ST-01b lobby flight in the ST-01 shaft (+0.30 -> +1.00) | ARCH GF 4 risers, section A-A | 0.126 (steps) | none | no row | hand found | waist HELD | |
| Domes S0 | | | | 6.780 | | | |
| Domes S1 | | 0 shell | | n/a | | | |
| Pool floor (RC base) | ST p.7 '40'; S-BW 7C6 outer D 3.50 x 1.75 + r 1.75; Q-26 A flat | 10.936 m2 x 0.40 = 4.374 (wall foot included) | 1.511 (6.045 m2 x convention 0.25) | 4.320 | his -0.054: typed 10.8 m2 vs 10.936 (residual unexplained); engine -2.863: half D lost + 0.25 not printed | DRAWING-CONFIRMED (T-183) | T-180: VERIFIED 4.374 |
| Pool walls (r2) | S-BW 7C6 / 7C5 band 2.357 m2 (all round, curved half included); 1.20 = rim +0.30 to the STRUCTURE line -0.90 (NW cut: finished floor -0.85 over a 50 mm build-up; p.7 'AS PER ARCH' rim to base top); 1.15 = finished depth (Q-26 A), kept beside it; upstand 0.15 above the +0.15 deck along 8.998 m (inside the 1.20, no extra m3) | 2.357 x 1.20 = 2.828 | 1.984 (straight strip 1.24 m2 x convention 1.60) | 4.320 | his +1.492: height on his 12 m 1.80 vs 1.20 (+1.440 = base thickness counted again +0.960 + 0.20 above the drawn rim +0.480), length 12 vs 11.784 (+0.052); engine -0.844: curved half lost -1.340, height convention 1.60 vs 1.20 +0.496 | DRAWING-CONFIRMED (T-183 r2) | T-180 / T-183 Checker 12:05: own 2.828 (D-T183-1) |
| Pool steps / benches | GF plan pool interior, p.7 (sloped profile excluded by Q-26 A) | none drawn | none | 0.228 | his scope, not drawn | NOT DRAWN (consultant C5: access) | |
| Pump room walls + floor (exists?) | S-BW (pool D + lift box only), GF plan, both DXF texts; owner Q-19 / Q-22 A | does not exist on the drawings | none | 3.480 | his scope, not drawn | NOT DRAWN | |
| Blinding under pool (separate line) | p.7 '10cm PLAIN CONCRETE' under 5 cm membrane + 5 cm screed; projection not dimensioned | >= 12.217 m2 x 0.10 = 1.222 (lower bound) | not separate | (not in his pool) | projection HELD (footing p.13 10 cm not extended: +0.134) | HELD (lower bound shown) | |

T-183 r2 (worker 1, 2026-10-22 14:55 UTC, READY c046645): pool RC total 7.202 m3 (base 4.374 + walls 2.828 at 1.20 to the structure line), engine A 3.495 (-3.707, -51.5 %), freelancer 12.348 (+5.146, +71.5 %, closes to 0.000); formwork 33.280 m2, membrane 30.932 m2 net, screed 1.591 m3, visible water-face finish 21.309 m2 (walls at the 1.15 finished depth; structural water face 13.283 m2), floor build-up 0.429 m3, wall top 2.357 m2, upstand exposed face 1.350 m2; rebar R1 860.97 .. 894.43 / R2 596.17 .. 616.66 kg HELD (designer); formation -1.50.
Superseded r1: T-183 (worker 1, 2026-10-22 11:05 UTC, READY 8beaa6a): pool RC total 7.084 m3 (base 4.374 + walls 2.710), engine A 3.495, freelancer 12.348 (+5.264 closes to 0.000); formwork 32.101 m2, membrane 30.307 m2 net, water-face 21.309 m2; rebar R1 847.00 .. 885.64 / R2 586.25 .. 610.35 kg HELD (designer); T-166 hoops corrected (-41.90 / -29.09 kg). Full ledger: research/agents_t183/T-183_POOL_RC.md on agents/task-T-183.

## 6. Checker result so far (T-180, verifier run 2026-10-22 09:52-10:24; SCOREBOARD.md 'CONCRETE REFERENCE RECONCILIATION')

Pool reconstructed from the drawing: floor 10.935 m2 x printed 0.40 = 4.374 m3; walls 2.357 m2 ring plan x 1.15 (floor top -0.85 to rim +0.30) = 2.710 m3; total 7.084 m3, steps UNKNOWN. Engine A 3.495 (-3.589: curved half of the wall ring missed; conventions 0.25 floor / 1.60 walls / 6.045 m2 instead of the printed 0.40, 1.15 and 10.935 m2). Freelancer 12.348 (+5.264: pump room 3.480 m3 not drawn, wall height 1.80, steps 0.228). Verified concrete lines 1 / 8. T-183 builds the full component split (blinding, base, walls at the junction, steps, rebar, formwork, joints, waterproofing, finishes) on this basis; main chat spot-check 2026-10-22 10:55: arithmetic of every term re-done, consistent.

T-184 (worker 1, 2026-10-22, READY on agents/task-T-184): every stair inventoried with continuity; 'the stair beside the lift' IS the dog-leg ST-01 (shares the lift's west wall on every plan); the round reception stair is ST-02. Stairs own 6.790 m3 measured + held parts vs freelancer 15.053 vs engine A 4.635 (engine 12.007 = stairs 4.635 + 2 domes 7.372). ST7757 p.16 is a typical N.T.S. section whose levels fit no Alsenan stair (reinforcement arrangement only). Full ledger: research/agents_t184/T-184_STAIRCASES.md.

## 7. Owner review 2026-10-22 16:30 (main chat): stair difference to the m3, verification scope, pool intersection

**Stairs, engine (released A) 4.635 vs own 6.790 = +2.155 m3; the missing ST-01 storey is 2.598 m3; the 0.443 m3 between them,
stair by stair (research/agents_t184/T-184_STAIRCASES.md sections 1 and 5 on the working branch, recomputed by the main chat):**

| Stair | Engine | Own (measured, held parts excluded) | Own - engine | Cause |
|---|---|---|---|---|
| ST-01 GF -> 1F | 2.786 | 2.148 | -0.638 | engine CONVENTIONS where the drawing prints otherwise or nothing: waist 0.175 (printed T 16), riser 0.165, and the winder turn measured by convention (own: HELD 0.35 .. 0.38 with its slab) |
| ST-01 1F -> 2F | 0 | 2.598 | +2.598 | D-T184-1: the storey folded away as "drawn again on" (levels ignored); silent omission |
| ST-01b lobby flight | 0 | 0.126 | +0.126 | small omission (steps only; waist HELD) |
| ST-02 round stair | 0.901 | 1.561 | +0.660 | engine reads only an 8.37 m2 winder region; own = straight flight + corner landing + short flight; curved treads HELD |
| ST-03 entrance stair | 0.948 | 0.357 | -0.591 | engine adds a 0.175 m convention waist no drawing prints (own: waist HELD) |
| Total | 4.635 | 6.790 | +2.155 | 2.598 - 0.443; 0.443 = 0.638 + 0.591 - 0.660 - 0.126 (closes to 0.000) |

The two totals do NOT have the same scope: the engine's 4.635 contains conventional values (ST-01 winder turn, ST-01 and
ST-03 convention waists) for parts the own ledger HOLDS, so "+2.155" is not the size of the engine error. No landing is
counted twice: the floor-arrival landings (2 x 1.95 x 2.50) are floor slab in both, the intermediate landings (1.44 +
3.00 m2 at T 16) are stair in both. Same calculation revision on both sides (released manifest A; T-184 ledger 9fbedc4,
merged 924c2bd).

**Verification status, stairs (never "VERIFIED" for the system):**

| Scope | m3 | Status |
|---|---|---|
| ST-01 MS2-L flight (1F -> 2F lower), Checker re-measure 15:00 | 1.059 | VERIFIED (sample) |
| ST-02 RS-S straight flight, Checker re-measure 15:00 | 0.972 | VERIFIED (sample) |
| Rest of the measured scope (other flights, landings, ST-01b steps, ST-03 steps) | 4.759 | DRAWING-CONFIRMED / CALCULATED, not independently re-measured |
| ST-01 winder turn + its slab, closing riser, head clash 0.115, 'B3 (With Stair)' beams | 0.35 .. 0.38 + open items | HELD |
| ST-02 12 curved treads (candidate 0.330), helicoid soffit (not drawn), CA junction 0 .. 0.09 | not quantified | HELD (Q-50 / Q-51) |
| ST-01b and ST-03 waists | not printed | HELD |
| Staircase system | 6.790 measured + held | PARTIALLY VERIFIED: 2 of the measured flights (2.031 m3, 30 %) re-measured; the system is not VERIFIED while the held geometry is open |

**Pool, owner questions answered by the Checker's 16:14 re-read (T-183 r2 MERGED 6380294), arithmetic re-done by the main chat:**
- 1.20 m wall height = rim (wall cap / water line) to the structural base top (structure line rim - 1.200 on the NW cut);
  finished floor rim - 1.150 = the printed 115. VERIFIED.
- The 0.15 m upstand is the top of the same wall (0.15 above the deck finish, 0.20 above the deck structure), INSIDE the
  1.20 m: no extra concrete; only its exposed outer face 8.998 m x 0.15 = 1.350 m2 is a separate quantity (finish / formwork).
- Wall / base intersection counted once: the base is the full outer D outline 3.50 x 1.75 + pi x 1.75^2 / 2 = 10.936 m2
  x 0.40 = 4.374 m3 (it includes the ground under the walls); the walls are the ring (outer 10.936 - water 3.10 x 1.55 +
  pi x 1.55^2 / 2 = 8.579) = 2.357 m2 standing on the base top, x 1.20 = 2.828 m3. No volume is in both.
- Pool concrete 7.202 m3 VERIFIED; the pool LINE stays PARTIALLY VERIFIED: reinforcement R1 860.97 .. 894.43 / R2 596.17 ..
  616.66 kg HELD (designer), joints / waterstop, membrane termination and finishes UNKNOWN.
