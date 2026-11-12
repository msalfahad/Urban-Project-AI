# T-737 EXTERIOR PLASTER READINESS on ARCH_TAKEOFF_V3.0.73 (worker 2, lane A, 2026-11-12; research only)

No quantity is measured, changed or wired; no candidate, hub, registry, rule / knowledge version file is touched.
Released default V2.9 + route G untouched. Rule R-T737-1 1.0.0 (`t737_rules.py`, every villa); application
`t737_alsenan.py` (`--check` rebuilds and compares); outputs `out/T737_READINESS.json`, `out/T737_ROWS.csv`. The QUEUED
T-314 r2 stage (agents/task-T-314 @ 080ccaa5, base V3.0.61) is read only through `in/T314_STAGE_T737.json`
(`t737_extract_stage.py`: summary blob 040ed5f9 = the T-698 pin, inputs script 7c6cb338, 12 source blob ids). No
drawing, workbook, client name or coordinate is in this folder. ERS read: s.2.1, s.2.4, s.3, s.7.

## 1. Physical element (ERS s.2.1)

The outer render / Sigma face of the envelope, band by band (storey F.F.L. -> next level, parapet outer / inner / top,
plinth, slab edge), each face once, every opening deducted once in full (Q-73) on the face that holds it. Exterior
heights are the printed levels (the storey band runs F.F.L. to the next F.F.L.: the render is continuous over the slab
edge, so Q-72 'to the slab underside' is an interior rule and does not cut it). Render 1:4 and spatter 1:2 (Q-79) are
materials of the same faces: spatter (B4-05, T-364) stays its own line on these hosts, never in the m2 here. Corner
beads (B4-09) are m.l on the arrises of these faces, arris once.

## 2. (a) Census of the stage on V3.0.73, by line id: LIVE 3, LIVE_NEW 15, STALE 0, GONE 0, COLLISION 0

| stage line | action | V3.0.73 | stage after (m2) |
|---|---|---|---|
| L-b05f70c9 GF storey | CHANGE | LIVE (HELD blank = stage base) | BOUNDED 376.694149 .. 410.179149 (W02 / D-GF-07 holes HELD) |
| L-8bb83e16 1F storey | CHANGE | LIVE | BOUNDED 248.178057 .. 249.954348 |
| L-d52c4f76 2F storey | CHANGE | LIVE | PROVISIONAL 117.305 (D-2F-01 2.20 m ASSUMED, Q-55 C) |
| 15 NEW lines (parapet outer x 4, inner x 4, top x 4, plinth, slab edge x 2) | ADD | element ids and stage line ids free | 3 MEASURED (GF / 2F parapet outer 14.385 / 14.900, 2F top 5.415), 11 bounded, 1F slab edge blank |

- The 7 facade hosts (3 FIN.EXT.FINISH + ARCH.FACADE GF / 1F / 2F / plinth) are identical in every index V3.0.61 ..
  V3.0.73 (13 indexes). V3.0.61 -> V3.0.73: 132 lines changed + 50 added + 0 removed, all STR.CONC / MAS.* /
  FIN.PLASTER / FIN.PAINT; no FIN.EXT / ARCH.FACADE line moved. So r3 re-runs the stage; it restates nothing.
- All 12 merged sources the stage read (T-305, T-311, T-324, T-337 x 5, T-349, T-348 x 2, T-567) have the same git
  blob on this tree as at 080ccaa5: STALE_SOURCE 0, so the 126 face rows and 38 holes are LIVE as built.
- Later merged records read against the stage (rule 3; each cited with the literal it must still contain):

| id | stage row | record | verdict |
|---|---|---|---|
| E1 | W02 hole 0 .. 28.485 | T-627 'W02 27.219: waits on D-53' | AGREES (HELD) |
| E2 | D-GF-07 sill / head +1.00 / +3.50 | T-682 'head 2.50 PRINTED' (Checker AGREE) | AGREES (2.50 = 3.50 - 1.00) |
| E3 | D-GF-07 width, hole 0 .. 5.000 | T-713 'opening widths not drawn (... D-GF-07' | AGREES (HELD) |
| E4 | D-GF-07 width | T-405 / T-697 ring 7.00 DC 'printed 2.50 x 2.00'; T-313 reveal head 0.200 x 2.000 DC vs T-305 / T-337 'leaf / hole width HELD' | **CONFLICT** (F-T737-1) |
| E5 | 'D-GF-07' in T-710 | 'DOOR:D-GF-07-PANTRY' gap 1.000 | NOT THE SAME ELEMENT (id collision, F-T737-2) |
| E6 | parapet tops x 0.30 | T-722 parapet concrete floors 1.799103 / 1.677886 / 2.949453 / 1.6245 m3 | AGREES: 5.99701 / 5.592956 / 9.83151 / 5.415 m x 0.30 (cross-trade, 6 dp) |
| E7 | F-T314-2 t199 helper | T-655 fix merged (c553cb8f) | FIXED: no r3 blocker |

