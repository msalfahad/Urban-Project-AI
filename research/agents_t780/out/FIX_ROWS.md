# T-780 fix rows on ARCH_TAKEOFF_V3.0.82: roof layers on one area per roof surface

Rule: ROOF_LAYER_AREA_V1 (proposed, research/agents_t780/t780_rules.py)

## Summary

```
{
 "rows": 19,
 "restated_t764_lines": [
  "L-aac1f35e08f85b643692",
  "L-90b40877c8c3da54ba1b"
 ],
 "blank_roof_lines_before": 0,
 "blank_roof_lines_after": 0,
 "roof_finish_m2": {
  "before": 248.809135,
  "after": 238.484216,
  "freelancer": 285.0,
  "after_vs_freelancer_pct": -16.3,
  "causes_m2_his_minus_ours": {
   "RULE_DIFFERENCE dome footprints +9.70 (2 openings, B4 rings) : his row gross": 30.718026,
   "RULE_DIFFERENCE DOME-3 footprint +13.90 (S0 shell on the slab) : his row gross": 15.274758,
   "TOLERANCE +9.70 membrane line vs face less exact dome discs (band 0.1575 = arc gain)": 0.0,
   "TOLERANCE annex corner arc discretisation (55.559 vs exact 55.560)": 0.001332,
   "UNRESOLVED residual of his row (T-626, below 1 %)": 0.521668
  }
 },
 "roof_membrane_m2": {
  "before": 256.230216,
  "after": 244.031083,
  "freelancer": 285.0,
  "after_vs_freelancer_pct": -14.4,
  "causes_m2_his_minus_ours": {
   "RULE_DIFFERENCE dome footprints +9.70 (2 openings, B4 rings) : his row gross": 30.718026,
   "RULE_DIFFERENCE DOME-3 footprint +13.90 (S0 shell on the slab) : his row gross": 15.274758,
   "TOLERANCE +9.70 membrane line vs face less exact dome discs (band 0.1575 = arc gain)": 0.0,
   "TOLERANCE annex corner arc discretisation (55.559 vs exact 55.560)": 0.001332,
   "UNRESOLVED residual of his row (T-626, below 1 %)": 0.521668,
   "ENGINE_RIGHT pool-court open-sky slab + ledge +5.50 (membrane, not in his row)": -5.546867
  }
 },
 "roof_upturn_lm": {
  "before": 220.610544,
  "after": 232.965084,
  "freelancer": 194.0,
  "after_vs_freelancer_pct": 20.1,
  "dome_ring_upturns_lm": 41.639936,
  "after_without_dome_rings_lm": 191.325148,
  "note": "his row's length basis is not printed; without the 3 dome-ring upturns ours is within 1.4 % of his 194.00 (consistent with his gross-dome area): proposal, not a split"
 },
 "annex_membrane_line": "the annex +4.30 roof HAS a membrane line: L-d57d2dc2 1F-ROOF-AT220 55.559 m2 (= ROOF-430, T-321 / T-702); the 13 Nov owner table note 'annex has no membrane line' is a label mismatch (AT220 is the 1F-plan name of ROOF-430), not a missing quantity"
}
```

## Beside (not in any line)

- alternative_top_roof_gross_m2: {"value": 49.665, "when": "the designer's roof plan shows the dome membrane running under DOME-3 (no base upturn): +15.275 m2 per layer, -13.855 lm upturn; designer item D-62 (no roof plan)"}
- annex_finish_on_d_band_m2: {"value": 54.9203, "when": "the D band at the annex wall foot is a built plinth on the slab (finish only, -0.639 m2 = 0.27 % of the roof finish trade)"}
- missing_item_dome_extrados: "3 concrete dome shells (S0) have no outer-surface waterproofing / finish line; spherical cap pi (a^2 + h^2): 2 x pi (2.21^2 + 1.90^2) = 53.38 m2 + pi (2.205^2 + 2.15^2) = 29.80 m2, about 83.2 m2 BESIDE only (no company default, no printed spec): Lead to route as a MISSING family / designer item, never folded into the roof membrane"
- pool_court_layers: "the +5.50 pool-court open-sky slab has a membrane line (4.907 + ledge 0.640) but no screed / insulation / protection / finish lines: its floor finish belongs to the pool-court outdoor floor family (T-769), not added here"

## Rows

