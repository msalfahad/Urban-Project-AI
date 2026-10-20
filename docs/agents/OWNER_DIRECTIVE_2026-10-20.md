# Owner directive 2026-10-20: Alsenan owner decisions and engineering reasoning (Q-50 to Q-63)

Given by the owner in his main chat on 2026-10-20 (about 11:40 UTC). It is recorded here in his own words, condensed only
where the text repeats. It binds every agent. Read it before any Alsenan quantity task and before writing an owner
question. The answers in OWNER_QUESTIONS.md point here for the full reasoning.

The main-chat audit against the existing Urban rules is at the end ("Contradictions and links to existing rules").

## Part 1. What the owner expects

- An engineering system, not a multiple-choice answer processor. It does not simply follow his answers, copy the
  freelancer, or pick the most convenient interpretation.
- What the system must do:
  - Read architectural, structural, sanitary, sectional, elevation and detail drawings together.
  - Understand how they describe one physical building, and separate confirmed, missing, contradictory and provisional
    information.
  - Calculate deterministically, with documented rules.
  - Detect missing quantities, double counting and wrong dimensions.
  - Compare against independent hand calculations and contractor BOQs, and explain discrepancies with evidence.
  - Ask the owner only real owner decisions, and escalate design issues to the architect or structural engineer.
  - Learn reusable methods without turning project assumptions into universal standards.
- Target: at least 95 % independently verified quantity accuracy, higher on financially material items. It is **not yet
  demonstrated**, so never report it as reached until independent testing proves it.
- Three things are each not proof:
  - a quantity that looks reasonable is not necessarily correct;
  - matching the freelancer is not proof;
  - differing from him is not proof of error.
- The objective is to reconstruct the actual designed building and measure it correctly.

## Part 2. How the engine must think

### 2.1 Evidence hierarchy

1. **Document applicability first.** Establish project, drawing number, revision, issue date, approval status,
   discipline, floor / area / element, and whether the drawing is superseded. An obsolete detail never overrides a
   current approved drawing because it is more detailed.
2. **Explicit, applicable project evidence.** Examples: a dimensioned structural section beats a CAD width; an
   approved door schedule beats an Urban fallback; an architectural section with the finished ceiling height beats an
   assumed deduction; a specific waterproofing detail beats a generic rule. This is not a rigid ladder: a beam schedule
   and a dimensioned section may both be authoritative, and if they conflict, record the conflict instead of choosing
   silently.
3. **Urban owner rules when the drawings are silent.** Examples:
   - internal door height fallback 2.20 m, marked ASSUMED;
   - wet areas include kitchens, bathrooms, pantries, washing and ironing rooms, subject to project scope;
   - membrane roll 1.00 x 10.00 m where that product is specified;
   - membrane overlap 0.10 m where approved;
   - upturn 0.20 m unless project details say otherwise;
   - actual drawing heights beat generic finishing-height assumptions.
4. **Engineering calculations derive quantities.** For example, 4.50 m / 28 risers = 16.07 cm is a calculation, not an
   owner preference.
5. **Assumptions only when permitted and labelled.** An assumed quantity is never shown as drawing-confirmed.
6. **Escalate unresolved design conflicts** as a designer clarification request. Never invent an answer to complete
   the BOQ.

### 2.2 Quantity status

Every quantity carries one of these statuses:

| Status | Meaning |
|---|---|
| VERIFIED | drawing-derived and independently checked |
| CALCULATED | deterministic, awaiting independent check |
| PROVISIONAL | explicit unresolved assumptions |
| ASSUMED | an approved fallback, not drawing-confirmed |
| HELD | the quantity or specification cannot be safely established |
| CONFLICT | applicable documents disagree |
| NOT APPLICABLE | evidence confirms the element is out of scope |

Quantity status is separate from code-test status: a passing pytest run does not prove an engineering quantity.

### 2.3 Three kinds of decision

