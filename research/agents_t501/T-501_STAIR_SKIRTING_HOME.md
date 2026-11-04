# T-501: home of the stair skirting pieces (B7-07 / B7-08) and the 1F shaft binding (development villa; method every villa)

Worker 1 (stream F, non-candidate), 2026-11-04. Research only: `research/agents_t501/*`, `tests/t501_stair_skirting_home/*`
(+ CODEMAP); no engine, rule, knowledge, registry, method or candidate file touched; no candidate quantity moves (the
line proposal in section 5 is for the stream F integrator). ERS 2026-10-22 applied: s.2.1 element first, s.2.2 evidence
(owner manual method and drawing-derived method side by side), s.2.4 reconciliation in lm, s.4 rule + test, s.7 lesson.
Rules: UP-STAIR-009 / -010 / -011 (library 1.4.0), UP-SKIRT-001 1.4.0, R-T410-1 .. 4, R-T481-3, ELEMENT_REGISTER 'STAIR
SKIRTING vs ROOM SKIRTING' (Lead 2026-11-04), OWNER_RULE_STAIRS 2026-10-24 S-9 (no winder generated; release each quantity
on its own evidence), Q-46 A, ORR-007 (form, open). Drawings named by Drive folder and title only.

## 0. What was read (own read this run)

| Source | Used for |
|---|---|
| Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55), decoded into `.work/private` only, BY HANDLE | 37 stations on the ST-01 shaft faces, GF / 1F / 2F (`t501_alsenan.py --dxf`, 1 mm tolerance): walls, windows, first / last nosings and riser faces of every ST-01 flight, the MS2-TR riser pair, the 2F slab-opening edge |
| research/agents_t410 (MERGED; reproduced byte-identical from the DXF this run, `t410_alsenan.py --write`: no diff) | stretch table, flight counts (T-184 / Q-46 A) |
| research/agents_t481 SHAFT_FACES_T481.csv, agents_t483 s.5 (WAITING T483_1F_SHAFT) | the 9.050 + 2.200 lm to bind |
| research/agents_t493 (MS2-TR at x 1.25 / 1.30), t412 (MS1-U 12th edge on ST p.4), t441 / t443 (stair-room children) | cited, cross-checked against own handle reads |
| BOQ_FAMILY_MASTER_1.48.0 B7-07 / B7-08 | family meaning |

## 1. Physical element and two findings before any number

A stair skirting is a strip on a wall / column face at the level of what stands against it: along a flight it climbs
(form zigzag UP-STAIR-010 or sloped UP-STAIR-011); on a landing or floor it is level. An open side has no face: never
skirted (B7-09 rail owns that edge).

**F-T501-1 (family meaning).** BOQ_FAMILY_MASTER 1.48.0 names B7-07 'Stair skirting zigzag' (توشيح متعرج) and B7-08 'Stair
skirting sloped' (توشيح مائل). The T-501 row and the register ruling read them as 'wall side / open side'. An open side
carries no skirting (R-T410-1), so that reading would create a family with no physical element. Proposal (R-T501-3): one
line per wall-side piece; its family is set by the project form (ORR-007): zigzag -> B7-07, sloped -> B7-08, never both
valued; until ORR-007 is answered the line is HELD-FORM with both figures beside. Lead: correct the register wording.

**F-T501-2 (the 9.050 lm is not a physical piece).** The 1F living line L-ba3599ec measured the shaft faces at the 1F
floor +5.50. Own read: on the 1F plan the east lane is MS1-U up to its last nosing ABE s 4.150 (riser face ABD 4.200) and
the west lane MS2-L from its first nosing AC0 s 4.500; between the walls north of these stations there is no +5.50 floor
anywhere (MS1-LD +3.50 and MS1-U below, MS2-LD +7.516 / +7.684 and MS2-U above). The 9.050 lm certain and the W13 / W25
2.200 lm range are therefore NOT_APPLICABLE in the room line; the skirting that physically exists on those faces is the
set of stair and landing pieces at their own levels (section 2), each its own line.

## 2. Pieces, flight by flight (LINES_T501.csv; face stations from the shaft's north-west inner corner)

Owner manual method (UP-STAIR-010 / -011, the rule pack): zigzag = goings + rises along the side; sloped = the rake from
the flight's plan run and total rise. Drawing-derived method (this run): the stations of each piece read by handle, the
risers standing in it, the level at each end; landings level. Both are given per piece; the form is not chosen (ORR-007).

