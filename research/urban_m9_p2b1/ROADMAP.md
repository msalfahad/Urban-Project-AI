# Recommended next-stage roadmap (deliverable 16)

Priorities follow the owner's order (rule interpretation, element completeness, correct release, traceability,
determinism, testing, performance, interface) and the demonstrated gaps of this phase. Nothing below is started:
the blind evaluation and any production use need separate owner authorization.

## 1. Where the reference plan stands (V2.3, no heights given; aggregate)

| BOQ line state | V2.2 | V2.3 |
|---|---|---|
| SOURCE_DERIVED (released) | 132 (30 %) | 149 (33 %) |
| PROVISIONAL (shown, never confirmed) | 75 (17 %) | 107 (23 %) |
| NOT_APPLICABLE with evidence | 0 | 34 (7 %) |
| BOUNDED_EXPOSURE | 17 (4 %) | 16 (3 %) |
| BLOCKED_RFI | 210 (48 %) | 152 (33 %) |

The blocked share is now dominated by document requests, not by owner questions. Largest B groups (instances):
wall-finish heights 56, window type and sill 34, floor-finish specification 28, stair sections 25, door evidence 13,
space identity 10, blockwork specification 7, lift identity 6.

## 2. What is still missing for 95 % independently verified quantity accuracy (measurable gaps)

1. **An independent measurement.** Accuracy is unmeasured: no blind comparison has been run. The scorer and protocol
   exist (Phase 2A / 2B-0); a 95 % claim needs the blind evaluation, per trade, on at least the reference plan and one
   unseen villa. *Gate: owner authorization.*
2. **Heights.** 56 wall-finish-height items and every door height on the owner fallback: without sections, wall
   areas stay BLOCKED and door areas ASSUMED. Reading section / elevation heights (or a filled heights facts file) is
   the single largest unlock.
3. **Window schedule / sills.** 34 - 45 window items (reveal floor status, skirting at sill windows, face deductions).
4. **Specifications.** Floor-tile sizes (28), block types (7), membrane systems: quantities exist, materials do not.
5. **Stair sections.** 25 stair items (risers, landings, stair-well ceilings).
6. **Room identity.** 10 unlabelled / merged spaces, the open-plan wet zone, the connecting space: labels or project
   decisions.
7. **Engine defects.** 8 doorway strips the engine cannot attribute to one opening; reader limits (entity kinds not
   read, nested hatches, DIMENSION entities).

## 3. Recommended work, in order

| # | Work | Why (demonstrated) | Expected effect | Size |
|---|---|---|---|---|
| 1 | **Blind evaluation (after authorization)** | accuracy is unmeasured | the first independent accuracy figure per trade | M |
| 2 | **Schedule and section reader** (door / window schedules as DXF tables or PDF text; section level texts -> heights facts with SOURCE authority) | the largest B groups; door areas ASSUMED | converts BLOCKED wall areas and ASSUMED door areas into SOURCE / CONFIRMED | L |
| 3 | **Per-face finish overrides** (facts by room / face; a feature wall) | audit case 5 (full-height tile over-states a feature wall) | removes a known over-statement | S |
| 4 | **Door details**: per-category jamb plaster height (main entrance 2.50), accessibility attribute from labels / schedule, main-entrance identification from elevations | audit cases 1, 3, 13 | fewer withheld / mis-proposed doors | S-M |
| 5 | **Strip attribution** (strip faces spanning two openings; strips at door closures) | 8 E items + 5 provisional-door strips on the reference plan | fewer blocked strip lines | M |
| 6 | **Project-decision workflow** (a validated decisions file per project, kept private; a review sheet listing connecting-space and class-review candidates) | 1 connecting space, 1 class review, 2 main-entrance candidates on the reference plan | doors released on a recorded decision, never a guess | S |
| 7 | **Registry governance**: versioned rule changes (1.0.1 ...) with history; an independent review of every record against the owner's texts | self-audit limit | trust in the registry | S |
| 8 | **Owner answers to OQ-01 .. OQ-04** | 4 open questions | closes the remaining D / C groups | owner |

## 4. Not recommended now

- Adding owner-required modifications beyond doors before the owner defines them.
- Any change to V1 .. V2.2 (frozen); new behaviour stays in an opt-in method version.
- Cosmetic interface work before the schedule / section reader.
