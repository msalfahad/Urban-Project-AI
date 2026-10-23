# T-241 Whole-line closure: CONC.BEAM, every beam run once (Alsenan; every villa)

Worker 1 (lane S), 2026-10-23, run session_019AKBYjYwgocgsECvjgqnyr. Research piece, not wired: no engine, candidate or
released line changed; integration is a lane I package after the Checker's verdict. Development villa, not an accuracy
claim. Drawings named by Drive folder and title; entities by DXF handle / face id; lengths, areas, volumes only.

## 0. Inputs and runs (own, this task)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179...38079 (= manifest) | the three roof-slab sheets: T-139 faces (402 incl. 4 dome-corner pieces) re-polygonised, every S-COL.BON outline + S-COL.HAT hatch (64 on the slab sheets) |
| "P7757_DXF_COMPRESSED.zip" -> P7757.dxf | ab54dd55... (= manifest) | the released baseline run only |
| freelancer RC workbook | committed cells | tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, sheet 'كمرات' (88 rows, formulas) |

Runs: released baseline A `tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json` on
the working head 48d1d846: **REPRODUCED**, 1,455 lines, BOQ_LINES.csv b96185d4; its STR.CONC.BEAM = 112 measured lines
64.8196 m3 (GF 39.138 / 1F 21.3831 / 2F 4.2985) + 24 bounded 8.449 .. 14.434 = the committed route G register exactly
(PROVISIONAL 112 = 64.8196; UNRESOLVED 24). T-139 `slab_faces.py` and T-110 `bands.py` (fit 0.6 / 0.6 / 0.1 mm) re-run on
the Drive copy. Candidate V3.0.5 .. V3.0.9a beam line = 65.2937 m3 + held 8.224 .. 13.759, 1 blocked (merged package
reports T-179 / T-187 / T-193 / T-231 / T-211: only the 1F west ring moved it): **not an own run**.

Files: `beam_line.py` (BEAM_LINE_V1, pure rules, stdlib + T-229 convex geometry), `t241_extract.py` (private DXF ->
`ALSENAN_PARTITION_INPUT.json`: face ids / classes / areas and the shares of every route G band and column outline, no
coordinates), `t241_alsenan_check.py` (ledger + partition + reconciliation from committed inputs) -> `LEDGER_T241.csv`
(140 runs), `BY_MARK_T241.csv` (his rows vs the runs, per storey and mark), `summary.json`; tests `tests/t241_beam_line`
(28).

## 1. The physical element and the convention (ERS s.2.1, s.3)

- RUN (BOQ CONC.BEAM = STR.CONC.BEAM): the solid of one beam between the faces of the members that SUPPORT it (columns
  under the slab = SOLID hatch on that slab sheet; a deeper beam it frames into), at the printed depth D below the slab
  top, width b. Storey named by the slab sheet (GF = GF roof; T-213 convention, as T-234).
- Convention **C1** stated on every side before any comparison (T-234): the slab panel stops at the beam faces, the beam
  is billed b x D x L at full depth and owns the band area x t. Released route G, the T-110 register, the T-234 slab
  ledger and the freelancer (B x D x L, e.g. B1 0.20 x 0.40) are all C1. C2 (plate over the beams) would move band x t
  to the slab line (`beam_line.convention`), slab + beam unchanged.
- Ownership at intersections (R-CONC-OWN-1, precedence column > beam > slab): a column footprint is the column line's;
  a member that STARTS on the beam (planted column P.C, turned part of a T.C: pattern hatch) never cuts it
  (R-BEAM-CONT-1, T-229); beam / stair heads inside B20 / B23 are the beams' (T-189, the stair ledger deducts them);
  the 1F west dome ring is one B4 run (Q-44 A, T-160); the 2F PC-2F record stops at the B7 soffit (T-220: B7 owns).
- A run ends only at a member it meets in 3-D (T-230): every end in the ledger is a column under the slab or a beam
  (T-229 census 182 ends: 73 at a support, 71 at a beam, 15 at a junction owner, 3 free cantilever ends); no end is a
  footing / neck outline (those are on other sheets, below the soffit).

