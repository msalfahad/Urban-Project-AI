# BOQ quantity impact of the geometry work (Phase 2B-5 Stage G)

**What this page shows.** For each geometry or recognition change or defect: which BOQ lines it moves, by how much
(synthetic: exact; reference plan: aggregates only), and whether the change is released, held or open. Nothing here
changes a frozen method. All changes are in the opt-in ARCH_TAKEOFF_V2.6.

## 1. Changes made in this program

| change | BOQ lines moved | synthetic evidence | reference plan (aggregate) | release state |
|---|---|---|---|---|
| V2.6 waterproofing installation layer (Stage B, D-V26-01 - 05) | **none by design**: the installed / procurement figures of V2.5 are kept byte for byte. V2.6 adds the piece plan, junction alternatives, joints, seams and lay order, and marks the procurement provisional while the floor-to-wall junction is open | 10 worked examples, 297 / 297 checks | 17 waterproofed areas computed. Junction UNRESOLVED; 4 shaped trims at splayed walls | provisional (junction detail is an owner decision) |
| D-V26-06 door symbol reconciliation (Stage D) | the door's own lines only: the passage becomes a DOOR (held, not released); its doorway strip moves from floor porcelain to a marble threshold; door jamb plaster is added; the passage line goes | B01 variants: a hinge 0.35 m off its jamb, or a 0.69 m leaf in a 1.00 m gap, becomes a held door. Doorway waterproofing = width x 0.20 m; threshold PROVISIONAL; floor unchanged (12.00 m2) | one opening reconciled. Floor porcelain −0.15 m2 and marble threshold +0.15 m2 (floor area conserved); jamb plaster +0.81 m2 (PROVISIONAL); passages 9 → 8 | door held (DOOR_SYMBOL_FIT_REVIEW); threshold and plaster PROVISIONAL |

Effect on the independent real-room checks (`REAL_ROOM_VERIFICATION.md` §7):

- failing checks 11 → 10 of 66;
- the room concerned: door count right, plaster error −0.94 → −0.15 m2, wall porcelain error −0.42 → −0.15 m2;
- what remains in that room is a width question for the drawing: 1.023 m jamb to jamb against the 0.80 m leaf.

## 2. Defects found and not fixed in this program (exposure)

| defect | BOQ lines exposed | size of the exposure | state |
|---|---|---|---|
| D-C2 doorway-strip attribution (a splayed wall; a merged strip) | marble thresholds, doorway waterproofing | sample: thresholds −49 % of the sample's threshold area (withheld with an RFI, not lost); doorway waterproofing −12 % | open, conservative (withheld, flagged) |
| D-C3 a doorless lobby merged into a wet room without a note | the wet scope of the lobby: waterproofing, full-height porcelain | sample: the lobby is 44 % of its room's area | owner scope decision |
| D-C4 skirting rule conflict (UP-CER-004 exception against the program's statement) | skirting in wet rooms with a 2.40 m tile below a 3.00 m finish | sample: about 41 lm | owner decision |
| D-C5 synthetic heights | every wall-area line (plaster, wall porcelain, paint, masonry) | all; door height 2.10 m used where the owner reference is 2.20 m | project values needed |
| D-D2 arc-walled room kept on its chord | membrane and tile layouts (procurement), the wall run, masonry and plaster by run | synthetic B10: layout planned for 12.00 m2 of a 13.02 m2 floor (the segment unplanned); wall run 11.0 / 10.2 lm against 14.22 / 13.42 lm (−23 %). Reference plan: 4 of 38 rooms have an arc-bounded face (all dry; Σ\|Δ\| 5.1 m2 of layout geometry); curved wall about 0.7 % of the wall run | asserted as found; roadmap item 2 |
| D-D1 layer roles inferred from one instance | doors, windows (as passages: door lines, thresholds, doorway waterproofing missing); a column (not deducted: floor / ceiling +) | synthetic B04: +2.18 % floor. Single-door drawings: every door / window typed PASSAGE | remedy available (`--layer-roles`); not seen on the reference plan (many doors) |

Area-based lines are exact in every synthetic case and in all five verified real rooms: floor, ceiling and
waterproofing floor. The exposure sits in **recognition** (which opening is a door), **attribution** (which strip
belongs to which doorway) and **layout geometry** (arcs). It does not sit in area arithmetic.

## 3. Vision and the BOQ

**Zero.** No quantity in any method comes from the raster or PDF prototypes. In the benchmark the vector PDF agrees
with CAD exactly. A clean raster agrees within 0.75 % on area, and a degraded scan never better than review. The
hybrid records keep the CAD value as the only BOQ basis (`FLOORPLAN_AI_RESEARCH.md` §5).

## 4. What would move the BOQ most, next

The ranking is by expected accuracy gain, in detail in `ROADMAP.md`:

1. doorway-strip attribution at splayed walls (D-C2);
2. arc-aware room polygons and curved wall bands (D-D2);
3. a scale / unit / layer-role pre-flight that refuses single-instance role inference (D-D1);
4. project heights instead of synthetic ones (D-C5, an input);
5. the owner decisions D-C3 / D-C4 and the junction detail.
