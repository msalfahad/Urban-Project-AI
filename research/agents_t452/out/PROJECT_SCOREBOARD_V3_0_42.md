# Project scoreboard: development villa (training sample; regression only, never a product accuracy figure) (development-villa-t131)

Key map: legacy URBAN_ALSENAN_KEY_MAP_V2; reconciled reference: URBAN_CHECKER_REFERENCES_V1; pricing basis: none (cost NOT priced); tolerance +-3 %.

## Released V2.9 + route G (1455 BOQ lines)

### Score (per trade and unit)

| Trade | Unit | Ref lines | Coverage | Silent omissions | Unit refused | Compared | WAPE | WAPE (adjudicated) | Signed | False pos. | Duplicates |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CONCRETE | m3 | 8 | 100.00 % | 0 | 0 | 3 | 17.03 % | 17.03 % | -17.03 % | 0 | 0 |
| DOORS | m2 | 1 | 0.00 % | 0 | 1 | 0 | - | - | - | 0 | 0 |
| FLOOR_AREA | m2 | 1 | 100.00 % | 0 | 0 | 1 | 5.85 % | 5.85 % | -5.85 % | 0 | 0 |
| PAINT | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | - | 0 | 0 |
| PLASTER | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | - | 0 | 0 |
| WINDOWS | m2 | 1 | 0.00 % | 0 | 1 | 0 | - | - | - | 0 | 0 |

### Review-set bindings (opt-in; ASSUMED — OWNER-APPROVED kept apart from released lines)

| Side | Key | Released lines | Binding: ASSUMED — OWNER-APPROVED | Bound sets (rule, verdict commit) | Held sets / lines | Line total |
|---|---|---|---|---|---|---|
| base | FLOOR.INTERNAL | 376.2857 on 44 | 9.3482 on 3 | COND:REVIEW_CLASSIFICATION:GF:GF-RDBD4F9 4.7307 (Q-06 A, 54cb4c42), COND:REVIEW_CLASSIFICATION:GF:GF-R8496F0 3.1325 (Q-06 A, 54cb4c42), COND:REVIEW_CLASSIFICATION:GF:GF-RD36087 1.4850 (Q-06 A, 54cb4c42) | - | 385.6339 |

### Variance per trade and unit (original workbook | reconciled reference)

| Trade | Unit | Keys | Compared | Reference | Engine | Var. original | Reconciled keys | Var. reconciled | Held | Exceptions | Offsetting | Complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ALUMINIUM | m2 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 1 | - | no |
| BLOCKWORK | m2 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 4 | - | no |
| CEILING | lm | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 2 | - | no |
| CEILING | m2 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 2 | - | no |
| CONCRETE | m3 | 8 | 3 | 111.811 | 92.767 | -17.03 % | 0 | - | 5 | - | - | no |
| DOORS | m2 | 1 | 0 | - | - | - | 0 | - | 0 | SCOPE_MISMATCH 1 | - | no |
| FLOOR | m2 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 2 | - | no |
| FLOOR_AREA | m2 | 1 | 1 | 409.580 | 385.634 | -5.85 % | 0 | - | 0 | - | - | yes |
| MARBLE | m2 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 1 | - | no |
| MARBLE | nr | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 1 | - | no |
| OTHER_CONCRETE | m3 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 1 | - | no |
| PAINT | (missing) | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 2 | - | no |
| PAINT | m2 | 1 | 0 | - | - | - | 0 | - | 1 | - | - | no |
| PLASTER | (missing) | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 5 | - | no |
| PLASTER | m2 | 1 | 0 | - | - | - | 0 | - | 1 | - | - | no |
| RAILING | lm | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 1 | - | no |
| REBAR | t | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 1 | - | no |
| SKIRTING | lm | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 3 | - | no |
| WALL_TILE | m2 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 2 | - | no |
| WATERPROOFING | lm | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 2 | - | no |
| WATERPROOFING | m2 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 2 | - | no |
| WINDOWS | m2 | 1 | 0 | - | - | - | 0 | - | 0 | SCOPE_MISMATCH 1 | - | no |

### Cost per trade (one approved basis, same rate both sides)

