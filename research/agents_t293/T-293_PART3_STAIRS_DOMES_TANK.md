# T-293 part 3: stair, dome and water-tank formwork tied to the V3.0.18 candidate concrete lines

Worker 1 (lane S), 2026-10-26 00:24 .. UTC, run unknown, branch `agents/task-T-293`. Research ledger: nothing wired, no
candidate or released line changed, no method version, no quantity released; formwork r4 is not rewritten (a corrected
formwork revision is a new file, carried by T-199). Integration dependency of T-199 (formwork is a BOQ category the
candidate lacks). Development villa, not an accuracy claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied. Parts 1 (MERGED
294da634) and 2 (MERGED a1e0c43a) are unchanged.

## 0. Inputs (all committed; no drawing read was needed this run)

| Input | Merged as | Used for |
|---|---|---|
| formwork r4 FORMWORK_LINES_R4.csv | T-264 90203feb | the SOURCE rows (via the part-1 builder `t293_alsenan.faces_r4`, identical records) |
| LEDGER_T281.csv (stair soffit planes, methods O / D) | T-281 789ebbb4 | the drawn soffit per flight / landing, and what lies under each lane |
| LEDGER_T258.csv (stair pieces r2) | T-258 b1b72a50 | the piece per row, beam-band entries (0.20 / 0.20 / 0.150), lanes 1.200 |
| t266_inputs.build() + engine.source.arch_v3018 | T-266 ceeb5135 (= V3.0.18) | the split / rebase / hold of each stair line; part line ids |
| CANDIDATE_V3016_CONCRETE_LINES.json | part 1 | stair / dome / ring lines (none in the T-254 V3.0.17 table: byte-identical) |
| FORMWORK_FACE_TO_LINE_T293_P2.csv | part 2 | the beam faces already booked under the round stair and on B15 |

The three V3.0.18 part lines are **recomputed** with the engine's own id function (`boq_line.line_id` on
`arch_v3018.part_element_id`): L-e37d81a8be8e0aa0010c, L-056402f98a6dbbcde0a0, L-85f64587588af8537b4b = T-266's
handoff, asserted. Command: `python3 -I research/agents_t293/t293p3_ledger.py --write`.

## 1. Physical element and the question (ERS s.2.1)

A formed face bounds one concrete PIECE; its formwork is reported beside the candidate line that carries that piece's
concrete. Stairs: riser forms (riser height x lane x count), the waist soffit (the inclined underside, true area = plan x
sec), landing soffits (flat). Domes: shell intrados (soffit form), extrados, ring faces, drum faces. Tank: its walls.
Question: which V3.0.18 line owns every piece of the 46 rows (23 STAIR + 18 DOME + 1 TANK + the 2 T-290 delta rows + the
part-2 rows R4-313 dome-opening band and R4-316 winder slab), at which status, and does every row close.

## 2. Result: 46 rows -> 70 pieces, closure 0.000000 m2 per (status, method) (`summary_t293_p3.json`)

