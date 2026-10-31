# T-392 Ring and pool-wall ownership residuals from the T-387 census (lane S, research only)

Worker 1, 2026-10-31 11:24 .. UTC, branch `agents/task-T-392`. No candidate quantity, line, state, rule version file,
method or released cell is changed; corrected quantities below are PROPOSALS for the Checker / lane I. Development villa
(Alsenan), method every villa; not an accuracy claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied.

## 0. Sources and run

Drive "Alsenan chalet project", decoded into `.work/private` only: 'ST7757 dxf.dxf' (sha256 `9f9d1179`), P7757.dxf from
P7757_DXF_COMPRESSED.zip (`ab54dd55`). Candidate of record V3.0.29 through the committed T-387 binding
(`research/agents_t387/BINDING_T387.csv`, lines `6b5dc44f`). Route G plan records re-exported by
`research/agents_t387/t387_geometry.py` (private). Own geometry: `t392_geom.py` (polygonize of layers 1 / S-BEAM /
S-COL.BON, arcs densified to 0.05 mm chord error; route G bands moved to the drawing frame by the one translation that
puts the B8 band on its faces 42C / 46D: 0.000 mm residual on B8 and on every other band used here).

```
python3 -I research/agents_t387/t387_geometry.py <private>/ST7757.dxf <private>/t392/geometry.json
python3 -I research/agents_t392/t392_geom.py <private>/ST7757.dxf <private>/t392/geometry.json <private>/t392/geom_out.json <private>/P7757.dxf
python3 -I research/agents_t392/t392_alsenan.py <private>/t392/geom_out.json --out research/agents_t392
```

Committed output `summary_t392.json`: m2, m3, handles and line ids only (no coordinate, polygon or name; a test refuses a
coordinate-sized number). Rules `t392_rules.py` R-T392-1 .. 4 and R-T387-7 (added to `t387_rules.py`); tests
`tests/t392_ring_pool_ownership/` (hand villa T392-K + the committed summary) and 4 new cases in
`tests/t387_overlap_census/test_t387_rules.py`.

## 1. (a) RING-B7: the 0.2182 m3 located on the drawing

Physical element: the B7 (20 x 75) ring beam round the GF-roof void over the pool, between its own drawn arcs (west 2EE /
2EF R 1.935 with 2F0 R 1.735; east 312 / 313 R 1.750 with 310 / 311 R 1.550), closed by the faces of the members that own
the crossings (B8 46D, B17 42D, CB1 2A9, B7 437), less the void (2F0 / 318 / 310 / CB1 face / 311 / 317; one straight
closing piece 1.330 m on the CB1 face, every arc junction 0.000 mm). The west crescent is one polygonize face with the
void (2F0 is tangent to the B8 face 46D): it is split off by the drawn void loop.

| Piece (drawn) | Plan m2 | Covered by route G arc bands 50 .. 53 | Not covered m2 | m3 (x 0.75) |
|---|---|---|---|---|
| West crescent (2EE / 2EF / 2F0, B8 face 46D) | 0.391427 | BAND0050 0.122854 + BAND0051 0.094969 | **0.173604** | 0.130203 |
| East-north (313 / 311, B7 face 437, CB1 face) | 0.146350 | BAND0053 0.087368 | **0.058982** | 0.044236 |
| East-south (312 / 310, B17 face 42D, CB1 face) | 0.128753 | BAND0052 0.069551 | **0.059202** | 0.044401 |
| **Ring** | **0.666531** (exact arcs, T-252: 0.666406) | **0.374743** | **0.291788** | **0.218840** |

- Line RING-B7 `L-e72c162de78a4bf302c0` 0.499805 m3 = 0.666406 x 0.75; own densified 0.499898 (+0.000093 m3, chord
  densification): AGREE.
- The census's 0.218186 = (0.666407 - 0.375492) x 0.75 took the four bands' whole area; 0.000750 m2 of the bands lies
  outside the drawn ring (their chords). On the ring's exact area the uncovered plan is 0.666406 - 0.374743 = 0.291663 m2
  = **0.218747 m3**; densified 0.218840. Residual between the census and the location: 0.00056 m3 = the band chords
  outside the ring, named.
