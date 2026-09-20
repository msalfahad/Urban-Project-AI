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

## Owner-verified plan layer (third checkpoint)

The owner's manual plan check (515 endpoints; 90 + 633 + 90 with the 20 as
thickness; both 90s legitimate; 40 + 452 + 45 next; 150 − 20 − 20 = 110 for
one opening) is recorded in `owner_plan_verification.py` as its own
evidence layer. Every segment is corroborated by authored DWG lines
(`OWNER_EVIDENCE_RECONCILIATION.json`): the upper 90 runs from the glazing
end to a door-layer line 0.232 past the return wall, so the earlier "matches
no authored span" is withdrawn. The CAD pier runs 0.700 / 0.468 are kept but
split by plaster-face ownership into column bonding 0.20 / 0.30 (S-COL.BON
hatch extents inside the room) and block 0.50 / 0.168, all PROVISIONAL.
Estimate v3 carries that split; v1 and v2 stay frozen. The SALOON card
`decision_cards/S1_SALOON_DIMENSIONS.png` shows setting-out spans in blue,
plaster faces in green and the thickness annotation. Freeze:
`FREEZE_OWNER_EVIDENCE.json`.

## SE elevation owner source check (fourth checkpoint)

The owner's second manual check ("155 exists; 50 is the top link of
100 + 870 + 420 + 50; I see no 130 and no 104") was answered on the native
scans of the original pages (SE elevation p4, B-B p9, A-A p8; embedded
image hashes equal the frozen source hashes). Every audited dimension is
recorded with sheet, page, hashes, text box, dimension line, tick endpoints,
what each end terminates on, the physical owner candidate and a
termination-based owner status (`SE_ELEVATION_SOURCE_AUDIT.json`,
`decision_cards/se_native/`). Findings: 104 is printed inside the lattice
zone and is a balustrade assembly height, not a misread of 139; 139 is
independent; 130 exists only on B-B and belongs to the NW roof edge; 97
sits on the arched feature left of the tower; 155 is tower top to dome
apex; the SE 50 is a chain link whose lower tick is a dashed datum, while
the tower parapet's 0.50 face is established on A-A. No text correction was
needed. The earlier D1 figures (1.22 / 1.42 over 7.10 m) are withdrawn
because a face height was applied over the lattice portion; the residual is
the floor/parapet split on the solid portion (Option A 1.40 at the +9.70
datum, recommended; Option B 1.22 at the drawn base line), 0.18 m² per
metre run, and no established m² changes because the solid portion has no
length. D2 is resolved provisionally from E1.4 and the DWG (edge level
line, no plasterable face). D3 stays with the owner. Estimate v3 is
unchanged. Cards: `decision_cards/D1_SE_PARAPET_SOURCE_CARD.png`; review
`OWNER_REVIEW_V4.md`; freeze `FREEZE_SE_AUDIT.json`.

## Parapet assembly and four-layer measurement (fifth checkpoint)

The SE roof edge was found in the DWG roof-plan copy (outer face 7.50 m,
roof-side floor line 7.10 m equal to the printed 129 + 2×R221 + 139 chain, a
250 mm line 3.767 m from the SW corner that is the frozen raster's UNK-01,
corner arc r = 0.231) and split into a solid NE portion (3.683 / 3.483 m)
and a kerb-and-lattice SW portion, PROPOSED_CORRESPONDENCE. The structural
set ST7757.pdf (an exact 1:100 vector plot) registers to the DWG by
translation with 30 of 30 columns under 55 mm; it gives the SE edge 7.497 m,
the +13.90 slab exterior ring 29.794 m and an RC edge beam 45×75 with a
20×20 upstand, and it defers the parapet above to the architectural detail.
D2 is answered in three statements: the 30×60 column exists on LOOP-059,
it is exposed (free-standing, beams not walls) and it does not own the
SALOON clear face; the 1.3 m dashed line is the overhead beam. The
assembly register (`PARAPET_ASSEMBLY_REGISTER.json`, 16 components), the
face register (17 faces, face-specific heights), the measurement regions
(virtual closures with zero material and no geometry authority), the
opening register, the plaster trace v4 (states per line, totals per unit),
A22 v4, the owner decision queue (six non-blocking items), the supersession
ledger (seven entries, all earlier freezes unchanged), the source coverage,
the leakage guard (clean) and three visual QA overlays on the original pages
are frozen in `FREEZE_ASSEMBLY.json`. Estimate v3 stays frozen; v4 adds the
roof-edge faces and the D2 column as PROVISIONAL lines.

## Second technical pass (sixth checkpoint, PA02)

D1 was rebuilt as a level-identity model: +9.70 is the structural slab and
parapet base (sections hatch the masonry from the slab top; the structural
roof sheet prints +9.70 on the slab), +9.88 is a level line drawn 0.16–0.18
above the slab on two different edges (the SE raster and the DWG's NW
elevation) with no build-up drawn anywhere; its identity stays
NOT_ESTABLISHED after source exhaustion, both bases are carried (1.22 / 1.40
on the SE solid portion, 0.63 m² apart) and the owner is asked for the roof
build-up, not for a choice. The DWG elevation blob was corrected from "SE,
mirrored" to the NORTH WEST elevation (its printed 155 / 269 / 305 / 230
match page 6). The column girth was rebuilt face by face (LOOP-059: four
exposed faces, 1.80 lm). The FF void over the reception is a stair well
bounded by railings and the curved stair, so no double-height wall exists;
the block stair well (printed 2.50 × 6.45) is measured as per-storey faces
(93.1 / 75.2 / 75.2 m² gross, PROVISIONAL, interruptions listed, underside
not established). The NE parapet was corrected to a 1.40 face plus a 0.20
band (A-A hatch 1.62; NE elevation top +11.27), the NW sea-view element is a
lattice balustrade on a low kerb (page 6), the SW parapet height comes from
the SE elevation's end-on view (~1.35 above the base line, PROPOSED), the
annex and tower edges are registered. SE façade openings were read on the
native page with the printed dimensions (arches as rectangle + semicircle);
the net faces are GEOMETRIC_REFERENCE_ONLY because the external finish
system is unknown (one element, the entrance arch, is confirmed cladding).
Wet rooms carry E1.4 chain lengths (59.2 lm GF, PROVISIONAL) with areas
NOT_ESTABLISHED; the project opening register holds 35 openings; profile
steel, floor-by-floor output and a coverage matrix are produced. The owner
queue was rebuilt to five items, none blocking. Freeze:
`FREEZE_PA02.json`.
