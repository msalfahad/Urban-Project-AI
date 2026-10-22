# T-128: plaster, paint and wet-wall tile per Alsenan room by BOTH methods (owner manual G1 and drawing-derived)

**r1, REJECTED by the checker 2026-10-22 02:40 (gate e); superseded by `T-128_R2_PLASTER_PAINT_TWO_METHODS.md`. Kept unchanged below as the record.**

Worker 3, 2026-10-21 05:00-05:35 UTC. Lane A (plan P-06). NO REPO CODE: this run's self-check (venv + project checks)
was refused by the session permission check, so no engine module or project tool ran; every number below is a hand /
standard-library calculation (`calc.py`, inputs typed with their source) on lengths traced from the Drive drawings.
Development villa (Alsenan), not an accuracy claim; nothing released changes. No client names, no coordinates, no images.

Files: `ROOMS_T128.csv` (31 rows: 28 rooms / zones + 3 stair-shaft storeys), `calc.py`, `trace_lengths.json` (wall-face
lengths per room by kind, from the trace in section 1), `summary.json` (per floor and kind).

Rules applied: G1 and G2 (OWNER_RECONCILIATION_2026-10-20.md), Q-43 (manual formula), Q-48 A (wet-wall tile to the
0.15 m decor ceiling, the same 0.15 used for paint), Q-52 C mod (per room, plaster and paint apart, a beam does not lower
the whole room, unknown ceiling = PROVISIONAL / HELD), Q-54 B (annex datum held), Q-55 C (door height 2.20 m ASSUMED
only when the drawings are silent; main entrance 2.50 printed), Q-57 A mod (ceilings measured apart: not in this table),
Q-06 / Q-30 / Q-37 (basin spaces, kitchen, pantry are wet), UP-FIN-PAINT-001 (dry: plaster + paint on one face; wet:
tile, no paint), UP-OPEN-SCHED-001 `wall_finish_deduction` = width x (min(head, H) - max(sill, 0)) (OWNER_APPROVED),
UP-QTY-STATUS-001 (held never 0). Rule note: UP-GEN-003 v1.1.0 still says PLASTER_PAINT "owner decision pending"
(Q-OPN-1), while UP-OPEN-SCHED-001 1.4.0 (owner-approved) gives the full-band deduction; this package uses
UP-OPEN-SCHED-001 and the Lead may want the registry line aligned (not an owner question: the approved rule exists).

## 1. Wall-face lengths: a second, independent trace (all 31 rows closed, including the 7 that T-112 could not close)

Method (scratchpad only): the architectural DXF from Drive "Alsenan chalet project" (P7757_DXF_COMPRESSED.zip, sha256
ab54dd55...) rasterised at 5 mm per pixel: wall lines (layer 1), columns (S-COL.BON) and windows (layer W) as barriers;
every door block closed by its closed-leaf line on the swing face and a second line across the wall thickness; wall
cavities narrower than 0.225 m filled; open sides that are not walls closed by named VIRTUAL lines (pantry to dining
4.46 m, wash lobby to hall 1.21 m, master bed room to the pool-side hall 1.44 m, the 1F lift-car mouth 0.96 m) and
reported apart (never plastered). Each region's boundary is split into WALL / WINDOW / DOOR / VIRTUAL by the nearest
drawn line. Calibration: the trace runs 2 cm inside the faces, so +0.16 m per closed contour; with it the trace
reproduces every printed rectangle to 0.00-0.01 m: 1F 245 x 205 baths 9.00 / 9.00, 210 x 225 8.70, 147 x 180 6.54,
2F 300 x 645 18.90, 300 x 185 9.70, GF 175 x 450 12.50, 130 x 150 5.60, 150 x 225 7.50, 150 x 210 7.19, dewaneya 20.14
(printed 20.128 with the R1.10 corner).

Cross-check against the engine room faces that the verifier merged in T-106 (V2.11 boundaries) and the freelancer:

