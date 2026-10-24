# T-282 formwork: ground-beam side forms closed on each carrier's drawn face per edge (lane S; Alsenan; every villa)

Worker 1, 2026-10-24 22:24 .. UTC, branch `agents/task-T-282`. Research only: nothing wired, no BOQ line changed, no
method version. Development villa, not an accuracy claim. Delta ledger against the merged formwork r4 (T-264).

Files: `face_trace.py` (rules R-FACE-CLOSE-1 / -SNAP-1 / -OWN-1 / -END-1 + the generic tracer), `t282_extract.py`
(private DXF -> `ALSENAN_EDGE_INPUT.json`: lengths, stations from each band's start, angles, handles; no coordinates, no
client text), `formwork_t282.py` (villa Q `--check` + the Alsenan delta from committed inputs),
`DELTA_T282_GROUND_BEAM_SIDES.csv` (126 rows: every span x side A / B + every end face), `summary_t282.json`. Tests:
`tests/t282_formwork_edges` (14: villa Q normal + adverse, rotated 30 deg / mirrored / offset; Alsenan pinned; committed
outputs = a fresh build).

Repeat: `python3 -I research/agents_t282/t282_extract.py <ST.dxf> --out research/agents_t282`, then
`python3 -I research/agents_t282/formwork_t282.py research/agents_t282`. Source: Drive "Alsenan chalet project" /
"ST7757 dxf.dxf" (sha256 9f9d1179..., = T-141 DXF_SHA); the 59 spans and their face-to-face lengths are rebuilt with
the T-242 / T-141 code and checked equal to the committed T-242 input before anything is written.

## 1. Physical element and the question (ERS s.2.1, s.3)

