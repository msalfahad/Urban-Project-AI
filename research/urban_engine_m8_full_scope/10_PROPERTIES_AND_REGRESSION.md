# 10 Properties and regression

## V5 and the frozen packages are unchanged

Every M8 behaviour is switched by a V6 convention:
- `generic_route.detect_options` adds `scope_from_findings` / `tread_angle_wrap` only when the conventions carry
  them;
- the completeness pass changes only under that option;
- `family_coverage` changes only when bounds are passed.

The checks:

| Check | Result |
|---|---|
| ST7757 under V5 before and after M8 (items, BOQ, coverage, findings, risk records) | identical |
| M7 quantity rows, seeds 301–340, both vocabularies (572 rows) | 0 moved against the stored M7 V5 records; 0 SILENT under V6 |
| Core families of every M8 synthetic villa, V5 against V6 | 0 rows moved (S_A, S_B; 80 villas) |
| Core families of ST7757, V5 against V6 | footings, columns, ground beams, ground slab, beams, slabs and lintels: no measured change (`st7757/BY_FAMILY.csv`) |
| M7 freeze test | M7's own freeze test accepts the files that M8's freeze records as changed since M7, and nothing else |
| Frozen packages M2–M7 | their package tests pass inside the full suite (below) |

## Metamorphic properties with the scope pass

Tool: `tools/m7_metamorphic.py --completeness`, conventions V6. The runs used held-out villas 401–410 with every
operation. The harness compares items by family / storey / category, and the bounded RC / plain totals.

| Operation | Frozen engine: pass / items invariant | Post-freeze: pass / items invariant |
|---|---|---|
| translate | 10 / 10 | 10 / 10 |
| rotate 90 | 7 / 10 | 10 / 10 |
| rotate 180 | 9 / 10 | 10 / 10 |
| rotate 270 | 8 / 10 | 10 / 10 |
| mirror | 0 / 10 | 0 / 10 |
| reorder | 10 / 10 | 10 / 10 |
| explode polylines | 10 / 10 | 10 / 10 |
| duplicate texts | 10 / 10 | 10 / 10 |
| unit change | 7 / 10 | 10 / 10 |
| unrelated furniture layer | 0 / 8 | 3 / 9 |

**What stays open after P1–P4:**

| Operation | Measured items | Bounded total | Cause |
|---|---|---|---|
| Mirror | invariant on every villa | low moves on every villa | pre-existing, the intake (W8-02): a mirrored HATCH keeps its boundary in object coordinates (negative extrusion), so the completeness pass loses the hatch-on-member finding and its negative bound |
| Unrelated furniture layer | invariant on 9 of 10 villas; villa 408 changes a GF slab under noise in V5 as well | widens | pre-existing slab-engine behaviour (W8-03): column-sized rectangles on the noise layer are reported as possible columns (LOW, "confirm it is a column") |

## Post-freeze fixes (each with its own record)

| Fix | What | Found by | Effect |
|---|---|---|---|
| P1 | stair flights are read one layer at a time and never from a non-structural layer | held-out property noise_layer, seed 401: a furniture line in a stair well joined the flight | 7 held-out stair elements moved closer to their flight truth; noise no longer changes a stair |
| P2 | a referenced family is "possibly drawn" only by a structural group on the noted plan | a furniture group beside a tank note dropped the tank allowance; a foundation pit dropped the allowance of a roof tank | ST7757 bounds unchanged against the pre-freeze run; no held-out element changed |
| P3 | the harness compares bounded totals at their 1-litre precision | rotations and the unit change differed in the reported third decimal only | rotations and units pass on all 10 villas |
| P4 | every scope rule has its own switch (`DOME_ON_TOP_PLAN`, `STAIR_LOOSE_FLIGHT`, `PRINTED_DIMENSION_NOTES`, `FINDING_BOUNDS`, `STOREY_PLAN_MISSING_BRACKET`) | the ablation needed each rule removable alone | with every V6 convention present nothing changes (ST7757 items and bounds identical) |

## Development-time property fixes

These came before the freeze; the M8 conventions record each one's reason.

| Fix | Why |
|---|---|
| `STAIR_TREAD_ANGLE_WRAP` | the slab engine binned tread directions without wrapping at 180°, so a 180° rotation split a flight. V5 keeps the frozen binning; seed 7 of the development set fails rotate 180 under V5 as well |
| A tolerant face boundary for stair-well lines | a flight's end lines on the well's own boundary were in or out by floating noise |
| `NON_STRUCTURAL_LAYERS` | furniture rectangles became pits and domes |
| The plot-outline guard | a plot line round every slab face is not a slab region |

## Full suite

**Command.** Run on the package tree:

```
python3 -m pytest -o addopts="" -p no:cacheprovider --junitxml=junit_m8.xml
```

**Classification.** `research/environment_recovery/classify_test_run.py`; the reduced record is `TEST_GATE_M8.json`.

| Class | M8 (`f541448`) | M7 |
|---|---:|---:|
| EXECUTED_PASSED | 7512 | 7476 |
| CODE_FAILURE | **0** | 0 |
| MANDATORY_BLOCKED_BY_MISSING_DATA | 376 | 376 |
| SKIPPED_PREREQUISITE_UNAVAILABLE | 136 | 136 |
| SKIPPED_OTHER | 2 | 2 |
| EXPECTED_FAILURE | 100 | 100 |

- **Raw pytest:** 344 failed, 7512 passed, 138 skipped, 100 xfailed, 32 errors in 10 min 29 s.
- **The failures are not code failures.** The 344 failures and 32 errors are the same 376 tests blocked by missing
  data as at M1–M7:
  - 373 under `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01`;
  - 1 needing the private reconciliation document under `data/runs/7757`;
  - 1 generated prerequisite;
  - 1 private path outside the repository.
- **Passes: +36**, exactly the 36 M8 tests. No earlier test changed state.
- **The first run (`3441d5e`) had 1 code failure.** `test_every_rebar_module_in_engine_is_declared` found
  `scope_quantities.py`, which names reinforcement only to mark the new families' steel MISSING_DATA.
  - The fix (`f541448`) declares it in the rebar product registry of the tests, as M6 did for
    `concrete_completeness`. No engine file changed.
  - The whole suite was then run again; the table above is that second run.
- **Gate: INCOMPLETE.** 376 tests are blocked by missing data, 136 are skipped for a prerequisite, and 108 locked
  prerequisites are missing. Only EXECUTED_PASSED proves anything; a skip is not a pass.
