# Brief for ChatGPT - V2.5 waterproofing constructability review (Phase 2B-4)

Context: the owner asked for an independent construction audit of the V2.5 waterproofing cutting plans before the
Floorplan AI research starts. The question was whether the mathematically optimised plan is a buildable installation.
Three synthetic rooms were audited. V1 - V2.5 are frozen and nothing in the engine was changed.

## What worked

1. **An independent construction calculator** (stdlib, integer mm, no engine import) rebuilds each plan piece by
   piece. It checks fit, coverage on a 10 mm grid, laps and the material balance, and lists every lap, junction,
   corner, doorway and penetration condition separately.
2. **All V2.5 quantities of the three rooms were reproduced exactly:**
   - WP-B: 17.80 m2 / 2 rolls;
   - WP-E: 16.54 m2 / 2 rolls;
   - WP-D: 13.80 m2 / 2 rolls.

   The arithmetic is right for the plan V2.5 models.
3. **The 3 x 4 m bathroom is shown under both buildable floor-to-wall junction methods**, each piece with size, source
   roll, rips and destination:
   - separate upstand: 17.80 m2 / 2 rolls with a 0.10 m flange, up to 3 rolls from a 0.16 m flange;
   - continuous fold: 17.60 m2 / 2 rolls / 3 seams.
4. **Nothing unapproved is counted as complete.** Corners, jamb junctions, thresholds and the pipe collar stay
   withheld, with their counts and limits. The pipe sleeve takes a collar up to 0.60 m clear of the seams.
5. **Corrected diagrams:** 14 installation plans with numbered pieces, joints, corners, jambs and seam ends, 14 cutting
   plans with every rip and cross-cut, and a junction section sheet.
6. **The calculator caught two errors in my own hand work** (H-A1, H-A2). Both were re-derived by hand.

## What is not working

1. **The floor-to-wall junction is an assumption.** V2.5 laps the upturn onto the floor with the 0.10 m joint lap of
   UP-WP-002 and never lists the junction as an open detail (F-01).
2. **The cutting record cannot be cut from.** It has no rips, lanes, piece ids, destinations or joint positions, and
   the L-shape's step offcut is recorded as a shape that does not exist (F-02).
3. **Joint placement is unchecked** (F-03):
   - WP-B: two joints sit on floor-seam ends;
   - WP-E: one joint ends 0.02 m from a corner;
   - WP-D: one piece starts on a corner.

   Rearranging the same pieces improves this to 0.30 / 0.14 / 0.10 m.
4. **V2.5's roll-sensitivity claim covers doorways only.** A wider junction flange can add a roll (F-09).
5. **The selection order is applied only between strip directions** (F-10). Applied to the band plan, fewer joints
   cost 0.26 - 2.80 m2 more membrane. The owner must set the scope.

## What I recommend next

1. Keep the waterproofing material figures CONDITIONAL on the junction detail.
2. Get the membrane system's data sheet: the junction method and flange, foldability, end lap, corner pieces, collar,
   joint offset and minimum piece.
3. Owner decisions: N-11 (junction method), N-12 (joint offset), N-13 (multi-layer points), and N-9 extended (scope of
   the selection order).
4. If authorised, implement the opt-in ARCH_TAKEOFF_V2.6 per `PATCH_PROPOSAL_V2_6.md`. That means the junction as an
   open detail with alternatives, a piece-level cutting plan, joint placement checks and offcut classes. The
   acceptance set is this audit's 31 tests, plus V1 - V2.5 byte identity.
5. Then start the Floorplan AI, MCP and skills research program.
