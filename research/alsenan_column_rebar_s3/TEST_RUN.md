# S3 test run

Full suite (`python -m pytest -q -p no:cacheprovider`) on the S3 working tree (commit 16a64cf):

| | count |
|---|---|
| tests collected | 6198 (6168 before S3 + 30 new) |
| passed | 6095 |
| xfailed | 100 (pre-existing expected failures) |
| skipped | 3 |
| failed / errors | 0 / 0 |
| wall time | 318 s |

New in S3:
- `tests/column_rebar_engine/test_column_rebar.py` - 19 (hand-derived known answers 20x50 / 25x60 / 30x80 / 25x100,
  rate-to-level, mass conservation, conflict release, laps / starters, firewall, 11 mutation classes)
- `tests/alsenan_structural_census/test_column_rebar_s3.py` - 11 (hash consumption, reproduction, 95 -> 95,
  mass conservation, claims PROJECT_ONLY + flag lifecycle, topology / rate semantics, claim leakage, core run =
  storey interval, no verified tie / hook in core, type-conflict release, adapter raises no flag and reads no
  benchmark)

Outputs built twice byte-identical (`build_column_rebar_s3.py --twice`). Review workbook recalculated
(1248 formulas, 0 errors, every check cell OK); 95 workbook ids = 95 drawing labels.
