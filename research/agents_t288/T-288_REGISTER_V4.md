# T-288: blockwork wall register v4, wall heights under the six sunken slab panels (development villa; every villa by R-T288-1)

Worker 2, claim 2026-10-25 03:41 UTC, lane A, gate 2. Base: working head e418c5e0 (register v3, T-285). Read-only over
register v3, the T-274 exact pieces (MERGED aba9399a), T-213 (MERGED d5df7d1f) and the Checker's 2026-10-25 01:43 - 02:09
whole-wall re-measures. No engine module, rule or knowledge file changed; no BOQ line moves; released default stays V2.9
+ route G. Register v4 is a research revision for lane I (T-279) to carry, NOT RELEASED. Drawings: Drive 'Alsenan
chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha ab54dd55) and 'ST7757 dxf.dxf' (sha 9f9d1179); no coordinate,
image or client name is committed (CLIP_T288.json holds handles and lengths only; a test asserts it).

ERS read: s.2.1 (physical element first), s.2.4 (reconcile to named causes, residual named), s.3 (build before deduct;
installed vs procurement: block units stay T-176), s.4 (rule + test with normal and adverse case), s.7 (lessons row).

## 1. Engineering question and answer

What is the underside of the member over each wall piece that lies under a sunken (lowered) slab panel, and what
height does that piece take? PHYSICAL ELEMENT: a block wall rises from its floor to the underside of whatever is over
it. T-213 rules a sunken panel is the same 0.16 slab lowered at full thickness ('T 16' printed inside hatch 280), so
its underside is d lower than a normal panel's; d is printed on no sheet (D-41). A wall piece under it is therefore
**4.50 - 0.16 - d = 4.34 - d** on the GF roof, never 4.34 (the normal soffit, what v3 booked) and never 0. Bounding
beams keep their own soffit (the panel steps down between them, T-213), so pieces under beams do not move.

## 2. Which pieces lie under a sunken panel (own clip, independent of the register)

alsenan_clip_t288.py: the six T-213 hatch regions (annotation islands united back, T-213 rule (a)); frames by matching
every column outline (GF 30 / 30, 1F 20 / 20, residual 0.0 mm); every layer-1 wall-face line of P7757.dxf clipped by
each region shrunk 20 mm; each wall's axis (midway between its two faces, spanning both sides' faces, so an opening gap
does not shorten it) clipped by the full region.

| Wall | Panel (hatch) | Census piece m (v4) | Own axis clip m | Faces in hatch m | Agreement |
|---|---|---|---|---|---|
| GF-W12 | GF-081 (298) | 0.4500 | 0.4000 + 0.0500 hatch-to-column gap = 0.4500 | 0.400 / 0.650 | AGREE: the hatch stops 0.05 m short of column 36E's face round the 'B28' label, no structural line in the gap (T-139 face 4.1176 vs hatch 4.1076 = this 0.0100 m2 strip) |
| GF-W16 | GF-141 (280) | **2.9500** (T-274 2.9489) | 2.9500 | 1.450 / 1.404 (openings W09 / W10 in the faces) | AGREE after the B5 correction below |
| GF-W20 | GF-016 (275) | 0.9678 | 0.9678 | 0.844 / 0.968 | AGREE |
| GF-W31 | GF-016 (275) | 1.0311 | 1.0751 | 1.000 / 1.106 | JUNCTION (named, below) |
| GF-W32 | GF-015 (276) | 0.3105 | 0.3117 | 0.059 / 0.059 | BAND EDGE 1.2 mm (named, below) |
| GF-W32 | GF-016 (275) | 0.4806 | 0.6210 | 0.273 / 0.142 (door gap) | JUNCTION (named, below) |
| GF-W34 | GF-015 (276) | 1.7231 | 1.7231 | 1.685 / 1.798 | AGREE |
| **Total** | | **7.9131 m** | | | Checker's own scan 02:00: 7.913 m |

