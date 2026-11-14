# Blank lines of ARCH_TAKEOFF_V3.0.86 (with MAIN FILL applied): where the figures are missing and what fills them

BLANK = no figure at all; HELD range = low..high only. Rebar is parked (count only). Every other line gets a figure by
the fallback order (geometry -> drawing read -> company default -> ratio -> safety); the last column says what the owner can give to
make it DRAWING-READ instead of DEFAULT.

## Per trade

| trade | BLANK | HELD range | what the owner can give |
|---|---|---|---|
| Tiles | 0 | 1 | finish of the room |
| Stairs | 14 | 0 | same stair section; railing type (steel / glass / timber) |
| Openings | 0 | 2 |  |
| Rebar (parked) | 799 | 894 |  |
| Other | 0 | 1 |  |

## MAIN FILL overlay (T-796 precedence): {"ALREADY": 66, "SKIP_NEWER": 23, "APPLY": 18}

A row applies only where the index line still carries the row's before state and no later fill_basis. Rows skipped (the index value stands):

| line id | item | unit | action | index | MAIN FILL row |
|---|---|---|---|---|---|
| L-0cb71da74613f446eee9 | FIN.ROOF.PROTECTION | m2 | SKIP_NEWER | ['RELEASED', 55.559, None, None] | ['RELEASED', 54.9203, None, None] |
| L-122cbab32ca719527de8 | FIN.ROOF.INSULATION | m2 | SKIP_NEWER | ['RELEASED', 115.813974, None, None] | ['RELEASED', 115.65646, None, None] |
| L-19912fbc18556b65ccf6 | FIN.ROOF.INSULATION | m2 | SKIP_NEWER | ['RELEASED', 34.390242, None, None] | ['RELEASED', 46.589375, None, None] |
| L-5f018cfc13aaa9ae2210 | FIN.ROOF.SCREED | m3 | SKIP_NEWER | ['RELEASED', 2.454075, None, None] | ['RELEASED', 2.373225, None, None] |
| L-8a5192a5ee3e40b61b08 | FIN.ROOF.INSULATION | m2 | SKIP_NEWER | ['RELEASED', 55.559, None, None] | ['RELEASED', 54.9203, None, None] |
| L-940b7a65d7e79bc0ec33 | FIN.ROOF.INSULATION | m2 | SKIP_NEWER | ['RELEASED', 32.721, None, None] | ['RELEASED', 31.643, None, None] |
| L-ab79aa46b9647f63b54a | FIN.ROOF.FINISH | m2 | SKIP_NEWER | ['RELEASED', 34.390242, None, None] | ['RELEASED', 46.589375, None, None] |
| L-b016c961ddf9e530e3c1 | FIN.ROOF.SCREED | m3 | SKIP_NEWER | ['RELEASED', 2.579268, None, None] | ['RELEASED', 3.494203, None, None] |
| L-bec94500648a90fb2f2a | FIN.ROOF.SCREED | m3 | SKIP_NEWER | ['RELEASED', 4.166925, None, None] | ['RELEASED', 4.119022, None, None] |
| L-c5c48bba5d23fa70e9ad | FIN.ROOF.PROTECTION | m2 | SKIP_NEWER | ['RELEASED', 34.390242, None, None] | ['RELEASED', 46.589375, None, None] |
| L-e0dc4455bc0c6ee4fa9b | FIN.ROOF.PROTECTION | m2 | SKIP_NEWER | ['RELEASED', 115.813974, None, None] | ['RELEASED', 115.65646, None, None] |
| L-f4ae7151a6e2b93dd7ad | FIN.ROOF.SCREED | m3 | SKIP_NEWER | ['RELEASED', 8.686048, None, None] | ['RELEASED', 8.674234, None, None] |
| L-f9e6d4f8c099f6a6cc8e | FIN.ROOF.PROTECTION | m2 | SKIP_NEWER | ['RELEASED', 32.721, None, None] | ['RELEASED', 31.643, None, None] |
| L-3e8fe55da71851816dd4 | FIN.WP.ROOF | m2 | SKIP_NEWER | ['RELEASED', 34.390242, None, None] | ['RELEASED', 46.589375, None, None] |
| L-78d7c8a989ab34527a1c | STR.EARTH.DISPOSAL | m3 | SKIP_NEWER | ['RELEASED', 10.476796, None, None] | ['HELD', None, 105.632, 115.546] |
| L-348c4d8d32f3f6d35fe5 | ARCH.FACADE | m2 | SKIP_NEWER | ['RELEASED', 125.16, None, None] | ['RELEASED', 117.14, None, None] |
| L-43527ae4e8ec75c56636 | ARCH.FACADE | m2 | SKIP_NEWER | ['RELEASED', 280.73812, None, None] | ['RELEASED', 231.3317, None, None] |
| L-8bb83e16cc7b104ab88b | FIN.EXT.FINISH | m2 | SKIP_NEWER | ['RELEASED', 249.954348, None, None] | ['RELEASED', 231.3317, None, None] |
| L-b05f70c92405dbcfbe62 | FIN.EXT.FINISH | m2 | SKIP_NEWER | ['RELEASED', 391.253149, None, None] | ['RELEASED', 413.7791, None, None] |
| L-c0e9a4c62171de1f369b | ARCH.FACADE | m2 | SKIP_NEWER | ['RELEASED', 71.75114, None, None] | ['RELEASED', 105.8867, None, None] |
| L-cc7dc0a51f3319a99482 | ARCH.FACADE | m2 | SKIP_NEWER | ['RELEASED', 469.329, None, None] | ['RELEASED', 413.7791, None, None] |
| L-d52c4f763b19aedf8b8b | FIN.EXT.FINISH | m2 | SKIP_NEWER | ['RELEASED', 117.305, None, None] | ['RELEASED', 117.14, None, None] |
| L-636fd3ff1784a12e653b | FIN.WP.ROOF | m2 | SKIP_NEWER | ['RELEASED', 115.813974, None, None] | ['RELEASED', 115.6565, None, None] |

