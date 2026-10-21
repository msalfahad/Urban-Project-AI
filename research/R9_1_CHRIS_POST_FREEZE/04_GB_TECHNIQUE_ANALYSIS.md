# 04 Ground beams: technique analysis, object by object

Sources:
- **Urban:** the frozen `GROUND_STRUCTURE_REGISTER` (V3: 43 bands, 59 spans) and the coverage-round `QUANTITY_SCENARIOS.ground_beams` (198.796 m). Band coordinates come from the re-derived `urban_extract/URBAN_GB_GEOMETRY_EXTRACT.json`, which reproduces both registers exactly.
- **christiannp:** the frozen `06_ground_beams/*`.
- **Crosswalk:** `03_GB_OBJECT_CROSSWALK.csv`.

## A. Network geometry: what physical objects each system found

| | Urban | christiannp |
|---|---|---|
| Face layer | `1` only | `1` accepted; 2 / 5 / S-FOOTINGS / S-BW / S-BOUN / D logged as candidates |
| Layer-1 faces in the GB frame | 85 LINE + 4 ARC | 89 (85 LINE + 4 ARC; MCP `entity_select` confirms) |
| Pairs accepted | 43 bands (41 straight + 2 arcs) | 44 strips (42 straight + 2 arcs), all 300 mm |
| Same face-handle pair | 43 of 43 | 43 of 44 |

- **Every Urban band is a christiannp strip with the same two faces.** The centreline offset is 0.0 mm on all 41 straight bands.
- **The only object difference is christiannp S008, faces `114` + `115`, 1.000 m.** Face 114 (4,225 mm) has two collinear partners on the other side: 115 (1,000 mm) and 7DF (3,225 mm).
- **Why Urban misses it:** `_pair_bands` keeps one best partner per face, the one with the largest overlap, and scans forward only (`lines[i + 1:]`). So 114 pairs with 7DF, and 115 never meets 114.
- **Classification:** this is a generic fragmented-mate defect, URBAN_MISSED_PHYSICAL_OBJECT, 1.000 m × 0.30 m. Urban already solved the same pattern for walls (R6 "fragmented-mate resolver with interval matching"), but never applied it to GB bands.

**No christiannp false positive.** All 44 accepted pairs are layer-1, 300 mm faces with no intervening face.

**Candidates christiannp rejected:**
- **134 LAYER_NOT_ALLOWED.** 30 of them are layer-2 pairs at 300 / 600 / 900 mm: stair treads that would otherwise look like beams. Others are S-FOOTINGS, S-BW and S-BOUN combinations.
- **1 TOO_WIDE.** P0050: faces 141 / 7D1 at 950 mm.
- **Would Urban accept any of them?** No, because Urban reads layer 1 at 300 ± 12 mm only. The stricter Urban rule is project-specific (MD01 / MD09), not wrong.

## B. Segmentation: is the difference segmentation only?

**Yes, apart from S008 and the arc convention.**

| Count | Urban | christiannp | Why they differ |
|---|---|---|---|
| Bands | 43 | 44 strips / 41 collinear bands | christiannp merges collinear strips with gap ≤ 1 m into one band; Urban keeps one band per face pair |
| Spans | 59 (band minus column rectangles; pieces < 0.09 m² dropped) | 97 edges / 98 support-to-support spans (columns + T-junctions are supports) | junctions split christiannp spans, not Urban spans |

**Length is invariant on a common basis:**
- **Gross:** Urban 207.847 m against christiannp 208.129 m. The −0.282 m difference is −1.000 m (S008) plus 0.718 m (arc sweep, section E).
- **Net of supports:** the gap comes only from the column-split convention (F). Urban 198.796 m; christiannp 191.873 m.

Comparing span counts (59 against 98) or band counts (43 against 41) therefore says nothing about accuracy.

## C. Widths

Both systems report 300 mm on every band or strip. christiannp derives it from the data (histogram `{300: 44}`); Urban imposes it (`width=300, tol=12`). Neither has a width disagreement on this sheet.

## D. Connectivity

Urban builds no node / edge graph for ground beams. christiannp's nodes:
- **Junctions:** 36 (34 of degree 3).
- **Columns:** 34.
- **Corners:** 3.
- **Pit-wall (S-BW 7C2):** 3.
- **Free ends:** 4.
  - S032 (17E / 17F, Urban GB-055);
  - S033 (180 / 181, Urban GB-056; free at both ends);
  - S042 (1811 / 1812, Urban GB-059).

The four free ends are the most useful QA output. A ground beam that ends on nothing is either a missing support in the drawing or a short stub. Urban measures these three spans and depth-bounds them, but never flags that they are unsupported.