## 2. Run table per storey (each run once; LEDGER_T241.csv)

Sources per run: T-110 register (merged 575df66: every one of the 119 plan labels bound, schedule row, **drawn width
re-measured from the two edge lines on 103 straight spans**, D from the schedule or the printed section A-A / B-B),
T-229 (merged 3803684e: ends at receiving faces, beside narrower supports, B26 / B27 continuous under the carried P.C,
the 7 column joints billed twice), T-145 (merged: CB5 span 2), this task's partition (two new held pieces).

| Storey (slab sheet) | Runs | Measured m3 (CALCULATED) | CONFLICT runs, m3 | HELD runs, m3 candidate (never 0) |
|---|---|---|---|---|
| GF roof, ST p.4 | 72 | **39.0270** | 4: B29, CB2 x2, B21 (D-27) 3.9585 .. 4.6653 | 7: B3 'With Stair' D-03 0.212 .. 0.3975; strips north of B20 D-05 0.282 .. 0.846; B24 cantilever D-04 0.375 .. 0.5625; B7 contested ring piece 0.035 .. 0.105; new GF-112 0.04 .. 0.12; outer west strip D-26 (no depth: no m3) |
| 1F roof, ST p.5 | 48 | **22.6906** | 3: B6 (D-27), CB10 x2 (D-02) 1.1864 .. 1.4457 | 9: strips / box D-05, one unlabelled span D-04 and the east ring D-28 0.8997: 2.6567 .. 4.9552; D-26 box and 0.10 strip (no m3) |
| 2F roof, ST p.6 | 20 | **4.2985** | 0 | 5: four unlabelled spans D-04 0.562 .. 1.687; new 2F-031 0.10 strip (no m3) |
| **CONC.BEAM** | **140** | **66.0161** | 7: **5.1448 .. 6.1110** | 21: **4.1627 .. 8.6732** + 4 with no value |

New runs this task: **BM-GF-035.2 CB5 span 2** 0.20 x 0.40 x 3.700 = **0.2960** CALCULATED (T-145; its band is GF-097,
billed by no beam line; released A bills its 0.1184 as slab); **BM-GF-062** (face GF-112, 0.20 x 0.50 north of the CB6
support column in line with B4, up to the B7 void ring, no label: HELD, candidate 0.040 .. 0.120 at D 0.40 .. 1.20,
Q-16); **BM-2F-019** (face 2F-031, 0.10 x 4.35 strip west of B15, no tag / bars / depth: HELD, no m3, D-26 family).

Two-source status of b and D: b is two-sourced (schedule + drawn edges, T-110) on every straight run; where they differ
the run is a CONFLICT (7 runs). D is printed once (schedule) except B20 / B23 west spans (printed sections A-A / B-B:
second source, equal). No D is defaulted; the unlabelled pieces carry the T-110 candidate convention as a range.

## 3. Partition check, plan (each face once; ALSENAN_PARTITION_INPUT.json)

Every face of the three slab sheets (T-139 classes, the same 402-face partition T-234 used) against the route G band
polygons and the column outlines, area by area (m2):

