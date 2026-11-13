# T-769 fix rows: fence, gates, pool face, outdoor floor and site families (V3.0.79 index)

Lines without a point figure in these families: 37 -> 0; rows 37; new lines for missing families 4 (B1-01, B1-05, B1-06 NOT_APPLICABLE, B1-07).

| vs freelancer | candidate | freelancer | diff | % |
|---|---|---|---|---|
| fence block above N.G. vs freelancer 'السور' 74.40 m2 | 95.44 | 74.40 | +21.04 | +28.3 % |
| fence plaster / paint vs freelancer exterior rows 87-90 107.24 m2 | 179.84 | 107.24 | +72.60 | +67.7 % |
| pool water face vs freelancer 40.80 m2 | 21.31 | 40.80 | -19.49 | -47.8 % |

| item | lines | after |
|---|---|---|
| EXT.FENCE.BLOCK [m2] | 4 | 95.4415 |
| EXT.FENCE.BLOCK_COUNT [pcs] | 1 | 1486.0 |
| EXT.FENCE.FACE [m2] | 7 | 41.4614 |
| EXT.FENCE.GATE [pcs] | 2 | 2.0 |
| EXT.FENCE.MASONRY_BELOW_NG [m2] | 1 | 23.4099 |
| EXT.FENCE.PAINT [m2] | 8 | 179.8425 |
| EXT.FENCE.PLASTER [m2] | 8 | 179.8425 |
| EXT.FENCE.TOP [lm] | 1 | 6.727 |
| EXT.FENCE.WALL [m2] | 2 | 9.54 |
| EXT.FLOOR.OUTDOOR [m2] | 2 | 17.2274 |
| EXT.POOL.WATER_FACE [m2] | 1 | 21.3087 |

