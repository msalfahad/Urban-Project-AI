# T-610 beam band overlap census (R-T610-1, research, unwired)

Candidate ARCH_TAKEOFF_V3.0.57 (= V3.0.58 for STR.CONC.BEAM); Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179..). Areas m2, volumes m3.

| storey | lines | zones | verdicts | zone m2 | engine m3 | physical m3 | engine - physical | DOUBLE | DEPTH | OMISSION | HELD zone m2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GF | 68 | 5 | ENGINE_RIGHT 2, ENGINE_WRONG_DOUBLE_COUNT 1, ENGINE_WRONG_UNDER 2 | 0.019926 | 0.011303 | 0.016937 | -0.005634 | 0.000692 | -0.006326 | -0.0 | None |
| 1F | 47 | 3 | ENGINE_RIGHT 1, ENGINE_WRONG_UNDER 1, HELD 1 | 0.016667 | 0.009375 | 0.0125 | -0.003125 | 0.0 | -0.003125 | 0.0 | 0.003333 |
| 2F | 19 | 1 | ENGINE_RIGHT 1 | 0.02 | 0.015 | 0.015 | 0.0 | 0.0 | 0.0 | 0.0 | None |

## Zones (pair by pair)

| storey | A mark (line, class) | B mark (line, class) | zone m2 | dA / dB | A only | B only | both | neither | engine m3 | physical m3 | diff | verdict | owner (deeper) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GF | B1 (L-39779d6e8cbcc6ac2bae, RELEASED) | B27 (L-3dddf99008ab922da814, RELEASED) | 0.014761 | 0.4 / 0.85 | 0.013237 | 0.001524 | 0.0 | 0.0 | 0.00659 | 0.012547 | -0.005957 | ENGINE_WRONG_UNDER | L-3dddf99008ab922da814 |
| GF | B27 (L-3dddf99008ab922da814, RELEASED) | CB8 (L-7c1a1da8004c4272ccba, RELEASED) | 0.00369 | 0.85 / 0.75 | 0.0 | 0.00369 | 0.0 | 0.0 | 0.002768 | 0.003137 | -0.000369 | ENGINE_WRONG_UNDER | L-3dddf99008ab922da814 |
| GF | B27 (L-3dddf99008ab922da814, RELEASED) | CB8 (L-bd16e6923af088014236, RELEASED) | 0.000923 | 0.85 / 0.75 | 0.0 | 0.0 | 0.000923 | 0.0 | 0.001476 | 0.000784 | 0.000692 | ENGINE_WRONG_DOUBLE_COUNT | L-3dddf99008ab922da814 |
| GF | B4 (L-6d79eaf1b0f24483b0e0, RELEASED) | B26 (L-c6fa4992eb3ed2aa01e6, RELEASED) | 0.000519 | 0.5 / 0.85 | 0.0 | 0.000519 | 0.0 | 0.0 | 0.000442 | 0.000442 | 0.0 | ENGINE_RIGHT | L-c6fa4992eb3ed2aa01e6 |
| GF | CB8 (L-b6b4eb28a8001c2af2dd, RELEASED) | B26 (L-c6fa4992eb3ed2aa01e6, RELEASED) | 3.3e-05 | 0.75 / 0.85 | 0.0 | 3.3e-05 | 0.0 | 0.0 | 2.8e-05 | 2.8e-05 | -0.0 | ENGINE_RIGHT | L-c6fa4992eb3ed2aa01e6 |
| 1F | B4 (L-02ee97d409df4b3a501b, RELEASED) | CB10 (L-50667f69855b6d588011, HELD) | 0.003333 | 0.5 / None | 0.003333 | 0.0 | 0.0 | 0.0 | None | None | None | HELD | - |
| 1F | CB12 (L-076a6d9e6df46aef97d1, RELEASED) | B6 (L-651a3d191bc4cb07cc1d, RELEASED) | 0.0125 | 0.75 / 0.5 | 0.0 | 0.0125 | 0.0 | 0.0 | 0.00625 | 0.009375 | -0.003125 | ENGINE_WRONG_UNDER | L-076a6d9e6df46aef97d1 |
| 1F | CB12 (L-076a6d9e6df46aef97d1, RELEASED) | CB11 (L-780b8142b030c0108b6b, RELEASED) | 0.004167 | 0.75 / 0.75 | 0.004167 | 0.0 | 0.0 | 0.0 | 0.003125 | 0.003125 | 0.0 | ENGINE_RIGHT | L-076a6d9e6df46aef97d1 |
| 2F | B2 (L-2999807a87e55d057be3, RELEASED) | B7 (L-f4a95b8019ae333d81ae, RELEASED) | 0.02 | 0.4 / 0.75 | 0.0 | 0.02 | 0.0 | 0.0 | 0.015 | 0.015 | 0.0 | ENGINE_RIGHT | L-f4a95b8019ae333d81ae |

