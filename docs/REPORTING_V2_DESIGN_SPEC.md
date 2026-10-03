# Urban QTO — Reporting Layer V2 — design spec

Reporting V2 is a **presentation layer**. It reads frozen engine registers and lays them out as a professional QS
report (Excel + PDF). It measures nothing, changes no engine, quantity, status, authority, owner fact, method,
blocker or release state, and never writes to a register.

## 1. Architecture

| Part | Where | Project-specific? |
|---|---|---|
| Presentation model, row classes, status aliases, declared sums, validation | `engine/reporting_v2/model.py` | no |
| Standard assembly (00_TOTAL_SUMMARY + adapter sheets) | `engine/reporting_v2/layout.py` | no |
| Bilingual glossary + user-facing explanation of technical codes | `engine/reporting_v2/terms.py` | no |
| Excel renderer (no formulas, print-ready, deterministic bytes) | `engine/reporting_v2/xlsx.py` | no |
| PDF renderer (HTML → Chromium, same sections, pinned metadata) | `engine/reporting_v2/pdf.py` | no |
| XLSX readback validation | `engine/reporting_v2/readback.py` | no |
| Alsenan adapter (A3 + B2A.1 register schemas) | `research/external_engine_lab/reporting_v2_alsenan.py` | register family |
| Qortuba adapter (RC1 register schemas) | `research/external_engine_lab/reporting_v2_qortuba.py` | register family |
| Build, regression, readback QA, freeze, package | `research/external_engine_lab/reporting_v2_build.py` | no |

`engine/reporting_v2` sits outside `engine/source` (it uses openpyxl, like `engine/boq_rc1_xlsx.py`) and imports no
QTO engine. A test enforces this.

## 2. Quantity cells — the no-recompute guarantee

Each quantity cell in the model is one of the following:

| Form | Meaning |
|---|---|
| `{"q": v, "src": "REGISTER:/json/pointer"}` | Copied from a frozen register. Re-resolved by `validate()`; the shown value must be identical. |
| `{"q": v, "sum": [src, ...]}` | **DECLARED_SUM**: an exact decimal sum of register values of one trade and unit. Every addend is recorded. This is the only arithmetic allowed. |
| `{"q": None, "blocked": code}` | No quantity. Written as **BLOCKED**, never as 0. |
| `{"q": None, "na": text}` | Not applicable, or not published by any register. |

There are no Excel formulas; the readback refuses any formula cell. Values are stored at full engine precision, and
only the number format rounds them.

## 3. Row classes — the no-double-count guarantee

| Class | Meaning |
|---|---|
| ADDITIVE | One canonical line per physical item. Appears on **00_TOTAL_SUMMARY only**. |
| BREAKDOWN_ONLY | Explains an ADDITIVE line (`explains: LINE@LEVEL`). Never added again. |
| ALTERNATIVE_MEASURE | The same item on another basis or unit (e.g. Qortuba WIN-02 area vs WIN-01 count, curved MID / MAX arcs). |
| TRACE_ONLY | Evidence, QA or counts. Nothing to add. |
| SUBTOTAL / TOTAL | A declared sum of ADDITIVE lines of one group and unit. Blocked lines are excluded. |

Trade totals add only the lines of one **group**: one kind of item in one unit. Floor area and ceiling area are never
added together. The totals-by-floor matrix adds the same lines by level, and its TOTAL PROJECT row equals the line
totals.

## 4. Status

Each row keeps its **technical code** as written in the register. The display state is an alias:

- COMPUTED (green)
- PARTIAL / REVIEW (amber)
- BLOCKED (red)
- INFO (grey)

The full alias table is printed on 07_METHODS_TRACEABILITY. An unknown code fails the build. User-facing reason,
effect and need are generic explanations of the code (`terms.EXPLAIN`). Priority is a reporting rule:

- structure / foundation → HIGH
- rooms / openings / finishes → MEDIUM
- information → LOW

## 5. Sheets (same order in Excel and PDF)

| # | Sheet | Role |
|---|---|---|
| 1 | 00_TOTAL_SUMMARY: project header, MAIN TOTALS BY TRADE, TOTALS BY FLOOR, coverage (line counts by status), key notes, PROJECT BOQ LINES | SUMMARY (only additive sheet) |
| 2 | 01_GROUND_FLOOR · 02_FIRST_FLOOR · 03_ROOF_SECOND_FLOOR. Same six sections each: KPI, rooms, structure (+ beams / columns by type), openings, masonry & finishes, notes / blockers. Roof adds ROOF WATERPROOFING. | BREAKDOWN |
| 3 | 04_FOUNDATION_SUBSTRUCTURE: footing types, straps, other substructure (computed or blocked with reason) | BREAKDOWN |
| 4 | 05_OPENINGS_ALUMINIUM: all-floor schedule by function; curved bases (MIN / MID / MAX / CHORD, selected basis) | SCHEDULE |
| 5 | 06_BLOCKERS_OWNER_QUESTIONS | INFO |
| 6 | 07_METHODS_TRACEABILITY: methods, owner facts, sources, run, status alias, classes | INFO |
| 7 | TECH_* appendix: column / beam occurrences, slab regions, opening evidence, value pointers, QA, input digests | TECH (not additive) |

Every breakdown sheet carries the note "Project totals: use 00_TOTAL_SUMMARY only." in row 5 and in its print header.

## 6. Bilingual

Arabic text is taken from these sources, in order:

1. The register's own Arabic (Alsenan ARCH_BOQ `ar`, Qortuba CANONICAL_BOQ `description_ar`).
2. The glossary (`terms.py`). Each entry records its source: BRIEF / REGISTER / REPO / LABEL.
3. Otherwise empty. Nothing is machine-invented.

Excel Arabic cells are right-aligned with RTL reading order. The PDF uses Cairo (bundled, OFL), shaped by Chromium.

## 7. Print

- Excel: landscape. A4 when the sheet grid is narrow, A3 otherwise. Fit to width, title rows 1–5 repeated on every
  page, section page breaks when a section fits on a fresh page, footer "project — phase | Page X of Y | Urban
  Projects".
- PDF: A4 landscape, a new page per sheet, table headers repeated on page breaks, the same footer.

## 8. QA and freeze

| Check | What it proves |
|---|---|
| `model.validate()` | Every pointer resolves to the shown value; declared sums match their addends; class / role / status / unit vocabularies hold; ADDITIVE only on the summary; every line on the summary; blocked ≠ 0. |
| `readback.validate()` | Sheet order; zero formulas; every written value cell equals the model; quantity and blocked cell counts equal the model's. |
| PDF text check | Section titles appear in order; every line id and its formatted quantity appears. |
| Regression | Every shown quantity equals the frozen register value. The register trees and `engine/source` are unchanged since the registers commit. Qortuba: all canonical items unchanged. Cross-checks hold: storey totals, footing / strap subtotals, A3 floor-area subtotals, column `by_storey`. |
| `REPORTING_V2_FREEZE.json` | Input register digests (= the model's sources), model content digests, output digests. |
