# T-396 Boundary fence masonry above natural ground, run by run (development villa; method every villa)

Worker 2 (lane A), 2026-10-31, run session_01E6cPnb6vTzXk6DkwhSN2Aa. Research row: no engine, rule, knowledge, method,
registry or candidate line changed; nothing released. ERS read and applied: s.2.1 (physical element first, composite
split), s.2.2 (evidence hierarchy: printed > drawn > inherited), s.2.3 (first principles), s.2.4 (freelancer reconciled in
m and m2 to named causes), s.3 (plane vs block net vs procurement kept apart; build before deduct), s.4 (rule + test),
s.7 (lesson). Owner rules: Q-65 C (fence material HELD, provisional alternatives for comparison only), Q-63 C (sea-side
element HELD: material, height, structure, gate), UP-QTY-STATUS-001, WORKFLOW_CONTROLS s.4 / s.5. Built on merged T-253
(upper G.B band, Checker own 0.0 %), T-361 (fence lines, gates), T-346 (passage closure), T-356 (lower band), T-279 /
T-333 (house blockwork lines) and READY T-392 (pool fourth side split, Lead ruling 2026-10-31 12:30). Files cited by Drive
folder and title, entities by DXF handle; no coordinates, image, client name or note text is committed.

## 0. What was read this run (Drive "Alsenan chalet project", read-only; private copies in .work/private only)

| Source | sha256 (prefix) | Read for |
|---|---|---|
| P7757_DXF_COMPRESSED.zip -> P7757.dxf | ab54dd55 | GF plan fence bands (layer 5), gate gap (HIDDEN), sea column 2F96; NW / SE elevation fence ends + '+-0.00' level blocks; layer-1 wall guard; column census in the bands |
| Alsenan_Architectural_P7757_Pages_11-12.pdf | 9c72175c | p.12 FENCE PLAN / FENCE ELEVATION / SECTION (400 dpi crops, by eye, nothing scaled); p.11 SECTION B-B (court) |
| ST7757.pdf | 74da1523 | p.14 TYPICAL BOUNDARY WALL plan + section A-A (400 dpi); p.1 notes |
| freelancer blockwork workbook (sheet 'الكميات') | 873308bb | the fence row (quantities only) |

## 1. The physical element (ERS s.2.1)

A boundary wall on this plot is a composite element, split by component, each with one owner:

| Component | Where it is drawn | Owner trade / line | This task |
|---|---|---|---|
| Lower G.B (0.20 wide, depth not written) on 130 x 80 x 30 pads | ST p.14 A-A; foundation band S-BOUN | CONC.GROUND, L-6290a9f3 (HELD) | no |
| Masonry BELOW N.G. between the two beams ("Brick Wall ... AS PER EXCAVATION DEPTH BELOW N.G. LEVEL") | ST p.14 A-A; ST p.1 note 2 (neighbour side: black block from the foundation level) | **in NO line: MISSING** | named, HELD (s.4) |
| Upper G.B 20 x 40, top at N.G. | ST p.14 plan + A-A | CONC.GROUND, L-fb7a6431 (HELD BLOCKED_RFI) | conservation only |
| Columns 20 x 30 R.C. 4 d14 at 'SEE ARCH PLAN' | ST p.14 plan / A-A (break line, no height) | CONC.COLUMN (count M4 not printed) | deducted from the block net (HELD) |
| **Masonry ABOVE N.G.** (the fence wall) | arch GF plan layer-5 bands; p.12 section / elevation | **in NO line: MISSING -> BOUNDARY WORKS** | **measured here** |
| Gate openings G-01 2.50 / G-02 1.00 | arch plan; p.12; elevations | EXTERNAL WORKS (T-361) | inside the runs, never wall |
| X railing in the street-fence dip | p.12 FENCE ELEVATION | MET guard RL-10 (HELD, V3.0.30) | the profile cut of the street wall |
| Finish faces (plaster / paint both sides, top, ends) | - | OTHER_TRADE (Q-65 C) | HELD, not measured |

## 2. Heights: what is printed and what is only drawn (ERS s.2.2)

