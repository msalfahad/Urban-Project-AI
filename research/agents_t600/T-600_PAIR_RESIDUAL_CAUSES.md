# T-600 column-beam pair residual (GF 0.620 + B7 0.120 / 1F 1.208 m3) split into physical causes

Worker 1 (lane S, non-candidate, backlog-permitted), 2026-11-07, run session_01E6cPndunKvSAjaBqztrywU, branch
`agents/task-T-600`. Research only: no engine module, candidate line, released line, rule register, method version or
frozen file changed; nothing released; no quantity moves. Development villa, not an accuracy claim. ERS s.2 - 4, s.7;
UP-CONC-JOINT-001 1.0.0 (T-599, LEAD_ADOPTED); R-T395-4; T-229; T-551 / T-572 / T-576; T-545; F-C-P02-1.

## 0. Sources and run

- Engine: ARCH_TAKEOFF_V3.0.58 (NOT RELEASED), beam lines through the merged T-545 reader, column lines / classes /
  A / D_ctrl through the merged T-551 reader, T-394 member binding, T-119 printed lower depths, T-252 ledger.
- Drawing (own read this run): Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179, `.work/private`
  only): every S-COL.BON outline by handle (drawn rectangle) and the route G beam bands (`bands.py`, fit <= 0.6 mm).
- Freelancer: the concrete + rebar workbook (sha256 ae608411, `.work/private` only): his beam excess per mark (as
  T-545) and his column marks (as T-551). Tracked output carries engine / drawing figures and terms in m3 only.
- Code: `t600_rules.py` (R-T600-1 .. 3, PROPOSED), `t600_alsenan.py` -> `out/T600_PAIR_RESIDUAL.json / .md`.

## 1. Physical element and question (ERS s.2.1)

The joint is the 3-D intersection of a column prism with the beams framing into it. The engine (column owns, slab top)
bills it once in the column line; he bills it in his beam rows run through the supports (columns stop 0.75 below the
slab top). T-599 matched J (A x D_ctrl over the compared column set) inside his beam THROUGH_SUPPORT T; the remainder
R = T - J per storey had no cause. Here every support his beam marks meet is measured on the drawing: the beam strip
(drawn band width) across the outline's extent along the beam axis (oblique bands in their own axis), inside / beside
the outline, x the printed depth; carriers at their drawn width; carried (planted / turned) members are not supports
(T-229: the beam line bills under them; a piece ending at one is read to the real column beyond it).

## 2. Result (m3, reference - engine sign; every table re-adds exactly; R-T600-1)

| Cause (class) | GF | 1F | Who is right (proposal) |
|---|---|---|---|
| Joint whose column partner is HELD (CONFLICT D-16 / D-63, GF 7 held C / C3 / C8 lines; 1F 10 held columns) | +0.485819 | +0.883632 | HELD: matched joint, the column line is blank, never 0 |
| Joint whose column has D_ctrl open (GF C7 368; 1F C8 664, C3 68B, P.C 20x50 69D), at the printed depth | +0.149875 | +0.259744 | RULE_DIFFERENCE matched at the printed LOWER_BOUND; open above (unprinted held members) |
| OVERLAP inside one column (two of his rows: crossing / same axis) | +0.767122 | +0.273311 | ENGINE_RIGHT where his rows reach (one solid billed twice) |
| BESIDE: his strip outside a narrower column outline (beam ends) | +0.544850 | +0.207487 | geometry named; owner per line (T-229 / T-610), not a joint |
| CARRIER crossings (his framing row through a carrier the carrier line bills) | +1.794125 | +0.223750 | ENGINE_RIGHT where realised (R-T610-1 owner) |
| UNCOVERED column head (A x D_ctrl under none of his strips; GF C11 35C 0.234 no beam row of his reaches) | -0.610719 | -0.006762 | ENGINE_RIGHT (in none of his rows) |
| SHORT: his rows stop inside the mark's support set (not apportioned: his rows carry no location) | -2.426751 | -0.667897 | named per mark, never 0 |
| BEYOND every drawn zone (GF B26 0.036555, CB5 0.000040; 1F CB12 0.035097) | +0.036595 | +0.035097 | UNRESOLVED by mark |
| **R = T - J** | **+0.740916** | **+1.208362** | |

T GF 3.022166 (statement 2.901714 + B7 0.120452), J GF 2.28125; T 1F 1.593362, J 1F 0.385 (both J reproduced member by
member). **The dominant cause is a SET difference, not a physical one**: of R, GF 0.635694 (85.8 %) and 1F 1.143376
(94.6 %) are joints his beams bill at columns whose engine line is HELD or D_ctrl-open, i.e. outside the J set; the
joint exists once, its column partner is simply not in the comparison. The physical remainder nets to GF +0.105222 /
1F +0.064986 = his double billing inside columns / at carriers (+) against column heads he never bills and rows that do
not run through (-). UNRESOLVED: only BEYOND, named by mark (GF 0.036595, 1F 0.035097).

Cross-checks: the 9 gap-side BESIDE strips measured here equal T-229's SUPPORT_CUT_BESIDE (383 0.0181 / 0.0184, 344
0.0572 / 0.0575, 368 0.0901 / 0.0900, 335 0.0943 / 0.0949, 688, 69A, 694, 68E) and are billed by the ledger beam runs,
so they are excluded from his zones (his excess over the engine cannot lie there). B26: the gap under carried 386 is
billed by the B26 run (T-229 +0.1798); its north end is read to C8 36E beyond the turned column 31B (outline 0.25
along the axis), not 31B's 0.90.

