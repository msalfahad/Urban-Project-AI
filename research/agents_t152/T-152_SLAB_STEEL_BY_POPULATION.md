# T-152 Alsenan suspended-slab steel by bar population, panel by panel and direction (NO REPO CODE)

Worker 1 (structural lane S), 2026-10-21. Development villa, not an accuracy claim. Nothing is wired and no released
quantity changes: a checked piece for the V3.0 candidate (lane I) once the checker has re-read it.

Sources (Drive "Alsenan chalet project", private copies in the git-excluded folder, never committed): "ST7757 dxf.dxf"
(sha256 9f9d1179...) and "ST7757.pdf" (sha256 74da1523...): p.4 / p.5 / p.6 roof-slab plans (200 dpi), p.7 dome and pool
details, p.8 general notes 9 and 22, p.15 TYP. SLAB ON BEAMS DETAIL and the temperature-reinforcement schedule, p.16 stair
details. Panel geometry: the T-139 ledger (agents/task-T-139 6f84281: 62 slab panels, 375.048 m2), rebuilt this run with
its own helper (`slab_faces.py` + `slab_ledger.py`, PANELS.csv identical to the committed one).
Rules: URBAN-REBAR-NET-AND-PROCUREMENT@v1 (kg = count x length x d^2/162, never kg/m3), URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1,
owner Q-44 A (dome openings), Q-71 (OPEN: count from a per-metre notation), UP-QTY-STATUS-001 (held is never 0),
owner directive drawing-first (a conflict between two drawings is recorded, not settled).

Files: `t152_slab_steel.py` (`--check` synthetic fixture; `build` makes `T152_INPUT.csv` from the private faces, numbers
only; `ledger` writes `T152_SLAB_STEEL.csv`, one row per panel and direction, and `T152_SUMMARY.json`).

## 1. Result in engineering terms (kg, suspended slabs; every count HELD on owner Q-71, lengths measured)

Bottom mesh = the printed panel bars, face to face, with the p.15 curtailment (50 % of the bars stop 0.125 L short of a
continuous support face) and the continuing half across those beams. Counts: A = ceil(rate x width), B = A + 1 (bar on
both edges), C = rate x width unrounded (information for Q-71).

| Slab (sheet) | Panels with bars / held | Bottom mesh A | B | C | Labels without '/m' (HELD) | Top bars over supports (HELD, 3 readings) |
|---|---|---|---|---|---|---|
| GF roof, p.4 | 28 / 5 | 1,463.56 | 1,536.11 | not split | 5.46 .. 8.79 | 432.84 .. 1,105.11 |
| 1F roof, p.5 | 14 / 8 | 858.91 | 903.36 | not split | 2.42 .. 10.77 | 255.04 .. 661.64 |
| 2F roof, p.6 | 7 / 0 | 592.62 (tank T&B 376.24 of it) | 628.58 | not split | - | 64.86 .. 164.77 + tank 28.66 .. 70.61 |
| **Total** | 49 / 13 | **2,915.09** | **3,068.05** | **2,853.00** | 7.89 .. 19.55 | 752.73 .. 1,931.52 + 28.66 .. 70.61 |

By diameter (A): ø10 2,466.91, ø12 186.96 (GF-078 7ø12/m, tank 2F-013 6ø12/m T&B), ø14 261.23 kg (tank 2F-011 T&B).

- **Measured part (lengths and kg/m), count HELD on Q-71**: bottom mesh 2,853.00 (C) .. 2,915.09 (A) .. 3,068.05 (B) kg.
- **HELD, never 0**: development / anchorage beyond the faces (note 9: 2 x 40 d .. 2 x 70 d per bar) 922.02 .. 1,708.27 kg;
  top bars over the supports 752.73 .. 1,931.52 kg (+ tank 28.66 .. 70.61); three labels without '/m' 7.89 .. 19.55 kg;
  13 panels with no printed bars (3.846 m2 dome corners, 0.235 m2 pool-court bay corners, 0.456 m2 stair wedge);
  temperature bars (no 16 cm row); GF-126 6ø14/m zone; 1F-084 corner bars 12 x ø14 (length not printed).
- Range of what is printed and measurable today, without development and temperature bars: **3,613.62 .. 5,089.73 kg**
  (C bottom + note-2 reading i, no tank top .. B bottom + the longest top reading with crossings + tank top + labels).

### Against the freelancer and the engine

| Line | kg | Hand (this ledger) | Difference | Verdict proposal |
|---|---|---|---|---|
| Freelancer slab steel (one lump, his slabs row: 5.40 t on 59.817 m3 = 90.3 kg/m3) | 5,400 | 3,613.62 .. 5,089.73 (+ HELD development 922 .. 1,708, temperature) | not like for like | **RULE_DIFFERENCE**: an allowance per m3 with no bar population; no % |
| Engine (frozen S7, restricted, 47 panels, reading C, note-2 top as 1/3 clear span from each face) bottom | 2,338.34 | 2,483.19 (same conventions, same 47 panels) | +144.85 (+6.2 %) | per cause below |
| Engine S7 top over supports | 1,463.68 | 1,597.64 (same conventions) | +133.96 (+9.2 %) | per cause below |

