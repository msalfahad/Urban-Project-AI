# T-140: coverage census V2 on BOQ_FAMILY_MASTER 1.1.0

Worker 3, 2026-10-21. Lane I, unblocked infrastructure: no method, line or quantity changes. The released run keeps
census V1 (`engine/source/coverage_census.py`, 1.0.0, untouched; `rule_store.family_master()` still 1.0.0).

## What was built

- `engine/source/coverage_census_v2.py` (new; nothing in the engine imports it; rollback = delete).
  `load_master()` reads `rules/coverage/BOQ_FAMILY_MASTER_1.1.0.json` and refuses it when its sha256 differs from
  `rules/RULES_MANIFEST.json`; `validate_master()` refuses an item code owned by two families, a capability outside
  the master's vocabulary, or a code both owned and listed without family. `census(lines, ...)` maps every family to
  the line keys 1.1.0 records for it (`item_codes`) and gives one state with its reason: FOUND / HELD / EXCLUDED /
  COUNTED_IN_PARENT / NOT_FOUND_IN_SOURCE / NOT_RUN / NO_LINE_KEY / NOT_IMPLEMENTED / BLOCKED_BY_SOURCE, plus per
  unit (never mixed): found lines and quantity, held lines (quantity always UNKNOWN, bounded ranges summed apart with
  a `complete` flag), excluded lines, lines not summed (never-additive pairs, order-independent). Rules carried over
  from census V1: route G family census for families without lines (it can never make a family FOUND), scope steel
  MISSING_DATA (B11-03), membrane roll plans from the material results (B8-05). New rules: a quantity only in a
  unit the family is not paid in is geometry, not the family's quantity (family stays HELD, flag
  QUANTITY_ONLY_OUTSIDE_FAMILY_UNIT); `run_kind="released"` / `"candidate"` turns "no line" into NOT_RUN when 1.1.0
  says the released method / the V3.0 candidate does not produce the family; codes of the run that no family owns
  are listed (`unowned_codes`, counted as silent omissions), codes 1.1.0 lists without a family are listed with
  their reason.
- `tests/t140_coverage_census_v2/` (24 tests, synthetic villa, hand values in the docstring).
- `tests/structural_comparison_engine/rebar_product_registry.py`: the new module declared in OTHER_REBAR_AWARE (it
  names STR.REBAR only to report missing scope steel, as census V1).
- `research/agents_t140/census_run.py`: the read-only runs and the census tables (outputs outside the repository).

## Runs on the development villa (Drive copies, read-only)

Inputs: architectural DXF from P7757_DXF_COMPRESSED.zip (sha256 ab54dd55...) and "ST7757 dxf.dxf" (sha256
9f9d1179...), both equal to the T-130 SOURCE_MANIFEST. Python 3.11 project venv, working head 75be4ad.

1. Released ARCH_TAKEOFF_V2.9 + route G exactly as 1.1.0 `run_evidence.released_run` records it (conventions V6, no
   facts, no profile): 1,455 lines, BOQ_LINES.csv sha256 b96185d4... = the T-130 run, byte-identical.
2. Candidate ARCH_TAKEOFF_V3.0.1 as research/agents_t133/v301_run.py plus the route G profile
   (research/urban_engine_m4_correctness/profile_st7757_m4.json, Gate B defect D1): base V2.9 with profile 1,621
   lines, V3.0.1 1,698 lines (identity: 1,685 unchanged identical, 9 replaced, 2 added vs V3.0).

Checks: census V1 recomputed from the run folders equals the COVERAGE.json each run wrote (state and line count of
all 99 families). Census V2 per item code and unit equals the 51 figures 1.1.0 recorded for the released run (lines,
released lines and quantity, held lines and bounded range, not-applicable lines): 51 / 51.

## Released run: census V1 vs V2 (99 families)

| | FOUND / QUANTIFIED | HELD (BOUNDED_ONLY + BLOCKED in V1) | NOT_FOUND_IN_SOURCE | NOT_RUN | NO_LINE_KEY | NOT_IMPLEMENTED | BLOCKED_BY_SOURCE |
|---|---|---|---|---|---|---|---|
| V1 (1.0.0 map) | 22 | 10 | 2 | 22 | - | 27 | 16 |
| V2 (1.1.0 map) | 27 | 14 | 2 | 1 | 21 | 18 | 16 |