| line | item | unit | element | before | after | label | basis |
|---|---|---|---|---|---|---|---|
| L-138c597bc2aa55cb2a99 | EXT.FENCE.FACE | m2 | FENCE:F-STREET:FACE:OUTSIDE | BLANK | 11.251 | ESTIMATE | 5.80 x 2.65 printed = 15.370 - dip / rounded gate end 4.119 m2 scaled from the p.12 elevation 1:100 = 11.251 |
| L-778a67b2fbd8b61f88ad | EXT.FENCE.FACE | m2 | FENCE:F-STREET:FACE:PLOT | BLANK | 10.721 | ESTIMATE | 5.60 x 2.65 printed = 14.840 - the same scaled dip 4.119 m2 = 10.721 |
| L-7aaa47641fd87354fb5d | EXT.FENCE.FACE | m2 | FENCE:F-STREET:FACE:END-G-01 | BLANK | 0.4094 | ESTIMATE | stop-end at G-01 0.20 x (2.65 - 0.603 scaled drop of the gate end) = 0.409 (T-404 at most 0.530) |
| L-020e561643e5903e5c21 | EXT.FENCE.FACE | m2 | FENCE:F-SEA:FACE:OUTSIDE | BLANK | 6.36 | ESTIMATE | sea solid 2.40 (T-396 runs, gate G-02 and pool back excluded) x 2.65 drawn in both elevations (not printed for this run; Q-63 C element, designer RFI-B-A11 replaces it) = 6.360 |
| L-e22ea03658c74421b9d9 | EXT.FENCE.FACE | m2 | FENCE:F-LOWER:FACE:OUTSIDE | BLANK | 3.18 | ESTIMATE | passage closure 1.20 (T-396) x 2.65 fence height (no height printed for the closure; same fence) = 3.180 |
| L-1874145bb43c31a0cd03 | EXT.FENCE.FACE | m2 | FENCE:F-SEA:FACE:PLOT | BLANK | 6.36 | ESTIMATE | sea solid 2.40 (T-396 runs, gate G-02 and pool back excluded) x 2.65 drawn in both elevations (not printed for this run; Q-63 C element, designer RFI-B-A11 replaces it) = 6.360 |
| L-71cfc2e9c70fbab1b3f1 | EXT.FENCE.FACE | m2 | FENCE:F-LOWER:FACE:PLOT | BLANK | 3.18 | ESTIMATE | passage closure 1.20 (T-396) x 2.65 fence height (no height printed for the closure; same fence) = 3.180 |
| L-aad105421b72b47c6f5c | EXT.FENCE.WALL | m2 | FENCE:F-SEA:WALL_PLANE | BLANK | 6.36 | ESTIMATE | 2.40 x 2.65 (as the sea faces) = 6.360 |
| L-cb47254352092a9d9662 | EXT.FENCE.WALL | m2 | FENCE:F-LOWER:WALL_PLANE | BLANK | 3.18 | ESTIMATE | 1.20 x 2.65 (as the closure faces) = 3.180 |
| L-479236085c3a79878c90 | EXT.FENCE.BLOCK | m2 | FENCE:F-NORTH:BLOCK_NET | BLANK | 81.5405 | ESTIMATE | plane 31.37 x 2.65 = 83.1305 - 2 columns x 0.30 x 2.65 (T-761 count: one per run end) = 81.540; block to the full 2.65 (lower 0.50 band material not printed) |
| L-4eb92fd041dee3234b34 | EXT.FENCE.BLOCK | m2 | FENCE:F-STREET:BLOCK_NET | BLANK | 9.131 | ESTIMATE | plane 14.840 (released) - scaled dip 4.119 - 2 columns 1.590 = 9.131 |
| L-9b4ba80e8886e850cc67 | EXT.FENCE.BLOCK | m2 | FENCE:F-SEA:BLOCK_NET | BLANK | 3.18 | ESTIMATE | plane 6.360 - 4 columns (two sea runs, G-02 jambs) 3.180 = 3.180 |
| L-22c53d141c69511bb328 | EXT.FENCE.BLOCK | m2 | FENCE:F-LOWER:BLOCK_NET | BLANK | 1.59 | ESTIMATE | plane 3.180 - 2 columns 1.590 = 1.590 |
| L-c632bb4647031c37de19 | EXT.FENCE.MASONRY_BELOW_NG | m2 | FENCE:BAND:MASONRY_BELOW_NG | BLANK | 23.4099 | ESTIMATE | band 44.07 x h 0.57 (formation 1.67 S01 as T-764 - blinding 0.10 - lower G.B 0.60 Q-28 A - upper G.B 0.40) = 25.120 - 10 columns x 0.30 x 0.57 = 23.410 (T-403 at least 17.628 at 1.50) |
| L-59991e8fddedbe977fbb | EXT.FENCE.BLOCK_COUNT | pcs | FENCE:ALL:BLOCKS | BLANK | 1486.0 | ESTIMATE | fence block net above N.G. 95.441 + below N.G. 23.410 = 118.851 m2 x 12.5 per m2 (owner Q-75 / Q-80), waste separate; type HELD (Q-65 C) |
| L-b1c2e0b93312e521d699 | EXT.FENCE.PLASTER | m2 | FENCE:F-NORTH:FACE:OUTSIDE:PLASTER | BLANK | 67.4455 | DRAWING-READ | exposed face 31.37 x 2.15 (p.12 SECTION '215' above the outside ground band '50') = 67.445; system as the house exterior (render 1:4 + paint, Q-79; fence finish not printed, owner item open under Q-65 C) |
| L-1e9a80dbea82741116cf | EXT.FENCE.PAINT | m2 | FENCE:F-NORTH:FACE:OUTSIDE:PAINT | BLANK | 67.4455 | DRAWING-READ | = the plaster face 67.445 (owner 2026-11-12: paint = plaster face) |
| L-36726588eba347a4c783 | EXT.FENCE.PLASTER | m2 | FENCE:F-NORTH:FACE:PLOT:PLASTER | BLANK | 77.425 | DRAWING-READ | exposed face 30.97 x 2.50 (2.65 - court +0.15; T-404 finishable lower bound) = 77.425; system as the house exterior (render 1:4 + paint, Q-79; fence finish not printed, owner item open under Q-65 C) |
| L-bac8095037312e3e90f4 | EXT.FENCE.PAINT | m2 | FENCE:F-NORTH:FACE:PLOT:PAINT | BLANK | 77.425 | DRAWING-READ | = the plaster face 77.425 (owner 2026-11-12: paint = plaster face) |
| L-eb19e5f5365e81dcedeb | EXT.FENCE.PLASTER | m2 | FENCE:F-STREET:FACE:OUTSIDE:PLASTER | BLANK | 8.351 | ESTIMATE | exposed face face 11.251 - 5.80 x 0.50 outside ground band (SECTION '50'; elevation draws about 2.0 exposed) = 8.351; system as the house exterior (render 1:4 + paint, Q-79; fence finish not printed, owner item open under Q-65 C) |
| L-8502adc8f55776e67a28 | EXT.FENCE.PAINT | m2 | FENCE:F-STREET:FACE:OUTSIDE:PAINT | BLANK | 8.351 | ESTIMATE | = the plaster face 8.351 (owner 2026-11-12: paint = plaster face) |
| L-e46d3f1324eb8625cbdc | EXT.FENCE.PLASTER | m2 | FENCE:F-STREET:FACE:PLOT:PLASTER | BLANK | 9.881 | ESTIMATE | exposed face face 10.721 - 5.60 x 0.15 court = 9.881; system as the house exterior (render 1:4 + paint, Q-79; fence finish not printed, owner item open under Q-65 C) |
| L-4465d1e72082b5678e4a | EXT.FENCE.PAINT | m2 | FENCE:F-STREET:FACE:PLOT:PAINT | BLANK | 9.881 | ESTIMATE | = the plaster face 9.881 (owner 2026-11-12: paint = plaster face) |
| L-639e70724813476c31d3 | EXT.FENCE.PLASTER | m2 | FENCE:F-SEA:FACE:OUTSIDE:PLASTER | BLANK | 5.16 | ESTIMATE | exposed face 2.40 x 2.15 (section as the other runs) = 5.160; system as the house exterior (render 1:4 + paint, Q-79; fence finish not printed, owner item open under Q-65 C) |
| L-0a2fbaa46f6a6b23323e | EXT.FENCE.PAINT | m2 | FENCE:F-SEA:FACE:OUTSIDE:PAINT | BLANK | 5.16 | ESTIMATE | = the plaster face 5.160 (owner 2026-11-12: paint = plaster face) |
| L-b7cf09f5c8966460da56 | EXT.FENCE.PLASTER | m2 | FENCE:F-SEA:FACE:PLOT:PLASTER | BLANK | 6.0 | ESTIMATE | exposed face 2.40 x 2.50 (court +0.15) = 6.000; system as the house exterior (render 1:4 + paint, Q-79; fence finish not printed, owner item open under Q-65 C) |
| L-2246f2ea8b345ac80584 | EXT.FENCE.PAINT | m2 | FENCE:F-SEA:FACE:PLOT:PAINT | BLANK | 6.0 | ESTIMATE | = the plaster face 6.000 (owner 2026-11-12: paint = plaster face) |
| L-52d8589716c7724358ca | EXT.FENCE.PLASTER | m2 | FENCE:F-LOWER:FACE:OUTSIDE:PLASTER | BLANK | 2.58 | ESTIMATE | exposed face 1.20 x 2.15 (section as the other runs) = 2.580; system as the house exterior (render 1:4 + paint, Q-79; fence finish not printed, owner item open under Q-65 C) |
| L-1c6a9f23a2f8320764a0 | EXT.FENCE.PAINT | m2 | FENCE:F-LOWER:FACE:OUTSIDE:PAINT | BLANK | 2.58 | ESTIMATE | = the plaster face 2.580 (owner 2026-11-12: paint = plaster face) |
| L-e802015729d4df311c0c | EXT.FENCE.PLASTER | m2 | FENCE:F-LOWER:FACE:PLOT:PLASTER | BLANK | 3.0 | ESTIMATE | exposed face 1.20 x 2.50 (court +0.15) = 3.000; system as the house exterior (render 1:4 + paint, Q-79; fence finish not printed, owner item open under Q-65 C) |
| L-8c90675aafd8738b1e26 | EXT.FENCE.PAINT | m2 | FENCE:F-LOWER:FACE:PLOT:PAINT | BLANK | 3.0 | ESTIMATE | = the plaster face 3.000 (owner 2026-11-12: paint = plaster face) |
| L-07ab81e68a2ad5d4b15c | EXT.FENCE.TOP | lm | FENCE:F-STREET:TOP | BLANK | 6.727 | ESTIMATE | plan 5.60 (corner square in the north top) + 1.127 developed along the scaled dip / rounded end = 6.727 |
| L-124e0c1ce0b8015699c9 | EXT.FENCE.GATE | pcs | FENCE:G-01:LEAF | BLANK | 1.0 | ESTIMATE | one gate set in the printed 2.50 opening (leaf not drawn: type / leaves by the designer, T-361) |
| L-b353801f6c9677de4f5d | EXT.FENCE.GATE | pcs | FENCE:G-02:LEAF | BLANK | 1.0 | DRAWING-READ | 1 leaf drawn (D120 single swing; elevation leaf 0.90 x 2.10), T-361 |
| L-0b3dce44cf70ae95ccd6 | EXT.POOL.WATER_FACE | m2 | GF-POOL-WATER#FINISH | BLANK | 21.3087 | DRAWING-READ | pool floor 8.5788 + inner perimeter 11.0695 x 1.15 (DXF dim 2E5E finished floor -0.85 to rim +0.30) = 21.309 (T-343) |
| L-1c51d1e7a3b65243382a | EXT.FLOOR.OUTDOOR | m2 | GF-COURT#POOL-DECK | HELD 6.548912 .. 6.548912 | 6.5489 | MEASURED | range low = high: the drawn polygon (T-157 / T-343) |
| L-dd6e372825ce06d45bdd | EXT.FLOOR.OUTDOOR | m2 | GF-COURT#PORCH | HELD 10.6785 .. 10.6785 | 10.6785 | MEASURED | range low = high: the drawn polygon (T-157 / T-343) |

## New lines (missing families; Worker 3 assigns line ids)

| family | item | unit | figure | label | basis |
|---|---|---|---|---|---|
| B1-01 | SITE.CLEARANCE | m2 | 470.55 | DRAWING-READ | plot 15.00 x 31.37 printed (ARCH p.1 / p.2) = 470.550; owner 2026-11-02 17:20 (6) scope = the plot (T-491) |
| B1-05 | SITE.ANTI_TERMITE | m2 | 319.99 | DEFAULT | building footprint = printed GF area 319.99 m2 (ARCH p.1, 68.00 % of 470.55); no sheet prints a soil treatment (T-471): Lead row default, the designer can strike it |
| B1-06 | SITE.DEWATERING | item | None | NOT_APPLICABLE | groundwater -4.50 printed (ST p.9 note 4) vs deepest formation -1.67: 2.83 m clear; conditional only (note 14, T-358 B1-06a). Excavation support B1-06b is TRIGGERED (T-358): left to T-771 |
| B1-07 | SITE.PRELIMINARIES | item | 1 | DEFAULT | one lump-sum item (owner 17:20 (6): site handover item; hoarding gross 92.74 lm = 2 x (15.00 + 31.37) beside, T-491); durations / counts by the contractor's programme |
