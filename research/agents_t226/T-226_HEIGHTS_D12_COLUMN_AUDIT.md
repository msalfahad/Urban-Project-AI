# T-226: blockwork resolution 2/4: wall heights from the drawn members, D-12, column footprints, junction audit

Worker 2, 2026-10-23 16:45 - 17:40 UTC, lane A, gate 2 (owner programme BLOCKWORK_RESOLUTION_PROGRAMME.md, 15:45).
Base: working head 48e6f08a (T-225 merged). Development villa; not an accuracy claim. Released default unchanged
(V2.9 + route G). Nothing here is VERIFIED: every closed piece is SOURCE-SUPPORTED PENDING INDEPENDENT CHECK.
ERS: read; s.2 steps 1-4 (define, evidence hierarchy, reconstruct from the drawing, reconcile in units), s.3 (a width
conflict and a depth are different quantities; build before deduct: column stretch is concrete), s.4 (rule + test).

## 1. The physical element and the method

A height piece is a stretch of block wall under ONE member (beam, slab or nothing). Owner Q-60 A: block height =
storey (slab top to slab top: GF 4.50, 1F 4.20, 2F 4.20 m, T-112) - depth of what sits on that stretch. The merged
T-108 r2 pipeline (MASONRY_AREA_V1 r2) was re-run unchanged (its output equals T108_BY_WALL.csv byte for byte) and
then with ONLY the pieces closed here rewritten to their printed depth; the T-225 builder (which reproduces register
v1 byte for byte) forms the rows. `register_delta.csv` holds the changed rows in the register v1 format; v1 is not
edited (T-228 builds v2 from the deltas).

Drawings read this run (Drive "Alsenan chalet project"; cited by title only): ST7757 dxf.dxf (sha 9f9d1179):
schedule cells, roof-slab plans round every held piece (labels, band edges, column boxes), rendered locally;
P7757.dxf (sha ab54dd55) wall bands mapped into the ST frame with the T-108 translations (GF-W36 falls exactly on its
band, 1F-W05 inside the CB10 band); p7757_arch_sheet10.pdf (SECTION A-A) and Alsenan_Architectural_P7757_Pages_11-12.pdf
p.1 (SECTION B-B; its cut line maps onto the 1F CB10 end; A-A and B-B cut neither CB2 nor B6). Nothing of them is
in the repository.

## 2. Rule UP-MAS-HPIECE-001 (proposed; any villa) and the result per piece (PIECE_RESOLUTION.csv)

R1 nothing drawn above -> HELD; R2 drawn member with no mark -> HELD, labelled neighbours give a BOUND only (Q-61 C(4));
R3 two marks with different depths -> CONFLICT range (Q-61 C(2)); **R4 one mark, every printed depth agrees -> the
depth closes the piece even when the member's WIDTH is in CONFLICT** (schedule vs drawn outline, Q-61 C(1)): the
masonry height uses the depth only; the width conflict stays open on the concrete line and is carried as a
dependency; R5 printed depths disagree -> CONFLICT; R6 a drawing that does not outline the member (an architectural section
hatching masonry and concrete alike) is not a depth source; **R7 a slab-plan face that merges a beam band and the
column under it is split by the column-BELOW outline**: inside it = column (no block), beside it under the band = that
beam (R4), under neither = R1.

