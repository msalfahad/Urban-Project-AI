# T-191 Swimming-pool reinforcement rev2, by bar mark, on the VERIFIED pool structure (Alsenan development villa; rules for every villa)

Worker 1 (structural lane S), 2026-10-23. Development villa, not an accuracy claim. Research only: nothing is wired,
nothing is released, the released default (V2.9 + route G) is unchanged; T-166 (rev1) and T-183 stay as merged. A
piece for lane I once the Checker has re-counted it. ENGINEERING_REASONING_STANDARD.md sections 2, 3 (notation meaning
before arithmetic, bar shapes from the detail, unit mass from the rule in force), 4 and 7 applied.

Sources (Drive "Alsenan chalet project", private copy in the git-excluded folder, never committed): `ST7757.pdf`
(sha256 74da1523...) **p.7 DETAIL OF SWIMMING POOL (N.I.S.)**, read at 100 / 300 dpi this run: the section labels AND
the exploded bar views drawn under the section (not used by rev1 or T-183); **p.8 note 9** (development / tie length of
starter bars not less than 70 d in tension zones, 40 d in compression zones) and **note 22** (cover not less than 2.5 cm
in columns, beams and slabs and 7 cm in concrete in contact with soil; walls are not listed). Geometry and levels are
the Checker-merged T-183 r2 ledger (cited, not re-derived): outer D back 3.50, sides 1.75, half circle r 1.75; walls
0.20; base 0.40; rim +0.30, structure line -0.90 -> **wall 1.20 m above the base top**; finished floor -0.85 (1.15 is
the finished depth). Owner Q-26 A (flat floor: the sloped-zone bars of p.7 are not used). Unit mass: project method
D2_OVER_162 (authority URBAN_OWNER_RULE, as every merged Alsenan steel ledger, e.g. the S3.1 column summary), through
`engine/source/rebar_unit_mass.py`; exact 7,850 kg/m3 as a check.

Code: `t191_pool_steel.py` (new, unwired; `--check`, `ledger INPUT.json`), `t191_report.py` (per-mark rev1 -> rev2
delta; writes `T191_STEEL.csv`, `T191_SUMMARY.json`), input `ALSENAN_POOL_STEEL_INPUT.json`, tests
`tests/t191_pool_steel/` (20 + 10 r2 pass, synthetic, not Alsenan, plus one regression on the printed-only input).

## 1. Result in engineering terms (kg; the line stays HELD)

| Population (p.7 zone) | Rev1 T-166 A / B | T-183 r2 face-to-face C .. B | **Rev2 net, bar by bar (low .. high)** | Held apart (never 0) |
|---|---|---|---|---|
| R1 deep-end detail | 900.01 / 927.54 | 860.97 .. 894.43 | **824.89 .. 883.59** (exact density 823.89 .. 882.52; R2 571.76 .. 617.22) | outer-vertical floor legs 84 x ø14 (length not dimensioned; drawn minimum 11.89 kg); ring laps 19.07 .. 42.15 kg (procurement) |
| R2 shallow-end detail | 620.13 / 639.45 | 596.17 .. 616.66 | **572.45 .. 617.96** | floor legs 72 x ø12 (minimum 7.55 kg); ring laps 12.26 .. 23.23 kg |

Which population governs a flat pool is the designer item D-57 / C1 (never chosen here): the pool steel line is HELD
on **572.45 .. 883.59 kg net** across both details, on the verified 1.20 m wall, with legs and laps listed apart.
Change against rev1: R1 -75.12 .. -16.42 kg (-8.3 .. -1.8 %), R2 -47.68 .. -2.17 kg (-7.7 .. -0.3 %).
r2 (D-T191-2, Checker 03:58): the base mats carry the count range A .. B (below); this moved only the LOW ends,
R1 839.34 -> 824.89 (-14.45 kg), R2 583.08 -> 572.45 (-10.63 kg); the high ends are unchanged.

What the range is made of (and nothing else): the non-soil cover (water face, wall top, base top) is not printed for a
pool wall (note 22 lists columns, beams, slabs and soil faces) and is bounded by the cage fit 0 .. 0.080 m (R1) /
0 .. 0.086 m (R2) = wall 0.20 - soil cover 0.07 - the four wall bar diameters; the hoop end positions are not
dimensioned (6 .. 7 hoops per face on 1.20 m at <= 0.20; the high end carries 7, HIGH_FROM_COUNT_B); the base-mat
count meaning of '/m' is not fixed by the pool's own drawing (count A density .. B maximum spacing, section 2a). The plan
direction of the main floor bars is not marked: both assignments were computed and give the same kg on this outline
(the D at the bar ends has r = b = 1.666 m).

