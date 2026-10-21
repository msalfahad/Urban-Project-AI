# T-119 Alsenan columns column by column to the controlling member, with the joints (NO REPO CODE)

Worker 1 (structural lane S), 2026-10-21. Development villa, not an accuracy claim. Nothing is wired and no released
quantity changes: a checked piece for the V3.0 candidate (lane I). Rules: URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1
(column concrete height = structural storey interval - depth of the deepest member framing into THAT column, slab t when
none; never a global depth), URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1 (joint = column area x (D_ctrl - t)),
UP-QTY-STATUS-001, owner Q-54 B (annex level held), Q-61 C (beam pieces member by member).

Sources (Drive "Alsenan chalet project", scratchpad copies, never committed): "ST7757 dxf.dxf" (sha256 9f9d1179...38079
= manifest) and "ST7757.pdf" (sha256 74da1523...37e3): p.1 COLUMN & AXIS PLAN (marks and printed sizes), p.4 / p.5 / p.6
GROUND / FIRST / SECOND FLOOR ROOF SLAB (columns drawn per storey, legend T.C turn column, D.C dead column, P.C planted
column), p.9 Schedule of Columns, p.10 Schedule of Simple Beams; all read by eye at 110 / 300 dpi this run. Beam
members, depths and statuses: the merged beam member register (research/agents_t110/BEAM_MEMBER_REGISTER.csv) with the
route G band polygons (research/agents_t110/scripts/bands.py). Slab t per panel: T-139 PANELS.csv (agents/task-T-139,
READY, not merged: only the thickness of the panel next to each column is taken from it; ST p.8 note 18 = 16 cm, tags
T 16 / T 18). Storey intervals: T-064 project data DRAWING-VERIFIED (GF +1.00 to +5.50 = 4.50, 1F 4.20, 2F 4.20).

Repeat (scratchpad dir W, outputs O): `python -I read_columns_dxf.py <ST.dxf> W/dump.json && python -I prep_frames.py
W/dump.json W && python -I ../agents_t110/scripts/bands.py ../urban_engine_m4_correctness/st7757_route_g W/bands.json &&
python -I ../agents_t139/slab_faces.py <ST.dxf> W/faces.json && python -I column_ledger.py W
../agents_t110/BEAM_MEMBER_REGISTER.csv <T-139 PANELS.csv> O && python -I summarise.py O/COLUMNS_TO_CONTROLLING_MEMBER.csv
O/ledger_summary.json`. Re-run this session from the committed scripts: byte-identical CSV and summary.

## 1. Result in engineering terms (column concrete above the necks, m3)

| Storey | Columns | Hand by the rule (all, candidate values) | of which CALCULATED | Joints A x (D_ctrl - t) | Engine released (full interval) | Engine after T-126 scope | Freelancer (interval - 0.75) |
|---|---|---|---|---|---|---|---|
| GF (p.4) | 30 | **16.900 .. 16.994** | 15 cols 8.875 | 2.572 | 20.247 (-3.347 .. -3.253, -16.5 %) | 20.250 | 17.438 (-0.538 .. -0.444, -3.1 .. -2.5 %) |
| 1F (p.5) | 20 (18 + 2 P.C) | **8.609 .. 8.678** | 13 cols 5.419 | 1.212 | 10.668 (-2.059 .. -1.990, -19.3 %) | 10.248 | 7.728 (+0.881 .. +0.950, +11.4 .. +12.3 %) |
| 2F (p.6) | 9 (8 + 1 P.C) | **3.307** | 5 cols 1.750 | 0.481 .. 0.487 | 5.796 (-2.489, -42.9 %) | 3.948 | 3.381 (-0.074, -2.2 %) |
| **Total** | **59** | **28.816 .. 28.979** | 33 cols **16.044** | **4.264 .. 4.270** | **36.711 (-7.895 .. -7.732, -21.5 .. -21.1 %)** | 34.446 (-15.9 .. -16.3 %) | **28.547 (+0.269 .. +0.432, +0.9 .. +1.5 %)** |

