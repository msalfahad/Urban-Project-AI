# Review brief for ChatGPT (Phase 2B-8)

**Phase:** V2.7 acceptance hardening and second-villa readiness. The work ships as a new opt-in method, **ARCH_TAKEOFF_V2.7.1** (knowledge registry 1.3.0). V1 – V2.7 are byte-identical.

No overall accuracy is claimed, and the full test suite is not green; its known failures are kept apart from new regressions in `TEST_EVIDENCE.md`.

## What worked

1. **REVIEW spaces now get every quantity that does not depend on their type** (UP-REVIEW-001).
   - Each space under wet-classification review is measured as a W.C. and as a lobby.
   - A quantity identical in both (same value, state, rule and a type-independent system) is released. On the reference plan that is the ceiling of the three hand-wash spaces, 9.348195 m².
   - Their wall faces are reported as confirmed geometry.
   - Everything else is a mutually exclusive conditional set, never summed.
   - Plaster is deliberately not released: behind wall porcelain it is a different system.
2. **Every line is reported exactly once:** confirmed / held (reason class) / excluded / conditional (UP-QTY-STATUS-001). Conservation holds on every run.
3. **The door-standard reconciliation keeps the as-drawn geometry and the owner minimum apart.** For the 0.80 m door recovered in V2.7:
   - as drawn 1.023 m, jamb span 0.80 m, leaf 0.69 m;
   - minimum 0.90 m;
   - allowance not established (the 0.11 m symbol difference is shown as geometry, not an allowance);
   - enlargement 0.10 m structural / 0.10 – 0.20 m leaf reading;
   - consultant and structural review required;
   - nothing applied.
   On the reference plan, 18 of 28 doors are below the minimum on every reading.
4. **Recognition weaknesses closed or bounded:**
   - round-bowl WC recognised;
   - seat and armchair look-alikes rejected, each naming its failing test;
   - a basin's own linework matched by insert path;
   - turned columns are jambs and wall cuts (invariant under rotation and mirror);
   - the ten untraced reference-plan lines are traced;
   - zero classification changes V2.7 → V2.7.1 on the reference plan.
5. **Attribution with independent verification.** `tools/indep_reader.py` (ezdxf + shapely, no engine import, 15 hand-truth tests) re-reads the drawing. `tools/arch_change_verify.py` classes every change: VERIFIED / EXPLAINED_UNVERIFIED / CONTRADICTED / UNEXPLAINED.
   - On the reference plan, V2.6 → V2.7.1 has 55 differences: 32 verified, 23 unverified with stated reasons, 0 contradicted, 0 unexplained.
   - Floor-wide records no longer cover unrelated locations. A hand-raised wall run next to a real layer-role change stays UNEXPLAINED.
6. **A sealed second-villa protocol** (URBAN_BLIND_V2):
   - 30 metrics over every requested category, each SUPPORTED / PARTIAL / UNSUPPORTED;
   - UNSUPPORTED never scored as zero;
   - a scorer that refuses engine-derived, uncommitted or changed references;
   - acceptance criteria PROPOSED.

## What did not work / is not done

1. **No second independent villa exists** in the workspace, so the blind evaluation has not started. That is correct per the protocol, but it means there is still **no accuracy evidence beyond one real plan**.
2. **23 of the 55 reference-plan changes are only explained, not independently verified:**
   - 13: a space bounded by a line on a non-wall layer;
   - 4: passages with no symbol;
   - 3: items with no independent check;
   - 2: window sills not in a plan;
   - 1: a withheld line.
3. **The first independent reading found two real contradictions:**
   - 0.209947 m of curved wall stubs (both faces < 0.30 m) are not in the wall run, by the engine's own convention. That convention may itself be wrong (D-P8-03).
   - A skirting check could not know a window was floor glazing.
   Both are now reported correctly, but the stub question is open.
4. **A WC-sized chair against a wall is still read as a WC** (L-P8-01, strict xfail). Geometry alone cannot separate them.
5. **Still open owner decisions:**
   - D-16: what the door minimum refers to;
   - D-17: the type of the three hand-wash spaces;
   - D-07: the curved wall basis;
   - the heights / sills (D-04): every wall-area line still rests on stated test heights;
   - the new OD-P8-01 (approve the acceptance criteria) and OD-P8-02 (supply the second villa and the QS).
6. **Ceilings and wall runs are PROVISIONAL** in the engine (type / material not in a plan). The release report lists them as confirmed quantities, labelled PROVISIONAL; the benchmark scores them as provisional answers only.
7. **Tooling defects were found when the reader met the real plan and fixed** (RTEXT attributes, Bezier arcs, T-junction noding, unclosed faces). They are recorded so that no verification is trusted beyond its tests.

## Recommendations (ranked; `NEXT_PHASE_PLAN.md`)

1. Read heights and sills from sections and schedules. This is the largest remaining error source.
2. Run the blind second-villa round as soon as OD-P8-01 / OD-P8-02 are answered.
3. Raise verification coverage on the reference plan to at least 80 % VERIFIED (passage rule, declared non-wall boundary rule, upturn / threshold checks).
4. Measure wall stubs and block walls.
5. Turn D-16 / D-17 into lines once answered.
6. Close the catalogue gaps: roofs, external works, formwork / excavation, combined export.

**Do not freeze V2.7.1 for production before step 2.**

## Questions for the reviewer

1. Is releasing only the ceiling, and holding plaster even when its area is identical, the right reading of "do not release plaster if a wall-tiling specification would alter the plaster system"? Or should the plaster substrate common to both systems be released as a separate item?
2. Should wall stubs shorter than 0.30 m (between openings) be measured in the wall run, as QS practice would? This changes the straight-wall convention too.
3. Are the proposed acceptance criteria right for commercial use? They are, per metric: coverage ≥ 0.90, within tolerance ≥ 0.90, |total error| ≤ 3 %, 0 silent omissions, false positives ≤ 2 %.
4. Is it acceptable that the independent reader, written by the engineering side, may be used only as an audit aid to the QS reference and never as the reference itself?
