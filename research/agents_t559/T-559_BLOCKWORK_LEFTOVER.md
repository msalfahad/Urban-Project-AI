# T-559 B9 blockwork leftover: T-550's UNRESOLVED 25.92 m2 taken to physical causes, parapet edge members by id

Worker 1 (lane S, non-candidate), 2026-11-06, claim 09:22 UTC, run session_01E6cPnbeJMZGUoD81iZ7u1F. Research only,
unwired: no engine module, method, rule / knowledge version, registry or candidate file changed; no released quantity
moves. Files: `t559_rules.py` (R-T559-1, R-T559-2, any villa), `t559_alsenan.py` (the table), `out/T559_LEFTOVER.json`,
`tests/t559_leftover/` (19 tests). Drawings read this run (Drive "Alsenan chalet project"): P7757_DXF_COMPRESSED.zip
(P7757.dxf), ST7757 dxf.dxf; his masonry workbook (Drive text reader). Decoded into `.work/private` only; his opening
rows stay in `.work/private/t559/his_openings.json`.

## 1. Openings, -26.2840 m2 (T-543 rows l GF / 1F / 2F + his 20 cm openings with no floor), opening by opening

Physical element: one actual opening in one wall (Q-73). His rows name no opening, so each unit is matched by floor,
wall section and size class (stated per pair in the JSON; consistent, not proven). Engine sizes are T-292's (merged
size + source), deductions sum to register V2 per floor (GF 42.660 = 42.6615 - 0.0015 print of the GF-W04 total).

His 20 cm section repeats the same five walls on GF / 1F / 2F (a shaft stacked through three storeys); its four
openings are 3 x 1.00 + 1 x 1.10. The only 20 cm shaft with one 1.00 opening per storey is the lift: L-GF-01 /
L-1F-01 / L-2F-01 (w 1.0, HELD; walls GF-W08, 1F-W07, 2F-W00), plus the lobby door D-GF-08 in GF-W08 (1.00 engine,
1.10 his). So his -9.84 has a floor and an id.

| Class | m2 | What |
|---|---|---|
| HELD | -23.3700 | he deducts openings the engine holds (not deducted, inside held walls): main door D-GF-07 -4.80, D-GF-14 -1.92, arched W17 -9.45 (outline HELD 4.4361 .. 9.858), lift doors L-GF/1F/2F-01 -7.20 |
| RULE_DIFFERENCE | -3.9000 | door heads: his 2.40 on every door vs the owner fallback 2.20 where none is printed (Q-55 C), on 22 matched doors |
| ENGINE_RIGHT | -5.3245 | printed window sill / head (T-201 / T-175: W08 / W09 / W10 / W13 / W14 / W24 / W25 / W27 / W29), drawing-confirmed h 2.20 (W11 / W12, T-207), true arched outlines W15 / W16 / W26 (UP-OPEN-ARCH-001) vs his rectangles |
| TOLERANCE | +0.0105 | widths within 5 mm (W08 1.501, W11 1.955) and the GF-W04 register print |
| UNRESOLVED | +6.3000 | counts: GF engine 5 external doors vs his 4 (D-GF-03 / D-GF-09, 0.90: +1.98), his 1.00 vs 0.90 / 1.10 (-0.48); 1F W18 (0.50 x 2.16, engine only, +1.08), his sixth 0.60 x 0.80 (-0.48), engine 10 doors vs his 8 (+1.76 +2.20), his 0.90 vs 1.00 (+0.24) |

## 2. The parapet edge member, by structural id (register ruling PARAPET EDGE DOWNSTAND MEMBER, F-C-T550-1)

Method: P7757 parapet face lines (layer 5, by handle) mapped onto the ST7757 roof-slab sheets by the column
registration (03_ARCH_STRUCTURAL_REGISTRATION pairs: arch GF / 1F / 2F plans -> ST, one translation each, 0.0 mm spread
on 30 / 20 / 9 columns; the GF roof-slab sheet = the 1F sheet + 38.724 m in x, 19 columns), then over the route G beam
bands (bands.py, fit <= 0.6 mm). 32 bands lie under the parapets of the four roofs; **every one is carried by exactly
one live STR.CONC.BEAM line** (27 RELEASED, 5 HELD; each route-G twin is EXCLUDED): no omission, no double count.

