# T-143: blockwork m2, m3 and block counts by hand, wall run by wall run (development villa, NO REPO CODE)

Worker 2, 2026-10-21 07:40-08:25 UTC, run session_01GaN5yBsGaRG9T7wZ97Dok4. Hand truth for the masonry-area module
(T-108). No engine, rule, test or fact file changed; no quantity released. Development villa, not an accuracy claim.
Self-check this run: clone PASS, venv PASS, codemap check PASS (stale none), tests/t061 PASS (20), freeze PASS (0).

## What was measured, in engineering terms

Block wall area per wall run = run length x the height under what sits on that wall (owner Q-60 A), member by member
along the wall, on the three floors. Lengths are the merged hand table (T-103) and the five Q-69 B lengths; the member
above each 2 cm of every wall comes from the structural roof-slab plan laid on the architectural plan.

| Floor | Hand gross m2 (Q-69 B physical run x Q-60 A height), measured part | + held runs at their candidate heights | Wall length with no candidate height (HELD) | Freelancer gross m2 (before his deductions, walls only) | Difference |
|---|---|---|---|---|---|
| GF | 460.07 | 497.31 .. 498.24 | 2.25 m | 515.40 | -55.32 m2 (-10.7 %) measured; -18.1 .. -17.2 m2 (-3.5 .. -3.3 %) with candidates |
| 1F | 371.83 | 398.24 .. 398.89 | 10.67 m (all under the two roof dome openings) | 441.41 (+ 41.25 "projections", no wall run) | -69.58 m2 (-15.8 %) measured; -43.2 .. -42.5 m2 (-9.8 .. -9.6 %) with candidates |
| 2F | 123.73 | 140.95 .. 145.54 | 0 | 137.70 | -13.97 m2 (-10.1 %) measured; +3.3 .. +7.8 m2 (+2.4 .. +5.7 %) with candidates |
| All | 955.63 | 1036.49 .. 1042.67 | 12.91 m | 1094.50 | -138.9 m2 (-12.7 %) measured; -58.0 .. -51.8 m2 (-5.3 .. -4.7 %) with candidates |

Measured block volume (m2 x drawn thickness): 172.19 m3, of which 2.70 m3 is the T-stem overlap of centreline runs
(each stem carried t_through / 2 into the wall it meets, T-103 junction census) to deduct for a physical volume. The
freelancer gives no m3. Net block m2 after openings: HELD on every row (no Urban masonry opening rule, below).
Of the measured 955.63 m2, 214.36 m2 is PROVISIONAL (annex datum, lift tie beam), the rest CALCULATED.

By block type and thickness (gross, measured part; type from T-107 / T-117 BLOCK_TYPE_BY_RUN.csv):

| Floor | White 0.20 | White 0.15 | Black 0.20 | Black 0.15 | Held type |
|---|---|---|---|---|---|
| GF | 155.73 m2, 31.15 m3 (68.13 provisional) | - | 144.65 m2, 28.93 m3 (82.50 provisional) | 159.70 m2, 23.95 m3 (63.73 provisional) | 1.60 m (GF-H01 0.40 band, GF-H02) |
| 1F | 157.11 m2, 31.42 m3 | - | 35.49 m2, 7.10 m3 | 179.23 m2, 26.88 m3 | - |
| 2F | 51.52 m2, 10.30 m3 | 27.99 m2, 4.20 m3 | 32.44 m2, 6.49 m3 | 11.78 m2, 1.77 m3 | - |

White blocks (owner Q-60 supplier sheet, gross basis before openings, product face not chosen): 62.5 x 25 face at 6.4
per m2 = GF 997 / 1F 1,006 / 2F 509 = 2,512 blocks; 60 x 20 face at 8.33 per m2 = 1,297 / 1,309 / 662 = 3,268 blocks.
Black blocks: no supplier face size given, count HELD. Adhesive: HELD (owner). These are comparison counts, not a
purchase quantity: the net m2 is HELD.

