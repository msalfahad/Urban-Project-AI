# S6 Phase 1: independent engineering assessment of the twelve requirements

**Verdict.** All twelve requirements are sound, and Phase 1 meets each of them. Four are worth revisiting before Phase 2, because they are either stricter than what they protect, or they leave a known silent path in production: R1/R9 (freezes), R8 (V1 exit behaviour), R4 (what counts as "eligible") and R5 (what geometry can and cannot verify).

---

**R1. Preserve S5, ARCH_TAKEOFF_V1, route G, structural outputs and owner rules**

*Met.*
- V1 is byte-identical: the synthetic villa (15 files), the reference plan (16 files), and the V1 snapshot test against HEAD `6b7a2e4`.
- The rules are unchanged (7 sha256).
- Route G is unchanged, and the full suite is green on the freeze tests.

*Assessment.* The freezes pin the **source bytes** of shared modules. Examples: `opening_census.py` sits in the S8.6 lintel digest, and `urban_intake.py` sits in the M7/M8 engine freezes. So a behaviour-neutral keyword parameter breaks frozen-history tests.

Phase 1 worked around this:
- a parallel module, `opening_gaps.py`, which calls the frozen `band_gaps` at the legacy tolerance;
- a second K2 kernel run inside the admission, costing about 1–3 s on the reference plan.

This is unnecessarily restrictive. Phase 2's reader fixes (nested hatches, MINSERT cells, SOLID fills, rotated columns) belong in `urban_intake.py`, `drawing_model.py` and the architectural reader.

*Recommendation.* Freeze behaviour (output hashes of the frozen runs), not module bytes. Alternatively, approve a recorded "post-freeze changes" list per freeze, as M8 already does with `changed_since_m7_freeze`.

*Owner decision needed before Phase 2.*

---

**R2. Admission and fail-loud validation (units, plan regions, empty drawings, DWG conversion, duplicate filenames, entity completeness)**

*Met.* 31 synthetic fixtures. Before (HEAD V1): 22 silent failures. After: V2 has 0 silent and V1 strict has 0 silent.

| | Blocked with exit 2 and its reason | Flagged on the BOQ | Measured identically |
|---|---|---|---|
| V2 | 9 | 10 | 12 |
| V1 strict | 12 | 10 | 9 |

*Assessment.*
- "Entity completeness" can only be proven against what the readers claim to read. Phase 1 proves two things:
  - every model-space entity has a K2 disposition;
  - the fills read independently of the plan reader (every depth, MINSERT cells, layer-0 inheritance) either sit on a measured column or are flagged on their room.
- What it cannot prove is that an entity the reader *did* read was interpreted correctly. That is the metamorphic suite's job.
- Duplicate filenames matter only where files share an output folder (DWG conversion). Those outputs are now hash-named, and the same file given as plan and structural is FATAL.

---

**R3. Fix the two unit-dependent tolerances; prove mm drawings unchanged**

*Met.*
- `unit_tol(0.001, UNIT_RELATIVE) == 1.0` exactly.
- At 1.0, `opening_gaps` calls the frozen function itself.
- The synthetic villa measures identically in mm, cm, m and inches.
- The reference plan in mm keeps all 341 V1 lines unchanged.

On the reference plan rescaled to metres, V2 gives the same 426 lines, the same rooms (class, words, area) and the same openings as in mm. The **one exception** is on GF:
- one wall-run line is 0.20 m shorter;
- 0.07 m² moves from wall mass to doorway strips;
- both come from two lost wall caps.

HEAD V1 on the same metre drawing silently lost about 44 % of its lines (192 instead of 341).

*Assessment.* The two tolerances were the whole unit defect. The metre run exposed a second, different class of fragility (S6P1-NEW-05):
- Lower length thresholds equal common drafted dimensions: a 100 mm minimum face piece, a 300 mm minimum overlap, and 0.4 / 0.5 m minimum gaps.
- A piece drawn exactly at the threshold sits about 1e-14 below it once the coordinates are scaled, or have decimals, and it is dropped. Two 100 mm door-frame returns are lost in metres.
- A relative 1e-9 slack makes metres equal millimetres. But it also changes the **millimetre** result of the reference plan: two more openings are found on one floor.
  - That is evidence the reference plan already has openings exactly at a threshold.
  - It also means the slack would break "mm unchanged".
- So the slack is **not adopted**. A strict-xfail test records the finding.

*Recommendation.* Adopt the slack in Phase 2, after the owner has reviewed the two openings it adds.

*Other notes.*
- A third literal, `_union(..., 1.0)` in `opening_census.overhead_cover`, is used only by the S8.6 lintel route (millimetre structural drawings) and is left alone.
- V1 keeps its literals. Behind `--strict-admission` it now refuses a unit coarser than 0.03 m (`LEGACY_TOLERANCE_TOO_COARSE`).

---

**R4. Floor-category completeness (measured quantity, explicit exclusion, or blocked/RFI record)**

*Met.* A three-view gate: physical face parts, space × {floor, ceiling, walls, skirting}, and finish zones. UNACCOUNTED fails the run with exit 3, and nothing is published. The gate passes on every floor of the synthetic villa and of the reference plan.

