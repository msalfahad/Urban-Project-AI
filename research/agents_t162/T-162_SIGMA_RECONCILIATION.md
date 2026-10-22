# T-162 Exterior Sigma / exterior plaster: the freelancer's 1,502.84 m2, term by term against the drawn facade (development villa)

Worker 2, 2026-10-22. Lane A, gate 2. NO REPO CODE: research files only (`research/agents_t162/*`); no engine, rule or
released quantity changes. Rules: owner notes Sigma 2026-10-21 (items 1-4), Q-07 B (bands slab top to slab top),
Q-64 B, Q-65 C, Q-67 A cond., Q-68 C, UP-GEN-003 1.1.0 (PLASTER_PAINT openings = OWNER_DECISION_PENDING),
UP-QTY-STATUS-001, WORKFLOW_CONTROLS section 5. Basis: T-159 facade faces (READY f35bafb, 1,022.534 m2 measured) and
the T-150 opening census (READY 8bbf39d), both not yet verified by the Checker. Freelancer figures: his exterior
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
| Roof / parapets (77-84) | 230.084 | 70.030 / 70.030 (row 77: 2F NE + NW faces, 14.90 m vs his 17.75 m) | rows 78-84 are parapet INNER faces (his runs 48.47 / 28.40 fit the inner runs of the 50.569 / 29.342 m outer runs); heights 1.70 / 0.70 not printed (drawing 1.30 / 0.50); rows 83 + 84 (63.40 m) fit no parapet run (GF house parapet 28.770 m) |
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

## 3. Corners (owner item 2, FLAGGED): measured in m.l, shown both ways

Measured on the T-159 outlines (rebuilt from the Drive plan DXF) with `t162_corners.ring_corners`: every junction of
two sides, CONVEX (external arris) / CONCAVE (internal angle) / MOUTH_END (free wall end at the passage mouth), height
where both faces exist from the printed levels (CORNERS_T162.csv, 41 vertical corners).

| Item | m.l (DRAWING-CONFIRMED) | HELD / ASSUMED | 2 m.l = 1 m2 (his practice, comparison only) |
|---|---|---|---|
| External vertical corners (26 convex + 4 passage-mouth ends): GF 74.100, 1F 36.084, 2F 18.800 | 128.984 | HELD 26.199 .. 27.049 (pool-court corners: +0.15 or +0.30 base; 1F recess returns: +10.80 or +11.00 top) | 64.492 |
| Internal angles (11 concave; not arrises, listed for completeness) | 46.200 | HELD 10.400 .. 10.700 | - |
| Parapet top, outer edge (GF annex 29.342, GF house 28.770, 1F 50.569, 2F 29.800; plan length, the 1F wave tops are longer) | 138.481 | inner edges: parapet inner faces, not measured here | 69.241 |
| Opening reveals on the facade (head + jambs + sill; 16 openings with heights, heads / sills of the other 20) | 189.630 | door jambs at 2.20 ASSUMED 58.600; jambs HELD on 20 openings | 94.815 |
| 1F slab edge over open air (lower arris) | - | 13.079 HELD (finish, Q-68) | - |
| **Total external arrises** | **457.095** | + 58.600 ASSUMED + HELD | **228.548** |

His 1,297.35 m.l (columns A "arrises and ends" + B "corners"): walls 465.25, roof face 64.45, parapets 420.86,
boundary wall 165.09, drip edge 181.70. On the same house scope (walls + roof face + parapets 950.56 m.l) the drawing
gives 457.095 m.l measured + 58.600 assumed + the HELD items; his row-level corner figures carry no description (for
example row 65 B 100.00, row 66 B 48.00 on the NE face), so they cannot be mapped one by one: UNRESOLVED per row,
RULE_DIFFERENCE in total (he counts both edges of every parapet and the drip edge; the drawing has no inner parapet
or drip-edge line in T-159's scope).

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

So no source found on Drive gives "2 m.l = 1 m2"; the only Kuwait source that measures corners (Urban's cost PDF)
keeps them in m.l. For the owner: (A) corners stay an m.l line (as the Urban cost PDF prices them); (B) his
conversion 2 m.l = 1 m2 added to the plaster area; (C) read MPW 1990 section 09200 Part 4 first (needs the file
split under 6.2 MB, or its text). Worker recommendation: A (keeps the measured length and the rate separate). Not
asked as a new question: 5 questions are open (limit 5); the Lead may bundle it with Q-OPN-1 (plaster openings).

## 5. Hand fixture (not the development villa): `check_t162.py --check` ALL PASS

Box GF 10 x 8 m (+-0.00 -> +4.00, parapet +4.60), 1F 6 x 8 m set back 4.00 m on the east (+4.00 -> parapet +8.50),
a door 1.00 x 2.20, a window 1.50 x 1.20, a window 2.00 m with no printed height. By hand: 8 convex corners
2 x 4.00 + 2 x 4.60 + 4 x 4.50 = 35.20 m.l; parapet top 16.00 + 28.00 = 44.00; reveals 5.40 + 5.40 + 4.00 (jambs
HELD); 94.00 m.l (47.00 at 2 m.l = 1 m2). Checked rotated 30 / -121 deg, mirrored, millimetres, clockwise, re-started,
a collinear extra vertex (no corner), an L ring (5 convex + 1 concave both ways), a tangent arc fillet (no corner), a
non-tangent bay arc (two corners, turn = asin(2 / 2.5)), a passage mouth (two MOUTH_END), a missing level (HELD None,
never 0), disjoint bands (raise).

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
  the owner's decisions on plaster openings (Q-OPN-1), corners (A / B / C above), drip edge and boundary wall;
  Checker verification of T-159 / T-150, which this package builds on.

Files: `t162_corners.py` (pure corner functions), `t162_alsenan_corners.py` (corners of the development villa; needs
T-159's `t159_sides.py` / `t159_alsenan.py` from agents/task-T-159 and its stage-1 rings in the scratchpad),
`t162_terms.py` (terms and openings), `check_t162.py` (fixture), `TERMS_T162.csv`, `OPENINGS_T162.csv`,
`CORNERS_T162.csv`, `summary.json`. Reproduce: `python3 -I research/agents_t159/t159_extract.py <plan DXF> <out>
research/urban_m9_s2/SYNTHETIC_FACTS_S2.json`, then `python3 -I research/agents_t162/t162_alsenan_corners.py
research/agents_t159 <out>/t159_rings.json --csv CORNERS_T162.csv` and `python3 -I research/agents_t162/t162_terms.py
research/agents_t159/FACADE_SIDES_T159.csv --out research/agents_t162`. Lengths, heights and areas only.
