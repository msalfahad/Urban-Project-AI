# Owner decisions (Phase 2B-6): one deduplicated register

This register replaces the three earlier phase lists:

- `research/urban_m9_p2b0/OWNER_DECISIONS.md`;
- `research/urban_m9_p2b3/OWNER_DECISIONS_OPEN.md`;
- `research/urban_m9_p2b5/OWNER_DECISIONS.md`.

Each earlier question is either **still open**, **answered** (by the owner's Part 4 statement or the registry), or
**not an owner question** (the drawing or a rule settles it, or it is software work). An answered question is never
asked again. Where the owner's knowledge already decides it, the registry rule is named.

## Answered: not to be asked again

| id | earlier question | answer | source | what the software must do |
|---|---|---|---|---|
| D-12 (2B-5 #11) | is a basin lobby a wet area? | **No, not merely because it holds a wash basin.** If the classification is genuinely unresolved, keep a review status | owner, Part 4 of this program | type a basin-only space for review, not wet (Experiment G; D-P6-07); record the policy in knowledge 1.2.0 |
| D-02 (2B-5 #2) | skirting in wet rooms whose wall tile is not full height | wet rooms take **full-height** wall porcelain and **no conventional skirting where the walls are fully tiled** | owner, Part 4; UP-WET-001 | the 2.40 m wall-tile height used in tests is a synthetic parameter. Real heights come from sections and schedules (Part 4 "Heights"). A drawing that shows part-height tile in a wet room conflicts with the owner requirement: keep both and flag |
| D-05 (2B-5 #5) | bathroom door openings below the owner standard: enlarge or accept? | the BOQ carries the drawn opening, the owner-required opening (minimum nominal door + 0.10 m), the required enlargement and a review status, **separately**, and never alters the drawn geometry | owner, Part 4; UP-DOOR-OPEN-002 (ordinary 1.00 → 1.10 m wall opening, bathroom 0.90 → 1.00 m) | already done by the door-feasibility views. Enlarging a given door is a design-coordination action, not a BOQ question |
| D-06 (2B-5 #6, withdrawn) | the reconciled two-way door's width | **the drawing settles it**: the symbol's jamb lines are 0.80 m apart, and the rest of the gap is proven wall | the drawing | Experiment A (D-P6-01) |

## Not owner questions (software or drawing)

| id | topic | why it is not asked | where it is handled |
|---|---|---|---|
| D-03 (2B-5 #3) | a doorless lobby merged into a wet room | under Part 4, an unresolved classification keeps a review status. The software must stop imposing wet scope silently. A policy question would only arise if the owner wants one | D-C3 in `ENGINEERING_DEFECT_REGISTER.md`; `NEXT_IMPLEMENTATION_PLAN.md` |
| - | single-instance layers, exploded doors, turned or exploded columns, nested plans | the drawing's geometry settles them, or the user declares roles; a software problem (Part 4) | run audit; Experiment C |
| - | the structural-vs-clear meaning of a CAD gap | the engine measures the drawn band gap as the structural (wall) opening; a schedule that states otherwise prevails and is flagged (UP-DOOR-OPEN-002 conflict rule) | door model |

## Still open: genuine owner decisions

| id | decision | options | what it unblocks | recommendation |
|---|---|---|---|---|
| **D-14** (new) | authorise an opt-in method with the proven corrections (`NEXT_IMPLEMENTATION_PLAN.md`) | authorise / defer | on the five independently read real rooms: 8 → 0 failing checks of 66. Synthetic: the held-door width, exploded single doors, turned or exploded columns, curved wall run | authorise. It is isolated (V1 - V2.6 stay byte-identical), and every change was proven tonight in a clone |
| **D-01** (2B-5 #1) | floor-to-wall waterproofing junction detail | separate upstand at a stated flange; continuous fold | releases the waterproofing procurement figure (now PROVISIONAL_DETAILS_OPEN) | owner's detail choice |
| **D-04** (2B-5 #4) | project heights for the reference villa | supply sections / schedules or project values; or approve labelled fallbacks (ASSUMED) | every wall-area line (plaster, wall porcelain, paint, masonry) | supply the sections: the engine must read them first (Part 4) |
| **D-07** (new) | basis of the wall run on curved walls | mean radius (MID_BAND_ARC: run x thickness = the band's plan area, as for straight walls) / inner face / outer face | ARCH.WALL_RUN and masonry on curved walls (+0.88 % of the reference plan's wall run on the mean radius, +0.80 % on the inner face) | mean radius. The other two stay published beside it |
| **D-13** (new) | start the formal blind evaluation | when the corrected method is frozen and a second real plan is verified / now / later | the only basis for an accuracy claim | after D-14 and a second plan |
| **D-15** (new) | a second real villa drawing set with an independent takeoff (input, not policy) | supply / not yet | verification of the corrections beyond one plan, before any freeze | supply one |
| D-08 (2B-5 #7) | PyMuPDF licence | AGPL compliance / Artifex commercial licence | the vector-PDF route for PDF-only sets | decide before any external distribution or hosted service |
| D-09 (2B-5 #8) | waterproofing offcut reuse and selection order (N-7, N-9) | reuse across areas / keep each area alone | the REUSABLE_SUBJECT_TO_N7 offcuts; no quantity until decided | - |
| D-10 (2B-5 #9, optional) | connect a CAD MCP server | which server, synthetic fixtures first | an MCP row in the benchmark | low priority: the one CAD MCP room reader tested tonight (as a library) found 1 of 5 rooms |
| D-11 (2B-5 #10, optional) | a trained floor-plan model | a cleared training set (Urban's own annotations), local inference | scans | not now (`FLOORPLAN_AI_RESEARCH.md`) |

## The rule this register follows

| what settles a question | so the software must... |
|---|---|
| the drawing | read it; never ask |
| the software cannot read the drawing | treat it as a software problem; never ask |
| a registry rule or an owner statement | follow it, cite it; never ask again |
| a genuine conflict between the drawing and an owner requirement | keep both and flag it |

Only what remains after these four is listed as open.
