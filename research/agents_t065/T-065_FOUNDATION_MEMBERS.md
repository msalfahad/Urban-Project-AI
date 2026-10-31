# T-065: Alsenan foundations split by member (owner answer Q-12 = B)

Worker 2, 2026-10-19, read-only hand reading (Lead 13:30: NO REPO CODE). No engine, rule, knowledge, test or data
file changed; no repository code was run. Development reference only, not an accuracy claim. Drawings are named by
Drive folder and title; entities by DXF handle; sizes and lengths only, no coordinates, no client data.

## Inputs (read in the session scratchpad, never committed)

| Input | Drive "Alsenan chalet project" | sha256 |
|---|---|---|
| structural DXF (9 frames: plans of PDF pages 1-7, schedules pages 9-10) | "ST7757 dxf.dxf" | 9f9d1179...38079 (= SOURCE_MANIFEST) |
| structural PDF, 16 pages (pages 13-16 typical details exist ONLY in the PDF) | "ST7757.pdf" | 74da1523...337e3 |
| architectural DXF (GF plan, cross-check of the boundary wall above ground) | "P7757_DXF_COMPRESSED.zip" | ab54dd55...31cc4 |
| freelancer rows | tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (footings sheet rows 13-33, ground-beams sheet rows 11-16, blockwork row 150) | in repo |

Tools: `research/agents_t065/foundation_member_census.py` (new, stdlib only, reads the DXF group codes itself, imports
no engine code) and its hand-truth self-test `selftest_census.py` (synthetic plot 10.00 x 6.00 m, plain and
shifted + mirrored: both pass). Command:
`python3 -I research/agents_t065/foundation_member_census.py "<ST7757 dxf.dxf>" --outer 1658 --inner 1659`.
PDF pages were rendered (pdftoppm) and read by eye; DIMENSION values are the dimension's own measurement / text.

## 1. What the drawings print about the plot-edge members

