# T-469: re-score of the candidate of record ARCH_TAKEOFF_V3.0.41 on every trade (worker 3, 2026-11-02)

Development villa only (regression sample, not a blind test): no product accuracy figure. Scoring and tools only: no
engine quantity, rule, method or released default changes. Freelancer QUANTITIES only (never rates or header cells).

## 0. Run identity (own run this session, Python 3.11.18, engine a04e3ea8)

Inputs: Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip (P7757.dxf sha256 ab54dd55) and "ST7757 dxf.dxf"
(9f9d1179), decoded by the wrapper into `.work/private`.

- Released baseline: `tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json` ->
  **REPRODUCED**, 1,455 lines, BOQ_LINES.csv b96185d4 (engine a04e3ea8 CLEAN).
- Candidate: `research/agents_t167/v304_run.py` then `research/agents_t431/v3041_run.py` -> **V3_0_40_BOQ_LINES.json
  aa6aa927 and V3_0_41_BOQ_LINES.json 5176c7c4 / csv 145eb34d REPRODUCED** (= the candidate of record, T-431 Gate B);
  V3.0.20 (the last full score, 2026-10-28) re-scored from the same run for the deltas.
- Scored lines tool (unchanged): `bash scripts/agent_env.sh run tools/alsenan_keymap.py --run A --reference
  tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json --key-map tests/alsenan/T001C_KEY_MAP.json --v2-verdicts
  research/agents_t177/CHECKER_VERDICTS_DEV_VILLA.json --set-bindings research/agents_t216/ALSENAN_SET_BINDINGS_T216.json
  --v2-candidate-lines V3_0_41_BOQ_LINES.json` -> `out/KEYMAP_T001C_V3_0_41.{md,json}`. The released rows reproduce
  the 2026-10-28 table byte-for-byte in content (concrete 17.03 / -17.03 compared 3; floor -5.85 %).
- New (this task): `research/agents_t469/t469_trade_scoreboard.py` (definitions in its docstring; 14 synthetic tests + 1 committed-output test in
  `tests/t469_trade_scoreboard`) on both sides -> `out/T469_SCOREBOARD_V3_0_41.{md,json}` (+ `out/..._V3_0_20.md`).
  Inputs are committed snapshots, never the live board (T-411 / T-473 lesson): `VERDICT_V2_SET_V3_0_40_SNAPSHOT.json`
  (board verdicts/V3.0.40, board commit 45e53abe), `DOWNGRADES_SNAPSHOT.json` (union by id of every
  verdicts/V3.0.*/DOWNGRADES.json, 22 records, board c6e70ddb), `CHECKER_REFERENCES_V1_SNAPSHOT.json` (16295eba),
  coverage registry `rules/coverage/BOQ_FAMILY_MASTER_1.36.0.json` (102 families = the expected BOQ lines until T-471
  states applicability), `FREELANCER_PAIRS_T469.json` (declared 1:1 diagnostic pairs).

## 1. Headline (owner categories; whole-line verification is the headline, never one overall %)

| Measure (102 expected BOQ lines = registry families) | Released V2.9 + route G | Candidate V3.0.41 |
|---|---|---|
| (2) measured: families fully released | 12 | 4 |
| (3) independently VERIFIED whole lines | 0 families; 0 item lines | **1 family (B10-08 suspended slabs 60.280 m3, record V2-0c71eb8f); 3 item lines** (STR.CONC.SLAB m3; WP.FOUNDATION.LIFT_PIT_SCREED 20.700 m2 and 1.035 m3) |
| (4) held: families with a held line | 26 | 51 |
| (5) unmeasured: families with no line | 64 | 46 (+1 excluded only) |
| (6) provisional material quantities | none released | 52 pcs membrane rolls (B8-05) released provisional; 3 material lines held (no qty) |
| (7) fully verified procurement quantities | 0 | 0 |
| (8) priced / unpriced | 0 priced / 1,454 lines UNPRICED | 0 priced / 4,836 lines UNPRICED (no approved rates; T-472) |

