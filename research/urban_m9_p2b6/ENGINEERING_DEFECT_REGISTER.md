# Engineering defect register (Phase 2B-6, Parts 6 and 12)

**Scope.** Every defect still open in ARCH_TAKEOFF_V2.6 after this program, plus the ones found tonight. None is
fixed in a method: V1 - V2.6 are unchanged (`TEST_EVIDENCE.md` §3).

**How tonight's defects are covered.**

- Those that alter a quantity are asserted *as found*, next to their hand truth, in
  `tests/m9_p2b6/test_p2b6_found_defects.py`.
- The read-only run audit (`tools/arch_run_audit.py`) names them on any run.
- The experiments that fix them are in `EXPERIMENT_RESULTS.md`, with the clone patch in `experiments/`.

**Classes, as Part 6 asks.**

| class | meaning |
|---|---|
| GEOMETRY | the measured shape is wrong |
| ROLE | the meaning of a layer is wrong |
| ALLOCATION | the right geometry is attributed to the wrong room or scope |
| COVERAGE | a quantity is withheld or held |
| PRESENTATION | no quantity changes |

## Register

| id | defect | class | affected quantities | measured exposure | independent reference | proposed general solution | regression risk | tests | readiness |
|---|---|---|---|---|---|---|---|---|---|
| **D-P6-01** (D-V26-06 residual) | a door drawn two ways at one opening is held, and takes the **wall gap's** width (1.027 m) instead of its symbol's (0.80 m) | GEOMETRY | door width; threshold; doorway waterproofing; reveal plaster; plaster, wall tile, skirting and upturn of both adjoining rooms (the opening deduction) | real plan: **7 of the 8** failing checks of 66, in one room. Synthetic: plaster −0.61 %, threshold +28 % | Phase 2B-5 raw-line jamb reading (ezdxf, not the engine); hand truth of CROSSING | Experiment A: the door takes its symbol's jamb span only when every remainder of the gap is proven wall on both faces (wall lines on the face, or a junction mouth); the remainders are closed as zero-material wall | a door set in a wider opening with an open side light or a column: such remainders are not proven wall, so they are refused and the case is kept for review (tested: OPEN_SIDE, COLUMN) | `test_d_p6_01` (as found); experiment: 7 synthetic variants, 1 real candidate | **ready for an opt-in method** |
| **D-P6-07** | an unlabelled space holding only wash-basin blocks is typed a wet room (FIXTURES) | ALLOCATION | the space's wet scope (floor tile, waterproofing floor / upturn, wall tile); the doorway waterproofing piece it takes from the adjoining W.C. | real plan: 3 spaces, 9.35 m2 of wet scope; **the last** failing check of 66 | Stage C reading; the owner statement (Part 4) | Experiment G: a basin alone does not type a space; it stays unlabelled with WET_CLASSIFICATION_REVIEW. Refinement needed: read a WC drawn as linework on a sanitary layer before withholding | a real W.C. whose WC is drawn as plain lines would lose its wet scope (to review, not to dry) until the WC-shape reader exists | `test_d_p6_07` (as found); audit A09 | **ready with the WC-shape refinement**; the owner's rule goes into the registry (knowledge 1.2.0) |
| **D-P6-02** | a single **exploded** door symbol (jamb and frame lines, leaf, swing) types its layer **WINDOW**: its lines lie in the wall gap, and the door rule needs two swings | ROLE → GEOMETRY | the swing bounds the room (floor, ceiling, waterproofing floor −π r²/4; perimeter +); the door counted as a window; the real window becomes a passage | synthetic: −3.2 % floor (0.385 m2), +1.10 m perimeter. Real plan: not affected (many doors) | hand truth (PLAIN: 12.00 m2, 14.00 m) | Experiment C: the single-instance door signature (hinge at a wall-gap jamb, door symbols explain ≥ 80 % of the layer) runs before the window rule, and window lines are counted only in gaps that hold no door | none on villa / mirror / reference plan (roles identical) | `test_d_p6_02`; audit A01 | **ready** |
| **D-D1** | a layer holding one door, one window or one column is not recognised (count thresholds: 2 swings, 4 lines, 3 squares) | ROLE | doors and windows read as passages: no door set, threshold or doorway lines. Columns not deducted | benchmark: 11 single-door drawings; B04 / C03 floor +2.18 % | benchmark hand truth | doors and windows: Experiment C signatures (15 / 15 benchmark cases exact). Columns: see D-P6-03 | adversarial set (wardrobe, threshold line) passes after the jamb and gap signatures | `tests/m9_p2b5_bench/test_bench.py` (as found); audit A02 / A03 / A11 | doors / windows **ready**; columns **not** |
| **D-P6-03** | small filled squares are typed COLUMN whatever they are: three hatched 0.15 m drains on one layer pass the count rule | ROLE | drains deducted from a (wet) floor; their faces skirted, tiled and upturned | synthetic: −0.0675 m2 floor, +1.80 m of finished perimeter | hand truth | geometry cannot separate a drain from a small column. A column role needs corroboration: the structural plan / column schedule, a declared role, or a column grid. Until then, the audit (A04) asks | - | `test_d_p6_03`; audit A04 | **design** (needs the structural cross-reference) |
| **D-P6-04** | the column inference reads only **axis-aligned** rectangles: a plan turned in its sheet loses its columns | ROLE → GEOMETRY | columns not deducted; their faces missing from plaster, skirting, paint | synthetic villa at 30°: 3 columns lost; a bedroom's plaster −10.4 %, floor +1.2 % | the villa's declared-role run (invariant) | oriented rectangle detection (Experiment C's loose rectangles); declared roles remove it today | none found | `test_d_p6_04`; audit A06 | **ready** (with C) |
| **D-P6-08** | the column inference reads only rectangles drawn as **one closed polyline**: a column of four LINEs is not inferred | ROLE | as D-P6-04 | synthetic: 0.09 m2 not deducted | hand truth | as D-P6-04 (four-line loops) | as D-P6-04 | audit A06 (`drawn_as: LINES`) | **ready** (with C) |
| **D-D2a** | an arc-walled room's polygon, `rect` and `dims` are the chord | PRESENTATION + layouts | membrane / tile layout pieces on the chord. Areas, perimeters, plaster, tile, skirting and upturn are already exact on the arc | B10: 1.02 m2 of 13.02 had no planned piece. Real plan: 4 of 38 rooms, all dry: no quantity changes | the circular-segment formula | Experiment B1: arc edges flattened into the polygon (sagitta ≤ 1 mm) | none: the area lines keep the exact segment term | `test_p2b5_curved_wall.py` (as found) | **ready** |
| **D-D2b** | a curved wall band is missing from the wall run (the band census reads straight lines only) | GEOMETRY | ARCH.WALL_RUN; MAS.BLOCK (once heights / material exist); the junction-piece conservation | B10: run 11.0 → 14.35 m (MID). Real plan: **+1.885 m, +0.88 %**, one band | raw-ezdxf arc census (not the engine): identical to 1e-6; the B10 wall-mass conservation | Experiment B2: concentric-arc band census; the run takes the mean-radius length (run x t = plan area, as for straight bands); all three bases published | the basis is a convention (`OWNER_DECISIONS.md` D-07) | audit A07 | **ready** (basis to confirm) |
| **D-P6-05** | a plan drawn inside a block holds every door: the door-frame evidence is read across the whole block occurrence (frame span 9 - 12 m vs 0.8 - 1.0 m openings) | COVERAGE | every door set held (not released); flagged REVIEW | synthetic villa: 5 of 5 internal door sets held; nothing else changes | the unnested run | scope the frame search to the swing's own nested occurrence (or a window around the opening) | low | `test_d_p6_05`; audit A05 | **design** (one function in the door model) |
| **D-P6-06** | a plan turned off the axes and drawn in metres gets a **zero-length** waterproofing termination line (a sub-tolerance sliver edge kept by a 1e-9 m filter in `wp_geometry.segments`) | PRESENTATION | one extra line with no quantity, and its review note | synthetic: 1 line | invariance against the mm drawing | merge pieces shorter than the edge tolerance | none | `test_d_p6_06`; audit A10 | **ready** (trivial; only in a new method, as V2.4 - V2.6 pin it) |
| D-C2 (2B-5) | leaf-closed doorways: the threshold is withheld (the opening is not established) | COVERAGE | marble thresholds; doorway strips | real plan: 5 doorway faces | raw jamb reading (2B-5 §8) | establish the opening from the symbol's jamb lines, as Experiment A does for held doors (not tested tonight on leaf-closed faces) | - | 2B-5 strip-split tests | design (A's machinery applies) |
| D-C2b (2B-5) | two leaf-closed doorway waterproofing pieces still take their whole face (an irregular face; a column) | GEOMETRY | doorway waterproofing | real plan: 2 pieces | 2B-5 raw reading | the closure box with column / irregular-edge handling | - | 2B-5 refusal tests | design |
| D-C3 (2B-5) | a doorless cell merged into a wet room takes the wet scope silently | ALLOCATION | wet scope of the cell | one sample room: 44 % of its area | Stage C | an attachment note and a review status (owner decision on doorless lobbies, `OWNER_DECISIONS.md` D-03) | - | - | design |
| D-C5 | wall-area lines rest on heights (synthetic in tests) | INPUT | plaster, paint, wall tile, masonry | every wall line | - | heights from sections / schedules; owner fallbacks labelled ASSUMED | - | - | needs a section reader or project facts |
| L-01 | a sheet frame turned with its plan is refused at admission | LIMITATION (safe) | - | - | - | none needed: refusal is correct | - | - | - |
| G-* | catalogue gaps: no measured items for formwork, excavation, aluminium windows / glazing (only counts), roof and balcony finishes, interlock paving, elevator-shaft finishes, decorative ceilings, hidden skirting, external walls | COVERAGE | whole BOQ families | see `BOQ_CAPABILITY_MATRIX.md` | - | see `PRIORITIZED_ROADMAP.md` | - | - | roadmap |

