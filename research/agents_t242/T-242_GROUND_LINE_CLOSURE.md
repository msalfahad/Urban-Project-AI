# T-242 Whole-line closure: CONC.GROUND, every ground / tie beam once (Alsenan; every villa)

Worker 1 (lane S), 2026-10-24, run unknown. Research piece, not wired: no engine, candidate or released line changed;
integration is a lane I package after the Checker's verdict. Development villa, not an accuracy claim. Drawings named
by Drive folder and title; entities by DXF handle / span id; lengths, areas, volumes only (no coordinates).

## 0. Inputs and runs (own, this task)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179...38079 | GROUND BEAMS PLAN: layer-1 band edges (85 lines, 4 arcs), S-COL.BON, S-BW lift ring, S-BOUN 7FE / 7FC / 810, the 14 LEVEL marks; FOUNDATION PLAN footings (moved by the frame pitch, T-141) |
| "ST7757.pdf" | 74da1523...337e3 | p.13 the four "Ground Beams" sections (re-read at 400 dpi: exterior section top "Ground Floor slab level", underside "Outer Normal ground level", depth "FOLLOW ARCH."), p.14 TYPICAL BOUNDARY WALL plan "GROUND BEAM (20x40)" and section A-A (upper G.B 20 x 40, top at N.G. LEVEL) |
| "P7757_DXF_COMPRESSED.zip" -> P7757.dxf | ab54dd55...31cc4 | GF plan (frame SH05): layers 1 / W / D and 30 S-COL.BON columns, 14 LEVEL marks |
| freelancer RC workbook | committed cells | tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, sheet 'الشناجات' rows 11-16, 'ورقة1' row 18 |

Runs: released baseline A `tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json`
on the working head 1cc1a153: **REPRODUCED**, 1,455 lines, BOQ_LINES.csv b96185d4 (its ARCH_WALLS.json is an input
of the extract). Candidate: `research/agents_t167/v304_run.py` own run on the same copies (V3.0.4 and its v29 / v210 /
v211 / v212 / restricted runs all carry the same 58 ground-beam lines; V3.0.5 .. V3.0.9 change no STR.CONC.GROUND_*
line per their merged package reports, T-179 / T-187 / T-193 / T-231 / T-211; the V3.0.9 chain itself was not
finished in this run).
Files: `ground_line.py` (GROUND_LINE_V1, pure rules, stdlib), `t242_extract.py` (private DXFs -> values-only
`ALSENAN_GROUND_INPUT.json`), `t242_alsenan_check.py` (-> `LEDGER_T242.csv` 62 rows, `summary.json`); tests
`tests/t242_ground_line` (22: Villa G hand fixture + adverse + Alsenan ledger pinned).

## 1. The physical element and the keyed line (ERS s.2.1)

The keyed reference line CONC.GROUND (tests/alsenan/T001B_KEY_MAP.json, freelancer 'ورقة1' row 18 = 'الشناجات'!I16 =
75.09 m3) carries **STR.CONC.GROUND_BEAM and STR.CONC.GROUND_SLAB**: his ground slab 295.5 m2 x 0.10 = 29.55, his
'longitudinal' 0.30 x 0.60 x 100 = 18.00 and 'transverse' 0.30 x 0.60 x 111 = 19.98 tie beams, and his 'شناج السور'
boundary beam 0.30 x 0.60 x 42 = 7.56. Physical components, each with its own status:

1. **Ground-beam run** (tie beam at GF slab level): b x D x L between the faces of what it meets in 3-D (printed neck,
   lift-pit ring, another ground beam; T-230: never a footing outline, 0.28 m+ below the soffit). Its section depends
   on its POSITION: interior (p.13 length classes 0.30 x 0.60 > 5 m, 0.30 x 0.40 < 5 m, 0.30 x 0.30 < 2.5 m, the first
   two "without concentrated load") or exterior (slab on one side, outside ground on the other: 0.30 wide, top = GF
   slab level, underside = outer normal ground level). Tops (T-214): main house +0.95, annex +0.25; outer ground
   printed as the existing +-0.00 or the court +0.15 (T-206 / T-214, which one: D-35).
