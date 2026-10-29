# T-335: ceiling ledgers bound to the V3.0.21 FIN.CEILING line ids, cross-checked against the V3.0.20 / V3.0.21 plaster / paint / tile lines (development villa; every villa by R-T335-1)

Worker 2 (lane A), claim 2026-10-29 08:47 UTC. Integration dependency of T-284 (backlog-permitted). Research only: no
engine module, rule / knowledge file, registry, candidate or released line changed; released default stays V2.9 + route
G; nothing released. ERS read: s.2.1 (physical element first), s.2.3 / 2.4 (first principles, reconcile in units),
s.3 (one element, several geometries; build before deduct), s.4 (rule + test, normal and adverse), s.7 (lesson row).
Builds on T-295 (MERGED 964c5ebe, Gate A 2026-10-25 15:33) and T-283 r3 (MERGED 6e141df6); both are imported, not edited.

## 1. Run and identity

Own run, Python 3.11.18, Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf `ab54dd55`) and
'ST7757 dxf.dxf' (`9f9d1179`), decoded into the private folder only: research/agents_t167/v304_run.py, then
research/agents_t315/v3021_run.py. **V3_0_20 json `097a80b6` / csv `ca90351b` and V3_0_21 json `be22a4e4` / csv
`3548e39c` (3,706 lines) REPRODUCED** = the candidates of record (T-244 / T-315 r2 Gate B). Extract
(`t335_alsenan.py --extract`): the 36 FIN.CEILING lines and the 130 FIN.PLASTER / FIN.PAINT / FIN.WALL.TILE lines
(ids, item codes, room / element ids, units, states, quantities, wall runs, formulas; no coordinates, no names) ->
CANDIDATE_V3021_T335.json; `--write` builds the tables, `--check` rebuilds them byte for byte.

## 2. Physical element (ERS s.2.1)

The ceiling plane of a room is what is built above the wall finish: the horizontal gypsum decor ceiling 0.15 below the
slab (Q-48 A), bulkhead vertical faces on free beam edges (owner method, Q-48 A + Q-43, R-CEIL-R3-2), stair soffits
(the stair finish), no-ceiling / dome pieces, and only where no decor ceiling is built an exposed plastered soffit.
Wall plaster, paint and tile are VERTICAL faces to the decor underside (GF 3.65, 1F / 2F 3.35, Q-43 / Q-48 A); the band
between the decor underside and the slab soffit is a wall face hidden behind the gypsum (Q-52 C: HELD), never a ceiling
face. A face carries layers (board, plaster coat, paint coat): two layers on one face are two pieces of work; the same
layer on one face in two lines is a double count.

## 3. Result (engineering terms)

**(a) Line ids.** All 36 V3.0.21 FIN.CEILING lines are the T-295 V3.0.15 lines with the same id, room / element, state,
quantity and gross (LINE_REBIND_T335.csv: 36 SAME, 0 CHANGED / NEW / GONE). V3.0.16 .. V3.0.21 changed only column /
ground-beam, wall-tile, skirting, ring and plaster / paint lines (their reports and modules: no ceiling code in
arch_v3016 .. arch_v3021). So the T-295 face-to-line ledger (79 faces, each once; 31 lines with faces, 5 exterior soffit
lines with none) binds to the candidate of record unchanged.

**(b) Cross-trade.** The 30 interior rooms that have a ceiling line carry 108 plaster / paint / tile lines (65 live, 43
NOT_APPLICABLE_WITH_EVIDENCE: superseded room lines and full-height-tile 'paint above tile'). **None measures a plan
area** (formulas: 'wall run x finish height - openings', 'face x owner height', 'tiled faces x owner height'); every
live line stops at the decor underside of its floor (3.65 GF / 3.35 1F, 2F), the two GF annex rooms at the held 3.15
(G2, BLOCKED). R-T335-1 validated over 66 claims (decor and bulkhead board in the ceiling lines, the stair soffit in
the GF stair-well line, every valued wall line): **double count 0.000 m2, horizontal face in a wall line 0.000 m2, gap
under the decor ceiling 0.000 m2** (CROSS_TRADE_T335.csv). The row's concern (V3.0.20 ceiling faces meeting the decor
lines) does not occur: V3.0.20 put plaster / paint on wall faces only.

