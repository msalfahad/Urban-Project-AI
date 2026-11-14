# T-776 boundary-wall foundation per run type on ARCH_TAKEOFF_V3.0.79 (fix rows, unwired)

| run type | centre m | in footings m | free m | pads | excavation m3 | band conc m3 | band above footings m3 | backfill m3 |
|---|---|---|---|---|---|---|---|---|
| FENCE | 44.07 | 1.60 | 42.47 | 10.0 | 32.8656 | 5.0964 | 0.0500 | 15.7305 |
| UNDER_BLDG | 44.37 | 19.35 | 25.02 | 0.0 | 12.0096 | 3.0024 | 0.5770 | 3.7530 |
| SEA_GAP | 3.50 | 0.50 | 3.00 | 0.0 | 1.4400 | 0.3600 | 0.0100 | 0.4500 |

| line | item | unit | before (set) | after | delta | label | basis |
|---|---|---|---|---|---|---|---|
| L-313384fed48301ae02d2 | STR.EARTH.EXCAVATION | m3 | 47.08732 (T-764) | 46.3152 | -0.77212 | ESTIMATE | per run type, p.14 A-A section (flush on the plot line, 10 past the inner face) x formation 1.60 (S01 -1.50 + 10 cm PC; no footing screed / membrane under the boundary member): FENCE 42.47 x 0.30 x 1.60 + 10 pads x 0.60 x 1.30 x 1.60 = 32.8656; UNDER_BLDG 25.02 x 0.30 x 1.60 = 12.0096; SEA_GAP 3.00 x 0.30 x 1.60 = 1.4400; = 46.3152 m3 (0.90 only at the pads; a blanket 0.90 would be 105.95) |
| L-89b8e6beaea55fc0e4c9 | STR.EARTH.BACKFILL | m3 | 32.623476 (T-764) | 30.423116 | -2.20036 | ESTIMATE | T-764 sum 32.6235 with its boundary part 22.1339 (two 0.10 strips x 1.57) replaced by 19.9335: inner 0.10 strip x 1.50 (PC top to N.G.) over 70.49 free = 10.5735 + 10 pads x (cut 1.248 - PC 0.078 - pad 0.195 beyond the strip - pad 0.039 in the strip) = 9.3600; outer face on the plot line: no strip |
| L-78d7c8a989ab34527a1c | STR.EARTH.DISPOSAL | m3 | 9.048556 (T-764) | 10.476796 | 1.42824 | ESTIMATE | T-764 9.0486 + excavation change -0.7721 - backfill change -2.2004 (in situ, no bulking) |
| L-6290a9f3d93f38cd46d6 | STR.CONC.BOUNDARY_WALL | m3 | 8.4588 (T-757) | 9.0958 | 0.637 | DEFAULT | Q-28 A B.W 0.20 x 0.60 over the free 70.49 m = 8.4588 (FENCE 5.0964, UNDER_BLDG 3.0024, SEA_GAP 0.3600) + the band part ABOVE the 14 footing tops it crosses (same underside -1.50, owner: deduct only the real overlap) 0.20 x (0.60 - H) x L = 0.6370 (C/F, FN 0.30; F15 0.40; F8, F10, F11, F14 0.50) = 9.0958 m3 |
| L-cda8f41522dc6f42b3d6 | STR.CONC.BOUNDARY_PAD | m3 | 3.12 (T-761) | 2.34 | -0.78 | SAFETY | 10 pads (T-761 SAFETY count) x 1.30 x (0.80 - 0.20 band through the pad, A-A '80' includes the G.B) x 0.30 = 2.3400 m3 (0.078 each was counted twice with the band) |
| L-d0313e5d204e2758996a | STR.CONC.BLINDING | m3 | 1.04 (T-761) | 0.78 | -0.26 | SAFETY | 10 pads x A-A PC beyond the band strip (0.80 + 0.10 toe - 0.30 strip = 0.60) x 1.30 x 0.10 = 0.7800 m3; the strip under the band is the new band-blinding line |
| L-16e428b50357188a94d2 | STR.FORMWORK | m2 | 12.6 (T-762) | 7.5 | -5.1 | ESTIMATE | 10 pads x (inner face 1.30 + two ends 0.60) x 0.30 = 0.75 each: the outer face is the band's face and the 0.20 under the band is no face = 7.5000 m2 |
| L-eb7b7329145b529cc89d | STR.FORMWORK | m2 | 83.36 (T-762) | 87.058 | 3.698 | ESTIMATE | hand: band 2 faces x 0.60 x 70.49 free = 84.588 - pad contact 10 x 1.30 x 0.30 = 3.900 + the faces above the footing tops 2 x (0.60 - H) x L = 6.3700 = 87.0580 m2 (replaces the face-ledger 83.36) |
| L-c632bb4647031c37de19 | EXT.FENCE.MASONRY_BELOW_NG | m2 | 23.4099 (T-769) | 20.535 | -2.8749 | ESTIMATE | T-769 method at formation 1.60: band 44.07 x h 0.50 (1.60 - 0.10 PC - 0.60 B.W - 0.40 upper G.B) - 10 columns x 0.30 x 0.50 = 20.5350 m2 |
| L-4f4e4c930e33ed6dafa3 | WP.FOUNDATION.BURIED_LIQUID | m2 | 154.94 (T-767) | 148.77 | -6.17 | ESTIMATE | T-767 method, buried height 1.50 (formation 1.60 - PC 0.10) instead of 1.57: straps 16.56 + 44.07 x 2 x 1.50 = 148.7700 m2 (T-767's RULE_DIFFERENCE note stands: p.14 prints no coating) |
| NEW:STR.CONC.BLINDING:BOUNDARY_BAND | STR.CONC.BLINDING | m3 | none | 2.1147 | +2.1147 | ESTIMATE | band plain concrete 70.49 free x 0.30 (A-A: flush outside, 10 past the inner face) x 0.10 = 2.1147 m3; carried by no candidate line (T-445 F-T445-4 'under the band between pads not drawn'; GB blinding L-7a5214a3 is the building ground beams only) |

Fence block 95.4415 m2 vs freelancer 74.4 m2 (1 x 37.20 x 2.00 (row 'fence', T-396 s.6)):

- height 2.00 -> printed 2.65 (p.12 SECTION '265') on his 37.20: +24.1800 m2 ENGINE_RIGHT
- length 37.20 -> 36.97 (north 31.37 + street plot face 5.60; his corner counted in both runs + 0.03 typed): -0.6095 m2 ENGINE_RIGHT
- street railing dip (p.12 elevation, scaled): -4.1190 m2 ENGINE_RIGHT
- 4 columns on his two runs x 0.30 x 2.65 (SAFETY count): -3.1800 m2 UNRESOLVED
- sea 2.40 + lower 1.20 runs he does not carry, net of their 6 columns: +4.7700 m2 RULE_DIFFERENCE
- residual +0.0000 m2

Beside (not in any line):

- drawing_method_band_0_40: {"band_free": 5.6392, "above_footings": 0.086, "note": "A-A lower G.B scales ~0.40, plan label 20x40; owner Q-28 A keeps B.W 20x60 PROVISIONAL (RFI C1 with the designer)"}
- f10_f_outline_at_H_0_30: 0.178
- t764_blanket_0_40_x_1_67: 47.08732
- blanket_0_90_x_1_67: 105.94647
- pad_positions_by_run_ends: "8 distinct run-end points (two corners shared), 4 of them inside a footing (C/F, C/F, F8 twice): ends alone justify 4 pads; intermediate columns 'SEE ARCH PLAN' are not drawn -> the T-761 SAFETY count 10 stays until the designer answers"
- freelancer_band: "8.604 = 71.7 x 0.20 x 0.60 ('perimeter tie beam'): RULE_DIFFERENCE on length (his 71.7 is not reproducible: 70.09 inner .. 72.59 outer free), ours 9.0958 adds the band above the footing tops he does not carry"
- possible_overlap_named: "L-438a4abd (building exterior GB blinding cut 0.10) may overlap the 0.30 band trench under the 25.02 m UNDER_BLDG free length by at most 25.02 x 0.30 x 0.10 = 0.75 m3; not changed here (T-764 line, its own cut basis)"
