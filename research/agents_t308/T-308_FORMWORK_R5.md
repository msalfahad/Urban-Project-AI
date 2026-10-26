# T-308 Formwork r5 research rows: one consolidated set by candidate concrete line, for T-199 (lane S; Alsenan; every villa)

Worker 1, 2026-10-26 02:22 .. UTC, run unknown, branch `agents/task-T-308`. Research ledger: nothing wired, no candidate
or released line changed, no method version, no quantity released; formwork r3 / r4 and the three T-293 part ledgers are
untouched (r5 is new files). Integration dependency of T-199 (formwork is a BOQ category the candidate lacks).
Development villa, not an accuracy claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied.

## 0. Inputs and commands

| Input | Merged as | Used for |
|---|---|---|
| FORMWORK_FACE_TO_LINE_T293.csv / _P2.csv / _P3.csv | T-293 parts 1 / 2 / 3: 294da634, a1e0c43a, 02f3e47e | the source of every r5 row (414 + 928 + 70 records) |
| summary_t293.json `closure` | part 1 | the 384 source rows (r4 361 + T-282 21 + T-290 2) per status / alternative / method |
| CANDIDATE_V3016_CONCRETE_LINES.json + T-254 per-line table (49 rows) + CANDIDATE_V3018_STAIR_DOME_LINES_T293P3.json | parts 1 / 3, T-254 Gate B 13:35, T-266 | the current candidate line state (V3.0.18) of every line a face is tied to |
| 'ST7757 dxf.dxf' (Drive "Alsenan chalet project", sha 9f9d1179, decoded into `.work/private` only) | - | BAND0049 read by handle; the r3 walk re-run (T-139 faces + route G bands) |

```
python3 -I research/agents_t139/slab_faces.py <ST7757 dxf.dxf> faces.json
python3 -I research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g bands.json
python3 -I research/agents_t308/t308_walk_delta.py faces.json bands.json --write   # T308_WALK_DELTA_BAND0049.json
python3 -I research/agents_t308/t308_r5.py --write                                 # the four r5 outputs
```

Outputs: `FORMWORK_R5_BY_FACE_T308.csv` (every row: r4 status / value, the merged ledger's tie, r5 status / value /
line / line state, rule, cause), `FORMWORK_R5_BY_LINE_T308.csv` (per candidate line x status x alternative x method: r4
before, r5 after, r5 held_from, delta, rules), `T199_FORMWORK_BY_LINE_T308.json` (the T-199 consumer: per line its r5
faces and totals; not-tied rows; the removed rows with rule and cause), `summary_t308.json`.

## 1. Physical element and the question (ERS s.2.1)

A formed face is a concrete surface cast against a form; it bounds ONE member and is reported beside the candidate line
that carries that member's concrete. Question: which formed faces exist physically, each once, on which candidate line;
r5 = the merged face-to-line ledgers with every Checker-confirmed correction applied once by a named rule
(`t308_rules.py`, R-T308-0 .. 6), never by a hand edit of a row.

## 2. Result: r4 before / r5 after by status and method (m2; never summed across status / alternative / method)

| Status, method | r4 (source rows) | merged ledgers | r5 | r5 - ledgers, by rule |
|---|---|---|---|---|
| CALCULATED E (element method) | 425.209420 | 425.209420 | **422.693420** | R-T308-1 -2.516 (CB5 span 2 once) |
| CALCULATED E=G | 418.871805 | 418.871805 | **418.871805** | 0 |
| CALCULATED G (drawing faces) | 644.933811 | 629.999558 | **626.872989** | R-T308-2 -2.797014, R-T308-3 +2.927816, R-T308-5 -3.257371 |
| ALTERNATIVE OQ-10 FORMED E=G | 205.461205 | 205.461205 | **170.205205** | R-T308-6 + 5 -35.256 (boundary G.B held with its line) |
| HELD G (low .. high) | 270.036689 .. 348.626311 | same | **269.659765 .. 348.249429** + held_from 18.191624 | R-T308-3 -0.376924 .. -0.376882 |

