# R9 read-only architecture gap study: Urban HEAD vs the research pack

This study is read-only. No production code was changed, nothing was installed, no donor code was copied, and S4 has not been started.

## 0. Evidence basis (v2)

**v1 (a75b845)** was written before the pack arrived. It used the ideas the R9 brief named, Urban's code at HEAD, and the donors held locally at their `DONORS.lock` commits (U-C4N `cdb10638`, OpenTakeoff `e6d2251c`, the christiannp forensic package).

**v2 (this revision)** adds three things:

1. **The delivered pack**, `Urban_BOQ_Research_Pack_2026-10-07.zip` (sha256 `166a7341…5331`). All 23 files were read: 15 docs, the clean-room reference files and the machine-readable files.
2. **A pinned-commit check of the three donors the pack asks to verify.** A blob-less, no-checkout git fetch was used. LICENSE, README, docs and dependency manifests were read; no source file was copied or run, and nothing was installed.

   | Donor | Commit | Licence (from the LICENSE file) | Dependencies |
   |---|---|---|---|
   | RoomGraph | `aec-platform/roomgraph@772f0954` | MIT | none |
   | aec-qto | `aec-platform/qto@82c10016` | MIT | `ifc-spf` (licence not checked) |
   | Rebar-Takeoff | `tolga-ileri/Rebar-Takeoff@54641dd8` | MIT | ezdxf, scipy, pandas, openpyxl, nicegui, pywebview |

   The full register, with confirmed features and limitations, is in `R9_LICENCE_DEPENDENCY_REGISTER.json`.
3. **A licence check of Urban's own runtime imports**, prompted by pack doc 06. This found R9-LIC-01 (PyMuPDF).

Every v1 `PACK_NOT_HELD` field is now filled; the builder refuses to emit one. Donors that the pack names but which were not fetched (cad-ai-agent, ConMCP, tianzheng-dwg-parse, FreeCAD-Reinforcement, Plansight, and the libraries) are marked `PACK_CLAIM_ONLY`.

