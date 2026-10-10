# S8.1A: ground-slab population recovery and cover-authority audit

Baseline `12cabc3`. This round releases **no** steel or concrete. S8.1 stays at 3.785852 m3 and 233.694587 kg, and no S8.1 file changes.

## Root cause of S8.1-PF-01

S1 tests one interior point per face. Face `RB-b5bf2906b114b4a7` (49.0742 m2) passes S1's area and thickness gates. Its point [21997.904, 16611.856] falls in ground-beam band `BL033`, so S1 dropped the whole face as a beam strip. The S-BW pit outlines close that band, but S1 did not use them as face edges.

## Recovered region

| part | lane | kind | m2 | owner |
|---|---|---|---|---|
| S8.1A-RG-01 | GROUND_SLAB_CANDIDATE | CELL_BETWEEN_MEMBERS | 11.9237 | SPC-GROUND_SLAB |
| S8.1A-RG-02 | STAIR_OR_SPECIAL_STRUCTURE | STAIR_FLIGHT_ZONE | 11.5200 | S8 STAIR (new element candidate: not in the PRE-S8 census) |
| S8.1A-RG-03 | GROUND_SLAB_CANDIDATE | CELL_BETWEEN_MEMBERS | 10.9742 | SPC-GROUND_SLAB |
| S8.1A-RG-04 | LIFT_PIT_OPENING | PIT_OPENING | 3.2400 | SPC-LIFT_PIT |
| S8.1A-RG-05 | GROUND_SLAB_CANDIDATE | CELL_BETWEEN_MEMBERS | 2.7212 | SPC-GROUND_SLAB |
| S8.1A-RG-06 | GROUND_SLAB_CANDIDATE | CELL_BETWEEN_MEMBERS | 2.2534 | SPC-GROUND_SLAB |
| S8.1A-RG-07 | STRUCTURAL_BEAM_OR_WALL | BEAM | 1.5060 | S5 GROUND_BEAM line BL033 (2 S1 occurrences) |
| S8.1A-RG-08 | GROUND_SLAB_CANDIDATE | CELL_BETWEEN_MEMBERS | 1.1875 | SPC-GROUND_SLAB |
| S8.1A-RG-09 | STRUCTURAL_BEAM_OR_WALL | BEAM | 0.9683 | S5 GROUND_BEAM line BL010 (2 S1 occurrences) |
| S8.1A-RG-10 | STRUCTURAL_BEAM_OR_WALL | BEAM | 0.8700 | S5 GROUND_BEAM line BL029 (1 S1 occurrences) |
| S8.1A-RG-11 | STRUCTURAL_BEAM_OR_WALL | BEAM | 0.8100 | S5 GROUND_BEAM line BL030 (1 S1 occurrences) |
| S8.1A-RG-12 | STRUCTURAL_BEAM_OR_WALL | WALL | 0.3600 | PS8-LIFT-WALLS |
| S8.1A-RG-13 | STRUCTURAL_BEAM_OR_WALL | WALL | 0.3600 | PS8-LIFT-WALLS |
| S8.1A-RG-14 | STRUCTURAL_BEAM_OR_WALL | WALL | 0.2400 | PS8-LIFT-WALLS |
| S8.1A-RG-15 | STRUCTURAL_BEAM_OR_WALL | WALL | 0.1400 | PS8-LIFT-WALLS |
| S8.1A-RG-16 | CLASSIFICATION_BLOCKED | SLIVER | 0.0000 | UNOWNED |

Gross 49.0742 m2. Candidate slab 29.0599 m2 (blocked: no thickness or mesh). Confirmed slab 0 m2. Lift-pit opening 3.2400 m2. Structural 5.2543 m2. Stair zone 11.5200 m2. Unclassified 0.38 mm2 (S8.1A-RG-16: sliver on 1|17E, kept as CLASSIFICATION_BLOCKED).

## TT1 scope

Verdict: **ANNOTATION_SCOPE_NOT_ESTABLISHED**. The two-cell S8.1 measurement is kept as a versioned Urban project-basis interpretation (I1). It is not presented as the only possible project interpretation (04).

## Cover

Contact: **CONTACT_CONDITION_UNRESOLVED**. Verdict: **COVER_APPLICABILITY_UNRESOLVED**. E.W. is one mesh of two crossing directions. A 100 mm slab cast against soil would need 70 + 10 + 10 + 25 = 115 mm. Off soil it needs 25 + 10 + 10 + 25 = 70 mm. Neither contact case is established, so S8.1's SOURCE_CONFLICT is corrected to unresolved in the correction layer (06). No bar level is invented.

## Conservation

Drawn ground-slab domain 225.075663 m2 = measured 37.858523 + blocked 158.830499 + excluded 28.386640 + conflicted 0.000000 + unclassified 0.000000.

Outputs 01-13 and the freeze manifest 14 are listed in the manifest.