The range is only the C8 section conflict (30X80 on p.1 vs 90 in the schedule, two columns). Re-add checks pass
(summarise.py asserts): per column height = interval - D_ctrl, column m3 = A x height, and column + joint + A x t =
A x interval for every column with one slab thickness; storey totals re-add to the total; 59 = 33 + 11 + 6 + 7 + 2.

Where the hand differs from the engine and the freelancer, in m3 (total; the per-storey split is in ledger_summary.json):

| Cause | vs engine 36.711 | vs freelancer 28.547 |
|---|---|---|
| 5 column pieces no upper slab plan draws (1F C3, 2F C3 x2, C5, C8; T-100, removed by T-126) | -2.268 | - |
| GF rounding of the engine line table | +0.003 | - |
| height basis: engine full interval vs the rule, sum of A x D_ctrl over 59 columns | -5.467 | - |
| height basis: freelancer's uniform 0.75 vs the column's own D_ctrl, sum of A x (0.75 - D_ctrl) | - | +0.443 |
| his count / size slips (T-100: GF C1 2 / C2 6 / C9 3 / C11 1 vs drawn 1 / 4 / 2 / 2, 1F no C6, 2F C9 0.90) | - | -0.011 |
| C8 section conflict, low reading 30X80 | -0.163 .. 0 | -0.163 .. 0 |
| **total** | **-7.895 .. -7.732** | **+0.269 .. +0.432** |

Concrete is moved, not saved: column (rule) 28.979 + joints 4.264 + column heads inside the slab A x t 1.203 = 34.446 =
the drawn columns at the full interval (GF 20.250 / 1F 10.248 / 2F 3.948). Under the rule the joint is its own line
(non-overlapping model) and the head belongs to the slab plate. **For lane I**: the beam register (T-110) measures beams
B x clear length x D between column faces and the T-139 slab panels stop at beam and column faces, so neither holds the
joint or the head; switching the column line to this rule without adding the joint line (4.264 m3) and the head
(1.203 m3) would lose 5.467 m3 silently (missing must never become 0).

## 2. How each column was measured (one row per column in COLUMNS_TO_CONTROLLING_MEMBER.csv)

- **Which columns stand on a storey**: the S-COL.BON outlines drawn on that storey's roof-slab plan (GF 34 / 1F 21 /
  2F 9 outlines), each bound to the p.1 outline at the same position (sheet offset found from 24 / 13 / 7 coincident
  outlines, binding error <= 0.07 m, turn columns 0.15 m) and to the p.1 mark with its printed size (35 marks, 35 bound,
  every binding checked against the p.1 render). Not columns of the storey: the two P.C outlines on p.4 (the starts of
  the 1F planted columns on B27 and B26), the P.C outline on p.5 (start of the 2F planted column on B19), and the
  second outline of each turn column on p.4. GF 34 - 2 - 2 = 30, 1F 21 - 1 = 18 + 2 P.C, 2F 8 + 1 P.C: equal to T-100.
- **Section**: the p.9 schedule band of the storey (read this run: GF C / C1 / C2 20x50, C3 / C4 25x50, C5 25x60,
  C6 25x70, C7 25x80, C8 25x90, C9 25x100, C10 25x70, C11 25x110; 1F C1-C5 20x50, C6 20x60, C7 20x80, C8 / C9 20x90;
  2F & Top C1-C6 20x50, C7 20x60, C8 / C9 20x70); planted columns at their printed P.C size. The drawn outline is
  listed where it differs (it carries no printed size).
- **Framing members**: every beam band of that storey's roof-slab plan within 3 mm of the column outline (route G band
  polygons, mapped with 0.6 mm fit error), each resolved to its T-110 member (mark, schedule depth H from p.10, status);
  plus the pieces route G has no band for (GF outer west strip BM-GF-061, the CB5 span 2 gap T-139 found, 1F box and
  0.10 strip outside CB12 BM-1F-037 / -038). Turn columns (T.C on p.4: GF C9 under B13 / B16 / B17 / B21, GF C8 under
  B1 / B28 / B26): the GF column is the p.1 orientation, framing read on both outlines (the beams land on the joint).
