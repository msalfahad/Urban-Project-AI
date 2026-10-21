# Full-suite comparison (Phase N10)

**The full suite is not green.** 345 failures and 32 errors remain at the final code commit. They are the known legacy failures from before N10 (§3).

## 1. Runs

Every run used a fresh clone of the named commit and `python3 -I` with its own `--basetemp`. The clone links the git-ignored private inputs folder `data/inputs`, as in earlier phases. pytest exits 1 on every run because of the known failures.

| Run | Commit | Tests | Passed | Failed | Errors | Skipped | xfailed | Time |
|---|---|---|---|---|---|---|---|---|
| baseline | **504b56a** | 9,343 | 8,700 | 346 | 32 | 160 | 105 | 32 min 16 s |
| first N10 run | **4b299ae** | 9,413 | 8,769 | 346 | 32 | 161 | 105 | 29 min 20 s |
| **final** | **24db651** | **9,413** | **8,770** | **345** | **32** | **161** | **105** | 29 min 48 s |

24db651 is the final code commit. Later commits change documentation and the generated maps only.

## 2. Test-by-test comparison, by identity (JUnit)

**Baseline 504b56a → final 24db651:**

| Comparison | Count | Detail |
|---|---|---|
| new tests | 70 | `tests/m9_n10`: curved 21, independent curved 6, masonry 11, facade 14, structural 14, registry 4. **All passed** |
| removed tests | 0 | |
| **passed → failed / error** | **0** | |
| failed → passed | 1 | the session guard (`tests/zz_freeze_integrity/test_zz_fi_session_guard.py`): the baseline's one new failure, fixed in dec6766 (D-N10-00) |
| passed → skipped | 1 | `tests/m1_usable_boq/test_m1_package.py::test_workbook_if_present`. **Environmental, not N10** (below) |
| other state changes | 0 | |
| failing set | 377 | a strict subset of the baseline's 378; none new; none in `tests/m9_*` |

**What the first N10 run (4b299ae) found, and how it was fixed:**

| Test | 504b56a | 4b299ae | 24db651 | Cause |
|---|---|---|---|---|
| `tests/structural_comparison_engine/test_rebar_product_firewall.py::test_every_rebar_module_in_engine_is_declared` | passed | **failed** | passed | D-N10-05: the new `engine/source/struct_n10.py` names reinforcement but was not declared in the rebar product firewall registry. Fixed in 24db651 (declared as OTHER_REBAR_AWARE). Reproduced before the fix, 54 passed in the folder after |

The targeted runs during the phase did not include this static-scan folder. `TEST_COMMANDS.md` now lists it.

**The pass → skip, explained.**

- The test skips when the git-ignored workbook `research/…/boq/STRUCTURAL_BOQ.xlsx` is absent. A later test in the same module writes it.
- In the baseline clone the workbook already existed from an earlier targeted run in that checkout. In the fresh N10 clones it did not, so the test ran before the workbook was written.
- In the 4b299ae clone, after the suite had written the workbook, the same test **passes** (1 passed).
- No N10 change touches that package.

## 3. Known failures, carried forward

- 345 failed and 32 errors: **377** tests in **26** legacy test modules. They are identical, test by test, to the 377 failing at the end of Phase 2B-9 (JUnit of the 065f3de run).
- The modules read git-ignored private datasets and workbooks that are not in the repository. None of them is in `tests/m9_*`.
- They are never reported as passing.

## 4. Conclusion

At 24db651 the full-suite run found **no newly introduced regression**:

- 0 tests went from pass to fail;
- the 70 new tests pass;
- the one regression found at 4b299ae (D-N10-05) is fixed;
- the one pass → skip is environmental and explained.

**The suite is not green** because of the known legacy failures. This result belongs to commit 24db651.
