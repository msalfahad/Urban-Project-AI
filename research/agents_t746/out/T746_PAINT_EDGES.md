# T-746 paint at opening edges as lm on ARCH_TAKEOFF_V3.0.74 (generated; research, unwired)

Rules R-T746-1, R-T746-2, R-T746-3; UP-FIN-PAINT-002 1.0.0 param 'edges' (LM_ITEMS_NOT_AREA); Lead ruling T-746 reading B. A return is an lm item (2 x h + w per opening side), its paint m2 moves to the lm line; plaster m2 untouched.

## Totals

- 30 return-paint lines: edge lm 0.000000 .. 33.800000, HELD 3; by status {'BOUNDED': 27, 'HELD': 3}; frames drawn over the full wall depth 25; by part {'HEAD': {'lm': ['0.000000', '25.000000'], 'gross': '25.000000'}, 'JAMBS': {'lm': ['0.000000', '8.800000'], 'gross': '119.400000'}}
- paint m2 leaving the m2 lines: rule (reading A, T-740) ['20.250000', '24.150000'], engine V3.0.74 ['0.000000', '24.150000']
- windows (58 sides): {'IN HELD': 2, 'IN NO_PAINT_EDGE': 27, 'OUT HELD': 3, 'OUT PAINT_LM': 26}; outside edge lm 106.020000 .. 106.020000, HELD 3
- paint m2: rule A ['841.260635', '929.204847'] -> rule B ['821.010635', '905.054847']; engine ['822.198159', '927.214521'] -> returns out ['822.198159', '903.064521']; floor re-add residual ['0.000000', '0.000000']

## By floor (m2 unless lm)

| floor | return lines | door edge lm | window outside lm | rule paint A | rule paint B | engine paint | engine returns out |
|---|---|---|---|---|---|---|---|
| GF | 16 | 0.000000 .. 22.400000 (HELD 2) | 39.700000 .. 39.700000 | 336.267835 .. 405.123147 | 326.057835 .. 391.793147 | 326.223659 .. 407.437921 | 326.223659 .. 394.107921 |
| 1F | 11 | 0.000000 .. 8.700000 (HELD 1) | 51.320000 .. 51.320000 | 376.685650 .. 390.834550 | 369.295650 .. 382.664550 | 370.157300 .. 386.529400 | 370.157300 .. 378.359400 |
| 2F | 3 | 0.000000 .. 2.700000 (HELD 0) | 15.000000 .. 15.000000 | 128.307150 .. 133.247150 | 125.657150 .. 130.597150 | 125.817200 .. 133.247200 | 125.817200 .. 130.597200 |

## Return-paint lines restated (by line id)

