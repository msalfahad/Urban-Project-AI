# T-242 Whole-line closure: CONC.GROUND, every ground / tie beam once (Alsenan; every villa)

Worker 1 (lane S), 2026-10-24, run unknown. Research piece, not wired: no engine, candidate or released line changed;
integration is a lane I package after the Checker's verdict. Development villa, not an accuracy claim. Drawings named
by Drive folder and title; entities by DXF handle / span id / panel id; lengths, areas, volumes only (no coordinates).

## 0. Inputs and runs (own, this task)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179...38079 | GROUND BEAMS PLAN: layer-1 band edges (85 lines, 4 arcs), S-COL.BON, S-BW lift ring, S-BOUN 7FE / 7FC / 810, the 14 LEVEL marks; FOUNDATION PLAN footings (moved by the frame pitch, T-141) |
| "ST7757.pdf" | 74da1523...337e3 | p.13 the four "Ground Beams" sections (exterior section re-read at 400 dpi: top "Ground Floor slab level", underside "Outer Normal ground level", depth "FOLLOW ARCH."); p.14 TYPICAL BOUNDARY WALL plan "GROUND BEAM (20x40)" and section A-A (upper G.B 20 x 40, top at N.G. LEVEL) |
| "P7757_DXF_COMPRESSED.zip" -> P7757.dxf | ab54dd55...31cc4 | GF plan: layers 1 / W / D, 30 S-COL.BON columns, 14 LEVEL marks |
| freelancer RC workbook | committed cells | tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, sheet 'الشناجات' rows 11-16, 'ورقة1' row 18 |

Runs: released baseline A `tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json`
on the working head 1cc1a153: **REPRODUCED**, 1,455 lines, BOQ_LINES.csv b96185d4 (its ARCH_WALLS.json and
ARCH_ROOMS.json are inputs of the extract: the architectural GF topology, not a quantity). Candidate:
`research/agents_t167/v304_run.py` own run on the same copies: V3.0.4 (and its v29 / v210 / v211 / v212 / restricted
runs) carry the same 58 ground-beam and 25 ground-slab lines; V3.0.5 .. V3.0.9 change no STR.CONC.GROUND_* line per
their merged package reports (T-179 / T-187 / T-193 / T-231 / T-211); the V3.0.9 chain itself was not finished here.
Files: `ground_line.py` (GROUND_LINE_V1, pure rules, stdlib), `t242_extract.py` (private DXFs + the two A-run JSONs
-> values-only `ALSENAN_GROUND_INPUT.json`), `t242_alsenan_check.py` (-> `LEDGER_T242.csv` 91 rows, `summary.json`);
tests `tests/t242_ground_line` (23: Villa G hand fixture + adverse + Alsenan ledger pinned).

## 1. The physical elements of the keyed line (ERS s.2.1)

The keyed reference line CONC.GROUND (tests/alsenan/T001B_KEY_MAP.json; freelancer 'ورقة1' row 18 = 'الشناجات'!I16 =
75.09 m3) carries **STR.CONC.GROUND_BEAM and STR.CONC.GROUND_SLAB**: his ground slab 295.5 m2 x 0.10 = 29.55, his
'longitudinal' 0.30 x 0.60 x 100 = 18.00 and 'transverse' 0.30 x 0.60 x 111 = 19.98 tie beams, his 'شناج السور'
boundary beam 0.30 x 0.60 x 42 = 7.56. Components, each with its own status:

1. **Ground-beam run** (tie beam at GF slab level): b x D x L between the faces of what it meets in 3-D (printed neck,
   lift-pit ring, another ground beam; T-230: never a footing outline, 0.28 m+ below the soffit). Its section depends
   on its POSITION: interior (p.13 length classes 0.30 x 0.60 > 5 m, 0.30 x 0.40 < 5 m, 0.30 x 0.30 < 2.5 m, the first
   two "without concentrated load"), exterior (slab on one side, outside ground on the other: 0.30 wide, D = GF slab
   level - outer normal ground level), or court (outside ground both sides: no printed section). Tops (T-214): main
   house +0.95, annex +0.25; outer ground printed as the existing +-0.00 or the court +0.15 (T-206 / T-214; which: D-35).
2. **Curved runs**: the annex arc 139 / 13A (quarter ring) and the main-house ring 157 / 158 round the pool court.
3. **Boundary-wall ground beam at natural ground** (p.14 upper G.B 0.20 x 0.40) on S-BOUN 7FE / 7FC / 810, where no
   building stands on the plot line (T-065 M3). It has NO line in released A or the candidate.
