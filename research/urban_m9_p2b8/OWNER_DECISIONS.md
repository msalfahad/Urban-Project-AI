# Owner decisions (Phase 2B-8): one deduplicated register

This register carries `research/urban_m9_p2b7/OWNER_DECISIONS.md` forward, and every id keeps its number.
- An answered question is never asked again.
- A question the drawing or a rule settles is not an owner question.
- Two ids are new: OD-P8-01 and OD-P8-02.

## What changed since Phase 2B-7

| id | change |
|---|---|
| D-18 | **answered** by the Phase 2B-8 instruction: release only quantities whose measurement and scope are invariant between the plausible classifications; never release plaster automatically if a wall-tiling specification would change the plaster system; never add scenarios together. **Implemented** in V2.7.1 (UP-REVIEW-001). Only the ceiling is released; the wall face is reported as confirmed geometry, not as plaster |
| D-16 | still **open**. The Phase 2B-8 instruction keeps the owner minimums (1.00 m ordinary, 0.90 m bathroom) and forbids assuming a universal 0.10 m allowance until D-16 is resolved. V2.7.1 implements exactly that (`DOOR_STANDARD_RECONCILIATION_DEMONSTRATION.md`) |
| D-13 / D-15 | the Phase 2B-8 instruction sets the order: seal a benchmark protocol and an independent reference **before** any blind run. The protocol is sealed (`benchmark/`); no second villa exists in the workspace. **OD-P8-02** replaces D-15's request |
| OD-P8-01 | new: approve or amend the benchmark acceptance criteria |
| OD-P8-02 | new: supply the second villa set and appoint the independent QS |

## Answered: not to be asked again

| id | question | answer | source | software |
|---|---|---|---|---|
| D-18 | for a space under wet-classification review, release the quantities both readings share? | yes, but only quantities invariant in measurement **and** scope; plaster is not released while a wall-tiling specification could change its system; scenarios are never added | Phase 2B-8 instruction, Section 1 | V2.7.1 (UP-REVIEW-001, UP-QTY-STATUS-001) |
| D-05 (presentation) | doors below the owner standard | keep the as-drawn opening, the jamb span, the leaf, the clear width, the minimum, the allowance (only if evidenced), the enlargement and the review status separately; never alter the drawn geometry | owner; Phase 2B-8 Section 2 | V2.7.1 reconciliation (UP-DOOR-OPEN-003 1.3.0) |
| D-14 | an opt-in corrected method | authorized; V2.7 provisionally accepted as an opt-in development method, not for a production freeze | Phase 2B-7 / 2B-8 | ARCH_TAKEOFF_V2.7, V2.7.1 |
| D-12 | is a basin lobby a wet area? | not merely because it holds a basin; unresolved → review status | owner, Phase 2B-6 | UP-WET-002 |
| D-02 | skirting in wet rooms | full-height porcelain: no conventional skirting where fully tiled | owner; UP-WET-001 | unchanged |
| D-06 | the reconciled two-way door's width | the drawing settles it | the drawing | D-V27-01 |

## Not owner questions (software, drawing or engineering)

| topic | where handled |
|---|---|
| WC-sized chair against a wall (L-P8-01) | software limitation; needs a second evidence source |
| wall stubs shorter than 0.30 m (D-P8-03) | engineering: measure as wall (QS practice), versioned |
| spaces closed by a non-wall line (D-P8-04), passages (D-P8-05) | verification tooling |
| a doorless lobby merged into a wet room (D-C3) | software, open |

## Still open: genuine owner decisions

| id | decision | options | what it unblocks | recommendation |
|---|---|---|---|---|
| **OD-P8-01** (new) | approve the blind-benchmark acceptance criteria (URBAN_BLIND_V2 §6) | as proposed: per metric coverage ≥ 0.90, within tolerance ≥ 0.90, \|total error\| ≤ 3 %, 0 silent omissions, false positives ≤ 2 % / amend / per-category values | the formal blind evaluation; until then results are PROPOSED_PASS / FAIL only | approve as proposed, or tighten room areas; must be decided **before** the run (a re-seal) |
| **OD-P8-02** (new; replaces D-15) | supply a second independent villa drawing set and appoint an independent QS for its reference | supply / not yet | the only route to an accuracy statement (V1 §8 needs two blind projects) | supply one complete set (all plans, sections, schedules); the QS measures it to `benchmark/REFERENCE_TEMPLATE.json` without seeing any engine output |
| **D-16** (OQ-05) | what the owner minimum door width refers to, and whether a frame allowance applies | the structural opening / the door leaf / the clear passage; an allowance of 0.10 m / another / none, per door type | the required opening and enlargement of every door; on the reference plan 18 of 28 doors are below the minimum on every reading, 5 depend on the reading | state the reading; if the leaf, the allowance per door type (PVC / aluminium) |
| **D-17** | the type of the three hand-wash spaces on the reference plan (9.348195 m²) | wet / dry / per space | their floor, wall, skirting and waterproofing scope; V2.7.1 now releases their ceilings and reports their wall faces | answer per space |
| D-07 | basis of the wall run on curved walls | mean radius / inner / outer | the curved wall run (1.884956 m on the mean radius) | mean radius; the other two stay published |
| D-13 | start the formal blind evaluation | after OD-P8-01 and OD-P8-02 | the accuracy statement | not before the reference is committed and the criteria approved |
| D-01 | floor-to-wall waterproofing junction detail | separate upstand / continuous fold | the procurement figure | owner's detail choice |
| D-04 | project heights and window sills | sections / schedules / labelled fallbacks | every wall-area line; skirting and tile at windows (D-P8-06) | supply sections and a window schedule |
| D-08 | PyMuPDF licence | AGPL / commercial | the vector-PDF route | before any distribution |
| D-09 | waterproofing offcut reuse (N-7, N-9) | reuse / keep apart | offcut figures | — |
| D-10 / D-11 | CAD MCP server; a trained floor-plan model | optional | — | low priority |

## The rule this register follows

| what settles a question | so the software must... |
|---|---|
| the drawing | read it; never ask |
| the software cannot read the drawing | treat it as a software problem; never ask |
| a registry rule or an owner statement | follow it, cite it; never ask again |
