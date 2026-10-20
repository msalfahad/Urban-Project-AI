# T-123 Ground-floor facade run: geometric perimeter, billable run and reveal returns; the slab over the side passage

Worker 1, 2026-10-20. Gate 1 (geometry integrity, no silent omission). NO REPO CODE: research files only, no engine,
rule or released quantity changes. Rules: owner Q-64 B CONDITIONAL (16:23), Q-67 A CONDITIONAL (18:45), Q-07 (facade
height, not used here: runs in metres only), UP-WALL-GEOM-001, UP-SPACE-002, UP-QTY-STATUS-001, UP-REVEAL-001 (1.4.0).
Data (Drive "Alsenan chalet project", read in the scratchpad, never copied here): P7757_DXF_COMPRESSED.zip (plan DXF,
sha256 ab54dd55...31cc4), "ST7757 dxf.dxf" (sha256 9f9d1179...), p7757_arch_sheet03.pdf (GF plan scan, 400 dpi),
p7757_arch_sheet04.pdf (not needed: the 1F plan was read in the DXF). Engine: ARCH_TAKEOFF_V2.12 run on the plan DXF
(Mode A, research/urban_m9_s2/SYNTHETIC_FACTS_S2.json), the released method. Reproduce: `t123_check.py` (docstring);
its output is the source of every number below. Coordinates are LOCAL (metres) to two drawn anchors, never absolute.

## 1. What the engine gives against the freelancer, and the three numbers the owner asked for

| GF facade run (m) | Q-67 A (passage outside; condition checked in 3, MET) | Q-67 B (passage inside) |
|---|---|---|
| Geometric perimeter (walks every drawn face, notch included) | **105.886694** | 98.886694 |
| Billable run, Q-64 B (notch closed straight at the column face) | **105.786694** - only once a reveal line measures the returns | 98.786694 (same condition) |
| Reveal returns (two 0.050 m faces of the notch) | **0.100**, measured by NO line in V2.12 | 0.100, same |
| Billable run TODAY (returns kept, never dropped, never counted twice) | **105.886694** | 98.886694 |