## E. Curves

Two concentric arc pairs, found by both systems: 139 / 13A and 157 / 158.

| Arc pair | Urban | christiannp | Why |
|---|---|---|---|
| 139 / 13A (radii 1000 / 1300) | 1.806 m | 1.806 m | same 0–90° sweep |
| 157 / 158 (radii 2250 / 2550) | 7.005 m gross; 6.180 m after column 17BD | 6.287 m | see below |

Arcs 157 and 158 have different sweeps: 96.38–263.62° (167.2°) and 109.75–259.84° (150.1°).
- **Urban** `_arc_bands` uses the first arc's sweep × mean radius.
- **christiannp** uses the angular overlap × mean radius.

Only the overlap is a two-faced beam. The extra 0.718 m lies where only one face exists (the arrival into the curved junction), so Urban's arc rule over-measures. This is a generic, small, deterministic fix, and is the second Urban defect found here.

christiannp in turn does not clip arcs at columns (`col_overlap` is computed for straight strips only), while Urban removes 0.825 m inside CN column 17BD. Classified SAME_GEOMETRY_DIFFERENT_CONVENTION.

## F. Support splitting (the column convention)

Same 36 column rectangles in both systems; the centres agree within 5 mm.

| | Urban | christiannp |
|---|---|---|
| Rule | band polygon minus column rectangles; piece length = projected extent | centreline clipped by every S-COL.BON box it crosses, including the end boxes |
| Length inside columns | 9.051 m | 16.256 m |

The two rules disagree on 16 straight strips:
- **Urban under-deducts.** A column narrower than the band, or offset from it, leaves the piece's projected extent unchanged (S006, S010, S014, S022: 0 against 0.3–0.4 m).
- **christiannp over-deducts end boxes.** It counts the full length the centreline runs into a column box, even where the band stops at the column face.

Neither is a measurement error; a QS rule must decide. Recommendation: a declared GB_COLUMN_SPLIT_CONVENTION on the span record, and both values carried, never one silently.

## G. Depth authority (kept separate from geometry)

- **Urban:**
  - interior spans: ST7757 p.13 typical ground-beam sections by span length, with D = 0.30 / 0.40 / 0.60 m. This is read on the visual source lane (R4.1); the table is a drawn detail with no DXF TEXT row;
  - 28 exterior spans: FOLLOW ARCH. → BOUNDED_CANDIDATE 1.0 m.
- **christiannp:** depth UNKNOWN after 8 DXF routes (A03, U01), so volume is published only as 0.4 / 0.6 / 0.8 m scenarios.
- **Classification:** SOURCE_AUTHORITY_DIFFERENCE. Urban holds an extra source route; christiannp searched DXF text only. Volumes may be compared only after both lengths are put on one basis and the depth source is named.

## Answers to the §5 questions

| Question | Answer |
|---|---|
| True Urban misses | **1: S008** (1.000 m). Plus the arc sweep over-measure (+0.718 m, a geometry rule, not a missing object). |
| True christiannp misses | **None in the network.** Its depth miss is a source-route gap (G), not a geometry miss. |
| Segmentation only? | Yes for everything else. Band and span counts differ by construction; length is invariant on a common basis. |
| Role of curves | 2 objects, 8.093 m. 1 identical; 1 differs by the sweep rule (+0.718 m Urban). |
| Useful pairing rules to learn | (1) **all partners per face** with interval accounting; (2) a full candidate log with reject reasons; (3) the intervening-face test; (4) arc angular-overlap length; (5) free-end QA |
| christiannp false-positive accepted pairs | none |
| christiannp rejected pairs Urban would accept | none (Urban is stricter: layer 1 only, 300 ± 12 mm) |

## Techniques: Urban versus christiannp

| Technique | Urban | christiannp | Decision |
|---|---|---|---|
| Partner selection | one best per face | all pairs, then acceptance | ADOPT_CONCEPT (multi-partner) |
| Width | fixed 300 ± 12 | 150–800 data-driven | KEEP_URBAN on this project; ADAPT to a width set from the schedule |
| Duplicate removal | 80 % polygon overlap | duplicate-face reason (< 5 mm) + intervening-face test | ADAPT |
| Arc length | one arc's sweep | angular overlap | ADOPT_CONCEPT |
| Column split | piece extent | centreline clip | CHALLENGER_ONLY (declared convention) |
| Topology | none | nodes / edges / free ends, tolerance snapping | CHALLENGER_ONLY (QA); rewrite with face-line intersection (MD07) |
| Depth | evidence ladder incl. visual lane | not assumed | KEEP_URBAN |
