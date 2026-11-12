# T-747 EXTERIOR PAINT FACES by the owner paint rule on ARCH_TAKEOFF_V3.0.75 (worker 2, lane A, 2026-11-12; research)

Nothing is wired: no candidate line, hub, registry, rule / knowledge version file or default moves (wiring: the T-314 r3
/ T-749 hub packages). Rules R-T747-1 .. -3 1.0.0 (`t747_rules.py`, every villa); application `t747_alsenan.py`
(`--check` rebuilds and compares); outputs `out/T747_EXT_PAINT.json`, `out/T747_FACES.csv` (126 faces). Input: the
T-314 r2 stage faces and holes, extracted by the stage's own builder at 080ccaa5 (`t747_extract_faces.py`, inputs blob
and the 12 source blobs asserted equal to the T-737 pin) into `in/T314_FACES_T747.json`. No drawing, workbook, client
name or coordinate in this folder; DXF evidence is quoted by handle, count and area only. ERS read: s.2.1, 2.2, 2.4, 7.

## 1. Physical element and the two methods

The painted exterior face = the rendered facade face of the same face id (storey band, parapet outer / inner above the
upturn / top, plinth, slab edge), each face once, its openings deducted once in full on the render (Q-73 A) and never
again on the paint; minus the parts the drawing finishes otherwise. Owner manual method: OWNER RULE PAINT 2026-11-12
("paint = plaster area on the same faces, inside and outside"; corners and opening edges are lm) and OWNER_NOTES_SIGMA
2026-10-21 (exterior Sigma = the exterior plaster area, not measured separately). Drawing method: the T-314 stage face
rows (T-305 / T-311 / T-324 / T-337 / T-348 r2 / T-567, all Checker-merged) face by face. The two coincide by
construction except where the drawing shows another finish; that is what this task checked.

## 2. Drawing check: what the elevations print on the facade faces (own decode, P7757.dxf sha256 ab54dd55)

- Sheets p.6 SE, p.7 SW, p.8 NW, p.9 NE elevations 1:100 (PDF, read as images) and the two DXF elevations (titles 24DB
  SE, 2A69 NW): no material hatch on any facade face (SE hatches 1C01 / 23DE / 23E3 / 23E7 are sections and ground), no
  finish note: 177 DXF texts, 0 finish words (clad, stone, marble, granite, tile, plaster, paint, sigma, coat, finish
  and their Arabic forms). CLAD / TILED deduction = 0 by the drawing on every face.
- ONE distinct surface is drawn: the SE entrance stone surround (quoins + voussoirs, layer '1' LINEs 1CA6 .. 1CF0,
  23AE .. 2402), +0.15 .. +4.36 by the level blocks (+-0.00 at block 2439; +0.30 / +4.30 markers 244A / 244C 4,000 mm
  apart; +1.00 = landing line 1BFE = D-GF-07 sill, door line 1C00 +1.00 .. +3.50). Polygonised: stones 1.154674 m2,
  stones + the 3 wedges to the drawn intrados 1.298383 m2 (zone), split at +1.00: plinth band 0.222500, storey band
  1.075883. Its material is printed nowhere: NOT_PRINTED_FINISH zone, paint 0 .. zone off the low end of GF/SE-2.
- Face attribution: the annex section hatch 1C01 is 6,700 mm wide (= GF/SE-1 annex face 6.70); the surround spans
  x 1,859 mm (-279,637 .. -277,778) inside the 3,700 mm left of the annex (= GF/SE-2 3.70, the face holding D-GF-07,
  sill +1.00 / head +3.50 = door line 1C00). Plinth band 0.15 .. 1.00 and storey band 1.00 .. 5.50 as T-337 binds SE-2.

## 3. Result per stage line (m2; render = stage net, asserted equal line by line to 6 dp)

| line | element | render (stage) | paint (rule) | state |
|---|---|---|---|---|
| L-b05f70c9 GF storey | STOREY | 376.694149 .. 410.179149 | **375.618266 .. 410.179149** | bounded (W02 / D-GF-07 holes, surround zone) |
| L-8bb83e16 1F storey | STOREY | 248.178057 .. 249.954348 | 248.178057 .. 249.954348 | bounded |
| L-d52c4f76 2F storey | STOREY | 117.305 | 117.305 | PROVISIONAL (D-2F-01 2.20 Q-55 C) |
| parapet outer GF / 2F | PARAPET_OUTER | 14.385 / 14.900 | 14.385 / 14.900 | MEASURED |
| parapet outer annex / 1F | PARAPET_OUTER | 14.671022 .. 15.271022 / 54.00748 .. 60.029307 | same | bounded |
| parapet inner annex / GF / 1F / 2F | PARAPET_INNER | 8.888 .. 14.914 / 8.209 .. 13.885 / 41.824 .. 56.609 / 8.49 .. 14.15 | same | bounded (D-39 split) |
| parapet top annex / GF / 1F / 2F | PARAPET_TOP | 5.997 .. 6.037 / 5.593 .. 5.674 / 9.832 .. 9.847 / 5.415 | same | 2F MEASURED |
| L-0a6d30ea plinth GF | PLINTH | 71.68859 .. 72.749795 | **71.46609 .. 72.749795** | bounded (finish not printed T-317; zone) |
| slab edge GF | SLAB_EDGE | 1.85426 .. 4.30924 | same | bounded |
| slab edge 1F | SLAB_EDGE | blank (6 of 7 faces blank) | **blank, never 0** (valued part 0.535 .. 2.00625 shown) | HELD |

