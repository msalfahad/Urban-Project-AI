# Urban Phase 2A: acceptance review and blind-test readiness

**Date and scope:** 2026-10-14. Review of Phase 2A at `e78f6bd` (commits `23cf674` … `e78f6bd`).

**Constraints honoured:** no production quantity changed. V1, V2, route G, the historical outputs and `opening_census.py` are untouched. V2.1 stays opt-in. The private benchmark was not opened.

**Verdict (stop at the gate):**
- **Phase 2A is accepted as engineering work, with conditions.**
- **V2.1 is not ready to be a default, and not yet fully ready for a blind round.**
  - Mode U (drawings only) can run now.
  - Mode A (with heights) stops on the reference plan because of a pre-existing defect (F-24).
- **One of the two unexpected reference-plan changes is accepted (the cell); the other is rejected (the skirting).**

**Documents in this folder:**

| File | Content |
|---|---|
| `BEFORE_AFTER_DECISION_MATRIX.csv` | BA-01 … BA-16: values, cause, evidence, predicted?, ablation, safe?, decision, competing interpretation, owner action |
| `DOOR_READINESS_REPORT.md` | readiness matrix, owner-rule check, door issues DR-01 … DR-07 |
| `SURFACE_ELIGIBILITY_RFI_REGISTER.csv` | the 135 + 5 ledger records as 10 distinct questions SE-01 … SE-10 |
| `blind_test/BLIND_TEST_PROTOCOL.md`, `blind_score.py`, `dry_run.py`, `DRY_RUN_RESULT.json` | the pre-registered blind test and its proven scorer |
| `GAP_PRIORITY.csv`, `NEXT_STAGE_ROADMAP.md` | the ranked gaps and the proposed next phase (not started) |
| `TEST_RESULTS_AND_WEAKNESSES.md` | every test run of this review and the open weaknesses |
| `research/freeze_integrity/ENGINEERING_FINDINGS.jsonl` | F-17 … F-24 appended (hash-chained) |

## 1. How the work was verified independently

These checks were made by this review. They did not rely on the sprint's own verifier.

1. **V1 / V2 unchanged.**
   - The CLI was run from a worktree at the pre-sprint commit and from `e78f6bd`, for both methods.
   - Drawings: the synthetic villa, a mirrored / turned / moved villa, and the reference plan.
   - **98 of 98 published files are byte-identical**, workbooks included.
2. **V2.1 deterministic.** Two runs give identical files.
3. **Frozen artefacts.** The baseline index check finds **0 differences**.
4. **Attribution.**
   - A private ablation separates the two V2.1 geometry switches.
   - **Every material change comes from the robust predicate.** The mean axis changes nothing at 6 dp.
   - With both switches at their frozen values, V2.1 reproduces V2.
5. **Geometry.**
   - Each changed quantity was traced to the drawn entities: wall-face pieces, frame lines, threshold lines.
   - This was done with the per-edge boundary roles instrumented.
6. **A stress test the sprint did not run.** The reference plan was run with heights supplied: test values, an experiment only. This exposed F-24.

## 2. Task A: the before / after audit

The full matrix is `BEFORE_AFTER_DECISION_MATRIX.csv`.

**The mechanism behind all of BA-01, 02, 03, 10, 11 and 12:**
- Two wall-face pieces on the ground floor are drafted as exactly 100 mm. They compute to 99.99999999965 mm and 99.99999999988 mm.
- V2 drops them under its 100 mm threshold through floating-point error. V2.1 keeps them.
- With those pieces as jambs, two gaps become openings:
  - a 1.0 m **door** from the kitchen into a small unlabelled space: the predicted U1;
  - a 1.0 m **window** in a 0.20 m internal wall between that space and a dining niche.

### 2.1 The unlabelled cell, 1.64 → 1.56 m² (BA-11): **accept as geometry; not as a typed room**

**Exact cause:**
- Without the window opening, the V2 face walk entered the window gap. It stopped at the outer frame line, 80 mm inside the 200 mm wall.
- So 0.080 m × 1.000 m = 0.080 m² of window reveal was counted as room floor. The perimeter carried two 0.08 m jamb returns and a 1.0 m glazing edge (5.16 m).
- V2.1 closes the cell at its own wall face with a window threshold. This is exactly the convention used for every other window (perimeter 5.00 m).
- The 0.080 m² moves into the window's reveal strip.

**Conservation:**
- The plate is identical.
- Unlabelled area −0.080; doorway strips +0.128; wall and column mass −0.048. The frame cells, formerly wall mass, are now reveal strips.
- Net change: 0.

