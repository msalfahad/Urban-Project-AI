# PRE-S8: structural completeness audit, excavation to roof (2026-10-08)

This is an analysis round. No kg is calculated, no frozen stage moves, and S8 is not started. S7 stays at **3,802.015 kg**.

## What was searched

- 2253 ST7757.dxf texts, legacy Arabic decoded and assigned to sheets.
- 33 structural families, searched as a population (01_FAMILY_POPULATION_SEARCH.csv).
- The S1 census registers, the PRE-S7 panel census and the S1 rule register (pp.1-16).
- The architectural P7757.dxf, where an object appears only there.

## Census (02)

There are 400 physical elements or population records, in 450 census rows. The other rows are faces of an element, component evidence or typical-only details: {'COMPONENT_EVIDENCE': 11, 'CONFLICT_CANDIDATE': 1, 'ELEMENT': 393, 'FACE_OF_ELEMENT': 36, 'POPULATION_RECORD': 6, 'TYPICAL_DETAIL_ONLY': 3}.

Elements by family:

- BEAM: 133
- BOUNDARY_WALL: 1
- CANTILEVER_OR_BEARING_WALL: 9
- COLUMN: 59
- DOME: 3
- DOME_RING_BEAM: 6
- ELEVATED_SLAB: 41
- FOOTING: 25
- GROUND_BEAM: 59
- GROUND_SLAB: 1
- LEAN_BLINDING_CONCRETE: 1
- LIFT: 3
- LINTEL: 1
- NECK_PEDESTAL: 36
- OPENING_TRIM: 3
- RC_PARAPET: 3
- STAIR_AND_LANDING: 5
- STRAP_BEAM: 3
- SUNKEN_SLAB: 6
- SWIMMING_POOL: 1
- WATER_TANK: 1

28 whole elements have no S3-S7 owner and go to S8. Another 19 rows are components of owned elements that S8 would take (special-column extras, sunken extras, the dome ring arcs).

Previously omitted, unregistered or newly bound occurrences:

- PS8-BLINDING-UNDER-FOOTINGS: plain-concrete blinding. No S-stage register holds it; V3b measured it in two overlapping ways.
- PS8-LIFT-WALLS: the S1 LIFT_PIT had no plan location. The FF lift footing (4 columns) and the decoded schedule remark 'قاعدة مصعد' (lift base) now bind it.
- PS8-DOME-TOWER-ARCH-ONLY: an architectural tower dome over the flat structural panel SP-2F_ROOF_SLAB-04 (conflict PS8-C01).
- ARC:FFRS:BA003-BA008: dome ring beams that S6 holds as untagged beams (PS8-C02).

## Coverage (03, 04, 05)

- Concrete comes from the V3b BOQ lines and the coverage-recovery dashboard. Lines are copied with their own labels and never re-summed.
- Rebar comes from the S3.1, S4.1, S5.1, S6.1 and S7 component states.
- Stage totals (copied, not combined):
  - S3.1: 7,488.205 kg
  - S4.1 (+D1.2): 3,629.600 kg
  - S5.1 (+AD1, D1.1): 1,436.232 kg
  - S6.1 (+D1.1): 4,014.765 kg
  - S7 (+S7A errata): 3,802.015 kg

## Interfaces (07)

- FOOTING -> STARTER -> COLUMN: OWNED_ONCE_WATCH_BOXED
- GROUND BEAM -> COLUMN: OWNED_ONCE
- COLUMN -> BEAM: OWNED_ONCE_CONCRETE_REGISTER_OVERLAP
- BEAM -> SLAB: OWNED_ONCE
- SLAB -> STAIR: S8_MUST_EXCLUDE_S7_PORTION
- SLAB -> CANTILEVER: NOT_OWNED
- WALL -> FOUNDATION: NOT_OWNED
- LIFT WALL -> PIT BASE: PARTIAL_OWNERSHIP
- POOL WALL -> POOL BASE: NOT_OWNED
- TANK WALL -> TANK BASE: WALLS_ABSENT
- DOME -> SLAB / RING BEAM: TRANSFER_REQUIRED
- BLINDING (three Urban measures): CONCRETE_REGISTER_OVERLAP

## S8 readiness (10, 11)

- STAIR_AND_LANDING: BLOCKED_NEEDS_AUTHORITY
- LIFT_PIT_AND_WALLS: BLOCKED_NEEDS_AUTHORITY
- SWIMMING_POOL: READY_PARTIAL
- DOME_OR_SPECIAL_ROOF: READY_PARTIAL
- GROUND_SLAB: READY_PARTIAL
- WATER_TANK: READY_PARTIAL
- RC_PARAPET: BLOCKED_NEEDS_AUTHORITY
- LINTEL: READY_PARTIAL
- BOUNDARY_WALL: BLOCKED_NEEDS_AUTHORITY
- SPECIAL_COLUMN: READY_PARTIAL
- CANTILEVER_OR_BEARING_WALL_BAND: BLOCKED_NEEDS_AUTHORITY
- SUNKEN_EXTRAS_AND_STEPS: BLOCKED_NEEDS_AUTHORITY
- OPENING_TRIM: BLOCKED_NEEDS_AUTHORITY
- DOME_RING_BEAM: READY_PARTIAL

## Reproduce

```
python3 -I research/pre_s8_structural_completeness/build_pre_s8.py
```

The build is byte-identical on rebuild. It is blind: no external reference or comparison register is read.
