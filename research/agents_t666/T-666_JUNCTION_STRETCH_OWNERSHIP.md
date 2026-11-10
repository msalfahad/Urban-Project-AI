# T-666 Junction-square ownership of the unlabelled beam pieces (F-T661-1) and the boundary band under the building stretches

Worker 1 (lane S), 2026-11-10, run session_01E6cPndsvxb4W1htCmqDcoK, branch `agents/task-T-666`. Research only: no
engine module, candidate line, rule file or method version changed; nothing released; wiring is lane I. ERS s.2 - 5;
UP-CONC-JOINT-001 (column-beam joint, LEAD_ADOPTED), R-CONC-OWN-1 1.0.0-proposed, R-T660-2, R-T659-3, Q-20, Q-62 A cond.
Development villa, not an accuracy claim.

## 0. Sources and run

- Lines: `research/agents_t661/out/LINE_INDEX_V3_0_62.json` (candidate V3.0.62, Gate B PASS); band bound
  `research/agents_t659/out/T659_LEDGER.json`.
- Own read this run (Drive 'Alsenan chalet project', read-only, decoded into `.work/private` only): 'ST7757 dxf.dxf'
  (2F / 1F roof-slab plans, FOUNDATION PLAN, GROUND BEAMS PLAN) and 'ST7757.pdf' p.1 (general notes), p.13 (ground-beam
  details), p.14 (typical boundary wall A-A), read by eye. `t666_extract.py <decoded dxf>` prints every geometric
  value used (relative, m); `t666_alsenan.py --write` -> `out/T666_LEDGER.json`; rules `t666_rules.py`.

## 1. Physical element (ERS s.2.1)

A junction square is the plan square where a beam piece meets another member, carried through the depth of whichever
member owns it. One owner line per square (Q-20, Q-62 A cond): a column whose outline contains it (UP-CONC-JOINT-001:
column to the slab top); else a line whose measured span covers it; else the piece itself (never in neither).

## 2. (a) F-T661-1: the five R-T660-2 pieces (m3)

