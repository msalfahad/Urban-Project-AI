# T-129 Main-stair arrival landings counted once: first floor (Q-66 B) and second floor (Q-70 A conditional), Alsenan

Worker 2, 2026-10-20. Read-only, NO REPO CODE (research files only; no engine, tools, rules or released quantity
changes). Inputs kept in the session scratchpad: Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip (DXF sha256
ab54dd55..., one ARCH_TAKEOFF_V2.9 run, the same pickle T-113 / T-116 / T-122 used), Alsenan_Architectural_P7757_Pages_05-06
(page 5, second floor plan, read at 400 dpi), p7757_arch_sheet10.pdf (section A-A), ST7757.pdf pages 4, 5 and 6 (ground,
first and second floor roof slabs). First-floor rows: the T-122 partition (agents/task-T-122 f85fe97, re-run unchanged in
this session: same 22 rows, 75.983 m2). Run:
`alsenan_arrivals_once.py --dxf <P7757.dxf> --v29 <pickle> --rows-1f <LIVING_1F_ROWS_Q66B.csv> --out <dir>`
(`--selftest` runs the synthetic case alone). Output in this folder: `ARRIVALS_ONCE_LEDGER.csv` (2F rows with polygons, then
the 1F rows of T-122) and `arrivals_once_summary.json`. Local metres from the 2F stair face's south-west corner (x east
across the stair, y north into the stair).

## 1. Result in engineering terms (m2)

| Item | Freelancer | Released engine V2.9 | Owner manual (printed sizes) | Drawing-derived (CAD) | Status |
|---|---|---|---|---|---|
| 2F arrival landing 250 x 195, marble (Q-70 A) | in "corridor" 7.70 (porcelain) | not measured (face typed stair; landing line HELD 0 .. 11.725) | **4.875** | 4.8075 body (+0.0675 beyond the drawn slab edge, +0.0575 east-lane sliver to the top riser) | MEASURED; finish marble: owner condition MET (section 2) |
| 2F area beyond the stair width, porcelain | (same 7.70 row) | not measured | **2.500** (200 x 125) | 2.500 | MEASURED |
| 2F "stair lobby 450 x 195" of the finish table (DF-2F-LOBBY) | 7.70 | - | 8.775 is NOT a drawn area: 7.375 | 7.375 | **CORRECTION -1.400** (section 3) |
| 1F arrival landing (Q-66 B, T-122) | in living 38.96 (porcelain) | in living 44.869 (porcelain) | 4.875 | 4.865 | MEASURED (T-122) |
| 1F porcelain (T-122) | 38.96 | 44.869 | 33.713 | 33.594 .. 33.711 HELD range | unchanged by this run |
| Stair marble, finish table + 2 arrivals | 295.44 all stairs (main stair landings 6.2) | - | **49.235** (39.485 + 4.875 + 4.875) | - | sum CONFIRMED; once-only **48.515 .. 49.235 HELD** (section 5) |
| Engine tread marble / steps of the 1F -> 2F lower flight drawn again on the 2F plan | - | **3.45 m2 + 11.5 lm counted twice** (6.90 + 23.0 under the second plan reading) | 0 | 0 | ENGINE DEFECT (section 6) |

Owner candidates of Q-70 A, checked: lobby porcelain 3.900 -> **2.500** (the 8.775 it starts from holds 1.400 m2 of wall,
column and shaft); stair marble 49.240 -> **49.235** (39.49 was 39.485 rounded) as a sum of lines, of which up to 0.72 m2
may be counted twice inside the flight rows (HELD until the flight-by-flight ledger).
Freelancer vs drawing on the same 2F area: 7.70 vs 7.375 (+0.325 m2, +4.4 %; his row gives no dimensions, so the 0.325 is
not traceable). After Q-70 A his basis would leave 7.70 - 4.875 = 2.825 porcelain vs 2.500 (-0.325, -11.5 %):
RULE_DIFFERENCE on the landing finish (he tiles both arrival landings in porcelain: 1F "living" 38.96, 2F "corridor"
7.70; his main-stair landing line is 6.2 m2 vs 1.5 + 3.125 + 4.875 + 4.875 = 14.375 here).

