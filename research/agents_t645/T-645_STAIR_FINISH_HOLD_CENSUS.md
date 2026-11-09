# T-645 B7 stair finishes: the 31 HELD-blank lines to a quantity or a named cause (research, unwired)

Worker 2, lane A, 2026-11-08. Files: `t645_rules.py` (R-T645-1, every villa), `t645_alsenan.py` (builder, repository files
only, sha256-pinned), `out/STAIR_HOLD_CENSUS_T645.json` / `.md` (one row per line), `tests/t645/` (10 tests). No engine,
rule / knowledge version, registry, frozen or candidate file changed; nothing wired or released.

## 1. Physical elements and method (ERS s.2.1)

- RISER marble (B7-03): the vertical face under each nosing, one riser per drawn front edge (T-412 R-T412-1). Visible
  height = finished riser R - tread marble t (UP-STAIR-003; t = 0.030, UP-STAIR-006 owner-confirmed default, no tread
  detail drawn). Width = the drawn front edge, less a proud column where the riser-face line itself crosses it.
- FLIGHT (B7-01, lm): the sloping pitch line nosing to nosing = goings x hypot(going, R) on a straight flight.
- R = (printed FFL to - FFL from) / governing riser count: the owner's construction method uses ONE intended finished
  riser per flight (OWNER_RULE_STAIRS_2026-10-24 s.1); unprinted intermediate landing levels are never used.
- This is the method of the only released riser line (E1 L-0afa7bd369ec489ebfc2: 5 x (0.85 / 5 - 0.030) x 2.80 = 1.96 m2)
  and of the candidate's own FIN.STAIR.FLIGHT formula (arch_measure: hypot(run, treads x riser)). The candidate holds
  every other riser / flight line BLOCKED_RFI 'STAIR_RISER_NOT_ESTABLISHED' only because the engine had no riser input.

Own read this run (Drive copies, `.work/private` only, by handle): every class-A and class-C front edge 1.150, every going
0.300 (MS1-L 9, MS1-U 10 on the arch plan + the 11th on ST p.4, MS2-L 11, MS2-U 10, D1 3, RS-S 10, RS-A 4); the riser-face
companions D0 (column 2FBD), ABB (3005), B55 / B54 / B53 (300E) cross the proud column over 0.050, so the five notched
nosings are also notched risers (CF / D1, B43 / B4E, B47 / B52 do not); ST p.4 east lane 459 .. 25B = 12 lines at 0.300
(459 the 12th, MS1-U floor edge); ST p.4 west lane 45A .. 25E = 12 lines over 3.300 (the MS1-L conflict reading); ST p.5
east lane 11 lines (MS2-U 12th edge drawn nowhere).

## 2. Result (scope = T-630 per_line, B7 HELD with no bound in the four codes: 31 lines, matches the row)

| Class | Lines | What happens |
|---|---|---|
| A_DRAWN | 10 | fix rows HELD blank -> RELEASED: risers D1 0.667, MS1-U 1.886, MS2-L 1.8975 (DRAWING-CONFIRMED), RS-S 1.633929, RS-A 0.751607 (ASSUMED - OWNER-APPROVED, Q-50 A cond riser 4.50 / 28, T-438 governing) = **6.836036 m2**; flights D1 1.041933, MS1-U 3.775064, MS2-L 3.782209, RS-S 3.403367, RS-A 1.361347 = **13.36392 lm** |
| C_OPEN | 6 | stay HELD, bounded: MS1-L riser 1.564833 .. 1.886 m2 and flight 3.088689 .. 3.775064 lm (C-ST-4 / RFI-A04: arch 10 fronts vs ST p.4 12; owner 2026-10-22 'MS1-L HELD'); MS2-U riser 1.7457 .. 1.9044 m2 and flight 3.438372 .. OPEN (12th edge and 11th going drawn on no sheet, T429_LAST_GOING, head clash B23); soffit ST-01 20.468807 .. OPEN, ST-02 4.460946 .. OPEN m2 (T-281) |
| B_HELD | 6 | blank, cause named, figure beside: MS1-T winder turn tread / riser / flight (D-67, S-9); RS-C curved tread / riser / flight (Q-50 A cond, RFI-A03, S-9: no walking line) |
| A_CARRIED | 9 | no figure: RS-S 1F F4 and GF F3, RS-A 1F F6, RS-C 1F F1 risers and flights, MS2-L 2F F1 flight (double count): each names its carrier (R-T429-1, one flight one valued line) |

