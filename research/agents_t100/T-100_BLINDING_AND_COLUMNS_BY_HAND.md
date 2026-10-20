# T-100: blinding and columns by hand (Alsenan; NO REPO CODE)

Worker 1, 2026-10-20 12:23-12:45 UTC. Hand reading of the structural drawings; no engine, rule, knowledge, test or data
file changed and no repository code was run (the code self-check of this run was refused, see the board). Development
reference only, not an accuracy claim. Drawings are named by Drive folder and title only; the CSVs hold marks, sizes,
counts and m3, no coordinates and no client data.

## Inputs (read in the session scratchpad, never committed)

| Input (Drive "Alsenan chalet project") | sha256 | Used for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179...38079 (= manifest) | footing outlines (foundation frame), ground-beam edge pairs and arcs (ground-beam frame), column outlines on the column-and-axis plan and on the three roof-slab plans |
| "ST7757.pdf" (16 pages) | 74da1523...337e3 | p.1 column-and-axis plan (marks, printed sizes, dimensioned C8), p.2 foundation plan, p.3 ground-beam plan, p.4-6 roof-slab plans (column presence per storey), p.9 schedules of columns and footings, p.10 schedule of simple beams (SB1-SB3), p.13 typical footing and ground-beam details |
| freelancer concrete workbook (حصر خرسانة+الحديد) | ae608411...1957c | his rows only, never as a value source |

Method: a stdlib reader of the DXF group codes (scratchpad only), rectangles and arc bands rasterised at 1 cm to take
unions (each square metre once), and the PDF pages read by eye at 200-300 dpi for every printed number used.

## 1. What the drawings print about blinding

| # | Source | Print |
|---|---|---|
| P1 | p.13 "TYP. DETAIL OF ISOLATED FOOTING." (second detail) | `10cm Plain con.` under the footing, dimension `10 | L x W | 10`: plan (L + 0.20)(W + 0.20), 0.10 thick |
| P2 | p.13 first footing detail (level difference > 2.5 m) | `10cm Plain con.` under the footing (projection drawn, not dimensioned); upper and lower ground beams |
| P3 | p.13 all four ground-beam sections (30x30, 30x40, 30x60, exterior 30 x "FOLLOW ARCH.") | `10 | 30 | 10` and `10` thick under each: 0.50 x 0.10 per metre of beam |
| P4 | p.13 both footing details | ground beams at ground-floor slab level on compacted fill, the footing well below: two separate plain-concrete layers |
| P5 | p.10 schedule rows SB1 70x50, SB2 100x50, SB3 50x40 | size only: no strap section, no blinding printed for straps |
| P6 | p.14 typical boundary wall (T-065 E4, E5) | 10 cm blinding under a 130x80x30 base; base count not printed |
| P7 | p.13 slab-on-ground notes | `COMPACTED SOIL` / `Well graded clean compacted fill` under the ground slab: no blinding layer under the slab or the courts |
| P8 | SH01 pool detail (T-044) | `10cm PLAIN CONCRETE.` under the pool (pool member, task T-049) |

## 2. Blinding by member (BLINDING_BY_MEMBER.csv)

Footings: 26 drawn footings, every drawn size = its schedule row (T-065), blinding (L + 0.20)(W + 0.20) x 0.10:

| Type | n | L x W (m) | m2 each | m3 |
|---|---|---|---|---|
| F | 4 | 0.90 x 0.80 | 1.100 | 0.440 |
| F2 | 2 | 1.90 x 1.70 | 3.990 | 0.798 |
| F3 | 2 | 1.60 x 1.40 | 2.880 | 0.576 |
| F4 | 2 | 2.20 x 2.00 | 5.280 | 1.056 |
| F5 | 2 | 2.40 x 2.10 | 5.980 | 1.196 |
| F6 | 1 | 2.60 x 2.20 | 6.720 | 0.672 |
| F8 | 1 | 4.00 x 3.60 | 15.960 | 1.596 |
| F9 | 1 | 3.40 x 2.70 | 10.440 | 1.044 |
| F11 | 1 | 3.50 x 1.50 | 6.290 | 0.629 |
| F12 | 1 | 4.40 x 3.20 | 15.640 | 1.564 |
| F13 | 1 | 4.30 x 2.40 | 11.700 | 1.170 |
| F14 | 1 | 3.80 x 3.30 | 14.000 | 1.400 |
| F15 | 1 | 1.80 x 1.00 | 2.400 | 0.240 |
| FF (lift raft) | 1 | 4.60 x 4.50 | 22.560 | 2.256 |
| FN | 4 | 1.00 x 1.00 | 1.440 | 0.576 |
| sum | 25 | | 152.130 | 15.213 |
| FN / F9 projections overlap, once | | | -0.337 | -0.034 |
| **footings, released-ready** | | | **151.793** | **15.179** |
| F10 (+ the F pad in its outline) | 1 | schedule 2.80 x 1.40 + 0.90 x 0.80, or drawn outline 3.25 x 1.40 | 4.80 + 1.10 / 5.13 | **HELD 0.480 - 0.590** (owner Q-31 C) |