- No other line holds any of it: the B8, straight B7 (BAND0006) and CB1 (BAND0041.2) bands and drawn cells hold
  **0.000 m2** of the drawn ring; the T-234 slab ledger bills none of it (T-252 r2: faces GF-035 / GF-060 class BEAM,
  the west crescent inside GF-040 'OPENING+RING', excluded).
- **Status: LOCATED, DRAWING-CONFIRMED; billed once by RING-B7; no double count, no gap.** Cause: route G's arc bands are
  narrower than the drawn ring at its ends (they stop short of the closing faces and of the tangent pinch on B8).

## 2. (b) The T-146 ring-overlap deduction 0.002566 m3: a named GAP, not rounding

T-146 (`t146_inputs.py RING_OVERLAP_M2`, report s.2) deducted 0.00178 / 0.00047 / 0.00117 m2 x 0.75 from B8 BAND0003,
straight B7 BAND0006 and CB1 BAND0041.2 as their 'overlap with the drawn B7 void ring', from T-252 r2's 'other beams'
bands in the ring 0.00342 m2'. Those bands were the T-110 band set (`research/agents_t110/scripts/bands.py`: the route
G overlay SVG mapped to metres by a least-squares fit, max error 0.6 mm on GF; own re-run: B8 0.2002 x 3.5207 m,
0.703778 m2 instead of the drawn 0.200 x 3.52014 = 0.704028). A 1 mm fit shift along the 1.7 m tangent contact gives
0.0018 m2.

