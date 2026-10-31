# T-403 Plot boundary wall below N.G., component by component, run by run (development villa; method every villa)

Worker 1 (lane S), 2026-10-31. Research row: no engine, rule, knowledge, method, registry or candidate line changed;
nothing released. ERS applied: s.2.1 (physical element first, composite split), s.2.2 (printed > drawn > inherited),
s.2.3 (first principles), s.2.4 (freelancer reconciled to named causes), s.3 (physical vs line; range never a mid
value), s.4 (rules + tests), s.7 (lesson). Owner rules: Q-28 A PROVISIONAL (deduct a footing crossing only where the
elevations overlap), Q-21 C (the 1.50 m note is a minimum excavation, not the founding level), Q-65 C (block type HELD),
UP-QTY-STATUS-001. Built on merged T-253 (upper G.B band 44.07 m), T-065 / T-356 (lower band 91.94 m, range
5.6392 .. 11.0328 m3, pad split), T-392 (pool back), T-394 (column owns the beam joint), T-396 (masonry above N.G.).
Files cited by Drive folder and title, entities by DXF handle; no coordinate, image, client name or note text committed.

## 0. Read this run (Drive "Alsenan chalet project", read-only; private copies in .work/private only)

| Source | sha256 prefix | Read for |
|---|---|---|
| ST7757.pdf | 74da1523 | p.14 TYPICAL BOUNDARY WALL plan + section A-A (300 dpi); p.1 general notes; p.2 FOUNDATION PLAN; p.3 GROUND BEAMS PLAN + legend; p.9 notes 1-4 + footing schedule; p.10 beam schedule row B.W; p.13 typical footing / ground-beam details |
| ST7757 dxf.dxf | 9f9d1179 | S-BOUN 7FE / 7FC / 810 (upper G.B band), 1658 / 1659 (lower band), hatches 7FD / 7FB / 80F, footing outlines of PITS_T347.csv, layer-1 and S-COL.BON lines (guards) |
| freelancer RC and blockwork workbooks | (repo FREELANCER_RAW_ROWS.json) | 'الشناج المحيط' (footing sheet r32), 'شناج السور' (ground-beam sheet r15), 'السور' (blockwork r150): quantities only |

## 1. The physical element (ERS s.2.1) and what each sheet prints

ST p.14 section A-A, from the bottom: 10 cm plain-concrete blinding (projecting 10 beyond the pad on the inner side,
flush with the wall on the boundary side); a pad '(130x80x30)' whose '80' includes the 20 of the beam; the LOWER G.B
(width 20, bars 2 d14 + 3 d16 T&B, d8/20; depth NOT written; soffit = pad soffit); 'Brick Wall' with the dimension
'AS PER EXCAVATION DEPTH BELOW N.G. LEVEL'; the UPPER G.B (20 x '40', same bars), top at 'N.G. LEVEL'; the column
'(20 x 30) COLUMN 4 d14' above; 'PLAIN CONC.' 15 on the inside at N.G. The plan prints 'GROUND BEAM (20x40)', the
columns '(20x30) R.C COLUMNS 4 d14' at 'SEE ARCH PLAN', a pad beside each column. Section A-A is cut beside a
column through a pad. p.3 legend 'Typical Boundary Wall' = brick hatch; in the DXF the hatches S-HAT.BAT 7FD (AR-B816C),
7FB (AR-B816C) and 80F (AR-B816) fill exactly the bands 7FE, 7FC and 810: the typical section is referenced, by the
printed legend, on all five fence pieces. No run-specific boundary section is printed anywhere in the ST set (the arch
p.12 fence section is above N.G., T-396). ST p.1 note 2: the house's external ground beams on the neighbour side are cast
with black block above and below them, built from the foundation level. ST p.9 note 1: excavation not less than 1.5 m
below the existing plot level. p.10 schedule: 'B.W 20 x 60' (4 d16 bottom, 2 d14 top, 7 d8/m).

