# EIMP part 1: scope list for the 10 Nov end-to-end BOQ (Lead, 2026-11-02 12:30 UTC per `date -u`)

Recovery plan step 1 (MISSION top section: "Scope list = EIMP + component register (T-471 part 1): Lead today, then
Worker 2"). This is the Lead's SCOPE LIST only: every scope-freeze component, the registry family that carries it, its
state in the candidate, the integration stream and the board row that moves it. Worker 2 (T-471) builds the EIMP proper
on it: construction method, rule and hierarchy level, formula, material calculation, drawing evidence, applicability
state per project and the component -> BOQ line map. Nothing here is a quantity; nothing here is VERIFIED.

Source of the states: `research/agents_t469/out/T469_SCOREBOARD_V3_0_41.json` (engine 4aaa9be0; candidate V3.0.41
5176c7c4, the only full per-family scoring) plus the one Gate B since then (T-442 -> V3.0.42 1793266d: ground slab).
States: VERIFIED (whole line, Checker record) / MEASURED (all lines released, not verified) / HELD (at least one held
line) / EXCLUDED_ONLY / NO_LINE. Applicability (NOT_APPLICABLE / POSSIBLY_APPLICABLE) is T-471's job, from the drawings,
never from this list. Training villa = development benchmark; the list is the same for every villa.

## Structure (stream S, Worker 3)

| Component | Family | Candidate state (lines) | Row that moves it | Gap / note |
|---|---|---|---|---|
| Excavation, backfill, disposal | B1-02 / 03 / 04 | NO_LINE | T-350 (TODO) | bounds beside blank lines (T-347 FILL) |
| Site clearance, anti-termite, dewatering | B1-01 / 05 / 06 | NO_LINE | T-471 states applicability | not in the scope freeze list; T-357: clearance not in drawn scope |
| Blinding | B10-01 | HELD (4) | T-445 (TODO, proposal) -> stream S | 24 pits 12.734 m3 VERIFIED, valued in no line |
| Footings / rafts | B10-02 | HELD (26) | T-180 | 25 / 26 pieces verified; F10 on S3 |
| Necks | B10-03 | HELD (36) | T-180 | |
| Ground beams / straps | B10-04 | HELD (71) | T-180, T-350 (held-range fixes) | 13 lines held by Checker downgrade |
| Ground slab | B10-05 | HELD (25) | done: T-442 V3.0.42 | GS valued 21.638 m3; rest held |
| Columns | B10-06 | HELD (72) | T-180 | RFI-S20 / D-66 conflict lines |
| Beams | B10-07 | HELD (191) | T-180 | |
| Suspended slabs | B10-08 | VERIFIED 60.280 m3 | none | the only whole verified family |
| Stairs concrete | B7-12 | HELD (12) | T-180 | flight residuals T-415 / T-417 |
| Domes / rings | B10-09 | HELD (5) | T-180 | |
| Pool / tank / lift pit | B10-10 | HELD (6) | T-419 (lift tie beam) | pool +1 UNKNOWN |
| Boundary wall, RC parapets | B10-11 / 12 | HELD (2 / 4) | T-350 (band downgrade), T-314 (parapet faces) | |
| Formwork, all elements incl. stairs | B10-13, B7-13 | HELD (612 + 31), 0 released | T-474 (NEW) | the scope item with no row |
| Reinforcement | B11-01 | HELD (2,643; 9,375.306 kg released) | T-449 wiring, T-382 (+ T-459 lap rule) | both merged modules unwired |
| Laps / stock length | B11-04 | NO_LINE | T-382 | T-459 REBAR_LAP_RULE_V2 merged, unwired |
| Rebar of stairs / pool / domes / tank | B11-03 | NO_LINE (BLOCKED_BY_SOURCE) | T-471 states evidence | Lead opens a row when printed details are shown |
| Foundation / buried waterproofing | B8-08 | HELD (19) | T-353 | 109.85 m2 / 5.4925 m3 pieces verified |

## Finishes (stream F, Worker 1)

| Component | Family | Candidate state (lines) | Row that moves it | Gap / note |
|---|---|---|---|---|
| Blocks by type and thickness | B9-01 | HELD (85) | T-180 (blockwork), T-449 round 3 | 7 wall groups UNKNOWN |
| Lintels | B9-02 | NO_LINE | T-448 -> T-453 | owner rule 2 Nov (AGENT_BRIEF) |
| Mesh / ties (accessories) | B9-03 | NO_LINE | T-363 | optional items, Q-77 |
| Mortar / glue | B9-04 | NO_LINE | T-372 | |
| Parapet blocks | B9-05 | NO_LINE | T-314 | |
| Spatter dash | B4-05 | NO_LINE | T-364 | after T-314 |
| Internal plaster | B4-03 | HELD (75) | T-454 (materials) | |
| External plaster / paint | B4-04 / B4-07 | NO_LINE / HELD (13) | T-314 | |
| Internal paint | B4-06 | HELD (76) | T-423 (F1 / F3 items) | |
| Floors porcelain / wet tile / screed | B3-01 / 02 / 05 | HELD (38) / MEASURED (20) / HELD (88) | T-455 (materials) | |
| Entrance / stair-hall marble floor | B3-03 | NO_LINE | T-471 states applicability | owner gate item 'entrance and stair-hall finishes' |
| Thresholds | B3-04 | HELD (38) | T-423 | |
| Skirting, hidden profile | B3-06 / B3-07 | HELD (39) / NO_LINE | T-422, T-443, then T-460 | |
| Wet-wall porcelain + layers | B4-01 | HELD (18) | T-457 (double count), T-455 | owner wet-wall rule 2 Nov |
| Wet-area WP, doorway, upturn 0.20 | B8-01 / 02 / 03 | HELD (35 / 41 / 25) | T-310 | wire WP policy V2 (T-458) |
| Membrane rolls | B8-05 | HELD (22); 52 pcs provisional | T-310 / materials | |
| Roof WP + upturn, roofing build-up | B8-06, B13-01 | HELD (8 / 16) | T-471 (export join T-383) | represented, no integration row |
| Balconies / terraces WP | B8-07 | NO_LINE | T-471 states applicability | |
| Pool / tank WP | B8-09 | NO_LINE (BLOCKED_BY_SOURCE) | T-471 states evidence | |
| Ceilings, bulkheads | B5-01 / B5-04 | HELD (41 / 14) | T-423 | double-height exclusions per T-446 |
| Doors, windows, shutters | B6-02..05 | HELD | T-180 later; counts B6-01 MEASURED | |
| Stair marble treads / risers / landings | B7-02 / 03 / 04 | HELD (15 / 15 / 4) | T-424 binds nosing to them | |
| Nosing | B7-05 | NO_LINE | T-424 | 69 edges 87.350 lm census merged |
| Stair skirting | B7-07 / 08 | NO_LINE | T-443 (flight-side binding) | |
| Lift marble (surround, threshold) | B6-06 / B6-07 | HELD (3) / MEASURED (6) | T-475 (NEW) | the scope item with no row |
| Handrails along the slope, guardrails | B7-10, B7-09, B13-08 | EXCLUDED_ONLY (1), HELD (19 / 6) | T-476 (NEW) | the scope item with no row |
| External paving | B13-02 | HELD (4) | T-471 | represented, no integration row |
| Fence | B13-04 | HELD (39) | T-471 | represented, no integration row |
| Materials layer | all | 52 pcs rolls only | T-448 -> T-453 / T-454 / T-455 | |

## Out of scope freeze (stated, not dropped)
MEP B12-01..05, landscaping B13-03, joinery B13-06, metalwork B13-07, sealants B13-05: no engine line and no
freelancer cover line (T-469). T-471 records each as NOT_APPLICABLE / POSSIBLY_APPLICABLE with evidence, never silent.

## What Worker 2 adds in T-471 (EIMP part 2)
Per component: applicability state with drawing evidence; construction method; rule and hierarchy level (drawing ->
revision -> project requirement -> OWNER CONFIRMED rule -> ESTIMATED method); formula; material calculation; the
component -> BOQ line map (every component to exactly one line, or NOT_APPLICABLE / MISSING with reason; unmapped and
doubly mapped reported). The Checker validates the EIMP (samples 10 states).
