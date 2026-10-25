# T-280 Column foundation cores and starters on the verified level chain (Alsenan; every villa)

Worker 1 (lane S), 2026-10-25. Research piece: one script + tests. The S3 column ledger is read only (not edited); no
released, candidate or frozen quantity moves (the column ledger is not wired into any BOQ line). Development villa, not
an accuracy claim. Drawings named by Drive folder and title only; no private file read in this run (every datum below
is a merged, cited record, WORKFLOW_CONTROLS s.10 rule 5).

Files: `t280_core_datum.py` -> `CORE_DATUM_T280.json` (reproducible: `python -I research/agents_t280/t280_core_datum.py`),
tests `tests/t280_core_datum/` (17).

## 0. Engineering question and inputs

From which physical datum does each column core and starter run, and is any length counted from the formation instead
of the footing top? (finding F-T273R2-01, T-273 r2 MERGED 42e32cf3: -74.381 kg over 31 chains if the formation sits at
its limit.)

| Input (merged) | Used for |
|---|---|
| research/alsenan_column_rebar_s3 COLUMN_MAIN_BAR_REGISTER / COLUMN_LAP_STARTER_REGISTER | the 36 FOUNDATION MAIN_CORE rows, 36 STARTER, 56 LAP rows; kg/m = pi/4 d^2 x 7850 (the ledger's own method) |
| T-200 level table | existing plot level +-0.00 DRAWING-CONFIRMED (P7757 LEL x6, ST SH08, SECTION A-A); GF FFL +1.00 |
| T-206 r2 s.2.2 (ST7757.pdf p.9 / p.13 / p.14) | formation 'not less than 1.5 m below the existing plot level' = a LIMIT (Q-21 C); p.13 underlay 5 + 2 + 10 cm = 0.17 m DRAWING-CONFIRMED for the isolated types; p.14 lift footing FF: membrane with no thickness (underlay HELD); schedule H per type |
| T-204 (p.14) | pit floor = top of FF; pit depth 'As Per Lift Manufactures recommendations' (D-43, HELD) |
| T-273 r2 reconciliation | starter projection + foundation core = two layers at the footing top; LAP_TOP at each FFL |

## 1. Physical element and the datum chain

The foundation segment of a column's main bars runs from the TOP OF ITS FOOTING (where the starter's 40 D projection
laps it) to the storey joint at GF FFL (the S3 joint, where the FOUNDATION LAP sits). The footing top is not printed as a
level; it follows from the printed chain:

    formation <= EGL - 1.50 = -1.50        footing bottom = formation + 0.17        footing top = footing bottom + H
    core = GF FFL - footing top  >=  1.00 - (-1.50 + 0.17 + H)  =  2.33 - H

- LOWER bound = formation at its printed limit (the only bound the drawings give).
- UPPER bound = OPEN: no lowest formation is printed (p.8 note 12 leaves it to the contractor / supervising engineer
  after the soil check; the p.13 two-beam detail exists for deeper footings). Never a value, never the ledger's number.
- The S3 ledger's 2.50 - H puts the footing UNDERSIDE at -1.50, i.e. a formation at -1.67: neither bound. Its label
  LOWER_BOUND is restated CONVENTION_NOT_A_BOUND.

