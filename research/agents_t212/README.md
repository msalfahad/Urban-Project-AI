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

## r2 (Checker 12:55 rejection: gate b on the merged head)

**Miss.** r1 validated on d5df7d1f; V3.0.7 (T-193, merge e866328a) came in afterwards and P1 correctly refused the new,
unclassified candidate module `engine/source/arch_v307.py` on the merged head.

**Class, from the module.** `arch_v307.py` = **GUARD_HOST**: docstring step 4 "GUARD RE-CHECK"; `changes_for()`
(line 577) always ends in `guard_changes()`, which runs `DG.guard(...)` (line 487) over the V3.0.6 lines with this
version's replacements plus the lines it adds; a finding on an added or a replaced line refuses the run. Same limit as
arch_v306: with no project guard input the guard is not run and only the run log says so (`NO_PROJECT_INPUT`, line
480). Imports arch_v30 / v302 / v304 / v305 / v306 and default_guard only (lines 60-65): no producer.

**P4 (new, same property).** A GUARD_HOST class is a claim that the module can run the guard: every GUARD_HOST module
other than `default_guard.py` must reach `default_guard.py` through its own transitive static imports, else a problem.
Live: arch_v306, arch_v307, tools/urban_boq_m9.py all reach it.

**For the next candidate version (T-199 V3.0.8 and later, lane I):** put `DEFAULT_GUARD_CLASS = "GUARD_HOST"` in the
new arch_v3xx module itself, so P1 classifies it without editing this folder and P4 holds it to the claim; run
tests/t212_guard_property on the package head merged with the working branch before READY.
