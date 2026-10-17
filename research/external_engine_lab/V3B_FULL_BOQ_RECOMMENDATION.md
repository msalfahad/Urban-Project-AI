# URBAN QTO — V3b FULL BOQ COMPLETION PROGRAM — recommendation (before implementation)

Base: V3a frozen registers (`tests/alsenan/registers_v3`, built twice from 245b4d3, byte-identical), Reporting V3 + unit
addendum (550318a). No engine, register or workbook has changed for this recommendation.

**Benchmark firewall.**
- The freelancer / web-app material was used only through the frozen B1 register, and only for **item names and scope
  labels** (expected-scope check, §20 of the brief).
- No benchmark quantity chose or changed anything here. The single benchmark number quoted (44.19 t rebar) is the one the
  owner quoted in the brief.
- The six excluded uploads were not opened.

---

## 1. Honest starting point (V3a)

| Trade | V3a item coverage | What is missing in plain words |
|---|---|---|
| Concrete | 62.1 % | necks, exterior ground beams, annex ground-slab zone, stairs, pool, domes, boundary wall; 9 column + 25 beam occurrences unbound |
| Rebar | 65.6 % (by items) — **far less by weight** | slabs not bound at all; every beam set waits for hook / bend detail; necks / starters; stairs, pool, domes, boundary wall absent |
| Blockwork | 81.6 % | over-opening infill, boundary wall |
| Plaster / paint | 35.4 % (82.9 % core) | external facades; paint in 3 zones under unbound beams; extras only REVIEW |
| Flooring | 95.1 % | stair finish, courtyard |
| Ceilings | 49 % items / 100 % core | cornice REVIEW only |
| Wall tile / WP | 100 % | but wall tile is **gross of openings** (conflicts with the Urban rule UP-CER-005) and the upturn is **hidden inside the membrane m²** |
| Openings | 66.7 % | **no opening area at all** (heights "not printed") |
| Stairs / railings | 50 % | riser count, waist, treads, handrail |

**Rebar shows the problem most clearly.** The official procurement subtotal is 6.891 t against a diagnostic 44.19 t.
The register explains most of the gap without any benchmark logic:

| Population | Bar sets | State in V3a |
|---|---|---|
| Suspended slabs | 0 | not bound at all |
| Beams | 204 | PARTIAL, straight weight only (4.116 t); hooks missing |
| Beams | 24 | BLOCKED |
| Ground beams | 124 | PARTIAL (1.253 t straight, interior beams only) |
| Columns | 74 | PARTIAL (1.093 t straight) |
| Lintels | 59 | PARTIAL (0.140 t) |
| Necks / starters, stairs, pool, domes, boundary wall | — | absent |

Only footings, two ground-slab sets and part of the columns and lintels are "complete".

**Root cause of most of the 32 BLOCKED lines.** V3a treated the twelve architectural PDF pages as "localisation only".
That was a wrong authority classification, not a property of the source:
- they are 4672 × 6624 px rasters of **dimensioned** 1:100 elevations and sections;
- they print levels, opening sizes, dome spans and rises, pool depths and the fence height (see §2).

---

## 2. New evidence found during this inspection

| # | Source (page) | Evidence (read directly) | Unlocks |
|---|---|---|---|
| E1 | P7757 arch PDF 07-12 p.2 — NORTH WEST ELEVATION 1:100 | ±0.00 ground, GF +1.00 (printed 100 plinth), 450 / 420 storey heights, 50 parapet, opening widths 155 / 99 / 269, **curved glazing 430 high + 20 head over 269 wide**, arched window heads, dome rises 172 and 215 | B01, B11 curved glazing, B05 |
| E2 | same sheet, lower right | cut through a sunken element beside the curved glazing: **115 pit + 70 step** below the +0.15 deck | B04 pool depth candidate (to be cross-checked with the p.3 pool outline) |
| E3 | p.6 SOUTH EAST ELEVATION | **dome span 441 / rise 215** on the tower roof (matches the p.7 dome detail 4.42 / 1.90 within the N.T.S. tolerance); slot window heights 200 / 230 / 250 / 200 + 170 arch; window 215 × 140; annex +0.30 / roof +4.30 / parapet 50; total 1440 | B05, B11 |
| E4 | p.1 SOUTH WEST and p.3 NORTH EAST ELEVATIONS | level chains only (100 / 550 / 870 / 1440 / 420 / 130 / 50); openings **drawn to scale but not dimensioned** | B11 by scaled measurement (RASTER_DERIVED) |
| E5 | p.4 SECTION A-A | full stair section GF +1.00 → 1F +5.50 → 2F +9.70 → roof +13.90; **treads drawn and countable**; external steps +0.30 / +0.15 / ±0.00 | B03 riser count and height |
| E6 | p.5 SECTION B-B | **two domes on the 2F terrace (+9.70) and one on the tower roof (+13.90)**; annex section 400 + 480; courtyard +0.15 between annex and house; 535 opening | B05 (3 bound domes), B14 courtyard |
| E7 | p.6 (B6) FENCE PLAN / ELEVATION / SECTION 1:100 | fence **2.15 m + 0.50 m = 2.65 m**; front run segments 580 / 250 / 81 / 195 / 115 / 195 / 83 with gates | B14 boundary wall (front run printed; other runs from the GF site plan) |
| E8 | P7757 arch PDF 01-06 p.1–2 — AREA CALCULATION | the architect's gross floor areas per storey by rectangle decomposition (GF / 1F / 2F totals and deductions) | independent Route B for slab / footprint area (gross) |
| E9 | ST7757 p.8 note 6 | f'c ≥ **300 kg/cm²** reinforced, **150 kg/cm²** plain (unless the engineer raises some beams / columns) | brief §8 concrete grade |
| E10 | ST7757 p.8 note 13 | **sulfate- and salt-resisting cement** for plain and reinforced concrete in contact with soil or groundwater | brief §8 cement type (SOURCE) |
| E11 | ST7757 p.8 notes 9, 18, 21, 22 | laps 70Ø / 40Ø; slab 16 cm unless stated; side bars 2 / 3 / 4 Ø12 in beams deeper than 60 cm "by beam width"; cover 2.5 / 7 cm | rebar (already used) |
| E12 | ST7757.dxf | **119 slab reinforcement annotations** on `S-TEXT-SLAB` (5Ø10/m, 8Ø16/m, nØd/Top) **and the bars themselves drawn**: 213 LINE + 14 LWPOLYLINE on `S-REIN-SLAB`, 12 corner bars on `S-REIN-CORNER` | B09: a binding problem, not a missing source |
| E13 | P7757.dxf | **388 DIMENSION entities** (366 linear chains: 750 / 3500 / 1150 / 200 wall …) | independent Route B for room areas (dimension-chain reconstruction) |

