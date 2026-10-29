# T-332 Formwork faces bound to the V3.0.21 concrete lines; faces re-opened by later merges re-measured (lane S)

Worker 1, 2026-10-29 11:33 .. UTC, run session_01E6cPnbYRdr5n6hha9zZLSB, branch `agents/task-T-332`. Research ledger:
nothing wired, no candidate or released line changed, no method version, no quantity released. Integration dependency
of T-199 (formwork is a BOQ category the candidate lacks): T-199 only wires the FILL table below. Development villa, not
an accuracy claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied.

## r2 (rework of D-T332-1, Worker 1, 2026-10-29 21:2x UTC, run session_01E6cPncGg8a6q3YcW1Efqmz)

Defect (Checker, Gate A d): the FILL writer re-aggregated HELD faces with a float formatter, so every HELD row printed
m2 0.000000 (201 / 201) and rows whose faces carry no bound printed lo / hi / held_from 0.000000: a consumer wiring the
table unchanged would read a held face as a known 0 m2. Every re-measure, binding and total of r1 is unchanged (the face
ledger, `summary_t332.json` and the chain are byte for byte the r1 build).

New rule **R-T332-8 FILL AGGREGATE** (`t332_rules.py` `bound_class` / `_aggregate` / `check_fill_row`, `fill_table`):
each face is VALUE, RANGE (lo and hi), AT_MOST (hi only), AT_LEAST (lo only), HELD_FROM (a measured value held by its
line's state) or UNBOUNDED. A FILL row prints m2 only when every face carries one (HELD always blank; a key mixing valued
and blank faces is refused); lo only when every bounded face carries a low end, hi only when every bounded face carries a
high end (an AT_MOST / AT_LEAST / UNBOUNDED face blanks the end it lacks: a partial sum would understate the row);
held_from only over HELD_FROM faces; the new trailing column `bound_classes` counts the faces per class. The writer
(`t332_alsenan.py` `fill_rows_of` / `fill_csv`) checks every row before and after printing and refuses a number that no
face carries.

Effect on `T199_FILL_T332.csv` (678 rows, same rows / lines / face ids / statuses; m2 of every CALCULATED and
ALTERNATIVE row unchanged): 201 HELD + 1 NOT_APPLICABLE m2 0.000000 -> blank; lo / hi / held_from 0.000000 -> blank
where no face carries them (476 CALCULATED / ALTERNATIVE rows, 171 / 27 / 24 HELD rows for held_from / lo / hi); 19 HELD
rows are wholly UNBOUNDED (e.g. L-00465df980165c529476 GROUND_BEAM, R4-071 annex exterior span, D-35: all blank). One
row changed from a number to blank because the old sum was an understatement, not a 0: **L-7863355dfcb68a681d2d
STR.CONC.STAIR HELD G**, r1 printed lo 1.440 / hi 1.562 m2, but its four faces are R4-316 winder slab RANGE 1.440 ..
1.562, R4-317 / R4-318 HELD_FROM 2.000 + 3.706 and R4-319 MS1-T winder faces UNBOUNDED, so the row has no range (r2: lo
/ hi blank, held_from 5.706, `RANGE 1; HELD_FROM 2; UNBOUNDED 1`). AT_MOST rows (e.g. L-26f6b6f2365c72e42291 COL-2F-54
shaft <= 5.320) now print lo blank instead of 0. A face's own printed low end of 0 (the JOINT_HELD 0 .. x ranges, 60
cells) is kept: it is carried by the face, not invented.

Not changed (named): `summary_t332.json` ledger totals (`R.totals`) still add HELD m2 / lo / hi as sums over faces (the
closure view, not consumed by T-199); the r1 test line asserting the FILL HELD m2 == 0.0 is replaced by `is None`
(stricter, the defect it pinned).

## 0. Run, identity, sources

Own run, Python 3.11.18, Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip (`ab54dd55`) and
'ST7757 dxf.dxf' (`9f9d1179`), decoded into `.work/private` only. `research/agents_t167/v304_run.py` then
`research/agents_t315/v3021_run.py`: **V3_0_21_BOQ_LINES.json `be22a4e4` / csv `3548e39c`** (= the candidate of record,
3,706 lines, 521 STR.CONC lines, 0 formwork lines).