## Fix rows

- FR-T610-1 GF B1 (L-39779d6e8cbcc6ac2bae) x B27 (L-3dddf99008ab922da814): ENGINE_WRONG_UNDER, zone 0.014761 m2, engine - physical -0.005957 m3 (DOUBLE 0.0, DEPTH -0.005957, OMISSION -0.0); owner L-3dddf99008ab922da814; line changes {'L-39779d6e8cbcc6ac2bae': -0.005295, 'L-3dddf99008ab922da814': 0.011252}
- FR-T610-2 GF B27 (L-3dddf99008ab922da814) x CB8 (L-7c1a1da8004c4272ccba): ENGINE_WRONG_UNDER, zone 0.00369 m2, engine - physical -0.000369 m3 (DOUBLE 0.0, DEPTH -0.000369, OMISSION -0.0); owner L-3dddf99008ab922da814; line changes {'L-3dddf99008ab922da814': 0.003137, 'L-7c1a1da8004c4272ccba': -0.002768}
- FR-T610-3 GF B27 (L-3dddf99008ab922da814) x CB8 (L-bd16e6923af088014236): ENGINE_WRONG_DOUBLE_COUNT, zone 0.000923 m2, engine - physical 0.000692 m3 (DOUBLE 0.000692, DEPTH -0.0, OMISSION -0.0); owner L-3dddf99008ab922da814; line changes {'L-3dddf99008ab922da814': 0.0, 'L-bd16e6923af088014236': -0.000692}
- FR-T610-4 1F CB12 (L-076a6d9e6df46aef97d1) x B6 (L-651a3d191bc4cb07cc1d): ENGINE_WRONG_UNDER, zone 0.0125 m2, engine - physical -0.003125 m3 (DOUBLE 0.0, DEPTH -0.003125, OMISSION -0.0); owner L-076a6d9e6df46aef97d1; line changes {'L-076a6d9e6df46aef97d1': 0.009375, 'L-651a3d191bc4cb07cc1d': -0.00625}

## Plan billed by two lines outside every drawn common block

