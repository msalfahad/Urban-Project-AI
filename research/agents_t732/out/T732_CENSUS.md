# T-732 census: STR.FORMWORK lines whose concrete member moved, ARCH_TAKEOFF_V3.0.73 vs the T-714 basis

Research only: nothing wired, released or VERIFIED; figures beside, never summed into a released total.

| line | column | member before -> after (m3) | shaft h lo / D | faces | T-714 | T-732 formwork m2 |
|---|---|---|---|---|---|---|
| L-5c555f96 | 41E COL-2F-56 | 0.303 .. 0.425 -> 0.326700 .. 0.425000 | 2.067000 / 0.40..1.2 | SHAFT REDERIVED 2.893800..5.390000; 5.2F-034.JOINT_HELD_M2 CAP_ONLY 0.000000..0.047900; -311.2F-034.JOINT_FACE AT_D_MIN 0.000000..0.192211 | BLANK_NAMED | BOUNDED 2.893800 .. 5.630111 |
| L-7f7fa7a8 | 424 COL-2F-52 | None .. None -> 0.328700 .. None | 2.067000 / 0.40..1.20 | SHAFT REDERIVED 2.893800..None; 5.2F-018.JOINT_HELD_M2 CAP_ONLY 0.000000..0.207566; 7.2F-018.JOINT_HELD_M2 CAP_ONLY 0.000000..0.520000; -311.2F-018.JOINT_FACE DEPENDENT 0.000000..None | BLANK_NAMED | AT_LEAST >= 2.893800 |
| L-8029c283 | 41B COL-2F-54 | 0.303 .. 0.425 -> 0.328700 .. 0.425000 | 2.867000 / 0.40..0.40 | SHAFT REDERIVED 4.013800..5.390000; R4-309.COL-2F-54 INDEPENDENT 0.192200..0.192200 | BLANK_NAMED | BOUNDED 4.206000 .. 5.582200 |
| L-8c96ce0b | 40F COL-2F-50 | None .. None -> 0.328700 .. None | 2.087000 / 0.40..1.20 | SHAFT REDERIVED 2.921800..None; 6.2F-000.JOINT_HELD_M2 CAP_ONLY 0.000000..0.509955; -311.2F-000.JOINT_FACE DEPENDENT 0.000000..None; 4-312.2F-000.EDGE_BAND DEPENDENT 0.000000..None | BLANK_NAMED | AT_LEAST >= 2.921800 |
| L-f2f2781a | 421 COL-2F-53 | 0.303 .. 0.425 -> 0.328700 .. 0.425000 | 2.867000 / 0.40..0.40 | SHAFT REDERIVED 4.013800..5.390000; R4-309.COL-2F-53 INDEPENDENT 0.138200..0.138200 | BLANK_NAMED | BOUNDED 4.152000 .. 5.528200 |
| L-fa037ca1 | 418 COL-2F-55 | 0.4242 .. 0.595 -> 0.457380 .. 0.595000 | 2.067000 / 0.40..1.2 | SHAFT REDERIVED 3.720600..6.930000; 5.2F-037.JOINT_HELD_M2 CAP_ONLY 0.000000..0.047900; -311.2F-037.JOINT_FACE AT_D_MIN 0.000000..0.240222 | BLANK_NAMED | BOUNDED 3.720600 .. 7.218122 |
| L-fcb1852c | 778 COL-2F-59 | 0.1824 .. 0.35 -> 0.201360 .. 0.350000 | 2.517000 / 0.75..0.75 | SHAFT REDERIVED 3.020400..4.900000; -311.2F-041.JOINT_FACE DEPENDENT 0.000000..None; 4-312.2F-041.EDGE_BAND DEPENDENT 0.000000..None | BLANK_NAMED | AT_LEAST >= 3.020400 |

Census (R-T732-2): 7 formwork lines with a moved member; 7 restated, 0 not.

| family | T-714 | after T-724 + T-732 |
|---|---|---|
| BOUNDED | 26: 87.941284 .. 103.192739 | 30: 102.914777 .. 127.151372 |
| AT_LEAST | 32: >= 98.543697 | 35: >= 107.379697 |
| BLANK_NAMED | 258 | 251 |
| FIX_ROW | 54 | 54 |

## T-724 strip children (NAMED blank; per-unit beside)

| piece | soffit m2 | edge m2 per m depth |
|---|---|---|
| GF-STRIP-AT-COL | 0.16 | 0.8 |
| GF-NW-CORNER | 0.029309 | 0.304315 |
| 1F-STRIP-AT-COL | 0.16 | 0.8 |
| 1F-NW-CORNER | 0.029309 | 0.304315 |

## Touched members whose formwork does not move

| line | member | class | why |
|---|---|---|---|
| L-40a1126c | L-fb7a6431 | BLANK_NAMED | member stays capped blank 0 .. 3.5256 (R-T724-3): no floor; faces OQ-10 |
| L-6d72f51d | L-684fcad3 | BLANK_NAMED | member AT_LEAST 1.903 already in T-714 (T-711 ledger); faces carry no figure (D-43) |
| L-71a283d2 | L-fb7a6431 | BLANK_NAMED | member stays capped blank 0 .. 3.5256 (R-T724-3): no floor; faces OQ-10 |
| L-8605b860 | L-fb7a6431 | BLANK_NAMED | member stays capped blank 0 .. 3.5256 (R-T724-3): no floor; faces OQ-10 |
| L-e3eb0057 | L-684fcad3 | BLANK_NAMED | member AT_LEAST 1.903 already in T-714 (T-711 ledger); faces carry no figure (D-43) |
| L-e86ee698 | L-ab37afa1 | AT_LEAST | member AT_LEAST 0.115155 already in T-714 (T-721 ledger); soffit FLOOR_ONLY 1.7993 kept |
