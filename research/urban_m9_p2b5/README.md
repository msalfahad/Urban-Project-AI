# M9 Phase 2B-5 - ARCH_TAKEOFF_V2.6 waterproofing constructability layer

Stage B of the overnight engineering program. V2.6 is opt-in (`--method ARCH_TAKEOFF_V2.6`). It adds the cutting
plan the engine actually cut and what that plan means on site. That layer changes no BOQ quantity; the two later
V2.6 corrections (D-V26-06 door reconciliation, D-V26-07 doorway strip split) move doorway lines only. V1 - V2.5 are
untouched.

| file | content |
|---|---|
| `V26_IMPLEMENTATION_REPORT.md` | what changed, authorisation boundaries, corrections vs the Phase 2B-4 findings, examples, acceptance gate, reference-plan aggregates, byte identity, new findings, defects fixed |
| `INSTALLATION_GEOMETRY.md` | the installation model: the seven quantities kept apart, piece ids, runs, corners, jambs, terminations, joints, seams, stagger, penetrations, drains, lay order, junction alternatives, what is not implemented |
| `WORKED_EXAMPLES.md` | the ten examples through the full verification chain (generated) - 297 of 297 checks pass |
| `VERIFICATION_CHAIN.csv` | the same checks as rows: example, quantity, expected (hand), engine, reference, difference, result |
| `JUNCTION_ALTERNATIVES.md` | the floor-to-wall junction alternatives per example and the flange sweeps (generated). Owner naming: A = continuous fold, B = separate upturn |
| `SCREENSHOT_REVIEW.md` | review of the four V2.5 diagrams and the new V2.6 diagrams (the owner's own screenshot files were not available) |
| `diagrams/IX-nn_install.svg`, `diagrams/IX-nn_cutting.svg` | installation plan and cutting plan of examples IX-01 to IX-08 (generated) |
| `make_p2b5.py` | the generator: `python3 -s research/urban_m9_p2b5/make_p2b5.py` (reproducible byte for byte) |

Stages C - F of the same program (real rooms, MCP and skills, floor-plan AI, the room-reader benchmark):

| file | content |
|---|---|
| `REAL_ROOM_VERIFICATION.md` | five real rooms measured independently (aggregates only): 66 checks, discrepancy register D-C1 - D-C5, error propagation, the D-C1 follow-up and its V2.6 re-score |
| `MCP_SKILLS_AUDIT.md` | the session's MCP inventory, the CAD MCP candidates, the Part 4.2 fixtures, the defects D-D1 / D-D2, ideas re-implemented, the skills inventory and the six Urban skills |
| `ROOM_READER_BENCHMARK.md` | the benchmark's cases, readers, metrics and the reading of the results |
| `bench/BENCHMARK_RESULTS.md`, `.json` | the generated benchmark figures (16 cases x up to 6 methods, hybrid records) |
| `FLOORPLAN_AI_RESEARCH.md` | floor-plan AI candidates with licences / weights / commercial use, the deterministic prototype, results, the hybrid architecture, the verdict |

Stages G - I (impact, review, regression, deliverables):

| file | content |
|---|---|
| `EXECUTIVE_SUMMARY.md` | the program in one page |
| `ENGINE_CAPABILITY.md` | what the engine can be trusted with now, by capability |
| `BOQ_IMPACT.md` | every change and open defect by BOQ line family, synthetic and real-plan aggregates |
| `RULE_PRECEDENCE.md` | Part 7 standards, precedence, provenance classes, the Part 8.3 tests |
| `DEFECTS_AND_CORRECTIONS.md` | engine defects, defects in this program's own work, corrections to statements |
| `OWNER_DECISIONS.md` | the outstanding genuine owner decisions |
| `ROADMAP.md` | development ranked by expected accuracy improvement |
| `LICENCE_ASSESSMENT.md` | open-source licences and how each item is used |
| `INDEPENDENT_REVIEW.md` | the program's own work challenged, by severity |
| `TEST_RUN.md` | the full suite against the Stage A baseline by test identity, frozen-integrity evidence |
| `DELIVERABLES.md` | the 24 Part 10 deliverables mapped to files |
| `CHATGPT_BRIEF.md` | the brief for ChatGPT: what worked, what is not working, what next |

Engine: `engine/source/wp_install.py` (new), trace in `engine/source/membrane_layout.py`, typed boundary in
`engine/source/wp_geometry.py`, integration in `engine/source/waterproofing_system.py` and `tools/urban_boq_m9.py`.
D-V26-06 (door symbol reconciliation): `engine/source/arch_rooms.py`, `engine/source/door_model.py`,
`engine/source/arch_measure.py`. D-V26-07 (doorway strips split at the opening boxes):
`engine/source/arch_completeness.py`, `engine/source/owner_finish_scope.py`, `engine/source/arch_measure.py`. Tests:
`tests/m9_p2b5/` (the installation layer, the door reconciliation, the strip split, the curved-wall characterisation)
and `tests/m9_p2b5_bench/` (the room-reader benchmark and the skills check). Expected values come from hand
derivations and independent calculators / readers that do not import the engine.