| Trade | Status | Compared keys | Reference cost | Engine cost | Var. original | Var. reconciled | Unpriced keys |
|---|---|---|---|---|---|---|---|
| CONCRETE | NO_APPROVED_PRICING_BASIS | 3 | - | - | - | - | - |
| DOORS | NO_APPROVED_PRICING_BASIS | 0 | - | - | - | - | - |
| FLOOR_AREA | NO_APPROVED_PRICING_BASIS | 1 | - | - | - | - | - |
| PAINT | NO_APPROVED_PRICING_BASIS | 0 | - | - | - | - | - |
| PLASTER | NO_APPROVED_PRICING_BASIS | 0 | - | - | - | - | - |
| WINDOWS | NO_APPROVED_PRICING_BASIS | 0 | - | - | - | - | - |

### High-value lines (line level)

| Key | Unit | Outcome | Engine | Original | Var. original | Reconciled | Var. reconciled | Exception |
|---|---|---|---|---|---|---|---|---|
| CONC.FOOTING | m3 | COMPARED | 77.265 | 77.631 | -0.47 % | NOT_VERIFIED | - | - |
| CONC.GROUND | m3 | HELD | - | 75.090 | - | NO_RECONCILED_REFERENCE | - | - |
| CONC.COLUMN | m3 | HELD | - | 39.752 | - | NO_RECONCILED_REFERENCE | - | - |
| CONC.BEAM | m3 | HELD | - | 65.966 | - | NO_RECONCILED_REFERENCE | - | - |
| CONC.SLAB | m3 | HELD | - | 59.817 | - | 60.280 | - | - |
| CONC.STAIR_DOME | m3 | COMPARED | 12.007 | 21.833 | -45.01 % | NO_RECONCILED_REFERENCE | - | - |
| CONC.POOL | m3 | COMPARED | 3.495 | 12.348 | -71.69 % | NO_RECONCILED_REFERENCE | - | - |
| DOORS.ALUMINIUM | m2 | UNIT_MISMATCH | - | 12.000 | - | NO_RECONCILED_REFERENCE | - | SCOPE_MISMATCH |
| WINDOWS.ALUMINIUM | m2 | UNIT_MISMATCH | - | 116.900 | - | NO_RECONCILED_REFERENCE | - | SCOPE_MISMATCH |

### Exceptions: ZERO_REFERENCE 0, ENGINE_ONLY 30, REFERENCE_ONLY 32, SCOPE_MISMATCH 2

