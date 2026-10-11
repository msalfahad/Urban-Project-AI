# Regression record: real failure → fix → test

**What this record covers**
- Each row is a failure seen on the real ST7757 set, or during M3 development, that the M2 engine (or an earlier M3 draft) got wrong.
- Each row gives the generic fix and the test that keeps it fixed.
- Tests use small synthetic drawings that reproduce the drafting pattern; they never use client geometry. The exception is `test_st7757_ground_beam_details`, which reads the private PDF and skips when it is absent.
- Test files are under `tests/m3_recovery/`.

## Footings (WP1)

| # | Failure | Fix | Test |
|---|---|---|---|
| R01 | Four footings had no quantity in M2 (NO_OUTLINE): FF and FN (type marks without a number), one outline opened by a strap entry, and the two-label footing of R02 - −16.2 m³ in all. | Polygon outlines; per-layer templates for outlines opened by a strap entry; a label beside its outline; a type mark without a number; label-only footings take the schedule size (`FOOTING_LABEL_ONLY`, outline not confirmed). | `test_m3_footings.py::test_every_footing_label_is_quantified_once`, `::test_quantities_by_hand` |
| R02 | One footing with no outline carried two type labels; M2 counted it under neither. | Quantified once (`FOOTING_LABEL_CONFLICT`: base the larger type, low the smaller), the second label held as `LABEL_TYPE_CONFLICT_SECONDARY`, a risk record and an RFI; its bars are MISSING_DATA (which type). | `test_m3_footings.py::test_bindings_and_risk_records` |

## Columns (WP2)

| # | Failure | Fix | Test |
|---|---|---|---|
| R03 | Twin outlines (drawn twice) made one label ambiguous. | Nested and duplicate outlines de-duplicated before binding. | `test_m3_columns.py::test_twin_outlines_do_not_make_labels_ambiguous` |
| R04 | A column-plan size equal to another band of the schedule was a false conflict. | Accepted when it equals any band of the type. | `::test_column_plan_size_is_no_false_conflict` |
| R05 | Columns counted on storeys where the roof plan shows none (13 occurrences). | Storey presence comes from the roof-slab plans; absent occurrences are not counted (`COLUMN_ABSENT_ON_STOREY_PLAN`). | `::test_storey_presence_from_the_roof_plan` |
| R06 | Necks were not measured. | A neck over its own footing, its height from printed levels; with no printed levels it stays UNRESOLVED with an exposure. | `::test_necks_over_their_own_footing`, `::test_necks_without_printed_levels_stay_unresolved` |
| R07 | A column-style mark in a beam table was read as a column. | The family comes from the table the row sits in. | `::test_a_column_mark_in_a_beam_table_is_a_beam` |

## Ground beams and straps (WP3)

| # | Failure | Fix | Test |
|---|---|---|---|
| R08 | Dotted marks (S.B2, G.B.1) were not read. SB2 has two schedule rows. | `DOTTED_MARK` with undotting. A duplicate row is bound by the drawn width (`BOUND_ROW_BY_DRAWN_WIDTH`, low confidence). | `test_m3_ground_beams.py::test_dotted_marks_and_duplicate_row_widths` |
| R09 | Strap beams were not measured. A first draft paired a footing's own two sides as a strap. | Straps between two different footings only, minus the footing plan. | `::test_straps_between_footings` |
| R10 | A 0.95 m slab strip on the GB plan was taken as a band. | GB-plan widths come from the schedule or the typical detail only; other drawn widths are rejected. | `::test_ground_beam_widths_are_source_supported` |
| R11 | Perimeter beams took the interior class section. | A band side facing outside takes the exterior detail. Depth comes from levels and build-up, with the class section as the low case. | `::test_perimeter_bands_take_the_exterior_detail` |
| R12 | Ground beams had 0 kg of steel. | Typical bars from the detail evidence (PROVISIONAL / LOW / OCR_DERIVED_UNREVIEWED). A missing role becomes an UNRESOLVED item and the component is PARTIAL_MISSING. Without evidence the state is MISSING_DATA, never 0 kg. | `::test_typical_bars_from_detail_evidence`, `::test_without_evidence_ground_beam_bars_stay_missing` |

## PDF evidence (WP4)

