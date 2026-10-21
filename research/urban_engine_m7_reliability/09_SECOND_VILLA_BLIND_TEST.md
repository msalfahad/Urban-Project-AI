# 09 Second villa blind test — BLOCKED

## Status

**Blocked: no second real drawing set is available.** Searched:

- the repository (`data/inputs/by_sha256/`): only ST7757's structural and architectural DXF and its PDFs;
- the connected Google Drive, by metadata only (titles containing `.dxf`, `.dwg`, `villa`, `structural`; CAD mime
  types): reference-library folders only, no drawing set. Nothing was opened or downloaded.

No result in this package is presented as second-villa evidence. The held-out synthetic set is generalisation evidence
about drawing variation, not about real-project accuracy; ST7757 remains the only real project, and its M7 run is
post-discovery.

## What is needed (intake requirements)

| # | Item | Why |
|---|---|---|
| 1 | Structural drawings as **DXF** (DWG converted with a pinned converter), every sheet: foundation, ground beam, column, each slab plan, schedules, sections, details | the route reads DXF geometry; a PDF alone carries no measurable geometry here |
| 2 | Architectural floor plans as DXF (optional, improves exterior ground beams and lintels) | registration on column patterns; lintel openings |
| 3 | The revision of each file (the manifest records the sha256; a different file is a different run) | decisions and results are bound to the revision |
| 4 | Storey heights / levels if not printed on the drawings (a profile JSON) | column and stair heights |
| 5 | An **independent** reference BOQ prepared without access to the engine's output, in `GENERIC_BOQ_CSV_V1` (FAMILY, STOREY, QUANTITY, UNIT m3, optional ITEM_REF, DESCRIPTION) — declared by path and sha256 in the manifest **before** the run | the comparison is meaningful only if the reference cannot have seen the run, and the run cannot have seen the reference |
| 6 | Who prepared the reference, with what method and scope (what it includes: blinding, lean concrete, stairs, tanks...) | scope differences are explained, never tuned away |
| 7 | Permission to keep the drawings out of git (private inputs) | client drawings are never committed |

## Protocol (enforced by `tools/urban_project_run.py`)

```
python3 -I tools/urban_project_run.py init  villa2.json --project V2 --structural S.dxf --architectural A.dxf \
                                            --profile P.json --reference-boq REF.csv --rate 26.5
python3 -I tools/urban_project_run.py run   villa2.json out/      # blind: the reference is never opened
python3 -I tools/urban_project_run.py check villa2.json out/      # rebuild in memory, byte for byte
git add out/RUN_FREEZE.json ... && git commit                     # the freeze is committed before comparing
python3 -I tools/urban_project_run.py compare villa2.json out/    # only now is the reference read
```

1. **Register**: the manifest records each drawing's sha256 and revision and the reference's declared sha256.
2. **Freeze the engine**: the run records the git commit and the sha256 of every engine file (and whether any differs
   from the commit).
3. **Run blind**: route G with V5, completeness, per-item independent checks, the release register. The JSON inputs
   pass `benchmark_protection.assert_blind`. Nothing reads the reference.
4. **Freeze the output**: `RUN_FREEZE.json` hashes every output; a frozen folder is never overwritten.
5. **Compare**: refused unless every frozen output is unchanged and the reference is the one declared before the run.
   Per family and storey: MATCH / EXPLAINED_BY_UNRESOLVED / ENGINE_SHORT / ENGINE_OVER / ENGINE_ONLY / REFERENCE_ONLY,
   with the difference in money at the declared rate. A state is a lead for investigation on the drawing, never a
   correction.
6. **Investigate, generalise, retest**: each difference traced to its geometric cause on the drawing; a rule about
   drawings in general (a new convention), tested on synthetic fixtures; the second villa re-run as a new, POST-FIX run
   in a new folder. The blind run and the post-fix run are reported separately; the blind numbers are never replaced.

The protocol was exercised end to end on a synthetic project (villa seed 3, reference = the generator's design truth):
`tests/m7_reliability/test_m7_project_run.py` — run, check, compare, and every refusal.
