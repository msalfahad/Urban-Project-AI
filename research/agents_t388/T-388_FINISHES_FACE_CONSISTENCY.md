# T-388: finishes face consistency on the candidate of record (development villa; method every villa)

Worker 2, 2026-10-31 06:45 UTC onward. Lane A, gate 1, backlog-permitted. Research + tests only: no engine module,
rule / knowledge version, registry, merged ledger or candidate line changed; **no quantity changes**. No drawing was
opened in this run: every input is a Checker-merged ledger of this repository, the same files the candidate's own
input modules pin by sha256 (t211, t244, t279, t315, t326, t327, t331 inputs). Candidate of record: the board names
V3.0.29; V3.0.30 (T-199, merged 2026-10-31 e29f3724) only ADDS formwork / metalwork lines and asserts every V3.0.29
line byte-identical, so the finish families read here are the same in both. Self-check (codemap check, pytest t061,
freeze): PASS. Development villa, not an accuracy claim.

## 1. Physical element (ERS s.2.1)

One wall **face** = one side of one wall seen from one room. On it the families stack: the **block** panel (the wall
itself, both sides at once, to the soffit of the member over it), the **plaster** coat (dry rooms) or the **backing**
coat (wet rooms, under the tile; UP-FIN-PAINT-001 substrate, Q-45 B), the **paint** (dry rooms) or the **wall tile**
(wet rooms, full height Q-48 A), and at each opening the **reveal** (jambs, head through the wall thickness) and the
**sill / threshold** (the floor-level face through the wall). An opening is ONE hole: every family that deducts it
deducts it once per face, on the faces of its host wall, with one size (a band family only the part inside its band,
R-T312-3). A reveal is its own surface and is never also inside a room face; a threshold is never also inside a room
floor. Installed area is what is measured here; procurement (waste) is out of scope.

Owner manual method and drawing-derived method side by side (Q-43 / Q-48 A; T-128): owner plaster top = paint top =
owner room height (GF 3.65, 1F / 2F 3.35; annex 3.15 information only, G2 HELD), so the owner plaster m2 equals the paint
m2 by rule; the drawing method runs plaster to the slab soffit (e.g. 4.04 on 1F) and paint to the ceiling line
(3.79 .. 3.89). That difference is a **RULE_DIFFERENCE** carried beside every line (T-211), not a defect.

## 2. Method (R-T388-1, proposed, every villa; `face_check.py`, stdlib)