| V3.0.18 line | Line state | Faces tied CALCULATED (m2) | r4 printed on it | Held on it |
|---|---|---|---|---|
| L-e37d81a8 ST-01 MS1-LD + MS1-U (VERIFIED part) | SOURCE_DERIVED 1.227952 | **8.095527** (landing 1.440, risers 2.400, soffit 4.255527) | 8.370 | - |
| L-67e4b048 MS2-L | SOURCE_DERIVED | **6.722695** (risers 2.419, soffit 4.303695) | 6.958 | column 691 exposure 0.028653 (D-16) |
| L-2416e65f MS2-LD (REBASE) | SOURCE_DERIVED 0.4696 | **2.935** (plates 1.495 + 1.440) | 3.000 | - |
| L-bb0e57b1 MS2-U | SOURCE_DERIVED | **6.682581** (risers 2.419, soffit 4.263581) | 6.958 | - |
| L-85f64587 D1 steps (DC part) | SOURCE_DERIVED 0.100286 | **0.840** (4 x 1.20 x 0.175) | 0.840 | - |
| L-056402f9 RS-S + RS-LD + RS-A (owner-approved part) | PROVISIONAL 1.536225 | **7.546233** (risers 2.121 + 0.964286, soffits 2.093071 + 0.870394 + 1.497482) | 10.321 | column 380 0.045378 (D-16) |
| L-7863355d ST-01 GF parent (MS1-L, MS1-T, winder slab) | BLOCKED_RFI | - | 5.706 | MS1-L risers 2.000 + waist 3.706 (C-ST-4), MS1-T faces, winder slab 1.44 .. 1.562 (C-ST-3) |
| L-061e18cf ST-03 E1 (HOLD) | BLOCKED_RFI | - | 2.380 | E1 risers 2.380 (R-FW-P3-1); waist soffit NOT_APPLICABLE (Checker 11:05) |
| L-659243ed MS2-TR, L-821032bc D1 parent, L-b6b0354b ST-02 parent | BLOCKED_RFI | - | - | MS2-TR, D1 waist, RS-C faces (no value) |
| L-8ea34765 / L-fffa895e DOME-A / DOME-B shell | SOURCE_DERIVED 2.540681 | **24.150** each (intrados) | 24.150 each | extrados (casting method not printed) |
| L-48b7d139 DOME-1F-W ring (= DOME-A) | SOURCE_DERIVED 0.7552 | - | - | ring faces HELD (S0 CONFLICT, T-185) |
| L-ab37afa1 DOME-1F-E ring (= DOME-B), L-d5401fa8 DOME-3 | BLOCKED_RFI | - | - | ring faces; tower shell / support (G3-a / D-21) |

Every live stair / dome / ring line carries faces (`live_lines_without_faces` empty). Not tied: drums DOME-A / DOME-B
(NO_CANDIDATE_LINE, named omission, blank), the 7 S1 scenario rows (8.783 m2 never a candidate face), the stringer
side-face aggregate R4-339 (HELD, no value), the TANK row (DUPLICATE_VIEW, s.3 F-03), the dome-opening band R4-313 and the
two T-290 delta rows (POINTER_ROW: booked as the RETIRED pieces of their r4 rows, never a second correction).

Hand checks: shell intrados R_o = (2.21^2 + 1.90^2) / 3.80 = 2.235289, R_i = 2.135289, h_i = 1.80: 2 pi R_i h_i = 24.1496
(printed 24.150); MS1-U soffit 3.720 x sec 1.143959 = 4.255527; RS-A risers 5 x 1.200 x 4.50 / 28 = 0.964286.

## 3. Findings (engineering)

**F-T293-P3-01 formwork r4 stair soffit rows over-measure the six closable stair lines by 3.625 m2 (-9.9 %).** r4
prints 36.447 m2 CALCULATED on them; the drawn faces are **32.822036 m2**. r4 derives each waist soffit as waist volume /
thickness (T-111), which runs over the owner concrete region, not the drawn underside. Every m2 of the 3.624964 is named
to its physical cause (residual 0.000):

| Cause (piece kind) | m2 | Where |
|---|---|---|
| inside another member: no surface (NO_FACE_INSIDE_MEMBER) | 0.783422 | MS1-U 0.20 into B20 (0.274550), MS2-U 0.20 into B23 (0.275070), MS2-L 0.150 into B20 (0.206302), column 374 in the RS-LD plate (0.0275) |
| under a member whose own rows already hold it (DUPLICATE_IN_SOURCE) | 1.914913 | RS-S over the 'B3 (With Stair)' band GF-159 1.247901 and the CA member 0.391387; RS-LD over GF-159 0.275625 (part 2: R4-258.GF-159 HELD 1.375625 on BM-GF-057; R4-254 GF-144 / 158 CALCULATED 0.315 + GF-143 HELD 0.03 on BM-GF-039 / 057) |
| readings the concrete ledger retired (RETIRED_IN_SOURCE) | 0.203246 | MS2-LD 0.480 reading 0.065 (T-290 s.5 (1)), RS-A 1.25 width 0.040179 risers + 0.068067 waist, RS-LD pre-r2 plate 0.030 |
| unmarked layer-5 pairs (HELD, no line) | 0.648919 | 535 / 536 under RS-S 0.306303 and RS-LD 0.087731; 2CC / 2CD under RS-LD 0.11875 and RS-A 0.136135 (F-T281-03) |
| column exposures in CONFLICT (HELD on the piece) | 0.074031 | columns 691 (MS2-L) 0.028653, 380 (RS-S) 0.045378 (T-248 D-16) |
| r4 print rounding | 0.000433 | six rows, each <= 0.0005 |

