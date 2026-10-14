# Blind architectural BOQ test: protocol URBAN_BLIND_V1

**Status:** PRE-REGISTERED, 2026-10-14. Not yet run.

**What this protocol does:**
- It fixes the drawings, the custody, the run, the freeze and the scoring.
- It does all of this before any blind drawing or benchmark reaches the engineering session.
- The scorer (`blind_score.py`) and its dry run (`dry_run.py`, `DRY_RUN_RESULT.json`) are committed with this protocol. A change to either after the drawings arrive voids the round.

**What it does not do:**
- It does not claim any accuracy.
- The only result so far is a scorer dry run on a synthetic drawing. That drawing is the engine's own regression fixture, so a perfect engine score on it is **not** evidence of accuracy.

## 1. Purpose and claim discipline

**The question:** on a villa drawing set the engine has never seen, how much of an independent architectural BOQ does ARCH_TAKEOFF_V2.1 release correctly? How much does it flag instead? How much does it omit silently? How much does it invent?

**The answer** is a table **per trade and per floor**. It is never a single percentage.

**Accuracy claims:** none is made unless section 8 allows it. With one project, section 8 never allows a percentage claim.

## 2. Roles and custody

| Role | Who | May see the benchmark before the freeze? |
|---|---|---|
| Custodian | the owner | yes (holds it) |
| Benchmark author | an independent quantity surveyor (not the engineer, not using the engine) | yes (writes it) |
| Engineer | the engineering session (Claude / Urban) | **no** |
| Facts preparer (assisted mode only) | a person who has not seen the benchmark | **no** |
| Scorer | `blind_score.py`, as committed before the drawings arrive | runs after the freeze only |

## 3. The drawing set

1. **Previously unseen.**
   - It must not be any drawing in the repository, in `data/`, or in the session history.
   - The custodian checks this with the sha256 of every file.
   - The engineer checks it with an entity-count fingerprint against the known drawings, without opening the benchmark.
2. **Content.**
   - The architectural plans of every level, as issued (DXF; or DWG through the adapter, recorded).
   - The sections and elevations.
   - The door and window schedules, if they exist.
   - What is present is recorded before the run. A missing schedule is a fact of the test, not a reason to stop.
3. **Privacy.**
   - The drawings and the benchmark never enter git or a shareable ZIP.
   - Only aggregate results and the protocol records are published.
   - The benchmark totals are added to the firewall's forbidden-number list at the reveal.

## 4. The benchmark (what the QS provides)

**Format:** the benchmark is one JSON file in the URBAN_BLIND_V1 schema, the same schema as `dry_run.synthetic_benchmark()`.

**`rooms`.** One entry per room and level, with:
- `bench_room_id`;
- `floor`;
- `name`;
- `category`, one of DRY, KITCHEN, BATHROOM, STAIR, SERVICE, EXTERIOR, SHAFT, OTHER;
- `ref_xy_m`: the room's label point in the drawing's own coordinates, in metres. This is the only matching key, so no room is matched by name.

**`room_quantities`.** One entry per room and trade:
- FLOOR_AREA (net room area);
- FLOOR_FINISH_DRY and FLOOR_FINISH_WET;
- WALL_CERAMIC, PLASTER, PAINT;
- CEILING;
- WATERPROOFING_FLOOR, WATERPROOFING_UPTURN, WATERPROOFING_DOORWAY;
- SKIRTING;
- STAIR_TREAD_AREA, STAIR_RISER_AREA, STAIR_LANDING_AREA;
- HANDRAIL.

**`elements`.**
- Every door: class PVC / ALU / MAIN / LIFT, structural opening width, height, position, leaves.
- Every window: width, height, sill height.

**`stairs`.** Treads, risers and handrail length per flight.

**Conventions, stated in the file.** These follow the owner rules. Where a rule is still open, the QS states the convention used.
- Floor finish is net of walls and columns. Thresholds are measured separately; they are not in either room.
- Skirting is the room perimeter minus door and passage openings. It runs under sill windows, and not under floor-level glazing.
- Wall ceramic height per wet room. Plaster and paint deduction rules.
- Waterproofing: floor plus upturn, per the UP-WP rules.
- Reveals: left, right and top at the stated depth for ordinary openings; left and right only for full-height openings.
- Doors: one set per door; the main entrance separately; lift doors excluded.
- Kitchen waterproofing: whatever the owner decided. If undecided, the QS lists it separately and it is not scored.