```
python3 -I research/agents_t332/t332_candidate.py <v3021 run> research/agents_t332/CANDIDATE_V3021_CONCRETE_LINES.json
python3 -I research/agents_t332/t332_extract.py <'ST7757 dxf.dxf'> research/agents_t332/ALSENAN_T332_INPUT.json
python3 -I research/agents_t332/t332_alsenan.py --write
```

Face source: **formwork r5** (T-308 MERGED efb38618) = r3 (T-163 659f889f) + r4 (T-264 90203feb) + the three T-293
face-to-line parts (294da634 / a1e0c43a / 02f3e47e) + the r5 rules; 1,305 r5 rows (1,180 on lines, 100 not tied, 25
removed). The row names r3; r5 is the newest merged revision built on it, so r5 is bound and the totals are closed back
to r3 step by step (section 3). Outputs: `FORMWORK_T332_BY_FACE.csv` (every face: r5 value and line, V3.0.21 tie / line
/ state, rule, delta cause and drawing source), **`T199_FILL_T332.csv`** (the FILL table), `T199_FORMWORK_BY_LINE_T332.json`
(consumer, same schema family as T-293 / T-308), `summary_t332.json` (totals, closure, chain, deltas, agreements, input
hashes). Rules and guards: `t332_rules.py` (R-T332-1 .. 7).

## 1. Physical element and the question (ERS s.2.1)

A formed face is a concrete surface cast against a form; it bounds ONE member and is reported beside the candidate line
that carries that member's concrete. A face cast against ground, blinding, screed or masonry has no form (footing and
pool bases on blinding / screed: no row; R-T332-4 refuses one booked as formed). Below the existing ground the owner
question OQ-10 is open: FORMED / EARTH_CAST travel together, never summed, never chosen. Searched before ruling:
OWNER_QUESTIONS_ANSWERED.md and the OWNER_RULE files for 'formwork' / 'shuttering': no answered owner rule measures
formwork; OQ-10 stays open (no owner manual method on record; the drawing methods E (element faces) and G (drawn faces)
stay side by side). Question: for every r5 face, which V3.0.21 concrete line owns it, once; which faces did merges after
r5 change, re-measured from the drawing.

## 2. Binding result (R-T332-1 / -2)

