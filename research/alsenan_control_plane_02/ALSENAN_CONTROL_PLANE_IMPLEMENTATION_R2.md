# Alsenan Accuracy Program — Round 2: Control Plane Implementation

Baseline `47dac56` (Round 1 audit). Branch `claude/access-permissions-setup-ii24ws`.

**Goal of this round.** Missing, review, partial, ambiguous or unread information must never quietly become a complete BOQ quantity. *Unknown is allowed. Unaccounted is not allowed.*

**What this round did not do:**
- It did not tune anything to the freelancer Excel.
- It did not implement the missing CB, strap, two-layer footing or stair reinforcement quantities.
- It did not change any geometry.
- It did not touch the frozen V3, V3b or Qortuba registers.
- It did not resolve any engineering question to make a gate pass.

## 1. Where things are

| Deliverable | Path |
|---|---|
| This report | `research/alsenan_control_plane_02/ALSENAN_CONTROL_PLANE_IMPLEMENTATION_R2.md` |
| Test run | `research/alsenan_control_plane_02/TEST_RUN.md` |
| Registers (frozen, sha256 in `registers/INDEX.json`, built twice and identical) | `research/alsenan_control_plane_02/registers/*.json` |
| Release V2 migration | `registers/RELEASE_V2_MIGRATION_REGISTER.json` |
| Trade dependency matrix | `registers/TRADE_DEPENDENCY_MATRIX.json` |
| Terminal object ledger | `registers/TERMINAL_OBJECT_LEDGER.json` |
| Structural source coverage V2 | `registers/STRUCTURAL_SOURCE_COVERAGE_V2.json` |
| Structural definitions V2 | `registers/STRUCTURAL_DEFINITION_REGISTER_V2.json` |
| Structural population coverage V2 | `registers/STRUCTURAL_POPULATION_COVERAGE_V2.json` |
| Wet-label accounting | `registers/WET_LABEL_ACCOUNTING_REGISTER.json` |
| Opening evidence V2 | `registers/OPENING_EVIDENCE_REGISTER_V2.json` |
| Wall-length conservation V2 | `registers/WALL_LENGTH_CONSERVATION_V2.json` |
| Legacy CAD migration | `registers/LEGACY_CAD_MIGRATION_REGISTER.json` |
| Calibration V2 | `registers/CALIBRATION_V2_REGISTER.json` |
| Gate transitions (with the superseded R1 tests) | `registers/GATE_TRANSITION_REGISTER.json` |
| Parallel candidate (old V3b qty and release beside V2) | `registers/ALSENAN_CONTROL_V2_CANDIDATE.json` (+ `ROOM_SPACES_V2.json`) |
| Post-freeze benchmark comparison | `research/alsenan_control_plane_02/POST_FREEZE_BENCHMARK_COMPARISON.json` |
| Runner, static registers, comparison | `build_control_v2.py`, `static_registers.py`, `post_freeze_compare.py` |

**How to rebuild.** Run `python3 research/alsenan_control_plane_02/build_control_v2.py <alsenan work dir | ctx.pkl> --twice`. Then run `post_freeze_compare.py`, which refuses to run if any register hash differs from `INDEX.json`.

The rebuilt V3b QA passes. The frozen `tests/alsenan/registers_v3b/BOQ_LINES_V3B.json` keeps its hash: it is read and never written.

## 2. Production changes

**Generic engines** (`engine/`, project-agnostic, stdlib only):

- **`engine/source/release_model_v2.py`** — Release Model V2.
  - States, ordered from least to most restricted:
    1. VERIFIED_COMPLETE
    2. VERIFIED_PARTIAL_LOWER_BOUND
    3. PROVISIONAL
    4. BUDGET
    5. BLOCKED
    
    NOT_IN_SCOPE sits apart from this order.
  - Fields: `release_state`, `population_complete`, `upstream_complete`, `procurement_eligible_v2`, `release_reason`, `blocking_refs`.
  - Confidence is derived from evidence: `evidence_grade`, `weakest_dependency`, `confidence_reasons`. It is never defaulted to H, and having no evidence components at all gives BLOCKED.
  - Upstream cap:
    - COMPUTED → VERIFIED_COMPLETE
    - REVIEW → PROVISIONAL
    - PARTIAL → LOWER_BOUND
    - anything else → BLOCKED
  - A blocked dependency gives BLOCKED. The number is kept only in `qty_audit`.
  - A lower bound is never procurement-eligible unless the owner explicitly approves it.
  - An Urban rule that only fixes the specification (`quantity_rule_dependency=False`) does not lower the release.
  - V1 (`technical.class`, `commercial.class`, `procurement_eligible_v1`) is kept unchanged alongside.
