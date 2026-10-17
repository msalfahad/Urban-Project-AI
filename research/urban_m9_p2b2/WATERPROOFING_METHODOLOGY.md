# Waterproofing methodology - ARCH_TAKEOFF_V2.4 (deliverable 5)

Program Part 3. Code: `engine/source/wp_geometry.py` (boundary), `engine/source/waterproofing_system.py` (areas,
transitions, penetrations, layout, cutting plan, schedule, BOQ lines); the layout engine
`engine/source/membrane_layout.py` is reused unmodified. Rules (registry 1.1.0): UP-WP-001 .. -004, UP-WP-DOOR-001,
UP-WP-MAT-001, UP-WP-LAY-001, UP-WET-001, UP-WP-ROOF-001. Tests: `tests/m9_p2b2/test_p2b2_waterproofing.py` (20).

## 1. The approved standards (Level A) and how a project overrides them (Level B)

| Rule | Standard | Overridden by |
|---|---|---|
| UP-WP-001 | roll 1.00 x 10.00 m = 10.00 m2 gross | a project roll width / length, or a project membrane system |
| UP-WP-002 | 0.10 m overlap at the joints between adjacent strips (side and end laps); never a flat 10 % waste | a project lap |
| UP-WP-003 | 0.20 m upturn along eligible wall boundaries (supersedes the general 0.15 m upturn, UP-WP-UPTURN-015, kept as DEPRECATED with its history) | a project upturn height (detail / specification), by scope |
| UP-WP-004 | drains, pipes, outlets, roof drains, corners, interruptions treated by the system detail; their dimensions and counts never invented | a project penetration / corner treatment |
| UP-WP-DOOR-001 | doorway transitions modelled on their own, never door width x 0.20 m blindly | a project doorway detail |

The value used for each area is resolved through the Project Engineering Rules Sheet (`RULES_SHEET_GENERATOR.md`); its
state (OWNER_STANDARD_ASSUMED, PROJECT_SPECIFIED, CONFLICT_REVIEW ...) is written on the line.

## 2. Which areas

Every space with a measured FIN.WP.FLOOR line: the owner wet scope (bathrooms / WCs, kitchens, pantries, ironing;
laundries once the project confirms them - UP-WET-001; now with a membrane layout for every one of them), balconies and roofs (UP-WP-ROOF-001). Wet
areas use the system group URBAN_DEFAULT_WET_AREA, exterior areas URBAN_DEFAULT_EXTERIOR; a project system
(UP-WP-MAT-001) names its own group. **Two systems are never added together.**

## 3. The boundary, edge by edge (`wp_geometry`)

1. Typed features on the floor: wall faces (wall layers), column sides, the two faces of every band opening (DOOR,
   PASSAGE, WINDOW_THRESHOLD), door closures, zone lines of an open-plan wet zone, glazing lines (window layer).
2. The room ring is cut into runs of one role. Where features coincide the priority is DOOR > PASSAGE >
   WINDOW_THRESHOLD > GLAZING > ZONE_LINE > COLUMN > WALL; an edge no feature explains is OTHER (an open edge).
   A window-layer line lying on the face of a recognised window opening is its frame / sash, not floor-level glazing
   (corrected in this phase after the reference plan: see `INDEPENDENT_REVIEW.md` D-04).
3. Upturn-eligible: WALL, COLUMN, WINDOW_THRESHOLD (the sill wall below a window - a floor-level window is the
   window-type question). Breaks: DOOR, PASSAGE, GLAZING, ZONE_LINE, OTHER.
4. Corners on the outer ring (counter-clockwise): a left turn is INTERNAL, a right turn EXTERNAL; obstruction rings
   (columns, shafts inside the area) are inverted. Upturn ends at every break are counted separately.
5. Runs: one closed loop, or the open runs between breaks.
6. Check: the segmentation must lie between the plan's own boundary-role upturn (V2.3 room runs) and that plus its
   glazing edge; outside that band the area keeps the boundary-role value, raises WP_BOUNDARY_SEGMENTATION_REVIEW
   (E) and its corners are not released.

## 4. The three quantities

| | Quantity | How |
|---|---|---|
| **A** | net horizontal area | the FIN.WP.FLOOR line (the waterproofed floor polygon, holes out) |
| **B** | installed membrane | A + wall upturn (eligible length x upturn height) + doorway continuation pieces + resolved transitions + laps (from the layout) |
| **C** | procurement | whole rolls of the project cutting plan of the system (section 6); never A / 10, never a waste percentage |

Kept apart on every row: consumed (cut from rolls), cutting waste (consumed - installed), untouched roll tails,
retained offcuts (only with a project minimum reusable width, UP-WP-LAY-001), packaging surplus.

## 5. Doorways and other breaks (UP-WP-DOOR-001, UP-WP-003)