(a) one opening id at most once per family per face, on at most two sides (a split side = part widths that must close
on the opening); (b) the same host wall in every family (= the block wall that deducts it); a door the room contour walks
as an off-line doorway piece is deducted on that piece (OPENING_OFF_ITS_FACE otherwise: room total unchanged, face
attribution named); (c) one size per opening across the full-height families (block, plaster, paint) within 0.01 m2, a
band family never above the hole; a block deduction smaller than the hole only with a cited cause (BLOCK_PART_EXPLAINED);
(d) tile top never above its coat top (TILE_ABOVE_COAT, m2); a fully tiled room carries no paint line other than
NOT_APPLICABLE; (d') per room each family's face length = the geometric face (contour less open sides) within 0.025 m
(five 5 mm walk samples, the artefact seen on Checker-verified rooms) or the difference is named in m2
(FACE_LENGTH_RESIDUAL); (e) a reveal carried by its own line never also walked into the face (REVEAL_IN_FACE, jamb-return
metres x height); (f) a threshold overlapping a room floor by more than 0.01 m2 is named; (g) HELD stays blank
(HELD_AS_ZERO refused; `family_total` reports the determinate sum and the HELD faces apart). Heights outside 0 .. 20 m
are refused (units).

`alsenan_t388.py` builds the face table read-only (sources in its docstring): T-250 face lengths (spine), T-333 r2 block
fill (opening deductions per wall), T-128 r3 + T-237 crosswalk / sizes + T-244 revisions (plaster / paint), T-312
(tile), T-329 (backing), T-313 r2 (reveals), T-325 (sills / thresholds and the strip-floor overlap), t211 records
(paint lines).

## 3. Results (files in this folder)

| file | content |
|---|---|
| FACES_T388.csv | 195 faces (63 dry, 11 shaft, 121 wet): length, block / plaster / paint / tile / backing tops (owner) and the drawing plaster / paint tops, family states, the openings each family deducts on the face, the block deductions of the wall |
| OPENINGS_T388.csv | 65 openings: block wall + m2 + state, plaster / paint faces + m2, tile / backing faces + m2, every reveal component (side, m2, state, line), every sill / threshold component (m2, state, line), deducted once per family per face |
| FINDINGS_T388.csv | 18 findings (below), each with its m2 |
| summary.json | counts |

| check | result on the candidate |
|---|---|
| (a) opening twice on one face, any family | **0** (65 of 65 openings once per family per face) |
| (a) split sides close | D-1F-02: 1F-13 0.42 + ST-1F 0.58 = 1.00 m (0.924 + 1.276 = 2.200 m2 = block 2.2000); W03: GF-08 + GF-15 developed room side 6.731 m x 3.65 = 5.9312 + 18.6369 = 24.5681 m2 = T-255 |
| (b) host wall | **0** mismatches (doors on off-line doorway pieces accepted as the door's own crossing) |
| (b) face attribution | **10 OPENING_OFF_ITS_FACE** (5 per family, tile and backing): D-1F-04 on 1F-02 (1.760 m2), D-GF-02 on GF-02 and GF-03, D-GF-10 on GF-10 and GF-11 (HELD) are deducted on a straight face whose drawn line carries no door (T-250 door_m 0) while the same room walks the doorway as its own OFF:DOORWAY piece tiled with no hole. **Room totals unchanged (0.000 m2)**; per face, e.g. 1F-02: face 1F-W23 3.600 instead of 5.360 m2, doorway piece 2.5628 instead of 0.8028 m2. GF-16 / D-GF-14 is attributed correctly (deducted on its doorway piece) |
| (c) one size | **0** mismatches above 0.01 m2; 1 BLOCK_PART_EXPLAINED: W18 block 1.0094 vs hole 1.080 (0.0706 m2: 0.0327 m of the 0.50 m width inside the column outline, T-333 r2 s.5 / Checker 2FD8; the finished face keeps the hole because the column is plastered / tiled as wall) |
| (d) tile above coat | **0**: tile top = backing top on all 73 determinate wet faces (3.35 x 40, 3.65 x 33); 42 faces HELD on both; the 29 annex faces print 3.15 as information only (G2 HELD) |
| (d) paint on full tile | **1**: the pantry paint line HL:WALL_FINISH:GF_07:PAINT (L-c3f7e68ce91a436802e2) stays BLOCKED_RFI blank although every tiled pantry face is tiled to the coat top (already named physically NOT_APPLICABLE by T-315 r2 and T-351; no lane I row carries the state change); 0 m2 now (blank), a double count only if ever valued |
| (d') face closure | **6 FACE_LENGTH_RESIDUAL**, all T-128 r3 open side longer than the T-250 walk's VIRTUAL metres: GF-07 pantry 4.49 vs 4.37 (-0.120 m: the WB-FL0007-FL0008 stretch, 0.05 m on each side, 'wall face drawn by the room contour, no masonry run', + 0.02 on GF-W01) -> tile **-0.438 m2** and backing **-0.438 m2** (owner 3.65); GF-08 dining 5.735 vs 5.595 (-0.140 m) -> plaster and paint **-0.511 m2** each (line BOUNDED / HELD anyway); GF-14 1.245 vs 1.200 (-0.045 m) -> tile and backing **-0.164 m2** each. GF-16 (-0.524 m to the T-074 VERIFIED outline) is explained in T-312 and not counted |
| (e) reveal in face | **0**: per room the off-line doorway metres never exceed the room's door widths (no jamb return walked: 32 / 32 rooms); every window and floor glazing room-side reveal is 0.000 m2 (frames flush with the room face, T-313 r2), so no window reveal can sit on a plaster face; the 22 door reveal lines (FIN.PLASTER jambs + head) + the 5 added by T-326 carry the door reveals once |
| (f) threshold in floor | **0**: largest strip / room-floor overlap 0.000394 m2 (138 strips, T-325) = drawing noise |
| (g) HELD as 0 | **0** |

Block vs plaster heights on the 75 opening-hosting faces stay as T-237 / T-250 merged them (AGREES 4, BAND_EXPLAINED 38
with 43.472 m2 of plastered beam band on 40 faces, BLOCK_HELD 30, PLASTER_HELD 3): not re-derived here. Block top is
known on 52 of the 195 faces (all classes); no wet face among them has its tile top above its block top.

## 4. Verdict proposals (engine vs drawing / ledgers; no freelancer figure is used or needed)

- Opening deductions across block / plaster / paint / backing / tile / reveal / sill-threshold: **ENGINE_RIGHT** (once
  per family per face, one host, one size; the one size difference W18 is physical and cited).
- OPENING_OFF_ITS_FACE (10): **ENGINE_RIGHT at room level, face attribution wrong**: no BOQ line moves (every wall-tile
  and backing line is per room), but any face-by-face use (setting-out, Gate B face re-measure, a future per-wall line)
  would read 1.760 m2 on the wrong face. Proposed lane I fix row (Lead): move the door hole to the OFF:DOORWAY piece
  in the T-312 / T-329 face ledgers' consumer (R-T388-1 b), totals asserted unchanged.
- FACE_LENGTH_RESIDUAL (GF-07 0.120 m, GF-14 0.045 m, GF-08 0.140 m): **UNRESOLVED**: the two merged walks of the same
  contour classify these metres differently (T-128 r3: open side; T-250: wall face). Physically the question is whether
  the 0.05 m wall-end faces of the stretch at the pantry / dining open edge (and the GF-14 open-side ends) are built and
  finished wall. Effect if they are wall: pantry tile +0.438 m2 (+1.35 % of 32.3422) and backing +0.438 m2, GF-14 tile
  and backing +0.164 m2 each (+0.6 % of 26.6544), GF-08 plaster / paint +0.511 m2 each (inside its HELD bound). HELD
  as findings for the Checker: re-measure on P7757.dxf at the T-250 FACE_LENGTH rows (run WB-FL0007-FL0008 stretch, both
  sides; GF-W01 run #2, drawn handle A6 3.00 vs face 3.015) and the GF-14 / GF-08 open-side ends. Never 0, no line
  changed here.
- Pantry paint line: **RULE (UP-FIN-PAINT-001)**: should be NOT_APPLICABLE_WITH_EVIDENCE (lane I state change; 0 m2).

## 5. Limits (named)

- The face table is built from the merged ledgers the candidate pins, not from a fresh candidate run (the run needs the
  private drawings and the T-167 chain); every line id quoted is the candidate's own (ledger columns / snapshots
  T-335 V3.0.21 for the pantry paint line).
- Block top is known on 52 of 195 faces (the T-237 opening-host walls): register v4 carries no height column, so the
  block-vs-coat height on faces without an opening stays with T-237 / T-250.
- The off-line doorway attribution is detected from T-250's door_m on the straight face; a doorway whose drawn door
  sits on the face line is not affected.

## 6. Lessons-register row proposed (ERS s.7)

| what happened | why | rule |
|---|---|---|
| A door hole was booked on a straight wall face while the same room walked the doorway as its own off-line piece, tiled with no hole: room total right, face wrong by w x h | the opening was attached to its host WALL id, the face pieces to the contour walk; the two keys were never joined | Join an opening to the face piece whose contour segment it lies on (R-T388-1 b); assert the room total unchanged when it moves |
| Two merged walks of one contour gave the pantry and dining open edge different lengths (0.12 / 0.14 m) | 'open side' vs 'wall face' is classified per sample in each walk; each ledger closes on its own walk | Every family's face length per room is checked against the one geometric face (d'); a difference is a named item in m2, never absorbed |

## 7. Tests

`tests/t388_face_consistency/test_t388_face_consistency.py` (15): hand fixture NOT the development villa (bedroom dry
3.00 m, bath wet tile 2.80, door 0.80 x 2.10 in the shared wall, window 1.20 x 1.20 in the outer wall; hand values in the
docstring) normal = no finding; mirror (relabelled) = same; adverse: opening deducted twice (1.680 m2), on a third face /
wrong host, tile 0.05 above its backing (0.100 m2), paint line on a fully tiled room, HELD face as 0 refused and never
summed, block / plaster size mismatch (0.210 m2), block part explained (0.360 m2), band above hole, reveal walked into the
face (0.630 m2) and threshold in the floor (0.120 m2), split side not closing, off-line doorway attribution, heights in mm
refused, face-length residual (-0.336 m2; HELD top gives no m2), deduction on an unknown face; the development-villa table
reproduces (counts above, and none of the defect kinds).
