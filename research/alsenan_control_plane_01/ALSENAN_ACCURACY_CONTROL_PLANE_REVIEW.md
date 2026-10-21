# ALSENAN — Forensic Accuracy & Control-Plane Audit, Round 1 (diagnose before fixing)

**Scope.** This round only diagnoses. No production module, frozen register or release quantity was changed.
No benchmark value was used to choose, move or "correct" any number. Qortuba (RC1_REFERENCE) was not touched, and no donor code entered production.

**Deliverables.** All under `research/alsenan_control_plane_01/`:

| File | What it is |
|---|---|
| `extract_live.py` → `evidence/LIVE_EXTRACT.json` | Facts the frozen registers do not carry: TS01 semantic state per room, wet labels and the site each falls in, wall-band ledger, column occurrence state against emitted kg, beam occurrences, footing and strap rows. |
| `extract_schedules.py` → `evidence/ST7757_SCHEDULE_EXTRACT.json` | Every attributed schedule block in ST7757.dxf (FT 12, FTB 5, SBT 35, C-BEAM2 9, C-BEAM3 4, CGT 12), 245 loose reinforcement texts, and the simple-beam REMARKS column bound to its rows (23). |
| `build_registers.py` → `registers/*.json` | The 10 registers plus `INDEX.json` (sha256). Offline and deterministic; rebuilds in about 3 s. |
| `tests/alsenan_control_plane/test_control_plane_r1.py` | 35 diagnostic tests plus 23 strict-xfail control gates. |

Numbers marked `DIAGNOSTIC_MAGNITUDE_NOT_A_QUANTITY` size a defect only. They are never a release value or a target.

---

## A. Physical space ≠ semantic zone ≠ trade region ≠ release line

Four objects are conflated on the Alsenan path:

| Layer | Producer | What it answers |
|---|---|---|
| Physical space (site) | TS01 `room_topology_v3` | Is there a closed region? (`physical_status`) |
| Semantic zone | TS01 `res["semantic"]` (SEMANTIC_ZONE_POLICY_V1) | How many named functions live in it, and are their boundaries known? |
| Trade region | `alsenan_v3_layers.finishes()` | Which finishes apply where (floor, skirting, tile, WP …)? |
| Release line | `alsenan_v3b_lines.mk` → `release_model.release` | Does the quantity enter totals or procurement? |

**The defect is that the Alsenan path never reads layer 2.**
- TS01 computes `semantic` and `SZ.trade_regions()` would return `BLOCKED_SEMANTIC_ZONE` for unresolved zones. Only the Qortuba R8.9–R8.14 labs consume it.
- Alsenan instead re-derives semantics from the joined name string (`_room_class`) and passes it straight to trades.

`ROOM_SEMANTIC_TRADE_RELEASE_REGISTER` shows the four layers side by side for all 30 rooms. Each layer is read from its own register, so a mismatch becomes a *flag*, never a correction.

## B. Semantic-zone integration audit

| Room | TS01 state | Alsenan class | Floor (in total) | Skirting | Ceiling | Wet labels inside |
|---|---|---|---|---|---|---|
| GF-Z04 *PANTRY / SALOON / RECEPTION / Wash / DINING / GARDEN* | ONE_PHYSICAL_SPACE_MULTIPLE_SEMANTIC_ZONES_UNRESOLVED | DRY | 155.655 m² URBAN_STANDARD, procurement-eligible, conf. H | 87.368 m | 139.65 m² | Wash / مغسلة → **no tile, no WP** |
| GF-Z06 *DEWANEYA / Wash* | same | DRY | 24.94 | 14.217 | 24.94 | Wash → **no tile, no WP** |
| 1F-Z06 *VOID / LIVING AREA* | same | DRY | 63.661 (79.666 − 16.005 void) | 80.823 | 79.666 | — |

Root cause is `alsenan_v3_layers.py:126–131` (`_room_class`): a multi-name zone resolves "DRY wins" (`return "DRY" if "DRY" in cls else …`).

Consequences:
- A wet sub-zone inside an open plan loses its tile and WP.
- GARDEN (EXTERNAL) inside GF-Z04 is floored in porcelain.

Seeded property test: the result is order-invariant, so the defect is the rule itself, not ordering.

## C. Flooring / ceiling / skirting release audit

- `alsenan_v3_registers.py:255`: `"COMPUTED" if r["status"] == "COMPUTED" else "COMPUTED"`. Both branches are identical, so room status never reaches the floor line.
- Skirting (`:259`), thresholds (`:264`) and ceiling (`:278`) are hard-coded `COMPUTED`.
- A metamorphic test mutates every room status to BLOCKED; the 30 floor statuses do not change.

**Decomposition of the 447.225 m² floor total** (independently re-derived in a test from the frozen ROOM + FINISH registers):

| Part | m² |
|---|---|
| Rooms with status COMPUTED | 121.974 |
| Rooms with status COMPUTED_REVIEW | **325.251** |
| of which DRY | 279.823 |
| of which UNKNOWN | 36.210 |
| of which WET | 9.218 |