`PACK_RECOMMENDATION_MAP.json` maps every pack recommendation (doc 01 #1–#18, backlog R9.1–R10.3, docs 05/06/07/14) to its gap-matrix rows. Rows that v2 changed carry a `CHANGED_BY_PACK` list.

Outputs (`build_r9_gap_study.py` regenerates them):

| File | Content |
|---|---|
| `R9_ARCHITECTURE_GAP_MATRIX.json` / `.csv` | 52 rows (36 v1, 26 of them updated by the pack, + 16 new), all brief §2 columns plus PRIORITY, CHANGED_BY_PACK, DECISION |
| `PROVENANCE_FIELD_COVERAGE.csv` | 22 fields × 4 record families |
| `SCALE_GATE_AUDIT.json` | DXF/DWG, vector PDF, raster PDF, IFC |
| `DONOR_TECHNIQUE_MATRIX.json` / `.csv` | 27 techniques × Urban / U-C4N / christiannp / RoomGraph / OpenTakeoff / Rebar-Takeoff / aec-qto |
| `R9_LICENCE_DEPENDENCY_REGISTER.json` | verified donors, pack-claim-only donors, Urban runtime imports |
| `PACK_RECOMMENDATION_MAP.json` | pack recommendation → gap-matrix rows |

Status counts (v2): 23 PARTIAL, 12 ALREADY_PRESENT, 9 URBAN_STRONGER, 3 CONFLICT, 2 MISSING, 3 NOT_APPLICABLE.

Recommendation counts (v2): 17 KEEP_URBAN, 14 ADAPT, 3 ADOPT, 4 CHALLENGER_ONLY, 3 REJECT, 11 DEFER.

## 1. State model (brief §3)

**Kept.** Urban's model is richer than the pack's examples (verified / review_required / conflict / assumption):

- three axes: measurement, authority, and a derived release state;
- six scenario layers: VERIFIED, LOWER_BOUND, BEST_PROVISIONAL, LOW, HIGH, UNQUANTIFIED.

Collapsing them would lose two distinctions:

- whether a "review_required" value is a bound, a candidate or blocked;
- the guarantee that uncertainty is never zero and never silently enters procurement.

No better architecture was shown, so the model stays (R9-ST-01: URBAN_STRONGER / KEEP_URBAN).

## 2. Quantity Fact Core (brief §4)

**A. Does Urban already have an equivalent?** Yes, in pieces, along three paths:

| Path | Chain |
|---|---|
| Architecture | `observations` (neutral source records) → `CANONICAL_MEASUREMENT_INPUT` (fail-closed) → methods → evidence rows → `boq_canonical` / `boq_report` (copy-only) |
| Structure | S1 census → `structural_schedule` rows → V3b BOQ lines |
| Coverage round | scenario parts |

There is no single named contract shared by all three.

**B. Are current facts neutral of measurement convention?** Source facts are: observations, census and handles. Quantities are not:

- `beam_occurrence_recovery`: B × (D − t);
- `column_concrete_geometry`: net of the slab above;
- `physical_wall_faces`: interval − terminating member, net of openings;
- `ground_slab_recovery`: cells net of beams.

**C. Do geometry modules embed BOQ rules that belong in a profile?** Yes, the four conventions above. They are explicit and documented, not hidden. A dual-basis precedent exists in `engine/contractor_measurement.py`.

**D. Would a new QuantityFact dataclass duplicate current models?** Yes. It would duplicate `CanonicalMeasurementInput`, scenario parts and BOQ evidence rows, and risks losing the state axes.

**E. Can the concept be an interface around existing models instead of a rewrite?** Yes. A contract and validator that maps every BOQ-bearing record to the QuantityFact fields, or fails.

**F. Smallest safe improvement:**

- a `CONVENTION_ID` stamp on every quantity record (R9-QF-02);
- the receipt validator (R9-PR-01).

No new object hierarchy.

## 3. Provenance (brief §5)

See `PROVENANCE_FIELD_COVERAGE.csv`.

- **The architectural R8 path is strong.** `run_manifest` carries:
  - RUN_INPUT_DIGEST;
  - the revision anchor sha;
  - the unit claim and scale;
  - claims offered, applied and rejected;
  - policy digests;
  - method and contract version;
  - kernel versions;
  - code commit plus CODE_BOUND_DIGEST.

  `boq_report` rows carry the TRACE fields.
- **S1 census rows** carry the drawing, handles, sheets, page and raw ATTRIBs.
- **The gap is structural V3b BOQ lines.** Their trace is free text. They have no handles, no drawing sha, no unit context, no version stamp and no remediation record.
- **Coverage-round parts** carry states and bounds, but not per-part drawing sha or revision.

Do **not** build a second provenance system. Extend the existing receipt (run manifest plus trace) to structural lines and scenario parts (R9-PR-01, P0).

Two fields stay absent by design:

- confidence factors, because Urban uses authority levels (R9-PR-02);
- human-reviewed geometry, because claims never edit geometry (R9-PR-03, DEFER until a review UI exists).

## 4. Scale gate, per source (brief §6)

See `SCALE_GATE_AUDIT.json`.

- **DXF/DWG:** a true gate exists and is stronger than the research proposal.
  - `frame.py` derives UNIT_CONTEXT from at least two independent evidence kinds within 0.5 %. INSUNITS counts only as a declaration.
  - DIMLFAC enters through dimension-family ratios.
  - Scale notes are observations, not truth; mixed scales raise a flag.
  - Region transforms are kept separate from native units.
- **Raster PDF:** a gate exists. `raster_evidence.calibrate` needs at least two printed dimensions.
- **Vector PDF:** **partial.** The frame transform and calibration objects exist, but no rule blocks a PDF-derived length that lacks a VERIFIED page UNIT_CONTEXT. **This is the one real missing gate** (R9-SC-02).
- **IFC:** no route. Deferred until an IFC project arrives.

PDF logic is not imposed on CAD model space.

## 5. RoomGraph (brief §7). Not ported.

| Idea | Urban equivalent | Verdict |
|---|---|---|
| Wall-line pairing before segment pairing | `wall_bands` V5, fragmented-mate resolver, `wall_band_reconciliation` | present; challenger only |
| Corner bridge repair | `junction_recovery`, `junction_patch`, reversible zero-material `topology_closures` | **Urban stronger** (evidence-gated, reversible) |
| T / crossing splitting, planar arrangement | TS01 exact noding, Route B half-edge shadow, GEOS cross-check | present (two independent routes) |
| Minimal-cycle rooms | planar faces = sites; `room_partition_graph` | present; challenger only |
| Opening classification | `opening_evidence` V3, authority, completion, `door_transition` | **Urban stronger** |
| Room adjacency graph | `room_matrix` view; side-aware window host | **partial: the genuine gap** (wall Method C was not run because no adjacency graph exists) |
| Multiple scale candidates | unit evidence families | present |
| Strict / no-guess | fail-closed everywhere | **Urban stronger** |

Against your weak areas:

- **Room closure / wall topology:** Urban already has the stronger primitives. Its residual failures are source gaps, not a missing algorithm.
- **Physical wall faces:** recovered in the coverage round.
- **Plaster / ceramic / paint sides, door gaps, open plan, wet rooms:** these need the **adjacency graph** (which room each face serves).

**Decision:** CHALLENGER_ONLY, after S4, as an independent vector-PDF room route for PDF-only projects. It must be benchmarked region by region against TS01 on a project that has both CAD and PDF (R9-RG-09).

Fixtures needed:

- hairline gap at a door;
- overshooting partition;
- open-plan with a column line;
- room split only by a floor-finish change;
- duplicate face;
- finish-line pair.

False-positive risk: bridging gaps silently merges rooms. Urban's evidence gate exists to prevent exactly that.

## 6. Rebar-Takeoff (brief §8). The most important pre-S4 finding.

| Capability | Urban |
|---|---|
| TEXT / MTEXT / ATTRIB / INSERT reading | present (K2 kernel, observations) |
| Bar-token parsing | **CONFLICT: three separate grammars** — `schedule_grammar.parse_bar`, `structural_schedule.bar_spec`, `slab_rebar_binding.parse` |
| Member marks | **Urban stronger** (exact tokens, B / CB / SB namespaces) |
| Nearby-dimension matching | partial; deliberately "never nearest-text" for members |
| Spatial, layer and block context; duplicates; ambiguity | per element family only |
| Confidence | **Urban stronger** (interpretation state plus authority) |
| Source coordinates | present (`schedule_grammar.cell`) |

What it genuinely adds before S4 is two things, both Urban-native, neither a port:

1. **One bar-token grammar** with one regression corpus. Every bar token in ST7757 must parse identically, and any disagreement is listed.
2. **A structure-wide annotation census with conservation.** Every bar-like token must end in exactly one terminal state:

   tokens in = bound + definition-only + unbound + unreadable + duplicate

**Decision:**

- the annotation evidence path becomes **PRODUCTION_EVIDENCE_PATH, Urban-native**;
- Rebar-Takeoff itself: licence verified MIT at `54641dd8`, but **rejected as a code or fixture donor (v2)**.
  - Its grammar is Turkish-convention (`16[16/20`, `L=400`, `BOY=`), not ST7757's (`5Ø10/m`, `8 Ø 12`, schedule ATTRIBs).
  - It binds lengths to the *nearest* length label, which Urban's beam binding forbids (R9-RT-04 is now CONFLICT / REJECT).
  - It describes itself as approximate.
  - The only parts kept are two metrics for the annotation census: automatic match rate and included-in-totals rate. Its "unresolved rows stay out of the total" rule is something Urban already does.

S4 footing bars mostly come from schedule ATTRIBs, which S1 already reads with handles and raw values. The real S4 blocker is BOXED semantics, and that needs a source or a claim, not a parser.

## 7. OpenTakeoff contracts (brief §9)

| Contract | Urban |
|---|---|
| Scale gate | **Urban stronger** (`scaleConfirmed` warns but does not block; rejected in DONORS.lock) |
| Quantity provenance schema | partial; adopt the idea of **actor ≠ method** on every receipt |
| Machine-original vs human-corrected geometry | defer; needs a review UI; Urban never edits geometry |
| Confidence factors | review priority only, never release |
| Measured vs procurement | present |
| Shared UI/MCP math | not applicable ("code calculates, agents never do") |
| Marked-up review export | partial; defer |

Apache-2.0: clean reimplementation only, with NOTICE.

## 8. Declarative rule engine (brief §10)

Urban's rules are already data-like:

- `urban_methods` V1 / V3: id@version, applies_to, never_applies_to, parameters, precedence;
- the `waste_procurement` hierarchy;
- profile JSONs;
- the structural rule register;
- the promotion lifecycle.

The arithmetic stays in code.

**Whether they can be expressed declaratively without losing authority, state and provenance behaviour is unproven.** The hard parts are precedence (SOURCE > OWNER_FACT > FALLBACK > BLOCKED), fail-closed blocking and convention stamps.

`URBAN_KW_V1` does not exist today. First build the **URBAN_KW_V1 golden fixture**: every released quantity plus its receipt, hashed from the frozen V3b and coverage-round outputs (R9-RE-02, P1). Migration (R9-RE-01) is deferred until a declarative profile reproduces that golden set byte for byte.

## 9. Geometry backend (brief §11)

Actual state:

- `engine/source` is stdlib-only by test, with two declared shapely exceptions: `topology_crosscheck` and `ground_slab_recovery`;
- about 45 legacy `engine/` modules import shapely directly, undeclared;
- `run_manifest` already records the loaded GEOS version.

**Decision:** formalise a **GeometryBackend register** (R9-GB-01, P1):

- every geometry-library import is declared with a backend id (URBAN_NATIVE / SHAPELY / future CLIPPER2 / CAD_ORACLE);
- a test enforces the declarations;
- run manifests carry the backend ids.

It is a contract, not a port. Porting the legacy modules is deferred (R9-GB-02).

## 10. Licence and dependency risks

| Item | Status |
|---|---|
| OpenTakeoff | Apache-2.0: clean reimplementation, NOTICE |
| U-C4N | MIT |
| christiannp | UNKNOWN; repo unresolved |
| OpenConstructionERP | AGPL: ideas only |
| RoomGraph | MIT, verified at 772f0954; no dependencies; ideas only |
| aec-qto | MIT, verified at 82c10016; depends on `ifc-spf` (licence not checked); pattern only |
| Rebar-Takeoff | MIT, verified at 54641dd8; heavy UI/build dependencies; nothing reused |
| **PyMuPDF (in Urban today)** | **AGPL-3.0 or commercial. Imported by 6 production `engine/` modules** (`pdf_vector_evidence`, `vector_source`, `geometry`, `glyph_text`, `sanitary_source`, `ingest/harness`). Not in DONORS.lock or THIRD_PARTY_PROVENANCE; `requirements.txt` lists it only as an optional comment. **R9-LIC-01: owner licence decision needed** |
| LibreDWG | GPL-3.0, used as an external binary producing JSON (not linked) |
| shapely | BSD-3; already present |
| ezdxf | MIT; K2 only |
| Clipper2 (pyclipper) | BSL-1.0 / MIT; not installed |
| ifcopenshell | LGPL-3.0; not installed; only for an IFC project |

No new dependency is recommended before S4. S4 reads DXF only, so R9-LIC-01 does not block it; the licence decision is still needed now.

## 11. Priority plan (genuine gaps only)

| Rank | Item | Why | Before S4? |
|---|---|---|---|
| P0 | Unified bar-token grammar + structure-wide annotation census with conservation (R9-RT-02, RT-05) | Three parsers may read one token differently; S4 consumes these tokens | **yes** (research/test first, then the production evidence path) |
| P0 | Quantity receipt on structural lines and scenario parts, on the existing run-manifest / trace shape (R9-PR-01) | Footing rebar must carry handles, drawing sha and rule id from day one | **yes** (the S4 output format) |
| P0 | Version stamps in comparison engines (R9-PR-05) | Stop old and new values mixing | yes (small) |
| P1 | CONVENTION_ID on quantity records (R9-QF-02); QuantityFact contract validator (R9-QF-01) | Profiles become possible without a rewrite | after S4 (S4 should emit the stamp from the start) |
| P1 | Vector-PDF hard scale gate (R9-SC-02) | The only missing true gate | after S4 (no PDF quantity in S4) |
| P1 | Room adjacency graph (R9-RG-06) | Wall Method C, plaster sides, wet rooms | after S4 |
| P1 | GeometryBackend register (R9-GB-01) | Declared imports, recorded backend | after S4 |
| P1 | URBAN_KW_V1 golden fixture (R9-RE-02) | Prerequisite for any rule migration | after S4 |
| P1 | Actor / method fields on receipts (R9-PR-04) | Audit | after S4 |
| P1 | **PyMuPDF licence decision + third-party manifest gate (R9-LIC-01, R9-LIC-02)** | AGPL in production `engine/` | decision now; migration or licence after S4 |
| P1 | explain_quantity over the receipt (R9-EX-01); per-family metrics registry (R9-BM-01) | Audit; S4 must emit bar-level records | after S4 |
| P2 | Permissive PDF stack (R9-PDF-01); rule lint (R9-RE-03); provenance-schema export view (R9-PR-07); match-line identity (R9-REV-01) | — | after S4 |
| P2 | RoomGraph vector-PDF challenger (R9-RG-09; a non-curved benchmark project is required); declarative profile migration (R9-RE-01) | Only with a benchmark project | after S4 |
| DEFER | Human-correction lineage; numeric confidence; marked-up export; IFC; legacy shapely port; formwork contact surfaces; MCP surface; impact-ordered review queue | No current consumer | — |
| REJECT | Rebar-Takeoff as a donor; nearest-label length matching; OR-Tools (native optimiser exists); RoomGraph door-width scale fallback; AUTO_PASS status | — | — |

Answers to brief §13:

- **A. Rebar-Takeoff-style annotation evidence path:** YES before S4, Urban-native.
- **B. RoomGraph vector-PDF challenger:** NO; after S4.
- **C. Provenance / scale normalisation:**
  - provenance receipt: YES before S4 (as S4's output format);
  - vector-PDF scale gate: after S4.
- **D. Formal geometry backend:** NO; after S4.
- **E. Declarative profile migration:** NO; golden fixture first, after S4.


## 12. What changed from a75b845 (v2 summary)

1. **New conflict, PyMuPDF (R9-LIC-01).**
   - AGPL-3.0 (or commercial) PyMuPDF is a runtime import of 6 production `engine/` modules, and it is undeclared.
   - v1 missed this because it audited functions, not licences.
   - It needs an owner decision: buy a commercial licence, or replace the PDF lane with pypdfium2 + pdfplumber (R9-PDF-01).
   - It does not block S4, which reads DXF only.
   - A third-party manifest gate (R9-LIC-02) stops a recurrence.
2. **Rebar-Takeoff downgraded.** v1 had it as challenger / test-fixture donor; v2 rejects it as a code or fixture donor.
   - Turkish label grammar.
   - Nearest-label length binding, which conflicts with Urban.
   - Approximate by design.
   - Its MIT licence is verified.
   - The pre-S4 P0 work (one grammar plus an annotation census) is unchanged and stays Urban-native. Only Rebar-Takeoff's two match-rate metrics are adopted.
3. **RoomGraph verified, decision unchanged (CHALLENGER_ONLY, P2, after S4).**
   - MIT, with no dependencies.
   - Its own LIMITATIONS rule out curved walls, single-line walls, walls over 420 mm and scans, so Alsenan's arches are out of scope and the benchmark needs a non-curved project.
   - Its door-width scale fallback is rejected as evidence.
   - Its room-adjacency concept supports R9-RG-06 (P1), which Urban builds on its own TS01 sites.
4. **aec-qto verified, decision unchanged (DEFER migration; golden fixture P1).**
   - MIT; it is IFC classification, not measurement.
   - New P2 row R9-RE-03: a rule lint for dead or shadowed methods.
5. **Pack proposals Urban already covers.**
   - Shapely as a dependency: Urban already uses it.
   - Rebar evidence ladder.
   - BarLengthBreakdown and laps.
   - Ambiguity excluded from totals.
   - Drawing survey.
   - The pack's verified / auto_pass / review_required states: Urban's three axes are kept, and AUTO_PASS is rejected.
6. **New deferred or P2 rows:** revision / match-line identity, explain_quantity, the per-family metrics registry, the permissive PDF stack, formwork, the MCP surface, typed agent operations, review-queue ordering and a provenance-schema export view.
7. **Before S4 is unchanged:** unified bar grammar plus annotation census; receipt fields on S4 outputs; version stamps in comparison engines. The one addition is that the PyMuPDF licence decision should be taken now, though the work comes after S4.
