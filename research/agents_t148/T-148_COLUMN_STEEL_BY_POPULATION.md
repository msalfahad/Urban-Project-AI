# T-148 Alsenan column steel by bar population, per column and storey (lane S, gate 3; NO REPO CODE; a checked piece for V3.0)

Worker 1, 2026-10-21. Development villa, not an accuracy claim. Hand ledger only: `t148_column_steel.py` does the
arithmetic of a hand table typed from the drawings (it imports nothing from `engine/`), `T148_COLUMNS.csv` has one row
per column, storey and component (327 rows over the 59 columns of the T-119 ledger), `T148_SUMMARY.json` the totals.
Nothing released changes; nothing is wired.

## Sources read this run (Drive "Alsenan chalet project"; structural DXF sha 9f9d1179, structural PDF sha 74da1523 = manifest)

| What | Where | Read |
|---|---|---|
| Main bars per mark and storey | PDF p.9 "Schedule of Columns" (300 dpi), bands FOUNDATION / GROUND FLOOR / 1st floor / 2nd floor & Top | all bars ø 16; GF C / C1 / C2 8, C3 / C4 8, C5 / C6 / C10 10, C7 / C8 12, C9 / C11 14; 1F C1 / C3 6, C2 / C4 / C5 / C6 8, C7 10, C8 / C9 12; 2F C1-C5 6, C6 / C7 8, C8 / C9 10; C, C10, C11 struck above GF; CN foundation only (4 ø 14). Cross-check: the DXF-derived engine schedule join (S3.1) gives the same count for every GF / 1F / 2F occurrence of a scheduled mark (GF 286 bars both) |
| Links | p.9 "DETAILS OF COLUMN REINFORCEMENT": "ST. OF COLUMN- 6ø8/m" (DXF S-TEXT.D, same words); arrangement by L = long side: L <= 50 cm one closed link, 50 < L < 80 cm two overlapping links, 80 < L < 120 cm three links (DXF texts ' 50cm < L < 80cm', ' 80cm < L < 120cm'); 135-degree hooks drawn, no length; sheet N.T.S. | count notation per metre = owner Q-71 (open); L = 80 cm (C7 at GF and 1F) is in neither band |
| Turned columns | PDF p.15 "TYP. DETAIL OF TWISTED COLUMN" (two variants) | 4 ø 16 EXTRA over 1 M below + 1 M above the floor (two printed dimensions; bars drawn over both, short top bend without length); spiral stirrups 6 ø 8 / m over the same 2 m, circle diameter not dimensioned |
| Planted columns | PDF p.15 "BEAM CARRYING PLANTED COL. DETAIL"; p.4 / p.5 leaders (DXF S-TEXT-SLAB 'P.C 20x70', 'P.C 20x50' x2) | column bars drawn into the beam with a foot, crank 100 cm above the beam top; the 4 ø 16 belongs to the carrying beam; **no bar count printed anywhere for a planted column** (no P.C row in p.9) |
| Laps | PDF p.8 general note 9: development length not less than 70 d in tension zones, 40 d in compression zones | zone and splice position not printed -> 40 d .. 70 d range, HELD (as T-138 r2) |
| Cover | PDF p.8 general note 22: not less than 2.5 cm in columns | link path only |
| Heights | T-119 ledger (agents/task-T-119 444e943, sha256 93ae82ae...79fe6b), copied as `T148_T119_INPUT.csv` | interval, concrete height to the controlling member, D_ctrl, status |
| Freelancer | workbook "RC", sheet 1 row 19 "total walls and columns" | 39.75 m3, steel 7.95 t (= 200 kg/m3), sheet "walls + columns" rows 11-72 |

## Result: engine vs freelancer (Alsenan, column steel above the necks, kg, net)

Main bar length per storey = T-119 concrete height + D_ctrl (bars run through the joint) = the storey interval
(GF 4.50, 1F 4.20, 2F 4.20 m; asserted per column). kg = count x length x d^2/162 (ø 16 = 1.5802 kg/m).

