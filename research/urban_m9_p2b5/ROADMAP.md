# Development roadmap, ranked by expected accuracy improvement (Phase 2B-5)

The ranking uses measured exposure: the five real rooms of Stage C (66 independent checks), the whole-plan
aggregates and the synthetic benchmark. Every item is an opt-in method step behind its own flag; frozen methods
stay as they are. V2.6 already carries D-V26-06 (door symbol reconciliation) and D-V26-07 (doorway strips split at
the opening boxes); the steps below belong in V2.7 once V2.6 is frozen as a whole.

| rank | work | why (measured) | BOQ families | proof needed |
|---|---|---|---|---|
| 1 | **the held door's width from its symbol's jamb lines** (D-C1 residual): narrow the band opening to the door symbol's jamb span and close the rest of the gap as wall in the face partition | 7 of the 8 remaining failed checks in the sample (one room); the raw reading already gives the answer (0.80 m of a 1.023 m gap, the rest a 73 mm return and a wall crossing) | plaster, wall porcelain, skirting, upturn, doorway waterproofing, threshold of that door | the room's seven checks to zero difference; synthetic two-way doors with a wall crossing beside them; V1 - V2.6 byte identity |
| 2 | **arc-aware room polygons and curved wall bands** (D-D2) | synthetic arc room: wall run −23 %, layout on the chord (1.02 m2 of 13.02 unplanned); reference plan: 4 of 38 rooms, ~0.7 % of the wall run | layouts (membrane, tiles), ARCH.WALL_RUN, masonry, plaster by run | B10 truth (`test_p2b5_curved_wall.py` turns from "as found" to the truth); concentric-arc wall bands on synthetic plans |
| 3 | **layer-role pre-flight** (D-D1): flag or refuse single-instance role inference; ask for `--layer-roles` | every door / window on a single-room sheet typed PASSAGE; a column not deducted (+2.18 % floor) | doors, thresholds, doorway waterproofing, floor / ceiling | benchmark single-door cases flip to exact without declared roles, or refuse |
| 4 | **heights from sections / schedules** (D-C5) | every wall-area line rests on heights; the test heights are synthetic | plaster, wall porcelain, paint, masonry | a section reader verified on synthetic sections; the owner's project heights |
| 5 | **leaf-closed doorways** (D-C2 residual): establish the opening of a door closed by its leaf from its symbol's jamb lines, so its threshold is measured; the irregular / column-bounded doorway pieces | 5 leaf-closed doorway faces on the plan, their thresholds withheld; 2 doorway pieces still take their whole face | thresholds, doorway waterproofing | the raw jamb reading already used in §8, synthetic leaf-closed doors with returns and columns |
| 6 | **attachment note for doorless cells merged into a wet room** (D-C3) | 44 % of one sample room takes the wet scope silently | wet scope (waterproofing, porcelain) | the cell flagged; owner decision 3 |
| 7 | waterproofing junction detail released (owner decision 1) | procurement now PROVISIONAL; one roll more at a 0.16 m flange | procurement rolls | Phase 2B-4 / 2B-5 examples re-run with the chosen detail |
| 8 | vector-PDF cross-check for PDF-only sets (after the licence decision) | exact on the benchmark; independent of CAD | none directly (a check) | a DXF / PDF pair of a real plan, privately |
| 9 | raster review aids: text-to-wall separation, rotation-aware gap closing | scan B09 spur (+23 % perimeter), B06 spurious gaps | none (review only) | benchmark |
| 10 | the formal blind evaluation (not started, as instructed) | the only basis for any accuracy claim | all | the owner's protocol |

Done in this program, from the earlier ranking: doorway-strip attribution at a jamb drawn only with the door symbol
(was rank 1; D-V26-07: thresholds in the sample 2 → 4 of 5, failed checks 10 → 8), and the door drawn two ways
(D-V26-06: 11 → 10).
