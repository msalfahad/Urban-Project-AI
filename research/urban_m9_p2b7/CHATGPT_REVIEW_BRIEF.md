# ChatGPT review brief (Phase 2B-7)

**Scope.** ARCH_TAKEOFF_V2.7 is built, opt-in, and frozen nowhere:

- V1 – V2.6 are byte-identical (1240 files, 0 differ, 39 runs).
- Full suite, compared test by test with the Phase 2B-6 end: 147 new tests, none failing; 0 failed → passed.
  - One timing-ratio test failed once. Its module is unchanged, and it passed 10 of 10 re-runs.
  - The suite is not green: the known 345 failures + 32 errors need private data (`TEST_EVIDENCE.md` §3).
- No owner policy was changed.
- No accuracy claim is made, and the blind evaluation has not started.

## What worked

1. **Door openings from jamb evidence.**
   - On the synthetic CROSSING case, every quantity reaches the hand truth.
   - On the private reference plan, one door goes from its 1.023 m wall gap to its 0.80 m jamb span, and seven of the
     eight failing Stage C checks pass.
   - Doors in genuinely wider openings (open side, column, glazed side panel, wall on one face) are kept, with the
     reason named.
2. **The exploded single door.** It is no longer typed WINDOW, and its swing is no longer subtracted from the floor.
   Wardrobe, threshold and mixed-layer adversaries are handled (the mixed layer is refused).
3. **Columns.**
   - Columns drawn turned, or as four LINEs, are found.
   - Drains are never columns.
   - A free-standing single square is refused, not guessed.
4. **Curved walls.** The room polygon follows the arc. The curved band joins the wall run, and on the reference plan
   it equals an independent raw-entity census to 1e-6 (+1.885 m).
5. **Wet rooms.**
   - A basin alone is REVIEW; it never makes a space wet, and never DRY.
   - A W.C. drawn as lines, inside an anonymous block, or named in Arabic or English is read.
   - Adversaries stay REVIEW: oval table, vanity counter, bidet, chair, detached cistern, the basin's own fittings.
6. **The five Section 3 proposals.** Each was validated against an independent ezdxf reader or hand truth:
   - WC shape (accepted as corroboration only);
   - nested door scoping;
   - opening position (1 mm, 12 placements);
   - zero-length repair;
   - per-line provenance (10 drawings: every entity resolves, runs along its room boundary within 1 mm, and leaves
     only the openings uncovered).
7. **No unexplained BOQ change.** A new tool attributes every V2.6 → V2.7 total to a correction record.
   - The villa and its mirror: 0 differences.
   - The reference plan: 95 differences, 0 unexplained.
8. **Stage C.** The five independently read rooms go from 8 failing checks of 66 to 0. That sample alone is not
   called success.

## What did not work, or is still weak

1. **Bugs in my own draft, found by validation on the reference plan before release.**
   - A row of aligned columns lost its COLUMN role. It moved 747 totals, and a too-coarse explainer scope had hidden it.
   - Basins' own tap and waste lines counted as "independent" sanitary evidence.
   - A held strip was given a dry finish.

   All are fixed, with tests. They show that synthetic tests alone were not enough.
2. **The WC shape rule has two known errors** (strict xfails): a round-bowl W.C. is missed, and an armchair drawn with
   a W.C.'s outline is taken for one. It is used only as corroboration, never alone.
3. **Spaces under wet review carry no finish lines at all.** On the reference plan: three hand-wash spaces, 9.35 m2,
   with their plaster (21.37 m2), wall tile, skirting and waterproofing. This is the largest V2.7 change, a reduction
   of the released BOQ, and it is held pending the owner (D-17). Ceiling and plaster are the same in both readings
   and could be released (D-18).
4. **Turned columns are not jambs and not wall cuts** (polygons only).
5. **Lines with no drawn entity.** 10 lines on the reference plan carry none and are recorded NOT_TRACED.
6. **One latent gap.** Fixture ids and insert paths use different forms, so a basin block's own linework is not
   excluded from the WC-shape candidates. It has no effect on any test or on the reference plan (L-P7-03).
7. **Everything real is one plan.** No second villa (D-15). Heights are still synthetic test facts (D-04).

## What I recommend next

1. **Owner answers.**
   - **D-16 (OQ-05):** what the 1.00 / 0.90 m minimum refers to (structural opening, leaf or clear passage), and
     whether a frame allowance applies. Until then, V2.7 shows every reading and a range.
   - **D-17:** the type of the three hand-wash spaces.
   - **D-18:** release the quantities both readings share.
2. **A second real villa with an independent takeoff** (D-15), before any freeze of V2.7 or any accuracy statement.
3. **Next phase, in this order** (`NEXT_PHASE_PLAN.md`):
   1. heights from sections and schedules;
   2. window and glazing areas;
   3. the combined architectural + structural export;
   4. formwork;
   5. roof / balcony / paving;
   6. excavation.

   Each follows the V2.7 pattern: tests with independent truth first, opt-in, an explainer that leaves nothing
   unexplained.
4. **Fix L-P7-03** (map fixture ids to insert paths) and decide D-07 (curved run basis).

## Questions for the reviewer

1. Is "basin + an independent drawn WC" the right threshold for typing a space wet? Should a WC block alone remain
   sufficient (V2.6 rule kept)?
2. Should a REVIEW space release ceiling and plaster now (D-18), or hold everything until classified?
3. Is the location-level scope of the difference explainer strict enough, given that floor-wide records are not used
   on the reference plan?
4. For P4 formwork, which method of measurement should the proposals be checked against?
