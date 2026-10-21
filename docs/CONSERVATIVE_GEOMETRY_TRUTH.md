# Conservative geometry truth round

The GEOS mechanism is accepted. The uncertainty had moved into the input
wall solid, and this round went looking for it. Four claims from earlier
rounds did not survive.

---

## 1 · Coverage, in one primitive

`45.9%` divided a **wall-band** length by a **source-stroke** length. A
two-face wall contributes about two source-face lengths and one band
length, so the numerator was deduplicated and the denominator was not.

Every term is now source-stroke length, and the parts add to the total:

| metric | length | share |
|---|---|---|
| `SOURCE_WALL_STYLE_STROKE_LENGTH_TOTAL` | 1912.5 m | 100% |
| `SOURCE_STROKE_LENGTH_USED_IN_ACCEPTED_BANDS` | 1061.5 m | 55.5% |
| `SOURCE_STROKE_LENGTH_FRAGMENTED_MATE` | 289.0 m | 15.1% |
| `SOURCE_STROKE_LENGTH_NON_WALL` | 266.7 m | 14.0% |
| `SOURCE_STROKE_LENGTH_UNRESOLVED` | 214.5 m | 11.2% |
| `SOURCE_STROKE_LENGTH_CLASSIFIED_SINGLE_LINE` | 58.1 m | 3.0% |
| `SOURCE_STROKE_LENGTH_DUPLICATE` | 22.6 m | 1.2% |
| `SOURCE_STROKE_LENGTH_UNACCOUNTED` | **0.0 m** | 0.0% |

Capture: **55.5%** of all source-stroke length reached an accepted band;
**75.4%** of the wall-like population did. Both terms source-stroke.

`PHYSICAL_WALL_LENGTH_FROM_ACCEPTED_BANDS` = 615.1 m from 243 bands, on a
`TWO_DRAWN_FACES_ARE_ONE_WALL` basis, reported separately and never divided
into the figures above. No physical length is derived for the unpaired
population.

## 2 · Unknown stays unknown

"127.1 m was never a wall" added three different things together. They are
reported apart:

```
classified non-wall   266.7 m   evidence says not masonry
duplicate              22.6 m   one mark twice — not an ADDITIONAL wall
unresolved            214.5 m   NOT proven non-wall, in neither figure
```

## 3 · Two wall solids

Admission is **per interval**, because a band is usually part established
and part not:

| grounds | length | solids |
|---|---|---|
| `BOTH_FACES_DRAWN` | 446.383 m | both |
| `ONE_FACE_WITH_AN_END_CAP` | 87.877 m | both |
| `ONE_FACE_WITH_A_JUNCTION_OVERHANG` | 24.024 m | both |
| `UNRESOLVED_SINGLE_FACE_EXTENSION` | **55.946 m** | diagnostic only |

```
ESTABLISHED_WALL_SOLID            104.43 m2   432 intervals
DIAGNOSTIC_AUGMENTED_WALL_SOLID   116.63 m2   453 intervals
the hypothesis adds                12.20 m2   10.5%
```

## 4 · What removing the 55.9 m does

The same free-space path on both solids:

| | ESTABLISHED | DIAGNOSTIC_AUGMENTED |
|---|---|---|
| free-space components | 13 | 19 |
| single-room candidates | 4 | 8 |
| largest merged component | **32 labels** | 23 labels |
| BED-01 | in the 32-label blob | **its own polygon** |
| BTH-01 | in the 32-label blob | 2-label component |
| STR-01 | in the 32-label blob | in the 23-label blob |

**BED-01 exists as its own room only because unestablished material was
treated as masonry.** Its boundary runs along 5.104 m of
`UNRESOLVED_SINGLE_FACE_EXTENSION` — WB-00160 (2152 mm) and WB-00030
(2000 + 952 mm).

## 5 · Five junction patches

Each proposed from local vector geometry, never from a tolerance:

