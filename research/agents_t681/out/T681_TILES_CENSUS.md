# T-681 tiles and adhesive HELD census (V3.0.65)

Candidate ARCH_TAKEOFF_V3.0.65; 104 HELD lines = filter 'class HELD and item_code in FIN.FLOOR.PORCELAIN, FIN.FLOOR.WET_TILE, FIN.FLOOR.FINISH_HELD, EXT.FLOOR.PORCELAIN, EXT.FLOOR.OUTDOOR, FIN.WALL.TILE, FIN.SKIRTING, FIN.STAIR.SKIRTING.SLOPED, FIN.STAIR.SKIRTING.ZIGZAG, FIN.FLOOR.BED.DRY, FIN.FLOOR.BED.WET'. Research only, nothing wired.

| class | lines |
|---|---|
| DESIGNER_ITEM | 7 |
| MEASURABLE_NOW | 6 |
| OPEN_BOUND | 44 |
| OWNER_OPEN | 46 |
| WIRING_GAP | 1 |

| code [unit] | lines | bounded low .. high | blank | by class |
|---|---|---|---|---|
| EXT.FLOOR.OUTDOOR [m2] | 2 | 17.227412 .. 17.227412 (2) | 0 | OWNER_OPEN 2 |
| FIN.FLOOR.BED.DRY [m3] | 23 | 9.045554 .. 12.060739 (23) | 0 | OPEN_BOUND 23 |
| FIN.FLOOR.BED.WET [m3] | 21 | 3.423023 .. 5.134535 (21) | 0 | OPEN_BOUND 21 |
| FIN.FLOOR.FINISH_HELD [m2] | 1 | 0 .. 0.23 (1) | 0 | DESIGNER_ITEM 1 |
| FIN.SKIRTING [lm] | 7 | none bounded | 7 | DESIGNER_ITEM 4, MEASURABLE_NOW 2, WIRING_GAP 1 |
| FIN.STAIR.SKIRTING.SLOPED [lm] | 22 | none bounded | 22 | MEASURABLE_NOW 2, OWNER_OPEN 20 |
| FIN.STAIR.SKIRTING.ZIGZAG [lm] | 22 | none bounded | 22 | MEASURABLE_NOW 2, OWNER_OPEN 20 |
| FIN.WALL.TILE [m2] | 6 | none bounded | 6 | DESIGNER_ITEM 2, OWNER_OPEN 4 |

Materials beside the quantity (released + HELD bounded; blank lines counted, never 0):

