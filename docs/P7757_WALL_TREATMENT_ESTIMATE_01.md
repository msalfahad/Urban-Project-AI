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

## Source review and correction layer (seventh checkpoint, PA03)

The owner's source review reopened four PA02 statements before any
dependent quantity was used. The FF "void" was reconciled without
arithmetic: the printed 587 × 400 are authored DWG dimension entities and
name the VOID_STAIR_ZONE (5.87 to the outer railing line; 4.00 from the
opening's north line to the NE wall face, which includes the 1.15 m
straight-flight strip), while PA02's 5.82 × 2.75 is the SLAB_OPENING
marked by the architectural X and, independently, by the structural p4
"Open To Below" X. Both objects are preserved (width:
SAME_OBJECT_DIFFERENT_FACE_BASIS; depth: IDENTITY_MAPPING_DIFFERENCE).
The statement "there is a void, therefore no double-height wall" was
withdrawn (L-10 reopened): the four opening edges were modelled from the
solid / dashed layers of both plan copies — north and east edges open with
FF railings, the west edge open at GF under an FF wall, the NE edge a GF
opening to the garden strip under an FF wall for 3.82 m and the same
200 wall on both floors for 2.05 m with the straight flight against it
(candidate double-height face RVF-S-B). No section cuts the opening (A-A
has it behind the viewer, B-B looks away), so
DOUBLE_HEIGHT_WALL_STATUS = NOT_FULLY_ESTABLISHED and every face stays
NOT_ESTABLISHED. The D2 column's exposure was rebuilt face by face with
the walls that end on it (CAD-822/823 on the west face, CAD-783 on the
east): internal plasterable girth 0.75 lm (0.85 on the structural depth),
external face 0.60 separate, exposed height NOT_ESTABLISHED, the 5.76 m²
superseded and 0.75 × 3.20 = 2.40 labelled OWNER_PARAMETRIC. The block
stair's 10 cm element stays UNRESOLVED with the full-height wall roles
excluded provisionally by A-A (the far flight is visible); the per-storey
stair subtotals were demoted to GEOMETRIC_REFERENCE_ONLY and the twelve
faces carry exposure / openings / landing / occlusion fields. The NE
elevation exists (page 7): the queue wording was withdrawn and the item
rewritten with SOLID_FACE_TOP (PROVISIONAL), BAND_EXISTS
(NOT_ESTABLISHED: page 7 draws one top line), BAND_HEIGHT (DERIVED 0.20)
and BAND_TRADE_ROLE (UNKNOWN) as separate fields. The SE opening
dimensions were re-read on native crops with witness terminations
(W1–W4 and the 2.15 × 1.90 window PRINTED_OWNED; two small 8 / 5 figures
at the W2 sill UNRESOLVED). A QA render validity register classifies every
overlay and source crop; three NE top crops are NOT_INFORMATIVE for a
band. Registers: VOID_GEOMETRY_RECONCILIATION,
RECEPTION_VERTICAL_FACE_REGISTER, STAIR_COMPONENT_REGISTER_V2,
COLUMN_VERTICAL_EXPOSURE_REGISTER, NE_ELEVATION_FINISH_ELIGIBILITY_REGISTER,
SE_OPENING_DIMENSION_OWNERSHIP_AUDIT, PA02_SOURCE_REVIEW_SUPERSESSION_LEDGER,
QA_RENDER_VALIDITY_REGISTER, PA03_DEPENDENT_QUANTITIES, A22 v6, queue v3
(six items, none blocking; a new RECEPTION-SECTION-SOURCE information
item), ledger L-15..L-22. Freeze: `FREEZE_PA03.json`.

## Multi-domain expansion batch (eighth checkpoint, PA04)

PA04 ran seven workstreams as a batch with three cold-challenge readers
and deterministic reconciliation. Plan regions were flood-filled from the
DWG wall and door layers (`engine/plan_regions.py`) on all three copies:
the first floor gives 21 regions with host-wall, door-line and open-edge
lengths per face (areas withheld: the FF height is NOT_ESTABLISHED); one
region merges the corridor, living area and two bedrooms because the DWG
closes no door there. Wet rooms carry host-wall lengths only (no tile
height invented). The NW elevation's authored DWG dimensions and jamb
lines fixed the three arched windows (155.2 × 216.1 + semicircle r 0.776)
and the tower arch (269.1 × 216.1 + segment rise 83.9); the cold challenge
showed pages 6 and 7 are section-elevations with the ground storey cut,
so one "door" was withdrawn and GF façade openings stay NOT_ESTABLISHED.
Roof edges were completed with the full field set (annex run 30.8 m from
the annex-roof region, heights missing); stair geometry v3 counts 26
treads on the main stair and gives slope-factor soffits; the beam
schedules (read visually, no text layer) put CB7 20 × 75 over the D2
column (exposed height 3.75, area 2.81 m², PROVISIONAL) and CB6 20 × 75 on
the opening's north edge. The reception challenger agreed with PA03 on
every plan edge and confirmed that no section cuts the opening. Openings
v2 unifies 71 records (actual overrides default), profiles v2, treatment
sequences v2, a scoped height table, ceiling and floor region registers,
A22 v7 (AGREE_ON_NUMBER_ONLY on the stair-well perimeter), coverage by
state, queue v4 (seven items, one new: FF-HEIGHT-RULE), metrics,
recommendations, parallelism classes and Project-3 entry criteria. Freeze:
`FREEZE_PA04.json`.

The architecture review (`pa04/ARCHITECTURE_REVIEW_PA04.json` / `.md`, one
read-only reviewer agent run after the freeze) is stored beside the frozen
artifacts and deliberately kept out of the freeze list: it edits no
production data and is advice, not measurement.


## Production ingestion and stable geometry architecture (ninth checkpoint, PA05)

