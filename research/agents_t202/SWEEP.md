# T-202 guard sweep: modules merged 2026-10-22 00:00 .. 2026-10-23 07:00 UTC vs the rebar firewall and the default guard

Working head swept: `d699b650` (Merge T-200). Generated part (section 1) by `python3 -I research/agents_t202/guard_sweep.py
table` (exit 0: 22 modules, 0 problems); re-derived independently in `tests/t202_guard_sweep` from one aggregate
`git diff --name-only 15fd9132 d699b650 -- engine/ tools/`. Window = first-parent history of the working branch after
`15fd9132` (Merge T-155, 2026-10-21 23:53 UTC, the last merge before 2026-10-22 00:00): 48 merges, no direct commit
touches engine/ or tools/. Registry class is read from `tests/structural_comparison_engine/rebar_product_registry.py`;
"names rebar" uses the firewall test's own words (rebar, bbs, reinforc) exactly as
`test_every_rebar_module_in_engine_is_declared` does.

Tests run on the head (task tree = d699b650 + this task's research / test files only):
`tests/structural_comparison_engine/test_rebar_product_firewall.py` + `tests/t186_default_guard`: all pass (62).

## 1. Sweep table

Window: first-parent `15fd9132..d699b650` (engine/ and tools/ .py files; A = added, M = modified).

| # | Module | Merges (task status sha) | Names rebar | Registry class | Importers (engine/ tools/) | Default guard | Why |
|---|---|---|---|---|---|---|---|
| 1 | `engine/source/arch_v302.py` | T-142 A 5de8657e | yes | OTHER_REBAR_AWARE | arch_v303, arch_v304, arch_v305, arch_v306, urban_boq_m9 | GUARDED_VIA_V3.0.6 | V3.0.2 lines (footing steel population) inherited by V3.0.6 |
| 2 | `engine/source/arch_v303.py` | T-151 A 47df1930 | yes | OTHER_REBAR_AWARE | arch_v304, urban_boq_m9 | GUARDED_VIA_V3.0.6 | V3.0.3 ledger steel lines inherited by V3.0.6 |
| 3 | `engine/source/arch_v304.py` | T-167 A cf5819c6 | no | not declared; names no rebar word: not required | arch_v305, arch_v306, urban_boq_m9 | GUARDED_VIA_V3.0.6 | V3.0.4 no-assumptions audit labels inherited by V3.0.6 |
| 4 | `engine/source/arch_v305.py` | T-179 A 90d0b769 | yes | OTHER_REBAR_AWARE | arch_v306, urban_boq_m9 | GUARDED_VIA_V3.0.6 | V3.0.5 ledger lines (slab / stair / pool / tank steel, dome ring) inherited by V3.0.6 |
| 5 | `engine/source/arch_v306.py` | T-187 A 8a6d604a | no | not declared; names no rebar word: not required | urban_boq_m9 | GUARD_HOST | ARCH_TAKEOFF_V3.0.6 runs DG.guard over every V3.0.5 line + the lines it adds (guard_changes); a guard finding on an ADDED line refuses the integration; with no project guard input the guard is NOT run and only the run log says so (state NO_PROJECT_INPUT, guard_changes line 396) |
| 6 | `engine/source/concrete_overlap_ownership.py` | T-189 A 3369f30e | no | not declared; names no rebar word: not required | none | CHECK_ONLY | states whether lines bill an intersection once; produces no BOQ quantity (complements DG-6) |
| 7 | `engine/source/coverage_census_v2.py` | T-140 A c3273f17 | yes | OTHER_REBAR_AWARE | none | CHECK_ONLY | terminal state per BOQ family; reads lines, writes no quantity |
| 8 | `engine/source/curved_geometry_check_v1.py` | T-197 A 97cd747e | no | not declared; names no rebar word: not required | none | CHECK_ONLY | curved / partial footprint issue rows (complements DG-3) |
| 9 | `engine/source/default_guard.py` | T-186 A 18b12176 | yes | OTHER_REBAR_AWARE | arch_v306 | GUARD_HOST | the guard itself (T-186); unwired on its own, run by arch_v306 |
| 10 | `engine/source/document_register_v1.py` | T-195 A 06c2b045 | no | not declared; names no rebar word: not required | none | CHECK_ONLY | sheet register + citation check; a source of the guard's `documents` evidence, not a guarded line |
| 11 | `engine/source/level_chain_v1.py` | T-200 A d699b650 | no | not declared; names no rebar word: not required | none | CHECK_ONLY | datum / link / issue rows (complements DG-4 finished vs structural) |
| 12 | `engine/source/masonry_centreline_v2.py` | T-125 A d3d24d4f; T-169 M 3a229f5e | no | not declared; names no rebar word: not required | none | UNWIRED_PRODUCER | wall-run lengths per thickness (Q-69 B); imported by no method or CLI; DG-1 / DG-3 / DG-5 / DG-6 must run when it is integrated |
| 13 | `engine/source/opening_consistency_v1.py` | T-194 A 4f2678c5 | no | not declared; names no rebar word: not required | none | CHECK_ONLY | plan = elevation = section = schedule issue rows |
| 14 | `engine/source/opening_scope_v1.py` | T-175 A b903360c | no | not declared; names no rebar word: not required | none | UNWIRED_PRODUCER | opening deductions by physical scope; imported by no method; DG-8 DEDUCTION_EXCEEDS_MEMBER and DG-6 apply at integration |
| 15 | `engine/source/route_g_scope_v1.py` | T-142 M 5de8657e | no | not declared; names no rebar word: not required | arch_v301, arch_v302 | GUARDED_VIA_V3.0.6 | route-G occurrence / blinding scope read by arch_v301 / arch_v302 only (not by the released route); its effect reaches the candidate lines that V3.0.6 guards |
| 16 | `engine/source/scope_crosswalk_v1.py` | T-196 A f933ef8a | no | not declared; names no rebar word: not required | none | CHECK_ONLY | freelancer row / candidate line / drawn element crosswalk (complements DG-5) |
| 17 | `engine/source/stair_rule_calculator.py` | T-158 A 21350931 | no | not declared; names no rebar word: not required | none | UNWIRED_PRODUCER | riser / tread counts and required length under UP-STAIR-015; a design check today, imported by no method; any quantity it feeds into a line is guarded at integration (DG-1 / DG-5) |
| 18 | `tools/alsenan_keymap.py` | T-177 M 130e2e32; T-182 M 50991742; T-181 M faa04202 | no | not declared; names no rebar word: not required | scoreboard_v2 | TOOLING | maps engine lines to scorer rows; comparison only, never upstream of a quantity |
| 19 | `tools/m9_rules_manifest.py` | T-158 M 21350931 | no | not declared; names no rebar word: not required | none | TOOLING | rule store manifest build / check |
| 20 | `tools/release_baseline.py` | T-165 A 37124da3 | no | not declared; names no rebar word: not required | none | TOOLING | pins a released baseline run (V2.9 + route G) for Gate B diffs |
| 21 | `tools/scoreboard_v2.py` | T-177 A 130e2e32; T-182 M 50991742 | no | not declared; names no rebar word: not required | alsenan_keymap | TOOLING | SCOREBOARD v2 by script; comparison only |
| 22 | `tools/urban_boq_m9.py` | T-142 M 5de8657e; T-151 M 47df1930; T-167 M cf5819c6; T-179 M 90d0b769; T-187 M 8a6d604a | yes | not declared; tools/ is outside the firewall scan (engine/ only) | label_census, release_baseline, compare | GUARD_HOST | CLI: the guard runs only under --method ARCH_TAKEOFF_V3.0.6 --v306-inputs; --method ARCH_TAKEOFF_V3.0.2 .. V3.0.5 still run UNGUARDED (superseded candidate versions); released V2.9 + route G is not guarded (opt-in candidate only) |

## 2. Results

1. **Firewall registry: complete for the window.** All 5 window modules in engine/ that name reinforcement are declared
   (arch_v302, arch_v303, arch_v305, coverage_census_v2, default_guard as OTHER_REBAR_AWARE); the other 12 engine
   modules name no rebar word, so the registry's own definition does not require a declaration. No declaration was added
   (the registry file is unchanged). tools/urban_boq_m9.py names reinforcement but tools/ is outside the firewall scan
   (engine/ only) by definition; no ACCURATE module or builder imports it statically (the firewall closure test passes).
2. **Default guard: wired in exactly one place.** default_guard.py is imported only by arch_v306.py (ARCH_TAKEOFF_V3.0.6).
   Consequences the Lead and the Checker should know:
   - `--method ARCH_TAKEOFF_V3.0.2 .. V3.0.5` stay selectable in tools/urban_boq_m9.py and run UNGUARDED. Any Gate B diff
     or scoreboard on the candidate should name V3.0.6 (or later), never an earlier extension.
   - A V3.0.6 run without the project's guard input (`--v306-inputs` with a `guard` block) does NOT run the guard; only
     the run log says so (`{"piece": "DEFAULT_GUARD", "state": "NO_PROJECT_INPUT"}`, arch_v306.py:396-397), the same
     convention as the other pieces. A run is guarded only when that log state is `RUN`.
   - Released V2.9 + route G is not guarded (opt-in candidate only; owner rule, unchanged).
3. **Three unwired quantity producers need the guard when they are integrated**: masonry_centreline_v2.py (wall-run
   lengths; DG-1 / DG-3 / DG-5 / DG-6), opening_scope_v1.py (deductions; DG-8 DEDUCTION_EXCEEDS_MEMBER, DG-6) and
   stair_rule_calculator.py (riser / tread counts; DG-1 / DG-5). Proposed acceptance line for any integration row that
   wires one of them: "its lines pass the V3.0.6+ guard with the guard block present (log state RUN), no finding on an
   added line".
4. **Seven check modules** (concrete_overlap_ownership, opening_consistency_v1, document_register_v1,
   curved_geometry_check_v1, scope_crosswalk_v1, level_chain_v1, coverage_census_v2) emit no BOQ quantity: the guard does
   not apply; each complements one guard code (named in the table).

## 3. Engine boundary found by the sweep (not the rebar firewall): K1 third-party imports

The r8 boundary tests (known failures K1_NOT_STDLIB and K1_IMPORTS_EZDXF in KNOWN_FAILURES.md) stop at the FIRST
offending file, so they never show the whole list. Full list on the head (static AST, every `import` incl. lazy ones;
excluding the four by-design exceptions cad/kernel_ezdxf.py, topology_crosscheck.py, ground_slab_recovery.py,
region_recovery.py): 24 engine/source modules import a third-party package.

| Package | Modules (window modules in bold) |
|---|---|
| ezdxf (K1 must not) | arch_v30, **arch_v302 (T-142)**, concrete_ledger_v3, opening_area, plot_edge_members |
| shapely | arch_v213, beam_binding_v2, element_register_v0, exterior_spaces, facade_passage_walls, masonry_centreline, **masonry_centreline_v2 (T-125)**, membrane_coverage_proof_v1, membrane_cutting_plan, membrane_fold_v2 .. v5, room_census_guard, room_label_guard, stair_flight_once_v1, stair_floor_residue |
| numpy | **concrete_overlap_ownership (T-189)** |
| pymupdf | opening_height_pdf (not in the dependency register: B-5 / B-6) |

Inside the window three merges added to an already-red boundary without anyone seeing it, because the test was already
failing on an older file. This is the same failure pattern as the T-186 firewall break (FEEDBACK cause 7). Not fixed here
(the row allows only a registry declaration); it needs a Lead row: either an owner / Lead decision that K1 is no longer
stdlib-only for named geometry modules (extend `by_design` with reasons) or moving the imports.

## 4. Proposed lessons-register row (ENGINEERING_REASONING_STANDARD s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-23 | 396 failing tests on the working head quoted as "3 known failures"; three window merges added K1 boundary violations unseen (T-202) | Boundary tests stop at the first offender, and known failures were carried as prose run after run, so a new failure of an already-red test is invisible | Every gate b compares test by test against one ledger (research/agents_t202/known_failures.json, checked by known_failures.py); a red test is never "known" as a file, only as an id with a cause; an already-red boundary test is re-run with its full offender list before a merge that touches its scope (every task) | tests/t202_guard_sweep (normal: complete window, ledger check exits 0 on known ids; adverse: undeclared rebar module, unclassified module, non-merge commit, NEW id exits 1) | proposed |