**Predicted?** No. Round 2 said the rooms were identical.

**Safe?** Yes, as geometry. The line stays ARCH.SPACE PROVISIONAL and an RFI. No finish quantity depends on it.

**Competing interpretations** (the owner should answer the second):
1. The opening is floor-level glazing or a serving hatch rather than a sill window. The strip would then be a floor or threshold, not a reveal; the cell itself would not change.
2. **The space may not be an internal room.**
   - Its level text is 0.15 m below the kitchen's and 0.85 m below the main floor's.
   - It has a 1.4 m opening to the facade with no door.
   - If it is an external service area, its floor belongs to external works. The kitchen door into it is then external: aluminium, not PVC (DR-03).

### 2.2 The dining-niche skirting, 1.90 → 2.40 m (BA-12): **reject**

**Exact cause:**
- On the dining side, the window frame is drawn flush with the wall face.
- So the threshold line that V2.1 adds lies exactly on a drawn window line. The boundary edge carries two roles: WINDOW_THRESHOLD and WINDOW.
- `arch_rooms._one_sided_roles` divides an edge's length equally among its roles. The result is 0.5 m "sill window" (skirted) plus 0.5 m "glazing edge" (not skirted).

**Why 2.40 m is wrong:** under the engine's own rules the answer is either:
- **1.90 m**: no skirting under floor-level glazing; or
- **2.90 m**: a sill window, with the skirting running under it.

2.40 m is not a possible physical answer.

**The defect is older than Phase 2A (F-17):**
- The same 50 / 50 split already acts in V2 on about 16.7 m of the boundary of rooms whose skirting is released.
- About 8.4 m of the V2 released skirting rests on the split. The V2.1 figure is about 9.3 m.
- Phase 2A only made one more instance visible.

**Owner action:** the window type, sill or floor-level, from the schedule or elevations. **Engineering action:** one role per edge, with a REVIEW range where the frame lies on the face (proposed, not done).

### 2.3 The rest

| Item | Decision |
|---|---|
| BA-01: +1 door | **Accept** the count and width. The door's class is challenged (DR-03). |
| BA-02: +1 window | **Accept** as an opening. Its type is unverified (an internal window). |
| BA-03: +0.20 m wall run | **Accept.** It is the two 0.100 m pieces. |
| BA-04 … BA-09: the owner door classes | **Accept**, except two door holds (DR-02, DR-03) and the silent withholding (F-19). |
| BA-10: one more threshold strip and one more window-reveal strip, as RFIs | **Accept.** |
| BA-13: float noise | **Accept.** |
| BA-14: identical plates | **Accept.** |
| BA-15: +9 unresolved | **Accept.** Composition: 3 door heights, 2 frame disagreements, 1 swing, 1 main entrance, 1 threshold and 1 reveal. |
| BA-16 | **Accept.** 6 of 23 threshold decisions flip relative to the frozen predicate; only 2 change a line. |

## 3. Task B: door readiness

The full report is `DOOR_READINESS_REPORT.md`.

**On the reference plan:** 28 door sets (29 leaves). 21 are confirmed, 6 provisional, and 1 an unresolved swing.

**Release-safe now, as count and width:** 16 door sets.
- 14 PVC: 12.2 m.
- 2 aluminium: 1.9 m.

**Held:**
- 1 aluminium door has a 0.9 m opening against a 1.0 m frame and is still released (F-18).
- 1 PVC door may be external (F-20).

**Withheld correctly:**
- 2 main-entrance candidates. Count 0 confirmed. Heights and areas blocked. Material NOT_ESTABLISHED.

**Withheld silently:** 1 door with an unresolved class (F-19).

**Heights and areas:** **0 of 28 door sets have a height or an area** (no source exists).

**Lift doors:** none classified, so the exclusion is untested. Three probable lift openings are passages (F-22).

**Double leaf:** one set.

**No fallback height was used, and no provisional door was promoted.**

## 4. Task C: surface ledger

The full register is `SURFACE_ELIGIBILITY_RFI_REGISTER.csv`.

**The 140 records are 7 owner-facing questions and 3 engineering / documentation items:**

| Id | Topic | Records |
|---|---|---|
| SE-01 | Window reveals | 52 |
| SE-02 | Door reveals and the door lining | 42 |
| SE-03 | Passage reveals and full height | 18 |
| SE-04 | Lift entrances | 6 |
| SE-05 | Reveals of unconfirmed doors (dependent; not an RFI) | 14 |
| SE-06 | Thresholds | 7 of the 140, plus 26 already BLOCKED |
| SE-07 | Kitchen waterproofing | 1 |
| SE-08 | The authority of each surface | — |
| SE-09 | Ledger conservation: 102 of 427 lines are outside the ledger | — |
| SE-10 | Window type | — |