## Method (hand, checked; helpers in this folder, run in the scratchpad)

1. Wall runs: the merged hand table T-103 (gross centreline minus columns, UP-WALL-GEOM-001 / UP-COL-ORIENT-001) and
   MASONRY_CENTRELINE_V2 (T-125, READY 14f554b) for the run geometry, the split-out stretches (open floor, not wall) and
   the openings per run. Every hand row is a row of T143_BLOCK_BY_WALL_RUN.csv (75 building rows).
2. Overlay: the structural roof-slab plans (Drive "Alsenan chalet project", ST7757 dxf.dxf, sha 9f9d1179) on the
   architectural plans (P7757 DXF, sha ab54dd55) by a pure translation found from the column outlines: GF 30 / 30,
   1F 20 / 20, 2F 9 / 9 columns coincide with 0.000 m residual (align step).
3. Member above: each wall centreline sampled every 0.02 m (columns and split-out stretches dropped); a sample within
   0.03 m of a beam band of the route G overlay takes that beam (T-110 member register: mark, b x h, status; the deeper
   one at a junction), else the slab face it lies in (T-139 face classes: slab t 0.16 by ST p.8 note 18, or a printed
   T tag), else nothing drawn. Pieces under another member shorter than 0.10 m at a junction join the run's main piece.
   Sampled lengths are scaled to the hand run (scale 0.9-1.0; the run carries T stems and doorways to the node).
   Edge test of the 0.03 m capture distance: at 0.06 and 0.10 m every floor total moves by 0.6 m2 or less (under
   0.5 %); at 0.00 m the 1F facade loses 16 m2 because its beams sit flush with the wall line (a centreline exactly on a
   beam edge), so a zero tolerance is wrong for flush walls and 0.03 m is kept.
4. Height (owner Q-60 A, his worked example basis): printed floor-to-floor minus the beam depth from the schedule, or
   minus the slab thickness: GF main 4.50 (+1.00 -> +5.50), 1F 4.20 (+5.50 -> +9.70), 2F 4.20 (+9.70 -> +13.90).
   Heights met: GF 3.75 (0.75 beams), 4.00 (0.50), 4.10 (0.40), 4.34 (slab); 1F 3.45 / 3.70 / 3.80 / 4.04; 2F 3.00
   (B15 1.20 deep), 3.45, 3.80. Annex (+0.30 -> +4.30 on the marks): 3.25 / 3.50 / 3.60 / 3.84, PROVISIONAL (owner
   Q-54 B: datum HELD).
5. Five lengths (owner Q-69 B): (1) architectural run = hand gross minus columns (owner manual comparison); (2a) physical
   candidate = (1) minus the full glazing spans of the three glass lines GF-W11 (6.332), GF-W37 (4.95), 1F-W25 (3.136);
   (2b) solid at the plan cut = (1) minus every drawn opening (T-103); (3) glass / aluminium length per run (V2);
   (4) masonry above / below glazing: HELD on every run with glazing (head / sill heights: T-144); (5) net-area inputs =
   (2a) x height, opening widths listed, deduction HELD.

## Second drawing read (issued scans, Drive "Alsenan chalet project", ST7757.pdf)

- p.8 RECOMMENDATIONS read on the issued sheet: note 18 "slabs 16 cm unless stated otherwise" (the slab height basis);
  note 19 "beams tie the lift columns at 3.00 m where the storey height exceeds 4.30 m, round the lift" (GF only:
  4.50 > 4.30; 1F / 2F 4.20 do not trigger it); note 20 "walls containing columns at the column thickness" (D-12).
- p.6 SECOND FLOOR ROOF SLAB: "B15" printed beside the NORTH span of the west band (water-tank panels "T 18"), the
  south span of the same band unlabelled and hatched: agrees with the register (B15 20 x 120 north -> 2F-W07 3.00 m
  under it; south span HELD, D-04).