- **`engine/source/trade_dependency.py`** — `TRADE_DEPENDENCY_MATRIX`.
  - A trade is blocked by an unresolved semantic split only when the zones need different treatments for that trade. This gives `BLOCKED_SEMANTIC_TRADE_BOUNDARY`.
  - An established void outline resolves the VOID split.
  - No wall is invented.
- **`engine/source/terminal_ledger.py`** — admit / terminate / check (unterminated, double or unknown terminations).
- **`engine/source/opening_evidence.py`** — count, width, height, area, function and material each carry their own state.
  - Area is never more certain than width and height.
  - There is no default height.
  - A window with a low sill or tall height is a `GLAZED_DOOR_CANDIDATE`, so its function is BLOCKED.
- **`engine/source/calibration_v2.py`** — UNIFORM, XY and AFFINE calibration (AFFINE needs at least 4 anchors and is solved by least squares).
  - The result is decomposed into sx, sy, rotation, shear and reflection.
  - An unobserved axis is never copied from the other axis.
  - A measurement cites its `calibration_id` and the axis it was taken along.
- **`engine/source/schedule_grammar.py`** — bar grammars:
  - COUNT_DIA_AT_SPACING
  - DIA_AT_SPACING
  - COUNT_DIA_PER_M
  - COUNT_DIA_POSITION
  - COUNT_DIA
  - UNPARSED
  
  It also provides cell provenance and `key_conflicts` (SOURCE_CONFLICT_DUPLICATE_SCHEDULE_KEY).
- **`engine/legacy_cad_guard.py`** — `require_legacy_opt_in()`. It exits with code 2 unless `--allow-legacy-cad-adapter` or `URBAN_ALLOW_LEGACY_CAD_ADAPTER=1` is given.

**Alsenan lab code** (`research/external_engine_lab/`):

- **`alsenan_v3_layers.py`**
  - `_room_class` returns `MIXED_SEMANTIC_ZONE` when the names in one space have different classes. The old "DRY wins" rule is gone.
  - Room and finish rows carry the TS01 `semantic_state`, `semantic_zones` and `zone_classes`.
  - A mixed room gets no default material.
- **`alsenan_v3_registers.py`**
  - `ROOM_STATUS_CAP` and `propagate()` are applied to floor, skirting, threshold, ceiling, cornice, plaster, paint, wall tile and waterproofing.
  - Mixed zones with a wet or service class emit BLOCKED T-WT and T-WP lines instead of dropping them.
  - A blockwork group with zero area is BLOCKED.
  - The `_det` fallbacks are fixed.
- **`alsenan_v3_structure.py`** — `terminal()` records:
  - **Footings:**
    - `REBAR_BLOCKED_CONCRETE_NOT_ESTABLISHED`
    - `REBAR_BLOCKED_NO_DEFINITION`
    - `REBAR_BLOCKED_SCHEDULE_CELL_UNREAD` (FF)
    - `REBAR_BLOCKED_PER_METRE_PENDING_CONSUMER_V2` (per-metre sets, and the FTB bottom layer that A3 stored under "boxed")
  - **Columns:**
    - `REBAR_BLOCKED_NO_DEFINITION`
    - D5 `REBAR_BLOCKED_OCCURRENCE_NOT_ESTABLISHED`, with audit vertical and tie kg
  - **Beams:**
    - `REBAR_BLOCKED_PENDING_REBAR_CONSUMER_V2` (CB)
    - `NO_DEFINITION`
    - `OCCURRENCE_NOT_MEASURED`
    - `LENGTH_MISSING`
  - **Straps:** `REBAR_BLOCKED_NO_CONSUMER` from the new `strap_rebar()`.
  - **Openings:** PARTIAL whenever the height is not established.
  - **Lintels:** blocked lintels keep their floor, so the C-LINT line can no longer claim COMPUTED. Lintel rebar is `REBAR_BLOCKED_LINTEL_NOT_ESTABLISHED`.
  - **Blockwork:** ambiguous bands give `BLOCKWORK_BLOCKED_AMBIGUOUS_BAND`; missing faces give `BLOCKWORK_BLOCKED_FACE_GEOMETRY_MISSING`.
- **`alsenan_v3b_lines.py`**
  - `measured_qty` is kept for lines outside the total.
  - The `cap_by_room_status()` choke point stops V3b re-derivations from losing the room status. This was found this round: `T-WP-FLOOR-GF-Z04` came back COMPUTED 155.655.
  - BLOCKED V3a wet lines are carried through.
- **`alsenan_structural_source_v2.py`** (new) — ST7757.dxf attribute blocks (FT, FTB, SBT, C-BEAM2, C-BEAM3, CGT), together with loose texts and PDF-only pages.
  - Output: 332 source objects, 77 definitions, the SB2 conflict and 23 side-bar remarks.
  - T/M and LOAD are design loads, never reinforcement.
  - `(T&B)` is a TOP_AND_BOTTOM candidate with no multiplication.
  - Pages 8 and 13–16 are BLOCKED_UNREAD: they are raster or vector glyphs with no text.