V3.0.18 (r5's candidate) -> V3.0.21: the 521 STR.CONC lines are the same ids and element ids; **one** concrete line
changed: ring ground beam BAND0043 L-7076482d75ca42691468 1.7349 -> 1.746943 m3 (T-255 V3.0.19, end closure).
So **1,189 / 1,189 tied faces SAME** (0 REBOUND, 0 lost, 0 newly held by a line state), 351 lines carry faces, 26
concrete lines WITH a quantity carry none (summary `live_concrete_lines_without_faces_ids`): 24 STR.CONC.GROUND_SLAB
(cast on blinding between ground-beam faces: no slab-edge form row in any revision), the footing blinding line (no
form) and BAND0013.1 (the ARC:139+13A sliver, SPLIT_UNRESOLVED as in r5). V3.0.22 (T-331, merged during this run) changes
FIN.PLASTER lines only (its Gate B: every other line byte-identical to V3.0.21), so the binding holds on it unchanged.
Untied rows keep their reasons: 69 SPLIT_UNRESOLVED, 38 NO_LINE (12 r5 + 2 lift-pit faces + 24 parapet runs), 7 INFO,
7 S1 scenario, 5 named.

| Status, method (tied faces) | r5 bound to V3.0.21 | T-332 | Change (named, section 4) |
|---|---|---|---|
| CALCULATED G | 626.872989 | **626.872989** | 0 |
| CALCULATED E=G | 418.871805 | **434.854504** | +15.982699 pool water face 13.283363 + outer face above EG 2.699336 |
| CALCULATED E (comparison method) | 422.693420 | **422.693420** | 0 |
| ALTERNATIVE OQ-10 FORMED E=G | 170.205205 | **180.045419** | +8.098008 pool walls + 3.599115 pool base edge - 1.856909 F8 into the pool envelope |
| ALTERNATIVE OQ-10 FORMED G / EARTH_CAST | 3.650857 / 0 | 3.650857 / 0 | 0 (pool / base EARTH_CAST rows 0 added) |
| HELD G (all rows) | 269.659765 .. 348.249429 | **351.248455 .. 551.031023** | + parapet 24 runs 81.588690 .. 202.781594 (NO_LINE) |
| HELD E=G | 0 .. 0 (10 rows blank) | 0 .. 5.600 | + pool back face on the boundary-wall line 0 .. 4.200 + 0 .. 1.400 |
| HELD OQ-10 FORMED E=G | 130.397653 .. 196.497147 | 130.397653 .. 198.354056 | + F8 / pool CONFLICT 0 .. 1.856909 |

Closure (R-T332-7, `summary_t332.json` `closure`): per (status, alternative, method) T-332 = r5 + named deltas,
residual 0.000000 on every key; held_from 18.191624 (G) + 35.256 (OQ-10 FORMED) carried unchanged.

## 3. Totals by element type closing on r3 1,078.274 m2 (CALCULATED, methods G and E=G)

| Element | r3 | r4 | r4 source rows | r5 | T-332 |
|---|---|---|---|---|---|
| BEAM | 387.936 | 393.235388 | 393.234766 | 390.251472 | 390.251472 |
| COLUMN | 183.967 | 117.461 | 117.461 | 117.461 | 117.461 |
| DOME | 48.300 | 48.300 | 48.300 | 48.300 | 48.300 |
| GROUND_BEAM (faces above N.G.) | 0 | 47.662713 | 47.947713 | 47.947713 | 47.947713 |
| JOINT | 11.878 | 9.638828 | 9.639228 | 8.712728 | 8.712728 |
| POOL | 0 | 0 | 0 | 0 | **15.982699** |
| SLAB | 375.048 | 375.048 | 375.0481 | 375.0481 | 375.0481 |
| SLAB_EDGE | 26.612 | 27.747032 | 27.746809 | 25.201745 | 25.201745 |
| STAIR | 44.533 | 44.533 | 44.428 | 32.822036 | 32.822036 |
| **Total** | **1,078.274** | **1,063.625961** | **1,063.805616** | **1,045.744794** | **1,061.727493** |

Every step named in m2 (`chain_steps`), residual 0.000000 per element and step:
- r3 -> r4 (-14.648039, T-264 delta rows): ring B7 soffit +0.391303 and sides +4.908085 (T-252); column section CONFLICT
  -57.246 and 2F roof datum D-39 -15.470, planted COL-1F-57 +6.210 (T-248 / T-256); joints -2.239172; void band owned by
  the ring / CB1 +1.135032; ground-beam faces above N.G. +6.239008 (ring) +41.423705 (exterior main runs, T-253).
- r4 -> source rows (+0.179655): T-282 170+7C3#4 side B +0.285; T-290 stair pointers -0.105; 3-dp print rounding of r4
  rows recomputed unrounded (BEAM -0.000622, JOINT +0.0004, SLAB +0.0001, SLAB_EDGE -0.000223).
- source -> r5 (-18.060822): R-T308-3 BAND0049 +2.601098 beam / +0.326718 band; R-T308-5 held with held lines -0.9265
  joints / -2.330871 bands; R-T308-2 stairs -2.797014; T-293 SPLIT_UNRESOLVED beam -5.584392 / band -0.540911; stair
  pieces held in their ledger -8.160031 and unmarked layer-5 pairs (no line) -0.648919.
- r5 -> T-332 (+15.982699): POOL water face +13.283363, POOL outer face above EG +2.699336.

## 4. Faces re-opened by merges after r5, re-measured from 'ST7757 dxf.dxf' (acceptance b)

| Element (merge) | Drawing (handle) | Before (r5) | After (T-332) | Cause / status |
|---|---|---|---|---|
| Pool walls + base (T-183 r2 MERGED geometry; T-320 EG split) | S-BW 7C6 outer D: back 3.50 + sides 2 x 1.75 + half circle R 1.75 = **12.497787 m**; 7C5 water D: 3.10 + 2 x 1.55 + R 1.55 = **11.069469 m**; deck edge = 12.497787 - 3.50 = **8.997787 m** | R4-340.WALLS / .BASE HELD, no value (r3 s.00: "a separate piece, not in this rework") | water face 11.069469 x 1.20 = **13.283363 CALCULATED**; outer face above EG 8.997787 x 0.30 = **2.699336 CALCULATED**; outer wall below EG 8.997787 x 0.90 = **8.098008 OQ-10 FORMED** / 0 EARTH_CAST; base edge 8.997787 x 0.40 = **3.599115 OQ-10 FORMED** / 0; back face on the boundary-wall line 3.50 x 1.20 / 3.50 x 0.40 **HELD 0 .. 4.200 / 0 .. 1.400** (F-T320-05, Q-28) | 33.279822 m2 in all = T-183 r2 G 33.280 (outer 19.996 + water 13.283), now split by EG and contact; levels base top -0.90, underside -1.30, rim +0.30 (T-183 r2), EG +-0.00 (T-320: walls 2.121 m3 below EG = 2.356726 x 0.90); base on screed, wall top: no form |
| F8 vs the pool envelope (T-320 F-T320-02 CONFLICT) | 1B24 F8 4.00 x 3.60 vs 7C6 buffered 0.10 (p.7 layers), sheet translation 38.7244 m from 10EB / 7C2 (same 2.20 x 2.20 ring): overlap with the outline **1.296546 m2** (T-189 1.296442, densification +0.0001), with the envelope **1.616091** (T-320 1.616); faces inside: **N 3.113818 m + E 0.600 m** | F8 FORMED 2 (4.00 + 3.60) 0.50 = 7.600 | FORMED **5.743091** + **HELD 0 .. 1.856909** (CONFLICT, 3.713818 x 0.50; footing body -1.33 .. -0.83 wholly inside the envelope depth) | the SB1 cover (-0.350) is on the S face (T-174: F8 bottom y): no second deduction (asserted) |
| Lift pit walls (T-322 MERGED: walls 20 on the raft top, depth D-43) | 10EB 2.20 x 2.20 / 10EA 1.80 x 1.80; columns 1099 / 1093 / 1096 / 1090 cover 1.70 m of the inner and 3.30 m of the outer faces; band net **1.100 m2** (= T-204 / T-322) | R4-342 HELD aggregate, no line | pit-side face **5.500 m2 per m** of pit height HELD; outer face **5.500 m2 per m** HELD (OQ-10 + D-43); NO_LINE (no pit-wall concrete line in V3.0.21) | column faces toward the pit belong to the column / neck lines (R-CONC-OWN-1) |
| Parapet RC faces (T-311 MERGED bd7b8c23; T-319 QUEUED) | PARAPET_RUN_LEDGER_T311.csv, 24 runs, 2 x RC height x centreline (Checker Gate A) | not in r5 | 24 HELD NO_LINE rows **81.588690 .. 202.781594** | NO_LINE: parapet RC is a MISSING concrete category; never in a line total |
| AGREES (re-read, nothing moves) | FF 1B2B 4.60 x 4.50 (+ p.9, p.14); F12 1ABF 4.40 x 3.20; arcs 157 R 2.250 x 167.236 deg = 6.567377 m, 158 R 2.550 x 150.086 deg = 6.679704 m; T-323 panels GF-081 4.1176 / GF-141 7.3009 m2; T-224 r2 (no free edge on any sunken panel); DG-3521554d (blinding has no form row) | FF 10.010, F12 10.640, ring 6.239008 / 5.963657, panels by member faces, sunken HELD x 50.885 m | unchanged | ring: T-255 moved only the concrete END closure (ends close on drawn faces: no end form); panels: r5 uses the T-139 member faces, never the hatch |

## 5. Engineering findings and verdict proposals

1. **F-T332-01 Pool formwork was in no revision (r3 -> r5) although its geometry was merged (T-183 r2).** 13.283363 +
   2.699336 m2 CALCULATED and 11.697123 m2 OQ-10 FORMED now sit on the two pool lines. Verdict proposal: ENGINE_WRONG
   (formwork r3 / r4 / r5 omission) -> HAND (drawn D outlines). Not FREELANCER: no formwork row in any of his workbooks
   (FREELANCER_NO_ROW, no %).
2. **F-T332-02 F8's FORMED sides overstate by 1.856909 m2** where F8 lies inside the pool envelope (CONFLICT at the
   printed limit, T-320); HELD 0 .. 1.856909 until the designer resolves the collision (T-183 interface 1). Verdict:
   UNRESOLVED (designer), the formed value never adopted.