**ChatGPT's 325.25 m² is confirmed.**

In V3b, every one of those floor lines is `URBAN_STANDARD` or `DERIVED`: `in_total = True`, `procurement_eligible = True`, commercial confidence `H` ("AS TECHNICAL").

The same holds for skirting (12 `F-SK` lines DERIVED) and ceilings (25 `CE` lines URBAN_STANDARD). Plaster and paint lines are technically BLOCKED where faces are blocked, but are procurement-eligible through PROVISIONAL_SOURCE_DERIVED (e.g. the GF-Z04 plaster sequence, 419.95 commercial). Wall tile and WP follow `room_class` only (see J).

## D. Release-model audit and migration design

**Today (`engine/source/release_model.py`, TWO_LAYER_RELEASE_V1):**
- `TECH_IN_TOTAL` includes `PARTIAL` and `URBAN_STANDARD`.
- `ALWAYS_ELIGIBLE = TECH_IN_TOTAL + OWNER_APPROVED_PROVISIONAL`.
- With no commercial record, the commercial view copies the technical one as `AS TECHNICAL`, confidence `H`.

So:
1. A PARTIAL population (a lower bound) is procurement-eligible as if complete.
2. A fallback (URBAN_STANDARD) material on an unproved room is indistinguishable from a measured one.
3. Confidence `H` is asserted, not derived.

**Proposed state set.** Design only; nothing is implemented this round.

| New state | Meaning | Technical total | Commercial total | Procurement |
|---|---|---|---|---|
| VERIFIED_COMPLETE | Population proved complete; every member measured or derived from source | yes | yes | yes |
| VERIFIED_PARTIAL_LOWER_BOUND | Measured members only; population known to be larger | yes, labelled "≥" | yes, labelled | **no** (until owner approves or completes) |
| PROVISIONAL | Inferred / fallback / code method with method, assumption, low–high | no | yes | only if owner-approved |
| BUDGET | Allowance | no | beside the total | no |
| BLOCKED | Evidence missing or conflicting | no | no | no |
| NOT_IN_SCOPE | Owner scope decision recorded | no | no | no |

**Backward-compatible migration:**
1. Add `release_state` beside the existing `technical.class` / `commercial.class`. Derive it with a pure function from (class, population-completeness flag, upstream room/occurrence status, owner approval). Do not change any existing key.
2. Map existing classes as follows:
   - MEASURED / DERIVED / RASTER_DERIVED / SOURCE_RULE / OWNER_PROJECT_FACT → VERIFIED_COMPLETE, **only when** the upstream status is COMPUTED and the population is complete; otherwise VERIFIED_PARTIAL_LOWER_BOUND or PROVISIONAL.
   - PARTIAL → VERIFIED_PARTIAL_LOWER_BOUND.
   - URBAN_STANDARD and CODE_METHOD → PROVISIONAL, unless an owner fact names the rule.
   - PROVISIONAL_* → PROVISIONAL.
   - BUDGET_ESTIMATE → BUDGET.
   - REVIEW / BLOCKED / BLOCKED_SOURCE_CONFLICT / NOT_IN_SOURCE / PENDING / TRUE_BLOCKER → BLOCKED.
   - NOT_IN_SCOPE → NOT_IN_SCOPE.
3. Recompute `procurement_eligible` from `release_state` only. Keep the old flag as `procurement_eligible_v1` for one release and diff the two sets in a register.
4. Confidence becomes a derived field (evidence grade of the weakest input), never a literal `"H"`.
5. Gate G07 (`PARTIAL` not procurement-eligible) is the acceptance test for step 3.

## E. STRUCTURAL_SOURCE_COVERAGE_REGISTER (101 rows)

| State | Count |
|---|---|
| CONSUMED_COMPLETE | 24 |
| CONSUMED_PARTIAL | 61 |
| UNREAD | 13 |
| NOT_RELEVANT | 2 |
| SOURCE_CONFLICT | 1 |

Each row carries source file, page, title, DXF handle / insert, row ids, parser, consumer, fields read, misread and unread, reason, provenance, affected population and defect id.

**Headlines:**
- **Continuous beams CB1–CB13 (D1).** The schedule is a DXF block (`C-BEAM2` / `C-BEAM3`) whose ATTRIBs carry BOTn-B/D, MID-B/D, MIDn-B/D and STRn-B/D. A3 hand-transcribed only B, H and spans from the PDF ("text drawn as vector glyphs"). Every bar attribute is unread. `T/M-n` are design loads (t/m), correctly NOT_RELEVANT.
- **Footings FT** (F, F2–F7, F9–F11, F15). The `BOXED` attribute ("3+4" … "3+8") is never parsed and never flagged (SD-08).
- **Footings FTB** (F8, F12, F13, F14, FF). These are two-layer rows (`SH-T-*`, `LO-T-*`, `SH-B-*`, `LO-B-*`, all per metre). D2 and D3 below.
- **Simple-beam REMARKS.** The side bars printed for B7–B29 (2Ø12/30cm; B16, B26, B27 2Ø16/20cm; B19 2Ø14/20cm) are captured as a string by `_simple_beam_library` and never consumed (SD-11).
- **SB2 duplicate.** Two schedule rows (80×50 and 100×50; the drawn width is 987 mm). The parser keeps one silently (SD-12, the one SOURCE_CONFLICT).
- **Unread loose texts and details:**
  - planted columns P.C 20×70 (10Ø16) and 2 × P.C 20×50 (8Ø16) (SD-13);
  - `(T&B)` ×4 on 2F slab bars (SD-14);
  - section B-B 11Ø18 / 3Ø18 (SD-15);
  - p.8 notes (raster) and p.15 temperature reinforcement (SD-16);
  - p.14 lift detail (D3);
  - p.16 stair steel layout (SD-17).
