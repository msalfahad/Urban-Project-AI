# Next-stage roadmap (proposal, not started)

**Status:** recommendation from the Phase 2A acceptance review, 2026-10-14. Nothing in it is implemented.

**Approval:** Phase 2B starts only with owner approval. The scored matrix is `GAP_PRIORITY.csv`; scores run 1–5, and higher means more impact, more risk or more complexity.

## 1. Ranking

| Rank | Gap | In the brief? | Impact | Risk if left | Complexity | Why here |
|---|---|---|---|---|---|---|
| 1 | Passage deduction per room (F-24) and one role per boundary edge (F-17) | no: found in this review | 5 | 5 | 2 | These produce **wrong or stopping released quantities**. Every other gap is a missing quantity. |
| 2 | Door release guards (F-18, F-19, F-20, F-22) | partly | 4 | 4 | 2 | 2 of 18 released doors should be held. One door is withheld silently. |
| 3 | Heights: facts workflow → schedule tables → elevations | yes (#3) | 5 | 3 | 2 / 4 / 5 | The largest single unlock: walls, door and window areas, reveals. |
| 4 | The blind round (URBAN_BLIND_V1) | yes (Task D) | 5 | 4 | 2 | Without it, ranks 5–10 are ordered by opinion, not evidence. |
| 5 | Provisional opening confirmation | yes (#4) | 3 | 3 | 3 | 6 of 28 door sets; it must never rest on dimensions alone. |
| 6 | Ledger conservation (F-21) and the missing finish emitters | yes (#6) | 4 | 3 | 3 | 102 of 427 lines are outside the ledger. There is no facade, roof or sill item. |
| 7 | Reveals and thresholds | yes (#5) | 3 | 2 | 3 | Blocked by owner decisions SE-01 to SE-06 and by heights. |
| 8 | Rotated columns (F-9) | yes (#1) | 2 | 2 | 2 | No effect on orthogonal plans. |
| 9 | DWG DIMLFAC per style (F-13) | yes (#2) | 1 | 1 | 2 | Dimensions change no quantity today. |
| 10 | Full BOQ coverage | yes (#7) | — | — | — | An outcome, measured per blind round. Not a package. |

## 2. Where this ranking disagrees with the brief's order

1. **Rotated columns and DWG DIMLFAC go to the bottom, not the top.**
   - On the reference plan neither changes a single released quantity.
   - DIMLFAC feeds only the read-only cross-check.
   - Rotated columns matter only on a rotated plan. The blind intake will record whether the drawing is rotated. If it is, rank 8 moves up for that round.
2. **Two defects the brief does not list come first.**
   - **F-24.** With wall heights supplied, the reference plan run stops. This is a latent V1 / V2 / V2.1 defect: a passage is deducted at full width from each of the six rooms that touch it.
   - **F-17.** A coincident-role 50 / 50 split puts about 8.4 m of released skirting on arithmetic, not evidence.

   Both are small to fix. Both affect **released** numbers or the ability to run at all. Fixing them before the blind round is legitimate: they were found on the development drawing, not on the blind set.
3. **Door schedule and elevation extraction is split.**
   - The owner can fill a heights facts sheet (URBAN_ARCH_FACTS_V1 already exists) in an hour per project. That unlocks most of what an elevation reader would, today.
   - Reading schedule tables from DXF text is next.
   - An elevation reader is the most complex item on the list. It should be built only if the blind round shows schedules are usually absent.
4. **The blind round comes before the large features (ranks 5–9).** Its purpose is to replace this ranking with measured error per trade.

## 3. Proposed next implementation phase (for approval)

**"Phase 2B-0: release safety and blind-round readiness."**

**Built as** a new opt-in method version, e.g. ARCH_TAKEOFF_V2.2. V1, V2 and V2.1 stay frozen, byte-identical, and verified as in this review.

**What it contains:**
1. **F-24.**
   - Each room deducts only the length of an opening that lies on its own boundary.
   - A negative net becomes a REVIEW line, never an exception that stops the run.
   - Tests: the synthetic open-plan case of one passage across several rooms, and the reference plan with test heights (private).
2. **F-17.**
   - One role per boundary edge, by a documented precedence.
   - A window whose frame lies on the room face becomes a REVIEW range: [floor-level, sill].
   - It is never a 50 / 50 split.
3. **Door guards.**
   - F-18: an open width REVIEW holds the door.
   - F-19: a DOOR_CLASS_UNRESOLVED finding.
   - F-20: a door into an untyped space that has a doorless facade opening gets a class REVIEW.
   - F-22: an opening of a stacked shaft becomes a LIFT_ENTRANCE candidate, EXCLUDED and REVIEW.
4. **F-21.**
   - A ledger conservation check: every line is in exactly one record, or OUT_OF_LEDGER_SCOPE with a reason.
   - An ENGINE_LIMIT status, separate from NO_EMITTER.
5. **Blind-round readiness.**
   - Tag the round's commit.
   - A heights facts sheet template for the owner, for Mode A.
   - Window positions in ARCH_OPENINGS (so the scorer can match windows by position).
   - No change to the scorer after the drawings arrive.

**Exit criteria:**
- V1 / V2 / V2.1 are byte-identical to `e78f6bd` on the synthetic villa, the mirrored villa and the reference plan.
- The full suite shows no new failure.
- Each change is listed in a before / after register with its cause, as in `BEFORE_AFTER_DECISION_MATRIX.csv`.
- The blind round's readiness checklist (protocol section 11) is complete.

**Not in Phase 2B-0:**
- schedule or elevation readers;
- reveal or threshold emitters;
- rotated columns;
- DWG DIMLFAC;
- any change to frozen outputs, route G or `opening_census.py`.
