# T-128 r2: plaster, paint and wet-wall tile per Alsenan room by both methods, re-walked on the verified boundaries

Worker 2, 2026-10-22 07:47 - 09:00 UTC. Lane A, rework of REJECTED r1 (checker 2026-10-22 02:40, gate e). NO REPO CODE:
research files only (this folder); no engine module, rule, knowledge version, key map, test or released quantity
changed. Development villa (Alsenan), not an accuracy claim. No client name, image or personal data is committed;
`walk_r2.py` carries the same room-selection points and clip boxes as the merged T-147 `ceil_ledger.py`, and every
output file holds lengths and areas only. Self-check of this run: codemap check, pytest t061, freeze 0: all PASS.

Supersedes the r1 tables (`ROOMS_T128.csv`, `summary.json`, `calc.py`, `trace_lengths.json` and the r1 report stay
unchanged as the record of the rejected run; `trace_lengths.json` is still read for one input, the share of each room's
face under a roof). New files: `walk_r2.json`, `ROOMS_T128_R2.csv` (32 rows), `OPENINGS_T128_R2.csv` (94 rows, one per
opening face), `FLOORS_T128_R2.csv`, `CHANGES_R1_R2.csv`, `summary_r2.json`, `scripts/walk_r2.py`, `scripts/calc_r2.py`,
`scripts/check_walk_r2.py`.

Data: Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip (P7757.dxf sha256 ab54dd55...), read this run into the
private folder only. Repeat: `python -I scripts/walk_r2.py ../agents_t147/scripts/rooms.py <P7757.dxf> walk_r2.json`
(project venv), then `python3 -I scripts/calc_r2.py walk_r2.json ../agents_t144/OPENINGS_T144.csv trace_lengths.json .`;
fixtures: `python3 -I scripts/calc_r2.py --check` and `python -I scripts/check_walk_r2.py` (both PASS).

## 0. What the checker rejected and what r2 does about each fault

| r1 fault (checker 02:40, Lead 04:20) | r2 |
|---|---|
| (1) curved rooms walked on a straight line, not on the verified boundaries | every room is walked on the checker-verified T-147 regions (T-153 floors, T-127 court): GF master bed 16.557 m2 / contour 21.537 m (checker 16.549 / 21.535) |
| (2) one door, two widths (GF master bath door 0.68 / 0.80) | one width per opening, from both of its faces (22 face pairs: openings seen from two rooms; frame = leaf + 0.11: 0.80 / 0.90 / 1.00) |
| (3) statuses not in WORKFLOW_CONTROLS s.5 terms | ASSUMED - OWNER-APPROVED / DRAWING-CONFIRMED / HELD on every quantity (section 4) |
| (4) stair shaft owner method | HELD on Q-72 (open); drawing-derived given beside it |
| (5) window heights | T-144 merged heights used (W03, W14 corrected, W17 corrected, W15, W18, W01, W13, W26); the 20 unprinted windows HELD (D-45) |

## 1. How the faces were walked

`walk_r2.py` re-runs the T-147 region builder on the DXF (barriers: layer 1 walls, S-COL.BON columns, W windows, door
closures, gap lines between collinear wall lines), takes each room's region (T-147 clips for the open zones), and walks
its contour at 5 mm steps. Each point is classed by the drawn line it lies on (within 5 mm): WALL, COLUMN (plastered like
the wall), WINDOW (layer W, incl. the curved pool glazing band and W17), door closure or gap line (an opening), or no
line at all (VIRTUAL: an open side, never plastered). Opening runs next to each other are one opening; an opening with a
door hinge within half its width + 0.6 m is a door, else a doorless opening. Three fixes to the regions, each named in
the output: (a) 1F east master: its 1.29 m doorless opening to its entry is a 0.15 m strip face (0.195 m2) added to the
room, so the two jambs are wall and the opening edges are not; (b) GF wash lobby: the basin niche joins through a 1.9 m
gap in a 0.15 m wall (strip 0.262 m2 added; lobby 4.739 m2 vs T-074 4.732); (c) GF master bath: the T-147 region runs
into the 0.15 m double-lined walls round the basin niche (4.596 m2), so the T-074 verified outline is used (2.10 x 2.00
less the 0.982 x 0.983 corner = 3.717 m2, contour 7.6245 m). Every other room's region area equals the T-147 / T-074 /
printed value to 0.01 m2 or better (`walk_r2.json` area_m2; comparison in section 6).

Walk bias, measured and corrected: an opening run loses about 5 mm at each wall end (a point within 5 mm of a jamb
line reads WALL). The fixture proves it (0.80 gap reads 0.79) and `calc_r2.py` adds 0.01 m per opening; the contour
total is exact, so the wall face is the contour less the corrected openings.

