# T-086: room-by-room finishing table with mortar, cement, sand and adhesive (owner request, Q-45)

Worker 3, 2026-10-20 00:02-00:14 UTC. Gate 2 (architectural coverage: floors, wet areas, tiles). Development villa
(Alsenan) only; NOT an accuracy claim. New method piece `engine/source/finish_materials_table.py`
(FINISH_MATERIALS_TABLE_V1), read by no released method: no released quantity changed.

## What the piece does

Per element (dry floor, wet floor, wet wall, stair flight, stair landing, roof) it takes an area from a merged engine
piece or a verified hand table and gives: bed thickness range, mortar m3 (low / high, 5 % waste), cement bags of
50 kg and loose sand m3 (1:4 only), adhesive bags of 20 kg; then sums per floor, per kind and for the project, with the
held rows listed and never added as 0. Values only from the owner:

| Value | Owner source |
|---|---|
| bed: regular floors 3 - 4 cm, wet floors (bartash) 4 - 6 cm | Q-45 answer, his own words |
| stairs 3 cm 1:3; wall mortar 2 cm 1:4; floors and bartash 1:4; 8 bags + 1.1 m3 sand per m3 of 1:4; waste 5 % on mortar | Q-45 option B, practice values he accepted (PROVISIONAL) |
| adhesive 20 kg covers 5 m2 of ceramic / porcelain | Q-45 answer (bag photo) |
| wall tiles floor to the underside of the 0.15 m decor ceiling, each door over its width | Q-48 A |
| one step = one tread + one riser of the flight width; section counts | Q-19, Q-46 A, Q-47 A |
| roofs and balconies get a screed, thickness not given | Q-41 |

HELD because the owner gave no value (never a typical figure): cement bags and sand for the 1:3 stair mortar (Q-45 gives
them for 1:4 only), roof / balcony screed thickness (Q-41), marble and stone adhesive coverage (Q-45), roof finish.

## Alsenan result (engine vs freelancer; freelancer = FIN workbook, tiles sheet)

| Trade line | Engine | Freelancer | Difference | Status |
|---|---|---|---|---|
| Wet floors, 17 areas | 72.12 m2 | 72.01 m2 | +0.11 m2 (+0.16 %) | RELEASED (verified hand table) |
| Wet floors with the pantry (Q-37 A, 4.50 x 3.00) | 85.62 m2 | no pantry row | +13.50 m2 | RELEASED |
| Dry floors, 10 rooms both have | 194.98 m2 | 189.61 m2 | +5.37 m2 (+2.83 %) | RELEASED (V2.9 porcelain lines) |
| Dry floors, all released (incl. doorway strips 5.77 m2) | 200.75 m2 | 337.57 m2 | open plan room HELD | 5 rows HELD |
| Open-plan dining / reception / saloon | HELD (candidate 108.03 m2) | 137.50 + entrance 10.46 m2 | not compared | HELD: V2.9 zone bounded by non-wall lines |
| Wet-room wall tiles | HELD (candidate 403.02 m2 on 15 rooms, before windows) | 433.83 m2 (at 3.00 m) | not compared | HELD: owner Q-52 open (no 0.60 m beam drawn) |
| Stair marble (treads + risers + landings, 6 flights + 2 landings) | 39.49 m2 | his steps are counted as number x width (63 + 28 + 5 steps) | not comparable (unit) | winders and round stair HELD (Q-50, Q-51) |
| Roofs inside the parapet (2 of 3) | 204.11 m2 | - | - | area RELEASED, screed and finish HELD |

Materials (all PROVISIONAL, owner practice values; low = thin bed, high = thick bed; whole bags rounded up on the sum):

| Surface | Mortar m3 | Cement bags 50 kg | Sand m3 | Adhesive bags 20 kg |
|---|---|---|---|---|
| Wet floors 85.62 m2 (bartash 4 - 6 cm) | 3.60 - 5.39 | 28.8 - 43.2 (buy 29 - 44) | 3.96 - 5.93 | 17.1 (buy 18) |
| Dry floors 200.75 m2 (3 - 4 cm) | 6.32 - 8.43 | 50.6 - 67.5 (buy 51 - 68) | 6.96 - 9.27 | 40.2 (buy 41) |
| Stairs 39.49 m2 (3 cm, 1:3) | 1.24 | HELD (1:3 not given) | HELD | HELD (marble) |
| Wet walls | HELD | HELD | HELD | HELD |
| Project (released rows) | 11.16 - 15.07 | 79.4 - 110.6 (buy 80 - 111) | 10.91 - 15.21 | 57.3 (buy 58) |

