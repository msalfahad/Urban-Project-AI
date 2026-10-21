# The ten worked examples - verification chain (generated)

OWNER / PROJECT RULE -> SOURCE DRAWING -> GEOMETRIC INTERPRETATION -> MEASUREMENT FORMULA -> INDEPENDENT EXPECTED RESULT -> ENGINE RESULT -> DIFFERENCE -> PASS / FAIL -> BOQ IMPACT

Expected = the hand derivation (tests/m9_p2b5/install_cases.py, typed literals). Engine = ARCH_TAKEOFF_V2.6 (waterproofing_system + wp_install). Reference = the independent calculator rebuilding the engine's own cutting plan piece by piece (tests/m9_p2b5/install_reference.py); `-` where the reference does not compute the quantity. Tolerance 0.0005 (rounding only).

**297 of 297 checks PASS.**

## IX-01 - 2.00 x 2.00 m bathroom, closed (no doorway)

**Rules:** UP-WP-001 roll 1.00 x 10.00 m; UP-WP-002 lap 0.10 m; UP-WP-003 upturn 0.20 m; UP-WP-DOOR-001 doorway continuation width x (depth + 0.10); UP-WP-LAY-001 rolls -> seams -> membrane; UP-WP-MAT-001 net / installed / procurement apart; UP-WP-004 corners and penetrations by detail; N-11 floor-to-wall junction OPEN (alternatives shown)

**Source drawing (synthetic):** ring [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]

**Geometric interpretation:** one closed band loop of 8.00 m from the ring start (0, 0); 4 internal corners at run positions 0 / 2.00 / 4.00 / 6.00 no drain drawn: NOT_SHOWN

**Formula:** floor = 2.00 x 2.00; upturn = 8.00 x 0.20; every band piece laps 0.10 over the one before, the first over the last (5 joints)

**Hand derivation:**

1. floor 4.00 + upturn 1.60 = proven subtotal 5.60 m2
2. strips along X (square: tie, X first): S1 y 0-1.00, S2 0.90-1.90, S3 1.80-2.00 (0.20 wide)
3. cuts S1 2.00, S2 2.00, and 2.00 ripped into S3 0.20 + lanes 0.30 + 0.30 + residue 0.20 (0.40 m2)
4. band 8.00 closed: lanes 2.00 + 2.00 cover 1.90 + 1.90; segment 3 x (L - 0.10) >= 4.20 -> 1.50 m, ripped into 3 lanes + 0.10 residue (0.15 m2)
5. pieces B1 2.00, B2 2.00, B3 1.50, B4 1.50, B5 1.50: B1 -0.10..1.90, B2 1.80..3.80, B3 3.70..5.20, B4 5.10..6.60, B5 6.50..8.00
6. joints 7.90-8.00 (the closure), 1.80-1.90, 3.70-3.80, 5.10-5.20, 6.50-6.60 -> to the corners 0.00, 0.10, 0.20, 0.80, 0.50 -> min 0.00 (the closure joint ends on the corner at the ring start)
7. floor seams S1/S2 y 0.90-1.00 and S2/S3 y 1.80-1.90 meet the east wall at r 2.90-3.00 / 3.80-3.90 and the west wall at r 7.00-7.10 / 6.10-6.20: 4 seam ends under the flange
8. joint 3.70-3.80 touches the seam end 3.80-3.90 (no overlap): min joint-to-seam 0.00, 0 stacked
9. laps: side 2 x 2.00 x 0.10 = 0.40; flange 8.00 x 0.10 = 0.80; band ends 5 x 0.03 = 0.15 -> 1.35
10. installed 5.60 + 1.35 = 6.95; consumed 3 x 2.00 + 1.50 = 7.50 = 6.95 + 0.55 true waste; 1 roll, 2.50 m2 stock; seams 2 + 5 = 7
11. continuous fold: developed 2.40 x 2.40, 3 strips 2.40 long (the last 0.60 wide) = 7.20 m2, 1 roll, 2 seams; installed (2 x 1.00 + 0.60) x 2.40 = 6.24 = 5.60 + laps 0.48 + corner squares 4 x 0.04 = 0.16

| quantity | expected (hand) | engine | reference | difference | result |
|---|---|---|---|---|---|
| direction | X | X | - | 0 | PASS |
| proven_subtotal_m2 | 5.6 | 5.6 | 5.6 | 0 | PASS |
| consumed_m2 | 7.5 | 7.5 | 7.5 | 0 | PASS |
| installed_m2 | 6.95 | 6.95 | 6.95 | 0 | PASS |
| laps_total_m2 | 1.35 | 1.35 | 1.35 | 0 | PASS |
| laps_side_m2 | 0.4 | 0.4 | 0.4 | 0 | PASS |
| laps_floor_end_m2 | 0 | 0 | 0 | 0 | PASS |
| laps_junction_m2 | 0.8 | 0.8 | 0.8 | 0 | PASS |
| laps_band_end_m2 | 0.15 | 0.15 | 0.15 | 0 | PASS |
| laps_doorway_m2 | 0 | 0 | 0 | 0 | PASS |
| true_waste_m2 | 0.55 | 0.55 | 0.55 | 0 | PASS |
| reusable_m2 | 0 | 0 | 0 | 0 | PASS |
| stock_m2 | 2.5 | 2.5 | 2.5 | 0 | PASS |
| rolls | 1 | 1 | 1 | 0 | PASS |
| floor_seams | 2 | 2 | 2 | 0 | PASS |
| floor_end_laps | 0 | 0 | 0 | 0 | PASS |
| band_joints | 5 | 5 | 5 | 0 | PASS |
| seams | 7 | 7 | 7 | 0 | PASS |
| band_pieces_m | [1.5, 1.5, 1.5, 2, 2] | [1.5, 1.5, 1.5, 2, 2] | [1.5, 1.5, 1.5, 2, 2] | 0 | PASS |
| min_joint_corner_m | 0 | 0 | 0 | 0 | PASS |
| min_joint_seam_end_m | 0 | 0 | 0 | 0 | PASS |
| joints_stacked_on_seam_ends | 0 | 0 | 0 | 0 | PASS |
| jamb_butt_joints | 0 | 0 | 0 | 0 | PASS |
| terminations | 0 | 0 | 0 | 0 | PASS |
| corners_internal | 4 | 4 | 4 | 0 | PASS |
| corners_external | 0 | 0 | 0 | 0 | PASS |
| flange_pleats_m2 | 0.04 | 0.04 | 0.04 | 0 | PASS |
| flange_gaps_m2 | 0 | 0 | 0 | 0 | PASS |
| t_flange_over_seam_end | 4 | 4 | 4 | 0 | PASS |
| t_doorway_lap_over_seam_end | 0 | 0 | 0 | 0 | PASS |
| t_seam_end_at_break | 0 | 0 | 0 | 0 | PASS |
| fold | rolls 1; consumed_m2 7.2; installed_m2 6.24; laps_m2 0.48; corner_excess_m2 0.16; seams 2 | rolls 1; consumed_m2 7.2; installed_m2 6.24; laps_m2 0.48; corner_excess_m2 0.16; seams 2 | - | 0 | PASS |

**Open details (flags):** expected DRAIN_NOT_SHOWN, FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_AT_CORNER, JOINT_OFFSET_UNVERIFIED, JOINT_TOUCHES_SEAM_END, LAY_ORDER_NOT_VALIDATED; engine DRAIN_NOT_SHOWN, FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_AT_CORNER, JOINT_OFFSET_UNVERIFIED, JOINT_TOUCHES_SEAM_END, LAY_ORDER_NOT_VALIDATED - PASS

**BOQ impact:** material only (B, rolls): 6.95 m2 installed, 1 roll; the closure joint at a corner is an installation instruction (start the loop off the corner), no quantity change

