# 13 christiannp donor code: techniques read from the frozen scripts

**Scope and handling:**
- The scripts are read as data from the frozen ZIP (`06_ground_beams/pairing.py`, `ground_beams.py`, `strap_beams.py`; `09_slabs/raster.py`, `planar.py`, `slabs.py`; `05_footings/footings.py`; `08_beams/beams.py`; `10_walls/walls.py`; `07_columns/columns.py`; `03_schedule_attributes/schedules.py`; `16_final/derive.py`).
- No script was executed. No code is copied into Urban.
- The ZIP carries no licence file, so the code stays NOT_LICENSED_FOR_REUSE. Only the concepts below may be rebuilt independently, Urban-native.
- "Urban" means the exact module that does the same job today.

## T1. Face pairing: `pairing.candidates` / `decide` / `strip_geom`

| Field | Content |
|---|---|
| INPUT | segments (LINE, LWPOLYLINE straight and bulge segments, ARC) with handle and layer |
| OUTPUT | every candidate pair with angle error, separation, overlap, % overlaps, endpoint relation, ACCEPT/REJECT + reason, and a shared-face flag; strips = the overlap centreline |
| ALGORITHM | O(n²) over straight pairs: angle ≤ `ang_tol`, perpendicular separation ≤ `sep_max`, projected overlap > 0. Arcs: concentric (≤ 5 mm), radius difference ≤ `sep_max`, angular overlap > 0. Acceptance: allowed layer, separation in [`sep_min`, `sep_accept_max`], overlap ≥ `min_overlap`, no allowed parallel face strictly between them over ≥ 50 % of the overlap. Side-aware ambiguity: a face accepted with partners on **opposite** sides |
| TOLERANCES | GB: 1°, ≤ 1000 candidate / 150–800 accept / overlap ≥ 150. Walls: 90–450, overlap ≥ 100, duplicate < 5 mm. Slabs: sep ≤ 1050 and schedule width ± 15 |
| ASSUMPTIONS | faces are straight or concentric; a beam is two parallel faces on one layer |
| FAILURE MODES | O(n²); multiple partners per face are all accepted (correct for fragmented mates, but needs interval accounting to avoid double area — christiannp has none); `FACE_SHARED_WITH_OTHER_ACCEPTED_PAIR` is False for P0035 / P0036 although face 114 is in both (collinear same-side partners are deliberately not "shared", so the column name overstates) |
| KNOWN FP / FN | FP if a stair or furniture layer is admitted (guarded by the layer whitelist); FN when one face is a polyline-bulge chord approximation |
| URBAN EQUIVALENT | `alsenan_v3_structure._pair_bands` (GB: one best partner, forward-only, 300 ± 12), `wall_band_reconciliation.pair_parallel_faces` (Method B), `engine/physical_wall.py` (fragmented-mate interval matching, walls only) |
| VERDICT | the full candidate log, multi-partner pairing and the intervening-face test are stronger than Urban's GB builder. Urban already has the interval idea for walls; the gap is applying it to GB and to Method B |

## T2. Arc strip length: `_ang_overlap`

- **Algorithm:** the angular overlap of the two arcs × mean radius.
- **Urban equivalent:** `_arc_bands` uses arc a's sweep. It is wrong when the sweeps differ: +0.718 m on 157 / 158.
- **Verdict:** ADOPT_CONCEPT.

## T3. GB topology: `ground_beams.run`

| Field | Content |
|---|---|
| ALGORITHM | each strip end snaps in order: column box ± 60 → T-junction onto a straight strip (distance ≤ w/2 + 60, angle > 10°) → onto a curved strip (≤ w + 60) → S-BW box (± 60) → corner (end to end ≤ 400) → free end. Through-columns are found by Liang–Barsky clipping and become interior supports. Edges are strips split at landing parameters. Bands are collinear strips with gap ≤ 1000 and the same width. |
| FAILURE MODES | tolerance snapping on oblique arrivals (MD07: the curved target needs w + 60); a corner radius of 400 can merge distinct ends; only the first column hit counts |
| KNOWN FP / FN | FREE_END may be a real stub or a missed support (4 here); no FP observed |
| URBAN EQUIVALENT | none (spans = band − columns) |
| VERDICT | CHALLENGER_ONLY, as a QA graph (free ends, degree histogram). Rebuild with face-line intersections, not tolerances |