Freelancer: pool steel 1,500 kg as one allowance on 12.348 m3 (121.5 kg/m3), including a pump room that no drawing
shows: **RULE_DIFFERENCE** (allowance per m3, scope not drawn), no %. Engine (released): no pool steel line (route G
holds none; V3.0.5 holds the 21 rev1 lines BLOCKED): nothing to compare.

## 2. The physical element and what p.7 prints (re-read this run)

Two-curtain RC wall on an RC base with two mats, D-shaped, closed all round. The section prints per zone; the bar views
under it give the shapes:

| Mark | R1 deep end | R2 shallow end | Shape (bar view under the section) | Count rule (r2: '/m' meaning per element, section 2a) |
|---|---|---|---|---|
| WV_OUT outer-face verticals | 7ø14/m | 6ø12/m | **L**: vertical + a leg along the base bottom (leg NOT dimensioned) | closed loop N = ceil(P_bar / s) (both meanings agree) |
| WV_IN water-face verticals | 7ø12/m | 6ø12/m | **hook over the wall top** to the outer bar line + **closed box in the base** (bottom leg, one leg up to the top mat, top leg back) | closed loop |
| WH_OUT outer hoops | "12/20cm" (ø not printed; read ø12 as the water-face label of the same wall) | ø10/20cm | closed ring, inside the verticals (dots drawn inside the vertical line) | 6 .. 7 over the 1.20 m wall above the base top (R-POOL-6) |
| WH_IN water hoops | ø12/20cm | ø10/20cm | closed ring, inside the verticals | 6 .. 7 |
| F_MAIN base top + bottom | 7ø14/m | 6ø12/m | straight, ends inside the outer verticals | open run: HELD range A = ceil(n x L_eff) .. B = ceil(L_eff / s) + 1 |
| F_DIST base top + bottom (dot rows, X leader to both mats) | 6ø14/m | 6ø12/m | straight | idem |
| RIM wall top | 3ø16 | none printed | rings, spread across the wall between the bar lines | printed count, never re-counted |
| CORNER base / wall | 3ø16 | 4ø16 | rings | printed count |

Rev1 read R2's water-face bars as "one U bar over the top, both faces": the bar view does not support it; R2 has the
same topology as R1 (outer L, inner hook + box), only the diameters and rates differ. Corrected here.

### 2a. The '/m' meaning on the pool base (r2, D-T191-2)

ERS s.3: a notation's meaning is established per element type. T-171 (merged) proved '/m' = maximum c/c spacing for
the FOOTING schedule only; the merged Gate B slab / stair steel (T-179) carries every open '/m' mesh as a count range.
Searched for the pool's own evidence (ST7757.pdf p.7 at 110 dpi this run, p.8 notes 1-24): no spacing dimension on the
base mats, no edge-bar position, no note that defines '/m'. p.7 uses two notations side by side ('n ø d/m' on the pool,
'ø12MM/15cm' on the dome), which shows that the set distinguishes a rate from a printed spacing, not which count the
rate means at the mat edges. So the base mats carry A (density: n bars per metre of the c/c spread L_eff, ceil(n x
L_eff)) .. B (maximum spacing: ceil(L_eff / s) + 1); low end on A, high end on B. A density count on the bar-end
extent (L_eff + d) lies inside A .. B because n d < 1. Walls are closed loops (ceil(n P) = ceil(P / s)): unaffected;
hoops print a spacing ('/20cm') and keep their own 6 .. 7 range.

| Mark (R1, on the bar-end outline 0.084 m inside, L_eff 3.318 m both ways) | A | B | kg A .. B per mat |
|---|---|---|---|
| F_MAIN 7ø14/m (7 x 3.318 = 23.23) | 24 | 25 | 84.902 .. 88.513 |
| F_DIST 6ø14/m (6 x 3.318 = 19.91) | 20 | 21 | 70.451 .. 74.065 |
| R2 F_MAIN / F_DIST 6ø12/m (bar-end outline 0.082 m inside, L_eff 3.324: 19.94) | 20 | 21 | 51.794 .. 54.452 |

x top + bottom: R1 low end -2 x (3.611 + 3.614) = -14.45 kg; R2 -4 x 2.658 = -10.63 kg.

