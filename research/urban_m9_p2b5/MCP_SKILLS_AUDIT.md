# CAD MCP and skills capability audit (Phase 2B-5 Stage D)

**Conclusion.**

- **No CAD MCP server is connected in this session**, so no MCP could be benchmarked. The benchmark has a slot for
  one (`MCP_ADAPTERS` in `tests/m9_p2b5_bench/bench_run.py`). Its fixtures now cover every feature Part 4.2 lists,
  with independent truth.
- The two readers that could be run are the engine and an independent ezdxf + shapely reader. Both were measured on
  16 synthetic plans.
- The benchmark found two engine defects and one refinement of a real-plan finding:
  - **D-D1:** layer roles inferred from a single instance.
  - **D-D2:** arc walls kept as chords.
  - **D-C1 refined:** a door drawn two ways at one opening. An opt-in fix is in ARCH_TAKEOFF_V2.6 (correction
    D-V26-06).
- Six repository-local Urban skills were written (`.claude/skills/`). None of the synced third-party skills is used
  for measurement.

## 1. MCP inventory (this session, verified)

| MCP server | what its tools do | reads CAD geometry? | use for Urban |
|---|---|---|---|
| Autodesk_Product_Help | product catalogue, help-content search | no (documentation only) | look up AutoCAD behaviour (e.g. DIMLFAC, XREF binding) - documentation, not evidence |
| Claude_Code_Remote | sessions, scheduled tasks, repositories | no | session management |
| github | repository operations | no | repository only |
| Claude_Docs, Google_Drive | documents, files | no | never a destination for private drawings without the owner's instruction |
| Canva, Higgsfield | design and media generation | no | not to be sent drawings or BOQ data |

The CAD MCP candidates of earlier stages, all read-only code reviews outside the repository:

| candidate | licence | status this session | earlier finding (handoff §10, donor table) |
|---|---|---|---|
| U-C4N/Autocad-MCP (@cdb1063) | MIT | NOT_AVAILABLE (not connected) | strong donor of ideas. Used: the OCS algorithm reference (clean reimplementation), the explicit skip / MINSERT / XREF record rules, plain-text cleanup (one small adaptation, notice kept). Rejected: unit inference overriding $INSUNITS, silent identity on a bad extrusion |
| beiming183-cloud/AutoCAD-MCP (@11f7c47) | MIT | NOT_AVAILABLE (not connected) | useful patterns: field-level read-back diffs, revision anchors, digests; its geometry digest is not a physical proof (blind to the object coordinate system) |
| christiannp/autocad | - | NOT_AVAILABLE (repository inaccessible in the earlier audit) | its outputs, run by the owner, were an external estimate in earlier stages |
| C48H74, felixalmesberger MCP repositories | MIT | NOT_AVAILABLE | read-only research clones; ideas only |

Connecting any MCP server is an owner decision (`.claude/skills/urban-mcp-benchmark/SKILL.md`, escalation). When one
is connected, it receives the synthetic fixtures only, through read-only inspection commands (no LISP, no save, no
drawing edits).

## 2. The benchmark fixtures (Part 4.2), with independent truth

