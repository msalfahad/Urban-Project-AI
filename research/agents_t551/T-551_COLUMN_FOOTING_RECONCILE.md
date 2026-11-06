# T-551 B10 column, neck, footing and blinding concrete: V3.0.58 against the freelancer, by component

Worker 1 (lane S, non-candidate, backlog-permitted), 2026-11-06, run session_01E6cPnc7M43PLLtBXeqvwoH, branch
`agents/task-T-551`. Research only: no engine, candidate, released line, rule file or method version changed; nothing
released. Development villa, not an accuracy claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied. Builds on T-394 (columns,
merged), T-233 (footings / blinding closure), T-478 (blinding plate), T-545 (beams, merged).

## 0. Sources and run

- Engine: candidate of record ARCH_TAKEOFF_V3.0.58 (NOT RELEASED); structural lines = `research/agents_t507/out/
  LINE_INDEX_V3_0_57.json` (V3.0.58 moves roof WP only, R-T507-1 (e)). GF / 1F column member data (mark, A, height,
  datums, D_ctrl) from the merged T-394 per-line record, joined by line id (every released line asserted A x h = m3).
- Freelancer: Drive "Alsenan chalet project", the concrete + rebar workbook, sheets 'footings' and 'walls + columns',
  downloaded this run, decoded into `.work/private` only, read with openpyxl (values and formulas, R-T541-1): every row
  is b x c x h x n and equals his cell (checked row by row); his sheet sub-totals equal his rows (no BM-ARITH here).
- Code: `t551_rules.py` (R-T551-1 .. 4), `t551_alsenan.py` (build + summary). The tables below were computed twice:
  by hand from the line index and his rows, and by the code from the private workbook; the test
  `test_dev_rebuild_equals_committed` asserts the two equal (they do, every term to 6 dp). Tracked
  `out/T551_COLUMN_FOOTING_RECONCILE.json` holds engine figures and terms only.

## 1. The physical elements (ERS s.2.1)

- Storey column: the solid inside its drawn outline from the ground-beam / slab top it stands on to the slab TOP it
  carries; the column line owns the joint + head because slab and beams are billed NET of its outline (R-T394-1,
  T-241). His columns stop one uniform soffit depth below the slab top on every storey (T-394).
- Neck: the column below the ground beam, from the footing TOP (the footing owns its depth) to the tie-beam top; all 36
  neck lines are HELD on the formation / founding depth (NO_SINGLE_VALUE, bound h 0.5 .. 2.5 m).
- Footing pad: drawn outline x schedule depth (T-233, 25 outlines measured, F10 + F outline 1B1B HELD, Q-31 C). The
  keyed footing line is wider: pads + straps SB1 - SB3 + the boundary band (his 'footings' sheet carries all three).
- Lift pit wall: the net ring 1.10 m2 (2.20^2 - 1.80^2 less the four lift column pieces 0.50 m2, which the lift necks
  own); depth 'as per lift manufacturer' (D-43): the LIFT_PIT:WALLS line is HELD blank.
- Blinding: 10 cm plain concrete under pads / beams; never part of a structural RC total (R-T551-3).

## 2. Component tables (engine - his, m3; every table re-adds exactly)

**Columns** (R-T551-1; COUNT = (drawn - his) x his section x his height; HELD = - held lines x the same; HEIGHT split)

