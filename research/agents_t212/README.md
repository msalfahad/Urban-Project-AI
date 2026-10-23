# T-212: guard test made reproducible, guard property checked live

**Defect.** `tests/t202_guard_sweep::test_guard_host_and_unwired_producers` was red on the working branch from merge
01eeafd0 (T-108 r2): it asserts `importers == []` for `opening_scope_v1.py`, and the sweep computed importers on the
LIVE tree, where the new unwired producer `masonry_area_v1.py` imports `opening_scope_v1` (the board row named
`masonry_centreline_v2`; the actual edge is `masonry_area_v1 -> opening_scope_v1`, line 42 of masonry_area_v1.py).
No candidate or released method reached either module: no quantity effect.

**Safety property the guard protects.** No released or candidate method reaches a producer the default guard
(T-186) has not been wired into, and every new engine module carries a default-guard class.

**Fix (no test edited or weakened).**

1. `research/agents_t202/guard_sweep.py`: `import_index` / `importers` take `rev`; `sweep()` scans importers on the
   tree AT its pinned HEAD d699b650 (`git ls-tree` + one `git cat-file --batch`). The 22-row table it prints is
   identical, row for row, to the committed `research/agents_t202/SWEEP.md`; `tests/t202_guard_sweep` passes unedited.
2. `research/agents_t212/guard_property.py check` (live tree): P1 every engine/ or tools/ .py added or modified after
   d699b650 is classified (T-202 `GUARD`, the `LATER` table here, or `DEFAULT_GUARD_CLASS = "<class>"` in the module
   itself, so a future module classifies itself without editing this folder); P2 the transitive importer closure of
   every UNWIRED_PRODUCER holds only unwired producers (research/ and tests/ are outside the scan); P3 no run-time load
   (importlib / `__import__`) names a producer. Relative imports and bare-stem imports are resolved (the T-202 index
   skips relative imports).

**Result on the live tree (working head d5df7d1f):** 2 modules after d699b650, both classified
(`masonry_area_v1` UNWIRED_PRODUCER, `element_continuity_v1` CHECK_ONLY); closures: `opening_scope_v1` ->
[`masonry_area_v1`] (allowed: producer importing producer), `masonry_centreline_v2`, `stair_rule_calculator`,
`masonry_area_v1` -> none. Problems 0.

**Limits.** Imports built from computed strings are not followed (P3 matches literal names); the classification of a
module is a judgement the Checker re-derives from its docstring and importers.
