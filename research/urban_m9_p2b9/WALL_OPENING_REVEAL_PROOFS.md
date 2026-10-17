# Wall, opening and reveal proofs — worked example 1 (steps A–H)

The fixture is `tests/m9_p2b9/p2b9_fixtures.example1`, the hand truth `p2b9_truth.py` (E1_*, E1F_*, E1_CLIP_*,
E1_UNKNOWN_*), and the tests `test_p2b9_openings.py`.

## A. Situation

- A 4.00 × 3.00 m bedroom: inner faces x 0.20–4.20, y 0.20–3.20; 0.20 m walls.
- Door D1 in the south wall, 1.00 m (jambs x 1.00 / 2.00).
- Window in the north wall, x 1.25–2.75 (1.50 m). Its glazing line is at y 3.30, mid-wall, so the room-side strip is
  0.10 m deep.
- The drawing set also carries:
  - the opening marks D1 / W1;
  - a door and window schedule: D1 1000 × 2200; W1 1500 × 1200, sill 1000;
  - a section SECTION A-A: F.F.L. ±0.00, F.C.L. +3.00, U/S SLAB +3.00 on the GROUND FLOOR band.

## B. Dimensions read

| Dimension | Value | Source |
|---|---|---|
| perimeter | 14.00 m | plan |
| plaster height | 3.00 m | SECTION, U/S SLAB |
| paint height | 3.00 m | SECTION, F.C.L. |
| door | 1.00 × 2.20 | SCHEDULE D1 |
| window | 1.50 × 1.20, sill 1.00, head 2.20 | SCHEDULE W1 |
| reveal depth | 0.10 m | strip 0.15 m² / 1.50 m |

## C. Manual calculation

| Quantity | Formula | Hand |
|---|---|---|
| gross wall face | 14.00 × 3.00 | 42.00 m² |
| door deduction | 1.00 × (min(2.20, 3.00) − 0) | 2.20 m² |
| window deduction | 1.50 × (min(2.20, 3.00) − 1.00) | 1.80 m² |
| **net plaster = net paint** | 42.00 − 2.20 − 1.80 | **38.00 m²** |
| of which above the window | 1.50 × (3.00 − 2.20) | 1.20 m² (inside the 38.00) |
| of which below the sill | 1.50 × 1.00 | 1.50 m² (inside the 38.00) |
| window reveal jambs | 2 × 0.10 × 1.20 | 0.24 m² |
| window head soffit | 0.10 × 1.50 (wall remains above: 0.80 m) | 0.15 m² |
| **window reveal plaster** (its own line, PROVISIONAL) | 0.24 + 0.15 | **0.39 m²** |
| **internal sill surface** (its own geometry; finish by the window detail) | 0.10 × 1.50 | **0.15 m²** |
| **door jambs and head** (its own line, PROVISIONAL) | 2 × 0.20 × 2.20 + 0.20 × 1.00 | **1.08 m²** |
| **skirting** (a sill window is skirted under its sill) | 14.00 − 1.00 | **13.00 m** |

**No double counting.**

- The wall face is measured on the room's boundary run (14.00 m). The jamb and reveal faces lie across the wall
  thickness, outside that run, so they are never inside the 38.00.
- The door jamb line (1.08) and the window reveal line (0.39) cover different openings.
- The strip outside the glazing (0.10 × 1.50 = 0.15 m²) is **external**. It is its own line
  (ARCH.WINDOW_REVEAL "window external strip"), not the room's reveal.

## D. Engine run (ARCH_TAKEOFF_V2.8, no facts file)

| Line | Engine | State |
|---|---|---|
| FIN.PLASTER plaster | 38.00 (gross 42.00; deductions door 2.20 SCHEDULE D1, window 1.80 SCHEDULE W1, sill 1.00) | SOURCE_DERIVED |
| FIN.PAINT paint | 38.00 | SOURCE_DERIVED |
| FIN.PLASTER door jambs and head | 1.08 | PROVISIONAL |
| FIN.PLASTER window reveals | 0.39 | PROVISIONAL |
| ARCH.WINDOW_REVEAL window sill surface | 0.15 | SOURCE_DERIVED |
| ARCH.WINDOW_REVEAL window external strip | 0.15 | SOURCE_DERIVED (external) |
| FIN.SKIRTING | 13.00 | SOURCE_DERIVED |
| ARCH.WINDOW | 1 (width 1.50, height 1.20, sill 1.00, area 1.80, mark W1) | SOURCE_DERIVED |
| door line | height from SCHEDULE (V2.8) | SOURCE_DERIVED |