3. **F-T332-03 The pool back face (on the boundary-wall line) is not measured** (what it is cast against is not drawn:
   Q-28 lower band / back wall): HELD 0 .. 5.600 m2.
4. **No line moved under a face**: the binding is identity on all 1,189 tied faces; the T-199 package can consume the FILL
   table as is. Lift-pit (2 rows) and parapet (24 rows) faces are NO_LINE: T-199 carries them as their own HELD rows
   (parapet: T-199 row acceptance 2026-10-28 20:20), never inside a concrete line.

## 6. Rules, tests, lessons row

Rules R-T332-1 .. 7 (`t332_rules.py` docstring; research scope, any villa; provenance T-332 on T-308 / T-293 / T-264 /
T-163 / T-183 / T-320 / T-322 / T-311). Tests `tests/t332_formwork_bind` (38): villa V332 by hand (NORMAL: footing on
blinding sides 3.500 OQ-10 pair, base no row; suspended beam soffit 0.800 + sides 3.600; slab edge 0.900 on the edge
beam's line; pit wall 4.800 / 6.400 m2 per m HELD; rebind by element; a measured face on a blank line held with
held_from; deltas REPLACE / ADD / REMOVE with closure; mirror / order invariant. ADVERSE: a face bound to two lines
refused; an element carried by two lines refused; a ground-cast face booked CALCULATED / FORMED / EARTH_CAST with a value
refused; a held face as 0 or with a value refused; a reversed range refused; a negative face without a named deduction
refused; unit / status refused; a face on a NOT_APPLICABLE line refused; S1 tied -> ScenarioLeak; a delta without cause or
source, of an unknown face, an ADD of an existing face, a held-as-0 replace refused; a dropped face fails the closure) and
Alsenan pinned (committed outputs = fresh build, every r5 face once, closure 0, no S1 in totals, held blank, pool faces
by hand = T-183 33.280, F8 overlaps = T-189 / T-320, lift ring 1.100 / 5.500, parapet 24 rows = T-311 totals, chain
closes on r3 1,078.274 with every residual 0, FILL table only tied faces, no drawing coordinates).