## 2. Owner condition of Q-70 A: does the drawing establish the 2.50 x 1.95 area as the main-stair landing? YES

Five independent drawing facts, each re-read in this run (summary keys in brackets):
1. **The 195 is a stair dimension, not a room dimension.** It is the last member of the stair's own interior chain
   120 + 330 + 195 = 645 (the 6450 compartment dimension), drawn inside the stair width at x 0.86 (DXF dimension
   entities, `printed_dimensions_found`: 1950, 3300, 1200, 6450, 2500 each found once; PDF page 5 prints the same chain).
2. **There is no "stair lobby".** Inside the 4.50 x 1.95 area the drawing prints only the level "+9.70", the dimension
   texts 450 / 195 / 125 / 180 / 20 and a wall-thickness "8" (`texts_in_arrival_and_lobby_area`); no room name, in the DXF
   or on PDF page 5. The name "stair lobby (printed 450 x 195)" came from the T-088 table, which read two separate
   dimensions as one room. So Q-70's premise "a printed, named lobby" does not hold.
3. **The arriving flight ends at its edge.** The walk line (layer ST) of the first-to-second-floor stair ends with its
   arrowhead at (1.925, 2.000), in the east lane, 0.05 beyond the 195 line (`walk_line_arrow_tips_local`); the east
   flight's drawn treads run 2.30 .. 5.30, and section A-A's 12 risers (owner Q-46 A) give 11 goings x 0.30 = 3.30 from
   5.30 down to exactly 2.00, the arrowhead.
4. **It is the first-floor landing one storey up.** T-122's printed landing rectangle shifted by the engine's plan-to-plan
   offset (dx -44.852655 m, 7 of 9 columns) coincides with the 2F rectangle: symmetric difference 0.000000 m2
   (`stacking_1F_landing_onto_2F`). Same walls and the same 195 and 120 / 10 / 120 dimensions; on both floors a door
   opens in the south wall of this area (1F opening x 0.09 .. 1.09, 2F x 0.42 .. 1.42), so on both it is also the way
   to the outside door: the first-floor case the owner ruled marble (Q-66 B) is the same arrangement.
5. **The area beyond the stair width is a different space.** It is 1.25 deep (the 1250 dimension, text "125"), not 1.95:
   the wall of the shaft (y 1.25 .. 1.45) and a column (x 2.50 .. 2.70, y 1.25 .. 1.75) close it. So the floor in front of
   the stair is an L: the stair's own 2.50 x 1.95 plus 2.00 x 1.25.
Structural cross-check: the arrival area lies in the ordinary floor-slab panel south of beam B23 (ST7757 p.5, first floor
roof slab, 5 T10/m), not in the "T 16" stair panel (8 T16/m, B3 "with stair" to B23); the first-floor landing likewise lies
south of B20 (p.4). Concrete is therefore counted once, in the floor slab; stair concrete under owner Q-47 A holds only the
two turn landings (1.20 x 1.25 and 2.50 x 1.25), so no arrival landing is in stair concrete. (The beam's exact position
against the 195 line is not measured here: lane S, T-111.)
No stair rises above the second floor: the second-floor roof slab (p.6) is a solid T 18 slab ("WATER TANK PLACE") over the
stair compartment, the 2F plan draws no cut line in the flights (the 1F plan does), and the main-stair counts of
section A-A (owner Q-46) end at +9.70.

Conclusion: the geometry supports A. AL-2F = 4.875 m2 marble (printed), as its own stair element; nothing of it is in
any porcelain row.

## 3. The second-floor face, every m2 once (face 18.600 m2, engine room 2F-R4D1B62)