- **Printed (Pages_11-12 p.12, SECTION 1:100):** the fence wall stands '265' above the lower ground line, split '50'
  (lower band, drawn in the same cross-hatch as the ground / paving bands on both sides) + '215' (upper part, outline only).
  No level is printed on the section, and the fence plan carries no cut mark. The fence elevation on the same sheet draws
  the street solid wall with a curved dip filled by an X railing (dip profile not dimensioned) and the 2.50 gate with only
  a ground strip.
- **Drawn, corroborating (P7757.dxf elevations):** the 0.20 fence end is drawn in both the NW elevation (lines 27EA /
  27EB, top 27F3) and the SE elevation (23DD / 23DF, top 23E6) with its top **2.650 m above the '+-0.00' level block**
  (2A43 / 2439) and 2.500 m above the court line '+0.15' (27F1 / 23E5). Section B-B (p.11) draws a line beyond the cut
  across the whole court whose position is consistent with that top (by eye, proportion only, not a measurement).
- **Datum:** ST p.14 A-A puts the upper G.B top at 'N.G. LEVEL'; T-253 (Checker re-read) settled N.G. = '+-0.00' at the
  plot. So the fence rises **2.65 m above N.G.**, the wall plane standing on the G.B top.
- **Not settled:** the material of the lower '50' band. The arch section hatches it like the paving; the structural set
  shows above N.G. only the column (break line) and no plinth. Block (block height 2.65) or a concrete plinth (block
  2.15 + 0.50 plinth) are both open: 0.50 x 36.97 = **18.485 m2** of block on the north and street runs (0.50 x 0.20 x
  36.97 = 3.697 m3 if concrete). Never chosen; designer fact proposed (s.7).

## 3. Run table (R-T396-1; corner squares once, in the north run, as the G.B band)

| Run | DXF (arch GF plan, layer 5) | Run m | Gates m | Excluded m | Solid m | t | Height above N.G. | Wall plane m2 | Block net m2 |
|---|---|---|---|---|---|---|---|---|---|
| F-NORTH (upper neighbour) | outer 99 + 98 = 31.370 (inner 13A 30.970 + BA) | 31.370 (both corners) | 0 | 0 | **31.370** | 0.20 | **2.65 PRINTED** (p.12) + drawn ends | **83.1305 DRAWING-CONFIRMED** | **HELD, at most 83.1305** (columns M4, lower 0.50 band) |
| F-STREET | 10F 8.300 = gap 110 (HIDDEN) 2.500 + solid to cap 10B | 8.100 (corner to north) | 2.500 (G-01) | 0 | **5.600** (= inner leg 13A 5.600) | 0.20 | **2.65 PRINTED** | **14.840 DRAWING-CONFIRMED** | **HELD, at most 14.840** (columns, lower band, undimensioned dip) |
| F-SEA (Q-63 C element) | 2F96 face -> 8D 0.2316 + 8D 5.1684 + 8E 1.700 = 7.100 | 6.900 (corner to north) | 1.000 (G-02) | 3.500 pool back (POOL wall) | **2.400** (0.2316 + 0.9184 S; 0.75 N + 0.20 + 0.1994 + 0.1006) | 0.20 | drawn 2.65 (gate-zone lines 2.50 over the court), **not printed; element HELD by the owner** | **HELD** (2.400 x 2.65 = 6.360 comparison only) | HELD |
| F-LOWER passage closure | 86 / 106 1.200, 0.20 apart | 1.200 | 0 | 0 | **1.200** | 0.20 | **none printed** (closure partly under the GF roof +5.50; T-361 E-02 stop-end HELD) | **HELD** | HELD |
| **Total** | | **47.570 -> band 44.07** | 3.500 | 3.500 | **40.570** | | | **97.9705 DC + 2 runs HELD** | **all HELD** |

