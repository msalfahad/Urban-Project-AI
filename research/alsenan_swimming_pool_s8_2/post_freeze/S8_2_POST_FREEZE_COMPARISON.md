# S8.2 post-freeze comparison

S8.2 was frozen at `ae6393b`. The manifest was verified before any reference was opened. S8.2 released 0 m3 and 0 kg, so every reference figure below is a difference. The classes close exactly on it. Nothing was tuned, and the S8.2 package was not written.

## Reference totals

| reference | quantity | value |
|---|---|---|
| FREELANCER_QS | CONCRETE_M3 | 12.348000 |
| FREELANCER_QS | REBAR_KG | 1500.000000 |
| OLD_URBAN_R4 | REBAR_KG | 588.740741 |
| OLD_URBAN_V3B | CONCRETE_M3 | 5.053000 |
| OLD_URBAN_V3B | FINISH_M2 | 15.500000 |
| OLD_URBAN_V3B | PLAIN_CONCRETE_M3 | 0.795500 |
| OLD_URBAN_V3B | REBAR_KG | 585.738272 |
| OLD_URBAN_V3B | WATERPROOFING_M2 | 23.720000 |
| ROUGH_RATIO | REBAR_KG | 611.413000 |

christiannp and U-C4N carry no pool figure.

## Difference by class

| reference | quantity | class | qty |
|---|---|---|---|
| FREELANCER_QS | CONCRETE_M3 | BLOCKED_IN_S8_2 | 4.374226 |
| FREELANCER_QS | CONCRETE_M3 | DEPTH_ASSUMPTION | 4.242106 |
| FREELANCER_QS | CONCRETE_M3 | GEOMETRY | 0.023668 |
| FREELANCER_QS | CONCRETE_M3 | SCOPE | 3.708000 |
| FREELANCER_QS | REBAR_KG | UNSEPARATED | 1500.000000 |
| OLD_URBAN_R4 | REBAR_KG | NOTATION_SCOPE | 236.530864 |
| OLD_URBAN_R4 | REBAR_KG | REFERENCE_FORMULA_MISMATCH | 34.291358 |
| OLD_URBAN_R4 | REBAR_KG | SOURCE_NOT_IN_S8_2 | 317.918519 |
| OLD_URBAN_V3B | CONCRETE_M3 | BLOCKED_IN_S8_2 | 4.374226 |
| OLD_URBAN_V3B | CONCRETE_M3 | GEOMETRY | -2.031460 |
| OLD_URBAN_V3B | CONCRETE_M3 | SOURCE_NOT_IN_S8_2 | 2.710234 |
| OLD_URBAN_V3B | FINISH_M2 | SCOPE | 15.500000 |
| OLD_URBAN_V3B | PLAIN_CONCRETE_M3 | BLOCKED_IN_S8_2 | 1.093556 |
| OLD_URBAN_V3B | PLAIN_CONCRETE_M3 | GEOMETRY | -0.298056 |
| OLD_URBAN_V3B | REBAR_KG | COUNT_CONVENTION | 28.712346 |
| OLD_URBAN_V3B | REBAR_KG | NOTATION_SCOPE | 231.207407 |
| OLD_URBAN_V3B | REBAR_KG | SOURCE_NOT_IN_S8_2 | 325.818519 |
| OLD_URBAN_V3B | WATERPROOFING_M2 | BLOCKED_IN_S8_2 | 10.935564 |
| OLD_URBAN_V3B | WATERPROOFING_M2 | GEOMETRY | -6.587134 |
| OLD_URBAN_V3B | WATERPROOFING_M2 | SOURCE_NOT_IN_S8_2 | 19.371570 |
| ROUGH_RATIO | REBAR_KG | SANITY_RATIO | 611.413000 |

## Equal scope

| item | S8.2 | old V3b | freelancer | state |
|---|---|---|---|---|
| pool base footprint | 10.935564 m2 (exact D-shape, CAD_GEOMETRY + stated 350) | 6.8250 m2 (3.50 x 1.95) | 10.8 m2 | S8.2 ESTABLISHED; references differ by geometry |
| wall plan band | 2.356726 m2 (exact; centre-line 11.783628 m) | 10.10 m x 0.20 | 12 m x 0.20 | S8.2 ESTABLISHED |
| wall height / depth | NOT_ESTABLISHED ('AS PER ARCH') | 1.15 m (raster claim, POOL CANDIDATE binding) | 1.8 m (no source) | BLOCKED in S8.2; references disagree |
| base thickness scope | 40 cm on the deep base only; slope and shallow not dimensioned | 0.40 everywhere | 0.40 everywhere | BLOCKED in S8.2 |
| base reinforcement notation | deep 7Ø14/m (+6Ø14/m transverse), slope 6Ø12/m, shallow 6Ø12/m | 7Ø14/m top and bottom both ways everywhere | unseparated | NOTATION_SCOPE |
| pump room, steps | NOT_SHOWN_IN_SOURCE | none | pump walls 1.08, room floor 2.4, steps 0.228 m3 | SCOPE |
| released quantity | 0 m3, 0 kg (totals unknown) | 5.053 m3, 585.738 kg | 12.348 m3, 1.5 t | no equal-scope released quantity exists |

## Findings

- **F-S8.2-PF-01** (SOURCE_NOT_IN_S8_2, OPEN (new source evidence needed; S8.2 unchanged)): Old V3b's 1.15 m depth is a raster reading '115 pit + 70 step below the +0.15 deck' on ARCH-P08-NW-ELEV of the architectural PDF (sha 281a0c3f8c1cdd8f2a78528513b66d14ba4793e981e2d8059423faf6e6162f99), bound only as a pool candidate. S8.2 read the architectural DXF (P7757.dxf) but not the architectural PDF elevations. Next round: restore that PDF, verify the 115 / 70 annotations bind to the pool (vector text, not raster), then release depth-dependent quantities only if they do.
- **F-S8.2-PF-02** (GEOMETRY, RECORDED (S8.2 geometry stands)): Old V3b measured the base as a 3.50 x 1.95 rectangle (6.825 m2) and the blinding as 2.15 x 3.70; the plan outline is a D-shape of 10.935564 m2. The old figures under-measure the plan by 4.110564 m2.
- **F-S8.2-PF-03** (NOTATION_SCOPE, RECORDED): Old V3b and R4 applied the deep-end callouts to the whole pool; S8.2 binds each of the 26 labels to its own run or dot row (shallow and slope zones carry 6Ø12/m and 6Ø14/m; the shallow wall Ø10/20cm).
- **F-S8.2-PF-04** (REFERENCE_FORMULA_MISMATCH, RECORDED (reference defect)): R4's pool components carry kg that do not equal their own printed formulas (e.g. '28 x 3.500 m x 14^2/162' = 118.567901 kg, row 127.037037 kg).
- **F-S8.2-PF-05** (SCOPE, OPEN (with F-S8.2-PF-01)): The freelancer adds pump-room walls (1.08 m3), a room floor (2.4 m3) and pool steps (0.228 m3). S8.2 found no pump room or steps on any sheet it read; the V3b raster note's '70 step' points at the same unread architectural elevation.
- **F-S8.2-PF-06** (DEPTH_ASSUMPTION, RECORDED): The references disagree on the wall height (V3b 1.15 m, freelancer 1.8 m); neither is a stated dimension in the S8.2 sources.
- **F-S8.2-PF-07** (NO_REFERENCE_QUANTITY, RECORDED): christiannp and U-C4N carry no pool figure.