- **Owner decisions:** finish choice, offcut reuse for purchasing, client finish wishes. Ask the owner.
- **Engineering calculations:** concrete volume, riser height, beam size from drawings, cement from a stated mix,
  deducting duplicated intersections. The engine calculates and shows evidence; never ask the owner to do the arithmetic.
- **Designer clarifications:** a conflicting beam schedule and plan, an undefined fence, an unclear slab level, missing
  stair details. These go to the architect or engineer. An owner's multiple-choice answer is not a substitute for
  required design confirmation.

## Part 3. Decisions

### Q-50 Round reception stair: A, CONDITIONAL

Use the stair reconstructed from the architectural and structural plans when no section exists, with its source named
("reconstructed, no section").

- 5.50 - 1.00 = 4.50 m; 4.50 / 28 = 0.1607 m (16.07 cm), inside 15-17 cm.
- Visible treads are not risers. Determine:
  - whether the arrival floor is the last tread;
  - whether the corner landing adds a rise;
  - whether the 12 curved, 11 straight and 5 further steps are distinct;
  - whether the architectural and structural plans agree;
  - whether the stair starts and ends at the stated levels.
- Never accept 28 because it gives a plausible riser.
- Reconstruct flight by flight. For each flight record: start and end level, risers, treads, tread geometry, width,
  waist, landing, and structural reference.
- Straight flights, once geometrically verified, are calculated on their own; curved parts stay held. The 0.318 + 0.151
  = 0.469 m3 still needs an independent check before release.
- Do not release the whole stair until the waist, landing and curved geometry are supported.

### Q-51 Winders and curved steps: A, CONDITIONAL

- Volume per step = 0.5 x riser x the step's actual drawn plan area, where the geometry supports the wedge over a
  uniform waist.
- Main-stair example 0.5 x 0.1667 x 1.44 = 0.120 m3 holds only if 1.44 m2 is the real combined area of the five steps.
  Do not assume the full 1.20 x 1.20 corner is step wedges: it may hold a landing or a void.
- Curved stairs, in order:
  1. CAD boundary per step;
  2. plan area;
  3. riser;
  4. wedge where valid;
  5. waist separately;
  6. landings separately;
  7. remove intersections.
- Use solids or integration for non-standard geometry. The formula is a method, not permission to invent geometry: an
  unknown area or waist is HELD.

### Q-52 Plaster and paint wall heights: C, MODIFIED

- Neither an automatic 0.60 m deduction nor the deepest beam anywhere in the room. The rule "slab to slab - beam -
  decor - floor build-up" was an approximation and must not override the drawings. The drawn depths are 0.40 / 0.50 /
  0.75 / 0.85 / 1.20 m.
- Per room:
  1. structural levels;
  2. finished floor and build-up;
  3. slab underside;
  4. beams that intersect the room;
  5. whether they project below the intended ceiling plane;
  6. architectural ceiling and section details;
  7. gypsum drops and bulkheads;
  8. wall plaster height;
  9. wall paint height separately.

  Plaster may run above the false ceiling while paint stops at it, depending on the specification.
- A beam does not automatically lower the whole room. An unknown finished ceiling level keeps the quantity provisional
  or held. **Never release all 32 rooms on a fabricated common height.**

### Q-53 Stair marble bed 1:3: C, CALCULATED PROVISIONAL RATE

Derive the materials from the mix, not from a fixed number. Illustration per 1.00 m3 of finished mortar:

| Step | Calculation | Result |
|---|---|---|
| Dry material (factor 1.33) | 1.00 x 1.33 | 1.33 m3 |
| Cement volume | 1.33 x 1/4 | 0.3325 m3 |
| Cement weight (1440 kg/m3) | 0.3325 x 1440 | 478.8 kg |
| Cement bags (50 kg) | 478.8 / 50 | about 9.6 bags |
| Sand | 1.33 x 3/4 | about 1.00 m3 |

