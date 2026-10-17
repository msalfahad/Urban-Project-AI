# BOQ quantity impact of the geometry work (Phase 2B-5 Stage G)

**What this page shows.** For each geometry or recognition change or defect: which BOQ lines it moves, by how much
(synthetic: exact; reference plan: aggregates only), and whether the change is released, held or open. Nothing here
changes a frozen method. All changes are in the opt-in ARCH_TAKEOFF_V2.6.

## 1. Changes made in this program

| change | BOQ lines moved | synthetic evidence | reference plan (aggregate) | release state |
|---|---|---|---|---|
| V2.6 waterproofing installation layer (Stage B, D-V26-01 - 05) | **none by design**: the installed / procurement figures of V2.5 are kept byte for byte. V2.6 adds the piece plan, junction alternatives, joints, seams and lay order, and marks the procurement provisional while the floor-to-wall junction is open | 10 worked examples, 297 / 297 checks | 17 waterproofed areas computed. Junction UNRESOLVED; 4 shaped trims at splayed walls | provisional (junction detail is an owner decision) |
| D-V26-06 door symbol reconciliation (Stage D) | the door's own lines only: the passage becomes a DOOR (held, not released); its doorway strip moves from floor porcelain to a marble threshold; door jamb plaster is added; the passage line goes; its doorway waterproofing piece is PROVISIONAL | B01 variants: a hinge 0.35 m off its jamb, or a 0.69 m leaf in a 1.00 m gap, becomes a held door. Doorway waterproofing = width x 0.20 m, PROVISIONAL; threshold PROVISIONAL; floor unchanged (12.00 m2) | one opening reconciled. Floor porcelain −0.15 m2 and marble threshold +0.15 m2 (floor area conserved); jamb plaster +0.81 m2 (PROVISIONAL); passages 9 → 8; 0.15 m2 of doorway waterproofing SOURCE_DERIVED → PROVISIONAL | door held (DOOR_SYMBOL_FIT_REVIEW); threshold, plaster and doorway waterproofing PROVISIONAL |
| D-V26-07 doorway strips split at the opening boxes (Stage G) | doorway lines only: a withheld threshold strip becomes the door's own threshold (marble / porcelain by UP-THR-001) plus a wall remainder with no quantity; a leaf-closed door's doorway waterproofing becomes the box between its closures | B01 with the real plan's pattern: V2.5 withholds a 0.2054 m2 face; V2.6 takes 0.16 m2 (0.80 x 0.20) and leaves 0.0454 m2 of wall. Leaf-closed variant: doorway waterproofing 0.2054 → 0.16 m2 (V2.5 over by 28 %) | marble thresholds +0.48 m2 (4 doorways); doorway-strip porcelain +0.135 m2 (1); doorway waterproofing −0.0715 m2 (2 leaf-closed pieces); 0.14 m2 of wall left as 4 RFI strips; floor areas, rooms and coverage unchanged | as each doorway's rule gives (SOURCE_DERIVED on the plan); the remainder BLOCKED_RFI |

Effect on the independent real-room checks (`REAL_ROOM_VERIFICATION.md` §7 - §8):

| | failing checks of 66 | thresholds passing | sample threshold area |
|---|---|---|---|
| V2.5 | 11 | 2 of 5 | −49 % (withheld) |
| V2.6 with D-V26-06 | 10 | 2 of 5 | −28 % |
| V2.6 with D-V26-06 and D-V26-07 | **8** | **4 of 5** | **+4.5 %** |

In the room of the two-way door: the door count is right, the plaster error is −0.94 → −0.15 m2 and the wall porcelain
error −0.42 → −0.15 m2. What remains there is the door's width: 1.023 m jamb to jamb against its symbol's 0.80 m, a
question the drawing answers (§8) and the engine does not yet apply.

Whole reference plan, V2.5 → V2.6 (the two corrections together; Mode A, synthetic heights):