## The families T-130 named as census gaps (released run; candidate where it differs)

| family | V1 | V2 | quantity per unit (V2) | explanation |
|---|---|---|---|---|
| B8-03 wet-room upturn | NOT_FOUND_IN_SOURCE | FOUND | m2: 14 lines 22.065 m2; lm: 4 terminations HELD 0 .. 0.505 lm | RESOLVED: FIN.WP.WALL_UPTURN mapped (was FIN.WP.UPTURN only). Candidate: 17 lines 25.115 m2 + 1 held; lm 7 held 0 .. 3.660 |
| B6-02 internal doors | NOT_IMPLEMENTED | FOUND | 15 pcs | RESOLVED: DOOR.INTERNAL.PVC was counted under B6-01 |
| B6-03 external / main doors | NOT_IMPLEMENTED | FOUND | 2 pcs | RESOLVED: DOOR.EXTERNAL.ALUMINIUM / DOOR.MAIN_ENTRANCE |
| B6-04 windows | NOT_IMPLEMENTED | FOUND | 27 pcs | RESOLVED: ARCH.WINDOW. B6-01 now keeps ARCH.DOOR / ARCH.PASSAGE only: 11 pcs (55 in V1 = 11 + 15 + 2 + 27, nothing lost) |
| B9-01 block walls | BLOCKED (7 lines) | HELD (28 lines) | lm: wall run 7 lines 216.931 lm found; m2: 14 held; m3: 7 held | RESOLVED + EXPLAINED: all four wall codes mapped; the only quantity is the wall run in lm, which is the walls' geometry, not the block m2, so the family stays HELD (owner Q-60 height, Q-65 type) |
| B3-04 door thresholds | NOT_RUN | FOUND | m2: 10 lines 1.340 m2 found, 14 ARCH.THRESHOLD held | RESOLVED: FIN.MARBLE.THRESHOLD and ARCH.THRESHOLD mapped |
| B2-02 room clear floor area | NOT_RUN | FOUND | 12 ARCH.SPACE lines 63.158 m2 | RESOLVED for the ARCH.SPACE lines (the room floors themselves are B3-01 / B3-02) |
| B2-03 gross floor area | NOT_RUN | NO_LINE_KEY | - | EXPLAINED: measured in ARCH_FLOOR_AREAS.json (a file, not a BOQ line: GF 284.1465, 1F 209.8017, 2F 55.08 m2 per 1.1.0); no line key exists to map; no independent check of the plates |

Other changes the 1.1.0 map brings, with their cause:

- B10-03 necks: V1 QUANTIFIED (it took route G's PARTLY_QUANTIFIED over 36 bounded lines) -> V2 HELD (no neck line
  carries a quantity: 35 bounded 3.075 .. 15.375 m3 + 1 blocked). V1 over-stated this family; V2 never lets a route
  census make a family FOUND.
- B4-07 external paint: V1 NOT_RUN -> V2 HELD (facade run 191.856 lm found, every m2 line held: no specification).
- B4-08 reveals: V1 NOT_IMPLEMENTED -> V2 HELD (27 ARCH.WINDOW_REVEAL lines, all blocked). The released reveal
  plaster lines are FIN.PLASTER (owned by B4-03): their sub-scope has no code of its own, so V2 cannot split them out.
- B7-09 guardrail: V1 NOT_IMPLEMENTED -> V2 HELD (14 FIN.RAILING lines, blocked).
- B8-07 balconies: V1 NOT_IMPLEMENTED -> V2 NOT_FOUND_IN_SOURCE. The released balcony membrane would be FIN.WP.FLOOR
  'exterior wp_floor', owned by B8-01; on this villa the released run has no such line (1.1.0 records none), so the
  state is right here; a villa with a drawn balcony would show it under B8-01 until the line carries its own code.