| line | item | unit | before | after | label | T-764 line | basis |
|---|---|---|---|---|---|---|---|
| L-8a5192a5ee3e40b61b08 | FIN.ROOF.INSULATION | m2 | 54.920 | 55.559 | DRAWING-READ |  | annex +4.30 face to wall face B3A (T-321 handles, exact arc 55.560332; engine arc 55.559 kept); finish hatch D1F + B2A stopped 0.640 m2 short on the D band B3C at the wall foot |
| L-0cb71da74613f446eee9 | FIN.ROOF.PROTECTION | m2 | 54.920 | 55.559 | DRAWING-READ |  | annex +4.30 face to wall face B3A (T-321 handles, exact arc 55.560332; engine arc 55.559 kept); finish hatch D1F + B2A stopped 0.640 m2 short on the D band B3C at the wall foot |
| L-702487d5998861c463c1 | FIN.ROOF.FINISH | m2 | 54.920 | 55.559 | DRAWING-READ |  | annex +4.30 face to wall face B3A (T-321 handles, exact arc 55.560332; engine arc 55.559 kept); finish hatch D1F + B2A stopped 0.640 m2 short on the D band B3C at the wall foot |
| L-bec94500648a90fb2f2a | FIN.ROOF.SCREED | m3 | 4.119 | 4.167 | DRAWING-READ |  | 55.559 m2 x screed 0.075 avg (company default); annex +4.30 face to wall face B3A (T-321 handles, exact arc 55.560332; engine arc 55.559 kept); finish hatch D1F + B2A stopped 0.640 m2 short on the D band B3C at the wall foot |
| L-940b7a65d7e79bc0ec33 | FIN.ROOF.INSULATION | m2 | 31.643 | 32.721 | DRAWING-READ |  | +5.50 strips face (T-321 handles AE3 / B25 / B33 / B5D / BDB / CED); finish hatch AE0 + D1A + 1252 leaves 1.078 m2 of symbol frames / door-swing gaps |
| L-f9e6d4f8c099f6a6cc8e | FIN.ROOF.PROTECTION | m2 | 31.643 | 32.721 | DRAWING-READ |  | +5.50 strips face (T-321 handles AE3 / B25 / B33 / B5D / BDB / CED); finish hatch AE0 + D1A + 1252 leaves 1.078 m2 of symbol frames / door-swing gaps |
| L-a6ce29981d037284ec84 | FIN.ROOF.FINISH | m2 | 31.643 | 32.721 | DRAWING-READ |  | +5.50 strips face (T-321 handles AE3 / B25 / B33 / B5D / BDB / CED); finish hatch AE0 + D1A + 1252 leaves 1.078 m2 of symbol frames / door-swing gaps |
| L-5f018cfc13aaa9ae2210 | FIN.ROOF.SCREED | m3 | 2.373 | 2.454 | DRAWING-READ |  | 32.721 m2 x screed 0.075 avg (company default); +5.50 strips face (T-321 handles AE3 / B25 / B33 / B5D / BDB / CED); finish hatch AE0 + D1A + 1252 leaves 1.078 m2 of symbol frames / door-swing gaps |
| L-122cbab32ca719527de8 | FIN.ROOF.INSULATION | m2 | 115.656 | 115.814 | DRAWING-READ |  | +9.70 face 146.532 less the two dome openings 2 x 15.359 (B4 rings, Q-44 A) + drawn band 0.1575 = membrane line (T-764, merged); finish hatch 2F21 + gaps stopped on the band |
| L-e0dc4455bc0c6ee4fa9b | FIN.ROOF.PROTECTION | m2 | 115.656 | 115.814 | DRAWING-READ |  | +9.70 face 146.532 less the two dome openings 2 x 15.359 (B4 rings, Q-44 A) + drawn band 0.1575 = membrane line (T-764, merged); finish hatch 2F21 + gaps stopped on the band |
| L-e005eb9041acb08d8b87 | FIN.ROOF.FINISH | m2 | 115.656 | 115.814 | DRAWING-READ |  | +9.70 face 146.532 less the two dome openings 2 x 15.359 (B4 rings, Q-44 A) + drawn band 0.1575 = membrane line (T-764, merged); finish hatch 2F21 + gaps stopped on the band |
| L-f4ae7151a6e2b93dd7ad | FIN.ROOF.SCREED | m3 | 8.674 | 8.686 | DRAWING-READ |  | 115.814 m2 x screed 0.075 avg (company default); +9.70 face 146.532 less the two dome openings 2 x 15.359 (B4 rings, Q-44 A) + drawn band 0.1575 = membrane line (T-764, merged); finish hatch 2F21 + gaps stopped on the band |
| L-3e8fe55da71851816dd4 | FIN.WP.ROOF | m2 | 46.589 | 34.390 | ESTIMATE |  | +13.90 top roof inside the parapet = 2F wall inner faces 7.70 x 6.45 = 49.665 m2 (DXF 12B7 / 1292 / 1283 / 1279, beam tops included; was slab panels 7.4543 / 0.16 = 46.589, F-V770-1) less DOME-3 base r 2.205 = 15.275 m2 (S0 concrete dome L-d5401fa8 stands on the slab; layers stop at its base with an upturn, as at the +9.70 domes, Q-24 / Q-29) = 34.390 m2; outline from the 2F walls, no roof plan: Q-34 stays with the owner |
| L-19912fbc18556b65ccf6 | FIN.ROOF.INSULATION | m2 | 46.589 | 34.390 | ESTIMATE |  | +13.90 top roof inside the parapet = 2F wall inner faces 7.70 x 6.45 = 49.665 m2 (DXF 12B7 / 1292 / 1283 / 1279, beam tops included; was slab panels 7.4543 / 0.16 = 46.589, F-V770-1) less DOME-3 base r 2.205 = 15.275 m2 (S0 concrete dome L-d5401fa8 stands on the slab; layers stop at its base with an upturn, as at the +9.70 domes, Q-24 / Q-29) = 34.390 m2; outline from the 2F walls, no roof plan: Q-34 stays with the owner |
| L-c5c48bba5d23fa70e9ad | FIN.ROOF.PROTECTION | m2 | 46.589 | 34.390 | ESTIMATE |  | +13.90 top roof inside the parapet = 2F wall inner faces 7.70 x 6.45 = 49.665 m2 (DXF 12B7 / 1292 / 1283 / 1279, beam tops included; was slab panels 7.4543 / 0.16 = 46.589, F-V770-1) less DOME-3 base r 2.205 = 15.275 m2 (S0 concrete dome L-d5401fa8 stands on the slab; layers stop at its base with an upturn, as at the +9.70 domes, Q-24 / Q-29) = 34.390 m2; outline from the 2F walls, no roof plan: Q-34 stays with the owner |
| L-ab79aa46b9647f63b54a | FIN.ROOF.FINISH | m2 | 46.589 | 34.390 | ESTIMATE |  | +13.90 top roof inside the parapet = 2F wall inner faces 7.70 x 6.45 = 49.665 m2 (DXF 12B7 / 1292 / 1283 / 1279, beam tops included; was slab panels 7.4543 / 0.16 = 46.589, F-V770-1) less DOME-3 base r 2.205 = 15.275 m2 (S0 concrete dome L-d5401fa8 stands on the slab; layers stop at its base with an upturn, as at the +9.70 domes, Q-24 / Q-29) = 34.390 m2; outline from the 2F walls, no roof plan: Q-34 stays with the owner |
| L-b016c961ddf9e530e3c1 | FIN.ROOF.SCREED | m3 | 3.494 | 2.579 | ESTIMATE |  | 34.390 m2 x screed 0.075 avg (company default); +13.90 top roof inside the parapet = 2F wall inner faces 7.70 x 6.45 = 49.665 m2 (DXF 12B7 / 1292 / 1283 / 1279, beam tops included; was slab panels 7.4543 / 0.16 = 46.589, F-V770-1) less DOME-3 base r 2.205 = 15.275 m2 (S0 concrete dome L-d5401fa8 stands on the slab; layers stop at its base with an upturn, as at the +9.70 domes, Q-24 / Q-29) = 34.390 m2; outline from the 2F walls, no roof plan: Q-34 stays with the owner |
| L-aac1f35e08f85b643692 | FIN.WP.ROOF_UPTURN | lm | 29.800 | 42.155 | ESTIMATE | yes | parapet inner faces 2 x (7.70 + 6.45) = 28.30 + DOME-3 base ring 13.855 = 42.155 lm (was the 2F facade run 29.8 = outer faces 2 x (8.10 + 6.80): the upturn rises on the inner face) |
| L-90b40877c8c3da54ba1b | FIN.WP.MEMBRANE_ROLLS | pcs | 7.000 | 5.000 | ESTIMATE | yes | top roof 34.390 m2 x 8 rolls / 55.559 m2 of roof 1F-AT220 (T-764 method kept) = 4.95 -> 5 rolls |
