# S8.3: dome and ring-beam structural QTO

Baseline `104c9d6`. Frozen before any comparison: `16_S8_3_FREEZE_MANIFEST.json`, `references_read: []`.

## Population

- **Two physical domes** are structural: DOME-A and DOME-B on the first-floor roof (terrace, +9.70).
  - Each has one closed ring beam, drawn as four segments between the framing beams.
  - The upper roof sheet and the architectural plan repeat their outlines; repeats are not counted again.
- **The tower dome** is architectural only (conflict CF-S8.3-01). It is not quantified.

## Released (PROJECT_BASIS_QTO)

- Concrete: **5.081361 m3**, the two shells. Each shell is 2.540681 m3: the solid between concentric spheres above the springing plane (chord 4.42 m, rise 1.90 m, thickness 0.10 m; outer radius 2.235289 m).
- Reinforcement: **602.111304 kg**, the shell mesh Ø12 at 150 mm, meridional and hoop, at a rate density over the mid-surface (25.401571 m2 per shell).
  - Unrounded, with no laps, hooks, anchorage or second mesh.
  - The fabrication count stays unresolved.

## Not released

- DOME-A RING_BEAM: SOURCE_CONFLICT. ring depth 'AS PER ARCH' (not established); ring plan position: plan band r 2211-2411 vs detail band under the shell edge (CF-S8.3-02, -03)
- DOME-A DRUM_BETWEEN_ROOF_AND_SPRINGING: BLOCKED_UNQUANTIFIED. architecture draws a 1.30 m drum; whether it is the RC ring itself or a wall under it is not stated
- DOME-B RING_BEAM: SOURCE_CONFLICT. ring depth 'AS PER ARCH' (not established); ring plan position: plan band r 2211-2411 vs detail band under the shell edge (CF-S8.3-02, -03)
- DOME-B DRUM_BETWEEN_ROOF_AND_SPRINGING: BLOCKED_UNQUANTIFIED. architecture draws a 1.30 m drum; whether it is the RC ring itself or a wall under it is not stated
- DOME-TOWER SHELL: SOURCE_CONFLICT. architectural only: no structural dome, thickness, ring or support (CF-S8.3-01)
- DOME-A SHELL_ANCHORAGE: BLOCKED_UNQUANTIFIED. leg length into the ring follows the 'AS PER ARCH' depth; the detail is N.I.S
- DOME-A RING_TOP: SOURCE_CONFLICT. ring centreline radius: plan 2311.1 vs detail 2111.1 (CF-S8.3-02); laps and continuity through the framing junctions; dome A ring segments also tagged B4 (2T12 / 4T16 schedule) (CF-S8.3-04)
- DOME-A RING_BOTTOM: SOURCE_CONFLICT. ring centreline radius: plan 2311.1 vs detail 2111.1 (CF-S8.3-02); laps and continuity through the framing junctions; dome A ring segments also tagged B4 (2T12 / 4T16 schedule) (CF-S8.3-04)
- DOME-A RING_SIDE: BLOCKED_UNQUANTIFIED. rows at 20 cm over a depth 'AS PER ARCH'
- DOME-A RING_LINKS: BLOCKED_UNQUANTIFIED. link size follows the ring depth; 8 / m along the ring is stated
- DOME-A RING_LAPS_AND_JUNCTIONS: BLOCKED_UNQUANTIFIED. no lap or junction detail with the framing beams and columns
- DOME-B SHELL_ANCHORAGE: BLOCKED_UNQUANTIFIED. leg length into the ring follows the 'AS PER ARCH' depth; the detail is N.I.S
- DOME-B RING_TOP: SOURCE_CONFLICT. ring centreline radius: plan 2311.1 vs detail 2111.1 (CF-S8.3-02); laps and continuity through the framing junctions
- DOME-B RING_BOTTOM: SOURCE_CONFLICT. ring centreline radius: plan 2311.1 vs detail 2111.1 (CF-S8.3-02); laps and continuity through the framing junctions
- DOME-B RING_SIDE: BLOCKED_UNQUANTIFIED. rows at 20 cm over a depth 'AS PER ARCH'
- DOME-B RING_LINKS: BLOCKED_UNQUANTIFIED. link size follows the ring depth; 8 / m along the ring is stated
- DOME-B RING_LAPS_AND_JUNCTIONS: BLOCKED_UNQUANTIFIED. no lap or junction detail with the framing beams and columns
- DOME-TOWER ALL: SOURCE_CONFLICT. no structural dome (CF-S8.3-01)

## Conflicts and questions