- Storey heights: the T-112 section reading (sheet 10, 157.4 px / m checked on the printed "420") gives GF 4.50,
  1F 4.20 between FFL marks; 2F +9.70 -> +13.90 from the elevations (T-103).

## Held, with the reason (never 0)

| Rows | Length | Why | Candidate |
|---|---|---|---|
| 1F-W11, W13, W17, W18, W24 (0.15 partitions) | 10.67 m | under the two 1F-roof dome openings (T-139 faces 1F-073 / 076 / 077): no beam or slab underside to stop at; NEW designer item | none |
| GF-W10 (CB2), 1F-W05 (CB10), 1F-W16 (B6) | 13.17 m | member CONFLICT (designer D-27 / D-02: width only, depth printed) | 4.00 / 3.70 / 3.70 m -> 50.78 m2 |
| GF-W03 | 2.65 m | CB3 / "B3 (With Stair)" two marks (D-03) | 3.75 .. 4.10 m -> 9.94 .. 10.87 m2 |
| 2F-W02, W03, W05, W07; 1F-W04 | 6.56 m | beam pieces with no mark and no printed depth (T-110 HELD, Q-61 C, designer D-04) | T-110 candidate depths 0.40 .. 1.20 -> 19.69 .. 24.94 m2 |
| GF-W07, GF-W36 | 0.62 m | beam / column junction face with no register member | none |
| GF-W30 | 1.525 m | no wall band on the plan run (T-125 MISSING), member not bound | none |
| GF-W37 solid 0.10 m, GF-H01 (0.40 band, B20 above), GF-H02 | 1.70 m | glazed line / thickness and material held (T-103) | - |
| GF lift walls W08, W09, W13, W14 (gross PROVISIONAL) | lift part 5.69 m | structural p.8 note 19: beams tie the lift columns at 3.00 m where the storey exceeds 4.30 m (GF 4.50): the tie beam's size is not printed, so its strip is not deducted | - |
| Annex walls (13 rows) | 49.09 m | annex datum HELD (Q-54 B) | heights on the printed marks, PROVISIONAL |
| Net m2 on every row | - | UP-GEN-003 (the opening table per trade) has SKIRTING, WALL_TILE, WATERPROOFING, PLASTER / PAINT rows and no MASONRY row; no other Urban rule deducts openings from block | - |
| Parapets 104.25 lm + 4.30 held thickness, street fence 8.20 lm (5.70 solid + 2.50 gate) | | owner Q-65 C (material HELD); north fence 31.17 lm and sea-side fence 7.00 lm as T-103 / T-107; heights from the fence and parapet details not read here | - |

Lintels: the structural set prints a lintel schedule by opening width (route G LINTEL_OPENINGS, 56 openings bound, 10
measured / 46 held); owner 10:45 (3): the printed structural schedule wins, never both, so precast atab lintels are
NOT APPLICABLE where it governs. Openings in white-block walls listed for that check: GF 17 (24.64 m), 1F 13 (16.39 m),
2F 5 (5.00 m), of which glazing spans GF 6.33, 1F 3.58.

## Q-69 B ground-floor ledger (corrected arithmetic)

T143_Q69_LEDGER_GF.csv, wall by wall: architectural run 143.16 m (external 86.825 + internal 56.335) -> physical
candidate 131.878 m (minus the saloon glazing 6.332 and the pool glass 4.95). Against the freelancer's 134.28 m:
external +8.275 m = the two glass lines 12.05 m (7.00 + 5.05) minus 3.775 m of pieces on either side that do not pair;
internal +0.605 m (T stems to the centreline); total +8.88 m (+6.6 %). On the physical candidate: -2.40 m (-1.8 %).
Q-69's "12.05 - 3.77 = 8.88" is corrected: 12.05 - 3.775 = 8.275 (external), + 0.605 internal = 8.88 overall.

## Who is right: proposals for the verifier