| Line | Mark | Line m3 | Drawn band / cell m3 | In ring: candidate band / drawn cell m2 | T-146 deduction m3 | R-T392-1 | Proposed m3 |
|---|---|---|---|---|---|---|---|
| `L-9a55aadc9f0880ae37a7` | B8 | 0.526665 | 0.528021 (cell 0.704028 = band) | 0 / 0 | 0.001335 | GAP 0.001335 | **0.528021** (+0.001356, of which 0.000021 the ledger's 4-dp 0.528) |
| `L-cbf53752cfd897c35c2c` | B7 straight | 0.254647 | 0.255000 (cell 0.340 = band) | 0 / 0 | 0.000353 | GAP 0.000353 | **0.255000** (+0.000353) |
| `L-9270e8b8860414386adb` | CB1 span 2 | 1.337922 | 1.338750 (band 1.785) | 0 / - | 0.000878 | GAP 0.000878 | **1.338750** (+0.000828; the ledger's 4-dp 1.3388 carried +0.000050) |
| | | | | | **0.002566** | **GAP 0.002566** | **+0.002537 m3** |

RING-B7 does not carry the slivers: it is measured between its own drawn edges and closed BY the B8 face 46D (tangent),
so it holds 0 m2 of the B8 cell; the deduction removed concrete that no line bills. **Settled: a named GAP of 0.002566 m3
on three beam lines (0.0009 % of the 285.0266 m3 valued structural concrete), cause the T-146 deduction of a fit
artefact; never 'rounding'.** For the CB1 band only the band is used: its east face is the S-BOUN sheet edge, not a
layer-1 line, so no closed CB1 cell exists in the polygonize (stated, not assumed). The census's MEMBERS rows BAND0003
(GAP, 'no documented deduction'), BAND0006 / BAND0041.2 (OK_ROUNDING) are DOCUMENTED_ADJUSTMENT under R-T387-7: the
T-146 ring-overlap deduction (the Checker's F-CHK-T387-1).

## 3. (a) The 0.0235 m3 small group, own figures by handle

| Line | Census residual m3 | Cause (own measure) | Status |
|---|---|---|---|
| B4 BAND0018 `L-a38b4013f5e3a30830b4` 0.296447 | +0.007381 | T-252 r2 R-BEAM-END-OBLIQUE-2: edges 27D 2.8907 / 282 3.0383 m (own), both end on S-BEAM 325; 0.2 x 0.5 x 2.9645 = 0.296446 (own - line -0.000001) | DOCUMENTED_ADJUSTMENT (merged ledger the census did not read) |
| CB4 BAND0021.1 `L-0e110d2c29b2cd318139` 0.250988 | +0.013550 | T-252 r2: edges 288 2.3744 / 285 2.6454 m to S-BEAM 325 (both 0.000 mm on 325); 0.2 x 0.5 x 2.5099 = 0.250988 (own - line 0.000000) | DOCUMENTED_ADJUSTMENT |
| CB8 BAND0039 `L-7c1a1da8004c4272ccba` 0.7163 | +0.002589 | census artefact: it gave the route G B27 band 48.2's 0.00345 m2 overlap to the B27 group while the CB8 line bills its band rectangle (0.00345 x 0.75 = 0.002588). Own geometry below | two findings |

CB8 own geometry (ST p.4 GF roof): CB8 lies between edges 272 and 2AC (0.30 apart); it stops on the oblique B27 face
S-BEAM 326; column 359 (S-COL.BON, 0.40 x 0.20) at its west end is owned by the column (T-229, -0.0600 m3, unchanged);
column 37D's corner west of 326 lies in its end. The route G band is a rectangle cut square at x of 2AC's end, which
runs 59 mm (perpendicular) past face 326:

| CB8 plan, m2 | |
|---|---|
| route G band (rectangle) | 1.035065 |
| drawn cell to face 326 | 1.046136 |
| band beyond face 326 (inside B27's drawn cell, host face 1.400797 m2 between 325 / 326) | 0.003690 -> **DOUBLE 0.002767 m3** with B27 (Checker T-387: B27 line 4.1918 = its drawn cell 4.192720 m3 to -0.00092) |
| cell short of the band end, less column 37D's 0.010220 | 0.004540 -> **GAP 0.003406 m3** |
| drawn net (cell - column 359 - column 37D) | 0.955915 m2 x 0.75 = **0.716937 m3** (proposal; line 0.7163, +0.000637) |

R-T392-2: both above the 0.001 m3 tolerance, reported apart, never netted. Status: DOUBLE 0.002767 m3 (CB8 / B27 at the
B27 face) and GAP 0.003406 m3 (CB8 end before face 326), both DRAWING-CONFIRMED geometry; proposed CB8 0.716937 m3.

Census group 0.0235 = 0.007381 + 0.013550 documented (T-252 r2) + 0.002589 census artefact; unexplained 0.000 m3.

## 4. (c) The pool's fourth side B7 / 8D: owner trade of the out-of-pool part

Physical element. Architectural GF plan: B7 / 8D are two layer-5 lines 0.200 apart, 5.1684 m long (the boundary-wall
pair convention of T-183 / T-016b / T-260). The pool arcs 202 (R 1.55) / 200 (R 1.75) share a centre; B7 lies exactly
1.550 and 8D 1.750 from it: B7 / 8D are the inner / outer faces of the pool's straight back wall over the pool's 3.500 m
side, and the same wall line runs on **0.9184 m south and 0.7500 m north of the pool = 1.6684 m outside the pool**. The
structural GF-roof ring arcs 310 / 312 are concentric with the pool arcs (same radii); by that translation 8D falls on
the S-BOUN line 2A7 (0.000 mm): the line pair is the plot boundary.

| Sheet | Element under the out-of-pool part | Covers south 0.9184 / pool back 3.50 / north 0.75 m | Line (V3.0.29) |
|---|---|---|---|
| ST ground-beam plan (S-BOUN 7FC, 7FE; 0.000 mm shift check) | boundary upper G.B 20 x 40, top at N.G. (T-253 p.14 A-A) | 7FC 0.9184 / 0 / 0; 7FE 0 / 0 / 0.75: **the upper G.B stops at the pool and resumes** | `L-fb7a6431fede62e93fd5` STR.CONC.GROUND_BEAM, HELD (BLOCKED_RFI: boundary-wall columns 'SEE ARCH PLAN'); its T-347 runs 7FC#1 / 7FE#3 DRAWING-CONFIRMED |
| ST foundation plan (S-BOUN 1658 / 1659, band 0.200) | lower boundary band | 0.9184 / **3.50** / 0.75 (continuous) | `L-6290a9f3d93f38cd46d6` STR.CONC.BOUNDARY_WALL, HELD (downgrade DG-6dd9f1caba1ca77d) |
| Architectural GF plan B7 / 8D above N.G. | boundary wall masonry (lane A) | 1.6684 m | **MISSING** (T-279: the boundary fence is in no masonry line) |
| Pool lines (T-183) | pool walls: band 2.356726 m2 = straight back 3.50 + 2 x 1.75 sides + half circle | back 3.50 only | do NOT carry the out-of-pool part (correct) |

**Owner trade: the plot boundary wall** (CONCRETE below N.G.: upper G.B 1.6684 x 0.20 x 0.40 = 0.133472 m3 inside the
HELD line L-fb7a6431; lower band inside the HELD line L-6290a9f3, section held by Q-28 A; MASONRY above N.G.: MISSING,
height not established here). Not pool concrete (R-T392-3 refuses giving it to the pool). Never 0: both concrete lines
stay HELD blank, the masonry is a named MISSING item.

Interface carried (not settled here, ERS s.2.7 not met): under the pool back 3.50 m the lower boundary band runs on
beneath the pool base (T-183 interface 2 / C6: 3.50 x 0.20 x 0.60 = 0.420 m3 'possibly in both'); the upper G.B does
not (it stops at the pool). The lower band line is HELD, so nothing is billed twice today; the designer item C6 stays.

## 5. (c) ELEMENT_REGISTER proposal rows (for the Lead; no register edit)

| Element | Drawing reference | Owner trade (proposal) | Line | Basis |
|---|---|---|---|---|
| Plot boundary wall along the pool's straight side, out-of-pool parts 0.9184 + 0.7500 m | arch GF plan B7 / 8D; ST ground-beam plan 7FC / 7FE; ST foundation plan 1658 / 1659 | BOUNDARY WALL: concrete below N.G. (upper G.B 20 x 40 + lower band), masonry above N.G. | L-fb7a6431 (HELD), L-6290a9f3 (HELD); masonry MISSING | T-392 s.4; T-183 s.5 |
| Pool straight back wall 3.50 m (= the boundary wall line over the pool) | arch B7 / 8D between the pool arcs' ends; ST GF-roof ring concentric | POOL walls (T-183 band) below the rim; upper G.B absent there; lower band beneath = interface C6 | pool walls line | T-183; T-392 s.4 |
| GF B7 ring beam between its drawn arcs, incl. 0.2918 m2 outside route G's arc bands | ST p.4 arcs 2EE / 2EF / 2F0 / 312 / 313 / 310 / 311, faces 46D / 42D / 2A9 / 437 | CONCRETE beam (ring) RING-B7 only; B8 / B7 / CB1 / slab hold none of it | L-e72c162d | T-252 r2; T-392 s.1 |
| CB8 end at the B27 face 326 | ST p.4 edges 272 / 2AC, S-BEAM 326, columns 359 / 37D | CB8 to face 326; the part beyond 326 is B27's; column 37D owns its corner | L-7c1a1da8 (proposal 0.716937) | T-392 s.3 |
| P.C 20 x 70 on GF B27 (Checker T-387 addition) | ST p.4 0x329 | B27 owns the plan under it; the column starts on the beam | L-3dddf990 | T-229; Checker 07:00 |

## 6. Verdict proposals, corrected quantities (proposals), what is missing

- RING-B7 0.499805: AGREE (own 0.499898 densified); census RECHECK 0.2182 -> LOCATED (0.218747 m3 exact-area basis).
- T-146 ring overlap: ENGINE_WRONG by 0.002566 m3 (deduction of a fit artefact); proposals B8 0.528021, B7 0.255000,
  CB1 span 2 1.338750 (+0.002537 m3 on three lines incl. -0.000029 of 4-dp ledger rounding; the GAP itself 0.002566).
- B4 / CB4: AGREE with T-252 r2 (own edges); the census residual was its own omission of that ledger.
- CB8: ENGINE_WRONG at its end: DOUBLE 0.002767 with B27 + GAP 0.003406, proposal 0.716937 (+0.000637 net, both parts
  reported).
- Pool fourth side: owner = plot boundary wall; concrete in two HELD lines, masonry MISSING; pool lines correct.
- No freelancer comparison here (T-385 holds it; these are line-internal ownership residuals).
- Not done / uncertain: column 37D's oblique line 37B inside its rectangle (the 0.010220 m2 uses the rectangle);
  boundary masonry height and the boundary columns 20 x 30 (designer, HELD); the lower band under the pool (C6).

## 7. Rules and proposed lessons-register rows (ERS s.7)

R-T387-7 (documented sub-tolerance deduction, every villa), R-T392-1 (neighbour-overlap deduction only against drawn
cells), R-T392-2 (band end across an oblique face: DOUBLE and GAP apart), R-T392-3 (line pair longer than a tank side:
outside part to the element the other sheets show), R-T392-4 (residual located piece by piece) - text in the modules.

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-31 | 0.002566 m3 deducted from three GF beams as 'overlap with the ring' that the drawing does not have (T-392) | the overlap was read from a band set fitted to an overlay (0.6 mm error), not from the drawn cells | a neighbour-overlap deduction is taken only from the members' drawn cells; an overlap a fitted / derived geometry shows and the drawn cells do not is a GAP on the deducting line, named (scope every villa; provenance T-392, Checker T-387 F-CHK-T387-1) | tests/t392_ring_pool_ownership: tangent beam GAP, real overlap counted once, mirror / rotation, mm2 / mm refused | PROPOSED |
| 2026-10-31 | a census called documented T-146 / T-252 adjustments 'rounding' or 'no documented deduction' (T-387) | it read one ledger field, not every merged ledger that wrote the line | reconcile to every merged ledger, formula first; a documented sub-tolerance item is named, never rounding (Checker 07:00 lesson) | tests/t387_overlap_census: named 0.0004 m3 normal / called-rounding refused / two ledgers / unnamed refused | PROPOSED |
| 2026-10-31 | a square-cut band at an oblique carrier both overran the carrier (DOUBLE 0.0028) and fell short of it (GAP 0.0034) on CB8, netting to 0.0006 (T-392) | a dangling edge end set the band's end, not the carrier face | measure a member to the carrier face; report beyond / short apart, never net | tests/t392: trapezoid hand case, mirrored, non-closing refused | PROPOSED |

## 8. T-387 outputs re-run (Checker's next-touch request, acceptance d)

Own V3.0.29 reproduction this run (`v304_run.py` + `v3029_run.py` on the Drive copies): BOQ_LINES json `6b5dc44f` / csv
`09b3493b` = the candidate of record. `t387_alsenan.py` now reconciles every merged ledger (R-T387-7: formula field,
T-229 ledger_adds / deducts, T-252 r2 runs whose released figure is the band's) and reads the committed T-392 findings.
MEMBERS_T387.csv: BAND0003 GAP -> GAP_NAMED, BAND0006 / BAND0041.2 OK_ROUNDING -> GAP_NAMED (label 'T-146 ring-overlap
deduction'), BAND0018 / BAND0021.1 RECHECK -> LEDGER_ADJUSTED (T-252 r2), BAND0039 RECHECK -> DOUBLE_AND_GAP_NAMED,
ring RECHECK -> LOCATED_EXTENSION. GF level band: unexplained gap 0.001356 -> 0; named GAP 0.005972 / DOUBLE 0.002767
m3 (status FAIL_HELD until lane I settles them); RECHECK 0.801008 -> 0.559303 m3 (B26 / B27 only). BINDING_T387.csv
unchanged; the downgrade file on agents/control is newer than T-387's (sha recorded in summary_t387.json), no binding
status moved.
