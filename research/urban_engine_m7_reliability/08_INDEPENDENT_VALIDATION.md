# 08 Independent validation

## 1 Held-out synthetic set (generalisation evidence)

Protocol: the engine was frozen at `af2822a` (`00_ENGINE_FREEZE.json`, sha256 of every engine, tool and conventions
file, committed in `08c4339`). Only then were seeds 301–340 generated — for the first time in this repository — and run
once by `heldout_run.py`, which refuses to run if any frozen file changed. The same drawings were run with the M6 engine
state (conventions V4). The truth is the generator's design record; it never reads the engine.

### Quantities (`tools/m7_evaluate.py`, 40 cluttered villas, 286 family / storey rows per set)

States per row: EXACT (within 1 % or 0.001 m³), IN_RANGE (inside an ambiguous-scope range: a bay holding a drawn
stair), REPORTED (short, and the shortfall is inside the engine's unresolved range or the storey's plan is reported
missing), SILENT (anything else; an over-count is always SILENT).

| Set | Engine | EXACT | IN_RANGE | REPORTED | **SILENT** | silent m³ |
|---|---|---:|---:|---:|---:|---:|
| development vocabulary | V4 | 136 | 10 | 93 | **47** | columns 15.2, slabs 125.0 |
| development vocabulary | V5 | 127 | 28 | 131 | **0** | 0 |
| held-out vocabulary | V4 | 130 | 11 | 94 | **51** | columns 15.7, slabs 182.3 |
| held-out vocabulary | V5 | 129 | 29 | 128 | **0** | 0 |

Every V4 silent row was an under-count (31 / 33 column rows, 16 / 18 slab rows). On the development seeds the same
kinds of row traced to a column absent from one plan but drawn above or bound to a pit square, and to bays merged into
a void; the held-out rows were not re-diagnosed one by one. EXACT falls for slabs under V5 because a bay holding stair
lines is no longer counted as slab in full: it becomes IN_RANGE or REPORTED — less "exact", never silent.

**No silent shortfall is not no shortfall.** V5 measures 1 199.6 of 1 454.8 m³ slab truth (development vocabulary).
The 255.2 m³ not measured is: 80.3 m³ inside reported unresolved ranges (85.2 m³ high), 50.6 m³ in bays holding a
drawn stair (ambiguous scope), and 124.3 m³ on five storeys whose plan the generator left out (the completeness pass
reports STOREY_PLAN_MISSING; no volume range is attached — open weakness M7-W21). Beams: 593.8 of 678.4 m³ — 31.1 m³
inside unresolved ranges (untagged spans) and 53.5 m³ on missing plans. Columns: 463.6 of 474.8 m³ — the 11.2 m³ short
is inside unresolved ranges. Footings: exact (646.0 m³).

Clean M2 villas (seeds 301–320, nothing injected): V4 and V5 identical; footings, columns and slabs EXACT on every
row, beams REPORTED (the untagged-span convention), no silent row.

### Completeness detection (`tools/m6_evaluate.py`, the M6 configurations)

| Set | Engine | injected | detected | false findings | design-void flags | family right / wrong / unknown |
|---|---|---:|---:|---:|---:|---|
| development vocabulary (A2) | V4 | 479 | 478 | 5 | 3 | 341 / 16 / 34 |
| development vocabulary (A2) | V5 | 479 | **479** | **1** | 5 | 350 / 12 / 30 |
| held-out vocabulary, hard (B2) | V4 | 479 | 478 | 8 | 3 | 326 / 21 / 44 |
| held-out vocabulary, hard (B2) | V5 | 479 | **479** | **1** | 4 | 335 / 19 / 38 |

A "design-void flag" is a REGION_EXCLUDED finding on the design's own opening bay (VOID + X across bay (0,0)): a
correct large-void review flag that the M6 truth does not list. The remaining false finding in each V5 set is one
SLAB_COVERAGE_LOW.

Repeated on the engine with the post-freeze fixes P1–P3 (`postfix_run.py`, reported apart in
`heldout/POSTFIX_COMPLETENESS.json`; the frozen records are not rewritten): both V5 sets identical on every
count above (detected, false findings by kind, design-void flags, family states, crashes).

### Metamorphic properties (seeds 301–310, 10 operations)

V4 69 / 100, V5 **100 / 100** (V4 failures: dup_text 10, explode 10, noise_layer 9, translate 2).

## 2 Per-item second method (`tools/m7_independent.py`)

Shapely (GEOS), which the route never uses, recomputes each measured concrete item from the detected polygons: slab
face less the union of bands and columns × thickness; band less columns − the junction squares the engine gave
another band × the item's depth reading; footing outline × printed depth (or every candidate type for a footing with two
type labels); columns B × H × h (arithmetic only — stated as such). What each check shares with the engine is recorded
per item. ST7757 (V5): 271 PASS, 58 NOT_COMPARABLE (arc bands, arc-bounded and recovered panels, items with no
section), **0 DIFFERS**. A check that differs makes the item UNRESOLVED whatever its support — the policy, not a person,
holds it back.

The checker itself was wrong once: it compared a footing labelled with two types against the first type's size; the
engine (convention: the larger) was right. Fixed after the freeze (P3); the item had been held UNRESOLVED meanwhile,
which is the failure mode the policy is meant to have.

## 3 Tests (`tests/m7_reliability/`, 42)

| File | What it proves |
|---|---|
| `test_m7_geometry.py` (11) | fixtures with the expected value from the fixture geometry: mirrored TEXT and MTEXT direction; crossing rectangles; unit-aware polyline rectangles; local origin moves everything and records it; a flush column does not cut; treads per layer; a furniture square is no column; continuous-beam anchorage equal in both directions (and different under the frozen rule); an exploded clipped outline is a polygon; a length on a class limit at the millimetre |
| `test_m7_legend.py` (5) | the adversarial legends above |
| `test_m7_release.py` (6) | the evidence ladder; an approval holds only for its revision and its item; an estimator cannot approve; an UNRESOLVED item cannot be approved into a total; a rejected OCR reading never returns by itself; totals keep their counts; reconciliation states, unmapped rows never guessed |
| `test_m7_project_run.py` (3) | the blind protocol: frozen before the reference is read, byte-identical rebuild, refusals (other revision, no freeze, an output edited after the freeze, another reference) |
| `test_m7_properties.py` (9) | every metamorphic operation on three cluttered villas (mm with drafting noise, metres, the furniture-on-mark case); V4 fails the unrelated-layer property; no SILENT row on four cluttered villas; a set-aside outline stays evidence |
| `test_m7_package.py` (8) | the package: files, hygiene (and no PDF / workbook / drawing / image in git), the freeze against git, the held-out summary against its records, the CSV builder byte for byte, the workbook and the visual QA PDF rebuilt from the records (the PDF twice, byte-identical), and (with the private drawings) the ST7757 records rebuilt live |