## Separating geometry from allocation (Part 6)

**Geometry defects** — the measured shape is wrong:

- D-P6-01: opening width;
- D-D2b: curved band;
- D-P6-04 / 08: columns not seen;
- D-C2b: irregular doorway piece.

Their fixes change areas and lengths, and are proven against hand truth and raw-entity readings.

**Role defects** — what a layer means is wrong:

- D-D1, D-P6-02, D-P6-03.

They become geometry defects downstream: a swing becomes a wall, or a drain a column.

**Allocation defects** — the shape is right, but it goes to the wrong room or scope:

- D-P6-07: basin lobby;
- D-C3: doorless cell;
- threshold ownership: settled by D-V26-07 in 4 of 5 sample doorways.

Their fixes move quantities between rooms or scopes without changing the plan totals of floor or wall. Only the owner's
rules decide them: no geometry test can.

## What changed in the register tonight

- **Narrowed.**
  - D-V26-06 / D-C1: from "the width should follow the symbol" to a rule that generalizes, tested on 7 synthetic
    variants and the plan's 1 candidate (→ D-P6-01).
  - D-D1: doors and windows can be solved by geometry; columns cannot without a second source.
- **New:** D-P6-02 to D-P6-08. They were found by adversarial fixtures and the transformation harness; the benchmark's
  block-drawn doors and axis-aligned columns had hidden them.
- **Answered by the owner:** D-P6-07. The owner's statement turns the basin-lobby question (2B-5 decision 11) into a
  software defect.
- **Corrections to earlier claims:**
  - C-09: the curved wall run was "~0.7 %" of the plan's wall run; measured, it is 0.80 % (inner face) or 0.88 %
    (mean radius).
  - C-10: the B10 test's future wall-run truth (14.217506 m) is the inner-face basis, a convention, not a fact.
  - C-11: "a single door's layer reads as a passage" (D-D1) holds for block doors. An exploded door layer reads as
    WINDOW, and the error is larger (D-P6-02).
