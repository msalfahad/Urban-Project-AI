# M3 real-drawing recovery and BOQ completeness: final report

**This is a planning estimate engine, not engineering-approved, with no prices. No quantity is construction-approved, and the gate stays INCOMPLETE.**

- **Categories:** Verified / Provisional / Unresolved / Not detected. A new project is never Verified, so every M3 quantity below is Provisional or Unresolved.
- **Comparison figures:** the M2 engine and the frozen M1 replay are comparison points, not ground truth. External estimates appear as positions only (`09_BENCHMARK_POSITIONS.csv`). Nothing was tuned to any of them.
- **Sources:** every number here comes from the live runs written by `build_m3_reports.py` (see `00_NUMBERS.json` and the CSVs it cites).

## 1. Code implemented

| WP | Module | What it does now |
|---|---|---|
| 1 | `engine/source/member_detection.footings` | Reads footing outlines four ways: rectangles, clipped polygons, per-layer templates for outlines opened by a strap entry, and a label beside its outline. Footings drawn by label only take the schedule size (outline not confirmed). Two type labels on one footing are quantified once (`FOOTING_LABEL_CONFLICT`). Nested twins are counted once. Type marks without a number (FF, FN) are accepted. |
| 2 | `column_occurrences`, `column_storeys`, `generic_route` | Twin outlines are de-duplicated. A column-plan size that equals any band of the schedule is accepted. Storey presence comes from the roof-slab plans. Necks are measured over their own footing from printed levels. A column mark found in a beam table is read as a beam. |
| 3 | `drawing_model.mark_family`, `bind_marks`, `generic_route._straps`, `slab_engine.band_sides` | Dotted marks (S.B2) are read. Duplicate schedule rows are bound by the drawn width. Strap beams on the foundation plan are measured, minus the footing plan. Ground-beam plans use source-supported widths only. Perimeter bands take the printed exterior detail. |
| 4 | `tools/pdf_evidence.py`, `engine/source/detail_evidence.py` | Native text first, then the vector check, then local OCR with four reads per token. A page-wide vector-glyph vote checks every digit against the drawn glyph. Records keep page and region coordinates, raw text, confidence and crops (crops are not committed). Owner and file-path text is redacted. A manual-transcription schema covers what OCR cannot read. Typical ground-beam details are assembled from the evidence. |
| 5 | `slab_engine.classify_regions`, `tread_family`, `open_boundary_panel` | Every face gets a region class. Stair zones are found from tread lines. A ground-slab cell with a free-standing column is unresolved. Every drawn column outline bounds the cells. An open-boundary face keeps its panel part (face minus bands). |
| 6 | `member_detection.intervening_parts`, `shared_face_parts`, `collinear_neighbours(supports=)`, `single_face_beams` | Strips that the pairing dropped whole for a few millimetres of overlap are recovered. Shared faces keep their unambiguous part. Inheritance bridges a column-filled gap. Layers named for beams join the edge layers. Single-face edge beams are inferred only under strict conditions. |
| 7 | `generic_route.rebar_completeness`, `tools/urban_boq_m2.py` | Every concrete component has one reinforcement state. Missing steel is counted by family and storey in BOQ section D, the MISSING_STEEL sheet, a CSV and the report PDF. It is a count, never 0 kg. |
| 8 | `generic_route._blinding_items`, `engine/source/family_coverage.py` | Blinding (plain concrete) is measured under footings and beams. Every other family gets a coverage record (state, evidence, reason, the input that would unlock it). An absent label is reported as "confirm absent", never as "absent". |
| 9 | `research/urban_engine_m3_recovery/evaluate_heldout.py`, `st7757_snapshot.py`, `build_m3_reports.py`; `tools/synthetic_villa.py --m3` | The M2 and M3 engines run on the same drawings in separate processes. The generator gains an M3 defect mode: a 10 mm intervening stub and a label-only footing. |
| 10 | `tools/m2_overlay.py`, `12_COVERAGE_DASHBOARD.html` | Region-coloured overlays, with before/after shown side by side. |
| 11 | CLI `--evidence`, the intake cache, rebuilds from the detected model | See `14_PERFORMANCE.json`. |

