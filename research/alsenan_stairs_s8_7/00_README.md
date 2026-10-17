# S8.7 staircases and landings

Round S8_7, baseline `3bdc894`, engine `3bdc894+code:d3ab0bd2d09ddf77`. Frozen before any comparison
(`17_S8_7_FREEZE_MANIFEST.json`, `references_read: []`).

## Physical population

- **ST-A main stair**: one dog-leg stair in two storey runs.
  - A1 runs GF -> 1F on the GF roof sheet: lower flight, winder turn, half-landing at +3.50, upper flight.
  - A2 runs 1F -> 2F on the 1F roof sheet, with the same parts. Its half-landing level is not printed.
- **ST-B lobby steps**: 4 risers from the GF floor (+1.00) down to the +0.30 side lobby, inside the S8.1A bay.
- **ST-C light-well stair**: GF -> 1F. A curved flight runs into a straight flight, then a corner landing, a
  5-riser flight and the top arrival at +5.50.
- **ST-D entrance steps**: 5 risers from +0.15 to the +1.00 porch. They were omitted from S1 / PRE-S8 and lie in
  SP-GBP-01, outside the building.

The five PRE-S8 zones are two staircases plus one repeated ground view. GF-03 and 1F-01 are ST-A. GF-21 and GF-28
are ST-C. GBP-12 is ST-C seen on the ground plan.

## Concrete

| Element | Kind | Plan m2 | Lane | m3 |
|---|---|---|---|---|
| A1-F1 | FLIGHT | 3.935 | SOURCE_CONFLICT | - |
| A1-W1 | WINDER_TURN | 1.5 | BLOCKED_UNQUANTIFIED | - |
| A1-L1 | HALF_LANDING | 1.44 | PROJECT_BASIS_QTO | 0.2304 |
| A1-F2 | FLIGHT | 3.96 | SOURCE_CONFLICT | - |
| A2-F1 | FLIGHT | 3.935 | BLOCKED_UNQUANTIFIED | - |
| A2-W1 | WINDER_TURN | 1.5 | SOURCE_CONFLICT | - |
| A2-L1 | HALF_LANDING | 1.44 | BLOCKED_UNQUANTIFIED | - |
| A2-F2 | FLIGHT | 3.6 | BLOCKED_UNQUANTIFIED | - |
| A2-T1 | TOP_ARRIVAL | 0.12 | PROJECT_BASIS_QTO | 0.0192 |
| B-F1 | STEP_FLIGHT | 1.08 | BLOCKED_UNQUANTIFIED | - |
| C-F1 | FLIGHT (curved part + straight part, no landing between) | 8.003095045 | BLOCKED_UNQUANTIFIED | - |
| C-L1 | CORNER_LANDING | 1.3525 | BLOCKED_UNQUANTIFIED | - |
| C-F2 | FLIGHT | 1.44 | BLOCKED_UNQUANTIFIED | - |
| C-T1 | TOP_ARRIVAL | 1.668642425 | PROJECT_BASIS_QTO | 0.266982788 |
| D-F1 | STEP_FLIGHT | 3.36 | BLOCKED_UNQUANTIFIED | - |

Released: **0.516582788 m3**, on the project basis. It is three flat plates whose outline, level and
thickness all have authority:

- the GF -> 1F half-landing A1-L1, at +3.50;
- the 1F -> 2F arrival strip A2-T1, at +9.70;
- the light-well top arrival C-T1, at +5.50.

Reinforcement released: **59.020862261 kg**, all Ø16. These are the 8Ø16/m bottom bars that the plan callouts
and bar lines carry across those plates, measured by rate density. Every flight, winder turn, unlevelled landing and
step flight is blocked or in source conflict; its sensitivity is in `07_CONCRETE_QTO.csv` and is never released.

The main open points for the engineer (`12_BLOCKED_AND_CONFLICTS.csv`, Q-ST-01 to Q-ST-12):

- **Q-ST-01**: the GF -> 1F riser count (structural 12 + 12, architectural 10 + 11).
- **Q-ST-02**: the waist thickness.
- **Q-ST-03**: the 1F -> 2F half-landing level and the light-well corner landing level.
- **Q-ST-08**: which typical p.16 bars apply to these stairs.

## S7 stair-adjacent top steel

75 strip ends, 75 bar runs, 71.895327413 kg (Ø10),
recomputed run by run from the frozen S7 bar records. All of it stays S7's; S8.7 releases no top bar at those
supports.

## Firewall

PRE-S8 is read through column whitelists only. One exploratory read during the source survey printed the
`CONCRETE_STATES` cell of the PRE-S8 candidate register (an earlier commercial stair figure). It is recorded in the
manifest and nothing reads it.