| Class | Side | Key / ref / item | Unit | Reason |
|---|---|---|---|---|
| SCOPE_MISMATCH | original | DOORS.ALUMINIUM | m2 | every engine answer is in another unit (refused, never converted) |
| SCOPE_MISMATCH | original | WINDOWS.ALUMINIUM | m2 | every engine answer is in another unit (refused, never converted) |
| REFERENCE_ONLY | original | FIN:الغلاف:16 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:17 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:18 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:19 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:22 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:23 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:24 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:25 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:26 | عدد | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:27 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:28 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:29 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:30 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:34 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:35 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:36 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:37 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:39 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | BLK:الغلاف:15 | m2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | BLK:الغلاف:16 | m2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | BLK:الغلاف:17 | m2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | BLK:الغلاف:19 | m2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | PNT:الفاتورة:18 |  | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | PNT:الفاتورة:22 |  | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | RC:ورقة1:24 | m3 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | RC:ورقة1:25 | t | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | ALU:الغلاف:20 | m2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | PLS:الفاتورة:17 |  | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | PLS:الفاتورة:18 |  | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | PLS:الفاتورة:19 |  | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | PLS:الفاتورة:25 |  | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | PLS:الفاتورة:26 |  | no key names this reference row (key-map gap or a total of keyed rows) |
| ENGINE_ONLY | engine | ARCH.EXTERIOR (1 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.FACADE (4 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.FACADE_RUN (6 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.PASSAGE (11 line(s)) | pcs | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.SPACE (12 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.THRESHOLD (14 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.WALL_PANEL (7 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.WALL_RUN (7 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.WALL_VOLUME (7 line(s)) | m3 | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.WINDOW_REVEAL (27 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | DOOR.INTERNAL.PVC (15 line(s)) | pcs | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.CEILING (31 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.EXT.FINISH (3 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.MARBLE.LANDING (2 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.MARBLE.RISER (14 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.MARBLE.THRESHOLD (10 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.MARBLE.TREAD (14 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.RAILING (14 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.SKIRTING (22 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.STAIR.FLIGHT (14 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.STAIR.STEP_LM (14 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WALL.TILE (14 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.DOORWAY (14 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.DOORWAY_TRANSITION (13 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.FLOOR (14 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.PENETRATION (14 line(s)) | pcs | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.TERMINATION (4 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.WALL_UPTURN (14 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | MAS.BLOCK (7 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | STR.REBAR (497 line(s)) | kg | unmapped item code (no key) |

## Candidate ARCH_TAKEOFF_V3.0.42 (4839 BOQ lines)

### Score (per trade and unit)

| Trade | Unit | Ref lines | Coverage | Silent omissions | Unit refused | Compared | WAPE | WAPE (adjudicated) | Signed | False pos. | Duplicates |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CONCRETE | m3 | 8 | 100.00 % | 0 | 0 | 1 | 0.77 % | 0.77 % | 0.77 % | 0 | 0 |
| DOORS | m2 | 1 | 100.00 % | 0 | 0 | 1 | 6.33 % | 6.33 % | 6.33 % | 0 | 0 |
| FLOOR_AREA | m2 | 1 | 100.00 % | 0 | 0 | 1 | 5.06 % | 5.06 % | -5.06 % | 0 | 0 |
| PAINT | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | - | 0 | 0 |
| PLASTER | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | - | 0 | 0 |
| WINDOWS | m2 | 1 | 100.00 % | 0 | 0 | 0 | - | - | - | 0 | 0 |

### Review-set bindings (opt-in; ASSUMED — OWNER-APPROVED kept apart from released lines)

| Side | Key | Released lines | Binding: ASSUMED — OWNER-APPROVED | Bound sets (rule, verdict commit) | Held sets / lines | Line total |
|---|---|---|---|---|---|---|
| Candidate ARCH_TAKEOFF_V3.0.42 | FLOOR.INTERNAL | 388.8591 on 44 | 0.0000 on 0 | -; 3 sets decided by this side's own released line (in the released lines, not added again): COND:REVIEW_CLASSIFICATION:GF:GF-RDBD4F9 4.7307, COND:REVIEW_CLASSIFICATION:GF:GF-R8496F0 3.1325, COND:REVIEW_CLASSIFICATION:GF:GF-RD36087 1.4850 | - | 388.8591 |

### Lines excluded: UNIT_NOT_IN_REFERENCE (a unit no reference line can use; never converted, never summed, never scored)

| Side | Line id | Item code | Unit | Quantity as written | Evidence state | Key |
|---|---|---|---|---|---|---|
| Candidate ARCH_TAKEOFF_V3.0.42 | L-d2488bbb7103c8cd2980 | WP.FOUNDATION.PROCUREMENT | item | blank | BLOCKED_RFI | unmapped |

### Variance per trade and unit (original workbook | reconciled reference)

| Trade | Unit | Keys | Compared | Reference | Engine | Var. original | Reconciled keys | Var. reconciled | Held | Exceptions | Offsetting | Complete |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ALUMINIUM | m2 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 1 | - | no |
| BLOCKWORK | m2 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 4 | - | no |
| CEILING | lm | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 2 | - | no |
| CEILING | m2 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 2 | - | no |
| CONCRETE | m3 | 8 | 1 | 59.817 | 60.280 | +0.77 % | 1 | -0.00 % | 7 | - | - | no |
| DOORS | m2 | 1 | 1 | 12.000 | 12.760 | +6.33 % | 0 | - | 0 | - | - | yes |
| FLOOR | m2 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 2 | - | no |
| FLOOR_AREA | m2 | 1 | 1 | 409.580 | 388.859 | -5.06 % | 0 | - | 0 | - | - | yes |
| MARBLE | m2 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 1 | - | no |
| MARBLE | nr | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 1 | - | no |
| OTHER_CONCRETE | m3 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 1 | - | no |
| PAINT | (missing) | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 2 | - | no |
| PAINT | m2 | 1 | 0 | - | - | - | 0 | - | 1 | - | - | no |
| PLASTER | (missing) | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 5 | - | no |
| PLASTER | m2 | 1 | 0 | - | - | - | 0 | - | 1 | - | - | no |
| RAILING | lm | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 1 | - | no |
| REBAR | t | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 1 | - | no |
| SKIRTING | lm | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 3 | - | no |
| WALL_TILE | m2 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 2 | - | no |
| WATERPROOFING | lm | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 2 | - | no |
| WATERPROOFING | m2 | 0 | 0 | - | - | - | 0 | - | 0 | REFERENCE_ONLY 2 | - | no |
| WINDOWS | m2 | 1 | 0 | - | - | - | 0 | - | 1 | - | - | no |

### Cost per trade (one approved basis, same rate both sides)

| Trade | Status | Compared keys | Reference cost | Engine cost | Var. original | Var. reconciled | Unpriced keys |
|---|---|---|---|---|---|---|---|
| CONCRETE | NO_APPROVED_PRICING_BASIS | 1 | - | - | - | - | - |
| DOORS | NO_APPROVED_PRICING_BASIS | 1 | - | - | - | - | - |
| FLOOR_AREA | NO_APPROVED_PRICING_BASIS | 1 | - | - | - | - | - |
| PAINT | NO_APPROVED_PRICING_BASIS | 0 | - | - | - | - | - |
| PLASTER | NO_APPROVED_PRICING_BASIS | 0 | - | - | - | - | - |
| WINDOWS | NO_APPROVED_PRICING_BASIS | 0 | - | - | - | - | - |

### High-value lines (line level)

| Key | Unit | Outcome | Engine | Original | Var. original | Reconciled | Var. reconciled | Exception |
|---|---|---|---|---|---|---|---|---|
| CONC.FOOTING | m3 | HELD | - | 77.631 | - | NOT_VERIFIED | - | - |
| CONC.GROUND | m3 | HELD | - | 75.090 | - | NO_RECONCILED_REFERENCE | - | - |
| CONC.COLUMN | m3 | HELD | - | 39.752 | - | NO_RECONCILED_REFERENCE | - | - |
| CONC.BEAM | m3 | HELD | - | 65.966 | - | NO_RECONCILED_REFERENCE | - | - |
| CONC.SLAB | m3 | COMPARED | 60.280 | 59.817 | +0.77 % | 60.280 | -0.00 % | - |
| CONC.STAIR_DOME | m3 | HELD | - | 21.833 | - | NO_RECONCILED_REFERENCE | - | - |
| CONC.POOL | m3 | HELD | - | 12.348 | - | NO_RECONCILED_REFERENCE | - | - |
| DOORS.ALUMINIUM | m2 | COMPARED | 12.760 | 12.000 | +6.33 % | NO_RECONCILED_REFERENCE | - | - |
| WINDOWS.ALUMINIUM | m2 | HELD | - | 116.900 | - | NO_RECONCILED_REFERENCE | - | - |

### Exceptions: ZERO_REFERENCE 0, ENGINE_ONLY 84, REFERENCE_ONLY 32, SCOPE_MISMATCH 0

| Class | Side | Key / ref / item | Unit | Reason |
|---|---|---|---|---|
| REFERENCE_ONLY | original | FIN:الغلاف:16 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:17 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:18 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:19 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:22 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:23 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:24 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:25 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:26 | عدد | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:27 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:28 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:29 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:30 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:34 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:35 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:36 | م2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:37 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | FIN:الغلاف:39 | م.ط | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | BLK:الغلاف:15 | m2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | BLK:الغلاف:16 | m2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | BLK:الغلاف:17 | m2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | BLK:الغلاف:19 | m2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | PNT:الفاتورة:18 |  | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | PNT:الفاتورة:22 |  | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | RC:ورقة1:24 | m3 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | RC:ورقة1:25 | t | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | ALU:الغلاف:20 | m2 | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | PLS:الفاتورة:17 |  | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | PLS:الفاتورة:18 |  | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | PLS:الفاتورة:19 |  | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | PLS:الفاتورة:25 |  | no key names this reference row (key-map gap or a total of keyed rows) |
| REFERENCE_ONLY | original | PLS:الفاتورة:26 |  | no key names this reference row (key-map gap or a total of keyed rows) |
| ENGINE_ONLY | engine | ARCH.EXTERIOR (1 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.FACADE (4 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.FACADE_RUN (6 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.PASSAGE (9 line(s)) | pcs | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.SHUTTER (3 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.SHUTTER (3 line(s)) | pcs | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.SPACE (11 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.THRESHOLD (14 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.WALL_PANEL (26 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.WALL_RUN (7 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.WALL_VOLUME (26 line(s)) | m3 | unmapped item code (no key) |
| ENGINE_ONLY | engine | ARCH.WINDOW_REVEAL (62 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | DOOR.INTERNAL.PVC (5 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | DOOR.INTERNAL.PVC (5 line(s)) | pcs | unmapped item code (no key) |
| ENGINE_ONLY | engine | DOOR.MAIN_ENTRANCE (1 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | DOOR.MAIN_ENTRANCE (1 line(s)) | pcs | unmapped item code (no key) |
| ENGINE_ONLY | engine | EXT.FENCE.BLOCK (4 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | EXT.FENCE.BLOCK_COUNT (1 line(s)) | pcs | unmapped item code (no key) |
| ENGINE_ONLY | engine | EXT.FENCE.FACE (9 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | EXT.FENCE.GATE (2 line(s)) | pcs | unmapped item code (no key) |
| ENGINE_ONLY | engine | EXT.FENCE.MASONRY_BELOW_NG (1 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | EXT.FENCE.PAINT (8 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | EXT.FENCE.PLASTER (8 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | EXT.FENCE.TOP (2 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | EXT.FENCE.WALL (4 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | EXT.FLOOR.OUTDOOR (2 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | EXT.FLOOR.PORCELAIN (1 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | EXT.PAVING.INTERLOCK (1 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | EXT.POOL.WATER_FACE (1 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.CEILING (41 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.CEILING.BULKHEAD (14 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.DOME.SOFFIT (2 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.EXT.FINISH (3 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.FLOOR.BED.DRY (23 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.FLOOR.BED.DRY (23 line(s)) | m3 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.FLOOR.BED.WET (21 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.FLOOR.BED.WET (21 line(s)) | m3 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.FLOOR.FINISH_HELD (3 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.MARBLE.LANDING (4 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.MARBLE.LIFT_SURROUND (3 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.MARBLE.LIFT_THRESHOLD (3 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.MARBLE.LIFT_THRESHOLD (3 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.MARBLE.RISER (14 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.MARBLE.THRESHOLD (14 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.MARBLE.TREAD (13 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.PAINT.CEILING (31 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.RAILING (19 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.ROOF.FINISH (4 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.ROOF.INSULATION (4 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.ROOF.PROTECTION (4 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.ROOF.SCREED (4 line(s)) | m3 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.SKIRTING (20 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.STAIR.FLIGHT (14 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.STAIR.SOFFIT (2 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.STAIR.STEP_LM (12 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WALL.TILE (18 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.DOORWAY (14 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.DOORWAY_TRANSITION (13 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.DOORWAY_TRANSITION_NR (14 line(s)) | pcs | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.FLOOR (18 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.MEMBRANE_ROLLS (22 line(s)) | pcs | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.PENETRATION (17 line(s)) | pcs | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.ROOF (4 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.ROOF_UPTURN (4 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.TERMINATION (7 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | FIN.WP.WALL_UPTURN (18 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | MAS.BLOCK (26 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | MET.RAILING.GUARD (6 line(s)) | lm | unmapped item code (no key) |
| ENGINE_ONLY | engine | STR.CONC.BOUNDARY_PAD (1 line(s)) | m3 | unmapped item code (no key) |
| ENGINE_ONLY | engine | STR.CONC.LIFT (1 line(s)) | m3 | unmapped item code (no key) |
| ENGINE_ONLY | engine | STR.CONC.PARAPET (4 line(s)) | m3 | unmapped item code (no key) |
| ENGINE_ONLY | engine | STR.FORMWORK (612 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | STR.FORMWORK.STAIR (30 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | STR.REBAR (2066 line(s)) | kg | unmapped item code (no key) |
| ENGINE_ONLY | engine | WP.FOUNDATION.BURIED_LIQUID (5 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | WP.FOUNDATION.FOOTING_MEMBRANE (2 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | WP.FOUNDATION.FOOTING_SCREED (2 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | WP.FOUNDATION.FOOTING_SCREED (2 line(s)) | m3 | unmapped item code (no key) |
| ENGINE_ONLY | engine | WP.FOUNDATION.FOOTING_SIDES (1 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | WP.FOUNDATION.LIFT_PIT_BOARD (2 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | WP.FOUNDATION.LIFT_PIT_MEMBRANE (2 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | WP.FOUNDATION.LIFT_PIT_SCREED (1 line(s)) | m2 | unmapped item code (no key) |
| ENGINE_ONLY | engine | WP.FOUNDATION.LIFT_PIT_SCREED (1 line(s)) | m3 | unmapped item code (no key) |
| ENGINE_ONLY | engine | WP.FOUNDATION.PROCUREMENT (1 line(s)) | item | unit no reference line can use (UNIT_NOT_IN_REFERENCE) |

