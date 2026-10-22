# T-182: the scoreboard's five measures kept apart (worker 3, 2026-10-22)

Owner scoreboard review 2026-10-22 09:05: scope coverage, independently verified coverage, accuracy against
independent drawing measurement, freelancer variance and HELD / UNKNOWN are five different things; released and
candidate never combined; every percentage with its numerator and denominator; the freelancer is not ground truth.
Tooling only: no engine quantity, rule, verdict or release changes.

## What changed

- `tools/scoreboard_v2.py`: opt-in layout `LAYOUT_FIVE` (`--layout five`; heading `## SCOREBOARD v2.1 <time>`),
  new functions `_accuracy`, `accuracy_text`, `_cells_five`; `score_side` / `build` take `layout` and `min_scope`.
  The default layout, its JSON and its markdown are unchanged (all 23 T-177 tests pass untouched; a T-182 test checks
  the default result has no new key).
- `tools/alsenan_keymap.py`: opt-in `--v2-five-measures` and `--v2-min-accuracy-scope` (need `--v2-out`); the v1
  outputs stay byte-identical (tested).
- `tests/t182_scoreboard_five_measures/`: 17 tests on the T-177 synthetic villa (not the development villa).

## The five columns (plus Trade / Unit / Baseline / Ref lines / Rule difference share)

| # | Column | Definition | Never |
|---|---|---|---|
| 1 | Coverage % (n / d) | reference lines the engine answers / reference lines | counts a silent or unit-refused line |
| 2 | Verified n / d | whole-scope checker re-measures of this side's compared quantity within 1 % (T-177 rule) | raised by a partial re-measure, a rule verdict, a verdict on another line or trade, a stale or > 1 % re-measure, freelancer agreement |
| 3 | Accuracy vs independent (lines, scope share) | engine vs the checker's own quantity: WAPE = sum abs(e - c) / sum c, signed = sum (e - c) / sum c, on every line with a whole-scope checker re-measure in its unit whose engine quantity this side releases; discrepant and stale re-measures INCLUDED | uses the freelancer quantity (not as reference, not as weight); counts a HELD line (listed, never 0) |
| 4 | Freelancer variance | the v1 WAPE / signed against the freelancer, with compared / reference lines | called accuracy |
| 5 | Held or UNKNOWN | the T-177 cell (bounded sums, UNKNOWN, conditional sets, NOT YET MEASURED causes) | 0 for a held line |

**Scope rule of column 3 (stated in the output JSON `five_measures_rule`).** Scope share = sum of the checker
quantities of the accuracy lines / the size of the trade and unit, where each reference line's size is its checker
quantity when one exists, else this side's released engine quantity. A reference line with neither (HELD without a
checker quantity, unit refused, silent) leaves the size incomplete: the share printed is then only an upper bound
("scope at most ...") and the cell is NOT YET MEASURED. Accuracy is reported only with >= 1 line, a complete size and
share >= `MIN_ACCURACY_SCOPE` = 0.50. The 0.50 is an initial operational value (like the 2 % / 5 % / 1 % thresholds of
WORKFLOW_CONTROLS s.1), for the Lead / owner to review with actual results; `--min-accuracy-scope` changes it per run.

Why the freelancer is not the weight: with his quantities as weights, moving his number would move the scope share
and could switch the accuracy cell between a figure and NOT YET MEASURED; the acceptance case (a smaller freelancer
variance leaves the accuracy column unchanged) fails under that variant (mutation run, below).

Why discrepant and stale re-measures stay in column 3: the checker's quantity is a property of the element measured
from the drawing, not of an engine run. Leaving the > 1 % lines out would report accuracy only where the engine was
already right. Column 2 (verified) still excludes them, as T-177 does.

## Tests (hand values written first; docstring of the test file)

Synthetic concrete bucket, 4 reference lines: checker FOOT 19.1 (engine 19.0), BEAM 10.0 (engine 10.4, stale, 4.0 %),
SLAB 8.0 (engine HELD), COL none (HELD) -> size incomplete, scope at most 29.1 / 37.1 = 78.44 % -> NOT YET MEASURED.
With a checker COL 5.0: size 42.1 complete, share 29.1 / 42.1 = 69.12 %, WAPE 0.5 / 29.1 = 1.72 %, signed
+0.3 / 29.1 = +1.03 %; minimum 75 % -> NOT YET MEASURED. Candidate (SLAB released 7.5): 3 lines, 37.1 / 42.1 =
88.12 %, WAPE 1.0 / 37.1 = 2.70 %, signed -0.2 / 37.1 = -0.54 %. Acceptance cases: four unrelated passed checks
(NO_RULE_DIFFERENCE, an agreeing PARTIAL re-measure, a whole re-measure of a floor line, a whole rule verdict on
paint) leave concrete Verified at 1 / 4; the held SLAB with a checker quantity stays in Held or UNKNOWN unchanged and is
listed NO_RELEASED_ENGINE_QTY; freelancer FOOT 20 -> 19 and BEAM 10 -> 10.4 make the variance 0.00 % while the
accuracy cell is identical (both the reported and the NOT YET MEASURED case); a missing freelancer quantity does not
remove a line from accuracy. Also: same label for released and candidate refused; heading v2.1 not matched by the
dashboard's `^## SCOREBOARD v2 ` pattern; bad minimum / layout refused; both CLIs.

