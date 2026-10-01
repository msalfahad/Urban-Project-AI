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

## R8.5 (shadow)

| script | writes (outputs/r8_5/) | purpose |
|---|---|---|
| `r8_5_source_exceptions.py` | `SOURCE_EXCEPTION_REGISTER.json` | every unrealised object per row region, positive-evidence states, explicit layer relevance |
| `r8_5_qualification.py` | `CAPABILITY_SIGNATURE_REGISTER.json`, `DECODER_QUALIFICATION_V2.json`, `INDEPENDENT_RECONCILIATION_RESULTS.json` | target signatures, V2 records, DXF search |
| `r8_5_value_shadow.py` | `SHADOW_VALUE_DIFF.json`, `CANONICAL_SHADOW_QUANTITIES.json`, `REAL_PROJECT_R8_5_STATUS.json` | canonical remeasurement (Qortuba), canonical status (P7757), native cross-check (Al Rashed) |
| `r8_5_package.py` | `data/reports/URBAN_QTO_R8_5_VALUE_SHADOW/` + zip | review package from the outputs and the final suite's junit |

### R8.5 follow-up (no independent DXF required)

| script | writes (tests/r8_5/registers/) | purpose |
|---|---|---|
| `r8_5_export_intake.py` | `R8_INDEPENDENT_EXPORT_INTAKE.json` | admission + measured verification of supplied DXFs (the two ezdxf DXFs: DIAGNOSTIC_NONQUALIFYING_CONVERSION) |
| `r8_5_adapter_defect.py` | `R8_ADAPTER_DEFECT_CLOSED_FLAG.json` | active-path defect report (project reader closed bit); reported, not fixed |
| `r8_5_migration_round1_scope.py` | `R8_MIGRATION_ROUND1_SCOPE.json` | scope of the design-only migration round 1 (`docs/R8_MIGRATION_ROUND1_DESIGN.md`) |

## R8.6 (pre-migration proof; shadow / design)

| script | writes | purpose |
|---|---|---|
| `r8_6_canonical_rebuild.py` | `tests/r8_6/registers/QORTUBA_ROUND1_PROOF.json` | the six round-1 rows rebuilt by the active method from canonical inputs only; method-input contract ablations |
| `r8_6_pre_migration.py` | `tests/r8_6/registers/*.json` | owner actions, dependency graph, blocker register, legacy audit, round-1 signatures, parser plan, defect, transaction, decisions |
| `r8_6_upload_drift.py` | `outputs/r8_6/UPLOAD_DRIFT_STATUS.json` | stored villa inventory vs the session upload folder (status step, never a test) |
| `r8_6_package.py` | `data/reports/URBAN_QTO_R8_6_PRE_MIGRATION_PROOF/` + zip | review package from the registers and the final suite's junit |

## R8.6A (DXF intake, source fidelity, parser independence; shadow)

External DXFs are read from the hash-addressed store `data/inputs/by_sha256/<sha256>.dxf` (untracked; declared in
`tests/r8_6a/FIXTURE_MANIFEST.json`). Run the scripts outside any test session (the determinism guard forbids
test-time writes). `<work>` holds the K2 pickles, indexes and D1 decodes the intake reads.

| script | writes | purpose |
|---|---|---|
| `r8_6a_reconcile.py` | `<work>/*_reconcile.json` | D1/K1 vs DXF/K2 diagnostic reconciliation (REAL tolerance, handle + instance path, no nearest-neighbour) |
| `r8_6a_intake.py` | `tests/r8_6a/registers/{DXF_INTAKE,DXF_PROVENANCE,SOURCE_FIDELITY,QORTUBA_ROUND1_DXF,P7757_DXF}*.json` | hash identification, streaming header/census/handle scan, writer vs decoder vs LASTSAVEDBY, revision identity, editing-time evidence, admission V2, scoped signature states, plan variants |
| `r8_6a_registers.py` | `tests/r8_6a/registers/{OWNER_ACTION_REGISTER,R8_6A_DECISION_REGISTER}.json` | owner actions V3 (FILE_RECEIVED vs INDEPENDENT_PROVENANCE_ESTABLISHED), decisions, contract review, findings, gates |
| `r8_6a_owner_images.py` | the two owner-review PNGs | Qortuba SECOND FLOOR PLAN variants (DXF as stored) and the Q-14 ten-space ceiling question |
| `r8_6a_package.py` | `data/reports/URBAN_QTO_R8_6A_DXF_INTAKE/` + zip | review package from the registers, the images and the final suite's junit |

