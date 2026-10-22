# T-159 The outside of the house, side by side: length, height and area of every facade side (development villa)

Worker 2, 2026-10-21. Gate 1 / 2 (facade run integrity; architectural coverage: facade). NO REPO CODE: research files
only (`research/agents_t159/*`); no engine, rule or released quantity changes. Rules: owner Q-07 (b) (facade band
slab top to slab top), Q-64 B CONDITIONAL, Q-67 A CONDITIONAL, Q-65 C (parapet material, not used: areas only),
Q-68 C (soffits / slab edges HELD), UP-FACADE-001 (the run is the outer face, openings included; plinth an RFI),
UP-GEN-003 1.1.0 (PLASTER_PAINT openings: owner decision pending -> net HELD), UP-QTY-STATUS-001, WORKFLOW_CONTROLS
section 5 statuses, owner directive drawing-first. Data (Drive "Alsenan chalet project", read in the scratchpad, never
copied here): P7757_DXF_COMPRESSED.zip (plan + SE / NW elevation frames, DXF sha256 ab54dd55...31cc4),
p7757_arch_sheet09.pdf (NORTH EAST ELEVATION), Alsenan_Architectural_P7757_Pages_07-08.pdf page 1 (SOUTH WEST
ELEVATION, sheet 07), p7757_arch_sheet10.pdf (decoded, not needed: every level used is printed on the elevations).

## 1. What the drawing gives against the freelancer (exterior wall faces, m2, gross: openings included)

The engine has no facade area (ARCH.FACADE: 4 lines BLOCKED_RFI, "FACADE_HEIGHT_NOT_IN_THE_DRAWING") and its GF run is
still 98.886694 m (-7.000 m, -6.6 %, the side passage, T-109 / T-123, not wired). So the comparison is the
drawing-derived hand table below against the freelancer's exterior plaster rows (file PLS rows 51-93 of
tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json: height x length per elevation).

| Elevation (outward facing) | Drawing, measured | Drawing, HELD (range) | Freelancer wall rows | Measured vs freelancer |
|---|---|---|---|---|
| NE (neighbour side, sheet 09) | 323.044 | 0.088 .. 0.104 | 258.000 | +65.044 (+25.2 %) |
| SE (street, DXF frame) | 197.829 | 0 | 166.612 | +31.217 (+18.7 %) |
| SW (court side, sheet 07) | 296.856 | 1.838 .. 7.212 | 275.160 | +21.696 (+7.9 %) |
| NW (sea view, DXF frame) | 204.804 | 4.896 .. 5.945 | 185.040 | +19.764 (+10.7 %) |
| freelancer "roof facade" 4.70 x 17.75 (part of the 2F faces) | in the rows above | - | 83.425 | - |
| **All faces** | **1,022.534** | **6.822 .. 13.261** + 13.079 m of 1F slab edge over open air (height not printed) | **968.237** | **+54.296 (+5.6 %)** |

