# T-088: floor level, floor-to-floor, beam and wall height of every Alsenan room (hand table, NO REPO CODE)

Worker 2, 2026-10-19 22:40-23:40 UTC. Gate 1 (storeys and levels; feeds plaster and paint). Development villa (Alsenan),
NOT an accuracy claim. Hand reading only: no engine module was run or changed, no quantity is released. One row per drawn
room: `ROOMS.csv` (32 rows). No client names, no coordinates.

Sources (Drive "Alsenan chalet project", read in the session scratchpad, never copied here): p7757_arch_sheet03.pdf (GF
plan), p7757_arch_sheet04.pdf (1F plan), Alsenan_Architectural_P7757_Pages_05-06 (page 5, 2F plan), p7757_arch_sheet10.pdf
(SECTION A-A), Alsenan_Architectural_P7757_Pages_11-12 (page 11, SECTION B-B), P7757_DXF_COMPRESSED.zip (P7757.dxf: level
marks, the dewaneya corner arc), ST7757 dxf.dxf (the beam schedule block attributes; the GROUND / FIRST / SECOND FLOOR ROOF
SLAB plans). The architectural and structural DXFs share one scale and orientation: the column outlines (layer
S-COL.BON in both) match by a pure translation per floor, so each room was laid over its roof-slab plan to read the beams
over it (overlay pictures in the scratchpad only).

Rules applied and nothing else: owner Q-43 answer and heights rule (2026-10-19 21:40): wall height for plaster and paint =
floor-to-floor (slab to slab, from the level marks) - 0.60 beam - 0.15 decor ceiling (owner Q-48 = A, 22:40: 0.15 m
everywhere, no range) - 0.10 floor finishing; a room whose drawn beam is deeper or shallower than 0.60 m is HELD for the owner; an unmarked room takes its
floor's level on a one-level floor, on the split GF only from what is drawn, else HELD. Q-14 (distinguish floor-to-floor
from wall height), Q-06 (basin-only spaces are wet), Q-30 (kitchens wet), UP-WET-001 / UP-FIN-PAINT-001 (wet rooms: full
height porcelain, no plaster / paint line), UP-HGT-001 (drawing first), UP-QTY-STATUS-001 (held, never 0).

## 1. Levels and floor-to-floor (two drawings each)

| Storey / zone | Floor level | Level above | Floor-to-floor | Where printed |
|---|---|---|---|---|
| GF main house | +1.00 | +5.50 | **4.50** | SECTION A-A (sheet 10) "450", SECTION B-B (page 11) "450"; marks in the open room, pantry, stair |
| GF street-side annex (dewaneya, driver, kitchen, their W.C. / wash) | +0.30 | +4.30 (annex roof) | **4.00** | SECTION B-B "400" +0.30 to +4.30; DXF SE elevation marks +0.30 / +4.30; 1F plan "ROOF +4.30" over it |
| 1F | +5.50 | +9.70 | **4.20** | A-A and B-B "420"; +5.50 printed in the living area and corridor |
| 2F | +9.70 | +13.90 (top roof) | **4.20** | A-A "420" +9.70 to +13.90; +9.70 printed in the stair lobby and on both 1F roofs |

The annex storey is 4.00 m, not the main house's 4.50 m: its walls get 3.15 m by the owner's formula, not 3.65 m.
Neither section draws a beam below a slab or a false ceiling: the wall heights below come only from the owner's rule.
Wall heights by the rule (0.60 beam, 0.15 decor): GF main 3.65 m, GF annex 3.15 m, 1F 3.35 m, 2F 3.35 m.

## 2. Room levels (32 drawn rooms)

* PRINTED inside the room: 10 (GF dewaneya +0.30, driver +0.30, kitchen +0.30, pantry +1.00, the dining / reception /
  saloon open room +1.00, stair hall +0.30 and +1.00; 1F corridor +5.50, living area +5.50, stair landing +5.50; 2F lobby +9.70).
* DERIVED on the split GF from what is drawn (door or opening with no step drawn into a room with a printed level): 8
  (dewaneya wash and W.C. +0.30; driver W.C. +0.30, both its neighbours print +0.30; the two core wedge W.C.s and their
  two-basin lobby +1.00, the lobby opens on the +1.00 hall; master bed room +1.00 through its 1.85 m lobby; its bath +1.00).