New conventions are all named, with ranges, in `engine/profiles/URBAN_M3_GENERIC_CONVENTIONS_V2.json`:

- FOOTING_LABEL_ONLY / _CONFLICT, NECK_HEIGHT_EXPOSURE_M
- GB_EXTERIOR_CANDIDATE, GB_EXTERIOR_BUILDUP_M
- SIDE_BAR_READING, SCHEDULE_DUPLICATE_ROW
- BLINDING_PROJECTION_M, BLINDING_UNDER, BLINDING_THICKNESS_EXPOSURE_M

The ST7757 profile carries 11 typed project values, each with its source.

## 2. Detection counts before / after (M2 engine, then M3 engine; `02_BEFORE_AFTER_DETECTION.csv`)

- **Footings (SH10):**
  - confirmed: 22 → 25
  - no outline: 4 → 0
  - one label-type conflict now held as one footing
  - straps: 0 → 3 (SB1, SB3 bound; SB2 bound by its drawn width)
- **Marks with no band (TAG_UNBOUND):** 7 → 1
  - 1F CB11 (×3) recovered
  - GF CB5, B1, B27 recovered
  - one GF CB5 label sits in a three-face zone and stays unbound
- **Unbound beam bands:** 15 → 13
- **GF bound bands:** 59 → 65 (B27 0.90 inclined, CB8 span 3, B1 and CB5 pieces)
- **1F bound bands:** 35 → 38
- **Ground-beam plan:**
  - the 0.95 m slab strip is no longer a band (58 bands, all at 0.30)
  - cells: 22 → 24 (the M2-missed 2.05 m² cell is closed; the 0.95 strip is slab again)
  - unenclosed band sides: 2 → 0
- **Region classes now reported:**
  - stair zones: 2 (8.37 m² on the ground-beam plan, 17.13 m² on 1F)
  - free-column cell: 1 (49.07 m²)
  - recovered open-boundary panel: 1
- **Schedule rows not found on any plan:** 39 → 32

## 3. Concrete by family, m³ (`03_CONCRETE_BY_FAMILY.csv`)

| Family | M2 generic | M3 low – base – high | M3 unresolved (n) | Frozen M1 replay |
|---|---|---|---|---|
| Footings | 50.04 | 64.52 – **66.26** – 66.26 | 0 | 66.26 |
| Columns | 41.17 | 46.14 – **46.14** – 48.81 | 13 (exposure 1.54 – 5.51) | 47.18 |
| Beams | 62.56 | 69.38 – **70.02** – 87.45 | 14 | 63.84 |
| Ground beams + straps | 27.36 | 30.49 – **41.05** – 43.47 | 0 | 36.25 |
| Slabs | 60.10 | **61.67** | 1 (stair zone, 2.74) | 57.10 |
| Ground slab | 22.20 | **16.78** | 2 (stair zone + free-column cell, 5.75) | 16.76 |
| **Core six** | **263.43** | 288.98 – **301.92** – 324.45 | 30 items, exposure 13.5 – 21.9 | **287.40** |
| Blinding (plain concrete) | 0 | 23.21 – **26.41** – 29.66 | 0 | 9.97 |

## 4. Reinforcement by family, kg (`04_REINFORCEMENT_BY_FAMILY.csv`)

| Family | M2 generic | M3 base | Frozen M1 replay |
|---|---|---|---|
| Footings | 2 876 | **3 736** | 3 630 |
| Columns | 6 100 | **6 651** | 7 488 |
| Beams | 6 882 | **7 564** | 5 490 |
| Ground beams + straps | 0 | **4 918** (28 link items unresolved) | 1 516 |
| Slabs | 2 512 | **2 584** | 3 802 |
| Ground slab | 1 371 | **1 036** | 1 035 |
| **Core six** | **19 741** | **26 488** (23 234 – 28 797) | **22 961** |

