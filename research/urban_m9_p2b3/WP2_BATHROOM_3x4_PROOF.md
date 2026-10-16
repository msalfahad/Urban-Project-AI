# The 3.00 x 4.00 m bathroom, proven strip by strip (WP-2)

The owner's scenario, calculated by hand before any engine result was read, then checked three ways: by an
independent reference calculator that imports nothing from the engine (`tests/m9_p2b3/proof_reference.py`, whole
millimetres), by the engine on the synthetic geometry (`proof_engine.wp_area`), and by the engine through the whole
drawing route on a DXF plan with two such bathrooms (`proof_drawings.bathrooms`, PD-1). Proof case `WP-B` in
`tests/m9_p2b3/proof_cases.py`; tests `test_p2b3_waterproofing_proofs.py`, `test_p2b3_integration.py`.

## 1. Scenario and the values it uses

| Input | Value | Source |
|---|---|---|
| Room (inner faces) | 4.00 m (x) x 3.00 m (y), floor 12.00 m2 | the scenario |
| Door | 1.00 m in the south wall, x 1.50 - 2.50, to a dry corridor | the scenario |
| Columns, drains, pipes | none | the scenario |
| Roll | 1.00 x 10.00 m | UP-WP-001 (owner approved) |
| Lap at every joint | 0.10 m | UP-WP-002 (owner approved) |
| Upturn | 0.20 m on the eligible wall boundary | UP-WP-003 (owner approved) |
| Doorway continuation | door width x wall depth, laps 0.10 m onto the floor | UP-WP-DOOR-001 (owner approved) |
| Doorway threshold detail | **not specified** - not assumed | open owner decision N-1 |
| Wall depth at the door | 0.20 m | **assumption of this proof** (the scenario gives none; used only for the continuation piece) |

## 2. The proven geometric subtotal

| Quantity | Calculation | Value |
|---|---|---|
| A - net floor | 4.00 x 3.00 | **12.00 m2** |
| Perimeter | 2 x (4.00 + 3.00) | 14.00 m |
| Eligible upturn length | 14.00 - 1.00 (the doorway is not a wall) | **13.00 m** (one open run, jamb to jamb) |
| Wall upturn | 13.00 x 0.20 | **2.60 m2** |
| Floor + upturn | 12.00 + 2.60 | **14.60 m2** - a geometric subtotal, not a material requirement |
| Doorway continuation | 1.00 x 0.20 | 0.20 m2 |
| Proven subtotal incl. continuation | 14.60 + 0.20 | 14.80 m2 |

## 3. Floor strips - why five, and which direction

Strips are cut across the full roll width (1.00 m) and lap 0.10 m side by side, so each strip after the first adds
0.90 m. The strip count across a width D is the smallest n with 1.00 + (n - 1) x 0.90 >= D.

| Direction | Strip length | Across | Strips | Check | Last strip |
|---|---|---|---|---|---|
| ALONG_Y (selected) | 3.00 m | 4.00 m | 5 | 1.00 + 3 x 0.90 = 3.70 < 4.00; 1.00 + 4 x 0.90 = 4.60 >= 4.00 | 4.00 - 4 x 0.90 = 0.40 m |
| ALONG_X | 4.00 m | 3.00 m | 4 | **three strips cover only 1.00 + 0.90 + 0.90 = 2.80 < 3.00** | 3.00 - 3 x 0.90 = 0.30 m |

## 4. The cut inventory, piece by piece (selected layout ALONG_Y)

