| Trade | Unit | Baseline | Ref lines | Coverage % | Compared | WAPE % | Signed % | Verified share % | Held or UNKNOWN | Rule difference share % |
|---|---|---|---|---|---|---|---|---|---|---|
| CONCRETE | m3 | A (released V29_ROUTEG_NO_PROFILE), manifest 48db934e, BOQ_LINES.csv b96185d4 | 8 | 100.00 | 3 | 17.03 | -17.03 | 0.00 (0 / 8); 5 partial re-measures not counted | 5 ref lines HELD; 205 engine lines: 122 bounded 44.108 .. 113.540 m3 + 83 UNKNOWN (no bound) | 12.50 (1 / 8) |
| CONCRETE | m3 | ARCH_TAKEOFF_V3.0.41, V3_0_41_BOQ_LINES.json 5176c7c4, V3_0_41_BOQ_LINES.csv 145eb34d | 8 | 100.00 | 1 | 0.77 | 0.77 | 0.00 (0 / 8); 5 partial re-measures not counted | 7 ref lines HELD; 127 engine lines: 83 bounded 28.701 .. 63.405 m3 + 44 UNKNOWN (no bound); 85 more excluded with reason | 12.50 (1 / 8) |
| DOORS | m2 | A (released V29_ROUTEG_NO_PROFILE), manifest 48db934e, BOQ_LINES.csv b96185d4 | 1 | 0.00 | 0 | NOT YET MEASURED | NOT YET MEASURED | 0.00 (0 / 1) | NOT YET MEASURED (unit refused: the engine answers DOORS.ALUMINIUM in pcs, the reference in m2) | NOT YET MEASURED |
| DOORS | m2 | ARCH_TAKEOFF_V3.0.41, V3_0_41_BOQ_LINES.json 5176c7c4, V3_0_41_BOQ_LINES.csv 145eb34d | 1 | 100.00 | 1 | 6.33 | 6.33 | 0.00 (0 / 1) | 0 ref lines HELD | NOT YET MEASURED |
| FLOOR_AREA | m2 | A (released V29_ROUTEG_NO_PROFILE), manifest 48db934e, BOQ_LINES.csv b96185d4 | 1 | 100.00 | 1 | 5.85 | -5.85 | 0.00 (0 / 1) | 0 ref lines HELD | NOT YET MEASURED (1 partial rule verdict not counted) |
| FLOOR_AREA | m2 | ARCH_TAKEOFF_V3.0.41, V3_0_41_BOQ_LINES.json 5176c7c4, V3_0_41_BOQ_LINES.csv 145eb34d | 1 | 100.00 | 1 | 5.06 | -5.06 | 0.00 (0 / 1) | 0 ref lines HELD | NOT YET MEASURED (1 partial rule verdict not counted) |
| PAINT | m2 | A (released V29_ROUTEG_NO_PROFILE), manifest 48db934e, BOQ_LINES.csv b96185d4 | 1 | 100.00 | 0 | NOT YET MEASURED | NOT YET MEASURED | 0.00 (0 / 1) | 1 ref line HELD; 13 engine lines: 13 UNKNOWN (no bound); 14 more excluded with reason | NOT YET MEASURED (1 partial rule verdict not counted) |
| PAINT | m2 | ARCH_TAKEOFF_V3.0.41, V3_0_41_BOQ_LINES.json 5176c7c4, V3_0_41_BOQ_LINES.csv 145eb34d | 1 | 100.00 | 0 | NOT YET MEASURED | NOT YET MEASURED | 0.00 (0 / 1) | 1 ref line HELD; 10 engine lines: 7 bounded 487.121 .. 542.861 m2 + 3 UNKNOWN (no bound); 31 more excluded with reason | NOT YET MEASURED (1 partial rule verdict not counted) |
| PLASTER | m2 | A (released V29_ROUTEG_NO_PROFILE), manifest 48db934e, BOQ_LINES.csv b96185d4 | 1 | 100.00 | 0 | NOT YET MEASURED | NOT YET MEASURED | 0.00 (0 / 1) | 1 ref line HELD; 29 engine lines: 2 bounded 2.360 .. 2.600 m2 + 27 UNKNOWN (no bound) | NOT YET MEASURED (1 partial rule verdict not counted) |
| PLASTER | m2 | ARCH_TAKEOFF_V3.0.41, V3_0_41_BOQ_LINES.json 5176c7c4, V3_0_41_BOQ_LINES.csv 145eb34d | 1 | 100.00 | 0 | NOT YET MEASURED | NOT YET MEASURED | 0.00 (0 / 1) | 1 ref line HELD; 20 engine lines: 8 bounded 488.201 .. 544.061 m2 + 12 UNKNOWN (no bound); 13 more excluded with reason | NOT YET MEASURED (1 partial rule verdict not counted) |
| WINDOWS | m2 | A (released V29_ROUTEG_NO_PROFILE), manifest 48db934e, BOQ_LINES.csv b96185d4 | 1 | 0.00 | 0 | NOT YET MEASURED | NOT YET MEASURED | 0.00 (0 / 1) | NOT YET MEASURED (unit refused: the engine answers WINDOWS.ALUMINIUM in pcs, the reference in m2) | NOT YET MEASURED |
| WINDOWS | m2 | ARCH_TAKEOFF_V3.0.41, V3_0_41_BOQ_LINES.json 5176c7c4, V3_0_41_BOQ_LINES.csv 145eb34d | 1 | 100.00 | 0 | NOT YET MEASURED | NOT YET MEASURED | 0.00 (0 / 1) | 1 ref line HELD; 2 engine lines: 1 bounded 9.870 .. 11.515 m2 + 1 UNKNOWN (no bound); 27 more excluded with reason | NOT YET MEASURED |

### Review-set bindings (opt-in; ASSUMED — OWNER-APPROVED kept apart from released lines)

| Side | Key | Released lines | Binding: ASSUMED — OWNER-APPROVED | Bound sets (rule, verdict commit) | Held sets / lines | Line total |
|---|---|---|---|---|---|---|
| A (released V29_ROUTEG_NO_PROFILE) | FLOOR.INTERNAL | 376.2857 on 44 | 9.3482 on 3 | COND:REVIEW_CLASSIFICATION:GF:GF-RDBD4F9 4.7307 (Q-06 A, 54cb4c42), COND:REVIEW_CLASSIFICATION:GF:GF-R8496F0 3.1325 (Q-06 A, 54cb4c42), COND:REVIEW_CLASSIFICATION:GF:GF-RD36087 1.4850 (Q-06 A, 54cb4c42) | - | 385.6339 |
| ARCH_TAKEOFF_V3.0.41 | FLOOR.INTERNAL | 388.8591 on 44 | 0.0000 on 0 | -; 3 sets decided by this side's own released line (in the released lines, not added again): COND:REVIEW_CLASSIFICATION:GF:GF-RDBD4F9 4.7307, COND:REVIEW_CLASSIFICATION:GF:GF-R8496F0 3.1325, COND:REVIEW_CLASSIFICATION:GF:GF-RD36087 1.4850 | - | 388.8591 |

### Lines excluded: UNIT_NOT_IN_REFERENCE (a unit no reference line can use; never converted, never summed, never scored)

| Side | Line id | Item code | Unit | Quantity as written | Evidence state | Key |
|---|---|---|---|---|---|---|
| ARCH_TAKEOFF_V3.0.41 | L-d2488bbb7103c8cd2980 | WP.FOUNDATION.PROCUREMENT | item | blank | BLOCKED_RFI | unmapped |