Total paint lines (17 valued + 1 blank): **1,006.633044 .. 1,085.612926 m2** vs render 1,007.931427 .. 1,085.612926;
render - paint = the surround zone 1.298383 .. 0 exactly; residual 0.000000 on every face, side and line. By floor
(faces incl. the valued 1F slab-edge part): GF 506.682 .. 557.404, 1F 354.376 .. 378.445, 2F 146.110 .. 151.770.
Per facade side x storey x element: `sides` in the json (e.g. 2F NE 31.82 = 8.10 x 4.20 - D-2F-01 2.20, NW 28.56,
SE 26.685, SW 30.24 = the 2F line 117.305, by hand). Before: V3.0.75 has NO exterior FIN.PAINT line; the 3
FIN.EXT.FINISH lines (render / Sigma) are HELD blank; the 16 EXT.FENCE plaster / paint lines are boundary wall (Q-65):
refused here, unchanged.

## 4. Edges as lm (R-T747-3; never m2, arris once with the beads)

- Window outside edges (jambs + head; sills / thresholds are their own item): **103.6831 lm**, 3 HELD (W02, W03, W17).
  T-746 gives 106.020: all 26 of its PAINT_LM windows are on facade faces; the difference -2.3369 is W15 / W16 / W26:
  T-746 took the rectangle 7.75 / 7.75 / 4.60, the merged T-405 / T-697 ledger the developed arched outline 6.8461 /
  6.8461 / 4.0709 (the render holes 4.363 / 4.363 / 1.875 m2 use the same arched outline). Residual 0.000000.
- Exterior doors (7): edge = the T-746 door return row (frame posts drawn over the full jamb depth: jambs 0, head 0 ..
  w) **0 .. 12.200 lm**, already inside T-746's door total: cited, never added again.
- Corners (vertical convex arrises, mouths, stop-ends, plinth; T-737 re-binding by host line): **168.500 .. 182.050
  lm** (+1.4 m NO_HOST blank). Horizontal arrises (parapet top edges, slab edges) stay in T-337 FIN.EXT.CORNERS 710.172
  .. 821.859 m.l (stage missing item): cited, not restated.

## 5. Findings and verdict proposals

- **F-T747-1 ENGINE_WRONG (T-746 window OUT lm)**: arched heads counted as rectangles, +2.3369 lm (106.020 vs 103.6831,
  -2.20 %); the developed outline governs (T-405 ARC_DEVELOPED). Fix rides the paint-edge wiring (T-749).
- **F-T747-2 NOT_PRINTED_FINISH (SE entrance surround)**: 1.298383 m2 drawn as stones, material unprinted; the render
  stage carries it as render. The render owner (T-314 r3) must carry the same exposure (render and paint move
  together); designer item (surround material), not an owner question.
- **F-T747-3 bead vs frame (for H2b)**: the 7 exterior door rings (39.2 m.l, T-737) count jambs as arrises while T-746
  found the frame drawn over the full jamb depth (no free arris): the bead owner re-checks before H2b wires.
- **Item code (for the Lead / T-749)**: no exterior FIN.PAINT code exists; the owner's Sigma note puts the paint area on
  the FIN.EXT.FINISH faces. Proposal: one paint (Sigma) line per stage line key, figure = this table, not a second
  render line.
- **Engine vs freelancer**: his Sigma net 1,469.9675 m2 vs paint 1,006.633 .. 1,085.613 (-31.52 % .. -26.15 %), the
  same reconciliation as the render (T-567, residual 0): RULE_DIFFERENCE (domes 181.806 excluded by the owner, half
  holes, boundary wall 107.24 Q-65, drip 50.88) and ENGINE_RIGHT (his row 65 double count 9.000, row 74 no face
  52.770). Corners his 1,297.35 m.l vs 168.5 .. 182.05 + 103.68 + 0 .. 12.2 (+ T-337 horizontals): RULE_DIFFERENCE
  (T-697: 3 lines per parapet metre, boundary wall, drip).

## 6. Checker re-measure suggestions (2 faces)

GF/SE-2/COVERED/storey (3.70 x 4.50 = 16.65 gross, D-GF-07 hole HELD 0 .. 5.000, surround storey part 1.075883 from the
handles above) and 2F/SE-1 storey (8.10 x 4.20 = 34.02 - W26 1.875 = 26.685 = paint).

## 7. Lessons register row (proposed, ERS s.7)

2026-11-12 | T-747 | exterior opening edge lm | a paint-edge ledger composed arched windows as rectangles while the bead
and hole ledgers of the same openings used the developed arc | one opening, one outline: take the developed outline
wherever a merged ledger established it, and reconcile every per-opening edge figure against the bead ring before
summing | tests/t747_ext_paint.
