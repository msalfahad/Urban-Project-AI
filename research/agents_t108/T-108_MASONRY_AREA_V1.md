# T-108: MASONRY_AREA_V1, block m2 / m3 / installed white units per wall run (development villa run)

Worker 2, 2026-10-23 06:44 - 07:30 UTC. Lane A, gate 2. New opt-in module `engine/source/masonry_area_v1.py`
(imported by nothing, not wired); no released quantity, rule file, frozen method or registry changed. Development villa,
not an accuracy claim. Drawings cited by Drive title only. ERS: read; s.2 (element, evidence, reconstruction,
reconciliation, status), s.3 (installed vs procurement, build before deduct, physical vs contract) and s.4 applied.

## 1. What the module does (any villa)

Per wall run: the member above each piece of wall (beam with its schedule depth, or slab with its thickness, or
nothing drawn), height = storey height (slab top to slab top) minus that depth (owner **Q-60 A**), weighted over the
pieces and applied to the **Q-69 B** physical blockwork length (glazing spans out; architectural run kept beside it);
the full area of each actual opening deducted only where masonry is built inside the run (**Q-73**, through
OPENING_SCOPE_V1 of T-175); m3 = net x drawn thickness; installed white units on the net for both supplier faces of the
Q-60 answer (62.5 x 25 -> 6.4 / m2, thicknesses 10-30 cm; 60 x 20 -> 8.333 / m2, 15 and 20 cm only); black units HELD
(no face size: Q-75 investigation T-176); atab only over openings in WHITE walls and NOT APPLICABLE wherever a printed
structural lintel schedule governs (never both), else width + 2 x a bearing given by a source, shortest supplier length
1.00 / 1.20 / 2.50 / 3.00 / 4.00 m, longer -> HELD; adhesive HELD (coverage not given).
A beam with no printed depth, a CONFLICT member, or nothing drawn above (dome opening, column face) holds its length;
a HELD storey datum (annex, Q-54 B) yields a candidate, never a quantity; a wall with any held length forms no candidate
net (an opening may sit in the held part). Guards: mm inputs, a depth not below the storey, non-s.5 statuses, unknown
block type / member kind -> ValueError. Waste, cutting, breakage and pallets are NOT here (procurement, T-176).

## 2. Development villa (Alsenan) through the module

Inputs: T-143 wall runs and members above (merged), T-175 opening hosts (census r3 of T-198: established block m2
change 0.000, DOWNSTREAM_T198.csv C1-C5). The module recomputes each of the 127 member-above pieces' heights from the
storey heights (GF 4.50, annex 4.00 PROVISIONAL, 1F 4.20, 2F 4.20) and the schedule depths: **max difference vs T-143's
heights 0.000 m**; gross vs T-143 on 71 rows max 0.006 m2 (sum 0.026, the 0.01 m rounding of piece lengths); net vs
T-175 on 43 rows max 0.001 m2; status mismatches 0.

| Floor | Gross, known pieces (DC / HELD-provisional or partly held) | Held length | Net DRAWING-CONFIRMED | Net ASSUMED — OWNER-APPROVED (door height Q-55 C) | m3 of the established net | Walls with net HELD | Net candidate on a provisional gross (not a quantity) |
|---|---|---|---|---|---|---|---|
| GF | 460.075 m2 (218.153 / 241.922) | 13.32 m | 122.324 m2 (10 walls) | 38.363 m2 (4) | 27.713 | 26 | 120.774 m2 |
| 1F | 371.835 (292.298 / 79.537) | 17.96 m | 106.134 (11) | 38.087 (3) | 23.689 | 12 | - |
| 2F | 123.733 (61.756 / 61.977) | 5.738 m | 43.136 (3) | 10.020 (1) | 10.130 | 5 | - |
| **All** | **955.643** | **37.019 m** | **271.594 (24)** | **86.469 (8)** | **61.532** | **43** | 120.774 |

By type and thickness (T108_TOTALS_BY_FLOOR_TYPE_T.csv): established net white 0.20 = GF 10.048 (4.458 DC + 5.590 AOA),
1F 17.215, 2F 21.476 m2 = **48.739 m2 -> 311.9 units 62.5 x 25 or 406.2 units 60 x 20** (installed, no waste; type
ASSUMED — OWNER-APPROVED: outer white by the Q-60 fallback, so the units carry that status); 19 white walls net HELD
(heads of 21 windows, member conflicts, unlabelled 2F beams, annex datum). Black: 309.324 m2 established net, units HELD.
Atab: NOT APPLICABLE on every opening (ST7757.pdf p.13 LINTEL SCHEDULE governs; lintels are the S8.6 line).