Conservation: run lengths net of pool back = 31.37 + 8.10 + 3.40 + 1.20 = **44.07 m = the Checker-verified T-253 band**
(7FE#1 31.37, 7FE#2 8.10, 7FE#3 2.25 + 7FC#1 1.15, 810#1 1.20); sea S part 0.2316 + 0.9184 = 1.15 = 7FC#1; sea N part
0.75 + 1.70 - 0.20 = 2.25 = 7FE#3; 0.9184 + 3.50 + 0.75 = 5.1684 = 8D (T-392 split reproduced from the verified runs).

Block net terms (R-T396-3): each boundary column takes 0.30 x 2.65 = **0.795 m2** of block face; no column is drawn in
any fence band (S-COL.BON census 0 on all four runs; ST p.14 'SEE ARCH PLAN'), so n is unknown and the net stays HELD
with AT_MOST = the plane, never the plane. Block TYPE, count and mortar: HELD (Q-65 C) on every run; the wall's 0.20
thickness is drawn (bands 0.20 apart; ST '20').

## 4. Masonry below N.G. (separate component, MISSING)

Length = the band, 44.07 m (continuous under the gates), 0.20 thick; height = from the lower G.B top to the upper G.B
soffit (N.G. - 0.40): **not printed** ('AS PER EXCAVATION DEPTH BELOW N.G. LEVEL'; the existing ground is printed only at
the plot corners, T-357) -> **HELD blank**. Material: black block on the neighbour sides by ST p.1 note 2 (north 31.37 +
lower 1.20 = 32.57 m, DRAWING-CONFIRMED material); street 8.10 and sea 3.40 m not printed. In no candidate line (the
concrete lines carry only the two beams; the 28 masonry lines are storey walls): a missing category beside the fence.

## 5. Cross-trade (acceptance c): 0 overlaps

CROSS_TRADE_T396.csv: layer-1 wall lines on the 8 fence faces 0 (DXF guard, parallel within 0.25 m); pool wall 0 (the
3.50 m pool back excluded by name; nothing is drawn above the rim in front of the pool drum); house facade 0 (boundary
faces are not facade, register 2026-10-30); T-279 / register v4 house blockwork 0 (GF-W15 7.100 is the entrance front,
not the sea line); boundary G.B lines 0 (the wall stands on the beam; band conserved); RL-10 railing 0 (it fills the
street dip); gates 0 (inside their runs). Register rows proposed (Lead): see s.8.

## 6. Freelancer (quantities only; acceptance d)

His row 'السور' (blockwork workbook, his 15 cm section): 1 x 37.20 x 2.00 = **74.40 m2**. Ours on his scope (north +
street solid, the only runs he has): 36.97 m x 2.65 = **97.9705 m2** wall plane. Difference **-23.5705 m2** (his figure is 24.1 % below our plane),
closed to named causes with 0.0000 m2 residual:

| Cause | m | m2 | Verdict proposal |
|---|---|---|---|
| corner square counted in both runs (his 31.37 + 5.80 outer; the 0.20 corner is in both) | +0.20 | +0.40 | ENGINE_RIGHT (R-T396-1) |
| his 37.20 vs 31.37 + 5.80 = 37.17 | +0.03 | +0.06 | UNRESOLVED (typed figure, no formula) |
| height 2.00 vs printed 2.65 (p.12 section, elevation ends drawn to 2.65) | -0.65 | -24.0305 | ENGINE_RIGHT on the plane (his 2.00 matches no printed or drawn dimension) |
| thickness: his 15 cm section vs drawn 0.20 | - | 0 (m2) | FREELANCER_WRONG (affects block type / count, not m2) |
| no sea element (Q-63 C), no passage closure, no below-N.G. masonry, no dip / column deduction | - | not compared | RULE_DIFFERENCE (scope) / HELD |

Block net: no verdict while the column count, the 0.50 band material and the dip are open (UNRESOLVED; ours HELD at most
97.9705 m2, his 74.40). Note: 2.65 - 0.50 - 0.15 = 2.00 reproduces his figure arithmetically, but no drawing supports
measuring block from a plinth top relative to the court; recorded as a coincidence, not a cause.

## 7. Designer facts (rfi/B row proposals; nothing sent)

1. The p.12 fence SECTION ('265' = '50' + '215'): which runs does it cut (street only, or every boundary wall), and is
   the lower '50' block, a concrete plinth or a finish band? (18.485 m2 block / 3.697 m3 concrete at stake.)
2. Boundary columns 20 x 30 'SEE ARCH PLAN': positions and count (0.795 m2 of block per column; already M4).
3. Street fence dip with X railing: profile (depth, chord) - the block deduction and the RL-10 railing length both wait on it.
4. Passage closure 1.20 m on the lower-neighbour side: top of wall (to the GF roof soffit, or the fence height).
5. Sea element (Q-63 C, RFI-B-A11): the elevations draw its gate-zone top 2.50 above the court (+2.65), the layer-D
   rectangles 39D (0.632) / 39E (0.447) at its ends: piers or wall ends?
6. Masonry below N.G.: the lower G.B level / excavation depth (with Q-28 / RFI-S03).

## 8. Rules, tests, register rows, lesson

Rules R-T396-1 .. -5 in `boundary_fence.py` (research, every villa): runs on the band with corners once and gates /
other owners' parts excluded by name; height only from a printed dimension of the wall itself (drawn geometry
corroborates, an owner-held element stays HELD); plane vs block net with every unknown term HELD at-most; type / count
HELD; below-N.G. masonry its own component; freelancer rows mapped by length, a corner counted twice named.