- **D_ctrl**: the deepest framing depth whose depth is printed: CALCULATED members, and members held for their WIDTH
  only (B29, CB2, B21, 1F B6, CB10: Q-61 C(1) conflicts; H is the same on both readings). **Height** = interval - D_ctrl.
- **Joint** = A x (D_ctrl - t), t = the slab panel next to the column (0.16 by note 18 or tag; 0.18 at the tank tags;
  a range where 0.16 and 0.18 panels meet, 2F x3); where no slab panel touches the column (the stair zone: GF C2 / C3 at
  the main stair, 1F C2 / C3), joint = A x D_ctrl.

Hand checks of three columns (verifier: re-measure these):

| Column | Section (p.9) | Framing (p.4-6, p.10) | D_ctrl | Height | Column m3 | Joint m3 |
|---|---|---|---|---|---|---|
| COL-GF-19 C11 D.C (dead column, p.4) | 0.25 x 1.10 = 0.275 | B1 20x40, B27 90x85 (B27 starts on it, p.4) | 0.85 | 4.50 - 0.85 = 3.65 | 1.0038 | 0.275 x 0.69 = 0.1898 |
| COL-2F-50 C2 (NW corner of the tank) | 0.20 x 0.50 = 0.10 | B3 20x40, B15 20x120 | 1.20 | 4.20 - 1.20 = 3.00 | 0.300 | 0.10 x (1.20 - 0.18) = 0.102 |
| COL-1F-41 C9 | 0.20 x 0.90 = 0.18 | B7 20x75, B1 20x40, B18 35x75 | 0.75 | 4.20 - 0.75 = 3.45 | 0.621 | 0.18 x 0.59 = 0.1062 |

## 3. Status of the 59 columns

| Status | n | Column m3 | Joint m3 | What holds it |
|---|---|---|---|---|
| CALCULATED | 33 | 16.044 | 2.360 .. 2.364 | nothing |
| HELD, framing member held, D_ctrl NOT changed by it | 11 | 5.337 | 0.764 .. 0.766 | CB2 x3 / B21 width conflicts, B24 east span (cand B24 0.75), CB3 / B3 With Stair, 1F unlabelled B2 piece (cand 0.40), 2F four unlabelled pieces (cand <= the calculated D) |
| HELD, framing member whose depth is not printed | 6 | 3.008 (upper value: deeper -> shorter) | 0.446 | GF C7 (BM-GF-058 strip north of B20), 1F C7 (BM-1F-033), 1F C8 (BM-1F-037 box), 1F C5 / C3 on CB10 (BM-1F-034 strip), 1F P.C 20x50 (BM-1F-038 strip): projections of designer D-26 |
| HELD, storey interval (Q-54 B, annex +0.30 / roof +4.30) | 7 | 3.125 (at 4.50) | 0.455 | GF C x3, C3 x3, C5 in the annex zone; C5 / C3 on the CB5 line also carry the main roof (CB5, B1, B5) and the annex beam CB6: two roof levels on one column |
| CONFLICT, section (C8 30X80 on p.1 vs schedule 90; designer D-16) | 2 | 1.302 .. 1.465 | 0.239 | GF and 1F C8 at the lower neighbour side |

The 11 "D_ctrl not changed" columns are held only because the task holds every column that a held member frames into;
their height does not depend on the held member (5.337 m3). Release of these is a Lead / owner call, not made here.

## 4. Findings

1. **One Urban rule, five controlling depths, eight column heights**: D_ctrl on Alsenan is 0.40 (B1 / B2 / B3 only: 10 columns), 0.50 (CB4,
   CB9, CB13, B5, B4: 9), 0.75 (34), 0.85 (B26 / B27 transfer beams: 4) and 1.20 (B15 at the tank: 2). The freelancer's
   uniform 0.75 is right on 34 columns, too deep on 19 and too shallow on 6; net the rule gives 0.443 m3 more than his height basis, offset by -0.011 of
   count slips: his 28.547 lands within 0.94 .. 1.51 % of the rule by compensation, not by method.
