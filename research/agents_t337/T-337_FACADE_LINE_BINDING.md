# T-337: EXTERIOR PLASTER / SIGMA — every face, opening and facade component bound to ONE owner line of V3.0.22 (development villa; every villa by R-T337-1 .. 3)

Worker 2 (lane A), claim 2026-10-29 14:55 UTC, run session_01E6cPnbsXqrEguvnCdbtCSy. Integration dependency of T-314
(lane I). Research only: no engine module, rule or knowledge file, candidate line, released line or V2.9 cell changed;
released default stays V2.9 + route G; nothing released. ERS applied: s.2.1 (each physical face / edge its own item),
s.2.2 (owner manual Q-07 B / Sigma method beside the drawing method on every row), s.2.4 (closure in m2, residuals
named), s.2.7 (no owner question: every open item is a designer / specification item already held), s.3 (one face one
owner; build before deduct; m.l never m2), s.4 (rules + tests), s.7 (lesson row, section 8). No client name, coordinate
or image is committed.

## 1. Inputs and identity

- Merged ledgers built on, not re-derived: T-305 faces / openings / items (9d71ef09), T-311 parapet runs and plinth
  segments (bd7b8c23), T-324 parapet components and corrections C1 .. C6 (bc5df868), T-162 r2 freelancer term map,
  T-317 spatter dash (host lines only).
- Candidate: own run this session, Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (`ab54dd55`)
  and 'ST7757 dxf.dxf' (`9f9d1179`): `research/agents_t167/v304_run.py` then `research/agents_t331/v3022_run.py`;
  **V3_0_22_BOQ_LINES json `7199c8b6` / csv `924a60b4` (3,706 lines)** = the T-331 / Checker V3.0.22 identity; extract
  `CANDIDATE_V3022_T337.json` (the 13 facade lines and the 6 other lines this binding cites, each present).
  The three FIN.EXT.FINISH ids are unchanged from V3.0.18 / V3.0.21 and still carry no quantity (BLOCKED_RFI).
- Freelancer cells: `tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json` (file PLS = Drive 'المساح الداخلى والسجما.xls',
  sheet rows 51-97 and invoice row 25), read cell by cell by the builder (E / F / G / H -> I).
- Builder `t337_alsenan.py --extract / --write / --check`; rules `facade_binding.py`; tests `tests/t337_facade_binding`.

## 2. The rule that decides the owner line (R-T337-1 .. 3, facade_binding.py)

1. **Owner line by element and level band**: plinth (ground -> lowest F.F.L.) -> PLINTH line; storey band ->
   the storey line of the floor whose [F.F.L., next level) holds it **by levels, not by which outline draws it**;
   band above a finished roof -> the PARAPET-OUTER line of that roof, **never a storey line**, also on a top floor
   whose candidate formula ('top floor to the parapet top') would reach it; plate edge over open air -> SLAB-EDGE
   (HELD blank). A ground floor with two F.F.L.s is two parts binding to the same storey line. A band crossing a
   level is refused until split.
2. **Openings once, by hole, on the band that holds them**; a hole leaving its band refused; HELD hole = [0, cap].
3. m2 face lines, m2 surface items and m.l edge lines kept apart; HELD = range, no point value; UNKNOWN = no number.

What this changes against T-305's IN_LINE / NO_LINE states (the only three moves, every one physical):

| Face | T-305 | Now | m2 | Why |
|---|---|---|---|---|
| annex faces SE-1, SW-1, SW-2, NW-1, SW-3 EDGE, NE-6 | +0.30 -> +4.80 in the GF storey line | split at the annex roof +4.30 (T-311): +0.30 -> +4.30 GF storey, +4.30 -> +4.80 PARAPET-OUTER ANNEX | 14.671 moved | the parapet is its own element (material HELD, Q-65 C; T-311) |
| 2F NW-1, NE-1, SE-1, SW-1 | +9.70 -> +14.40 in the 2F storey line | split at the 2F roof +13.90: 9.70 -> 13.90 2F storey 125.160, 13.90 -> 14.40 PARAPET-OUTER 2F 14.900 | 14.900 moved | as above |
| 1F SE-1 face on the annex roof +4.30 -> +5.50 | NO_LINE | GF storey line | 4.080 in | its levels lie inside the GF house storey +1.00 -> +5.50 (rule 1); the face rows replace run x H, so the outline no longer decides |
| 1F NW-2 parapet outer band | 4.585 DRAWING-CONFIRMED | 4.223 .. 4.585 HELD | -0.362 lo | T-324 C3: the roof plan draws the parapet on the 3.2496 m chord, the 1F outline on the 3.5283 m arc; the outer edge is the frame profile |
| annex B34 extension outer face on the boundary line AC7 | not in T-305 | 0 .. 0.600 HELD in PARAPET-OUTER ANNEX | +0 .. 0.600 | T-324 C5: one face, two readings (annex vs boundary wall, Q-65 C) |

