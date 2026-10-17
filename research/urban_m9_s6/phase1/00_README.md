# M9 S6 Phase 1: ARCH_TAKEOFF_V2 (drawing admission, unit-relative tolerances, completeness gates)

These notes are generic: no drawing identity, no client figure, no benchmark value. The reference-plan evidence (counts, areas, discovery report, variants) is in the PRIVATE folder of the S6 Phase 1 ZIP, outside the repository.

Base: HEAD `6b7a2e4` (the S6 review). Nothing here starts Phase 2.

## What Phase 1 delivers

`--method ARCH_TAKEOFF_V2` (opt-in) is `ARCH_TAKEOFF_V1`'s measurement wrapped in four layers:

1. **Drawing admission, before any quantity** (`URBAN_DRAWING_DISCOVERY_V1`, stages 0–10).
   - It stops with **exit 2** on:
     - an empty model space;
     - undeclared or contradicted units;
     - paper-space sheets;
     - plan titles outside every frame, or no plan region;
     - a cut through drawn geometry;
     - a missing XREF;
     - a failed, empty, stale or garbage DWG conversion;
     - plan = structural drawing;
     - `--structural` without `--conventions`;
     - an entity with no reader disposition.
   - On a stop, no BOQ is published. The report, the stopping findings and the remedies are, and an earlier BOQ in the same folder is moved to `SUPERSEDED_<n>`.
   - Reviewer inputs are recorded, never defaulted: `--units`, `--region` and `--accept-missing-xref`.
2. **Unit-relative tolerances** (1 mm in every unit, exactly 1.0 at mm), plus plan regions split along the empty bands between drawn plans, and sheet frames drawn as lines.
3. **Entity-completeness flags (REVIEW_REQUIRED, on the room)**:
   - fills read independently of the plan reader that are not measured as columns;
   - fills the plan reader cannot read;
   - door blocks scaled non-uniformly;
   - hidden-layer content.
4. **Completeness gates**:
   - every physical face part, and every space × {floor, ceiling, walls, skirting}, ends in LINE / RFI / EXCLUDED (with its reason);
   - every doorway strip is reviewed individually (threshold / window reveal / unattributed) and becomes a BLOCKED_RFI line;
   - UNACCOUNTED fails the run with **exit 3** (nothing published; `diagnostics/` keeps the computed lines).

`ARCH_TAKEOFF_V1` is unchanged. Its outputs are byte-identical to the base on the synthetic villa (15 files) and the reference plan (16 files). `--strict-admission` puts V1 behind the same admission, adding only `DRAWING_DISCOVERY.json`.

## Before / after (synthetic fixtures through the production CLI)

| Sweep | Silent (exit 0, wrong) | Blocked (exit 2 + reason) | Flagged on the BOQ | Measured identically |
|---|---|---|---|---|
| HEAD V1 (before) | 22 | 0 | 0 | 9 |
| V1 now (no flag) | 22 (unchanged, as required) | 0 | 0 | 9 |
| V1 `--strict-admission` | **0** | 12 | 10 | 9 |
| **V2** | **0** | 9 | 10 | 12 |

The 31 fixtures include 4 controls and 1 hand-truth case. The fake-converter DWG cases (empty, stale, garbage, same name) are all FIXED in V2 and in V1 strict.

The finish cases:
- the band above partial wet tile;
- stair-hall walls and skirting;
- door thresholds;
- window reveals.

They go from no line and no RFI to one BLOCKED_RFI line each. No quantity and no material is assumed.

## Files

| File | What |
|---|---|
| `S6P1_01_DEFECT_MATRIX_BEFORE_AFTER.csv` | All 44 review entries plus 5 Phase 1 findings: before (HEAD V1), V1, V1 strict, V2, status, evidence |
| `S6P1_02_SOURCE_CHANGES.md` | Every changed / new module, why it is V1-neutral, and the files left alone because other freezes pin them |
| `S6P1_03_TEST_RESULTS.md`, `TEST_GATE_M9_S6P1.json` | Full suite in two sessions, classified; the S6 tests; the real-plan tests |
| `S6P1_04_DISCOVERY_*.json` | Discovery reports: the synthetic villa (admitted), a units stop (blocked) and a nested-plan flag |
| `S6P1_05_AREA_RECONCILIATION_SYNTHETIC.json` | Per floor: the face partition, the categories (V1 = V2), the strips by class and by verification, and the V1 lines kept |
| `S6P1_06_ENGINEERING_ASSESSMENT.md` | The twelve requirements, assessed |
| `S6P1_07_HANDOFF.md` | What works, what does not, and what to do next |
| `v1_snapshot.py` | Writes the V1 quantity snapshot `tests/m9_s6/data/V1_SYNTHETIC_VILLA_SNAPSHOT.json` (made from HEAD `6b7a2e4`) |
| `repro/` | The harnesses used for the matrix (method and extra flags from the environment) |

## Running it

```
python3 tools/urban_boq_m9.py arch --drawings PLAN.dxf --out OUT --method ARCH_TAKEOFF_V2 [--facts FACTS.json]
    [--units mm|cm|m|in] [--region GF=x0,y0,x1,y1 ...] [--accept-missing-xref BLOCK ...]
    [--structural ST.dxf --conventions engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json]
exit 0  admitted and complete: V1's files + DRAWING_DISCOVERY.json + FINISH_COVERAGE.json
exit 2  admission blocked: DRAWING_DISCOVERY.json + ADMISSION_BLOCKED.json (+ DWG_CONVERSION.json), no BOQ
exit 3  completeness failed: COMPLETENESS_FAILED.json + diagnostics/, no BOQ
```

## Open (not Phase 1)

- **Reader fixes** (S6 Phase 2): nested and MINSERT hatches, SOLID fills, layer-0 inheritance, rotated or exploded columns, too few columns, non-uniform door blocks, Arabic diacritics, and honouring layer state. These are all **flagged** today, never silent.
- **S6P1-NEW-05, threshold float fragility.** The reference plan in metres differs from mm by one 0.20 m wall run. The slack that fixes it changes the mm result, so it waits for review.
- **Owner decisions:**
  - freezes by behaviour rather than by source bytes;
  - V1 strict by default;
  - the structural-default warning in the frozen entry points;
  - the surface-eligibility table;
  - the opening-deduction threshold;
  - the threshold / reveal / stair-hall / exterior finishes (Q-S6-1, Q-S6-4, Q7, Q1).
- The gate stays **INCOMPLETE**. Nothing is reviewed or quotation-ready.
