# T-163 Alsenan formwork m2 per element type, from the checker-merged concrete ledgers (lane S; NO REPO CODE)

Worker 1, 2026-10-22 (r1 05:20; **r2 rework 20:29 .. 21:40, section 0**). Development villa, not an accuracy claim. Nothing is wired and no released quantity changes:
a checked piece for the V3.0 candidate (lane I). Formwork is a missing BOQ category: the released method has no
formwork line, and `engine/source/struct_n10.py` writes a FORMWORK.json that no BOQ line reads (L-N10-04).

Files: `t163_formwork.py` (the ledger: face formulas, the drawing-face walker, the synthetic `--check`, the Alsenan
lines; it imports nothing from `engine/`; `--r1` reproduces the rejected r1 files byte for byte), `JOINT_BY_COLUMN.csv`
(r2: per column the face lengths by neighbour and the joint at the drawn outline and at the stated section),
`FORMWORK_LINES.csv` (267 lines in r2: element, floor, item, method, m2 or held
range, status, basis, freelancer, verdict), `ledger_summary.json` (per floor and totals).
Repeat: `python -I ../agents_t139/slab_faces.py <ST.dxf> faces.json` (T-139, reproduces T-139 PANELS.csv byte for
byte, checked this run) then `python -I t163_formwork.py faces.json <out>`; `python -I t163_formwork.py --check`.

Sources (Drive "Alsenan chalet project", private scratch copies, never committed): "ST7757 dxf.dxf" (sha256
9f9d1179...), "ST7757.pdf" (sha256 74da1523...: p.13 footing and ground-beam details, p.14 parapet / lift / boundary
details, p.11 continuous-beam schedule), freelancer concrete workbook (حصر خرسانة+الحديد, 8 sheets). Merged ledgers
used: footings T-065 / T-100 / T-136, ground beams and straps T-138 r2 / T-141, columns T-119 r2, beams T-110 / T-149 /
T-145, slabs T-139, stairs T-084 / T-111. Rules: URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1, URBAN-COLUMN-HEIGHT-TO-
CONTROLLING-MEMBER@v1, OQ-10 / OQ-11, Q-21 C, Q-26 A, Q-28, Q-44 A, Q-61 C, Q-62 A cond, UP-QTY-STATUS-001.

## 0. Rework r2 (Checker 2026-10-22 12:05, D-T163-1): column joint faces at through / flush and oblique framing

**What was wrong.** The Checker re-measured COL-GF-19 (C11 0.25 x 1.10, D_ctrl 0.85, slab 0.16) at **1.004 m2** of
open joint face against r1's 1.124 m2 (+12.0 %). Traced this run on the DXF faces, r1's walker had two geometric faults,
not a rule fault:
1. **Probe leak at an internal acute wedge.** Drafting lines (B1's band line and a diagonal) cut the column into three
   faces; r1 walked every piece edge and probed 30 mm off it. From the diagonal, near its 12.8 deg vertex, the probe
   crossed the thin neighbouring piece and landed in the slab beyond: **0.150 m 'to slab' that does not exist** (r1's
   1.466 m vs the drawn 1.316 m = N 1.100 + W 0.050 + S 0.166).
2. **30 mm probe past the face line.** On the east face, B27's oblique edge passes exactly through the NE corner, so at
   the face B27 (85 deep, = D_ctrl) covers the whole face; 30 mm out the probe met B1 (40 deep) over 0.050 m and counted
   0.050 x 0.45. r1's 'under B1 0.250 m' = west 0.200 (B1's own width, right) + this 0.050 (wrong).
