# S8.2: swimming pool, source-controlled concrete and reinforcement QTO

Baseline `763a00e`. Built blind and frozen before comparison (`18_S8_2_FREEZE_MANIFEST.json`, `references_read: []`).

## Result

- Released concrete: **0 m3**. All 7 concrete rows are blocked.
- Released reinforcement: **0 kg**. The 21 bar families are split by lane as {'BLOCKED_UNQUANTIFIED': 16, 'SOURCE_CONFLICT': 5}.
- Pool totals: **unknown**. They are left empty, not 0.

The p.7 detail is NOT TO SCALE. Its depths, wall heights and deep / slope / shallow lengths read 'AS PER ARCH', and the architectural set prints none of them. Every volume and every bar mass therefore waits for a stated depth, height or extent.

## Established geometry (GBP, exact lines and arcs)

| item | m2 |
|---|---|
| structural footprint (base) | 10.935564 |
| water outline | 8.578838 |
| wall band (200 mm) | 2.356726 |
| PL-WALL-RUN-E | 0.700000 |
| PL-WALL-RUN-N | 0.310000 |
| PL-WALL-RUN-S | 0.310000 |
| PL-WALL-RUN-W | 1.036726 |

Stated dimensions: walls 20 cm (both), deep base 40 cm. Perimeters: water 11.069469 m, outer 12.497787 m.

## Reinforcement

- 6 drawn bar runs in the main section, shaped {'COMPOUND': 2, 'CRANKED': 4}.
- 1 bar-end mark, 10 sub-detail shapes and 16 dot rows.
- Diameters: [10.0, 12.0, 14.0, 16.0] mm.
- All 26 S1 records terminate: {'FAMILY_PRIMARY_LABEL': 17, 'SAME_FAMILY_SECOND_LABEL (counted once)': 1, 'SECOND_VIEW_DIAMETER_CONFLICT': 1, 'SECOND_VIEW_OF_FAMILY': 5, 'SECOND_VIEW_TOPOLOGY_DIFFERS': 1, 'SUB_DETAIL_BINDING_AMBIGUOUS': 1}.
- Wall/base interfaces: {'BASE_ONLY': 3, 'SINGLE_BENT_BAR': 5, 'UNRESOLVED': 6}.
- No physical bar schedule exists. Bends, hooks, laps and anchorage are drawn only on the NTS detail.

## Build-up (kept as printed, separate BOQ families)

- `PL-BUILDUP-SCREED`: '5cm SECREED.' -> SCREED (BLOCKED_UNQUANTIFIED)
- `PL-BUILDUP-INSULATION_MEMBRANE`: '5cm INSULATION MEMBRANE.' -> WATERPROOFING_OR_INSULATION (BLOCKED_UNQUANTIFIED)
- `PL-BUILDUP-PLAIN_CONCRETE`: '10cm PLAIN CONCRETE.' -> PLAIN_CONCRETE (BLOCKED_UNQUANTIFIED)

## Conflicts (17) and questions (11)

See `16_CONFLICT_AND_QUESTION_REGISTER.csv`.

## Outputs

- `00_README.md`
- `01_POOL_SOURCE_AND_RULE_REGISTER.csv`
- `02_POOL_POPULATION_AND_OWNERSHIP.csv`
- `03_CONCRETE_GEOMETRY_AND_QTO.csv`
- `04_BASE_REINFORCEMENT_QTO.csv`
- `05_WALL_REINFORCEMENT_QTO.csv`
- `06_BAR_RUN_AND_BENT_BAR_REGISTER.csv`
- `07_BLOCKED_REINFORCEMENT_REGISTER.csv`
- `08_WALL_BASE_INTERFACE_AUDIT.csv`
- `09_PLAIN_CONCRETE_AND_BUILD_UP_REGISTER.csv`
- `10_FLOOR_POOL_SUMMARY.csv`
- `11_PROVENANCE.jsonl`
- `12_CONSERVATION_CHECKS.csv`
- `13_REBAR_EVIDENCE_BINDING.csv`
- `14_COVER_APPLICABILITY.csv`
- `15_SENSITIVITY_SCENARIOS.csv`
- `16_CONFLICT_AND_QUESTION_REGISTER.csv`
- `17_S8_2_SUMMARY.json`
- `18_S8_2_FREEZE_MANIFEST.json`