| Room | This trace (wall faces, m) | Engine T-106 boundary | Freelancer length | Note |
|---|---|---|---|---|
| 1F master bed 425 x 450 | 17.68 | 17.70 | 17.50 | +0.18 vs printed = column faces in the room |
| 1F master bed 500 x 365 | 17.39 | 17.40 | 17.30 | |
| 1F master bed 380 x 430 | 16.20 | 16.20 | 22.30 | he adds the two 3.05 m passage walls (they are in the 1F open zone here) |
| 1F master bed east (curved W17) | 22.07 | 22.151 | 21.90 | **first hand-traced length** (engine face existed) (T-112 HELD) |
| GF master bed room | 20.58 + 1.44 open side | 21.534 | 21.05 | **first hand-traced length** (T-112 HELD); open side to the pool-side hall not plastered |
| GF open room (dining + entrance + reception + saloon) | 58.43 + 7.09 open sides | 56.006 + 7.600 (2nd face) | 54.25 | **first hand-traced length** |
| 1F living + corridor + landing + connector | 38.61 (+13.38 shaft, +0.96 lift mouth) = 52.95 | 52.44 | 40.25 + 9.35 | **first hand-traced length**; shaft walls split off (section 4) |
| 2F lobby (outside the shaft) | 13.31 (+14.25 shaft) | - | 9.00 | **first hand-traced length** |
| laundry / kitchen / GF wash lobby | 16.92 / 14.48 / 8.27 + 1.21 | 16.94 / 14.50 / 9.499 | - | |

22 closed rooms agree with the engine faces within 0.10 m (the 1F open zone within 0.51 m, the GF master and the GF open room differ by how their open sides are drawn); the trace is independent of the engine (different program, no
shared code), so the lengths are now verified by two methods. GF wedge W.C.s: 6.71 / 7.37 vs T-074 hand traces 6.81 /
7.41 (diagonal walls, -0.10 / -0.04 m).

## 2. Heights by both methods

| Zone | Marks (floor-to-floor) | (a) Owner manual (G1) | (b) Drawing-derived paint / wet-tile height | (b) Plaster height | (b) - (a) |
|---|---|---|---|---|---|
| GF main (+1.00) | 4.50 | 3.65 | 4.09 .. 4.19 | 4.09 .. 4.34 | +0.44 .. +0.54 |
| GF annex (+0.30) | 4.00 on marks, datum HELD | 3.15 PROVISIONAL (G2) | 3.59 .. 3.69 PROVISIONAL-DATUM | 3.59 .. 3.84 | +0.44 .. +0.54 |
| 1F (+5.50) | 4.20 | 3.35 | 3.79 .. 3.89 | 3.79 .. 4.04 | +0.44 .. +0.54 |
| 2F (+9.70) | 4.20 | 3.35 | 3.79 .. 3.89 PROVISIONAL-DATUM | 3.79 .. 4.04 | +0.44 .. +0.54 |
| GF W.C. 175 x 135, basin space | room level not drawn | HELD | HELD | HELD | - |
| Stair shaft | continuous through the storeys | HELD (no owner rule) | storey interval 4.50 / 4.20 / to the roof 3.79 .. 3.89 | same | - |