The candidate has fewer "fully released" families than the released configuration because it surfaces held lines the
released method did not carry (e.g. columns: released 0 m3 + 82 UNKNOWN on V2.9; candidate 19.776 m3 released + held);
the expected-line count is the same 102. The per-trade table is `out/T469_SCOREBOARD_V3_0_41.md` (pasted into the
SCOREBOARD section).

## 2. Engine vs freelancer per trade (keyed and diagnostic)

Scored (tool, key map T001C, V3.0.41): CONCRETE 8 ref lines, coverage 100 %, compared 1 (CONC.SLAB 60.280 vs
59.817 m3 = **+0.77 %**), 7 held; DOORS 12.760 vs 12.000 m2 = **+6.33 %** (heads RULE_DIFFERENCE Q-55 C, widths and
count ENGINE_RIGHT, T-268); FLOOR_AREA 388.859 vs 409.580 m2 = **-5.06 %** (V3.0.20 -6.86 %, released -5.85 %);
PLASTER, PAINT, WINDOWS held (no compared %).

Keyed lines as ranges (released + held low .. high; an UNKNOWN keeps the upper end open):

| Key | Freelancer | Released V2.9 + route G | V3.0.41 |
|---|---|---|---|
| CONC.BLINDING | 47.055 m3 | held 7.276 .. 16.887 = -84.5 .. -64.1 % | held 21.059 .. 25.964 = -55.3 .. -44.8 % (T-445 / T-322: pits blinding 12.734 m3 VERIFIED not yet valued; boundary-wall base UNMEASURED) |
| CONC.FOOTING | 77.631 m3 | 77.265 = -0.47 % | 67.695 + held 9.426 .. 9.998 = -0.66 .. +0.08 % |
| CONC.GROUND | 75.090 m3 | 17.127 + held 22.568 .. 64.104 = -47.1 .. +8.2 % | 41.001 + held 2.808 .. 10.182 + 15 UNKNOWN = >= -41.7 % |
| CONC.COLUMN | 39.752 m3 | held + 83 UNKNOWN | 19.776 + held 12.243 .. 28.977 + 17 UNKNOWN = >= -19.5 % |
| CONC.BEAM | 65.966 m3 | 64.820 + held 8.449 .. 14.434 = +11.1 .. +20.1 % | 66.321 + held 8.373 .. 13.780 + 5 UNKNOWN = >= +13.2 % |
| CONC.SLAB | 59.817 m3 | 61.551 + held 2.740 = +7.48 % | **60.280 = +0.77 %, WHOLE LINE VERIFIED** |
| CONC.STAIR_DOME | 21.833 m3 | 12.007 = -45.0 % | 10.450 + 6 UNKNOWN = >= -52.1 % (T-415 / T-417 flight residuals) |
| CONC.POOL | 12.348 m3 | 3.495 = -71.7 % | 7.202 + 1 UNKNOWN = >= -41.7 % |
| PLASTER.INTERNAL | 1,151.138 m2 | 17.740 + 29 held = >= -98.3 % | 580.582 + held 488.201 .. 544.061 + 12 UNKNOWN = >= -7.2 % |
| PAINT.INTERNAL_WALL | 1,191.128 m2 | 13 UNKNOWN | 217.208 + held 487.121 .. 542.861 + 3 UNKNOWN = >= -40.9 % |
| DOORS.ALUMINIUM | 12.000 m2 | unit refused (pcs) | 12.760 = +6.33 % |
| WINDOWS.ALUMINIUM | 116.900 m2 | unit refused (pcs) | 76.256 + held 9.870 .. 11.515 + 1 UNKNOWN = >= -26.3 % |

