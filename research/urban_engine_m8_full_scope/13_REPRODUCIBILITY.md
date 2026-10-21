# 13 Reproducibility

Run every command from the repository root. Use `python3 -I` for anything that reads data.

## Engine and conventions

| Item | Value |
|---|---|
| Engine freeze | `00_ENGINE_FREEZE.json` (commit `9d7aceb`): every frozen file's sha256 and its git blob at that commit |
| Post-freeze fixes | `engine/source/scope_quantities.py` (P1, P2, P4) and `tools/m7_metamorphic.py` (P3); `tests/m8_full_scope/test_m8_package.py` checks that nothing else changed |
| Conventions | `engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json` (V6). V5 stays the default of `tools/urban_project_run.py`; the CLI default stays V3 |

**Running a project with V6:**

```
python3 -I tools/urban_boq_m2.py run --drawings STRUCTURAL.dxf --route G \
    --conventions engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json --out OUT/ [--profile P.json] [--arch ARCH.dxf]
```

**Outputs added by V6 (on top of the M7 outputs):**
- `SCOPE_BOUNDS.csv`
- `SCOPE_TOTALS.json`
- the `SCOPE_*` columns of `COMPLETENESS_FINDINGS.csv`
- BOQ section F in `CONTRACTOR_BOQ.csv`
- family coverage state `BOUNDED_NOT_MEASURED`

## Records

| Record | Command | Notes |
|---|---|---|
| `heldout/` | `python3 -I research/urban_engine_m8_full_scope/heldout_run.py run` | Run once on the frozen engine. It refuses a second run and refuses a changed engine |
| `heldout_postfix/` | `python3 -I research/urban_engine_m8_full_scope/postfix_run.py` | The same S_A / S_B / P runs with P1–P4 |
| `st7757/` | `python3 -I research/urban_engine_m8_full_scope/st7757_run.py [--cache DIR]` | Needs the private drawings in `data/inputs/by_sha256/`. About 10 minutes with the ablation (`--no-ablation` skips it) |
| CSV deliverables (`02`, `05`, `06`, `06A`, `11`) | `python3 -I research/urban_engine_m8_full_scope/build_package.py` | Rebuilt from the records. `test_m8_package.py` checks that they rebuild byte for byte |
| Workbook (not committed) | `python3 -I research/urban_engine_m8_full_scope/build_package.py --xlsx OUT.xlsx` | |
| Visual QA PDF (not committed) | `python3 -I research/urban_engine_m8_full_scope/build_visuals.py OUT.pdf` | Synthetic geometry only. ST7757 appears as numbers; positions appear as differences |

## Synthetic villas

**Generate one villa:**

```
python3 -I tools/synthetic_villa_m8.py OUT_DIR SEED [--heldout-vocabulary] [--hard]
```

**Score a set of seeds:**

```
python3 -I tools/m8_evaluate.py OUT.json SEED ... [--heldout-vocabulary] [--hard]
```

**Seeds used:**
- Development: 1–90.
- Held-out: 401–440, generated for the first time by `heldout_run.py` after the freeze.
- The M7 held-out seeds 301–340 were re-run under V6 only to show that no M7 row moved.

## Tests

**M8 tests:**

```
python3 -m pytest -q tests/m8_full_scope
```

- `test_m8_scope.py`: 27 cases.
- `test_m8_package.py`.

**Full suite:** see `TEST_GATE_M8.json`. It records:
- the command;
- the counts;
- the classification of every failure (code / environment / data).
