# T-289 Structural basis ledger: the candidate lines that rest on unprinted depths / heights

Worker 1 (lane S), 2026-10-25, run session_01MUK5qLSecwWiqUoJ5KMGKL. Research piece: no engine, candidate or released
line changed, no V2 record written; lane I applies it (T-254 / T-266), the Checker issues the downgrade records
(T-245 (f)). ERS read; s.2.1 - 2.6, s.3, s.4 applied.

## 1. Run and identity

Own run, Python 3.11.17, Drive copies 'ST7757 dxf.dxf' (`9f9d1179`) and P7757.dxf from P7757_DXF_COMPRESSED.zip
(`ab54dd55`): research/agents_t167/v304_run.py (V3.0.4 csv `d86de34a` reproduced) then research/agents_t270/v3015_run.py:
**V3_0_15_BOQ_LINES.csv `a4dc01dd`, json `e54cae74` = the T-270 r2 Gate B files** (3,699 lines). Project id
'ST7757 villa (structural set)', revision set `297e913d...` on every ledger row (one project, one revision set, one
candidate). Extract: `python3 -I research/agents_t289/t289_extract.py <run>/v3015 <ST7757 dxf.dxf> --svg
<run>/structural/overlays/SH08_GROUND_BEAM_PLAN_GROUND.svg --out research/agents_t289` (byte-identical on re-run:
CANDIDATE `4952568d`, PAIRING `34412f1a`); ledger: `python3 -I research/agents_t289/t289_alsenan.py --write`
(BASIS_LEDGER_T289.csv `af7cea5a`).

## 2. The four named totals, line id by line id (residual 0.000 m3 each)

| Named total | Lines (item code + element id) | Sum of line ids | Residual |
|---|---|---|---|
| 24 exterior ground beams | 24 STR.CONC.GROUND_BEAM, element P-C:GROUND_BEAMS:GROUND:BANDnnnn[.k] with side OUTSIDE | 11.934579 | -0.000021 (named 11.9346 is rounded) |
| 2F columns | 8 STR.CONC.COLUMN floor 2F (PC-2F is BLOCKED in the candidate, no quantity) | 3.528000 | 0.000000 |
| 7 annex columns | 7 STR.CONC.COLUMN GF bound to T-248 GFRS 34A / 34D / 356 / 350 / 353 / 35F / 365 | 3.712500 | 0.000000 |
| ST-03 | 1 STR.CONC.STAIR L-061e18cf35a4b6b33d68 | 0.948267 | 0.000000 |
| **found here**: main exterior runs inside 'interior' lines | 3 STR.CONC.GROUND_BEAM BAND0006.2 / BAND0005.1 / BAND0043 | 1.830623 | 0.000000 (pinned) |

Binding: ground beams by engine band id -> T-242 run (face-line handle pair) through the run's own SH08 overlay,
registered on the face lines by edge voting (1 : 0.02953 px/mm, 133 edge votes; every straight band paired with its
overlap, arcs by centre); columns by sheet + mark + storey + position after one modal frame translation between the
candidate and the T-248 register (dx 75 968, dy 14 448 mm, 29 votes; every binding within 2 mm, one member each).

## 3. Per line: what the drawings print and what the line becomes

PHYSICAL ELEMENT. A ground beam is the concrete between its drawn faces from its printed soffit to its printed top; a
column from the top of the member under it to the soffit of the member over it; a flight's riser and waist are printed
or HELD.

