# T-322 FF raft and lift-pit foundation component ledger; F-T320-03 settled (development villa; rule for every villa)

Worker 1 (lane S), 2026-10-29, run unknown. Research piece, unwired: no engine, candidate or released line changed;
integration is a lane I package after the Checker's verdict. Development villa, not an accuracy claim. Drawings named
by Drive folder and title; entities by DXF handle; sizes, areas and counts only.

Files: `lift_base_ledger_v1.py` (LIFT_BASE_LEDGER_V1, stdlib), `t322_alsenan_check.py` (reads the own-read input and the
merged ledgers T-170 / T-204 / T-219 / T-233 / T-320 read only) -> `LEDGER_T322.csv`, `summary.json`;
`ALSENAN_LIFT_BASE_INPUT.json` (values only); tests `tests/t322_lift_base_ledger` (20).

## 0. Inputs (own reads, this task)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179...38079 (= T-233 manifest) | FF outline 1B2B 4600.0 x 4500.0 (closed S-FOOTINGS, tag 1676 'FF'); FTB INSERT 2B1E (FF W 460, H 450, DEPHT 55); ring S-BW 10EB 2200 x 2200 / 10EA 1800 x 1800; columns S-COL.BON 1099 / 1093 / 1096 / 1090; plot line S-BOUN 1658; every footing entity within 1.5 m |
| "ST7757.pdf" | 74da1523...337e3 | p.9 Schedule of Footings row FF 460 / 450 / 55, remark 'lift base' (Arabic) (110 dpi); p.13 both typical footing details (110 dpi); p.14 lift detail at 110 / 400 dpi AND its vector lines (PyMuPDF, page rotation 270 resolved) |

## 1. The physical element, layer by layer (ERS s.2.1), each component once

Governing detail: ST p.14 'DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT)' (the specific detail of this
element; p.13 'TYP. DETAIL OF ISOLATED FOOTING.' is the typical of the other isolated footings). p.14, bottom up:
'10cm Plain con.' (blinding, drawn beyond the side build-up) / 'Water proofing membrane' (no thickness) / '5cm Screed'
/ footing 'AS PER SCHEDULE' / pit walls '20' on the footing top, pit floor = footing top, pit depth 'As Per Lift
Manufactures recommendations' / on the footing sides and the outer wall faces: membrane + 'Protection Board' (no
thicknesses) / outside: 'Well graded clean compacted fill from excavation material'.

