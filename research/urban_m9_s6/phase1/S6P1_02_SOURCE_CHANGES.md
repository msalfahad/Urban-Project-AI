# S6 Phase 1: source changes

All the new behaviour sits behind `--method ARCH_TAKEOFF_V2` (or `--strict-admission` on V1).

Shared helpers gain keyword parameters. The defaults are today's literals, so `ARCH_TAKEOFF_V1` and route G run the same code paths as before. This is proven by hashes and by tests:
- the synthetic villa: 15 output files, byte-identical;
- the reference plan: 16 output files, byte-identical;
- `tests/m9_s6/test_s6_frozen.py`: a V1 quantity snapshot taken from HEAD `6b7a2e4`.

## Files not changed on purpose

These files sit inside other milestones' frozen code digests:

| File | Frozen by | What S6 does instead |
|---|---|---|
| `engine/source/opening_census.py` | the S8.6 lintel freeze `CODE` digest (its build script; `tests/lintels_s8_6` rebuilds it byte for byte) | `engine/source/opening_gaps.py` (new). At `merge_tol == 1.0` it calls the frozen `band_gaps`; any other value runs the same procedure, built from opening_census's own helpers |
| `tools/urban_intake.py` | the M7 and M8 engine freezes (`00_ENGINE_FREEZE.json`, `files_sha256`) | `tools/arch_discovery.k2_census(doc)` runs the K2 kernel again on the admission's own document |
| `tools/urban_boq_m2.py`, `tools/urban_project_run.py` | the S1 frozen-route test | the structural-defaults warning lives in `urban_boq_m9` |

The first full-suite attempt edited `opening_census.py` and `urban_intake.py`. It showed that the S8.6 double-build rewrote the frozen README stamp, and that the M7/M8 freeze tests would fail.

Both edits were reverted. The rewritten research files were restored with `git checkout`, and nothing from that run is committed.

## Changed modules (V1-neutral by construction)

| File | Change | V1 default |
|---|---|---|
| `engine/source/arch_plan.py` | Adds `TOL_POLICIES` and `unit_tol(unit_m, tol)` (LEGACY 1.0 drawing unit, or UNIT_RELATIVE 1 mm in the unit; equal at mm). `_small_rects(..., tol)`. `layer_roles(..., tol)`, which calls `opening_gaps.band_gaps(merge_tol=...)`. `plan_regions(..., split, frames_from_lines_fallback)`: EMPTY_BANDS is a recursive XY-cut along empty bands at least 0.5 m wide, and never through drawn geometry. Also `xy_cut`, `frame_segments`, `cut_crossings` | `tol="LEGACY"`, `split="TITLE_MIDPOINTS"`, no fallback |
| `engine/source/arch_rooms.py` | `_columns(..., tol)` and `spaces(..., tol)` pass the policy through | `"LEGACY"` |
| `engine/source/lintel_measure.py` | `openings(..., tol)` derives `merge_tol` and calls `opening_gaps.band_gaps` | `"LEGACY"`, so the frozen `band_gaps` runs |
| `engine/source/boq_line.py` | Two item codes, `ARCH.THRESHOLD` and `ARCH.WINDOW_REVEAL` (bilingual) | unused by V1 |
| `tools/dwg_adapter.py` | `convert(..., strict)` names the output `<stem>.<sha12>.dxf` and removes a stale target before converting. An unreadable result is `CONVERTED_FILE_UNREADABLE`; an empty model space is `EMPTY_CONVERSION`; both are BLOCKED. `loss_report` adds the model-space entity types | `strict=False`: M9 S3 naming and behaviour |
| `tools/urban_boq_m9.py` | `ARCH_TAKEOFF_V2`, `--strict-admission`, and the reviewer inputs `--units`, `--region`, `--accept-missing-xref`. Admission, entity checks, completeness gate, exit 2 / 3 and `_supersede`. The `--structural` warning, plus `STRUCTURAL_CONVENTIONS_REQUIRED` for V2 | V1 without `--strict-admission` never calls any S6 code (tested with the admission patched to raise) |