Diagrams: `diagrams/IX-01_install.svg`, `diagrams/IX-01_cutting.svg`

## IX-02 - 3.00 x 4.00 m bathroom, one 1.00 m door (the audited WP-B)

**Rules:** UP-WP-001 roll 1.00 x 10.00 m; UP-WP-002 lap 0.10 m; UP-WP-003 upturn 0.20 m; UP-WP-DOOR-001 doorway continuation width x (depth + 0.10); UP-WP-LAY-001 rolls -> seams -> membrane; UP-WP-MAT-001 net / installed / procurement apart; UP-WP-004 corners and penetrations by detail; N-11 floor-to-wall junction OPEN (alternatives shown)

**Source drawing (synthetic):** ring [(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)]; doors [D1]

**Geometric interpretation:** one open run of 13.00 m from the east jamb (x 2.50) round to the west jamb (x 1.50); corners SE 1.50, NE 4.50, NW 8.50, SW 11.50

**Formula:** as Phase 2B-4 WPB-A1 (the hand derivation there); the installation layer adds the joint, seam-end and jamb inventory

**Hand derivation:**

1. proven subtotal 12.00 + 2.60 + 0.20 = 14.80 m2; strips ALONG_Y S1..S5 (S5 0.40 wide)
2. cuts S1-S4 3.00 whole; 3.00 ripped S5 0.40 + L1 + L2; 2.80 ripped L3 L4 L5 + 0.10 residue
3. DW 1.00 from L1 (2.00 left = B2); B1 = L2 3.00; B3 B4 B5 2.80
4. joints 2.90-3.00, 4.80-4.90, 7.50-7.60, 10.20-10.30: corners 1.40, 0.30, 0.90, 1.20 -> 0.30; the joints at 4.80 and 7.50 lie on the S4/S5 and S1/S2 seam ends -> 2 stacked, min 0.00
5. 7 seam ends under the flange + 1 under the doorway lap; 2 butt joints at the jambs; best order 2.00, 3.00, 2.80 x 3 from the west jamb: corners >= 0.30, seam ends >= 0.20
6. consumed 17.80 = installed 17.52 + 0.28 true waste; 2 rolls, stock 2.20; seams 4 + 4 = 8
7. continuous fold: developed 4.40 x 3.40, 4 strips 4.40 long ALONG_X (the last 0.70) = 17.60 m2, 2 rolls, 3 seams; installed 16.28 = 14.80 + laps 1.32 + corner squares 0.16
8. junction flange: 2 rolls up to 0.15 m, 3 rolls from 0.16 m (Phase 2B-4 SWEEP_HAND)

| quantity | expected (hand) | engine | reference | difference | result |
|---|---|---|---|---|---|
| direction | Y | Y | - | 0 | PASS |
| proven_subtotal_m2 | 14.8 | 14.8 | 14.8 | 0 | PASS |
| consumed_m2 | 17.8 | 17.8 | 17.8 | 0 | PASS |
| installed_m2 | 17.52 | 17.52 | 17.52 | 0 | PASS |
| laps_total_m2 | 2.72 | 2.72 | 2.72 | 0 | PASS |
| laps_side_m2 | 1.2 | 1.2 | 1.2 | 0 | PASS |
| laps_floor_end_m2 | 0 | 0 | 0 | 0 | PASS |
| laps_junction_m2 | 1.3 | 1.3 | 1.3 | 0 | PASS |
| laps_band_end_m2 | 0.12 | 0.12 | 0.12 | 0 | PASS |
| laps_doorway_m2 | 0.1 | 0.1 | 0.1 | 0 | PASS |
| true_waste_m2 | 0.28 | 0.28 | 0.28 | 0 | PASS |
| reusable_m2 | 0 | 0 | 0 | 0 | PASS |
| stock_m2 | 2.2 | 2.2 | 2.2 | 0 | PASS |
| rolls | 2 | 2 | 2 | 0 | PASS |
| floor_seams | 4 | 4 | 4 | 0 | PASS |
| floor_end_laps | 0 | 0 | 0 | 0 | PASS |
| band_joints | 4 | 4 | 4 | 0 | PASS |
| seams | 8 | 8 | 8 | 0 | PASS |
| band_pieces_m | [2, 2.8, 2.8, 2.8, 3] | [2, 2.8, 2.8, 2.8, 3] | [2, 2.8, 2.8, 2.8, 3] | 0 | PASS |
| min_joint_corner_m | 0.3 | 0.3 | 0.3 | 0 | PASS |
| min_joint_seam_end_m | 0 | 0 | 0 | 0 | PASS |
| joints_stacked_on_seam_ends | 2 | 2 | 2 | 0 | PASS |
| jamb_butt_joints | 2 | 2 | 2 | 0 | PASS |
| terminations | 0 | 0 | 0 | 0 | PASS |
| corners_internal | 4 | 4 | 4 | 0 | PASS |
| corners_external | 0 | 0 | 0 | 0 | PASS |
| flange_pleats_m2 | 0.04 | 0.04 | 0.04 | 0 | PASS |
| flange_gaps_m2 | 0 | 0 | 0 | 0 | PASS |
| t_flange_over_seam_end | 7 | 7 | 7 | 0 | PASS |
| t_doorway_lap_over_seam_end | 1 | 1 | 1 | 0 | PASS |
| t_seam_end_at_break | 0 | 0 | 0 | 0 | PASS |
| best_corner_m | 0.3 | 0.3 | 0.3 | 0 | PASS |
| best_seam_end_m | 0.2 | 0.2 | 0.2 | 0 | PASS |
| junction_rolls | [2, 3] | [2, 3] | - | 0 | PASS |
| junction_roll_change_flange_m | 0.16 | 0.16 | - | 0 | PASS |
| fold | rolls 2; consumed_m2 17.6; installed_m2 16.28; laps_m2 1.32; corner_excess_m2 0.16; seams 3 | rolls 2; consumed_m2 17.6; installed_m2 16.28; laps_m2 1.32; corner_excess_m2 0.16; seams 3 | - | 0 | PASS |

**Open details (flags):** expected DRAIN_NOT_SHOWN, FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_OFFSET_UNVERIFIED, JOINT_ON_SEAM_END, JUNCTION_CHANGES_ROLL_COUNT, LAY_ORDER_NOT_VALIDATED; engine DRAIN_NOT_SHOWN, FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_OFFSET_UNVERIFIED, JOINT_ON_SEAM_END, JUNCTION_CHANGES_ROLL_COUNT, LAY_ORDER_NOT_VALIDATED - PASS

**BOQ impact:** B 17.52 m2 / 2 rolls as V2.5; the material state becomes PROVISIONAL_DETAILS_OPEN while the junction is open (2 rolls with a flange up to 0.15 m, 3 from 0.16 m); 17.60 m2 with a fold

Diagrams: `diagrams/IX-02_install.svg`, `diagrams/IX-02_cutting.svg`

## IX-03 - 3.60 x 3.00 m wet area, two doors and a pipe sleeve (the audited WP-E)

**Rules:** UP-WP-001 roll 1.00 x 10.00 m; UP-WP-002 lap 0.10 m; UP-WP-003 upturn 0.20 m; UP-WP-DOOR-001 doorway continuation width x (depth + 0.10); UP-WP-LAY-001 rolls -> seams -> membrane; UP-WP-MAT-001 net / installed / procurement apart; UP-WP-004 corners and penetrations by detail; N-11 floor-to-wall junction OPEN (alternatives shown)

**Source drawing (synthetic):** ring [(0.0, 0.0), (3.6, 0.0), (3.6, 3.0), (0.0, 3.0)]; doors [D1, D2]; pipes [T1]