| Check | GF | 1F | 2F | Result |
|---|---|---|---|---|
| SLAB panels x beam bands | 0.0915 over 32 panels | 0.0790 / 18 | 0.0105 / 7 | slivers only (max 0.007 per panel = band fit 0.6 mm x edge length): **no band in a slab panel, no panel in a band** (C1 PASS) |
| band over a SOLID column outline (billed twice) | 347, 34A, 34D, 350, 356, 359: 0.4401 m2 | 667 (C9): 0.0090 | 778: 0.0799 | GF + 1F = the T-229 seven joints; x D = 0.2787 m3 vs T-229 0.2778 (re-derived independently, +0.0009); deducted from the beam runs (column owns). 2F 778 = PC-2F under B7: the T-220 record stops at the B7 soffit, so B7 owns it (PASS) |
| band over a PATTERN outline (carried) | 322 under B16 / B21 | 77B under B19 | - | beam runs on, PASS (R-BEAM-CONT-1) |
| carried outline with no band (beam cut) | 0.3497 (P.C 329, 386) | 0 | 0 | B26 / B27 cut at the carried P.C: in the runs (T-229) |
| beam-lane faces uncovered by band and column | 5.3174 | 1.3630 | 0.2844 | split below |
| - named: CB5 span 2 GF-097 | 0.7400 | | | new run 0.296 m3 |
| - named: held strips / boxes / B3 'With Stair' / GF-112 / 2F-031 / void-ring arcs | 2.4033 + 0.3661 edge | 0.6821 + 0.2457 edge | 0.2718 | in HELD runs (never 0); GF void ring arc faces GF-035 / GF-060 0.1171 m2 short of the route G arc bands: not cut-checked (as T-229), HELD finding |
| - beam ends and beside supports (46 / 19 / 4 faces) | 1.8113 + 0.3497 carried | 0.2663 | 0.0057 | vs T-229 strip plan area 1.9046 / 0.3606 / 0: residual **+0.261 / +0.073 / +0.006 m2** (B24 end +0.049, CB8 +0.040, B9 +0.014, the rest < 0.02 per face: drafting-gap closure and the 0.6 mm fit); named, not added (the T-229 strips are the measured ones) |

So: every one of the 136 route G bands (112 released + 24 held) lies in exactly one run (the four 1F west-ring arc bands in the T-110 ring row; 0 unassigned);
every drawn beam face is billed by one run or one named HELD run; the only beam face billed by no line in released A
that the drawings measure is CB5 span 2.

## 4. Line totals vs released A, the candidate and the freelancer (m3)

| Storey | Drawing (this task, measured) | Released A (b96185d4) | Drawing - released, named causes (residual) | Freelancer | Drawing - freelancer |
|---|---|---|---|---|---|
| GF roof | 39.0270 (+ CONFLICT 3.958 .. 4.665, HELD 0.944 .. 2.031 + 1 no value) | 39.1380 (+ bounded 3.755 .. 5.293) | **-0.1110** = B26 / B27 continuous +2.6700; route G held pieces measured (B20 west span by section A-A, B7 strip, B20 upstand) +1.2750; CB5 span 2 +0.2960; T-229 strips net of the 6 column joints +0.1186; released at the schedule width, now CONFLICT -4.4706; residual 0.00003 | 42.8829 | -3.8559 |
| 1F roof | 22.6906 (+ CONFLICT 1.186 .. 1.446, HELD 2.657 .. 4.955 + 2 no value) | 21.3831 (+ 4.131 .. 7.453) | **+1.3075** = B23 west span (section B-B) + B23 upstand +1.1325; west ring B4 0.7553 replacing the arc bands 0.2811 +0.4742; T-229 strips net of C9 +0.2526; B6 now CONFLICT -0.5519; residual -0.00003 | 17.0270 (his I82; his own page sum I79 = 17.155) | +5.6636 |
| 2F roof | 4.2985 (+ HELD 0.562 .. 1.687 + 1 no value) | 4.2985 (+ 0.562 .. 1.687) | 0.0000 (no change) | 6.0560 | -1.7575 |
| **CONC.BEAM** | **66.0161** (CONFLICT **5.145 .. 6.111** apart; HELD **4.163 .. 8.673** + 4 no value) | **64.8196** (+ 8.449 .. 14.434) | **+1.1965**, closed per storey to named causes | **65.9659** | **+0.0502 (+0.08 %)** |

Candidate V3.0.9a (65.2937, merged reports): drawing - candidate = +0.7224 = the released causes above less the west
ring (+0.4742, already in the candidate).

**The +0.08 % against the freelancer is a coincidence, not agreement** (as T-110 warned): by storey and mark
(BY_MARK_T241.csv, his 67 measured rows / my 140 runs):

