# S2 — test run record

Full suite (`python -m pytest -q -p no:cacheprovider --junitxml=...`), started on the S2 working tree:

| Result | Count |
|---|---|
| passed | 6,065 |
| xfailed (expected, pre-existing) | 100 |
| skipped | 3 |
| failed / errors | 0 |
| total collected | 6,168 |
| wall time | 393 s |

Previous record (S1): 6,042 passed / 100 xfailed / 3 skipped. The +23 are the new tests:
15 generic synthetic tests (`tests/structural_review_engine/`), 7 Alsenan S2 adapter tests
(`tests/alsenan_structural_census/test_flags_s2.py`) and 1 review-manifest guard
(`tests/alsenan_structural_census/test_census_s1.py`).

Two small edits landed while this run was in progress: the wording of the summed affected-quantity line in
`engineering_flags.summary` and one tightened assertion in `test_flags_s2.py`. After them, the 65 S2-related
tests (`tests/structural_review_engine` + `tests/alsenan_structural_census`) were re-run on the committed tree
(94140bd): 65 passed.
