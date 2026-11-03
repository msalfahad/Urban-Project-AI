# T-492: stale-pending guard scoped to the working-branch merge

Source: Checker finding F-C-T443-1 (T-443 r2 verdict), Lead ruling: a package is merged only when its task commit
reached the working branch, never because it is on its own task head.

## Defect (reproduced)
`tests/t485_registry_promotion::test_a_merged_package_never_stays_pending_in_the_newest_registry` used
`_merged(c) = c is an ancestor of HEAD`. On agents/task-T-443 @ c165a8f3 (detached copy, venv Python 3.11):
`AssertionError: assert ['T-443'] == []` (1 failed). Every READY package fails it by construction.

## Change
- `research/agents_t492/working_branch_merge.py` (new): `make_merged(root)` -> predicate. Merged when the commit is an
  ancestor of W = origin/claude/access-permissions-setup-ii24ws (else the local branch of that name), or when HEAD is
  that branch checked out ahead of W and the commit is a first-parent commit of W..HEAD. A commit brought in only by an
  unpublished merge (trial merge, a task branch integrating another task branch) is not merged. No W ref:
  `WorkingBranchUnavailable` (never a silent "not merged"). Ancestry via `FMC.git_is_ancestor` (T-463 shallow rules).
- `tests/t485_registry_promotion/test_t485_promotion.py`: `_merged` helper only now calls the predicate.
  `build_master_1_43_0.stale_pending` unchanged (the predicate is a test-side input; it did not belong there).
- `tests/t485_registry_promotion/test_t492_working_branch_merge.py` (new): temp-repo histories (no villa data):
  (a) own task branch passes, also after merging W into it (the T-443 shape); (b) merged into W and pending fails;
  (c) committed on W's first-parent chain fails, and on the checked-out local W ahead of origin; trial merge (detached
  and on the branch) does not name the package; a package integrated by another task branch stays pending; no W ref is
  refused; local W used without origin; unknown commit not merged.

## Not weakened
1.42.0 still returns 39 stale on this head (`test_1_42_0_pending_are_stale_on_this_head`). The old HEAD predicate's
false positive is asserted in test (a) as the contrast.

## Results
See the board handoff (task head and the T-443 trial merge, test by test).