| Situation | Treatment |
|---|---|
| doorway between two waterproofed spaces | DOORWAY_CONTINUATION: the membrane runs through (the doorway piece, counted once); no vertical item |
| doorway to a dry / exterior / not-established side | DOOR_THRESHOLD_TRANSITION with three alternatives: UPTURN_ACROSS_THRESHOLD = w x h m2; CONTINUATION_TERMINATED = 0 m2 + w lm termination; JAMB_RETURNS = 2 x t x h m2 + w lm termination |
| project doorway detail given | the selected alternative is released (RESOLVED_BY_DETAIL, PROJECT_SPECIFIED) |
| no detail | UNRESOLVED: FIN.WP.DOORWAY_TRANSITION as BOUNDED_EXPOSURE (low .. high of the alternatives), DOORWAY_WP_TRANSITION_DETAIL_REQUIRED (B); never in a confirmed total |
| passage / zone line to another waterproofed space | continuation, no item |
| glazing edge, passage to a dry side, open edge | FIN.WP.TERMINATION (lm) by the termination detail; without one BOUNDED_EXPOSURE, WP_TERMINATION_DETAIL_REQUIRED (B) |

The floor continuation piece (FIN.WP.DOORWAY, the approved owner method kept from the rule store) is horizontal; every
transition alternative is vertical or a termination length, so nothing is counted twice (`BEFORE_AFTER_BOQ.md` section 4).

## 6. Layout and cutting plan (UP-WP-LAY-001)

Per area, `membrane_layout`'s polygon strips are evaluated in **both orientations** (ALONG_X, ALONG_Y): floor strips
with side laps, the upturn band (h + lap) cut into lanes of the roll width, doorway pieces, end laps. Selection is
deterministic: fewest rolls (area alone), then fewest seams, then least consumed membrane, then ALONG_X before ALONG_Y;
both alternatives are reported. A polygon is laid as a polygon (an L-shape, a kitchen, an irregular roof), not as its
bounding box - the same 6 m2 laid as 2.40 x 2.50 m needs 1 roll, as 3.00 x 2.00 m or 6.00 x 1.00 m 2 rolls
(`MEMBRANE_CUTTING_REPORT.md`).

The project cutting plan takes every full-width piece of every computed area of one system group and cuts them from
shared rolls, **first fit decreasing** (length descending, then room id), deterministic. A roll remainder is reused
only where the plan places a piece in it - the reuse is listed piece by piece; no offcut is credited that the plan does
not cut. The synthetic villa: 6 rolls for three areas, 7 if each area were installed alone.

## 7. Penetrations, corners, detailing

- Penetrations are counted from the drawing: blocks and texts inside the area matching floor drain / gully / trap,
  roof drain / rainwater / scupper, pipe sleeve / soil stack, outlet / clean-out (a label next to its block counts
  once). Sanitary fixtures are listed as indicative only (a WC symbol does not establish an outlet through the
  membrane). Nothing found: NOT_SHOWN, count **None** (never 0), FIN.WP.PENETRATION BLOCKED_RFI,
  WP_PENETRATIONS_NOT_SHOWN (B). Counted but no treatment: WP_PENETRATION_DETAIL_REQUIRED (B).
- Corners (internal / external from the polygon) are listed; their reinforcement waits for the system detail
  (WP_CORNER_DETAIL_REQUIRED).
- Every withheld item is listed with the cutting plan; none is added to the roll count.

## 8. When a roll count is CONFIRMED

Only when the membrane system is specified for every area of the group (UP-WP-MAT-001) **and** no detailing item of
the group is withheld. Otherwise the plan is PROVISIONAL and states why (`why_not_confirmed`); the owner-standard roll
alone is not a basis for a confirmed count (`test_roll_count_never_confirmed_without_a_valid_basis`).

## 9. Outputs

`WATERPROOFING_SCHEDULE.json/.csv` (per room, per floor, project; per system, never summed across systems),
`MEMBRANE_CUTTING_PLAN.json` (rolls and pieces), BOQ lines FIN.WP.WALL_UPTURN (m2), FIN.WP.DOORWAY_TRANSITION (m2),
FIN.WP.TERMINATION (lm), FIN.WP.PENETRATION (pcs) next to the unchanged FIN.WP.FLOOR and FIN.WP.DOORWAY, the
WATERPROOFING_PROCUREMENT view in `BOQ_SCENARIOS.json`, the ledger table ELIGIBILITY_V0_3_WP_SYSTEM.

## 10. Limits

- The lap direction (shingle order towards the drain) and the falls are not modelled; laps are counted, not oriented.
- A window threshold is upturned on the assumption of a sill wall; a floor-level window or a glazed door drawn on a
  window layer inside a recognised window opening is only caught by the window-type question.
- Penetrations drawn as plain geometry (circles without a block or label) are not read.
- The roof / balcony system is the exterior default until a specification names it; parapet heights and fall
  screeds are outside this route.