| Component | Printed / drawn | Owner trade / line | Result (fence band 44.07 m) |
|---|---|---|---|
| Upper G.B 20 x 40, top N.G. | p.14 plan + A-A; band 7FE / 7FC / 810 | STRUCTURE, `L-fb7a6431` (HELD BLOCKED_RFI) | gross **3.5256 m3** DRAWING-CONFIRMED; net HELD, AT_MOST 3.5256 (column joints, T-394) |
| Lower G.B 20 x d on blinding | A-A (d unwritten); foundation band 1658 / 1659; p.10 B.W 20 x 60 | STRUCTURE, inside `L-6290a9f3` (HELD) | band solid **3.3976 .. 5.2884 m3** (fence share); line low end NOT ESTABLISHED (pad split) |
| Pads 1.30 x 0.80 x 0.30 | A-A / plan; count 'SEE ARCH PLAN', none drawn | STRUCTURE: **MISSING** | HELD: 0.312 m3 gross / 0.234 net of the 0.078 beam share, per pad; n not printed (M4) |
| Blinding under pads / beam | A-A 0.10 under the pad (0.90 across); between pads not drawn | STRUCTURE: **MISSING** | HELD: per pad 0.090 x [1.30 .. 1.50 along] = 0.117 .. 0.135 m3; under the beam between pads not drawn |
| Masonry below N.G. 0.20 | A-A 'Brick Wall'; black block on the neighbour runs (p.1 n.2) | BOUNDARY WORKS / MASONRY: **MISSING** | plane **AT_LEAST 17.628 m2**, value HELD (formation, d); net HELD (columns) |
| Columns 20 x 30 below N.G. | A-A (above), plan 'SEE ARCH PLAN' | STRUCTURE (CONC.COLUMN, M4) | HELD (count) |
| Excavation / backfill | p.14 'AS PER EXCAVATION DEPTH'; p.9 n.1 | EARTHWORKS (T-347 Z1-TRENCH-BOUNDARY, HELD) | not counted again |
| Plain concrete 15 at N.G. (inside) | A-A 'PLAIN CONC.' | EXTERNAL WORKS paving | named, not measured |

## 2. Runs (acceptance a; R-T403-1 / -2)

The lower band (axis 91.94 m, `t403_extract.py`) split along its axis by the upper G.B footprint (sheet translation
closed on the east edge to 0.000 mm):

| Run | Axis m | Section and why | Footing crossings m | Free m | Lower G.B band solid m3 | Upper G.B gross m3 | Masonry plane AT_LEAST m2 |
|---|---|---|---|---|---|---|---|
| F-NORTH (neighbour) | 31.37 | typical (legend hatch 7FD) | 0 | 31.37 | 2.5096 .. 3.7644 | 2.5096 | 12.548 |
| F-STREET | 8.10 | typical (7FD) | 0.20 (F:1668) | 7.90 | 0.6320 .. 0.9720 | 0.6480 | 3.240 |
| F-SEA-N | 2.25 | typical (7FD) | 0 | 2.25 | 0.1800 .. 0.2700 | 0.1800 | 0.900 |
| F-SEA-S | 1.15 | typical (7FB) | **1.15 (whole run inside F8 1B24)** | 0.00 | 0.0000 .. 0.1380 | 0.0920 | 0.460 |
| F-PASSAGE (neighbour) | 1.20 | typical (80F) | 0.25 (F:166A) | 0.95 | 0.0760 .. 0.1440 | 0.0960 | 0.480 |
| **Fence total** | **44.07** | | **1.60** | **42.47** | **3.3976 .. 5.2884** | **3.5256** | **17.628** |

Allocation as T-253 / T-396 (corner squares once, in the north run); conservation: 44.07 = the upper G.B by area
(7FE 41.72 + 7FC 1.15 + 810 1.20). The typical section governs every fence run below N.G. (printed legend); the run
differences are not section differences but crossings: the sea-south run lies wholly over house footing F8 and the
passage and street ends over the two 'F' footings, where the band and footing levels are not printed (Q-28).

Rest of the same lower band (not fence; named, never taken into the fence): POOL back 3.50 m (0.50 over F8;
0.2400 .. 0.4200 m3), HOUSE south 29.972 m (13.702 crossings; 1.3016 .. 3.5966), HOUSE street 6.599 m (1.399;
0.4160 .. 0.7919), HOUSE sea 7.799 m (4.249; 0.2840 .. 0.9359). Sum 91.94 m, free 70.49 m, 5.6392 .. 11.0328 m3 =
T-356 reproduced exactly; owner method A 8.4588 m3 = 5.0964 (fence) + 0.3600 (pool) + 3.0024 (house).