| Wall | Piece (member) | m | Evidence (ST7757 dxf.dxf) | Rule | Result |
|---|---|---|---|---|---|
| GF-W10 | CB2 BM-GF-055, 2 spans | 3.46 + 3.36 | CB2 schedule cells B 20 / H 50, spans 4.0 / 4.0 (read this run); band 0.25 drawn = width conflict only; no section cuts it | R4 | h 4.50 - 0.50 = **4.00** |
| 1F-W05 | CB10 BM-1F-031, 2 spans | 3.68 + 2.30 | CB10 schedule B 25 / H 50, spans 3.0 / 4.1; band 0.30 drawn (D-02 width only); the 0.20 wall lies inside the band; section B-B cuts the 1F end walls and draws a solid head band 0.49 .. 0.51 m from the slab top at both ends (scaled at 300 dpi, scale checked on the 4.20 m storey; corroboration, not the source) | R4 | h 4.20 - 0.50 = **3.70** |
| 1F-W11 | CB10 west end | 0.12 | wall end 0.10 m inside the CB10 band | R4 | 3.70 |
| 1F-W16 | B6 BM-1F-030 crossing | 0.26 | B6 schedule 25 / 50; drawn 0.20 = width only | R4 | 3.70 |
| GF-W03 | CB3 / 'B3 (With Stair)' | 2.64 | CB3 H 75 and B3 H 40 on one span | R3 | HELD, CONFLICT 9.900 .. 10.824 m2 (designer D-03) |
| 1F-W04 | unlabelled, B23 face -> column | 0.80 | re-read: no text on the span; B2 only on the north span | R2 | HELD, bound 3.040 m2 at the one neighbour B2 (not a value) |
| 2F-W02 | unlabelled east span | 0.92 | B3 west / B8 middle printed, none here | R2 | HELD, 3.174 .. 3.496 m2 |
| 2F-W03 | two unlabelled verticals below the columns | 0.26 + 0.26 | B1 on the spans above only | R2 | HELD, 0.988 + 0.988 m2 at B1 |
| 2F-W05 | same vertical | 1.24 | same | R2 | HELD, 4.712 m2 at B1 |
| 2F-W07 | west band south span | 2.94 | B15 (H 120) on the north span only | R2 | HELD, 8.820 .. 11.172 m2 |
| GF-W36 | 0.20 band between the CB6 column and the B7 arc | 0.50 | closed by a line at the arc start, collinear with B4, no text of its own; **in no T-110 beam record** | R2 | HELD, 1.875 .. 2.000 m2 (B4 H 50 / B7 H 75) |
| GF-W07 | east end, between the column face and the CB1 band edge | 0.12 | CB1 schedule B 35 / H 75 (spans 7.5 / 5.7); the column BELOW CB1 is 200 x 500 (T-229 merged: CB1 wider than its column) = the architectural column outline; T-139 had merged band + column into one 'BEAM_OR_COLUMN' face | R7 -> R4 | h 4.50 - 0.75 = **3.75** |
| 1F-W11, W13 (2), W17, W18, W24 | under the open dome rings | 4.01, 2.98, 1.40, 0.44, 0.44, 1.02 | T-139 faces | R1 | HELD: T-227 (d), not this package |

The previous cause 'no member drawn above' was correct only for the dome pieces: GF-W36 and GF-W07 have members drawn
above them (an unlabelled beam piece; the CB1 band beside a narrower column).

## 3. Before / after (register delta; m2, SOURCE-SUPPORTED PENDING INDEPENDENT CHECK)

| Wall | Type / t | Gross before | Gross after | Net before | Net after | Still held on |
|---|---|---|---|---|---|---|
| GF-W10 | WHITE 0.20 | 23.543 HELD (6.825 m held) | **50.845** source-supported | HELD | HELD | W05 / W06 / W07 heads (T-227 e) |
| 1F-W05 | WHITE 0.20 | 0.771 HELD (6.076 m held) | **23.254** | HELD | **19.334** (m3 3.867) | nothing (Checker re-measure) |
| 1F-W11 | BLACK 0.15 | 0.444 HELD | 0.888 HELD | HELD | HELD | dome piece 4.01 m (T-227 d) |
| 1F-W16 | BLACK 0.15 | 20.846 HELD | **21.808** | HELD | HELD | A-1F-01 height (T-227 / T-222) |
| GF-W07 | WHITE 0.20 | 4.018 HELD (0.120 m held) | **4.468** | HELD | **4.468** (m3 0.894) | nothing (Checker re-measure) |

Hand check 1F-W05: (5.98 x 3.70 + 0.22 x 3.45) / 6.20 sampled = 3.691 m x 6.30 m = 23.254 m2; - W14 3.920 = 19.334 m2.
GF-W10: (3.54 x 3.75 + 6.82 x 4.00 + 2.50 x 4.10) / 12.86 = 3.951 x 12.87 = 50.845 m2.
GF-W07: (0.98 x 4.10 + 0.12 x 3.75) / 1.10 = 4.062 x 1.10 = 4.468 m2 (no opening in the run).
Totals (BEFORE_AFTER.csv by floor x thickness x type): established gross 567.251 -> 667.626 m2 (+100.375: WHITE 0.20
+78.567, BLACK 0.15 +21.808); established net 337.410 -> 361.212 m2 (+23.802, WHITE 0.20: 1F 19.334 + GF 4.468,
source-supported; +7.1 % of the established net);
independently VERIFIED 0 -> 0. The gross - deductions vs net gap stays fully explained (240.569 = reconstructed
240.568 m2, R-T225-1). Freelancer: comparison only (his 1F external 20 cm section is one height for the floor; not like
for like while held length remains).

## 4. D-12: the 20 column-containing rows (17 runs; D12_M3_RANGE.csv, D12_COLUMNS.csv)