PA05 built the generic ingestion package `engine/ingest/` (ids, status,
units, rules, owner inputs, curves, sheet roles, source inventory, views,
dimensions, faces, opening sites, spaces, measurement regions, a nine-stage
harness and twelve executable gates) and ran P7757 through it as input
data only (`research/qs_wall_treatment_01/pa05/config_p7757.py`). The
supervised run finds eight model-space views, recovers the plan-copy
offsets from endpoint voting, owns 377 of 389 authored dimensions on both
ends (the void's 587 / 400 among them), yields 2,714 horizontal, 2,622
vertical, 7,366 angled and 120 arc faces by developed length, 578 opening
sites of which 173 are UNRESOLVED (a site, never a merge), 71 physical
spaces with anchors and bounding entities, 59 semantic anchors, and 284
trade measurement regions whose closures are hash-reversible. The
migration adapter classifies 213 frozen items (60 without loss, 107 with
information loss, 29 not migratable, 17 historical only) and edits nothing.
The PA05 success gate A–K passed, so P7757_BLIND_REBUILD_01 ran in a fresh
directory under an audit hook that logged every file open (three source
files, no violation); its frozen outputs agree with the supervised run on
curve radii, dimension ownership, plan-copy offsets and region
reversibility, and differ where the blind run lacks the sheet reads and
layer overrides that the supervised configuration carries. All twelve
Project-3 gates pass. Freeze: `FREEZE_PA05.json`. The second architecture
review (`pa05/ARCHITECTURE_REVIEW_PA05.json` / `.md`) is stored beside the
artifacts and kept out of the freeze, as in PA04.

## Production bridge (tenth checkpoint, PA06)

PA06 built the generic bridge from source files to the deterministic quantity engines: a source-unit
resolver, a primitive role classifier, block / hatch / structural object roles, a wall-material continuity
site model with fixtures A-J, cells and physical regions, vector wall length per space, a storey / copy
family register, hybrid sheet roles, a bilingual semantic ontology, one canonical state lattice with
boundary adapters (lm is a presentation alias of m), and the quantity bridge to
`qs_measurement_region` / `plaster_trade_engine`. P7757 ran as regression data through
`research/qs_wall_treatment_01/pa06/run.py` with freeze barriers after geometry and topology:
9369 primitives, 1991 material entities,
3522 hatch strokes rejected, 25 topology cells in
23 physical regions, 2535.21 m of
vector material wall (a structure metric, not a quantity), 16 functional zones,
453 measurement closures, quantity-input lines by state
{"NOT_ESTABLISHED": 36, "PROVISIONAL": 50}. The blind rebuild v2 (P7757_BLIND_REBUILD_02, sources only,
audit hook, tolerances declared before the run) passed all thirteen criteria. The cold architecture review
and PROJECT_3_ENTRY_GATE_V2 are recorded beside the artifacts; the gate is not READY while the review names
a failure able to produce a silently wrong quantity. Freeze: `FREEZE_PA06.json`.

After the first PA06 freeze an apparatus defect was found: closed plot cells between the site boundary and
the building carried PROVISIONAL floor and ceiling area lines (a plot area presented as a floor). The fix is
generic (SPACE_CLASS = EXTERIOR_SITE from site labels inside the cell, plot-boundary edges or the view edge;
such cells get NOT_APPLICABLE lines and are excluded from interior wall totals). The corrected run was
written to `pa06r1/` with its own blind rebuild (P7757_BLIND_REBUILD_PA06R1) and frozen as
`FREEZE_PA06R1.json`; `FREEZE_PA06.json` and `pa06/` are kept unchanged as history and the supersession is
recorded in the PA06 ledger.

## Geometry and topology safety (eleventh checkpoint, PA07)

PA07 closed the five PA06 blockers that could produce a plausible quantity from the wrong physical geometry.
Material is now a band of paired faces with evidence (`engine/ingest/material_bands.py`, §169), a band is a
one-dimensional host cut into MATERIAL / OPENING / JUNCTION / UNRESOLVED intervals with zero-material chords
sealing every interval end (`band_topology.py`, §170), spaces are the connected components of the whole free mask
with no seed grid (`planar_faces.py`, §171), column facts are kept separate (`junctions.py`, §172), per-entity
linetype, visibility and lineweight are resolved through the layer and block tables (`engine/cad_adapter.py`),
and the bridge runs only behind nine named gates (`pipeline7.py`, §173). 51 new adversarial tests
(`tests/test_pa07_*.py`) cover the fifteen band cases, the nine curved fixtures and the space fixtures.

P7757 ran as regression data through `research/qs_wall_treatment_01/pa07/run.py`: 9369 raw
primitives, 2031 band candidates of which 443 accepted, 1299 rejected and 289 unresolved
(each with its reason), sites {'UNRESOLVED': 42, 'CAD_JUNCTION': 23, 'PROBABLE_DOOR_OPENING': 1, 'MATERIAL_CONTINUITY': 1, 'CONFIRMED_DOOR_OPENING': 8, 'CONFIRMED_WINDOW_OPENING': 2}, planar faces {'EXTERIOR_CONNECTED': 7, 'MATERIAL_INTERIOR': 591, 'SLIVER': 124, 'ELIGIBLE': 12},
3 interior spaces on plan views, 3.005 m of
material boundary on them (structure only), bridge-allowed lines 0. The PA06R2
figure of 1282.684 m of interior vector wall was not preserved and could
not be: most P7757 walls carry a third parallel line and no hatch or end returns, so the band engine leaves them
UNRESOLVED and the rooms beside them leak to the exterior face. That is the FAIL VISIBLY outcome the phase was built
for; the owner queue asks which line is the wall face. No independent second villa exists in the repository or the
uploads, so the validation protocol is frozen unexecuted (`SECOND_REGRESSION_SOURCE_REQUIRED.json`, §174) and
PROJECT_3_ENTRY_GATE_V3 is NOT_READY. Freeze: `FREEZE_PA07.json`; the cold review and its POST_REVIEW variants sit
beside the frozen artifacts.

After the PA07 freeze a cold review (separate context, FM-P6 list withheld until its second round) found 18 failure
modes, six of them CRITICAL and silent: a wardrobe or counter outline joined at its ends became a wall, any bare
rectangle up to 600 mm became a column, unresolved walls were invisible to the topology so rooms merged across them,
one perpendicular stub counted as material fill, aligned partitions across a corridor promoted to an open passage,
and far-side T-junctions chorded both faces so the bridge had never formed a region on real geometry. The review's
classification of the PA06 modes against PA07: FIXED 4, PARTIALLY_FIXED 10, UNCHANGED 1, WORSENED 1 (FM-P6-16,
the attribution sampling). PA07R1 applied the cheap guards (`pa07r1/PA07R1_GUARDS.json`, seven new tests in
`tests/test_pa07r1_guards.py` including an end-to-end pipeline7 run that forms a closed, reversible region on a
synthetic villa and blocks the same villa with an unresolved doorway) and re-ran P7757 as `pa07r1/`: 367
accepted bands, 42 interior spaces on plan views of which 1 established and
41 BOUNDARY_PROVISIONAL (the unresolved walls now split the leaked regions instead of
merging them), bridge-allowed lines 0. PA07 and its freeze are kept unchanged as history; the
revision is frozen as `FREEZE_PA07R1.json`. No fresh cold review of PA07R1 was performed, so gate v3 condition 13
stays failed. The answer to an unseen-villa draft BOQ remains NO.

### PA07R1 cold review, PA07R2 guards and the PA08 harness (eleventh checkpoint, continued)

A fresh cold review of PA07R1 in a new context (given only the generic ingestion code, the PA07R1 code, tests, freeze
manifest, metrics and quantity-safety register; no FM-P6 list, no earlier review, no P7757 quantities) found 18
failure modes: CRITICAL_SILENT 3 (bulged-polyline arcs decoded with the wrong centre so curved walls vanished and
rooms merged; furniture / ceiling copies of a plan each measured once; an enlarged 2x detail passing all gates),
HIGH_SILENT 8, LOUD 3, QUALITY 4; verdict IS_PA07R1_SAFELY_CONSERVATIVE = NO ("conservative by yield, not by
construction"). The fifteen-question post-review gate, executed as synthetic counterexamples
(`pa07/post_review_gate.py`), failed PA07R1 on five questions (stair fixture error, single-face gap leaving one side
ESTABLISHED, a walled GARDEN classed INTERIOR, a continuous-line beam splitting a room, and a wall nib beside a door
jamb becoming a column whose face was counted twice and then crashing the bridge). PA07R2 applied sixteen guards and
corrections (`pa07r2/PA07R2_GUARDS.json`, `tests/test_pa07r2_guards.py`, §175–§177): the review's findings stand
FIXED 3, GUARDED 8, PARTIALLY_GUARDED 1, RECORDED for PA09 5, no change 1, OPEN 0; the gate passes 15 of 15 under
PA07R2. P7757 rerun as `pa07r2/` (regression only, delta in `PA07R2_P7757_DELTA.json`): accepted bands 367 -> 174
(308 short transverse pairs and 59 thin bands now UNRESOLVED, 14 wall nibs, 7 column candidates), confirmed doors
6 -> 12, spaces 45 (2 established), bridge-allowed 0, a new SCALE_STATUS gate blocking 68 lines on views whose wall
thickness medians differ from the source. The PA08 blind-validation harness (`pa08/`, §178) is prepared and dry-run
on a synthetic villa (every step executes, the deliberate leak is caught, SILENT_WRONG_QUANTITY_COUNT 0) but not
executed: no independent villa exists; `SECOND_REGRESSION_SOURCE_REQUIRED.json` stays active and gate v4 is
NOT_READY. The answer to an unseen-villa draft BOQ remains NO.

### PA08_QORTUBA_BLIND_01 (first independent blind run)

An independent second-floor apartment plan (QORTUBA: DWG R2013 in centimetres, decoded with LibreDWG 0.13.3, plus its
plotted A3 PDF) was accepted (`pa08_qortuba/PA08_SOURCE_ACCEPTANCE.json`) and run through the frozen PA07R2 engine
AS-IS in the audited subprocess (no violation; engine code hashes identical to FREEZE_PA07R2). Result: units cm
SOURCE_ESTABLISHED; 101 authored dimensions read, 85 agreeing with geometry and 16 rotated dimensions mis-measured by
the adapter (recorded as blind defect QBD-04, HUMAN_REVIEW, no quantity consumes them); 20 room labels, of which the
10 Arabic ones are keyboard-mapped Latin glyphs the engine cannot read (decoded deterministically in the research layer
as AI_INTERPRETED); 24 accepted wall bands (97 m), 131 unresolved; 1 door and 1 provisional window of 8 door blocks and
7 window groups; 12 provisional cells with seven rooms' labels merged into one; bridge-allowed 0. Every vertical
quantity is NOT_ESTABLISHED (no Qortuba height exists; P7757 heights not reused). Ten blind defects recorded, none
critical, nothing patched. Frozen as `FREEZE_PA08_QORTUBA_BLIND_01.json`; preliminary verdict
NOT_READY_FOR_EXTERNAL_COMPARISON (topology not sufficiently represented). The owner's withheld comparison data was
not requested or used.

**PA08-QORTUBA-R1 (post-blind generic partition recovery).** The blind
freeze stood; the failure it recorded was diagnosed before any geometry
changed. `QORTUBA_PARTITION_FAILURE_REGISTER.json` names nine boundaries
of the merged cell with their entities, layers, block relations, face
pairs, authored thickness dimensions and door intersections, and assigns
each to one of eight generic failure classes; a raster ablation proves
which boundaries are causal. Six generic rules answer them: the angle wrap
repair (§179), end-gap intervals with junction, along-wall and shared-gap
refinements (§181), end caps on unresolved strips so a strip is never a
corridor, closed-outline separators for unpaired material loops, revival
of demotions whose host never survived (§180), and a thickness-supported
band rule that promotes a thin pair only with an authored dimension **and**
a junction to established structure. Qortuba's seven labelled rooms now
occupy seven separate cells. Fifty-three spaces, eleven labelled; fifty-two
internal floor regions, three `SOURCE_ESTABLISHED` (14.07 m²), the rest
provisional; wall length, skirting path and profile path are three separate
items with no contractor deduction; block, plaster and paint carry lengths
only, every area `NOT_ESTABLISHED` for want of a height. An independent
reader of the original sheet agreed with fourteen of fifteen comparable
adjacencies. The P7757 regression is a yield loss in the safe direction:
accepted wall length 384 → 502 m and established spaces 2 → 5, against
confirmed doors 12 → 11 with twenty door-class sites where there were
twelve. Frozen as `FREEZE_PA08_QORTUBA_R1`; the owner's withheld flooring,
skirting and profile quantities were not requested, opened or inferred.

**PA08-QORTUBA-R2 (artifact cells against real floor space).** R1's
partition recovery left fifty-three cells, thirty-four under a square
metre. R2 changes no engine rule; it adds a measurement-layer classifier
that names, for every cell, which physical element's interior it is
(§183). Of the fifty-three: nine are free space, one the roof, one the
sheet's own site region, fourteen stair components, eight the interiors of
wall strips, frames, columns or joinery, four drafting slivers, and sixteen
remain `HUMAN_REVIEW`. Forty-four cells leave floor scope, among them a
0.417 m² stair pocket R1 had released as established floor area. Room
relations are now read through the doorway cell (§184), which resolved the
one outstanding semantic disagreement: the bath-to-dress boundary is a
**door**, on leaf, frame and jamb-return evidence in the DWG, not the
reader's say-so. Boundary certainty separates an opening's line position
from its type (§185). Nine floor-finish regions result, one
`SOURCE_ESTABLISHED` at 5.10 m² and seven provisional at 116.53 m²; the
blockers are genuine unresolved perimeter, from 1.2 per cent of the
boundary in one bathroom to 57.6 per cent in the dress room. Skirting and
profile stay separate trade lines. Ceilings are derived case by case from
the cleaned region. Block, plaster and paint carry lengths only. Frozen as
`FREEZE_PA08_QORTUBA_R2`; `READY_FOR_WITHHELD_FLOORING_COMPARISON: NO`, and
the withheld quantities were not requested, opened or inferred.

**PA08-QORTUBA-R3 (floor-finish measurement regions).** R2 held the
physical wall model conservative and let that decide the floor, which is an
architectural error: where a floor finish stops is a question about lines,
not about material roles. R3 separates the two. The discriminator is
thickness evidence (§186). A paired band's drawn face means something with
a thickness stands there, so the floor stops, whatever the band's material
role turns out to be; an unpaired single line has no thickness evidence and
cannot fix where a floor stops, so the region is assembled across it and
every crossing is recorded, reversibly. Doors and open edges are closed by
measurement closures that carry no material, no wall, no geometry authority
(§187). All nine regions come out `SOURCE_ESTABLISHED`: dry 116.138 m²
across six rooms, wet 17.863 m² across three bathrooms, kept separate. The
dress room, which R2 could not measure at all, is 11.985 m². No physical
wall verdict moved: twenty provisional, one established, three not
established, exactly as R2 left them, and block, plaster and paint areas
remain `NOT_ESTABLISHED` for want of a height. The area method is an
arrangement of the bounding lines, cross-checked against the raster and
refused on disagreement; the membership test is asked of the region as
assembled, not of one raster cell (§188). Authored dimensions confirm a
span only when a single dimension or a boundary-to-boundary chain says so
(§189), which replaced bounding boxes smaller than their own polygons.
Skirting nets the skirting-eligible class rather than subtracting a
remembered list (§190), so the three wet rooms read zero pending the
owner's skirted-or-tiled ruling with their wall-edge geometry preserved.
Skirting 99.025 m dry; profile 143.025 m, a separate trade line on the same
walls. Frozen as `FREEZE_PA08_QORTUBA_R3`;
`READY_FOR_WITHHELD_FLOORING_COMPARISON: YES` for the flooring package
only, and the withheld quantities were not requested, opened or inferred.

**PA08-QORTUBA-EXTERNAL-RECONCILIATION-01 (first withheld contractor
comparison).** The contractor sources were unsealed after R3 was frozen. One
document arrived: a priced one-page takeoff sheet dated 23.9.2025, eleven
rows, total 1611.266, whose own arithmetic reproduces exactly. The كيال
working sheets were not supplied, so the transcription register for them is
empty by design (§193). Transcription was frozen at `8346b2bbc412b661`
before any comparison ran, and every R3 artifact hash was verified before and
after; nothing in R3 changed.

The headline result is a confirmed engine defect that is not a geometry
error. The contractor bills skirting and profile at exactly the same length,
76.90 m and 76.90 m, and the owner confirms the black profile sits directly
above the skirting. R3 had released 143.025 m of profile against 99.025 m of
skirting. Sorting the 44.000 m difference into R3's own segment classes
accounts for every metre with zero residual: 12.100 m of door openings,
26.200 m of bathroom wall whose skirting R3 holds at `SOURCE_REQUIRED`,
2.750 m of non-wall edge and 2.950 m of column face. Correcting the trade
rule collapses the profile discrepancy exactly onto the skirting one
(§191, §192). The wet-room release is the worse half: an upper trade was
more certain than the trade beneath it.

Everything else stayed open, honestly. Floor 116.138 m² against 107.76 m²
and skirting 99.025 m against 76.90 m are both unexplained, because the sheet
names no storey and no room; neither is counted as an error. Of eleven
contractor rows, eight need a tiling height, a finish specification or a
sanitary drawing, and the engine emitted nothing for all eight, which is the
refusal holding. Nine rooms are `NOT_COMPARABLE` for want of a room-level
source. Silent wrong quantity count: one, with two unresolved candidates
deliberately excluded (§194). Frozen as
`FREEZE_PA08_QORTUBA_EXTERNAL_RECONCILIATION_01`. No engine rule was changed;
four fixes are recommended for R4 and none implemented.
`READY_FOR_NEXT_VALIDATION_VILLA: NO`.

**PA08-QORTUBA-ROOM-BY-ROOM-QS-01 (source-only takeoff, then the aggregate
check).** The owner asked for the surveyor's own room-by-room calculation
from the DWG rather than a contractor working sheet. Because the contractor
totals had already been seen, integrity rests on order and reach rather than
on blindness (§198): the takeoff module imports no contractor register and no
comparison code, its source carries none of the contractor aggregates as a
literal, and its freeze was written on a clean tree at commit `1de7f7e`
before the comparison module existed.

Three things the drawing gave up that earlier phases missed. An unlabelled
internal lobby of 4.510 m² serves two bedrooms and a bathroom through doors
of 925, 1000 and 1125 mm, and is a room on that evidence (§195). Of seven
glazed elements, six sit in wall bands that run continuously past them so the
floor-level trades run underneath, while one cuts its band through at 2750 mm
between the hall and the preparation area and stops both trades at its jambs
(§196). The profile is issued as a second BOQ item on the skirting's own
path, per the owner's description of the installed product, instead of being
measured again under a rule of its own (§197).

Totals, summed from the rows: dry floor 120.6475 m² over seven rooms, wet
17.8625 m² over three, apartment 138.5100 m². Skirting 106.075 m, profile
106.075 m, ceiling 138.5100 m². Block 51.800 m at 150 mm and 86.930 m at
200 mm. Plasterable face 135.225 m, paint eligible 107.625 m, the difference
being the wet rooms. Every area needing a height stays `NOT_ESTABLISHED`, and
the bathroom and preparation host walls total 38.750 m of net host wall
waiting on one number. Each room formula merges the arrangement into the few
rectangles a surveyor would write by hand, and a test multiplies every
formula back out.

Against the contractor aggregates: flooring 120.6475 against 107.76, skirting
and profile 106.075 each against 76.90. No engine error and no contractor
error was recorded from any of it, because a total of known room scope cannot
be scored against a summary line that names no storey and no room (§199).
What the comparison did establish is that both sides measure the profile at
exactly the skirting length, so the trade rule agrees independently on both
sides even where the magnitudes do not. Frozen as
`FREEZE_PA08_QORTUBA_ROOM_BY_ROOM_QS_01` and
`FREEZE_PA08_QORTUBA_QS01_AGGREGATE_COMPARISON`; no engine rule changed.

**QORTUBA-PRICING-INPUT-MATRIX (trade BOQ readiness).** The frozen
room-by-room takeoff re-cut into the twelve trades a bill is priced by, with
the room rows left underneath as calculation backup. No geometry was
measured and no engine rule touched; the workpaper freeze digest is verified
before the matrix is built and its artifacts are unchanged after.

Six layers are separate fields on every row: measured geometry, commercial
scope, waste, procurement, rate and amount. Only the first is ever filled.
No rate was supplied for this project, so no row carries a rate or an amount,
and the Excel columns for them are created empty on purpose.

Fifty-eight trade rows. Twenty-six carry an established quantity and need
only a rate: floors 120.6475 m² dry and 17.8625 m² wet, skirting 106.075 m,
profile 106.075 m, flat ceiling 138.5100 m², ceiling perimeter 153.125 m
taken on the gross wall line because a cove runs across a door head where a
skirting stops, eight wall-length lines by thickness, three plaster face
lines, paint 107.625 m with the tiled bathrooms excluded rather than assumed
painted, bathroom and roof and terrace waterproofing, the stair plan area and
the door and glazed-unit counts. Thirty-two rows are blocked and each names
one next input.

Grouping those asks collapses thirty-two blocked rows onto seventeen
distinct inputs, and three of them carry most of the weight: the opening
heights unblock eight rows, the stair section four, the finishes schedule
three. Four vertical heights are asked for separately because they are
different numbers, with a note that one building section would supply all of
them. Nothing is requested that no named row needs.

Readiness is reported per trade with no overall percentage, because the
trades are blocked by different things and one number would hide which.
External plaster, external paint and railings are `NOT_READY` and each needs
a drawing this set does not contain. Frozen as
`FREEZE_QORTUBA_PRICING_INPUT_MATRIX`, with the workbook written out in trade
order as `QORTUBA_PRICING_INPUT_MATRIX.xlsx`.

**QORTUBA-FINAL-PRICING-AUDIT (reclassification against the pricing unit).**
The pricing matrix's ready flag tested whether a row held a number rather
than whether it held a priceable one, and twenty-six rows passed that test
wrongly. This pass reclassifies every row against the stricter rule: ready
only when the quantity is in the unit and on the basis the bill prices that
item by (§200). No geometry, no engine rule and no quantity was created.

Sixty-seven rows across sixteen trade sections, now including concrete,
steel, sanitary and electrical as sections of their own rather than folded
into other items. **Final pricing quantities available now: zero.** Thirty
rows carry a measured input, six have the right unit but unconfirmed scope,
thirty need a drawing or a specification, and one records an exclusion so it
stays visible.

The demotions are the point. Blockwork lengths by thickness were offered
against an area rate. Plaster and paint face lengths were offered against
area rates. Seven aluminium units were offered as a count. A 12.643 m² stair
plan footprint was offered against a marble rate. The ceiling's 138.5100 m²
is base geometry and not a decor quantity, and the 153.125 m perimeter is
room geometry and not a cove.

Every row now carries three quantity fields rather than one: measured input,
final BOQ quantity and the unit that second figure must arrive in, with the
conversion formula and the single blocking input written beside it (§201).
Ranking each trade's blockers by how many measured rows they release, rather
than by how often they appear, changed ceramic's first ask from the sanitary
drawings to the tiling height (§202). Two inputs dominate: the wall height
releases ten rows and the opening heights another ten.

Eleven trades are partially ready and five are not ready. Frozen as
`FREEZE_QORTUBA_FINAL_PRICING_AUDIT`, with the workbook rewritten in the
sixteen-section layout.

**URBAN-PROJECTS-BOQ-SCHEMA-LIBRARY (the house pricing structure, learned
from previous projects).** Six historical workbooks were read for structure
only: concrete and steel, aluminium, paint, floors with waterproofing and
decor and railing, internal and external plaster, and blockwork. Two are
legacy `.xls` and were read directly with a read-only reader, so no
conversion was needed and no original was modified; two further uploads are
byte-identical duplicates and one is a programme of works rather than a bill.

Forty-one items recorded with their raw Arabic name, canonical name, pricing
unit, quantity basis, formula pattern, quoted deduction rule and source sheet.
Every item's Arabic text is verified to exist in the sheet the register names,
and every workbook hash is verified. No quantity, rate, total or room
dimension from any reference project is stored, and a test scans for them
(§203).

Two row shapes run through every workbook: a summary invoice carrying the
priced items with full and half deduction columns, and a detail takeoff where
count, length and height build each element under a storey heading. Ten house
conventions were recovered, including openings deducted at half rather than
in full, corner and end beads measured by the metre and then halved under the
rule written on the sheet as 2م=1م, a waterproofing upturn priced by the
metre with no height, stairs and landings as one combined area with a counted
side piece, and blockwork priced by area per thickness with external
blockwork as its own item.

Against that schema, fifteen Qortuba pricing units are confirmed and five are
wrong (§204). The upturn correction is the valuable one: carried as an area
needing a height, the house prices it by the metre, so the measured bathroom
perimeter of 27.600 m is already the quantity. Thirteen rows need recutting
to the house's row shapes, chiefly the stair, the ceiling decor split and the
aluminium summary (§205). Ten house items have no Qortuba counterpart, among
them render under skirting, plaster corners and ends, and the roof upturn,
which needs a roof perimeter Qortuba never measured. Three rows have no house
precedent at all, including the black profile, and none was given one (§206).

### Urban BOQ rule registry and the Qortuba conversion map

The schema library says how the house measures. Turning that into rules for a
live project is where a reference project leaks, so the registry records each
rule at a level: thirty-six rules, thirty-five HISTORICAL_PRECEDENT and one
QORTUBA_PROJECT_RULE, none at URBAN_STANDARD (§207). Each carries its
generalisation safety: seventeen safe candidates, eleven trade-specific,
six contractor-specific and two project-specific. The six contractor-specific
rules — the half deductions on plaster and paint, the 2م=1م halving of corners
and wall ends, the blockwork deduction columns — are the ones that look like
house practice and are not, and none of them is applied to Qortuba without the
owner (§208).

The conversion map holds thirty-nine Qortuba BOQ items, each with three
separate quantity layers. Exactly one final BOQ quantity exists: the bathroom
floor waterproofing, 17.8625 m², where the measured unit and the house pricing
unit are the same and the house bills the item with no deduction, so the
conversion is the identity. The membrane specification is still outstanding
and sets the rate, not the quantity, which is why that row is final and the
ceramic rows carrying the same kind of area are not.

Three more items are a single rule decision away, each already measured in the
right unit: the skirting at 106.075 m, the black profile on the same path at
106.075 m, and the bathroom waterproofing upturn at 27.600 m. Fifteen items
need one project input, overwhelmingly a height the drawing set does not
contain; fourteen need a drawing or a schedule.

Thirteen owner questions are raised, ranked by how many measured rows each
answer alone makes payable — and a compound blocker is never counted as
released by one answer (§209). The tiling height leads, releasing the two wall
ceramic rows. The blockwork height affects nine rows and releases none of
them, because every blockwork row also waits on the deduction column. Missing
drawings are listed as documents rather than dressed up as decisions.

Two quantities changed shape in this pass and neither was recomputed. The
seventh glazed element, still UNRESOLVED, was taken out of the aluminium
windows item and given its own row (§210); and the ceiling cornice was given
the gross wall line of 153.125 m rather than the net skirting run, because a
cornice crosses the doorway a skirting stops at (§211). The black profile
remains a new candidate BOQ item, بروفايل أعلى النعلة, priced by the metre by
analogy with نعلات, marked as a Qortuba project rule and an Urban standard
candidate, and not promoted.

### Owner rules v1 and the Qortuba recalculation

The owner supplied explicit rules, and they sit on a stored priority ladder:
a project drawing beats an owner override, which beats an approved Urban
standard, which beats an approved temporary default, which beats a question.
A historical BOQ precedent sits on no rung of that ladder at all until the
owner puts it on one (§207 still holds; what changed is that ten rules now
have an owner behind them).

Ten rules were promoted to URBAN_STANDARD: connected floor and wall ceramic
in wet and service rooms, no skirting or profile in such a room, no paint on
a fully ceramic face, the membrane as a floor item plus a 0.15 m upturn, the
doorway left unbroken in that upturn, the full opening deduction for all
wall-area trades, 0.25 m three-sided reveals for plaster and paint, the
hidden skirting and hidden profile sharing one payable path, normal skirting
as a separate system at half the hidden rate, and source dimensions over
defaults. Eight Qortuba project rules carry the four 3.00 m heights and the
project's system choices, and are explicitly not company policy. One
temporary default — a 2.20 m door height — is flagged on every figure it
touches (§213), and was not extended to windows (§214). Seven historical
precedents were superseded and demoted to reference only, among them both
half-opening deductions and the blockwork deduction column that had been the
single most-blocking open question.

Thirteen quantities are now final. The hidden skirting and the hidden
profile are 96.475 m each, down from 106.075 m: the PAINTRY leaves the
skirting under the ceramic rule and the column faces join it under the
deduction rule (§217). The bathroom membrane is 17.8625 m² of floor and
30.225 m of upturn, the latter corrected upward by exactly the three
bathroom door widths (§216). Floor ceramic splits into 17.8625 m² wet and
11.685 m² service, leaving 108.9625 m² of dry floor still waiting on a
finishes schedule. Six blockwork thicknesses are final at 3.00 m with full
opening deductions.

Seven quantities are partially calculated: they carry a deterministic value
and a named list of openings that still have no height. Bathroom wall
ceramic reads 84.900 m², computed from the gross perimeter so the tiled
strip above each door head survives; plaster and paint each read 311.951 m²
over the same dry faces, equal by construction rather than coincidence; tile
preparation reads 118.350 m². The residual is honest and bounded: seven
glazed elements and ten unclassified sites have no height, and six of the
glazed elements have no host room either, so they are named on every row
they could reach and on no row they could not (§215).

Eleven owner questions are now closed and recorded as closed, so they are
not asked again. Five remain, and only one of them is new: whether the
PAINTRY takes waterproofing as well as ceramic, with 11.6825 m² of floor and
11.150 m of perimeter already measured and waiting on one word.

### Owner-rule application audit

The owner asked for the recalculation to be audited before any quantity was
accepted. Two of its findings changed the bill.

The blockwork had been formed from anything with a measured spacing. Object
identity was never checked, and six of the eight thickness groups turn out
to contain no masonry at all: the 300 mm group is four 2.900 m bands drawn
on the STAIR layer around the stair shaft, the 350 and 450 mm groups are
COLUMN_BANDs closed at both ends with an evidenced fill, the 550 mm band
shares the COL and WALL layers, the 600 mm band bounds stair on both sides,
and the 219 mm group is eighty millimetres of drafting arrow with both face
roles UNKNOWN_GEOMETRY (§218). All six are demoted to geometric reference.
Within the surviving 150 and 200 mm groups a further 10.35 m of column and
compound band is excluded, so confirmed masonry is 128.38 m of the measured
155.16 m, and blockwork falls from 260.790 to 235.740 m² at 200 mm and from
138.735 to 134.495 m² at 150 mm.

The skirting proof came out differently from expected. The path reconciles
segment by segment in all ten rooms, and no opening height enters it at all
(§219) — but the width of six glazed elements was not deducted, because
each stands in a band carrying no opening site, so the wall runs
continuously past it in plan. Leaving them on the path gives 96.475 m;
deducting every window width gives 86.589 m. Both are published and the
pair is demoted to PROJECT_RULE_REQUIRED, because the difference is a
reading of the rule rather than a fact about the drawing.

Two smaller repairs came with it. Every glazed element is now joined to its
host band and host room, so a window in one bedroom no longer blocks the
plaster in another — and attributing by room id rather than room name
corrected a double count across the two rooms both called BED.ROOM (§220).
Tile preparation reconciles exactly with the two wall ceramic items,
118.350 m² either way, because the backing render sits behind the tile on
the same faces.

Thirteen quantities were final before the audit. Five survive it.

### Opening completion and the confirmed skirting

The owner confirmed the skirting rule: every door, sliding door and window
width comes off the path. The hidden skirting and the hidden profile are both
86.589 m, stored as QP-10 and QP-11, and the question is closed. The
superseded 96.475 m reading is kept beside them with the rule that closed it
(§224).

The remaining blocker was opening height and type, so the drawing set was
searched exhaustively for both. Nothing was found, and the search itself is
recorded: no block attributes anywhere, all 101 dimensions in the plan plane,
no schedule, no elevation, no section, no opening mark, and no named block of
an opening type (§222). The drawing carries no opening height at all, and the
three things that could supply one are named.

Two things the search did resolve. Five sites interrupt only one face of
their wall — four of them exactly one wall thickness wide — and a doorway
interrupts both, so they are wall ends rather than openings; with four CAD
junctions that is nine register entries which now block nothing (§223). And
the independent PDF reading, whose declared powers cover the presence of a
door, identifies two of the remaining gaps as doorless openings, recorded as
type evidence and never as a dimension.

The blockwork gained nothing from the owner's rule and lost nothing either:
235.740 m² at 200 mm and 134.495 m² at 150 mm, both still partial, because
every masonry group carries either an unheighted opening or a thickness whose
face doubling leaves the BOQ line ambiguous. Wall ceramic is 84.900 m² to the
bathrooms and 33.450 m² to the PAINTRY; tile preparation is 118.350 m², still
the exact sum of the two. Plaster and paint are 311.9513 m² each.

The aluminium rows are schedules rather than counts (§225): seven door
openings at 16.665 m² on the temporary door height, and seven glazed elements
with widths and no areas, because no default may reach a window.

Seven quantities are final. One silent escape was caught on the way: the room
HALL / whgm never matched the canonical name HALL, so HALL had been dodging
every opening residual in the register. It now carries five.

### Owner inputs v2 and the communication rules

Five rules were promoted to URBAN_STANDARD and six Qortuba inputs stored.
Two of the standards are about how the engine talks rather than how it
measures: there is no default window height, an absent one is
OWNER_INPUT_REQUIRED (§227), and no question put to an owner may carry an
internal identifier (§226). Eleven questions are now asked in words — room,
opening, width, what it joins — with the ids in an audit column and a
numbered plan crop drawn from the frozen geometry so the numbers on the
sheet match the numbers in the table.

The other three standards changed quantities. Interior doors are PVC and
have their own schedule, aluminium carries exterior openings only (§228);
the waterproofed room types are enumerated and now include the pantry; and
a ceiling is priced by area until a ceiling drawing exists, so the 153.125 m
perimeter leaves the bill (§230).

Thirteen quantities are final. The pantry joins the waterproofing at
11.685 m² of floor and 11.150 m of gross-perimeter upturn — the gross room
perimeter, not the skirting path, which is zero there. The dry floor is
released as porcelain at 108.9625 m², re-totalled room by room from the
frozen polygons rather than inherited, because the pantry left the dry set
after that subtotal was written. The ceiling is one line at 138.510 m². The
PVC schedule is 16.665 m² across seven doors; the internal glazed opening is
6.050 m² on the owner's supplied 2.200 m height; the aluminium schedule
carries six windows with widths, no areas and no assumed heights.

That supplied height moved four other figures. Wall ceramic to the pantry
falls to 27.400 m², tile preparation to 112.300 m² — still exactly the sum
of the two wall ceramic items — and plaster and paint to 305.9013 m² each.
Blockwork at 150 mm falls to 128.445 m² as the wall carrying that opening
resolves.

One defect the tests caught: the opening had been deducted from the Hall
only. A blue element's nearest-room attribution had collapsed a two-room
opening to one room, leaving the Pantry with 6.050 m² of wall it does not
have (§229).

### Crops for the five unanswerable questions, and a price that is not an area

Nothing was recalculated in this pass. Two things were made answerable.

Eleven questions were open. Six named a room and a window and could be
answered from an armchair. Five asked what an opening *is* — and a sentence
like "a 1.100 m gap in a bedroom wall facing the stair landing" is not a
place. Neither was the whole-plan image: eleven numbers at plan scale sit on
top of each other.

So each of the five got its own crop, generated in
`research/qs_wall_treatment_01/pa08/qortuba/boq/owner_question_crops.py` from
material already frozen. The jamb object ids the R1 opening register names
are resolved back to coordinates in the DWG decode — a lookup, not a new
measurement — and the gap is drawn on the host band's own centreline and
thickness. Around it goes enough wall to recognise the place, with the
adjacent rooms named, one large red number on the questioned gap, and the
measured clear width printed on the image. Below it the six choices: door,
open passage, window, sliding door, not an opening, other. No CAD handle,
site id or hash appears on any image; the opaque id stays in the audit
record. Openings #10 and #11 sit at opposite ends of the same 1.900 m stub,
so each crop says so — a person shown one of them would otherwise answer for
both (§231).

The second correction is a status, not a number. The seven interior PVC
doors and their 16.665 m² of opening area are established and every wall
trade around them has already taken the deduction — but none of that says
whether the doors are priced per door, per set, or by the square metre. The
row now carries PHYSICAL_OPENING_AREA_M2 = 16.665 ESTABLISHED with
FINAL_PRICING_QUANTITY empty and PROJECT_RULE_REQUIRED, rather than
reporting the one number it happens to have as though it were the bill. The
Hall/Pantry glazed opening is the same: 2.750 × 2.200 = 6.050 m² is
physically fixed and stays deducted from both rooms, while its commercial
material and trade are unwritten (§232). Both are now open items O-09 and
O-10 in the question ledger; V2-03 — that the doors are PVC and not
aluminium — stays closed.

### The open-passage correction

The owner answered two of the five gaps: both 1.200 m openings are open
passages, not doors. The other three stay unresolved and are not inferred.

OPEN_PASSAGE is now a permanent opening type (§233) with two subtypes,
OPEN_PASSAGE_FULL_HEIGHT and OPEN_PASSAGE_WITH_HEAD. It carries no
procurement line at all — the PVC schedule is unchanged at seven doors and
16.665 m², and neither passage appears in it or in any aluminium row — and
it takes no height from the door default, because a passage is not a door.

The correction that had a number attached to it was in the linear path. The
frozen boundary traced both gaps as continuous wall face, so their widths
were still on the skirting and profile run; skirting does not run across an
opening. Each passage interrupts the path of both rooms it joins:

| Opening | Room path | Before | After |
|---|---|---|---|
| Hall ↔ Lobby, 1.200 m | HALL | 23.054 | 21.854 |
| | UNLABELLED_INTERNAL_SPACE (Lobby) | 7.050 | 5.850 |
| M.Bedroom ↔ Dressing, 1.200 m | M.B.ROOM | 15.452 | 14.252 |
| | DRESS | 12.425 | 11.225 |

Four widths, 4.800 lm, so the hidden skirting and the hidden profile both
move from 86.589 lm to **81.789 lm**. QP-09, the owner's window rule that
fixed 86.589, is untouched; QP-17 records what came off it and QP-10/QP-11
carry the corrected figure. The row stays FINAL: a linear deduction needs no
height and does not wait for one.

Nothing else moved. No wall area was deducted for either passage — the
vertical condition is QP-18, OWNER_INPUT_REQUIRED, and the blockwork,
plaster, paint and wall-ceramic rows of the four rooms involved simply
continue to name these two openings among what they are waiting for, as they
already did. The question put to the owner is now the one that is still
open: "is it open all the way to the ceiling, or is there wall above it?"
The type question is retired for those two (§234), and their crop numbers,
#8 and #9, do not move.

### QS Workflow v1, and the two passage answers

The development philosophy changed here. The objective is not an engine that
understands every drawing condition on its own; it is drawings → first
takeoff → owner questions → owner answers → final quantities → Excel →
owner approval. Where a ten-second answer resolves an ambiguity, the answer
is cheaper and more reliable than the geometry rule, and the rule is written
only when the same deterministic error would recur across projects.

Both passages are now answered. #8, Hall ↔ Lobby, is
OPEN_PASSAGE_FULL_HEIGHT at the 3.000 m wall height — 1.200 × 3.000 =
3.600 m², left and right reveals, no top, because there is no head to finish
(§237). #9, Master bedroom ↔ Dressing room, is OPEN_PASSAGE_WITH_HEAD at
2.200 m — 1.200 × 2.200 = 2.640 m², all three reveals. That 2.200 m is an
explicit Qortuba owner input recorded as QP-19, not TD-02 wearing the same
number. Neither enters a procurement schedule.

The false ceramic dependency is gone (§235). #8's host band runs past a
bathroom and the Pantry, so the over-inclusive attribution had it blocking
bathroom ceramic, pantry ceramic and tile preparation — three faces it is
not in. Attribution now prefers the two rooms an opening actually joins.
Bathroom ceramic has no pending opening at all and waits only on the TD-02
door heights; pantry ceramic and tile preparation wait only on the Pantry
window, which really is in the Pantry wall.

The skirting and profile figure was revalidated rather than protected:
81.789 lm still checks, because the width deduction never depended on the
height.

The export shape is prepared but not connected (§238):
`APPROVED_QUANTITIES.json` carries all nineteen fields per record and leaves
every one of them DRAFT.

### Finishing mode

The internal door height is confirmed: 2.20 m, an
OWNER_CONFIRMED_PROJECT_PARAMETER stored as QP-21, not the TD-02
placeholder it replaces (§239). Nothing about the arithmetic changed — the
figure was always 2.20 m — but the reservation attached to it is gone, so a
quantity whose only outstanding item was the door height is now FINAL.

Bathroom wall ceramic, **84.900 m²**, is the row that moved: established
host length, QP-01 tile height 3.00 m, source-established door widths,
QP-21 door height, and — since QP-20 removed the dry-room opening that never
belonged to those faces — nothing pending. Thirteen quantities are now
final, six partial.

The six that remain partial each name a real outstanding opening: pantry
ceramic and tile preparation wait on the Pantry window; plaster and paint
wait on six window heights and three unresolved gaps; the two blockwork
rows wait on a thickness-item ambiguity that is not an opening at all.

The PVC schedule keeps its layers apart: seven doors and 16.665 m² of
opening area are established as physical facts, and FINAL_PRICING_QUANTITY
stays PROJECT_RULE_REQUIRED until the owner gives the unit. A settled
measurement does not settle a pricing basis.

The final owner batch is eleven rows of three kinds (§240): nine
measurement inputs that hold up quantities, one trade classification, and
one pricing input that holds up nothing in the takeoff at all.

### Final completion: the last three gaps, and two defects they exposed

The owner closed #7, #10 and #11 as full-height wall interruptions for
measurement — 3.000 m, no architectural type named and none inferred, no
procurement item of any kind. Storing them surfaced two errors that were
already in the engine.

The first was arithmetic. The 1.900 m stub between the two 1.100 m bedroom
gaps produced **−0.900 m²** of blockwork: the band's measured length already
stops at each gap, so deducting them subtracted wall that was never counted
(§241). Seven walls carry an end gap, four of them doors, so this had been
quietly understating blockwork since before these openings existed.
Correcting it moves figures reported earlier in this project — 150 mm
blockwork settles at 128.870 m² and 200 mm at 235.740 m².

The second was attribution. #10 and #11 sit in a band that belongs to two
unlabelled spaces; no apartment room's finish run passes along it. They
therefore interrupt no skirting path and deduct from no room's plaster —
while remaining real holes in a confirmed masonry band, which the blockwork
row records. Reveals now follow deductions rather than leading them (§242).

Room-side attribution is read from the frozen finish-path registers (§243),
which name the 2.700 m opening's rooms exactly — the Hall and the 18.75 m²
bedroom — and independently reproduce the pairs already established for both
passages.

Hidden skirting and hidden profile settle at **76.389 lm**; plaster and
paint at **283.0025 m²** each. Thirteen quantities are final. The only
measurement questions left are the six window heights.
