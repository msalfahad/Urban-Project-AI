# Alsenan (ST7757) through the generic route, against the frozen replay

**Data:** `04_ALSENAN_GENERIC_VS_FROZEN.csv`, one row per trade and family. Route G outputs are in `alsenan_route_g/`.

**How route G ran**
- It used the committed engine (comparison first run on 8c1e28e and unchanged since), the generic convention set and `profile_st7757.json`.
- The profile holds four printed inputs and nothing else: the GF / 1F / 2F storey heights from P7757 VE-AA-09, and the p.13 typical ground-beam classes.
- No frozen stage register, layer list, mark list or coordinate was given to the generic route.

**The frozen replay (route A)** is M1's: verified releases plus provisional base, research/alsenan_m1_usable_boq/boq.

Both are planning estimates. Neither is ground truth: this is a consistency comparison between two of our own routes.

## Summary

| scope | frozen replay | generic route | generic / frozen |
|---|---|---|---|
| RC concrete, six families in generic scope (footings, columns, beams, ground beams, slabs, ground slab) | 287.4 m³ | 263.4 m³ | 0.917 |
| reinforcement, the same six families | 22,961 kg | 19,741 kg | 0.860 |
| RC concrete outside generic scope (stairs, domes, lift, pool, tank, lintels, cantilevers) | 33.2 m³ | not quantified: BOQ section C | — |
| plain concrete (blinding) | 9.97 m³ | not quantified: BOQ section C | — |
| reinforcement outside generic scope | 1,906 kg | not quantified: BOQ section C | — |

## By family, with the evidence for each difference

| family | frozen | generic | ratio | class | evidence |
|---|---|---|---|---|---|
| beams, concrete | 63.84 | 62.56 | 0.98 | SAME_OBJECTS_CLOSE_RESULT | Same bands. 16 unbound or ambiguous bands are UNRESOLVED with exposure (8.9 m³ high), not added. |
| slabs, concrete | 57.10 | 60.10 | 1.05 | CONVENTION_DIFFERENCE | Generic panels stop at band faces. Thickness is printed, or sheet-uniform (provisional). One OPEN_BOUNDARY face on GF is reported, not counted. |
| footings, concrete | 66.26 | 50.04 | 0.76 | DETECTION_GAP | Four footing marks (F, F11, F10, FN) have no outline the generic route can bind. They carry no quantity yet: their schedule size is known, but the generic route does not price a footing it cannot locate. Listed as FOOTING_NO_OUTLINE. |
| columns, concrete | 47.18 | 41.17 | 0.87 | DETECTION_GAP | 35 column-plan occurrences carry marks (C, CN, …) with no schedule row; they are UNRESOLVED. Foundation necks need a founding level the drawing does not print. |
| ground beams, concrete | 36.25 | 27.36 | 0.75 | CONVENTION_DIFFERENCE | The generic route applies the p.13 class depth to every band. The frozen replay separates exterior beams (depth to 1.00 m less build-up) and straps. One 0.95 m slab strip was taken as a ground beam (width-mode flaw, see 06). |
| ground slab, concrete | 16.76 | 22.20 | 1.32 | SCOPE_DIFFERENCE | 19 identical faces, plus a generic-only 49.07 m² face with free-standing columns inside it, plus the 8.37 m² stair-flight zone S8.1 excluded (06). |
| beams, steel | 5,490 | 6,882 | 1.25 | BAR_MODEL_DIFFERENCE | The generic model gives schedule bars full length plus 40 d anchorage, and ACI links at the schedule pitch, where the frozen stages used their own BBS. 11 of M1's bar-less beam components now have a model (05). |
| columns, steel | 7,488 | 6,100 | 0.81 | BAR_MODEL_DIFFERENCE | Generic: main bars per storey plus a 50 d lap, and ties from the printed tie note. 35 unscheduled occurrences carry no bars. |
| footings, steel | 3,630 | 2,877 | 0.79 | DETECTION_GAP | The same four footings without an outline. |
| ground beams, steel | 1,516 | 0 | 0.00 | GENERIC_MISSING_DATA | The typical ground-beam bars are only in the PDF detail. The PDF has no text layer (vector glyphs) and there is no OCR, so all 59 bands are MISSING_DATA in the rebar register. |
| ground slab, steel | 1,035 | 1,371 | 1.32 | SCOPE_DIFFERENCE | The same mesh note over the larger generic area. |
| slabs, steel | 3,802 | 2,512 | 0.66 | BAR_MODEL_DIFFERENCE | The generic route reads the slab mesh note in one direction (SLAB_MESH_DIRECTIONS base 1, range 1–2). The frozen stages measured their own strips. |

## Coverage risk the generic route reports on Alsenan (`07_ALSENAN_COVERAGE_RISK.csv`)

| kind | count | kind | count |
|---|---|---|---|
| SCHEDULE_ROW_NOT_FOUND_ON_PLAN | 39 | OPENING_DEDUCTED | 5 |
| BAND_UNBOUND | 15 | FOOTING_NO_OUTLINE | 4 |
| MARK_TAG_UNBOUND | 7 | MARK_AMBIGUOUS | 4 |
| FAMILY_NOT_QUANTIFIED | 6 | SLAB_UNENCLOSED_BAND_SIDE | 2 |
| BAND_MULTIPLE_MARKS | 1 | SLAB_OPEN_BOUNDARY_FACE | 1 |
| SCHEDULE_DUPLICATE_MARK | 1 | | |

**Not-detected families (BOQ section C)**
- With drawing evidence: domes, parapets, plain concrete, pool, stairs, water tank.
- With no label found, and "confirm absent" lines: cantilevers, necks, lift, lintels, walls.
- The frozen replay holds lift and lintel quantities, so the "confirm absent" line matters. Without it, the generic route would have hidden two real families.

## What would close the gap (by impact)

1. Ground-beam bars: read the typical detail (PDF OCR, or the DXF detail sheet SH01 if its texts are drawn there).
2. Footings without an outline: a footing mark with a schedule size but no outline should give a PROVISIONAL quantity at schedule size, with COUNT_FROM_MARK and a coverage-risk flag, rather than nothing.
3. Ground beams: an exterior-band rule, an outermost-band class with a reported depth range.
4. Columns: report unscheduled occurrences by mark with the drawn section as an exposure.
5. Ground slab: flag panels that hold free-standing columns or level marks (PANEL_CONTAINS_COLUMNS) and restrict width modes to scheduled widths.