## T4. Column split of beam length: `clip_len`

- **Algorithm:** clip the centreline by each S-COL.BON box, summing every box it touches (end boxes included).
- **Urban equivalent:** polygon difference, then the projected extent of each piece.
- **Assessment:** the two conventions differ by 7.2 m on this sheet (16.256 against 9.051 m). Both are deterministic.
- **Verdict:** CHALLENGER_ONLY: a declared convention, both values carried.

## T5. Strap beams: `strap_beams.py`

- **Algorithm:** pair S-FOOTINGS faces; reject FOOTING_TO_FOOTING_GAP (both faces are edges of two different footings, MD08); choose the schedule row by drawn width (R4).
- **Failure mode:** the strip length is the full face overlap, including the length inside the footings, so footing concrete is double-counted (6.036 against Urban's clear 3.392 m³).
- **Verdict:**
  - footing-gap rejection: ADAPT;
  - length rule: REJECT (keep Urban's clear length).

## T6. Raster area oracle: `raster.run`

| Field | Content |
|---|---|
| INPUT | barrier segments (face layer + S-OPENING edges, minus X / fan lines), column boxes, strip rectangles / annular sectors, opening seeds, slab seeds |
| ALGORITHM | square grid at res with an origin shift; barrier samples every res / 3 → EDGE cells (an 8-connected chain); column boxes filled; OUTSIDE = 4-connected flood from border cells (cannot cross an 8-connected chain); components of the remaining FREE cells; a cell centre inside a strip rectangle → BEAM_INTERIOR; a component holding an opening seed → OPENING; < 0.10 m² → UNRESOLVED_ENCLOSED; else SLAB. Area = SLAB × res²; alternative = + ½ × EDGE cells touching SLAB |
| TOLERANCES | res 100 / 50 / 25 / 10 mm; origin shifts (0, 0) and (0.37 r, 0.61 r); min component 0.10 m² (A09) |
| FAILURE MODES | always under-reads by the edge band (GBP 10 mm: −1.03 m² against Urban BEST, −1.70 m² against christiannp's own vector); a one-cell drawing gap leaks at fine resolution; voids smaller than a cell vanish; runtime grows with 1 / r² (3.2 s at 10 mm on 5.1 M cells) |
| CONVERGENCE (frozen) | GBP slab-only 201.94 → 209.70 → 213.59 → 215.98; half-edge 215.70 → 216.76 → 217.19 → 217.44 against vector 217.68; origin difference at 10 mm ≤ 0.04 m². Same pattern on GFRS / FFRS / SFRS (half-edge within 0.03–0.18 % of vector at 10 mm) |
| URBAN EQUIVALENT | none (Urban is vector-only: `ground_slab_recovery`, `slab_region`) |
| VERDICT | **ORACLE_ONLY**. Stable and independent of the vector arrangement, so it is a good regression oracle for leak detection (a jump in OUTSIDE cells between resolutions). Never a publishing route. |

## T7. Vector planar faces: `planar.faces` + `slabs.vector`

- **Algorithm:**
  - discretise arcs (≤ 3° chords);
  - split at intersections and T-touches (tolerance 2 mm);
  - snap vertices (1 mm);
  - half-edge traversal to bounded faces, with nested outlines subtracted as holes;
  - classify each face by an interior point (point classification) or by sampling (apportioning).
- **Barrier set:**
  - face layer (`1`; on GBP also `S-BW`);
  - **S-OPENING edge segments**: X-cross and fan lines removed;
  - column boxes.
- **Failure modes:**
  - point classification mislabels mixed faces (218.33 against 217.68 m² sampled);
  - the detail-cluster rule ("touches no column") dropped one real plan segment (U21);
  - the lift pit is found as an S-BW closed polyline whose area is **3.24 m² ± 0.01 m², hard-coded** (`slabs.py` line 122): a DONOR_HEURISTIC that would not generalise.
- **Urban equivalent:** `engine.source.slab_region.regions` (T.build arrangement, sites, band-point component selection, opening roles by VOID label / cross length / tread lines) and `ground_slab_recovery.decompose` (shapely difference).
- **Verdict:**
  - S-OPENING edges as barriers: ADOPT_CONCEPT. It resolves Urban's GF OPENING_CONFLICT.
  - Detail-cluster rule: REJECT, because Urban's band-point component selection is safer.
  - Pit-by-area: REJECT. Use the S-BW layer role plus a closed box instead.

## T8. Opening markers: `slabs.prepare`

- **Algorithm:**
  - **X-cross:** two S-OPENING lines intersecting in their interiors (0.05 < t < 0.95). The intersection point is the seed.
  - **Radial fan:** ≥ 6 S-OPENING line ends at one rounded point → AMBIGUOUS_VOID.
- **Urban equivalent:** cross length ≥ 1.5 × the face diagonal → OPENING_VOID. This also fires on fans.
- **Verdict:**
  - X-cross seed: equivalent.
  - Fan detection: ADOPT_CONCEPT, as a classification (AMBIGUOUS) only.

## T9. Footing occurrences: `footings.py`

| Field | Content |
|---|---|
| ALGORITHM | 4 outline routes (A1 F-block unit square scaled; A2 closed polyline; A3 four-line loop; A4 open notched polyline closed by bbox); tags by regex; candidates ≤ 2500 mm; priority (1) tag inside + dims within 60 mm, (2) nearest with matching dims, (3) nearest only, flagged; all candidates logged; two tags on one outline → UNRESOLVED |
| TOLERANCES | 60 mm dimension match; 2500 mm search |
| FAILURE MODES | dims are compared as a sorted pair (L / W orientation ignored); A4 bbox closure assumes the notch lies on the bbox edge (MD05) |
| URBAN EQUIVALENT | S1 `FOOTING_OCCURRENCE_REGISTER` (the same 4 geometries; competing_tags kept; OUTLINES_OVERLAP check) |
| RESULT | 26 / 26 outlines identical by handle; the same F / F10 conflict |
| VERDICT | KEEP_URBAN. A useful addition is the **logged rejected-candidate list** (34 rows), as a regression fixture |

## T10. Beam tag binding: `beams.py`

- **Algorithm:**
  - candidates within 1500 mm;
  - accept the nearest strip that is parallel (|tag rotation − strip angle| ≤ 10°), within the strip's extent, within 1000 mm, and whose schedule width matches the drawn width within 30 mm;
  - if only parallel and within extent: UNRESOLVED (width);
  - else UNRESOLVED (no parallel strip).
- **Failure modes:**
  - the orientation test uses the **tag text rotation**, so horizontal tags on oblique members (B7 ×4, B4 ×2 on FFRS) can never bind;
  - wide beams (B27, 900 mm) are lost when no strip of that width is paired within 1 m.
- **Urban equivalent:** `engine.source.beam_binding.bind` (merged member lines, tag rotation from the DXF, breadth mismatch = flag, never nearest-text).
- **Verdict:**
  - use the width-equality gate and the orientation + extent test as a **tie-break for Urban AMBIGUOUS tags only**: ADAPT;
  - do not use it as the primary binder.

## T11. R1–R5 object tests: `beams.py`

| Rule | Assessment |
|---|---|
| R1 | 25 CONDITIONAL: the band strip sum against the schedule span sum. Urban already raises SPAN_LENGTH_CONFLICT / SPAN_COUNT_CONFLICT |
| R2 | collinear inheritance; 2 of 6 unsafe |
| R3 | same-mark de-dup on one band; safe in 34 cases |
| R4 | schedule-width validation; safe in 104 cases |
| R5 | never applied; 3 cases would have been unsafe |

**Decision:** keep Urban. Do not reintroduce R5.

## T12. Wall per-metre classification: `walls.py`

- **Algorithm:**
  - an accepted pair on a W-layer face → OPENING_SPAN;
  - column overlap (centreline samples every 20 mm inside S-COL.BON boxes) > 50 % → COLUMN_OVERLAP;
  - shared face → UNKNOWN;
  - separation < 140 → parapet / kerb;
  - else PHYSICAL_WALL.
  - Rejected rows are classified as DUPLICATE (< 5 mm), FINISH_LINE (5–60 mm on layer 1) or LAYER5 parallel pairs.
- **Failure modes:**
  - **no door / window block overlap test**: door spans whose faces are drawn continuous stay PHYSICAL_WALL, and OPENING_SPAN comes only from W-frame pairs (9.94 m);
  - LAYER5 pairs (248.9 m) are not separable.
- **Urban equivalent:** `wall_band_reconciliation.classify` (column boxes; door / window extents grown 25 mm, with a door-swing circle box that can over-cover the wall either side of the leaf; duplicate stretch).
- **Result:** on the 166 face-identical pairs (270.63 m gross), christiannp says wall 210.39 / column 32.93 / ambiguous 27.30. Urban says wall 175.06 / column 31.71 / **opening 53.96** / duplicate 9.89.
- **Verdict:**
  - the opening definition differs. Neither system's per-metre opening class is authoritative; reconcile against the R5 opening evidence register;
  - the side-aware ambiguity rule: KEEP_URBAN (Urban WALL_BAND_AMBIGUOUS already covers it).

## T13. Column continuity: `columns.py`

- **Algorithm:**
  - closed S-COL.BON outlines per plan in frame-local coordinates;
  - cluster positions within 120 mm;
  - 120–600 mm offsets are logged as rejected continuations;
  - record the hatch pattern (SOLID / ANSI35) and the nearest C* text within 1200 mm;
  - a storey interval is counted when the outline is drawn on that storey's roof plan.
- **Failure modes:**
  - turned or shifted columns split into two positions (2 chains here);
  - planted columns are counted in the storey below (3 intervals).
- **Urban equivalent:** the S1 `COLUMN_VERTICAL_CHAIN_REGISTER` (members by sheet, planted_on, type changes).
- **Verdict:** KEEP_URBAN. The hatch pattern is useful as corroborating evidence only (MD14).

## T14. Schedule ATTRIB reading: `schedules.py`

- **Algorithm:** for each schedule INSERT (FT, FTB, CGT, SBT, C-BEAM2, C-BEAM3), read the ATTRIBs. Semantic field = **the header TEXT above the ATTDEF x-position** (FT: W prints under 'L', H under 'W', DEPHT under 'H'). Parse numbers with an optional '/m' suffix.
- **Urban equivalent:** S1 `rules_s1` maps the FT tags to L / W / D by a fixed table.
- **Verdict:** ADOPT_CONCEPT. Header-position binding is generic, and it would have caught the tag-name lie without a project table (MD02).

## T15. Rebar evidence: `derive.py`

- **Algorithm:** one row per evidence item: raw text, handle, source type, parsed value, geometry length, assumption, include / exclude + why. kg = count or rate × length × d² / 162, with **bar length = member dimension** (A05: no cover, hooks or laps). STI-B is read as per metre (A06); the FT mesh is taken as the bottom layer (A07).
- **Urban equivalent:** the S1 / S3 evidence registers per element, `rebar_model`, and the ACCURATE / ROUGH separation (RF.1).
- **Verdict:**
  - the single evidence table with terminal states: ADOPT_CONCEPT (it is the annotation census Urban still lacks as one artefact);
  - the length rule and the kg: REJECT for accurate rebar.
