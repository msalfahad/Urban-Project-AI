# T-475 Lift marble per landing: B6-06 outer surround and B6-07 lift threshold (stream F, research only)

Worker 1, 2026-11-02 15:28 .. UTC, branch `agents/task-T-475`. No quantity, line, state, method, rule file or released /
candidate cell is changed. Development villa (Alsenan), not an accuracy claim; the method LIFT_LANDING_CENSUS_V1 is for
every villa. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied. Drawings named by Drive folder and title, entities by DXF handle;
station-local sizes only (origin = middle of the lift opening at mid wall, landing side = -y).

Built on, not re-derived (WORKFLOW CONTROLS s.10.5): T-413 MERGED ae87deb1 (LIFT_ENTRANCE_MARBLE_V1, R-T413-1 .. 7; its
module is imported for the band / union / threshold arithmetic, not copied), T-421 (V3.0.38 lines L-c32effca ..
L-fdbd9636), T-401 (shaft, roof closed), T-441 (lift opening in skirting: whole, no jambs), T-296 (skirting deductions by
opening id). This task adds the per-landing CENSUS, an independent re-read of every station on a SECOND drawing (the PDF
plans), the threshold-to-landing fit and level relation, and the per-station deduction matrix.

## 0. Sources read this run (Drive "Alsenan chalet project", decoded by the wrapper into `.work/private`)

| Drawing | What was read |
|---|---|
| P7757.dxf (P7757_DXF_COMPRESSED.zip) | GF / 1F / 2F plans at the shaft: every LINE / INSERT / TEXT / DIMENSION within 2.6 m of each opening (layer, handle, station-local ends); dimension definition points (1042, 145F, 152A, EC5, 1538, E94, 142F, 672, 666, 67D) |
| p7757_arch_sheet03.pdf (GF plan) | 300 dpi crop of the shaft, pixel-scaled on the printed '180' (2.95 px/cm after x2.5) |
| p7757_arch_sheet04.pdf (1F plan) | same, x3 (3.54 px/cm) |
| Alsenan_Architectural_P7757_Pages_05-06.pdf p.1 (2F plan) | same, x3 |
| Alsenan_Architectural_P7757_Pages_11-12.pdf p.1 (SECTION B-B) | storey levels +1.00 / +5.50 / +9.70, roof line; nothing above the roof but domes / parapet |

The lift is internal: no exterior elevation (sheets 06 - 09) shows a landing. No lift / marble / threshold text exists
in the DXF (searched TEXT / MTEXT and block names in English and Arabic: 0 hits besides two elevation titles); no
surround or landing-door detail exists on any sheet read here or by T-413 / T-401 (ST p.14 'Lift door' without size).

## 1. The physical element (ERS s.2.1)

Per landing DOOR of LIFT-01 (UP-ELEV-001): (1) B6-07 threshold: one marble piece across the clear opening on the landing
floor, top flush with the landing F.F.L. (no step drawn), its own object (never B3-04 / ARCH.THRESHOLD / B3-07 /
porcelain); (2) B6-06 surround: marble jambs + head on the landing wall face (UP-ELEV-002 / -003, union area); (3) the
OPENING: a hole in the 0.200 shaft wall, deducted whole by the neighbouring trades, never a door. Not this element: the
landing door, frame and sill (lift supplier, UP-DOOR-CLS-005 / UP-ELEV-SCHED-001), the shaft structure (T-401 / T-408).

## 2. Census by floor (R-T475-1)

| Floor | State | Evidence (DXF) | Second drawing (PDF) |
|---|---|---|---|
| GF | LANDING, 1 door (ELV-01-GF, engine OP-011) | jambs 226 / 227 1.000 apart in the 0.200 south wall ('200' 672); 4 layer-5 lines across the gap (22B landing face, 22A / 229 door lines, 228 shaft face); N / E / W inner faces 219 / 212 / 216 unbroken | sheet 03: one gap with four sill lines, 1.02 m (295 px / 2.95), centred on the 1.80 shaft; the three other walls closed |
| 1F | LANDING, 1 door (ELV-01-1F, OP-007) | jambs B96 / B97 1.000; inner faces B15 / B11 / B13 unbroken | sheet 04: 1.00 m (355 px / 3.54); '125' landing depth printed; other walls closed |
| 2F | LANDING, 1 door (ELV-01-2F, OP-002) | jambs 12AE / 12AF 1.000; '200' 1538; inner faces 1299 / 1293 / 1297 unbroken | Pages_05-06 p.1: 1.00 m (355 px); '125' landing depth, '450' lobby, +9.70 |
| ROOF | NO_LANDING | shaft closed by the +13.90 roof slab (T-401, ST 2F roof plan) | SECTION B-B: nothing above the roof but domes / parapet; no overrun door |

