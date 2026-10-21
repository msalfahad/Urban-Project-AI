# Phase 2B-3 - engineering calculation proof and multi-drawing validation (ARCH_TAKEOFF_V2.5)

Owner program "URBAN PROJECT AI - V2.5 engineering calculation proof & multi-drawing validation" (WP-1 .. WP-8),
with the owner's safeguards of 2026-10-16. The approach: every measurement rule the engine applies is proven on a
human-readable example first, calculated independently of the engine, before it is trusted. What the proofs found
wrong is corrected in a new opt-in method, ARCH_TAKEOFF_V2.5. V1 .. V2.4 stay byte-identical; `rules/` and
`opening_census.py` are untouched. Synthetic examples are shown in full; the reference plan appears as aggregates only.

```
python3 -I tools/urban_boq_m9.py arch --drawings PLAN.dxf --out OUT --method ARCH_TAKEOFF_V2.5 \
        [--project-rules PROJECT_RULES.json] [--independent-checks CHECKS.json] [--facts FACTS.json]
```

## Results in one table

| | Result |
|---|---|
| 3.00 x 4.00 m bathroom (WP-2) | A 12.00, upturn 2.60 (13.00 m eligible), subtotal 14.60 m2; 5 strips of 3.00 m (last 0.40 m); band segment 2.80 m; laps 2.72, B 17.52, **consumed 17.80 m2, 2 rolls**, waste 0.28 m2. Hand = reference = engine = drawing route. Doorway detail UNRESOLVED (0.00 - 0.20 m2); 2 rolls for every doorway alternative (`WP2_BATHROOM_3x4_PROOF.md`) |
| Waterproofing cases | 13 (A 2x2, B 3x4, S strip boundary, C drain, CX drain patch, BX threshold detail, LX 0.15 m lap, D L-shape, E kitchen 2 doors + pipe, F roof, G balcony, W WC, H shared rolls): all pass on V2.5, in sequence; V2.4 fails in every case with a band segment (D-V25-01) |
| Door cases | 10 (the program's list): all pass on V2.5; V2.4 fails one (DR-06, the reach boundary) |
| Rules-sheet cases | 5 on the proof drawing PD-1: scope, conflict, drawing binding (mismatch refused), invalidation |
| Hand vs independent reference | every compared quantity agrees (waterproofing 10 - 20 per case, doors 5 - 18) |
| Engine defects found and fixed (V2.5 only) | 9 (`DEFECT_REGISTER.md`); 5 errors in the proof work itself found by the comparison and corrected by re-derivation |
| V1 .. V2.4 | 747 of 747 output files byte-identical to a clean baseline of HEAD |
| V2.5 | deterministic (254 of 254 files over two runs); villa 6 -> 5 rolls (proven minimal); reference plan 14 rolls (proven minimal), 138.13 -> 136.36 m2 consumed |
| Tests | 59 new (`tests/m9_p2b3`), all pass. Affected suites with the reference plan: 647 passed, 0 failed. Full suite: 8165 passed, **0 new failures** against the Phase 2B-2 baseline; its 345 failed + 32 errors are the known baseline set, unchanged test by test (`REGRESSION_AND_FROZEN_INTEGRITY.md`) |

## Deliverables (WP-8)

| # | Deliverable | File |
|---|---|---|
| 1 | Proof methodology (incl. the reference calculator's formulas) | `PROOF_METHODOLOGY.md` |
| 2 | Waterproofing worked examples (tables) | `WP2_BATHROOM_3x4_PROOF.md` (the 3x4 bathroom strip by strip), `CALCULATION_SHEETS.md` (generated, every case) |
| 3 | Layout diagrams | `diagrams/<case>_layout.svg` (generated) |
| 4 | Roll cutting plans | `CUTTING_PLANS.md`, `diagrams/<case>_rolls.svg` (generated) |
| 5 | Door worked examples | `DOOR_WORKED_EXAMPLES.md` (generated) |
| 6 | Project rules comparison examples | `RULES_SHEET_EXAMPLES.md` (generated, through the CLI) |
| 7 | Expected versus actual | `EXPECTED_VS_ACTUAL.md`, `EXPECTED_VS_ACTUAL.csv` (generated) |
| 8 | Defect register and fixes | `DEFECT_REGISTER.md` |
| 9 | BOQ traceability matrix | `TRACEABILITY_MATRIX.md` (generated); every V2.5 run writes `BOQ_TRACEABILITY.json / .csv` |
| 10 | Regression and frozen-integrity report | `REGRESSION_AND_FROZEN_INTEGRITY.md` |
| 11 | Remaining uncertainties | `REMAINING_UNCERTAINTIES.md`; open owner decisions separately in `OWNER_DECISIONS_OPEN.md` |
| 12 | Next-stage recommendations | `NEXT_STAGE_RECOMMENDATIONS.md` |
| - | Independent review | `INDEPENDENT_REVIEW.md` |
| - | Brief for ChatGPT | `CHATGPT_BRIEF.md` |

The generated files come from `make_p2b3_docs.py` (`python3 -I research/urban_m9_p2b3/make_p2b3_docs.py`): views of
the committed proof cases and of engine runs made by the generator - never hand-transcribed.

## Code and data

| Path | What |
|---|---|
| `tests/m9_p2b3/proof_cases.py`, `proof_cases_doors.py`, `proof_cases_rules.py` | the proof cases: scenario, rules, overrides, hand calculation, expected literals, coordinates, exclusions |
| `tests/m9_p2b3/proof_reference.py` | the independent reference calculator (stdlib only, millimetres, exhaustive search) |
| `tests/m9_p2b3/proof_check.py` | hand vs reference |
| `tests/m9_p2b3/proof_engine.py` | the engine adapter and the comparison (the only library file that imports the engine) |
| `tests/m9_p2b3/proof_drawings.py` | the proof drawing PD-1 (DXF) |
| `tests/m9_p2b3/test_p2b3_*.py` | 59 tests: independence 4, waterproofing proofs 29, door proofs 13, rules and traceability 8, integration 5 (parametrised counts) |
| `engine/source/membrane_layout.py` | V2.5 band planner (`band_planner` = MIN_SEGMENT_V2_5), exact roll packing (`pack_rolls`), detail patches - all behind keys no earlier method passes |
| `engine/source/waterproofing_system.py` | `build_area(..., v25=True)`: band topology of a resolved doorway detail, patches, material basis and roll sensitivity; `cutting_plan(..., exact=True)` |
| `engine/source/door_feasibility.py` | `feasibility(..., v25=True)`: inclusive reach, conservative open run |
| `engine/source/traceability.py` | the BOQ traceability chain and the method-proof table |
| `tools/urban_boq_m9.py` | method ARCH_TAKEOFF_V2.5, `--independent-checks`, the drawing binding of the project rules, `BOQ_TRACEABILITY.json / .csv` |
