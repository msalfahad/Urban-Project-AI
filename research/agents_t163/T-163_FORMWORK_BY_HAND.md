# T-163 Alsenan formwork m2 per element type, from the checker-merged concrete ledgers (lane S; NO REPO CODE)

Worker 1, 2026-10-22. Development villa, not an accuracy claim. Nothing is wired and no released quantity changes:
a checked piece for the V3.0 candidate (lane I). Formwork is a missing BOQ category: the released method has no
formwork line, and `engine/source/struct_n10.py` writes a FORMWORK.json that no BOQ line reads (L-N10-04).

Files: `t163_formwork.py` (the ledger: face formulas, the drawing-face walker, the synthetic `--check`, the Alsenan
lines; it imports nothing from `engine/`), `FORMWORK_LINES.csv` (263 lines: element, floor, item, method, m2 or held
range, status, basis, freelancer, verdict), `ledger_summary.json` (per floor and totals).
Repeat: `python -I ../agents_t139/slab_faces.py <ST.dxf> faces.json` (T-139, reproduces T-139 PANELS.csv byte for
byte, checked this run) then `python -I t163_formwork.py faces.json <out>`; `python -I t163_formwork.py --check`.

Sources (Drive "Alsenan chalet project", private scratch copies, never committed): "ST7757 dxf.dxf" (sha256
9f9d1179...), "ST7757.pdf" (sha256 74da1523...: p.13 footing and ground-beam details, p.14 parapet / lift / boundary
details, p.11 continuous-beam schedule), freelancer concrete workbook (حصر خرسانة+الحديد, 8 sheets). Merged ledgers
used: footings T-065 / T-100 / T-136, ground beams and straps T-138 r2 / T-141, columns T-119 r2, beams T-110 / T-149 /
T-145, slabs T-139, stairs T-084 / T-111. Rules: URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1, URBAN-COLUMN-HEIGHT-TO-
CONTROLLING-MEMBER@v1, OQ-10 / OQ-11, Q-21 C, Q-26 A, Q-28, Q-44 A, Q-61 C, Q-62 A cond, UP-QTY-STATUS-001.

## 1. Result in engineering terms (m2 of contact area)

Freelancer: **no formwork row in any of his six workbooks** (885 raw rows in tests/alsenan/registers_b1 and every
text cell of the concrete workbook searched: 0 hits). Engine released: **no formwork line**. So every line below is a
new line; the verdict against the freelancer is FREELANCER_NO_ROW throughout (no %).

| Element (floor) | Drawing-face method G, CALCULATED | Element-face method E (struct_n10 rule on the same ledgers) | Held, never 0 |
|---|---|---|---|
| Slab soffits (GF / 1F / 2F roof) | **206.684 / 123.479 / 44.885 = 375.048** | same (T-139 panels) | slab under the winders 1.44 .. 1.56; sunken panels drop x 50.885 m (D-41) |
| Beam soffits | **55.966 / 34.065 / 7.824 = 97.855** | 55.738 / 34.242 / 7.904 = 97.884 (-0.03 %) | faces of HELD / CONFLICT members (with sides) GF 26.777, 1F 5.947, 2F 1.406 |
| Beam sides below the slab | **166.556 / 93.564 / 28.591 = 288.711** | 187.103 / 109.884 / 30.339 = 327.326 (E +38.615, +13.4 %) | faces next to stair zones, ring faces, held edge strips, unmatched pieces: 0 .. 40.8 |
| Upstands B20 / B23 (20 x 20 x 3.00) | **1.200 + 1.200** | same | - |
| Columns, shaft to the controlling soffit (30 DRAWING-CONFIRMED) | **101.897 / 66.600 / 15.470 = 183.967** | E upper bound perimeter x (interval - 0.16): 208.858 | 29 HELD columns 172.073 .. 176.115 (T-119 causes; 3 planted columns HELD) |
| Column joint faces left open by beams | **8.022 / 5.348 / 0.854 = 14.224** | not measured (inside E's upper bound) | joints of HELD columns 11.301 |
| Slab-thickness band at free edges | **14.240 / 8.949 + 4.446 dome openings / 4.160 = 31.795** | HELD (OQ-12) | stair-zone and ring edges 0 .. 1.64; pool-court void 1.090 .. 1.210 |
| Stairs: risers, waist soffits, landing soffits | **44.533** (main stair 30.992, round stair 10.321, entrance + lobby risers 3.220) | not measured (E holds stairs) | winders, closing riser, curved flight, stringer sides, lobby waist |
| **Above ground, total** | **1,038.533** | - | **220.752 .. 276.506** + 9 unquantified lines |

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
  quantified: E 208.858 vs G shaft 183.967 + open joint faces 14.224 = 198.191, E +10.667 m2, +5.4 %).