**Missing steel** (`08_MISSING_STEEL_BY_FAMILY_STOREY.csv`):

- 110 concrete components have no full bar quantity: 82 MISSING_DATA and 28 PARTIAL_MISSING.
- They are listed in BOQ section D, in the workbook and in the report PDF as counts, never as 0 kg.

## 5. Missing components recovered (classes from `05_RECONCILIATION_M2_TO_M3.csv`)

**Corrected omission:**

| Component | Concrete | Steel | Note |
|---|---|---|---|
| FF footing (type mark without a number) | 11.39 m³ | 735 kg | `FOOTING_TYPE_MARK_WITHOUT_NUMBER` |
| FN footing (type mark without a number) | 0.26 m³ | 13 kg | `FOOTING_TYPE_MARK_WITHOUT_NUMBER` |
| Footing outline recovered from its layer template | 2.63 m³ | 112 kg | `FOOTING_OUTLINE_RECOVERED` |
| Column necks over their footings (28) | 10.86 m³ | 1 429 kg | `COLUMN_NECK` |
| CB11 (1F) recovered from a 10 mm intervening stub (3 parts) | 2.85 m³ | | `INTERVENING_FACE_PART`; the frozen replay also has 2.85 m³ for CB11 |
| Shared-face part (GF) | +0.18 m³ new, −0.81 m³ on the same component | −116 kg | `SHARED_FACE_UNAMBIGUOUS_PART`: the part both faces agree on replaces a longer M2 band |
| Open-boundary panel part (GF) | 0.14 m³ | | `OPEN_BOUNDARY_RECOVERED` |
| Strap beams SB1, SB3 | 2.65 m³ | 405 kg | `STRAP_BEAM` |
| Ground-beam bars from the p.13 detail evidence (58 bands; OCR-derived, unreviewed) | | 4 281 kg | `GB_BARS_FROM_PDF_EVIDENCE` |
| Blinding under footings and ground beams | 26.41 m³ | | `BLINDING` (thickness OCR-read, RFI M3-RFI-06) |

- B27, B1 and CB5 on GF are now bound. Their bands were re-numbered by the new topology, so they sit in the untagged NEW_OR_RENAMED rows rather than under a cause tag. GF B27 is now 3.34 m³ in 2 items; the frozen replay has 2.63 m³ in 1 item.
- On the ground-beam plan the 2.05 m² cell M2 missed is closed, and the 0.95 m strip is slab again. The plan's panel area goes from 222.04 to 225.23 m².

**Corrected double count:**

- No M2 component was counted twice at the component level.
- The bands M3 recovers are cut out of the slab faces so that they are not counted twice. Beam strip area grows from 49.90 to 57.47 m² on 1F and from 51.47 to 63.20 m² on GF, and the panels shrink by the same plan area.

**Source interpretation:**

- 13 columns absent on the storey plan are no longer counted: −5.88 m³, −878 kg.
- The two stair zones are held out of the slabs: −0.84 m³ ground slab and −2.74 m³ slab, now UNRESOLVED with their exposure.

**Provisional assumption:**

- **Perimeter ground beams on the exterior detail (24 bands):**
  - against M2: +10.06 m³ (+0.49 on one new band, +9.57 on 23 existing ones);
  - against the typical class section: +9.90 m³ and +754 kg. With every band at the class section, the family would be 31.15 m³.
- **Spans inherited along their line:**
  - M3 holds 11 such items, 5.98 m³ in all;
  - against M2 the net change is about zero (+3.31 m³ on 4 new items, −3.36 m³ on 2 re-cut ones).

**Remaining source ambiguity:**

- SB2 (duplicate schedule rows, bound by its drawn width): 1.13 m³, 231 kg.
- The two type labels on one footing: 1.96 m³, quantified once.
- The 49.07 m² ground-slab cell with a free-standing column: unresolved, exposure 4.91 m³.