Unkeyed trades, DIAGNOSTIC pairs (declared 1:1, same unit and element; boundary not Checker-reconciled, not a score):
blockwork MAS.BLOCK 579.101 m2 + 7 UNKNOWN vs freelancer total 1,260.690 m2 (range open: the 7 held wall groups carry
no bound); wet-room wall tiles 340.304 m2 + 6 UNKNOWN vs 433.830; internal skirting 184.017 + 0 .. 24.638 + 2 UNKNOWN
vs 282.850 lm; wet-room floor waterproofing 85.621 vs 72.010 m2 = +18.90 % (released V2.9: 62.773 = -12.83 %); internal
railing 17.366 + 17 UNKNOWN vs 18.950 lm; wet-room upturns (engine m2, freelancer lm) and rebar (engine kg, freelancer
t, a kg/m3 lump, RULE_DIFFERENCE T-272) REFUSED as unit mismatches, never converted.

Unscored trades and why: B1 site works, B12 MEP: no engine line and no freelancer cover line; ceilings (engine physical
ceiling m2 vs freelancer gypsum decor m2: different elements); external plaster / paint, stair marble, yard and pool
finishes, roof waterproofing: no key and no declared 1:1 pair (T-452 A4 owns project-independent keys). Rebar: released
9,375.306 kg on 374 lines + held 894 bounded 14,278.249 .. 19,646.878 + 798 UNKNOWN (after the Checker's 38-line
874.862 kg downgrade; 9,375.306 + 874.862 = 10,250.168, the board's earlier released figure), not scored.

## 3. Released V2.9 + route G per-family concrete statement (none existed; Lead report 2026-11-01)

From `out/T469_SCOREBOARD_V3_0_41.md` "Per-family concrete statement": V2.9 + route G released 231.630 m3 on the B10
families + held 205 lines (122 bounded 44.108 .. 113.540 m3, 83 UNKNOWN); MEASURED families: footings 66.264, stair
4.635, domes 7.372, pool 3.495, boundary wall 7.220 m3; columns 82 lines all UNKNOWN; blinding held 7.276 .. 16.887.
Candidate V3.0.41: released 267.357 m3 on the B10 families + held 143 lines (98 bounded 53.908 .. 88.901, 45 UNKNOWN);
15 of them held by Checker downgrades (ground beams 13, blinding 1, boundary wall 1).

## 4. What changed since the last full score (V3.0.20, 10-28) on the keyed lines

FLOOR_AREA -6.86 -> -5.06 % (released floor lines 381.464 -> 388.859 m2, T-414 / T-418 / T-427 integrations);
PLASTER released 234.948 -> 580.582 m2 (wet-room backing and room faces); columns released 28.215 -> 19.776 m3 with the
held bound 4.209 .. 18.858 -> 12.243 .. 28.977 (lines moved to held by later integrations, not a lost quantity);
CONC.GROUND released 43.714 -> 41.001 m3 (lines moved to held; the held bound and UNKNOWN count grew, see the range
table); every other keyed cell unchanged.

## 5. Findings for the Lead / Checker

1. The tool's Verified-share column prints 0 / 8 for concrete because its verdict file is V1; the V2 record
   V2-0c71eb8f (CONC.SLAB WHOLE) still binds V3.0.41 by line content (`CARRIED_BY_CONTENT`): all 9 V3.0.40 V2 records
   carry by content to V3.0.41 (no own line changed). The Checker re-binds them; this task writes no verdict.
2. The keyed tool does not apply Checker downgrades; the 8-category table does (14 records APPLIED on V3.0.41). Two
   views of one candidate therefore differ by the downgraded lines; both are labelled.
3. Four downgrade records (DG-1b0eacce, DG-a97ec2ea, DG-d0012905, DG-eba2b0b8) bind the same 38 rebar lines
   874.862 kg: counted once (by line), never four times.
4. Material layer: the only released material quantity is 52 pcs membrane rolls (B8-05), PROVISIONAL; T-448 / T-453 ..
   T-455 own the rest.

## 6. Limits

Expected scope = the registry's 102 families, not a per-project applicability (T-471 completeness matrix). The keyed
reference covers 13 lines; per-trade keys for the other trades are T-452 (A4). Freelancer pairs are diagnostics only.
No cost figure (no approved rates). The family-level "verified whole line" is stricter than the item-line count; both
are shown.
