# T-624 beam-end open items (R-T624-1, research, unwired)

Candidate ARCH_TAKEOFF_V3.0.57 (= V3.0.58 for STR.CONC.BEAM); Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179..). T-229 regions rebuilt with T-229's own code; frame offset spread GF 0.002275 m (42 pieces), 1F 0.00113 m (27 pieces), 2F 0.000475 m (10 pieces).

## (a) GF CB4 BAND0021.1.r2

```
{
 "basis": "the r2 mean-length excess is the drawn triangle between CB4's two faces and B27's face: inside no other member's rectangle, billed by no other line and in no other T-229 region; billed once",
 "billed_by_other_lines_m2": 0.0,
 "boundary_drawn_share": 1.0,
 "edge_lengths_m": [
  6.54537,
  6.274383
 ],
 "excess_m2": 0.027103,
 "excess_m3": 0.013552,
 "excess_minus_triangle_m3": 2e-06,
 "in_other_t229_regions_m2": 0.0,
 "in_own_t229_end_region_m2": 0.026207,
 "in_slab_panel_m2": 0.0,
 "in_support_columns_m2": 0.0,
 "line_id": "L-0e110d2c29b2cd318139",
 "own_t229_end_region_m2": 0.026397,
 "printed": "2.5099 x 0.2 x 0.5 = 0.250988",
 "rect_m2": 0.474877,
 "run": "BM-GF-021#BAND0021.1.r2",
 "triangle_m2": 0.027099,
 "triangle_sides_on": [
  "645 (1)",
  "805 (S-BEAM)"
 ],
 "triangle_x_depth_m3": 0.013549,
 "verdict": "ENGINE_RIGHT"
}
```

## (b) the five model-only pairs

| storey | mark | column | line | depth | piece | owned | in rect | T-229 end (class, add m3) | region m2 | piece outside region | wedge m2 | verdict | m3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GF | B28 | C27 | L-16dade3e7416d986e44f | 0.75 | 0.015961 | 0.015961 | 0.0 | GF:BAND0035.1 end 0 (END_SHORT_AT_CARRIED, 0.0612) | 0.081634 | 0.0 | None | ENGINE_RIGHT | 0.0 |
| GF | B26 | C27 | L-c6fa4992eb3ed2aa01e6 | 0.85 | 0.147325 | 0.147325 | 0.0 | GF:BAND0047.2 end 1 (END_SHORT_AT_CARRIED, 0.1812) | 0.213219 | 5.2e-05 | None | ENGINE_RIGHT | 4.5e-05 |
| GF | B26 | C25 | L-c6fa4992eb3ed2aa01e6 | 0.85 | 0.006189 | 0.006171 | 0.0 | GF:BAND0047.1 end 0 (END_AT_SUPPORT, 0.0) | None | None | 0.006171 | ENGINE_WRONG_OMISSION | 0.005245 |
| GF | B27 | C8 | L-3dddf99008ab922da814 | 0.85 | 0.22336 | 0.210123 | 0.0 | GF:BAND0048.1 end 0 (END_SHORT_OBLIQUE, 0.1787) | 0.210229 | 0.000355 | None | ENGINE_RIGHT | 0.000302 |
| 1F | B19 | C15 | L-45e0d887d33192039e05 | 0.75 | 0.010952 | 0.010952 | 0.009534 | 1F:BAND0030.1 end 1 (END_AT_SUPPORT, 0.0) | None | None | 0.001418 | ENGINE_WRONG_OMISSION | 0.001064 |