| Flight / landing | Wall side pieces (stations) | Status | Zigzag / sloped lm (beside) | Drawing refs |
|---|---|---|---|---|
| MS1-L GF +1.00 -> +2.667 | W 3.900 .. 2.250 (3 pieces, column 2FBD returns 0.100) | HELD-FORM | 2.750 / 2.039 | GF 298, DC, 2FBD |
| | W 2.250 .. 1.200 | HELD (GF window 352-354) | 1.717 / 1.234 | GF 352-354 |
| MS1-T winders | W 0 .. 1.200, N 0 .. 1.150 | HELD (S-9) | - | GF 49E / 4A0 / 4A2 / 26E |
| MS1-LD +3.50 | E 0 .. 1.150 | **1.150 DRAWING-CONFIRMED** (level) | - | GF 21B, 1F B16; south edge 481 / A92 |
| | N 1.350 .. 2.500 | HELD (opening 3FD / 3FE) | - | GF 2AB / 3FD / 26F |
| MS1-U +3.50 -> +5.50 | E1 1.150 .. 2.100 | HELD-FORM | 1.617 / 1.111 | GF 21B, 1F B16 |
| | E2 2.100 .. 3.000 | HELD (GF hidden opening 33C / 33D) | 1.400 / 1.052 | GF 33C / 33D |
| | E3a 3.000 .. 4.150 | HELD-FORM | 1.817 / 1.345 | GF 21C, 1F B16, ABE |
| | **E3b 4.150 .. 4.450** | **CONFLICT** (new, F-T501-3) | 0.467 / 0.351 | 1F ABE / ABD vs ST p.4 459 |
| MS2-L 1F +5.50 -> +7.516 | W 4.500 .. 2.250 (3 pieces, column 3005 returns 0.100) | HELD-FORM | 3.694 / 2.737 | 1F AF1, AC0, 3005; 2F 12B7 |
| | W 2.250 .. 1.200 | HELD (W13 C5C / 12D1) | 1.722 / 1.230 | 1F C5C, 2F 12D1 |
| MS2-LD split landing | W 0 .. 1.050 (+7.516), N 0 .. 1.300 (+7.516), N 1.300 .. 1.400 + 2.400 .. 2.500 (+7.684), E 0 .. 1.150 (+7.684) | **3.700 DRAWING-CONFIRMED** (level; new, F-T501-4) | - | 1F AF0 / ADE / ADD / B16, 2F 12B8 / 127E / 127D / 129A, BE5 / 12B5, A97, 135B |
| | W 1.050 .. 1.200 (W13), N 1.400 .. 2.400 (W25) | HELD (sill / head vs the landing not printed) | - | 1F C5C, CE2 |
| MS2-TR closing riser | at N 1.300 | HELD (2F diagonal 2F1F / 2F20, Q-ST-11) | 0.168 / - | BE4 / BE5, 12B4 / 12B5 |
| MS2-U +7.684 -> 2F +9.70 | E 1.150 .. 4.450 | HELD-FORM | 5.316 / 3.867 | 1F B16, 2F 129A, 135B |
| D1 GF +0.30 -> +1.00 | E 1.150 .. 2.050 | HELD-FORM | 1.600 / 1.140 | GF 21B, 481 .. 490 |
| ST-02 RS-S / RS-LD / RS-C, ST-03 E1 | carried from T-410 unchanged (RS-LD 1.250 DRAWING-CONFIRMED level; RS-S 2 pieces HELD-FORM 4.457 / 3.300; RS-S.S0 / RS-C UNKNOWN; E1 HELD-FORM 2.050 / 1.471) | | | T-410 |

Totals: landings (FIN.SKIRTING, level) **6.100 lm DRAWING-CONFIRMED** = MS1-LD 1.150 + MS2-LD 3.700 + RS-LD 1.250 (T-410:
2.400). Flights HELD-FORM: 13 pieces, 53 risers, zigzag **23.300 lm** / sloped **17.009 lm** (T-410 23.767 / 17.360 less
E3b). HELD / UNKNOWN / CONFLICT: 12 pieces, 12.666 m plan, blank, never 0.

