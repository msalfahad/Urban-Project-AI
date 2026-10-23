# T-223: the curved 1F room, the typing of unlabelled faces, the sills (floor-area line)

Worker 2 (lane A), 2026-10-23 22:41-23:40 UTC. Gate 1 (floor-area reference line, CLOSABLE rank 1). Research piece,
unwired: no released or candidate quantity changes; lane I wiring is T-240. ERS applied: s.2 steps 1-4 (element first,
evidence hierarchy, reconstruction from the printed dimensions and the drawn faces, reconciliation in units), s.3
(classify before measuring; one strip one line; never the value closer to the freelancer), s.7 (lessons rows below).

Data (Drive "Alsenan chalet project", decoded into the private folder, never committed): P7757_DXF_COMPRESSED.zip
(P7757.dxf sha256 ab54dd55), "ST7757 dxf.dxf" (9f9d1179, for the released run only). Released A re-run on engine
242e50b2 (`tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json`): REPRODUCED,
1,455 lines, BOQ_LINES.csv b96185d4. Every reference below is a P7757.dxf entity handle (HEX) or a printed dimension.

## 1. The curved east room 1F-R3CFCFD: geometry ENGINE_RIGHT, the freelancer row not reproducible

Physical element: the bedroom floor inside its walls, bounded on the east by a concave curved window bay that wraps the
oval VOID. Faces (layer 1): west B0D, north ACE, east straight piece B6B (twin AC8), south C09 / C0A with the open
passage OP-009 between them, then strip C0B and the lobby (B0B, C10 / C0F, B1D / B1C, C0C). The curved face: jamb arcs
BD1 / BD6 on layer 1 at R 2.135 m, glazing BD2 (layer W) on the SAME radius between them, BD3 .. BD5 inside it, the
outer wall face BCD / BD0 at R 1.935: the room face is R 2.135 (the glazing line counts only because the wall jambs lie
on the same curve). Printed dimensions confirm the reading: F4C 4200 (west face to the straight east line), EAD 4000,
E6F **3450 = the width at the apex of the arc** (west face to centre - R), E7B 200 (curved wall R 2.135 - R 1.935),
F88 1800 x FAA 2100 (lobby), F9F 150 (strip).

| Part | Hand | Source |
|---|---|---|
| room to the arc face | 4.20 x 4.00 - circular segment 1.6833 = **15.1167** | arc R 2.135, sweep 94.19 deg between the C0A / B6B ends |
| strip OP-009 | 1.30 x 0.15 = **0.195** | C09 / C0A gap, F9F |
| lobby | 1.80 x 2.10 = **3.780** | F88 / FAA |
| column projections | 2FEA 0.015 + 300B 0.0175 + 2FDB 0.0425 (0.02375 room + 0.01875 lobby) = **-0.075** | S-COL.BON outlines |
| joinery box in the lobby | 0.50 x 2.10 (layer 5 B0C / C17, no wall line): floor continues, **not deducted** | URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1 |
| **line** | **19.0167 m2, outline 22.151 lm** | engine L-9a22d1b81ee426e86af1 19.0165 (0.0002 = the mm rounding of the two arc ends) |

The engine line is right on geometry (= Checker 22:05 own reading, 15.1165 for the room). Against the freelancer row
(FIN tiles sheet row 22 'bed room 1', 17.29 m2 with 22.89 lm in his perimeter column; paired to this room by elimination
after T-218), every reading was tried on BOTH keys (`CURVED_ROOM_PAIRING_T223.csv`):

