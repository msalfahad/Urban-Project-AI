# T-735 formwork conflict decider: 7 lines, one live form each, on ARCH_TAKEOFF_V3.0.73

Research only: nothing wired, released or VERIFIED; figures beside, never summed into a released total.

| line | column | member m3 | sections | shaft h lo / D | T-707 | T-714 | **T-735 live (m2)** |
|---|---|---|---|---|---|---|---|
| L-6cba8c04 | 34A COL-GF-15 | 0.26352 .. 0.405 | 0.20x0.40 / 0.20x0.50 | 2.544 / 0.75..0.75 | 3.760800 .. 5.446000 | BLANK | **AT_LEAST >= 3.052800** |
| L-6f83fc39 | 412 COL-2F-51 | 0.3287 .. 0.425 | 0.20x0.50 | 2.537000 / 0.75..0.75 | 4.349800 .. 5.698000 | BLANK | **BOUNDED 4.183916 .. 5.532116** |
| L-7fe93376 | 350 COL-GF-29 | 0.26352 .. 0.50625 | 0.20x0.40 / 0.25x0.50 | 2.544 / 0.75..0.75 | 3.760800 .. 5.835000 | BLANK | **AT_LEAST >= 3.052800** |
| L-b35c1688 | 415 COL-2F-49 | 0.3287 .. 0.51 | 0.20x0.50 / 0.20x0.60 | 2.067000 / 0.75..1.2 | 4.377800 .. 6.544000 | BLANK | **AT_LEAST >= 2.893800** |
| L-ddec0b3f | 34D COL-GF-16 | 0.26352 .. 0.405 | 0.20x0.40 / 0.20x0.50 | 2.544 / 0.75..0.75 | 3.760800 .. 5.446000 | BLANK | **AT_LEAST >= 3.052800** |
| L-f9836bd6 | 356 COL-GF-28 | 0.26352 .. 0.405 | 0.20x0.40 / 0.20x0.50 | 2.544 / 0.75..0.75 | 3.760800 .. 5.446000 | BLANK | **AT_LEAST >= 3.052800** |
| L-867e155d | BM-1F-031 REST side | beam held (width) | D 0.50 t 0.16 | L 0.300055503 | - | BLANK cap 0 | **BOUNDED 0.102019** |

| family B10-13 | after T-732 | after T-735 |
|---|---|---|
| BOUNDED | 30: 102.914777 .. 127.151372 | 32: 107.200712 .. 132.785507 |
| AT_LEAST | 35: >= 107.379697 | 40: >= 122.484697 |
| BLANK_NAMED | 251 | 244 |
| FIX_ROW | 54 | 54 |

## Supersession (R-T735-1)

- L-6cba8c04 T-707: UPPER_BOUND_METHOD_NOT_A_FLOOR: low 3.760800 = P x (h_lo - t) (UP-FW-001: includes the faces under framing members, F-T732-1); high 5.446000 = P_max x (h_hi - t) = the perimeter envelope (ENVELOPE_NOT_LINE_HIGH: leaves out the slab-edge band outside the column)
- L-6cba8c04 T-714: BLANK_WITH_POSITIVE_FLOOR: T-714 'no positive floor: every face is 0 .. x or follows an unstated reading': it read the shaft as DEPENDENT on the column reading; R-T732-1 floors the shaft at P_min x (least panel top - base - D_max) = 3.052800 for every reading
- L-6f83fc39 T-707: UPPER_BOUND_METHOD_NOT_A_FLOOR: low 4.349800 = P x (h_lo - t) (UP-FW-001: includes the faces under framing members, F-T732-1); high 5.698000 = P_max x (h_hi - t) = the perimeter envelope (ENVELOPE_NOT_LINE_HIGH: leaves out the slab-edge band outside the column)
- L-6f83fc39 T-714: BLANK_WITH_POSITIVE_FLOOR: T-714 'no positive floor: every face is 0 .. x or follows an unstated reading': it read the shaft as DEPENDENT on the column reading; R-T732-1 floors the shaft at P_min x (least panel top - base - D_max) = 3.551800 for every reading
- L-7fe93376 T-707: UPPER_BOUND_METHOD_NOT_A_FLOOR: low 3.760800 = P x (h_lo - t) (UP-FW-001: includes the faces under framing members, F-T732-1); high 5.835000 = P_max x (h_hi - t) = the perimeter envelope (ENVELOPE_NOT_LINE_HIGH: leaves out the slab-edge band outside the column)
- L-7fe93376 T-714: BLANK_WITH_POSITIVE_FLOOR: T-714 'no positive floor: every face is 0 .. x or follows an unstated reading': it read the shaft as DEPENDENT on the column reading; R-T732-1 floors the shaft at P_min x (least panel top - base - D_max) = 3.052800 for every reading
- L-b35c1688 T-707: UPPER_BOUND_METHOD_NOT_A_FLOOR: low 4.377800 = P x (h_lo - t) (UP-FW-001: includes the faces under framing members, F-T732-1); high 6.544000 = P_max x (h_hi - t) = the perimeter envelope (ENVELOPE_NOT_LINE_HIGH: leaves out the slab-edge band outside the column)
- L-b35c1688 T-714: BLANK_WITH_POSITIVE_FLOOR: T-714 'no positive floor: every face is 0 .. x or follows an unstated reading': it read the shaft as DEPENDENT on the column reading; R-T732-1 floors the shaft at P_min x (least panel top - base - D_max) = 2.893800 for every reading
- L-ddec0b3f T-707: UPPER_BOUND_METHOD_NOT_A_FLOOR: low 3.760800 = P x (h_lo - t) (UP-FW-001: includes the faces under framing members, F-T732-1); high 5.446000 = P_max x (h_hi - t) = the perimeter envelope (ENVELOPE_NOT_LINE_HIGH: leaves out the slab-edge band outside the column)
- L-ddec0b3f T-714: BLANK_WITH_POSITIVE_FLOOR: T-714 'no positive floor: every face is 0 .. x or follows an unstated reading': it read the shaft as DEPENDENT on the column reading; R-T732-1 floors the shaft at P_min x (least panel top - base - D_max) = 3.052800 for every reading
- L-f9836bd6 T-707: UPPER_BOUND_METHOD_NOT_A_FLOOR: low 3.760800 = P x (h_lo - t) (UP-FW-001: includes the faces under framing members, F-T732-1); high 5.446000 = P_max x (h_hi - t) = the perimeter envelope (ENVELOPE_NOT_LINE_HIGH: leaves out the slab-edge band outside the column)
- L-f9836bd6 T-714: BLANK_WITH_POSITIVE_FLOOR: T-714 'no positive floor: every face is 0 .. x or follows an unstated reading': it read the shaft as DEPENDENT on the column reading; R-T732-1 floors the shaft at P_min x (least panel top - base - D_max) = 3.052800 for every reading
- L-867e155d T-714: CAP_ZERO_FROM_HELD_DEPTH: the 0 .. 0 face is the walk's held-depth convention (D None -> 0 m2 + held length 0.300056 m), not a measured zero; no ZERO_BY_GEOMETRY: the band is 0.50 deep under a 0.16 slab along that length