Openings: every hole stays on the line T-305 gave it (all 36 census openings in the three storey lines; none in a
parapet, plinth or slab-edge band). Every printed head is checked inside its band after the splits (annex heads
<= +2.80 < +4.30; 2F heads <= +12.50 < +13.90); W11 / W12 / W05 / W17 have an established area with an unprinted datum:
their band is 4.00 / 4.50 / 4.20 m high and the hole cannot rise into the roof slab / parapet above it.

## 3. FILL table for T-314 (FILL_T314_T337.csv; m2; acceptance a, f)

| Owner line | State | Faces | Gross | Openings fixed (of which assumed) | Held deduction | **Net** | Owner Q-07 B part | Status |
|---|---|---|---|---|---|---|---|---|
| GF **L-b05f70c92405dbcfbe62** | EXISTING | 30 | 469.329 | 59.150 (10.560) | 0 .. 33.485 (W02, D-GF-07) | **376.694 .. 410.179, blank point** | 469.329 | HELD (bounded) |
| 1F **L-8bb83e16cc7b104ab88b** | EXISTING | 12 | 265.309 | 30.784 | - | **234.526** | 265.309 | DRAWING-CONFIRMED |
| 2F **L-d52c4f763b19aedf8b8b** | EXISTING | 4 | 125.160 | 7.855 (2.200 D-2F-01) | - | **117.305** | 125.160 | ASSUMED — OWNER-APPROVED part |
| NEW FIN.EXT.FINISH PARAPET-OUTER ANNEX +4.30 | NEW | 7 | 14.671 .. 15.271 | - | - | 14.671 .. 15.271 | 14.671 | HELD (C5 0 .. 0.600) |
| NEW FIN.EXT.FINISH PARAPET-OUTER GF +5.50 | NEW | 3 | 14.385 | - | - | **14.385** | 14.385 | DRAWING-CONFIRMED |
| NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70 | NEW | 11 | 53.551 .. 59.291 | - | - | 53.551 .. 59.291 | 47.458 | HELD (NE-1 / SW-1 / SW-2 heights, NW-2 C3) |
| NEW FIN.EXT.FINISH PARAPET-OUTER 2F +13.90 | NEW | 4 | 14.900 | - | - | **14.900** | 14.900 | DRAWING-CONFIRMED |
| NEW FIN.EXT.FINISH PLINTH GF (geometry: L-c0e9a4c62171de1f369b) | NEW | 29 | 71.689 .. 72.750 | - | - | 71.689 .. 72.750 | outside Q-07 B (RFI) | HELD (pool-court bottom; finish not printed) |
| NEW FIN.EXT.FINISH SLAB-EDGE 1F | NEW | 9 | blank | - | - | **blank** (13.079 m, depth not printed, Q-68 C) | - | HELD |
| **all face lines** | | 109 | | 97.789 | 0 .. 33.485 | **897.720 .. 938.606** + slab edges HELD | | |

W02 and D-GF-07 stay HELD blank by name (acceptance c): the GF line has no point value; its faces GF NW-7 (35.550) and
GF SE-2 (16.650) carry the bounded holes 0 .. 28.485 and 0 .. 5.000.

Non-face items, each its own line (FILL_ITEMS_T314_T337.csv; ITEMS_T337.csv):

| NEW line | Unit | Quantity | Status |
|---|---|---|---|
| FIN.EXT.PARAPET-INNER (above the upturn top) per roof | m2 | annex 8.888 .. 14.914, GF 8.209 .. 13.885, 1F 41.824 .. 56.609, 2F 8.490 .. 14.150 | HELD (split height not printed, D-39) |
| FIN.WP.UPTURN-ZONE-FACE per roof (WATERPROOFING edge detail) | m2 | 0 .. 5.966 / 0 .. 5.554 / 0 .. 9.668 / 0 .. 5.660 | HELD; above + zone = one face 94.123 .. 99.558 (never summed hi + hi) |
| FIN.EXT.PARAPET-TOP per roof | m2 | 5.997 .. 6.037 / 5.593 .. 5.674 / 9.832 .. 9.847 / 5.415 = 26.836 .. 26.973 | HELD (D bands) + 2F DC |
| FIN.EXT.CORNERS | m.l | DC 124.700 vertical + 43.100 mouth ends + 137.110 openings + parapet top arrises 272.960 .. 273.919 = **577.870 .. 578.829**; ASSUMED 32.200 (doors 2.20); HELD 2.10 .. 2.55 (pool-court plinth corners), 0 .. 11.90 (1F parapet ends), 0 .. 1.20 (passage-mouth stop-end, one item for T-305 and T-324), frames 98.002 .. 195.180, slab-edge arris blank | physical m.l; the 2 m = 1 m convention is a half-RATE, shown in T-162 r2 as payable, never an area |
| FIN.EXT.COPING / DRIP / corner-bead accessory / DIVIDER faces | m.l / m2 | no number | UNKNOWN |
| FIN.EXT.FRAME (frames, SE 0.20 band) | m2 | blank | HELD / UNKNOWN |

