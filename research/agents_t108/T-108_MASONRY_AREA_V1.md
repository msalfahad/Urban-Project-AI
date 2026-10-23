# T-108: MASONRY_AREA_V1, block m2 / m3 / installed white units per wall run (development villa run)

Worker 2, r1 2026-10-23 06:44 - 06:57 UTC; r2 (rework of the Checker rejection 07:13) 07:41 - 08:40 UTC. Lane A, gate 2. New opt-in module `engine/source/masonry_area_v1.py`
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

## 0. r2: what the rejection found and what changed

Checker 07:13 (gates e + h): r1 took each run's length from T-143's hand column L2a, which carries every T stem to the
through-wall centreline, so the stem piece (half the through wall) was counted in two walls (owner Q-69 B: never count
masonry in two segments). The Checker's own read of 2F-W08: 3.000 m to the face, not 3.10 m. r2:

- **Length source** (alsenan_t108.py `build`): every row now takes the Q-69 B length of its MASONRY_CENTRELINE_V2 run
  (T-125 / T-169, merged and verified): the V2 architectural run (doors, windows, passages stay IN the run; Q-73 deducts
  their area) less only the full-height glazed lines the census takes out (W02 = engine OP-019 6.3316 m on GF-W11; the
  1F concave bay glazing 3.5788 m). Input `T108_V2_RUN_LENGTHS.csv`, written by `t108_v2_lengths.py` from one V2 run on
  P7757.dxf (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip) on this branch's code; per-floor / family sums
  reproduce the merged T-125 totals (test). The T-143 hand length stays beside it as a comparison column with its delta
  and the T-125 verdict.
- **One physical run, one row**: 1F-W14 and 1F-W15 are one V2 run (WB-FL0022-FL0023, 4.0157 m) with the doorless
  1.30 m opening P-1F-01 inside it (the hand runs stopped at it); r2 merges them and deducts P-1F-01 in the run (Q-73);
  its head is not drawn on any sheet (T-201), so this row's net is HELD with bounds 10.971 .. 16.223 m2 (r1 counted
  the two hand pieces 11.615 m2 and carried P-1F-01's masonry outside every row).
- **No V2 run** (GF-W30, GF-W37, GF-H02): hand length kept as comparison only (`length_source HAND` caps the status at
  HELD); all three were HELD in r1 too.
- **Held ends** (new): where the physical module could not close an end (no clean T or L, the 45 deg corners; T-125
  verdict UNRESOLVED) the measured run is established and the rest is a HELD bound (0 .. max more, never added): GF-W13
  0.200, GF-W20 / W21 / W31 0.137, GF-W32 0.278, GF-W33 0.217 (hand 0.217 > module 0.137), GF-W34 0.256 m; and the 1F
  bay band 0.477 m on 1F-W25 (below). Total 1.839 m, 0 .. 7.460 m2.
- **T-stem overlap**: 0 by construction (a V2 stem stops on the face). The r1 'T-stem overlap 2.70 m3 HELD' was this same
  double count, not a held item: removed.
- **Module** (engine/source/masonry_area_v1.py `check_length_source`, `wall_gross`): optional `length_source`
  (PHYSICAL_MODULE / HAND), `ends` (a T_STEM end measured to the CENTRELINE is refused, ValueError), `held_end_max_m`
  (+ why) reported as a HELD bound; inputs without them behave exactly as r1 (test).

1F bay (1F-W00 + 1F-W01 + 1F-W25, all under CB12, one height 3.45 m): hand masonry 6.647 + 0.853 + 0.537 = 8.037 m;
V2 6.5708 + 0.8208 + 0.1685 = 7.5601 m; difference 0.4769 m = 0.443 m glass basis (V2 and the census take the glazing
3.579 m on the glass mid circle carried to the centrelines; the hand row subtracted the drawn glazing arc 3.136 m, so its
L2a 0.537 is not its own L1 - L3 = 0.094) + 0.034 m arc vs chord (T-125 row F, UNRESOLVED). Which ends of the bay are
block is not settled by the plan alone: V2's 0.1685 m (the drawn stub 1F-STUB-001) is established, 0 .. 0.4769 m
(0 .. 1.645 m2) HELD on 1F-W25 for an elevation / section read.

## 2. Development villa (Alsenan) through the module (r2)

Inputs: V2 run lengths (above), T-143 members above each piece (heights, merged), T-175 opening hosts (census r3 of
T-198). The module recomputes each of the 127 member-above pieces' heights from the storey heights (GF 4.50, annex 4.00
PROVISIONAL, 1F 4.20, 2F 4.20) and the schedule depths: **max difference vs T-143's heights 0.000 m** (unchanged; the
Checker's 2F-W08 height 3.80 agrees). Gross / net now differ from T-143 / T-175 by design (the length): 70 rows, sum
|d gross| 20.763 m2, of which 4.608 is the P-1F-01 run (now in the gross) and the rest the stems and ends below.

