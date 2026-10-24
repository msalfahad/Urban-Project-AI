# T-250: geometric face crosswalk (face length per wall), W03 room-side line, the W06 room, the roof-datum faces

Worker 2, 2026-10-24 05:40 UTC onward, run session_01RE1GSHEjxcHfg5zBhSU6Fz. Lane A, gate 2; feeds T-244 (plaster /
paint whole line). Research + tests only: no engine module, method, rule / knowledge version, registry, merged ledger or
released / candidate quantity changed; nothing applied. Development villa, not an accuracy claim. ERS read: s.2 steps
1-4, s.3 (geometric scope before numbers; one element, several trades), s.4, s.7. Drawing: Drive 'Alsenan chalet
project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha ab54dd55); every reference below is an entity handle on it.

## 1. Physical element (ERS s.2 step 1)

A wall FACE is one straight wall run seen from one side. Its LENGTH is the stretch of the run's face line the room
actually touches, between the drawn corners; a column flush with the face is on it (plastered as wall, T-128 COLUMN), a
column standing proud is not (its own faces are off the line). The room-side line of a curved opening is the drawn line
that bounds the room (the room lies on it), developed along that line between the jambs. Block, plaster and paint of one
face read ONE storey interval (floor structural top -> slab top above); heights differ only by the member over the wall.

## 2. Method (`face_crosswalk.py`, stdlib, any villa; rules R-T250-1 .. 3 proposed)

- Room side: the merged T-128 r3 walk (walk_r2.py, a6ac2c66) is executed unchanged on the drawing and must reproduce
  walk_r3.json on 32 / 32 rooms (contour and paintable to 0.002 m) before it is used; every 5 mm contour sample keeps
  its class, its length and the drawn entity it lies on (handle).
- Wall side: MASONRY_CENTRELINE_V2 (T-125 capture, engine module unchanged) gives every band (centreline, t) and the
  span of every split run; a split piece belongs to the final run that lists it as a member.
- (a) a sample is on a band face when its offset is t / 2 within 0.025 m, inside the band (+ 0.03), AND the room lies
  beyond that face (a 1 cm probe outward is in the room, inward is not); a room lying inside the strip is refused as a
  face of that band. Each run side is then closed metre by metre: room face (which room) / inside another band (L, T or
  crossing) / inside a column outline / no room. From the room side every sample is on exactly one face or listed as
  off-line, so the room contour closes exactly.
- (b) `room_side_line`: the one candidate line the rooms touch over at least half its arc; two or none, a dimension
  line, or a developed length that does not close with the walk is refused. Printed window width kept beside.
- (c) `one_datum`: two different intervals on one face refused; a HELD datum holds both heights (never 0).
- Capture (coordinates, scratch only): `capture_t250.py`; outputs: `alsenan_t250.py` (lengths, ids, handles).

## 3. Results

**(a) Face length per wall** (`FACE_LENGTH_T250.csv`, `WALL_SIDE_CLOSURE_T250.csv`, `ROOM_CLOSURE_T250.csv`)

| measure | value |
|---|---|
| runs / run sides closed (every metre named) | 70 / 142 of 142 |
| room-face rows on straight runs (+ 7 rows on split stretches, 1.355 m) | 158, on 68 register walls |
| room contours closed (on faces + off-line = walked contour) | 32 / 32, max 0.0013 m |
| face length on straight wall faces / of which plastered-painted (WALL + COLUMN) | 394.684 m / 318.521 m |
| off the wall lines: column faces proud 20.825, open sides 21.233, glazing off a band (W03, W17) 9.947, doorway reveals / closures 8.864, wall 9.827 (curved stubs, arc band, walls with no V2 band; incl. 3.317 inside band strips) | 70.698 m |
| per room: finish on faces + off-line WALL / COLUMN = T-128 r3 paintable (WALL + COLUMN) | 32 / 32 within 0.01 m |
| T-237 room-wall faces given a geometric length | 69 of 75 (6 named below) |
| beam-band m2 on the 40 BAND_EXPLAINED faces of T-237 (face length x band per metre) | 43.472 m2 (concrete substrate under plaster) |