### Height coverage (found and settled this run)
Four rows had member-above samples over less than 80 % of the run (flag LOW_HEIGHT_COVERAGE). Cause: a free-end doorway
sits inside the run but not on the wall band, so T-143 sampled nothing over it and extended the band's height. Own read
on ST7757 dxf.dxf (roof-slab plans; translation from the column outlines GF 30 / 30 at (202.33, 841.64) m, 1F 20 / 20 at
(208.46, 841.64) m, residual <= 0.004 m, reproducing T-143's alignment): over D-GF-02 (GF-W27) and D-GF-10 (GF-W29) no
beam edge within 0.70 m and slab rebar text only, no T tag -> slab 0.16, same member; over D-1F-03 (1F-W12) the B4 band
(0.20 wide) continues over 0.988 of the 1.089 m gap -> same member. **No height or quantity changes**; DRAWING-CONFIRMED
by own read. 1F-W25 (concave bay stubs) not read: for the Checker.

## 3. Engine vs freelancer (his BLK rows, T143_TOTALS_VS_FREELANCER.csv), units first

| Floor / his section | Ours gross (known) | His gross | Diff | Like-for-like? |
|---|---|---|---|---|
| GF external | 250.058 | 300.875 | -50.817 (-16.9 %) | no: 7.545 m held |
| GF internal 0.15 | 159.697 | 181.720 | -22.023 (-12.1 %) | no: 1.525 m held |
| GF internal 0.20 | 50.320 | 32.800 | +17.520 (+53.4 %) | no: 2.65 m held |
| 1F external | 157.113 | 199.651 | -42.538 (-21.3 %) | no: 6.899 m held |
| 1F internal 0.15 | 179.237 | 211.418 | -32.181 (-15.2 %) | no: 11.061 m held |
| **1F internal 0.20** | **35.484** | **30.340** | **+5.144 (+17.0 %)** | **yes (gross)** |
| 2F external | 79.509 | 96.255 | -16.746 (-17.4 %) | no: 4.451 m held |
| **2F internal 0.15** | **11.780** | **11.100** | **+0.680 (+6.1 %)** | **yes** |
| 2F internal 0.20 | 32.444 | 30.340 | +2.104 (+6.9 %) | no: 1.287 m held |

Reconciled exactly, 2F internal 0.15 (one wall, 2F-W08, net): ours **10.020** vs his **7.020** m2 = +3.000 m2:
(1) gross +0.680 = length 3.10 vs 3.00 m (+0.10 x 3.70 = 0.37, our run to the centreline node, UP-WALL-GEOM-001) and
height 3.80 vs 3.70 m (+0.10 x 3.10 = 0.31; 4.20 - B3 0.40 by Q-60 A vs his one height per floor);
(2) deductions 1.760 vs 4.080 = -2.320: his 4.08 = 1.70 x 2.40 = D-2F-03 0.80 + D-2F-02 0.90; D-2F-02 stands in a
0.20 wall (2F-W05, census band 0.20) so it is deducted there, not here (2.16), and door height 2.20 (Q-55 C) vs his 2.40
on 0.80 (0.16). 0.37 + 0.31 + 2.16 + 0.16 = 3.00, no residual. Verdicts: height ENGINE_RIGHT under Q-60 A (RULE_DIFFERENCE
vs his method); length RULE_DIFFERENCE (centreline vs face, T-103); D-2F-02 wall allocation ENGINE_RIGHT (drawn band
0.20); door height RULE_DIFFERENCE (Q-55 C).
1F internal 0.20 (+5.144 m2): ours = lift-core walls 1F-W02 / W03 / W09 23.900 m2 (6.40 m) + stair wall 1F-W07 11.584 m2;
his 30.34 m2 is the same figure on 1F and 2F (one lift-core row copied per floor, T-143 finding 4). Which of our walls
his row covers is not given by his sheet: UNRESOLVED (his length / height split), never his number.
Everywhere else the comparison is not like-for-like while held length remains (held is missing, not 0); the T-143
finding stands that one height per floor misstates block area by 4-10 % per floor on this villa.

## 4. Held, unknown, missing (never 0)

- 43 walls net HELD (by cause in T108_BY_WALL.csv): 28 openings with no established area (21 window heads: T-201 READY
  would release most; main entrance; master bath door; arches; lift openings; P-GF-01), member CONFLICT / unprinted 2F
  beams / dome openings (36.319 m of held length, with GF-H01 0.70), annex datum (Q-54 B), lift tie beam (ST p.8 note 19).
- Outside the rows: P-1F-01 masonry above the S8.6 lintel 0 .. 4.992 m2; pool-court piers (T-154); masonry above / below
  the glazing of W02 / W03 / W17 (Q-69 B item 4); parapets 104.25 lm and street fence 8.20 lm (Q-65 C); T-stem overlap
  2.70 m3 (T-143) to deduct for a physical volume; D-12 thickness conflict (77.57 drawn vs 100.07 m3 at column thickness
  on 19 rows, T-143) never chosen.
- Black units, mortar / adhesive, pallets: T-176 (procurement) and the owner's Q-75 path.

## 5. Rule, test, lessons row (standard s.4)

- Rule proposal (any villa; provenance Q-60 A + Q-69 B + Q-73 + Q-60 supplier sheet; not a project fact): block area per
  wall = sum over member-above pieces of (storey height - member depth) x piece length, scaled to the physical run;
  a piece with no printed member depth is held, never defaulted; installed units only from a supplier face that exists in
  that thickness; atab never where a printed lintel schedule governs. Proposed as UP-MASONRY-AREA-001 v1.0.0 (new file).
- Tests: `tests/t108_masonry_area/test_masonry_area.py` (15: hand villa T108-B; adverse: held beam depth, nothing drawn
  above, held storey, mirror, pieces scaled, glazed line, schedule beats atab, atab too long / no bearing, 0.10 white has
  no 60 x 20 face, mm refused, HELD never summed, an opening larger than the known part does not falsely refuse) and
  `test_t108_alsenan_ledger.py` (ledger reproduces byte for byte; invariants).
- Lessons row proposed: 2026-10-23 | 3 block walls carried a height over a doorway no sample had read (coverage 0.38 ..
  0.67) | the member-above sampling ran on the wall band, and a free-end doorway inside the run is not on the band |
  every run reports its height coverage; under 0.8 the member over the uncovered part is read before the height is
  extended (any villa) | LOW_HEIGHT_COVERAGE flag in MASONRY_AREA_V1 + test_pieces_scaled_to_the_run | settled on 3 walls
  by own read, 1F-W25 open.

Files: `alsenan_t108.py` (`--check` reproduces), `T108_BY_WALL.csv` (75 rows), `T108_TOTALS_BY_FLOOR_TYPE_T.csv`,
`T108_VS_FREELANCER_BY_SECTION.csv`, `summary.json`.