| line family | change |
|---|---|
| FIN.MARBLE.THRESHOLD | +0.63 m2 (5 lines more) |
| FIN.FLOOR.PORCELAIN | +0.135 m2 SOURCE_DERIVED, −0.15 m2 PROVISIONAL (one strip became a threshold) |
| FIN.WP.DOORWAY | −0.22 m2 SOURCE_DERIVED, of which 0.15 m2 moved to PROVISIONAL (the held door) and 0.07 m2 removed (the wall in two leaf-closed pieces) |
| FIN.PLASTER, FIN.WALL.TILE | +1.57 / +0.52 m2 SOURCE_DERIVED and +0.78 m2 PROVISIONAL (door instead of a full-height passage deduction; door jamb plaster) |
| ARCH.PASSAGE | 9 → 8 |
| room floor, ceiling, waterproofing floor | unchanged |

## 2. Defects found and not fixed in this program (exposure)

| defect | BOQ lines exposed | size of the exposure | state |
|---|---|---|---|
| D-C1 residual: the held two-way door's width | the door's wall deductions (plaster, wall porcelain, skirting, upturn), its doorway waterproofing and threshold | sample: R-C's seven remaining failed checks (plaster −0.15 m2, wall porcelain −0.15 m2, threshold / doorway waterproofing +0.034 m2 each) | settled by the drawing (§8); roadmap 1 |
| D-C2 residual: leaf-closed doorways | thresholds withheld at doors closed by their leaf (the opening itself is not established); two leaf-closed pieces refused (an irregular face, a column) | 5 leaf-closed doorway faces on the plan; two doorway waterproofing pieces still take their whole face (one irregular face of 0.22 m2; one with a column, 0.012 m2 beyond its 0.80 m jambs) | open, flagged |
| D-C3 a doorless lobby merged into a wet room without a note | the wet scope of the lobby: waterproofing, full-height porcelain | sample: the lobby is 44 % of its room's area | owner scope decision |
| D-C4 skirting rule conflict (UP-CER-004 exception against the program's statement) | skirting in wet rooms with a 2.40 m tile below a 3.00 m finish | sample: about 41 lm | owner decision |
| D-C5 synthetic heights | every wall-area line (plaster, wall porcelain, paint, masonry) | all; door height 2.10 m used where the owner reference is 2.20 m | project values needed |
| D-D2 arc-walled room kept on its chord | membrane and tile layouts (procurement), the wall run, masonry and plaster by run | synthetic B10: layout planned for 12.00 m2 of a 13.02 m2 floor (the segment unplanned); wall run 11.0 / 10.2 lm against 14.22 / 13.42 lm (−23 %). Reference plan: 4 of 38 rooms have an arc-bounded face (all dry; Σ\|Δ\| 5.1 m2 of layout geometry); curved wall about 0.7 % of the wall run | asserted as found; roadmap 2 |
| D-D1 layer roles inferred from one instance | doors, windows (as passages: door lines, thresholds, doorway waterproofing missing); a column (not deducted: floor / ceiling +) | synthetic B04: +2.18 % floor. Single-door drawings: every door / window typed PASSAGE | remedy available (`--layer-roles`); not seen on the reference plan (many doors) |
| basin lobby typed wet from its fixtures | the lobby's own wet scope and which room carries a shared doorway piece | one lobby on the plan; R-E's one failing check | owner scope decision (11) |

Area-based lines are exact in every synthetic case and in all five verified real rooms: floor, ceiling and
waterproofing floor. The exposure sits in **recognition** (which opening is a door), **attribution** (which strip
belongs to which doorway), **opening width** and **layout geometry** (arcs). It does not sit in area arithmetic.

## 3. Vision and the BOQ

**Zero.** No quantity in any method comes from the raster or PDF prototypes. In the benchmark the vector PDF agrees
with CAD exactly. A clean raster agrees within 0.75 % on area, and a degraded scan never better than review. The
hybrid records keep the CAD value as the only BOQ basis (`FLOORPLAN_AI_RESEARCH.md` §5).

## 4. What would move the BOQ most, next

The ranking is by expected accuracy gain, in detail in `ROADMAP.md`:

1. the held door's width from its symbol's jamb lines (the D-C1 residual, now settled by the drawing);
2. arc-aware room polygons and curved wall bands (D-D2);
3. a scale / unit / layer-role pre-flight that refuses single-instance role inference (D-D1);
4. project heights instead of synthetic ones (D-C5, an input);
5. the owner decisions D-C3 / D-C4 / the basin lobby and the junction detail.