| code | unit | released (lines) | held bounded / blank | total low .. high | material |
|---|---|---|---|---|---|
| FIN.FLOOR.PORCELAIN [m2] | m2 | 305.020973 (22) | 0 / 0 | 305.020973 .. 305.020973 | adhesive HELD 61.004195 .. 101.673658 bags (tile size not sourced: owner-rule bound area / 5 .. area / 3) |
| FIN.FLOOR.WET_TILE [m2] | m2 | 75.945577 (20) | 0 / 0 | 75.945577 .. 75.945577 | adhesive HELD 15.189115 .. 25.315192 bags (tile size not sourced: owner-rule bound area / 5 .. area / 3) |
| FIN.WALL.TILE [m2] | m2 | 340.3038 (12) | 0 / 6 | 340.3038 .. 340.3038 | adhesive HELD 68.06076 .. 113.4346 bags (tile size not sourced: owner-rule bound area / 5 .. area / 3) |
| EXT.FLOOR.PORCELAIN [m2] | m2 | 21.0142 (1) | 0 / 0 | 21.0142 .. 21.0142 | adhesive HELD 4.20284 .. 7.004733 bags (tile size not sourced: owner-rule bound area / 5 .. area / 3) |
| FIN.FLOOR.BED.DRY [m2] | m2 | 301.518472 (23) | 0 / 0 | 301.518472 .. 301.518472 | AREA: bed area (m2); its cement / sand ride on the m3 line |
| FIN.FLOOR.BED.DRY [m3] | m3 | 0 (0) | 23 / 0 | 9.045554 .. 12.060739 | 1:4 PROVISIONAL: cement 72.364432 .. 96.485912 bags, sand 9.950109 .. 13.266813 m3 (waste separate) |
| FIN.FLOOR.BED.WET [m2] | m2 | 85.575578 (21) | 0 / 0 | 85.575578 .. 85.575578 | AREA: bed area (m2); its cement / sand ride on the m3 line |
| FIN.FLOOR.BED.WET [m3] | m3 | 0 (0) | 21 / 0 | 3.423023 .. 5.134535 | 1:4 PROVISIONAL: cement 27.384184 .. 41.07628 bags, sand 3.765325 .. 5.647989 m3 (waste separate) |
| FIN.FLOOR.FINISH_HELD [m2] | m2 | 6.1275 (2) | 1 / 0 | 6.1275 .. 6.3575 | HELD: material not named (porcelain or marble) |
| EXT.FLOOR.OUTDOOR [m2] | m2 | 0 (0) | 2 / 0 | 17.227412 .. 17.227412 | HELD: OD-1 open: interlock (no adhesive) or ceramic |
| FIN.SKIRTING [lm] | lm | 209.428592 (18) | 0 / 7 | 209.428592 .. 209.428592 | HELD: no owner coverage rule per lm for skirting adhesive |
| ADHESIVE, the four tile codes as one purchasing group (group not decided: per code shown above) | bags | | | | HELD: exact 148.45691 .. 247.428183 -> 149 .. 248 bags (one ceil) |

MEASURABLE NOW (R-T681-2):
- L-33f2018c987f782d1c91 MS2-LD.W13 (W 1.050 .. 1.200): blank -> NOT_APPLICABLE 0 lm (DRAWING-CONFIRMED); walking levels 7.516 .. 7.516 lie inside the opening 6.5 .. 8.8: no wall face at the junction (full deduction of an actual opening)
- L-760bfa8dd00061361695 MS2-LD.W25 (N 1.400 .. 2.400): blank -> FULL 1 lm (DRAWING-CONFIRMED); walking level 7.684 at or above the head 7: the junction is on solid wall; adverse head 7.36: FULL 1
- L-18efa069acded71c81e7 MS1-L.W2 sloped (W 2.250 .. 1.200): blank -> NOT_APPLICABLE 0 lm (DRAWING-CONFIRMED); walking levels 2.0002 .. 2.667 lie inside the opening 2 .. 4: no wall face at the junction (full deduction of an actual opening)
- L-4ff56def5b73b558afbe MS2-L.W2 sloped (W 2.250 .. 1.200): blank -> NOT_APPLICABLE 0 lm (DRAWING-CONFIRMED); walking levels 6.844 .. 7.516 lie inside the opening 6.5 .. 8.8: no wall face at the junction (full deduction of an actual opening)
- L-76748b7b62ab2d52b4e2 MS1-L.W2 zigzag (W 2.250 .. 1.200): blank -> NOT_APPLICABLE 0 lm (DRAWING-CONFIRMED); walking levels 2.0002 .. 2.667 lie inside the opening 2 .. 4: no wall face at the junction (full deduction of an actual opening)
- L-f45c2e6d46b0cc6a7e53 MS2-L.W2 zigzag (W 2.250 .. 1.200): blank -> NOT_APPLICABLE 0 lm (DRAWING-CONFIRMED); walking levels 6.844 .. 7.516 lie inside the opening 6.5 .. 8.8: no wall face at the junction (full deduction of an actual opening)

Overlay-only lines in manifest V20 (not candidate lines, not in the census): 10

