# T-799 his plaster shaft rows 54.00 m2 + Checker F-V788-1 (research; no candidate line moved)

Worker 2 (lane A), 2026-11-14, claim 20:40 UTC. Drive "Alsenan chalet project" read this run (read-only, private
copies only): P7757_DXF_COMPRESSED.zip, p7757_arch_sheet03.pdf (GF plan), p7757_arch_sheet04.pdf (1F plan), the
freelancer plaster workbook (his rows read by number only; the repository copy tests/alsenan/registers_b1 agrees).
No coordinates, drawing images, names or workbook text stored.

## 1. His two "no drawn face" rows, 54.00 m2 (4.62 % of his 1,169.13)

| His row | m2 | Physical element found | Ours | Class |
|---|---|---|---|---|
| GF section row 8 "stair wall", 11.25 x 3.60 | 40.50 | the faces of the ST-02 round-stair well where it rises through the 1F (void 5.87 x 4.00 printed on sheet 04, the top flight along the neighbour-side wall, printed run 7.02). It is the only stair in his GF section apart from ST-01, which his rows 23 / 24 bill. Length: printed 7.02 + 4.00 = 11.02 (-2.0 %); DXF neighbour-side run of our 1F-13 face 10.67 + 0.20 pier jogs = 10.87 (-3.4 %). His GF reception faces are already in his hall row 7 (54.25 vs our GF-08 53.19 lm), so row 8 is not a GF face | carried ONCE in the 1F-13 run of FIN.PLASTER (neighbour run 10.67 + west well face 5.135 m, x 4.04): no omitted face, no fix row | PLACEMENT: his GF section vs our 1F-13. Whether his 1F living row 15 (40.25 lm) also bills these faces (a double count on his side) cannot be read: he gives no per-wall rows. Proposal ENGINE_RIGHT on face count (the faces exist once, ours once); UNRESOLVED on his side |
| 2F section row 24 "continued" (of the stair-house box), 2.50 x 5.40 | 13.50 | no face: the only 2.50 m wide faces of ST-01 are the shaft faces (inside his row 23 box 14.80 x 12.90, T-173) and the GF south wall under the 1F slab (also inside the box, which counts a south side over the full 12.90) | - | UNRESOLVED, 13.50 m2 = 1.15 % of his 1,169.13; probable second count of the shaft's 2.50 m south side (not established) |

Residual named: 13.50 m2 (1.15 %). The 54.00 split: 40.50 PLACEMENT (element identified, carried in our 1F-13) +
13.50 UNRESOLVED.

Physical faces found missing from ours while tracing the ST-02 well (below materiality, logged, no fix row; owner
13 Nov: nothing below 1 % of its line): (a) the 1F slab-thickness band 0.16 m on the neighbour-side wall where the well
has no slab (printed run 7.02): 1.12 m2; (b) the beam face under the 1F master-bed wall on the well's west side
(no GF wall below, 4.00 + 1.20 printed, beam depth not read here, company default 0.60): about 3.12 m2 DEFAULT.
Together about 4.2 m2 = 0.26 % of FIN.PLASTER 1,622.0. If the Lead wants them: one fix row on the 1F-13 line.

## 2. F-V788-1: doors as barriers (R-T788-4, `t799_rules.py`; R-T788-3 not edited)

The adverse case reproduces the defect: a 4 x 4 room between a hall and a lobby with four 0.90 m door gaps on one
axis (two interior, two exterior) escapes in exactly 2 rays (0 and 180 deg) and R-T788-3 drops it as OUTDOOR. R-T788-4
adds every door gap (closing chord or the door block's drawn geometry) to the barrier lines; doors not read = HELD.
Tests `tests/t799/test_t799_door_barrier.py` (9): defect reproduced, adverse stays indoor (+ mirror, rotation), a yard
piece stays outdoor, doorless openings unchanged, the split moves a piece only by doors, doors not read raises.

Alsenan (`t799_cornice_check.py`, upper bound: all 135 block INSERTs in the plan exploded, 775 lines added as
barriers): the GF open-room clip still has ONE outdoor piece, 0.849 m2 under both rules. More barriers can only turn
OUTDOOR into INDOOR, so with doors alone it is the same. **The cornice 426.31 lm does not move.**

## 3. Lesson row (proposed, ERS s.7)

| 2026-11-14 | his two "stair" plaster rows had no drawn face | a "stair wall" row in a storey section can bill the faces of a different stair's double-height well that the engine carries in the upper zone | look for every stair and void on all floors before calling a row faceless; compare a zone with the rows of every section that can bill its faces | t799 doc s.1 | proposed |