```
[
 {
  "column": "C27",
  "column_outline": "support + carried 31B (S-COL.HAT ANSI35)",
  "depth_m": 0.75,
  "in_other_band_m2": 0.0,
  "in_own_rectangle_m2": 0.0,
  "in_slab_panel_m2": 0.0,
  "line_id": "L-16dade3e7416d986e44f",
  "mark": "B28",
  "owned_m2": 0.015961,
  "piece_in_region_m2": 0.015961,
  "piece_m2": 0.015961,
  "piece_outside_region_m2": 0.0,
  "placement": "BILLED_BY_ADD",
  "region_carried_column_m2": 0.065,
  "region_content_agrees": "STRIP",
  "region_m2": 0.081634,
  "region_minus_drawn_content_m2": 0.006893,
  "region_minus_drawn_content_m3": 0.005169,
  "region_minus_strip_content_m3": 0.000439,
  "region_outline_on": [
   "1073 (1)",
   "709 (1)",
   "793 (S-COL.BON)",
   "795 (S-COL.BON)",
   "795 (S-COL.BON)",
   "795 (S-COL.BON)",
   "878 (S-COL.BON)"
  ],
  "region_vs_add_m3": 2.5e-05,
  "region_x_depth_m3": 0.061225,
  "residual_m3": 0.0,
  "storey": "GF",
  "strip_content_drawn_share": 1.0,
  "strip_content_m2": 0.081049,
  "t229_add_m3": 0.0612,
  "t229_class": "END_SHORT_AT_CARRIED",
  "t229_end": "GF:BAND0035.1 end 0",
  "verdict": "ENGINE_RIGHT"
 },
 {
  "column": "C27",
  "column_outline": "support + carried 31B (S-COL.HAT ANSI35)",
  "depth_m": 0.85,
  "in_other_band_m2": 0.0,
  "in_own_rectangle_m2": 0.0,
  "in_slab_panel_m2": 0.0,
  "line_id": "L-c6fa4992eb3ed2aa01e6",
  "mark": "B26",
  "owned_m2": 0.147325,
  "piece_in_region_m2": 0.147273,
  "piece_m2": 0.147325,
  "piece_outside_region_m2": 5.2e-05,
  "placement": "BILLED_BY_ADD",
  "region_carried_column_m2": 0.065,
  "region_content_agrees": "HULL",
  "region_m2": 0.213219,
  "region_minus_drawn_content_m2": 0.001117,
  "region_minus_drawn_content_m3": 0.000949,
  "region_minus_strip_content_m3": -0.000367,
  "region_outline_on": [
   "793 (S-COL.BON)",
   "795 (S-COL.BON)",
   "795 (S-COL.BON)",
   "795 (S-COL.BON)",
   "876 (S-COL.BON)",
   "878 (S-COL.BON)",
   "903 (1)",
   "904 (1)"
  ],
  "region_vs_add_m3": 3.6e-05,
  "region_x_depth_m3": 0.181236,
  "residual_m3": 4.5e-05,
  "storey": "GF",
  "strip_content_drawn_share": 0.902545,
  "strip_content_m2": 0.213651,
  "t229_add_m3": 0.1812,
  "t229_class": "END_SHORT_AT_CARRIED",
  "t229_end": "GF:BAND0047.2 end 1",
  "verdict": "ENGINE_RIGHT"
 },
 {
  "band_skew_deg": 1.487855,
  "column": "C25",
  "column_outline": "371",
  "depth_m": 0.85,
  "face_end_distance_to_column_m": [
   2e-06,
   0.0
  ],
  "faces_end_on_column": true,
  "in_other_band_m2": 1.8e-05,
  "in_own_rectangle_m2": 0.0,
  "in_slab_panel_m2": 0.0,
  "line_id": "L-c6fa4992eb3ed2aa01e6",
  "mark": "B26",
  "omission_m3": 0.005245,
  "owned_m2": 0.006171,
  "piece_m2": 0.006189,
  "storey": "GF",
  "t229_add_m3": 0.0,
  "t229_class": "END_AT_SUPPORT",
  "t229_end": "GF:BAND0047.1 end 0",
  "t229_square_threshold_would_drop_it": false,
  "verdict": "ENGINE_WRONG_OMISSION",
  "wedge_billed_by_any_line_m2": 0.0,
  "wedge_class": "DRAWN_WEDGE",
  "wedge_in_any_t229_region_m2": 0.0,
  "wedge_m2": 0.006171,
  "wedge_sides_on": [
   "1353 (S-TEXT-SLAB)",
   "881 (S-COL.BON)",
   "881 (S-COL.BON)",
   "903 (1)",
   "904 (1)"
  ]
 },
 {
  "column": "C8",
  "column_outline": "35C",
  "depth_m": 0.85,
  "in_other_band_m2": 0.013237,
  "in_own_rectangle_m2": 0.0,
  "in_slab_panel_m2": 0.0,
  "line_id": "L-3dddf99008ab922da814",
  "mark": "B27",
  "owned_m2": 0.210123,
  "piece_in_region_m2": 0.209768,
  "piece_m2": 0.22336,
  "piece_outside_region_m2": 0.000355,
  "placement": "BILLED_BY_ADD",
  "region_carried_column_m2": 0.0,
  "region_content_agrees": "HULL",
  "region_m2": 0.210229,
  "region_minus_drawn_content_m2": 0.000106,
  "region_minus_drawn_content_m3": 9e-05,
  "region_minus_strip_content_m3": -0.071905,
  "region_outline_on": [
   "686 (1)",
   "687 (1)",
   "806 (S-BEAM)",
   "858 (S-COL.BON)",
   "860 (S-COL.BON)",
   "860 (S-COL.BON)",
   "860 (S-COL.BON)"
  ],
  "region_vs_add_m3": -5e-06,
  "region_x_depth_m3": 0.178695,
  "residual_m3": 0.000302,
  "storey": "GF",
  "strip_content_drawn_share": 0.72665,
  "strip_content_m2": 0.294823,
  "t229_add_m3": 0.1787,
  "t229_class": "END_SHORT_OBLIQUE",
  "t229_end": "GF:BAND0048.1 end 0",
  "verdict": "ENGINE_RIGHT"
 },
 {
  "band_skew_deg": 6.909691,
  "column": "C15",
  "column_outline": "667",
  "depth_m": 0.75,
  "face_end_distance_to_column_m": [
   0.0,
   0.0
  ],
  "faces_end_on_column": true,
  "in_other_band_m2": 0.0,
  "in_own_rectangle_m2": 0.009534,
  "in_slab_panel_m2": 0.0,
  "line_id": "L-45e0d887d33192039e05",
  "mark": "B19",
  "omission_m3": 0.001064,
  "owned_m2": 0.010952,
  "piece_m2": 0.010952,
  "storey": "1F",
  "t229_add_m3": 0.0,
  "t229_class": "END_AT_SUPPORT",
  "t229_end": "1F:BAND0030.1 end 1",
  "t229_square_threshold_would_drop_it": true,
  "verdict": "ENGINE_WRONG_OMISSION",
  "wedge_billed_by_any_line_m2": 0.0,
  "wedge_class": "DRAWN_WEDGE",
  "wedge_in_any_t229_region_m2": 0.0,
  "wedge_m2": 0.001418,
  "wedge_sides_on": [
   "1639 (S-COL.BON)",
   "1713 (1)"
  ]
 }
]
```

