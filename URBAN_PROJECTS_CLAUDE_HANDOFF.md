# URBAN PROJECTS AI BOQ/QTO — COMPLETE CLAUDE CODE HANDOFF

Written by Claude Code for an independent reviewer (ChatGPT) and for Mohammad. The goal is to let the reviewer **challenge** the system, so this report states what exists, what it proves, and where it is weak.

**How to read this report**

* **Measured / run / read** means I ran it or read the file in this snapshot.
* **Reported** means it is taken from an earlier round's frozen package, and I did not re-derive it now.
* **Synthetic** test success is never presented as proof of accuracy on a real drawing.
* An **XFAIL** is a known failure that has been written down. It is never counted as a pass.
* File paths are relative to the repository root.

---

## 1. Snapshot / version

| Field | Value |
|---|---|
| Repository | `msalfahad/Urban-Project-AI` (GitHub) |
| Root path (this container) | `/home/user/Urban-Project-AI` |
| Branch | `claude/access-permissions-setup-ii24ws` |
| Code snapshot commit | `1c331c5e2418f05bbc8244b0b7d207b860e2d8ad`, "V3c forensic accuracy + donor gap audit: recommendation only, no engine change" (2026-10-04 21:30:51 UTC) |
| Handoff commit | One commit on top of `1c331c5` that adds **only** this file (`URBAN_PROJECTS_CLAUDE_HANDOFF.md`). There is no code change. |
| `git status` at the snapshot | clean: 0 modified, 0 staged, 0 untracked outside `.gitignore` |
| Snapshot time | 2026-10-05, about 15:25–16:30 UTC. The full test run started at 15:27 UTC. |
| Tracked files | 2,056 |
| Size | `.git` 51 MB. The working tree is 3.9 GB, of which `data/` is 3.8 GB (gitignored). |

**What this handoff represents.** It represents **the latest committed version and the working tree together**: they are identical, because nothing is uncommitted. The ZIP also adds selected **gitignored** files that are needed for review. Those files exist only on this container's disk and not in git. They are listed in §41 and in `ZIP_MANIFEST.txt` inside the ZIP.

**Important gitignored folders.** These are not in git and are only partly in the ZIP.

| Folder | Size | Contents | In ZIP? |
|---|---|---|---|
| `.secrets/` | small | API key, deploy service-account JSON, Twilio env | **NO, never** |
| `data/experiments/` | 2.4 GB | every research run (P7757, Qortuba PA08, …) | only the Qortuba PA08 sealed-takeoff JSON + seal |
| `data/runs/` | 1.0 GB | CAD decodes (`cad_convert/*.json`, e.g. ALRASHED 25,429 objects) | NO (large; regenerable from DWG with the pinned decoder) |
| `data/inputs/by_sha256/` | 303 MB | client DWG / DXF / PDF / DWF, content-addressed | NO (client drawings: send the selected ones separately, §41) |
| `data/golden/` | 99 MB | 23010 sealed site benchmark + fixtures; 7757 PDFs / DWG | JSON / MD only |
| `data/reports/` | 44 MB | every round package (R8 spec, RC1, V3 / V3b packages, …) | MD + JSON + CSV only (no XLSX / PDF / ZIP / PNG) |
| `data/rate_cards/`, `data/rate_library/` | small | **pricing** data | NO (out of QTO scope) |

There is **no CI**: there is no `.github/` folder and no workflow files. Tests are run by hand with `python3 -m pytest`.

---

## 2. Executive status

There are two honest one-line summaries:

1. **The CAD source layer (R8 / K1 / K2) is the most rigorous part of the system.** It is mathematically tested, fails closed, and is well documented.
2. **The quantity engines are real but not production-grade.** They produce deterministic, traceable, reproducible BOQs for two real projects (Qortuba apartment, Alsenan villa). A forensic audit (V3c) still proved **six silent rebar population defects** and an **≈140 m blockwork wall-length deficit** on Alsenan, and none of these were caught by any of the 5,875 tests.

Tests prove *consistency*. They do not prove *correctness against a human QS*.

### WORKING (implemented and tested; real-drawing evidence exists)

* **DWG decoding** through the pinned LibreDWG 0.13.3 `dwgread` → JSON (D1). This is fidelity-checked on real P7757, Qortuba and Al Rashed files.
* **DXF reading** through ezdxf 1.4.4 (K2).
* **K1 CAD kernel** (`engine/source/cad/kernel.py` + `kernel_ocs.py`): exact composed affine transforms, mirrored arcs, bulge side, OCS / extrusion fail-closed, block base points, nested INSERTs. It passes 330 R8.1 tests and the mutation tests.
* **Capability register.** Every entity type gets an explicit support level; anything unsupported is recorded and never dropped silently (`engine/source/capability.py`, `conservation.py`).
* **Unit / frame policy.** INSUNITS is treated as evidence and not authority. A conflict leads to COUNT_ONLY. Human unit claims are versioned and tied to a file hash (`engine/source/frame.py`).
* **Deterministic, reproducible registers.** Alsenan V3b registers were built twice and are byte-identical. Qortuba RC1 is frozen.
* **Two-layer release model.** The TECHNICAL view (measured / derived) and the COMMERCIAL view (labelled provisional with low / high range) are kept separate. BLOCKED rows never enter a total (`engine/source/release_model.py`).
* **Reporting V2 / V3.** XLSX / PDF workbooks with a readback check, LibreOffice recalculation and formula mapping.
* **Floor / ceiling / wet-floor areas** for clean rooms on vector CAD. On Qortuba, floors agree with the contractor to +1.12% (PA08), and the 23010 full scope is +0.41% vs the manual site measure (errors partly cancel; see §16).

### PARTIALLY WORKING

* **Room closure / identity** on villas. It merges wet rooms into dry zones on Alsenan (GF-Z04 "PANTRY / SALOON / RECEPTION / Wash / DINING / GARDEN"), and 1F is missing baths.
* **Wall finishes** (plaster / paint / wall tile). These are computed with reveals and NET deductions, but the height basis is disputed (plaster to soffit vs to the false ceiling: an 18.8% swing). On Alsenan 37 of 87 tile / WP lines and 67 of 73 plaster / paint lines are BLOCKED technically.
* **Blockwork.** Computed only on wall runs that carry a material claim, which leaves Alsenan ≈140 m of wall length short (−36.5% vs the freelancer).
* **Openings.** Detection and counts are good. **Heights** are mostly not established: on Alsenan, 26 of 33 window heights are BUDGET_ESTIMATE.
* **Structural concrete** (schedule-driven). It is proven within 0.01 m³ against the freelancer row by row, but the scopes differ (ground slab D6, pool, stairs, perimeter strap).
* **Rebar.** It is a real bar-by-bar takeoff (counts × lengths × D²/162), not a ratio. Several **populations are silently missing** (D1–D4, D6) and one is over-counted (D5). Urban net is 26.24 t vs freelancer 44.19 t; after the fixes it is estimated at 30–32 t.
* **PDF raster lane.** Sheet calibration from printed level chains is used for heights (V3b). The raster topology pipeline (E87) and the hybrid path (E95) work only on 23010.
* **Arabic text.** Legacy SHX Arabic decode and an alias table exist; the coverage gaps are in §30.

### IMPLEMENTED BUT NOT SUFFICIENTLY TESTED

* `engine/source/bbs_optimiser.py`: hooks / bends from **ACI 318-19 tables whose edition is not verified** (marked PROVISIONAL_CODE_METHOD); first-fit-decreasing cutting on 12 m stock.
* `engine/source/slab_rebar_binding.py`: binds slab annotations to drawn bars and panels. A de-duplication rule may merge two real layers (OQ-9).
* `engine/source/raster_evidence.py`: raster calibration grades. Tested on one project (Alsenan, 6 sheets).
* Waste / procurement register. The waste values are deliberately **blank (PENDING)**, never zero.
* Dual measurement (Route B / C). 12 rooms reconciled; 14 rooms have Route A only.
* `engine/document_reader.py` (E89): an LLM reads image crops of title blocks / notes, with caching. It is used only on 23010.

### KNOWN BROKEN

* **`engine/cad_adapter.py`** (the old production CAD adapter) still has the mirrored-ARC bug and 9 other transform defects (§8, §9). It is **not fixed**; it is pinned by 43 + 5 XFAIL tests. It is still imported by the legacy ingest harness, `cad_measure` and round self-tests. The current pipelines (Alsenan, Qortuba RC1, R8.x) use K1 / K2 instead.
* **Rebar populations D1–D6** on Alsenan (§21).
* **Wet / dry zone purity** (L-17) and **skirting along void / railing edges** (L-18, suspected).
* **PARTIAL rows inside the technical total** (L-1). The total is a lower bound but is not labelled as one.
* **Al Rashed**: every physical value is VALUE_NOT_COMPUTABLE because of the unit conflict (§11). This is by design: fail closed until the owner confirms.

### NOT IMPLEMENTED

* Population-completeness invariant ("every concrete occurrence has bar sets or an explicit BLOCKED row").
* Schedule / table inventory ("every table on a sheet is consumed or listed UNREAD").
* Blockwork wall-length conservation per floor.
* Revision delta **at entity / quantity level for production**. E11 / E46 exist, but only as a BOQ-line diff and a research tool (§29).
* Live write of QTO outputs (Alsenan V3b, Qortuba RC1) to Firestore. `pm_sync` exists but is only wired to the old manual-takeoff pipeline.
* OCR engine (no Tesseract). Raster schedules are not machine-read.
* MINSERT realisation, XREF resolution, SPLINE / REGION / WIPEOUT / IMAGE geometry, LEADER / MLEADER, old-style POLYLINE in the capability register.
* Excavation, raft, retaining walls, formwork, structural steel.
* CI.

### DEPRECATED / SUPERSEDED (do not rely on)

* `engine/cad_adapter.py` for any geometry that has reflections, OCS, block base points, MINSERT or XREF. It is superseded by K1 / K2.
* The R2–R6e "round" geometry stack on 23010 / P7757 (`engine/round*_*.py`, `tests/test_round*`). It is kept as regression history.
* PA05–PA07 ingest pipelines (`engine/ingest/*`). They were superseded by the R8 source layer, but still use cad_adapter.
* Qortuba PA08 quantities (REV_OLD). They are superseded by RC1 on REV_NEW, but kept as the sealed benchmark.
* `README.md` claims ("50 tests pass", the E1–E20 table) are **stale**.
* Rules R-02, R-05, R-07, R-09, R-13, R-17, R-26 (§15).

---

## 3. Current architecture (the real one)

The original plan was "17 LLM agents + E1–E22 engines, with the LLM extracting quantities". **That is not what the QTO system is today.** Quantities are produced by **deterministic Python code**. LLM agents exist, but none of them sits in the current quantity path.

| Layer | Purpose | Main modules | Inputs → Outputs | Called by → calls |
|---|---|---|---|---|
| **Intake / drawing control** | content-address every file, revision identity, admission class | `engine/source/run_manifest.py`, `canonical_input.py`, `owner_claims.py`, `data/registry/*.json`, `data/inputs/by_sha256/` | file → sha256, writer fingerprint, revision id, admission | project runners → decoders |
| **CAD decode** | DWG → JSON (D1), DXF → objects (D2/K2) | `engine/source/decoder_pins.py` (LibreDWG 0.13.3 pin), `engine/source/cad/libredwg_map.py`, `kernel_ezdxf.py` | DWG / DXF → observations (handles, layers, blocks, raw entities) | runners → K1 / K2 |
| **CAD realisation (K1)** | place every block occurrence in world coordinates exactly | `engine/source/cad/kernel.py`, `kernel_ocs.py`, `observations.py`, `findings.py`, `digests.py`, `capability.py`, `conservation.py` | observations → realised parts with lineage (insert chain, handle path), findings, SRD-1 / RGD-1 digests | runners → frame / topology |
| **Units / frame** | decide whether a value may be physical | `engine/source/frame.py`, `cad_profile.py`, `qualification.py`, `region_candidates.py` | INSUNITS, DIMLFAC, dimension evidence, owner claims → UNIT_CONTEXT, MEASUREMENT_FRAME (CONFIRMED / UNCONFIRMED / CONFLICT) | all measurement engines check it |
| **Geometry / topology** | walls, bands, faces, spaces, closures, openings | `engine/source/topology*.py`, `wall_bands.py`, `wall_faces_v2.py`, `room_topology_v3.py`, `topology_closures.py`, `opening_*.py`, `door_transition.py`, `semantic_zones.py`, `text_role_v3.py` | realised parts → spaces, wall faces, opening register | QTO runners |
| **PDF lane** | vector paths, raster topology, glyph text, frames, document reading | `engine/vector_source.py` (E41), `raster_topology.py` (E87), `glyph_text.py` (E88), `document_reader.py` (E89, LLM), `frames.py` (E23F), `hybrid_path.py` (E95), `engine/source/raster_evidence.py` (V3b) | PDF → paths / pixels / text → candidate spaces, calibrated heights | 23010 runners; Alsenan V3b heights |
| **Engineering interpretation** | structural schedules, tags, occurrences, slab binding | `engine/source/structural_schedule.py`, `structural_qto.py`, `structural_vertical.py`, `beam_binding.py`, `slab_region.py`, `slab_rebar_binding.py`, `concrete_model.py`; **project code in `research/external_engine_lab/alsenan_phase_a3.py`, `alsenan_v3_structure.py`, `alsenan_v3b_struct.py`, `alsenan_v3b_rebar.py`** | DXF texts + PDF images (hand-transcribed schedules) → typed members, rebar definitions | Alsenan runners |
| **QS / quantities** | finishes, WP, skirting, reveals, blockwork, openings, stairs | `engine/source/finish_height_v3.py`, `wall_height.py`, `reveal_finish.py`, `opening_reveals.py`, `waterproofing*.py`, `trade_regions.py`, `trade_strips.py`, `corner_bead.py`, `exposed_finish.py`, `marble_thresholds.py`; older `engine/qs_core/*` (Al Rashed R5–R7) | spaces + openings + rules → quantity rows with formula + trace | runners |
| **Rules** | Urban methods, owner facts, project rules | `engine/source/urban_methods.py`, `urban_methods_v3.py`, `owner_facts.py`, `owner_method_facts.py`, `data/registry/*RULES*.json`, `data/trade_rules/*.json`, `tests/alsenan/registers_v3b/OWNER_METHOD_REGISTER.json` | rule id → parameter / method | QS engines |
| **BOQ / release** | canonical items, release views, provisional classes, waste | `engine/source/boq_canonical.py`, `release_model.py`, `room_matrix.py`, `waste_procurement.py`, `boq_report.py` | quantity rows → BOQ lines (TECHNICAL / COMMERCIAL) | runners → reporting |
| **Validation / QA** | invariants, gates, conservation, freeze | `engine/qs_core/invariants.py` (INV-01..28), `engine/source/conservation.py`, `closure_release.py`, FINAL_QA registers, `conftest.py` determinism guard | registers → PASS / FAIL records | runners, tests |
| **Reporting** | XLSX / PDF for owner and QS | `engine/reporting_v2/*`, `engine/reporting_v3/*`, `research/external_engine_lab/reporting_v2_alsenan.py` | registers → workbooks, PDFs, readback | build scripts |
| **Agents (LLM)** | business / communication tasks + A1 / A2 drawing reading | `agents/a1_*` … `agents/a17_*`, `agents/base.py` | text / images → validated JSON | `pipeline/orchestrator.py`, tools, integrations |
| **Storage / Firestore** | BOQ items into the Flutter app | `engine/pm_sync.py` (E14), `engine/boq_formula.py`, `tools/connect_firestore.py`, `tools/firestore_sandbox.py` | approved BOQ lines → `projects/{id}/boqItems/{itemId}` | `pipeline/end_to_end.py`, `pipeline/phase0.py` only |
| **Pricing (separate)** | rate library, audit of priced BOQ | `engine/rate_library.py` (E4), `engine/audit/*` (Phase 0 auditor), `engine/preliminaries.py`, `engine/cooling.py` | priced workbook → audit report | `pipeline/*`, not the QTO runners |

**Where the real project logic lives.** Much of the per-project QTO logic (Alsenan A-phase … V3b, Qortuba R8.x / RC1) lives in **`research/external_engine_lab/`**: 174 files, about 44,800 lines of Python. Generic engines were promoted into `engine/source/` (95 files, stdlib-first). The boundary rule is "engine/ never imports research/", and there is **one known violation** (§22, boundary debt). A reviewer should treat `research/external_engine_lab/alsenan_*` as **project runners holding project-specific transcriptions** (schedules typed in from the PDF), and not as generic engines.

