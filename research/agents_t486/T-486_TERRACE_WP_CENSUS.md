# T-486 B8-07 balcony / terrace waterproofing: applicability census, overlap with the roof WP lines

Worker 2 (lane A), 2026-11-03, run session_01E6cPnb7f8PsvX8qhs7zV3a. Research piece (backlog-permitted, no candidate
file): research/agents_t486/* and tests/t486_terrace_wp/*; no engine module, method, rule / knowledge version, registry
or candidate quantity changed. ERS applied: s.2 steps 1-4 (element first, evidence hierarchy, reconstruction from the
drawn entities, reconciliation in units), s.3 (physical vs contract; a covered surface is not a roof), s.7 (lesson below).
Drawings by Drive title and entity handle only ("Alsenan chalet project": P7757_DXF_COMPRESSED.zip -> P7757.dxf sha256
ab54dd55..., re-checked this run; sanitary-7757.pdf sheet 2, 1F drainage). No coordinate is stored: `t486_alsenan.py`
reads the named entities from the private decoded drawing at run time (without it the zone is HELD, tested).

## 1. Result in engineering terms

**B8-07 on the development villa: 0.000 m2 NEW membrane, by evidence, not by default.** No BALCONY or TERRACE label
exists in the drawing (every room-label block listed: 4 ROOF, 2 VOID, no balcony); no slab projects past the floor
below with a door onto it. The only surface with a terrace FUNCTION (a door opens onto it) is the 2F roof terrace +9.70,
and its membrane is already in FIN.WP.ROOF (B8-06). The census found instead **one exposed slab with no line in any
family: the slab round the oval void over the GF pool court, 4.907 m2 open to the sky (MISSING, B8-06 roof function)
plus 0.640 m2 of ledge under the 2F slab overhang (HELD, exposure)**.

| Zone | Label / level | Under it | Access | WP layer | Membrane m2 (own) | Candidate line (V3.0.46) | Carried m2 | Status | Adds |
|---|---|---|---|---|---|---|---|---|---|
| ROOF-430 1F west | ROOF B8D, +4.30 (1.20 below the 1F FFL) | GF plate 100 % (T-062) | no door | YES (UP-WP-ROOF-001, Q-24); 1 gully + RWP, slope 1 % | 55.560 (T-062 / T-321) | L-d57d2dc2 FIN.WP.ROOF | 55.559 | CARRIED, residual +0.001 named (T-303) | 0 |
| TERRACE-550 1F SE L strip | ROOF B81, +5.50 = 1F FFL | GF plate 100 % | no door (windows only; T-321's "door closure 0.406" is the Q-25 drafting gap on a layer-D line) | YES; gully, slope 1 % | 32.721 | L-2f7502be | 32.721 | CARRIED, 0.000 | 0 |
| ROOF-970 2F roof terrace | ROOF 12AA / 12C3, +9.70 | 1F plate 99.0 % | 2F roof door (T-321 s.2) | YES; 4 RWPs, slope 1 % | 115.814 (circles) | L-636fd3ff | 115.832 | CARRIED (the B8-07-function zone), -0.018 named (polygon domes, T-321) | 0 |
| ROOF-1390 2F block roof | on no plan (D-62) | 2F | none | YES | HELD (Q-34; 49.665 drawing-derived beside) | L-3e8fe55d HELD | - | HELD, never 0 | - |
| **POOLCOURT-550** slab round the oval void | no label; +5.50 (LEVEL 1251) | GF pool court (exterior) | no door (glazed bay BD2..BD5, bath window C33..C3E) | YES by the rule's purpose ("exterior horizontal surfaces exposed to water"); **no gully, RWP or slope printed** | **4.907** open to the sky | **none** | 0 | **MISSING** (B8-06 roof function) | **4.907 m2 + 5.694 lm upturn** |
| POOLCOURT-550 overhang ledge | same slab, west of the wall line | pool court | - | UNKNOWN: under the 2F slab 4.20 m above, open to the void | 0.640 | none | 0 | HELD (exposure) | - |

Overlap with the roof WP, per zone (the acceptance check): 55.559 + 32.721 + 115.832 = **204.112 m2 already carried by
FIN.WP.ROOF, of which 115.832 is the terrace-function zone; nothing of it is added to B8-07**.

## 2. POOLCOURT-550 measured (own, from the named entities, read at run time)

Physical element: the top of the slab that the GF roof-slab sheet casts over the pool court (soffit 12.834 .. 14.704 m2,
T-127 / T-154, Q-68). Edges: west the 1F wall outer face (B62 / B61 / C35 / B60) and the curved bay's outer
face (BCD + BCE + BD0, r 1.935); north C7D and east B30 (single layer-5 lines: slab edges, no parapet; the parallel
lines C7E / C80 / B31 are layer 2 = the GF walls below); south the 0.20 m parapet pair to the SE strip (BDC / BDB) and
its end (B32 / C7F). Void BCF + 2F1C + C7A + 2F1B (3.825 m2, 7.139 lm; its east arc = the GF pool water edge r 1.55).
Three piers of the bay frame stand on the slab (layer D on 1F, the same outlines layer 5 on 2F; the elevation shows them
rising from the slab): north 0.2949, south 0.1724, south-west 0.1163 m2. Over it: the 2F plan draws nothing east of the
wall line, and the 2F roof slab's straight east edge passes over the bay bulge west of it.

| Term | m2 | Hand |
|---|---|---|
| open-sky gross | 8.3537 | wall line to plot line x slab north edge to parapet face, less the parapet end |
| - piers | 0.5837 | north 0.2950, south 0.1724, south-west 0.1163 (rectangles with notches / tabs and rounded corners) |
| - void east of the wall line | 2.8632 | 3.8245 - 0.9613 |
| **open-sky net (MISSING)** | **4.9069** | |
| overhang ledge (HELD) | 0.6396 | bulge 1.6010 - void 0.9614 |

Boundary: upturn 5.694 lm open-sky (pier faces 3.868, window wall 0.500, parapet face 0.895 + end 0.432) + 3.528 lm bay
face under the overhang = 9.222 (hand 9.223); open slab edges 6.868 lm (north 1.500, east 5.368) and the void edge 7.139
lm: terminations by detail, treatment HELD (length shown); cut line 0.562 lm continuation.
Reconciliation: T-062's 6.130 (gross 9.955 less the void, piers not deducted) = own 6.1301; own whole-slab net 5.5464
= 6.1301 - piers 0.5837; split 4.9069 + 0.6396. Every unit named, residual 0.0000.

## 3. Engine vs freelancer, verdict proposals

- B8-07: engine (candidate) no line; own census 0 new m2: **ENGINE_RIGHT as an absence** (proposal), with the registry
  state to change from NO_LINE to "APPLICABLE, CARRIED BY B8-06 FIN.WP.ROOF (115.832 m2)" (a family with no own line on
  this villa, like the F-3 families of T-471).
- POOLCOURT-550: engine 0 line vs own 4.907 m2: **ENGINE_WRONG (omission)**; the freelancer's roof line 285.00 m2 (cells
  not read: workbook 23.6 MB, over the connector limit) cannot show whether he has it: UNRESOLVED on his side.
- Freelancer roof 285.00 vs candidate 204.112 (-28.4 %): unchanged by this piece; adding 4.907 gives 209.019 (-26.7 %).

## 4. Rule (proposed, every villa; provenance T-486) and lessons row

WP applicability is decided by the physical surface, not the label: every slab top OPEN TO THE SKY is a WP zone under
UP-WP-ROOF-001 (its stated purpose); a door onto it makes it terrace function (B8-07), none makes it roof function
(B8-06); one physical membrane is one line (a terrace already in FIN.WP.ROOF is CARRIED, never added); a surface under
a slab above is not a roof (covered: NOT_APPLICABLE; covered but open beside: HELD); solids standing on the slab are
deducted and their faces get the upturn; slab and void edges are terminations (length measured, treatment by detail).

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-03 | A 4.9 m2 exposed slab (pool-court roof) had no WP line in any family; B8-07 read NO_LINE as if work were missing | applicability was keyed to ROOF / BALCONY labels; an unlabelled exposed slab fell between families, and a terrace already carried by the roof line looked like a gap | classify every slab top by exposure, access and the lines already over it; label never decides (every villa) | tests/t486_terrace_wp (normal: villa Q; adverse: carried roof terrace not added, held never 0, mixed held / measured refused, unknown access, rotation / mirror / mm, cut continuation; dev villa hand) | proposed |

## 5. For the Checker (re-measure one zone from the drawing, not from this file)

POOLCOURT-550 on P7757.dxf 1F frame: C7D, B30, C7F / B32 (parapet end), BDC, the wall line B62 / B60, void arcs BCF / 2F1C / C7A / 2F1B, piers CAA..CA4, CB2..CA2,
CA1 / CA3 / C9E -> 8.3537 - 0.5837 - 2.8632 = 4.9069 m2. Sanitary sheet 2: no gully / RWP / slope on it.

## 6. Not done / uncertain

- Drainage of POOLCOURT-550 is designed nowhere (falls, outlet): a designer item (RFI), never blocking; screed / falls
  for it as for the other roofs (B13-01, T-321).
- The pier footprint deduction assumes the piers are solid on the slab (drawn on two floors, rising in the elevation);
  if they are hollow cladding on the wall, the membrane would run under them (+0.584 m2): named, not chosen.
- The SE strip's west edge may meet a 0.10 m layer-D band along the wall (C9D / 1308, about 0.6 m2) that T-321 did not
  deduct: noted for B8-06, not measured here.
- Freelancer cells not read; the 2F roof's 1.453 m2 beyond the 1F plate (T-062) is consistent with the bay bulge
  overhang (1.601 m2 between the wall line and the bay face, less the wall's own band): not closed here.
