# Control-plane audit R1: test run

Full suite: `python3 -m pytest -q -p no:cacheprovider -rxXs`, run from the repository root on the commit that adds this folder. Exit status 0.

| | Baseline (handoff round) | This round | Delta |
|---|---|---|---|
| Tests | 5,875 | 5,933 | +58 |
| Passed | 5,780 | 5,815 | +35 (new diagnostic tests) |
| Xfailed | 92 | 115 | +23 (control gates G01–G23, all `strict=True`) |
| Skipped | 3 | 3 | 0 (unchanged: real-source row unset; QS_MEASUREMENT_REGION_BUILDER absent ×2) |
| Failed / errors | 0 | 0 | 0 |
| Unexpected passes (XPASS) | 0 | 0 | 0 |

**New file:** `tests/alsenan_control_plane/test_control_plane_r1.py`.
- 35 tests pass:
  - characterisation of D1–D6, C, B, D, J and SD-04 / 08 / 11 / 12;
  - three seeded property / metamorphic tests;
  - register / evidence integrity and code-anchor tests.
- 23 control gates are expected failures. Each was checked with `--runxfail` and fails on its own `AssertionError`, not on an incidental exception.

**Production code changed: none.** `git status` shows only the two new folders.
