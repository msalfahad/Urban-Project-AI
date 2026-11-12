# T-733 tiles H3 readiness: F1 / F4 tread highs, V-07, tile and marble census on V3.0.73 (lane A, research, unwired)

Worker 2, 2026-11-12. Candidate of record ARCH_TAKEOFF_V3.0.73 (c5a0b128, NOT RELEASED). No engine module, rule /
knowledge version, registry or frozen file touched; nothing wired; no released quantity moved; V2.9 + route G unchanged.
Drawings (Drive "Alsenan chalet project", own decode this run into the private folder): P7757_DXF_COMPRESSED.zip ->
P7757.dxf (sha256 ab54dd55) and "ST7757 dxf.dxf" (9f9d1179). Files: `t733_extract.py` (own read by handle ->
`T733_DRAWN.json`: handles, layers, lengths, areas, counts only), `t733_rules.py` (R-T733-1 .. -4, every villa),
`t733_alsenan.py` (builder, 10 inputs sha256-pinned, `--check`), `out/T733_H3_READINESS.{json,md}`,
`tests/t733_tiles_h3` (14 tests).

## (a) F1 / F4 tread highs: ENGINE_RIGHT, the T-727 'double count risk' withdrawn

Physical element. ST-02 draws every step as a PAIR of lines 0.050 m apart (layer 5 and layer 2; straight flight pairs
B43/B4E .. B4D/B58, radial pairs BA3/BA4 .. BB9/BBA; the GF plan draws the same pair 22F / 234, offset 0.050). A flight's
plan area is the strip between its first and last line of the SAME set.

| reading (own, by handle) | F1 m2 | F4 m2 | overlap | union | sum |
|---|---|---|---|---|---|
| engine (F1 on layer 2 BBA..B4E, F4 on layer 5 B43..B4D) | 4.094412 | 3.450000 | 0.057438 | 7.486974 | 7.544412 |
| one set, layer 2 (BBA..B4E, B4E..B58) | 4.094412 | 3.450000 | 0 | 7.544412 | 7.544412 |
| one set, layer 5 (BB9..B43, B43..B4D) | 4.104061 | 3.450000 | 0 | 7.554061 | 7.554061 |

- My mixed reading reproduces T-727's engine footprints to the 1e-6 (F1 4.094412, F4 3.45, overlap 0.057438, union
  7.486974): the engine read F1 on the layer-2 set and F4 on the layer-5 set. That puts the 0.050 x 1.150 junction strip
  into both flights AND drops the 0.050 x 1.150 strip at F4's arrival (x 3.000 .. 3.050): the footprints overlap but
  nothing is built twice. On either one set the overlap is 0 and sum = union (SET_MIX, R-T733-1).
- Governing set (R-T733-2): the layer-2 set's far line B58 lies on the drawn void edge B75 and the inner stringer end
  B76 (gap 0.000); the layer-5 line B4D stops 0.050 short. The layer-5 top line BB9 also runs out to r 2.7805 (the outer
  string, 1.200 long) where every tread line is 1.150: its first quad carries 0.009466 m2 of string, not tread.
- So: 1F L-6cf11c2d high 4.094413 (own 4.094412, +0.000001 rounding) and L-ea55ed31 high 3.45 (own 3.45) are each right;
  their sum 7.544413 is the physical tread plan of both flights. GF carriers: L-fa534ec5 beside 4.094413 right;
  L-89c84fdd RELEASED 3.45 right. **No line changes; verdict ENGINE_RIGHT on all four.** Applying R-T727-1's union to
  these highs (4.036974) would have under-measured F1 by 0.057438 m2 (-1.40 %).
- T-727's 1F living porcelain (33.411036, ENGINE_RIGHT) is unaffected: the arrival strip x 3.000 .. 3.050 lies inside
  the light-well outline (east edge AF5 at x 4.200), where the T-345 record deducts every m2 of the face once whatever
  its label. Only the 'union of flights' figure 7.486974 understates the two flights by 0.057438 m2 (a label defect).
- After H3s wiring (T-723 rows), the two 1F exposure lines become EXCLUDED (T-715 R-T715-3), so no 1F high is ever
  valued; the GF carriers hold the treads.

## (b) V-07 third dome: HELD -> NOT_A_VOID (DRAWING-CONFIRMED) on the approved design

