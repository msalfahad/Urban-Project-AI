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
| Excel renderer (engine values locked, report / check formulas only, protected, print-ready, deterministic bytes) | `engine/reporting_v2/xlsx.py` | no |
| PDF renderer (HTML → Chromium, same sections, pinned metadata) | `engine/reporting_v2/pdf.py` | no |
| XLSX readback validation, LibreOffice recalculation, what-if check | `engine/reporting_v2/readback.py` | no |
| QS reconciliation sheet (08) | `engine/reporting_v2/layout.py` `reconciliation_sheet()` + adapter structural blocks | no / register family |
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

No engine quantity is ever an Excel formula. Values are stored at full engine precision, and only the number format
rounds them. Formulas exist only where §9 allows them.

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
| 7 | 08_QS_RECONCILIATION: QS manual check against the Urban values (§9) | RECON (not additive) |
| 8 | TECH_* appendix: column / beam occurrences, slab regions, opening evidence, value pointers, QA, input digests | TECH (not additive) |

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
| `readback.validate()` | Sheet order; every formula is one the model holds, with the exact text; every written value cell equals the model; quantity, blocked, formula and input cell counts equal the model's; every sheet protected; engine cells locked; only input cells unlocked. |
| `readback.recalc()` | LibreOffice Calc (headless) recalculates the workbook: every formula value equals the model's evaluated value; no error cell. |
| `readback.whatif()` | Manual values typed into a copy (item rows at +0.1 / +2 / +20 %, a blocked row, a text value, the Urban length / height / area in every structural check): every recalculated formula equals the Python evaluation, the expected statuses hold, engine quantities and 00 totals are unchanged. |
| PDF text check | Section titles appear in order; every line id and its formatted quantity appears. |
| Regression | Every shown quantity equals the frozen register value. The register trees and `engine/source` are unchanged since the registers commit. Qortuba: all canonical items unchanged. Cross-checks hold: storey totals, footing / strap subtotals, A3 floor-area subtotals, column `by_storey`. |
| `REPORTING_V2_FREEZE.json` | Input register digests (= the model's sources), model content digests, output digests. |

## 9. Formulas and the QS reconciliation sheet (addendum)

**Formula policy.** No formula creates or replaces an Urban engine quantity. A formula cell is a structured spec in the
model (`{"f": {"op", "args"}, "v", "expect"}`); the renderer writes the Excel text, `model.evaluate()` computes the same
value in Python, and every report total carries the deterministic value (exact decimal sum) it must equal.

| Formula | Where |
|---|---|
| `SUM` over frozen line totals | 00 MAIN TOTALS BY TRADE |
| `SUM` over frozen per-level line cells; TOTAL PROJECT = `SUM` of floors | 00 TOTALS BY FLOOR |
| `COUNTIFS` / share | 00 coverage, 08 check progress |
| `SUM` / `SUMNB` (blank while nothing is typed) | 08 subtotals and project totals |
| `PROD` (`COUNT x L x W x H`, `L x B x (D - t) / 10000`, `COUNT x B x D x H / 10000`, `area x t / 100`) | 08 structural manual checks |
| `DIFF` = `ROUND(manual - Urban, 9)`, `PCT` = `ROUND((manual - Urban) / Urban, 9)`, `RSTATUS` | 08 every row |

PROJECT BOQ LINES line totals stay frozen values: the line total is the canonical QTO line.

**08_QS_RECONCILIATION** (after 07, before TECH_):

- CHECK SETTINGS / LEGEND: editable MATCH / CLOSE tolerances (0.5 % / 3 %), colour key, status rules, the boundary
  (nothing typed flows back).
- CHECK PROGRESS BY FLOOR: item rows, checked, and counts per reconciliation status.
- ITEM RECONCILIATION - BY FLOOR: one row per line share. Floor blocks (adapter-defined; Alsenan: FOUNDATION / GF / 1F
  / SECOND FLOOR + ROOF / EXTERNAL + OTHER) are separated by thick borders. Inside a block the items of one group are
  contiguous and close with a SUBTOTAL; ALT ITEM rows (alternative measures) are listed but never added; the PROJECT
  block adds the groups over all floors. The table has an AutoFilter (row type, floor, trade, status, room, unit,
  reconciliation status).
- ARCHITECTURAL RECONCILIATION: one row per architectural item group (floor area, ceiling, skirting, blockwork,
  plaster, paint, floor tile, wall tile, waterproofing, aluminium / glazing; marble / hidden profile shown as NOT
  MEASURED when no register exists).
- Adapter structural blocks (Alsenan): FOOTINGS (count + L / W / H pre-filled from the schedule and plan tags),
  BEAMS (B / D / slab t pre-filled; clear length typed), COLUMNS (count / B / D pre-filled; clear height typed),
  SLABS (thickness pre-filled; net area typed), each with floor subtotals and a TOTAL.

| Reconciliation status | Rule |
|---|---|
| ENGINE BLOCKED | Urban quantity BLOCKED - never a mismatch, no difference, no % |
| NOT COMPARABLE | no Urban quantity on this basis (not measured / not on plan), or a non-numeric check |
| NOT CHECKED | no manual value yet |
| MATCH / CLOSE / REVIEW | \|manual / Urban - 1\| within MATCH tol / within CLOSE tol / beyond (Urban = 0: MATCH only if manual = 0) |

Colours: white / grey = engine (locked) · light yellow = input (unlocked) · light blue = formula · green / amber / red
= MATCH / CLOSE / REVIEW (conditional formatting) · grey = ENGINE BLOCKED / NOT CHECKED / NOT COMPARABLE. Every sheet
is protected without a password. The workbook asks Excel to recalculate on open (openpyxl writes no cached formula
values); the PDF prints the evaluated values, which the LibreOffice check proves equal to the computed ones.
