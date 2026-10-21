# S6 Phase 1: test results

The full suite ran on the S6 Phase 1 working tree (byte-identical to the commit), as the `pytest.ini` testpaths in two sessions run one after the other: `tests engine`, then `agents`. Package, tests and data were not edited while it ran.

The run was classified with `research/environment_recovery/classify_test_run.py` on the merged junit.

| Class | S5 | S6 Phase 1 |
|---|---|---|
| CODE_FAILURE | 0 | 0 |
| EXECUTED_PASSED | 7740 | 7810 |
| EXPECTED_FAILURE | 100 | 101 |
| MANDATORY_BLOCKED_BY_MISSING_DATA | 376 | 376 |
| SKIPPED_OTHER | 6 | 10 |
| SKIPPED_PREREQUISITE_UNAVAILABLE | 146 | 146 |
| total | 8368 | 8443 |

Gate: **INCOMPLETE**. Reasons: 376 mandatory regression tests blocked by missing data; 146 tests skipped for an unavailable prerequisite; 108 locked prerequisites missing {'BENCHMARK': 14, 'DERIVED': 87, 'SOURCE': 7}.

Code-failure tests: none.

## What the S6 Phase 1 tests cover (`tests/m9_s6`)

- **Admission**: 9 unmeasurable variants each stop with exit 2 and no BOQ. Also covered: the admitted baseline, units given by a reviewer, paper-space sheets with reviewer regions, an accepted XREF, reviewer inputs refused for V1, an earlier BOQ moved aside, hidden-layer flags, K2 dispositions, the FATAL rule and the gate rule.
- **DWG** (fake converter only): empty, garbage, stale and same-name conversions, and the CLI exit 2 for V2 and V1 strict.
- **Tolerances**:
  - `unit_tol` is exactly 1.0 at mm;
  - the legacy defaults are the old literals, and the frozen `band_gaps` is called at 1.0;
  - the unit-relative copy reproduces the frozen function;
  - V2 at mm keeps every V1 quantity;
  - mm / cm / m / inch give identical quantities;
  - V1 strict refuses a metre drawing;
  - one strict xfail records S6P1-NEW-05.
- **Regions**: two plans in one frame, the V1-strict cut stop and its control, frames drawn as lines, the sheet frame on the wall layer, `xy_cut` never cutting geometry, and region override validation.
- **Completeness**: the coverage gate, the three views kept apart, strips reviewed individually, the surfaces V1 left silent, full-height tile, exterior scope, and exit 3 on an unaccounted surface.
- **Entity completeness**: the baseline columns, 8 lost-column variants flagged on their room, WCS fills at every depth, the layer filter, unread fills, distorted door blocks.
- **Frozen**:
  - the V1 snapshot from 6b7a2e4;
  - V2 keeps every V1 line;
  - V1 never runs the admission;
  - V1 strict adds only the report;
  - structural conventions: a warning for V1, required for V2.
- **Real plan** (env-gated): V2 admitted and complete on every floor, V1 lines kept, every strip reviewed, every column fill measured, V1 strict admitted.
- **Hygiene**: notes, tests and new modules carry no identity; the new engine modules are stdlib-only.

## Real-drawing tests (run separately, private drawing)

```
============================= 18 passed in 39.82s ==============================
```

## Sweeps (production CLI, separate processes)

- 31 synthetic variants: HEAD V1 has 22 silent failures. V2 has 0 (9 blocked, 10 flagged, 12 identical). V1 strict has 0 (12 blocked, 10 flagged, 9 identical).
- 6 DWG cases with the fake converter. HEAD V1: D1 (empty), D2 (stale), D4 (same name) and D6 (plan = structural) are silent; D3 (garbage) crashes; D5 (no conventions) runs on the defaults. V2 blocks D1, D2, D3, D5 and D6 with exit 2 and keeps D4 apart. V1 strict blocks D1, D2, D3 and D6, keeps D4 apart, and warns on D5.
- 4 finish cases: V1 is silent on 3 (the band above tile, the stair hall, the strips). V2 gives an RFI line for every surface. The diacritic case is unchanged in both (an ARCH.SPACE RFI).
- V1 byte identity: the synthetic villa (15 files) and the reference plan (16 files) match the hashes taken at 6b7a2e4.