- **`alsenan_control_v2.py`** (new) — the ALSENAN_CONTROL_V2 candidate and all the registers above.

**Tools.** Seventeen user CLIs that can reach `engine/cad_adapter.py` now call the guard on the first line of `main()`. Historical code is not deleted.

**Qortuba.** No change: RC1_REFERENCE is not patched.

**Tests:**
- `tests/alsenan_control_plane/test_control_plane_r2_engines.py` — 35 tests.
- `tests/alsenan_control_plane/test_control_plane_r2_gates.py` — 37 tests: 33 passed and 4 strict-xfail.
- `test_control_plane_r1.py` — the superseded tests listed in `GATE_TRANSITION_REGISTER.superseded_round1_tests` are removed. The frozen-data tests stay. The R1 register rebuild skips only the live-code `LEGACY_CAD_REACHABILITY_REGISTER`.

## 3. Quantities changed only by release status

The migration register has one row per line: 395 rows in total.

| Change kind | Lines |
|---|---|
| UNCHANGED | 207 |
| RELEASE_ONLY (same number, new release) | 177 |
| MEASUREMENT_AND_RELEASE | 5 |
| NEW_LINE (BLOCKED, no number) | 6 |

**The five MEASUREMENT_AND_RELEASE lines** are rebar lines whose blocked sets moved out of the total into explicit BLOCKED records. No geometry changed. The differences reconcile exactly:
- **R-COLUMNS** (GF, 1F, 2F_ROOF): 5329.857 → 3590.202 kg. The drop of **1739.655 kg** is the 26 D5 occurrences (`d5_excluded_from_verified.audit_kg` = 1739.651, verticals plus ties).
- **R-FOOTINGS-GF:** 1132.674 → 887.093 kg. The drop of **245.581 kg** is the four per-metre sets (F8, F12, F13, F14).
- **R-BBS-PURCHASED-TECH:** 15323.555 → 13161.482 kg. The drop of 2162.07 kg is the 1985.2 kg net above plus the laps and cutting offcut of those sets.

The NEW_LINE rows are:
- T-WT and T-WP for GF-Z04 and GF-Z06 (BLOCKED_SEMANTIC_TRADE_BOUNDARY);
- B-150-UNR-GF and B-400-UNR-GF (blocked blockwork).

**Release transitions on changed lines:**

| Old class → V2 state | Lines |
|---|---|
| URBAN_STANDARD → PROVISIONAL | 71 |
| BLOCKED (with commercial provisional) → PROVISIONAL | 46 |
| PARTIAL → LOWER_BOUND | 31 |
| DERIVED → PROVISIONAL | 13 |
| DERIVED → LOWER_BOUND | 12 |
| → BLOCKED | 8 |
| CODE_METHOD → PROVISIONAL | 1 |

Procurement-eligible lines: V1 249 → V2 89, all of them VERIFIED_COMPLETE.

## 4. Identical geometry values

The rebuilt V3a lines were compared with the frozen `registers_v3/BOQ_LINES.json` (`v3a_measurement_identity`):

| Result | Lines | Meaning |
|---|---|---|
| IDENTICAL | 254 | |
| STATUS_ONLY | 56 | Same number, status capped: room status, lintel, mixed zones |
| NUMBER_CHANGED | 11 | All rebar NET / PROC / STRAIGHT lines for columns and footings, explained by the D5 and per-metre sets above |
| NEW | 11 | BLOCKED, with no number |

No floor, wall, ceiling, opening or concrete geometry value changed. This is asserted in `test_no_gaming_geometry_identical_to_frozen_v3a`.

## 5. Gates (§22 evidence)

For each gate the table gives the old failure, the production change, the new behaviour, the real Alsenan evidence and the test that proves it. The source is `registers/GATE_TRANSITION_REGISTER.json`, generated from `static_registers.py`. A test asserts that the register equals the static definition and that every proving test exists.

**PASS (19):** G01–G10, G12, G14, G16–G22.

**Strict XFAIL (4)**, by design, so that an XPASS turns red:
- **G11** — the per-metre two-layer footing quantity consumer is Round 3 work.
- **G13** — the strap-beam rebar consumer is Round 3 work, and SB2 is in source conflict.
- **G15** — the D6 ground-zone binding needs the engineer's answer to Q-S4. Unchanged.
- **G23** — the page-16 stair layout is vector glyphs, and its applicability is unproved.

**Semantics corrected** (the R1 gate asked for a forced classification or a zero counter; R2 asks for accounting):

