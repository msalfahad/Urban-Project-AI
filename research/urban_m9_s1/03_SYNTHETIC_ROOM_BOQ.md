# 03 Synthetic room BOQ (the S1 room schedule)

Input `SYNTHETIC_ROOMS_S1.json` (geometry source SYNTHETIC_FIXTURE): 6 rooms on two floors - two wet rooms, a polygon kitchen (layout BLOCKED for S2), and a store with no dimensions (BLOCKED_RFI). The room-by-room workbook is built by `tools/urban_boq_m9.py rooms` (xlsx: in the S1 ZIP only, never committed).

## Lines

| Floor | Room | Item | Net m2 | Evidence | Rule |
|---|---|---|---|---|---|
| GF | GF-BATH-01 | FIN.FLOOR.WET_TILE | 6.000 | SOURCE_DERIVED | UP-CER-001@1.0.0 |
| GF | GF-BATH-01 | FIN.WP.FLOOR | 6.000 | SOURCE_DERIVED | UP-WP-001@1.0.0 |
| GF | GF-BATH-01 | FIN.WP.DOORWAY | 0.160 | SOURCE_DERIVED | UP-WP-003@1.1.0 |
| GF | GF-BATH-01 | FIN.WP.UPTURN | 2.000 | SOURCE_DERIVED | UP-WP-002@2.0.0 |
| GF | GF-LIV-01 | FIN.FLOOR.PORCELAIN | 22.680 | SOURCE_DERIVED | UP-CER-001@1.0.0 |
| GF | GF-KIT-01 | FIN.FLOOR.PORCELAIN | 12.000 | SOURCE_DERIVED | UP-CER-001@1.0.0 |
| 1F | 1F-BED-01 | FIN.FLOOR.PORCELAIN | 15.120 | SOURCE_DERIVED | UP-CER-001@1.0.0 |
| 1F | 1F-BATH-02 | FIN.FLOOR.WET_TILE | 7.360 | SOURCE_DERIVED | UP-CER-001@1.0.0 |
| 1F | 1F-BATH-02 | FIN.WP.FLOOR | 7.360 | SOURCE_DERIVED | UP-WP-001@1.0.0 |
| 1F | 1F-BATH-02 | FIN.WP.DOORWAY | 0.180 | SOURCE_DERIVED | UP-WP-003@1.1.0 |
| 1F | 1F-BATH-02 | FIN.WP.UPTURN | 2.020 | SOURCE_DERIVED | UP-WP-002@2.0.0 |
| 1F | 1F-STORE-01 | FIN.FLOOR.PORCELAIN | - | BLOCKED_RFI | UP-CER-001@1.0.0 |

## Material results

| Room | Method | State | Units | Consumed m2 | Cutting waste m2 | Offcuts m2 | Packs | Blocked by |
|---|---|---|---|---|---|---|---|---|
| GF-BATH-01 | TILE_RECT_EXACT_V1 | COMPUTED_REVIEW | 9 | 6.480 | 0.016 | 0.490 | UNRESOLVED |  |
| GF-BATH-01 | MEMBRANE_RECT_EXACT_V1 | COMPUTED_REVIEW | 2 | 10.540 | 0.454 | 0.096 | 2 |  |
| GF-LIV-01 | TILE_RECT_EXACT_V1 | COMPUTED | 32 | 23.040 | 0.094 | 0.365 | 16 |  |
| GF-KIT-01 | TILE_RECT_EXACT_V1 | BLOCKED | - | - | - | - | UNRESOLVED | POLYGON_OPTIMIZER_NOT_IMPLEMENTED (S2): the S1 tile engine lays rectangles only |
| 1F-BED-01 | TILE_RECT_EXACT_V1 | COMPUTED | 42 | 15.120 | 0.085 | 0.000 | 11 |  |
| 1F-BATH-02 | TILE_RECT_EXACT_V1 | COMPUTED_REVIEW | 22 | 7.920 | 0.018 | 0.584 | UNRESOLVED |  |
| 1F-BATH-02 | MEMBRANE_RECT_EXACT_V1 | COMPUTED_REVIEW | 2 | 12.300 | 0.770 | 0.090 | 2 |  |

## Unresolved

| Room | Item | Question / reason |
|---|---|---|
| GF-BATH-01 | FIN.FLOOR.WET_TILE (boxes) | PACKAGING_NOT_ESTABLISHED: no pieces-per-box / roll data for the selected product (supplier or data sheet needed) |
| GF-BATH-01 | FIN.WP.DOORWAY / FIN.WP.UPTURN | DOORWAY_UPTURN_DETAIL_REQUIRED: Q-WP-1 how the doorway 0.20 m is built and whether it is billed in addition to the doorway floor piece (UP-WP-003 v1.1.0) |
| GF-BATH-01 | FIN.WP.DOORWAY / FIN.WP.UPTURN | DOORWAY_DOUBLE_COVERAGE_REVIEW: Q-WP-1 how the doorway 0.20 m is built and whether it is billed in addition to the doorway floor piece (UP-WP-003 v1.1.0) |
| GF-BATH-01 | FIN.WP (detailing) | CORNER_TREATMENT_NOT_SPECIFIED: 6 corner(s) counted, corner pieces not quantified |
| GF-BATH-01 | FIN.WP (detailing) | PENETRATION_DETAIL_NOT_SPECIFIED: 1 penetration(s) counted, collars / patches not quantified |
| GF-KIT-01 | FIN.FLOOR.PORCELAIN | POLYGON_OPTIMIZER_NOT_IMPLEMENTED (S2): the S1 tile engine lays rectangles only |
| 1F-BATH-02 | FIN.FLOOR.WET_TILE (boxes) | PACKAGING_NOT_ESTABLISHED: no pieces-per-box / roll data for the selected product (supplier or data sheet needed) |
| 1F-BATH-02 | FIN.WP (detailing) | CORNER_TREATMENT_NOT_SPECIFIED: 6 corner(s) counted, corner pieces not quantified |
| 1F-STORE-01 | FIN.FLOOR.PORCELAIN | ROOM_GEOMETRY_NOT_ESTABLISHED: room dimensions / polygon |
