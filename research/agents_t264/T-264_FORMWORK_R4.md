# T-264 formwork r4: the concrete components changed or added since formwork r3 (lane S; Alsenan; every villa)

Worker 1, 2026-10-24 09:24 .. UTC, branch `agents/task-T-264`. Research only: nothing wired, no released quantity
changes, no method version (lane I takes the line set into the candidate via T-199). Development villa, not an accuracy
claim.

Files: `formwork_r4.py` (rules + villa W `--check` + the Alsenan delta ledger from committed inputs), `t264_extract.py`
(private DXF + T-139 faces -> `ALSENAN_R4_INPUT.json`: lengths, areas, handles only), `FORMWORK_LINES_R4.csv` (361 lines:
r3's 283 with every change applied, columns `change` / `cause` / `refs`), `FORMWORK_DELTA_R3_R4.csv` (262 rows, each
REMOVED / CHANGED / NEW with r3 and r4 status, m2, range and cause), `summary_r4.json`. Tests: `tests/t264_formwork_r4`
(villa W normal + adverse; Alsenan pinned from committed inputs; the committed outputs equal a fresh build).

Repeat: `python3 -I research/agents_t139/slab_faces.py <ST.dxf> faces.json` (T-139, reproduces r3 byte for byte, checked
this run), `python3 -I research/agents_t264/t264_extract.py <ST.dxf> faces.json research/agents_t264/ALSENAN_R4_INPUT.json`,
`python3 -I research/agents_t264/formwork_r4.py research/agents_t264`. Source: Drive "Alsenan chalet project" /
"ST7757 dxf.dxf" (sha256 9f9d1179..., = manifest). r3 was re-run first on that copy: FORMWORK_LINES.csv,
JOINT_BY_COLUMN.csv and ledger_summary.json identical byte for byte.

## 1. Physical element and rules (ERS s.2.1, s.3)

Formwork contact area = the concrete surface cast against a form, from the SAME drawn geometry as the concrete line
that owns the element; soffits, sides, slab-edge bands and column joints apart; one owner per face (R-CONC-OWN-1, r3
D-T163-3). Below ground the owner question OQ-10 stays open: FORMED / EARTH_CAST carried as two alternatives, never
summed, never chosen. Three rules this task writes (proposed, research scope, any villa):

