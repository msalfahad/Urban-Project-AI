# T-117: Alsenan masonry centreline run (MASONRY_CENTRELINE_V1) vs the T-103 hand table, run by run

Gate 2 (blockwork). Worker 3, 2026-10-20. Drawing: Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip ->
P7757.dxf, sha256 ab54dd55...31cc4 (= manifest), decoded in the session scratchpad only. Engine: working branch head
8c23eea, ARCH_TAKEOFF_V2.12 walls, MASONRY_CENTRELINE_V1 (T-027, not wired). Rules: UP-WALL-GEOM-001 (centreline =
masonry run), UP-COL-ORIENT-001 (columns are concrete), UP-QTY-STATUS-001; owner Q-60 A and block rules of 10:45, Q-63 C,
Q-65 (open). Block m2 / m3 are not in this task (T-108).

Files: `alsenan_centreline_run.py` (runs the piece on the drawing; writes JSON to the scratchpad), `t117_compare.py`
(this table), `ENGINE_VS_HAND_BY_RUN.csv` (every engine piece and every T-103 row, paired, with cause and verdict
proposal; LOCAL metres = origin at the lower-left corner of each floor's wall centrelines), `TOTALS_BY_FLOOR_THICKNESS.csv`,
`D12_WALLS_WITH_COLUMNS.csv` (every column the run line crosses), `D12_CONFLICT_RUNS.csv`, and
`../agents_t107/BLOCK_TYPE_BY_RUN.csv` (T-107's typed table, written here because its own branch was refused).

## 1. Totals per floor and thickness (metres, centreline, openings in the run, columns out)

The piece is run with the column outlines the wall stage itself uses (30 GF / 20 1F / 9 2F = the T-100 column census).
Without them (`measure_arch` default) it subtracts only each band's own column metres and misses every column inside an
L-corner extension: GF +4.09, 1F +2.43, 2F +1.20 m too much. Any wiring must pass the column polygons.

| Floor | t | Engine (col. polygons) | Engine (band basis) | Hand T-103 | Engine - hand | Freelancer |
|---|---|---|---|---|---|---|
| GF | 0.15 | 38.023 | 37.988 | 41.185 | -3.162 (-7.7 %) | |
| GF | 0.20 | 111.395 | 115.515 | 101.975 | +9.420 (+9.2 %) | |
| GF | 0.40 | 0.600 released | 0.600 | HELD (GF-H01) | status differs | |
| **GF** | 0.15+0.20 | **149.418** | 153.503 | **143.160** | **+6.258 (+4.4 %)** | **134.28** (engine +15.14, +11.3 %) |
| 1F | 0.15 | 54.917 | 55.067 | 57.045 | -2.128 (-3.7 %) | |
| 1F | 0.20 | 63.279 | 65.561 | 63.708 | -0.429 (-0.7 %) | |
| **1F** | | **118.196** | 120.629 | **120.753** | **-2.557 (-2.1 %)** | **120.31** (engine -2.11, -1.8 %) |
| 2F | 0.15 | 10.900 | 10.900 | 11.000 | -0.100 (-0.9 %) | |
| 2F | 0.20 | 28.700 | 29.900 | 28.775 | -0.075 (-0.3 %) | |
| **2F** | | **39.600** | 40.800 | **39.775** | **-0.175 (-0.4 %)** | **39.10** (engine +0.50, +1.3 %) |

Held by the piece (never 0): GF 0.15 max +0.552 m at three 45 deg junctions, GF 0.20 max +0.20 m at one corner.

## 2. Every difference over 0.05 m, by cause (sum = engine - hand)

| Cause (general, not Alsenan-specific) | GF | 1F | 2F | Proposal |
|---|---|---|---|---|
| A. Band joins two collinear walls across open floor (no wall face on any layer, no opening): GF y 1.50 one band from the annex W.C. wall (x 7.80) to the garden wall (x 25.37), 16.52 m of which 4.30 m are wall (+12.22); x 21.925 two 0.15 stubs joined across the 1.96 m inside the wedge W.C. pair (+1.91) | +14.13 | | | HAND_RIGHT |
| B. Band runs across both mouths of the open-air side passage (x 10.70-11.90, lines on a non-wall layer; T-109) | +2.50 | | | HAND_RIGHT |
| C. Doorway between a wall's free end and a perpendicular wall left out of the run (OPENING_GAP only joins two collinear bands): GF W27 0.874, W29 0.649; 1F W12 1.089, W23 0.880 | -1.52 | -1.97 | | HAND_RIGHT |
| D. Wall not in the run at all: GF-W30 (0.30 stub from the wedge corner + its 0.797 door) | -1.53 | | | HAND_RIGHT |
| E. Pool-side glazed line GF-W37 (0.20 band filled with 4.95 m glazing, PDF: curved glass wall) has no band; 0.10 m of it is block | -5.05 | | | run: UNRESOLVED (the hand keeps the almost all-glass line GF-W11 and GF-W37 in the run, the engine keeps W11 only; the freelancer has neither); solid 0.10 HAND_RIGHT |
| F. Concave curved bay in the 1F east wall: the band runs straight across the chord (glazing line) instead of the 3.673 m arc; the arc becomes a 0.169 m stub | | -0.35 | | HAND_RIGHT |
| G. T junction: hand runs the stem to the through-wall centreline (T piece counted twice, also in the plan strip); piece stops on the face. Incl. 0.225 / 0.175 inside the C rows | -1.48 | -1.38 | -0.18 | ENGINE_RIGHT |
| H. 45 deg junctions: piece HELD (max 0.552 m listed) or cut square at the drawn end | -0.74 | | | UNRESOLVED (piece holds them) |
| I. 1F doorless 1.375 m opening between 1F-W14 and 1F-W15 (x 15.27-16.645): in the piece's run, in neither hand row (T-103's own basis keeps openings in the run); east end stops at the mitred bay cap (0.234) | | +1.14 | | ENGINE_RIGHT (1.375) / UNRESOLVED (0.234) |
| J. Corner end held by the piece | -0.05 | | | UNRESOLVED (held) |
| **Total** | **+6.26** | **-2.56** | **-0.18** | |

Runs equal to the hand to 0.001 m: GF 13 of 33 paired pieces, 1F 9 of 23, 2F 7 of 9.

Engine right where the hand table is not: G (3.03 m in all, the hand table double-counts the T piece) and I (1.375 m).
Hand right where the engine is not: A, B, C, D, F: +16.63 m too much on GF and 5.43 m too little over GF / 1F. The GF
result (+4.4 % on the hand, +11.3 % on the freelancer) is therefore NOT a better measurement: it hides +16.63 m of
non-wall under -10.37 m of misses. The piece is not ready to be wired.

Fix proposals for a MASONRY_CENTRELINE_V2 (new version, T-027 stays frozen in behaviour):
1. Split every band at each stretch of its centreline where neither face is drawn on the wall layer and no door /
   window / opening symbol sits (A, B), then re-join only by the existing OPENING_GAP rule (opening width, <= 3.0 m).
2. A doorway between a free wall end and a perpendicular wall (door insert or swing arc in the gap, gap <= 3.0 m) is
   added to the run up to that wall's face (C, D).
3. A curved band of the wall layer whose ends meet a straight band replaces that band's chord (F); a line drawn as a
   0.20 band filled with glazing is listed as a glazed line (E), never dropped silently.
Hand-checked fixture cases for it: two collinear 0.20 walls 11.2 m apart joined only by a garden edge on another layer
(run = the two walls); an L room with a 0.80 door at the free end of a partition (run includes 0.80); a concave bay.

## 3. GF hand vs freelancer, +8.88 m (+6.6 %), split wall by wall (T-103 pairing)

External (hand 86.83 vs 78.55 m, +8.28): the saloon facade line GF-W11 (7.00 m less columns, 6.33 of it glazing) and
the pool-side glazed line GF-W37 (5.05) have no row of his, +12.05 m: RULE_DIFFERENCE (an almost all-glass line kept in
the run by the T-103 basis); the rest, -3.77 m, are his external pieces that T-103 could not pair one to one (face-to-face
lengths; his three 4.45 m rows booked as 15 cm internal may be the 0.20 passage walls): UNRESOLVED as in T-103.
Internal (hand 56.34 vs 55.73, +0.61): the T stems to centreline in the hand table (cause G, GF 1.48 m) more than
explain it: engine (T on the face) is closer to his face-to-face pieces.

## 4. Designer item D-12: walls that contain columns (structural p.8, rec. 20, built at the column thickness)

From `D12_CONFLICT_RUNS.csv` (a column whose long side lies in the wall line and that is wider than the drawn wall):

| Floor | Drawn 0.15, column wider (by the note) | Drawn 0.20, column 0.25 (by the note) |
|---|---|---|
| GF | GF-W28 5.527 m -> 0.25 (column 1.00 x 0.25) | GF-W00+W01, W02+W03, W04+W05, W07, W10, W13, W15, W17: 63.94 m (hand metres) |
| 1F | 1F-W18 5.275 m -> 0.20 (column 1.00 x 0.20); 1F-W23 6.500 m -> 0.25 (0.70 x 0.25) | 1F-W02, W04, W06, W08, W10: 37.24 m |
| 2F | - | 2F-W07 5.725 m |

Metres per thickness by the plan (as drawn) and by the note are both shown; every one of these runs is a CONFLICT
(designer D-12), never chosen. By the note GF would move 5.527 m from 0.15 to 0.25 and 63.94 m from 0.20 to 0.25; 1F
5.275 m 0.15 -> 0.20, 6.500 m 0.15 -> 0.25, 37.24 m 0.20 -> 0.25; 2F 5.725 m 0.20 -> 0.25. Open for the designer: does
"containing" mean only the stretch beside the column (the note's literal reading for a wall, the whole run) or the run
between columns too; and do columns at a wall end or corner (END_OR_CORNER_COLUMN in the CSV) count. T-107 listed the
three 0.15 runs; the 0.20-around-0.25 runs are new here on 1F (5 runs) and 2F (1 run).

## 5. T-107 typed table (research/agents_t107/BLOCK_TYPE_BY_RUN.csv)

93 rows = every T-103 row. Totals reproduce the verifier's 15:10 reconciliation: WHITE ASSUMED (owner Q-60 fallback,
outer walls) GF 60.455 / 1F 54.013 / 2F 26.850 = 141.32 m; BLACK ASSUMED (inner) 56.335 / 66.740 / 12.925 = 136.00 m;
BLACK PROVISIONAL (S1 structural p.1 note 2, extent D-11) GF-W00 / W01 26.37 + north fence 31.17 = 57.54 m; HELD:
parapets 59.313 + 44.94 + 4.30 (thickness held) + top-roof parapet (no plan) under Q-65, street fence 8.20 under Q-65,
GF-H01 / H02 1.60; UNRESOLVED (Q-63 C, no type): sea-side element 7.00 m. The three D-12 0.15 runs carry the conflict flag.

## 6. Who is right (summary for the verifier)

ENGINE_RIGHT: T junctions (G) 3.03 m; 1F doorless opening 1.375 m. HAND_RIGHT: bands across open floor / passage mouths
(A, B) 16.63 m over; doorways at free ends and GF-W30 (C, D) 5.02 m under; 1F curved bay 0.35 m. UNRESOLVED: GF-W37
glazed line in or out of the run (5.05 m; same question for GF-W11 against the freelancer); 45 deg and corner holds 0.79
m. Missing: the MASONRY_CENTRELINE_V2 fix (a code task); designer answer on D-12; owner Q-65 for parapet / fence type.