| Component | Quantity | Status | Source | Owner line |
|---|---|---|---|---|
| Blinding (plain concrete 0.10) | **HELD**, AT_LEAST 4.60 x 4.50 x 0.10 = 2.070 m3 | HELD (projection not printed on p.14) | p.14 '10cm Plain con.'; edge drawn, not dimensioned | CONC.BLINDING |
| Membrane under the screed | area 20.700 m2; volume HELD (no thickness on p.14) | DC / HELD | p.14 label; T-219 | WP.LIFT_PIT_MEMBRANE_FIXED |
| Screed 0.05 under the raft | 20.700 m2, 1.035 m3 | DRAWING-CONFIRMED | p.14 '5cm Screed'; T-219 | SCREED.LIFT_PIT_BASE |
| Raft FF | 4.60 x 4.50 x 0.55 = **11.385 m3** | DRAWING-CONFIRMED (outline = schedule) | 1B2B + 2B1E + p.9 | CONC.FOOTING |
| Pit floor | = raft top: 0 additional | DRAWING-CONFIRMED (not a volume) | p.14 | none (listed so it is never added twice) |
| Pit walls, plan | 2.20^2 - 1.80^2 = 1.600 gross; net of C1 / C2 / C2 / C9 0.10 + 0.10 + 0.10 + 0.20 = **1.100 m2** | DRAWING-CONFIRMED | 10EB / 10EA, columns; = T-204 | CONC.LIFT_PIT_WALL |
| Pit walls, concrete | 1.100 m3 per m of pit height | HELD (pit depth not printed) | p.14 | CONC.LIFT_PIT_WALL |
| Lift columns in the ring band | 0.50 m2 | column / neck lines (R-CONC-OWN-1) | T-204 | not here |
| Side membrane / board thickness | not printed | HELD (changes the neat plan and the side layers' volume, not their areas) | p.14 | WP (T-219 areas 10.920 + 15.810 / 26.730 m2) |
| Backfill round the pit | material printed | HELD with the levels | T-170 / T-320 | B1-03 |

## 2. F-T320-03: why T-233 and T-170 disagree on the FF blinding (ERS s.2.3-2.4)

- T-233 2.256 m3 = (4.60 + 2 x 0.10)(4.50 + 2 x 0.10) x 0.10 = 4.80 x 4.70 x 0.10, with `projection_m 0.1` from p.13
  applied to ALL 26 outlines (ALSENAN_FOOTING_INPUT.json `source.projection_source`), FF included.
- T-170 HELD: 'p.14 prints no blinding projection'.
- Own read of p.14: correct, nothing is dimensioned. The p.14 detail is the governing one for FF (its title names this
  case; p.9 marks FF 'lift base'); its side build-up is different from p.13 (membrane + protection board up the sides,
  drawn outside the footing face), so p.13's '10 | L x W | 10' is a dimension of another element type.
- **Cause: INHERITED OFFSET** (a typical-detail value of other footings carried onto an element with its own detail).
  Not a measurement error in T-233's arithmetic (2.256 is right for p = 0.10).
- Scale evidence (for the designer, never a quantity): p.14 is drawn at one scale, proven by two printed values:
  '5cm Screed' 7.08 pt and '10cm Plain con.' 14.16 pt = 141.6 pt per m both (1:20.0). At that scale the blinding edge
  is 21.24 pt = **0.150 m** beyond the footing face on both sides (0.080 m beyond the drawn 0.051 / 0.050 m board +
  0.020 m membrane); the membrane under the screed is drawn 0.020 m (= p.13's printed '2'). The drawing is a typical:
  its footing is drawn 0.40 deep, i.e. not to the FF size, so a scaled length is evidence of intent only.
- **Corrected ledger figure: HELD, AT_LEAST 2.070 m3** (the screed and the raft stand on it; p.14 draws the blinding
  under the whole footing), readings 2.256 (p = 0.10, INHERITED from p.13) and 2.352 (p = 0.15, SCALED off p.14). Impact
  between the readings 0.096 m3; 0.018 m3 per cm of projection. Never 0, never the other ledger's figure.

## 3. Closures (acceptance 4)

| Against | Merged figure | This ledger | Residual |
|---|---|---|---|
| T-233 CONC.FOOTING FF | 11.385 | 11.385 | 0.000 |
| T-233 CONC.BLINDING measured | 14.990438 = 24 pits inside the plot + FF 2.256 | 12.734438 measured + FF HELD | FF piece moves out of measured: -2.256 m3 to HELD |
| T-320 24 pits' blinding inside the plot | 12.734438 | 12.734438 | 0.000 |
| T-320 Z1 established | 105.162974 (no FF value) | no FF value added | 0.000 (FF blinding hold re-based: 0 .. 2.256 -> HELD, AT_LEAST 2.070 when wholly below EG) |
| T-219 lift screed | 20.70 m2 / 1.035 m3 | 20.70 / 1.035 | 0.000 |
| T-204 ring net | 1.100 m2 | 1.100 m2 | 0.000 |
| T-170 FF neat plan (HELD) | HELD | HELD, AT_LEAST 20.70 m2; readings 22.56 (p 0.10) / 23.52 (p 0.15) | same hold, same cause |
| Second plan | ring on the GROUND BEAMS plan 7C2 / 7BE / 7BD | = 10EB / 10EA shifted -38724.4 mm (T-205), same size | AGREE; DXF carries no lift detail (p.14 is PDF only) |
| Neighbours | F12 1ABF clear gap 0.5998 m; others >= 0.71 m; plot line 3.70 m | no blinding overlap in either reading (gap >= 0.35 m); no D-14 part | none |

## 4. Engine, candidate and freelancer (m3)

| Item | Drawing (this task) | Released A / candidate | Freelancer | Verdict proposal |
|---|---|---|---|---|
| FF raft | 11.385 DC | 11.385 (in the footing line, T-233) | in his footings sheet (T-233: 65.634 incl. FF) | ENGINE_RIGHT (unchanged) |
| FF blinding | HELD, >= 2.070 (2.256 / 2.352 readings) | candidate footing blinding 15.179437 PROVISIONAL carries FF at p = 0.10 (2.256, T-193 union) | his whole-plot plate 47.055 (RULE_DIFFERENCE, T-233) | candidate basis WRONG for FF (inherited offset): lane I should hold the FF piece (-2.256 m3 from the provisional line to HELD); UNRESOLVED (designer) for the value |
| Lift screed / membrane | 1.035 m3 / 20.70 m2 DC | no line | no row (T-219) | missing in both (T-219) |
| Pit walls | 1.100 m2 x h HELD | no line | 2.40 m3 incl. the columns (T-204) | UNRESOLVED (pit depth) |

## 5. Rule, test, lessons row

R-LIFT-BASE-1 (proposed, every villa; provenance T-322 from ST p.13 / p.14 of this set; a new rule version when
adopted): a dimension of an element is taken from its GOVERNING detail; a value printed only on a typical detail of
another element type is an INHERITED reading, never DRAWING-CONFIRMED; an unprinted blinding projection leaves the
blinding HELD with the AT_LEAST bound (plan of what stands on it x printed thickness); a scaled length off a detail whose
scale two printed dimensions prove is designer evidence, never a quantity; the pit floor is the raft top and the pit
walls start there (a wall reaching into the raft, or a raft depth carrying the wall, is refused).
Tests `tests/t322_lift_base_ledger` (20): villa R by hand (raft 4.00 x 4.50 x 0.55 = 9.900, pit 1.60 x 1.80 in a 0.20
ring 1.520 m2 x 1.40 = 2.128, blinding p 0.10 printed 1.974, screed 0.900; corner column 1.480 / 2.072; proud column);
adverse: offset not printed -> HELD >= 1.800; offset from a typical detail -> INHERITED, HELD; scaled reading never a
quantity, inconsistent scale refused, one printed dimension refused; pit wall in raft and wall refused (two ways), pit
floor slab refused; pit height missing HELD, HELD with value refused; ring outside raft, column into pit refused;
outline vs schedule CONFLICT; cm / mm identical; unit undeclared refused; mirror and quarter turn identical; no
governing detail / no source refused; Alsenan pins.

Lessons row proposed (ERS s.7): 2026-10-29 | FF blinding 2.256 m3 measured in one merged ledger and HELD in another
(F-T320-03) | The p.13 typical footing projection was applied to every outline, including the lift footing that has its
own detail (p.14) with a different side build-up and no projection dimension | Take an element's dimensions from its
governing detail; a typical detail of another element type gives an INHERITED reading only; an unprinted projection
leaves the blinding HELD with its AT_LEAST bound (every villa) | tests/t322_lift_base_ledger (inherited offset -> HELD;
printed on the governing detail -> DC) | PROPOSED

## 6. For the Checker (re-measure from the drawings)

1. p.14 lift detail: no projection dimension under the footing; labels '10cm Plain con.', '5cm Screed', membrane with no
   thickness; vector lines (displayed sheet, pt): blinding x 65.12 .. 432.20, y 339.76 .. 353.92; footing faces x 86.36
   / 410.96; screed y 329.80 .. 336.88.
2. FF 1B2B (136342.0, 43148.1)-(140942.0, 47648.1) vs FTB 2B1E and p.9 row FF.
3. Ring 10EB / 10EA and the four columns: net 1.100 m2.
4. F12 1ABF clear gap 0.5998 m to FF.

## 7. Not done / uncertain

- Pit depth (designer / lift supplier, D-43), side build-up thicknesses, membrane thickness on p.14: HELD.
- Whether the other 25 footings' p.13 offset is right is not in scope (their detail is the typical; T-233 Gate A).
- No candidate line changed; the lane I correction (FF piece of the provisional footing-blinding line to HELD) is a
  proposal for the integration package.
