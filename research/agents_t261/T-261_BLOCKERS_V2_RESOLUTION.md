# T-261: blockwork register v2, the 41 blockers wall by wall (development villa; every villa by rule R-T261-1)

Worker 2, claim 2026-10-24 13:41 UTC, lane A, gate 2. Base: working head 991f85fa (T-228 r2 MERGED bf4dd2a9 is an
ancestor). Register v2 (research/agents_t228) is READ ONLY: nothing is applied, no BOQ line moves, released default stays
V2.9 + route G. Drawings cited by Drive title and entity handle only; no coordinate, image or client name is committed.
ERS: read; s.2.1 (each piece is its own physical element), s.2.2 evidence hierarchy (plan geometry by handle, ST
schedule / frames, Checker figures), s.3 build before deduct (an opening is deducted only from the piece it physically
pierces), s.4 rule + test, s.7 row below.

## 1. The engineering question and the answer

For each blocker: is the missing item printed on another sheet? Searched this run: the full text of ST7757 dxf.dxf
(general notes on unmarked beams, lift / tie-beam notes, the dome detail) and the architectural plan geometry
(P7757.dxf) for every opening on a wall that also carries a held piece.

- **No missing ITEM was found printed elsewhere.** ST7757 dxf prints no general rule for unmarked beams (0 hits for
  'UNLESS', 'OTHERWISE', 'NOT SHOWN / MARKED', 'ALL BEAMS'), no 'LIFT' or 'TIE BEAM' text (the lift tie beam lives
  only in the PDF note 19: consultant D-43), and the DETAIL OF DOME (1A18, '(N.I.S)' 1A19) prints ring bars only
  (3%%c16 1A47, 3%%c18 1A4B, 8%%c8/m 1A29, 2%%c14/20cm 1A37, %%C12MM/15cm 1A0E), no ring size or level. Annex datum
  (owner Q-54 B HOLD), the seven undrawn opening heads (T-201 searched every sheet incl. the DWF), the CB2 width
  CONFLICT and the glazed strips stay as T-227 / T-228 named them.
- **What the drawings DO settle is which part of each wall is already established.** Eight held-net walls carry a
  held piece (a stair-shaft piece, an unlabelled span, a dome-opening piece) beside pieces whose heights are printed.
  The register could not form any net on them because one opening list was booked against the whole wall. Assigning
  each opening by its drawn jambs to the one piece it pierces (rule R-T261-1) gives each wall an established part
  (SOURCE-SUPPORTED PENDING INDEPENDENT CHECK) plus a HELD increment that keeps its figure, never 0.

## 2. Split walls (T261_SPLIT.csv: pieces, jamb offsets, handles)

| Wall | t / type | Established pieces (h) | Openings in them | Est. gross | Ded. | **Est. net** | Still HELD (figure, not a quantity) |
|---|---|---|---|---|---|---|---|
| GF-W10 | 0.20 W | CB2 3.470 + CB2 3.350 (4.00), B24 3.550 (3.75): Checker's own pieces | W05, W06, W07 (3 x 0.480) | 40.5925 | 1.440 | **39.1525** | stair-foot piece 2.500 m on the printed +0.30 landing with D-GF-09 (8.270); W.C. stretch 0 .. 0.945 |
| 1F-W10 | 0.20 W | CB9 3.470 / 3.350 / 3.550 (3.70) | W21, W22, W23 (3 x 0.480) | 38.369 | 1.440 | **36.929** | B3 shaft piece 2.500 m with W25 1.500 (9.500 - 1.500 = 8.000) |
| 2F-W02 | 0.20 W | B8 3.470 (3.45) | W28 0.480, W29 1.800 | 11.9715 | 2.280 | **9.6915** | B3 shaft piece with W27 (8.000); length residual 0.097 m (0.335); BM-2F-015 0.933 m (3.219 .. 3.545) |
| 1F-W04 | 0.20 W | B2 2.777 (3.80) | W13 2.760 | 10.5526 | 2.760 | **7.7926** | BM-1F-032 0.823 m (depth not printed, D-04) |
| 2F-W03 | 0.15 W | B2 2.430 + B1 1.740 + B2 3.196 (3.80) | D-2F-01 2.200 | 27.9908 | 2.200 | **25.7908** | BM-2F-017 / -018 2 x 0.267 m (1.015 each) |
| 2F-W07 | 0.20 W | B15 2.741 (3.00) | W26 1.875 (arched outline, T-238) | 8.2230 | 1.875 | **6.3480** | BM-2F-016 2.984 m (8.952 .. 11.339) |
| 1F-W18 | 0.15 B | B5 + slab 1F-057 + B6 (register 17.934) | none | 17.934 | 0 | **17.934** | dome-opening piece 0.439 m, top not drawn |
| 1F-W24 | 0.15 B | slab 1F-094 + B6 (register 5.651) | none | 5.651 | 0 | **5.651** | dome-opening piece 1.024 m, top not drawn |
| **Total** | | | | | | **149.289** (27.389 m3) | |