**The review rules, applied:**
- **Reveals.**
  - On the reference plan, every window wall is 0.20 m and every door wall 0.15 or 0.20 m. A fixed 0.25 m depth exceeds all of them, and frames are often flush with one face.
  - The depth should be measured from the frame line, with 0.25 m as an ASSUMED cap. The alternative is for the owner to confirm that 0.25 m includes finishes not drawn.
- **Full height.**
  - Full height is decidable only where head lines are drawn: 2 of 9 passages.
  - One "passage" (11.22 m along a column line) is probably not an opening at all.
- **No duplicates.**
  - Door reveals may duplicate the PVC door set's lining (SE-02).
  - The threshold must be removed from both adjoining floors (SE-06).
- **Kitchen waterproofing:** kept as an open owner decision. Nothing is inferred.
- **Eligibility:**
  - Ceilings rest on a PROPOSAL row.
  - Walls (UP-CER-009) and wet areas (UP-CER-001, UP-WP-001 / 002) rest on owner rules.
  - Thresholds rest on the open Q-S6-1.
  - **Every wall finish is blocked by missing heights.**

**Two engineering defects:**
- The 5 NO_EMITTER records are engine limits: the emitter exists but stops (STRIP_NOT_ATTRIBUTED).
- The ledger does not conserve the BOQ lines (F-21).

## 5. Task D: blind test

The protocol is `blind_test/BLIND_TEST_PROTOCOL.md`.

**How it is sealed and scored:**
- The benchmark is sealed by a salted sha256 commitment.
- The prediction is frozen by the hash of every published file.
- The scorer is committed before the drawings arrive.

**Metrics:**
- per trade, per floor, and for kitchens and bathrooms separately;
- coverage, WAPE, tolerance hits, total error;
- silent and flagged omissions kept apart;
- duplicates, false-positive items and quantity;
- door class confusion and width error;
- room category confusion.

**Claims:** a percentage claim needs every bar met on **two** independent projects. With one project the scorer refuses every claim, and a test enforces this.

**Dry run:** on the synthetic villa, **6 of 6 injected faults are detected**, each in its own category. The engine's perfect synthetic score is not evidence, because the villa is its own fixture.

**Pre-registered expectations:**
- **Mode U** will flag wall ceramic, plaster, paint, door and window areas, reveals and thresholds.
- **Mode A** must not run on V2.1 until F-24 is fixed.

## 6. Task E: gap ranking

The full ranking is `GAP_PRIORITY.csv` and `NEXT_STAGE_ROADMAP.md`.

| Order | Gap |
|---|---|
| 1 | F-24 and F-17: wrong or stopping **released** quantities |
| 2 | Door guards |
| 3 | Heights, through a facts sheet first, then schedule tables, then elevations |
| 4 | The blind round |
| 5 | Provisional opening confirmation |
| 6 | Ledger conservation and missing emitters |
| 7 | Reveals and thresholds |
| 8 | Rotated columns |
| 9 | DWG DIMLFAC |
| 10 | Full BOQ coverage, an outcome measured per round, not a package |

## 7. Required final response

### 1. What worked

- **The robust predicate does what Round 2 predicted.**
  - It keeps drafted-exact 100 mm pieces that V2 lost to floating-point error.
  - It recovers one door and one window on the reference plan.
  - It has 0 UNDECIDABLE decisions, and every decision is recorded.
- **V2.1 is genuinely opt-in.** V1 and V2 are byte-identical to before the sprint across 98 files, and V2.1 is deterministic.
- **The door model:**
  - stable ids;
  - conservation holds on every floor;
  - double leaf = one set;
  - main-entrance candidates withheld rather than assumed;
  - no fallback height;
  - provisional doors never promoted.
- **The ledger never counts a NO_EMITTER, UNRESOLVED or BLOCKED record as a "missing item".** CONFIRMED_MISSING is 0.
- **The dimension cross-check** resolves DIMLFAC per dimension and changes no quantity.
- **The freeze baseline and the findings chain held** through the sprint and this review.

### 2. What failed or remains unverified

**Failed (found in this review; all open):**
- F-24: the run stops whenever wall heights are supplied (V1, V2 and V2.1 on the reference plan).
- F-17: the 50 / 50 role split in skirting (BA-12, and about 8.4 m already in V2).
- F-18: a door is released with an open width REVIEW.
- F-20: a door into a probably external space is classed PVC.
- F-19: a door is withheld silently.
- F-21: the ledger misses 102 lines, and its NO_EMITTER label is mislabelled.
- F-22: lift entrances are not recognised without a word.