Ground beams (all drawn on p.3: 41 straight edge pairs 0.30 apart + 2 curved beams from the arc pairs, the annex quarter
circle r 1.00 / 1.30 and the beam round the pool r 2.25 / 2.55; drawn length 204.77 m straight + 1.81 + about 7.0 m
curved): strips 0.50 x length = 106.78 m2 gross; crossings once -4.50; column / neck footprints that pierce the layer
-5.37; **net 96.91 m2**. Of it, 41.57 m2 lies in plan over footing blinding. Two readings of the drawings (P2 vs P4):

| Reading | What it means | m2 | m3 |
|---|---|---|---|
| R (detail "LESS THAN 2.5m", P4) | beam blinding is its own layer at beam level, also over a footing | 96.91 | **9.691** |
| L (union with the footing layer, the engine's method) | beam blinding over a footing not counted | 55.34 | **5.534** |

Which footing detail governs depends on the level difference between ground beam and footing, i.e. on the founding
level, which the owner holds (Q-21 C). So the beam blinding is HELD between 5.534 and 9.691 m3; the ground-beam length
basis (GB_LENGTH_BASIS) is a second, smaller hold on the same line (drawn edge lengths used here).

Straps SB1 / SB2 / SB3: (B + 0.20) x clear length (T-065: 4.55 / 2.294 / 3.259 m) = 4.095 + 2.753 + 2.281 = 9.129 m2,
0.913 m3 **HELD** (P5: no strap section or blinding printed; the engine includes them in its beam blinding).
Boundary-wall bases: HELD (count not printed, T-065 C3). Pool: with the pool (T-049).

Totals: released-ready 15.179 m3; all members hand range **20.713** (L, no straps, F10 out) to **26.373 m3** (R + straps +
F10 0.590). Engine 22.155 m3 lies inside it.

## 3. Engine vs hand vs freelancer, blinding

| Term | Engine (T-044 run B / T-064) | Hand | Freelancer | Difference and cause | Proposal |
|---|---|---|---|---|---|
| footing layer | 15.659 (156.59 m2) | 15.179 + F10 HELD 0.480-0.590 | (in one plate) | +0.480 = F10 at its schedule size, released while the footing F10 itself is HELD (Q-31 C); the rest = hand to the cm2 (FN / F9 overlap once in both) | ENGINE_RIGHT on 25 footings; F10 blinding must follow its footing: HELD (engine releases a held member's blinding) |
| beam + strap layer | 6.496 (64.96 m2, union with the footing layer) | L 5.534 + straps 0.913 = 6.447 (64.47 m2); R 9.691 + 0.913 | (in one plate) | engine = reading L + straps within 0.49 m2 (0.8 %); the deduction of 41.57 m2 over footings and the strap blinding both rest on unprinted choices | UNRESOLVED (held on Q-21 C and P5) |
| total | **22.155** | released-ready 15.179; range 20.713 - 26.373 | **47.055** | freelancer 15.00 x 31.37 x 0.10: one plate under the whole plot (470.55 m2: courts, garden, building). No sheet draws it; P7 prints compacted soil under the ground slab. Same 0.10 thickness, so the whole -24.900 m3 (-52.9 %) is the basis | ENGINE_RIGHT on basis (member layers as drawn); freelancer's plate is RULE_DIFFERENCE / not on the drawings |

Case for the Lead (not chosen here): 8 footings are drawn ON the plot line (3 F, F11, F14, F8, F15, FN); their 10 cm
projection on that side falls outside the plot (1.89 m2 = 0.189 m3, included in the 15.179 above). No Urban rule says
whether a projection that cannot be built beyond the boundary is measured.

## 4. Columns per storey (COLUMNS_BY_STOREY.csv)

Count: the column-and-axis plan (p.1) prints 35 marks with sizes (5 C, C1, 4 C2, 6 C3, 2 C4, 3 C5, C6, C7, 2 C8, 2 C9,
C10, 2 C11, 5 CN); each was bound to its outline by mark and printed size, then followed by position onto the
ground-floor, first-floor and second-floor roof-slab plans (p.4-6): a column stands on a storey when its outline is drawn
on that storey's roof-slab plan. Section = the schedule band of that storey (p.9, printed); height = printed level interval
(GF +1.00 to +5.50 = 4.50, 1F +5.50 to +9.70 = 4.20, 2F 4.20 from the elevation chain, T-064 DRAWING-VERIFIED).

| Storey | Columns drawn | m3 at floor-to-floor | of which HELD | Engine (run B) | Freelancer (his height) |
|---|---|---|---|---|---|
| GF | 30 (no CN) | 20.250 | 8 lines 4.725: the 7 columns in the annex zone (+0.30 floor, height waits on Q-54) and the C8 below | 30 lines 20.247 | 32 at 3.75 = 17.438 |
| 1F | 18 + 2 planted (P.C 20x70, P.C 20x50 printed on the GF roof slab) = 20 | 10.248 | 1 line 0.756 (C8 below) | 21 lines 10.668 | 19 at 3.45 = 7.728 |
| 2F | 8 + 1 planted (P.C 20x50 printed on the 1F roof slab) = 9 | 3.948 | 0 | 13 lines 5.796 | 9 at 3.45 = 3.381 |
| total | 59 | **34.446** (releasable 28.965) | 5.481 | **36.711** | 28.547 |

- GF: engine = hand to 0.003 m3 (same 30 columns and sizes): ENGINE_RIGHT on count and section.
- 1F: engine +1 C3 (0.20 x 0.50 x 4.20 = 0.420): the 1F roof-slab plan draws only 2 C3; ENGINE_WRONG, HAND_RIGHT (p.5).
- 2F: engine +2 C3, +1 C5, +1 C8 = 0.840 + 0.420 + 0.588 = 1.848 m3: the 2F roof slab covers only the stair / tank core
  and draws 9 columns (p.6, checked at 200 dpi); ENGINE_WRONG, HAND_RIGHT. Together the engine is 2.268 m3 over on 1F / 2F
  (the run's 2F presence test did not bind the core plan).
- C8 at the lower neighbour side: p.1 prints `C8 30X80` with dimensions 70 + 10 = 80, the schedule gives C8 30 x 90 (and
  the slab plans draw 0.80): two printed values disagree, so this column is HELD on every storey (GF 0.900 at 0.80 / 1.013 at 0.90,
  1F 0.672 / 0.756) - a designer question, not an engine choice.
- Height basis: engine and hand take the full floor-to-floor interval; the freelancer takes 3.75 / 3.45 (= interval -
  0.75, the deepest beam). At his heights the hand count gives 28.536 m3, within 0.011 of his 28.547 (his count and size
  slips offset: GF C1 2 / C2 6 / C9 3 / C11 1 vs drawn 1 / 4 / 2 / 2, 1F no C6 and C7 2 / C8 1 / C9 1 vs 1 / 2 / 2, 2F C9
  at 0.90 vs schedule 0.70). The 5.91 m3 between the two bases is a measurement rule (does a column run through the slab
  / beam depth?); no Urban rule found: case for the Lead. Verdict: RULE_DIFFERENCE on height; on counts / sizes HAND_RIGHT
  vs freelancer (GF -2 C2 -1 C1 -1 C9 +1 C3 +1 C11; 1F +1 C6; 2F C9 size).
- Drawn outlines on the slab plans that differ from the schedule band (e.g. GF C drawn 0.20 x 0.40 vs 0.20 x 0.50, 1F
  C5 / C6 / C7 drawn at the GF width 0.25) are listed per line; the schedule is the printed value, the outlines carry no
  printed size.

Necks (counts only, heights HELD by Q-21 C): 35 columns reach a footing (30 + 5 CN; the 4 lift-core columns stand on
the FF raft), engine 28 neck lines, freelancer 34 (C3 5, C11 1, CN 6 vs drawn 6 / 2 / 5). Lift columns print the GF
sizes (C1 / C2 20X50, C9 25X100) already at foundation level on p.1. C4 at the upper neighbour / sea corner prints
30X50 on p.1 but is drawn 0.25 x 0.50 on the foundation plan.

## 5. What is missing / uncertain

- Engine figures are quoted from the T-044 run B line table (research/agents_t044) and the m4 / m5 blinding audit, not
  re-run (code refused this run).
- Ground-beam lengths are drawn edge lengths; the length basis is held (GB_LENGTH_BASIS) and the 0.49 m2 between engine
  and hand reading L was not traced line by line.
- The DXF frame of each roof-slab plan was identified by its position in the drawing row and confirmed by the column counts
  on p.4-6 (34 / 21 / 9 outlines); the verifier should re-measure three footings (F12, F14, FF) and the 2F column count.