Each support family keeps its own chain (ERS s.3: a detail's value is not carried to another detail):

| Family | Chains | Chain used | Result |
|---|---|---|---|
| P13_ISOLATED, column continues above | 24 | p.13 underlay 0.17, schedule H | LOWER = 2.33 - H, UPPER OPEN |
| P13_CONFLICT (F / F10 under X15-Y01, X16-Y01) | 2 | 0.17, max H over both types (0.50) | LOWER 1.83 m, valid for both readings; type stays a finding |
| P13_ISOLATED, CN column STOPPING in the foundation storey | 3 | bottom as above; TOP = closing ground beam / slab top, not printed | HELD (TOP_DATUM_NOT_PRINTED) |
| LIFT_PIT_FF (X09-Y07, X09-Y09, X10-Y07, X10-Y09) | 4 | p.14: core = GF FFL - pit floor (= FF top); pit depth and FF membrane thickness unprinted | HELD (PIT_DEPTH_NOT_PRINTED); the p.13 0.17 is not carried over |
| UNBOUND (CN on 'FT:RB', STR-COL-001) | 3 | no footing bound | HELD (SUPPORT_NOT_BOUND); conditional 1.63 m if on a p.13 footing, shown, never summed |

New finding (stopping columns): for the 6 CN columns that stop in the foundation storey the ledger runs the core up to
GF FFL, through the floor build-up above the closing member's structural top, and then adds 40 D of ANCHORAGE_TOP. The
bars end in the closing ground beam / slab, whose top is not printed (T-206 r2: no structural slab top on any sheet), so
GF FFL is not their top datum; the core length is HELD at the top end as well. Columns that continue (30 chains, same
bars FOUNDATION -> GF on all 30, checked) are not affected by where the joint sits: moving it only shifts length between
the FOUNDATION and GF segments, the chain total is unchanged.

## 2. Per chain (kg at full precision, t = kg / 1000 once; ledger kg as stored)

| Chain | Type | Bars | Footing | Family | Ledger m / kg (label CONVENTION) | Restated LOWER m / kg / t | Delta kg |
|---|---|---|---|---|---|---|---|
| COLPOS-X01-Y01-2138-7462 | C | 8 T16 | FTG-F-1888-7312 | P13_ISOLATED | 2.200 / 27.779 | 2.030 / 25.632 / 0.025632 | -2.147 |
| COLPOS-X01-Y05-2038-13762 | C | 8 T16 | FTG-F-1888-13312 | P13_ISOLATED | 2.200 / 27.779 | 2.030 / 25.632 / 0.025632 | -2.147 |
| COLPOS-X02-Y05-4738-13862 | C | 8 T16 | FTG-F-4288-13462 | P13_ISOLATED | 2.200 / 27.779 | 2.030 / 25.632 / 0.025632 | -2.147 |
| COLPOS-X03-Y04-6338-12062 | C3 | 8 T16 | FTG-F3-5538-11362 | P13_ISOLATED | 2.200 / 27.779 | 2.030 / 25.632 / 0.025632 | -2.147 |
| COLPOS-X04-Y01-7988-7462 | C3 | 8 T16 | FTG-F15-7088-7312 | P13_ISOLATED | 2.100 / 26.516 | 1.930 / 24.370 / 0.024370 | -2.147 |
| COLPOS-X05-Y02-12538-9062 | C3 | 8 T16 | FTG-F3-11838-8262 | P13_ISOLATED | 2.200 / 27.779 | 2.030 / 25.632 / 0.025632 | -2.147 |
| COLPOS-X05-Y04-12538-11912 | C5 | 10 T16 | FTG-F13-11188-10712 | P13_ISOLATED | 2.000 / 31.567 | 1.830 / 28.884 / 0.028884 | -2.683 |
| COLPOS-X06-Y01-14088-7462 | C | 8 T16 | FTG-F-13638-7312 | P13_ISOLATED | 2.200 / 27.779 | 2.030 / 25.632 / 0.025632 | -2.147 |
| COLPOS-X06-Y04-14438-12062 | C11 | 14 T16 | FTG-F13-11188-10712 | P13_ISOLATED | 2.000 / 44.193 | 1.830 / 40.437 / 0.040437 | -3.756 |
| COLPOS-X07-Y?-15888-16162 | C7 | 12 T16 | FTG-F12-13688-14562 | P13_ISOLATED | 1.800 / 34.092 | 1.630 / 30.872 / 0.030872 | -3.220 |
| COLPOS-X08-Y04-17038-12362 | C6 | 10 T16 | FTG-F6-15938-11062 | P13_ISOLATED | 2.000 / 31.567 | 1.830 / 28.884 / 0.028884 | -2.683 |
| COLPOS-X08-Y09-17038-17362 | C3 | 8 T16 | FTG-F12-13688-14562 | P13_ISOLATED | 1.800 / 22.728 | 1.630 / 20.582 / 0.020582 | -2.147 |
| COLPOS-X08-Y10-17038-20562 | C2 | 8 T16 | FTG-F2-16188-19612 | P13_ISOLATED | 2.150 / 27.147 | 1.980 / 25.001 / 0.025001 | -2.147 |
| COLPOS-X09-Y07-19688-15662 | C2 | 8 T16 | FTG-FF-18688-14112 | LIFT_PIT_FF | 1.950 / 24.622 | HELD (pit depth) | - |
| COLPOS-X09-Y09-19688-17362 | C1 | 8 T16 | FTG-FF-18688-14112 | LIFT_PIT_FF | 1.950 / 24.622 | HELD (pit depth) | - |
| COLPOS-X09-Y10-19738-20562 | C2 | 8 T16 | FTG-F2-18888-19612 | P13_ISOLATED | 2.150 / 27.147 | 1.980 / 25.001 / 0.025001 | -2.147 |
| COLPOS-X10-Y07-21713-15912 | C9 | 14 T16 | FTG-FF-18688-14112 | LIFT_PIT_FF | 1.950 / 43.089 | HELD (pit depth) | - |
| COLPOS-X10-Y09-21688-17362 | C2 | 8 T16 | FTG-FF-18688-14112 | LIFT_PIT_FF | 1.950 / 24.622 | HELD (pit depth) | - |
| COLPOS-X11-Y10-23558-20662 | C5 | 10 T16 | FTG-F5-22358-19612 | P13_ISOLATED | 2.100 / 33.145 | 1.930 / 30.462 / 0.030462 | -2.683 |
| COLPOS-X12-Y01-24458-7462 | C3 | 8 T16 | FTG-F14-22408-7312 | P13_ISOLATED | 2.000 / 25.253 | 1.830 / 23.107 / 0.023107 | -2.147 |
| COLPOS-X12-Y02-24308-8912 | C8 | 12 T16 | FTG-F14-22408-7312 | P13_ISOLATED | 2.000 / 37.880 | 1.830 / 34.660 / 0.034660 | -3.220 |
| COLPOS-X13-Y08-27308-16612 | C9 | 14 T16 | FTG-F9-25608-15262 | P13_ISOLATED | 1.950 / 43.089 | 1.780 / 39.332 / 0.039332 | -3.756 |
| COLPOS-X13-Y10-27458-20662 | C4 | 8 T16 | FTG-F4-26358-19662 | P13_ISOLATED | 2.100 / 26.516 | 1.930 / 24.370 / 0.024370 | -2.147 |
| COLPOS-X14-Y02-27658-8962 | C5 | 10 T16 | FTG-F5-26458-7912 | P13_ISOLATED | 2.100 / 33.145 | 1.930 / 30.462 / 0.030462 | -2.683 |
| COLPOS-X15-Y01-31408-7462 | C10 | 10 T16 | FTG-CONFLICT_F_F10-30008-7312 | P13_CONFLICT | 2.000 / 31.567 | 1.830 / 28.884 / 0.028884 | -2.683 |
| COLPOS-X15-Y06-31508-15062 | C8 | 12 T16 | FTG-F8-29258-13262 | P13_ISOLATED | 2.000 / 37.880 | 1.830 / 34.660 / 0.034660 | -3.220 |
| COLPOS-X15-Y10-31508-20687 | C4 | 8 T16 | FTG-F4-30408-19687 | P13_ISOLATED | 2.100 / 26.516 | 1.930 / 24.370 / 0.024370 | -2.147 |
| COLPOS-X15-Y?-31208-15726 | CN (stops) | 4 T14 | FTG-F8-29258-13262 | P13_ISOLATED | 2.000 / 9.667 | HELD (top datum; bottom 1.830 info) | - |
| COLPOS-X16-Y01-33108-7562 | C | 8 T16 | FTG-CONFLICT_F_F10-30008-7312 | P13_CONFLICT | 2.000 / 25.253 | 1.830 / 23.107 / 0.023107 | -2.147 |
| COLPOS-X16-Y03-33108-11312 | CN (stops) | 4 T14 | FT:RB-93c296ab668f4cce | UNBOUND | 1.800 / 8.701 | HELD (support; cond. 1.630) | - |
| COLPOS-X16-Y06-33108-14962 | C3 | 8 T16 | FTG-F8-29258-13262 | P13_ISOLATED | 2.000 / 25.253 | 1.830 / 23.107 / 0.023107 | -2.147 |
| COLPOS-X?-Y01-17913-7462 | C11 | 14 T16 | FTG-F11-16163-7312 | P13_ISOLATED | 2.000 / 44.193 | 1.830 / 40.437 / 0.040437 | -3.756 |
| COLPOS-X?-Y10-31108-20498 | CN (stops) | 4 T14 | FTG-F4-30408-19687 | P13_ISOLATED | 2.100 / 10.151 | HELD (top datum; bottom 1.930 info) | - |
| COLPOS-X?-Y?-24058-12787 | CN (stops) | 4 T14 | FT:RB-d03ae1c0114c9c48 | UNBOUND | 1.800 / 8.701 | HELD (support; cond. 1.630) | - |
| COLPOS-X?-Y?-28583-12787 | CN (stops) | 4 T14 | FT:RB-4f1fedf6f22d413e | UNBOUND | 1.800 / 8.701 | HELD (support; cond. 1.630) | - |
| COLPOS-X?-Y?-29108-18112 | CN (stops) | 4 T14 | FTG-FN-28608-17612 | P13_ISOLATED | 2.200 / 10.634 | HELD (top datum; bottom 2.030 info) | - |

Hand checks: X01-Y01 (F, H 0.30, 8 T16): footing top <= -1.50 + 0.17 + 0.30 = -1.03; core >= 1.00 + 1.03 = 2.03 m;
8 x 2.03 x 1.578336 = 25.632 kg (ledger 2.20 m / 27.779 kg; delta 8 x 0.17 x 1.578336 = -2.147 kg). X15-Y01 (F or
F10, 10 T16): max H 0.50 -> 1.83 m, 10 x 1.83 x 1.578336 = 28.884 kg (with F the bound would be 2.03 m; 1.83 holds for
both). Every ledger H equals the T-206 r2 schedule H of its type (0 findings).

## 3. Totals and reconciliation

| | Rows | Ledger (CONVENTION) | Restated |
|---|---|---|---|
| LOWER bound restated | 26 | 801.321 kg = 0.801321 t | **734.781 kg = 0.734781 t** (LOWER_BOUND, UPPER OPEN); delta -66.548 kg (P13 -61.718, conflict -4.830) |
| HELD (no bound from the drawings) | 10 | 173.510 kg | HELD: pit depth 4, stopping-column top 3, unbound support 3 (never 0) |
| All foundation cores | 36 | 974.831 kg | 734.781 kg bound on 26 + 10 HELD |

T-273 r2's -74.381 kg reconciled: same formula recomputed -74.374 kg (residual -0.007 kg: T-273 took kg/m from the
rounded row kg; here unrounded, named) = -61.713 restated (24 continuing p.13 chains) - 10.196 withdrawn (4 lift FF
chains: FF underlay not printed, pit depth HELD) - 2.465 withdrawn (3 stopping CN on p.13 footings: top datum HELD);
plus -4.830 for the 2 F / F10 conflict chains T-273 left out. (Row-rounded sums: -61.718 / -66.548.)

