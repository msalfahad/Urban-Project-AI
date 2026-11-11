# T-719 void register on ARCH_TAKEOFF_V3.0.71 (research, unwired)

| void | name | pierces | below | outline m2 | status | floor (pierced storey) | ceiling below | top |
|---|---|---|---|---|---|---|---|---|
| V-01 | ST-02 light well over the GF reception (double height GF + 1F) | 1F | GF | 26.240000 | DRAWING-CONFIRMED | DEDUCTED_TWICE -0.057168 | DEDUCTED_ONCE -0.000100 | DOUBLE_COUNT_RISK |
| V-02 | oval opening beside the 1F east bay | 1F (slab east of the curved glazing) | GF (pool court, exterior) | 3.824427 | DRAWING-CONFIRMED | EXTERIOR | - | - |
| V-03 | lift shaft 1.80 x 1.80 | 1F and 2F slabs (stacked GF / 1F / 2F) | pit / GF | 3.240000 | DRAWING-CONFIRMED | DEDUCTED_ONCE | - | - |
| V-04 | ST-01 dog-leg stair shaft (GF -> 2F) | 1F and 2F slabs | GF / 1F (stair continuous to the 2F stair hall) | 10.725000 | DRAWING-CONFIRMED | - | DEDUCTED_ONCE | - |
| V-05 | west dome opening | 1F roof slab (2F plan, roof terrace) | 1F rooms | 15.359013 | DRAWING-CONFIRMED | - | 1F-RB72F22:ceiling DEDUCTED_ONCE; 1F-R8BDA49:ceiling DEDUCTED_ONCE; 1F-R48AA46:ceiling DEDUCTED_ONCE | DEDUCTED_ONCE |
| V-06 | east dome opening | 1F roof slab (2F plan, roof terrace) | 1F rooms | 15.359013 | DRAWING-CONFIRMED | - | 1F-R3CFCFD:ceiling DEDUCTED_ONCE; 1F-R48CDA5:ceiling DEDUCTED_ONCE; 1F-R78C367 (inside the decor group) DEDUCTED_ONCE (HELD part); 0.030 m2 named residual: own circle vs T-283's arc pieces | DEDUCTED_ONCE |
| V-07 | third dome (upper roof) | top roof slab (+13.90) | 2F rooms | None | HELD | NOT A DRAWN VOID (S0) | - | - |

## Flags (no quantity moved)

- V-01 L-b06400d46d252f242018: **ENGINE_WRONG (candidate)** 0.057168 m2: 1F living porcelain deducts one 1.15 x 0.05 strip of the light well twice (two ST-02 flight footprints summed where they overlap) (if corrected: 33.468204)
- V-01 L-35341ff2e6a848b9436b: **DOUBLE_COUNT_RISK** 16.005000 m2: blank 'ceiling over void' line names m2 the decor group line L-43bf1f86 already carries; it must never be valued beside it (if corrected: line stays blank / EXCLUDED; no value moves)

## Candidate lines read

- L-ac337bf041e8184a315c 1F-R3CFCFD:ceiling: RELEASED 18.674700 (1F east master ceiling (under V-06))
- L-c25a76ebdaab3ec65076 1F-R48AA46:ceiling: RELEASED 3.781500 (1F bath ceiling (under V-05))
- L-c85ec92c5f1e50dadd11 1F-R48CDA5:ceiling: RELEASED 4.277800 (1F bath ceiling (under V-06))
- L-fc116bb666b184740090 1F-R78C367:ceiling: HELD None (1F living ceiling parent)
- L-35341ff2e6a848b9436b 1F-R78C367:ceiling over void: HELD None (1F living 'ceiling over void' (V2.9 base line))
- L-43bf1f869e1588f1d3bd 1F-R78C367:ceiling#DECOR_GROUP: RELEASED 51.049600 (1F living decor ceiling (top of V-01))
- L-b06400d46d252f242018 1F-R78C367:floor: RELEASED 33.411036 (1F living porcelain (pierced storey of V-01))
- L-05b1d88f06c38f962cb6 1F-R8BDA49:ceiling: RELEASED 3.599800 (1F bath ceiling (under V-05))
- L-69ebc828b4c61f4ea348 1F-RB72F22:ceiling: RELEASED 7.469200 (1F west master ceiling (under V-05))
- L-7531772e1581b35eea5f 2F-R1DB2D2:ceiling: RELEASED 19.350001 (2F maid ceiling (under dome 3))
- L-dd6930fd19ca1b908c56 2F-R4D1B62:stairwell ceiling: HELD None (ST-01 2F stairwell)
- L-1bd4ec39660768d22677 2F-RE83BED:ceiling: RELEASED 5.550000 (2F bath ceiling (under dome 3))
- L-f74c0fc7f78b579e6097 DOME:EAST:intrados: HELD None (east dome soffit (top of V-06))
- L-cf3e2b55648f676ffb1d DOME:WEST:intrados: HELD None (west dome soffit (top of V-05))
- L-2175a965bb7c48a50e6c GF-R31F8AE:stairwell ceiling: HELD None (ST-01 GF stairwell)
- L-eb3be58fc760b39f0e38 GF-RC99C2A:ceiling: RELEASED 101.137092 (GF open-plan ceiling (storey below V-01))