| Line | Piece | Squares and owner (DXF) | Length owned | Before V3.0.62 | After | Beside (not added) |
|---|---|---|---|---|---|---|
| L-dc8cbfc1 | 2F BAND0008.1 | south: PIECE (edges 399 / 39C start on outer line 392; the south band's inner face is drawn as 394 / 395 stopping at the piece; BAND0004 / 0005 measured to its faces); north: COLUMN 418 (crossing band 398 / 3A2 lies inside the 0.20 x 0.70 column; BAND0007.1 / .2 stop at its faces) | 1.400 | 0.111944 .. 0.335832 | **0.112 .. 0.336** | |
| L-7c3edce2 | 2F BAND0011.1 | south: PIECE (3A1 / 39E on 392; 393 / 394 stop at it); north: COLUMN 41E | 1.400 | 0.111944 .. 0.335832 | **0.112 .. 0.336** | |
| L-d62d2fcf | 2F BAND0006.1 | SW corner: PIECE (397 / 3AD on 392; 393 starts at 3AD; BAND0003 stops there); north: COLUMN 424 (772 / 773 inside it) | 3.100 | 0.247976 .. 0.743928 | **0.248 .. 0.744** | |
| L-8d031491 | 2F BAND0001.3 | west: column 415 face; NE corner: PIECE (38D / 38E run to outer line 39A; east band face 39B stops at 38E; BAND0009 B7 measured 6.60 to 38E) | 1.130 | 0.090376 .. 0.271128 | **0.0904 .. 0.2712** | GAP 0 .. 0.014 (B7 0.75 deep stops at the corner; piece low 0.40) |
| L-f83c4a46 | 1F BAND0005.1 | south: THROUGH B23 (5E4 / 5E1 0.45 run through; span BAND0031.2 covers it); north: column 691 face | 0.800 | 0.064016 .. 0.192048 | **0.064 .. 0.192** | 0 .. 0.0405 (piece below B23 soffit only if deeper than 0.75) |
| | **5 lines** | | | **0.626256 .. 1.878768** | **0.626400 .. 1.879200** | |

Depths: R-T660-2 breadth-0.20 schedule envelope 0.40 .. 1.20 (unchanged). Change +0.000144 / +0.000432 m3 = route G
face-to-face lengths (1.3993 / 1.1297 / 3.0997 / 0.8002) replaced by the drawn edge lengths (exact on the DXF).

**Finding (resolves F-T661-1, residual 0.000 m3).** The Checker's two readings both mislocate the square:
- near-face lengths 1.200 / 1.200 / 0.930 / 2.900 drop the south / corner squares that the drawing puts inside the piece
  and that no other line bills (BAND0003 / 0004 / 0005 / 0009 stop at the piece's faces): 4 x 0.016 .. 0.048 m3 would
  be in NO line;
- the far-face reading (south band face to the far face of the crossing band) gives the same 1.400 / 3.100 numbers,
  but its 0.20 square at the crossing band is inside column 418 / 41E / 424, which owns it to the slab top
  (UP-CONC-JOINT-001; the columns' 2F lines L-53f223b0 / L-33a9b772 / L-c10e2945 are HELD, blank, D-39 roof datum).
So the bounds stand (to the drawn length); the square each piece owns is at its outer end. The only open concrete is
named beside two lines and never added: 0 .. 0.014 (NE corner below the piece soffit) and 0 .. 0.0405 (1F piece below
B23) - both close with the piece depth (D-04).

Floor check by hand (2F roof, the same plan; route G extents from `agents_t110/BEAM_MEMBER_REGISTER.csv`, column
outlines 40F / 412 / 415 / 418 / 41B / 41E / 421 / 424 from the DXF): every band crossing / corner has
exactly one owner under R-T666-1. Of the 38 line ends of the 19 lines, 12 meet a junction square: 5 inside a column
(40F NW corner, 412, and the crossing squares in 418 / 41E / 424), 3 in a through span (B8 over BAND0008.3's north
end, B7 BAND0009 at BAND0007.2's east end and at the SE corner), 4 kept by the pieces above (SW, NE, the two south
squares); every other end stops at a column face. GAP 0, DOUBLE 0 apart from the known
T-220 item (B7 billed through the planted column 778, owned by B7 there). Not committed as code (hand census for the
Checker).

## 3. (b) Boundary band L-6290a9f3 on the building stretches

- FOUNDATION PLAN (ST p.2): closed S-BOUN pair 1658 / 1659 (0.20, centre line 91.94) with ONE ANSI37 hatch 1657 over
  the whole ring: **the band is drawn under all three stretches** (side 1, lower street, lower sea).
- GROUND BEAMS PLAN (ST p.3): the building's 0.30 exterior G.B (F8 / 7D4, FC / 7D0, 136 / 7D5 = 6.70 m, FD / 7E0 =
  7.90 m) on the same plot line, covering the band's 0.20 strip in plan; the N.G.-level boundary pieces 7FE / 7FC / 810
  abut the G.B ends (no overlap).
- Levels: ST p.1 note 2 (neighbour side): exterior ground beams cast ABOVE AND BELOW black brick built up from the
  foundation level; ST p.13 exterior-wall G.B: from GF slab level to the outer normal ground level ('FOLLOW ARCH.', D-35)
  on 10 cm blinding; ST p.14 A-A: lower beam at the base, brick 'AS PER EXCAVATION DEPTH BELOW N.G. LEVEL' between.

| Stretch | Band centre line under the G.B | inside footings | free | Vertical relation | Deduction |
|---|---|---|---|---|---|
| side 1, under F8 | 10.43 | 2.33 | 8.10 | DISJOINT (note 2) | 0 |
| side 1, under FC | 18.77 | 10.60 | 8.17 | DISJOINT (note 2) | 0 |
| street lower 6.70 | 6.60 | 1.40 | 5.20 | DISJOINT (p.13 + p.14) | 0 |
| sea lower 7.90 | 7.80 | 4.25 | 3.55 | DISJOINT (p.13 + p.14) | 0 |
| **total** | **43.60** | 18.58 | **25.02** | | **0** |

Result: the band continues under every building stretch (drawn); the band line bills the foundation-level prism and
the G.B lines bill the N.G.-level prisms of their title depths (R-T658-1 / 3 / 8): no 3-D intersection, nothing
removed, nothing counted twice. **L-6290a9f3 stays HELD 5.6392 .. 11.0328 m3** (T-659 bound; V3.0.62 still carries
the point 7.2204: wire the T-659 bound). No new designer item (the sheets settle it). Named, not concrete: on the street
/ sea stretches no note names what fills between the G.B soffit and the band (note 2 is the neighbour side): a masonry
question for that trade.

## 4. Owner manual method beside the drawing method; who is right

| Item | Owner / freelancer method | Drawing-derived | Verdict proposal |
|---|---|---|---|
| 5 pieces | no rows (unlabelled) | 0.6264 .. 1.8792 HELD | not comparable |
| band | Q-28 A 8.459 (owner provisional); freelancer 8.604 (71.7 m x 0.20 x 0.60) | 5.6392 .. 11.0328 HELD | WITHIN; UNRESOLVED (section C1, Q-28) - unchanged by T-666 |

## 5. Rules, tests, lessons row (proposed)

`t666_rules.py` R-T666-1 (one owner per junction square: column > through span > the piece; near / far face follows
the owner) and R-T666-2 (boundary element on a stretch shared with a building G.B: drawn -> kept; plan coincidence
deducts nothing; DISJOINT 0, INTERSECT with precedence once, otherwise HELD exposure). `tests/t666_junction_ownership`
(32): hand villa V666 T-junction normal; column-at-junction adverse (beam drawn through the column); near-face loses a
square; mirror / rotation / translation; through member + exposures; DOUBLE / PARTIAL refused; mm, missing, mid-span,
nothing left, low > high; band on plot line DISJOINT / UNKNOWN / INTERSECT / bad relation; development rebuild from
committed files, each line once, key figures, band unchanged, no absolute coordinate.

Lessons row (ERS s.7): | 2026-11-10 | a junction square was placed at the crossing band (inside a column) and a near-face
length was proposed for 4 pieces | the square's owner was read from the piece's ends, not from which line's drawn
outline and measured span holds it | one owner per square: column (to slab top) > a line whose span covers it > the
piece itself; the piece runs to the far face only for a square no other line bills (every villa; R-T666-1) |
tests/t666_junction_ownership | PROPOSED |

## 6. For the Checker (re-measure)

1. Square 2F BAND0008.1 north: 398 / 3A2 inside column 418 (0.20 x 0.70), BAND0007.1 / .2 stop at 418's faces.
2. Square 2F BAND0001.3 NE corner: 38D / 38E end on 39A, 39B stops at 38E, BAND0009 6.60 m.
3. Stretch: street lower 136 / 7D5 (6.70) over the hatched band 1657; band centre line 6.60, in footings 1.40.
