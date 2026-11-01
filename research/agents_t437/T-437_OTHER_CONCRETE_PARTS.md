# T-437 Other unexplained concrete parts of the r4 roll-up: pool-wall height, beam lengths, boundary lengths

Worker 1 (lane S, backlog-permitted), 2026-11-01 21:24 .. UTC, branch `agents/task-T-437`. Research only: no engine,
candidate, line, rule / knowledge version file, method or released cell changed; nothing released or moved. Development
villa (Alsenan), method every villa; not an accuracy claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied.

## 0. Sources and run

Own Drive copy this run (folder "Alsenan chalet project", decoded into `.work/private` only): 'ST7757 dxf.dxf'
(sha256 `9f9d1179` = manifest). Pool levels and printed layers: merged T-183 r2 (NW elevation cut of P7757 dxf + ST p.7,
Checker re-read). His figures: read at run time from the committed `tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json`
by sheet and row (never retyped). Parts: merged T-428 summary (`unexplained_left`, asserted); beam marks: merged T-395
summary (asserted per mark and per storey). Drawing figures (metres, by DXF handle): `ALSENAN_T437_INPUT.json`.

```
python3 -I research/agents_t437/t437_alsenan.py --write      # summary_t437.json (m3, m, handles; no coordinate)
```

Rules `t437_rules.py` R-T437-1 .. 5; tests `tests/t437_other_parts` (28; hand Villa R437 + the committed summary).

## 1. Result (signs engine - freelancer, m3)

| Part (T-428) | m3 | Physical element | What the drawing allows | Status now | Proposal for the Checker |
|---|---|---|---|---|---|
| PL-WALLS height rest | -0.471346 | RC pool wall, 0.20 thick, rim +0.30 to base top -0.90 = 1.20 m on the band 2.356726 m2 | his 1.80 m = rim to formation exactly (1.20 wall + 0.40 base + 0.05 screed + 0.05 membrane + 0.10 blinding), and also = rim to base underside 1.60 + the 0.20 upstand above the deck structure counted again; both put 0.20 m x 2.356726 m2 outside the RC wall | UNRESOLVED (class waits for the Checker) | **ENGINE_RIGHT**, cause ambiguous between the two exact constructions; not RC wall concrete either way |
| BM-GF B7 | -0.120805 | GF B7: straight 1.20 (4B6), quarter arc 47D, void straight 437, ring at the pool void | each of his two B7 rows alone is reproduced by several drawn sums within his precision (3 / 3), **no pair** of them uses disjoint drawn pieces | UNRESOLVED | UNRESOLVED (no consistent construction; T-252: one row has no location) |
| BM-GF B2 | -0.011152 | GF B2, three runs | his rows 1 and 3 are drawn readings exactly (column 341 face to line 278, 2.950; edge 29E, 3.100: through-support, inside T-395's traced term); his row 2 passes the longest drawn reading of the x 57.2 run (edge 286, 4.500 m, already through B1's own 0.80 m run and column 36B) by 0.100 m | UNRESOLVED | UNRESOLVED, untraced 0.008 .. 0.072 m3 |
| BM-GF B11 / B8 | +0.004050 / +0.001665 | | his rows 0.027 / 0.011 m short of the drawn face-to-face length, inside one 0.05 m step of his printing | UNRESOLVED | **ENGINE_RIGHT** (STEP, R-T437-5) |
| BM-1F CB12 | -0.160962 | 1F CB12 0.25 x 0.75, edges 5DE / 5DF, columns 69D 0.20 / 664 0.90 / 676 0.25 along the axis, end carriers 5C1-5C5 (0.30) and 5BE-5C0 (0.20) | his length passes the outermost drawn extent (outer faces of the two end carriers, 12.000 m) by **1.000 m**; constructions tried: valued f2f 10.782147, through 664 11.55, inner carrier faces 11.50, edge 5DE 11.75, carrier centre lines 11.75, outer carrier faces 12.000 | UNRESOLVED | UNRESOLVED; untraced at least **0.187500** (F-T437-2) |
| BM-1F B11 / B6 | +0.007173 / +0.000273 | | 0.048 m (0.05 step) / 0.002 m (0.01 step) short of the drawn length | UNRESOLVED | **ENGINE_RIGHT** (STEP) |
| BM-2F B2 | -0.087240 | 2F B2 0.20 x 0.40: four drawn runs, four labels (790 on BAND0003 2.50, 78E on BAND0005 3.00, 78A on BAND0007.1 1.80, 775 on BAND0007.2 3.00) | four of his rows bind the four drawn runs exactly; **one 2.500 m row is left over**, longer than the whole through-support room of the mark (1.3995 m: gap 418 0.1995, column 41E 0.20, five carrier widths 0.20); no held 2F run is 2.50 m | UNRESOLVED | **ENGINE_RIGHT** (COUNT, R-T437-3; F-T437-1) |
| GB-BOUNDARY length | -0.050400 | upper G.B band 7FE (0.20 wide) | his length is printed to whole metres: within 0.5 m the 7FE axis 41.72 and the 7FE outer run 42.12 both reproduce it (inner 41.32 does not); the band's solid is its area 8.344 m2 / 0.20 = 41.72 m either way | UNRESOLVED | **ENGINE_RIGHT**, cause ambiguous (axis rounded or outer run); never the 0.28 m as concrete |
| BW-BAND length | -0.145200 | lower boundary band 1658 / 1659 (0.20 wide), footing crossings 21.45 axis / 21.05 inner / 20.15 outer (T-403 / T-065) | no one-face construction within 0.05 m (axis free 70.49, +1.21; inner free 70.09, +1.61; outer free 72.59, -0.89); the only near figures mix faces (outer length less inner crossings 71.69; axis less outer crossings 71.79): refused | UNRESOLVED | UNRESOLVED (constructions and misfits listed) |
| **Row (re-adds to -1.033946, 2e-6)** | **-1.033944** | | | | ENGINE_RIGHT -0.595825 / UNRESOLVED -0.438119 |
| C9 section (restated, not re-measured) | -0.138000 | 1F C9 (667 / 679) | 2 x (0.18 - 0.20) m2 x 3.45 m (T-394): schedule 1ST 20 x 90 (engine), drawn outline 679 0.25 x 1.00, his 0.20 x 1.00 | UNRESOLVED | designer item (unchanged) |