- **Columns (CGT).** CONSUMED_COMPLETE; matches p.9.

## F. STRUCTURAL_POPULATION_COVERAGE_REGISTER

Every concrete occurrence has one rebar state:

| Population | State counts |
|---|---|
| FOOTING (27) | COMPLETE 4 (FN), PARTIAL 20 (16 BOXED-unread + 4 D2), BLOCKED 3 (F, F10, FF) |
| COLUMN (105) | COMPLETE 48, NOT_REQUIRED 31, **REBAR_WITHOUT_CONCRETE 26** |
| BEAM (78) | COMPLETE 51, PARTIAL 26, BLOCKED 1 |
| CONTINUOUS_BEAM (11) | BLOCKED 11 (6 MEASURED, silent) |
| STRAP_BEAM (3) | BLOCKED 3 (silent) |
| Slab / ground / lintels / dome / pool / boundary / ext-GB / starters / stairs | population rows from V3b; STAIRS BLOCKED |

**26 occurrences disappear with no row of any kind:** FF ×1, BOXED ×16, measured CB ×6, straps ×3.

## G. D1–D6 reproduced

Each defect has a characterisation test that calls the real function on a synthetic input:

| ID | Reproduction | Alsenan magnitude |
|---|---|---|
| D1 | `beam_rebar` with a MEASURED `CB1` occurrence emits nothing (`structure.py:325` `d is None` → `continue`) | 13 CB types; 6 measured + 5 other occurrences; zero CB rows in any rebar register. CB1 example: 35×75, spans 7.5 / 5.7, BOT 4Ø18 / 5Ø18, MID 8Ø18, STR 5Ø8/m / 9Ø10/m, top 3Ø14, side 2Ø12/30cm |
| D2 | `footing_rebar` with `count=6, per_m=True` emits 6 bars per direction; the BOT layer becomes "boxed bars BLOCKED" | F8, F12, F13, F14: emitted 245.6 kg vs schedule straight-mesh magnitude ≈ 2,095 kg (both layers, `per_m × span`; **DIAGNOSTIC_MAGNITUDE_NOT_A_QUANTITY**) |
| D3 | FF (lift footing, قاعدة مصعد) has a merged two-layer cell → `bars {}` → `footing_rebar` returns `[]` | 1 occurrence (4.60 × 4.50 × 0.55); TOP 6Ø14/m, BOT 9Ø14/m both ways |
| D4 | SB types parsed as `element="STRAP"`; `beam_rebar` filters `element == "BEAM"` | SB1 4.55 m, SB2 2.29 m, SB3 3.26 m; e.g. SB1 bottom 7Ø16, top 13Ø18, links 8Ø8 |
| D5 | `column_rebar` ignores occurrence state | 26 occurrences / **1,739.7 kg**: NOT_DRAWN 1,007.1, BLOCKED_UPPER 312.4, SEVERAL_OUTLINES 231.8, TAG_NOT_BOUND 188.3. V3b's concrete residue explicitly excludes NOT_DRAWN (`v3b_struct.py:329`), so concrete and rebar disagree by construction |
| D6 | `ground()` binds a zone label to `min(hit, key=area)` (`structure.py:108`) | ZONE-1 outer 103.44 m² (slab 70.41) inside FP-1 227.72 m². ZONE-2 recovered in V3b (outer 60.557, slab 44.983). Whether the rest of FP-1 is slab-on-grade is unresolved (Q-S4) |

## H. SILENT_DROP_REGISTER (23 rows)

All 136 `continue` sites in the active Alsenan modules were read. The 23 rows are the ones that remove a quantity-bearing object with no BLOCKED / NOT_IN_SCOPE row.

Each row has: code location, anchor, condition, input population, current behaviour, correct future behaviour, severity and the test that pins it. `test_sd_code_anchors_hold` checks every cited `file:line` still contains its anchor, so the register cannot rot silently.

**HIGH severity:**

| ID | Location | What is dropped |
|---|---|---|
| SD-02 / SD-20 | | Column state (D5) |
| SD-03 | `structure.py:325` | CB / non-measured beams (D1) |
| SD-07 | `structure.py:431` | Ambiguous wall bands, 46.63 m |
| SD-10 | `registers.py:293` | Wet labels in DRY zones |
| SD-22 | `structure.py:108` | Min-area ground binding (D6) |
| SD-23 | | Unplaced wet labels |

