# Phase 2B-4 - V2.5 waterproofing constructability review

A focused independent construction audit of the V2.5 waterproofing diagrams and cutting plans for three rooms:
- the 3.00 x 4.00 m bathroom;
- the 3.60 x 3.00 m wet area with two doors and a pipe sleeve;
- the L-shaped bathroom.

Its purpose is to tell a mathematically optimised cutting plan apart from a physically buildable installation. V1 -
V2.5 are frozen and unchanged: no engine, CLI, rules or registry file was touched. The corrections are a documented
opt-in patch, not applied. Floorplan AI research has not been started.

## Results in one table

| Question | Answer |
|---|---|
| How does the 0.20 m upturn meet the floor in V2.5? | As a separate band strip folded at the junction, with a 0.10 m flange lapped onto the floor sheet. The 0.10 m is the UP-WP-002 joint lap, assumed for a junction the rule does not cover. The junction is not listed as an open detail (F-01) |
| Buildable alternatives for the 3 x 4 m bathroom | **A, separate upstand:** 17.80 m2 / 2 rolls with a 0.10 m flange; 18.77 (0.11 - 0.13 m) and 18.75 (0.14 - 0.15 m) / 2 rolls; 20.60 m2 / **3 rolls** from 0.16 m.<br>**A + a reinforcing strip:** BLOCKED (product data).<br>**B, continuous fold:** 17.60 m2 / 2 rolls / 3 seams.<br>All CONDITIONAL on the product detail |
| Are 17.80 m2 and 2 rolls valid? | 2 rolls: yes, for every flange up to 0.15 m and for the continuous fold. 17.80 m2: only under V2.5's own assumption. The proven subtotal of 14.80 m2 holds in every case (`WPB_FLOOR_TO_WALL_JUNCTION.md`) |
| The two-door room | Both doorway pieces are right and both transitions correctly UNRESOLVED. Each doorway piece meets the band ends edge to edge at both jambs (4 open junctions). The D2 lap crosses a floor-seam end. The pipe sleeve is counted, its treatment withheld; a centred collar up to 0.60 m stays clear. One band joint ends 0.02 m from a corner; 0.14 m once rearranged (`WPE_DOORS_AND_PIPE.md`) |
| The L-shape | Every corner is continuous inside a band piece except (2,3), where a piece starts on the corner; at best 0.10 m once rearranged. The external corner needs its own piece. The step offcut is a reusable 1.00 x 0.80 m piece, not a 0.27 x 3.00 m trim; reused, it gives 13.50 instead of 13.80 m2 (`WPD_CORNERS_SEAMS_CUTTING.md`) |
| V2.5 quantities | All reproduced by the independent piece-level rebuild (`ENGINE_VS_REBUILD.md`) |
| Findings | 12 (F-01 - F-12): 4 FAIL (junction assumed, record not cuttable, joints unchecked, roll-sensitivity statement), 4 PASS with notes, 3 notes, 1 PASS (`CONSTRUCTABILITY_AUDIT_REPORT.md`) |
| Tests | `tests/m9_p2b4`: 31 tests, all pass |

## Files

| File | What |
|---|---|
| `CONSTRUCTABILITY_AUDIT_REPORT.md` | the short engineering audit report: method, findings with PASS / FAIL, conclusions |
| `WPB_FLOOR_TO_WALL_JUNCTION.md` | the 3 x 4 m bathroom: both junction methods; every strip and upturn piece; laps by type; reconciliation; the validity of 17.80 m2 / 2 rolls |
| `WPE_DOORS_AND_PIPE.md` | the two door transitions and the pipe sleeve |
| `WPD_CORNERS_SEAMS_CUTTING.md` | internal-corner continuity, seam locations, material cutting |
| `PRODUCT_AND_OWNER_CONFIRMATIONS.md` | what needs product-specific confirmation; new owner decisions N-11 - N-13; N-9 extended |
| `PATCH_PROPOSAL_V2_6.md` | the documented opt-in patch and its authorisation boundaries (not applied) |
| `PLAN_TABLES.md` (generated) | every audited plan piece by piece: size, roll, parent, destination; laps; junctions; balance; joints; corners |
| `JUNCTION_SWEEP.md` / `.csv` (generated) | the 3 x 4 m bathroom for junction flanges 0.10 - 0.20 m, both readings of the selection order |
| `ENGINE_VS_REBUILD.md` (generated) | the V2.5 engine's records against the rebuild |
| `diagrams/` (generated) | corrected diagrams: for each of the 14 plans an installation plan (upturn folded out flat, pieces numbered, joints, corners, jambs, seam ends, pipe) and a cutting plan (every rip and cross-cut, destinations, offcut classes); `JUNCTION_SECTIONS.svg` (the two junction methods) |
| `make_p2b4_audit.py` | regenerates the generated files: `python3 -I research/urban_m9_p2b4/make_p2b4_audit.py` |
| `CHATGPT_BRIEF.md` | what worked, what did not, what to do next |

Plans: WPB-A1 (V2.5 as planned), -A1-ARR (same pieces, buildable order), -A1-FJ (fewest joints), -A2-LM / -A2-FJ
(0.15 m flange), -B (continuous fold). Then WPE-A1, -A1-ARR, -A1-FJ, -B; and WPD-A1, -A1-ARR, -REUSE, -FJ.

## The audit library

| File | What |
|---|---|
| `tests/m9_p2b4/construct_reference.py` | the independent construction calculator: stdlib, integer mm, no engine import; plan verifier with a 10 mm coverage grid, material tree and balance, junction inventory, joint-arrangement search, planners for both junction methods |
| `tests/m9_p2b4/construct_cases.py` | the rooms, the 14 plans piece by piece, their hand derivations and expected literals; the hand-verified sweep points |
| `tests/m9_p2b4/construct_engine.py` | reads the V2.5 engine's records; the only file of the library that reaches the engine |
| `tests/m9_p2b4/test_p2b4_*.py` | independence, plans, alternatives, engine comparison and pinned findings |

## Integrity

| Check | Result |
|---|---|
| Frozen code and data | no file under `engine/`, `tools/`, `rules/` or `research/freeze_integrity/` changed (the audit adds only `tests/m9_p2b4` and this folder); V1 - V2.5 outputs therefore cannot change |
| Freeze verifier | `tools/freeze_verify.py check`: 0 frozen artefacts differ |
| Tests | `tests/m9_p2b4` 31 passed; `tests/m9_p2b3` (the V2.5 proof library) 59 passed; the S1 package hygiene test 6 passed |
| Reproducibility | the generated files are byte-identical when regenerated, also under a different Python hash seed |
| Hygiene | identity, external-figure and secret scan of every new file: 0 findings |