The beam sub-parts re-add exactly to the T-395 storey terms (GF -0.126242, 1F -0.153516, 2F -0.087240) and the per-mark
T-395 figures are asserted. If the Checker accepts every proposal, the r4 'unexplained, no owner' list loses -0.595825 m3
(to ENGINE_RIGHT) and keeps -0.438119 m3 UNRESOLVED (GF B7 -0.120805, GF B2 -0.011152, 1F CB12 -0.160962, BW-BAND
-0.145200) plus C9 -0.138 (designer). No candidate line, valued figure or residual moves (R-T428-1).

## 2. The pool wall (ERS s.2.1, s.2.3)

Physical element: the RC wall of the D-shaped tank, 0.20 thick, on the 0.40 RC base; RC height above the base top =
rim +0.30 - structure line -0.90 = 1.20 m (R-POOL-4, T-183 r2, DRAWING-CONFIRMED), the 0.15 upstand above the deck finish
inside it; below the base: 5 cm screed, 5 cm membrane, 10 cm plain concrete (formation -1.50). His row: one run at 1.80 m
on the 0.20 thickness; his floor row already covers the outer footprint at 0.40 (base counted again: -0.942690, T-385).

| Construction for his 1.80 (to 0.05 m) | Value | Misfit | Meaning |
|---|---|---|---|
| rim to RC base top (the wall) | 1.20 | +0.60 | engine basis |
| rim to base underside / finished depth 1.15 + build-up 0.05 + base 0.40 | 1.60 | +0.20 | base again (T-385 named) |
| rim to screed underside / membrane underside | 1.65 / 1.70 | +0.15 / +0.10 | |
| **rim to formation** | **1.80** | **0.000** | the dig depth: screed, membrane and blinding taken as wall height |
| **rim to base underside + upstand above the deck structure again** | **1.80** | **0.000** | the upstand (already inside 1.20) counted twice |
| deck finish to formation | 1.65 | +0.15 | |