Bar lines (centrelines): outer verticals at c_s + d/2 = 0.077 m (R1) inside the outer face (soil cover 7 cm, note 22);
hoops inside the verticals; water-face verticals at c_n + d/2 from the water face; verticals run from the bottom mat
(c_s + d/2 above the base underside) to c_n + d/2 below the rim: **length = 0.40 + 1.20 - 0.07 - c_n - d**. The 0.15 m
upstand above the deck is wall concrete already inside rim - base top (R-POOL-8): no extra bar, its height is in the
1.20. The curved ring is measured in full: inward offsets keep the arc centre, so P(t) = 12.497787 - (4 + pi) t.

## 3. Hand re-count for the Checker (one wall population, from p.7 and T-183 r2's geometry)

R1 outer-face verticals 7ø14/m: P_bar = 12.497787 - 7.141593 x (0.07 + 0.007) = 11.947884 m; N = ceil(11.947884 x 7 =
83.635) = **84** (rev1 88 on the concrete face 12.4978). Length at c_n = 0: 1.60 - 0.07 - 0.014 = 1.516 m; 84 x 1.516 =
127.344 m x 1.209877 kg/m = **154.07 kg**; at c_n = 0.080: 1.436 m, 145.94 kg. Floor leg HELD (84 legs, drawn minimum
across the wall 0.117 m each).
Also re-countable: R1 water verticals at c_n = 0: P = 12.497787 - 7.141593 x 0.194 = 11.112318, N = ceil(77.79) = 78;
bar = 1.518 + hook 0.117 + box 2 x 0.117 + 0.318 = 2.187 m; 78 x 2.187 x 0.888889 = 151.63 kg.

## 4. Delta rev1 -> rev2 per mark (kg; low .. high), the cause of each step

S1 = verified height only (verticals 1.55 -> 1.60 m base underside to rim; hoops over the 1.20 m wall instead of
0.40 + 1.15); S2 = bar centrelines at the covers + the counting meaning (loops ceil(P/s), base mats count A .. B); S3 = drawn
shapes (hook + box). Full table in `T191_STEEL.csv`.

| R1 mark | Rev1 A | S1 height | S2 bar lines / counts | **S3 rev2** | Main cause |
|---|---|---|---|---|---|
| WV_OUT 7ø14/m | 165.03 | 170.35 | 145.94 .. 154.07 | **145.94 .. 154.07** | +0.05 m build-up (+5.32); 88 -> 84 bars on the bar line and covers (-24.41 .. -16.28) |
| WV_IN 7ø12/m | 107.47 | 110.93 | 104.81 .. 105.25 | **130.25 .. 151.63** | drawn hook + box in the base (+25.44 .. +46.38) |
| WH_OUT ø12/20 | 88.87 | 66.66 .. 77.76 | 63.23 .. 73.77 | **63.23 .. 73.77** | 8 hoops over 1.55 -> 6 .. 7 over 1.20 (-22.22 .. -11.11) |
| WH_IN ø12/20 | 78.72 | 59.04 .. 68.88 | 62.77 .. 69.68 | **62.77 .. 69.68** | idem; ring on the bar line outside the water face (+3.73 .. +0.80) |
| FB / FT MAIN 7ø14/m (each) | 94.61 | 94.61 | 84.90 .. 88.51 | **84.90 .. 88.51** | chords to the bar ends inside the outer verticals (0.084 m) instead of face to face; count A 24 .. B 25 |
| FB / FT DIST 6ø14/m (each) | 79.50 | 79.50 | 70.45 .. 74.07 | **70.45 .. 74.07** | idem; count A 20 .. B 21 |
| RIM / CORNER 3ø16 (each) | 55.86 | 55.86 | 54.64 .. 56.00 | **54.64 .. 56.00** | rings on their own positions instead of the wall centreline |
| **Total** | **900.01** | **866.91 .. 887.86** | **799.46 .. 837.20** | **824.89 .. 883.59** | |

R2: 620.13 -> S1 597.35 .. 611.89 -> S2 551.75 .. 577.94 -> **572.45 .. 617.96** (WV_IN hook + box +20.70 .. +40.02;
WV_OUT 75 -> 72 bars; hoops 8 -> 6 .. 7).
Against T-183 r2 section 3 (face-to-face, straight bars): the difference is S2 + S3 above; T-183's net-of-7-cm column
(R1 812.63 .. 850.15) had the covers but not the shapes.

## 5. Held items and designer list (nothing for the owner: standard 2.7 not met)

