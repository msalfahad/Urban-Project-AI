# Door feasibility methodology - ARCH_TAKEOFF_V2.4 (deliverable 7)

Program Part 4. Code: `engine/source/door_feasibility.py` over the door model (`door_model`, `door_standards`, both
unchanged) and the floor geometry; rules UP-DOOR-FEAS-001, UP-DOOR-OPEN-002, UP-DOOR-HGT-001, UP-DOOR-AREA-001,
UP-DOOR-DEP-001 (registry 1.1.0). Tests: `tests/m9_p2b2/test_p2b2_door_feasibility.py` (17) and the jamb-plaster CLI
test. A door-by-door example: `DOOR_SCHEDULE_SYNTHETIC_VILLA.md`; the four views: `AS_DRAWN_VS_OWNER_STANDARD.md`.

**Clearance is geometry, never structural approval. No row recommends cutting a column, a beam or a structural wall.
A proposed modification is never an as-drawn quantity.**

## 1. Standards (Level A, owner-approved; Level B project rules override within scope)

| Category | Nominal door | Required wall opening (nominal + 0.10 m) | Height (OWNER_STANDARD_ASSUMED) |
|---|---|---|---|
| internal PVC | 1.00 m | 1.10 m | 2.20 m |
| bathroom PVC | 0.90 m | 1.00 m | 2.20 m |
| external aluminium | 1.00 m | 1.10 m | 2.20 m |
| main entrance | the project's own dimensions (no ordinary standard applied) | - | 2.50 m |
| elevator landing | excluded (elevator quotation schedule, UP-DOOR-CLS-005) | - | not established |

Heights are never labelled DRAWING_MEASURED; a source height (facts) or a project rule replaces the owner standard
and says so.

## 2. Per door

1. **CAD wall opening** - the band opening measured jamb to jamb (as drawn; never altered).
2. **Required opening** - from the standard (or the project rule) for the door's category.
3. **Max nominal door as drawn** - CAD opening - allowance (bathroom 0.80 m opening -> 0.70 m door).
4. **Compliance** - MEETS_STANDARD, ENLARGEMENT_REQUIRED (enlargement = required - CAD), NOT_APPLICABLE.
5. **Clearances** on each side of the opening along its wall (START / END), read up to 3.00 m (REACH_M): the plain wall
   until the first constraint - COLUMN, another OPENING, a JUNCTION (a wall joining or crossing), a CORNER, a
   WALL_END, or OPEN_RUN (no constraint within the reach: the value is a lower bound,
   `max_feasible_is_lower_bound`). Both faces of the wall are read; the smaller governs.
6. **Pier** - a 0.10 m minimum pier is kept beside an enlarged jamb against a junction / corner / wall end / opening.
   This is an ENGINE_REVIEW_THRESHOLD shown as ENGINE_LIMITATION on the rules sheet, not an owner standard; a project
   rule (UP-DOOR-FEAS-001 min_pier_m) replaces it.
7. **Placements** that fit the available wall: SPLIT_EQUAL, START_SIDE, END_SIDE, else UNEQUAL; the pier left on each
   side is reported.
8. **Swing** - the quarter disc the larger (owner-standard) leaf sweeps about its hinge, the hinge moved with the
   enlarged jamb, checked against walls, columns and drawn fixtures on the swing side; the drawn leaf is checked too
   (`as_drawn`). A swing symbol whose closed leaf lies outside the jambs is SWING_SYMBOL_INCONSISTENT - reported, not
   evaluated; a double leaf is not re-evaluated.
9. **Host wall structure** - STRUCTURAL / NON_STRUCTURAL_SPECIFIED only from a project rule (structural drawings);
   MASONRY_INDICATED where the plan draws a column frame and the wall is on a masonry layer (not verified); UNKNOWN
   where no column frame is drawn.
10. **Beyond the enlarged jamb** - the spaces on both faces; a stair, shaft or lift there constrains the enlargement.
11. **Dependency impacts** of the enlargement (UP-DOOR-DEP-001): opening area, blockwork deduction, plaster / paint
    on each side by its wet / dry scope, skirting, head soffit and reveals, threshold - carried with the proposal,
    never applied to the as-drawn lines.

## 3. Classes

| Class | When |
|---|---|
| STANDARD_FITS_AS_DRAWN | the CAD opening meets the required opening; the main entrance (project dimensions govern) |
| ENLARGEMENT_GEOMETRICALLY_POSSIBLE | a placement fits the plain wall, the host wall is MASONRY_INDICATED or NON_STRUCTURAL_SPECIFIED, the larger swing is clear, no stair / shaft / lift at the enlarged jamb |
| ENLARGEMENT_CONSTRAINED | not enough plain wall; or the larger swing meets a wall / column / fixture; or a stair / shaft / lift lies at the enlarged jamb (the governing reason is listed first) |
| ENLARGEMENT_REQUIRES_ENGINEERING_REVIEW | the plain wall allows it but the host wall is STRUCTURAL or UNKNOWN; or columns on both sides (only a structural alteration would widen it - never recommended) |
| INSUFFICIENT_DRAWING_EVIDENCE | category not settled (main-entrance candidate, class review); width not confirmed (provisional / held conflicting dimensions); no band opening read; the applicable standard in conflict |

## 4. Views and approvals

AS_DRAWN (released doors as drawn - the BOQ door lines), OWNER_STANDARD (what each requires), PROPOSED_MODIFICATION
(the enlargement and its class, status MODIFICATION_PROPOSED_NOT_APPROVED), UNRESOLVED, EXCLUDED (elevators) - never
added together. Each proposal lists who must approve it: owner / architect (the design change); a structural engineer
(host wall and lintel - always when MASONRY_INDICATED, a review when STRUCTURAL / UNKNOWN); for a constrained door the
owner / architect choice of a smaller door or a redesign. `APPROVALS_REQUIRED.json` collects them.

## 5. Door jamb plaster by category height

The V2.3 jamb / head plaster line (UP-FIN-PLASTER-001: 2 x wall t x H + t x w) is rebuilt at each door's category
height: internal / bathroom PVC and external aluminium 2.20 m, the main entrance 2.50 m (OWNER_STANDARD_ASSUMED); a
main-entrance candidate is a BOUNDED_EXPOSURE between the 2.20 and 2.50 m results (JAMB_HEIGHT_CLASS_PENDING, B);
an elevator landing is not established (JAMB_HEIGHT_NOT_ESTABLISHED). V2.3 took every jamb at 2.20 m.

## 6. Example (the owner's)

Bathroom door, CAD wall opening 0.80 m: required opening 1.00 m (0.90 m door + 0.10 m); max nominal door as drawn
0.70 m; enlargement +0.20 m; compliance ENLARGEMENT_REQUIRED - never treated as fitting
(`test_bathroom_0_80_needs_0_20_and_is_not_treated_as_fitting`).

## 7. Limits

- Lintels, beams over the opening and the wall's real structural role are not read from the architectural plan.
- A column frame drawn on the plan is taken as a sign of a framed structure (MASONRY_INDICATED), not as proof.
- The swing check covers the drawn walls, columns and fixture blocks of the floor; furniture, radiators, sockets and
  services in the wall are not read.
- Double-leaf doors and sliding doors are not re-swung; an inconsistent swing symbol is reported only.