Both exact constructions give the same class: the last 0.20 m x 2.356726 m2 = 0.471345 m3 is not RC wall concrete (the
screed / membrane / blinding are separate items, T-183 R-POOL-3, the blinding HELD for its projection; the upstand is
already in the wall). His pump-room wall row uses the same 1.80 m, and no pump room is drawn (T-183): weak evidence that
1.80 is his standing pool depth, not a drawn level. Proposal ENGINE_RIGHT, cause ambiguous; the earlier text 'height above
the rim' is withdrawn: no construction puts concrete above +0.30.

## 3. Beams (R-T437-2 / -3 / -5)

- **2F B2 (COUNT).** His rows (3.00 x 2, 2.50 x 2, 1.80 x 1) against the four drawn, labelled runs 3.00 / 3.00 / 2.50 /
  1.80: exact binding, one 2.50 row left over; the mark residual is -0.200000 = 2.50 x 0.20 x 0.40. The whole
  through-support room on the mark is 1.3995 m, so the left-over row can never be a length basis. **F-T437-1:** T-395's
  THROUGH_SUPPORT -0.112760 on 2F B2 belongs to the same row (his four other rows are face to face exactly): proposal to
  re-class it to COUNT in the next roll-up (it is a traced part, not in this row's -1.033946; no figure moved here).
- **1F CB12 (UNRESOLVED, bound).** Engine valued length 10.782147 m (= 2.021651 / 0.1875; it holds 0.132147 m of
  beside-support plan beyond the bands). Outermost drawn extent = outer faces of the end carriers 37.848 .. 49.848 on the
  sheet axis = 12.000 m (edges 5DE 11.75 / 5DF 11.60 lie inside it). Drawn room for any through-support length = 1.217853 m;
  his excess over the valued length 2.217853 m; untraced at least 1.000 m = **0.187500 m3**. **F-T437-2:** T-395's
  allowance 1.359397 m passes the drawn room by 0.141544 m (0.026539 m3): the support allowance added the 69D / 664 /
  676 extents to a valued length that already holds the beside-support piece (R-T437-2 adverse case). Untraced stays
  UNRESOLVED; the T-395 figure -0.160962 is the lower of the two readings, not a cause.
- **GF B2 (UNRESOLVED).** Two rows trace exactly to drawn readings that run through supports (column 341 face to the
  carrier line 278 = 2.950, inside column 32F; edge 29E = 3.100 through columns 34A and 356); the third row passes the
  longest reading of its run (edge 286, 4.500 m, from 32C's outer face to the B20 face, already through B1's own 0.80 m run
  and column 36B) by 0.100 m: untraced 0.008 m3 if B1's run is in his row, up to 0.072 m3 if not. T-395's -0.011152 lies
  inside that range.
- **GF B7 (UNRESOLVED).** Drawn pieces: straight 1.200 (33E / 341; 2.200 outer faces; edge 293 1.800), quarter arc 47D
  (centre 1.884956, outer 2.042035, inner 1.727876; + the 0.50 m strip past column 353, + column 356), void straight 437
  (1.700; 2.250 outer faces), ring (plan / 0.20 = 3.332030; arcs 2F0 2.674973, 2EE + 2EF 1.214690, 310 + 311 1.546783,
  312 + 313 0.833834). Within his precision, his first row has 3 drawn sums and his second 3, but no pair uses disjoint
  pieces: no consistent construction of both rows. Never the nearest.
- **STEP rows (GF B11 +0.004050, GF B8 +0.001665, 1F B11 +0.007173, 1F B6 +0.000273):** his length is short of the
  drawn face-to-face length by less than one step of his printing (0.05 m; 0.01 m on B6), and never longer: ENGINE_RIGHT.

## 4. Boundary lengths

Upper G.B (band 7FE: segments 2.45 / 31.37 / 8.30 outer, 2.25 / 30.97 / 8.10 inner, two 0.20 ends; axis by area 41.72):
his figure is printed to whole metres, so the axis and the outer run both reproduce it within half a metre; the solid of
the band is its area over its width either way, so the 0.28 m x 0.30 x 0.60 = 0.0504 m3 is not boundary concrete
(ENGINE_RIGHT proposed, cause ambiguous). The mixed sums (outer 31.37 + 8.30 + inner 2.25 = 41.92) are refused.
Lower band: no one-face construction within 0.05 m (table s.1); T-065's reading 'between the inner and outer free
lengths' is confirmed, and the two near figures (71.69, 71.79) mix faces: refused. Stays UNRESOLVED.

## 5. Methods side by side (ERS s.2.2)

| Part | Owner manual method | Drawing-derived (candidate of record) | Freelancer |
|---|---|---|---|
| pool wall | R-POOL-4: RC height rim -> structure line, band x height | 2.356726 x 1.20 = 2.828071 | 12 m run x 1.80 x 0.20 (base, under-base layers or upstand inside) |
| beams | URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1: face to face, supports to the column / carrier | valued lengths (T-395) | through most supports; one extra 2F B2 row; CB12 1.00 m beyond the drawn extent |
| boundary | Q-28 A (lower band, PROVISIONAL), band area / width | 41.72 m upper (HELD line), 70.49 m free lower (HELD) | whole-metre upper length; lower 1.21 m longer than the axis free length |

## 6. Disjointness

No part or sub-part id of this row is owned by T-430 (GB-MAIN), T-436 (GS-SLAB and its sub-parts, merged c943cabb),
T-444 (GS cell I-07) or T-445 (footing blinding): asserted in the script and in the tests. The pool blinding (T-183
component B) is named only as the meaning of a construction; nothing of it is counted here.

## 7. Observation for the Checker / lane I (no figure moved)

**O-T437-1:** GF B4 edges 2B2 / 2B3 run 0.500 m past column 353 to the closing line 484, where the B7 arc 47D begins.
That 0.20 x 0.50 m plan is in no beam line (B4 BAND0030.1 stops at 353; the arc band BAND0049 starts at 484): 0.050 m3 at
B4's 0.50 depth .. 0.075 m3 at B7's 0.75 (a range: which member's depth is not printed). Slab coverage not checked.
Candidate GAP for lane I; never 0 if confirmed.

## 8. Rules (R-T437-1 .. 5, every villa) and proposed lessons row (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | -1.034 m3 of pool / beam / boundary residual stood 'untraced' after r4 (T-428), one part described as 'wall height above the rim' | the parts were split against allowances and nearest figures, never against every drawn construction; two allowances over-read (2F B2 count read as length; CB12 support counted inside an already-valued length) | a figure is traced only by a construction within his printed precision; mixed-face constructions are refused; several exact constructions are a cause only when they give one class; a through allowance is bounded by the outermost drawn extent less what the valued length already holds; a left-over row longer than the mark's whole support room is a COUNT; a difference inside one printing step is his step (every villa; provenance T-437) | tests/t437_other_parts (Villa R437: pool rim-to-formation unique, boundary whole-metre / mixed refused, beam 'length taken through a column already deducted', count vs length, step, split / disjoint refusals) | PROPOSED |

## 9. Checker re-measure list

- One beam length: 1F CB12 on 'ST7757 dxf.dxf': edges 5DE 11.750 / 5DF 11.600, columns 69D (0.20 along), 664 (0.90), 676
  (0.25), carriers 5C1 / 5C5 (0.30) and 5BE / 5C0 (0.20); outer carrier faces 12.000 m apart.
- 2F B2 labels 790 / 78E / 78A / 775 on BAND0003 / 0005 / 0007.1 / 0007.2 (2.50 / 3.00 / 1.80 / 3.00).
- Pool: T-183 levels; rim to formation 1.80 = 1.20 + 0.40 + 0.05 + 0.05 + 0.10.

## 10. Not done / uncertain

- GF B7 and CB12 his lengths stay unexplained; GF B2's third row depends on whether his row includes B1's 0.80 m run.
- The boundary whole-metre reading relies on his printed precision (an integer); if the Checker reads his 42 as 42.00,
  GB-BOUNDARY stays UNRESOLVED (no construction within 0.005 m).
- C9 restated only; O-T437-1 slab coverage not checked; V3.0.39 not re-run (no valued concrete line read changed since
  V3.0.34 per the merged roll-ups).