| Storey | Columns | Hand NET RELEASED (main bars) | Hand NET HELD, defined | Unquantified main | Frozen engine S3.1 main core (research) | Route G provisional (all parts) | Freelancer |
|---|---|---|---|---|---|---|---|
| GF | 30 | **1,038.22** (15 cols) | 995.56 (15 cols) | - | 2,033.78 (= hand 2,033.78) | 2,889.18 (30 occ.) | lump, see below |
| 1F | 20 | **676.98** (12 cols) | 358.40 (6 cols) | 2 planted | 1,141.56 (hand defined 1,035.38: +106.19) | 1,727.04 (22 occ.) | |
| 2F | 9 | **159.29** (4 cols) | 185.84 (4 cols) | 1 planted | 398.22 (hand defined 345.13: +53.09) | 1,483.91 (22 occ.) | |
| Turned-column extra (p.15) | 2 | **12.64** (GF C8) | 12.64 (GF C9) | spirals | 4 ø 16 x 2 m provisional | | |
| **Total** | **59** | **1,887.13 kg** | **1,552.43 kg** | 3 planted columns | 3,573.56 main core | 6,100.13 | 7.95 t "walls + columns" lump |

HELD on top of net (ranges, never 0):

| Item | kg | Why held |
|---|---|---|
| Links 6 ø 8 / m over the concrete height, 55 columns | A 793.96 / B 829.41 / C 781.37 at the lower-bound path (exact for 1-link columns); drawn proportions A 946.94 / B 989.32 (information); B upper path 1,245.03 | count = owner Q-71 (A ceil, B A + 1, C fractional); overlapping-link lengths not printed (N.T.S.); hooks without length |
| Links of C7 at GF and 1F (L = 80 cm) | unquantified | link arrangement for L = 80 not in either printed band (rule gap) |
| Laps, note 9 | reading S (splice only where a bar runs over the 12 m stock: 8 GF-1F-2F stacks of 12.90 m, 1 lap per through bar) 52.59 .. 92.03; reading P (splice of every bar at every floor) 499.61 .. 874.32 (GF 289.25 .. 506.19, 1F 157.77 .. 276.10, 2F 52.59 .. 92.03) | zone (tension / compression) and splice position not printed |
| Planted columns P.C 20x70 / 20x50 (1F x2, 2F x1) | main bars, starters (crank 100 cm above the beam top, foot in the beam) unquantified | bar count not printed (no p.9 row; leaders print only the size) |
| Bar ends stopping at a roof (286 bar ends: count drops above, or top storey) | unquantified | anchorage / bend not drawn: BLOCKED_DETAILING |
| Section transitions (44: foundation 30 -> GF 20 / 25 wide, 25 -> 20 at 1F, length changes, two turns) | unquantified | crank / offset detail not printed |
| Links through the joints (6 / m x D_ctrl: 238.8 levels in all) | unquantified | whether links continue through the beam-column joint is not printed |
| Turned-column spirals (2) | unquantified; 12 / 13 / 12 turns (A / B / C) | spiral diameter not dimensioned; Q-71 |

What the held main bars wait on (main-bar kg = count x interval does NOT depend on D_ctrl):

| Cause (from T-119) | Columns | Main kg | Effect on the steel |
|---|---|---|---|
| Framing member held (CB2 / B21 / CB10 width conflicts, unlabelled pieces, unprinted depths) | 16 | 962.37 | none on the main bars (length = interval whatever D_ctrl is); only the link zone (height) depends on it. Held only because the task keeps every T-119 hold |
| Annex interval, owner Q-54 B (+0.30 / +4.30) | 7 | 412.45 (at 4.50 m) | real: bar length waits on the annex datum |
| C8 section conflict (p.1 30X80 vs schedule 90), designer D-16 | 2 | 164.98 (12 ø 16 as C8) | real: read as C7 the column has 12 (GF) / 10 (1F) bars |
| Planted column, bars not printed | 3 | not quantified | real: no count anywhere |

**Freelancer**: his column steel is inside one lump, "total walls and columns" 7.95 t on 39.75 m3 (lift walls 2.40 + necks
8.805 + GF 17.44 + 1F 7.73 + roof 3.38 m3), i.e. 200 kg/m3: a kg/m3 allowance, not a bar population. RULE_DIFFERENCE, no %
(URBAN-REBAR-NET-AND-PROCUREMENT@v1: never kg/m3). For orientation only: his allowance on his own columns above the necks
(28.547 m3) would be 5.71 t, against 3.44 t of main bars defined here plus 0.78 .. 1.25 t of links and 0.05 .. 0.87 t of
laps (held).