- For preliminary purchasing, about 10 bags and 1.00 m3 of sand, subject to material, mix and waste. These are not
  universal constants.
- Keep separate: geometric mortar volume, theoretical cement, theoretical sand, purchasing allowance, and the supplier's
  or approved mix.
- Never apply the 1:4 rate to 1:3. Never add waste without a named source or an owner-approved allowance.
- For any mix, derive the materials from the stated ratio and documented assumptions.

### Q-54 Ground-floor annex height: B, HOLD until the datum is verified

- 4.30 - 0.30 = 4.00 m does not establish the slab-to-slab height. +4.30 may be the structural slab top, the finished
  roof, the waterproofing, the screed or another datum.
- Inspect section B-B and the roof details, and cross-check slab thickness, roof build-up, elevations, and door and
  window heights. Release only if the documents clearly make +4.30 the structural slab; otherwise HOLD and request
  clarification.
- A level mark must have a known physical reference. Never treat every roof mark as the structural slab.

### Q-55 Doors without a printed height: C for final Alsenan dimensions, existing owner fallback kept

- Urban fallback: internal door 2.20 m, used only when the drawings are silent and not a Kuwait standard.
- Main entrance: 2.00 x 2.50 as printed, so 2.50 governs.
- Other doors: search plans, schedules, elevations, sections and details, and match each opening to its type and mark.
  If none is found:
  - request the door schedule;
  - use 2.20 m only for a provisional quantity, marked ASSUMED;
  - keep the measured width;
  - never take the freelancer's 2.40 m without evidence.
- A fallback allows provisional estimating; it never makes an unknown dimension confirmed.

### Q-56 First-floor living and circulation: A, CONDITIONAL

- Separate rows: living 22.20 + corridor beside the void 7.04 + main-stair landing 4.88 + connector beside the lift
  4.80 = 38.92 m2 (freelancer 38.96, engine 44.87).
- The 5.95 m2 difference is significant. Check for:
  - overlapping polygons and wrong boundaries;
  - stair openings counted as floor;
  - double-counted circulation;
  - lift voids;
  - connector geometry;
  - classification errors;
  - adjacent areas included.

  Never assume the freelancer is right because the reconstruction is close to him.
- Porcelain is a provisional finish unless documented. The landing may become marble: move it to marble without changing
  the geometry.
- Geometry and finish classification are separate data. Never merge distinct spaces to match a contractor.

### Q-57 Ceiling plaster and paint: A, MODIFIED

- A gypsum decor ceiling takes a finishing and paint system, not cement plaster. Ceiling paint is not blindly the floor
  area.
- Measure separately:
  1. horizontal gypsum area;
  2. moisture-resistant gypsum where specified;
  3. other boards;
  4. vertical bulkhead faces;
  5. cove returns and drops;
  6. actual paintable gypsum surfaces;
  7. concrete ceiling plaster only where specifically required.
- Moisture-resistant board may still be painted: the board and the paint system are separate decisions.
- The freelancer's 337.57 + 72.01 + 42.75 = 452.33 m2 is comparison evidence only. The 42.75 m2 of cove needs geometry
  or an approved detail.
- Use "ceiling paint = floor area" only for a flat, horizontal, fully paintable ceiling whose specification supports
  it.

### Q-58 Membrane offcuts: A, CONDITIONAL

- Suitable offcuts may be reused within the same roof or room.
- Current system:
  - roll 1.00 x 10.00 m;
  - adjacent overlap 0.10 m;
  - upturn 0.20 m, folded from the same strip, not added as separate skirting.
- Calculate physical strip layouts; never divide the net area by 10 m2.
  - Example: a 3 x 4 m kitchen takes 4 strips of 4.40 m (with both upturns), about 16.28 m2 cut from two rolls. That is a
    geometric example, not a universal detail.
