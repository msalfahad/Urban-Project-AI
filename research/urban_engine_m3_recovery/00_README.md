# M3: real-drawing recovery and BOQ completeness (development package)

**Planning estimate engine. Not engineering-approved. No prices. The gate stays INCOMPLETE.**

Read `01_FINAL_REPORT.md` first.

## Deliverables

| # | Deliverable | File |
|---|---|---|
| 1 | Final report (items 1–10) | `01_FINAL_REPORT.md` |
| 2 | Before / after detection (M2 vs M3) | `02_BEFORE_AFTER_DETECTION.csv` |
| 3 | Concrete by family (M2, M3 low/base/high, frozen M1) | `03_CONCRETE_BY_FAMILY.csv` |
| 4 | Reinforcement by family | `04_REINFORCEMENT_BY_FAMILY.csv` |
| 5 | Reconciliation M2 → M3, component level, with classes | `05_RECONCILIATION_M2_TO_M3.csv`, `05_RECONCILIATION_SUMMARY.csv` |
| 6 | Beams by mark vs the frozen replay | `06_BEAMS_BY_MARK_VS_FROZEN.csv` |
| 7 | The 89 historical reinforcement components | `07_REINFORCEMENT_COMPLETENESS_89.csv` |
| 8 | Missing reinforcement by family and storey | `08_MISSING_STEEL_BY_FAMILY_STOREY.csv`; also BOQ section D, the `MISSING_STEEL` sheet and the report PDF |
| 9 | External estimates, positions only | `09_BENCHMARK_POSITIONS.csv` |
| 10 | Unresolved register | `10_UNRESOLVED_REGISTER.csv` |
| 11 | Not-detected register and coverage risk | `11_NOT_DETECTED_REGISTER.csv`, `11_COVERAGE_RISK.csv` |
| 12 | Coverage dashboard (overlays before / after, inline SVG) | `12_COVERAGE_DASHBOARD.html` |
| 13 | Held-out evaluation on unseen drawings | `13_HELDOUT_EVALUATION.md`, `13_HELDOUT_EVALUATION.json` |
| 14 | Runtime, caching, incremental recalculation | `14_PERFORMANCE.json` |
| 15 | Workflow: one command, PDF evidence, manual transcription | `15_WORKFLOW.md` |
| 16 | Regression record: real bug → fix → test | `16_REGRESSION_RECORD.md` |
| 17 | Test run | `17_TEST_RUN.md`, `TEST_GATE_bfa208e.json` |
| 18 | Notes for ChatGPT: worked / not working / next | `18_CHATGPT_NOTES.md` |
| 19 | Engineering RFIs | `19_RFIS.csv` |
| – | The ST7757 run through route G (the contractor-facing outputs) | `st7757_route_g/` (CSV, HTML, SVG, JSON committed; `STRUCTURAL_BOQ.xlsx`, `BOQ_REPORT.pdf` and `VISUAL_QA_OVERLAYS.pdf` regenerate with `15_WORKFLOW.md` §5) |
| – | Typical-detail evidence from the PDF (p.13) | `evidence/DETAIL_EVIDENCE.json` (crops not committed) |
| – | Project profile (printed values with provenance) | `profile_st7757_m3.json` |

## Scripts

| Script | What it does |
|---|---|
| `build_m3_reports.py` | Writes files 00 and 02–14 from live runs: the M2 engine in its own process from a worktree at its commit, and the current engine. It refuses to write anything that carries owner text, Arabic source text, a file path or a firewalled benchmark number. |
| `st7757_snapshot.py` | One engine's view of the ST7757 drawing as plain JSON (counts, family totals, item ids). |
| `evaluate_heldout.py` | Generates and scores the held-out synthetic sets for either engine. |

## Inputs this package used

- The private ST7757 structural DXF and the PDF set (`data/inputs`, git-ignored).
- `profile_st7757_m3.json`, with 11 typed project values.
- `engine/profiles/URBAN_M3_GENERIC_CONVENTIONS_V2.json`.
- `evidence/DETAIL_EVIDENCE.json`.
- The frozen M1 registers, for comparison only.

## Categories

| Category | Meaning |
|---|---|
| **Verified** | Never on a new project. |
| **Provisional** | low / base / high with its blocker. |
| **Unresolved** | An exposure, never in a total. |
| **Not detected** | A family coverage state. |

## What is not changed

- Frozen S1–S9A stages, M1 and the M2 evidence (`research/urban_engine_m2_generalization`, pinned by sha256) are untouched.
- No original drawing was modified.
