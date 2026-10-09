# S8.4 post-freeze comparison

Run after the freeze (`15_S8_4_FREEZE_MANIFEST.json`, sha `45fd614f0c22…`), verified before and after; no frozen quantity changes.

## Equal scope: the four tank callouts

The old Urban V3b register has one bar set per tank callout, **222.479 kg**, against S8.4's **361.209 kg**. V3b's figure is reproduced by its own formula (count x bar length x D^2/162) and bridged step by step:

| step | kg |
|---|---|
| V3B four tank sets (one face each) | 222.479 |
| RUN_BASIS: less V3b's 2 x 175 mm embedment beyond the faces (S8.4 blocks anchorage) | -26.272 |
| COUNT_BASIS: whole bars floor(n W) + 1 on the rectangle -> unrounded rate x area (panel 01's notch) | -9.084 |
| LAYER: add the second face each callout's (T&B) states | +187.123 |
| STOP_ZONE: less the bottom stop zones S8.4 blocks | -13.038 |
| S8.4 released | 361.209 |

- The largest difference is the layer: V3b reads each callout once and never applies its (T&B).
- V3b adds 175 mm embedment at each end and counts whole bars as floor(n W) + 1; S8.4 measures face to face, blocks anchorage and keeps the count unrounded.

## Concrete

- No earlier figure itemises the tank panels. V3b's C-SLAB-2F is the whole plate, 55.478 m2 x 0.180 m = 9.986 m3; its own thickness on the two tank faces gives 2.4543 m3, the same as S8.4.
- V3b's 180 mm over the whole floor disagrees with the source (160 mm outside the tank panels): PRE-S7 C-05, outside S8.4's scope.

## Other references

- PF-02 Urban V3b (BOQ_LINES_V3B) (R-SLAB-2F_ROOF (whole 2F roof, 16 bar sets)): SCOPE. the four tank sets (222.479 kg) sit inside this line with the other panels' sets; the line misses the (T&B) top faces of the tank panels (187.123 kg at S8.4's basis); the control plane marks it VERIFIED_PARTIAL_LOWER_BOUND
- PF-03 Urban V3b (BOQ_LINES_V3B) (C-SLAB-2F (net plate x t)): SCOPE + PLATE_BASIS + THICKNESS_BASIS. V3b: 55.478 m2 x 0.180 m for the whole floor (beam strips inside the plate, full depth); the tank panels are not itemised (PRE-S8 NOT_ITEMISED). V3b's own rule on the two tank faces gives 2.4543 m3 = S8.4 2.4543 m3 (NO_DIFFERENCE in thickness there); outside them the source says 160 mm (P8-N18), V3b uses 180 (PRE-S7 C-05)
- PF-05 freelancer QS (lineage) (SLABS / SLAB_NET_2F (net of beams)): SCOPE. not itemised per panel. Explanation only: the same face-to-face basis over the whole 2F roof (S7's 5 panels at their 160 mm, 5.0000 m3, plus S8.4's 2.4543 m3) gives 7.4543 m3, +0.0427 m3 from the freelancer net; never a release
- PF-06 multi-engine comparison (SLABS 2F (oracle)): NOT_COMPARABLE. the oracle agrees with V3b's full-depth plate (9.986 m3); no per-panel figure
- PF-07 freelancer QS (lineage) (SLABS steel (all floors)): NOT_COMPARABLE. one steel tonnage for every slab of the building
- PF-08 control plane V2 (C-SLAB-2F / R-SLAB-2F_ROOF states): NOT_COMPARABLE. C-SLAB-2F VERIFIED_COMPLETE; R-SLAB-2F_ROOF VERIFIED_PARTIAL_LOWER_BOUND; neither itemises the tank
- PF-09 PRE-S8 coverage (WATER_TANK 2F_ROOF_SLAB): NOT_COMPARABLE. PRE-S8 coverage NOT_MEASURED / faces {"NOT_ITEMISED": 2}: no earlier Urban figure for the tank; S8.4 is the first itemised measure
- PF-10 coverage-recovery dashboard (SLABS (all floors)): NOT_COMPARABLE. one slab total for the building; no per-panel figure