- Second-floor roof: 17 rolls with trim reuse, 18 without; a 0.70 x 6.97 m leftover; a 4.60 m parapet step to cover.
  **Before approving 17, prove the leftover covers the detail.** Check: width, length, overlap, upturn geometry, corners
  and terminations, the seam arrangement, and whether patches are allowed there. Area alone does not prove an offcut is
  usable.
- Report all of these: net area, strip count, strip dimensions, gross cut area, overlap consumption, corner detailing,
  roll count, reusable offcuts and unusable waste. Purchasing stays separate from the installed BOQ.

### Q-59 Tile offcuts: B, MODIFIED

- Reuse of suitable offcuts is allowed within the same room. **No arbitrary universal 20 cm minimum.** A piece is usable
  only if it meets another position's dimensions, cutting loss, orientation, pattern, veining, edge finish, minimum
  piece size, appearance and installer / manufacturer limits. For example, a 15 cm piece may suit a hidden edge and not
  a visible one.
- Per room and tile size, report:
  1. net area;
  2. tile size;
  3. joint;
  4. layout;
  5. full tiles;
  6. cut tiles;
  7. reused offcuts;
  8. unusable offcuts;
  9. **optimised** purchase;
  10. **conservative** purchase.
- An optimised layout is not guaranteed field performance. With no tile size, never invent one: report the area and
  hold the count.

### Q-61 Contradictory and unmarked beams: C, member by member

| Piece | Decision |
|---|---|
| (1) CB10, schedule 0.25 x 0.50 vs drawn 0.30, 0.744 / 0.893 m3 | **HOLD AS CONFLICT.** Find whether 0.30 is the structural width, a finish, a drafting error or another element. Do not pick the schedule only because it is printed: reconcile the section and the schedule. |
| (2) GF CB3 / "B3 (with stair)" | **HOLD.** Same beam, different types, stair-modified, or an extra component? Never duplicate concrete. |
| (3) Dome and void rings | B4 only where the element is identified as B4; never extend B4 to unrelated rings; otherwise hold. |
| (4) Six unlabelled spans | **HOLD.** Keep location, length and candidate volume; never omit. |
| (5) Strips north of B23 / B20 | Exclude only if the sections conclusively show they are not concrete beams; if incomplete or ambiguous, unresolved. |
| (6) West outer strip, SE box, CB12 outer strip | **HOLD**; investigate plans, sections, elevations and details. |

Every member record carries: a unique id, floor and location, type, geometry, governing section, schedule reference,
volume, evidence status and a conflict record.

- A missing label is not proof that a beam is absent; a drawn line is not proof that it exists.
- Never take the largest volume just to be conservative. Uncertainty stays visible, never hidden in an inflated quantity.

### Q-62 Stair / landing overlap: A, CONDITIONAL

- The same concrete is measured once. Main stair 5.011 - 0.060 = 4.951 m3; 0.163 m3 over all stairs, accepted only
  after the intersection geometry is verified.
- Method:
  1. model the flight;
  2. model the slab or landing;
  3. compute the intersection;
  4. assign it to the slab / landing under the chosen convention;
  5. deduct it from the stair;
  6. keep the deduction in the ledger.

  Use solids for complex geometry.
- No double count at stair-landing, beam-slab, column-beam or footing-ground-beam junctions. Never deduct overlapping
  plan lengths unless the volumes really intersect in 3-D. One convention for the whole project.

### Q-63 Sea-side fence: C, HOLD and request design clarification

- 7.00 m overall (6.00 solid + 1.00 gate, subject to drawing check), 0.20 m drawn; material and height unknown (block,
  RC, a low wall with glass or metal railing, other).
- Create a visible unresolved BOQ element, "Sea-side boundary element, 7.00 m overall", listing the unknowns: material,
  height, structure, foundation, finishes, railing / glazing, gate.
- Request clarification from the architect. An unidentified element goes into the missing-scope register: unknown is not
  zero.

## Part 4. What the agents must learn