Lower-band ranges: low = free x 0.20 x 0.40, high = drawn x 0.20 x 0.60 (two printed readings of the depth: the p.14
plan '(20x40)' with A-A's identical G.B bars, vs the p.10 'B.W 20 x 60' row; a range, never a mid value).

## 3. Masonry below N.G. height (R-T403-4)

h = formation depth - blinding 0.10 - lower G.B depth (0.40 | 0.60) - upper G.B 0.40. The formation depth is printed
only as a minimum (p.9 note 1: >= 1.50 m below the existing plot level, taken as N.G. +-0.00 per T-253 / T-347; A-A
ties the brick to that excavation depth). So h >= 1.50 - 0.10 - 0.60 - 0.40 = **0.40 m** (0.60 m if the beam is 0.40),
no upper bound printed: plane **AT_LEAST 44.07 x 0.40 = 17.628 m2**, value HELD. Over the 1.60 m of footing crossings
the bound still holds (F8 0.50 and F 0.30 are not thicker than the 0.60 beam reading). The house footing depth was not
used (refused by rule). Net = plane - n x 0.30 x h: HELD (n). Material: black block on F-NORTH and F-PASSAGE
(31.37 + 1.20 = 32.57 m, p.1 note 2); F-STREET / F-SEA 11.50 m 'Brick Wall' only: type HELD (Q-65 C).

## 4. The two existing HELD lines (acceptance b; never counted again)

- `L-fb7a6431fede62e93fd5` STR.CONC.GROUND_BEAM (upper G.B): KEEP HELD; the reason restated in units: gross 44.07 x
  0.20 x 0.40 = 3.5256 m3 DRAWING-CONFIRMED; each boundary column takes its joint 0.20 x 0.30 x 0.40 = 0.024 m3 (beam
  stops at the column faces, T-394); count not printed and none drawn (S-COL.BON lines inside the band: 0; layer-1 house
  G.B faces inside the band: 0.000 mm). Proposal: show bounded_high 3.5256, value blank.
- `L-6290a9f3d93f38cd46d6` STR.CONC.BOUNDARY_WALL (whole lower band): KEEP HELD (T-356 range unchanged); proposal: split
  the line by owner class (FENCE 44.07 / POOL 3.50 / HOUSE 44.37 m) with the ranges of s.2, so a boundary-works group
  and the house never share one figure; low end NOT ESTABLISHED (0.078 m3 per pad, n not printed).
Nothing of this task enters either line twice: the new components (pads, blinding, masonry below N.G.) are separate
MISSING items.

## 5. Overlaps (acceptance c; all 0.000)

Pool wall: the 3.50 m pool back is its own run, outside the fence runs (0.000 m in the fence). House G.B: 0.000 mm of
layer-1 faces inside the upper G.B band. T-396 plane: above N.G. vs this task below N.G. (the upper G.B top is N.G.):
0.000 m2. Footing crossings: the low end deducts them, the high end does not (Q-28); the footings themselves stay in
their own lines. Column lines inside the band: 0.

## 6. Owner manual method and drawing-derived method side by side

| Component | Owner manual method | Drawing-derived (this task) | Candidate V3.0.32 | Freelancer |
|---|---|---|---|---|
| Lower band, fence share | Q-28 A: free 42.47 x 0.20 x 0.60 = 5.0964 PROVISIONAL, not released | 3.3976 .. 5.2884 HELD (low end NOT ESTABLISHED) | inside L-6290a9f3 HELD | inside his 71.7 m perimeter row |
| Lower band, whole | Q-28 A 8.4588 PROVISIONAL | 5.6392 .. 11.0328 HELD | HELD blank (downgrade) | 71.7 x 0.20 x 0.60 = 8.604 |
| Upper G.B | none beyond the print | 3.5256 gross, net HELD (AT_MOST) | HELD BLOCKED_RFI | 42 x 0.30 x 0.60 = 7.560 |
| Pads | none | HELD (n) | none (MISSING) | none |
| Masonry below N.G. | no owner rule (blockwork: run x height) | AT_LEAST 17.628 m2, HELD | none (MISSING) | none (his 74.40 m2 is above N.G.) |

## 7. Freelancer (quantities only; acceptance d)

- Upper G.B: his 7.560 vs our gross 3.5256 m3: **-4.0344 m3 (-53.4 %)**, closed with 0.0000 residual: width printed
  0.20 vs his 0.30 **-2.6442** (ENGINE_RIGHT: '20' in A-A and the 0.20 band); depth printed 0.40 vs his 0.60
  **-1.7628** (ENGINE_RIGHT: '40' in A-A, '(20x40)' on the plan); length 44.07 vs 42.0 **+0.3726** at his section
  (ENGINE_RIGHT for 2.35 m: 7FC 1.15 + 810 1.20 drawn and hatched as boundary wall, not in his 42; his 42 vs the 7FE
  axis 41.72: +0.28 m UNRESOLVED, a typed figure close to the 7FE outer run 42.12).
- Lower band: his 8.604 vs owner method A 8.4588: -0.1452 m3 (-1.7 %), all length (70.49 vs 71.7 m, -1.21 m:
  UNRESOLVED, T-065: between the inner and outer free lengths); section 0.60 = one of the two printed readings
  (RULE_DIFFERENCE pending RFI-S03 / Q-28). He does not split fence and house.
- Pads, blinding, masonry below N.G., boundary columns: absent from his workbooks; ours HELD (no comparison number).
  Verdict on existence: ENGINE_RIGHT (drawn in A-A); on quantity UNRESOLVED (HELD).

## 8. Finding beyond the fence band (for the register; not measured)

ST p.1 note 2 puts black block BELOW the house's external ground beams on the neighbour side, from the foundation level,
and the foundation plan carries the same 0.20 band there: on the south (neighbour) side the house G.B stands on block
over the lower band for **29.97 m** of axis (HOUSE_S). That masonry is in no line either (MISSING), height HELD (house
G.B soffit by mark, D-34; formation). On the street and sea house sides (6.60 + 7.80 m) the band is drawn but nothing
is printed between it and the house G.B: designer fact.

## 9. Designer facts for the RFI register (consultant items; no owner question)

1. Lower boundary G.B depth: 20 x 40 (as the plan label and A-A bars) or the B.W 20 x 60 row; is B.W this member?
   (fence share 3.3976 .. 5.2884 m3; whole band 5.6392 .. 11.0328).
2. Formation (excavation) level of the boundary wall below N.G. (masonry >= 17.628 m2 on the fence, open upward).
3. Boundary columns / pads: positions and count (0.312 m3 pad, 0.024 m3 upper joint, 0.30 x h of block per column).
4. Pad / beam share owner (0.078 m3 per pad) and blinding under the lower beam between pads (not drawn).
5. Band vs house footing levels at F8 (the whole sea-south run 1.15 m), F:1668, F:166A (Q-28 condition 2).
6. Street and sea house sides: what stands between the lower band and the house G.B.

## 10. Rules, tests, lessons, lane I proposal

Rules R-T403-1 .. -7 in `t403_rules.py` (research, every villa). Tests `tests/t403_boundary_below_ng` (15): Villa Q
hand fixture (rear 25.00 m typical with pads and 6 printed columns; side 7.00 m with its own section and a same-level
footing crossing: upper 2.368 m3, lower 3.665 m3, pads 1.512 m3, masonry plane 26.300 / net 24.320 m2), run-order
invariance; adverse: typical section on a run with its own section, formation from the house footings, unsourced
formation, unknown columns summed as 0, mm as m, a house run as fence, a missing run, two depths collapsed, unprinted
crossing levels, beams deeper than the formation; the development villa outputs reproduce and pin.

Lessons-register row proposed: | 2026-10-31 | The boundary wall below N.G. (pads, blinding, 44 m of masonry between
the beams, and 30 m of block under the house G.B on the neighbour side) sat in no line; the lower band was one figure
for fence and house alike | the boundary concrete was handled as two beam lines and the wall between them as 'depth
not printed' | a boundary wall below ground is enumerated component by component and its foundation band split by owner
run (fence / pool / house), each component bound to one line or named MISSING; a printed general minimum (excavation
>= 1.50 m) gives an AT_LEAST bound, never a value, and never the house footing depth (every villa; provenance T-403) |
tests/t403_boundary_below_ng | PROPOSED |

Lane I proposal (no candidate line here): split `L-6290a9f3` by owner class with the ranges of s.2; set the bounded
high 3.5256 on `L-fb7a6431`; add HELD blank MISSING lines: BOUNDARY PADS (unit 0.312 / 0.234 m3, n HELD), BOUNDARY
BLINDING, BOUNDARY MASONRY BELOW N.G. (plane AT_LEAST 17.628 m2) and HOUSE-SIDE BLOCK BELOW G.B (neighbour side,
29.97 m, height HELD).

Reproduce: `python3 -I research/agents_t403/t403_extract.py "<private>/ST7757.dxf"` (checks the committed input),
`python3 -I research/agents_t403/t403_alsenan.py` (checks the summary).
