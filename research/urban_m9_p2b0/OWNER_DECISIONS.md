# Remaining owner decisions after Phase 2B-0

**Nothing in this list was decided by the engine.**
- Until an answer is recorded, `ARCH_TAKEOFF_V2.2` keeps the affected quantity out of released totals, as a hold, a REVIEW, a range or an RFI.
- An answer is recorded as a project rule or a per-element decision, never as a code default.
- No provisional quantity is promoted automatically.

Each decision below lists:
- **Question:** what the owner needs to answer.
- **Today:** what V2.2 does until then.
- **Reference plan:** the effect, aggregate only.
- **Unblocks:** what the answer releases.

## Before the blind round

These decide what the scored totals mean.

**OD-1. Skirting under windows (F-17; BA-11, BA-12)**
- **Question:**
  - Per window type: is it a sill window (skirting runs under it) or floor-level glazing (no skirting)?
  - Separately: is the V1 convention right that a window threshold on a recessed frame's room face is a sill window?
- **Today:**
  - The length both readings agree on is released.
  - An edge carrying both roles is a [0, length] range.
  - The recessed-frame convention is kept, but it is a convention, not evidence.
- **Reference plan:** 9 range lines, [0, 25.348] m in total; BA-12 is 1.90 m + [0, 1.00] m.
- **Unblocks:** those 9 ranges and the skirting total's meaning.

**OD-2. The 0.9 m / 1.0 m external door (F-18; DR-02)**
- **Question:** settle the width: the 0.9 m jamb-to-jamb opening, or the 1.0 m door block.
- **Today:** the door is held (`DOOR_HELD_WIDTH_REVIEW`).
- **Reference plan:** 1 aluminium door, 0.9 m, withheld.
- **Unblocks:** 1 aluminium door.

**OD-3. The small unlabelled space next to the kitchen (F-20; DR-03)**
- **Question:** is it inside the building envelope?
- **Today:** the door into it is `CLASS_REVIEW`, not internal PVC.
- **Reference plan:** 1 door (1.0 m) withheld.
- **Unblocks:** 1 door; PVC or aluminium.

**OD-4. The 3 openings into the stacked shaft (F-22; DR-06)**
- **Question:** are they lift landings? A lift word, a lift schedule or the owner can confirm this.
- **Today:** they are `LIFT_ENTRANCE_CANDIDATE` (REVIEW), and their passage lines are PROVISIONAL.
- **Reference plan:** 3 candidates; passage lines go from 12 to 9 released.
- **Unblocks:** the lift-door exclusion rule, applied for the first time on a real drawing.

**OD-5. The main entrance (DR-01)**
- **Question:** name it, or name the evidence that identifies it.
- **Today:** 2 candidates (REVIEW), kept separate from aluminium.
- **Reference plan:** 2 door sets, 3 leaves, 3.0 m.
- **Unblocks:** the main-entrance line.

**OD-6. Heights for Mode A**
- **Question:** who fills `FACTS_TEMPLATE_HEIGHTS.json` from the sections and schedules, and with what authority?
- **Today:** Mode U only; every wall finish and every door / window area is an RFI.
- **Reference plan:** with test heights, plaster would be 16 released + 12 ranged of 30.
- **Unblocks:** Mode A of the blind round.

## Can follow the blind round

These narrow ranges and RFIs; nothing released depends on them.

**OD-7. Deduction rule for openings that close a face without a band gap (F-26)**
- **Question:** what to deduct for a door closed only by its leaf, or for glazing on the room face. Options:
  - the door height × the closure length; or
  - nothing.
- **Today:** a [deducted, not deducted] range.
- **Reference plan:** 24 wall-finish lines are ranged (test heights).
- **Unblocks:** the wall-finish ranges.

**OD-8. Threshold strips (Q-S6-1)**
- **Question:** the threshold finish, and whether the closure strips are measured.
- **Today:** 6 closure strips are `OUT_OF_LEDGER_SCOPE`; 39 threshold lines are RFIs.
- **Unblocks:** the threshold lines.

**OD-9. Finish above wall tile (Q7)**
- **Question:** paint or another finish above the tile band.
- **Today:** RFI.
- **Reference plan:** 16 paint RFIs.
- **Unblocks:** wet-room paint.

**OD-10. Stair-hall finish (Q-S6-4)**
- **Question:** plaster and paint inside the stair enclosure.
- **Today:** RFI.
- **Reference plan:** 2 plaster + 2 paint RFIs.
- **Unblocks:** stair-hall finishes.

**OD-11. Reveal depth (SE-01 … SE-03)**
- **Question:** is 0.25 m a cap or a fixed value? Do door reveals exist under the PVC lining?
- **Today:** reveal RFIs (26 window reveals). Every wall on the plan is ≤ 0.20 m.
- **Unblocks:** reveal lines.

**OD-12. Kitchen waterproofing (SE-07)**
- **Question:** is the kitchen floor waterproofed?
- **Today:** open; nothing is inferred.
- **Unblocks:** 1 ledger record.

**OD-13. Provisional doors (DR-05)**
- **Question:** no decision is needed to keep them unreleased. To release them, a door schedule or an independent opening is needed.
- **Today:** `DOOR_PROVISIONAL`, withheld.
- **Reference plan:** 6 doors.
- **Unblocks:** 6 doors.

## Process decisions

- **OD-14. Approve protocol amendment A1** and the hash freeze in `BLIND_READINESS_RECORD.json`.
- **OD-15. Appoint the QS** and agree the conventions sheet (protocol section 4).
- **OD-16. Identify a second blind project.** Any percentage claim needs two projects.
- **OD-17. Decide whether V2.2 may be proposed as a default.** This happens only after the blind round, never before it.
