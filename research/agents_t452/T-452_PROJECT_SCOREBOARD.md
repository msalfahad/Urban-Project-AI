# T-452: project-agnostic key map and scoreboard (worker 1, 2026-11-02)

Owner directive 2026-11-02 A4 + follow-up (both variances, quantity AND cost, exception classes, line-level view).
Scoring tool only: no engine quantity, rule, method, key map or released default changes. Development villa = regression
sample, never a product accuracy figure.

## What was built

- `tools/project_scoreboard.py` (new): one manifest (`URBAN_PROJECT_SCORE_MANIFEST_V1`) per project names its run, its
  normalised freelancer workbook, its key map (`URBAN_PROJECT_KEY_MAP_V1`, carries `project_id`; the legacy training
  maps T001B / T001C are accepted unchanged), and optionally a reconciled reference (`URBAN_CHECKER_REFERENCES_V1`), a
  pricing basis (`URBAN_PRICING_BASIS_V1`), set bindings (T-216), high-value keys and the tolerance (default +-3 %).
- The score is NOT re-implemented: each side goes through `alsenan_keymap.engine_rows / reference_rows` and
  `alsenan_scoreboard.score` (project-independent rules, historical names). `tools/alsenan_keymap.py` and
  `tools/alsenan_scoreboard.py` are not edited.
- Goal B layer on top: variance vs ORIGINAL workbook and vs RECONCILED reference kept apart (a reconciled record is used
  only if this project's, VERIFIED, same unit, exactly the key's item codes; the original is never substituted);
  exception classes ZERO_REFERENCE / ENGINE_ONLY / REFERENCE_ONLY / SCOPE_MISMATCH; cost on ONE approved basis, same rate
  both sides, INCOMPLETE_PRICING when any compared key of a trade is unpriced, NO_APPROVED_PRICING_BASIS without one;
  OFFSETTING_ERRORS when a trade total is within tolerance but a compared line is not; high-value line view.
- `research/agents_t452/DEV_VILLA_MANIFEST.json`: the training villa's manifest (run given with `--run`, private).

## Acceptance

1. Training-villa score reproduced exactly through the generic path (own run, Python 3.11.18, engine 86335fa8; Drive
   "Alsenan chalet project" P7757.dxf ab54dd55, "ST7757 dxf.dxf" 9f9d1179):
   - Released V2.9 + route G: `tools/release_baseline.py run .../V29_ROUTEG_NO_PROFILE.json` REPRODUCED, 1,455 lines,
     BOQ_LINES.csv b96185d4.
   - Candidate: `research/agents_t167/v304_run.py` then `research/agents_t442/v3042_run.py` -> V3_0_42_BOQ_LINES.json
     **1793266d** (= T-442 record, 4,839 lines).
   - `alsenan_keymap.py` (T001C + T-216 set bindings) vs `project_scoreboard.py` (manifest), each side: score JSON
     byte-identical (released 969b7920, candidate 079059ad) and markdown byte-identical (ae844261, 4e60363d):
     **diff 0 lines** on both sides. Candidate scored beside the released run's release report (as scoreboard v2 does).
2. Synthetic second project N452 (generic key map, own workbook, 8 keys, 7 trades) scored through the CLI with no code
   change; hand calculation in the test docstring.
3. Adverse: ZERO_REFERENCE (plaster ref 0, engine 30: no %), SCOPE_MISMATCH (kg vs t refused; engine NOT_APPLICABLE vs
   reference 400; reconciled record of other item codes), REFERENCE_ONLY (no engine line; unkeyed cover row), ENGINE_ONLY
   (unmapped code; unit 'item'), HELD never 0 or a partial sum, foreign key map / pricing refusals, line-order invariance.

## Training villa, V3.0.42 view (regression only; full table `out/PROJECT_SCOREBOARD_V3_0_42.md`)

| Trade / unit | Released V2.9 + route G | Candidate V3.0.42 |
|---|---|---|
| CONCRETE m3 vs workbook | 3 of 8 compared, 92.767 vs 111.811 = -17.03 %; 5 HELD | 1 of 8 compared (CONC.SLAB 60.280 vs 59.817 = +0.77 %); 7 HELD |
| CONCRETE m3 vs reconciled | none (CONC.SLAB held) | CONC.SLAB 60.280158 vs Checker 60.2804 = -0.0004 % |
| DOORS m2 | SCOPE_MISMATCH (engine answers in another unit) | 12.760 vs 12.000 = +6.33 % |
| FLOOR_AREA m2 | 385.634 vs 409.580 = -5.85 % | 388.859 vs 409.580 = -5.06 % |
| Cost | NO_APPROVED_PRICING_BASIS (T-472 paused) | same |
| Exceptions | ENGINE_ONLY 30, REFERENCE_ONLY 32, SCOPE_MISMATCH 2 | ENGINE_ONLY 84, REFERENCE_ONLY 32, SCOPE_MISMATCH 0 |

CONC.FOOTING's reconciled record is PARTIALLY VERIFIED and of item code STR.CONC.FOOTING only, while the key also holds
STRAP and BOUNDARY_WALL: it is NOT_VERIFIED here (and would be SCOPE_MISMATCH once verified) - never compared. ENGINE_ONLY
84 = unmapped item codes of the candidate (key-map gaps, not false positives); REFERENCE_ONLY 32 = workbook cover rows no
key names (e.g. blockwork, rebar t, waterproofing, skirting): the generic report now lists them instead of dropping them.

## Missing / next

No approved pricing basis exists, so cost variance is untested on real data (synthetic only). The reconciled reference
holds 2 records; T-469 / T-471 can switch to this tool (manifest + `goal_b` block). Key-map gaps (84 ENGINE_ONLY codes,
32 unkeyed cover rows) are a key-map task, not this tool.