| # | Failure | Fix | Test |
|---|---|---|---|
| R13 | Two OCR reads agreed on `5016` where the drawing shows `3Ø16` (3 / 5 confusion). | Page-wide vector-glyph vote plus four reads per token; a read the glyphs contradict is rejected. | `test_m3_detail_evidence.py::test_glyph_votes_settle_the_3_5_confusion`, `::test_st7757_ground_beam_details` |
| R14 | `$8/15cm` and `30em` did not parse. | `$` added to the diameter glyphs; spacing accepts the `em` OCR misread. | `::test_notation_parses` (parametrised), `::test_notation_rejects` |
| R15 | Page 13 has 6 native words, and that stopped OCR. | OCR also runs on vector-glyph pages (paths > 20 × words). | `::test_native_text_pdf_needs_no_ocr`, `::test_st7757_ground_beam_details` |
| R16 | Link tokens were missed, and a missed link left the steel silently short. | Detail-region re-read above each caption. Rejected records are tracked, and missing roles become UNRESOLVED. | `::test_captions_and_assembly_roles`, `::test_st7757_ground_beam_details` |
| R17 | Owner and title-block text could enter a record. | Redaction before recording; `validate` refuses a record or note that matches. | `::test_validation_and_redaction` |
| R18 | No pathway existed when OCR is absent. | `OCR_UNAVAILABLE`, then manual transcription in the same schema; a raster page needs unanimous reads. | `::test_raster_pdf_without_ocr_goes_to_manual`, `::test_raster_pdf_ocr_needs_unanimous_reads` |

## Slabs and beams (WP5 / WP6)

| # | Failure | Fix | Test |
|---|---|---|---|
| R19 | Stair zones were counted as slab. | `tread_family` (FLIGHT or WINDER). A face that is ≥ 25 % treads is a STAIR_ZONE, UNRESOLVED with exposure. | `test_m3_slabs_beams.py::test_stair_zone_is_not_slab` |
| R20 | A ground-slab cell held a free-standing column. | That cell is UNRESOLVED (`SLAB_CELL_FREE_COLUMNS`). On a suspended slab the cell is counted and flagged. | `::test_free_column_on_a_suspended_slab_is_counted_and_flagged`, `::test_ground_slab_cells_closed_by_a_column_outline_and_free_column` |
| R21 | CB11 (1F, 2.85 m³) was dropped whole. A 10 mm intervening face made the pairing conflict. | `intervening_parts` keeps the parts of the strip clear of the stub. | `::test_strip_with_a_10mm_intervening_stub_is_recovered`; the held-out m3 set has 157 stubs |
| R22 | A shared face was dropped. A first single-face draft gave a false positive on CB5. | `shared_face_parts` keeps the unambiguous part. Single-face beams need one deduplicated face, a non-thin panel behind and none in front. | `::test_unambiguous_part_of_a_shared_face`, `::test_single_face_edge_beam` |
| R23 | CB8's inheritance was missed: the column outline stops 30 mm short of the gap. | Gap-on-support slack is 0.25 × width; inheritance bridges a support-filled gap. | `::test_inheritance_across_a_column_filled_gap` |
| R24 | B27 sits on its own named beam layer. | Named BEAM-role layers join the edge layers on one mark. | `::test_a_named_beam_layer_joins_on_one_mark` |
| R25 | An open-boundary face leaked into the CB8 strip. | The face keeps its panel part (face minus bands), PROVISIONAL / LOW, with steel MISSING_DATA. | `::test_open_boundary_panel_is_face_minus_bands` |

## Completeness and families (WP7 / WP8)

| # | Failure | Fix | Test |
|---|---|---|---|
| R26 | Missing steel was invisible: a component with no bars added 0 kg. | One rebar state per concrete component. Missing steel is counted by family and storey in BOQ section D, the MISSING_STEEL sheet and the PDF. | `test_m3_completeness_families.py::test_every_concrete_component_has_a_state_and_missing_steel_is_counted` |
| R27 | Blinding was not measured. | `_blinding_items` with projection; with no printed thickness it is UNRESOLVED with exposure. | `::test_blinding_under_every_footing`, `::test_blinding_without_a_printed_thickness_is_unresolved` |
| R28 | An absent family label read as "absent". | Family coverage states; NO_EVIDENCE_FOUND means "confirm absent". | `::test_family_coverage_states`; `tests/m2_generic_engine/test_synthetic_villas.py` (states updated) |

## Tooling (found while building this package)

| # | Failure | Fix |
|---|---|---|
| R29 | CLI `KeyError: 0`: the name `rc` was used for two things. | Renamed (`rcomp`). |
| R30 | Builder `KeyError 'TRADE'`. | `FAMILY_SUMMARY` uses lowercase keys. |
| R31 | The dashboard failed its own hygiene check on an output folder name. | Folder renamed `st7757_route_g`; SVGs inlined. |
| R32 | The synthetic stub was too short to have any effect (under the 0.3 m minimum face). | 0.41 m at line-end columns. |

These are guarded by `test_m3_reports.py` (the package checks) and the M2 suite.