| opening | floor | rooms | paint line | depth | w | h | plaster m2 | paint m2 engine | paint m2 A | paint m2 B | edge lm B | status | cause | frame |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D-1F-01 | 1F | 1F-01;1F-02 | L-2b4e45da29a5b2dd7981 | 0.15 | 0.8 | 2.2 | 0.780000 .. 0.780000 | 0.000000 .. 0.780000 | 0.780000 .. 0.780000 | 0.000000 .. 0.000000 | 0.000000 .. 0.800000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D315 handle C2B: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-1F-08 | 1F | 1F-10;1F-13 | L-37cdb8db76a870eff3fe | 0.15 | 0.9 | 2.2 | 0.795000 .. 0.795000 | 0.000000 .. 0.795000 | 0.795000 .. 0.795000 | 0.000000 .. 0.000000 | 0.000000 .. 0.900000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D215 handle C18: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-1F-09 | 1F | 1F-11;1F-13 | L-56b08dbf65e47a26c561 | 0.15 | 0.9 | 2.2 | 0.795000 .. 0.795000 | 0.000000 .. 0.795000 | 0.795000 .. 0.795000 | 0.000000 .. 0.000000 | 0.000000 .. 0.900000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D215 handle BEF: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-1F-05 | 1F | 1F-07;1F-13 | L-da69c4bd2954b31c0fb7 | 0.2 | 0.9 | 2.2 | 1.060000 .. 1.060000 | 0.000000 .. 1.060000 | 1.060000 .. 1.060000 | 0.000000 .. 0.000000 | 0.000000 .. 0.900000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block d220 handle C1A: frame posts 0.050 m over the full wall depth 0.200 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-1F-06 | 1F | 1F-07;1F-08 | L-d7409e4cefc3ee62aaf6 | 0.15 | 0.8 | 2.2 | 0.780000 .. 0.780000 | 0.000000 .. 0.780000 | 0.000000 .. 0.780000 | 0.000000 .. 0.000000 | 0.000000 .. 0.800000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD WET_BOTH_SIDES_TILE_NOT_ESTABLISHED | plan block D315 handle 11B4: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-1F-10 | 1F | 1F-11;1F-12 | L-762c50f64c3b6b6b9999 | 0.15 | 0.8 | 2.2 | 0.780000 .. 0.780000 | 0.000000 .. 0.780000 | 0.780000 .. 0.780000 | 0.000000 .. 0.000000 | 0.000000 .. 0.800000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D315 handle C12: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-1F-07 | 1F | 1F-09 | L-f430f55002cce63efb40 | 0.15 | 0.8 | 2.2 | 0.780000 .. 0.780000 | 0.000000 .. 0.780000 | 0.780000 .. 0.780000 | 0.000000 .. 0.000000 | 0.000000 .. 0.800000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D315 handle BEE: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-1F-02 | 1F | 1F-01;1F-13;ST-1F | L-c74cb759ac5ff7e6cfa0 | 0.15 | 1.0 | 2.2 | 0.810000 .. 0.810000 | 0.000000 .. 0.810000 | 0.810000 .. 0.810000 | 0.000000 .. 0.000000 | 0.000000 .. 1.000000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D115 handle C31: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| A-1F-01 | 1F | 1F-10 | L-6d2b3f8c5c33dd795433 | 0.15 | blank | blank | blank | blank | blank | blank | blank | HELD | SIZE_NOT_ESTABLISHED | handle -: no census symbol |
| D-1F-03 | 1F | 1F-04;1F-13 | L-d086b605ac0e50af082a | 0.15 | 1.0 | 2.2 | 0.810000 .. 0.810000 | 0.000000 .. 0.810000 | 0.810000 .. 0.810000 | 0.000000 .. 0.000000 | 0.000000 .. 1.000000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D115 handle C32: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-1F-04 | 1F | 1F-04;1F-03 | L-c17b547dd9cdad8faf26 | 0.15 | 0.8 | 2.2 | 0.780000 .. 0.780000 | 0.000000 .. 0.780000 | 0.780000 .. 0.780000 | 0.000000 .. 0.000000 | 0.000000 .. 0.800000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D315 handle C2E: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-2F-01 | 2F | 2F-01 | L-d9d0cb88542f719484f7 | 0.15 | 1.0 | 2.2 | 0.810000 .. 0.810000 | 0.000000 .. 0.810000 | 0.810000 .. 0.810000 | 0.000000 .. 0.000000 | 0.000000 .. 1.000000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D115 handle 12BA: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-2F-03 | 2F | 2F-03;2F-02 | L-b12d7eb43e52a3d98ab4 | 0.15 | 0.8 | 2.2 | 0.780000 .. 0.780000 | 0.000000 .. 0.780000 | 0.780000 .. 0.780000 | 0.000000 .. 0.000000 | 0.000000 .. 0.800000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D315 handle 12BB: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-2F-02 | 2F | 2F-03;2F-01 | L-4e7e711e5c8abc074414 | 0.2 | 0.9 | 2.2 | 1.060000 .. 1.060000 | 0.000000 .. 1.060000 | 1.060000 .. 1.060000 | 0.000000 .. 0.000000 | 0.000000 .. 0.900000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block d220 handle 12C2: frame posts 0.050 m over the full wall depth 0.200 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-GF-03 | GF | GF-04 | L-897dca14b0b8c45be725 | 0.2 | 0.9 | 2.2 | 1.060000 .. 1.060000 | 0.000000 .. 1.060000 | 1.060000 .. 1.060000 | 0.000000 .. 0.000000 | 0.000000 .. 0.900000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block d220 handle 1B5: frame posts 0.050 m over the full wall depth 0.200 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-GF-06 | GF | GF-07 | L-7969458ba9185391c684 | 0.2 | 1.0 | 2.2 | 1.080000 .. 1.080000 | 0.000000 .. 1.080000 | 1.080000 .. 1.080000 | 0.000000 .. 0.000000 | 0.000000 .. 1.000000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D120 handle 33E: frame posts 0.050 m over the full wall depth 0.200 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-GF-01 | GF | GF-01 | L-6777e02aa04439148278 | 0.2 | 1.0 | 2.2 | 1.080000 .. 1.080000 | 0.000000 .. 1.080000 | 1.080000 .. 1.080000 | 0.000000 .. 0.000000 | 0.000000 .. 1.000000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D120 handle 15E: frame posts 0.050 m over the full wall depth 0.200 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-GF-08 | GF | GF-08;ST-GF | L-ba30cda374ebb4a8c7da | 0.2 | 1.0 | 2.2 | 1.080000 .. 1.080000 | 0.000000 .. 1.080000 | 1.080000 .. 1.080000 | 0.000000 .. 0.000000 | 0.000000 .. 1.000000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D120 handle 2C7: frame posts 0.050 m over the full wall depth 0.200 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-GF-13 | GF | GF-08;GF-15 | L-65c1d5f9695ad983d89f | 0.15 | 1.0 | 2.2 | 0.810000 .. 0.810000 | 0.000000 .. 0.810000 | 0.810000 .. 0.810000 | 0.000000 .. 0.000000 | 0.000000 .. 1.000000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D115 handle 2F2: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-GF-09 | GF | ST-GF | L-91dfc7c4d8ea4c86a547 | 0.2 | 0.9 | 2.2 | 1.060000 .. 1.060000 | 0.000000 .. 1.060000 | 1.060000 .. 1.060000 | 0.000000 .. 0.000000 | 0.000000 .. 5.300000 | BOUNDED | JAMBS FRAME_COVERAGE_NOT_PRINTED; HEAD FRAME_COVERAGE_NOT_PRINTED | handle 3FF: POSITION CONFLICT: the block's frame posts are not at the drawn masonry jambs (block width vs wall gap) (block 1.000 m vs masonry 0.900 m) |
| D-GF-11 | GF | GF-12;GF-14 | L-9df1fbe948884e7c4d2a | 0.15 | 0.8 | 2.2 | 0.780000 .. 0.780000 | 0.000000 .. 0.780000 | 0.000000 .. 0.780000 | 0.000000 .. 0.000000 | 0.000000 .. 0.800000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD WET_BOTH_SIDES_TILE_NOT_ESTABLISHED | plan block D315 handle 321: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-GF-12 | GF | GF-13;GF-14 | L-0ea62c4cef8e2ce5a244 | 0.15 | 0.8 | 2.2 | 0.780000 .. 0.780000 | 0.000000 .. 0.780000 | 0.000000 .. 0.780000 | 0.000000 .. 0.000000 | 0.000000 .. 0.800000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD WET_BOTH_SIDES_TILE_NOT_ESTABLISHED | plan block D315 handle 320: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-GF-07 | GF | GF-08 | L-7f8d0739849d36a7e832 | 0.2 | 2.0 | 2.5 | 1.400000 .. 1.400000 | 0.000000 .. 1.400000 | 1.400000 .. 1.400000 | 0.000000 .. 0.000000 | 0.000000 .. 2.000000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D200 handle 281: frame posts 0.050 m over the full wall depth 0.200 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-GF-05 | GF | GF-06 | L-78d0a48c8bf5af4b21c4 | 0.2 | 1.0 | 2.2 | 1.080000 .. 1.080000 | 0.000000 .. 1.080000 | 1.080000 .. 1.080000 | 0.000000 .. 0.000000 | 0.000000 .. 1.000000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D120 handle 192: frame posts 0.050 m over the full wall depth 0.200 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-GF-04 | GF | GF-04;GF-05 | L-26efbd99ac40f2435692 | 0.15 | 0.8 | 2.2 | 0.780000 .. 0.780000 | 0.000000 .. 0.780000 | 0.780000 .. 0.780000 | 0.000000 .. 0.000000 | 0.000000 .. 0.800000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD FRAME_COVERAGE_NOT_PRINTED | plan block D315 handle 19E: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| A-GF-01 | GF | GF-01;GF-02 | L-eab5536cbc5b1f7829dd | 0.15 | blank | blank | blank | blank | blank | blank | blank | HELD | SIZE_NOT_ESTABLISHED | handle -: no census symbol |
| D-GF-02 | GF | GF-02;GF-03 | L-8dd621261ceb5b8e3919 | 0.15 | 0.8 | 2.2 | 0.780000 .. 0.780000 | 0.000000 .. 0.780000 | 0.000000 .. 0.780000 | 0.000000 .. 0.000000 | 0.000000 .. 0.800000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD WET_BOTH_SIDES_TILE_NOT_ESTABLISHED | plan block D315 handle 1EF: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 0.0 0.0 0.0 0.0 mm) |
| D-GF-10 | GF | GF-10;GF-11 | L-dc8b92788150cda368a1 | 0.15 | 0.8 | 2.2 | 0.780000 .. 0.780000 | 0.000000 .. 0.780000 | 0.000000 .. 0.780000 | 0.000000 .. 0.000000 | 0.000000 .. 0.800000 | BOUNDED | JAMBS FRAME_COVERS_RETURN_DRAWN; HEAD WET_BOTH_SIDES_TILE_NOT_ESTABLISHED | plan block D315 handle 339: frame posts 0.050 m over the full wall depth 0.150 m at the drawn masonry jambs (offsets 3.0 3.0 0.0 0.0 mm) |
| D-GF-14 | GF | GF-15;GF-16 | L-f3270cd391188bcf433c | 0.15 | 0.8 | 2.2 | 0.780000 .. 0.780000 | 0.000000 .. 0.780000 | 0.780000 .. 0.780000 | 0.000000 .. 0.000000 | 0.000000 .. 5.200000 | BOUNDED | JAMBS FRAME_COVERAGE_NOT_PRINTED; HEAD FRAME_COVERAGE_NOT_PRINTED | handle 334: not a door block: no frame drawn |
| D-GF-15 | GF |  | L-2d7f8ab2fb489d7f0963 | blank | blank | blank | blank | blank | blank | blank | blank | HELD | SIZE_NOT_ESTABLISHED | handle 2D8: masonry jamb not found on both faces |