| Reading | m2 | lm | d m2 | d lm | Verdict |
|---|---|---|---|---|---|
| A drawn (engine line) | 19.0167 | 22.151 | +1.7267 | -0.739 | NOT A PAIRING |
| B A less the joinery box | 17.9667 | 23.151 | +0.6767 | +0.261 | NOT A PAIRING |
| C room only | 15.0604 | 16.651 | -2.2296 | -6.239 | NOT A PAIRING |
| D room + strip | 15.2554 | 16.951 | -2.0346 | -5.939 | NOT A PAIRING |
| E straight wall line (REFUSED, T-197 R4) | 20.700 | 21.900 | +3.410 | -0.990 | NOT A PAIRING |
| F chord of the arc ends (REFUSED) | 20.4906 | 21.769 | +3.2006 | -1.121 | NOT A PAIRING |
| G apex 3.45 x 4.00 rectangle (REFUSED) | 17.700 | 20.400 | +0.410 | -2.490 | NOT A PAIRING |
| H the segment taken off twice (not drawn) | 17.3333 | 22.151 | +0.0433 | -0.739 | NOT A PAIRING |

**The 0.044 m2 named:** the residual 1.7267 = the circular segment 1.6833 (the area between the straight east line and
the drawn arc, which a straight-line reading would ADD, not remove) + 0.0434. The 0.0434 exists only under reading H
(the segment subtracted a second time), which is no drawn element and misses his perimeter by 0.739 lm, so it is not
his method either. No drawn element is 0.043 m2 (columns 0.075, strip 0.195, pier pieces 0.019 / 0.024). Verdict:
**ENGINE_RIGHT** on the geometry (own hand calculation from the printed 4200 / 4000 / 3450 / 200 and the drawn R 2.135);
the freelancer side is **UNRESOLVED** (his row is typed with no dimensions; neither key closes on any physical reading:
+1.727 m2, +9.99 %). Nothing is moved toward him. Status: room geometry DRAWING-CONFIRMED (+ Checker 22:05 re-measured);
the attached lobby boundary as T-218 (walls, door, no partition).

## 2. Typing rule for unlabelled faces (proposed UP-SPACE-FACE-TYPE-001, every villa)

Scope: an unlabelled face of the architectural plan. Provenance: UP-SPACE-001 1.0.0 (interior / exterior from enclosure
and connectivity), UP-SPACE-002 1.0.0 (a project decision binds one space), UP-WET-002 1.3.0 (wet evidence), Q-67 A,
URBAN-FINISH-QUANTITY-INDEPENDENT-OF-MATERIAL@v1 (geometry is released without a proven material),
URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1. A rule change is a new rule version: lane I registers it (not edited here).

1. A binding decision EXTERIOR, or an opening to outside air with no door / glazing: never the internal floor line
   (bound: FLOOR.OUTDOOR; unbound: POSSIBLY_EXTERIOR, HELD).
2. A stack / riser / lift drawn above or below and no floor inside: SHAFT, no floor line.
3. Enclosed and reached only from interior spaces: INTERIOR; the area ENTERS FLOOR.INTERNAL (never ARCH.SPACE only).
4. Wet only by wet evidence (WC, shower, bath, floor drain, an owner wet code); a basin alone is not wet; no fixture
   and the drainage plan read: DRY; drainage not read: class HELD. The finish MATERIAL stays HELD unless a material rule
   binds the class (never borrowed from the room it opens into).
5. A box on an annotation / furniture layer with no wall line and nothing above / below is joinery (floor continues);
   with a wall line or a counterpart above / below it is a possible shaft: HELD.

Applied (`FACE_TYPING_T223.csv`):

