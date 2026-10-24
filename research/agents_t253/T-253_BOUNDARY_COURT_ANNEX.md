# T-253 CONC.GROUND, the parts the drawings settle without the consultant (Alsenan; every villa)

Worker 1 (lane S), 2026-10-24, run session_016pExpFZGA45T4G8EijnJcx. Research piece, not wired: no engine, candidate or
released line changed; integration is lane I (T-254) after the Checker's verdict. Development villa, not an accuracy
claim. Drawings named by Drive folder and title; entities by DXF handle / run id; lengths, areas, volumes and levels
only (no coordinates). Built on the merged T-242 ledger (9455a63d), T-065 / T-073 (boundary members), T-214 (structural
tops), T-230 (end rule); none re-derived except where this task reads new evidence.

## 0. Inputs (own, this run)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179...38079 | GROUND BEAMS PLAN: S-BOUN bands 7FE / 7FC / 810, S-COL.BON columns, S-BW pool outline 7C6, layer-1 beam faces, layer 2 / D opening symbols, the 6 '+-0.00' level blocks (layer 3, block LEL) and the 14 LEVEL texts |
| "ST7757.pdf" | 74da1523...337e3 | p.3 ground-beams plan (visual), p.13 "Ground Beams for exterior walls" (400 dpi), p.14 TYPICAL BOUNDARY WALL plan + section A-A |
| "p7757_arch_sheet03.pdf" | (Drive) | GF plan: '+-0.00' marks outside the plot on all four sides, '+0.15' courts, '+0.30' annex, '+1.00' main house |
| "Alsenan_Architectural_P7757_Pages_11-12.pdf" p.11 | (Drive) | SECTION B-B through the annex, the court and the main house (300 dpi crops) |

Files: `boundary_court.py` (BOUNDARY_COURT_V1, pure rules, stdlib), `t253_extract.py` (private DXF -> values-only
`ALSENAN_BOUNDARY_INPUT.json`), `t253_alsenan_check.py` (-> `LEDGER_T253.csv`, `summary.json`); tests
`tests/t253_boundary_court` (24: Villa B hand fixture + adverse + Alsenan pinned).

## 1. The boundary-wall ground beam at natural ground (work a)

**Physical element** (p.14): the UPPER of the two boundary-wall beams: "GROUND BEAM (20x40)" on plan, section A-A
top at "N.G. LEVEL", dimension 40, 2 d14 (T&B) + 3 d16 (T&B), d8/20; above it the 20 x 30 columns (4 d14) and the
brick wall; below it the brick wall "AS PER EXCAVATION DEPTH BELOW N.G. LEVEL" down to the LOWER G.B (20 wide, depth
not written) on an 80 x 30 base on 10 cm blinding. The lower G.B is the foundation-plan band (S-BOUN 1658 / 1659,
owner Q-28, PROVISIONAL): a different member at a different elevation; nothing is shared with the upper beam (brick
between them). On the ground-beams plan (p.3) the upper beam is the brick-hatched 0.20 band drawn only where no
building stands on the plot line (legend "Typical Boundary Wall").

**Run by run** (corner squares once, in the longer run; `band_runs`; area conserved 8.814 m2 = 8.344 + 0.230 + 0.240):

| Run | Where | Length (m) | Ends: member met in 3-D (DXF handle) | Openings drawn across (band continuous) | m3 at 0.20 x 0.40 |
|---|---|---|---|---|---|
| 7FE#1 | upper neighbour side, whole plot length | 31.37 | both plot corners (owns both corner squares) | - | 2.5096 |
| 7FE#2 | street side, upper part | 8.10 | building column C (204, annex corner; runs from its footing through N.G.) | gate 2.50 (layer 2, 13B) | 0.6480 |
| 7FE#3 | sea side, upper part | 2.25 | pool outer wall 7C6 (wall from below the pool floor to the rim +0.30) | door symbols 0.90 (102) / 0.447 (1AA, layer D) | 0.1800 |
| 7FC#1 | sea side, between the pool and C3 | 1.15 | column C3 (1FC) and the pool outer wall 7C6 | - | 0.0920 |
| 810#1 | lower neighbour side, between the annex and the main house | 1.20 | column 218 (east); annex exterior beam face 10B (west): the 3-D member there is the annex beam only if it is deeper than 0.25 m (annex CONFLICT, s.4), else the neighbour-side brick under it (ST p.1 note 2); the plan length is unaffected | - | 0.0960 |
| **Band** | | **44.07** | 5 of 6 end faces on a member that runs through N.G. (the others are corners); 1 HELD (3-D member only), length closed | | **3.5256** |