## 3. (b) Restated faces: none stale. Spot re-measure by handle (own decode, P7757.dxf sha256 ab54dd55, mm)

- 2F storey (L-d52c4f76, the only valued storey line): outer wall lines on layer 1 bound an 8,100 x 6,800 box:
  1291 (6,800, one line), 1274 / 1275 / 1276 / 1277 on one y (1,730 + 1,295 + 675 + 1,600 = 5,300 + 3 gaps 2,800 =
  8,100), 1280 / 1281 (615.8 + 6,484.2 + gap 1,000 = 8,100), 1287 / 1288 (1,250 + 4,350 + gap 1,200 = 6,800).
  Perimeter 29.80 m (= ARCH.FACADE_RUN 2F RELEASED 29.8) x band 4.20 (+9.70 printed: level texts 134E / 1350 / 1352;
  +13.90 from the sections, not re-read) = **125.160 m2 = stage 2F gross 125.16 AGREE**; faces 8.1 x 4.2 = 34.02 and
  6.8 x 4.2 = 28.56 AGREE with T-337 2F/NE-1 and 2F/NW-1.
- Level breakpoints the stage and the bead split use, printed in the plans by handle: +0.15 (394, 407, 409, 40B, 40D,
  4AE), +0.30 (401, 403, 405, 4AC), +1.00 (40F, 411, 413, A74), +4.30 (D20), +5.50 (D16, D18, D1B, D1D, 1251), +9.70
  (134E, 1350, 1352): AGREE.

## 4. (c) The 43 exterior bead rows (T-728 H2b) re-bound onto the stage lines: 43 in, 51 out, arris once

Rings take the line of the face that holds the hole (all 36 on their storey line: same ids, stage keeps them). Vertical
arrises (T-172 VERTICAL_CORNERS, merged) are cut at the face levels of the stack on either side that holds most of the
span (T-337 binding levels). State per R-T728-1 on the post-stage host (PROVISIONAL / MEASURED = RELEASED in the line
index, T-469 line_class).

| row | before (T-728) | after the stage, by host |
|---|---|---|
| EXT#2F-CONVEX 18.8 | 1 row on 2F storey | 2F storey 16.8 (4 x 4.20) RELEASED + 2F parapet outer 2.0 (4 x 0.50) RELEASED |
| EXT#1F-CONVEX 39.0 | 1 row on 1F storey | 1F storey 37.8 (9 x 4.20) + **GF storey 1.2** (NE-2/SE-1 +4.30 .. +5.50 faces the lower roof, bound to GF by T-337), both HELD point |
| EXT#GF-CONVEX 66.9 | 1 row on GF storey | GF storey 57.5 + plinth 7.4 + annex parapet 1.0 (HELD point) + GF parapet outer 1.0 (RELEASED) |
| EXT#GF-MOUTHS 43.1 | 1 row on GF storey | GF storey 36.4 + plinth 4.3 + annex parapet 1.0 HELD point; **1.4 NO_HOST** (2 x +4.80 .. +5.50 at NE-5/NE-6: passage wall end above the annex parapet top, no stage face) HELD blank |
| EXT#1F-CONVEX-PARAPET-ENDS 0 .. 11.9 | on 1F storey | **1F parapet outer** (bounded): HELD 0 .. 11.9 |
| EXT#GF-CONVEX-PLINTH 2.1 .. 2.55 | on ARCH.FACADE plinth L-c0e9a4c6 | **stage PLINTH GF line** (bounded): HELD 2.1 .. 2.55 |
| EXT#GF-MOUTHS-STOP 0 .. 1.2 | on GF storey | **GF parapet outer** +5.50 .. +6.00 (T-172): HELD 0 .. 1.2 own cause |
| 36 rings | GF / 1F / 2F storey | same line; 2F 5 rows RELEASED 19.8709 (incl. D-2F-01 5.4 ASSUMED Q-55 C); GF / 1F HELD point; W02 / W03 / W17 HELD blank (own) |

Reconciliation (exact, asserted): measured ledger 310.6831 m.l (GF 183.5 + 1F 88.5122 + 2F 38.6709, = T-697 exterior)
= RELEASED 39.6709 + HELD point 269.6122 + NO_HOST 1.4. Released beads move 0 -> 39.6709 m.l only when r3 merges.

## 5. Findings

