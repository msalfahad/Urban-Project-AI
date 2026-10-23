# T-215: block-wall HELD bounds closed from the drawings, part 1: the GF 45 deg and column ends (development villa)

Worker 2, 2026-10-23 13:41 - 15:00 UTC, run session_01Q2V7fPynCjJRtDTxJMf6Eb. Lane A, gate 2. Files: research/agents_t215/*,
tests/t215_junction_close/* only (no engine, rule, registry, frozen or released file changed; T-108 files untouched).
ERS: read; s.2 steps 1-4 (element, evidence, first-principles reconstruction, reconciliation), s.3 (one element counted
once; physical vs procurement), s.4 (rule + test), s.7 row below. Drawings cited by Drive title and DXF handle only; no
coordinate, image or client name is committed. Development villa, not an accuracy claim.

## 1. Result in engineering terms

T-108 r2 carried the GF block walls that end at 45 deg junctions or at a column with a HELD bound "0 .. max more,
never added": GF-W13 0.200, GF-W20 / W21 / W31 0.137 each, GF-W32 0.278, GF-W33 0.217, GF-W34 0.256 m = **1.362 m
HELD**, and the Checker's G-T108-1 junction piece (GF-W22 / GF-W34, about 0.150 m of 0.15 wall) inside GF-W34's bound.

**All eight are closed from the drawn faces: +0.2855 m of 0.15 black wall that the runs did not count (0.0428 m2 of
masonry in plan), each piece assigned to exactly one wall; 0 m stays HELD at these ends.**

| Row | T-108 length | HELD bound | Closed length | Change | Member(s) over the run | Gross m2 change | m2 status |
|---|---|---|---|---|---|---|---|
| GF-W13 (0.20) | 0.700 | 0 .. 0.200 | 0.700 | 0 (the end is the column, concrete) | B1 4.10 | 0 | EXACT |
| GF-W20 | 1.018 | 0 .. 0.137 | 0.981 | -0.037 (Y node) | slab 4.34 | -0.161 | EXACT |
| GF-W21 | 1.024 | 0 .. 0.137 | 0.993 | -0.031 (bend) | slab 4.34 | -0.135 | EXACT |
| GF-W22 | 2.887 | none (piece sat in W34's) | 2.982 | +0.095 (junction piece, G-T108-1) | slab 4.34 / B1 4.10 | +0.390 .. +0.413 | BOUNDED |
| GF-W31 | 1.279 | 0 .. 0.137 | 1.321 | +0.042 (Y node) | slab 4.34 / B4 4.00 | +0.166 .. +0.181 | BOUNDED |
| GF-W32 | 2.842 | 0 .. 0.278 | 2.968 | +0.116 (Y node) +0.011 (column end) | slab 4.34 / B1 4.10 / B11 3.75 | +0.473 .. +0.547 | BOUNDED |
| GF-W33 | 1.256 | 0 .. 0.217 | 1.287 | +0.031 (bend) | slab 4.34 | +0.135 | EXACT |
| GF-W34 | 2.355 | 0 .. 0.256 | 2.415 | +0.060 (junction piece, G-T108-1) | slab 4.34 / B3 4.10 | +0.244 .. +0.259 | BOUNDED |
| **GF, 0.15 black** | | **1.362 m HELD** | | **+0.2855 m** | | **+1.113 .. +1.239 m2** (m3 +0.167 .. +0.186) | |

Length: DRAWING-CONFIRMED (both faces drawn on the wall layer of P7757.dxf; the bound is closed, not narrowed).
Gross m2: EXACT where the run has one member above it (Q-60 A height); BOUNDED by the run's own member heights where it
has several, because T-143 sampled the member above along the band only and the end piece lies beyond the band: the
member over the end piece is the remaining cause (one read of the GF roof-slab plan of ST7757 dxf.dxf at each end).
Never the weighted mean. Effect on T-108's established net 337.412 m2 (DC 252.817 + AOA 84.595): **+1.113 .. +1.239
m2** (DC rows W20 / W21 / W22 / W31 / W33 / W34 +0.640 .. +0.692; AOA row W32 +0.473 .. +0.547), not applied to the
ledger here (T-108 files untouched; Worker 3 integrates). White / black split: every closed row is BLACK (inner wall,
Q-60 fallback, ASSUMED — OWNER-APPROVED, no block note on any sheet, T-107); white 0.20 established net unchanged
47.359 m2 (303.1 / 394.7 units); black units stay with T-176.

Engine vs freelancer: GF internal 0.15 (his 181.720 m2 gross) is still not like-for-like while other held length
remains in that section (T-108 s.3: 2.687 m held incl. 1.162 m of these ends -> now 1.525 m; GF internal 0.20: 2.850 ->
2.650 m with GF-W13's 0.200 closed); no verdict on
the section total. Per wall: his hand runs carry these ends to centrelines (T-125 UNRESOLVED rows, -0.050 .. -0.256 m
vs ours); with the physical length now closed, those rows become ENGINE_RIGHT on the drawn faces for the length (the
hand column stays a comparison column, never the input).

## 2. The physical elements and the evidence (s.2 steps 1-3)

P7757.dxf GF plan (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip), wall layer faces by handle:

- **J-A, G-T108-1**: GF-W22 (0.15, faces D2:528 / D2:545) runs north to the north wall; GF-W34 (0.15, 45 deg, faces
  D2:806 / D2:807) starts with its lower face at GF-W22's east-face top and its upper face on the north wall's near face
  (D2:625 / D2:691, drawn with a 0.250 m gap where both stems join it). The runs counted GF-W22 to its east-face top
  and GF-W34 to the perpendicular through its node point; the masonry between those cuts and the north face is
  0.0232 m2 (a trapezoid 0.250 / 0.150 x 0.112 m less what the oblique cut already counted). Independent check: a 0.5 mm
  grid over the face inequalities gives the window masonry 0.173311 vs 0.173219 m2 (0.05 %).
- **J-B**: GF-W21 is one bent wall with GF-W33: both faces turn 45 deg (D2:190 -> D2:792, D2:736 -> D2:793), no through
  wall. The two runs count 2.280 m together = the drawn area / 0.15 (residual -0.000003 m2): nothing was missing; the
  bound closes at 0 net and 0.031 m moves from GF-W21 to GF-W33 (each to the mitre).
- **J-C, Y node**: GF-W20 comes down from the north wall and splits into GF-W31 (SE, D2:804 / D2:805) and GF-W32 (SW,
  D2:796 / D2:791); the crotch is the corner D2:791 / D2:804; door OP-018 opens 0.14 m from the node in GF-W32. The runs
  left the node triangle uncounted (V2 called GF-W32's node end a free end): 0.0180 m2.
- **J-D, column**: GF-W32's 45 deg end runs into the 0.20 x 0.50 column on the GF-W13 line (S-COL.BON outline,
  handles D2:12171 / D2:12173); its faces stop on the column outline (D2:795 on the east face, D2:799 on the top face).
  The run counted 0.0012 m2 of concrete inside the column and missed a 0.0028 m2 masonry triangle: net +0.0016 m2
  (hand: triangle 0.106 x 0.053 / 2 = 0.0028 less 0.049 x 0.049 / 2 = 0.0012 inside the column = 0.0016, = module).
  GF-W13's held top end is that column: no masonry, closes at 0.

## 3. Rule (proposed, any villa; new file when adopted, never an edit): UP-MAS-JUNCTION-001 v1.0.0

The masonry at a wall junction is the region the drawn faces enclose, less columns. Every point of it belongs to ONE
wall: inside one band -> that wall; inside several -> the through wall drawn continuous across the junction (a stem
stops on its face, the V2 T rule); else the wall in whose band it lies most centrally (|d| / (t / 2) smallest: at an L
each wall gets half the corner parallelogram, the mitre's areas, for any thickness; mirror / rotation invariant);
masonry inside no band is UNASSIGNED and HELD; two crossing through walls are refused. Each wall's length change =
its share / t minus what its run already counts in the same window; extra lengths claimed beyond the unmeasured area
count a piece twice and are refused. A held end is closed by area, never by extending a centreline to a guessed point.

## 4. Tests and validation

- tests/t215_junction_close/test_junction_close.py (13): villa T215-F, NOT Alsenan, hand truth in the docstring: F1 L
  corner 0.700 m2 -> 2.000 / 1.500 m, deltas -0.100 / +0.100; F2 T + 45 deg stem under a through wall: 0.295000 m2,
  junction piece 0.020607 m2; F3 end in a column -> 0; unequal thickness; mirror, 90 deg and 30 deg + shift invariance.
  Adverse: junction piece claimed by both walls -> refused; an L corner square in both -> refused; millimetres
  refused; no direction refused; empty masonry -> ValueError ("HELD, never 0"); a wall listed twice refused; masonry
  in no band -> PARTLY_HELD with its area; two crossing through walls refused; a through wall takes the seat.
- tests/t215_junction_close/test_t215_alsenan_ledger.py (6): every cluster CLOSED, sum t x delta = residual, the G-T108-1
  piece assigned once, the bend moves length without changing the total, the column end 0, no change above its old
  bound, EXACT only for one member, no coordinates in the files.
- `alsenan_t215_ends.py --check` reproduces both CSVs from the private capture (outside the repository): PASS. The V2
  capture reproduces T-108's run lengths (`t108_v2_lengths.py --check` PASS on the same capture).

## 5. Not closed in this run (stay HELD with their bounds; never 0)

- 1F bay basis 0.477 m on 1F-W25 (0 .. 1.645 m2): which ends of the concave glazed bay are block needs the elevation /
  section read (DWF), not the plan; same method then applies to the stub ends.
- 1F-W14 + W15 with P-1F-01 (net 10.971 .. 16.223 m2) and P-1F-01 masonry above its lintel 0 .. 4.992 m2: head drawn
  on no sheet (T-201 / T-207 re-checked; section B-B draws two leafed doors there: a drawing conflict for the designer).
- P-GF-05 masonry above the lintel 2.232 .. 2.700 m2: B1 soffit level at the opening (SW elevation face to +4.70, section
  B-B beam stubs to +4.95 at the court wall, T-143 calculated +5.10 with the structural top HELD, T-200 / T-206 / T-214).
- The member over each closed end piece on the four BOUNDED rows (one ST7757 dxf.dxf GF roof-slab read per end).

## 6. For the Checker (re-measure from the drawing)

1. J-A on P7757.dxf GF: GF-W22 faces D2:528 / D2:545, GF-W34 faces D2:806 / D2:807, north face D2:625 / D2:691 gap:
   the masonry between GF-W22's east-face top, the north face and GF-W34's faces; expected unmeasured 0.0232 m2,
   GF-W22 +0.095 / GF-W34 +0.060 m by the band rule (or by your own once-only split; the total is the check).
2. J-D: GF-W32's faces D2:795 / D2:799 end on the column outline D2:12173 (0.20 x 0.50); GF-W13's top is that column.

## 7. Lessons-register row (proposed, s.7)

2026-10-23 | 1.362 m of GF block wall held as '0 .. max more' at 45 deg and column ends for a day, and one junction
piece sat inside another wall's bound (G-T108-1) | an end the centreline module could not type as T or L was held
instead of measured, although both faces were drawn | close a wall end by the drawn masonry AREA, assign every point
once (band, through wall, most-central band), never by extending a centreline; a held end needs an undrawn face
(any villa) | tests/t215_junction_close (piece in both walls refused; F1 / F2 / F3 hand truth) | READY (T-215 part 1).
