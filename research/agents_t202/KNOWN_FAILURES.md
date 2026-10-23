# Known failures on the working head (T-202 ledger)

**Rule for workers and the Checker: compare test by test with this list.** Save the -q output of your run and check it:

    bash scripts/agent_env.sh pytest --tree task-<ID> tests/<folders> > RUN.txt 2>&1
    python3 -I research/agents_t202/known_failures.py check RUN.txt

`NEW` ids (exit 1) are your run's own failures (gate b). A `KNOWN` id is still a failure, never a pass: write "green except
the ledger (n known)". The machine-readable ledger is `known_failures.json` (one entry per test id: kind, cause code,
cause, evidence line, first failing commit and its basis, owner); rebuild it only from a full-suite run with
`build_ledger.py RUN.txt <head sha>`, which refuses any failure no listed cause explains.

## 1. Head and run

- Head: `d699b650` (Merge T-200, 2026-10-23 07:00 UTC), full suite `bash scripts/agent_env.sh pytest --tree task-T-202
  tests/` (Python 3.11.17 venv, pinned requirements), 07:03 - 07:22 UTC.
- Outcomes (progress characters): 10,958 passed, 364 failed, 32 errors, 214 skipped, 105 xfailed (11,673).
- The 396 failing ids fall under 5 causes: PRIVATE_INPUT_ABSENT 390, DEPENDENCY_NOT_REGISTERED 2, K1_IMPORTS_EZDXF 2,
  K1_NOT_STDLIB 1, WORKTREE_GITDIR 1. **No failure is caused by a merge of the 2026-10-22 00:00 .. 2026-10-23 07:00
  window**: the 6 non-private failures fail identically at the window base `15fd9132` (run of tests/christiannp_blind_process,
  r8_0, r8_1, r8_2 on a detached worktree of 15fd9132: same 6 FAILED), and the private-input ones fail since their test
  was added.
- The session ended with the conftest DETERMINISM GUARD message for `tests/t202_guard_sweep/*` only: this task's test
  files were created in the tree while the run was in progress (not a test writing into tests/). No test failed for it.
- Earlier board text named "three known failures" (r8_0 B5 / B6 pymupdf, s7 / s9a rebuild): those are 3 of these 396.

## 2. How first_failing was established

