# S8.1 post-freeze comparison (ground slab, two source-zoned cells)

S8.1 was frozen at `201f441`. The manifest sha256 is `e99d83a750b64541...`.
This script refused to open any earlier figure until three checks passed:
- every frozen hash still matches;
- the manifest is the one committed at the freeze;
- that commit holds no post-freeze file.

Nothing here changes S8.1. It stays **37.859 m2, 3.786 m3, 233.695 kg** (two marker cells SP-GBP-08, SP-GBP-14; 6.1728 kg/m2, 61.73 kg/m3). The other 19 faces (129.771 m2) stay BLOCKED.

## Equal scope: the two marker cells

| cell | S8.1 m2 | old Urban cell m2 | diff | christiannp face m2 | diff |
|---|---|---|---|---|---|
| SP-GBP-08 (GS-ZONE-1690) | 14.8931 | 14.7729 | -0.1202 | 14.8931 | -0.0000 |
| SP-GBP-14 (GS-ZONE-169D) | 22.9654 | 22.9301 | -0.0353 | 22.9650 | -0.0004 |

Every reference uses the same thickness (0.10 m) and the same mesh (5Ø10/m each way, one layer) on these two cells. On equal scope the only difference is the cell boundary.

## Reference totals

| reference | quantity | matching | reference | S8.1 | reference - S8.1 | on S8.1 scope | classes |
|---|---|---|---|---|---|---|---|
| OLD_URBAN_CR_LOWER_BOUND | CONCRETE_M3 | CELL | 11.528 | 3.786 | 7.742 | 3.770 | ZONE_EXTENT_SCOPE +6.923, OTHER_OWNER_CELL +0.834, MARKER_CELL_GEOMETRY -0.016, REFERENCE_ROUNDING +0.000 |
| OLD_URBAN_CR_BEST | CONCRETE_M3 | CELL | 21.701 | 3.786 | 17.915 | 3.770 | ZONE_EXTENT_SCOPE +12.841, POPULATION_GAP +4.256, OTHER_OWNER_CELL +0.834, MARKER_CELL_GEOMETRY -0.016, REFERENCE_ROUNDING -0.000 |
| OLD_URBAN_R4 | REBAR_KG | ZONE_VIA_CR_CELL_SPLIT | 712.277 | 233.695 | 478.583 | 232.735 | ZONE_EXTENT_SCOPE +427.358, OTHER_OWNER_CELL +51.482, MARKER_CELL_GEOMETRY -0.960, ZONE_POLYGON_RESIDUAL +0.702, REFERENCE_ROUNDING +0.000 |
| OLD_URBAN_R3 | REBAR_KG | ZONE_VIA_CR_CELL_SPLIT | 712.277 | 233.695 | 478.583 | 232.735 | ZONE_EXTENT_SCOPE +427.358, OTHER_OWNER_CELL +51.482, MARKER_CELL_GEOMETRY -0.960, ZONE_POLYGON_RESIDUAL +0.702, REFERENCE_ROUNDING +0.000 |
| OLD_URBAN_V3B | REBAR_KG | ZONE_VIA_CR_CELL_SPLIT | 720.691 | 233.695 | 486.997 | 232.735 | ZONE_EXTENT_SCOPE +427.358, OTHER_OWNER_CELL +51.482, COUNT_CONVENTION +8.414, MARKER_CELL_GEOMETRY -0.960, ZONE_POLYGON_RESIDUAL +0.702, REFERENCE_ROUNDING +0.000 |
| OLD_URBAN_V3B | CONCRETE_M3 | ZONE_VIA_CR_CELL_SPLIT | 11.539 | 3.786 | 7.753 | 3.770 | ZONE_EXTENT_SCOPE +6.923, OTHER_OWNER_CELL +0.834, MARKER_CELL_GEOMETRY -0.016, ZONE_POLYGON_RESIDUAL +0.011, REFERENCE_ROUNDING +0.000 |
| CHRISTIANNP_FORENSIC | CONCRETE_M3 | CELL | 21.768 | 3.786 | 17.982 | 3.786 | ZONE_EXTENT_SCOPE +12.938, POPULATION_GAP +4.207, OTHER_OWNER_CELL +0.837, MARKER_CELL_GEOMETRY -0.000 |
| CHRISTIANNP_FORENSIC | REBAR_KG | CELL | 1,343.720 | 233.695 | 1,110.025 | 233.692 | ZONE_EXTENT_SCOPE +798.656, POPULATION_GAP +259.691, OTHER_OWNER_CELL +51.681, MARKER_CELL_GEOMETRY -0.003, REFERENCE_ROUNDING +0.000 |
| FREELANCER | CONCRETE_M3 | CATEGORY | 29.550 | 3.786 | 25.764 | n/a | ZONE_EXTENT_SCOPE +12.977, GROSS_AREA_UNSEPARATED +12.787 |
| FREELANCER | REBAR_KG | NOT_COMPARABLE | n/a | 233.695 | n/a | n/a | - |
| UC4N | CONCRETE_M3 | CATEGORY | 32.183 | 3.786 | 28.397 | n/a | SCOPE_UNSEPARATED +28.397 |
| CHRISTIANNP_ORIGINAL | CONCRETE_M3 | CATEGORY | 32.404 | 3.786 | 28.618 | n/a | SCOPE_UNSEPARATED +28.618 |
| UC4N | REBAR_KG | NOT_COMPARABLE | n/a | 233.695 | n/a | n/a | - |
| ROUGH_130_KG_PER_M3 | REBAR_KG | SANITY_ONLY | 492.161 | 233.695 | 258.466 | n/a | SANITY_RATIO +258.466 |

