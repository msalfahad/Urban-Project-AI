# Phase 2B-2 - master engineering rules, waterproofing optimization and door feasibility (ARCH_TAKEOFF_V2.4)

Owner program "URBAN PROJECT AI - master engineering rules, waterproofing optimization & door feasibility"
(2026-10-16, Parts 1 - 10). A controlled extension of ARCH_TAKEOFF_V2.3: a new opt-in method, ARCH_TAKEOFF_V2.4; V1 ..
V2.3 outputs byte-identical; `rules/` and `opening_census.py` untouched. Synthetic examples are shown in full; the
reference plan only as aggregates.

```
python3 -I tools/urban_boq_m9.py arch --drawings PLAN.dxf --out OUT --method ARCH_TAKEOFF_V2.4 \
        [--project-rules PROJECT_RULES.json] [--facts FACTS.json] [--decisions DECISIONS.json]
```

## The eight questions (Part 10) and where V2.4 answers them

| # | Question | Answer in every run | Synthetic villa | Reference plan (aggregates) |
|---|---|---|---|---|
| 1 | What does the drawing show? | rooms, openings, walls, measured lines (`ARCH_*.json`, `BOQ_LINES`); `ENGINEERING_SUMMARY.json` `what_the_drawing_shows` | 6 door elements, 3 waterproofed areas | 28 door elements, 17 waterproofed areas |
| 2 | What does Urban require? | registry 1.1.0 values on the rules sheet (`PROJECT_RULES_SHEET`) | roll 1.00 x 10.00 m, lap 0.10 m, upturn 0.20 m; doors 1.10 / 1.00 / 1.10 m openings | same |
| 3 | Where do they differ? | door compliance and enlargement; doorway transitions; project overrides (`where_they_differ`) | 5 doors 0.20 m below standard; 3 doorway transitions open | 23 doors need enlargement; 15 doorway transitions open |
| 4 | Can the modification fit? | door feasibility class per door (`DOOR_FEASIBILITY`) | 3 geometrically possible, 2 engineering review (no column frame on the first floor), 1 insufficient evidence | 11 possible, 5 constrained, 12 insufficient evidence |
| 5 | What is measured, assumed, proposed, unresolved? | evidence state on every line; four door views; rules-sheet states; ledger | `measured_assumed_proposed_unresolved` | ledger conserves, CONFIRMED_MISSING 0 |
| 6 | How much material, with detailing and waste? | A net / B installed / C rolls per system; consumed, cutting waste, withheld detailing (`WATERPROOFING_SCHEDULE`, `MEMBRANE_CUTTING_PLAN`) | 31.36 / 46.22 m2, 6 rolls (7 if each area alone), PROVISIONAL | 72.12 / 120.02 m2, 14 rolls (19 if alone), PROVISIONAL |
| 7 | Which project rules govern? | the rules sheet: Level B rows with scope, source, state; `rules_sha256` in every output | none given: Urban standards, OWNER_STANDARD_ASSUMED | none given |
| 8 | What must be approved? | `APPROVALS_REQUIRED.json`: design changes, structural confirmations, waterproofing system and details, rule conflicts | door enlargements (owner / architect, structural engineer), the membrane system and details | 51 door items, 1 waterproofing system |

## Deliverables (Part 9)

| # | Deliverable | File |
|---|---|---|
| 1 | Pre-implementation audit | `PRE_IMPLEMENTATION_AUDIT.md` |
| 2 | Updated engineering registry | `REGISTRY_1_1_0.md` (generated; source `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json`), `KNOWLEDGE_RETENTION_AUDIT.md` (Part 6, generated) |
| 3 | Supersession and conflict report | `SUPERSESSION_AND_CONFLICTS.md` (generated) |
| 4 | Project Engineering Rules Sheet generator | `RULES_SHEET_GENERATOR.md`, `RULES_SHEET_EXAMPLE.md` (generated) |
| 5 | Waterproofing calculation methodology | `WATERPROOFING_METHODOLOGY.md` |
| 6 | Membrane cutting and roll-layout report | `MEMBRANE_CUTTING_REPORT.md` (generated) |
| 7 | Door feasibility methodology | `DOOR_FEASIBILITY_METHODOLOGY.md` |
| 8 | Door-by-door feasibility schedule | `DOOR_SCHEDULE_SYNTHETIC_VILLA.md` (generated; the reference plan's schedule is private) |
| 9 | As-drawn versus owner-standard comparison | `AS_DRAWN_VS_OWNER_STANDARD.md` (generated) |
| 10 | Before / after BOQ effects | `BEFORE_AFTER_BOQ.md`, `BEFORE_AFTER_SYNTHETIC.md` (generated) |
| 11 | Tests and remaining failures | `TEST_RESULTS.md` |
| 12 | Frozen-version integrity evidence | `FROZEN_INTEGRITY.md` |
| 13 | Risks and unresolved questions | `RISKS_AND_UNRESOLVED.md` |
| 14 | Independent reviewer findings | `INDEPENDENT_REVIEW.md` |
| 15 | Roadmap to 95 % | `ROADMAP_TO_95.md` |

The generated files come from `make_p2b2_docs.py` (`python3 -I research/urban_m9_p2b2/make_p2b2_docs.py`): views of the
committed registry and of the synthetic villa run, never hand-transcribed.

## Code and data

| Path | What |
|---|---|
| `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json` | registry 1.1.0 (39 rules, 14 conflicts, 48 question patterns), built by `tools/kb_build_1_1.py` from the frozen 1.0.0 |
| `engine/source/knowledge.py` | versioned registry access (`using("1.1.0")` for V2.4; 1.0.0 stays the default) |
| `engine/source/project_rules.py` | Level B project rules, scoped resolution, the rules sheet, its hash and invalidation |
| `engine/source/wp_geometry.py` | the waterproofed boundary edge by edge: roles, corners, runs |
| `engine/source/waterproofing_system.py` | areas, transitions, penetrations, layouts, the cutting plan, schedules, BOQ lines |
| `engine/source/door_feasibility.py` | clearances, constraints, placements, swing, structure, classes, views, approvals, jamb plaster heights |
| `tools/urban_boq_m9.py` | method ARCH_TAKEOFF_V2.4, `--project-rules`, outputs `PROJECT_RULES_SHEET.json/.csv`, `WATERPROOFING_SCHEDULE.json/.csv`, `MEMBRANE_CUTTING_PLAN.json`, `DOOR_FEASIBILITY.json/.csv`, `APPROVALS_REQUIRED.json`, `ENGINEERING_SUMMARY.json`, `OUTPUT_MANIFEST.json` |
| `tests/m9_p2b2/` | 63 tests: registry 10, project rules 9, waterproofing 20, door feasibility 17, CLI integration 7 |
