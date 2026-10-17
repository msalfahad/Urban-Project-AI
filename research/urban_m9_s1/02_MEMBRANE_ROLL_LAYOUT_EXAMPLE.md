# 02 Membrane roll layout - synthetic 3.00 x 2.00 m bathroom

Engine: `engine/source/membrane_layout.py` (MEMBRANE_RECT_EXACT_V1, rectangle exact). Rebuilt by `build_examples.py`.

## Inputs

| Parameter | Value | Source |
|---|---|---|
| room | 3.00 x 2.00 m (synthetic) | owner S1 example |
| door | 0.80 m wide in a 0.20 m wall | test parameter |
| roll | 1.00 x 10.00 m (10 m2) | MEM-URBAN-DEFAULT-1x10, owner default (UP-WP-005) |
| side / end lap | 0.10 / 0.10 m minimum | owner minimum (a stricter data sheet would win) |
| upturn | 0.2 m on the full boundary, doorway included | UP-WP-002 v2.0.0 |
| doorway detail | NOT_ESTABLISHED: both rows kept and flagged | UP-WP-003 v1.1.0, Q-WP-1 open |
| upturn band | 0.20 m + 0.10 m lap onto the floor = 0.30 m, cut as 3 lanes across the roll | S1 method |
| strip direction | both tried; fewer rolls, then less material, wins | S1 method |
| minimum reusable offcut | 0.30 m on both sides | test parameter |
| corners / penetrations | counted, not quantified (system not named) | UP-WP-005 note |

## Net surfaces (the BOQ lines)

| Item | Net m2 | Formula |
|---|---|---|
| FIN.WP.FLOOR | 6.000 | length x width (inside the finished wall line) |
| FIN.WP.DOORWAY D-01 | 0.160 | door width x wall depth |
| FIN.WP.UPTURN | 2.000 | full perimeter incl. doorway segments x upturn height (no door deduction) |

Net installed 8.160 m2. The doorway piece lies in the wall thickness, outside the floor polygon, so it is never inside the floor area; whether the doorway 0.20 m is a separate return or sits inside the doorway piece is the open detail (flags DOORWAY_UPTURN_DETAIL_REQUIRED, DOORWAY_DOUBLE_COVERAGE_REVIEW). With the detail UPTURN_WITHIN_DOORWAY_PIECE the doorway segment is billed once and the net reads 8.000 m2.

## Roll plan

Direction ALONG_Y: 4 floor strips of 2 m across 3 m (each further strip adds 0.90 m; the last one trimmed to 0.3 m); upturn band 0.3 m in 5 pieces [2.0, 1.2, 2.54, 2.54, 2.22].

| Seam | Count | Lap m | Running lm |
|---|---|---|---|
| longitudinal | 3 | 0.1 | 6.000 |
| transverse_floor | 0 | 0.1 | 0.000 |
| upturn_end_laps | 5 | 0.1 | 1.500 |
| upturn_to_floor_lap | - | 0.1 | 10.000 |
| doorway_to_floor_lap | - | 0.1 | 0.800 |

| Roll | Segments (m) | Cut m | Untouched tail m |
|---|---|---|---|
| 1 | 2 floor strip 1; 2 floor strip 2; 2 floor strip 3; 2 floor strip 4 | 8.000 | 2.000 |
| 2 | 2.54 upturn lanes | 2.540 | 7.460 |

Alternatives tried: ALONG_X 2 rolls, consumed 10.870 m2, cutting waste 0.787 m2; ALONG_Y 2 rolls, consumed 10.540 m2, cutting waste 0.454 m2.

## Material balance

| Component | m2 |
|---|---|
| net installed | 8.160 |
| overlap (laps) | 1.830 |
| cutting waste | 0.454 |
| reusable offcuts retained | 0.096 |
| packaging surplus (untouched roll tails) | 9.460 |
| = 2 rolls x 10 m2 | 20.000 |

Cutting waste 5.56 % of the net installed area (owner definition). Overlap, cutting waste, offcuts and surplus are separate rows; none of them enters the BOQ net.

## What the forbidden shortcuts would have said (reference only)

| Shortcut | Rolls | Why it is wrong here |
|---|---|---|
| net / 10 m2 | 1 | ignores laps, trims and the band lanes |
| net + 10 % | 1 | a flat rate, not the cutting plan |
| roll plan (S1) | 2 | strips, laps, band lanes and whole rolls |

## M9A fixture WP-1 (2.30 x 3.20 m, door 0.90 m) on the same roll

Strips along 3.20 m: 3 (covering 2.80 m), floor strip material 9.600 m2 against 7.360 m2 net; net installed 9.740 m2; 2 rolls; overlap 1.950 m2; cutting waste 0.954 m2.