4. **Ground slab** (slab on grade, 'T=10cm', T-206 DRAWING-CONFIRMED): the panels between the ground-beam faces
   (convention C1 as T-234 / T-241: the beam is billed full depth from the slab top and owns its strip).

## 2. Interior, exterior or court: four independent readings (answered run by run)

No earlier record settled it: the pre-S5 register (S5 / T-138) marks it "ARCHITECTURAL_EXTERIOR_WALL_OVERLAY_PENDING
(Q-R4-6)", and the candidate releases its 24 "perimeter" beams at the interior class depth because it found "no
architectural wall evidence". This task did the overlay:

- **Sheet placement**: the ground-beam sheet carries copies of the architect's 14 GF level marks; the one translation
  that maps all 14 architectural LEVEL texts onto structural ones of the same value (0.0 mm) places the GF plan; check:
  all 30 architectural columns land on structural columns (residual <= 0.071 m = half the drawn width difference,
  0.20 / 0.25 architectural vs 0.30 structural).
- **S1 printed levels**: faces of the band edges + columns + ring + boundary bands + the architectural walls / windows /
  doors; a probe 0.40 m outside each band face at 1/4, 1/2, 3/4 of the span reads OUT (court +0.15 or beyond the plot
  line), IN (+1.00 / +0.30) or no mark.
- **S2 architectural wall on the beam** (ARCH_WALLS.json GF, within 0.20 m of the axis, parallel, overlap > 0.10 m):
  EXTERIOR when one of its sides is the exterior.
- **S3 pre-S5 register** (its two outline tests as T-138 carries them).
- **S4 slab panels by side**: the panel enclosed by beams on each side of the run and its cover by the architectural
  GF rooms (ARCH_ROOMS.json).

Rule (`ground_line.classify`): exterior only with S1 plus S2 or S3 (or S2 plus S3 when S1 has no mark); rooms on both
sides with no printed outside side -> interior; outside on one side and a room-less enclosed panel on the other ->
court; a reading the printed levels contradict never wins; one source alone never classifies an exterior beam.

| Class | Runs | Notes |
|---|---|---|
| EXTERIOR | 24 straight + 2 curved | 16 straight + the ring in the main house; 8 + the arc in the annex; 21 of the 24 straight ones carry an architectural wall with an EXTERIOR side (S2) |
| INTERIOR | 32 | 109+7CB#1, 114+115+7DF#1, 180D+180E#1 (S3 'EXT or interior') settled by S4: rooms on both sides |
| COURT | 3 | 1811+1812#1 (court +0.15 both sides, free end on the plot line); 178+7DB#1 and 185+7C7#1 (the outdoor stair court on one side, the room-less strip GS-16 on the other) |

Disagreements resolved on the evidence: 10A+7C9#1 and 10B+7D1#1 / #2 are interior walls for the architectural topology
(S2: its plate includes the passage), but the passage between the two building parts carries the court level +0.15 on
both sheets (S1) and S3 reads them exterior: EXTERIOR. 13E+7D6#2 (0.50 m to the annex arc): S1 + S2 exterior against
S3: EXTERIOR.

## 3. Run table (each run once; LEDGER_T242.csv)

Lengths: GROUND_SYSTEM_SPANS_V2 face to face (T-141, 52 / 53 equal to the T-138 hand within 0.3 mm), with the three
lift-ring ends of T-230 (15D+7C8#1 2.900, 17C+7E3#1 3.228, 177+7CD#1 5.020 m) and the T-230 neck readings per end
(DOUBLE removed at the four drafting-note ends, 0.030 m2 each; GAP beside C3 / CN / C8 / lift C2 added once, to one
run; the C8 and lift-C2 section CONFLICTs kept as ranges). Every p.13 title that holds on the face-to-face or the
centreline basis is kept (D-34). D-33: a tee or crossing between the run's two faces (the band's junction list
filtered to the run).

