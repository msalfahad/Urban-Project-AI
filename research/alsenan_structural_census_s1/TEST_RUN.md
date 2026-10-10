# Round S1 — test run record

Full suite, run on the commit that added the S1 census (`606efec`), with
`python -m pytest -q -p no:cacheprovider --junitxml=...`:

| Result | Count |
|---|---|
| passed | 6,042 |
| xfailed (expected, pre-existing) | 100 |
| skipped | 3 |
| failed / errors | 0 |
| total collected | 6,145 |
| wall time | 289 s |

Previous round (Round 5): 6,015 passed / 100 xfailed / 3 skipped. The +27 are the new
`tests/alsenan_structural_census/test_census_s1.py` tests; nothing else changed state.

S1 registers: built twice byte-identical (`INDEX.json: built_twice_identical = true`);
`test_rebuild_matches_frozen_registers` reproduces every register hash from the DXF;
`test_rebar_untouched` confirms the Round 3 / Round 4 rebar registers are unchanged.
