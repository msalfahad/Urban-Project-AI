# Repository baseline (Phase 2B-6, Part 5)

**Branch** `claude/access-permissions-setup-ii24ws`. **Head at the start** `5dc2753` (Phase 2B-5 Stage I).

Every reported result below was **re-run** tonight, not copied from the earlier reports. Private runs used the
restored reference plan in the authorised private work area, and only aggregates appear here.

## 1. What was inspected

| item | where | state found |
|---|---|---|
| V2.6 source | `engine/source/wp_install.py` (new, 1 084 lines); `membrane_layout.py`, `wp_geometry.py`, `waterproofing_system.py` (Stage B); `arch_rooms.py`, `door_model.py`, `arch_measure.py` (D-V26-06); `arch_completeness.py`, `owner_finish_scope.py` (D-V26-07); `tools/urban_boq_m9.py` | 11 files, +1 872 / −89 lines since `64827c6`; every change behind `--method ARCH_TAKEOFF_V2.6` |
| previous reports | `research/urban_m9_p2b5/` (24 deliverables) | read; claims re-checked below |
| defect register | `research/urban_m9_p2b5/DEFECTS_AND_CORRECTIONS.md` | superseded by `ENGINEERING_DEFECT_REGISTER.md` (this folder) |
| test evidence | `research/urban_m9_p2b5/TEST_RUN.md` | reproduced (§2) |
| freeze verifier | `tools/freeze_verify.py`, `research/freeze_integrity/` | reproduced (§2) |
| engineering rules | `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json` (39 rules: 32 owner-approved, 4 reference-only, 2 deprecated, 1 project-specific; 4 grouped owner questions); `rules/` 1.5.0 | unchanged; pinned by every run record (rule-set digest) |
| owner decisions | `research/urban_m9_p2b5/OWNER_DECISIONS.md` and two earlier phase files | deduplicated in `OWNER_DECISIONS.md` (this folder) |
| roadmap | `research/urban_m9_p2b5/ROADMAP.md` | superseded by `PRIORITIZED_ROADMAP.md` |
| floor-plan AI research | `research/urban_m9_p2b5/FLOORPLAN_AI_RESEARCH.md`, `LICENCE_ASSESSMENT.md` | extended in `FLOORPLAN_AI_RESEARCH.md` (this folder) |
| CAD / MCP research | `research/urban_m9_p2b5/MCP_SKILLS_AUDIT.md` | extended in `CAD_MCP_GEOMETRY_RESEARCH.md` |
| repository skills | `.claude/skills/urban-*/SKILL.md` (six) | audited in `ENGINEERING_SKILLS_AUDIT.md` |

## 2. Reproduction of the reported results

| reported result (2B-5) | reproduced tonight | result |
|---|---|---|
| V1 - V2.5 byte-identical on three drawings (villa, mirror, reference plan), Mode U and Mode A | snapshot of the head against the Stage A snapshot | **968 files, 0 differ** |
| V2.6 deterministic | V2.6 at the head against the `b9baa7b` snapshot | **272 files, 0 differ** |
| full suite: 9 017 tests; 345 failed + 32 errors, all private-data | full suite at `5dc2753` in a clean clone, matched by test identity with `b9baa7b` | **9 017; 8 378 passed, 345 failed, 32 errors, 160 skipped, 102 xfailed; 0 state changes, 0 new, 0 removed** |
| 182 targeted tests pass | `tests/m9_p2b5` + `tests/m9_p2b5_bench` | **182 passed** |
| freeze verifier 0 differing; environment in lock; closure exit 0 | `freeze_verify.py check / env / closure` | **0 differing; in lock, no package differences; exit 0** |
| real rooms: 8 of 66 checks failing under V2.6 | Stage C re-score of the private V2.6 run | **8 of 66** (7 in the held door's room, 1 basin-lobby attribution) |
| D-D2: ~0.7 % of the plan's wall run on curved walls | a raw-ezdxf census | **corrected: 0.80 % (inner face) / 0.88 % (mean radius), one band** |
| D-D2: 4 of 38 rooms arc-bounded | the experiment's polygon diff | **4 of 38**, all dry |

## 3. Tests that depend on private data that is not in the repository

| count | where | cause |
|---|---|---|
| 345 failures + 32 errors | 26 test files of earlier stages (M5 reconciliation, the structural stages, workbook rules) | 375 are `FileNotFoundError` on git-ignored datasets and workbooks; the other 2 need a private source inventory and a workbook under `data/` |

They fail identically on every head since Stage A and are reported separately every phase. No test of this program
depends on a private drawing: `tests/m9_p2b6` builds every drawing synthetically.

## 4. Repository changes made by this program

| path | what |
|---|---|
| `tools/arch_run_audit.py` | new: read-only audit of a finished run (A01 - A11) |
| `tests/m9_p2b6/` | new: synthetic fixtures (`p2b6_fixtures.py`), CLI helpers, 14 found-defect / invariance tests, 9 audit tests |
| `.claude/skills/urban-cad-audit/SKILL.md` | updated: V2.6, the run audit, the new failure modes |
| `research/urban_m9_p2b6/` | the 14 deliverables, experiment scripts and the experiment patch (not applied) |

No file under `engine/`, `rules/`, `knowledge/` or any frozen package was changed.