| Component | Runs | CALCULATED m3 | HELD / CONFLICT m3 | What holds it |
|---|---|---|---|---|
| Interior, closable | 5 | **2.2684** | | 109+7CB#1 0.5280, 17C+7E3#1 0.3874, 7DC+7DD#2 0.4230, 7E7+7E8#1 0.4230, 7E9+7EA#1 0.5070 |
| Interior, D-33 | 12 | | 6.5919 (one candidate each) | another beam lands between the faces; p.13 prints only "without concentrated load" |
| Interior, D-34 | 8 | | 1.1328 .. 1.5225 | under 2.5 m 'less than 2.5 m' AND 'less than 5 m' hold literally; or the basis moves the class; 184+7CF#3 exactly 5.00 |
| Interior, D-33 + D-34 | 5 | | 1.3661 .. 1.9258 | both |
| Interior, neck CONFLICT | 2 | | 0.6764 .. 0.6964 | 184+7CF#1 / #2 at C8 (24D): 0.30 x 0.80 drawn vs 0.30 x 0.90 schedule (T-217) |
| **Interior** | **32** | **2.2684** | **9.7673 .. 10.7365** | |
| Exterior, main house (D-35) | 16 + ring | | **13.4400 .. 15.9600** | D 0.80 .. 0.95 (top +0.95 to the court +0.15 / existing +-0.00) |
| Exterior, annex (CONFLICT) | 8 + arc | | 0.8912 .. 2.2280 (literal) | top +0.25: the literal depth 0.10 .. 0.25 m is shallower than every printed section while the drawn exterior section holds three bar layers (S5 ANNEX_DEPTH_SOURCE_CONFLICT re-derived): not a candidate quantity |
| Court | 3 | | 0.6270 .. 1.4100 | no printed section; candidates = interior classes and the exterior range |
| **Building ground beams** | **61** | **2.2684** | **24.7254 .. 30.3344** | total range **26.9938 .. 32.6028** |
| Boundary-wall G.B at N.G. | 1 (3 bands) | | <= **3.5256** | 0.20 x 0.40 x 44.07 m (8.814 m2 of band) DRAWING-CONFIRMED solid; the 20 x 30 boundary columns inside it are drawn on no plan (T-065 M4): no established low end |
| **Ground slab** | 29 panels | **20.4328** (27 panels, 204.3284 m2) | 0 .. 1.2304 (2 panels) | GS-12 8.124 m2: the architectural plan names it 'Garden / yard / court' (floored or open: not printed); GS-16 4.180 m2: enclosed by beams beside the outdoor stair court, in no room, no level mark |

