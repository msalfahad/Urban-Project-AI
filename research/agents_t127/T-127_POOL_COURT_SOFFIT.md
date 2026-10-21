# T-127 Pool-court soffit by hand, corrected total of soffits over outside air, finish evidence (development villa; NO REPO CODE)

Worker 2, 2026-10-21. Gate 2 (architectural coverage: ceilings / exterior soffits). Rework of T-121 (REJECTED 2026-10-20
18:40, gate d: the pool-court void deducted was the route G face, not the drawn opening; the gross was never measured by
hand). Rules: owner Q-38 A (the printed 6.57 m line governs the curved glazing), Q-39 C (windows curved on plan on the
outer arc: not needed here, see 1.3), Q-67 A CONDITIONAL (condition MET, verifier 2026-10-20 21:05 on T-123), Q-68 C with
A as the PROVISIONAL estimating method, UP-QTY-STATUS-001, directive 2026-10-20 5.1 (missing scope never zero).
Data (Drive "Alsenan chalet project", read in the scratchpad, never copied here): P7757_DXF_COMPRESSED.zip (plan DXF,
sha256 ab54dd55...), "ST7757 dxf.dxf" (sha256 9f9d1179...), p7757_arch_sheet09.pdf, p7757_arch_sheet10.pdf,
Alsenan_Architectural_P7757_Pages_11-12.pdf (scans). Reproduce: `pool_court_hand.py`, `reconcile_t121_basis.py`
(local frame, printed values only; no client coordinate, name or file in this folder).

## 1. Pool-court soffit (PL-03) from the printed dimensions

Local frame (m): X = 0 at the court face of the 0.20 m west pier / glazing-band ends, Y = 0 at the court face of the south
wall. Printed on the GF plan (sheet 03): horizontal 2000 (X 0 to the OUTER face of the east boundary wall) with the wall
20 / 200; vertical chain 750 + 3500 + 1150 = 5.400 between the north and south wall faces, walls 200 each; pool 3500 from
its west edge to the outer boundary face (radius 1.750, centre X 0.250, Y 1.150 + 1.750 = 2.900); 500 from the pool edge
to the court face of the curved band; band 20 / 200.

### 1.1 Gross (court face to court face): 16.525 m2

| Piece | Calculation (printed) | m2 |
|---|---|---|
| Rectangle between the wall faces | (2.000 - 0.200) x (0.750 + 3.500 + 1.150) = 1.800 x 5.400 | 9.7200 |
| West bulge inside the printed 657 line | circle r = 3.500 / 2 + 0.500 = 2.250 about the pool centre, cut by X = 0 at d = 0.250: r^2 acos(d/r) - d sqrt(r^2 - d^2) = 5.0625 x 1.45946 - 0.250 x 2.23607 | 6.8295 |
| Check of the line | arc length 2.250 x 2 acos(0.250 / 2.250) = 6.5675 m = printed **657** (Q-38 A) | |
| less GF column proud of the north wall face | 0.500 x 0.050 (CAD: T-123 anchor N, verifier-checked) | -0.0250 |
| **Gross soffit seen from the court** | | **16.5245** |

### 1.2 The drawn opening (GF roof slab sheet, B7 ring): 3.690 m2

The bay between the straight beam faces (B8 east face, CB1 inner face, B7 straight leg, B17) is 1.700 x 2.7005 =
4.591 m2 (verifier 4.592). Inside it the B7 ring is drawn as two circles: inner faces r 1.550 about the pool centre and
r 1.735 about a centre 1.435 m east (the centre of the 1F curved window r 1.935), tips rounded r 0.510 (top) / r 0.690
(bottom), the east side closed by the CB1 face. The same inner outline is drawn on the 1F plan with the VOID label.
Area inside the inner faces = **3.6901 m2** (verifier 3.689; the 0.001 is arc polygonisation). Outer faces r 1.750 / r 1.935
(no fillets): ring band 0.6664 m2; the four bay corners outside the outer faces 0.2343 m2 (no slab bars, no label: beam
zone). Ring + corners = 0.9007 = the verifier's "ring band 0.903" (bay less void). Void bounds X -0.050..1.650,
Y 1.580..4.280: inside the gross court area. Radii are CAD (the slab sheet prints no dimension); the 1F plan prints the
ring 200 and the void 3059 / 306 (between other faces, not used as a bound).

