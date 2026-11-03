# T-455 B3 TILES purchase quantities (adhesive bags, tile boxes)

Method: `engine/source/finish_materials_table_v4.py` (FINISH_MATERIALS_TABLE_V4, UNWIRED_PRODUCER; V1 .. V3 untouched).
Ledger beside candidate V3.0.45: `research/agents_t455/t455_tile_purchase.py` -> `out/TILE_PURCHASE_T455.{json,csv}`.
No candidate or released line moves.

## Physical element and rules

A tiled surface of one tile product. Bought for it: 20 kg adhesive bags (one adhesive product per purchasing group) and
whole boxes of the tile product. Net area, consumption, cutting waste (from the room layout, UP-CER-010), packaging
surplus, spare and purchase are separate figures.

| Rule | Value | Status |
|---|---|---|
| UPC-ADHESIVE-001@1.0.0 | 60 x 60 / normal 5 m2, 120 x 60 3 m2, 160 x 80 3 m2 per 20 kg bag; ceil per product at the purchasing group | OWNER CONFIRMED 2026-11-02 |
| UP-CER-010@1.0.0 | cutting waste from the room layout of the selected size; never a flat size percentage | OWNER APPROVED 2026-10-12 |
| Q-59 B modified | offcut reuse inside the same room only: OPTIMISED beside CONSERVATIVE | owner 2026-10-20 |
| B3 directive | boxes at PROJECT level per tile type; one spare box per tile type | owner 2026-11-02 |
| Q-42 | joint 1 mm inside, 2 mm outside (enters the layout count only) | owner 2026-10-19 |

Not given anywhere (HELD, never defaulted): tile sizes of the training villa, tile products, pieces per box.

## What changed (V3 -> V4)

1. Adhesive by tile size, fractional per row, one ceil per purchasing group. V3 used 5 m2 per bag whatever the size and
   printed a project "bags to buy" from a partial sum when rows were held. V4: a held row makes the group HELD with its
   known part and an owner-rule BOUND (area / 5 .. area / 3); per floor / per kind is never rounded.
2. Boxes per tile product: tiles = sum of the rooms' layout counts (TILE_COUNT_V1 on TILE_POLYGON_GRID_V1, any simple
   polygon with obstructions: a non-rectangular room is no longer blocked); boxes = ceil(project tiles / pieces per box)
   + 1 spare; the per-room-rounded figure is reported beside it (project <= per room: ceil of a sum <= sum of ceils).
3. `purchase_from_lines()` applies the same rules to areas measured upstream (a candidate line index).

## Worked example (non-training fixture, tests/t455_tile_purchase)

60 x 60 product P-A, 4 pieces / box (fixture packaging), joint 1 mm:

| Room | Net m2 | Conservative | Optimised (in-room reuse) |
|---|---|---|---|
| R1 2.00 x 1.50 | 3.00 | 12 (4 x 3 positions, 6 whole + 6 cut) | 9 (3 strips 0.6 x 0.298 from 2 tiles; 2 strips 0.197 + corner from 1) |
| R2 L 2.40 x 2.40 less 1.20 x 1.20 | 4.32 | 12 | 12 (offcuts 1 - 3 mm) |
| R3 2.50 x 2.00 | 5.00 | 20 | 15 |
| Product | 12.32 | 44 -> project 11 + 1 = 12 boxes; per room 3 + 3 + 5 + 1 = 12 | 36 -> 9 + 1 = 10; per room 3 + 3 + 4 + 1 = 11 (1 box saved) |

Adhesive, one group: 0.6 + 0.864 + 1.0 + wet wall 20.16 / 3 = 6.72 -> 9.184 -> 10 bags (V3: 32.48 / 5 = 6.496, the
120 x 60 wall understated by 2.688 bags). Net lower bound 12.32 / 0.36 -> 35 tiles is shown, never used as the count.

## Training villa (candidate V3.0.45, ledger)

| Item code | Lines (rel / held) | Released m2 | V3 bags (any size) | V4 bags | Owner-rule bound |
|---|---|---|---|---|---|
| FIN.FLOOR.PORCELAIN | 22 / 0 | 305.0210 | 61.0042 | HELD (no size) | 61.004 .. 101.674 |
| FIN.FLOOR.WET_TILE | 20 / 0 | 75.9456 | 15.1891 | HELD | 15.189 .. 25.315 |
| FIN.WALL.TILE | 12 / 6 | 340.3038 | 68.0608 | HELD | 68.061 .. 113.435 (6 faces without area) |
| EXT.FLOOR.PORCELAIN | 1 / 0 | 21.0142 | 4.2028 | HELD | 4.203 .. 7.005 |
| FIN.FLOOR.FINISH_HELD | 2 / 1 | 6.1275 | none (finish not named) | HELD | none |
| Total | 57 / 7 (13 EXCLUDED) | 748.4121 | 148.4569 -> V3 printed 149 | HELD | 148.457 .. 247.428 on released lines |

Size evidence: the architectural DXF census (T-087) read 276 texts, 0 tile size notes; the ground-floor PDF sheet 03
(Drive "Alsenan chalet project", p7757_arch_sheet03.pdf) has no text layer and its wet block shows room names,
dimensions, levels and a drafted hatch only (a pattern, never scaled). Boxes: HELD for all 61 porcelain lines
(no product named, no packaging). Freelancer: no adhesive or box line in the keymap (NOT COMPARED).

Effect: V3's 148.457 bags (149) was a size-blind figure that equals the LOW end of the owner rule; if the large formats
(120 x 60 / 160 x 80) are chosen it rises to 247.428 (+66.7 %). Released quantities: none changed.

## Verdict proposal and lesson

UNRESOLVED (input missing, not a rule question): adhesive bags and boxes of the training villa wait on the tile size
and product per room (a finishes schedule or an owner project decision, level 1 / 2), and on pieces per box (supplier
sheet). Proposed lesson (s.7): "a material rate keyed by a product property (tile size) is HELD when the property is
not sourced; the size-blind rate is the bound's low end, never the quantity" - rule R-T455-3, tests normal (sizes
given) and adverse (size absent -> HELD with bound; 30 x 30 not classified -> HELD).