| Gate | R1 asked for | R2 asks for |
|---|---|---|
| G04 | wet labels forced into rooms | every label ends in a terminal state |
| G08 | parse success | a terminal coverage state, with interpretation reported separately at 47.9 % |
| G09 | a zero counter | every population has a terminal state |
| G16 | ambiguous length = 0 | raw = accounted, unaccounted = 0, blockwork at LOWER_BOUND |
| G17 | unpaired boundary = 0 | the same accounting as G16 |
| G20 | BOXED interpreted | BOXED captured raw, with BLOCKED_SEMANTICS |
| G21 | side bars in bar definitions | remarks as typed tokens with a pending consumer |

**No-gaming tests** pin the raw counts that were not zeroed:
- 46.63 m of ambiguous wall;
- 187.82 m of unpaired boundary;
- 35 wet labels;
- 26 D5 occurrences;
- 332 source objects.

| Gate | Defect | State | Old failure | Production change | New behaviour | Real Alsenan evidence | Proving test |
|---|---|---|---|---|---|---|---|
| G01 | C-1 | PASS | R1: 325.251 m2 of COMPUTED_REVIEW room floor released as COMPUTED (registers.py 'COMPUTED' if .. else 'COMPUTED') | alsenan_v3_registers.propagate(): every room-derived line is capped by its room status; alsenan_v3b_lines.cap_by_room_status() caps V3b re-derivations | a COMPUTED_REVIEW room yields REVIEW lines (V1) and at most PROVISIONAL (V2) | RELEASE_V2_MIGRATION_REGISTER: no F-FL line of a non-COMPUTED room is VERIFIED_COMPLETE | `test_G01_review_room_floor_never_verified` |
| G02 | B-1 | PASS | R1: TS01 MULTI_UNRESOLVED zones released as one clean zone | rooms carry TS01 semantic_state; ALSENAN_CONTROL_V2 evaluates every room trade through TRADE_DEPENDENCY_MATRIX | split-dependent trades of GF-Z04 / GF-Z06 are BLOCKED_SEMANTIC_TRADE_BOUNDARY; no line of an unresolved space is VERIFIED_COMPLETE | GF-Z04 floor 155.655 BLOCKED (audit), GF-Z06 floor 24.94 BLOCKED | `test_G02_unresolved_semantic_space_never_released_as_one_clean_zone` |
| G03 | B-2 | PASS | R1: _room_class('DEWANEYA / Wash') == 'DRY' (DRY wins) | alsenan_v3_layers._room_class returns MIXED_SEMANTIC_ZONE for names of different classes | mixed spaces get no default dry material and no dry-only quantity | GF-Z04, GF-Z06, 1F-Z06 = MIXED | `test_G03_dry_wins_removed` |
| G04 | J-1 | PASS (semantics corrected) | R1 gate asked wet_rooms_lost == [] (forces labels into rooms) | WET_LABEL_ACCOUNTING_REGISTER: every wet label ends in a terminal state; mixed-zone wet trades emit BLOCKED lines (registers.tile_wp) | unaccounted_wet_labels == []; blocked labels keep the wet population incomplete | 35 labels: 25 bound, 5 blocked semantic boundary, 4 blocked no physical site, 1 not in scope (pool) | `test_G04_every_wet_label_accounted` |
| G05 | C-2 | PASS | R1: skirting hard-coded COMPUTED | propagate() on F-SK | skirting follows room status | F-SK lines of review rooms REVIEW | `test_G05_skirting_status_propagates` |
| G06 | C-3 | PASS | R1: ceiling hard-coded COMPUTED | propagate() on CE | ceiling follows room status | CE lines of review rooms REVIEW | `test_G06_ceiling_status_propagates` |
| G07 | D | PASS (V2 field) | R1: release('PARTIAL') procurement_eligible (V1) | engine/source/release_model_v2: PARTIAL -> VERIFIED_PARTIAL_LOWER_BOUND, never procurement eligible without owner approval; V1 kept as procurement_eligible_v1 | lower bounds shown '>= q', not procurable by default | every VERIFIED_PARTIAL_LOWER_BOUND line has procurement_eligible_v2 = False | `test_G07_partial_never_procurement_eligible_v2` |
| G08 | E-1 | PASS (semantics corrected) | R1 gate asked every source object CONSUMED_COMPLETE (parse success) | alsenan_structural_source_v2 + STRUCTURAL_SOURCE_COVERAGE_V2: every admitted source object has a terminal coverage state; interpretation reported separately | accounting 100 %, interpretation < 100 % stated | 332 source objects accounted | `test_G08_every_structural_source_object_has_a_terminal_state` |
| G09 | F-1 | PASS (semantics corrected) | R1 gate asked zero silent occurrences only via a register count | production terminal records (alsenan_v3_structure.terminal) + STRUCTURAL_POPULATION_COVERAGE_V2 + ledger | every concrete / rebar occurrence ends in a terminal state; BLOCKED allowed | ledger conserved | `test_G09_every_structural_population_has_a_terminal_state` |
| G10 | D1 | PASS (definitions only) | R1: no CB definition in any register | STRUCTURAL_DEFINITION_REGISTER_V2 reads C-BEAM2 / C-BEAM3 ATTRIBs | 13 typed CB definitions; CB rebar populations stay BLOCKED (REBAR_BLOCKED_PENDING_REBAR_CONSUMER_V2) | CB1-CB13 | `test_G10_cb_definitions_captured_from_source` |
| G11 | D2 | XFAIL (by design this round) | per-metre footing counts used as bar counts | per-metre sets now BLOCKED terminal records (no wrong kg released) | quantity consumer is Round 3 | F8 / F12 / F13 / F14 BLOCKED | `test_G11_two_layer_footing_quantity_consumer` |
| G12 | D3 | PASS | R1: FF emitted nothing | footing_rebar emits REBAR_BLOCKED_SCHEDULE_CELL_UNREAD | FF has a blocked population row | FF #? BLOCKED | `test_G12_ff_emits_a_blocked_population` |
| G13 | D4 | XFAIL (by design this round) | straps filtered out | strap_rebar emits REBAR_BLOCKED_NO_CONSUMER terminals (accounted) | strap quantity consumer is Round 3 | SB1-SB3 BLOCKED | `test_G13_strap_rebar_quantity_consumer` |
| G14 | D5 | PASS | R1: 1,739.7 kg on 26 occurrences with no concrete | column_rebar emits REBAR_BLOCKED_OCCURRENCE_NOT_ESTABLISHED with the kg in audit only | no verified rebar without an established occurrence | 26 occurrences BLOCKED | `test_G14_no_verified_rebar_without_an_established_occurrence` |
| G15 | D6 | XFAIL (owner / engineer question Q-S4) | min-area ground binding | none this round | unchanged | - | `test_G15_ground_zone_not_bound_by_minimum_area` |
| G16 | I-1 | PASS (semantics corrected) | R1 gate asked ambiguous_m == 0 | blockwork() writes BLOCKWORK_BLOCKED_AMBIGUOUS_BAND rows; WALL_LENGTH_CONSERVATION_V2 | raw 46.63 m kept; accounted 46.63; unaccounted 0; blockwork LOWER_BOUND | 13 ambiguous bands | `test_G16_ambiguous_wall_length_accounted_not_erased` |
| G17 | I-2 | PASS (semantics corrected) | R1 gate asked unpaired boundary == 0 | every boundary item outside a band is classified in the ledger | raw 187.82 m kept as AMBIGUOUS_BLOCKED; glazing / obstacle edges classified; unaccounted 0 | 772 unpaired items | `test_G17_unpaired_boundary_accounted` |
| G18 | K-1 | PASS | R1: 59 V3a openings COMPUTED with a BLOCKED height | openings() rows PARTIAL with per-attribute states; OPENING_EVIDENCE_V2 | area never more certain than height | 0 COMPUTED-with-blocked-height | `test_G18_opening_area_never_computed_with_blocked_height` |
| G19 | SD-12 | PASS | R1: SB2 duplicate kept silently | schedule_grammar.key_conflicts in the V2 reader | SOURCE_CONFLICT_DUPLICATE_SCHEDULE_KEY with both rows; SB2 population BLOCKED | SB2 80x50 / 100x50 | `test_G19_duplicate_sb2_is_an_explicit_conflict` |
| G20 | SD-08 | PASS (semantics corrected) | R1 gate asked BOXED interpreted | FT definitions keep raw_boxed_value + BLOCKED_SEMANTICS; affected footings LOWER_BOUND | captured, not guessed | 11 FT types | `test_G20_boxed_captured_and_accounted` |
| G21 | SD-11 | PASS (semantics corrected) | R1 gate asked side bars in bar definitions | REMARKS bound to rows as typed tokens (TOKENS_PARSED_SEMANTICS_CANDIDATE) | accounted; no kg added | 23 beams B7-B29 | `test_G21_side_bar_remarks_accounted` |
| G22 | O-1 | PASS | R1: tools/run_cad_pipeline.py reaches cad_adapter unguarded | engine/legacy_cad_guard.py called first in main() of 17 tools | refusal (exit 2) without explicit opt-in | 17 / 17 user CLIs guarded | `test_G22_user_cli_legacy_adapter_guarded` |
| G23 | SD-17 | XFAIL (applicability unproved) | stair rebar BLOCKED | none (page-16 layout captured as BLOCKED_UNREAD source object, not applied) | unchanged | - | `test_G23_stair_rebar_bound_to_typical_layout` |