- B8-06 roof waterproofing: released NOT_RUN (1.1.0: the released method has no roof line); candidate FOUND
  (m2: 3 lines 204.112 m2 + 1 held top roof; lm: 3 upturn lines 181.589 lm + 1 held).
- B8-05 membrane rolls: released FOUND from the material results only (no BOQ line; flag); candidate FOUND 21
  FIN.WP.MEMBRANE_ROLLS lines 52 pcs (rolls) + 1 held.
- Twenty-one families with capability but no line key (B1-02 excavation, B10-13 formwork, B2-01 / B2-03 (above) / B2-04 / B2-05,
  B3-03 / B3-05 / B3-07, B4-04 / B4-09 / B4-10, B6-06 / B6-07, B7-05 / B7-07 / B7-08, B9-05, B11-02 / B11-04,
  B12-01) are now NO_LINE_KEY with the 1.1.0 reason instead of NOT_RUN / NOT_IMPLEMENTED: a run cannot answer them
  until a method writes a line for them.
- Item codes of the runs without a family: ARCH.EXTERIOR (1 line; 1.1.0 lists it with its reason); unowned codes:
  none, in both runs.

## Candidate V3.0.1 against the released run (family level, V2 census)

| family | released (no profile) | V3.0.1 candidate |
|---|---|---|
| B3-01 dry floors | 31 lines 323.143 m2 | 30 lines 278.274 m2 + 1 held 38.459 .. 38.979 m2 |
| B3-02 wet floors | 13 lines 53.143 m2 | 16 lines 62.491 m2 |
| B7-12 stair concrete | 3 lines 4.635 m3 | 4 lines 9.954 m3 |
| B8-01 wet-room membrane | 14 lines 62.773 m2 | 18 lines 85.621 m2 |
| B10-01 blinding | HELD 7.276 .. 16.887 m3 | FOUND 15.179 m3 + 3 held 6.976 .. 10.784 m3 |
| B10-03 necks | HELD 3.075 .. 15.375 m3 | FOUND 28 lines 10.856 m3 + 8 held 0.405 .. 2.025 m3 |
| B10-04 straps / ground beams | 3 lines 3.781 m3 + 59 held 17.801 .. 59.337 m3 | 61 lines 30.755 m3 + 2 held 0 .. 1.809 m3 |
| B10-06 columns | HELD (82 blocked) | FOUND 59 lines 34.446 m3 + 5 held 1.134 .. 3.483 m3 |
| B10-08 slabs | 75 lines 61.551 m3 + 1 held 2.740 | 75 lines 60.919 m3 |
| B11-01 reinforcement | 467 lines 16,392.6 kg + 30 held | 646 lines 23,032.5 kg + 30 held |

These are census readings of the two runs, not verified quantities and not a release; the structural differences
come mostly from the route G profile, which the released run of 1.1.0 / the scoreboard does not use (see finding 1).

## Findings for the Lead and the Checker

1. Two different runs are both called "released V2.9 + route G". 1.1.0 `run_evidence.released_run` (and the T-130
   figures this census reproduces 51 / 51) is the run without the route G profile and without the project facts
   (1,455 lines); the V3.0 / V3.0.1 runners' base V2.9 run uses the profile and the facts (1,621 lines). 8 of the 51
   1.1.0 per-code figures differ on the profiled run (B7-12, B10-01, B10-03, B10-04, B10-05, B10-06, B10-08, B11-01).
   A Gate B diff "against V2.9 + route G" must name which of the two it uses.
2. Census V1 says B10-03 necks are QUANTIFIED on the released run although no neck line carries a quantity; V2 says
   HELD. Census V1 stays as it is (released run); the Lead decides whether the released run adopts V2.
3. Sub-scopes without their own code cannot be separated by any census that maps by item code: reveal plaster inside
   FIN.PLASTER (B4-08 vs B4-03), balcony membrane inside FIN.WP.FLOOR (B8-07 vs B8-01). A dedicated code per
   sub-scope in a later method version would close this.

Missing / not done: adoption of V2 by `tools/urban_boq_m9.py` (a released-run change: owner / Lead decision, not this
task); a second villa with drawings (none on Drive; the synthetic villa covers the rules).
