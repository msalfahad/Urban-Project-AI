# T-567 B5 external plaster / facade finish vs the freelancer, by elevation and face class (research, unwired)

Worker 2 (lane A), claim 2026-11-06 14:41 UTC, run session_01E6cPncudNM6EH1zr3ptjFE. Files: `t567_rules.py`
(R-T567-1 .. 5, any villa), `t567_inputs.py` (row map, every term's arithmetic written out), `t567_alsenan.py` ->
`out/T567_EXT_RECONCILE.json`, `ELEVATION_MATRIX_T567.csv`, `COMPONENTS_T567.csv`, `FACES_T567.csv` (`--check`
rebuilds byte-identical), tests `tests/t567_ext_plaster_reconcile/` (24). No engine module, method, rule / knowledge
version, registry or candidate file changed; no quantity moves; nothing released. ERS applied: s.2.1 (each face its
element and class first), s.2.2 (owner Q-07 B bands beside the drawn faces on every plinth term), s.2.4 (exact closure,
residual 0, every term named), s.2.7 (no owner question: every open item is a designer / specification item already
held, or the freelancer's own unprinted figure), s.3 (one face, one elevation, one class; m.l never m2), s.4, s.7.

## 1. Candidate of record and the physical element

ARCH_TAKEOFF_V3.0.58 = the V3.0.57 facade lines (arch_v3058 (e)); line index `LINE_INDEX_V3_0_57.json`:
FIN.EXT.FINISH GF / 1F / 2F (L-b05f70c9..., L-8bb83e16..., L-d52c4f76...) **HELD, blank** (never 0); ARCH.FACADE 4 HELD
blank; EXT.FENCE.PLASTER 8 HELD blank; ARCH.WINDOW_REVEAL 54 valued 12.438866 m2 + 8 blank (own family); FIN.CEILING
L-23072352... 12.834 (pool-court soffit). **Engine figure for external render: none (HELD); the T-314 wiring is QUEUED.**

The physical element: the outer render / Sigma face of the built envelope, band by band (plinth, storey, parapet outer,
slab edge) plus the parapet inner face and top, each face once on the elevation it faces; openings deducted in full
(Q-73); reveals (ARCH.WINDOW_REVEAL), soffits (FIN.CEILING) and any cladding (B4-11) are their own families and stay
out of the render total. Cladding: T-360 found no material printed on any face (0 m2, C-1 arch surround HELD 1.5149):
no cladding m2 sits inside render m2 (R-T567-1, test).

## 2. His workbook, read from its formulas (own read this run)

Drive 'Alsenan chalet project', the internal plaster + Sigma .xls, decoded into the private folder and converted there
with LibreOffice so the formulas survive (no workbook text committed). Every I cell of rows 51-90 is PRODUCT(E:H) of
typed count / height / width / length: **no hidden sub-row**. Elevation subtotals J55 SUM(I51:I55) SW, J61 SUM(I58:I61)
SE, J65 SUM(I63:I65) NE, J75 SUM(I68:I75) NW, J79 SUM(I77:I79) roof faces + parapets, J84 SUM(I83:I84) parapets, J90
boundary, J92 = H92 x F92 drip; **J93 = SUM(J53:J92) holds each row once** (no row summed twice at subtotal level).
J97 = I96 (= J41, his external opening list, the same list his internal plaster deducts) + I97 (11 x 0.70 x 0.50
bathroom windows) = 65.745; invoice row 25 net = J93 - J97 / 2 = **1,469.9675**. Columns A ('ends') and B ('corners')
are m.l, summed A93 + B93 = 1,297.35 m.l and paid at half (invoice row 26): **no reveal or arris is in his m2**.
Formula check in the builder: each group equals his subtotal cell exactly; J93 = their sum.

## 3. The exact bridge (R-T567-3; both passes residual 0.000000)

Our faces: T-337's 109 keys with T-348 r2 applied (NW-2 parapet re-measured 4.223 .. 4.585 HELD -> 3.977236 DC; 11 new
faces: screen front / back 4.715710 each, pier returns and corner arc 2.616773, moulding steps 0 .. 1.776291 HELD,
void ring 0.892720 .. 3.347700, court-front edge 0.961540, NW-2 edge 0.535 .. 2.006; NW-1 / NW-3 slab edges removed,
NOT_A_FACE); parapet inner + top from T-324 (120.959425 .. 126.530065, matches T-337 ITEMS); his rows 65 / 69 by the
T-346 bands, 70 / 71 / 74 by T-348 r2. 6 slab-edge faces stay **BLANK by name** (depth not printed, Q-68 C).

| m2 | lo pass | hi pass |
|---|---|---|
| our gross (render faces + parapet inner / top) | **1,164.144740** | **1,182.457106** |
| his gross J93 | 1,502.840000 | 1,502.840000 |
| his - ours | +338.695260 | +320.382894 |
| RULE_DIFFERENCE: domes (owner item 3) +181.806; pool soffit = FIN.CEILING line +12.834; plinth below his +1.00 planes (owner Q-07 B) -31.5245 (rows 52 / 64 / 69) | +163.1155 | +163.1155 |
| HELD: his frames 28.8675 + boundary wall 107.24 (EXT.FENCE.PLASTER, Q-65 C) + drip 50.876 (UNKNOWN) = 186.9835; our HELD faces in no row of his -8.249946 / -20.991672 | +178.733554 | +165.991828 |
| UNRESOLVED (his unprinted figures): row 77 2.85 m of 2F run 13.395; row 78 girth 1.70 printed nowhere 21.091 / 15.944; rows 83 + 84 7.5 m of run no plan draws 5.540 / 5.256 | +40.025635 | +34.594995 |
| ENGINE_RIGHT: his widths / lengths / heights / one-plane practice vs the drawn faces (terms +49.22 / +49.08), his no-face parts (row 65 double count 9.000, row 74 no exterior face 52.770, soffit surplus 6.320), drawn faces in no row of his -160.491 | -43.180312 | -43.320312 |
| ROUNDING (4-dp / 6-dp face areas, named) | +0.000883 | +0.000883 |

Net: his 1,469.9675 (half of 65.745) against ours **1,032.870939 .. 1,084.668305** (full holes 97.788801 + W02 0 ..
28.485 + D-GF-07 0 .. 5.000 HELD): **his - ours +385.30 .. +437.10 m2 (ours -29.7 % .. -26.2 %)**. Like for like
(his rows of other families or HELD scope removed: domes, soffit row, frames, boundary, drip = 387.9435): his comparable
gross 1,114.8965 vs ours 1,164.14 .. 1,182.46 (**+4.4 % .. +6.1 %**); comparable net 1,082.024 vs ours 1,032.87 ..
1,084.67 (**-4.5 % .. +0.2 %**). The brief's 447.44 (= his net - T-305's 1,022.534 outer gross) mixed a net with a
gross and left out the parapet inner / top (120.96 .. 126.53) and T-348's faces: it is not a reconciliation figure.

