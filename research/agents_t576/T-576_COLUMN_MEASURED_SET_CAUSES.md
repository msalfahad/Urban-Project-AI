# T-576 B10 GF / 1F column measured-set differences split into signed causes, and the GF B7 beam -0.120 m3 traced

Worker 1 (lane S, non-candidate, backlog-permitted), 2026-11-07, run session_01E6cPnbzcVXNDW6oHYKkj1t, branch
`agents/task-T-576`. Research only: no engine module, candidate line, released line, rule file or method version changed;
nothing released; no quantity moves. Development villa, not an accuracy claim. ERS s.2 - 4 and s.7 applied; R-T551-1 .. 4,
R-T566-1 .. 5, R-T572-4, R-T394-1, R-T395-4, R-CONC-OWN-1, MISSION no-assumptions.

## 0. Sources and run

- Engine: ARCH_TAKEOFF_V3.0.58 (NOT RELEASED); column lines through the merged T-551 reader (V3.0.57 LINE_INDEX + T-394
  per-line member data); position marks / CONFLICTs from the merged T-566 own read of ST7757 dxf
  (`POSITION_INPUT_T566.json`, `T566_REGISTRATION.json`); settled framing depths of the open members from the T-119 ledger;
  storey datums T-214 (slab tops +0.95 / +5.45 / +9.65, DRAWING-CONFIRMED on sections A-A / B-B).
