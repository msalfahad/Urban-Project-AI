# Phase 2B-8: V2.7 acceptance hardening and second-villa readiness

**Status.** ARCH_TAKEOFF_V2.7 stays provisionally accepted as an opt-in development method. It is not approved for a production freeze, and no overall accuracy is claimed.

- **New method.** The hardening ships as a new opt-in method, **ARCH_TAKEOFF_V2.7.1** (knowledge registry 1.3.0).
- **Frozen methods.** V1 to V2.7 are byte-identical to their Phase 2B-6 / 2B-7 snapshots (`TEST_EVIDENCE.md` §1).
- **Second villa.** No second villa has been run. None exists in the authorised workspace, and the formal blind evaluation has not started.

Plain terms used below:
- **REVIEW space:** a space the engine cannot type with evidence (for example a basin-only lobby).
- **Conditional quantity:** a quantity that depends on how such a space is eventually classified.
- **The reference plan:** the one real villa architectural drawing in the workspace (private; aggregates only here).

## 1. REVIEW-space BOQ coverage (UP-REVIEW-001, UP-QTY-STATUS-001)

**What V2.7 did.** It withheld every finish of a REVIEW space. On the reference plan, three hand-wash spaces (9.348195 m² in all) had no ceiling, wall, floor or waterproofing line.

**What V2.7.1 does.** It measures each REVIEW space that has a plausible set of classifications under both readings:
- **WET_SCOPE:** a W.C. / wash room, under the owner wet scope UP-WET-001;
- **DRY_SCOPE:** a lobby / wash area.

Every quantity of the space then goes into exactly one of five classes:

| Class | Meaning | Where it is |
|---|---|---|
| GEOMETRY_CONFIRMED | area, ceiling plan, perimeter, wall run and **wall face** measured with confidence, whatever the type | `REVIEW_SPACES.json` geometry; not BOQ lines |
| INDEPENDENT_OF_CLASSIFICATION | identical in every scenario: same quantity, state and rule, and a system that does not depend on the type | **released into the main BOQ**, labelled CLASSIFICATION_INVARIANT |
| CONDITIONAL_ON_CLASSIFICATION | differs between scenarios | scenario sets in `BOQ_SCENARIOS.json` / `BOQ_RELEASE_REPORT.json`, mutually exclusive, never summed |
| REQUIRES_DRAWING_EVIDENCE | no scenario can measure it: a detail, a drain, a height not in the drawing | held, with the reason |
| NOT_ESTABLISHABLE | the space has no evidence-based set of types (a plain unlabelled space) | geometry only; nothing released |

**Plaster.** Plaster is **not** released even when its area is the same in both scenarios.
- Behind wall porcelain the plaster is a different system (UP-FIN-PAINT-001).
- The wall face itself is still reported as confirmed geometry. A reliable wall measurement is never suppressed; it is just not turned into a finish line whose system is unknown.

**The release report.** Every line of the run appears exactly once:
- CONFIRMED;
- HELD, with a reason class: REQUIRES_DRAWING_EVIDENCE, REQUIRES_OWNER_DECISION or ENGINEERING_REVIEW;
- EXCLUDED, with the reason;
- CONDITIONAL scenario sets, kept apart.

The conservation check `every_line_once` holds on every run.

**Reference plan, Mode A, aggregates** (full table in `REVIEW_SPACE_BOQ_DEMONSTRATION.md`):
- The three hand-wash spaces are classified REVIEW in V2.7 and V2.7.1 alike. No V2.7 → V2.7.1 room classification changed.
- V2.7.1 releases their three ceilings, **9.348195 m²**, the only quantity invariant under both readings. That is the only BOQ difference from V2.7 on this plan: 3 lines, 484 → 487.
- Floor finish, wall finish, skirting and waterproofing stay conditional.
- The three other REVIEW spaces have no fixture evidence. They are NOT_ESTABLISHABLE, so their geometry is reported and nothing is released.

Tests: `tests/m9_p2b8/test_p2b8_review_release.py` (18).

## 2. Door-standard reconciliation (UP-DOOR-OPEN-003, registry 1.3.0)