**Sealing.**
- The custodian publishes `commitment(benchmark, salt)`, a sha256 of the salt plus the file, before the run.
- The file stays encrypted, outside the session, until step 6.5.

## 5. Run modes (both pre-declared; both frozen before the reveal)

- **U, unassisted.** Drawings only, with `--method ARCH_TAKEOFF_V2.1`. No facts file and no layer overrides.
- **A, assisted.** As U, plus a facts file (heights, finishes) prepared from the drawings by the facts preparer. It is recorded and hashed before the run.

  Mode A measures the engine with the inputs a QS would read from sections. Mode U measures the engine alone.

**Engine version.** The engine version is the commit tagged for the round.
- If fixes for F-17 to F-22 are wanted in the round, they ship as a separately versioned method frozen before the drawings arrive.
- V2.1 itself is scored as the baseline either way.

## 6. Procedure

1. Pre-registration. This protocol, the scorer and the dry run are committed. The round's commit is tagged.
2. Environment. The run uses the locked environment (`URBAN_REQUIRE_LOCK_ENV=1`, CPython 3.11.17, the lock packages).
3. Intake.
   - The custodian hands over the drawings.
   - The engineer records the sha256 of every file and the drawing discovery (`DRAWING_DISCOVERY.json`).
   - The engineer records which sources exist (schedules, sections, elevations).
4. Run, once per plan file and mode:

   ```
   python3 -I tools/urban_boq_m9.py arch --drawings PLAN.dxf --out OUT --method ARCH_TAKEOFF_V2.1
   ```

   - The output directory is the prediction.
   - A crash, an admission block (exit 2) or a completeness failure (exit 3) **is the result**. Nothing is re-run.
5. Freeze.
   - Run `blind_score.freeze_record(OUT, commit=..., mode=..., drawing_sha256=...)`. It records the sha256 of every published file and a digest.
   - The record is sent to the custodian and committed. It contains hashes only.
   - From this point the outputs are read-only.
6. Reveal and score.
   - The custodian releases the benchmark, and its commitment is checked.
   - The engineer runs `blind_score.export(OUT)` and then `blind_score.score(...)` with the committed scorer.
7. Report.
   - The full metric tables are published in aggregate.
   - Every error is classified (section 9).
   - The benchmark totals go into the firewall list.
8. After the reveal.
   - No change made after the reveal is ever scored as blind on this project.
   - A fix is validated on a new blind project.

## 7. Metrics (computed by `blind_score.score`)

**Matching.**
- **Rooms:** a benchmark room is matched to the predicted room of the same floor whose polygon contains its label point. The smallest such room wins where faces are nested.
- **Merged rooms:** two or more benchmark rooms in one predicted room are MERGED. They are scored once, against the sum of those rooms.
- **Unmatched predicted rooms:** a predicted room with no benchmark point produces false positives.
- **Doors:** matched by position within 0.60 m.
- **Windows:** matched by width within 0.02 m, per floor, since V2.1 publishes no window position.

**Outcome of each benchmark item (room × trade):**

| Outcome | Meaning |
|---|---|
| RELEASED | A released quantity exists. Its error and relative error are reported, with whether it is within tolerance. |
| FLAGGED_OMISSION | The engine produced a provisional, bounded or RFI line, but no released value. Honest, but not an answer. |
| SILENT_OMISSION | No line and no flag at all. |
| DUPLICATE | More than one released line answers the same item (an aggravating flag). |
| FALSE_POSITIVE | A released quantity in a scored trade that answers no benchmark item. Its quantity is added to the total error. |

**Per trade, per floor, and per category** (kitchens and bathrooms reported separately):

| Metric | Definition |
|---|---|
| `bench_items`, `bench_total` | the benchmark items and their total |
| `released_matched` | items answered by a released quantity |
| `coverage_qty` | benchmark quantity of the released-matched items ÷ benchmark total |
| `wape_released_matched` | Σ \|predicted − benchmark\| ÷ Σ benchmark, over released-matched items |
| `within_tolerance` | items with \|error\| ≤ max(0.10, 2 % × benchmark) for m² and lm; exact for counts |
| `total_error_pct` | (Σ released predictions, false positives included, − benchmark total) ÷ benchmark total |
| `silent_omissions`, `flagged_omissions` | counted separately, never merged |
| `false_positive_items`, `false_positive_qty`, `fp_share` | the invented quantity, and its share of the benchmark total |
| `duplicates` | items answered more than once |