## 6. Totals by trade: V2 release beside the old V3b technical total

The table below is `ALSENAN_CONTROL_V2_CANDIDATE.totals_by_trade_unit`. R-BBS and `no_total` lines are excluded. "Blocked audit" is a number kept only for audit; it is never released.

| Trade / unit | Verified complete | Lower bound (≥) | Provisional | Budget | Blocked audit | Blocked lines | Old V3b technical |
|---|---|---|---|---|---|---|---|
| ALUMINIUM_OPENINGS / lm | 77.629 | 35.767 | 0.000 | 0.000 | 0.000 | 0 | 113.396 |
| ALUMINIUM_OPENINGS / m2 | 52.022 | 44.971 | 10.206 | 5.481 | 0.000 | 0 | 96.993 |
| ALUMINIUM_OPENINGS / nr | 60.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 60.000 |
| BLOCKWORK / m2 | 184.708 | 518.316 | 156.508 | 0.000 | 0.000 | 2 | 703.024 |
| CEILINGS / m2 | 121.973 | 0.000 | 185.601 | 0.000 | 139.650 | 2 | 447.224 |
| CONCRETE / m3 | 157.694 | 125.146 | 62.840 | 7.950 | 0.000 | 1 | 282.840 |
| FLOORING / lm | 57.798 | 0.000 | 152.917 | 0.000 | 101.585 | 2 | 312.300 |
| FLOORING / m2 | 122.373 | 0.000 | 291.913 | 0.000 | 180.595 | 2 | 447.744 |
| PLASTER_PAINT / lm | 0.000 | 84.920 | 0.000 | 0.000 | 0.000 | 0 | 84.920 |
| PLASTER_PAINT / m2 | 181.831 | 0.000 | 7,830.079 | 0.000 | 0.000 | 5 | 181.831 |
| REBAR / kg | 2,312.617 | 16,353.514 | 4,623.577 | 319.113 | 0.000 | 1 | 20,651.366 |
| STAIRS_RAILINGS / lm | 14.290 | 0.000 | 74.324 | 0.000 | 0.000 | 0 | 14.290 |
| STAIRS_RAILINGS / m | 0.300 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0.300 |
| STAIRS_RAILINGS / m2 | 0.000 | 0.000 | 30.532 | 0.000 | 0.000 | 0 | 0.000 |
| WALL_TILE_WATERPROOFING / lm | 0.000 | 0.000 | 96.064 | 0.000 | 0.000 | 0 | 96.064 |
| WALL_TILE_WATERPROOFING / m2 | 489.249 | 0.000 | 1,764.644 | 0.000 | 0.000 | 4 | 1,005.006 |

