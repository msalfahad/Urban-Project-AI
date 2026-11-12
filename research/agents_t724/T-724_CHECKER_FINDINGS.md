# T-724 concrete / formwork Checker findings round (lane S, research only)

Worker 1, 2026-11-12, branch `agents/task-T-724`, on candidate ARCH_TAKEOFF_V3.0.72 (T-703 line index). Nothing wired,
released or VERIFIED; the candidate is not restated (concrete round 10 / the formwork hub wire it). Rules
`t724_rules.py` (R-T724-1 .. 4, every villa), builder `t724_alsenan.py` (inputs sha256-pinned in `PINS.json`) ->
`out/T724_FINDINGS.json` + `out/T724_CENSUS.md`, tests `tests/t724_checker_findings`. ERS s.2-7; R-T721-1..3, R-T714-1,
R-T712-1..3, R-CONC-OWN-1, R-T704-2, UP-QTY-STATUS-001, R-T696-1.

Own reads this run (Drive 'Alsenan chalet project', read-only, private copies only): 'ST7757 dxf.dxf' (sha 9f9d1179)
and 'ST7757.pdf' p.7 (rendered, viewed). Only drawing facts (handles, distances, labels) are recorded.

## (1) F-V721-1 east dome ring L-ab37afa1: floor KEPT at AT_LEAST 0.115155 m3

