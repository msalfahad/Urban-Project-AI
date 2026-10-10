# christiannp forensic: recommendations (v2)

Rule: nothing is recommended because it brings a total closer to the freelancer or a donor. Nothing is implemented in this round.

## Production later

| Rank | Idea | Report basis | Problem solved | Generic implementation | Risk / false positives | Required tests | Trades |
|---|---|---|---|---|---|---|---|
| P0 | Candidate geometry when semantic authority is missing | the report keeps measurable strips, cells and faces | lost populations | scenario layers on every trade (coverage round) | low | blocked object with measured geometry publishes best > 0, official unchanged | all |
| P0 | Width gate (from R4) | R4 | wrong label binding | WIDTH_MISMATCH on the binding; re-assign only to an *adjacent* label; tolerance from drawing units | finish lines at beam width | `test_width_mismatch_flags_binding`, `test_reassignment_requires_adjacency`, `test_width_tolerance_scales_with_units` | beams, GB |
| P0 | Wall-face pairing with per-metre classification | wall pairing | unexplained wall gaps | `wall_band_reconciliation` as a required cross-route | finish-line pairs | door / column / duplicate / finish-line classification tests | blockwork, plaster |
| P0 | Physical wall faces before finishes | A10 / A13 counter-example | finish gating; storey-height faces | `physical_wall_faces`: interval − terminating member, per face, openings by evidence ladder | low | `test_wall_face_height_is_interval_minus_member` | finishes |
| P0 | Agreement class on every cross-route comparison | the donor-donor identities | false double confirmation | DONOR_AGREEMENT_CLASS on comparison rows; CONFIDENCE_UP only for INDEPENDENT_EXTRACTION_AGREEMENT | none | `test_identical_routes_do_not_raise_confidence`, `test_shared_assumption_agreement_never_confirms` | all |
| P0 | Version stamp on every comparison value | the 79 m vs 89.74 m confusion | old and new values mixed | ENGINE_COMMIT / REGISTER_VERSION / DRAWING_SHA / CALCULATION_ROUND required fields | none | `test_comparison_rows_carry_version_stamp` | all |
| P1 | CB occurrence-once per plan (from R1) | R1 | double-counted continuous beams | one occurrence per CB per plan; span excess = SPAN_LENGTH_CONFLICT, never truncation | hidden supports | `test_cb_allocated_once_per_plan`, `test_cb_span_excess_is_conflict_not_truncation`, `test_cb_width_match_ranks_before_length` | beams |
| P1 | Collinear continuation (from R2) | R2 | unlabelled continuations | CANDIDATE continuity: same width, stops at a support carrying a new tag | lintels, edge beams | `test_collinear_continuation_requires_same_width`, `test_continuation_stops_at_support_with_new_tag`, `test_continuation_is_candidate_not_verified` | beams |
| P1 | Ground-beam network comparison | GBP 85 / 42 / 200.036 | count-based comparisons | compare total length, node types (end / T / L / X), components and segmentation (bands vs spans) | none | `test_ground_beam_network_length_connectivity_segmentation` | GB |
| P1 | Footing outline / tag dual route | footing extraction | F3 / F-F10 / FN | reconcile each outline to one tag or a conflict record | low | `test_footing_outline_two_tags_is_source_conflict`, `test_irregular_footing_uses_polygon_area` | footings |
| P1 | Declared storey-boundary convention on column records | A2 / A3 | split disagreements read as errors | each record states its base and top levels and their authority | none | `test_column_storey_split_declared_and_total_conserved` | columns |
| P2 | ATTRIB-first schedule reading | report (schedule extraction) | text-matching errors | INSERT ATTRIB before TEXT, with pagination | low | ATTRIB wins over nearby TEXT | footings, columns, beams |

## Oracle-only

- **Independent Urban raster oracle** (`CHRISTIANNP_RASTER_METHOD_SPEC.json`). It uses the report's five classes plus OUTSIDE:
  - 100 / 50 / 25 / 10 mm resolutions, at two grid origins;
  - EDGE_LINE_CELLS reported, never allocated;
  - tests for convergence, origin shift, one-cell leaks, sub-cell voids and edge cells.
- **R3-style distance de-duplication**, for diagnostics only.
- **Donor totals and per-floor values**, only as post-freeze comparison rows carrying an agreement class.

## Reject completely

| Technique | Why |
|---|---|
| R5: equal sharing of leftover strip length | Arithmetic allocation without geometry. It hides missing strips and gives members the wrong lengths (and rebar). |
| R3 as production de-duplication | A fixed 2 m distance depends on drawing scale and merges distinct short beams. |
| A1 0.20 GF slab | The project default is 0.16 unless locally noted. |
| A5 0.60 ground-beam depth | Contradicts the printed interior sections; unsourced on the exterior. |
| A7 outline as slab-on-grade | Includes beam and column footprints; at most a HIGH scenario. |
| A8 CN continuation | Contradicts S1 chains and the human review. |
| A14 floor / ceiling = slab net area | Includes wall footprints and non-room area. |
| A15 roof WP without upturns | Incomplete. |
| A2 / A3 / A9 / A10 / A11 / A12 / A13 as defaults | Conventions or assumptions, not evidence. Urban uses ladders and declared conventions. |
| 22.916 t as a rebar comparison basis | KNOWN_INCOMPLETE_NET_DRAWING_REBAR (unresolved list in the report). |
| Copying unseen donor code (raster, pairing) | Not held, not licensed; rebuild independently. |

## Top 10 generic Urban improvements

1. Scenario-layer publication everywhere.
2. The width gate.
3. Wall-band reconciliation as a required cross-route.
4. Physical wall faces feeding finishes.
5. Agreement class plus version stamp on every comparison row.
6. CB occurrence-once with conflicts instead of caps.
7. Collinear continuation as a candidate.
8. Ground-beam network comparison: length, connectivity, segmentation.
9. Footing dual route.
10. The independent raster oracle (oracle only).