| Piece | Cut from | Cut size | Laid where | Laps |
|---|---|---|---|---|
| S1 | roll 1, 0.00 - 3.00 m | 1.00 x 3.00 | x 0.00 - 1.00 | - |
| S2 | roll 1, 3.00 - 6.00 m | 1.00 x 3.00 | x 0.90 - 1.90 | 0.10 x 3.00 over S1 |
| S3 | roll 1, 6.00 - 9.00 m | 1.00 x 3.00 | x 1.80 - 2.80 | 0.10 x 3.00 over S2 |
| S4 | roll 2, 0.00 - 3.00 m | 1.00 x 3.00 | x 2.70 - 3.70 | 0.10 x 3.00 over S3 |
| S5 | roll 2, 3.00 - 6.00 m | 1.00 x 3.00, cut lengthwise to 0.40 | x 3.60 - 4.00 | 0.10 x 3.00 over S4 |
| L1, L2 | the 0.60 x 3.00 trim of S5 | two lanes 0.30 x 3.00 (0.60 / 0.30 = 2, no residue) | - | - |
| DW | L1 | 1.00 x 0.30 (0.20 wall depth + 0.10 lap) | the doorway floor x 1.50 - 2.50 | 1.00 x 0.10 onto the floor |
| G | roll 2, 6.00 - 8.80 m | 1.00 x 2.80 band segment | - | - |
| L3, L4, L5 | G | three lanes 0.30 x 2.80 + 0.10 x 2.80 residue | - | - |
| B1 | L2 | 0.30 x 3.00 | band, run 0.00 - 3.00 m | 0.10 onto the floor |
| B2 | L1 remainder | 0.30 x 2.00 | run 2.90 - 4.90 m | 0.10 over B1 + 0.10 onto the floor |
| B3 | L3 | 0.30 x 2.80 | run 4.80 - 7.60 m | 0.10 over B2 + floor |
| B4 | L4 | 0.30 x 2.80 | run 7.50 - 10.30 m | 0.10 over B3 + floor |
| B5 | L5 | 0.30 x 2.80 | run 10.20 - 13.00 m | 0.10 over B4 + floor |

The band run starts at the east jamb (x 2.50) and goes round the room to the west jamb (x 1.50): corners at 1.50,
4.50, 8.50 and 11.50 m along the run; the joints (2.90 - 3.00, 4.80 - 4.90, 7.50 - 7.60, 10.20 - 10.30 m) fall on no
corner.

Why 2.80 m for the band segment: after the offcut lanes (B1 covers 3.00, B2 covers 2.00 - 0.10 = 1.90) 8.10 m of the
run is left; three lanes each lapping 0.10 need 3 x (L - 0.10) >= 8.10, so L >= 2.80 m. A 2.79 m segment covers
3 x 2.69 = 8.07 m < 8.10 m. V2.4 sized it 8.10 / 3 + 2 x 0.10 = 2.90 m (two laps per lane instead of one: defect
D-V25-01).

## 5. Laps, installed membrane (B), consumption, waste, rolls

| Item | Calculation | m2 |
|---|---|---|
| Side laps (floor) | 4 seams x 3.00 m x 0.10 m | 1.20 |
| Band lap onto the floor | 13.00 m x 0.10 m | 1.30 |
| Band joints | 4 x 0.30 m x 0.10 m | 0.12 |
| Doorway piece lap | 1.00 m x 0.10 m | 0.10 |
| **Laps total** | | **2.72** |
| **B installed** | 12.00 + 2.60 + 0.20 + 2.72 (= floor 13.20 + doorway 0.30 + band 13.40 x 0.30 = 4.02) | **17.52** |
| **Consumed** | cuts 5 x 3.00 + 2.80 = 17.80 m x 1.00 m | **17.80** |
| **Cutting waste** | 17.80 - 17.52 (the 0.10 x 2.80 m residue of G) | **0.28** |
| Untouched roll remainders | roll 1 1.00 m + roll 2 1.20 m (full width: stock, not waste) | 2.20 |
| **Rolls** | 17.80 m > 10.00 m -> at least 2; roll 1 = S1 S2 S3 (9.00 m), roll 2 = S4 S5 G (8.80 m) | **2** |

Both owner figures are reproduced: **17.80 m2 consumed and 2 rolls** (hand = reference = engine on the synthetic
geometry = engine through the drawing route on PD-1).

The other direction (ALONG_X): 4 strips of 4.00 m fill rolls 1 and 2 to 8.00 m each; a single band segment of 2.14 m
(3 x 2.04 = 6.12 >= 6.10) does not fit their 2.00 m remainders and would open a third roll. Filling roll 1's remainder
with a 2.00 m segment (3 lanes, 5.70 m) and finishing with a 0.40 m segment in roll 2 keeps 2 rolls at 18.40 m2 and 6
band joints. Selection (UP-WP-LAY-001): both 2 rolls; seams 4 + 4 = 8 (ALONG_Y) against 3 + 6 = 9 -> ALONG_Y.