Length, r2 vs the hand run, on the 71 rows with a V2 run: 285.188 vs 288.345 m (-3.157 m): ENGINE_RIGHT rows (T stems
stop on the face; 24 rows in all; GF-W29 doorway to the drawn face +0.126; 1F-W14 + W15 +1.141 with P-1F-01 in the run; 1F-W20
crossing counted once) -1.714 m; T-125 UNRESOLVED 45 deg ends -0.842 m (held as bounds); rows within 0.05 m or without a
T-125 verdict -0.601 m (the 1F bay band -0.477 (held as a bound), GF-H01 -0.100 (row HELD), 1F-W21 -0.025).

| Floor | Gross, known pieces (DC / HELD-provisional or partly held) | Held length + held ends | Net DRAWING-CONFIRMED | Net ASSUMED — OWNER-APPROVED (door height Q-55 C) | m3 of the established net | Walls with net HELD | r1 established net (DC + AOA) |
|---|---|---|---|---|---|---|---|
| GF | 451.791 m2 (213.329 / 238.463) | 13.220 m + 1.362 m | 117.641 m2 (10 walls) | 38.221 m2 (4) | 26.990 | 26 | 160.687 |
| 1F | 370.180 (292.548 / 77.632) | 17.618 m + 0.477 m | 92.040 (9) | 36.733 (3) | 21.303 | 13 | 144.221 |
| 2F | 123.226 (61.376 / 61.849) | 5.697 m | 43.136 (3) | 9.640 (1) | 10.073 | 5 | 53.156 |
| **All** | **945.197** (r1 955.643) | **36.535 m + 1.839 m** | **252.817 (22)** | **84.595 (8)** | **58.366** (r1 61.532) | **44** (74 rows) | 358.063 |

Established net 337.412 m2 (r1 358.063: -20.651 m2, -5.8 %) = -11.615 m2 of 1F-W14 / W15 moved to HELD with P-1F-01
(bounds 10.971 .. 16.223) and -9.041 m2 on 19 rows that keep a net (17 by length: stems to the face, 45 deg ends, the 1F bay; GF-W29
+0.547 the other way; GF-W11 / GF-W28 +0.001 rounding of the V2 run); 0.005 m2 total rounding. Per row in T108_BY_WALL.csv (columns
d_length_vs_hand_m, t143_gross_m2, t175_net_m2). Net candidate on a provisional gross (annex,
not a quantity) 115.448 m2 (r1 120.774).

By type (T108_TOTALS_BY_FLOOR_TYPE_T.csv): established net white 0.20 = GF 10.050 (4.460 DC + 5.590 AOA), 1F 15.833,
2F 21.476 = **47.359 m2 -> 303.1 units 62.5 x 25 or 394.7 units 60 x 20** (r1 48.739 -> 311.9 / 406.2; -1.380 m2 = 1F-W25
-1.272 (bay) and 1F-W01 -0.111); installed, no waste; type ASSUMED — OWNER-APPROVED (outer white, Q-60 fallback).
Black: 290.052 m2 established net (r1 309.324), units HELD (T-176). Atab: NOT APPLICABLE on every opening (ST7757.pdf
p.13 LINTEL SCHEDULE governs).

### Height coverage (r1, unchanged)
GF-W27 / GF-W29 (slab 0.16 over the free-end doorway) and 1F-W12 (B4 continues over 0.988 of the 1.089 m gap): own read
of ST7757 dxf.dxf roof-slab plans in r1 (column-outline translation GF 30 / 30, 1F 20 / 20, residual <= 0.004 m), same
member, no height change. 1F-W25: one piece under CB12 (0.17 m) over the 0.1685 m stub: coverage of the run is full.

## 3. Engine vs freelancer (his BLK rows, T143_TOTALS_VS_FREELANCER.csv), units first

| Floor / his section | Ours gross (known) | His gross | Diff | Like-for-like? |
|---|---|---|---|---|
| GF external | 250.059 | 300.875 | -50.816 (-16.9 %) | no: 7.545 m held |
| GF internal 0.15 | 152.025 | 181.720 | -29.695 (-16.3 %) | no: 2.687 m held (incl. ends) |
| GF internal 0.20 | 49.707 | 32.800 | +16.907 (+51.5 %) | no: 2.850 m held |
| 1F external | 155.468 | 199.651 | -44.183 (-22.1 %) | no: 7.376 m held |
| 1F internal 0.15 | 179.491 | 211.418 | -31.927 (-15.1 %) | no: 10.719 m held |
| **1F internal 0.20** | **35.221** | **30.340** | **+4.881 (+16.1 %)** (r1 +5.144) | **yes (gross)** |
| 2F external | 79.509 | 96.255 | -16.746 (-17.4 %) | no: 4.451 m held |
| **2F internal 0.15** | **11.400** | **11.100** | **+0.300 (+2.7 %)** (r1 +0.680, +6.1 %) | **yes** |
| 2F internal 0.20 | 32.317 | 30.340 | +1.977 (+6.5 %) | no: 1.246 m held |

