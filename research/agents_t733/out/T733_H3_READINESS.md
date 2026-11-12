# T-733 tiles H3 readiness on ARCH_TAKEOFF_V3.0.73 (c5a0b128, NOT RELEASED)

## (a) F1 / F4 tread highs

| reading | F1 m2 | F4 m2 | overlap | union | sum |
|---|---|---|---|---|---|
| mixed_engine | 4.094412 | 3.45 | 0.057438 | 7.486974 | 7.544412 |
| set_layer2 | 4.094412 | 3.45 | 0.0 | 7.544412 | 7.544412 |
| set_layer5 | 4.104061 | 3.45 | 0.0 | 7.554061 | 7.554061 |

Verdict: SET_MIX; governing set set_layer2 (end lines on the drawn outline); NO_DOUBLE_COUNT: T-727 s.5 DOUBLE_COUNT_RISK 0.0574 m2 withdrawn (SET_MIX); highs kept

| line | item | element | class | candidate | own | diff | verdict |
|---|---|---|---|---|---|---|---|
| L-6cf11c2d30387d0942b9 | FIN.MARBLE.TREAD | 1F-R78C367:flight 1 | HELD | 4.094413 | 4.094412 | 0.000001 | ENGINE_RIGHT |
| L-ea55ed317bc4de89aec1 | FIN.MARBLE.TREAD | 1F-R78C367:flight 4 | HELD | 3.450000 | 3.450000 | 0.000000 | ENGINE_RIGHT |
| L-fa534ec5f9dc14947899 | FIN.MARBLE.TREAD | GF-RC99C2A:flight 1 | HELD | 4.094413 | 4.094412 | 0.000001 | ENGINE_RIGHT |
| L-89c84fdd4964dec8a323 | FIN.MARBLE.TREAD | GF-RC99C2A:flight 2 | RELEASED | 3.450000 | 3.450000 | 0.000000 | ENGINE_RIGHT |

## (b) V-07

Before: HELD NOT A DRAWN VOID (S0). After: NOT_A_VOID (DRAWING-CONFIRMED): slab panel drawn continuous; beams cross the footprint.

Evidence: overlay {'arch_2F_block_columns': 9, 'matched_st': 9, 'worst_corner_residual_mm': 0.495909}; sheet columns 9; inside the dome footprint {'HATCH/S-COL.HAT': 2, 'LINE/1': 7, 'LINE/S-COL.BON': 2, 'LINE/S-REIN-SLAB': 3, 'LWPOLYLINE/REIN': 1, 'LWPOLYLINE/S-COL.BON': 2, 'LWPOLYLINE/S-TEXT.D': 1}; beam lines crossing 7; S-OPENING on sheet 0.

Ceilings: L-7531772e1581b35eea5f 2F-R1DB2D2:ceiling 19.350001 ENGINE_RIGHT; L-1bd4ec39660768d22677 2F-RE83BED:ceiling 5.550000 ENGINE_RIGHT

S1: client request (Q-29, owner 2026-10-22: no revised structural drawing): an open skylight would need a redesigned slab (beams and a column cross the footprint); shown apart, not quantified, never applied; designer item DOME-3 / CF-S8.3-01 (D-21) unchanged

## (c) census

321 lines; HELD 127 (blank 72); stale vs V3.0.69 {'stale': 0, 'missing': 0, 'added': 0}

| code | class | n |
|---|---|---|
| EXT.FLOOR.OUTDOOR | HELD | 2 |
| EXT.FLOOR.PORCELAIN | RELEASED | 1 |
| FIN.FLOOR.BED.DRY | HELD | 23 |
| FIN.FLOOR.BED.DRY | RELEASED | 23 |
| FIN.FLOOR.BED.WET | HELD | 21 |
| FIN.FLOOR.BED.WET | RELEASED | 21 |
| FIN.FLOOR.FINISH_HELD | HELD | 1 |
| FIN.FLOOR.FINISH_HELD | RELEASED | 2 |
| FIN.FLOOR.PORCELAIN | EXCLUDED | 13 |
| FIN.FLOOR.PORCELAIN | RELEASED | 22 |
| FIN.FLOOR.WET_TILE | RELEASED | 20 |
| FIN.MARBLE.LANDING | HELD | 2 |
| FIN.MARBLE.LANDING | RELEASED | 2 |
| FIN.MARBLE.LIFT_SURROUND | HELD | 3 |
| FIN.MARBLE.LIFT_THRESHOLD | RELEASED | 6 |
| FIN.MARBLE.RISER | EXCLUDED | 1 |
| FIN.MARBLE.RISER | HELD | 13 |
| FIN.MARBLE.RISER | RELEASED | 1 |
| FIN.MARBLE.THRESHOLD | RELEASED | 14 |
| FIN.MARBLE.TREAD | EXCLUDED | 2 |
| FIN.MARBLE.TREAD | HELD | 5 |
| FIN.MARBLE.TREAD | RELEASED | 8 |
| FIN.SKIRTING | EXCLUDED | 28 |
| FIN.SKIRTING | HELD | 7 |
| FIN.SKIRTING | RELEASED | 18 |
| FIN.STAIR.SKIRTING.SLOPED | HELD | 22 |
| FIN.STAIR.SKIRTING.ZIGZAG | HELD | 22 |
| FIN.WALL.TILE | HELD | 6 |
| FIN.WALL.TILE | RELEASED | 12 |

| HELD cause (source) | n |
|---|---|
| AT_LEAST (T-715) | 3 |
| AT_MOST (T-715) | 8 |
| BLANK_NAMED (T-715) | 1 |
| CONDITIONAL_ON_FORM (T-715) | 27 |
| DESIGNER_ITEM (T-681) | 7 |
| MEASURABLE_NOW (T-681) | 2 |
| MEASURED (T-715) | 8 |
| NOT_APPLICABLE (T-715) | 12 |
| OPEN_BOUND (T-681) | 44 |
| OWNER_OPEN (T-681) | 6 |
| PRINTED_VALUE_GAP (T-648) | 3 |
| RANGE (T-715) | 4 |
| WIRING_GAP (T-681) | 1 |
| WIRING_GAP (T-715) | 1 |

Wiring H3 / H3s: 94 rows, stale hosts 0

| hub | action | n |
|---|---|---|
| H3 | CHANGE | 2 |
| H3S | ADD | 1 |
| H3S | BESIDE | 44 |
| H3S | CHANGE | 43 |
| H3S | KEEP | 1 |
| H3S | TEXT | 3 |

no line in this census carries a waste factor; size-based waste (Urban tile rule) is applied only in the materials stage on the purchasing group, never as a default here

no quantity moved; nothing wired; V2.9 + route G unchanged
