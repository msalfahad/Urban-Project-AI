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