The same faults explain the other columns: 1F C9 COL-1F-39 1.147 -> 0.948 (r1 leaked 0.306 m into two slabs at the
diagonal's two acute ends), GF C11 COL-GF-25 0.919 -> 0.805 (B27 crosses two corners), and they also touched beams and
edges (B15 at the 2F tank: a 20 mm break-mark sliver beyond its west side was 'outside' at 30 mm: 0.816 m2 of side and
0.144 m2 of edge band moved from CALCULATED to HELD, where the sliver's neighbour strip belongs).

**r2 rule (module: `merge_owner_faces`, `classify_edges(exact=True)`, `column_face_trace`, `stated_joint`).**
(a) The pieces of ONE element (a column, or one beam member cut by drafting lines) are walked as ONE outline: an edge
between two pieces of the same element is never a formwork face. A column is walked on its DRAWN outline (T-119 x, y,
drawn size) when its pieces lie inside it: band lines of framing beams drawn across a column (a notch, a cut corner, a
gap) are not column faces. (b) Each edge, moved 2 mm outward, is cut exactly by every face beyond it (no 50 mm
sampling, no 30 mm probe): a framing member covers exactly the length it occupies on that face, i.e. its own width for
an orthogonal member (B1 0.20 on a 0.25 face leaves 0.05 open) and its oblique trace for an oblique one. Probe 1 / 2 /
5 mm give 13.017 / 13.018 / 13.016 m2 of joint (pieces-hull walk, before the drawn-outline step; stable); 10 / 20 mm
drift up (13.094 / 13.184) as the probe starts to cross obliquely cut neighbours. (c) **Stated dimensions govern**
(every slab sheet: "THE BUILDER TO WORK WITH STATED DIMENSIONS NOT TO SCALE DRAWING"; T-119 finding 5 takes the p.9
schedule section; 10 of the 30 DRAWING-CONFIRMED columns are drawn at another size): the drawing gives the TOPOLOGY
(which member frames on which face, over what length), the schedule gives the face length; on a resized face only the
open part changes: open = L_stated - framed length, at the open part's height (D_ctrl - t to a slab or outside,
D_ctrl - D beside a shallower beam). A face framed over its whole drawn length stays fully framed. A resized face whose
open parts have two heights, or that is shorter than its framing while an open part is drawn, or longer with no open
part drawn (which end grows is not printed) is HELD with its range; never scaled, never 0.

**Result (the 30 DRAWING-CONFIRMED columns, m2 of open joint face).** r1 14.224 -> r2 at the drawn outline 13.254
(INFO line) -> r2 at the stated section **11.878 CALCULATED (27 columns) + 1.003 .. 1.180 HELD (3 columns: GF C3
COL-GF-14, GF C COL-GF-24 and COL-GF-30, drawn 0.20 / 0.40 where the schedule says 0.25 / 0.50 and nothing open is
drawn on the longer face)**. Against r1: -0.970 m2 is the walker fix and -1.376 the stated-section basis; 1.003 .. 1.180
moves to HELD. Element method E vs drawing G on these columns: E 208.858 vs G shaft 183.967 + joints 12.881 .. 13.058 =
196.848 .. 197.025: **E +11.833 .. +12.010 m2 (+6.0 .. +6.1 %)**, was +10.667 (+5.4 %) in r1 (D-N10-04).

| Column | Mark | Section p.9 | Drawn | D_ctrl | r1 joint | r2 drawn outline | r2 stated section | Status |
|---|---|---|---|---|---|---|---|---|
| COL-1F-31 | C4 | 0.20x0.50 | 0.50x0.25 | 0.75 | 0.375 | 0.522 | 0.492 | CALCULATED |
| COL-1F-32 | C5 | 0.20x0.50 | 0.60x0.25 | 0.50 | 0.443 | 0.442 | 0.340 | CALCULATED |
| COL-1F-33 | C4 | 0.20x0.50 | 0.50x0.25 | 0.50 | 0.306 | 0.306 | 0.272 | CALCULATED |
| COL-1F-34 | C2 | 0.20x0.50 | 0.20x0.50 | 0.40 | 0.192 | 0.168 | 0.168 | CALCULATED |
| COL-1F-35 | C2 | 0.20x0.50 | 0.20x0.50 | 0.50 | 0.342 | 0.210 | 0.210 | CALCULATED |
| COL-1F-37 | C1 | 0.20x0.50 | 0.20x0.50 | 0.75 | 0.375 | 0.317 | 0.317 | CALCULATED |
| COL-1F-38 | C2 | 0.20x0.50 | 0.20x0.50 | 0.40 | 0.215 | 0.192 | 0.192 | CALCULATED |
| COL-1F-39 | C9 | 0.20x0.90 | 0.20x1.00 | 0.75 | 1.147 | 0.948 | 0.830 | CALCULATED |
| COL-1F-41 | C9 | 0.20x0.90 | 0.25x1.00 | 0.75 | 0.894 | 0.924 | 0.776 | CALCULATED |
| COL-1F-42 | C2 | 0.20x0.50 | 0.20x0.50 | 0.75 | 0.676 | 0.560 | 0.560 | CALCULATED |
| COL-1F-44 | C6 | 0.20x0.60 | 0.25x0.70 | 0.50 | 0.000 | 0.000 | 0.000 | CALCULATED |
| COL-1F-47 | C5 | 0.20x0.50 | 0.60x0.25 | 0.75 | 0.384 | 0.354 | 0.295 | CALCULATED |
| COL-2F-51 | C2 | 0.20x0.50 | 0.20x0.50 | 0.75 | 0.456 | 0.596 | 0.596 | CALCULATED |
| COL-2F-53 | C1 | 0.20x0.50 | 0.20x0.50 | 0.40 | 0.183 | 0.138 | 0.138 | CALCULATED |
| COL-2F-54 | C2 | 0.20x0.50 | 0.20x0.50 | 0.40 | 0.215 | 0.192 | 0.192 | CALCULATED |
| COL-GF-04 | C2 | 0.20x0.50 | 0.20x0.50 | 0.40 | 0.048 | 0.048 | 0.048 | CALCULATED |
| COL-GF-06 | C3 | 0.25x0.50 | 0.25x0.50 | 0.40 | 0.025 | 0.000 | 0.000 | CALCULATED |
| COL-GF-07 | C1 | 0.20x0.50 | 0.20x0.50 | 0.75 | 0.375 | 0.317 | 0.317 | CALCULATED |
| COL-GF-08 | C2 | 0.20x0.50 | 0.20x0.50 | 0.40 | 0.215 | 0.192 | 0.192 | CALCULATED |
| COL-GF-11 | C9 | 0.25x1.00 | 0.25x1.00 | 0.75 | 1.129 | 1.158 | 1.158 | CALCULATED |
| COL-GF-12 | C2 | 0.20x0.50 | 0.20x0.50 | 0.75 | 0.706 | 0.590 | 0.590 | CALCULATED |
| COL-GF-13 | C8 | 0.25x0.90 | 0.90x0.25 | 0.85 | 0.994 | 0.993 | 0.993 | CALCULATED |
| COL-GF-14 | C3 | 0.25x0.50 | 0.20x0.50 | 0.75 | 0.353 | 0.295 | 0.295 .. 0.354 | HELD: S: stated face 0.25 longer than drawn 0.20 with no open part drawn; N: stated face 0.25 longer than drawn 0.20 with no open part drawn |
| COL-GF-17 | C6 | 0.25x0.70 | 0.25x0.70 | 0.50 | 0.455 | 0.462 | 0.462 | CALCULATED |
| COL-GF-19 | C11 | 0.25x1.10 | 1.10x0.25 | 0.85 | 1.124 | 1.000 | 1.000 | CALCULATED |
| COL-GF-24 | C | 0.20x0.50 | 0.20x0.40 | 0.75 | 0.383 | 0.354 | 0.413 .. 0.472 | HELD: W: stated face 0.50 longer than drawn 0.40 with no open part drawn |
| COL-GF-25 | C11 | 0.25x1.10 | 1.10x0.25 | 0.85 | 0.919 | 0.805 | 0.805 | CALCULATED |
| COL-GF-26 | C3 | 0.25x0.50 | 0.50x0.25 | 0.75 | 0.325 | 0.295 | 0.295 | CALCULATED |
| COL-GF-27 | C10 | 0.25x0.70 | 0.70x0.25 | 0.85 | 0.706 | 0.637 | 0.637 | CALCULATED |
| COL-GF-30 | C | 0.20x0.50 | 0.40x0.20 | 0.75 | 0.265 | 0.236 | 0.295 .. 0.354 | HELD: N: stated face 0.50 longer than drawn 0.40 with no open part drawn |
| **30 columns** | | | | | **14.224** | **13.254** | **11.878** CALCULATED + **1.003 .. 1.180** HELD | |


**Hand checks (re-measure these).** Each joint above was re-derived by a separate face-line trace (the drawn outline's
four faces moved 2 mm out and intersected with the T-139 faces; heights from the member register): all 30
DRAWING-CONFIRMED columns agree with the walker within 0.0001 m2 at the drawn outline (same faces, so this checks the
walker's arithmetic and topology, not the face partition).
- **COL-GF-19** (Checker's column): N slab 1.100 x 0.69 = 0.759; W slab 0.050 x 0.69 + B1 0.200 x 0.45 = 0.1245; S slab
  0.168 x 0.69 = 0.1159 (B27's SW edge meets the face at 0.166 .. 0.168 m: oblique, 2 mm out) + B27 0.932 x 0;
  E B27 0.050 x 0 + drafting gap 0.198 (B27's band continuation between B1's lines: covered) + B1 corner sliver 0.002 x
  0.45 = 0.0009 -> **1.0003 m2 vs Checker 1.004 (-0.4 %)**; drawn = stated (1.10 x 0.25), so 1.000 is the line value.
- **COL-1F-39** (1F C9, schedule 0.20 x 0.90, drawn 0.20 x 1.00, D_ctrl 0.75 by B19 40 x 75): drawn faces E slab 0.800
  + B4 0.200 (50 deep: x 0.25), W slab 0.622 + B19 0.378 (x 0), S B19 0.184 + slab 0.016, N B5 0.200 (x 0.25): drawn
  1.438 x 0.59 + 0.400 x 0.25 = 0.948; stated: each long face 0.10 shorter in its slab part: E 0.700 x 0.59 + 0.05,
  W 0.522 x 0.59, S 0.016 x 0.59, N 0.05 -> **0.830 m2** (r1 1.147).
- **COL-GF-25** (GF C11 1.10 x 0.25, D_ctrl 0.85): S at the plate edge 1.100 x 0.69 = 0.759; N B27 1.056 x 0 +
  BM-GF-041 (75 deep) 0.044 x 0.10; W B27 0.080 x 0 + BM-GF-040 (75) 0.170 x 0.10; E BM-GF-041 0.250 x 0.10 ->
  **0.805 m2** (r1 0.919: two cut corners walked as faces).
- Synthetic adverse cases in `--check` and tests/t163_formwork (not Alsenan): beam narrower than the face running
  through flush (1.767; r1 1.970), deeper oblique beam over part of a face (1.215; r1 1.317), the column cut by a
  drafting diagonal = the uncut column, a 20 mm break sliver beyond a beam (held, not an outer face), stated section
  1.1325 vs drawn 1.3525, and the three HELD cases of (c).

**Other lines moved by the walker fix (no other rule changed):** beam sides below the slab 288.711 -> **287.681**
(-1.030 m2, -0.36 %: B15 at the tank -0.816 to HELD, GF stub BM-GF-020 -0.192, +/- 0.05 .. 0.11 on about 20 members
from exact splitting); slab-thickness band 31.795 -> **31.058** (-0.737: column-piece edges r1 called 'outside' and the
two break slivers); held above ground 220.752 .. 276.506 -> **221.507 .. 277.365**. Beam and slab soffits, shafts,
stairs and every below-ground line: unchanged (`--r1` reproduces the r1 files byte for byte).

**Lessons-register row proposed (ENGINEERING_REASONING_STANDARD section 7):** 2026-10-22 | Column joint faces +12 %
(COL-GF-19 1.124 vs 1.004 m2); whole joint line 14.224 vs 11.878 + 1.003 .. 1.180 HELD | (1) one element walked as its
drafting pieces: probes from internal edges leaked past acute wedges; (2) a 30 mm probe read the member 30 mm away,
not the one at the face; (3) the drawn outline used where the stated schedule size governs | Walk each element as one
outline (a column on its drawn outline); split every face exactly at the faces beyond it (2 mm); a framing member
covers exactly its trace on the face; the stated section changes only the open part of a resized face, else HELD (any
villa; formwork and any face-contact measure) | tests/t163_formwork + `--check` (normal bay; adverse: through flush
beam narrower than the face, oblique corner beam, diagonal-cut column, break sliver, stated vs drawn) | r2 READY.

## 1. Result in engineering terms (m2 of contact area)

Freelancer: **no formwork row in any of his six workbooks** (885 raw rows in tests/alsenan/registers_b1 and every
text cell of the concrete workbook searched: 0 hits). Engine released: **no formwork line**. So every line below is a
new line; the verdict against the freelancer is FREELANCER_NO_ROW throughout (no %).

| Element (floor) | Drawing-face method G, CALCULATED | Element-face method E (struct_n10 rule on the same ledgers) | Held, never 0 |
|---|---|---|---|
| Slab soffits (GF / 1F / 2F roof) | **206.684 / 123.479 / 44.885 = 375.048** | same (T-139 panels) | slab under the winders 1.44 .. 1.56; sunken panels drop x 50.885 m (D-41) |
| Beam soffits | **55.966 / 34.065 / 7.824 = 97.855** | 55.738 / 34.242 / 7.904 = 97.884 (-0.03 %) | faces of HELD / CONFLICT members (with sides) GF 26.777, 1F 5.947, 2F 1.406 |
| Beam sides below the slab | **r2 166.460 / 93.475 / 27.746 = 287.681** (r1 288.711) | 187.103 / 109.884 / 30.339 = 327.326 (E +39.645, +13.8 %) | faces next to stair zones, ring faces, held edge strips, unmatched pieces: 0 .. 40.8 |
| Upstands B20 / B23 (20 x 20 x 3.00) | **1.200 + 1.200** | same | - |
| Columns, shaft to the controlling soffit (30 DRAWING-CONFIRMED) | **101.897 / 66.600 / 15.470 = 183.967** | E upper bound perimeter x (interval - 0.16): 208.858 | 29 HELD columns 172.073 .. 176.115 (T-119 causes; 3 planted columns HELD) |
| Column joint faces left open by beams (r2, stated section) | **6.498 / 4.454 / 0.926 = 11.878** (27 columns; r1 14.224; drawn outline 13.254) | not measured (inside E's upper bound) | 3 resized columns 1.003 .. 1.180; joints of HELD columns 10.955 |
| Slab-thickness band at free edges | **r2 13.920 / 8.667 + 4.446 dome openings / 4.025 = 31.058** (r1 31.795) | HELD (OQ-12) | stair-zone and ring edges 0 .. 1.64; pool-court void 1.090 .. 1.210 |
| Stairs: risers, waist soffits, landing soffits | **44.533** (main stair 30.992, round stair 10.321, entrance + lobby risers 3.220) | not measured (E holds stairs) | winders, closing riser, curved flight, stringer sides, lobby waist |
| **Above ground, total** | **r2 1,034.420** (r1 1,038.533) | - | **r2 221.507 .. 277.365** + 9 unquantified lines |

Below ground, OQ-10 carried as two alternatives (never summed, never chosen):

| Element | FORMED | EARTH_CAST | Held |
|---|---|---|---|
| 25 drawn footings (released concrete), F x4 .. FN x4 | **92.240** | **0** | F10 (Q-31 C) 4.200 .. 5.220; FN / F9 notch -0.450 .. 0; strap-end contacts -2.050 .. 0 |
| Ground beams, the 4 spans with one p.13 section and no EXT / CONC flag | **11.140 - 0.240 tee = 10.900** | **0** | 15 CONC + 11 section-candidate + 2 held spans 60.644 .. 66.865; 29 exterior spans 183.658 m2 per metre of depth (FOLLOW ARCH, D-35); 2 curved bands |
| Straps SB1 / SB2 / SB3 | - | - | 8.648 .. 9.449 (length basis not set, T-141) |
| Boundary band M1 / ground beam M3 / pads | - | - | M1 56.392 .. 110.328 (Q-28 provisional only); M3 35.256 (concrete line unresolved); pads count not printed |
| Necks (35) | - | - | 52.000 m2 per metre of neck height for the 30 GF sections (Q-21 C) |
| **Below ground, total** | **103.140** | **0** | **162.640 .. 227.118** + 34 unquantified lines |

## 2. How each face was measured

- **G, drawing faces.** T-139's polygonised faces of the three roof-slab plans (re-made from the DXF; PANELS.csv
  reproduced exactly) are walked edge by edge in 50 mm steps, and the face beyond each edge decides the contact
  area (rules in the module text). Band pieces are bound to their member by the member id in the T-139 evidence, a
  mark printed inside the band (B21 is oblique and is found this way), or the T-110 register centre, width, length
  and axis (orientation must agree; a junction square takes the deepest member through it). Columns by the T-119
  outline. 0.718 m2 of small GF band pieces bind to no member and stay HELD.
- **Depth basis (OQ-11) settled by the drawing:** ST p.14 "TYPICAL DETAIL OF PARAPET SECTION" dimensions the beam
  depth "AS PER SCH." from the slab top line (15 slab) to the beam soffit, so the schedule depth is the TOTAL depth;
  every merged ledger (T-119, T-139, T-149) already uses D - t. No alternative is carried. For information only: the
  BELOW_SLAB reading would add 2 x 0.16 x 359.793 m = 115.134 m2 to E's beam sides.
- **E, element faces:** struct_n10's draft face rule (UP-FW-001) evaluated on the merged ledgers: soffit B x clear
  length, sides 2 L (D - t), columns perimeter x (interval - t). Why E is higher: (1) beam sides: tee junctions (a
  framing beam's end covers the carrier's side) and the faces next to stair zones, ring bands and held edge strips
  are not deducted or held; on B8 (GF) E gives 2 x 3.520 x 0.59 = 4.154, G gives 5.023 m x 0.59 = 2.964 + 1.817 m
  next to the pool-court ring HELD; (2) columns: E counts the joint zone as if no beam framed in (D-N10-04, now
  quantified: E 208.858 vs G shaft 183.967 + open joint faces 12.881 .. 13.058 (r2) = 196.848 .. 197.025, E +11.833 ..
  +12.010 m2, +6.0 .. +6.1 %; r1 said 14.224 / +10.667 / +5.4 %, section 0).
- **Hand checks inside the ledger** (re-measure these): bay GF-032 (B8 bay, 3.500 x 3.520 clear): beam edges B8 3.520
  / B16 3.520 / B17 3.500 / B24 3.500 m, = T-139's independent table; bay 1F-084 ('T 16'): CB13 4.85 / B18 4.85 / CB11
  4.30 / B4 4.30 m; 2F-013 (tank, T 18): B3 3.0 / B3 2.7 + column 0.3 / B1 1.8 / B8 1.8 m. Column COL-GF-19 (C11
  0.25 x 1.10, D_ctrl 0.85): r1's joint 1.124 m2 was REJECTED (Checker 1.004); r2 1.0003 m2, see section 0 for the face
  by face trace; shaft 2 x 1.35 x 3.650 = 9.855 m2 (agreed by the Checker).
- **Slab edges:** every free edge of the plate (outer perimeter and the X-box openings) x the thickness of the panel
  beside it; the edge-beam face below the slab is already in the beam sides, so nothing is counted twice. Dome
  openings (Q-44 A, p.7 inner diameter 442): 2 x 2 pi x 2.2111 x 0.16 = 4.446 m2; the ring beams' faces below the
  slab are HELD with the rings (T-160 READY, not merged).
- **Footings:** 2 (L + W) H per drawn footing at its schedule size (p.9 = drawn outline, T-065); base on 10 cm
  blinding (p.13): no form; top open. p.13 draws an insulation membrane and "two layers liquid water proofing to all
  surface in contact with earth" round the footing sides: practice reads that as formed sides, but it does not
  settle OQ-10, so both alternatives stay. **Ground beams:** 2 L D on the T-141 face-to-face span with the p.13
  section from the length (LT2.5 30 x 30, LT5 30 x 40, GT5 30 x 60); EXT (exterior, depth FOLLOW ARCH.), CONC
  (concentrated-load candidate) and two-title spans HELD exactly as T-138 r2 holds their steel.
- **Stairs (T-111 drawn method):** riser forms = risers x width x riser; waist soffit = waist m3 / t (= width x sloped
  length; MS1-L 0.5930 / 0.16 = 3.706 = 1.20 x 2.70 x 1.1440); landing soffit = landing m3 / t. Entrance flight: B-B
  draws the waist on fill, so its soffit takes no form (NOT APPLICABLE with evidence); the lobby flight's waist
  thickness and bedding are not printed (HELD).
- **Not applicable with evidence:** the 5 undrawn columns (1F C3, 2F C3 x2, C5, C8: no upper slab plan draws them,
  T-100 / T-126); F7 (scheduled, not drawn); dome shells (Q-29 client change).

## 3. Verdict proposals for the checker

| Line | Proposal |
|---|---|
| Every formwork line vs freelancer | FREELANCER_NO_ROW: his workbooks price concrete and steel only (formwork is a missing category on both sides) |
| struct_n10 (engine, research only) beam sides vs drawing | ENGINE_WRONG / HAND_RIGHT on method: 2 L (D - t) without junction faces overstates by 39.645 m2 (13.8 %; r1 38.615 / 13.4 %) on the CALCULATED beams; part of the gap is faces the hand ledger HOLDS (stair / ring / edge strips), not faces that do not exist |
| struct_n10 column sides | ENGINE_WRONG (upper bound, as its own D-N10-04 says): +11.833 .. +12.010 m2 (+6.0 .. +6.1 %) on the 30 DRAWING-CONFIRMED columns (r2; r1 +10.667) |
| r1 joint faces (this task, rejected) | WORKER_R1_WRONG, r2 fixes it: 14.224 -> 11.878 CALCULATED + 1.003 .. 1.180 HELD (walker fix -0.970, stated section -1.376); COL-GF-19 1.0003 vs Checker 1.004 (-0.4 %) |
| struct_n10 slab edges HELD | HAND resolves it: 31.058 m2 (r2; r1 31.795) measured from the drawn plate perimeter and openings |
| Footing / ground-beam sides | RULE_DIFFERENCE pending OQ-10 (owner): FORMED 103.140 vs EARTH_CAST 0 on the released scope |
| OQ-11 | settled by ST p.14: TOTAL depth (no alternative needed) |

## 4. Held items (never 0) and what each needs

OQ-10 (owner: formed or earth-cast sides) for every below-ground line; Q-21 C founding levels (necks, strap and
footing contacts, FN / F9 notch); D-33 / D-34 / D-35 (ground-beam sections: concentrated load, length basis of the
titles, exterior depth); T-141 strap length basis; Q-28 M1 band (provisional only); Q-31 C F10; Q-61 C held beam
pieces and edge strips; T-160 dome rings (READY); Q-62 A cond stair / landing junction faces; D-41 sunken-slab drop;
D-44 tank B15; pool walls (T-049 TODO, Q-26 A); lift-pit walls (no merged concrete ledger); stair stringer sides.

## 5. For lane I (Worker 3, V3.0 integration)

Proposed lines: FW.SLAB_SOFFIT (375.048), FW.BEAM_SOFFIT (97.855), FW.BEAM_SIDES (r2 287.681 + 2.400 upstands),
FW.COLUMN (183.967), FW.JOINT (r2 11.878, plus its HELD line 1.003 .. 1.180), FW.SLAB_EDGE (r2 31.058), FW.STAIR (44.533), all CALCULATED from merged evidence,
plus FW.FOOTING / FW.GROUND_BEAM as an OQ-10 pair (103.140 / 0) and every HELD row of FORMWORK_LINES.csv as its own
held line. One surface, two trades: the slab-soffit m2 is formwork for the concrete trade only, never also a ceiling
line. Not a new method version: the candidate's own line set.

## 6. What is missing / uncertain

- The walker binds 0.718 m2 of GF band pieces to no member (HELD) and assigns small junction squares to the deepest
  member through them; the sides it gives are checked on four bays (r1) and, in r2, every DRAWING-CONFIRMED column's joint by a separate
  face-line trace (same faces); the beam sides were not re-traced face by face in r2 (only the walker fix moved them,
  -1.030 m2).
- r2 joints use the schedule (stated) section with the drawn framing topology; on 10 columns the drawing is at another
  size (T-119 finding 5): 7 resolve exactly, 3 stay HELD. The covered length on a face is the drawn trace of the framing
  band; where a band is itself drawn at another width than its schedule the trace is the drawing's (not re-checked
  against T-149 widths here).
- 1F slab soffit uses T-139's 123.479 m2: 1.809 m2 of it (the dome-corner pieces) sits inside the dome faces, whose
  edges are held with the rings.
- No owner manual method for formwork is on record (no owner answer names one); the two methods side by side are the
  engine's draft face rule (E) and the drawing faces (G).