- **R-FW-CURVED-1**: a curved member's faces are its own drawn arcs (R x sweep) classed by what lies beyond each piece
  (slab: D - t; void / outside: full depth = D - t + the slab band, owned by the member; an equal or deeper beam: 0);
  its soffit is its plan area between its own edges. A chord offered for an arc is refused. A probe walk is not used
  where a void is tangent to a straight face (the probe reads the member's vanishing sliver as an exposed face).
- **R-FW-GB-EXPOSED-1**: a ground-beam face that stands above the outer natural ground (p.13 "Ground Beams for exterior
  walls": soffit on the "Outer Normal ground level", T-253 datum +-0.00) has nothing to be cast against: CALCULATED,
  outside OQ-10. A buried face is the OQ-10 pair; a face is EARTH_CAST as a fact only with the printed detail named
  (refused otherwise); where the panel beside a face is not established (GS-12 garden, GS-16 room-less), FORMED stays
  and the EARTH_CAST alternative is HELD 0 .. L D.
- **R-FW-STATUS-1**: a formwork face takes the status of the concrete reading it rests on, from the newest merged
  ledger: a section CONFLICT gives a perimeter range (never the larger end), a NOT_PRESENT member leaves with its source
  (never a 0 line), a planted column starts on the slab top it stands on, a held datum (D-39) holds the shaft (upper
  bound, no low end).

## 2. Delta r3 -> r4 by element (m2 contact area; full list in FORMWORK_DELTA_R3_R4.csv)

| # | Element (source) | r3 | r4 | Change and cause |
|---|---|---|---|---|
| 1 | GF void ring B7 soffit (T-252 MERGED b37be82d) | 0.275103 (GF-035 + GF-060 only) | **0.666406** | +0.391303: the 0.391 m2 ring part of the RING_MIX face GF-040 was in no line |
| 1 | ring B7 outer arcs to the slab (2EE 0.6494, 2EF 0.5653, 312 0.3696, 313 0.4643 = 2.0485 m) x 0.59 | 0.485975 (two pieces, probe-trimmed) | **1.208629** | arcs as arcs; straight outer pieces 46D / 42D / 2A9 / 437 lie on B8 / B17 / CB1 / B7 0.75 = covered |
| 1 | ring B7 void arcs (2F0 2.6750, 318 0.9233, 310 0.6827, 311 0.8641, 317 0.6185 = 5.7635 m) x 0.75 | HELD (RING_MIX) | **3.400487 side + 0.922166 band** | one owner for the opening face (D-T163-3) |
| 1 | CB1 (BM-GF-042) face the void reaches on 2A9: 1.3304 m x 0.75 | HELD (RING_MIX) | **0.784944 side + 0.212866 band** | the void's own straight piece |
| 1 | GF beam sides G line / GF slab-edge band line | 166.460 / 13.920 | **171.368085 / 15.055032** | +4.908085 / +1.135032 |
| 1 | GF RING_MIX held rows (6.463 m sides, 1.215 m edges); pool-court band HELD 1.090 .. 1.210 | HELD | removed / OWNED_BY_OTHER_LINE | measured on the ring and CB1 |
| 2 | B4 BM-GF-017 and CB4 BM-GF-021 span 1 ends on the oblique B27 face (T-252) | walk faces GF-153 0.5929 / GF-129 0.5020 | **unchanged** | the drawing-face walk already ran both edges to the carrier (27D 2.8907 / 282 3.0383; 288 2.3744 / 285 2.6454): route G's one-face end never reached formwork |
| 3 | main-house exterior G.B, 16 straight runs (T-242 / T-253, D 0.95) | 29 spans HELD 'per metre of depth' | **41.424 CALC** (outer faces above N.G., 14 runs) + **53.394 FORMED** (their 14 inner faces + both faces of 109+7CB#2 and 145+7CA#1, whose outer side is the room-less panel GS-16) | lengths face to face (T-230); exterior side = the side with no ground-slab panel (T-242) |
| 3 | ring G.B ARC:157+158 | HELD 'about 7.0 m' | **6.239008 CALC** (inner arc 157, R 2.25 x 167.236 deg = 6.5674 m, pool-court side) + **5.963657 FORMED** (outer arc 158, 6.6797 - 17BA 0.3002 - 17BD 0.1020 = 6.2775 m) | arcs as arcs; tee 177+7CD#2 on the outer face HELD -0.12 .. -0.09 |
| 3 | interior runs released at one p.13 class: 109+7CB#1, 17C+7E3#1, 7DC+7DD#2, 7E7+7E8#1, 7E9+7EA#1 | 3 of 5 FORMED (184+7CF#2 was the 4th) | **15.1224 FORMED** | T-242 lengths / classes; 184+7CF#2 now HELD (neck end-piece conflict, 2.053 .. 2.120) |
| 3 | interior HELD (D-33 / D-34), court (T-253 candidates), annex CONFLICT (9 runs, no value) | per T-141 | ranges per run; annex HELD unquantified (literal 2 L 0.25 shown, never adopted) | |
| 3 | tee covers (incoming end cast against a carrier side, 0.30 x min(D_in, D)) | one -0.240 row | 1 exact (-0.120, 109+7CB#1 on 7D0+FC#1) + 32 HELD (-4.230 .. -3.300) | per carrier and side |
| 3 | boundary G.B 44.07 m x 0.40 (T-253 DRAWING-CONFIRMED, p.14 A-A) | HELD 35.256 (concrete unresolved) | **35.256 FORMED / 0 EARTH_CAST** | buried both faces; soffit on the brick wall, top under the paving: no form; 810#1 west end HELD 0 .. 0.08; boundary-column share = line split only (M4) |
| 4 | straps SB1 / SB2 / SB3 (T-174, Q-74 axis length) | HELD 8.648 .. 9.449 | **9.4491 FORMED** + soffits HELD 0 .. 7.107 | covered footing faces F8 0.350, F11 / F6 0.5095 each, F15 0.2136, F3 0.1602 = **-1.7428 FORMED**; F10 + F HELD -0.35 .. -0.21 (replaces three -2.050 .. 0 rows) |
| 5 | FN 180C / F9 notch (T-233, one bottom stack) | HELD -0.450 .. 0 | **-0.450 FORMED** | both notch faces cast against each other |
| 5 | F10 + F outline 1B1B (T-239 CONFLICT) | HELD 4.200 .. 5.220 | **HELD 4.650 .. 5.220** | range = its two readings (outline 4.650, rows 5.220); F10 alone 4.200 is not a reading |
| 6 | 5 undrawn upper column lines (T-256 NOT_PRESENT) | 5 rows 0.0 NOT_APPLICABLE | **removed** | never a 0 line |
| 6 | 10 section-CONFLICT columns r3 released (GF-14 / 24 / 30, 1F-31 / 32 / 33 / 39 / 41 / 44 / 47) | 57.246 CALC | **HELD 55.371 .. 62.941** | drawn vs printed perimeter x r3 height; 5 already-held CONFLICT columns widened |
| 6 | 2F shafts COL-2F-51 / 53 / 54 (D-39 roof datum, T-248) | 15.470 CALC | **HELD <= 15.470** (no low end) | only the finished +13.90 is printed |
| 6 | planted COL-1F-57 P.C 20x70 (T-248 DRAWING-CONFIRMED) | HELD 6.210 | **6.210 CALC** + joint 0.766928 CALC | 1.80 x (4.20 - 0.75); the T-151 'planted stay HELD' rule superseded |
| 6 | 1F joint line (stated section) | 4.454 | **2.214828** + HELD 3.006 .. 3.496 (7 CONFLICT columns) | GF 3-column joint range 1.003 .. 1.180 -> 0.885 .. 1.180 |

**Totals (m2).** Above ground G CALCULATED **1,078.274 -> 1,015.963 (-62.311)** = ring +6.434, CONFLICT columns
-57.246, 2F roof datum -15.470, COL-1F-57 +6.210, 1F joints -2.239. Held above 221.507 .. 277.365 -> 270.036 .. 348.543
(+3 lines with no low end). Below ground: new CALCULATED (faces above N.G., outside OQ-10) **47.663**; OQ-10 FORMED
**103.140 -> 209.112** (footings 91.790 + boundary 35.256 + ground beams 74.480 + straps 9.449 - covers 1.743 - tee
0.120), EARTH_CAST 0; held below 162.640 .. 227.118 (34 unquantified) -> 125.818 .. 217.649 (12 unquantified). The
E method (802.658) is not re-based (comparison method on the T-149 spans; r4 changes G only).

## 3. Reconciliation (ERS s.2.4)

- **Ring B7, walk vs arcs.** A probe walk on the split face gives sides +5.102 / band +1.191; the arc method gives
  +4.908 / +1.135. The difference is the walk's error, traced: at the three points where the void is tangent to B7 /
  B8 / B17 (318 on 42D, 317 on 437, 2F0 on 46D) a 2 mm probe lands in the void over chords 2 sqrt(2 x 0.002 x R) =
  0.105 / 0.090 / 0.166 m = 0.364 m read as exposed (+0.215 sides, +0.058 band), less 0.021 m of void arc and 0.012 m
  of outer arc the walk trims at acute piece ends. Residual 0.000.
- **Freelancer.** No formwork row in any of his workbooks (r3, unchanged): FREELANCER_NO_ROW throughout; no %.
- **Owner manual method.** None on record for formwork; the two methods side by side stay E (element faces) and G
  (drawing faces).

## 4. Verdict proposals

| Line | Proposal |
|---|---|
| ring B7 soffit / sides / void band | HAND (arcs) RIGHT; r3 RING_MIX hold resolved by T-252; walk at tangents WRONG by +0.215 / +0.058 m2 (not used) |
| B4 / CB4 oblique ends | r3 G already RIGHT (no change); route G concrete was the line in error (T-252) |
| exterior G.B outer faces 47.663 | DRAWING-CONFIRMED geometry (T-253 datum), formed by R-FW-GB-EXPOSED-1; Checker to accept or reject the rule |
| everything below ground in OQ-10 | RULE_DIFFERENCE pending OQ-10 (FORMED 209.112 / EARTH_CAST 0) |

## 5. Held (never 0) and missing

Held: annex exterior 9 runs (D-35 annex CONFLICT), D-33 / D-34 runs, court runs (GS-16), EARTH_CAST alternative beside
GS-12 / GS-16, tee covers with an incoming candidate depth, strap soffits, 1B1B footing and its SB1 cover, the 810#1
end face, CONFLICT column shafts and joints, 2F shafts (D-39), COL-1F-58 (framing depth open), COL-2F-59 (D-39 + section).
Not done in r4 (changed earlier or not named by the row): pool walls / base on the VERIFIED T-183 geometry, lift-pit walls
(T-204), the ground slab panels GS-01 .. 29 (T-242: slab on fill between beam faces), the 1F dome ring faces, necks (still
HELD in T-248), the 4 annex columns T-248 also marks section CONFLICT but T-256 gives no drawn size for (their r3 ranges
carry the printed perimeter only), and the plot-line question for exterior outer faces (no neighbour structure is drawn).

## 6. Checker re-measure

(a) ring B7 sides from 'ST7757 dxf.dxf' arcs 2EE / 2EF / 312 / 313 (outer, R 1.935 / 1.75) and 2F0 / 318 / 310 / 311 /
317 (void), CB1 piece on line 2A9 between the ends of 310 and 311 (1.3304 m); (b) one boundary run, 7FE#2 8.10 m x 0.40
x 2 = 6.480 m2 FORMED (p.14 A-A: top at N.G., brick below); (c) one exterior run, 7E0+FD#2 3.25 m: outer face 3.0875 CALC
(p.13 soffit at 'Outer Normal ground level'), inner face 3.0875 FORMED beside GS-01.

## 7. Lessons register row (proposed, ERS s.7)

2026-10-24 | Formwork r3 carried 57.246 m2 of column shafts and 15.470 m2 of 2F shafts as CALCULATED on concrete
readings the newer column ledger holds (section CONFLICT, roof datum), and the GF void ring as a held RING_MIX face |
A derived trade (formwork) kept the statuses of the concrete ledger it was built on, not the newest merged one; a probe
walk was used where a void is tangent to straight faces | R-FW-STATUS-1 + R-FW-CURVED-1 (above; any villa) |
tests/t264_formwork_r4 (normal + adverse: chord for an arc, one-face end, earth-cast without a printed detail, NOT_PRESENT
member, planted column to the foundation, held never 0) | READY (Gate A pending).
