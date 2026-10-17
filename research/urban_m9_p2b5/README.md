# M9 Phase 2B-5 - ARCH_TAKEOFF_V2.6 waterproofing constructability layer

Stage B of the overnight engineering program. V2.6 is opt-in (`--method ARCH_TAKEOFF_V2.6`). It adds the cutting
plan the engine actually cut and what that plan means on site. It changes no BOQ quantity, and V1 - V2.5 are
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

Engine: `engine/source/wp_install.py` (new), trace in `engine/source/membrane_layout.py`, typed boundary in
`engine/source/wp_geometry.py`, integration in `engine/source/waterproofing_system.py` and `tools/urban_boq_m9.py`.
Tests: `tests/m9_p2b5/` (90 tests). Expected values come from hand derivations and an independent calculator that does
not import the engine.