What is in NO line, named (not chosen here):
- the hidden band above the decor underside, wall run x 0.15: **0 .. 53.851 m2 HELD** over the rooms whose lines print
  a face length (Q-52 C; no specification prints plaster above the false ceiling), counted once per face (the tile line
  repeats the plaster face in wet rooms); rooms whose lines print no run stay unmeasured (named in band_basis blank);
- paint on the gypsum ceiling: the candidate has no ceiling paint line (FIN.PAINT lines are wall faces). T-283 owner
  'paintable gypsum' 389.163 m2 (decor 361.229 + bulkheads 27.935) - for T-284: a layer of FIN.CEILING or its own
  line, never both (R-T335-1 rule 1);
- concrete ceiling plaster behind the gypsum: NOT SPECIFIED (refused as PLASTER_BEHIND_DECOR unless a specification
  prints it).

**(c) Totals per kind vs the T-283 ledger.** Decor 362.006092 m2 = T-283 361.2287 + the Checker's 0.777392 north of
riser 315 (residual 0.000000); bulkheads 27.9345 m2 = T-283 27.935 (0.0005 rounding of T-283's table); stair soffit
carried 1.440 m2 (MS1-LD, in the BLOCKED GF stair-well line). Engine interior FIN.CEILING (29 valued lines) 403.163 m2
PROVISIONAL vs decor 362.006 DRAWING-CONFIRMED: **-41.157 m2 (-10.21 %)**, every m2 named in T-295 s.4 (domes 29.070
HELD, stair pieces 21.201, no ceiling 15.316, B23 underside 0.173, less the 16.005 void the GF line deducts). Valued
lines after the fill: 353.410 m2 decor (-49.753 m2 vs their 403.163), + 5.626 decor in the BLOCKED 2F stair hall line,
+ 1.440 stair soffit in the BLOCKED GF line, + 2.970 in a NEW line (1F dressing), + 27.935 bulkhead faces apart.

**(d) Freelancer by cell (never proof; FREELANCER_T335.csv).** Diwaniya 24.84 vs 24.940 (+0.100, +0.40 %), master
bed GF 16.66 vs 16.550 (-0.66 %), driver 7.87 vs 7.875, kitchen 9.55 vs 9.630 (+0.84 %), laundry 10.00 vs 10.151
(+1.51 %), maid 19.58 vs 19.350 (-1.17 %), roof W.C. 5.62 vs 5.550 (-1.25 %): the rooms with no stair, dome or void
agree within 1.6 % (finish face vs structural face). Reception + dining + entrance 147.96 vs 103.937 (-44.023, -29.75 %:
light well 14.943 + stair ST-02 10.786 + the GF garden-band pieces HELD class P-2 and the remainder unexplained by cell); 1F living 38.96
vs 51.050 (+12.090, +31.03 %: his row omits the double-height ceiling over the light well, T-271 verdict); bedrooms
1-4 74.00 vs 60.699 (-13.301, -17.97 %: the west / east dome discs 11.923 HELD). Freelancer decor total 409.58 vs
362.006 (-47.574, -11.62 %): no verdict on a total while domes 30.718, stair zones 33.076, class 19.146 and the 2F
stair box 12.974 m2 stay HELD (T-283 / T-295 verdicts unchanged).

**(e)** tests/t335_ceiling_cross_trade (28): villa K hand fixture (lounge 6.00 x 4.50 with a 2 x 2 light well -> decor
23.00, beam B1 free edges 9.00 m -> owner bulkhead 1.35 (drawing-derived 4.05 alternative), walls 21.00 x 3.00 - 2.20
= 60.80, band 0 .. 3.15; store with a printed plastered soffit 3.00 and walls to the soffit 20.29; bath decor 5.00,
tile 22.83, band 0 .. 1.35; stair underside HELD) under identity / mirror / 37 deg + translation / mirror + -90 deg;
adverse: plaster behind a gypsum ceiling, a soffit in a wall line, an exposed soffit in a board line, a decor face in two
ceiling lines (LAYER_TWICE, 23.0 m2 counted twice), a bulkhead in a wall line, a wall line to the soffit booking the
hidden band (3.15 m2), a void / dome finished, a stair soffit in a ceiling or wall line, HELD booked or carried as 0,
HELD unnamed, millimetres, decor above the soffit, an interior face in an exterior soffit line; Alsenan: byte rebuild,
V3.0.21 hashes, 36 SAME, double 0, tops = decor underside, totals, FILL rows, freelancer cells, no coordinates / names.

**(f) FILL table for T-284 (FILL_T284_T335.csv)**, one row per V3.0.21 line key (35 keys: 34 lines + the 1F living
group of two) + 1 NEW LINE: V3.0.21 state, before (BLANK when BLOCKED), decor DRAWING-CONFIRMED, bulkhead ASSUMED -
OWNER-APPROVED apart, stair soffit carried, horizontal change, HELD items by name (blank), action. T-295's consumer
ledger (CEILING_FACE_LINE_LEDGER_T295.csv) stays the face-level input; this table is its line-level form on V3.0.21.

## 4. Rule, lesson, verdicts

- **R-T335-1** (ceiling_cross_trade.py, PROJECT-INDEPENDENT; provenance R-T295-1, R-CEIL-R3-2, Q-43 / Q-48 A, Q-52 C,
  UP-CEIL-001 / O-P8-02): one (surface, layer) in one line; a layer must fit its surface (gypsum: board + paint; exposed
  soffit: plaster + paint; void / dome: nothing; stair soffit: the stair-well line or none); wall lines are vertical and
  stop at the decor underside (the band above is HELD apart, a shortfall is a named gap); HELD never 0; units checked;
  a line's role from its element id (room ceiling / stair-well / exterior soffit).
- **Lessons row (ERS s.7, proposed):** 2026-10-29 | after the plaster / paint revision (V3.0.20) a reviewer feared its
  faces met the decor ceiling on the same soffit | the item families were compared by trade name, not by surface and
  layer | bind every finish line to (surface, layer) and refuse the same layer twice; read the wall line's formula and
  height against the decor underside before integrating a ceiling family (any villa) | tests/t335_ceiling_cross_trade |
  PROPOSED.
- **Verdict proposals:** decor vs engine ENGINE_WRONG on domes / stair pieces / no-ceiling strips (T-283 / T-295
  carried), ENGINE_MISSING on the 1F dressing 2.970; plaster / paint vs ceiling: NO DOUBLE COUNT (ENGINE_RIGHT on the
  wall faces' height basis, Q-43 / Q-48 A); band above the decor ceiling RULE_DIFFERENCE pending a specification (Q-52 C,
  HELD, not an owner question: an answered rule).

## 5. For the Checker (re-measure / re-derive)

1. Your own V3.0.21 run: json `be22a4e4` / csv `3548e39c`; re-extract FIN.CEILING (36 lines) and compare with
   CANDIDATE_V3015_CEILING_LINES.json of T-295: id, state, quantity, gross equal on all 36.
2. Pick GF-RC99C2A: its live plaster line HL:WALL_FINISH:GF_08 formula '53.188 m face x 3.65 m owner height ...'
   (BOUNDED 152.0505 .. 178.805), paint the same: no plan-area term; band 53.188 x 0.15 = 7.9782 m2 HELD; ceiling line
   L-eb3be58fc760b39f0e38 110.922696 -> decor 101.137092 + bulkheads 11.9189 apart.
3. Pick a wet room, 1F-R26FA0D: tile line 16.940 m run to 3.35 (decor underside), plaster BLOCKED; ceiling 10.151 decor
   + 0.2146 bulkhead; band 16.940 x 0.15 = 2.541 m2 counted once (not again for the tile line).
4. Confirm no FIN.PAINT line in V3.0.21 measures a ceiling (no ceiling paint line exists).

## 6. What stays HELD / not done

HELD blank (unchanged from T-295): stair soffit true areas 24.976 m2 plan, domes 30.718, class P-2 19.146, 2F stair box
12.974, stair / shaft tops 4.990, B23 underside 0.1725, edges / coves / board type. New named: hidden band 0 .. 53.851
m2; ceiling paint layer (no line); rooms whose wall lines print no run (band unmeasured). Not done (T-284's): any line
change, the 1F group split, the P-2 vs exterior soffit overlap check, the item-code decision for the ceiling paint layer.