Checks: plan overlap of the bands with columns 0.0000, with the pool 0.0000, with ground-beam strips 0.0000 (T-242);
no column outline drawn inside any band (`columns_drawn_in_bands` 0). No footing ends or is crossed by a run: every end
is a column / pool face at the plot line (footings lie below the 0.40 m beam, T-230).

**Status**: the band concrete 44.07 m x 0.20 x 0.40 = **3.5256 m3 DRAWING-CONFIRMED** (physical solid at N.G. level).
The 20 x 30 boundary columns pass through it (4 d14 column bars through the beam): by R-CONC-OWN-1 the column line,
billed through, owns 0.20 x 0.30 x 0.40 = **0.024 m3 per column**; their count is not printed ("SEE ARCH PLAN", none
drawn on any plan, T-065 M4), so the BEAM LINE is HELD at 3.5256 - 0.024 n (n unknown). The physical total does not
move with n: only the split between the beam and column lines waits on M4.

**Versus the lines** (gap re-checked on the current head fee98d9a, lessons row 2026-10-24): released A (b96185d4,
T-242 own run): none; candidate V3.0.4 own run (T-242): none; V3.0.5 .. V3.0.10 modules (`engine/source/arch_v30*.py`
on fee98d9a) add no ground or boundary line. **Silent omission in every state: ENGINE_WRONG (omission), 3.5256 m3.**

**Versus the freelancer** ('الشناجات' row 15: B15 0.3, C15 42 typed, no formula, D15 0.6, E15 = 7.56):
his - ours = 7.56 - 3.5256 = **+4.0344 m3** (ours is 53.4 % below his) = section (0.18 - 0.08 m2) x 42.00 = **+4.2000** + length
(42.00 - 44.07) x 0.08 = **-0.1656**; residual 0. Section: 0.30 x 0.60 is printed for no boundary member (p.14 prints
20 x 40 on plan and 40 in A-A): FREELANCER_WRONG (section). Length: his 42 is a bare number; 7FE alone is 41.72
(centre) .. 42.12 (outer) and 7FC + 810 = 2.35 m: he probably omitted the two short bands (UNRESOLVED, a probable cause,
not proven).

## 2. The outer-ground datum of the exterior ground beams: D-35 settled for the main house

p.13 "Ground Beams for exterior walls" (400 dpi): top arrow "Ground Floor slab level"; the underside carries a dashed
line labelled **"Outer Normal ground level"**; depth "FOLLOW ARCH."; bars 3 d16 top, two levels of 2 d12 / 30 cm side
bars, 6 d16 bottom in two rows, d8/15; 0.30 wide on 10 cm blinding. The question T-242 left (D-35) was WHICH outer
ground: the existing +-0.00 or the court +0.15. Five independent readings answer it:

| # | Reading | Sheet | Says |
|---|---|---|---|
| 1 | 6 level blocks '+-0.00' outside the plot line, all four sides (0.59 .. 1.29 m outside it) | ST p.3 (DXF layer 3) | natural ground at the plot = +-0.00 |
| 2 | '+-0.00' marks outside the plot on the street, both neighbour sides and the sea side | arch GF plan (sheet 03) | same |
| 3 | ground line '+-0.00' at the street end beside the annex and at the far plot end, earth hatch below | section B-B (Pages_11-12 p.11) | same |
| 4 | the court '+0.15' is a hatched PAVING band drawn on the earth line, its underside level with the '+-0.00' ground line (pixel profile at 300 dpi: band top 0.15 .. 0.19 m above that line) | section B-B | the court +0.15 is a finish ON natural ground +-0.00 |
| 5 | "PLAIN CONC." 15 drawn above the G.B top at "N.G. LEVEL" | ST p.14 A-A | court paving 0.15 on N.G. |