Bottom, by cause (every S7 panel pairs with one hand panel by area to 0.05 m2): GF-126 bars in x +63.70 kg (S7 blocked
the panel's x direction on the second label 6ø14/m; the hand ledger measures the printed 7ø10/m over the panel and holds the
6ø14/m zone apart: **UNRESOLVED**, designer item); continuing-half crossings +53.64 kg (hand 74.34 kg shared to the
panels from the probe gap, S7 20.70 kg support-owned); the remaining +27.51 kg is not decomposed (end-continuity reading,
e.g. S7 curtails 1F-018 x at the stair-zone end where the hand ledger finds no slab beyond the beam, and line placement on
skewed panels). On the other 44 measured panel directions the hand value is 0.0 .. 6.8 kg above S7 per direction, never
below: **ENGINE_RIGHT** on the method (same conventions re-derived independently from the drawing), the gaps being the
crossing allocation and the continuity reading above.
Top: not split by cause this run (not measured); S7 excludes the tank and replaces note 2 by 3ø16/Top at one support.

## 2. How each panel was measured (one row per panel and direction in T152_SLAB_STEEL.csv)

- **Labels**: every slab label of the three sheets read on the 200 dpi PDF and placed in its panel; 99 of the 107 '/m'
  labels on the slab layer lie within 0.35 m of a parallel bar line on the DXF bar layer (S-REIN-SLAB), the other 8 are
  the stair labels (8ø16/m, stair ledger). A horizontal label = bars running in x; vertical = in y. Two labels are written
  on a beam band and belong to the strip beside it, by eye (GF-134 x 6ø10/m, 1F-057 y 5ø10/m).
- **Notation**: 'n ø d/m' = n bars per metre run (T-155 evidence: the same set prints a count 'n ø d' and a spacing
  'ø d/s cm'). '(T&B)' = the same mesh top and bottom (2F tank panels 2F-011 7ø14/m x, 6ø14/m y; 2F-013 6ø12/m both).
- **Bar lines**: for each direction the bars are spread across the panel's full extent between beam faces (note 22 sets a
  minimum cover of 2.5 cm, so nothing is deducted and the bars run on into the beams); each bar line's length is its chord
  across the panel polygon (local length on the skewed and L-shaped panels, cut where an opening crosses it).
- **p.15 curtailment**: an end is continuous when another slab panel of the same sheet lies within 0.80 m beyond the face
  along the bar line (widest beam band 0.65 m, B26). At a continuous end 50 % of the bars stop 0.125 x L short of the face
  (L = the local clear run of that bar line); the other 50 % cross the beam (gap shared half to each panel). Stair zones,
  voids and dome openings are not slab beyond the beam: no curtailment there.
- **Development**: the extension of each bar beyond the faces (into edge beams to 40 mm of the far face per p.15, laps at
  supports) is not drawn with a length: HELD as note 9's 2 x 40 d .. 2 x 70 d per bar, never 0.

Re-measured by hand (three panels the checker can re-read):

| Panel | Clear sizes (T-139 register) | Label | A bars x length | B | Continuous ends (A) | p.15 A length | kg A |
|---|---|---|---|---|---|---|---|
| GF-098 x | 4.200 (x) x 3.700 (y) | 6ø10/m | ceil(6 x 3.70) = 23 x 4.20 = 96.60 m | 24 x 4.20 = 100.80 | 22 of 46 (east side, CB4) | 96.60 - 22 x 0.5 x 0.125 x 4.20 = 90.825 | 56.065 + crossing 0.702 |
| GF-098 y | | 7ø10/m | ceil(7 x 4.20) = 30 x 3.70 = 111.00 m | 31 x 3.70 = 114.70 | 26 of 60 (south side, B1) | 111.00 - 26 x 0.23125 = 104.988 | 64.807 + 0.986 |
| 1F-084 x ('T 16') | 4.300 x 4.850 | 8ø10/m | ceil(8 x 4.85) = 39 x 4.30 = 167.70 m | 40 x 4.30 = 172.00 | 54 of 78 | 153.188 | 94.560 + 2.801 |
| 1F-084 y | | 7ø10/m | ceil(7 x 4.30) = 31 x 4.85 = 150.35 m | 32 x 4.85 = 155.20 | 31 of 62 | 140.953 | 87.008 + 0.957 |
| 2F-011 x (tank, T&B) | 2.500 x 3.300 (column notch) | 7ø14/m (T&B) | ceil(7 x 3.30) = 24 x 2.50 (2 layers) | 25 | top layer face to face | 119.80 m both layers | 144.94 net (bottom layer curtailed) |

## 3. Top bars over the supports: two project drawings disagree (HELD, designer item)