Lessons row (proposed, ERS s.7): 2026-10-29 | The pool's formed faces (13.283 m2 water face, 2.699 above EG, 11.697 OQ-10)
were in no formwork revision for three revisions although T-183 r2 had merged the pool geometry with a formwork row | Each
formwork revision re-based the rows it inherited and the elements its row named; a member whose concrete ledger merged
later than the first revision was carried as a HELD placeholder and never re-opened | When a derived trade is rebound to a
newer candidate, list every concrete ledger merged since the derived ledger's base and re-open each member's faces from
the drawing; a placeholder row of a member whose geometry is merged is a finding, not a hold (PROJECT-INDEPENDENT) |
tests/t332_formwork_bind (pool faces by hand; F8 conflict; held as 0 refused) | PROPOSED.

## 7. Checker re-measure (suggested)

(a) Pool on 'ST7757 dxf.dxf' S-BW 7C6 / 7C5: segment lengths (3.50 / 1.75 / R 1.75 half circle / 1.75; 3.10 / 1.55 / R
1.55 / 1.55) and the water face 11.069469 x 1.20 = 13.283363; (b) F8 1B24 north face inside 7C6 + 0.10 after the 38.7244 m
sheet shift (3.113818 m) and east 0.600 m; (c) lift ring 10EA inner faces minus the four columns (0.30 + 0.30 + 0.30 + 0.80
= 1.70 m) -> 5.500 m2 per m; (d) one FILL row: L-15a128c38982af899894 (POOL WALLS) CALCULATED E=G 15.982699 = 13.283363 +
2.699336; (e) the identity: V3.0.18 vs V3.0.21 STR.CONC lines differ only on L-7076482d75ca42691468 (quantity).

## 8. Not done / uncertain

Pit depth (D-43), the pool back face contact (Q-28), the F8 / pool collision (designer), OQ-10 (owner) and every r5 HELD
item stay as named. The E method was not re-based (comparison method, unchanged since r3). No full suite (research files
only; L3 on the formwork / parapet / lift / displacement folders).
