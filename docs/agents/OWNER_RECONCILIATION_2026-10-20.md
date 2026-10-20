# Owner response 2026-10-20: Q-64 to Q-66, reconciliation G1 to G5, dual-method design

These are the owner's decisions, given in his main chat on 2026-10-20 at about 15:45 UTC. They are recorded in his own
words, with layout only. They bind every agent, together with:

- OWNER_DIRECTIVE_2026-10-20.md, where the main-chat audit lines X1, X3 and X5 are withdrawn;
- the 12:15 correction in OWNER_SESSION_CHANGES.md, which preserves the owner's manual BOQ method.

## Part 1: open questions

### Q-64 Facade notch: B, conditional

- Use the straight facade measurement of **105.787 m** if the additional 0.10 m represents return faces already measured
  under the window / glass reveal finish.
- Do not double-count those surfaces in both the main facade run and the reveal quantities.
- However, verify the actual CAD geometry, and confirm that the 0.05 m column projection and the 0.08 m recess are
  assigned to the correct finish items.
- Keep the **105.887 m** geometric perimeter as an audit comparison.

General rule: distinguish the physical wall perimeter from the billable main facade finish and the separate reveal
quantities. The measurement convention must be consistent.

### Q-65 Roof parapets and street-side fence: C, with provisional alternatives

- Do not select white or black block solely because white is lighter, or because the neighbouring fence uses black block.
- First check whether "white" and "black" refer to different block products, densities or materials, or only to colour.
- Roof parapets may have structural, loading, stability and waterproofing requirements that cannot be established from
  colour alone.
- The neighbour-side fence specification does not automatically govern the street-side fence.
- Keep the confirmed geometry:
  - roof parapets 104.25 lm, subject to measurement verification;
  - street-side fence 8.20 lm overall, of which 5.70 lm solid and a 2.50 lm gate opening.
- Request the material and construction details from the designer.
- The engine may calculate provisional alternatives for comparison, but the final material classification stays **HELD**
  until confirmed.

### Q-66 First-floor main-stair landing: B

- Use marble for the 4.875 m2 main-stair landing, consistent with the owner's existing rule that stair finishes are
  marble. Do not also count this landing under porcelain.
- Candidate revised quantities: first-floor porcelain **33.713 m2**, stair marble **44.365 m2**. They hold only after it
  is verified that the 4.875 m2 landing was previously included exactly once and that the original category totals are
  otherwise correct.
- Keep the landing as a separate measured element, classified under marble. Do not merge its geometry into the stair
  flight.

## Part 2: reconciliation

### G1 Wall heights: agree, with modification

- Preserve the owner's original manual formula exactly:

  > wall height = slab-to-slab height - 0.60 m beam allowance - 0.15 m decorative ceiling allowance - 0.10 m floor
  > allowance

  For Alsenan this gives GF **3.65 m**, 1F **3.35 m**, 2F **3.35 m**. These are the owner-defined manual measurement
  heights.
- Use them for the owner-manual BOQ calculation where the method applies and no confirmed project-specific detail
  overrides it.
- Also calculate drawing-derived wall heights wherever the documents give sufficient evidence, and show both results and
  their differences.
- Do not claim that the manual 0.60 m beam allowance is the actual beam depth in every room.
- **Do not classify every drawing-derived height as held simply because a reflected ceiling plan is absent.** Search
  architectural sections, elevations, ceiling details, room schedules and other applicable documents first.
- For plaster, paint and wet-wall tiles, keep separate finish boundaries and measurement rules.
- If an applicable project detail explicitly gives a different height, flag the difference and use the confirmed
  project requirement for the drawing-derived quantity.
- Do not erase or modify the owner's manual calculation.

### G2 Ground-floor annex height: B for the released quantity, manual result kept as provisional

- Keep the owner's calculation: +4.30 - +0.30 = 4.00 m; 4.00 - 0.60 - 0.15 - 0.10 = **3.15 m**. Show it as
  **OWNER MANUAL METHOD - PROVISIONAL**.
- Section B-B shows +4.30 is not the structural slab level, so the 4.00 m slab-to-slab assumption is not confirmed.
- Do not release the annex wall quantity with 3.15 m as a confirmed height. Request the actual structural slab datum and
  the applicable finishing height.
- Keep the manual calculation for comparison and provisional estimating, and hold the final height-dependent quantity
  until the conflict is resolved.

### G3 Footing F10 bigger area: agree, with the original Q-31 limitation kept

- Q-31 stays a project-specific provisional instruction for F10. The 2.275 m3 candidate is provisional, not verified.
- The larger quantity is not automatically correct because it is conservative. Keep the competing geometries and
  calculations.