**3 stations, census DRAWING-CONFIRMED** (no UNKNOWN floor). Same as T-413.

## 3. Per-landing pieces (CENSUS_T475.csv)

| Station | Width | Face beside jamb L / R (DXF; PDF check) | Bands L / T / R | Door h | B6-06 surround | B6-07 threshold | Landing depth (fit) | Level |
|---|---|---|---|---|---|---|---|---|
| ELV-01-GF | 1.000 D-C | 0.700 to door D120 jamb (20E) / 0.650 to column 2F8A corner (20D + 0.05 proud); PDF >= 0.61 / 0.66 | 0.50 / 0.50 / 0.50 A-OA | HELD | HELD 1.000 .. 5.000 | 0.500 m2 + 1.000 m.l | open hall: nothing across the front within 2.5 m (NOT_LIMITING) | FLUSH +1.00 (40F) |
| ELV-01-1F | 1.000 D-C | 0.600 to wall end B16 (external) / 0.935 to door d220 jamb (AFD); PDF 0.59 / 0.99 | 0.50 / 0.50 / 0.50 A-OA | HELD | HELD 1.000 .. 4.700 | 0.500 + 1.000 | 1.250 printed (1042), fits 0.50 | FLUSH +5.50 (D18) |
| ELV-01-2F | 1.000 D-C | 0.600 to wall end 129A (external) / **0.400 to INTERNAL corner** (1289, wall 1294 / 128D); PDF 0.61 / **0.40** | 0.50 / 0.50 / **HELD 0 .. 0.400** | HELD | HELD 0.750 .. 4.280 | 0.500 + 1.000 | 1.250 printed (145F), fits | FLUSH +9.70 (134E) |

D-C = DRAWING-CONFIRMED; A-OA = ASSUMED — OWNER-APPROVED (UP-ELEV-002 0.50 band, UP-ELEV-005 0.50 depth). Door clear
height h: printed nowhere (plans, sections A-A / B-B, ST p.14), so A(h) = h (L + R) + T (W + L + R) stays the formula with
AT_LEAST the top band and AT_MOST h = storey - T (storeys 4.50 / 4.20 / 4.20 from the printed levels). Totals:
**B6-07 1.500 m2 / 3.000 m.l / 3 pcs (ASSUMED — OWNER-APPROVED depth); B6-06 HELD 2.750 .. 13.980 m2, never 0.** The
1F right face reads 0.935 on the DXF and about 0.99 on the PDF (door leaf drawn from the frame line); both hold the 0.50
band, so no quantity depends on it. Stations are NOT equivalent (2F right band), so 'typical x 3' is refused (R-T475-6).

## 4. Threshold vs floor finish and the opening deduction (R-T475-2 / -3 / -5)

- Level: the landing F.F.L. is printed on each landing within 2.2 m of the opening and no step / level line crosses the
  front: the threshold is FLUSH with the landing floor; no riser item.
- Fit: the 0.50 owner depth fits the printed landing (1.250 at 1F / 2F; GF open). A landing shallower than the depth
  would make the area HELD (0, W x landing] (K475 2F case), never the fallback.
- Position across the wall band: the four layer-5 lines at -0.100 / 0.000 / +0.050 / +0.100 suggest the landing-door
  line at 0.000 or +0.050, which would cap the threshold's in-band part at 0.100 .. 0.150 (floor part 0.350 .. 0.500
  instead of the T-421 0.300 .. 0.500). The lines carry no label or dimension, so this is **not** applied: the T-421
  HELD bound stays; named for the Checker / RFI L-1 (supplier sill depth).

| Trade at each station | Deduction | Status | Candidate today |
|---|---|---|---|
| Skirting of the landing face | clear width 1.000 whole, 0 jamb skirting | DRAWING-CONFIRMED | GF L-71e2e002 OP-011 'PASSAGE' 1.000 deducted, no jamb; 1F L-ba3599ec OP-007 'PASSAGE' 1.000, no jamb (T-296 ledger); 2F: the T-443 lobby lines (OP-002 as LIFT, queued). Quantity right; GF / 1F class word 'PASSAGE' -> 'LIFT' is text only (0.000 lm) |
| Wall finish of the landing face | opening W x h AND the surround area | HELD with h (opening 1.000 x h; surround bound above) | the surround is not painted: when B6-06 is valued the paint / plaster of that face loses the same m2 (T-413 s.7.5) |
| Landing floor finish | threshold floor part | certain 0.300 deducted, 0 .. 0.200 HELD (T-421) | GF L-7625f35c, 1F L-b06400d4, 2F lobby line (T-421) |
| B3-04 / ARCH.THRESHOLD / B3-07 / B4-09 | none | NOT_APPLICABLE | the 3 ARCH.THRESHOLD bands listed without quantity (T-421) |