## 3. GF B7 0.120452 (F-C-T590-2) traced

With T-576's complete closing-face set (straight piece ends at C2 33E / C1 341 read here from the outlines, 0.149930;
carriers B8 BAND0003 / CB1 BAND0041.2 / B17 BAND0044.1 at drawn widths, 0.382500) the B7 zones are 0.532430 m3 against
his B7 excess 0.354452 (0.234000 + 0.120452): SHORT 0.177978, **UNTRACED 0.000** - the row is his B7 lengths running
into the carriers that close the curved pieces (members named), agreeing with T-576 (3.55 m x 0.20 x 0.75).

## 4. JOINT_HEAD readings (R-T600-3; Lead amendment)

| Storey | Reading | J m3 | minus record, by member |
|---|---|---|---|
| GF | T-551 (record) | 2.281250 | - |
| GF | T-572 | 1.883750 | C3 365 -0.0625, C3 36B -0.0500, C3 383 -0.09375, C8 36E -0.19125 (CONFLICT-reading marks out of the set) |
| GF | T-576 (10E0 = C8) | 2.033750 | as T-572, + C7 368 +0.150 (A 0.20 x printed D_low 0.75, LOWER_BOUND) |
| GF | T-576 (10E0 = C7) | 2.075000 | C3 x3 -0.20625 (C8 36E kept) |
| 1F | T-551 / T-572 | 0.385000 | - |
| 1F | T-576 (10E0 = C8) | 0.460000 | + P.C 20x50 69D +0.075 (LOWER_BOUND) |
| 1F | T-576 (10E0 = C7) | 0.595000 | + 69D +0.075, + C8 664 +0.135 (LOWER_BOUND) |

Every difference is a whole member entering or leaving the compared set; each member's joint is the same in every
reading. **1F 0.385 vs 0.460 (Verifier amendment 2)**: the drawing supports the 0.075 at 69D as a printed lower bound:
CB11 (0.30 x 0.75) and CB12 (0.25 x 0.75) both reach the P.C 20x50 outline (zones 0.100 / 0.050 m2 inside it) and CB11
alone covers its whole 0.10 m2 footprint, so the joint is >= 0.10 x 0.75 = 0.075 m3; it is open above only by the
unprinted depth of BM-1F-038 (0.10 strip outside CB12, D-26; BM-1F-035 candidates <= 0.75). The 0.385 record leaves
69D out of the set (HEIGHT_OPEN), it does not read a different depth. Neither reading is chosen: the physical joint
is the same; R moves between OUTSIDE_SET_OPEN and the set term by exactly 0.075.

## 5. 2F (cited, not re-derived)

0.420 m3 = his roof-beam lengths through the support-column footprints 0.564 less one drawn, tagged B1 run with no row
of his 0.144 (Checker verdict T-180 P02, F-C-P02-1). Column side: every 2F column line is HELD (D-39), J = 0: the
0.564 joint sits in held column lines (the same OUTSIDE_SET_HELD class as GF / 1F), never 0.

## 6. Verdicts, what is open

- No ENGINE_WRONG found: no fix row, no quantity change. ERS s.2.7 not met: **no owner question**.
- For the statement (proposal): restate each storey's pair residual by these classes; OUTSIDE_SET_HELD joins the
  HELD class of its column lines; OUTSIDE_SET_OPEN is RULE_DIFFERENCE at the printed lower bound; BEYOND stays
  UNRESOLVED by mark.
- Open: SHORT cannot be apportioned to supports (his rows carry no location), so OVERLAP / CARRIER are realised only
  where his rows run through; END-side BESIDE ownership (what the drawing holds beside a narrower column at a beam end)
  is per line (T-229 / T-610), not settled here.

## 7. Rules, tests, lessons row (proposed)

R-T600-1 (pair residual by zone, exact closure, each cause once), R-T600-2 (support zone from the drawn outline and
band; carried members are not supports), R-T600-3 (compared-set readings by member). `tests/t600` (16): hand villa
V600 (3 columns: crossing in K1 0.020 overlap / 0.007 uncovered, beam wider than K2 0.012 beside, K3 HELD 0.036;
R 0.067 = 0.151 - 0.084), mirror / rotation invariance, oblique strip, same-axis repeat; adverse (cause counted twice,
held as 0 / missing, mm, %, open sum, unknown class, one member with two joint values, empty outline); development
villa from the committed output (closure per storey / column / mark, J by member, B7 traced, readings reproduced, no
freelancer row tracked) and the private rebuild.

Lessons row (ERS s.7): | 2026-11-07 | a column-beam pair residual (GF 0.620, 1F 1.208 m3) stood as unexplained after
the joint rule | J was taken over a compared column SET while his beams run through every drawn support, held and
D-open columns included; allowance extents were read as max(w, d) and at carried members | reconcile a pair residual
support by support from the drawn outline and band; a joint whose partner line is outside the set is named (HELD /
open), never netted as a discrepancy; carried members are not supports (every villa; provenance T-600, R-T600-1 .. 3)
| tests/t600 | PROPOSED |

## 8. Checker re-measure list

- Largest physical cause: GF CARRIER crossings 1.794 (B4 0.420, B7 0.3825, B29 0.169, CB1 0.131): carrier widths at
  the B4 ends on ST7757 GF roof plan.
- 1F 69D: CB11 / CB12 bands reach the P.C 20x50 outline (zones 0.100 / 0.050 m2); GF B26 north end at C8 36E.
- `test_private_rebuild_equals_committed` with the three private inputs.