r4 G 644.934 vs ledgers 629.999: the 62 pieces parts 2 / 3 already held (held_from kept). Closure (asserted in the
build): (1) the union of the three parts reproduces every one of the 384 source rows to 0.0005 m2 per row (unrounded
pieces vs 3-dp printed rows: E -0.00058, E=G +0.0001, G -0.000445, held G +0.000662 / +0.002839, named in the summary);
(2) r5 = merged ledgers + the rule deltas per (status, alternative, method), residual 0.000000. 1,301 union rows + 4
BAND0049 pieces = 1,305 r5 rows: 715 CALCULATED, 109 ALTERNATIVE, 439 HELD, 25 REMOVED, 17 information / scenario /
not-applicable rows. 351 candidate lines carry faces.

## 3. Corrections, each by its rule (r4 before -> r5 after)

**(1) CB5 span 2 once (R-T308-1; F-T293-P2-01, Checker 23:00 CONFIRMED on drawing and code).** Line
L-3e9076546ea34d8cbcc7 (BM-GF-035.2 CB5 span 2): E 5.032 -> 2.516 m2 (soffit 0.20 x 3.70 = 0.740 and sides 2 x 3.70 x
(0.40 - 0.16) = 1.776, once). The two DUPLICATE_IN_SOURCE rows R4-253.R138.DUP / R4-255.R138.DUP are REMOVED. G unaffected.

**(2) Stair rows: drawn soffit only (R-T308-2; F-T293-P3-01, Checker 01:55 own-checked ST-02 RS-S).** The r4 stair rows
print 44.533 m2 CALCULATED; 8.086 of it lies on the two held stair lines (MS1-L 5.706, E1 risers 2.380: HELD with the
line, R-FW-P3-1). On the six closable lines r4 36.447 -> r5 **32.822036 m2** (-3.624964, -9.9 %), every m2 named:

| Cause | m2 | r5 |
|---|---|---|
| inside another member, no surface (B20 / B23 / column 374) | 0.783422 | REMOVED |
| under a member whose own rows hold it (B3 'With Stair' GF-159, CA) | 1.914913 | REMOVED (the beam rows keep it) |
| readings the concrete ledger retired (MS2-LD 0.480, RS-A 1.25 width, RS-LD pre-r2) | 0.203246 | REMOVED |
| held pieces of closable lines (columns 691 / 380 D-16, unmarked layer-5 pairs) | 0.722950 | HELD, held_from kept |
| r4 print rounding | 0.000433 | REMOVED |

Per line: ST-02 L-056402f9 10.321 -> 7.546233; MS1-LD + MS1-U L-e37d81a8 8.370 -> 8.095527; MS2-L L-67e4b048 6.958 ->
6.722695; MS2-U L-bb0e57b1 6.958 -> 6.682581; MS2-LD L-2416e65f 3.000 -> 2.935; D1 steps 0.840 unchanged. The two T-290
pointer rows (-0.065 / -0.040) are REMOVED (their correction is the retired piece above, never a second one): the
R-T308-2 delta on CALCULATED G is therefore -2.902014 + 0.105 = -2.797014.

**(3) BAND0049 ruled from the drawing: a drawn face (R-T308-3; F-T293-P2-02 UNRESOLVED -> resolved).** Own read of 'ST7757
dxf.dxf', ST p.4 GF roof slab, by handle: BAND0049 is NOT a void-ring piece (the T-110 register type and the r3
hard-code 'B7 ring band' call it so; T-252 found it outside the ring, 25 m away). It is a quarter-circle corner beam
between the B2 run (lines 29E / 2B9) and the beam strip 2B2 / 2B3: arcs **29F R 1.300 and 2A0 R 1.100, centre on the
corner, 0 .. 90 degrees**, closed by line 314 (beside column COL-GF-15) and line 484; mark block 47D 'b7' 0.135 m
outside the outer arc. Width 1.300 - 1.100 = 0.200 = B7 20 x 75 (ST p.10); centre-line length 1.200 x pi / 2 = 1.885 =
the T-110 / T-149 R056 length (two sources agree). Its plan is T-139 face **GF-095** (0.376924 m2 polygonised; exact
pi / 4 (1.300^2 - 1.100^2) = 0.376991), which the r3 walk left UNMATCHED (tag outside the face, B7 not a unique mark,
and a curved member has no H / V rectangle for the band search). Route G's band BAND0049 covers 99.49 % of GF-095 and no
other band touches it. The merged walk re-run unbound reproduces T293P2_WALK_RECORDS.json exactly (785 records); bound
(GF-095 -> BM-GF-049) only these records change:

