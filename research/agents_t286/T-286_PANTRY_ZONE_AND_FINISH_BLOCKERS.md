# T-286: the plaster / paint blockers the drawings settle (W03 room-side line, W06 wedge) and the floor-area RFI gap G4 (GF pantry "doorway zone")

Worker 2, 2026-10-25. Drawing: Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55),
p7757_arch_sheet03.pdf (image-only, read at 200 / 300 dpi). Engine faces: released ARCH_TAKEOFF_V2.9 re-run on this
DXF (Python 3.11.17). Code: `pantry_zone.py` (rules R-T286-1 .. 3), `alsenan_t286.py` (Alsenan run), `summary_t286.json`
(handles, metres, coordinates relative to the pantry box corner only). Tests: `tests/t286_pantry_zone/test_t286.py`.
Nothing applied to any candidate or released line; no engine / registry file touched.

## 0. Result in one paragraph

All three named blockers are settled by the drawings; no designer row and no owner question is needed. (a) W03 and
(b) W06 were already settled by T-250 (MERGED 47390c9b, Checker own re-walk 2026-10-24 10:40): the SCOREBOARD v2
CLOSABLE rows 3 / 4 still cite the earlier T-237 state (Checker 00:12), a stale citation. My own re-read of W03
reproduces the merged reading: room-side line 6.7291 m (Checker own 6.7294, T-128 walk 6.731). (c) G4: the 1.100 m2
"pantry doorway zone" is not a doorway: it is the floor under the drawn east pantry counter, cut out by the engine
between the counter outline and a zone line the drawing never draws; it lies wholly inside the printed pantry box and
is WET pantry floor by owner Q-37 A. Candidate floor-area effect when integrated: internal floor 380.364 -> 381.464 m2
(+1.100, +0.29 %), all on the wet line; the pantry box then closes 13.500 - 0.045 column = 13.455 m2 with residual
-0.0001 m2. Plaster / paint: no m2 moves; their one remaining named blocker is the roof datum (designer D-39, 18 faces).

## 1. W03 room-side line and W06 wedge (plaster, paint): already settled, stale citation

| Item | Scoreboard text (from T-237, Checker 00:12) | Settled by | Own re-read this run | m2 effect |
|---|---|---|---|---|
| W03 | "split 6.731 vs drawn 6.5675" | T-250 MERGED 47390c9b: room face = glass line 27D (r 2.450, arc 6.7918) + returns - partition end = 6.726 .. 6.738; Checker own 6.7294 | 27D polyline 6.9251 (arc 6.7918 + returns 0.0917 + 0.0416) - partition 2E2 / 2E4 end on the arc 0.1960 (both ends on r 2.450 within 0.03 mm) = **6.7291 m** | none: T-128 deducts 6.731 (+0.0019 m x 4.30 = 0.008 m2, below rounding) |
| W06 | "W06 wedge" | T-250 MERGED: glass 3E6 (+3E3 / 3EC) bounds GF-13 (wedge B) only; GF-12 1.26 m away; T-128 / T-209 already deduct it in GF-13 | not re-derived (merged Checker verdict cited, WORKFLOW_CONTROLS s.10.5) | none |

Cause of the 0.164 m named in the row, by physical element: 6.5675 is ARC 201 (layer 5, r 2.250, the POOL-side face of the
0.20 glazed band, where '657' is printed); 6.731 is the room-side walk on the ROOM-side glass line 27D (r 2.450). Arc
6.7918 - 6.5675 = +0.2243 (the other face of the band, other radius and sweep), + jamb returns 0.1333, - partition end
0.1960 = +0.1616 m (6.7291 - 6.5675). It is a RULE_DIFFERENCE between trades (window line by owner Q-38 A on the printed
6.57; finishes on the room face), not a mismatch. Status: DRAWING-CONFIRMED (T-250) with the Checker's own 6.7294.
The scoreboard row should drop W03 and W06 and keep only DCR-6 (roof datum, designer D-39 item 3, 18 faces).

## 2. G4: the GF pantry "doorway zone" 1.100 m2

### 2.1 Physical element (ERS s.2 step 1)