*Assessment.* "Eligible" is not defined by an owner rule. Phase 1 treats all four surfaces as eligible for every measured room, and excludes, with a reason:
- the wall and column mass;
- slivers;
- voids;
- the stair below seen through an opening;
- shafts.

Completeness is not correctness. A lost column or a merged room still partitions the plan, so the gate passes. That is why the entity checks are separate REVIEW flags.

*Recommendation.* An owner-approved surface-eligibility table per space kind, for example: an external covered area's soffit, skirting in fully tiled wet rooms, a stair hall.

---

**R5. Review doorway and window-reveal strips individually; no automatic non-floor classification**

*Met.*
- Each doorway face is its own strip record.
- Its class comes from its boundary evidence (threshold lines of its opening, door closures, glazing).
- It is then checked against the opening geometry: inside the opening box, depth at most the wall thickness, and bounded by glazing for a window.
- Every strip is a BLOCKED_RFI line. A window reveal is neither floor nor excluded.

*Assessment.* Geometry can verify that a strip **is a window reveal**. It cannot verify its **floor status**: that needs the sill height, from the window schedule or the elevations.

On the reference plan, a number of door and passage strips fail the box or depth check:
- thresholds set back from the wall face;
- one face spanning two openings;
- a wide passage cut by zone lines.

These become UNATTRIBUTED RFIs with `failed_checks` and their extents, never silent. A finer check, for example accepting a strip bounded by a door closure inside the jamb box, is a Phase 2 refinement and needs no owner rule.

---

**R6. Physical regions, functional spaces and finish zones kept separate**

*Met* as three views in `FINISH_COVERAGE.json`.

*Assessment.* The finish-zone view is only as rich as V1's S5 zones: zones drawn as lines inside open plans. A full finish-zone model, with zones from finish hatches or a finish schedule, is Phase 2.

---

**R7. Fatal admission errors: exit 2, no final BOQ, diagnostic evidence kept**

*Met.*
- On a stop: `DRAWING_DISCOVERY.json`, `ADMISSION_BLOCKED.json` and `DWG_CONVERSION.json` are written.
- An earlier run's BOQ in the same folder is moved to `SUPERSEDED_<n>`, never deleted.

*Deviation to approve.* A completeness failure exits with **3**, not 2. It still publishes no BOQ, and it keeps the computed lines in `diagnostics/`. A different code lets a caller tell "the drawing cannot be read" apart from "the drawing was read but a surface is unaccounted".

---

**R8. Preserve V1 exit behaviour; test a separate strict mode first**

*Met.* V1 without the flag is byte-identical, with the same exit codes. `--strict-admission` adds only `DRAWING_DISCOVERY.json` on an admitted drawing (byte-equal V1 files), and stops with exit 2 otherwise.

*Assessment.* Keeping V1's exit 0 keeps 22 known silent failure modes reachable in production. Strict mode admits the reference plan unchanged.

*Recommendation.* Make `--strict-admission` the V1 default once the owner has reviewed it on a second real project. Until then, the CLI help says it plainly.

---

**R9. Structural defaults preserved on frozen routes; visible warnings; explicit conventions for V2**

*Met.*
- `urban_boq_m9 arch --structural` without `--conventions` prints a WARNING (V1).
- V2 stops with exit 2, `STRUCTURAL_CONVENTIONS_REQUIRED`.
- Route G's own defaults are unchanged.

*Restriction.* The warning cannot be printed by `urban_boq_m2.py` or `urban_project_run.py`. Both are pinned byte-for-byte by the S1 frozen-route test, so direct route-G users still get no warning.

*Recommendation.* Approve a warning-only change to those two entry points.

---

**R10. Assume no garden finish, kitchen waterproofing, threshold material, stair-hall finish or opening-deduction rule**

*Met.* Every such surface is an RFI line with no quantity and no material. The 85 added lines on the reference plan and the 19 on the villa all have `measured_net = null`.

*Assessment.* V1's existing wall-finish lines deduct every opening (UP-CER-009 as implemented: run × height − openings). That is kept by R1. Whether the owner's rule has a size threshold is listed as an open owner question (S6-ARC-04). It was not changed.

---

**R11. Reproduce the known defects before each fix; rerun the complete regression and metamorphic suites**

*Met.*
- The "before" column of the matrix is the S6 harness run on an export of HEAD `6b7a2e4`: 31 synthetic cases, 4 DWG cases, the finish cases and the real-plan variants.
- Each later fix was first reproduced in the same harness. Examples: the frame-on-wall-layer plate, which went to 780 m² on the synthetic villa without the fix; and the nested-hatch room split on the real plan.
- The full suite was run in two sequential sessions. The metamorphic suites are inside it: m7 metamorphic, m9_s5, and the S6 units, regions and nesting suites.

---

**R12. Test on the existing villa without using human benchmark quantities**

*Met.*
- No benchmark file was opened. The firewall terms appear in no output.
- The real-plan tests are structural: gates, conservation, line identity, flag counts.
- Reference areas are given only where S5 already gave them (an independent area table, used for the plate comparison), and are kept in the private folder.
