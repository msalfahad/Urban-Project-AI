# T-600 (r2) column-beam pair residual (GF 0.620 + B7 0.120 / 1F 1.208 m3) split into physical causes

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

## 2. Result (m3, reference - engine sign; every table re-adds exactly; R-T600-1 r2)

r2 (Verifier 2026-11-07T23:58Z): carriers are entered once per physical node at the drawn crossing on the framing axis;
SHORT is not a cause (it is capacity minus his volume, UNRESOLVED per group of marks). The r1 percentage headline
("85.8 % / 94.6 % set difference") is withdrawn: which zones his rows reach is unknown, so no class is apportioned to
his rows as a share.

| Term (class) | GF | 1F | Status |
|---|---|---|---|
| Zone at a HELD column partner (CONFLICT D-16 / D-63) | +0.485819 | +0.883632 | CAPACITY at HELD lines (never 0) |
| Zone at a D_ctrl-open column, printed depth | +0.149875 | +0.259744 | CAPACITY at the printed LOWER_BOUND |
| OVERLAP inside one column (two of his rows: crossing / same axis) | +0.767122 | +0.273311 | CAPACITY (realised only where both rows run through) |
| BESIDE: strip outside a narrower column outline | +0.544850 | +0.207487 | geometry named; owner per line (T-229 / T-610) |
| CARRIER_NODE: drawn crossings, once per physical node | +1.720971 | +0.188034 | CAPACITY (r1 1.794125 / 0.223750) |
| UNCOVERED column head (A x D_ctrl under none of his strips) | -0.610719 | -0.006762 | ENGINE_RIGHT (in none of his rows) |
| UNRESOLVED_SHORT: capacity - T per group of marks | -2.353597 | -0.632181 | UNRESOLVED by group, per-mark bounds |
| BEYOND every drawn zone (GF B26 0.036555, CB5 0.000040; 1F CB12 0.035097) | +0.036595 | +0.035097 | UNRESOLVED by mark |
| **R = T - J** | **+0.740916** | **+1.208362** | unchanged from r1 |

T GF 3.022166 (statement 2.901714 + B7 0.120452), J GF 2.28125; T 1F 1.593362, J 1F 0.385 (J reproduced member by
member). Each storey residual is the sum of the capacity terms above less the UNRESOLVED shortfall. The statement's
2.248826 m3 (GF 0.620464 + 1F 1.208362 + 2F 0.420000; B7 0.120452 traced separately, s.3) stays UNRESOLVED as a total;
only the parts in s.6 - 7 are bounded or named.

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

## 6. r2: carrier node census (R-T600-1 r2)

Every carrier entry is re-read on the drawing as the parallelogram where the framing strip (drawn lateral range,
extended on its own axis) crosses the carrier strip; its length on the framing axis is w_carrier / sin(theta).
Orthogonal entries agree with the T-229 recorded extent to <= 7 mm (e.g. B4 -> B22 0.498, -> B26 0.651, -> B21 0.407,
-> B11 0.200, -> B16 0.298 m); oblique ones do not: B27 (0.90 wide, sin 0.805 = 53.6 deg) is crossed over 1.119 /
1.120 m (B4 / B5), not 0.90. CB8 -> CB7 is collinear (no crossing): kept at the recorded 0.20, labelled RECORDED_PARALLEL.
Entries whose plan polygons share area are one node, capacity = depth-layered union once:

| Node (storey) | Marks entering | Capacity | Entries sum | Entered more than once |
|---|---|---|---|---|
| B27 crossing at the B4 / B5 line (GF) | B4 BAND0018, B5 BAND0017, CB4 BAND0021.1 | 0.243784 | 0.375801 | 0.132017 |
| B22 BAND0045 at y 37.85-38.05 (GF) | B4 BAND0018 (D 0.50), CB3 BAND0019.1 (D 0.75) | 0.074690 | 0.124525 | 0.049835 |
| 1F BAND0031.2 at x 18.37 (1F) | B2 BAND0005.1 (0.20 x 0.40), CB13 BAND0024.2 (0.30 x 0.50) | 0.067425 | 0.103178 | 0.035753 |