## I. WALL_LENGTH_CONSERVATION_REGISTER

Totals across GF / 1F / 2F:

| Measure | m |
|---|---|
| Established band centreline | **209.35** (167.25 excluding the 920 mm band) |
| Ambiguous band centreline | **46.63** (GF 32.06, 1F 14.57) |

**Both of ChatGPT's figures are confirmed.**

- Blockwork rows equal the established non-920 bands exactly (Δ ≤ 0.001 m per floor). The 920 mm band is an explicit EXCLUDED row.
- The 46.63 m of ambiguous bands ends in **no row** (SD-07).
- A further **187.82 m** of admitted TOPOLOGY_BOUNDARY face length (GF 112.75, 1F 50.76, 2F 24.31) belongs to no band and is unclassified as wall, not-wall or blocked.
- Conservation rule: admitted boundary length = established + ambiguous + unpaired, and every metre must end in a blockwork row, a BLOCKED row or a NOT_WALL classification.

## J. Wet-room map

V3b gives wet-floor WP 58.237 m² and wall tile 369.123 m² (commercial; technical 26.36). The freelancer gives 72.01 / 433.83. These are **findings only**.

Four wet rooms lose their label:

| Floor | Label | Where | Why |
|---|---|---|---|
| GF | Wash / مغسلة | GF-Z04 (DRY) | DRY-wins |
| GF | Wash | GF-Z06 (DRY) | DRY-wins |
| 1F | W.C / مرحاض | NO_SITE (0.52 m from 1F-R07 LAUNDRY) | physical closure missing |
| 1F | BATH / حمام | NO_SITE (0.92 m from 1F-R01) | physical closure missing |

- The GF pool label (حمام سباحة) is NO_SITE (external), correctly not a wet room.
- GF-R05 BATH is UNLABELLED in TS01 but WET in Alsenan.
- The tile/WP gap is explained structurally (lost rooms plus the DRY-wins rule) before any area comparison is made.

## K. OPENING_COMPLETENESS_REGISTER (60 openings)

| Kind | COMPLETE | HEIGHT_PROVISIONAL | HEIGHT_BLOCKED |
|---|---|---|---|
| Door | 10 | 13 | 3 |
| Double-leaf door | 0 | 0 | 1 |
| Window | 2 | 24 | 7 |

- Only 12/60 have a source or raster height.
- **59/60 carry V3a status `COMPUTED` with a BLOCKED height** (status defect, gate G18).
- 21 windows are flagged GLAZED_DOOR_CANDIDATE (sill < 0.15 m or height ≥ 2.0 m), e.g. GF-W15 / W16 1.955 × 2.063, 1F-W12 2.45 × 2.097, GF-W09 6.332 × 3.65. They need owner confirmation before door / window trade split.

## L. PDF X/Y and affine calibration proposal

**Today** (`alsenan_v3b_raster.calibrate` → `engine/source/raster_evidence.calibrate`):
- One scalar `px_per_cm`, fitted only on the **vertical** printed level chain (`y = y0 − s·level`).
- It is then applied to both axes.
- There is no x-axis observation, no rotation or skew term, and no per-axis residual. Measurements do not record which calibration produced them.

**Proposal** (plan-measure pattern: `UniformPageCalibration | XyPageCalibration` with `xReference` / `yReference`, and `calibrationId` on every measurement):
1. **Per-axis.** Calibrate x from a horizontal printed dimension chain or a grid-axis spacing, and y from the level chain. Store `sx`, `sy`, observations, residuals and `worst_rel_dev` per axis. If |sx − sy| / s > tol, raise CALIBRATION_ANISOTROPIC, and measurements on that sheet become PROVISIONAL.
2. **Affine** (vector-backed sheets). Fit `[x', y'] = A·[x, y] + t` by least squares to ≥ 4 anchor pairs: DXF column-grid intersections and the same intersections detected on the raster. Report RMS and maximum residual in mm. Release only if max residual ≤ 0.5 × the smallest measured feature tolerance.
3. Every raster-derived quantity carries `calibration_id`, `axis` and `residual_mm`. Gate: a measurement whose calibration is missing or anisotropic cannot be RASTER_DERIVED.
4. Synthetic tests: a known anisotropic scale (sx ≠ sy), a 0.5° rotation, a shear, and a page with fewer than 4 anchors (must be NOT_SCALABLE).

## M. Donor re-audit (`DONOR_DELTA_REGISTER`)