## What the hand reading found (verdict proposals for the checker)

1. **Main bars: the frozen engine research S3.1 equals the hand on every scheduled GF column** (2,033.78 kg, 286 bars at
   4.50 m): ENGINE_RIGHT on GF. Same length basis (storey interval, bars through the joint).
2. **S3.1 gives the three planted columns bars no drawing prints** (1F P.C 20x70 10 ø 16, 1F P.C 20x50 8 ø 16, 2F P.C 20x50
   8 ø 16; its register: `schedule_join` DUPLICATE_ROW, `schedule_row` null, MAIN_BARS VERIFIED): 172.56 kg released as
   verified with no source. Proposal: HELD (BARS_NOT_PRINTED), designer request. Hand check: (10 + 8 + 8) x 4.20 x 1.5802
   = 172.56 kg.
3. **S3.1 reads the 1F C8 conflict column as C7** (10 ø 16; p.1 prints 30X80) while it reads the GF one as C8: -13.27 kg
   (2 x 4.20 x 1.5802). T-119 holds both as CONFLICT (D-16): UNRESOLVED until the designer answers. 1F: +119.47 - 13.27
   = +106.19; 2F: +53.09 (planted only). Re-adds to 3,573.56 - 3,414.28 = 159.28.
4. **Link count**: the p.9 note is per metre, so the count is owner Q-71 (open). S3.1 releases its ties as LOWER_BOUND
   under "URBAN_OWNER_RULE (S3.1 §22B: an explicit '/m' count is a rate per metre)" with ceil(rate x zone), and two
   PROJECT_ONLY owner claims dated 2026-10-06 in research/alsenan_column_rebar_s3_1/ALSENAN_COLUMN_PROJECT_CLAIMS.json:
   ALS-S3-CLAIM-001 "6ø8/m = six complete tie levels (sets) per metre" and ALS-S3-CLAIM-002 "L exactly 80 cm uses the
   3-link arrangement". None of the three is in the Urban registers (rules/, knowledge/, OWNER_DECISIONS_REGISTER,
   OWNER_QUESTIONS Answered), so this ledger holds them; **for the Lead**: these owner statements may already answer
   Q-71 for column links (reading A, sets per metre) and the L = 80 gap; worth putting to the owner with Q-71.
5. **The p.9 details draw fewer bars than the schedule prints**: the L <= 50 detail draws 4 corner bars and one link,
   while 20 x 50 columns carry 6 or 8 ø 16 (the 50 < L < 80 detail draws 8 bars; GF C5 / C6 / C10 carry 10). The printed
   count governs (UP-KB-PREC-001); the restraint of intermediate bars is a designer observation, no quantity change.
6. **Minimum thickness table vs schedule**: the p.9 table asks T min 25 cm for 4.3 <= H <= 4.7 m; the GF interval is 4.50
   m but GF C / C1 / C2 are 20 cm wide in the schedule. Designer observation (concrete and steel follow the schedule).
7. **Turned columns** (GF C9 COL-GF-09, GF C8 COL-GF-13, p.4 T.C): the p.15 extra 4 ø 16 x 2.00 m = 12.642 kg each is
   printed and dimensioned; released on C8, held on C9 only because T-119 holds that column (B21 width conflict, D_ctrl
   unchanged). The spiral is unquantified (diameter not dimensioned).
8. **Freelancer**: RULE_DIFFERENCE (kg/m3 lump with walls and necks); never copied.

## Owner manual method and drawing-derived method side by side

