# T-680 stair-shaft plaster / paint round 2 (lane A, research, unwired)

Worker 2, 2026-11-10. Candidate ARCH_TAKEOFF_V3.0.65 (T-671 line index). Nothing wired or released; V2.9 + route G
unchanged; no engine, rule or knowledge version file touched. Rules R-T680-1 .. -3 in `t680_rules.py`; builder
`t680_alsenan.py` (`--check`); outputs `out/T680_SHAFT_ROUND2.{json,md}`; tests `tests/t680_shaft_round2`.
Inputs: the merged T-173 shaft model (shaft-local, no coordinates), T-201 HEADS (DWF vector heads, Checker-verified
MERGED 5dade783), T-676 census (MERGED cffefa0c). No new drawing read was needed: every term used is merged evidence.

## Physical element

Shaft ST-01: four wall faces (W, E, N, S-GF), each one continuous face from its lowest floor to the roof soffit
(Q-72, R-SHAFT-1), split at +5.50 / +9.70 into the three storey-band lines GF / 1F / 2F, for plaster (to the
structural roof soffit) and paint (0.15 below, Q-48 A). Contacts (landings, flights, slab bands) and openings are
subtracted once as a union in the face plane.

## What changed and why

0. **Baseline reproduced**: the T-173 model + the T-640 D-T173-1 / B3 corrections reproduce all six candidate /
   overlay bounds (GF / 1F to 0.01, 2F 44.508 .. 49.868 vs 44.512 .. 49.872 and 42.723 .. 47.933 vs 42.722 .. 47.932:
   T-640 rounding of its inputs, <= 0.004 m2).