| Face | Evidence (handles) | Class | Floor line | Area | Status |
|---|---|---|---|---|---|
| 1F dressing 1F-RFFE7AF | faces B03 + B04 / B00 / B20 / AD4 + AD5 = 1.650 x 1.800 (EE9 1650); OP-011 1.000 open passage to the 3.80 x 4.30 room, OP-019 0.800 door to the bath; inside only the layer-5 box B0A / BE3 (0.50 x 1.80, a diagonal, no wall line) and dimensions, 0 inserts; no fixture, no drain on the 1F drainage plan (T-218, sanitary-7757.pdf p.2) | INTERIOR, DRY | FLOOR.INTERNAL **+2.970 m2** (released: ARCH.SPACE only, L-7c5a02386f49947cf223) | 2.970 | area DRAWING-CONFIRMED (Checker re-measured); material HELD (URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1 sets porcelain once the DRY class is VERIFIED) |
| GF side passage (engine faces GF-R7B7A5D 1.560 / GF-RF002DC 3.600) | 1.200 x 4.700 own re-read: west A2 / A3 (door 19C), east 9F / A0 / A1 (windows 3BE / 3CB), boundary wall 105 / 106 (86 doubles 105) closed, mouth between the ends of 120 / 15A with **0 lines on any layer across it** | EXTERIOR (Q-67 A, condition MET by the Checker 2026-10-20 21:05) | out of ARCH.SPACE and out of the internal key: **FLOOR.OUTDOOR side area 5.640 m2** | 5.640 | area DRAWING-CONFIRMED (= T-123); finish porcelain / ceramic by the owner's sides rule (OWNER_RULE_OUTDOOR_FLOORS_2026-10-21): ASSUMED - OWNER-APPROVED |

Found on the way (side passage, released A): its faces carry 3.600 + 1.560 + the mouth strip GF-STRIP-OP-007 0.240
(L-686c823304edc2a7ae64, released as INTERIOR porcelain) = 5.400; **0.240 m2 is missing** (the 1.20 x 0.20 band at the
B5 beam / 1F wall position; no line on any layer there, T-123); and **GF-STRIP-OP-001 0.280 m2 porcelain
(L-2973740849077f193603) is the top of the solid boundary wall** (the engine reads the layer-5 boundary wall as a 1.40 m
passage; lines 105 / 106 run the full width): no floor at all, and its twin ARCH.THRESHOLD L-891f465afcfe1dec121e
(BLOCKED_RFI) bills the same strip twice. Both strips sit inside T-208's GF-OPEN group of the internal key.

## 3. Strips and sills: one strip, one line (`STRIPS_T223.csv`)

| Strip | Joins | Released A | Proposed | Status |
|---|---|---|---|---|
| 1F OP-011 1.00 x 0.15 | 3.80 x 4.30 room / dressing (now DRY) | porcelain 0.150 | porcelain strip 0.150 (UP-THR-001 dry, floor continues) | DRAWING-CONFIRMED (T-218 had it HELD with the untyped side) |
| 1F OP-007 1.00 x 0.20 | living / lift shaft (jambs B96 / B97) | porcelain 0.200 | ARCH.THRESHOLD lift landing | HELD (UP-DOOR-CLS-005) |
| 2F OP-002 1.00 x 0.20 | stair room / lift shaft | porcelain 0.200 | ARCH.THRESHOLD lift landing | HELD |
| 2F OP-001 1.00 x 0.15 | stair room / +9.70 roof | porcelain 0.150 | ARCH.THRESHOLD exterior sill | HELD |
| GF OP-007 1.20 x 0.20 | side passage mouth | interior porcelain 0.240 | part of FLOOR.OUTDOOR 5.640 | ASSUMED - OWNER-APPROVED |
| GF OP-001 | boundary wall body | porcelain 0.280 + ARCH.THRESHOLD twin | none (no floor) | ENGINE DEFECT |

Sills out of the floor line into ARCH.THRESHOLD: **0.550 m2** (area kept, HELD, never 0). After the proposal every
opening is billed by one line (`assert_one_strip_one_line` passes); the released GF OP-001 pair is the one duplicate.

## 4. Floor-area like for like, restated (`FLOOR_KEY_T223.csv`)

