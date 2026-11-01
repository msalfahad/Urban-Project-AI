# T-414 B3-05 floor screed / cement bed per room (FLOOR_BED_V1): owner manual method beside the drawn build-up

Worker 2 (lane A), 2026-11-01, run session_01E6cPnbbYArqNSvNCWw6g4A. Development villa, not an accuracy claim. ERS read;
s.2 steps 1-4 and 7, s.3 (physical vs contract, installed vs procurement, a value's scope not extended), s.4 applied.
Research only: research/agents_t414/* and tests/t414_floor_bed/*; no engine module, method, rule / knowledge version,
registry, candidate or released quantity changed. Candidate of record ARCH_TAKEOFF_V3.0.34 reproduced on the Drive copies
("Alsenan chalet project": P7757_DXF_COMPRESSED.zip -> P7757.dxf `ab54dd55`, 'ST7757 dxf.dxf' `9f9d1179`, decoded into
.work/private only): V3_0_34_BOQ_LINES.json `4c7f581c` (= T-399), 4,690 lines.

## 1. Result in engineering terms

| Space kind | Rows valued | m2 (status of each row's area) | Owner manual (Q-45), installed m3 | Drawing-derived m3 | Status of the thickness |
|---|---|---|---|---|---|
| DRY rooms + doorway strips (MORTAR_BED) | 19 (+13 NOT_APPLICABLE finish rows) | **288.1458** (DRAWING-CONFIRMED 17 rows, ASSUMED — OWNER-APPROVED 2: the open room 109.7784 and 1F-R3CFCFD 19.0165) | **8.6443 .. 11.5258** (0.03 .. 0.04 m) ASSUMED — OWNER-APPROVED | **HELD, bound 0 .. 14.3001** (area x b, b 0.050 / 1F 0.049 DRAWING-CONFIRMED, T-214) | HELD: the tile thickness is printed nowhere |
| WET rooms incl. kitchen, laundry, pantry (MORTAR_BED, 'bartash', no separate screed line: Q-41) | 21 | **85.5756** (DRAWING-CONFIRMED 14, ASSUMED — OWNER-APPROVED 7) | **3.4229 .. 5.1347** (0.04 .. 0.06 m) ASSUMED — OWNER-APPROVED | **HELD, no bound** (no section cuts a wet room; the 1F / 2F sunken drops are printed nowhere, D-41) | HELD |
| BALCONY (SCREED, own line, Q-41) | 0 on this villa | - | - | - | every exterior slab floor is a roof / terrace zone of B13-01 |
| Roof / terrace / stair / pool / foundation / outdoor ground | excluded (owned elsewhere) | - | - | - | B13-01 (T-321 / T-328), B7, T-309, T-219 / T-353, B13-02 |

Total B3-05 area **373.7214 m2** on 40 rows; installed bed by the owner's ranges **12.0672 .. 16.6605 m3** (PROVISIONAL,
NOT RELEASED). The owner's dry range is CONSISTENT with the drawn build-up on every dry row: 0.040 + adhesive 0 .. 0.003 <=
b 0.050, leaving 0.007 .. 0.020 m for the tile, which is exactly the slot T-214 named. Nothing is held as 0; no row is in
two families. Room table: `ROOM_TABLE_T414.csv` (line id, engine element, kind, layer, candidate state, area status, m2,
FFL, slab top, b, both m3, the owner check, the membrane relation, what is missing); `summary.json`.

## 2. The physical element (ERS s.2 step 1, s.3)

B3-05 is the cement-sand layer laid on the structural slab (dry room) or on the membrane (wet room) under the floor finish
of one room: one layer of the build-up b = FFL - structural top (T-214). Physically t_layer = b - t_finish - t_adhesive;
installed m3 = area x t_layer. Kept apart:

- **Contract form** (Q-41, owner's words "if it is roof or balconies it is screed; bathrooms, cement is enough"): dry and
  wet rooms get a MORTAR_BED under the tiles (wet: the only layer above the membrane; no falls / protection screed line),
  balconies a SCREED as its own line; roofs and terraces belong to the roof build-up (B13-01), stairs to the stair bed (B7).
- **Physical vs a rate**: whether a tiler's rate includes the bed is a pricing question; the layer is built in every row
  and is reported as an installed quantity, never priced here.
- **Installed vs procurement**: cement bags, sand and 5 % waste are the procurement view of
  engine/source/finish_materials_table.py (T-086) and are NOT mixed into the installed m3 above.
- **Which rooms are wet**: the wet-room tile code, or a room whose WHOLE floor is under the membrane (FIN.WP.FLOOR area =
  floor area: the kitchen GF-RA3AD49, Q-30 A). A membrane over PART of a dry room (the open room's pantry, 13.5 m2 inside
  GF-RC99C2A) does not make the room wet: the candidate already carries that part as four wet lines (2.800001 + 8.954867 +
  0.600 + 1.100 = 13.454867 m2, Q-37 A) and nets it out of the open-room line (118.733284 - 8.954867 = 109.778417).
- **NOT_APPLICABLE finish rows** (13 doorway strips and the pantry room face whose line states 'no floor' with evidence):
  no finish there, so no bed: NOT_APPLICABLE, never a held 0.

## 3. Methods side by side (ERS s.2 step 2)

| Room kind | Owner manual method | Drawing-derived method | Residual / why they are not merged |
|---|---|---|---|
| DRY | Q-45: bed 0.03 .. 0.04 m (+ adhesive <= 3 mm + tile) | b = 0.05 (GF main, annex) / 0.049 (1F) drawn on SECTION A-A / B-B, DRAWING-CONFIRMED (T-214, Checker merged); t_finish not printed -> 0 < t_layer <= b | owner range lies inside the drawn bound: CONSISTENT; the 0.007 .. 0.020 m left is the unprinted tile, named, not closed |
| WET | Q-45: 0.04 .. 0.06 m with 1 % falls | b HELD: no section cuts a wet room; the 1F / 2F wet panels are sunken with an unprinted drop | the owner's 0.06 exceeds the dry b 0.05, so the wet rooms cannot share the dry level: the dry layer is never carried to them (STEPPED_SLAB_NOT_OWN_LEVEL) |
| BALCONY | Q-41 screed, thickness not given | constant drawn layer refused against falls (T-214) | both HELD |

## 4. Freelancer (quantities only; Drive "Alsenan chalet project", floors / waterproofing / decor / marble workbook)

He has **no screed, bed, cement or sand row** (B3-05 is an engine-only line, as T-086 found for the mortar). The area
basis compares with his tiled-floor rows (409.58 m2 = 337.57 dry + 72.01 wet):

- Wet **85.5756 vs 72.01 m2 (+13.5656, +18.8 %)**, fully TRACED: the pantry 13.4549 m2 (Q-37 A, he has no pantry row)
  + 0.1107 m2 on the 17 wet areas (T-074 hand table, +0.16 %, VERIFIED). Verdict: RULE_DIFFERENCE (pantry) /
  ENGINE_RIGHT (T-074).
- Dry **288.1458 vs 337.57 m2 (-49.4242, -14.6 %)**, inherited from the floor-finish family (B3-01), not from the bed:
  GF open room 111.8484 (109.7784 + under-stair 2.07) vs his reception + dining 137.50 + entrance 10.46 = 147.96
  (-36.1116: the pantry 13.4549 moved to wet, the below-cut stair treads 6.1244 = 8.194412 - 2.07, and **16.53 m2
  UNRESOLVED**, the entrance / stair-hall floor that has no candidate floor line); 1F living 33.711 vs 38.96 (-5.249,
  T-345 traced the line, the corridor split UNRESOLVED, T-086); **2F stair lobby: no candidate floor line** vs his
  corridor 7.70 (printed 4.50 x 1.95 = 8.775, T-086); seven rooms within -0.95 .. +0.10 m2 (T-086 verdicts stand);
  doorway strips +1.25 (he has none). Rooms with no floor-finish line get NO bed row here: UNKNOWN by inheritance, never 0;
  the fix belongs to the floor-area family (lane A row on B3-01, see s.7).

## 5. One layer, one item (acceptance b)

`summary.json` `double_counted: []`. On the B3-05 rooms the only other layers are the membrane lines B8-01 / B8-02 / B8-03
(a different layer, reported beside); 16 roof-layer lines (B13-01), 62 stair finish lines (B7) and 4 outdoor paving lines
(B13-02) are owned elsewhere and contribute 0 rows; the pool (T-309) and foundation screed (T-219 / T-353) have no floor-
finish line in the candidate. A roof / terrace offered as a B3-05 row is refused (OWNED_ELSEWHERE).

## 6. Rule, test and lessons row (proposed)

Rule R-T414-1 (any villa, provenance T-414; owner rules Q-41 / Q-45 at their own scope): the B3-05 layer of a room is
MORTAR_BED (dry, wet) or SCREED (balcony) by Q-41; its area is the room's floor-finish line (HELD stays HELD,
NOT_APPLICABLE carries nothing); its thickness is reported twice, never merged: the owner's Q-45 range (ASSUMED — OWNER-
APPROVED, checked CONSISTENT / PARTLY / CONFLICT against the drawn b) and the drawing-derived b - t_finish - t_adhesive
with b from the room's OWN zone (a sunken / wet room never takes the dry b) and t_finish only as printed (else a bound
0 .. b, else HELD); roofs / terraces / stairs / pool / foundation / ground paving are other families.

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | B3-05 had no line on any villa; the bed existed only as a T-086 material range on V2.9 areas | the bed thickness was treated as unknowable, so no per-room layer was carried, although the drawn build-up b bounds it and the owner gave ranges | R-T414-1 above (any villa) | tests/t414_floor_bed (K414 normal: dry bound + owner range, printed finish -> drawing range, sunken own level, balcony screed HELD, NA row; adverse: defaulted thickness, roof counted twice / roof screed overlap, held as 0, sunken / wet room given the dry b, same room twice, owner bed that cannot fit = CONFLICT, units mm / ft) | proposed |

## 7. Proposal for lane I and what is missing

- Lane I row: carry FLOOR_BED_V1 into the next candidate as B3-05 lines `FIN.FLOOR.BED.DRY` / `FIN.FLOOR.BED.WET`
  (m2 = the floor-finish line, installed m3 on the owner range ASSUMED — OWNER-APPROVED, the drawing bound beside),
  binding each to its finish line id; NOT RELEASED.
- Missing: the tile / stone thickness (printed nowhere; no owner rule) -> the drawn bed stays HELD; the wet-room and
  sunken-panel levels (D-40 / D-41); floor-finish lines for the GF entrance / stair hall and the 2F stair lobby (B3-01
  gap, new lane A row recommended); balcony screed thickness (Q-41, no balcony on this villa).
- No owner question: ERS s.2.7 is not met (the tile thickness is an unprinted design value for the designer item D-40,
  not an owner decision; the owner ranges already exist).

## 8. For the Checker (re-measure, not from this file)

1. Re-run research/agents_t399/v3034_run.py on the Drive copies (sha `4c7f581c`), then
   `python3 -I research/agents_t414/t414_alsenan.py <dir>`: 53 rows, table sha in summary.json.
2. By hand: the open-room net 118.733284 - 8.954867 = 109.778417 (line formula), the pantry box 13.5 = 0.045 + 2.800001 +
   8.954867 + 0.600 + 1.100 (T-286 closure), and one dry row: 1F-R0E919A 16.34 x 0.049 = 0.8007 m3 bound, 16.34 x 0.03 ..
   0.04 = 0.4902 .. 0.6536.
3. The kitchen GF-RA3AD49: FIN.WP.FLOOR 9.630001 = floor 9.630001 (whole room under the membrane, Q-30 A).
