# Owner decisions (Phase 2B-7): one deduplicated register

This register carries `research/urban_m9_p2b6/OWNER_DECISIONS.md` forward. Every id keeps its number.

- An answered question is never asked again.
- A question the drawing or a rule settles is not an owner question.
- Only three ids are new: D-16, D-17, D-18.

## What changed since Phase 2B-6

| id | change |
|---|---|
| D-14 | **answered**: the opt-in method is authorized; ARCH_TAKEOFF_V2.7 is built (`V27_IMPLEMENTATION_REPORT.md`) |
| D-12 | answered in 2B-6; **implemented** in V2.7 (UP-WET-002), with one refinement found on the reference plan: a basin's own fittings drawn loose on a sanitary layer are not a second piece of evidence |
| D-06 | answered in 2B-6 (the drawing settles it); **implemented** (D-V27-01). On the reference plan the door now takes its 0.80 m jamb span |
| D-05 | **split**. The BOQ presentation (drawn opening, required opening, enlargement and review status kept separately; the drawn geometry never altered) stays answered. The numeric reference of the minimum is **reopened as D-16**, as Section 4 of the Phase 2B-7 authorization requires. Frozen methods keep UP-DOOR-OPEN-002 (1.1.0) unchanged |
| D-16, D-17, D-18 | new (below) |

## Answered: not to be asked again

| id | question | answer | source | software |
|---|---|---|---|---|
| D-14 | authorize an opt-in corrected method | authorized, opt-in, V1 – V2.6 byte-identical | Phase 2B-7 authorization | ARCH_TAKEOFF_V2.7 |
| D-12 | is a basin lobby a wet area? | not merely because it holds a wash basin; if unresolved, a review status | owner, Phase 2B-6 Part 4 | UP-WET-002 (knowledge 1.2.0); V2.7 types such a space REVIEW, never DRY, and holds its doorway's finish too |
| D-02 | skirting in wet rooms | full-height wall porcelain, no conventional skirting where fully tiled | owner; UP-WET-001 | unchanged |
| D-05 (presentation) | doors below the owner standard | drawn, required, enlargement and status separately; never alter the drawn geometry | owner; UP-DOOR-OPEN-002 | V2.7 adds the seven-reading record (UP-DOOR-OPEN-003) |
| D-06 | the reconciled two-way door's width | the drawing settles it | the drawing | D-V27-01 |

## Not owner questions (software or drawing)

| id | topic | where handled |
|---|---|---|
| D-03 | a doorless lobby merged into a wet room | software (D-C3, still open in `ENGINEERING_DEFECT_REGISTER.md`): attach with a note and a review status |
| - | single-instance layers, exploded doors, turned / four-line columns, nested plans, rows of aligned columns | V2.7 (D-V27-02, -03, -07) |
| - | WC drawn as lines / in anonymous blocks / Arabic or English words | V2.7 (D-V27-05); the two known shape errors are software limitations, not questions |

## Still open: genuine owner decisions

| id | decision | options | what it unblocks | recommendation |
|---|---|---|---|---|
| **D-16** (new; OQ-05) | **what the owner minimum door width refers to**, and whether a frame / installation allowance applies | the minimum (1.00 m ordinary, 0.90 m bathroom) is the structural wall opening / the door leaf / the clear passage; an allowance of 0.10 m (the 1.1.0 registry's value), another value, or none | the required opening and the proposed enlargement of every V2.7 door row. Each now shows the shortfall on every reading and a range (low; high with the registry allowance) | state the reading the minimum refers to. If it is the leaf, state the frame allowance per door type (PVC / aluminium) |
| **D-17** (new; project input) | the type of three basin-only spaces on the reference plan (hand-wash areas, 9.35 m2 in all) | wet / dry / one by one | their floor, wall and waterproofing scope, and their doorway finishes; each is a WET_CLASSIFICATION_REVIEW item in the run | answer per space; the drawing does not establish it |
| **D-18** (new) | for a space under wet-classification review, release the quantities both readings share? | release ceiling and plaster (same in both), hold floor / wall finish and waterproofing / hold everything (current) | ceiling and plaster of review spaces (on the reference plan: 9.35 m2 of ceiling and the walls' plaster) | release the shared quantities, labelled; hold the type-dependent ones |
| D-07 | basis of the wall run on curved walls | mean radius (MID_BAND_ARC) / inner / outer face | ARCH.WALL_RUN on curved walls: one band on the reference plan, 1.884956 m on the mean radius (1.727876 inner, 2.042035 outer) | mean radius (run x thickness = the band's plan area); the other two stay published |
| D-01 | floor-to-wall waterproofing junction detail | separate upstand / continuous fold | the procurement figure | owner's detail choice |
| D-04 | project heights | sections / schedules / labelled fallbacks | every wall-area line | supply sections; the next phase reads them first (`NEXT_PHASE_PLAN.md` P1) |
| D-13 | start the formal blind evaluation | not started, as instructed | the only basis for an accuracy claim | after V2.7 is reviewed and D-15 is supplied |
| D-15 | a second real villa drawing set with an independent takeoff | supply / not yet | verification beyond one plan | supply one; V2.7 has been checked on one real plan only |
| D-08 | PyMuPDF licence | AGPL / commercial | the vector-PDF route | before any distribution |
| D-09 | waterproofing offcut reuse (N-7, N-9) | reuse / keep apart | REUSABLE_SUBJECT_TO_N7 offcuts | - |
| D-10 | connect a CAD MCP server (optional) | which, synthetic first | an MCP benchmark row | low priority |
| D-11 | a trained floor-plan model (optional) | cleared data, local inference | scans | not now |

## The rule this register follows

| what settles a question | so the software must... |
|---|---|
| the drawing | read it; never ask |
| the software cannot read the drawing | treat it as a software problem; never ask |
| a registry rule or an owner statement | follow it, cite it; never ask again |
| a genuine conflict between the drawing and an owner requirement, or a requirement whose meaning is ambiguous | keep both readings and flag it (D-16) |