## 4. By elevation (ELEVATION_MATRIX_T567.csv; R-T567-4; lo pass, hi in brackets)

| Our elevation | in his SW | SE | NE | NW | ROOF | PARAPETS | no row of his | **our gross** | our holes (full) |
|---|---|---|---|---|---|---|---|---|---|
| SW | 251.465 | - | - | - | - | - | 47.229 (52.603) | **298.694 (304.068)** | 19.250 |
| SE | - | 150.482 | - | - | - | - | 22.203 | **172.685** | 19.535 + 0 .. 5.000 |
| NE | - | - | 274.045 | - | 38.070 | - | 11.017 (11.633) | **323.132 (323.748)** | 5.485 |
| NW | 2.325 | - | - | 119.142 | 31.960 | - | 44.958 (51.709) | **198.385 (205.137)** | 47.569 + 0 .. 28.485 |
| passage | - | - | 6.955 | - | - | - | 43.335 | **50.290** | 5.950 |
| roof: parapet inner + top | - | - | - | - | 82.119 (87.406) | 38.840 (39.124) | 0 | **120.959 (126.530)** | - |
| + his terms | +21.370 | +16.131 | -32.000 | +13.128 | +33.555 (28.268) | +5.540 (5.256) | | | |
| + his rows with no drawn face | 0 | +24.930 | +9.000 | +257.667 | 0 | 0 | BOUNDARY 107.24, DRIP 50.876 | | |
| **= his group (his subtotal cell)** | **275.160** | **191.5425** | **258.000** | **389.9375** | **185.704** | **44.380** | | | |

