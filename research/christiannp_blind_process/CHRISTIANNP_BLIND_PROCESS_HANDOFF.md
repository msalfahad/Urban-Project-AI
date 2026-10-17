# christiannp-autocad blind run: forensic process handoff (v2, evidence correction)

Nothing in this package changes the sealed christiannp result, Urban production code or any frozen Urban register. No BOQ was rerun.

## 0. Evidence classes

| Class | Meaning |
|---|---|
| **REPORT_EXPLICIT** | Stated in the sealed report `CHRISTIANNP_ALSENAN_BLIND_FULL_BOQ.md`. |
| **URBAN_FROZEN** | Urban's frozen registers. Every value carries ENGINE_COMMIT, REGISTER_VERSION, DRAWING_SHA and CALCULATION_ROUND. |
| **ARITHMETIC_INFERENCE** | Arithmetic on the two classes above. Never a donor record. |
| **NOT_HELD** | The chronological MCP transcript, raw LISP history, scripts, raw entity dumps, raw wall pairs, raw raster cells and raw beam allocations. |

**Report file status.** The report file has not yet reached this environment. It is not in the upload folder, the repository or on disk.

- Every REPORT_EXPLICIT item is imported from your quotation of the report, with `report_file_check: PENDING`.
- Place the file unchanged at `process_log/CHRISTIANNP_ALSENAN_BLIND_FULL_BOQ.md` and run `scripts/verify_report_quotes.py`. It checks 43 quoted claims against the text and writes `process_log/REPORT_QUOTE_CHECKS.json`.
- Values you said are in the report but did not quote are listed as **AWAITING_REPORT_FILE** in `process_log/EVIDENCE_INVENTORY.json`, not as NOT_HELD:
  - raster class areas;
  - the rest of the unresolved-rebar list;
  - the footing occurrence table;
  - the stair breakdown;
  - the plaster composition;
  - per-floor column lists.

**v1 changed in this revision:**

- RELAYED becomes REPORT_EXPLICIT.
- INFERRED becomes ARITHMETIC_INFERENCE.
- Two v1 inferences are **withdrawn**: the "uniform 4.49 m wall height, no deductions" plaster reading (§9) and the "1F/2F columns clear of beams" reading (§6).

## 1. Process record

| Field (per step) | Status |
|---|---|
| Chronological tool calls, tool names, arguments, active document | NOT_HELD |
| AutoLISP expressions / scripts, PowerShell / local scripts | NOT_HELD |
| Raw entity dumps, raw pairs, raw raster cells, raw beam allocations | NOT_HELD |
| Stage outputs and the rules and assumptions that shaped them | REPORT_EXPLICIT (below) |

| Stage | REPORT_EXPLICIT content |
|---|---|
| Ground-beam plan | 85 raw lines → 42 paired strips, 200.036 m, 300 mm widths; volume = drawn width × 0.60 (A5) × length = 36.006 m³ |
| Ground slab | 324.038 m² × 0.10 = 32.404 m³; area A7 |
| Slabs | 50 mm raster, layer-1 lines + arcs, exterior flood fill; classes SLAB_LABELLED / BEAM_INTERIOR / OPENING / UNRESOLVED_ENCLOSED / EDGE_LINE_CELLS; net GF 290.555 / 1F 179.325 / 2F 55.275 m²; A1 |
| Columns | FOU 6.150 / GF 26.235 / 1F 8.888 / 2F 3.377 m³ under A2, A3, A4, A8, A12 |
| Beams | GF 25.206 / 1F 18.562 / 2F 2.823 m³ under R1–R5 |
| Walls / finishes | 150 mm 79.971 m, 200 mm 183.497 m; faces 2364.7 m² under A10, A13; A11, A14, A15 |
| Rebar | 22.916 t net drawing rebar with an explicit unresolved list (§8) |

## 2. Ground beams

**REPORT_EXPLICIT, kept apart:**

- GEOMETRY: 85 raw lines; 42 paired strips; 300 mm widths; 200.036 m.
- DEPTH: 0.60 m, **assumption A5**.
- VOLUME: 36.006 m³ = width × 0.60 × length. This is an **assumption-dependent** volume, not a source-measured one.

**ARITHMETIC_INFERENCE:**

- 200.036 × 0.30 × 0.60 = 36.0065, which matches.
- 85 lines for 42 pairs leaves one line unpaired, or one face shared or split. Which is NOT_HELD.