The largest single item is ST-02: r4 10.321 vs drawn 7.546 m2 (-26.9 %): r4 takes the full 1.20 x 3.00 lane under RS-S,
while 1.755 m2 of that plan is the stair beam band, the CA member, a column edge and an unmarked pair (T-281 s.3 closes
the plan exactly: 1.845 + 1.100 + 0.345 + 0.040 + 0.270 = 3.600). Verdict proposal: **ENGINE_WRONG** (formwork r4
research method on the stair rows); fix in a new formwork revision (r3 / r4 untouched), carried by T-199. The 1.915 m2
duplicate is a real double count across the formwork rows (stair rows + part-2 beam rows); the 0.783 m2 is a face that
does not exist.

**F-T293-P3-02 method D beside method O.** On the tied soffits, method D (T-281 physical planes: the sloped waist runs on
under the next plate's edge) totals 20.709033 vs method O 20.218750 m2 (+0.490283) for the eight pieces with both; RS-A's
D head kink (0.374173 plan, 0.424483 true) lies under the 1F arrival slab C-T1, a slab panel part 2 already ties as slab
soffit, so D can never be added to the slab ledger without moving it out of the panel. Carried as `alt_D_m2`, never
summed, never chosen by size (no owner rule measures formwork; FREELANCER_NO_ROW).

**F-T293-P3-03 the TANK row is beam B15, and the B15 faces stand on D-44.** r4's 'water-tank walls (B15 20 x 120 up /
down)' is beam B15 = BM-2F-007 (T-149 R125, 0.20 x 1.20 x 2.70, candidate P-C:BEAMS:2F:BAND0006.2 L-713bc64aaa210610e7fe),
whose faces part 2 already ties as CALCULATED on the DOWNSTAND reading (E soffit 0.540 + sides 5.616; G soffit 0.540 +
sides 3.978806 + edge band 0.21615). The TANK row is therefore a second view of one member (DUPLICATE_VIEW, never a face).
D-44 (up- or downstand not printed) is open: for the faces the slab plan shows, the E area is the same either way by
symmetry (2 x 2.70 x (1.20 - 0.16) above or below a 0.16 slab, 0.20 x 2.70 under-face), but the 0.540 under-face then
belongs to the slab panel, not the beam, and the G side faces depend on what abuts B15 above vs below the slab (tank
columns C2 / C3, T-119 heights 3.00 .. 3.80 m): not quantified. For T-199: B15's faces carry the D-44 flag; no value
moves here (part 2 files unchanged). The rest of the tank (top slab, other walls) is not drawn (D-44 / D-52): no face.

**F-T293-P3-04 the DOME-A ring line is measured, its faces are held.** L-48b7d139 carries 0.7552 m3 = the p.5 plan B4 band
in-bay 1.5105 x 0.50, while T-185 holds the S0 ring on the plan-vs-detail CONFLICT (r 2.211 - 2.411 vs 2.011 - 2.211): the
formwork row is HELD on a line the candidate measures. Same kind as T-193's open note (1). Named for lane I; no value
here.

**F-T293-P3-05 consistency of held lines (for the Checker / T-199).** Here a face whose piece's concrete is carried by no
candidate quantity is HELD with it (R-FW-P3-1, the Lead 00:15 direction: 'ST-03 HELD -> its formed faces HELD with it'):
MS1-L 5.706 and E1 risers 2.380 m2 are kept as held_from. Part 2 showed 26 CALCULATED pieces (3.2574 m2) beside held beam
/ column lines with a `line_flag` instead. T-199 must apply one rule to both; proposal: R-FW-P3-1 (hold), which keeps
every value and never shows a face as a measured element beside a blank line. E1's riser inputs are all drawn (5 x 2.80 x
0.170): its faces become CALCULATED the moment a package splits the ST-03 steps (0.355017 DC) into their own line.