Mutation runs (deliberately broken copies, restored after): (1) dropping > 1 % lines from accuracy -> 2 tests fail;
(2) freelancer quantity as the size weight -> 3 tests fail.

## Development villa (own runs of the Drive DXFs, this run)

Baseline A: `tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json` -> REPRODUCED,
1,455 lines, BOQ_LINES.csv b96185d4. Five-measures rows with the T-177 verdict file:

| Trade m-unit | Coverage | Verified | Accuracy vs independent | Freelancer variance | Held or UNKNOWN |
|---|---|---|---|---|---|
| Concrete m3 | 100.00 (8 / 8) | 0 / 8; 3 partial not counted | NOT YET MEASURED (0 lines) | WAPE 17.03 %, signed -17.03 % (3 / 8) | 5 HELD; 205 lines: 122 bounded 44.108 .. 113.540 + 83 UNKNOWN |
| Floor area m2 | 100.00 (1 / 1) | 0 / 1 | NOT YET MEASURED | NOT YET MEASURED (0 / 1) | 3 conditional sets UNKNOWN |
| Plaster m2 | 100.00 (1 / 1) | 0 / 1 | NOT YET MEASURED | NOT YET MEASURED (0 / 1) | 29 lines: 2 bounded 2.360 .. 2.600 + 27 UNKNOWN |
| Paint m2 | 100.00 (1 / 1) | 0 / 1 | NOT YET MEASURED | NOT YET MEASURED (0 / 1) | 13 UNKNOWN; 14 excluded |
| Doors / Windows m2 | 0.00 (0 / 1) | 0 / 1 | NOT YET MEASURED | NOT YET MEASURED (0 / 1) | unit refused (pcs vs m2; T-181) |

Candidate: `research/agents_t151/v303_run.py` + route G profile -> V3_0_3_BOQ_LINES.csv 5ba4ae93 (= the checker's),
scored beside its base run B's release report as separate rows: concrete B 100.00 (8 / 8), 0 / 8, accuracy NOT YET
MEASURED, variance WAPE 18.17 % / signed -17.16 % (5 / 8), 3 HELD (38 lines: 35 bounded 13.918 .. 23.871 + 3
UNKNOWN); V3.0.3 100.00 (8 / 8), 0 / 8, NOT YET MEASURED, WAPE 15.38 % / -13.04 % (3 / 8), 5 HELD (43 lines: 40
bounded 19.725 .. 36.465 + 3 UNKNOWN; 5 excluded); floor, plaster, paint, doors / windows as T-177.

Every figure that also exists in the T-177 layout is identical to the 08:15 / 12:05 rows. Accuracy is NOT YET
MEASURED everywhere because the verdict file holds no whole-scope checker re-measure yet (the pool line of T-180 is
PARTIALLY VERIFIED: steps not drawn, rebar held, so it is a partial record).

## Findings for the Lead / Checker

1. **What it takes to report concrete accuracy.** 3 of the 8 concrete reference lines are released and 5 are HELD.
   Under the scope rule, accuracy appears only when every one of the 8 has a size independent of the freelancer: the
   3 released lines have the engine's, but each of the 5 held lines needs a whole-scope checker quantity (or a
   released engine quantity in a later candidate). Re-measuring only the 3 compared lines would give accuracy lines
   but still NOT YET MEASURED. T-180's order (one line per run) can use this: held lines measured by the checker
   count as size even while the engine holds them.
2. **Verdict file.** A whole-scope REMEASURE record needs `engine_qty` = the quantity of the run it re-measured; a
   later run with another quantity keeps the record in accuracy (stale, flagged) but out of Verified.
3. **Dashboard.** The new table is under `## SCOREBOARD v2.1 <time>`; the T-132 parser (`^## SCOREBOARD v2 `) keeps
   reading the T-177 table until the main chat adapts `build_dashboard_data.py` (its job per the task row).
4. The 0.50 minimum is operational, not engineering: proposed for review once two trades have checker quantities.

Proposed lessons-register row (standard s.7): 2026-10-22 | an accuracy share could be moved by the freelancer's
number or flattered by leaving discrepancies out | accuracy and its scope weighted by the reference being scored
against | accuracy is engine vs the independent checker quantity, sizes from checker or engine only, discrepancies
included, below a stated minimum scope NOT YET MEASURED (any villa, any trade) | tests/t182 (adverse: freelancer
moved, discrepant line dropped) | READY T-182.