### 1.3 Net soffit PL-03 = 16.5245 - 3.6901 = **12.834 m2** (was 14.020 in T-121; verifier CAD basis 14.704)

What the 12.834 m2 is made of (projected plan area; beam widths are CAD faces of the slab sheet):

| Part | m2 |
|---|---|
| slab panels | 7.961 |
| B17 strip (Y 1.130..1.580) | 1.362 |
| CB1 strip inside the court (X 1.650..1.800) | 0.765 |
| B8 strip (west bulge) | 0.704 |
| B7 ring band (inner to outer face) | 0.666 |
| B24 strip (Y 5.100..5.400 inside the court) | 0.519 |
| B7 straight leg | 0.340 |
| B28 strip | 0.282 |
| bay corners outside the ring faces | 0.234 |
| **total** | **12.834** |

Beam SIDE faces (drops below the slab) are not in this plan area (beam depths: T-110 member register; not measured here).
Q-39 C is not needed: the soffit boundary is the band face that Q-38 A fixes (printed 657); no window area is measured.

### 1.4 Why not 18.393 / 14.704 (written reason, acceptance clause)

T-121's gross is a CAD set: slab plate less the V2.9 facade outline. The outline follows the house, so it counts slab that
bears on the walls that bound the court and the recess in front of the curved frame. Those walls are the house's own
facade walls (the GF plan overview: the north wall runs on west along the north facade; the east wall carries the east
facade glazing further south), each with an opening onto outside air. Which faces the V2.9 outline actually walked is not
reproduced here (no engine run in this NO REPO CODE task): the table is a reconstruction that comes within 0.088 m2.
Added back to the hand gross:

