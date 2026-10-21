# Blind architectural BOQ test: protocol URBAN_BLIND_V2

**Status:** sealed in Phase 2B-8, before any second-villa drawing has been run under it. No accuracy is claimed.

- The machine-readable form is `URBAN_BLIND_V2_PROTOCOL.json`; where this document and the JSON differ, the JSON governs.
- The scorer is `blind_score_v2.py` (stdlib only) and the reference format is `REFERENCE_TEMPLATE.json`.
- `SEAL.json` holds the sha256 of all four files. A change to any of them after a reference is committed voids the round.

**What V2 keeps from URBAN_BLIND_V1** (`research/urban_m9_p2a_acceptance/blind_test/BLIND_TEST_PROTOCOL.md`):
- roles and custody (section 2);
- the drawing set and its privacy (section 3);
- the procedure (section 6);
- the outcomes (section 7);
- the claim rule (section 8);
- the error classes (section 9).

V1's scorer is not changed.

**What V2 changes:**
1. It is the method under test: ARCH_TAKEOFF_V2.7.1 (primary) and ARCH_TAKEOFF_V2.7 (comparator), both frozen at the commit that seals this protocol.
2. It covers the categories requested in Phase 2B-8, and each metric has a support status.
3. An UNSUPPORTED metric is reported as UNSUPPORTED, with the reference total, and is never scored as zero.
4. The reference must be independent of the engine. The scorer refuses a reference that is not.
5. Conditional (review-space) and provisional quantities are flagged, never counted as answers.
6. The acceptance criteria are stated, but they are PROPOSED until the owner approves them.

## 1. Categories and support

The support status describes ARCH_TAKEOFF_V2.7.1 as sealed.
- **SUPPORTED:** the quantity comes from plan evidence. It is scored.
- **PARTIAL:** emitted only in the stated conditions. It is scored, and its gaps are counted.
- **UNSUPPORTED:** the engine does not establish the quantity. It is reported, never scored and never zero.

| Category | Metric | Level | Support | Engine source | Condition / why |
|---|---|---|---|---|---|
| Room floor areas by floor | FLOOR_AREA | room | SUPPORTED | room record `area_m2` | matched by label point |
| Wet rooms | WET_FLOOR_AREA | room | SUPPORTED | FIN.FLOOR.WET_TILE | a review space answers only conditionally (FLAGGED) |
| Wet rooms | WALL_CERAMIC_AREA | room | PARTIAL | FIN.WALL.TILE | Mode A (tile height); a window sill is not in a plan |
| Ceilings | CEILING_AREA | room | PARTIAL | FIN.CEILING | measured, but always PROVISIONAL (the ceiling type is not in a plan): a PROVISIONAL answer |
| Ceilings | DOUBLE_HEIGHT_EXCLUDED_AREA | room | PARTIAL | room `double_height_m2` | from void symbols and stacked plans only |
| Doors | DOOR_COUNT | floor × class | SUPPORTED | DOOR.* lines | a candidate or unresolved class is a flagged omission |
| Doors | DOOR_OPENING_WIDTH | door | SUPPORTED | opening `width_m` | as drawn; the owner minimum (D-16) is never applied |
| Doors | DOOR_CLASS | door | SUPPORTED | door schedule class | PVC / ALU / MAIN / LIFT |
| Doors | DOOR_LEAF_WIDTH | door | PARTIAL | the drawn leaf | not every symbol draws a leaf |
| Doors | DOOR_HEIGHT | door | UNSUPPORTED | none | not in a plan (in Mode A it is the input) |
| Windows and glazing | WINDOW_COUNT | floor | SUPPORTED | ARCH.WINDOW lines | |
| Windows and glazing | WINDOW_WIDTH | window | SUPPORTED | opening `width_m` | |
| Windows and glazing | WINDOW_HEIGHT, SILL_HEIGHT, GLAZING_AREA | window | UNSUPPORTED | none | not in a plan |
| Plaster and paint | PLASTER_AREA | room | SUPPORTED | FIN.PLASTER | Mode A (plaster height) |
| Plaster and paint | PAINT_AREA | room | PARTIAL | FIN.PAINT | paint above wall tile is held |
| Skirting | SKIRTING_LM | room | SUPPORTED | FIN.SKIRTING | floor glazing and sill windows not told apart |
| Waterproofing | WP_FLOOR_AREA, WP_UPTURN_AREA, WP_DOORWAY_AREA | room | SUPPORTED | FIN.WP.* | |
| Wall runs and openings | WALL_RUN_LM | floor | PARTIAL | ARCH.WALL_RUN | PROVISIONAL; both faces drawn over ≥ 0.30 m |
| Wall runs and openings | OPENING_COUNT | floor | SUPPORTED | opening records | |
| Wall runs and openings | MASONRY_AREA | floor | UNSUPPORTED | none | material and height: BLOCKED_RFI |
| Stairs | TREAD_COUNT, TREAD_AREA, LANDING_AREA | stair | PARTIAL | FIN.MARBLE.* | straight and winder flights in plan |
| Stairs | RISER_AREA, FLIGHT_SLOPING_LM, HANDRAIL_LM | stair | UNSUPPORTED | none | the rise is not in a plan: BLOCKED_RFI |

## 2. The independent reference

**Author.** An independent quantity surveyor appointed by the owner.
- The QS is not the engineer.
- The QS is never shown any engine output for this villa.

**Allowed methods:** `QS_HAND_TAKEOFF` and `QS_CAD_MEASUREMENT`. The reference states:
- its method;
- `engine_outputs_consulted: false`;
- the sha256 of every drawing it was measured from;
- the conventions used wherever an owner rule is still open (D-16, D-07, kitchen waterproofing, skirting under windows).