These are raster readings by eye for the recommendation only.

In implementation each value becomes a RASTER_DERIVED claim carrying:
- the sheet sha256 and the pixel box;
- the printed text;
- the scale check, which compares the pixel length of at least two printed dimensions on the same sheet and must agree
  within tolerance.

Nothing above is used as a quantity until that pass exists.

---

## 3. Blocker classification (all 15 groups, all 32 BLOCKED lines)

Release classes used below:
- **Technical (T):** MEASURED / DERIVED / SOURCE_RULE / OWNER_PROJECT_FACT / URBAN_STANDARD / PARTIAL / BLOCKED.
- **Commercial (C):** the T classes plus PROVISIONAL_SOURCE_DERIVED / PROVISIONAL_GEOMETRIC_INFERENCE / PROVISIONAL_CODE_METHOD /
  PROVISIONAL_URBAN_FALLBACK / PROVISIONAL_OWNER_METHOD / BUDGET_ESTIMATE.
- **Confidence:** H (proved by two routes), M (one route + consistency check), L (method only).

| ID | Lines (qty affected) | Why V3a stopped | Class (brief §0) | Resolution routes (ladder order) | Independent check? | Raster? | Urban method? | Code? | Commercial estimate? | Expected after V3b |
|---|---|---|---|---|---|---|---|---|---|---|
| **B01** exterior ground-beam depth | C-GB-EXT: 28 spans, 110.30 m measured, volume 0 | "follow arch." treated as missing | **SOURCE_RESOLVABLE** + DOCUMENT_EXTRACTION_DEFECT | E1 / E3 / E6: plinth ±0.00 → +1.00 printed on all elevations and sections; beam = plinth face from GB bottom to slab soffit; GB bottom from the p.13 interior-GB rule (same founding band) | elevation level chain vs section level chain (two sheets) | yes (printed) | — | — | yes | T: DERIVED (depth = 1.00 + below-ground part per the interior GB section), M; residual: below-grade part if the sections disagree |
| **B02** necks / founding level | C-NECK, R-COL-FDN | founding level "left to site and soil" (note 12) | **OWNER_INPUT_NEEDED** for technical; **COMMERCIAL_ESTIMATE_POSSIBLE** | note 12 really leaves it to site; sections show only ±0.00 and +1.00; commercial: neck height = founding depth − footing t − ground beam, with the founding depth as a stated provisional parameter (e.g. 1.50 m below ±0.00; owner editable) | count × section × provisional height vs total column stack | no | yes (owner method) | — | yes, with range ±0.5 m | T: BLOCKED (true source gap); C: PROVISIONAL_OWNER_METHOD, L–M, range shown |
| **B03** stairs | C-STAIR, F-STAIR, S-RAIL | riser count "not proved"; waist "THICK" | **SOURCE_RESOLVABLE** (risers) + **CODE_STANDARD_CAN_RESOLVE** / OWNER (waist) | E5: count treads per flight on A-A, divide floor-to-floor (4.50 / 4.20) → riser height, check 2R + G with going 30 (p.16); waist: note 18 "16 cm unless stated" is the governing slab default → SOURCE_RULE candidate; railing = flight slope length + landing edges | riser count from section vs plan tread lines in P7757.dxf | yes (count) | — | 2R + G comfort band as a sanity check only | yes | T: DERIVED (risers, treads, marble m², nosing lm, railing lm); waist SOURCE_RULE (note 18) flagged for confirmation |
| **B04** pool | C-POOL | depths "as per arch." | **SOURCE_RESOLVABLE** (candidate) | E2 section (115 + 70) + p.3 pool outline (plan) + p.7 thicknesses (walls 20, base 40, blinding 10) | plan outline area × depth vs elevation cut width | yes | — | — | yes | T: DERIVED if E2 is proved to be the pool cut (location match on plan); else C: PROVISIONAL_SOURCE_DERIVED, M |
| **B05** dome | C-DOME 2.668 m³ REVIEW (one generic dome) | detail N.T.S., "not bound to a plan" | **SOURCE_RESOLVABLE** — scope filter BOUND_PROJECT_ELEMENT | E3 / E6: three domes drawn (tower roof span 441 / rise 215; two terrace domes); count and spans from the 2F / roof plan circles in P7757.dxf; shell 10 cm (p.7), Ø12 / 15 cm (p.7) | elevation span vs plan circle diameter | yes | — | — | yes | T: DERIVED (3 domes: concrete, rebar, plaster / paint, WP); M → H after the plan match |
| **B06** F / F10 | C-FTG: 2 of 27 footings | genuine drawing conflict (OQ3-S1) | **OWNER_INPUT_NEEDED** (technical); COMMERCIAL_ESTIMATE_POSSIBLE | keep both candidates; commercial: the larger of the two definitions (conservative) with the alternative shown | — | no | yes | — | yes (bounded by the two definitions) | T: BLOCKED; C: PROVISIONAL_SOURCE_DERIVED (range = the two definitions), H on the range |
| **B07** beam / column binding residue | C-BEAM 18 + 7 + 0 blocked occurrences; C-COL 5 + 3 + 1 blocked; R-BEAM-*-BLK (24 sets) | tag binding tolerance, several outlines, band-type conflict | **SEMANTIC_BINDING_DEFECT** | generic binder V2: tag-to-band by leader / containment / collinearity scoring; candidates kept and reconciled; residue rendered on one image sheet | occurrence count from tags vs count from drawn bands; schedule section × CAD length | no | — | — | yes (unbound band × nearest-family section, labelled) | T: DERIVED for bound; residue C: PROVISIONAL_GEOMETRIC_INFERENCE, M |
| **B08** hooks / bends / stirrup closing | 6.602 t of partial sets (beams 204, columns 74, ground beams 124, lintels 59 sets) | no bending detail; OD-V3-3 forbids invention | **CODE_STANDARD_CAN_RESOLVE** (needs the governing code named) | project detail (none) > project notes (laps / cover only) > **governing detailing code** (the notes use ACI-style kg/cm² and 70Ø / 40Ø development; Kuwait practice is ACI 318 — needs owner confirmation) > Urban fallback | net vs procurement vs BBS cutting optimisation (§9) | — | Urban fallback possible | **yes** (ACI 318 standard hooks: 90° and 180° bar hooks, 135° seismic stirrup hooks, by db) | yes | T: SOURCE_RULE + CODE_METHOD once the code is confirmed; C: PROVISIONAL_CODE_METHOD until then |
| **B09** slab reinforcement | R-SLAB-ALL (all suspended slabs; largest missing rebar population) | annotations not bound to extents | **SEMANTIC_BINDING_DEFECT** (+ GEOMETRY_ENGINE_DEFECT) | E12: bind each `S-TEXT-SLAB` annotation to its drawn bar on `S-REIN-SLAB` (nearest bar line whose direction and extent fit the text, never nearest text alone), then the bar's span to the slab panel polygon; bottom mesh "5Ø10/m E.W." distributed over the panel; top bars over supports from the drawn bar length; corner bars from `S-REIN-CORNER` | panel area × mesh density (Route B) vs bar-by-bar sum (Route A) | — | — | anchorage beyond supports from laps / code | yes | T: DERIVED for bound panels; ambiguous panels C: PROVISIONAL_GEOMETRIC_INFERENCE |
| **B10** annex ground-slab zone 2 | C-GSLAB-ZONE-2 (and its mesh, blinding) | exterior beam drawn on another layer → zone not closed | **GEOMETRY_ENGINE_DEFECT** | close the zone across layers (structural element role, not layer name); Route B: annex footprint from the arch plan (+0.30 block) minus beam bands | arch footprint vs structural zone | — | — | — | yes | T: DERIVED, H |
| **B11** opening heights | O-*-A (7 area lines), B-OVER-OPEN, P-REVEAL, O-CURVED-A | "no schedule; SW / NE raster" | **DOCUMENT_EXTRACTION_DEFECT** + SOURCE_RESOLVABLE | printed dims on NW / SE (E1, E3); scaled heights on SW / NE (E4) and the sections (E5, E6) with per-sheet scale calibration; plan width from DXF must match the raster width (cross-sheet check) | plan width (DXF) vs raster width at calibrated scale; same opening in two views where visible | **yes** | Urban fallback heights only as last resort (labelled) | — | yes | T: RASTER_DERIVED (printed = H, scaled = M); C: complete; curved glazing 4.30 printed → H |
| **B12** room soffit under unbound beams (paint) | P-PA-GF-Z04 (155.7 m² zone, 112.3 m wall blocked), P-PA-GF-R12, P-PA-1F-Z06 | band type conflict over the room | **SEMANTIC_BINDING_DEFECT** (follows B07) | after B07, take the controlling soffit per wall piece (finish_height_v3 already splits faces); residue: the deepest **bound** beam of the same span family as a labelled inference | paint height from section A-A / B-B raster (finished ceiling) vs structural soffit | yes (sections) | yes (OD-V3-1 build-up fallback already labelled) | — | yes | T: DERIVED for bound; residue C: PROVISIONAL_GEOMETRIC_INFERENCE |
| **B13** finish extras | REVIEW: spatter dash 1,922.9 m² (= all plastered walls), corner beads 15.7 lm (suspiciously low), cornice 511.0 lm | coverage rule not decided (OD-V3-4) | **PROJECT_METHOD_AVAILABLE** (owner decides scope once) | owner scope rule per extra (yes / no + where); corner-bead geometry needs a fix (external corners of plastered faces incl. openings once B11 releases reveals) | bead count from wall-face convex corners vs opening reveal edges | — | yes | — | yes | C: PROVISIONAL_OWNER_METHOD per extra; corner-bead engine fix (GEOMETRY_ENGINE_DEFECT) |
| **B14** facades / boundary wall / courtyard | P-EXT, B-BWALL, F-COURT, C-BWALL | "not measured this round" | **SOURCE_RESOLVABLE** (+ DOCUMENT_EXTRACTION) | facades: each elevation outline × calibrated scale, minus openings (B11), per facade, cross-checked with the plan perimeter × level chain; boundary wall: E7 height 2.65 + run from the GF site plan (plot line in P7757.dxf) + p.14 typical foundation; courtyard: plan region between annex and house at +0.15 (E6) | facade area by elevation vs plan perimeter × height | yes | — | — | yes | T: DERIVED / RASTER_DERIVED (M); boundary runs not drawn on the fence sheet: from the site plan (M) |
| **B15** lift shaft | 3.24 m² × 3 storeys excluded from finishes | repeated 1.8 × 1.8 m site; p.14 typical lift | **POSSIBLE_PROJECT_ELEMENT** → OWNER confirmation, but it does not block quantities | scope filter: publish the shaft as POSSIBLE_PROJECT_ELEMENT; finishes excluded with the area shown; lift pit / walls only if confirmed | — | sections show no pit (no basement) | — | — | yes (both scenarios shown) | C: OWNER_CONFIRMATION_REQUIRED, quantity impact shown both ways |

