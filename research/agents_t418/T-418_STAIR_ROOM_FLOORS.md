# T-418: floor parts of the stair rooms, the silent omission of the floor-finish family (B3-01)

Worker 2 (lane A), 2026-11-01. Gate 2. Research only: nothing is wired, no released or candidate quantity changes.
Development villa, not an accuracy claim. Inputs: Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip (architectural
DXF, sha256 ab54dd55) and "ST7757 dxf.dxf" (sha256 9f9d1179), decoded into .work/private only; the candidate of record
the candidate of record ARCH_TAKEOFF_V3.0.35 reproduced on them by research/agents_t400/v3035_run.py (own run this
task: V3_0_35_BOQ_LINES.json sha256 b011bace and V3_0_34 4c7f581c, both = the T-400 / T-399 pins; 4,730 lines, 33
FIN.FLOOR.PORCELAIN + 20 FIN.FLOOR.WET_TILE). Merged ledgers T-111 (stair flights), T-129 (2F arrival, Q-70 A), T-147 (room faces), T-153 (spaces), T-086.

## 1. The physical question (ERS s.2.1)

Each candidate room that holds a stair (the GF stair room GF-R31F8AE, face 12.475 m2; the 2F stair hall 2F-R4D1B62,
face 18.600 m2) receives NO floor-finish line in V3.0.35, although both faces contain walkable floor at a printed level.
The "16.53 m2 entrance / stair hall" named in T-414 is NOT one space: it is a residual of the GF open-room comparison
(section 4). The entrance hall itself is inside the open room GF-RC99C2A (T-153: "dining, reception, saloon, entrance and
the hall to the master bed room") and has its line; what has no line is the floor INSIDE the stair rooms.

## 2. Space table (room-local dimensions; SPACE_TABLE_T418.csv)

GF stair room, 2.500 x 5.000 inner less the column 0.050 x 0.500 proud of the west wall = 12.475 m2 (engine face):

| Part | Owner | m2 | Level | Evidence | Status |
|---|---|---|---|---|---|
| hall at the foot of MS1-L / top of D1 (south door to the D1 top riser) | B3-01 FLOOR | **4.8050** (2.50 x 0.45 + 1.15 x 0.70 + 1.15 x 2.50) | +1.00 (mark inside) | layer 1 walls, layer 2 MS1-L first riser 1.150 from the south wall, divider 0.450 .. 3.850, layer 5 D1 top riser 2.950 | area DRAWING-CONFIRMED; finish HELD (porcelain if floor / marble if landing) |
| back-door lobby under the +3.50 half landing | B3-01 FLOOR | **1.3225** (1.15 x 1.15) | +0.30 (mark inside) | north door 0.890 to the north court (+0.15); D1 foot riser 3.850 | area DRAWING-CONFIRMED; finish HELD as above; sub-level floor |
| MS1-L treads below the cut, less the column | B7 | 3.0800 | - | 10 riser lines at 0.300 (T-111 2.700 m) | owned by STAIRS |
| MS1-T winders, NW quarter | B7 | 1.3225 | - | radial layer-2 lines | STAIRS |
| D1 3 treads | B7 | 1.0350 | - | 4 riser lines (layer 5) at 0.300 | STAIRS |
| central divider 0.200 | SOLID | 0.6800 | - | layer 2 closed outline | no floor |
| strip north of the divider end | UNREAD | HELD 0 .. 0.2300 | - | two unread layer-2 lines | HELD (never 0) |

2F stair hall, face 18.600 m2 (T-129 MERGED, re-read this run on layers 1 / 2 / 5 / D):

| Part | Owner | m2 | Evidence | Status |
|---|---|---|---|---|
| floor beyond the stair width, printed (450 - 250) x 125 | B3-01 FLOOR | **2.5000** | lift box face at 1.250, maid-room door, '+9.70' | area DRAWING-CONFIRMED; porcelain ASSUMED — OWNER-APPROVED (Q-70 A names it porcelain) |
| arrival 250 x 195 | B7 | 4.8750 | owner Q-70 A, condition met (T-129) | STAIRS (marble) |
| east-lane foot strip 1.15 x 0.35 | B7 | 0.4025 | inside flight row ST-MS2-U | STAIRS |
| slab opening over the 1F-2F flights | VOID | 10.8225 | T-129 O-2F | no floor |

Both faces re-add to 0.0000 m2 and no two parts overlap (STAIR_ROOM_FLOOR_V1 refuses either). New floor-finish parts:
**8.6275 m2 DRAWING-CONFIRMED** (GF 6.1275, 2F 2.5000) + **0 .. 0.2300 HELD**; stairs B7 parts 10.715 m2 stay STAIRS.

## 3. Why the candidate missed them (rule R-T418-1, every villa)

Both faces are labelled STAIR (ARCH_ROOMS: codes ['STAIR'], kind STAIR, name 'Stair'). The floor reconciliation
engine/source/arch_floor.py:94-96 then puts the WHOLE rest of a STAIR-only face (face - void - drawn treads) into
STAIR_LANDINGS_BOUND ("an upper bound of the landings"), never into ROOM_FLOOR: GF-R31F8AE = treads 3.425 + landings
bound 9.050; 2F-R4D1B62 = treads 6.875 + landings bound 11.725 (V3.0.4 stage; the V3.0.35 lines carry it). No floor-finish
line is ever built from STAIR_LANDINGS_BOUND, so the floor at the foot of a flight, a lower lobby under a landing and
the floor beyond the stair width at an arrival fall out silently, lumped with real landings, winders and the well. In open-plan cases (the 1F living, the GF round stair) the stair lies inside a floored room and the
floor survives; in a walled stair room it is lost. R-T418-1: a stair room face is partitioned, never dropped (B7 /
FLOOR / VOID / SOLID / UNREAD), the parts re-add to the face, a floor part needs level evidence (else HELD), a floor part
over a tread, a porch or another room's floor is refused, and every floor part is bound to a floor-finish line or
reported SILENT_OMISSION. Not an Alsenan constant: no layer name, room id or dimension of this villa is in the module.

Finish (area and finish are separate data, owner Q-56): no sheet prints a finish schedule (T-091, T-153). The 2F part
is named porcelain by owner Q-70 A ('candidate lobby porcelain'): ASSUMED — OWNER-APPROVED. The two GF parts sit at the
foot of a flight (MS1-L) and at the top / foot of D1, with no printed landing depth: URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1
never applies to STAIR (rules/methods/URBAN_METHOD_REGISTER_V3.json) and UP-STAIR-005 makes a landing marble, and Q-70 A
says to keep the finish HELD when the geometry does not establish a landing. So their AREA (6.1275 m2) is a floor-finish
quantity DRAWING-CONFIRMED and their FINISH is HELD (porcelain or marble), never chosen. The freelancer's main-stair
landing marble row (6.20 m2, no breakdown) may hold this hall; a match by figure is refused. No owner question now:
the finish is a designer / finish-schedule item for the Lead's RFI list (ERS 2.7 is met only if the designer cannot
answer); nothing else waits on it.