| # | Source | What it prints |
|---|---|---|
| E1 | PDF p.2 / DXF FOUNDATION PLAN, S-BOUN closed polylines 1658 (outer) and 1659 (inner) | a closed band 0.20 m wide on all four plot sides, cross-hatched like the lift-pit concrete walls (FF); no tag, no section mark |
| E2 | same sheet, DIMENSIONs 12D3, 139B, 1421, 142F, 138D ("10") and the chains 290 ... 150 (= 3117) and 150 ... 480 | the outer grid lines sit 0.10 m inside the plot line on the street, sea and lower neighbour sides, i.e. on the band centre line; plot 31.37 x 15.00 (block texts) |
| E3 | PDF p.10 / DXF schedules frame, simple-beam schedule row "B.W" (INSERT 1FA5) | B.W: B 20, D 60, bottom 4 d16, top 2 d14, stirrups 7 d8 /m |
| E4 | PDF p.14 "TYPICAL BOUNDARY WALL (PLAN)" (N.I.S, not in the DXF) | GROUND BEAM (20x40) between (20x30) R.C. COLUMNS 4 d14, spacing "SEE ARCH PLAN"; at each column a pad "(130x80x30)" on the inner side; section mark A-A cut THROUGH a pad |
| E5 | PDF p.14 "TYPICAL BOUNDARY WALL SECTION (A-A)" (N.I.S) | top (G.B) at N.G. level, dimension 40, 2 d14 + 3 d16, d8/20; brick wall "AS PER EXCAVATION DEPTH BELOW N.G. LEVEL"; lower (G.B) 20 wide, depth NOT dimensioned, same bars; base 80 x 30 ("80" includes the G.B width; bars 7 d12 and "4 d12 (B.W)"); blinding 10 cm, 10 cm past the toe |
| E6 | PDF p.1 general note 2 (Arabic) | the exterior ground beams on the NEIGHBOUR side are cast on black brick built up from foundation level |
| E7 | PDF p.13 "Ground Beams for exterior walls" | 30 wide x "FOLLOW ARCH." depth, 3 d16 top, 6 d16 bottom, 2 d12/30 cm sides, on 10 cm blinding |
| E8 | PDF p.3 / DXF GROUND BEAMS PLAN, S-BOUN 7FE, 7FC, 810 | the boundary band (brick-hatched, 0.20 m) only where no building stands on the plot line; where the building stands on it, the building's 0.30 m exterior ground beam (LINEs F8/7D4, FC/7D0, 136/7D5, FD/7E0) |
| E9 | architectural GF plan (P7757, layer 5) | boundary wall above ground on the same runs as E8: whole upper neighbour side, street side upper 8.30 m with a 2.50 m gate (layer-2 line 110 at the gate, also drawn on the foundation plan as 1081), sea side upper part with a door / gate (line 8F) and the pool wall, a 1.20 m piece between the two building parts on the lower neighbour side; no boundary-wall columns drawn (only the building's columns on the plot line) |

Conflict register (recorded, not settled; MISSION.md "understand the drawings first": a project drawing never settles a
conflict between two drawings):
- **C1 depth of the foundation-level beam**: schedule B.W 20 x 60 (E3) vs typical detail lower (G.B) 20 wide with no
  printed depth, plan label "GROUND BEAM (20x40)" (E4, E5). The plan band width 0.20 (E1) agrees with both.
- **C2 bars**: B.W row bottom 4 d16 / top 2 d14 / 7 d8 per m vs detail G.B 3 d16 + 2 d14 / d8 at 20 cm (5 per m).
- **C3 pads**: the typical plan prints a 1.30 x 0.80 x 0.30 pad at every boundary column; the foundation plan draws
  no such pad along the band, and neither the structural nor the architectural plans draw boundary-wall columns, so
  the pad count is NOT PRINTED.
- **C4 "B.W"**: the schedule uses B.W as a beam mark; the detail writes "(B.W)" against the pad's 4 d12 bars, which can
  also be read as "both ways". Which member the mark names is not printed unambiguously.
- **C5 F10**: footing outline 1B1B is one 3.25 x 1.40 m outline holding the tags F10, C10 and F (strap SB1 passes
  through it); schedule F10 = 2.80 x 1.40 x 0.50 and F = 0.90 x 0.80 x 0.30. Drawn outline and schedule disagree.

## 2. Every member on the foundation plan, classified

Isolated footings: 26 outlines found by the census (12 inserts of the unit-square block "F" on layer S-DIM scaled to
size, 9 closed and 3 OPEN polylines on S-FOOTINGS (open where a strap enters), 3 four-LINE squares); tags read from
the sheet texts and the C/F and C11/F11 tag blocks. Every drawn size equals its schedule row (L x W either way) except C5.

| Type | Count drawn and tagged | Schedule L x W x H (m) | m3 each | Hand m3 | Engine (FOOTING_COMPARISON) | Freelancer |
|---|---|---|---|---|---|---|
| F (C/F) | 4 (+1 inside 1B1B, C5) | 0.90 x 0.80 x 0.30 | 0.216 | 0.864 (+ held) | 0.864, 1 conflict | 0.864 (4) |
| F2 | 2 | 1.90 x 1.70 x 0.35 | 1.1305 | 2.261 | 2.261 | 2.261 |
| F3 | **2** (tags at two separate outlines, 1.6 x 1.4 and 1.4 x 1.6) | 1.60 x 1.40 x 0.30 | 0.672 | **1.344** | 1.344 | **0.672 (1)** |
| F4 | 2 | 2.20 x 2.00 x 0.40 | 1.76 | 3.520 | 3.520 | 3.520 |
| F5 | 2 | 2.40 x 2.10 x 0.40 | 2.016 | 4.032 | 4.032 | 4.032 |
| F6 | 1 | 2.60 x 2.20 x 0.50 | 2.86 | 2.860 | 2.860 | 2.860 |
| F7 | 0 (scheduled, not drawn) | 3.00 x 2.50 x 0.50 | 3.75 | 0 (not on plan) | 0 | 0 |
| F8 | 1 | 4.00 x 3.60 x 0.50 | 7.20 | 7.200 | 7.200 | 7.200 |
| F9 | 1 | 3.40 x 2.70 x 0.55 | 5.049 | 5.049 | 5.049 | 5.049 |
| F10 | 1 (C5) | 2.80 x 1.40 x 0.50 | 1.96 | **HELD** (drawn 3.25 x 1.40 outline) | blocked | 1.960 |
| F11 | 1 (open outline) | 3.50 x 1.50 x 0.50 | 2.625 | 2.625 | 2.625 | 2.625 |
| F12 | 1 | 4.40 x 3.20 x 0.70 | 9.856 | 9.856 | 9.856 | 9.856 |
| F13 | 1 | 4.30 x 2.40 x 0.50 | 5.16 | 5.160 | 5.160 | 5.160 |
| F14 | 1 | 3.80 x 3.30 x 0.50 | 6.27 | 6.270 | 6.270 | 6.270 |
| F15 | 1 | 1.80 x 1.00 x 0.40 | 0.72 | 0.720 | 0.720 | 0.720 |
| FF (lift raft) | 1 | 4.60 x 4.50 x 0.55 | 11.385 | 11.385 | 11.385 | 11.385 |
| FN (neck footings) | 4 | 1.00 x 1.00 x 0.30 | 0.30 | 1.200 | 1.200 | 1.200 |
| **isolated total** | | | | **64.346 + F10 / F held** | **64.346** (register; current run 64.304 + F10 1.960 provisional) | **65.634** |

Note: FN outline 180C is notched where it overlaps F9 (0.40 x 0.35 m = 0.14 m2 shared plan area); counting both at
full size counts that piece twice (0.14 x 0.30 = 0.042 m3, FN being the thinner): the B1 register run and the
freelancer count it twice; the current engine run (64.304) counts it once.

Strap beams (DXF S-FOOTINGS LINE pairs, tags S.B1 / sb2 blocks / S.B3; schedule p.10): clear length between the
footing faces along the strap axis, measured by hand: SB1 0.70 x 0.50 x 4.55 = 1.593; SB2 1.00 x 0.50 x 2.294 = 1.147;
SB3 0.50 x 0.40 x 3.259 = 0.652; **total 3.391 m3** (B1 register engine 3.392 and freelancer 3.3925 agree; the current
run reproduced by T-037 has 2.649 + 1.132 PROVISIONAL = 3.781, not traced here).

Plot-edge members (the subject of Q-12 (c)):

| Member | Drawing evidence | Length (centre line) | Section | Hand m3 | Engine | Freelancer |
|---|---|---|---|---|---|---|
| M1 foundation-level boundary band (all four sides) | E1, E2, E6; section C1 open | **91.94 m** closed = 2 x 31.17 + 2 x 14.80 (band area 18.388 m2 / 0.20; = printed plot 31.37 x 15.00 less the printed 0.10 m offsets); of it **70.49 m free** and **21.45 m inside 9 footing outlines** (10 footings: 3 C/F, F15, F11, F14, F10 + F in one outline, F8, FN) | B.W 0.20 x 0.60 (E3) **or** 0.20 x 0.40 (E4); held by C1 | 0.20 x 0.60: 11.033 gross / **8.459 net of footings**; 0.20 x 0.40: 7.355 / 5.639 | 60.17 m x 0.20 x 0.60 = 7.220 (frozen line); T-058 guard: 78.54 m measured + 13.40 m held | 71.7 m x 0.20 x 0.60 = 8.604 ("perimeter tie beam", footings sheet) |
| M2 boundary-wall pads 1.30 x 0.80 x 0.30 | E4, E5 typical only; C3 | count NOT PRINTED | 0.312 m3 each | **HELD** (no count) | none | none |
| M3 boundary-wall ground beam at N.G. level | E4 (20x40), E5 (dimension 40), E8 band 7FE + 7FC + 810, E9 | 41.72 + 1.15 + 1.20 = **44.07 m** (7FE: area 8.344 m2 / 0.20; outer run 31.37 + 8.30 + 2.45 = 42.12 m) | 0.20 x 0.40 printed twice | **3.526** (7FE alone 3.338) | **not measured this run** (whether route G emits the S-BOUN band of the ground-beam plan was not checked: no repo code could run) | 42 m x 0.30 x 0.60 = **7.560** ("boundary ground beam", ground-beams sheet) |
| M4 boundary-wall columns 0.20 x 0.30 | E4 "SEE ARCH PLAN" | count NOT PRINTED (no boundary column on either plan) | 0.20 x 0.30 x height (not printed) | **HELD** | none | not identified |
| M5 building exterior ground beams on the plot line | E7, E8 (0.30 wide, depth "FOLLOW ARCH"), E6 | part of the ground-beam line (T-041), not of the footing line | | not in this task | ground-beam line | ground-beams sheet |

## 3. The 31.77 m (91.94 m drawn vs 60.17 m kept), edge by edge

| Band side | Drawn centre line | Kept by the frozen line | Above it (E6, E8, E9) | Inside footings | Free |
|---|---|---|---|---|---|
| side 1, lower neighbour (outer 1658 seg 2 / inner 1659 seg 2) | 31.17 | **0** (dropped: frozen 5-point EXPLAINED_BY_MEMBER, T-050) | building on the plot line: its 0.30 exterior G.B on black brick from foundation level (note E6); 1.20 m boundary wall between the two parts | 13.95 (C/F x2, F15, F11, F14, F10 + F outline) | 17.22 |
| side 2, sea | 14.80 | 14.60 (inner paired overlap) | lower 7.90 m building; upper part pool wall + boundary wall + gate | 5.90 (F10 + F outline, FN, F8) | 8.90 |
| side 3, upper neighbour | 31.17 | 30.97 | boundary wall, full length | 0 | 31.17 |
| side 4, street | 14.80 | 14.60 | lower 6.70 m building; upper 8.30 m boundary wall incl. 2.50 m gate | 1.60 (C/F x2) | 13.20 |
| **total** | **91.94** | **60.17** | | **21.45** | **70.49** |

91.94 - 60.17 = 31.77 = side 1 (31.17) + corner basis 0.60 (three kept sides measured on the inner overlap, 3 x 0.20).
Corners are counted once (closed centre-line rectangle); the gate does not interrupt the foundation band on any sheet.
**Side 1 is a real member**: it is the foundation the general note E6 asks for under the neighbour-side brick.

**New defect in the merged strip guard (T-058):** its 13.40 m "held under members" is exactly the ring length inside
CLOSED footing polylines and column outlines (re-computed here: 8.40 + 4.30 + 0 + 0.70 = 13.40 m). It misses 8.05 m
inside footings drawn as inserts of the footing block on another layer (3 C/F pads) and as OPEN outlines (F11, the
F10 + F outline, opened for a strap). So its MEASURED 78.54 m (9.425 m3) includes 8.05 m (0.966 m3) that lies inside
footings. Drawing: 70.49 m free, 21.45 m inside footings. The census self-test also showed that a MIRRORED block
insert (negative X scale) inverts the footing box unless it is normalised; the guard should be tested for that too.

## 4. Verdict proposals (for the verifier)

| Line / term | Engine | Freelancer | Hand from the drawing | Proposal |
|---|---|---|---|---|
| Isolated footings, F3 count | 2 (1.344) | 1 (0.672) | 2 tagged outlines (1.344) | **ENGINE_RIGHT** (+0.672 m3 vs freelancer) |
| Isolated footings, F10 (+ corner F) | held | 1.960 (+ F at 0.216 inside his 4) | drawn outline 3.25 x 1.40 vs schedule 2.80 x 1.40 (C5) | **UNRESOLVED** (RFI below); engine holding it is right |
| Isolated footings, other types | 63.002 (register) / 62.960 (current, FN-F9 overlap counted once) | 63.002 | 63.002 at full size, 62.960 with the overlap once | agree; overlap 0.042 m3: ENGINE_RIGHT |
| Strap beams | 3.392 (register) / 3.781 (current) | 3.3925 | 3.391 | register and freelancer agree; current +0.390 m3 not traced (superseded by T-073, T-389 note: agreement is not proof; the strap is re-derived by hand from the drawn F10 + F outline, research/agents_t073/T-073_RESULT.md:85) |
| M1 band length | 60.17 m (frozen) | 71.7 m | 91.94 m drawn, 70.49 m free of footings | frozen engine **wrong** (side 1 lost); freelancer **UNRESOLVED**: his 71.7 m lies between the free length on the inner face (91.14 - 21.05 = 70.09) and on the outer face (92.74 - 20.15 = 72.59), consistent with "band less footings" but not reproducible |
| M1 band section | 0.20 x 0.60 | 0.20 x 0.60 | C1 conflict | **UNRESOLVED** (owner Q-28) |
| M1 band where it runs through a footing | (guard: held) | apparently deducted | no Urban rule on concrete overlap | **UNRESOLVED** (owner Q-28) |
| M3 boundary ground beam at N.G. level | not measured | 7.560 (0.30 x 0.60 x 42) | 3.526 (0.20 x 0.40 x 44.07) | **UNRESOLVED** until the engine line is read (silent omission if route G emits none); against the drawing the freelancer's 0.30 x 0.60 is not printed for this member (drawing 3.526 vs 7.560: -4.03 m3, -53.4 %) |
| M2 pads, M4 columns | none | none | count not printed | HELD for both; RFI |

Footing line (CONC.FOOTING), engine as reproduced by T-037 on the current method (ARCH_TAKEOFF_V2.9 + route G, the
run behind the scoreboard's 77.27 m3): isolated 64.304 SOURCE_DERIVED + F10 1.960 PROVISIONAL + straps 2.649 + 1.132
PROVISIONAL + band 7.220 = **77.265 m3** vs freelancer 65.634 + 3.3925 + 8.604 = **77.631 m3** (-0.366 m3, -0.5 %).
Against the hand reading:
- isolated: engine 64.304 = hand 64.346 less 0.042, which is exactly the FN / F9 overlap (0.14 m2 x 0.30) counted once:
  ENGINE_RIGHT on that piece; the F10 1.960 PROVISIONAL rests on the schedule while the drawn outline differs (C5):
  UNRESOLVED;
- straps: engine 3.781 vs hand 3.391 (+0.390 m3, +11.5 %): the engine's strap split was not traced this run (the
  B1 register's older run gives 3.392); a check for the verifier;
- band: engine 7.220 (60.17 m, side 1 lost) vs drawn 11.033 gross / 8.459 net of footings at 0.20 x 0.60 (or
  7.355 / 5.639 at 0.20 x 0.40): the near-match of the two footing totals is a coincidence of offsets (F3 +0.672,
  F10 both 1.96, band -1.384, straps +0.389), as T-037 already suspected.
With the band corrected to the drawing and F10 held, the footing line would be 64.304 + 3.781 + 8.459 = 76.544 m3
(net, 0.60) or 79.118 m3 (gross, 0.60): which one is the owner's call (Q-28), not a fit to the freelancer.

## 5. RFI wording for the designer (proposed)

1. Boundary wall at foundation level: does schedule row B.W (20 x 60) apply to the closed 0.20 m band on the
   foundation plan, or the typical boundary-wall section (lower G.B 20 wide on 130 x 80 x 30 pads)? Please give the
   depth of the lower ground beam and the boundary-column positions.
2. Footing under C10: the plan draws one 3.25 x 1.40 m outline with the tags F10 and F; the schedule gives F10 2.80 x
   1.40 x 0.50 and F 0.90 x 0.80 x 0.30. Which governs?

## 6. Proposed engine task (general, not Alsenan constants)

Plot-edge member ledger (new method piece, not wired; the frozen footing and strip code untouched):
(a) report isolated footings, strap beams, the foundation-level boundary band, boundary-wall pads and the boundary
ground beam at N.G. level as **separate lines** (owner Q-12 answer); (b) the band's footing members must include block
inserts whose geometry sits on the footing layer (any insert layer, scale signs normalised) and open footing outlines,
so the 21.45 m inside footings is reported as such (fixes the T-058 8.05 m); (c) section from the schedule row only
when the band is bound to it by printed evidence, else HELD with the candidate sections (C1); (d) the boundary band of
the ground-beam plan (S-BOUN-type band, 0.20 m) measured as its own line with the printed typical section, or HELD;
(e) pads and columns HELD until a count is printed. Fixture (hand-calculated, not Alsenan): the self-test plot here
(31.20 m centre line, 4.60 m inside footings, 26.60 m free) extended with a strap entering an open outline, a
rotated plot (30 degrees), a metre-unit copy and a band with no schedule row (HELD, never 0).

## 7. Not done / uncertain

- No engine run (repository code refused for this worker): engine figures are quoted from FOOTING_COMPARISON.json,
  T-037 and T-058, not re-measured. Whether the engine emits M3 is open.
- Founding level, neck heights, excavation and backfill stay HELD (owner Q-21, task T-042).
- Blinding: the freelancer prices 15.00 x 31.37 x 0.10 = 47.055 m3 over the whole plot; the typical details print
  10 cm blinding only under footings and ground beams (10 cm past each face). Not measured here.
- The freelancer's 71.7 m and 42 m are bare numbers in his workbook; their exact runs are not identifiable.