| | Owner / Urban manual method (this ledger) | Drawing-derived engine (frozen S3.1) | Route G (provisional) |
|---|---|---|---|
| Count | as printed in p.9 per storey; planted columns HELD (not printed) | as printed; planted columns get a same-size row (DUPLICATE_ROW) | schedule main bars + tie note |
| Main bar length | storey interval = T-119 height + D_ctrl (through the joint) | storey interval (same) | profile heights |
| Laps | note 9, 40 d .. 70 d, HELD; splice position not printed: reading S (stock only) and reading P (every floor) | 40 d PROVISIONAL, 70 d alternative | convention |
| Links count | 6 / m over the concrete height, readings A / B / C, HELD (Q-71) | ceil(rate x clear zone), LOWER_BOUND, "owner rule §22B" | (n / m x L + 1) |
| Links length | 1 link: exact core path (cover 2.5 cm, note 22); 2 / 3 overlapping links: lower bound, upper bound, drawn proportion as information | outer perimeter x levels (lower bound) | model |
| L = 80 cm | HELD (rule gap) | 3 links (project claim 002) | - |
| Hooks, bends, transitions | BLOCKED_DETAILING, unquantified | provisional hooks; transitions BLOCKED | convention |
| Mass | d^2 / 162 | d^2 / 162 | d^2 / 162 |

## Three columns for the checker (re-count on p.9 and p.15)

| Column | Schedule (p.9) | Main bars net | Links (Q-71) | Other |
|---|---|---|---|---|
| COL-GF-19 GF C11 (dead column, p.4 D.C) | 25 x 110, 14 ø 16; struck above GF | 14 x 4.50 x 1.5802 = 99.556 kg RELEASED | 3 links (80 < 110 < 120); height 3.65: A 22 / B 23 / C 21.90 levels; lower path 2 x 1.042 + 6 x 0.192 = 3.236 m | all 14 bar ends stop at the GF roof (anchorage not drawn) |
| COL-1F-41 1F C9 | 20 x 90, 12 ø 16 (GF below 14, 2F above 10) | 12 x 4.20 x 1.5802 = 79.644 kg RELEASED | 3 links; height 3.45: A 21 / B 22 / C 20.70; lower path 2.536 m: A 21.039 kg | lap 12 x 0.64 .. 1.12 m = 12.136 .. 21.239 kg; 2 bar ends stop at the 1F roof; transition 25 x 100 -> 20 x 90 |
| COL-GF-13 GF C8 (turned, p.4 T.C) | 25 x 90, 12 ø 16 | 12 x 4.50 x 1.5802 = 85.333 kg RELEASED | 3 links; height 3.65: A 22 / B 23 / C 21.90; lower path 2.836 m | p.15 extra 4 x 2.00 x 1.5802 = 12.642 kg RELEASED; spiral HELD |

## Non-Alsenan hand fixture (asserted by the script)

Column "K2", three storeys, 30 x 60 / 30 x 60 / 25 x 45, 8 ø 20 / 6 ø 20 / 4 ø 16, intervals 3.60 / 3.30 / 3.30, D_ctrl 0.60 /
0.50 / 0.45: main 71.111 / 48.889 / 20.859 kg (n x interval x d^2/162; independent of D_ctrl); storey-2 lap 11.852 .. 20.741
kg; run 10.20 m < 12 m: no stock lap; 30 x 60 -> 2 overlapping links, lower 2 x 0.542 + 4 x 0.242 m; 25 x 45 -> 1 link 1.168 m,
height 2.85 m -> A 18 / B 19 / C 17.1, A 8.306 kg (HELD). Adversarial: rotation / mirror (60 x 30 = 30 x 60), units (mm
typed once), L = 80 cm boundary -> no band (HELD), mark with no schedule row -> HELD never 0, exact multiple 6 / m x 3.00
m = 18 levels (no float overshoot).

## Not done / uncertain

- Necks (foundation band of p.9, 30 x .. with the GF counts) are outside this task: their height is held (owner Q-21 C);
  the GF lap reading P is listed, the neck bars are not.
- Engine figures are read from the frozen research registers (S3.1, route G default run), not re-run.
- Heights and statuses come from T-119 (READY, not merged); if the checker changes a T-119 row, re-run the script with
  `--t119 <csv>`.
- Designer requests for the Lead: planted-column bars (count, starter leg / foot / crank), L = 80 link arrangement,
  overlapping-link lengths, hook / bend lengths, section transitions, spiral diameter; D-16 (C8) unchanged.