Engineering reading: "normal ground" is the natural ground; the +0.15 courts are 0.15 m of plain-concrete paving laid
on it, a finish (UP-LEVEL-DATUM lesson: a finished level never feeds a concrete dimension). **Datum = +-0.00 for every
exterior run.** Main house: D = +0.95 (T-214 structural top) - 0.00 = **0.95 m**, deeper than every printed section
(no conflict) and consistent with the drawn bar arrangement (two side-bar levels at the printed 30 cm pitch; the
section is not scaled: its 30 width and 10 blinding give 7.9 vs 10.5 px/cm). The 0.80 alternative (to the court
paving) is retired by readings 4-5, not chosen for being larger.

**Main house exterior, 16 straight runs + the pool-court ring ARC:157+158**: plan areas from the merged T-242 ledger
(face to face, T-230 ends) x 0.95 = **15.9600 m3**, each run equal to T-242's high end (pinned in the tests).
Status proposed: **DRAWING-CONFIRMED** (was HELD 13.440 .. 15.960 on D-35); the Checker re-reads the five readings.

## 3. The annex exterior runs: CONFLICT kept, narrowed (work c)

Annex: structural top +0.25 (FFL +0.30 less 0.05, T-214 DRAWING-CONFIRMED); outer ground +-0.00 (readings 1-3: the
street side is +-0.00 directly; the court side is +-0.00 under the paving). Two printed sources disagree:

- **Reading L (levels, "FOLLOW ARCH.")**: D = 0.25 - 0.00 = **0.25 m** -> 9 runs (8 straight + the arc ARC:139+13A,
  plan 8.9119 m2 = 27.90 m x 0.30 + arc 0.5419, end pieces net 0.0000) = **2.2280 m3**. T-242's literal range 0.10 .. 0.25 is narrowed to 0.25 by the
  datum (the 0.10 end was the court paving).
- **Reading S (section)**: the printed exterior section draws three bar zones (3 d16 top, two side-bar levels at 30 cm,
  6 d16 in two bottom rows) that a 0.25 m beam cannot hold, and 0.25 is shallower than the shallowest printed ground
  beam (30 x 30, "less than 2.5 m"), while the annex interior runs framing into these beams are 0.30 .. 0.60 deep.
  The section prints no depth: **no value**.
- Status: **CONFLICT, no quantity released** (literal 2.2280 shown as one reading, never adopted; never the larger
  or the smaller end). Runs: 10B+7D1#1, 10B+7D1#2, 136+7D5#1, 137+138#1, 13D+7D2#1, 13E+7D6#2, 7D4+F8#1, 7D4+F8#2,
  ARC:139+13A.

## 4. The three court runs (work b)

| Run | Length (m) | Ends | Section | m3 range (candidates, not a quantity) |
|---|---|---|---|---|
| 1811+1812#1 | 1.30 | column C4 (1E8) -> **the boundary band 7FE face** (both face lines 1811 / 1812 end at right angles on the 7FE sea-leg inner face; the band runs continuous across the run's 0.30 width) | outside ground both sides: no printed section | 0.117 .. 0.156 (0.30 / 0.40) |
| 178+7DB#1 | 3.80 | beam junction 145+7CA -> column 230 | court +0.15 on one side, the room-less panel GS-16 on the other | 0.456 .. 1.083 (0.40 / 0.95) |
| 185+7C7#1 | 0.60 | column 230 -> beam junction 109+7CB | as 178+7DB | 0.054 .. 0.171 (0.30 / 0.40 / 0.95) |
| **Court** | | | **HELD** | **0.627 .. 1.410** |

Correction to T-242: 1811+1812#1 was "FREE_END at the end: support not established"; it ends on the boundary band face,
so its **plan length 1.30 m is closed** (it cannot run into the band, which owns the 0.20 strip). Its 3-D support
stays with its section: if its soffit is below N.G. it bears on the boundary G.B, if above, on the boundary brick wall
(not a structural support). The exterior candidate is 0.95 only (0.80 retired with the datum); the range ends do not
move. GS-16 (4.18 m2, beside the outdoor stair court, in no room, no level) decides 178+7DB / 185+7C7: if it is a GF
slab panel they are exterior runs (0.95), if open, court runs with no section (T-242 architect item).