Each door row (`DOOR_STANDARD_RECONCILIATION.json` / `.csv`) keeps these fields apart:
- the as-drawn wall opening (the gap jamb to jamb);
- the measured jamb span (the symbol's own jamb lines);
- the door leaf;
- the finished clear width (NOT_ESTABLISHED: frame stops and leaf thickness are not in a plan);
- the owner minimum (1.00 m ordinary, 0.90 m bathroom; its reference is still open as D-16);
- the frame allowance;
- the proposed enlargement on every reading;
- whether consultant / structural review is required, and why.

**Frame allowance.**
- It is taken only from an accepted source: an approved schedule, a manufacturer detail or a project rule. None is evidenced, so `value_m` is null.
- The 0.10 m of registry 1.1.0 is shown as REQUIRES_CONFIRMATION, never applied.
- The CAD symbol's opening-minus-leaf difference is reported as drawing geometry, not as an allowance.

**What is never done.** The CAD geometry is never changed to meet the minimum. The BOQ measures the as-drawn door, and the enlargement is a CONDITIONAL scenario set (DOOR_OWNER_MINIMUM, depends on D-16), never in the main BOQ.

**The 0.80 m door recovered in V2.7** (reference plan; `DOOR_STANDARD_RECONCILIATION_DEMONSTRATION.md`):

| Field | Value |
|---|---|
| As-drawn opening | 1.023274 m |
| Jamb span | 0.80 m (the BOQ width) |
| Drawn leaf | 0.69 m (swing radius) |
| Symbol difference | 0.11 m (geometry, not an allowance) |
| Owner minimum (bathroom) | 0.90 m |
| Enlargement, structural reading | 0.10 m |
| Enlargement, leaf reading | 0.10 – 0.20 m (the 0.21 m leaf shortfall) |
| Fits inside the drawn gap? | yes; the 0.223 m remainder of wall shrinks to 0.123 / 0.023 m |
| Review | consultant and structural REQUIRED (WALL_REMAINDER_CUT, LINTEL_SPAN_INCREASE) |
| Status | BELOW_MINIMUM_ON_EVERY_READING; nothing applied |

The same pattern on a synthetic plan is derived by hand in `tests/m9_p2b8/test_p2b8_doors.py` (7 tests).

## 3. Recognition weaknesses

| Weakness (V2.7 as found) | V2.7.1 | Evidence |
|---|---|---|
| Round-bowl WC not recognised (false negative) | a circle bowl of pan size (0.32 – 0.42 m), centred on a cistern within 0.05 m, the cistern on a wall within 0.10 m, is WC evidence | 18-plan truth table, invariant under rot30 / mirror / metres |
| Armchair / seat with a WC outline (false positive) | rejected: BOWL_WIDER_THAN_A_WC_PAN, CISTERN_NOT_ON_A_WALL. Every rejected candidate names its failing test | `test_p2b8_recognition.py` |
| A WC-sized chair against a wall | **still recognised as a WC**: geometry alone cannot tell them apart. Documented limitation L-P8-01 (strict xfail); the space is typed with a review flag, never released silently | strict xfail |
| A fixture's id compared with an insert path in another form (L-P7-03) | a basin block's own linework is matched to its insert by the decimal handle of every entity's insert path. On the reference plan the basins' own linework (43 / 86 / 86 entities) is now excluded as the basin, not mistaken for loose fittings | `test_basin_block_linework_is_the_basin` |
| Turned column as a door jamb / wall interruption | a column polygon off the drawing axes is a band-gap obstacle (jamb) and cuts the wall run like a box (UP-COL-ORIENT-001). A plan turned 30° / 37° / 90° or mirrored measures as the unturned plan | `test_turned_column_*` |
| Ten untraced source-entity lines | on the reference plan all ten were threshold strips. V2.7.1 traces them through the strip (STRIP basis), and any line still untraced must state why | `test_every_measured_line_names_its_entities_or_why_not`; reference plan 0 untraced (V2.7: 10) |
| Classification changes without sufficient evidence | reference plan, V2.7 → V2.7.1: **0** room classification changes (38 rooms). V2.6 → V2.7.1: 3, exactly the hand-wash spaces (WET → REVIEW), each re-read by the independent fixture census (§4) | `ref_V2.6_to_271` / `ref_V2.7_to_271` (private, aggregates) |

**Rule kept:** a weak geometric resemblance never becomes an authoritative room classification. When the evidence is insufficient, the space stays REVIEW.

## 4. Attribution: a correction record is not proof

`tools/arch_change_verify.py` lists every BOQ total that differs between two runs of one drawing and the correction records that can explain it. It checks each against **`tools/indep_reader.py`**, a second reading of the drawing with ezdxf + shapely + arithmetic that imports no engine module (tested on its own against hand truth, `test_p2b8_indep_reader.py`, 15 tests).

| Status | Meaning |
|---|---|
| VERIFIED | a record covers it and every applicable independent check agrees with the new value |
| EXPLAINED_UNVERIFIED | a record covers it; no independent check applies (the reason is stated) |
| CONTRADICTED | a record covers it, but an independent check disagrees (exit 1) |
| UNEXPLAINED | no record covers it (exit 1) |

**Independent checks:**
- face area;
- P × H − openings for plaster / paint / tile;
- P − doors for skirting;
- door width × wall thickness;
- jamb plaster 2tH + wt;
- an arc census of concentric wall-layer arcs for the curved wall run;
- a fixture census (inserts by block-name word, loose sanitary-layer pieces) for a wet-evidence decision. This verifies the stated evidence, not the rule.

**Floor-wide records no longer conceal unrelated changes.**
- A layer-role record covers only the locations its own entities touch. It covers the walls only for a wall or column role, because the wall run is read from wall and column linework only.
- A column record covers the rooms near the columns, their openings and the walls.
- A record already present in the before run explains nothing.

`test_a_layer_role_record_covers_only_its_own_entities` proves it: a hand-raised wall run stays UNEXPLAINED next to a real layer-role change.

**Reference plan, Mode A (private run, aggregates):**

| Pair | Differences | VERIFIED | EXPLAINED_UNVERIFIED | CONTRADICTED | UNEXPLAINED |
|---|---|---|---|---|---|
| V2.6 → V2.7.1 | 55 | 32 | 23 | 0 | 0 |
| V2.7 → V2.7.1 | 3 | 2 | 1 | 0 | 0 |

- **V2.6 → V2.7.1, verified:**
  - 26 by the fixture census (the three wet-evidence decisions);
  - 5 by takeoff;
  - 1 by face area;
  - 1 by the arc census: the curved wall run +1.884956 m equals the census.
- **V2.6 → V2.7.1, unverified:**
  - 13: the space is bounded on one side by a 1.256 m line of a non-wall layer, so the wall lines alone do not enclose it;
  - 4: a gap with no door or window symbol;
  - 3: an item with no independent check;
  - 2: a window sill not in the drawing;
  - 1: a withheld line.
- **V2.7 → V2.7.1:** the three released ceilings. Two are verified by the independent face; one is unverified for the non-wall boundary above.

**Two contradictions the first reading found, both resolved by evidence, not by loosening a tolerance:**
1. **The arc census counted 0.209947 m more curved wall than the engine.** Those are two stubs either side of a curved window, where both faces are drawn over less than 0.30 m. The engine's wall run requires both faces over at least 0.30 m, for straight and curved walls alike. The census now applies the same stated convention and lists shorter stubs apart. Whether such stubs belong in the wall run is engineering item **D-P8-03**.
2. **A skirting check deducted only the door, but the engine also deducted a window.** A plan cannot tell floor glazing (no skirting) from a sill window (skirting), so skirting is no longer independently checked where a window is on the face.

Tests: `test_p2b8_attribution.py` (7):
- CROSSING plaster, tile and skirting VERIFIED against hand truth;
- the B10 curved band VERIFIED by the arc census;
- the released ceiling VERIFIED by the independent face;
- wet evidence VERIFIED by the fixture census;
- a hand-perturbed plaster CONTRADICTED;
- an emptied log UNEXPLAINED;
- the layer-role scope test above.

## 5. Second villa: sealed benchmark protocol URBAN_BLIND_V2

No second independent villa set exists in the authorised workspace (`SECOND_VILLA_READINESS.md`). The protocol, scorer and reference template are written and sealed in `benchmark/` (`SEAL.json`) before any second-villa run.

**Coverage:** all requested categories. Each of the 30 metrics is SUPPORTED (13), PARTIAL (9) or UNSUPPORTED (8), with the engine source and the condition.

**Rules the scorer enforces:**
- An UNSUPPORTED metric is reported with its reference total, never scored and never zero.
- The reference must come from an independent QS. The scorer refuses a reference that consulted the engine, names an engine identifier, or repeats the engine's digits.
- It also refuses a changed reference, a wrong salt, an unfrozen method or another drawing.
- Conditional (review-space) and provisional quantities are FLAGGED / PROVISIONAL, never counted as released answers.

**Acceptance criteria:** PROPOSED, pending owner approval (OD-P8-01). The scorer reports only PROPOSED_PASS / PROPOSED_FAIL.

Tests: `test_p2b8_benchmark.py` (14).

## 6. Regression and reporting

See `TEST_EVIDENCE.md`:
- byte identity of V1 – V2.7;
- the targeted suites;
- the independent reader;
- freeze verification;
- the full-suite comparison by test identity against the Phase 2B-7 baseline.

**In brief:**
- V1 – V2.7: 1518 files, 0 differ.
- Freeze check: 0 frozen artefacts differing.
- `tests/m9_p2b8`: 97 passed, 1 strict xfail.
- `tests/m9_p2b7`: 145 passed, 2 strict xfails.
- `tests/m9_kb`: 78 passed.
- Full suite against Phase 2B-7, by test identity: 0 passed → failed, 0 new tests failing, 1 failed → passed (a timing test).

**The full suite is not green.** Its 345 failures + 32 errors are the known private-data set, carried forward unchanged and kept apart from new regressions there.

## What did not work, and what remains

See `REMAINING_DEFECT_REGISTER.md`. In brief:
- the WC-sized chair (L-P8-01);
- spaces bounded by non-wall lines cannot be independently verified (D-P8-04);
- short wall stubs are not in the wall run (D-P8-03);
- D-16, D-17 and D-07 are still open;
- one real plan only;
- no blind evaluation yet.
