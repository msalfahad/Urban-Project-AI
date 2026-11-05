# T-526: masonry run ends that abut RC columns (F-T520-1), R-T526-1 COLUMN_END_CENSUS_V2

Worker 1, lane S, claim 2026-11-05 13:24 UTC, base engine 046b9ad3 (candidate of record unchanged; released default
V2.9 + route G untouched). Research only: `end_census_v2.py` (project-agnostic rule), `t526_extract.py` (drawing reader,
inputs outside the repository), `t526_alsenan.py` (training-villa builder on the merged ledgers' own code, `--check`
reproduces), `out/` (ids, classes, mm gaps, covers; no drawing coordinate), `tests/t526_column_end_census/` (23 tests).
No merged folder, engine, rule-store, registry or candidate file changed. Drawings cited by Drive folder and title only:
'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha ab54dd55) and 'ST7757 dxf.dxf' (sha 9f9d1179).

## 1. Physical element and engineering question (ERS s.2.1)

The vertical joint where the last block of a masonry run meets an RC column face. It carries the perimeter joint mortar
(R-T520-1), a sharmat tie per tie level (R-T355-1/-3), a crack-mesh strip per finished side (T-317) and ends the run's
clear length. Question: which drawn element terminates each of the 4 F-T520-1 ends, and is the omission systematic?

## 2. Answer: the omission is the census RULE, not a drawing layer

- Every one of the 4 ends meets a column drawn on BOTH drawings: the architectural outline (P7757, wall stage capture)
  and the structural S-COL.BON outline (ST7757), matched by one translation per storey (GF 30/30, 1F 20/20, 2F 9/9
  architectural columns, residual 0.0000 m). Gap 0.0 mm, full-thickness cover 1.0000 on all four.
  1F-W09 end 0 -> COL-1F-37 (C1, 0.20 x 0.50, ST 682); 1F-W23 end 0 -> COL-1F-57 (P.C 20x70, 0.70 x 0.20, ST 66A);
  2F-W01 end 0 -> COL-2F-53 (C1, ST 421); 2F-W08 end 0 -> COL-2F-54 (C2, 0.20 x 0.50, ST 41B) (T-119 ledger ids / marks).
- Cause (V1 rule): T-274 cuts a run at every column outline the run CROSSES; T-355 R-T355-3 `junctions` and T-317
  `joints` / `joints_to_soffit` then list a junction only between two CONSECUTIVE pieces of one run (BLOCK / COLUMN). A
  column the run ENDS ON (standing in the met wall of a T, at an L corner, or beyond a free end) is never a piece of the
  run, so its junction is never listed. The 12 V1-missed ends are 7 T_STEM and 5 FREE_END run ends (V2 run end types;
  the L ends carry a 0.075 / 0.10 m extension INTO the corner column, which makes it a run piece): the blind spot is
  the end condition, not a layer, an angle or a tolerance (gap 0.0 mm on all 12).
- Structural-only columns: ST7757 carries 4 outlines with no architectural column (GF 31B / 329 / 386, 1F 77B). Only
  31B touches a census run (GF-W07, stations 0.400 .. 0.600) and it lies wholly inside the architectural column piece
  0.000 .. 0.800 of that run (a second rectangle of the same C8 column): no masonry moved. None meets a run end.

## 3. Rule R-T526-1 (new version of the junction census; every villa; provenance F-T520-1, T-526)

V2 junctions = V1 interior junctions + one END junction per run end classified from the drawings by what lies beyond
the end face (strip [gap, gap + 0.02 m] x full thickness, 0.5 mm inset; search 0.05 m; arch + structural-only outlines):
COLUMN (cover >= 0.999, gap 0) and COLUMN_WITHIN_JOINT (0 < gap <= the 10 mm joint): a junction, run length unchanged;
GAP_HELD (joint < gap <= 0.05 m): HELD naming the void; PARTIAL_COLUMN (0 < cover < 0.999: offset or angled column):
HELD with the contact width; NO_COLUMN (incl. zero-area corner touch): V1's masonry class stands; COLUMN_PIECE_IN_RUN:
V1's own junction, never twice. Units in metres (mm refused); outlines None refused (never 'no column').

## 4. Full Alsenan census re-run (END_CENSUS_V2_T526.csv: 72 runs, 140 ends probed, 2 curved runs not probed)

COLUMN_PIECE_IN_RUN 54, NO_COLUMN 73, COLUMN 12 (all missed by V1), PARTIAL_COLUMN 1 (HELD). Every V1 listing of a
COLUMN_PIECE_IN_RUN end was found in both SHARMAT_T355 and JOINTS_T317 except GF|WB-FL0028-FL0029 (t 0.40, no register
wall: outside the masonry census, not a junction omission).

Per-end effect of the 12 missed ends + 1 held (MISSED_ENDS_T526.csv; deltas vs the V1 censuses, sign +):