1. **Separate measurement from purchasing.**
   - Waterproofing: installed m2, upturns, cut m2, whole rolls, waste / offcuts.
   - Porcelain: installed m2, tile size, joint, pieces, purchase pieces / boxes, waste / offcuts.
   - Mortar: m3, cement bags / kg, sand m3, purchase allowance.

   Never mix these in one field.
2. **Separate geometry from specification.** A confirmed room area with an unknown finish; a confirmed door width with
   an assumed height; a confirmed wall length with a held paint height. Never hold every known measurement because one
   attribute is missing, and never release a derived quantity that depends on the missing attribute.
3. **Never silently close missing scope.** The 7 m fence, unlabelled beams, missing columns, undefined stair details,
   unknown roof parts, missing door schedules and unidentified ceiling finishes are visible unresolved elements with
   clarification requests.
4. **Detect contradictions before calculating.**
   1. Read every discipline.
   2. Check revisions.
   3. Extract dimensions and labels.
   4. Link elements across plans, sections and schedules.
   5. Detect conflicts.
   6. Resolve what the drawings resolve.
   7. Flag the rest.
   8. Then calculate.

   Do not discover contradictions only after comparing with the freelancer.
5. **The freelancer's BOQ is comparison evidence.** He may double-count, use another section, omit a fence, assume a
   door height, add roof area or use other conventions. Compare engine vs an independent drawing-based QS quantity vs the
   freelancer, find the real cause, and never optimise the engine to match him.
6. **Confidence reflects evidence, not agreement.** Two agents agreeing proves nothing if they share an assumption. The
   verifier reconstructs from the drawings, by a separate method where possible, and checks engineering correctness, not
   only that the code runs.

## Part 5. Implementation and reporting

### 5.1 Decision register

Record all 13 decisions with:
- question id and the owner's answer;
- the full explanation;
- project applicability and any general rule;
- assumptions;
- outstanding designer questions;
- quantity status, evidence references and verification requirements.

Do not turn every Alsenan decision into a global rule:
- the 2.20 m door fallback is an existing Urban rule;
- the +4.30 annex datum is an Alsenan drawing issue;
- the 1:3 mortar calculation is a reusable method;
- the 38.92 m2 breakdown is project geometry.

### 5.2 Engine changes only where justified

No edits to frozen production methods to implement these answers. Each change:
1. names the existing rule;
2. names the defect or missing capability;
3. shows the drawing evidence;
4. designs a deterministic correction;
5. adds targeted tests;
6. runs regression;
7. gets independent verification;
8. reports quantity changes;
9. is released only through the approved workflow.

No silent changes to established BOQ quantities.

### 5.3 Next Alsenan report

Per question, report:
- (A) decision;
- (B) evidence;
- (C) calculation;
- (D) the previous released engine result;
- (E) the new candidate result;
- (F) the freelancer and why he differs;
- (G) verification status;
- (H) outstanding uncertainty;
- (I) engine improvement;
- (J) financial relevance, flagged without invented prices.

### 5.4 Priority by engineering and financial risk

1. Structural concrete omissions and double counting.
2. Missing or incorrect structural members.
3. Floor and wall finishes.
4. Waterproofing coverage and rolls.
5. Stairs and marble.
6. Doors, windows and aluminium.
7. Ceilings.
8. Purchasing optimisation.

Do not over-invest in small offcuts while major structural quantities are unresolved.

### 5.5 Accountability

Update agents.json, the board, RUN_LOG, the decision register and the evidence files. Every completed task names:
- the worker and the independent verifier;
- the commit;
- the drawing evidence and the tests;
- the quantity differences and the limitations.

Workers 2 and 3 are not treated as having completed independent code verification while their execution is blocked.
Their hand measurements are evidence, not a substitute for engine execution and validation.

## Part 6. Final directive

