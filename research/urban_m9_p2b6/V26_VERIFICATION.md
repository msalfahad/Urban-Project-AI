# V2.6 verification: the ten questions of Part 5

The baseline was reproduced before anything else (`REPOSITORY_BASELINE.md` §2). Every claim below rests on a re-run
from tonight or on a cited test.

## 1. What is genuinely implemented?

In the opt-in method `ARCH_TAKEOFF_V2.6`:

- **The waterproofing construction layer (Stage B)** (`engine/source/wp_install.py`):
  - piece plan, offcuts, joints, seams, corners, penetrations, drains;
  - the open floor-to-wall junction with its alternatives.

  No BOQ quantity changes by design.
- **D-V26-06: one door drawn two ways at one opening** (`arch_rooms.closure_in_passage`, `match_swings_review`). It is
  reconciled into one held DOOR (DOOR_SYMBOL_FIT_REVIEW), and its doorway waterproofing is PROVISIONAL.
- **D-V26-07: doorway strips split at the opening box** (`arch_completeness.split_strips`, `closure_box`).

Beside the method:

- the room-reader benchmark;
- the raster / vector-PDF vision prototypes and the hybrid reconciliation (test tree only);
- six repository skills.

Added tonight:

- the read-only run audit (`tools/arch_run_audit.py`);
- the Phase 2B-6 tests.

## 2. What is only researched?

- floor-plan AI models (`FLOORPLAN_AI_RESEARCH.md`);
- CAD MCP servers (none connected; one run as a library, `EXPERIMENT_RESULTS.md` H);
- geometry libraries (`CAD_MCP_GEOMETRY_RESEARCH.md`);
- the knowledge-class design (`ENGINEERING_SKILLS_AUDIT.md`).

## 3. What is experimental?

Experiments A, B1, B2, C and G run in an isolated clone behind `URBAN_EXP`. The patch is in
`experiments/ENGINE_EXPERIMENTS_NOT_APPLIED.patch` and is not applied. So are the vision prototype and the U-C4N
library run.

## 4. What is production-capable?

Nothing is production-released: the formal blind evaluation has not started, and no quantity is engineer-released.

**Behaves as designed and is verified on independent truth:**

- the architectural route for straight-walled plans with declared or well-populated layer roles: room areas,
  perimeters, ceilings, waterproofing floors, windows;
- every line that follows the room boundary, curved boundaries included (plaster, tile, skirting, upturn on B10 equal
  the arc formulas);
- the frozen-method machinery: byte identity, the freeze verifier, run records.

**Production-capable as a check:** the run audit.

## 5. What remains provisional?

- waterproofing procurement (the junction detail is open);
- the held door and its doorway waterproofing;
- thresholds at pantry / external doorways (by rule);
- every wall-area line, which rests on heights (synthetic in tests);
- door classes that wait for the main-entrance review;
- every quantity the run audit flags.

## 6. Which calculations have independent verification?

| calculation | independent reference |
|---|---|
| ten waterproofing examples (297 checks) | the Phase 2B-5 constructability reference (`tests/m9_p2b5/install_reference.py`) |
| the five real rooms (66 checks) | a raw-entity reading, independent of the engine |
| D-V26-07 boxes | a raw-line jamb reading |
| the benchmark (16 cases) | hand truth |
| tonight: the held door's width rule | hand truth on 7 synthetic variants; the raw reading on the real door |
| tonight: the curved band | the circular-segment formula; a raw-ezdxf arc census of the reference plan (not the engine) |
| tonight: the B10 wall-mass conservation | outer area − room − door strip |
| tonight: every found defect | its hand truth (`tests/m9_p2b6`) |

**What is NOT independent:** the engine's own conservation checks (same pipeline), and the run audit's records-based
checks (they read the engine's evidence). The audit's drawing checks (A06, A07) read the DXF with ezdxf directly.

## 7. Which reported results cannot be reproduced?

Every reported Phase 2B-5 result was reproduced (`REPOSITORY_BASELINE.md` §2), with one figure corrected: the curved
wall run's share is 0.80 / 0.88 %, not "~0.7 %".

What cannot be reproduced here:

- the 377 private-data tests (their datasets are not in the repository);
- any CAD MCP benchmark (none connected).

## 8. Which tests depend on unavailable private drawings?

- 345 failures + 32 errors in 26 earlier test files depend on git-ignored datasets and workbooks.
- The Stage C real-room scoring is a private script on the private plan, and is not in the repository.
- No repository test of this program needs a private drawing.

## 9. Which defects materially affect BOQ quantities?

| defect | where it shows | quantities affected |
|---|---|---|
| D-P6-01 | held door width | 7 of the 8 failing real checks; threshold, doorway waterproofing, reveal, plaster, tile, skirting, upturn |
| D-P6-07 | basin-only space typed wet | the last failing real check; 9.35 m2 of wet scope on the plan |
| D-P6-02 | exploded single door typed WINDOW | −3.2 % floor on the fixture |
| D-D1 | single-instance layers | doors / windows as passages; a column not deducted (+2.18 %) |
| D-P6-03 | drains typed COLUMN | - |
| D-P6-04 / 08 | columns lost when turned or drawn as four lines | −10.4 % plaster in one villa room at 30° |
| D-D2b | curved wall run | +0.88 % of the plan's wall run |
| D-C2 | leaf-closed thresholds withheld | 5 doorways |
| D-C2b | two doorway waterproofing pieces too large | - |
| D-C3 | doorless cell takes wet scope | - |
| D-C5 | heights | every wall-area line |

## 10. Which defects affect only presentation or attribution?

| kind | defects |
|---|---|
| presentation | D-D2a (polygon, `rect`, `dims` on the chord: no quantity on the real plan; layouts on the chord for arc rooms); D-P6-06 (a zero-length termination line) |
| coverage, flagged rather than silent | D-P6-05 (nested plan: doors held, REVIEW) |
| attribution | D-P6-07 moves the doorway waterproofing piece and the wet scope between rooms and review; D-C3 moves scope, not plan totals |

## How reliable is V2.6?

On the five independently read real rooms it fails 8 of 66 checks, all from two causes (a held door's width, a basin
lobby's type). Both causes are now understood, and an experiment removes both (0 of 66).

On straight-walled synthetic plans with declared roles it is exact. Its weak points sit before measurement, in how
layers are understood:

- single-instance and exploded symbols;
- turned or exploded columns;
- whole plans inside blocks.

These are silent today unless the new run audit is run. There is no accuracy figure: the blind evaluation has not
started.