### run decompositions

```
[
 {
  "beam": "1F B19 (BAND0030)",
  "drawing_derived_m3": 1.6301,
  "residual_m3": 0.0,
  "terms_m3": {
   "END_SHORT_OF_MEMBER 0.0289": 0.0289,
   "released_rectangles": 1.6012,
   "route_g_held_rectangles": 0.0
  }
 },
 {
  "beam": "GF B26 (BAND0047)",
  "drawing_derived_m3": 4.0846,
  "residual_m3": 0.0,
  "terms_m3": {
   "CUT_AT_CARRIED 0.1163": 0.1163,
   "END_SHORT_AT_CARRIED 0.1812": 0.1812,
   "released_rectangles": 3.1039,
   "route_g_held_rectangles": 0.6832
  }
 },
 {
  "beam": "GF B27 (BAND0048)",
  "drawing_derived_m3": 4.1918,
  "residual_m3": 0.0,
  "terms_m3": {
   "CUT_AT_CARRIED 0.4418": 0.4418,
   "END_SHORT_OBLIQUE 0.1787": 0.1787,
   "END_SHORT_OBLIQUE 0.2282": 0.2282,
   "released_rectangles": 2.5025,
   "route_g_held_rectangles": 0.8406
  }
 },
 {
  "beam": "GF B28 (BAND0035)",
  "drawing_derived_m3": 0.2121,
  "residual_m3": 0.0,
  "terms_m3": {
   "END_SHORT_AT_CARRIED 0.0612": 0.0612,
   "released_rectangles": 0.1509,
   "route_g_held_rectangles": 0.0
  }
 }
]
```