- Drawing re-checked this run (Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf', sha256 9f9d1179, `.work/private` only):
  GFRS column outlines (34 = 30 SOLID on positions + 4 PATTERN starts, none SOLID off a position), the quarter-arc B7
  (arcs 29F / 2A0, R 1.30 / 1.10, closing line 484, column 353, lines 2B2 / 2B3 of the B4 line), the ring arcs 2EE / 2EF /
  2F0 / 310 - 313 / 317 / 318 and faces 46D / 42D / 2A9 / 437, and the route G bands at both B7 piece ends.
- Freelancer: Drive 'Alsenan chalet project', the concrete + rebar workbook (sha256 ae608411 = B1 manifest), read in
  memory; tracked output carries engine figures, terms in m3 and his measured-set storey totals only.
- Code: `t576_rules.py` (R-T576-1 .. 4), `t576_alsenan.py` -> `out/T576_COLUMN_CAUSES.json` (every reading, every mark).

## 1. The physical elements and the height basis (ERS s.2.1)

Storey column: drawn outline x slab top to slab top (the column line owns joint + head, slabs and beams net of it,
R-T394-1). GF interval +0.95 -> +5.45 = 4.50 m, 1F +5.45 -> +9.65 = 4.20 m. **His heights are 3.75 / 3.45 on every row =
the drawn interval - 0.75: his datum frame equals the drawn one (STOREY term 0.000 on every row)**; the whole height
difference is his one head depth 0.75 against the member's own controlling depth D_ctrl (the deepest framing beam). Per
member A x 0.75 = JOINT_HEAD A x D_ctrl (RULE_DIFFERENCE: ownership) + GLOBAL_DEPTH A x (0.75 - D_ctrl) (ENGINE_RIGHT:
his own clear-height convention with one global depth instead of the drawn one; + on 0.40 / 0.50 beams, - on 0.85).
Where a framing member's depth is not printed (T-119 FRAMING_MEMBER_HELD_D_OPEN), the settled framing beam prints
D_low = 0.75, so D_ctrl >= 0.75: JOINT_HEAD >= A x 0.75 and GLOBAL_DEPTH <= 0, open below. The column's m3 does not
depend on D_ctrl (it runs to the slab top); only the split does. **So 1F +21.74 % = 0.75 / 3.45 exactly**: on 1F every
measured-set member agrees in count and section and the whole difference is the 0.75 m head; GF would be +20.0 %
(0.75 / 3.75) before COUNT and BASE.

## 2. Per-mark tables (merged reading 10AE = C3, 10E0 = C8; engine - his, m3; re-add exactly)

**GF, 9 marks** (engine 12.705 vs his 11.53125 = **+1.17375, +10.18 %**)

| Mark | Engine | COUNT | JOINT_HEAD (RD) | BASE (ER) | GLOBAL_DEPTH (ER) | Count evidence |
|---|---|---|---|---|---|---|
| C1 | 0.450 | -0.375 ER | +0.075 | | | 1 drawn = 1 registered; his storey rows exceed his own neck rows |
| C2 | 1.800 | -0.750 ER | +0.205 | | +0.095 | 4 = 4; his storey rows exceed his neck rows |
| C9 | 2.250 | -0.9375 ER | +0.375 | | | 2 = 2; his storey rows exceed his neck rows |
| C11 | 2.475 | +1.03125 ER | +0.4675 | | -0.055 | 2 = 2 (35C / 37D, REGISTERED 3 / 3); his one row |
| C4 | 1.125 | | +0.1875 | | | |
| C5 | 2.130 | | +0.3375 | +0.105 (35F from +0.25) | | |
| C6 | 0.7875 | | +0.0875 | | +0.04375 | |
| C7 | 0.900 | | +0.150 at D_low 0.75 (B20; BM-GF-058 unprinted) | | 0.000 (upper; open below) | |
| C10 | 0.7875 | | +0.14875 | | -0.0175 | |
| **Total** | **12.705** | **-1.03125** | **+2.03375** | **+0.105** | **+0.06625** | |

By class: **RULE_DIFFERENCE +2.03375; ENGINE_RIGHT -0.860 (-7.46 % net of the rule difference)**: his rows carry four
GF columns of marks C1 / C2 / C9 that no drawn GF member has (the GF roof plan draws 30 SOLID members, all on
registered positions, 0 off a position) and that his own neck rows of the same marks do not carry, and miss one drawn C11.

**1F, 4 marks** (engine 3.108 vs his 2.553 = **+0.555, +21.74 %**): JOINT_HEAD C1 +0.075, C2 +0.205, P.C 20x70 +0.105,
P.C 20x50 +0.075 at D_low 0.75 (CB12 / CB11; BM-1F-035 / -038 unprinted) = **RULE_DIFFERENCE +0.460**; GLOBAL_DEPTH C2
+0.095 (D 0.40 / 0.50 / 0.40 on 67C / 670 / 66D) = **ENGINE_RIGHT +0.095 (+3.72 % net)**; P.C 20x50 counter-term 0.000
upper, open below. T-572's 'HEIGHT_OPEN +0.075' is now split at its printed lower end.

## 3. CONFLICT readings (R-T576-2; never a majority)

| Reading 10AE / 10E0 | GF set | GF diff | GF % | GF by class | 1F set | 1F diff | 1F % |
|---|---|---|---|---|---|---|---|
| C3 or C / **C8** (FP + CAP) | 9 marks incl. C7 | +1.17375 | +10.18 | RD +2.03375, ER -0.860 | 4 marks | +0.555 | +21.74 |
| C3 or C / **C7** (GBP) | 9 marks incl. C8, not C7 | +0.34875 | +2.80 | RD +2.075, ER -0.8825, CONFLICT_BOUNDED -0.84375 (his second GF C8 row) | 5 marks incl. C8 664 | +0.690 | +21.74 |

10AE never moves the measured set (C3 / C carry other held lines). 10E0 does: the GF % is **+2.80 .. +10.18 by reading**;
the 1F % is +21.74 under both (the extra member 664 is again a pure head). Both GF readings are stated; none is chosen.

## 4. GF B7 -0.120452 m3 (T-566 UNRESOLVED) traced

His GF B7 rows total 2.363 m longer than the four valued engine pieces (BAND0025.1 1.20, BAND0006 1.70, quarter arc
BAND0049 1.885, RING-B7 0.666406 m2 / 0.20 = 3.332 m). T-545's allowance (1.55 m) held only the two straight pieces' T-229
ends; **the T-229 support input has no end record for a curved or ledger-only piece**, so the remaining 0.803 m was
UNTRACED by construction. Closing faces read on the drawing (R-T576-3):

| Piece | End 1 | End 2 | Allowance m |
|---|---|---|---|
| BAND0025.1 | column 33E 0.50 | column 341 0.50 | 1.00 |
| BAND0006 (face 437) | B8 BAND0003 0.20 | CB1 BAND0041.2 0.35 | 0.55 |
| BAND0049 quarter arc | collinear B2 BAND0027 (mark boundary) 0 | line 484 against the HELD unlabelled piece GF-112 (D-04), beside 0 | 0 |
| ring NW arc 2EE | B7 face 437 (same mark) 0 | B8 face 46D 0.20 (oblique; void 2F0 tangent) | 0.20 |
| ring SW arc 2EF | B8 face 46D 0.20 | B17 face 42D 0.45 (oblique; void 318 pinch) | 0.65 |
| ring SE arc 312 | B17 face 42D 0.45 | CB1 face 2A9 0.35 | 0.80 |
| ring NE arc 313 | CB1 face 2A9 0.35 | B7 face 437 (same mark) 0 | 0.35 |
| **Total** | | | **3.55** |

His 2.363 m lies inside 3.55 m: **THROUGH_SUPPORT -0.354452 m3 (RULE_DIFFERENCE), UNTRACED 0.000**. Sensitivity: with
only the CB1 ring ends (2.25 m) 0.015 m3 would remain beyond; any reading that also counts the B8 or the B17 ring ends
(2.65 / 3.15 m) closes it. Not apportioned (his rows carry no location); GF-112 0.50 m (held) and the outer-face arc
reading (+0.157 m on BAND0049) are listed beside, never inside the allowance. T-566's beam UNTRACED -0.365289 becomes
-0.244837 named ENGINE_RIGHT + 0.014517 precision + **0.000 UNRESOLVED**; T-545 GF THROUGH_SUPPORT -2.902 -> -3.022 (split
change only, no line changed).

## 5. Who is right (proposals), what is open

- RULE_DIFFERENCE: column JOINT_HEAD GF +2.03375 (incl. C7 at D_low), 1F +0.460 (incl. P.C at D_low); GF B7
  THROUGH_SUPPORT -0.354452.
- ENGINE_RIGHT: GF COUNT -1.03125 (C1 / C2 / C9 rows without a drawn GF member and beyond his own neck rows; C11 one
  drawn member he omits), GF BASE +0.105, GLOBAL_DEPTH GF +0.06625 / 1F +0.095 (his one 0.75 depth vs the drawn 0.40 /
  0.50 / 0.85).
- CONFLICT_BOUNDED: 10E0 C8 / C7 moves GF between +2.80 % and +10.18 % (designer item, already on the T-566 RFI addition;
  every line at 10E0 HELD).
- Open, one-sided: the GLOBAL_DEPTH counter-term on GFRS 368, FFRS 69D (and 664 under C7) <= 0 below by the unprinted
  depth of BM-GF-058 / BM-1F-035 / -038 / -037 (designer items D-04 / D-05); the engine m3 does not move with it.
- No ENGINE_WRONG found: no fix row, no quantity change. UNRESOLVED 0.000 in every table. ERS s.2.7 not met: **no owner
  question**.

## 6. Rules, tests, lessons row (proposed)

R-T576-1 .. 4 (`t576_rules.py`). `tests/t576_column_causes` (15): hand villa V576 (column 0.30 x 0.60, storey 4.20, beam
0.60: clear 3.60 x 0.18 = 0.648, through 0.756, joint 0.108 owned once; global depth both signs; open depth split at the
printed lower end; base drop; storey term; mirror / rotation / mm / % / missing), adverse (joint in both / neither
refused, CONFLICT by majority refused, all readings kept, unknown class, % on 0, curved-piece end missing ->
NOT_DETERMINABLE, held piece as an allowance end refused), development villa from committed files (4 readings close per
mark and storey, merged reading = T-572, 1F % = 0.75 / 3.45, 10E0 moves the set, B7 allowance) and the private rebuild.

Lessons row (ERS s.7): | 2026-11-07 | a +21.7 % on 1F columns and a GF B7 -0.120 m3 UNTRACED stood as unexplained |
the column % was quoted without its height basis (his h = storey - one 0.75 head), and the beam support input carried
no ends for curved / ledger-only pieces | restate a family % as height basis + per-mark causes before calling it a
discrepancy; a beam remainder is UNTRACED only after every piece end (curved included) has a closing record; a measured
set is reported for every CONFLICT reading (every villa; provenance T-576, R-T576-1 .. 4) | tests/t576_column_causes |
PROPOSED |

## 7. Checker re-measure list

- GFRS: 30 SOLID outlines all on positions (T-566 input counts); his GF C1 / C2 / C9 rows vs his neck rows (private run).
- Ring ends: arcs 2EE / 2EF meet faces 437 / 46D / 42D obliquely, 312 / 313 meet 42D / 2A9 / 437; void 2F0 / 318 / 317
  touch 46D / 42D / 437 at single points.
- BAND0049 end 0 deg: line 484 against GF-112 (not a carrier); end 90 deg collinear with B2 BAND0027.
- `test_private_rebuild_equals_committed` with `.work/private/concrete_rebar.xlsx`.
