# T-162 Exterior Sigma / exterior plaster: the freelancer's 1,502.84 m2, term by term against the drawn facade (development villa)

Worker 2, 2026-10-22; **r2** 2026-10-22 (rework of the Checker's rejection of 10:20, judged by
ENGINEERING_REASONING_STANDARD.md in full: corners as one m.l line with four separate figures, never m2; parapets as
physical items; the r1 opening-arris double count corrected; rule, regression pair and lessons row in sections 3-8).
Lane A, gate 2. NO REPO CODE: research files only (`research/agents_t162/*`); no engine, rule or
released quantity changes. Rules: owner notes Sigma 2026-10-21 (items 1-4), Q-07 B (bands slab top to slab top),
Q-64 B, Q-65 C, Q-67 A cond., Q-68 C, UP-GEN-003 1.1.0 (PLASTER_PAINT openings = OWNER_DECISION_PENDING),
UP-QTY-STATUS-001, WORKFLOW_CONTROLS section 5. Basis: T-159 facade faces (READY f35bafb, 1,022.534 m2 measured) and
the T-150 opening census (READY r2 d4a22b0, **NOT merged**: every opening figure below rests on it and moves with
its verdict); T-159 is merged (349251f). Freelancer figures: his exterior
plaster sheet as recorded in `tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json` (file PLS, sheet rows 29-41 and
51-97, invoice rows 24-26). Drive read (read-only, scratchpad only): P7757_DXF_COMPRESSED.zip (plan + elevation
frames, to rebuild the T-159 outlines for the corners); reference books listed in section 4.

## 1. Result in one table (m2; "drawing" = T-159 faces, geometric = ground to top, Q-07 = from the floor level)

| His group (rows) | His m2 | Drawing faces he covers: geometric / Q-07 | What explains the difference |
|---|---|---|---|
| SW (51-55) | 275.160 | 253.790 / 238.069 | 3 rows MAPPED (SW-9 edge, the 6.77 m beside the tower, the 8.10 m under the tower; his heights start at +-0.00 or +1.00, the drawing at +0.15); annex rows as a group (below) |
| SE (58-60; frame 61 apart) | 166.612 (+24.930 frame) | 150.482 / 144.647 | row 58 one plane 14.40 x 6.75: only 4.50 m runs flush ground -> +14.40; 2.30 m of the 2F face stands on the 1F roof over the porch; row 59 5.25 x 11.85 against the 1F street face 7.50 m (+4.30 / +5.50 -> wave +11.30 .. +10.085): neither figure printed |
| NE (63-65) | 258.000 | 274.045 / 251.435 | row 64 RULE_DIFFERENCE (one plane 10.00 x 19.20 for two set-back faces, T-159 HAND_RIGHT 222.205); row 65 2 x 1.50 x 6.00 UNRESOLVED (no such face on sheet 09; possible double count with the 1F end faces) |
| NW (68-75) | 389.938 = 185.040 walls + 181.806 domes + 19.154 pool soffit + 3.938 frame | 63.425 / 63.425 | domes EXCLUDED (owner item 3); pool soffit: owner accepts 12.834 (item 4); rows 70 + 71 + 74 = 19.80 m at 5.50 / 5.70 against 12.628 m of 1F sea face (7.17 m of his run is not on that face: the pool-court walls are candidates); rows 68 / 69 UNRESOLVED |
| Roof / parapets (77-84) | 230.084 | 70.030 / 70.030 (row 77: 2F NE + NW faces, 14.90 m vs his 17.75 m) | rows 78-84 (146.659 m2) are parapet INNER FACE + TOP (r2, section 3.2: his 0.70 = 0.50 face + 0.20 top; row 79 agrees within -0.111 m2); rows 83 + 84 = GF house + 2F parapets (+7.130 m of run not drawn); row 78 (1F) 1.70 unprinted: +15.279 .. +20.382 m2 UNRESOLVED |
| Boundary wall (87-90) | 107.240 | - | HELD, owner Q-65 (not a house face) |
| Drip edge (92) | 50.876 | - | HELD, not answered by the owner |
| **Total** | **1,502.840** | **811.772** of the 1,022.534 m2 drawn faces | + **210.761 m2 of drawn faces in NO freelancer row** (below) |

