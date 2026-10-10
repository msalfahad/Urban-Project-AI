# 01 christiannp forensic re-run: intake and freeze verification

This round treats the ZIP below as the authoritative frozen christiannp dataset. Earlier chat summaries and the earlier quoted blind report are not used where the ZIP holds the original evidence.

## 1. Package

| Field | Value |
|---|---|
| ZIP | `CHRISTIANNP_FORENSIC_RERUN_2026_10_07.zip`, 1,959,747 bytes |
| ZIP sha256 | `fcaff77001a470bb2187e086f42b6cdbc435f8b5ea02126c9cb7aea67bce7b80` |
| Members | 194; no absolute paths and no `..` |
| Extraction | a fresh scratch directory, read with `python3 -I`; no christiannp script was executed |
| Manifest | `FORENSIC_FREEZE_MANIFEST.json`, sha256 `af2d3441cf2d464e5fb31c8651a540abf22ff5dc55f9d34786f9506038197bf2` |
| Frozen at | 2026-10-07T17:04:17Z: "Frozen before any comparison with Urban / donor / freelancer / prior benchmark results" |
| Urban HEAD | `2c00561` (no Urban file changed before the crosswalk was built) |

## 2. Hash verification

- **The 188 files the manifest lists:**
  - 188 of 188 have matching sha256 and byte size;
  - 0 are missing;
  - 0 are altered.
- **Files present but not in the manifest:** 5, at the root: `TOOL_CALL_INDEX.csv`, `MANUAL_DECISIONS.csv`, `ASSUMPTION_REGISTER.csv`, `UNRESOLVED_REGISTER.csv` and `CHRISTIANNP_FORENSIC_DONOR_REPORT.md`.
  - Each is byte-identical to its hashed copy under `01_tool_calls/`, `14_assumptions/`, `15_unresolved/` or `17_donor_lessons/`.
  - They are convenience copies, not new evidence.
- **Files the builder read:** every one is hash-checked against the manifest before use. The 31 files and their hashes are in `CHRIS_INPUT_LEDGER.json`.

## 3. Source-before / source-after

| Drawing | sha256 before = after | Same file Urban decodes |
|---|---|---|
| P7757.dxf | `ab54dd55…31cc4` (17,227,946 B, mtime unchanged) | YES (Urban K2 decode `k2_ab54dd554c31fe4a`) |
| ST7757.dxf | `9f9d1179…738079` (3,153,037 B, mtime unchanged) | YES (Urban K2 decode `k2_9f9d1179a5d2a663`) |
| ST7757.dwg (open in AutoCAD, not used) | `3f7a556c…f0227` | n/a |

Other integrity evidence:
- **DBMOD:** 53 (ST) and 21 (P), before and after. The state was already non-zero before the run.
- **Disk versus memory:** reconciled handle for handle, and IDENTICAL for both drawings (`02_raw_entities/DISK_VS_MEMORY_CHECK.json`).

So both systems measured the same two files. Every difference below is a method difference, not a source difference.

## 4. Process artefacts read

| File | Content |
|---|---|
| `PROCESS_LOG.md` | 24 steps, S00–S23, with origin labels (MCP_NATIVE, CUSTOM_LISP, LOCAL_SCRIPT, CLAUDE_REASONING, ENGINEERING_ASSUMPTION, …). |
| `TOOL_CALL_INDEX.csv` | 34 MCP calls, 6 of them FAILED or DEFECTIVE (C005–C009, C013, C018, C024, C025). Four raw outputs it lists (C018, C019, C021, C022) are not separate files; they are reproduced verbatim in `02_raw_entities/MCP_RAW_OUTPUTS_PHASE0-3.md`. **This is the only "expected output missing" finding.** |
| `MANUAL_DECISIONS.csv` | 18 decisions, MD01–MD18 (gap analysis in 12). |
| `ASSUMPTION_REGISTER.csv` | 10 assumptions, A01–A10; none is publishable as verified. |
| `UNRESOLVED_REGISTER.csv` | 21 unresolved facts, U01–U21. |
| `15_unresolved/REJECTED_CANDIDATES_INDEX.csv` | 9 regression areas. |
| Trade folders 03–13 and `16_final/QUANTITY_SUMMARY.csv` | 80 rows. Every quantity in this package comes from these files. |

## 5. Differences from the earlier quoted blind report

The rerun's assumption numbering (A01–A10) is not the earlier A1–A15. The earlier rule set R1–R5 is re-tested object by object in `08_beams/BEAM_RULE_TESTS_R1_R5.csv`.

| Topic | Earlier report (superseded) | Frozen ZIP (used) | Explanation from the files |
|---|---|---|---|
| GB raw lines → strips | 85 raw lines → 42 strips, 200.036 m | 89 layer-1 faces (85 LINE + 4 ARC) → 44 strips, 208.129 m | 200.036 m is exactly the straight-strip length in the ZIP (`straight_strip_length_mm` 200035.8): the earlier figure left out the 2 arc strips (8.093 m) |
| GB depth | A5 0.60 m, 36.006 m³ | not assumed: 0.4 / 0.6 / 0.8 m scenarios (24.976 / 37.463 / 49.951 m³) | A03, U01 |
| GF slab thickness | A1 0.20 | not assumed (A04, U05) | see 10: the stacked `T` / `16` tags were missed |
| Rebar | 22.916 t | 13,412.6 kg of INCLUDED components; 16 components UNRESOLVED | component evidence only, no ratios |

## 6. Coordinate frames used for matching

- **christiannp:** frame-local coordinates (origin at the DEFPOINTS sheet-frame minimum). GBP origin (78929.897, 29036.099); GFRS origin (40205.49, 29036.099); and so on.
- **Urban:** the S1 census registers are already frame-local and use the same hex handles. Urban's frozen V3 GB register keys bands by decimal handle (`H2004` = `7D4`).
- **Join keys:** handles first, with coordinates as a check:
  - ground beams: face-handle pairs;
  - footings: outline handles;
  - columns: per-plan outline handles;
  - beams: tag handles;
  - walls: face-handle pairs;
  - slab openings: bbox IoU in the local frame.
- **Geometry Urban does not store:** band coordinates, cell polygons and opening rings were re-derived by `scripts/extract_urban_geometry.py` from the frozen K2 decode with the frozen Urban builders. Every extract reproduces the frozen register first:
  - 43 bands / 59 spans / 198.796 m;
  - 31 ground-slab cells with the same ids and areas;
  - B2A1 slab gross and opening areas on all three roof sheets.