Starters and laps (the same-datum check): all 36 STARTER rows = (H - 70 cover) + 300 foot + 40 D, measured on the footing
body (bottom cover from the footing underside, projection above the footing top): independent of the formation, 0 kg
change, 36 / 36 OK (5 BLOCKED have no length, correctly). All 56 LAP rows are LAP_TOP at the FFL above their segment:
independent of the formation, 0 kg change, 56 / 56 OK. Nothing in the ledger is counted from the formation; the only
datum error is the footing UNDERSIDE placed at the formation limit (the 0.17 m underlay omitted), plus the stopping
columns' top at GF FFL.

## 4. Engine vs freelancer; verdict proposals

No BOQ line moves (the column ledger is research only; nothing released, nothing candidate). The freelancer's
reinforcement is a kg/m3 lump (44.19 t) with no column-core line: **RULE_DIFFERENCE, no %** (URBAN-REBAR-NET-AND-
PROCUREMENT@v1). Verdict proposals: the 26 restated lower bounds ENGINE (ledger) WRONG on its label: 2.50 - H is a
convention, the printed lower bound is 2.33 - H (-66.548 kg, -8.3 % of those rows' ledger kg); 10 rows UNRESOLVED (designer
items below). Not an owner question (ERS 2.7 not met: unprinted design values, not an owner decision).

