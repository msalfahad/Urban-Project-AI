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
| Earthworks | 0 | 1 |  |
| Rebar (parked) | 799 | 894 |  |
| Other | 0 | 1 |  |

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
| Earthworks | STR.EARTH.DISPOSAL | m3 | EW-T350:B1-04:ALL | HELD range | 105.632 | 115.546 | disposal range | excavation - backfill | none |
| Other | FIN.WALL.TILE.EDGE | lm | T-771:NEW:TILE_EDGE:DOOR_JAMBS | HELD range | 0.0 | 73.1 | no figure | to be decided | ? |