1. Height basis, every floor: the freelancer takes one height per floor and zone (GF 4.00, annex 3.50, 1F 3.70 / 3.45,
   2F 3.45 / 3.70); owner Q-60 A takes the underside of the member above each wall: RULE_DIFFERENCE, ENGINE_RIGHT under
   the owner's rule. Hand example: GF-W01 neighbour wall, 15.17 m under CB8 20/30 x 75 -> 4.50 - 0.75 = 3.75 m and
   1.30 m under B1 20 x 40 -> 4.10 m: 62.16 m2; his same pieces at 4.00 m: 65.88 m2 (-3.72 m2).
2. Glass lines (GF-W11, GF-W37): he has no row; Q-69 B keeps only the solid pieces: FREELANCER_RIGHT on the physical
   run, masonry above / below HELD (T-144). The 1F concave bay (1F-W25, 3.58 m glazing): same.
3. 1F "projections" 7.50 x 5.50 = 41.25 m2: no wall run on any plan: UNRESOLVED (elevation feature, T-103 / T-144).
4. GF internal 0.20 (+53 % on his 20 cm row): his row holds only the lift core; the plans draw and print 0.20 for the
   annex WC wall, the wall under the reception stair and the lift-lobby walls: ENGINE_RIGHT on thickness (T-103), the
   0.15 + 0.20 sum is the like-for-like line.
5. Dome-opening walls, member conflicts and unlabelled beams: UNRESOLVED (designer items, above); never 0.

## For the checker (plan P-07: re-measure 5 walls)

| Wall | Hand pieces (member above: length -> height) | Gross m2 |
|---|---|---|
| GF-W01 (0.20, black S1 provisional) | CB8 x 0.75: 6.34 + 5.74 + 3.08 -> 3.75; B1 0.40: 1.12 -> 4.10; CB1 0.75: 0.18 -> 3.75 | 62.155 |
| GF-W28 (0.15, D-12 conflict 0.25) | slab GF-039: 2.34 -> 4.34; B17 0.75: 1.76; B13 0.75: 0.98; B11 0.75: 0.26 -> 3.75; slab GF-052: 0.18 -> 4.34 | 22.215 |
| 1F-W06 (0.20 white, south facade) | CB11 0.75: 6.72 + 3.30 + 2.64 -> 3.45; B4 0.50: 3.80 -> 3.70 | 57.772 |
| 1F-W20 (0.15 black) | slab 1F-023: 4.55, slab 1F-063: 1.20 -> 4.04; B19 0.75: 0.46 -> 3.45 | 25.076 |
| 2F-W07 (0.20 white) | B15 20 x 120: 2.70 -> 3.00; unlabelled beam BM-2F-016: 2.94 -> HELD | 8.222 + HELD |

## Learned / missing

- Learned: on this villa the member above changes along most walls (a 16 m facade wall carries 3 beam depths), so one
  height per floor (the freelancer's way) misstates block area by 4-10 % per floor; the structural and architectural
  CAD share a pure translation recoverable from columns alone, which the module (T-108) can use on any villa.
- Learned: walls can stand under a roof dome opening (1F); Q-60 A has no answer there, a designer item, not a default.
- Missing: an Urban masonry opening-deduction rule (net m2 HELD everywhere: for the Lead); the tie-beam size round the
  lift (note 19); the D-12 thickness conflict changes m3 on 19 rows from 77.57 (drawn) to 100.07 m3 (column
  thickness), never chosen; parapet and fence heights / materials (Q-65 C); masonry above / below glazing (T-144).

Files: T143_BLOCK_BY_WALL_RUN.csv (one row per wall run), T143_TOTALS_VS_FREELANCER.csv, T143_TOTALS_BY_TYPE_THICKNESS.csv,
T143_Q69_LEDGER_GF.csv, scripts/ (align, heights, build, totals, q69 helpers; inputs stay in the scratchpad).