A lower VERIFIED total is not a regression. It is the questionable part of the old technical total moving into LOWER_BOUND, PROVISIONAL or BLOCKED. Examples:
- **Rebar:** 18,666 kg is verified or lower bound. The 1,985 kg difference from the old 20,651 kg is exactly the D5 and per-metre sets.
- **Floor:** 447.744 m² = 122.373 verified + 144.656 provisional (review rooms) + 180.595 blocked audit (GF-Z04 and GF-Z06, semantic split), plus the remaining threshold and other provisional lines.

## 7. Structural source objects (ST7757)

There are 332 admitted objects, and every one is accounted for (accounting 100 %).

| Coverage state | Objects |
|---|---|
| CONSUMED_COMPLETE | 52 |
| CONSUMED_PARTIAL | 271 |
| SOURCE_CONFLICT (the two SB2 rows) | 2 |
| BLOCKED_UNREAD | 7 |

The seven BLOCKED_UNREAD objects are pages 8, 14, 15 (×3) and 16 (×2). Their content is raster or vector glyphs with no text layer.

**Interpretation is reported separately, at 47.9 %:**

| Interpretation state | Objects |
|---|---|
| INTERPRETED | 159 |
| BLOCKED_INTERPRETATION | 117 |
| PARTIALLY_INTERPRETED | 27 |
| TOKENS_PARSED_SEMANTICS_CANDIDATE (side-bar remarks) | 23 |
| CANDIDATE_TOP_AND_BOTTOM (`(T&B)`, no multiplication) | 4 |
| CONFLICT | 2 |

**77 definitions** (definitions only; none feeds a released quantity):
- CONTINUOUS_BEAM: 13, all PARTIALLY_INTERPRETED (T/M is a design load, not reinforcement);
- SIMPLE_BEAM: 31;
- STRAP_BEAM: 2 interpreted plus 2 in CONFLICT (SB2: 80×50 against 100×50, neither row chosen);
- FOOTING: 11 partial, with BOXED kept raw as BLOCKED_SEMANTICS, plus 1 interpreted;
- FOOTING_2_LAYER (FTB): 5;
- COLUMN: 12.

## 8. Structural populations

Occurrences:

