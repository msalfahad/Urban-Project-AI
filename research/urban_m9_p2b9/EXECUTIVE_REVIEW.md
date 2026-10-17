# Executive review — Phase 2B-9

## 1. Bottom line

ARCH_TAKEOFF_V2.8 (opt-in, registry 1.4.0) now does five new things:

1. **Reads wall-finish heights from the drawing**, using one evidence hierarchy, each trade at its own height, and a
   missing-evidence report.
2. **Builds an opening schedule.** Height, sill, head and class per opening; each opening is deducted by its own
   band; floor glazing is not skirted; an unknown sill becomes a range; a window without a height holds its area.
3. **Measures window reveals and sills** from the actual geometry.
4. **Measures short returns and curved wall stubs** as wall.
5. **Keeps curved-wall faces apart.**

Every rule was proven first on a worked example with hand arithmetic (examples 1–4), then on regression and
transformation tests, then on the whole villa.

**On the real reference plan, V2.8 changes one BOQ quantity: +0.16854 m of wall run, independently verified.** The
plan carries no schedule, no section bound to a floor and no height notes, so the new height and opening logic has
nothing to read there. The engine lists exactly what is missing (138 items in Mode A) and invents nothing.

No accuracy is claimed, no blind evaluation was started and nothing was frozen for production.

## 2. Phase 2B-8 review (section 2 of the instruction)

| Item | Finding |
|---|---|
| **The 1,518 frozen files** (V1 – V2.6: 1,240; V2.7: 278) | regenerated at the new tree: **0 differ**. V2.7.1 (308 files) also 0 differ. See `REGRESSION_AND_FROZEN_EVIDENCE.md` |
| **V2.7.1 behaviour** | re-run on the worked examples: plaster 37.65 m² on example 1 with the synthetic facts (window deducted at full height without a sill; door 2.10 m from the facts); window reveal BLOCKED; short returns lost from the wall run; the curved-glazing room lost silently. Each is now an as-found test or a V2.8 correction |
| **The 23 unverified changes** (V2.6 → V2.7.1) | re-run with the current verifier: still **32 / 55 verified, 23 explained-unverified, 0 contradicted**. 13 depend on one zone-bounded space (D-P9-04: when the reader closes it with the drawn zone line, it disagrees by 0.899 m², recorded and not forced); 4 symbol-less gaps; 2 sills; 4 with no independent check yet |
| **The 377 full-suite failures** | compared test by test with the new clean-clone run (see `REGRESSION_AND_FROZEN_EVIDENCE.md` §3) |
| **D-P8-03 (stubs)** | its description was wrong: collinear stubs were already counted; only non-collinear returns and short curved stubs were lost. Corrected and fixed in V2.8 |

## 3. Answers to the closing questions

1. **What new quantities can the engine measure?**
   - Heights per trade from drawing evidence; door heights from schedules.
   - Window height, sill, head, class and area (or held).
   - Each opening's own band deduction.
   - Window reveal plaster (jambs, head soffit) and the sill surface; the floor-glazing strip as floor.
   - Skirting with floor glazing excluded and unknown sills ranged.
   - Short straight returns and curved stubs in the wall run.
   - Inner / centreline / outer arcs of curved walls.
   - Lost room labels reported.
2. **Which were independently verified?**
   - Hand truth: everything in the worked examples (46 tests).
   - The independent reader:
     - the reference plan's stub (+0.16854 m);
     - the synthetic villa's 7 skirting changes per layout;
     - the return census and the stub census on fixtures.
3. **Which remain provisional?**
   - Reveal plaster and door jamb plaster (frame detail).
   - The floor-glazing floor strip.
   - The wall run (material).
   - Ceilings (type).
   - On the reference plan, every wall area, which rests on the stated project facts, not drawing evidence.
4. **Which defects were corrected?**
   - The full-height window deduction (sill clip).
   - Blocked window reveals.
   - Lost returns and curved stubs (D-P8-03, description corrected).
   - Silent room loss, now reported.
   - Skirting at floor glazing / unknown sills (D-P8-06).
   - Synthetic heights where evidence exists (D-04).
   - Before release, three V2.8 draft defects were fixed:
     - a 30.75 m skirting double count;
     - wall-tile height noise in the missing-evidence report;
     - a sill taken from a wrong-width schedule row.
5. **Which BOQ categories are still missing?**
   - Blockwork m² / m³.
   - Facade finishes.
   - Ceiling types and bulkheads.
   - Stair risers, flights and rails.
   - Roof build-up.
   - Screeds.
   - Ironmongery and glazing systems.
   - Formwork, excavation and external works (`BOQ_CAPABILITY_GAP_AUDIT.md`).
6. **How much did the real reference-plan BOQ change?**
   - One line value: ARCH.WALL_RUN 216.7625 → 216.9311 m (+0.16854 m, +0.08 %).
   - The line count is unchanged (487 Mode A / 476 Mode U); no finish quantity changed.
7. **What remains blocked?**
   - By drawings: sections with F.F.L. / F.C.L. / U/S SLAB per floor, and a door / window schedule (or printed
     heights and sills), for the reference plan; a second villa set; an independent QS.
   - By owner decisions: D-16, D-17, the kitchen membrane, the reveal / sill finish, waterproofing details,
     approval of the acceptance framework, and authorisation to freeze and run blind.
8. **What is the highest-value next step?**
   - Obtain one drawing set with sections and a door / window schedule (ideally the second villa).
   - V2.8 is built to read them, and they move every wall-area line from assumed facts to drawing evidence.
   - After that comes D-P9-01 / -02 (curved openings).