- **Hand checks inside the ledger** (re-measure these): bay GF-032 (B8 bay, 3.500 x 3.520 clear): beam edges B8 3.520
  / B16 3.520 / B17 3.500 / B24 3.500 m, = T-139's independent table; bay 1F-084 ('T 16'): CB13 4.85 / B18 4.85 / CB11
  4.30 / B4 4.30 m; 2F-013 (tank, T 18): B3 3.0 / B3 2.7 + column 0.3 / B1 1.8 / B8 1.8 m. Column COL-GF-19 (C11
  0.25 x 1.10, D_ctrl 0.85, B27 85 deep on one face): faces to slab 1.250 + 0.216 = 1.466 m x 0.69 = 1.0115, under
  B1 (40 deep) 0.250 m x 0.45 = 0.1125, joint 1.124 m2; shaft 2 x 1.35 x 3.650 = 9.855 m2.
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
| struct_n10 (engine, research only) beam sides vs drawing | ENGINE_WRONG / HAND_RIGHT on method: 2 L (D - t) without junction faces overstates by 38.615 m2 (13.4 %) on the CALCULATED beams; part of the gap is faces the hand ledger HOLDS (stair / ring / edge strips), not faces that do not exist |
| struct_n10 column sides | ENGINE_WRONG (upper bound, as its own D-N10-04 says): +10.667 m2 (+5.4 %) on the 30 DRAWING-CONFIRMED columns |
| struct_n10 slab edges HELD | HAND resolves it: 31.795 m2 measured from the drawn plate perimeter and openings |
| Footing / ground-beam sides | RULE_DIFFERENCE pending OQ-10 (owner): FORMED 103.140 vs EARTH_CAST 0 on the released scope |
| OQ-11 | settled by ST p.14: TOTAL depth (no alternative needed) |

## 4. Held items (never 0) and what each needs

OQ-10 (owner: formed or earth-cast sides) for every below-ground line; Q-21 C founding levels (necks, strap and
footing contacts, FN / F9 notch); D-33 / D-34 / D-35 (ground-beam sections: concentrated load, length basis of the
titles, exterior depth); T-141 strap length basis; Q-28 M1 band (provisional only); Q-31 C F10; Q-61 C held beam
pieces and edge strips; T-160 dome rings (READY); Q-62 A cond stair / landing junction faces; D-41 sunken-slab drop;
D-44 tank B15; pool walls (T-049 TODO, Q-26 A); lift-pit walls (no merged concrete ledger); stair stringer sides.

## 5. For lane I (Worker 3, V3.0 integration)

Proposed lines: FW.SLAB_SOFFIT (375.048), FW.BEAM_SOFFIT (97.855), FW.BEAM_SIDES (288.711 + 2.400 upstands),
FW.COLUMN (183.967), FW.JOINT (14.224), FW.SLAB_EDGE (31.795), FW.STAIR (44.533), all CALCULATED from merged evidence,
plus FW.FOOTING / FW.GROUND_BEAM as an OQ-10 pair (103.140 / 0) and every HELD row of FORMWORK_LINES.csv as its own
held line. One surface, two trades: the slab-soffit m2 is formwork for the concrete trade only, never also a ceiling
line. Not a new method version: the candidate's own line set.

## 6. What is missing / uncertain

- The walker binds 0.718 m2 of GF band pieces to no member (HELD) and assigns small junction squares to the deepest
  member through them; the sides it gives are checked on four bays and one column, not on every face.
- 1F slab soffit uses T-139's 123.479 m2: 1.809 m2 of it (the dome-corner pieces) sits inside the dome faces, whose
  edges are held with the rings.
- No owner manual method for formwork is on record (no owner answer names one); the two methods side by side are the
  engine's draft face rule (E) and the drawing faces (G).