**URBAN_FROZEN** (V3 `GROUND_STRUCTURE_REGISTER`, commit 1381aa6; coverage round 680264d; ST7757.dxf sha 9f9d1179…):

- 43 paired bands (layer-1 double lines, 300 mm);
- 59 spans after splitting at the 36 columns on the sheet;
- 198.796 m.

**Result: Urban and christiannp independently reconstruct the same physical ground-beam network** (+1.240 m, +0.62 %). At the band level the segmentation nearly coincides: 42 strips against 43 bands. Urban's 59 is the same network split at supports.

Node connectivity cannot yet be compared: the donor strip end points are NOT_HELD, and Urban's frozen register keeps lengths, not band coordinates. Future generic test: `test_ground_beam_network_length_connectivity_segmentation`, comparing total network length, node types and components, and segmentation (bands vs spans). Never counts alone.

Volume consequence of A5 against Urban's printed sections:

| Interior depth | Effect |
|---|---|
| 0.30 m (16 spans) | +2.250 m³ |
| 0.40 m (11 spans) | +2.434 m³ |
| 0.60 m (4 spans) | 0 |

The exterior at 0.60 m is −13.236 m³ against Urban's 1.0 m best (bracket 0.90–1.30). A5 is wrong where Urban has a printed section and unsourced where it has none.

## 3. Ground slab

- **THICKNESS_AUTHORITY:** the T=10 cm text. It is a SOURCE; its scope across panels is unresolved.
- **AREA_AUTHORITY:** A7, the GF gross outline. PLAUSIBLE_BUT_UNVERIFIED as scope; rejected as verified.

The outline includes ground-beam and column footprints. Urban's cells between ground beams give best 21.701 m³; the remaining ~10.7 m³ is A7 scope.

## 4. CHRISTIANNP_RASTER_METHOD_SPEC

See `CHRISTIANNP_RASTER_METHOD_SPEC.json`.

| | Content |
|---|---|
| REPORT_EXPLICIT | 50 mm raster; layer-1 lines + arcs; exterior flood fill; output classes SLAB_LABELLED, BEAM_INTERIOR, OPENING, UNRESOLVED_ENCLOSED, EDGE_LINE_CELLS; class areas (in the report, AWAITING import) |
| NOT_HELD | grid origin, bounding region, rasterisation implementation, stroke width, flood-fill seed and code, class rules, edge-cell allocation, cell list, tolerances, raw script |

ARITHMETIC_INFERENCE per floor:

- implied thicknesses 0.200 / 0.160 / 0.180, so A1 adds +11.622 m³;
- the best-fitting opening sets keep the 10.725 m² stair well on GF and 1F (hypothesis H-SLAB-1). This is NON_UNIQUE until the OPENING / UNRESOLVED_ENCLOSED / EDGE_LINE_CELLS areas are imported.

**Recommendation:** rebuild an **independent Urban raster oracle** (design and convergence tests in the JSON). Do not copy unseen donor code. It is oracle-only and never a production quantity.

## 5. Beam rules R1–R5 (REPORT_EXPLICIT)

Full assessment, failure modes and tests are in `CHRISTIANNP_BEAM_RULES_R1_R5.json`. No rule is adopted automatically.

| Rule | Text | Useful idea | Unsafe part | Decision |
|---|---|---|---|---|
| R1 | Continuous beam allocated once per plan, capped at the schedule total span; width match preferred, then length | one occurrence per CB per plan; width-first ranking | the cap hides missing supports and span-count conflicts | **Production candidate, partly:** occurrence-once and width-first; the cap becomes a SPAN_LENGTH_CONFLICT check, never a truncation |
| R2 | CB may continue collinearly into an adjacent unlabelled strip | collinearity is real continuity evidence | may run into a lintel or edge beam | **Production candidate as CANDIDATE continuity only:** same width, stops at a support carrying a new tag |
| R3 | Same-mark labels < 2 m apart are merged | repeated tags exist | a fixed distance is scale-dependent and merges two short beams | **Oracle-only.** De-duplicate by shared strip geometry, not distance |
| R4 | Schedule vs drawn width > 60 mm → strip goes to the matching-width label | width is strong binding evidence | silent re-assignment, possibly to a distant label; fixed tolerance | **Production candidate as a gate:** record WIDTH_MISMATCH; re-assign only to an adjacent label; tolerance from drawing units |
| R5 | Remaining strip length shared equally among simple labels | none | arithmetic allocation without geometry; spreads errors invisibly; rebar inherits wrong lengths | **Reject for production.** Leftover length stays a CANDIDATE residue with identity. Your suspicion is confirmed. |

