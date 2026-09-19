# P7757_WALL_TREATMENT_ESTIMATE_01 — checkpoint

Continuation of the long-horizon orchestration after the owner-input gate.
All client data stays under `data/` (gitignored); this note carries the
method, the code paths and the freeze digests. Benchmark figures live only
in the gitignored reconciliation and owner review package.

## §0 verification from disk

| expected | found |
|---|---|
| git HEAD `bcc2578` | `bcc2578`, tree clean |
| `TRACE_PILOT_REPORT.json` `6b21ce40…` | match |
| `visual_trace.py` `25fc1bce…` | match |
| `P7757_DETERMINISTIC_PATH_FREEZE.json` `4207b1bd…` | match |

No discrepancy between the narrative and the repository.

## Order of events, provable from the freeze files

1. `FREEZE_ESTIMATE.json` — audits, registers, estimate, UI, parameters, code.
2. `A22_STRUCTURAL_COMPARISON.json`, then `FREEZE_A22.json`.
3. Benchmark survey and reconciliation (spreadsheets opened only after the
   A22 freeze; `benchmark_survey.py` verifies every frozen artifact byte for
   byte before opening anything), then `FREEZE_FINAL.json`.

Two code files were edited after `FREEZE_A22`: `engine/cad_curve_register.py`
(float rounding of a radius, for the synthetic test; the P7757 register is
byte-identical) and `research/qs_wall_treatment_01/freeze.py` (the final
stage). The artifact hashes in `FREEZE_A22` were re-verified unchanged
before the benchmark was opened.

## What the phase built

- `engine/material_role_audit.py` — overlap relations, material roles,
  §4 balustrade rule, TRADE_CONTRIBUTION_ID double-count guard.
- `engine/dimension_owner.py` — DIMENSION_OWNER_STATUS from traced
  extension lines, ink check, separate from TEXT_READ_ESTABLISHED.
- `engine/wall_face_set.py`, `engine/wall_treatment_engine.py` —
  WALL_FACE_SET / LINEAR_SURFACE_RUN basis, partial-quantity architecture,
  reveals, profile-eligible edges per category, parapet faces and capping,
  external per floor, control joints never invented.
- `engine/cad_curve_register.py` — exact arcs from the DWG, correspondence
  proposed only.
- `research/qs_wall_treatment_01/` — declarations, owner parameters,
  runners, estimate, QS trace, sensitivity, review UI, source inventory,
  A22, benchmark survey and reconciliation, freeze, owner review package.
- Tests: `tests/test_material_role_audit.py`, `tests/test_dimension_owner.py`,
  `tests/test_wall_treatment_engine.py`, `tests/test_cad_curve_register.py`.
- Invariants §126–§132 in `docs/ENGINEERING_INVARIANTS.md`; section 9 of
  `docs/A21_VISUAL_TRACE_ARCHITECTURE.md`.

## Result on the traced subset (established subtotals, never totals)

| trade | established m² | provisional m² (apart) | coverage |
|---|---|---|---|
| NORMAL_INTERNAL_PLASTER (SALOON) | 22.88 | 2.208 | PARTIAL |
| COLUMN_BONDING_PLUS_PLASTER (SALOON) | 5.76 | 0 | PARTIAL, flagged by A22 T9 |
| ROOF_PARAPET_CAPPING | 0 | 1.42 | PARTIAL |
| all other trades on the four cases | 0 | 0 | PARTIAL (unresolved scope listed) |

COMPLETE_TOTAL_STATUS is NOT_ESTABLISHED everywhere. Sensitivity (scenario
mode): 26.85 / 28.64 / 30.43 m² at 3.00 / 3.20 / 3.40.

## A22 and benchmark, in one line each

A22: 2 structural agreements (return wall 2.00 printed = 2.000 authored;
no enclosure on either path), 1 basis difference (neighbour wall 5.15
printed vs an 8.43 authored face run), 1 geometry difference (the sea-view
chain 90+633+20+90 does not reconcile with the authored extents; the 633
itself matches a line exactly), CAD stronger on the pool curve, visual
stronger on the reception void, one shared-assumption agreement (the owner
height), items T2/T3/T9 for human review.

Benchmark: one contractor statement of executed plaster works (site record,
genuinely independent of the design family) was identified among nine
sealed spreadsheets; verdicts are height, opening-rule, basis, scope and
identity-mapping differences and one human-review item on parapets. No
number was tuned; NOT_COMPARABLE at the total level.

Freeze digests: see `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/FREEZE_FINAL.json`.

## Dual basis (owner decisions of the second checkpoint)

The site record uses a contractor measurement basis; the estimate uses an
engineering basis. Both are now computed on the same frozen faces and kept
apart (`engine/quantity_layers.py`, `engine/contractor_measurement.py`,
`research/qs_wall_treatment_01/dual_basis.py`). On the comparable SALOON
faces the whole difference is the height rule (3.20 owner input vs 3.60 site
record); no opening is deductible on either basis there. Everything beyond
the traced faces is scope, not error.

A raster-to-DWG registration fitted from ten declared pairs (residuals under
6 px, about 19 mm per pixel) resolved A22 items T2, T3 and T9 by the source
hierarchy: the printed 5.15 runs exactly from an authored stub at the open
edge to the sea-view wall line; the 633 is the glazing band exactly; the
printed 90s are pier bodies or an unowned span, not exposed plaster faces.
The 1.80 lm column line is retired and replaced by CAD exposed faces
0.700 + 0.468 lm as a PROVISIONAL line (`CAD_TRACE_LINKS.json`, estimate v2).

Residual owner decisions are three visual cards (`decision_cards/`): the SE
parapet face basis, the element at the SALOON/RECEPTION open edge, and the
benchmark workbook's identity. Freeze: `FREEZE_DUAL.json`.
