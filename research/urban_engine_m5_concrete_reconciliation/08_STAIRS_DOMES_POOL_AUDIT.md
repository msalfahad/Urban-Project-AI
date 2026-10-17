# 08 Stairs, domes, pool and specials (investigations E + F)

## Stairs

| Family | Floor | Part | FL m3 | U low | U base | U high | U cond. high | Class |
|---|---|---|---|---|---|---|---|---|
| STAIRS | ALL | ST-A | 8.13 | 4.95 | 5.17 | 6.46 | 0.00 | ASSUMPTION_DIFFERENCE |
| STAIRS | ALL | ST-B | 0.00 | 0.00 | 0.29 | 0.55 | 0.00 | MISSING_IN_FREELANCER |
| STAIRS | ALL | ST-C | 5.51 | 2.61 | 2.72 | 3.16 | 0.00 | ASSUMPTION_DIFFERENCE |
| STAIRS | ALL | ST-D | 1.41 | 0.00 | 0.88 | 1.97 | 0.00 | ASSUMPTION_DIFFERENCE |

There are four drawn stairs (S8.7):

- **ST-A main stair:** GF -> 1F -> 2F; two flights, a winder turn and a half-landing per storey.
- **ST-B lobby steps:** 4 risers, +1.00 -> +0.30.
- **ST-C light-well stair:** curved flight, straight flight, corner landing, short flight.
- **ST-D entrance steps:** 5 risers, +0.15 -> +1.00.

How the freelancer's rows map:

- its main stair (4 flights x 5.3 m + 3 landings) is ST-A;
- its 'entrance stair' is ST-D;
- its 'stair 2' (16.4 m x 1.2 m) is ST-C;
- ST-B has no row.

Every freelancer row uses a 0.28 m 'steps + waist slab' equivalent over the plan length.

Urban integrates each drawn flight, winder and landing at the waist range: 7.56 - 12.13 m3, base 9.06. The waist is not printed (p.16 'THICK' has no value), so it is RFI-M5-06. The GF -> 1F riser arrangements of S8.7A-C stay research only; none is an approved quantity.

## Domes

| Family | Floor | Part | FL m3 | U low | U base | U high | U cond. high | Class |
|---|---|---|---|---|---|---|---|---|
| DOMES | ROOF | DRUMS | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | UNRESOLVED_REQUIRES_ENGINEER |
| DOMES | ROOF | RINGS | 0.00 | 1.65 | 1.65 | 6.38 | 0.00 | MISSING_IN_FREELANCER |
| DOMES | ROOF | SHELLS | 6.78 | 5.08 | 5.08 | 5.08 | 0.00 | GEOMETRY_DIFFERENCE + SCOPE_DIFFERENCE |
| DOMES | ROOF | TOWER | 0.00 | 0.00 | 0.00 | 0.00 | 2.84 | UNRESOLVED_REQUIRES_ENGINEER |

**Different components, near-equal totals.** The numeric closeness is not agreement.

- **The freelancer** prices three shells of 22.6 m2 x 0.10, about a hemisphere on the 1.90 m rise.
- **Urban** measures the two drawn domes as spherical caps (printed 4.42 m chord, 1.90 m rise, 0.10 thick: S8.3) and their ring beams (depth 'AS PER ARCH': range).
- **Held as UNRESOLVED by Urban:**
  - the tower dome (architecture only);
  - the 1.30 m drums.

## Pool, lift, specials