## 6. Columns: occurrence and floor membership

The vertical model is REPORT_EXPLICIT:

- A2: GF base ±0.00;
- A3: neck 1.00 m;
- A4: roof +13.90;
- A12: levels = FFL;
- A8: CN continued through FOU + GR.

URBAN_FROZEN (S1 level register 606efec):

- GF FFL +1.00; floor-to-floor 4.5 / 4.2 / 4.2 m printed;
- founding level not printed (≥ 1.5 m below plot level);
- slab top = FFL − build-up, build-up not printed.

ARITHMETIC_INFERENCE (implied section sum = report volume ÷ the report's own height):

| Floor | Report m³ | Report height (full / to soffit) | Implied ΣA m² | Urban ΣA m² | Reading |
|---|---|---|---|---|---|
| FOU | 6.150 | 1.00 (A3) | 6.15 | 6.24 | neck only; Urban's FOU runs to GF FFL |
| GF | 26.235 | 5.50 / 5.30 (from ±0.00, A2) | 4.77–4.95 | 4.50 | GF starts 1.00 m below the printed GF FFL; A8 adds sections |
| 1F | 8.888 | 4.20 / 4.04 | 2.12–2.20 | 2.44 | smaller population or sections, not height |
| 2F | 3.377 | 4.20 / 4.02 | 0.80–0.84 | 0.94 | as 1F |

FOU + GF totals agree: 32.385 against 32.153 m³.

Classification:

| | Items |
|---|---|
| URBAN_CORRECT | census, chains, no CN propagation |
| DONOR_ASSUMPTION | A2, A3, A12 |
| KNOWN_WRONG | A8 |
| SOURCE_CONFLICT | none |

The v1 "clear of beams" hypothesis is withdrawn.

## 7. Footings

URBAN_FROZEN (V3b 66dd3fb): 25 released occurrences, 64.346 m³. The F/F10 outline is blocked as a source conflict.

The report total is 65.669 m³ (+1.323). The ranked decompositions (ARITHMETIC_INFERENCE) are NON_UNIQUE until the report's footing occurrence table is imported (AWAITING_REPORT_FILE).

## 8. Rebar: KNOWN_INCOMPLETE_NET_DRAWING_REBAR

The 22.916 t comes with an explicit unresolved list (REPORT_EXPLICIT):

- continuous-beam T/M fields;
- BOXED footing bars;
- ground-beam reinforcement;
- missing slab direction;
- slab top bars without extent;
- CN reinforcement;
- CB MID/support bars;
- top hangers;
- stair reinforcement;
- … the rest is AWAITING_REPORT_FILE.

It is **never** compared with Urban's ACCURATE_BOQ_REBAR as if both were complete. A comparison is only valid per component that both sides hold as resolved (`CHRISTIANNP_UNRESOLVED_REBAR.json`).

## 9. Walls and plaster

- **Wall pairing:** donor pairs and parameters are NOT_HELD. The 166 diagnostic rows are Urban Method B with handles (version-stamped). The report's 200 mm length of 183.497 m sits 1.4 m from Urban's unclassified Method-B gross of 184.897 m, which breaks down as:
  - paired wall 111.615;
  - opening spans 34.570;
  - column overlap 28.819;
  - duplicate faces 9.893.
- **Plaster:** REPORT_EXPLICIT rules are A10 (wall height = floor-to-floor − slab thickness) and A13 (door 2.10).
  - ARITHMETIC_INFERENCE: two faces on all 263.468 m of pairs at the tallest A10 height (4.30 m, GF) give at most 2265.8 m², which is less than 2364.7 m².
  - So the plaster figure contains faces beyond the wall pairs: columns, exterior or parapet faces, or other surfaces.
  - The composition is AWAITING_REPORT_FILE. The v1 "uniform 4.49 m, no deductions" reading is **withdrawn**.

## 10. A1–A15

Detail is in `CHRISTIANNP_ASSUMPTION_FORENSICS.json`. All are REPORT_EXPLICIT; the file check is pending.

| Id | Assumption | Nature | After Urban review | Production |
|---|---|---|---|---|
| A1 | GF slab t = 0.20 | ASSUMPTION | KNOWN_WRONG (0.16 default unless noted) | REJECT |
| A2 | GF column base ±0.00 | ASSUMPTION | PLAUSIBLE_BUT_UNVERIFIED (storey convention; GF FFL printed +1.00) | REJECT |
| A3 | neck height 1.00 | ASSUMPTION | PLAUSIBLE_BUT_UNVERIFIED (founding not printed, ≥ 1.5 m) | REJECT |
| A4 | 2F roof top +13.90 | DERIVED | SOURCE_SUPPORTED (9.70 + 4.20 printed) | ACCEPT as derived level |
| A5 | ground-beam depth 0.60 | ASSUMPTION | KNOWN_WRONG (0.30 / 0.40 printed on 27 of 31 interior spans) | REJECT |
| A6 | blinding 0.10 + 0.10 projection | ASSUMPTION | SOURCE_SUPPORTED (Urban reads the local blinding detail) | ACCEPT where the detail applies |
| A7 | ground slab = GF gross outline | ASSUMPTION | PLAUSIBLE_BUT_UNVERIFIED as scope | REJECT as verified |
| A8 | CN continued through FOU + GR | ASSUMPTION | KNOWN_WRONG | REJECT |
| A9 | stair waist / landing | ASSUMPTION | PLAUSIBLE_BUT_UNVERIFIED | REJECT |
| A10 | wall height = floor-to-floor − slab | DERIVED | PLAUSIBLE_BUT_UNVERIFIED (ignores beams over walls; uses A1) | REJECT |
| A11 | ceiling = net slab above | DERIVED | PLAUSIBLE_BUT_UNVERIFIED | REJECT |
| A12 | structural levels = FFL | ASSUMPTION | PLAUSIBLE_BUT_UNVERIFIED (build-up not printed) | REJECT |
| A13 | door leaf 2.10 | ASSUMPTION | PLAUSIBLE_BUT_UNVERIFIED (most 2.117 cross-verified; 2.607 and 3.65 types exist) | REJECT as default |
| A14 | floor / ceiling = slab net area | ASSUMPTION | KNOWN_WRONG (includes wall footprints and non-room area) | REJECT |
| A15 | roof WP = SFRS only, no upturns | ASSUMPTION | KNOWN_WRONG (upturns and other exposed roofs omitted) | REJECT |

## 11. Donor agreement

See `CHRISTIANNP_DONOR_AGREEMENT.json`.

| Element | Pair | Class |
|---|---|---|
| Ground-beam length | christiannp vs Urban | INDEPENDENT_EXTRACTION_AGREEMENT |
| BUA | all three | INDEPENDENT_EXTRACTION_AGREEMENT |
| Columns FOU + GF total | christiannp vs Urban | INDEPENDENT_EXTRACTION_AGREEMENT |
| Slab net area GF / 2F | christiannp vs U-C4N | INDEPENDENT_EXTRACTION_AGREEMENT (1F UNDETERMINED) |
| Footings | all three | SHARED_SOURCE_AGREEMENT |
| Ground slab | christiannp vs U-C4N | SHARED_SOURCE (thickness) + SHARED_ASSUMPTION (area) |
| Ground-beam volume | christiannp vs U-C4N | SHARED_ASSUMPTION_AGREEMENT (U-C4N 36.005 ÷ 0.18 = 200.03 m) |
| Slab volume | christiannp vs U-C4N | SHARED_ASSUMPTION_AGREEMENT (both GF 0.20) |
| Columns per floor | christiannp vs U-C4N | SHARED_ASSUMPTION_AGREEMENT (three floors identical to the litre) |
| Stairs | christiannp vs U-C4N | UNDETERMINED |

Both donor runs were agent sessions working from the same owner brief, so donor-donor agreement defaults to CORRELATED_REASONING unless shown otherwise.

## 12. Versioning

Every Urban value now carries:

- ENGINE_COMMIT;
- REGISTER_VERSION (path@sha256);
- DRAWING_SHA (P7757.dxf ab54dd55…, ST7757.dxf 9f9d1179…);
- CALCULATION_ROUND.

The ~79 m 200 mm wall figure came from an earlier Urban snapshot. The current frozen value is 89.74 m (verified) and 134.076 m (best), from the coverage round at 680264d.
