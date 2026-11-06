# T-550 B9 blockwork: T-543's UNRESOLVED 101.43 m2 taken to physical causes, H1 measured (research, unwired)

Worker 1 (lane S), 2026-11-06, claim 07:23 UTC, run session_01E6cPnejbSPSQD3juAee7VA. Files: `t550_parapet_split.py`
(R-T550-1, any villa), `t550_alsenan.py` (the restated table), `t550_section_parapets.py` (DWF section reader),
`out/T550_UNRESOLVED_RESTATED.json`, `tests/t550_parapet_split/` (8 tests). No engine module, method, rule / knowledge
version, registry or candidate file changed; no quantity moves. Drawings read this run (Drive "Alsenan chalet
project"): the architectural .dwf (sections A-A / B-B, vector), P7757_DXF_COMPRESSED.zip (P7757.dxf: GF / 1F plans, NW
and SE elevations), p7757_arch_sheet09.pdf (NE elevation), p7757_arch_sheet10.pdf (A-A),
Alsenan_Architectural_P7757_Pages_07-08.pdf p.1 (SW elevation); his masonry workbook (Drive text reader, R-T541-1).

## 1. Physical element and H1 (ERS s.2 steps 1-3)

A parapet is the wall standing on a roof edge. The engine measures its face ABOVE THE FINISHED ROOF (centreline x
printed height above finish, T-311 / T-319). Below the finished level the architect's cuts hatch one concrete element:

| Roof | Reading | Finish | Hatched slab top | Edge member bottom | Parapet top |
|---|---|---|---|---|---|
| +5.50 terrace | P7757.dxf NW elevation, lines 27E2 / 27E5 / 27E6 / 27E3, hatch 27D1 | +5.50 | +5.45 | **+4.95** | +6.00 |
| +4.30 annex | P7757.dxf SE elevation, 241A / 2419 / 241E / 241B, hatch 1C01 | +4.30 | +4.25 | **+3.75** | +4.80 |
| +5.50, +9.70, +13.90 | DWF SECTION A-A (datum by 4 markers, 1.8 mm spread) | 0 | -0.05 | **-0.549 / -0.549 / -0.55** | +0.499 / +1.599 / +0.50 |
| +4.30, +9.70 | DWF SECTION B-B | 0 | -0.05 | -0.468 .. -0.551, deeper cuts -1.10 / -1.20 | +0.499 |

**H1 (MEASURED):** every one of his parapet heights is the printed height above the finished roof + 0.50 m: 1.00 =
0.50 + 0.50 (GF terrace + annex row), 1.80 = 1.30 + 0.50 (1F roof, elevation dimension 130), 1.00 = 0.50 + 0.50
(+13.90 roof). 0.50 is the drawn edge-member depth below the hatched slab top (0.55 below finish), not the roof
build-up b_edge (the only drawn roof layer is the constant 0.05 band T-214 refused). T-543's "+0.63 on the 1F roof" was
his 1.80 against the engine's mean run height 1.171: the printed nominal is 1.30; the 0.13 are the per-run printed
heights (NW-5 0.448, SE-1 1.041, NW-4 1.099). Whatever b_edge proves to be, the zone below the finish is concrete in
every printed alternative (cuts hatch it; ST p.14 P1 upstand 'more than the height of roof finishing'): beam lines own
it to the slab top, STR.CONC.PARAPET (HELD) the upstand. So the class of that part does not wait for D-39.

## 2. The parapet residual (T-543 row 5d, 71.4658 m2) split exactly (R-T550-1)

| His row | His m2 | Engine face above finish | Length census | Below finish (concrete) | His flat height vs printed per run | HELD run heights |
|---|---|---|---|---|---|---|
| GF + annex 66.00 x 1.00 | 66.0000 | 29.2775 (58.555 m x 0.50) | +7.4451 UNRESOLVED | +29.2775 ENGINE_RIGHT | 0 | - |
| 1F roof 42.85 x 1.80 | 77.1300 | 57.6617 (49.233 m) | -11.4888 UNRESOLVED | +24.6163 ENGINE_RIGHT | +7.6307 ENGINE_RIGHT | -1.2900 (SW-2 0.385 .. 1.60, NE-1 / SW-1) |
| +13.90 roof 29.80 x 1.00 | 29.8000 | 14.5250 (29.050 m x 0.50) | +0.7500 RULE_DIFFERENCE (outer 2 x (8.10 + 6.80) vs centreline) | +14.5250 ENGINE_RIGHT | 0 | - |
| **Total** | **172.93** | **101.4642** | **-3.2937** | **+68.4188** | **+7.6307** | **-1.2900** |