- T-719 / T-727 recorded "no structural drawing". There is one: the ST sheet carried by exactly the nine 2F-block
  columns (overlay 9 / 9 column outlines, worst corner residual 0.50 mm), beam-line extent 8.175 x 6.800 = 55.59 m2 (the
  2F block top roof, +13.90).
- Inside the dome footprint (circle 1300, r 2.205, disc 15.274758 m2) that sheet draws 7 beam lines (B1 / B2 pairs
  crossing, chords 0.065 .. 4.113 m), 3 slab reinforcement lines running through, 2 column outlines + their fills;
  S-OPENING entities on the whole sheet: 0; no circle, arc, ring or non-column hatch. The panel is continuous.
- R-T733-3: the ceilings below are closed by drawing. 2F maid L-7531772e 19.350001 and bath L-1bd4ec39 5.55 m2 (released,
  full) are **ENGINE_RIGHT**; deduction 0 is DRAWING-CONFIRMED, not a default. The dome itself (arch elevations, springing
  +14.40 above the slab) and its material stay with Q-29 / DOME-3 / CF-S8.3-01 (D-21): unchanged.
- S1 (client's open-skylight request, owner 2026-10-22: no revised structural drawing): would need a redesigned slab
  (beams and a column cross the footprint); shown apart, not quantified, never applied.

## (c) Census on V3.0.73 and the H3 / H3s wiring list

- Scope: the T-681 tile filter (11 codes) + FIN.MARBLE.*: **321 lines**, byte-identical V3.0.69 -> V3.0.73 (stale 0,
  missing 0, added 0). HELD 127 (72 blank): tile 104 + marble 23.
- HELD by cause (newest merged ledger first: T-715 stair ledger, then T-681 / T-702, then T-648): T-715 CONDITIONAL_ON_FORM
  27, NOT_APPLICABLE 12, AT_MOST 8, MEASURED 8, RANGE 4, AT_LEAST 3, BLANK_NAMED 1, WIRING_GAP 1; T-681 OPEN_BOUND 44,
  DESIGNER_ITEM 7, OWNER_OPEN 6, MEASURABLE_NOW 2, WIRING_GAP 1; T-648 PRINTED_VALUE_GAP 3 (lift surrounds). Every HELD
  line has a cause id; none is 0.
- H3 wiring (T-723 rows, made on V3.0.71) restated: 94 rows (H3 CHANGE 2 = T-702 GF-10 / GF-11 wall tile bounds
  11.40 .. 25.21 and 7.04 .. 19.555 m2; H3s 92 = T-715 / T-718 stair finishes: CHANGE 43, BESIDE 44, TEXT 3, ADD 1,
  KEEP 1). Every host's V3.0.71 entry equals its V3.0.73 entry: **stale hosts 0**; the list wires as it stands. T-733
  adds no row (no quantity changes).
- Waste: no line carries a tile waste factor; size-based waste (Urban rule) belongs to the materials stage on the
  purchasing group, never a default here.

## Engine vs freelancer

No quantity moved. The freelancer's stair marble is not itemised by flight (T-412 / T-553); the 2F ceilings are inside
his flat ceiling rows: NOT_COMPARABLE at line level. Verdicts: tread highs ENGINE_RIGHT (T-727 s.5 risk withdrawn);
V-07 ceilings ENGINE_RIGHT (closed slab drawn); census: no stale entry.

## Lessons-register row (proposed, ERS s.7)

2026-11-12 | a 0.0575 m2 'double count' between two stair flights (T-727) and a 'no structural drawing' dome void
(T-719) | the footprints were read on different line sets of the same step pairs, and the slab sheet was not looked for
by column overlay | read every flight on ONE step-line set (the set whose end lines meet the drawn outline) before a sum
or union; find the governing slab sheet by overlaying checked columns before calling a void unresolved (any villa) |
tests/t733_tiles_h3 (normal: set mix kept; adverse: physical overlap, missing reading, unread slab, no slab, stale
entry) | closed, no quantity moved.

## For the Checker (re-measure)

1. 1F plan, ST-02: pairs B43 / B4E and B4D / B58 0.050 apart; B58, B75 and the end of B76 on one x; the F1 quads on
   BBA .. BA4 + junction BA4 -> B4E (12 quads, last 0.398468); F4 on B4E .. B58 = 1.150 x 3.000.
2. ST sheet with the nine 2F-block columns: no S-OPENING, beams B1 / B2 across the circle footprint (2F plan 1300).