## 4. Dry floor against the freelancer (FIN workbook, tiles sheet; 337.57 m2)

Candidate dry 288.1458 (-49.4242, -14.6 %) -> with these parts, as floor-finish area (GF finish HELD), 296.7733 m2
(**-40.7967, -12.09 %**). The difference
closes on these components (summary.json, sum = difference to 0.0001):

| Component | m2 | Class | Verdict proposal |
|---|---|---|---|
| GF pantry floored wet (Q-37 A) | -13.4549 | TRACED | RULE_DIFFERENCE |
| GF round-stair treads below the cut (B7) | -6.1244 | TRACED | RULE_DIFFERENCE |
| GF garden band in the reception (D-48) | -13.9860 | HELD | UNRESOLVED (designer) |
| GF stair-room floor (this task; area DC, finish HELD) | +6.1275 | TRACED | UNRESOLVED: no floor row of his; his landing row 6.20 m2 may hold it (no breakdown, no match by figure) |
| GF open-room residual | -2.5463 | UNEXPLAINED | UNRESOLVED |
| GF master / dewaneya / driver | -0.0051 | TRACED | T-086 |
| doorway strips valued (GF 0.35, 1F 0.72, 2F 0.18) | +1.2500 | TRACED | engine-only |
| 1F living (Q-66 B landing + T-345) | -5.2490 | TRACED | RULE_DIFFERENCE |
| 1F bed rooms | -1.3785 | TRACED | T-086 |
| 2F maid room | -0.2300 | TRACED | T-086 |
| 2F arrival marble (Q-70 A, B7) | -4.8750 | TRACED | RULE_DIFFERENCE |
| 2F corridor residual (his 7.70, no dimensions) | -0.3250 | UNEXPLAINED | UNRESOLVED |

The "16.53 m2 UNRESOLVED" of T-414 = garden band 13.9860 HELD + 2.5463 unexplained; it is not a missing room.

## 5. Cross-trade findings (no quantity changed here)

- ONE m2 ONE LINE: each stair room carries a FIN.MARBLE.LANDING line BOUNDED_EXPOSURE 0 .. (face - drawn treads):
  GF L-1983e89d 0 .. 9.050, 2F L-5d2be30d 0 .. 11.725. Those upper bounds hold the floor parts above; when the floor
  lines are integrated the bounds become 0 .. 2.9225 and 0 .. 9.2250 (summary.json landing_bound_overlap). Bound only.
- STAIRS (for T-412, tread census): the candidate's GF-R31F8AE tread line is 2.415 m2 = 7 treads x 0.300 x 1.150, while
  the plan draws 10 MS1-L riser lines at 0.300 over 2.700 m = 9 straight treads (T-111): 3.105 m2 less the 0.025 column
  = 3.080 m2 inside this face. Not changed here; B7 owns it.
- STAIRS (for T-412): on 2F-R4D1B62 V3.0.35 values two tread lines 3.450 + 3.450 m2 PROVISIONAL (L-79beb968, L-07f00d5b),
  while the merged T-135 ledger reads the 2F F1 HELD (stacked, step count differs) and F2 SEEN_ABOVE (0); and the 2F
  arrival 4.875 m2 marble (Q-70 A) is carried only inside the 0 .. 11.725 landing bound, never as a figure.

## 6. What remains

HELD: the 0.200 x 1.150 strip (0 .. 0.2300 m2); the garden band (D-48). UNEXPLAINED: GF open room -2.5463, 2F corridor
-0.3250. Doorway strip of the GF stair-room south door and the lift-door recess on 2F (lift threshold, T-413) are not
floor-finish parts here. Lane I proposal (with T-420): a FIN.FLOOR.PORCELAIN line 2F stair lobby 2.5000
(area DRAWING-CONFIRMED, finish ASSUMED — OWNER-APPROVED Q-70 A); two floor-finish lines GF stair hall 4.8050 (+1.00)
and GF back lobby 1.3225 (+0.30) with area DRAWING-CONFIRMED and finish HELD (porcelain / marble), never folded into the
landing marble or the porcelain total as a figure; the two FIN.MARBLE.LANDING bound lines on these faces lose the floor
parts from their upper bound (summary.json landing_bound_overlap); the B3-05 bed follows each line once it exists.

Lesson row (ERS s.7): a stair room face dropped whole from the floor-finish family (rule R-T418-1 above; test
tests/t418_stair_room_floor).