## E. Intermediates compared

Every intermediate agrees with C, difference 0:

- gross 42.00;
- each deduction, with its own authority string;
- reveal depth 0.10, jambs 0.24, head 0.15.

## F. Differences resolved — what V2.7.1 did

V2.7.1 was run on the same drawing with the S2 synthetic facts (door 2.10, window 1.50; it reads no schedule and no
section). Its plaster is **37.65** = 42.00 − 1.00 × 2.10 − 1.50 × 1.50, for two reasons:

- the window is deducted at its full height inside the band (`WINDOW_POSITION_ASSUMED`), with no sill;
- the door height comes from the facts.

Its window reveal is **BLOCKED_RFI**. `test_v271_deducted_the_window_at_full_height` keeps that as-found record;
V2.7.1 itself is unchanged.

## G. Variants, regression and transformation

| Variant (drawing evidence) | Formula | Hand | Engine | Diff | Test |
|---|---|---|---|---|---|
| floor-to-ceiling glazing W2 1.50 × 3.00, sill 0 | 42.00 − 2.20 − 1.50 × 3.00 | 35.30 | 35.30 | 0 | `test_floor_glazing_is_not_skirted` |
| … its skirting (not skirted at floor glazing) | 14.00 − 1.00 − 1.50 | 11.50 | 11.50 | 0 | same |
| … its reveals (jambs only: head = ceiling, no wall above) | 2 × 0.10 × 3.00 | 0.60 | 0.60 | 0 | `test_floor_glazing_reveals_and_floor_strip` |
| … the strip to the glazing is **floor**, not sill | 0.10 × 1.50 | 0.15 | 0.15 (FIN.FLOOR.PORCELAIN, PROVISIONAL) | 0 | same |
| head 2.90 above F.C.L. +2.80, under U/S SLAB +3.00 | plaster 42.00 − 2.20 − 1.50 × 1.90; paint 39.20 − 2.20 − 1.50 × 1.80 | 36.95 / 34.30 | 36.95 / 34.30 | 0 | `test_a_window_is_deducted_inside_each_band_only` |
| … its reveals | 2 × 0.10 × 1.90 + 0.10 × 1.50 | 0.53 | 0.53 | 0 | same |
| no schedule: the sill is unknown | certain skirting 14.00 − 1.00 − 1.50, range + [0, 1.50] | 11.50 + [0, 1.50] | 11.50 + [0, 1.50] | 0 | `test_an_unknown_sill_makes_skirting_a_range` |
| … the wall face | between full-height and no deduction | [35.30, 39.80] | [35.30, 39.80] | 0 | same |
| … the window | width released, **area held** | 1 / held | 1 / held | — | `test_a_window_without_a_height_holds_its_area` |
| the mark's schedule row has another width (1.20 ≠ 1.50) | neither its height nor its sill is the window's | held | held (SCHEDULE_WIDTH_DIFFERS) | — | same |

- **Invariance:** translate, mirror, metres, reorder and plan rotation all give identical quantities (10 tests).
- **V1 to V2.7.1:** byte-identical (`REGRESSION_AND_FROZEN_EVIDENCE.md`).

## H. The whole villa

- **Reference plan.** There is no schedule, no binding section and no marks. Every window keeps its area held
  (26 windows: sill not established), so V2.8 changes no plaster, paint or skirting quantity there:
  - the 23 windows on room boundaries were already in the F-17 range;
  - this is checked edge by edge, so none is moved twice.
- **Synthetic villa** (two layouts, with and without facts). V2.8 moves the unknown-sill window thresholds out of the
  certain skirting into a range:
  - with facts: −8.70 m released, +8.70 m range;
  - without facts: −6.00 m and +6.00 m;
  - all 7 rooms per layout are independently **VERIFIED** (`INDEPENDENT_VERIFICATION_RESULTS.md`).

### The double count found and fixed during this phase

The first V2.8 draft subtracted every window's threshold from the certain skirting. On the reference plan those edges
were already outside the certain skirting, in the F-17 range (mixed role sets), so the draft:

- removed 30.75 m that had never been counted;
- added the same 30.75 m to the range a second time.

The adjustment now works edge by edge against the F-17 reading (`arch_v28.skirting_adjustment`, using
`release_safety.boundary_detail` threshold sets). On the reference plan the change is 0.
