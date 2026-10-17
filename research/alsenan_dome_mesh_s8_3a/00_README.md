# S8.3A: independent dome-shell reinforcement distribution audit

Baseline `6ddd988`. A dated correction layer on the frozen S8.3; S8.3 and its errata verify unchanged.

## Answer

- The frozen **602.111304 kg** stays the S8.3 PROJECT_BASIS_QTO quantity, now classified **IDEALIZED_SURFACE_DENSITY_QTO**.
  - It is not a physical lower bound and not a validated BBS.
  - The fabrication-grade layout is unresolved.
- The drawing is a generic specification: Ø12 at 150 mm, meridional and hoop, one typical section, N.I.S.
  - It does not say where the meridional 150 mm applies.
  - Its one continuous meridian drawn over the crown cannot be built for every bar.
- The hoops are supported as 150 mm along the meridian. Their continuous total is A / s in every scenario.
- The scenarios differ only in the meridians:

| scenario | meridional m / dome | hoop m / dome | kg, two domes | x frozen | lane |
|---|---|---|---|---|---|
| A existing uniform surface density (frozen S8.3) | 169.343804 | 169.343804 | 602.111304 | 1.0000 | PROJECT_BASIS_QTO (frozen, unchanged) |
| B meridians fixed at 150 mm on the springing circle, springing to crown | 280.045865 | 169.343804 | 798.914968 | 1.3269 | SENSITIVITY_ONLY |
| B-FAB scenario B with whole bars and whole circles | 281.738327 | 176.169871 | 814.059019 | 1.3520 | SENSITIVITY_ONLY |
| C test rule: alternate meridians stop where the spacing halves (75 mm) | 212.557915 | 169.343804 | 678.936390 | 1.1276 | SENSITIVITY_ONLY |

## Formulas

Mid-surface: R_m = 2.185289474 m, centre 0.335289474 m below the springing, psi0 = acos(d / R_m) = 1.416757646 rad.

- Area: A = 2 pi R_m^2 (1 - cos psi0) = 25.401570619 m2.
- Springing circle: 2 pi R_m sin psi0 = 13.568001560 m.
- Meridian, springing to crown: R_m psi0 = 3.096025571 m.
- A: L = A / s for each family.
- B: N = circumference / s = 90.453344 (unrounded); L_mer = N R_m psi0; L_hoop = A / s.
- C (a test rule, not a source): every other meridian stops where the spacing falls to 75 mm.
- kg = L x 12^2 / 162 x 2 domes.

## Drawing evidence

- **meridional bars**: label 1A0E 'Ø12MM/15cm' points at the drawn bar line (r 10841.8 vs bar r 10841.8). bars in the vertical planes through the dome axis (radial in plan, curved in section).
- **circumferential bars**: label 1A15 'Ø12MM/15cm' points at the hoop dots; 62 dots. horizontal circles at successive heights, cut in the section.
- **where the 150 mm spacing is stated**: only in the two label texts; no dimension, no reference circle, no 'max' or 'at springing'. the reference location of the meridional spacing is NOT stated.
- **hoop spacing along the meridian**: the dots sit at a constant angular step (2.6424 deg, spread 0.000011) from 9.38 to 170.56 deg. uniform along the arc, i.e. measured along the shell (a vertical spacing would not be uniform in angle); drawn about every 100 mm, not 150: the drawn pitch is graphic.
- **meridian continuity**: one bar drawn from ring to ring over the crown (arc 9.24 to 170.76 deg, crosses the crown: True), with 4 straight legs and hooks into both ring cuts. continuous springing to springing as drawn.
- **stops, staggers, splices, density changes**: none drawn: no curtailment mark, no lap, no second spacing, no crown ring, cap mesh or trimming bar. the section shows one typical bar of each family.
- **the plan's radial lines**: [20, 20] radial lines per dome on layer S-OPENING, 18 deg apart. a dome / opening symbol, not bars: 20 lines on a 13.6 m circle would be 0.68 m apart, against the 150 mm label.
- **status of the drawing**: DETAIL OF DOME (N.I.S): one typical section, cut through the axis. a generic reinforcement specification (size, spacing, directions, anchorage into the ring), not a buildable radial-bar layout.

## Missing evidence for a physically defensible quantity

- ME-01 (Engineer): where the meridional 150 mm applies (at the springing, as a maximum, or as an average). decides between A-type and B-type quantities.
- ME-02 (Engineer): the meridional arrangement: number of radial bars, which stop and where, or a crown detail (crown ring, cap mesh, cut-off radius). the drawn continuous meridians cannot all pass the crown.
- ME-03 (Engineer): laps / splices of both families: positions and lengths. hoops reach 13.6 m on the mid-surface.
- ME-04 (Engineer / architect): anchorage of the meridians into the ring: leg length and hook. follows the ring depth 'AS PER ARCH' (S8.3 CF-S8.3-03).
- ME-05 (Engineer): bar layer position and cover (mid-surface used). intrados / extrados change the area by -5 / +5 %.
- ME-06 (Engineer): one mesh or two (S8.3 CF-S8.3-07 read one from the drawing). doubles the quantity.
- ME-07 (Engineer): role and size of the unlabelled junction bar (S8.3-E02). already blocked; listed so it is not lost.

No new bar object was found beyond the S8.3 register and errata ({'ALREADY_RECORDED': 86, 'REPEAT_OF_RECORDED_FAMILY': 1}). The crown termination is missing information, not a missing drawn bar.

## Outputs

- `00_README.md`
- `01_SOURCE_EVIDENCE.csv`
- `02_SCENARIOS.csv`
- `03_PHYSICAL_LAYOUT_FEASIBILITY.csv`
- `04_STATUS_CHANGES.csv`
- `05_BAR_OBJECT_RECONCILIATION.csv`
- `06_MISSING_EVIDENCE.csv`
- `07_FROZEN_VERIFICATION.json`
- `08_S8_3A_SUMMARY.json`
- `09_S8_3A_FREEZE_MANIFEST.json`
