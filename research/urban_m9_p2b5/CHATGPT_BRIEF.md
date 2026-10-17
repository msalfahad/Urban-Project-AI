# Brief for ChatGPT - overnight engineering program (Phase 2B-5)

Context: the owner asked for an autonomous overnight program on Urban's architectural takeoff. It had six aims:

- find the largest remaining measurement errors and fix them where it is safe;
- prove every number independently;
- research floor-plan AI, CAD MCPs and skills;
- keep V1 - V2.5 frozen;
- keep the private reference plan private;
- not start the blind evaluation.

All new behaviour is in the opt-in method ARCH_TAKEOFF_V2.6.

## What worked

1. **Two real measurement errors found and fixed, each proven independently.**
   - **D-V26-06, a door drawn two ways at one opening.** The room model read a passage, the door schedule a 0.80 m
     door. V2.6 reconciles them as one held door.
   - **D-V26-07, doorway strips running on past the jamb.** The jamb was drawn only with the door symbol; the wall
     piece beside it is under the band census's 100 mm minimum, so no wall cap seals the wall body, and the doorway
     face runs into a wall junction. V2.5 withholds the threshold, and for a leaf-closed door over-measures the doorway
     waterproofing (+28 % on the synthetic case). V2.6 splits the face at the door's box, only when the face's own
     edges prove the reading.

   On the real plan (aggregates):
   - 5 doorways get their threshold;
   - 2 doorway waterproofing pieces lose their wall;
   - 8 faces / pieces are refused, with reasons;
   - a raw-line jamb reading (ezdxf, not the engine's reader) confirms every box: 0.80 / 0.90 m between the door
     symbol's own jamb lines, remainders to 0.1 mm.
2. **Five real rooms checked against an independent reading: 66 checks.**

   | method | failing checks |
   |---|---|
   | V2.5 | 11 |
   | V2.6 with D-V26-06 | 10 |
   | V2.6 with D-V26-07 | **8** |

   Floor, ceiling, perimeter and windows are exact in every room. Thresholds pass in 4 of 5 doorways (2 under V2.5).
   The sample's threshold area goes from −49 % (withheld) to +4.5 %.
3. **The waterproofing construction layer (Stage B)** turns the V2.5 cutting record into a plan that can be cut and
   laid:
   - pieces, offcuts, joints, seams, corners, penetrations and drains;
   - the open floor-to-wall junction with its alternatives.

   297 / 297 independent checks over ten worked examples. No BOQ quantity changed by design.
4. **A room-reader benchmark with hand-derived truth**: 16 synthetic plans, including nested / mirrored /
   non-uniform blocks, metres, polylines, arcs, Arabic text, DIMENSIONs, window blocks and an XREF.
   - The engine is exact on every straight-walled plan and refuses the XREF.
   - It exposed D-D1 (a layer drawn once is not recognised) and D-D2 (an arc room is kept on its chord).
5. **Frozen methods untouched**: V1 - V2.5 byte-identical on three drawings (968 files); freeze verifier 0
   differing; the full suite compared with the Stage A baseline by test identity (`TEST_RUN.md`).
6. **The independent reader earned its place.** It caught the first D-V26-06 version merging two real rooms. The tests
   caught a loose tolerance in D-V26-07. The raw geometry showed that the first explanation ("the jamb is not drawn")
   was wrong.

## What is not working

1. **The held two-way door still takes the wall gap's width** (1.023 m) instead of its symbol's (0.80 m). This is 7
   of the 8 remaining failures, all in one room. The drawing settles it: the symbol's jamb lines are 0.80 m apart,
   and the rest of the gap is a 73 mm return plus a wall crossing. Applying it means closing the remainder inside the
   face partition, which changes the room boundary; it was not done.
2. **Leaf-closed doors**: their thresholds stay withheld (the opening is not established). Two doorway waterproofing
   pieces are still the whole face (an irregular face, a column).
3. **Arc-walled rooms (D-D2)**: area right, but layouts and the wall run are on the chord (−23 % wall run on the
   synthetic room; ~0.7 % of the real plan's wall run).
4. **Single-instance layers (D-D1)**: a door or column layer drawn once is not recognised without `--layer-roles`.
5. **No accuracy figure**: the blind evaluation was not started (instruction). Both V2.6 corrections are proven on one
   real plan only. Wall-area lines rest on synthetic heights.
6. **No CAD MCP is connected**, so none could be benchmarked.

## Answers to the program's questions

| question | answer |
|---|---|
| implemented | V2.6: the waterproofing construction layer, D-V26-06, D-V26-07 (with the held door's doorway waterproofing provisional); the benchmark, the vision prototype and the hybrid reconciliation (test tree only); six Urban skills |
| only researched | floor-plan AI models (CubiCasa5K, RoomFormer, HEAT, Floor-SP, Raster-to-Vector, DeepFloorplan); CAD MCP servers (none connected) |
| independently verified | the ten waterproofing examples (297 checks); 66 real-room checks; every D-V26-07 box by a raw-line jamb reading; the benchmark against hand truth; V1 - V2.5 byte identity |
| provisional | waterproofing procurement (junction detail open); the held door and its threshold, plaster and doorway waterproofing; pantry / external thresholds by rule; heights (synthetic) |
| failed | 8 of 66 real-room checks (7: the held door's width; 1: a doorway piece carried by a basin lobby the engine types wet); raster labels 8 / 12, scans review-level only |
| corrected | C-01 - C-08 in `DEFECTS_AND_CORRECTIONS.md` (a typed total, an overstated defect, an engine plan misattributed, a scoring fault, a missing-line claim, an "owner decision" the drawing settles) |
| tests run | `tests/m9_p2b5` + `tests/m9_p2b5_bench`: 182 passed. The full suite (9017 tests) against the Stage A baseline by test identity: 182 new tests all pass, 0 changed state; the 345 failed + 32 errors are the unchanged baseline set (git-ignored private datasets). Freeze verifier 0 differing; V1 - V2.5 byte identity (`TEST_RUN.md`) |
| real quantities verified | five rooms: floor, ceiling, perimeter, skirting, plaster, wall porcelain, waterproofing floor / upturn / doorway, doors, windows, thresholds; six doorway boxes from raw lines |
| did computer vision help | as a cross-check, yes (the vector PDF is exact); as a measurement, no (a clean raster within 0.75 % on area, a degraded scan review-only). It found none of the engine's defects; CAD-level checks did. It never makes a BOQ quantity |
| useful MCPs / skills | no CAD MCP available. GitHub and the local toolchain (ezdxf, shapely, Tesseract) did the work. The six repository skills now encode the BOQ verification chain (`urban-boq-proof`), the CAD audit, rule reconciliation, freeze integrity, the MCP benchmark and floor-plan vision review; the synced third-party skills are not rule sources |

## What I recommend next

1. **Apply the held door's width from its symbol's jamb lines** (V2.7). Narrow the band opening to the symbol's jamb
   span and close the remainder as wall in the face partition. The acceptance test is the room's seven checks going
   to zero difference, with V1 - V2.6 byte identity.
2. **Arc-aware room polygons and curved wall bands** (D-D2), against the benchmark's B10 truth.
3. **A layer-role pre-flight** that refuses single-instance role inference or asks for `--layer-roles` (D-D1).
4. **Project heights** from sections or schedules, or the owner's values (D-C5).
5. **Owner decisions** (`OWNER_DECISIONS.md`):
   - the waterproofing junction detail;
   - wet-room skirting under part-height tile;
   - the doorless-lobby and basin-lobby scopes;
   - bathroom door enlargement;
   - the PyMuPDF licence.
6. **A second real plan**, verified the same way, before trusting D-V26-06 / 07 widely. Then freeze V2.6 as a whole.
7. **The formal blind evaluation**, when the owner starts it: the only basis for an accuracy claim.