2. **Transfer beams**: B26 65x85 and B27 90x85 carry the planted 1F columns P.C 20x50 / 20x70 (p.4 leaders) and frame
   into GF C8 (turn), C10, C11 (dead) and C11: these four GF columns are 0.10 shorter than the 0.75 basis.
3. **Turn and dead columns** (p.4 legend): GF C9 and C8 turn at the GF roof (1F outline rotated 90 deg); GF C11 at the
   D.C stops at the GF roof (no 1F row in p.9). The engine's presence test (T-126) already handles both.
4. **B15 20x120 at the tank** (p.10; top bars 6 ø 18 > bottom 4 ø 16): no section on the structural set shows whether it
   hangs below the slab or stands up as the tank wall. Read as printed (schedule depth below the slab top, the reading
   of every other beam): 2F C2 and C3 get 3.00 m. If the designer confirms an upstand, both become 4.20 - 0.18 = 4.02 m
   (+0.204 m3). Observation for the Lead (designer request), not a hold under any written rule.
5. **Drawn column outlines that differ from the schedule** (no printed size on any slab-plan outline): GF C x5 drawn
   0.20 x 0.40 (schedule 20 x 50), GF C3 x2 drawn 0.20 wide; 1F C3 / C4 / C5 / C6 / C7 drawn at the GF width 0.25 and
   1F C9 drawn 1.00 long (schedule 20 wide, C9 90 long); 2F C5 / C3 drawn 0.60 / 0.25; P.C 20x50 drawn 0.20 x 0.40 on
   p.5 / p.6. Section from the printed schedule (as T-100), because each slab sheet prints "THE BUILDER TO WORK WITH
   STATED DIMENSIONS NOT TO SCALE DRAWING" and p.9 is the only stated column size above the foundation. At the drawn
   sizes the total would be +0.793 m3 (GF -0.638, 1F +1.356, 2F +0.075; turn-column twin outline excluded). Listed per
   row (column `drawn`) so the verifier can see every case.
6. **For lane I (V3.0.x)**: see section 1, joints 4.264 and heads 1.203 m3 must become lines when the rule is wired.

## 5. Verdict proposals (for the verifier)

- Column height basis, engine (full interval, 36.711 / 34.446 after scope) vs hand by the rule: **ENGINE_WRONG** on the
  column line (-5.467 m3 move to joint + head under the written rule), **total concrete unchanged** if the joint and head
  lines are added.
- Freelancer 28.547 vs hand 28.816 .. 28.979: **RULE_DIFFERENCE** on height (uniform 0.75 vs the column's own D_ctrl;
  +0.443), **HAND_RIGHT** on counts / sizes (T-100 list), net +0.9 .. +1.5 %.
- 5 undrawn columns: ENGINE_RIGHT after T-126 (already verified).
- Joints: freelancer's workbook has no column-joint row; whether he carries them in beams or slabs is UNRESOLVED.

## 6. Not done / uncertain

- Storey intervals are the T-064 DRAWING-VERIFIED floor-level differences; a structural slab-top level is not printed on
  the ST set (owner Q-54 directive: a level needs a known physical reference). A different finish build-up between the
  ground slab and the suspended floors would shift GF heights; not printed, not assumed.
- Column bottom at GF taken at the GF level (+1.00) for every non-annex column, as T-100 / T-064; the necks below are
  T-100 / Q-21 C (held). Columns next to the +0.15 courts (pool court, sea side) stand on the same ground beams.
- Joint t comes from T-139 PANELS.csv (READY, not yet merged); the three 0.16 / 0.18 corners keep a range.
- Beam depths are the p.10 schedule H as carried in the T-110 register; continuous-beam depths (CB rows) are the
  register's (printed continuous schedule, not re-read this run).
- Engine figures are quoted (T-100 / T-044 run B line table; T-126 scope table), not re-run.
