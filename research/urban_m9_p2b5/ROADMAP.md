# Development roadmap, ranked by expected accuracy improvement (Phase 2B-5)

The ranking uses measured exposure: the five real rooms of Stage C (66 independent checks), the whole-plan
aggregates and the synthetic benchmark. Every item is an opt-in method step behind its own flag; frozen methods
stay as they are.

| rank | work | why (measured) | BOQ families | proof needed |
|---|---|---|---|---|
| 1 | **doorway-strip attribution** at splayed walls and merged strips (D-C2) | the largest measured real error: marble thresholds −49 % of the sample's threshold area withheld; doorway waterproofing −12 %; 3 of 5 wet doorways | FIN.MARBLE.THRESHOLD, FIN.WP.DOORWAY | the five Stage C rooms re-scored; synthetic splayed-wall doorways with hand truth |
| 2 | **arc-aware room polygons and curved wall bands** (D-D2) | synthetic arc room: wall run −23 %, layout on the chord (1.02 m2 of 13.02 unplanned); reference plan: 4 of 38 rooms, ~0.7 % of the wall run | layouts (membrane, tiles), ARCH.WALL_RUN, masonry, plaster by run | B10 truth (`test_p2b5_curved_wall.py` turns from "as found" to the truth); concentric-arc wall bands on synthetic plans |
| 3 | **two-way door widths** (after D-V26-06): reconcile jamb-to-jamb vs leaf closure with DIMENSION / schedule evidence | the residual R-C differences (plaster −0.15 m2, wall porcelain −0.15 m2, skirting, upturn, doorway waterproofing) | door-related wall deductions | Stage C R-C to zero difference with a stated source |
| 4 | **layer-role pre-flight** (D-D1): flag or refuse single-instance role inference; ask for `--layer-roles` | every door / window on a single-room sheet typed PASSAGE; a column not deducted (+2.18 % floor) | doors, thresholds, doorway waterproofing, floor / ceiling | benchmark single-door cases flip to exact without declared roles, or refuse |
| 5 | **heights from sections / schedules** (D-C5) | every wall-area line rests on heights; the test heights are synthetic | plaster, wall porcelain, paint, masonry | a section reader verified on synthetic sections; the owner's project heights |
| 6 | **attachment note for doorless cells merged into a wet room** (D-C3) | 44 % of one sample room takes the wet scope silently | wet scope (waterproofing, porcelain) | the cell flagged; owner decision 3 |
| 7 | waterproofing junction detail released (owner decision 1) | procurement now PROVISIONAL; one roll more at a 0.16 m flange | procurement rolls | Phase 2B-4 / 2B-5 examples re-run with the chosen detail |
| 8 | vector-PDF cross-check for PDF-only sets (after the licence decision) | exact on the benchmark; independent of CAD | none directly (a check) | a DXF / PDF pair of a real plan, privately |
| 9 | raster review aids: text-to-wall separation, rotation-aware gap closing | scan B09 spur (+23 % perimeter), B06 spurious gaps | none (review only) | benchmark |
| 10 | the formal blind evaluation (not started, as instructed) | the only basis for any accuracy claim | all | the owner's protocol |