| Group | Lines | Engine m3 | Engine basis | Printed for these elements | Ledger |
|---|---|---|---|---|---|
| Main-house exterior (14 T-253 runs) | 13 | 6.3336 | net plan x INTERIOR class depth 0.30 / 0.40 / 0.60 ('perimeter band, no architectural wall evidence': CONVENTION_ONLY) | ST p.13 exterior section: top 'Ground Floor slab level' (+0.95, T-214), underside 'Outer Normal ground level' = +-0.00 (T-253 s.2, five readings) -> D 0.95 printed by two levels of the element | **12.4296 DRAWING-CONFIRMED** (runs face to face x 0.95, merged T-242 / T-253; +6.0960 m3) |
| Main-house exterior in lines the engine typed interior | 3 | 1.8306 | the same interior class depth (no outside side found by the route) | as above (109+7CB#2, 145+7CA#1, ring ARC:157+158) | **3.5304 DRAWING-CONFIRMED** (+1.6998 m3); ring end closure +0.67 % still open in T-254 (ii) |
| Annex exterior (9 runs) | 8 | 4.9740 | interior class depth; 4 annex bands drawn through their supports (1.5 / 6.4 / 3.1 / 10.125 m vs face to face 1.2 / 6.0 / 2.4 / 9.70) | 'FOLLOW ARCH.' from +0.25 to +-0.00 gives 0.25 m, which cannot hold the printed exterior section (three bar zones) | **CONFLICT, blank** (D-35 annex; the literal 0.25 reading 2.2280 m3 is shown, never adopted) |
| Court (3 runs) | 3 | 0.6270 | interior class depth | no printed section for a beam with outside ground on both sides / GS-16 undecided | **HELD, blank**, range 0.627 .. 1.410 (T-253 s.4) |
| 2F columns | 8 | 3.5280 | B x H x storey height 4.20 (FFL +9.70 to the FINISHED roof +13.90) | base +9.65 (T-214, DRAWING-CONFIRMED); only the finished +13.90 printed for the top, no roof slab level, no build-up (D-39); tank columns 40F / 424 also D-44 | **HELD, blank**: <= 2.805 on 6 lines, 2 open (T-248) |
| Annex columns 34A / 34D / 356 / 350 / 353 | 5 | 2.4750 | 4.50 m (profile storey) | base +0.25 (T-214); annex roof prints only the finished +4.30 (Q-54 B answered B, D-39) | **HELD, blank**: <= 2.2275, no low end (T-248) |
| CB5 columns 35F (C5) / 365 (C3) | 2 | 1.2375 | 4.50 m | T-287 G1 (READY, not merged): base +0.25, h 5.20 -> 1.4300 proposed | **PENDING-VERIFICATION, blank** (T-248 range 1.2375 .. 1.4300 HELD); carried only after the T-287 verdict |
| ST-03 entrance flight | 1 | 0.9483 | straight_flight(5, riser 0.165, going 0.30, width 2.80, waist 0.175): both conventions | 5 risers over 0.85 m (0.170 drawn), run 1.20 m; no waist printed (T-187 / T-258, S-9) | **HELD, blank**; steps 0.355017 DRAWING-CONFIRMED component (T-258) |

Contractual view (owner 23:53 (f) / 23:57 (f2)): the 43 lines carry 21.9540 m3 (20.1234 named + 1.8306 found).
The main-house exterior lines, 8.1642 m3 at the interior depth (13 + 3 lines), re-base to **15.9600 m3
DRAWING-CONFIRMED** (16 runs + ring, = T-253 s.2 exactly; +7.7958 m3, +95.5 %); the rest goes BLANK: annex beams
4.9740 CONFLICT, court 0.6270 HELD, 2F columns 3.5280 HELD, annex columns 2.4750 HELD + 1.2375 PENDING, ST-03 0.9483
HELD. Nothing becomes 0.

## 4. Cross-trade lines that read the same depth / height (named, not changed)

- V3.0.15 has **no formwork line** for any of these members and **no ground-beam reinforcement line** on the 24 + 3
  bands at the GROUND storey (the BAND0002 / BAND0003 / BAND0019 bar lines are FOUNDATION-sheet bands, other members).
- 30 column reinforcement lines (MAIN / TIES of the 15 columns above) are NOT_APPLICABLE_WITH_EVIDENCE: no quantity
  rests on the heights; when bars are taken off they must use the column height of this ledger (HELD here).
- WP.FOUNDATION.BURIED_LIQUID L-8a3c318c960e271efee1 (45.4682 m2) and its HELD line L-eba4599c26b0d24de873: face
  heights D - 0.10 with D from T-253 (0.95), not from the candidate's interior depth: consistent with this ledger.

## 5. Verdict proposals (for the Checker)

- 24 + 3 exterior / perimeter beam lines at the interior depth: **ENGINE_WRONG basis** (depth not printed for the
  interior classes on an exterior run); main house **ENGINE_RIGHT on nothing but plan length** (13 / 16 lines: band
  drawn = face to face); annex lengths through supports = a second engine error, moot while CONFLICT.
- 2F / annex columns at the profile storey height to finished levels: **ENGINE_WRONG basis** (FINISHED_AS_STRUCTURAL).
- ST-03: **ENGINE_WRONG basis** (convention riser and waist), steps component right on the drawing.
- Checker re-derive (two lines from the sheets): exterior beam **L-e9a885323ad6ec3ea32b** (BAND0011.3 = run 7D0+FC#3:
  LINE 7D0 / FC face to face 6.35 m x 0.30 x 0.95 = 1.8097 m3 vs engine 1.1430); 2F column **L-d79d17d14f39d5148cb8**
  (SFRS:421 C1 0.30 x 0.30 on +9.65; top: only the finished +13.90 printed on section A-A -> HELD <= 0.425, engine 0.42
  at 4.20 m to the finished roof).

## 6. Rule, test, lesson

Rule (research, every villa; provenance T-242 / T-248 / T-253 / T-289): a basis ledger row is DRAWING-DERIVED only on
a depth / level printed for that element (or its own class), carries its sheet, and its group's line ids sum to the
named total within 0.0005 m3; a borrowed depth, a 0 depth, a column end at a finished level, a HELD row without its
item, a value from an unmerged task, two projects / revision sets are refused (`basis_ledger.py`).
Tests: tests/t289_basis_ledger (villa M hand fixture: printed class depth 0.432 m3, exterior depth from two printed
levels 1.200 m3, column to a printed soffit 0.315 m3 NORMAL; ADVERSE unprinted depth HELD blank, neighbour depth / 0
depth / item-less HELD refused, line-id sum 1.600 vs 1.512 refused, column to a finished roof / from an FFL refused,
unmerged value PENDING blank, mirror order invariant, unit slip refused; Alsenan pins).
Lessons row (proposed): 2026-10-25 | The 24 'exterior' beam lines the owner's (f) rule names are not the exterior set:
3 main-house exterior runs (1.8306 m3 at interior depth) sit in lines typed interior, and the 24 hold annex and court
runs of other classes | The total was named from the engine's own side test (OUTSIDE), not from the drawn runs | A
correction list is built run by run from the drawing-side class of every member (T-242 / T-253 runs), then bound to
the candidate's line ids; a list taken from the engine's own flag is checked for members the flag missed (any villa,
any trade) | tests/t289 (24 + 3, 15.9600 = T-253) | OPEN (T-289 READY).

## 7. What is missing

ST-03 included (not left to T-266); ring end rule (T-254 (ii)) and the 107+7CE stub (T-254 (i)) are lane I items; the
CB5 columns wait on T-287; D-35 annex, the court section / GS-16, D-39, Q-54 B, D-44 are the designer items holding
the blanks. No accuracy claim.