- **CF-S8.3-01** (OPEN (carries PS8-C01)): architecture draws a third dome (r 2205, chord 4.41 m, rise 2.15 m, springing +14.40) on the plan, both elevations and section B-B, but section A-A, which cuts the tower, draws none; structurally the place is the flat panel ['SP-2F_ROOF_SLAB-04'] that S7 releases. Not counted, not quantified.
- **CF-S8.3-02** (OPEN): the to-scale plan draws the 200 band outside the dome circle (r 2211.1-2411.1); the N.I.S detail puts the '442' span between the ring OUTER faces, the shell extrados meeting them, so the ring lies under the shell edge (r 2011.1-2211.1); section B-B draws the drum outer face on the dome outer face.
- **CF-S8.3-03** (OPEN): p.7 dimensions the ring depth 'AS PER ARCH'; architecture draws a drum 1.30 m above the +9.70 roof but not the ring bottom; the B4 schedule row (dome A tags) says 50 cm; the drawn N.I.S depth is never used.
- **CF-S8.3-04** (OPEN): two of dome A's four ring segments carry 'B4' tags (S6 bound them): B4 = 20 x 50 cm, top 2T12, bottom 4T16, 6T8/m; the DETAIL OF DOME (SEE DETAIL x4) gives 3T16 / 3T18 / 2T14@20 / 8T8/m. Dome B carries no tag.
- **CF-S8.3-05** (OPEN): NW elevation apex +12.409; SE elevation +12.849; section B-B +12.86 / +12.87. No quantity depends on it.
- **CF-S8.3-06** (RECORDED): the elevation profiles fit R 2193 / 2197 mm; a 4.42 m chord needs R >= 2.21 m; the structural cap is R 2.235 m. Form agrees, size differs slightly.
- **CF-S8.3-07** (RESOLVED_BY_DRAWING): S1 read 'two layers' from the two 'Ø12MM/15cm' labels; their leaders point one at the drawn meridional bar and one at the hoop dots: one mesh, two directions. A second mesh is a sensitivity case only.
- **CF-S8.3-08** (OPEN): dome A's circle (r 2211.1) crosses its side framing faces at x -2111 / 1989; dome B's at 2161: the shell edge / ring would bear partly on the side beams.
- **CF-S8.3-09** (RECORDED): section B-B '130' gives +11.00; the SE elevation's lower dimension line is +10.92. No quantity depends on it.
- **PS8-C02** (RESOLVED_BY_TRANSFER): all eight ring segments (BA001-BA008, six untagged + two tagged B4) transfer to S8.3 with 0 kg (05)
- **Q-S8.3-01** (OPEN): Engineer: give the ring beam depth and its plan position relative to the dome edge (outside the 4.42 m circle as on p.5, or under the shell edge as on p.7), and whether the 1.30 m drum is RC.
- **Q-S8.3-02** (OPEN): Engineer: do the 'B4' tags on dome A's ring apply, or does the DETAIL OF DOME govern both rings?
- **Q-S8.3-03** (OPEN): Architect / engineer: is the tower dome built (section A-A omits it), and in what material, thickness and support? Does the +13.90 slab under it change?
- **Q-S8.3-04** (OPEN): Engineer: anchorage of the shell bars into the ring, laps of the ring bars, and the junction detail with the framing beams and columns.

## Profile and levels

| item | value | state |
|---|---|---|
| terrace dome outer chord at the springing plane | 4.42 m | STATED_DIMENSION |
| terrace dome rise, springing to the outer apex | 1.9 m | STATED_DIMENSION |
| terrace dome shell thickness | 0.1 m | STATED_DIMENSION |
| profile of the drawn shell | SPHERICAL_ABOUT_AXIS  | ESTABLISHED |
| architectural terrace profile (SE elevation) | CIRCULAR  | CORROBORATES_FORM |
| architectural terrace profile (NW elevation) | CIRCULAR  | CORROBORATES_FORM |
| outer sphere radius from the stated chord and rise | 2.2353 m | DERIVED_FROM_STATED |
| centre of the sphere below the springing plane | 0.3353 m | DERIVED_FROM_STATED |
| horizontal shell width at the springing plane | 0.1012 m | DERIVED_FROM_STATED |
| terrace roof level (ring and drum stand on it) | 9.7 m | STATED_LEVEL |
| terrace dome springing level | 11 m | STATED_ON_ONE_SECTION |
| terrace dome apex level | 12.9 m | DERIVED_FROM_STATED |
| ring beam depth |  m | NOT_ESTABLISHED |
| tower dome chord at its springing | 4.41 m | ARCHITECTURAL_ONLY |
| tower dome rise | 2.15 m | ARCHITECTURAL_ONLY |
| tower dome shell thickness |  m | NOT_ESTABLISHED |
| openings in any dome shell | NONE_DRAWN  | ESTABLISHED |

## Exposure before the freeze

During source discovery, the frozen PRE-S8 census rows for the domes were printed in the session.
- One of their columns carries earlier commercial dome figures from an old Urban register.
- The builder does not read that file.
- No reading, convention or quantity here was chosen with reference to those figures.
- One sensitivity case (the tower dome with the terrace thickness, SA-TOWER-SHELL) lands close to one of them. It stays sensitivity only, and its 0.10 m comes from the terrace detail.
- The post-freeze comparison reports them.

## Outputs

- `00_README.md`
- `01_SOURCE_REGISTER.csv`
- `02_DOME_POPULATION.csv`
- `03_DOME_PROFILE_AND_LEVELS.csv`
- `04_RING_GEOMETRY.csv`
- `05_S6_TO_S8_3_OWNERSHIP_DELTA.csv`
- `06_CONCRETE_REGISTER.csv`
- `07_REBAR_NOTATION_REGISTER.csv`
- `08_REBAR_QTO_REGISTER.csv`
- `09_BLOCKED_COMPONENTS.csv`
- `10_SOURCE_CONFLICTS_AND_QUESTIONS.csv`
- `11_INTERFACE_AUDIT.csv`
- `12_SENSITIVITY_CASES.csv`
- `13_CONSERVATION_CHECKS.csv`
- `14_PROVENANCE.jsonl`
- `15_S8_3_SUMMARY.json`
- `16_S8_3_FREEZE_MANIFEST.json`
