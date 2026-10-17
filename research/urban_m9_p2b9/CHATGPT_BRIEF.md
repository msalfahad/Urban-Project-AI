# Brief for ChatGPT review — Phase 2B-9

This is an Urban Projects bilingual Kuwait villa BOQ / QTO engine (architectural route).

- Prices are out of scope.
- The long-term target is ≥ 95 % accuracy proven by independent blind tests. **That is not a claim about the current
  engine. No blind test has been run, and none can be until a second villa set exists.**
- This phase added ARCH_TAKEOFF_V2.8 (opt-in). V1 – V2.7.1 are byte-identical to their frozen outputs.

## What worked

1. **Heights from the drawing.**
   - One evidence hierarchy covers element annotations, schedules, sections / elevations, derived, floor notes,
     project notes, project facts and the Urban default.
   - Plaster runs to the soffit and paint / tile to the finished ceiling; floor-to-floor is never used.
   - Same-rank conflicts hold the value; units are inferred only when one reading is plausible.
   - Proven on 9 evidence variants of one room against hand arithmetic, plus unit and invariance tests.
2. **The opening schedule.** Height, sill, head and class per opening, with the schedule width checked.
   - Each opening is deducted by its own band, which fixes the V2.7.1 full-height window assumption.
   - Floor glazing is not skirted, and an unknown sill becomes a range.
   - A window with no height releases its width and holds its area.
3. **Window reveals** from the measured depth (no fixed depth): jambs plus a head soffit only where wall remains, and
   the sill surface as its own item. The floor-glazing strip is treated as floor.
4. **Wall stubs.**
   - Short returns and curved stubs (0.05–0.30 m) now count as wall, with the plan area conserved.
   - The earlier claim that collinear stubs were lost was **wrong**: they were already counted. The record is
     corrected.
5. **Curved walls.** Inner, centreline and outer arcs are kept apart, so no mean radius is used for a face.
6. **Independent verification of every V2.8 change.**
   - Reference plan: +0.16854 m wall run VERIFIED by an arc census of the raw entities.
   - Synthetic villa: 7 / 7 skirting changes VERIFIED by an independent face takeoff.
7. **A double count caught before release.** The first draft took 30.75 m of window thresholds off the reference
   plan's skirting although they were already in a range. It was fixed edge by edge.

## What did not work, or is not done

1. **The reference plan carries no heights.** It has no schedule, no section bound to a floor, and no notes. V2.8
   therefore changes almost nothing there. The 138 missing items are listed; nothing was invented.
2. **Curved glazing without a wall gap loses its room** (D-P9-01). With roles declared, the floor takes the reveal
   strip (D-P9-02). V2.8 reports the lost label but does not fix either.
3. **The Phase 2B-8 unverified 23 are still 23.** The largest group (13) depends on one space closed by a drawn zone
   line. Closed with that line, the reader's face disagrees by 0.899 m² (D-P9-04). This was recorded, not forced.
4. **Blockwork m² / m³, elevations, facade finishes, ceiling types, stair risers / flights** are still absent or
   blocked.
5. **A turned schedule sheet** is not read (L-P9-01).
6. **No second villa exists.** The blind run cannot start.

## Questions for the reviewer

1. Is the evidence hierarchy right for Kuwait villa drawing sets? In particular, should a room-scoped ceiling note
   outrank a section (it does now, as an element annotation)?
2. Is "an unknown sill is a skirting range, never certain" the right default? The alternative is the owner's
   sill-window assumption, labelled.
3. Should stubs under 0.05 m be masonry, or artefacts as now?
4. Do the proposed acceptance measures (A1–A11, `ACCEPTANCE_FRAMEWORK_PROPOSAL.md`) fit QS practice, especially the
   materiality weights without prices?
5. For D-P9-04: which should own a recess mouth, the room or the reader's gap closure?

## Recommendations (unapproved)

1. **Highest value: obtain sections and a door / window schedule.** Use the second villa, or the reference villa's
   own sheets if they exist outside the DXF. Every wall-area quantity moves from facts to evidence.
2. Fix the curved-opening recognition (D-P9-01 / -02) with an adversarial test set.
3. Add blockwork m² / m³ once a section gives the block height.
4. Have the owner approve the acceptance framework **before** any blind run.