How the assignment was read (Checker: re-measure from these, never these numbers as expected):
- SL-1 line (GF-W10 / 1F-W10 / 2F-W02): the plan draws the same column outlines on every storey frame (S-COL.BON GF
  2F7E / 2F81 / 2F84 / 2FC9; 1F 2FE1 / 2FE4 / 2FE7 / 300B; 2F 2F63 / 2F66 / 2F69): faces 2.500 | 3.470 | 3.350 | 3.550
  m. Jambs from the piece's start face: W05 / W21 / W28 0.375 .. 0.975 (3E2 / 3E1, CC4 / CC3, 133D / 133C); W06 / W22
  2.870 .. 3.470 (3EF / 3EE, CD1 / CD0); W29 2.270 .. 3.470 (1330 / 132F); W07 / W23 0.400 .. 1.000 of the 3.350 span
  (3FC / 3FB, CDE / CDD); D-GF-09 1.453 .. 2.353 (outer-face gap 2B8 / 2B9, the 0.900 Checker width), W25 / W27 1.400
  .. 2.400 (CEB / CEA, 134B / 134A) of the 2.500 shaft piece. W25 and W27 are the shaft windows; they go with the
  HELD piece.
- 1F-W04 / 2F-W07 (walls along y) and 2F-W03: the T-110 member positions (ST frames, metres) mapped onto the plan frame
  with the SL-1 B3 member as the common point (checked on two storeys, one constant 0.05 m band offset): W13 (C5A ..
  C5C) lies inside B2 BM-1F-006, 1.000 m clear of BM-1F-032; W26 (12CF .. 12D1) inside B15 BM-2F-007, 0.55 m clear of
  BM-2F-016; D-2F-01 (D115 block 12BA) inside B2 BM-2F-004, 0.83 m clear of the nearer unlabelled piece.
- 1F-W18 / 1F-W24: no opening in the run (T-175 hosts; T-249 inventory).

Not split (each says why in T261_BLOCKERS.csv): 2F-W05 (door D-2F-02, d220 block 12C2, lies under the unlabelled
BM-2F-017, so its 1.980 belongs to the held piece; but the mapped member extents leave 0.70 m of the 2.250 m run
under neither member: re-measure first), 1F-W11 / 1F-W13 / 1F-W17 (doors not located against the dome-face pieces
this run), GF-W03 (two marks on one span, D-03, and no printed base under the ST-02 flight).

## 3. Effect (net installed blockwork, development villa; proposed, nothing applied)

Established net 449.260 -> **598.549 m2 (+149.289, +33.2 %)**, m3 80.674 -> 108.063 (+27.389); VERIFIED 4.458 and
PROJECT-SPECIFIC 85.144 unchanged; the 149.289 is SOURCE-SUPPORTED PENDING INDEPENDENT CHECK until the Checker
re-measures every split wall (programme s.5). Walls with no established part: 39 -> 31 of 76; the eight split walls
keep a HELD increment (figures above, never 0). By floor x thickness x type: T261_COVERAGE.csv (GF 0.20 white +39.153;
1F 0.20 white +44.722; 1F 0.15 black +23.585; 2F 0.20 white +16.040; 2F 0.15 white +25.791).

