# T-742 B9-05 PARAPET BLOCK WALLS, missing family draft (worker 2, lane A, 2026-11-12; research only)

No candidate line, hub, registry, method or rule / knowledge version file is touched; released default V2.9 + route G
untouched; nothing wired or released. Rule R-T742-1..3 1.0.0 (`t742_rules.py`, every villa); application
`t742_alsenan.py` (`--check` rebuilds from merged files); own DXF census `t742_census.py` (private inputs, writes
`in/T742_CENSUS.json`: handles, layers, lengths only); outputs `out/T742_PARAPET_BLOCKS.json` / `.md`; tests
`tests/t742_parapet_blocks` (17). Drawing read this run: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip
(P7757.dxf, 1F plan and 2F plan, layers 5 and 1), plus the T-159 outline rings rebuilt from it in the private scratch.
ERS read: s.2.1, s.2.4, s.2.7, s.3, s.7.

## 1. Physical element and owner trade (ERS s.2.1)

One parapet run = one element: the body standing on a roof / terrace edge over its centreline, from where the masonry
starts to the coping underside. Datum (register 'PARAPET EDGE DOWNSTAND MEMBER'): the masonry starts at the slab
finish; where the keyed detail prints an RC upstand above the slab top (ST p.14 P1, '30'), it starts at the upstand
top: start = max(0, upstand - b_edge). The edge member below the finish is B10 beam concrete, never B9. Material: no
detail is keyed to any Alsenan run (P1 brick on a 0.30 upstand; P2 / P3 all RC; sections A-A / B-B hatch every
parapet with the slab: T-311 s.2), so every run is UNKEYED: HELD under D-39 / Q-65 C (DESIGNER_QUESTIONS item 5),
interval from the RC reading (0 in B9; the run is then STR.CONC.PARAPET, lane S) to the block ceiling, never in both,
never 0 as a value. No owner question (ERS 2.7: a designer item already answered HOLD by the owner, Q-65 C).

## 2. The draft lines (one per roof chain, 25 runs = the V3.0.23 candidate run set incl. T-324 NE-6x)

| Chain | Runs | B9-05 net m2 HELD (RC .. ceiling) | m3 | P1 reading at b_edge 0 | + m2 per m b_edge |
|---|---|---|---|---|---|
| Annex +4.30 | 7 | 0 .. 15.092525 | 0 .. 3.018505 | 5.997010 .. 6.037010 | 29.985050 |
| GF +5.50 | 3 | 0 .. 14.184950 | 0 .. 2.836990 | 5.592956 .. 5.673980 | 27.964780 |
| 1F +9.70 | 11 | 0 .. 57.661748 | 0 .. 15.471096 | 37.645009 .. 42.891953 | 49.157550 |
| 2F +13.90 | 4 | 0 .. 14.525000 | 0 .. 2.707500 | 5.810000 | 29.050000 |
| **Total** | 25 | **0 .. 101.464223** | 0 .. 24.034091 | **55.044975 .. 60.412943** | 136.157430 |

Ceiling = centreline x printed height above the finish (the register datum, no upstand, no cap): 101.464223 m2 =
T-550's engine face above finish 101.4642 (AGREE). P1 reading (block on the 0.30 upstand at b_edge 0) 55.045 .. 60.413
vs T-311's 0 .. 60.596: high end -0.183 = T-324 C3 (NW-2 straightened, -0.4435 m x 1.00 m above the upstand)
+ NE-6x (+1.29995 m x 0.20 = +0.2600) = -0.1835. Procurement: HELD (block type Q-65 C;
12.5 per m2 applies only to black block once keyed, Q-75 / Q-80). m3 on the 1F NW group uses t HELD 0.20 .. 0.6052 (s.4).

## 3. Census by handle (R-T742-3): 25 runs, every run tied to its roof-plan entities or named

Registration by vote (outline vertex on entity end point): GF outline -> 1F plan 13 / 18, 2F -> 2F plan 8 / 8, 1F ->
2F plan 9 / 22 (the 13 misses are the NW waves, s.4). DRAWN 11, PARTLY_DRAWN 8, NOT_ON_ROOF_PLAN 5 (1F NW group, s.4), run
found after T-311 1 (NE-6x). Notes and the named cause of every PARTLY_DRAWN:
- Annex NE-6 / SE-1, GF NE-4 / NW-7: the outer face is the SITE BOUNDARY line (AC7, B2C, B30 on layer 5); inner faces
  B34 / B37 / B25 + B34 / B32 + B33. Boundary parapets: one physical run, the boundary line is its outer face.
- Annex SW-3 B36 / B35 drawn 6.000 / 6.200 -> centreline 6.100 = the V3.0.23 low end 6.1001; GF SW-9 BDB / BDC drawn
  0.8948 + t/2 = 0.9948 = the V3.0.23 low end 0.99478: both ranges confirmed at their low end by the roof plan; the
  outline high ends stay as the range (not narrowed here: the Checker re-measures, then the hub narrows).