| Item | Status | Quantity kept |
|---|---|---|
| Which population governs a flat pool (C1 / D-57) | HELD_DESIGNER | R1 and R2 side by side |
| Non-soil cover of the pool wall / base top (note 22 lists no walls) | HELD, bounded by the cage fit | in the range |
| Hoop end positions | HELD count 6 .. 7 per face | in the range (high carries 7) |
| Base-mat count meaning of '/m' (no pool evidence; T-171 is footings only) | HELD count A .. B | in the range (low A, high B) |
| Outer-vertical floor legs (L shape, length not dimensioned) | HELD_LENGTH | R1 84 x ø14, R2 72 x ø12; drawn minimum 11.89 / 7.55 kg, no upper value |
| Ring laps: every ring is a closed loop and needs at least one closing lap; rings on the bar lines are 11.20 .. 11.88 m, so 1 or 2 pieces depending on the lap; lap 40 d .. 70 d (note 9; tension / compression zone not printed) | HELD_LAP, procurement only | R1 19.07 .. 42.15 kg, R2 12.26 .. 23.23 kg, never in the net |
| Soil cover behind membrane + screed (C3): does note 22's 7 cm apply? | consultant | information: at 0 cm (face to face) R1 891.39 .. 956.79, R2 618.64 .. 671.45 kg |
| Outer hoop label printed "12/20cm" without ø | read ø12 (same wall's water face prints ø12/20cm) | designer confirm |
| Sloped-zone bars (6ø14/m, 6ø12/m, cranked bars) | not used (Q-26 A flat) | none |

## 6. General rule (proposed; scope every villa, closed RC ring walls: pools, tanks, pits; provenance T-191; adoption = a NEW rule version)

R-POOL-9 POOL / TANK STEEL BY BAR MARK. (a) Counts from the notation meaning, established per element type (r2): a
bar set round a closed wall is N = ceil(P_bar / s) (no '+1'; density and maximum-spacing readings agree); an open
'/m' mesh carries A = ceil(n x L_eff) .. B = ceil(L_eff / s) + 1 (low end A, high end B) unless the element's own
drawing fixes the meaning, cited; hoops over a height whose end positions are not dimensioned are a held range
[ceil(H/s), ceil(H/s) + 1], the high end carrying the high count; printed counts are never re-counted. (b) Lengths on
bar centrelines at the printed covers; an unprinted cover is a bounded range from the cage fit, never a borrowed value.
(c) Shapes from the detail's bar views: legs fixed by the element's own dimensions are measured, an undimensioned leg
is HELD_LENGTH with its count, never a guessed extent. (d) Verticals run base underside to the rim, the wall height
being R-POOL-4 r2's structural height. (e) Every closed ring carries at least one closing lap (procurement, from the lap
note), never inside the net and never 0. (f) Unit mass from the project's method.

## 7. Verdict proposals (POOL steel, kg)

- Rev1 (T-166) pool rows: superseded on the verified geometry (height, counts on bar lines, shapes): replace by rev2,
  line HELD (D-57). Lane I: carry per mark with low / high and the held legs / laps as separate HELD items.
- Freelancer 1,500 kg: RULE_DIFFERENCE (kg/m3 allowance, undrawn pump room), not scored.
- Released engine: no pool steel line: nothing to score.

## 8. Lessons-register row (proposed for ENGINEERING_REASONING_STANDARD section 7)

| 2026-10-23 | Pool steel rev1 900.01 kg (R1) vs rev2 824.89 .. 883.59 kg (T-191 r2) | Bars measured as straight sticks on the CONCRETE face (verticals 1.55 m, hoops "12.50 m > 12 m, one lap") while the detail's own bar views draw a hook + closed box on the water-face bars and an L leg on the outer bars, and the bars sit on centrelines inside the covers (rings 11.20 .. 11.88 m) | R-POOL-9: read the bar views before measuring; lengths on bar centrelines at printed covers, unprinted cover bounded by the cage fit; undimensioned legs HELD; closed rings always carry a closing lap (procurement); counts by the notation meaning (any villa: pools, tanks, pits, ring walls) | tests/t191_pool_steel (normal: round-ended pool in mm by hand; adverse: finished depth as wall height refused, high end with the low count, exact division, leg turned into a number, lap inside the net) | READY, Checker to re-count |

r2: the D-T191-2 row (pool base mats counted only at max spacing + 1) is already in ERS s.7 (Lead 04:20, status
'rework'); its regression test is now `tests/t191_pool_steel/test_mesh_count_r2.py` (normal: stadium / rectangle mesh
A .. B by hand; adverse: open mesh A != B with low on A and high on B, exact division still A != B, the footing meaning
fixed without this element's evidence REFUSED, unknown meaning refused; closed loop where both meanings agree):
proposed status 'fixed in T-191 r2, Checker to confirm'.