The freelancer has no cement, sand or adhesive line: these are engine-only lines.

## Who is right (proposals for the verifier)

- Dewaneya 24.94 vs 24.84 (+0.4 %), GF master 16.55 vs 16.66 (-0.7 %), driver 7.875 vs 7.87, 1F masters 19.05 vs
  19.00, 18.22 vs 18.25, maid 19.35 vs 19.58 (-1.2 %): AGREE within 1.2 % (drawn face vs his rounded dimensions).
- 1F master 380 x 430: 16.34 vs 17.29 m2 (-5.5 %): the room itself is ENGINE_RIGHT (printed 3.80 x 4.30 = 16.34,
  T-088); the freelancer's extra 0.95 m2 is probably part of the room's 1.47 x 3.05 passage (T-088: "the passage is not
  counted in it"). In which V2.9 face that passage floor sits was not hand-checked: UNRESOLVED for the passage. (The
  unlabelled face 1F-RFFE7AF, 1.80 x 1.65 = 2.97 m2, is a different space: it opens through OP-019.)
- 1F master 420 x 400 with passage: 19.02 vs 19.46 m2 (-2.3 %): UNRESOLVED (curved glazing edge not dimensioned).
- 1F living 44.87 vs 38.96 m2 (+15.2 %): UNRESOLVED. V2.9 nets 75.98 m2 by the void (16.01), its stair treads (8.34)
  and the flight seen through the opening (6.77); the face also holds the corridor / stair landing at +5.50 (T-088 1F-05),
  which the freelancer has no row for. A hand split of corridor vs living is needed.
- 2F stair lobby 8.775 vs 7.70 m2 (+14.0 %): ENGINE_RIGHT proposal: printed 4.50 x 1.95 = 8.775 (T-088, page 5).
- Wet floors: as T-074 (verified): 8 ENGINE_RIGHT / RULE_DIFFERENCE, total +0.16 %.
- Wet walls: RULE_DIFFERENCE in height (his 3.00 m is printed nowhere; owner Q-48 A gives 3.15 / 3.35 / 3.65) and
  UNRESOLVED until Q-52; his length 144.6 lm includes the door widths, Q-48 takes them out.

## Every V2.9 face is accounted for

`alsenan_finish_summary.json` "face_census": 38 faces: 9 dry rows, 2 in the HELD open-plan row, 17 matched to a wet-area
row, 4 HELD rows (GF stair hall, 3 unlabelled faces of 3.60, 1.56 and 2.97 m2), 3 shafts, 1 garden, 1 merged zone and the
2F stair face (its printed lobby is a row). Faces not in the table: 0.

## What is missing or uncertain

- Wet-wall m2 and its mortar and adhesive wait on owner Q-52 (beam depth) and on the window heights (only 1 of the 11
  wet-room windows prints a height, T-083); GF-10 and GF-11 also wait on their floor level (Q-43, T-088).
- Stair cement and sand wait on the 1:3 bag and sand values; marble adhesive on its coverage (Q-45).
- The V2.9 tread deduction uses its own tread width (1.15 m) and the stair rows the printed 1.20 m: up to about
  0.05 m x tread length per tread may sit in both the porcelain and the marble (not measured; under 0.5 m2).
- Not in this table: skirting, the GF annex roof (T-071 HELD), the second-floor top roof (Q-34 parked), balconies.

Files: `alsenan_finish_table.py` (run), `ALSENAN_FINISH_TABLE.csv` (70 rows), `alsenan_finish_summary.json` (sums,
comparison, face census). Inputs read in the session scratchpad from Drive "Alsenan chalet project" (P7757_DXF_COMPRESSED.zip),
never copied here.
