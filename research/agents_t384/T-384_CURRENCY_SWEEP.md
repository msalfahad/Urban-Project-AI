# T-384 privacy fix: currency figures in the PUBLIC repository

Trigger: Checker observation O-T380-1 (T-380 Gate A). Rule: CLAUDE.md (main) private-data section; workers quote a
freelancer QUANTITY only, never a rate or an amount. No figure is repeated in this report.

## 1. Removed (forward only, no history rewrite)

| File:line | What was there | Action |
|---|---|---|
| `research/agents_t380/T-380_DRAINAGE_SOURCE_CENSUS.md:100` | unit rate of the 'شاور' row (qty 11) | rate removed; quantity 11 kept |
| `research/agents_t380/t380_alsenan.py:143` | same rate in the `FREELANCER_SHOWER` comment | comment only; value 11 unchanged; t380 tests pass unchanged |

Source correction: the 'شاور' row with quantity 11 is row WEB-018 of Urban's own web-app 'cost by category' export
(`tests/alsenan/registers_b1/WEB_APP_ROWS.json`), not a cell of a freelancer workbook. The freelancer workbooks'
unit-price columns ('سعر الوحدة') hold no figures and their amount cells are 0.0 in `FREELANCER_RAW_ROWS.json` (checked
cell by cell: FIN, BLK, PNT, RC, ALU, PLS cover / invoice sheets). The rate was still private commercial content and
added nothing to the quantity reasoning, so removing it stands.

## 2. Sweep (research/, tests/, docs/; 288 lines in 29 files at the T-384 commit)

Scanner: `research/agents_t384/currency_guard.py` (a number directly before / after KWD, KD, K.D., fils or the Arabic
dinar / fils words and abbreviation, or a number on a key ending _kwd / _kd / _fils; case-sensitive so identifiers
such as `kd3` are not hits). A second, wider search for 'freelancer / his ... rate / price' followed by a number found
only quantities ('the freelancer prices X m3' means he measures X). Result: **no freelancer rate or amount remains**.