- Owner manual convention side by side (Q-07: bands start at the floor; UP-FACADE-001 keeps the plinth an RFI):
  storey + parapet bands **955.797 m2** (= 1,022.534 - 66.736 m2 of plinth from the printed outside level to the
  printed F.F.L.). Geometric (owner's T-159 request: ground to top) **1,022.534 m2** measured.
- Per floor: GF 105.886694 m of faces, 561.041 m2 (+4.952 .. 6.013 HELD); 1F 63.168865 m, 321.432 m2 (+1.870 .. 7.248
  HELD + slab edge); 2F 29.800 m, 140.060 m2.
- The freelancer's other exterior plaster rows are a different scope and are not in the comparison: frames 28.868,
  dome 181.806, pool soffit 19.154, roof parapets 146.659 (1.70 / 0.70 m heights, not printed), boundary fence
  107.240, drip edge 50.876 (total with the walls 1,502.840 m2).
- Verdict proposals (for the Checker): the totals are a **RULE_DIFFERENCE** (he takes one plane per elevation at
  whole-facade heights 14.40 / 11.85 / 10.00 / 9.80 / 6.00 / 5.25 / 4.80; the drawing has set-back faces that each
  carry their own printed band). Inside it, **HAND_RIGHT** proposals with the printed figure: NE house - his 10.00 x
  19.20 = 192.000 against the GF face 19.37 x 6.00 (ground to the GF parapet, sheet 09 '100 + 450 + 50') = 116.220
  plus the 1F face set back 1.50 m, 19.27 x 5.50 (+5.50 to the +11.00 parapet, sheet 09 '130') = 105.985: 222.205
  (+30.205); the 2F faces are 29.80 x 4.70 (+9.70 to +14.40, '420 + 50' on all four elevations) = 140.060 where his
  rows give 4.70 x 17.75 plus the parts inside his 14.40 rows. **UNRESOLVED**: his parapet rows (1.70 / 0.70 m) -
  the drawing prints 0.50 above each roof and 1.30 above the 1F roof; which faces his parapet rows hold is not
  written in the workbook.

## 2. How each side was made

1. **Sides.** The released engine's outline per floor (ARCH_TAKEOFF_V2.9, unchanged to V2.12), split where the face
   turns (straight runs on one line, arcs on one circle; a run includes its openings, UP-FACADE-001). Arc sides carry
   the true arc length. The sides re-add to the runs exactly: GF 27 sides = 98.886694 m, 1F 12 = 63.168865 m, 2F 4 =
   29.800000 m (difference 0.000000 m). On the GF the passage mouth (OP-007, 1.200 m) and the boundary-wall end
   (OP-001, 1.200 m) are not faces and the two passage faces are added (4.700 + 4.700 m, owner Q-67 A, T-109 /
   T-123): GF faces **105.886694 m** = the geometric perimeter. Billable run (Q-64 B) 105.786694 m only once a reveal
   line measures the two 0.050 m notch returns (GF SE-5 and the first 0.050 m of NW-3); none does (T-123), so both
   stay in the faces here and are named. 1F: the window recess returns NE-1 / SW-1 (0.080 + 0.080 m, D-N10-01, T-014)
   stay in the faces (geometric 63.168865 m; closed on the face line 63.008865 m).
2. **Facing.** North arrow on the plan frames (N to the lower right): plan +x (the end marked SEA VIEW) = NW
   elevation, -x (street) = SE elevation, +y = SW (sheet 07), -y = NE (sheet 09); the DXF elevation titles confirm SE
   and NW. Sides are named by facing and order round the outline (NE-1, NE-2, ...).
3. **What stands above / below each side**, computed from the outlines (`t159_sides.against_upper`), not typed in:
   FLUSH (the upper face continues on the same line), COVERED (the upper plate is over the face: a porch soffit, the
   passage roof), EDGE (a roof edge: the face ends at that roof's parapet). Arcs read by hand (2).
4. **Heights from printed levels only** (each band in FACADE_SIDES_T159.csv with its sheet):

| Level | m | Printed on |
|---|---|---|
| external ground | +-0.00 | all four elevations; plot corners on the GF plan |
| courts, forecourt, porch, passage, pool court | +0.15 | GF plan marks; SE elevation chain under the stair tower; NW elevation |
| pool rim | +0.30 | NW elevation, pool axis 115 / 70 |
| annex F.F.L. / house GF F.F.L. | +0.30 / +1.00 | GF plan; SE chain 30 / 400 / 50; chains 100 / 870 / 420 / 50 |
| annex roof / annex parapet top | +4.30 / +4.80 | 1F plan, SE elevation, sheet 09 / '480' on SE, 07, 09 |
| 1F F.F.L. = GF roof / GF parapet top | +5.50 / +6.00 | 1F plan, NW 100 + 450, '550' on 07 / 09 / NW 550 + 50, '50' on 07 / 09 |
| 2F F.F.L. = 1F roof | +9.70 | 2F plan, 100 + 870 on all four |
| 1F parapet top, NE and SW faces | +11.00 | '130' above +9.70 on sheets 09 and 07 |
| 1F parapet, SE and NW faces | wave / steps | **no dimension** except +11.10 / +11.30 at the SE face's NE end ('6800' from +4.30, '200') and '110' on NW: the area above +9.70 is integrated along the CAD top line of the DXF elevation frame (status DRAWING-CONFIRMED, CAD geometry); SE 7.807 m2 over 7.500 m (mean +10.741), NW per side (mean +11.00 / +10.80 / +10.148) |
| 2F parapet top | +14.40 | '1440' and 420 + 50 on all four (NW: 3200 to +14.20 + 200) |

   Bands per side: GF = plinth (outside level -> F.F.L.) + storey (F.F.L. -> +5.50 where the 1F is flush or over it,
   Q-07; -> the roof parapet top +6.00 house / +4.80 annex where it is a roof edge). 1F = +5.50 -> +9.70, plus the
   parapet above +9.70 where it is a roof edge, plus +4.30 -> +5.50 where the 1F face stands on the annex roof (SE
   face, NE 3.40 m: the SE elevation dimensions it from +4.30). 2F = +9.70 -> +14.40.

## 3. Side by side (FACADE_SIDES_T159.csv has every band with its source)

| Floor | Side | Faces | Length m | Height bands (bottom -> top, m) | Measured m2 | HELD m2 | Openings on it (width m) |
|---|---|---|---|---|---|---|---|
| GF | SE-1 | SE | 6.7000 | edge 6.700: +0.00->+0.30; edge 6.700: +0.30->+4.80 | 32.160 | - | OP-028 1.955, OP-029 1.955 |
| GF | SW-1 | SW | 3.1000 | edge 3.100: +0.15->+0.30; edge 3.100: +0.30->+4.80 | 14.415 | - | OP-009 1.000 |
| GF | SW-2 (arc) | SW | 2.0420 | edge 2.042: +0.15->+0.30; edge 2.042: +0.30->+4.80 | 9.495 | - | - |
| GF | NW-1 | NW | 0.5000 | edge 0.500: +0.15->+0.30; edge 0.500: +0.30->+4.80 | 2.325 | - | - |
| GF | SW-3 | SW | 6.4000 | covered 0.200: +0.15->+0.30; covered 0.200: +0.30->+5.50; edge 6.200: +0.15->+0.30; edge 6.200: +0.30->+4.80 | 29.900 | - | OP-004 0.600, OP-005 0.900, OP-006 1.500 |
| GF | SW-4 | SW | 1.2000 | not a face: passage mouth / boundary-wall end (Q-67 A) | - | - | - |
| GF | SW-5 | SW | 3.0000 | covered 3.000: +0.15->+1.00; covered 3.000: +1.00->+5.50 | 16.050 | - | OP-008 1.000 |
| GF | SE-2 | SE | 3.7000 | covered 3.700: +0.15->+1.00; covered 3.700: +1.00->+5.50 | 19.795 | - | OP-021 2.000 |
| GF | NE-1 | NE | 1.4000 | covered 1.400: +0.15->+1.00; covered 1.400: +1.00->+5.50 | 7.490 | - | - |
| GF | SE-3 | SE | 0.4000 | covered 0.400: +0.15->+1.00; covered 0.400: +1.00->+5.50 | 2.140 | - | - |
| GF | SW-6 | SW | 1.4000 | flush 1.400: +0.15->+1.00; flush 1.400: +1.00->+5.50 | 7.490 | - | - |
| GF | SE-4 | SE | 4.5000 | flush 4.500: +0.15->+1.00; flush 4.500: +1.00->+5.50 | 24.075 | - | OP-022 1.200 |
| GF | SW-7 | SW | 14.8700 | flush 14.870: +0.15->+1.00; flush 14.870: +1.00->+5.50 | 79.554 | - | OP-013 0.900, OP-014 0.600, OP-015 0.600, OP-016 0.600 |
| GF | NW-2 (return) | NW | 0.2500 | flush 0.250: +0.15->+1.00; flush 0.250: +1.00->+5.50 | 1.337 | - | - |
| GF | NE-2 | NE | 0.5000 | covered 0.500: +0.15->+1.00; covered 0.500: +1.00->+5.50 | 2.675 | - | - |
| GF | SE-5 (return) | SE | 0.0500 | covered 0.050: +0.15->+1.00; covered 0.050: +1.00->+5.50 | 0.268 | - | - |
| GF | NE-3 (return) | NE | 0.0800 | covered 0.080: +0.15->+1.00; covered 0.080: +1.00->+5.50 | 0.428 | - | - |
| GF | NW-3 (return) | NW | 0.1935 | covered 0.193: ?->+1.00 HELD 0.700..0.850 m; covered 0.193: +1.00->+5.50 | 0.871 | 0.135..0.164 | - |
| GF | NW-4 (arc) | NW | 6.6577 | covered 6.658: ?->+1.00 HELD 0.700..0.850 m; covered 6.658: +1.00->+5.50 | 29.960 | 4.660..5.659 | - |
| GF | NW-5 (return) | NW | 0.1435 | covered 0.143: ?->+1.00 HELD 0.700..0.850 m; covered 0.143: +1.00->+5.50 | 0.646 | 0.100..0.122 | - |
| GF | SW-8 (return) | SW | 0.0800 | covered 0.080: ?->+1.00 HELD 0.700..0.850 m; covered 0.080: +1.00->+5.50 | 0.360 | 0.056..0.068 | - |
| GF | NW-6 | NW | 0.4500 | covered 0.450: +0.15->+1.00; covered 0.450: +1.00->+5.50 | 2.407 | - | - |
| GF | SW-9 | SW | 2.0000 | covered 0.500: +0.15->+1.00; covered 0.500: +1.00->+5.50; edge 1.500: +0.15->+1.00; edge 1.500: +1.00->+6.00 | 11.450 | - | - |
| GF | NW-7 | NW | 7.9000 | edge 7.900: +0.00->+1.00; edge 7.900: +1.00->+6.00 | 47.400 | - | OP-019 6.332 |
| GF | NE-4 | NE | 19.3700 | edge 19.370: +0.00->+1.00; edge 19.370: +1.00->+6.00 | 116.220 | - | - |
| GF | NE-5 | NE | 1.2000 | not a face: passage mouth / boundary-wall end (Q-67 A) | - | - | - |
| GF | NE-6 | NE | 10.8000 | edge 10.800: +0.00->+0.30; edge 10.800: +0.30->+4.80 | 51.840 | - | OP-001 0.200 |
| GF | P-1 (passage) | NW | 4.7000 | covered 4.700: +0.15->+0.30; covered 4.700: +0.30->+5.50 | 25.145 | - | OP-025 1.000 |
| GF | P-2 (passage) | SE | 4.7000 | covered 4.700: +0.15->+1.00; covered 4.700: +1.00->+5.50 | 25.145 | - | OP-024 1.500, OP-023 1.000 |
| 1F | NW-1 | NW | 1.1703 | slab_edge_below 0.920: ?->+5.50 HELD; storey 1.170: +5.50->+9.70; parapet 1.170: +9.70->+11.00 (CAD top line) | 6.436 | 0.000..0.000 + slab edge | - |
| 1F | NW-2 (arc) | NW | 3.5283 | slab_edge_below 3.528: ?->+5.50 HELD; storey 3.528: +5.50->+9.70; parapet 3.528: +9.70->+11.00 (CAD top line) | 19.404 | 0.000..0.000 + slab edge | COP-001 2.977 |
| 1F | NW-3 | NW | 0.5780 | slab_edge_below 0.578: ?->+5.50 HELD; storey 0.578: +5.50->+9.70; parapet 0.578: +9.70->+11.00 (CAD top line) | 3.179 | 0.000..0.000 + slab edge | - |
| 1F | NE-1 (return) | NE | 0.0800 | slab_edge_below 0.080: ?->+5.50 HELD; storey 0.080: +5.50->+9.70; parapet 0.080: +9.70->? HELD 1.100..1.300 m | 0.336 | 0.088..0.104 + slab edge | - |
| 1F | NW-4 | NW | 0.4673 | slab_edge_below 0.467: ?->+5.50 HELD; storey 0.467: +5.50->+9.70; parapet 0.467: +9.70->+10.80 (CAD top line) | 2.476 | 0.000..0.000 + slab edge | - |
| 1F | SW-1 (return) | SW | 0.0800 | slab_edge_below 0.080: ?->+5.50 HELD; storey 0.080: +5.50->+9.70; parapet 0.080: +9.70->? HELD 1.100..1.300 m | 0.336 | 0.088..0.104 + slab edge | - |
| 1F | NW-5 | NW | 6.7250 | slab_edge_below 0.325: ?->+5.50 HELD; storey 6.725: +5.50->+9.70; parapet 6.725: +9.70->+10.15 (CAD top line) | 31.258 | 0.000..0.000 + slab edge | OP-016 1.552, OP-017 1.552 |
| 1F | NE-2 | NE | 19.2700 | storey 19.270: +5.50->+9.70; parapet 19.270: +9.70->+11.00 | 105.985 | - | OP-001 0.600, OP-002 0.600, OP-003 1.552 |
| 1F | SE-1 | SE | 7.5000 | over_lower_roof 3.400: +4.30->+5.50; slab_edge_below 4.100: ?->+5.50 HELD; storey 7.500: +5.50->+9.70; parapet 7.500: +9.70->+10.74 (CAD top line) | 43.387 | 0.000..0.000 + slab edge | OP-022 2.450 |
| 1F | SW-2 | SW | 4.4000 | slab_edge_below 3.000: ?->+5.50 HELD; storey 4.400: +5.50->+9.70; parapet 4.400: +9.70->? HELD 0.385..1.600 m | 18.480 | 1.694..7.040 + slab edge | - |
| 1F | SE-2 | SE | 4.5000 | storey 4.500: +5.50->+9.70 | 18.900 | - | OP-021 1.200 |
| 1F | SW-3 | SW | 14.8700 | storey 14.870: +5.50->+9.70; parapet 6.770: +9.70->+11.00 | 71.255 | - | OP-012 1.000, OP-013 0.600, OP-014 0.600, OP-015 0.600 |
| 2F | NW-1 | NW | 6.8000 | storey+parapet 6.800: +9.70->+14.40 | 31.960 | - | - |
| 2F | NE-1 | NE | 8.1000 | storey+parapet 8.100: +9.70->+14.40 | 38.070 | - | OP-001 1.000 |
| 2F | SE-1 | SE | 6.8000 | storey+parapet 6.800: +9.70->+14.40 | 31.960 | - | OP-008 1.200 |
| 2F | SW-1 | SW | 8.1000 | storey+parapet 8.100: +9.70->+14.40 | 38.070 | - | OP-003 1.000, OP-004 0.600, OP-005 1.200 |

Totals check: GF 561.041 + 1F 321.432 + 2F 140.060 = 1,022.533 (1,022.534 unrounded) m2 measured.

## 4. Held items (never 0)

| Item | Where | Why held | Bound |
|---|---|---|---|
| plinth of the pool glazing | GF NW-3 / NW-4 / NW-5 / SW-8 (7.075 m) | the face meets the pool: rim +0.30 or deck +0.15, the drawing does not say which the face stands on | 4.951 .. 6.013 m2 |
| 1F parapet over the porch | 1F SW-2 (4.40 m) | sheet 07 draws a curved top with no dimension | 1.694 .. 7.040 m2 |
| 1F recess returns above +9.70 | 1F NE-1 / SW-1 (0.16 m) | top +10.80 (recess) or +11.00 (face) | 0.176 .. 0.208 m2 |
| 1F slab edge over open air | 13.079 m (porch 7.10, pool court 5.98) | slab depth not printed on the architectural sheets; owner Q-68: candidate exterior slab edge, finish HELD | no number |
| openings | 45.125 m of opening width on the faces | heights printed only for D01 2.00 x 2.50, W03 6.57 x 4.30, W14 2.45 x 1.60, W17 2.977 x 3.50 (47.589 m2, T-144 evidence, READY); every other head / sill not printed | net facade HELD (UP-GEN-003 1.1.0: PLASTER_PAINT openings, owner decision pending) |

Not in this table (other scope, listed so nothing is lost): roof parapet inner faces and copings, the domes, the 1F
roof railings (X lattice above the +9.80 / +10.085 wall tops on the NW and SE faces: not a wall face), soffits
(Q-68), the street / boundary fence (Q-65), the 0.658 m2 second outline the engine finds on every floor (an RFI).
The NE faces stand on the NE plot boundary line (sheet 09 draws them on the boundary with +-0.00 both ends): they are
counted as exterior faces as the elevation draws them.

## 5. Hand fixture (not the development villa): `check_t159.py --check` PASS

L-shaped two-storey house: GF (0,0)(12,0)(12,4)(7,4)(7,9)(0,9) with a half-circle bay r 4.50 on the west side
(two CAD arcs), 1F set back to the 7 x 9 m block; ground 0.00, GF +0.50, 1F / GF roof +4.00, GF parapet +4.60, 1F
parapet +8.50. By hand: GF sides 12 / 4 / 5 / 5 / 7 / arc 4.5 pi = 47.137167 m; GF S side FLUSH 7 + EDGE 5; GF area
205.430968 m2 (arc 20.7 pi); 1F east side FLUSH 5 over GF E-2 + COVERED 4 over the GF roof; 1F 144.000 m2; house
349.430968 m2. Checked: rotated 30 / -121 / 90 deg, mirrored, millimetres, re-started at another vertex, walked
clockwise, mirrored + clockwise + millimetres together, a porch variant (1F 1.5 m over the GF S side: GF S COVERED 7,
1F 157.500 m2, the 1F S side over open air), a missing ground level (GF areas HELD, 1F unaffected), a band with no top
(None, never 0), a top below its bottom (raises), an empty outline, a 0.05 m jog kept as a RETURN, an opening kept
in its side. A side split both above AND below is HELD by the composer (no proportional guess).

## 6. What is learned / what is missing

- A face that stands on a LOWER roof starts at that roof, not at its floor: the 1F SE face rises from the annex roof
  (+4.30), and the SE elevation dimensions it from there (+4.080 m2 here). A per-floor band alone misses it.
- Set-back storeys give two faces on one elevation (the GF face to its parapet and the 1F face behind it): the
  freelancer's one plane per elevation (10.00 x 19.20 on NE) merges them and drops the 0.50 m where both exist.
- Wavy or stepped parapets carry no dimension; their area exists only as CAD line geometry of the elevation frame
  (DXF), integrated along the side; the raster sheets (07, 09) cannot give it.
- 13.08 m of 1F slab edge stands over open air (porch, pool court): a facade item with no printed depth.
- Missing: wiring the side split + bands into a method (lane I, the V3.0 candidate) after Gate A; opening heights
  (T-144 / T-150 READY); the net (UP-GEN-003 PLASTER_PAINT pending); the slab depth from the structural sheets for the
  slab edges; the SW-2 parapet curve; the pool plinth.

Files: `t159_extract.py` (engine outline per floor -> t159_rings.json in the scratchpad), `t159_sides.py` (pure:
split_sides, name_sides, against_upper, band_area, house_facade), `t159_alsenan.py` (the table; levels with sources),
`check_t159.py` (hand fixture), `FACADE_SIDES_T159.csv`, `summary.json`.
Reproduce: `python3 -I research/agents_t159/t159_extract.py <P7757 plan DXF> <out> research/urban_m9_s2/SYNTHETIC_FACTS_S2.json`
then `python3 -I research/agents_t159/t159_alsenan.py <out> --csv <csv>` (the DXF from Drive "Alsenan chalet project"
/ P7757_DXF_COMPRESSED.zip, kept outside the repository). Lengths, heights and areas only.