| Component | GF | 1F | 2F | Total | Verdict proposal |
|---|---|---|---|---|---|
| COUNT (GF C1 -0.375, C2 -0.750, C9 -0.9375, C3 +0.46875, C11 +1.03125; 1F C3 -0.345, C7 -0.552, C8 +0.621, C9 +0.690) | -0.562500 | +0.414000 | 0 | **-0.148500** | ENGINE_RIGHT (labelled outlines, T-217 / T-394) |
| HELD (GF 4 CONFLICT + 5 annex; 1F 11 CONFLICT; 2F 9 on D-39) | -4.125000 | -4.623000 | -3.381000 | **-12.129000** | HELD, never 0 |
| JOINT_HEAD A x D_ctrl (column owns joint + head to the slab top) | +2.281250 | +0.385000 | 0 | **+2.666250** | RULE_DIFFERENCE (line ownership) |
| BASE (two CB5-line columns from +0.25, T-287 G1) | +0.192500 | 0 | 0 | **+0.192500** | ENGINE_RIGHT |
| GLOBAL_DEPTH (his one 0.75 soffit depth vs the member's D_ctrl 0.40 / 0.50 / 0.85) | +0.118750 | +0.095000 | 0 | **+0.213750** | ENGINE_RIGHT (owner method 'never a global depth') |
| HEIGHT_OPEN (D_ctrl not settled: GF C7; 1F C3 68B, C8 664, P.C 20x50) | +0.150000 | +0.285000 | 0 | **+0.435000** | traced, split open |
| SECTION | 0 | 0 | 0 | 0 | AGREE on every valued member |
| **Residual** | **-1.945000** | **-3.444000** | **-3.381000** | **-8.770000** | |

Engine valued GF 15.4925 / 1F 4.284 (incl. the planted PC-1F-A / -B) / 2F 0; his rows 17.4375 / 7.728 / 3.381.
HELD here follows the R-T394-2 convention: of -12.129, 10.34925 is his share on held lines his rows carry and 1.77975 is
held drawn members beyond his count of the mark (GF C3, 1F C8, 1F C9), carried back by COUNT. 1F C6 (held CONFLICT) and
the five storey-less CN columns (TYPE_NOT_IN_SCHEDULE; 3 bounded 0.378 .. 1.161 each) have no row of his.

**Since T-394 (V3.0.29 -> V3.0.58)**: the 15 printed-vs-drawn CONFLICT columns T-394 P1 named are now HELD bounded
(GF 4 lines 2.070 .. 2.475, 1F 11 lines 5.964 .. 7.644). Their volume moved from SECTION / HEIGHT / COUNT into HELD:
GF residual +0.530 -> -1.945, 1F +2.520 -> -3.444; T-394's UNRESOLVED -0.138 (1F C9 section) is now inside HELD.

**Necks**: engine 0 valued (36 HELD, bound 3.075 .. 15.375) vs his 8.805: **HELD -8.805**. His share lies INSIDE the
engine bound on every held line his rows carry; the engine draws one
C3 and one C11 neck more than his rows (2 held lines NO_ROW_OF_HIS). Uncertain, for the Checker: his C11 neck section
(his row) against the C11 neck section implied by the engine bound.

**Lift pit walls** (R-T394-6 on V3.0.58): his ring is the gross 1.60 m2: **SCOPE_DOUBLE -0.750** (the four column pieces,
also in his neck rows; ENGINE_RIGHT) + **HELD -1.650** (net ring 1.10 m2 x his depth on the HELD LIFT_PIT:WALLS line,
D-43) = -2.400.

**Keyed footing line** (R-T551-2): engine 67.6945 (pads 64.304 + straps 3.3905) vs his 77.6305 = **-9.936**:

| Component | m3 | Cause | Verdict proposal |
|---|---|---|---|
| COUNT F3 (2 drawn outlines) | +0.672 | T-233, both outlines tagged F3 | ENGINE_RIGHT |
| HELD F10 + F outline 1B1B | -1.960 | his F10 row alone; engine bound 2.176 .. 2.275: his share BELOW (the F pad in the same outline is in no row of his) | HELD (Q-31 C) |
| HELD boundary band | -8.604 | his row vs the held line bound 7.2204: his share ABOVE (T-065 / Q-28 A drawing range 5.639 .. 11.033) | HELD |
| OVERLAP FN 180C | -0.042 | FN notched 0.40 x 0.35 x 0.30 where F9 lies; F9 owns it (R-CONC-OWN-1); his four FN rows bill it again | ENGINE_RIGHT |
| LENGTH SB2 -0.0036, SB3 +0.0016 | -0.002 | drawn 2.2927 / 3.2580 m (T-231) against his rounded lengths | ENGINE_RIGHT |
| SB1 in F10 + F (0 .. 0.385), SB3 in F3 (0.0295 .. 0.2683) | 0 | held strap pieces inside footing outlines, no row of his | HELD, NO_ROW_OF_HIS |

The 20 Oct 'footing -0.37 UNRESOLVED' (released A 77.265 vs 77.631) is closed by name: on V3.0.58 the keyed line is
+0.672 drawn pad, -0.044 drawing-precision terms and -10.564 held, nothing unexplained. The pads alone: 64.304 vs his
pad rows 65.634 = -1.330 = +0.672 - 1.960 - 0.042.

**Blinding** (T-478 s.4 restated; V3.0.58 lines asserted equal to V3.0.45): engine 12.734438 valued (24 pits,
VERIFIED) vs his 47.055 plate (one layer over the plot rectangle, T-478) = -34.320562 = HELD -7.640374 .. -9.483519 (FF raft,
F10 + F in plot, ground beams plan-distinct, straps) + RULE_DIFFERENCE -26.680188 .. -24.837043 (one layer under the
whole plot that no sheet draws); closes at both held ends.

## 3. Overlaps counted once (acceptance; R-T551-3)

| Pair | Evidence | Result |
|---|---|---|
| column / slab | T-241 partition: 0.0000 m2 of slab inside any of the 59 outlines; column to the slab TOP with slab NET | once, column line |
| column / beam | T-229 DOUBLE joints deducted from the beams, column owns (T-545: GF columns 347, 350, 356, 359, -0.2116 m3) | once; all four owning columns are now HELD lines, so that joint volume sits in held column lines, never dropped |
| neck / GF column; neck / footing | T-387 R-T387-4; neck from the footing top | once |
| FN / F9 | F9 owns the notch (T-233) | once (engine); twice in his rows (OVERLAP) |
| lift column pieces / lift ring | R-T394-6 | once (engine); twice in his rows (SCOPE_DOUBLE) |
| blinding / structural | plain concrete, separate family | refused inside a structural total (test) |

**Column / beam pairing per storey** (the T-545 hand-over): column JOINT_HEAD vs beam THROUGH_SUPPORT (his beam lengths
through column and carrier footprints): GF +2.281 - 2.902 = **-0.620**, 1F +0.385 - 1.593 = **-1.208**, 2F 0 - 0.533 =
**-0.533** m3. The joint + head on the valued columns is the most of his beam-through volume that can sit over valued
columns; the rest of THROUGH_SUPPORT is over held columns (their joint volume is inside HELD here) and over carrier
beams (beam / beam). The per-crossing split (which run passes which column) is NOT done: it needs the T-229 support
input per run beside his beam rows (proposal for the Checker / a follow-up, no quantity moves).

## 4. Who is right, what is open

- ENGINE_RIGHT: column COUNT -0.149, BASE +0.193, GLOBAL_DEPTH +0.214; footing COUNT +0.672, OVERLAP -0.042, LENGTH
  -0.002; lift SCOPE_DOUBLE -0.750.
- RULE_DIFFERENCE: column JOINT_HEAD +2.666 (ownership; its counterpart is part of T-545's -5.028 THROUGH_SUPPORT);
  blinding plate -24.837 .. -26.680.
- HELD (never 0): columns -12.129, necks -8.805, lift walls -1.650, F10 + F -1.960, band -8.604, blinding -7.640 ..
  -9.484. Causes already on the designer / owner lists (D-39, D-43, Q-21 formation, Q-31 C, Q-28 A, D-16 / D-63 column
  sections, D-14 / D-15): ERS s.2.7 not met, **no owner question**.
- TRACED, split open: column HEIGHT_OPEN +0.435 (D_ctrl not settled on 4 members).
- No ENGINE_WRONG found: no fix proposal, no quantity change. UNRESOLVED: 0.000 in every table.
- Uncertain: held-line rows are bound to his rows by count per mark, not by position; the classes (INSIDE / BELOW /
  ABOVE) are information only.

## 5. Rules, tests, lessons row (proposed)

R-T551-1 (column split per storey and mark, held CONFLICT columns in HELD, never SECTION), R-T551-2 (footing line split,
a per-piece remainder needs a drawn cause else UNTRACED), R-T551-3 (column / slab once, neck from the footing top,
blinding never structural, m3 only), R-T551-4 (held bound beside his row). `tests/t551_column_footing_reconcile` (20):
hand villa V551 (footing 2.00 x 1.80 x 0.50 + neck 0.30 x 0.50 x 1.20 + column 0.25 x 0.50 through a 0.20 slab:
6.3925 m3 both conventions; column split +0.18 = +0.32 - 0.32 + 0.18 + 0.06 - 0.06; footing split +0.80), adverse
(column-slab twice / nowhere, neck from the footing bottom, blinding in a structural total, mm / kg / %, held as 0,
missing, open sum, line not A x h, mirror / rotation), development villa from committed files, and the private rebuild.

Lessons row (ERS s.7): | 2026-11-06 | footing -0.37 m3 stood UNRESOLVED since 20 Oct and the column residuals moved
sign between candidates | the keyed footing line mixes pads, straps and the boundary band; a candidate that holds
CONFLICT columns moves their volume into HELD | a family residual is split per mark into COUNT / HELD / SECTION /
HEIGHT (or a drawn per-piece cause) on the candidate being compared, never carried from an older candidate's split
(every villa; provenance T-551, R-T551-1 .. 4) | tests/t551_column_footing_reconcile | PROPOSED |

## 6. Checker re-measure list

- Re-run `test_dev_rebuild_equals_committed` with the workbook at `.work/private/concrete_rebar.xlsx`.
- GF C11: two outlines 35C / 37D (1.10 x 0.25) against his one row (COUNT +1.031); 1F C9 two outlines (667, 679).
- FN 180C notch 0.40 x 0.35 (T-233) and SB2 drawn 2.2927 m.