**Audit aid, never the reference.**
- Before sealing the reference, the custodian may audit the QS figures with `tools/indep_reader.py`. That reader uses ezdxf, shapely and arithmetic, and imports no engine module.
- The QS settles any difference.
- The reader is never itself the reference: it was written by the engineering side.

**Not generated from the engine.** The scorer refuses a reference in any of these cases:
- **REFERENCE_ENGINE_DERIVED:** the reference says engine outputs were consulted.
- **REFERENCE_METHOD_NOT_ALLOWED:** the method is not an independent QS method.
- **REFERENCE_LEAKAGE_MARKER:** an engine identifier or field name appears anywhere in it. Examples are a method or policy id, an engine room / opening / correction / face / door-element id, a source-handle reference, or `measured_net` / `evidence_state` / `line_id`.
- **REFERENCE_MATCHES_ENGINE_DIGITS:** the reference repeats the engine's digits. The test is: 5 or more values that carry 4 or more decimals equal the engine's value exactly, and they make up half or more of such values.

**A metric the QS cannot measure is left out, never entered as 0.** An UNSUPPORTED metric may still be given. It is reported with its total and not scored.

## 3. Sealing, commitment and the run

The sequence is fixed. A step out of order voids the round.
1. **Seal.** This protocol, the scorer and the template are committed with `SEAL.json`. Done in Phase 2B-8.
2. **Second villa.** The owner supplies a drawing set that the engine has never seen. The custodian records the sha256 of every file. None of these files ever enters git or a shareable package.
3. **Reference.** The QS prepares the reference in the `URBAN_BLIND_V2_REFERENCE` format.
4. **Commitment.** The custodian runs `blind_score_v2.py commit` and publishes the result: sha256(salt + reference), the protocol sha256 and the drawing sha256s. The reference stays with the custodian.
5. **Acceptance criteria.** The owner approves or amends section 6. That is a protocol amendment, so it is re-sealed **before** the run.
6. **Run.** The engineer runs the frozen methods once per plan file and mode, U and A. The facts for Mode A are prepared by someone who has not seen the reference. A crash or a refusal is the result; nothing is re-run.
7. **Freeze.** The output directory's file hashes are recorded and sent to the custodian. The outputs are read-only from then on.
8. **Reveal and score.** The custodian releases the reference and the salt, and `blind_score_v2.py score` is run. Before scoring anything, the scorer checks:
   - the seal;
   - the reference itself;
   - the commitment;
   - that the run's method is frozen;
   - that the run's drawing is in the reference's set.
9. **Report.** Aggregate tables per category and metric are published, never a single number. Each error is classified per V1 section 9. The reference totals go into the firewall list.
10. **After the reveal.** No change made after the reveal is ever scored as blind on this villa.

## 4. Matching and tolerances

**Matching**
- **Room:** the engine room of the same floor whose polygon contains the reference label point; the smallest wins where faces nest. If two reference rooms fall in one engine room, they are MERGED and scored once, on their sum.
- **Door and window:** the nearest engine opening of the floor within 0.60 m, each engine opening used once.
- **Stair:** the engine space containing the reference point.

**Tolerance:** |engine − reference| ≤ max(abs, rel × reference). The values are pre-registered:

| Unit | abs | rel |
|---|---|---|
| m² | 0.10 | 2 % |
| lm | 0.05 | 2 % |
| m (widths) | 0.02 | — |
| counts and classes | exact | — |

## 5. Outcomes and metrics

Each reference item has one outcome:

| Outcome | Meaning |
|---|---|
| RELEASED | A released value exists. Its error is reported, and it counts toward coverage and acceptance. |
| PROVISIONAL | A value exists in a provisional, bounded or assumed state. Its error and tolerance are reported (`provisional_error`, `provisional_within_tolerance`, `coverage_qty_incl_provisional`). It never counts as released coverage or acceptance. |
| FLAGGED | An RFI, a **conditional** (review-space scenario) quantity, or a line without a value. It is not an answer. |
| SILENT | No line and no flag. |
| NOT_APPLICABLE | The engine says the item does not apply, with evidence. |
| MERGED | The item is answered by another reference room's engine room. |

Per metric, the scorer reports:
- `reference_items` and `reference_total`;
- `coverage_qty`;
- `wape_released`;
- `within_tolerance_share`;
- `total_error_pct`, with released predictions and false positives included;
- `false_positive_items` / `false_positive_qty` / `fp_share`;
- the outcome counts.

An UNSUPPORTED metric reports only `reference_items`, `reference_total` and why.

## 6. Acceptance criteria: PROPOSED, pending owner approval

A metric meets the criteria on the blind villa when all of these hold:
- coverage_qty ≥ 0.90;
- within-tolerance share ≥ 0.90;
- |total error| ≤ 3 %;
- 0 silent omissions;
- false-positive share ≤ 2 %.

While the criteria are PROPOSED, the scorer reports PROPOSED_PASS or PROPOSED_FAIL, never acceptance.

Approval is owner decision OD-P8-01, and it must be made before the run. Separately, an accuracy percentage still requires two independent blind projects (V1 section 8).

## 7. Readiness (Phase 2B-8)

- **Second villa.** No second independent villa set exists in the authorised workspace. The only real drawings there are the reference villa's architectural and structural sets, which belong to one project. OD-P8-02 asks the owner to supply one.
- **Ready now:** the protocol, the scorer and the template, which are sealed, and the independent reader, which is available as an audit aid.
- **Not done:** no engine method has been run on any second-villa drawing.