## 5. Methods side by side (ERS s.2.2) and freelancer

| Method | Stations | Surround | Threshold |
|---|---|---|---|
| Owner manual (UP-ELEV-001 .. 005) | one per landing door | 0.50 bands, union, needs h | drawn width x 0.50 |
| Drawing-derived (DXF + PDF, this run) | 3 (roof closed) | widths not printed; 2F right capped at 0.400 on both drawings; h not printed | 1.000 drawn on both drawings; depth not printed; fits the 1.250 landing |
| Candidate V3.0.38 (T-421) | 3 | HELD 2.750 .. 13.980 | 1.500 m2 / 3.000 m.l |
| Freelancer | no row for either (T-413 census of his marble sheet) | - | - |

Difference engine vs drawing: **0.000** on every station (summary.json `candidate_agreement` all true). Freelancer: no
row -> verdict proposals: B6-07 **ENGINE_RIGHT on scope** (UP-ELEV-005; 1.500 m2 vs 0, hand: 3 x 1.000 x 0.500), B6-06
**ENGINE_RIGHT on scope, quantity HELD** (UP-ELEV-001 / -002 / -003; bound 2.750 .. 13.980 m2 vs 0). The 6 B6-07 lines
(3 m2 + 3 m.l) are confirmed piece by piece on two drawings: proposed for the Checker as VERIFIABLE (width
DRAWING-CONFIRMED, depth owner default), never DRAWING-CONFIRMED in m2.

## 6. Stream F proposal (lane I; nothing edited here)

1. Keep the 6 B6-07 lines as they are (L-c32effca / L-f2b76041, L-9840d1da / L-64dd750f, L-eba7ac43 / L-e29e5748); add
   to each the census evidence (jamb handles + PDF sheet) and `landing_depth` 'NOT_LIMITING' / 1.250.
2. Keep the 3 B6-06 lines HELD (L-b66b8e76 1.000 .. 5.000, L-d788f643 1.000 .. 4.700, L-fdbd9636 0.750 .. 4.280), with
   the missing facts by name: door clear height (supplier / RFI L-1) at all three; 2F right band width (architect).
3. Skirting GF L-71e2e002 / 1F L-ba3599ec: change only the deduction class text OP-011 / OP-007 'PASSAGE' -> 'LIFT'
   (0.000 lm); 2F as T-443.
4. When the door height arrives: value B6-06 and deduct the same m2 + the opening W x h from the landing-face paint /
   plaster lines in the same package (R-T421-1: pieces tied at change time).

HELD (never 0): B6-06 at all 3 stations (h), 2F right band (0 .. 0.400), threshold floor-part position (0 .. 0.200 per
station). Unsupported: threshold thickness / edge detail, the bed under the threshold, reveal lining of the 0.200 jambs.

## 7. Rules, tests, lessons row (proposed)

LIFT_LANDING_CENSUS_V1 `research/agents_t475/lift_landing_census_v1.py` (R-T475-1 .. 6, stdlib, imports T-413's module).
`research/agents_t475/t475_alsenan.py --write / --check` reproduces `CENSUS_T475.csv` and `summary.json`. Tests
`tests/t475_lift_landing_census/` (hand villa K475, not Alsenan: GF / 2F with a printed surround detail, 1F without ->
HELD 0.950 .. 4.050; 2F landing 0.40 deep -> threshold HELD 0 .. 0.360; family bound 4.060 .. 7.160 / 0.900 .. 1.260;
adverse: mirror, rotation 0 / 37 / 90 / 180, mm refused, UNKNOWN floor never copied, roof claimed without opening
refused, through-car two stations, catalogue 2.10 m height refused, detail band wider than the face refused, level
UNKNOWN without F.F.L.; Alsenan pins).

Lessons row (ERS s.7): | 2026-11-02 | an owner fallback depth for a lift threshold was applied without checking that the
landing in front holds it | a default dimension is a geometric claim about the space it lands in, checked on the
station's own plan | every default depth / width is checked against the printed landing depth / face; where it does not
fit, the piece is HELD with the bound (0, available], never the default and never 0 (every villa) |
tests/t475_lift_landing_census (K475 2F 0.40 landing) | PROPOSED

## 8. Checker re-measure (one landing): ELV-01-2F

P7757.dxf 2F: jambs 12AE / 12AF 1.000; landing face 1289 0.400 to the internal corner (1294 / 128D, door d220 12C2 in
that wall); left 128A 0.600 to wall end 129A; '1250' 145F landing face to 1283; '+9.70' 134E. PDF Pages_05-06 p.1:
'125' and '450' printed beside the shaft, opening about 1.00, lower face about 0.40 to the perpendicular wall.