One width per opening: the two faces of a door differ by 0.05 - 0.06 m on 11 doors (the frame rebate side: 0.79 / 0.74,
0.99 / 0.94, 0.89 / 0.83); the wider face equals the door block's leaf + 0.11 m (0.69 -> 0.80, 0.79 -> 0.90, 0.89 ->
1.00), i.e. the frame lines the checker measured, and is used for both rooms. Rule note: UP-OPEN-SCHED-001 reads "the
opening's own length on the boundary"; taken per face it would deduct 0.606 m less over the 11 narrow faces (1.33 m2 at
2.20 m), a difference under 0.2 % of the dry total. The checker's one-width demand is followed; the Lead may want the
rule text aligned (FEEDBACK, not an owner question).

## 2. The rooms bounded by curved glazing or a curved wall (fault 1)

| Room | r1 | r2 (verified boundary) | Check |
|---|---|---|---|
| GF master bed room | face 20.576 m (straight W-layer line at the court + 1.44 m "open side"); W03 3.955 m | contour 21.537 m, no open side; W03 curved inner face 5.106 m; wall + columns 14.631 m; doors 1.00 + 0.80 | checker: contour 21.535, glazing 5.011 + 0.091 = 5.102, paintable 14.633, doors 1.80: all within 0.004 m |
| | owner gross 75.10, net 56.95 | **owner gross 21.537 x 3.65 = 78.61 m2, net 78.61 - W03 5.106 x 3.65 - doors 1.80 x 2.20 = 56.01 m2** (ASSUMED - OWNER-APPROVED: G1 + Q-55 C) | checker 78.60 / 56.02 |
| | | drawing-derived gross 88.09 .. 90.24 m2 (85 % of the face on the floor slab DRAWING-CONFIRMED, 15 % under the terrace roof HELD, DCR-6), net 63.24 .. 64.89 | W03 head +5.30 is above both ceiling lines: full-band deduction in both methods |
| 1F east master (curved W17) with its entry | face 22.073 m, W17 3.32 m, entry not in the room | contour 22.35 m (T-147 region 18.829 + the 0.195 m2 mouth = 19.024 m2; T-153 floor 19.017); W17 curved inner face 3.266 m; doors 0.80 (faces 0.79 / 0.74) + 0.90 (0.89 / 0.89) | contour by hand: main 16.85 + entry 7.80 - 2 x 1.29 mouth edges + 2 x 0.15 jambs = 22.37 (strip width 0.03 m explains 0.02 m) |
| | owner gross 73.95, net 59.75 (T-144: 59.08) | **owner gross 22.35 x 3.35 = 74.87 m2, net 74.87 - W17 3.266 x 3.35 (crown 3.50 above the line) - 1.70 x 2.20 = 60.19 m2** (ASSUMED - OWNER-APPROVED) | freelancer 74.46 m2 (21.90 m x 3.40): owner gross +0.41 m2 (+0.6 %) |
| | | drawing-derived gross 84.71 .. 86.94, net 69.54 .. 71.77: HELD (the whole face is under the +9.70 roof, DCR-6) | |
| GF open room (dining / reception / saloon) | "other glazing (plan)" 0.93 m straight; face 58.43 m | the W03 band (one LWPOLYLINE on layer W, 6.92 m inner face) runs on past the bed-room wall: 1.625 m of it faces the open room (sill / head printed with W03); face 53.19 m | r1's 58.43 m included about 6.2 m of lift-shaft walls (walked through the lift landing door); the T-147 region keeps a 0.849 m2 piece east of the W03 band, i.e. pool court (exterior): dropped here |
| GF dewaneya (R1.10 corner) | 20.137 m | 20.127 m | printed 20.128 m (T-088) |

No other room has a curved boundary in the DXF (the round stair in the open room has no wall line).

## 3. Results per floor (m2; dry = plaster + paint face, wet = wall tile to the 0.15 m decor ceiling, Q-48 A)

Heights unchanged from r1 / T-144: owner manual G1 GF 3.65, annex 3.15 (G2), 1F / 2F 3.35; drawing-derived paint / tile
height = floor-to-floor - 0.16 slab - b (0 .. 0.10, not printed) - 0.15 decor = GF 4.09 .. 4.19, annex 3.59 .. 3.69,
1F / 2F 3.79 .. 3.89; plaster may run to the slab soffit (+0.15). Gross = (contour - open sides) x height; net by
UP-OPEN-SCHED-001 full band; an unprinted opening makes the net a range (lower = full band, upper = no deduction).

Engine (this table) vs the freelancer, his dry plaster rows for the same rooms (gross before openings):

