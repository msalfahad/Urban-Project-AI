# S3.1: generic engine improvements and the Alsenan multi-engine structural comparison

Baseline: `b6a8fef` (S3 test-run record). Comparison only: no Urban production quantity was changed by any
comparison source. Footing rebar was **not** started.

## Order of work (benchmark firewall)

1. Generic modules + synthetic tests (no project numbers in `engine/source`; the §26 firewall test enforces it).
2. S3.1 column rerun (`research/alsenan_column_rebar_s3_1`), built twice byte-identical.
3. `URBAN_PRODUCTION_FREEZE.json` written with the hashes of every production register the comparison reads,
   **before** the freelancer workbook was opened (`freelancer_workbook_opened_before_this_record: false`).
4. Comparison build: it re-checks the freeze, then traces the FREELANCER_QS_REFERENCE workbook and the recorded
   oracle values.

## Generic modules (engine/source)

| module | what it does |
|---|---|
| `rebar_unit_mass.py` | one project-wide unit-mass method (D2/162, D2/162.16, exact density, standard table); `assert_single_method` refuses a mixed project |
| `rough_rebar_sanity.py` | ROUGH_REBAR = concrete x category ratio, sanity check only; element-class mapping (joint -> walls/columns), BBS_COMPLETE_VARIANCE vs BBS_INCOMPLETE_SIDE_BY_SIDE, never "missing steel", ROUGH_RATIO_NOT_CONFIGURED |
| `comparison_scope.py` | views with measurement basis, included/excluded components and overlap policy; DIRECTLY_COMPARABLE / COMPARABLE_AFTER_NORMALIZATION / NOT_COMPARABLE; no % for NOT_COMPARABLE; normalisation groups |
| `cad_oracle.py` | read-only CAD oracle (MATCH/CLOSE/CONFLICT/UNAVAILABLE); pagination -> INCOMPLETE, tool failure -> UNAVAILABLE |
| `source_oracle_comparison.py` | Urban vs oracle row (MATCH / CLOSE / CONFLICT / NOT_COMPARABLE / ORACLE_UNAVAILABLE); the Urban value is deep-copied, never overwritten |
| `cad_guards.py` | donor learnings: segment-crosses-region (not start point), closed-polygon area only, unreadable text -> SOURCE_REVIEW, evidence state from authority class, one physical geometry authority, schedule rows never create occurrences |
| `structural_population_discovery.py` | PRESENT / NOT_PRESENT / BLOCKED / UNKNOWN for every population; NOT_PRESENT without refs is downgraded to UNKNOWN; parapet stiffener scenario (drawing -> project rule -> Urban 4 m candidate, PROVISIONAL + PARAPET_STIFFENER_SPACING_REQUIRED) and ring-beam requirement |
| `source_roles.py` | PRODUCTION_SOURCE / EXTERNAL_ORACLE / FREELANCER_QS_REFERENCE / URBAN_OWNER_RULE capabilities; only production and owner rules can resolve a quantity |
| `column_rebar.py` (changed) | transverse notation parser (`/m` = RATE_PER_M), level-method policy, COLUMN_SECTION_TRANSITION -> BLOCKED_TRANSITION_DETAIL, unit mass through `rebar_unit_mass` |

Profiles: `engine/profiles/URBAN_ROUGH_REBAR_PROFILE_V1.json` (owner rule, integers, no benchmark values) and
`URBAN_STANDARD_CANDIDATES_V1.json` (parapet stiffener 4 m and top ring beam, candidates only).

## S3.1 column corrections

| | S3 | S3.1 |
|---|---|---|
| unit mass | exact density (columns only) | D2/162, same as every other Urban rebar module |
| `/m` notation | END_LEVEL flag open | RATE_PER_M -> RATE_COUNT by URBAN_OWNER_RULE (flag resolved by policy) |
| section transitions | assumed straight | 44 segments BLOCKED_TRANSITION_DETAIL (2 orientation changes) |
| headline | one modelled total | VERIFIED 3,364.978 / LOWER_BOUND 2,509.906 / PROVISIONAL 1,354.814 / BLOCKED_MODELLED 258.508 kg / 51 unquantified blocked parts; modelled sum 7,488.205 kg is **not final** |

