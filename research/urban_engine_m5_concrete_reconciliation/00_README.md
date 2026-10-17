# M5: quotation-critical concrete reconciliation and independent quantity audit (ST7757)

Planning reconciliation, not engineering approval. The gate stays INCOMPLETE.

- **Phase:** RECONCILIATION. The Urban engine is frozen at M4 `35c0587`; candidate hash `2e4a6ec6fa4e6e35c87efb7f`.
- **External figures:** read from their records at build time. They never reach the engine and no quantity was tuned to them.
- **Freelancer source:** the original workbook is not in this environment. The hash-pinned S3.1 lineage, which traced every leaf row from the workbook's formulas, is used and cited as DERIVED (02A).
- **MCP sources:**
  - U-C4N is held at category level only;
  - christiannp has report-explicit per-floor and per-stage values;
  - neither sealed report is in the repository (02A records where they were expected).

**Rebuild** (the private drawings in `data/inputs/by_sha256/`):

```
python3 -I research/urban_engine_m5_concrete_reconciliation/build_m5_package.py --cache CACHE_DIR
```

**Paths:** `{P}` in printed paths stands for the project folder prefix of the stage folders (not reproduced).

| File | What it holds |
|---|---|
| 00_NUMBERS.json | Every headline number, the freeze block, the check count |
| 01_EXECUTIVE_CONCRETE_RECONCILIATION.md | Findings, what changed, the questions, the recommendation |
| 02_SOURCE_SCOPE_MATRIX.csv | Scope item x source: quantity and measurement basis |
| 02A_SOURCE_INVENTORY.csv | Every file read, sha256, recorded-hash check; missing sources with location |
| 02B_FOUR_SOURCE_BASELINE.csv | The four totals reproduced from their records |
| 02C_FAMILY_TOTALS.csv | Family totals of the four sources and of the Urban reference |
| 03_ELEMENT_BY_ELEMENT_COMPARISON.csv | One row per element group (family, floor, mark): four sources, class, cost, location, treatment |
| 03A_ELEMENT_MEMBERSHIP.csv | Every freelancer row and Urban item, with its group and state (nothing dropped) |
| 04_FREELANCER_VS_URBAN_BRIDGE.csv | Ordered causes from the freelancer RC to the Urban measured base |
| 05_GROUND_BEAM_AND_SLAB_AUDIT.md | + 05A (cells), 05B (beam classes) |
| 06_SUSPENDED_SLAB_AUDIT.md | + 06A (panels), 06B (floors) |
| 07_FOUNDATIONS_COLUMNS_BEAMS_AUDIT.md | + 07A (mark crosswalk), 07B (frame per floor) |
| 08_STAIRS_DOMES_POOL_AUDIT.md | Stairs, domes, pool, lift and specials |
| 09_BLINDING_CONCRETE_AUDIT.md | + 09A (blinding options); plain concrete only |
| 10_MISSING_CONCRETE_REGISTER.csv | Missing in Urban's base or in the freelancer's, located |
| 11_DOUBLE_COUNT_REGISTER.csv | + 11A (the M5 ownership decisions) |
| 12_QUOTATION_COST_EXPOSURE.xlsx | Generated, git-ignored; CSV twins 12 / 12A committed |
| 13_PRIORITY_RFIS.csv | The minimum questions, ranked by KWD swing |
| 14_VISUAL_CONCRETE_QA.pdf | Generated, git-ignored; the HTML and the SVGs (visual/) are committed |
| 15_INDEPENDENT_VALIDATION.md | + 15A (the checks) |
| 16_TEST_RESULTS.md | Tests on this commit |
| 17_CHATGPT_HANDOFF.md | What worked, what did not, what to do next |
| 18_ENGINE_CHANGE_V3_TO_V4.csv | Before / after of the Phase 8 engine fix |
| M5_CONCRETE_RECONCILIATION_WORKBOOK.xlsx | Consolidated workbook (generated, git-ignored) |

