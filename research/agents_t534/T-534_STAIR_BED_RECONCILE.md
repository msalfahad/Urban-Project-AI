# T-534 B7 stair bed area: Q-53 39.49 m2 vs the T-511 census 35.4313 m2, reconciled to the physical cause

Worker 2 (lane A), 2026-11-05, branch agents/task-T-534, base engine f05abdd6 (candidate of record ARCH_TAKEOFF_V3.0.58;
its only change over V3.0.57 is FIN.WP.ROOF, so the stair lines are read from the V3.0.57 line index of T-507).
Research only, UNWIRED: `research/agents_t534/*`, `tests/t534_stair_bed/*`. No engine, rule, registry or candidate file
changed; no released quantity moves. ERS s.2.1 (physical element first), s.2.4 (reconcile in units, residual named),
s.4 (rule + test), s.7 (lesson). No drawing, workbook, image or client name is copied; every figure below is a
dimension, a count or an engine line id already in merged research.

## 1. Physical element and the question

Stair marble is three surfaces: the TREAD (horizontal going, front edge to front edge = riser face to riser face, x the
drawn front-edge width), the RISER (vertical plate, width x VISIBLE height = rise - 0.030 tread marble, UP-STAIR-003 /
UP-STAIR-006) and the LANDING (its polygon, UP-STAIR-005). The riser onto a landing or a floor has no tread above it.
The drawn 0.050 nosing overhangs the riser plate below and carries no bed (it is the B7-05 nosing lm, T-412).

The 1:3 bed (Q-45 B: stairs 3 cm, 1:3; Q-53 C rate, UP-STAIR-017) lies under the horizontal stone. Behind a riser the
setting mortar is a vertical backing; it is in the stair bed scope here because the owner was asked for it by name:
Q-45 item 1 'marble stairs (treads, risers) __ cm', answered B (stairs 3 cm 1:3), and Q-53's own scope 'marble treads,
risers, landings' (answered C). Status of the riser bed: ASSUMED - OWNER-APPROVED (Q-45 B, Q-53 C). Without such a
source the method holds the riser bed by name and keeps the riser marble (R-T534-2, adverse test).
So, on this villa, bed area = marble area (treads + visible risers + stair landings); a floor-or-landing whose finish is
undecided (GF hall 4.805, GF lobby 1.3225, R-T490-1) is in neither.

## 2. What the two figures are (flight by flight; FLIGHT_TABLE_T534.csv)

- **39.49 (39.485) = T-086 (worker 3, 2026-10-20)**, the table the Q-53 text cites: 6 flights (E1, D1, MS1-L, MS1-U,
  MS2-L, MS2-U) + 2 printed landings (MS1-LD 1.20 x 1.25, MS2-LD 2.50 x 1.25), built as ONE TREAD PER RISER at the printed
  width 1.20 and the FULL rise; round stair, winders and arrivals not in it. Not a candidate figure.
- **35.4313 = the 11 RELEASED stair-bed lines of the candidate** (T-511 census): 8 treads (MS1-L 3.105, D1 1.035, MS1-U
  3.795, MS2-L 3.795, MS2-U 3.450, RS-S 3.450, RS-A 1.380, E1 3.3594), 1 riser (E1 1.960) and 2 landings (E1 entrance
  5.1794, 1F arrival 4.9225). The other 23 stair-bed lines are 20 HELD (every main / round stair riser, the winder
  turn, RS-C, exposure re-readings, two landing bounds) and 3 EXCLUDED (MS2-L read again on 2F, RS-S folded reading).
  It is an AT_LEAST figure, never complete.

