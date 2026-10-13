# P2-00 Stage 1: freeze integrity verification report

**Scope: Stage 1 only.** It is add-only and was approved as D1.

What Stage 1 did **not** do:
- implement any Phase 2A geometry;
- change production code;
- change historical BOQs, route G or benchmark files;
- change any frozen output or manifest;
- change any owner rule.

**Stage 2 has not been started.** Its proposal is in `PROPOSED_STAGE2.md` and awaits review.

**Labels used:**

| Label | Meaning |
|---|---|
| **[VERIFIED]** | reproduced by a command recorded here |
| **[INFERENCE]** | engineering reasoning |
| **[OWNER]** | needs the owner |

## 1. Changed files

`git diff --name-status 70835ea..23cf674`, where `70835ea` is the round-2 notes commit. **Every entry is `A` (added). Nothing was modified or deleted.**

| Status | File |
|---|---|
| A | `research/freeze_integrity/ENGINEERING_FINDINGS.jsonl` |
| A | `research/freeze_integrity/ENVIRONMENT_LOCK.json` |
| A | `research/freeze_integrity/ERRATA.jsonl` |
| A | `research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl` |
| A | `research/freeze_integrity/PHASE2A_ACCEPTANCE_ADDENDUM.csv` |
| A | `research/freeze_integrity/PROPOSED_STAGE2.md` |
| A | `research/freeze_integrity/PROPOSED_STAGE2_ALTERNATIVE.diff` |
| A | `research/freeze_integrity/README.md` |
| A | `research/freeze_integrity/stage2_threshold_shift_check.py` |
| A | `tests/zz_freeze_integrity/__init__.py` |
| A | `tests/zz_freeze_integrity/test_fi_verifier_synthetic.py` |
| A | `tests/zz_freeze_integrity/test_zz_fi_session_guard.py` |
| A | `tools/freeze_verify.py` |


- **Nothing under `engine/` changed.**
- `tools/` gained one new file, `tools/freeze_verify.py`. No existing tool changed. The verifier is stdlib-only, and no production module imports it; a test enforces both.
- Two runs live outside the repository: the private architectural-baseline config (it names the reference drawing) and the verifier reports.

## 2. Environment lock (D5) [VERIFIED]

**`ENVIRONMENT_LOCK.json`:** CPython **3.11.17** and **63 packages** at exact versions (`pip freeze --all`). Among them:

| Package | Version |
|---|---|
| ezdxf | 1.4.4 |
| numpy | 2.4.6 |
| shapely | 2.2.0 |
| openpyxl | 3.1.5 |
| scipy | 1.17.1 |
| pymupdf | 1.28.2 |
| pypdf | 6.19.0 |
| pillow | 12.3.0 |
| matplotlib | 3.11.2 |
| pytest | 9.1.1 |

**How it is enforced:**
- The verifier compares the running interpreter and its package set with the lock. It reports `PASS` only inside it.
- A clean run outside the lock reports `NOT_A_PASS_OUTSIDE_THE_LOCKED_ENVIRONMENT`; the synthetic test exercises this.
- Python 3.13.16 on the same machine differs from the lock in its version and in **62 packages**, so no 3.13 result can be a pass. Round 2 showed why: 10 freezes differ there in the last binary digits of a float.
- With `URBAN_REQUIRE_LOCK_ENV=1`, the guard test also fails any session that runs outside the lock.

## 3. Immutable baseline: the proof (requirement 1) [VERIFIED]

**The baseline index:** `FREEZE_BASELINE_INDEX.jsonl`, append-only and hash-chained, records:
- **37 freeze manifests**;
- **495 distinct non-code research artefacts** that they pin;
- the V1 synthetic snapshot;
- **4 owner rule files** (`rules/owner_decisions`, `rules/owner_library`, `rules/methods`).

**Check of the working tree against the index:** 0 differences.