| Part 4.2 feature | case(s) | truth source |
|---|---|---|
| closed / open polylines | C03 (wall faces chained into LWPOLYLINEs; one ring opened into two runs; the column a closed LWPOLYLINE) | B04's hand truth |
| nested INSERTs, mirrored blocks, non-uniform scaling, coordinate transformations | C01 (walls in block WALLS_IN, inserted at scale 2.0 / 0.5 in WALLS_OUT, inserted mirrored, turned 90 degrees and moved; the contents are the inverse transform, so the world geometry is B01's) | B01's hand truth; the round trip checked to 1e-12 mm |
| mirrored arcs, rotated doors | B02 (mirrored door block), B06 (27-degree plan), B09 (the whole plan mirrored) | hand truth, mirrored / turned |
| curved walls | B10 (an ARC inner face and a bulged LWPOLYLINE outer face) | the circular-segment formula |
| door openings, window blocks | every case; C05 (the window as a unit block, xscale = width) | hand truth |
| dimension text, Arabic room labels | C04 (Arabic room words, linear DIMENSIONs, one inside a room with a text override) | B05's hand truth |
| metre and millimetre units | C02 ($INSUNITS 6, every value / 1000) | B01's hand truth |
| XREF limitations | C06 (the walls in an external reference whose file is not supplied) | truth = a refusal |
| room polygon extraction | all 16 | hand truth |

## 3. Results: the engine and the independent reader on the CAD fixtures

| reader | geometry | openings | unsupported / refused | runtime per case | reproducibility |
|---|---|---|---|---|---|
| engine, declared layer roles | exact (area, perimeter, IoU 1.0) on every straight-walled case and every encoding (C01 - C05); B10: area exact, polygon the chord (D-D2) | exact on every case | C06 refused: `BLOCKED: XREF_NOT_SUPPLIED`, no BOQ published | about 1.1 s | byte-identical reruns (fixed DXF metadata) |
| engine, inferred layer roles | as declared, except the column of B04 / C03 not deducted (+2.18 %) | a door, window or column layer drawn once is not recognised: doors and windows become passages (D-D1) | C06 refused | about 1.1 s | idem |
| independent reader (ezdxf + shapely) | exact; B10 to the 0.5 mm arc flattening (area −0.008 %) | exact, except B08's lobby door (it reads labelled rooms only) | C06 refused: `NOT_SUPPORTED: XREF ... not resolved`; no unit → NOT_SUPPORTED | about 0.01 s | deterministic |

Read-only safety: every reader opens the DXF read-only. The engine writes only to its output folder. No CAD
application was started and no command was run on any drawing.

### Defects found by the fixtures

- **D-D1. Layer roles inferred from a count.** Inferring a DOOR layer needs two anchored swings, and a COLUMN layer
  three filled squares (`engine/source/arch_plan.py` `layer_roles`). A drawing with one door types its door and
  window as passages; one column is not deducted.
  - Real plans with many doors are not affected.
  - Partial plans and single-room sheets are.
  - Remedy available today: `--layer-roles` (recorded in RUN_RULES).
- **D-D2. An arc-walled room is kept on its chord.** The face area and boundary length follow the arc exactly. But
  `polygon_m`, `rect` and `dims` are the chord polygon (B10: 4.00 x 3.00 m), so three things follow:
  - the membrane cutting plan is laid for the chord rectangle;
  - the curved wall band is missing from `ARCH_WALLS` and the wall-run line (11.0 lm gross against 14.22 lm);
  - polygon-based tile layouts would be laid on the chord.

  The area lines are right; the layout and wall-run lines are not. Real-plan exposure (private, aggregate):
  - 4 of 38 rooms have an arc-bounded face, all dry, with |Δ| of 5.1 m2 in total between face and chord;
  - wall-layer arcs total 4.5 m of face line, about 0.7 % of the wall run.

  Tests: `tests/m9_p2b5/test_p2b5_curved_wall.py`, which asserts the defect as found. The fix (arc-aware polygons,
  curved wall bands) is ranked in the roadmap; it touches the room model, so it needs its own opt-in method step.
- **D-C1, refined (from Stage C).** Of three bathroom door blocks near passages on the real plan:
  - two close their own wall-to-wall doorways beside the passage. They are separate PROVISIONAL doors, which is
    correct; the independent reader confirms one of them as a 0.80 m inner doorway.
  - one closes a 0.80 m gap *inside* a 1.02 m band opening read as PASSAGE: one opening drawn two ways.

  ARCH_TAKEOFF_V2.6 (D-V26-06) reconciles that case. The passage becomes a DOOR held from every released total, with
  both widths recorded. On the real plan the effect is:
  - door count right;
  - plaster error −0.94 → −0.15 m2 and wall porcelain error −0.42 → −0.15 m2 in that room;
  - one doorway strip moves from porcelain to a marble threshold (0.15 m2, floor area conserved);
  - nothing else changes.

  Tests: `tests/m9_p2b5/test_p2b5_door_reconcile.py`.
- **C06 (not a defect).** Both readers refuse a missing XREF rather than measure an empty plan.

## 4. Reverse engineering: ideas re-implemented and demonstrated (Part 4.3)

| topic | implementation (clean, Urban-owned) | demonstrated by |
|---|---|---|
| geometry normalisation, units | `$INSUNITS` → mm per unit (no unit: NOT_SUPPORTED); the engine's admission gate checks units against the drawn geometry | C02 |
| block transformation mathematics | M = T·R·S per INSERT, composed through nesting; the fixture is built with the inverse transform | C01 (round trip to 1e-12 mm) |
| arc orientation | the arc centre from OCS to WCS; a mirrored block reverses the sweep (Mx R(r) S = R(−r) S(−sx)) | B02, B09 (doors exact under mirroring) |
| door-symbol recognition | strict fit + V2.6 reconciliation (leaf closure inside a passage; review limits for a swing closing nothing) | `test_p2b5_door_reconcile.py` (20 cases, boundaries included) |
| room boundary reconstruction | collinear-gap closure rules + polygonise (independent reader); TS01 topology (engine) | all cases |
| PDF vector extraction | PyMuPDF paths → wall faces by parallel partner → the same closures | `vector_pdf_rooms`, exact on B01 - B10 |
| CAD / PDF coordinate matching | the DXF and its PDF at a known scale through the hybrid rules: AGREE on every room | `test_the_hybrid_rules_on_the_benchmark` |
| capability refusal (U-C4N's contract) | NOT_SUPPORTED / BLOCKED states instead of a silent result | C06, `test_no_ocr_is_not_supported` |

No code was copied from an incompatible licence. The vision research (`FLOORPLAN_AI_RESEARCH.md`) records the GPL and
non-commercial projects that were read for ideas only.

## 5. Skills inventory

**Synced third-party skills, reviewed before any use.**

| skill | what it is | relevance | decision |
|---|---|---|---|
| quantity-takeoff-rules | Gulf BOQ measurement notes: blocks, mortar, lintels, plaster, tiles with size-based waste, skirting, waterproofing upturn 150 - 300 mm; includes the user's 2025 supplier prices | relevant as a secondary reference; the hierarchy it states (contract / specification first) agrees with the owner's | **not a rule source**: the owner rule store and registry govern. Its generic skirting rule (perimeter minus doors) conflicts with the owner's no-skirting rule under full-height wet-room tile. Its prices are not used or reproduced. |
| cad, dxf, engineering-drawing | text-to-CAD generation of mechanical parts (build123d / cadgen via uvx) | not for reading architectural plans | not used |
| pdf | general PDF operations (proprietary licence noted in the skill) | partly: PDF text / vector reading | not needed (PyMuPDF used directly) |
| reverse-engineer-anything | an npm CLI for apps, binaries, websites | not CAD geometry | not used |
| deep-research, skill-creator, docx / pptx / xlsx, browser and workspace skills | research coordination, office files, browsing | general tooling | xlsx conventions followed for workbooks; none used for measurement |

**Repository-local Urban skills (written in this stage, `.claude/skills/`).** Each defines purpose, trigger, inputs,
authorised tools, safety, outputs, tests and escalation. `tests/m9_p2b5_bench/test_skills.py` checks each one's
structure, its cited paths and its safety section.

| skill | for |
|---|---|
| urban-cad-audit | takeoff readiness of a drawing: units, frames, layer roles, door symbols, curved walls, XREFs (read-only) |
| urban-boq-proof | the verification chain for a BOQ quantity: rule → drawing → geometry → formula → independent value → engine value → difference → BOQ impact |
| urban-mcp-benchmark | benchmarking any reader or MCP against the synthetic truth before it is trusted |
| urban-floorplan-vision-review | running the vision prototypes and the hybrid rules; never a BOQ quantity from vision |
| urban-freeze-integrity | proving frozen methods unchanged (byte identity, freeze verifier) |
| urban-rule-reconciliation | rule precedence and conflicts, with provenance classes and owner questions |

## 6. Recommendation

1. Keep the native engine as the reader. Use the independent reader as the parity oracle in tests. Adopt no MCP
   until one is connected and passes this benchmark on the synthetic fixtures.
2. Ask the owner to connect a CAD MCP only if a capability is missing that DXF reading cannot provide: native DWG
   without conversion, or proxy / custom objects. Run it on the synthetic fixtures first.
3. Fix D-D2 next in an opt-in method step (arc-aware room polygons and curved wall bands). Keep D-D1 covered by
   declared roles until the inference is reworked.
