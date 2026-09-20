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