**F-T293-P3-06 D1 riser width (note, no change).** The four D1 riser lines are drawn 1.150 long in a 1.200 lane: 4 x 1.150
x 0.175 = 0.805 vs 0.840 m2 (-0.035, -4.2 %), the same residual the Checker carried as a note on the concrete (11:05).

## 4. Owner manual method vs drawing method (ERS s.2.3)

No owner rule measures formwork and the freelancer has no formwork row (FREELANCER_NO_ROW, no %). Methods kept side by
side: r4 element / volume-thickness rows (source), the drawn soffit planes O (tied) and D (alternative). They agree on
risers (every lane / count / riser printed), on the MS1-LD and MS2-LD-E plates and on the dome intrados; they differ only
by the named causes in F-01 / F-02.

## 5. Rules, tests, lesson

Rules R-FW-P3-1 .. 5 (`t293p3_ledger.py` docstring; research scope, any villa; provenance T-293 part 3 on T-264 / T-281 /
T-258 / T-266 / T-290). Tests `tests/t293p3_formwork_stair_dome` (31): villa V293P3 by hand (NORMAL: flight soffit 1.75 x
1.00 x sec 1.220656 = 2.136147 with 0.244131 inside the beam band and -0.000278 rounding, risers 1.400, landing 1.18 + a
0.02 column, a winder face held with its parent, dome intrados 2 pi 1.545 x 0.92 = 8.930920, drum no line, tank = beam
view; closure, consumer, mirror order. ADVERSE: a measured face on a held piece refused, pieces that do not close / a
negative / missing piece / a piece with no member refused, a row without a quantity not split, mm2 refused, held never
0, a drum never gets a value, a TANK and a BEAM view of one member refused, NO_FACE / ROUNDING pieces never reach the
consumer) and Alsenan pinned (46 rows once, closure, recomputed V3.0.18 ids and states, tied m2 per line, the 3.624964
split by cause, held pieces blank, duplicates really booked in part 2, T-290 pointers, domes, TANK = B15, D beside O,
committed outputs = fresh build, no coordinates).

Lessons row (proposed, ERS s.7): 2026-10-26 | A formwork soffit taken as concrete volume / thickness (T-111) carried the
waist's run inside beam bands and over the members under the lane, 3.625 m2 on six stair lines, 1.915 of it booked again
by the beam rows | A derived trade quantity inherited the concrete region's extent, not the formed surface's | Measure a
form on the drawn surface it touches; split any volume-derived area into the drawn face, the part inside other members
(no face), the part under members whose own rows hold it (one face once) and retired readings, closing to 0.0005
(PROJECT-INDEPENDENT) | tests/t293p3_formwork_stair_dome | OPEN (T-293 part 3 READY).

## 6. Checker re-measure (suggested)

(a) MS1-U: T-281 25B -> B20 face 3.100 x 1.200 = 3.720 plan x sec(0.300, 4.50 / 27) = 4.255527; T-258 'last 0.20 inside
the B20 band 458 / 2C6' -> 0.274550 inside; r4 4.530 = 0.7248 / 0.16. (b) ST-02 RS-S plan 3.000 x 1.200 = 3.600 = 1.845 +
GF-159 1.100 + CA 0.345 + column 380 0.040 + pair 0.270, against part 2's GF-159 / GF-143 / 144 / 158 rows. (c) The three
part line ids from `boq_line.line_id`. (d) B15 = BM-2F-007 on 'ST7757 dxf.dxf' p.6 (tag B15 20 x 120) and the TANK row.