0 pair(s): none (route G junction squares are deducted once; ledger runs stop at other members' plans)

## Sensitivity: oblique drawn end cap (a face running on past its partner)

- base: cap 1 x width (the census above)
- cap 0 x width: {'per_storey_engine_minus_physical_m3': {'GF': -0.006326, '1F': -0.003125, '2F': None}, 'fix_rows': ['GF B1 x B27 -0.005957', 'GF B27 x CB8 -0.000369', '1F CB12 x B6 -0.003125'], 'billed_twice_outside': 0}
- cap 2 x width: {'per_storey_engine_minus_physical_m3': {'GF': -0.005634, '1F': -0.003125, '2F': 0.0}, 'fix_rows': ['GF B1 x B27 -0.005957', 'GF B27 x CB8 -0.000369', 'GF B27 x CB8 0.000692', '1F CB12 x B6 -0.003125'], 'billed_twice_outside': 0}

## Ledger plan checks (HL lines)

- GF B24 L-007ee1494e960a6985a7: ledger 1.426197 vs plan model 1.415625 (residual 0.010572) MODEL_RESIDUAL
- GF B5 L-06fc0372ccf1017c16f6: ledger 0.36166 vs plan model 0.361696 (residual -3.6e-05) MODEL_MATCHES
- GF CB4 L-0e110d2c29b2cd318139: ledger 0.250988 vs plan model 0.237438 (residual 0.01355) MODEL_RESIDUAL
- GF CB7 L-128bbb3f98713383935f: ledger 1.6801 vs plan model 1.77 (residual -0.0899) MODEL_RESIDUAL
- GF B28 L-16dade3e7416d986e44f: ledger 0.212122 vs plan model 0.162882 (residual 0.04924) MODEL_RESIDUAL
- GF CB1 L-2e2fc5195697247a6a0b: ledger 1.940009 vs plan model 1.970625 (residual -0.030616) MODEL_RESIDUAL
- GF B27 L-3dddf99008ab922da814: ledger 4.1918 vs plan model 4.190879 (residual 0.000921) MODEL_MATCHES
- GF B1 L-4a9628ac51fddc7945cd: ledger 0.205544 vs plan model 0.205557 (residual -1.3e-05) MODEL_MATCHES
- GF B17 L-616a12281372088e618d: ledger 1.76542 vs plan model 1.764562 (residual 0.000858) MODEL_MATCHES
- GF B4 L-6d79eaf1b0f24483b0e0: ledger 0.3429 vs plan model 0.342927 (residual -2.7e-05) MODEL_MATCHES
- GF B20 L-6e1034e07c44c4644c22: ledger 0.990006 vs plan model 0.945 (residual 0.045006) MODEL_RESIDUAL
- GF CB8 L-7c1a1da8004c4272ccba: ledger 0.716937 vs plan model 0.776299 (residual -0.059362) MODEL_RESIDUAL
- GF CB1 L-9270e8b8860414386adb: ledger 1.33875 vs plan model 1.366875 (residual -0.028125) MODEL_RESIDUAL
- GF B8 L-9a55aadc9f0880ae37a7: ledger 0.528021 vs plan model 0.528021 (residual 0.0) MODEL_MATCHES
- GF B4 L-a38b4013f5e3a30830b4: ledger 0.296447 vs plan model 0.296446 (residual 1e-06) MODEL_MATCHES
- GF B2 L-ac63a60a21f5618611a1: ledger 0.2002 vs plan model 0.232 (residual -0.0318) MODEL_RESIDUAL
- GF B11 L-b274a04546a58e0ecfdd: ledger 0.68655 vs plan model 0.686262 (residual 0.000288) MODEL_MATCHES
- GF CB8 L-bd16e6923af088014236: ledger 1.310964 vs plan model 1.305 (residual 0.005964) MODEL_MATCHES
- GF B26 L-c6fa4992eb3ed2aa01e6: ledger 4.0846 vs plan model 4.035184 (residual 0.049416) MODEL_RESIDUAL
- GF B7 L-cbf53752cfd897c35c2c: ledger 0.255 vs plan model 0.255 (residual 0.0) MODEL_MATCHES
- GF B9 L-db759eb6300a0147c463: ledger 0.9153 vs plan model 0.945 (residual -0.0297) MODEL_RESIDUAL
- GF B13 L-fab1bc66232c8d568797: ledger 0.952313 vs plan model 0.95226 (residual 5.3e-05) MODEL_MATCHES
- 1F CB12 L-076a6d9e6df46aef97d1: ledger 1.079463 vs plan model 1.062188 (residual 0.017275) MODEL_RESIDUAL
- 1F B1 L-419db30d16a77844a58d: ledger 0.129688 vs plan model 0.129569 (residual 0.000119) MODEL_MATCHES
- 1F B19 L-45e0d887d33192039e05: ledger 1.62356 vs plan model 1.631121 (residual -0.007561) MODEL_MATCHES
- 1F B25 L-74bde45d27edaeb8dc32: ledger 2.849975 vs plan model 2.849834 (residual 0.000141) MODEL_MATCHES
- 1F CB11 L-935e72dff296573fff64: ledger 0.619159 vs plan model 0.6225 (residual -0.003341) MODEL_MATCHES
- 1F CB11 L-9696bbb45246c6dce183: ledger 1.539652 vs plan model 1.52524 (residual 0.014412) MODEL_RESIDUAL
- 1F B23 L-ab62c5990fe1114d6171: ledger 1.132104 vs plan model 1.0725 (residual 0.059604) MODEL_RESIDUAL
- 1F CB13 L-ca163e55e38f8968a766: ledger 0.467672 vs plan model 0.45875 (residual 0.008922) MODEL_MATCHES

## F-C-P03-2

```
{
 "zone_m2": 0.014761,
 "checker_overlap_m2": 0.014761,
 "B1_bills_m2": 0.013237,
 "B27_run_bills_m2": 0.001524,
 "both_m2": 0.0,
 "neither_m2": 0.0,
 "B1_line_excess_vs_net_m3": 0.005295,
 "checker_B1_m3": 0.005295,
 "physical_m3": 0.012547,
 "engine_m3": 0.00659,
 "engine_minus_physical_m3": -0.005957,
 "verdict": "ENGINE_WRONG_UNDER",
 "owner_deeper": {
  "owner": "L-3dddf99008ab922da814",
  "lines": {
   "L-39779d6e8cbcc6ac2bae": {
    "engine_in_zone_m3": 0.005295,
    "should_m3": 0.0,
    "change_m3": -0.005295
   },
   "L-3dddf99008ab922da814": {
    "engine_in_zone_m3": 0.001295,
    "should_m3": 0.012547,
    "change_m3": 0.011252
   }
  }
 }
}
```