2. **Curved runs**: the two arc bands (annex 139 / 13A quarter ring, main-house 157 / 158 ring round the pool court).
3. **Boundary-wall ground beam at natural ground** (p.14 upper G.B 0.20 x 0.40) on S-BOUN 7FE / 7FC / 810, where no
   building stands on the plot line (T-065 M3). It has NO line in released A or the candidate.
4. **Ground slab**: keyed, not re-measured here (section 6).

## 2. Interior or exterior: three independent readings (the question the task asked, answered run by run)

No earlier record settled it: the pre-S5 register (T-138 / S5) marks it "ARCHITECTURAL_EXTERIOR_WALL_OVERLAY_PENDING
(Q-R4-6)", and the candidate releases its 24 "perimeter" beams at the interior class depth because it found "no
architectural wall evidence". This task did the overlay:

- **Sheet alignment**: the architectural GF plan sits on the ground-beam sheet by one translation; all 30
  architectural columns pair with a structural column (residual <= 0.071 m = half the drawn width difference, 0.20 /
  0.25 architectural vs 0.30 structural) and all 14 LEVEL marks of the two sheets pair with the same value at 0.0 mm.
- **S1 (printed levels, structural sheet)**: faces of the band edges + columns + ring + boundary bands + the
  architectural walls / windows / doors; probe 0.40 m outside each band face at 1/4, 1/2, 3/4 of the span; a side is
  OUT at the court level +0.15 or beyond the plot line, IN at +1.00 / +0.30.
- **S2 (architectural wall on the beam)**: the GF wall of ARCH_WALLS.json (released A) within 0.20 m of the beam axis,
  parallel, overlap > 0.10 m; EXTERIOR when one of its sides is the exterior.
- **S3 (pre-S5 register)**: its two outline tests as T-138 carries them (EXT / EXT or interior / interior).

Rule (`ground_line.classify`): exterior only with S1 plus S2 or S3 (or S2 plus S3 when S1 has no mark); a reading the
printed levels contradict never wins; one source alone never classifies an exterior beam.

| Class | Runs (straight + curved) | Notes |
|---|---|---|
| EXTERIOR | 25 + 2 | 18 main house (ring 157 / 158 included), 9 annex (arc 139 / 13A included) |
| INTERIOR | 29 | |
| CANDIDATES | 4 | 109+7CB#1 (no wall, no outside side), 114+115+7DF#1, 178+7DB#1 (beside the outdoor stair court), 180D+180E#1 |
| COURT | 1 | 1811+1812#1: court +0.15 on both sides, free end on the plot line (V2 held it): no printed section applies |

Where the readings disagreed: 10A+7C9#1, 10B+7D1#1 / #2 are interior walls for the architectural topology (S2), but
the passage between the two parts carries the court level +0.15 (S1) and S3 reads them exterior: EXTERIOR (the slab
stops at the beam, outside ground beyond it). 13E+7D6#2 (0.50 m into the annex arc): S1 + S2 exterior, S3 interior:
EXTERIOR.

## 3. Run table (each run once; LEDGER_T242.csv)

