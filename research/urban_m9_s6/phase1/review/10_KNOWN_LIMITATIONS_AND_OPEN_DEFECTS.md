# Known limitations and unresolved defects (state at c757d8a plus this review)

## New in this review

| Id | Defect | Severity | Affects | Silent? | Phase 2 item |
|---|---|---|---|---|---|
| S6R-A1 | strict float comparison at drafted thresholds. A drafted 100 mm wall-face piece survives about 50 % of the time at a random rotation, in mm and in m. Latent at the 300 mm overlap and the 500 / 400 mm gaps | HIGH | V1, V2, M4 / route-G lintel evidence | yes | P2-01 |
| S6R-A2 | frozen V1 and route-G / M4 lintel evidence miss a drafted door and a drafted window on the reference plan | HIGH (frozen) | frozen results | yes | P2-00 errata; route-G correction deferred to the owner |
| S6R-A3 | strip ids hash raw coordinates, so the same strip gets a different id in another unit | LOW | V2 | no | P2-03 |
| S6R-A4 | the metamorphic harness never rotates by non-right angles or uses site-scale offsets | MED (test gap) | all | — | P2-02 |
| S6R-B1 | 8 of 29 drawn door swings have no door line (7 CLOSED, 1 unresolved) | HIGH | V1, V2 | yes (only a door-status count in `ARCH_PLAN.json`) | P2-04 |
| S6R-B2 | engine defects are emitted as client RFIs (14 of 85 lines) | MED | V2 | no | P2-06 |
| S6R-B3 | one RFI line per element, not per question (85 lines, 4 questions) | MED | V2 | no | P2-06 |
| S6R-B4 | rule conflict: wet-room tile full height (method register, `finish_height.py`) vs derived per face (UP-CER-009, `arch_measure`) | MED | V2 Q7 lines | no | owner decision |
| S6R-B5 | no plaster or paint quantity on the reference plan (heights not established); the gate still says PASS | MED (expectations) | V1, V2 | no (RFIs) | P2-08; needs sections |
| S6R-C5 | `gross_floor_plate_m2` is the largest wall-network component only, without saying so | LOW | V1, V2 | no | label it (S) |
| S6R-D1 | fills read from model space only, first path, edge start points, no layer-0 inheritance (the root of four FLAGGED rows) | MED | V1, V2 | flagged in V2 | P2-05 |
| S6R-D2 | 388 DIMENSION entities unread: no independent evidence used | MED | all | warned | P2-09 |
| S6R-D3 | 51 texts in an unmapped Arabic SHX font are undecoded; no discovery finding | MED | V1, V2 | **yes** (`RUN_RULES` only) | P2-10 |
| S6R-D4 | curved walls are not wall bands in the architectural path | MED | V1, V2 | yes, for curved walls | deferred (flag first) |
| S6R-D5 | linetype (hidden / dashed) is not read | MED | V1, V2 | possible | P2-11 |

## Carried from Phase 1 (unchanged)

- **Reader fixes not done.** Nested / MINSERT / SOLID fills, layer-0 inheritance for fills, rotated / exploded columns, fewer than three columns, non-uniform door blocks, Arabic diacritics, honouring the layer state. V2 flags them; none is silent in V2.
- **Discovery stages 3 and 8 are NOT_RUN.** Stage 3 is drawing identity, title block and revision; stage 8 is the feature census.
- **Paper space.** A plan shown only through a viewport stops (or needs `--region`).
- **Vertical model.** No section source on the reference plan (`NO_SECTION_SOURCE`, BLOCKED_ITEM, stage 7). Every finish height is NOT_ESTABLISHED without facts.
- **Owner rules not approved:**
  - Q-S6-1 thresholds;
  - Q-S6-4 stair hall;
  - Q7 band above wet tile;
  - Q1 exterior;
  - Q-OPN-1, the plaster / paint opening deduction;
  - the surface-eligibility table.
- **Route G structural defaults.**
  - The warning lives in `urban_boq_m9` only.
  - The frozen entry points `urban_boq_m2` and `urban_project_run` still default silently.
  - Changing that is an owner decision.
- **One real drawing.** Every real-drawing result comes from one villa (R8).

## What is not claimed

- No accuracy percentage. No "95 %".
- Nothing is quotation-ready.
- The test gate is **INCOMPLETE**: 376 mandatory tests are blocked by missing data.
- No result was tuned to benchmark or human quantities. The benchmark was not read in this review.