| Flight / landing | A: Q-53 / T-086 (T + R + L) | B: candidate released | C: drawing-derived (this task) |
|---|---|---|---|
| E1 (5 risers, 4 treads, 2.80) | 4.200 + 2.380 = 6.580 | 3.3594 + 1.960 = 5.3194 | 3.360 + 1.960 = 5.320 |
| D1 (4 / 3, 1.15) | 1.440 + 0.840 = 2.280 | 1.035 + HELD | 1.035 + 0.667 = 1.702 |
| MS1-L (10 / 9 + winder 485) | 3.600 + 2.000 = 5.600 | 3.105 + HELD | 3.105 + 1.5717 = 4.6767 |
| MS1-T winder turn | HELD | HELD | HELD (S-9; beside 1.495) |
| MS1-U (12 / 11) | 4.320 + 2.400 = 6.720 | 3.795 + HELD | 3.795 + 1.886 = 5.681 |
| MS2-L (12 / 11) | 4.320 + 2.4192 = 6.7392 | 3.795 + HELD | 3.795 + 1.9044 = 5.6994 |
| MS2-TR closing riser | 0.2016 (inside T-086's 13) | none | HELD (position, beside 0.1587) |
| MS2-U (12 / 10 + 1 going HELD) | 4.320 + 2.4192 = 6.7392 | 3.450 + HELD | 3.450 + 1.9044 = 5.3544 (+0.345 HELD) |
| RS-C curved | HELD | HELD | HELD (Q-50 A cond; beside 4.0944 + 1.8039) |
| RS-S (11 / 10) | HELD | 3.450 + HELD | 3.450 + 1.6535 = 5.1035 |
| RS-A (5 / 4) | HELD | 1.380 + HELD | 1.380 + 0.7516 = 2.1316 |
| MS1-LD | 1.500 | no line (T-493 F-3) | 1.4375 |
| MS2-LD | 3.125 | inside HELD bound | 2.9325 |
| RS-LD | - | no line (T-493 F-2) | 1.3525 |
| 1F arrival (Q-66 B) | - | 4.9225 | 4.9225 |
| 2F arrival (Q-70 A) | - | inside HELD bound | 4.8650 |
| E1 landing | - | 5.1794 | 5.1800 |
| **Total** | **39.4850** (complete within its scope; 5 HELD rows) | **AT_LEAST 35.4313** + 20 HELD | **AT_LEAST 56.3586** + 8 HELD |

C sources: tread fronts and goings T-425 (MERGED, Checker re-measured), riser counts T-412 (section A-A, Q-46 A; D1 /
E1 / round stair from the plans, Q-50 A cond), levels T-184 (rises MS1 4.50 / 27, MS2 4.20 / 25, D1 0.70 / 4, E1 0.85 / 5,
round stair 4.50 / 28), landings T-493 (MERGED). C = 23.370 treads + 12.2986 risers + 20.690 landings.

## 3. Reconciliation 39.485 -> 35.4313 (-4.0537 m2, -10.27 %), residual 0.0000 (RECONCILE_A_TO_B_T534.csv)

Each key (flight x surface) is decomposed count -> width -> depth / height; the parts add exactly.

| Cause | m2 | Physical meaning |
|---|---|---|
| Tread COUNT | -3.0000 | T-086 put one tread on every riser; the riser onto a landing / floor has none, and MS2-U's 11th going is not drawn (E1 -0.84, MS2-U -0.72, D1 / MS1-L / MS1-U / MS2-L -0.36 each) |
| WIDTH | -0.6600 | printed stair width 1.20 vs the drawn front edge 1.150 on the treads (T-412 / T-425 ENGINE_RIGHT) |
| Riser HEIGHT | -0.4200 | E1: full rise 0.17 vs visible 0.14 (UP-STAIR-003): 5 x 2.80 x 0.03 |
| POLYGON | -0.0006 | E1 treads: candidate polygon 3.3594 vs printed 3.3600 |
| SCOPE, out | -14.9050 | 6 main-stair riser groups HELD in the candidate (10.2800: MS1-L 2.000, MS1-U 2.400, MS2-L 2.4192, MS2-TR 0.2016, MS2-U 2.4192, D1 0.840) + 2 landings with no released line (MS1-LD 1.500, MS2-LD 3.125) |
| SCOPE, in | +14.9319 | E1 landing 5.1794, 1F arrival 4.9225 (Q-66 B, answered after T-086), RS-S 3.450 and RS-A 1.380 (Q-50 A cond, answered after T-086) |
| **Total** | **-4.0537** | |

**Finding F-T534-1.** The 4.05 m2 gap is not one cause: it is a net of +-14.9 m2 of scope that almost cancels
(+0.0269) plus -4.08 m2 of measurement (tread count, width, riser height). Neither figure is the stair bed: 39.49 is a
different, partly double-counted scope (a tread on every riser; 1.20 width; full rise), and 35.4313 is an AT_LEAST
subset whose 11 lines are each physically right (every released key agrees with C within the 0.0006 polygon
residuals, B_to_C).

## 4. The bed area for V7, with status, and V7 restated

| Basis | Area m2 | Installed mortar m3 (0.03) | Cement theoretical (9.576 / m3) | Sand theoretical (0.9975 / m3) | Purchasing allowance (10 bags, 1.00 m3 / m3) | Status |
|---|---|---|---|---|---|---|
| Candidate released (wireable now) | AT_LEAST 35.4313 | 1.062939 | 10.1787 bags | 1.0603 m3 | 10.6294 bags, 1.0629 m3 | PARTIAL: 20 HELD lines named, never 0 |
| Drawing-derived (C) | AT_LEAST 56.3586 | 1.690758 | 16.1907 bags | 1.6865 m3 | 16.9076 bags, 1.6908 m3 | treads DRAWING-CONFIRMED (T-425), landings DRAWING-CONFIRMED (T-493), risers CALCULATED (A-A / plan count x printed levels x UP-STAIR-006 DEFAULT), riser bed ASSUMED - OWNER-APPROVED (Q-45 B); 8 HELD |
| C without the riser-bed source | AT_LEAST 44.0600 | - | - | - | - | adverse view only (riser bed HELD 12.2986) |

V7 (FINISH_MATERIALS_TABLE_V7, R-T528-1) is wired on ONE area: the candidate's released stair-bed lines, printed AT_LEAST
35.4313 + HELD (20 lines). B -> C = +20.9273 m2 (+59.1 %): risers held in the candidate 10.3386 (counts settled by T-412)
+ landings with no line 10.5875 (T-493 F-1 .. F-4, T-502 queued) + polygon 0.0012. The V7 bed reaches C only through
those integrations, line by line, never by a total.
HELD on C (beside, never in): MS1-T winders (1.495 reading), RS-C 12 treads 4.0944 + 12 risers 1.8039, MS2-U 11th going
0.345, MS2-TR riser 0.1587, GF hall 4.805 + lobby 1.3225 (finish undecided).

## 5. Verdict proposals and engine vs freelancer

- Q-53's 39.49 vs candidate 35.4313: RULE_DIFFERENCE (scope) + ENGINE_RIGHT on the measurement (tread count, width,
  visible riser): the candidate's released lines agree with the drawing; T-086's tread-per-riser and 1.20 width are
  superseded by T-412 / T-425.
