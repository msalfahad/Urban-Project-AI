# Reproduction commands

Run everything from a clone at commit `c757d8a`, with Python 3.11+ and `ezdxf`, and with `python3 -I`. Private drawings stay outside the repository; `PLAN.dxf` stands for a private plan.

## Phase 1 defect matrix (`12_DEFECT_MATRIX_BEFORE_AFTER.csv`)

The repro harnesses are in `scripts/phase1_repro/`, the same files as `research/urban_m9_s6/phase1/repro/`.

```
# synthetic variants through the production CLI (method and extra flags from the environment)
S6_METHOD=ARCH_TAKEOFF_V1                      python3 -I scripts/phase1_repro/s6_repro_v.py      REPO OUT_DIR
S6_METHOD=ARCH_TAKEOFF_V1 S6_EXTRA=--strict-admission python3 -I scripts/phase1_repro/s6_repro_v.py REPO OUT_DIR
S6_METHOD=ARCH_TAKEOFF_V2                      python3 -I scripts/phase1_repro/s6_repro_v.py      REPO OUT_DIR
# DWG cases with a fake converter (FAKEBIN: a directory holding a fake dwg2dxf)
S6_METHOD=ARCH_TAKEOFF_V2 python3 -I scripts/phase1_repro/s6_repro_dwg_v.py REPO OUT_DIR FAKEBIN
# finish cases (the band above tile, the stair hall, strips, diacritics): V1 and V2
python3 -I scripts/phase1_repro/s6_repro_arch_v.py REPO OUT_DIR
# metamorphic variants of a private plan (base, metres, nested2, frames_exploded): counts only
S6_METHOD=ARCH_TAKEOFF_V2 python3 -I scripts/phase1_repro/s6_real_variants_v.py REPO PLAN.dxf WORK_DIR
# V1 lines unchanged in V2, and what V2 adds
python3 -I scripts/phase1_repro/v1_v2_compare.py V1_OUT V2_OUT [JSON]
```

To rebuild the matrix from those outputs:

```
python3 -I scripts/phase1_repro/build_matrix.py S6P1_DIR REVIEW_CSV OUT_CSV
```

- `S6P1_DIR` holds the sweep outputs.
- `REVIEW_CSV` is the S6 review register, `phase1_notes/S6_01_DEFECT_REPRODUCTIONS_PUBLIC.csv`.

The area reconciliation:

```
python3 -I scripts/phase1_repro/area_reconciliation.py V1_OUT V2_OUT OUT_JSON
```

## Investigation A (float boundary)

```
git archive c757d8a engine tools rules | tar -x -C WORK/src && ln -s "$REPO/data" WORK/src/data
python3 -I fixtures_investigation_A/make_fixtures.py OUT/dxf
python3 -I fixtures_investigation_A/eval_fixtures.py WORK/src OUT/dxf OUT/A_FIXTURE_RESULTS.json
python3 -I fixtures_investigation_A/a_method_comparison.py 2000 OUT/A_METHOD_COMPARISON.json
# private plan: instrumented run; SLACK_SET is one of none | face | overlap | gap | all
python3 -I scripts/threshold_probe.py WORK/src PLAN.dxf OUT/run ARCH_TAKEOFF_V2 SLACK_SET GF=<ref> 1F=<ref> 2F=<ref>
python3 -I scripts/qdiff.py OUT/run_a OUT/run_b [JSON]
python3 -I scripts/m4_lintel_probe.py WORK/src PLAN.dxf
# private crops: PRIVATE_DO_NOT_COMMIT/scripts/inspect_pieces.py (it names the plan's segments)
```

**Check that the probe is faithful.** With `SLACK_SET=none`, the probe's `BOQ_LINES.json`, `ARCH_OPENINGS.json`, `ARCH_WALLS.json`, `ARCH_ROOMS.json` and `FINISH_COVERAGE.json` must hash equal to a plain CLI run.

## Investigation B (RFI audit)

```
python3 -I tools/urban_boq_m9.py arch --drawings PLAN.dxf --out V1_OUT --method ARCH_TAKEOFF_V1 --reference-areas GF=.. 1F=.. 2F=..
python3 -I tools/urban_boq_m9.py arch --drawings PLAN.dxf --out V2_OUT --method ARCH_TAKEOFF_V2 --reference-areas GF=.. 1F=.. 2F=..
python3 -I scripts/rfi_audit.py V1_OUT V2_OUT B_RFI_AUDIT.csv B_RFI_AUDIT.json [FLOAT_MISSED_DOOR_BLOCKS]   # value in the PRIVATE README
```

## Tests

```
python3 -m pytest -q tests/m9_s6                      # S6 Phase 1 tests (one session at a time)
URBAN_REAL_PLAN_DXF=PLAN.dxf URBAN_R5_REGISTERS=<R5_REGISTERS_DIR> \
    python3 -m pytest -q tests/m9_s6/test_s6_real_plan.py     # <R5_REGISTERS_DIR>: see the PRIVATE README
python3 -m pytest -q tests engine && python3 -m pytest -q agents  # full suite, two sessions, one after the other
```