Physical element: the ring under the east first-floor-roof dome opening, section referenced by 'SEE DETAIL' to ST p.7.
Drawn section (DXF): outline 1A0A, link 1A0B inside it; top 3T16 (1A47; circles 1A33 / 1A49 / 1A35 on the link's top
edge), bottom 3T18 (1A4B; 1A22 / 1A26 / 1A24), side '2T14/20cm' (1A37 with leader 1A36 to circle 1A2B, 1A2D opposite),
a second side level drawn 1A2F / 1A31 with no label, links 8T8/m (1A29); an unlabelled smaller circle 1A4D near the top
(the dome shell's T12/15cm lapping in; off the link verticals). Depth dimension 182F measures 3750 drawing units but its
text is overridden 'AS PER ARCH'. The PDF title sheet note reads 'THE BUILDER TO WORK WITH STATED DIMENSIONS. NOT TO
SCALE DRAWING.' and the detail is marked N.I.S.

Reasoning (R-T724-1): a set labelled by a pitch ('/20cm') has as many levels as the depth needs, so its level count is
a function of the depth we are bounding; the two circles drawn are a picture of the pitch on a not-to-scale sheet that
tells the builder to use stated dimensions, not a stated number. Counting the second level would derive the depth from
a drawing of the depth. The labelled level counts once (it is tied to the faces: circles on the link verticals), the
counted top and bottom levels count, the unlabelled 1A4D never counts.

| Reading | Depth floor m | m3 (x least plan 1.7993 m2) | Status |
|---|---|---|---|
| 2 x 0.008 + 0.016 + 0.014 + 0.018 (one pitch level) | 0.064 | **0.115155** | KEPT (T-721) |
| + second drawn side level 0.014 | 0.078 | 0.140345 | NOT ADOPTED (pitch picture, N.I.S.) |
| scaled: drawn pitch 1000 units = 0.20 m -> 1:5; outline 1000 x 3750 -> 0.20 x 0.75 | 0.75 | (1.349) | NOT ADOPTED (measurement of an N.T.S. detail whose depth text is withheld) |

Cause named: D-28, ring depth not stated (182F overridden; the architect's sections draw no ring). New fact for D-28:
the drawn pitch and the 0.20 plan width are mutually consistent with 1:5, so a designer answer of 0.75 would agree with
the drawing; that is for the designer to state. Formwork: the T-714 ring line keeps its FLOOR_ONLY soffit 1.7993 m2.

## (2) F-V714-1 scaled soffits: 4 lines restated, 6 stand

The 0.2502 is T-402's `drawn_width_m` column, which is schedule b x the member's concrete ratio (0.433997 / 0.34692 x
0.20 = 0.250198): the band polygon carries joint slivers, so it is not the edge distance. Own edge reads (perpendicular
distance between the two LINEs, both ends): 274 / 278 **0.250**, 5E7 / 5E8 0.300, 434 / 433 0.400, 2CE / 463 0.200,
5CD / 5CC 0.200. R-T724-2: scale by (other / drawn edge width).

| Line | Member | Before m2 | After m2 | Low shift |
|---|---|---|---|---|
| L-3280c42c | CB2 BM-GF-055 span 1 | 3.559227 .. 3.733233 | **3.559782 .. 3.733233** | +0.000555 |
| L-b4968289 | CB2 span 2 | 3.434990 .. 3.603002 | **3.435526 .. 3.603002** | +0.000536 |
| L-030e2ec6 | CB2 remainder | 0.000095 .. 0.000120 | 0.000096 .. 0.000120 | +0.000001 |
| L-59f0c115 | CB2 remainder | 0.000195 .. 0.000245 | 0.000196 .. 0.000245 | +0.000001 |
| 6 others (CB10 x3, B21, B29, B6) | edge = recorded width | unchanged | unchanged | 0 |

Hand check L-3280c42c: soffit 0.867255 at 0.250 (implied length 3.46902 vs f2f 3.4692; at 0.2502 it would be 3.46625,
2.9 mm short) -> 0.867255 x 0.20 / 0.250 = 0.693804; + side 2.310933 + edge band 0.555045 = 3.559782 (= Checker).
Formwork BOUNDED family 87.941284 -> **87.942377 m2** (+0.001093); high 103.192739 unchanged. Implied lengths beside:
B21 7.356 vs f2f 7.482 (soffit netted at joints), B29 6.757 vs 6.740 (skew-ended trapezoid: edges 6.773 / 6.741).

## (3) F-T723-3 GROUND_BEAM L-fb7a6431: one state = HELD BLANK, cap 3.5256 m3 beside

Index 0.0 .. 3.5256. Drawing: S-BOUN bands 7FE 8.344 + 7FC 0.230 + 810 0.240 = 8.814 m2 / 0.20 = 44.07 m (own read)
x 0.20 x 0.40 (p.14 '(20x40)', A-A, T-403 Gate A) = 3.5256 gross; columns 20 x 30 'SEE ARCH PLAN': 0 drawn in the bands
(own read), count not printed (M4 / Q-28), each takes 0.024 m3. A low of 0 is no floor (R-T724-3): the line is HELD
BLANK with the gross as a cap beside, never among the BOUNDED. Ground-beam family: **8 BOUNDED 1.178378 .. 1.571171 m3**
(= the T-704 code form) + this line capped 3.5256 + 17 AT_LEAST (T-712) + 3 named blanks; T-712's '9 bounded ..
5.096771' is restated, not added. Owner manual method: none beyond the print; freelancer 7.560 (T-403, -53.4 % on the
gross, ENGINE_RIGHT on width / depth) unchanged.

## (4) Drawn roof-edge strip in no line: 0.378618 m2, each piece NAMED once

| Piece | Where (own read) | m2 (= m3 per m depth) | Owner |
|---|---|---|---|
| GF strip at column 366 | edges 2C6 / 2C7 unbroken 4.325 m; column x 3.000 .. 3.800 from the west end, north face on 2C6 | 0.160000 | NAMED blank child of BAND0031 (D-05 / D-26) |
| 1F strip at column 68C | edges 5E1 / 5E6 unbroken 4.325 m; column 3.000 .. 3.800 | 0.160000 | NAMED blank child of BAND0013 |
| GF NW corner | square 0.20 x 0.20 inside ARC 316 (r 0.231334) | 0.029309 | NAMED blank corner child |
| 1F NW corner | square inside ARC 647 (same r, same offset) | 0.029309 | NAMED blank corner child |

Neighbours checked on the DXF: the GF west strip is L-aba59a21 (BM-GF-061, 0.2 x 4.1): outer edge 2B6 / 2FB / 2B7 at
0.200 from 2B5, from beam face 2AF to the y of 2C6 = 4.100 m (= its line 0.82 m2; ticks 2F9 / 2FA / 2FC inside it), so
it ends at the corner square's south face; the 1F west strip L-a9d5e7dc (5E7 / 5E5, 7.500) ends at the y of 5E1. The
route G band overlay (SH06 GF) shows BAND0031.1 / .2 with the 0.80 gap at the column and no band over the corner.

R-T724-4 / R-CONC-OWN-1: no line's stated basis contains a piece (the span lines stop at the column faces; the north
strip starts at the square's east face, the west strips end at its south face), and no two do; folding a piece into
the neighbouring span line would be a choice, so each is named with its exact area. No double count: columns and beam
bands lie south of the strip edge (0 overlap); the T-139 slab faces GF-063 / 1F-043 are EDGE_HELD with no slab m3.
Named record residuals (line lengths vs drawn): GF L-634cefe5 3.0005 (0.5 mm past the column face, 0.0001 m2), 1F
L-67f3d325 2.9987 and L-54e397fe 0.5238 (1.3 / 1.2 mm short, 0.0005 m2 in no record): engine-walk rounding, named.

## Verdict proposals

(1) UNRESOLVED (D-28; floor only, 0.115155 stands). (2) ENGINE (T-714 piece) WRONG by +0.001093 m2 on the low end,
corrected here; no freelancer formwork row (NOT_COMPARABLE). (3) census convention fixed, no quantity moves.
(4) NOT_COMPARABLE (no freelancer row), 4 named blank children proposed for the wiring.

## Lessons row (ERS s.7, proposed)

| 2026-11-12 | 0.2502 scale used for 0.250 drawn soffits; a 0 .. x line counted bounded; a second drawn side level offered as a
depth bound | a derived width stood in for the edge distance; a census read the index's 0 as a low; a pitch picture read as a
count | a scale uses the drawn edge width; 0 .. x is a capped blank; only stated bar counts bound a depth (R-T724-1..4,
every villa) | tests/t724_checker_findings | PROPOSED |
