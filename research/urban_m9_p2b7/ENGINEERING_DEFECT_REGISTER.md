# Engineering defect register (Phase 2B-7)

**Scope.** This register carries `research/urban_m9_p2b6/ENGINEERING_DEFECT_REGISTER.md` forward.

- **"Fixed in V2.7"** means the defect is corrected in ARCH_TAKEOFF_V2.7, with an acceptance test against hand
  truth or an independent reader.
- V1 – V2.6 keep every defect as found: they are frozen, and the Phase 2B-6 as-found tests still assert them.
- Classes are as in Phase 2B-6: GEOMETRY, ROLE, ALLOCATION, COVERAGE, PRESENTATION, INPUT.

## Carried from Phase 2B-6

| id | defect | class | V2.7 status | evidence |
|---|---|---|---|---|
| D-P6-01 | a door drawn two ways at one opening takes the wall gap's width (1.027 m) instead of its symbol's (0.80 m) | GEOMETRY | **fixed** (D-V27-01). Wider openings are kept, with the remainder named | CROSSING to hand truth; on the reference plan, 7 of the 8 failing Stage C checks pass |
| D-P6-07 | a basin-only space is typed wet | ALLOCATION | **fixed** (D-V27-05). REVIEW, never DRY; its doorway strip is held too | on the reference plan, the last failing Stage C check passes; 3 spaces (9.35 m2) go to REVIEW |
| D-P6-02 | a single exploded door types its layer WINDOW; the swing is subtracted from the floor | ROLE → GEOMETRY | **fixed** (D-V27-02) | PLAIN: 12.00 m2, 14.00 m; aligned column row: the hall exact (V2.6 −0.3848 m2 = π·0.7²/4) |
| D-D1 | a layer with one door, window or column is not recognised | ROLE | doors and windows **fixed**. One or two columns: **refused** with a record unless wall-bound and explaining the layer (never guessed) | B04 refusal; B10 door block |
| D-P6-03 | small filled squares typed COLUMN (drains) | ROLE | **fixed for drain-size squares** (< 0.20 × 0.20 m never a column). A drain of column size still needs a second source (structural plan / schedule); audit A04 asks | drains / three drains / drain at wall |
| D-P6-04 / D-P6-08 | columns turned off the axes, or drawn as four LINEs, are not inferred | ROLE → GEOMETRY | **fixed** (D-V27-03). Limitation: a turned column is not an opening jamb or a wall-cut | villa turned 30°; FOUR_LINE / TURNED fixtures |
| D-D2a | an arc-walled room's polygon is the chord | PRESENTATION + layouts | **fixed** (D-V27-04) | B10 shoelace within 0.003 m2 |
| D-D2b | a curved wall band is missing from the wall run | GEOMETRY | **fixed** (D-V27-04). Basis D-07 open | reference plan: +1.884956 m, equal to the raw-ezdxf census to 1e-6 |
| D-P6-05 | a plan inside a block holds every door (frame span read across the whole block) | COVERAGE | **fixed** (D-V27-07) | FR_GROUP / FR_NEST: V2.6 frame 2.40 / 4.40 m, door withheld; V2.7 0.80 m, released |
| D-P6-06 | a turned plan in metres gets a zero-length waterproofing termination | PRESENTATION | **fixed** (D-V27-08) | PLAIN rot37 metres; unit tests on `wp_geometry.segments` |
| D-C2 (2B-5) | leaf-closed doorways: threshold withheld | COVERAGE | open (D-V27-01's jamb machinery applies; not extended to leaf-closed faces) | - |
| D-C2b (2B-5) | two leaf-closed doorway pieces take their whole face | GEOMETRY | open | - |
| D-C3 (2B-5) | a doorless cell merged into a wet room takes the wet scope silently | ALLOCATION | open | - |
| D-C5 | wall-area lines rest on synthetic heights | INPUT | open: next phase P1 (`NEXT_PHASE_PLAN.md`) | - |
| L-01 | a sheet frame turned with its plan is refused at admission | LIMITATION (safe) | unchanged | - |
| G-* | catalogue gaps: formwork, excavation, glazing areas, roof / balcony / paving, combined export… | COVERAGE | next phase plan | - |

## Found in Phase 2B-7

All were found by the validation work of this phase: the reference plan, the run audit and the difference explainer.

| id | defect | class | found by | status |
|---|---|---|---|---|
| D-P7-01 | **V2.6**: an arc-walled wet room gets a false 3.0 m FIN.WP.TERMINATION of kind OTHER (the arc's chord taken as an open edge) | PRESENTATION | B10 acceptance test | fixed in V2.7 (D-V27-04); V2.6 as found |
| D-P7-02 | **V2.7 draft**: a row of aligned columns lost its COLUMN role. The wall guard measured the band *span*: a row's faces lie on two long lines, though only the columns' own sides are drawn | ROLE | the reference plan (3 floors; 747 differing totals) | fixed before release: the guard counts paired drawn faces (`paired_long_m`). Test: aligned rows to hand truth, invariant |
| D-P7-03 | **V2.7 draft**: a basin's own taps, wastes and spout lines drawn loose on the sanitary layer counted as a second piece of sanitary evidence | ALLOCATION | the reference plan (3 hand-wash spaces typed wet) | fixed: linework within 0.30 m of a basin block is the basin. Adversarial fixture BASIN_FITTINGS |
| D-P7-04 | **V2.7 draft**: the same column found by both readers counted twice (float-different boxes); the log claimed added columns | PRESENTATION | the difference explainer | fixed: boxes equal within 1 mm are one column |
| D-P7-05 | **V2.7 draft**: the doorway strip of a space under wet review was given the dry floor porcelain | ALLOCATION | the BOQ impact review | fixed: the strip is held with THRESHOLD_OF_SPACE_UNDER_WET_REVIEW |
| D-P7-06 | **V2.7 draft**: provenance mapped lines by floor; two regions of one floor reuse opening ids | PRESENTATION | independent provenance check (villa) | fixed: one region at a time; records carry floor and region |
| D-P7-07 | the run audit read V2.6 evidence keys only (A03 / A04 printed "None" on V2.7 runs) and flagged a curved band V2.7 measures (A07) | PRESENTATION (tool) | audit on V2.7 runs | fixed in `tools/arch_run_audit.py`; the p2b6 audit tests still pass |
| L-P7-01 | the WC-shape rule misses a round bowl | COVERAGE (safe: REVIEW) | adversarial fixture | **known limitation**, strict xfail |
| L-P7-02 | an armchair drawn with a W.C.'s outline passes the WC-shape rule; with a basin, the space is typed wet (flagged for review) | ALLOCATION | adversarial fixture | **known limitation**, strict xfail. Geometry alone cannot separate the two; it stays corroborating evidence only |
| L-P7-03 | the exclusion of a basin block's own linework from the WC-shape candidates is ineffective: fixture ids and insert paths use different id forms | ALLOCATION (latent) | code review during D-P7-03 | open. No effect on the tests or the reference plan (no WC shape found there). Next phase: map fixture ids to insert paths |
| L-P7-04 | a space under wet review carries no finish lines, not even ceiling and plaster, which both readings share | COVERAGE | BOQ impact review | open, owner decision D-18 |
| L-P7-05 | 10 lines of the reference plan carry no source entity (strip remainders, schedule-only items) | PRESENTATION | provenance census | recorded NOT_TRACED, never invented |