A ground-beam side form is the concrete face along ONE drawn edge line of the band, between the faces of what the beam
meets on THAT edge. Formwork r4 billed both sides of each run at one length L (T-242: V2 face to face, cut square at
the support's outermost station across the width, or the T-242 end-adjusted length), tees as separate 0.30 x min(D_in, D)
covers. Question (Lead): does r4 carry the square-cut faces and the sliver members the Verifier found in T-276 r1?

Two drawing-derived methods side by side (no owner manual method exists for formwork):

- **W, edge walk**: each edge line walked from mid-span to the carrier V2 names at that end (column, band, ring).
- **T, traced faces**: the boundary of the union of every drawn member (straight bands between their own edge lines,
  each edge closed on its named carrier; curved bands between their own arcs as arcs; columns; the lift ring), every
  boundary piece given to ONE owner: column face (within 1 mm) -> lift wall -> the band edge it lies on -> the band's
  own end. Junction zones (tees, crossings, a band framing into the ring) are not boundary: no square cut, no earth
  pocket can arise. Comparable length T' = traced side + the tee gaps on that side (r4 deducts tees on its own rows).

Rules (proposed, research scope, any villa; every face-tracing trade: formwork, waterproofing, plaster):
**R-FACE-CLOSE-1** a member ends on its carrier's drawn face on each of its own edges; a square cut is refused.
**R-FACE-SNAP-1** an offset thinner than 1 mm between two outlines is not a member (a column 0.05 mm inside a band edge
is the column's face); 1 mm or more = two faces; a curved face is never snapped to a straight one at a tangent point.
**R-FACE-OWN-1** one owner per face piece (R-CONC-OWN-1 order); a tee covers its carrier over the incoming band's width
ON the carrier face (b / sin angle; on an arc, the arc between the incoming edges' hits). **R-FACE-END-1** an end face
exists only where a band stops with nothing drawn against it (free end, gap to a column, end on a footing below, end
beside a partial-width column); a drawn line stopping short of its named carrier is closed onto it (cap 2 x width).

## 2. Result: r4 vs the drawn faces (m of face, m2 = m x the r4 depth of that run)

106 of the 118 span-sides (59 spans x A / B) AGREE with r4 within 2.5 mm (both methods); 12 side rows and 8 end-face rows change:

| Run, side | r4 L | W | T' | delta m | r4 depth basis | delta m2 | status | cause |
|---|---|---|---|---|---|---|---|---|
| 177+7CD#2 A (frames into ring ARC 158) | 1.5367 | 1.7557 | 1.7558 | +0.2191 | HELD 0.30 / 0.40 | +0.066 .. +0.088 | DRAWING-CONFIRMED | square cut at the shorter edge (Verifier T-276: LINE 177 to -1.944 vs -2.163) |
| 17E+17F#1 A / B (col 1EF oblique, 45 deg carrier 176+7E6) | 2.4269 | 2.685 / 2.7648 | 2.687 / 2.7668 | +0.2601 / +0.3399 | HELD 0.30 / 0.40 | +0.180 .. +0.240 | DRAWING-CONFIRMED | each edge on its own carrier face |
| 180+181#1 B (two 45 deg carriers) | 0.789 | 1.387 | 1.389 | +0.600 | HELD 0.30 / 0.40 | +0.180 .. +0.240 | DRAWING-CONFIRMED | B line drawn 0.110 short of 180D+180E: closed on it; the r1 'end face' does not exist |
| 182+183#1 A | 2.0732 | 2.3722 | 2.1431 | +0.0699 | HELD 0.30 / 0.40 | +0.021 .. +0.028 | DRAWING-CONFIRMED | the edge meets band 15D+7C8 0.229 m before 170+7C3 (no face there; W overstates) |
| 170+7C3#4 B (exterior, above N.G.) | 3.25 | - | 3.55 | +0.300 | CALC 0.95 | **+0.285** | DRAWING-CONFIRMED | column 17C0 does not reach edge B; the face runs on beside it to 1E8 |
| 1811+1812#1 A | 1.3 | - | 1.8 | +0.500 | HELD 0.30 / 0.40 | +0.150 .. +0.200 | DRAWING-CONFIRMED | column 1E8 partial width; face runs on to 17C0 |
| 13E+7D6#1 B / #2 B | 4.3 / 0.5 | - | 4.45 / 0.65 | +0.15 / +0.15 | HELD 0.40 / annex CONFLICT | +0.060 / m only | DRAWING-CONFIRMED | column 211 partial width (beside-support halves) |
| 10B+7D1#1 A, 7D4+F8#2 A (annex L corner) | 1.2 / 4.25 | 1.499 / 4.25 | 1.5 / 4.55 | +0.3 / +0.3 | annex CONFLICT | m only | DRAWING-CONFIRMED | the two outer faces of the corner square, in neither r4 run |
| END 15D+7C8#1 (on footing), 17C+7E3#1 (on footing), 177+7CD#1 (gap to col 1EC), 1811+1812#1 (free) | 0 | - | 0.300 each | +1.200 | HELD / FORMED | +0.12 FORMED; +0.39 .. +0.42 HELD | DRAWING-CONFIRMED | free end faces, in no r4 row |
| END beside partial columns: 15E+15F#1 0.100, 170+7C3#4 0.2318, 1811+1812#1 0.0972 | 0 | - | 0.4290 | +0.429 | HELD / FORMED | +0.220 FORMED; +0.069 .. +0.079 HELD | DRAWING-CONFIRMED | band end not covered by the column |
| 15D+7C8#1 B | 2.9 | 1.8999 | 2.8499 | -0.0501 | HELD 0.40 | -0.020 | HELD | not settled (start on footing F 1B2B; the r4 L is the T-242 adjusted length) |
| 13E+7D6#2 END | 0 | - | 0.0017 | +0.0017 | annex CONFLICT | m only | HELD | a 1.7 mm piece, above the snap |

**Totals of the change (m2, never summed across statuses):** r4 CALCULATED (above N.G.) **+0.285** (one face);
OQ-10 FORMED alternative **+0.340** (two end faces; EARTH_CAST alternative unchanged 0); HELD ranges **+1.116 .. +1.355**
(+ -0.020 HELD on 15D+7C8#1 B); annex CONFLICT runs **+0.750 m** of face (no depth: m only). Physical faces added:
+3.189 m of side face, +1.629 m of end face (DRAWING-CONFIRMED). No change is applied to any BOQ line.

**Ring ARC:157+158 (the Verifier's T-276 case):** inner face 157 = 6.5674 m (= r4; a tangent-point snap at column 17BA
would have taken 0.0079 m, refused by R-FACE-SNAP-1); outer face 158 traced **5.9056 m** = 109.750 -> 176.628 (2.9765)
+ 183.372 -> 211.992 deg (1.2738) + 220.294 -> 257.542 deg (1.6578) (Verifier own 5.9055 m: +0.0001); framing zone of
band 177+7CD on the arc = **0.3715 m** (hits r 2.5501 / 2.5496 at 220.318 / 211.971 deg); 5.9056 + 0.3715 = 6.2771 vs r4
6.2775 (-0.0004): r4's outer face is right as a total, its tee cover is not: r4 covers 0.30 x min(D_in, 0.95) = HELD
-0.12 .. -0.09, drawn width 0.3715 -> -0.149 .. -0.111 (delta -0.029 .. -0.021 m2, stays HELD with D_in). The ring's
west end piece 0.3226 m (inner arc ends 96.382 deg, outer 109.750 deg on LINE 7C3 / column 17C0) is not settled: HELD
by name.

**Tee covers on the carriers (r4 0.30 per tee):** three 45-degree tees cover 0.4243 m each (0.30 / sin 45) on 176+7E6
A / B and 180D+180E B: r4 under-deducts 0.1243 x min(D_in, D) each (HELD rows, -0.037 .. -0.050 m2 each). Carriers with
drawn tee zones and NO r4 cover row: 109+7CB#1 (0.1278 A + 0.100 B, FORMED 0.40: r4 overstates by up to
0.2278 x 0.40 = 0.091 m2; the incoming depths are not pinned here: HELD), 114+115+7DF#1 B 0.100 (HELD run), annex
13D+7D2#1 (0.600), 7D4+F8#1 (0.300), 7D4+F8#2 (0.600) (annex CONFLICT, m only). Partial zones 170+7C3#2 A 0.5615 (two
covers 0.600 in r4, -0.0385), 170+7C3#3 A 0.430 (one cover 0.300, +0.130), 15D+7C8#1 0.4127 (one 0.300, +0.113): listed
for the Checker, not quantified.

**Sliver census (R-FACE-SNAP-1):** over every band x every parallel column face within 5 mm, exactly ONE real offset
exists: COL:255 vs band 7D0+FC, 0.052 mm over 0.700 m (the T-276 'GAP piece'). r4 is not affected (V2 spans already
treat COL:255 as a full-width support, and the traced union gives the 0.700 m to COL:255). All other coincident faces
are below 1 micron (the same line). A closing of the union by 0.5 mm removes slits between outlines drawn a hair apart
(the first trace without it read several +0.300 m 'faces' inside such slits).

## 3. Reconciliation (ERS s.2.4) and verdict proposals

- r4 vs drawn faces: the whole difference is end treatment: (a) a square cut at the support's outermost station where a
  carrier is oblique / curved or a column covers part of the width (+3.189 m); (b) free ends never billed (+1.629 m);
  (c) tee covers at 0.30 where the drawn zone is wider (oblique, arc) or where no cover row exists. Residual between W and
  T on rows where both exist: <= 2 mm (the walk reads a 45-degree face on a +-1 mm strip), except 182+183#1 A where W
  stops at the named carrier through another member (T right, W wrong) and 15D+7C8#1 B (HELD).
- Freelancer: no formwork row in any workbook (r3 / r4): FREELANCER_NO_ROW; no %.
- Verdict proposals: ring outer face and 177+7CD#2 A: HAND (traced) RIGHT, r4 tee cover width WRONG (0.30 vs 0.3715);
  oblique / partial-width runs: HAND RIGHT, r4 square cut WRONG by the m above; free end faces: r4 OMISSION; COL:255
  sliver: r4 RIGHT (unaffected), the rule protects the traced trades.

## 4. Held (never 0) and missing

HELD: 15D+7C8#1 side B (-0.0501 m), the ring west end piece 0.3226 m, 13E+7D6#2 end 1.7 mm, every cover width change
(depends on D_in), the carriers with no r4 cover row, every annex delta (depth CONFLICT, m only). Not done here: slab
level beams (r3 / r4 G faces come from the T-139 drawing-face walk, which already ends both edges on the carrier, T-264
row 2; a sliver census of the slab sheets is not measured), soffits (ground-beam soffits on blinding: no form), the
neck faces (neck line HELD on Q-21 C).

## 5. Checker re-measure (Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf', GROUND BEAMS PLAN)

(a) the ring junction: ARC 158 (R 2.55) pieces 109.750 -> 176.628, 183.372 -> 211.992, 220.294 -> 257.542 deg (outer face
5.9056 m), LINE 177 / 7CD end points on the arc (framing 0.3715 m), band 177+7CD#2 side A on LINE 177 from column
COL:245's face to the arc = 1.7558 m less the 7E7+7E8 tee 0.300 = 1.4558 m traced; (b) one oblique run: 17E+17F#1, LINE
17F (A) 2.687 m and LINE 17E (B) 2.7668 m between column 1EF's faces and band 176+7E6's 45-degree face (tee 182+183 0.300
on B); (c) the sliver: COL:255 outline vs LINE FC / 7D0 offset 0.052 mm over 0.700 m.

## 6. Lessons register row (proposed, ERS s.7)

2026-10-24 | Formwork r4 billed both sides of 10 ground-beam runs at one square-cut length (+3.189 m of side face
missing), billed no free end face (+1.629 m), and covered oblique / arc tees at 0.30 (0.4243 / 0.3715 drawn) | Spans
were cut at one station per end and both faces took the run length; tee covers took the incoming width, not its width
on the carrier face | R-FACE-CLOSE-1 / -SNAP-1 / -OWN-1 / -END-1 (any villa; formwork, waterproofing, plaster) |
tests/t282_formwork_edges (normal: oblique carrier per edge, band into a ring at two stations, free end; adverse: square
cut refused, a column 0.05 mm inside a band edge -> column face (without the snap 0.5 m false beam face), a line 0.700 m
short never invented; rotation / mirror) | READY (Gate A pending).
