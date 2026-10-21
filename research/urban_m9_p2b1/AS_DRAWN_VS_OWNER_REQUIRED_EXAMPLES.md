# As-drawn versus owner-required BOQ examples (deliverable 7)

The AS_DRAWN view is what the drawing establishes; the OWNER_REQUIRED view is the same doors under the owner opening
standard (UP-DOOR-OPEN-002) - a proposed modification, never approved by the engine and never added to AS_DRAWN.
Source files of every run: `DOOR_SCENARIOS.json` / `.csv`, `BOQ_SCENARIOS.json`.

## 1. Synthetic villa (tools/arch_synth; every value checkable from the coordinates), door by door

Heights: run U - no heights given (owner reference 2.20 m, ASSUMED); run A - a schedule height 2.10 m (SOURCE).

| Door | Category | CAD wall opening | Owner-required wall opening | Enlargement | Nominal door | Height (U / A) | AS_DRAWN area U / A (m2) | OWNER_REQUIRED area U / A (m2) | View |
|---|---|---|---|---|---|---|---|---|---|
| GF living - bathroom | BATHROOM_PVC | 0.80 | 1.00 | +0.20 | 0.90 | 2.20 ASSUMED / 2.10 SOURCE | 1.76 ASSUMED / 1.68 CONFIRMED | 2.20 ASSUMED / 2.10 CONFIRMED | AS_DRAWN |
| GF living - kitchen | INTERNAL_PVC | 0.90 | 1.10 | +0.20 | 1.00 | same | 1.98 ASSUMED / 1.89 CONFIRMED | 2.42 ASSUMED / 2.31 CONFIRMED | AS_DRAWN |
| GF living - bedroom | INTERNAL_PVC | 0.90 | 1.10 | +0.20 | 1.00 | same | 1.98 ASSUMED / 1.89 CONFIRMED | 2.42 ASSUMED / 2.31 CONFIRMED | AS_DRAWN |
| 1F corridor - master bedroom | INTERNAL_PVC | 0.90 | 1.10 | +0.20 | 1.00 | same | 1.98 ASSUMED / 1.89 CONFIRMED | 2.42 ASSUMED / 2.31 CONFIRMED | AS_DRAWN |
| 1F bathroom - corridor | BATHROOM_PVC | 0.80 | 1.00 | +0.20 | 0.90 | same | 1.76 ASSUMED / 1.68 CONFIRMED | 2.20 ASSUMED / 2.10 CONFIRMED | AS_DRAWN |
| GF living - outside (1.00 m) | MAIN_ENTRANCE_CANDIDATE | 1.00 | 1.00 (as drawn) | 0 | - | 2.20 ASSUMED / 2.10 SOURCE | withheld | withheld | UNRESOLVED |

Totals (released doors): AS_DRAWN - 5 doors, 4.30 m of wall opening, 9.46 m2 ASSUMED (U) / 9.03 m2 CONFIRMED (A);
OWNER_REQUIRED - 5 doors below the standard, +1.00 m of total enlargement, 5.30 m of wall opening, 11.66 m2 ASSUMED
(U) / 11.13 m2 CONFIRMED (A). The two views are reported side by side and never summed.

Each enlarged door lists its dependent trades for review (openings, masonry, wall finish per side, skirting on a dry
side, head / reveal plaster, threshold - marble on a wet side - and doorway waterproofing, lintel span); none of them
changes a BOQ line.

## 2. The owner's corrected examples (unit level; `test_the_owner_correction_table`)

| CAD | Category | AS_DRAWN | OWNER_REQUIRED | Note |
|---|---|---|---|---|
| 0.90 | internal PVC | 0.90 | 1.10 (+0.20) | the 10 cm is already inside 1.10: never 1.20 |
| 0.90 | bathroom PVC | 0.90 | 1.00 (+0.10) | |
| 1.00 | external aluminium | 1.00 | 1.10 (+0.10) | |
| 1.20 | internal PVC | 1.20 | 1.20 (0) | nominal door 1.10 (RULE_DERIVED: CAD - 0.10) |

## 3. Reference plan (aggregate only)

| View | Category | Doors | Wall opening (m) | Enlargement (m) | Area, no heights (m2) | Area, heights given (m2) |
|---|---|---|---|---|---|---|
| AS_DRAWN | DOOR.INTERNAL.PVC (incl. bathrooms) | 14 | 12.20 | - | 26.84 ASSUMED | 25.62 CONFIRMED |
| AS_DRAWN | DOOR.EXTERNAL.ALUMINIUM | 2 | 1.90 | - | 4.18 ASSUMED | 3.99 CONFIRMED |
| OWNER_REQUIRED | INTERNAL_PVC | 7 (7 below standard) | 7.70 | +1.10 | 16.94 ASSUMED | 16.17 CONFIRMED |
| OWNER_REQUIRED | BATHROOM_PVC | 7 (7 below standard) | 7.00 | +1.40 | 15.40 ASSUMED | 14.70 CONFIRMED |
| OWNER_REQUIRED | EXTERNAL_ALUMINIUM | 2 (2 below standard) | 2.20 | +0.30 | 4.84 ASSUMED | 4.62 CONFIRMED |
| UNRESOLVED | 6 provisional widths, 2 main-entrance candidates, 1 class review, 2 class unresolved, 1 held aluminium | 12 | - | - | withheld | withheld |
| EXCLUDED | elevator | 0 door elements (3 landing openings on the elevator schedule) | - | - | - | - |

"Heights given" is the private synthetic heights facts file of the regression runs (a SOURCE height for doors), not
a schedule of the project; it shows how the same doors move from ASSUMED to CONFIRMED areas when a source exists.

## 4. Other BOQ scenarios

`BOQ_SCENARIOS.json` carries three views of every run: AS_DRAWN (the BOQ lines by item and state - PROVISIONAL is
never confirmed), OWNER_REQUIRED (the door view above; knowledge registry 1.0.0 defines no other owner-required
modification) and UNRESOLVED (lines without a quantity, withheld doors, question groups). The wet-area scope, the
thresholds, the jamb plaster and the waterproofing are not "owner-required modifications": they are how the drawn
building is measured under approved rules, so they are AS_DRAWN lines (see `BEFORE_AFTER_COMPARISON.md`).
