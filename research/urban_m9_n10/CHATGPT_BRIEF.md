# Brief for ChatGPT review: Phase N10

**About the engine.** This is the Urban Projects bilingual BOQ / QTO engine for Kuwait villas, covering the architectural route and the route G structural register.

- Prices are out of scope.
- The long-term target is at least 95 % accuracy, proven by independent blind tests. **This phase does not reach it and does not claim it.** No blind test has been run, and none can be until a second villa set exists.

**What this phase added:**

- ARCH_TAKEOFF_V2.9 (opt-in), with V1 – V2.8 byte-identical;
- a separate structural formwork, excavation and rebar-audit tool;
- registry 1.5.0.

**Time.** The program allowed ten hours. About three hours of elapsed work are evidenced by the commit timestamps.

## What worked

1. **Curved openings** (the D-P9-01 / D-P9-02 fix).
   - A jambed gap in a curved wall band is now an opening, closed by arcs on both wall faces. The room ends at its own face.
   - The strip between the face and the glazing is a reveal or sill strip, measured radially. It is never floor.
   - Curved glazing on an unassigned layer is inferred only under three guards.
   - Example 4S: floor 7.507006 → 7.068583 m², the hand truth, VERIFIED by the independent reader.
   - On the real plan, one window was gained and plaster and paint each gained +57.9478 m² of certain quantity, verified to within 0.00001 m².
2. **The zone-bounded room** (D-P9-04).
   - The verifier now unions the reader's faces inside the room and reads zone lines by handle.
   - The V2.6 → V2.7.1 changes went from 32 to **45 of 55 VERIFIED**, with 0 contradicted.
3. **Masonry by thickness.**
   - The panel runs from the section T.O.S. to U/S SLAB. A beam bottom gives a range; with no beam evidence the panel is held at its upper bound.
   - The material is kept separate.
   - Hand truth 43.26 m² / 8.652 m³; range 35.86 – 43.26 m².
   - A finish height or floor-to-floor is never used as a masonry height.
4. **Facade.**
   - The run is the outer cycle of the floor topology, with openings closed on the outer face.
   - A second outline is an RFI, never added. An enclosure (boundary wall) holds the facade.
   - The area runs F.F.L. → next F.F.L., net of each opening's own band.
   - Hand truth: run 15.60 m, net 50.60 m².
   - On the real plan, the outline's plate equals the engine's floor plate on every floor.
5. **Structural formwork from the route G register.**
   - Faces are MEASURED, CONDITIONAL (both alternatives shown, never summed), UPPER_BOUND or HELD.
   - Footings, column bounds and slab soffits equal the synthetic villa's design spec on seeds 3 and 5.
   - Conservation holds against route G's volumes.
6. **Rebar audit.**
   - d²/162 is +0.12 % against 7,850 kg/m³.
   - Every row's derivation is classified; 0 ratios were presented as measured.
7. **No regression.**
   - V1 – V2.8 are byte-identical: 2,170 files.
   - V2.9 is deterministic: 362 files.
   - The freeze check reports 0 differing.
   - The full suite was compared test by test with the baseline (`FULL_SUITE_COMPARISON.md`).
8. **Defects caught before commit.** Three facade and verifier draft defects were fixed before commit: loose-line outlines, the arc parameter in the ring, and an outline spanning all floors.

## What did not work, or is not done

1. **D-N10-01 (contradicted by the reader).** On the 1F, the facade run is +0.16 m (0.25 %): the engine walks the recess of a window the census missed. It was reported, not tolerated away.
2. **D-N10-02.** The reader closes only 0.30 – 2.60 m gaps, so the GF outline leaks through a wide glazed opening and is not independently established.
3. **Real plans carry no bound section levels.** The section sheets exist, but their F.F.L. bands are not bound to plan floors. Masonry, facade area and exterior finish therefore stay **held** on the reference plan.
4. **D-N10-03.** Masonry has no independent reading.
5. **D-N10-04.** Column formwork is an upper bound only, because beam-column adjacency is not in the register.
6. **Formwork and excavation are separate files,** not BOQ workbook lines yet.
7. **Excavation volume is held everywhere real.** It needs NGL, the founding level and the working space.
8. **Roofs, balconies and external works:** not attempted.
9. **The full suite is not green.** The known legacy failures in modules that need private data remain.

## Questions for the reviewer

1. **Facade convention.** Should the facade be measured F.F.L. → F.F.L. (as now), slab top → slab top, or by a stated storey height?
2. **Masonry.** Is "held at the upper bound when no beam evidence" the right default? The alternative is an owner rule, for example "beams over every external wall".
3. **Formwork.** Is the column face upper bound acceptable as a planning figure, provided it is labelled? Or should column formwork stay held until adjacency exists?
4. **Recesses.** Should the facade run close a glazing-lined recess at the face line? That is what the reader does, and it would fix D-N10-01.
5. **Masonry scoring.** Score the panel geometry separately from the block material?

## Recommendations (unapproved)

1. **Highest value: bind the section bands to the plan floors** on the real plan, tests first. Every masonry and facade area, and the room heights, would then come from the drawing instead of facts.
2. **Ask the owner OQ-06 – OQ-13** (beams over walls, materials, facade convention, finish, formwork conventions, excavation levels).
3. **Fix D-N10-01 and D-N10-02** (both small).
4. **Put formwork and excavation into the BOQ workbook** with their states.
5. **Keep the blind protocol sealed** until a second villa exists and the owner authorises a run.