Tests `tests/t396_boundary_fence` (12): Villa K hand fixture (L-shaped plot fence, 20.00 m + 12.00 m with a 3.50 gate, 3
printed columns, height 2.40: plane 67.920 m2, block 65.760 m2; concrete plinth 0.30 -> 40.560 on A), mirror / order
invariance; adverse: gate as wall / gate outside its run / zero gate, invented / unsourced / drawn-only height, owner-held
element with a printed height, pool back in two lines, mm and cm as m, missing run, HELD summed as 0, unknown columns
released, undimensioned dip released, column faces larger than the plane, freelancer corner double count; development
villa committed outputs reproduce and pinned; no coordinates in the committed input.

Register rows proposed (Lead): (1) BOUNDARY FENCE ABOVE N.G.: 4 runs 31.37 / 5.60 (+2.50 gate) / 2.40 (+1.00 gate, pool
back 3.50 excluded) / 1.20 m, owner BOUNDARY WORKS, plane 97.9705 m2 DC on north + street, block net HELD; (2) BOUNDARY
MASONRY BELOW N.G.: 44.07 m x 0.20, height HELD, black block on the neighbour sides (ST p.1 n.2), owner BOUNDARY WORKS
(or MASONRY), MISSING; (3) the lower '50' band of the fence: material UNRESOLVED, owner open (BOUNDARY WORKS if block,
CONC if plinth), never both.

Lane I integration proposal (no candidate line here): add BOUNDARY WORKS lines per run: wall plane m2 (north 83.1305,
street 14.840 DRAWING-CONFIRMED; sea, passage HELD blank), block net m2 HELD blank with the at-most beside, block type /
count HELD (Q-65 C), and one HELD blank line for the below-N.G. masonry; bind the railing RL-10 and gates G-01 / G-02
by id, never as wall.

Lessons-register row proposed: | 2026-10-31 | The boundary fence (97.97 m2 of wall plane, plus the masonry between the
two boundary beams) sat in no masonry line through 31 candidate versions; the freelancer's 74.40 m2 was the only figure
| the fence was handled as a material question (Q-65 C) and its concrete as beam lines; the wall between and above the
beams was never defined as a physical element with its own components | a boundary wall is enumerated component by
component (lower beam, masonry below N.G., upper beam, columns, masonry above N.G., gates, infill, finishes), each bound
to one line or named MISSING; a held material holds the type and count, never the geometry (every villa; provenance
T-396) | tests/t396_boundary_fence (gate as wall, invented height, pool back twice, held as 0) | PROPOSED |

## 9. Missing / uncertain

- Block net on every run (columns, lower band, dip); the sea element and the passage closure heights; below-N.G. depth.
- The p.12 section is unlocated: its use on the north run rests on it being the fence sheet's only section, with the
  north fence end drawn to the same 2.65 in two elevations; no long elevation of the north fence exists, so a profile
  change along its 31.37 m would not be visible on any sheet (residual risk named, designer fact 1).
- The 0.03 m in the freelancer's typed length.

Reproduce: `python3 -I research/agents_t396/t396_extract.py <P7757.dxf>` (checks the committed input; `--write`
rebuilds), `python3 -I research/agents_t396/t396_alsenan.py --check`.