| End | Column (T-119 / mark / ST) | length m / m2 / blocks | mesh m.l owner / drawing | ties nr | perimeter mortar m3 |
|---|---|---|---|---|---|
| 1F-W09 e0 0.20 T | COL-1F-37 C1 682 | 0 / 0 / 0 | +6.70 / +7.40 | +6 | +0.007021 (0.003334 -> 0.010355) COMPUTED |
| 1F-W23 e0 0.15 T | COL-1F-57 P.C 20x70 66A | 0 / 0 / 0 | +6.70 / +7.20 | +6 | +0.001792 figure (0.15 module HELD, T-506) |
| 2F-W00 e1 0.20 T | COL-2F-55 C9 418 | 0 / 0 / 0 | +6.70 / +7.40 | +6 | HELD 0 .. 0.007039 (wall outside T-520) |
| 2F-W01 e0 0.20 T | COL-2F-53 C1 421 | 0 / 0 / 0 | +6.70 / +7.40 | +6 | HELD 0.007114 - 0.001852 b_r (D-39) |
| 2F-W08 e0 0.15 F | COL-2F-54 C2 41B | 0 / 0 / 0 | +6.70 / +7.40 | +6 | HELD 0 .. 0.002015 - 0.001389 b_r (D-39, other end O) |
| GF-W03 e0 / e1 0.20 F | COL-GF-23 C8 380 / COL-GF-22 C5 374 | 0 / 0 / 0 | HELD | HELD | HELD (BM-GF-057 depth not printed) |
| GF-W09 e0 0.20 T | COL-GF-07 C1 341 | 0 / 0 / 0 | HELD | HELD | HELD (lift tie beam, ST p.8 n.19) |
| GF-W25 e0 0.15 T | COL-GF-29 C3 350 | 0 / 0 / 0 | HELD | HELD | HELD (annex datum Q-54 B) |
| GF-W10 e1 / GF-W18 e0 0.20 F white | COL-GF-01 C4 335 / COL-GF-28 C 34D | 0 / 0 / 0 | HELD | HELD (Q-60) | HELD (thin-bed, Q-60) |
| GF-W16 e0 0.20 T white | COL-GF-30 C 359 | 0 / 0 / 0 | +7.40 / +7.30 | HELD (Q-60) | HELD (Q-60) |
| GF-W20 e1 0.15 T | COL-GF-02 C5 332 | HELD (contact 0.0195 of 0.150 m) | HELD | HELD | HELD |

Totals measured: length 0 m, blockwork 0 m2, blocks 0 nr (every end face IS the column face, gap 0.0 mm; Q-73 / Q-75
unchanged); crack-mesh V joints +40.90 m.l (owner band) / +44.10 m.l (drawing band) on 6 ends; sharmat ties +30 nr on 5
black ends; perimeter mortar COMPUTED 0.20 m +0.007021 m3 (1F-W09), the others HELD with expressions / bounds above.
T-520's own totals do NOT move: T-520 already read these 4 ends from the drawing (END_CONDITIONS_T520); the new
information is (a) the 8 further ends, (b) the T-355 / T-317 deltas, (c) the structural identity of every column.
Plaster return / corner bead at these ends: none (the column is as wide as or wider than the wall: internal corners
only, covered by the mesh strip rows above; no external corner is created).

## 5. Verdicts

Freelancer (blockwork workbook): no tie, mesh or mortar row (T-355 / T-367) -> RULE_DIFFERENCE, no numeric verdict.
Census V1 vs V2 at the 12 ends: ENGINE_WRONG (V1) -> V2 proposal, hand proof per end class in tests (fixture P526: a
run ending on a column drawn only on the structural sheet: 0 -> 1 junction, ties 4, mesh 2 x 2.70 m, perimeter
0.92625 x 0.20 x 0.010 x 2.79 = 0.005168475 m3). Not wired: the T-355 / T-317 / T-498 ledgers need a version that reads
END_CENSUS_V2 (lane S / I package).

## 6. Lessons row (ERS s.7, proposed)

| 2026-11-05 | 12 masonry run ends that stop on an RC column face were missing from the tie, mesh and perimeter-joint censuses |
the junction census listed only BLOCK / COLUMN boundaries between consecutive pieces of one run; a column the run ends
on is never a piece | classify every run end from the drawings (both sheets) by what lies beyond its end face, within
one joint, full thickness; partial or gapped contact HELD by name (every villa; R-T526-1) | tests/t526_column_end_census
(structural-only column at the end; corner touch none; offset partial HELD; 5 mm gap inside the joint; 15 mm HELD) |
PROPOSED |

## 7. For the Checker (re-measure 2 ends from the DXF)

- 1F-W09 end 0 (run WB-FL0024-FL0025, T-stem end): the column outline beyond the end, P7757 1F plan, matched to ST7757
  S-COL.BON 682 (C1 0.20 x 0.50): gap 0, cover 1; perimeter (3.80 - 0.01) x 0.0018525 = 0.007021 m3.
- 2F-W08 end 0 (run WB-FL0024-FL0025 on 2F, free end): ST7757 S-COL.BON 41B (C2 0.20 x 0.50), the 0.15 wall ending on
  its 0.50 face: gap 0, cover 1; ties 6 (top 3.80 on T-317's 2F basis), mesh 2 x 3.70 m (drawing band).

Reproduce: `t526_extract.py <scratch> <ST7757.dxf>` (scratch from research/agents_t125 + agents_t274/t274_runs.py), then
`t526_alsenan.py --check`.