| Roof | Run (T-311) | P7757 handles | ST band / mark | B10 line |
|---|---|---|---|---|
| annex +4.30 | NE-6 | B34 / AC7 | GF BAND0014 CB7 20x75 | L-128bbb3f98713383935f RELEASED 1.6801 |
| annex +4.30 | SE-1 | B37 / B2D / B2E | GF BAND0028 B9 20x75 | L-db759eb6300a0147c463 RELEASED 0.9153 |
| annex +4.30 | SW-1 | B41 / B28 | GF BAND0027 B2 20x40 | RELEASED 0.2002 |
| annex +4.30 | SW-3 | B35 / B36 | GF BAND0029.2 CB6 20x75 | L-6bdfcf21ebb29773436e RELEASED 0.8775 |
| terrace +5.50 | NE-4 | B25 / AC7 | GF BAND0039, 0040.1, 0040.2 CB8 30x75; BAND0015 B1 | RELEASED 0.716937 / 1.310964 / 1.42875 / 0.091584 |
| terrace +5.50 | NW-7 | B33 / B30 / C85 / C86 | GF BAND0041.1 CB1 35x75 | L-2e2fc5195697247a6a0b RELEASED 1.940009 |
| terrace +5.50 | SW-9 | BDB / BDC | GF BAND0032 B1 20x40 | RELEASED 0.076 |
| 1F roof +9.70 | NE-2 | 127F / 1285 | 1F BAND0002.1 B4 20x50; BAND0027.1-.3 CB11 30x75 | RELEASED 0.381173; 1.539652 / 0.619159 / 0.7425 |
| 1F roof +9.70 | SE-1 | 12C4 / 12C7 | 1F BAND0014 unlabelled 0.20 (BM-1F-034) | L-a9d5e7dc22013e24d691 HELD 0.6 .. 1.8 |
| 1F roof +9.70 | SW-3 | 1273 / 1278 | 1F BAND0001.3 / .4 CB9 20x50 | RELEASED 0.335 / 0.355 |
| 1F roof +9.70 | SW-2 | 12B9 | 1F BAND0031.1 / .2 B23 45x75 | RELEASED 1.132104 / 1.11375 |
| 1F roof +9.70 | NW (sea side) | 12A7 / 1308 / 1322 / 1323 / 12A6; 1318 / 1319; 1309 / 130B | 1F BAND0018.1 / .2 CB12 25x75; BAND0025 (BM-1F-036); BAND0023 (BM-1F-035) | RELEASED 1.079463 / 0.942188; HELD 0.676 .. 1.015; HELD 0.135 .. 0.2025 |
| +13.90 roof | perimeter | outline 8.10 x 6.80 (his 29.80) | 2F BAND0006.1 (HELD), 0006.2 B15, 0009 B7, 0001.1 B3, 0001.2 B8, 0001.3 (HELD), 0003 B2, 0004 B1, 0005 B2 | 7 RELEASED, 2 HELD |

Finding (geometry): the architect's cut draws the edge member 0.50 below the slab top on every roof; the structural
schedule gives 0.50 only for B4 / CB9 on the 1F roof, and 0.75 (CB7, CB8, CB1, CB6, B9, CB11, CB12, B23, B7, B8), 0.40
(B1, B2, B3) or 1.20 (B15) elsewhere. Member sizes follow the schedule (B-S18), so the beam line owns the zone below the
slab top to the schedule depth; the masonry above the finish is the engine's face (ENGINE_RIGHT stands). The 5 HELD
lines stay HELD in B10 (never 0, never blockwork).

## 3. Per-run printed heights behind T-550's 7.6307 m2 (1F roof, his 1.30 above the finish vs the printed run)