The frozen S3 outputs still reproduce (the S3 adapter pins exact density and turns the transition check off).

## Freelancer lineage: the label is narrower than the scope

All 8 concrete categories sum back to the summary cell from traced Excel formulas (workbook check cells read OK).

| category | traced scope beyond the label |
|---|---|
| foundations | + perimeter ground beam 8.604 + straps 3.392 m3 |
| ground beams + ground slab | + boundary-wall beam 7.56 m3 |
| walls + columns | + 1.5 m necks 8.805 + lift walls 2.4 m3 |
| beams | gross depth (overlaps Urban slab full depth); 1F subtotal skips row 59 (0.128 m3) |
| slabs | net of beam footprints; 1F deduction multiplied by 0 |
| stairs | includes the domes (6.78 m3) |
| pool | includes pump-room wall and floor; a stray cross-sheet total has a broken reference (not used) |
| steel | typed tonnages, no formulas: no bar-by-bar lineage |

## Comparison results (Urban vs references)

Agreement (same basis):
- gross footprint: Urban 595.1 vs oracles 590.4 / 598.7 m2 (MATCH)
- net slab 1F / 2F: within 1% of U-C4N (MATCH); GF +5% (opening treatment)
- footings: Urban 64.3 lower bound vs 65.6-66.6 (CLOSE, F/F10 blocked on the Urban side)
- straps: Urban = freelancer 3.392 m3

Largest real disagreements (review required):
- ground beams 11.2 (exterior blocked) vs 36-46.6 m3
- ground slab 11.5 vs 29.6-32.4 m3
- straps vs oracles 6.1 m3 (the oracles appear to include more than the strap band)
- beam downstands 37.6 vs 50.8 / 46.6; slabs at full depth 81.4 vs 95.7 / 96.8 (the oracle volume implies ~0.20 m thickness)
- pool scope 5.05 vs 12.35 (the QS includes the pump room)

Convention-only (not errors): freelancer beams 66.0 vs Urban 37.6 and slabs 59.8 vs 81.4 are NOT_COMPARABLE on their
own. The FRAME union per floor (columns + joints + beams + slabs) gives GF -13%, 1F +10%, 2F -5%.

Rough rebar vs actual: every category except the pool has an incomplete BBS, so they are shown side by side
(released / provisional / blocked); only the pool reports a variance. There is no global villa kg/m3.

## Missing / blocked populations

BLOCKED: neck/pedestal, structural/lift walls, lift pit, lift tie beam, dome ring beam, stairs and landings,
boundary wall and its ground beam, parapet. UNKNOWN: beam openings, water tank, boundary RC column, parapet
stiffener columns and ring beam, equipment bases, planters, other special RC. NOT_PRESENT (with refs): raft, strip
footing, pile cap, flat slab, ribbed slab.

## What worked

- The production freeze, then post-freeze comparison: the gate is re-checked by hash on every build.
- Formula lineage instead of label matching: it exposed five labels hiding extra scope and two formula defects.
- Comparability states stopped convention differences (beam gross vs downstand) from being read as errors.
- The S3.1 corrections are generic and reproduce S3 when switched off.

## What is not working / open

- Ground beams, ground slab and stairs are still the largest gaps; Urban is a lower bound there (blocked sources).
- The oracle values are recorded from the brief, not re-run; a live CAD oracle run is still UNAVAILABLE.
- Oracle net rebar (22.6 / 22.9 t) is known incomplete, so it cannot be compared.
- Column section transitions are blocked: ST7757 has no transition detail.

## Recommended next

1. Consultant questions for the ground-beam exterior set, the ground-slab extent and the stair waist/riser (largest real gaps).
2. Confirm whether the lift walls and boundary beam exist in the structural set (freelancer hints only).
3. Ask for the column transition detail and the parapet stiffener spacing.
4. Next trade after review: beam rebar (S4) on the same engine pattern. Footing rebar stays parked until approved.

Deliverables: the 9 registers + INDEX in this folder; the workbook `review/ALSENAN_MULTI_ENGINE_STRUCTURAL_COMPARISON.xlsx`
(client data, gitignored; 560 formulas, 0 errors) with its hash in `review/REVIEW_MANIFEST.json`.
