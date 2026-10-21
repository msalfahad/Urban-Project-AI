# Brief for ChatGPT - Phase 2B-3 (ARCH_TAKEOFF_V2.5)

Context: the Urban Project AI BOQ engine (Python, stdlib engine, DXF architectural route). The owner asked that every
measurement rule be proven on an independently calculated, human-readable example before it is trusted. This phase
built that proof library. What the proofs found wrong is corrected in a new opt-in method, ARCH_TAKEOFF_V2.5. V1 ..
V2.4 are frozen and byte-identical. Reference-plan figures are aggregates; everything else is synthetic.

## What worked

1. **The 3.00 x 4.00 m bathroom is proven** by hand, by an independent reference calculator, by the engine on the
   coordinates and by the engine through a drawn plan.
   - Strips: 5 of 3.00 m (the last 0.40 m); band segment 2.80 m.
   - Quantities: laps 2.72 m2, B 17.52 m2, **consumed 17.80 m2, 2 rolls**, waste 0.28 m2.
   - Strip-by-strip cut inventory with roll allocation and joint positions: `WP2_BATHROOM_3x4_PROOF.md`.
2. **The doorway detail is not assumed.**
   - The proven subtotal (14.80 m2 incl. the doorway continuation) is kept apart from the provisional final
     requirement.
   - The threshold transition is UNRESOLVED with its range (0.00 - 0.20 m2).
   - The roll count is shown to stay at 2 under every doorway alternative.
3. **28 proof cases pass on V2.5**: 13 waterproofing (simplest first), 10 doors, 5 project rules sheets.
   - Hand calculation and independent reference agree on every compared quantity.
   - The expected values are typed literals; an AST test refuses computed ones.
   - The reference imports no engine code; an AST test checks this.
4. **The proofs found 9 engine defects**, all fixed in V2.5 only:
   - a band segment over-allowance (two end laps per lane instead of one), present in every V2.4 case with a new
     segment;
   - no use of roll remainders for the band;
   - first-fit packing missing the minimum (4 rolls vs 3);
   - resolved patch details missing from B and the rolls;
   - an unlapped threshold upturn;
   - a non-conservative door reach boundary;
   - unbound project-rules files;
   - no line-level traceability;
   - a V2.4 "hand" test that had copied the engine formula.
5. **Errors in my own work were caught too** (5, e.g. a hand calculation that evaluated one orientation only).
   - They were corrected by re-deriving the figure by hand, never by copying the engine.
6. **Traceability:**
   - every V2.5 run writes BOQ_TRACEABILITY (owner rule -> drawing evidence -> formula -> independent expected ->
     engine -> line);
   - INDEPENDENTLY_VERIFIED appears only when an independent figure for that line is supplied (`--independent-checks`);
   - a wrong figure gives FAILED_VALIDATION.
7. **Integrity:**
   - V1 .. V2.4: 747 of 747 files byte-identical;
   - V2.5 deterministic: 254 of 254;
   - freeze verifier, closures and environment lock clean;
   - villa 6 -> 5 rolls (proven minimal); reference plan 14 rolls (proven minimal), 1.77 m2 less membrane consumed;
   - the proof drawing and the generated reports are reproducible byte for byte (a non-deterministic DXF write was
     found and fixed in the test helper).

## What is not working / not done

1. Real drawings have **no line-level independent figures**: their lines are ENGINE_TESTED_ONLY at best.
2. **Door feasibility** still rests on an inferred structure and a 0.10 m engine pier: no structural feasibility is
   claimed.
3. **Proven geometry is rectilinear only.** No case has a column inside a wet area. Lap shingling is not validated.
4. **Corners, penetrations, doorway transitions and open-edge terminations** stay withheld until the owner sets the
   details.
5. **The full test suite is not green** for the known baseline reasons (missing git-ignored datasets).
   - 8165 passed, 345 failed, 32 errors;
   - against the Phase 2B-2 baseline, test by test: 0 new failures, 0 changed, 59 added (all pass);
   - the affected suites with the reference plan: 647 passed, 0 failed.
6. **The formal blind evaluation has not started**, as instructed.

## What I recommend next

1. An independent take-off of 3 - 5 rooms of a real plan, supplied as `--independent-checks`.
2. Bind the structural plan to the door host walls.
3. Owner decisions:
   - N-1: the doorway detail;
   - N-5 / N-6: corner and penetration treatment sizes;
   - N-7: the minimum practical piece;
   - N-8: carrying part rolls between floors.
4. Extend the proof library: a non-rectilinear room, an internal column, a drawn exterior plan, and a second reviewer
   for two sheets.
5. Then adopt V2.5 for new runs, and only then start the blind evaluation, gated by the proof library.

## Questions only the owner can answer

N-1 .. N-10 in `OWNER_DECISIONS_OPEN.md`: doorway detail, pier, shower upturn, side vs end lap, corner treatment,
penetration treatment, minimum piece / reusable offcut, carrying part rolls, confirming "fewest seams before least
membrane", open-edge termination.