**A rebuild can no longer overwrite its comparison baseline unnoticed:**
- **The verifier never rebuilds in the repository.** It uses a disposable git worktree, runs each test alone from a pristine tree, compares against the committed git objects, and then removes the worktree.
- **Every verifier run below reports `repository unchanged: True`.** That compares `git status` and HEAD before and after.
- **Isolating each test fixes a second form of F-1.**
  - The first version of the verifier ran one test file per session.
  - In the synthetic repository, the first rebuild rewrote a manifest that the second test then checked against, and so passed.
  - The verifier now runs one test per session, and the synthetic test proves the downstream pin refusal is seen.
- **The F-1 self-heal itself is reproduced and caught** (`test_f1_self_heal_happens_with_the_in_place_pattern_and_the_index_catches_it`):
  - with the historical in-place pattern, the first run fails and rewrites the manifest;
  - the second run passes;
  - the index check then names the rewritten manifest and README.
- **The guard runs last in a full session** (`tests/zz_freeze_integrity`). It fails if any indexed artefact differs, so an in-place rewrite by any earlier test now fails the session. The root `conftest.py` determinism guard covers `data/` and `tests/` only.
- **The index and both registers are append-only twice over:**
  - by their hash chain, which detects an edited, removed or reordered line;
  - by their git history, which detects truncation of the last lines, something a chain cannot see.

**Limit [INFERENCE].** The historical in-place rebuild tests still exist, and Stage 1 does not edit them. A failing one can still rewrite files in the working tree. Stage 1 makes that *detected* (the guard), *recoverable* (git) and *never the reference*: the verifier compares against git objects.

## 4. Verification results at 23cf674 (run V0, in the lock) [VERIFIED]

**Selection:**
- every test named `rebuild`, `rerun` or `byte_identical` (the historical freezes);
- plus `tests/m9_s6` (V1 / V2 behaviour, including the reference-plan V2 tests with the drawing provided);
- plus `tests/lintels_s8_6/test_opening_census.py`;
- plus the reference-plan V1 takeoff, compared with its 16 output hashes recorded at `6b7a2e4`.

**Run V0** (ref `74eed6c`, the first baseline run): 158 BYTE_IDENTICAL, 5 SKIPPED, overall **FAIL** because the repository moved during the run (a docs commit and a verifier edit). The check worked as designed; it also exposed finding F-11 (the ref was read by name, not resolved once), fixed in `23cf674`.

**Run V0R** (ref `23cf674`, a private clone of the repository so that development could continue meanwhile; the inputs are linked read-only):

| Run | Overall | Tests run | Verdicts | Repository unchanged | Environment lock | Patches | Repins |
|---|---|---|---|---|---|---|---|
| V0R | **PASS** | 162 | BYTE_IDENTICAL 158, SKIPPED 5 | True | matches | 0 | 0 |

### V0R: every test that is not BYTE_IDENTICAL (5)