## 5. Rule proposed (every villa; provenance T-280; a new rule version only when adopted)

**R-COL-CORE-DATUM-1**: a column's foundation core starts at the TOP of its footing: footing top = formation + the
underlay printed for THAT support's detail + H. A formation printed only as a limit ('not less than x below existing
ground') gives a LOWER bound (formation at the limit) and an OPEN upper bound, never a value; a value obtained by placing
the footing underside at the formation limit is a convention, never labelled a bound. Underlay not printed for the
support (lift pit footing, unbound support) -> HELD, never measured from the formation and never borrowed from another
detail. A column that stops in the foundation storey ends in its closing member's structural top, not at FFL. Starters
and laps are measured on the footing body and the storey joints, independent of the formation.

## 6. Lessons-register row (proposed, ERS s.7)

2026-10-25 | A foundation core labelled LOWER_BOUND was 0.17 m longer than the printed minimum; a whole-ledger restatement
applied one footing detail's underlay to the lift footing too | The footing underside was put at the 'not less than 1.5 m'
excavation limit (the underlay between formation and footing ignored), and a correction was applied by "chains with a
known footing" instead of by the support's own detail | Restate each bound on its own chain (formation limit + that
detail's underlay + H); a support whose detail prints no underlay stays HELD; a stopping column's top is its closing
member, not FFL (any villa) | tests/t280_core_datum (villa K280 normal; underlay missing HELD, lift pit HELD, stopping
column HELD, unbound conditional not summed, mm input refused) | PROPOSED.

## 7. Not done / uncertain (designer items, no quantity chosen)

- Founding level: only the limit is printed (Q-21 C): every UPPER bound OPEN.
- Lift pit depth (D-43) and the FF membrane thickness: 4 lift chains HELD.
- CN columns: stub / pedestal question (STR-COL-001), 3 supports unbound, and the closing member top level for all 6.
- F / F10 footing type at X15-Y01 / X16-Y01 (bound covers both).
- GF FFL -> structural top build-up (T-206 r2: not printed): sets where the continuing columns' joint physically sits;
  no change to chain totals (same bars both sides on all 30).
- The 70 mm starter bottom cover is the ledger's 'cover against soil' rule while the footing is cast on blinding /
  membrane / screed; cover rule not in this row's scope (named, not changed).
- The S3 ledger itself is not edited (a column-ledger rework or the lane I integration takes these bounds with the
  Checker's verdict).