Hand checks (independent of the code): MS2-LD 1.050 + 1.300 + 0.100 + 0.100 + 1.150 = 3.700; E3a zigzag 1.150 + 4 x
0.166667 = 1.817, sloped 1.150 x hypot(3.30, 2.00) / 3.30 = 1.150 x 1.169320 = 1.345; E3b 0.300 + 0.166667 = 0.467 /
0.300 x 1.169320 = 0.351; 23.767148 - 0.466667 = 23.300481; 17.359845 - 0.350796 = 17.009049.

**F-T501-3 (MS1-U top: two drawings, one strip).** T-410 runs MS1-U 3.300 m (11 goings, Q-46 A 12 risers) from A92 s 1.150
to s 4.450; the architectural 1F plan ends it at ABE 4.150 / ABD 4.200 (11 riser lines) and the 1F room line takes B16
from 4.150 (T-481 room remainder 1.050 lm). ST p.4 draws the 12th edge 459 at s 3.30 of the flight (= 4.450), T-412. So
B16 4.150 .. 4.450 (0.300 m) was claimed by both if T-410's stretch were wired as is. R-T501-4: E3b is its own CONFLICT
piece, blank; the room line keeps its 0.300 certain until the Q-46 RFI / B20 head clash fixes the 1F floor edge (one
figure today, never two). T-481's own CSV places MS1-U at 0.850 .. 4.150: 0.300 off (it overlaps MS1-LD.E 0 .. 1.150);
the plan union 4.150 is unaffected.

**F-T501-4 (MS2-LD released level, split-independent).** T-410 held all MS2-LD for 'MS2-TR position not drawn'. The wall
faces beside the landing are drawn on both plans that bracket it (1F AF0 / ADE / ADD / B16 and 2F 12B8 / 127E / 127D /
129A, same stations to 1 mm) with openings only at W13 / W25 (stacked windows on both plans). The closing riser's place
only moves length between the +7.516 and +7.684 parts and adds one 0.168 step where it meets a wall; the level total
3.700 lm does not depend on it. T-410's MS2-LD.E 1.200 ran to A97 (the WEST lane's top nosing) and overlapped MS2-U from
135B 1.150 by 0.050 at +7.684: corrected to 1.150 (refused in code if reverted, pin test).

## 3. The binding (BINDING_T501.csv; acceptance 'bind the 9.050 + 2.200 lm')

| Room-line piece (+5.50) | lm | Covered by (all levels) | Residual | Decision |
|---|---|---|---|---|
| E 0 .. 4.150 | 4.150 | MS1-LD.E, MS1-U.E1 / E2 / E3a, MS2-LD.E, MS2-U.E (D1.E below) | 0.000 | NOT_APPLICABLE |
| W AF0 0 .. 1.050 | 1.050 | MS2-LD.W (MS1-T.W below) | 0.000 | NOT_APPLICABLE |
| W AF1 2.250 .. 4.500 (+ 3005 returns 0.100) | 2.350 | MS2-L.W1 / W1C / W1B (MS1-L below) | 0.000 | NOT_APPLICABLE |
| N ADE 0 .. 1.400 + ADD 2.400 .. 2.500 | 1.500 | MS2-LD.NW / NE / NE2 (MS1-T.N, MS1-LD.N below) | 0.000 | NOT_APPLICABLE |
| W13 1.050 .. 2.250 (range) | 1.200 | MS2-LD.W13 0.150 + MS2-L.W2 1.050 | 0.000 | NOT_APPLICABLE |
| W25 1.400 .. 2.400 (range) | 1.000 | MS2-LD.W25 | 0.000 | NOT_APPLICABLE |

9.050 lm certain + 2.200 lm held = 11.250 lm, residual 0.000 (T-481: 10.225 vs walk 10.232, its 0.007 named there). No
stair piece sits at +5.50 inside any retired segment (refused in code otherwise). Overlap with FIN.SKIRTING after the
proposal: **0 lm**, checked level-aware in code over every piece on the three shaft faces together with the room pieces
on them (GF lobby +0.30, GF hall +1.00, 1F remainder +5.50, 2F arrival +9.70; T-441 / T-443 children). Named, not valued:
2F 129A 4.450 .. 4.500 (0.050 m between MS2-U's end and the 2F arrival, inside T-418's east-lane foot strip) is in no
piece; same Q-46 cause as E3b on the floor above.

## 4. Engine vs freelancer (quantities only)