- Bisect causes (first-parent bisection of the working branch with the wrapper on a detached worktree, each probe a run
  of the test file; last good / first failing):
  - DEPENDENCY_NOT_REGISTERED (r8_0 and r8_1 B5 / B6): good 88842872, failing **2dee9544** (Merge T-082, opening heights
    from vector PDF, 2026-10-19 21:58 UTC: engine/source/opening_height_pdf.py imports pymupdf).
  - K1_NOT_STDLIB (r8_1 k1 stdlib): good 15de9c45, failing **362630a1** (Merge T-061, room_label_guard.py imports shapely,
    2026-10-19 12:00 UTC).
  - K1_IMPORTS_EZDXF (r8_1 kernel_ocs, r8_2 k2): good c564481e, failing **5f07bf00** (Merge T-078, opening_area.py imports
    ezdxf, 2026-10-19 17:59 UTC).
  - WORKTREE_GITDIR (christiannp rebuild): good a5eeebe2, failing **504b56a7** (PR #2 navigation maps, 2026-10-17); cause
    found by a direct diff of the rebuilt package: only `ENGINE_COMMIT` differs (recorded short sha vs `UNCOMMITTED`),
    because tests/rebuild_sandbox.py:74 writes `gitdir: <root>/.git` and in a git worktree `.git` is a file.
- PRIVATE_INPUT_ABSENT: first first-parent commit that contains the test file (the input was never committed: `git log`
  over data/inputs, data/experiments and data/runs is empty on every fetched ref). Missing inputs, by group:
  `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/...` (pa08 Qortuba, pa09 Alrashed / villa blind),
  `data/inputs/by_sha256/9f9d1179...dxf` (the structural DXF by hash: control plane G08, S9A, and the byte-identical
  rebuilds of D1.1, D1.2, S6.1, S7, PRE-S7, PRE-S7.1, S7A, PRE-S8, S8.1, S8.1A, source-recovery delta: each builder's
  captured stderr names this file; S9A by build_s9a.py:53), `data/runs/7757/reconciliation/...` (benchmark protection),
  and one session-upload path under /root/.claude/uploads (pa08 boq schema, originals check).

## 3. Ledger by test file

| Cause | Test file | Test(s) | First failing | Owner |
|---|---|---|---|---|
| PRIVATE_INPUT_ABSENT | `tests/alsenan_control_plane/test_control_plane_r2_gates.py` | test_G08_every_structural_source_object_has_a_terminal_state | 7c5b162b | pre-existing (owner data); no task |
| WORKTREE_GITDIR | `tests/christiannp_blind_process/test_package.py` | test_builder_reproduces_outputs_byte_for_byte | 504b56a7 | pre-existing; fix proposed for a Lead row (tests/rebuild_sandbox.py) |
| PRIVATE_INPUT_ABSENT | `tests/d1_1_stirrup_authority_audit/test_d1_1_package.py` | test_rebuild_is_byte_identical | 35567e26 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/d1_2_footing_cover_audit/test_d1_2_package.py` | test_rebuild_is_byte_identical | d0d2ad93 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/ground_slab_s8_1/test_s8_1_package.py` | test_rebuild_is_byte_identical | 201f4415 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/ground_slab_s8_1a/test_s8_1a_package.py` | test_rebuild_is_byte_identical | 042e427b | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/pre_s8_census/test_pre_s8.py` | test_rebuild_is_byte_identical | 7e1ebe84 | pre-existing (owner data); no task |
| DEPENDENCY_NOT_REGISTERED | `tests/r8_0/test_r8_0_import_boundaries.py` | test_B5_B6_engine_source_dependencies_registered | 2dee9544 | pre-existing since T-082 (merge 2dee9544); fix = register the dependency or move the reader (own task) |
| DEPENDENCY_NOT_REGISTERED | `tests/r8_1/test_r8_1_boundaries.py` | test_B5_B6_live_engine_source_dependencies_registered | 2dee9544 | pre-existing since T-082 (merge 2dee9544); fix = register the dependency or move the reader (own task) |
| K1_NOT_STDLIB | `tests/r8_1/test_r8_1_boundaries.py` | test_k1_is_stdlib_only_in_r8_1 | 362630a1 | pre-existing since T-061 (merge 362630a1, room_label_guard.py shapely); the K1 boundary needs an owner / Lead decision (extend by_design or move modules): own task |
| K1_IMPORTS_EZDXF | `tests/r8_1/test_r8_1_kernel_ocs.py` | test_k1_is_independent_of_ezdxf | 5f07bf00 | pre-existing since T-078 (merge 5f07bf00, opening_area.py); in the T-202 window arch_v302.py (T-142) adds one more; own task |
| K1_IMPORTS_EZDXF | `tests/r8_2/test_r8_2_k2.py` | test_k1_does_not_import_ezdxf | 5f07bf00 | pre-existing since T-078 (merge 5f07bf00, opening_area.py); in the T-202 window arch_v302.py (T-142) adds one more; own task |
| PRIVATE_INPUT_ABSENT | `tests/s7a_qa/test_s7a_qa.py` | test_rebuild_is_byte_identical | 7e1ebe84 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/slab_rebar_pre_s7/test_pre_s7_package.py` | test_rebuild_is_byte_identical | 7e0c03b7 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/slab_rebar_pre_s7_1/test_pre_s7_1_package.py` | test_rebuild_is_byte_identical | 787890c6 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/slab_rebar_s7/test_s7_package.py` | test_rebuild_is_byte_identical | 16741ecc | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/source_recovery_delta/test_source_recovery_delta.py` | test_rebuild_is_byte_identical | 5184c638 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/structural_s9a/test_s9a_package.py` | 2 tests | e97fa4b9 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/superstructure_beam_rebar_s6_1/test_alsenan_s6_1_package.py` | test_rebuild_is_byte_identical | 23a8dbff | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_benchmark_protection.py` | test_the_p7757_reconciliation_document_obeys_the_protocol | 2558e06b | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa08_qortuba_boq_rules.py` | 23 tests | 3e11d974 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa08_qortuba_boq_schema.py` | 14 tests | 91d6e918 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa08_qortuba_ext01.py` | 13 tests | 63107978 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa08_qortuba_final_takeoff.py` | 10 tests | 7aebc0ac | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa08_qortuba_open_passage.py` | 9 tests | e288f9b0 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa08_qortuba_opening_completion.py` | 19 tests | 4ee18715 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa08_qortuba_owner_inputs_v2.py` | 20 tests | e8da9b2e | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa08_qortuba_owner_rule_audit.py` | 26 tests | 9a810ce9 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa08_qortuba_owner_rules.py` | 33 tests | d72645a4 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa08_qortuba_pricing.py` | 15 tests | 65944bad | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa08_qortuba_pricing_audit.py` | 15 tests | db542ce8 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa08_qortuba_qs01.py` | 21 tests | 1de7f7ea | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa08_qortuba_question_crops.py` | 11 tests | cc0b92a6 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa08_qortuba_workflow_v1.py` | 20 tests | 7a0fa385 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa09_alrashed.py` | 20 tests | a91358cb | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa09_alrashed_amendment.py` | 3 tests | 8f4a7056 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa09_alrashed_detailed.py` | 32 tests | 8f4a7056 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa09_alrashed_final.py` | 14 tests | 3e847af6 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa09_alrashed_historical.py` | 14 tests | 58b77ad3 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa09_alrashed_quantities.py` | 12 tests | 95f78ca9 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa09_alrashed_unseal.py` | 6 tests | 4c713e63 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa09_villa_attribution.py` | 8 tests | fd0cd07c | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa09_villa_blind_inventory.py` | 6 tests | 36cd48a9 | pre-existing (owner data); no task |
| PRIVATE_INPUT_ABSENT | `tests/test_pa09_villa_blind_protocol.py` | 11 tests | f8b1cdba | pre-existing (owner data); no task |

## 4. Follow-ups proposed to the Lead (not done here; each is its own task)

1. tests/rebuild_sandbox.py: resolve the `gitdir:` line when `root/.git` is a file (fixes WORKTREE_GITDIR; test
   infrastructure, no quantity).
2. K1 boundary: decide per module (extend the tests' `by_design` with reasons, or move the import); see SWEEP.md s.3 for
   the full list of 24 modules. Until then the three r8 tests stay red and hide new offenders.
3. pymupdf: register it in the dependency register or isolate opening_height_pdf.py (B-5 / B-6).
4. Private-input tests: run only where the owner's data exists; a marker or a fixture-level skip with a printed reason
   would make them visible as "not run here" instead of 390 failures. Owner / Lead decision (tests are never weakened
   without one).
