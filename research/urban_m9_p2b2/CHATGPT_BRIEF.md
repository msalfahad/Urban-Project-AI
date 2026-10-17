# Brief for ChatGPT - Phase 2B-2 (ARCH_TAKEOFF_V2.4)

Context: the Urban Project AI BOQ engine (Python, stdlib engine, DXF architectural route). This phase implemented the
owner program "master engineering rules, waterproofing optimization and door feasibility" as a new opt-in method,
ARCH_TAKEOFF_V2.4, on top of the frozen V2.3. Reference-plan figures below are aggregates; the synthetic villa is a
generated test drawing.

## What worked

1. **Two rule levels with a hash.** Urban standards (registry 1.1.0) and project rules (a JSON per project, scoped by
   project / location type / door category / floor / room / wall / opening) resolve per element; same-rank
   disagreements become CONFLICT_REVIEW with both values kept and nothing applied. A 15-section Project Engineering
   Rules Sheet is produced before the BOQ; its `rules_sha256` is in every output, and a changed sheet moves the earlier
   outputs to SUPERSEDED_n.
2. **Waterproofing as a material system.** The wall upturn is now the eligible wall boundary x 0.20 m (doorways
   excluded and modelled as transitions with three alternatives, withheld without a detail). Three quantities are
   kept apart: A net, B installed, C rolls from a deterministic cutting plan per membrane system (two orientations per
   area, first-fit decreasing across areas). Penetrations not drawn are NOT_SHOWN (count None, never 0). A roll count
   is CONFIRMED only with a specified system and no withheld detail.
   - Villa: upturn 7.84 -> 7.34 m2; 6 rolls for 3 areas (7 if each alone).
   - Reference plan: upturn 28.945 -> 25.085 m2; 14 rolls for 17 areas (19 if alone); 14 is the area lower bound.
3. **Door feasibility.** Per door:
   - CAD opening, required opening, max nominal door as drawn, enlargement;
   - clearances to columns / openings / junctions / corners;
   - placements, a swing check, the host-wall structure state;
   - one of five classes, four views never summed, and an approvals list.

   Jamb plaster uses each category's height; a main-entrance candidate is a 2.20 .. 2.50 m range.
4. **Nothing frozen moved.** V1 .. V2.3 outputs were byte-identical on 505 of 505 files across 3 drawings and 2 modes.
   V2.4 is deterministic (242 of 242 files identical across two runs). Freeze verifier, closures and the environment
   lock are all clean.
5. **Tests found real defects.**
   - A metamorphic door test exposed a wrong mirror in the synthetic generator.
   - The reference-plan run exposed window frame lines read as floor-level glazing: 33 false terminations and 10
     false reviews.
   - Both are fixed with failing-first tests (63 new tests).

## What is not working / not done

1. **Host-wall structure is inferred, not read.** A drawn column frame gives MASONRY_INDICATED; a floor with no frame
   gives UNKNOWN. The structural plan is not bound to the architectural doors.
2. **Penetrations.** The reference plan draws no drains, so every wet area is NOT_SHOWN. No plumbing drawing is read.
3. **Window thresholds** are upturned assuming a sill wall. A floor-level window would be wrong until the window type is
   known.
4. **No default doorway detail.** Every wet-to-dry doorway stays an open item (15 on the reference plan).
5. **Laps** are counted but not oriented (no shingle order towards the drain).
6. **Project rules files** are not tied to the drawing hash.
7. **Exterior waterproofing** (balcony / roof) is proved only on synthetic plans.
8. **The full test suite is not green** for the reasons already known (missing git-ignored datasets). See
   TEST_RESULTS.md for the counts against the baseline.
9. **Formal blind testing** has not started.

## What I recommend next (in order)

1. Bind the structural plan (route G already reads walls and columns) to classify door host walls.
2. Ask the owner for an Urban default doorway waterproofing detail, and use a project membrane data sheet to confirm
   roll counts.
3. Read the drainage / plumbing drawing for penetrations.
4. Make the window-threshold upturn PROVISIONAL until the window schedule says "sill" (a V2.5 opt-in).
5. Require the drawing sha256 in the project rules file.
6. Validate on a second and a third real plan, including a roof / balcony plan, then run the blind test.

## Questions only the owner can answer

| # | Question |
|---|---|
| N-1 | An Urban default doorway waterproofing detail? |
| N-2 | The minimum pier beside an enlarged door opening? The engine uses a 0.10 m review threshold. |
| N-3 | A shower upturn rule? |
| N-4 | Side and end laps both 0.10 m? |

Still open from earlier phases: OQ-02, OQ-03, OQ-04.