* FLOOR LEVEL on a one-level floor (owner Q-43): 12 (1F 10 rooms +5.50, 2F W.C. and maid room +9.70).
* HELD, level unclear: 2 (GF W.C. 175 x 135 by the stair and the 110 x 135 basin space in front of it: their passage opens on
  the stair hall between the printed +0.30 and +1.00 marks, and the plan does not show on which side of the steps).
* The stair halls (GF, 1F, 2F) are listed but their walls run through the storeys (the freelancer measures them as one
  14.8 m x 12.9 m shaft): no owner height rule covers a stair-shaft wall, so they stay HELD.

The engine count of 27 rooms (ARCH_TAKEOFF_V2.9, T-081) merges spaces this table keeps apart (the pantry inside the open
room, the core basin spaces, the corridors); every one of its 27 is inside these 32 rows.

## 3. Beams over the rooms: no 0.60 m beam exists on this villa

Beam schedule (ST7757, schedule of simple beams and continuous beams, block attributes): depths are 0.40 (B1, B2, B3, CB5),
0.50 (B4, B5, B6, CB2, CB4, CB9, CB10, CB13), 0.75 (B7-B14, B16-B25, B28, B29, CB1, CB3, CB6, CB7, CB8, CB11, CB12),
0.85 (B26, B27) and 1.20 (B15). The only 0.60 m type, "B.W" 0.20 x 0.60, is in the schedule but on none of the three
roof-slab plans. Per room (CSV column DEEPEST_DRAWN_BEAM):

| Deepest beam at the room | Rooms |
|---|---|
| 1.20 (B15) | 2F stair lobby |
| 0.85 crossing (B26 65x85, B27 90x85) | GF open room (dining / reception / saloon), pantry |
| 0.75 crossing (CB6, B11, B19) | dewaneya, core two-basin lobby, 1F master bed room 380 x 430 |
| 0.75 on an edge | GF wash / W.C. / driver / driver W.C. / kitchen (CB6, CB7), master bed room and its bath, stair hall; 1F west master bed room (B23), master bed room 500 x 365, corridor, east master bed room, east bath, living area; 2F W.C. and maid room (B8, B7) |
| 0.50 | GF stair-core W.C., the two core wedge W.C.s; 1F two west baths, laundry, W.C., bath by the laundry |
| 0.40 | GF basin space by the stair |

So, by the owner's own instruction (beam deeper or shallower than 0.60 m: hold for him), **every room is HELD**. The rule's
0.60 m is a standard deduction that never meets a drawn 0.60 m beam here. New owner question **Q-50** (which depth to
deduct). The heights the CSV shows are the owner formula with 0.60 (GF 3.65, annex 3.15, 1F and 2F 3.35); with
the drawn beam instead: 0.75 gives GF 3.50, annex 3.00, upper floors 3.20; 0.85 gives GF 3.40; 0.50 gives upper floors
3.45; 0.40 gives GF 3.85.

## 4. Wall lengths and plaster / paint against the freelancer (diagnostic; nothing released)

Only dry rooms carry the plaster and paint lines (UP-FIN-PAINT-001; wet rooms are fully tiled). The freelancer's sheet
uses one flat height per floor (GF 3.60 including the annex, 1F 3.40, living 3.50, 2F 3.40) and the same rows for paint.
Lengths were read from the printed dimensions; openings are NOT deducted (no opening height is printed on the plans:
gross figures; the freelancer deducts 58.25 m2 of openings from 1 209.39 m2 gross).

| Floor | Dry room (printed length) | Hand m2: rule with 0.60 beam (decor 0.15) | with the drawn 0.75 beam | Freelancer | Difference (0.60 rule) |
|---|---|---|---|---|---|
| GF annex | dewaneya 20.128 m (400 x 630 printed, corner arc R1.10 CAD) | 63.40 | 60.38 | 20.0 x 3.60 = 72.00 | -8.60 m2 (-11.9 %) |
| GF annex | driver 12.50 m (175 x 450) | 39.38 | 37.50 | 12.5 x 3.60 = 45.00 | -5.63 m2 (-12.5 %) |
| 1F | master bed room 17.50 m (425 x 450) | 58.63 | 56.00 | 17.5 x 3.40 = 59.50 | -0.88 m2 (-1.5 %) |
| 1F | master bed room 17.30 m (500 x 365) | 57.96 | 55.36 | 17.3 x 3.40 = 58.82 | -0.87 m2 (-1.5 %) |
| 2F | maid room 18.90 m (300 x 645) | 63.32 | 60.48 | 18.9 x 3.40 = 64.26 | -0.95 m2 (-1.5 %) |
| **5 matched rooms** | 86.328 m vs his 86.20 m (+0.128 m, +0.15 %) | **282.67** | **269.72** | **299.58** | **-16.91 m2 (-5.6 %); with the 0.75 beam -29.86 m2 (-10.0 %)** |
| 1F | master bed room 380 x 430: 16.20 m (room rectangle) | 54.27 | 51.84 | 22.3 x 3.40 = 75.82 (adds the two 3.05 m walls of the 1.47 m passage) | not comparable (allocation) |