## 6. Usable offcuts and installation constraints

| Offcut | Size | Use |
|---|---|---|
| S5 trim | 0.60 x 3.00 m | two band lanes L1, L2 (used: DW, B1, B2) |
| Band segment residue | 0.10 x 2.80 m | scrap (narrower than a 0.30 m lane) |
| Roll remainders | 1.00 x 1.00 m, 1.00 x 1.20 m | stock: a full-width piece for another room of the same system (WP-H) |

Checked for every case (`test_every_cutting_plan_is_installable`): each cut fits a roll; a roll's cuts never exceed
10.00 m; every lapped band piece covers something past its lap; only whole 0.30 m lanes are used as band; the material
balances. Not validated (no source): lap shingling towards the drain (no fall plan), a minimum practical piece length
(no system data sheet - owner question N-7).

## 7. What the material requirement does not include - proven subtotal versus provisional final requirement

| Item | State | Quantity |
|---|---|---|
| A, upturn, continuation (14.80 m2) | **PROVEN** (measured geometry x approved standards) | 14.80 m2 |
| Installed membrane B, consumption, rolls | **PROVISIONAL**: computed from a valid cutting plan, but details below are open | 17.52 / 17.80 m2, 2 rolls |
| Doorway threshold transition | **UNRESOLVED** - no detail; not assumed | alternatives: upturn across the threshold 1.00 x 0.20 = 0.20 m2; continuation terminated 0 m2 + 1.00 m termination; jamb returns 2 x 0.20 x 0.20 = 0.08 m2 + 1.00 m termination -> range 0.00 - 0.20 m2 |
| Corner treatment | WITHHELD - no detail, no size | 4 internal corners |
| Penetrations | NOT_SHOWN - none drawn (the count is not established, never 0) | - |
| Membrane system | not named: the Urban standard roll | roll count PROVISIONAL |

Does the open doorway detail change the roll count? With the threshold upturned the band becomes one closed 14.00 m
loop: pieces 3.00 + 2.00 lapped (4.80 m), segment 3 x (L - 0.10) >= 9.20 -> 3.17 m; roll 2 = 3.00 + 3.00 + 3.17 =
9.17 m -> **still 2 rolls** (V2.5 reports it as `roll_sensitivity` on every area). The corner and penetration
treatments cannot be included: they have no size until a detail gives one.

**Final material requirement: PROVISIONAL (`PROVISIONAL_DETAILS_OPEN`)** - 17.52 m2 installed, 17.80 m2 consumed, 2
rolls, plus the doorway transition (0.00 - 0.20 m2), the corner treatment and the membrane system to be decided.

## 8. Engine comparison

| Quantity | Hand | Reference | V2.5 | V2.4 (frozen) |
|---|---|---|---|---|
| A / eligible / upturn | 12.00 / 13.00 / 2.60 | same | same | same |
| Strips (direction) | 5 (ALONG_Y), last 0.40 | same | same | same |
| Band pieces (m) | 2.00, 2.80, 2.80, 2.80, 3.00 | same | same | 2.00, 2.60, 2.90, 2.90, 3.00 |
| Laps / B | 2.72 / 17.52 | same | same | same |
| Consumed / waste | 17.80 / 0.28 | same | same | 17.90 / 0.38 (FAILED_VALIDATION) |
| Rolls | 2 | 2 | 2 | 2 |
| ALONG_X alternative | 2 rolls, 9 seams, 18.40 | 2 / 9 / 18.40 | same | 3 rolls, 18.24 (FAILED_VALIDATION) |
| Roll count with the doorway upturned | 2 | - | 2 | not reported |

Row-level tables for every case: `CALCULATION_SHEETS.md`, `EXPECTED_VS_ACTUAL.md / .csv`; diagrams
`diagrams/WP-B_layout.svg`, `diagrams/WP-B_rolls.svg`.
