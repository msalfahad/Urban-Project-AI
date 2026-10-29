# T-339: roof build-up layers bound to the V3.0.22 candidate (integration dependency of T-328; every villa)

Worker 1 (lane S), 2026-10-29, run session_01E6cPndWyP5sfpJkj5NKcTA. Research only: research/agents_t339/* and
tests/t339_roof_binding/*; no engine module, method, rule / knowledge version, registry, frozen file, candidate or
released line changed. Development villa, not an accuracy claim. Drawings cited by Drive title and entity handle; local
metres in T-321's frames (origin = each roof's inner south-west corner), no absolute coordinate, no client data.
ERS applied: s.2.1 (the roof split into slab / parapet / layer stack, one owner per layer), s.2.2 (owner rules beside
the drawing: Q-41 / Q-45 / Q-24 / Q-34 / D-39), s.2.3 - 2.4 (slab zone re-measured by handle, reconciled in m2, every
residual named), s.2.7 (no owner question: every open item is a designer specification already held: D-39 t0,
insulation / protection UNKNOWN, finish material, Q-34 top roof), s.3 (area basis vs volume quantity; physical vs
payable), s.4 (rules + tests), s.7 (lesson row, section 8).

## 1. Inputs and run identity

- Merged ledgers, not re-derived: T-321 (59c82a05) zone x layer ledger and outlines; T-324 (bc5df868) parapet
  components (top surfaces = the parapet's plan footprint, centreline x drawn 0.200); T-342 (4dd9cff8) the V3.0.22 roof
  WP lines bound by source entity (AT216 / AT220 / AT379; AT385 = DUPLICATE_OF AT379) and the candidate extract
  `7199c8b6`.
- Re-measured this run: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 `ab54dd55`):
  each roof's slab zone to the parapet's OUTER 0.20 wall line by handle (`t339_measure.py` -> MEASURED_T339.json):
  annex AC7 / C6F / B36 / B39 / arc B29 r 1.300 / B26, divider face CEC; terrace AC7 / C7F / BDC, walls B5D / AE3,
  divider face CED; 1F roof 127F (+ 131E) / 12A5 / 131C / 131B (layer 2) / 1273 / 12C7 / 12A8, walls 1291 / 1281 /
  1288. The finish hatches (D1F / B2A, AE0 / D1A / 1252, 2F21) and the dome circles 12EB / 2F33 re-read for the
  overlap checks. Frame / moulding lines beyond the 0.20 wall line (B2D / B2E, B27 / B28, 1308 .. 1323, C85 / C86) are
  the facade frame item (T-305 / T-324), not slab, not parapet: not used.
- Candidate: own run research/agents_t167/v304_run.py then research/agents_t331/v3022_run.py (Python 3.11.18) for the
  STR.CONC.SLAB lines (SLAB_LINES_T339.json, section 5).

## 2. The binding (acceptance a): BINDING_T339.csv, 24 rows = 4 roofs x 6 layers, each once

Owner trade per layer from the Lead's cross-trade register (ELEMENT_REGISTER 2026-10-29): falls = SCREED, ONE volume
(Q-41; Q-45 its mix only); membrane + upturn = WATERPROOFING (existing lines); insulation / protection / walking finish
= ROOFING B13-01 (NEW rows). Edges: every layer inside the parapet INNER face (R-T339-1).

| Roof (element; storey of the WP lines / of the slab) | Screed to falls (NEW, m3) | Membrane (existing, m2) | Upturn (existing, lm) | Insulation / protection (NEW) | Walking finish (NEW, m2) |
|---|---|---|---|---|---|
| ROOF-430 annex +4.30 (1F-ROOF-AT220; 1F / GF) | HELD blank; basis 54.920 .. 55.560 m2 | L-d57d2dc2fafac8bc72d8 55.559 (layer 54.920 .. 55.560) | L-d4c73babd2a275c28929 35.727 (35.728) | UNKNOWN, blank | **54.920** DRAWING-CONFIRMED, material blank |
| TERRACE-550 +5.50 (1F-ROOF-AT216; 1F / GF) | HELD blank; basis **31.643 .. 32.721** | L-2f7502be6f501baf49b1 32.721 (layer 31.643 .. 32.721) | L-994b88140f2ea50f1b31 52.940 | UNKNOWN, blank | **31.643** |
| ROOF-970 1F roof +9.70 (2F-ROOF-AT379 + AT385; 2F / 1F) | HELD blank; basis 115.656 .. 115.814 (domes 2 x 15.359 SCOPE_UNKNOWN beside) | L-636fd3ff1784a12e653b 115.832 (layer 115.656 .. 115.814) | L-5ce5ba49792e8f9d1f6f 92.922 (65.140 + rings 27.785) | UNKNOWN, blank | **115.656** (domes excluded) |
| ROOF-1390 main roof +13.90 (2F-ROOF-TOP; 2F / 2F) | HELD (Q-34) | L-3e8fe55da71851816dd4 BLOCKED_RFI | L-aac1f35e08f85b643692 BLOCKED_RFI | HELD | HELD; drawing-derived 49.665 m2 beside, not released |

Status count: DRAWING-CONFIRMED 3 (the finish areas), ASSUMED - OWNER-APPROVED 6 (membrane / upturn on the three
measured roofs), UNKNOWN 6 (insulation / protection there), HELD 9 (3 screed volumes + the 6 top-roof rows), VERIFIED 0. No HELD or UNKNOWN row
carries a number; nothing is 0. NEW rows: 16 (4 screed, 4 insulation, 4 protection, 4 finish); existing lines: 8,
unchanged. The oval-void area +5.50 (6.130 m2, T-303) stays UNKNOWN as a roof (no ROOF label; T-062 held): no row.

Line against layer (summary.json line_vs_layer; the lines are NOT moved by this task):

| Line | Line | Layer (hi) | Difference | Cause |
|---|---|---|---|---|
| AT220 membrane | 55.559 | 55.560332 | -0.001332 m2 | engine face with the arc B2B as a polyline (arc flattening); **T-321 wrote 0.000 by comparing the hand 55.560, not the line** (F-T339-2) |
| AT216 membrane | 32.721 | 32.721 | 0.000 | the wall-face reading; 31.643 is the D-band low end (F-T339-1) |
| AT379 membrane | 115.832 | 115.814 | +0.018 m2 | domes deducted as polygons 2 x 15.350, not circles 2 x 15.359 (T-321) |
| AT220 upturn | 35.727 | 35.728 | -0.001 lm | arc length rounding (T-321) |
| AT379 upturn | 92.922 | 92.925 | -0.003 lm | dome rings as polygons (T-321) |

## 3. Closure (acceptance b): slab roof zone - parapet footprint - layer = named causes (CLOSURE_T339.csv)

Slab roof zone = the roof part of the slab to the parapet's drawn 0.20 wall line (measured above); parapet footprint =
T-324 top surfaces (centreline x 0.200). Every closure closes to <= 0.00005 m2 (tolerance 0.0001).

| Roof | Slab zone | Footprint (T-324) | Layer | Residual | Named causes | Unexplained |
|---|---|---|---|---|---|---|
| ROOF-430, face to the wall | 61.597323 | 6.037010 | 55.560332 | -0.000019 | T-324 arc top at 5 dp (0.37699 vs pi (1.3^2 - 1.1^2) / 4 = 0.376991) | -0.000018 (T-324 5-dp run tops) |
| ROOF-430, face to the D band | 61.597323 | 5.997010 | 54.920332 | +0.679981 | D band 0.200 x 3.200 = 0.640 + SW-3 end over the band 0.040 (T-324 C1) | -0.000018 |
| ROOF-430, finish hatch | 61.597323 | 6.037010 | 54.920300 | +0.640013 | D band 0.640; hatch arc flattening -0.00003 | +0.000046 |
| TERRACE-550, face to the wall | 38.355 | 5.673980 | 32.721 | -0.039980 | junction square x -0.20 .. 0 at the boundary line: T-324 GF NE-4 runs from the divider's far face (outer arris 19.370) = -0.040; T-324 rounding +0.00002 | 0.000000 |
| TERRACE-550, D band = finish | 38.355 | 5.592956 | 31.643 | +1.119044 | D band along the 1F wall foot 1.078 (F-T339-1) + SW-9 end at the band C9E 0.405 x 0.200 = 0.081024 (T-324 C6) - junction square 0.040 | +0.000020 |
| ROOF-970, face to the wall | 156.36 | 9.846530 | 115.81396 | +30.69951 | dome footprints 2 x pi 2.211092^2 = 30.71804; T-311 / T-324 runs NE-1 and SW-1 (0.040 x 0.200 return ends each, inner arris 0) -0.016; NW-1 .. NW-5 centreline 11.8127 vs 11.800 -0.00254 | +0.00001 |
| ROOF-970, D band = finish | 156.36 | 9.831510 | 115.65646 | +30.87203 | domes 30.71804 + D band 0.075 x 2.100 = 0.1575 + SW-2 end at the band 0.075 x 0.200 = 0.01502 (T-324 C2) - 0.016 - 0.00254 | +0.00001 |
| ROOF-1390 (HELD, beside) | 55.08 (8.10 x 6.80) | 5.415 | 49.665 (7.70 x 6.45) | 0.000 | - | 0.000 |

Hand checks (own, by parts): terrace zone 19.17 x 1.50 + 1.50 x 6.40 = 38.355; 1F roof zone 19.27 x 5.20 + 6.77 x 6.80
+ 4.40 x 2.30 = 100.204 + 46.036 + 10.120 = 156.360; annex zone 12.00 x 1.50 + 10.60 x 3.40 + 4.40 x 0.50 + 3.10 x
1.30 + pi 1.30^2 / 4 = 18.000 + 36.040 + 2.200 + 4.030 + 1.327323 = 61.597323. The divider CEC / CED (0.200 x 1.300 = 0.260 m2) lies in neither roof zone
and in no T-324 top (its faces / top UNKNOWN): named for the parapet rows, never a layer.

## 4. Cross-check: no area shared with the parapet rows (acceptance c; CROSSCHECK_T339.csv)

| Parapet row | Layer | Shared | How shown |
|---|---|---|---|
| parapet footprint: T-324 tops 26.836 .. 26.973 m2 = T-319 STR.CONC.PARAPET plan (L-1d419b64 / L-b5ffc172 / L-9a2c8116 / L-030538dd, V3.0.23 READY) | every plan layer | **0.000 m2** | layer <= inner-face area (R-T339-1 check on every row) and zone = footprint + face (section 3) |
| the same footprint polygon (outer wall line - inner face) | FINISH, the designer's hatch (an independent entity) | **0.000002 / 0.000000 / 0.000000 m2** | t339_measure.py: hatch in the strip; hatch outside the inner face the same (arc flattening only) |
| T-324 INNER_FACE_UPTURN_ZONE (0 .. 5.966 / 5.554 / 9.668 / 5.660 m2, WP edge detail, NO LINE) | UPTURN (membrane, lm line) | 0.000 m2 | one face, two items: the membrane upturn (lm) vs the finish / protection over it (m2, T-324) |
| T-324 inner face above the upturn, top surface | screed / insulation / protection / finish | 0.000 m2 | no upturn height printed for any layer but the membrane: no vertical layer row exists |
| T-337 NEW FIN.EXT.FINISH PARAPET-OUTER per roof; MAS.BLOCK parapet alternative (T-311 / T-333) | every layer | 0.000 m2 | outside the inner face; no layer is vertical there |
| divider CEC / CED 0.260 m2 | every plan layer | 0.000 m2 | both roofs stop on its faces; its upturn 1.300 m is in each roof's upturn line (two faces) |

## 5. The slab under the roofs (CONC slab lines)

The roof slab's concrete is STR.CONC.SLAB, under every layer and untouched by the build-up rows. SLAB_LINES_T339.json
lists the slab lines by storey from the run in section 1 (GF roof slab under ROOF-430 and TERRACE-550, 1F roof slab
under ROOF-970, 2F roof slab under ROOF-1390): **GF 40 lines 33.069524 m3 (7 blank), 1F 26 lines 19.756334 m3 (4
blank), 2F 9 lines 7.454300 m3 (2 blank)**, V3_0_22_BOQ_LINES.json `7199c8b6` (3,706 lines; V3.0.21 `be22a4e4`
reproduced on the way). These are the whole storey's roof-slab lines (the GF roof slab also carries the 1F rooms), not
the roof zones only; they equal the T-139 hand panels (33.069 / 19.757 / 7.454 m3). The per-panel
attribution of those lines to one roof is NOT made here (panel ids are SITE ids of the structural sheet; T-139 panels
are net of beams): named as open, no quantity depends on it.

## 6. FILL table T-328 consumes unchanged (acceptance e): FILL_T328_T339.csv, 24 rows

One row per binding: ADD (finish, 3 with a number), ADD (blank, held) (screed 4, insulation 4, protection 4, top-roof
finish 1), UNCHANGED (cross-reference) (the 8 WP lines). Each row: target (line id or NEW row name), roof element,
storey, layer, owner trade, unit, quantity (blank when HELD / UNKNOWN), basis area, status, bounds beside, held
reason, exclusive-with (the parapet rows and the slab). T-328 acceptance mapped: (a) T-321 corrected edges bound by
line id: yes, ROOF-430 to the divider CEC (+2.079 m2 strip), ROOF-970 to the inner face 1278; (b) no layer exceeds its
roof outline and no layer runs up a parapet: R-T339-1 / -5; (c) ranges only from named causes (D band, D-39), held
blank; (d) one screed volume per roof; (e) the 8 WP lines unchanged.

## 7. Findings (never forced to fit)

1. **F-T339-1: the terrace D band.** T-321 read the D band as a range on ROOF-430 (0.640 m2) and ROOF-970 (0.1575) but
   carried TERRACE-550's face layers as one value 32.721. The terrace finish hatch leaves exactly one gap, 1.078 m2,
   in the band along the 1F wall foot (layer D C8A .. CA3, B5E, C9D; x 16.67 .. 18.075 local): the same physical
   question (what the band is is not printed), so the face layers are 31.643 .. 32.721 m2 with the cause named. The
   membrane line 32.721 (the wall-face end) is unchanged; nothing is chosen.
2. **F-T339-2: AT220 line value.** The V3.0.22 membrane line is 55.559, not 55.560: T-321's "0.000" closure compared
   the T-062 hand value. Residual -0.001332 m2, arc flattening of the engine face (segment count not traced).
3. **Owner trade of the walking finish.** T-321 put FINISH under FLOOR FINISH; the Lead's register (ELEMENT_REGISTER
   2026-10-29, roof build-up row) gives ROOFING B13-01. The binding follows the register (it governs cross-trade
   ownership); T-328 should confirm the family name when it adds the rows.
4. The falls screed above-t0 volume of T-321 (14.208 .. 17.470 m3) is on T-321's outline, which for ROOF-970 includes
   the dome footprints; it is NOT a lower bound of the screed row (domes SCOPE_UNKNOWN): kept beside as text only.

Engine vs freelancer: roof membrane, candidate 55.559 + 32.721 + 115.832 = 204.112 m2 vs his single roof line 285.00
m2 (T-071 figure; his cells not read: workbook over the connector limit), -80.888 m2 (-28.4 %): T-321's scope
decomposition stands (top roof 49.665 HELD Q-34 + dome footprints 30.718 SCOPE_UNKNOWN = 284.478, residual +0.522 m2):
RULE_DIFFERENCE + HELD scope, unchanged by this task. Screed, insulation, protection, roof finish: NOT COMPARED (his
rows not read). Verdict proposals: F-T339-1 ENGINE_RIGHT on the range (the band is drawn, its meaning unprinted);
F-T339-2 named residual, no line change.

## 8. Rules, tests, lesson

- `t339_binding.py`: R-T339-1 (layer edge inside the parapet inner face; an area that reaches the outer face refused),
  R-T339-2 (each roof x layer once, to a line of its own family or a NEW row; UNKNOWN blank; HELD never 0), R-T339-3
  (one screed volume per roof; an m2 screed quantity refused; no default thickness), R-T339-4 (closure with named
  causes, unexplained reported), R-T339-5 (no plan overlap with the parapet footprint; no vertical layer row without a
  printed height; no row naming a parapet component).
- `tests/t339_roof_binding/test_t339_rules.py`, NON-Alsenan hand villa: roof A +3.50 8.00 x 5.00 with a parapet on
  three sides (zone 8.20 x 5.40 = 44.28 = 40.00 + 21.40 x 0.20) and a 0.10 band (finish 39.50), roof B +7.00 4.00 x
  3.00 parapet all round (14.96 = 12.00 + 14.80 x 0.20); mirror / rotation 0, 30, -121, 47 deg. Adverse: a layer to the
  parapet outer face (and mm as m2) refused; the falls screed as an area or twice refused; a held thickness as 0 or a
  default thickness refused; HELD / UNKNOWN as 0 or with a number refused; the membrane as a B13-01 row, on a
  FIN.EXT line, or one line under two roofs refused; a row naming a parapet component, an unprinted upstand refused; an
  unexplained residual reported (closes = False).
- `tests/t339_roof_binding/test_t339_alsenan.py`: byte rebuild of the four tables and the summary; 24 rows once; held
  blank; the 8 lines = the V3.0.22 extract; closures close; shared 0; the terrace range; the measurement re-read from
  the private drawing when present (skip otherwise).
- ERS s.7 row (proposal): 2026-10-29 | the roof layers had no binding: one face reading per roof was carried as the
  membrane line, the D band read as a range on two roofs but not on the third, and a closure compared a hand value
  instead of the line | the layer edge was taken from one outline per roof and the closure was not tied to the slab
  zone and the parapet footprint | bind every roof x layer once (existing line of its own family or a NEW row), edges
  inside the parapet inner face, close slab zone - parapet footprint - layer to named causes, and apply an edge reading
  (D band) to every roof where the same band is drawn (every villa) | tests/t339_roof_binding | proposed.

## 9. For the Checker (re-measure from the drawing, not from this file)

1. P7757.dxf annex roof: AC7 0.200 outside B34; C6F x start (-0.200); B36 / B39 / arc B29 r 1.300; B26 y 6.500 -> zone
   61.597 m2; terrace: C7F x end 19.170, BDC y 7.700 -> 38.355; 1F roof: 127F, 12A5 / 131C / 131B, 1273, 12C7, 12A8
   (y 7.300) -> 156.360.
2. The terrace finish-gap piece 1.078 m2 lies in the D band along the 1F wall foot (C8A .. CA3, B5E, C9D) and nowhere
   else (F-T339-1).
3. V3.0.22 line AT220 membrane 55.559 (F-T339-2); the 8 line ids in BINDING_T339.csv.

## 10. Not done / uncertain

- Per-panel attribution of the STR.CONC.SLAB lines to each roof (section 5).
- The D band's physical meaning (three roofs), t0 (D-39), insulation / protection scope, finish material, the top roof
  (Q-34) and the oval-void area: all HELD / UNKNOWN by name, never 0.
- The freelancer's build-up rows were not read (workbook over the connector limit).