Freelancer FIN.SKIRTING 282.85 lm (12 dry-room gross perimeters, T-106; his perimeters run along the shaft) and 96 stair
skirting PIECES (T-410 s.4; main stair 63). Candidate FIN.SKIRTING certain 212.379 lm (V3.0.51) -> **209.429 lm after
this proposal** (-9.050 room line, +6.100 landings; -2.950 lm, -1.39 %); vs freelancer -24.9 % -> -26.0 %:
RULE_DIFFERENCE (doors deducted UP-CER-003; one face one owner along a stair), never the target. Stair flights: unit
RULE_DIFFERENCE (his pieces vs lm), as T-410. Verdict proposals: shaft faces at +5.50 ENGINE_WRONG in the room line
(no floor there; hand: ABE 4.150 / AC0 4.500 bound the floor zone), corrected by the move; MS2-LD level skirting
ENGINE_OMISSION (3.700 lm in no line; hand above); MS1-U top 0.300 UNRESOLVED (two drawings).

## 5. Stream F line proposal (no candidate change in this task)

- FIN.SKIRTING: L-ba3599ec net 41.435360 -> **32.385360** (the 9.050 NOT_APPLICABLE_WITH_EVIDENCE, stations above); its
  range L-079bc766 0 .. 2.200 -> NOT_APPLICABLE (W13 / W25 go with MS2-LD.W13 / .W25 and MS2-L.W2). New landing lines
  (children of the stair rooms, register ruling): MS1-LD 1.150, MS2-LD 3.700 (W 1.050, N 1.500, E 1.150), DRAWING-CONFIRMED;
  RS-LD 1.250 (T-410); held blank: MS1-LD.N, MS2-LD.W13, MS2-LD.W25.
- B7-07 / B7-08: one line per flight wall piece of LINES_T501.csv, family 'B7-07 | B7-08', HELD-FORM blank with both
  figures; held / unknown / conflict pieces blank with cause; MS2-TR step blank. When ORR-007 is answered every HELD-FORM
  line takes B7-07 (zigzag) or B7-08 (sloped) with no re-measure.
- Retire T483_1F_SHAFT / T443_1F_SHAFT waiting names at the same time.

## 6. Code, tests

- `t501_stair_skirting_home.py`: R-T501-1 `check_one_owner` (level-aware), R-T501-2 `retire` (closure), R-T501-3 `line` /
  `check_lines` (form decides the family), R-T501-4 `split` + carrier rule. `t501_alsenan.py`: `--dxf` re-reads 37
  stations by handle, `--write`, `--check` (no private input).
- `tests/t501_stair_skirting_home`: 19 tests. Hand villa K501 (not Alsenan): straight flight between walls (4.220 /
  3.039803 per side; B7-07 8.440 / B7-08 6.079606), dog-leg landing level once (3.600), stacked flights, retire by
  closure (residual 0; missing piece keeps the figure), mirror invariance, conflict split. Adverse: open side as a line,
  landing return twice, flight and floor at one level, conflict without carrier, retiring where the floor stands, side
  used as a form, held with a value / confirmed 0, average of the forms, held without cause, millimetres, flight without
  run / rise. Alsenan pins: reproduces, closure 9.050 + 2.200 residual 0, totals by hand, T-410 positions (MS2-LD.E 1.200,
  E3 unsplit) refused, 50 ST-01 flight risers once. T-410 (21) and T-481 (23) suites still pass.

## 7. Held / missing; lesson

Held: ORR-007 (form; decides 6.291 lm, zigzag - sloped); W13 / W25 / GF window 352-354 / hidden opening 33C / 33D sills
and heads against the flights; MS2-TR place (diagonal 2F1F / 2F20); MS1-U top 0.300 (Q-46 RFI / B20); the 2F 0.050.
Checker: re-measure one flight (suggest MS2-L W side, AC0 4.500 -> A97 1.200, column 3005) and MS2-LD's 3.700 by handle.

Proposed ERS s.7 row: | 2026-11-04 | a room line measured 9.050 lm of skirting at +5.50 along a shaft with no +5.50 floor,
and two stair tables placed one flight 0.300 m apart | faces were bound by plan stations only; the level of what stands
against the face was never tested, and flight ends came from goings x count, not from the drawn last riser | a face
piece is owned by what stands against it at its level: test plan overlap AND level band before binding; take flight
ends from the drawn first / last nosing on every plan, and a count that needs more run than is drawn is a CONFLICT piece,
not a longer flight (any villa) | tests/t501 check_one_owner / retire / split | T-501 |