---

## 4. Data flow

**The planned flow:** drawing → parsed geometry → engineering meaning → quantity → rules → validation → BOQ.

**The real flow today** (Alsenan V3b / Qortuba RC1):

```
1  Intake: sha256 → data/inputs/by_sha256; revision + admission recorded (run_manifest)
2  Decode: DWG → LibreDWG dwgread JSON (D1)  |  DXF → ezdxf (K2)  |  PDF → PyMuPDF paths/images
3  Realise: K1 kernel → world-placed parts with lineage; capability + conservation accounting
4  Frame: UNIT_CONTEXT → MEASUREMENT_FRAME; CONFLICT ⇒ COUNT_ONLY (no physical value)
5  Topology: wall bands → faces → closures → spaces (vector); raster only as a second signal
6  Identity: text roles (Arabic legacy decode + aliases) → space roles (wet / dry / service …)
7  Openings: door / window / sliding occurrences → host wall → width; height from source / raster / BUDGET
8  Structure (Alsenan): hand-transcribed schedules (from the PDF) + DXF tags → occurrences → concrete
9  Rebar: bar definitions × occurrence geometry → bar sets → D²/162 kg/m → BBS cutting (12 m stock)
10 Rules: Urban methods + owner facts + project rules → heights, upturns, reveals, deductions
11 Release: each line gets TECHNICAL class (in/out of total) + COMMERCIAL class (provisional range)
12 Validation: FINAL_QA checks, invariants, freeze twice (byte-identical), Qortuba regression
13 Output: JSON registers (tests/alsenan/registers_v3b/*, data/reports/...) → XLSX / PDF (Reporting V3)
14 (Not connected) Firestore boqItems via pm_sync — used only by the old manual-takeoff pipeline
15 Post-freeze only: benchmark comparison (freelancer / contractor) — never fed back as a target
```

**Differences from the plan:**

* Step 8 relies on **hand transcription by Claude Code during development**, recorded as Python constants such as `CB_TRANSCRIPTION`. There is no automatic schedule reader for raster schedules.
* No step calls an LLM.
* The benchmark is read only after the freeze (`benchmark_firewall.py`).

---
## 5. Agent inventory

**Count.** There are **17 code agents** (A1–A17) plus `agents/_template`. Each code agent has `prompt.md`, `schema.py` (a dataclass schema with validation), `agent.py` and `tests/`.

**Runner and model tiers.** The shared runner is `agents/base.py`. The model tiers are CHEAP = `claude-haiku-4-5` (the default), REASONING = `claude-sonnet-5` and BEST = `claude-fable-5-1`. `ladder()` moves up a tier when the output fails schema validation.

**Tests.** There are 203 agent tests, all passing, and they run offline against stubbed model responses. Live use needs `ANTHROPIC_API_KEY`.

A18–A22 are **research protocol roles, not code agents**:

* A18: blind-input isolation contract (`engine/blind_input_contract.py`).
* A19: checker.
* A20: unused.
* A21: visual trace (`docs/A21_VISUAL_TRACE_ARCHITECTURE.md`, `research/a21_*`).
* A22: structural comparison.

**Biggest change from the original 17-agent design.** A1 Extractor and A2 Reviewer were meant to measure drawings. **No current QTO output comes from them.** All Alsenan / Qortuba / R8 quantities are deterministic code. A1 / A2 were used in "Run 1" on 23010 (`docs/RUN1_ACCEPTANCE.md`) and remain experimental.

| # | Agent (path) | Responsibility | Inputs → outputs | LLM? | Deterministic part | Calls / called by | Status |
|---|---|---|---|---|---|---|---|
| A1 | `agents/a1_extractor` | read a drawing / schedule into measurement records | image / text → records (item, unit, dims, `confidence` low / medium / high, citation) | yes | schema validation; E1 unit guard / E3 calculator downstream | called by tools / Run 1; nothing in the current QTO | experimental (102 tests) |
| A2 | `agents/a2_reviewer` | blind second takeoff + challenge | same drawing, never A1's output → records + disagreements | yes | imports A1 schema; E30 reconcile compares | Run 1 | experimental (22 tests) |
| A3 | `agents/a3_client` | WhatsApp replies in Kuwaiti Arabic | message → reply + intent | yes | schema | `integrations/whatsapp` | prototype |
| A4 | `agents/a4_followup` | re-engage quiet leads | lead history → message | yes | schema | orchestrator | prototype |
| A5 | `agents/a5_faq` | consistent FAQ answers | question → answer | yes | schema | A3 | prototype |
| A6 | `agents/a6_planner` | work breakdown / dependencies | project scope → activities | yes | E12 schedule computes dates | `pipeline/create_project.py` | prototype |
| A7 | `agents/a7_quotation` | Arabic quotation / contract text | approved BOQ + terms → clause text (**no numbers**; numbers come from E22 documents) | yes | E22 renders | tools/documents | prototype (17 tests) |
| A8 | `agents/a8_briefer` | owner daily / weekly brief | events → brief | yes | schema | orchestrator | prototype |
| A9 | `agents/a9_orchestrator` | route events / priorities | event → route | yes (prompt); `pipeline/orchestrator.py` is deterministic | — | — | prototype |
| A10 | `agents/a10_content` | Instagram captions | brief → captions | yes | — | A15 / A16 | prototype |
| A11 | `agents/a11_site_progress` | site WhatsApp photos → progress log | photos / messages → log | yes | — | integrations | prototype |
| A12 | `agents/a12_call_summariser` | call → lead record | transcript → record | yes | — | — | prototype |
| A13 | `agents/a13_contract_reader` | signed contract → deadline alerts | contract → terms | yes | E6 alerts | — | prototype |
| A14 | `agents/a14_ig_analyst` | Instagram analytics | metrics → findings | yes | — | A15 | prototype |
| A15 | `agents/a15_marketing` | content plan | A14 findings → plan | yes | — | A16 | prototype |
| A16 | `agents/a16_post_designer` | post assets brief | plan → brief / caption / poll | yes | — | tools/grid | prototype (17 tests) |
| A17 | `agents/a17_campaign` | per-build campaign | build + stage → campaign | yes | E21 campaign | tools/campaign | prototype (13 tests) |

**Other places an LLM is used.** These sit outside the agent folders:

* `engine/document_reader.py` (E89): a model reads image crops of the 23010 sheet (title block / notes), cached in `data/golden/23010/doc_read_cache`.
* `engine/semantic_compare.py` and `engine/group_registry.py` import agent labels.

**Ownership findings**

* **Tasks with no owner:**
  * schedule / table reading for structural drawings (done by hand transcription);
  * population completeness;
  * revision delta at entity level;
  * pushing QTO into Firestore.
* **Overlap:** A1 / A2 overlap with the deterministic engines, which now do their job. A9 (prompt) overlaps with `pipeline/orchestrator.py` (code).
* **Probably unnecessary for QTO:** A1 / A2 as quantity producers. Keep them, if at all, as readers of raster schedules with confidence, never as the quantity authority.
* **Missing:** a schedule-reader component (deterministic + OCR) and a "plan-vs-schedule mismatch → RFI" generator (V3c §C.E).

---

## 6. E-module inventory

**What an E-module is.** It is a deterministic Python module in `engine/`, identified by an `E<n>` tag at the top of its docstring. There are no model calls, except E89.

**Exact count.** Measured by parsing module docstrings:

* **99 distinct E-ids** across **145 files**.
* Caveat: the id "E1" is overloaded. It is the original *E1 Unit Guard*, and also the tag on 42 modules from the research round called "E1.x" (E1.1–E1.4 foundation work).

There are also two families with **no E-id**:

* `engine/source/*` (95 files): the R8 / V3 generation, which is the current core.
* Supporting packages: `engine/qs_core/*` (22), `engine/ingest/*` (35), `engine/reporting_v2|v3/*` (7 + 7), `engine/audit/*` (8).

In total there are 424 `.py` files under `engine/`, 250 of them at the top level.