- Freelancer: no cement / sand rows (T-511 s.5); his stair marble is pieces x 1.20 (T-425 s.4: RULE_DIFFERENCE /
  ENGINE_RIGHT on 56 risers). No new freelancer figure here.
- Checker re-measure suggestion (2 flights): MS1-U (11 fronts A92 .. ABE x 0.30 x 1.15 = 3.795; 12 risers x 1.15 x
  (4.50 / 27 - 0.03) = 1.886) and E1 (4 x 0.30 x 2.80 = 3.36; 5 x 2.80 x (0.85 / 5 - 0.03) = 1.96; landing 1.40 x 3.70).

## 6. Rule, tests, lesson

R-T534-1 .. 3 (stair_bed_reconcile.py docstring, every villa, no villa constant): surface parts (HELD never 0, a surface
once); bed scope (treads and landings bedded; a riser only with a named source; a material-held landing out, kept
beside); reconciliation by count -> width -> depth, scope and polygon causes named, any rest UNEXPLAINED and refused.
Tests `tests/t534_stair_bed`: P534 fixture (12 risers 0.17 x 0.30 x 1.20 + landing 1.20 x 1.20: marble 7.416 = bed 7.416
by hand, V7 0.22248 m3 / 2.1305 bags; no riser source -> AT_LEAST 5.40 + riser bed HELD 2.016), held flight HELD not
0, unknown rise holds risers only, held going / closing riser beside, mm / mirror / rotation, refusals (twice, treads >
risers, visible riser <= 0, a held figure, a figure-less release), a by-hand reconciliation (7.05 -> 7.416) and its
refusals; Alsenan pins (39.485 -> 35.4313 by cause, residual 0; C 56.3586; V7 on B 1.062939 m3 / 10.178704 bags;
committed out/ reproduces). `python3 -I research/agents_t534/t534_alsenan.py --check` reproduces without private input.

Lessons-register row proposed (ERS s.7):

| 2026-11-05 | stair bed 39.49 (Q-53) vs 35.4313 (census), 4.05 m2 unexplained | a hand table built one tread per riser at the printed width and full rise; the candidate releases treads but holds risers and two landings; the near-equal totals hid +-14.9 m2 of opposite scope | compare stair figures key by key (flight x surface), never by total; tread count from drawn fronts, visible riser = rise - tread marble; a bed under a riser needs its own source | tests/t534_stair_bed | T-534 |

## 7. For lane I (no candidate change here)

Wire V7 on the released stair-bed lines (AT_LEAST 35.4313, 20 HELD named). Lift the held riser lines with the T-412
counts (B7-03, +10.3386 m2 on 7 flights) and add the T-493 landing lines (T-502, +10.5875 m2); each lifts the V7 bed
line by line. Missing / uncertain: winders and RS-C (designer), MS2-U last going, MS2-TR position, GF hall / lobby
finish (RFI-B-A12), the riser plate notch at 5 proud-column edges (T-410, not applied on the 1.15 basis), and whether
the 20 mm landing marble (UP-STAIR-007) takes a thicker bed to stay flush (no detail; bed kept at the Q-45 3 cm).