Read across the matrix: his groups are his elevation sheets, not the faces' orientation: his ROOF row 77 carries the 2F
NE and NW faces (38.07 + 31.96), his SW row 54 carries the annex NW jog (2.325); his annex run is allocated 4.00 / 13.00
/ 1.50 m over rows 54 / 55 / 60 against the drawn 5.642 / 6.40 / 6.70 m (+31.68 in SW, -24.96 in SE, -7.88 in SW; net
-1.16 m2 on the 18.50 vs 18.742 m run). Faces he has in no row: the porch / pool-court / passage faces (GF SW-5, SE-2,
SE-3, NE-1 .. 3, NW-2 .. 6, SW-6, SW-8, SW-9 covered, P-1, P-2 3.40 m), 1F SW-2 over the porch (18.48), the 1F NW-4 /
NE-1 / SW-1 returns and the NW-1 corner arc (0.936): 160.491 m2 drawn + 8.25 .. 20.99 HELD.

## 5. Verdict proposals (Checker)

- Candidate: **ENGINE_OMISSION** (3 FIN.EXT.FINISH lines HELD blank; T-314 to wire), not ENGINE_WRONG; no drawn face of
  the merged ledgers was found wrong in this run (each face once, residual 0).
- Plinths -31.52: RULE_DIFFERENCE (his planes from +1.00 = owner Q-07 B; the plinth is its own HELD line, RFI).
- Openings: RULE_DIFFERENCE on the rule (Q-73 full holes 97.79 + 0 .. 33.485 HELD vs his half 32.87). His list holds
  36 openings (25 in rows 29-41 + 11 bathroom windows), the same count as the 36-opening census, but 65.745 m2 against
  our 97.79 fixed holes: his sizes are window measures, not holes (W03 / W17 / arches, T-305); by mark: T-568.
- Domes, soffit row: RULE_DIFFERENCE (owner items 3 / 4). Frames, boundary, drip: HELD (other family / not drawn /
  unanswered), bounded by his figure only for display, never our quantity.
- Rows 77 / 78 / 83 + 84: UNRESOLVED (his runs / girth printed nowhere; drawing-first: the drawn values stand).
- Everything else ENGINE_RIGHT on the drawn faces (two traces: T-159 / T-305 rings and T-346 / T-348 plan cuts).

## 6. Rule, tests, lesson, what is missing

R-T567-1 .. 5 (module docstring). Tests: villa B567 box 10 x 8 x 3.5, parapet 1.00, t 0.20, window 1.50 x 1.20: walls
126.00 - 1.80 = 124.20; parapet outer 36.00, **inner 34.40 (inner run 36.00 - 8 t), top 7.04**: our gross 203.44, net
201.64; his one-plane statement 234.00 / 233.10 bridges +30.56 = outer parapet counted again +36.00 + inner on the
outer run +1.60 - tops -7.04 (the brief's 'parapet 36.00 x 2' holds only for t = 0); mirror / rotation (6 orders) and
millimetre input invariant; plinth / datum terms close. Adverse: a face on two elevations, booked twice, matched beyond
its whole by two rows; cladding m2 inside render; inner face on the outer run; HELD 0 .. 0, DC range, UNKNOWN with a
number, blank face without HELD; blank HELD matched by m2; m.l as a face; floats; a term without a source or with an
unknown cause; tolerance > 0; a row that does not close; rows not adding to his gross; a re-measure changing elevation;
a removal without a reason. Development villa: --check rebuild, his groups on his subtotal cells, both passes residual 0,
pinned totals, candidate lines blank, faces once (118), T-348 applied, no Arabic text in outputs.

Lesson proposal (ERS s.7): "2026-11-06 | external plaster vs the freelancer was compared as one total (his net 1,469.97
vs our outer gross 1,022.53, '447.44') | a net was set against a gross and his elevation groups were taken as the faces'
orientation, so cross-elevation rows (2F faces in his 'roof' row, annex run split over SW / SE rows) and parapet inner /
top looked like scope gaps | bridge gross to gross per face key on its own elevation, show his groups as a matrix, take
each side's opening rule as its own step, and exclude other line families (ceiling, fence, cladding, reveals) by name
(every villa) | tests/t567_ext_plaster_reconcile | proposed."

Missing / HELD (never 0): W02 / D-GF-07 holes (designer); slab-edge depths (6 blank faces); pool-court plinth bottom;
1F parapet heights NE-1 / SW-1 / SW-2; moulding step faces; void ring depth; C5 face owner; frames; drip; exterior finish
specification (the area does not depend on it); T-348 finding: the element SW of the W18 strip +0.594 m possibly in no
face key (not measured here; candidate 0.594 x 4.20 .. 5.50 = 2.49 .. 3.26 m2, named, not added).