| patch | gap | width | verdict | evidence / conflict |
|---|---|---|---|---|
| JP-0001 | BTH-03/BED-02 | 50 mm | REFUSED | 1 band within 800 mm; raster 0.43; 3 wall-like strokes at the gap |
| JP-0002 | BTH-01/BED-NW | 50 mm | REFUSED | 1 band; raster 0.50; 3 wall-like strokes |
| JP-0003 | MBTH-02/BED-02 | 100 mm | **VALIDATED** | T-junction, GEOMETRY + RASTER, 13 mm extension of 441 mm allowed |
| JP-0004 | BTH-04/BED-02 | 150 mm | REFUSED | separations differ by 251 mm — two different walls |
| JP-0005 | BED-04/BED-02 | 300 mm | REFUSED | raster support **0.00** — nothing is drawn there |

Repair classes: 2 × `REPAIR_IS_IN_WALL_FACE_PAIRING`, 1 ×
`REPAIR_IS_JUNCTION_ASSEMBLY`, 1 × `NOT_ONE_WALL…`, 1 ×
`NOTHING_IS_DRAWN_HERE_THE_OPENING_IS_REAL`.

Validated material: **0.0026 m²**.

## 6 · The counterfactual

Established solid, plus only JP-0003, nothing else changed:

```
single-room candidates   4 -> 4    (+0)
largest component       32 -> 32   (+0 labels)
wall solid            +0.00167 m2
verdict: REPAIRS_CHANGED_NOTHING_IN_THE_PARTITION
```

The five gaps are **not** the dominant cause of the merging. Last round said
they were, on the strength of the localiser pointing at them.

## 7 · Snap topology, not area

| | 0.01 mm | 0.05 mm |
|---|---|---|
| wall-solid components | 49 | 46 |
| area | | +0.000369 m² |

Two joins created by the coarser grid, both `NUMERICAL_NOISE_JOIN` within
the measured noise floor, at (10347, 24250) and (31548, 26120). Zero
`FALSE_JOIN`. `coarse_grid_is_defensible: true` — proven on topology, not
inferred from area.

Production still builds the established solid on the measured tolerance.
The separation figure is quantised to the fine grid, so it bounds the
distance rather than measuring it exactly; what it establishes is that the
pieces are indistinguishable *at* the noise floor.

## 8 · What "CONFIRMED" was confirming

The evidence rule had two holes: it never checked the pen, and its "no mate"
test looked only for collinear neighbours on the same line, not for the
parallel face a single-line wall is defined by not having.

Pen widths in the 434.8 m population, against a measured 1.14 pt wall pen:

```
0.36 pt   34 strokes    79.9 m
0.72 pt    6 strokes   177.5 m
1.14 pt    4 strokes   155.6 m   <- the only wall-pen strokes
0.30 pt   20 strokes    18.0 m
0.12 pt   11 strokes     3.9 m
```

With pen, parallel-face, over-length and wall-network tests added:
**434.8 m → 58.1 m in 2 strokes**, a 7.5× overreach retired. Both survivors
are 29 m runs at y = 2452 and y = 51200 — outside the building's extent,
almost certainly the sheet frame. They are reported with that caveat rather
than removed by another rule chosen to remove them.

The claim is split: `SINGLE_LINE_WALL_EXISTENCE_SUPPORTED` may become a
`TOPOLOGY_SEPARATOR_HYPOTHESIS`; `SINGLE_LINE_WALL_GEOMETRY_COMPLETE`
requires an independently established thickness and both face positions,
and nothing produces it.

## 9 · The blind sample

Deterministic, seeded on the drawing id and revision, stratified across
long / medium / short / junction-connected / isolated / near-a-labelled-room.
The manual expected-wall list is not consulted in the sampling or in any
evidence field, and every member carries `verdict: NOT_ADJUDICATED_HERE`.

The 12-member sample of the original population is what exposed the pen and
parallel-face holes: 11 of 12 were not wall-pen, and members had parallel
faces at 40.5, 51.4, 151.4, 237.9 and 248.7 mm.

## 10 · BED-01, neutrally

```
vector 21.0338 m2   reference 23.7838 m2   IoU 0.802   delta -11.56%
```

