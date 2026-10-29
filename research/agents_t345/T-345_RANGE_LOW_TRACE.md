# T-345: the one UNEXPLAINED T-341 line, 1F porcelain L-b06400d4, traced to its cause (every villa)

Worker 1 (lane S), 2026-10-29. Research only: no engine, method, rule / knowledge version, registry, frozen file or
candidate line changed; nothing re-measured beyond re-running the merged piece STAIR_FLOOR_RESIDUE_V1 unchanged.
Development villa, not an accuracy claim. Drawings by Drive title only: "Alsenan chalet project" /
P7757_DXF_COMPRESSED.zip (DXF `ab54dd55`) and "ST7757 dxf.dxf" (`9f9d1179`).

## 1. The physical element and the question

Physical element: the +5.50 finished floor inside the open first-floor living / corridor / landing face
(engine face SITE-a95bf979baf4cfae, room 1F-R78C367), which the main dog-leg stair and the round stair pass through and
an outlined opening (void) cuts. ERS s.2.1 question: which physical pieces of that face are not porcelain floor, each
once, so that face - pieces = the line's net 33.711036 m2.

T-341 found: face 75.983002 - the line's list 31.113649 (treads 8.336981, void 16.005, flight below 6.771668) =
44.869353; the line starts from the range low 38.458536; 44.869353 - 38.458536 = 6.410817 m2, of which the held strips
D-13 / D-23 explain 0.520 and **5.890817 m2 were unnamed**.

## 2. Root cause (arithmetic, not a missing opening)

The line's net was set by ARCH_TAKEOFF_V3.0 piece STAIR_FLOOR_RESIDUE_V1 (T-116; `engine/source/arch_v30.py`
`stair_changes`, 537-620), which replaces measured_net, formula and calculation.inputs.v3_0 but **leaves the base line's
`deductions` list as it was**. That list is the ARCH_TAKEOFF_V2.x base (`engine/source/arch_measure.py` 359-372 from
`engine/source/arch_floor.py` `_treads` 51-62 / `split_face` 65-105). Two different tread measurements therefore sit on
one line: the list (base) and the net (piece). Nothing is unlisted physically: no opening, no fixed element other than
the stair, no threshold half, no room-face difference (face 75.983002 is the same in both; T-122 / Checker 00:58).

## 3. The 5.890817 m2, item by item (acceptance a), `t345_trace.py` on V3.0.22 `7199c8b6` (own run, 3,706 lines; = the T-341 file)

| # | Item (engine id) | m2 | Physical cause / rule | Source |
|---|---|---|---|---|
| 1 | own flight F5 (radial winder, 4 quads, 2 concave) | **+0.353736** | the base clips every tread quad as convex (`PP.region_area_in_convex`): F5's two concave winder quads are under-deducted (base 1.116981, exact union 1.470717) | TRACE_ROWS: F5 |
| 1a | own flight F2 | -0.000035 | 0.1 mm snap grid of the piece (3.770000 -> 3.769965), not a piece | TRACE_ROWS: F2 |
| 2 | flight of the plan below F4 | **-0.057558** | the base sums F1 + F4 + F6 one by one; F1 and F4 overlap by 0.057438 m2 inside the face (base: twice; piece: once, on F1) + 0.000120 grid | TRACE_ROWS: F4 |
| 2a | flight of the plan below F1 | +0.000075 | snap grid (1.981668 -> 1.981743), not a piece | TRACE_ROWS: F1 |
| 3 | VOID_RESIDUE R01 | 1.437249 | cell inside the printed opening touching the void (open to below; never floor) | piece cell |
| 4 | VOID_RESIDUE R02 | 0.597420 | the same, beside the flights below F1 / F4 / F6 | piece cell |
| 5 | STAIR_FOOTPRINT R03 | 2.119832 | dog-leg well: turn of the stair under the printed half landing 250 x 125, gap between the flights, well end inside the landing (T-122 R-NB 1.404 + R-GP 0.670 + R-LC 0.010 + slivers); stair, UP-STAIR-005 | piece cell |
| 6 | STAIR_FOOTPRINT R04 | 1.352454 | round-stair quarter landing inside the living rectangle (T-122 R-RQ; marble, size not printed: HELD on the stair side) | piece cell |
| 7 | STAIR_FOOTPRINT R05 | 0.057500 | round-stair arrival edge strip 1.15 x 0.05 beside F6 (T-122 R-RE) | piece cell |
| 8 | STAIR_FOOTPRINT R06 | 0.021884 | sliver along the radial flight F5 (1.1497 x 0.0345) | piece cell |
| 9 | STAIR_FOOTPRINT R07 .. R13 | 0.008260 | 7 slivers 0.0011 - 0.0018 m2 along the curved flight F1 / F4 (T-116 note *) | piece cells |
| | **sum** | **5.890817** | residual **0.000000** m2 | |

Check: own +0.353701 (= piece 8.690682 - base 8.336981), below -0.057483 (= 6.714185 - 6.771668); 0.353701 - 0.057483 + 2.034669 (VOID_RESIDUE) + 3.559930 (STAIR_FOOTPRINT) = 5.890817. The piece's own
conservation: face 75.983002 - void 16.005 - own 8.690682 - below 6.714185 = 44.573135 (free floor ledger) vs exact
geometry 44.573006 (BALANCED, 0.000129 m2 grid noise); 44.573135 - 2.034669 - 3.559930 - held 0.520 = 38.458536 = range
low, exactly.