Against the freelancer (comparison column only, never a target; not like for like while walls are held):
GF external 94.706 -> 133.859 vs his 266.355; 1F external 103.967 -> 148.689 vs his 165.621 (his includes 41.25 m2 of
projections with no wall run); 1F internal 0.15 89.039 -> 112.624 vs his 195.098 (his includes 66.00 m2 of parapet);
2F external 21.476 -> 63.306 vs his 86.575. No per-wall freelancer row: verdict proposals RULE_DIFFERENCE (piece
heights by printed member, Q-60 A, vs his one height per floor) on the split walls; no total verdict while a wall in the
section is held (ERS s.7, an equal total is never agreement).

## 4. Still HELD (33 blockers + the held pieces of the 8 split walls)

| Cause | Walls | Exact missing item | Who |
|---|---|---|---|
| annex datum (Q-54 B) | GF-W00, W02, W04, W06, W17, W18, W23, W24, W25, W27, W35 | annex roof slab top / build-up | designer D-39; owner Q-54 B HOLD |
| lift tie beam | GF-W08, W09, W13, W14 | b x h of the lift tie beam (ST PDF p.8 note 19; not in the DXF) | consultant D-43 |
| held opening head | GF-W15, W26, W30, 1F-W07, 1F-W14+W15, 1F-W16, 2F-W00 | head / size drawn on no sheet | designer / consultant |
| beam depth | GF-W03 (D-03), 2F-W05 (+ the D-04 pieces of the split walls) | depth of an unlabelled span | designer D-04 / Q-61 C |
| dome opening | 1F-W11, 1F-W13, 1F-W17, GF-W36 (+ 1F-W18 / 1F-W24 pieces) | top of wall under the open ring (dome detail N.I.S.) | designer (S0); client request S1 not issued |
| stair shaft (R-T228-3) | pieces of GF-W10, 1F-W10, 2F-W02 | stair landing members on the shaft line; the +0.30 base is printed | lane S (stair detail) |
| strips / increments | GF-H01, GF-H02, GF-W37; GF-W22 / GF-W34 (0 .. 0.013 / 0 .. 0.014) | material / base / top; CB2 width | designer |

No owner question: none meets ERS s.2.7 (designer / consultant items or an existing owner HOLD).

## 5. Rule, test, lessons row (ERS s.4)

- **R-T261-1** (research/agents_t261/piece_split.py; any villa; provenance R-T228-1 point 5, programme s.2 / s.5,
  ERS s.3): a wall with a held piece carries established part + HELD increment; a piece is established only with a
  printed member / slab height (or a Checker figure) on the storey basis and no bare stair member on top; each opening
  goes to the one piece its two jambs lie in; a straddling opening leaves the wall wholly HELD; pieces close to the
  census length (a residual is its own HELD piece); a finish / freelancer / default / bare storey height is refused; the
  HELD increment is never 0.
- **tests/t261_blocker_split** (18): villa N (not Alsenan; hand truth in the docstring: wall under beams of two depths
  14.000 + 11.375 - 1.800 = 23.575 with a no-beam piece HELD, also mirrored; stair-foot piece on a raised landing HELD,
  13.520 established) + adverse (finish / freelancer / default / storey height refused, height with no source refused,
  HELD shown as 0 refused, held piece dropped -> NOT_CLOSED, millimetres, duplicate and unknown pieces, straddling
  opening -> wall HELD) + Alsenan (outputs reproduce, GF-W10 = the Checker's 39.1525, 1F-W10 36.929, stair-line
  pieces held with W25 / W27 / D-GF-09, split gross = register v2 gross within 0.003, every still-held blocker named,
  no coordinates in the outputs).
- Lessons row proposed: 2026-10-24 | eight held-net walls showed no established net at all although most of each wall
  stands under printed members (149.289 m2) | the opening list was booked against the whole wall, so one held piece
  held every opening and the whole net | an opening is deducted from the piece its two jambs pierce (drawn geometry);
  a wall with a held piece carries established part + HELD increment, never one number and never 0 (any villa) |
  tests/t261_blocker_split (normal: two depths + held piece; adverse: straddling opening, held as 0, finish height) |
  PROPOSED.

Reproduce: `python3 -I research/agents_t261/build_t261.py --check`.