NE-2 19.07 x 0 | NW-1 1.02275 x 0.001 | NW-2 3.1672 x 0 | NW-3 0.53045 x 0.001 | NW-4 0.4673 x 0.201 = 0.0939 |
**NW-5 6.625 x 0.852 = 5.6445** | **SE-1 7.30 x 0.259 = 1.8907** | SW-3 6.6699 x 0 | NE-1 / SW-1 / SW-2 HELD. Sum
7.6307 (asserted). Handles: SE-1 12C4 / 12C7 (7.500, over the BM-1F-034 band), NE-2 127F / 1285, SW-3 1273 / 1278;
NW-1 .. NW-5 on the sea-side group 12A7 / 1308 .. 1313 (the split of that group into runs is T-311's, not re-read).

## 4. The 25.9224 m2 restated (exact)

| Class | m2 | Parts |
|---|---|---|
| UNRESOLVED | 58.5064 | projections 41.25; wall-length census +15.0002 (GF +5.5193, 1F +11.2416, 2F -1.7608); parapet lengths +7.4451 / -11.4888; opening counts +6.30 |
| HELD | -23.3700 | held openings he deducts (s.1) |
| ENGINE_RIGHT | -5.3245 | printed window heights / arched outlines (s.1) |
| RULE_DIFFERENCE | -3.9000 | door head 2.40 vs Q-55 C 2.20 |
| TOLERANCE | +0.0105 | |
| **Total** | **25.9224** | |

UNRESOLVED gross |m2| 104.99 -> **86.93**. B9 table by class after T-559 (gap 792.8970 unchanged): HELD 562.6245,
ENGINE_RIGHT 111.7763, RULE_DIFFERENCE 61.9986, UNRESOLVED 58.5064, TOLERANCE -2.0088. ENGINE_WRONG: none found.

Wall-length census (beside the table, lengths in m, his section sums vs register V2 by group / thickness): GF his
external 78.55 / 15 cm 47.53 / 20 cm 8.20 vs engine EXTERNAL 76.743 (+1.50 HELD stubs) / INTERNAL 0.15 39.599 /
INTERNAL 0.20 15.000; 1F 54.97 / 57.14 / 8.20 vs 50.813 / 56.813 / 9.620; 2F 27.90 / 3.00 / 8.20 vs 26.85 / 3.00 /
9.75. His 20 cm shaft is 8.20 m on every floor; the engine's lift-front wall is GF-W08 4.30 / 1F-W07 3.22 / 2F-W00
1.80 (his front piece 1.80 each floor) and GF-W02 / GF-W03 (4.30 m of 0.20 internal walls) he books as 15 cm: section
placement, length-neutral. Net per floor +1.438 / +3.064 / -0.50 m: concentrated on the 1F external walls (+4.157 m);
not matched run by run here (his rows name no wall). Projections: no new element found (T-550 search stands).

## 5. Verdict proposals

- Openings: HELD -23.37 (held openings), RULE_DIFFERENCE -3.90 (Q-55 C door head), ENGINE_RIGHT -5.3245 (printed
  heads / outlines), UNRESOLVED +6.30 (counts, named). Re-check: `t559_alsenan.py --his <private rows>`.
- Edge members: ENGINE_RIGHT for the blockwork line; B10 carries all 32 bands once (27 RELEASED, 5 HELD). Re-measure:
  the handles above on P7757.dxf + the registration pairs; bands from `research/agents_t110/scripts/bands.py`.
- Projections 41.25, wall lengths +15.00, parapet lengths -4.04: UNRESOLVED, named.

## 6. Lesson row (proposed, ERS s.7)

| 2026-11-06 | T-543 / T-550 carried -26.28 m2 of 'openings census' and the edge member under the parapets as one number each | his opening rows carry no id and the edge member had no structural id | R-T559-1 (every villa): match his openings to the engine's by floor, section and size class, split each pair into width (tolerance <= 5 mm, else UNRESOLVED) and height (Q-55 C fallback RULE_DIFFERENCE, printed ENGINE_RIGHT, true outline ENGINE_RIGHT), HELD openings HELD, unpaired counts UNRESOLVED, census closed exactly; R-T559-2: parapet masonry from the finish, the edge member is the structural band under the parapet line, carried once by a live B10 line (0 = scope gap, 2 = double, both refused / reported) | tests/t559_leftover (B559 by hand; adverse held-with-deduction, paired twice, census not closing, mm / None, masonry from the soffit with a downstand, double-carried band) | proposed |

Missing: the projections element; his wall rows matched run by run; the 1F sea-side run split (T-311); his GF + annex
parapet length basis; the HELD facts behind the held openings and the 5 HELD edge bands.
