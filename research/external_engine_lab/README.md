# External engine lab (research only)

This folder may hold donor clones, comparison scripts, native AutoCAD experiments,
external MCP tests, benchmark adapters and experimental outputs.

- `DONORS.lock` pins every donor at the commit reviewed (2026-09-30), with licence, purpose and status.
- `THIRD_PARTY_PROVENANCE.json` holds the prepared provenance rows for the only two approved COPY_ADAPT items.
- `donors/` and `outputs/` are gitignored. No donor source is committed here.

**Production boundary:** nothing under `engine/` may import this folder, an MCP server, a donor engine or live AutoCAD COM. The rule is enforced by `tests/r8_0/test_r8_0_import_boundaries.py`. The lab talks to production only through files, and a lab result can only ever become an OBSERVATION, TRANSCRIPTION, GEOMETRY_CANDIDATE or QA_FINDING. It never becomes a FINAL quantity.

## R8.1 additions

- **MINSERT oracle.** `minsert_reflection_oracle.py` produces `MINSERT_REFLECTION_ORACLE.dxf`, `.json` and `.md`. It is the one-time native AutoCAD check for a MINSERT placed under a reflecting parent. Status: `MINSERT_REFLECTION_ORACLE_CONFLICT`; the analysis favours the hand truth.
- **Real-drawing characterisation.** `r8_1_real_drawing_characterisation.py DECODE.json ...` runs a read-only pass over a real decode:
  - production D1 → K1 against `cad_adapter`;
  - field audit;
  - mirrored-arc comparison;
  - dynamic-block counts.

  Its output goes to `outputs/`, which is gitignored. No count it prints may become a production target.

## R8.2 additions

- **`r8_2_shadow_impact.py`: the shadow bridge.** It runs the real downstream code for each active path:
  - Qortuba QS01;
  - P7757 PA07;
  - the Al Rashed project reader.

  Each run is repeated once per defect, with that single defect corrected (K1 is the corrector). The diffs are written to `outputs/`. `cad_adapter.normalize` is patched in-process only; nothing published changes.
- **`r8_2_k2_real_attempts.py`** tries K2 on the real sources through `dwg2dxf` plus ezdxf, and records the exact failures and hashes. No DXF is repaired.
- **`r8_2_path_and_independence.py`** holds the ACTIVE_PATH_MAP and DECODER_INDEPENDENCE_MATRIX as data. `verify()` checks the map against the runners' imports; this check is pinned by `tests/r8_2/test_r8_2_paths_and_pins.py`.

## R8.3 — pinned re-decode, unit context, measurement frame (SHADOW)

- `r8_3_pinned_redecode.py` — re-decodes every original DWG present with the REGISTERED dwgread
  (sha256 fe49cf28…) into `data/runs/pinned_redecode/` (historical JSON untouched); compares bytes, UTF-8
  normalisation, SRD, census, handle representation, references; records the text-decoding delta row by row and
  the `PINNED_LIBREDWG_DWGREAD_JSON_HANDLE_REPRESENTATION_DEFECT` (reproduction count, collisions, affected references).
- `r8_3_real_status.py` — evidence (engine/source/cad/unit_evidence.py) → UNIT_CONTEXT / region / MEASUREMENT_FRAME /
  CAD_PROFILE (engine/source/frame.py, cad_profile.py) for the three real sources; column Question A. No quantity is
  read; nothing is published.
- Neither file is imported by `engine/`.

## R8.4 (shadow)

| script | writes | purpose |
|---|---|---|
| `r8_4_qualification.py` | `outputs/r8_4/DECODER_QUALIFICATION_*.json`, `INDEPENDENT_RECONCILIATION_RESULTS.json` | target feature profiles, handle representation, qualification register (P7757 BLOCKED_EXTERNAL_INPUT), DXF search with writer provenance |
| `r8_4_regions.py` | `outputs/r8_4/REFERENCE_REGION_REGISTER.json` | deterministic region candidates, active-path view roles, pending adapter designations (none accepted) |
| `r8_4_shadow_diff.py` | `outputs/r8_4/SHADOW_ROW_DIFF.json`, `REAL_PROJECT_R8_4_STATUS.json` | row-by-row current vs canonical (frame V2, CAD profile V2), status only, no value recomputed |
| `r8_4_package.py` | `data/reports/URBAN_QTO_R8_4_QUALIFICATION_SHADOW/` + zip | review package from the outputs, registers and the final suite's junit |

Run order: qualification → regions → shadow_diff → (final suite) → package. No script writes to a published, approved or frozen artefact.