**Summary of the ladder outcome I expect:**

| Outcome | Blockers |
|---|---|
| Solvable from source, technically | B01, B03 (risers), B04 (if the cut is proved), B05, B09, B10, B11, B14 |
| Solvable by a generic engine fix | B07, B09, B10, B12, the corner-bead part of B13 |
| Needs a code / method decision once | B08 (governing detailing code), B13 (extras scope), B03 waist confirmation |
| True technical gaps | B02 founding level, B06 F / F10 |

Both true technical gaps still get a labelled commercial quantity with a range. **TRUE_BLOCKER (no commercial estimate
possible): none that I can see today.**

---

## 4. Architecture: TECHNICAL_QTO ≠ COMMERCIAL_BOQ

**One line model, two release views.** Every BOQ line keeps its technical status and gains a commercial status:
- `release.technical` = {class, qty | null, reason};
- `release.commercial` = {class, qty, method, assumption, source / rule, confidence, range_low, range_high}.

Rules (enforced by tests):
1. TECHNICAL_QTO totals only take technical classes. PARTIAL never enters the technical total; it is reported separately,
   as today.
2. A COMMERCIAL_BOQ total may take PROVISIONAL_*; every such cell is visibly labelled in the workbook (amber pattern + class
   text). The total row says how much of it is provisional.
