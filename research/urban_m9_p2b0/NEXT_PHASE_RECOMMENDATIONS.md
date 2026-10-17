# Recommendations after Phase 2B-0 (proposal, not started)

**Scope:** nothing here is implemented. The blind round and Phase 2B-1 start only with owner approval.

## 1. Prioritized recommendations

| # | Recommendation | Why now | Depends on |
|---|---|---|---|
| 1 | **Answer the six round-gating owner decisions:** OD-1 sill / floor-level glazing, OD-2 the held door, OD-3 the envelope question, OD-4 the lift candidates, OD-5 the main entrance, OD-6 the facts preparer. Also approve amendment A1 (OD-14). | They decide what the scored skirting and door totals *mean*. Without them, a skirting or door error in the round cannot be told apart from a rule disagreement. | owner only; no code |
| 2 | **Appoint the QS, agree the conventions sheet, and identify a second blind project** (OD-15, OD-16). | A one-project round can only be diagnostic. The claim rule needs two. | owner |
| 3 | **Run the blind round as pre-registered** (URBAN_BLIND_V1, amendment A1): Mode U on V2.1 and V2.2, Mode A on V2.2 only. Re-run `make_readiness_record.py` at the tagged commit and log its digest. | It replaces opinion-ranked gaps with measured error per trade. The engineering prerequisites are now met. | 1, 2 |
| 4 | **Phase 2B-1, ordered by the round's measured errors.** The default order below applies if the round is not yet available: | | 3 |
| 4a | Door and window schedule tables read from DXF text (heights, types, sill status). | The largest unlock: heights for every wall finish and every door / window area. It also answers OD-1 per window from evidence. | facts workflow (exists) |
| 4b | A deduction rule for face-closing openings (F-26), once OD-7 is answered. | Closes the 24 wall-finish ranges. A small, testable change. | OD-7 |
| 4c | Provisional-door confirmation from an independent opening plus two typed sides, never from a dimension alone (DR-05). | 6 doors; 6 of 28 door sets on the reference plan. | none |
| 4d | Reveal and threshold emitters (SE-01 … SE-03, Q-S6-1). | 26 window reveals, 39 thresholds, 6 out-of-scope closure strips. | OD-8, OD-11 |
| 4e | The families the ledger still has no emitter for: facade, roof, sills. | `boq_completeness` stays NOT_ESTABLISHED until they exist. | rule decisions |
| 4f | Rotated columns (F-9) and DWG DIMLFAC (F-13). | No effect on orthogonal DXF plans. Moves up only if the blind set is rotated or DWG-only. | intake census of the blind set |
| 5 | **Promotion of V2.2 to a default:** only after the blind round, never before it (OD-17). | V2.2 has run on 2 synthetic villas, the new fixtures and one real plan. | 3 |

## 2. Independent objections and challenges

1. **"F-24 fixed" is not "wall finishes measured".**
   - V2.2 stops the run from aborting and from releasing negative quantities. That is release safety.
   - On the reference plan with test heights, 12 of 30 plaster lines remain ranges, because doors closed by their leaf and face glazing are not deducted (F-26).
   - Do not read the release counts as accuracy.
2. **The F-17 fix is conservative by design.**
   - It releases the lower outcome, and the range carries the rest.
   - Where the truth is "sill window", released skirting is now **under**-stated by up to 25.348 m on the reference plan, until OD-1 is answered.
   - That is the intended trade: no arbitrary midpoint. But a QS comparison of released skirting alone will show a shortfall that the range explains.
3. **The recessed-frame sill convention was kept, not fixed.**
   - It is inherited V1 behaviour, and it can be wrong for floor-level glazing in a recessed frame.
   - Replacing it with a range everywhere would be "safer", but it would move every recessed-window threshold into a range without evidence that the convention is wrong. That is an owner call (OD-1).
4. **Lift candidates come from topology, not from a lift.**
   - A shaft-coded space plus an opening is a strong hint, not proof: service shafts and dumbwaiters look the same.
   - That is why candidates are REVIEW and never excluded or released automatically.
5. **The F-20 rule is a heuristic with a known false-positive mode.**
   - "A doorless opening listed by this space alone" also fires when the other side is internal but was not closed into a room: a stair void, a double-height area, or an undetected corridor.
   - That is acceptable because the outcome is REVIEW, never a reclassification to aluminium.
6. **Ledger conservation is bookkeeping, not completeness.**
   - Every emitted line is now accounted for. Lines the engine never emits (facade, roof, sills) are still invisible to conservation.
   - The ledger says so (`NOT_ESTABLISHED`). It should never be presented otherwise.
7. **The test base is narrow.**
   - Every fixture here is synthetic and orthogonal, apart from the rotated metamorphic cases.
   - The only real drawing is the development plan the defects were found on. Fixing defects found on the development plan before a blind round is legitimate. It also means the blind round is the first independent test of V2.2.
8. **The full suite carries a large baseline of environment failures** (missing private data). It cannot show a regression in those tests. The classification in `TEST_RESULTS_AND_INTEGRITY.md` separates them, but it cannot exercise them.

## 3. Reasons to delay the blind round

The engineering side is ready. The round should still wait for:

1. **OD-1 … OD-5.** Without them the round scores skirting and doors against an undefined rule. The result would measure the rule gap, not the engine.
2. **OD-6, a named facts preparer.** Without it, Mode A cannot run, and wall finishes, door / window areas and reveals go unscored.
3. **A second project (OD-16).** With one project, no percentage claim is allowed. The round is still useful as a diagnostic, but it should be planned as one.
4. **A QS and an agreed conventions sheet (OD-15).** Without them, the benchmark's own conventions are unknown at scoring time. That is the one failure mode the protocol cannot repair after the reveal.
5. **Approval of amendment A1 and the hash freeze (OD-14).** The scorer and protocol changed in this phase (window positions). Running before approval would leave the change unratified.

None of these needs engineering work, so the delay is owner time only.
