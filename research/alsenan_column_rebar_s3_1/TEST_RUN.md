# S3.1 test run

Full suite (`python -m pytest -q -p no:cacheprovider`) on the S3.1 working tree (baseline b6a8fef):

| | count |
|---|---|
| tests collected | 6237 (6198 before S3.1 + 39 new) |
| passed | 6134 |
| xfailed | 100 (pre-existing expected failures) |
| skipped | 3 (pre-existing) |
| failed / errors | 0 / 0 |
| wall time | 303 s |

New in S3.1:
- `tests/structural_comparison_engine/test_s31_engines.py` - 24 (the 20 brief cases: rough ratio is sanity only,
  BBS incomplete side by side, unknown class not configured, joint mapping, comparability without %, oracle
  pagination / failure, region crossing, open polyline, unreadable text, structured evidence, single geometry
  authority, population discovery, parapet scenario, source roles; plus the §26 firewall, unit mass, '/m' notation
  and section transitions)
- `tests/alsenan_structural_census/test_multi_engine_s3_1.py` - 15 (S3.1 index + S3 untouched, headline split,
  one unit-mass method, transitions blocked, freeze recorded first and still holding, lineage sums, scope notes,
  no % on NOT_COMPARABLE, profile = engine profile, rough never replaces actual, population completeness,
  oracle register, rebuild reproduces)

S3.1 and comparison outputs built twice byte-identical (`--twice`). Review workbook recalculated (560 formulas,
0 errors, all 8 lineage checks OK).
