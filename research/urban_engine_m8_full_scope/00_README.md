# M8 — Full-scope generic structural BOQ: every drawn family measured or bounded

**M7 asked** whether a quantity, once the takeoff holds it, can be trusted.

**M8 asks** the question a freelance QS answers on every job: *is every structural element that the drawing shows
priced, and when a dimension is not printed, what assumption prices it, and with what range?*

**The rules of the work** are unchanged from M7:
- the work changed the engine, not the project;
- every rule is a statement about drawings in general;
- every rule is a named convention in a new set (V6), so V5 and the frozen M2–M7 packages still reproduce;
- the evidence that the rules generalise is a held-out synthetic set generated only after the engine was frozen.

**The brief**, written before any work: `00_M8_BRIEF.md`.

| | |
|---|---|
| Conventions | `engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json`: 103 conventions, V5's 66 + 37 M8 rules. Opt-in on the CLI (`--conventions`). V5 stays the default of `tools/urban_project_run.py`; the CLI default stays V3 |
| New engine module | `engine/source/scope_quantities.py`, the scope pass. Each completeness finding becomes measured items (when the family is settled), or a bound with a stated range, or a recorded reason to add nothing |
| Changed engine modules | `generic_route` (stairs measured from the drawn run, the partial-run path, printed notes), `concrete_completeness` (group ids kept, a per-face stair-zone check), `slab_engine` (tread directions wrapped at 180°), `family_coverage` (state BOUNDED_NOT_MEASURED). Every change is gated by a V6 convention |
| Changed tools | `tools/urban_boq_m2.py` (the scope pass in route G; BOQ section F; `SCOPE_BOUNDS.csv`, `SCOPE_TOTALS.json`), `tools/m7_metamorphic.py` (`--completeness`: properties on the bounded totals) |
| New tools | `tools/synthetic_villa_m8.py` (a villa with hidden design truth for every scope element, printed in about half), `tools/m8_evaluate.py` (records matched to elements, scored per element and per villa) |
| Tests | `tests/m8_full_scope/`: `test_m8_scope.py` (27 cases from 18 tests) and `test_m8_package.py` (9) |

## How it was built (each step frozen before the next read anything new)

| Step | What | Record |
|---|---|---|
| 1 | Brief and baseline: what route G with V5 leaves unmeasured on ST7757 and on synthetic villas | `00_M8_BRIEF.md` |
| 2 | Stairs: multi-flight decomposition, partial runs, winders, riser rule, printed notes | `03_SCOPE_RULES.md` §3 |
| 3 | Box structures (pool, pit, tank, lift), domes, the boundary wall; parapets and referenced families as allowances | `03_SCOPE_RULES.md` §2–§3 |
| 4 | Bounds for every other finding, the missing-storey bracket, BOQ section F | `03_SCOPE_RULES.md` §4 |
| 5 | Synthetic generator and evaluator, development seeds 1–90 | `tools/synthetic_villa_m8.py`, `tools/m8_evaluate.py` |
| 6 | Engine freeze `9d7aceb` (`00_ENGINE_FREEZE.json`, committed in `a772be1` before any held-out seed existed) | `00_ENGINE_FREEZE.json` |
| 7 | Held-out seeds 401–440, generated for the first time and run once (two vocabularies), plus the M7 held-out rows under V6 and the metamorphic properties | `heldout/`, `04_HELDOUT_VALIDATION.md`, `06A_ACCEPTANCE_FROZEN.csv` |
| 8 | Post-freeze fixes P1–P4, re-run apart | `heldout_postfix/`, `06_ACCEPTANCE.csv`, `10_PROPERTIES_AND_REGRESSION.md` |
| 9 | ST7757 V5 → V6 with ablation. Post-discovery, not blind | `st7757/`, `07_ST7757_BEFORE_AFTER.md`, `09_ABLATION.md` |
| 10 | Positions: the stage record, the freelance QS, the two MCP runs. Read after the freeze, written as differences only | `st7757/POSITIONS.csv`, `08_ST7757_POSITIONS.md` |
| 11 | Package, workbook, visual QA, full suite | this folder, `TEST_GATE_M8.json` |

## Files

| File | |
|---|---|
| `00_M8_BRIEF.md` | the milestone brief (goal, principles, work packages, acceptance, what M8 cannot do) |
| `00_ENGINE_FREEZE.json` | the freeze: commit, sha256 and git blob of every engine file |
| `01_EXECUTIVE_REPORT.md` | results against the acceptance, the verdict, the honest answer to the goal |
| `02_CONVENTIONS_V6.csv` | the 37 M8 conventions: value range, unit, rationale |
| `03_SCOPE_RULES.md` | every scope rule: when a family is settled, how each element is measured, how each finding is bounded |
| `04_HELDOUT_VALIDATION.md` | the held-out protocol and results per element kind and per villa |
| `05_HELDOUT_BY_ELEMENT.csv` | every held-out element: truth, engine low / base / high, outcome |
| `06_ACCEPTANCE.csv`, `06A_ACCEPTANCE_FROZEN.csv` | acceptance per run and kind: post-freeze and frozen |
| `07_ST7757_BEFORE_AFTER.md` | ST7757 V5 → V6 by family; the scope pass; the bounded total in parts |
| `08_ST7757_POSITIONS.md` | ST7757 against the four positions, as differences and in-range flags |
| `09_ABLATION.md` | each M8 convention alone on ST7757 |
| `10_PROPERTIES_AND_REGRESSION.md` | V5 and frozen packages unchanged; metamorphic properties; post-freeze fixes |
| `11_WEAKNESS_REGISTER.csv` | W8-01 … W8-13: what is still wrong or weak, and the next step for each |
| `12_QUOTATION_STATUS.md` | the verdict (not quotation-ready), what M8 changes, the wording to use |
| `13_REPRODUCIBILITY.md` | commands, records, seeds |
| `15_CHATGPT_HANDOFF.md` | what worked, what did not, what to do next |
| `TEST_GATE_M8.json` | the full-suite run, classified (gate INCOMPLETE) |
| `heldout/`, `heldout_postfix/`, `st7757/` | the records (sha256 lists inside their summaries) |
| `build_package.py`, `build_visuals.py` | rebuild the CSV deliverables, the workbook and the visual QA PDF from the records. The workbook and PDF are not in git |
| `heldout_run.py`, `postfix_run.py`, `st7757_run.py` | the runs that made the records |

**External records.** The freelance QS and MCP figures were not opened during the development of M8. They were read
by `st7757_run.py` only after the freeze, from the M5 record, and appear only as differences. No reference quantity
is in any engine file or convention.

**ST7757 identity.** The private drawings are referred to by sha256 only. No client drawing is rendered: the visual
QA shows synthetic geometry.