## Every line (rebar left out)

| trade | item | unit | element | state | low | high | why no figure | what fills it | owner can give |
|---|---|---|---|---|---|---|---|---|---|
| Tiles | FIN.FLOOR.FINISH_HELD | m2 | GF-R31F8AE:GF-ST-CN | HELD range | 0.0 | 0.23 | floor finish range | plan area | finish of the room |
| Stairs | FIN.RAILING | lm | RAIL:RL-07:ST-01:T-MS1-N | BLANK |  |  | railing with no run length | flight sloped length + landing edge | same stair section; railing type (steel / glass / timber) |
| Stairs | FIN.RAILING | lm | RAIL:RL-07:ST-01:T-MS2-LD | BLANK |  |  | railing with no run length | flight sloped length + landing edge | same stair section; railing type (steel / glass / timber) |
| Stairs | FIN.RAILING | lm | RAIL:RL-09 | BLANK |  |  | railing with no run length | flight sloped length + landing edge | same stair section; railing type (steel / glass / timber) |
| Stairs | FIN.RAILING | lm | RAIL:RL-11 | BLANK |  |  | railing with no run length | flight sloped length + landing edge | same stair section; railing type (steel / glass / timber) |
| Stairs | FIN.RAILING | lm | RAIL:ST-01b:GF east-lane band beyond D1 | BLANK |  |  | railing with no run length | flight sloped length + landing edge | same stair section; railing type (steel / glass / timber) |
| Stairs | FIN.SKIRTING | lm | GF-R31F8AE:stair hall skirting | BLANK |  |  | stair hall / landing skirting with no length | landing perimeter - openings | same |
| Stairs | FIN.SKIRTING | lm | SKIRT-T443:GF-ST-HALL:DIVIDER-BAND | BLANK |  |  | stair hall / landing skirting with no length | landing perimeter - openings | same |
| Stairs | FIN.SKIRTING | lm | SKIRT-T443:GF-ST-HALL:OP-020-JAMBS | BLANK |  |  | stair hall / landing skirting with no length | landing perimeter - openings | same |
| Stairs | FIN.SKIRTING | lm | SKIRT-T443:GF-ST-LOBBY030:WEST-FACE | BLANK |  |  | stair hall / landing skirting with no length | landing perimeter - openings | same |
| Stairs | FIN.SKIRTING | lm | STAIR-SKIRT:MS1-LD.N | BLANK |  |  | stair hall / landing skirting with no length | landing perimeter - openings | same |
| Stairs | FIN.SKIRTING | lm | STAIR-SKIRT:MS2-LD.W13 | BLANK |  |  | stair hall / landing skirting with no length | landing perimeter - openings | same |
| Stairs | FIN.SKIRTING | lm | STAIR-SKIRT:MS2-LD.W25 | BLANK |  |  | stair hall / landing skirting with no length | landing perimeter - openings | same |
| Stairs | MET.RAILING.GUARD | lm | RAIL:RL-04 | BLANK |  |  | guard rail with no run length | edge length | same |
| Stairs | MET.RAILING.GUARD | lm | RAIL:RL-10 | BLANK |  |  | guard rail with no run length | edge length | same |
| Openings | ARCH.SPACE | m2 | HL:FLOOR_SCOPE:HELD_WITH:GF:GF-OP-003-NO-OPENING:band | HELD range | 0.604 | 0.604 | space area range | plan area | none |
| Openings | ARCH.SPACE | m2 | HL:FLOOR_SCOPE:UNDER_STAIR_HELD:GF:GF-RC99C2A-UNDER-STAIR | HELD range | 6.124412 | 6.124412 | space area range | plan area | none |
| Other | FIN.WALL.TILE.EDGE | lm | T-771:NEW:TILE_EDGE:DOOR_JAMBS | HELD range | 0.0 | 73.1 | no figure | to be decided | ? |