## R8.7 (canonical measurement input, Qortuba new revision; shadow)

The contract lives in `engine/source` (`canonical_input.py`, `canonical_build.py`, `owner_scope.py`); the lab only
bridges it to the legacy QS01 method. Owner decisions are scoped claims in `data/registry/OWNER_PROJECT_CLAIMS.json`.

| script | writes | purpose |
|---|---|---|
| `r8_7_canonical.py` | `<work>/*_k2.pkl` (`build-k2`) | QS01 contract, strict / lenient bridge, isolated stub-decode runner, revision inputs, scoped units |
| `r8_7_proof.py` | `tests/r8_7/registers/{QS01_METHOD_INPUT_CONTRACT,FAIL_CLOSED_ABLATION_RESULTS,QORTUBA_REVISION_DELTA,Q14_SCOPED_CEILING_RULE,REGION_CLASSIFICATION_NEW_REVISION}.json` | ablations, OLD_K1 / OLD_K2 / NEW_K2 runs, parser-culprit bisection, cause attribution, scoped Q-14, region classes |
| `r8_7_registers.py` | `tests/r8_7/registers/{QORTUBA_SOURCE_REVISION_REGISTER,OWNER_ACTION_REGISTER,OWNER_PROJECT_CLAIMS,CANONICAL_MEASUREMENT_INPUT_SCHEMA,R8_7_DECISION_REGISTER}.json` | revisions, owner actions V4, claim scope checks, schema, decisions / gates / findings |
| `r8_7_dwg_anchor.py` | `tests/r8_7/registers/NEW_DWG_SOURCE_IDENTITY.json` | candidate original DWG vs the new-revision DXF with the pinned decoder; verdict by fixed rules, never forced |
| `r8_7_package.py` | `data/reports/URBAN_QTO_R8_7_CANONICAL_INPUT/` + zip | review package from the registers and the final suite's junit |
| `r8_8_topology.py` | `tests/r8_8/registers/{OLD_QORTUBA_CROSS_ROUTE,NEW_QORTUBA_TOPOLOGY,QORTUBA_SIX_ROW_STATUS,ELLIPSE_EXCLUSION_AUDIT,GEOMETRY_ROLE_REGISTER,VISIBILITY_AUTHORITY_REGISTER,REGION_MEMBERSHIP_POLICY,SITES_*,TOPOLOGY_CROSSCHECK,TOLERANCE_ARCHITECTURE}.json` | TS01 certified topology on old K1 / old K2 / new K2, cross-route control, six-row status, GEOS cross-check, tolerance inventory + H584 ULP study (project semantics live here only) |
| `r8_8_registers.py` | `tests/r8_8/registers/{OWNER_ACTION_REGISTER,ENGINEERING_ACTION_REGISTER,SOURCE_SUBPART_IDENTITY_SCHEMA,R8_8_DECISION_REGISTER,ARCHITECTURE_REVIEW}.json` | owner actions V5 (owner-doable only), engineering actions, decisions / findings / gates / answers, architecture review |
| `r8_8_package.py` | `data/reports/URBAN_QTO_R8_8_TOPOLOGY_STABILITY/` + zip | review package (18 md + 16 json + 2 site overlays) |

`<work>` must hold `old_k2.pkl` (K2 on LibreDWG's DXF of the old DWG) and `new_k2.pkl` (K2 on the hash-addressed new DXF).
