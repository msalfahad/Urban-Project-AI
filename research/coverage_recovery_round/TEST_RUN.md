# Coverage recovery round: test run

Full suite run from the working tree at commit `9f1fa79`:

    python -m pytest -q -p no:cacheprovider --junitxml=<scratch>/cr2.xml

| Collected | Failed | Errors | Skipped | Time |
|---|---|---|---|---|
| 6310 | 0 | 0 | 103 | 241.7 s |

The previous baseline (RF.1, `24bd540`) was 6265 tests with 0 failed.

## What the first full run caught (fixed in `9f1fa79`)

| Test | Cause | Fix |
|---|---|---|
| `tests/r8_1/test_r8_1_boundaries.py::test_nothing_outside_tests_imports_engine_source_yet` | `engine/__init__.py` and the `bbs_steel` deprecated wrapper imported `engine.source.rebar_sanity_qa` | Added a production-layer mirror, `engine/rebar_sanity_qa.py`, and a parity test that keeps the two copies identical |
| `tests/r8_2/test_r8_2_paths_and_pins.py::test_no_production_module_consumes_the_source_engine_yet` | Same cause | Same fix |
| `tests/r8_1/test_r8_1_boundaries.py::test_k1_is_stdlib_only_in_r8_1` | `ground_slab_recovery.decompose()` imports shapely lazily | Declared by design, the same way as `topology_crosscheck.py`. `classify()` and `quantities()` remain stdlib-only |

## Round-specific suites

- `tests/coverage_recovery_engine/test_coverage_recovery.py`: the 20 synthetic cases, the donor regressions, the sanity tiers and the neck mapping.
- `tests/coverage_recovery_engine/test_alsenan_coverage_round.py`:
  - INDEX hashes and freeze integrity; the freeze was written blind;
  - no donor or reference number appears in the blind outputs, the blind scripts or the new engine modules;
  - population conservation and the dashboard scenario invariants;
  - every slab deduction carries an opening id;
  - a rebuild reproduces the frozen outputs (this ran; it was not skipped).
- `tests/structural_comparison_engine/test_rebar_product_firewall.py`: the RF.1 firewall plus the QA-layer shim checks and the production/source parity check.