- Drawn faces with no freelancer row (210.761 m2, every one listed in TERMS_T162.csv): the GF sea face NW-7
  47.400 (7.90 m, the saloon glazing W02 6.33 m sits in it), the pool glazing face NW-4 29.960 and the pool-court
  returns 7.387, the two side-passage faces P-1 / P-2 50.290 (exterior under Q-67 A, cond.), the porch faces (GF SW-5
  16.050, SW-6 7.490, SW-9 covered part 2.675, SE-2 entrance 19.795, SE-3 2.140, NE-1 7.490; 1F SW-2 over the porch
  18.480), the returns SE-5 / NW-2 1.605. His 1,502.84 is therefore NOT a superset of the drawn facade: he leaves out
  faces recessed behind the porch, the pool court and the passage, and adds domes, frames, inner parapet faces,
  the boundary wall and the drip edge.
- Annex: his rows 54 + 55 + 60 hold 4.00 + 13.00 + 1.50 = 18.50 m of annex faces at 5.25 / 4.80 m; the drawing has
  18.742 m (SE-1 6.70, SW-1 3.10, arc SW-2 2.042, jog NW-1 0.50, SW-3 6.40) at +-0.00 / +0.15 -> +4.80: his 90.60 m2
  against 88.295 m2 (+2.6 % his). The run agrees; only his split between the SW and SE groups differs (MAPPED as a
  group); his 5.25 m height (row 54) is not printed (sheet 07 prints 480).