Sum 71.4658 = T-543 5d exactly (asserted). Length causes named: 1F his 42.85 is the drawn chain 49.233 minus NW-5
(6.625 m, the 0.448 m low run) within +0.242 m (consistent, not proven: his row names no run); GF + annex +7.445 m over
the drawn 58.555 m (outer faces about 59.4 m): no further run drawn on layer 5 at +4.30 / +5.50.

## 3. The other UNRESOLVED parts (investigated; stay UNRESOLVED, each named)

- **Projections 41.25 (his 7.50 x 5.50, 1F page, no opening).** 5.50 = printed +-0.00 to +5.50 (NW elevation 29D0). The
  only printed 7.50 is GF plan dimension 4E9 along the sea-side saloon facade: 0.70 wall + 6.33 glazed opening (window
  layer W 262-265, 6.232 m) + 0.47 wall (B5 / B6). No 7.50 x 5.50 masonry face exists on the four elevations or two
  sections (checked: NW arch frame, SE stair-tower frame, SW 1F overhang about 4.5 m). Physical element not identified.
- **Openings -26.284 (rows l + his unassigned -9.84).** Named, not movable to a number: door heights (he 2.40, owner
  fallback 2.20 where unprinted, Q-55 C: at most 25.40 m x 0.20 = 5.08 m2); HELD openings (lift / arch / panel / two
  doors) sit undeducted inside the HELD wall figures of row d while he deducts them (sizes HELD: the coupling is named);
  his four 20 cm openings name no floor. One-by-one matching to engine walls not done.
- **Wall-length census +15.00 (rows m, GF +5.52 / 1F +11.24 / 2F -1.76)** unchanged from T-543.

## 4. Restated B9 table by class (gap 792.8970 m2, exact)

| Class | T-543 | T-550 | Move |
|---|---|---|---|
| HELD | 587.2845 | 585.9945 | -1.2900 (1F held run heights, split out of 5d) |
| UNRESOLVED | 101.4319 | **25.9224** | -75.5095 |
| RULE_DIFFERENCE | 65.1486 | 65.8986 | +0.75 (+13.90 outer vs centreline) |
| ENGINE_RIGHT | 41.0513 | **117.1008** | +76.0495 (concrete below the finish 68.4188 + printed run heights 7.6307) |
| TOLERANCE | -2.0193 | -2.0193 | 0 |

UNRESOLVED gross |m2| after: 104.99 (projections 41.25, openings 26.28, wall lengths 18.52 (net +15.00), parapet lengths 18.93); net
25.92 because the signs cancel. ENGINE_WRONG: none found. The freelancer books 68.42 m2 of concrete edge (below the
finished roof) and 7.63 m2 of parapet above the printed heights as blockwork.

## 5. Verdict proposals (for the Checker)

- Parapet face below the finished roof, 68.4188 m2: **ENGINE_RIGHT** (concrete, not masonry; DWF A-A / B-B, P7757.dxf
  27D1 / 1C01, P1 note). Re-measure: `python3 -I research/agents_t550/t550_section_parapets.py <private .dwf>` and the
  four elevation lines by handle.
- 1F per-run printed heights, 7.6307 m2: **ENGINE_RIGHT** (T-311 run ledger, PRINTED runs); held runs -1.2900 HELD.
- +13.90 length 0.75 m2: **RULE_DIFFERENCE** (outer dimensions vs centreline).
- Parapet lengths (+7.445 / -11.489 m2), projections, openings, wall lengths: **UNRESOLVED**, named above.

## 6. Lesson row (proposed, ERS s.7)

| 2026-11-06 | T-543 held 71.47 m2 of parapet 'height below the finish, b_edge HELD' and read his 1F excess as +0.63 | the freelancer's datum was inferred against the engine's mean height instead of the printed nominal, and the zone below the finish was tied to b_edge | R-T550-1 (every villa): split a freelancer parapet row as H = printed nominal above finish + delta; read delta against the printed heights; the zone below the finished roof is concrete in every printed alternative -> ENGINE_RIGHT with the drawn evidence (else HELD); per-run printed heights vs his flat height ENGINE_RIGHT, HELD runs HELD; length census separate; a slab-top height is never a height above finish | tests/t550_parapet_split (B550 by hand: both datums; adverse slab-top-as-finish, held-as-agreement, no evidence -> HELD, negative delta / None / mm / unbased length) | proposed |

Missing: the projections element, his opening schedule by wall, his GF + annex parapet length basis, the 1F run he
omits (proof), b_edge (D-39, now irrelevant to the masonry class).