What the plans build there (41 column outlines inside the 17 runs, P7757.dxf): 23 are 0.25 across in a 0.20 wall
(one face flush, a 0.05 nib on the other) and 3 are 0.20 / 0.25 in a 0.15 wall (nib 0.05 one side, 0.10 one side, or
0.05 both sides): the architecture draws the block at its printed thickness AND the column projecting, deliberately;
10 are drawn 0.20 = the 0.20 wall (flush both faces: a column-size question for T-217, not D-12); 5 stand long side
across the wall. The column stretch is concrete and is cut from every run once (section 5), so **gross and net m2 are
unchanged by D-12**; only m3 and the block product are in question: on the 7 rows with an established net (GF-W07
new), 23.407 m3 at the drawn thickness .. 31.737 m3 at the note's column thickness (+8.330 m3), never chosen; 13 rows:
net HELD, range not formed. Finding: note 20 at 0.25 m on a BLACK wall (8 rows: GF-W00, W01, W02, W03, W13, W28, 1F-W02, W23)
needs a block the owner's black range (0.15 / 0.20, Q-60) does not have: NO_STANDARD_PRODUCT, for the designer with
D-12. Status: CONFLICT range (designer D-12), unchanged; no owner question (ERS 2.7: a designer item already open).

## 5. Column footprints and junctions (COLUMN_CUT_AUDIT.csv, IDENTITY_BY_FLOOR.csv)

The merged T-125 V2 run was reproduced on P7757.dxf (t108_v2_lengths.py --check PASS: same run lengths as T-108 r2).
Rule UP-MAS-COLCUT-001: run = centreline - stretch inside columns + only explained additions. 31 runs / bands cross a
column (36: GF 15 + 3 split bands, 1F 11 + 2 split, 2F 5; 31.285 m of centreline inside columns): **0 columns counted
as block**; 30 runs exact (23) or + L-corner squares (7: 0.075 / 0.100 / 0.175 / 0.200 m = the partner walls' half
thicknesses); 5 split
bands shorter than their centreline (the split gap; never longer); 1 residual named: 1F WB-FL0074-FL0075 (1F-W23)
+0.0048 m beyond a 0.075 T-stem seat (UNEXPLAINED, below the 0.05 m census limit, not a column effect: 0.70 m in
columns is excluded). Area identity (union of wall strips less columns vs sum run x t): 1F PASS (0.000 m2), 2F PASS
(0.000 m2), GF PASS_WITH_LISTED_PIECES (+0.116 m2 = the 0.12 m2 strip beside the column in the 0.40 band GF-H01
(T-227 c) - 0.0009 m2): no L-corner square counted twice or missing; T stems 0 by construction (26 + 29 + 5 T
junctions). 6 GF junctions stay held (1.027 m max, closed by T-215, applied by T-228).

## 6. Verdict proposals, held items, owner items

- GF-W07 / GF-W10 / 1F-W05 / 1F-W11 / 1F-W16 heights: ENGINE_RIGHT (proposal) once re-measured: the printed depth governs
  (Q-60 A); the freelancer's single floor height (GF 4.00, 1F 3.70 / 3.45) is a RULE_DIFFERENCE (T-143).
- HELD with the missing item named: GF-W03 (one mark per span: designer D-03), 1F-W04 / 2F-W02 / W03 / W05 / W07 (a
  mark for each unlabelled span: designer D-04), GF-W36 (new: the 0.50 m band's mark; also a beam piece with no concrete
  line: lane S). Smallest held m2 in this scope: 0.988 (2F-W03).
- No owner question: every open item is a drawing conflict or omission for the designer (ERS 2.7 not met).
- Lessons rows proposed: (1) "A beam's width conflict was carried into the masonry height, holding 6.82 + 5.98 +
  0.38 m of wall with a printed, uncontested depth | the register status (CONFLICT) was read as 'depth unknown' | a
  height piece needs only the depth; a width-only conflict stays on the concrete line as a dependency
  (UP-MAS-HPIECE-001 R4, every villa) | tests/t226_heights (R4 normal; R2 / R3 / R5 / R6 adverse) | proposed".
  (2) "A wall end under a merged 'beam or column' face was held as 'nothing drawn above' | the slab-face class merged
  the CB1 band and its narrower column | split a merged face by the column-BELOW outline (R7, every villa) |
  tests/t226_heights R7 (adverse: unlabelled band stays R2) | proposed". (3) Own correction this run: I first read
  section B-B as outlining no beam; at 4x zoom it draws a solid head band continuous with the slab (corroborates CB10
  H 50): a raster section is read at the junction scale before calling it uninformative (extends the 2026-10-23
  build-up-band row).

Files: height_rules.py (pure rules), alsenan_t226.py (--check), alsenan_t226_audit.py (needs the private V2 capture),
register_delta.csv, PIECE_RESOLUTION.csv, BEFORE_AFTER.csv, D12_M3_RANGE.csv, D12_COLUMNS.csv, COLUMN_CUT_AUDIT.csv,
IDENTITY_BY_FLOOR.csv, summary.json; tests/t226_heights.