| Row | m2 | Category / line | Polygon (local m) |
|---|---|---|---|
| AL-2F arrival landing 250 x 195 | 4.8750 | MARBLE_LANDING, new element ST-MS-LD-2F (Q-70 A) | (0,0)-(2.50,0)-(2.50,1.95)-(0,1.95) |
| LB-2F beyond the stair width 200 x 125 | 2.5000 | PORCELAIN, 2F floor | (2.50,0)-(4.50,0)-(4.50,1.25)-(2.50,1.25) |
| H-FS-2F east-lane foot of the arriving flight 1.15 x 0.35 | 0.4025 | HELD position, marble in every reading, 0 m2 added (section 4) | (1.35,1.95)-(2.50,1.95)-(2.50,2.30)-(1.35,2.30) |
| O-2F stair opening over the 1F -> 2F stair | 10.8225 | none on 2F (flights and half landing are their own stair rows) | CSV |
| Z-2F face in no row | 0.0000 | check | - |
| **Sum** | **18.6000** | pairwise overlap 0.000000 | |

The finish table's DF-2F-LOBBY 8.775 = the rectangle 4.50 x 1.95: 7.375 of it is in the face, 1.400 is not floor
(0.900 shaft 2F-R2BDCEE, 0.500 wall and column) (`printed_450x195_rectangle`). Whatever finish the owner gives the
landing, the 2F floor in front of the stair is 7.375 m2, not 8.775 (the finish table over-states it by +1.400, +19.0 %;
the freelancer's 7.70 is closer). Verdict proposal: HAND_RIGHT 7.375 against the T-086 / T-088 table.

Drawn reading of AL-2F (second method): a layer-5 line at y 1.90 crosses the west lane and the well (x 0 .. 1.35,
segment D2:5002:0) 0.05 inside the printed 195 edge; the line at 1.95 (D2:5003:0) and the nosing line at 2.00 belong to the
lower flight seen below. On the second floor the y 1.90 line is the floor edge over the lower flight (the 1F plan has it
only across the well, T-122 R-LC 0.010). Drawn landing body 4.8075 = 4.875 - 1.35 x 0.05; in the east lane the floor runs
to the top riser at 2.00 (+0.0575). Printed 4.875 vs drawn 4.8075 .. 4.865: -0.068 .. -0.010 m2 (-1.4 .. -0.2 %),
RULE_DIFFERENCE (where marble stops at a balustrade / slab edge is a detail no sheet prints). The marble line uses the
printed 4.875, as T-122 did on the first floor.

## 4. The foot strips (D-13 on 1F, H-FS-2F on 2F): settled in quantity, still HELD in name

- 2F: section A-A (12 risers, Q-46 A), the drawn going 0.30 and the walk-line arrowhead all put the top riser of the
  arriving flight at y 2.00. So of the 0.4025 strip, 0.345 (y 2.00 .. 2.30) is the 11th tread of that flight and 0.0575
  (y 1.95 .. 2.00) is landing beyond the printed 195. Both marble; neither porcelain. The 11th tread is already inside
  flight row ST-MS2-U (12 treads counted, section 5). Status CALCULATED, quantity added to any line: 0.
- 1F (D-13, T-122): same position and size. One correction of T-122's evidence: the walk line on the 1F plan is the
  first-to-second-floor path (it starts on the landing in the west lane), so its arrowhead at y 7.15 marks that stair's
  arrival at +9.70, one storey up, not the edge of the +5.50 floor. At +5.50 the east lane receives the ground-to-first
  floor upper flight (ST-MS1-U, 12 risers by section A-A). The 1F plan cuts the stair with a break line in the west lane
  only; by the usual plan convention the east-lane treads (10 drawn goings, y 7.45 .. 10.45) and the winders north of
  10.45 are that ground-to-first flight seen below the cut, and 11 goings from 10.45 end at 7.15: the same geometry as on
  the second floor (0.345 the 11th tread, 0.0575 landing). This reading is practice, not a printed note, so the label
  stays HELD (designer D-13, flight ledger T-111). In every reading the strip lies inside the stair width and the printed
  330 run: marble, never porcelain, and never to be added to the 4.875 landing (that would count it twice with the flight
  row). Quantity added to any line: 0.

## 5. Stair marble ledger, once-only check (m2)

| Element | m2 | Source | Once-only note |
|---|---|---|---|
| ST-E1 entrance flight | 6.580 | finish table (T-084) | - |
| ST-D1 hall to +0.30 | 2.280 | finish table | - |
| ST-MS1-L GF -> 1F lower (A-A: 10) | 5.600 | finish table | the GF stair-hall chain is different; T-111 |
| ST-MS1-U GF -> 1F upper (A-A: 12) | 6.720 | finish table | 12 treads for 12 risers: one tread may lie on a landing or the held winders; T-111 |
| ST-MS2-L 1F -> 2F lower (12 + closing riser) | 6.941 | finish table | 12 x 0.30 = 3.60 m of run |
| ST-MS2-U 1F -> 2F upper (A-A: 12) | 6.739 | finish table | 12 treads for 12 risers: 11 goings between two counted landings |
| ST-MS1-LD GF -> 1F landing 120 x 125 | 1.500 | finish table | - |
| ST-MS2-LD 1F -> 2F half landing 250 x 125 | 3.125 | finish table | plan chain prints 120 |
| ST-MS-LD-1F arrival (Q-66 B) | 4.875 | T-122 | once (not in 1F porcelain) |
| ST-MS-LD-2F arrival (Q-70 A) | 4.875 | this run | once (not in 2F porcelain) |
| **Sum of lines** | **49.235** | | owner candidate 49.240 = same with 39.49 rounded |

Double-count check: the printed chain leaves 3.30 m (y 1.95 .. 5.25, the "330") between the arrival landing and the
north band in each lane, but both 1F -> 2F flight rows cover 12 x 0.30 = 3.60 m. Either the flights' last 0.30 m lies on a
landing that is also counted (0.30 x 1.20 = 0.36 m2 per flight) or the true goings are shorter than the 0.30 the rows use;
the drawings disagree on the counts (owner Q-46: plan 12 + 4 + 11, section 13 + 12, structural 12 + 1 + 11). Once-only stair
marble is therefore **48.515 .. 49.235 m2, HELD** until the flight-by-flight ledger (T-111) fixes each flight's treads and
going; the two arrival landings themselves are counted once (each in exactly one line, polygons above and in T-122).
Not checked here: the ground-to-first-floor flights against the stair-hall chain (different, T-111) and the round stair
(HELD rows).

## 6. Engine defect found: the second-floor plan's flights are counted as new flights

ARCH_TAKEOFF_V2.9 measures, for the stair face on the second floor, FIN.MARBLE.TREAD 3.45 + 3.45 = 6.90 m2 and
FIN.STAIR.STEP_LM 11.5 + 11.5 = 23.0 lm (MACHINE_ONLY, measured, not held) for flights F1 (west lane) / F2 (east lane)
of the 2F plan. Its own cross-plan record pairs them with first-floor flights F2 / F3 (overlap 1.0) and reads them
"STACKED" (a new flight of the next storey), because no void mark is near them (engine/source/arch_rooms.py
`cross_plan_flights`, the STACKED reading). But no flight rises above the second floor (section 2: solid T 18 roof slab
over the compartment, no cut line on the 2F plan, section A-A's counts end at +9.70): every flight on the 2F plan is a
flight of the storey below seen from above.
- **Certain duplicate: 2F F1 = 1F F2**, the first-to-second-floor lower flight (west lane; both end at the same north
  edge, y -793.194 world = 2F local 5.25; on the 1F plan it starts at the landing edge and is the 1F's own flight, 3.795 m2,
  12.65 lm). Released V2.9 over-count: **+3.45 m2 tread marble, +11.5 lm steps** (owner rule UP-STAIR-008: "a step drawn
  on two plans is one step").
- **2F F2 (east lane)** is the first-to-second-floor upper flight. Whether it is a duplicate depends on what the 1F plan's
  east lane shows: by the plan convention (section 4) it is the ground-to-first-floor upper flight below the cut, and then
  2F F2 is the only measurement of the upper flight (not a duplicate); if the 1F east lane were the upper flight drawn
  above the cut, 2F F2 would also be a duplicate (+3.45 m2, +11.5 lm more) and the ground-to-first upper flight would be
  missing. Which one is for the flight-by-flight ledger (T-111).
The 2F landing line (HELD 0 .. 11.725 upper bound) spans the same opening. Proposal for the Lead (new task, code): on the
top storey of a stacked core (no flight continuing above, no cut line on the upper plan), a flight paired with a flight
of the storey below is SEEN (counted once, on the lower plan), not STACKED; fixture with a two- and a three-storey stacked
core (mirror, rotation, mm / m). Verdict proposal: HAND_RIGHT (one stair), engine over-count 3.45 m2 / 11.5 lm certain.

## 7. D-23 (1F, 0.05 x 2.35 element beside the round-stair flight): new evidence, still HELD

The same closed 0.05 m element is drawn on the ground-floor plan at the same place (plan offset 44.853 m, layer 2; on the
1F plan layer 5), from the wall face (y 0.05) to the top of the flight (y 2.40), with its outer face flush with the east
face of the column at the wall (1F x 10.87 local = the column's east face; GF the same). It runs along the open side of the
flight and of the quarter landing on both floors, so it reads as a stair-side element (stringer, upstand or balustrade
base) rather than living floor. No sheet names it or gives its height, so the 0.1175 m2 stays HELD (designer D-23); 1F
porcelain stays 33.594 .. 33.711. If the designer confirms a stair-side element, porcelain = 33.594 m2.

## 8. Synthetic check (not Alsenan)

`--selftest`: a 2.40 x 6.00 stair with a 1.80 landing, a 1.60 x 1.10 area beyond the stair width, a 1.10 x 0.40 foot
strip and a 0.04 x 0.60 column notch, in metres and millimetres, rotated 0 / 90 / 217 deg and mirrored: landing 4.320,
beyond 1.760, foot 0.440, opening 9.616 by hand, re-added to the face with no overlap; with no printed landing depth the
landing and the foot strip are HELD (None, never 0) and the stair stays whole in the opening row. PASS.

## 9. Verdict proposals for the verifier

- 2F arrival 4.875 m2 marble under Q-70 A: owner condition MET (section 2, five facts); RULE_DIFFERENCE vs the freelancer
  (porcelain). Re-measure suggested: the 1950 / 3300 / 1200 / 6450 dimension chain and the 1250 dimension on the DXF.
- 2F porcelain 2.500 vs owner candidate 3.900 and table 8.775: HAND_RIGHT (8.775 = two dimensions read as one room).
- 2F floor in front of the stair 7.375 vs freelancer 7.70 (+0.325, +4.4 %): UNRESOLVED (his row is not traceable).
- Stair marble 49.235 (sum of lines) CONFIRMED; once-only 48.515 .. 49.235 HELD (flight rows vs printed run, T-111).
- D-13 / H-FS-2F: marble in every reading, 0 m2 to add; D-23 HELD (new evidence).
- Engine 2F tread marble / steps: the 1F -> 2F lower flight counted on both plans, +3.45 m2 / +11.5 lm certain
  (+6.90 / +23.0 under the second reading of the 1F east lane): engine over-count, HAND_RIGHT.

## 10. What is missing

T-111 (flight by flight: treads and going of every flight, which settles the 0 .. 0.72 m2 overlap and the GF -> 1F
checks); designer D-13 / D-23 labels; no method version wires any of this (released 1F living 44.869 and the V2.9 2F stair
lines unchanged). Gate 1 (no surface in two lines; no lost floor) and gate 2 (stairs). Rules: owner Q-56 A, Q-66 B,
Q-70 A (conditional), Q-46 A, Q-47 A, UP-STAIR-001, -002, -005, -008, UP-QTY-STATUS-001, arch_floor FLOOR AREA
RECONCILIATION.