**Untagged changes:** the remaining M2 → M3 differences are re-numbered components. One example is beams: 16 M2 ids gone (−20.22 m³) and 17 new ids (+21.82 m³). The per-family split between deltas with and without a cause tag is in `05_RECONCILIATION_SUMMARY.csv`.

## 6. Unresolved remaining (`10_UNRESOLVED_REGISTER.csv`, `11_NOT_DETECTED_REGISTER.csv`)

**Concrete: 30 unresolved items, exposure 13.5 – 21.9 m³, never in a total.**

| Blocker | Items |
|---|---|
| Unbound bands | 13 |
| Necks without a footing / section match | 8 |
| Column types not in the schedule | 5 |
| Stair zones | 2 |
| Multiple-mark band | 1 |
| Free-column cell | 1 |

**Steel:**

- **28 ground beams are PARTIAL_MISSING**, with links as an unresolved item. The less-than-5 m class link read was rejected (EV-0007), and no links were read for the less-than-2.5 m class.
- **82 components have no bar quantity (MISSING_DATA).** Reasons, from `st7757_route_g/REBAR_COMPLETENESS.csv`:

| Reason | Components |
|---|---|
| Continuous-beam bars are per span, and the span order is not mapped | 25 (19 of them among the 89 historical components) |
| Slab panels with no bar tag inside | 25 |
| Beam bands without a section | 14 (13 unbound, 1 multiple-mark) |
| Necks: no FOUNDATION band for CN / no footing found | 6 / 2 |
| Column types not in the schedule | 5 |
| Stair-zone and free-column cells | 3 |
| Open-boundary panel (tags of the leaked cells not assignable) | 1 |
| Footing type conflict | 1 |

- **By family:** beams 39, slabs 27, ground beams 28 (partial), columns 13, ground slab 2, footings 1. Total 110 (`08_MISSING_STEEL_BY_FAMILY_STOREY.csv`).

**Families outside the core six:**

| State | Families |
|---|---|
| QUANTIFIED | blinding |
| PARTLY_QUANTIFIED | necks |
| COUNTED_IN_PARENT | cantilevers |
| DETECTED_NOT_QUANTIFIED, with the input each needs | lintels, pool, stairs, domes, water tank, parapets |
| NO_EVIDENCE_FOUND ("confirm absent") | lift, walls |

**The 89 historical components** (`07_REINFORCEMENT_COMPLETENESS_89.csv`):

- Identities are kept.
- PROVISIONAL_MODEL: 11 → 24. The 11 are confirmed unchanged.
- MISSING_DATA: 46 → 19 (the continuous-beam span order).
- Ground-beam components: 17 PARTIAL_MISSING (links of the short classes).
- Unmatched: 26 → 23.
- The 6 lift components stay OUTSIDE_SCOPE.

## 7. Differences against the frozen replay