| line | code | element | bound | class | ref |
|---|---|---|---|---|---|
| L-1c51d1e7a3b65243382a | EXT.FLOOR.OUTDOOR | GF-COURT#POOL-DECK | 6.548912 .. 6.548912 | OWNER_OPEN | OD-1 (OWNER_RULE_OUTDOOR_FLOORS_2026-10-21) |
| L-dd6e372825ce06d45bdd | EXT.FLOOR.OUTDOOR | GF-COURT#PORCH | 10.6785 .. 10.6785 | OWNER_OPEN | OD-1 (OWNER_RULE_OUTDOOR_FLOORS_2026-10-21) |
| L-1a37b9a20284b5d43c6d | FIN.FLOOR.BED.DRY | 1F-R0E919A:floor:bed | 0.4902 .. 0.6536 | OPEN_BOUND |  |
| L-2bd727ad5af18963fcee | FIN.FLOOR.BED.DRY | 1F-R3CFCFD:floor:bed | 0.570496 .. 0.760662 | OPEN_BOUND |  |
| L-eaa8f30545cb37cac799 | FIN.FLOOR.BED.DRY | 1F-R78C367:floor:bed | 1.002331 .. 1.336441 | OPEN_BOUND |  |
| L-df07af4dda9e862fcc9d | FIN.FLOOR.BED.DRY | 1F-RB72F22:floor:bed | 0.5715 .. 0.762 | OPEN_BOUND |  |
| L-2a22528954348cfe8f5d | FIN.FLOOR.BED.DRY | 1F-RED0D19:floor:bed | 0.54645 .. 0.7286 | OPEN_BOUND |  |
| L-73acb02d16a6e7283a16 | FIN.FLOOR.BED.DRY | 1F-STRIP-OP-005:doorway strip:bed | 0.00405 .. 0.0054 | OPEN_BOUND |  |
| L-2cfe31faa23d63b519a3 | FIN.FLOOR.BED.DRY | 1F-STRIP-OP-006:doorway strip:bed | 0.00405 .. 0.0054 | OPEN_BOUND |  |
| L-bb85c5a6ef369ddb3c52 | FIN.FLOOR.BED.DRY | 1F-STRIP-OP-011:doorway strip:bed | 0.0045 .. 0.006 | OPEN_BOUND |  |
| L-de23b2f2e950f1271444 | FIN.FLOOR.BED.DRY | 1F-STRIP-OP-020:doorway strip:bed | 0.0045 .. 0.006 | OPEN_BOUND |  |
| L-86fe1fd55ffd5f019980 | FIN.FLOOR.BED.DRY | 1F-THRESHOLD-D-1F-03:doorway strip:bed | 0.0045 .. 0.006 | OPEN_BOUND |  |
| L-e64c279d4f59c053e0e2 | FIN.FLOOR.BED.DRY | 2F-R1DB2D2:floor:bed | 0.5805 .. 0.774 | OPEN_BOUND |  |
| L-6ad86fb8cffae1db8883 | FIN.FLOOR.BED.DRY | 2F-R4D1B62:2F-ST-LOBBY:bed | 0.066 .. 0.088 | OPEN_BOUND |  |
| L-dcd2057b1af45b1506bc | FIN.FLOOR.BED.DRY | 2F-STRIP-OP-007:doorway strip:bed | 0.0054 .. 0.0072 | OPEN_BOUND |  |
| L-bff6fe38b9392a8fcad6 | FIN.FLOOR.BED.DRY | GF-R31F8AE:GF-ST-HALL:bed | 0.14415 .. 0.1922 | OPEN_BOUND |  |
| L-b87fd07d7fc055529b3d | FIN.FLOOR.BED.DRY | GF-R31F8AE:GF-ST-LOBBY030:bed | 0.039675 .. 0.0529 | OPEN_BOUND |  |
| L-1d6187b5cbe130c765e1 | FIN.FLOOR.BED.DRY | GF-R51E127:floor:bed | 0.23625 .. 0.315 | OPEN_BOUND |  |
| L-aca5059199408fa8fd16 | FIN.FLOOR.BED.DRY | GF-R7512EA:floor:bed | 0.74821 .. 0.997613 | OPEN_BOUND |  |
| L-d94637fde6d101142bd8 | FIN.FLOOR.BED.DRY | GF-R75FBAE:floor:bed | 0.496489 .. 0.661986 | OPEN_BOUND |  |
| L-77a1828643912803397f | FIN.FLOOR.BED.DRY | GF-RC99C2A:floor:bed | 3.284353 .. 4.379137 | OPEN_BOUND |  |
| L-93a91d33816d3f613fb2 | FIN.FLOOR.BED.DRY | GF-RFD4E1D:SOUTH-FACADE-DINING:bed | 0.16935 .. 0.2258 | OPEN_BOUND |  |
| L-e04bc22980376ee3dc6c | FIN.FLOOR.BED.DRY | GF-STRIP-OP-010:doorway strip:bed | 0.006 .. 0.008 | OPEN_BOUND |  |
| L-14ee83afeb3d8d89b667 | FIN.FLOOR.BED.DRY | GF-STRIP-OP-012:doorway strip:bed | 0.0045 .. 0.006 | OPEN_BOUND |  |
| L-a691179a929d6be0fada | FIN.FLOOR.BED.DRY | HL:FLOOR_SCOPE:UNDER_STAIR:GF:GF-RC99C2A-UNDER-STAIR:bed | 0.0621 .. 0.0828 | OPEN_BOUND |  |
| L-2537d8e9bbcc02a38181 | FIN.FLOOR.BED.WET | 1F-R26FA0D:floor:bed | 0.40604 .. 0.60906 | OPEN_BOUND |  |
| L-d052fc204af327475d0b | FIN.FLOOR.BED.WET | 1F-R48AA46:floor:bed | 0.2009 .. 0.30135 | OPEN_BOUND |  |
| L-4ad2142aa1c80602446e | FIN.FLOOR.BED.WET | 1F-R48CDA5:floor:bed | 0.189 .. 0.2835 | OPEN_BOUND |  |
| L-21b716533078b7c0f111 | FIN.FLOOR.BED.WET | 1F-R52AC05:floor:bed | 0.10584 .. 0.15876 | OPEN_BOUND |  |
| L-8067c0be0645790208f8 | FIN.FLOOR.BED.WET | 1F-R8BDA49:floor:bed | 0.2009 .. 0.30135 | OPEN_BOUND |  |
| L-84e82fbdf76caf361086 | FIN.FLOOR.BED.WET | 1F-RED23B8:floor:bed | 0.1431 .. 0.21465 | OPEN_BOUND |  |
| L-93e7f9a075077c9ed7ca | FIN.FLOOR.BED.WET | 2F-RE83BED:floor:bed | 0.222 .. 0.333 | OPEN_BOUND |  |
| L-309e534c9e69a0e9eea0 | FIN.FLOOR.BED.WET | GF-R8496F0:floor:bed | 0.1253 .. 0.18795 | OPEN_BOUND |  |
| L-2b9341453af532f440a9 | FIN.FLOOR.BED.WET | GF-RA3AD49:floor:bed | 0.3852 .. 0.5778 | OPEN_BOUND |  |
| L-87ef5acbbd0f2d210025 | FIN.FLOOR.BED.WET | GF-RB28769:floor:bed | 0.094704 .. 0.142057 | OPEN_BOUND |  |
| L-a9d9a66ef39bd297b3cb | FIN.FLOOR.BED.WET | GF-RB62B55:floor:bed | 0.135 .. 0.2025 | OPEN_BOUND |  |
| L-ef1a214a1415b15aae85 | FIN.FLOOR.BED.WET | GF-RD36087:floor:bed | 0.0594 .. 0.0891 | OPEN_BOUND |  |
| L-f0f2b9606bb5c88b8133 | FIN.FLOOR.BED.WET | GF-RD6F891:floor:bed | 0.148707 .. 0.223061 | OPEN_BOUND |  |
| L-4b441d934e11e0dc0bba | FIN.FLOOR.BED.WET | GF-RDBD4F9:floor:bed | 0.189228 .. 0.283842 | OPEN_BOUND |  |
| L-410b5ba3307fa9d754a2 | FIN.FLOOR.BED.WET | GF-RDF7D28:floor:bed | 0.0945 .. 0.14175 | OPEN_BOUND |  |
| L-91e5d65e221e06e01409 | FIN.FLOOR.BED.WET | GF-RF38DAF:floor:bed | 0.107009 .. 0.160513 | OPEN_BOUND |  |
| L-6cef63554b61bc313f9e | FIN.FLOOR.BED.WET | GF-RFAD3C4:floor:bed | 0.078 .. 0.117 | OPEN_BOUND |  |
| L-db4ddcc9c0dad26f3400 | FIN.FLOOR.BED.WET | HL:FLOOR_SCOPE:TO_WET:GF:GF-OP-003-NO-OPENING:pantry:bed | 0.024 .. 0.036 | OPEN_BOUND |  |
| L-de27c912fcc3487b4410 | FIN.FLOOR.BED.WET | HL:FLOOR_SCOPE:WET:GF:GF-PANTRY-RC06FED:bed | 0.112 .. 0.168 | OPEN_BOUND |  |
| L-e42d43677f585b1be06e | FIN.FLOOR.BED.WET | HL:FLOOR_SCOPE:WET:GF:GF-PANTRY-RC99C2A-PART:bed | 0.358195 .. 0.537292 | OPEN_BOUND |  |
| L-e3f1ecf81479cf6bc108 | FIN.FLOOR.BED.WET | HL:FLOOR_SCOPE:WET:GF:SITE-0a31aaa10796d33a:bed | 0.044 .. 0.066 | OPEN_BOUND |  |
| L-a788de4672b1f0d2e6c1 | FIN.FLOOR.FINISH_HELD | GF-R31F8AE:GF-ST-CN | 0 .. 0.23 | DESIGNER_ITEM |  |
| L-47fa825d197d32754240 | FIN.SKIRTING | GF-R31F8AE:stair hall skirting | blank | DESIGNER_ITEM |  |
| L-4e7d3bef5e6ac89252ff | FIN.SKIRTING | SKIRT-T443:GF-ST-HALL:DIVIDER-BAND | blank | DESIGNER_ITEM |  |
| L-6ff876aefb5a3631565c | FIN.SKIRTING | SKIRT-T443:GF-ST-HALL:OP-020-JAMBS | blank | WIRING_GAP |  |
| L-d589222eace010fefa69 | FIN.SKIRTING | SKIRT-T443:GF-ST-LOBBY030:WEST-FACE | blank | DESIGNER_ITEM |  |
| L-5273c35e05acc8ebeb59 | FIN.SKIRTING | STAIR-SKIRT:MS1-LD.N | blank | DESIGNER_ITEM |  |
| L-33f2018c987f782d1c91 | FIN.SKIRTING | STAIR-SKIRT:MS2-LD.W13 | blank | MEASURABLE_NOW |  |
| L-760bfa8dd00061361695 | FIN.SKIRTING | STAIR-SKIRT:MS2-LD.W25 | blank | MEASURABLE_NOW |  |
| L-775f62538c1f46077807 | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:D1.E | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-b77a64fb9a941582f25c | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:E1.S | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-a43adc74906d8bcd7b1c | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS1-L.W1 | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-ff51392df9e2c8c21efe | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS1-L.W1B | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-aed4c2990437f767dc90 | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS1-L.W1C | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-18efa069acded71c81e7 | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS1-L.W2 | blank | MEASURABLE_NOW |  |
| L-28c33cd0ab5d19426661 | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS1-T.N | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-2fae5d35b21e97684844 | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS1-T.W | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-32f71724eeeaa46638c9 | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS1-U.E1 | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-20c2640927e41626893d | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS1-U.E2 | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-cfecfcea2280155a6a74 | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS1-U.E3a | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-8e463d6ce740fc19e60c | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS1-U.E3b | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-9b1da1af7c162de2233c | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS2-L.W1 | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-caacb4c1425981b2585f | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS2-L.W1B | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-193f8e812d9ade5f9c41 | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS2-L.W1C | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-4ff56def5b73b558afbe | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS2-L.W2 | blank | MEASURABLE_NOW |  |
| L-76de75ce9a315998be99 | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS2-TR.N | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-4b902816d29b75fab7fc | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:MS2-U.E | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-1c082cc60442407ed517 | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:RS-C.OUT | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-ebe230d8c2fbc35332b8 | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:RS-S.S0 | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-0ae4be232407b92343ef | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:RS-S.S1 | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-d980ace38bdd63fa8de4 | FIN.STAIR.SKIRTING.SLOPED | STAIR-SKIRT:RS-S.S2 | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-4548e7ad947b07624e81 | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:D1.E | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-add5acd610925402e0f5 | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:E1.S | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-53f3b7f153af0e1f5538 | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS1-L.W1 | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-9e5ed7164ee85f0fc196 | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS1-L.W1B | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-c56a452218763d5e7bbf | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS1-L.W1C | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-76748b7b62ab2d52b4e2 | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS1-L.W2 | blank | MEASURABLE_NOW |  |
| L-5f0bd2b45c1718aeefc4 | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS1-T.N | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-5bc4cea35db33e41d78c | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS1-T.W | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-bc0e1e80ca50865ccd06 | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS1-U.E1 | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-1ed4cfaa1c12054b401d | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS1-U.E2 | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-9ec979f00305b8ae8049 | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS1-U.E3a | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-984553ed0b69b0f77fe2 | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS1-U.E3b | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-656ab12cc9b9797d3b1a | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS2-L.W1 | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-20432b887f91dee03925 | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS2-L.W1B | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-1c907e0a59c55204e430 | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS2-L.W1C | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-f45c2e6d46b0cc6a7e53 | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS2-L.W2 | blank | MEASURABLE_NOW |  |
| L-5021b820dba41f631dde | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS2-TR.N | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-c8dce28c50dabd7b17fb | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:MS2-U.E | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-1a0d2ab50e42b0219eab | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:RS-C.OUT | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-c074ce526885a44423d0 | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:RS-S.S0 | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-544b6b11bab9bbf037fb | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:RS-S.S1 | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-8dde910ffeeb94a58323 | FIN.STAIR.SKIRTING.ZIGZAG | STAIR-SKIRT:RS-S.S2 | blank | OWNER_OPEN | ORR-007 (payable form zigzag / sloped) |
| L-d0858b30e0ea869bd047 | FIN.WALL.TILE | GF-R8496F0:wall_tile | blank | OWNER_OPEN | Q-54 B HOLD |
| L-c330b8dc47261d5ada7e | FIN.WALL.TILE | GF-RA3AD49:wall_tile | blank | OWNER_OPEN | Q-54 B HOLD |
| L-96d9839bd3bca4c08a67 | FIN.WALL.TILE | GF-RB62B55:wall_tile | blank | OWNER_OPEN | Q-54 B HOLD |
| L-de4088e7012e655bb071 | FIN.WALL.TILE | GF-RD36087:wall_tile | blank | DESIGNER_ITEM |  |
| L-1341e0410a469089c3be | FIN.WALL.TILE | GF-RDF7D28:wall_tile | blank | DESIGNER_ITEM |  |
| L-88c11c5d8dc1dfd7c27e | FIN.WALL.TILE | GF-RFAD3C4:wall_tile | blank | OWNER_OPEN | Q-54 B HOLD |
