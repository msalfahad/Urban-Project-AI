# 02 Baseline and architecture

## Baseline reproduced before any M7 change

| Check | Result |
|---|---|
| M6 full suite (`5729e01`) | 7 434 passed, 0 code failures, 376 blocked by missing data (`research/urban_engine_m6_completeness/06_TEST_RESULTS.md`) |
| M1–M6 package suites on the working tree | all pass; the live reproductions of the M4 registers, the M5 text files and both M6 ST7757 runs rebuild byte for byte |
| M6 held-out V2 record (seeds 201–240) re-run with conventions V4 | 470 / 470 detected in both vocabularies, 9 and 11 false findings — identical to the M6 record |

Every M7 change was re-checked against this baseline after it was made (the frozen packages are the regression
oracle). Two candidate changes were withdrawn because they moved a frozen output at the last digit without changing a
quantity: an origin-relative `poly_area` (it changed which footing an M4 check names as the "worst" of 26 identical
zero differences) and an ungated local-origin slab build (it moved SVG coordinates in the M5 package by one ulp). Both
ideas survive as the gated V5 convention `GEOMETRY_LOCAL_ORIGIN`.

## The pipeline and where its risks were

```
DXF --intake--> entities --drawing model--> sheets / roles / storeys --schedule reader--> rows
    --member detection--> footings, columns, bands, marks --slab engine (TS01 topology)--> faces
    --items (provisional estimate)--> PROVISIONAL / UNRESOLVED items --completeness--> findings
    --[M7] independent checks--> --[M7] release policy--> states, totals with counts
    --[M7] project runner--> frozen run --[M7] reconciliation (after the freeze only)
```

| Stage | Risk found in M7 | Kind | Rule (V5 unless stated) |
|---|---|---|---|
| intake | MTEXT direction vector ignored; mirrored TEXT in OCS | reading | intake fixes (unconditional; no frozen output changes) |
| drawing model | frames drawn as lines; duplicated annotations; polyline rectangles below 1.0 unit; local frame | placement / encoding | `SHEET_FRAMES_FROM_LINES`, `DUPLICATE_ANNOTATION_READ_ONCE`, `UNIT_AWARE_RECTANGLES`, `GEOMETRY_LOCAL_ORIGIN` |
| member detection | column on a furniture layer; nearest outline instead of the section; crossing outlines; exploded clipped outline; flush column cuts a band by noise | interpretation / predicate | `COLUMN_LAYER_EVIDENCE`, `COLUMN_OUTLINE_BY_SECTION`, `RECTANGLE_FROM_FOUR_SIDES`, `POLYGON_FROM_LINE_RING`, `TOUCH_IS_NOT_OVERLAP` |
| slab engine | bays merged through a support gap and dropped as one opening; an opening label inside a face holding beams; stair lines broken by another layer; free-column test on flush / arc geometry | topology / predicate | `SLAB_JUNCTION_GAP_CLOSURE`, `SLAB_OPENING_EXTENT_GUARD`, `STAIR_TREADS_ONE_LAYER`, `TOUCH_IS_NOT_OVERLAP` |
| items | column absent on a plan but drawn above; flight inside a panel; continuous beam read reversed; class limits at float precision | silent quantity | `COLUMN_PRESENCE_CONTRADICTION`, `SLAB_STAIR_FOOTPRINT_UNRESOLVED`, `CB_ENDS_BY_SHARED_SUPPORT`, `LENGTH_CLASS_AT_MILLIMETRE` |
| completeness | legend rows close together; evidence lost when a rule tightens | interpretation | `LEGEND_NEAREST_CAPTION`; post-freeze P2 |
| release | no per-item check, no revision-bound decisions, OCR rejections not persistent | release | `engine/source/quantity_release.py` |

## The gating pattern

Every behaviour change is switched on by the presence of a convention id in the merged conventions
(`generic_route.detect_options`), passed down as detection options (the drawing model carries them to every sheet's
entities, so member detection and the completeness pass read the same switches). V3 / V4 runs see none of them, which
is why the M4–M6 packages reproduce unchanged. V5 is the default of the project runner, so a new project gets M7.