| Class | Marks | Drawing m3 | His m3 | Meaning |
|---|---|---|---|---|
| on the drawing AND in his sheet | 47 | 61.278 .. 62.245 | 66.094 (incl. the 0.128 row his total drops) | his lengths run through the supports (e.g. CB5 7.10 m vs 2.300 + 3.700 between faces, T-145; CB8 17.9 m), he prices the HELD unlabelled / projection pieces under the neighbour's mark (B24 5.75 m = span + cantilever D-04; B15 6.8 m = B15 + the unlabelled 3.1 m D-04) and the D-27 spans at the schedule width: RULE_DIFFERENCE (through-support length) + scope we HOLD (Q-16 / Q-61 C) |
| on the drawing, NOT in his beam sheet under that mark | 6: GF B27 4.192, B28 0.212, CA 0.173; 1F B19 1.624, B25 2.850, B5 0.833 | **9.883** | 0 (no 'B27 / B25 / B19' text in any of his 17 sheets) | labelled on the slab plans (T-110: 119 labels bound): FREELANCER omission by row, offset by the through-support lengths above |
| his formula slip | - | - | -0.128 | 'كمرات' I82 = SUM(I60:I78) leaves out row 59 (1F B1 0.20 x 0.40 x 1.60 = 0.128) that his own page sum I79 = SUM(I59:I78) = 17.155 carries; his total I100 uses I82 |

## 5. Consultant items carried as ranges (never their larger end)

| Item | Runs | Range m3 | Status |
|---|---|---|---|
| D-02 CB10 width (schedule 25 / drawn 30) | 1F CB10 x2 | 0.744 .. 0.8925 | CONFLICT |
| D-27 schedule vs drawn width | GF B29, CB2 x2, B21; 1F B6 | 4.401 .. 5.2185 (with the T-229 strips at each reading) | CONFLICT |
| D-03 'B3 (With Stair)' vs CB3 | GF CB3 span 2 | 0.212 .. 0.3975 | HELD |
| D-04 unlabelled / contested pieces (+ GF-112 new) | GF 3 (B24 cantilever, B7 ring piece, GF-112), 1F 1, 2F 4 | 1.076 .. 2.6665 | HELD |
| D-05 / D-26 projection strips and boxes (+ 2F-031 new) | GF 3, 1F 7, 2F 1 | 1.975 .. 4.7095 where a candidate exists; 4 with no depth: no m3 | HELD |
| D-28 east dome ring (no B4 mark) | 1F | 0.8997 | HELD |
| D-16 C8 30x80 vs 30x90 | ends of B26 / B28 at the turned part of C8 | if 0.90 and the extra 0.10 lies towards them: -0.055 / -0.019 (not applied; the drawn 0.80 outline is the face the edges stop at) | sensitivity, stated |
| D-63 lift columns / D-65 undrawn upper columns | no beam run is cut at them (route G cuts only at drawn S-COL.BON outlines; the lift members are on the foundation / column plans) | 0 effect on CONC.BEAM | named, no hold |

## 6. Verdict proposals (for the Checker)

| Item | Proposal |
|---|---|
| 140 runs, measured 66.0161 m3 | DRAWING-CONFIRMED pieces (T-110 / T-229 / T-145 merged, re-joined here; partition re-derived from the DXF); **PARTIALLY CLOSABLE**: the measured component is closable once the Checker re-measures a sample per storey; the CONFLICT (5.145 .. 6.111) and HELD (4.163 .. 8.673 + 4) components stay apart, never their larger end |
| released A 64.8196 | ENGINE_WRONG on: CB5 span 2 missing (0.296; its band billed as slab 0.1184), B26 / B27 cut at carried members and held (2.670), the T-229 strips and 7 double joints (net +0.371), the 5 D-27 spans + CB10 released at the schedule width (4.470 + 0.552 now CONFLICT); ENGINE_RIGHT on every other released piece (re-joined unchanged; T-110 widths, T-229 ends) |
| candidate V3.0.9a 65.2937 | as released, without the ring item; the integration (lane I, T-146 / a V3.0.x package) takes CB5 span 2 into CONC.BEAM and out of CONC.SLAB in the same package as T-234's 13 non-slab faces |
| freelancer 65.9659 | FREELANCER_RIGHT nowhere proven per member; RULE_DIFFERENCE on lengths through supports (C1 at faces vs his centre / through lengths); FREELANCER omission of 6 labelled marks (9.883 m3); his 1F total formula slip -0.128; the near-equal totals are a coincidence |

