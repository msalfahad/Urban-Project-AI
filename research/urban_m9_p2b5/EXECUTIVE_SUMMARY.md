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
   - **Failures:** 11 of 66 checks. All come from opening recognition and doorway-strip attribution, not from areas
     or rules.
3. **The largest real error, fixed in V2.6 (D-V26-06).** A door drawn two ways at one opening was split between the
   room model (a passage) and the door schedule (a 0.80 m door). V2.6 reconciles it as one door, held for review. On
   the real plan exactly one opening changes:
   - the door count is right;
   - that room's plaster error falls from −0.94 to −0.15 m2;
   - 11 → 10 failing checks.

   The first version of the rule was wrong (it merged two real rooms). The independent reader caught it and a guard
   was added before commit.
4. **Room-reader benchmark (Stage D).** Sixteen synthetic plans with hand truth cover every CAD feature the program
   listed:
   - nested, mirrored and non-uniformly scaled blocks;
   - metres, polylines, arcs, Arabic labels, dimensions;
   - window blocks and an XREF.

   The engine is exact on all straight-walled plans and refuses the XREF. Two engine defects were found and are
   asserted in tests:
   - **D-D1:** a layer drawn once is not recognised.
   - **D-D2:** an arc-walled room is kept on its chord, so its layouts and wall run are wrong while its area is right.
5. **CAD MCPs and skills.** No CAD MCP is connected in this session, so none could be benchmarked; the slot is ready.
   Six repository-local Urban skills were written and tested. The synced third-party skills were reviewed: none is a
   rule source.
6. **Floor-plan AI (Stages E / F).** No reviewed trained model is cleared for commercial use on drawings: CubiCasa5K
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
follows Urban's drawing conventions. Wall-area lines rest on synthetic heights.

## Decisions waiting for the owner

The waterproofing junction detail; wet-room skirting under part-height tile; the scope of a doorless lobby; project
heights; bathroom door enlargement; the PyMuPDF licence (`OWNER_DECISIONS.md`).

## Next

In order of expected gain (`ROADMAP.md`):

1. doorway-strip attribution at splayed walls;
2. arc-aware rooms and curved wall bands;
3. the width of the two-way door;
4. a layer-role pre-flight;
5. heights from sections.