## Windows (room side and outside)

| opening | side | room | depth | w | h | edge lm | status | cause | sill / threshold |
|---|---|---|---|---|---|---|---|---|---|
| W01 | IN | ST-GF | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W01 | OUT | ST-GF | 0.1 | 1.2 | 2.0 | 5.200000 .. 5.200000 | PAINT_LM | - | SILL 1.2 m.l: own item (bound to ARCH.WINDOW_REVEAL L-0de10f4db591a2467b82), finish not printed as paint: not a paint edge |
| W02 | IN | GF-08 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W02 | OUT | GF-08 | 0.08 | blank | blank | blank | HELD | SIZE_NOT_ESTABLISHED | SILL 6.33 m.l: own item (bound to ARCH.WINDOW_REVEAL L-a430e89b6d52e1c994e0), finish not printed as paint: not a paint edge |
| W03 | IN | GF-08 | blank | blank | blank | blank | HELD | SIZE_NOT_ESTABLISHED | - |
| W03 | OUT | GF-08 | blank | blank | blank | blank | HELD | SIZE_NOT_ESTABLISHED | THRESHOLD 0 m.l: own item (bound to ARCH.WINDOW_REVEAL NO_LINE), finish not printed as paint: not a paint edge |
| W04 | IN | GF-04 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W04 | OUT | GF-04 | 0.08 | 0.6 | 0.8 | 2.200000 .. 2.200000 | PAINT_LM | - | SILL 0.6 m.l: own item (bound to ARCH.WINDOW_REVEAL L-6add1d9c5ce0493a3e60), finish not printed as paint: not a paint edge |
| W05 | IN | GF-10 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W05 | OUT | GF-10 | 0.08 | 0.6 | 0.8 | 2.200000 .. 2.200000 | PAINT_LM | - | SILL 0.6 m.l: own item (bound to ARCH.WINDOW_REVEAL L-bd633784436adfde4033), finish not printed as paint: not a paint edge |
| W06 | IN | GF-13 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W06 | OUT | GF-13 | 0.08 | 0.6 | 0.8 | 2.200000 .. 2.200000 | PAINT_LM | - | SILL 0.6 m.l: own item (bound to ARCH.WINDOW_REVEAL L-eef0162ee1ce392fc7d5), finish not printed as paint: not a paint edge |
| W07 | IN | GF-16 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W07 | OUT | GF-16 | 0.08 | 0.6 | 0.8 | 2.200000 .. 2.200000 | PAINT_LM | - | SILL 0.6 m.l: own item (bound to ARCH.WINDOW_REVEAL L-dec26399645ab26c13f9), finish not printed as paint: not a paint edge |
| W08 | IN | GF-06 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W08 | OUT | GF-06 | 0.08 | 1.5 | 1.5 | 4.500000 .. 4.500000 | PAINT_LM | - | SILL 1.5 m.l: own item (bound to ARCH.WINDOW_REVEAL L-b6691e6f54bf47eb4f89), finish not printed as paint: not a paint edge |
| W09 | IN | GF-07 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W09 | OUT | GF-07 | 0.08 | 1.5 | 1.5 | 4.500000 .. 4.500000 | PAINT_LM | - | SILL 1.5 m.l: own item (bound to ARCH.WINDOW_REVEAL L-1bedabba8af5d2529e77), finish not printed as paint: not a paint edge |
| W10 | IN | GF-07 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W10 | OUT | GF-07 | 0.08 | 1.0 | 1.5 | 4.000000 .. 4.000000 | PAINT_LM | - | SILL 1.0 m.l: own item (bound to ARCH.WINDOW_REVEAL L-bea7d46e51c809fbe623), finish not printed as paint: not a paint edge |
| W11 | IN | GF-01 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W11 | OUT | GF-01 | 0.1 | 1.95 | 2.2 | 6.350000 .. 6.350000 | PAINT_LM | - | SILL 1.95 m.l: own item (bound to ARCH.WINDOW_REVEAL L-10af4bb68e88181775a7), finish not printed as paint: not a paint edge |
| W12 | IN | GF-01 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W12 | OUT | GF-01 | 0.1 | 1.95 | 2.2 | 6.350000 .. 6.350000 | PAINT_LM | - | SILL 1.95 m.l: own item (bound to ARCH.WINDOW_REVEAL L-36e2b88d45f02c84a404), finish not printed as paint: not a paint edge |
| W13 | IN | ST-1F | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W13 | OUT | ST-1F | 0.1 | 1.2 | 2.3 | 5.800000 .. 5.800000 | PAINT_LM | - | SILL 1.2 m.l: own item (bound to ARCH.WINDOW_REVEAL L-ec91f75c35edf30f9c65), finish not printed as paint: not a paint edge |
| W14 | IN | 1F-01 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W14 | OUT | 1F-01 | 0.1 | 2.45 | 1.6 | 5.650000 .. 5.650000 | PAINT_LM | - | SILL 2.45 m.l: own item (bound to ARCH.WINDOW_REVEAL L-ea48300c45f8efa96ffe), finish not printed as paint: not a paint edge |
| W15 | IN | 1F-13 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W15 | OUT | 1F-13 | 0.08 | 1.55 | 3.1 | 7.750000 .. 7.750000 | PAINT_LM | - | THRESHOLD 0.0 m.l: own item (bound to ARCH.WINDOW_REVEAL L-0e2e7299371efb8338cc), finish not printed as paint: not a paint edge |
| W16 | IN | 1F-13 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W16 | OUT | 1F-13 | 0.08 | 1.55 | 3.1 | 7.750000 .. 7.750000 | PAINT_LM | - | THRESHOLD 0.0 m.l: own item (bound to ARCH.WINDOW_REVEAL L-146170b53ca02c2456f9), finish not printed as paint: not a paint edge |
| W17 | IN | 1F-11 | blank | blank | blank | blank | HELD | SIZE_NOT_ESTABLISHED | - |
| W17 | OUT | 1F-11 | blank | blank | blank | blank | HELD | SIZE_NOT_ESTABLISHED | SILL 0 m.l: own item (bound to ARCH.WINDOW_REVEAL L-c90d5d6c06a671fc3b99), finish not printed as paint: not a paint edge |
| W18 | IN | 1F-12 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W18 | OUT | 1F-12 | 0.08 | 0.5 | 2.16 | 4.820000 .. 4.820000 | PAINT_LM | - | SILL 0.5 m.l: own item (bound to ARCH.WINDOW_REVEAL NO_LINE), finish not printed as paint: not a paint edge |
| W19 | IN | 1F-02 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W19 | OUT | 1F-02 | 0.08 | 0.6 | 0.8 | 2.200000 .. 2.200000 | PAINT_LM | - | SILL 0.6 m.l: own item (bound to ARCH.WINDOW_REVEAL L-e709025cfb48633cc369), finish not printed as paint: not a paint edge |
| W20 | IN | 1F-03 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W20 | OUT | 1F-03 | 0.08 | 0.6 | 0.8 | 2.200000 .. 2.200000 | PAINT_LM | - | SILL 0.6 m.l: own item (bound to ARCH.WINDOW_REVEAL L-e60b1ffc24c8bc76ec1a), finish not printed as paint: not a paint edge |
| W21 | IN | 1F-07 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W21 | OUT | 1F-07 | 0.08 | 0.6 | 0.8 | 2.200000 .. 2.200000 | PAINT_LM | - | SILL 0.6 m.l: own item (bound to ARCH.WINDOW_REVEAL L-cdd13c017d2f5328032e), finish not printed as paint: not a paint edge |
| W22 | IN | 1F-08 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W22 | OUT | 1F-08 | 0.08 | 0.6 | 0.8 | 2.200000 .. 2.200000 | PAINT_LM | - | SILL 0.6 m.l: own item (bound to ARCH.WINDOW_REVEAL L-dbec1a970ca591bebd43), finish not printed as paint: not a paint edge |
| W23 | IN | 1F-09 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W23 | OUT | 1F-09 | 0.08 | 0.6 | 0.8 | 2.200000 .. 2.200000 | PAINT_LM | - | SILL 0.6 m.l: own item (bound to ARCH.WINDOW_REVEAL L-1b5962c15890ecb2f6da), finish not printed as paint: not a paint edge |
| W24 | IN | 1F-04 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W24 | OUT | 1F-04 | 0.08 | 1.55 | 1.5 | 4.550000 .. 4.550000 | PAINT_LM | - | SILL 1.55 m.l: own item (bound to ARCH.WINDOW_REVEAL L-560e87c03e18569ae941), finish not printed as paint: not a paint edge |
| W25 | IN | ST-1F | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W25 | OUT | ST-1F | 0.08 | 1.0 | 1.5 | 4.000000 .. 4.000000 | PAINT_LM | - | THRESHOLD 0.0 m.l: own item (bound to ARCH.WINDOW_REVEAL L-63087103666a3c4b177b), finish not printed as paint: not a paint edge |
| W26 | IN | ST-2F | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W26 | OUT | ST-2F | 0.1 | 1.2 | 1.7 | 4.600000 .. 4.600000 | PAINT_LM | - | SILL 1.2 m.l: own item (bound to ARCH.WINDOW_REVEAL L-d91627a1feb6dc854723), finish not printed as paint: not a paint edge |
| W27 | IN | ST-2F | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W27 | OUT | ST-2F | 0.08 | 1.0 | 1.5 | 4.000000 .. 4.000000 | PAINT_LM | - | THRESHOLD 0.0 m.l: own item (bound to ARCH.WINDOW_REVEAL L-d540d2198577747bcf84), finish not printed as paint: not a paint edge |
| W28 | IN | 2F-02 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W28 | OUT | 2F-02 | 0.08 | 0.6 | 0.8 | 2.200000 .. 2.200000 | PAINT_LM | - | SILL 0.6 m.l: own item (bound to ARCH.WINDOW_REVEAL L-44f5f5c49b50d62b44f3), finish not printed as paint: not a paint edge |
| W29 | IN | 2F-03 | blank | blank | blank | 0.000000 .. 0.000000 | NO_PAINT_EDGE | FRAME_FLUSH_NO_RETURN | - |
| W29 | OUT | 2F-03 | 0.08 | 1.2 | 1.5 | 4.200000 .. 4.200000 | PAINT_LM | - | SILL 1.2 m.l: own item (bound to ARCH.WINDOW_REVEAL L-a6565fe2cd9df42f77fd), finish not printed as paint: not a paint edge |