3. A provisional value can never be written into the technical column. A provisional value equal to a measured value is
   still labelled provisional until a technical route proves it.
4. BUDGET_ESTIMATE is allowed only where no geometric or source route exists. It carries a range and is never mixed into a
   measured subtotal.

Registers:
- `TECHNICAL_QTO_REGISTER.json`;
- `COMMERCIAL_BOQ_REGISTER.json` (same line ids, two views);
- `BLOCKER_RESOLUTION_REGISTER.json` (one row per blocker × route attempted: ROUTE / RESULT / EVIDENCE / QUANTITY_RELEASED /
  RELEASE_CLASS / CONFIDENCE / REMAINING_RISK, in the brief's 14-step order).

---

## 5. Dual independent measurement

Route B must not call the Route A engine.

| Element | Route A (primary) | Route B (check) |
|---|---|---|
| Room floor / ceiling | V3 topology polygon (DXF) | dimension-chain reconstruction from the 388 DXF DIMENSION entities (E13), with orthogonal rectangle decomposition of the clear dimensions; curved rooms: arc-segment area from the arc entity parameters (not the polygon) |
| Slab concrete | closed slab region × t | architect's gross storey area (E8) − voids − shafts − openings measured separately, then × t |
| Footings / columns / beams | CAD occurrence × schedule section | independent tag count × schedule × printed dimensions (no CAD geometry) |
| Blockwork / plaster | wall bands × height | wall-centre length from dimension chains × height from the section level chain |
| Openings | DXF plan width × raster height | the same opening's width measured on the raster elevation at calibrated scale |
| Rebar | bar-by-bar (count × cut length × kg/m) | population density check (panel area × mesh per m; beam length × bars per section) |

Stored fields:
- PRIMARY_QTY, PRIMARY_METHOD;
- CHECK_QTY, CHECK_METHOD;
- ABS_DIFF, DIFF_PCT;
- RECON_STATUS ∈ {RECONCILED, WITHIN_TOLERANCE, INVESTIGATE, CHECK_UNAVAILABLE};
- FINAL_QTY = PRIMARY_QTY.

FINAL_QTY is never the average and never the value nearer a benchmark. A disagreement above tolerance opens a REMEASURE case;
it does not change the number.

Proposed QA tolerances (configurable, a trigger only):

| Element | Tolerance |
|---|---|
| Rooms | 0.5 % or 0.05 m² |
| Slabs | 1 % |
| Structural members | 2 % |
| Openings | 3 % (raster) |
| Rebar density check | 10 % |

---

## 6. Geometry first, material second

- `05_FLOORING_PORCELAIN.xlsx` becomes **`05_FLOORING.xlsx`**:
  - one row per room;
  - columns ROOM, GEOMETRIC AREA A, INDEPENDENT AREA B, RECONCILED NET AREA, FINISH TYPE (BY_SPEC / PENDING), MATERIAL
    AUTHORITY, WASTE, PROCUREMENT.
- The current dry-room default (`URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1`) moves to the material column only. It never decides
  or limits the area.
- Wet / service rooms keep their classification (tile, no skirting) subject to project override.
- **Ceilings:**
  - ceiling geometry is 100 % (V3a already releases every ceiling area);
  - the ceiling-material question no longer appears as a blocker;
  - Q-F2 is dropped from the owner list (material stays BY_SPEC).

---

## 7. Waste / procurement layer

**Columns on every applicable row:** NET QTY, UNIT, WASTE METHOD, WASTE %, WASTE QTY, PROCUREMENT QTY.
- The rule library already says this: UP-GEN-002, "MEASURED_NET | WASTE | PROCUREMENT | CONTRACTOR_COMMERCIAL, never one
  number".
- The net / technical BOQ never changes.

**Hierarchy:** ITEM OVERRIDE > TRADE / MATERIAL RULE > PROJECT RULE > **PENDING**. With PENDING, waste %, waste qty and
procurement qty are **blank, not zero**. The inputs live in a yellow WASTE_INPUTS sheet (project, trade and item levels)
that the formulas read.

| Trade | Waste method |
|---|---|
| Flooring / tile / marble | layout-based when tile size is known (no tile size in source → PENDING); otherwise the owner % |
| Rebar | BBS cutting optimisation: bar marks → cut lengths (incl. hooks / bends / laps) → first-fit-decreasing nesting into 12 m stock with offcut reuse → PURCHASE weight, OFFCUT, EFFECTIVE WASTE %, PROCUREMENT weight. A plain % is used only where cutting is impossible, labelled. |
| Concrete | technical = net geometric volume; ORDER / POUR ALLOWANCE is a separate column (owner / supplier rule), never added to the technical volume |
| Blocks, plaster, paint, WP | net stays the BOQ; procurement separate; % from owner rules only |

**Stock length vs laps.** 12 m stock length (procurement) is kept apart from the 70Ø / 40Ø structural laps (source). A lap
is counted where the design needs continuity *or* where a bar longer than 12 m must be spliced. The stock length never
defines the lap length.

---

## 8. Blinding — full-footprint method (owner construction method)

**Two methods, published side by side.**

**SOURCE_DETAIL_LOCAL_BLINDING** (today):
- 15.213 m³ under footings + 4.425 m³ under interior ground beams;
- p.13: 10 cm, 10 cm beyond the member.

**OWNER_EXECUTION_FULL_FOOTPRINT_BLINDING:**
- applicable footprint × 0.10 m;
- footprint = outer face of the perimeter ground beams + 0.10 m (the p.13 "10 cm beyond"), for the main house and, separately,
  the annex;
- the pool is excluded and has its own blinding (p.7).

**Do not double count.** A full-footprint pour at the founding level *replaces* the local pads only if both are at the same
level. The footings sit lower than the ground beams, so the physically consistent version is:
- full footprint at ground-beam bottom level, plus
- local pads under footings only where the footing bottom is below that level (a step, not a second layer under the same
  area).

I will compute both readings. Only one enters the commercial total: OWNER_EXECUTION once the owner confirms, recorded as
**PROJECT_ONLY** in the new `OWNER_METHOD_REGISTER` (never auto-globalised).

---

## 9. Concrete grade / cement (brief §8) — resolved from source

| Field | Value |
|---|---|
| CONCRETE_STRENGTH (reinforced) | f'c ≥ 300 kg/cm² (note 6) |
| CONCRETE_STRENGTH (plain) | 150 kg/cm² (note 6) |
| CEMENT_TYPE | sulfate- and salt-resisting for all concrete against soil / groundwater (note 13) |
| SOIL_CONTACT | per element (footings, necks, ground beams, ground slab, pool, boundary-wall footings) |
| EXPOSURE_CLASS / SULFATE_REQUIREMENT | from note 13 (no numeric class printed → recorded as "SRC required, class not printed") |

No soil-specific strength is invented: note 6 gives one strength for all reinforced concrete.

---

## 10. Rebar completion campaign (highest priority)

### 10.1 REBAR_POPULATION_REGISTER

Columns: EXPECTED / DEFINITIONS FOUND / OCCURRENCES BOUND / SETS COMPUTABLE / PARTIAL / MISSING / WEIGHT COVERAGE.
No project total is declared until every population row is accounted for.

| Population | V3a state | V3b route |
|---|---|---|
| Footings | 48 computed, 4 blocked (boxed bar shape) | shape from the footing detail; F / F10 per B06 |
| Straps | strap bands measured, bars not | schedule / p.13 typical |
| Necks / starters | blocked | B02 provisional height |
| Ground beams | 124 partial (interior) | B08 hooks + B01 exterior |
| Ground slab | 2 computed (zone 1) | zone 2 via B10 |
| GF / 1F / 2F columns | 74 computed + 74 partial | B07 + B08 |
| GF / 1F / 2F beams | 204 partial + 24 blocked | B07 + B08 + side bars (note 21) |
| GF / 1F / 2F slabs | not bound | **B09 slab binding engine** |
| Lintels | 118 computed + 59 partial | B08 |
| Stairs | absent | p.16 stair rebar per m + B03 geometry |
| Pool | absent | p.7 + B04 |
| Domes | absent | p.7 Ø12 / 15 cm + B05 (3 domes) |
| Boundary wall | absent | p.14 typical + B14 |
| Lift | possible element | B15 scenario only |

### 10.2 Generic slab reinforcement binding (B09)

1. **Parse** each annotation: count or spacing, diameter, "/m", Top / Bottom, E.W., corner.
2. **Associate** the text with the drawn bar on the reinforcement layer role (not a layer name): the nearest bar line whose
   direction is parallel to the text baseline and whose extent contains the text projection. Leaders and wipeouts count as
   evidence. Competing candidates are kept and scored, never resolved by nearest text alone.
3. **Bind** the bar to its slab panel polygon (V3 slab regions, already closed per storey) and, for top bars, to the
   supporting beam band.
4. **Compute** distribution extent ⊥ bar direction, bar length (drawn length, or panel span + anchorage), bar count
   (extent / spacing + 1), and weight.
5. **Route B check:** panel area × mesh density.
6. Ambiguous panels → candidates + reconciliation case.

### 10.3 Beams / columns

- **Side bars (note 21):** "2 / 3 / 4 Ø12 by beam width" for D > 60 cm.
  - Search the beam schedule and sections for any section that prints side bars. If the width families in the schedule
    are exactly three, the ascending mapping is deterministic → SOURCE_RULE candidate. Otherwise it is
    PROVISIONAL_SOURCE_DERIVED with the 2–4 bar range.
- **Hooks / bends / stirrup closing:** hierarchy = project detail > project notes > governing code > Urban fallback >
  BLOCKED_DETAILING.
  - The project prints no bending detail.
  - The governing code is not named on the drawings → **one owner decision**: confirm ACI 318 (my recommendation for Kuwait
    MPW practice and these notes) as the detailing code for Alsenan.
  - With that, standard hooks and stirrup closing come from the code tables by db, as PROVISIONAL_CODE_METHOD until
    confirmed and CODE_METHOD after.
  - No internet BBS constants.
- **Laps:** 70Ø tension / 40Ø compression (source, governs Alsenan). Where the design is silent on tension vs compression
  zone, beams bottom / top and slab bars use 70Ø (conservative) and column verticals use 40Ø; the assumption is stated.

### 10.4 Donor research

`v-Zak/bar-bending-scheduler` (DXF reinforcement labels → CSV) is **not yet inspected in this session**.
- It will be reviewed read-only as RESEARCH_ONLY / CLEAN_REIMPLEMENT (no declared licence → no code copied).
- Expected lessons: label grammar, bar-mark inventory, CSV reconciliation.
- The existing donors (AutoCAD-MCP ×2, OpenTakeoff, external-engine lab) give the oracle and measurement lessons already
  recorded in `DONOR_REUSE_REGISTER`.
- No runtime dependency is added.

---

## 11. Raster / PDF elevation lane (B01, B04, B05, B11, B14)

**Evidence class.** `RASTER_DERIVED` with two grades:
- **PRINTED:** the dimension text is read and its dimension line is located → H;
- **SCALED:** a measurement at a calibrated scale → M.

**Scale calibration per sheet.** At least two printed dimensions on the same sheet are measured in pixels. Their ratio must
agree within 1 %; otherwise the sheet is not scalable and only printed values are used.

**Cross-sheet checks:**
- the plan opening width (DXF, exact) must equal the elevation width at the calibrated scale within the tolerance before any
  height from that sheet is accepted;
- the level chains must agree across sheets (100 / 550 / 870 / 1440 appear on four sheets).

**Mechanics.**
- Line detection on the binarised raster finds dimension lines, level markers and opening rectangles.
- The printed numbers are read by visual reading, then **verified geometrically**: the dimension's pixel length × scale must
  equal the printed value. OCR alone is never trusted.

**Output.** Per opening: ID, FLOOR, ROOM, FUNCTION, MATERIAL (BY_SPEC), WIDTH (DXF), HEIGHT (raster, grade), AREA, SOURCE,
CHECK ROUTE, STATUS.

**Height hierarchy:** explicit dimension > schedule (none) > section / elevation printed > raster scaled > owner fact >
versioned Urban fallback > commercial estimate.

---

## 12. Finish corrections

- **Wall tile.** TECHNICAL_NET_WALL_TILE = gross eligible wall − full openings + applicable reveals. This is rule
  UP-CER-005 "GROSS_MINUS_OPENINGS" plus the reveal rule URBAN-REVEAL-FINISH-METHOD; V3a published the gross. A separate
  COMMERCIAL_PAYABLE_WALL_TILE basis (gross, if that is how the contractor is paid) is a second, labelled column; the two
  are never mixed. This needs B11 (opening heights).
- **Plaster / paint.** The same pair: TECHNICAL_NET and COMMERCIAL_PAYABLE.
- **Waterproofing.** Separate components per wet room and roof:
  - FLOOR MEMBRANE m²;
  - UPTURN PATH lm;
  - UPTURN HEIGHT m;
  - DERIVED UPTURN m²;
  - TOTAL m² (informational).

  The upturn path is published as its own engine line; it is no longer recovered from formula text. The upturn path is
  net of door openings (UP-GEN-003).

---

## 13. Owner-question cleanup (rebuilt register)

| Question | V3b | Reason |
|---|---|---|
| Q-F2 ceiling material | **dropped** | material never blocks area |
| Q-O1 opening heights | **dropped** | raster lane (B11) |
| Q-S3 stair waist / risers | reduced to "confirm 16 cm waist (note 18)" | risers from section A-A |
| Q-S4 pool depths | reduced to "confirm the cut on the NW elevation is the pool" if the plan match fails | E2 |
| Q-S5 dome | **dropped** | 3 domes bound (E3, E6) |
| Q-S1 exterior GB depth | **dropped** if the section chain proves it | E1 / E6 |
| Q-A2 GF open zone | kept only if it changes a quantity (it does not: the zone is measured as one open space) → **dropped** | — |
| Q-S2 founding level | kept (technical) | commercial estimate meanwhile |
| Q-S6 F / F10 | kept (technical) | commercial range meanwhile |
| Q-S7 bar bending | becomes "confirm ACI 318 as the detailing code" | — |
| Q-A1 lift shaft | kept as scope confirmation | both scenarios shown |
| Q-F1 extras | kept as a one-time scope decision | — |

---

## 14. Expected-scope engine (names only, from the B1 labels)

`EXPECTED_SCOPE_REGISTER.json` lists every item a competent QS takeoff of this villa carries and asks "did Urban produce
it?":
- **Plaster:** internal plaster, external plaster, plaster corners, spatter dash (wet rooms / طرطشة), spatter dash under
  skirting.
- **Paint:** internal, decor.
- **Floors and skirting:** floor tile; yard flooring and yard skirting; marble stairs (m² and nosing / riser count) and stair
  skirting.
- **Pool:** pool floor and wall tile.
- **Waterproofing:** wet-room floor + upturn lm; roof floor + upturn lm.
- **Ceilings:** gypsum dry / wet; cornice dry / wet.
- **Railings:** internal railing.
- **Blockwork:** external / 150 / 200.
- **Concrete:**
  - blinding;
  - footings + straps + perimeter;
  - ground slab + beams;
  - necks + columns + walls;
  - beams;
  - slabs;
  - stairs + domes;
  - pool.
- **Rebar and openings:** rebar total; aluminium doors / windows.

No quantity or price from those documents is read or used. Benchmark values stay sealed until the V3b freeze.

**Scope filter (brief §23).** Each expected item is one of:
- BOUND_PROJECT_ELEMENT: domes, pool, boundary wall, courtyard;
- POSSIBLE_PROJECT_ELEMENT: lift;
- TYPICAL_DETAIL_ONLY: e.g. the p.14 lift detail if no lift is confirmed;
- NOT_IN_SCOPE / NOT_IN_SOURCE: basement — sections show none, and the lift detail says "without basement".

Only confirmed / expected scope enters the completeness denominator.

---

## 15. Mismatch investigation (after the V3b freeze)

`MISMATCH_REGISTER.json` creates one MISMATCH_CASE per comparison beyond tolerance, against:
- the freelancer;
- the web app;
- Route B.

Each case carries:
- a classification: SCOPE / UNIT / MATERIAL / REVISION / GEOMETRY / OPENING DEDUCTION / HEIGHT / MISSING POPULATION /
  PROCUREMENT vs NET / PAYABLE vs TECHNICAL / BENCHMARK ERROR / URBAN ENGINE ERROR / UNRESOLVED;
- the evidence for each side;
- what to inspect next.

Units are normalised first (UNIT_CONTROL, already built). No variance is reported without a classification.

---

## 16. Manual teaching mode

`OWNER_METHOD_REGISTER.json` holds one record per owner answer:
- RULE / FACT, VALUE, SCOPE;
- SOURCE = OWNER, DATE, PROJECT;
- PROMOTION_CLASS ∈ {PROJECT_ONLY, URBAN_STANDARD_CANDIDATE, URBAN_STANDARD_APPROVED}.

Behaviour:
- Seeded with the V3 owner decisions (OD-V3-1..10) and the new full-footprint blinding fact (PROJECT_ONLY).
- An answer is never globalised automatically: promotion needs an explicit owner statement.
- The existing `data/registry/URBAN_OWNER_METHOD_RULES.json` becomes the store for approved standards.

---

## 17. Workbooks and reports

- **Detailed rows** gain:
  - PRIMARY METHOD / QTY;
  - CHECK METHOD / QTY;
  - DIFF / DIFF %, RECON STATUS;
  - FINAL NET QTY;
  - UNIT;
  - WASTE METHOD / % / QTY, PROCUREMENT QTY;
  - MATERIAL / TYPE;
  - AUTHORITY, CONFIDENCE, STATUS, NOTE.
- **The two measurements are never shown as two payable quantities.**
- **Flooring:** one row per room.
- **Master summary:** two blocks.
  - A — NET / TECHNICAL (technical classes only).
  - B — PROCUREMENT / COMMERCIAL (net + waste + procurement, with provisional share).
  - Units as the unit addendum; never a cross-unit total.
- **Reports:** `URBAN_BOQ_COMMERCIAL_REPORT.pdf` and `URBAN_QTO_TECHNICAL_AUDIT.pdf`.
- **Release label:** **V3b FULL-BOQ CANDIDATE**, not FINAL.

---

## 18. Coverage targets — what I expect, honestly

Technical and commercial coverage are reported separately, per the brief.

| Trade | Target (brief) | Expected technical | Expected commercial | Main risk |
|---|---|---|---|---|
| Concrete | ≥ 95 % | ~85–90 % (necks, F / F10 remain technical gaps) | ~100 % | founding level is a range |
| Rebar | ≥ 95 % | depends on B09 + the code decision; ~80–90 % | ~100 % with code-method hooks | slab binding ambiguity |
| Blockwork | ≥ 95 % | ~95 % | 100 % | boundary-wall runs not on the fence sheet |
| Flooring | ≥ 98 % | ~98 % | 100 % | stair finish depends on B03 |
| Ceiling geometry | 100 % | 100 % (already) | 100 % | — |
| Wall tile / WP | ≥ 98 % | ~98 % after net-of-openings | 100 % | opening heights (B11) |
| Openings | ≥ 95 % | ~90 % (raster scaled = M) | 100 % | SW / NE scaled heights |
| Stairs | ≥ 95 % | ~90 % (waist SOURCE_RULE pending confirmation) | 100 % | waist |

Coverage is not permission to fabricate. A provisional cell always shows its method and range.

---

## 19. Work order (one round, gated freezes)

1. **Evidence pass** (no quantities yet):
   - raster lane with scale calibration (§11);
   - claims register for E1–E13;
   - synthetic tests for scale calibration and the printed-vs-scaled grades.
2. **Generic engines, each with synthetic tests written first and a Qortuba rerun:**
   - **2a** Slab rebar binding (B09). It is the largest weight population, so it comes first.
   - **2b** Beam / column binder V2 (B07 → B12).
   - **2c** Cross-layer zone closure (B10).
   - **2d** Opening schedule from raster (B11), then net wall tile / plaster / paint with reveals (§12), and the waterproofing
     component split.
   - **2e** Stair geometry from section (B03).
   - **2f** Domes, pool, boundary wall, courtyard, facades (B04, B05, B14).
   - **2g** Hooks / bends / closing by the confirmed code (B08); the BBS cutting optimiser (§7).
   - **2h** Route B engines: dimension chains, the area-calculation sheet, independent counts (§5).
3. **Two-layer release model**, waste / procurement layer, blinding two methods, owner method register, expected-scope
   register.
4. **Freeze V3b:**
   - registers built twice, byte-identical;
   - Qortuba shadow (RC1_REFERENCE untouched);
   - then the post-freeze mismatch engine.
5. **Reporting:**
   - updated 11 workbooks (05_FLOORING renamed);
   - both PDFs;
   - readback + LibreOffice recalc, built twice;
   - one full suite from the final commit;
   - package.

**Risk.** Steps 1, 2a and 2d are the largest; this is several times the size of V3a. If the raster lane does not reach the
calibration bar on a sheet, that sheet's heights stay PROVISIONAL (commercial) instead of RASTER_DERIVED (technical). The
round does not stop.

---

## 20. Where I disagree / caution

1. **"Ultimately more accurate than a freelancer"** is reachable for geometry: rooms, slabs, openings and concrete, because
   two independent routes plus exact CAD beat hand takeoff. It is **not** reachable for rebar until the project's bending
   detailing basis is fixed: a hook-length standard changes every bar.
2. **Commercial provisional quantities will move.** A BUDGET_ESTIMATE row must never feed a procurement order. I propose
   the procurement block only takes MEASURED / DERIVED / RECONCILED / CODE_METHOD rows plus explicitly owner-approved
   PROVISIONAL rows.
3. **Full-footprint blinding.** If the footprint pour is executed at ground-beam bottom and footings are lower, the
   physically honest quantity is "footprint + footing steps", not "footprint only" and not "footprint + all local pads".
   I will model it that way unless you tell me the site practice differs.
4. **The 44.19 t diagnostic.** A completed engine may still land well below it. Kuwait villa takeoffs often use kg/m³
   ratios, which OD-V3-3 rejects. If so, the mismatch engine will classify it (MISSING POPULATION vs METHOD), not chase it.

---

## 21. Decisions I need from you (method only — no drawing can answer these)

1. **Governing detailing code for hooks, bends and stirrup closing:** confirm **ACI 318** for Alsenan (PROJECT_ONLY first).
2. **Waste rules:** give % per trade (flooring, wall tile, blocks, plaster, paint), or leave them PENDING (blank) this
   round. Rebar waste will come from the cutting optimiser regardless.
3. **Blinding:**
   - confirm the full-footprint method for Alsenan, at ground-beam bottom with footing steps, 0.10 m;
   - say whether it applies to the annex.
4. **Commercial provisional policy:** may PROVISIONAL_* rows enter the commercial total (labelled, with ranges), and may
   owner-approved provisional rows enter the procurement block?
5. **Payable basis:** is the contractor paid on gross or net for wall tile, plaster and paint? This sets the
   COMMERCIAL_PAYABLE column; the technical column is net regardless.
6. **Extras scope (B13):** measure corner beads, spatter dash (where), cornice (which rooms), reveals — yes / no per item.

Still open but **not blocking the round** (each gets a labelled commercial quantity meanwhile): founding level (B02),
F / F10 (B06), lift shaft confirmation (B15), and the waist confirmation (B03).
