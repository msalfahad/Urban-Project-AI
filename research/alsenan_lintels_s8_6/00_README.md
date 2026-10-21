# S8.6 - lintels: opening census, schedule binding, lintel concrete and reinforcement

Baseline `818321e`, engine stamp `818321e+code:6629546ee8609d25`. Frozen before any comparison (`references_read: []`).

## Openings

- 65 wall openings found from the P7757 wall faces, 1 gate in the boundary wall and 8 slab openings (S1). 3 candidate gaps were rejected (wall bends, unrelated wall ends).

- 1F: 1_INTERNAL_DOOR 10, 4_5_GLAZED_WINDOW_OR_FULL_HEIGHT_UNRESOLVED 11, 5_FULL_HEIGHT_GLAZED_OPENING 2, 6_SERVICE_SHAFT_OPENING 1, 7_OPEN_ARCHWAY_OR_PASSAGE 2
- 1F_ROOF_SLAB: 8_STRUCTURAL_SLAB_OPENING 2
- 2F: 1_INTERNAL_DOOR 2, 3_EXTERNAL_DOOR 1, 4_5_GLAZED_WINDOW_OR_FULL_HEIGHT_UNRESOLVED 4, 6_SERVICE_SHAFT_OPENING 1
- GF: 1_INTERNAL_DOOR 8, 2_MAIN_ENTRANCE_DOOR 1, 3_EXTERNAL_DOOR 6, 4_5_GLAZED_WINDOW_OR_FULL_HEIGHT_UNRESOLVED 12, 6_SERVICE_SHAFT_OPENING 1, 7_OPEN_ARCHWAY_OR_PASSAGE 4
- GF_ROOF_SLAB: 8_STRUCTURAL_SLAB_OPENING 5
- GROUND_SLAB_SOG: 8_STRUCTURAL_SLAB_OPENING 1

## Decisions

- BLOCKED_SUPPORT_IDENTITY: 52
- OPENING_NOT_REQUIRING_SEPARATE_LINTEL: 8
- SCHEDULE_BOUND_LINTEL: 14

## Released (PROJECT_BASIS_QTO)

- 14 lintels, 0.745262 m3, 96.427 kg.
- m3 by floor: GF 0.441969, 1F 0.303293, 2F 0
- kg by diameter: Ø8 23.478, Ø10 22.5, Ø12 40.045, Ø14 10.405
- Not released (sensitivity only): 50 lintels, 4.231717 m3, 522.091 kg.

## Outputs

- `00_README.md`
- `01_OPENING_CENSUS.csv`
- `02_LINTEL_SCHEDULE_TRANSCRIPTION.csv`
- `03_ARCH_STRUCTURAL_REGISTRATION.csv`
- `04_OPENING_LINTEL_BINDING_MATRIX.csv`
- `05_BEAM_OVERLAP_AUDIT.csv`
- `06_LINTEL_CONCRETE_QTO.csv`
- `07_LINTEL_REBAR_QTO.csv`
- `08_BLOCKED_AND_CONFLICTS.csv`
- `09_OPENING_REGISTER_FOR_BOQ.csv`
- `10_OWNERSHIP_RECONCILIATION.csv`
- `11_CONSERVATION_CHECKS.csv`
- `12_SOURCE_AUTHORITY.csv`
- `13_PROVENANCE.jsonl`
- `14_S8_6_SUMMARY.json`
- `15_S8_6_FREEZE_MANIFEST.json`

Rebuild: `python3 -I research/alsenan_lintels_s8_6/build_s8_6.py` (byte-identical). Renders of the drawings stay outside git.