## 5. Consultant rows narrowed to exact runs (work d; text proposals for CLARIFICATIONS_CONSULTANT, the Lead edits it)

| Row | Runs | m3 at stake | One-line question |
|---|---|---|---|
| D-33 | 17: 13E+7D6#1, 13F+7D3#1, 140+7D7#1, 142+7D8#1, 15D+7C8#1, 15E+15F#1, 175+7DE#1, 176+7E6#1, 177+7CD#1, 177+7CD#2, 17D+7E4#1, 17E+17F#1, 180D+180E#1, 184+7CF#3, 7DC+7DD#1, 7E1+7E2#1, 7E7+7E8#2 | 7.958 .. 8.518 (printed-class candidates) | Do the p.13 ground-beam sections ("without concentrated load") apply to a ground beam that receives another ground beam between its supports? If not, give the section of these runs. |
| D-34 | 13: 114+115+7DF#1, 13C+7D9#1, 141+7DA#1, 142+7D8#1, 15C+7CC#1, 16F+7FF#1, 177+7CD#2, 17B+7E5#1, 17E+17F#1, 180+181#1, 180D+180E#1, 182+183#1, 184+7CF#3 (5 shared with D-33) | 2.499 .. 3.448 | For a ground beam shorter than 2.5 m (both "less than 2.5 m" 30x30 and "less than 5 m" 30x40 hold), which section applies, and is the length class read face to face? (184+7CF#3 is exactly 5.00 m.) |
| D-35 annex | 9 (s.3) | literal 2.2280; section unknown | The annex exterior ground beams (top +0.25, natural ground +-0.00) give 0.25 m by "FOLLOW ARCH.", shallower than every printed ground-beam section and unable to hold the drawn exterior section: what is their depth? |
| D-35 main house | 17 (16 + ring) | 15.960 | **Withdraw as a depth question** (s.2: the drawings settle the datum). Optional confirmation only: "Outer Normal ground level = natural ground +-0.00 (the courts' +0.15 is paving)?" |
| M4 | 5 boundary runs | 0.024 m3 per column | Boundary-wall columns 20x30 ("SEE ARCH PLAN", none drawn on any plan): give their positions and count. |

