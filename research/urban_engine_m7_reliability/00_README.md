# M7 — Engine reliability: placement-invariant measurement, release policy, held-out validation

M6 asked *what does the drawing show that the takeoff does not hold*. M7 asks *when the takeoff holds a number, can
it be trusted, and does it stay the same when the drawing is drawn differently but the building is the same*. The
work changed the engine, not the project: every rule is a statement about drawings in general, every rule is a
convention in a new set (V5) so the frozen M4–M6 packages still reproduce byte for byte, and the evidence that the
rules generalise is a held-out synthetic set generated only after the engine was frozen.

| | |
|---|---|
| Conventions | `engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json` (66 = V4's 49 + 17 M7 rules). Opt-in on the CLI (`--conventions`); the default of `tools/urban_project_run.py`. The CLI default stays V3. |
| New engine modules | `engine/source/quantity_release.py` (release policy), `engine/source/boq_reconcile.py` (post-freeze BOQ reconciliation) |
| Changed engine modules | `drawing_model`, `generic_route`, `member_detection`, `slab_engine`, `continuous_beams`, `concrete_completeness` (every change gated by a V5 convention), `tools/urban_intake.py` (two unconditional reading fixes that change no frozen output) |
| New tools | `tools/m7_metamorphic.py` (property harness), `tools/m7_evaluate.py` (quantities on cluttered villas against the design), `tools/m7_independent.py` (per-item second method), `tools/urban_project_run.py` (project manifest, blind run, freeze, check, compare) |
| Tests | `tests/m7_reliability/` (geometry fixtures, legend adversarial fixtures, release policy, reconciliation, project runner protocol, properties on cluttered villas, package) |

## How it was built (each step frozen before the next read anything new)

| Step | What | Record |
|---|---|---|
| 1 | Baseline: M6 full suite and held-out records reproduced on the working tree | `02_BASELINE_AND_ARCHITECTURE.md` |
| 2 | Metamorphic harness (translate, rotate, mirror, reorder, explode, duplicate text, unrelated layer, units) on cluttered development villas (seeds 1–16) and on ST7757; every failure traced to a geometric cause; a generic rule per cause | `03_ENGINE_WEAKNESS_REGISTER.csv`, `04_GEOMETRY_AUDIT.md`, `heldout/DEV_METAMORPHIC_SEEDS_1_8.json`, `st7757/METAMORPHIC.json` |
| 3 | Quantity evaluation against the design truth on cluttered villas (the M6 generator's completeness cases on top of the M2 frame) | `tools/m7_evaluate.py` |
| 4 | Release policy, per-item independent checks, project manifest runner, generic BOQ reconciliation | `07_MEASUREMENT_RELEASE_REGISTER.csv`, `08_INDEPENDENT_VALIDATION.md` |
| 5 | Engine freeze `af2822a` (`00_ENGINE_FREEZE.json`, committed in `08c4339` before any held-out seed existed) | `00_ENGINE_FREEZE.json` |
| 6 | Held-out seeds 301–340, generated for the first time and run once, V4 (M6 engine state) against V5 | `heldout/*.json`, `heldout/HELDOUT_SUMMARY.json` |
| 7 | ST7757 V4 vs V5 with a per-convention attribution (post-discovery, not blind) | `st7757/`, `10_BEFORE_AFTER_QUANTITIES.csv` |
| 8 | Three post-freeze fixes found on ST7757 after step 6, reported apart (P1 lintel width bands at 1 mm; P2 set-aside column outlines stay evidence; P3 checker for label-conflict footings) | `01_EXECUTIVE_REPORT.md` §B |
| 9 | Second villa: searched (repository, connected drive) — none available: BLOCKED; intake requirements and the protocol, dry-run end to end on a synthetic project | `09_SECOND_VILLA_BLIND_TEST.md` |
| 10 | Package, workbook, visual QA, full suite | this folder, `12_REGRESSION_RESULTS.md` |

External records (freelancer BOQ, MCP reports) were not opened in M7. No reference quantity is in any engine file;
the unit rate 26.5 KWD/m³ is a reporting input of the workbook and the quotation-risk note only.

## Files

| File | |
|---|---|
| `01_EXECUTIVE_REPORT.md` | answers A–G |
| `02_BASELINE_AND_ARCHITECTURE.md` | baseline reproduction, the pipeline and where its risks were |
| `03_ENGINE_WEAKNESS_REGISTER.csv` | every weakness: found by, rule, ST7757 effect, synthetic evidence, status |
| `04_GEOMETRY_AUDIT.md` | invariance findings, slab topology, before / after |
| `05_DRAWING_INTERPRETATION.md` | legend reader V3, symbol states, layer evidence, adversarial fixtures |
| `06_COMPLETENESS_RECONCILIATION.csv` | completeness detection V4 / V5 (held-out), ST7757 findings and their delta |
| `07_MEASUREMENT_RELEASE_REGISTER.csv` | ST7757 items by trade / family / storey / release state (full register: `st7757/RELEASE_REGISTER.csv`) |
| `08_INDEPENDENT_VALIDATION.md` | held-out protocol and results; per-item second-method checks; tests |
| `09_SECOND_VILLA_BLIND_TEST.md` | blocked; what is needed; the protocol |
| `10_BEFORE_AFTER_QUANTITIES.csv` | ST7757 V4 / V5 by family and storey with the convention that made each change; held-out totals with truth |
| `11_QUOTATION_RISK.md` | at 26.5 KWD/m³: what may and may not be quoted |
| `12_REGRESSION_RESULTS.md` | targeted suites, full suite, classification |
| `13_REPRODUCIBILITY.md` | commands, hashes, determinism |
| `14_VISUAL_ENGINEERING_QA.pdf` | charts and synthetic before / after overlays (no client drawing rendered); generated by `build_visuals.py`, not in git |
| `15_CHATGPT_HANDOFF.md` | what worked, what did not, what to do next |
| `M7_RELIABILITY_WORKBOOK.xlsx` | generated by `build_package.py`, not in git: dashboard, quantities, reconciliation, measured vs unresolved, detection, validation, error, money, traceability |
| `build_package.py`, `build_visuals.py`, `heldout_run.py`, `postfix_run.py`, `st7757_run.py` | the builders (every CSV, the workbook and the PDF are rebuilt from records; `postfix_run.py` repeats the held-out completeness runs on the post-fix engine, reported apart) |
