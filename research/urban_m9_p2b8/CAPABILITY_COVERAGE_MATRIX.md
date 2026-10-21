# Capability coverage matrix (Phase 2B-8)

**Method:** ARCH_TAKEOFF_V2.7.1 (opt-in). The frozen methods V1 – V2.7 are unchanged.

**Columns**
- **"Benchmark"** is the support status the sealed protocol URBAN_BLIND_V2 gives the category. An UNSUPPORTED metric is reported, never scored as zero.
- **"Evidence"** says what a quantity has been checked against: hand truth on synthetic plans, the independent reader (`tools/indep_reader.py`) on the reference plan, or nothing yet.

**No category has an accuracy figure.** There is one real plan and no blind evaluation (`SECOND_VILLA_READINESS.md`).

## Reference plan, Mode A: line states (V2.7.1, 487 lines, aggregates)

| Release category | Lines | Of which |
|---|---|---|
| CONFIRMED (a quantity) | 296 | 196 SOURCE_DERIVED, **100 PROVISIONAL** |
| HELD | 191 | 162 requires drawing evidence, 20 requires an owner decision, 9 engineering review |
| EXCLUDED | 0 | (Mode U: 28 not applicable with evidence) |
| CONDITIONAL scenario sets | 4 | 3 review spaces (WET / DRY), 1 door owner minimum (D-16); never in a total |

**Note on PROVISIONAL.**
- A PROVISIONAL quantity is measured, but its specification or type is pending. Examples are every ceiling (the type is not in a plan) and the wall run (material and height).
- `BOQ_RELEASE_REPORT.json` lists it under CONFIRMED, with its state on every line and in the totals.
- The benchmark scorer counts it as a PROVISIONAL answer, never as released.

## Matrix

| Capability | V2.6 | V2.7 | V2.7.1 | Evidence | Benchmark | Remaining gap |
|---|---|---|---|---|---|---|
| Room floor areas by floor | measured | + arc polygons, turned / four-line columns | + turned columns as jambs | hand truth (CROSSING, PLAIN, B10, lobby); reader faces exact on fixtures, invariant rot30 / mirror / metres; on the reference plan 1 face-verified, the rest not re-read | SUPPORTED | spaces closed by non-wall lines (D-P8-04) |
| Wet-room floor | measured | basin-only spaces REVIEW | REVIEW spaces: conditional WET / DRY sets | hand truth; fixture census on 3 reference spaces (verified for 2; 1 not closed by walls) | SUPPORTED | D-17 (type of the 3 spaces) |
| Wet-room wall ceramic | measured (heights) | as V2.6 | as V2.7; conditional in review spaces | hand truth (CROSSING 20.7696 m² VERIFIED) | PARTIAL (Mode A) | window sills (D-P8-06); real heights (D-04) |
| Ceilings | measured, PROVISIONAL | withheld in review spaces | **invariant ceiling released** in review spaces (+9.348195 m² on the reference plan) | hand truth; independent face for 2 of the 3 released ceilings | PARTIAL (always PROVISIONAL) | ceiling type per room (O-P8-02) |
| Double-height exclusions | from void symbols | as V2.6 | as V2.6 | fixture tests (earlier phases) | PARTIAL | voids drawn only in section |
| Internal / external doors | counted, classed | jamb-span width (0.80 m door) | + standard reconciliation (minimum, readings, enlargement, review), never applied | hand truth (BATH_CORRIDOR, PLAIN, WIDE, DOUBLE); jamb plaster and threshold verified on the reference plan | SUPPORTED (height UNSUPPORTED) | D-16; leaf-closed doorways (D-C2) |
| Windows and glazing | counted, width | as V2.6 | as V2.6 | hand truth | width SUPPORTED; height / sill / glazing UNSUPPORTED | sills and heads from sections / schedules |
| Plaster and paint | measured (heights) | review spaces withheld | review spaces: **wall face reported as confirmed geometry**; plaster conditional (system behind porcelain) | hand truth (26.382 m² VERIFIED); reader takeoff | plaster SUPPORTED (A); paint PARTIAL | paint above tile; real heights |
| Skirting | measured | as V2.6 | as V2.6 | hand truth (8.554 m VERIFIED) | SUPPORTED | floor glazing vs sill windows (D-P8-06) |
| Waterproofing | floor, upturn, doorway, layouts | basin spaces held | conditional in review spaces | 297 / 297 independent checks (V2.5 / V2.6 examples); doorway WP verified | SUPPORTED | junction detail (D-01) |
| Wall runs and openings | straight bands | + curved bands | + turned column cuts; stubs < 0.30 m not counted | arc census on the reference plan (+1.884956 m VERIFIED); 0.209947 m of short stubs found (D-P8-03) | run PARTIAL (PROVISIONAL); openings SUPPORTED; masonry UNSUPPORTED | stubs, block walls (BLOCKED_RFI) |
| Stairs | treads, landings; risers / flights / rails blocked | as V2.6 | as V2.6 | earlier stair stages | treads / landings PARTIAL; risers, flights, rails UNSUPPORTED | heights from sections |
| Room classification | lexicon, fixtures | WC shape, basin rule | round bowl, pan-width, wall cistern, basin linework by insert path | 18-plan truth table; reference plan: 0 V2.7 → V2.7.1 classification changes | — | WC-sized chair (L-P8-01) |
| Provenance | partial | per-line source entities (10 untraced) | 0 untraced; every untraced line states why | reference plan: 328 room-boundary, 135 opening, 14 wall-band, 10 strip | — | — |
| Change attribution | — | floor-wide explainer | **independent verification** (VERIFIED / EXPLAINED_UNVERIFIED / CONTRADICTED / UNEXPLAINED), narrowed scopes | reference plan V2.6 → V2.7.1: 55 differences, 32 verified, 23 unverified (reasons stated), 0 contradicted, 0 unexplained | — | D-P8-04 / -05 / -06 |
| Release reporting | lines and ledgers | as V2.6 | confirmed / held (reason class) / excluded / conditional; every line once | conservation on every run | — | — |
| Structural BOQ | route G (separate) | unchanged | unchanged | earlier stage packages | not in URBAN_BLIND_V2 | combined export |
| Roofs, external works, formwork, excavation | absent | absent | absent | — | not in URBAN_BLIND_V2 | catalogue gaps (G-*) |

## What "commercially useful" still needs

1. **A blind second villa** (OD-P8-02), so that any category has an accuracy statement at all.
2. **Real heights and sills from sections and schedules** (D-04, D-P8-06). They move every wall-area line from synthetic heights to evidence.
3. **The owner's D-16 and D-17.** They turn the door and review-space conditional sets into BOQ lines.
4. **The catalogue gaps.** Roofs, external works and formwork / excavation are still absent from this route.