Hand checks (independent of the code): 4 x 1.15 x 0.145 = 0.667; 13.80 x (1/6 - 0.03) = 1.886; 13.75 x 0.138 = 1.8975;
12.50 x 0.1307143 = 1.633929; 5.75 x 0.1307143 = 0.751607; 11 x 0.3431877 = 3.775064; 11 x 0.3438372 = 3.782209;
3 x 0.3473111 = 1.041933; 10 x 0.3403367 = 3.403367; 4 x 0.3403367 = 1.361347. Soffit ST-01 low = method D 17.243246 +
MS1-L min D 3.225561 = 20.468807 (method O 17.197803 + 3.677828 = 20.875631; one method at a time).

Effect on the 10 Nov BOQ (if lane I wires the rows after the Checker): B7 m2 HELD blank 37 -> 37 - 5 released - 4 bounded
(risers 2 + soffits 2) = 28 blank (20 formwork B7-13, not this row; 6 risers = 2 by cause + 4 carried; 2 treads by
cause); B7 lm HELD blank 28 -> 28 - 5 released - 2 bounded = 21 (7 flights = 2 by cause + 5 carried; 14 skirting /
railing, not this row). Released B7-03 1.96 -> 8.796036 m2; B7-01 0 -> 13.36392 lm.

## 3. Freelancer and who is right

His stair rows are pieces (one per step, tread + riser + nosing together, UP-STAIR-008), no riser m2, no flight lm and no
soffit row (T-412 s.5, T-434): RULE_DIFFERENCE, nothing comparable in m2 / lm. Width: ENGINE_RIGHT 1.150 drawn (his
1.20 is the structural lane). Verdict proposals per line: A_DRAWN = ENGINE_RIGHT on the drawing (hand calculation above).

## 4. For the Lead / Checker

- F-T645-1 (one geometry, OWNER_RULE_STAIRS s.1): the MS1-L TREAD and STEP lines are RELEASED (3.105 m2 / 10.35 lm on the
  architectural 10-front reading, T-425 / T-429) while C-ST-4 / RFI-A04 keeps the MS1-L riser count open and the owner
  said 'MS1-L HELD' (2026-10-22). Either T-434 (Q-46 A: A-A 10 + 5 governs, Checker-verified) settles the FINISH count -
  then the MS1-L riser 1.564833 m2 and flight 3.088689 lm release with it - or the tread / step release is premature.
  Kept HELD here (owner words win); Lead to rule, Checker to re-measure.
- MS1-U's 12th riser sits under the B20 head clash (Q-46 RFI); the riser exists (12 risers, A-A) and ST p.4 draws its
  edge (459): released. If the Checker reads the clash as moving the edge, the riser width / height do not change.
- Checker re-measure picks: RS-S riser 1.633929 (B43 .. B4D, notches at 300E) and MS2-L flight 3.782209 (AC0 .. A97).
- Lesson proposal (ERS s.7): "2026-11-08 | 27 riser / flight lines HELD blank for days although every flight's riser
  follows from printed levels and the governing count | the engine wanted a riser input and the census read
  'BLOCKED_RFI' as a missing design fact | a hold reason is checked against the merged evidence before it is carried:
  R = printed rise / governing count where the count is settled; an RFI tag that the evidence answers is not a cause |
  R-T645-1 | tests/t645 | PROPOSED".

## 5. Not done / uncertain

Soffit high ends (warped / helicoid soffits not drawn, members HELD) and the O / D choice (no owner soffit rule); soffit
finish type not printed; MS1-T and RS-C until D-67 / RFI-A03; the D1 and E1 undersides are not rows (T-281 s.9).