- Request designer clarification, and independently verify the footing plan, section and dimensions.
- Q-61 does not cancel Q-31. The general principle remains: the engine must not arbitrarily select the largest quantity.
- Do not release the F10 candidate as a verified final quantity without the required evidence.

### G4 Mortar 1:4: agree, with modification

- Preserve the owner's Q-45 manual purchasing method, per 1 m3 of 1:4 mortar:
  - cement **8 bags** of 50 kg;
  - sand **1.10 m3**.
- Also keep the previously approved **5 % purchasing waste** allowance (Q-09 / Q-45), if the decision register confirms
  it applies to these materials. Waste goes in a separate column, never inside the consumption rate.
- For comparison, show the theoretical ratio-derived method: about 7.7 bags and 1.06 m3 of sand. Theoretical consumption
  and manual purchasing quantities are different outputs. Never silently replace 8 bags and 1.10 m3 with the theoretical
  values.
- Verify whether the 5 % waste is applied to the material quantities before rounding to whole bags or purchasing units.
  Never apply the same waste allowance twice.
- For 1:3 mortar, keep the separate calculated method (about 9.6 bags and 1.00 m3 of sand per m3), subject to its stated
  assumptions.

### G5 Main stair concrete overlap: agree, conditional on independent 3-D verification

- Keep three figures:
  - the owner manual calculation, **5.011 m3**;
  - the proposed corrected calculation, **4.951 m3**;
  - the proposed overlap deduction, 0.060 m3.
- 4.951 m3 may become the released measurement only after the actual concrete intersection is independently verified.
- Never deduct an overlap merely because two plan polygons intersect: the structural solids must physically overlap in 3-D.
- Verify the reported 0.163 m3 over all stairs separately. Keep 5.011 m3 as an auditable manual calculation.

## Section 5: dual-method design, agreed with modification

- Both the OWNER MANUAL METHOD and the DRAWING-DERIVED METHOD are preserved.
- **Not approved:** an unconditional rule that the manual method always becomes the released BOQ quantity.
- Distinguish five things:
  1. the owner manual calculation;
  2. the drawing-derived calculation;
  3. the provisional estimate;
  4. the independently verified quantity;
  5. the released BOQ quantity.
- The default calculation framework is the owner's approved manual methodology, using actual project dimensions where
  appropriate. Explicit applicable project details must not be ignored.
- When the two methods differ, keep both and explain the discrepancy. Use the confirmed project-specific measurement
  basis for the released quantity when the evidence and verification are sufficient.
- A genuine unresolved drawing contradiction or an unsupported critical dimension keeps the quantity held or provisional,
  according to its approved status. Never release a quantity just because the manual method can produce a number.
- Per affected element, record:
  - element id and location;
  - owner manual formula and result;
  - drawing-derived formula and result;
  - drawing and rule references;
  - difference in quantity and %;
  - reason for the difference;
  - applicable measurement basis;
  - confidence and verification status;
  - final released quantity, if authorised.
- Where the two methods measure different scopes, reconcile their boundaries before comparing percentages.
- Build this in a new controlled engine version: no edits to frozen methods and no silent change to released
  quantities. The aim is to keep the owner's engineering knowledge while making the engine better at understanding the
  actual drawings.

## Part 3: actions (state as given by the owner)

| # | Action | State | Instruction |
|---|---|---|---|
| 1 | Claude Code scheduled tasks with the repo attached | **NOT YET CONFIRMED** | Not complete until all four exist, each with the correct repository, each with one successful authorised test run. Never disable the old tasks before the replacements work. Permission changes stay narrowly scoped to the required commands. |
| 2 | Kuwait specification chapters 07100, 09200, 09300, 09400, 09900 | **NOT YET CONFIRMED** | Listed as outstanding until the PDFs exist and are verified. Never invent their contents or treat chapter numbers alone as evidence. |
| 3 | Designer questions (DESIGNER_CLARIFICATIONS.md) | **NOT YET CONFIRMED** | Keep the register open. The owner will confirm separately when they are forwarded. |
| 4 | Scanned construction books | **DEFERRED** | Priority goes to the Alsenan drawing reconciliation, structural quantities, wall heights and independent verification. Books later. |

## Final owner instruction

- Do not treat the owner's earlier manual BOQ answers as mistakes because the drawing-derived method gives a different
  result. His method stays available, reproducible and auditable.
- At the same time, do not force the final BOQ to follow an assumption when the project documents establish something
  different.
- The engine must understand why each quantity is calculated, which method applies, what evidence supports it, and
  whether it is safe to release.
- Proceed with the approved investigations and controlled implementation. No silent change to frozen methods; no release
  of unverified quantities.