No wall line lies inside hatch 287 (GF-128) or 5BF (1F-018). Seven face lines lie ON a panel edge and are outside after
the 20 mm shrink (A2 on 280; 158 / 159 on 287; ADB / ADC / B12 / B14 on 5BF): each wall's other face is outside the
panel, so the wall stands under the bounding beam, not the lowered slab. Three short lines inside panels are cross
lines of claimed walls (3C8 / 3C4 W09 / W10 jambs in GF-W16, 26C the glazing cap of GF-W12); no face line is unclaimed.

Named differences (never silently taken):
- **GF-W16 B5 edge (+0.0011 m, corrected):** T-274's route-G band puts B5 at 0.0012 + 0.1999 = 0.2011 m, the drawn band
  (ST 281 / 27C, 0.200 = SBT W 20) and the hatch 280 edge give 0.2000 and a sunken piece 2.9500; the Checker's own
  02:00 cut and this clip agree, so v4 re-cuts the wall: CB8 0.1000 at 3.75 + slab GF-169 1.2000 at 4.34 + B5 0.2000 at
  4.00 + GF-141 2.9500 at 4.34 - d = 4.4500 = census (residual 0.0000).
- **GF-W31 / GF-W32 at the 3-way 45-degree junction under GF-016 (+0.0440 / +0.1404 m):** the face-span axis runs on
  through the junction of GF-W20 / GF-W31 / GF-W32; the census run (T-125 / T-215, MERGED) stops at the junction bound
  and books the junction once. The census pieces are kept (they close the census); the Checker's re-clip of the
  junction is open. Bound of the effect: at most 0.184 m on the d coefficient (0.184 d m2), nothing at d = 0.
- **GF-W32 under GF-015 (+0.0012 m):** route-G band edge of the beam between 275 / 276 vs the drawn hatch edge; census
  piece kept, listed (d coefficient only; both neighbours are at 4.34 at d = 0).

## 3. Register v4 (one established revision)

| Basis | v3 m2 | v4 = value at d = 0 (UPPER BOUND, not a quantity) - HELD term | Determinate (d-free walls) |
|---|---|---|---|
| A (37 walls with a figure) | 449.5934 | **449.6007 - 7.9131 x d m2** (d HELD, D-41) | 402.7988 m2 on 31 walls (72.8414 m3) |
| B (A + T-261 r3 parts) | 625.8957 | **625.9030 - 7.9131 x d m2** | 579.1011 m2 on 42 walls |

The six walls HELD ON DROP carry 'U - L x d' (U 46.8019 m2 together, L 7.9131 m): GF-W12 1.9530 - 0.4500 d; GF-W16
15.4360 - 2.9500 d; GF-W20 4.2398 - 0.9678 d; GF-W31 5.6455 - 1.0311 d; GF-W32 9.1294 - 0.7911 d; GF-W34 10.3982 -
1.7231 d. GF-W20 / GF-W34 keep their CB2 width CONFLICT increments (0.0170 / 0.0139 m2, D-27) by name. Their 7.9131 x
4.34 = 34.34 m2 at the normal soffit is not established.

Determinate split (basis A, WORKFLOW_CONTROLS s.5): VERIFIED **297.847 m2 on 18 walls** (= the Checker's SCOREBOARD
share after 02:09; GF-W12 withdrawn, 1F-W22 / 1F-W20 / 1F-W00 / 1F-W06 / 1F-W05 / GF-W01 added at the Checker's own
values, R-T285-1 rule 2); DRAWING-CONFIRMED 28.7331; ASSUMED — OWNER-APPROVED 76.2187 (GF-W32 left this class for HELD
ON DROP); HELD: the 6 walls above + 28 walls wholly HELD + 10 walls' HELD increments.

Reconciliation v3 -> v4 at d = 0: +0.0073 m2, residual 0.0000 (RECONCILIATION_V4.csv):