| Category | Modules (E-id → file) | Purpose | Status |
|---|---|---|---|
| **Units / QA core** | E1 `unit_guard.py`, E3 `calculator.py`, E5 `audit_log.py`, E28 `completeness.py`, E30 `reconcile.py`, E33 `release.py`, E44 `quantity_trace.py`, E48 `takeoff_status.py`, E49 `findings.py`, E50 `run_manifest.py`, E83 `release_blocker.py`, E85 `freeze_guard.py`; `engine/source/frame.py`, `conservation.py`, `release_model.py`, `run_manifest.py` | unit safety, totals, release, freeze | E1 / E3 legacy but valid; **source/** versions are current |
| **CAD** | `cad_adapter.py` (no E-id, **legacy, defective**), `cad_geometry.py`, `cad_entity_role.py`, `cad_trace_registration.py`; **`engine/source/cad/` (K1 kernel, kernel_ocs, libredwg_map, kernel_ezdxf, text)**, `capability.py`, `decoder_pins.py`, `cad_profile.py`, `qualification.py`, `digests.py`, `observations.py`, `realised.py` | decode, realise, account | K1 / K2 = current; cad_adapter = superseded but still imported |
| **Geometry / topology (PDF and CAD, 23010 / P7757 rounds)** | E23 `geometry.py`, E25 `walls.py` / `wall_model.py`, E31A–E31E `planar.py`, `face_qa.py`, `local_topology.py`, `space_boundary.py`, `space_graph.py`, E39 `envelope.py`, E42 `connectivity.py`, E43 `wall_stitching.py`, E47 `space_model.py`, E51–E56 (lengths, bbox, area_accuracy, space_identity, clear_internal, face_nesting), E59–E61 (falsifiers, wall_solid, free_space), E64–E81 (topology signals, unpaired strokes, leak map, snap tolerance, wall authority, junction patch, counterfactual, snap topology, space recall, blob causes, fragment recovery), E86, E90–E93, E96–E102 (enclosure, space topologies, portal fixtures) | room / space recovery research on 23010 and P7757 | **legacy research stack.** Valuable history, many partly superseded by `engine/source/topology*.py`, `wall_bands.py`, `room_topology_v3.py` |
| **PDF** | E41 `vector_source.py`, E87 `raster_topology.py`, E88 `glyph_text.py`, E89 `document_reader.py` (LLM), E23F `frames.py`, E95 `hybrid_path.py`, E63 `document_observations.py`, E94 `dimension_check.py`, `raster_qa.py`; `engine/source/raster_evidence.py` | vector paths, raster spaces, glyph text, frames, calibrated heights | experimental; 23010-centred, plus Alsenan raster heights |
| **Architecture / finishes** | E34 `openings.py`, E38 `heights.py`, E27 `trade_rules.py`, `plaster_trade_engine.py`, `wall_treatment_engine.py`, `parapet_assembly.py`; **source/**: `wall_faces_v2.py`, `wall_height.py`, `finish_height_v3.py`, `reveal_finish.py`, `opening_reveals.py`, `opening_register.py`, `opening_completion.py`, `door_transition.py`, `waterproofing.py`, `waterproofing_policy.py`, `trade_regions.py`, `trade_strips.py`, `corner_bead.py`, `exposed_finish.py`, `marble_thresholds.py`, `room_matrix.py`, `curved_opening.py` | finishes, WP, skirting, reveals | source/ = current; plaster / wall_treatment = PA-era with boundary debt |
| **Structural** | E2 `bbs_steel.py` (schedule → kg, ratio only as a sanity check); **source/**: `structural_schedule.py`, `structural_qto.py` (forbids kg/m³ keys), `structural_vertical.py`, `beam_binding.py`, `slab_region.py`, `slab_rebar_binding.py`, `concrete_model.py`, `bbs_optimiser.py`, `schedule_table.py` | concrete, rebar | current but **project runners in research/** hold the transcriptions |
| **Rules** | E27 `trade_rules.py`, `rule_library.py`, `urban_methods.py`, `urban_methods_v3.py`, `owner_facts.py`, `owner_method_facts.py`, `owner_claims.py`, `owner_scope.py` | rules | see §15 |
| **Revision** | E11 `revision_delta.py` (BOQ-line diff), E46 `revision_entities.py` (entity identity across revisions), `engine/source/canonical_input.py` | revisions | partial |
| **Output / data** | E14 `pm_sync.py` + `boq_formula.py`, E22 `documents.py`, E40 `qa_workbook.py` / `qa_writer.py`, E45 `templates.py`, `export_provenance.py`, `reporting_v2/*`, `reporting_v3/*`, `engine/source/boq_canonical.py`, `boq_report.py` | XLSX / PDF / Firestore docs | reporting = working; pm_sync = not wired to QTO |
| **Business (not QTO)** | E4 `rate_library.py`, E6 `alerts.py`, E7 phase-0 auditor (`engine/audit/*`), E8 `waste.py`, E9 `cooling.py`, E10 `funnel.py`, E12 `schedule.py`, E13 `benchmark.py`, E15 `finance.py`, E17 `preliminaries.py`, E18 `subcontractor.py`, E20 `estimate_actual.py`, E21 `campaign.py` | pricing / business | outside QTO; pricing must stay separate (§32) |

**Not built.** E16 (Instagram collector) and E19 (productivity benchmarks) are planned in `docs/ARCHITECTURE.md`. E35–E37 appear only in `docs/PHASE2_PLAN.md` (planned).

**Duplicates / consolidation candidates**

* `walls.py` / `wall_model.py` / `wall_graph` / `source/wall_bands.py` / `source/wall_faces*.py`
* `room_topology.py` / `room_topology_v3.py`
* `text_role.py` / `text_role_v3.py`
* `finish_height.py` / `finish_height_v3.py`
* `urban_methods.py` / `urban_methods_v3.py`
* `release.py` / `release_matrix.py` / `e1_release.py` / `source/release_model.py`
* `run_manifest.py` in both `engine/` and `engine/source/`
* `cad_adapter.py` vs K1

**Dead or near-dead.** The `round2`–`round6e` self-test modules, plus the fixture modules `enclosure_fixtures.py` and `portal_topology_fixtures.py`, are used only by their own tests.

---

## 7. DWG / DXF status

### Path

* **DWG** → self-built **LibreDWG 0.13.3 `dwgread`** → JSON (route **D1**), mapped by `engine/source/cad/libredwg_map.py`. Only fields that have been verified are mapped. The decoder binary is pinned by sha (`fe49cf28…`) in `engine/source/decoder_pins.py`.
  * The binary is present in this container at `/tmp/ldwg/programs/dwgread`, and its sha256 matches the pin. It lives in `/tmp`, **outside the repository**, so a fresh machine must rebuild it with the configure line recorded in `decoder_pins.py`. The cached decodes are in `data/runs/cad_convert/` (not in the ZIP; 1 GB).
* **DXF** → **ezdxf 1.4.4** (route **K2**, `kernel_ezdxf.py`). It is used for Qortuba REV_NEW and Alsenan P7757.dxf.
* **Not used:** ODA File Converter, AutoCAD COM, or any cloud converter. An independent AutoCAD / ODA DXF export to cross-check LibreDWG is **BLOCKED_EXTERNAL_INPUT**: it needs Mohammad to export from AutoCAD.
* **Realisation:** the observations go to the **K1** kernel (custom code, stdlib only) for placement.

### Entity support (`engine/source/capability.py` + census)

| Entity | Status | Notes |
|---|---|---|
| LINE | **Fully supported** (REALISED_EXACT, FINAL_GEOMETRY) | |
| LWPOLYLINE (incl. bulge) | **Fully supported** | bulge side corrected under reflection in K1 |
| POLYLINE (old 2D / 3D) | **Not in the register; status unknown / unsupported** | not observed as a blocker on the 3 projects. A gap to close. |
| ARC | **Fully supported** in K1 | **broken in cad_adapter** (mirror) |
| CIRCLE | **Fully supported** | |
| ELLIPSE | **Partial**: realised exactly, but PREVIEW only | downstream measurement cannot consume it. Al Rashed has 319, 6 with normal (0,0,−1). |
| Elliptical arc from non-uniform INSERT scale | **Partial** (PREVIEW) | cad_adapter turns it into a circle (defect) |
| SPLINE | **Parsed but ignored** (NOT_MAPPED / SKIPPED, counted) | |
| HATCH | **Carried as an anchor only** (no area use) | 226 on Al Rashed |
| INSERT / BLOCK | **Fully supported** (composed affine, base point, lineage) | |
| Nested blocks | **Fully supported** | tested to several levels, including double reflection |
| Anonymous / dynamic blocks (`*U`) | **Supported with findings** | 52 `*U` blocks / 235 inserts on Al Rashed |
| MINSERT | **Unsupported** (NOT_REALISED, REVIEW_ONLY) | D1 mapping unverified; ezdxf realises it wrongly under a reflecting parent. There are 0 MINSERTs in the real files. |
| XREF | **Unsupported** (XREF_NOT_RESOLVED, four-state model, recorded, never silent) | 0 in the real files |
| TEXT / MTEXT | **Carried** (anchors, roles, legacy Arabic decode) | MTEXT control codes not fully decoded in cad_adapter (defect) |
| ATTRIB / ATTDEF | **Carried** | |
| DIMENSION | **Carried** (value + definition points) | rotated linear projection is wrong in cad_adapter. Dimensions are **evidence**, not geometry. |
| LEADER / MLEADER | **Not in the register; ignored** | |
| SOLID | **REVIEW_ONLY** (UNVERIFIED_FOR_QTO_USE) | 124 on Al Rashed |
| 3DFACE | **Not in the register** | not relevant on the current plans |
| WIPEOUT, IMAGE, REGION, OLE2FRAME, custom classes | **Parsed but ignored** (NOT_MAPPED → SKIPPED, counted) | |
| ACAD_PROXY_ENTITY | **PROXY (not realised)** | |
| Invisible entities | **HIDDEN** (not realised) | **cad_adapter realises them**: 6,211 segments + 1,932 arcs on Al Rashed |

---

## 8. CAD transformation status

### K1 (`engine/source/cad/kernel.py`, `kernel_ocs.py`): custom code

| Transform | K1 handling | Exactness |
|---|---|---|
| Translation, rotation, X / Y / Z scale | composed 3×3 / 4×4 affine per INSERT chain: `T(ins) · R(rot) · S(sx, sy, sz) · T(−base)` | exact (float64) |
| Negative scale / mirroring | determinant of the full composed map; reflection flips the arc sweep and the bulge sign | exact |
| Block base points | subtracted before scale / rotate | exact (0 non-zero base points on Al Rashed) |
| Nested transforms | full product down the chain; lineage kept (insert handle path) | exact |
| OCS / WCS / extrusion / normals | arbitrary-axis algorithm in `kernel_ocs.py`; **fail-closed** on an unreadable or degenerate extrusion (a finding, never a silent identity) | exact |
| Arcs under transforms | **curves by point mapping**: start / end / mid mapped through the full map; the direction comes from the det sign | exact for similarity maps; a non-uniform map produces an ellipse (PREVIEW) |
| Ellipses | exact parametric mapping; PREVIEW only for QTO | exact geometry, not consumed |
| Bulge polylines | bulge to arc, mapped; sign flipped under reflection | exact |
| MINSERT grids | **not realised** (REVIEW_ONLY) | — |
| XREF | **not resolved** (recorded) | — |

**K2 (ezdxf).** ezdxf's own `virtual_entities` / transform does the work. It has known library failures: MINSERT yields the first cell only; xref INSERT yields nothing; MINSERT under a reflecting parent puts the rows on the wrong side. These are pinned in DONORS.lock and register LIBRARY_KNOWN_FAILURE. K1 and K2 are cross-checked (R8.8 cross-route).

**Legacy `engine/cad_adapter.py`.** Hand-written, **known-defective**, and frozen as is:

* adds the rotation to the arc angles under a reflection;
* ignores OCS / extrusion;
* ignores base points;
* does not expand MINSERT;
* fails open on frame;
* silent XREF;
* non-uniform-scale arc as a circle;
* rotated dimension projection;
* MTEXT codes not decoded;
* realises invisible geometry;
* places nameless block content at top level;
* OLE2FRAME type-2 drop;
* places unowned entities in model space;
* handle identity collision.

---

## 9. Mirrored ARC bug status

| Question | Answer |
|---|---|
| Fixed? | **Fixed in K1 (R8.1). NOT fixed in `engine/cad_adapter.py`**, which is still imported by legacy paths (ingest harness, `cad_measure`, round self-tests, `research/qs_wall_treatment_01`). |
| Fixing code | `engine/source/cad/kernel.py` (curve mapping through the composed map; sweep direction from `det`) |
| Root cause | `cad_adapter.py` L688–695 adds the composed **rotation** to the arc start / end angles even when the map contains a **reflection**. A reflection is applied as a rotation. This is mutation MT-02 in the register. Worked example: local centre (1000, 0), r 500, 0°→90°, mirrored in X. Truth: start (−1500, 0), end (−1000, 500), mid (−1353.553, +353.553), clockwise. cad_adapter gives end (−1000, −500), mid y −353.553, counter-clockwise: the "180→270" symptom. |
| Tests | `tests/r8_0` fixtures (hand-derived truth + ezdxf oracle + reference realiser) and `tests/r8_1` (330 tests, incl. real-K1 mutations MT-01 / 02 / 03 / 49 that break K1 and must be caught) |
| Nested mirrored arcs | **tested, pass on K1** |
| Negative X scale | **tested, pass** |
| Negative Y scale | **tested, pass** |
| Negative X + Y (double reflection = rotation 180°) | **tested, pass** (control: the reflections cancel) |
| Reflection + rotation | **tested, pass** |
| Reflected block inside reflected block | **tested, pass** |
| cad_adapter | **still wrong**: XFAIL `KNOWN_DEFECT` MIRRORED_ARC_SWEEP ×8, MIRRORED_BULGE_SIDE ×7 (pinned; they would XPASS-fail if someone "fixed" the adapter without moving the register) |
| Real exposure | Al Rashed: 46 realised arcs in mirrored placements (18 unique), all wrong in cad_adapter. P7757: 10–11 wrong. Door swings / hinge side are affected on any path still using cad_adapter. |

**Bottom line.** The *kernel* is correct and tested. The *system* is safe only on paths that use K1 / K2. Retiring `cad_adapter` (or routing it through K1) is **not done**. The R8.5 verdict was MIGRATION_PLANNING_READY YES, EXECUTION NO.

---

## 10. Donor repository status

Sources: `research/external_engine_lab/DONORS.lock` (reviewed 2026-09-30) and the V3c re-audit of 2026-10-04 (`research/external_engine_lab/V3C_FORENSIC_ACCURACY_DONOR_AUDIT.md` §C).

* **No donor is a runtime dependency.**
* **No donor code is imported by `engine/`.**
* One small COPY_ADAPT exists: the `labels.py:plain` text-cleanup idea from U-C4N (MIT, notice kept), placed in `engine/source/cad/text`.
* Everything else is clean reimplementation or ideas.
* **Urban remains independent.**
* The only third-party runtime libraries are ezdxf 1.4.4 (MIT, K2 only), shapely (lab adapters), PyMuPDF (PDF) and openpyxl. LibreDWG is GPL and is used as an **external binary** producing JSON, so it is not linked.

| Donor | Purpose | What was used | Rejected | Licence | Class |
|---|---|---|---|---|---|
| U-C4N/Autocad-MCP @cdb1063 | CAD source / transform, OCS, snapshot / diff / topology | OCS algorithm reference → clean reimplementation in `kernel_ocs.py`; skip / MINSERT / XREF explicit-record rules; text plain → `cad/text` | `unit_of` (inferred unit overrides INSUNITS, mm default); silent identity on a bad extrusion; hand-rolled planar faces; P&ID network as wall topology. **Not yet taken:** the handle-stability gate for diffs | MIT | **Strong donor** |
| Kentucky-ai/OpenTakeoff @e6d2251 (locked; head beaa4fe is 34 commits newer) | PDF / document / schedule, One-Click rooms | stance: no quantity without a confirmed scale; candidate-generator only; gating doc. V3c recommends: named `confidence_factors`, the PROOF overlay discipline, the click-stability metric, "schedule scan never drops a row silently", raster-schedule OCR with misread repair (new) | flood fill as a measurement route; quantities on unconfirmed scale; mixed-scale warn-not-block; silent row drop | Apache-2.0 | **Strong donor (ideas)**, mostly **not yet implemented** |
| beiming183-cloud/AutoCAD-MCP @11f7c47 | CAD verification patterns | field-level readback diffs, revision anchors, digest pattern (Urban SRD-1 / RGD-1), endpoint topology. **Missed:** UNASSIGNED_ENTITY / MISSING_SEMANTIC_FIELD ("everything must be claimed"), which would have caught D1 | `geometry_digest` as physical proof (OCS-blind) | MIT | **Useful donor** |
| Slacker-LLC/autocad-mcp @2723b4f | live AutoCAD COM readback (lab oracle) | reference only | unitless INSUNITS treated as mm | Apache-2.0 | Limited |
| puran-water/autocad-mcp | upstream of beiming183 | benchmark reference | — | MIT | Limited |
| ahmetcemkaraca/AutoCAD_MCP, vigneshpbmenon/autocad-mcp-server | MCP servers | inspected | everything | MIT | Not useful |
| **christiannp/autocad** | — | — | — | unknown | **Inaccessible** (UNRESOLVED_EXTERNAL_REPOSITORY) |
| datadrivenconstruction/OpenConstructionERP | ERP | idea: decoder binary pinning | all code / text | **AGPL-3.0** | Idea only |
| v-Zak/bar-bending-scheduler, thuanlm-eng/steel-bar-takeoff, divyanshu964/Rebar-Pdf-Extractor, xu323/Rebar-Material-Schedule-OCR-Pipeline | rebar | ideas: schedule-first orientation, per-Ø summary + % share (used in V3c §A.2), merged-cell table geometry + per-cell OCR confidence (xu323: best idea for the FF merged cell) | LLM-as-parser; permissive regexes | **no licence (all rights reserved)** | Useful ideas only; **no copy** |
| ContractorKeith/conmcp | deterministic sheet classification, plan-vs-schedule mismatch → RFI | idea (not implemented) | — | MIT | Useful |
| hamzaabduljabbar/autoConst | index-once DB, confidence hierarchy, envelope sanity | ideas only | code / schema text (product restriction) | source-available, no resale | Useful ideas |

---

## 11. Units / frame architecture

**Current terminology** (`engine/source/frame.py`):

* **UNIT_CONTEXT**: what we know about the drawing unit. It comes from INSUNITS (a *declaration*), DIMLFAC (a *candidate*), dimension-vs-geometry ratios, wall-pair spacing, and **human claims**. The status is CONFIRMED / UNCONFIRMED / CONFLICT.
* **REGION_MEASUREMENT_TRANSFORM**: the per-region (viewport / drawing-region) scale from drawing units to metres.
* **MEASUREMENT_FRAME**: the combination of the two. It decides the **release level** of every value:
  * CONFIRMED → FINAL allowed;
  * UNCONFIRMED → PREVIEW (shadow) only;
  * CONFLICT → **COUNT_ONLY**: counts are allowed and every physical value is `VALUE_NOT_COMPUTABLE`.
* "PHYSICAL_FRAME" is an older name and is not used in `engine/source/`.

| Source | Handling |
|---|---|
| DWG / DXF INSUNITS | read as **declaration evidence only**; it never authorises a unit on its own |
| mm / cm / m / inch / feet | a factor table to metres, applied **once**, at measurement time, through the frame. Geometry stays in drawing units until then. |
| DIMLFAC | **candidate only**. It can raise a question; it can never confirm or change a status. |
| Human claim | `data/registry/OWNER_UNIT_CLAIMS.json`: versioned, bound to the exact file sha256, non-transferable to another revision, supersession recorded |
| Model space vs layout / viewport | only model space is measured. Layout viewport scale is not used for physical values. Regions are designated (R8.4 reference-region designation). |
| PDF points | `engine/vector_source.py` keeps page units (pt). Scale comes from a printed dimension (23010: one 40.00 m dimension, checked on one 25.00 m dimension, residual 2.37 mm). Calibration is **single-sheet**; the two-axis affine fit is **open**. |
| Raster pixel scale | `engine/source/raster_evidence.py`: sheet calibration from printed level chains; grades PRINTED / SCALED; width gate; content-addressed claims |

**Risk questions**

* **Converting twice:** guarded. Conversion happens only at the frame boundary, and tests assert idempotence. *Residual risk:* legacy `cad_adapter` / ingest paths have their own `engine/ingest/units.py` with a `TO_BASE` table, so mixed paths could double-convert. This has not been audited end to end.
* **Assuming metres wrongly:** prevented in `engine/source` (no default unit; fail closed). The old R7 / qs_core engine (§255 of `docs/ENGINEERING_INVARIANTS.md`) **did** let a declared metre unit overrule INSUNITS on wall-band evidence. That engine still exists.
* **Inches read as metres:** this is exactly the Al Rashed case. It is now caught as CONFLICT.
* **Trusting bad INSUNITS:** prevented (declaration only).
* **DIMLFAC contamination:** prevented (candidate only).
* **Model / layout confusion:** model space only. Layouts are not measured.

### Al Rashed unit issue

| Item | Value |
|---|---|
| File | Al Rashed villa DWG sha `299c61b1…` → `data/runs/cad_convert/ALRASHED_ARCHITECTURAL.json` |
| INSUNITS | **1 (inches)** |
| DIMLFAC | header 1.0. The dimension style shows **DIMLFAC 100**. 504 dimensions display 100× their geometric length (metres drawn, cm shown). |
| Physical evidence | wall pairs are 5.1 mm apart if read as inches, and **200 mm if read as metres**. The implied-unit candidate set {100, 1000, 100000, 2540, 30480} mm per unit excludes 25.4 (inch). |
| Interpretation adopted | **None automatically.** UNIT_CONTEXT = **CONFLICT → COUNT_ONLY**. Every physical value is VALUE_NOT_COMPUTABLE. Owner action **RESOLVE_ALRASHED_UNIT is OPEN**. |
| Old behaviour | R7 / qs_core accepted "metres" from wall-band evidence. The R7 Al Rashed numbers (§17) were produced under that assumption and are for orientation only. |
| Generic or project-specific | **Generic** (frame policy, no project constant). The only project-specific input would be an owner claim bound to that sha. |

---

## 12. Architectural BOQ

Evidence comes from Qortuba RC1 (apartment, REV_NEW, **SHADOW / RC1_REFERENCE**) and Alsenan V3b (villa, **FULL-BOQ CANDIDATE, not FINAL**). Status words: **PR** production-ready · **IT** implemented, needs more testing · **P** partial · **PL** planned · **M** missing. **Nothing is PR.**

Alsenan V3b line counts per trade (389 lines). Technical coverage = (full + 0.5 × partial) / items.

| Trade | Items | COMPUTED | PARTIAL | BLOCKED | REVIEW | Technical coverage | Commercial coverage |
|---|---|---|---|---|---|---|---|
| Concrete | 42 lines / 40 items | 20 | 6 | 14 | 2 | 57.5% | 97.5% |
| Rebar | 30 / 28 | 5 | 14 | 11 | 0 | 39.3% | 96.4% |
| Blockwork | 19 | 14 | 4 | 1 | 0 | 84.2% | 100% |
| Plaster / paint | 73 / 67 | 3 | 3 | **67** | 0 | **6.7%** | 100% (64 provisional) |
| Flooring | 41 / 40 | 39 | 0 | 1 | 1 | 97.5% | 100% |
| Ceilings | 51 / 26 | 25 | 0 | 0 | 25 | 96.2% | 96.2% |
| Wall tile / WP | 100 / 87 | 63 | 0 | 37 | 0 | 57.5% | 100% |
| Aluminium / openings | 27 | 20 | 4 | 3 | 0 | 81.5% | 100% |
| Stairs / railings | 6 | 2 | 0 | 4 | 0 | 33.3% | 100% |

"Commercial coverage 100%" means a value exists, **often a labelled provisional or BUDGET_ESTIMATE**. It does not mean a measured value.

| Category | Status | How it is detected / calculated |
|---|---|---|
| Floor area: room-by-room | **IT** | vector closure of wall faces → clear internal polygon; RC1 room matrix proves that the rooms sum to the trade totals |
| Floor-by-floor, total internal | **IT** | sum of spaces per level; floor closure invariant (INV-07) |
| Wet / dry rooms | **P** | role from text labels (Arabic / English aliases). **Fails when a closure merges a wet room into a dry zone** (Alsenan L-17). |
| External areas, balconies, terraces | **P** | courtyard / roof / terrace handled as separate scopes on Alsenan. GARDEN can leak into a floor zone. |
| Room perimeter | **IT** | face-path length per space |
| Wall lengths / wall surface | **P** | wall bands → faces × height authority (`wall_height.py`, `finish_height_v3.py`: interval − member depth, or an owner height) |
| Internal / external walls | **P** | envelope + band side; facades single-route (L-6) |
| Openings / deductions | **IT** | opening register, full deduction (US-06), reveals 0.25 m L / R / top (US-07). **Heights are often BUDGET.** |
| Plaster (wall, deductions, wet / dry) | **P** | NET plaster to the masonry termination (method PLASTER-TO-MASONRY-TERMINATION); height basis disputed (OQ-10: soffit vs false ceiling, ±18.8%) |
| Paint (walls, ceiling, deductions) | **P** | PAINT-TO-FINISHED-CEILING. Ceiling paint = ceiling area when specified. |
| Ceramic floor / wall tiles (bath, kitchen, laundry, ironing, pantry, other wet) | **P** | wet floor = space area; wall tile to full height (WET-WALL-TILE-FULL-HEIGHT) or the owner height (Qortuba 3.0 / 3.2 m) minus openings + reveals. Pantry = OPEN_AMERICAN on P7757; WP room types enumerated (US-14). **Missing wet rooms → missing tile** (Alsenan −14.9%). |
| Ceiling by room / floor totals | **IT** | ceiling = room area (US-15), with material pending |
| Skirting normal / hidden + profile | **IT** (Qortuba) / **P** (Alsenan) | skirting path engine (V2 / V4): along the dry-room faces, door widths excluded, continuous under windows (RC1). Hidden skirting and profile on the same path (US-08). Normal skirting rate = half of hidden is a **rate rule**, not a quantity. L-18: may run along void / railing edges (suspected). |
| Waterproofing: floor, upturns, perimeter, door rule | **IT** | WP = floor membrane + 0.15 m upturn (US-04 / UP-WP); upturn not broken at doorways (US-05); roof upturn 0.20 m (ROOF-WATERPROOF-UPTURN-200). Roof WP books flat + upturn m² together (L-2: inconsistent with wet-room WP). |
| Blockwork 100 / 150 / 200 / other, deductions | **P** | thickness from band width, with a **material claim required** (masonry identity before measurement). Opening deductions per wall line (INV-19). **Alsenan ≈140 m short.** Parapet height basis 0.50 (OQ-8). 100 mm: supported if drawn. |
| Doors (internal PVC, main, aluminium external, count / width / height / area) | **P** | door occurrence (block / arc / jamb motif), host wall, width from geometry. Height: source → raster → owner (QP-21 2.2) → TD-02 2.2 fallback. Material: US-13 interior PVC / exterior aluminium. |
| Windows (count / width / height / area / room / floor / aluminium) | **P** | window occurrence → host (side-aware), width from geometry. Height: source / raster / BUDGET (US-11 says no default). Alsenan: 26 / 33 heights are budget estimates. |
| Stairs (risers, treads, area, handrail, landing, lm) | **P** | STAIR_CONCRETE_V2 independent riser / tread counts; curved bases; Alsenan stair handrail 19.124 lm (+0.9% vs freelancer); concrete stairs only provisional; entrance / second stair possibly missing (OQ-5) |

---

## 13. Structural BOQ

All of this is on Alsenan P7757 / ST7757 only. The structural schedules were **transcribed by hand** (by Claude Code, from PDF page images and DXF texts) into the Python constants in `research/external_engine_lab/alsenan_phase_a3.py`. The generic engines then compute occurrences and volumes. No other project has structural takeoff. Al Rashed structural is blocked by units.

| Element | Detection | Quantity | Source | Validation | Known limitations |
|---|---|---|---|---|---|
| Excavation | **M** | — | — | — | not implemented |
| Blinding | **IT** | founded footprint 288.276 m² × 0.10 + pool = 29.623 m³ | foundation plan | owner method OD-V3B-1 (full footprint) | freelancer uses the full plot (47.06 m³); scope decision |
| Footings | **IT** | 25 tags + F / F10: 66.306 m³ (C-FTG 64.346 PARTIAL + F / F10 1.96 provisional range 0.432–1.96) | SCHEDULE OF FOOTINGS + tags | matches the freelancer per type (+0.67, F3 double tag OQ-11) | 2 blocked |
| Raft | **M** | — | — | — | none on the projects |
| Foundation / strap beams | **IT** concrete | STB1–3 3.392 m³ (exact match) | strap rows + measured bands | — | **no rebar (D4)** |
| Ground beams | **IT** | int 88.5 m + ext 110.3 m × 0.3 × 1.0 (provisional depth) = 44.33 m³ | p.13 sections | +6.35 vs freelancer, method difference | ext depth provisional |
| Necks | **P** | 6.25 m³ (median fallback) | schedule | −2.56 | per-type section not used |
| Columns | **IT** | 31.405 m³ (storey interval incl. joints + residue) | column schedule + plans | method proven | 13 2F columns not drawn (OQ-13); rebar uses a different filter (D5) |
| Beams + slabs + lintels | **IT** | 123.768 m³ (downstand B × (D − t) + net plate + lintels) | schedules + plans | sum within −1.6% of the freelancer | split differs by convention |
| Ground slab | **P / defect** | 11.54 m³ (two labelled cells) | label binding | **D6**: smallest-cell binding, should be ≈295 m² | OQ-2 |
| Stairs | **P** | 5.231 m³ (2 flights, provisional) | arch / struct | −9.82 vs freelancer | extra stairs probably missing |
| Domes | **IT** | shells 7.52 + ring beams 5.97 (D 0.75 provisional) | details | — | ring depth provisional |
| Pool | **P** | 5.053 m³ | details | −7.30 | pump room missing (OQ-6) |
| Retaining walls / elevator walls | **M** / owner-gated | 0 | — | — | elevator walls OQ-1 |
| Concrete total | — | **316.058 m³** vs freelancer 352.436 (−10.3%, reconciled row by row to 0.01 m³) | | | |
| Formwork | **M** | — | — | — | not implemented |
| Structural steel | **M** | — | — | — | not relevant so far |

---

## 14. Rebar

**Verdict.** It **is a true bar-by-bar takeoff engine**, not a weight-ratio converter:

* `engine/source/structural_qto.py` **forbids** the `kg_per_m3` / `ratio` keys in a quantity;
* E2 `bbs_steel.py` keeps the ratio as a sanity check only.

But it is **incomplete in population coverage**, and it relies on **hand-transcribed schedules**.

**Unit weight.** `kg/m = D² / 162` with D in mm, implemented in `research/external_engine_lab/alsenan_v3b_rebar.py:22` and `alsenan_v3b_struct.py:35`. This equals 0.006173 D², about 0.08% above πD²/4 × 7850 = 0.006165 D². kg → t is ÷1000 with **no early rounding**. NET, PROCUREMENT (BBS purchased) and PARTIAL bases are shown separately and **never summed** (UNIT_CONTROL gate).

| Population | Implemented? | Extraction | Needed annotation | Missing info → |
|---|---|---|---|---|
| Footing bottom / top mesh | **yes, defective** | schedule row (count / Ø / spacing) × footing side − 2 × 7 cm cover | footing schedule | **D2:** per-metre counts used as absolute; **D3:** FF merged cell → **no row (silent)**; boxed bars G1 BLOCKED |
| Strap beams | **no (D4)** | — | SB schedule exists | silently absent |
| Ground beams | yes | bar sets by detail (3 + 3 layers ×2) | p.13 | — |
| Column verticals + ties | yes, **over-count (D5)** | schedule bars; ties `ceil(6 × interval)`; starters; splice 40Ø / floor | column schedule | 17 off-storey columns still get bars (+1.04 t) |
| Beam main / stirrups (simple beams) | yes | schedule top / bottom; stirrups `ceil(rate/m × clear)`; side bars as a separate role | beam schedule | inner links (box symbol) not modelled (G3, OQ-7) |
| **Continuous beams CB1–CB13** | **no (D1)** | bars never transcribed | "SCHEDULE OF CONTINUES BEAMS" p.11–12 | **silent skip, no BLOCKED row**, ≈2.2 t missing |
| Slab reinforcement | yes | `slab_rebar_binding.py`: annotation → parallel drawn bar → panel by ray casting; clear span + embedment; per-metre count; 123 annotations (92 bound, 12 partial, 8 detail, 7 text-only, 2 drawn-extent, 2 de-duplicated) | slab plans | UNBOUND never estimated; de-dup may hide two layers (OQ-9) |
| Ground slab mesh | yes, scope defect (D6) | 5Ø10/m E.W. on two cells | label | smallest-cell binding |
| Lintels | yes | lintel schedule, 5 / m links | schedule | — |
| Domes / pool | yes | details | details | pool geometry unresolved |
| Stairs | **BLOCKED** | — | no detail found | BLOCKED row (correct) |
| Raft / retaining wall | **no** | — | — | — |
| Distribution / additional bars | partially (side bars, REMARKS not parsed) | | | |

**Other supported details**

* **Bar parameters:** diameter, count, spacing (per-m and @), lengths (clear + embedment / anchorage), repetitions × occurrences.
* **Laps:** bars > 12 m are split with the project lap (tension 70Ø / compression 40Ø, from ST7757 p.8). Example: a 44.07 m boundary-wall bar gets 3 laps.
* **Cover:** 2.5 cm, or 7 cm against soil (p.8).
* **Hooks / bends:** `engine/source/bbs_optimiser.py` with ACI 318-19 Table 25.3.1 / 25.3.2 values. **The edition is not verified**, so these are PROVISIONAL_CODE_METHOD and not in the technical total.
* **Bar marks / shape codes:** **no shape-code library** (BS 8666 / ACI). Boxed and detail-shape bars are BLOCKED.
* **Development length** = the project lap rule. No code calculation.
* **Splice zones:** not modelled beyond the lap counts.
* **BBS cutting:** first-fit decreasing on 12 m stock with offcut reuse.
  * Technical view: used 13,986 kg, purchased 15,324 kg, waste 8.73%.
  * Commercial view: used 26,035 kg, purchased 27,537 kg, waste 5.46%.

**Totals (V3b frozen).** Net 26.24 t (26.56 incl. budget), purchased 27.537 t, vs freelancer 44.19 t. V3c proves that the freelancer's figure is **concrete × round kg/m³ allowances** (75 / 130 / 200 / 150 / 90 / 180 / 120) and not a measurement. After fixing D1–D6 and G1 / G2 / G3 / G6, Urban is estimated at **30–32 t** (≈34 t if stairs, elevator walls and pool are confirmed). This is a diagnostic estimate, not a quantity.

---

## 15. Urban rules

There are four rule stores. The full raw dump is in `HANDOFF_EXTRAS/rules_dump.txt` in the ZIP.

**Rule stores**

1. `data/experiments/…/URBAN_OWNER_RULES_V1` (gitignored; included in the ZIP extras where present): US-01..17, QP-01..23, TD, R-superseded.
2. `data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json` (44 rules, tracked).
3. `data/registry/URBAN_OWNER_METHOD_RULES.json` (7) plus `engine/source/urban_methods.py` / `urban_methods_v3.py` (code-level methods).
4. Project owner decisions (`research/external_engine_lab/alsenan_v3_owner_decisions.json`, `tests/alsenan/registers_v3b/OWNER_METHOD_REGISTER.json`).

### 15.1 Global Urban Projects rules (owner-declared standards)

| ID | Rule | Value | Trade | Implemented in |
|---|---|---|---|---|
| US-04 / UP-WP-001..004 | WP = floor membrane + upturn | 0.15 m upturn | WP | `waterproofing.py`, `waterproofing_policy.py` |
| US-05 | upturn not broken at the doorway | — | WP | same |
| US-06 | full opening deduction | — | plaster / paint / tile / block | opening register |
| US-07 | reveals 0.25 m L / R / top, no sill | 0.25 m | finishes | `opening_reveals.py`, `reveal_finish.py` |
| US-08 | hidden skirting + profile on the same path | — | skirting | skirting path engine |
| US-09 | normal skirting rate = ½ hidden | rate rule | **pricing** | not in QTO (correct) |
| US-10 | source dimensions override defaults | — | all | authority ladders |
| US-11 | no default window height | — | windows | opening heights → BUDGET / BLOCKED instead |
| US-13 | interior doors PVC, exterior aluminium | — | doors | opening classification |
| US-14 | enumerated WP room types incl. pantry | — | WP | role table |
| US-15 | ceiling by area | — | ceiling | room matrix |
| US-16 / 17 | open passage handling | — | floor / skirting | passage strips |
| UP-CER-001..008, UP-PANTRY-001..004, UP-STAIR-001..012, UP-ELEV-001..005, UP-VOCAB-001..005, UP-GEN-001..004, UP-QA-001 / 002 | rule library (ceramic, pantry, stair, elevator, vocabulary, general, QA) | various | various | `rule_library.py` + trade engines (partly) |
| Code methods | WET-WALL-TILE-FULL-HEIGHT; PLASTER-TO-MASONRY-TERMINATION; PAINT-TO-FINISHED-CEILING; ROOF-WATERPROOF-UPTURN-200 (0.20 m); FLOOR-FINISH-BEFORE-CABINETRY; curved glazing on the inner arc; COLUMN-HEIGHT-TO-CONTROLLING-MEMBER; BEAM-TYPE-FROM-SCHEDULE-LENGTH-FROM-PLAN; NON-OVERLAPPING-SLAB-BEAM-MODEL; FINISH-QUANTITY-INDEPENDENT-OF-MATERIAL; DRY-FLOOR-PORCELAIN-DEFAULT; WET-FLOOR-TILED; NO-SKIRTING-FULL-TILE-WET; CEILING-QUANTITY-WITHOUT-MATERIAL; REBAR-NET-AND-PROCUREMENT; FINISH-EXTRAS-SEPARATE-ITEMS | | | `urban_methods.py`, `urban_methods_v3.py` |
| Owner method rules (7) | WET-SERVICE-MARBLE-THRESHOLD, SKIRTING-OPENING-METHOD, WALL-FINISH-HEIGHT-METHOD, REVEAL-FINISH-METHOD, EXPOSED-COLUMN-FINISH, EXPOSED-INTERIOR-DUCT-FINISH, FLOOR-FINISH-BEFORE-CABINETRY | | | `URBAN_OWNER_METHOD_RULES.json` |

### 15.2 Project-specific rules

| ID | Project | Rule | Value |
|---|---|---|---|
| QP-01 | Qortuba | wall tile height | 3.0 m (PA08). RC1 uses 3.20 m (WTL-01, later owner fact). |
| QP-02 / 03 / 04 | Qortuba | blockwork / plaster / paint height | 3.0 m (PA08). RC1 plaster / paint to 3.15 m. |
| QP-10 / 11 | Qortuba | hidden skirting / profile | 76.389 lm (PA08). R8.17 notes: "never a target". |
| QP-12 / 19 / 21 / 23 | Qortuba | door / sliding-door heights | 2.2 m |
| QP-22 | Qortuba | window height | 1.5 m |
| (other QP-05..20) | Qortuba | see the dump | |
| P7757 project rules | Alsenan | pantry OPEN_AMERICAN; stair finish MARBLE; elevator none established | `data/registry/P7757_PROJECT_RULES.json` |
| OD-V3-1..10 | Alsenan | e.g. residential floor build-up fallback 0.10 m; finish qty independent of material; rebar net + procurement; extras as separate items | `alsenan_v3_owner_decisions.json` |
| OD-V3B-1..13 + OC-V3B-A..E | Alsenan | full-footprint blinding; project concrete grade / cement; NET payable basis; finish sequences; angle beads; reveals; cornice presence pending; two-layer release; waste pending; rebar detailing authority | `OWNER_METHOD_REGISTER.json`. Promotion class PROJECT_ONLY or URBAN_STANDARD_CANDIDATE, **none globalised** |
| 23010 | 23010 | heights, ceramic, plaster | `data/registry/23010_heights.json`, `data/trade_rules/23010_*.json` |

### 15.3 Test assumptions

* Synthetic fixtures use their own declared units, heights and tolerances.
* R8 hand-derived truth uses unit-less drawing coordinates.
* The determinism guard forbids project constants in production code (INV-09, test `no_comparison_input`).

### 15.4 Temporary fallbacks

| ID | Fallback | Value | Where it applies | Label |
|---|---|---|---|---|
| TD-01 | door width | 1.0 m | when no geometry | TEMPORARY_DEFAULT |
| TD-02 | door height | 2.2 m | when no source | TEMPORARY_DEFAULT |
| OD-V3-1 / RESIDENTIAL-FLOOR-BUILDUP-FALLBACK | floor build-up | 0.10 m | Alsenan | PROVISIONAL_URBAN_FALLBACK |
| neck median | neck section | median of types | Alsenan | provisional |
| ext GB depth | 1.0 m | Alsenan | provisional |
| dome ring depth | 0.75 m | Alsenan | provisional |
| parapet height | 0.50 m | Alsenan | owner question OQ-8 |
| ACI 318-19 hooks | table values | rebar | PROVISIONAL_CODE_METHOD |
| window heights | budget estimate | Alsenan 26 / 33 | BUDGET_ESTIMATE (commercial only) |

### 15.5 Superseded rules

* **R-02, R-05, R-07, R-09, R-13, R-17, R-26** (old Qortuba rules, superseded by US / QP).
* **QP-01 / 02 / 03 / 04 (3.0 m)**, superseded for RC1 by later owner facts (3.15 / 3.20).
* The **QP-10 76.389 lm** target, superseded (skirting is continuous under windows in RC1).
* **R7 "declared metre overrides INSUNITS"**, superseded by the R8 frame policy.

---
## 16. Qortuba benchmark

### 16.1 What the "ground truth" actually is (flagged)

There is **no independent survey** of Qortuba. Two references exist:

1. **The sealed benchmark** (`QORTUBA_BENCHMARK_SEAL.json`, BENCHMARK_PROJECT_01).
   * Source file: `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/pa08_qortuba_boq/QORTUBA_FINAL_PRE_PRICING_TAKEOFF.json`.
   * Built at git head `7aebc0a`, digest `f15e31bc6da05504`, on revision **REV_OLD** (DWG sha `2ec3a9c8…`).
   * This is **Urban's own PA08 takeoff after owner rules V1**, frozen and sealed. It is *not* an external measurement.
2. **The contractor's sheet.** This is the only external reference, and it has only 6 rows.

The current engine output is **RC1** (`data/reports/URBAN_QTO_QORTUBA_ARCHITECTURAL_RC1_FINAL/`). RC1 was built on **REV_NEW** (DXF sha `df0e1d69…`, which the owner declared authoritative) with **later owner facts** (plaster / paint to 3.15 m, wall tile to 3.20 m, skirting continuous under windows). **RC1 and the seal therefore differ by revision and by rules.** The table below is shown as requested, but most of the differences are *expected basis changes*, not engine errors.

* The seal is **unchanged**.
* PASS / FAIL uses a **±3% reading tolerance chosen here for the report**. No pre-declared tolerance exists for RC1-vs-seal.
* "BASIS" marks a known rule or revision change.

| Item | Ground truth (seal, REV_OLD) | Engine (RC1, REV_NEW) | Diff | % | PASS/FAIL |
|---|---|---|---|---|---|
| Dry floor porcelain | Q-13 108.9625 m² | FLR-01 111.8988 | +2.9363 | +2.69% | PASS (±3%); revision |
| Wet floor ceramic | Q-11 17.8625 m² | FLR-02 17.7425 | −0.1200 | −0.67% | PASS |
| Service floor ceramic | Q-12 11.685 m² | FLR-03 11.685 | 0 | 0.00% | PASS |
| Ceiling | Q-14 138.51 m² | CLG-01 140.637 | +2.127 | +1.54% | PASS |
| Plaster | Q-08 268.1731 m² (3.0 m) | PLS-01 307.3615 (3.15 m) | +39.188 | +14.61% | FAIL / **BASIS** (height alone → 281.58; the remaining +25.8 m² comes from the revision and face changes, not decomposed here) |
| Paint | Q-09 268.1731 m² | PNT-01 307.3615 | +39.188 | +14.61% | FAIL / BASIS (same) |
| Wall ceramic (bath 84.9 + service 24.9835) | Q-05 + Q-06 = 109.8835 m² (3.0 m) | WTL-01 127.6935 (3.20 m) | +17.81 | +16.21% | FAIL / BASIS (height alone → 117.21) |
| Tile preparation | Q-10 109.8835 m² | WTP-01 127.6935 | +17.81 | +16.21% | FAIL / BASIS |
| Hidden skirting | Q-01 76.389 lm | SKT-01 94.1368 | +17.748 | +23.23% | FAIL / **BASIS** (RC1 runs under windows; R8.17 declared 76.389 "never a target") |
| Hidden profile | Q-02 76.389 lm | HPR-01 94.1368 | +17.748 | +23.23% | FAIL / BASIS |
| WP floor (wet 17.8625 + pantry 11.685) | 29.5475 m² | WPF-01 29.4275 | −0.12 | −0.41% | PASS |
| WP upturn (wet 30.225 + pantry 11.15) | 41.375 lm | WPU-01 44.2 | +2.825 | +6.83% | FAIL (not decomposed) |
| WP upturn area reference | Q-04R 4.5338 + Q-04PR 1.6725 m² | (RC1 books lm only) | — | — | NOT COMPARABLE |
| Aluminium windows | Q-15 17.2459 m² | WIN-02 16.0539 m² (WIN-01 6 nr) | −1.192 | −6.91% | FAIL (revision openings; not decomposed) |
| Internal PVC doors | Q-16 16.665 m² (PRICING_BASIS_REQUIRED) | DOR-01 6 nr, DOR-02 1 nr | — | — | NOT COMPARABLE (m² vs nr) |
| Internal glazed opening | Q-17 6.05 m² | SGD-02 6.05 m² (SGD-01 1 nr) | 0 | 0.00% | PASS |
| Blockwork 150 | Q-07-150 128.87 m² (PARTIALLY_CALCULATED) | not in RC1 | — | — | **NOT COMPUTED** |
| Blockwork 200 | Q-07-200 218.4942 m² (PARTIALLY_CALCULATED) | not in RC1 | — | — | **NOT COMPUTED** |
| Marble thresholds | — | MRB-01 0.51 m², MRB-02 3.4 lm | — | — | new in RC1 |
| Plaster small item | — | PLS-02 1.510248 m² | — | — | new in RC1 |

**Contractor comparison** (the only external reference):

| Row | Contractor | Urban seal (PA08) | Diff | Urban RC1 | Diff | Note |
|---|---|---|---|---|---|---|
| CC-01 floor | 107.76 m² | 108.9625 | +1.12% | 111.8988 | +3.84% | |
| CC-02 skirting | 76.9 lm | 76.389 | −0.66% | 94.1368 | +22.41% | RC1 rule change |
| CC-03 profile | 76.9 lm | 76.389 | −0.66% | 94.1368 | +22.41% | |
| CC-04 baths + kitchens | 159.28 | 139.431 | −12.46% | — | — | different basis |
| CC-05 corners + grooves | 26.35 lm | — | — | — | — | NOT_COMPARABLE |
| CC-06 chamfered corners | 12 lm | — | — | — | — | NOT_COMPARABLE |

**Disagreement flagged by Claude.** The seal mixes the revision (REV_OLD) and rules (3.0 m heights, the 76.389 skirting target) that the owner later changed. It is a valid *regression anchor for PA08*, but it should **not** be used as the accuracy reference for RC1. What is needed is an **independent hand takeoff of REV_NEW under the current owner rules**.

### 16.2 23010 (first project, PDF)

Sealed manual site measure (كيال): full scope 395.67 m² (dry 322.50, wet / service 73.17); ceramic wall length 102.70 lm (gross, doors not deducted).

* The engine gives 397.30 m², which is **+0.41%** on the full scope.
* By reconciliation group the errors are +0.2%, +2.9% and +1.1%. Positive and negative room errors cancel.
* Per-room error metrics **cannot be computed**: 10 manual rows have no coordinates.

(`docs/RUN1_ACCEPTANCE.md` §9.)

### 16.3 Alsenan (P7757) vs freelancer (B1)

The freelancer's numbers are a reference, **not ground truth**: their rebar is an allowance, and several of their rows are copied. From V3c §B:

* flooring +9.2%;
* skirting +10.4%;
* wall tile −14.9% (Urban misses wet rooms);
* wet WP −19.1% (same cause);
* roof WP +13.1% like-for-like;
* blockwork −36.5% (Urban under-measures ≈140 m of wall);
* paint +0.7% (the agreement is not proof);
* plaster +18.8% (height basis);
* blinding −37% (scope);
* RC concrete −10.3% (reconciled row by row);
* rebar −40.6% (method + defects).

---

## 17. Al Rashed benchmark

| Field | Value |
|---|---|
| Project | Al Rashed villa, Sabah Al Ahmad (workbook "الراشد صباح الاحمد") |
| Owner, consultant, permit, plot number | **not recorded in the repository** |
| Plot | 22.00 × 27.28 = 600.16 m² geometric vs 600.00 m² in the schedule |
| Floors | BASEMENT / GROUND / FIRST |
| DWG revision | 16-11-2025-R3, sha `299c61b1…` (decoded with LibreDWG; 25,429 objects) |
| PDF revision / DWG–PDF match | the PDF set exists in `data/inputs`. A formal DWG↔PDF identity check like the one done for P7757 / ST7757 (R8.6A) **has not been done for Al Rashed**. |
| Unit interpretation | INSUNITS 1 (inch) vs physical evidence for metres → **CONFLICT → COUNT_ONLY** (§11). Owner action RESOLVE_ALRASHED_UNIT is OPEN. |
| Finishing height | not established (R7 used storey intervals) |
| Door height / width fallback | TD-02 2.2 m / TD-01 1.0 m (temporary defaults); R7 door count 35 |
| Window treatment | R7 window height guide gives bathrooms 0.60 m vs a site frame of 0.75 m (14% low) |
| Wet-room rules | US-04 / US-14 global |
| Ground truth | historical workbook with only **2 confident quantities**: insulation 950.22 m², balustrade 57 lm |
| Engine results (current R8 policy) | **No physical value** (VALUE_NOT_COMPUTABLE). Counts only. |
| Engine results (old R7 / qs_core, commit 557e466, orientation only) | 50 spaces; floor areas 556.27 / 448.14 / 59.12 m²; 42 openings (35 doors, 7 windows; 30 hosts confirmed, 12 unresolved); 150 wall lines **all BLOCKED** (no wall material in the source); project total null; 50 root questions; invariants 75 / 75 (25 per floor); acceptance 31 / 31. The frozen blind takeoff sha `7e9a3eba…` gives e.g. blockwork 150 = 190.289 / 200 = 963.188 (orientation only). |
| CAD exposure (latest accepted) | 68 mirrored INSERTs (layer 0: 43, A-TARG: 6, WIN-EWAN: 7, SYM-EWAN: 12); **46 realised arcs** in mirrored placements (**18 unique**; DOOR-EWAN 43, A-TARG 3); ELLIPSE 319, of which **6 with normal (0,0,−1)**; MINSERT 0; XREF 0; non-zero block base points 0; 610 block headers; 52 `*U` anonymous blocks / 235 inserts; SOLID 124; WIPEOUT 5; custom-class 10; DIMENSION 514 (454 rotated linear); MTEXT 515; ATTRIB 164; HATCH 226; OLE2FRAME labelled type 2; cad_adapter would realise 6,211 invisible segments + 1,932 invisible arcs. **Correction:** the old claim "7 mirrored arcs on the window layer" is actually 7 mirrored **INSERTs** on WIN-EWAN. |
| Unresolved | the unit; DWG↔PDF identity; wall materials (all 150 lines blocked); 12 unresolved opening hosts; window heights |

**What Al Rashed tests that Qortuba does not:**

* unit-conflict detection (an inch-declared drawing in metres, DIMLFAC 100);
* mirrored door arcs at scale (cad_adapter defect exposure);
* negative-Z ellipses;
* anonymous dynamic blocks;
* a basement + 2 floors villa;
* invisible geometry;
* OLE / IMAGE exceptions;
* the R5–R7 opening / host / dependency / question machinery on a real villa.

---

## 18. R8

**Purpose.** R8 is the **CAD source-truth programme**. It proves, with hand-derived truth, an independent oracle and mutation tests, that CAD geometry is placed correctly and that nothing is dropped silently, *before* any quantity uses it. It then hardens units / frame, decoder qualification, provenance and the Qortuba QS chain (R8.6–R8.20).

**R8 files.** The spec files live only in the gitignored `data/reports/URBAN_QTO_R8_SPEC/`, **included in the ZIP**:

| File | Exists? |
|---|---|
| `R8_REVISED_SPEC.md` | yes (data/reports, not git) |
| `R8_SCHEMA_DRAFT.json` | yes (data/reports, not git) |
| `R8_TEST_MATRIX.json` | yes (data/reports, not git) |
| `R8_DECISION_LOG.md` | yes (data/reports, not git) |
| `R8_ALRASHED_EXPOSURE_CENSUS.json` | yes (data/reports, not git) |
| Registers | `tests/r8_0/registers/*.json` (git): fixtures, mutations, **R8_0_EXPECTED_FAILURES.json**, contract supersession, … |
| Packages | `data/reports/URBAN_QTO_R8_0_TEST_BASELINE`, `…R8_1…` through `…R8_20…` (MD / JSON in the ZIP) |

**Method**

* **Fixtures:** F01–F36 (36). Each is a small synthetic DXF built in code (`tests/r8_0` builders).
* **Truth:** **hand-derived** world coordinates (written in the test, independent of any library).
* **Independent ezdxf oracle:** ezdxf's own `virtual_entities` is used as a second opinion. Where ezdxf is known wrong (MINSERT under reflection), it is registered as LIBRARY_KNOWN_FAILURE.
* **Reference realiser:** a minimal test-side realiser, separate from production.
* **Mutations:** MT-01–MT-51 (51), plus 3 sensitivity mutations. Each mutation is a deliberate bug injected into the kernel; the tests must fail.

**Expected failures** (`R8_0_EXPECTED_FAILURES.json`, 87 entries, all currently XFAIL):

| Class | Count | Meaning |
|---|---|---|
| KNOWN_DEFECT (cad_adapter) | 43 | MIRRORED_ARC_SWEEP 8, MIRRORED_BULGE_SIDE 7, OCS_EXTRUSION_IGNORED 5, BLOCK_BASE_POINT_IGNORED 5, MINSERT_NOT_EXPANDED 5, FRAME_FAIL_OPEN 5, XREF_SILENT 5, NON_UNIFORM_SCALE_ARC_AS_CIRCLE 1, ROTATED_DIMENSION_PROJECTION 1, MTEXT_CODES_UNDECODED 1 |
| TARGET_NOT_IMPLEMENTED | 39 | fact policy, scope, transcription, source delta, claims, … (features not yet built) |
| CONTRACT_SUPERSEDED | 3 | F17, MT-32, MT-33: the contract changed (**reclassified, not fixed**) |
| LIBRARY_KNOWN_FAILURE | 1 | ezdxf MINSERT under a mirrored parent |
| BOUNDARY_DEBT | 1 | `plaster_trade_engine.py` / `wall_treatment_engine.py` import `research.a21_trace_sufficiency_01.parameters` |

Plus **5 R8.2 KNOWN_DEFECT XFAILs** (cad_adapter): invisible geometry realised; nameless block content at top level; OLE2FRAME type-2 drop; unowned entity placed in model space; handle identity collision.

**Ratchet history** (expected failures → pass):

* R8.1: 38 TNI → PASS (K1_REALISE 32, OCS 5, digest 1).
* R8.2: 14.
* R8.3: 22 (+2 disputed).
* R8.4: 1 real, plus **3 reclassified to SUPERSEDED, which is a reclassification and not a fix**.

---

## 19. R8.1

| Question | Answer |
|---|---|
| What R8.1 was meant to fix | build a correct production CAD kernel (K1) so that geometry no longer depends on the defective `cad_adapter` |
| What actually changed | **new** `engine/source/` modules (9, stdlib only): `observations.py`, `findings.py`, `cad/libredwg_map.py` (D1, verified fields only), `cad/kernel_ocs.py`, `cad/kernel.py`, `digests.py` (SRD-1 / RGD-1), plus capability / text helpers |
| Production modules changed | **none of the existing ones.** `cad_adapter.py` was untouched (sha `4d060a1d…`, unchanged since 2026-09-20). At R8.1 time no production path consumed K1. Later rounds (R8.3+, Alsenan, RC1) route the research pipelines through K1 / K2. |
| Tests changed / added | `tests/r8_1/` (**330 tests, all pass now**); 8 / 8 digest vectors; real-K1 mutations MT-01 / 02 / 03 / 49 break K1 and are caught |
| Expected failures that became passes | 38 (TARGET_NOT_IMPLEMENTED → PASS, because the target now exists in K1) |
| Expected failures that remain | all 43 cad_adapter KNOWN_DEFECT entries (because cad_adapter **was not fixed**) + TNI entries for later features |
| Reclassified, not fixed | **nothing in R8.1.** (In R8.4, 3 were reclassified to CONTRACT_SUPERSEDED.) |
| At the time | 4,112 passed / 124 xfailed |

**The distinction the owner asked for:**

* "**Tests pass because failures are marked XFAIL**" is true for `cad_adapter`. Its geometry is **still wrong**, and 48 XFAILs document it.
* "**The production geometry is correct**" is true **only for K1 / K2 paths**, and only for the entity types in §7 that are marked supported.

---

## 20. Current test results

**Run.** `python3 -m pytest -q -p no:cacheprovider --junitxml=…` from commit `1c331c5`. It started 2026-10-05 15:27 UTC, took **374.8 s**, and exited with code **0**. Counts were parsed from the JUnit XML, which is in the ZIP as `HANDOFF_EXTRAS/junit_full.xml`.

| Scope | Tests | Passed | Failed | XFailed | XPassed | Skipped | Errors |
|---|---|---|---|---|---|---|---|
| **Full repository** | **5,875** | **5,780** | **0** | **92** | **0** | **3** | **0** |
| R8.0 (`tests/r8_0`) | 366 | 279 | 0 | 87 | 0 | 0 | 0 |
| R8.1 (`tests/r8_1`) | 330 | 330 | 0 | 0 | 0 | 0 | 0 |
| CAD geometry / frame R8.2–R8.5 | 453 | 447 | 0 | 5 | 0 | 1 | 0 |
| CAD legacy `test_cad*` / dxf | 26 | 26 | 0 | 0 | 0 | 0 | 0 |
| R8.6–R8.20 (Qortuba / P7757 QS chain) | 796 | 796 | 0 | 0 | 0 | 0 | 0 |
| PDF (vector_source, raster_topology, raster_qa, glyph_text, document_reader, hybrid_path, frames, golden_23010) | 101 | 101 | 0 | 0 | 0 | 0 | 0 |
| BOQ / architectural: RC1 Qortuba | 37 | 37 | 0 | 0 | 0 | 0 | 0 |
| BOQ / architectural: PA08 Qortuba | 284 | 284 | 0 | 0 | 0 | 0 | 0 |
| Architectural + structural + rebar: Alsenan (`tests/alsenan`) | 304 | 304 | 0 | 0 | 0 | 0 | 0 |
| qs_core / R5–R7 / PA09 Al Rashed | 468 | 468 | 0 | 0 | 0 | 0 | 0 |
| Reporting v2 / v3 | 38 | 38 | 0 | 0 | 0 | 0 | 0 |
| Pricing auditor (`tests/audit`) | 35 | 35 | 0 | 0 | 0 | 0 | 0 |
| Agents | 203 | 203 | 0 | 0 | 0 | 0 | 0 |
| Everything else (legacy geometry rounds, QA workbook, topology research, documents, …) | 2,434 | 2,432 | 0 | 0 | 0 | 2 | 0 |

**Structural / rebar** has no separate suite. Those tests are inside `tests/alsenan` (304) plus engine tests for `bbs_optimiser`, `slab_rebar_binding`, `structural_*`. They are not separately counted: **NOT RUN separately**, but included in the full run.

**Skips (3):**

* `tests/r8_4/…::test_mt33_superseding_expectation_real_source`: needs `URBAN_R8_REAL_SOURCE` (a real DWG path), not set.
* 2 × `test_measurement_region_invariants`: "QS_MEASUREMENT_REGION_BUILDER does not exist yet". **This is a planned engine, not a pass.**

**XFAILs (92) are known failures, not passes:**

* 87 in R8.0 (43 cad_adapter defects, 39 not implemented, 3 superseded, 1 library, 1 boundary debt);
* 5 in R8.2 (cad_adapter).

**Real-file tests.** Most real-drawing tests read **frozen registers / cached decodes**, not the DWG itself. The pinned decoder exists only at `/tmp/ldwg`, outside the repository. Tests needing the raw real source are skipped (`URBAN_R8_REAL_SOURCE` unset) or use committed fixtures.

### 20.1 Test quality

| Type | Exists? | Examples |
|---|---|---|
| Unit | yes, many | engine/source modules |
| Geometry fixture (hand-derived truth) | yes | R8.0 F01–F36, R8.1 |
| Mutation | yes | MT-01–51 (CAD); V3b register mutations; UNIT_CONTROL mutations; R5–R7 acceptance mutations |
| Integration | yes | runners rebuilding registers and comparing digests |
| End-to-end | partial | Alsenan / Qortuba rebuilds from cached decodes; pipeline end_to_end (manual takeoff → priced doc) |
| Real DWG | partial (via cached decodes / frozen registers) | P7757, Qortuba, Al Rashed |
| Real PDF | partial | 23010 golden; ST7757 raster calibration |
| Real villa | yes (Alsenan, Al Rashed counts) | |
| Ground truth | weak | 23010 site measure (area only); Qortuba seal (self-produced); contractor 6 rows; freelancer (allowance-based) |
| Regression | strong | byte-identical rebuilds, Qortuba shadow regression every round |
| Property-based / fuzz | **none** (no hypothesis); shuffle-order tests only | |

**Biggest test gaps:**

1. **No independent known-answer takeoff per population**: V3c proved that 6 silent population defects passed every test.
2. No "missing population" mutation (delete a schedule → it must raise).
3. No independent human takeoff for Qortuba REV_NEW or Alsenan.
4. No second structural project.
5. Real DWG re-decode is not part of the test suite (the decoder lives outside the repository in `/tmp/ldwg`).
6. No property-based / fuzz geometry tests.
7. No CI, so nothing guarantees the suite is run.

---

## 21. Known bugs

| # | Bug | Severity | Module | BOQ affected | Project | Repro | Test exists? | Root cause | Workaround | Planned fix | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B1 | Mirrored ARC sweep / bulge side (+8 other transform defects) | **Critical** (on legacy paths) | `engine/cad_adapter.py` | doors, swings, curved walls, any geometry in reflected blocks | Al Rashed 46 arcs, P7757 10–11 | yes | 48 XFAIL | reflection applied as rotation; OCS / base / MINSERT ignored | use K1 / K2 | migrate / retire cad_adapter (R8.5 plan) | OPEN |
| B2 (D1) | Continuous beams CB1–13 carry no rebar; silent | **Critical** | `alsenan_v3_structure.py:319-347`, `alsenan_phase_a3.py` | rebar ≈ −2.2 t | Alsenan | yes | **no** | bars never transcribed; empty definition → silent skip | none | transcription + population invariant | OPEN |
| B3 (D2) | Per-metre footing bars used as an absolute count | High | `alsenan_v3_structure.py:285` | rebar ≈ −0.60 t | Alsenan | yes | no | `per_m` ignored | none | typed bar grammar | OPEN |
| B4 (D3) | FF footing zero rebar (merged cell); silent | High | `footing_rebar()` | −0.29 to −0.72 t | Alsenan | yes | no | merged two-row cell → empty definition | none | merged-cell split + BLOCKED row | OPEN |
| B5 (D4) | Strap beams have no rebar | High | (missing function) | −0.42 to −0.65 t | Alsenan | yes | no | not built | none | strap population | OPEN |
| B6 (D5) | 17 off-storey columns get rebar | High | `alsenan_v3_structure.py:298-302` | **+1.04 t over** | Alsenan | yes | no | rebar filter ≠ concrete filter | none | shared occurrence filter | OPEN |
| B7 (D6) | Ground slab bound to the smallest closed cell | High | `alsenan_v3_structure.py:98-113` | −10.9 to −18 m³ concrete, −0.67 to −1.1 t | Alsenan | yes | no | `min(hit, key=area)` | owner OQ-2 | scope inference + contradiction check | OPEN |
| B8 | Blockwork wall-length deficit ≈140 m | **Critical** for blockwork | wall-band material claims | blockwork up to −30% | Alsenan | yes | no | unclaimed / unbound runs drop out | none | wall-length conservation audit | OPEN |
| B9 (L-17) | Wet rooms merged into dry zones; GARDEN inside a floor zone | High | room closure / identity | tile −15%, WP −19%, floor | Alsenan | yes | no | no zone-purity rule | none | wet / dry / outdoor purity | OPEN |
| B10 (L-1) | PARTIAL rows in the technical total, not labelled | Medium | `engine/source/release_model.py:29-30` | totals read as complete | Alsenan | yes | yes (by design) | policy | read the PARTIAL flag | label "verified lower bound" | OPEN |
| B11 (L-2) | Roof WP mixes flat m² + upturn; wet-room WP split | Low | T-RWP lines | WP presentation | Alsenan | yes | no | inconsistent convention | — | split | OPEN |
| B12 (L-18) | Skirting may run along void / railing edges | Medium | skirting path | skirting | Alsenan 1F-Z06 | suspected | no | no void-edge exclusion | — | audit | SUSPECTED |
| B13 | Evaluation map errors E1–E4 hid defects | Medium | `alsenan_v3b_evaluation.py: MAP` | reporting / evaluation | Alsenan | yes | no | pre-declared causes accepted | — | typed map | OPEN |
| B14 | De-dup of identical slab labels may merge two layers | Medium | `slab_rebar_binding.py` | slab rebar | Alsenan labels 491 / 749 | yes | partially | rule too broad | OQ-9 | owner answer | OPEN |
| B15 | Window heights mostly budget estimates | High (commercial) | opening heights | aluminium m², deductions | Alsenan 26 / 33 | yes | yes (labelled) | no source height | raster / owner | raster sections | OPEN |
| B16 | Boundary debt: engine imports research | Medium | `plaster_trade_engine.py`, `wall_treatment_engine.py` | plaster / wall treatment (PA-era) | P7757 | yes | XFAIL | frozen by B-7 | — | move parameters | OPEN |
| B17 | Al Rashed unit conflict | Blocker (project) | frame | all values | Al Rashed | yes | yes | INSUNITS vs evidence | owner claim | owner action | OPEN (by design) |
| B18 | README / ARCHITECTURE docs stale | Low | docs | — | — | — | — | — | — | rewrite | OPEN |
| B19 | Pinned decoder binary lives outside the repository (`/tmp/ldwg`) | Medium (ops) | decoder_pins | re-decode impossible on a fresh machine without a rebuild | all DWG | yes | skip | built by hand in /tmp | cached decodes | scripted / containerised decoder build | OPEN |
| B20 | Hooks from unverified ACI edition | Low | `bbs_optimiser.py` | procurement weight | Alsenan | — | yes | edition unverified | labelled PROVISIONAL | verify table | OPEN |

---

## 22. Technical debt

Ranked by severity.

1. **Two CAD stacks.** `cad_adapter.py` (defective) is still imported by legacy paths next to K1 / K2. Highest risk of a silent geometry regression if someone reuses a legacy path.
2. **Project logic in `research/external_engine_lab/`.** About 44.8k lines, including **hand-transcribed schedules as Python constants** (`CB_TRANSCRIPTION`, footing / beam / column libraries). This is not generic, and it is not reusable for a new villa without new code.
3. **Duplicate generations of engines:** wall / face / topology / room / text-role / finish-height / release / run_manifest v1 / v2 / v3 (§6). Each is tested, but the reader cannot tell which one is authoritative without the round history.
4. **Rules spread across 4+ stores** (§15), some in gitignored `data/experiments`. There is no single rule registry with versioning, and the owner-approval state is not consumed uniformly.
5. **Boundary debt.** The allowlist is still present: `engine/plaster_trade_engine.py` and `engine/wall_treatment_engine.py` import `research.a21_trace_sufficiency_01.parameters`.
   * Pinned by `tests/r8_0/test_r8_0_import_boundaries.py` as an XFAIL BOUNDARY_DEBT, and frozen by decision B-7.
   * **R8.1 did not reduce it.**
   * Production risk is medium: these PA-era engines are not used by RC1 / V3b, but they are importable from `engine/`.
6. **Gitignored critical artefacts** (R8 spec, round packages, seals, owner rules V1) live only on disk. Losing the container loses them. Only partial copies exist in old handover ZIPs.
7. **No CI.**
8. **Weak typing**: dict-heavy registers and ad-hoc JSON schemas (SCHEMA strings), not validated by a schema library.
9. **Units in legacy paths** (`engine/ingest/units.py`, `engine/units.py`) are separate from `engine/source/frame.py`.
10. **Pricing fields inside measurement objects** in the old app bridge (`costRate`, `sellingRate` in `pm_sync.BOQ_ITEM_FIELDS`). This is guarded by INV-10, but it is a coupling.
11. **Dead code**: round self-tests and fixtures used only by their own tests; the `pipeline/` chain built around manual takeoffs.
12. **Documentation drift**: README "50 tests", the ARCHITECTURE A1–A13 table, E1–E20 lists.
13. **LLM dependency is *low*** for QTO (good), but E89 caching on 23010 means that path is not reproducible without the cache.

---

## 23. Confidence

There is **no single numeric confidence score**. The model is **categorical, by evidence class**:

* **Technical class** per line:
  * in total: MEASURED, DERIVED, RASTER_DERIVED, SOURCE_RULE, CODE_METHOD, OWNER_PROJECT_FACT, URBAN_STANDARD, PARTIAL;
  * out of total: REVIEW, BLOCKED, BLOCKED_SOURCE_CONFLICT, NOT_IN_SOURCE, PENDING.
* **Commercial class** per line:
  * PROVISIONAL_SOURCE_DERIVED, PROVISIONAL_SOURCE_RANGE, PROVISIONAL_GEOMETRIC_INFERENCE, PROVISIONAL_CODE_METHOD, PROVISIONAL_URBAN_FALLBACK, PROVISIONAL_OWNER_METHOD, OWNER_APPROVED_PROVISIONAL, BUDGET_ESTIMATE.
  * Each must carry `method`, `assumption`, `confidence` (**H / M / L**), `low` and `high` (`engine/source/release_model.py: REQUIRED`).
* **Geometry:** frame status (CONFIRMED / UNCONFIRMED / CONFLICT), capability level per entity, closure grade, portal grade (evidence-strength tiers E99), host-resolution status.
* **Text:** role authority grades (R8.9), legacy-decode lexicon hit / miss; there is no OCR confidence because there is no OCR.
* **Scale:** PRINTED vs SCALED raster grades; single-dimension calibration residual.
* **Semantic:** space role on positive evidence ("UNKNOWN is not VOID").
* **Rule:** the authority ladder (source > owner fact > Urban standard > fallback).
* **Agents:** A1 / A2 records carry `confidence` in {low, medium, high} (schema), but they are not used in QTO.

**What happens when confidence is low:**

1. The line is **not put in the technical total** (BLOCKED / REVIEW).
2. It may appear in the commercial view **only** as a labelled provisional with a range, or as BUDGET_ESTIMATE.
3. An **owner question** is raised (root questions, deduplicated).
4. It is **never silently produced as a final quantity**.

Procurement takes only technical-in-total, OWNER_APPROVED_PROVISIONAL and H-confidence provisionals.

**Missing:** named confidence factors per line (which edge or assumption cost the confidence; the OpenTakeoff idea). There is no overall numeric score, and the categories are not calibrated against outcomes.

---

## 24. Provenance

| Field | Recorded? |
|---|---|
| Source file | **yes**: sha256 (content-addressed), path, writer fingerprint |
| Drawing name / sheet | yes (sheet / region role registers) |
| Revision | yes (revision identity, REV_OLD / REV_NEW; owner claims bound to sha) |
| Page | yes for PDF lanes (page index; raster sheet id) |
| Floor | yes (level / floor register) |
| Room | yes (space id; room matrix) |
| Entity ID | **yes**: DWG handle, plus the **insert handle path** for block occurrences (lineage) |
| Layer | yes (canonical effective layer, R8.9) |
| Block name | yes |
| Original geometry | yes in observations (raw decode) |
| Transformed geometry | yes (realised part + composed map, digest RGD-1) |
| Original units / final units | yes (UNIT_CONTEXT + frame on the run manifest) |
| Applied rules | yes on V3b / RC1 lines (`authority`, method / rule ids); partial on older engines |
| Deductions / additions | yes as detail rows (opening deductions with width + height evidence; INV-17) |
| Agent | n/a for QTO (no agent); A1 / A2 records cite the drawing location |
| Engine | partially (module named in register SCHEMA / method); **the git head is recorded in freeze manifests**, not on every line |
| Confidence | class + H / M / L on provisionals |
| Validation results | FINAL_QA register per release; invariants records; freeze digests |

**Schema.** Each BOQ line has `formula`, `authority`, `trace` and `details[]` (sub-rows with `ref`, `formula`, `qty`, `status`). Registers carry SCHEMA ids. Exports pass `engine/export_provenance.py` ("an export says where it came from, or it is not exported"). E44 `quantity_trace.py` traces a quantity back to the drawing (23010 path). Run manifests record inputs, digests and the git head.

**Missing:**

* the per-line handle list for every quantity in V3b (the trace is often textual, e.g. "A3 footing occurrence rows");
* a uniform provenance schema across engines;
* a PROOF overlay image per quantity;
* Firestore-side provenance.

---

## 25. Duplicate protection

| Risk | Protection | Strength |
|---|---|---|
| Two engines measuring the same wall | wall stretch ownership by disjoint intervals (round 6D); INV-05 every component ends in exactly one state; wall-band identity | good on bands; **no global wall-length conservation** |
| PDF and DWG both adding a quantity | lanes are not summed: raster is a second signal / height source only; dual-measurement register compares, never adds | good |
| A block and its realised geometry | K1 realises block content; the INSERT itself is not geometry; conservation accounting counts every observation once | good (K1) |
| Parent and child geometry | lineage handle path; source sub-part identity (R8.8); handle-identity collision is a **cad_adapter defect** | good on K1 |
| Same door / window twice | opening register with one host per opening (INV-01); near-collinear door closure; double-leaf motif; duplicate-occurrence register (R8.10) | good on Qortuba / Alsenan; ambiguous hosts surfaced (INV-12) |
| Repeated XREF | XREF not resolved (four-state) | n/a |
| Repeated MINSERT | MINSERT not realised | n/a |
| Duplicate rooms / copied plan views | repeated-geometry / drawing-frame detection (round 6C); drawing-region role; unique physical-space register | good on P7757; region designation needed per project |
| Duplicate BOQ lines | canonical BOQ item model (RC1, one payable identity per measurement item + aliases); `line_ids_unique` in FINAL_QA; alternatives / components excluded from totals; rebar NET / PROCUREMENT / PARTIAL never summed | good |
| Beam / side bar / residue double count | checked in V3c: **none found** | — |
| Slab label de-dup | **may under-count** (OQ-9) | weak |

---

## 26. Missing-item / invariant system

* **qs_core invariants** (`engine/qs_core/invariants.py`): **28 defined (INV-01..INV-28)**. Examples:
  * INV-01: one host per opening;
  * INV-02 / INV-14: deductions reconcile band by band;
  * INV-03: unresolved openings never allocated;
  * INV-04: no wall material becomes floor;
  * INV-06 / INV-07: area closure;
  * INV-08: order independence;
  * INV-09: no comparison data in production code;
  * INV-10: pricing fields separate and empty;
  * INV-15: BLOCKED never in a published total;
  * INV-16: no masonry billing on thickness alone;
  * INV-17: every deduction traces to width + height evidence;
  * INV-18: wall continuity proved;
  * INV-19: opening basis decided per wall line.

  In the R7 Al Rashed run, **25 were applied per floor × 3 floors = 75 / 75 pass**. That count is from the R7 package; it was not re-run here.
* **Engineering invariants document:** `docs/ENGINEERING_INVARIANTS.md` has **318 numbered sections (§1–§318)**. These are design decisions and invariants, many enforced by tests.
* **Free-space invariants** (E66), **free-space QA**, **MISSING_SPACE_QA** (PA07), **stair coverage gate per floor**, the **completeness matrix** (V3), **EXPECTED_SCOPE_REGISTER** (V3b) and **source conservation** ("nothing silently disappears").
* **V3b FINAL_QA (14 checks):**
  * no provisional in technical;
  * technical quantity only for technical classes;
  * every provisional labelled;
  * provisional within range;
  * waste pending blank, never zero;
  * rebar bases never summed;
  * alternatives not in totals;
  * line ids unique;
  * units known;
  * no V3a line dropped;
  * matrix = lines;
  * concrete lines carry a grade;
  * benchmark not read;
  * never the 44.19 target.

  State: **PASS**.

**What is NOT checked:** the cross-trade missing-item checks the owner listed. These **do not exist as automatic invariants**:

* concrete without rebar (**D1, D3 and D4 prove the gap**);
* a wet room without wall ceramic;
* a window without an aluminium line;
* a stair without a handrail;
* a room with a floor but no ceiling (partly covered by the completeness matrix);
* a schedule table never read.

The expected-scope register and completeness matrix cover some of these **by hand-declared scope**, not by rule. This is **P0 #1** (§35).

---

## 27. Firestore / backend

* **Firebase project:** `urbanprojectsmanager`. The app is Flutter (`msalfahad/UrbanProjectsManager`, a separate repository not attached here).
* **Written by this repo:**
  * `projects/{projectId}/boqItems/{itemId}`, through `engine/pm_sync.py` (E14);
  * the document fields exactly match the app's `BoqItemModel.toMap()`: `projectId, groupId, packageId, packageName, templateId, name, unit, formulaType, measurements, costRate, sellingRate, isDeleted, linkedCostItemId, notes, categoryId, costTypeId, photoUrl, createdAt, updatedAt`;
  * `formulaType` is one of simple / area / volume / perimeter, plus a `measurements` map, mirrored by `engine/boq_formula.py`, so the app recomputes the same quantity;
  * the writer is injectable (a fake in tests, firebase-admin live).
* **Sandbox:** `tools/connect_firestore.py` / `tools/firestore_sandbox.py` write only under `sandbox/...`.
* **Planned, not implemented here:** costItems, clientRequests, clientPayments, aiReports, auditLogs.
* **Not connected:** the QTO V3b / RC1 outputs are **not written to Firestore**. They are JSON registers + XLSX / PDF on disk. There is no Firestore schema for drawings, rooms, provenance, validation, rules or agent results.
* **Revisions in Firestore:** none. Old quantities are traceable only through git + frozen registers, not in the database.

---

## 28. Output schema

**Real example**: Alsenan V3b BOQ line (`tests/alsenan/registers_v3b/BOQ_LINES_V3B.json`, SCHEMA `URBAN_ALSENAN_V3B_BOQ_LINES_V1`, release label "V3b FULL-BOQ CANDIDATE (not FINAL)", 389 lines):

```json
{
  "trade": "CONCRETE", "level": "GF", "group": "SUBSTRUCTURE", "code": "C-FTG",
  "desc_en": "Isolated footings (reinforced concrete)", "desc_ar": "قواعد منفصلة خرسانة مسلحة",
  "unit": "m3", "qty": 64.346, "status": "PARTIAL",
  "formula": "sum of 25 footings (L x W x H from SCHEDULE OF FOOTINGS); 2 blocked",
  "authority": "SOURCE (schedule + plan)",
  "trace": "A3 footing occurrence rows",
  "details": [
    {"ref": "FN", "formula": "1.00 x 1.00 x 0.30", "qty": 0.3, "status": "COMPUTED"},
    {"ref": "F5", "formula": "2.40 x 2.10 x 0.40", "qty": 2.016, "status": "COMPUTED"},
    {"ref": "FF", "formula": "4.60 x 4.50 x 0.55", "qty": 11.385, "status": "COMPUTED"}
  ]
}
```

(`details` is truncated here; the real line lists all 25 footings.)

**Technical view row** (`TECHNICAL_QTO_REGISTER.json`):

```json
{"line_id":"B0001","trade":"CONCRETE","level":"GF","code":"C-FTG","unit":"m3","class":"PARTIAL","qty":64.346,"in_total":true,"no_total":false}
```

**Commercial view row** (`COMMERCIAL_BOQ_REGISTER.json`):

```json
{"line_id":"B0002","trade":"CONCRETE","level":"GF","code":"C-FTG-FF10","unit":"m3","class":"PROVISIONAL_SOURCE_RANGE","qty":1.96,"low":0.432,"high":1.96,"confidence":"M","method":"the two schedule definitions of the one drawn outline","assumption":"SELECTED COMMERCIAL BASIS = the larger (F10) definition, labelled","in_commercial_total":true,"budget":false,"procurement_eligible":false,"provisional":true}
```

**How each concept is represented:**

* **Project:** the register set and folder.
* **Floor:** `level`.
* **Room:** the room matrix (RC1) / finish register rows.
* **Trade:** `trade`.
* **BOQ item:** `code` + `line_id`.
* **Description:** `desc_en` / `desc_ar`.
* **Unit / quantity:** `unit`, `qty`.
* **Raw quantity and deductions:** in `details` / `formula`. There is no separate `raw_qty` / `deduction_qty` field on every line; finish registers carry gross / deduction / net.
* **Rule:** `authority` / method.
* **Source:** trace + registers.
* **Confidence:** class + H / M / L.
* **Validation:** FINAL_QA.

The **RC1 canonical BOQ** (`engine/source/boq_canonical.py`) adds one payable identity per item with aliases. Its 22 Qortuba items are listed in §16.

---

## 29. Revision handling

* **Implemented:**
  * revision identity (sha, writer fingerprint, revision id), and admission classes (R8.6A);
  * owner claims bound to an exact sha and **not transferable** to a new revision;
  * `engine/source/canonical_input.py`: CANONICAL_MEASUREMENT_INPUT, fail closed;
  * E46 `revision_entities.py`: entity identity across revisions (research, 23010 / P7757);
  * E11 `revision_delta.py`: diff two **BOQ snapshots** by item id → added / removed / changed lines with cost impact;
  * R8.7: a **diagnostic** Qortuba REV_OLD → REV_NEW remeasurement and delta.
* **Not implemented as a production feature:** an R2 → R3 pipeline that automatically reports added / removed rooms, changed walls / doors / windows / structure and changed quantities at entity level, and **invalidates** old quantities. Today a new revision means a **new run**. Old claims stop applying because they are bound to the old sha (which is effectively an invalidation of owner facts), and E11 can diff the BOQ lines. Room- and opening-level matching across revisions is research-grade only.

---

## 30. Arabic support

* **CAD text:**
  * `engine/source/legacy_text.py` decodes **legacy SHX Arabic** (ARABIC_KEYBOARD_101 and XARAB_GLYPH_V1 mappings). This is essential on Alsenan, where room labels are keyboard-mapped Latin glyphs.
  * Its LEXICON covers BATH / KITCHEN / LIVING / MAID / WC / WASH / LAUNDRY / RECEPTION / DINING / DEWANEYA …
  * A text-style font map is used.
* **Aliases:** `data/registry/space_aliases.json` has 111 aliases.

| Label | Supported? |
|---|---|
| حمام | yes |
| مطبخ | yes |
| غسيل | yes |
| كوي | yes |
| مخزن | yes |
| صالة | yes |
| استقبال | yes |
| غرفة | yes |
| درج | yes |
| مصعد | yes |
| **ديوانية** | **missing from the alias table** (present in the legacy lexicon as DEWANEYA) |
| مجلس | **missing** |
| حوش | **missing** |
| pantry / بانتري | **missing** |

* **Mixed labels:** bilingual corroboration and source-scoped tag families (V3).
* **PDF text:** PyMuPDF text extraction where a text layer exists.
* **Glyph-only drawings:** `glyph_text.py` (E88) finds text without text objects (23010) by shape comparison. There is **no OCR engine**. E89 uses an LLM on image crops, cached.
* **Normalisation:** alef / ya / ta-marbuta normalisation exists in the alias matching. Shaping / RTL: CAD legacy text is decoded to logical order; PDF RTL order issues were handled ad hoc on 23010.
* **Confidence:** there is no numeric text confidence; there is role authority.
* **Weak:**
  * no OCR for raster schedules (Arabic or English);
  * alias gaps (ديوانية, مجلس, حوش, pantry);
  * structural abbreviations are parsed per project, not by a grammar;
  * RTL in PDF text layers is not systematically tested.

---

## 31. Kuwait-specific logic

| Kind | What is encoded |
|---|---|
| **Urban internal rules** | US-01..17, UP-* rule library, the owner method rules, project facts (§15). Example: WP upturn 0.15 m / roof 0.20 m, reveals 0.25 m, PVC inside / aluminium outside. These are **company practice, not regulation**. |
| **Kuwait regulation / code** | **essentially none encoded.** There is no Kuwait Municipality / MEW / KBC rule in the QTO engines. `engine/audit/refdata.py` lists "structural concrete grades used in Kuwait residential / commercial" (pricing auditor reference data). |
| **General engineering** | ACI 318-19 hook tables (**edition unverified**, PROVISIONAL); D²/162 rebar weight; cover / lap values come **from the project drawings** (ST7757 p.8), not from a code |
| **Business / locale** | KWD currency in `engine/units.py` / `quantity_state.py` / `ingest/units.py`; Kuwaiti Arabic in the agents; `engine/cooling.py` (provisional BTU/h per m² for the Kuwait climate: **pricing / estimating, not QTO**); preliminaries rate card (KWD, provisional) |

**Questionable / non-Kuwait assumptions:**

* ACI (US) hook tables used as the code method. Kuwait practice often follows BS / ACI mixes; to be confirmed.
* 12 m stock bar length (common in Kuwait, but an assumption).
* The 2.2 m door / 1.0 m width temporary defaults.
* The 0.10 m floor build-up fallback.

None of these is a Kuwaiti regulation.

---

## 32. Pricing boundary

* **The QTO engines produce quantities only.**
  * V3b / RC1 registers record no rates (the takeoff records **RATES_SUPPLIED 0**).
  * INV-10 asserts that pricing fields stay separate and empty in measurement objects.
  * `rule_library.py` rejects currency tokens in measurement rules.
  * The benchmark firewall stops price / benchmark data entering engine inputs.
* **Pricing code that exists (separate):**
  * E4 `rate_library.py`;
  * `data/rate_cards/P7757_RATE_CARD.json`, `data/rate_library/alsenan_chalet.json` (excluded from the ZIP);
  * E7 Phase-0 auditor (`engine/audit/*`, `tools/phase0_audit`);
  * E17 preliminaries, E9 cooling;
  * `pipeline/end_to_end.py` (manual takeoff → priced → app doc);
  * PA08 Qortuba pricing tests (`test_pa08_qortuba_pricing`, `_pricing_audit`).
* **Contamination risks (flagged):**
  * `pm_sync` documents carry `costRate` / `sellingRate`, because that is the app's model;
  * US-09 (normal skirting = half the hidden rate) is a **rate rule** stored in the owner rule set;
  * Q-16 is "PRICING_BASIS_REQUIRED".

  None of these changes a quantity. Keep pricing in the web app.

---

## 33. Recent changes

Most recent first. Each round recorded a recommendation first, then the implementation, freeze and package.

| Commit | Change | Why | Main files | Tests | Result |
|---|---|---|---|---|---|
| 1c331c5 | V3c forensic accuracy + donor audit (doc only) | explain the freelancer gaps; find engine defects | `research/external_engine_lab/V3C_FORENSIC_ACCURACY_DONOR_AUDIT.md` | none | 6 proven defects D1–D6, ranked fixes; **no code change** |
| 66dd3fb | V3b freeze: 19 registers built twice (byte-identical), post-freeze evaluation, Qortuba shadow unchanged | freeze the candidate BOQ | `tests/alsenan/registers_v3b/*`, reporting | register tests + mutations | QA PASS |
| 17efc83 | V3b engines: BBS optimiser (ACI hooks provisional, FFD cutting), two-layer release, waste / procurement, corner beads, slab binding V1.1, structure (domes, pool, stairs, necks, F / F10, blinding …), finishes NET with reveals | full BOQ candidate | `engine/source/bbs_optimiser.py`, `release_model.py`, `waste_procurement.py`, `corner_bead.py`, `alsenan_v3b_*` | alsenan tests | 389 lines |
| c00594b | Raster evidence lane + slab rebar binding | heights from raster sections; slab bars from plans | `raster_evidence.py`, `slab_rebar_binding.py` | synthetic tests | 6 sheets calibrated |
| 18d2ed5 | Owner decisions OD-V3B-1..13, OC-V3B-A..E recorded | decisions before code | owner register | — | — |
| 550318a | Unit-control addendum (display units, rebar bases never summed) | unit safety in reports | reporting | UNIT_CONTROL mutations | PASS |
| 1381aa6 | Alsenan V3a final BOQ frozen (17 registers) | first full BOQ | registers | register tests | frozen |
| b15fb84 / b4eef43 | V3 engines: legacy Arabic text decode, tag families, opening completion, finish-height split by beam coverage, Reporting V3 | Alsenan rooms / openings / finishes | `legacy_text.py`, `opening_completion.py`, `finish_height_v3.py`, `reporting_v3/*` | 17 synthetic | Qortuba 72 / 72 unchanged |
| 9ef9353 / 6b67f61 | Reporting V2 + QS reconciliation sheet | owner-readable workbooks with formulas | `engine/reporting_v2/*` | readback, LibreOffice recalc | PASS |
| 7d8c3df | B2A.1 stair count model + curved bases | stair defect | `structural_vertical.py` etc. | tests | stair stays BLOCKED |
| 4b32b4d | Slab region engine stdlib-only | boundary purity | `slab_region.py` | — | — |
| (RC1) | Qortuba RC1 canonical BOQ, room matrix, opening schedule | release candidate for the apartment | `boq_canonical.py`, `room_matrix.py`, `rc1_*` | 37 | RC1_REFERENCE |
| (R8.13–R8.20) | wall-band V5, skirting path V2 / V4, door transition V2, reveals, wall faces V2, WP, sliding doors, human review, BOQ XLSX | Qortuba QS chain | `engine/source/*` | 796 (R8.6–R8.20) | shadow-complete |
| (R8.3–R8.5) | UNIT_CONTEXT / frame, decoder qualification, source exceptions, value shadow | unit safety, Al Rashed | `frame.py`, `qualification.py`, `source_exceptions.py` | 453 | MIGRATION_PLANNING_READY YES / EXECUTION NO |
| (R8.1–R8.2) | K1 kernel, capability register, K2 ezdxf route, conservation | correct CAD geometry | `engine/source/cad/*`, `capability.py`, `conservation.py` | 330 + 199 | K1 correct; cad_adapter untouched |
| (R8.0) | CAD test baseline: 36 fixtures, 51 mutations, 87 expected failures | prove the CAD defects | `tests/r8_0/*` | 366 | baseline |

---

## 34. Current work

* **Current task:** this handoff (report + ZIP). There is no code in progress.
* **Branch:** `claude/access-permissions-setup-ii24ws`.
* **Last engineering state:** V3c audit committed as **recommendation only**. It explicitly says *"STOP. DO NOT IMPLEMENT UNTIL MOHAMMAD / CHATGPT REVIEW."* Nothing was interrupted half-way.
* **Unresolved:**
  * owner questions OQ-1..OQ-13 (Alsenan);
  * RESOLVE_ALRASHED_UNIT;
  * an independent AutoCAD / ODA DXF export;
  * an independent hand takeoff for Qortuba REV_NEW.
* **Tests:** the full suite is green (5,780 passed / 92 XFAIL / 3 skipped / 0 failed).
* **Next implementation (after approval):** V3c §I rank 1: the population-completeness invariant + schedule / table inventory. Then rank 2: continuous-beam rebar.

---

## 35. Priorities

**P0: critical before any real BOQ use**

1. Population-completeness invariant + schedule / table inventory (no silent skip; every scheduled / drawn population → quantity or a BLOCKED row; every table → read or UNREAD).
2. Fix the rebar populations D1 (continuous beams), D5 (column filter), D2 / D3 (typed bar grammar, merged cells) and D4 (straps).
3. Blockwork wall-length conservation per floor (UNCLAIMED must be 0 or listed).
4. Wet / dry / outdoor zone purity (no wash / WC / garden in a dry zone); recover the missing 1F baths.
5. Retire or wrap `engine/cad_adapter.py` (route every path through K1 / K2); remove the boundary debt.
6. An independent known-answer takeoff per population (one villa, one apartment), done by a human QS **before** engine runs.
7. Label the technical total "verified lower bound (contains PARTIAL)" (L-1).

**P1: high**

1. Ground-slab scope inference + physical contradiction check (D6).
2. Opening heights from raster sections / elevations (26 / 33 budget heights).
3. Owner method decisions: plaster height basis (OQ-10), parapet height (OQ-8).
4. Schedule reading: OCR / vector-glyph table reader with per-cell confidence and merged-cell geometry (replace hand transcription).
5. Al Rashed: owner unit claim → full rerun under K1; DWG↔PDF identity check.
6. CI (pytest on push) and committing the gitignored spec / registers that matter.
7. Shape-code library for detail bars (boxed footings, inner links, stairs).

**P2: important later**

1. Entity-level revision delta with invalidation.
2. Write QTO to Firestore with provenance.
3. Rule registry consolidation (one versioned store).
4. Named confidence factors per line; PROOF overlays.
5. Consolidate duplicate engine generations.
6. Old POLYLINE / LEADER / MLEADER / SPLINE in the capability register.

**P3: future / commercial**

1. Agent re-scope (A1 / A2 as schedule readers with confidence).
2. Plan-vs-schedule mismatch → RFI generator.
3. Second and third structural projects.
4. A live AutoCAD MCP read-only oracle (lab).
5. UI.

---

## 36. Barriers to 95%+

Ranked.

| # | Barrier | Affects | Why | Probability it bites on a new villa | BOQ impact | Proposed solution |
|---|---|---|---|---|---|---|
| 1 | Whole populations missed silently | rebar, any scheduled element | readers keyed to known titles; empty definition = skip | **high** | rebar −10 to −40% | completeness invariant + table inventory |
| 2 | Schedules transcribed by hand | all structure | no schedule reader (raster / glyph tables) | **certain** (needs new code per project) | blocks automation | deterministic table reader + OCR + per-cell confidence + human confirm |
| 3 | Wall length without a material claim | blockwork, plaster | material identity required before measurement | high | blockwork −30% | conservation + material inference with review |
| 4 | Room identity / closure on villas | tile, WP, floor, skirting | merges wet into dry; open plans | high | tile / WP ±15–20% | zone purity; seal ladder; door-seal ideas |
| 5 | Heights (openings, finishes) | windows, doors, plaster, tile | not on plans; sections are raster | high | ±10–20% on wall finishes | raster sections → printed level chains; owner method register |
| 6 | Method conventions differ from the human QS | plaster, parapet, blinding, roof WP | different bases | certain | ±18–47% per item | publish both bases; owner decides once per trade |
| 7 | Units / scale | everything | bad INSUNITS, single-dimension PDF calibration | medium | catastrophic if wrong (now caught) | the frame policy (done); two-axis calibration |
| 8 | Legacy CAD path reuse | geometry | cad_adapter still importable | low–medium | doors / curves wrong | retire it |
| 9 | No independent ground truth | evaluation | benchmarks are self-made or allowance-based | certain | we cannot *measure* 95% | human known-answer takeoffs |
| 10 | Scope ambiguity (what is in the job) | blinding, slabs, pool, stairs | drawings incomplete | high | ±5–10% | expected-scope register + owner questions |

**Honest status.** Accuracy on clean floor areas is about ±1–3%. On a whole villa BOQ, the evidence (V3c) shows **several trades off by 15–40%** against a human, partly from Urban defects and partly from basis differences. **95% is not demonstrated for any trade except clean floor / ceiling areas.**

---

## 37. Human review requirements

**Must be flagged, never guessed:**

* ambiguous or conflicting units / scale (Al Rashed);
* missing dimensions / heights;
* unclear or merged rooms;
* conflicting drawings (plan vs schedule; F3 double tag; FF garbled cell);
* unusual structural details (box symbols, boxed bars, domes, pool);
* poor scans;
* missing reinforcement schedules / details (stairs);
* overlapping revisions;
* scope questions (elevator, pump room, perimeter strap, slab-on-grade extent);
* method choices (plaster height, parapet height, blinding extent).

**Can be automated safely today** (with review sampling): K1 geometry placement, capability / conservation accounting, floor / ceiling areas for closed rooms on vector CAD, opening counts and widths, schedule-driven concrete **once the schedule is confirmed**, rebar for populations whose schedule rows are typed and confirmed, BBS cutting, report generation.

**Rule:** anything that is not confirmed goes to REVIEW / BLOCKED, or to a labelled provisional with a range, plus an owner question.

---

## 38. Commercial readiness (0–10)

| Use | Score | Why |
|---|---|---|
| Internal experimentation | **7** | deterministic, reproducible, heavily tested, honest status classes |
| Internal Urban Projects use (QS assistant beside a human) | **5** | useful for areas, counts, concrete from confirmed schedules and an audit trail; human must check rebar, blockwork, wet rooms and heights |
| Real project BOQ assistance (deliverable checked by a QS) | **3** | the silent population defects (V3c) mean a QS cannot trust completeness without the P0 invariants; schedules need hand transcription |
| Semi-automated commercial use | **2** | no schedule reader, per-project code in research/, no CI, no Firestore integration of QTO |
| Fully automated commercial use | **0–1** | not appropriate; it would produce silently incomplete rebar / blockwork |

---

## 39. Top 20 risks

Most dangerous first.

1. **Silent missing populations** (rebar CB / straps / FF; any unscheduled element). Missing quantity, no warning.
2. **Blockwork under-measurement** (unclaimed wall runs). Missing quantity.
3. **Legacy `cad_adapter` used on a new project.** Wrong mirrored doors / arcs, OCS, base points; silent.
4. **Hand-transcribed schedule errors** (typos in Python constants). Wrong structure / rebar; silent.
5. **Wet rooms merged into dry zones.** Missing tile / WP, wrong floor finish.
6. **PARTIAL rows read as complete totals.** Under-statement presented as complete.
7. **Wrong unit accepted via the old R7 / qs_core path** (declared metre over INSUNITS).
8. **Wrong revision**: a run on a superseded file (claims are bound to sha, but runners pick files by config).
9. **Opening heights as budget estimates** flowing into procurement or a client BOQ.
10. **Method-basis mismatch** with the client's QS (plaster height, parapet, blinding) causing disputes.
11. **Slab-label de-dup merging two real layers.** Missing slab rebar.
12. **Off-storey members counted** (D5 pattern) in other populations. Double / over count.
13. **Typical-label scope too small** (D6 pattern). Missing slab area / concrete.
14. **Skirting along voids / railings.** Over-count.
15. **PDF single-dimension calibration** on a new raster project. Wrong scale.
16. **Unsupported entities** (SPLINE / REGION / LEADER / old POLYLINE / MINSERT / XREF) carrying real geometry. Missing items (recorded, but easy to ignore).
17. **Gitignored artefacts lost** (seals, specs, owner rules). Loss of the audit trail.
18. **Evaluation maps hiding defects** (pre-declared causes). False confidence.
19. **LLM-read title-block data** (E89) used without a cache or check. Wrong sheet metadata.
20. **Pricing / measurement coupling** in the app bridge (`costRate` in the boqItems doc). Confusion between quantity and price changes.

---

## 40. Questions for ChatGPT

1. **CAD math:** Check `engine/source/cad/kernel.py` and `kernel_ocs.py`. Is "curves by point mapping, with sweep direction from det of the full composed map" correct for every similarity and reflection case? What breaks under non-uniform scale + rotation inside a reflected parent?
2. **OCS:** Is the fail-closed arbitrary-axis implementation correct for extrusion (0, 0, −1) ellipses and arcs (Al Rashed has 6)? Should PREVIEW ellipses be promoted to measurable geometry, and how should that be tested?
3. **Units:** Review `engine/source/frame.py`. Is CONFLICT → COUNT_ONLY the right policy for Al Rashed (INSUNITS = inch, DIMLFAC 100, walls 200 mm apart as metres)? What minimal owner evidence should be enough to confirm metres?
4. **Population completeness:** Design review of V3c §I-1. What is the right data model so that "every concrete occurrence ↔ bar sets or an explicit BLOCKED row", and "every table on a sheet ↔ a reader or UNREAD", become hard invariants?
5. **Rebar:** Re-derive the continuous-beam (CB1–CB13) bar quantities from ST7757 p.11–12 independently. Is the D²/162 weight plus the project lap (70Ø / 40Ø) and cover (25 / 70 mm) approach acceptable for a Kuwait BBS? Should ACI hooks be replaced by BS 8666 shape codes?
6. **Freelancer reconciliation:** Challenge each PROVEN / PROBABLE verdict in V3c §B. In particular: the blockwork 140 m deficit, the plaster height basis, and roof WP (dome footprints).
7. **Room identity:** What algorithm should split a merged villa zone that holds both wet and dry labels? Is OpenTakeoff's door-seal / minimum-passage idea adequate on CAD (not raster)?
8. **Blockwork:** Propose a wall-length conservation equation per floor (architectural centreline = blockwork + RC wall + openings + columns + UNCLAIMED) and the tolerances.
9. **Test design:** Our tests prove consistency, not correctness. What known-answer golden set (minimum size, which populations) gives real evidence for a 95% claim? How should it be frozen against leakage?
10. **Confidence:** Is categorical evidence-class confidence + H / M / L on provisionals sufficient, or should named confidence factors / a numeric score be added? How would it be calibrated?
11. **Provenance:** What minimum per-line provenance (handles, sheet, revision, rule ids, engine version) is needed for a commercial-grade audit trail, and where should it live (registers vs Firestore)?
12. **Architecture:** Should the project runners in `research/external_engine_lab/` be promoted into a generic `engine/projects/` layer with data-only project configs? What is the migration order that does not break the frozen registers?
13. **Agents:** Is there any safe role for LLM agents in QTO (e.g. raster schedule reading with per-cell confidence + human confirmation), or should QTO stay LLM-free?
14. **Revision control:** Recommend an entity-level revision-delta design (handle- or geometry-signature-based) that invalidates the affected quantities only.
15. **Qortuba truth:** Is it valid to keep the PA08 seal (REV_OLD) as a regression anchor while RC1 runs on REV_NEW? What should the new reference be?
16. **Commercial:** Given §38, what is the shortest path to a "QS assistant" product that a Kuwaiti contractor would trust?

---

## 41. Files to send ChatGPT

### FILES TO SEND TO CHATGPT

**Minimum set (send all of these):**

* [ ] `URBAN_PROJECTS_BOQ_CURRENT_FULL.zip`: the whole tracked repository at `1c331c5` + this report + `HANDOFF_EXTRAS/` (R8 spec files, round package MD / JSON, Qortuba PA08 sealed takeoff + owner rules V1, 23010 sealed benchmark JSON, test JUnit XML + non-pass list, rules dump, engine inventory). See `ZIP_MANIFEST.txt` inside.
* [ ] `URBAN_PROJECTS_CLAUDE_HANDOFF.md`: this report (it is also inside the ZIP and in the repository root).
* [ ] `research/external_engine_lab/V3C_FORENSIC_ACCURACY_DONOR_AUDIT.md`: the latest accuracy audit (inside the ZIP; worth attaching separately).

**Real project files (not in the ZIP; upload separately):**

* [ ] **Alsenan / P7757:** architectural `P7757.dwg` and/or `P7757.dxf` (INSUNITS 4 mm) + structural **`ST7757.pdf`** (pages 3, 7, 8, 11–14, 16 matter most for D1–D6). Optional: the freelancer B1 workbooks (concrete / rebar / finishes) for §B.
* [ ] **Qortuba:** REV_NEW DXF (sha `df0e1d69…`, the authoritative one) and REV_OLD DWG (sha `2ec3a9c8…`) + the contractor comparison sheet.
* [ ] **Al Rashed:** the DWG (sha `299c61b1…`, revision 16-11-2025-R3) + the matching PDF set + the historical workbook "الراشد صباح الاحمد" (the only ground truth: insulation 950.22 m², balustrade 57 lm).
* [ ] **23010:** `AR-00` PDF (rev MAR.2023) + the sealed site benchmark (the JSON is in the ZIP under `HANDOFF_EXTRAS/data/golden/23010/`; the PDF is not).

All of these live on this container under `data/inputs/by_sha256/` and `data/golden/`. They are client drawings, so they were deliberately left out of the ZIP.

**Do not send:** `.secrets/`, rate cards / rate library (pricing), `data/experiments` bulk, `data/runs` decodes (1 GB; regenerable).