| State | Occurrences |
|---|---|
| Complete | 4 |
| Partial (lower bound) | 132 |
| Blocked | 58 |
| Not required (column type has no section in that storey) | 31 |

**The 58 blocked occurrences:**
- **Footings (7):** 2 with concrete not established, 1 FF schedule cell unread, and 4 per-metre sets pending the consumer.
- **Beams (10):** 8 with the length missing, which were silent before this round, and 2 not measured.
- **CB:** 11, pending the consumer.
- **Columns:** 26, from D5. Audit 1739.65 kg; excluded from verified.
- **Lintel:** 1.
- **Straps:** 3, with no consumer.

**Population rows:**
- VERIFIED_COMPLETE: GROUND_SLAB, POOL.
- PROVISIONAL: BEAM_RESIDUE, BEAM_SIDE_BARS, BOUNDARY_WALL, COLUMN_STARTERS, DOME, FOOTING_F_F10, GROUND, GROUND_BEAM_EXT, SLAB.
- BLOCKED: STAIRS.

## 9. Silent disappearances remaining

`TERMINAL_OBJECT_LEDGER` admits 1,998 quantity-bearing objects and terminates 1,998. There are no unterminated, double-terminated or unknown terminations:
- 395 BOQ lines;
- 332 source objects;
- 772 unpaired boundary items;
- 137 wall bands;
- 105 columns;
- 78 beams;
- 60 openings;
- 35 wet labels;
- 30 rooms;
- 27 footings;
- 11 CB;
- 3 straps;
- 1 lintel;
- 12 population rows.

**Inside the admitted set: zero.** Three known residuals are not disappearances, and I state them so none is hidden:
1. **D6 (G15)** binds the ground zone to the smallest containing cell. This is a possible mis-binding, not a drop. It is unchanged pending Q-S4.
2. **Non-per-metre "boxed" footing rows** still emit a generic BLOCKED row ("boxed bar shape not dimensioned"). The row is visible, but it carries no specific terminal-state code.
3. **The seven PDF-only objects** are accounted for as whole pages or details. Their inner content (for example, the page-15 temperature-steel rule) is captured, but it is not enumerated bar by bar.

## 10. Wet labels

Thirty-five labels are all accounted for; `unaccounted_wet_labels == []`.

| Terminal state | Labels | Which |
|---|---|---|
| BOUND_TO_REGION | 25 | |
| BLOCKED_SEMANTIC_TRADE_BOUNDARY | 5 | GF-Z04: تحضير, PANTRY, Wash, مغسلة. GF-Z06: Wash |
| BLOCKED_NO_PHYSICAL_SITE | 4 | 1F: W.C, مرحاض, BATH, حمام |
| NOT_IN_SCOPE | 1 | حمام سباحة, the pool. It is measured by the pool population |

`wet_trade_population_complete = false`, so no project wall-tile or waterproofing total is VERIFIED_COMPLETE.

## 11. Wall length

| | GF | 1F | 2F | Total |
|---|---|---|---|---|
| Masonry 150 (m) | 26.094 | 42.713 | 8.700 | 77.51 |
| Masonry 200 (m) | 38.861 | 28.881 | 21.998 | 89.74 |
| Excluded with reason (m) | 14.035 | 14.035 | 14.035 | 42.10 |
| Ambiguous: raw = accounted (m) | 32.062 | 14.568 | 0 | **46.63** (unaccounted 0) |
| Unpaired topology boundary: raw = blocked (m) | 112.747 | 50.765 | 24.309 | **187.82** (unaccounted 0) |
| Other boundary items classified (glazing / RC interface) (m) | | | | 437.44 in total |
| Blockwork release | LOWER_BOUND | LOWER_BOUND | LOWER_BOUND | |

Blockwork: 184.708 m² verified, ≥ 518.316 m² lower bound, 156.508 m² provisional, and 2 lines BLOCKED.

## 12. Openings

There are 60 openings. Each attribute carries its own state:

| Attribute | Verified | Provisional | Blocked |
|---|---|---|---|
| Count | 60 | | |
| Width | 59 | | 1 |
| Height | 12 | 47 | 1 |
| Area | 12 | 47 | 1 |
| Function | 36 | | 24 |

- The 24 blocked functions are glazed-door candidates; they stay unresolved.
- Material is PROVISIONAL (by specification) unless it has a source.
- **V3a records that are COMPUTED with a BLOCKED height: 0.** In Round 1 there were 59.

## 13. Calibration V2

All six raster sheets are re-expressed as XY calibrations from the same level-chain observations: `AXIS_NOT_OBSERVED` / `X_NOT_OBSERVED`. They reproduce the legacy px/cm to a relative difference of at most 1e-9. Heights along Y stay valid. **No Alsenan quantity is recomputed.** The finding is that a raster width taken along X has no observed X scale.