## New modules

| File | What |
|---|---|
| `engine/source/discovery.py` (stdlib) | The `URBAN_DRAWING_DISCOVERY_V1` report has stages 0–10 and levels FATAL / BLOCKED_ITEM / REVIEW_REQUIRED / WARNING.<br>Stage rules: inventory, units, regions and the V1 legacy-tolerance check.<br>Gate: FATAL anywhere, or a BLOCKED_ITEM in stages 0–5, stops the run with exit 2. A later BLOCKED_ITEM blocks only the items it names |
| `engine/source/arch_completeness.py` (stdlib) | Strip register, with each doorway face reviewed individually.<br>Strip lines: one BLOCKED_RFI line per opening.<br>Surface RFIs for the stair hall, the band above partial wet tile, and the exterior scope.<br>The three-view coverage gate.<br>Column evidence (fills against measured columns, per room), unread fills, and door blocks scaled non-uniformly |
| `engine/source/opening_gaps.py` (stdlib) | `band_gaps` with a merge tolerance. The frozen function is used at 1.0 |
| `tools/arch_discovery.py` | Source census: layouts, XREFs, MINSERT cells, nesting depth, hidden layers, kinds.<br>`k2_census`, `shapes` (every fill in WCS at every depth, MINSERT cells expanded, layer-0 inheritance), `admit_intake`, `admit_regions`, `override_regions` |

## What V2 does, in run order

1. **Pre-admission (stage 0).**
   - `--structural` needs `--conventions` (FATAL).
   - The plan and the structural drawing must not be the same file (FATAL); the same name with different content is a WARNING.
   - A DWG goes through strict conversion. A failed or empty conversion is FATAL `DWG_CONVERSION_BLOCKED`.
2. **Intake.**
   - Stage 1, inventory: an empty model space is FATAL. A missing XREF is BLOCKED_ITEM unless accepted. Hidden-layer content and paper-space content are REVIEW. MINSERTs, nested hatches and kinds not measured are WARNINGs. A top-level entity without a K2 disposition is FATAL.
   - Stage 4, units: undeclared is BLOCKED_ITEM, with the inferred unit in the evidence. Contradicted is BLOCKED_ITEM. A reviewer's `--units` is REVIEW.
3. **Regions (stages 2 and 5).**
   - EMPTY_BANDS split, falling back to frames drawn as lines.
   - Paper-space sheets, titles outside frames, no title and no region are FATAL.
   - A cut through geometry is BLOCKED_ITEM.
   - A reviewer's `--region` is REVIEW.
4. **Measurement.**
   - V1's own measurement, with UNIT_RELATIVE tolerances.
   - The sheet frame's own sides are dropped from the region.
5. **After measurement.**
   - Strips, surface RFIs and coverage.
   - Stage 6 entity checks: COLUMN_EVIDENCE_NOT_MEASURED, FILLS_NOT_READ_IN_PLAN and DOOR_SYMBOLS_DISTORTED, as REVIEW findings plus per-room unresolved records.
   - Stage 7 vertical model, stage 9 finish zones, stage 10 readiness.
6. **Publication.**
   - Coverage not PASS → exit 3. Nothing is published; `diagnostics/` keeps the computed lines and the coverage.
   - Otherwise V1's files are published, plus `DRAWING_DISCOVERY.json` and `FINISH_COVERAGE.json`.

## Tried and not adopted

**A relative 1e-9 slack on the lower length thresholds of the band path** (S6P1-NEW-05). The thresholds were:
- the 100 mm minimum face piece;
- the 300 mm minimum overlap;
- the 0.4 / 0.5 m minimum gaps;
- the column side range.

The slack made the reference plan in metres equal to millimetres. But it changed the millimetre result of the reference plan itself (two more openings on one floor), which breaks "mm unchanged".

It was reverted, and `test_a_drafted_100_mm_face_piece_survives_in_a_metre_drawing` (strict xfail) records the finding for Phase 2.