**Geometric interpretation:** two open runs: 3.90 m from D2 to D1 and 7.60 m from D1 to D2; a pipe sleeve drawn at (3.20, 0.40); no drain drawn

**Formula:** as Phase 2B-4 WPE-A1

**Hand derivation:**

1. proven subtotal 10.80 + 11.50 x 0.20 + 0.34 = 13.44 m2; strips ALONG_Y S1..S4 (S4 0.90)
2. a 3.64 m band segment (3 lanes) and a 0.90 m doorway segment (DW-D1, DW-D2, B1)
3. run 1: B1 0.90 + B2 3.10, joint 0.80-0.90 (1.50 from the corner, 0.20 from a seam end); run 2: B3 3.64, B4 3.64, B5 0.52, joints 3.54-3.64 and 7.08-7.18 -> the last ends 0.02 from the corner at 7.20
4. best order of run 2: 3.64, 0.52, 3.64 -> 0.14 from corners and seam ends
5. pipe: 0.30 clear of the band flanges, 0.40 of the nearest floor seam -> a centred collar up to 0.60 m
6. consumed 16.54 = installed 15.75 + 0.79 true waste; 2 rolls, stock 3.46; seams 3 + 3 = 6; 4 butt joints
7. continuous fold: developed 4.00 x 3.40, 4 strips 4.00 ALONG_X = 16.00 m2, 2 rolls, 3 seams, installed 14.80

| quantity | expected (hand) | engine | reference | difference | result |
|---|---|---|---|---|---|
| direction | Y | Y | - | 0 | PASS |
| proven_subtotal_m2 | 13.44 | 13.44 | 13.44 | 0 | PASS |
| consumed_m2 | 16.54 | 16.54 | 16.54 | 0 | PASS |
| installed_m2 | 15.75 | 15.75 | 15.75 | 0 | PASS |
| laps_total_m2 | 2.31 | 2.31 | 2.31 | 0 | PASS |
| laps_side_m2 | 0.9 | 0.9 | 0.9 | 0 | PASS |
| laps_floor_end_m2 | 0 | 0 | 0 | 0 | PASS |
| laps_junction_m2 | 1.15 | 1.15 | 1.15 | 0 | PASS |
| laps_band_end_m2 | 0.09 | 0.09 | 0.09 | 0 | PASS |
| laps_doorway_m2 | 0.17 | 0.17 | 0.17 | 0 | PASS |
| true_waste_m2 | 0.79 | 0.79 | 0.79 | 0 | PASS |
| reusable_m2 | 0 | 0 | 0 | 0 | PASS |
| stock_m2 | 3.46 | 3.46 | 3.46 | 0 | PASS |
| rolls | 2 | 2 | 2 | 0 | PASS |
| floor_seams | 3 | 3 | 3 | 0 | PASS |
| floor_end_laps | 0 | 0 | 0 | 0 | PASS |
| band_joints | 3 | 3 | 3 | 0 | PASS |
| seams | 6 | 6 | 6 | 0 | PASS |
| band_pieces_m | [0.52, 0.9, 3.1, 3.64, 3.64] | [0.52, 0.9, 3.1, 3.64, 3.64] | [0.52, 0.9, 3.1, 3.64, 3.64] | 0 | PASS |
| min_joint_corner_m | 0.02 | 0.02 | 0.02 | 0 | PASS |
| min_joint_seam_end_m | 0.14 | 0.14 | 0.14 | 0 | PASS |
| joints_stacked_on_seam_ends | 0 | 0 | 0 | 0 | PASS |
| jamb_butt_joints | 4 | 4 | 4 | 0 | PASS |
| terminations | 0 | 0 | 0 | 0 | PASS |
| corners_internal | 4 | 4 | 4 | 0 | PASS |
| corners_external | 0 | 0 | 0 | 0 | PASS |
| flange_pleats_m2 | 0.04 | 0.04 | 0.04 | 0 | PASS |
| flange_gaps_m2 | 0 | 0 | 0 | 0 | PASS |
| t_flange_over_seam_end | 5 | 5 | 5 | 0 | PASS |
| t_doorway_lap_over_seam_end | 1 | 1 | 1 | 0 | PASS |
| t_seam_end_at_break | 0 | 0 | 0 | 0 | PASS |
| best_corner_m | 0.14 | 0.14 | 0.14 | 0 | PASS |
| best_seam_end_m | 0.14 | 0.14 | 0.14 | 0 | PASS |
| pipe_T1_clear_m | 0.3 | 0.3 | 0.3 | 0 | PASS |
| fold | rolls 2; consumed_m2 16; installed_m2 14.8; laps_m2 1.2; corner_excess_m2 0.16; seams 3 | rolls 2; consumed_m2 16; installed_m2 14.8; laps_m2 1.2; corner_excess_m2 0.16; seams 3 | - | 0 | PASS |

**Open details (flags):** expected FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_OFFSET_UNVERIFIED, LAY_ORDER_NOT_VALIDATED, NO_DRAIN_DRAWN; engine FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_OFFSET_UNVERIFIED, LAY_ORDER_NOT_VALIDATED, NO_DRAIN_DRAWN - PASS

**BOQ impact:** B 15.75 m2 / 2 rolls as V2.5; the pipe collar (P-8) stays withheld with its 0.60 m limit

Diagrams: `diagrams/IX-03_install.svg`, `diagrams/IX-03_cutting.svg`

## IX-04 - L-shaped bathroom 3.00 x 3.00 m less 1.00 x 1.00 m (the audited WP-D)

**Rules:** UP-WP-001 roll 1.00 x 10.00 m; UP-WP-002 lap 0.10 m; UP-WP-003 upturn 0.20 m; UP-WP-DOOR-001 doorway continuation width x (depth + 0.10); UP-WP-LAY-001 rolls -> seams -> membrane; UP-WP-MAT-001 net / installed / procurement apart; UP-WP-004 corners and penetrations by detail; N-11 floor-to-wall junction OPEN (alternatives shown)

**Source drawing (synthetic):** ring [(0.0, 0.0), (3.0, 0.0), (3.0, 2.0), (2.0, 2.0), (2.0, 3.0), (0.0, 3.0)]; doors [D1]

**Geometric interpretation:** one open run of 11.10 m with 5 internal corners and 1 external (the re-entrant corner); the strip crossing the step leaves a 1.00 x 0.80 m rectangle outside the room

**Formula:** as Phase 2B-4 WPD-A1

**Hand derivation:**

1. proven subtotal 8.00 + 11.10 x 0.20 + 0.18 = 10.40 m2; strips ALONG_X S1-S3 3.00 long, S4 0.30 x 2.00
2. S3 crosses the step: its part x 2.00-3.00, y 2.00-2.80 lies outside the room -> a 1.00 x 0.80 m offcut (REUSABLE_SUBJECT_TO_N7), not a 0.27 x 3.00 trim
3. band B1 2.00, B2 1.10, B3 2.80, B4 2.80, B5 2.80: B4 starts on the corner (2, 3) at 5.60 -> a joint at a corner; best order: 0.10 from the corners, 0.20 from the seam ends
4. consumed 13.80 = installed 12.52 + 0.48 true waste + 0.80 reusable; 2 rolls, stock 6.20; seams 3 + 4 = 7
5. continuous fold: not computed (not a rectangle; the external corner needs a gusset detail)