**Elements, per floor:**
- benchmark count, released count, matched;
- omissions and released false positives;
- class confusion: benchmark class → predicted class and status;
- width mean absolute error;
- the main entrance separately (MAIN → MAIN_CANDIDATE is a flagged omission).

**Rooms:**
- matched, unmatched and merged;
- category confusion: benchmark category → engine kind, e.g. KITCHEN → SERVICE.

**Not scored, but listed:** item codes that have no trade mapping (`unscored_item_codes`). Nothing is dropped silently.

## 8. When an accuracy claim is allowed

A trade may be described with a percentage only if every one of these holds:
- coverage ≥ 95 %;
- WAPE ≤ 5 % on released-matched items;
- 0 silent omissions;
- false-positive share ≤ 2 %;
- **at least 2 independent blind projects.**

`blind_score.claims` applies these rules. With one project it returns "claim not allowed" for every trade. The test checks this.

"95 %" is never quoted for the BOQ as a whole. Coverage and accuracy are always reported side by side. They are never multiplied into one number.

## 9. Error classification after the reveal

Each non-RELEASED-within-tolerance item gets exactly one cause:

| Cause | Meaning |
|---|---|
| GEOMETRY | wrong boundary, opening or wall |
| CLASSIFICATION | wrong room kind or door class |
| SOURCE_MISSING | the drawings do not contain the information (heights, schedules) |
| CONVENTION_MISMATCH | the engine's rule differs from the QS's stated convention |
| RULE_OPEN | an owner decision is pending |
| BENCHMARK_ERROR | the QS checks and confirms, recorded |
| SCORER_ERROR | a defect in the scorer itself |

**Disputes:**
- The QS decides convention disputes, in writing.
- The engine is not re-run.
- The prediction is not edited.

## 10. Pre-registered expectations

These expectations come from the reference-plan behaviour and are written before the round, so the round can falsify them.

| Trade | Mode U expectation | Why |
|---|---|---|
| Floor area by room and level | released for typed rooms; provisional for unlabelled / merged spaces | geometry is measured; the type comes from words |
| Kitchens and bathrooms separately | kitchen typed SERVICE (dry finish); bathrooms WET | the owner rule keeps kitchen waterproofing open |
| Floor finishes (dry, wet) | released for typed rooms | UP-CER-001 |
| Waterproofing floor, upturn, doorway | released in wet rooms | UP-WP-001 / 002 |
| Skirting | released for dry rooms, **with the F-17 window split** | UP-CER-003 |
| Wall ceramic, plaster, paint | **flagged** (no height source in Mode U). Mode A: measured, but V2.1 over-deducts shared passages and can stop (F-24) | heights missing; F-24 |
| Ceilings | provisional | ELIGIBILITY_V0 row is a PROPOSAL |
| Doors | count and width by class released; heights, areas and the main entrance flagged | no schedule; F-18 / F-20 risks |
| Windows | count and width released; heights and areas flagged | no schedule |
| Stairs and handrails | treads provisional or bounded; risers and handrails flagged | riser height / handrail scope not in plan |
| Reveals, thresholds | flagged | owner decisions SE-01 to SE-06 |

## 11. Readiness checklist (before the drawings arrive)

- [x] Scorer and dry run committed. Six injected faults are each detected in their own category (`DRY_RUN_RESULT.json`, `tests/m9_p2a/test_p2a_blind_scoring.py`).
- [x] V1 and V2 are unchanged by Phase 2A, and V2.1 is deterministic. The acceptance review confirms both.
- [ ] **Mode A is not safe on V2.1 as it stands (F-24).**
  - With heights supplied, a passage shared by several rooms is deducted in full from each room.
  - The run stops with a LineError: the reference plan does.
  - Mode A may run only on a version that fixes this. Otherwise it is declared not run, and the result is not a crash.
- [ ] Owner decisions on BA-11 / BA-12 and the door holds DR-02 / DR-03 (they decide what V2.1's skirting and door totals mean).
- [ ] The QS appointed, and the conventions sheet (section 4) agreed.
- [ ] The round's commit tagged. The decision recorded on whether a fixed version runs beside V2.1.
- [ ] The facts preparer named, if Mode A is run.
- [ ] A second blind project identified (needed for any percentage claim).