- Engine (released V2.12): 98.886694 m, PROVISIONAL / MACHINE_ONLY (line L-05b442c4e19068c7513a). Against the Q-67 A
  geometric run: **-7.000 m (-6.6 %)**, engine wrong on the passage (HAND_RIGHT, as T-016b / T-109 found; now settled by
  the owner's Q-67 A and the drawing check below). Unchanged since the last report (no method wired).
- Freelancer: no facade-run row (his exterior plaster is m2 per elevation, 1502.84 gross / 1469.97 net), so no m-for-m
  comparison; the run feeds facade m2 once heights are wired (Q-07, T-031). Not measured here: facade m2.

## 2. The notch at the north end of the curved pool glazing (verifier: re-measure the 0.08 recess here)

Anchor N = the corner of GF column handle 2F87 (layer S-COL.BON, 0.500 x 0.250 m) nearest the glazing. The V2.12 outline
walks, from N: up the column side 0.0500, along the wall face (layer-1 line 274) 0.0800, down the frame end (layer-W
polyline 280) 0.0500, then on along the frame 0.1435 m to the start of the arc:

| Piece (local m from N) | Length | What it is |
|---|---|---|
| (0, 0) -> (0, +0.050) | 0.050 | column 2F87 side: the 0.05 m by which the column stands proud of the wall face 274 |
| (0, +0.050) -> (-0.080, +0.050) | 0.080 | wall face 274 inside the pocket (equal to the closing chord, so it does not change the run) |
| (-0.080, +0.050) -> (-0.080, 0) | 0.050 | the end of the outer frame line 280: the second return |
| walked 0.180 / straight across 0.080 | **0.100** | the two returns = the Q-64 difference |

The 0.08 m recess is the distance between the outer frame line 280 (local x -0.080) and the glazed band's outer face
line 96 (layer 5, local x 0, 0.264 m long; its twin at the south end is line 95, 0.214 m): the frame (polylines 27D, 27E,
27F, 280, layer W) fills the inner 0.12 m of the 0.20 m band and the outer 0.08 m is open. The scan of sheet 03 shows the
same: a filled column about 0.25 x 0.50 m standing a few cm proud of the 0.20 m wall where the curved frame ends in a small
pocket; no dimension prints 5 or 8 cm, so 0.050 / 0.080 are CAD geometry (DXF in mm, exact to 0.1 mm).

**Is a reveal line measuring those faces? No.** V2.12 has 11 GF ARCH.WINDOW_REVEAL lines (OP-004, -006, -014, -015,
-016, -019, -022, -023, -024, -028, -029; line ids in T-123_LEDGER.csv), all BLOCKED_RFI (sill heights), all for
straight windows 6.70 to 31.43 m from the notch. The curved pool glazing itself has no opening record in the released
method: not in ARCH.WINDOW (GF 11 lines, none is it), not in CURVED_OPENINGS (only 1F COP-001), no reveal line; the
outline walks its frame as 6.994659 m of role WINDOW. (Known: T-077's piece counts it but is not wired.) UP-REVEAL-001
measures reveals on the ROOM side of the glazing; the notch is on the outside, so even a wired pool-glazing reveal line
would not hold these faces unless it measures the external strip. So under Q-64 B's condition the 0.100 m is NOT
deducted: the billable run stays 105.886694 m (Q-67 A) and becomes 105.786694 m the day a reveal or external-strip line
measures the two 0.050 m returns (owner: never double-counted, never dropped).

Consistency note (not a new question): at the south end of the same glazing the outline steps 0.080 m from the frame
line to the wall face (local wall end face, single step, no proud column). It stays in both the geometric and the
billable run, as does the 0.080 wall face inside the north pocket: they are where the facade plane changes, not returns
counted twice.

## 3. Q-67 condition: is the side passage open to outside air without doors or glazing? MET on the drawings

Anchor P = the passage corner where the annex face meets the boundary wall's inner face. Passage 1.200 x 4.700 m =
5.640 m2 (printed "120" across it on sheet 03; length from the drawn faces).
- Mouth (local y 4.700, between GF columns 2FB0 annex side and 2FAD house side): **0 entities on any layer cross it**
  (dimensions aside): no door, window, gate, glazing or wall line. The scan shows the same open end.
- Far end: the 0.200 m boundary wall (layer-5 lines 105 / 106, with 86 doubling 105) across the full width, no opening.
- Inside: one level mark +0.15 (the court level; annex +0.30, house +1.00), three dimensions, nothing else.
- Beyond the mouth (4.0 m): 0 doors, 0 windows; the +0.15 entrance forecourt with the entrance steps, open onto the
  court (+0.15, no slab over it: T-121 census). Elevations were not read.
- Faces bounding it: annex east face 3.60 + W.C. door 1.00 (block D120) + 0.10 = 4.700 m; house west face 1.05 + window
  1.50 (line 3BE) + 1.05 + window 1.00 (3CB) + 0.10 = 4.700 m.
So the passage is a roofed outdoor passage with one open end and no enclosing door or glazing: owner Q-67 A applies and
the geometric run is 98.886694 - 1.200 (mouth, OP-007) - 1.200 (boundary wall face, OP-001 walked as building) + 4.700 +
4.700 = **105.886694 m**. This is the wall-boundary correction the owner asked for (each face read, no 7.00 m constant).
Under Q-67 A the passage walls get exterior plaster and paint, measured separately (heights not measured here: Q-07,
Q-54 annex level, plinth; T-031).

## 4. The slab over the passage, read a second way (raw slab-sheet entities, not route G faces as T-121)

Registration: the GF ROOF SLAB sheet of ST7757 onto the GF plan by translation only: **30 of 30** GF column outlines
coincide with slab-sheet columns (next best offset: 1 vote). Then every slab-sheet line drawn across the full passage
width, measured from the boundary wall's inner face (slab edge line 2AD, layer 1, on that face):

| Band (mm from boundary inner face) | Width x 1.200 m | What the slab sheet draws | Above it on the 1F plan (DXF) |
|---|---|---|---|
| 0 .. 1300 | 1.560 m2 | slab panel, bars drawn (S-REIN-SLAB 4ED, 4EE, 4EF), "5 T10/m" (4F0, 4F1) | 1F roof hatch D1F (layer 3, outer loop): 1.5600 m2 = exposed GF roof |
| 1300 .. 1500 | 0.240 m2 | beam B5 (lines 27C / 281, label 498) | 1F wall (lines at 1300 / 1500) |
| 1500 .. 4500 | 3.600 m2 | slab panel, bars 514-516, "5 T10/m" 518, "6 T10/m" 517, the "T 16" tag; hatch 280 (S-HAT.BAT) over 2.7547 m2 of it | 1F bathroom (floor hatch 1256 over 2.9400 m2, walls at 1500 and 3950 / 4100), then the 1F bedroom corner |
| 4500 .. 4700 | 0.240 m2 | beam B1 at the mouth (lines 2AE / 2AF, label 476) | 1F bedroom corner |
| **Total** | **5.640 m2** | roofed over the whole length | under 1F rooms / walls **4.080**, under the exposed GF roof **1.560** |

Who is right: T-121 (route G faces) 4.084 + 1.556 = 5.640 m2, roofed full length: **CONFIRMED** (split differs by
0.004 m2: here the panel edge and the 1F roof hatch both stop at 1300 mm, so 1.560 / 4.080). T-109's "1.56 m2 open to
the sky": **CONTRADICTED** (the GF roof slab covers it). Under Q-67 A the passage soffit is 5.640 m2 on plan (exterior
soffit, Q-68: finish HELD); beam sides of B5 (both faces across 1.20 m) and B1 (inner face) are additional soffit
surface, NOT MEASURED (beam depths are the beam register's work, T-110). The hatch on layer S-HAT.BAT over the north
panel is the same hatch that lies under the other 1F wet rooms on this sheet (one under a 1F W.C., this one under two 1F
bathrooms); no legend text was found, so its meaning is NOT ESTABLISHED (relevant to designer D-24: a wet floor over
outside air).

## 5. Found on the way (for the verifier and the Lead; nothing changed)

- The engine's two GF spaces in the passage (GF-RF002DC 3.600 m2, local 1500 .. 4500, and GF-R7B7A5D 1.560 m2, local
  0 .. 1300; T-099's "unlabelled rooms") leave out two 1.20 x 0.20 m strips (0.480 m2) at exactly the B5 and B1 beam /
  1F wall positions, although the GF plan DXF draws no line there (every entity inside the strip listed by the script).
  Under Q-67 A the passage floor (exterior paving) is 5.640 m2, the engine's spaces 5.160 m2. Cause not traced.
- The windows on the passage (OP-023 1.00 m, OP-024 1.50 m) have internal reveal lines (L-87b9ef735cbe2f99877e,
  L-a3d22686697ece9b59a6, HELD); under Q-67 A their outer faces are exterior (facade openings +3.50 m with the W.C. door).

## What is learned / what is missing

- A billable-run rule that moves faces to "the reveal" needs a reveal line that exists: here the glazing the notch
  belongs to has no opening record in the released method, so the faces must stay in the facade run for now.
- The slab sheet, registered on columns, answers "roofed or open" directly from its own panel edges and beams; the 1F
  plan's roof hatch is an independent second witness of the exposed part. An architectural outline above is not.
- Missing: wiring the passage reading (T-109 piece) and a reveal / external-strip line for the curved pool glazing into a
  method version; facade m2 and passage wall plaster / paint heights (T-031, Q-07, Q-54); beam side soffits (T-110);
  the 0.480 m2 of passage floor outside the engine's spaces.