| quantity | expected (hand) | engine | reference | difference | result |
|---|---|---|---|---|---|
| direction | X | X | - | 0 | PASS |
| proven_subtotal_m2 | 10.4 | 10.4 | 10.4 | 0 | PASS |
| consumed_m2 | 13.8 | 13.8 | 13.8 | 0 | PASS |
| installed_m2 | 12.52 | 12.52 | 12.52 | 0 | PASS |
| laps_total_m2 | 2.12 | 2.12 | 2.12 | 0 | PASS |
| laps_side_m2 | 0.8 | 0.8 | 0.8 | 0 | PASS |
| laps_floor_end_m2 | 0 | 0 | 0 | 0 | PASS |
| laps_junction_m2 | 1.11 | 1.11 | 1.11 | 0 | PASS |
| laps_band_end_m2 | 0.12 | 0.12 | 0.12 | 0 | PASS |
| laps_doorway_m2 | 0.09 | 0.09 | 0.09 | 0 | PASS |
| true_waste_m2 | 0.48 | 0.48 | 0.48 | 0 | PASS |
| reusable_m2 | 0.8 | 0.8 | 0.8 | 0 | PASS |
| stock_m2 | 6.2 | 6.2 | 6.2 | 0 | PASS |
| rolls | 2 | 2 | 2 | 0 | PASS |
| floor_seams | 3 | 3 | 3 | 0 | PASS |
| floor_end_laps | 0 | 0 | 0 | 0 | PASS |
| band_joints | 4 | 4 | 4 | 0 | PASS |
| seams | 7 | 7 | 7 | 0 | PASS |
| band_pieces_m | [1.1, 2, 2.8, 2.8, 2.8] | [1.1, 2, 2.8, 2.8, 2.8] | [1.1, 2, 2.8, 2.8, 2.8] | 0 | PASS |
| min_joint_corner_m | 0 | 0 | 0 | 0 | PASS |
| min_joint_seam_end_m | 0.2 | 0.2 | 0.2 | 0 | PASS |
| joints_stacked_on_seam_ends | 0 | 0 | 0 | 0 | PASS |
| jamb_butt_joints | 2 | 2 | 2 | 0 | PASS |
| terminations | 0 | 0 | 0 | 0 | PASS |
| corners_internal | 5 | 5 | 5 | 0 | PASS |
| corners_external | 1 | 1 | 1 | 0 | PASS |
| flange_pleats_m2 | 0.05 | 0.05 | 0.05 | 0 | PASS |
| flange_gaps_m2 | 0.01 | 0.01 | 0.01 | 0 | PASS |
| t_flange_over_seam_end | 6 | 6 | 6 | 0 | PASS |
| t_doorway_lap_over_seam_end | 0 | 0 | 0 | 0 | PASS |
| t_seam_end_at_break | 0 | 0 | 0 | 0 | PASS |
| best_corner_m | 0.1 | 0.1 | 0.1 | 0 | PASS |
| best_seam_end_m | 0.2 | 0.2 | 0.2 | 0 | PASS |
| fold | BLOCKED | BLOCKED | - | 0 | PASS |

**Open details (flags):** expected DRAIN_NOT_SHOWN, FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_AT_CORNER, JOINT_OFFSET_UNVERIFIED, LAY_ORDER_NOT_VALIDATED; engine DRAIN_NOT_SHOWN, FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_AT_CORNER, JOINT_OFFSET_UNVERIFIED, LAY_ORDER_NOT_VALIDATED - PASS

**BOQ impact:** B 12.52 m2 / 2 rolls as V2.5; 0.80 m2 of the 1.28 m2 offcuts is a reusable rectangle (its reuse is N-7): reused for the doorway piece the room needs 13.50 m2 instead of 13.80 m2

Diagrams: `diagrams/IX-04_install.svg`, `diagrams/IX-04_cutting.svg`

## IX-05 - 3.00 x 2.50 m bathroom with a free-standing 0.40 x 0.40 m column, one 0.90 m door

**Rules:** UP-WP-001 roll 1.00 x 10.00 m; UP-WP-002 lap 0.10 m; UP-WP-003 upturn 0.20 m; UP-WP-DOOR-001 doorway continuation width x (depth + 0.10); UP-WP-LAY-001 rolls -> seams -> membrane; UP-WP-MAT-001 net / installed / procurement apart; UP-WP-004 corners and penetrations by detail; N-11 floor-to-wall junction OPEN (alternatives shown)

**Source drawing (synthetic):** ring [(0.0, 0.0), (3.0, 0.0), (3.0, 2.5), (0.0, 2.5)]; doors [D1]; obstruction 1

**Geometric interpretation:** the column is an obstruction: the floor excludes it, its four faces are upturned (a closed 1.60 m loop with 4 EXTERNAL corners seen from the room) the outer run: 10.10 m open from the east jamb of D1 (x 1.20); corners SE 1.80, NE 4.30, NW 7.30, SW 9.80

**Formula:** floor = 3.00 x 2.50 - 0.40 x 0.40; upturn = (11.00 - 0.90 + 1.60) x 0.20; continuation 0.90 x 0.20

**Hand derivation:**