100% of the disagreement is **spatially attributed**:

| cause | area | attributed to |
|---|---|---|
| F — segmentation grew out through the doorway | 3.8370 m² | the reference's construction |
| A — its boundary stopped 83 mm short of the finish face | 0.5671 m² | the reference's construction |
| D — it carved around fixtures (60 holes) | 0.4859 m² | the reference's construction |

`adjudication: CORRECTNESS_NOT_YET_ADJUDICATED_BY_AN_INDEPENDENT_SOURCE`.
There is no independent ground truth on this project; the sealed site
benchmark is not opened. BED-01 remains frozen, the comparison ran after its
hash was taken, and no tuning followed.

## 11 · BED-01 release audit

```
DIAGNOSTIC_GEOMETRY_ACCEPTED   = true
PRODUCTION_GEOMETRY_RELEASED   = false
```

Two blockers:
1. its boundary rests on **5.104 m** of wall material whose physical
   presence is not established;
2. its partition depends on two barriers whose portal existence is not
   validated (`PT-BED-01-west-27124`, `PT-GH27048-line-27348`).

BTH-01 and STR-01: both verdicts false.

## 12 · Two recalls

```
DIAGNOSTIC_SPACE_GEOMETRY_RECALL          9 / 17   (52.9%)
RELEASE_ELIGIBLE_SPACE_GEOMETRY_RECALL    0 / 17   (0.0%)
```

The gap is nine spaces. Block reasons across the single-label components:
`BOUNDARY_RESTS_ON_UNESTABLISHED_WALL_MATERIAL` 6,
`PARTITION_DEPENDS_ON_A_DIAGNOSTIC_PORTAL` 4,
`GEOMETRY_ROLE_IS_NOT_AN_OCCUPIABLE_SPACE` 4.

## 13 · Release free space vs diagnostic free space

`RELEASE_FREE_SPACE` — established solid, 2 release-eligible barriers of 19:
4 single-room candidates, 32-label largest component, every control inside
it.

`DIAGNOSTIC_FREE_SPACE` — augmented solid, all 19 barriers: 8 single-room
candidates, 23-label largest component, BED-01 alone in its own polygon.

## 14 · Merged component work list

40 separators across the three components, ranked by rooms unlocked, then
frozen controls, then passage width — never by length.

By representation: 22 `ACCEPTED_TWO_FACE_BAND`, 16 `NOTHING_DRAWN`,
2 `PORTAL_CANDIDATE`. By confidence: 1 HIGH, 2 MEDIUM, 37 LOW.
Junction patches needed: 1.

Every row reads `effect_when_repaired: NOT_MEASURED` except the one with a
counterfactual, which reads `MEASURED: … REPAIRS_CHANGED_NOTHING`.

## 15 · Component count is still not a target

46 wall-solid components remains diagnostic. The established solid has *more*
(67) than the augmented one (50), because removing the unestablished
extensions disconnects things — and that is not a defect. The target is
correct space partitioning.

## 16 · Workbook

Dashboard: `GEOMETRY_MECHANISM_PROVEN = PASS`,
`DIAGNOSTIC_SPACE_RECALL = 9 / 17`,
`RELEASE_ELIGIBLE_SPACE_RECALL = 0 / 17`,
`FINAL_BOQ_STATUS = BLOCKED`.

Free Space QA gains `geometry_source` (`ESTABLISHED` /
`DIAGNOSTIC_AUGMENTED`), `release_eligible`, `portal_minimum_status` and
`unestablished_wall_dependency_m`.

## 17 · Project 2

Still no second drawing. `tools/freeze_new_source.py` stays ready and
refusing.

---

## What this round established

The system can now distinguish, at the geometry level, what is physically
established from what is only a useful topology hypothesis. It also
established that **no room on this floor is currently release-eligible** —
zero of seventeen — and that three of the claims in the last round's report
were wrong: the five gaps are not the dominant cause, 434.8 m of single-line
wall was a classifier artefact, and 45.9% coverage was a mixed-primitive
division.
