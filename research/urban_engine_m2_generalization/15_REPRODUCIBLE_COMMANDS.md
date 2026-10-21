# Reproducible commands

All commands run from the repository root with Python 3.11+ and `ezdxf` installed. Chromium is needed for the PDFs only; pass `--no-pdf` without it.

## Run the BOQ on a new villa (route G)

```bash
python3 -I tools/urban_boq_m2.py run --drawings NEW_STRUCTURAL.dxf --out OUT
# optional: printed values the drawing lacks (storey heights, typical ground-beam classes)
python3 -I tools/urban_boq_m2.py run --drawings NEW.dxf --profile my_profile.json --out OUT
# change one assumption (re-uses the detection; with --cache the drawing is not re-read either)
python3 -I tools/urban_boq_m2.py run --drawings NEW.dxf --out OUT2 --set BEAM_DEPTH_READING=BELOW_SLAB --cache .cache
```

**Outputs in OUT**
- `STRUCTURAL_BOQ.xlsx` and `BOQ_REPORT.pdf`;
- `VISUAL_QA_OVERLAYS.pdf` and `overlays/*.svg`;
- `CONTRACTOR_BOQ.csv`, with sections A concrete, B reinforcement by diameter and C not detected;
- `PROVISIONAL_REGISTER.csv`, `UNRESOLVED_REGISTER.csv`, `COVERAGE_RISK.csv` and `REBAR_COMPLETENESS.csv`;
- `ASSUMPTIONS.csv`, `SENSITIVITY.csv`, `EXCEPTIONS.csv`, `FAMILY_SUMMARY.csv`, `FLOOR_SUMMARY.csv` and `STEEL_BY_DIAMETER.csv`;
- `SUMMARY.json` and `run_log.json` (step timings).

A profile is a convention list in the same format as `research/urban_engine_m2_generalization/profile_st7757.json`, for example `STOREY_HEIGHT_GF` = 4.5 with `provenance` PRINTED_VALUE.

**Route selection**
- `--route A`: the frozen Alsenan replay (unchanged M1).
- `--route B`: an M1 takeoff profile.
- `--route C`: inventory only.
- `--route G`: the generic route forced on any set.
- Default `auto`: A for a known set without a profile, B with a takeoff profile, G otherwise.

## Reproduce the M2 evidence

```bash
# synthetic evaluation (truth from the design); seeds are the held-out sets of 11_GENERIC_TEST_RESULTS.md
python3 -I tools/m2_evaluate.py OUT.json 401 402 403 404 405 406 407 408 409 410 411 412 413 414 415 416 417 418 419 420
python3 -I tools/m2_evaluate.py OUT.json 401 ... 420 --defects
python3 -I tools/m2_evaluate.py OUT.json 401 ... 420 --hard-defects
# one synthetic drawing with its truth and profile
python3 -I tools/synthetic_villa.py OUT_DIR 7 --defects
# Alsenan through route G, and the comparison / audit package (needs the private ST7757 drawing under data/inputs)
python3 -I tools/urban_boq_m2.py run --drawings data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf \
        --profile research/urban_engine_m2_generalization/profile_st7757.json --route G \
        --out research/urban_engine_m2_generalization/alsenan_route_g --as-of 2026-10-10
python3 -I research/urban_engine_m2_generalization/build_m2_reports.py
# tests
python3 -m pytest -q tests/m2_generic_engine
python3 -m pytest -q tests/m1_usable_boq tests/structural_comparison_engine tests/r8_0
```

## Windows

**Running the commands**
- Use `py -3.11` in place of `python3`. Paths may use `\` or `/`.
- Install the dependency with `py -3.11 -m pip install ezdxf`.
- For the PDFs, install Chromium through Playwright (`py -m pip install playwright` then `py -m playwright install chromium`) and point `tools/urban_structural_boq.CHROMIUM` at it, or pass `--no-pdf`.

**Converting a DWG**
- DWG is refused: the engine never claims native DWG support.
- Convert it to DXF first with the ODA File Converter (free, offline) or by `SAVEAS` from AutoCAD / BricsCAD. Record the converter and version.

## Claude Code users

- The repository's checks are the commands above. Always run Python with `-I` on downloaded drawings.
- Keep drawings under `data/inputs/` (git-ignored); outputs are written where `--out` points.
- **Never commit:** `.xlsx` files, review PDFs or client drawings. The package `.gitignore` already excludes the generated PDFs and workbooks.
- If you work through an AutoCAD MCP, keep it read-only (export DXF only). Never run downloaded LISP or scripts.