| Wall | v3 | v4 | Change | Cause |
|---|---|---|---|---|
| GF-W01 | 62.1550 | 62.1640 VERIFIED | +0.0090 | 0.0026 m sliver inside B26's drawn outline at 3.65 (was HELD) +0.0095; v3 had kept the T-143 gross over T-274's exact -0.0009; Checker own 62.1638 reported 62.164 +0.0004 |
| GF-W16 | 15.4356 | 15.4360 - 2.9500 d | +0.0004 | B5 drawn band (above) |
| 1F-W06 | 54.4897 | 54.4860 VERIFIED | -0.0037 | W24 at its drawn jamb 1.5523 (not the label 1.550) -0.0035; Checker own gross 57.7744 vs 57.7747 and rounding -0.0002 |
| 1F-W05 | 19.3030 | 19.3030 VERIFIED | 0.0000 | B23 0.3500 / CB10 3.6500 (not 0.349 / 3.651) -0.0003; Checker own W14 jamb 2.4498 and rounding +0.0003 |
| 1F-W00 | 12.9336 | 12.9350 VERIFIED | +0.0014 | Checker own value (census 6.571 vs run 6.5708, rounding) |
| 1F-W20 | 24.5068 | 24.5070 VERIFIED | +0.0002 | Checker own 24.5073 reported 24.507 |
| 1F-W22 | 20.4010 | 20.4010 VERIFIED | 0.0000 | class only |
| GF-W12 / W20 / W31 / W32 / W34 | as v3 | U - L x d | 0 at d = 0 | R-T288-1 drop term |

The six width-CONFLICT walls keep both readings exactly as v3 (GF-W19, GF-W20, GF-W22, GF-W34, 1F-W16, 1F-W11).

## 4. Engine vs freelancer

No freelancer row per wall (one height per floor); no total verdict while 28 walls are wholly HELD. Effect of this
revision on the comparison: the GF internal and external sections lose 7.9131 x d m2 against v3 (d HELD), plus +0.0073
m2 of named corrections. WHO IS RIGHT on the six walls: UNRESOLVED until D-41 prints d (the freelancer's one height
per floor ignores the sunken panels; RULE_DIFFERENCE on the method, the quantity waits on d).

## 5. Rule, tests, lessons row

- **R-T288-1** (register_v4.py, PROJECT-INDEPENDENT; provenance Verifier 2026-10-25 02:00 + T-213): a wall height piece
  under a slab panel flagged sunken / lowered takes storey - t - d with d HELD until printed (storey - t only when the
  drawing shows a thinned slab with a flush soffit); the region is the hatch with its annotation islands and member gaps
  closed, a face on its edge is outside; the wall carries 'U - L x d', never a plain net, never 0; pieces still close the
  census; a ruling on a level re-cuts every element whose top or bottom is that level.
- **tests/t288_register_v4** (16): villa V (not Alsenan) hand truth: V-W1 wholly under 3.000 m (10.950 - 3.000 d), V-W2
  partly 2.000 m (14.530 - 2.000 d), V-W3 normal 10.950; adverse: storey - t booked on a sunken piece refused, plain
  net / 0 / wrong length / drop term without a panel refused, face on the edge not clipped, annotation island not
  splitting (3.000 not 2.600), hatch short of a column closed (2.000 not 1.950), pieces not closing / millimetres
  refused, mirror and rotation equal; Alsenan: --check reproduces, 7.9131 m on six walls, totals, residual 0, VERIFIED
  297.847 on 18 walls without GF-W12, every register row passes the rule, no coordinate in the clip file.
- **Lessons register row (s.7, proposed):** 'a level ruling on one trade (T-213: sunken panel = lowered soffit) did not
  reach the trade under it (blockwork heights); after any level ruling, re-cut every element whose top or bottom is that
  level' -> CLOSED by this register when merged (R-T288-1 rule 5 + the NORMAL_SOFFIT_BOOKED refusal).

## 6. For the Checker (re-measure)

1. Re-clip GF-W16 (Drive 'Alsenan chalet project' / P7757.dxf faces 9F / A0 / A1 and AE / AF / B0; ST7757 hatch 280,
   B5 band 281 / 27C): 2.9500 m under GF-141, net 15.4360 - 2.9500 d. 2. Re-measure GF-W01: 62.1640 VERIFIED, the B26
   sliver 0.0026 m at 3.65. 3. Optional: the GF-016 junction (GF-W31 1.0311 / GF-W32 0.4806 census vs axis 1.0751 /
   0.6210). 4. D-41 affected quantities now include blockwork heights 7.9131 m x d (Lead: S13 of the RFI package).