MEASUREMENT_ORIGIN is on every row of `S8_1_POST_FREEZE_REFERENCE_TOTALS.csv`. The old V3b figures are `OLD_V3B_CALCULATED`; S8.1 is the source-verified current measurement.

## Findings (new issues; nothing applied)

- **S8.1-PF-01 POPULATION_GAP**: a region round lift pit 7BE has no S1 / PRE-S8 / S8.1 ground-slab face, so S8.1 neither measures nor blocks it. Evidence: old Urban cell ['FP1-C99368_44772:X'] 42.5596 m2; christiannp 11 slab faces 41.8356 m2 + pit opening 3.24 m2. Effect on S8.1: none on the two-zone quantities (no TT1 marker there); the blocked register under-states the unquantified ground slab. Next: new issue: face the GBP core with the S-BW pit lines as barriers, register the cells as BLOCKED (no thickness / mesh) and the pit as an opening; new regression; new version.
- **S8.1-PF-02 ZONE_EXTENT_INTERPRETATION**: old Urban extended each TT1 marker to a multi-cell zone (V3a ZONE-1: 7 cells; V3b ZONE-2: the whole FP-2 footprint, 7 cells); christiannp and the freelancer apply T=10cm to every cell. Evidence: no printed zone boundary, hatch extent or note ties TT1 to more than the cell that holds it (S8.1 02 rules / 06 blocked). Effect on S8.1: none; the 19 other cells stay BLOCKED. Next: owner / engineer question: does 'T=10cm 5Ø10/m E.W.' apply to the whole ground slab? An answer is new source evidence for a new version.
- **S8.1-PF-03 OWNERSHIP_OVERLAP**: old Urban (V3a ZONE-1) and christiannp both counted stair-flight cell SP-GBP-12 as ground slab. Evidence: ['FP1-C101329_39533:R'] 8.3401 m2 / christiannp ['F130'] 8.3723 m2. Effect on S8.1: none; PRE-S8 gives the cell to the S8 stair family, S8.1 never measures it. Next: keep it with the stair family; no ground-slab item there.
- **S8.1-PF-04 COUNT_CONVENTION**: V3b ZONE-2 uses n = floor(sqrt(A)/0.2) + 1 equivalent square bars per direction. Evidence: +8.414 kg over area x rate. Effect on S8.1: none (S8.1 never adds +1). Next: none.

## Class meanings

- `MARKER_CELL_GEOMETRY`: same marker cell, different boundary: S8.1 measures the drawn ground-beam inner faces with the arc as an arc; old Urban subtracts 300 mm bands and single lines from a founded footprint; christiannp samples vector faces.
- `ZONE_EXTENT_SCOPE`: the reference quantifies cells with no TT1 marker; S8.1 binds each marker to the cell that holds it and keeps the other cells BLOCKED (unknown is not zero).
- `OTHER_OWNER_CELL`: the reference counts the stair-flight cell SP-GBP-12 as ground slab; PRE-S8 gives it to the S8 stair family.
- `POPULATION_GAP`: reference area at points no S1 / PRE-S8 / S8.1 face covers: the lift-pit core round S-BW 7BE (old Urban counted the pit inside one cell) and slivers / beam-band remnants.
- `ZONE_POLYGON_RESIDUAL`: the old zone polygon (V3a ZONE-1 / V3b ZONE-2) against its own coverage-round cell split.
- `COUNT_CONVENTION`: V3b ZONE-2: n = floor(sqrt(A)/0.2) + 1 bars of A / ((n - 1) x 0.2) m; S8.1 = rate x area, never +1.
- `GROSS_AREA_UNSEPARATED`: one gross area row: beam / column footprints, the stair cell and the unfaced core are not separable.
- `SCOPE_UNSEPARATED`: one ground-slab figure with no cell list: whole-slab scope against two marker cells.
- `REFERENCE_ROUNDING`: the reference's printed rounding of its own area / kg.
- `SANITY_RATIO`: a category kg/m3 heuristic (ground beams + slab together) against a restricted rate x area QTO.
- `UNKNOWN`: not explained.

The rough 130 kg/m3 ratio is `SANITY_CHECK_ONLY`. It is shown, not used. No S8.1 quantity is tuned, scaled or promoted towards any reference.

UNKNOWN rows: 0.