T-217 (neck section CONFLICT at C8, 184+7CF#1 / #2, 0.6764 .. 0.6964) is a designer item already listed (not repeated).

## 6. Deltas for lane I (T-254), nothing applied

| Line / component | Now (candidate V3.0.x) | After the Checker's verdict | Status |
|---|---|---|---|
| STR.CONC.GROUND_BEAM boundary G.B at N.G. | absent (A, V3.0.4 .. V3.0.10) | ADD 5 runs 44.07 m: band 3.5256 m3; beam line HELD = 3.5256 - 0.024 n (M4) | band DRAWING-CONFIRMED; beam line HELD |
| exterior main house (16 + ring) | inside the 24 'perimeter' lines released at the interior class depth (11.9346 for all 24, not paired one to one, T-242) | 15.9600 m3 at D 0.95 | DRAWING-CONFIRMED (proposal) |
| exterior annex (8 + arc) | same 24 lines | HELD, CONFLICT (literal 2.2280 named, no value) | CONFLICT |
| court 3 runs | released at interior classes | HELD 0.627 .. 1.410; 1811+1812 length 1.30 closed | HELD |

Building ground beams after T-253 (m3): CALCULATED 2.2684 (T-242, VERIFIED as a component) + main exterior 15.9600
(proposal) = 18.2284; HELD interior 9.7673 .. 10.7365 (D-33 / D-34 / T-217) + court 0.627 .. 1.410; annex CONFLICT
(literal 2.2280, section no value). Freelancer 37.98 (211 m x 0.30 x 0.60; length +3.558 through supports and section
+1.819 .. +7.428, T-242); his boundary 7.56 vs drawn 3.5256 (s.1).

## 7. Verdict proposals (for the Checker)

| Item | Proposal |
|---|---|
| boundary G.B band 3.5256 m3 | DRAWING-CONFIRMED; re-measure 7FE (8.344 m2), 7FC (0.230), 810 (0.240) at 0.20 wide x 0.40 (p.14); runs 31.37 / 8.10 / 2.25 / 1.15 / 1.20 m; ends on C (204), pool 7C6, C3 (1FC), column 218, face 10B |
| released A / candidate | ENGINE_WRONG (silent omission of 3.5256 m3 in every state) |
| freelancer boundary 7.56 | FREELANCER_WRONG section (+4.2000 at his length); length -0.1656 UNRESOLVED (typed 42) |
| outer-ground datum +-0.00 | DRAWING-CONFIRMED (5 readings, s.2); re-read p.13 (dashed line at the soffit), p.14 A-A, B-B at the annex street end and the court paving band, the GF plan marks |
| main exterior 15.960 m3 | DRAWING-CONFIRMED proposal; candidate's 24 perimeter lines ENGINE_WRONG basis (interior depth on exterior beams, T-242) |
| annex exterior | CONFLICT kept (designer D-35 annex); literal 2.2280 is not a quantity |
| court 3 runs | HELD; 1811+1812 end corrected (boundary band face, length 1.30 closed) |

## 8. Rules, test, lessons row

Rules proposed (every villa; provenance T-253; adopted as new rule versions, never edits in place):
- **R-GB-DATUM-1**: the underside datum of an exterior ground beam ("outer normal ground") is the natural ground the
  drawings print outside the building; a finished paving drawn on the natural ground (court, yard, walkway) is a
  finish and never the datum; natural readings that disagree are a CONFLICT; only finished levels printed -> HELD.
  A literal depth (structural top - datum) shallower than every printed ground-beam section is a CONFLICT, never adopted.
- **R-BOUND-GB-1**: a boundary-wall beam band is split into straight runs with each corner square in one run (the
  longer); a run ends on the face of a member that runs through its level band (column / neck, pool or tank wall,
  beam at the same level), never on a footing below its soffit and never through one; the band's physical concrete is
  settled by band x printed section, and columns that pass through it (R-CONC-OWN-1) only move volume between lines:
  an unprinted column count holds the split, not the band.
Test: `tests/t253_boundary_court` (Villa B: U band 20.00 / 5.80 / 2.80 m -> 2.288 m3, 3 columns -> beam 2.216, rotation /
mirror / cm, datum under a +0.20 paving -> 0.00, D 1.20, shallow annex 0.20 -> CONFLICT, court run candidates;
adverse: length through a footing refused, a footing below the soffit as an end refused, 'FOLLOW ARCH.' depth with no
printed source refused, missing depth -> HELD never 0, paving-only datum HELD, disagreeing natural levels CONFLICT,
unsourced level refused, free end / masonry not supports, non-uniform / oblique band refused; Alsenan pinned).
Lessons row (proposed): 2026-10-24 | The exterior ground-beam depth was held for two days between 'existing +-0.00' and
'court +0.15' (D-35) | The two printed levels were read as alternatives before the drawings were asked what each level
physically is: the +0.15 is 0.15 m of court paving drawn on the natural ground in section B-B and in p.14 A-A | A level
is typed (natural ground, finished paving, structural top, FFL) from the sections before it is used as a datum; a finish
is never a structural datum; a two-level 'alternative' is investigated before it becomes a consultant row (any villa) |
tests/t253_boundary_court test_outer_ground_datum_and_exterior_depth + test_adverse_finished_paving_is_never_the_datum |
PROPOSED.

## 9. Not done / uncertain

- The main-house depth rests on reading the dashed "Outer Normal ground level" line as the natural ground; a consultant
  may still state otherwise (optional confirmation in s.5); the quantity is DRAWING-CONFIRMED, not VERIFIED.
- The 3-D member at the west end of 810#1 depends on the annex conflict (length unaffected).
- Bars (2 d14 + 3 d16, d8/20 per p.14), formwork and excavation of the boundary beam: other tasks; nothing released.
- GS-16 (floored or open) and GS-12 stay architect items (T-242).