From T-218 (+2.4643 m2, +0.64 %): the dressing 2.970 and OP-011 0.150 now sit in the engine key AND in his 'bed room 2'
19.46 (S5 no longer taken out of either side: AGREE); GF OP-001 0.280 (wall top) and GF OP-007 0.240 (exterior) leave
the engine's internal key. Engine **387.5339** vs reference **385.5896** -> **+1.9443 m2 (+0.50 %)**, closed to named
parts (residual -0.0001 rounding): curved room +1.7267 UNRESOLVED (freelancer side, engine geometry ENGINE_RIGHT),
engine-only porcelain door strips +0.600 (1F 0.420, 2F 0.180), GF-OPEN -0.2923 (was +0.2277), the other T-208 rows
unchanged, west +0.050, 500 x 365 -0.035. Not a release: the released default stays V2.9 + route G.

## 5. Rule, tests, lessons rows

Tests `tests/t223_floor_typing` (24): villa K223 hand fixture (5.00 x 4.00 room, concave bay R 2.00 at 1.50 m:
19.093376 m2 / 18.245186 m; outward bay 20.906624), bulge and radius conventions equal, mirror, rotation, reversed ring,
millimetres; adverse: chord-only arc refused, glazing arc without a wall on the same curve refused, radius in the wrong
unit refused, unknown unit refused; typing: dressing DRY with material HELD, WC wet, basin alone / drainage unread HELD,
shaft with a stack out, box with a wall line or a counterpart not joinery, open end unbound HELD (never internal), bound
exterior to the outdoor key, missing area HELD never 0; one strip in floor AND threshold refused; pairing needs both
keys and a physical reading. The Alsenan ledger reproduces from committed files (`alsenan_t223.py --check`).

Lessons-register rows (proposed): (1) 2026-10-23 | the 1F dressing 2.970 m2 missing from the floor line | an unlabelled
enclosed face was typed nothing and stayed ARCH.SPACE | type an unlabelled face from its own evidence (enclosure,
connectivity, fixtures, drainage, boxes, decisions); an interior one enters the floor line with its material HELD
(every villa) | tests/t223_floor_typing | proposed. (2) 2026-10-23 | 'curved room +1.727 UNRESOLVED' read as a
straight-line measure | the residual was compared with one key and the segment's sign was not checked | pair every
reading on area AND perimeter and check the sign of each named part before naming a residual (every villa) | ledger
test | proposed. (3) 2026-10-23 | a 0.280 m2 'doorway strip' on top of a solid boundary wall | a wall drawn on a
non-wall layer read as a gap in the wall band | a strip needs an opening drawn on the plan (door, window or an open gap
with no line across it); a gap in the band alone is not one (every villa; lane I check) | ledger test | proposed.

## 6. Missing / held

- Curved room: freelancer side UNRESOLVED (row typed, no dimensions); a designer / freelancer breakdown would close it.
- Dressing finish material HELD; side passage material porcelain vs ceramic not split by the owner rule (both allowed).
- The 0.240 m2 band missing from the passage: cause in the engine not traced (no line on any layer there).
- Not done: the GF 23-line batch other than the passage; the wiring (T-240, lane I).

Checker re-measure: (1) curved room on P7757.dxf: arcs BD1 / BD2 / BD6 R 2.135 (centre shared with BCD / BD0), the
C0A / B6B arc ends, dims F4C / EAD / E6F / E7B, the lobby F88 / FAA and the columns 2FEA / 300B / 2FDB; (2) the dressing
faces B03 / B04 / B00 / B20 / AD4 / AD5, box B0A / BE3, nothing else inside; (3) the passage A2 / A3 / 9F / A0 / A1, the
boundary wall 105 / 106 (no gap) and the empty mouth between 120 / 15A.

Files: `floor_typing.py` (method, any villa, stdlib), `extract_t223.py` (by handle -> `ALSENAN_T223_INPUT.json`, local
frames, no coordinates), `RELEASED_A_T223.json` (released line ids / values), `alsenan_t223.py` (ledger, `--check`),
`CURVED_ROOM_PAIRING_T223.csv`, `FACE_TYPING_T223.csv`, `STRIPS_T223.csv`, `FLOOR_KEY_T223.csv`, `summary.json`.
