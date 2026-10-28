# T-321 Roofing build-up (B13-01): zone x layer area ledger, every roof / terrace once

Worker 3, 2026-10-28, run unknown (lane A row taken by lane I: lane I had no TODO). Development villa, not an accuracy
claim. ERS read; s.2 steps 1-4 and 7, s.3 (physical vs contract, notation before arithmetic, an interpretation not
extended to another element), s.4, s.7 applied. Research only: research/agents_t321/* and tests/t321_roof_buildup/*;
no engine module, method, rule / knowledge version, registry, candidate or released quantity changed. Drawings cited by
Drive title and entity handle; outlines in local metres (origin = each roof's inner south-west corner).

## 1. Result in engineering terms

**No roof layer is printed anywhere in the issued set.** Every text of the architectural DXF (109, the Arabic notes
decoded: room names and title block only), every text of the structural DXF (374: excavation, soil, formwork notes and
'CHECK ARCHITECTURAL DETAIL OF PARAPET, BEFORE CASTING'), the three sanitary drainage sheets (RWPs and 'SLOPE 1%' only)
and the SECTION A-A roof bands (one constant 0.05 / 0.20 drafting band, refused as a build-up by T-214 / T-221) were
searched: no insulation, protection, screed, membrane or tile callout and no thickness. The one 'INSULATION' print is the
pool detail (ST p.7 TEXT 1876 '5cm INSULATION MEMBRANE.'), a pool base / wall layer, not extended to a roof (ERS s.3).
What the drawings DO fix is each layer's AREA, by its own edge:

| Zone (candidate element) | Membrane / screed plan, to wall & parapet faces | Finish plan, to the designer's hatch | Footprints (own status per layer) | Vertical faces round it (upturn) |
|---|---|---|---|---|
| ROOF-430 annex +4.30 (AT220) | **54.920 .. 55.560 m2** (D-band reading .. wall face) | **54.920 m2** (hatch D1F + B2A) | - | 35.728 m: parapet 29.628, divider 1.300, walls 4.600, closure 0.200 |
| TERRACE-550 +5.50 strips (AT216) | **32.721 m2** (= Checker 21:05) | **31.643 m2** (hatch AE0 + D1A + 1252) | - | 52.940 m: parapet 26.470, divider 1.300, gate stub 0.894, door closure 0.406, walls 23.870 |
| ROOF-970 1F roof +9.70 (AT379) | **115.656 .. 115.814 m2** net of the domes | **115.656 m2** (hatch 114.985 + drafting gaps 0.672) | 2 domes 2 x 15.359 m2: finish EXCLUDED, membrane / screed / insulation / protection SCOPE_UNKNOWN (T-303) | 65.140 m + dome rings 2 x 13.893 m |
| ROOF-1390 main roof +13.90 (TOP) | HELD (owner Q-34); drawing-derived 49.665 m2 inside the parapet faces (7.70 x 6.45) | HELD (no roof plan) | third dome 15.275 m2 (Q-29: held) | 28.300 m (= T-311) |
| area round the oval void +5.50 | UNKNOWN (T-303: 6.130 m2, no ROOF label) | - | - | - |

Per layer (WORKFLOW_CONTROLS s.5), the same on every roof (ROOF-1390 HELD on all five):

| Layer | Owner trade | Scope evidence | Area | Thickness / volume | Candidate line |
|---|---|---|---|---|---|
| FALLS_SCREED (screed to falls) | ROOFING B13-01 | ASSUMED - OWNER-APPROVED: Q-41 'if it is roof or balconies it is screed', own line; fall printed 1 % (T-221) | face plan above (DRAWING-CONFIRMED) | t0 unprinted (D-39): volume HELD; the part above the t0 plane 14.208 .. 17.470 m3 (table s.4) | NO LINE |
| MEMBRANE | WATERPROOFING B8-06 | UP-WP-ROOF-001 / Q-24, 0.20 m upturn | face plan above | - | AT220 / AT216 / AT379 IN_LINE, TOP BLOCKED_RFI (cross-reference; never a B13-01 line) |
| INSULATION | ROOFING B13-01 | UNKNOWN: printed nowhere, no owner rule | (face plan, if it exists) | HELD | NO LINE |
| PROTECTION | ROOFING B13-01 | UNKNOWN: Q-41 gives ONE screed line ('falls / protection'); a separate layer is neither printed nor ruled | (face plan, if it exists) | HELD | NO LINE |
| FINISH | FLOOR FINISH | extent PRINTED (layer-3 hatch); material HELD (no tile / paving type, no owner rule for roofs; Q-42 gives roof tile joints 2 mm) | finish plan above (DRAWING-CONFIRMED) | - | NO LINE (see s.6) |

Which layers turn up the parapet: only the membrane has a rule (0.20 m, Q-24); a finish skirting, an insulation or a
protection upstand is printed nowhere: the upturn LENGTH is measured (column above), every other layer's height HELD.

## 2. The physical elements and each edge's meaning (ERS s.2 step 1, s.3)

- **Wall / parapet face** (layer 1 walls, layer 5 parapets): where a membrane turns up and a screed stops.
- **D band** (layer D, a 0.20 x 4.018 m rectangle along the 1F wall foot on ROOF-430, handles B3C / C40 / C47; a 0.075 m
  band with profile arcs along the 2F west wall on ROOF-970, 12E2 / 12E6): every parapet stops on it (B35, 12B9) and the
  designer's finish hatch runs to it. What it is physically (cladding / moulding / a thicker wall below) is not printed:
  the face layers stay a range (ROOF-430 0.640 m2, ROOF-970 0.1575 m2), named D-BAND, never chosen.
- **Finish hatch** (layer 3, pattern LINE): the designer's finish extent. Its annotation is not construction: islands
  round labels / level symbols / RWP symbols are not deducted; three symbol frames drawn as EXTERNAL paths on TERRACE-550
  (0.113 / 0.236 / 0.137 m2) are excluded; on ROOF-970 the hatch boundary follows the 2F roof door's swing (0.89 quarter
  circle, 0.622 m2) and leaves two cusps where the domes touch the parapets (2 x 0.022 m2): finish exists there.
- **Dome discs** (12EB / 2F33, r 2.211092, tangent to the west and east parapet faces): the finish hatch stops at them;
  no roof walking surface lies inside a dome under S0 or S1, so the finish excludes them; for the other layers T-303's
  SCOPE_UNKNOWN stands (Q-24 / Q-29 C / T-185).
- **ROOF-1390**: no roof plan (D-62); the parapet continues the 2F walls in their plan thickness (section A-A, T-172 /
  T-311 Gate A): inner faces 12B7 / 1292 / 1279 / 1283 give 7.70 x 6.45 = 49.665 m2; outer 8.10 x 6.80 = 55.08 m2. Third
  dome (1300, layer 2 'above', r 2.205018, tangent to the east inner face) 15.275 m2; a 2.18 m box seen beyond in A-A
  (top +14.40) is unidentified; 'WATER TANK PLACE' has no tank drawn. HELD under Q-34 (no number released, never 0).

## 3. Reconciliation (ERS s.2 step 4): every residual named (CLOSURE_T321.csv)

| Closure | Own | Reference | Residual | Named causes |
|---|---|---|---|---|
| ROOF-430 vs T-221 | 55.560 | 52.854 (T-221 reported 52.848: its arc sampling) | +2.706 | +2.079 strip between the house SW corner line and divider CEC (1.599 x 1.300) missing from T-221's outline; +0.637 3.2 m band to the wall face B3A (T-221 stopped on the D band); -0.009 T-221 corner rounding |
| ROOF-970 vs T-221 | 146.532 | 147.691 | -1.159 | -1.321 T-221 took the east wing's north edge on the parapet OUTER face 1273 (6.801 instead of 6.600); +0.162 west wing to the wall face 1288 (4.200 x 2.100) vs T-221 4.125 x 2.099 |
| AT220 membrane line | 55.560 | 55.560 | 0.000 | same basis (T-062) |
| AT216 membrane line | 32.721 | 32.721 | 0.000 | = Checker 21:05 screed / membrane |
| AT379 membrane line | 115.814 | 115.832 | -0.018 | candidate deducts the domes as polygons (2 x 15.350), not circles |
| TERRACE-550 finish vs Checker 21:05 | 31.643 | 31.681 | -0.038 | -0.035 a symbol frame of hatch D1A drawn as an external path across the wall face; **-0.003 UNEXPLAINED** (the Checker's computation is not on the board) |
| ROOF-970 finish hatch vs own finish | 114.985 | 115.656 | -0.672 | door swing -0.622, dome cusps -0.045, arc flattening -0.004 (tolerance 0.001) |
| ROOF-430 parapet faces vs T-311 ANNEX | 29.628 | 28.428 | +1.200 | **+1.400 boundary parapet B34 between the house SW wall line and the divider: in NO T-311 run (F-T321-02)**; -0.200 T-311 SW-3 runs across the D band to the wall face |
| TERRACE-550 parapet + divider vs T-311 GF | 27.770 | 27.970 | -0.200 | T-311 NE-4 runs the boundary parapet body across the 0.20 divider |
| ROOF-970 parapets vs T-311 1F | 48.265 | 48.784 | -0.519 | -0.444 sea side: T-311 NW-1 .. NW-5 follow the shaped parapet top (12.044), the roof-level face 12A7 is straight (11.600); -0.075 SW-2 across the D band |
| ROOF-1390 parapets vs T-311 2F | 28.300 | 28.300 | 0.000 | - |
| candidate roof upturns | 153.808 | 153.807 | +0.001 | arc rounding |

**Freelancer (one roof line 285.00 m2; his cells NOT read: workbook over the connector limit; figure from T-071 /
T-303).** Candidate 204.112 m2, -28.4 % (UNRESOLVED since T-071). A scope decomposition that reaches his figure:
three roofs as measured 204.095 + the two +9.70 dome footprints 30.718 (membrane under the domes) + the +13.90 roof inside
its parapet faces 49.665 (third dome not deducted) = 284.478 m2, **residual +0.522 m2 (+0.18 %)**. Consistent with his
figure, NOT a proof of his method; it says the -28.4 % gap is SCOPE (top roof held by Q-34, dome footprints held by
Q-24 / Q-29), not measurement: proposal RULE_DIFFERENCE + HELD scope, Checker to confirm against his cells.

## 4. Falls (T-221's model, unchanged, on the corrected outlines)

| Zone | Outline m2 | Rise max EIKONAL .. AXIS | Above the t0 plane m3 | T-221 (its outline) |
|---|---|---|---|---|
| ROOF-430 | 55.560 | 0.119 .. 0.149 m | 3.401 .. 4.208 | 0.112 .. 0.147 m, 3.103 .. 3.882 |
| TERRACE-550 | 32.721 | 0.190 .. 0.203 m | 2.718 .. 2.910 | same rise, 2.712 .. 2.900 |
| ROOF-970 (incl. dome footprints) | 146.532 | 0.107 .. 0.144 m | 8.089 .. 10.352 | same rise, 8.168 .. 10.455 |
| total | | | **14.208 .. 17.470** | 14.0 .. 17.2 |

ROOF-430's far point moves into the 1.6 x 1.3 strip: the parapet allowance T-221 computed for it shrinks by up to
0.007 m (still NOT PROVEN, t0 unprinted). Screed volume = area x t0 + the above: HELD on t0 (D-39), never 0.

## 5. Cross-trade and double-count checks

- **Falls layer, one physical volume, two owner rules (CONFLICT, for the Lead):** Q-41 books a roof screed as its own
  line; Q-45 puts the roof falls into the cement bed under the tiles ('roof depending on slope'). The ledger carries the
  falls ONCE (FALLS_SCREED, B13-01); which trade books it decides whether a tile-bed line may also carry it. Not an
  owner question here (ERS 2.7: the Lead first checks whether the two answers were meant as one layer).
- Membrane: WATERPROOFING only; the ledger refuses it as a B13-01 row (test). Upturn: its own lm item, never folded into
  the flat m2 (test).
- Parapet: F-T321-02 adds 1.400 m of boundary parapet (annex roof side, x 10.4 .. 11.8) missing from T-311's run ledger:
  its concrete / blockwork / faces / formwork are in no T-311 quantity (0.20 x 0.50 printed height + b_edge). For T-319.
- Domes: finish excluded, other layers SCOPE_UNKNOWN; rings 27.785 m (circles) vs candidate 27.784 (polygons).

## 6. Statuses and lines (no BOQ line moved)

FALLS_SCREED 203.298 .. 204.095 m2 plan (ROOF-430 54.920 .. 55.560, TERRACE-550 32.721, ROOF-970 115.656 .. 115.814)
ASSUMED - OWNER-APPROVED scope (Q-41), area DRAWING-CONFIRMED, volume HELD; INSULATION / PROTECTION UNKNOWN; FINISH
202.220 m2 (54.920 + 31.643 + 115.656) DRAWING-CONFIRMED area, material HELD; ROOF-1390 every layer HELD (Q-34);
oval-void area UNKNOWN. No candidate line carries a roof screed, insulation, protection or roof finish (V3.0.20 run
checked: s.8). Nothing VERIFIED: Checker to re-measure.

## 7. Rule and lessons row (proposed)

Rule (any villa, provenance T-321): a roof build-up is a layer stack, each layer its own item with ONE owner trade; a
layer exists by a print or an owner rule (else UNKNOWN, a row, never 0); each layer's area is measured to its OWN drawn
edge (finish to the finish hatch's physical edges, face layers to the wall / parapet faces; an edge with two physical
readings is a range with its cause named); annotation is not construction (label islands, symbol frames, door swings in a
hatch); thickness only from a print (else HELD); upturns in lm on their own.

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-28 | Roof areas carried as ONE number per roof, while two of them were wrong by an edge (ROOF-430 -2.706 m2: a 1.6 x 1.3 strip missed; ROOF-970 +1.321 m2: north edge on the parapet OUTER face) and the finish and membrane differ by edge (TERRACE-550 31.643 vs 32.721) | An outline traced once and reused for every layer; edges not tied to entity handles; hatch annotation and door swings read as edges | Measure each roof layer to its own drawn edge, every vertex from a named entity (handle), annotation excluded, alternative edges as a named range; close every roof against every earlier reading with each unit named (every villa) | tests/t321_roof_buildup (normal: two-zone villa by layer; adverse: membrane as insulation, default thickness, folded upturn, held as 0, fall as a percent number, mm / mirror / rotation, unnamed closure residual) | proposed |

## 8. For the Checker (re-measure from the drawings, not from this file)

1. P7757.dxf 1F frame, ROOF-430: B34 (11.800 inner face), CEC (divider at x 11.8), ADF (house south wall face at
   y 1.3), B3A (wall face x 10.4) vs B3C (D band x 10.2), B35 / B38 / arc B2B (centre (2.9, 5.2), r 1.1, 0 .. 90 deg),
   B41, B37 -> 55.560 / 54.920; hatches D1F 53.022 + B2A 1.899 = 54.920.
2. 2F frame, ROOF-970: 1285 / 12A7 (11.600) / 1278 (inner, NOT 1273 outer) / 1291 / 1281 / 1288 vs 12E2 / 12B9 / 12C9
   -> 146.532 / 146.375; circles 12EB / 2F33; hatch 2F21 five paths 114.985; the door-swing gap at local (5.25, 4.62).
3. ROOF-1390: 12B7 / 1292 / 1279 / 1283 (7.70 x 6.45), circle 1300.
4. F-T321-02: B34 from the house SW wall line (x -194.493 drawing mm) to CEC: 1.400 m in no T-311 run.
5. V3.0.20: no line on a roof element other than FIN.WP.ROOF / ROOF_UPTURN / MEMBRANE_ROLLS (s.8 below).

## 9. Not done / uncertain

- The freelancer's roof cells were not read (23.6 MB workbook, over the connector limit); 285.00 is the T-071 figure.
- What the D bands are physically (0.640 / 0.1575 m2 ranges) and the falls-layer trade (CONFLICT) are open.
- ROOF-1390's net area (dome 3, the 2.18 m box) stays HELD with the roof (Q-34).
