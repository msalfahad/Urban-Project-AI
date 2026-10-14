# Phase 2B-1 - engineering knowledge, owner rules and ARCH_TAKEOFF_V2.3

Owner master program "Master engineering intelligence, owner knowledge and BOQ development" and the owner
correction on door opening dimensions, both of 2026-10-14. Work packages WP-1 .. WP-6. Aggregate results only: the
reference plan's per-door, per-room and line-level outputs stay private.

## Deliverables (Part J)

| # | Deliverable | File |
|---|---|---|
| 1 | Executive engineering summary | `EXECUTIVE_SUMMARY.md` |
| 2 | Root-cause analysis of repeated questions (WP-1) | `ENGINEERING_KNOWLEDGE_AUDIT.md` |
| 3 | Permanent owner-rule register | `OWNER_RULE_REGISTER.md` (a view of `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json`) |
| 4 | Rule conflict and precedence matrix | `RULE_CONFLICT_PRECEDENCE_MATRIX.md` |
| 5 | Construction reasoning model (WP-2) | `ENGINEERING_REASONING_MODEL.md` |
| 6 | Door classification and opening-standard implementation (WP-3) | `DOOR_RULE_IMPLEMENTATION_REPORT.md` |
| 7 | As-drawn versus owner-required BOQ examples | `AS_DRAWN_VS_OWNER_REQUIRED_EXAMPLES.md` |
| 8 | Wet-area and skirting validation (WP-4) | `FINISH_ELIGIBILITY_REPORT.md` |
| 9 | Elevator exclusion and quotation-schedule validation | `ELEVATOR_SCHEDULE_VALIDATION.md` |
| 10 | Element and surface completeness | `COMPLETENESS_REPORT.md` |
| 11 | Before / after quantity comparison | `BEFORE_AFTER_COMPARISON.md` |
| 12 | Tests and regression results (WP-5) | `TEST_RESULTS.md` |
| 13 | Frozen-version integrity evidence | `FROZEN_INTEGRITY.md` |
| 14 | Independent objections and remaining risks (WP-6) | `INDEPENDENT_AUDIT.md` |
| 15 | Outstanding genuine owner questions only | `OWNER_QUESTIONS.md` |
| 16 | Recommended next-stage roadmap | `ROADMAP.md` |

## Code and data

| Path | What |
|---|---|
| `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json` | the registry (rules, conflicts, question catalogue, owner questions) - built by `tools/kb_build.py` |
| `knowledge/RULE_SOURCE_INDEX.json` | every rule / fact / question source of the repository and the earlier-question crosswalk - `tools/kb_index.py` |
| `engine/source/knowledge.py` | registry access, precedence, question classification and grouping |
| `engine/source/space_model.py` | space connectivity model and project decisions |
| `engine/source/door_standards.py` | door categories, owner opening standard, heights, scenarios, dependency map, elevator schedule |
| `engine/source/owner_finish_scope.py` | wet-area scope, wall-tile height, thresholds, jamb plaster, passage-jamb skirting, exterior waterproofing |
| `tools/urban_boq_m9.py` | method `ARCH_TAKEOFF_V2.3`; new outputs `SPACE_MODEL.json`, `DOOR_SCENARIOS.json/.csv`, `ELEVATOR_SCHEDULE.json`, `OWNER_QUESTIONS.json`, `BOQ_SCENARIOS.json`; option `--decisions` (project decisions, URBAN_PROJECT_DECISIONS_V1, kept with the project's private inputs) |
| `tests/m9_kb/` | 78 tests |

## Running

```
python3 -I tools/urban_boq_m9.py arch --drawings PLAN.dxf --out OUT --method ARCH_TAKEOFF_V2.3 \
        [--facts FACTS.json] [--decisions DECISIONS.json]
python3 -I tools/kb_build.py --check && python3 -I tools/kb_index.py --check
python3 -m pytest tests/m9_kb
```
