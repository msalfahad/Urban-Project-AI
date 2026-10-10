# S8.3A TEST_RUN: dome-shell reinforcement distribution audit

Baseline HEAD `6ddd988`. Commits of the round:

| Commit | What it holds |
|---|---|
| `4c63445` | The layout engine `engine/source/shell_line_distribution.py`, the S8.3A package (10 outputs + builder) and its 16 tests |
| this commit | This record and the gate report `TEST_GATE_4c63445.json` |

S8.3A moves **no quantity**. The frozen S8.3 manifest (`92bfe9c0b2b7…`, 32 files) and the three S8.3 errata files
verify before and after the build. The 602.111304 kg stays PROJECT_BASIS_QTO, now classified
IDEALIZED_SURFACE_DENSITY_QTO.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/dome_mesh_s8_3a tests/dome_ring_s8_3 tests/structural_comparison_engine tests/r8_0/test_r8_0_import_boundaries.py tests/r8_1/test_r8_1_boundaries.py tests/environment_recovery
```

158 passed and 1 xfailed at `4c63445`. The xfail is the recorded B-7 boundary debt (two engine modules import a
research parameter file). It predates S8.3A.

| File | Tests | Covers |
|---|---|---|
| `test_shell_line_distribution.py` | 6 | Synthetic known answers only. See the list below |
| `test_s8_3a_package.py` | 10 | See the list below |

`test_shell_line_distribution.py` tells the layout rules apart:

- **Uniform density is not a fixed-meridian layout.**
  - Fixed meridians carry ψ0·cot(ψ0/2) times the density.
  - That is π/2 on a hemisphere and 2 for a very shallow cap.
  - The two never agree for a cap no deeper than a hemisphere.
- **Fixed meridians:** an unrounded count of 2πa/s, each one R·ψ0 long.
- **Hoops at spacing s along the meridian** give exactly A/s.
  - Midpoint sums converge to it.
  - A set that starts on the rim is biased long.
- **Variable circumference:** the meridian spacing shrinks as sin ψ to zero at the crown. The crowding radius is
  checked.
- **Termination and crowding:** halving curtailment at 75 mm lies between the density and the uncurtailed meridians.
  - Frequent curtailment tends to the density.
  - Rare curtailment tends to the fixed meridians.
  - An invalid minimum spacing is refused.
- **Fabrication rounding is never the continuous quantity:** the counts are ceil(meridians) and floor(hoops) + 1.

`test_s8_3a_package.py` covers:

- S8.3 and its errata untouched, and the S8.3A manifest verifying;
- scenario A reproducing the frozen 08 register exactly;
- scenario B recomputed from first principles (≈ 798.915 kg);
- nothing released;
- the status changes;
- the drawing evidence;
- no double count against the S8.3 errata;
- the missing evidence ME-01 to ME-07;
- blindness tokens and the registry;
- a byte-identical rebuild, which needs the private drawings.

The density test (scenario A) is checked only as a reproduction of the frozen figure. It is never used as evidence of a
physical meridian layout.

The builder was run twice with byte-identical output (10 files).

There was also an independent cross-check outside the engine. It is a scratch script, not a tracked test:

- **Method:** a plain midpoint integration along the meridian, 200,000 steps.
- **Inputs:** the mid-surface rebuilt straight from the printed chord 4.42, rise 1.90 and t 0.10.
- **Scenario C rule:** the meridian count halves wherever the spacing drops below 75 mm.

It reproduced every scenario:

| Scenario | Integration | Engine |
|---|---|---|
| A | 602.1113 kg | 602.111304 kg |
| B | 798.915 kg | 798.914968 kg |
| C | 678.9361 kg | 678.936390 kg |

### Defects found and fixed before the freeze

Two of the synthetic tests failed on the first run:

1. **A wrong claim in the engine docstring and the test.** It said the two rules agree for a very shallow cap. The ratio
   tends to 2 there, not 1. The docstring and the assertion were corrected.
2. **A silent truncation in `halving_curtailment`.** The loop stopped after 200 levels, which cut the series short
   when the minimum spacing was close to the nominal one. It now runs to the crown and raises an error if it fails to.

The S8.3A scenario C needs 37 levels, so its figure (678.936390 kg) was unchanged by the fix. A rebuild changed only
`08_S8_3A_SUMMARY.json` and `09_S8_3A_FREEZE_MANIFEST.json`, through the code hash.

## Full suite: NOT GREEN, gate INCOMPLETE

`python3 -m pytest -o addopts="" -q -rfEs -p no:cacheprovider --junitxml=...` was run on the clean committed tree
`4c63445`. No file was edited during the run.

| Run | Commit | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|---|
| 8 | `ac788a5` (S8.3 errata) | 6748 | 344 | 32 | 138 | 100 | 353.0 s | 1 |
| 9 | `4c63445` (S8.3A) | **6764** | 344 | 32 | 138 | 100 | 302.4 s | 1 |

- The 16 extra passes are this round's 16 tests. All of them executed and passed.
- The blocked, code-failure and prerequisite-skipped test sets are identical to run 8's.

### Every test, classified (`classify_test_run.py`, run 9)

| Class | Tests | Meaning |
|---|---|---|
| 1. Executed and passed | **6764** | The only class that proves anything |
| 2. Legitimately skipped: prerequisite unavailable | **136** | A private input, fixture, client data or generated artefact is absent. Never counted as a pass |
| Skipped for another reason | 2 | `QS_MEASUREMENT_REGION_BUILDER does not exist yet` |
| Expected failures (xfail) | 100 | Recorded by the tests themselves |
| 3. Mandatory regression blocked by missing data | **376** | Failed or errored on a missing required file |
| 4. Actual code failures | **0** | |

The 376 blocked tests, by missing path:

| Missing | Tests |
|---|---|
| `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/...` | 373 |
| `data/runs/7757/...` | 1 |
| A generated prerequisite (`run workbook_boq first`) | 1 |
| A session upload under `/root/.claude` | 1 |

**Complete-project regression gate: INCOMPLETE.**

- 376 mandatory regression tests are blocked by missing data.
- 136 tests are skipped for an unavailable prerequisite.
- 108 locked prerequisites are missing: 14 BENCHMARK, 87 DERIVED and 7 SOURCE.

The gate stays INCOMPLETE until the private fixtures and the sealed benchmark evidence are restored.

- The blind builders never read benchmark truth.
- Test IDs and missing paths are in `TEST_GATE_4c63445.json`.
- That file holds no content and no benchmark value.

## Limitations

- The full suite is red because private data is missing. No missing-data skip is presented as a pass.
- The drawing-dependent S8.3A tests skip when the private drawings are absent. The synthetic engine tests always run.
- Scenarios B, B-FAB and C are sensitivity only.
  - C rests on a stated test rule (alternate meridians stop where the spacing halves). The source shows no curtailment.
  - None of them is a lower bound, an upper bound or a BBS.
- No old Urban, freelancer, contractor or donor figure was read (`references_read: []`).