## 14. Benchmark firewall and post-freeze comparison

- The control builders never reference a benchmark register; this is tested by `test_benchmark_firewall`.
- `post_freeze_compare.py` ran after `INDEX.json` was frozen. It verified every hash first.
- It reuses the V3b evaluation's own line selection, and it proves the selection is identical: the old V3b technical total per item matches `BENCHMARK_EVALUATION_V3B` exactly.
- Every difference is recorded as FINDING_ONLY. Nothing was tuned.

## 15. Tests

**Command:** `python3 -m pytest -p no:cacheprovider -rfE --junitxml=…`, run from the repository root on the working tree that is committed. Exit status 0, in 323.8 s.

| Suite | Passed | Failed | Xfailed | Xpassed | Skipped |
|---|---|---|---|---|---|
| **Full suite** | **5,869** | **0** | **96** | **0** | **3** |
| Control plane (`tests/alsenan_control_plane`) | 89 | 0 | 4 (G11, G13, G15, G23) | 0 | 0 |
| Alsenan (`tests/alsenan`) | 304 | 0 | 0 | 0 | 0 |
| Qortuba RC1 (`tests/rc1`) | 37 | 0 | 0 | 0 | 0 |
| R8 (`tests/r8_*`) | 1,852 | 0 | 92 | 0 | 1 |

The three skips are the same as at baseline:
- the real-source row (`URBAN_R8_REAL_SOURCE` is unset);
- `QS_MEASUREMENT_REGION_BUILDER` is absent (×2).

There are no Qortuba or R8 regressions. RC1_REFERENCE and every frozen V3, V3b and Qortuba register are untouched (`git status` shows no change under `tests/rc1`, `tests/alsenan/registers*`, or the Qortuba registers).

**Change from Round 1** (5,933 tests: 5,815 passed, 115 xfailed, 3 skipped) to **Round 2** (5,968 tests: 5,869 passed, 96 xfailed, 3 skipped):

| Change | Tests | Passed | Xfailed |
|---|---|---|---|
| Removed: R1 tests superseded (14 characterisation tests and 23 R1 gates) | −37 | −14 | −23 |
| Added: `test_control_plane_r2_engines.py` | +35 | +35 | |
| Added: `test_control_plane_r2_gates.py` | +37 | +33 | +4 |
| **Net** | **+35** | **+54** | **−19** |

**No XPASS was produced, and no assertion was weakened.** The R1 gates were not turned into passes. They are superseded by R2 gates that assert production behaviour and the R2 registers. The four R2 xfails are `strict=True`.

## 16. Round 3 recommendation

The work below is to be reviewed by ChatGPT and Mohammad first. No D1–D4 quantity is implemented until that review.

**1. D1 — continuous-beam (CB) consumer.**
- The 13 definitions are already captured: bottom bars per span, MID and top bars, STR1/STR2 stirrups by zone, and spans.
- What is needed:
  - an occurrence-to-span binding for the 11 CB occurrences;
  - the anchorage and lap rule from the typical CB detail.
- The engineer must confirm the stirrup zone lengths.
- Gate: a new G24 "CB rebar from source, per span", with a strict xfail until then.

**2. D2 — two-layer footing (FTB) consumer.**
- For each layer, bar count = ceil(span × n per metre) + 1, with both the top and bottom layers.
- This applies to F8, F12, F13, F14 and FF.
- FF needs the page-14 lift-footing detail transcribed by hand from the PDF. That transcription must be recorded as a human claim, not parsed.
- G11 turns PASS only through this consumer.

**3. D4 — strap-beam consumer.** For SB1 and SB3. SB2 stays BLOCKED until the engineer answers which row (80×50 or 100×50) governs. That is a question, not a rule.

**4. D5 — the 26 column occurrences.** Establish their concrete (storey sheet or column schedule) or keep them BLOCKED. Their 1,739.65 kg stays in audit until then.

**5. Owner and engineer questions, not code:**
- **Q-S4:** the D6 ground-zone binding (G15).
- **Wet-zone extents in GF-Z04 and GF-Z06:** an owner dimension or a sketch would lift BLOCKED_SEMANTIC_TRADE_BOUNDARY for tile and waterproofing.
- **The 1F BATH / W.C closure:** a missing physical site, so this is a geometry closure fix that comes back through the frozen-control path.
- **Page-16 stairs:** an engineer's confirmation that the typical layout applies (G23).

**6. Calibration.** Add horizontal anchors (grid or dimension strings) before any raster width along X is used. The Y-only sheets stay height-only.

**7. Keep V2 parallel.** ALSENAN_CONTROL_V2 stays a candidate beside the frozen V3b until the owner accepts the release-state presentation, with lower bounds shown as "≥ q" and not procurable.

**Then STOP.** This round implemented control, accounting and release safety only.