1. **R-T680-1: W25 and W27 heads applied.** T-173 held the shaft's 1F window (W25) as a band +3.50 .. +7.524 and W27
   as +7.684 .. roof soffit (sill / head printed nowhere). T-201 since established both from the DWF SOUTH WEST
   ELEVATION vector geometry (outline 1.001 x 1.501, datum the view's own level ticks, issue check 0.006 / 0.013 m):
   W25 +5.50 .. +7.00, W27 +9.70 .. +11.20. Binding: both 1.00 m windows stacked at along-facade 13.27 m on the SW
   facade = the shaft's 'N' face (T-173 frame), T-325 'W25 (1F stair), W27 (2F stair)'. Effect: each window is now
   deducted 1.50 m2 in both cases; the over-wide held bands no longer reach into the GF band (the W25 band below
   +5.50: 2.00 m2) or the 1F band (the W27 band below +9.70: 2.02 m2).
2. **R-T680-2: pier returns into their bands.** The T-173 storey bands exclude the two 0.05 m column returns on the
   W face (1.21 .. 1.22 m2 for the whole shaft): no candidate line carried them. Now split by band: GF 0.423, 1F
   0.396, 2F 0.394 .. 0.404 (plaster) / 0.379 .. 0.389 (paint); whole face = sum of bands checked (refused otherwise).
3. 2F keeps the T-640 corrections unchanged (low: W 0.104 + E 0.104 + N 0.05 + B3 0.08; high: W + E).

| line | band | before | after | change low / high (m2) |
|---|---|---|---|---|
| L-95f2c45c FIN.PLASTER / L-145bd239 FIN.PAINT | GF | 48.52 .. 62.01 | 50.945 .. 62.434 | +2.425 / +0.424 |
| L-0eac839f FIN.PLASTER / L-2ab93d50 FIN.PAINT | 1F | 42.48 .. 47.67 | 45.317 .. 46.564 | +2.837 / -1.106 |
| L-418121a4 FIN.PLASTER | 2F | blank (overlay 44.512 .. 49.872) | 47.342 .. 48.772 | +2.830 / -1.100 vs overlay |
| L-5a7a5c6f FIN.PAINT | 2F | blank (overlay 42.722 .. 47.932) | 45.392 .. 46.822 | +2.670 / -1.110 vs overlay |

Range width: 1F 5.19 -> 1.25 m2, 2F 5.36 -> 1.43 m2 (plaster). Whole shaft: plaster 143.604 .. 157.770, paint
141.654 .. 155.820 (T-173 whole 137.06 .. 160.98 / 135.26 .. 159.03).

Code totals of the HELD lines (V3.0.65 = V3.0.64 for these codes): FIN.PLASTER 932.72581 .. 1,006.77641 (14) + 10
blank -> 985.32981 .. 1,054.86641 (15) + 9 blank (+52.604 / +48.090: the 2F line 47.342 .. 48.772 newly bounded,
GF / 1F +5.262 / -0.682); with the T-676 OP-009 fix also applied: high 1,054.74641. FIN.PAINT 487.1210 .. 542.8606
(7) + 3 blank -> 537.7750 .. 589.0006 (8) + 2 blank (+50.654 / +46.140).

Coat materials (Q-79 internal 1:4, T-676 R-T676-3, 0.02 m ESTIMATED): GF 7.806 .. 9.566 bags / 1.084 .. 1.329 m3 sand;
1F 6.943 .. 7.134 / 0.964 .. 0.991; 2F 7.254 .. 7.473 / 1.007 .. 1.038. Spatter dash and water HELD (T-364; no ratio).

## Still open (named, never 0)

GF: build-up b 0 .. 0.10, NW floor under the winders +0.30 / +1.00 (C-SH-2), winder soffit (C-ST-3), the doorless
passage head to the basin space (OP-020), B20 over the GF south wall (Q-46 / OQ-11). 1F: b, B20 / B23 ends. 2F: b,
roof datum D-39, B23 end, D-T173-1 N and B3 (low end). The 1F / 2F spread is now almost all b and the beam ends.

Stair-core wet rooms L-a636dabc (GF-RD36087) and L-3f7fb1b3 (GF-RDF7D28) stay HELD blank, datum named: the floor
level +0.30 / +1.00 (T-088, C-SH-2), the top of the wet-wall render (1F slab soffit, and in GF-RDF7D28 a held beam,
T-283 / Q-61 C), and a held opening head (OP-020 passage; OP-014 window). A 0.70 m datum spread with an unestablished
top and a held opening gives no two-sided bound from the drawings.

## Findings

- F-T680-1 (designer list, D-45 class): section A-A (raster, 1:100) draws the W25 glazing about +5.6 .. +7.36, the
  SW elevation vector +5.50 .. +7.00. The vector governs (UP-OPEN-GEOM-001 proposal: a raster is never scaled);
  impact if the section were right: 1F lines -0.26 m2. W27 agrees (+9.75 .. +11.25 scaled vs +9.70 .. +11.20).
- F-T680-2: the storey-band split of T-173 dropped the pier returns (1.21 m2 per finish); fixed here, by band.
- T-314 (exterior faces) and T-364 (spatter dash) lines are not touched; the shaft's outside faces belong to T-314.

## Engine vs freelancer; verdict proposals

His two 'stair-house walls' rows are gross (204.42 m2, openings in a half-deduction list): like for like gross stays
-27.35 m2 (-13.4 %) (T-173 s.3, unchanged here). On W25 / W27 heights T-201's ENGINE_RIGHT stands (drawn 1.50 vs his
2.00). Verdict for the six lines: ENGINE_RIGHT on scope (open south side, R-SHAFT-1), RULE_DIFFERENCE on opening
deductions (full Q-73 vs his half), UNRESOLVED for his 2.50 x 5.40 row (on no drawing).

## For the Checker (re-measure two faces)

1. N face, 1F band, HI case (b 0): region u 0 .. 2.50, z 5.50 .. 9.70 = 10.50; minus MS2-LD bands (west 0 .. 1.25 at
   +7.516: 7.356 .. 7.516; east 1.25 .. 2.50 at +7.684: 7.524 .. 7.684) = 1.25 x 0.16 x 2 = 0.40; minus W25 1.00 x 1.50
   = 1.50 -> **8.60 m2** (paint = plaster below +9.70).
2. N face, 2F band plaster, HI case: u 0 .. 2.50, z 9.70 .. 13.74 = 10.10; minus W27 1.50 -> **8.60 m2** (before the
   T-640 N 0.05 correction, which the high end does not take).

Lessons-register row (proposed, ERS s.7): 2026-11-10 | a shaft window stayed a whole held band (2 .. 4 m2 per band)
after its head was established elsewhere, and the storey split dropped the pier returns | a held item is re-checked
against every later Checker-verified record before a line is restated; a band split keeps every built piece in one
band | R-T680-1 / -2 (every villa) | tests/t680 (normal: band before / after, returns by band, mirror; adverse: raster,
width, mm, head < sill, outside the face, unconfirmed status, missing roof datum, dropped returns, bad bound) | PROPOSED.