Lengths: GROUND_SYSTEM_SPANS_V2 face to face (T-141, 52 / 53 equal to the T-138 hand within 0.3 mm), with the three
lift-ring ends of T-230 (15D+7C8#1 2.900, 17C+7E3#1 3.228, 177+7CD#1 5.020 m) and the T-230 neck readings per end
(DOUBLE removed at the four drafting-note ends 0.030 m2 each; GAP beside C3 / CN / C8 / lift C2 added once; the C8 and
lift-C2 section CONFLICTs kept as ranges). Every title that holds on the face or centreline basis is kept (D-34).

| Component | Runs | CALCULATED m3 | HELD / CONFLICT m3 | What holds it |
|---|---|---|---|---|
| Interior, closable | 4 | **1.7404** | | 17C+7E3#1 0.3874, 7DC+7DD#2 0.4230, 7E7+7E8#1 0.4230, 7E9+7EA#1 0.5070 |
| Interior, D-33 | 12 | | 6.5919 (one candidate each) | another beam ends on the span between its faces; p.13 prints only "without concentrated load" |
| Interior, D-34 | 7 | | 0.9236 .. 1.2435 | span under 2.5 m: 'less than 2.5 m' AND 'less than 5 m' hold literally; or the basis moves the class |
| Interior, D-33 + D-34 | 4 | | 1.1771 .. 1.6738 | both |
| Interior, neck CONFLICT | 2 | | 0.6764 .. 0.6964 | 184+7CF#1 / #2 at C8 (24D): 0.30 x 0.80 drawn vs 0.30 x 0.90 schedule (T-217) |
| **Interior** | **29** | **1.7404** | **9.3690 .. 10.2055** | |
| Exterior, main house (D-35) | 17 + ring | | **13.5840 .. 16.1310** | D 0.80 .. 0.95 (top +0.95 to the court +0.15 / existing +-0.00) |
| Exterior, annex (CONFLICT) | 8 + arc | | 0.8912 .. 2.2280 (literal) | top +0.25: the literal FOLLOW ARCH. depth 0.10 .. 0.25 m is shallower than every printed section while the drawn section holds three bar layers (S5 ANNEX_DEPTH_SOURCE_CONFLICT re-derived): not a candidate quantity |
| Candidates + court | 5 | | 1.4993 .. 3.7541 | section not established (interior classes or exterior range) |
| **Building ground beams** | **61** | **1.7404** | **25.3434 .. 32.3186** | total range **27.0838 .. 34.0590** |
| Boundary-wall G.B at N.G. | 1 (3 bands) | | <= **3.5256** | 0.20 x 0.40 x 44.28 m (8.814 m2 of band) DRAWING-CONFIRMED solid; the 20 x 30 boundary columns inside it are drawn on no plan (T-065 M4): no established low end |
| Ground slab | - | not measured | | keyed STR.CONC.GROUND_SLAB |

**The interior component is NOT closable as a whole** (the Lead's premise "interior runs, which the drawings close"):
of 29 interior runs only 4 (1.7404 m3) have one printed section on every basis with no beam landing on them. The
rest wait on D-33 (16 runs: is a ground beam that carries another ground beam a "concentrated load"?), D-34 (11 runs:
title precedence below 2.5 m and the length basis) and T-217 (2 runs). D-35 holds every exterior run.

## 4. Partition and overlaps (each piece once)

Drawn ground-beam strips (straight bands at their full drawn extent + the two arc regions) = **62.1441 m2** = spans
54.3118 + columns 4.6437 + arcs net of supports and straight bands 2.3680 + six named pieces 0.8204 (residual
0.0002 m2): 17C+7E3 lift end 0.390 and 15D+7C8 lift end 0.300 (= the T-230 ring lengths, now in their runs); the C3
(211) gap 0.030 (= T-230 GAP, in 13D+7D2#1); the lift C2 (1EF) oblique gap 0.0104 (= T-230, as a range); and a **new
corner square 0.0900 m2 at 10B+7D1 / 7D4+F8 billed by no span** (both bands end in the junction, V2 cuts the zone from
both): owned by the plot-line run 7D4+F8#2 (annex exterior). Span x span and span x column overlaps: 0.0000 m2.
Unpaired layer-1 face pieces: 18, all <= 0.50 m end pieces at corners (no beam left unpaired). Boundary bands 7FE /
7FC / 810 overlap no building beam or column (0.0000 m2). Ground beams over footings in plan: no 3-D contact (T-230,
gap >= 0.28 m), nothing deducted; straps (SB1-3) lie 0.28 m+ below (T-230), nothing shared.

## 5. Line totals vs released A, the candidate and the freelancer (m3)

| Component | Drawing (this task) | Released A (b96185d4) | Candidate (own V3.0.4 run, = V3.0.9 per reports) | Freelancer | Difference, named causes |
|---|---|---|---|---|---|
| Building ground beams | **1.7404 CALCULATED + 25.3434 .. 32.3186 HELD** (27.0838 .. 34.0590) | 59 BOUNDED lines 17.801 .. 59.337 (D 0.30 .. 1.00 on 197.79 m), nothing measured | 58 PROVISIONAL 27.3649: 34 interior 15.4304 (net plan x class) + **24 perimeter 11.9346 released at the interior class depth** ("no architectural wall evidence"; the printed exterior section only its high alternative) | 37.98 (211 m x 0.30 x 0.60) | his - ours = **length +3.558** (his lengths run through the supports: drawn bands 200.04 m + curved 7.89 vs face to face 191.23 m) + **section +0.363 .. +7.338** (0.60 on every beam vs the printed 0.30 / 0.40 / 0.60 interior and 0.80 .. 0.95 exterior); residual 0.0001 |
| Boundary G.B at N.G. | <= 3.5256 (44.28 m x 0.20 x 0.40) | **none** | **none** | 7.56 (42 m x 0.30 x 0.60) | his - drawn = section +4.428 (0.18 vs 0.08 m2 printed) + length -0.410 (42.00 vs 44.28 m) = +4.034 |
| Ground slab | not measured | 13.341 PROVISIONAL + 3.786 SOURCE_DERIVED + BOUNDED 4.767 | 13.4548 + 3.7859 + BOUNDED 3.9298 | 29.55 (295.5 m2 x 0.10) | not reconciled here |
| **CONC.GROUND line** | **NOT CLOSABLE** | (beams unmeasured) | | **75.09** | not comparable as a whole while held |

## 6. Verdict proposals (for the Checker)

| Item | Proposal |
|---|---|
| 4 interior runs 1.7404 m3 | DRAWING-CONFIRMED pieces (V2 face lengths, T-230 ring end for 17C+7E3#1, one title on both bases, no tee); re-measurable now |
| exterior classification | 27 runs EXTERIOR by S1 + S2/S3 (section 2); 4 CANDIDATES and 1 COURT held |
| candidate 24 perimeter lines 11.9346 | **ENGINE_WRONG basis**: an exterior beam released at an interior class depth (a convention, T-186 default guard) under "no architectural wall evidence", while 22 of the 25 straight exterior runs here carry an architectural GF wall with an EXTERIOR side on the beam (S2) and the printed section is FOLLOW ARCH.; drawing 13.584 .. 16.131 (main) + annex CONFLICT; HELD on D-35, never released (the candidate's 24 lines were not paired run by run with ours) |
| candidate 34 interior lines 15.4304 | ENGINE released runs that D-33 / D-34 hold (25 of our 29 interior runs); ENGINE_RIGHT on the 4 closable ones only after the Checker's re-measure |
| released A ground beams | bounded only; no ground-beam quantity to verify; the boundary G.B at N.G. is missing in A and the candidate (silent omission, <= 3.5256) |
| freelancer beams 37.98 | RULE_DIFFERENCE (lengths through supports, +3.558) + section not printed (0.30 x 0.60 everywhere): FREELANCER_WRONG on the section of every interior beam under 5 m and below the D-35 range on every main-house exterior one |
| freelancer boundary 7.56 | FREELANCER_WRONG section: 0.30 x 0.60 is printed for no boundary member (p.14 prints 20 x 40 twice) |
| CONC.GROUND line | BLOCKED BY CONSULTANT (D-33, D-34, D-35, M4 boundary columns) and NOT MEASURED (ground slab) |

Checker re-measure list (whole interior component + the new pieces): the 4 CALCULATED runs on p.3 / the DXF
(17C+7E3 from the 7E2 face to the ring 7C2 outer face 3.228; 7DC+7DD#2 column 7F5 to the 177 face 3.525; 7E7+7E8#1
the 7CF face to column 7ED 3.525; 7E9+7EA#1 column 7F5 to column 7ED 4.225); the corner square 10B+7D1 / 7D4+F8
(0.30 x 0.30); the exterior reading of 10A+7C9 and 10B+7D1 (the +0.15 mark in the passage between the two parts on
both sheets); S-BOUN 7FE (8.344 m2), 7FC (0.230), 810 (0.240) at 0.20 wide; re-run `t242_extract.py <ST dxf> <P7757
dxf> <ARCH_WALLS.json of the A run>` and `t242_alsenan_check.py`.

## 7. Designer items (narrowed; proposed rows for CLARIFICATIONS_CONSULTANT_2026-10-23.md)

- **D-33 narrowed**: no ground beam carries a column (all 36 columns of the ground-beam plan are founded on footings /
  necks, T-141 / T-205); the only point loads are beam-on-beam tees, on 28 runs (16 interior, 11 exterior, 1
  candidate). Ask: "do
  the p.13 sections apply to a ground beam that receives another ground beam (a tee)?" Impact interior: 7.7690 ..
  8.2657 m3 held at their printed-class candidates (the loaded section is unquantified).
- **D-34 narrowed**: below 2.5 m both titles hold literally; ask "the most specific title governs, on the face-to-face
  length?" Impact 2.1007 .. 2.9173 m3 (11 runs); 184+7CF#3 is exactly 5.00 m and stays open under any reading.
- **D-35 split**: main house (top +0.95): which outer ground, +-0.00 or the court +0.15 (13.584 .. 16.131 m3); annex
  (top +0.25): the literal depth 0.10 .. 0.25 m cannot hold the drawn section: give the annex exterior beam depth.
- **M4** boundary columns 20 x 30 "SEE ARCH PLAN": positions / count (the beam's own share of 3.5256 m3).

## 8. Rule, test, lessons row

General rule proposed (every villa; provenance T-242; a new rule version when adopted, R-GB-LINE-1): a ground-beam
line is closed only when (a) every drawn band strip is billed by exactly one run or a named piece (plan partition,
corner squares included), (b) every run ends at a member it meets in 3-D, (c) each run's POSITION is read before its
section: exterior (slab one side, outside ground the other) from the printed levels of the sheet plus the
architectural wall or the outline test, never from one source alone, and an exterior run is never released at an
interior class depth, (d) an interior run is released only when one printed title holds on every length basis and no
member lands on it that the section's title excludes, (e) the keyed line lists every keyed component (beams, curved
runs, the boundary-wall beam, the ground slab) with its own status.
Test: tests/t242_ground_line (Villa G: interior 4.00 m 0.4800, < 2.5 m D-34 range, tee D-33, exterior 0.80 .. 0.95,
annex below-typical CONFLICT, curved by plan area, neck DOUBLE once, mm / cm; adverse: exterior depth defaulted
refused, footing / outline as an end refused, an intersection billed twice refused, held shown as 0 or as one end
refused, a run twice refused, no title -> no default, a court run with no section -> HELD with no value, line with an
unmeasured component not closable; Alsenan ledger pinned: alignment, partition conservation, 29 / 27 / 1 / 4, 1.7404,
13.584 .. 16.131, 3.5256, the corner square, no exterior run released, the freelancer cells).
Lessons row (proposed): 2026-10-24 | The candidate released 24 exterior ground beams at the interior class depth
(11.9346 m3) and the Lead expected the interior runs to close | The section of a ground beam depends on its position,
and no record had overlaid the architectural walls (Q-R4-6 pending since S5): the engine took "no wall evidence found"
as interior; the interior premise ignored D-33 / D-34 | Read a member's position (printed levels + architectural
wall) before its typical section; "no evidence found" is HELD, never the interior default (every villa) |
tests/t242_ground_line test_adverse_exterior_depth_never_defaulted + test_classification_sources | PROPOSED.

## 9. Not done / uncertain

- Ground slab (STR.CONC.GROUND_SLAB) not re-measured: the line stays NOT CLOSABLE; proposed follow-up row (slab panels
  between the beam faces under C1, thickness from the printed note, the lift opening and the stair zone out).
- The candidate figures are the own V3.0.4 run; V3.0.5 .. V3.0.9 from their merged reports (no ground-beam change).
- Bars, links and formwork of the changed runs: other tasks. Nothing released.