- Like for like (his wall rows 968.237 m2 = owner's "walls without domes etc.", against 1,022.534 measured): the
  +54.296 m2 (+5.6 %) of T-159 is the net of -210.761 m2 he does not measure and the merged / longer planes he does
  (NE +30.205, SE row 58 +22.265 against the flush faces, NW 1F rows +46.465, rows 65 / 68 / 69 93.150 m2 with no
  face). The totals agreeing within 6 % hides about 300 m2 of differences in both directions.

Verdict proposals (for the Checker): totals RULE_DIFFERENCE (one plane per elevation vs set-back faces each with its
printed band, as in T-159); faces not in his rows **HAND_RIGHT** where the face is drawn and printed (porch, GF sea
face, pool glazing face), **RULE_DIFFERENCE / owner Q-67 A cond.** for the passage faces; rows 65, 68, 69, 78-84
**UNRESOLVED** (no printed face or height); domes **EXCLUDED** (owner item 3); pool soffit **ACCEPTED 12.834** (owner
item 4); boundary wall and drip edge **HELD**.

## 2. Openings (owner item 1): what his 13 rows hold

His sheet lists 13 rows under "windows, external openings" (rows 29-41: 25 openings, 61.895 m2), used to deduct from
the interior plaster AND reused for the exterior (row 96); row 97 adds 11 x 0.70 x 0.50 = 3.85 m2 (spatter dash).
Exterior deduction 65.745 at HALF = 32.8725 m2 (invoice row 25). Against the 36 facade openings of the T-150 census
(OPENINGS_T162.csv):

| His rows | Census openings | Match |
|---|---|---|
| 29 / 30 / 31 (1.20 x 2.00 / 2.30 / 1.70) | W01 / W13 / W26 | exact, printed |
| 33 (2.45 x 1.50) | W14 2.45 x 1.60 printed | height differs |
| 37 (2.00 x 2.30) | D-GF-07 main door 2.00 x 2.50 printed | height differs |
| 38 (2 x 1.55 x 2.70) | W15, W16 1.55 x 3.10 (crown) | height differs |
| 41 (0.50 x 1.50) | W18 0.50 x 2.16 printed | height differs |
| 35 / 36 / 39 (1.50 / 1.00 / 1.50 windows, 6) | W08, W09; two of W10 / W25 / W27; W24 + one not found | widths match, heights HELD in the drawing |
| 32 + 34 + 40 (11 doors 1.00 x 2.30) | 6 outside-class doors (D-GF-01/03/05/06/09, D-2F-01) | 5 doors not identified |
| 97 (11 x 0.70 x 0.50) | 10 small bathroom windows 0.60 wide (heights HELD) | count 11 vs 10 |
| NOT in his list | W02 6.33 (height HELD), W03 6.57 x 4.30 = 28.251, W17 3.29 x 3.50 = 11.515, W11 / W12 1.95, W29 1.20, one 1.00 window | - |

Answer to the owner's guess ("maybe he did small windows"): **no**. His list is 12 doors and 13 mid-size windows
(the 11 small bathroom windows sit in row 97); what it LEAVES OUT are the largest glazings (W02 saloon, W03 pool
glazing, W17 curved window: at least 39.766 m2 printed plus W02) and the two diwaniya windows. Facade openings with a
printed / inferred height: 66.576 m2; doors at the owner reference 2.20 (ASSUMED) 12.760 m2; heights HELD on 20
openings (24.98 m of width). **Net: HELD** (UP-GEN-003 1.1.0 PLASTER_PAINT = OWNER_DECISION_PENDING, Q-OPN-1, never
asked on this board). Comparisons only, not quantities: T-159 gross 1,022.534; less the printed-height openings in
full 955.958; at his half rule 989.246.

## 3. Corners and parapets as physical items (r2)

The r1 table showed corners converted to area ("2 m.l = 1 m2", 228.548) and offered the owner an option to add them to
the plaster area. Both are withdrawn: the owner-notes correction of 2026-10-22 07:10 (from his invoice cells and the
Urban cost PDF) establishes that corners are their own m.l line; "2 m = 1 m" is a half-length / half-rate PAYMENT
convention (standard section 3: physical, contract, payable, rate and amount kept apart). Nothing below converts
m.l to m2, and `t162_corners.add_area_m2` refuses an m.l item in a plaster total (check_t162.py adverse case).

### 3.1 The physical element (standard 2.1)

One exterior corner line = every external arris of the plastered envelope, each a component of its own: vertical
convex arrises of each storey outline; the two arrises of a free wall end (facade side and passage side); the outer
and the inner top arris of every parapet, each on its own run; the perimeter arris of every facade opening (head, two
jambs, sill for a window); slab edges over open air; frame mouldings; drips. Internal (concave) angles and the inner
base junction of a parapet with the roof are terminations, not arrises.

A parapet is (section A-A, sheet 10, plain 0.20 m wall continuing the facade): outer face (in the T-159 facade faces,
not counted again) + inner face (m2, from the roof slab top to the parapet top) + top surface (m2, centreline x t) +
outer and inner top arris (m.l) + stop-ends only at free ends. **New evidence read this run** (Drive "Alsenan chalet
project", ST7757.pdf page 14, read-only): the structural sheet draws three parapet types: (P1) "TYPICAL DETAIL OF
PARAPET SECTION": brick wall on a 30 cm RC upstand over the slab ("must be more than the height of roof finishing"),
an RC capping beam with a moulded outward projection whose profile and heights are "AS PER ARC."; (P2) "DETAIL OF
PARAPET SECTION": RC parapet 130 high with a 30 wide x 10 deep cap, stepped onto the edge beam; (P3) "DETAIL OF
PARAPET SECTION": tapered RC parapet 105 high, 15 at the top. The three structural slab plans carry the note "CHECK
ARCHITECTURAL DETAIL OF PARAPET, BEFORE CASTING" (ST DXF text, three places). No sheet keys P1 / P2 / P3 to a run, and
no architectural parapet detail is on Drive. So the profile is the architect's: section A-A (plain top) governs the
measured figures below; the 0.20 m top band the elevations draw on the 2F NW face and the 1F SE wave is consistent with
a P1 cap whose profile is not drawn: UNKNOWN. Quantity at stake if a 0.30 m cap (P2) sits on the 1F runs: top surface
+4.968 m2 (centreline 49.677 m x 0.10) and one more arris per metre for each side the cap overhangs (cap lower
edge, +49.677 m.l per side, up to +99.353 m.l): HELD as a designer item (list in section 7). The RC upstand (P1) changes the substrate of the lower
0.30 m of the inner face (concrete under plaster, a brick / concrete joint), not its area. The exposed plaster height
of an inner face starts at the roof finish, whose build-up is not printed: the inner-face figures below are measured
from the structural slab top and are an UPPER bound of the plastered area (UNKNOWN deduction for the build-up and the
0.20 m membrane upturn of owner Q-58).

### 3.2 Parapets, run by run (PARAPETS_T162.csv; re-computed in `t162_r2.py` from the per-side runs of T-172)

| Roof parapet (printed levels) | Outer top arris m.l | Inner top arris m.l | Top m2 | Inner face m2 | Ends |
|---|---|---|---|---|---|
| Annex +4.30 -> +4.80 | 29.342 | 28.428 | 5.777 | 14.214 | both abut higher construction: no stop-end |
| GF house +5.50 -> +6.00 | 28.770 | 27.970 | 5.674 | 13.985 | abuts the 1F NW face; NE passage-mouth end UNKNOWN: stop-end HELD 0 .. 1.20 m.l |
| 1F +9.70 -> +11.00 (NE / SW printed; NW / SE waves from the CAD top line) | 50.569 | 48.784 | 9.935 | 52.082 .. 57.185 (heights HELD on NE-1, SW-1 returns and SW-2 0.385 .. 1.60) | both abut the 2F faces |
| 2F +13.90 -> +14.40 (closed ring; NE wall 0.15) | 29.800 | 28.300 | 5.415 | 14.150 | none |
| **Total** | **138.481** | **133.482** | **26.801** | **94.431 .. 99.534** | |

Check by hand (2F ring, outer 6.80 x 8.10): inner sides 6.80 - 0.20 - 0.15 = 6.45 and 8.10 - 2 x 0.20 = 7.70, inner run
2 x (6.45 + 7.70) = 28.300; top 2 x (6.80 + 6.45) / 2 x 0.20 + (8.10 + 7.70) / 2 x (0.20 + 0.15) = 2.650 + 2.765 =
5.415 m2; inner face 28.300 x 0.50 = 14.150 m2. The annex, GF and 1F tops follow the same centreline rule ((outer +
inner) / 2 x 0.20: 5.777, 5.674, 9.935), so the T-172 totals are reproduced, not copied. Status: geometry
DRAWING-CONFIRMED (T-172 READY d7f81ef, not verified); whether the inner faces and tops are in the exterior plaster /
Sigma scope: UNKNOWN (no specification); listed, added to no line.

His parapet rows 78-84 (146.659 m2), in units, against inner face + top of the runs each row covers (his outer faces
are in his elevation rows, as the drawing's are in T-159):

| His rows (his label) | His L x H = m2 | Drawn runs: inner face + top | His - drawn | Cause, in m2 |
|---|---|---|---|---|
| 79 (annex roof parapet) | 28.40 x 0.70 = 19.880 | annex 14.214 + 5.777 = 19.991 | **-0.111** | his 0.70 = 0.50 inner face + 0.20 top (girth); length 28.40 vs 28.428 -0.014 (face) and top on his run instead of the centreline -0.097. MAPPED |
| 83 + 84 ("parapets of the annexes' roofs" + "parapet", his subtotal J84 44.38) | 63.40 x 0.70 = 44.380 | GF house 13.985 + 5.674 and 2F 14.150 + 5.415 = 39.224 | **+5.156** | +7.130 m of run that no drawing shows (63.40 vs 56.270) = +4.991; top on his run vs centreline +0.165. The 7.130 m: UNRESOLVED (no further parapet on any plan) |
| 78 (parapet, 1F) | 48.47 x 1.70 = 82.399 | 1F 52.082 .. 57.185 + 9.935 = 62.017 .. 67.120 | **+15.279 .. +20.382** | length 48.47 vs 48.784: -0.533; height: his 1.70 against a drawn girth of 1.271 .. 1.376 per metre of inner run (printed maximum 1.30 + 0.20 top = 1.50 still leaves 0.20 x 48.47 = 9.694 m2 unexplained). UNRESOLVED: 1.70 is not printed anywhere |
| **Total** | **146.659** | **121.232 .. 126.335** | **+20.324 .. +25.427** | +4.991 undrawn run, +15.812 .. +20.915 the 1F height, -0.533 the 1F run length, -0.111 annex, +0.165 centreline |

So his parapet rows are not inner faces only (r1 reading): with 0.70 = 0.50 + 0.20 they are inner face + top, which
the annex row confirms to 0.6 %. What stays unexplained is named: 7.130 m of run (4.991 m2) and the 1F height
(15.812 .. 20.915 m2). Both are larger than the physical upper bound, which itself still includes the unprinted roof
build-up.

His parapet m.l (column B 2 x L = 280.59; column A 1 x L = 140.27) against the physical top arrises 271.962 m.l
(outer 138.481 + inner 133.482): B is +8.628 (both edges taken on one run, and rows 83 / 84 carry 7.130 m of undrawn
run); A is a third line per metre with no physical arris (a plain parapet has 2 top arrises: 1.943 per metre of outer
run on the fixture, 1.964 here, never 3). Verdict proposals: B RULE_DIFFERENCE (+ the undrawn 7.130 m UNRESOLVED);
A RULE_DIFFERENCE (counting convention, not an edge).

### 3.3 Corners: one m.l line per component, four separate figures (CORNERS_R2_T162.csv)

Physical = measured full length. Contract = the physical length (Urban measures the physical edge; his own contract
basis is 1,297.35). Payable under his half convention = contract / 2 (a payment figure, comparison only). Rate basis =
Urban cost PDF 1.25 KWD per m.l of full length = half the exterior plaster rate 2.50 KWD/m2. Amount = contract x 1.25
(= payable x 2.50). Amounts are comparisons for the owner's cost view, not a priced BOQ.

| Component | Physical m.l | Payable m.l (half, comparison) | Amount KWD at 1.25 | Status | HELD / UNKNOWN beside it |
|---|---|---|---|---|---|
| GF convex arrises (13) | 66.900 | 33.450 | 83.62 | DRAWING-CONFIRMED | pool-court plinth 2.10 .. 2.55 |
| 1F convex arrises (9) | 39.000 | 19.500 | 48.75 | DRAWING-CONFIRMED | parapet end parts 0 .. 11.90; slab edges below +5.50 (Q-68) |
| 2F convex arrises (4 x 4.70) | 18.800 | 9.400 | 23.50 | DRAWING-CONFIRMED | - |
| Wall ends at the two passage mouths (8 arrises) | 43.100 | 21.550 | 53.88 | DRAWING-CONFIRMED | GF parapet stop-end 0 .. 1.20 |
| Parapet outer top arrises | 138.481 | 69.240 | 173.10 | DRAWING-CONFIRMED | wave tops longer than plan: UNKNOWN |
| Parapet inner top arrises | 133.482 | 66.741 | 166.85 | DRAWING-CONFIRMED | - |
| Opening arrises (36 facade openings) | 137.110 | 68.555 | 171.39 | DRAWING-CONFIRMED (T-150 NOT merged) | jambs HELD on 20 openings; arch / curved heads at chord, arc extra UNKNOWN |
| Door arrises at 2.20 m (6 doors) | 32.200 | 16.100 | 40.25 | ASSUMED — OWNER-APPROVED (Q-55 C) | - |
| Slab edge over open air, frames, drips, boundary wall | - | - | - | HELD | 13.079 m (Q-68); frames 98.002 .. 195.180 (profile); drip UNKNOWN (nothing drawn); boundary wall Q-65 |
| **Measured** | **576.872** | 288.436 | 721.09 | DRAWING-CONFIRMED | + 32.200 ASSUMED + HELD |

r1 -> r2 changes, each with its cause: (1) **opening arrises 189.630 -> 137.110 m.l measured and 58.600 -> 32.200
ASSUMED: r1's caller added 2 x height per opening a second time** (`opening_reveal_ml` already returns head + 2 jambs
(+ sill); the hand fixture tested the function, not the composition, so it passed). Example W01 1.20 x 2.00 with sill:
2 x 1.20 + 2 x 2.00 = 6.40 m.l, r1 10.40. Defect size -52.520 m.l measured, -26.400 m.l assumed. CORNERS_T162.csv rows
corrected; `t162_corners.opening_arrises` composes once; check_t162.py has the adverse case. (2) Vertical arrises
128.984 -> 167.800 m.l: the 4 passage-mouth wall ends have 2 arrises each, not 1 (+22.400 with the T-172 heights),
the 3 pool-court convex corners are measured from the +1.00 court level with only the plinth HELD (+13.500; r1 held
them whole), the 1F corners run to +9.70 with the unprinted parapet end parts HELD instead of taken from the CAD top
line (36.085 -> 39.000 + HELD 0 .. 11.90). Source T-172 (READY d7f81ef, my own, not verified). (3) Parapet inner top
arrises added: +133.482 m.l.

His line like for like (house scope: without the boundary wall 165.09 and the drip 181.70 = 950.56 m.l) against
609.072 m.l (576.872 measured + 32.200 assumed), +341.488 m.l: parapets 420.86 - 271.963 = +148.897 (third line
140.27 + both edges on one run and the undrawn 7.130 m 8.628); walls and roof face 529.70 - 337.110 = +192.590, of
which named: 2F corners his 12.60 (3 x 4.20) vs 18.800 (-6.200, ENGINE_RIGHT on the height, T-172), NW frame 17.55
in his cells vs frames HELD here, pool-court ceiling 18.00 vs the drawn void edge 6.810 (HELD, Q-68); the rest
(his column A facade cells 281.70 and A77 51.85 carry no description) UNRESOLVED per cell. Payable comparison: his
648.675 m.l against 288.436 + 16.100 m.l on the same convention.

## 4. Reference-book search for the corner convention (found / not found)

| Source (Drive, read-only) | Result |
|---|---|
| Kuwait Ministry of Public Works, General Specifications for Buildings and Engineering Works (1990), Vol. 1 | NOT READ for plaster: its contents list section 09200 "plaster works" and say every chapter has a Part 4 "measurement" (introduction), but the connector's text stops at about page 80 (section 02230, roads) and the file (11.8 MB) is over the 6.2 MB download limit. The measurement clause of 09200 is the place to look. |
| Kuwait Society of Engineers, "Bayt Al-Omr" guide (2023), plaster works list, item 56 | FOUND, execution only: expanded metal mesh with the corner and end beads is installed as part of the interior plaster works. No measurement convention (no m.l, no 2 m.l = 1 m2). |
| "Ain Al-Mushrif" (site supervision errors) | NOT FOUND (no plaster measurement text). |
| "Finishes" (Eng. Abdulghani Al-Jund) and Qatar QCS 2014 | NOT READ: the connector returns no text (scanned / too large). |
| Two takeoff workbooks in the owner's Drive (residential building takeoff; takeoff tables) | NOT FOUND: plaster is m2 per room, no corner item. |
| Kuwait Building Code, administrative requirements | not relevant (administration). |
| The owner's own Urban cost PDF (owner notes) | prices exterior corners as their own m.l item, 1,300 m.l x 1.25 KWD, NOT converted to m2. |

No source found on Drive converts corners to area; the only Kuwait source that measures corners (Urban's cost PDF)
keeps them as an m.l line, and the owner-notes correction (2026-10-22 07:10) settles the convention: one m.l line at
full physical length, "2 m = 1 m" = half payable length / half rate. **Not an owner question** (r1's options A / B / C
are withdrawn; standard 2.7 not met). What remains is a reference search only: the measurement clause of MPW 1990
section 09200 Part 4 (file 11.8 MB, connector text stops near page 80), to be read when a copy under 6.2 MB exists.

## 5. Hand fixture (not the development villa): `check_t162.py --check` ALL PASS

Box GF 10 x 8 m (+-0.00 -> +4.00, parapet +4.60), 1F 6 x 8 m set back 4.00 m on the east (+4.00 -> parapet +8.50),
a door 1.00 x 2.20, a window 1.50 x 1.20, a window 2.00 m with no printed height. By hand: 8 convex corners
2 x 4.00 + 2 x 4.60 + 4 x 4.50 = 35.20 m.l; parapet outer top 16.00 + 28.00 = 44.00; opening arrises 5.40 + 5.40 + 4.00
(jambs HELD) -> 94.00 m.l physical. r2 cases: four figures of that line (physical 94.00 unchanged by the convention,
payable 47.00 m.l, amount 117.50 KWD = 47.00 x 2.50, no m2 key, HELD stays None); ADVERSE: a corner m.l line added
to a plaster m2 total raises; the 1F parapet ring 6 x 8, t 0.20, 0.50 high: outer 28.00, inner 26.40 m.l, top 5.44 m2,
inner face 13.20 m2, 1.943 arrises per metre (ADVERSE: never 3); a HELD height gives a range, an unknown height None,
a missing thickness raises; opening arrises composed once over a list (measured 9.40, assumed 5.40, 1 HELD) and the
ADVERSE r1 defect (1.20 x 2.00 with sill = 6.40, never 10.40). r1 cases kept: rotated 30 / -121 deg, mirrored,
millimetres, clockwise, re-started, collinear vertex, L ring, tangent fillet, bay arc, passage mouth, missing level
(HELD None), disjoint bands (raise). The two r1 assertions of the "2 m.l = 1 m2" figure were removed on the Checker's
instruction (the conversion is withdrawn), replaced by the adverse m2 refusal.

## 6. Checker re-measure suggestion (one elevation)

NE (sheet 09 + the plan DXF): his rows 63 / 64 / 65 = 258.000 against the drawing's GF NE-6 51.840 (10.80 x 4.80),
GF NE-4 116.220 (19.37 x 6.00), 1F NE-2 105.985 (19.27 x 5.50), plus 2F NE-1 38.070 in his roof row 77; and its
corners: NE-6 / SE-1 4.800, NW-7 / NE-4 6.000, NE-4 and NE-6 at the passage mouth 5.350 / 4.650, 1F NW-5 / NE-2 5.300,
NE-2 / SE-1 5.500, 2F NE-1 corners 2 x 4.700.

## 7. What is learned / what is missing

- Matching his total within 6 % says little: about 211 m2 of drawn faces are missing from his rows and about 300 m2
  of his rows are merged planes, unprinted heights, domes, inner parapets or items outside the house.
- His opening list is the interior one reused; it leaves out the biggest glazings, so his half deduction (32.87)
  is unrelated to the facade's real openings (66.576 m2 printed + 12.760 assumed + 20 HELD).
- A corner's height must come from the parapet top AT that end (wavy parapets: +11.30 / +10.085 on the 1F street
  face), not from the mean height used for the face area.
- Missing: the MPW 1990 measurement clause (file too large for the connector); opening heights (designer D-45);
  the owner's decisions on plaster openings (Q-OPN-1), drip edge and boundary wall (corners are settled: m.l line);
  Checker verification of T-150 (not merged) and T-172 (READY), which this package builds on.
- r2 designer items (no owner question: standard 2.7 not met): which ST p.14 parapet type (P1 brick + RC cap /
  P2 RC 1.30 with 0.30 cap / P3 tapered RC 1.05) applies on each run and the cap profile (the plans say "check
  architectural detail of parapet"): top +4.968 m2 and +49.677 .. 99.353 m.l of cap edges on the 1F if P2;
  the roof build-up thickness (exposed inner-face height); the 7.130 m of parapet run in his rows 83 / 84 and his
  1F height 1.70.

Files (r2 adds `t162_r2.py`, `PARAPETS_T162.csv`, `CORNERS_R2_T162.csv`; run `python3 -I research/agents_t162/t162_r2.py --write`): `t162_corners.py` (pure corner functions), `t162_alsenan_corners.py` (corners of the development villa; needs
T-159's `t159_sides.py` / `t159_alsenan.py` from agents/task-T-159 and its stage-1 rings in the scratchpad),
`t162_terms.py` (terms and openings), `check_t162.py` (fixture), `TERMS_T162.csv`, `OPENINGS_T162.csv`,
`CORNERS_T162.csv`, `summary.json`. Reproduce: `python3 -I research/agents_t159/t159_extract.py <plan DXF> <out>
research/urban_m9_s2/SYNTHETIC_FACTS_S2.json`, then `python3 -I research/agents_t162/t162_alsenan_corners.py
research/agents_t159 <out>/t159_rings.json --csv CORNERS_T162.csv` and `python3 -I research/agents_t162/t162_terms.py
research/agents_t159/FACADE_SIDES_T159.csv --out research/agents_t162`. Lengths, heights and areas only.

## 8. General rule, regression test, lessons row (standard section 4; r2)

- Rule (any villa; research functions in `t162_corners.py`, proposed for a future rule version, no rule file
  changed): an exterior corner line is one m.l line per physical component (vertical arrises, both arrises of a
  free wall end, outer and inner parapet top arrises on their own runs, opening perimeters, slab edges, frames,
  drips), reported as physical / contract / payable / rate / amount, never m2 and never added to a plaster area. A
  parapet is two faces, a top on its centreline and two top arrises; its plastered inner face starts at the roof
  finish (an upper bound when the build-up is not printed). Where a structural typical detail and the architectural
  section differ on the parapet profile and the sheet defers to the architect ("check architectural detail"), the
  architectural section governs and the profile difference is HELD as a designer item. A per-item function is
  composed ONCE by a list function that the test calls; a caller never re-adds a term the function returns.
  Provenance: owner notes Sigma correction 2026-10-22 07:10; standard sections 2-4; Checker verdict 2026-10-22 10:20.
- Regression: check_t162.py --check (normal: box corners, four figures, parapet ring, opening list; adverse: m.l into
  m2 raises, 3 lines per metre is not physical, 1.20 x 2.00 window 6.40 not 10.40, missing thickness raises, HELD
  stays None).
- Lessons-register row proposed (section 7): 2026-10-22 | Opening arrises 189.630 / 58.600 m.l (T-162 r1) vs
  137.110 / 32.200 | the Alsenan caller added 2 x height again to a function result that already held the jambs; the
  fixture tested the function, not the composition | compose per-item functions once in a tested list function;
  the fixture must exercise the same path the project run uses (any villa, any trade) | check_t162.py "openings
  measured / adverse 6.40" | rule recorded; test added. Second row: 2026-10-22 | his parapet rows read as inner faces
  (r1) | a row's height (0.70) checked against one face only | decompose the parapet first; 0.70 = 0.50 face + 0.20
  top reproduces his annex row to -0.111 m2 (any villa) | check_t162.py parapet cases | rule recorded.
