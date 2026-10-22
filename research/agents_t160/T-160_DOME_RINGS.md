# T-160 Alsenan dome ring beams: the in-bay ring, its overlaps with the straight beams, and the 1F slab 0.37 m2 (NO REPO CODE)

Worker 1 (structural lane S), 2026-10-22. Development villa, not an accuracy claim. Nothing is wired, no engine file and
no released quantity changes: a checked piece for the V3.0 candidate (lane I) and for the beam register.

Sources (Drive "Alsenan chalet project", private copies in `.work/private`, never committed): "ST7757 dxf.dxf"
(sha256 9f9d1179...), "ST7757.pdf" (sha256 74da1523...): p.5 FIRST FLOOR ROOF SLAB (read at 150 dpi: both dome bays,
their framing marks, the ring band, the four see-detail labels per dome), p.7 DETAIL OF DOME (dia 442, ring 20 wide,
depth dimensioned "as per architect"), p.4 GROUND FLOOR ROOF SLAB (searched for dome openings: none, below).
Earlier work used as input, re-measured here, not copied: T-110 beam register (`research/agents_t110`), T-139 slab
ledger (`research/agents_t139/PANELS.csv`, merged ea91168), S8.3 dome study (`research/alsenan_dome_ring_s8_3`).
Rules: owner Q-44 A (the ring round each structural dome opening stays, B4 0.20 x 0.50 from the slab plan),
Q-61 C(2) / C(3) (never duplicate concrete; B4 only where the ring is identified as B4, else HELD),
URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1, UP-QTY-STATUS-001, Q-62 A cond.

Files: `read_bays.py` (reads the bay faces, ring radii and columns from the DXF; prints JSON), `DOMES_INPUT.json`
(the numbers it read, with the member and register id of each face), `dome_ring.py` (closed-form + shapely ring
partition; `--check` = synthetic NON-Alsenan fixture), `DOME_RINGS.csv` (one row per dome, per side, per column),
`slab_1f_gap.py` (the 1F lump test), `arc_ends.py` (does every drawn ring arc end on a bay face?). Repeat:
`python -I read_bays.py <ST dxf> 16.38,41.65 30.83,41.65` -> `python -I dome_ring.py DOMES_INPUT.json --csv DOME_RINGS.csv`;
`python -I dome_ring.py --check`; `python -I slab_1f_gap.py research/agents_t139/PANELS.csv`;
`python -I arc_ends.py <ST dxf> 16,41,17,42 W=14.269,E=18.369,S=39.4403,N=43.8625` (west dome; east dome
`30,41,31,42 W=28.6168,E=32.989,S=39.4403,N=43.8625`; GF pool court `71,46,74,48.5 W=71.4134,E=73.1134,S=45.8278,N=48.5283`).

## 1. Result in engineering terms (concrete, m3; Alsenan development villa)

| Line | Before | After (this hand reading) | Freelancer | Note |
|---|---|---|---|---|
| West dome ring (B4 0.20 x 0.50) | register 0.7553 CALCULATED (in-bay 1.5105 m2) | **0.7552** (in-bay **1.5105 m2** x 0.50; 0.01 %, face rounding) | no row | confirmed: the register already takes only the in-bay part |
| East dome ring (no mark) | register HELD, candidate 0.8997 | **HELD**, candidate **0.8997** (in-bay **1.7994 m2** x 0.50, never released) | no row | Q-61 C(3): no B4 mark on or near it |
| Full-annulus alternative (the checker's warning) | not used by any released line | would add **0.6969 m3** (west) and **0.5524 m3** (east candidate) of concrete already counted in B6 / CB10 / CB13 / B25 / CB12, two columns and one slab panel | - | rejected: double count |
| Beams, register CALCULATED total (T-110 + T-145 CB5) | 65.060 | **65.060, unchanged** (-0.910, -1.38 % vs freelancer) | 65.970 | no dome-ring double count in the register |
| 1F roof slab (hand 19.757 vs freelancer 19.200 m3) | 0.37 m2 unexplained | **UNRESOLVED, immaterial: 0.369 m2 = 0.059 m3 = 0.30 % of the 1F slab** | 120.00 m2 lump | best single trace below; no owner question |

The answer to the checker's side finding: **the double count does not exist in the beam register** (it takes 1.5105 /
1.7994 m2, the in-bay part, not the 2.9042 m2 annulus), and it does not exist in the released route G either (route G
measures only the drawn arc band pieces inside the bay). It exists only as a method risk: the Q-44 hand estimate
("about 1.45 m3 per opening", full centreline circle) and the frozen opt-in M8 scope measure (`scope_quantities._dome`,
ring = pi (r_o^2 - r_i^2) x depth, no deduction) both take the full annulus. On Alsenan the M8 run finds no ring
(ring area 0 on the 2F rib groups), so no Alsenan number carries it today; on another villa whose dome plan draws two
full concentric circles it would. Lane I: never wire a ring from the full annulus; the opt-in binder
`beam_binding_v2.ring_beams` already deducts straight beams and columns.