GF, open American pantry west of the dining room (UP-PANTRY-001), printed 450 x 300 (DIMENSION 5E1 4500: A6 -> north
face 158; DIMENSION 5D5 3000: west wall face AE -> layer-5 line B3). Engine record (V2.9 floor_areas, strip
SITE-0a31aaa10796d33a): area 1.100, class UNATTRIBUTED, opening OP-003 (PASSAGE 11.22 m), failed check
OUTSIDE_OPENING_BOX, disposition BLOCKED_RFI, "a strip in the wall thickness that no single opening kind bounds"; carried
in V2.9 inside the ARCH.THRESHOLD twin of OP-003 (measured 1.27, no net quantity) and retired with that twin in T-240.

### 2.2 What the drawing prints around it (sheet search)

Polygon relative to the box's south-west corner (x east, y north, m): (1.6, 0) (3.0, 0) (3.0, 1.3) (2.5, 1.3) (2.5, 0.5)
(1.6, 0.5); 1.4 x 0.5 + 0.5 x 0.8 = **1.100 m2**. Every edge read on P7757.dxf:

| Edge | Length m | Drawn line | What it is |
|---|---|---|---|
| south | 1.400 | A6 (layer 1) | south wall face (neighbour wall) |
| east | 1.300 | B3 (layer 5) | pantry east edge; also the counter's outer edge |
| north | 0.500 | none | an engine zone line: the garden-band edge lines A8 / A9 / 4B4 stop 3.800 m EAST of the box (x of their west ends); nothing is drawn across the pantry at that line on the DXF or on sheet 03 |
| west / inner | 0.800 + 0.900 + 0.500 | B4, AA, B2 (layer 5) | the east counter outline: B2 / AA / B4 / 15D with B3 and A6 close an L counter 1.400 x 0.500 along the south wall + 0.500 x 2.500 along B3 = 1.950 m2; two bar stools (LWPOLYLINEs 174 - 177) on the dining side of B3 |

No door block, no jamb, no glazing line and no wall line bounds it (the pantry's only door, D120 33E, is in the north wall,
3.2 m north of the piece). Sheet 03 (300 dpi) draws the same counter L with the two stools beyond it and no line across the
pantry. Searched: P7757.dxf layers 1, 2, 5, W, S-COL.BON, DIMENSION and blocks in a 6 x 7 m window round the box;
sheet 03 at 200 / 300 dpi. ST7757 not needed (a floor finish piece, no structural edge).

### 2.3 Reconstruction and reconciliation (ERS s.2 steps 3-4)

| Piece inside the printed box | m2 | What it is physically | Class |
|---|---|---|---|
| printed box 3.000 x 4.500 | 13.500 | | |
| column 2FAE notch 0.900 x 0.050 | -0.045 | column | no floor |
| GF-RC06FED (T-240, moved whole) | 2.800001 | open pantry floor, south part | WET (Q-37 A) |
| GF-RC99C2A part (T-240) | 8.955 (engine 8.954867) | open pantry floor, north part, incl. the west counter L 1.905 and the east counter's upper 0.750 | WET (Q-37 A) |
| OP-003 strip part (T-240) | 0.600 | engine strip along the same undrawn line, incl. 0.100 of the east counter and 0.058 of the west counter | WET (Q-37 A) |
| **doorway zone** | **1.100** | floor under the east counter, below the undrawn line (1.0999 inside the counter outline, 0.0001 CAD offset) | **WET (Q-37 A)** |
| residual | -0.0001 | CAD offset | |

Counter footprints are not deducted anywhere else in this line: the west counter (1.963 net of the column) and the
upper 0.850 of the east counter already sit in the merged wet pieces; the Checker-VERIFIED kitchen GF-RA3AD49 9.630 m2
(T-180 slot) is wall face to wall face with its counter lines 11C / 137 inside; T-114 (MERGED) "counters not
deducted, like every wet area"; UP-CER-001 deducts only a stair footprint, a marble threshold and another finish's
area. Holding this one piece of counter footprint while the other 2.813 m2 is carried would treat one physical
condition two ways. Owner method and drawing method agree here: Q-37 A wets the printed box; the drawing places the
piece inside it.

### 2.4 Status and before / after (candidate V3.0.15, NOT RELEASED; nothing applied by this task)

| Line | Before | After (when lane I integrates) | Status |
|---|---|---|---|
| Floor area internal (m2) | 380.364 + 1.100 HELD (RFI) | **381.464** (+1.100, +0.289 %) | DRAWING-CONFIRMED geometry; class by owner Q-37 A |
| of which wet floor tile (pantry) | 12.354868 | 13.454868 (= box 13.455, residual -0.0001) | idem |
| Pantry membrane (Q-37 A, own line) | 13.50 | 13.50 unchanged (already the whole box) | unchanged |
| Plaster / paint | - | no change | - |

