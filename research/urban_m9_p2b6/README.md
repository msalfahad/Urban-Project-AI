# Phase 2B-6: overnight engineering intelligence program

## The 14 deliverables (Part 14)

| # | file | what it holds |
|---|---|---|
| 1 | `EXECUTIVE_SUMMARY.md` | the seven success questions answered |
| 2 | `REPOSITORY_BASELINE.md` | what was inspected; every reported result re-run |
| 3 | `V26_VERIFICATION.md` | Part 5's ten questions |
| 4 | `ENGINEERING_DEFECT_REGISTER.md` | every open defect: root cause, quantities, reference, solution, risk, tests, readiness |
| 5 | `FLOORPLAN_AI_RESEARCH.md` | 14 points per candidate (extends 2B-5's report) |
| 6 | `CAD_MCP_GEOMETRY_RESEARCH.md` | MCP availability, U-C4N library run, geometry libraries |
| 7 | `ENGINEERING_SKILLS_AUDIT.md` | the six skills; knowledge classes; question deduplication |
| 8 | `EXPERIMENT_RESULTS.md` | Experiments A - H with numbers |
| 9 | `BOQ_CAPABILITY_MATRIX.md` | the whole BOQ, capability by capability; prioritisation scores |
| 10 | `PRIORITIZED_ROADMAP.md` | ranked work and phases |
| 11 | `NEXT_IMPLEMENTATION_PLAN.md` | the proposed opt-in method: scope, acceptance tests, steps, risks |
| 12 | `TEST_EVIDENCE.md` | tests, frozen integrity, real-room and synthetic before / after |
| 13 | `OWNER_DECISIONS.md` | one deduplicated register (answered / not a question / open) |
| 14 | `CHATGPT_REVIEW_BRIEF.md` | the review brief |

## Other contents

`experiments/` holds the clone patch and two synthetic scripts:

| file | what it is |
|---|---|
| `ENGINE_EXPERIMENTS_NOT_APPLIED.patch` | the clone's engine experiments, behind `URBAN_EXP` flags; documentation only, **not applied** to `engine/` |
| `vision_crosscheck.py` | Experiment D |
| `uc4n_library_run.py` | Experiment H |

## Repository changes

| path | what |
|---|---|
| `tools/arch_run_audit.py` | read-only run audit |
| `tests/m9_p2b6/` | fixtures, helpers, 23 tests |
| `.claude/skills/urban-cad-audit/SKILL.md` | updated |

## What these documents supersede in `research/urban_m9_p2b5/`

The 2B-5 files are kept unchanged as the record of that phase.

| 2B-5 file | superseded by |
|---|---|
| `DEFECTS_AND_CORRECTIONS.md` (open items) | `ENGINEERING_DEFECT_REGISTER.md` |
| `ROADMAP.md` | `PRIORITIZED_ROADMAP.md` |
| `OWNER_DECISIONS.md` (and 2B-0, 2B-3 lists) | `OWNER_DECISIONS.md` |
| `ENGINE_CAPABILITY.md` | `BOQ_CAPABILITY_MATRIX.md` |
| `CHATGPT_BRIEF.md` | `CHATGPT_REVIEW_BRIEF.md` |
| `FLOORPLAN_AI_RESEARCH.md`, `MCP_SKILLS_AUDIT.md` | extended (not replaced) by the 2B-6 research files |

## Privacy

| rule | how it is kept |
|---|---|
| reference-plan data | appears only as aggregates or differences |
| drawings | none committed; every fixture is generated |
| private scripts | the Stage C scorer and the raw arc census stay in the private work area |
