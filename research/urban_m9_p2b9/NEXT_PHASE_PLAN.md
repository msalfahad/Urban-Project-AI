# Next-phase plan (proposed)

The plan is ordered by value to a complete, defensible architectural BOQ. Nothing below starts the blind evaluation
or freezes a version. Both need the owner's authorisation (`SECOND_VILLA_READINESS.md`).

| Rank | Work | Why | Acceptance (hand truth first) |
|---|---|---|---|
| 1 | **Owner supplies a second villa set with sections and schedules** (or, failing that, the reference plan's own sections / schedules if they exist outside the DXF) | every wall-area line now waits on drawing heights; V2.8 can read them | V2.8 run lists 0 missing heights for the rooms the sections cover |
| 2 | **D-P9-01 / D-P9-02 curved openings**: infer a window from a glazing arc concentric with a wall arc pair; close a curved opening on the room face | the room is lost or its floor over-counted by the reveal strip | example 4S: floor 7.068583, plaster from the inner face, reveal strip 0.438423 as reveal; adversarial set (an arc that is a hatch, a furniture arc) |
| 3 | **Blockwork m² / m³** from the wall run, once the block height (T.O.S. to soffit / beam) is evidenced by a section | the largest absent architectural quantity | a synthetic floor with a section: block area = run × (soffit − T.O.S. − beam) − openings |
| 4 | **Elevation reader** for window heads / sills (L-P9-02), with an ambiguity rule (arched heads, levels below the F.F.L.) | many sets carry heights only on elevations | synthetic elevations, rectangular and arched; the reference plan's must stay ambiguous unless resolvable |
| 5 | **D-P9-04 zone-bounded space**: cell-by-cell reconciliation; a reader rule for recesses vs openings | 13 unverified differences on the reference plan | the reader's face equals the engine's or the difference is explained by a stated convention |
| 6 | **Independent passage rule** (D-P8-05) for plaster / paint / tile | 4 unverified differences | passage deducted by its width at full height, hand truth |
| 7 | **Facade finishes** from the outer faces (already measured) | an absent category | external plaster / paint on a synthetic villa, outer arcs kept |
| 8 | Ceiling types / bulkheads (reflected ceiling plan) and stair risers / flights from sections | PROVISIONAL and BLOCKED today | hand truth per item |

**Owner decisions needed** (none was invented):

- OD-P9-01: adopt or amend `ACCEPTANCE_FRAMEWORK_PROPOSAL.md`, with category weights;
- D-16;
- D-17;
- the kitchen membrane scope;
- the reveal and sill finish by window type;
- the waterproofing junction / corner / penetration details;
- whether stubs under 0.05 m are ever masonry.