| Family | Floor | Part | FL m3 | U low | U base | U high | U cond. high | Class |
|---|---|---|---|---|---|---|---|---|
| GB_PERIMETER | GROUND | PERIMETER | 8.60 | 0.00 | 0.00 | 0.00 | 3.17 | SOURCE_CONFLICT |
| LINTELS | 1F | ALL | 0.00 | 0.23 | 0.25 | 0.26 | 1.00 | MISSING_IN_FREELANCER |
| LINTELS | 2F | ALL | 0.00 | 0.00 | 0.00 | 0.00 | 0.43 | MISSING_IN_FREELANCER |
| LINTELS | GF | ALL | 0.00 | 0.20 | 0.22 | 0.23 | 1.98 | MISSING_IN_FREELANCER |
| POOL | GROUND | BASE | 4.32 | 4.37 | 4.37 | 4.37 | 0.00 | MATCHED_WITHIN_TOLERANCE |
| POOL | GROUND | STEPS | 0.23 | 0.00 | 0.00 | 0.00 | 0.00 | SCOPE_DIFFERENCE |
| POOL | GROUND | WALLS | 4.32 | 2.12 | 2.71 | 3.06 | 0.00 | HEIGHT_OR_LEVEL_DIFFERENCE |
| POOL_PUMP_ROOM | GROUND | PUMP_ROOM | 3.48 | 0.00 | 0.00 | 0.00 | 0.00 | SCOPE_DIFFERENCE |
| LIFT | FOUNDATION | OVERRUN | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | UNRESOLVED_REQUIRES_ENGINEER (in neither base) |
| LIFT | FOUNDATION | PIT_WALLS | 2.40 | 2.15 | 2.15 | 2.69 | 0.00 | GEOMETRY_DIFFERENCE |
| LIFT | FOUNDATION | TIE-GF | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | UNRESOLVED_REQUIRES_ENGINEER (in neither base) |
| CANTILEVER_PORTIONS | 1F | S9A-CP-05 | 0.00 | 0.00 | 0.00 | 0.00 | 0.22 | MISSING_IN_FREELANCER |
| CANTILEVER_PORTIONS | 2F | S9A-CP-06 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | MISSING_IN_FREELANCER |
| CANTILEVER_PORTIONS | 2F | S9A-CP-07 | 0.00 | 0.00 | 0.00 | 0.00 | 0.10 | MISSING_IN_FREELANCER |
| CANTILEVER_PORTIONS | 2F | S9A-CP-08 | 0.00 | 0.00 | 0.00 | 0.00 | 0.04 | MISSING_IN_FREELANCER |
| CANTILEVER_PORTIONS | GF | S9A-CP-02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.02 | MISSING_IN_FREELANCER |
| CANTILEVER_PORTIONS | GF | S9A-CP-03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.19 | MISSING_IN_FREELANCER |
| CANTILEVER_PORTIONS | GF | S9A-CP-04 | 0.00 | 0.00 | 0.00 | 0.00 | 0.12 | MISSING_IN_FREELANCER |
| WATER_TANK | 2F | S8.4-C-01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | UNRESOLVED_REQUIRES_ENGINEER |
| WATER_TANK | 2F | S8.4-C-02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | UNRESOLVED_REQUIRES_ENGINEER |
| WATER_TANK | 2F | S8.4-C-TANK_BASE | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | UNRESOLVED_REQUIRES_ENGINEER |
| WATER_TANK | 2F | S8.4-C-TANK_WALLS | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | UNRESOLVED_REQUIRES_ENGINEER |
| BOUNDARY_WALL | SITE | BEAM | 7.56 | 0.00 | 0.00 | 0.00 | 5.29 | SCOPE_DIFFERENCE |
| PARAPETS | ROOF | S9-PARAPET-1F_ROOF | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | UNRESOLVED_REQUIRES_ENGINEER |
| PARAPETS | ROOF | S9-PARAPET-2F_ROOF | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | UNRESOLVED_REQUIRES_ENGINEER |
| PARAPETS | ROOF | S9-PARAPET-GF_ROOF | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | UNRESOLVED_REQUIRES_ENGINEER |

- **Pool:**
  - the base matches;
  - the walls differ by height, because the floor profile is a PROFILE_CONFLICT between the architectural flat floor and the structural deep end / slope;
  - the steps and the pump room are not drawn on any sheet (S8.2 source search), so they are UNRESOLVED and never assumed absent;
  - the curved ground beam around the pool (R 2250 +) is a separate element from the pool wall (R 1550 / 1750, 500 mm gap; S8.2A) and is counted once.
- **Lift:**
  - the four 200 mm pit walls (S8.8) are the freelancer's 'lift walls';
  - Urban measures the drawn pieces to the founding range;
  - the GF tie beam and the overrun are not drawn;
  - the lift footing FF is a footing (07).
- **Water tank:**
  - the roof slabs are in the 2F slabs (D-01);
  - the base and walls are not drawn.
- **Cantilever portions:** the hatched bands of S9A, at the adjacent slab thickness, CONDITIONAL (D-04).
- **Parapets:** architecture only.

Figures: `visual/05_STAIRS_DOMES.svg`, `visual/06_POOL_SPECIAL_SCOPE.svg`.