| Walk record | before | after (r5) | Hand check |
|---|---|---|---|
| GF-095 UNMATCHED_PLAN (R4-275 piece, HELD, no line) | 0.376924 | - (becomes the soffit) | |
| GF-095 BEAM_SOFFIT -> BAND0049 line, CALCULATED | - | **0.376924** | 0.376991 exact arcs (chord -0.000067) |
| GF-095 BEAM_SIDE (inner arc beside slab GF-105, outer free edge, below the 0.16 slab) | - | **2.224174** | (1.727876 + 2.042035) x 0.59 = 2.224248 |
| GF-095 EDGE_BAND (outer free edge x 0.16, the beam's own face, R-FW-P2-2) | - | **0.326718** | 2.042035 x 0.16 = 0.326726 |
| GF-095 end against GF-112 (depth not printed, line BOUNDED_EXPOSURE) | - | HELD 0 .. **0.118** | 0.200 x 0.59 |
| GF-093 COL-GF-15 joint face next to UNMATCHED (R4-268 piece, HELD 0 .. 0.117958) | 0 .. 0.117958 | REMOVED | D_ctrl 0.75 - B7 D 0.75 = 0 (r3 joint rule) |
| GF-095 UNMATCHED_LEN 3.769787 m (a length, no m2 row) | 3.769787 m | - | arcs 3.769911 m |

BAND0049 line L-5bc1baae70fcc325abea (PROVISIONAL 0.282743 m3 = 0.37699 x 0.75): E 2.6013 (soffit 0.377 + sides
2.2243) and now G 2.927816 = soffit + sides 2.601098 (E agrees to -0.000202, polygonised arcs) + edge band 0.326718
(which E leaves HELD, OQ-12). Verdict proposal: ENGINE_WRONG (r3 walk binding of curved members); BAND0049 concrete
identity confirmed by its drawn face.

**(4) TANK row = beam B15 (R-T308-4; F-T293-P3-03 re-measured this run).** Own read, ST p.6 2F roof slab: tag 7A9 'B15'
beside the strip between lines 397 / 3AD (0.200 apart), clear between column outlines 424 (top face) and 40F (bottom
face) = 2.700 m; the panel east of it is 2F-011 'T 18 (T&B)' = the water-tank slab. E soffit 0.20 x 2.70 = 0.540 and
sides 2 x 2.70 x (1.20 - 0.16) = 5.616 = part 2's R4-298 / R4-300 rows on L-713bc64aaa210610e7fe; G sides 3.978806 =
east 2.70 x (1.20 - 0.18) = 2.754 + west free edge 1.2008 x 1.02 = 1.2248 (band 1.2008 x 0.18 = 0.21615), the other
1.50 m of the west side HELD next to the break-line sliver 2F-008 and the edge strip 2F-031 (0 .. 0.765 each). The r4
'water-tank walls (B15 20 x 120 up / down)' row names the same member and carries no value: same physical faces ->
REMOVED; D-44 (up- or downstand) stays on B15's faces. No other tank wall is drawn (D-44 / D-52): no face.
Note F-T308-02 (no change): E as written (UP-FW-001 draft, struct_n10) takes D - 0.16 on both sides; beside the printed
T 18 panel the east side is 2.754, not 2.808 (E -0.054 m2 there). Only two panels print 0.18 (2F-011, 2F-013). E stays
the method as written; G carries the printed thickness; side by side, never chosen.

**(5) Faces held with their line (R-T308-5 = R-FW-P3-1, Checker 01:55 'one rule for held lines').** The 26 part-2
CALCULATED pieces on lines whose concrete carries no quantity in V3.0.18 (edge bands of CB2 BM-GF-055 runs, 2F / GF
column joints on lines V3.0.17 holds, U-C beam runs) become HELD, blank, held_from **3.257371 m2**; their line_flag is
superseded. Part 1 and part 3 already held such faces. No face is tied to a NOT_APPLICABLE line (refused by the build).

**(6) Boundary G.B re-tied to its added line (R-T308-6).** V3.0.17 added the HELD line L-fb7a6431fede62e93fd5
(T254:GROUND_BEAMS:GROUND:BOUNDARY_GB_NG, M4 boundary columns; id recomputed with `boq_line.line_id`): the 5 runs'
OQ-10 FORMED 35.256 m2 (EARTH_CAST 0) and the 810#1 end HELD 0 .. 0.08 move from NO_CANDIDATE_LINE to that line, HELD
with it (held_from 35.256). Part 1 finding (2) (16 main-house exterior GB lines at the interior depth) is closed by
V3.0.17: those lines now carry D 0.95 (DRAWING-CONFIRMED), the same basis as their faces.

Still listed, never 0 (`summary_t308.json` live_concrete_lines_without_faces, 81): the 35 necks (one held aggregate row,
Q-21 C), 25 ground-slab lines (cast on blinding; no slab-edge form row in r4), the D-05 / D-26 strips (BM-GF-058 two runs,
BM-1F-033 two runs, BM-1F-036 / 037 / 038, BM-2F-019), U-C beam / column runs with no walk face, two straps inside
footings, the pool steps, and ARC:139+13A in BAND0013.1 / BAND0042 (SPLIT_UNRESOLVED). Drums: NO_CANDIDATE_LINE.

## 4. Owner manual method vs drawing method (ERS s.2.3); freelancer

No owner rule measures formwork; the freelancer has no formwork row (FREELANCER_NO_ROW, no %). The two drawing-derived
methods E (element faces) and G (drawn faces) stay side by side, never summed, never chosen by size; OQ-10 FORMED /
EARTH_CAST stay alternatives.

## 5. Verdict proposals

CB5 span 2 ENGINE_WRONG (r3 / r4 E, fixed in r5); stair rows ENGINE_WRONG (r4, fixed in r5); BAND0049 ENGINE_WRONG (r3
walk binding; face found, G 2.927816 CALCULATED); TANK row a duplicate view (removed); B15 E vs printed T 18 a method
note (-0.054 m2, unchanged). Freelancer: FREELANCER_NO_ROW.

## 6. Rules, tests, lesson

Rules R-T308-0 .. 6 and the guards (`t308_rules.py` docstring; research scope, any villa; provenance T-308 on T-293 /
T-163 / T-264). Tests `tests/t308_formwork_r5` (25): villa V308 by hand (NORMAL: a continuous beam over three supports
in two runs, S1 0.600 + 2.100 on L1, S2 0.800 + 2.800 on L2 once, r4 2.200 / 7.700; a stair flight under band beam B1,
drawn soffit 3.12 x sec 1.118034 = 3.488266 on the stair line, 0.536656 under the band removed, the beam keeps 0.480; a
column face on a BLOCKED line HELD with held_from 1.250; a boundary face re-tied to its added line and held; union
replaces NAMED rows; band binding; mirror order. ADVERSE: a shared span booked twice refused; a soffit under a band
beam on both rows refused; a measured face with no drawn evidence refused; a removed kind left tied refused; a held face
as 0 refused; a face on a NOT_APPLICABLE / unknown line refused; a key in two parts refused; band binding below 95 % /
two bands / none -> unmatched) and Alsenan pinned (union and closure, CB5, the stair split, BAND0049 with first-principle
checks, TANK = B15, the 26 holds and the boundary, states, committed outputs = fresh build, no coordinates).

Lessons row (proposed, ERS s.7): 2026-10-26 | A curved corner beam (BAND0049, B7 quarter circle R 1.10 / 1.30) had
element faces but no drawing face for four revisions; it was carried as a 'void ring arc piece' by a register type and a
hard-coded r3 binding | The drawing-face walk bound band faces by an inside tag or an H / V axis rectangle, so a curved
member whose tag sits outside its face matched nothing, and a type label was trusted over the drawn position | Bind an
unmatched band face to the one member whose band covers it (>= 95 %, no other band), never by a type label; re-run the
walk with that binding only and prove every other record unchanged (PROJECT-INDEPENDENT) | tests/t308_formwork_r5
(band binding normal / adverse; Alsenan walk delta 781 / 785 unchanged) | PROPOSED (T-308).

## 7. Checker re-measure (suggested)

(a) BAND0049 on 'ST7757 dxf.dxf' ST p.4: arcs 29F / 2A0 (R 1.300 / 1.100, 0 .. 90), closing lines 314 / 484, block 47D
'b7'; GF-095 area and the walk delta (T308_WALK_DELTA_BAND0049.json) by re-running `t308_walk_delta.py`;
(b) B15 on ST p.6: 7A9, lines 397 / 3AD, column outlines 424 / 40F (2.700), panel 2F-011 'T 18'; (c) one stair line
r4 -> r5 (ST-02 L-056402f9 10.321 -> 7.546233) in FORMWORK_R5_BY_LINE_T308.csv; (d) CB5 L-3e907654 E 5.032 -> 2.516.