Per floor, what stays HELD (never 0), with the freelancer's figure for that part:
- **GF** (freelancer 452.88 m2): open room 195.30 (beam 0.85 crossing, reception double height, no closed printed run),
  master bed room 75.78 (curved pool wall not dimensioned), stair wall 40.50 (stair). His "wash" 24.30 m2 is a basin-only
  space, wet by owner Q-06: not a plaster / paint line (RULE_DIFFERENCE).
- **1F** (441.27 m2): east master bed room 74.46 (curved glazing not dimensioned), living area 140.88 (open to the void
  and the curved stair), "basins corridor" 31.79 (not identified as a dry room on sheet 4 by this run).
- **2F** (94.86 m2): stair lobby 30.60 (stair, beam 1.20).
- Stair core 204.42, door reveals 15.96 (UP-FIN-PLASTER-001, frame detail), opening deductions -58.25: not measured here.
- Project: internal plaster HELD vs 1 151.14 m2, internal paint HELD vs 1 191.13 m2 (paint adds his 39.99 m2 of stair
  soffits). What this table can measure today is 6 dry rooms, 102.53 m of printed wall, 336.94 m2 at the owner's
  formula (0.60 beam, 0.15 decor), against his matching rows 375.40 m2 (31 % of his 1 209.39 m2 gross plaster rows).

Verdict proposals (for the verifier):
- Lengths: driver, both 1F master bed rooms and the maid room AGREE (identical printed lengths); dewaneya ENGINE_RIGHT
  +0.128 m (hand: 2 x (4.00 + 6.30) - 2 x 1.10 + 1.728 = 20.128 m, the printed rectangle with its drawn R1.10 corner;
  he rounds 20.0).
- Heights, 1F / 2F: RULE_DIFFERENCE: his flat 3.40 m is not the owner's formula (3.35 m with 0.60); -1.5 %.
- Heights, GF annex: proposal ENGINE_RIGHT once Q-50 is answered: his 3.60 m is the main house height applied to a storey
  printed 4.00 m high (SECTION B-B); by the owner's formula 3.15 m, -12.2 % on those two rooms (-14.22 m2). UNRESOLVED
  until then (held).
- 1F master bed room 380 x 430: RULE_DIFFERENCE (he allocates the passage walls to the room).

## 5. Held for the owner (with the reason)

1. Every room: drawn beam is not 0.60 m (0.40 / 0.50 / 0.75 / 0.85 / 1.20, table in section 3): owner question Q-50.
2. GF W.C. 175 x 135 and the 110 x 135 basin space by the stair: level unclear (+0.30 or +1.00).
3. Stair halls GF / 1F / 2F: walls run through the storeys; no owner rule for a stair-shaft wall height.
4. GF reception under the 1F void: double-height walls, no owner rule.
5. Wall lengths not printed as a closed run: GF open room, GF master bed room (curved pool wall), 1F east master bed room
   (curved glazing), 1F living area and corridor, 2F lobby: need the CAD outline (a code task, T-081 rework / V2.9 faces).
6. Wet rooms: wall tiles to the 0.15 m decor ceiling (owner Q-48 = A), so the same heights as above; not a plaster /
   paint line, and held on the same beam question Q-50.

## 6. What this changes and what is missing

- For the T-081 rework: the 12 one-level rooms and 8 derived GF rooms above are the hand truth for the unmarked-room step;
  the 2 held GF rooms must stay held; the annex is a separate 4.00 m zone; and a beam test needs the drawn beam per room,
  which on this villa is never 0.60 m.
- Not done here: the CAD outline of the 7 rooms without a closed printed run; opening deductions (opening heights are not
  on the plans; T-083); the pantry outline (owner Q-37).