- **F-T737-1 (CONFLICT, decider named).** D-GF-07 main door width: the bead / reveal ledgers (T-405, T-697 ring 7.00,
  T-313 head 0.200 x 2.000) carry 2.00 m DRAWING-CONFIRMED; the face ledger (T-305 / T-337) holds the same width
  (render single leaf vs plan 2.00 x 2.50, T-175, D-53) and the masonry round (T-713) says the width is not drawn. One
  physical opening, two states. Carried as CONFLICT, nothing picked (R-T730-1). Decider: a Lead ruling on the evidence
  hierarchy (a printed plan tag ranks above a render, ERS s.2.2) or designer D-53. Impact if 2.00 governs: GF storey
  high 410.179149 -> 405.179149 m2 (hole 5.000 fixed); if held: the ring D-GF-07#EXT 7.0 m.l must become
  2 x 2.50 + w (w held), and T-313 / T-405 reveal / bead rows follow.
- **F-T737-2 (id collision).** 'D-GF-07' names the main door in T-305 / T-337 / T-405 / T-559 / T-584 and the GF-07
  pantry door in T-336 / T-710 (FIN.WP.DOORWAY 0.200 m2). Never join the two by name; key by opening and room.
- **F-T737-3 (one face, two codes).** The plinth face is ARCH.FACADE L-c0e9a4c6 (HELD blank, register / geometry) and,
  after r3, NEW FIN.EXT.FINISH PLINTH GF (71.68859 .. 72.749795). Both are B4-07 codes: T-739 aggregation and the
  scoreboard must count the face once (union-not-sum), ARCH.FACADE m2 as register only.
- **F-T737-4 (bead hosts move at r3).** All 7 non-ring bead rows change host or split when T-314 r3 lands (2F
  corners onto the 2F parapet; the 1F lower-roof part onto GF; plinth and stop-end onto their new lines). T-736 / H2b
  must wire from this re-binding, not from the T-728 host column.

## 6. (d) Rebase plan for T-314 r3

1. Branch from the then working branch (after T-736 merges: T-717 V3.0.74, T-729 V3.0.75, T-736 V3.0.76, T-738
   V3.0.77 per the hub order); take the next free ARCH_TAKEOFF_V3.0.x and BOQ_FAMILY_MASTER version at claim and
   reserve them in the row. Port arch_v3062.py as arch_v30xx extending the candidate of record (base module and
   check-key names only, R-T314-1 unchanged), hub --v30xx-inputs, run / apply scripts on the new base; inputs
   (t314_inputs.py) unchanged: their 12 sources are the same blobs.
2. Re-assert outside rows on the new base (5,123 V3.0.73 lines + whatever T-717 .. T-738 add); expected CHANGED 3 /
   ADDED 15; totals move only in FIN.EXT.FINISH|m2 ('AT_LEAST 152.005 + HELD 14 lines').
3. Rebuild every candidate-bound artefact by its tool in the run-of-record commit (T459 binding, maps: L-T717-1).
4. Carry F-T737-1 as CONFLICT on the GF line (no figure picked) unless the Lead rules first; state F-T737-3 in the
   package. L4 to the end; F-T314-2 is fixed (T-655).
5. After r3: H2b wires the 51 re-bound bead rows of section 4 (T-736 successor), and T-364 (B4-05 spatter) restates its
   71 + 46 exterior rows on the stage lines (T-698).

## 7. Engine vs freelancer (unchanged; nothing wired)

His net 1,469.9675 m2 vs the stage 1,007.931 .. 1,085.613 m2 (-31.4 % .. -26.1 %), reconciled to cause by T-567 (residual
0): RULE_DIFFERENCE (domes 181.806, half vs full holes Q-73 A, plinth), his HELD / UNKNOWN rows, ENGINE_RIGHT (row 65
double count 9.000, row 74 no exterior face 52.770). Beads: exterior 310.6831 vs his 1,297.35 m.l RULE_DIFFERENCE (T-697).
This task moves no figure.

## 8. Lessons-register row (proposal, ERS s.7)

2026-11-12 | a bead ledger was hosted on the storey line although its arrises cross the parapet / lower-roof / plinth
bands that a pending face package moves to their own lines | the derived element (arris) was bound to a line by floor,
not by the face that holds each height | when face lines are split by element, cut every vertical arris at the face
levels and host each part on the line of the face that holds it; parts no face holds are NO_HOST, never a neighbour |
R-T737-1 rule 4 | tests/t737_exterior_readiness | PROPOSED.

Tests: tests/t737_exterior_readiness (31): synthetic villa W737 by hand (two-F.F.L. corner, parapet cut, mirror,
units mm vs m, gap -> NO_HOST, ambiguous stacks, slab edge without levels, gone host never a neighbour, moved host,
unit / element swap, collisions, zero / inverted refused) and the development villa (rebuild equal, pins, stale 0,
history, sources, evidence verdicts, parapet tops, 43 -> 51 rows, 310.6831 exact, specific splits, conflict carried).