Other owners named, never in these lines: pool-court soffit L-23072352a28aeca7b051 (FIN.CEILING 12.834, owner item 4);
membrane upturn base m.l in the roof WP lines L-d4c73babd2a275c28929 / L-994b88140f2ea50f1b31 / L-5ce5ba49792e8f9d1f6f /
L-aac1f35e08f85b643692 (2F HELD); plinth wall-course substrate L-4165954ce4871eda30cc (5.059 m2, block, not a finish);
spatter dash B4-05 (T-317's own item on the same faces); boundary fence OTHER_TRADE HELD (Q-65 C); domes NOT_APPLICABLE.

**For T-317 (spatter host lines):** its Sigma hosts move with this binding: GF host 387.285 .. 420.770 -> 376.694 ..
410.179 (-14.671 annex parapet + 4.080 lower-roof face), 2F 132.205 -> 117.305 (-14.900), the parapet NO_LINE host
68.298 .. 73.676 -> the four PARAPET-OUTER lines 97.507 .. 103.847 (it now includes annex / 2F parapets); total host
area unchanged except the named C3 / C5 ranges.

## 4. Closure (CLOSURE_T337.csv; acceptance b)

Every T-305 face once: 98 rows -> 109 binding rows (10 split bands + the C5 face). Drawing-confirmed 1,017.948 =
T-305 1,022.534 - 4.585 (NW-2 now HELD), residual **0.000000**; HELD 11.045 .. 18.447 = T-305 6.822 .. 13.261 + NW-2
4.223 .. 4.585 + C5 0 .. 0.600, residual **0.000000**. Parapet outer per roof against T-324 OUTER_FACE: 2F 0.000, GF
+0.00005, annex -0.00003 (+ the C5 range taken 0 .. 0.600 where T-324 carries 0.600), 1F -0.0007 (+ the C3 -0.362 range):
T-305 4-decimal face areas against T-311 / T-324 run lengths. Plinth against T-311's 29 segments 71.689 .. 72.750:
0.000000. Inner faces, tops and arrises are T-324's quantities carried unchanged (residual 0 by construction).

## 5. Owner method beside the drawing method

Owner notes Sigma 2026-10-21: Sigma is the exterior plaster area (not a second area); Q-07 B bands from the floor;
openings in full where masonry exists (Q-73 A); corners their own m.l line (correction 2026-10-22). The owner Q-07 B
figure is the face rows inside the bands: **storey lines 859.798 + parapet outer 91.414 (+ held) = the T-305 955.797
less the 4.585 NW-2 face now HELD**; the drawing method adds the plinth 71.689 .. 72.750 (an RFI under Q-07 B, held
here as its own line, never folded into GF) and the lower-roof face 4.080 (inside the GF bands by levels). Same
openings in both (full holes); the methods differ only by the plinth.

## 6. Against the freelancer (FREELANCER_T337.csv; acceptance d)

His net 1,469.967 m2 (invoice F25) = gross 1,502.840 (J93) - openings 65.745 (J97) at half 32.873 (D25). By his cells:

| His rows | His m2 | Owner lines here | Drawing | Difference and cause |
|---|---|---|---|---|
| walls 51-55, 58-60, 63-65, 68-71, 74, 77 (I cells) | 968.238 gross; 935.365 net of half openings | the three storey lines + four PARAPET-OUTER + PLINTH | 1,022.534 (+ held) gross; **897.720 .. 938.606** net of full holes | -37.645 .. +3.241 m2 (-4.0 % .. +0.3 %): RULE_DIFFERENCE on openings (his half 32.873 vs full 97.789 + 0 .. 33.485 held, owner item 1: half is his practice, not a rule); his single planes per elevation (rows 64, 58, 59), heights from +-0.00 / +1.00 without the plinth split, 93.150 m2 in rows 65 / 68 / 69 with no drawn face (possible double counts, UNRESOLVED), 210.761 m2 of drawn faces in no row of his (T-162 r2 per row) |
| parapets 78, 79, 83, 84 | 146.659 | PARAPET-INNER + UPTURN-ZONE + PARAPET-TOP | 120.959 .. 126.530 | -25.700 .. -20.129: row 79 ENGINE_RIGHT on the run (B34); rows 83 + 84 +7.5 m of undrawn run; row 78 1.70 m girth printed nowhere (T-324) |
| domes 72 | 181.806 | NOT_APPLICABLE | - | owner item 3 (no domes) |
| pool soffit 73 | 19.154 | FIN.CEILING L-23072352a28aeca7b051 | 12.834 | owner item 4 accepts 12.834 (another line) |
| frames 61, 75 | 28.868 | FIN.EXT.FRAME | HELD blank | profile not detailed (designer) |
| boundary 87-90 | 107.240 | OTHER_TRADE | HELD | Q-65 C |
| drip 92 (0.28 x 181.70) | 50.876 | FIN.EXT.DRIP | UNKNOWN | nothing drawn; owner not answered |
| **total** | **1,469.967** | | wall faces + parapet inner / top **1,018.679 .. 1,065.136** + held / unknown lines | the comparable part is the first two rows; the rest is scope he carries that the drawing or the owner excludes or holds |

Verdict proposals for the Checker: the face-to-line ownership is ENGINE_RIGHT-ready (the candidate lines carry no
quantity: there is no engine figure to judge yet, so UNRESOLVED = HELD, never 0); the opening deduction is
RULE_DIFFERENCE (owner Q-73 A full holes vs his half); rows 65 / 68 / 69 UNRESOLVED (no drawn face); parapet rows as
T-324.

## 7. Tests (acceptance e)

`tests/t337_facade_binding/test_t337_rules.py`, villa N (not Alsenan; hand calculation in its docstring): house
F.F.L. +0.60 / +4.00, annex F.F.L. +0.20 with its roof +3.70 (a two-F.F.L. ground floor), a 1F face standing on the annex
roof, parapets on both roofs: every face once 95.500; GF line 45.600 gross, 41.910 net (W1 1.800 DC, D1 1.890
assumed); 1F 35.200, net 32.200 .. 35.200 (W2 HELD 0 .. 3.000, no point value); parapets 2.500 / 6.400; plinth 5.800;
run x storey height 44.200 shown wrong by -1.400. Adverse: a parapet band in a storey line (refused with or without the
roof named); bands across the F.F.L. / the next F.F.L. refused until split; a held face as 0 refused (blank HELD
accepted); UNKNOWN with a number refused; a DRAWING-CONFIRMED range refused; an opening deducted twice, a hole leaving
its band, a hole larger than its face, a HELD hole bounded at 0 refused; a face booked in two lines refused; an m.l line
used for a face or as m2 refused; reversed order and millimetre levels give the same rows.
`test_t337_alsenan.py`: byte rebuild, candidate V3.0.22 identity and ids, every face once, closure 0, no parapet band in
a storey line, the split storey lines and the lower-roof face, 39 opening rows once (W02 / D-GF-07 HELD bounded, never
0), the slab-edge line blank, UNKNOWN items without a number, T-324 C3 / C5 carried.

## 8. Learned, missing, lessons row (ERS s.7)

- Learned: the candidate's own top-floor formula ('to the lowest parapet top', UP-FACADE-001) folds 29.571 m2 of parapet
  outer face (annex 14.671, 2F 14.900) into storey lines even where T-305 kept the GF / 1F parapet bands apart: a face
  row must carry its band's ELEMENT, and the storey owner must be read from levels (the 4.080 m2 face on the annex
  roof is a GF-level face drawn on the 1F outline).