| Floor, dry rooms | Owner method gross | Drawing-derived gross | Freelancer | Owner vs him | Drawing vs him | r1 owner vs him |
|---|---|---|---|---|---|---|
| GF: dewaneya, driver (annex, HELD G2), open room, master bed | 375.52 | 422.76 .. 433.49 | 388.08 | -12.56 (-3.2 %) | +34.7 .. +45.4 (+8.9 .. +11.7 %) | +3.09 (+0.8 %) |
| 1F: 4 master bed rooms + open zone | 378.88 | 428.65 .. 439.96 | 441.26 | -62.38 (-14.1 %) | -12.6 .. -1.3 (-2.9 .. -0.3 %) | -66.24 (-15.0 %) |
| 2F: maid room, lobby | 93.50 | 105.78 .. 108.57 | 94.86 | -1.36 (-1.4 %) | +10.9 .. +13.7 (+11.5 .. +14.5 %) | +13.06 (+13.8 %) |
| Stair shaft GF / 1F / 2F (owner HELD Q-72) | HELD | 67.95 + 54.65 + 49.30 .. 50.60 = 171.90 .. 173.20 | 204.42 shaft + 40.50 GF stair wall = 244.92 | - | -73.0 .. -71.7 (-29.8 .. -29.3 %) | (r1 -81.0 .. -79.6) |

Whole house, dry incl. the shaft, drawing-derived: gross **1,129.09 .. 1,155.22 m2** vs his gross plaster 1,209.39:
**-80.3 .. -54.2 m2 (-6.6 .. -4.5 %)** (r1 -4.9 .. -2.6 %); net 929.37 .. 1,044.28 vs his plaster net 1,151.14 (half
deductions): -221.8 .. -106.9 (-19.3 .. -9.3 %), vs his paint net 1,191.13: -261.8 .. -146.9 (-22.0 .. -12.3 %); of the
114.9 m2 net range, 26.1 m2 is the unprinted floor build-up and about 88.8 m2 the unprinted openings (lower bound = full
band). Owner method, dry rooms without the shaft: gross
847.90 (r1 874.12; annex 102.78 of it HELD, G2), net 685.19 .. 753.74.

Wet-wall tile: owner gross 483.89 m2 (annex 109.62 of it HELD, G2; 2 GF rooms HELD on level) vs his spatter-dash total
433.83 at 3.00 m flat: +50.1 (+11.5 %), not comparable room by room; drawing-derived 546.76 .. 561.05.

Per floor and status bucket: `FLOORS_T128_R2.csv` (owner gross ASSUMED - OWNER-APPROVED / HELD; drawing-derived gross
DRAWING-CONFIRMED / HELD by roof share; nets as ranges).

What moved since r1, and why (per room in `CHANGES_R1_R2.csv`):

- GF open room -5.24 m of face (-19.1 m2 owner): r1 walked the lift-shaft walls; the lift landing door (1.00 m) is now an
  opening and the W03 part replaces the 0.93 m "other glazing".
- 2F lobby -4.31 m (-14.4 m2): same lift cause; the lobby face is now 9.01 m, the freelancer's 9.00 m: AGREE.
- GF master bed +0.96 m, 1F east master +0.28 m (+3.5 / +0.9 m2): the curved boundaries (section 2).
- GF stair hall 15.10 m (r1 11.94): the verified stair-hall face (T-147 / T-153 GF-S01 12.475 m2), with its two doors and
  the 0.90 m doorless opening to the basin space; GF basin space 4.90 m (r1 6.63 with a "stair passage"): T-074.
- GF wedge W.C.s 7.414 / 6.810 m = T-074 (r1 had the two lengths swapped), and the 0.60 m window is in wedge B (245 x 167)
  in the DXF, not wedge A as r1 / T-144 list it.
- 1F open zone +0.84 m: the T-147 clip at the shaft box; 1F west master's door (1.00) is shared 0.42 / 0.58 between the
  open zone and the shaft part (one width, two face parts).

## 4. Statuses (WORKFLOW_CONTROLS s.5) used in ROOMS_T128_R2.csv

| Quantity | Status | Source |
|---|---|---|
| owner manual heights GF 3.65, 1F / 2F 3.35 and every gross on them | ASSUMED - OWNER-APPROVED | G1 (OWNER_RECONCILIATION_2026-10-20), Q-43, Q-48 A |
| door head 2.20 m (46 door faces) | ASSUMED - OWNER-APPROVED | Q-55 C (only where the drawings are silent; main entrance 2.50 printed) |
| annex owner 3.15 m (6 rooms) | HELD, shown as OWNER MANUAL METHOD - PROVISIONAL with the candidate range in the drawing-derived column | G2, Q-54 B |
| drawing-derived on a floor slab | DRAWING-CONFIRMED, bounded by b = 0 .. 0.10 m (DCR-7) | ST general note slab 0.16, Q-48 A decor 0.15 |
| drawing-derived under a roof mark (annex, 1F roofs, 2F, terrace share) | HELD with the candidate range (DCR-6) | G2 logic, r1 section 2 |
| stair shaft, owner method | HELD | Q-72 open |
| stair shaft GF / 1F, drawing-derived | DRAWING-CONFIRMED gross (storey interval on the marks); landing-edge bands UNKNOWN, not deducted; 2F part HELD (roof datum) | T-111 for the landings |
| net with a window / arch / doorway / lift door whose head is not printed | HELD, range | T-144 census, D-45 |
| two GF wet rooms with no drawn level | HELD, candidate range both levels in CANDIDATE_RANGE | T-088 |