**Unverified:**
- **Any accuracy on an unseen drawing.** Nothing was measured, so no percentage can be claimed.
- Route G in this review (the sprint's verifier only).
- The window types, the type of the unlabelled space, door heights, and the main entrance.

### 3. Safe to accept

- BA-01: the door count and width.
- BA-02: as an opening.
- BA-03.
- BA-04, BA-08, BA-10, BA-13, BA-14, BA-15, BA-16.
- BA-11, as geometry only.
- BA-05 for 14 PVC doors.
- BA-06 for 2 aluminium doors.
- The withholding in BA-07 and BA-09.

### 4. Requires owner approval

| What | Owner choice |
|---|---|
| **BA-12** | Reject 2.40 m. Choose 1.90 m or 2.90 m by window type. |
| The class of the kitchen door into the unlabelled space | PVC or aluminium. Is that space inside the envelope? |
| The width of the held aluminium door | 0.9 m or 1.0 m |
| The main entrance | which door, and its material |
| Door heights | a schedule or elevations, or a project height recorded as ASSUMED |
| SE-01 … SE-07 | in particular: is the 0.25 m reveal depth a cap or a fixed value; do door reveals exist under a PVC lining; the threshold finish (Q-S6-1); kitchen waterproofing |
| ELIGIBILITY_V0 ceiling row | approve or amend |
| Phase 2B-0 | approve or decline (section 7.7) |

### 5. What I recommend changing in the plan

1. **Put a release-safety version (2B-0) before the blind round.**
   - It fixes F-24, F-17 and the door guards.
   - Score V2.1 and the new version side by side, both frozen before the reveal.
2. **Replace "elevation extraction" with a heights facts sheet that the owner fills from the sections.** Read schedule tables next. Build elevation reading only if the blind round shows schedules are usually missing.
3. **Move rotated columns and DWG DIMLFAC to the bottom.** Neither changes a released quantity on the reference plan.
4. **Make the ledger conserve every line before any omission figure is quoted from it.**
5. **Plan two unseen projects, not one.** One project can rank the gaps; it cannot support a percentage claim.
6. **Treat the synthetic villa as a regression fixture only.**

### 6. My objections to the instructions

1. **"0.25 m reveal depth".**
   - It exceeds every wall drawn on the reference plan (0.15–0.20 m).
   - As a fixed depth it would over-measure every reveal.
   - I recommend measured depth with 0.25 m as an ASSUMED cap, unless 0.25 m is meant to include undrawn finishes or cladding.
2. **"All internal doors PVC / external aluminium".**
   - The rule needs a definition of *external*: the building envelope, or weather exposure.
   - The reference plan already has a door into a semi-external service space where the two readings give different materials.
3. **"Lift shaft excluded from ordinary room finishing".** I agree. But the shaft's own finishes and the landing surrounds should appear as named lift-package lines, so the exclusion cannot become a silent omission.
4. **"Prepare V2.1 for a genuinely blind test" together with "do not change production quantities" and "no Phase 2B".**
   - These cannot all be met for Mode A: V2.1 stops when heights are given (F-24).
   - I kept to the constraints. The consequence is that only Mode U is ready.
5. **"Group the 135 + 5".** I agree. But 14 of them are not questions (they depend on door confirmation), and 5 are engine limits mislabelled as NO_EMITTER. The owner faces 7 questions, not 10 or 140.
6. **The Task E list ranks only coverage gaps.** Ranked that way, the defects that make released numbers wrong (F-24, F-17, F-18, F-20) would stay in place behind lower-value work.

### 7. Proposed next implementation phase, and why

**Phase 2B-0: release safety and blind-round readiness.** It is a new opt-in method version; V1, V2 and V2.1 stay frozen. Its content is set out in `NEXT_STAGE_ROADMAP.md` §3:
- per-room opening deduction, with negative values turned into REVIEW (F-24);
- one role per boundary edge (F-17);
- door guards (F-18, F-19, F-20, F-22);
- ledger conservation (F-21);
- window positions in the openings output;
- a heights facts template;
- tagging the blind round's commit.

**Why this phase first:**
- **It is the only work that changes numbers already released.**
- It is small and testable on the existing fixtures.
- It is a precondition for the assisted blind mode.
- It was found on the development drawing, so fixing it before the round does not tune to the blind set.

**After that, the blind round decides the order of everything else.**

**I have stopped at the acceptance gate.** Nothing of Phase 2B has been started.