## (c) GF B27 tip (F-T619-1)

```
{
 "B1_line_id": "L-39779d6e8cbcc6ac2bae",
 "B1_rebuilt_m3": 0.151391,
 "B1_value_m3": "0.1514",
 "B27_line_id": "L-3dddf99008ab922da814",
 "B27_rectangle_m2": 2.944132,
 "B27_rectangle_x_0.85_m3": 2.502512,
 "B27_run_rectangle_term_m3": 2.5025,
 "companion_m3": 0.0,
 "route_g_junction_deduction_on_B1": [
  {
   "area_m2": 0.001524,
   "owner": "BAND0048.1"
  }
 ],
 "state": "BILLED_ONCE_BY_OWNER",
 "tip_in_B1_billed_m2": 0.0,
 "tip_in_B27_rectangle_m2": 0.001524,
 "tip_in_any_t229_region_m2": 0.0,
 "tip_m2": 0.001524,
 "verdict": "ENGINE_RIGHT",
 "zone_m2": 0.014761
}
```

## (d) FR-T614-H1 (F-T619-2)

```
{
 "band": "GF BAND0039 (CB8)",
 "billed_by_any_line_m2": 0.0,
 "boundary_drawn_share": 1.0,
 "boundary_on": [
  "626 (1)",
  "806 (S-BEAM)",
  "893 (S-COL.BON)"
 ],
 "column": "C13 (col 2, outline 37D)",
 "depth_m": 0.75,
 "end_gap_m": 0.024783,
 "faces_offset_and_drawn_length_m": [
  [
   -0.0,
   19.37
  ],
  [
   0.3,
   3.450217
  ]
 ],
 "held_row": "FR-T614-H1",
 "hull_length_m": 3.450217,
 "in_any_t229_region_m2": 0.0,
 "in_slab_panel_m2": 0.0,
 "line_id": "L-7c1a1da8004c4272ccba",
 "m3": 0.003405,
 "region_m2": 0.00454,
 "run": "BM-GF-040#BAND0039",
 "run_printed_length_m": 3.4502,
 "state": "MEASURED",
 "t614_held_m2": 0.00454,
 "verdict": "ENGINE_WRONG_OMISSION"
}
```

## Fix rows

- FR-T624-1 GF B26 L-c6fa4992eb3ed2aa01e6 at C25 (371): 0.006171 m2 x 0.85 = +0.005245 m3 (DRAWN_WEDGE (d))
- FR-T624-2 1F B19 L-45e0d887d33192039e05 at C15 (667): 0.001418 m2 x 0.75 = +0.001064 m3 (DRAWN_WEDGE (d))
- FR-T624-3 GF CB8 L-7c1a1da8004c4272ccba at C13 west end gap (col 2, 37D): 0.00454 m2 x 0.75 = +0.003405 m3 (END_GAP (c); supersedes FR-T614-H1)

## B10 STR.CONC.BEAM effect

```
{
 "after_c_m3": 66.392081,
 "after_t624_m3": 66.401795,
 "fix_rows_m3": 0.009714,
 "gap_to_his_m3": 0.30792,
 "gap_to_his_pct": 0.465883,
 "his_m3": 66.093875,
 "note": "research, unwired: no candidate line moved; for the next wiring manifest",
 "v14_after_total_m3": [
  66.392081,
  66.393376
 ]
}
```