Room nets that are fully known: GF master bed 56.01, GF wedge A 25.30, GF wash lobby 26.65, 1F west master 51.41, 1F
east master 60.19, 1F bath east 26.30 (ASSUMED - OWNER-APPROVED); the annex W.C.s 21.86 / 15.88 (HELD, G2).

## 5. New openings and corrections for the openings table (T-144 / T-150 owners; FEEDBACK for the Lead)

- 3 lift landing doors (GF open room, 1F open zone, 2F lobby), 1.00 m wide on the face, no leaf block, no head printed:
  not in T-144's 79 rows; HELD here (lift supplier item; designer list).
- GF basin space <-> stair hall: a 0.90 m doorless opening (faces 0.890 / 0.891), not "D120 to open room 1.00": HELD
  (no leaf drawn, so Q-55 C does not apply; head not printed).
- GF stair hall north door: 0.90 m on its only face (T-144 1.00).
- W05-07 W.C. window: in wedge B (245 x 167), not wedge A.
- W03: one LWPOLYLINE band, 6.92 m inner face: 5.106 m in the bed room + 1.625 m in the open room (+ the wall crossing);
  printed width 6.57 (Q-38 A) is the 657 line at r 2.25, the room faces are at r 2.45.
- Wedge B: 0.80 m of its diagonal face carries no wall line in the DXF (a door-closure copy sits there); counted as wall
  face as T-074 did (its 6.810 m contour); checker please look.
- For the ceilings piece (T-147, merged PARTIAL): its GF open-room region holds 0.849 m2 of pool court east of the W03
  band, and its GF master-bath region 4.596 m2 holds 0.879 m2 of niche wall cavity (T-074 3.717).

## 6. Region check (walk area vs the verified value)

28 of the 32 walked rooms equal their T-147 region area to 0.01 m2 (and the T-074 / printed value where one exists) (e.g. GF master bed 16.5567 = T-147 16.557, checker
16.549, T-153 16.55; 1F 425 x 450 19.05; 2F maid 19.35 = 3.00 x 6.45). Exceptions, all explained above: GF master bath
(T-074 used), GF wash lobby 4.739 (T-074 4.732, niche strip), 1F east master 19.024 (T-153 19.017, mouth strip), GF open
room 134.398 less the 0.849 court piece. Contours of the 17 wet rooms = T-074 perimeters within 0.012 m (lobby 9.512 vs
9.500).

## 7. Who is right (proposals for the checker)

- GF master bed room: ENGINE_RIGHT on length (21.537 m on the verified curved boundary; freelancer 21.05 m); height
  RULE_DIFFERENCE (owner 3.65 vs his 3.60).
- 1F east master: AGREE on length within 2.1 % (22.35 vs his 21.90 m; his row gives no breakdown); RULE_DIFFERENCE on
  height.
- 2F lobby: AGREE (9.01 vs 9.00 m). r1's ENGINE_RIGHT on this room is withdrawn (it walked the lift).
- 1F open zone: ENGINE_RIGHT on length stays (39.45 m of face outside the shaft box vs his 55.70 m).
- Stair shaft: RULE_DIFFERENCE on method (his 14.80 m box x 12.90 m vs faces per storey x storey interval), drawing-derived
  -29.8 .. -29.3 % on his 244.92 m2 (shaft + GF stair wall); owner method HELD on Q-72.
- Opening deductions: RULE_DIFFERENCE (his half deduction vs the approved full band).

## 8. What is missing

Q-72 (shaft owner height), DCR-6 roof datum, DCR-7 floor build-up, 20 window heads + 3 arches + 2 doorless openings + 3
lift doors (designer list), door schedule (Q-55 C stays ASSUMED), landing-edge bands in the shaft (T-111 lengths), the
1F unlabelled space by arch120 (2.97 m2, UNKNOWN type, its walls not in this table), door / window reveals (UP-REVEAL-001,
separate lines), the beam-end patches (T-110). Checker re-measure proposal: GF master bed (as at 02:40) and the 1F east
master (contour 22.35 m, W17 3.266 m, doors 0.80 / 0.90), plus the W03 open-room part (1.625 m).