| Family | M3 vs frozen | Explanation |
|---|---|---|
| Footings concrete | equal (66.26) | |
| Ground slab concrete | 16.78 vs 16.76 | |
| Columns | −1.04 m³ | 5 occurrences of types not in the schedule and 8 necks without a footing or section match are UNRESOLVED in M3 (13 items, exposure 1.54 – 5.51). The frozen replay measured several of them from its stage registers. |
| Beams | +6.18 m³ | By mark (`06_BEAMS_BY_MARK_VS_FROZEN.csv`, 63.31 m³ of marked frozen beams) the difference is +6.71 m³. **Marks where M3 has more items than the frozen replay: +5.60 m³.** These are mostly spans given to the collinear mark across a support (B23, B20, B15, B24) plus recovered pieces (CB8's third span +0.78, B27 +0.71). **Marks with the same item count: +2.78 m³.** These are length and width readings (B19 +0.74, B22 +0.53, B18 +0.38, 2F B7 +0.33, B13 +0.31, B11 +0.29). **Marks with fewer items: −1.67 m³.** CB10 −0.74: each of its two labels lies between a 0.20 m and a 0.30 m band, so neither binds (MARK_AMBIGUOUS; the bands are among the 13 unbound). CB3, GF B7 and CB5 are cut at supports. |
| Ground beams | +4.79 m³ | The exterior detail applies to all 24 bands with an outside side (generic rule). The frozen replay used its own S5 exterior candidates and held 8 spans unresolved. With every band at the typical class section the generic total is 31.15. |
| Slabs | +4.57 m³ | M2 was already +3.00 m³ over the frozen replay (thickness readings on untagged panels against the frozen thickness authority). M3 adds the GF panels closed by B27's faces, which M2 had leaked into the CB8 strip. It removes the 1F stair zone (17.13 m²) and the recovered beam strips. |
| Ground-beam steel | +3.40 t | The frozen replay has bars only for the spans its S5 stage released. M3 models the typical bars of every band and strap from the PDF evidence: provisional, low confidence, OCR-derived and unreviewed. |
| Beam steel | +2.07 t | M2 was already +1.39 t over the frozen BBS: the generic bar model uses 40 d anchorage at both ends and no curtailment. M3 adds the bars of the recovered and inherited beams (+0.68 t). |
| Column steel | −0.84 t | 13 absent occurrences, and generic laps against the frozen BBS. |
| Slab steel | −1.22 t | One-direction mesh from tags against the frozen S7 two-way model. |
| Blinding | +16.4 m³ | The frozen replay held footing blinding UNRESOLVED (thickness not printed). M3 reads "10cm Plain con." from p.13 (OCR, unreviewed) and adds a 0.10 m projection. |

## 8. Performance on unseen drawings (`13_HELDOUT_EVALUATION.json`)

The test set is 40 new layouts (seeds 501–540, never used before), each drawn three ways: clean, with drafting noise, and with the M3 real-bug defects. Each set was scored by both engines on the same files.

| Set | Engine | Success | Beam recall | Beam concrete MAE | Footing MAE |
|---|---|---|---|---|---|
| clean | M2 / M3 | 40 / 40 | 0.9975 / 0.9975 | 0.40 % / 0.40 % | 0 / 0 |
| drafting noise | M2 / M3 | 40 / 40 | 0.9975 / 0.9975 | 0.40 % / 0.40 % | 0 / 0 |
| M3 defects (157 stubs, 40 label-only footings) | M2 | 40 | **0.896** | **11.8 %** (max 31 %) | **8.0 %** |
| M3 defects | M3 | 40 | **0.9975** | **0.43 %** | **0** |

- Precision is 1.0 everywhere.
- The remaining 0.4 % beam error is M2's documented residual: the untagged span and a type missing from the schedule are unresolved by design.
- On the real set, accuracy against independent truth remains unknown: only comparison figures exist.

## 9. Tests

- The new M3 tests are in `tests/m3_recovery/`, one file per work package:
  - `test_m3_footings.py`
  - `test_m3_columns.py`
  - `test_m3_ground_beams.py`
  - `test_m3_detail_evidence.py` (includes the ST7757 p.13 real regression)
  - `test_m3_slabs_beams.py`
  - `test_m3_completeness_families.py`
  - `test_m3_reports.py` (this package)
- The M2 synthetic suite also exercises the M3 coverage states.
- Pass / fail / skip counts for each file, and for the full suite, are in `17_TEST_RUN.md`.

## 10. What remains before a reliable contractor BOQ

1. A person reviews the OCR-derived ground-beam bars (14 records with crops) and the blinding thickness note. Each becomes MANUALLY_CONFIRMED in the evidence file and drops the OCR blocker.
2. Answers to the RFIs in `19_RFIS.csv`:
   - the 49 m² cell
   - the stair extents
   - SB2's row
   - CB10's width
   - which ground beams are exterior, and the outer ground level
   - links of the short ground-beam classes
3. Continuous-beam bars by span: the span order along the beam line (25 components, 19 of them historical).
4. The families with no generic measurement: stairs (sections), lintels (architectural opening widths), pool, lift, water tank, parapets and domes (their details).
5. Independent ground truth for at least one real villa. The only real comparison is still with our own frozen replay; the 95 % target is not demonstrated.
