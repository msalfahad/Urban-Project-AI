# S8.6A - lintel bearing, release authority and quantity reconciliation (dated correction layer)

Baseline `974bff2`, date 2026-10-10, stamp `974bff2+code:34d3aace68075085`. The frozen S8.6 package is verified and never written.

## Result

- Frozen S8.6 release: 14 lintels, 0.745261681 m3, 96.427279858 kg (history).
- Corrected eligible release: **7 lintels, 0.366 m3, 49.589037037 kg**.
- By floor: GF 0.102 m3, 1F 0.264 m3, 2F 0 m3

## Every lintel

| Lintel | Frozen m3 | Corrected state | Corrected m3 | Reason |
|---|---|---|---|---|
| LT-OP-1F-003 | 0.048 | RETAINED_PROJECT_BASIS_QTO | 0.048 | both bearings are drawn masonry >= 400 mm (independent trace); no beam band over the opening; door symbol (a swing leaf in the gap) gives a wall to carry (head not printed: Q-HEAD-GENERAL stands) |
| LT-OP-1F-014 | 0.048 | RETAINED_PROJECT_BASIS_QTO | 0.048 | both bearings are drawn masonry >= 400 mm (independent trace); no beam band over the opening; door symbol (a swing leaf in the gap) gives a wall to carry (head not printed: Q-HEAD-GENERAL stands) |
| LT-OP-1F-017 | 0.043792802 | BLOCKED_BEARING_REQUIREMENT | 0 | BLOCKED_BEARING_REQUIREMENT: start 259.2 mm (T_JUNCTION) against MIN.40cm |
| LT-OP-1F-018 | 0.0495 | RETAINED_PROJECT_BASIS_QTO | 0.054 | both bearings are drawn masonry >= 400 mm (independent trace); no beam band over the opening; arch block or header lines drawn over both faces gives a wall to carry (head not printed: Q-HEAD-GENERAL stands) |
| LT-OP-1F-020 | 0.051 | RETAINED_PROJECT_BASIS_QTO | 0.051 | both bearings are drawn masonry >= 400 mm (independent trace); no beam band over the opening; door symbol (a swing leaf in the gap) gives a wall to carry (head not printed: Q-HEAD-GENERAL stands) |
| LT-OP-1F-021 | 0.063 | RETAINED_PROJECT_BASIS_QTO | 0.063 | both bearings are drawn masonry >= 400 mm (independent trace); no beam band over the opening; arch block or header lines drawn over both faces gives a wall to carry (head not printed: Q-HEAD-GENERAL stands) |
| LT-OP-GF-005 | 0.042723447 | BLOCKED_BEARING_REQUIREMENT | 0 | BLOCKED_BEARING_REQUIREMENT: start 223.7 mm (T_JUNCTION) against MIN.40cm |
| LT-OP-GF-008 | 0.048 | RETAINED_PROJECT_BASIS_QTO | 0.048 | both bearings are drawn masonry >= 400 mm (independent trace); no beam band over the opening; door symbol (a swing leaf in the gap) gives a wall to carry (head not printed: Q-HEAD-GENERAL stands) |
| LT-OP-GF-013 | 0.06002 | BLOCKED_COLUMN_CONNECTION | 0 | BLOCKED_COLUMN_CONNECTION: start 100 mm (COLUMN) against MIN.40cm |
| LT-OP-GF-014 | 0.092 | BLOCKED_HEAD_FUNCTION_UNRESOLVED | 0 | bearings confirmed, but the opening is glazing whose function (window or full-height) is unresolved and no head is printed: on this project printed sills show full-height glazing exists, so a wall above the head is not established. Not released automatically. |
| LT-OP-GF-018 | 0.06002 | BLOCKED_COLUMN_CONNECTION | 0 | BLOCKED_COLUMN_CONNECTION: end 100 mm (COLUMN) against MIN.40cm |
| LT-OP-GF-021 | 0.043515 | BLOCKED_BEARING_REQUIREMENT | 0 | BLOCKED_BEARING_REQUIREMENT: start 253 mm (T_JUNCTION) against MIN.40cm |
| LT-OP-GF-028 | 0.054 | RETAINED_PROJECT_BASIS_QTO | 0.054 | both bearings are drawn masonry >= 400 mm (independent trace); no beam band over the opening; door symbol (a swing leaf in the gap) gives a wall to carry (head not printed: Q-HEAD-GENERAL stands) |
| LT-OP-GF-029 | 0.041690432 | BLOCKED_BEARING_REQUIREMENT | 0 | BLOCKED_BEARING_REQUIREMENT: start 372.7 mm (OBLIQUE_JUNCTION); end 189.1 mm (L_CORNER) against MIN.40cm |

## Outputs

- `00_README.md`
- `01_RELEASE_AUTHORITY_REGISTER.csv`
- `02_SIX_CASE_INVESTIGATION.csv`
- `03_BEARING_AND_COLUMN_CONNECTION_AUDIT.csv`
- `04_COVER_AND_STIRRUP_AUTHORITY.csv`
- `05_CORRECTED_ELIGIBLE_RELEASE_VIEW.csv`
- `06_CONCRETE_OWNERSHIP_AND_OVERLAP.csv`
- `07_REINFORCEMENT_RECLASSIFICATION.csv`
- `08_OPENING_CENSUS_VERIFICATION.csv`
- `09_QUANTITY_RECONCILIATION.csv`
- `10_PREVIOUS_FREEZE_VERIFICATION.csv`
- `11_S8_6A_SUMMARY.json`
- `12_S8_6A_CORRECTION_MANIFEST.json`

Rebuild: `python3 -I research/alsenan_lintels_s8_6a/build_s8_6a.py` (byte-identical).