Reconciled exactly, 2F internal 0.15 (one wall, 2F-W08; Checker's own read 07:13 = ours): ours **9.640** vs his
**7.020** m2 = +2.620 m2: (1) gross +0.300 = length 3.00 = his 3.00 m (11.10 / 3.70; r1's +0.37 'centreline' item was the
double count: FREELANCER_RIGHT on the length) and height 3.80 vs 3.70 m (+0.10 x 3.00 = 0.30; 4.20 - B3 0.40 by Q-60 A
vs his one height per floor: ENGINE_RIGHT under Q-60 A); (2) deductions 1.760 vs 4.080: his 4.08 = 1.70 x 2.40 = D-2F-03
0.80 + D-2F-02 0.90; D-2F-02 stands in the 0.20 wall 2F-W05 (census band 0.20): 2.16 not here (ENGINE_RIGHT), and door
height 2.20 (Q-55 C) vs his 2.40 on 0.80: 0.16 (RULE_DIFFERENCE). 0.30 + 2.16 + 0.16 = 2.62, no residual.
1F internal 0.20 (+4.881 m2): lift-core walls 1F-W02 / W03 / W09 23.900 m2 (6.40 m, unchanged) + stair wall 1F-W07
11.321 m2 (3.220 m to the face, r1 3.295); his 30.34 m2 is the same figure on 1F and 2F (one lift-core row copied, T-143
finding 4): which walls his row covers is UNRESOLVED (his split), never his number.
Everywhere else not like-for-like while held length remains (held is missing, not 0).

## 4. Held, unknown, missing (never 0)

- 44 rows net HELD (by cause in T108_BY_WALL.csv): openings with no established area (window heads: T-201 MERGED
  5dade783 after this branch's r1 base; feeding its heads is the next piece, not in this narrow rework), P-1F-01 head
  (NOT DRAWN, T-201), member CONFLICT / unprinted 2F beams / dome openings (36.535 m of held length incl. GF-H01 0.60),
  annex datum (Q-54 B), lift tie beam (ST p.8 note 19).
- Held ends and the 1F bay basis: 1.839 m, 0 .. 7.460 m2 (section 0).
- Outside the rows: pool-court piers (T-154); masonry above / below the glazing of W02 / W03 / W17 (Q-69 B item 4);
  parapets 104.25 lm and street fence 8.20 lm (Q-65 C); D-12 thickness conflict (T-143) never chosen.
- Black units, mortar / adhesive, pallets: T-176 (procurement) and the owner's Q-75 path.

## 5. Rule, test, lessons rows (standard s.4)

- Rule proposal UP-MASONRY-AREA-001 v1.0.0 (new file, any villa; provenance Q-60 A + Q-69 B + Q-73 + Q-60 supplier
  sheet): block area per wall = sum over member-above pieces of (storey height - member depth) x piece length, applied
  to the PHYSICAL run of the verified physical-length module (a T stem stops on the face; a hand run is a comparison
  column, never the input); an end the module cannot close is a HELD bound; a piece with no printed member depth is held,
  never defaulted; installed units only from a supplier face that exists in that thickness; atab never where a printed
  lintel schedule governs.
- Tests: `tests/t108_masonry_area/test_masonry_area.py` (r1 15 + r2 6, fixture T108-C not Alsenan: stem to the face
  11.40 / 9.64 m2; adverse: the same stem to the centreline (3.10 m) refused; a HAND length capped at HELD and never
  summed; a held end reported as a bound, not added; unknown source / end kind refused; unstated source unchanged) and
  `test_t108_alsenan_ledger.py` (byte-for-byte reproduction; every row's length = its V2 runs; 2F-W08 3.000 / 11.400 /
  9.640; stem rows shorter than the hand; V2 inputs reproduce the merged T-125 totals; no V2 run in two rows).
- Lessons rows proposed (s.7): 2026-10-23 | block area on hand runs that carry T stems to the centreline (r1 358.063 vs
  r2 337.412 m2 established) | the hand truth and the physical length were taken as one | the physical length comes from
  the verified physical module; a hand run is a comparison column, never the input (any villa) | tests/t108 r2
  (centreline stem refused, HAND capped) | fixed in r2. And: 2026-10-23 | 3 block walls carried a height over a doorway no
  sample had read | member-above sampling on the wall band misses a free-end doorway | report height coverage; under 0.8
  read the member over the uncovered part (any villa) | LOW_HEIGHT_COVERAGE + test_pieces_scaled_to_the_run | settled.

Files: `t108_v2_lengths.py` (V2 run -> `T108_V2_RUN_LENGTHS.csv`; `--check` on the run file), `alsenan_t108.py`
(`--check` reproduces), `T108_BY_WALL.csv` (74 rows), `T108_TOTALS_BY_FLOOR_TYPE_T.csv`,
`T108_VS_FREELANCER_BY_SECTION.csv`, `summary.json`.