## 2. One row per dome: ring, overlaps and m3 (re-adding exactly)

Closed form (by hand, `dome_ring.py` header): A_ring = [pi r_o^2 - sum seg(r_o, d_k)] - [pi r_i^2 - sum seg(r_i, d_k)],
seg(r, d) = r^2 acos(d/r) - d sqrt(r^2 - d^2). r_i 2.2111, r_o 2.4111 (DXF, both domes; inner diameter 4.42 = p.7's 442).
Faces = distance from the dome centre to each framing member's inner face (DXF layer 1 lines). Shapely agrees to 3e-7 m2.

| | West dome (centre 16.380, 41.651) | East dome (centre 30.828, 41.651) |
|---|---|---|
| Framing (inner face d / far face, m) | W CB10 inner strip 2.1111 / 2.4111; E CB13 1.9889 / 2.2889; S, N B6 2.2111 / 2.4611 | W B25 2.2111 / 2.7611; E CB12 2.1611 / 2.4111; S, N B6 2.2111 / 2.4611 |
| Full annulus pi (r_o^2 - r_i^2) | 2.9042 m2 | 2.9042 m2 |
| in B6 north / B6 south | 0.2586 / 0.2586 | 0.2586 / 0.2586 |
| in the west member | CB10 inner strip 0.3840 (of it 0.0534 in the column 13.969-14.169 x 40.648-41.248) | B25 0.2586 |
| in the east member | CB13 0.3685 (of it 0.0362 in the column 18.369-18.619 x 41.048-41.748) | CB12 0.3290 |
| past the member's far face | **0.1241** east of CB13 (it reaches 2.4111 > far face 2.2889) = inside slab panel 1F-084 (T-139, tag T16) | 0 |
| **ring in the bay (own concrete)** | **1.5105 m2** | **1.7994 m2** |
| re-add | 1.5105 + 0.2586 x 2 + 0.3840 + 0.3685 + 0.1241 = **2.9042** | 1.7994 + 0.2586 x 3 + 0.3290 = **2.9042** |
| depth | 0.50 (plan B4 mark x 2, schedule B4 20 x 50, Q-44 A): DRAWING-CONFIRMED | **not printed for this ring** (no mark within 3.2 m; p.7 says "as per architect"): HELD |
| ring m3, gross (slab ledger stops at r_o) | **0.7552** | **HELD** (candidate 0.8997 at the B4 size, not released) |
| same, non-overlapping split | slab share 1.5105 x 0.16 = 0.2417 + downstand 1.5105 x 0.34 = 0.5136 (never both with the gross) | HELD |
| opening inside the bay (skylight, Q-44 A) | 14.9818 m2 | 15.3278 m2 |
| slab corners outside r_o (T-139) | 1.6387 m2 (T-139: 0.4677 + 0.3525 + 0.3517 + 0.4668 = 1.6387) | 2.2074 m2 (T-139: 0.5814 + 0.5823 + 0.5223 + 0.5214 = 2.2074) |
| bay check: opening + ring + corners | 14.9818 + 1.5105 + 1.6387 = 18.1310 = 4.1000 x 4.4222 | 15.3278 + 1.7994 + 2.2074 = 19.3346 = 4.3722 x 4.4222 |

The drawing itself confirms the in-bay model: on p.5 / the DXF the outer ring circle is drawn only between the framing
members (west arcs 34.4-66.5, 113.5-151.1, 208.9-246.5, 293.5-325.6 deg); `arc_ends.py` puts every one of the 12 west
arc ends and 8 east outer arc ends on a bay face (within 3 mm), and the framing beams run through unbroken. The west
inner circle is also broken at the CB10 / CB13 faces; only the east inner circle is one full CIRCLE entity reaching
0.05 m into CB12 (section 7, item 3).

Each overlap is removed once: the B6 parts stay in the B6 spans (each spans the full bay width, 4.100 / 4.4222 /
4.3722 m), the CB10 / CB13 / B25 / CB12 parts stay in those members, the column parts stay in the column line
(T-119: columns to the controlling member), and the 0.1241 m2 past CB13 stays in the slab panel 1F-084.

## 3. Beam register before / after and the freelancer, split by cause (dome bays only)

Register CALCULATED re-added from `agents_t110/BEAM_MEMBER_REGISTER.csv`: 111 rows 64.7645 + CB5 span 2 0.2960 (T-145,
merged) = **65.0605 m3 before and after**: this task moves nothing in it (west ring confirmed 0.7552 vs 0.7553). The
east ring stays outside the total (HELD 0.8997); CB10 stays CONFLICT (0.7438 schedule / 0.8925 drawn width, D-02).

The dome bays are where the freelancer's beam list differs most in kind (his 1F beam sheet, rows by mark):

| Dome-bay member | Register (m3) | Freelancer (m3) | Difference | Proposed verdict |
|---|---|---|---|---|
| B6, four spans 4.100 / 4.100 / 4.4222 / 4.3722 m (0.25 x 0.50) | 2.1243 | one row 4.37 m = 0.5463 | **+1.5780** | ENGINE_RIGHT: four B6 labels on p.5 (one per dome-bay side), hand 0.25 x 0.50 x 4.100 = 0.5125 each west |
| B25 6.8754 m (0.55 x 0.75) | 2.8361 | **no row** | **+2.8361** | ENGINE_RIGHT: B25 printed on p.5 between the bays, drawn 0.55 = schedule; hand 0.55 x 0.75 x 6.8754 = 2.8361 |
| CB13, two spans 3.000 + 3.150 m (0.30 x 0.50) | 0.9225 | GCB13 7.00 m = 1.0500 | -0.1275 | RULE_DIFFERENCE: he runs through the column and to centres; Urban basis is face to face |
| CB12, two spans 5.625 + 5.025 m (0.25 x 0.75) | 1.9969 | GCB12 13.00 m = 2.4375 | -0.4406 | RULE_DIFFERENCE: same length basis |
| West ring (B4) | 0.7552 | no row | +0.7552 | ENGINE_RIGHT (Q-44 A keeps it; hand above) |
| East ring | HELD 0.8997 | no row | not compared | UNRESOLVED (Q-61 C(3); designer D-28) |
| CB10 | CONFLICT 0.7438 / 0.8925 | GCB10 7.00 m x 0.25 = 0.8750 | not compared | UNRESOLVED (D-02) |
| **Dome bays, CALCULATED vs his comparable rows** | **8.6350** | **4.0338** | **+4.6012** | the freelancer under-measures the dome bays by 4.60 m3 (B25 missing, three B6 spans missing, ring missing) |

So the register total (65.06) and the freelancer (65.97) being close (-0.91, -1.4 %) hides +4.60 m3 the freelancer
leaves out in the dome bays alone: outside the dome bays his rows exceed the register's CALCULATED lines by 5.51 m3.
That is not a verdict: the register's CONFLICT (5.12 - 6.09 m3) and HELD (4.12 - 8.55 m3) lines sit outside its total,
and the other rows were not re-measured here.
His domes themselves sit in his stair + dome sheet (three shells 22.6 m2 x 0.10 x 3 = 6.78 m3), not in beams.

## 4. Owner manual method and drawing-derived method side by side

| Item | Manual (Q-44 hand estimate / freelancer) | Drawing-derived (this piece) | Difference |
|---|---|---|---|
| Ring per opening | centreline circle 3.14 x 4.62 = 14.5 m x 0.20 x 0.50 = about 1.45 m3 (full annulus 2.9042 m2 x 0.50 = 1.4521) | in-bay annulus 1.5105 / 1.7994 m2 x 0.50 = 0.7552 / 0.8997 (HELD) | -0.6969 / -0.5524 m3: the parts inside the framing beams, two columns and one slab panel, which are already measured there |
| Freelancer | no ring row; three dome shells in the stair + dome sheet | shells not in this task (S8.3 measured them; the owner says the chalet has no domes, skylights stay, Q-44 A) | not compared |

The Q-44 text itself said the 1.45 was "before taking off" what the ring shares; with Q-61 C(2) and Q-20 (no concrete
counted twice, as quoted in Q-62) the in-bay figure is the owner's rule applied, not a new rule: no owner question.

## 5. The 1F slab 0.37 m2 (`slab_1f_gap.py`)

- Hand 1F roof slab (T-139, 22 panels): 123.4786 m2 x 0.16 = 19.7566 m3. Freelancer: one lump 120.00 m2 x 0.16 = 19.200
  (his deduction 0.4 x 0.15 x 1.35 is written with count 0). Gap +3.4786 m2 (+0.5566 m3, +2.82 %).
- H1 (he left out the 8 dome-square corners, 3.8475 m2 in PANELS.csv): remainder **+0.3689 m2** (+0.0590 m3).
- H2: no drawn 1F piece or pair of pieces re-adds the whole +3.4786 within 0.01 m2.
- H3 (after H1): one natural trace: the **0.20 strip north of B23, east piece, 0.366 m2** (T-139 1F-043, held in the beam
  lane as BM-1F-033, D-05 / Q-61 C(5)): if he counted that strip as slab, the residual is 0.003 m2. (A second, mixed-sign
  pair also fits and is not a reading.)
- Sheets searched for anything else: p.5 (every panel, the strips round the roof edge, the stair well and the X box
  1F-036 3.240 m2, the sunken panel 1F-018 5.400 m2, the two dome bays), p.6 (the 2F roof repeats the dome outlines on a
  boundary layer: repeats, not slab), p.7 (dome detail: no slab piece). Nothing on the drawings explains the lump by
  itself: the lump has no breakdown.
- Proposal: **UNRESOLVED, immaterial** (0.369 m2, 0.059 m3, 0.30 % of the 1F slab, under the Lead's 0.5 % line, no rule
  gap). The 8 corners are slab on the drawing (between the beams, outside r_o): HAND_RIGHT if he left them out.
  No owner question.

## 6. Who is right (proposals for the checker)

- West ring 0.7552 m3: **ENGINE_RIGHT / HAND_RIGHT** (register = hand to 0.01 %); the full-annulus 1.4521 is wrong
  (double count 0.6969 m3, partition in section 2).
- East ring: **UNRESOLVED** (HELD, Q-61 C(3), designer D-28); candidate 0.8997, never the full 1.4521.
- Dome-bay framing vs freelancer: B6 x 3 spans and B25 **ENGINE_RIGHT** (+4.414 m3 he leaves out), CB13 / CB12
  **RULE_DIFFERENCE** (length basis), ring **ENGINE_RIGHT**.
- 1F slab 0.37 m2: **UNRESOLVED, immaterial** (section 5).
- Checker re-measure suggestion (one dome): east dome, CB12 side: seg(2.4111, 2.1611) - seg(2.2111, 2.1611) =
  0.3602 - 0.0312 = 0.3290 m2; ring in bay = 2.9042 - 3 x 0.2586 - 0.3290 = 1.7994 m2.

## 7. What we learned (every villa)

1. A ring drawn round an opening in a bay framed by straight beams owns only the annulus inside the bay. The drawing
   says so itself: the outer ring line stops at each beam face. Measure the ring from that bay, never from the full circle.
2. The ring can reach past a narrow framing member into the next panel (west dome: 0.124 m2 east of the 0.30 CB13). A
   full-circle ring would then double count with a slab panel as well as with beams and columns.
3. The opening circle (the skylight) also crosses the framing faces here: west 0.088 m2 into CB10 and 0.289 m2 into CB13
   (0.139 of it in the column), east 0.031 m2 into CB12. The beams are drawn continuous, so they stay whole; this is
   recorded as a drawing conflict (S8.3 CF-S8.3-08), not a deduction. If the designer said the opening cuts them, the
   framing members would lose about 0.044 (CB10) + 0.075 (CB13) + 0.023 (CB12) m3 plus a column top: immaterial, held as
   a note only.
4. A freelancer lump close to the hand total can hide a whole missing member: the dome bays alone are 4.60 m3 short in
   his list (B25 and three B6 spans).
5. Closed-form circle-segment arithmetic is exact and checkable by hand; the polygon method is only the cross-check.

## 8. Held / not measured (never 0)

- East ring concrete: HELD (candidate 0.8997 m3 at the B4 size), designer D-28.
- CB10 width: CONFLICT (D-02), its share of the ring overlap is inside whichever width is confirmed.
- Ring depth on the p.7 detail ("as per architect", drawn about 0.75): dropped with the dome under Q-44 A; no number taken.
- Ring rebar (B4 bars vs the p.7 ring bars): not measured here (beam steel T-149 / S8.3 sensitivity only).
- Formwork of the ring (both faces of the in-bay arcs): not measured (formwork task T-163).
- GF roof slab: no dome opening (no 4.42 m circle, no see-detail label). Its only ring is the B7 band round the
  pool-court void (two half rings, r 1.55 / 1.75 and 1.735 / 1.935, joined by two small fillet arcs). Checked this run
  with `arc_ends.py`: **all 18 arc ends lie on the four bay faces (B8 east, CB1 west, the south beam, B7 south) or join
  another arc of the void**, so the band is drawn in-bay like the domes and no register row (BM-GF-049 .. -052, the
  contested BM-GF-060 HELD) takes a full annulus. The bay re-adds: 1.700 x 2.7005 = 4.5909 m2 = void 3.690 + ring 0.666
  + corners 0.234 (T-127); a plain two-circle lens model without the fillets gives void 3.712 / ring 0.645 / corners
  0.2343 (corners equal; the 0.021 m2 difference is the fillet strip, which T-127 / T-139 already place in the
  contested piece). No change.
- The third (tower) dome: no structural drawing (S8.3 CF-S8.3-01), outside this task.