B27 node: B4 / B5 alone = 0.20 x 1.120 x 0.50 = 0.1119 (the Verifier's 0.112, r1 had 0.180); CB4 enters the same B27
crossing from the north on its own axis (0.90 / sin 36.4 = 1.518 m, 0.1518 m3) and shares 0.040 m2 with the B4 / B5
parallelogram: union 0.4876 m2 x 0.50 = 0.2438. Every other multi-entry position the Verifier listed was checked and is
a separate node: BAND0045 is entered at four positions (B29 y 42.0, B3 y 43.0, B4 + CB3 y 37.85: one shared node);
BAND0042 by B29 (y 42.0) and B4 BAND0010 (y 43.2); BAND0014 by B4 BAND0012 (x 49.5), B4 BAND0030.1 (x 46.3) and CB8
(collinear); BAND0048.1 by B5 + CB4 (the B27 node above). B7's eight closing-face entries keep T-576's verified widths
and are eight distinct nodes: the ring arcs end on face 46D at y 48.005 / 46.291, on 42D at x 71.734 / 72.862, on 2A9 at
y 46.098 / 48.198 (own DXF read of arcs 2EE / 2EF / 312 / 313), and even a +-0.20 m superset of each ring continuation
overlaps no other entry. One sliver: the B20 -> BAND0025.1 crossing shares 0.0001 m2 with the B7 column zone at BAND0025.1
(edge contact, < 0.0001 m3, printed in the notes).

Effect: CARRIER GF 1.794125 -> 1.720971 (-0.073154), 1F 0.223750 -> 0.188034 (-0.035716); the shortfall rises by the
same amounts; R unchanged.

## 7. r2: SHORT restated as capacity bounds; per-mark proposals

Marks sharing a node form a group: GF B4 + B5 + CB3 + CB4 (group capacity - T = 0.634737 m3), 1F B2 + CB13 (0.187789);
every other mark is its own group. Per mark the shortfall lies in [exclusive capacity - T, + its shared entries]:
B4 0.267944 .. 0.429706, B5 0.016666 .. 0.128647, CB3 0.005718 .. 0.080433, CB4 0.025935 .. 0.177803; 1F B2 0.112625 ..
0.148513, CB13 0.007739 .. 0.075029. B4's r1 "SHORT 0.407324" is therefore not a figure for B4 alone.

Who-is-right per mark only where the mark is its own group and |SHORT| <= 0.01 m x b x D (his row runs through every
zone within the drawn-edge tolerance): GF B2 (0.000073), CB5 (-0.000040), CB7 (0.000046). CB6: SHORT 0.030000 equals its
one carrier entry CB6 -> BAND0028 0.029985 within tolerance: CONDITIONAL (his row runs through both column zones and
stops at the carrier face; the split is not unique, PLAUSIBLE only). For these marks, per column (out/T600_PAIR_RESIDUAL.md):
REC columns (B2 at C2 32C / 32F, C1 341, C3 36B; CB5 at C5 35F, C3 365; CB6 at C5 35F) RULE_DIFFERENCE (the joint the
engine column line bills once, his beam row bills it; no quantity error); HELD columns (B2 at C 34A / 356; CB6 at C3 353;
CB7 at C 34D / 359) HELD, never 0; BESIDE slivers named geometry. No overlap is realised between two strictly run-through
marks; CB5 / CB6 at C5 35F (0.015990 m3) is ENGINE_RIGHT only if CB6's conditional run-through holds. Every other mark:
capacity bound only, SHORT UNRESOLVED.

## 8. Verdicts, what is open

- No ENGINE_WRONG found: no fix row, no quantity change. ERS s.2.7 not met: **no owner question**.
- Statement (proposal): keep 2.248826 m3 UNRESOLVED; print per storey the capacity terms above and the UNRESOLVED
  shortfall by group; OUTSIDE_SET_HELD joins the HELD class of its column lines; OUTSIDE_SET_OPEN is RULE_DIFFERENCE at
  the printed lower bound; BEYOND stays UNRESOLVED by mark.
- Kept as VERIFIED (cited, not redone): 1F 69D joint >= 0.075 m3 LOWER_BOUND; per-storey closure GF 0.740916 / 1F
  1.208362; B7 traced (UNTRACED 0, group SHORT 0.177978).
- Open: which zones his rows reach (his rows carry no location); END-side BESIDE ownership per line (T-229 / T-610, and
  T-614 for narrow corner columns).

## 9. Rules, tests, lessons row (proposed)

R-T600-1 (pair residual by zone, exact closure, each cause once; r2: carrier capacity once per physical node at the
drawn crossing on the framing axis, SHORT not a cause, bounds per mark), R-T600-2, R-T600-3 (unchanged). `tests/t600`
(21): r1 hand villa V600 and adverse cases; r2 hand cases: oblique crossing 0.90 / sin 53.6 = 1.118160 m (not 0.90),
parallel refused; two collinear marks into one node counted once (0.111816 vs entries 0.223632), a third oblique mark
joins by union; adverse 'one node, two marks' refused, shared node with drawn width != his b refused, entry twice
refused, SHORT as a cause class refused; development villa: B27 / B22 / 1F shared nodes, every entry in one node, group
closure, per-mark bounds, proposals only where SHORT ~ 0; private rebuild equals the committed output.

Lessons row (ERS s.7): | 2026-11-08 | a carrier crossing entered once per framing mark doubled one physical node (B27
at the B4 / B5 line, +0.068 m3) and a balancing SHORT was read as a cause | crossings were keyed by mark and measured
on the recorded perpendicular extent; the closure term was given a physical label | measure a crossing on the framing
axis (w / sin theta), census nodes by plan position across marks and enter each once; a balancing term is UNRESOLVED
with bounds, never a cause (every villa; provenance T-600 r2, R-T600-1 r2) | tests/t600 | PROPOSED |

## 10. Checker re-measure list

- B27 node: B4 / B5 crossing x 56.510-57.630 (0.20 x 1.120 x 0.50 = 0.112) and CB4's share (x 57.093-57.294).
- B22 node at BAND0045 (B4 + CB3, x 60.594-61.092, y 37.848-38.048): 0.0996 m2 x 0.75 (CB3 deeper) = 0.0747.
- 1F BAND0031.2 node (B2 inside CB13, x 18.368-18.668): 0.1348 m2 x 0.50 = 0.0674.
- `test_private_rebuild_equals_committed` with the three private inputs.
