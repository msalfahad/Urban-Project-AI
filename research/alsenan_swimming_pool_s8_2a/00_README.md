# S8.2A: architectural elevation source recovery and pool depth authority

Baseline `3286056`. A dated correction layer on the frozen S8.2. No S8.2 file changes. Manifest `12_S8_2A_FREEZE_MANIFEST.json`, `references_read: []`.

## Answer

- **'115' belongs to the swimming pool** (BOUND). It is the inner depth from the pool-wall top (+0.30) to the inner floor (-0.85), at the one plane the north-west elevation draws.
- **'70' does not.** It runs from the pool-wall top (+0.30) to the house ground floor (+1.00).
- **'+0.15'** is the deck round the pool. The walls rise 0.15 above it.
- **Released:** concrete 0 m3, reinforcement 0 kg. The floor profile is a **PROFILE_CONFLICT**: the architectural elevation draws one flat floor, the structural detail a deep end, a slope and a shallow end. So no single depth applies to the whole pool.

## Source identity

- `ARCH_PART_1_PAGES_01-06` `cd3b8669d559…` against the earlier `80b6a8042899…`: **WRAPPER_METADATA_ONLY**. The new file is 134 bytes longer, entirely from an added /Title and /Subject. Removing them reproduces the earlier file's SHA-256 exactly.
- `ARCH_PART_2_PAGES_07-12` `1e7087d3e61b…` against the earlier `281a0c3f8c1c…`: **WRAPPER_METADATA_ONLY**. The new file is 134 bytes longer, entirely from an added /Title and /Subject. Removing them reproduces the earlier file's SHA-256 exactly.

## Binding criteria (vector DXF)

- [x] IDENTITY_LABEL: plan text 'swimming pool' (layer 5) 739.0 mm from the pool arc centre, inside the R1550 water outline
- [x] DIMENSION_MATCH: elevation outer faces 3500.0 mm apart = plan '350' (4C4) 3500.0 mm
- [x] DIMENSION_MATCH: elevation inner faces 3100.0 mm apart = 2 x the R1550 water arc
- [x] DIMENSION_MATCH: elevation wall 200.0 mm = R1750 - R1550
- [x] FEATURE_MATCH: 10 generator lines inside the element are those of a cylinder of radius 1550.0 mm seen side-on (angles [71.7, 44.6, 31.1, 18.3, 12.2]): the pool's semicircular inner wall R1550
- [x] FEATURE_MATCH: the curved element above is symmetric about the same axis with half-width 2236.1 mm = the plan arc R2250 (96.379-263.621 deg, inner face of the curved wall: pool R1750 + gap 500) projected on the facade axis, 2236.1 mm
- [x] FEATURE_MATCH: view direction: both drawn features are symmetric about the element's axis. The curved-wall arc projects symmetrically only onto plan y (-2236..2236 mm); onto x it spans -2250..-250 mm. So the elevation looks along plan x, from the straight sea-side end
- [x] LEVEL_MATCH: '+0.15' on the elevation deck line right of the element and 2 '+0.15' LEVEL marks round the pool in plan
- [ ] CONTRADICTION: another sunken object (lift, pit, tank, sump) labelled at this place in plan: []

## Pool levels and zones

| item | value | state |
|---|---|---|
| pool wall top level | 0.3 m | ESTABLISHED |
| deck level round the pool | 0.15 m | ESTABLISHED |
| wall upstand above the deck | 0.15 m | DERIVED_FROM_STATED_LEVELS |
| inner depth at the drawn plane | 1.15 m | STATED_AT_DRAWN_PLANE_ONLY |
| inner floor level at the drawn plane | -0.85 m | DERIVED_AT_DRAWN_PLANE_ONLY |
| deep-end depth |  m | NOT_ESTABLISHED |
| shallow-end depth |  m | NOT_ESTABLISHED |
| wall heights by wall run |  m | NOT_ESTABLISHED |
| floor slope |   | PROFILE_CONFLICT |
| deep / shallow zone boundaries in plan |  m | NOT_ESTABLISHED |
| direction of any deep / shallow profile |   | INFERENCE_ONLY |
| base thickness by zone | {"deep": 0.4, "shallow": null, "slope": null} m | UNCHANGED_FROM_S8_2 |
| structural concrete ownership | base owns footprint x thickness incl. wall footprint; walls own band x height above base top  | UNCHANGED_FROM_S8_2 |
| pool wall / base interfaces | {"BASE_ONLY": 3, "SINGLE_BENT_BAR": 5, "UNRESOLVED": 6}  | UNCHANGED_FROM_S8_2 |
| floor profile across sources | PROFILE_CONFLICT  | PROFILE_CONFLICT |

## Outputs

- `00_README.md`
- `01_ARCH_PDF_IDENTITY_COMPARISON.csv`
- `02_ELEVATION_TO_PLAN_BINDING_AUDIT.csv`
- `03_DIMENSION_SOURCE_REGISTER.csv`
- `04_POOL_DEPTH_AND_ZONE_INTERPRETATION.csv`
- `05_QUANTITY_READINESS_DELTA.csv`
- `06_BLOCKED_REGISTER_DELTA.csv`
- `07_CONFLICT_AND_QUESTION_REGISTER_DELTA.csv`
- `08_SENSITIVITY_CASES.csv`
- `09_CONSERVATION_CHECKS.csv`
- `10_PROVENANCE.jsonl`
- `11_S8_2A_SUMMARY.json`
- `12_S8_2A_FREEZE_MANIFEST.json`