| File | Lines | Class | Origin | Action |
|---|---|---|---|---|
| `docs/ARCHITECTURE.md` | 12, 75 | OWNER | owner budget / audit totals from the Urban web-app cost export | kept |
| `docs/ENGINEERING_INVARIANTS.md` | 2660 | OWNER | owner's commercial rate on one quotation (development project 2) | kept |
| `docs/ONBOARDING.md` | 47 | OWNER | audit total on the owner's budget | kept |
| `docs/P7757_WALL_TREATMENT_ESTIMATE_01.md` | 1272 | OWNER | owner-supplied historical workbook of another project (not a freelancer workbook): a material total it omits | kept |
| `docs/PROJECT_2_ROUND6E_LINEAGE_STAIRS_AND_EXPORT.md` | 294 | OWNER | owner's commercial rate (development project 2) | kept |
| `research/agents_t162/CORNERS_R2_T162.csv` | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | OWNER | Urban cost PDF rate basis (OWNER_NOTES_SIGMA_2026-10-21) | kept |
| `research/agents_t162/T-162_SIGMA_RECONCILIATION.md` | 155, 200, 214 | OWNER | Urban cost PDF rate basis (owner notes) | kept |
| `research/agents_t162/check_t162.py` | 16, 170, 171 | OWNER | Urban cost PDF rate basis (owner notes) | kept |
| `research/agents_t162/t162_corners.py` | 5, 136, 137, 144, 151 | OWNER | Urban cost PDF rate basis (owner notes) | kept |
| `research/agents_t162/t162_r2.py` | 188 | OWNER | Urban cost PDF rate basis (owner notes) | kept |
| `research/agents_t172/T-172_CORNERS_PARAPETS.md` | 103 | OWNER | Urban cost PDF rate basis (owner notes) | kept |
| `research/external_engine_lab/alsenan_phase_b1_recommendation.json` | 15 | OWNER | Urban Projects' own web-app 'cost by category' export (owner's commercial document; quantities derived from the freelancer BOQ per tests/alsenan/registers_b1/BENCHMARK_DEPENDENCY.json, rates are Urban's own: the freelancer workbooks' unit-price columns are empty in FREELANCER_RAW_ROWS.json) | kept |
| `research/qs_wall_treatment_01/pa09/alrashed/historical_audit.py` | 457 | OWNER | same owner-supplied historical workbook (other project): defect L-05 amount | kept |
| `research/qs_wall_treatment_01/pa09/alrashed/validation_amendment.py` | 165 | OWNER | same owner-supplied historical workbook (other project): defect L-05 amount | kept |
| `research/urban_engine_m5_concrete_reconciliation/01_EXECUTIVE_CONCRETE_RECONCILIATION.md` | 3, 27, 29, 122, 124, 126, 128, 130, 214 | OWNER | concrete m3 x the owner brief's planning rate (reporting input, not a freelancer rate) | kept |
| `research/urban_engine_m5_concrete_reconciliation/06_SUSPENDED_SLAB_AUDIT.md` | 31 | OWNER | concrete m3 x the owner brief's planning rate (reporting input, not a freelancer rate) | kept |
| `research/urban_engine_m5_concrete_reconciliation/14_VISUAL_CONCRETE_QA.html` | 19 | OWNER | concrete m3 x the owner brief's planning rate (reporting input, not a freelancer rate) | kept |
| `research/urban_engine_m5_concrete_reconciliation/visual/08_TOP20_DISCREPANCIES.svg` | 1 | OWNER | concrete m3 x the owner brief's planning rate (reporting input, not a freelancer rate) | kept |
| `research/urban_engine_m7_reliability/00_README.md` | 33, 49 | OWNER | concrete m3 x the owner brief's planning rate (reporting input, not a freelancer rate) | kept |
| `research/urban_engine_m7_reliability/01_EXECUTIVE_REPORT.md` | 90, 91 | OWNER | concrete m3 x the owner brief's planning rate (reporting input, not a freelancer rate) | kept |
| `research/urban_engine_m7_reliability/11_QUOTATION_RISK.md` | 1, 9, 48, 49 | OWNER | concrete m3 x the owner brief's planning rate (reporting input, not a freelancer rate) | kept |
| `tests/alsenan/registers_b1/WEB_APP_ROWS.json` | 215 lines (15 .. 1890) | OWNER | Urban Projects' own web-app 'cost by category' export (owner's commercial document; quantities derived from the freelancer BOQ per tests/alsenan/registers_b1/BENCHMARK_DEPENDENCY.json, rates are Urban's own: the freelancer workbooks' unit-price columns are empty in FREELANCER_RAW_ROWS.json) | kept |
| `tests/alsenan/test_alsenan_b1_comparison.py` | 112 | OWNER | parser fixture string of one Urban web-app row | kept |
| `tests/test_campaign.py` | 102, 108, 121, 129 | PUBLIC | synthetic test fixture (campaign budget engine) | kept |
| `tests/test_campaign_cli.py` | 85, 86, 87, 150 | PUBLIC | synthetic test fixture (campaign budget engine) | kept |
| `tests/test_documents_cli.py` | 60, 78, 95 | PUBLIC | synthetic test fixture (contract document engine) | kept |
| `tests/test_documents_engine.py` | 26, 27 | PUBLIC | synthetic test fixture (dinar formatter) | kept |
| `tests/test_documents_render.py` | 21, 89, 97, 147 | PUBLIC | synthetic test fixture (contract document renderer) | kept |
| `tests/test_rate_library.py` | 54 | PUBLIC | synthetic parser input | kept |

Column-form amounts with no unit token on the line (`research/urban_engine_m5_concrete_reconciliation/04_*.csv`,
`10_*.csv`, `12A_*.csv`, KWD columns) are the same m3 x owner-brief-rate products as the M5 report: OWNER, kept.

## 3. Observations for the Lead / owner (not edited here; history is an owner item)

- O-T384-1: `tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json` keeps every non-empty freelancer workbook cell
  verbatim (885 rows), including the measurer's firm name in a cover-sheet title cell. These are quantities, not rates,
  but CLAUDE.md (main) forbids workbook contents in tracked files. B1 register that tests/alsenan reads: removal needs an owner decision.
- O-T384-2: `WEB_APP_ROWS.json` WEB-003 carries a labour subcontractor's personal name in its description, and the file
  keeps Urban's own unit rates for 88 rows. Owner data, so kept; the owner may want it out of a PUBLIC repository.
- O-T384-3: the historical workbook audit under `research/qs_wall_treatment_01/pa09/` and its docs summary carry one
  amount from an owner-supplied workbook of another project; classified OWNER, kept.

## 4. Guard

`tests/t384_currency_guard`: normal (quantity lines, identifiers, a rate unit without a figure) and adverse (figure
before / after every token, Arabic forms, currency keys; a new research file with a rate is refused; non-text files
ignored); the repository check refuses any research / tests / docs file with a currency figure that
`CURRENCY_BASELINE_T384.json` does not list with class OWNER or PUBLIC. A freelancer rate is never listed: it is removed.

Lessons-register proposal (ERS s.7): "Private commercial figures: a rate quoted for context is still workbook content;
quote quantities only. Guard: t384 currency scan. Scope: every villa, every research file."
