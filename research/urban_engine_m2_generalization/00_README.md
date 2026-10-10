# M2: reusable, generic BOQ engine (development package)

**Planning estimate engine. Not engineering-approved. No prices. The gate stays INCOMPLETE.** Read `01_EXECUTIVE_SUMMARY.md` first.

| # | deliverable (Phase 18) | file |
|---|---|---|
| 1 | Executive development summary | `01_EXECUTIVE_SUMMARY.md` |
| 2 | Architecture before / after | `02_ARCHITECTURE_BEFORE_AFTER.md` |
| 3 | Implemented reusable modules | `03_MODULES.md` |
| 4 | Generic extraction test results | `11_GENERIC_TEST_RESULTS.md`, `evaluation/*.json` |
| 5 | Alsenan generic-route comparison | `04_ALSENAN_GENERIC_VS_FROZEN.md` / `.csv`, `07_ALSENAN_COVERAGE_RISK.csv`, `alsenan_route_g/` |
| 6 | Reinforcement completeness report | `05_REINFORCEMENT_COMPLETENESS.md`, `05_REINFORCEMENT_COMPLETENESS_89.csv`, `alsenan_route_g/REBAR_COMPLETENESS.csv` |
| 7 | Ground-slab gap audit | `06_GROUND_SLAB_GAP_AUDIT.md` / `.csv` |
| 8 | Source-derived visual QA PDF | `alsenan_route_g/VISUAL_QA_OVERLAYS.pdf` and `synthetic_demo_villa_7/VISUAL_QA_OVERLAYS.pdf` (generated, not committed: reproduce with `15_REPRODUCIBLE_COMMANDS.md`); the committed sources are `overlays/*.svg` and `OVERLAYS.html` |
| 9 | Contractor BOQ Excel | `alsenan_route_g/STRUCTURAL_BOQ.xlsx`, `synthetic_demo_villa_7/STRUCTURAL_BOQ.xlsx` (generated, not committed; `CONTRACTOR_BOQ.csv` is committed) |
| 10 | Benchmark discrepancy report | `12_BENCHMARK_DISCREPANCY_REPORT.md`, `09_BENCHMARK_POSITIONS.csv` (positions only) |
| 11 | Accuracy and coverage metrics | `08_ACCURACY_COVERAGE_METRICS.json`, `11_GENERIC_TEST_RESULTS.md` |
| 12 | Remaining technical debt | `13_TECHNICAL_DEBT.md` |
| 13 | Engineering RFIs | `14_ENGINEERING_RFIS.csv` |
| 14 | Reproducible test commands | `15_REPRODUCIBLE_COMMANDS.md` |
| 15 | TEST_RUN.md | `TEST_RUN.md` |
| 16 | Commit and branch details | `16_COMMITS_AND_BRANCH.md` |
| – | The ten questions of Phase 19 | `17_SUCCESS_CRITERIA.md` |
| – | Stair scenarios (owner preferences, side by side) | `10_STAIR_SCENARIOS.csv` |

**Inputs this package used**
- The private ST7757 structural DXF (`data/inputs`, git-ignored).
- `profile_st7757.json`, with four printed values.
- The generic convention set `engine/profiles/URBAN_M2_GENERIC_CONVENTIONS_V1.json`.
- The frozen M1 / S8.1 / S9 registers, for comparison only.

**Builder:** `build_m2_reports.py` regenerates files 04–10 and 08 from the drawing. It refuses to write any output that carries owner text, Arabic source text or a firewalled benchmark number.