For every uncertainty, ask:
1. What physical element is being measured?
2. Which current drawings describe it?
3. Are they consistent?
4. What dimensions are explicit?
5. What geometry can be calculated deterministically?
6. Which Urban rules apply?
7. Which assumptions remain?
8. Could it overlap another BOQ item?
9. Is there a missing element the freelancer did not count?
10. Can an independent engineer reproduce it?
11. Is it releasable, provisional or held?
12. Does it reveal a reusable engine defect?

Never:
- ask the owner to choose a structural dimension the documents should establish;
- copy the freelancer;
- invent dimensions to raise completion;
- show unresolved quantities as zero;
- confuse passing tests with validated accuracy.

Correctness, traceability, completeness and independent verification come before speed. These answers authorise the
stated working rules and investigations. They do **not** automatically authorise releasing held quantities, changing
frozen engine versions, or merging unverified code. Next objective: measurable improvement on the Alsenan drawings,
supported by reproducible calculations and independent QS evidence. Target 95 %+ independently verified accuracy with
no material silent omissions.

## Contradictions and links to existing rules (main-chat audit, 2026-10-20)

| # | Point | Existing rule or state | Effect |
|---|---|---|---|
| X1 | Q-52 says the height formula is an approximation | Owner 2026-10-19 (Q-43): plaster / paint wall = slab to slab - 0.60 beam - 0.15 / 0.20 decor - 0.10 floor (GF 3.65, 1F / 2F 3.35); Q-48 uses the same heights for wet-room wall tile | **Superseded as a release rule.** The values become a fallback and cross-check only. Every piece that releases per-room wall heights from the common formula (room levels / finish-height work) returns to per-room geometry; Q-48 wet-wall tile heights follow the same per-room method |
| X2 | Q-55 fallback 2.20 m | Already in knowledge 1.5.0 (door heights, `owner_reference_height_m`: INTERNAL_PVC / BATHROOM_PVC / EXTERNAL_ALUMINIUM 2.20, MAIN_ENTRANCE 2.50, state OWNER_STANDARD_ASSUMED) | Consistent. Process defect: Q-55 was written as if no rule existed. The team must check the knowledge registry before asking |
| X3 | Q-53: never add waste without a named source | The Q-45 record carries a "waste 5 %" practice value and "8 bags, 1.1 m3 sand per m3" for 1:4 | The 5 % is not owner-approved: drop it from released figures (show it only as a labelled purchasing option). 1:4 materials are now derived by the same method (1.33 / 5 = 0.266 m3 cement = 383 kg = 7.7 bags; sand 1.06 m3), not the fixed 8 / 1.1 |
| X4 | Wet areas include kitchens and pantries | The kitchen is in the 17 released wet areas (verifier hand check: kitchen strips 15.30 m, 2 rolls). The pantry is HELD in V2.11 ("Q-37 project data"), although Q-37 was answered (waterproof around the pantry) and its printed size 4.50 x 3.00 m is confirmed on sheet 03 (hand plan: 21 rolls with the pantry) | The pantry hold now conflicts with Q-37 and this directive. Release it through the normal workflow (wet areas 19 -> 21 rolls) unless a drawing reason is recorded |
| X5 | Q-54 HOLD | Merged room-level / wall-height work used +0.30 to +4.30 = 4.00 m for the annex (3.15 m wall) in at least one hand reading | Annex heights go back to HELD |
| X6 | Q-61 (1) CB10 HOLD AS CONFLICT | The team recommended "printed schedule wins" | The owner's rule replaces it: a schedule / drawing conflict is a CONFLICT plus a designer request, never resolved by picking the printed one |
| X7 | 2.2 status vocabulary | Engine and board use RELEASED / HELD / PROVISIONAL / BLOCKED / UNRESOLVED / NOT_PRESENT ... | Needs a mapping table (no rename of frozen outputs); new outputs use the seven statuses |
| X8 | Q-59: no fixed 20 cm minimum | No Urban rule gives a minimum piece size | Not a contradiction but a gap: the optimised count needs per-position constraints the drawings do not give, so publish both counts, the optimised one PROVISIONAL |