| Donor | Licence | Delta / ideas | Use |
|---|---|---|---|
| **M1 OpenTakeoff** | Apache-2.0 | Lock e6d2251 → upstream c7e02eb (+42 commits). 63a86e5 measured that OCR confidence does not separate misreads (below 0.9: 21 correct + 10 misreads). 24d1d95 `repairKey` keeps `read_as`. 256ef63 adversarial OCR fixtures. c3ec135 idempotent re-import. sheetgraph `find_schedule` / `resolve_tag`. RFI tombstones. `scalewarn` as a gate | Patterns only |
| **M2 U-C4N** | per DONORS.lock | Shadow experiment design below | Shadow only |
| **M3 jeremylongshore/cad-ai-agent** | Apache-2.0 | Seeded-RNG fuzz property tests (no runtime dependency; used in this round's tests). Deterministic HealthReport with `checks_run`. Pure, order-stable cross-drawing consistency checker | Patterns only |
| **M4 userfypp/plan-measure** | MIT | Per-axis XY calibration; `calibrationId` on measurements; versioned persistence codec | Patterns only (L) |
| **M5 ContractorKeith/conmcp** | MIT | Unknown sheet → "unclassified", not a guess. One UOM vocabulary. `audit_event`. Source sheet on every item | Patterns only |
| **M6 braedonsaunders/bidwright** | **AGPL-3.0-only** | Evidence gate: an item without a structured source reference is rejected; prose ("best judgment") must keep failing, and the gate has its own contract test. Drawing-evidence atlas lists excluded documents explicitly | **Ideas only; no code, no structure copied** |

**M2 — U-C4N shadow experiment design.**
- Run U-C4N as a read-only shadow reader of ST7757.dxf and P7757.dxf.
- Compare against K2 (ezdxf):
  - per-entity-type counts;
  - INSERT / ATTRIB values for the six schedule blocks;
  - TEXT strings and heights;
  - layer membership.
- Output: a SHADOW_DIFF register. Any disagreement is a finding about one reader, never an input.
- No production import. Run under the existing donor sandbox, with a pinned commit.

**M7 — donor-derived implementations done wrongly:**
1. Schedule reading took the *idea* of a schedule reader (OpenTakeoff) but read the PDF and a hand transcription, when the DXF carries the same tables as ATTRIBs.
2. No `find_schedule`-style coverage check exists, which is why D1, D2, D3, D4, SD-08 and SD-11 were never detected.
3. Raster calibration took a single scale (M4 shows the per-axis model).
4. The release model asserts confidence `H` rather than deriving it (M6's gate shows that the source reference must be structural, not declared).

## N. Property / mutation tests and control gates (23)

**Implemented now** (seeded `random.Random`, no new dependency):
- `_room_class` is order-invariant;
- `release.in_total ⇔ class ∈ TECH_IN_TOTAL ∧ qty ≠ None`;
- metamorphic room-status mutation leaves floor statuses unchanged (pins C).

**Control gates G01–G23**, each `xfail(strict=True)`. Each fails today on its own assertion (checked with `--runxfail`). An XPASS turns red, so the gate must be promoted when the fix lands.

| Gate | Defect | Assertion after the fix |
|---|---|---|
| G01 | C-1 | No COMPUTED_REVIEW room floor in total |
| G02 | B-1 | TS01-unresolved zone ⇒ BLOCKED_SEMANTIC_ZONE |
| G03 | B-2 | Multi-name zone with a wet label is not DRY |
| G04 | J-1 | No wet room lost |
| G05 | C-2 | Skirting status follows room |
| G06 | C-3 | Ceiling status follows room |
| G07 | D | PARTIAL is not procurement-eligible |
| G08 | E | Every structural source object consumed or not relevant |
| G09 | F | No silent occurrence |
| G10 | D1 | 13 CB definitions exist |
| G11 | D2 | Per-metre respected, both layers |
| G12 | D3 | FF emits a row |
| G13 | D4 | Straps emit rebar |
| G14 | D5 | No rebar without concrete |
| G15 | D6 | No min-area binding |
| G16 | I-1 | Ambiguous length ends in a row |
| G17 | I-2 | Unpaired boundary classified |
| G18 | K | No COMPUTED opening with a BLOCKED height |
| G19 | SD-12 | Duplicate schedule name recorded as conflict |
| G20 | SD-08 | BOXED parsed |
| G21 | SD-11 | Side-bar REMARKS consumed |
| G22 | O | No user CLI reaches the legacy adapter without a deprecation guard |
| G23 | SD-17 | Stair rebar bound to the p.16 typical layout |

## O. LEGACY_CAD_REACHABILITY_REGISTER

The register is built from a static AST import graph (module-level and lazy imports; bare lab names resolved). 83 files outside this audit reference `cad_adapter`.

| Entry point | State | Chain |
|---|---|---|
| RC1 Qortuba (`rc1_qortuba`) | **REACHABLE (module-level)** | rc1_qortuba → r8_20_qortuba → r8_19_registers → r8_18_registers → r8_18_qortuba → r8_18_blind → r8_14_qortuba → r8_8_topology → **r8_7_canonical** → engine/cad_adapter |
| Alsenan V3b | NOT_REACHABLE | — |
| `engine.ingest.harness` | REACHABLE | direct import |
| `tools/run_cad_pipeline.py` | REACHABLE, **no deprecation guard** (seal check only) | direct import |
| `engine.freeze_manifest` | REACHABLE_LAZY | function-level import |
| `engine.document_reader`, `engine.pm_sync`, `tools/run_pipeline.py` | NOT_REACHABLE | — |

RC1 measures through the K1/K2 route but imports CA dataclasses and `run_legacy`. RC1 is RC1_REFERENCE and is **not patched**; the gate (G22) targets user CLIs, not RC1.

## P. ACCURACY_SCORECARD_DRAFT

This scorecard measures **control-plane completeness**, not closeness to the freelancer workbook. No row reads a benchmark value, and a test enforces that.

| ID | Metric | Now | Accept |
|---|---|---|---|
| M01 | Floor m² released while the room is COMPUTED_REVIEW | 325.251 | 0 |
| M02 | TS01-unresolved zones released | 3 | 0 |
| M03 | Wet rooms whose label is lost | 4 | 0 |
| M04 | Structural source objects fully consumed | 25.7 % | 100 % |
| M05 | Required concrete occurrences with complete rebar | 53.4 % | 100 % |
| M06 | Occurrences dropped silently | 26 | 0 |
| M07 | Rebar kg on occurrences with no concrete | 1,739.7 | 0 |
| M08 | Ambiguous wall-band m with no row | 46.63 | 0 |
| M09 | Unpaired topology-boundary m with no row | 187.82 | 0 |
| M10 | Openings with a source or raster height | 20 % | 100 % (or BLOCKED rows) |
| M11 | V3a openings COMPUTED with a BLOCKED height | 59 | 0 |
| M12 | Silent-drop code paths | 23 | 0 |

## Q. BENCHMARK_CONFIDENCE_REGISTER

No freelancer value is VERIFIED_SOURCE_TRUTH. Only a value re-derived from the drawings can be.

**STRONG_HUMAN_REFERENCE** (formula-backed):

| Benchmark | Value | Basis |
|---|---|---|
| Floor | 409.58 | `=H65+D31` |
| Skirting | 282.85 | |
| Wall tile | 433.83 | `=SUM(G42:G64)` |
| Blockwork | 1,260.69 | |
| Paint | 1,191.13 | gross − deduction |
| Plaster | 1,151.14 | gross − deduction |
| Blinding | 47.06 | |
| Reinforced concrete | 352.44 | contains a +0.128 m³ formula skip |

**WEAK_HUMAN_REFERENCE:**
- **Wet-floor WP 72.01**: a typed cover constant equal to the wet-floor tile subtotal and reused for wet ceilings and decor paint. WP equals tile area; there is no separate measurement.
- **Roof WP 285**: typed constant.
- **Internal railing 18.95**: typed constant.
- **Rebar 44.19 t**: the sum of seven typed constants (5.8 + 9.75 + 7.95 + 9.89 + 5.4 + 3.9 + 1.5) with no bar schedule behind it.

**HUMAN_FORMULA_ERROR:**
- FIN رخام+حوش!H44 double-counts H13 (151.8).
- RC كمرات!I82 skips I59 (0.128).

## R. Outputs

`ALSENAN_ACCURACY_CONTROL_PLANE_REVIEW.md` (this file) plus 10 JSON registers and `INDEX.json` in `registers/`:

- STRUCTURAL_SOURCE_COVERAGE
- STRUCTURAL_POPULATION_COVERAGE
- SILENT_DROP
- ROOM_SEMANTIC_TRADE_RELEASE
- WALL_LENGTH_CONSERVATION
- OPENING_COMPLETENESS
- LEGACY_CAD_REACHABILITY
- DONOR_DELTA
- BENCHMARK_CONFIDENCE
- ACCURACY_SCORECARD_DRAFT

Evidence is in `evidence/`.

## S. Test run

See `TEST_RUN.md`. It is written from the final full-suite run of this commit.

**Why the existing tests missed these defects:**
1. **Registers were tested against themselves.** The V3 / V3b register tests assert internal consistency and freeze-twice determinism. A constant status, or a dropped population, is perfectly self-consistent.
2. **There was no source-coverage oracle.** No test enumerated the schedule blocks of the DXF and asked "who consumed this?". D1, D2, D3, D4, SD-08 and SD-11 are invisible without one.
3. **The synthetic tests covered engines, not adapters.** TS01 semantic zones are well tested in `engine/source`, but nothing tested that the Alsenan adapter *uses* them. That is the integration gap.
4. **Silent `continue` has no observable output to assert on.** Only a conservation test (input count = output rows + blocked rows) can catch it, and none existed.
5. **Release tests checked rule shape, not rule correctness.** `PARTIAL ∈ TECH_IN_TOTAL` is the specified rule, so tests passed. Nobody asked whether a lower bound should be procurement-eligible.
6. **Benchmark comparisons were (rightly) findings-only**, so large differences (wall tile −93.9 % technical) were recorded but never routed to a root-cause test.

## U. Stop

This round stops at diagnosis. The smallest safe implementation order and the owner questions are in section T below.

---

## T. Final report

### 1. Confirmed defects

| Area | Defect |
|---|---|
| B-1 | TS01 semantic state not consumed by the Alsenan path |
| B-2 | DRY-wins room class |
| C-1 / C-2 / C-3 | Constant COMPUTED status on floor, skirting, thresholds and ceiling. 325.251 m² of COMPUTED_REVIEW floor is released |
| D | PARTIAL and URBAN_STANDARD are procurement-eligible at asserted confidence H |
| D1 | CB reinforcement unread |
| D2 | Per-metre counts read as absolute; BOT layer blocked as "boxed" |
| D3 | FF emits nothing |
| D4 | Straps filtered |
| D5 | 1,739.7 kg on 26 occurrences with no concrete |
| D6 | Min-area ground binding |
| SD-08 | BOXED unread |
| SD-11 | Side-bar REMARKS unused |
| SD-12 | SB2 duplicate kept silently |
| SD-13 – SD-17 | P.C, T&B, section B-B, notes / temperature steel, stair layout unread |
| I | 46.63 m ambiguous plus 187.82 m unpaired boundary end in no row |
| J | 4 wet rooms lost |
| K | 59 openings COMPUTED with a BLOCKED height |
| L | Single-axis raster scale |
| O | User CLI reaches `cad_adapter` with no deprecation guard |

### 2. ChatGPT wrong or overstated

**Confirmed exactly:** 325.25 m², 209.35 m, 46.63 m, and D1–D6 as stated.

**Precision notes.** These are where a reading of those figures would overstate:
- **209.35 m includes the 920 mm band** (3 × 14.035 m). That band is an explicit EXCLUDED blockwork row, not a silent drop. The established length that becomes blockwork is 167.25 m, and it is fully conserved.
- **D2 is worse than "per_m ignored".** The BOT layer is also misrouted into `boxed` and emitted as BLOCKED.
- **Side bars are not "unknown".** The V3a code says the mapping "is not printed", but REMARKS prints them for B7–B29.
- **T/M-n in the CB schedule are design loads.** Any reading of them as bars would be wrong.
- **72.01 m² (wet-floor WP) and 44.19 t (rebar) cannot serve as truth.** Both are typed constants (WEAK_HUMAN_REFERENCE).

### 3. Unresolved

- Whether the remainder of FP-1 is slab-on-grade (D6).
- Whether p.15 twisted column / beam in casement apply anywhere.
- BOXED meaning ("3+4": starter bars? box ties?).
- Whether the 1F W.C / BATH are real rooms whose closure is missing, or stale labels.
- Glazed-door candidates (21).
- SB2: which row governs (the drawn width favours 100×50).
- `(T&B)` layer count on the 2F slab.

### 4. Code locations (research/external_engine_lab unless stated)

| Location | Defect |
|---|---|
| `alsenan_v3_layers.py:126–131` | `_room_class` (DRY wins) |
| `alsenan_v3_layers.py:200` | `REVIEW if phys else REVIEW` |
| `alsenan_v3_registers.py:255, 259, 264, 278` | Constant statuses |
| `alsenan_v3_registers.py:293` | Wet-only tile / WP |
| `alsenan_v3_structure.py:108` | D6 |
| `alsenan_v3_structure.py:277–289` | D2, D3, SD-01 |
| `alsenan_v3_structure.py:300` | D5 |
| `alsenan_v3_structure.py:325–330` | D1, SD-04 |
| `alsenan_v3_structure.py:344` | Side bars |
| `alsenan_v3_structure.py:379, 401, 431, 515` | Other silent `continue` sites |
| `alsenan_phase_a3.py:46–73` | CB transcription |
| `alsenan_phase_a3.py:248` | REMARKS captured, unused |
| `alsenan_phase_a3.py:420` | STRAP element |
| `alsenan_phase_a3.py:425` | `boxed` = sub-rows |
| `alsenan_phase_a.py` `footing_schedule` | BOXED / REMARKS unread |
| `alsenan_v3b_rebar.py:166, 169` | Residue skips |
| `alsenan_v3b_struct.py:329` | Concrete excludes NOT_DRAWN |
| `alsenan_v3b_raster.py:107` | Single-axis calibration |
| `engine/source/release_model.py:29, 37, 57` | Release model |
| `tools/run_cad_pipeline.py` | No deprecation guard |

### 5. Alsenan quantities affected

- **Flooring:** 325.251 m² (of 447.225).
- **Skirting and ceilings:** for the same rooms.
- **Wall tile / WP:** 4 wet rooms missing.
- **Blockwork:** 46.63 m centreline of ambiguous walls missing, plus 187.82 m of unclassified boundary.
- **Rebar:**
  - CB (13 types, 11 occurrences) and straps (3): zero;
  - F8, F12, F13, F14: 245.6 kg emitted against a ≈ 2,095 kg straight-mesh magnitude (diagnostic);
  - FF: zero;
  - BOXED bars: zero (16 footings);
  - columns: +1,739.7 kg without concrete;
  - side bars: provisional range instead of the printed values;
  - stairs: zero.
- **Openings:** 48 of 60 heights are provisional or blocked.

None of these are corrected here.

### 6. Existing good Urban code that is bypassed

| Code | Bypassed by |
|---|---|
| TS01 `res["semantic"]` and `SZ.trade_regions()` (BLOCKED_SEMANTIC_ZONE) | The Alsenan adapter |
| `engine/source/waterproofing_policy` | Never reached for DRY-classed zones |
| K2 ezdxf ATTRIB reading (used in R8) | A3 schedule parsing (reads PDF instead) |
| The publication contract "blocked rows never enter a total" (R5.1) | Defeated upstream by the constant COMPUTED status |
| `release_model` REVIEW class | Never produced for finishes, because the status is constant |

### 7. Donor ideas implemented wrongly

- **Schedule reader:** PDF / hand transcription instead of DXF ATTRIBs, and no coverage check.
- **Raster calibration:** single scalar instead of per-axis.
- **Evidence gate:** confidence declared ("AS TECHNICAL", H) rather than derived from a structured source reference.

### 8. New donor ideas

| Donor | Idea |
|---|---|
| OpenTakeoff | Never gate on OCR confidence; keep `read_as` beside the repair; adversarial schedule fixtures; idempotent re-import; `find_schedule` / `resolve_tag` with an unresolved state; RFI tombstones; scale-warning as a gate |
| cad-ai-agent | Seeded fuzz property tests; `checks_run` in every report; cross-drawing consistency (architectural ↔ structural tags, lift, stair) |
| plan-measure | XY calibration with `calibrationId` |
| conmcp | "Unclassified" fallback; single UOM vocabulary; per-item sheet reference |
| bidwright (ideas only) | Structured-source evidence gate with its own contract test; explicit excluded-document list |

### 9. Test gaps

There was:
- no source-coverage oracle;
- no population conservation test (input occurrences = rows + blocked rows);
- no adapter-integration test for TS01 semantics;
- no metamorphic status test;
- no release-correctness test (only rule shape);
- no code-anchor test for known drop sites.

All are now present as characterisation tests or G01–G23 gates.

### 10. Control gates

G01–G23 (section N), all strict-xfail today. In addition:
- registers rebuild byte-identically from committed evidence;
- the INDEX hashes match;
- the silent-drop code anchors still hold;
- the scorecard cannot read benchmarks.

### 11. Smallest safe implementation order

Each step is its own round: tests first, then the frozen-register rebuild, then a diff register against this round's registers.

1. **Release correctness (C, D).** Wire room status into floor, skirting, threshold and ceiling. Add `release_state` per D, with PARTIAL not procurement-eligible. Smallest diff, largest exposure (325 m²). Gates G01, G05, G06, G07.
2. **Semantic integration (B, J).** Consume TS01 `semantic`. An unresolved zone becomes BLOCKED_SEMANTIC_ZONE for wet trades. A wet label inside a DRY zone becomes a TILE_WP_BLOCKED row. Unplaced wet labels become WET_LABEL_UNPLACED rows plus owner questions. Gates G02, G03, G04.
3. **Silent drops → BLOCKED rows**, with no quantity change. Every SD row writes a BLOCKED / NOT_IN_SCOPE record, and a population-conservation test is added. Gates G09, G16, G17, G18.
4. **Structural schedule from DXF ATTRIBs.** Parse FT / FTB / SBT / C-BEAM / CGT directly; record SB2 as SOURCE_CONFLICT; parse BOXED and REMARKS. Definitions only, with no new quantities yet. Gates G08, G10, G19, G20, G21.
5. **Rebar consumers.** Per-metre and two-layer footings (D2), FF (D3), straps (D4), CB (D1), side bars, and rebar state following occurrence state (D5). Gates G11–G14.
6. **Ground binding (D6) and stair layout (SD-17).** Engineer answers are needed first. Gates G15, G23.
7. **Calibration (L)** per-axis / affine, then **legacy CLI deprecation guard (O)**, gate G22.

### 12. Owner / QS questions

| ID | Question |
|---|---|
| Q-A1 | GF-Z04 contains *Wash* and *GARDEN*: where are the wash area's boundaries? Is the garden part of the internal porcelain floor? |
| Q-A2 | GF-Z06 *Wash*: same question. |
| Q-A3 | 1F W.C and BATH labels lie outside every closed room (0.52 m from LAUNDRY, 0.92 m from 1F-R01). Are they rooms whose walls are missing from the plan, or stale labels? |
| Q-A4 | Confirm the 21 glazed-door candidates (e.g. GF-W15 / W16, 1F-W12, GF-W09) as doors or windows. |
| Q-A5 | Should a lower-bound (PARTIAL) quantity ever be procured before completion? |
| Q-S1 | Footing BOXED column "3+4" … "3+8": what bars are these (starter / box ties), and what is their shape? |
| Q-S2 | Two SB2 rows (80×50 and 100×50): which governs? The drawn width is 987 mm. |
| Q-S3 | `(T&B)` on the 2F slab: are both layers the printed bar? |
| Q-S4 | Is the part of footprint FP-1 outside ground-slab ZONE-1 also slab-on-grade (T = 10 cm, 5Ø10/m E.W.)? |
| Q-S5 | Do the p.15 typical details (twisted column, beam in casement, planted column) apply? Where are P.C 20×70 and 2 × P.C 20×50? |
| Q-S6 | May the p.16 typical stair steel layout be used for the stair bar schedule? |
| Q-S7 | p.8 notes are a raster image. Can the engineer supply them as text (notes 1–24)? |