Who is right (floor, this piece): the engine's BLOCKED_RFI "doorway strip" is an ENGINE DEFECT (an undrawn zone line +
a fixture outline read as strip boundaries); proposal ENGINE_WRONG_CLASS, settled by the drawing (no RFI). Freelancer:
not consulted for the class (he has no pantry wet row: Q-37 problem statement), no comparison figure changed by him.

Side finding (no quantity): the V2.9 ARCH.THRESHOLD twin of OP-003 (measured strips 1.27, no net quantity) was retired
in T-240 as "the same strip billed twice"; it actually held three other faces: this 1.100 and 0.130 + 0.040 inside the
body of the GF-W16 pier between the two pantry windows (layer-1 lines AF / A0, wall, no floor). The retirement moved no
quantity; the record text is imprecise, nothing to undo.

Side observation (no quantity): the DXF draws the pantry east line B3 / AD up to the north wall (4.500 m); sheet 03 draws
it only to the end of the counter (about 3.0 m from the south wall). The pantry box stays the printed 450 x 300 (Q-37 A),
so no line moves.

## 3. Rules, tests, lessons (ERS s.4)

- R-T286-1 (any villa): a floor piece is a doorway / threshold strip only when an opening jamb bounds it; a piece bounded
  only by wall faces, fixture outlines (counter, joinery, furniture), a printed room edge and undrawn zone lines lies in
  the room whose printed box contains it and takes that room's class with its full area; outside every box, across two
  boxes or in a HELD-class room it is HELD with its area kept.
- R-T286-2 (any villa): the room-side line of a curved opening = the drawn line the room touches (arcs as arcs) + jamb
  returns - partition ends on it; a schedule width, a dimension text or the band's other face is refused as the room face
  (extends R-T250 to a room on the concave side, where the room face is SHORTER than the outer face).
- R-T286-3: totals report established and HELD apart; a HELD item as 0 is refused.
- Tests (29, villa S, not Alsenan): counter-bounded piece -> wet room floor (1.440, mirror, two rotations + shift), dry
  room; adverse: jamb present -> strip unchanged, piece across a box / outside every box / two boxes / HELD class -> HELD
  with area kept, class without source, mm polygon, stated area mismatch, open perimeter, uncited drawn bound, unknown
  bound kind, closure with a None piece, closure missing a piece; curved window room side 4.150 < outer 4.500, mirror,
  partition end from arc points, point off the arc, schedule / text / no source refused, other face refused, mm refused,
  wedge room 5.200 + 1 HELD, HELD as 0 / UNKNOWN as 0 / no quantity / bad status refused; committed summary consistent.
- Lessons row (proposed): 2026-10-25 | a 1.100 m2 pantry piece sat 'BLOCKED_RFI doorway strip' for days and reached the
  RFI list with no question text | the engine extended a band edge line 3.8 m beyond its drawn end and closed the piece on
  counter lines, then named it after the nearest opening id | a strip is a strip only where an opening jamb bounds it;
  fixture outlines and undrawn zone lines are no floor boundary; the piece takes the class of the printed room box it lies
  in; before a piece goes on an RFI list, every edge is matched to a drawn line by handle | t286 | OPEN until integrated.
  Second row (process): a CLOSABLE row kept citing a blocker (W03, W06) for a day after the merge that settled it
  (T-250, 10:40) | the row text was carried forward from the T-237 verdict | a blocker citation names the verdict it rests
  on and is re-checked against every merge since | none (scoreboard text) | for the Checker / Lead.

## 4. For the Checker (re-measure from the drawing, not from these numbers)

1. W03 room-side face on P7757.dxf: LWPOLYLINE 27D (layer W) length with its bulge arc, the partition faces 2E2 / 2E4
   ends on it, ARC 201 for the pool face (6.7291 here; your 6.7294 at 10:40).
2. The pantry piece: its six edges against A6, B3, B4, AA, B2 and the west ends of A8 / A9 / 4B4 (3.800 m east of B3);
   the counter outline on sheet 03; the box closure 13.500 - 0.045 - 2.800 - 8.955 - 0.600 - 1.100.