- 2F NE-1 / SE-1 / SW-1: gaps 1.000 / 1.200 / 2.800 m in the layer-1 wall lines are 2F openings at the plan cut, below
  the +13.90 roof; the parapet runs continuous (T-737 2F 8,100 / 6,800 box, Checker AGREE). 1F NE-2 outer 127F 18.27
  of 19.27 (the NE end arc 130A), inner 1285 18.87 exact; 1F SW-2 inner 12B9 4.125, outer 12A8 2.4949 + 12C5 at 0.40.

## 4. 1F NW group (finding F-T742-1)

The roof plan draws the 1F roof NW parapet's inner face as ONE straight line 12A7 = 11.600 m, with an outer profile of
varying depth: 1308 0.30 (5.487 m), 130E 0.605 (0.60), 12A6 0.20 (0.50), 1315 / 1319 0.498 (4.488), 1318 0.548 band,
inner grooves 1322 / 1323 (0.125 / 0.175). T-311's outline inner arrises total 12.0435 m: difference -0.4435 m =
exactly the T-324 C3 straightening of NW-2 already in V3.0.23 (12.3362 -> 11.8927 m centreline) and the 1F length
gap T-550 named (49.676 vs 49.233): **AGREES**, cause closed. The body thickness of the group is not one t: m3 HELD at
0.20 .. 0.6052 (m2 unchanged); which depth is solid block vs a render / frame profile is part of designer item 5.

## 5. One run, two trades (R-T742-2): face lengths vs the masonry centreline

| Chain | T-737 outer face | length from face / 0.50 | sum outer arris | masonry centreline (T-311) | corner term | closes |
|---|---|---|---|---|---|---|
| Annex | 14.671022 .. 15.271022 BOUNDED | 29.342044 | 29.342100 | 28.885100 | 0.457000 | yes (-0.000056) |
| GF | 14.385 MEASURED | 28.770000 | 28.769900 | 28.369900 | 0.400000 | yes (+0.0001) |
| 2F | 14.900 MEASURED | 29.800000 | 29.800000 | 29.050000 | 0.750000 | yes (0.000000) |
| 1F | 54.00748 .. 60.029307 BOUNDED | not invertible (per-run CAD-top heights, 3 runs HELD) | - | - | - | census instead (s.3, s.4) |

The faces measure the outer arris, the masonry the centreline; their difference is the corner term (outer - inner) /
2 per run, named, not a residual; every corner is counted once in each trade. Annex high end +0.60 m2 = NE-6x (T-324
C5) and the SW-3 cut range, carried as the bound.

## 6. Against the freelancer (comparison only)

His three parapet rows 66.00 x 1.00 + 42.85 x 1.80 + 29.80 x 1.00 = 172.93 m2 of blockwork vs B9-05 0 .. 101.464 m2
(P1 reading 55.045 .. 60.413): +71.466 m2 over the ceiling = his 0.50 m below the finish (concrete edge member,
ENGINE_RIGHT, T-550 68.419) + his flat 1.80 vs printed 1F run heights (ENGINE_RIGHT 7.631) + the named length / held
items of T-550 (net -4.584). Verdict proposals: material **UNRESOLVED** (designer item 5, Q-65 C); datum below the
finish **ENGINE_RIGHT** (T-550); B9-05 line **HELD**, not comparable as a released figure.

## 7. Lesson row (proposed, ERS s.7)

| 2026-11-12 | B9-05 had no line while the parapet was measured on the plaster side (T-737) and the concrete side (T-319) | the run ledger came from the floor outline only, with no handle on the roof plan, so the two trades could not be shown to measure one physical run | R-T742-1..3 (every villa): one element per run, one owner trade by keyed material (UNKEYED -> HELD 0 .. block ceiling, never both, never 0); masonry datum = slab finish or the printed upstand top; census each run by handle on the plan that draws the roof (DRAWN / PARTLY_DRAWN named / NOT_ON_ROOF_PLAN); faces vs masonry close by the corner term (outer - inner) / 2 | tests/t742_parapet_blocks (P742 by hand: 3 runs, corner once, one held height; adverse: RC run, unkeyed, missing / float / mm height, held without item, no masonry under the cap, upstand without b_edge, duplicate run) | proposed |

## 8. Missing / HELD (never 0)

Material per run and the cap profile (designer item 5, Q-65 C); b_edge per roof (D-39); 1F NE-1 / SW-1 / SW-2 heights;
1F NW body thickness 0.20 .. 0.605; block type -> procurement. For Worker 3 (integration, after the Checker): 4 new
B9-05 lines HELD as in s.2, ids free, no released line moves, exclusive with STR.CONC.PARAPET by run (register).