1. floor 7.50 - 0.16 = 7.34; upturn 11.70 x 0.20 = 2.34; continuation 0.18 -> proven subtotal 9.86 m2
2. ALONG_X: strips 3.00 long across 2.50: n = 3 (1.00 + 2 x 0.90 = 2.80), S3 0.70 wide; S1 y 0-1.00, S2 0.90-1.90, S3 1.80-2.50; the column (y 1.00-1.40) lies in S2 only: S2 is one 3.00 m piece with the column footprint cut out (a 0.40 x 0.40 offcut)
3. S3 is cut from a full 3.00 piece: trim 0.30 -> one lane 3.00 (no residue); DW 0.90 from it -> 2.10 left
4. outer run: 2.10 (no lap) covers 2.10, 8.00 left; then the column loop 1.60 (every piece lapped): the shortest segment of 3 lanes that finishes both: two lanes cover 2 (L - 0.10), the third finishes the run and keeps 1.70 for the column: 3L - 8.30 >= 1.70 -> L = 3.34 (3.33 leaves 1.69)
5. 3.34 does not fit roll 1's 1.00 m tail; filling the tail first (1.00 + a 2.44 segment) gives 2 rolls but 7 joints against 4 -> 3.34 is kept
6. band: B1 2.10, B2 3.34, B3 3.34, B4 1.62 (outer run); B5 1.70 (column loop, from the third lane's rest); 0.02 m of that lane is left (0.006 m2)
7. ALONG_Y for comparison: 4 strips 2.50 (10.00 m) + a 2.70 segment = 12.70 m2, 2 rolls, 3 + 5 = 8 seams -> ALONG_X (2 rolls, 2 + 4 = 6 seams) is selected
8. laps: side 2 x 3.00 x 0.10 = 0.60; flange 11.70 x 0.10 = 1.17; band ends 4 x 0.03 = 0.12; doorway 0.09 -> 1.98; installed 9.86 + 1.98 = 11.84
9. consumed 3 x 3.00 + 3.34 = 12.34; offcuts 0.50 = column footprint 0.16 (0.40 x 0.40, REUSABLE_SUBJECT_TO_N7) + segment residue 0.10 x 3.34 = 0.334 + lane rest 0.006 (TRUE_WASTE 0.34); 2 rolls (3.34 + 3.00 + 3.00 | 3.00), stock 0.66 + 7.00 = 7.66 m2
10. outer joints 2.00-2.10, 5.24-5.34, 8.48-8.58: corners 0.20, 0.94, 1.18 -> 0.20; floor seams (y 0.90-1.00, 1.80-1.90) meet the east wall at r 2.70-2.80 / 3.60-3.70 and the west wall at 8.80-8.90 / 7.90-8.00 -> seam distances 0.60, 1.54, 0.22 -> 0.22
11. column loop from (1.30, 1.00): one piece 1.70, its closing joint 1.50-1.60 ends on the corner at the loop start (0.00); the S1/S2 lap (y 0.90-1.00) runs along the column's south face under its flange (a seam along a wall, r 0-0.40): the closing joint touches it -> min joint-to-seam 0.00
12. corners 4 internal + 4 external: flange pleats 0.04, flange gaps at the column 4 x 0.01 = 0.04 m2
13. continuous fold: not computed (an obstruction inside the room)

| quantity | expected (hand) | engine | reference | difference | result |
|---|---|---|---|---|---|
| direction | X | X | - | 0 | PASS |
| proven_subtotal_m2 | 9.86 | 9.86 | 9.86 | 0 | PASS |
| consumed_m2 | 12.34 | 12.34 | 12.34 | 0 | PASS |
| installed_m2 | 11.84 | 11.84 | 11.84 | 0 | PASS |
| laps_total_m2 | 1.98 | 1.98 | 1.98 | 0 | PASS |
| laps_side_m2 | 0.6 | 0.6 | 0.6 | 0 | PASS |
| laps_floor_end_m2 | 0 | 0 | 0 | 0 | PASS |
| laps_junction_m2 | 1.17 | 1.17 | 1.17 | 0 | PASS |
| laps_band_end_m2 | 0.12 | 0.12 | 0.12 | 0 | PASS |
| laps_doorway_m2 | 0.09 | 0.09 | 0.09 | 0 | PASS |
| true_waste_m2 | 0.34 | 0.34 | 0.34 | 0 | PASS |
| reusable_m2 | 0.16 | 0.16 | 0.16 | 0 | PASS |
| stock_m2 | 7.66 | 7.66 | 7.66 | 0 | PASS |
| rolls | 2 | 2 | 2 | 0 | PASS |
| floor_seams | 2 | 2 | 2 | 0 | PASS |
| floor_end_laps | 0 | 0 | 0 | 0 | PASS |
| band_joints | 4 | 4 | 4 | 0 | PASS |
| seams | 6 | 6 | 6 | 0 | PASS |
| band_pieces_m | [1.62, 1.7, 2.1, 3.34, 3.34] | [1.62, 1.7, 2.1, 3.34, 3.34] | [1.62, 1.7, 2.1, 3.34, 3.34] | 0 | PASS |
| min_joint_corner_m | 0 | 0 | 0 | 0 | PASS |
| min_joint_seam_end_m | 0 | 0 | 0 | 0 | PASS |
| joints_stacked_on_seam_ends | 0 | 0 | 0 | 0 | PASS |
| jamb_butt_joints | 2 | 2 | 2 | 0 | PASS |
| terminations | 0 | 0 | 0 | 0 | PASS |
| corners_internal | 4 | 4 | 4 | 0 | PASS |
| corners_external | 4 | 4 | 4 | 0 | PASS |
| flange_pleats_m2 | 0.04 | 0.04 | 0.04 | 0 | PASS |
| flange_gaps_m2 | 0.04 | 0.04 | 0.04 | 0 | PASS |
| t_flange_over_seam_end | 4 | 4 | 4 | 0 | PASS |
| t_doorway_lap_over_seam_end | 0 | 0 | 0 | 0 | PASS |
| t_seam_end_at_break | 0 | 0 | 0 | 0 | PASS |
| seams_along_walls | 1 | 1 | 1 | 0 | PASS |
| run_min_joint_corner_m | [0.2, 0] | [0.2, 0] | [0.2, 0] | 0 | PASS |
| run_min_joint_seam_end_m | [0.22, 0] | [0.22, 0] | [0.22, 0] | 0 | PASS |
| fold | BLOCKED | BLOCKED | - | 0 | PASS |

**Open details (flags):** expected DRAIN_NOT_SHOWN, FLOOR_SEAM_ALONG_A_WALL, FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_AT_CORNER, JOINT_OFFSET_UNVERIFIED, JOINT_TOUCHES_SEAM_END, LAY_ORDER_NOT_VALIDATED; engine DRAIN_NOT_SHOWN, FLOOR_SEAM_ALONG_A_WALL, FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_AT_CORNER, JOINT_OFFSET_UNVERIFIED, JOINT_TOUCHES_SEAM_END, LAY_ORDER_NOT_VALIDATED - PASS

**BOQ impact:** B 11.84 m2 / 2 rolls; the column adds 1.60 m of upturn (0.32 m2) and 4 external corners whose flange gaps (0.04 m2) need the corner detail; the column footprint is a reusable 0.40 x 0.40 offcut

Diagrams: `diagrams/IX-05_install.svg`, `diagrams/IX-05_cutting.svg`

## IX-06 - 4.00 x 3.00 m kitchen: a 0.90 m door to the dry dining, a 0.80 m service doorway to a waterproofed laundry, a floor drain

**Rules:** UP-WP-001 roll 1.00 x 10.00 m; UP-WP-002 lap 0.10 m; UP-WP-003 upturn 0.20 m; UP-WP-DOOR-001 doorway continuation width x (depth + 0.10); UP-WP-LAY-001 rolls -> seams -> membrane; UP-WP-MAT-001 net / installed / procurement apart; UP-WP-004 corners and penetrations by detail; N-11 floor-to-wall junction OPEN (alternatives shown)

**Source drawing (synthetic):** ring [(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)]; doors [D1, D2]; drains [FD1]

**Geometric interpretation:** D2 leads to a waterproofed laundry: the membrane runs through (DOORWAY_CONTINUATION, resolved by geometry); D1 to a dry room: its threshold transition is UNRESOLVED two open runs: 6.70 m from D2 (east jamb, y 1.30) over the north wall to D1 (y 2.00), corners NE 1.70 and NW 5.70; 5.60 m from D1 (y 1.10) over the south wall to D2 (y 0.50), corners SW 1.10 and SE 5.10 the drain FD1 is drawn at (1.40, 2.20)

**Formula:** floor 4.00 x 3.00; upturn (14.00 - 0.90 - 0.80) x 0.20; continuation (0.90 + 0.80) x 0.20

**Hand derivation:**

1. floor 12.00 + upturn 12.30 x 0.20 = 2.46 + continuation 0.34 -> proven subtotal 14.80 m2
2. ALONG_Y: strips 3.00 long across 4.00: n = 5 (1.00 + 4 x 0.90 = 4.60), S5 0.40 wide; trim 0.60 -> lanes L1 L2 3.00 (no residue)
3. DW-D1 0.90 from L1 (2.10 left); DW-D2 0.80 from the shortest lane that fits (L1's 2.10) -> 1.30 left
4. run 1 (6.70): L2 3.00 covers 3.00; L1's 1.30 covers 1.20; 2.50 left; a new segment for 2.50 (lapped) + run 2 5.60: the first lane gives 2.60 to run 1, then 3L - 2.80 >= 5.60 -> L = 2.80 (2.79 gives 5.57)
5. 2.80 fits roll 2's 4.00 m tail; band: run 1 B1 3.00, B2 1.30, B3 2.60; run 2 B4 2.80, B5 2.80, B6 0.20
6. ALONG_X for comparison: 4 strips 4.00 + a 2.00 roll tail + a 0.50 segment = 18.50 m2, 2 rolls, 3 + 5 = 8 seams; ALONG_Y 17.80 m2, 2 rolls, 4 + 4 = 8 seams -> ALONG_Y (less membrane at equal rolls and seams)
7. laps: side 4 x 3.00 x 0.10 = 1.20; flange 12.30 x 0.10 = 1.23; band ends 4 x 0.03 = 0.12; doorways (0.90 + 0.80) x 0.10 = 0.17 -> 2.72; installed 17.52
8. consumed 5 x 3.00 + 2.80 = 17.80 = 17.52 + 0.28 true waste (0.10 x 2.80); 2 rolls (3 x 3.00 | 2 x 3.00 + 2.80), stock 1.00 + 1.20 = 2.20 m2; seams 8
9. run 1 joints 2.90-3.00, 4.10-4.20: corners 1.20, 1.50; the floor seams (x 0.90-1.00 ... 3.60-3.70) meet the north wall at r 4.70-4.80, 3.80-3.90, 2.90-3.00, 2.00-2.10: the joint 2.90-3.00 lies on the S3/S4 seam end (stacked)
10. run 2 joints 2.70-2.80, 5.40-5.50: corners 1.60, 0.30 -> min 0.30; seam ends on the south wall r 2.00-2.10, 2.90-3.00, 3.80-3.90, 4.70-4.80 -> 0.10, 0.60
11. 8 seam ends under the flange, none in a doorway; 4 butt joints at the jambs (D1, D2); B6 is a 0.20 m piece (0.10 past its lap): its acceptability is P-9
12. drain FD1 at x 1.40: 0.40 from the S1/S2 and S2/S3 laps, 0.70 from the north flange -> a centred collar up to 0.80 m; lay order from the drain strip S2: S2, S1, S3, S4, S5
13. continuous fold: developed 4.40 x 3.40 = WP-B's: 17.60 m2, 2 rolls, 3 seams, installed 16.28
14. junction flange: ALONG_X keeps 2 rolls while the 0.70 m trim of S4 holds two band lanes (b = 0.20 + j <= 0.35, j <= 0.15: lanes 4.00 + 4.00 less the doorway pieces leave a band need that fits the two 2.00 m roll tails); from j = 0.16 the trim holds one lane and either direction needs at least 15.00 (or 16.00) m of floor + 5.50 m of segments > 20.00 m -> 3 rolls

| quantity | expected (hand) | engine | reference | difference | result |
|---|---|---|---|---|---|
| direction | Y | Y | - | 0 | PASS |
| proven_subtotal_m2 | 14.8 | 14.8 | 14.8 | 0 | PASS |
| consumed_m2 | 17.8 | 17.8 | 17.8 | 0 | PASS |
| installed_m2 | 17.52 | 17.52 | 17.52 | 0 | PASS |
| laps_total_m2 | 2.72 | 2.72 | 2.72 | 0 | PASS |
| laps_side_m2 | 1.2 | 1.2 | 1.2 | 0 | PASS |
| laps_floor_end_m2 | 0 | 0 | 0 | 0 | PASS |
| laps_junction_m2 | 1.23 | 1.23 | 1.23 | 0 | PASS |
| laps_band_end_m2 | 0.12 | 0.12 | 0.12 | 0 | PASS |
| laps_doorway_m2 | 0.17 | 0.17 | 0.17 | 0 | PASS |
| true_waste_m2 | 0.28 | 0.28 | 0.28 | 0 | PASS |
| reusable_m2 | 0 | 0 | 0 | 0 | PASS |
| stock_m2 | 2.2 | 2.2 | 2.2 | 0 | PASS |
| rolls | 2 | 2 | 2 | 0 | PASS |
| floor_seams | 4 | 4 | 4 | 0 | PASS |
| floor_end_laps | 0 | 0 | 0 | 0 | PASS |
| band_joints | 4 | 4 | 4 | 0 | PASS |
| seams | 8 | 8 | 8 | 0 | PASS |
| band_pieces_m | [0.2, 1.3, 2.6, 2.8, 2.8, 3] | [0.2, 1.3, 2.6, 2.8, 2.8, 3] | [0.2, 1.3, 2.6, 2.8, 2.8, 3] | 0 | PASS |
| min_joint_corner_m | 0.3 | 0.3 | 0.3 | 0 | PASS |
| min_joint_seam_end_m | 0 | 0 | 0 | 0 | PASS |
| joints_stacked_on_seam_ends | 1 | 1 | 1 | 0 | PASS |
| jamb_butt_joints | 4 | 4 | 4 | 0 | PASS |
| terminations | 0 | 0 | 0 | 0 | PASS |
| corners_internal | 4 | 4 | 4 | 0 | PASS |
| corners_external | 0 | 0 | 0 | 0 | PASS |
| flange_pleats_m2 | 0.04 | 0.04 | 0.04 | 0 | PASS |
| flange_gaps_m2 | 0 | 0 | 0 | 0 | PASS |
| t_flange_over_seam_end | 8 | 8 | 8 | 0 | PASS |
| t_doorway_lap_over_seam_end | 0 | 0 | 0 | 0 | PASS |
| t_seam_end_at_break | 0 | 0 | 0 | 0 | PASS |
| drain_FD1_clear_m | 0.4 | 0.4 | 0.4 | 0 | PASS |
| drain_FD1_on_seam | False | False | False | 0 | PASS |
| lay_order | [2, 1, 3, 4, 5] | [2, 1, 3, 4, 5] | [2, 1, 3, 4, 5] | 0 | PASS |
| shortest_band_piece_m | 0.2 | 0.2 | - | 0 | PASS |
| junction_rolls | [2, 3] | [2, 3] | - | 0 | PASS |
| junction_roll_change_flange_m | 0.16 | 0.16 | - | 0 | PASS |
| fold | rolls 2; consumed_m2 17.6; installed_m2 16.28; laps_m2 1.32; corner_excess_m2 0.16; seams 3 | rolls 2; consumed_m2 17.6; installed_m2 16.28; laps_m2 1.32; corner_excess_m2 0.16; seams 3 | - | 0 | PASS |

**Open details (flags):** expected FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_OFFSET_UNVERIFIED, JOINT_ON_SEAM_END, JUNCTION_CHANGES_ROLL_COUNT; engine FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_OFFSET_UNVERIFIED, JOINT_ON_SEAM_END, JUNCTION_CHANGES_ROLL_COUNT - PASS

**BOQ impact:** B 17.52 m2 / 2 rolls; the service doorway carries no threshold transition (continuation), the dining door does (withheld); the drawn drain fixes the lay order

Diagrams: `diagrams/IX-06_install.svg`, `diagrams/IX-06_cutting.svg`

## IX-07 - 4.00 x 1.50 m balcony: a 1.80 m door, the front edge open (railing)

**Rules:** UP-WP-001 roll 1.00 x 10.00 m; UP-WP-002 lap 0.10 m; UP-WP-003 upturn 0.20 m; UP-WP-DOOR-001 doorway continuation width x (depth + 0.10); UP-WP-LAY-001 rolls -> seams -> membrane; UP-WP-MAT-001 net / installed / procurement apart; UP-WP-004 corners and penetrations by detail; N-11 floor-to-wall junction OPEN (alternatives shown)

**Source drawing (synthetic):** ring [(0.0, 0.0), (4.0, 0.0), (4.0, 1.5), (0.0, 1.5)]; doors [D1]; open edges [E1]

**Geometric interpretation:** the front edge (y = 0) has no wall: no upturn, the membrane edge needs a termination detail (4.00 m) two open runs of 2.60 m: from the open edge up the east wall (corner NE 1.50) to the door; from the door over the north wall (corner NW 1.10) down the west wall to the open edge the corners at the open edge are upturn ends, not corners no drain drawn

**Formula:** floor 4.00 x 1.50; upturn (11.00 - 4.00 - 1.80) x 0.20; continuation 1.80 x 0.20

**Hand derivation:**

1. floor 6.00 + upturn 5.20 x 0.20 = 1.04 + continuation 0.36 -> proven subtotal 7.40 m2
2. ALONG_X: strips 4.00 across 1.50: n = 2, S2 0.60 wide; trim 0.40 -> 1 lane 4.00 + 0.10 x 4.00 residue
3. DW 1.80 from the lane -> 2.20 left; run 1 (2.60): 2.20 covers 2.20, 0.40 left; then run 2 (2.60): a segment whose first lane finishes run 1 (0.50 used) and whose lanes cover run 2: 3L - 0.70 >= 2.60 -> L = 1.10 (1.09 gives 2.57); it fits the 2.00 m roll tail
4. band: run 1 B1 2.20, B2 0.50; run 2 B3 1.10, B4 1.10, B5 0.60
5. ALONG_Y for comparison: 5 strips 1.50 + a 1.80 doorway segment = 9.30 m2, 1 roll, 4 + 2 = 6 seams -> ALONG_X (1 roll, 1 + 3 = 4 seams)
6. laps: side 4.00 x 0.10 = 0.40; flange 5.20 x 0.10 = 0.52; band ends 3 x 0.03 = 0.09; doorway 1.80 x 0.10 = 0.18 -> 1.19; installed 8.59
7. consumed 2 x 4.00 + 1.10 = 9.10 = 8.59 + 0.51 true waste (0.40 + 0.11); 1 roll, stock 0.90 m2; seams 4
8. run 1 joint 2.10-2.20: 0.60 from the corner NE (1.50), 1.10 from the seam end (east wall, r 0.90-1.00)
9. run 2 joints 1.00-1.10 and 2.00-2.10: the first ends on the corner NW (1.10) -> 0.00; seam end on the west wall at r 1.60-1.70 -> 0.50 and 0.30
10. 2 corners (both internal); 2 seam ends under the flange; 2 butt joints (D1) and 2 terminations at the open edge (the band ends there); the open edge itself: 4.00 m of termination
11. continuous fold: not computed (the open edge has no wall to fold onto)

| quantity | expected (hand) | engine | reference | difference | result |
|---|---|---|---|---|---|
| direction | X | X | - | 0 | PASS |
| proven_subtotal_m2 | 7.4 | 7.4 | 7.4 | 0 | PASS |
| consumed_m2 | 9.1 | 9.1 | 9.1 | 0 | PASS |
| installed_m2 | 8.59 | 8.59 | 8.59 | 0 | PASS |
| laps_total_m2 | 1.19 | 1.19 | 1.19 | 0 | PASS |
| laps_side_m2 | 0.4 | 0.4 | 0.4 | 0 | PASS |
| laps_floor_end_m2 | 0 | 0 | 0 | 0 | PASS |
| laps_junction_m2 | 0.52 | 0.52 | 0.52 | 0 | PASS |
| laps_band_end_m2 | 0.09 | 0.09 | 0.09 | 0 | PASS |
| laps_doorway_m2 | 0.18 | 0.18 | 0.18 | 0 | PASS |
| true_waste_m2 | 0.51 | 0.51 | 0.51 | 0 | PASS |
| reusable_m2 | 0 | 0 | 0 | 0 | PASS |
| stock_m2 | 0.9 | 0.9 | 0.9 | 0 | PASS |
| rolls | 1 | 1 | 1 | 0 | PASS |
| floor_seams | 1 | 1 | 1 | 0 | PASS |
| floor_end_laps | 0 | 0 | 0 | 0 | PASS |
| band_joints | 3 | 3 | 3 | 0 | PASS |
| seams | 4 | 4 | 4 | 0 | PASS |
| band_pieces_m | [0.5, 0.6, 1.1, 1.1, 2.2] | [0.5, 0.6, 1.1, 1.1, 2.2] | [0.5, 0.6, 1.1, 1.1, 2.2] | 0 | PASS |
| min_joint_corner_m | 0 | 0 | 0 | 0 | PASS |
| min_joint_seam_end_m | 0.3 | 0.3 | 0.3 | 0 | PASS |
| joints_stacked_on_seam_ends | 0 | 0 | 0 | 0 | PASS |
| jamb_butt_joints | 2 | 2 | 2 | 0 | PASS |
| terminations | 2 | 2 | 2 | 0 | PASS |
| corners_internal | 2 | 2 | 2 | 0 | PASS |
| corners_external | 0 | 0 | 0 | 0 | PASS |
| flange_pleats_m2 | 0.02 | 0.02 | 0.02 | 0 | PASS |
| flange_gaps_m2 | 0 | 0 | 0 | 0 | PASS |
| t_flange_over_seam_end | 2 | 2 | 2 | 0 | PASS |
| t_doorway_lap_over_seam_end | 0 | 0 | 0 | 0 | PASS |
| t_seam_end_at_break | 0 | 0 | 0 | 0 | PASS |
| fold | BLOCKED | BLOCKED | - | 0 | PASS |

**Open details (flags):** expected DRAIN_NOT_SHOWN, FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_AT_CORNER, JOINT_OFFSET_UNVERIFIED, LAY_ORDER_NOT_VALIDATED; engine DRAIN_NOT_SHOWN, FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_AT_CORNER, JOINT_OFFSET_UNVERIFIED, LAY_ORDER_NOT_VALIDATED - PASS

**BOQ impact:** B 8.59 m2 / 1 roll (exterior system); the 4.00 m open-edge termination and the door threshold stay withheld; a balcony without a drawn drain is NOT_SHOWN, never zero

Diagrams: `diagrams/IX-07_install.svg`, `diagrams/IX-07_cutting.svg`

## IX-08 - 12.00 x 6.00 m roof: parapets, an access door, a 2.00 m open edge, two roof drains

**Rules:** UP-WP-001 roll 1.00 x 10.00 m; UP-WP-002 lap 0.10 m; UP-WP-003 upturn 0.20 m; UP-WP-DOOR-001 doorway continuation width x (depth + 0.10); UP-WP-LAY-001 rolls -> seams -> membrane; UP-WP-MAT-001 net / installed / procurement apart; UP-WP-004 corners and penetrations by detail; N-11 floor-to-wall junction OPEN (alternatives shown)

**Source drawing (synthetic):** ring [(0.0, 0.0), (12.0, 0.0), (12.0, 6.0), (0.0, 6.0)]; doors [D1]; open edges [E1]; drains [RD1, RD2]

**Geometric interpretation:** parapet walls carry the upturn; the open edge E1 (east, y 2.00-4.00) and the door D1 (north, x 5.00-6.00) break it into runs of 8.00 m and 25.00 m the strips are 12.00 m long - longer than a roll - so each is spliced 10.00 + 2.10

**Formula:** as the Phase 2B-3 proof case WP-F; spliced strips laid with end laps

**Hand derivation:**

1. proven subtotal 72.00 + 6.60 + 0.20 = 78.80 m2; 7 strips ALONG_X, each spliced at x 9.90-10.00
2. consumed 92.14 = installed 90.18 + 1.96 true waste; 10 rolls, stock 7.86 m2; seams 6 + 7 + 4 = 17
3. laps: side 7.20; end 0.66; flange 3.30; band ends 0.12; doorway 0.10 -> 11.38
4. run 1 (8.00): one piece; run 2 (25.00): B 2.00, 1.10, 7.44, 7.44, 7.42: joints 1.90-2.00, 2.90-3.00, 10.24-10.34, 17.58-17.68: corners 3.00, 2.00, 0.66, 5.32 -> 0.66; the west-wall seam end at 10.00-10.10 is 0.14 from the third joint
5. 12 seam ends under the flange (10 side laps on the east and west parapets, 2 end laps on the south and north); 2 side laps end at the open edge
6. every strip is spliced at the same place: the end laps of neighbouring strips are not staggered (0.00) - 12 four-layer crossings
7. both drains (y 1.00) sit on the S1/S2 lap (y 0.90-1.00); RD2 also on the splice line: 0.00 clear
8. two drains: the catchments are not drawn, no lay order is derived; continuous fold: not computed (open edge)

| quantity | expected (hand) | engine | reference | difference | result |
|---|---|---|---|---|---|
| direction | X | X | - | 0 | PASS |
| proven_subtotal_m2 | 78.8 | 78.8 | 78.8 | 0 | PASS |
| consumed_m2 | 92.14 | 92.14 | 92.14 | 0 | PASS |
| installed_m2 | 90.18 | 90.18 | 90.18 | 0 | PASS |
| laps_total_m2 | 11.38 | 11.38 | 11.38 | 0 | PASS |
| laps_side_m2 | 7.2 | 7.2 | 7.2 | 0 | PASS |
| laps_floor_end_m2 | 0.66 | 0.66 | 0.66 | 0 | PASS |
| laps_junction_m2 | 3.3 | 3.3 | 3.3 | 0 | PASS |
| laps_band_end_m2 | 0.12 | 0.12 | 0.12 | 0 | PASS |
| laps_doorway_m2 | 0.1 | 0.1 | 0.1 | 0 | PASS |
| true_waste_m2 | 1.96 | 1.96 | 1.96 | 0 | PASS |
| reusable_m2 | 0 | 0 | 0 | 0 | PASS |
| stock_m2 | 7.86 | 7.86 | 7.86 | 0 | PASS |
| rolls | 10 | 10 | 10 | 0 | PASS |
| floor_seams | 6 | 6 | 6 | 0 | PASS |
| floor_end_laps | 7 | 7 | 7 | 0 | PASS |
| band_joints | 4 | 4 | 4 | 0 | PASS |
| seams | 17 | 17 | 17 | 0 | PASS |
| band_pieces_m | [1.1, 2, 7.42, 7.44, 7.44, 8] | [1.1, 2, 7.42, 7.44, 7.44, 8] | [1.1, 2, 7.42, 7.44, 7.44, 8] | 0 | PASS |
| min_joint_corner_m | 0.66 | 0.66 | 0.66 | 0 | PASS |
| min_joint_seam_end_m | 0.14 | 0.14 | 0.14 | 0 | PASS |
| joints_stacked_on_seam_ends | 0 | 0 | 0 | 0 | PASS |
| jamb_butt_joints | 2 | 2 | 2 | 0 | PASS |
| terminations | 2 | 2 | 2 | 0 | PASS |
| corners_internal | 4 | 4 | 4 | 0 | PASS |
| corners_external | 0 | 0 | 0 | 0 | PASS |
| flange_pleats_m2 | 0.04 | 0.04 | 0.04 | 0 | PASS |
| flange_gaps_m2 | 0 | 0 | 0 | 0 | PASS |
| t_flange_over_seam_end | 12 | 12 | 12 | 0 | PASS |
| t_doorway_lap_over_seam_end | 0 | 0 | 0 | 0 | PASS |
| t_seam_end_at_break | 2 | 2 | 2 | 0 | PASS |
| min_end_lap_stagger_m | 0 | 0 | 0 | 0 | PASS |
| drain_RD1_clear_m | 0 | 0 | 0 | 0 | PASS |
| drain_RD1_on_seam | True | True | True | 0 | PASS |
| drain_RD2_clear_m | 0 | 0 | 0 | 0 | PASS |
| drain_RD2_on_seam | True | True | True | 0 | PASS |
| fold | BLOCKED | BLOCKED | - | 0 | PASS |

**Open details (flags):** expected DRAIN_ON_A_FLOOR_SEAM, END_LAPS_NOT_STAGGERED, FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_OFFSET_UNVERIFIED, LAY_ORDER_NOT_VALIDATED; engine DRAIN_ON_A_FLOOR_SEAM, END_LAPS_NOT_STAGGERED, FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_OFFSET_UNVERIFIED, LAY_ORDER_NOT_VALIDATED - PASS

**BOQ impact:** B 90.18 m2 / 10 rolls as V2.5; two installation defects of the plan are now visible (drains on a lap, end laps in one line) - correcting them is a lay-out change with a possible material effect (staggering the splices of a 12 m strip needs another cut pattern)

Diagrams: `diagrams/IX-08_install.svg`, `diagrams/IX-08_cutting.svg`

## IX-09 - Shared roll inventory: the 4 x 3 m bathroom, a 1.50 x 1.20 m WC and the 2 x 2 m bathroom on one floor, one membrane system

**Rules:** UP-WP-001 roll 1.00 x 10.00 m; UP-WP-002 lap 0.10 m; UP-WP-003 upturn 0.20 m; UP-WP-DOOR-001 doorway continuation width x (depth + 0.10); UP-WP-LAY-001 rolls -> seams -> membrane; UP-WP-MAT-001 net / installed / procurement apart; UP-WP-004 corners and penetrations by detail; N-11 floor-to-wall junction OPEN (alternatives shown); UP-WP-MAT-001 C: whole rolls of the cutting plan per membrane system

**Interpretation:** only full-width cuts are shared between areas (a roll remainder cut to a piece's length); band lanes, trims and offcuts stay with their area

**Formula:** fewest whole rolls for the multiset of cut lengths (exact packing)

**Hand derivation:**

1. cuts: bathroom 3.00 x 5 + 2.80; WC 1.20 + 1.20 + 1.50 (Phase 2B-3 WP-W); 2 x 2 bathroom 2.00 x 3 + 1.50
2. each alone: 2 + 1 + 1 = 4 rolls
3. together 15.00 + 2.80 + 3.90 + 7.50 = 29.20 m -> at least 3 rolls; 3 is reached: 3.00 + 3.00 + 2.00 + 2.00 = 10.00; 3.00 + 3.00 + 2.80 + 1.20 = 10.00; 3.00 + 2.00 + 1.50 + 1.50 + 1.20 = 9.20
4. gross 30.00 m2 = consumed 29.20 + untouched 0.80; one roll saved by sharing, none carried between floors

| quantity | expected (hand) | engine | difference | result |
|---|---|---|---|---|
| rolls_alone | 4 | 4 | 0 | PASS |
| rolls_shared | 3 | 3 | 0 | PASS |
| consumed_m2 | 29.2 | 29.2 | 0 | PASS |
| gross_m2 | 30 | 30 | 0 | PASS |
| untouched_m2 | 0.8 | 0.8 | 0 | PASS |
| pieces | 13 | 13 | 0 | PASS |

**BOQ impact:** procurement C: 3 rolls instead of 4 (the BOQ quantities A and B are unchanged)

## IX-10 - Two separate membrane systems: the 4 x 3 m bathroom (wet-area system) and a 4.00 x 1.50 m balcony (exterior system)

**Rules:** UP-WP-001 roll 1.00 x 10.00 m; UP-WP-002 lap 0.10 m; UP-WP-003 upturn 0.20 m; UP-WP-DOOR-001 doorway continuation width x (depth + 0.10); UP-WP-LAY-001 rolls -> seams -> membrane; UP-WP-MAT-001 net / installed / procurement apart; UP-WP-004 corners and penetrations by detail; N-11 floor-to-wall junction OPEN (alternatives shown); UP-WP-MAT-001: never a roll or a total across membrane systems

**Interpretation:** different systems never share a roll, even where a remainder would fit

**Formula:** fewest whole rolls per system

**Hand derivation:**

1. bathroom cuts 3.00 x 5 + 2.80 = 17.80 -> 2 rolls; balcony (Phase 2B-3 WP-G) 4.00 + 4.00 + 2.44 = 10.44 -> 2 rolls; 4 rolls in all
2. if the systems were mixed, 28.24 m would fit 3 rolls (4.00 + 3.00 + 3.00; 4.00 + 3.00 + 2.80; 3.00 + 3.00 + 2.44) - the system boundary costs one roll and is kept

| quantity | expected (hand) | engine | difference | result |
|---|---|---|---|---|
| systems | 2 | 2 | 0 | PASS |
| rolls_by_scope | WET 2; EXTERIOR 2 | EXTERIOR 2; WET 2 | 0 | PASS |
| rolls_total | 4 | 4 | 0 | PASS |
| rolls_if_mixed | 3 | 3 | 0 | PASS |

**BOQ impact:** procurement C per system: 2 + 2 rolls, never 3 combined; no total across systems

