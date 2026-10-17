# Reproducible commands (M4)

Every command runs from the repository root.

The private drawings live in `data/inputs/by_sha256/` and are git-ignored:
- the structural DXF `9f9d1179…dxf`
- the architectural DXF `ab54dd55…dxf`

The detail evidence is the frozen M3 file `research/urban_engine_m3_recovery/evidence/DETAIL_EVIDENCE.json`.

## 1. Run the M4 pipeline on a drawing set (any villa)

```
python3 -I tools/urban_boq_m2.py run --route G \
    --drawings STRUCTURAL.dxf --arch ARCHITECTURAL.dxf \
    --profile PROFILE.json [--evidence DETAIL_EVIDENCE.json] [--evidence-review READINGS.json] \
    --out OUT_DIR [--cache CACHE_DIR] [--no-pdf] [--no-xlsx]
```

- **Conventions:** the default set is `engine/profiles/URBAN_M4_GENERIC_CONVENTIONS_V3.json`.
- **Profile:** holds the project's printed values only (storey heights, typical classes, levels, schedules).
- **Outputs:** the M1/M2 registers plus the M4 registers:
  - `MISSING_REINFORCEMENT_REGISTER.csv`, `MISSING_REINFORCEMENT_SUMMARY.csv`
  - `UNRESOLVED_CONCRETE_EXCEPTIONS.csv`
  - `CB_LINES.csv`, `CB_PHYSICAL_BARS.csv`
  - `ARCH_GB_EXTERIOR.csv`
  - `LINTEL_OPENINGS.csv`
  - `SLAB_FACES.csv`
  - `OCR_DERIVED_ITEMS.csv`, `OCR_REVIEW.csv`
  - `CONFLICTS.csv`
  - `overlays_m4/*.svg`, `M4_VISUAL_QA.html` (+ `.pdf`)
  - `STRUCTURAL_BOQ.xlsx`, with the M4 sheets added

ST7757:

```
python3 -I tools/urban_boq_m2.py run --route G \
    --drawings data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf \
    --arch data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf \
    --profile research/urban_engine_m4_correctness/profile_st7757_m4.json \
    --evidence research/urban_engine_m3_recovery/evidence/DETAIL_EVIDENCE.json \
    --evidence-review research/urban_engine_m4_correctness/evidence/OCR_INDEPENDENT_READINGS.json \
    --out OUT_DIR --cache CACHE_DIR
```

## 2. Build the M4 package

```
git worktree add M3_WORKTREE cbfa13e
python3 -I research/urban_engine_m4_correctness/build_m4_package.py --m3-root M3_WORKTREE \
    --heldout HELDOUT_OUT_DIR --visual VISUAL_DIR --crops CROPS_DIR --cache CACHE_DIR
```

- **M3 snapshot:** the M3 numbers come from the M3 commit, run in its own process. The frozen M3 package is never modified.
- **M3 per-component register:** a replay of the M3 conventions through the current engine. It is accepted only when its rebar-state counts equal the M3 commit's own.
- **`VISUAL_DIR`** receives the files that embed client drawing content and are never committed:
  - the OCR review sheet with its crops (`CROPS_DIR` = the p.13 crops of the M3 PDF evidence run)
  - the visual QA PDF
  - the Excel BOQ

## 3. Held-out evaluation (new seeds 601–640)

```
python3 -I research/urban_engine_m4_correctness/evaluate_heldout_m4.py generate --drawings H/clean --seeds 601-640 --mode clean
python3 -I research/urban_engine_m4_correctness/evaluate_heldout_m4.py generate --drawings H/m4 --seeds 601-640 --mode m4
for s in clean m4; do
  python3 -I research/urban_engine_m4_correctness/evaluate_heldout_m4.py score --engine-root M3_WORKTREE --conventions V2 \
      --drawings H/$s --seeds 601-640 --out HELDOUT_OUT_DIR/${s}_M3.json
  python3 -I research/urban_engine_m4_correctness/evaluate_heldout_m4.py score --engine-root . --conventions V3 \
      --drawings H/$s --seeds 601-640 --out HELDOUT_OUT_DIR/${s}_M4.json
done
```

## 4. Tests

```
python3 -m pytest -q tests/m4_correctness                      # M4 unit, integration, package
python3 -m pytest -q tests/m2_generic_engine tests/m3_recovery tests/r8_1 tests/test_benchmark_protection.py \
    tests/structural_comparison_engine/test_rebar_product_firewall.py
python3 -m pytest -q                                           # full suite (13_TEST_RECORD.md)
```