Checker re-measure list: (1) one run per storey from the edge lines: GF CB5 span 2 (edges x 52.693 / 52.893 between
the B1 face y 41.248 and the B20 face y 44.948 = 3.700) and GF B22 (T-110: 7.80); 1F B25 (BAND0032, drawn 0.55 x 0.75 x 6.8754 = 2.850, not in his sheet) and 1F B19 end at C9 (T-229
0.0289); 2F B7 (6.60) and 2F B15 (BAND0006.2, 1.20 deep); (2) every
CONFLICT run: CB10 (D-02), B29 / CB2 / B21 / 1F B6 (D-27) drawn widths on the edge lines; (3) the seven column joints
347 / 34A / 34D / 350 / 356 / 359 / 667 (SOLID hatch) under their bands and 778 under 2F B7 (T-220); (4) faces GF-097,
GF-112, 2F-031 on p.4 / p.6 (no band, no label); (5) re-run: `python3 -I research/agents_t139/slab_faces.py <dxf> faces.json`,
`python3 -I research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g bands.json`,
`python3 -I research/agents_t241/t241_extract.py <dxf> faces.json bands.json`, `python3 -I research/agents_t241/t241_alsenan_check.py`.

## 7. Rule, test, lessons row

General rule proposed (every villa; provenance T-241; a new rule version when adopted, R-BEAM-LINE-1): a beam line is
closed only when (a) every drawn beam face of every slab sheet is billed by exactly one run or one named HELD run (an
area partition against the slab panels and the column footprints, C1 stated), (b) every run ends at a member it meets
in 3-D, (c) the width is two-sourced (schedule and drawn edges) and a difference is a CONFLICT range, (d) a total is
compared with another side only by storey AND mark, because equal totals can hide offsetting scope and convention
differences.
Test: tests/t241_beam_line (Villa B: two spans with a carried P.C, an edge beam, a width CONFLICT, an unlabelled piece;
m / cm / mm, rotation 0 / 30 / -47.5 mirrored / 90; adverse: the cut at a carried member kept, a CONFLICT collapsed to
either end, HELD released or 0, a run twice in the line, a footing outline below the soffit as an end, a member above
the beam as an end, an unprinted level as an end, a finished level as a structural top, a slab plate over the beams
(DOUBLE = band area), a band through two columns (DOUBLE 0.150 m2), a band in beam AND slab, an unstated convention;
metamorphic row order; Alsenan ledger pinned: 140 runs, 66.0161, ranges, partition, the 6 unmatched marks, his slip).
Lessons row (proposed): 2026-10-23 | CONC.BEAM drawing 66.016 vs freelancer 65.966 m3 (+0.08 %) looked closed | the
totals agree by offset: he omits six labelled marks (9.883) and runs every other beam through its supports and over the
held pieces (+3.85 .. +4.82), and one 0.128 row falls out of his own sum | compare a line by storey and mark (or member)
before any total is called agreement; an equal total is never evidence (every villa, every trade) |
tests/t241_beam_line test_freelancer_cells_and_slip (pinned) + test_reconcile_names_the_residual (adverse) | PROPOSED.

## 8. Not done / uncertain

- The candidate figure is from the merged package reports, not an own run of V3.0.9a.
- Lengths of the released pieces are route G's re-joined (T-110 re-measured 5, T-229 checked every end and cut, this
  task's partition checks every drawn face by area); no new per-run length re-measure beyond the partition.
- The GF void-ring arc faces (0.117 m2 short of the route G arc bands) and the per-face end residual 0.261 m2 (GF) /
  0.073 m2 (1F) are named, not added.
- Formwork / rebar of the changed runs: other tasks. Nothing released.
