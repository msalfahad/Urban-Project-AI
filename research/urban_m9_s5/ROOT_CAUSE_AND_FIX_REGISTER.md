# M9 S5: root-cause and fix register (generic)

Every entry was found on the reference villa or by a new regression test, and fixed by a generic rule in the existing modules. No benchmark figure and no drawing identity is written here.

| Id | Defect | Root cause | Fix (module / function) | Test |
|---|---|---|---|---|
| D1 | An open space whose room words need different finishes (dry + exterior / wet) stayed one unallocated face | a MERGED face could only be split by a drawn wall; lines drawn inside it were never used | `arch_rooms.zone_partition`: TS01 pass 3 on the non-structural lines clipped to the face (symbols and lines through walls excluded), cells grouped by words and finish family, lines kept only between groups; PROVISIONAL + ZONE_FROM_DRAWN_LINES | `test_s5_zones.py`, `test_s5_real_regression.py` |
| D2 | A wash lobby (basins, no room word) inside the open space had no wet floor or waterproofing | D1: no face existed for it | D1's zones + the S3 fixtures rule (ROOM_TYPE_FROM_FIXTURES, review) | zones fixture (wash corner) |
| D3 | A door between two wet spaces got two waterproofing doorway pieces | per-room loop with no owner of the door | `arch_measure.measure`: `wp_door_owner` (one piece; the other upturn line notes SHARED_WET_DOORWAY) | `test_a_door_between_two_wet_rooms_has_one_doorway_piece` |
| D4 | The ceiling under a void was counted on the lower and the upper plan | Round 5's void-above rule was not ported | `arch_rooms.voids_above` (column-grid alignment, lower-plan corroboration) + ceiling lines NORMAL_LEVEL / DOUBLE_HEIGHT | `test_s5_ceilings_wp.py` |
| D5 | The ceiling deduction list named a void and a stair below that were not deducted | list copied from the floor line | the ceiling list names only what it deducts | ceiling tests |
| D6 | A stair enclosure had no ceiling record (silent omission) | NO_FINISH branch emitted nothing | FIN.CEILING STAIRWELL, BLOCKED_RFI (section needed) | `test_stair_room_has_a_blocked_stairwell_ceiling` |
| D7 | Guardrails were never measured | no side classification of flights | `arch_measure.flight_sides` + FIN.RAILING on open sides (UP-STAIR-012), BLOCKED without a riser | `test_flight_sides_wall_or_open` |
| D8 | Openings carried no host wall, type or height state | inventory fields missing | `arch_measure._host_wall` + opening fields | real run (every opening hosted) |
| D9 | Arabic text of a pre-2007 DXF was lost (`\U+XXXX` escapes) | the reader did not decode the DXF escapes | `tools.arch_intake.decode_text` (DXF_UNICODE_ESCAPE; raw kept) | `test_dxf_version_round_trip_keeps_every_quantity`, `test_dxf_unicode_escapes_are_decoded_and_the_raw_text_kept` |
| D10 | A wall finish would run along a zone line (no wall there) | run = the whole perimeter | run = perimeter − ZONE_LINE length | `test_measurement_follows_the_zones` |
| D11 | Added boundary pieces were not logged | – | `spaces()["repairs"]`, `ARCH_PLAN.regions[].repairs` | `test_repairs_are_logged_never_moved` |

Open items, all needing an owner rule, a source or a second villa:
- a circulation band around a void inside one room;
- whether a GARDEN-labelled strip inside the building outline takes the floor finish;
- the waterproofing scope (kitchens);
- the definition of the architect's floor area;
- the skirting remainder;
- linetype (dashed hidden lines) in zones;
- landing and void-edge balustrades;
- the DWG round trip.
