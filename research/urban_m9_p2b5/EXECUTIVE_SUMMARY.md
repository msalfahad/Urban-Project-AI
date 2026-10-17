# Executive summary: overnight engineering program (Phase 2B-5)

**What it set out to do.** Find the largest remaining sources of measurement error and fix them where it is safe.
Prove each result against independent numbers. Research floor-plan AI, CAD MCPs and skills. Keep every frozen method
unchanged and every private drawing private.

## What was done

1. **Waterproofing constructability (Stage B).** The opt-in ARCH_TAKEOFF_V2.6 adds the plan the engine actually cuts:
   - every piece, joint, seam and offcut;
   - corners, penetrations and drains;
   - the open floor-to-wall junction with its alternatives.

   Ten worked examples pass 297 of 297 independent checks. No BOQ quantity changed by design, and procurement stays
   provisional until the owner chooses the junction detail.
2. **Real rooms (Stage C).** Five rooms of the private reference plan were measured independently of the engine.
   - **Floor, ceiling, perimeter and windows:** exact in every room.
   - **Failures:** 11 of 66 checks under V2.5. All come from opening recognition and doorway attribution, not from
     areas or rules.
3. **Error 1, fixed in V2.6 (D-V26-06): a door drawn two ways.** At one opening the room model read a passage while
   the door schedule held a 0.80 m door. V2.6 reconciles it as one door, held for review, and its doorway lines are
   provisional. The door count is now right, that room's plaster error falls from −0.94 to −0.15 m2, and the failed
   checks go from 11 to 10.

   The first version of the rule was wrong (it merged two real rooms). The independent reader caught it and a guard
   was added before commit.
4. **Error 2, fixed in V2.6 (D-V26-07): doorway strips that run on past the jamb.** The largest measured error in the
   sample was the withheld thresholds: −49 % of the sample's threshold area. The cause, read from the raw drawing:
   - the jamb is drawn only with the door symbol;
   - the wall piece beside it is too short to seal the wall body;
   - so the doorway face runs on into a wall junction.

   V2.6 splits such a face at the door's box only when the face's own edges prove the reading. The same proof bounds
   the doorway waterproofing of a leaf-closed door, which V2.5 over-measures (+28 % on the synthetic case). On the real
   plan:
   - 5 doorways get their threshold;
   - 2 doorway waterproofing pieces lose 0.07 m2 of wall;
   - 8 faces / pieces are refused, with reasons.

   A raw-line reading confirms every box (0.80 / 0.90 m between the symbol's jamb lines). In the sample, thresholds go
   from 2 of 5 to 4 of 5 passing, and the failed checks from 10 to **8 of 66**.
5. **Room-reader benchmark (Stage D).** Sixteen synthetic plans with hand truth cover every CAD feature the program
   listed:
   - nested, mirrored and non-uniformly scaled blocks;
   - metres, polylines, arcs, Arabic labels, dimensions;
   - window blocks and an XREF.

   The engine is exact on all straight-walled plans and refuses the XREF. Two engine defects were found and are
   asserted in tests:
   - **D-D1:** a layer drawn once is not recognised.
   - **D-D2:** an arc-walled room is kept on its chord, so its layouts and wall run are wrong while its area is right.
6. **CAD MCPs and skills.** No CAD MCP is connected in this session, so none could be benchmarked; the slot is ready.
   Six repository-local Urban skills were written and tested. The synced third-party skills were reviewed: none is a
   rule source.
7. **Floor-plan AI (Stages E / F).** No reviewed trained model is cleared for commercial use on drawings: CubiCasa5K
   is CC BY-NC, RoomFormer's data is non-commercial, HEAT is GPL non-commercial. A deterministic prototype gives:

   | input | result |
   |---|---|
   | vector PDF | exact |
   | clean raster | within 0.75 % on area |
   | degraded scan | review-level only (4.1 %, spurious openings, a word read as a wall) |

   Vision never makes a BOQ quantity.

## Evidence that nothing was broken

- V1 - V2.5 outputs are byte-identical on three drawings: 968 files, 0 differ.
- The freeze verifier reports 0 frozen artefacts differing; the environment is in lock.
- The full suite was compared with the Stage A baseline by test identity (`TEST_RUN.md`).
- The privacy scan is clean; no private drawing, room id or client name is in any committed file.

## What it does not show

There is no accuracy figure: the formal blind evaluation was not started, as instructed. The synthetic benchmark
follows Urban's drawing conventions. Wall-area lines rest on synthetic heights. Both V2.6 corrections were proven on
one real plan; a second plan is needed before trusting them widely.

## What is left in the sample

Of the 8 failed checks, 7 are in one room and come from the held two-way door's width. The drawing already answers it
(0.80 m between its symbol's jambs); the engine does not yet apply it. The last one is attribution: a doorway piece is
carried by a basin lobby the engine types wet.

## Decisions waiting for the owner

- the waterproofing junction detail;
- wet-room skirting under part-height tile;
- the scope of a doorless lobby, and whether a basin lobby is wet;
- project heights;
- bathroom door enlargement;
- the PyMuPDF licence.

See `OWNER_DECISIONS.md`.

## Next

In order of expected gain (`ROADMAP.md`):

1. the held door's width from its symbol's jamb lines;
2. arc-aware rooms and curved wall bands;
3. a layer-role pre-flight;
4. heights from sections;
5. thresholds of leaf-closed doors.