(b) = floor-to-floor - 0.16 m slab (ST general note, "all slabs 16 cm unless stated") - floor build-up b - 0.15 m decor
ceiling (owner Q-48 A, which the owner applies to paint too). b is not printed anywhere: 0 (upper value) .. 0.10 m (the
owner's own floor allowance, Q-43). Plaster may run above the decor ceiling to the slab soffit (Q-52: "depending on the
specification"; none printed), so its range runs from the paint height to the soffit. Evidence searched before any
hold (G1): section A-A (p7757_arch_sheet10.pdf, re-measured at 300 dpi this run: slab bands drawn 0.20 m between line
centres, 0.23 m outside to outside, scale 118 px per m checked on the printed 420; level arrows on the band top; no false
ceiling, bulkhead or beam drawn under any slab), section B-B (pages 11-12, T-112), all 12 architectural pages and the DXF
(T-091 census: no ceiling level, room schedule, ceiling detail or floor build-up printed), the structural DXF (only the
architectural underlay marks +9.70 on the second-floor roof-slab plan beside the water-tank place; no structural slab
level; the only build-up printed in the structural set, "5 cm screed / 5 cm insulation membrane / 10 cm plain
concrete", belongs to the swimming-pool detail, not to a roof).

Why the methods differ (the same 0.44 m everywhere when b = 0.10): the owner formula takes off a 0.60 m beam allowance,
the drawings put a 0.16 m slab over every room (0.60 - 0.16 = 0.44). Beams do not lower a whole room (Q-52); a beam that
crosses a room is a bulkhead under the decor ceiling, i.e. a CEILING item (Q-57), not a lower wall: GF open room B26 /
B27 0.85 (0.54 m below the decor ceiling), pantry B27, GF wash lobby B11 0.75 (0.44), dewaneya CB6 0.75 (0.44), 1F 380 x
430 B19 0.75 (0.44) and B6 0.50 (0.19), 1F west master B6 0.50 (0.19), 2F maid B2 0.40 (0.09), 2F lobby B15 1.20 (0.89).
Beams on a wall line leave the wall face continuous (the beam side is part of the plastered face).

New datum finding (designer request, not an owner question): the owner held the annex because +4.30 is a finished roof
mark (G2). The same holds for every room under a ROOF: section A-A draws +13.90 on the top of the roof band exactly as
+4.30, the plans print the 1F roofs at +9.70 and the GF terraces at +5.50 (the next FFL), and the sanitary sheets print
SLOPE 1 % on the +4.30 and +9.70 roofs (falls screed above the slab). By the plan overlay (sheets repeat every 44.85 m)
the rooms wholly under a roof are: the 6 annex rooms, 1F master bed rooms west / 500 x 365 / east, the 1F west and east
baths, and every 2F room; 13 more are partly under a roof (column UNDER_ROOF_SHARE). Their drawing-derived heights are
marked PROVISIONAL-DATUM: computed (G1), not releasable until the roof slab-top level and the roof build-up are given.
With no stepped slab drawn in the structural set, a roof build-up of more than the floor build-up would also put the
finished roof above the printed mark: DCR-6 below.

## 3. Results per floor (gross m2 before openings; nets in section 5)

Dry rooms: plaster m2 = paint m2 under the owner method (UP-FIN-PAINT-001); the drawing-derived plaster range is wider
(to the soffit).

| Floor, dry rooms | Wall faces | (a) Owner manual | (b) Drawing-derived paint | (b) plaster upper | Freelancer, same rooms | (a) vs him | (b) vs him |
|---|---|---|---|---|---|---|---|
| GF: dewaneya, driver, open room, master bed | 111.64 m | **391.17** (annex 102.81 PROVISIONAL) | **440.30 .. 451.45** | 468.21 | 388.08 (72.00 + 45.00 + 195.30 + 75.78) | +3.09 (+0.8 %) | +52.2 .. +63.4 (+13.5 .. +16.3 %) |
| 1F: 4 master bed rooms + living / corridor / landing zone | 111.95 m | **375.03** | **424.30 .. 435.48** | 452.28 | 441.27 (bed rooms 268.60 + living 140.88 + basins corridor 31.79) | -66.24 (-15.0 %) | -17.0 .. -5.8 (-3.8 .. -1.3 %) |
| 2F: maid room, lobby | 32.21 m | **107.92** | **122.09 .. 125.31** | 130.15 | 94.86 (64.26 + 30.60) | +13.06 (+13.8 %) | +27.2 .. +30.5 (+28.7 .. +32.1 %) |
| Stair shaft GF / 1F / 2F | 11.94 / 13.38 / 14.25 m | HELD (no owner rule) | **163.93 .. 165.35** | 167.49 | 204.42 (14.80 x 12.90 + 5.40 x 2.50) + GF stair wall 40.50 | - | -81.0 .. -79.6 vs his 244.92 (shaft + stair wall) |
| **All dry incl. shaft** | | **874.12** + shaft HELD | **1 150.62 .. 1 177.59** | 1 218.13 | 1 209.39 gross plaster rows (incl. 24.30 wash, 15.96 door reveals) | - | **-58.8 .. -31.8 (-4.9 .. -2.6 %)** |

Wet rooms (wall tile to the decor ceiling, Q-48 A; heights as section 2): GF 11 rows 257.47 m2 owner (annex 109.53
PROVISIONAL; 2 rows HELD on level) / 290.59 .. 298.13 drawing; 1F 6 rows 193.48 / 218.89 .. 224.67; 2F 32.49 / 36.76 ..
37.73. Owner total 483.44 m2 (+2 HELD) vs the freelancer's wet-room spatter-dash area 433.83 m2 (one total, 3.00 m flat):
+49.61 m2 (+11.4 %), not comparable room by room.

What the numbers say: (1) the owner method on the same rooms is within 1 % of the freelancer on GF and -1.5 % on the
same-wall 1F / 2F rooms (3.35 vs his 3.40), but the 1F set is -15 % because the freelancer gives the 1F open zone 55.70
m of wall (living 40.25 + basins corridor 9.35 + the 380 x 430 passage 6.10) where the drawing has 38.61 m outside the
shaft; (2) the drawing-derived heights are 0.44 .. 0.54 m higher than the owner heights in every zone, which adds +13 ..
+15 % to every wall area; (3) the whole-house drawing-derived total lands 2.6 .. 4.9 % under the freelancer's gross
plaster, because his flat 3.40 / 3.60 m and his longer 1F / shaft runs cancel the lower owner heights.

## 4. Stair shaft (the 7th T-112 hold, now measured)

The main dog-leg stair shaft (2.46 m wide inside, same rectangle on the three plans) is traced per storey: wall faces
GF 11.94 m (W01 1.20 x 2.00 printed, north door 1.00), 1F 13.38 m (W13 1.20 x 2.30 printed, door 1.00, one 1.00 window
unprinted), 2F 14.25 m (W26 arched 1.20 held, W27 1.00 held). Drawing-derived: the shaft walls are continuous through
the storeys, so GF x 4.50 + 1F x 4.20 + 2F to the decor ceiling 3.79 .. 3.89 = 163.93 .. 165.35 m2 gross (plaster to the
roof soffit 167.49). Not deducted yet: the landing-slab edge bands where the landings meet the shaft walls (landing
lengths in T-111), and the 2F roof datum (PROVISIONAL-DATUM). The freelancer: 14.80 m x 12.90 m + 5.40 x 2.50 = 204.42
m2 (his perimeter is the full 2 x (2.46 + 5.0) box at every storey, including the open landing sides). The owner formula
has no stair-shaft case: OWNER METHOD HELD, no question raised (the owner's G1 asks for drawing-derived values where the
documents allow, and here they do).

## 5. Nets (UP-OPEN-SCHED-001, full band) and what holds them

Doors: printed widths from the door blocks (0.80 / 0.90 / 1.00 / 2.00; the master-bath loose arc 0.68), heights 2.20 m
ASSUMED (Q-55) except the main entrance 2.50 printed. Windows: only W14, W17, W18, W03 (pool glazing, PROBABLE: T-083),
W01, W13 print sill and head. Arch openings (GF dewaneya / wash, 1F 380 x 430): head not printed.

- Net PROVISIONAL (every opening known, doors ASSUMED): GF master bed 56.95 m2 (W03 is full height: head 4.30 above both
  methods' ceilings), GF W.C. by the dewaneya 21.87, driver W.C. 15.88, wedge B 25.13, wash lobby 26.66; 1F west master
  51.34, east master 59.75, bath east 26.31; 2F lobby 40.42 (owner method).
- Net HELD with bounds (lower bound = every unknown opening taken full height; upper = gross less the known openings):
  owner method per floor GF dry 313.85 .. 357.67 m2, 1F dry 319.95 .. 338.88, 2F dry 95.97 .. 100.00; wet GF 217.59 ..
  238.98, 1F 169.81 .. 179.87, 2F 28.73 .. 30.73. The freelancer nets 1 151.14 (plaster) / 1 191.13 (paint) by deducting
  HALF of 116.50 m2 of openings: RULE_DIFFERENCE (no Urban rule deducts half).
- Door jamb / head plaster (UP-FIN-PLASTER-001) and window reveals (UP-REVEAL-001) are separate lines, not in this table;
  the trace lists the reveal returns it met apart (0.04 .. 0.95 m per room).

## 6. Checks of openings against the two ceiling lines

- GF master bed room, W03 pool glazing head 4.30 above +1.00: above the owner line 3.65 (+0.65) AND above the
  drawing-derived decor ceiling 4.09 .. 4.19 (+0.11 .. +0.21) and the B8 soffit: the conflict stands in both methods
  (DCR-2 of T-112).
- 1F east master, W17 crown 3.70: above the owner line 3.35 (+0.35) but BELOW the drawing-derived ceiling 3.79 .. 3.89:
  the conflict exists only in the owner method; the CB12 soffit check (DCR-3) remains.
- 1F west master W14 head 2.80, bath east W18 head 3.00, 1F stair W13 head 3.30: inside both methods.
- 1F west master and the living zone sit under the open dome positions (Q-29 / Q-44): no ceiling plane exists there;
  their drawing-derived heights assume a flat decor ceiling across the opening (DCR-4 of T-112 stands).

## 7. Who is right (proposals for the verifier)

- Lengths, 22 closed rooms: AGREE (trace = engine faces within 0.10 m; printed rectangles to 0.01 m).
- 1F open zone, 2F lobby: ENGINE_RIGHT on length (the drawing has 38.61 / 13.31 m of wall outside the shaft; the
  freelancer's 55.70 / 9.00 m are not in the drawing as walls; trace path in section 1).
- Heights: RULE_DIFFERENCE (owner 3.65 / 3.35 vs his flat 3.60 / 3.40; drawing-derived 4.09 .. 4.19 / 3.79 .. 3.89).
- Stair shaft: RULE_DIFFERENCE on method (his box perimeter x 12.90 vs faces per storey x storey interval), drawing-derived
  -19.8 .. -19.1 % on his 204.42 m2.
- Opening deductions: RULE_DIFFERENCE (half vs full band).

## 8. Designer requests (for DESIGNER_CLARIFICATIONS.md; the Lead files them)

- DCR-6 Roof datum (new): slab-top levels of the GF terrace roofs (+5.50 finished), the 1F roofs (+9.70) and the main
  roof (+13.90), and the roof build-up (falls screed, insulation, protection); confirm whether the roof slab steps down
  from the adjacent floor slab. Decides every drawing-derived wall height under a roof (17 rooms wholly or mostly).
- DCR-7 Ceilings (repeat of T-112 "general"): a reflected ceiling plan or the decor-ceiling level per room, and the
  floor build-up per floor; until then the drawing-derived values stay PROVISIONAL with the 0 .. 0.10 m build-up range.
- DCR-2, DCR-3, DCR-4 of T-112 stand (section 6).

## 9. What is missing / not done here

Door heights (only the main entrance is printed), 18 window heights, arch heads; roof and floor build-ups; the landing
edge bands in the shaft; the beam-end patches where a crossing beam meets a wall (beam widths in the T-110 register,
under 0.5 m2 per beam end); ceilings (Q-57, separate table); door jamb / reveal lines. Checker re-measure proposal (3
rooms): 1F master bed east (curved wall, 22.07 m), GF master bed room (20.58 m + 1.44 m open side) and the 1F open zone
(38.61 m outside the shaft): open the 1F / GF plans on the Drive DXF and walk the wall faces.