- Sheet note 2 (p.4, p.5, p.6, paraphrase): top bars 5 ø 10 per metre over the beams, for a length of one third of the span,
  in both directions. It does not say whether that is the whole bar or the length on each side, nor which span.
- p.15 TYP. SLAB ON BEAMS DETAIL: top bars 0.30 x the larger of the two clear spans over a continuous support, 0.25 L1
  top anchor bars at a non-continuous support; p.15 note 3: the larger top steel where adjacent spans differ.
- Carried readings (kg, A .. B counts at 5 / m; crossings of continuous beams shown apart):
  reading i (1/3 span is the whole bar, L/6 each side) 752.73 .. 798.64; reading ii (L/3 from each face into each panel)
  1,505.46 .. 1,597.28; p.15 (0.30 max(L1, L2) / 0.25 L1) 1,507.04 .. 1,600.82; crossings 131.90 .. 141.87.
- Readings ii and p.15 agree to 0.2 %; reading i is half. The tank panels (T&B) carry a full top mesh; whether note 2 adds
  bars there is a separate HELD line (28.66 .. 70.61 kg).

## 4. Held lines and printed bars that are not a panel mesh (nothing dropped)

| Where | Printed | What | Status |
|---|---|---|---|
| GF-020 y, GF-076 x, 1F-041 y | '5ø10' without '/m' | 5 bars in all, or 5 per metre | HELD 7.89 .. 19.55 kg (designer item) |
| GF-126 (south part, by the round stair) | 6ø14/m, hooked west end | a second x bar, zone not delimited | HELD (designer item) |
| 1F-084 corners | 3ø14 x 4 (legend 'Corner Reinforcement') | 12 bars, length not printed | HELD |
| 8 dome corners, 4 pool-court bay corners, GF-146 wedge | none (p.4 / p.5 / p.7 / p.16 searched) | 4.537 m2 of slab with no bars printed | HELD (designer item) |
| every 16 cm panel parallel to a beam | p.15 temperature schedule | rows 100, 125, 150, 175 ... mm only; no 160 mm row | HELD (no interpolation) |
| GF-025 / GF-130 / 1F-016 | 8ø16/m | stair zones | stair ledger (T-111), not slab |
| CB6 / B7 / B4 joint (GF), B8 and B7 east ends (2F) | 3ø16/Top, 4ø16/Top, 5ø18/Top | hooked top bars of beams | beam lane (T-149) |
| GF south edge, 1F-023 | P.C 20x70 10ø16, P.C 20x50 8ø16 | planted columns | column ledger (T-148) |

## 5. Evidence for owner Q-71 (for the Lead; not a recommendation)

The frozen slab-rebar research PRE-S7.1 records a decision set "AD2" with authority "URBAN_OWNER_DECISION (AD2 + PRE-S7.1
brief)": AD2-D02 "N bars/m over W m = N x W equivalent bars, unrounded, no +1" (= Q-71 reading C) and AD2-D06 "1/3 x clear
span from the support face into the panel" (= note-2 reading ii). Neither appears in the owner decisions register or in
OWNER_QUESTIONS answers, so this ledger does not use them (same situation as the column-link claims T-148 found). On
Alsenan slabs the three count readings give 2,853.00 (C) / 2,915.09 (A) / 3,068.05 (B) kg of bottom mesh: A - C 62.09
(+2.2 %), B - C 215.05 (+7.5 %).

## 6. What we learned (every villa)

1. A slab sheet's general note can conflict with the typical slab detail of the same set (top-bar extent): record both,
   hold the line, ask the designer; never pick one.
2. The typical detail decides the bottom-bar population (50 % curtailed at continuous supports), which a plan label alone
   does not show: face to face uncurtailed is 3,044.31 kg against 2,830.28 kg curtailed inside the panels (+7.6 %) at A.
3. Continuity has to be read per bar line (a stair zone, a void or a dome opening beyond a beam is not a continuous slab).
4. On skewed panels reading B (bars on both edges) can give less steel than A: the edge lines run where the panel is
   narrow (GF-126 y: 92.54 vs 93.12 m). Count readings are not ordered on irregular panels.
5. A label written on a beam band belongs to the strip its bar line runs in (2 cases here).

## 7. Fixture (`--check`, NON-Alsenan, hand-calculated, all PASS)

Two panels 3.0 x 4.2 and 4.0 x 4.2 on a 0.20 m beam (6 ø 12/m: A 26 / B 27 bars, face 78.0 m, p.15 73.125 m, crossing
1.300 m, kg 66.156; Q-71 C 67.200 kg; top 21 lines: i 21.0 m, ii 42.0 m, p.15 40.95 m, crossing 2.1 m); mirror and 90-degree
rotation unchanged; mm-to-m unchanged; L-shaped panel (A 60.0 / B 64.0 m); panel with an opening (A 70.0 / B 76.0 m, the
opening edge is not a support); a label without '/m' kept HELD with both readings; an empty extent refused; an exact
multiple (5 / m x 4.2 m = 21, not 22).
