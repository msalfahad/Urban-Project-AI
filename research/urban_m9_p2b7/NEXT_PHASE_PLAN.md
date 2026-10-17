# Next development phase: plan only (Phase 2B-7 Section 7)

**No broad implementation.** This is a plan. Every item would be a new opt-in method (ARCH_TAKEOFF_V2.8, or a
structural / site method) that keeps V1 – V2.7 byte-identical, built in the same order as V2.7:

1. acceptance tests with independently derived truth;
2. then the engine change;
3. then the reference plan;
4. then a difference explainer that leaves nothing unexplained.

**Measurement rules.** Where one is stated below without an owner source, it is a **proposal for confirmation**, not
a policy.

## Priority and dependencies

| order | item | why this position | depends on |
|---|---|---|---|
| **P1** | heights from sections, elevations and schedules | every wall-area line (plaster, paint, wall porcelain, masonry) and every opening area rests on heights; today they are synthetic test facts (D-C5, D-04) | nothing new: the drawings exist; section reading is new |
| **P2** | window and glazing areas | windows are counted, not measured: aluminium is a large cost family, and window areas also deduct from wall finishes | P1 (sill and head heights) |
| **P3** | combined architectural + structural BOQ export | the structural route (G) and the architectural route already emit canonical lines. One workbook and one traceability chain make every later item reviewable. Low risk: no new geometry | the canonical line schema (exists) |
| **P4** | structural formwork | large cost item. The concrete member geometry already exists in route G | route G members; P1 for storey heights; P3 to present it |
| **P5** | roof, balcony and external paving | roof waterproofing exists as a scope; the areas, falls and edge details need the roof plan and levels | P1 (levels), the roof plan reader |
| **P6** | excavation and backfill | needs site levels (natural ground, formation), working space and the foundation geometry. It has the least drawing evidence in typical sets and the most conventions to confirm | route G foundations; site levels; owner conventions |

## P1: heights

**Measurement rules.**

- Wall finish height is from the finished floor level to the ceiling (or slab soffit where there is no ceiling),
  per room.
- Wall porcelain height is full height in wet rooms (owner, UP-WET-001).
- Door head heights come from the schedule; window sill and head from the schedule or the elevations.
- **Conflict rule.** A value read from two sources that disagree is kept twice and flagged, never averaged.

**Input evidence, in this order of authority.**

1. Schedules (door / window tables, ceiling schedules).
2. Sections: level annotations FFL / SSL / TOS, ceiling lines.
3. Elevations: openings.
4. Level texts on plans.
5. Project facts (labelled PROJECT_SPECIFIED).
6. Owner fallbacks, labelled ASSUMED, used only if the owner approves them (D-04).

**Independent tests.**

- A synthetic section DXF whose level texts and ceiling lines give known heights per room.
- A schedule table with door / window head and sill.
- A conflicting pair (schedule vs section): the test asserts both values are kept and flagged.
- Unit / rotation / nesting invariance.
- Truth comes from the fixture coordinates and texts.

**Regression boundary.**

- Only the height inputs change; areas and lengths are unchanged.
- The difference explainer attributes every change to a HEIGHT_SOURCE record.
- V2.7 with synthetic facts is unchanged.

## P2: window and glazing areas

**Measurement rules.**

- **Window area** = width × height of the structural opening; the frame size from the schedule if given, else the
  opening.
- **Glazing area** = per sash, from the schedule, or a stated frame deduction (proposal: the schedule's figure only;
  no default deduction without owner confirmation).
- **Reveal / sill / head finishes** = opening perimeter × wall thickness, as the doors already do.
- **Deduction from the wall finishes** = the opening area, when the opening is measured.

**Input evidence.**

- The opening's width and position from the plan: this exists, and V2.7 positions are proven to 1 mm.
- The height from P1.
- Type marks and their schedule rows: a mark-text-to-opening association, a new reader.

**Independent tests.**

- A wall with three windows of different marks and a schedule.
- A curved-wall window (the B10 family).
- A corner window.
- A window in a mirrored block.
- Truth by hand.

**Regression boundary.** V2.7 counts are unchanged. New area lines, and new deductions from the wall finishes, are
explained by WINDOW_AREA records.

## P3: combined architectural + structural export

**Rule.** Both routes' canonical lines are kept as they are, in one workbook. The sheets are:

- by trade;
- by floor;
- by room / member;
- a traceability sheet (line → rule → source entities, using V2.7 provenance);
- the unresolved register.

There is no double count where the routes touch (lintels, columns in walls, stair finishes vs stair concrete):
**an ownership table decides which route owns each item.**

**Input evidence.** The existing outputs only.

**Independent tests.**

- The synthetic villa: every line appears exactly once, and the per-trade totals equal the sum of both routes.
- A deliberately shared item (a column in a wall) is owned once.

**Regression boundary.** Both routes are unchanged; the export is a new reader.

## P4: structural formwork

**Measurement rules (proposals, to confirm against the owner's / client's method of measurement).**

- Formwork = the contact area of concrete surfaces that need temporary support:
  - beam sides and soffits;
  - slab soffits and edges;
  - column sides;
  - wall faces;
  - footing and ground-beam sides (soffits only where not cast on blinding).
- Intersections are deducted where one member's face is cast against another's.
- Openings over a stated area are deducted (threshold to confirm).

**Input evidence.**

- Route G member geometry: beam spans, sections, slab outlines, columns.
- Storey heights from P1 / structural sections.

**Independent tests.**

- One beam-slab-column bay computed by hand.
- A T-junction of beams.
- A slab with an opening.
- A sloped or curved member (the dome machinery exists).

**Regression boundary.** The concrete volumes are unchanged; formwork is a new line family.

## P5: roof, balcony and external paving

**Measurement rules.**

- Roof and balcony membrane: plan area plus the upturns; this is the existing waterproofing system, applied to roof
  areas.
- Screed to falls: area, with thickness per the specification.
- Tiles: area.
- Parapet copings: length.
- External paving: area by material, with the edges (kerbs) by length.

**Input evidence.**

- Roof plan outlines, parapets, drains and falls (arrows, level texts).
- Site plan hard landscape hatches.

**Independent tests.**

- A roof with two drains and a parapet.
- A balcony with a threshold to an interior.
- A paved area with an L-shaped kerb.

**Regression boundary.** Interior rooms are unchanged.

## P6: excavation and backfill

**Measurement rules (proposals, to confirm).**

- Excavation = the footing / ground-beam plan area plus the working space (a convention), × depth from natural
  ground to formation.
- Backfill = excavation − the buried structure.
- Disposal = the surplus.
- Every convention (working space, side slope, bulking) is a labelled parameter, never a default.

**Input evidence.**

- Foundation plans: route G footings and ground beams.
- Natural ground and formation levels.
- The site levels drawing, if any.

**Independent tests.**

- A single footing.
- A strip under a ground beam.
- Two footings whose working spaces overlap (counted once).

**Regression boundary.** Concrete is unchanged.

## What must not happen in the next phase

- An accuracy claim, or the formal blind evaluation, before D-13 / D-15.
- A default for an owner convention.
- A change to V1 – V2.7.
