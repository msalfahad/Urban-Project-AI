# Phase 2B-0: test results, regression classification and frozen-version integrity

**Commits:**
- `9875f40`: code, tests and the blind-readiness files.
- The next commit adds these reports, the findings records F-25 … F-32 and `tests/m9_p2b0/test_p2b0_metamorphic.py`.
- The affected suites were re-run on that commit's tree (section 2.2).

## 1. Frozen-version integrity

| Check | How | Result |
|---|---|---|
| V1, V2 and V2.1 outputs unchanged | CLI `arch` with each method, on the synthetic villa, its mirror and the reference plan, byte-compared with the snapshot taken at `981ef5f` before any edit. Repeated after every stage. | **168 / 168 files identical** at the end (V1 46, V2 52, V2.1 70) |
| Frozen artefacts | `tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl` | **0 artefacts differ** |
| Route G, historical packages, `opening_census.py`, `rules/` | `git diff --name-only 981ef5f` | **untouched**. Changed code: `engine/source/{arch_measure,arch_rooms,door_model,surface_ledger}.py`, `tools/urban_boq_m9.py`; new: `engine/source/release_safety.py` |
| Default paths unchanged | every new branch is guarded by a keyword that only `ARCH_TAKEOFF_V2.2` passes (`release_safety`, `guards`, `conserve`) | defaults off; covered by the byte-identity row |
| `engine/source` stays stdlib-only | imports of `release_safety.py`: `__future__`, `math`, `collections` | **yes** |
| Findings register | append-only hash chain (`FV.read_chain`, `append_only_history`) | 8 records appended (F-25 … F-32); chain valid; `tests/zz_freeze_integrity` 19 passed |
| V2.2 deterministic | two V2.2 CLI runs of the three drawings | **70 / 70 files identical** |
| Blind-evaluation freeze | `tests/m9_p2b0/test_p2b0_blind_freeze.py` against `BLIND_READINESS_RECORD.json` | passed |

## 2. Test runs

### 2.1 Full suite at `9875f40`

**Setup:**
- Where: the private clone used for the Phase 2A baseline. It has `data/inputs` and no real-plan variable.
- Command: `python3 -m pytest -p no:cacheprovider --basetemp=<tmp>/bt --junitxml=<tmp>/junit.xml`.
- Time: 15 min 54 s. A second suite was running in parallel.

| Run | Collected | Passed | Failed | Errors | Skipped | xfailed |
|---|---|---|---|---|---|---|
| Baseline `e78f6bd`, same clone | 8,557 | 7,921 | 345 | 32 | 157 | 102 |
| **`9875f40`** | **8,597** | **7,958** | **345** | **32** | **160** | **102** |

**The suite is not passing:** 377 failures and errors remain. All of them are classified below, and none is caused by this phase.

**Classification:**
- **New failures: 0.** The 345 failures and 32 errors are the same test ids as the baseline. No baseline failure disappeared either.
- **The 377 baseline failures and errors**, as classified in `research/urban_m9_p2a_acceptance/TEST_RESULTS_AND_WEAKNESSES.md` §2.1:
  - 373 are `FileNotFoundError` on the gitignored `data/experiments/...` datasets;
  - 1 is a missing `data/runs/...` output;
  - 1 is "run workbook_boq first";
  - 1 is a client upload from an earlier session;
  - 1 is the clone-layout artefact `test_m5_package.py::test_live_reproduction_of_every_committed_text_file`, which passes in the main repository.
  - **Code failures: 0.**
- **New tests: 40.**
  - 35 in `tests/m9_p2b0`, plus the 5 `tests/m9_p2a/test_p2a_blind_scoring.py` tests added at `981ef5f`.
  - 36 pass. 4 skip: the reference-plan tests, which need `URBAN_REAL_PLAN_DXF`. They are run in 2.2.
- **One existing test changed state:** `tests/m1_usable_boq/test_m1_package.py::test_workbook_if_present` went from skipped to passed. The git-ignored workbook it checks now exists in the clone. This is environment, not code.

**Cross-check:** a fresh clone at `981ef5f`, without `data/inputs`, gives 358 failed, 32 errors and 210 skipped. The extra failures and skips come from the missing local data. That run is kept only to show the environment dependence, and the e78f6bd comparison above uses the same clone on both sides.

### 2.2 Affected suites, with the reference plan

**Setup:**
- Environment: `URBAN_REAL_PLAN_DXF` = the private plan.
- Tree: the working tree of the reporting commit.

| Suite | Passed | xfailed | Failed |
|---|---|---|---|
| `tests/m9_p2b0` (F-24, F-17, doors, F-21, blind freeze, metamorphic) | 42 | 0 | 0 |
| `tests/m9_p2a` (including the blind scorer) | 99 | 1 (F-9 strict xfail) | 0 |
| `tests/m9_s2_arch` | 61 | 0 | 0 |
| `tests/m9_s6` | 74 | 1 (earlier xfail) | 0 |
| `tests/zz_freeze_integrity` | 19 | 0 | 0 |
| **Total** | **295** | **2** | **0** |

### 2.3 Failing before the fix, passing after

The "before" logs are kept privately. Each was run with the real-plan variable set, against the code before that fix.

| Defect | Test file | Before the fix | After |
|---|---|---|---|
| F-24 / F-26 | `test_p2b0_f24_deductions.py` | 5 of 10 failing | 10 / 10 |
| F-17 | `test_p2b0_f17_skirting.py` | 2 of 7 failing | 7 / 7 |
| F-18, F-19, F-20, F-22 + invariants | `test_p2b0_door_guards.py` | 8 of 9 failing or erroring (only the V2.1 characterization passed) | 9 / 9 |
| F-21 | `test_p2b0_f21_ledger.py` | 5 of 7 failing | 7 / 7 |
| Blind freeze | `test_p2b0_blind_freeze.py` | n/a (the record did not exist) | 2 / 2 |
| V2.2 metamorphic | `test_p2b0_metamorphic.py` | n/a (new property test) | 7 / 7 |

- Each file keeps a **V2.1 characterization test**: the frozen defect is still present in V2.1, unchanged.
- **V2.2 metamorphic property:** wall-finish and skirting lines (released, ranged and blocked) are identical after each of:
  - translation to 10⁷;
  - rotation by 90°, 37.37° or a random angle far from the origin;
  - mirroring;
  - mm → m.
- It holds on five Phase 2B-0 fixtures and the villa's first floor. The ground floor is excluded under rotation because of F-9: rotated columns are lost. A private wider run also showed 0 differences, for V2.1 and V2.2 alike. It used 9 transforms, on both villa floors, with rotations on the first floor only, plus all 5 fixtures.

## 3. Proof that unaffected quantities are invariant

**Synthetic villa and its mirror, Mode U and Mode A (synthetic heights):** V2.2 equals V2.1 on 85 / 85 lines, in evidence state, net and range.

**Reference plan, Mode U:**
- 413 lines are unchanged.
- The only differences are the predicted ones:
  - 3 ARCH.PASSAGE lines become PROVISIONAL (lift candidates);
  - 9 FIN.SKIRTING lines are released lower, plus 9 range lines;
  - 2 door lines leave the released totals (1 held, 1 class review).

**Fixtures:**
- `test_every_other_quantity_is_unchanged` in the F-24 and F-17 files compares every non-target line of V2.2 with V2.1.
- Without heights, all lines are identical.

**Reference plan, Mode A:** V2.1 has no output (`LineError`), so invariance there can only be shown in Mode U.