**The interior component is NOT closable as a whole** (the Lead's premise "interior runs, which the drawings close"):
of 32 interior runs only 5 (2.2684 m3) carry one printed section on every basis with no member landing on them. D-33
holds 17 runs (7.9580 .. 8.5177), D-34 13 runs (2.4989 .. 3.4483, 5 shared), T-217 2. D-35 holds every exterior run;
the annex exterior is a source conflict, not a range to pick from. The GF stair hall panel (GS-08, 11.52 m2, marks
+0.30 and +1.00) is slab under both levels; the +0.30 lobby step up to +1.00 is the stair's concrete (T-184).

## 4. Partition and overlaps (each piece once)

Drawn ground-beam strips (straight bands at their full drawn extent + the two arc regions) = **62.1441 m2** = spans
54.3118 + columns 4.6437 + arcs net of supports and straight bands 2.3680 + six named pieces 0.8204 (residual
0.0002 m2): 17C+7E3 lift end 0.390 and 15D+7C8 lift end 0.300 (= the T-230 ring lengths, in their runs); the C3 (211)
gap 0.030 (= T-230 GAP, in 13D+7D2#1); the lift C2 (1EF) oblique gap 0.0104 (= T-230, as a range); and a **new corner
square 0.0900 m2 at 10B+7D1 / 7D4+F8 billed by no span** (both bands end in the junction, V2 cuts the zone from both):
owned by the plot-line run 7D4+F8#2. Span x span and span x column overlaps: 0.0000 m2. Unpaired layer-1 face pieces:
18, all <= 0.50 m end pieces at corners (no beam left unpaired). Ground plan: beams + columns + ring 73.8316 m2 + slab
panels 216.6324 m2 = 290.464 m2 inside the beam network, each piece in one component. Boundary bands overlap no
building beam or column (0.0000 m2). Ground beams over footings: no 3-D contact (T-230, gap >= 0.28 m); straps 0.28 m+
below (T-230): nothing shared.

## 5. Line totals vs released A, the candidate and the freelancer (m3)

| Component | Drawing (this task) | Released A (b96185d4) | Candidate (own V3.0.4 run, = V3.0.9 per reports) | Freelancer | Difference, named causes |
|---|---|---|---|---|---|
| Building ground beams | **2.2684 CALCULATED + 24.7254 .. 30.3344 HELD** (26.9938 .. 32.6028) | 59 BOUNDED lines 17.801 .. 59.337 (D 0.30 .. 1.00 on 197.79 m), nothing measured | 58 PROVISIONAL 27.3649: 34 interior 15.4304 (net plan x class) + **24 perimeter 11.9346 released at the interior class depth** ("no architectural wall evidence"; the printed exterior section only its high alternative) | 37.98 (211 m x 0.30 x 0.60) | his - ours = **length +3.558** (his lengths run through the supports: drawn bands 200.04 m + curved 7.89 vs face to face 191.23 m) + **section +1.819 .. +7.428** (0.60 on every beam vs the printed 0.30 / 0.40 / 0.60 interior and 0.80 .. 0.95 exterior); residual 0.0001 |
| Boundary G.B at N.G. | <= 3.5256 (44.07 m x 0.20 x 0.40) | **none** | **none** | 7.56 (42 m x 0.30 x 0.60) | his - drawn = section +4.407 (0.18 vs 0.08 m2) + length -0.373 (42.00 vs 44.07 m) = +4.034 |
| Ground slab | **20.4328 CALCULATED + 0 .. 1.2304 HELD** (204.33 + 12.30 m2) | 23 lines 17.127 (13.341 PROVISIONAL + 3.786 SOURCE_DERIVED) + BOUNDED 4.767: 218.94 m2 at 0.10 | 24 lines 17.2407 + BOUNDED 3.9298: 211.71 m2 | 29.55 (295.5 m2 x 0.10) | his - ours = slab drawn over the beam / column / ring strips 73.83 m2 x 0.10 = **+7.383** (the beams are billed full depth from the slab top: the same concrete twice, C1) + held panels +1.230 + **5.04 m2 unexplained (+0.504)**, his 295.5 a bare number. A: domain +2.31 m2 against ours, its measured / bounded split not traced per panel |
| **CONC.GROUND line** | **22.7012 CALCULATED + HELD** | | | **75.09** | NOT CLOSABLE; not comparable as a whole while held |

## 6. Verdict proposals (for the Checker)

| Item | Proposal |
|---|---|
| 5 interior runs 2.2684 m3 | DRAWING-CONFIRMED pieces (V2 face lengths, T-230 ring end for 17C+7E3#1, one title on both bases, no member landing); re-measurable now |
| ground slab 27 panels 20.4328 m3 | DRAWING-CONFIRMED panels (enclosed by beam faces, each in the architectural GF rooms or carrying a floor level; 'T=10cm'); re-measurable now; 2 panels HELD |
| exterior / court classification | 26 runs EXTERIOR by S1 + S2/S3; 3 COURT; 0 left as candidates (section 2) |
| candidate 24 perimeter lines 11.9346 | **ENGINE_WRONG basis**: exterior beams released at an interior class depth (a convention, T-186 default guard) under "no architectural wall evidence", while 21 of our 24 straight exterior runs carry an architectural GF wall with an EXTERIOR side on the beam and the printed section is FOLLOW ARCH.: drawing 13.440 .. 15.960 (main) + annex CONFLICT, HELD on D-35, never released (the candidate's 24 lines were not paired one to one with ours) |
| candidate 34 interior lines 15.4304 | released runs that D-33 / D-34 hold (27 of our 32 interior runs); ENGINE_RIGHT only on the 5 closable ones after the Checker's re-measure |
| released A / candidate ground slab | A 218.94 m2 vs drawing 216.63 m2 (+2.31 m2, +0.231 m3) in all states; candidate 211.71 m2 (-4.93 m2); split by panel not traced: UNRESOLVED, a lane I comparison |
| boundary G.B at N.G. | missing in A and the candidate (silent omission, <= 3.5256 m3): ENGINE_WRONG (omission) |
| freelancer beams 37.98 | RULE_DIFFERENCE (lengths through supports, +3.558) + section not printed (0.30 x 0.60 on every beam): FREELANCER_WRONG on the section of every interior beam under 5 m and below the D-35 range on every main-house exterior one |
| freelancer boundary 7.56 | FREELANCER_WRONG section: 0.30 x 0.60 is printed for no boundary member (p.14 prints 20 x 40 twice) |
| freelancer slab 29.55 | RULE_DIFFERENCE + double count: his plate runs over the 73.83 m2 of beams he bills full depth; residual 5.04 m2 named, unexplained |
| CONC.GROUND line | BLOCKED BY CONSULTANT (D-33, D-34, D-35, M4) with two slab panels held; measured components 22.7012 m3 re-measurable now |

Checker re-measure list (whole interior closable component + the new pieces): the 5 CALCULATED runs on p.3 / the DXF
(109+7CB#1 from the 7D0 face to column 228, 4.400; 17C+7E3 from the 7E2 face to the ring 7C2 outer face, 3.228;
7DC+7DD#2 column 7F5 to the 177 face, 3.525; 7E7+7E8#1 the 7CF face to column 7ED, 3.525; 7E9+7EA#1 column 7F5 to
column 7ED, 4.225); the corner square 10B+7D1 / 7D4+F8 (0.30 x 0.30); the exterior reading of 10A+7C9 / 10B+7D1 (the
+0.15 mark in the passage between the two parts on both sheets); S-BOUN 7FE (8.344 m2), 7FC (0.230), 810 (0.240) at
0.20 wide; a sample of slab panels (GS-01 24.505 m2, GS-02 22.965, GS-08 11.520 between beam faces); re-run
`t242_extract.py <ST dxf> <P7757 dxf> <A ARCH_WALLS.json> --arch-rooms <A ARCH_ROOMS.json>` and
`t242_alsenan_check.py`.

## 7. Designer items (narrowed; proposed rows for CLARIFICATIONS_CONSULTANT_2026-10-23.md)

- **D-33 narrowed**: no ground beam carries a column (all 36 columns of the ground-beam plan are founded, T-141 /
  T-205); the only point loads are beam-on-beam tees, on 28 runs (17 interior). Ask: "do the p.13 sections apply to a
  ground beam that receives another ground beam?" Impact interior: 7.9580 .. 8.5177 m3 held at the printed-class
  candidates (the loaded section is unquantified).
- **D-34 narrowed**: below 2.5 m both titles hold literally; ask "the most specific title governs, on the face-to-face
  length?" Impact 2.4989 .. 3.4483 m3 (13 runs); 184+7CF#3 is exactly 5.00 m and stays open under any reading.
- **D-35 split**: main house (top +0.95): which outer ground, +-0.00 or the court +0.15 (13.440 .. 15.960 m3); annex
  (top +0.25): the literal depth 0.10 .. 0.25 m cannot hold the drawn section: give the annex exterior beam depth.
- **M4** boundary columns 20 x 30 "SEE ARCH PLAN": positions / count (the beam's own share of 3.5256 m3).
- **Architect**: GS-12 'Garden / yard / court' (8.124 m2 inside the beam network): floored or open? (if open, its four
  bordering interior runs become exterior, D-35).

## 8. Rule, test, lessons row

General rule proposed (every villa; provenance T-242; a new rule version when adopted, R-GB-LINE-1): a ground line is
closed only when (a) every drawn band strip is billed by exactly one run or a named piece (plan partition, corner
squares included) and every enclosed panel by one slab panel; (b) every run ends at a member it meets in 3-D; (c) each
run's POSITION is read before its section: exterior (slab one side, outside ground the other) from the printed levels
plus the architectural wall or the outline test, never one source alone; an exterior run is never released at an
interior class depth; (d) an interior run is released only when one printed title holds on every length basis and no
member lands on it that the title excludes; (e) the keyed line lists every keyed component (beams, curved runs, the
boundary-wall beam, the ground slab) with its own status.
Test: tests/t242_ground_line (Villa G: interior 4.00 m 0.4800, < 2.5 m D-34 range, tee D-33, exterior 0.80 .. 0.95,
annex below-typical CONFLICT, curved by plan area, neck DOUBLE once, mm / cm, S4 by side; adverse: exterior depth
defaulted refused, footing / outline as an end refused, an intersection billed twice refused, held shown as 0 or as
one end refused, a run twice refused, no title -> no default, a court run with no section -> HELD with no value, a line
with a held component not closable; Alsenan ledger pinned).
Lessons row (proposed): 2026-10-24 | The candidate released 24 exterior ground beams at the interior class depth
(11.9346 m3) and the interior runs were expected to close | A ground beam's section depends on its position and no
record had overlaid the architectural walls (Q-R4-6 pending since S5): "no wall evidence found" became interior; the
interior premise ignored D-33 / D-34 | Read a member's position (printed levels + architectural wall + the rooms on
each side) before its typical section; "no evidence found" is HELD, never the interior default (every villa) |
tests/t242_ground_line test_adverse_exterior_depth_never_defaulted + test_classification_sources | PROPOSED.

## 9. Not done / uncertain

- The candidate figures are the own V3.0.4 run; V3.0.5 .. V3.0.9 from their merged reports (no ground change).
- The slab panels are compared with A / the candidate in total only (their per-panel split not traced).
- S2 / S4 use the released A run's architectural topology (ARCH_WALLS / ARCH_ROOMS), not a re-drawn one: an
  engine-derived reading, used only beside the printed levels (S1) and the pre-S5 tests (S3).
- Bars, links and formwork of the changed runs: other tasks. Nothing released.