- Missing (HELD / UNKNOWN, never 0): W02 / D-GF-07 holes (D-53 / D-45); pool-court plinth bottom; 1F parapet heights
  NE-1 / SW-1 / SW-2 and the NW-2 frame profile; C5 face owner (Q-65 C); slab-edge depth (Q-68 C); exterior finish
  specification and plinth finish (plaster / Sigma or cladding, T-317); parapet split height (D-39); coping, drip, beads,
  frames, divider, SE 0.20 band.
- Lessons-register row (proposal): 2026-10-29 | the facade lines carried a top-floor parapet inside the storey line
  ('top floor to the parapet top') while the lower floors' parapets were separate, and a face standing on a lower roof
  had no line because it was drawn on the upper outline | the owner line was taken from the formula of the floor whose
  outline draws the face, not from the element and the levels of the band | bind each face band by element (plinth /
  storey / parapet / slab edge) and by levels: the storey whose F.F.L. -> next level holds the band, a parapet band
  above a roof always on its parapet line (every villa) | tests/t337_facade_binding | proposed.

Files: `facade_binding.py`, `t337_alsenan.py`, `CANDIDATE_V3022_T337.json`, `BINDING_T337.csv`, `OPENINGS_T337.csv`,
`ITEMS_T337.csv`, `FILL_T314_T337.csv`, `FILL_ITEMS_T314_T337.csv`, `CLOSURE_T337.csv`, `FREELANCER_T337.csv`,
`summary.json`; tests `tests/t337_facade_binding/`.