| Piece | m2 | Is it soffit? |
|---|---|---|
| hand gross (1.1) | 16.525 | yes |
| recess between the curved frame line (CAD 0.080 m off the printed band face, T-123) and the printed 657 line | 0.561 | exterior, but inside the printed 0.20 glazing band: listed separately (SX-02, M-11), not in PL-03 |
| slab over the east facade wall, X 1.800..2.000 x 5.400 | 1.080 | 0.904 of it is the head soffit of the printed 4521 opening in that wall (4.521 x 0.200, SX-01, M-11); 0.176 sits on the wall piers |
| slab over the north facade wall, Y 5.400..5.600 (less the column) | 0.316 | 0.200 of it is the head soffit of the 1.00 m opening in that wall (CAD width between the column and a 0.30 pier, wall 200 printed; overhead lines drawn, SX-03, M-11); 0.116 sits on the pier and wall end |
| sum | 18.481 | T-121 18.393: +0.088 not traced (the V2.9 outline's walk along the north wall / column 2F87 is not reproduced by hand) |

So the 1.870 m2 between the verifier's net 14.704 and 12.834 is basis, not error in the void: 1.396 m2 of wall tops and
opening heads, 0.561 m2 of frame recess, less the untraced 0.088. The verifier's void (3.689) is confirmed.

## 2. Corrected soffits over outside air (all five places)

| Place | Soffit m2 (hand basis) | Was (T-121) | Basis / status of the geometry | Finish evidence found | Finish status | Option A provisional (Q-68) |
|---|---|---|---|---|---|---|
| PL-01 GF entrance porch | 19.181 | 19.181 | T-121 hand 19.182, verifier 19.198 (not re-measured here) | none | HELD | ext. plaster 19.181 + ext. paint 19.181 |
| PL-02 GF side passage | 5.640 | 5.640 | verifier T-123: 1.560 + 0.240 + 3.600 + 0.240, all roofed; exterior soffit under Q-67 A, condition MET (verifier 2026-10-20 21:05) | none | HELD | 5.640 + 5.640 |
| PL-03 GF pool court | **12.834** | 14.020 | this note, printed dimensions, net of the drawn void 3.690 | none | HELD | 12.834 + 12.834 |
| PL-04 1F roof east edge | 4.374 | 4.374 | T-121 CAD (verifier reproduced 3.189 / 0.873 / 0.312) | none | HELD | 4.374 + 4.374 |
| PL-05 1F roof west / north band | 2.417 | 2.417 | T-121 CAD; what the band is: designer D-25 | none | HELD | 2.417 + 2.417 |
| **Total** | **44.446** | 45.632 | verifier CAD basis 46.316 | | HELD | 44.446 + 44.446 |
| SX-01 head soffit of the 4.521 m boundary opening (sea side) | 0.904 | in PL-03 CAD | 4.521 x 0.200 printed | none | HELD, with the opening reveals | not added |
| SX-02 recess in front of the curved pool frame | 0.561 | in PL-03 CAD | CAD 0.080 x frame arc 6.657 + ends | none | HELD with the glazing reveal / external-strip line (T-123) | not added |
| SX-03 head soffit of the 1.00 m opening in the north facade wall of the court | 0.200 | in PL-03 CAD | CAD 1.000 x printed 0.200 | none | HELD, with the opening reveals | not added |

Option A is the owner's PROVISIONAL estimating method only (Q-68 C): it is shown in its own column, never as a released
finish. No soffit is a gypsum / decor ceiling candidate (Q-68: never interior gypsum on exterior exposure).

## 3. Finish evidence search (Q-68 C): nothing printed for any place

- Plan DXF: every TEXT / MTEXT read (English and the Arabic-keyboard-encoded labels decoded by hand): room names, levels,
  title block, "SEA VIEW", "VOID", court labels; no finish, plaster, paint, ceiling, gypsum or cladding note.
- Structural DXF: the NOTE on each slab sheet (decoded: check the architectural stair / projection details before
  casting; top bars over beams for a third of the span both ways), "CHECK ARCHITECTURAL DETAIL OF PARAPET", the pool
  "5cm INSULATION MEMBRANE": no soffit finish.
- Sheet 09 (north-east elevation), sheet 10 (section A-A), pages 11-12 (section B-B, fence elevation, plan and section):
  scans, no finish legend, no hatch legend, no specification text.
- No finish schedule or specification is among the Drive files. Designer request D-24 already asks the soffit finish and
  build-up per place (figures corrected by this task); until it is answered every place stays HELD.

## 4. Who is right: the freelancer's "ceiling above the swimming pool" 19.154 m2

His row (PLS workbook, statement sheet row 73): count 2 x width 3.14 x length 3.05 = 19.154. In the same sheet 3.14 is
pi in the dome row (6 x 3.14 x 9.65); no printed dimension 3.14 or 3.05 bounds the court; 3.05 is printed on the 1F as the
curved window height. Against the hand figures: vs net 12.834 m2 +6.320 m2 (+49.2 %); vs the whole court ceiling with the
void left in, 16.525 m2, +2.629 m2 (+15.9 %). Because 19.154 exceeds the entire ceiling of the court on any face-to-face
basis the drawings allow, the proposal is **ENGINE_RIGHT (hand calculation above)** for the ceiling quantity, with a note
for the verifier: if his row is not a ceiling but the curved upstand round the 1F void (pi x about 2 m x 3.05 m high
would match), it is a RULE_DIFFERENCE on a different surface, and that surface is then missing from our ledger. Not
decided here.

## 5. Learned / missing

- A soffit is the ceiling the space sees: measure between the faces of the walls that bound the space, not "plate outside
  the house outline". Where a court is a notch in the house open through wall openings, the outline method can count the
  tops of its bounding walls and the opening heads
  (here 1.396 m2, +8.4 % on the court).
- A void inside a beam ring is the area inside the INNER faces (3.690 m2), not the route G face (4.373 m2, which is the
  bay less the corners); the ring band and the bay corners are beam soffit and stay in the ceiling.
- Missing: finish (HELD, D-24); beam side faces under the soffits (T-110 depths); SX-01 / SX-02 / SX-03 need their reveal lines;
  the 0.088 m2 residual of the T-121 CAD set; the porch was not re-measured in this run (T-121 and the verifier agree
  within 0.017 m2).