## 4. FILL row for T-246 (acceptance b): `TRACE_ROWS_T345.csv` / `TRACE_LINES_T345.csv`

L-b06400d4: **TRACED**. Gross restated 33.711036 -> **75.983002** (the face, `calculation.inputs.v3_0.conservation`),
and the list replaced (not appended: the base tread rows are superseded by the piece's) by FILL_ROWS rows, each once:

    75.983002 - [void 16.005 + own F2 / F3 / F5 8.690682 + below F1 / F4 / F6 6.714185
                 + VOID_RESIDUE R01 / R02 2.034669 + STAIR_FOOTPRINT R03 .. R13 3.559930
                 + D-13 tread 0.345 (NOT_FLOOR, T-269) + 1F landing split out 4.9225 (Q-66 B)] = 33.711036 = net

D-13 nosing 0.0575 and D-23 band 0.1175 are FLOOR by T-269 (in the net, never deducted; the nosing then leaves with the
landing 4.9225 = 4.875 - 0.010 + 0.0575). Applied in memory to a copy (`apply_trace`, what T-246 does): T-330 on the line NOT_SUMMING -> **OK** (summary.json).
The 22 rows: 6 flights, 1 void (V01), 13 residue cells, D-13 tread, landing split-out.

## 5. The same trace on every other floor line (acceptance c): `FLOOR_LINE_SURVEY_T345.csv`

All 52 V3.0.22 floor-finish lines (GF 31, 1F 16, 2F 5) surveyed: only two faces hold stair flights or a void.
- **1F L-b06400d4** (6 flights, 1 void): the only line whose net STAIR_FLOOR_RESIDUE_V1 set (scope
  STAIR_PASSES_THROUGH_SLAB); traced above. The piece record recomputed from the V2.9 run equals the line's own
  calculation.inputs.v3_0 aggregates (void, residue, footprint, held, floor before residue) to 0.000005, so the trace
  is the line's own geometry, not a re-measure.
- **GF L-7625f35c** (4 round-stair flights at their foot, no void): the piece keeps it (LOWEST_STOREY_NOT_ASSESSED);
  its list (treads 8.194412) is the base list and its net the base net, so list and net come from ONE measurement and
  T-341 closed it (RECONCILED_GROSS_RESTATED, residual 0). It does NOT hide this cause. The exact union is 8.194304
  (-0.000108, grid); its 15.437 m2 of not-assessed cells around the rising stair are a separate, already-named lowest-
  storey question (T-116), not a list defect.
- The other 50 lines: no flight, no void inside the face (the piece leaves them as they are).
So the cause (a piece-set net over a base list) occurs on exactly one Alsenan line; on another villa it occurs on every
floor face the piece changes, which the survey finds by `piece_applied`.

## 6. Owner manual method and drawing method side by side

Owner manual (Q-56 A rows, printed sizes; T-122 / T-240): living 22.200 + corridor 7.044 + connector 4.469 = 33.713
porcelain; landing 4.875 marble (Q-66 B). Drawing (V3.0.22 line, this trace): 33.711036 porcelain, landing 4.9225.
Difference -0.002 m2 (-0.006 %): the 0.010 well end under the balustrade and the 0.0575 nosing band moved with the
landing (T-269), already named by T-122 / T-240. Freelancer: one 38.96 m2 living row incl. the landing (not split):
porcelain + landing 38.633536 vs 38.96 = -0.326 m2 (-0.84 %), RULE_DIFFERENCE on the landing finish (T-240; not
re-judged). This trace changes no quantity: the net 33.711036 stays as the Checker verified it (T-269 / T-240).

## 7. Verdict proposals

- L-b06400d4 net 33.711036: unchanged, ENGINE_RIGHT (Checker T-269 / T-240); the T-341 UNEXPLAINED status is a LIST
  defect, not a quantity defect: ENGINE_LIST_STALE (base list carried under a piece-set net).
- Base list tread rows 8.336981 / 6.771668: ENGINE_WRONG for the deduction list (concave winder clipped, overlap twice);
  they are not a quantity of any exported line once T-246 takes this fill.

## 8. What is missing / uncertain

- The engine fix belongs to the method, not to research: a future method version should write the piece's list when it
  sets the net (arch_v30.stair_changes). Not done here (no method change authorised by this row).
- R04 (round-stair quarter landing 1.352454) and R03 (dog-leg well) are deducted from porcelain correctly; their marble
  areas belong to the stair ledger (held there), not to this line.

## 9. Lesson (proposed for ENGINEERING_REASONING_STANDARD s.7)

| 2026-10-29 | the 1F porcelain line's list did not explain its net (5.891 m2 'unnamed') | a method piece replaced the net from an exact geometry while the line kept the base method's deduction list (convex clipping, flight overlaps summed): two measurements of one stair on one line | a piece that changes a line's net must restate the line's list from the same geometry; a list is traced by recomputing the piece, never by fitting the gap (every villa) | tests/t345_trace (normal 2 + geometry 4 incl. mirror / rotation / mm; adverse 4) | trace DONE; consumption T-246; engine fix = a future method version |