| Test | Verdict | Rewritten files: raw / behaviour / masks | Builder error |
|---|---|---|---|
| `tests/structural_census/test_multi_engine_s3_1.py::test_rebuild_reproduces_committed_outputs` | SKIPPED | - | freelancer reference workbook is client data (not in git) |
| `tests/coverage_recovery_engine/test_coverage_round.py::test_rebuild_reproduces_frozen_outputs` | SKIPPED | - | local data/ inputs not present (gitignored) |
| `tests/r9_1_chris_post_freeze/test_r9_1_package.py::test_rebuild_byte_for_byte` | SKIPPED | - | frozen christiannp dataset not present |
| `tests/test_pa09_{R}_regression_r7.py::test_an_identical_rerun_changes_no_identity` | SKIPPED | - | run research.qs_wall_treatment_01.pa09.{R}.regression_r7 first |
| `tests/m9_s6/test_s6_tolerances.py::test_a_drafted_100_mm_face_piece_survives_in_a_metre_drawing` | SKIPPED | - | S6 Phase 1 open finding (S6P1-NEW-05): a lower length threshold equal to a drafted dimension (the 100 mm minimum face pi |


## 5. Mutation tests [VERIFIED]

They run in a disposable worktree only. The patches are in the private evidence.

| Run | Patch to `engine/source/opening_census.py` | Repin of its code pin (worktree only) | Selection |
|---|---|---|---|
| MT-1a | one appended comment line | yes | S8.6 and every freeze downstream of it, `tests/m9_s6`, the census unit tests, the reference-plan V1 |
| MT-1b | the same comment | no | S8.6 and downstream |
| MT-2 | **a behaviour change** (face-piece threshold × 1.5): the negative control | yes | as MT-1a |

| Run | Overall | Tests run | Verdicts | Repository unchanged | Environment lock | Patches | Repins |
|---|---|---|---|---|---|---|---|
| MT-1a | **FAIL** | 162 | BEHAVIOUR_CHANGED 2, BEHAVIOUR_IDENTICAL_PROVENANCE_DIFFERS 1, BUILD_FAILED 10, BYTE_IDENTICAL 145, SKIPPED 5 | True | matches | 1 | 1 |
| MT-1b | **FAIL** | 162 | BEHAVIOUR_IDENTICAL_PROVENANCE_DIFFERS 1, BYTE_IDENTICAL 144, REFUSED_BY_SOURCE_PIN 12, SKIPPED 5 | True | matches | 1 | 0 |
| MT-2 | **FAIL** | 162 | BEHAVIOUR_CHANGED 3, BEHAVIOUR_IDENTICAL_PROVENANCE_DIFFERS 1, BUILD_FAILED 10, BYTE_IDENTICAL 142, SKIPPED 5, TEST_FAILED_NO_OUTPUT_CHANGE 2 | True | matches | 1 | 1 |

### MT-1a: every test that is not BYTE_IDENTICAL (18)

| Test | Verdict | Rewritten files: raw / behaviour / masks | Builder error |
|---|---|---|---|
| `tests/structural_census/test_multi_engine_s3_1.py::test_rebuild_reproduces_committed_outputs` | SKIPPED | - | freelancer reference workbook is client data (not in git) |
| `tests/coverage_recovery_engine/test_coverage_round.py::test_rebuild_reproduces_frozen_outputs` | SKIPPED | - | local data/ inputs not present (gitignored) |
| `tests/lift_s8_8/test_s8_8_package.py::test_rebuild_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/lintels_s8_6/test_s8_6_package.py::test_rebuild_byte_identical` | BEHAVIOUR_IDENTICAL_PROVENANCE_DIFFERS | `00_README.md` DIFFERENT/EQUAL/M1_CODE_STAMP; `14_S8_6_SUMMARY.json` DIFFERENT/EQUAL/M1_CODE_STAMP; `15_S8_6_FREEZE_MANIFEST.json` DIFFERENT/EQUAL/M1_CODE_STAMP,M2_CODE_MAP,M4_MANIFEST_OUTPUT_HASHES | - |
| `tests/lintels_s8_6/test_s8_6_post_freeze.py::test_rerun_identical` | BEHAVIOUR_CHANGED | `03_POST_FREEZE_SUMMARY.json` DIFFERENT/DIFFERENT/- | - |
| `tests/lintels_s8_6a/test_s8_6a_package.py::test_rebuild_byte_identical` | BEHAVIOUR_CHANGED | `10_PREVIOUS_FREEZE_VERIFICATION.csv` DIFFERENT/DIFFERENT/-; `11_S8_6A_SUMMARY.json` DIFFERENT/DIFFERENT/M1_CODE_STAMP; `12_S8_6A_CORRECTION_MANIFEST.json` DIFFERENT/DIFFERENT/M1_CODE_STAMP,M2_CODE_MAP | - |
| `tests/m1_usable_boq/test_m1_package.py::test_rebuild_is_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/r9_1_chris_post_freeze/test_r9_1_package.py::test_rebuild_byte_for_byte` | SKIPPED | - | frozen christiannp dataset not present |
| `tests/stairs_s8_7/test_s8_7_package.py::test_rebuild_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/stairs_s8_7a/test_s8_7a_package.py::test_rebuild_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/stairs_s8_7b/test_s8_7b_package.py::test_rebuild_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/stairs_s8_7c/test_s8_7c_package.py::test_rebuild_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/structural_s9/test_s9_package.py::test_rebuild_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/structural_s9/test_s9_post_freeze.py::test_rerun_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/structural_s9a/test_s9a_package.py::test_rebuild_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/structural_s9a/test_s9a_post_freeze.py::test_hygiene_no_benchmark_figure_and_rerun_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/test_pa09_{R}_regression_r7.py::test_an_identical_rerun_changes_no_identity` | SKIPPED | - | run research.qs_wall_treatment_01.pa09.{R}.regression_r7 first |
| `tests/m9_s6/test_s6_tolerances.py::test_a_drafted_100_mm_face_piece_survives_in_a_metre_drawing` | SKIPPED | - | S6 Phase 1 open finding (S6P1-NEW-05): a lower length threshold equal to a drafted dimension (the 100 mm minimum face pi |

### MT-1b: every test that is not BYTE_IDENTICAL (18)

| Test | Verdict | Rewritten files: raw / behaviour / masks | Builder error |
|---|---|---|---|
| `tests/structural_census/test_multi_engine_s3_1.py::test_rebuild_reproduces_committed_outputs` | SKIPPED | - | freelancer reference workbook is client data (not in git) |
| `tests/coverage_recovery_engine/test_coverage_round.py::test_rebuild_reproduces_frozen_outputs` | SKIPPED | - | local data/ inputs not present (gitignored) |
| `tests/lift_s8_8/test_s8_8_package.py::test_rebuild_byte_identical` | REFUSED_BY_SOURCE_PIN | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: code engine/source/opening_census.py |
| `tests/lintels_s8_6/test_s8_6_package.py::test_rebuild_byte_identical` | BEHAVIOUR_IDENTICAL_PROVENANCE_DIFFERS | `00_README.md` DIFFERENT/EQUAL/M1_CODE_STAMP; `14_S8_6_SUMMARY.json` DIFFERENT/EQUAL/M1_CODE_STAMP; `15_S8_6_FREEZE_MANIFEST.json` DIFFERENT/EQUAL/M1_CODE_STAMP,M2_CODE_MAP,M4_MANIFEST_OUTPUT_HASHES | - |
| `tests/lintels_s8_6/test_s8_6_post_freeze.py::test_rerun_identical` | REFUSED_BY_SOURCE_PIN | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: code engine/source/opening_census.py |
| `tests/lintels_s8_6a/test_s8_6a_package.py::test_rebuild_byte_identical` | REFUSED_BY_SOURCE_PIN | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: code engine/source/opening_census.py |
| `tests/m1_usable_boq/test_m1_package.py::test_rebuild_is_byte_identical` | REFUSED_BY_SOURCE_PIN | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: code engine/source/opening_census.py |
| `tests/r9_1_chris_post_freeze/test_r9_1_package.py::test_rebuild_byte_for_byte` | SKIPPED | - | frozen christiannp dataset not present |
| `tests/stairs_s8_7/test_s8_7_package.py::test_rebuild_byte_identical` | REFUSED_BY_SOURCE_PIN | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: code engine/source/opening_census.py |
| `tests/stairs_s8_7a/test_s8_7a_package.py::test_rebuild_byte_identical` | REFUSED_BY_SOURCE_PIN | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: code engine/source/opening_census.py |
| `tests/stairs_s8_7b/test_s8_7b_package.py::test_rebuild_byte_identical` | REFUSED_BY_SOURCE_PIN | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: code engine/source/opening_census.py |
| `tests/stairs_s8_7c/test_s8_7c_package.py::test_rebuild_byte_identical` | REFUSED_BY_SOURCE_PIN | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: code engine/source/opening_census.py |
| `tests/structural_s9/test_s9_package.py::test_rebuild_byte_identical` | REFUSED_BY_SOURCE_PIN | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: code engine/source/opening_census.py |
| `tests/structural_s9/test_s9_post_freeze.py::test_rerun_identical` | REFUSED_BY_SOURCE_PIN | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: code engine/source/opening_census.py |
| `tests/structural_s9a/test_s9a_package.py::test_rebuild_byte_identical` | REFUSED_BY_SOURCE_PIN | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: code engine/source/opening_census.py |
| `tests/structural_s9a/test_s9a_post_freeze.py::test_hygiene_no_benchmark_figure_and_rerun_identical` | REFUSED_BY_SOURCE_PIN | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: code engine/source/opening_census.py |
| `tests/test_pa09_{R}_regression_r7.py::test_an_identical_rerun_changes_no_identity` | SKIPPED | - | run research.qs_wall_treatment_01.pa09.{R}.regression_r7 first |
| `tests/m9_s6/test_s6_tolerances.py::test_a_drafted_100_mm_face_piece_survives_in_a_metre_drawing` | SKIPPED | - | S6 Phase 1 open finding (S6P1-NEW-05): a lower length threshold equal to a drafted dimension (the 100 mm minimum face pi |

### MT-2: every test that is not BYTE_IDENTICAL (21)

| Test | Verdict | Rewritten files: raw / behaviour / masks | Builder error |
|---|---|---|---|
| `tests/structural_census/test_multi_engine_s3_1.py::test_rebuild_reproduces_committed_outputs` | SKIPPED | - | freelancer reference workbook is client data (not in git) |
| `tests/coverage_recovery_engine/test_coverage_round.py::test_rebuild_reproduces_frozen_outputs` | SKIPPED | - | local data/ inputs not present (gitignored) |
| `tests/lift_s8_8/test_s8_8_package.py::test_rebuild_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/lintels_s8_6/test_s8_6_package.py::test_rebuild_byte_identical` | BEHAVIOUR_IDENTICAL_PROVENANCE_DIFFERS | `00_README.md` DIFFERENT/EQUAL/M1_CODE_STAMP; `14_S8_6_SUMMARY.json` DIFFERENT/EQUAL/M1_CODE_STAMP; `15_S8_6_FREEZE_MANIFEST.json` DIFFERENT/EQUAL/M1_CODE_STAMP,M2_CODE_MAP,M4_MANIFEST_OUTPUT_HASHES | - |
| `tests/lintels_s8_6/test_s8_6_post_freeze.py::test_rerun_identical` | BEHAVIOUR_CHANGED | `03_POST_FREEZE_SUMMARY.json` DIFFERENT/DIFFERENT/- | - |
| `tests/lintels_s8_6a/test_s8_6a_package.py::test_rebuild_byte_identical` | BEHAVIOUR_CHANGED | `10_PREVIOUS_FREEZE_VERIFICATION.csv` DIFFERENT/DIFFERENT/-; `11_S8_6A_SUMMARY.json` DIFFERENT/DIFFERENT/M1_CODE_STAMP; `12_S8_6A_CORRECTION_MANIFEST.json` DIFFERENT/DIFFERENT/M1_CODE_STAMP,M2_CODE_MAP | - |
| `tests/m1_usable_boq/test_m1_package.py::test_rebuild_is_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/m6_completeness/test_cc_package.py::test_both_runs_rebuild_byte_for_byte_from_the_frozen_engines` | TEST_FAILED_NO_OUTPUT_CHANGE | - | - |
| `tests/m7_reliability/test_m7_package.py::test_live_rebuild_of_the_st7757_records` | TEST_FAILED_NO_OUTPUT_CHANGE | - | - |
| `tests/r9_1_chris_post_freeze/test_r9_1_package.py::test_rebuild_byte_for_byte` | SKIPPED | - | frozen christiannp dataset not present |
| `tests/stairs_s8_7/test_s8_7_package.py::test_rebuild_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/stairs_s8_7a/test_s8_7a_package.py::test_rebuild_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/stairs_s8_7b/test_s8_7b_package.py::test_rebuild_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/stairs_s8_7c/test_s8_7c_package.py::test_rebuild_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/structural_s9/test_s9_package.py::test_rebuild_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/structural_s9/test_s9_post_freeze.py::test_rerun_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/structural_s9a/test_s9a_package.py::test_rebuild_byte_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/structural_s9a/test_s9a_post_freeze.py::test_hygiene_no_benchmark_figure_and_rerun_identical` | BUILD_FAILED | - | engine.source.delta_release.DeltaReleaseError: frozen baseline altered: inputs research/lintels_s8_6/15_S8_6_FREEZE_MANI |
| `tests/test_pa09_{R}_regression_r7.py::test_an_identical_rerun_changes_no_identity` | SKIPPED | - | run research.qs_wall_treatment_01.pa09.{R}.regression_r7 first |
| `tests/m9_s6/test_s6_tolerances.py::test_a_drafted_100_mm_face_piece_survives_in_a_metre_drawing` | SKIPPED | - | S6 Phase 1 open finding (S6P1-NEW-05): a lower length threshold equal to a drafted dimension (the 100 mm minimum face pi |
| `ARCH_BASELINE::reference_plan_V1` | BEHAVIOUR_CHANGED | `ARCH_FLOOR_AREAS.json` DIFFERENT/DIFFERENT/-; `ARCH_OPENINGS.json` DIFFERENT/DIFFERENT/-; `ARCH_PLAN.json` DIFFERENT/DIFFERENT/-; `ARCH_ROOMS.json` DIFFERENT/DIFFERENT/-; `ARCH_WALLS.json` DIFFERENT/DIFFERENT/-; `BOQ_LINES.csv` DIFFERENT/DIFFERENT/-; `BOQ_LINES.json` DIFFERENT/DIFFERENT/-; `COVERAGE.csv` DIFFERENT/DIFFERENT/-; `COVERAGE.json` DIFFERENT/DIFFERENT/-; `MATERIAL_RESULTS.json` DIFFERENT/DIFFERENT/-; `OVERLAY_1F.svg` DIFFERENT/DIFFERENT/-; `OVERLAY_2F.svg` DIFFERENT/DIFFERENT/-; `OVERLAY_GF.svg` DIFFERENT/DIFFERENT/-; `RUN_RULES.json` DIFFERENT/DIFFERENT/-; `UNRESOLVED.json` DIFFERENT/DIFFERENT/-; `URBAN_ROOM_BOQ.xlsx` DIFFERENT/DIFFERENT/- | - |

**Reading of the mutation runs [VERIFIED]:**
- **MT-1b (comment only, no repin): every downstream rebuild is refused by its own pin check** (12 REFUSED_BY_SOURCE_PIN); S8.6
  itself differs in its code stamps only (BEHAVIOUR_IDENTICAL_PROVENANCE_DIFFERS). The pins do their job.
- **MT-1a (comment only, S8.6 code pin re-pinned in the worktree): a single re-pin does not absorb even a comment.** The S8.6
  manifest's own bytes change with its code map, and 10 downstream builders pin those bytes (BUILD_FAILED: "frozen baseline
  altered"); 2 outputs copy the upstream manifest hash into fields the masks do not cover (BEHAVIOUR_CHANGED). Every other
  freeze, the V1 / V2 tests and the reference-plan V1 hashes stay BYTE_IDENTICAL. Finding F-10.
- **MT-2 (a real behaviour change, the face-piece threshold x 1.5): detected** - the reference-plan V1 takeoff changes, the
  M6 / M7 route-G live rebuilds fail, the S8.6 downstream builds are refused. The negative control fails, as it must.
- Together: no change to `opening_census.py` can land without a freeze-graph migration; the recommended Stage 2 diff to pinned
  files stays **0 lines**.


## 6. Proposed Stage 2 diff (NOT applied): see `PROPOSED_STAGE2.md`

**Recommended Stage 2 diff to pinned files: none (0 lines).**
- **Why none is needed:** each of the three thresholds is used in one strict comparison. Passing `T - m` through the existing parameters is exactly the robust predicate: 648 / 648 synthetic checks agree.
- **What that leaves untouched:** every pin, every frozen manifest, every historical test.
- **The alternative, if the owner prefers explicit predicates:** `PROPOSED_STAGE2_ALTERNATIVE.diff` (17 lines; keyword-only, default `None` = the frozen expression). Its dry run is S2-DRY below.

**S2-DRY was not run in this sprint.** The alternative diff remains a proposal; MT-1a already shows that any byte change to the pinned file cascades (F-10), which is the reason the recommendation is the 0-line route. ARCH_TAKEOFF_V2.1 (Phase 2A, separate report) uses that route: the frozen functions are called with T - m from the unpinned module `engine/source/robust_geometry.py`.

## 7. Other Stage 1 findings

**F-5 [VERIFIED]. Source pins do not cover the import closure.** This is the strongest reason to treat behaviour, not source digests, as the authority.

- freezes with pinned .py files: 33 (of which 4 are M6-M8 engine-freeze records)
- with at least one unpinned repository module on the computation path: 30 of 33
- most frequent unpinned modules on S-stage computation paths: `engine/source/graphic_evidence.py` (21), `engine/source/arch_quantity_truth.py` (17), `engine/source/planar_shadow_topology.py` (16), `engine/source/structural_census.py` (14), `engine/source/bbs_optimiser.py` (3), `engine/source/rebar_sanity_qa.py` (3)
- Phase 2A candidate files found UNPINNED on a freeze's computation path: `engine/source/opening_census.py` in ['urban_engine_m6_completeness', 'urban_engine_m6_completeness', 'urban_engine_m7_reliability', 'urban_engine_m8_full_scope'], `engine/source/topology.py` in ['urban_engine_m6_completeness', 'urban_engine_m6_completeness'], `engine/source/opening_gaps.py` in ['urban_engine_m6_completeness', 'urban_engine_m6_completeness', 'urban_engine_m7_reliability', 'urban_engine_m8_full_scope'], `engine/source/lintel_measure.py` in ['urban_engine_m6_completeness', 'urban_engine_m6_completeness', 'urban_engine_m7_reliability', 'urban_engine_m8_full_scope'], `tools/urban_intake.py` in ['urban_engine_m6_completeness', 'urban_engine_m6_completeness']

| Freeze (stage folder) | Pinned .py | Functional closure .py | Unpinned on the computation path |
|---|---|---|---|
| ad1_authority_decisions | 4 | 5 | 1 |
| dome_mesh_s8_3a | 6 | 10 | 4 |
| dome_ring_s8_3 | 6 | 9 | 3 |
| footing_rebar_s4 | 9 | 14 | 5 |
| footing_rebar_s4_1 | 3 | 3 | 0 |
| ground_slab_s8_1 | 6 | 11 | 5 |
| ground_slab_s8_1a | 6 | 10 | 4 |
| ground_system_rebar_s5 | 7 | 9 | 2 |
| ground_system_rebar_s5_1 | 4 | 4 | 0 |
| lift_s8_8 | 5 | 9 | 4 |
| lintels_s8_6 | 6 | 10 | 4 |
| m1_usable_boq | 11 | 32 | 21 |
| slab_rebar_pre_s7 | 9 | 10 | 1 |
| slab_rebar_pre_s7_1 | 6 | 10 | 4 |
| slab_rebar_s7 | 9 | 13 | 4 |
| slab_rebar_s7a_qa | 4 | 5 | 1 |
| special_columns_s8_5 | 5 | 9 | 4 |
| stairs_s8_7 | 5 | 9 | 4 |
| stairs_s8_7b | 7 | 11 | 4 |
| stairs_s8_7c | 7 | 11 | 4 |
| structural_s9 | 4 | 5 | 1 |
| superstructure_beam_rebar_s6 | 6 | 8 | 2 |
| superstructure_beam_rebar_s6_1 | 4 | 4 | 0 |
| swimming_pool_s8_2 | 9 | 13 | 4 |
| swimming_pool_s8_2a | 11 | 15 | 4 |
| water_tank_s8_4 | 7 | 11 | 4 |
| d1_1_stirrup_authority_audit | 6 | 7 | 1 |
| d1_2_footing_cover_audit | 5 | 6 | 1 |
| pre_s8_structural_completeness | 4 | 8 | 4 |
| urban_engine_m6_completeness | 5 | 72 | 67 |
| urban_engine_m6_completeness | 6 | 74 | 68 |
| urban_engine_m7_reliability | 21 | 79 | 58 |
| urban_engine_m8_full_scope | 27 | 81 | 54 |


**Phase 2A modules on route-G (M6–M8) computation paths [INFERENCE + VERIFIED closure].** `opening_census`, `opening_gaps` and `lintel_measure` are reached by the M6–M8 engine freezes without being pinned there.
- Any V2.1 change in those modules must be an opt-in branch, with the default path unchanged.
- The M7 / M8 rebuild tests (`test_live_rebuild_of_the_st7757_records`, `test_the_csv_deliverables_rebuild_from_the_records`) are in the verifier selection.

**One more strict threshold, outside Phase 2A.** `opening_census.arc_gaps` (`if g < min_gap_mm`, curved walls) also compares strictly. It is listed for the threshold census.

## 8. Registers

| Register | Entries |
|---|---|
| `ERRATA.jsonl` | E-001 … E-005: S6R-A1, S6R-A2, S6R-B1, the angle-bin projection, the M4 lap-count `ceil` |
| `ENGINEERING_FINDINGS.jsonl` | F-1 … F-8: self-healing rebuilds, code stamps, angle bin, no pin, unpinned closure, 3.13, DIMLFAC header, reveal / head NO_EMITTER |

## 9. Owner decisions and requirements recorded

- **D1:** Stage 1 is done (add-only).
- **D2:** Stage 2 is not started; it is proposed for review.
- **D3:** `ELIGIBILITY_V0` stays PROPOSAL; it is diagnostics only.
- **D4:** provisional doors are shown separately, excluded from released totals.
- **D5:** the lock.
- **Requirements 1–6:** written as acceptance tests in `PHASE2A_ACCEPTANCE_ADDENDUM.csv`.
  - Requirement 2: three separate widths (structural opening, frame, nominal leaf).
  - Requirement 3: four ledger classes (NO_EMITTER / UNRESOLVED_ELIGIBILITY / MISSING_SOURCE / CONFIRMED_MISSING). No reveal / head record is CONFIRMED_MISSING while reveal measurement is undecided.
  - Requirement 4: no inference of heights, waterproofing or kitchen class from missing drawings.
  - Requirement 1 and the owner-rule part of requirement 4 are already enforced by Stage 1 (the index guard).

## 10. Full suite

**Full suite at `1a68eb7`** (CPython 3.11.17 in the lock; the reference-plan drawing provided through `URBAN_REAL_PLAN_DXF`; `-o addopts=`; 12 min 12 s) **[VERIFIED]**:

| Collected | Passed | Failed | Errors | Skipped | xfailed |
|---|---|---|---|---|---|
| 8,556 | **7,930** | 344 | 32 | 148 | 102 |

**Every one of the 376 failures and errors is a missing-private-data failure, and none is a regression [VERIFIED]:**
- **374** are `FileNotFoundError` on a gitignored `data/experiments/...` dataset (the PA-08 / PA-09 historical studies, absent in this container).
- **1** is a missing `data/experiments` output ("run workbook_boq first").
- **1** is a client upload from an earlier session, not present here.
- **The same 376 tests were rerun at the pre-sprint commit `a1493b1`:** 344 failed and 32 errors, identically.
- **0 code failures.**
- The total of 376 equals the M9 S1 test gate's `MANDATORY_BLOCKED_BY_MISSING_DATA` count.

**After the suite:** `2a34281` (lift doors are never measured) changes only `door_model.finalise` (V2.1 only) and adds one test. The affected suites (`tests/m9_p2a`, `tests/m9_s2_arch`, `tests/m9_s6`, `tests/zz_freeze_integrity`) pass at `2a34281`. The final verifier ran at `2a34281` (section 7).

## 11. Reproduce

```
python3 -I tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl
python3 -I tools/freeze_verify.py env --lock research/freeze_integrity/ENVIRONMENT_LOCK.json
python3 -I tools/freeze_verify.py closure
URBAN_REAL_PLAN_DXF=<drawing> python3 -I tools/freeze_verify.py rebuild --out <dir> \
    --lock research/freeze_integrity/ENVIRONMENT_LOCK.json [--arch-baseline <private config>]
python3 -I tools/freeze_verify.py rebuild --out <dir> --lock ... --patch <diff> --repin --only '<regex>'
python3 -I research/freeze_integrity/stage2_threshold_shift_check.py
```

**Stop point: Stage 2 is not started.** The next step needs the owner's review of section 6.