Run vs face, worked (handles in the CSV): GF-W01 (exterior 0.20, run span 19.170, V2 arch run 16.470 = register 16.470):
room face 16.700 (GF-07 3.015, GF-08 13.856; drawn 119 / column faces), inside WB-FL0081-FL0082 0.200 (T end), proud
columns 2.270; the outer side has no room (exterior). 1F-W05: room face 6.950 of 7.100 (1F-01 4.500 incl. W14 2.45,
1F-03 2.450), 0.150 inside 1F-W11 (T end). The register length (masonry, columns and openings out) and the face length
(room side, column faces and openings in) are two lengths of one wall; each difference is named per side in
`face_reading`.

**(b) W03 room-side line** (`CURVED_ROOM_SIDE_T250.csv`). Drawn: four glass LWPOLYLINEs on layer W, arc parts 27D
6.7918 (r 2.450), 27E 6.7472 (2.410), 27F 6.7025 (2.370), 280 6.6577 (2.330) about one centre; ARC 201 (layer 5, r 2.250,
6.5675) is the pool-side face of the 0.20 glazed band, where '657' is printed. The rooms GF-08 / GF-15 lie OUTSIDE the
circle and touch only 27D (6.605 m of its arc); 27E / 27F / 280 / 201 are touched by no room (refused as room faces).
Room-side developed line = 27D arc 6.7918 + its two straight returns on the straight wall's face line to the jambs
0.0917 + 0.0417 - the end of the GF-15 / GF-08 partition stopping on the glass (layer-1 line 2E2) 0.187 .. 0.199 =
**6.726 .. 6.738 m**; T-128 walked 6.731 (inside the range). VERDICT: T-128 RIGHT for plaster / paint (the room face is
the outer glass line, not 'on no face line' as T-237 read it); the window line keeps the owner's Q-38 A 6.57. +0.156 ..
+0.168 m is a RULE_DIFFERENCE between trades (window width on the printed pool-side face vs the room's own face), not a
mismatch; T-237's SPLIT_FACE_SUM_DIFFERS (+0.692 m2) closes with no quantity change. W17 (same test): the room face is
the outer glass arc BD2 3.2895 (= the Q-39 C outer arc), T-128 3.286; BD3 / BD4 / BD5, BCE, BCF refused; height HELD (T-238).

**(c) W06 room** (`WINDOW_ROOMS_T250.csv`): the glass 3E6 (0.50) with its returns 3E3 / 3EC bounds GF-13 only
(0.650 m touched); GF-12 is 1.26 m away. GF-13 = 'W.C. core wedge B 245 x 167' (T-128 / T-147 names). T-128 r3 and T-209
already deduct W06 in GF-13: ENGINE (T-128 / T-209) RIGHT, the census side label 'wedge A' (T-150 / T-175 / T-198,
carried from T-144) is wrong; no m2 moves (T-237's 0.480 m2 'move' does not occur).

**Same failure, found by the geometric crosswalk** (no quantity moves; identity only):
- W19 / W20 and the two west-bath doors: T-128 calls 1F-02 'bath west upper' and 1F-03 'lower'; the census uses the
  opposite words. Geometry: W19 glass and door D-1F-01 (OP-004, on 1F-W11) are in T-128's 1F-03; W20 and D-1F-04 (the
  doorway at 1F-W23's free end) in 1F-02. T-237 joined the ledgers by name, so its faces 1F-03 / 1F-W23 and 1F-02 /
  1F-W11 are swapped (each room still deducts one 0.80 door: room nets unchanged).
- GF-16 (master bath): the walked region runs INSIDE the strips of GF-W19 (2.000 x 0.15 = 0.300 m2, between drawn
  lines 2DD and 2DE) and GF-W31 (0.181 m2); its contour lies on the FAR faces (2DE = GF-15's face; GF-14's face on
  GF-W31), the bath's own faces (2DD, 2.000 m) are walked by nobody. Lengths are equal, so no metre is lost, but one
  physical face is carried twice (paint in GF-15, tile in GF-16) and the near face never; floor region +0.481 m2 (T-147
  already uses the printed 3.717 m2). 3.252 m of GF-16's contour is listed 'inside a band strip'.

**(d) Roof-datum faces** (`ROOF_DATUM_T250.csv`; the 18 T-237 HEIGHT_DATUM_SPLIT_ROOF faces). One datum per face:
floor structural top (T-214, DRAWING-CONFIRMED) -> slab top above.
- 1F faces under ROOF-970 (10 faces, 24.408 m): floor top 5.451. Reading A, the roof slab is the 2F floor slab carried
  on (sections draw one band, T-221 s.3): slab top 9.65 -> interval 4.199 = the register's 4.20 and T-128's plaster top
  4.04 + slab 0.16: **one datum, the two ledgers already agree in value**; their split is in status only. Reading B, the
  slab under a roof finish: 9.70 - b_roof, b_roof < 0.30 (parapet note, ST p.14) -> interval 3.949 .. 4.199. HELD on
  D-39 item 3 (continuous or stepped / cast to falls).
- 2F faces under ROOF-1390 (3 faces, 7.881 m) and GF annex faces under ROOF-430 (5 faces, 17.380 m): no slab at
  another level to carry on; interval = finished mark - b_roof - floor top, > 3.950 (2F) / > 3.750 (annex) by the
  parapet bound. The registers' 4.20 / 4.00 imply b_roof = 0.050, the constant drawn line T-214 / T-221 refused on roofs
  (CONSTANT_LAYER_VS_FALLS): those block heights are finished-derived, not established. HELD (D-39; annex also Q-54 B).
- Sensitivity, block and plaster alike (one datum): 0.497 m2 per 0.01 m of interval per trade over the 16 faces with a
  length (49.669 m). Two faces have no straight-run length: 1F-03 / 1F-W23 (the label swap above: the face is 1F-02's at
  the 1F-W23 free end) and 1F-11 / 1F-W25 (curved bay stub).

**(e) For T-244** (nothing applied): use `FACE_LENGTH_T250.csv` for face m2 (length x one-datum height); band m2 43.472
on the 40 band faces; W03 finish deduction on 6.731 (T-128, drawing 6.726 .. 6.738); W06 in GF-13; GF-16's 3.252 m on
the near faces of GF-W19 / GF-W31; faces on walls with no V2 band (GF-W30 between GF-15 / GF-16, GF-W37, GF-H02) stay in
the rooms' off-line metres (HELD for a per-face length).

## 4. Statuses

Face lengths, W03 / W17 room-side lines, W06 room: DRAWING-CONFIRMED (geometry), Checker to re-measure. Roof-datum
faces: HELD (one datum named; D-39 / Q-54 B). Nothing VERIFIED, nothing released. No owner question (ERS 2.7 not met:
W03 is settled by drawing + Q-38 A; the roof datum is a designer item already on D-39).

## 5. For the Checker (re-measure; handles on P7757.dxf)

1. W03: the arc part of LWPOLYLINE 27D (r 2.450, 6.7918), its returns 0.0917 / 0.0417, line 2E2 where the partition
   stops on it; confirm the rooms lie outside 27D and touch none of 27E / 27F / 280 / ARC 201.
2. W06: glass 3E6 / 3E3 / 3EC on the GF-13 (wedge B) contour, not GF-12.
3. Three roof-datum faces: 1F-01 / 1F-W05 (face 4.500 m: layer-1 lines in the CSV), 2F-02 / 2F-W08 (3.020), GF-01 /
   GF-W18 (6.326): face length, and that the interval reads 5.451 -> 9.65 (A) or 9.70 - b_roof (B), never 4.20 by marks.
4. GF-16 inside the GF-W19 strip: lines 2DD / 2DE (0.15 apart), the region crosses 2DD.
Reproduce: `capture_t250.py <P7757.dxf> <t125_inputs.pkl> --out <scratch>` (t125 pickle from
research/agents_t125/alsenan_v2_dump.py), then `alsenan_t250.py <capture> [--check]`; tests `tests/t250_face_crosswalk`.

## 6. Rule, lessons

- R-T250-1 (proposed, any villa): a room face belongs to the wall whose face line it lies on AND beyond which the room
  lies; every metre of a run side is named (room / junction / column / no room); a room region inside a wall strip is
  not a face of that wall. R-T250-2: the room-side line of a curved opening is the one drawn line the room touches,
  developed with its jamb returns, less partitions stopping on it; the printed window width stays the window line's.
  R-T250-3: one storey interval per face for every trade; two intervals refused, a HELD datum holds both.
- Lessons row proposed (ERS s.7): "Room-to-opening and room-to-wall links were joined across ledgers by room NAMES
  ('wedge A', 'upper' / 'lower'), which differ between ledgers for the same space (W06, W19 / W20, D-1F-01 / D-1F-04) |
  names are labels, not geometry | crosswalk rooms, walls and openings by the drawn entities a room's contour touches,
  never by name strings (any villa, any trade) | tests/t250_face_crosswalk (room inside a strip refused; window room by
  its glass)".
